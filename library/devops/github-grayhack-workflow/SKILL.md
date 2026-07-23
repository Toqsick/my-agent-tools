---
name: github-grayhack-workflow
title: GitHub GrayHack Development Workflow
description: |
  Use when coordinating GreyHack development through GitHub issues, feature branches, pull requests, or documentation updates tied to repository work.
  NOT for in-game GreyHack actions, generic GitHub administration unrelated to GreyHack, or merging changes without required verification.
  Standardizes the issue-to-branch-to-PR workflow and keeps GreyHack code and project documentation synchronized.
version: 1.1.0
author: Hermes
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - GitHub
    - GreyHack
    - GreyScript
    - greyscripts
    - Workflow
    - Issues
    - PRs
    - Telegram
    - Doku
    category: devops
    requires_toolsets:
    - terminal
    - files
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['greyhack', 'github', 'documentation', 'coordinating', 'development']
keywords: ['greyhack', 'github', 'documentation', 'coordinating', 'development']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack-hermes-api', 'greyhack-mission-orchestrator', 'greyhack-smart-macro']
---



# GitHub GrayHack Development Workflow

Dieser Skill automatisiert den GitHub-Entwicklungsworkflow für `greyscripts` auf Basis von `/home/bratan/Downloads/GitHub-Guide mit GrayHack.pdf`.

Er macht aus dem Guide einen wiederholbaren Hermes-Workflow:

```text
Idee / Bug / Tool aus ROADMAP.md
↓
Issue erstellen
↓
Label + Milestone setzen
↓
Branch erzeugen
↓
Code/Doku ändern
↓
Commits mit Refs #X schreiben
↓
PR mit Closes #X öffnen
↓
Doku aktualisieren
↓
Merge/Release prüfen
```

set -euo pipefail
## Ziel-Repo

```text
https://github.com/Toqsick/greyscripts
```

set -euo pipefail
## Zentrale Doku

```text
/home/bratan/docs/system/github-grayhack-guide.md
/home/bratan/.hermes/plans/github-grayhack-automation.md
/home/bratan/greyscripts/docs/hermes-automation.md
/home/bratan/docs/system/github-grayhack-todo-scan-YYYY-MM-DD.md
```

set -euo pipefail
For local todo discovery before issue creation, also load the reference:

```text
references/repo-todo-scan-2026-06-19.md
```

set -euo pipefail
For Greybel CI/build verification, use the implementation notes:

```text
references/greybel-ci-build-2026-06-19.md
```

set -euo pipefail
## Automatisierung im Repo

Seit 2026-06-18 gibt es ein Python-Skript im Repo:

```text
/home/bratan/greyscripts/scripts/hermes-automation.py
```

set -euo pipefail
Es automatisiert:
- Issues mit Labels + Milestones erstellen
- Branches von Issues ableiten
- GreyScript-Dateien bauen (`greybel build`)
- PRs mit `Closes #X` erstellen
- Milestone-Fortschritt anzeigen
- Roadmap-Tools aus `ROADMAP.md` listen

Seit dem P0-CI-Lauf am 2026-06-19 gibt es zusätzlich:
- `scripts/ci-build.sh` für lokale Greybel-Build-Verifikation
- `.github/workflows/ci.yml` für CI-Build-Artefakte
- `references/greybel-ci-build-2026-06-19.md` als Detailnotiz zu CLI, Scope und bekannten Build-Fehlern

**Wichtig:** Das Skript liegt aktuell auf `develop` und ist der primäre Einstiegspunkt für Hermes-Automatisierung.

Befehle:
```bash
python3 scripts/hermes-automation.py issue --title "[BUG] ..." --label bug --milestone v0.5.0
python3 scripts/hermes-automation.py branch --issue 5 --name feature/filecore
python3 scripts/hermes-automation.py build --file src/filecore.src
python3 scripts/hermes-automation.py pr --issue 5 --title "feat: filecore Closes #5"
python3 scripts/hermes-automation.py milestone --name v0.5.0
python3 scripts/hermes-automation.py roadmap
```

