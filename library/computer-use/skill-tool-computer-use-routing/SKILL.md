---
name: skill-tool-computer-use-routing
description: |
  Use when choosing whether a task should be handled by a reusable skill, a direct structured tool call, or GUI computer-use based on available interfaces and risk.
  NOT for performing the selected task itself, bypassing a purpose-built API, or using GUI automation when a deterministic tool is available.
  Defines a routing decision framework for selecting the safest, most reliable action surface before execution.
version: 1.0.0
author: Yuno (Basti)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - system
    - strategy
    - computer-use
    - tools
    - workflow
    related_skills:
    - computer-use
    - hermes-agent-skill-authoring
trigger_keywords: ['task', 'tool', 'available', 'choosing', 'whether']
keywords: ['task', 'tool', 'available', 'choosing', 'whether']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['yuno-team-routing', 'hybrid-swarm-evaluation', 'mlops-suite']
---


# System-Strategie: Skills, Tools & Computer Use (Das Aktions-Trias)

## Overview
Dieses Dokument definiert die **Schnittstellen- und Workflow-Strategie** des KI-Betriebssystems. Es regelt, wie das Zusammenspiel zwischen **Skills (prozedurales Wissen)**, **Tools (programmatische Hebel)** und **Computer Use (GUI-Interaktion im Hintergrund)** abläuft. Das Ziel ist es, Aufgaben mit minimalem Token-Verbrauch, maximaler Geschwindigkeit und unfehlbarer Stabilität auszuführen.

```
                  ┌────────────────────────────────────────┐
                  │          1. SKILL (Prozedur)           │
                  │   - "Wie wird die Aufgabe gelöst?"     │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          2. TOOL (Hebel)               │
                  │   - Direct-Writes, Terminal-APIs, etc. │
                  └───────────────────┬────────────────────┘
                                      │  [Falls keine CLI/API]
                                      ▼
                  ┌────────────────────────────────────────┐
                  │     3. COMPUTER USE (Auge & Hand)      │
                  │   - Native GUI-Steuerung im Background │
                  └────────────────────────────────────────┘
```

---

## When to Use (Die 3 Säulen)

| Säule | Zweck | Repräsentant | Latenz | Token-Kosten |
|---|---|---|---|---|
| **Skills (Atome)** | Prozedurales Gedächtnis (Wie machen wir etwas?) | `obsidian-canvas-factory` | N/A (statisch) | Minimal (In-Context) |
| **Tools (Moleküle)** | Direkte, programmgesteuerte Aktionen | `write_file`, `terminal` | < 1 Sekunde | Gering |
| **Computer Use (Organismus)** | Physische Steuerung von Desktop-Apps | `cua-driver` (Click, Type) | 5 - 15 Sekunden | Extrem hoch |

---

## Das Stufen-Modell der Effizienz (Entscheidungs-Hierarchie)

Um die Workstation-Ressourcen zu schonen und Stabilität zu garantieren, gilt die **eiserne Regel**: *Arbeite dich immer von Stufe 1 nach Stufe 4 hinab. Nutze die nächste Stufe nur, wenn die vorherige unmöglich ist.*

### 🟢 Stufe 1: Nativer Dateizugriff / API (Die stabilste Stufe)
- **Methode**: Direct-Reads & Writes, strukturierte JSON-Patches.
- **Beispiel**: Erstellen eines Obsidian-Canvas via Python-Schreibbefehl (`write_file`).
- **Latenz**: < 50ms | **Stabilität**: 100 %

### 🟡 Stufe 2: Terminal / Shell CLI (Die universelle Stufe)
- **Methode**: Ausführen von Shell-Befehlen, package-manager CLI, Git, systemctl.
- **Beispiel**: Stoppen eines Daemons via `systemctl --user stop hermes-gateway`.
- **Latenz**: < 500ms | **Stabilität**: 95 %

### 🟠 Stufe 3: Headless Browser / Extraktion (Die Web-Stufe)
- **Methode**: Extrahieren sauberer Markdown-Daten aus Webseiten oder PDFs.
- **Beispiel**: Auslesen von Paket-Dokus oder GitHub-Releases via `web_extract`.
- **Latenz**: 2 - 5 Sekunden | **Stabilität**: 90 %

### 🔴 Stufe 4: GUI / Computer Use (Die physische Hintergrund-Stufe)
- **Methode**: Reales Anklicken, Scrollen, Tippen und Ziehen in nativen GUI-Fenstern im Hintergrund via `cua-driver`.
- **Beispiel**: Steuern des nativen Musik-Streaming-Clients, Steuern in-game in Grey Hack, wenn keine API greift.
- **Latenz**: 5 - 15 Sekunden | **Stabilität**: 75 - 80 % (Verlangt kontinuierliche Vision-Verifikation)

