# Grey Hack Game Reconnaissance — Worked Example (2026-07-06)

> Full session log from the first successful Computer-Use reconnaissance of Grey Hack V0.9.6771 on Basti's Zorin OS 18.1 (Wayland host + Steam Flatpak + Xwayland for the game).

## Environment

| Component | Value |
|---|---|
| OS | Zorin OS 18.1 (Ubuntu 24.04 Noble) |
| Session | Wayland (`zorin-wayland`) — Xwayland for game |
| Game | Grey Hack V0.9.6771 - BETA via Steam (Flatpak) |
| Game PIDs | 4563 (main) + 876 (Steam mirror) |
| Game Window IDs | 12582985 + 56623112 (both 1920x1080 @ Y=391) |
| In-game user | `gregor@ibm` |
| Tesseract | 5.3.4 with `eng+deu` language packs |
| cua-driver | 0.7.0 |

## Display-Variable Setup (First Blocker)

Without explicit env vars, cua-driver `doctor` returned:

```
[warn] display server: neither DISPLAY nor WAYLAND_DISPLAY set
```

**Solution:** Inspect Xwayland process:

```bash
ps -eo pid,cmd | grep -i Xwayland
# /usr/bin/Xwayland :1 -rootless -noreset ... -auth /run/user/1000/.mutter-Xwaylandauth.L8U0R3
```

→ `DISPLAY=":1"`, `XAUTHORITY="/run/user/1000/.mutter-Xwaylandauth.L8U0R3"`.

After setting both in every subprocess, cua-driver `doctor`:

```
[ok  ] display server: X11 (DISPLAY=:1)
[ok  ] X11 connection: connected, 2 visible top-level windows
[ok  ] AT-SPI: org.a11y.Bus reachable via session bus
```

All 6 checks green.

## Window Detection

```bash
xdotool search --name "Grey"
# → 12582985
# → 56623112

wmctrl -lp
# 0x03000044  0 247    bratan-17-P1 Steam
# 0x03600008  0 876    bratan-17-P1 Grey Hack
```

Two Grey Hack windows exist — the main game window (12582985) and a Steam-overlay mirror (56623112). Both show the same content.

## AT-SPI Returns Nothing Useful

```bash
cua-driver call get_window_state '{"pid": 4563, "window_id": 12582985, "include_screenshot": false}'
# {
#   "element_count": 1,
#   "elements": [{"element_index": 0, "role": "window"}],
#   "tree_markdown": "- [0] window \"\" [actions=[activate]]\n"
# }
```

**Confirmed:** Grey Hack is a pure canvas renderer. AT-SPI gives us nothing beyond "this is a window". All UI info must come from OCR.

## Screenshot Capture (Three Methods Tested)

| Method | Result | Notes |
|---|---|---|
| `cua-driver call get_desktop_state` | ❌ Fails: `X11 error BadMatch code 8` | Desktop-scope screenshot not supported in this Xwayland config |
| `cua-driver call get_window_state ... include_screenshot: true` | ✅ 1568x882, ~330 KB | Returns base64 PNG + (empty) AT-SPI tree |
| `xwd -id 12582985 → convert xwd → png` | ✅ 1920x1080, ~300 KB | Full native res; 2-step subprocess chain |

**Decision:** Use cua-driver when available (cleaner), fall back to xwd if cua-driver times out or returns error.

## OCR with --psm 6 (The Critical Finding)

Tested three PSM modes against the Manual page (Inhaltsverzeichnis):

| PSM Mode | Char Count | Quality |
|---|---|---|
| `--psm 3` (auto) | 498 | Words fragmented: `Branchin;`, `Loopir` |
| `--psm 4` (column) | 455 | Same fragmentation issues |
| **`--psm 6` (uniform block)** | **1048** | **Clean word boundaries, full table legible** |

Combined with TSV mode → pixel-perfect coordinates for every detected word.

## App-Taskbar Coordinates (From TSV)

Tesseract TSV output with `--psm 6`:

```
FileExplorer  left=195  top=159  width=91   (confidence 93.0)
Terminal      left=386  top=159  width=67   (confidence 94.9)
Map           left=585  top=167  width=30   (confidence 97.0)
Mail          left=766  top=159  width=28   (confidence 96.7)
Browser       left=929  top=159  width=63   (confidence 96.5)
Notepad       left=1108 top=167  width=64   (confidence 96.7)
Manual        left=1293 top=159  width=54   (confidence 96.9)
CodeEditor    left=1457 top=159  width=86   (confidence 82.8)
Gift-txt      left=1653 top=167  width=55   (confidence 82.4)
```

