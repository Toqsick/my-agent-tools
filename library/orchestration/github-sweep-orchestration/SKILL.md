---
name: github-sweep-orchestration
description: |
  Use when you need to use the github-sweep-orchestration workflow and its documented procedures.
  NOT for unrelated tasks outside the github-sweep-orchestration workflow.
  Provides focused guidance for github-sweep-orchestration.
version: 1.0.0
author: Hermes Agent
license: MIT
trigger_keywords: ['github', 'sweep', 'orchestration', 'workflow', 'need']
keywords: ['github', 'sweep', 'orchestration', 'workflow', 'need']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'multi-agent-pitfalls-cheatsheet']
---


# GitHub Sweep Orchestration

Multi-Agent Pattern für kompletten GitHub-Repo-Cleanup mit M3-Bienen.

## Trigger
- "manage mein github", "räum github auf", "was ist offen", "gehe alle issues an"
- User will Übersicht über offene Items + gleichzeitige Bearbeitung

## Phase 1 — Recon (Queen, inline)

### 1.1 Inventory
```
mcp__github__get_me → User bestimmen
mcp__github__search_pull_requests(is:open is:pr user:@me)
mcp__github__search_issues(is:open is:issue user:@me)
```

### 1.2 Categorize & Score
Jedes Item in eine von 4 Kategorien einordnen:

| Kategorie | Kriterien | Beispiele |
|---|---|---|
| ⭐⭐⭐ Quick Win | < 5 Min, nur API-Aktion | Dependabot schließen, Duplikat weg, Stale Issue |
| ⭐⭐ Active Impact | Code-Änderung nötig, klar spezifiziert | Syntax-Fixes, Bugfix mit Datei+Zeile |
| ⭐ Feature/Strategic | Neue Implementierung | Tool bauen, Architecture-Assessment |
| 📦 Parken | Vage, Zukunftsmusik, oder XL-Aufwand | Konzept-Issues, Branch-Merges mit Konflikten |

### 1.3 Wellen planen
- **Welle 1:** Alle unabhängigen Tasks (Closers + Fixers + Features ohne Abhängigkeiten)
- **Welle 2:** Tasks die auf Welle-1-Ergebnissen aufbauen (z.B. Issue schließen nachdem Code committed)
- **Welle 3 (optional):** Assessment + Strategic Analysis

Max 6 Bienen pro Welle (config default `max_concurrent_children: 6`).

## Phase 2 — Wave Dispatch (M3 Bienen)

### 2.1 M3-Pinning verifizieren
```yaml
# config.yaml → delegation:
model: MiniMax-M3
provider: minimax
max_concurrent_children: 6
reasoning_effort: xhigh  # wichtig für Code-Qualität
```
Prüfen mit `read_file ~/.hermes/config.yaml offset=383 limit=15`.

### 2.2 Biene-Typen und Briefing-Vorlagen

Jede Biene bekommt ein **water-tight Briefing** mit:
- Exaktem Working Directory (`find ~ -maxdepth 4 -name "repo" -type d` vorab klären!)
- Repo + Branch + Remote URL
- Akzeptanzkriterien als Checkliste
- Sprachregeln (GreyScript: no negative indices, multi-line if, char(10) function, .src extension)
- Build-Verification-Befehl
- **"Do NOT commit or push"** — Queen macht den finalen Commit

#### 🔴 Closer-Biene (GitHub API only)
```
Goal: Close [PR/Issue numbers] on [repo] with comment "[Begründung]"
Use: mcp__github__update_pull_request(state=closed) / mcp__github__issue_write(state=closed, state_reason=completed)
Add comment BEFORE closing via mcp__github__add_issue_comment
Verify: list remaining open items after closing
```

#### 🟡 Fixer-Biene (Mechanische Bugfixes)
```
Goal: Fix [N] bugs in [repo] (Issue #[X])
Working Directory: [exact path]
Files + Lines: [exact list from issue body]
Rules: [language-specific constraints]
After: run [build command] to verify
Do NOT commit or push. Report git diff --stat.
```

#### 🟢 Feature-Biene (Komplette Implementierung)
```
Goal: Implement [feature] for Issue #[X]
Working Directory: [exact path]
Files to create: [list with expected line counts]
Acceptance Criteria: [copy from issue]
Style reference: [point to existing files in repo]
Build: [greybel/jest/tsc command]
Do NOT commit or push. Report all files created/modified.
```