---

## Workflow-Strategie: Szenario-Vergleiche

### Szenario A: Erstellung eines Netzwerkgraphen in Obsidian
* **Der falsche Weg (Stufe 4)**: 
  Öffne das Obsidian-Fenster, klicke auf "Neuer Canvas", klicke und ziehe Elemente auf die Arbeitsfläche und tippe Text ein.
  * *Ergebnis*: Dauert 3 Minuten, verbraucht $4.50 an GPT/Sonnet-Tokens, scheitert bei jedem zweiten Klick-Versatz.
* **Der richtige Weg (Stufe 1 via Skill)**:
  Lade den Skill `obsidian-canvas-factory`. Generiere das Canvas-JSON mit deterministischen Pixel-Koordinaten und Hex-IDs im Speicher. Schreibe die Datei direkt mit `write_file` nach `08 Anhaenge/Excalidraw/Graph.canvas`.
  * *Ergebnis*: Dauert 1,5 Sekunden, 100% fehlerfrei, kostet Bruchteile eines Cents.

### Szenario B: Lokale Musik abspielen oder System-Widgets steuern
* **Der einzige Weg (Stufe 4)**:
  Da das lokale Musikprogramm oder System-Widget keine offene API- oder CLI-Schnittstelle besitzt, muss `computer_use` herangezogen werden.
  * *Ablauf*:
    1. **Capture**: Screenshot des Dashboards machen (`computer_use(action="capture", mode="som")`).
    2. **Fokus**: Finde die Element-ID des Play-Knopfes (z.B. `#12`).
    3. **Aktion**: Klicke den Knopf (`computer_use(action="click", element=12, capture_after=True)`).
    4. **Verify**: Kontrolliere im Folge-Screenshot, ob sich das Icon geändert hat.

---

## Common Pitfalls

1. **GUI-Overkill**: Der Versuch, Probleme grafisch zu lösen, die sich weitaus stabiler auf Terminal- oder Dateiebene lösen lassen (z.B. Editieren von Konfigurations-JSONs in der GUI statt via API).
2. **Ignorieren der Vision-Verifikation**: Ausführen mehrerer Klicks hintereinander auf Stufe 4, ohne zwischendurch einen Kontroll-Screenshot zu machen (`capture_after=True`). Wenn sich ein Fenster verschiebt, klickt der Agent ins Leere.
3. **Mangelnde Fehlerbehandlung (Stufe 4)**: Blockierte Klicks durch Popups oder Dialoge nicht über die ESC-Taste (`computer_use(action="key", keys="escape")`) abzufangen.
4. **Linux Wayland: cua-driver subprocess erbt kein Display** — `cua-driver doctor` meldet `[warn] display server: neither DISPLAY nor WAYLAND_DISPLAY set`. Auf einem Wayland-Desktop (z.B. Zorin/GNOME mit Xwayland) muss man DISPLAY + XAUTHORITY **explizit** in den Subprocess-Env injizieren, sonst sieht cua-driver keine Fenster und `list_windows` gibt `{"windows": []}` zurück. Rezept in `references/linux-xwayland-display.md`.

## Verification Checklist
- [ ] Stufen-Modell wurde vor der Werkzeugwahl konsultiert
- [ ] Für Dateioperationen wurden native Tools (`patch`, `write_file`) statt GUI-Editoren verwendet
- [ ] Computer-Use-Aktionen nutzen immer die Element-Index-Methode (`element=N`) statt roher Pixel-Koordinaten
- [ ] Jede GUI-Interaktion wird sofort mit `capture_after=True` auf Erfolg geprüft
- [ ] **Vor dem ersten Subprocess-cua-driver-Call auf Linux: `hermes computer-use doctor` ausgeführt und alle Display-/X11-/AT-SPI-Checks grün** (siehe `references/linux-xwayland-display.md` für den Wayland-spezifischen Xwayland-Auth-File-Trick)

## Support-Dateien

- `references/linux-xwayland-display.md` — Linux Wayland-Desktop + cua-driver: Rezept zum Finden des Xwayland-Auth-Files und zum Injizieren von DISPLAY+XAUTHORITY in den Subprocess-Env, damit `list_windows` und `get_window_state` funktionieren.

## Verbindet zu
- [[Yuno - Mobile Persona]] — Mobile Interaktions-Modi
- [[MOC - KI-Architektur]] — Die systemische KI-Struktur
- [[Working Agreement - Yuno Basti]] — Erlaubte Eingriffs-Korridore
