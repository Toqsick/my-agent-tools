# firecrawl-web — Skill-Beschreibung

**Name:** firecrawl-web
**Version:** 1.0.0
**Autor:** BexTuychiev
**Quelle:** https://github.com/BexTuychiev/firecrawl-claude-code-skill
**Lizenz:** MIT

## Was ist das?

Web-Scraping, Screenshots, strukturierte Daten-Extraktion, Web-Search und Crawling via Firecrawl API. Konvertiert Webseiten in LLM-ready Markdown und strukturierte Daten.

## Wann nutzen?

- Aktuelle Web-Informationen benötigt
- URL scrapen / Webseite als Markdown extrahieren
- Screenshots von Webseiten machen
- Strukturierte Daten von einer Seite extrahieren
- Framework- oder Library-Dokumentation crawlen
- Web-Suche durchführen

## Features

| Feature | Beschreibung |
|---------|--------------|
| **Markdown** | Webseite → sauberes Markdown |
| **Screenshots** | Webseite als Bild |
| **Extract** | Strukturierte Daten (JSON) |
| **Search** | Web-Suche |
| **Crawl** | Dokumentation/Website crawlen |
| **Anti-Bot** | Bypass für Bot-Schutz |
| **JS-Rendering** | JavaScript-rendered Seiten |

## Commands

```bash
# Webseite als Markdown
python3 ~/.hermes/.agents/skills/firecrawl-web/fc.py markdown "https://example.com"

# Nur Main-Content (ohne Nav/Footer)
python3 ~/.hermes/.agents/skills/firecrawl-web/fc.py markdown "https://example.com" --main-only

# Screenshot
python3 ~/.hermes/.agents/skills/firecrawl-web/fc.py screenshot "https://example.com"

# Strukturierte Daten extrahieren
python3 ~/.hermes/.agents/skills/firecrawl-web/fc.py extract "https://example.com"

# Web-Search
python3 ~/.hermes/.agents/skills/firecrawl-web/fc.py search "query"

# Dokumentation crawlen
python3 ~/.hermes/.agents/skills/firecrawl-web/fc.py crawl "https://docs.example.com"
```

## Script-Pfad

```
~/.hermes/.agents/skills/firecrawl-web/fc.py
```

## Voraussetzungen

- Firecrawl API-Key (kostenlos verfügbar)
- Python 3
- `firecrawl-py` Package

## Hinweis für Hermes

Das Firecrawl-Skill ist primär für OpenCode/Claude Code gedacht. Für Hermes gibt es bereits eingebaute Tools:
- `web_extract` für Webseiten → Markdown
- `web_search` für Web-Suche
- `browser` für interaktive Seiten
- `browser_get_images` für Screenshots

Ohne Firecrawl API-Key sind die Hermes-Built-in-Tools die bessere Wahl.
