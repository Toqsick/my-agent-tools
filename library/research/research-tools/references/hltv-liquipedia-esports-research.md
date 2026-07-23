# Esports & Tech News Research — Fallback Chain

## Quick Source Reference (verified 2026-06-26)

| Source | URL | Was | Methode | Zuverlässigkeit |
|--------|-----|-----|---------|-----------------|
| Heise Security | `heise.de/security/` | CVEs, Exploits, Patches (DE) | `curl + grep '"headline":"'` | ✅ Sehr gut |
| Heise Tech | `heise.de/` | Allgemeine Tech-News (DE) | `curl + grep '"headline":"'` | ✅ Sehr gut |
| HLTV RSS | `hltv.org/rss/news` | CS2/ESL Turnier-News | `curl + grep '<title>'` | ✅ Sehr gut |
| HN Frontpage | `news.ycombinator.com` | Tech-Trends | `curl + grep 'titleline'` | ✅ Gut |
| BleepingComputer | `bleepingcomputer.com/news/security/` | Security-News (EN) | `curl + grep slugs` | ✅ Gut |
| The Verge | `theverge.com/cyber-security` | Security/Tech (EN) | `curl + sed strip` | ✅ Gut |
| Liquipedia API | `liquipedia.net/counterstrike/api.php` | Brackets, Matches | `curl --compressed + JSON` | ⚠️ Playoffs fehlen |
| HLTV Direkt | `hltv.org/matches` | Live-Ergebnisse | ❌ Cloudflare | ❌ Blockiert |
| web_search | Firecrawl | Allgemeine Suche | built-in | ⚠️ Manchmal down |

## Quellen-Hierarchie (resilient bei Blockaden)

Wenn HLTV/Liquipedia blockiert sind (Cloudflare), nutze dieseFallback-Kette:

### HLTV.org
- **Direktzugriff meist blockiert** (Cloudflare Challenge, JS erforderlich)
- **✅ EMPFOHLEN — RSS Feed (kein Cloudflare, funktioniert mit einfachem curl!):**
  ```bash
  curl -sL "https://www.hltv.org/rss/news" 2>/dev/null | grep -oP '(?<=<title>)[^<]+' | head -20
  curl -sL "https://www.hltv.org/rss/news" 2>/dev/null | grep -oP '(?<=<description>)[^<]+' | head -20
  ```
  Liefert neueste News-Titel UND Descriptions direkt als XML. RSS ist der zuverlässigste HLTV-Zugang.
- **Workaround 1 — Google Cache:**
  ```bash
  curl -sL "https://webcache.googleusercontent.com/search?q=cache:hltv.org/matches" \
    -H "User-Agent: Mozilla/5.0"
  ```
- **Workaround 2 — Archive.org:** `https://web.archive.org/web/2026/https://www.hltv.org/matches`
- **Akzeptabler Fallback:** The Verge Esports, ESPN Esports, Reddit r/GlobalOffensive

### Liquipedia
- **API (funktioniert ohne JS!):**
  ```bash
  # Rendered HTML (für Playoffs, Brackets):
  curl -sL --compressed \
    "https://liquipedia.net/counterstrike/api.php?action=parse&page=IEM_Cologne_2026&prop=text&format=json" \
    -H "User-Agent: Mozilla/5.0" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('parse',{}).get('text',{}).get('*','')[:5000])"

  # Raw Wikitext (für strukturierte Match-Daten):
  curl -sL --compressed \
    "https://liquipedia.net/counterstrike/api.php?action=parse&page=IEM_Cologne_2026&prop=wikitext&format=json" \
    -H "User-Agent: Mozilla/5.0"
  ```
- **Wichtig:** `--compressed` flag ist OBLIGATORISCH (sonst 406 von ihrem Proxy)
- **Playoffs sind client-side gerendert** → API zeigt nur Grundseite. Nutze Prize Pool Tabelle als Proxy.

### The Verge (Tech News Fallback)
- **Funktioniert gut mit einfachem curl:**
  ```bash
  curl -sL "https://www.theverge.com/cyber-security" -H "Mozilla/5.0" \
    | sed 's/<[^>]*>//g' \
    | grep -iP '(CVE|exploit|hacker|breach|vulnerability|patch|ransomware)' \
    | head -15
  ```
- Artikel-Listen sind im SSR-HTML enthalten (Next.js), strippbar mit sed
- Sortierung: neueste Artikel zuerst (chronologisch)

### Web Search / Web Extract
- Kann ausfallen (Firecrawl/NoneType Errors)
- Wenn `web_search` fehlschlägt → web_extract direkt auf Ziel-URL
- Beide fallen → curl-basierter Fallback (siehe oben)

