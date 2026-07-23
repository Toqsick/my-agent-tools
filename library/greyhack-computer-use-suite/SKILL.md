---
name: greyhack-computer-use-suite
description: |
  Use when orchestrating active GreyHack gameplay through Computer Use, defining a mission, assigning observer and macro roles, or enforcing pre-run safety gates.
  NOT for real-world systems, plain GreyScript authoring without GUI actions, or unsupervised gameplay that violates the suite’s hard safety rules.
  Defines the Queen-Bee architecture that coordinates mission orchestration, visual observation, and guarded smart-macro execution in GreyHack.
version: 1.1.0
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
    - computer-use
    - queen-bee
    - orchestrator
    - autonomous-gaming
    related_skills:
    - computer-use
    - subagent-patterns
    - working-agreement
trigger_keywords: ['greyhack', 'gameplay', 'mission', 'macro', 'safety']
keywords: ['greyhack', 'gameplay', 'mission', 'macro', 'safety']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack-mission-orchestrator', 'greyhack-smart-macro', 'greyhack-game-observer']
---


# GreyHack Computer-Use Suite — Queen-Bee Architecture

The 3-skill pattern for autonomous GreyHack gameplay using the `cua-driver` Computer Use stack. Built 2026-07-06 as Basti's flagship test lab for the Queen-Bee metaphor applied to gaming.

## When to Use

- **Trigger**: You want to automate a repetitive GreyHack mission (Portscan → Exploit → Data extract)
- **Trigger**: You want a passive Mitschnitt of your GreyHack sessions for later review
- **Trigger**: You want to validate Multi-Agent patterns in a game environment where failure is recoverable
- **Trigger**: You want to turn your Obsidian Vault into the command center for autonomous gameplay

## The 3-Skill Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         OBSIDIAN VAULT (Mission-Definitionen)               │
│  03 Projekte/Queen-Bee-Lab/Missions/                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ read
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: greyhack-mission-orchestrator (Autonom)          │
│  - Liest Mission-MD aus dem Vault                           │
│  - State-Machine für Steps                                  │
│  - Kill-Switch bei Permission-Dialogen                       │
│  - Telegram-Alerts (Working Agreement §7)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ call
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: greyhack-smart-macro (Aktiv)                     │
│  - type_greyscript(file) → tippt .src ins Spiel            │
│  - click_with_retry(element, expected_text)                 │
│  - automated_login(user, pass)                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ computer_use
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: greyhack-game-observer (Passiv)                   │
│  - capture_session_tick() → Screenshot + Tesseract OCR     │
│  - Schreibt Markdown nach 99 Capture/                      │
│  - background_only=True (kein Editor-Focus-Klau)            │
└──────────────────────────┬──────────────────────────────────┘
                           │ cua-driver
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         GREY HACK SPIEL-FENSTER (steam)                     │
└─────────────────────────────────────────────────────────────┘
```

## The 6 Hard Safety Rules

These are NON-NEGOTIABLE for the Orchestrator:

| # | Rule | Implementation |
|---|---|---|
| 1 | **Never click permission dialogs** | `check_kill_switch()` runs BEFORE every action; matches on &quot;permission&quot;, &quot;allow&quot;, &quot;deny&quot;, &quot;sudo&quot;, &quot;password prompt&quot; |
| 2 | **Telegram-alert on kill-switch trigger** | `send_telegram_alert()` uses `~/.hermes/.env` tokens; if `.env` missing → log locally and continue (fail-safe) |
| 3 | **Max 3 consecutive unverifiable → STOP** | Anti-Cheat trigger: after 3 failed Klicks (`effect: unverifiable`) kill mission immediately. More tries WILL crash GreyHack (verified 2026-07-06) |
| 4 | **Window-ID > PID for capture** | Grey Hack spawns 2 processes (Steam Mirror). Use `xdotool search --name &quot;Grey&quot;` to find Window-IDs, then `get_window_state {&quot;window_id&quot;: &lt;id&gt;}` — never PID-only. PID 4563 can point to wrong process |
| 5 | **State persisted after each step** | `Mission-State - Live-Status.md` rewritten in Vault after every action |
| 6 | **Wayland Env-Vars mandatory** | Every subprocess call needs `DISPLAY=:1` + `XAUTHORITY=/run/user/1000/.mutter-Xwaylandauth.*` (auth file changes per login — verify with `ls /run/user/$(id -u)/.mutter-Xwaylandauth*`) |

## Mission Definition Format

Drop a `.md` file in `03 Projekte/Queen-Bee-Lab/Missions/`:

```markdown
---
type: mission
target: <User/IP>
priority: P0
status: ready-to-run
---

# Mission: <Name>

## Steps
1. <action 1>
2. <action 2>
...
```

Then run:
```bash
python3 ~/.hermes/skills/computer-use/greyhack-mission-orchestrator/scripts/orchestrator.py \
  "/home/bratan/Dokumente/Obsidian Vault/03 Projekte/Queen-Bee-Lab/Missions/<file>.md" \
  --dry-run  # always dry-run first
