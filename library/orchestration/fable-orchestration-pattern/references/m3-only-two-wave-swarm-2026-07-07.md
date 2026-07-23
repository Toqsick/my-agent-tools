# M3-Only Two-Wave Swarm — GitHub Audit Session (2026-07-07)

## Session-Daten
- **Datum:** 2026-07-07
- **Pattern:** Variante C (M3-Only Two-Wave Scout→Execute)
- **Modell:** MiniMax-M3 (glm-5.2 als Queen)
- **Kosten:** $0.00 (kein Fable-Call nötig)
- **Dauer:** Wave 1 = 4m14s (5 Bienen), Wave 2 = ~3 Min (3 Bienen)

## Wann M3-Only statt Fable→M3?

Wenn die Aufgabe **keine strategische Judgment** braucht, sondern systematische Erfassung + prioritisierte Ausführung:
- GitHub-Audits (Issues, PRs, Branches, Hygiene)
- Repo-Inventuren
- Code-Scans (Pattern-Matching, Metriken)
- File-Tree-Analysen

Fable wird überflüssig wenn die "Strategie" einfach aus "sammle Fakten → priorisiere → User wählt" besteht.

## Wave 1: Read-Only Scout (5 Bienen parallel)

| Biene | Aufgabe | API-Calls | Dauer | Output |
|-------|---------|-----------|-------|--------|
| 🐝1 | Issue-Triage (greyscripts) | 12 | 147s | 7 Issues kategorisiert (nicht 54 — alte Zahl war falsch) |
| 🐝2 | PR-Review (hermes-v7 #7+#8) | 20 | 255s | 2 PR-Analysen + Cross-Konflikt-Matrix |
| 🐝3 | Branch-Cleanup-Scan (5 Repos) | 12 | 213s | 46 Branches, 0 stale, 11 WARN |
| 🐝4 | Repo-Archiv-Scan (30 Repos) | 5 | 53s | 5 archivierbar (alle Forks) |
| 🐝5 | Hygiene-Audit (Top-5) | 7 | 209s | 6×5 Matrix, 12 Gaps |

**Total:** 56 API-Calls, 261s, 5 strukturierte Reports.

### Queen-Konsolidierung
- 5 Reports → 1 Masterplan mit 🟥🟧🟨🟩 Priorisierung
- ⭐⭐⭐ Bewertungssystem (Nutzen vs. Aufwand)
- 3 Quick-Win-Optionen (A/B/C) für User zur Auswahl

### Bewährter Konsolidierungs-Format

```markdown
## 🟥 P0 — Sofort (blockiert oder rechtlich kritisch)
### P0-1: [Titel] ⭐⭐⭐ (Zeit, kostenlos)
**Warum:** [Begründung]
**Fix:** [Lösung]

## 🟧 P1 — Diese Woche
### P1-1: [Titel] ⭐⭐⭐ (Zeit)
...

## 🟨 P2 — Nice to Have
...

## 🟩 P3 — Wenn mal Zeit ist
| Task | Aufwand |
```

## Wave 2: Write-Execute (3 Bienen parallel, nach User-Freigabe)

User wählte "A+B" aus 3 Optionen (A=LICENSE, B=Archivieren, C=MCP-Token).

| Biene | Aufgabe | Mutation |
|-------|---------|---------|
| 🐝1 | LICENSE → MaxClaw (public) | `gh api` file create |
| 🐝2 | LICENSE → 3 private Repos | `gh api` batch |
| 🐝3 | Archive 5 Forks + close Issue #48 | `gh repo archive` + `gh issue close` |

**Wichtig:** Wave 2 dispatcht erst NACH `clarify(choices=...)` User-Freigabe.

## Briefing-Templates für M3-Only Swarm

### Scout-Biene (read-only)
```
Kontext: Du bist Biene #N im Yuno-Schwarm.
Repo: OWNER/REPO (GitHub).
Aufgabe: [Spezifische read-only Analyse]
Schritte: [1-4 konkrete gh CLI Befehle]
Output: [Strukturiertes Format, Deutsch]
Read-only — keine Änderungen an GitHub.
```

### Execute-Biene (write)
```
Kontext: Du bist Biene #N im Yuno-Schwarm.
AUFGABE: [Spezifische Schreib-Aktion]
Schritte: [1-4 konkrete gh CLI Befehle mit --method PUT]
Verifizierung: [gh api Check dass Aktion geklappt hat]
Output: Bestätigung mit HTTP-Status. Deutsch.
```

## GitHub MCP 401 → gh CLI Fallback

**Pattern:** Alle Bienen trafen unabhängig auf `mcp__github__*` 401 Bad Credentials.
**Fix:** Jede Biene fiel selbstständig auf `gh` CLI zurück (Keyring-Token, `repo`-Scope).
**Root Cause:** MCP-Server-Token abgelaufen oder nicht konfiguriert im Hermes-Profil.
**Lesson:** Subagent-Briefings sollten immer `gh` CLI als primären GitHub-Zugriff nennen, nicht MCP. MCP ist unzuverlässig für delegierte Subagenten.

## Validierung: Basti-Feedback

Nach Wave 1 sagte Basti: **"A+B wieder mit M3 Bienen das hat gut funktioniert"**

Das bestätigt:
1. M3-Only Pattern funktioniert ohne Fable für Audit/Scan-Aufgaben
2. Two-Wave Scout→Execute mit User-Gate ist der richtige Workflow
3. `clarify(choices=[...])` als Gate zwischen Wave 1 und Wave 2 ist das bevorzugte Interface
4. Triviale Tasks (wie #48 close) können an eine der Execute-Bienen angehängt werden statt als eigene Wave

## Key Findings (Session-Ergebnisse)

### greyscripts
- **7 offene Issues** (nicht 54 — alte Zahl aus früheren Sessions. Immer live prüfen!)
- CI rot (Issue #30) — blockiert neue Feature-Commits
- `main` vs `master` Default-Branch-Konflikt
- 10+ stale copilot/* Branches (aber alle <30 Tage)

### hermes-v7
- PR #7 (SecurityKernel): Code solide (+4.550 Zeilen), aber CI rot wegen pre-existing TS-Fehlern → NEEDS-WORK
- PR #8 (Plugin-Registry): 66 Files / +19.439 Zeilen Draft, coverage/ + logs/ im Diff → CLOSE/splitten
- babel-jest (#8) vs. ts-jest (#7) Konflikt — Entscheidung nötig vor Merge

### GitHub Account-wide
- 4/5 Hauptrepos ohne LICENSE (MaxClaw = public, rechtliches Risiko)
- 5 archivierbare Repos (Greyjson = 631 Tage DEAD)
- multi-agent-workflows als einziges Repo ohne CI
