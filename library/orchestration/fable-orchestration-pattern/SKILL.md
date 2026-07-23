---
name: fable-orchestration-pattern
description: |
  Use when selecting an orchestration variant for a multi-agent swarm, assigning planner and worker tiers, or balancing parallelism against coordination cost.
  NOT for single-agent tasks, mechanical execution with no delegation need, or launching a swarm before scope and verification gates are defined.
  Explains the Fable-to-M3 two-tier pattern and how to choose a reliable swarm topology for the workload.
version: 1.3.0
changelog:
- '1.3.0 (2026-07-07): Variante C (M3-Only Two-Wave) hinzugefügt — Scout→Execute Pattern
  validiert bei GitHub-Audit (5+3 Bienen, $0, 7 Min). Neue Pitfalls #17-20 (MCP-401,
  Default-Branch verify, Issue-Count stale, Variante C). Referenz m3-only-two-wave-swarm-2026-07-07.md.'
- '1.2.0 (2026-07-05): Phase 5 Push&PR nach Execution + SSH-Fallback-Fix + Anti-Patterns
  erweitert + cleanup-workflow.'
- '1.2.0 (2026-07-05): Phase 5 Push&PR nach Execution + SSH-Fallback-Fix + Anti-Patterns
  erweitert + cleanup-workflow.'
- '1.1.0 (2026-07-05): 3-Tier Advanced Pattern (Fable→M3→Fable) + Cross-Check Methodology
  + CI-is-kaputt + MD5-before-Diff Pitfalls. Referenz refactor-session-2026-07-05.md.'
- '1.0.0 (2026-07-05): Initial aus GitHub-Hygiene-Session extrahiert. Fable 5 → M3
  Two-Tier Pattern, --bare Pitfall, keine-limits Präferenz'
license: MIT
platforms:
- linux
triggers:
- fable
- orchestration
- swarm
- keine limits
- strategy
- mechanic
- two-tier
- triage
- bot verification
- security-audit
- refactor
- github audit
- repo scan
- bienen
- scout swarm
author: Hermes Agent
trigger_keywords: ['swarm', 'agent', 'selecting', 'orchestration', 'variant']
keywords: ['swarm', 'agent', 'selecting', 'orchestration', 'variant']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['multi-agent-work', 'swarm-router', 'multi-agent-cluster-patterns']
---


# Fable 5 → M3 Schwarm — Two-Tier Orchestration Pattern

## TL;DR

Drei gültige Varianten, je nach Komplexität:

### Variante A: Two-Tier (Fable→M3) — Standard
1. **Fable 5** (1 Call, ~$0.30, text output) → Strategie/Plan/Judgment
2. **M3 xhigh** (bis zu 5 Subagenten parallel, kostenlos) → Mechanik/Messung/Analyse
3. **Queen** (Yuno) → Konsolidierung, Cross-Check, Freigabe

### Variante B: Three-Tier (Fable→M3→Fable) — Kritische Entscheidungen
1-3 wie Variante A, plus:
4. **Fable 5 (Validation)** (1 Call, ~$0.30) → Validierung der Subagent-Befunde gegen Fable-Strategie

### Variante C: M3-Only Two-Wave (Scout→Execute) — Schnelle Audits ⭐ validiert 2026-07-07
1. **M3 Schwarm Wave 1** (3-5 Bienen, read-only) → Inventur/Analyse/Reports
2. **Queen** → Konsolidiert zu Masterplan mit ⭐⭐⭐ Priorisierung
3. **clarify(choices)** → User wählt Umfang der Ausführung
4. **M3 Schwarm Wave 2** (1-3 Bienen, write) → Führt die freigegebenen Aktionen aus
5. **Queen** → Verifiziert jede Aktion aus den Bienen-Reports

**Wann welche Variante?**
| Kriterium | A (Fable→M3) | B (3-Tier) | C (M3-Only) |
|-----------|:----------:|:---------:|:-----------:|
| Strategie nötig | ✅ | ✅ | ❌ |
| Kritische Entscheidung | ❌ | ✅ | ❌ |
| Read-only Audit/Scan | ✅ | ❌ | **⭐ Best** |
| Kosten | $0.30 | $0.60 | **$0.00** |
| Speed | ~5 Min | ~10 Min | **~4 Min** |
| Basti hat es validiert | ✅ | ✅ | ✅ "das hat gut funktioniert" |

Full session report for Variante C: `references/m3-only-two-wave-swarm-2026-07-07.md`

## Warum dieses Pattern?

