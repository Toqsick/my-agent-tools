# MiniMax Code 3.0.47 — Login-Flow & Endpoints (Session 2026-07-08)

## App-Identität

- **ProductName:** "MiniMax Code" (FileVersion 3.0.47.67)
- **CompanyName:** MiniMax
- **Bundle:** Electron (.asar), Wine 11.11, Wine-Chromium 140
- **Bottle:** Shared mit MiniMax Hub (`MiniMax-Hub`)
- **Installer:** NSIS 3.04 (Nullsoft), silent `/S` hängt (EBADF-Bug)

## Login-Endpoints (agent.minimax.io/matrix/api/v1)

| Endpoint | Methode | Zweck |
|---|---|---|
| `/user/login/sms/send` | POST | SMS-Code anfordern |
| `/user/login/phone` | POST | Phone + Code einloggen |
| `/user/getOpenData` | GET | User-Profile abrufen |
| `/user/info` | GET | User-Info |
| `/chat/desktop_heartbeat` | POST | Heartbeat alle 6-10s |

## Login-Typen (aus app.asar)

| Konstante | Wert | Bedeutung |
|---|---|---|
| `LOGINTYPEPHONE` | `""` | Phone-Login (default) |
| `LOGINTYPEANDROIDONECLICK` | `"1"` | Android One-Click |
| `LOGINTYPEIOSONECLICK` | `"2"` | iOS One-Click |
| `LOGINTYPEANONYMOUS` | `"3"` | Anonym (Gast) |
| `LOGINTYPETHIRDPART` | `"5"` | Third-Party |
| `GITHUB` | `"8"` | GitHub OAuth |
| `FIREBASE` | `"11"` | Firebase |
| `PASSWORD` | `"20"` | Passwort |
| `EMAIL_CODE` | `"21"` | Email-Code |
| `SUB_ACCOUNT` | `"9"` | Sub-Account |

## Login-URL

`https://agent.minimax.io/login?sso=1&download_source=default`

## Custom-Protocol-Callback

`minimax-code://auth-callback?code=...&state=...`

Registriert via Desktop-File + xdg-mime in dieser Session.

## Auth-Domains

| Domain | Cookie |
|---|---|
| `agent.minimax.io` | `_token`, `_oauth_state` |
| `account.minimax.io` | `_sid` |
| `www.minimax.io` | `_token` |
| `platform.minimax.io` | `_token` |

## Config-Injection-Pfad

```
$WINEPREFIX/drive_c/users/$USER/AppData/Roaming/MiniMax Agent/
  minimax-agent-config.json     # Haupt-Config (tokens, localStorageConfig)
  logs/main-YYYY-MM-DD.log      # Electron-Logs
  logs/renderer-YYYY-MM-DD.log
  Network/Cookies                # Chromium-Cookie-Storage (SQLite)
  Local Storage/leveldb/         # Electron-LevelDB (falls genutzt)
```

## Config-JSON-Struktur

```json
{
  "tokens": {
    "accessToken": "...",
    "refreshToken": "..."
  },
  "localStorageConfig": {
    "isOnboardingCompleted": true,
    "showWebChatHistoryTips": false
  }
}
```

## Heartbeat

- **Endpoint:** `agent.minimax.io/matrix/api/v1/chat/desktop_heartbeat`
- **Intervall:** 6-10s (stabil unter Wine)
- **HotUpdate:** `https://file.cdn.minimax.io/public/minimax-agent/hot-update/en/prod/manifest.json`

## Wine-Prozess-Struktur (bei laufender App)

- `MiniMax Code.exe` (main)
- `MiniMax Code.exe --type=gpu-process`
- `MiniMax Code.exe --type=network-service`
- `MiniMax Code.exe --type=renderer` (×2)
- `wineserver` (Wine-Infrastruktur)

## Artefakte (erstellt in dieser Session)

- `~/50-System/bin/minimax-code` — PTY-Launcher
- `~/50-System/bin/minimax-code-url-handler` — Custom-Protocol-Handler
- `~/.local/share/applications/minimax-code.desktop`
- `~/.local/share/applications/minimax-code-url-handler.desktop`
- `~/docs/system/minimax-code-bottles-2026-07-08.md` — komplette Install-Doku

## Bekannte Probleme

1. **Screenshots unter Wayland:** `import -window` liefert leeres Bild,
   `scrot` nimmt den ganzen Screen. Kein direkter App-Screenshot möglich.
2. **Login-Token-Injection pending:** App ist gestartet, Login-Screen erscheint,
   Social-Login geht auf Server-Seite durch, aber Token kommt nicht zurück
   weil Custom-Protocol-Handler fehlte. Handler ist jetzt registriert —
   beim nächsten Versuch sollte es funktionieren.
3. **Chromium v10 Cookies:** `encrypted_value` statt Klartext — kann nicht
   einfach aus der SQLite gelesen werden. Alternative: DevTools.