```

## Common Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | cua-driver not installed | `hermes computer-use install` — system-level requirement, not a skill fix |
| 2 | Tesseract not installed | `sudo apt install tesseract-ocr` — OCR is the observer's eyes |
| 3 | Steam Big-Picture mode blocks overlay | Run GreyHack in windowed mode; close Steam overlay with Shift+Tab |
| 4 | Hardcoded element indices | Always `capture` before `click` — indices are only valid until next capture |
| 5 | `raise_window=True` steals editor focus | Never set this flag; use `background_only=True` everywhere |
| 6 | Race conditions between steps | Always `time.sleep(2.0)` between mission steps + `capture_after=True` |
| 7 | Reraldi@adahidomev.net OCR misread | Pre-build known-name correction map; Tesseract reads &quot;l&quot; as &quot;1&quot; often |
| 8 | **Anti-Cheat blocks XSendEvent input** | `cua-driver click/type_text` returns `effect: unverifiable`. Grey Hack uses Canvas rendering without AT-SPI + server-side anti-bot detection. Fix: `delivery_mode: foreground` (steals focus) or User-as-Input-Channel (user clicks, agent reads via OCR) |
| 9 | **Wayland + Xwayland: missing Env-Vars** | `DISPLAY=:1` + `XAUTHORITY=...` must be set in EVERY subprocess call. Auth file changes per login — verify with `ls /run/user/$(id -u)/.mutter-Xwaylandauth*` |
| 10 | **Window-ID-stability vs PID** | Grey Hack spawns 2 Windows (Steam Mirror). `xdotool search --name &quot;Grey&quot;` finds both. Use Window-ID not PID for `get_window_state` |
| 11 | **Tesseract PSM-Modus-Mismatch** | PSM 3 vs PSM 6 gives different results for same image. For critical values (IPs, ports, version numbers): run PSM 3,4,6 in parallel and take majority vote |
| 12 | **Anti-Cheat-Crash: game closes** | After 3+ `effect: unverifiable` clicks, Grey Hack may self-terminate. Kill-Switch MUST trigger at 3 consecutive failures — no retries |

## Verification Checklist (Before Live-Run)

- [ ] cua-driver installed (`hermes computer-use install`)
- [ ] Tesseract OCR available (`which tesseract`)
- [ ] Telegram token in `~/.hermes/.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_HOME_CHANNEL`)
- [ ] Dry-run succeeded (mission parses, all steps enumerated)
- [ ] Vault backup created
- [ ] Kill-switch test passed (manually triggered with dummy permission dialog)
- [ ] GreyHack window visible to cua-driver (not Big-Picture mode)
- [ ] Wayland Env-Vars set: `DISPLAY=:1` + `XAUTHORITY` matches current session (`ls /run/user/$(id -u)/.mutter-Xwaylandauth*`)
- [ ] Grey Hack has one window (check `xdotool search --name &quot;Grey&quot;` — if 2 results, use the lower hexadecimal Window-ID)
- [ ] Anti-Cheat awareness: plan for `effect: unverifiable` — max 3 retries, then switch to User-as-Input-Channel
- [ ] Observer capture limit: set `--interval 60` not 5, or prepare daily-note format to avoid Storage Bloat (254 files in 15 min possible)

## Connecting Skills

- **`computer-use`** — The base cua-driver skill (universal, any-model)
- **`subagent-patterns`** — The State-Machine pattern comes from here
- **`working-agreement`** — §7 covers Telegram routing conventions
- **`vault-architecture`** — Vault structure where missions live

## Filesystem Layout

```
~/.hermes/skills/computer-use/
├── greyhack-game-observer/
│   ├── SKILL.md
│   └── scripts/greyhack_capture.py
├── greyhack-smart-macro/
│   ├── SKILL.md
│   └── scripts/greyhack_macro.py
├── greyhack-mission-orchestrator/
│   ├── SKILL.md
│   └── scripts/orchestrator.py + mission_state.py
└── greyhack-suite-README.md  (Quickstart for all three)

Obsidian Vault:
03 Projekte/Queen-Bee-Lab/
├── Missions/  (one .md per mission)
└── Mission-State - Live-Status.md  (auto-updated)

99 Capture/  (Observer screenshots, auto-populated)

05 Ressourcen/
└── GreyHack - Computer-Use-Mission-System.md  (architecture overview)
```

## Why This Suite Exists

GreyHack is the ideal test lab for Multi-Agent patterns because:
1. **Failure is recoverable** — game restarts cleanly, no real-world blast radius
2. **Observable** — visual state changes are visible via screenshots (Pattern-7 verification)
3. **Scriptable** — GreyScript gives us a textual interface into the game world
4. **Mission-shaped** — clear goal/target structure maps perfectly onto Plan→Execute→Verify loops