| Faktor | Serielle Fable-Calls | Two-Tier (Fable→M3) | Three-Tier (Fable→M3→Fable) |
|--------|----------------------|---------------------|----------------------------|
| Kosten | ~$0.30×N | ~$0.30×1 | ~$0.60×1 |
| Parallelität | Nacheinander (Rate Limits) | Parallel (lokal) | Parallel (lokal) |
| Strategie-Qualität | Gut, aber abgelenkt | Fokussiert, kein Tool-Overhead | Fokussiert + validiert |
| Validierung | ✗ | Weak (Queen-Cross-Check) | Strong (Fable-judged) |
| Time-to-Result | 30+ Min | ~5 Min | ~10 Min |
| Entscheidungsqualität | Mittel | Mittel | Hoch |
| **Empfehlung** | ✗ | Einfache Scouts | **Kritische Entscheidungen** |

## Dispatch-Workflow

### Phase 0: Inventur (READ-ONLY, selbst machen)
- Ist-Zustand erfassen: `ls`, `git log`, `find`, `diff`
- Phase-0-File-Schreiben: `~/docs/system/schwarm-PROJECT-DATE/`
- Security-Check: `grep -r "gho_" ~/ --include="*" 2>/dev/null | head -5`

### Phase 0.5: User-Entscheidungsmatrix
- 2-4 konkrete Optionen (A/B/C/D) aus Phase 0
- Basti wählt → Schwarm konfigurieren

### Phase 1a: Fable 5 Strategy-Call (1 Background-Prozess)
```bash
# NICHT mit --bare — das überspringt OAuth!
claude -p "$(cat /tmp/fable-brief.md)" \
  --model claude-haiku-4-5 \
  --output-format text \
  > /tmp/fable-result.txt 2>&1
```

**Briefing-Muster (self-contained):**
```markdown
# Fable 5: [Task-Name]

## Deine Rolle
Du bist Fable 5 (Claude Haiku via Pro Rabat). Stratege & Denker.
1 Call, alles in einer Antwort. Keine Rückfragen.

## Kontext
[Alle Fakten: Pfade, LOC, Dates, Konflikte — KEIN Dateizugriff möglich]

## Aufgaben
1. [Konkrete Frage 1]
2. [Konkrete Frage 2]

## Output-Format
Strukturiertes Markdown. Deutsch. Präzise.
```

### Phase 1b: M3 xhigh Schwarm (bis zu 5 parallel)
```python
delegate_task(tasks=[
    {"goal": "Task 1: ...",
     "context": "Repo-Pfade, Constraints. Read-only. Deutsch.",
     "role": "leaf"},
    ...
])
```

**Toolsets pro Task:** terminal + file + search (kein web)

### Phase 1c: Fable 5 Validation-Call (Advanced: 3-Tier)
Nach Subagent-Rückkehr: Zweiter Fable-Call mit echten Messdaten.

**Wann:** Wenn Fable-Strategie und Subagent-Messungen abweichen oder Entscheidung kritisch ist.

**Briefing-Unterschied zu Phase 1a:**
- Enthält die echten Subagent-Outputs (LOC, MD5, Diffs, CI-Status)
- Fable bekommt: "Das hast du empfohlen → DAS haben Subagenten gemessen → Validier und korrigier"

**Getestet 2026-07-05:**
- Phase 1a: `src/{crypto,recon,tools}/` Layout vorgeschlagen
- Phase 1b: security/ enthielt grsa_v2 (MD5-identisch), yuno_viper braucht eigenes Verzeichnis
- Phase 1c: Validierte auf Option C (`src/{core,crypto,recon,tools,viper}/`)

### Phase 2: Cross-Check
**Die kritischste Phase — hier entstehen oder sterben Entscheidungen.**

#### Cross-Check-Matrix
| Was | Fable (schätzt) | M3 Subagent (misst) | Queen validiert |
|-----|----------------|---------------------|-----------------|
| LOC/Zeilen | "~300" | `wc -l` = 433 | ✅/❌ |
| Duplikate | "vermutlich ähnlich" | `md5sum` = identisch | ✅ |
| Build-Status | "sollte grün sein" | CI = 5× failure | 🚨 NEUE ERKENNTNIS |
| CI-Timing | "vor Refactor" (Intuition) | Build tot → noch kritischer | ✅ Fable korrigiert |

**Pattern: Fable sagt "schätze", Subagent sagt "messe", Queen sagt "wer hat recht".**

