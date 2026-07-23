# Kanban Diagnostics Recipes

> Session-tested recipes for diagnosing stuck/blocked Kanban tasks. Pair with the **Pitfalls** section in `SKILL.md` — these are the *how-to-verify* counterparts to the *what-goes-wrong* entries.

## Recipe 1: Why is a ready task not being dispatched?

```bash
# 1. Confirm the task is in 'ready' (not stranded somewhere else)
hermes kanban show <id> | head -5

# 2. Check the assignee field — empty = dispatcher can't spawn
hermes kanban show <id> | grep -E "assignee|status"

# 3. Check diagnostics on the active board
hermes kanban diagnostics
# Output flags 'stranded_in_ready' if assignee is null/missing

# 4. List ALL stranded tasks across boards (catch cross-board cases)
for board in $(hermes kanban boards list --json | jq -r '.[].slug'); do
  hermes kanban boards switch "$board" >/dev/null
  echo "═══ $board ═══"
  hermes kanban list --status ready
done

# 5. Verify the assignee profile actually exists
hermes profile list | grep "<assignee-name>"
```

**Root cause ranking** (from real Basti install, 2026-07-09):
1. `assignee` empty (25/25 ready tasks) — silent failure per spec
2. Profile exists but lacks description → auto-decompose blind (only matters if triage)
3. Profile model is `stopped` (Gateway indicator, NOT a spawn blocker — the spawn starts it on demand)
4. Workspace path invalid (rare; usually caught with clearer error)

## Recipe 2: Worker spawned but crashed in <60 seconds

```bash
# Find the per-task log
find ~/.hermes/kanban/boards -name "<task_id>.log" -path "*/logs/*"

# Most common cause: invalid skill pin (see Pitfalls in SKILL.md)
cat "$(find ~/.hermes/kanban/boards -name '<task_id>.log' -path '*/logs/*' | head -1)"
# Look for: 'Error: Unknown skill(s): ...'

# Verify the skill exists
hermes skills list | grep "<pinned-skill-name>"

# Three fixes (pick one):
hermes kanban edit <task_id> --skill <correct-name>     # rename
# OR remove the skill pin entirely (let worker derive from body)
# OR delete + recreate with corrected skill
```

**Other crash signatures** (less common):
- `'No module named ...'` → worker profile has wrong Python environment
- `'API key not set'` → profile config missing credential
- `'profile not found'` → assignee string typo (shouldn't happen — spec catches this)

## Recipe 3: Recovering a circuit-broken task

After `failure_limit` consecutive crashes, the dispatcher auto-blocks the task. To recover:

```bash
# Option A: Reclaim + retry with same profile (works if root cause fixed)
hermes kanban reclaim <task_id> --reason "fixed skill pin, retry"

# Option B: Reassign + retry with different profile
hermes kanban reassign <task_id> <different-profile> --reclaim

# Option C: If the task is no longer relevant, archive it
hermes kanban comment <task_id> "ARCHIVE: <reason>"
hermes kanban archive <task_id>

# Verify recovery
hermes kanban diagnostics
hermes kanban show <task_id>
```

## Recipe 4: Bulk-assigning 25+ stranded ready tasks

When you inherit a backlog of unassigned tasks (the "Phase 1" scenario):

```bash
# 1. Get the inventory first
hermes kanban list --status ready --json | jq -r '.[] | "\(.id)|\(.title)"' > /tmp/ready-tasks.txt

# 2. Categorize by board (different boards = different concerns)
for board in hermes system voice dashboard greyhack; do
  hermes kanban boards switch "$board" >/dev/null
  heres_kanban_assignments=$(hermes kanban list --status ready --json | jq -r '.[] | "\(.id) \(.title)"')
  echo "═══ $board ═══"
  echo "$heres_kanban_assignments"
done

# 3. Set profile descriptions FIRST (auto-decompose depends on it)
hermes profile describe yuno-coder --text "..."
# ... etc

# 4. Assign per-board (script the loop, but verify each manually before bulk-run)
# Pattern from 2026-07-09 run:
hermes kanban boards switch system >/dev/null
hermes kanban assign t_43934c0b yuno-coder
hermes kanban assign t_b7669543 yuno-coder
hermes kanban block t_a5e0398d needs_input "requires physical reboot"
hermes kanban boards switch voice >/dev/null
# ... etc

# 5. Verify with diagnostics — should now show no stranded_in_ready
hermes kanban diagnostics
```

## Recipe 5: Cleaning stale daemon files after 2026-07-02 spec change

The standalone `hermes kanban daemon` was deprecated in favor of gateway-embedded dispatcher. Stale `daemon.pid` files linger and confuse operators.

```bash
# Check for stale files
ls -la ~/.hermes/kanban/daemon.*

# If present and dated before 2026-07-02 → safe to remove
rm ~/.hermes/kanban/daemon.pid ~/.hermes/kanban/daemon.log

# Verify dispatcher is still configured
grep -A 5 "kanban:" ~/.hermes/config.yaml | head -10
# Expect: dispatch_in_gateway: true, dispatch_interval_seconds: 60
```

## Profile-description template

For each specialist profile, write a description that helps the auto-decomposer route correctly. Pattern that works (from Basti's 2026-07-09 setup):

```bash
# Engineer-type profile
hermes profile describe yuno-coder --text "Code-Implementierung, Refactoring, Bug-Fixes, Tests, Code-Reviews in ~/10-Projekte/. Primärsprachen: Python, Bash, JavaScript/TypeScript. Off-scope: Visual Design, Long-Form Writing."

# Vision/design profile
hermes profile describe yuno-vision --text "Visuelle Inhalte: Bilder (text-to-image), Diagramme (SVG/Excalidraw), UI-Mockups, Architektur-Sketches."

# Search/lookup profile
hermes profile describe yuno-flash --text "Bulk-Search, schnelle Lookups, parallele Datenakquise. Geschwindigkeit > Tiefe. Off-scope: Komplexe Analysen."

# Generalist fallback
hermes profile describe yuno --text "Generalist, Standard-Tasks, Fallback wenn kein spezifischer Profile passt. Hat Zugriff auf das volle Skill-Set."
```

## Coverage-map methodology

For any "how much of the spec are we actually using" question:

1. Read the spec reference (`~/.hermes/hermes-agent/website/docs/user-guide/features/kanban.md`)
2. Count distinct features (CLI verbs, lifecycle states, workspace kinds, advanced patterns)
3. Query each board's SQLite DB: `SELECT DISTINCT assignee FROM tasks`, `SELECT workspace_kind`, `SELECT goal_mode`, etc.
4. Cross-tabulate: feature × evidence × coverage %
5. Bucket into "fully used / partial / unused" with one-line justification each
6. Produce a phased install plan (Phase 0 = cleanup, Phase 1 = biggest ROI wins, etc.)

The full coverage-map template is in `~/docs/system/kanban-coverage-map-install-plan-2026-07-09.md` (Basti install, 51 tasks across 6 boards, ~40% baseline coverage).