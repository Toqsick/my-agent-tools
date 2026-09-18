# gh-recipes.md — exacte GitHub-Kommandos für den Loop

Alle Befehle mit explizitem `-R <owner/repo>` (deterministisch, kein cwd-Zufall).
GitHub MCP ist bewusst **nicht** im Spiel — alles über `gh` CLI (Single Source of Auth).
Issue-Anlage/Labels: kanonisch in plan-dev-loop → `references/issue-authoring.md`
(hier nur der Loop-Betrieb).

## Milestone-Frontier

```bash
# Offene Issues eines Milestones (Maschinenlesbar)
gh issue list -R OWNER/REPO --milestone "M9 — Titel" --state open \
  --json number,title,body,labels,updatedAt --limit 100

# Milestone-Fortschritt (GraphQL — gh hat kein natives Milestone-CRUD)
gh api graphql -f query='
query($owner:String!, $repo:String!, $num:Int!) {
  repository(owner:$owner, name:$repo) {
    milestone(number:$num) {
      title openIssues: issues(states:OPEN) { totalCount }
      closedIssues: issues(states:CLOSED) { totalCount }
    }
  }
}' -F owner=OWNER -F repo=REPO -F num=10

# Alle Milestones (Nummer für GraphQL besorgen)
gh api repos/OWNER/REPO/milestones --paginate
```

## Issues

```bash
gh issue view N -R OWNER/REPO --comments          # BRIEF-Input
gh issue close N -R OWNER/REPO --reason completed # erst NACH Evidenz-Kommentar:
gh issue comment N -R OWNER/REPO --body-file evidence.md
```

`Closes #N` / `Fixes #N` im PR-Body schließt das Issue beim Merge in die Default-Branch
automatisch — für Evidenz-Close trotzdem **vorab** den Evidenz-Kommentar setzen; wer
sich auf Auto-Close verlässt, verliert den Beweis-Ort. Abnahme-Issues: Auto-Close per
Formulierung vermeiden („Implementiert in #PR" statt „Closes").

## PR-Flow (LAND)

```bash
git push -u origin wip/T-9.3
gh pr create -R OWNER/REPO --title "T-9.3 Parity-Report-Werkzeug (#97)" \
  --body-file pr-body.md --milestone "M9 — Titel" --base main

gh pr checks N -R OWNER/REPO --watch     # blockiert; in ZCode: run_in_background=true

# Merge-Modus native-auto (Protection aktiv — via scripts/merge-probe.sh ermittelt):
gh pr merge N -R OWNER/REPO --squash --auto --delete-branch
# Merge-Modus agent-side (403/404 — privates Free-Repo):
gh pr merge N -R OWNER/REPO --squash --delete-branch

# Branch-Weg-Kontrolle (gh-Bug cli#9073: --auto -d löscht remote nicht immer)
git ls-remote --heads origin wip/T-9.3   # muss leer sein nach Merge

# CI rot am PR → Fix auf DEMSELBEN Branch:
git commit -am "fix(scope): CI-finding [T-9.3]" && git push
```

Niemals `--admin` (bypassed Requirements) und nie `--rebase`/`--merge`, wenn der
Repo-Kanon Squash sagt.

## Merge-Modus-Probe (Branch Protection)

```bash
# HTTP-Status der Protection-API entscheidet (siehe ${CLAUDE_PLUGIN_ROOT}/scripts/merge-probe.sh):
gh api -i repos/OWNER/REPO/branches/main/protection | head -1
#   HTTP 200 → Protection aktiv          → native-auto
#   HTTP 403 → Free-Plan/privat          → agent-side   (pokerogue-Fall, live 16.09.2026)
#   HTTP 404 → keine Protection gesetzt  → agent-side
```

Native Auto-Merge braucht ohnehin Requirements (Protection + ggf. Merge-Queue).
Wer Merge-Queue fährt, muss CI auf `merge_group` triggern können, sonst stallt jede
Queued-PR (GitHub-Doku: managing-a-merge-queue).

## agent-log

```bash
# Laufendes Status-Issue einmalig anlegen (harness-bootstrap), dann pro Session:
gh issue comment 28 -R OWNER/REPO --body-file session-log.md
```

## Schutz gegen Selbsttäuschung

- PR-Title trägt die Issue-Nummer `( #NN)`, der Body `Closes #NN` — beides, damit
  GraphQL-Sichten und Humans dieselbe Verbindung sehen.
- Evidenz-Kommentare zitieren Befehl + Exit-Code + Zahlen („verify: 300 Cases /
  45.020 Assertions, Exit 0"), nie nur „grün".
- `gh run list -R OWNER/REPO --limit 5` + `gh run view <id> --log-failed` für
  CI-Fehler-Ursachen vor jeder Fix-Hypothese.
