# Z-AI / GLM Provider Profile — Basti's Verified Setup (2026-07-15)

## Vergleichstabelle

| Eigenschaft | `claude` (Anthropic Pro) | `claude-zai` (Z-AI/GLM) |
|---|---|---|
| **Auth** | OAuth (Pro Subscription) | API Token (GLM Coding Plan) |
| **Haiku** | `claude-haiku-4-5` | `glm-4.7-flash` |
| **Sonnet** | `claude-sonnet-4-5` | `glm-5` |
| **Opus** | `claude-opus-4-5` | `glm-5.2[1m]` |
| **Context max** | 200K | 1M (Opus-Tier) |
| **Effort** | Auto | `max` |
| **Plugins** | 4 aktiv | 4 aktiv (synced) |
| **Cost/turn** | ~$0.08–0.13 | ~$0.05–0.13 |
| **Cmd** | `claude` | `claude-zai` |
| **PATH** | `~/.local/bin/claude` | `~/50-System/bin/claude-zai` |
| **Settings** | `~/.claude/settings.json` | `~/.claude-zai/settings.json` |
| **Banner** | None (native green) | Cyan wrapper banner (interactive only) |

## Basti's Optimized Z-AI Settings (2026-07-15)

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "zai_xxx",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.7-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-5",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5.2[1m]",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  },
  "model": "sonnet",
  "effortLevel": "max",
  "enableWorkflows": true,
  "theme": "dark",
  "enabledPlugins": {
    "skill-creator@claude-plugins-official": true,
    "frontend-design@claude-plugins-official": true,
    "ui-ux-pro-max@ui-ux-pro-max-skill": true,
    "find-skills@easier-life-skills": true
  },
  "extraKnownMarketplaces": {
    "easier-life-skills": "https://easier-life-skills.com/manifest.json",
    "ui-ux-pro-max-skill": "https://skill.ui-ux-pro-max.com/manifest.json"
  },
  "skipWorkflowUsageWarning": true,
  "agentPushNotifEnabled": true,
  "theme": "dark"
}
```

## Model Routing Entscheidung (Basti's Custom, 2026-07-15)

| Vorher | Nachher | Begründung |
|---|---|---|
| Haiku → `glm-4.5-air` | Haiku → `glm-4.7-flash` | Basti's Preference: 4.7 Flash ist Haiku-Äquivalent |
| Sonnet → `glm-5.2[1m]` | Sonnet → `glm-5` | Basti's Preference: glm-5 mit reasoning on = Sonnet-Äquivalent |
| Opus → `glm-5.2[1m]` | Opus → `glm-5.2[1m]` | Unverändert: 1M Context + max effort = Opus-Äquivalent |

### Z-AI Proxy Resolution (verified live, 2026-07-15)

| Modell-String | Proxy akzeptiert? | Context Window |
|---|---|---|
| `glm-4.7-flash` | ✅ | 200K |
| `glm-4.7` | ✅ | 200K |
| `glm-4.5-air` | ✅ | 200K |
| `glm-5` | ✅ | 200K |
| `glm-5.2` | ✅ | 200K |
| `glm-5.2[1m]` | ✅ | 1M |
| `glm-flash` | ❌ | — |

### Effort Mapping (Z-AI-spezifisch)

| Claude Code effort | GLM-5.2 actual mapped effort |
|---|---|
| `low`, `medium`, `high` (default) | `high` |
| `xhigh`, `max`, `ultracode` | `max` |

## Wrapper v2.0 Features

### `claude-zai doctor` — Health Check Subcommand

Prüft in einem Durchlauf:
1. **Binary** — existiert, ausführbar, Version
2. **Settings** — File existiert
3. **Token** — Länge > 20 Zeichen
4. **Endpoint** — Ausgabe der Base-URL
5. **Model-Routing** — Alle 3 Tier-Mappings anzeigen
6. **Plugins** — Anzahl aktiver Plugins
7. **Ping-Test** — Quick Call mit Haiku-Modell (~$0.001)
8. **Gesamtergebnis** — 0 Fehler = 🎉, sonst ⚠️ mit Count

### Banner-Regeln

| Situation | Banner? |
|---|---|
| `claude-zai` (interaktiv, kein Subcommand) | ✅ Cyan Banner |
| `claude-zai -p "task"` | ❌ Suppressed |
| `claude-zai --version` | ❌ Suppressed |
| `claude-zai --help` | ❌ Suppressed |
| `claude-zai doctor` | ❌ (eigener doctor-Banner) |
| `claude-zai auth status` | ❌ Suppressed |
| `claude-zai mcp list` | ❌ Suppressed |

Banner-Suppression-Check: `case "${1:-}" in -p|--print|--version|-v|--help|-h|doctor|auth|mcp|agents|update|upgrade|plugin|plugins) SUPPRESS=true ;;`

## Verified Tests (2026-07-15, live API)

```bash
# Test 1: Haiku-Routing
claude-zai -p "Reply: ok" --model haiku --max-turns 1 --output-format json
# → Backend: glm-4.7-flash, Context: 200000 ✅

# Test 2: Sonnet-Routing + 1M Context
claude-zai -p "Reply: ok" --model sonnet --max-turns 1 --output-format json
# → Backend: glm-5, Context: 200000 ✅

# Test 3: Plugin-Parität
python3 -c "
import json
a = set(json.load(open('/home/bratan/.claude/settings.json')).get('enabledPlugins',{}).keys())
z = set(json.load(open('/home/bratan/.claude-zai/settings.json')).get('enabledPlugins',{}).keys())
print(f'Plugins: {a == z} ({len(a)}/{len(z)})')
ma = set(json.load(open('/home/bratan/.claude/settings.json')).get('extraKnownMarketplaces',{}).keys())
mz = set(json.load(open('/home/bratan/.claude-zai/settings.json')).get('extraKnownMarketplaces',{}).keys())
print(f'Markets: {ma == mz} ({len(ma)}/{len(mz)})')
"
# → Plugins: True (4/4), Markets: True (2/2) ✅

# Test 4: Doctor Subcommand
claude-zai doctor
# → Binary ✅, Settings ✅, Token ✅, Routing ✅, Plugins ✅, Ping ✅

# Test 5: Kein Banner in Print/Version Mode
claude-zai --version  # → "2.1.204 (Claude Code)" only ✅
claude-zai -p "ok" --max-turns 1  # → no banner ✅
```

## Kosten (Live API, July 2026)

| Test | Kosten | Modell |
|---|---|---|
| Ping Test (Haiku) | ~$0.001 | `glm-4.7-flash` |
| Print-Mode Task (Sonnet) | ~$0.0538 | `glm-5` |
| Print-Mode Task (Opus) | ~$0.0305 | `glm-5.2[1m]` |

## Wrapper: `~/50-System/bin/claude-zai`

Der Wrapper liegt als Symlink-Ziel, nicht per PATH-Eintrag. Pfad:

```
~/50-System/bin/claude-zai → ist nicht im PATH
~/.local/bin/claude-zai → Symlink dorthin (oder PATH-Eintrag nötig)
```

BTW: `~/50-System/bin/` ist NICHT im PATH, obwohl AGENTS.md das mal behauptet hat. Symlink von `~/.local/bin/` dorthin, oder Wrapper direkt in `~/.local/bin/` installieren.

## Runbook

Ausführliches Runbook: `~/.hermes/docus/runbooks/claude-zai-klon.md`

Enthält:
- Vollständiges Setup-Protokoll
- Token-Handling (niemals ausgeben)
- Fehlerbehandlung
- Backup-Locations
- Die Überlegungen zum `--settings`-Flag vs. Dual-Binary-Ansatz