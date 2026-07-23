# Browser Cookie Persistence — Brave/Chrome/Chromium-basierte

Wenn sich der User beschwert "kann mich nicht mehr einloggen" oder "Google erkennt Gerät nicht",
liegt es häufig NICHT am Passwort, sondern an **aggressivem Cookie-Cleanup** moderner
Anti-Tracking-Browser (Brave 149+, LibreWolf, ungoogled-chromium, Arc, etc.).

Dieses Dokument zeigt den Diagnose-Workflow am Beispiel Brave — gilt sinngemäß für alle
Chromium-basierten Browser mit Sync-Feature.

## Das Symptom

- Login funktioniert kurz nach Logout / Restart
- Nach Stunden oder Tagen: "Bitte neu anmelden" auf Google/GitHub/Slack/etc.
- Cookie-DB hat viele Rows für `accounts.google.com`, aber **Werte sind leer**
- Brave/Chrome meldet sich selbst als "neues Gerät"

## Warum das passiert

Anti-Tracking-Browser haben einen Mechanismus, der **old-Google-Logins bereinigt**:

- Brave 149+: `were_old_google_logins_removed: true` in Preferences → Cleanup passiert
- Firefox: ähnlicher Mechanismus via `network.cookie.thirdparty.sessionOnly` Default
- Arc/Chromium: `Third-Party-Cookies = Blocked in Incognito` Settings

**Auslöser:** Sync ist nicht aktiv (oder nur teil-aktiv).

## Schnelle Diagnose (1-2 Minuten)

```bash
# 1. Cookie-DB-Pfad finden (Brave als Beispiel)
COOKIES=~/.config/BraveSoftware/Brave-Browser/Default/Cookies
[ -f "$COOKIES" ] || COOKIES=~/.config/chromium/Default/Cookies   # Chromium
[ -f "$COOKIES" ] || COOKIES=$HOME/.config/google-chrome/Default/Cookles  # Chrome

# 2. Werte-Längen pro Google-Cookie auslesen (leer = 0)
sqlite3 "$COOKIES" \
  "SELECT host_key, name, length(value) FROM cookies
   WHERE host_key LIKE '%google%' OR host_key LIKE '%accounts.google%'
   ORDER BY host_key, name LIMIT 30"

# ⛔ Wenn value_length = 0 über mehrere Cookie-Rows → Browser putt sie regelmäßig leer
# ✅ Wenn value_length > 0 → Login-Cookies sind intakt, Problem liegt woanders
```

## Sync-Status prüfen

```bash
python3 << 'EOF'
import json, os
home = os.environ['HOME']
pref_path = f"{home}/.config/BraveSoftware/Brave-Browser/Default/Preferences"
with open(pref_path) as f:
    d = json.load(f)
sync = d.get('sync', {})
print(f"Sync_Enabled: {sync.get('is_sync_enabled', False)}")
print(f"brave_sync_v2.seed vorhanden: {bool(d.get('brave_sync_v2', {}).get('seed'))}")
print(f"sync_types aktiv: {d.get('dual_layer_user_pref_store', {}).get('user_selected_sync_types', [])}")
EOF

# ⛔ Häufigstes Bild:
# sync_types: ["preferences", "typedUrls"]  ← nur 2 von 9 möglichen
# were_old_google_logins_removed: true
```

## Symptom-Checkliste

| Befund | Bedeutung |
|--------|-----------|
| `seed` fehlt | Sync war nie aktiv → Browser ist "anonymes Gerät" für alle Services |
| `seed` da, `sync_types` nur 2 | Sync angelegt, aber im Setup-Wizard zu schnell durchgeklickt |
| `were_old_google_logins_removed: true` | Cleanup-Mechanismus läuft, wird bei aktivem Sync deaktiviert |
| Alle Cookies haben `value_length = 0` | Cleanup war erfolgreich → User muss sich neu einloggen |

## Fix-Workflow: Brave Sync sauber einrichten

### Schritt 1 — User-Anleitung (manuell)

1. `brave://settings/braveSync/setup` im neuen Tab öffnen
2. "Neues Sync-Konto" → "Computer"
3. **24-Wort-Recovery-Code aufschreiben** (in KeepassXC oder Papier!)
4. Sync läuft, danach bei Google neu einloggen + "Dieses Gerät merken" anklicken

### Schritt 2 — Dem User die Sync-Typen explizit nennen

Default landet oft nur auf `preferences` + `typedUrls`. User MUSS diese aktivieren:
- ✅ Preferences
- ✅ Bookmarks
- ✅ History
- ✅ Tabs
- ✅ Extensions
- ✅ Passwords
- ✅ Autofill
- ✅ Reading List

### Schritt 3 — Brave komplett neu starten

