---
name: hermes-plan-mode-recovery
description: >-
  Use when user asks for recovering a stuck Hermes Desktop plan mode, diagnosing an unresponsive Plan button, backing up and removing a malformed plan file, or restarting Desktop after plan-state corruption. NOT for improving the content of a valid plan or general Hermes crashes unrelated to plan mode. Provides a diagnostic script and guarded manual recovery path that preserves session state before deleting only the broken plan artifact.
platforms:
- linux
version: 1.0.0
author: Yuno
license: MIT
lane: worker-flash
reasoning_effort: medium
tags:
- hermes-desktop
- plan-mode
- recovery
- workaround
- bug
trigger_keywords: ['plan', 'hermes', 'desktop', 'mode', 'state']
keywords: ['plan', 'hermes', 'desktop', 'mode', 'state']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['plan', 'plan-glm', 'plan-review-and-orchestrate']
---

# Hermes Plan-Mode Recovery

Wenn der Hermes-Desktop-Chat in einen hängenden Plan-Mode fällt und Write-Tools (`mnemosyne_remember`, `mnemosyne_sleep`, `write_file`, `patch`, `execute_code` mit Schreibops) den Fehler "Plan mode is active — write operations are blocked" werfen, dann hilft dieser Skill.

## Symptom

```
[hermes] error: Plan mode is active — tool 'mnemosyne_remember' is not on the read-only allowlist.
[hermes] Run `/plan approve` (or `/plan off`) first; the active plan file is
         '/home/bratan/.hermes/plans/<plan-id>.md'.
```

Slash-Command `/plan approve` oder `/plan off` im Chat löst es **NICHT**, wenn der Plan-File zu klein ist (siehe Ursache).

## Ursache (Bug, closed-source)

Hermes-Desktop-Electron konvertiert Initial-Chat-Prompts in Plan-Files unter `~/.hermes/plans/`. Bei **Mini-Prompts (< 1 KB Output)** entsteht ein Mini-Plan-File mit nur der Goal-Zeile, **ohne** das v2-Format (YAML-Frontmatter + ```tasks-Fence). Der `/plan approve`-Handler erwartet aber das v2-Format und verwirft den Mini-Plan stillschweigend. Der Write-Lock bleibt aktiv, weil der Plan-File existiert.

**Quellen-Code:** closed-source, gepackt in `apps/desktop/release/linux-unpacked/resources/app.asar` (8.7 MB). Kein direkter Source-Patch möglich ohne Electron-Rebuild.

## Schnellster Fix

```bash
# Trockenlauf zuerst (zeigt Diagnose)
~/50-System/bin/hermes-plan-unlock.sh --dry-run

# Echte Anwendung (killt Hermes-Desktop + löscht Plan-File + startet neu)
~/50-System/bin/hermes-plan-unlock.sh --force
```

**WICHTIG:** Der Restart killt die aktive Desktop-Session. Wenn du im Chat Recovery brauchst, führe das Skript aus einem **externen Terminal** aus (nicht aus dem Chat, der gerade hängt).

## Manuelle Recovery (5 Schritte)

Falls das Skript nicht verfügbar ist:

```bash
# 1. Plan-File diagnostizieren
ls -la ~/.hermes/plans/ | tail -5
# Suche den NEUESTEN Plan-File (meist < 1 KB wenn's der Bug ist)

# 2. Prüfe ob es ein v2-Format-Plan ist
head -3 ~/.hermes/plans/<neuester>.md | grep '^---'   # YAML-Frontmatter
grep -c '^```tasks' ~/.hermes/plans/<neuester>.md     # tasks-Fence

# 3. Backup anlegen
mkdir -p ~/.hermes/plans/.trash-$(date +%Y%m%d-%H%M%S)
cp ~/.hermes/plans/<neuester>.md ~/.hermes/plans/.trash-<timestamp>/

# 4. Hermes-Desktop beenden (vorsichtig, speichert aktive Session)
pkill -TERM -f 'apps/desktop/release/linux-unpacked/Hermes'
sleep 3
pkill -KILL -f 'apps/desktop/release/linux-unpacked/Hermes' 2>/dev/null

# 5. Plan-File löschen + Desktop neu starten
rm -f ~/.hermes/plans/<neuester>.md
nohup hermes desktop >/dev/null 2>&1 &
disown
```

## Diagnose-Checkliste

| Frage | Was es bedeutet |
|---|---|
| Existiert ein Plan-File in `~/.hermes/plans/`? | Ja → Write-Lock wahrscheinlich aktiv |
| Ist der Plan-File < 1 KB? | Ja → Hängender Mini-Plan, Workaround anwenden |
| Hat der Plan-File YAML-Frontmatter (`---`)? | Nein → Wahrscheinlich Mini-Plan, Workaround anwenden |
| Hat der Plan-File ```tasks-Fence? | Nein → Wahrscheinlich Mini-Plan, Workaround anwenden |
| Läuft Hermes-Desktop-Prozess? | `pgrep -f Hermes` zeigt PID oder leer |
| Letzte Fehler im Log? | `grep 'Plan mode is active' ~/.hermes/logs/desktop.log` |

## Vorbeugung

- **Große/komplexe Tasks:** Schreibe den Plan zuerst als v2-Plan-File (YAML-Frontmatter + ```tasks-Fence), dann `/plan approve`. Das verhindert den Mini-Plan-Bug.
- **Mini-Prompts:** Tipp direkt eine klare Aufgabe ohne "Plan" Trigger-Wörter ("plan", "kickoff", "todo"), z. B. statt "Plan: räume die Datenbank auf" besser "Archiviere alle Sessions älter als 2 Wochen".
- **Prüfe nach Prompt:** Wenn du eine Antwort mit "Plan kickoff" oder "Plan-Files" siehst, schau in `~/.hermes/plans/` nach ob ein File angelegt wurde. Wenn < 1 KB: direkt selbst löschen.

## Pitfalls

- **Restart killt aktive Session:** Wer das Recovery-Skript aus dem hängenden Chat heraus ausführt, killt sich selbst. Immer in externem Terminal.
- **Offene Tabs/Edits:** Electron speichert Session-State separat, Restart verliert keine History, aber offene Tabs die nicht committed sind.
- **Gateway läuft weiter:** `hermes-gateway.service` (Port 8642) ist ein separater Prozess, wird durch Desktop-Kill nicht beeinflusst. Aktive CLI-Sessions überleben.
- **Race mit anderen Usern:** Wenn mehrere User auf der Maschine arbeiten, ist SIGTERM auf `Hermes` zu grob. Skript fragt VOR dem Kill nach (außer `--force`).

## Upstream-Issue

Code ist closed-source. Mögliche Patches upstream:
1. Plan-Parser sollte Mini-Files ohne v2-Format still ablehnen statt Lock aktivieren
2. `/plan approve` Slash-Command sollte auch Mini-Files als "trivial" akzeptieren
3. Initial-Prompt-Erkennung sollte nicht jeden Prompt als Plan-Trigger interpretieren

Tracker: https://hermes-agent.nousresearch.com/docs → "Plan mode" Issue-Tag
