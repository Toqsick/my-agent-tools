# Nexus Mods: Manuelle Downloads

**Warum kein curl:** Cloudflare nutzt TLS-Fingerprint-Bot-Detection. Selbst mit korrekt exportierten Browser-Cookies (cf_clearance, nexusmods_session) gibt curl 403 "Just a moment..." Challenge statt Inhalt. Die `cf_clearance` Cookie ist UA+IP+TLS-bound und curl hat einen anderen TLS-Fingerprint als Brave/Chrome. **Einziger funktionierender Weg:** User klickt manuell im echten Browser.

## HTML-Download-Helper (pragmatischer Workaround)

Statt User mit Copy-Paste von 444 Links zu quälen, baue einen **lokalen HTML-Helper** mit Progress-Tracking:

```bash
# 1. Mod-IDs aus Collection extrahieren (GitHub-Repo der Collection als Source)
python3 -c "
import json
mods = json.load(open('mods-lite-final.json'))
html = '<html><body>'
for i, m in enumerate(mods, 1):
    html += f'<div id=\"mod-{m[\"id\"]}\"><a href=\"https://www.nexusmods.com/cyberpunk2077/mods/{m[\"id\"]}?tab=files\" target=\"_blank\">{i}. [{m[\"category\"]}] {m[\"name\"]}</a> <button onclick=\"markDone({m[\"id\"]})\">done</button></div>'
html += '</body></html>'
open('download-helper.html', 'w').write(html)
"

# 2. User öffnet: file:///home/bratan/cp77-modding/cod-research/download-helper.html
# 3. Klickt jeden Link → Manual Download → ZIP landet in ~/Downloads/
# 4. Klickt "done" für Fortschritt
# 5. Verschiebt ZIPs nach ~/cp77-modding/downloads/
# 6. Ruft sort-downloads.sh auf (siehe unten)
```

## Workflow für manuelle Downloads

1. User öffnet Brave (eingeloggt auf nexusmods.com)
2. Öffnet `file:///home/bratan/cp77-modding/cod-research/download-helper.html`
3. Klickt jeden Mod-Link → Files-Tab → "Manual Download" (Slow geht durch, schneller Mod Manager nicht)
4. ZIPs landen in `~/Downloads/`
5. Verschiebt ZIPs nach `~/cp77-modding/downloads/`
6. Führt `./scripts/sort-downloads.sh` aus (siehe unten)
7. Smoke-Check re-runnen

**Sortier-Skript (`~/cp77-modding/scripts/sort-downloads.sh`):**
- Erkennt `.archive`-Dateien → `archive/pc/mod/`
- Erkennt `.dll` + Plugins → `red4ext/plugins/<mod_name>/`
- Fallback: kompletter Inhalt → `red4ext/plugins/<mod_name>/`
- Loggt alles nach `~/cp77-modding/sort-downloads.log`

Wichtige Nexus Mod IDs für NG+ Setup:
| Mod | ID | Install-Pfad |
|---|---|---|
| New Game Plus - Native | 15043 | `red4ext/plugins/New Game Plus/` |
| Mod Settings | 4885 | `red4ext/plugins/ModSettings/` |
| redscript | 1511 | `red4ext/plugins/redscript/` |