#### Validierte Abweichungen (2026-07-05)
| Punkt | Fable (Phase 1a) | M3 (Phase 1b) | Ausgang |
|-------|-------------------|---------------|---------|
| Clone AHEAD | 2 Commits | 3 Commits | M3 richtig |
| grsa_v2 | "vermutlich ähnlich" | MD5-identisch, 433 Zeilen | M3 richtig |
| xmem canonical | "schätze A" | 16 Hunks, 61 Zeilen Diff, A=Obermenge | Beide recht, M3 mit Beleg |
| Verzeichnis-Layout | src/{crypto,recon,tools} | src/{core,crypto,security,tools,viper} | **Fable korrigierte zu C** |
| CI-Status | "sollte funktionieren" | 5× failure, letzter Build 2026-06-27 | M3 enthüllt Issue |
| CI-Fix-Timing | "vor Refactor" | Build ist tot | Fable validiert "nach Refactor" |

### Phase 3: Synthese + Masterplan
- Queen konsolidiert alle Outputs
- Quality Gates definieren
- Execution-Reihenfolge priorisieren (P0→P1→...)
- Basti-Freigabe per Telegram

### Phase 4: Execution
- Pro Schritt: Build/Test/Verify
- Nach jedem Schritt: Status-Update
- Execution-Reihenfolge: Fable empfiehlt (validiert 2026-07-05: Task 2→3→1→5→4)
- Änderungen committen NACH Verify — nicht vorher

### Phase 5: Push & PR (validiert 2026-07-05)

Nach Execution: **Push → Cleanup → PR**.

#### 5a. Push (immer zuerst — sichert Arbeit)
```bash
# SSH bevorzugt
git push -u origin branchname

# SSH failed? ("Permission denied (publickey)")
# → HTTPS + gh credential helper:
git remote set-url origin https://github.com/OWNER/REPO.git
git config credential.helper "/usr/bin/gh auth git-credential"
git push -u origin branchname
```

**Pitfall:** Wenn kein SSH-Key auf GitHub registriert ist, funktioniert `ssh -T git@github.com` nicht. Lokaler Key existiert, ist aber nie hochgeladen. Fix: `gh auth git-credential` als Git-Credential-Helper (nutzt Token im Keyring).

#### 5b. Cleanup
```bash
# Session-Temp-Files
rm -f /tmp/fable-*.txt /tmp/m3-schwarm*.json /tmp/progress*.log

# Stale OS-Files
find . \( -name ".DS_Store" -o -name "*.swp" -o -name "*.bak" \) -delete

# Leere Zielverzeichnisse
find src/ -type d -empty -delete

# Commit Cleanup
git add -A && git commit -m "chore: cleanup empty dirs and stale files"
```

**Pitfall:** Nur Files löschen die man explizit identifiziert hat. Keine blinden `rm -rf *`.

#### 5c. PR erstellen
```bash
gh pr create \
  --base develop \
  --head refactor/BRANCH-NAME \
  --title "refactor: kurze beschreibung (DATUM)" \
  --body "$(cat <<'EOF'
## Zusammenfassung

## Was geändert wurde

### Bereich 1
- Änderung mit Begründung

### Bereich 2
- Änderung mit Begründung

## Akzeptanzkriterien
- [x] Kriterium 1

## Test-Plan
1. Schritt 1
2. Schritt 2

## Rollback-Plan
- Backup-Branch: backup/develop-before-YYYY-MM-DD
- Pre-Refactor-Backup: /path/to/backup
EOF
)"
```

**PR-Body Prinzipien:**
1. Immer **Rollback-Plan** drin
2. Akzeptanzkriterien als Checkliste
3. **Kein** AI-Boilerplate — präzise Deutsche Sätze
4. Test-Plan mit shell-Befehlen
5. `Related:`-Section mit Doku-Pfaden

## Tool-Aufruf: Claude CLI für Fable

### RICHTIG (diese Session validiert)
```bash
claude -p "$(cat brief.md)" --model claude-haiku-4-5 --output-format text > result.txt
```

### FALSCH (getestet + gefailed)
```bash
# --bare überspringt OAuth → "Not logged in"
claude --bare -p "$(cat brief.md)" --model claude-haiku-4-5 ...
# --max-turns limitiert → Fable kann nicht antworten
```

### Warum --bare failt (DEBUG)
- `--bare` deaktiviert OAuth/Keychain-Read
- `gh auth status` zeigt Token, aber Claude CLI ohne `--bare` liest ihn via native Keychain
- Fix: `--bare` WEGLASSEN

### Warum keine Limits (BASTI-PRÄFERENZ)
- `--max-turns 3` → Fable bekommt 0 Antwort-Turns → "Reached max turns"
- `--max-budget-usd 0.30` → kappt Fable mitten in der Antwort
- **Basti sagte "keine limits"** — das ist ein Style-Command, kein Vorschlag

### Output-Format: text vs json
| Kriterium | text | json |
|-----------|------|------|
| Strategy-Calls | ✅ Strukturiertes Markdown | ❌ Starre Struktur |
| Triage/Klassifikation | ❌ Unnötig verbose | ✅ Parsebar |
| **Empfehlung** | **Strategie/Pläne** | Ja/Nein/Zahl-Entscheidungen |

