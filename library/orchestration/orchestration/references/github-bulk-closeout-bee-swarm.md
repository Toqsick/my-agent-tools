# Bienen-Schwarm GitHub Bulk Closeout

**Domain:** GitHub Issue/PR Cleanup via orchestrated subagents  
**Pattern:** Adaptive 2-3 Wave M3 Bienen-Schwarm  
**Validated:** 2026-07-07 (15→2 open items, 3 repos, 8 bees total)  
**Parent skill:** orchestration/multi-agent-orchestration

---

## Wann verwenden

Basti sagt: "manage mal mein github", "gehe alle an", "was ist offen" — Aufforderung zum kompletten GitHub-Cleanup.

Trigger-Signal: Basti will gesehen haben was offen ist UND aktiv werden. Nicht nur "zeig mal" sondern "mach was".

## Adaptive Wave Dispatch (validiert 2026-07-07)

Das Besondere am 2026-07-07 Run war die **adaptive Wellensteuerung**: Wave 1 entscheidet, WELCHE Bees in Wave 2 starten, Wave 2 schaltet optional auf restliche S-Tickets um.

```
Phase 0: Discovery (scan ALL repos)
Phase 1: Priorisieren (2-4 Optionen → User entscheidet)
  ↓ "mach mal"
Wave 1: 3 Bees (breite Cleanup-Welle — alle Repos, Priorität P0)
  ↓ Natur der Resultate evaluieren
Wave 2: 1-3 Bees (verbleibende Issues + Assessments)
  ↓ Vorletzte Issues schließen
Phase 3: Finalize + P3-Hygiene
  ↓ "ja weiter"
Mini-Wave 3: 1-2 Bees (S-Tickets + kleine Features)
  ↓ Finale Issues schließen
Phase 4: Queen-Consolidation (Scorecard + Verifikation)
```

**Kernregel:** Die Wellenbreite passt sich dynamisch an. Wave 1 = immer 3 Bees (breit). Wave 2 + 3 = 1-3 Bees je nachdem was übrig ist. Nie mehr als 3 parallel — das verträgt der Context-Window.

### Mid-Flight Progress Tracking

Sobald Bees dispatched sind, SOFORT eine `todo()`-Scorecard erstellen — sichtbar für User:

```
| Biene | Status | Task |
|---|---|---|
| 🅰️ | ⏳ Dispatched | greyhack cleanup |
| 🅱️ | ⏳ Dispatched | greyscripts #43 |
| 🅲 | ⏳ Dispatched | parse-exploit-reqs |
```

Jedes eintreffende Bee-Result (ASYNC DELEGATION BATCH COMPLETE) sofort verarbeiten:
1. `todo()`-Status aktualisieren → ✅ / ❌
2. Mid-Flight-Kommentar an User ("Biene X gelandet! Hier die Details...")
3. Wenn Commit-fähig: sofort commiten + pushen + Issue schließen
4. Nicht auf andere Bees warten — das produziert Leerlauf

### PR/Issue Assessment Pattern ("Hot Garbage" Fallback)

Nicht jedes Issue/PR enthält echten Code. Beispiel PR #8 (2026-07-07):
- 6.885 Zeilen "addiert" → aber alles CI-Artifakte (coverage/, HTML-Reports)
- Kein einziger echter Code-Change
- Outcome: PR schließen mit `state_reason=not_planned`

**Assessment-Schritte:**
1. PR-Diff holen (`pull_request_read method='get_diff'`)
2. Files-Liste holen (`pull_request_read method='get_files'`)
3. Schlüssel-Files inhaltlich checken (ist das echter Code oder CI-Müll?)
4. Wenn nur CI/Artifakte: `not_planned` mit Begründungskommentar
5. `.gitignore`-Tipp hinterlassen wenn coverage/-Artefakte drin waren

## Workflow

### Phase 0: Discovery — Scan ALL repos

Parallel MCP calls:
```
search_issues(query="is:open is:issue user:Toqsick")
search_pull_requests(query="is:open is:pr user:Toqsick")
```

Output: Strukturierte Matrix — Nummer, Titel, Repo, Typ, Alter, Labels, Dringlichkeit.

**Wichtig:** Per-Repo counten, nicht nur totals. Besseres User-Feeling wenn man sieht "greyhack: 5 → 0, greyscripts: 0 → 1, hermes-v7: 1 → 1".

### Phase 1: Priorisieren (User-Entscheidung)

Präsentiere als Tabelle mit Aufwandseinschätzung (S/M/L) und Dispatch-Plan.

**Regel:** Nie "was soll ich machen?" — immer 2-4 Optionen mit Konsequenz.

### Phase 2: Wave 1 — Breite Cleanup-Welle

Dispatch 3 parallele Bees via `delegate_task(tasks=[...])`. Pro Bee:

1. **Briefing enthält:** Repo-Name, Issue-Nummer, lokaler Pfad (~/30-Library/<repo>), Branch-Name, exakte ACs aus Issue
2. **Read-only first:** Code-Status prüfen, Issue-Body lesen, ggf. Assessment erstellen
3. **Nur additive Fixes** — nie bestehende Struktur brechen
4. **Report:** Welche Files geändert, welche Diffs, ob Tests bestanden
5. **Commit-NIE im Subagent** — Bee reportet nur, Parent committed

**Wellen-Prinzip:**
- Wave 1 (3 Bees): Hauptlast — alle offenen Items, breite Abdeckung
- Wave 2 (1-3 Bees): Verbleibende + Assessments + P3-Hygiene
- Mini-Wave 3 (1-2 Bees): S-Tickets + kleine Features die sich währenddessen auftun

### Phase 3: Finalize — Sofort nach Bee-Rückkehr

Jede Bee wird sofort verarbeitet — nicht auf andere warten:

```
1. Prüfen ob Fix reell (Subagent-Claims verifizieren!)
2. git add <files>
3. git commit -m "scope: message\n\nCloses #N"
4. git push
5. mcp__github__add_issue_comment (Diffs + Details)
6. mcp__github__issue_write (state=closed, state_reason=completed)
```

### Phase 4: Queen-Consolidation Report

Nachdem ALLE Bees zurück sind — finaler Report. Format:

```
# 🏆 Finale Scorecard — Kompletter Swarm-Durchlauf

## GitHub VORHER → NACHHER
| Repo | Open PRs | Open Issues | → | Open PRs | Open Issues |
|---|---|---|---|---|---|
| greyhack | N | N | → | 0 ✨ | 0 ✨ |
| greyscripts | N | N | → | 0 | N |
| hermes-v7 | N | N | → | 0 | N |

**X open Items → Y open Items.**

## Komplette Session-Statistik
| Metrik | Wert |
|---|---|
| Bienen dispatched (gesamt) | N |
| GitHub Items geschlossen | N |
| Neue Tools implementiert | N |
| Neue Dateien erstellt | N |
| Commits gepusht | N |
| Security Gaps geschlossen | N |
```

Danach: `search_issues(is:open)` und `search_pull_requests(is:open)` als Verification erneut laufen lassen.

## Pitfalls

| # | Problem | Fix |
|---|---------|-----|
| 1 | Eine Bee macht alles | 3 parallele Bees + Wellen-Prinzip |
| 2 | Auf alle Bees warten → Leerlauf | Jede sofort finalizen |
| 3 | "Was soll ich machen?" | Matrix mit 2-4 Optionen |
| 4 | Commit ohne Verify | Tests ausführen + Subagent-Claims prüfen vor commit |
| 5 | Bee ohne Read-only-Vorlauf | Erst Code-Status prüfen |
| 6 | Beide Repos im selben Commit | Pro Repo eigener Commit/Branch |
| 7 | Subagent-Claims blind glauben | IMMER verifizieren: SHAs, Diffs, File-Existenzen |
| 8 | Wave 1 komplett abwarten | Wave 2-Planung während Bee-Flug (Parent arbeitet) |
| 9 | PR nur Diff lesen → falsches Urteil | Files-Liste + Inhalt prüfen (CI-Artifakte erkennen) |
| 10 | Scorecard vergessen | Queen-Consolidation am Ende IMMER machen |

## Beispiel-Briefing (validiert 2026-07-07)

```
User: Basti (Toqsick)
Repo: Toqsick/hermes-v7
Local path: ~/30-Library/hermes-v7
Branch: feat/security-kernel

Issue #1: refactor(security): Security Kernel 4-Ebenen-Architektur

Assessment: Code existiert bereits via PR #7. Nur 2 Gaps offen:
Gap 1: ReviewerA Intent-Hash-Pflichtprüfung
Gap 2: hermes.config.json securityKernel Block
Gap 3: Tests für beide

Do NOT commit or push. Report all changes with diffs.
```

## Queen-Consolidation Per-Bee Template

Wenn eine Bee den finalen Report liefert, konsolidiere in diesem Format:

```
🐝 **${name} gelandet — ${headline}!**

> ✅ ${was_wurde_gemacht}
> ✅ ${nächste_aktion}
> ${besonderheit}
```

Wenn Bee leeren/fehlerhaften PR findet:

```
🐝 **${name} gelandet — ${headline}!** (◔_◔)

> 📋 **Assessment:** ${kurzfassung}
> ${detail}
> ✅ PR #N geschlossen — \`not_planned\`.
```

## Related

- `references/phase-1-spawn-experts.md` — General expert-spawn template
- `references/pitfalls-detailed.md` — Full pitfall list (check #5, #11, #17)
- `github-issues` skill — Issue CRUD commands (bulk operations section)
- `github-pr-workflow` skill — PR lifecycle commands
- `references/queen-bee-configuration.md` — M3 pinning + concurrent config
- `references/hybrid-local-fable-swarm.md` — Alternative: Local + Fable hybrid