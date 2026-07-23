---

name: greyhack-game-observer
description: |
  Use when you are passively observing and documenting a GreyHack gameplay session — watching chat, capturing screenshots, logging in-game events to a transcript without taking autonomous actions.
  NOT for active GreyHack play (use greyhack-smart-macro), mission orchestration (use greyhack-mission-orchestrator), or non-GreyHack games.
  Passive observer role for GreyHack: monitors screenshots, in-game chat, and netmaps, writes structured session logs for later review.
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
    - greyhack
    - observer
    - ocr
    - screenshot
    - automation
    related_skills:
    - computer-use
    - greyhack-smart-macro
    - greyhack-mission-orchestrator
trigger_keywords: ['greyhack', 'session', 'chat', 'screenshots', 'game']
keywords: ['greyhack', 'session', 'chat', 'screenshots', 'game']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack-hermes-api', 'greyhack-smart-macro', 'greyhack-mission-orchestrator']
---


# GreyHack Game Observer

## Overview
Der **GreyHack Game Observer** ist das passive Beobachtungs-Modul unserer Computer-Use-Pipeline für Grey Hack. Er erfasst im Hintergrund (im Vordergrund spielst du!) Screenshots des Spielfensters und extrahiert mit Hilfe von OCR (Tesseract) den angezeigten Text. Diese Snapshots werden als Markdown-Dateien in deinem Obsidian Vault abgelegt — so entsteht eine lückenlose, durchsuchbare Mitschrift deiner Game-Sessions.

## When to Use
- **Trigger**: Du willst eine GreyHack-Session dokumentieren, ohne aktiv zu schreiben.
- **Trigger**: Du willst im Nachhinein nachvollziehen können, welche Befehle du im Spiel eingegeben hast.
- **Trigger**: Der Orchestrator-Skill (`greyhack-mission-orchestrator`) braucht eine Datenbasis für State-Recognition.
- **Trigger**: Du willst Basti-Patterns und Erfolgsrezepte aus deinen Spielstunden destillieren.
- **Nicht verwenden für**: Aktive Steuerung des Spiels (nutze `greyhack-smart-macro`) oder autonome Missionen (nutze `greyhack-mission-orchestrator`).

## How It Works

Das Observer-Modul arbeitet nach dem **3-Schichten-Pattern**:

```
┌─────────────────────────────────────────────────────────┐
│  Schicht 1: CAPTURE                                      │
│  - cua-driver screenshot vom Grey-Hack-Fenster           │
│  - mode="som" mit AX-Tree-Index (Linux: AT-SPI)          │
│  - Keine Fenster-Fokus-Klau (background_only=True)       │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Schicht 2: OCR-EXTRACTION                               │
│  - Tesseract OCR auf das Screenshot                     │
│  - Monospace-Font von Grey Hack ist OCR-freundlich       │
│  - Strukturiert in: Header / Body / Footer / Status      │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Schicht 3: VAULT-PERSISTENZ                            │
│  - Markdown-Datei in 99 Capture/ Ordner                 │
│  - Dataview-kompatibel (Tags: capture, greyhack)         │
│  - Wiki-Links zu Missionen/Orten/NPCs                   │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### 1. Voraussetzungen prüfen

```bash
# cua-driver muss installiert sein
hermes computer-use install

# Tesseract OCR muss verfügbar sein
which tesseract  # Sollte /usr/bin/tesseract zurückgeben

# Falls nicht installiert:
sudo apt install tesseract-ocr tesseract-ocr-deu

# Grey Hack-Fenster identifizieren
wmctrl -l | grep -i "grey\|hack"  # X11
# oder für Wayland:
gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval 'global.get_window_actors().map(a => a.meta_window.get_title()).filter(t => t.toLowerCase().includes("grey"))'
```

### 2. Observer starten

```python
from hermes_tools import computer_use
import subprocess
import datetime
from pathlib import Path

VAULT_CAPTURE_DIR = Path("/home/bratan/Dokumente/Obsidian Vault/99 Capture")
VAULT_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

