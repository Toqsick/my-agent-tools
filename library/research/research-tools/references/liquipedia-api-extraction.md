# Liquipedia / MediaWiki API Data Extraction

## Problem

Liquipedia pages are heavily JS-rendered. Raw HTML via `curl` returns 200KB+ of nav/ads/scripts with match data only in client-side rendered widgets. The `web_extract` tool may fail with scheme errors on Liquipedia URLs.

## Solution: Use the MediaWiki API

Liquipedia runs MediaWiki. The `action=parse` API returns clean wikitext with all match data in structured templates.

### Basic Pattern

```bash
# ALWAYS use --compressed (gzip) — Liquipedia returns 406 without it
curl -sL --compressed \
  "https://liquipedia.net/counterstrike/api.php?action=parse&page=PAGE_NAME&prop=wikitext&format=json" \
  -H "User-Agent: Mozilla/5.0"
```

### Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `action` | `parse` | Parse page, return structured content |
| `page` | Full page name (e.g. `Intel_Extreme_Masters/2026/Cologne/Stage_1`) | Target page |
| `prop` | `wikitext` | Get raw wikitext (not HTML) |
| `format` | `json` | Machine-readable output |

### Parsing Match Data from Wikitext

Match results use `{{Match}}` templates with nested `{{Map}}` templates:

```
{{Match
  |opponent1={{TeamOpponent|teamname1}}
  |opponent2={{TeamOpponent|teamname2}}
  |date=June 2, 2026 - 12:30 CEST |finished=true
  |map1={{Map|map=Inferno|finished=true
    |t1firstside=ct|t1t=5|t1ct=8|t2t=4|t2ct=4
  }}
}}
```

- `t1t` / `t1ct` = Team 1 T-side / CT-side rounds
- `t2t` / `t2ct` = Team 2 T-side / CT-side rounds
- `finished=true` = match completed
- `finished=skip` = map not played (series ended early)
- Overtime rounds use `o1t1firstside`, `o1t1t`, `o1t1ct` prefixes

### Standings / Swiss Table

Standings use `{{SwissTableLeague}}` template with `|bg1=up|team1=xxx` entries:
- `bg` values: `up` (advancing), `down` (eliminated), `stay` (still playing), `stayup`/`staydown`
- `temp_tie` = seed/rank within group

### Tournament Page Structure

Major tournaments typically have pages:
- `Intel_Extreme_Masters/2026/Cologne` — Main page (overview, prizepool, participants)
- `Intel_Extreme_Masters/2026/Cologne/Stage_1` — Stage 1 (Swiss, 16 teams)
- `Intel_Extreme_Masters/2026/Cologne/Stage_2` — Stage 2 (Swiss, 16 teams)
- `Intel_Extreme_Masters/2026/Cologne/Stage_3` — Stage 3 (Swiss, 16 teams)
- `Intel_Extreme_Masters/2026/Cologne/Playoffs` — Playoffs (8 teams, single elim)

### Python Parsing Snippet

```python
import re, json

def parse_liquipedia_matches(wikitext):
    """Extract match results from Liquipedia wikitext."""
    matches = []
    for m in re.finditer(r'\{\{Match\s*\n(.*?)\n\s*\}\}', wikitext, re.DOTALL):
        block = m.group(1)
        opp1 = re.search(r'opponent1=\{\{TeamOpponent\|([^}]+)\}\}', block)
        opp2 = re.search(r'opponent2=\{\{TeamOpponent\|([^}]+)\}\}', block)
        date = re.search(r'date=([^|]+)', block)
        finished = 'finished=true' in block
        maps = []
        for map_m in re.finditer(r'map\d+=\{\{Map\|map=([^|]+)\|finished=(\w+)', block):
            maps.append({'map': map_m.group(1), 'status': map_m.group(2)})
        if opp1 and opp2:
            matches.append({
                'team1': opp1.group(1),
                'team2': opp2.group(1),
                'date': date.group(1).strip() if date else None,
                'finished': finished,
                'maps': maps
            })
    return matches
```

### prop=text vs prop=wikitext

| Prop | Returns | Best for |
|------|---------|----------|
| `wikitext` | Raw wikitext with `{{Template}}` markup | Parsing match brackets, structured data |
| `text` | Rendered HTML (cleaner for reading) | Extracting standings tables, prizepool, participants |

