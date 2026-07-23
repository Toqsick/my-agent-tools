# GreyHack Manual Reading — Assisted Reconnaissance 2026-07-06

Session where we OCR-extracted the in-game **CodeEditor → Manual → GreyScript programming handbook** from Grey Hack, page by page, with the user driving navigation and the agent extracting content.

## Mission Context

- **Continuation of**: GreyHack 15-min reconnaissance (2026-07-06)
- **New technique**: **Assisted reconnaissance** — user clicks, agent reads
- **Target content**: GreyScript handbook (29 pages, German/English mixed)
- **Why this matters**: Step-handlers for the Reraldi-Mission need GreScript syntax knowledge. The in-game Manual is the **canonical** source (matches game V0.9.6771).

## Why Assisted Reconnaissance (vs. fully automated)

After 15-min full-access recon, we discovered:
- `cua-driver click` returns `effect: unverifiable` (XSendEvent rejected)
- `cua-driver type_text` returns `effect: unverifiable`
- xdotool clicks visually land but don't change game state
- The game has its own **Anti-Cheat / Anti-Bot** layer that detects XSendEvent input

For the Manual-Reading session specifically:
- The user is **already in front of the screen** and can manually click sub-pages
- The agent can take a screenshot, run OCR, and extract the content
- This is **massively more efficient** than spending hours figuring out how to bypass anti-cheat just to read a manual

## The Assisted-Reconnaissance Pattern

```
User: opens Manual tab
   ↓
User: clicks sub-page (e.g. "Libraries & Exploits")
   ↓
Agent: cua-driver get_window_state → screenshot
   ↓
Agent: Tesseract OCR with --psm 6 --tsv → text + coordinates
   ↓
Agent: parses, cleans, formats
   ↓
Agent: writes structured .md to vault (e.g. 09 System-Doku/GreyHack/)
   ↓
   repeat for next sub-page
```

## Worked Example — Libraries & Exploits (page)

### User: clicks "Libraries & Exploits" in CodeEditor → Manual

### Agent: Screenshot via cua-driver

```bash
DISPLAY=:1 \
XAUTHORITY=/run/user/1000/.mutter-Xwaylandauth.$(ls -t /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1 | grep -oP '[A-Z0-9]+$') \
cua-driver call get_window_state '{
  "pid": 4563,
  "window_id": 12582985,
  "include_screenshot": true
}'
```

### Agent: Save PNG and OCR with German language pack

```bash
# Save the base64 PNG to a file
python3 -c "
import json, base64, sys
data = json.load(sys.stdin)
with open('/tmp/gh_manual.png', 'wb') as f:
    f.write(base64.b64decode(data['screenshot_png_b64']))
" < /tmp/gh_response.json

# OCR — KEY INSIGHT: -l eng+deu + --psm 6
tesseract /tmp/gh_manual.png stdout -l eng+deu --psm 6
# → 1048 characters, 33 lines (vs 455 chars with --psm 4)
```

### Agent: Extract structured content from OCR

The raw OCR text is **noisy** — it includes:
- The page's narrative content (what we want)
- Surrounding chrome (status bar, taskbar, file metadata)
- Frequently **garbled JSON-like syntax** when the page has code samples

**Extraction strategy**: Manually identify content boundaries and re-format into a clean vault note:

```yaml
---
tags: [greyhack, manual, libraries, exploits, reconnaissance, 2026-07-06]
importance: 9
quelle: Grey Hack Manual (In-Game)
seite: Libraries & Exploits
datum: 2026-07-06 17:29
---

# 📘 Grey Hack Manual: Libraries & Exploits

> **Quelle**: In-Game Manual (CodeEditor/Manual-App)
> **OCR-Extrahierung**: Tesseract 5.3.4 via cua-driver screenshot

## Hauptkonzept
[extracted content]
```

## Key Findings From the Manual

The **Libraries & Exploits** chapter explained:

1. **Schwachstellen in Bibliotheken**: SSH-Server hat `libssh.so` installiert → kann Sicherheitslücken enthalten
2. **Exploit-Klassen**:
   - **Remote-Exploits**: ssh, ftp, smtp, sql (offene Services)
   - **Lokale Exploits**: init.so, kernel_module.so, net.so (Privilege-Escalation)
3. **Zero-Day-Exploits**: Periodische Gerüchte (alle 2 Monate Spiel-Zeit) → Investigation → IP → Debug-Library → unit_testing → metalib.payload
4. **Tipp aus dem Manual**: "Sparen Sie sich etwas Geld und mieten Sie einen Server für Tests — ohne Behörden-Alarm"

## Step-Handler Building Blocks (extracted for Mission-Implementation)

| Mission-Step | Manual-Info | Code-Target |
|---|---|---|
| Portscan | "Welche Services sind offen?" | `portscan.src` |
| SMTP-Enum | `smtp` ist Remote-Exploit-Target | `smtp_enum.src` |
| Brute-Force | suid_exploit database | `suid_exploit.src` |
| Cleanup | "Spuren vermeiden" (next chapter) | `avoid_traces.src` |

## Discovered OCR Optimization

For **Grey Hack manual pages** (mixed text + code + JSON-garble):

| Tesseract config | Output length | Quality |
|---|---|---|
| `-l eng --psm 4` (column) | 455 chars | Misses most content |
| `-l eng --psm 6` (block) | 1048 chars | **Best for this UI** |
| `-l eng+deu --psm 6` | 1048+ chars | **Recommended** (German UI text) |
| `-l eng --psm 6 tsv` | 1048 chars + coords | For element-mapping |

**Key insight**: `psm 6` (uniform block of text) survives structural noise that breaks `psm 4` (column-detection). The Grey Hack Manual has many code blocks that look like vertical lists to `psm 4`, causing it to mis-segment the text.

## Pitfalls Encountered

1. **Empty OCR with default `--psm 3`**: Tesseract failed completely with auto page-segmentation on the first manual page. Switching to `--psm 6` immediately fixed it.

2. **Mixed German/English UI text**: Grey Hack has German UI strings (e.g. "Hilfe", "Spuren vermeiden") but the game logic is English. Using `-l eng` alone produced 30-40% garbled German text. `-l eng+deu` reduced garble to <5%.

3. **JSON-garble in code blocks**: Pages with code samples (e.g. the Zero-Day-Exploit page) show curly-brace-enclosed text that Tesseract reads as a single column. This is acceptable — we extract narrative content and skip the code (we have our own `greyhack-tools` repository with canonical code).

4. **Sub-window WID changes between sessions**: The WID 12582935 from the first recon session became 12582985 in the manual-reading session. Always re-discover with `xdotool search --name "Grey Hack"` at session start — don't hardcode WIDs.

## Step-Handler Recipe (extracted for Orchestrator-Skill)

```python
# In orchestrator.py, add a new handler for "manual" steps:
def _action_manual_page(self, step_description: str) -> None:
    """Capture and OCR a Grey Hack Manual page the user opened."""
    # 1. Screenshot
    png_path = self._capture_greyhack_window()
    # 2. OCR
    ocr_text = subprocess.run(
        ["tesseract", png_path, "-", "-l", "eng+deu", "--psm", "6"],
        capture_output=True, text=True
    ).stdout
    # 3. Save as vault note
    note = f"# Grey Hack Manual Page: {step_description}\n\n{ocr_text}\n"
    vault_path = VAULT / "05 Ressourcen/greyhack-manual-extract.md"
    vault_path.write_text(note)
```

## Files Created This Session

- `09 System-Doku/GreyHack/GreyHack-Manual-Libraries-und-Exploits.md` (5.5 KB) — extracted Libraries & Exploits chapter
- `99 Capture/gh_manual_20260706_140303.png` — primary screenshot
- Multiple follow-up screenshots from later manual sub-pages

## Siehe auch

- `desktop-window-reconnaissance` (parent skill)
- `references/greyhack-recon-2026-07-06.md` — 15-min full-access recon transcript
- `greyhack-mission-orchestrator` — the consumer of this extracted manual content
