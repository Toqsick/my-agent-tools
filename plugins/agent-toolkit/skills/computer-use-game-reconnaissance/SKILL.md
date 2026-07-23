---


name: computer-use-game-reconnaissance
description: Use when user asks for computer use game reconnaissance, Computer-Use Game Reconnaissance, When to Use This Skill, Why Bother? (Cost vs Value). NOT for unrelated tasks, simple questions. Reconnoiters game executables via static file analysis before GUI automation.
platforms:
- linux
category: computer-use
version: 1.0.0
author: Yuno (Basti)
lane: worker-flash
reasoning_effort: high
triggers:
- game reconnaissance
- canvas game UI
- OCR a game window
- cua-driver game
- in-game vision
- computer use canvas game
- extract in-game manual
- user clicks manually
- ich klicke selber durch
- manual extraction
- game internals deep scan
- static game analysis
- pre-launch reconnaissance
- DLL inventory
- game file structure scan
- strings analysis on game
- what scripting engine does X use
license: MIT

---

# Computer-Use Game Reconnaissance

Drive **canvas-rendered games** (no AT-SPI, anti-cheat-aware) via Computer-Use tools — read state, document UI layout, build a coordinate map for future automation. Proven on Grey Hack V0.9.6771 (Steam, Flatpak, Wayland host, 1920x1080 window).

## When to Use This Skill

| Trigger | Why |
|---|---|
| "Recon a game" / "Map a game UI" | Need systematic UI/UX inventory before any automation |
| "OCR a canvas game" / "Read a game window" | Extract text from a window that has no AT-SPI accessibility tree |
| "Computer-use in-game" | Want vision-based interaction without text-protocol APIs |
| "Build a coordinate map for a game" | Find pixel positions of buttons/menus without UI tree access |
| "cua-driver game" / "Grey Hack vision" | Specific game requests |

**Don't use this for:** normal GUI apps with AT-SPI (use `computer-use` skill directly), text-mode games with documented protocols (just pipe text), games with public modding APIs (use the API).

## Phase 0: Pre-Launch Static File Analysis (Configs, DLLs, Scripting Engine)

> **Run this BEFORE launching the game.** Every Unity game ships a directory of
> managed DLLs, configs, and native plugins — reading these tells you the
> scripting engine, game version, networking libs, mod potential, and security
> surface without a single OCR step.

### Why Bother? (Cost vs Value)

| Time | Insight Gained | Alternatives |
|---|---|---|
| ~2 min | Scripting engine (Mono vs IL2CPP vs custom) | Takes 1h+ of in-game probing |
| ~1 min | Game version (Unity build GUID, Addressables, patch date) | Not shown in most games |
| ~3 min | DLL inventory (game logic size, 3rd-party libs, mono BCL) | Invisible from inside the game |
| ~3 min | Strings scan → library names, keywords, native deps | Reveals features user may not know exist |

**Total:** ~10 minutes of static analysis before ever touching the game itself.

### Unity Game Directory Anatomy (Common)

```
Grey Hack/
├── Grey Hack.x86_64              → ELF stub (loads UnityPlayer.so)
├── UnityPlayer.so                → Unity runtime (32 MB, BuildID embedded)
├── Grey Hack_Data/
│   ├── app.info                  → App name (no version — version lives in build GUID)
│   ├── boot.config               → Build GUID, GC settings, HDR toggle
│   ├── ScriptingAssemblies.json  → 89+ DLLs manifest (game logic + Unity + Mono)
│   ├── RuntimeInitializeOnLoads.json → Auto-init hooks at startup
│   ├── Managed/                  → 100+ managed DLLs (game logic, Unity engine, Mono BCL, 3rd-party)
│   │   ├── Assembly-CSharp.dll   → ***Haupt-Game-Logic*** (3.6 MB)
│   │   ├── Assembly-CSharp-firstpass.dll → Bootstrap (often pure Unity image effects)
│   │   ├── Newtonsoft.Json.dll   → JSON (save games, web API)
│   │   ├── Facepunch.Steamworks.* → Steamworks wrapper
│   │   ├── Mono.Data.Sqlite.dll  → Local SQLite (if game uses one)
│   │   ├── Paroxe.PDFRenderer.dll → PDF rendering
│   │   └── 80+ Unity.*.dll       → Engine modules
│   ├── Plugins/                  → Native .so libraries (steam_api, pdf renderer, ...)
│   ├── Resources/                → Unity built-in resources (splash, shared assets)
│   ├── StreamingAssets/aa/       → Addressables bundles (catalog, locale data, asset bundles)
│   ├── MonoBleedingEdge/         → Embedded Mono runtime
│   └── *.db                      → Local SQLite database (game state, player data)
```

