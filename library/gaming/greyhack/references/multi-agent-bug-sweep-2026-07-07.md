# Multi-Agent Bug-Scan Sweep Workflow (2026-07-07)

## Trigger

User asks "fix all bugs" / "schwarm drüber" / "auto-fix sweep" / "welle N go". Class of task = large-scale static-pattern + build-failure sweep across `~/10-Projekte/10-active/greyhack-tools/` oder vergleichbare Multi-Module Repos.

## 5-Phasen-Pattern (proven 2026-07-07, 2 PRs #56+#57, 41→66/66 OK)

### Phase 0 — Inventur (parent-direct, ~30-60s)

- `git ls-files '*.src' | grep -v -E "^(tests/|imports/|build/|greybel-vs/|\.ci-build/)"` — Track active files
- Static-Scan: alle 14 Pattern-RegEx über ALLE Files, **KEIN Top-N-Cutoff** (sonst Coverage-Gap wie Sub-Agent A 2026-07-07 mit lzw/lzw + lzw/test)
- `bash scripts/ci-build.sh` ausführen, alle Failures sammeln
- **5-Kategorien-Klassifizierung** der Failures (siehe unten)
- Library-Filter explizit pflegen — siehe Library-Filter unten

### Phase 1 — Library-Filter (Pitfall #5)

Bei "missing //command: marker" Sweeps: Library-Filter MUSS enthalten:
`lib_core`, `listlib`, `util.src`, `core/`, `recon_lite`, `tests/test_`, `cli_core`, `libcore`, `buildcore`, `netcore`, `debugcore`, `filecore`, `cliFeedback`, `lzw/`, `xmem`, `minitest/libs/`, `minitest/examples/`, `fix_perms`, `attack_tiers`, `ransomeware`, `install`, `installer/`, `libcore`.

### Phase 2 — Schwarm-Dispatch

NON-OVERLAPPING Sub-Agent-Scopes (Pitfall #4): jeder Agent bekommt vollständige File-Liste für SEIN Pattern. Mehrere Agents auf gleicher File = Race-Condition (Parent-Direct eingreifen wenn entdeckt).

Jeder Agent-Briefing MUSS enthalten:
1. Backup-Pflicht (`cp <file> <file>.bak-$(date +%Y%m%d-%H%M%S)`)
2. Verifikations-Pflicht (`greybel build` exit-code)
3. **Pflicht-Output-Pfad** für Report (z.B. `/tmp/fix-report-agent-X.md`)
4. **Sentinel-Token** am Ende (`##AGENT_X_DONE##`) — fehlend = Truncation (Pitfall #13)
5. **Pitfall #13 Mitigation:** Master prüft am Ende Sentinel + Backup-Files vorhanden, nicht nur Report lesen

### Phase 3 — Master-Verify (parent-direct)

- `git status --short` zeigt alle geänderten Files
- `bash scripts/ci-build.sh` zeigt aktuellen Build-Status
- Sentinel-Check: `grep "##AGENT_X_DONE##" /tmp/fix-report-*.md` — fehlende Sentinels = Truncated Agents
- Backup-Check: fehlende `.bak-*` Files bei erwarteten Changes = Agent hat nicht gearbeitet

### Phase 4 — Commit + Push + PR

- `git checkout -b fix/sweep-<datum>` + `git add -A` + commit + push + `gh pr create`
- PR-Body mit Pattern-Tabelle vorher/nachher, Files-geändert-Stat, Sub-Agent-Summaries

## 5-Kategorien-Build-Fail-Klassifizierung (Pitfall #6)

| Kategorie | Error-Signature | Behebung |
|-----------|----------------|----------|
| **Pattern-bug** | `no matching open if block`, `got Keyword`, `unexpected token` | String-in-String, ternary, einzeiliges-if etc. |
| **Import-resolution** | `Dependency ... does not exist` | In-Game-Pfad → relativer Repo-Pfad |
| **API-not-found** | `undefined function`, `Path "X" not found` | Funktion/Symbol existiert nicht in GreyScript |
| **Type-mismatch** | `got Identifier where ... required` | **NICHT Pattern-Fail!** String-in-String-Concatenation ohne `+` |
| **Mock-env-only** | `Path "wget" not found in map` | nur in greybel Mock, im echten Game OK |

**Bei "other" immer manuell 5+ Zeilen Kontext schauen** — Sub-Agent-Briefings können falsch diagnostizieren (Welle 2: 3 von 3 Briefs waren teilweise falsch → Sub-Agenten mussten improvisieren).

## 6 Sub-Agent-Fallen (proven 2026-07-07)

1. **Coverage-Gap** — Cutoff-Limits vermeiden, alle Files listen
2. **Filter zu aggressiv** — Briefings ohne "Top-N" formulieren
3. **Report-Truncation** — Sentinel-Check als Pflicht
4. **Race-Condition** — non-overlapping File-Listen, sonst Parent-Direct
5. **Library-Filter zu eng** — Inventur-Filter prüfen vor Dispatch
6. **Fehldiagnose** — 5+ Zeilen Kontext vor Fix-Entscheidung