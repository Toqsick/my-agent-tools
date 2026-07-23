# Bug Fix History & Auto-Fixers

## Fixes Applied (2026-06-17)
| File | Fix | Pattern |
|------|-----|---------|
| `alias-cli/alias.src` | `globals.sh/pc` → local `shell/pc` | NP-05 |
| `alias-cli/alias.src` | `globals.sh.build` → `shell.build` | NP-05 |
| `dankestein/secure.src` | Single quotes → escaped | NP-02 |
| `lib_core/lib_core.src` | `is_folder` → `is_binary` | NP-09 |
| `scp_upload/scp_upload.src` | `is_folder` → `is_binary` | NP-09 |
| `decypher_v3.src` | `get_shell.host_computer` 4x → once `pc = shell.host_computer` | NP-04 |
| `portscan/portscan.src` | Escaped quotes → simple quotes | NP-02 |
| `xmem/xmem.src` | 3x unclosed if-blocks repaired, 8x bare exit -> exit(), 6x get_shell.host_computer cached | NP-20 |
| `src/filecore.src` | Merge conflict removed, orphaned fragments fixed, is_folder -> is_binary, single-line if/then/end if -> multi-line, ternary -> if/else | NP-18, STRUCT |

## xmem Fix (2026-06-24 — BREAKTHROUGH)
`get_shell(username, password)` → `get_shell`. GreyScript's `get_shell()` takes zero parameters. The xmem tool was broken for 2+ weeks because of `shell = get_shell(username, password)` at line 186. Fix: use `user_input()` separately for credentials, then authenticate via the Shell object methods.

## Python Auto-Fixer: single-line if/then/end if (proven 2026-06-25)

When 80+ files all have the same P0 pattern, manual editing is too slow. Script: `scripts/fix-single-line-if.py`.

```python
import re
SINGLE_LINE_IF = re.compile(
    r'^([ \t]+)(if\b.+?\bthen\b)(.+?)(\bend if\b)\s*$',
    re.IGNORECASE
)

def fix_file(path):
    text = path.read_text()
    lines = text.split('\n')
    out = []
    fixes = 0
    for line in lines:
        m = SINGLE_LINE_IF.match(line)
        if not m:
            out.append(line)
            continue
        indent, head, body, tail = m.groups()
        body = body.strip()
        new_block = f"{indent}{head}\n{indent}\t{body}\n{indent}{tail}"
        out.append(new_block)
        fixes += 1
    if fixes:
        path.write_text('\n'.join(out))
    return fixes
```

**Key learnings:**
- Regex uses `[ \t]+` not `\t+` because some files (grsa_v2, hardening) use 4-space indent
- Idempotent — re-running produces 0 fixes
- Does NOT handle `if X then A; B end if` (multi-statement bodies) — those need manual review
- Does NOT handle inline-if `("X" if cond else "Y")` — separate manual fix
- **Validated output:** 81 fixes across 13 files in a single run for PR #29

## Import Path Fix Method (regex)

When fixing `import_code` paths across many files with Python `re.sub`, be careful with trailing parens:

```python
# WRONG — creates double parens:
content = re.sub(r'import_code\("..."\)', 'import_code("..."))', content)  # extra )!

# CORRECT — match the full pattern including trailing paren, replace cleanly:
content = re.sub(r'import_code\("..."\)\)', 'import_code("...")', content)

# CORRECT — simpler: just replace the path inside the parens:
content = re.sub(r'import_code\("[^"]*"\)', 'import_code("lib_core")', content)
```

Or use sed after build (safer):
```bash
sed -i 's|import_code("../lib_core/lib_core.src")|import_code("lib_core")|g' bin/*.src
```

## Multi-Agent Auto-Fix Pipeline (2026-06-23)

`greyhack-auto-fix.sh` — Automatische Bug-Fixing-Pipeline inspired by TheMorpheus407's the-dmz Projekt. Orchestriert 4 spezialisierte AI-Agenten (Research → Implement → Review A/B → Finalize) über `hermes chat -q`. Alle Rollen mit `openrouter/owl-alpha` (0€).

