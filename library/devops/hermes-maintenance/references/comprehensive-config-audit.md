# Comprehensive Config Architecture Audit
**For use during post-update checks and after provider/auxiliary changes.**

This reference captures the full Python/YAML introspection script developed during the 2026-06-06 audit. Run it to check every dimension of config health in one pass.

## One-Shot Audit Script

```python
#!/usr/bin/env python3
"""Comprehensive Hermes config audit. Run after `hermes update` or provider changes."""
import yaml
from collections import Counter
from pathlib import Path

cfg_path = Path.home() / '.hermes' / 'config.yaml'
cfg = yaml.safe_load(cfg_path.read_text())

print("=" * 60)
print("HERMES CONFIG ARCHITECTURE AUDIT")
print("=" * 60)

# 1. Model consistency
m = cfg.get('model', {})
print(f"\n## 1. Model Config")
if m.get('model') != m.get('default'):
    print(f"  ⚠ model({m.get('model')}) ≠ default({m.get('default')})")
else:
    print(f"  ✓ model == default == {m.get('model')}")
print(f"  Provider: {m.get('provider')}")
print(f"  Base URL: {m.get('base_url')}")

# 2. No ollama remnants
print(f"\n## 2. Ollama Cleanliness")
ollama_refs = []
for section, val in cfg.items():
    if isinstance(val, dict):
        for k, v in val.items():
            if isinstance(v, str) and 'olla' in v.lower():
                ollama_refs.append(f"{section}.{k} = {v}")
if ollama_refs:
    print(f"  ⚠ ollama references found:")
    for r in ollama_refs:
        print(f"    {r}")
else:
    print(f"  ✓ No ollama references in any section")

# 3. Auxiliary provider consistency
ax = cfg.get('auxiliary', {})
auto_svcs = []
explicit_svcs = []
for svc, svc_cfg in ax.items():
    if isinstance(svc_cfg, dict):
        p = svc_cfg.get('provider', 'not set')
        if p == 'auto':
            auto_svcs.append(svc)
        else:
            explicit_svcs.append(f"{svc}={p}")
print(f"\n## 3. Auxiliary Providers")
print(f"  Explicit: {', '.join(explicit_svcs) if explicit_svcs else 'none'}")
if auto_svcs:
    print(f"  ⚠ On 'auto' (falls back through provider chain): {auto_svcs}")
else:
    print(f"  ✓ All auxiliary providers explicitly set")

# 4. Fallback providers
fps = cfg.get('fallback_providers', [])
print(f"\n## 4. Fallback Providers ({len(fps)})")
for fp in fps:
    print(f"  {fp.get('provider')}/{fp.get('model')}")

# 5. Custom providers
cps = cfg.get('custom_providers', [])
print(f"\n## 5. Custom Providers ({len(cps)})")
for cp in cps:
    print(f"  {cp.get('name')}: {cp.get('base_url')}")

# 6. Platform toolsets — check for duplicates
pt = cfg.get('platform_toolsets', {})
print(f"\n## 6. Platform Toolsets — Duplicates")
found_dupes = False
for plat, tools in pt.items():
    if isinstance(tools, list):
        dupes = {t: c for t, c in Counter(tools).items() if c > 1}
        if dupes:
            print(f"  ⚠ {plat}: {len(dupes)} duplicated tool(s)")
            for t, c in dupes.items():
                print(f"    {t}: {c}×")
            found_dupes = True
if not found_dupes:
    print(f"  ✓ No duplicate entries found")

# 7. Known section completeness
known_top = {
    '_config_version', 'agent', 'approvals', 'auxiliary', 'bedrock', 'browser',
    'checkpoints', 'code_execution', 'command_allowlist', 'compression', 'context',
    'credential_pool_strategies', 'cron', 'curator', 'custom_providers', 'dashboard',
    'delegation', 'discord', 'display', 'fallback_providers', 'file_read_max_chars',
    'gateway', 'goals', 'group_sessions_per_user', 'honcho', 'hooks', 'hooks_auto_accept',
    'human_delay', 'image_gen', 'kanban', 'known_plugin_toolsets', 'logging', 'lsp',
    'matrix', 'mattermost', 'memory', 'model', 'model_catalog', 'network', 'onboarding',
    'openrouter', 'paste_collapse_char_threshold', 'paste_collapse_threshold',
    'paste_collapse_threshold_fallback', 'personalities', 'platform_toolsets',
    'prefill_messages_file', 'privacy', 'prompt_caching', 'providers', 'quick_commands',
    'reasoning', 'secrets', 'security', 'session_reset', 'sessions', 'skills', 'slack',
    'streaming', 'stt', 'telegram', 'terminal', 'timezone', 'tool_loop_guardrails',
    'tool_output', 'tools', 'toolsets', 'tts', 'updates', 'video_gen', 'voice', 'web',
    'whatsapp', 'x_search'
}
unknown = set(cfg.keys()) - known_top
print(f"\n## 7. Unknown Top-Level Keys")
if unknown:
    print(f"  ⚠ Possibly unrecognized: {sorted(unknown)}")
else:
    print(f"  ✓ All top-level keys recognized")

# 8. Delegation config
d = cfg.get('delegation', {})
print(f"\n## 8. Delegation Config")
print(f"  reasoning_effort: {d.get('reasoning_effort', 'not set')}")
print(f"  model: {d.get('model', 'not set')}")
print(f"  provider: {d.get('provider', 'not set')}")
print(f"  max_concurrent_children: {d.get('max_concurrent_children')}")
print(f"  child_timeout_seconds: {d.get('child_timeout_seconds')}")

# 9. Security
sec = cfg.get('security', {})
print(f"\n## 9. Security Config")
print(f"  redact_secrets: {sec.get('redact_secrets')}")
print(f"  tirith_enabled: {sec.get('tirith_enabled')}")
print(f"  allow_private_urls: {sec.get('allow_private_urls')}")

# 10. Connectivity check
print(f"\n## 10. Gateway Status Suggestion")
print(f"  After any change to auxiliary.*, fallback_providers, or model: `hermes gateway restart`")
print("=" * 60)
```

## Usage

Save as `~/.hermes/scripts/config-audit.py` and run:

```bash
python3 ~/.hermes/scripts/config-audit.py
```

Or pipe through on each post-update check via a one-liner:

```bash
python3 -c "$(cat ~/.hermes/skills/devops/hermes-maintenance/references/comprehensive-config-audit.md | sed -n '/```python/,/```/p' | sed '1d;$d')"
```

## Audit History

| Date | Hermes Version | Key Findings |
|------|---------------|--------------|
| 2026-06-06 | v0.16.0 | 7 aux services on `auto`, 21 duplicate telegram tools, model consistent ✓, no ollama ✓ |
