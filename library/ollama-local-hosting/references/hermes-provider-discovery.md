# Hermes Provider Discovery (Desktop vs CLI)

Diagnostic reference for the case where custom `providers:` entries appear in
`hermes model` (CLI) but are missing from the Desktop UI model picker overlay.

## Root Cause

Hermes` `list_picker_providers()` function in `hermes_cli/model_switch.py`
accepts an optional `user_providers` parameter that carries the
`providers:` dict from `config.yaml`. When passed, the function creates
picker rows for each custom provider entry.

**CLI (`hermes model`):** Calls `list_picker_providers()` with
`user_providers=cfg.get("providers", {})` — custom entries appear.

**Desktop API:** The web_server endpoint that serves the model picker UI
calls `list_picker_providers()` **without** the `user_providers` argument,
so custom providers are silently skipped — only built-in providers
(OpenAI, Anthropic, Nous, Ollama Cloud, Z.AI, etc.) appear.

## Diagnostic Script

```python
from hermes_cli.config import load_config
from hermes_cli.model_switch import list_picker_providers

cfg = load_config()
providers_section = cfg.get("providers", {})

print("Config has providers:", list(providers_section.keys()))

# Desktop behavior (no user_providers)
r1 = list_picker_providers(
    current_provider="minimax-oauth",
    current_model="MiniMax-M3",
    include_moa=True
)
local_in_r1 = any("local-ollama" in str(p.get("slug","")).lower() or
                   "local-ollama" in str(p.get("name","")).lower()
                   for p in r1)
print(f"Desktop (no user_providers): local-ollama visible = {local_in_r1}")

# CLI behavior (with user_providers)
r2 = list_picker_providers(
    current_provider="minimax-oauth",
    current_model="MiniMax-M3",
    user_providers=providers_section,
    include_moa=True
)
local_in_r2 = any("local-ollama" in str(p.get("slug","")).lower() or
                   "local-ollama" in str(p.get("name","")).lower()
                   for p in r2)
print(f"CLI (with user_providers): local-ollama visible = {local_in_r2}")
print(f"Provider count diff: Desktop={len(r1)} vs CLI={len(r2)}")
```

## Workarounds

1. **CLI picker verwenden:** `hermes model` öffnet die curses-basierte
   Modell-Auswahl im Terminal. Funktioniert korrekt.
2. **Direkter Aufruf:** `hermes chat --provider custom:local-ollama --model <name>`
   umgeht den picker komplett.
3. **Modell setzen:** `hermes config set model.provider custom:local-ollama`
   und `hermes config set model.default <model>` — `/new` danach.

## Upstream Fix (wann implementiert)

Der Bug liegt im Endpoint der `web_server.py` der den Model-Picker-Overlay
bedient. Der Fix: `user_providers=cfg.get("providers", {})` an den Aufruf
von `list_picker_providers()` übergeben.

```python
# In web_server.py, find the endpoint that calls list_picker_providers
# and add the user_providers parameter:
list_picker_providers(
    current_provider=...,
    current_model=...,
    user_providers=cfg.get("providers", {}),  # ← add this
    include_moa=...
)
```

## Verwandte Skills

- `ollama-local-hosting` → "Hermes Integration (Minimal)" für Config-Format
- `hermes-admin` → allgemeine Admin-Operationen
