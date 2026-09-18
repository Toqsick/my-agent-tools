#!/usr/bin/env bash
# loop-state.sh — State-Handling für .dev-loop/state.json + Single-Writer-Lock.
#
# Lock-Design: Agenten-Sessions sind stundenlang aktiv, das Script selbst ist
# kurzlebig — der Lock hält deshalb session-id + Zeitpunkt, nicht eine PID.
# Eine Session verlängert ihren Lock durch erneutes `lock <eigene-id>` (Heartbeat).
# Fremder Lock: jünger als 6 h → Verweigerung; älter → gilt als stale.
#
# Usage: loop-state.sh <repo-path> <command> [args]
#   lock <session-id>     Lock setzen/verlängern (idempotent für eigene id)
#   unlock [session-id] [--force]  Lock freigeben (fremder frischer Lock: id ODER --force nötig)
#   set <key> <value>     State-Feld setzen (phase/issue/… landen in current.*)
#   get [key]             State oder einzelnes Feld ausgeben
#   show                  State hübsch + Lock-Status
# State-Schema: skills/dev-loop/references/state-contract.md
# Exit: 0 ok; 1 = lebender fremder Lock; 2 = Benutzungs-/Verarbeitungsfehler.
set -euo pipefail

[ $# -ge 2 ] || { sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
REPO=$1
CMD=$2
DIR=${REPO%/}/.dev-loop
STATE=$DIR/state.json
LOCK=$DIR/lock
STALE_SECS=$((6 * 3600))

mkdir -p "$DIR"

lock_sid() {
  [ -f "$LOCK" ] || return 0
  sed -n 's/^session=//p' "$LOCK"
}
lock_age() { # Sekunden seit Lock-Änderung (leer = kein Lock)
  [ -f "$LOCK" ] || return 0
  echo $(( $(date +%s) - $(stat -c %Y "$LOCK") ))
}

case "$CMD" in
  lock)
    [ $# -ge 3 ] || { echo "lock braucht <session-id>" >&2; exit 2; }
    SID=$3
    if [ -f "$LOCK" ]; then
      HELD=$(lock_sid); AGE=$(lock_age)
      if [ "$HELD" = "$SID" ]; then
        : # Heartbeat: unten neu schreiben
      elif [ "${AGE:-0}" -lt "$STALE_SECS" ]; then
        echo "LOCK HELT: session '${HELD:-?}' (seit ${AGE:-?}s < ${STALE_SECS}s) — kein zweiter Loop." >&2
        exit 1
      else
        echo "stale Lock (session '${HELD:-?}', ${AGE:-?}s alt) — überschreibe." >&2
      fi
    fi
    printf 'session=%s\nsince=%s\n' "$SID" "$(date -Is)" > "$LOCK"
    echo "locked: $SID"
    ;;
  unlock)
    SID=""; FORCE=no
    for a in "${@:3}"; do
      if [ "$a" = "--force" ]; then FORCE=yes; else SID=$a; fi
    done
    if [ -f "$LOCK" ]; then
      HELD=$(lock_sid); AGE=$(lock_age)
      if [ "$FORCE" != yes ] && [ "$SID" != "${HELD:-}" ] \
         && [ "${AGE:-0}" -lt "$STALE_SECS" ]; then
        echo "Lock gehört '${HELD:-?}' (${AGE:-?}s alt, frisch) — eigene session-id angeben oder --force." >&2
        exit 1
      fi
      rm -f "$LOCK"; echo "unlocked"
    else
      echo "kein Lock vorhanden"
    fi
    ;;
  set)
    [ $# -ge 4 ] || { echo "set braucht <key> <value>" >&2; exit 2; }
    KEY=$3; VAL=$4
    python3 - "$STATE" "$KEY" "$VAL" <<'PYEOF' || { echo "loop-state.sh: set fehlgeschlagen" >&2; exit 2; }
import datetime, json, os, sys
path, key, val = sys.argv[1], sys.argv[2], sys.argv[3]
state = {}
if os.path.exists(path):
    with open(path) as f:
        state = json.load(f)
current_fields = ("phase", "issue", "task_id", "impl_iterations", "verify_result",
                  "pr", "brief_file", "evidence_last")
target = state.setdefault("current", {}) if key in current_fields else state
if key in ("issue", "impl_iterations"):  # numerische Felder nicht als String speichern
    try:
        val = int(val)
    except ValueError:
        pass
target[key] = val
state["updated"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
    f.write("\n")
PYEOF
    ;;
  get)
    KEY=${3:-}
    python3 - "$STATE" "$KEY" <<'PYEOF'
import json, os, sys
path, key = sys.argv[1], sys.argv[2] or None
if not os.path.exists(path):
    print("{}")
else:
    with open(path) as f:
        state = json.load(f)
    if not key:
        print(json.dumps(state, ensure_ascii=False))
    else:
        cur = state.get("current", {})
        print(json.dumps(cur.get(key, state.get(key)), ensure_ascii=False))
PYEOF
    ;;
  show)
    python3 - "$STATE" <<'PYEOF'
import json, os, sys
path = sys.argv[1]
if os.path.exists(path):
    with open(path) as f:
        print(json.dumps(json.load(f), ensure_ascii=False, indent=2))
else:
    print("(kein state)")
PYEOF
    if [ -f "$LOCK" ]; then
      echo "lock: session=$(lock_sid) alter=$(lock_age)s (stale ab ${STALE_SECS}s)"
    else
      echo "lock: keiner"
    fi
    ;;
  *)
    echo "unbekannter Befehl: $CMD" >&2; exit 2
    ;;
esac