## Pitfalls

1. **`--bare` NICHT verwenden** — überspringt OAuth → "Not logged in"
2. **`--max-turns` NIEMALS limitieren** (für Basti) — "keine limits"
3. **`--output-format json` nur für Klassifikation** — Strategie braucht text
4. **Briefing muss SELF-CONTAINED sein** — Fable hat keinen Dateizugriff
5. **Subagent-Output validieren** — Fable schätzt, Subagent misst, Queen cross-checkt
6. **Nicht mehr als 5 Subagenten parallel** — max des Systems
7. **Kein web-Toolset für M3** — nur lokale Messung
8. **Output-Pfade IMMER explizit** — `~/docs/system/schwarm-PROJECT-DATE/`
9. **Fable kostet ~$0.30/Call** — 1 Call für Strategie reicht
10. **`claude models` ist kein Subcommand** — `list` startet interaktiven Dialog
11. **CI-Status VOR Refactor prüfen** — Wenn CI rot ist, CI-Fix vor oder nach Umbau, nie mittendrin
12. **MD5-Check VOR Diff bei Duplikat-Verdacht** — `md5sum file1 file2` spart diff-Lesen bei 433+ Zeilen
13. **SSH-Key Status prüfen VOR push** — `ssh -T git@github.com` testen, nicht blind mit SSH-Remote pushen
14. **Kein Rollback-Plan im PR** — ohne Backup-Branch kann der Reviewer nicht sicher mergen
15. **Temp-Files aufräumen NACH PR** — sonst liegen `/tmp/fable-*` für Tage
16. **`gh repo delete` braucht `delete_repo` Scope** — Standard-Scopes reichen nicht. Prüfen mit `gh auth status | grep delete_repo`
17. **GitHub MCP 401 in Subagenten** — `mcp__github__*` Calls geben 401 Bad Credentials für delegierte Subagenten. Briefings sollen `gh` CLI als primären GitHub-Zugriff nennen (Keyring-Token, `repo`-Scope), nicht MCP.
18. **Default-Branch verify vor `gh api` PUT** — nicht jedes Repo nutzt `main`. `hermes-v7-sse-dashboard` nutzt `master`. Immer `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'` prüfen vor Branch-spezifischen API-Calls.
19. **Issue-Counts veralten schnell** — greyscripts hatte "54 Issues" im Memory, real waren es 7. Immer `gh issue list --state open --limit 100` live prüfen, nie auf Memory-Zahlen vertrauen.
20. **Variante C (M3-Only) braucht kein Fable** — bei reinen Audit/Scan-Aufgaben ist Fable overkill. Queen kann direkt konsolidieren + `clarify(choices)` als Gate nutzen. Basti validiert: "das hat gut funktioniert".

## See Also

- `orchestration/multi-agent-orchestration` — Hub-Skill, Pattern-Repository
- `orchestration/multi-agent-pitfalls-cheatsheet` — Trigger-Watchlist vor delegate_task
- **`orchestration/pr-ship-pattern`** — End-to-End "Feature → gemergter PR" Blueprint (komponiert fable-orchestration-pattern + yuno-team-orchestrator + github-pr-workflow)
- `yuno-team-orchestrator` — 6-Persona-Team mit Fix-Loop-Pattern (Engineer→Verifier→Fix→Re-Audit→PASS). Komplementiert Variante C (M3-Only) durch iterative Qualitätssteigerung statt paralleler Breite.
- `user/preferences` — Basti's Style-Präferenzen

## Related Reference Files

- `references/github-hygiene-session-2026-07-05.md` — Token-Leak, SSH-Migration, Fork-Archivierung
- `references/refactor-execution-2026-07-05.md` — 5-Task Refactor, Acceptance-Criteria-Matrix, Backup-Strategie

## Anti-Patterns

- **Fable für Mechanik verwenden** — teuer, kein Tool-Zugriff, langsam
- **M3 für Strategie** — schwächer in Judgment/Abwägung
- **Limits setzen ohne User-Auftrag** — Basti: "keine limits"
- **Briefings ohne Executive Summary** — Fable kann nicht lesen was nicht drin steht
- **Subagenten Output nicht validieren** — Subagenten lügen/überschätzen sich
- **SSH-Key-Status nicht vor push prüfen** — `ssh -T git@github.com` testen
- **Kein Rollback-Plan im PR** — ohne Backup kann der Reviewer nicht mergen
- **Temp-Files nicht aufräumen** — `/tmp/fable-*` liegen für Tage
