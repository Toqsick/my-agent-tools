# Brave: White-Screen bei Drittanbieter-Logins (OAuth/SSO)

> Symptom: Du klickst auf den Login-Link einer Electron-App
> (z.B. `account.minimax.io/unified-login`) den die App dir per Deeplink
> gibt, der Browser öffnet ihn — und du siehst nur eine weiße Seite.
> Der Server liefert HTTP 200 mit valides HTML/JS — alle Scripts
> von `cdn.<app>.com` reachable, aber Next.js bleibt im Loading-Spinner
> hängen (`BAILOUT_TO_CLIENT_SIDE_RENDERING`).

## Schnell-Diagnose

```bash
# Server liefert was?
curl -sL -o /tmp/login.html -w "HTTP %{http_code}\n" \
  https://<login-domain>/<path>

# Server-side JS/CSS reachable?
HTML=$(cat /tmp/login.html)
grep -oE 'src="https?://[^"]+' <<< "$HTML" | sort -u | while read url; do
  curl -s -o /dev/null -w "%{http_code}  $url\n" "$url"
done
```

**Typisches Ergebnis:** Server liefert 200 + alle CDN-Scripts 200, **aber**
Google Tag Manager (`googletagmanager.com/gtag/js`) antwortet mit `000` (Timeout).

## Ursache

1. Browser ist **Brave mit installierten Filter-Extensions**
   (uBlock Origin, uMatrix, Cookie-AutoDelete, Script-Blocker etc.)
2. Brave-Shields blockt den Tracking-Script (gtag.js)
3. Die Web-App ist ein **Next.js-SPA mit Client-Side-Rendering**
4. Beim Boot prüft Next.js: ist gtag.js geladen? Nein → BAILOUT_TO_CLIENT_SIDE_RENDERING
5. Statt Fallback zu SSR bleibt die Seite im Loading-Spinner
6. **WICHTIG:** Nur **Shields ausschalten reicht NICHT** — die Filter-Extensions
   blocken Resource-Loading auf DOM-Level (webRequestBlocking, declarativeNetRequest)
   das über die normale Tab-Cookie-Schicht läuft.

## Verifikation

```bash
# Welche Filter-Extensions sind installiert?
ls ~/.config/BraveSoftware/Brave-Browser/Default/Extensions/ | head -20

# Besonders aggressiv (blocken Scripts):
# - jcokkipkhhgiakinbnnplhkdbjbgcgpe  → uBlock Origin
# - fplfeajmkijmaeldaknocljmmoebdgmk  → uMatrix
# - mlomiejdfkolichcflejclcbmpeaniij  → Manifest-V3-Blocker
# - knpfogmkplfinkdfehonaelmgjganbia  → Cookie-AutoDelete
```

## Lösungen

### 1. Inkognito-Modus (schnellste, 30 Sek)

Inkognito-Tab (`Ctrl+Shift+N`) deaktiviert alle Extensions standardmäßig.
Shields-Toggle im Inkognito macht das Tab zur Clean-Slate-Browser-Session.

```
1. Ctrl+Shift+N → Inkognito-Fenster
2. Login-URL in Adressbar einfügen
3. Shields für login-domain auf AUS (falls noch aktiv)
4. Login durchführen
5. Tab bleibt offen bis Wine-App den Token übernimmt
```

Nachteil: Cookie lebt nur bis Tab geschlossen wird. Token muss zur App
übertragen werden **bevor** der Tab zu ist.

### 2. Dediziertes Brave-Profil ohne Extensions (dauerhafter)

```bash
# Profil anlegen über chrome://settings/people oder CLI:
brave --user-data-dir=/home/bratan/.brave-login --no-first-run
```

In diesem Profil **keine** Extensions installieren. Ist persistent,
kann Sync'd werden, gewinnt Login-Daten normal.

### 3. Filter-Whitelist für die Login-Domain (5 Min)

In uBlock Origin → Filter Lists → Custom Filters:

```
@@||account.<app>.com^$important
@@||cdn.<app>.com^$important
@@||<app>.com/auth^$important
```

Erfordert Browser-Neustart. Whitelisted bleibt dauerhaft.

### 4. Alternative Browser (kein Setup)

Falls nur eine einmalige Login nötig:
- Firefox (deutlich weniger Extensions installiert)
- Chromium-Vanilla (Flatpak: `org.chromium.Chromium`)
- GNOME-Web (Flatpak: `org.gnome.Epiphany`) — Trackings-Blocker minimal

## OAuth-State-Token lesen (vor dem White-Screen-Check)

Bevor du irgendwas tust, prüfe das **Login-URL** selbst:

```python
import base64, urllib.parse, json

url = "https://account.<app>.io/unified-login?login_redirect=%2Foauth2%2Fauthorize%3F..."
state = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['login_redirect'][0]
oauth2 = urllib.parse.parse_qs(state)
state_b64 = oauth2['state'][0] + '=' * (4 - len(oauth2['state'][0]) % 4)
state_json = json.loads(base64.b64decode(state_b64))

print(json.dumps(state_json, indent=2))
# → zeigt: device_id, biz_id, version_code, back-url, ...
```

Damit weißt du:
- **Welcher OAuth-Provider** (Feishu, Google, Microsoft, GitHub)
- Welche **App/Electron-Version** das Token erwartet
- Welche **device_id** die App erwartet (Login muss vom selben Device kommen)

## Pitfalls

1. **Shields aus ist NICHT genug** — Filter-Extensions wirken tiefer als die Tab-Cookie-Schicht
2. **andere Inkognito-Tabs helfen nicht** — der Token muss zum Wine-App-Prozess fließen
3. **uBlock default-Filterlisten** blocken gtag auch ohne dass du das merkst
4. **Whitelist nicht persistent** wenn du später Browser-Reset machst
5. **Andere Filter-Extensions** (uBlock Lite, AdGuard, Ghostery etc.) können genauso blocken — nicht nur die offensichtlichen

## Quellen

- Brave Help Center: "Why am I getting ERR_BLOCKED_BY_CLIENT?"
- uBlock Origin: "Advanced mode dynamic filtering"
- Session 2026-07-03: MiniMax Hub `account.minimax.io/unified-login` white-screen unter Brave 149 mit installiertem uBlock Origin + uMatrix + 14 weiteren Extensions