Both require `--compressed`. Use `text` for quick human-readable extraction, `wikitext` for programmatic parsing.

```bash
# For rendered HTML (standings, prizepool, participants)
curl -sL --compressed \
  "https://liquipedia.net/counterstrike/api.php?action=parse&page=PAGE_NAME&prop=text&format=json" \
  -H "User-Agent: Mozilla/5.0"
```

### Playoffs Bracket Limitation

**Important:** The Playoffs bracket is often NOT included in the API response (neither `text` nor `wikitext`). The bracket is rendered client-side via JavaScript and may be empty in the API output.

Workarounds:
1. **Check the Prize Pool table** — it lists final placements (1st, 2nd, 3rd-4th, 5th-8th etc.). If 3rd-4th are filled in, the semifinals are done. If 1st is still `TBD`, the Grand Final hasn't been played yet.
2. **Check "Upcoming Matches"** — the page header lists scheduled matches with countdown timers.
3. **Raw HTML scraping fallback** — when the API returns empty brackets, use `curl --compressed` to get the full HTML and extract data with Python regex (see below).

### Raw HTML Scraping Fallback

When the MediaWiki API returns empty/incomplete bracket data (common for Playoffs), fall back to fetching the raw HTML page and extracting match results with regex:

```bash
# Step 1: Fetch compressed HTML
curl -sL "https://liquipedia.net/counterstrike/PAGE_NAME" \
  -H "User-Agent: Mozilla/5.0" -H "Accept-Encoding: gzip" --compressed \
  -o /tmp/liq.html

# Step 2: Extract match/bracket sections with Python
python3 -c "
import re
with open('/tmp/liq.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'Quarterfinals' in line or 'Semifinals' in line or 'Grand Final' in line:
        start, end = max(0, i-5), min(len(lines), i+80)
        context = '\n'.join(lines[start:end])
        clean = re.sub(r'<[^>]+>', ' ', context)
        clean = re.sub(r'&[a-z]+;', '', clean)
        clean = re.sub(r'&#\d+;', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        print(clean[:3000])
        break
"
```

**Why this works:** Even though Liquipedia is JS-heavy, the server-side rendered HTML still contains match data as plain text within the HTML structure (team names, scores, map names). The `<[^>]+>` tag stripping + entity cleanup produces readable output.

**Key markers to search for in raw HTML:**
- `Quarterfinals`, `Semifinals`, `Grand Final` — bracket section headers
- Team names appear as plain text between HTML tags
- Scores appear as `N : N` patterns (e.g. `2 : 1` for Bo3 results)
- Map names: `Dust II`, `Mirage`, `Inferno`, `Nuke`, `Anubis`, `Overpass`, `Ancient`
- `TBD` = not yet determined (match not played)

**Pitfalls:**
- The raw HTML is ~1.5MB — use `head`/`tail` or targeted regex, don't print everything
- HTML entities (`&#160;`, `&amp;`) need cleanup
- Some data is truly JS-only (live scores, countdown timers) — not available without browser
- Stage pages (Stage_1, Stage_2, Stage_3) have more complete data than the main page in the API

### Pitfalls

1. **406 Not Acceptable**: Always use `--compressed` flag with curl. The API requires gzip encoding.
2. **Page names**: Use exact page names (check URL). Spaces become underscores.
3. **Rate limiting**: Don't hammer the API. Cache results when possible.
4. **TBD entries**: Early in tournaments, some opponents show as `TBD`.
5. **Finished flag**: Check `|finished=true` on the Match template.
6. **Map scores**: `finished=skip` means the map wasn't played.
7. **Playoffs data missing**: Bracket results may not be in the API response. Use Prize Pool placement as proxy for completed matches, or fall back to raw HTML scraping.
8. **web_extract fails on Liquipedia**: The `web_extract` tool may fail with "No scheme supplied" errors on Liquipedia URLs. Use `curl --compressed` directly instead.
9. **browser unavailable**: If browser tools fail (no engine), the raw HTML fallback via curl is the most reliable approach for Liquipedia data.

### Applicability

This pattern works for any MediaWiki-based wiki:
`https://wiki.example.com/api.php?action=parse&page=Page_Name&prop=wikitext&format=json`
Always use `--compressed`.
