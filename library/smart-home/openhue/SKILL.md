---
name: openhue
description: "Use when user asks to control Philips Hue lights, rooms, brightness, colors, scenes, or presets through the OpenHue CLI, or needs its installation and command syntax. NOT for general smart-home automation or non-Hue brands. Provides terminal workflows for listing resources, changing light state, controlling rooms, and applying quick presets."
version: 1.0.0
author: community
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Smart-Home
    - Hue
    - Lights
    - IoT
    - Automation
    homepage: https://www.openhue.io/cli
prerequisites:
  commands:
  - openhue
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['openhue', 'rooms', 'presets', 'and', 'control']
keywords: ['rooms', 'presets', 'user', 'asks', 'control']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# OpenHue CLI

Control Philips Hue lights and scenes via a Hue Bridge from the terminal.

## Prerequisites

```bash

set -euo pipefail
# Linux (pre-built binary)
curl -sL https://github.com/openhue/openhue-cli/releases/latest/download/openhue-linux-amd64 -o ~/.local/bin/openhue && chmod +x ~/.local/bin/openhue

# macOS
brew install openhue/cli/openhue-cli
```

First run requires pressing the button on your Hue Bridge to pair. The bridge must be on the same local network.

## When to Use

- "Turn on/off the lights"
- "Dim the living room lights"
- "Set a scene" or "movie mode"
- Controlling specific Hue rooms, zones, or individual bulbs
- Adjusting brightness, color, or color temperature

## Common Commands

### List Resources

```bash

set -euo pipefail
openhue get light       # List all lights
openhue get room        # List all rooms
openhue get scene       # List all scenes
```

### Control Lights

```bash

set -euo pipefail
# Turn on/off
openhue set light "Bedroom Lamp" --on
openhue set light "Bedroom Lamp" --off

# Brightness (0-100)
openhue set light "Bedroom Lamp" --on --brightness 50

# Color temperature (warm to cool: 153-500 mirek)
openhue set light "Bedroom Lamp" --on --temperature 300

# Color (by name or hex)
openhue set light "Bedroom Lamp" --on --color red
openhue set light "Bedroom Lamp" --on --rgb "#FF5500"
```

### Control Rooms

```bash

set -euo pipefail
# Turn off entire room
openhue set room "Bedroom" --off

# Set room brightness
openhue set room "Bedroom" --on --brightness 30
```

### Scenes

```bash

set -euo pipefail
openhue set scene "Relax" --room "Bedroom"
openhue set scene "Concentrate" --room "Office"
```

## Quick Presets

```bash

set -euo pipefail
# Bedtime (dim warm)
openhue set room "Bedroom" --on --brightness 20 --temperature 450

# Work mode (bright cool)
openhue set room "Office" --on --brightness 100 --temperature 250

# Movie mode (dim)
openhue set room "Living Room" --on --brightness 10

# Everything off
openhue set room "Bedroom" --off
openhue set room "Office" --off
openhue set room "Living Room" --off
```

## Notes

- Bridge must be on the same local network as the machine running Hermes
- First run requires physically pressing the button on the Hue Bridge to authorize
- Colors only work on color-capable bulbs (not white-only models)
- Light and room names are case-sensitive — use `openhue get light` to check exact names
- Works great with cron jobs for scheduled lighting (e.g. dim at bedtime, bright at wake)
