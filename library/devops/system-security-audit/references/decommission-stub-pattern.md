# Decommission & Stub Pattern — Legacy Script → Skill Transition

> **Quelle:** MaxClaw-Script v1.0.0 (634 Zeilen, 24 KB) → `system-security-audit` Skill v1.1.0 (2026-07-13)
> Workstation-Audit auf Basti's Zorin OS: Altes Bash-Audit-Script war stale (Cluster-Topo vor 2026-07-04), produzierte nur False-Positives.
> Statt Rewrite → Decommission + Skill-Absorbption + PATH-Stub.

## Wann dieses Pattern triggern

- Ein Bash/Python-Script unter `~/50-System/bin/` oder `~/20-Workspace/scripts/` ist nachweislich **veraltet** (referenziert nicht mehr existierende Pfade, prüft Keys die nicht konsumiert werden)
- Der User sagt "D — Script neuschreiben" und eine Skill-basierte Alternative existiert bereits oder kann leicht geschaffen werden
- Ein Legacy-Script produziert dauerhaft **Rauschen** (False-Positives > 50 % der Findings)

## Decommission-Checklist

### ⬜ Schritt 0: Vor dem Anrühren — Dependencies checken

```bash
# 1. Wird das Script von cron aufgerufen?
crontab -l | grep -F <script-name>
# 2. Wird das Script von anderen Scripts importiert/sourced?
grep -rF '<script-name>' ~/50-System/bin/ ~/20-Workspace/scripts/ 2>/dev/null
```

### ⬜ Schritt 1: Original archivieren

```bash
TRASH=~/.hermes/.trash-$(date +%Y-%m-%d)
mkdir -p "$TRASH"
mv ~/50-System/bin/<script>.sh "$TRASH/<script>.sh.v<old-version>-stale"
```

**Konvention:** Datierter Trash-Ordner, Version-Tag + `-stale` Suffix auf der Datei. Pfad: `~/.hermes/.trash-YYYY-MM-DD/` — innerhalb des Hermes-Home (backup-resistent, kein XDG-Trash).

### ⬜ Schritt 2: PATH-Stub hinterlegen

Am **exakt gleichen Pfad** platzieren (damit `which <script>` und PATH-Integrationen intakt bleiben). Zwingend enthalten:
- Datum der Stilllegung
- Pfad zum archivierten Original
- Welches Skill die Logik jetzt abdeckt + konkreter Aufruf
- Pfad zum relevanten Report

### ⬜ Schritt 3: Skill absorbieren

Nicht den Code kopieren — die **Learnings** aus dem Legacy-Script aufnehmen:
- Was erkannte das Script gut? → in Recon-Scout integrieren
- Was waren die Stale-Path-False-Positives? → als Anti-Pattern
- Welche Checks haben echten Wert? → in CRIT-Verification-Step
- Was war Rauschen? → "Nicht mehr machen" notieren

### ⬜ Schritt 4: Lern-Dokumentation im Skill

`## Post-Run Learnings (YYYY-MM-DD <Task>)` Abschnitt: was gut war, was Müll, konkrete Ergänzungen, Anti-Patterns.

### ⬜ Schritt 5: Report aktualisieren

Section "D — ✅ Erledigt am YYYY-MM-DD" mit allen Aktionen.

## Stub-Template

```bash
#!/usr/bin/env bash
# <script-name> — DEPRECATED STUB (<date>)
# Das Original-Script (v<version>) wurde am <date> stillgelegt.
# Grund: <kurze Begründung>
# Archiviert: ~/.hermes/.trash-<date>/<script-name>.v<version>-stale
# Ersetzt durch: <skill-name> Skill (<skill-pfad>/SKILL.md)
# Aufruf: In Hermes-Chat sagen: "<aufruf>"
exit 0
```

## Anti-Patterns

- ❌ Neues Bash-Script statt Skill — der Punkt ist Absorption, nicht Rewrite
- ❌ Original löschen statt archivieren — keine Rückverfolgbarkeit
- ❌ Stub ohne ausreichende Info — "use skill X" allein reicht nicht
- ❌ Cron/Cross-Reference vorher nicht checken — stiller Crash der nächste Cron-Lauf