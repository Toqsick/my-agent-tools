# Fullscan / Deep-Intel Template (Sub-Sub Workflow)

Use this template when the user asks you to "scan X completely",
"deep intel beschaffen", "vollscan mit bienen", or "alles zu Y
rausfinden" — comprehensive directory/application investigation with
parallel non-overlap bees.

## Core Pattern

```
Pre-Flight → Scope Division → N× (Parent + Sub-Sub) → Verification
```

## Pre-Flight Reconnaissance

Before dividing scopes, gather the lay of the land in a single
terminal batch (parallelise independent queries):

```bash
# Directory structure & sizing
du -sh "/target/path/"
du -sh "/target/path/"*/  | sort -rh | head -15
find "/target/path/" -maxdepth 3 -type d | sort

# File type distribution (config, code, binary, data, media)
find "/target/path/" -maxdepth 3 -name "*.yaml" -o -name "*.json" -o \
  -name "*.db" -o -name "*.src" -o -name "*.dll" -o -name "*.so" | head -30
ls -la "/target/path/"*.{db,json,yaml,sh} 2>/dev/null

# Notable items (subdirs with custom content, DB files, scripts)
du -sh "/target/path/"*/. 2>/dev/null | sort -rh
total_size=$(du -s /target/path | awk '{print $1}')

# Timestamp for side-effect files
TS=$(date +%s); echo "TS=$TS"
mkdir -p /tmp/scan-{alpha,beta,gamma,delta}
```

**Output:** a mental map of what's in the target, used to draw
non-overlapping scope boundaries for the bees.

## Scope Division Rules

- Every bee gets a **logically non-overlapping slice** of the target.
- If two bees would read the same files, merge or re-scope.
- Typical slices:
  - **Database/Data** — all structured data (SQLite, CSV, JSON dumps)
  - **Tools/Scripts** — user-authored code, deployment scripts
  - **Binaries/Internals** — compiled code, config files, DLLs, assets
  - **Diff/History** — multiple versions of the same data to compare
- Each slice must be independently verifiable (sub-sub can check
  without stepping on another bee's territory).

## Bee Briefing Pattern

Each bee in `delegate_task(tasks=[...])` follows this structure:

**Goal** (first sentence): one-line scope summary.
**Context** (second paragraph): target paths, vault paths, constraints.

**HAUPT-TASK** (numbered steps):
1. What to read/analyse
2. What NOT to do (no plaintext passwords, no writes outside paths)
3. Deliverable path (vault note Markdown): absolute path
4. Side-effect JSON (machine-readable): absolute path

**SUB-SUB-TASK** (SPAWNE Sub-Biene via delegate_task):
- What the sub must verify (independent cross-check)
- Sub deliverable path: same prefix + `-sub.md`
- Sub MUST write to absolute path, not choose its own

**Self-Report MUST contain:**
- sub_call_count
- Number of items scanned/processed
- Both file paths and sizes
- Verdict: Pass/Fail

### Non-Overlap Checklist

Before dispatching, check each pair of bees:
- [ ] No bee reads the same primary files as another
- [ ] No bee writes to the same vault note as another
- [ ] Side-effect JSON keys don't collide
- [ ] Sub-Sub verifications don't overlap

## Typical Scale

| Scope | Parent Time | Sub-Sub Time | Files Output |
|-------|-------------|--------------|-------------|
| 4 bees | ~260s total | ~90s each | 4 vault notes + 4 JSON + 4 sub reports |
| 6 bees | ~400s total | ~90s each | 6 vault notes + 6 JSON + 6 sub reports |

Budget: `2N` concurrent children. With default max 6: 3 bees covered
exactly. With max 8: 4 bees. Raise via `hermes config set delegation.max_concurrent_children <N>` if needed.

## Verification

```bash
# All side-effect files present?
ls -la /tmp/scan-*/<TS>*

# All vault notes deliverable?
ls -la "/home/bratan/Dokumente/Obsidian Vault/09 System-Doku/GreyHack/GreyHack-*-2026-07-*.md"

# Sub-Sub integrity (each sub should have confirmed independently)
for f in /tmp/scan-*/<TS>-sub.md; do echo "--- $f ---"; cat "$f"; done
```

## Example Briefing (Savegame Deep Dive)

```
SAVEGAME DEEP INTEL EXTRACTION with Sub-Sub-Cross-Verify.

HAUPT-TASK (du selbst):
1. Extrahiere VOLLSTÄNDIGE Daten aus der GreyHackDB.db (read-only!):
   - Alle N Tabellen mit kompletten Schemas
   - Players-Tabelle: kompletter Player-State
   - InfoGen: GameClock, Seed, DeleteVersion, Meta
   - Computer: alle IDs, IsRouter/IsPlayer, Hardware
   - Map: alle IPs, NetworkType, AccessType, Date
   - Passwords: N Einträge → NICHT Klartext! Nur Statistik
     (Längen-Verteilung, Char-Pattern, Top-Frequenzen)
   - MailAccounts, BankAccounts, WebPages, Logs, Files
2. Schreibe Deep-Intel-Report: /vault/path/Note-Name-2026-07-14.md
3. Side-Effect JSON: /tmp/scan-alpha/<TS>.json

SUB-SUB-TASK (SPAWNE Sub-Biene via delegate_task):
Sub-Biene führt unabhängigen Table-Count für alle N Tabellen aus.
Vergleicht mit Report-Counts.
Schreibt: /tmp/scan-alpha/<TS>-sub.md

Self-Report: sub_call_count, Tabellen, Passwort-Statistik, Files.
```

## Common Scope Cuts for Game/App Scans

| Scope | What It Covers | Example Side-Effect |
|-------|---------------|-------------------|
| Alpha | Structured data (DB, config) | Row counts, passwords stats |
| Beta | Custom/user-authored content | .src scripts inventory, //command audit |
| Gamma | Binary/config internals | DLL list, strings keywords, version info |
| Delta | Multi-version diff analysis | MD5 hashes, row diffs between versions |
| Epsilon | Media/assets | Image count, sizes, format distribution |
| Zeta | Network/external deps | Steam libs, plugin versions, web endpoints |

## Anti-Patterns

- **Overlapping scope** — two bees both reading the DB is wasted
  budget. Divide cleanly: Alpha gets all DB content, Gamma gets
  everything that ISN'T the DB.
- **No pre-flight** — dispatching blindly without `du -sh` and
  `find` first means you don't know the shape. Always recon first.
- **Too many bees** — more than 6 concurrent children hits the
  default budget wall. 4 is the sweet spot for comprehensive scans.
- **Bee writes to vault before queen confirms** — bees should write
  side-effect files, not vault notes directly if the queen wants
  to curate first. In our usage, bees DO write vault notes directly
  (Basti's flow: dispatch → verify → done). When in doubt, write
  to `/tmp/` first.
- **Sub-Sub for mechanical-only tasks** — sha256sum, ls, cp, grep
  are faster inline. Sub-Sub only pays off with reasoning or
  high-volume output.