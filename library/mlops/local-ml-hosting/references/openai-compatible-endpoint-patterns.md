# OpenAI-Compatible Endpoint Pattern for Local LLMs

This reference captures the provider-neutral pattern used for custom bots/helpers that need to switch between cloud LLM APIs and local Ollama without changing application logic.

## Why this pattern

Many LLM providers expose an OpenAI-compatible endpoint:

```text
POST /v1/chat/completions
```

Ollama also exposes this shape locally:

```text
POST http://127.0.0.1:11434/v1/chat/completions
GET  http://127.0.0.1:11434/v1/api/tags
```

That means a small helper can support both:

- cloud provider, e.g. Nous/Hermes
- local Ollama
- future OpenAI-compatible providers

without provider-specific SDK dependencies.

## Recommended environment shape

```env
# Cloud default
NOUS_API_BASE_URL=https://api.nousresearch.com/v1
NOUS_MODEL=qwen/qwen3.6-35b-a3b
HERMES_API_KEY=...

# Local Ollama override
# NOUS_API_BASE_URL=http://127.0.0.1:11434/v1
# LOCAL_LLM_MODEL=deepseek-r1:8b
# HERMES_API_KEY can be empty for local Ollama
```

If you control the config, a more generic naming is even better:

```env
LLM_API_BASE_URL=https://api.nousresearch.com/v1
LLM_MODEL=qwen/qwen3.6-35b-a3b
LLM_API_KEY=...
LOCAL_LLM_MODEL=deepseek-r1:8b
```

## Implementation checklist

1. Read base URL, model, and API key from config/env.
2. Detect local Ollama by normalized endpoint:
   - `http://127.0.0.1:11434/v1`
   - `http://localhost:11434/v1`
3. If local Ollama is detected:
   - allow missing API key
   - omit `Authorization: Bearer ...` unless explicitly configured
   - use `LOCAL_LLM_MODEL` as the default model
4. If cloud provider is detected:
   - require API key
   - send `Authorization: Bearer <key>`
   - use cloud model name
5. Build the same payload for both backends:

```json
{
  "model": "deepseek-r1:8b",
  "messages": [
    {"role": "system", "content": "Du bist Yuno."},
    {"role": "user", "content": "Was geht?"}
  ],
  "temperature": 0.3,
  "stream": false
}
```

6. Parse `choices[0].message.content`.
7. Return structured results:

```json
{
  "ok": true,
  "answer": "...",
  "model": "deepseek-r1:8b",
  "usage": null
}
```

## Health check

For local Ollama:

```bash
curl -s http://127.0.0.1:11434/api/tags
```

Expected:

```json
{"models":[{"name":"deepseek-r1:8b",...}]}
```

For cloud providers, a health check without a valid API key is usually not meaningful; treat config presence as the preflight and let the first request prove runtime access.

## Pitfalls

### 1. Cloud model name used against Ollama

Bad:

```env
NOUS_API_BASE_URL=http://127.0.0.1:11434/v1
NOUS_MODEL=qwen/qwen3.6-35b-a3b
```

Ollama will likely return:

```text
model not found
```

Fix:

```env
NOUS_API_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=deepseek-r1:8b
```

### 2. Requiring API key for local Ollama

Bad:

```python
if not api_key:
    raise RuntimeError("API key missing")
```

Fix:

```python
local_ollama = endpoint.endswith(":11434/v1")
if not api_key and not local_ollama:
    raise RuntimeError("API key missing")
```

### 3. Sending Authorization header to Ollama

Ollama does not need an auth header. Prefer:

```python
headers = {"Content-Type": "application/json"}
if api_key:
    headers["Authorization"] = f"Bearer {api_key}"
```

### 4. Treating Hermes voice STT/TTS as the same thing as LLM

Hermes has built-in STT/TTS provider concepts, but a custom Discord voice bot still needs its own voice pipeline:

- LLM brain: Nous/Hermes or local Ollama
- STT: faster-whisper, Groq, OpenAI, etc.
- TTS: Edge TTS, NeuTTS, Google TTS, etc.
- Discord voice transport: discord.py voice client

Keep these layers separate so the LLM backend can change without rewriting the voice bot.
