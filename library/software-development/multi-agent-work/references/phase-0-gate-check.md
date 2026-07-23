# Phase 0 — Pre-Flight Gate-Check (Details)

Vor dem Spawn von Subagenten die Verfügbarkeit von `delegate_task` prüfen. Ein Gate-Blocker mitten im Workflow kostet mehr Zeit als der Check davor.

## Smoke-Test

```python
# Prüfe: delegate_task verfügbar?
# Smoke-Test: delegate_task mit echo GATE_OK
# Folgende Muster blockieren das Gate:
#   "HermesUltraCode gate · escalated" → HermesUltraCode blockiert
#   "base_prompt is empty; nothing to dispatch" → Provider-Fehler
#   "Cannot resolve delegation provider" → delegation.provider falsch
#
# BEI GATE-BLOCKER: ERST FIXEN, DANN FALLBACK!
#   → Step 1: Gate deaktivieren (siehe unten)
#   → Step 2: Hermes-Prozess NEU STARTEN (nicht nur /reset!)
#   → Step 3: Erneut testen
#   → Step 4: Nur wenn Fix nicht möglich → Parent-Direct-Fallback
```

## Gate-Fix-Befehle (VOR Fallback versuchen!)

Wenn `delegate_task` mit HermesUltraCode/Tirith/Provider-Fehlern blockiert:

```bash
# 1. HermesUltraCode deaktivieren
hermes plugins disable hermesultracode
hermes tools disable hermesultracode

# 2. Tirith-Security deaktivieren
hermes config set security.tirith_enabled false

# 3. Delegation-Provider prüfen und fixen
hermes config set delegation.provider openrouter
hermes config set delegation.model deepseek/deepseek-v4-pro

# 4. HERMES DESKTOP KOMPLETT NEU STARTEN (nicht nur /reset!)
# /reset reicht NICHT — Prozess muss neu starten für Config-Änderungen
```

**Erst wenn der Fix nicht funktioniert:** `references/parent-direct-fallback.md` nutzen.

## Modus-spezifisches Verhalten

- **Experiment-Mode:** Phase 0 ist Pflicht. Dokumentiere, ob Subagenten funktionieren oder nicht.
- **Delivery-Mode:** Phase 0 darf übersprungen werden, wenn Subagenten in dieser Session schon einmal funktioniert haben. Bei erstmaligem Spawn: kurz prüfen.