These are **Window-local coordinates** (Window at X=0, Y=391 on desktop). To get desktop coordinates for clicking: add `(Window_y_offset=391)` and `(button_width/2)`:

```python
APP_CLICK_CENTERS = {
    "FileExplorer": (240, 565),
    "Terminal":    (421, 565),
    "Map":         (600, 565),
    "Mail":        (780, 565),
    "Browser":     (944, 565),
    "Notepad":     (1123, 565),
    "Manual":      (1305, 565),  # currently active
    "CodeEditor":  (1477, 565),
    "Gift-txt":    (1678, 565),
}
```

## Anti-Cheat Discovery (The Important One)

Tried three input methods against the game:

| Method | cua-driver Response | xdotool Behavior |
|---|---|---|
| `click` (left, screen coords) | `{"effect": "unverifiable", "path": "xtest_desktop", "verified": false}` | exit 0, but no state change |
| `click` with `pid`+`window_id` | `{"effect": "unverifiable", "path": "x11_atspi", "verified": false}` | n/a |
| `type_text` ("help\n") | `{"effect": "unverifiable", "escalation": {"reason": "background insert could not be confirmed"}}` | n/a |
| `bring_to_front` | Success: `{"prior_active": 56623112, "window_id": 12582985}` | works (no synthetic input) |

**Conclusion:** Grey Hack rejects **synthetic input via XSendEvent**. XTEST path (foreground) might work but wasn't tested (would steal focus). Game state manipulation via Computer-Use is effectively blocked.

**Fallback:** Switched to **read-only reconnaissance mode** — OCR-only, build coordinate maps, extract Manual content via screenshots while user clicks navigation buttons.

## Manual Extraction Pipeline (Proven Workflow)

For each manual page user navigated to:

```python
def capture_and_extract(label):
    """Capture Grey Hack window + extract text via OCR."""
    env = gh_env()
    result = subprocess.run(
        ["cua-driver", "call", "get_window_state", json.dumps({
            "pid": 4563, "window_id": 12582985, "include_screenshot": True
        })],
        capture_output=True, text=True, env=env, timeout=20
    )
    data = json.loads(result.stdout)
    png = base64.b64decode(data["screenshot_png_b64"])
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    vault = Path(f"/home/bratan/Dokumente/Obsidian Vault/99 Capture/gh_manual_{timestamp}.png")
    vault.parent.mkdir(parents=True, exist_ok=True)
    vault.write_bytes(png)
    
    ocr = subprocess.run(
        ["tesseract", str(vault), "-", "-l", "eng+deu", "--psm", "6"],
        capture_output=True, text=True, env=env, timeout=20
    ).stdout.strip()
    
    return png, ocr, vault

# User clicks navigation button manually
# Then: capture_and_extract("manual_firststeps")
# Then: generate vault note with OCR content
```

**Three manual sections extracted in one session:**
- `GreyHack-Manual-Libraries-und-Exploits` (5574 bytes — Remote/Local/Zero-Day exploits)
- `GreyHack-Manual-First-Steps` (4010 bytes — WiFi hack workflow)
- `GreyHack-Manual-Savegame` (2127 bytes — Auto-save mechanics)
- `GreyHack-Manual-Avoid-Traces` (3268 bytes — /var/system.log cleanup)

Total: 14979 bytes of structured knowledge extracted from in-game UI.

## Key Takeaways

1. **Canvas games need vision-first.** AT-SPI returns one element. OCR is the only interface.
2. **Display vars must be explicit on Wayland+Xwayland.** Forgetting this is the #1 source of "computer use doesn't work" reports.
3. **`--psm 6` is the OCR mode for game UIs.** Other modes fragment words badly.
4. **TSV mode gives you pixel coordinates for free.** No separate image analysis needed.
5. **`effect: unverifiable` is the anti-cheat signal.** Switch to read-only mode immediately.
6. **`bring_to_front` works without synthetic input.** Useful for window activation without click contamination.
7. **Two windows (main + Steam mirror) is normal.** Both show same content; either is fine to capture.
8. **Save screenshots to vault `99 Capture/` not /tmp.** /tmp is ephemeral; vault is permanent.

## Anti-Patterns Discovered

- ❌ **Trusting "exit 0" from xdotool click without screenshot verification** — game state may not change despite success report
- ❌ **Using desktop-scope screenshot on Xwayland** — BadMatch error; use window-specific
- ❌ **Setting only DISPLAY without XAUTHORITY** — XSendEvent auth fails silently
- ❌ **Reading OCR without TSV** — you get text but lose coordinates (hard to map back to UI)
- ❌ **Single-PSM-mode OCR pipeline** — always run with `psm 6` for games, log if quality drops