def capture_session_tick(session_id: str = None) -> str:
    """Einen Observer-Tick ausführen: Screenshot + OCR + Markdown speichern."""
    session_id = session_id or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Schicht 1: Screenshot via cua-driver
    screenshot = computer_use(
        action="capture",
        mode="som",  # Wir wollen AX-Index für spätere Macro-Aktionen
        app="steam",  # Grey Hack läuft über Steam (Native Linux oder Proton)
        background_only=True  # KEIN Fenster-Fokus-Klau!
    )
    
    # Schicht 2: OCR-Extraktion
    screenshot_path = f"/tmp/greyhack_capture_{session_id}.png"
    with open(screenshot_path, "wb") as f:
        f.write(screenshot)
    
    ocr_result = subprocess.run(
        ["tesseract", screenshot_path, "-", "-l", "eng", "--psm", "6"],
        capture_output=True, text=True, timeout=10
    )
    ocr_text = ocr_result.stdout.strip()
    
    # Schicht 3: Vault-Persistenz
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    capture_file = VAULT_CAPTURE_DIR / f"{timestamp[:10]}_GreyHack_{session_id}.md"
    
    md_content = f"""---
tags: [capture, greyhack, computer-use]
session-id: {session_id}
captured-at: {timestamp}
stimmung: gameplay-dokumentation
---

# 🎮 GreyHack Capture — {timestamp}

> **Snapshot-Modus:** Observer (passive Mitschrift)
> **Spiel-Fenster:** steam / Grey Hack
> **OCR-Engine:** Tesseract (eng, psm 6)

## 📺 Screenshot

![GreyHack Snapshot]({screenshot_path})

## 📝 OCR-Extrahierter Text

```
{ocr_text}
```

## 🧠 Kontextuelle Notizen

<!-- Yuno / Orchestrator: Hier können automatische Notizen eingefügt werden -->
- **Erkannte UI-Elemente**: Siehe Screenshot
- **Verbindet zu**: [[GreyHack - Werkzeugkasten & Patterns]], [[Queen-Bee-Lab - GreyHack-Tests]]
- **Nächster Tick**: In 5 Sekunden (default)

## Verbindet zu

- [[MOC - Gaming-Performance]] — Gaming-Hub
- [[System - Skill-Tool-ComputerUse-Strategie]] — Strategie-Dokument
- [[greyhack-smart-macro]] — Nächste Stufe: Aktionen
"""
    
    with open(capture_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return str(capture_file)

# Endlos-Loop mit manuellem Kill-Switch (Ctrl+C)
if __name__ == "__main__":
    import time
    import sys
    
    interval = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0  # Sekunden
    print(f"🔍 Observer startet (Intervall: {interval}s, Ctrl+C zum Beenden)")
    
    try:
        while True:
            tick_result = capture_session_tick()
            print(f"  ✓ Tick: {tick_result}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n🛑 Observer gestoppt.")
```

### 3. Im Hintergrund starten (mit Telegram-Notification)

```bash
# Observer mit Logging im Hintergrund starten
nohup python3 /home/bratan/.hermes/skills/computer-use/greyhack-game-observer/scripts/greyhack_capture.py 5 \
  > /tmp/greyhack_observer.log 2>&1 &

# Bei Beendigung: Telegram-Alert (via cron-trap)
echo "GreyHack Observer gestoppt um $(date)" | \
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_HOME_CHANNEL}" \
  -d "text=$(cat -)"
```

## Common Pitfalls
1. **Fenster-Fokus-Klau**: Niemals `raise_window=True` setzen! Das würde deinen Editor-Focus klauen und dich beim Spielen stören.
2. **OCR auf Wayland**: Tesseract selbst ist Tool-agnostic, aber die Screenshot-Quelle muss Wayland-kompatibel sein. Auf GNOME/Wayland: `gnome-screenshot` oder `grim` verwenden statt X11-`import`.
3. **Zu hohe Frequenz**: 1× pro Sekunde ist für die meisten Use-Cases overkill und kostet CPU + Storage. Empfehlung: 5-10 Sekunden Intervall.
4. **Steam vs. Grey-Hack-Fenster**: Wenn Grey Hack im Big-Picture-Modus läuft, ist das sichtbare Fenster "steam" (mit dem Overlay). Direkt-Fenster-Targeting kann dann fehlschlagen — teste mit `wmctrl -l` welches Fenster aktiv ist.
5. **Vault-Speicher-Explosion**: 1 Tick/5s = 12 Dateien/Minute = 17.280 Dateien/Tag! Empfehlung: Daily-Note-Format (eine Datei pro Tag, viele Snapshots darin) oder Auto-Archivierung älterer Captures.
6. **❌ KEIN `from hermes_tools import computer_use`** — Dieser Import funktioniert NICHT im Hermes-Subprocess-Kontext (TUI/CLI/execute_code). `hermes_tools` enthält NICHT das `computer_use`-Symbol. Der funktionierende Pfad ist **cua-driver als Subprocess mit DISPLAY+XAUTHORITY-Env-Injektion** auf Linux/Wayland. Vollständiges Rezept siehe `references/linux-wayland-screenshot-recipe.md`. Symptom eines falschen Imports: `ImportError: cannot import name 'computer_use' from 'hermes_tools'`.

## Verification Checklist
- [ ] `cua-driver` ist installiert (`hermes computer-use install`)
- [ ] Tesseract OCR ist verfügbar (`which tesseract`)
- [ ] Grey Hack läuft in einem erkennbaren Fenster
- [ ] Observer-Tick erzeugt valide Markdown-Datei in `99 Capture/`
- [ ] Screenshot ist im Markdown referenziert und existiert physisch
- [ ] Kein Fenster-Fokus-Klau (Editor behält Focus, wenn Observer läuft)

## Verbindet zu
- [[MOC - Gaming-Performance]] — Gaming-Hub
- [[Queen-Bee-Lab - GreyHack-Tests]] — Testlabor für unsere Queen-Bee-Architektur
- [[greyhack-smart-macro]] — Nächste Stufe: Vom Beobachten zum Agieren
- [[System - Skill-Tool-ComputerUse-Strategie]] — Strategischer Kontext
- [[Yuno - Mobile MaxClaw-Setup]] — GreyHack-Inventar-Referenz

## Support-Dateien

- `references/linux-wayland-screenshot-recipe.md` — **WICHTIG**: Vollständiges Rezept für den Linux-Wayland-Pfad (Xwayland-Auth-File finden, DISPLAY+XAUTHORITY in Subprocess-Env injizieren, `cua-driver call get_window_state` JSON-Parsing für base64-Screenshots). Lies das VOR dem ersten `capture_screenshot`-Aufruf auf einem Wayland-Desktop.
- `scripts/greyhack_capture.py` — Laufende Implementierung. Enthält 3-Tier-Fallback: `cua-driver get_window_state` → `scrot` mit Display-Env → Exception mit Install-Hinweis.
