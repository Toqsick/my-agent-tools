# Offline-Fallback Strategy

Use Ollama as a transparent fallback for online providers (Nous, DeepSeek
Cloud) when the internet is down. The user's preference: keep Nous as
default, only switch to Ollama when offline.

## Why this is hard

Hermes has no built-in offline detection. The fallback mechanism only
fires AFTER a request fails (with retries), which means:
- Online requests still get retried 3x (slow)
- Connection errors are not the same as "we're offline" from the user's
  perspective
- A flaky connection can ping-pong between Nous and Ollama

## Strategy 1: Manual Switch

For occasional offline work, switch manually:

```bash
hermes chat --provider custom:ollama-local --model qwen3.5:9b
```

Or set permanently for the session:

```bash
hermes config set model.provider custom:ollama-local
hermes config set model.default deepseek-r1:8b
# Work offline
hermes config set model.provider nous  # Restore
hermes config set model.default deepseek/deepseek-v4-flash
```

## Strategy 2: Pre-flight Check Script

A wrapper that probes connectivity before launching Hermes:

```bash
#!/usr/bin/env bash
# ~/.local/bin/hermes-smart
set -euo pipefail

PROBE_URL="${OLLAMA_HEALTHCHECK:-https://api.nous.example/ping}"
TIMEOUT=3

if curl -sS --max-time "$TIMEOUT" "$PROBE_URL" >/dev/null 2>&1; then
    # Online: use default config
    exec hermes "$@"
else
    # Offline: prepend --provider override
    if ss -tlnp 2>/dev/null | grep -q ':11434'; then
        exec hermes --provider custom:ollama-local --model qwen3.5:9b "$@"
    else
        echo "ERROR: offline AND Ollama not running" >&2
        exit 1
    fi
fi
```

Drop-in replacement: alias `hermes` to `hermes-smart` in your shell rc.

## Strategy 3: Hermes Fallback Mechanism (Slow)

Configure a fallback chain so Hermes falls back to Ollama when Nous fails:

```yaml
fallback_providers:
  - provider: "custom:ollama-local"
    model: "qwen3.5:9b"
    base_url: "http://127.0.0.1:11434/v1"

agent:
  api_max_retries: 1   # Schnelles Failover: 1 Retry, dann Fallback
```

**Drawback:** Still tries Nous first (3-10s wasted). Only kicks in after
explicit failures.

## Strategy 4: systemd Watchdog (Advanced)

Use a systemd path unit to detect when network is down and flip config
automatically. Requires custom script logic — not covered here.

## Diagnostic Checks

**Ollama läuft wirklich?**

```bash
systemctl --user status ollama --no-pager | head -3   # Service
ss -tlnp | grep 11434                                  # Port
ls -la ~/.local/bin/ollama 2>/dev/null                 # Binary
```

**Wichtig:** `ollama ps` zeigt nur *geladene Modelle* — ein leerer Output
bedeutet **nicht**, dass Ollama beendet ist. Der systemd-Service kann
weiterlaufen ohne geladenes Modell.

**Quick connectivity probe:**

```bash
curl -sS --max-time 3 https://api.nous.example/v1/models -o /dev/null -w "%{http_code}\n"
# 200/401 = online, 000/timeout = offline
```

**End-to-End Ollama Test:**

```bash
timeout 30 curl -sS http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:8b",
  "prompt": "Antworte in einem Wort: Hi",
  "stream": false
}' | python3 -c "import json,sys; r=json.load(sys.stdin); print(r.get('response','NO RESPONSE')[:50])"
```

## Recommendation

For most users: **Strategy 1 + Strategy 3 hybrid.** Set fallback_providers
in config (Strategy 3) so you get automatic failover when internet drops.
For known-offline sessions (plane, etc.), use manual switch (Strategy 1)
to avoid the retry penalty.