Ctrl+Shift+Q (Quit komplett, kein Restore-Session). Sonst persistiert der Flag nicht.

## Pitfalls

- **Cookies werden NICHT synchronisiert** zwischen Geräten (by Design, Datenschutz).
  Sync ändert NUR das Verhalten des Cleanups, nicht die Cookies selbst.
- **Brave Sync ≠ Google Sync.** Brave hat eigene Encryption, eigenes Backend.
- **Brave-Fehler 144.1.86+**: `Sync Enabled: False` im Preferences obwohl es läuft.
  Wahrer Indikator: `brave_sync_v2.seed` vorhanden.
- **Wayland + Browser** kann Login-Popups anders behandeln als X11.

## Workaround wenn Sync nicht möglich

Falls User Sync ablehnt (Privacy-Concern) oder keinen Account anlegen will:

1. **Hauptfix:** Browser-Konfiguration → `chrome://settings/cookies` → "Alle Cookies erlauben"
2. **Oder:** Domain-Whitelist: `accounts.google.com` + `*.google.com` explicit erlauben
3. **Oder:** Stündlicher Reload der Login-Seite erzwingt neuen Auth-Pin

## Diagnose-Screenshot ohne xdotool

Oft brauchst du einen Screenshot eines bestimmten X11-Fensters, aber **xdotool / gnome-screenshot / scrot sind nicht installiert** oder wegen Sudo-Requirement nicht verfügbar.

Lösung mit reinen X11-Standardtools + ImageMagick:

```bash
# 1. Welche Fenster hat die App / wo ist das Haupt-Fenster?
DISPLAY=:1 xwininfo -root -tree 2>&1 | grep -E "<app-name>"

#   Beispiel-Output:
#     0x4400005 "MainWindow": ("app.exe")  1432x740+4+421  +4+421
#     0x4e00005 "Error": ("app.exe")  354x292+47+73   ← modal error
#     (mehrere 1x1-Fenster für Electron IPC)

# 2. Welche Fenster-IDs haben Map-State "IsViewable" (also sichtbar)?
DISPLAY=:1 xwininfo -id 0x4400005 | grep -E "Map State|Width|Height"

# 3. Screenshot eines bestimmten Fensters
DISPLAY=:1 xwd -id 0x4400005 -out /tmp/snap.xwd      # X11 standard
convert /tmp/snap.xwd /tmp/snap.png                    # ImageMagick decodiert

# 4. ⚠️ Pitfall: xwd bricht mit "BadColor" / "BadMatch" ab wenn Fenster noch
#    nicht gemappt ist → dann kein Screenshot möglich. Andere Window-ID testen.
```

**Falls `xwd` auch fehlt:**

```bash
# Variante 1: import (ImageMagick CLI)
DISPLAY=:1 import -window 0x4400005 /tmp/snap.png

# Variante 2: gnome-screenshot (falls verfügbar)
DISPLAY=:1 gnome-screenshot -f /tmp/snap.png

# Variante 3: Pipe-Pattern für Headless-Server
# → Wayland: `grim -g '0,0 1920x1080' /tmp/snap.png` (Pipewire-basierte Distros)
```

## Verwandte Diagnose-CookiesDB-Commands

```bash
# Größte Cookies-DB nach Host (welche Services sind aktiv)
sqlite3 ~/.config/BraveSoftware/Brave-Browser/Default/Cookies \
  "SELECT host_key, count(*) FROM cookies
   GROUP BY host_key ORDER BY count(*) DESC LIMIT 15"

# Welche Auth-Cookies haben nicht-leere Werte? (= wirklich eingeloggt)
sqlite3 ~/.config/BraveSoftware/Brave-Browser/Default/Cookies \
  "SELECT host_key, name, datetime(last_access_utc/1000000 + strftime('%s','1601-01-01'), 'unixepoch')
   FROM cookies
   WHERE host_key LIKE '%google%' AND length(value) > 0
   ORDER BY last_access_utc DESC LIMIT 10"

# Was wurde in den letzten 24h gelöscht? (via Tombstone-Mechanismus)
# — Bei Chromium gibt es keine "gelöschten" Cookies, weil sie ge-cleanupt werden.
# Stattdessen: Time-since-last-cleanup via CT-Header auf jedem Request.
```

## Quellen

- Brave Sync internals: `~/.config/BraveSoftware/Brave-Browser/Default/Sync Data/` zeigt wo Brave die Brave-Encryption-Keys speichert
- Chromium Cookie-Cleanup-Mechanismus: `chrome/browser/net/cookie_cleanup_factory.cc`
- Brave Desktop Sync-Doku: https://github.com/brave/brave-browser/wiki/Brave-Sync
- Sessions: 2026-07-03 MiniMax Hub und Brave Login-Loops
