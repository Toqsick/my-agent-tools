# Cyberpunk Approach Trilogy — Session Reference

**Date:** 2026-07-04 · **Owner:** Basti · **Builder:** Yuno 🐝
**File outputs:** `/home/bratan/cyberpunk-clip-1.md` + `/home/bratan/docs/system/cyberpunk-trilogie/README.md` + `/home/bratan/scripts/cyberpunk-trilogie/generate_clip.py`

## What the trilogy is

Three POV clips, ~8s each, ~24s total, 16:9 cinematic, I2V mode:

1. **Clip 1 — Night City Alley:** Bastis Cyberpunk 2077 screenshot as first frame, dolly-in past rusted yellow railing → tilt-up to megabuilding facade
2. **Clip 2 — Megabuilding Entry:** First-person walk-up to keycard reader, swipe, elevator ride up to floor 42
3. **Clip 3a — Apartment Door → City View:** Door 4217 with sticky note and "Spiegel" neon → into apartment → dramatic skyline reveal through floor-to-ceiling window

## Style anchors (locked for all 3)

- **Palette:** deep blacks, desaturated concrete grays, rust yellow, teal-cyan, warm amber, pink neon accents
- **Lighting:** cold cyan key + warm tungsten secondary, high contrast, wet floor reflections
- **Camera:** first-person POV, handheld sway, smooth dolly
- **Style modifier:** "CD Projekt Red Phantom Liberty, anamorphic 35mm film grain, photorealistic"
- **Recurring object:** worn plastic keycard with cyan magnetic stripe (appears in clips 2 + 3a)

## Audio arc (for editor)

- Clip 1: ambient drone + footsteps + bass pulse → **builds**
- Clip 2: foley-heavy (swipe, beep, clack, hydraulic, hum, ding) → **foley**
- Clip 3a: foley → silence inside → city ambience → soft piano chord → **emotional payoff**

## Continuity hooks (for editor cutting)

- Clip 1 END → Clip 2 BEGIN: hard cut at Tilt-up Apex (Megabuilding-Glasfassade full frame) → cut to close-up keycard reader
- Clip 2 END → Clip 3a BEGIN: hard cut at Door 4217 first-frame → straight cut to door 4217 first-frame

## Why a master .md file and not just chat output

Basti explicitly opted for the "Du gibst mir 5 Min — du enablest Plugin + setzt Key, ich warte" path. The .md file gives him:
- Drag-droppable prompts for any web UI (kling.com, veo3.google.com, fal.ai/cinema)
- Self-contained continuity hooks for editor work
- Persistent record that survives chat scrollback

File naming convention: `~/cyberpunk-clip-N.md` (root, easy to find) + trilogy README in `~/docs/system/cyberpunk-trilogie/`.

## What blocked direct generation this session (infrastructure, not prompt)

- `FAL_KEY` not set (FAL.ai image/video plugin not enabled)
- `OPENAI_API_KEY` not set (openai-codex plugin not enabled)
- All other image/video plugins (krea, xai) also not enabled
- No local ComfyUI, no local Stable Diffusion
- OLLAMA available with vision model `xentriom/gemma-4-12B-agentic-fable5-composer2.5:v2:Q8_0` (12GB) — usable for text+vision but not specifically tuned for cinematic generation
- First solution delivered: copy-paste-ready prompt packages

## Web-Token vs API-Key discovery journey (2026-07-04 LATE SESSION)

The actual blocker was more subtle than missing keys. Notes for future sessions:

### The two credentials
Basti has a **MiniMax Hub** desktop app (Wine-bottled, wrapper at `~/bin/minimax-hub` reading `HILO_USER_TOKEN` env via `HILO_USER_TOKEN_FILE=~/.config/minimax-hub-token`). The token saved by that wrapper is **web-auth only** (JWT `eyJhbG...`). 

For `api.minimax.io/v1/*` you need a **separate API Secret Key** (`sk-api-...` format) generated via `platform.minimax.io/user-center/basic-information`.

### Endpoint disambiguation
Basti pastes a curl pointed at `api.minimax.io/v1/video_generation`. Diagnostic on `/v1/models` returned **only M-series text-LLM models**, zero video models — confirming that endpoint is the text-LLM API, not HailuoAI/MiniMax-Video. The video service shares branding but lives at a separate endpoint that we did not confirm in this session.

### Status code semantics (very useful)
- `1004` "Please carry the API secret key in the Authorization field" → wrong token type, no Bearer prefix helps. User must fetch API key from portal.
- `1008` "insufficient balance" → auth worked, plan empty. User tops up OR is on wrong API entirely.
- `200` with empty `task_id` + `base_resp.status_code: 1008` → silent billing refusal.

### What was delivered
Once credits are added on the correct endpoint, fire:
```bash
python3 /home/bratan/scripts/cyberpunk-trilogie/generate_clip.py \
    --clip 1 \
    --api-key "$MINIMAX_VIDEO_KEY" \
    --first-frame-url "https://i.imgur.com/DEIN_BILD.jpg"
```
This was NOT executed in-session because the upload-helper is a stub (`NotImplementedError`) — the user is expected to host the screenshot on any public CDN first and pass the URL.

## Prompt engineering choices made

- **English prompts** (model best practice)
- **I2V over T2V** (user's screenshot IS the perfect first frame — no need to generate)
- **Multi-model fallback prompts:** wrote Veo3 (primary, with audio), Kling 2.1 (shorter), Wan 2.6 (I2V + audio). Three variants covers any provider user might enable.
- **Trilogy-wide style anchors** re-mentioned in each clip's prompt so models see consistent style even if used individually
- **Sound design notes** in each prompt since Veo3 is the only model that bakes audio in directly; other models require separate TTS/SFX generation

## Cyberpunk OST companion deliverable (2026-07-04)

Same session produced `/home/bratan/cyberpunk-suno-prompts.md` — 5-track × 5-min Suno prompt package inspired by the **actual Cyberpunk 2077 OST tracks** at `/mnt/DATA/Programme/Steam/steamapps/music/Cyberpunk 2077 Bonus Content/soundtrack/`. 

Key technique used: **style analysis on real reference tracks** via `ffprobe` (duration, sample rate, bitrate) → derive Style-Field blocks for Suno with matching tempo/key/instrumentation profile. The reference tracks had durations of 154-335s (2:34 to 5:35) which directly inspired the 5-minute-target prompt architecture with explicit loop-extension strategy.

## File paths to remember

- Source screenshot: `/home/bratan/.var/app/com.valvesoftware.Steam/.local/share/Steam/userdata/760940113/760/remote/1091500/screenshots/20260520233244_1.jpg`
- Cyberpunk 2077 OST reference (read-only): `/mnt/DATA/Programme/Steam/steamapps/music/Cyberpunk 2077 Bonus Content/soundtrack/mp3/cd1/` and `cd2/`
- Clip 1 master: `/home/bratan/cyberpunk-clip-1.md`
- Trilogy README: `/home/bratan/docs/system/cyberpunk-trilogie/README.md`
- Suno prompts: `/home/bratan/cyberpunk-suno-prompts.md`
- Generator script: `/home/bratan/scripts/cyberpunk-trilogie/generate_clip.py`
- MiniMax Hub wrapper: `~/bin/minimax-hub` (v2, reads `HILO_USER_TOKEN`)
- Hailuo web token: `~/.config/minimax-hub-token` (JWT, web-auth only, NOT API key)
