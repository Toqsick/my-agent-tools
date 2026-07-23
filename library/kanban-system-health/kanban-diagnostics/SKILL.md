---
name: kanban-diagnostics
title: "Kanban Diagnostics — Live-State, Diagnose-Baum, Status-Reports"
description: "Use when the Kanban dispatcher is misbehaving: tasks not spawning, dispatcher stuck, gateway dead, board-status unclear, or you need a live-state health check. NOT for cleanup phases (use kanban-phases), pitfall recovery (use kanban-pitfalls), or audit (use kanban-audit). Covers Live-State-Check + Diagnose-Baum (5 Hypothesen) + Status-Report-Template."
category: kanban-system-health
version: '3.0'
created: '2026-07-23'
author: Yuno (split from kanban-system-health v2.5)
lane: koenigin
agent: universal
trigger_keywords: ['kanban', 'diagnostic', 'health check', 'live-state', 'dispatcher', 'gateway', 'lock-contention', 'stale daemon', 'ready-tasks']
keywords: ['kanban', 'diagnostic', 'health', 'dispatcher', 'gateway', 'lock', 'stale', 'ready-tasks', 'board-status']
related_skills: ['kanban-phases', 'kanban-pitfalls', 'kanban-audit', 'kanban-orchestrator', 'board-policy']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from kanban-system-health 2026-07-23)'

license: MIT
---

# Kanban Diagnostics — Live-State, Diagnose-Baum, Status-Reports

Kanban Diagnostics — Live-State, Diagnose-Baum, Status-Reports

_Extracted from kanban-system-health v2.5 on 2026-07-23._

## Quick-Start: Welche Phase brauche ich?


| User-Frage | Phase | Schnell-Link |
|---|---|---|
| "Läuft Kanban?" / "Tasks hängen" | **Phase 0+1** (Cleanup + Assignment) | §1-§4 |
| "Wie dispatche ich Worker produktiv?" | **Phase 2** (Worker-Maturity) | §5 |
| "Wie nutze ich Swarm / Auto-Decomp / Goal-Mode?" | **Phase 3** (Advanced Patterns) | §6 |
| "Wie sehe ich das im Browser / Dashboard?" | **Phase 4** (GUI + Polish) | §7 |
| "Wie nutze ich das weiter? Was kommt als nächstes?" | **Phase 5+** (Evolution) | §8 |

---

## 1. Live-State-Check (in dieser Reihenfolge!)


Bei "läuft Kanban?" / "warum hängt X?" immer diese 5 Schritte — nicht aus dem Gedächtnis antworten, sondern **echte Commands fahren**.

### Schritt 1: Built-in diagnostics (VOR allen anderen Checks!)


**Gelernt 2026-07-09:** Bevor man manuelle SQL-Queries fährt oder Profile/Boards einzeln durchgeht, **erst die eingebauten Diagnose-Befehle laufen lassen.** Diese fassen die wichtigsten Erkenntnisse aus den Schritten 2-5 in einer CLI-Ausgabe zusammen:

```bash
### Schritt 2: Dispatcher-Konfiguration lesen


```bash
grep -A 15 "^kanban:" ~/.hermes/config.yaml
```

**Erwartet (Production-Ready seit 2026-07-09):**
```yaml
kanban:
  dispatch_in_gateway: true              # ← kritisch: muss true sein
  dispatch_interval_seconds: 60          # Polling-Tick
  failure_limit: 2                       # Auto-Block nach 2 Crashes
  orchestrator_profile: 'yuno'           # Phase 3+: Root-Owner nach Decompose
  default_assignee: 'yuno'               # Phase 1+: Fallback für unbekannte Profile
  auto_decompose: true
  auto_decompose_per_tick: 3
  dispatch_stale_timeout_seconds: 14400
  auto_subscribe_on_create: true         # Phase 3: Auto-Notify
  notification_sources: ['*']            # Phase 3: Cross-Profile-Notifications
```

**Befund-Tabelle:**

| Wert | Problematisch wenn |
|---|---|
| `dispatch_in_gateway: false` | ❌ Daemon läuft standalone statt embedded |
| `dispatch_interval_seconds: 0` | ❌ Kein Polling |
| `default_assignee: ''` UND ready-Tasks `(unassigned)` | ⚠️ Spawn-Skip droht |
| `failure_limit: 0` | ❌ Circuit-Breaker nie ausgelöst |
| `notification_sources: ''` (als String!) | ❌ Listen-String — funktioniert nicht |
| `auxiliary.kanban_decomposer.model: ''` | ⚠️ Decompose greift nicht |

### Schritt 3: Prozess-Landschaft


```bash
ps -ef | grep -E '(hermes_cli|gateway|kanban)' | grep -v grep
echo "---"
ss -tlnp 2>/dev/null | grep -E ':(8333|8765|11434|34647|8789)' || echo "keine hermes-ports"
```

Erwartet: Gateway-PID (z.B. `python -m hermes_cli.main gateway run`). NICHT erwartet: separater `hermes kanban daemon` Prozess — der ist deprecated seit 2026-07-02.

**⚠️ KRITISCHE KONSEQUENZ:** Der embedded Dispatcher lebt NUR solange der Gateway läuft. Wenn `systemctl --user is-active hermes-gateway.service` = `inactive (dead)`, dann ist **auch der Dispatcher tot** — ready-Tasks akkumulieren sich ungesehen. Der Cron-Ticker (separate Loop, unabhängig vom Gateway) heartbeatet weiter und täuscht "alles läuft" vor. **Verifikations-Kette:**
```bash
### Schritt 4: Stale Daemon-Files


