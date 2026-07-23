# Electron-App OAuth-Deeplink unter Linux — Ende-zu-Ende-Login-Flow

> Wie eine Electron-App via OAuth/SSO Login das Token aus dem Browser zurückbekommt,
> wenn Wine-X11 den Browser-Popup nicht durchschalten kann.
> Konkretes Rezept am Beispiel MiniMax Hub (HailuoAI), aber generisch anwendbar auf
> jede Electron-App die `app<name>://auth-callback?accessToken=...` als Deeplink nutzt.

## Das Problem in einem Satz

Electron-Apps brauchen Login-Token vom Browser. Wine öffnet den Browser-Popup falsch.
**Ende-zu-Ende-Lösung:** Linux-Distribution-Handler (xdg-mime + .desktop) registrieren +
PTY-Wrapper für die App + ggf. Env-Var-Injection für Server-Token.

## Architektur — Was wofür da sein muss

```
[Browser-Tab mit deeplink://auth-callback?accessToken=XYZ]
                  │
                  ├── xdg-open → fragt XDG nach URL-Schema
                  │
                  └── .desktop-File registriert für x-scheme-handler/<scheme>
                       │
                       └── Exec=...wine App.exe %u
                            │
                            └── Wine-Prozess nimmt deeplink-Arg entgegen
                                 (App liest process.argv[1])
```

**Beide Hälften MÜSSEN da sein:**
1. Wine-App muss deeplink-Argumente akzeptieren (Electron liest sie aus process.argv)
2. xdg-mime/.desktop muss Wine-App mit dem Argumenten starten können

## Schritt 1: Welchen URL-Scheme erwartet die App?

**Reverse-engineering der App-asar-Dateien** zeigt die App-Web-Seite, die sie beim Login
als Bridge benutzt. Beispiel MiniMax Hub:

```javascript
// Aus /hub.minimax.io/login JavaScript (gefunden via curl + strings auf der HTML):
var HOST_CONFIG = {
  'hub.minimax.io': { account: '...', scheme: 'minimax-hub' },
  'hub.minimaxi.com': { account: '...', scheme: 'minimax-hub-cn' },
  // ...
};
function openHubDeeplink(token) {
  var url = HUB_SCHEME + 'auth-callback?accessToken=' + encodeURIComponent(token);
  // → "minimax-hub://auth-callback?accessToken=XYZ"
}
```

Pattern-Hinweise:
- `HOST_CONFIG` mappt Hub-Domain → Login-Domain → URL-Schemata
- Deeplink-Format fast immer: `<scheme>://auth-callback?accessToken=<token>`
- Manche Apps: `<scheme>://oauth/callback?code=...&state=...` (Standard-OAuth2)

**Herausfinden ohne Web-Source:**
```bash
# Strings aus asar extrahieren, nach Scheme + Callback suchen
strings ~/.var/app/com.usebottles.bottles/data/bottles/bottles/<bottle>/drive_c/<app>/resources/app.asar \
  | grep -iE 'x-scheme-handler|registerScheme|setAsDefaultProtocolClient|deeplink|callback' \
  | head -20

# → typische Funde: "minimax-hub", "hailuoai-callback", "<app>://auth"
```

## Schritt 2: .desktop-File für den URL-Schema-Handler erstellen

Linux braucht ein MIME-Type-Mapping. Drei Files:

```bash
# ~/.local/share/applications/<app-name>-url-handler.desktop
[Desktop Entry]
Name=<App> URL Handler
Exec=/home/bratan/.var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64/bin/wine 'Z:\\<app-dir>\\<app>.exe' --no-sandbox %u
Type=Application
MimeType=x-scheme-handler/<scheme>;
NoDisplay=true
```

```bash
# Registrieren:
update-desktop-database ~/.local/share/applications/
xdg-mime default <app-name>-url-handler.desktop x-scheme-handler/<scheme>
```

**Wichtig: `%u` ist der Platzhalter für die URL!** Ohne ihn kommt die URL nicht bei
der App an.

## Schritt 3: Wine-Prozess akzeptiert deeplink-Argument

Electron liest `process.argv` für deeplink-URLs:
```javascript
// In der App-Source-Code:
app.setAsDefaultProtocolClient('minimax-hub');
app.on('open-url', (event, url) => { /* macOS */ });
app.on('second-instance', (event, argv) => {
  // Windows/Linux: URL ist in argv[argv.length - 1]
  const url = argv[argv.length - 1];
  // ...
});
```

**Heißt:** Wenn wir `wine app.exe minimax-hub://auth-callback?accessToken=XYZ` aufrufen,
bekommt die App den URL-String über `process.argv`. Die App-CLI muss also den URL
als Argument weitergeben.

## Schritt 4: Manuelles Triggern (wenn Browser→xdg→Wine-Kette klemmt)

```bash
# Direkt mit Wine:
~/.var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64/bin/wine \
  'Z:\\MiniMax-Hub\\MiniMax Hub.exe' --no-sandbox 'minimax-hub://auth-callback?accessToken=XYZ'

# Oder via xdg-open (testet den ganzen OS-Handler-Stack):
xdg-open 'minimax-hub://auth-callback?accessToken=XYZ'
```

## Diagnose-Matrix für "Login klappt nicht in Wine"

