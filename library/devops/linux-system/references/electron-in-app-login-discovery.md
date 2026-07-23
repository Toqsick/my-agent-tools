# In-App Electron Login: Built-in Login Page (Next.js Renderer)

> Alternative zum externen OAuth-Deeplink: Manche Electron-Apps haben einen **eigenen Login-Screen
> direkt im Electron-Renderer** (als Next.js/React-Webapp in `app.asar`), der gegen API-Endpoints
> authentifiziert — **kein externer Browser** nötig.
> Konkretes Rezept am Beispiel MiniMax Code 3.0.47, aber generisch anwendbar.

## Das Problem in einem Satz

Externe OAuth-Deeplink-Setups (siehe `references/electron-oauth-deeplink-linux.md`) brauchen
Browser + xdg-mime + .desktop-Handler + Wine-URL-Arg-Durchschleifung. **In-App-Login-Apps
brauchen NICHTS davon** — der Login-Screen ist Teil der Electron-App selbst und zeigt sich
automatisch im Wine-Fenster.

## Erkennungsmerkmale: In-App-Login vs. Externer-Browser-Login

| Merkmal | In-App-Login | Externer-Browser-Login (Hub) |
|---------|-------------|------------------------------|
| Login erscheint | **Im selben Electron-Fenster** | Neuer Browser-Tab (extern) |
| Erster Start zeigt | Onboarding (3 Punkte-Loader) → Login-Formular | Haupt-UI + Login-Button |
| App-Logs beim Start | `navigateToLogin → type=login window registered` | `[Auth] waiting for OAuth callback` |
| Window-Größe Login | ~688×758 | Externer Browser (variabel) |
| API Targets | `matrix/api/v1/user/login/phone` + `sms/send` | `account.minimax.io/unified-login` |
| Token-Quelle | API-Response (JSON) | Deeplink URL-Scheme |
| Config-Datei | `minimax-agent-config.json` | `%APPDATA%/<vendor>/.../Global/tokens` |
| Browser nötig | ❌ Nein | ✅ Ja |

## Diagnose: So findest du raus, welcher Login-Typ es ist

### Schritt 1: App starten und Logs verfolgen

```bash
LOG_DIR="$BOTTLE/drive_c/users/$USER/AppData/Roaming/<vendor>/<app>/logs"
LOG_FILE="$LOG_DIR/main-$(date +%m-%d).log"
tail -f "$LOG_FILE" 2>/dev/null || echo "Kein main-*.log gefunden — andere Log-Pfade suchen"

# Nach 15-30s Logs analysieren:
grep -E "navigateToLogin|WindowManager.*window.*type=|onboarding|login" "$LOG_FILE"
```

**In-App-Login sieht so aus:**
```
[22:44:30] [WindowManager] Registered window: type=onboarding, id=1
[22:44:47] [Auth] navigateToLogin triggered, source: onboarding:not_logged_in
[22:44:47] [WindowManager] Registered window: type=login, id=2
[22:44:48] [WindowManager] Unregistered window: type=onboarding, id=1
```

**Externer-Browser-Login sieht so aus:**
```
[12:34:56] [Auth] Opening browser: https://account.minimax.io/unified-login?...
[12:34:57] [Auth] Waiting for auth callback (timeout: 120s)
```

### Schritt 2: Config-Datei untersuchen

```bash
CONFIG_FILE="$WINE_DIR/drive_c/users/$USER/AppData/Roaming/<vendor>/<app>/localStorageConfig/*.json"
ls -la "$CONFIG_FILE"

# Typische Keys:
cat "$CONFIG_FILE" | python3 -m json.tool 2>/dev/null
# → {"localStorageConfig": {"isOnboardingCompleted": false, ...}, "tokens": {}}
```

### Schritt 3: Login-Endpoints identifizieren (aus asar oder Logs)

```bash
# Aus den App-Logs: Heartbeats zeigen die API-Basis-URL
grep -oP 'https?://[a-zA-Z0-9._/-]+heartbeat[a-zA-Z0-9._/-]*' "$LOG_FILE" | head -1

# Aus dem asar: Login-API-Endpoints
strings "$APP_ASAR" 2>/dev/null | grep -oP '/matrix/api/v1/user/login/[a-z_/]+' | sort -u
# → /matrix/api/v1/user/login/sms/send, /matrix/api/v1/user/login/phone, ...
```

