#!/usr/bin/env bash
# ============================================================================
# self-service-fix.sh — TEMPLATE für self-service Hilfsscripts
# ============================================================================
# Pattern: ein Fix-Script das Basti selber ausführt, mit Review-Modus.
#
# Was bringt das?
#   1. Diff ist sichtbar bevor etwas kaputt geht (--dry-run)
#   2. Sudo wird nur an Stellen gebraucht wo es wirklich nötig ist
#   3. --askpass erlaubt PW aus dem Stream (für nicht-PTY-Aufrufer)
#   4. Strukturierter Logfile-Output (in /tmp/fix-*.log)
#   5. Am Ende klare "what's next" Anweisungen (Reboot, Test, etc.)
#
# Verwendung:
#   cp templates/self-service-fix.sh ~/fix-scripts/<task>.sh
#   vim ~/fix-scripts/<task>.sh   # Steps und Diagnose anpassen
#   bash ~/fix-scripts/<task>.sh --dry-run
#   bash ~/fix-scripts/<task>.sh
#
# Yuno-Konventionen:
#   - Cyan ▸  für Schritte, Grün ✔ für OK, Gelb ⚠ für Warnungen,
#     Rot ✖ für fatale Fehler.
#   - Diagnose-Step IMMER als allererstes — niemals blind reparieren.
#   - Jeder Schritt nutzt say/ok/warn/fail Helper, nicht echo direkt.
#   - sudo nur in need_sudo()-gewrappte Blöcke.
# ============================================================================

set -u                # undef. vars failen; set -e WEG wegen sudo!
set -o pipefail

LOG="/tmp/$(basename "${0%.sh}").log"
CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

# Options parsen (Standard-Mode: dry-run früh-anschauen)
DRY_RUN=0
ASK_PW=0
for arg in "$@"; do
  case "$arg" in
    --dry-run|-n) DRY_RUN=1 ;;
    --askpass|-A) ASK_PW=1 ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--askpass]"
      echo "  --dry-run  Nur Diagnose, KEINE Änderungen"
      echo "  --askpass  Sudo-PW via Stdin-Eingabe (für nicht-PTY-Aufrufer)"
      exit 0
      ;;
  esac
done

# Output-Helper (alle ge-Tee'd nach LOG)
say()    { echo -e "${CYAN}▸ $*${NC}"  | tee -a "$LOG"; }
ok()     { echo -e "${GREEN}✔ $*${NC}"  | tee -a "$LOG"; }
warn()   { echo -e "${YELLOW}⚠ $*${NC}" | tee -a "$LOG"; }
fail()   { echo -e "${RED}✖ $*${NC}"   | tee -a "$LOG"; exit 1; }

# Erste sinnvolle SUDO-Variable setzen (wird in need_sudo überschrieben)
[ "$EUID" -ne 0 ] && SUDO="sudo -n" || SUDO=""

# DRY-RUN Modus: ersetzt sudo durch echo "DRY:"
if [ "$DRY_RUN" -eq 1 ]; then
    SUDO="echo DRY-RUN:"
    warn "=== DRY-RUN MODE — Es werden KEINE Änderungen am System gemacht ==="
fi

# Hilfsfunktion: SUDO-Variable je nach Aufrufkontext setzen
need_sudo() {
  if [ "$EUID" -eq 0 ];       then return 0; fi                       # root
  if [ "$DRY_RUN" -eq 1 ];    then SUDO="echo DRY:"; return 0; fi     # dry-run
  if sudo -n true 2>/dev/null; then SUDO="sudo -n"; return 0; fi       # NOPASSWD
  if [ "$ASK_PW" -eq 1 ];     then SUDO="sudo -S"; return 0; fi       # Stdin PW
  warn "Brauche Sudo-PW. Starte das Script in einem Terminal:"
  echo "        bash $(realpath "$0")"
  echo "  oder mit Stdin-PW:"
  echo "        echo '<passwort>' | bash $0 --askpass"
  SUDO="sudo"
}

# --- Header ---
echo "==============================================================================="
echo "  $(basename "$0") — Self-Service Fix-Script  (Yuno-Konvention)"
echo "==============================================================================="
# Logfile frisch öffnen (alte Run-Spuren überschreiben)
: > "$LOG"
echo "" | tee -a "$LOG"
date | tee -a "$LOG"

# ============================================================================
# STEP 1 — IMMER Diagnose-Snapshot zuerst!
# ============================================================================
say "STEP 1 / N — Diagnose-Snapshot"
cat <<SNAPSHOT | tee -a "$LOG"
  Vor dem Fix:
    System           : $(uname -a | head -c 60)...
    Active User      : $(whoami)
    Sudo             : $(sudo -n true 2>/dev/null && echo "NOPASSWD OK" || echo "PW erforderlich")
SNAPSHOT
ok "Diagnose-Snapshot gemacht."

# ============================================================================
# STEP 2..N — Reparatur-Schritte
#
# In jedem Step:
#   1. say "STEP N / M — Kurzbeschreibung"
#   2. Diagnose-Check: ist das Problem überhaupt da?
#   3. need_sudo()  falls sudoize nötig
#   4. $SUDO befehl  ← keine auto-Aktion, immer mit warn vorne dran
#   5. ok "Ergebnis"
#
# Beispiel:
# say "STEP 2 / 3 — Paket reinstallieren"
# if command -v foobar >/dev/null; then
#   ok "foobar bereits vorhanden."
# else
#   warn "foobar fehlt. Re-installation:"
#   need_sudo
#   $SUDO apt install -y foobar 2>&1 | tee -a "$LOG"
#   command -v foobar >/dev/null && ok "foobar repariert" || fail "reparatur fehlgeschlagen"
# fi
# ============================================================================

# (Hier kommen die eigentlichen Reparatur-Schritte des konkreten Fixes)

# ============================================================================
# ABSCHLUSS-Check + nächste Schritte
# ============================================================================
echo ""
echo "==============================================================================="
echo "  ABSCHLUSS-Check"
echo "==============================================================================="
echo ""
ok "Fertig."
echo ""
echo "  Logfile für später anschauen:"
echo "        less $LOG"
echo ""
echo "  Bei Reboot-Bedarf:"
echo "        systemctl reboot"
echo "==============================================================================="