### BleepingComputer (Security News — funktioniert gut!)
- **Security-News mit einfachem curl:**
  ```bash
  curl -sL "https://www.bleepingcomputer.com/news/security/" \
    -H "User-Agent: Mozilla/5.0" \
    | grep -oP '>([A-Z][^.!?]*[^.!?])<' | grep -v "^\<(html\|head\|body\|div\|span\|a\|p\|li\|ul\|script\|meta\|link\|img\|title\|h[1-6]\|br\|hr\|input\|form\|button\|section\|nav\|footer\|header\|main\|article\|aside\|figure\|figcaption\|table\|tr\|td\|th\|thead\|tbody\|tfoot\|label\|fieldset\|legend\|select\|option\|textarea\|video\|audio\|canvas\|svg\|path\|line\|rect\|circle\|polygon\|polyline\|ellipse\|text\|g\|defs\|use\|symbol\|clippath\|mask\|pattern\|image\|switch\|foreignObject\|desc\|title)" | head -20
  ```
  Einfacher: Article-Slugs extrahieren:
  ```bash
  curl -sL "https://www.bleepingcomputer.com/news/security/" \
    | grep -oP '(?<=<a href="https://www.bleepingcomputer.com/news/security/)[^"]*' | head -10
  ```
  (Slugs können mit `-` zu Titel umgewandelt werden: `sed 's/-/ /g'`)

### Heise.de Security (Deutschland — funktioniert gut mit curl!)
- **Security-News mit einfachem curl (DE-quelle!):**
  ```bash
  curl -sL "https://www.heise.de/security/" \
    -H "User-Agent: Mozilla/5.0" \
    | grep -oP '"headline":"[^"]*"' | sed 's/"headline":"//;s/"//' | head -20
  ```
  Liefert die neuesten Security-Headlines als JSON-LD embedded data. Sehr zuverlässig.
- **Tech-News allgemein:**
  ```bash
  curl -sL "https://www.heise.de/" \
    -H "User-Agent: Mozilla/5.0" \
    | grep -oP '"headline":"[^"]*"' | sed 's/"headline":"//;s/"//' | head -20
  ```
- **Vorteil:** Deutsche Quelle, oft minütlich aktuell, kein Cloudflare
- **Pitfall:** Manche Headlines sind Paywall-Only (🔒) — trotzdem sichtbar als Titel

### Hacker News (Frontpage — curl statt Algolia)
- **Einfacher curl auf news.ycombinator.com:**
  ```bash
  curl -sL "https://news.ycombinator.com" \
    -H "User-Agent: Mozilla/5.0" \
    | grep -oP '<span class="titleline"><a[^>]*>[^<]*' | sed 's/.*>//' | head -30
  ```
  Liefert die aktuellen Top-Stories. Gut für Tech-Trends, weniger für Breaking Security-News.
- **Algolia API** (unzuverlässig für zeitkritische News, siehe Pitfalls)

### Hacker News (Algolia API)
- **Pitfall:** `numericFilters=created_at_i>timestamp` funktioniert UNZUVERLÄSSIG — liefert oft alte Posts (2013-2022) statt aktuelle.
- **Workaround:** `search_by_date` Endpoint nutzen, aber nur ohne `numericFilters`:
  ```bash
  curl -sL "https://hn.algolia.com/api/v1/search_by_date?query=security+OR+exploit+OR+hack+OR+cyber&hitsPerPage=10&tags=story"
  ```
  Achtung: Auch hier kann die Sortierung unzuverlässig sein. Besser: HN als sekundäre Quelle nur für Trending-Themen nutzen, nicht für Breaking News.
- **Besser für Security-News:** BleepingComputer (siehe oben) ist zuverlässiger und aktueller.

## Wichtige Pitfalls

| Symptom | Ursache | Fix |
|---------|---------|-----|
| Cloudflare "Just a moment..." | hltv.org, liquipedia (ohne API) | **HLTV RSS Feed** nutsen (kein Cloudflare!) |
| `406 Not Acceptable` | Liquipedia ohne gzip | `--compressed` flag hinzufügen |
| `grep: lookbehind assertion is not fixed length` | macOS grep unterstützt kein variabel-length lookbehind | `sed 's/<[^>]*>//g'` statt grep mit lookbehind |
| HLTV Results leer trotz Cloudflare-Block | Challenge-Seite wird serviert | **RSS Feed** als primäre Quelle — funktioniert immer |
| web_search "NoneType" Error | Firecrawl backend down | web_extract als 1. Fallback, curl als 2. Fallback |
| HN Algolia gibt alte Posts zurück | `numericFilters` kaputt/unzuverlässig | `search_by_date` Endpoint oder BleepingComputer als Security-Quelle |
| grep "lookbehind assertion is not fixed length" | macOS/BSD grep unterstützt kein variabel-length lookbehind | `sed 's/<[^>]*>//g'` statt grep mit lookbehind |
| Liquipedia API liefert nur Grundseite ohne Playoffs | Playoffs sind client-side JS-rendert | Prize Pool Tabelle als Proxy für Ergebnisse, oder Heise/HLTV RSS |

## Output-Format für Esports-Briefing

Kompakt (max 20 Zeilen), nach Sektionen getrennt:
```
🎮 ESL/CS2: <Turnierstatus, Ergebnisse, Überraschungen>
💻 Tech: <Neueste Tech-News>
🔒 Security: <CVEs, Exploits, Bug Bounties>
```
Mit Emojis für Scanbarkeit. Keine langen Erklärungen.
