#!/bin/bash
# verify-plan-quality-gates.sh
# Runs S1-S7 Quality Gates against a plan file.
# Usage: bash /path/to/verify-plan-quality-gates.sh <plan-file>
# Exit code: 0 = all gates green, 1 = gates failed, 2 = file not found
#
# Quality Gates (from better-plan-strategy / glm-plan-m3-execute):
#   S1: Realit�ts-Status-Tabelle (Pre-Plan-Check)
#   S2: SSOT-Audit-Tabelle (optional, nur bei audit-driven)
#   S3: Konkrete Minuten-Sch�tzungen
#   S4: Atomic-Write Policy (soft check)
#   S5: Risiko-Sektion R1-Rn
#   S6: Wave-Strategie (bei >3 Tasks)
#   S7: Done-Kriterium Checkbox-Liste

PLAN="${1:-$HOME/.hermes/plans/last-plan.md}"
PASS=true
TASK_COUNT=0

if [ ! -f "$PLAN" ]; then
    echo "� Plan-File nicht gefunden: $PLAN"
    exit 2
fi

echo "═══════════════════════════════════════════════════════════"
echo "PLAN QUALITY GATES - $(basename "$PLAN")"
echo "═══════════════════════════════════════════════════════════"
echo ""

# --- S1: Realit�ts-Status-Tabelle ---
cnt=$(grep -c "Realit�ts-Status\|Reality-Check\|Live-Verifik" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "� S1: Realit�ts-Status-Tabelle ($cnt Treffer)"
else
    echo "� S1: Realit�ts-Status-Tabelle FEHLT"
    echo "   -> Plan braucht eine verifizierte Realit�tstabelle vor den Tasks"
    PASS=false
fi

# --- S2: SSOT-Audit-Tabelle (optional) ---
cnt=$(grep -c "Geplanter Status\|Brief-Behauptung\|Tats�chlicher Status" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "� S2: SSOT-Audit-Tabelle ($cnt Treffer)"
elif grep -qi "audit\|refactor\|backlog" "$PLAN" 2>/dev/null; then
    echo "� S2: SSOT-Tabelle fehlt, aber Plan scheint audit-driven - empfohlen"
else
    echo "- S2: SSOT-Tabelle (nicht erforderlich)"
fi

# --- S3: Konkrete Minuten-Sch�tzungen ---
cnt=$(grep -cE "[0-9]+ Min" "$PLAN" 2>/dev/null || echo 0)
wave_cnt=$(grep -cE "Welle|Wave" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "� S3: Minuten-Sch�tzungen ($cnt Treffer)"
elif [ "$wave_cnt" -ge 1 ]; then
    echo "� S3: Minuten-Sch�tzungen FEHLEN - braucht Sch�tzungen f�r Wave-Planung"
    PASS=false
else
    echo "� S3: Keine Minuten-Sch�tzungen (ok f�r trivialen Plan ohne Waves)"
fi

# --- S4: Atomic-Write Policy (soft) ---
cnt=$(grep -c "Atomic-Write\|write_file.*not.*patch\|ein.*write_file" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "� S4: Atomic-Write Policy ($cnt Treffer)"
else
    echo "- S4: Atomic-Write Policy nicht explizit"
fi

# --- S5: Risiko-Sektion R1-Rn ---
cnt=$(grep -cE "^###? R[0-9]" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "� S5: Risiko-Sektion ($cnt Risiko-Items)"
else
    echo "� S5: Risiko-Sektion R1-Rn FEHLT"
    PASS=false
fi

# --- S6: Wave-Strategie ---
cnt=$(grep -cE "Welle|Wave" "$PLAN" 2>/dev/null || echo 0)
task_cnt=$(grep -cE "^### Task [0-9]" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "� S6: Wave-Strategie ($cnt Treffer)"
elif [ "$task_cnt" -ge 4 ]; then
    echo "� S6: Wave-Strategie FEHLT - $task_cnt Tasks brauchen Wave-Gruppierung"
    PASS=false
else
    echo "- S6: Wave-Strategie (<=3 Tasks, nicht n�tig)"
fi

# --- S7: Done-Kriterium Checkbox-Liste ---
cnt=$(grep -cE "^- \[ \]" "$PLAN" 2>/dev/null || echo 0)
if [ "$cnt" -ge 1 ]; then
    echo "� S7: Done-Kriterium ($cnt Checkboxen)"
else
    echo "� S7: Done-Kriterium Checkbox-Liste FEHLT"
    PASS=false
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
if $PASS; then
    echo "  � ALLE 7 GATES GREEN - Plan bereit f�r Dispatch"
    exit 0
else
    echo "  � GATES FAILED - Plan braucht �berarbeitung"
    echo "  Zur�ck zu GLM mit spezifischem Feedback zu den �-Gates"
    exit 1
fi
