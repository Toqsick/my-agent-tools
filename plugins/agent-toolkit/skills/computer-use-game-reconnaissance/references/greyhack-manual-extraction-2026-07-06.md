# Grey Hack Manual Extraction — Pattern 7 Session (2026-07-06)

> Companion to `greyhack-recon-2026-07-06.md`. Documents the **hybrid manual-extraction workflow** (Pattern 7) applied to Grey Hack V0.9.6771.

## Trigger Conditions

This session activated Pattern 7 because:

1. **Anti-cheat detected** (per Pattern 4): `effect: unverifiable` on all cua-driver click/type attempts
2. **Rich text content available**: 7 manual sections + 29-page GreyScript programming bible
3. **User signal**: "später ich klicke erstmal selber durch" → accepted manual driving
4. **Mnemosyne context-loader reminder** from user ("Verstanden — Mnemosyne-Kontext geladen! 👍") confirmed session-start ritual

## Sections Extracted (in order)

| # | Section | Bytes | Key Insight |
|---|---|---|---|
| 1 | Libraries & Exploits | 5574 | Remote vs Local vs Zero-Day; metalib.debug_tools workflow |
| 2 | First Steps | 4010 | airmon→iwlist→aireplay→aircrack WiFi hack chain |
| 3 | Savegame | 2127 | Auto-save in real-time for both single + multiplayer |
| 4 | Avoid Traces | 3268 | `/var/system.log` is THE critical cleanup target |
| 5 | Karma & Reputation | 3647 | Karma is profile stat, not morality; negative OK if balanced |
| 6 | Reverse Shell | 5430 | rshell-server + Social Engineering "Funny Game" + Abwehrtipps |
| 7 | Scripting Libraries | 4977 | 22+ GreyScript modules: Metaxploit (hacking), MetaMail (mail), etc. |

**Total: 29,033 bytes of structured vault knowledge** from ~30 minutes of user clicking + Yolo OCRing in parallel.

## Per-Page Execution Loop (as deployed)

```python
# 1. User clicks next manual page in-game (no Yolo input needed)
# 2. Yolo captures:
import subprocess, json, base64, time
from pathlib import Path

env = os.environ.copy()
env["DISPLAY"] = ":1"
env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"

result = subprocess.run(
    ["cua-driver", "call", "get_window_state", json.dumps({
        "pid": 4563, "window_id": 12582985, "include_screenshot": True
    })],
    capture_output=True, text=True, env=env, timeout=20
)
png = base64.b64decode(json.loads(result.stdout)["screenshot_png_b64"])

# 3. Save screenshot to vault 99 Capture/
timestamp = time.strftime("%Y%m%d_%H%M%S")
vault_screenshot = Path(f"/home/bratan/Dokumente/Obsidian Vault/99 Capture/gh_manual_{timestamp}.png")
vault_screenshot.write_bytes(png)

# 4. OCR with --psm 6 (game UI mode)
ocr = subprocess.run(
    ["tesseract", str(vault_screenshot), "-", "-l", "eng+deu", "--psm", "6"],
    capture_output=True, text=True, env=env, timeout=20
).stdout.strip()

# 5. Yolo writes vault note (template per Pattern 6):
#    - Frontmatter: tags, aliases, importance, quelle, seite, datum, author, reihenfolge, kritisch_fuer
#    - OCR content (cleaned, structured)
#    - Mission-Relevanz section (mapping content to Mission-Reraldi-IP-154 steps)
#    - Verbindet zu wiki-links (other manual sections + missions + MOCs)
# 6. Loop: user clicks next page
```

## Cross-Linking Strategy

Each extracted note has a **Verbindet zu** section linking to:

- **All other extracted manual sections** (First-Steps ↔ Savegame ↔ Avoid-Traces ↔ Libraries ↔ Karma ↔ Reverse-Shell ↔ Scripting)
- **Active mission** (`Mission-Reraldi-IP-154`) — which steps use which knowledge
- **Orchestrator skill** (`greyhack-mission-orchestrator`)
- **Reconnaissance report** (`GreyHack - Reconnaissance-Report-2026-07-06`)
- **MOC hub** (`MOC - Gaming-Performance`)

This creates a **dense knowledge subgraph** that the orchestrator can query when implementing mission steps.

## Mission-Relevanz Insights Discovered

| Manual Section | Mission-Reraldi-IP-154 Step |
|---|---|
| First Steps | Step 1 prerequisite (WiFi hack required for any network access) |
| Libraries & Exploits | Step 4 (Metaxploit + metalib.payload for Zero-Day) |
| MetaMail module | Step 3, 5 (SMTP enum + mailbox access) |
| Avoid Traces | Step 7 (`/var/system.log` cleanup) |
| Reverse Shell | Alternative to Step 2 if direct port-scan fails |
| Karma | Side-effect awareness (negative karma from hackshop missions) |

## Anti-Patterns Avoided (from this session)

- ❌ **Saving OCR only as text** — we kept PNG screenshots for human-verification
- ❌ **Single-PSM-mode OCR** — verified `psm 6` is best for canvas game UIs
- ❌ **Skipping Mission-Relevanz section** — kept it even for "obvious" sections like Savegame
- ❌ **Generic vault notes** — each note got its own Frontmatter + importance level
- ❌ **Forgetting to check game window status** — must screenshot fresh after user clicks

## When NOT to Use Pattern 7

- ❌ Game has AT-SPI elements (use Pattern 1+2+computer-use skill)
- ❌ Game accepts synthetic input (use full cua-driver click/type)
- ❌ User wants zero interaction (use API/terminal-based automation)
- ❌ Manual has < 3 pages (just OCR + ask, no pipeline needed)

## Performance Note

Pattern 7 is **slow but thorough** — ~3 minutes per manual section (user click + 5-second screenshot + 3-second OCR + 30-second note generation). For 29-page GreyScript bible, full extraction would take ~90 minutes. Use selective extraction (key sections first, expand as needed).
</parameter>