### The Scan Pipeline (7 Phases)

#### Phase 1 — Config Files (1 min)

```bash
cat "/path/to/Grey Hack_Data/app.info"
cat "/path/to/Grey Hack_Data/boot.config"
# → Build GUID is the version fingerprint
```

Key findings:
- **`app.info`** — just app name. No version number.
- **`boot.config`** — `build-guid=<uuid>` = deterministic build identifier.
- **`ScriptingAssemblies.json`** — lists every DLL Unity loads. Game logic DLLs
  (`Assembly-CSharp.dll`, `Assembly-CSharp-firstpass.dll`) are the priority targets.
- **`RuntimeInitializeOnLoads.json`** — hooks that fire at boot
  (custom log filters, Addressables init).

#### Phase 2 — DLL Inventory with Categorization (2 min)

```python
# Python pseudocode — stat every .dll in Managed/, categorize by prefix
for dll in Managed/*.dll:
    entry = {"name": dll.name, "size": dll.size(), "mtime": dll.mtime(), "sha256": hash(dll)}
    if dll.name in ("Assembly-CSharp.dll", "Assembly-CSharp-firstpass.dll"):
        entry["category"] = "GAME_LOGIC"
    elif dll.name.startswith(("UnityEngine", "Unity.", "Unity/")):
        entry["category"] = "UNITY_ENGINE"
    elif dll.name.startswith(("mscorlib", "System.", "Mono.", "netstandard")):
        entry["category"] = "MONO_RUNTIME"
    else:
        entry["category"] = "THIRD_PARTY"
```

Expected distribution (Grey Hack confirmed):

| Category | Count | Example |
|---|---|---|
| **GAME_LOGIC** | 2 | Assembly-CSharp.dll (3.6 MB), Assembly-CSharp-firstpass.dll (80 KB) |
| **UNITY_ENGINE** | ~79 | UnityEngine.*Module.dll, Unity.*.dll |
| **MONO_RUNTIME** | ~24 | mscorlib, System.*, Mono.* |
| **THIRD_PARTY** | ~4 | Newtonsoft.Json, Facepunch.Steamworks.Posix, OSA, Paroxe.PDFRenderer |

**Key signal:** The mtime of `Assembly-CSharp.dll`. If it's different from all
other DLLs, the game got a **live patch** (common for Steam games with hotfixes).
This is the only DLL that changes post-launch — all other DLLs stay at the
original build timestamp.

#### Phase 3 — Native Plugins Scan (1 min)

```bash
ls -la "Grey Hack/Grey Hack_Data/Plugins/"
file "Grey Hack/Grey Hack_Data/Plugins/"*
strings "Grey Hack/Grey Hack_Data/Plugins/libsteam_api.so" | grep -E 'AppID|SteamAPI|S_API' | head -10
```

Expected:
- **`libsteam_api.so`** — Steamworks. Spot-check strings for AppID.
- **`libpdfrenderer.so`** — PDF rendering (if game has in-game docs).
- **`UnityPlayer.so`** — at top-level (not in Plugins/). strings for `BuildID`.

#### Phase 4 — Strings Analysis (3 min, the high-value step)

```bash
# 1. Find the scripting engine
strings "Managed/Assembly-CSharp.dll" | grep -iE 'Miniscript|Lua|Python|Mono\.(Script|CSharp)|JS\.(Engine|Runtime)' | sort -u

# 2. Find library/API names (GreyScript case)
strings "Managed/Assembly-CSharp.dll" | grep -E 'LIB[A-Z]{2,}|METAXPLOIT|KERNEL_MODULE|CRYPTO' | sort -u

# 3. Find source file paths (reveals project structure)
strings "Managed/Assembly-CSharp.dll" | grep -E 'Assets\\.*\.(cs|js)' | sort -u | head -40

# 4. Find factory methods (API entry points)
strings "Managed/Assembly-CSharp.dll" | grep -E 'Create.*Lib|Get.*Lib|Init[A-Z]|Install[A-Z]' | sort -u

# 5. Find version strings
strings "Managed/Assembly-CSharp.dll" | grep -iE 'version|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | sort -u | head -20

# 6. Find native .so references (P/Invoke targets)
strings "Managed/Assembly-CSharp.dll" | grep -E '\.so$|\.so\.[0-9]' | sort -u
```

