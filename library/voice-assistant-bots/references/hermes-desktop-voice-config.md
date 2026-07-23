# Hermes Desktop Voice Config (TTS)

## Purpose

Configure and debug Hermes Desktop's Text-to-Speech (TTS) pipeline — making the agent speak back instead of only responding in plain text.

## Config Layout (in `~/.hermes/config.yaml`)

```yaml
voice:
  record_key: ctrl+b          # Push-to-talk hotkey
  max_recording_seconds: 180  # Max recording duration
  auto_tts: true              # ← Auto-generate audio for every response
  beep_enabled: true          # Start/stop beeps
  silence_threshold: 200      # For auto-stop
  silence_duration: 3         # Seconds of silence before auto-cut

tts:
  provider: <name>            # ← Active provider selector!
  use_gateway: true           # Route through gateway (usually needed)
  edge:
    voice: de-DE-KatjaNeural  # Free, good German voice
  openai:
    model: gpt-4o-mini-tts    # Premium, better quality
    voice: alloy
  elevenlabs:
    voice_id: pNInz6obpgDQGcFmaJgB
  minimax:
    voice_id: German_SweetLady
  # … more providers
```

## Critical Pattern: `auto_tts: true` Does NOT Guarantee Audio Output

Setting `voice.auto_tts: true` tells Hermes "generate audio for each response" — but **it only works if `tts.provider` actually works**. Common failure mode:

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `auto_tts: true`, but only plain text output | TTS provider is misconfigured or fails silently | Switch `tts.provider` to a tested backend |
| Audio cache empty (`~/.hermes/audio_cache/` = 4K) | No TTS call ever succeeded | Verify with `text_to_speech` tool directly |
| Stt works, no TTS output | Provider can't authenticate or model not found | Check provider's API key in `.env` |
| Gateway routes fine, no auto-play | Gateway audio delivery not configured | Set `tts.use_gateway: true` |

## Quick Diagnostic

```bash
# 1. Check audio cache — empty? TTS never ran
du -sh ~/.hermes/audio_cache/
ls ~/.hermes/audio_cache/

# 2. Which TTS provider is active?
grep -A1 '^tts:' ~/.hermes/config.yaml | head -3

# 3. Is auto_tts on?
grep 'auto_tts' ~/.hermes/config.yaml

# 4. Switch to a known-working provider (Edge TTS — free, no API key)
# Edit config.yaml: change tts.provider from minimax (or whatever) to "edge"
```

## Provider Selection Matrix

| Provider | Cost | Audio Quality | German | Set-up | Notes |
|----------|------|---------------|--------|--------|-------|
| `edge` (Edge-TTS) | Free | Good (KatjaNeural) | ✅ de-DE-KatjaNeural | None | Works immediately, no API key; Microsoft cloud service |
| `openai` | Paid | Excellent (alloy, nova, etc.) | ✅ via gpt-4o-mini-tts | API key in `.env` | gpt-4o-mini-tts cheapest TTS model |
| `elevenlabs` | Paid | Best-in-class | ✅ multilingual | API key | High quality, ~$5/mo for hobby |
| `minimax` | Paid (credits) | Good (German_SweetLady) | ✅ | API key + tokens | MiniMax M3 credits. May fail silently if API key missing or misrouted |
| `neuphonic/neutts` | Local | Good (GGUF quantized) | ✅ | ~2 GB download | Fully offline, local inference |
| `piper` | Local | Okay (TTS) | ✅ de-DE-KatjaNeural | ~80 MB model | Fastest, no GPU needed |

## Most Likely Failure Mode (This Session's Discovery)

```yaml
# CONFIG SHOWN (broken):
tts:
  provider: minimax          # ← Problem
  minimax:
    voice_id: German_SweetLady
voice:
  auto_tts: true
```

**Why it fails:** MiniMax TTS needs a `MINIMAX_API_KEY` in `.env` AND working credits. Without those, `text_to_speech` may silently fall back to nothing.

**Fix:** Switch to Edge TTS (free, no key):
```yaml
tts:
  provider: edge
  edge:
    voice: de-DE-KatjaNeural
voice:
  auto_tts: true
```

After change, restart Hermes Desktop:
```bash
systemctl --user stop hermes-gateway.service && sleep 3 && systemctl --user start hermes-gateway.service
```

## Manual TTS Test (Read-Only, No Config Change)

Use the `text_to_speech` tool directly in any session. Example:
```
Ich rufe text_to_speech(text="Achtung, Yuno Smoke-Test Eins, Voice-Pipe aktiv.")
```

Then check:
- `ls ~/.hermes/audio_cache/` → MP3 file appeared
- File size > 1 KB = call succeeded
- If the file exists but you hear nothing → check audio sink / speaker output (not TTS config)

## Auto-TTS vs Voice-Reply Plugin

| Approach | What it does | Pro | Con |
|----------|-------------|-----|-----|
| **`auto_tts: true`** | Hermes generates TTS audio on every reply, auto-saves to cache | Zero effort, built-in | No guarantee of auto-play; depends on Gateway audio delivery |
| **Voice-Reply Plugin** | Custom `voice_reply.py` that intercepts agent output and streams to audio sink | Full control: choose provider, add toggle, add hotkey | Requires writing + maintaining a plugin |
| **External Script** | `bash ~/.hermes/scripts/voice_reply.sh` after each response | Easy to implement, no config changes | Manual trigger, not automatic |

Recommended stack: set `tts.provider: edge` with `auto_tts: true` first. If auto-playback still doesn't happen, build a thin voice-reply plugin that calls `text_to_speech` explicitly and pipes the result to `paplay`.

## Pitfalls

### ⚠️ `tts.provider` selects the *active* provider, `voice.auto_tts` toggles *auto-generation*

These are independent. `auto_tts: true` without a working provider → silence.

### ⚠️ Restart Required

TTS config changes in `config.yaml` require a Hermes Gateway restart:
```bash
systemctl --user stop hermes-gateway.service && sleep 3 && systemctl --user start hermes-gateway.service
```

Simply closing/reopening the Hermes Desktop app may not reload `config.yaml`.

### ⚠️ Audio Cache Location

```bash
ls ~/.hermes/audio_cache/
# If empty after a TTS call: call failed. Check provider config.
# If files exist but no sound: speaker/auth path issue, not TTS.
```

### ⚠️ Provider Fallback Not Automatic

If the active TTS provider fails, Hermes does NOT fall back to another provider. It simply produces no audio. Configure only one provider at a time and test before switching.

### ⚠️ .env Secrets

Some providers (OpenAI, ElevenLabs, MiniMax) require API keys in `~/.hermes/.env`. Without them, the provider fails in the background — no error is surfaced to the user.
