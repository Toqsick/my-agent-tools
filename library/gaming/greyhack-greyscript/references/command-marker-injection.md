# `//command:` Marker Injection — Welle-2 Sweep Pattern

**Verified:** 2026-07-07 (Agent F in Bug-Fix-Schwarm Welle 2, 44 files, 44/44 OK)
**Audience:** Future wave-agents doing systematic `//command:` marker sweeps across the greyhack-tools repo.

This reference distils the operational pattern that worked end-to-end on the
44-file sweep. The umbrella skill (`greyhack-greyscript`) already references
`//command:` markers in its description and deployment sections; this file is the
"how do I actually run a sweep on N files" playbook.

---

## Why this exists

GreyHack's DB-injection deployment (see `references/deployment.md` and
`references/config-deployment.md`) treats files starting with `//command: <name>`
as standalone CLI commands. Files without that marker are not pickable as
commands — they're silently treated as libraries. The repo had ~80+ `.src`
files in various states of marker-coverage; Welle 1 swept a subset and missed
44. Welle 2 (this skill) closed the gap.

## What counts as a "standalone command" vs a library/sub-module/test

The repo has mixed conventions. Decision tree (used and verified):

**Standalone command (needs marker):**
- Lives directly under `greyhack-tools/<toolname>/<toolname>.src` AND
  implements a CLI/feature (has `params`, `exit("usage: ..."`, top-level body)
- Lives under `src/<category>/<name>.src` and is the entry point of a feature
- Lives under top-level `tools/<name>.src` and is meant to be invoked by name

**NOT a standalone command (skip even if no marker):**
- Anything under `*/libs/`, `*Test*`, `*test*.src`, `*examples/`
- `lib_*` files (e.g. `lib_core.src`, `listLib.src`, `Util.src`)
- Multi-class definitions like `attack_tiers.src`, `ransomeware.src` — they
  register multiple commands in one file via class metadata, single
  `//command:` is wrong
- Anything with no executable body (pure data table, pure import-only stub)

**Trap:** `minitest/runner.src` and `minitest/testApi.src` LOOK like standalone
files, but the runner is invoked via `minitest test <file>` so it's a sub-module
of `minitest.src`. **Welle 1's mistake was over-applying markers here.** Filter
by directory-prefix as well as by file basename.

## Detection script (one-liner)

Pre-flight scan before touching anything:

```bash
cd /home/bratan/10-Projekte/10-active/greyhack-tools
echo "=== ALREADY MARKED ==="
grep -rIl "^//command:" greyhack-tools/ src/ tools/ | sort
echo "=== NEED MARKER (candidates) ==="
for f in $(find greyhack-tools src tools -name "*.src" \
             -not -path "*/libs/*" -not -path "*/examples/*" \
             -not -name "*Test*" -not -name "*test*" \
             -not -name "lib_*" -not -name "listLib.src" \
             -not -name "attack_tiers.src" -not -name "ransomeware.src"); do
  first=$(head -1 "$f")
  if [[ "$first" != "//command:"* ]]; then
    echo "  $f  -> $first"
  fi
done
```

Always cross-check the output against the brief's file-list before starting —
agents have over-applied markers in past waves.

## Insertion algorithm (verified working on all 44 files)

```python
first_line = original.split("\n", 1)[0]

if first_line.startswith("//command:"):
    # Already marked — skip (or re-verify build)
    pass
elif first_line.startswith("//"):
    # COMMENT-BRANCH: prepend marker + blank line, keep original comment
    new_content = f"//command: {name}\n\n" + original
elif first_line == "":
    # Edge: empty file or starts with blank line
    new_content = f"//command: {name}\n" + original
else:
    # CODE-BRANCH: prepend marker + `// ===` divider header
    new_content = f"//command: {name}\n// ===\n" + original
```

**Why `// ===` for the code branch?** It visually separates the marker/header
from executable code, so subsequent human readers can see "here be the metadata,
here begins code". This matches the convention already used in newer files
(e.g. `src/tools/recon.src` line 1 = `//command: recon`, line 3 = banner).

**Why blank line for the comment branch?** Without the blank line, the original
banner comment visually fuses with the marker — humans (and grep-based
extractions) have to know the exact byte offset. One blank line is the canonical
separation in this repo.

## Name disambiguation (the trap nobody documents)

`greyhack-tools/portscan/portscan.src` and `tools/portscan.src` are TWO
different files both wanting `//command: portscan`. GreyHack's DB-index uses the
command name as a primary key — collision = one overwrites the other.