What each tells you:
- **Scripting engine** — determines mod potential. Miniscript = Grey Hack's custom fork. Lua/Python/JS = different game.
- **Library names** — uppercase enums = internal library enum. All 14+ library names revealed.
- **Source paths** — `Assets\Greyscript\CryptoIntrinsics.cs` = C# source structure.
- **Factory methods** — `CreateCryptoLib`, `CreateMetaXploitLib` = API entry points.
- **Version strings** — embedded DLL versions, Unity versions.
- **Native refs** — empty = 100% managed C#. Found refs = P/Invoke surface.

#### Phase 5 — Resources + StreamingAssets (1 min)

```bash
ls -la "Grey Hack_Data/Resources/"
ls -la "Grey Hack_Data/StreamingAssets/aa/"
jq '.m_AddressablesVersion, .m_SettingsHash' "StreamingAssets/aa/settings.json"
```

What to look for:
- **addressables version** — tells you Unity build target version
- **locale files** — which languages are shipped (e.g. only EN + ES = no DE)
- **settings hash** — deterministic fingerprint of build settings

#### Phase 6 — Subagent Verification (2 min)

Dispatch a `delegate_task(role='leaf')` to independently run `strings` on
the game logic DLLs and cross-reference your findings. This catches false
positives and missed hits:

```
# Main agent finds 14 library names
# Sub-bee independently finds: same 14 + confirms count + finds 3 more
# → cross-reference: 14 confirmed, 3 debatable → final list: 14
```

See `sub-sub-workflow` skill for the full dispatch pattern. The sub-bee
should write its findings to
`/tmp/gh-fullscan-<ts>-sub.md` with the same section structure as the
parent report.

#### Phase 7 — Output Generation (1 min)

Two outputs, both valuable:

**A) Machine-readable JSON** — full DLL inventory with sizes, hashes, mtimes:
```json
{
  "scan_metadata": {...},
  "game_version": {...},
  "config_files": {...},
  "dll_inventory": {"total_count": 109, "categories": {...}, "all_dlls": [...]},
  "plugins_native": [...],
  "streaming_assets": {...},
  "greyscript_libraries_detected": [...],
  "scripting_engine": "Miniscript (custom fork)"
}
```

**B) Obsidian Markdown report** — structured knowledge with:
- TL;DR table (key metrics at a glance)
- Security-relevant observations
- Follow-up scan recommendations

### Pitfalls

