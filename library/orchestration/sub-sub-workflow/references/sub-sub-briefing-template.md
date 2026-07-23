# Sub-Sub Briefing Template

Copy-paste template for one parent task in a `delegate_task` `tasks=[...]` array.
Each parent needs its own template instance with `<placeholders>` filled in.

## When to Use

Use this template verbatim inside a `delegate_task` goal string when you want
a parent subagent to delegate a sub-subagent whose work you can verify
afterwards via a side-effect file on disk.

## Prerequisites

- Skill: `sub-sub-workflow`
- Config: `delegation.max_spawn_depth >= 2`
- Config: `delegation.orchestrator_enabled: true`
- Role on parent: `orchestrator` (NOT the default `leaf`)
- Toolsets on sub-sub at minimum: `terminal`, `file`

## Template

```
SUB-SUB-DISPATCH-TEST (verifiable via side-effect files).

Hauptdatei (your deliverable):
  /tmp/<prefix>/<ts>.<ext>
  Format hint: <one-line description of expected content>

Sub-Sub-Datei (sub-bee deliverable, proves the spawn happened):
  /tmp/<prefix>/<ts>-sub.<ext>
  Format hint: <one-line description of expected content>

Workflow:
1. Do the parent task first. Write the Hauptdatei.
2. THEN spawn exactly one sub-bee via delegate_task. Pass it:
   - the same prefix and timestamp
   - a clear single-file deliverable at /tmp/<prefix>/<ts>-sub.<ext>
   - role='leaf' is fine for the sub itself; what matters is
     that you (the parent) keep delegate_task in your toolset.
3. If /tmp/<prefix>/<ts>-sub.<ext> is missing after your work,
   you did NOT delegate. Retry with:
     delegate_task(goal='...', toolsets=['terminal','file'])

Self-Report MUST include:
  - sub_call_count (how many delegate_task calls you made)
  - both file sizes in bytes
  - both file paths (absolute)
  - a Lohnt-sich-Bewertung line (yes/no + one-sentence reason)
```

## Placeholders

- `<prefix>` — short tag identifying this run, e.g. `sub-sub-test-2026-07-14`
- `<ts>` — Unix timestamp from `date +%s` at the moment of dispatch
- `<ext>` — file extension (`json`, `md`, `txt`, `csv`, ...)

## Variants

For hash-verifiable sub-output, set `<ext>` to `txt` and ask the sub to
write one line per entry in `<sha256>  <path>` format. The parent can
then run `sha256sum` against the same paths and confirm byte equality.

For inventory data, set `<ext>` to `json` and require the sub to write
a JSON array of objects with stable keys. The parent can `jq` the file
to validate shape.

For markdown reports, set `<ext>` to `md` and require a markdown table
header plus at least one data row.

## Anti-Patterns

- Naming the sub-deliverable the same as the parent deliverable. The
  parent will overwrite the sub-file when it finishes its own task.
  Use the `-sub` suffix to keep them distinct.
- Forgetting the explicit "if missing you did not delegate" sentence.
  Subagents will silently skip the spawn when their toolset strips
  `delegate_task` (default for `role='leaf'`). The explicit retry
  hint is the difference between a clean failure and a silent skip.
- Letting the sub choose its own output path. If parent and sub pick
  independent paths, file collision and drift become hard to spot.
  Pin both paths in the parent's goal.