## Login-Arten (aus dem Enum der App)

| LoginType | Wert | Beschreibung |
|-----------|------|-------------|
| PHONE | 0 | Standard Phone + SMS-Code (region +86 als Default) |
| ANDROID_ONECLICK | 1 | Android-Ein-Klick-Login |
| IOS_ONECLICK | 2 | iOS-Ein-Klick-Login |
| ANONYMOUS | 3 | Anonymer Login (Trial ohne Account) |
| THIRDPART | 5 | Drittanbieter-Login (generisch) |
| GITHUB | 8 | GitHub OAuth |
| FIREBASE | 11 | Firebase Auth |
| PASSWORD | 20 | Email + Password |
| EMAIL_CODE | 21 | Email + Verifikationscode |

MiniMax Code verwendet: UI zeigt vermutlich Phone/Chat-basierte Optionen zuerst
(regionabhängig). GitHub/Email/Password sind über "More options" erreichbar.

## Onboarding-Skip: isOnboardingCompleted

Die Config-Datei hat diesen Key-Prozess:

```json
{"localStorageConfig": {"isOnboardingCompleted": false}, "tokens": {}}
```

**Setzen auf `true`** führt dazu, dass die App das Onboarding überspringt und sofort
zum Login navigiert — nützlich als **Diagnose-Hilfe**:

**Konsequenz:** Die App schließt dann Onboarding sauber (`unregistered window: type=onboarding`),
geht zu Login und — wenn kein Token da ist — beendet sich **sauber und freiwillig**.
Das ist ein sicheres Feature: Coding-Apps ohne Login dürfen nicht in Workspaces schreiben.

## Token-Injection für in-app-login Apps

Bei In-App-Login-Apps läuft der Token-Flow anders als beim externen Deeplink:

```
[User klickt "Sign in" im Wine-Fenster]
  → Electron-Renderer zeigt Login-Formular (Next.js Seite)
  → User gibt Credentials ein
  → POST an agent.minimax.io/matrix/api/v1/user/login/phone
  → Response enthalt accessToken
  → App speichert in electron-store / leveldb / config.json
```

**Manuelle Token-Injection:** Statt Deeplink-Workaround schreibt man Token direkt
in die Config-Datei unter `tokens.accessToken`. Token-Quellen: (1) Manueller Login
im Wine-Fenster, (2) Token aus Host-Browser auf `agent.minimax.io` extrahieren,
(3) Token aus Sibling-App recyceln.

## Der asar-extract Trick für Login-Routes

Da der Login-Screen oft als **Next.js-Seite im `app.asar`** gebündelt ist:

```bash
# asar entpacken
npx --yes -p @electron/asar asar extract "$APP_ASAR" /tmp/asar-extract/
# Login-spezifische Seiten finden
ls /tmp/asar-extract/out/login/ 2>/dev/null
# → index.html, page-XXXX.js (Next.js route)

# Login/Callback URLs in JavaScript suchen
grep -r "login/phone\|login/sms\|/user/login" /tmp/asar-extract/out/ \
  | grep -v node_modules | head -20
```

## Patterns & Lessons

1. **Nicht jede Electron-App braucht externes OAuth.** Manche haben die Login-Seite
   direkt im Electron-Renderer als Next.js/React-App.
2. **Der erste visuelle Hinweis sind die Window-Types in den Logs.** `type=onboarding`
   → `type=login` = In-App-Login. `type=browser` → externes OAuth.
3. **In-App-Login unter Wine funktioniert ohne PTY-Wrapper-xdg-OAuth-Stack.**
4. **Config-Injection ist einfacher** — `minimax-agent-config.json` nimmt Token direkt,
   kein Wine-Registry-Env-Var-Bypass nötig.
5. **Heartbeat-Check bleibt der beste Health-Probe** unabhängig vom Login-Typ.

## Verwandte Referenzen

- `references/electron-oauth-deeplink-linux.md` — Externer OAuth-Deeplink (Gegenstück)
- `references/windows-apps-on-linux.md` — Grundsetup, PTY-Wrapper, Bundle-Extrakt
- MiniMax Code 3.0.47 (2026-07-08) vs. MiniMax Hub 1.0.7 (2026-07-03)