| # | Pitfall | Symptom | Fix |
|---|---|---|---|
| 1 | Only scanned one DLL | Miss 80% of the picture (Unity/Mono/3rd-party) | Always enum ALL DLLs, then filter |
| 2 | Trusted mtime as patch evidence | Fresh install might not match original | Cross-check build GUID + catalog hash |
| 3 | Stopped at first `strings` result | False positives from Unity boilerplate | Verify with subagent or grep for specific patterns |
| 4 | Assumed IL2CPP from directory layout | Missed that Mono DLLs are present and loadable | Check for MonoBleedingEdge/ AND Managed/*.dll |
| 5 | Only wrote Obsidian report (no JSON) | Machine-readable data lost for future cross-referencing | Write BOTH — JSON for automation, MD for human reading |

### When to Use This Whole Pipeline

Load this skill and start at Phase 0 when the user asks any of:
- "game internals deep scan"
- "static game analysis"
- "pre-launch reconnaissance"
- "DLL inventory"
- "game file structure scan"
- "strings analysis on game"
- "what scripting engine does X use"

### Reference File

- `references/greyhack-static-analysis-2026-07-14.md` — full worked example
  of the 7-phase pipeline applied to Grey Hack (109 DLLs, 15 GreyScript
  libraries identified, subagent verification confirmed)

## Core Insight: Canvas Games Need Vision-First

Canvas-rendered games (Grey Hack, most Steam games on Linux) draw their entire UI to a single GPU buffer. The OS sees **one window with one role: "window"** — no buttons, no menus, no labels. AT-SPI returns `element_count: 1` and the only element is `window "<game>"`.

**Solution:** Treat the game as a **read-only image stream**, extract text via OCR, and use OCR's bounding-box output (TSV) to derive UI coordinates.

## Pattern 1: Wayland + Xwayland Display Setup (Critical)

### The Problem

Modern Linux desktops run **Wayland** (Zorin/Ubuntu default). The game launches via Xwayland (X11 server embedded in Wayland for compatibility). When cua-driver runs as a subprocess, **it inherits no display vars** → `doctor` reports:

```
[warn] display server: neither DISPLAY nor WAYLAND_DISPLAY set
```

→ All window-driving tools fail silently.

### The Fix

Set **two env vars** before every cua-driver subprocess:

```python
env = os.environ.copy()
env["DISPLAY"] = ":1"
env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"
```

### How to Find Your Values

```bash
# DISPLAY: look at Xwayland process
ps -eo pid,cmd | grep -i Xwayland
# Output: /usr/bin/Xwayland :1 -rootless -noreset ... -auth /run/user/1000/.mutter-Xwaylandauth.L8U0R3

# DISPLAY = ":1" (the number after the colon)
# XAUTHORITY = the path after "-auth"
```

### Helper Function

```python
def gh_env():
    """Standard env for cua-driver / xdotool on Wayland+Xwayland."""
    env = os.environ.copy()
    env["DISPLAY"] = ":1"
    env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"
    return env
```

Use this for every cua-driver / xdotool / xwd / scrot call. **Forgetting it is the #1 cause of "computer use doesn't work" reports.**

## Pattern 2: Window-Specific Screenshots (The Workhorse)

cua-driver's desktop screenshot (`get_desktop_state`) **fails with X11 error code 8 (BadMatch)** on Wayland+Xwayland for some setups. **Window-specific screenshots work.** Two methods:

### Method A: cua-driver (preferred when working)

```python
import subprocess, json, base64
env = gh_env()
result = subprocess.run(
    ["cua-driver", "call", "get_window_state", json.dumps({
        "pid": 4563, "window_id": 12582985, "include_screenshot": True
    })],
    capture_output=True, text=True, env=env, timeout=20
)
data = json.loads(result.stdout)
png_bytes = base64.b64decode(data["screenshot_png_b64"])
# png_bytes is ready to OCR or save
```

Returns: 1568x882 PNG (max_image_dimension default), 200-500 KB.

### Method B: xwd + convert (fallback when cua-driver fails)

```python
# xwd = X Window Dump, captures any specific window
subprocess.run(["xwd", "-id", str(wid), "-silent", "-out", "/tmp/screen.xwd"], env=env, timeout=10)
subprocess.run(["convert", "/tmp/screen.xwd", "/tmp/screen.png"], timeout=10)
# Then OCR /tmp/screen.png
```

**Returns:** native resolution (1920x1080), larger file (~300 KB), no base64 roundtrip.

### When to Use Which

| Method | Pros | Cons |
|---|---|---|
| cua-driver `get_window_state` | Always includes AT-SPI tree (even if empty); base64 in single call | Fails on some Wayland+Xwayland configs (X11 BadMatch) |
| xwd + convert | Always works when window is on-screen; full native res | Requires 2 subprocess calls; no AT-SPI tree |

## Pattern 3: OCR with TSV Mode for Coordinate Extraction

This is the **secret weapon** for canvas games — Tesseract's TSV output mode gives pixel-perfect coordinates for every detected word.

### The Command

```bash
tesseract /tmp/screen.png /tmp/out -l eng+deu --psm 6 tsv
```

- `psm 6` = Assume a uniform block of text (best for game UIs)
- `tsv` = Tab-separated output with left/top/width/height/conf/text columns
- `-l eng+deu` = Multi-language (Grey Hack uses German UI strings)

### Why `--psm 6` and Not 3 or 4?

Tested on Grey Hack:
- **psm 3 (auto)**: ~498 chars, fragments words (`FizzBuzz` → `Branchin;`, `Loopir`)
- **psm 4 (column)**: ~455 chars, similar issues
- **psm 6 (uniform block)**: ~1048 chars, clean word boundaries, **plus TSV coordinates**

### Parsing TSV for UI Elements

```python
tsv_output = subprocess.run(
    ["tesseract", png_path, "-", "-l", "eng+deu", "--psm", "6", "tsv"],
    capture_output=True, text=True
).stdout

# TSV columns: level page_num block_num par_num line_num word_num left top width height conf text
for line in tsv_output.split("\n"):
    cols = line.split("\t")
    if len(cols) >= 12 and cols[11].strip() and cols[10] != "-1":
        word = cols[11].strip()
        x, y, w, h = cols[6], cols[7], cols[8], cols[9]
        # x,y is top-left corner; w,h is size
        center_x = int(x) + int(w) // 2
        center_y = int(y) + int(h) // 2
        # → click target for future automation
```

### Map → Action

Once you have coordinates, build a **click-target map**:

```python
# Pseudo-detected from TSV:
app_positions = {
    "FileExplorer": (195 + 45, 159 + 391 + 15),
    "Terminal":    (386 + 35, 159 + 391 + 15),
    "Map":         (585 + 15, 159 + 391 + 15),
    # ...
}
# Then: subprocess.run(["xdotool", "click", ...]) or cua-driver click
```

## Pattern 4: Anti-Cheat Detection Signal

Canvas games (and many Steam games) implement **anti-bot detection** that rejects XSendEvent synthetic input. The symptom is consistent across cua-driver and xdotool:

### cua-driver Signal

```json
{
  "effect": "unverifiable",
  "escalation": {
    "reason": "background insert could not be confirmed — re-call with delivery_mode:\"foreground\" if a screenshot shows the text didn't appear",
    ...
  }
}
```

The `"effect": "unverifiable"` field is your anti-cheat tell. The escalation hint suggests `delivery_mode: "foreground"`, but be aware **foreground steals focus from the user**.

### xdotool Signal

xdotool `click` and `type` **report success (exit 0)** but the game state **does not change**. Verify by screenshotting after each action and diffing OCR output.

### Mitigation Strategies

| Strategy | Cost | Trade-off |
|---|---|---|
| `delivery_mode: "foreground"` | Focus theft | User sees every action; may break their flow |
| Move mouse over target before click | Slow | Sometimes tricks anti-cheat that checks mouse movement |
| Press key for longer (`xdotool key --delay 100`) | Slow | Mimics human key-hold timing |
| Drive the game via its **internal scripting API** if available | Best | But most games don't expose one |
| **Give up clicks, use only OCR** | None | Read state, don't manipulate — perfect for reconnaissance |

### Decision Tree

```
Is the game state manipulable via API/terminal? ──── YES → use API, no Computer-Use needed
                 │ NO
                 ▼
Does cua-driver click return "unverifiable"? ──── YES → use foreground-mode + user consent
                 │ NO
                 ▼
Does xdotool click change game state? ──── YES → use xdotool (cheaper)
                 │ NO
                 ▼
Read-only mode: OCR-only, document UI, build maps for human-driven automation
```

## Pattern 5: Reconnnaissance Loop (5-Phase Cycle)

```
Phase 1: Capture  → screenshot via cua-driver OR xwd
Phase 2: OCR      → tesseract --psm 6 (and tsv for coordinates)
Phase 3: Map      → parse TSV, identify UI elements + their click centers
Phase 4: Verify   → screenshot again after each action attempt
Phase 5: Document → write findings to vault (Obsidian note + screenshots)
```

**Pattern: Always run a verify-screenshot after any action.** If state didn't change, you hit anti-cheat — fall back to OCR-only mode.

## Pattern 7: Hybrid Manual-Extraction Workflow (User Drives, Yolo Reads)

When the game has rich in-game documentation (manuals, tutorials, codex) that the user wants to extract to vault notes, but **cua-driver clicks are blocked by anti-cheat** (Pattern 4), use a **hybrid** approach:

### The Workflow

1. **User navigates manually** — clicks the next manual page/section in the game
2. **Yolo screenshots + OCRs in parallel** — no synthetic input needed
3. **Yolo generates vault note** with OCR content + Mission-Relevanz + Wiki-Links

### Why This Works

- ✅ User has real input → game advances to next page (anti-cheat doesn't fire)
- ✅ Yolo gets full-resolution screenshot of the new page (via Pattern 2)
- ✅ OCR extracts clean text (Pattern 3) with no risk of detection
- ✅ Vault grows systematically with each page
- ❌ Slower than autonomous clicks (one page per user action)
- ❌ Requires user attention (but they can keep playing while Yolo processes)

### Detection Signal That This Pattern Is Needed

| Signal | Meaning |
|---|---|
| `effect: unverifiable` on cua-driver click | Anti-cheat blocks synthetic input (Pattern 4) |
| User says "I'll click myself" / "ich klicke selber durch" | User has accepted manual driving as alternative |
| Game has rich text content (manuals, codex, tutorial pages) | Worth systematic extraction even if slow |

### Per-Page Loop

```
User clicks next manual page in game
       ↓
Yolo captures window screenshot (Pattern 2)
       ↓
Yolo runs OCR with --psm 6 (Pattern 3)
       ↓
Yolo writes vault note:
  - Frontmatter (tags, aliases, importance, source-page, datum)
  - OCR content (cleaned, structured)
  - "🎮 Mission-Relevanz" section (maps content to active missions)
  - "🔗 Verbindet zu" wiki-links (other manual sections + missions + MOCs)
       ↓
User clicks next page → loop repeats
```

### Reusable Note Template (for Pattern 7)

The note skeleton from Pattern 6 can be reused unchanged, but **always** add the `Mission-Relevanz` and `Verbindet zu` sections — these make the extracted content useful for active projects, not just dead docs.

### Real-World Result (Grey Hack 2026-07-06)

Extracted 7 manual sections in ~30 minutes of user clicking:
- First Steps (WiFi hack workflow)
- Savegame (auto-save mechanics)
- Avoid Traces (/var/system.log cleanup)
- Libraries & Exploits (Remote/Local/Zero-Day)
- Karma & Reputation (hack reputation system)
- Reverse Shell (rshell + social engineering)
- Scripting Libraries (22+ GreyScript modules)

Total: ~29 KB of structured vault knowledge that the orchestrator can now reference for mission-step implementation.

## Pattern 6: OCR Output → Vault Note Pipeline

This is where Computer-Use meets Obsidian vault work. After OCR'ing a game screen:

```python
vault_path = Path("/home/bratan/Dokumente/Obsidian Vault/09 System-Doku/<Game>")
vault_path.mkdir(parents=True, exist_ok=True)

# 1. Save screenshot
screenshot_file = vault_path / f"{topic}_{timestamp}.png"
screenshot_file.write_bytes(png_bytes)

# 2. Run OCR
ocr_text = subprocess.run(
    ["tesseract", str(screenshot_file), "-", "-l", "eng+deu", "--psm", "6"],
    capture_output=True, text=True
).stdout

# 3. Generate vault note with frontmatter + OCR content + Verbindet zu
note_content = f"""---
tags: [gaming, {game_slug}, manual, reconnaissance, 2026-07-06]
aliases: [{game}-Manual-{section}]
importance: 8
quelle: {game} Manual (In-Game)
seite: {section}
datum: 2026-07-06 17:29
author: Yuno (Computer-Use-OCR-Extraktion)
---

# 📘 {game} Manual: {section}

> **Quelle**: In-Game Manual
> **OCR-Extrahierung**: Tesseract 5.3.4 via cua-driver screenshot
> **Datum**: ...
> **Original-Screenshot**: `99 Capture/{screenshot_name}`

{ocr_content}

## 🎮 Mission-Relevanz

...

## 🔗 Verbindet zu

- [[<related-note>]]
"""
```

Each manual section becomes its own note → enzyklopädisch vernetzt via Wiki-Links.

## Pitfalls

| # | Pitfall | Symptom | Fix |
|---|---|---|---|
| 1 | Forgot display env vars | `cua-driver doctor`: "neither DISPLAY nor WAYLAND_DISPLAY set" | Set DISPLAY + XAUTHORITY in every subprocess (Pattern 1) |
| 2 | Used `--psm 3` or `--psm 4` for OCR | Fragmented OCR (`Branchin;`, `Loopir`) | Use `--psm 6` for canvas game UIs |
| 3 | Trusted cua-driver "unverifiable" silently | Game state never changes despite success messages | Detect `effect: unverifiable`, switch to OCR-only mode |
| 4 | Used xdotool click without verifying | Wasted time clicking on non-clickable areas | Always screenshot+OCR-diff after action |
| 5 | Single window ID assumed | Captured Steam-overlay window instead of game window | Use both window IDs and compare OCR; main window has full UI |
| 6 | No timestamp on screenshots | Can't reconstruct recon session | Filename: `{topic}_{YYYYMMDD_HHMMSS}.png` |
| 7 | Saving screenshots only in /tmp | Lost on reboot | Save into vault `99 Capture/` folder for permanence |

## Reference Recipes

### Recipe 1: Full Game Recon Loop (Grey Hack Example)

```python
import subprocess, os, json, time, base64
from pathlib import Path

def gh_env():
    env = os.environ.copy()
    env["DISPLAY"] = ":1"
    env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"
    return env

def capture_game_window(wid, label="recon"):
    """Capture + OCR + save to vault."""
    env = gh_env()
    
    # Try cua-driver first
    result = subprocess.run(
        ["cua-driver", "call", "get_window_state", json.dumps({
            "pid": 4563, "window_id": int(wid), "include_screenshot": True
        })],
        capture_output=True, text=True, env=env, timeout=20
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        png = base64.b64decode(data["screenshot_png_b64"])
    else:
        # Fallback: xwd + convert
        subprocess.run(["xwd", "-id", str(wid), "-silent", "-out", "/tmp/screen.xwd"],
                       capture_output=True, env=env, timeout=10)
        subprocess.run(["convert", "/tmp/screen.xwd", "/tmp/screen.png"], env=env, timeout=10)
        png = Path("/tmp/screen.png").read_bytes()
    
    # Save to vault
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    vault_capture = Path(f"/home/bratan/Dokumente/Obsidian Vault/99 Capture/game_{label}_{timestamp}.png")
    vault_capture.parent.mkdir(parents=True, exist_ok=True)
    vault_capture.write_bytes(png)
    
    # OCR
    ocr = subprocess.run(
        ["tesseract", str(vault_capture), "-", "-l", "eng+deu", "--psm", "6"],
        capture_output=True, text=True, env=env, timeout=20
    ).stdout.strip()
    
    return png, ocr, vault_capture

# Usage:
png, ocr_text, path = capture_game_window(12582985, label="manual_firststeps")
print(f"📸 {path.name} ({len(png)} bytes)")
print(f"📝 OCR ({len(ocr_text)} chars):")
print(ocr_text[:500])
```

### Recipe 2: Detect Anti-Cheat

```python
def detect_anti_cheat(action_result_json):
    """Returns True if cua-driver signaled unverifiable (anti-cheat)."""
    try:
        data = json.loads(action_result_json)
        return data.get("effect") == "unverifiable"
    except:
        return False
```

## See Also

- `computer-use` skill — base cua-driver usage (windows, clicks, typing)
- `greyhack-game-observer` — Grey Hack-specific observer (uses this pattern)
- `greyhack-smart-macro` — Grey Hack-specific click/type (built on this skill)
- `sub-sub-workflow` — independent subagent verification pattern (used in Phase 0, Phase 6)
- `references/greyhack-recon-2026-07-06.md` — in-game visual reconnaissance with OCR coordinates and anti-cheat discovery
- `references/greyhack-manual-extraction-2026-07-06.md` — Pattern 7 (hybrid user-drives / Yolo-OCRs) session detail + cross-linking strategy
- `references/greyhack-static-analysis-2026-07-14.md` — Phase 0 worked example: full 7-phase static analysis pipeline (109 DLLs, 15 libraries, subagent verification)
- `references/canvas-game-anticheat-patterns.md` — extended anti-cheat detection for other games

## Source

- Built from session 2026-07-06: Grey Hack reconnaissance under Steam + Flatpak + Wayland
- All techniques proven via real terminal execution on Basti's Zorin OS 18.1 workstation