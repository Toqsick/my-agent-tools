# edge-tts voice catalog — extended notes

Captured 2026-07-09 from edge-tts 7.2.7 on Basti's Zorin OS 18.1.

## German voices — full list

The full Microsoft German catalog is larger than the reliable subset above. Tested working on Basti's box:

- `de-DE-ConradNeural` — male, default pitch-rate. **Most reliable, always works.**
- `de-DE-KatjaNeural` — female, default. **Reliable.**
- `de-DE-KlausNeural` — male, younger. **Currently failing with NoAudioReceived on Basti's edge endpoint** (since at least 2026-07-09). Retry later.
- `de-DE-RalfNeural` — male, middle-aged. **Untested.** Likely works since it's in the same Azure region as Conrad.

Other voices in the catalog not yet validated here:
- `de-DE-AmalaNeural` (female)
- `de-DE-ElkeNeural` (female)
- `de-DE-GiselaNeural` (female)
- `de-DE-JonasNeural` (male)
- `de-DE-KillianNeural` (male)
- `de-DE-LouisaNeural` (female)
- `de-DE-MajaNeural` (female)
- `de-DE-TanjaNeural` (female)

When user requests a specific named voice, try it once. If it fails, fall back to the catalog of confirmed-working voices.

## Other useful locales

- English: `en-US-GuyNeural`, `en-US-JennyNeural`, `en-GB-RyanNeural`, `en-GB-SoniaNeural`
- French: `fr-FR-DeniseNeural`, `fr-FR-HenriNeural`
- The CLI lists every voice with `edge-tts --list-voices` — output is huge, grep for the locale.

## Why voices can return NoAudioReceived

Microsoft's edge-tts endpoint is rate-limited per-IP and can throttle specific voices during peak hours. Symptoms:

1. First call after a long gap returns `NoAudioReceived` immediately
2. Subsequent calls with the same voice succeed once it "warms up"
3. After ~50 short calls in quick succession the endpoint throttles

Mitigation: spacing between calls (5+ seconds), preferring Conrad because it's on the most-used shard.

## CLI argument pitfalls (verified)

```
# Works:
--rate=-5%
--pitch=+2Hz
--volume=+0%

# Fails with "expected one argument":
--rate "-5%"
--pitch "+2Hz"

# Returns NoAudioReceived silently (output is empty file):
--rate=-30% --pitch=+10Hz   # both extreme
--text "..." with smart quotes " "

# Works but might sound wrong:
--text with German umlauts as direct UTF-8 (default)
--text with umlauts spelled out ("ae" instead of "ä") — more reliable for older voices
```

## When to consider alternatives

- **Need emotional control / SSML prosody tags** → switch to Azure Speech (paid) or piper-tts (local, trained voices)
- **Need offline / no network** → piper-tts with a German ONNX model
- **Need to clone a specific voice** → Coqui XTTS, OpenVoice, or ElevenLabs
- **Need music** → not TTS; use Suno/HeartMuLa
