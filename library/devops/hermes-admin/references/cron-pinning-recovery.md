---
name: cron-pinning-recovery
title: Cron Pinning Recovery — Hermes LLM-Cron Drift-Workflow
date: 2026-07-10
status: verified pattern (8 LLM-Crons recovered, 100% grün)
mnemosyne: 51462e7daa9535a2 (Pin-Audit-Cache)
parent: cron-error-categories (Category C = LLM provider drift)
issue-ref: Hermes GitHub #44585 (Drift-Protection)
vault-mirror: ~/Dokumente/Obsidian Vault/05 Ressourcen/Cron Drift Protection - Recovery-Workflow 2026-07-10.md
---

# Cron Pinning Recovery — Hermes LLM-Cron Drift-Workflow

> Vollständiges Recovery-Pattern für Cronjobs, die nach `hermes config set model.provider` / `model.default` mit **`RuntimeError: Skipped to prevent unintended spend`** gestoppt sind.
>
> Dies ist **Category C** aus dem [3-Category Diagnostic Model](cron-error-categories.md) — die systemischste Kategorie, weil sie **alle unpinned LLM-Crons gleichzeitig** trifft.

## Symptom

In `~/.hermes/logs/agent.log`:

```text
RuntimeError: Skipped to prevent unintended spend: global inference config drifted
since this job was created (provider 'zai' -> 'minimax'; model 'glm-5' -> 'minimax-m3'),
and this job is unpinned. No inference call was made. To run on the new config, pin it
explicitly: `cronjob action=update job_id=<id> provider=<provider> model=<model>` (or pin
the original values to keep them). See #44585.
```

In `cronjob(action='list')`:

- `last_status: error`
- `last_delivery_error: null` (Job lief, aber Output wurde nicht erzeugt — keine Delivery nötig)
- `last_run_at` aktualisiert, aber keine sichtbare Wirkung
- `model: null` und/oder `provider: null` in der Job-Config (Pinning fehlt)

## Ursache (Root Cause)

Hermes' **Drift-Protection** ist ein **Spend-Schutz** — keine Debug-Hilfe. Wenn ein LLM-Cronjob ohne explizites `provider`/`model`-Pinning erstellt wird, übernimmt er **die zum Erstellungszeitpunkt aktive Global-Config**. Bei jedem späteren `hermes config set model.provider` / `model.default` ändert sich diese. Der Job ist "drifted" und wird beim nächsten Tick **übersprungen** statt mit dem neuen Model zu laufen — sonst würden ungewollt Kosten auf dem neuen Provider entstehen.

**Wichtig — Pinning ist binär, nicht additiv:** Ein nachträgliches `cronjob action=update` setzt **nur** explizit übergebene Felder. Wenn nur `provider` aber nicht `model` gesetzt wird (oder umgekehrt), bleibt der Job unpinned und driftet beim nächsten Switch erneut.

## Diagnose-Checkliste (2-Minuten-Triage)

```bash
# 1. Welche Jobs sind unpinned?
hermes cron list 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
for j in d.get('jobs', []):
    if j.get('model') is None or j.get('provider') is None:
        print(f\"  UNPINNED: {j['job_id']} {j['name']} (provider={j.get('provider')}, model={j.get('model')})\")
"

# Alternative ohne Python:
hermes cron list | grep -B1 -E '"model":\s*null|"provider":\s*null'

# 2. Aktuelle Global-Config (Ziel-Pin)
grep -E 'provider:|default:' ~/.hermes/config.yaml | head -10

# 3. Letzter Switch-Zeitpunkt (zur Korrelation)
journalctl --user -u hermes-gateway --no-pager | grep -iE 'provider|model|switch' | tail -5

# 4. Heuristic — wenn 2+ Crons gleichzeitig error zeigen: systemische Ursache (Drift) zuerst
echo "→ 2+ LLM-Crons gleichzeitig error = Category C-Drift, Bulk-Recovery. Sonst individuell."
```

**Heuristic — "2+ errors → systemic first":** Nicht jeden Cron einzeln debuggen, wenn 2+ gleichzeitig error zeigen. Drift und alle betroffenen Jobs in einem Pass repinnen — spart 20-30 Minuten.

