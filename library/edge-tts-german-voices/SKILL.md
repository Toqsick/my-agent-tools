---

name: edge-tts-german-voices
description: "Use when user asks for German TTS, edge-tts synthesis, Microsoft edge voice catalog for German, German audio narration. NOT for non-German languages or non-edge TTS engines. Use Microsoft edge-tts CLI to synthesize German speech audio."
category: media
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['german', 'edge', 'microsoft', 'audio', 'user']
keywords: ['german', 'edge', 'microsoft', 'audio', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['audio-instructions', 'voice-clone']
---
# edge-tts for German audio

Use the system `edge-tts` CLI (located in `~/.hermes/hermes-agent/venv/bin/edge-tts`) to synthesize German speech without API keys. No Microsoft account or auth needed — uses Edge's free public TTS endpoint.

## When to use

- Quick German voice-overs / greetings (`mach mir eine audio datei`)
- Audiobook chapter recording drafts
- Voice-memo style explanations
- Any short-to-medium German narration that doesn't need custom-trained voice or emotional control

For SSML / prosody tags, voice cloning, or offline TTS → switch tools. edge-tts is plain-text only.

## Canonical command shape (Bash-safe)

```bash
/home/bratan/.hermes/hermes-agent/venv/bin/edge-tts \
  --voice de-DE-<Voice> \
  --rate=-5% \
  --pitch=+0Hz \
  --text "German text without shell-unsafe chars" \
  --write-media out.mp3
```

**Critical quoting rules:**
- Flag values use `--name=value` form, **never** `--name "value"`. The latter parses as empty argument and returns `expected one argument`.
- `--rate` format: `+0%` / `-5%` / `+10%` (range roughly -50%..+100%).
- `--pitch` format: `+0Hz` / `+2Hz` / `-3Hz` (range -50Hz..+50Hz, but keep small for naturalness).
- **Avoid combining aggressive rate and pitch shifts** (e.g. `--rate=-15% --pitch=+5Hz`) — produces `NoAudioReceived` errors silently. If the first call fails, halve the values and retry before assuming the voice is broken.
- Text must have no smart-quotes, no em-dashes from copy-paste, no HTML entities. Edge-TTS rejects some unicode punctuation. If the first call returns `NoAudioReceived`, strip the text to ASCII-safe substitutes and retry.

## Reliable German voice catalog

Only these are confirmed-working on Basti's box (2026-07-09). Try in this order; if the requested gender/tone is not listed, **state the limitation and offer the closest match** — don't waste three retries on a known-offline voice.

| Voice | Gender | Tone | Default rate/pitch for "friendly" | Notes |
|---|---|---|---|---|
| `de-DE-ConradNeural` | male | reif, sachlich, leicht neutral | `--rate=-8% --pitch=+3Hz` | **Most reliable male voice.** Pitch up + slower rate turns him noticeably warmer. |
| `de-DE-KatjaNeural` | female | freundlich, hell | `--rate=-5% --pitch=+0Hz` | Reliable female default. |
| `de-DE-KlausNeural` | male | jünger, enthusiastisch | (offline 2026-07-09) | **Returns `NoAudioReceived` consistently right now.** Skip unless endpoint recovers. |
| `de-DE-RalfNeural` | male | ruhig, mittel-alt | untested | Available in catalog but not yet verified on this box. |

If the user asks for a "younger / friendlier / enthusiastic" male and Klaus is down → deliver Conrad with the warm-up tuning and explain.

## Failure modes and recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| `edge-tts: error: argument --rate: expected one argument` | `--rate "-5%"` (space + quoted) → parsed as empty | Use `--rate=-5%` (equals sign, no space, no quotes) |
| `NoAudioReceived: No audio was received` | (a) Unicode in text, (b) extreme rate/pitch combo, (c) that voice is rate-limited / offline | Try in this order: (1) strip smart-quotes / em-dashes; (2) halve rate/pitch; (3) fall back to a different voice from the catalog |
| Output MP3 is 0 bytes | TTS API call failed mid-stream (network blip or voice unavailable) | Delete the empty file (`rm 0bytes.mp3`), retry once with same args, then fall back voice |
| MP3 plays but sounds mispronounced | G2P engine doesn't know the word | Try Umlaut-Remove variant ("Gude" stays, "Schoen" instead of "Schön") or accept the artifact |

After any failure, **always delete the 0-byte output file** before retrying, otherwise the next call silently returns success-without-data on top of it.

## Verification (don't skip)

```bash
ffprobe -v error -show_entries format=duration:stream=channels,sample_rate,codec_name \
  -of default=noprint_wrappers=1 out.mp3
```

Expect: `codec_name=mp3`, `sample_rate=24000`, `channels=1`, `duration` matches text length × ~0.07s/char for normal rate. Anything else → suspect parameter error.

## Voice selection cheat sheet for common user phrasing

User says → Voice + tuning
- "deutsche männliche Stimme" → Conrad, `--rate=-8% --pitch=+3Hz` (warm) or default (neutral)
- "freundlich" → +3Hz pitch and slight rate-down on any voice
- "ruhig / sachlich" → default rate/pitch on Conrad
- "weibliche Stimme" → Katja
- "Gude / hessisch-Akzent" → none of the voices have a regional accent; pitch-up + slow gives "warmer" impression, that's the most you get without SSML

## References

- `references/voice-catalog.md` — extended voice catalog (English, French, etc.) and per-voice punctuation/character quirks