set -euo pipefail
## Aktiver Cron-Job

Seit 2026-06-18:
```text
Name: greyscripts-daily-status
Schedule: 0 9 * * * (täglich 09:00)
Job-ID: 009b472a967f
```

set -euo pipefail
Der Cron prüft:
- Offene Issues nach Label
- Milestone-Fortschritt (v0.4.0, v0.5.0, v0.6.0)
- Offene PRs
- Nächster empfohlener Schritt aus ROADMAP.md

**[SILENT]-Protokoll:** Wenn nichts geändert hat, antwortet der Cron exakt `[SILENT]` und unterdrückt die Benachrichtigung.

## Aktueller Stand (2026-06-19)

```text
Branch: develop
Phase 1: gemergt/erreicht — Auto-Label, Auto-Close, Bot-Loop-Schutz, core.setOutput()-Fix, Hermes CLI/Doku
Automation: /home/bratan/greyscripts/scripts/hermes-automation.py liegt auf develop
Cron: greyscripts-daily-status läuft täglich um 09:00
Nächste Phase: v0.5.0 — CI/CD Complete
```

set -euo pipefail
Nach dem Stand von 2026-06-19:
- Nicht mehr von `feature/ci-cd-workflow` ausgehen; im lokalen Checkout ist `develop` der relevante Branch.
- Phase 1 ist abgeschlossen; neue Arbeit sollte Phase 2/3 priorisieren.
- Vor Issue-Erstellung immer den lokalen Todo-Scan und ROADMAP-Abgleich durchführen.

## Grundregeln

1. **Branch policy für Experimente**
   - Code-/Tool-/Script-Änderungen nur auf `develop` oder einem Feature-Branch von `develop`.
   - Vor jeder Änderung Branch und Status prüfen:
     ```bash
     git branch --show-current && git status --short --branch
     ```

set -euo pipefail
   - Wenn der aktuelle Branch `main` ist, nicht direkt ändern. Entweder `develop` auschecken oder einen Feature-Branch von `develop` erstellen.
   - `main` niemals ohne explizite User-Freigabe mergen oder übernehmen.

2. **Kein Code ohne Issue**
   - Jede Änderung beginnt mit einem Issue.
   - Bugfixes, Features, neue Module und Tools bekommen eigene Issues.

2. **Commits referenzieren, PRs schließen**
   - Commit: `Refs #123`
   - PR-Title/Body: `Closes #123`

3. **Branches vom Issue ableiten**
   - Feature: `feature/<issue>-<kurzname>`
   - Fix: `fix/<issue>-<kurzname>`
   - Doku: `docs/<issue>-<kurzname>`

4. **Labels konsistent verwenden**
   - `bug`
   - `enhancement`
   - `new module`
   - `new tool`
   - `docs`
   - `wontfix`
   - `in progress`

5. **Milestones versioniert planen**
   - `v0.4.0`: Phase 1 abgeschlossen — Agenten-ready GitHub Flow, Auto-Label, Auto-Close, Bot-Loop-Schutz, Hermes CLI/Doku
   - `v0.5.0`: Phase 2 — CI/CD Complete, Greybel-Build-Verifikation, Composite Actions, Release-Drafter
   - `v0.6.0`: Phase 3 — Agent-Dispatch, Monitoring, Build-Artifacts, Failure-Notification

6. **Jeder relevante Schritt wird dokumentiert**
   - Laufdokumentation: `~/docs/system/github-grayhack-run-YYYY-MM-DD.md`
   - Status: `~/docs/system/github-grayhack-status.md`

7. **Entscheidungen per Telegram**
   - Chat-ID: `telegram:7222661188`
   - Wenn eine Entscheidung nötig ist, aktiv Telegram senden und nicht passiv im Chat warten.

## Local Repo Todo Scan vor Issue-Erstellung

Bevor neue Issues für GreyHack/GitHub-Workflow-Arbeit erstellt werden, erst einen lokalen read-only Todo-Scan durchführen und die Ergebnisse dokumentieren.