## Fix pro Job (1-Zeilen-Recovery)

```bash
# Provider + Model IMMER zusammen setzen (sonst greift die Protection nicht)
cronjob action=update job_id=<id> provider=<current_provider> model=<current_model>

# Verify
cronjob action=get <id> 2>&1 | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    j = d.get('job', d)
    print(f\"  job {j['job_id']}: provider={j.get('provider')}, model={j.get('model')}\")
except: print('manual check needed')
"
```

**Beispiel** (aktuelle Config `minimax`/`MiniMax-M3`):

```bash
cronjob action=update job_id=76039d75e57d provider=minimax model=MiniMax-M3
```

**Bulk-Recovery** (alle unpinned Jobs auf einmal repinnen):

```bash
CURRENT_PROVIDER=$(grep -E '^  provider:' ~/.hermes/config.yaml | head -1 | awk '{print $2}')
CURRENT_MODEL=$(grep -E '^  default:' ~/.hermes/config.yaml | head -1 | awk '{print $2}')

hermes cron list | python3 -c "
import sys, json
d = json.load(sys.stdin)
for j in d.get('jobs', []):
    if j.get('model') is None or j.get('provider') is None:
        print(f\"{j['job_id']}|{j['name']}\")
" | while IFS='|' read -r id name; do
    echo "Pinning $name ($id)…"
    cronjob action=update job_id="$id" provider="$CURRENT_PROVIDER" model="$CURRENT_MODEL"
done
```

## Verifikation (Post-Fix)

```bash
# 1. Trockenlauf triggern (verbraucht für LLM-Cron ggf. Tokens — vorher entscheiden)
cronjob action=run job_id=<id>

# 2. last_status prüfen — Ziel ist "ok"
cronjob action=get <id> 2>&1 | grep -E 'last_status|execution_success'

# 3. Falls Status nicht-ok bleibt:
journalctl --user -u hermes-gateway --no-pager -n 30 | grep -i "<job_id>\|drift\|44585"

# 4. Wenn mehrere Jobs gleichzeitig gepingt wurden: jede ID kurz prüfen
hermes cron list | python3 -c "
import sys, json
d = json.load(sys.stdin)
errs = [j for j in d.get('jobs',[]) if j.get('last_status') == 'error']
print(f'{len(errs)} jobs noch im error-Status:', [j['name'] for j in errs])
"
```

## Bei pausierten Jobs (Edge-Case)

```bash
# 1. Erst Pin setzen, dann Resume (in dieser Reihenfolge!)
cronjob action=update job_id=<id> provider=<p> model=<m>

# 2. Resume
cronjob action=resume job_id=<id>

# 3. Schedule nochmal explizit setzen falls "paused" bleibt
#    (manche Hermes-Versionen verlieren Schedule beim langen Pause)
cronjob action=update job_id=<id> schedule="<original schedule>"

# 4. Verify
cronjob action=list | grep -E "<id>|<original-schedule>"
```

## Lessons Learned (verifiziert 2026-07-10 Audit, alle 8 LLM-Crons recovered)

1. **Pinning ist binär, nicht additiv.** `provider` UND `model` MÜSSEN in derselben `cronjob action=update`-Action gesetzt werden. Nachträglich nur eins von beiden setzen = Pinning greift nicht.
2. **Script-Crons sind safe.** `no_agent=true`-Jobs haben kein LLM, kein Model, kein Drift-Risk. Der Fix betrifft nur LLM-Crons.
3. **Audit gehört ins Daily-Briefing.** Bei jedem Provider-Switch: einmal `cronjob action=list` durchgehen und Pinning mit aktueller Global-Config matchen. Mnemosyne-Cache hilft hier, ist aber kein Ersatz für Live-Check.
4. **OAuth-Provider-Varianten.** `yuno-mittags-check` pinnt auf `minimax-oauth` (NICHT `minimax`). Anderer Billing-Pfad, das ist by-design — bei einem OAuth→API-Key-Switch würde das wieder driften, aber das ist bewusst gewählt. Audit-Map muss diese Sonderfälle kennen.
5. **Pausierte Jobs vergessen Drift-Check.** Nach Resume laufen sie sofort mit altem Drift-Status → erst updaten, dann reschedulen, dann resume. Sonst läuft der Job 1x mit altem Config und driftet sofort wieder.
6. **Dry-Run via `cronjob action=run`:** Verbraucht ggf. Tokens (LLM läuft einmal). Für Script-Crons billig, für LLM-Crons vorher entscheiden ob der Lauf "akzeptabel" ist. Alternative: nur `cronjob action=get` und `last_run_at`/`last_status`-Check.
7. **Tool-Validation-Quirk:** `cronjob action=update schedule=""` (leerer String) meckert mit "Invalid schedule ''". Felder sparsam setzen, leere weglassen — sonst fällt das ganze Update aus.
8. **Mnemosyne-Pin-Status-Cache.** Nach einem vollständigen Audit (alle 8 LLM-Crons grün) → Fact-Memory in Mnemosyne speichern (importance ~0.85). Das spart beim nächsten Switch die komplette Audit-Schleife, weil `mnemosyne_recall("cron pinning audit")` sofort den Soll-Stand liefert.

