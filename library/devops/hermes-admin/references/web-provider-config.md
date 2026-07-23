# Hermes Web Provider Configuration

**Stand:** 2026-07-16  
**Kontext:** Ermittelt bei DDGS-Search-Backend-Umstellung (Session 2026-07-16)

## Config Keys (in `config.yaml`)

```yaml
web:
  backend: firecrawl           # Shared fallback (genutzt wenn search/extract kein Override)
  search_backend: ddgs         # Override für Suche (leer = verwendet `backend`)
  extract_backend: parallel    # Override für Extraktion (leer = verwendet `backend`)
  use_gateway: true            # Nous/Managed Gateway (Subscriber)
  cloud_provider: browser-use  # Cloud-Browser-Provider
```

**Routing-Logik** (aus `tools/web_tools.py` + `agent/web_search_registry.py`):

1. `web.search_backend` → wenn gesetzt & verfügbar → verwenden
2. Andernfalls `web.backend` → wenn verfügbar → verwenden
3. Andernfalls Auto-Detect (env vars)

Gleiches Schema für `extract_backend` → `backend`.

**Hermes hat keine automatische Cross-Provider-Fallback-Kette.**
Wenn `search_backend: ddgs` fehlschlägt (Rate-Limit, Timeout), gibt der
Provider `{"success": False, "error": "..."}` zurück. Der Agent muss dann
manuell auf `web_extract` (bekannte URL) oder Browser-Tool ausweichen.

## Verfügbare Search-Provider (Built-in Plugins)

Provider leben als Plugins unter `~/.hermes/hermes-agent/plugins/web/<name>/`:

| Provider-Name | Config-Wert | API-Key? | Search | Extract | Besonderheit |
|---|---|---|---|---|---|
| **Firecrawl** | `firecrawl` | `FIRECRAWL_API_KEY` | ✅ | ✅ | Standard, auch über Nous Gateway |
| **DDGS** | `ddgs` | Keiner | ✅ | ❌ | Lokal, kostenlos, HTML-Scrape, kein API-Key |
| **Brave Free** | `brave-free` | `BRAVE_API_KEY` | ✅ | ❌ | 2.000 Queries/Monat gratis |
| **SearXNG** | `searxng` | Keiner | ✅ | ✅ | Self-hosted nötig |
| **Tavily** | `tavily` | `TAVILY_API_KEY` | ✅ | ✅ | 1.000 API-Calls/Monat free |
| **Exa** | `exa` | `EXA_API_KEY` | ✅ | ✅ | API-Key erforderlich |
| **Parallel** | `parallel` | Verschiedene | ❌ | ✅ | Multi-Provider-Extraktion |
| **xAI** | `xai` | `XAI_API_KEY` | ✅ | ✅ | xAI/Grok-Web-Search |

## DDGS Provider (Details)

- **Pfad:** `~/.hermes/hermes-agent/plugins/web/ddgs/provider.py`
- **Installation:** `pip install ddgs` (im venv: `~/.hermes/hermes-agent/venv/bin/pip`)
- **Version (Stand):** 9.14.4 (`from ddgs import DDGS`)
- **Kapazität:** Search-only (`supports_extract → False`)
- **Timeout:** 30s Wall-clock (Prozess intern), 10s Request (DDGS Client)
- **Rate-Limits:** Server-seitig von DuckDuckGo (ca. 100 Queries/Std frei)
- **Auth:** Kein API-Key nötig

### Verfügbarkeit prüfen

```bash
# Check ob installiert
pip3 show ddgs 2>/dev/null || echo "NOT INSTALLED"

# Test-Suche
python3 -c "
from ddgs import DDGS
with DDGS(timeout=10) as d:
    for hit in d.text('test query', max_results=2):
        print(hit.get('title', ''), '→', hit.get('href', ''))
"
```

### Provider-Ressourcen finden

```bash
# Alle Web-ProviderPlugin anzeigen
ls ~/.hermes/hermes-agent/plugins/web/

# Verfügbarkeit des DDGS-Providers testen
cd ~/.hermes/hermes-agent && python3 -c "
from plugins.web.ddgs.provider import DDGSWebSearchProvider
p = DDGSWebSearchProvider()
print('Name:', p.name)
print('Available:', p.is_available())
print('Supports search:', p.supports_search())
print('Supports extract:', p.supports_extract())
"
```

## Fallback-Patterns (Behavioral, nicht konfiguriert)

Da Hermes keine automatisierte Fallback-Kette hat, muss der Agent bei
DDG-Failure manuell ausweichen:

| Fallback | Wann | Kosten |
|---|---|---|
| `web_extract` auf bekannte URL | URL bekannt | Firecrawl-Tokens (via Nous-Subscription) |
| Browser-Tool (`browser_navigate` + `browser_snapshot`) | URL unbekannt | Browser-Session, keine API-Kosten |
| Config auf `firecrawl` zurücksetzen (`search_backend: ''`) | Dauerhafter Wechsel nötig | Braucht `/reset`, verbraucht Firecrawl-Kontingent |

## Config Validation

```bash
# Nach Änderung: Config check
hermes config check

# Web-Config auslesen
python3 -c "
import yaml
cfg = yaml.safe_load(open('/home/bratan/.hermes/config.yaml'))
web = cfg.get('web', {})
print('backend:', web.get('backend'))
print('search_backend:', web.get('search_backend'))
print('extract_backend:', web.get('extract_backend'))
"
```

**Wichtig:** Config-Änderungen an `web.search_backend` greifen erst nach
`/reset` oder neuer Session. Die laufende Session cacht den Provider
beim Start.

## Verification via Hermes Plugin Manager (Golden Path)

Der sauberste Weg, zu prüfen welcher Provider **tatsächlich resolved** wird:

```python
from hermes_cli.plugins import get_plugin_manager
from agent.web_search_registry import get_active_search_provider, list_providers

pm = get_plugin_manager()
pm.discover_and_load(force=True)  # <-- nötig für Plugin-Kontext!

# Vollständige Provider-Landschaft
for p in list_providers():
    print(f"{p.name:15s} search={p.supports_search()} extract={p.supports_extract()} avail={p.is_available()}")

# Der aktive (resolved) Provider
active = get_active_search_provider()
print(f"Aktiv: '{active.name}' — avail={active.is_available()}")
```

**Wichtig:** `get_active_search_provider()` funktioniert **nur** nach
`pm.discover_and_load()` — im Standalone-Python sind 0 Provider registriert.
Die echte Hermes-Laufzeit ruft das beim Start automatisch.

## Pitfalls

### Hermes-Guard blockt Direkt-Edits auf `config.yaml`

`patch` und `write_file` auf `~/.hermes/config.yaml` werden **by design**
geblockt (Cross-Profile-Guard). Immer `hermes config set <key.path> <value>`
benutzen:

```bash
# ✅ korrekt
hermes config set web.search_backend ddgs

# ❌ wird geblockt (Hermes-Guard)
patch ~/.hermes/config.yaml ...
write_file ~/.hermes/config.yaml ...
```

### `hermes config set` strippt Kommentar-Blöcke

Bei `hermes config set` werden auskommentierte Beispiel-Blöcke am
Datei-Ende entfernt. **Kein Datenverlust** — die Blöcke sind inaktive
Beispiele aus der Default-Config, aber die Diff-Größe überrascht:

```bash
# Vorher: Datei 21953 bytes
# Nachher: Datei ~18000 bytes
# Diff zeigt nur 1 intendierte Änderung, Rest sind Kommentar-Strips
# → vorher Backup machen!
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d)
diff ~/.hermes/config.yaml.bak.* ~/.hermes/config.yaml | head -20
```