**Standard-Scope:**

- `README.md`, `ROADMAP.md`, `CHANGELOG.md`
- `plan.md`, `de/plan.md`
- `docs/`, `.github/`, `.github/workflows/`
- `scripts/`, `src/`, `tools/`
- `.hermes/plans/`

**Standard-Ausschluss:** `.git/`, `imports/`, Backup-/Import-Archive, generierte Artefakte. Nur einschließen, wenn der User explizit einen historischen Import-Scan will.

**Marker-Strategie:**

1. Exakte aktive Marker suchen: `TODO`, `FIXME`, `WIP`.
2. `BUG`/`HACK` nur ergänzt suchen und False Positives herausfiltern, weil dieses Repo viele legitime Vorkommen von `Grey Hack`, `Grey-Hack` und `GreyScript` enthält.
3. Workflow-Todos nicht nur aus `.github/workflows/*.yml` ableiten; Phase-2-Todos stehen oft in `~/docs/system/` und `.hermes/plans/`.
4. `ROADMAP.md` vor Issue-Erstellung gegen `CHANGELOG.md`, `README.md`, `src/` und `tools/` abgleichen.

**Wichtige Erkenntnisse aus dem 2026-06-19 Scan:**

- `.github/workflows/*.yml` hatte keine klassischen TODO/FIXME/WIP-Marker.
- Nächste echte Arbeit ist Phase 2 (`v0.5.0`):
  - Greybel-Build-Verifikation in CI
  - `scripts/ci-build.sh` auf aktive `.src`-Verzeichnisse erweitern
  - Composite Action für Node-/Tooling-Setup
  - Release-Drafter
- `ROADMAP.md` ist teilweise veraltet: `decypher` steht dort noch als nicht implementiert, obwohl `src/crypto/decypher.src` und `CHANGELOG.md` es als vorhanden listen.
- `README.md:38` markiert `gsc` als WIP; aktiver Source-Pfad muss geklärt werden.
- `plan.md`/`de/plan.md` enthalten vor allem historische/stale Hinweise.

**Dokumentation:** Scan-Ergebnis unter `~/docs/system/github-grayhack-todo-scan-YYYY-MM-DD.md` speichern. GitHub API/Issues/PRs nur mit expliziter Freigabe read-only abfragen; keine Issues automatisch erstellen.

Siehe `references/repo-todo-scan-2026-06-19.md` für den vollständigen Scan-Playbook-Auszug.

## Greybel CI Build Verification

Use `references/greybel-ci-build-2026-06-19.md` for the 2026-06-19 P0-CI implementation. For the concrete P0 build-fix run, also see the GreyHack skill reference `greyhack:references/p0-build-fixes-2026-06-19.md`.

Key rules:

- `greybel-js` is the npm package name; the executable is `greybel`.
- Build syntax is `greybel build <source.src> <output-dir>`, not `--out`/`--type exe`.
- Default CI scope is active `src/` + `tools/`; `greyhack-tools/` is opt-in because it contains imported/stale sources.
- Real Greybel verification should be allowed to fail on active source syntax errors; do not hide failures with a permissive CI gate.

## Issue-Body-Vorlage

```markdown
## Zweck

## Betroffenes Modul / Tool

## Beschreibung

## Schritte zur Reproduktion / Umsetzung

## Erwartetes Ergebnis

## Definition of Done

## Referenzen

- ROADMAP.md
- GitHub-Guide mit GrayHack.pdf
```

set -euo pipefail
## Commit-Konventionen

Muster:

```text
<type>(<scope>): <subject> [Refs #<issue>]
```

set -euo pipefail
Typen:

| Typ | Bedeutung |
|---|---|
| `feat` | neue Funktion |
| `fix` | Bugfix |
| `docs` | Dokumentation |
| `tool` | neues Tool oder Tool-Erweiterung |
| `refactor` | Refactoring ohne Funktionsänderung |
| `chore` | Wartung, Build, CI, Repo-Aufgaben |

Beispiele:

```text
feat(filecore): add base file helpers Refs #5
fix(buildcore): validate bin path before safeBuild Refs #6
docs(readme): document issue workflow Refs #7
tool(decypher): add initial decryption helpers Refs #123
```

set -euo pipefail
## Standard-Workflow

### 1. GitHub-Auth prüfen

```bash
gh auth status
gh repo view Toqsick/greyscripts
```

set -euo pipefail
Wenn nicht authentifiziert:

```bash
gh auth login
```

set -euo pipefail
### 2. Issue erstellen

```bash
gh issue create \
  --title "[CI] Add Greybel build verification to CI" \
  --label "enhancement" \
  --milestone "v0.5.0" \
  --body-file ~/docs/system/github-grayhack-issues/greybel-ci.md
```

set -euo pipefail
### 3. Issue abrufen

```bash
gh issue view <NUM> --json number,title,labels,milestone,state,url
```

set -euo pipefail
### 4. Branch erzeugen

```bash
ISSUE=123
SHORT=decypher-base

git fetch origin
git checkout main
git pull --ff-only
git checkout -b "feature/${ISSUE}-${SHORT}"
git push -u origin "feature/${ISSUE}-${SHORT}"
```

set -euo pipefail
### 5. Commit schreiben

```bash
git add .
git commit -m "feat(decypher): add initial decryption helpers Refs #123"
git push
```

set -euo pipefail
### 6. PR öffnen

```bash
gh pr create \
  --title "feat(decypher): add initial decryption helpers Closes #123" \
  --body-file /tmp/github_grayhack_pr_body.md
```

set -euo pipefail
PR-Body-Vorlage:

```markdown
## Summary

Closes #123

## Changes

- ...

## Definition of Done

- [ ] Issue verlinkt
- [ ] Commit referenziert Issue
- [ ] Doku aktualisiert
- [ ] Tests/Build geprüft, falls vorhanden
- [ ] Keine unnötigen Änderungen
```

set -euo pipefail
## Doku-Template

Datei:

```text
~/docs/system/github-grayhack-run-YYYY-MM-DD.md
```

set -euo pipefail
Inhalt:

```markdown
# GitHub GrayHack Workflow Run

## Datum

## Ziel

## Issue

- Nummer:
- Titel:
- Label:
- Milestone:
- URL:

## Branch

- Name:
- Status:

## Schritte

1. ...
2. ...

## Ergebnis

- Issue erstellt: ja/nein
- Branch erstellt: ja/nein
- PR geöffnet: ja/nein
- Doku aktualisiert: ja/nein

## Nächster Schritt

## Entscheidungen

- ...
```

set -euo pipefail
## Status-Dokument

Datei:

```text
~/docs/system/github-grayhack-status.md
```

set -euo pipefail
Template:

```markdown
# GitHub GrayHack Status

## Offene Issues

| Issue | Titel | Label | Milestone | Status |
|---|---|---|---|---|

## Offene PRs

| PR | Titel | Branch | Status |
|---|---|---|---|

## Letzte Aktivität

- ...

## Nächste empfohlene Aktion

- ...
```

set -euo pipefail
## `.gitattributes`-Konfliktlösung

Falls wieder ein Merge-Konflikt in `.gitattributes` auftaucht, diese Version verwenden:

```gitattributes
# Git LFS recommendation
*.pdf filter=lfs diff=lfs merge=lfs -text

# GreyScript Quelldateien als GreyScript markieren
*.src linguist-language=GreyScript
*.gs linguist-language=GreyScript

# Dokumentation nicht zur Sprachstatistik zaehlen
docs/** linguist-documentation
*.md linguist-documentation

# Hilfsskripte nicht zur Sprachstatistik zaehlen
scripts/** linguist-vendored
tools/** linguist-vendored
```

set -euo pipefail
## Telegram-Eskalationsvorlage

```text
GitHub GrayHack Workflow braucht Entscheidung:

Issue: #123 — feat(decypher): add initial decryption helpers
Option A: Branch erstellen und Issue auf in progress setzen
Option B: erst Issue-Body ergänzen
Option C: pausieren

Empfehlung: A
```