## Audit-Tabelle (Template — bei jedem Audit füllen)

| Datum | Job-ID | Name | Vorher (provider/model) | Nachher | Verify |
|-------|--------|------|------------------------|---------|--------|
| 2026-07-10 | `76039d75e57d` | multi-agent-master-workflow-8h | null/null | minimax / MiniMax-M3 | ✅ dry-run ok |
| 2026-07-10 | `b1381735ce35` | orch-weekly-improve | (script-cron, paused) | resumed | ✅ state scheduled |

Zum Kopieren: für jeden gepinnten Job eine Zeile. Spalten helfen beim Diff zwischen Audit-Runden.

## Anti-Patterns

- ❌ `hermes config set model.provider ...` OHNE danach Cron-Audit — triggert den nächsten Drift.
- ❌ Bulk-Recovery-Script OHNE vorher Backup von `cronjob action=list` Output.
- ❌ `cronjob action=update schedule=""` — Tool-quits mit "Invalid schedule". Workaround: Schedule auslassen, dann separat updaten wenn nötig.
- ❌ Pinning mit veralteten Werten (z.B. `glm-5` von vor 2 Wochen) — Job läuft, ist aber wieder driften wenn der Provider weg ist.

## Verwandte Referenzen

- [`cron-error-categories.md`](cron-error-categories.md) — Category C (Provider Drift) im 3-Category-Model
- [`cron-debug-deepdive.md`](cron-debug-deepdive.md) — Generisches Cron-Debug-Workflow
- [`cron-debug-notes.md`](cron-debug-notes.md) — Frühere Debug-Notizen
- [`cron-duplicate-guard-pattern.md`](cron-duplicate-guard-pattern.md) — Wenn Bulk-Fixes Duplicate-Crons erzeugen
- [`model-provider-switch.md`](model-provider-switch.md) — Provider-Switch-Workflow inkl. Cache-Lag-Pitfall
- `devops/hermes-maintenance/references/config-drift-protection.md` — **Andere** Drift: externer Cron überschreibt config.yaml (nicht LLM-Cron-Pinning). Verwandt, aber klar zu unterscheiden.
- `devops/hermes-maintenance/SKILL.md` §11 (Kritische Pitfalls) — Kurzverweis auf diese Reference

## Mnemosyne-Integration

Vor dem nächsten `cronjob action=list` einmalig `mnemosyne_recall("cron pinning audit")` — liefert den letzten Audit-Stand und die Sonderfälle (z.B. OAuth-Provider). Das reduziert Audit-Zeit von 2-3 Minuten auf ~30 Sekunden.

**Beim Audit festgestellte Tatsache speichern:**

```python
mnemosyne_remember(
    content="Alle <N> LLM-Crons gepinnt (Audit YYYY-MM-DD): <job-list with provider/model>. "
            "Script-Crons drift-safe. Sonderfall <name> pinnt auf <oauth-provider>.",
    scope="global",
    source="fact",
    importance=0.85,
)
```

**Bestehender Mnemosyne-Cache:** ID `51462e7daa9535a2` (Audit vom 2026-07-10, alle 8 LLM-Crons grün, inkl. `minimax-oauth`-Sonderfall für `yuno-mittags-check`).
