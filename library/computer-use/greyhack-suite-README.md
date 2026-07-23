---
name: greyhack-suite-readme
description: Read this first when working with the GreyHack Computer Use Suite.
---

# 🎮 GreyHack Computer-Use-Suite

## Was ist das?

Dieses Verzeichnis enthält drei zusammenarbeitende Skills für autonomes GreyHack-Gameplay:

```
greyhack-suite/
├── greyhack-game-observer/        # Beobachten (Screenshot + OCR)
│   ├── SKILL.md
│   └── scripts/greyhack_capture.py
├── greyhack-smart-macro/          # Agieren (Type, Click)
│   ├── SKILL.md
│   └── scripts/greyhack_macro.py
└── greyhack-mission-orchestrator/ # Orchestrieren (State-Machine + Kill-Switch)
    ├── SKILL.md
    └── scripts/orchestrator.py + mission_state.py
```

## Quick-Start (3 Schritte)

### 1. cua-driver installieren (einmalig)

```bash
hermes computer-use install
```

### 2. Tesseract OCR installieren (einmalig)

```bash
sudo apt install tesseract-ocr
```

### 3. Erste Mission testen

```bash
# Dry-Run: nur Parsing
python3 greyhack-mission-orchestrator/scripts/orchestrator.py \
  "/home/bratan/Dokumente/Obsidian Vault/03 Projekte/Queen-Bee-Lab/Missions/Mission-Reraldi-IP-154.md" \
  --dry-run

# Live-Run (VORSICHT! Vorher Backup!)
python3 greyhack-mission-orchestrator/scripts/orchestrator.py \
  "/home/bratan/Dokumente/Obsidian Vault/03 Projekte/Queen-Bee-Lab/Missions/Mission-Reraldi-IP-154.md"
```

## Voraussetzungen

- ✅ cua-driver installiert
- ✅ Tesseract OCR installiert
- ✅ Grey Hack läuft in erkennbarem Fenster (Steam oder direkt)
- ✅ Obsidian Vault mit Queen-Bee-Lab Mission-Dateien
- ✅ Telegram-Bot-Token in `~/.hermes/.env` (für Kill-Switch-Alerts)

## Sicherheits-Checkliste

- [ ] Mission wurde im Dry-Run-Modus getestet
- [ ] Vault-Backup wurde erstellt
- [ ] Kill-Switch ist funktionsfähig (Test mit Dummy-Permission-Dialog)
- [ ] Telegram-Verbindung funktioniert
- [ ] Grey Hack läuft NICHT im Big-Picture-Modus (Steam-Overlay-Problem)

## Hilfe

Siehe individuelle Skill-Beschreibungen:
- `greyhack-game-observer/SKILL.md`
- `greyhack-smart-macro/SKILL.md`
- `greyhack-mission-orchestrator/SKILL.md`