#### 🔵 Assessment-Biene (Read-only Analyse)
```
Goal: Assess [Issue/PR] and recommend action
Steps: [numbered analysis steps with API calls]
Options: A) Keep  B) Close  C) Repurpose
Report: viability score, effort estimate, dependencies, risks
```

### 2.3 Dispatch
Alle unabhängigen Bienen gleichzeitig mit `delegate_task` dispatchen. Sie laufen parallel im Hintergrund und returnieren automatisch als ASYNC message.

## Phase 3 — Queen Consolidation

### 3.1 Ergebnisse einsammeln
- Jede Biene returniert automatisch als ASYNC message
- Bonus-Funde extrahieren (z.B. zusätzliche Bugs die beim Fixen entdeckt wurden)
- Build-Status verifizieren (wurde greybel/jest tatsächlich grün?)

### 3.2 Commit + Push (Queen macht das selbst!)
```bash
cd [repo]
git add [specific files]  # NICHT blind -A wenn andere Artefakte herumliegen
git commit -m "feat: [description] (Issue #[X])

[Details]

Closes #[X]"
git push origin [branch]
```

WICHTIG: Nicht jede Biene einzeln committen — **ein Commit pro logischer Einheit** (z.B. alle Syntax-Fixes in einem Commit, das neue Tool in einem anderen).

### 3.3 Issues auf GitHub schließen
```
mcp__github__add_issue_comment(issue_number=X, body="[Summary with commit ref]")
mcp__github__issue_write(issue_number=X, state=closed, state_reason=completed)
```

### 3.4 Finale Verifikation
```
mcp__github__search_issues(is:open is:issue user:@me)
mcp__github__search_pull_requests(is:open is:pr user:@me)
→ Scorecard VORHER → NACHHER
```

## Pitfalls (aus echter Session gelernt)

### Biene-Verhalten
- **Bienen sollen NICHT committen** — Queen macht den finalen Commit um Merge-Konflikte zwischen zeitgleich laufenden Bienen zu vermeiden
- Biene braucht **exakte Dateipfade** — sonst sucht sie ewig mit `find`
- `greybel build` / `npx jest` als Verification **im Briefing fordern**, nicht optional
- Biene vergisst manchmal README/Docs zu aktualisieren — Queen muss nachfassen
- Bei 100 API-Calls Limit: M3 Bienen treffen manchmal das `max_iterations` Limit bei komplexen Tasks → acceptable, Hauptsache Core-Task done

### GitHub API
- `update_pull_request` für PR-Close, `issue_write` für Issue-Close
- Comment **vor** Close hinzufügen (sonst ist der Close ohne Kontext)
- `state_reason: completed` für saubere Schließung
- Dependabot PRs: immer mit Begründung schließen, sonst reopen sie sich

### Branch-Hygiene
- Vor Commit: `git status --short` prüfen ob untracked Files von anderen Prozessen da sind
- Nur relevante Files adden (`git add [specific files]`), nicht blind `git add -A` wenn andere Artefakte herumliegen
- SSH vs HTTPS remote: `git remote set-url` wenn SSH-Auth fail schlägt

### M3-Konfiguration
- `reasoning_effort: xhigh` für Code-Qualität wichtig
- `max_iterations: 100` reicht für die meisten Tasks (Feature-Bienen brauchen ~80-100)
- Timeout: Feature-Bienen können 8-12 Min brauchen (583s longest observed)
- Kosten: praktisch nichts — 10 Bienen × ~3 Min = Peanuts

## Key Metrics (Referenz aus 2026-07-07 Session)

| Metrik | Typischer Wert |
|---|---|
| Bienen pro Session | 6-10 |
| Items geschlossen pro Session | 10-15 |
| Features implementiert | 2-4 |
| Code-Zeilen geschrieben | ~2.000-2.500 |
| Gesamtdauer (parallel) | ~30-45 Min |
| M3 Kosten | < $1 |

## Voraussetzungen

- `delegation.model: MiniMax-M3` in `~/.hermes/config.yaml`
- `mcp__github__` Tools verfügbar (GitHub MCP Server konfiguriert)
- Local clones der Repos unter `~/30-Library/` oder `~/10-Projekte/`
- `greybel-js` / `greybel` für GreyScript Build-Verification installiert
