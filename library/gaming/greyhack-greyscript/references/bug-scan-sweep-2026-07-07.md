# Bug-Scan Sweep Lessons — 2026-07-07

> **Source session:** 78 aktive `.src`-Files, 8 Sub-Agenten in 2 Wellen, 2 PRs (#56 + #57) gemerged nach main (commit `b200313`).
> **Build-Result:** 41/66 fake-grün → 47/66 ehrlich (Welle 1) → 71/71 OK (Welle 2).
> **Use case:** Reproduction recipe + pitfalls for the NEXT multi-agent `.src` bug sweep on any greyhack-tools-style repo.

## 14-Pattern Static-Scan Coverage

The full pattern list that caught 100% of the build-breakers across 78 files (78 active, 47 OK at baseline):

| # | Pattern | Regex | Severity |
|---|---------|-------|----------|
| (a) | one-line `if X then Y end if` | `\bif\b.*\bthen\b.*\bend\s+if\b` | 🔴 CRITICAL (Build-Breaker) |
| (b) | ternary `X if C else Y` | `\bif\b.*\belse\b` (skip `else if` chains) | 🔴 CRITICAL |
| (c) | `\n` statt `char(10)` | `\\n` in string context | 🔴 CRITICAL |
| (d) | single-quote `'text'` in CODE | `'[^']*'` then classify (skip if inside `print(...)`) | 🔴 CRITICAL |
| (e) | inline-if assignment `X = (Y if C else Z)` | `=\s*\(.*\bif\b.*\belse\b` | 🔴 CRITICAL |
| (f) | `\` in strings (no `char(34)` workaround) | `\\"` not followed by `char(34)` | 🔴 CRITICAL |
| (g) | `===` separator line | `^=+\s*$` (convert to `// ===`) | 🔴 CRITICAL |
| (h) | `[^N]` negative index | `\[\^-?\d+\]` | 🔴 CRITICAL |
| (i) | `.strip()` / `.trim()` (GreyScript has none) | `\.(strip\|trim)\b` | 🔴 RUNTIME CRASH |
| (j) | `str_repeat()` | `\bstr_repeat\b` | 🔴 RUNTIME |
| (k) | `get_system_time()` | `\bget_system_time\b` | 🔴 RUNTIME |
| (l) | `HTTP.Request()` | `\bHTTP\.Request\b` | 🔴 RUNTIME (use `pc.wget` instead) |
| (m) | `require_shell` self-recursion | `pc\s*=\s*require_shell\s*\(` count > 1 | 🔴 CRITICAL |
| (n) | NO `//command:` marker | first line doesn't start with `//command:` | ⚠️ DEPLOY-BLOCKER (only for standalone commands) |

**Real-world findings (78 files):** (a)=40, (d)=16, (f)=4, (i)=4, (l)=4, (b)=1. Pattern (n) had 76 hits but most were libs/tests (filter needed — see Pitfall 2 below).

## 6 Sub-Agent Pitfalls (proven, 8 agents × 78 files = 6240+ agent-tool-calls)

### Pitfall 1: Static-Scan Coverage-Gap with Top-N Cutoff

**Symptom:** Sub-Agent A fixte nur die Top-7 Pattern-(a)-Files (nach Fund-Anzahl sortiert). 2 weitere Files mit je 1 Fund (`lzw/lzw.src`, `lzw/test.src`) blieben ungefixt und tauchten erst im CI-Build als Fail auf.

**Briefing-Disziplin:** "ALLE Files, keine Cutoffs, keine Filter" — Top-N ist nur für Reporting, nicht für Verarbeitung.

```python
# FALSCH — Cutoff-Limit:
top_offenders = sorted(results, key=lambda x: -x['count'])[:20]
# RICHTIG — Alle listen:
all_files_with_patterns = sorted(results, key=lambda x: -x['count'])
```

### Pitfall 2: Filter-Heuristik zu eng (Library vs Standalone)

**Symptom:** Erste Library-Heuristik listete 38 Missing-`//command:`-Marker; zweite Iteration (breitere Heuristik) ergab 44.

**Maintainer Liste in Briefings fest einbacken:**

```python
library_indicators = [
    'lib_core', 'listlib', 'util.src', 'core/', 'recon_lite',
    'tests/test_', 'cli_core', 'libcore', 'buildcore', 'netcore',
    'debugcore', 'filecore', 'cliFeedback',
    'lzw/', 'xmem',
    'minitest/libs/', 'minitest/examples/',
    'fix_perms', 'attack_tiers', 'ransomeware',
    'install', 'installer/', 'libcore',
]
# NICHT in den Filter: alle top-level Tools
```

### Pitfall 3: Sub-Agent-Fehldiagnose bei Folgefehlern

**Symptom:** Briefing sagte "wifi_crack L47: unbekannte `step()` Funktion". Sub-Agent H hat's richtig diagnostiziert: `step` IST in `lib_core.src:49` definiert — der genuine Bug waren 2 fehlende `)` in unclosed `render([...])`-Blocks. Der Parser lief rekursiv bis L47 und reklamierte `step` als unerwartetes Token.

**Briefing-Disziplin:** "unbekannte Funktion"-Meldungen können Folgefehler sein. Bei "got Identifier/Keyword at line N" immer **5+ Zeilen VOR N prüfen**, nicht nur die genannte Zeile.

**Real-world: list-lib/tests.src:** Briefing sagte "falsche each() API". Echter Bug: greybel-js parst Inline-`obj.method(function(...)body end function)` als rechtsseitige Wertzuweisung grundsätzlich NICHT. 5 Blöcke mussten zu `name = function(...); body; end function; obj.method(name)` umgebaut werden.

### Pitfall 4: Race-Condition zwischen Sub-Agenten auf gleicher File

**Symptom:** Sub-Agent A (Pattern a) und Sub-Agent D (Pattern i) bearbeiteten beide `password_generator.src`. D's Briefing sagte "out-of-scope", A's war unklar. Parent musste eingeschreiten.

**Briefing-Disziplin:** NON-OVERLAPPING File-Listen pro Sub-Agent. Cross-Check: jeder Sub-Agent gibt am Ende "Files touched" aus, master summiert und prüft overlap.

### Pitfall 5: Static-Scan übersieht String-in-String-Concatenation

**Symptom:** 3 Build-Fails zeigten `got Identifier[X:Y - X:Y+10: value = 'WORD'] where any of ",", ")" is required`. Das ist String-in-String-Concatenation ohne `+` Operator — `print("via "metaxploit":")` — der statische Pattern-Scan mit `\bif\b` etc. erwischt das NICHT.

**Brauche spezifischen Regex:**
```python
re.search(r'"[^"]*"[a-zA-Z_][^"]*"', line)  # zwei " ohne + zwischen
```

**Fix:** `char(34)` oder String-Concatenation mit `+`:
```greyscript
// FALSCH:  print("Adressen (via "metaxploit"):")
// RICHTIG: print("Adressen (via " + char(34) + "metaxploit" + char(34) + "):")
```

### Pitfall 6: CI-Bug NP-99 — Bash-Exit-Code-Falle

**Symptom:** CI-Script brach nach dem ersten File ab und loggte "Build done" obwohl 65/66 Files nie gebaut wurden. Monatelang nicht entdeckt weil CI "grün" meldete.

**Root cause:**
```bash
set -euo pipefail
BUILT=0
for f in files; do
    if greybel build "$f" "$t" 2>/dev/null; then  # 2>/dev/null schluckt Errors
        ((BUILT++))                                # CRASH wenn BUILT=0: "value is 0"
    fi
done
```

**Fix:**
```bash
err_log="$(mktemp)"
if greybel build "$f" "$target" 2>"$err_log"; then
    ((++BUILT)) || true          # pre-increment, exit-code neutralisiert
else
    head -3 "$err_log" | sed 's/^/        /'  # show first error lines
    ((++FAILED)) || true
fi
rm -f "$err_log"
```

**Hinweis:** Auf main-Branch wurde das Problem parallel mit Issue #28+#30 fundamental anders gelöst (komplett neues ci-build.sh mit Pass/Fail-Liste + Tee-Logging). Der NP-99-Fix war obsolet sobald gemerged, aber Wissen bleibt wertvoll für Custom-CI-Scripts.

## 5-Kategorien Build-Fail Klassifizierung

Am Ende jedes Static-Scan die Failures kategorisieren:

| Kategorie | Beispiel-Error | Fix-Typ |
|-----------|---------------|---------|
| **Pattern-bug** | `got Keyword`, `no matching open if block`, `unexpected token` | Inline-expand / char()/ etc. |
| **Import-resolution** | `Dependency ... does not exist` | Relative Pfade + Stub-Files |
| **API-not-found** | `undefined function`, `Path "X" not found` | Stub-Function oder Refactor |
| **Type-mismatch** | `got Identifier where ...` | String-Concatenation ohne `+` |
| **Mock-env-only** | `Path "wget" not found in map` | Kein Fix nötig (nur in greybel Mock, nicht im echten Game) |

## PR-Merge-Strategie bei CONFLICTING PRs

**Symptom:** PR wurde erstellt, später `mergeable: CONFLICTING`. Grund: main ist seit Branch-Start voraus (parallele Merges).

**Workflow:**
```
1. PR-Diagnose: gh pr view <N> --json mergeable,baseRefName
2. Bei CONFLICTING: git rebase origin/main (linear history, weniger Konflikte)
3. git push --force-with-lease (sicherer als --force, checkt remote-State)
4. PR ist jetzt MERGEABLE → gh pr merge <N> --squash --delete-branch
5. Working-Tree: git checkout main && git pull
```

**Bei Path-Mismatch (z.B. `src/core/filecore.src` vs `src/filecore.src`):**
Rebase detected das meistens (git behandelt sie als separate Files). Falls manuelle Konflikte: `git checkout --theirs` oder `--ours` pro File und dann Edit.

**Real-world:** Welle 2 Branch hatte 8 commits sauber rebased auf origin/main ohne Konflikt. `--force-with-lease` chckte dass remote-branch nicht zwischenzeitlich überschrieben wurde.

## Empfohlener Workflow (proven)

```
1. Phase 0 Inventur (parent-direct, 30-60s):
   - git ls-files '*.src' | filter (active + tracked, exclude tests/imports/build/greybel-vs/.ci-build)
   - Static-Scan ALLE 14 Patterns (KEIN cutoff!)
   - Build-Run, alle Failures sammeln
   - 5-Kategorien-Klassifizierung
   - Library-Filter mit aktualisierter Liste (Pitfall 2)
   - NON-OVERLAPPING Sub-Agent-Scopes definieren (Pitfall 4)

2. Schwarm-Dispatch:
   - N Sub-Agenten, jeder mit KOMPLETTER File-Liste für sein Pattern
   - JEDER Sub-Agent: Backup + Edit + Verify + Report + Sentinel (`##AGENT_X_DONE##`)
   - Backups via .bak-TIMESTAMP, in .gitignore abgedeckt

3. Master-Verify (parent-direct):
   - git status --short zeigt alle geänderten Files
   - CI-Run zeigt aktuellen Build-Status
   - 5-Kategorien-Re-Check: was ist grün geworden, was nicht?
   - Sentinel-Check: fehlende Reports = Truncated Agents, neu dispatchen

4. Vor Push: `gh pr view <N> --json mergeable` (Pitfall-Mitigation)
   - Bei MERGEABLE: direkt pushen
   - Bei CONFLICTING: rebase + force-with-lease
```

## Verwandte Skill-References

- `references/yuno-viper-build-breaker-audit-2026-07-04.md` — Pattern-(a)-Audit für 5 Viper-Module (142 Funde in <30s)
- `references/build-pipeline-ci-quirks.md` — greybel -u / -dbf flag effects
- `references/build-ci-fix-2026-06-19.md` — Batch-Fix einzeiliger ifs
- `references/p0-pattern-reference-2026-06-25.md` — Auto-Fix-Strategie (Original)
- `references/cross-module-verification.md` — Post-Build-Checks

— Yuno für Basti, 2026-07-07