```bash
./greyhack-auto-fix.sh --bug 1        # Bug fixen
./greyhack-auto-fix.sh --list         # Bugs anzeigen
./greyhack-auto-fix.sh --bug 1 --dry-run  # Nur Research
```

Details: `references/auto-fix-pipeline.md`

## Pre-Scan Pattern: Python Pattern-Scan vor 3-Expert-Audit (2026-07-02)

Wenn ein Multi-Agent-Audit über die GreyHack-Toolbase laufen soll, **NICHT** die 3 Subagents selbst alle 100+ Files scannen lassen. Das verbrennt API-Calls und produziert Lücken.

**Stattdessen:** Parent macht deterministischen Pre-Scan via `execute_code` (Python+regex), filtert auf echte Pattern-Matches, und gibt dem P0/P1-Bug-Hunter-Subagent NUR die kuratierte Treffer-Liste zum Verifizieren.

### Workflow (proven 2026-07-02 mit GreyHack 102 .src-Files, 236 Matches, 36 P0)
1. **Parent Phase 0**: `python3 ~/docs/greyhack-audit-2026-07-briefings/04-pre-scan-script.py` → `pre-scan-results.md`
2. **Parent Phase 1**: Spawn 3 Subagents mit Briefings aus `01-expert1-codebase.md`, `02-expert2-build.md`, `03-expert3-bugs.md`
3. **Expert 3 Briefing enthält explizit**: "PRE-SCAN-PFAD: `~/docs/greyhack-audit-2026-07-briefings/pre-scan-results.md`. Wenn diese Datei nicht existiert, ABBRUCH und melden."
4. **Expert 3 MAX 8 calls** (statt 12): verifiziert nur die Pre-Filter-Liste, kein eigener Scan
5. **Parent Post-Spawn**: Realitäts-Check gegen `wc -l` der SKILL.md-Dateien + Pattern-Re-Grep auf den Top-3-Treffern

### Top-Treffer aus 2026-07-02 Scan
| Pattern | Severity | Files | Hits | Beispiel |
|---|---|---|---|---|
| `is_folder` (NP-21) | P0 | 9 | 22 | `lib_core/`-Tools |
| `is_binary` als Folder-Check (NP-30) | P1 | 13 | 20 | oft in scan-Listen |
| Single Quotes (NP-19) | P1 | 19 | 34 | String-Konstruktionen |
| Password als CLI-Param (NP-51) | P1 | 12 | 123 | Tools mit Auth |
| `get_shell(user, pass)` (xmem-Bug) | P0 | 2 | 2 | Regressions-Risiko |
| `HTTP.Request` (NP-N2) | P0 | 3 | 7 | NIEMALS kompilierbar |

### When NOT to use Pre-Scan
- Tool ist brandneu und Pattern-Set kennt es noch nicht → Subagent muss selbst scannen
- Pattern-Set selbst ist veraltet (>30 Tage seit letztem Update) → erst Pattern-Set refreshen
- Aufgabe ist nicht "find bugs in codebase" sondern "refactor tool X" → direkter Parent-Modus reicht

Reference: `~/docs/greyhack-audit-2026-07-briefings/` (3 Subagent-Briefings + Pre-Scan-Script + Verifikations-Checkliste, Master-Plan `00-parent-plan.md`)

## Operational Lessons (2026-06-17)

### Sub-Agent Batch Size for Tool Documentation
- **Max 5-8 tools per sub-agent** (not 15-20)
- 15+ tools per agent → timeout after 10min with only 6-10 API calls completed
- **Better approach**: Do it yourself in small batches of 5-6 tools, or dispatch multiple sub-agents with 5 tools each

### Write_file Size Limit
- `write_file` calls with >8K tokens of content cause stream timeouts
- Break large READMEs into multiple smaller writes or use `patch` for incremental additions
- Bug reports: Keep the full report under ~300 lines. Use condensed table format for known patterns.
