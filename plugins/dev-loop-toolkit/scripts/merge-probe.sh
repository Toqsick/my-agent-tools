#!/usr/bin/env bash
# merge-probe.sh — ermittelt den Merge-Modus für ein Repo (dev-loop LAND-Phase).
#
#   HTTP 200 → Protection aktiv          → native-auto  (gh pr merge --squash --auto)
#   HTTP 403 → Free-Plan/privat/Rechte   → agent-side   (checks --watch + squash)
#   HTTP 404 → keine Protection gesetzt  → agent-side   (--auto braucht Requirements)
#
# Usage: merge-probe.sh <owner/repo> [branch=main]
# Exit: 0 in allen bewertbaren Fällen; 2 = gh nicht authentifiziert/Netzwerk;
#       3 = Repo/Zweig nicht gefunden (Tippfehler?) oder unklarer Status —
#           nicht automatisch mergen, Mensch fragen.
set -euo pipefail

usage() { sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 3; }

if [ $# -lt 1 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then usage; fi
REPO=$1
BRANCH=${2:-main}

# Vorab: existiert Repo::Zweig überhaupt? (404 der Protection-API wäre sonst ein
# Tippfehler, der als "keine Protection" dokumentiert würde.)
resp=$(gh api -i "repos/${REPO}/branches/${BRANCH}" 2>/dev/null || true)
bstatus=$(printf '%s' "$resp" | head -1 | awk '{print $2}')
case "$bstatus" in
  200) ;;
  404)
    echo "merge-probe.sh: repos/${REPO} :: ${BRANCH} nicht gefunden — Tippfehler?" >&2
    exit 3
    ;;
  "")
    echo "merge-probe.sh: gh api nicht erreichbar/nicht authentifiziert (repos/${REPO})" >&2
    exit 2
    ;;
  *)
    echo "merge-probe.sh: unerwarteter HTTP ${bstatus} beim Zweig-Check" >&2
    exit 3
    ;;
esac

resp=$(gh api -i "repos/${REPO}/branches/${BRANCH}/protection" 2>/dev/null || true)
status=$(printf '%s' "$resp" | head -1 | awk '{print $2}')

case "$status" in
  200)
    mode=native-auto
    reason="Branch-Protection aktiv — Requirements vorhanden, --auto erlaubt"
    ;;
  403)
    mode=agent-side
    reason="HTTP 403 — Free-Plan/privat oder keine Admin-Rechte (pokerogue-Präzedenz)"
    ;;
  404)
    mode=agent-side
    reason="HTTP 404 — keine Protection konfiguriert; --auto ohne Requirements wirkungslos"
    ;;
  "")
    echo "merge-probe.sh: gh api nicht erreichbar/nicht authentifiziert (repos/${REPO})" >&2
    exit 2
    ;;
  *)
    echo "unknown HTTP ${status} — NICHT automatisch fortfahren; Merge-Modus vom Menschen klären lassen" >&2
    exit 3
    ;;
esac

echo "$mode"
echo "# Grund: $reason"
echo "# Zweig: ${REPO} :: ${BRANCH}"
echo "# Ergebnis in WORKFLOW.md dokumentieren (bitte nicht erneut danach suchen)."