set -euo pipefail
## Cron-Monitoring

Optional:

```text
Alle 30 Minuten:
1. gh issue list --repo Toqsick/greyscripts --state open --limit 50
2. gh pr list --repo Toqsick/greyscripts --state open --limit 50
3. gh issue list --repo Toqsick/greyscripts --state open --label "in progress" --limit 20
4. Status mit ~/docs/system/github-grayhack-status.md vergleichen
5. Bei Änderung Doku aktualisieren und zusammenfassen
6. Bei Entscheidung Telegram senden
7. Wenn nichts geändert: [SILENT]
```

set -euo pipefail
## GitHub Actions Workflow-Patterns

### Bot-Loop-Schutz in Auto-Reply-Workflows

Workflows die auf `issue_comment` oder `pull_request_review` reagieren müssen eigene Bot-Kommentare ignorieren, sonst entsteht eine Endlos-Schleife. Am Anfang jedes `github-script`-Blocks einfügen:

```javascript
// Bot-Loop-Schutz: Nicht auf eigene Kommentare antworten
const sender = context.payload.sender;
if (sender && sender.type === 'Bot') {
  core.info(`Ignoriere Bot-Kommentar von ${sender.login}`);
  return;
}
```

set -euo pipefail
### `core.setOutput()` statt `return {}`

In `actions/github-script@v7` werden Step-Outputs mit `core.setOutput()` übergeben, nicht mit `return {}`. Falsch:

```javascript
return { reminded: JSON.stringify(reminded) };
```

set -euo pipefail
Richtig:

```javascript
core.setOutput('reminded', JSON.stringify(reminded));
```

set -euo pipefail
Nachfolgende Steps lesen dann: `${{ steps.remind_step.outputs.reminded }}`

### Auto-Label Workflow Pattern

Issues basierend auf Titel-Präfixen automatisch labeln:

```yaml
name: Auto Label Issues

on:
  issues:
    types: [opened]

permissions:
  contents: read
  issues: write

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - name: Auto-label issue
        uses: actions/github-script@v7
        with:
          script: |
            const title = context.payload.issue.title.toLowerCase();
            const labels = [];

            if (title.startsWith('bug:') || title.startsWith('fix:')) labels.push('bug');
            if (title.startsWith('feat:') || title.startsWith('feature:')) labels.push('enhancement');
            if (title.startsWith('docs:')) labels.push('docs');
            if (title.startsWith('tool:') || title.includes('router')) labels.push('new tool');
            if (title.includes('netcore') || title.includes('filecore')) labels.push('new module');

            if (labels.length > 0) {
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.payload.issue.number,
                labels: [...new Set(labels)]
              });
            }
```

set -euo pipefail
### Auto-Close Workflow Pattern

Issues schließen wenn ein PR mit `Closes #N`, `Fixes #N` oder `Resolves #N` gemergt wird:

```yaml
name: Auto Close Done Issues

on:
  pull_request:
    types: [closed]

permissions:
  contents: read
  issues: write
  pull-requests: read

jobs:
  close-issues:
    runs-on: ubuntu-latest
    if: github.event.pull_request.merged == true
    steps:
      - name: Close linked issues
        uses: actions/github-script@v7
        with:
          script: |
            const pr = context.payload.pull_request;
            const body = `${pr.title}\n${pr.body || ''}`;
            const issueRefs = [...body.matchAll(/(?:Closes|Fixes|Resolves)\s+#(\d+)/gi)]
              .map(match => parseInt(match[1]));
            const uniqueIssues = [...new Set(issueRefs)];

            for (const issueNumber of uniqueIssues) {
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issueNumber,
                state: 'closed'
              });
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issueNumber,
                body: `Abgeschlossen durch PR #${pr.number}: ${pr.title}`
              });
            }
