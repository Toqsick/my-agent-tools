# Cron Error Categories — 4-Category Diagnostic Model

> Real session examples from Basti's workstation (2026-07-08).
> Each category has a distinct root cause, telltale signature, and fix path.

## Category A: Script-cron with missing path/env

**Session:** `orch-weekly-improve` (cron `b1381735ce35`, Sonntag 04:00, no_agent=true)

**Symptom:** `last_status=error` im Briefing, aber keine Telegram-Nachricht. Cron läuft durch, schreibt nur "ERROR: ..." in sein Log.

**Root cause:** Das Skript `/home/bratan/.hermes/scripts/orchestrator-self-improve.sh` referenziert:
```bash
SKILL_DIR="${SKILL_DIR:-/home/bratan/.hermes/skills/orchestration/hermes-orchestration}"
RUNS_DIR="${SKILL_DIR}/memory/runs"
```
Der `memory/runs/`-Pfad wurde gelöscht (unbekannt wann, vermutlich bei Skill-Umzug oder Cleanup). Seit 2026-07-05 schreibt das Skript:
```
ERROR: Runs directory missing: /home/bratan/.hermes/skills/orchestration/hermes-orchestration/memory/runs
```

**Diagnose:**
1. Skript-Log lesen: `cat ~/.hermes/orchestrator-self-improve.log | grep ERROR`
2. Pfad prüfen: `test -d /home/bratan/.hermes/skills/orchestration/hermes-orchestration/memory/runs`
3. Testrun: `bash ~/.hermes/scripts/orchestrator-self-improve.sh`

**Fix:** `mkdir -p /home/bratan/.hermes/skills/orchestration/hermes-orchestration/memory/runs`

**Pattern:** Skript-Crons (no_agent=true) laufen als bash-Script — sie haben keinen LLM-Schutz. Wenn eine referenzierte Datei/Verzeichnis verschwindet, läuft das Script trotzdem durch, schreibt "ERROR" in sein Log, und produziert kein Telegram-Output. Der `last_status=error` kommt vom non-zero exit code.

---

## Category B: Script-cron designed as manual-only

**Session:** `multi-agent-master-workflow-8h` (cron `76039d75e57d`, alle 8h, no_agent=true)

**Symptom:** `last_status=error` trotzdem das Skript mit `exit 0` endet.

**Root cause:** Das Skript `/home/bratan/.hermes/scripts/run-master-workflow.sh` hat einen Guard:
```bash
if [ -z "${HERMES_ENDPOINT:-}" ]; then
  echo "Kein HERMES_ENDPOINT gesetzt — Skill-Inventur (manual-only Modus):"
  if [ -f "$SKILL_PATH" ]; then
    head -50 "$SKILL_PATH"
  else
    echo "  (Pipeline-Spec nicht gefunden: $SKILL_PATH)"
  fi
  exit 0
fi
```
`HERMES_ENDPOINT` wurde nie gesetzt. Das Skript gibt "manual-only" aus und exit 0. Hermes zeigt `last_status=error` — vermutlich weil das Skript keine *actionable* Output produziert oder der Cron-Timeout-Tracker das Skript als "did nothing useful" erkennt.

**Diagnose:**
1. Skript direkt testen: `bash ~/.hermes/scripts/run-master-workflow.sh`
2. Output checken: "Kein HERMES_ENDPOINT gesetzt" = manuell-only Modus
3. Cron-Job-Definition checken: `cronjob action=list` → ist der Job überhaupt nötig?

**Fix:** Den Cron-Job entweder entfernen (wenn nie automatisch laufen soll) oder `HERMES_ENDPOINT` setzen und das Skript für Auto-Run ertüchtigen.

---

## Category C: LLM-driven cron with provider drift

**Session:** `yuno-daily-gallery` (cron `4999a33bdf1d`, täglich 21:00, LLM-driven)

**Symptom:** `last_status=error` mit sauberem RuntimeError im Gateway-Log.

**Root cause:** Der Cron wurde erstellt als globaler Provider `zai` + Model `glm-5` aktiv war. Nach einem Wechsel zu `minimax` + `MiniMax-M3` hat Hermes' Safety-Schutz (#44585) die Ausführung verweigert:
```
RuntimeError: Skipped to prevent unintended spend: global inference config drifted
since this job was created (provider 'zai' -> 'minimax'; model 'glm-5' -> 'minimax-m3'),
and this job is unpinned. No inference call was made.
```

**Diagnose:**
1. Gateway-Log: `journalctl --user -u hermes-gateway --no-pager -n 50 | grep 44585`
2. Cron-Definition: `cronjob action=list` → schau ob `model`-Feld gesetzt ist (fehlt = unpinned)

**Fix:**
```bash
cronjob action=update job_id=4999a33bdf1d model={provider=minimax model=minimax-m3}
```
Oder wenn der alte Provider wieder aktiv wird:
```bash
cronjob action=update job_id=4999a33bdf1d model={provider=zai model=glm-5}
```
**Wichtig:** Der Fix muss via `cronjob`-Tool (nicht via `hermes cron` CLI) erfolgen, da das CLI kein `--model`-Flag hat.

**Pattern:** Jeder globale Provider/Model-Change betrifft ALLE existierenden LLM-Crons. Ein Batch-Update aller unpinned LLM-Crons nach einem Provider-Wechsel ist empfehlenswert.

---

## Quick Reference: Find All Errors in One Command

```bash
# Gateway-Log (Category C = LLM drifts)
journalctl --user -u hermes-gateway --since "1h" --no-pager | grep -E "error|fail|44585|RuntimeError"

# Script-Logs (Category A = path drifts)
grep -rn "ERROR" ~/.hermes/orchestrator-*.log 2>/dev/null

# Cron-Status (alle Kategorien)
cronjob action=list
```

## Updated 2026-07-11
Expanded to 4 categories: added Category D (Silent-OK) from cron-fleet-audit-2026-07-11. Real-world example: orch-weekly-pipeline exits 0 despite all steps failing — Step 4 (Memory-Stats) acted as a 'lifeline' masking dead Steps 0-3.