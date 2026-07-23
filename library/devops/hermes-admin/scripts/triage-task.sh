#!/bin/bash
# triage-task.sh
# Erstellt Triage-Task + wartet auf Auto-Decompose-Tick + zeigt Result.
# Nutzung: bash triage-task.sh "<title>" [body]
#
# Pitfall #16: --triage Flag (nicht --status triage)

set -e

title="${1:?Usage: $0 <title> [body]}"
body="${2:-Bitte präziser formulieren.}"

echo "═══ Triage-Task erstellen ═══"
echo "Title: $title"
echo "Body: $body"
echo

# Create (Pitfall #16: --triage, nicht --status triage)
result=$(hermes kanban create "$title" --triage --body "$body" --json 2>&1)
task_id=$(echo "$result" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('id','?'))" 2>/dev/null || echo "?")

echo "Created: $task_id"
echo

# Warte auf Dispatch-Tick (60s) + Decomp-Run
echo "Waiting 75s for auto-decompose tick..."
sleep 75

# Resultat anzeigen
echo
echo "═══ Result ═══"
echo "─── Triage-Status ───"
hermes kanban list --status triage 2>&1 | head -10
echo
echo "─── Parent-Task ───"
hermes kanban show "$task_id" 2>&1 | head -15
echo
echo "─── Sub-Tasks (Children) ───"
hermes kanban show "$task_id" --json 2>&1 | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
children = d.get('children', [])
if children:
    print(f'{len(children)} Sub-Tasks erzeugt:')
    for c in children:
        print(f'  - {c}')
else:
    print('Keine Children — Auto-Decomp hat (noch) nicht gefeuert.')
" 2>/dev/null || echo "(JSON-Parse fehlgeschlagen)"