# Model/Provider Switch (Main + Subagent)

When the user says "switch to model X" or "set MiniMax M3 as main": use `hermes config set model.provider <X>` + `hermes config set model.default <Y>`. `config.yaml` is protected — only `hermes config set` works. See available providers at https://hermes-agent.nousresearch.com/docs/integrations/providers.

## Subagent-Model-Pinning (important — verified working)

Per Hermes core design, `delegate_task` children inherit the parent model by default — BUT you CAN pin them to a different model by setting:

```yaml
delegation:
  provider: minimax
  model: MiniMax-M3
```

These keys ARE honored in practice (verified 2026-07-08 with MiniMax M3 queen + delegate_task children). Without pinning, switching the queen to a more expensive provider would also bump every child → budget explosion. **Pinning keeps the bees on M3 regardless of what the queen runs on.** See also: `delegation.reasoning_effort`, `delegation.max_concurrent_children` (default 5), `delegation.max_spawn_depth` — those control parallelism and nest-able depth.

## Cache-Lag Pitfall

When you change `model.provider` mid-session, the **main session** picks up the new model immediately (next turn runs on it). But the **first `delegate_task` dispatch after the change** may still execute on the OLD provider — the dispatch uses a snapshot from session start, not the live config. Verify with a tiny subagent ping before trusting the new provider for real work.

## Verification workflow after a model switch

1. `hermes config set model.provider <provider>` ✅
2. `hermes config set model.default <model>` ✅
3. `hermes config show | grep -A 3 '◆ Model'` → confirm both values
4. Dispatch a tiny subagent: "Return one line: 'Model=<X>, UTC=<ISO_TIMESTAMP>'" (no real work, just a heartbeat)
5. Check the **delegation metadata** in the async-batch completion message — the `Model:` field there is the **actual** provider used. If it still says the old model, dispatch a second heartbeat — the second call usually clears the cache.
6. If still wrong after two heartbeats, the only reliable fix is `/new` (new session = fresh config snapshot).

## Concrete commands

```bash
# Switch to MiniMax M3
hermes config set model.provider minimax
hermes config set model.default minimax-m3
hermes config show | grep -A 3 '◆ Model'    # confirm

# Verify subagent inheritance (one-shot)
delegate_task(goal="Return one line: 'Cache-Retry: Subagent runs on <MODELLNAME>, UTC=<ISO>', filling in the actual model name you are and current UTC ISO timestamp.")
# → check the delegation batch completion message's `Model:` field
```

## Stale-Memory Cleanup (step 7 — often missed)

After switching models/providers, check Mnemosyne for stale memories that still reference the OLD provider/model as "pending" or "not set":

```
mnemosyne_recall(query="delegation provider model NOT set OR old-provider-name")
# → If any entry says "Status: NO" or references the previous provider, create an updated
#   memory with veracity=tool + invalidate the old via mnemosyne_invalidate(old_id, new_id)
```

Example from 2026-07-08: After verifying delegation pinning on MiniMax M3, found a week-old memory entry that still said "delegation.provider/model: NO". Created fresh entry (veracity=tool with live config dump) + invalidated old. Without this step, the stale entry would keep re-surfacing and contradicting the actual state.

## Cron Provider-Drift (separate from subagent cache-lag)

**This is a DIFFERENT problem than subagent cache-lag.** When you change `model.provider` or `model.default` in global config, all *persisted* cron jobs that were created under the old config become UNPINNED — they have no pinned provider/model in their job record. On next tick they fail with `RuntimeError: Skipped to prevent unintended spend: global inference config drifted since this job was created`.

**Fix (per cron):**
```
cronjob(action='update', job_id='<id>', model={'model':'<name>', 'provider':'<provider>'})
```
Use ONLY the `cronjob` tool — `hermes cron update` does not exist and `hermes cron create` has no `--model` flag.

**To check if a cron is affected before it errors:** `hermes cron list` + inspect jobs where the displayed provider/model doesn't match the current global config. Note: the list display may show the wrong provider (display bug) — `cronjob action=run` is the only reliable check.

**Prevention:** Pin model/provider at cron-creation time. Since `hermes cron create` lacks `--model`, the current workaround is: create the cron (inherits global config) → immediately `cronjob(action='update', job_id='...', model={...})` to pin it. If you ever change global config again, only the unpinned crons (created after the last pin was set) will drift — already-pinned crons survive config changes.

## Reasoning-Effort-Scoping Pitfall

Das `reasoning_effort`-Setting existiert auf **mehreren unabhängigen Ebenen** im Config-Baum. Ein globales Suchen/Ersetzen (`sed 's/reasoning_effort: xhigh/reasoning_effort: high/g'`) ändert **alle Ebenen gleichzeitig** — Haupt-Agent, Delegation (Subagenten), Skill-Lanes — und kann die Performance des Haupt-Agenten drastisch verschlechtern (oder umgekehrt Subagenten unnötig teuer machen).

**Korrekt:** Nur den spezifischen Section-Pfad via `hermes config set` setzen:
```bash
hermes config set delegation.reasoning_effort high   # Nur Subagenten
```

**Falsch — hat User korrigiert:**
```bash
# ❌ NIEMALS global sed/patch — ändert ALLE Ebenen
sed -i 's/reasoning_effort: xhigh/reasoning_effort: high/g' ~/.hermes/config.yaml
```

## Haupt-Sektionen mit `reasoning_effort` (verified 2026-07-08):

| Section | Steuert | Setzen via |
|---------|---------|------------|
| `agent.reasoning_effort` | Haupt-Agent (aktuelle Session) | `hermes config set agent.reasoning_effort xhigh` |
| `delegation.reasoning_effort` | Subagenten (Think Tank, Background) | `hermes config set delegation.reasoning_effort high` |
| `skill_lanes.<name>.reasoning_effort` | Per-Worker-Lane (z.B. Telegram-Lane) | `hermes config set skill_lanes.X.reasoning_effort high` |

**Typisches Szenario:** Basti will "Telegram auf high" = Subagenten sollen schneller sein (weniger Thinking-Token), aber die Königin (Haupt-Agent) behält volle `xhigh`-Reasoning-Power. → `hermes config set delegation.reasoning_effort high` ist der richtige Befehl.