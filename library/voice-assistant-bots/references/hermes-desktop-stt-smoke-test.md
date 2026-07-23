# Hermes Desktop STT Smoke Test

## Purpose

Verify that Hermes Desktop's local Whisper STT pipeline works end-to-end: microphone capture → WAV file → Whisper transcription → text output. This is a **local, offline** test — no cloud API needed.

## Prerequisites

- Hermes Desktop app running
- `faster-whisper` (recommended, ~1.2GB) OR `openai-whisper` (fallback) in Hermes venv
  - Verify: `~/.hermes/hermes-agent/venv/bin/python -c "from faster_whisper import WhisperModel; print('faster-whisper OK')"`
  - Fallback: `~/.hermes/hermes-agent/venv/bin/python -c "import whisper; print(whisper.__version__)"`
- Working microphone (list devices: `pactl list short sources | grep input` or `arecord -l`)
- `arecord` available (`sudo apt install alsa-utils` if missing)

## Venv & pip Setup (PEP 668)

Hermes Agent's venv lives at `~/.hermes/hermes-agent/venv/` — **no dot prefix** (not `.venv`).

**If pip is missing from the venv** (e.g. `ModuleNotFoundError: No module named 'pip'`):

```bash
~/.hermes/hermes-agent/venv/bin/python -m ensurepip --upgrade
```

This installs pip 24.x inside the venv without touching the system Python (PEP 668 compliant).

## 1. Device Enumeration (pre-flight)

**Don't guess the `-D` parameter — measure:**

```bash
# PulseAudio sources (human-readable)
pactl list short sources | grep input

# ALSA hardware list (numerical)
arecord -l

# PulseAudio source level (mute/volume)
pactl get-source-volume @DEFAULT_SOURCE@
pactl get-source-mute @DEFAULT_SOURCE@

# If muted:
pactl set-source-mute @DEFAULT_SOURCE@ 0
# Microphone volume to 100%:
pactl set-source-volume @DEFAULT_SOURCE@ 65536
```

**Expected for SteelSeries Arctis 7:**
- `arecord -l` → Card 1 (USB Audio), Device 0
- ALSA device string: `plughw:1,0`
- PulseAudio source: `alsa_input.usb-SteelSeries_SteelSeries_Arctis_7-00.mono-chat`

## 2. Model Selection Guide

| Model | Backend | Size | RAM | Speed | German Accuracy | Use Case |
|-------|---------|------|-----|-------|-----------------|----------|
| `base` | vanilla whisper | 142 MB | ~1 GB | ~1× realtime | 70–80% | Quick first test |
| `medium` | vanilla whisper | 740 MB | ~2 GB | ~0.5× realtime | 85–90% | Better DE, lower RAM |
| `large-v3` | vanilla whisper | 2.8 GB | ~6 GB | ~0.3× realtime | 92–95% | Best but RAM-heavy |
| `large-v3` | **faster-whisper** (CTranslate2 INT8) | 1.5 GB | ~2 GB | **5–10× realtime** | **95+%** | ✅ **RECOMMENDED** |

The upgrade from `whisper base` → `faster-whisper large-v3` on this system (i7-13620H, 15 GB RAM) delivered:
- **5–10× faster inference** (CTranslate2 INT8 quantization)
- **~2 GB RAM** instead of ~6 GB for vanilla large-v3
- **No English drift** on short German phrases (language="de" enforced)
- No GPU needed — runs on CPU with int8 compute

## 3. Run the smoke test

Use the script at `scripts/voice-stt-smoke.sh` (relative to this skill directory)
or copy it to `~/.hermes/scripts/voice-stt-smoke.sh`.

```bash
bash ~/.hermes/scripts/voice-stt-smoke.sh
```

Interactive prompt waits for ENTER before starting the 3-second capture.

The script uses **three-stage architecture**:
1. **Stage 1** — 3-second audio capture via `arecord`
2. **Stage 1.5** — Pre-Load larger model into RAM (skips Stage 2 cold start)
3. **Stage 2** — Transcribe: `faster_whisper` primary → `vanilla whisper` fallback
4. **Stage 3** — Cleanup temp WAV

## 4. Interpret Results

| Signal | What it means |
|---|---|
| `WAV: 96044 Bytes` | Audio captured successfully (96 KB ≈ 3 sec PCM) |
| `Pre-Load: ✓ large-v3 ready (CTranslate2 INT8)` | Model warmed up (cold start bypassed) |
| `✓ Transkription abgeschlossen (de, Wahrscheinlichkeit 0.XX)` | German language detected, high confidence |
| `→ FINAL: 'Hallo Welt'` | ✅ **TRANSCRIPTION SUCCESS** — full pipe certified |
| `→ FINAL: ''` (empty) | Microphone received silence. Check mute + volume (see above) |
| `Non-zero exit` | Check `LOG` file for Python/CTranslate2 stacktrace |
| `Fallback: vanilla whisper 'base'` | `faster-whisper` not installed → imports vanilla |
| `ModuleNotFoundError: whisper` | Venv path wrong → `ls ~/.hermes/hermes-agent/` to check |