| Symptom | Wahrscheinliche Ursache | Fix |
|---------|------------------------|-----|
| Wine-App crashed bei OAuth-Popup | Node-Stdio-EBADF | PTY-Wrapper (siehe windows-apps-on-linux.md) |
| Browser öffnet, Login-Form da, "In App öffnen" tut nix | xdg-mime-Handler nicht registriert | Schritt 2 oben |
| "In App öffnen" öffnet andere App | Default-App für Scheme falsch zugeordnet | `xdg-mime default <app>.desktop x-scheme-handler/<scheme>` |
| Wine-App öffnet, aber kein Token | App-Code erwartet andere URL-Form | strings auf asar prüfen, deeplink-Format vergleichen |
| Token in Browser-Cookies aber App-Env-Var leer | Env-Var-Injection nicht aktiv | Token-Datei anlegen, App neu starten |
| Login macht nichts (Spinner dreht endlos) | Token-Validierung schlägt fehl | Token-Decode: `eyJ...` → JWT-Expiration-Check (`tokenValid()` aus Login-Script) |

## Konkretes Beispiel: MiniMax Hub

**Login-URL die Wine App erzeugt:**
```
https://hub.minimax.io/login?device_id=5dc9bb85-...&version_code=1.0.7
```

**Login-Flow:**
1. User klickt "Click to log in" in Wine-App
2. Wine öffnet `hub.minimax.io/login?device_id=...` im Browser
3. Browser checkt `_token`-Cookie. Leer (kein HailuoAI-Login)
4. Browser redirectet zu `account.minimax.io/unified-login?...` (Hailuo Login)
5. Hailuo-Login + Zustimmung → Callback `hub.minimax.io/auth/callback?code=...`
6. Hub setzt `_token`-Cookie
7. Hub redirectet zu `hub.minimax.io/login?device_id=...` mit Token
8. Hub's JS-Code liest Token, baut `minimax-hub://auth-callback?accessToken=...`
9. `location.href = ...` triggert xdg-open → .desktop File → Wine

**Wichtig:** Schritt 8 ist der einzige der **ohne Browser-Plugin** durchgeht.

## White-Screen-Varianten (klassische Verwechslung)

Oft werden diese Symptome miteinander verwechselt:

| Was du siehst | Was es bedeutet | Echte Ursache |
|---------------|---------------|---------------|
| Wine-Fenster 354×292 mit Titel "Error" | Electron-Default-Error-Dialog | Login-Token fehlt — App wartet, ist NICHT gecrasht |
| Wine-Fenster 1432×740 Haupt-UI | App läuft normal | Login noch nicht passiert |
| Wine-Fenster mit Logs im Hintergrund aber Titel "Error" | Electron Error-Modal | App-Code crashed beim Token-Laden — Stack-Trace in `main-*.log` |

**Diagnose-Trick:** Erst `pgrep -af "wine"` + `wmctrl -lp` → wenn PID lebt, lebt die App.
Dann `tail -25 ~/.var/app/com.usebottles.bottles/data/bottles/bottles/<bottle>/drive_c/users/<user>/AppData/Roaming/<vendor>/<app>/logs/main-$(date +%m-%d).log` →
Was steht da? `[config] userToken resolved: (empty)` = Login fehlt.

## Patterns aus dieser Lektion

1. **Electron-Apps in Wine brauchen sowohl PTY-Wrapper ALS AUCH xdg-mime-Handler.**
   Beide Hälften der Login-Brücke müssen funktionieren.

2. **Die Login-JS im Browser-UI ist häufig die einzige zuverlässige Doku.**
   Sie enthält den exakten Deeplink-Format. Strings-re extract über `curl + HTML-Parsing`
   schlägt `grep auf der Web-Side` weil die HTML inline initial-state-Daten enthält.

3. **OAuth-Tokens werden in drei Schichten bewegt:**
   - Browser-Cookies (Web-Auth-Layer)
   - `host.docker.internal`-artige Bridge-Cookies (`hub.minimax.io/_token`)
   - Electron-interner Storage (`globalStorage.get("tokens").accessToken`)

   Jede Schicht muss funktionieren, sonst bleibt der Login hängen.

4. **Wine-Bridge-Cookies (`hub.minimax.io/_token`) sind vom Host-Network aus unsichtbar.**
   Das Wine-Loopback ist localhost-intern. Wir müssen den Token durch die
   App-CLI-Args, Env-Vars oder xdg-URL-Schemes fließen lassen.

## Quick-Test ob der ganze Login-Flow steht

```bash
# 1. Wine-App neu starten
~/.var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64/bin/wineserver -k
<pty-launcher>  # App startet ohne PTY-EBADF-Crash

# 2. Browser-Login via Inkognito:
xdg-open 'https://account.minimax.io/unified-login?login_redirect=%2Foauth2%2Fauthorize%3Fclient_id%3Dhub%26redirect_uri%3Dhttps%253A%252F%252Fhub.minimax.io%252Fauth%252Fcallback%26response_type%3Dcode%26state%3DSTATE_TOKEN'

# 3. HailuoAI Login-Form ausfüllen + 2FA
# 4. Bei "Open in App" auf "Open MiniMax Hub" klicken
# 5. Wine-App muss Empfang bestätigen via:
tail -f ~/.var/app/com.usebottles.bottles/data/bottles/bottles/<bottle>/drive_c/users/<user>/AppData/Roaming/@hilo/MiniMax\ Hub\ Global/logs/main-$(date +%m-%d).log \
  | grep -E 'userToken|auth_login|deeplink'
```

Login erfolgreich wenn:
- `[config] userToken resolved: (empty)` verschwindet
- Stattdessen: `[config] userToken resolved: eyJhbGc...`
- App-Ui zeigt Avatar/Username in der Sidebar unten links

## Woanders weiterlesen

- `references/windows-apps-on-linux.md` — Electron-App-Grundsetup (PTY-Wrapper, Runner, Bundle-Extract)
- `references/brave-third-party-login-white-screen.md` — White-Screen-Login-Falle (Browser-side)
- `references/vpn-dns-block-brave-shields.md` — System-DNS-Block der Browser-Seite blockt
