#!/usr/bin/env bash
# frontier.sh — offene Issues eines GitHub-Milestones als sortierte Dev-Loop-Frontier.
#
# Sortierung: Dep-Edges aus den Issue-Bodies ("Depends-on: #N", "depends on #N",
# "Setzt #N voraus") — Issues mit offener Abhängigkeit im selben Milestone stehen
# hinten; untereinander stabile Reihenfolge nach Issue-Nummer.
# Gate-/blocked-/idea-Issues werden separat ausgewiesen (Regeln: SKILL dev-loop).
#
# Hinweis: Abhängigkeiten auf Issues außerhalb des abgefragten Milestones gelten
# als erfüllt (geprüft wird nur die offene Menge dieses Milestones).
#
# Usage:
#   frontier.sh <owner/repo> <milestone-title> [--json]
# Exit: 0 = Frontier ermittelt (auch wenn leer); 2 = gh-/Verarbeitungsfehler;
#       3 = Aufruffehler (usage).
set -euo pipefail

usage() { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 3; }

[ $# -ge 2 ] || usage
REPO=$1
MILESTONE=$2
FMT=text
[ "${3:-}" = "--json" ] && FMT=json

raw=$(gh issue list -R "$REPO" --milestone "$MILESTONE" --state open \
      --json number,title,body,labels --limit 200 2>/dev/null) || {
  echo "frontier.sh: gh issue list für '$REPO' / Milestone '$MILESTONE' fehlgeschlagen" >&2
  exit 2
}

# Leere Ausgabe kann ein Tippfehler im Milestone-Namen sein (gh filtert nur, fehlt
# nicht) — dann explizit gegen die existierenden Milestones prüfen statt "leer= fertig".
if [ "$raw" = "[]" ]; then
  if ! gh api "repos/${REPO}/milestones" --jq '.[].title' 2>/dev/null \
       | grep -Fqx -- "$MILESTONE"; then
    echo "frontier.sh: Milestone '$MILESTONE' existiert nicht in $REPO — Tippfehler?" >&2
    exit 2
  fi
fi

tmp=$(mktemp /tmp/frontier-raw.XXXXXX)
trap 'rm -f "$tmp"' EXIT
printf '%s' "$raw" > "$tmp"

FRONTIER_FILE=$tmp FRONTIER_FMT=$FMT FRONTIER_REPO=$REPO FRONTIER_MS=$MILESTONE \
python3 <<'PYEOF' || { echo "frontier.sh: Verarbeitung fehlgeschlagen" >&2; exit 2; }
import json, os, re, sys

fmt = os.environ.get("FRONTIER_FMT", "text")
with open(os.environ["FRONTIER_FILE"]) as f:
    issues = json.load(f)

def labels_of(it):
    return [str(l.get("name", "")).lower() for l in (it.get("labels") or [])]

def kind(it):
    title = (it.get("title") or "").lower()
    labs = labels_of(it)
    if title.startswith("gate:") or "gate" in labs:
        return "gate"
    if title.startswith("blocked:") or "blocked" in labs:
        return "blocked"
    if title.startswith("idea:") or "idea" in labs:
        return "idea"
    if re.search(r"^abnahme\s*:?\s*(mensch|pending|offen)", it.get("body") or "",
                 re.I | re.M):
        return "acceptance"
    return "task"

DEP1 = re.compile(r"depends[- ]on\s*:?\s*((?:#\s*\d+[\s,]*)+)", re.I)
DEP2 = re.compile(r"setzt\s+((?:#\s*\d+[\s,]*)+)\s+voraus", re.I)
NUM = re.compile(r"#\s*(\d+)")

def deps_of(it):
    body = it.get("body") or ""
    out = []
    for rx in (DEP1, DEP2):
        for m in rx.finditer(body):
            out += [int(n) for n in NUM.findall(m.group(1))]
    return out

tasks, gates, blocked, ideas, acceptance = [], [], [], [], []
for it in issues:
    k = kind(it)
    {"gate": gates, "blocked": blocked, "idea": ideas,
     "acceptance": acceptance}.get(k, tasks).append(it)

open_task_ids = {t["number"] for t in tasks}
ready, waiting = [], []
for t in sorted(tasks, key=lambda x: x["number"]):
    open_deps = sorted(d for d in deps_of(t) if d in open_task_ids and d != t["number"])
    (waiting if open_deps else ready).append((t, open_deps))

result = {
    "repo": os.environ["FRONTIER_REPO"],
    "milestone": os.environ["FRONTIER_MS"],
    "next": [t["number"] for t, _ in ready],
    "frontier": (
        [{"number": t["number"], "title": t["title"], "status": "ready"} for t, _ in ready]
        + [{"number": t["number"], "title": t["title"], "status": "waiting-on",
            "open_deps": d} for t, d in waiting]
    ),
    "gates_open": [{"number": g["number"], "title": g["title"]} for g in gates],
    "blocked": [{"number": b["number"], "title": b["title"]} for b in blocked],
    "acceptance_pending": [{"number": a["number"], "title": a["title"]}
                           for a in acceptance],
    "parked_ideas": [{"number": i["number"], "title": i["title"]} for i in ideas],
}

if fmt == "json":
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

print(f"Frontier — {result['repo']} · {result['milestone']}")
if result["next"]:
    print(f"  NÄCHSTES: #{result['next'][0]}")
for e in result["frontier"]:
    if e["status"] == "ready":
        print(f"  [ready ] #{e['number']} {e['title']}")
    else:
        ds = ", ".join(f"#{d}" for d in e["open_deps"])
        print(f"  [warten] #{e['number']} {e['title']} — braucht {ds}")
for g in result["gates_open"]:
    print(f"  [GATE  ] #{g['number']} {g['title']} → HALT bis Approval-Kommentar")
for b in result["blocked"]:
    print(f"  [block ] #{b['number']} {b['title']}")
for a in result["acceptance_pending"]:
    print(f"  [abnah ] #{a['number']} {a['title']} (Implementation evtl. fertig, Abnahme beim Menschen)")
for i in result["parked_ideas"]:
    print(f"  [idee  ] #{i['number']} {i['title']} (geparkt, nicht in Frontier)")
if result["gates_open"]:
    print("GATE-HALT: offene Gates stoppen Meilenstein-Übergang/Start (SKILL-Regeln).")
PYEOF
