---

name: firecrawl-web
description: "Use when user asks for Firecrawl web scraping, structured data extraction, Markdown conversion of URLs, screenshots via Firecrawl. NOT for hand-rolled scraping with curl/bs4 or non-web sources. Web-scraping, screenshots, and structured data extraction via Firecrawl."
metadata:
  author: BexTuychiev
  version: 1.0
lane: worker-flash
reasoning_effort: high
agent: Researcher
routing_hint: '**Agent-Scope:** Deep-research, fact-checking, paper-search, knowledge-base.
  Off-scope: code-building, visual design, writing — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['firecrawl', 'scraping', 'structured', 'data', 'extraction']
keywords: ['firecrawl', 'scraping', 'structured', 'data', 'extraction']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---
---

# Firecrawl Web Skill

Web-Zugriff via Firecrawl API — Screenshots, Markdown-Extraktion, strukturierte Daten, Crawling.

## Script

Das Skill bringt `fc.py` mit:
```

set -euo pipefail
~/.hermes/.agents/skills/firecrawl-web/fc.py
```

## Commands

```bash

set -euo pipefail
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

## Hinweis für Hermes

Firecrawl braucht einen API-Key. Ohne Key sind die Built-in-Tools (`web_extract`, `web_search`) **typischerweise ebenfalls deaktiviert**, weil sie intern denselben Firecrawl-Backend nutzen. Beide returnen dann:
`{"error": "Web tools are not configured. Set FIRECRAWL_API_KEY …"}`

### Fallback-Kaskade wenn weder Firecrawl noch Built-ins funktionieren

1. **GitHub-MCP-Tools** (funktionieren ohne API-Key):
   - `mcp__github__get_file_contents(owner, repo, path, ref?)` für Dateien in Repos
   - `mcp__github__search_repositories`, `search_code`, `search_issues`, `search_commits` für Suche
   - `mcp__github__list_issues`, `pull_request_read`, `issue_read` für GitHub-Diskussionen
2. **Raw `curl` auf bekannte Roh-URLs** (kein Auth, oft zensurfrei):
   - `curl -sL https://gist.githubusercontent.com/<user>/<id>/raw` — Gist-Inhalt direkt
   - `curl -sL https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>` — Repo-Rohdatei
   - `curl -sL https://api.github.com/<endpoint>` — GitHub REST API (60 req/h ohne Token, 5000 mit `GITHUB_TOKEN`)
   - `curl -sL https://news.ycombinator.com/item?id=<NNN>` — HN-Thread (HTML)
3. **MCP-Search-Tools** als Discovery-Schicht (liefern Treffer-Listen, kein Volltext)
4. Erst danach: User bitten, den Key zu konfigurieren (`hermes model`)

### PITFALL: `web_extract` ist KEIN unabhängiger Pfad

Wer annimmt, `web_extract` sei eine eigenständige Hermes-Implementierung, liegt falsch. Beide Tools — Firecrawl-Skill UND die Built-ins `web_extract`/`web_search` — hängen am selben Firecrawl-Backend und fallen zusammen aus. Bei Firecrawl-Konfig-Problemen direkt zur Fallback-Kaskade oben springen, statt zweimal den gleichen Fehler zu erhalten.

Verifiziert 2026-07-13: `web_extract` lieferte für `https://gist.github.com/cereblab/...` exakt die Firecrawl-Konfig-Fehlermeldung; gleichzeitig funktionierten `mcp__github__*` und `curl` auf die identische URL ohne jede Änderung am Setup.

### Wenn nur das Firecrawl-Skill geladen ist, der Key aber fehlt

Nicht `fc.py markdown <url>` aufrufen — der Wirft einen Auth-Fehler. Statt:
```bash
curl -sL -A "Mozilla/5.0" "https://<url>" | head -c 50000
```
Reicht für 95 % der Read-only-Fact-Check-Anwendungen.

Das Firecrawl-Skill ist primär für OpenCode gedacht. Für Hermes reichen die Built-in-Tools in den meisten Fällen.
