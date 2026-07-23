# Hermes Troubleshooting — Deep Dives

## Voice not working
1. Check `stt.enabled: true`
2. Install deps: `uv pip install --python ~/.hermes/hermes-agent/venv/bin/python pyaudio SpeechRecognition openai-whisper`
3. Check mic: `arecord -l`
4. `/restart` gateway, restart Hermes Desktop

## Tool not available
1. `hermes tools` — check enabled
2. `/reset` after enabling

## Model/provider issues
1. `hermes doctor` → `hermes auth` → check `.env`

## Gateway crash loop
```bash
systemctl --user reset-failed hermes-gateway
```

## Changes not taking effect
- Tools/skills: `/reset` · Config: gateway restart · Code: restart process

## Skill Loader Ambiguity Bug
Use fully-qualified path: `skill_view(name='devops/hermes-admin')`. Fix: clean up `.curator_backups/`.

## Common Gateway Pitfalls
0. No `hermes telegram status` — use `hermes status` or `hermes gateway status`.
1. `config.yaml` is PRIMARY — `.env` secondary.
2. Multiple gateways collide on same token.
3. `hermes gateway restart` blocked in agent sessions — use `systemctl --user`.
4. `.env` protected from `patch()`.
5. `.curator_backups` causes ambiguous skill errors.
6. `.env` can override `config.yaml` for Telegram — check BOTH files.
7. `systemctl --user` auto-approved in 2026-06+ (may block in safe-mode).