```bash
ls -la ~/.hermes/kanban/daemon.pid ~/.hermes/kanban/daemon.log 2>/dev/null
```

**Pitfall:** Alte `daemon.pid` und `daemon.log` werden NICHT automatisch aufgeräumt. **Cleanup-Pflicht:** löschen wenn vorhanden.

### Schritt 5: Board-Status + ready-Tasks-Inventar


```bash
hermes kanban boards list
echo "---"
hermes kanban list  # für aktuelles Board
echo "---"
## 2. Diagnose-Baum (5 Hypothesen, in Reihenfolge der Wahrscheinlichkeit)


### Hypothese 1 (häufigste): `(unassigned)` blockiert Spawn


**Symptom:** `hermes kanban list` zeigt ready-Tasks mit `(unassigned)`.

**Ursache:** Dispatcher **silent skippt** Tasks deren `assignee` nicht in `hermes profile list` vorkommt. Bestätigt durch `kanban-orchestrator` v3.0.0 §Pitfalls.

**Fix:**
```bash
### Hypothese 2: Skill-Lookup-Mismatch (Per-Profile!)


**Symptom:** Worker crashed sofort beim Spawn mit `Error: Unknown skill(s): <name>`.

**Ursache:** Skills werden **per Worker-Profile** gesucht, NICHT global. `yuno-coder` hat nur 17 Skill-Categories (research/email/smart-home/software-development/...) — nicht die vollen 129 Skills wie `yuno`.

**Skill-Mapping-Tabelle (verifiziert 2026-07-09):**

| Skill / Category | Welches Profile hat es? |
|---|---|
| `software-development/*` (claude-coder, plan, critic-gate, etc.) | `yuno-coder` |
| `research/*`, `email/*`, `github/*`, `media/*` | `yuno-coder` oder `yuno` |
| `creative/*` (Anime, ASCII, etc.) | `yuno-vision` |
| `gaming/*`, `gaming/greyhack-*`, `gaming/greyhack-greyscript` | `yuno` |
| `voice-assistant-bots/*` (discord-voice) | `yuno` |
| `yuno-cleaner` (root) | `yuno` |
| alles (Full-Set 129 Skills) | `yuno`, `local-9b` (96 Skills) |
| default (leer / 0 Skills) | NIEMALS als Worker nutzen |

**Fix:** Vor jeder Assignierung prüfen:
```bash
find ~/.hermes/profiles/<ziel-profile>/skills -name "*<skill-name>*"
### Hypothese 3: Profile-Description fehlt → Auto-Decomp blind


**Symptom:** `hermes config set auxiliary.kanban_decomposer.model "..."` aktiv, aber Triage-Tasks werden nicht decomposed.

**Ursache:** Decomposer braucht Profile-Descriptions um Tasks dem richtigen Profil zuzuweisen. Ohne Description → Decompose-Failure.

**Fix:**
```bash
### Hypothese 4: Worktree ohne Git-Repo


**Symptom:** Worker crashed mit `task has workspace_kind=worktree but board <slug> has no default_workdir set. Set a board default workdir (a git repo)`.

**Fix:**
```bash
### Hypothese 5: Gateway-embedded Dispatcher nicht aktiv


**Symptom:** Gateway-PID NICHT sichtbar, `hermes kanban diagnostics` zeigt keine neuen Einträge.

**⚠️ Check-Reihenfolge (IMMER Gateway-Status zuerst!):**

```bash
## 11. Status-Report-Template (für User-Lieferung)


Wenn der User eine "läuft es?"-Frage stellt, sollte die Antwort **diese Struktur** haben (gelernt 2026-07-09, kam gut an):

1. **TL;DR** (1-2 Sätze): Was läuft, was nicht
2. **Inventur:** Skills, Profile, Boards (mit Counts)
3. **Live-Prozess-Check:** PIDs, offene Ports, Config-Settings
4. **Ready-Tasks-Inventar:** alle ready-Tasks einzeln mit "warum wartet es"-Erklärung
5. **Diagnose:** 5 Hypothesen mit Wahrscheinlichkeits-Ranking
6. **Re-Aktivierungs-Plan:** konkrete Schritte mit Verifikations-Checks
7. **Lessons Learned:** Bullet-Points für nächste Session
8. **Verwandte Doku:** Links zu ähnlichen Reports

User will **ehrliche Faktenlage**, nicht "alles super". Wenn was nicht läuft, klar sagen. Wenn was läuft, mit Beweisen (PIDs, Counts).

---