### ⚠️ Venv Detection BEFORE Stage 1.5 (set -u Pitfall)

If the script uses `set -u` (as part of `set -euo pipefail`), a common error occurs:
```
script.sh: line 38: HERMES_PY: unbound variable
```

**Root cause:** The `HERMES_VENV`/`HERMES_PY` variables are defined later in the script (e.g., in Stage 2), but `set -u` causes an immediate exit when the variable is referenced earlier (e.g., in Stage 1.5 Pre-Load).

**Fix:** Define `HERMES_VENV` and `HERMES_PY` at the **top of the script**, before any stage that uses them. Always quote the variable:

```bash
HERMES_VENV=~/.hermes/hermes-agent/venv
HERMES_PY="$HERMES_VENV/bin/python"
if [ ! -x "$HERMES_PY" ]; then
    HERMES_PY="$(command -v python3)"
fi
```

Then use consistently throughout:
```bash
"$HERMES_PY" - <<'PYEOF'    # ← quotes required for set -u
# ...
PYEOF
```

**Never** defer the definition to after the first reference, even if the first reference is in a "pre-load" stage.

## 5. Pitfalls

### ⚠️ Venv Path: `venv`, not `.venv`

Hermes Agent installs its Python venv at `~/.hermes/hermes-agent/venv/` — **no dot before `venv`**.
Most common error: scripts reference `~/.hermes/hermes-agent/.venv/bin/python` (doesn't exist).

**Diagnosis:**
```bash
ls ~/.hermes/hermes-agent/
# → Do you see 'venv/' or '.venv/'?

# Test faster-whisper import
~/.hermes/hermes-agent/venv/bin/python -c "from faster_whisper import WhisperModel; print('OK')"

# Test fallback
~/.hermes/hermes-agent/venv/bin/python -c "import whisper; print(whisper.__version__)"
```

**Robust venv detection (for scripts):**
```bash
HERMES_VENV=~/.hermes/hermes-agent/venv
HERMES_PY="$HERMES_VENV/bin/python"
[ -x "$HERMES_PY" ] || HERMES_PY="$(command -v python3)"
```

### ⚠️ Missing pip in venv (PEP 668)

The Hermes venv may not have pip installed. Fix without touching system Python:

```bash
~/.hermes/hermes-agent/venv/bin/python -m ensurepip --upgrade
```

### ⚠️ Cold Start (first run)

- **faster-whisper large-v3**: ~1.5 GB download + ~30 seconds load time on first run
- **faster-whisper** caches in `~/.cache/huggingface/hub/`
- **vanilla whisper base**: ~140 MB, ~30–90 seconds first download
- Vanilla whisper caches in `~/.cache/whisper/`

Both models remain cached after first load — subsequent runs are 1–5 seconds.

### ⚠️ Trigger Timing

The script does **3 seconds audio capture**. If the user doesn't speak during those 3 seconds, the transcript is empty.

**Fix:** `read -p "ENTER …"` before `arecord` ensures the user is ready.

### ⚠️ Volume too low

Despite ENTER trigger and 96 KB WAV, the transcript may be empty if speech is too quiet.
→ `pactl set-source-volume @DEFAULT_SOURCE@ 65536` (100%)

### ⚠️ Ensure `faster-whisper` Is Installed

The script falls back to vanilla whisper if `faster_whisper` fails to import. To install:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install --upgrade faster-whisper
```

(Requires pip in venv first — see section 5, 'Missing pip in venv'.)

## 6. Known-good device configuration

| Property | Value |
|---|---|
| Audio device | SteelSeries Arctis 7 (Card 1, USB Audio) |
| Input source | `alsa_input.usb-SteelSeries_SteelSeries_Arctis_7-00.mono-chat` |
| ALSA device | `plughw:1,0` |
| Format | S16_LE, 16 kHz mono |
| Primary model | `faster-whisper large-v3` (CTranslate2, int8, cpu, language=de) |
| Fallback model | `vanilla whisper base` (fp16=False, language=de) |
| Script path | `~/.hermes/scripts/voice-stt-smoke.sh` |
| Hotkey | Strg+B in Hermes Desktop |
| Venv | `~/.hermes/hermes-agent/venv/` (no dot) |
| Pip (if missing) | `$VENV/bin/python -m ensurepip --upgrade` |
