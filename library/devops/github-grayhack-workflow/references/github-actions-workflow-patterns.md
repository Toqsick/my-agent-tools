# GitHub Actions Workflow Patterns — 2026-06-18 Implementation Notes

Diese Datei dokumentiert die konkreten Patterns die am 2026-06-18 im `greyscripts`-Repo implementiert wurden. Sie ist als Copy-Paste-Referenz für zukünftige Workflow-Erweiterungen gedacht.

---

## 1. Bot-Loop-Schutz (`auto-pr-reply.yml`)

**Problem:** Workflow reagierte auf `issue_comment:created` und damit auch auf eigene Bot-Kommentare → Endlos-Schleife.

**Lösung:** Am Anfang des `github-script`-Blocks:

```javascript
// Bot-Loop-Schutz: Nicht auf eigene Kommentare antworten
const sender = context.payload.sender;
if (sender && sender.type === 'Bot') {
  core.info(`Ignoriere Bot-Kommentar von ${sender.login}`);
  return;
}
```

**Commit:** `8f6e6579e9b6a4ad973ff1ca99ce4d8b81e7a394`
**PR:** #23 (gemergt)

---

## 2. `core.setOutput()` Fix (`pr-reminder.yml`)

**Problem:** Step-Output wurde mit `return {}` zurückgegeben, nachfolgende Steps bekamen leere Daten.

**Falsch:**
```javascript
return { reminded: JSON.stringify(reminded) };
```

**Richtig:**
```javascript
core.setOutput('reminded', JSON.stringify(reminded));
```

**Zusatzfix:** Doppelter `env:`-Block in derselben Datei zusammengeführt damit `yamllint` durchläuft.

**Commit:** `c070b62`
**PR:** #24 (gemergt)

---

## 3. Auto-Label Workflow (`auto-label.yml`)

**Trigger:** `issues: opened`

**Logik:**
- `bug:` / `fix:` → `bug`
- `feat:` / `feature:` → `enhancement`
- `docs:` → `docs`
- `tool:` / enthält `router` → `new tool`
- enthält `netcore` / `filecore` → `new module`

**Commit:** `88adaa4c53e3d57feb087e56a057f4559cb661e0`
**PR:** #25 (gemergt)

---

## 4. Auto-Close Workflow (`auto-close-done.yml`)

**Trigger:** `pull_request: closed` mit `if: github.event.pull_request.merged == true`

**Logik:**
1. PR-Titel + Body durchsuchen nach `Closes #N`, `Fixes #N`, `Resolves #N`
2. Issues schließen mit `github.rest.issues.update(... state: 'closed')`
3. Kommentar posten: `Abgeschlossen durch PR #X: <PR-Titel>`

**Commit:** `ec3335e2265be8215e5268296fe3e40505d468e8`
**PR:** #26 (gemergt)

---

## 5. Milestone per API erstellen

**Pitfall:** `gh milestone` existiert in der installierten CLI-Version nicht.

**Funktionierender Weg:**

```bash
# Milestone erstellen
gh api repos/Toqsick/greyscripts/milestones \
  -f title=v0.4.0 \
  -f description='Agenten-ready GitHub Flow: Auto-Label, Auto-Close, Bot-Loop-Fixes, Hermes CLI' \
  -f state=open >/dev/null 2>&1 || true

# Milestone-ID abrufen
MILESTONE_ID=$(gh api repos/Toqsick/greyscripts/milestones \
  --jq '.[] | select(.title=="v0.4.0") | .number')

# Issue zuweisen (PATCH, milestone als Integer!)
gh api -X PATCH repos/Toqsick/greyscripts/issues/3 \
  -f milestone=$MILESTONE_ID
```

**Wichtig:** `-f milestone=1` muss als Integer kommen. Strings führen zu HTTP 422: `"1" is not an integer or null`.

---

## 6. Subagent-Dispatch: PRs nachschieben

**Beobachtung:** Subagents erstellen Branches und pushen Commits, aber keine Pull Requests.

**Nach dem Dispatch immer ausführen:**

```bash
# 1. Branches prüfen
git branch -a | grep -E 'workflow|auto|pr-reminder' | sort

# 2. PRs erstellen
gh pr create --base develop --head feature/workflow-bot-loop-protection \
  --title "fix(workflows): add bot-loop protection to auto-pr-reply" \
  --body "Fixes #3

## Changes
- Added Bot-Sender check

## Testing
- YAML lint passed"

# 3. Mergen wenn validiert
gh pr merge 23 --merge --delete-branch
```

**Merke:** Subagent-Ergebnisse sind erst fertig wenn PRs existieren, validiert und gemergt sind.

---

## 7. Workflow-Lint

```bash
.github/workflows/lint-workflows.sh
```

**Hinweis:** `yamllint` zeigt typische `on:`-Truthy-Warnings in GitHub Actions Workflows an. Diese sind bekannt und nicht kritisch. Entscheidend ist Exit Code 0 ohne echte Fehler.
