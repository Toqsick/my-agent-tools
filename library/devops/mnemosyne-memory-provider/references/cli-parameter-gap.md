# Mnemosyne CLI: Parameter-Gap zur Python-API

Die `mnemosyne` CLI (`/home/bratan/.hermes/hermes-agent/venv/bin/mnemosyne`) ist
ein vierter Import-Pfad neben den dreien in `api-signature.md` — mit **deutlich
weniger Parametern** als die Python-API.

## Parameter-Vergleich: CLI vs Python-Direct-API

| Parameter | CLI `store` | Python `mnemosyne.remember()` |
|-----------|-------------|-------------------------------|
| `content` | ✅ 1. positional | ✅ |
| `source` | ✅ 2. positional | ✅ |
| `importance` | ✅ 3. positional (float) | ✅ |
| `scope` | ❌ | ✅ (global/session) |
| `metadata` | ❌ | ✅ (dict) |
| `trust_tier` | ❌ | ✅ |
| `bank` | ❌ | ✅ |
| `extract` | ❌ | ✅ |
| `extract_entities` | ❌ | ✅ |
| `valid_until` | ❌ | ✅ |

## Konsequenz

Wenn die Hermes-Tools (`mnemosyne_remember`, `mnemosyne_recall`) nicht im
Toolset verfügbar sind und nur die CLI erreichbar ist, müssen strukturierte
Felder wie `scope`, `metadata`, und `trust_tier` **im Content-Text selbst**
kodiert werden.

**Workaround — Structured Content Encoding:**

```
[Pattern] Titel — Beschreibung

Scope: global
Source: workflow
Metadata: key=value, key2=value2
TrustTier: tool

Fließtext des Inhalts...
```

Die CLI `mnemosyne_recall` hat das gleiche Problem — sie akzeptiert `query`
und `top_k` (optional, default 5) als positional args, aber keine
`vec_weight`, `fts_weight`, `from_date`, `to_date` etc.

| Parameter | CLI `recall` | Python `mnemosyne.recall()` |
|-----------|-------------|-----------------------------|
| `query` | ✅ 1. positional | ✅ |
| `top_k` | ✅ 2. positional (default 5) | ✅ (`top_k`) |
| `vec_weight` | ❌ | ✅ |
| `fts_weight` | ❌ | ✅ |
| `importance_weight` | ❌ | ✅ |
| `temporal_weight` | ❌ | ✅ |
| `from_date` / `to_date` | ❌ | ✅ |
| `source` | ❌ | ✅ |
| `topic` | ❌ | ✅ |
| `bank` | ❌ | ✅ |

**Workaround CLI Recall:** Die CLI `recall` nutzt standardmäßig FTS5-only
(keine Vektorgewichtung möglich). Für Hybrid-Search oder temporale Filter
muss man den Python-Pfad nehmen: entweder direkten Import (`from mnemosyne
import recall`) oder `_handle_recall` (siehe `mnemosyne-memory-provider`
SKILL.md § Mnemosyne Direct Recall in Dashboard Backends).

## Wann tritt dieser Gap auf?

1. **System-Prompt / AGENTS.md / Task-Brief referenziert Tool-Namen**
   (`mnemosyne_remember`, `mnemosyne_recall`) die im aktuellen Hermes-Profil
   nicht verfügbar sind → Fallback auf CLI.

2. **Subagent / routed task** bekommt Memory-Operationen nicht als
   Hermes-Tool, sondern muss auf die CLI ausweichen.

3. **Background-Script / Cron-Job** hat keinen Zugriff auf die
   Hermes-Tool-Umgebung.

## Erkennungs-Pattern

Wenn ein Task sagt „Nutze `mnemosyne_remember(...)`" oder
„`mnemosyne_recall(...)`" aber dieser Tool-Name nicht im Function-Schema
deiner Umgebung auftaucht, dann:

1. `which mnemosyne` — finde die CLI
2. `mnemosyne --help` — prüfe die verfügbaren Subcommands
3. Bei `store`: Content strukturiert kodieren (siehe oben)
4. Bei `recall`: Akzeptiere FTS5-only oder weiche auf Python-Import aus

## Session-Beleg

Validated 2026-07-17: Task sagte `mnemosyne_remember`/`mnemosyne_recall`,
diese existierten nicht im Toolset. Lösung: `mnemosyne store <content>
<source> <importance>` via CLI. Scope (`global`) musste im Content-Text als
`Scope: global` kodiert werden.