```

set -euo pipefail
Siehe `references/github-actions-workflow-patterns.md` für vollständige Beispiele aus der 2026-06-18 Implementierung.

## Milestone-Management mit `gh api`

Die installierte `gh`-CLI-Version hat **kein** `gh milestone`-Subcommand. Milestones müssen über die REST-API verwaltet werden:

```bash
# Milestone erstellen
gh api repos/Toqsick/greyscripts/milestones \
  -f title=v0.4.0 \
  -f description='Agenten-ready GitHub Flow' \
  -f state=open >/dev/null 2>&1 || true

# Milestone-ID abrufen
MILESTONE_ID=$(gh api repos/Toqsick/greyscripts/milestones \
  --jq '.[] | select(.title=="v0.4.0") | .number')

# Issue einem Milestone zuweisen (PATCH, milestone als Integer)
gh api -X PATCH repos/Toqsick/greyscripts/issues/3 \
  -f milestone=$MILESTONE_ID
```

set -euo pipefail
**Pitfall:** `milestone` muss als Integer übergeben werden, nicht als String. Bei `-f milestone="1"` kommt HTTP 422: `"1" is not an integer or null`.

## Subagent-Dispatch: PRs nachschieben

Subagents erstellen Branches und committen/pushen, aber **erstellen keine Pull Requests automatisch**. Nach dem Dispatch muss ein eigener PR-Creation-Schritt folgen:

```bash
# 1. Branches prüfen
git branch -a | grep 'fix/'

# 2. PRs manuell erstellen
gh pr create --base develop --head fix/auto-label-workflow \
  --title "feat(workflows): add auto-label for issues" \
  --body "Fixes #3

## Changes
- Added auto-label workflow

## Testing
- YAML lint passed"

# 3. Optional direkt mergen wenn validiert
gh pr merge 25 --merge --delete-branch
```

set -euo pipefail
**Merke:** Subagent-Ergebnisse sind nicht fertig bis PRs existieren und gemergt sind. Immer nach dem Dispatch `gh pr list` prüfen.

## CLI-Pitfall: gh ohne lokales Git-Repo

Wenn Hermes nicht in einem lokalen Checkout von `Toqsick/greyscripts` läuft, dürfen `gh issue list` und `gh pr list` nicht ohne `--repo` ausgeführt werden. `gh` versucht sonst, das Repo aus dem aktuellen Git-Arbeitsverzeichnis abzuleiten und schlägt fehl:

```text
failed to run git: fatal: Kein Git-Repository
```

set -euo pipefail
Korrektes Muster für Cronjobs und Hermes-Sessions außerhalb des Repos:

```bash
gh issue list --repo Toqsick/greyscripts --state open --limit 5 \
  --json number,title,labels,milestone,state,url

gh pr list --repo Toqsick/greyscripts --state open --limit 5 \
  --json number,title,headRefName,state,url
```

set -euo pipefail
## Sicherheit und Grenzen

- Keine destruktiven Git-Befehle ohne explizite Bestätigung.
- Kein Force-Push.
- Kein Merge ohne Review-Status oder explizite Freigabe.
- Keine GitHub-Aktionen ausführen, wenn `gh auth status` fehlschlägt.
- Wenn `gh` nicht verfügbar oder nicht authentifiziert ist, nur Plan und Befehle vorbereiten.

## Nützliche Befehle

```bash
# Issues
gh issue list --state open --limit 50
gh issue list --state open --label bug --limit 20
gh issue list --state open --label "in progress" --limit 20

# PRs
gh pr list --state open --limit 50
gh pr status

# Repo
gh repo view Toqsick/greyscripts

# Lokale Doku
mkdir -p ~/docs/system/github-grayhack-issues
mkdir -p ~/docs/system/github-grayhack-runs
```

## Quellen

- `/home/bratan/Downloads/GitHub-Guide mit GrayHack.pdf`
- `/home/bratan/docs/system/github-grayhack-guide.md`
- `/home/bratan/.hermes/plans/github-grayhack-automation.md`
- `/home/bratan/docs/system/github-grayhack-todo-scan-2026-06-19.md`
- `references/repo-todo-scan-2026-06-19.md`
- `references/greybel-ci-build-2026-06-19.md`