**Rule:** When two `.src` files have the same basename:
1. The one living under `greyhack-tools/<name>/<name>.src` gets the plain name.
2. The duplicate gets `<basename>_<dir_prefix>` (e.g. `portscan_main` for
   `tools/portscan.src`, `decypher_src` for `src/crypto/decypher.src`).

The brief in Welle 2 explicitly named this rule ("Bei Namens-Konflikten
(z.B. zwei Files mit gleichem basename): prefix mit Verzeichnis, z.B.
`portscan_main` für `tools/portscan.src`").

## Backup convention (cross-agent safe)

Other wave agents use `*.bak-agent-g-<TS>`, `*.bak-agent-h-<TS>`, etc. To not
clobber their backups:

```bash
TS=$(date +%Y%m%d-%H%M%S)
BACKUP="<file>.bak-agent-f-${TS}"
[ -f "$BACKUP" ] || cp -p "<file>" "$BACKUP"
```

The `cp -p` preserves mtime so backups from different agents don't show the
same timestamp. The `bak-agent-X-` prefix lets future forensics tell which
agent touched which file.

**Pre-flight check** before any sweep:
```bash
find . -name "*.bak-*" -mmin -120 | head -30
```
If backups are landing right now, another agent is mid-flight on overlapping
files. Either wait or coordinate.

## Build verification

After every edit, run:

```bash
greybel build <file> /tmp/build-agent-X/<basename>/build -dbf 2>&1 | tail -2
```

`-dbf` (disable build folder) writes the artefact directly to the output dir
without a `build/` subdir — keeps the temp tree flat and findable. Save outputs
to `/tmp/build-agent-X/<basename>/build` so a final `OK=44 FAIL=0` summary
loop can sweep them all in one pass:

```bash
FAIL=0; OK=0
for entry in "${FILES[@]}"; do
  file="${entry%%:*}"; name="${entry##*:}"
  result=$(greybel build "$file" "/tmp/build-agent-X/${name}/build" -dbf 2>&1 | tail -2)
  if grep -q "Build done" <<< "$result"; then
    OK=$((OK+1))
  else
    FAIL=$((FAIL+1)); echo "FAIL: $file -> $result"
  fi
done
echo "OK=$OK FAIL=$FAIL"
```

**Pitfall — transient dependency-resolver flakiness:** During Welle 2's sweep,
one file (`greyhack-tools/auto_exploit/auto_exploit.src`) emitted
`FAIL rc=1: Dependency …/home/Bratan/bin/lib_core does not exist` on the
first pass but built clean on immediate re-run. The greybel CLI has a known
flaky dependency-walk on cold cache. **Always do a final re-verify pass on
files that failed once before logging them as broken.** Mark the report as
"OK (Re-Verify)" so future readers know the failure was transient.

## End-to-end script outline

The full Agent-F script is at `/tmp/agent-f-process.py` (created during the
sweep). It does:
1. Loop the brief's file list
2. Backup per-file with `*.bak-agent-f-<TS>`
3. Apply the insertion algorithm
4. Run `greybel build` for verification
5. Emit a Markdown report to `/tmp/fix-report-agent-f.md`

Adapt the FILES list and backup prefix per agent (`agent-g`, `agent-h`, …) and
the same script runs again.

## Output report structure (what future waves will read)

```
# Agent X — Welle 2 Bug-Fix-Schwarm Fix Report

## Ergebnis-Summary
- N von N Files erfolgreich bearbeitet
- 0 Files bewusst übersprungen (oder list why)
- 0 Conflicts

## Pro File: Befund + Eingriff + Build-Result
| File | Command-Name | Aktion | Build-Result |

## Bewusst übersprungen
- (keine) or list reasons

## Edge-cases / Beobachtungen
- Comment-Branch / Code-Branch counts
- Name-disambiguation decisions
- Cross-agent backup observations

## SENTINEL: ##AGENT_X_DONE##
```

The sentinel line is what the orchestrator greps for to confirm agent
completion. Without it, downstream agents don't know you're done.

## Known adjacent skills / references

- `references/deployment.md` — DB-injection deployment, why `//command:` matters
- `references/config-deployment.md` — config schema
- `references/greyhack-bug-scan-2026-07-07.md` — related wave-2 sibling sweep
- `references/static-scan-false-positives-2026-07-07.md` — false-positive patterns
  to avoid when classifying libraries vs commands