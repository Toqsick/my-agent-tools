# TTS Provider Switch (verified 2026-07-02)

## Provider Config Reference

| Provider | config.yaml Pfad | Schlüssel-Feld | Beispiel |
|----------|-----------------|----------------|----------|
| `edge` (default) | `tts.edge.voice` | voice | `de-DE-KatjaNeural` |
| `minimax` | `tts.minimax.voice_id` | voice_id | `German_SweetLady` |
| `elevenlabs` | `tts.elevenlabs.voice_id` + `model_id` | beide | `pNInz6obpgDQGcFmaJgB` |
| `openai` | `tts.openai.voice` | voice | `alloy` |
| `gemini` | `tts.gemini.voice` | voice | `Kore` |
| `mistral` | `tts.mistral.voice_id` | voice_id | UUID |
| `xai` | `tts.xai.voice_id` + `language` | beide | `eve` + `de` |

## Workflow

```bash
hermes config set tts.provider minimax
hermes config set tts.minimax.voice_id German_SweetLady

# Verify
~/.hermes/hermes-agent/venv/bin/python3 -c "
from hermes_cli.config import load_config
cfg = load_config()
print(cfg['tts']['provider'], cfg['tts']['minimax']['voice_id'])"
```

## Voice-Discovery (Minimax)

```bash
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -d '{"voice_type":"system"}' https://api.minimax.io/v1/get_voice > /tmp/voices.json
```

## Pitfalls

- **`config.yaml` protected** — only `hermes config set` works.
- **Voice-ID ≠ Voice-Name** — Edge reads `voice`, Minimax reads `voice_id`.
- **Discovery endpoints vary:** Minimax = `POST /v1/get_voice`, ElevenLabs = `GET /v1/voices`.
- **Yuno-Bot-Skript mitziehen** — `apply_hermes_voice_config.sh` must be updated too.
