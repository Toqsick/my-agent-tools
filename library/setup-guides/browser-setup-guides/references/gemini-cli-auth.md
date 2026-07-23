# Gemini CLI Auth-Setup (Google AI Pro Abo)

**Stand:** 2026-07-05 (Basti Session)
**Tool:** `@google/gemini-cli` v0.49.0 (npm global install)
**Kontext:** Basti hat Google AI Pro Abo, will Gemini-Modelle aus dem Terminal nutzen.

## TL;DR

**OAuth-Variante funktioniert NICHT mehr** für individuals — Gemini CLI v0.49.0 ist für Code-Assist-OAuth deprecated. Google hat auf "Antigravity" migriert. **→ API-Key-Variante ist der einzige stabile Weg** für Bastis Pro-Abo.

## Installations-Kommandos

```bash
# Installation (Node 20+ vorausgesetzt, npm global)
npm install -g @google/gemini-cli

# Verifikation
which gemini && gemini --version    # sollte 0.49.0 oder neuer zeigen
```

## Auth-Varianten — welche wann?

### A. OAuth "Sign in with Google" — **DEPRECATED für individuals**

```bash
gemini
# Menü: "Sign in with Google" → Browser-Login oder NO_BROWSER=true
```

**Was passiert nach Login:** Google akzeptiert den Token, dann aber:
> *"This client is no longer supported for Gemini Code Assist for individuals. To continue using Gemini, please migrate to the Antigravity suite of products: https://antigravity.google"*

→ Eingeloggt, aber **kein einziger API-Call funktioniert**. Migration auf Antigravity nötig (Stand 2026-07-05 noch unbekannt welche Form das hat — neue CLI? VSCode-Plugin? Web?).

### B. API-Key über AI Studio — **EMPFOHLEN für Basti**

**Schritt 1: Key generieren**
- Geh auf https://aistudio.google.com/apikey
- "Create API key" → Key kopieren
- ⚠️ Key **NIEMALS im Chat pasten**, nur lokal in `.env` einfügen

**Schritt 2: Settings umstellen**

```bash
# ~/.gemini/settings.json muss auf API-Key-Modus stehen:
cat ~/.gemini/settings.json
# {
#   "security": {
#     "auth": {
#       "selectedType": "gemini-api-key"
#     }
#   }
# }
```

Falls noch auf oauth-personal: `selectedType` auf `gemini-api-key` ändern.

**Schritt 3: Key in .env schreiben**

```bash
touch ~/.gemini/.env && chmod 600 ~/.gemini/.env
nano ~/.gemini/.env
# Inhalt:
# GEMINI_API_KEY=<dein-key-aus-aistudio>
# Optional (für OAuth-Fallback-Modi):
# GOOGLE_OAUTH_CLIENT_ID=...
# GOOGLE_OAUTH_CLIENT_SECRET=...
```

**Schritt 4: Test**

```bash
# Schnell (Flash-Modell):
gemini -m gemini-2.5-flash -p "Hallo, nenne dein Modell in einem Satz"

# Volle Power (Pro Preview, das die TUI rechts unten anzeigt):
gemini -m gemini-3.1-pro-preview -p "Komplexer Coding-Task..."
```

Modell-Verfügbarkeit prüfen: in interaktiver TUI rechts unten auf `/model` klicken — Liste zeigt alle Modelle die der Key/Account nutzen darf.

### C. Vertex AI — **nicht relevant für Basti**

Nur wenn GCP-Projekt mit aktiviertem Billing + Vertex AI API. overkill für Bastis Setup.

## Häufige Fehler

| Fehler | Ursache | Fix |
|---|---|---|
| `API_KEY_INVALID` (Status 400) | Key ist gesperrt/abgelaufen oder nie in `.env` geschrieben | Neuen Key in AI Studio generieren, in `~/.gemini/.env` eintragen |
| OAuth-URL "malformed request" beim Klicken | Chat-Rendering hat URL kaputt gemacht (`%20` → Space, lange Params truncated) | **Im eigenen Terminal** `NO_BROWSER=true gemini` ausführen, URL lokal kopieren |
| "Failed to sign in. Authentication consent could not be obtained" | Hermes-Hintergrund-TTY kann keinen Browser öffnen | Im normalen Terminal (zorin-terminal) ausführen, oder NO_BROWSER=true |
| OAuth-Login klappt, aber jeder API-Call sagt "This client is no longer supported" | Gemini CLI v0.49.0 für individuals deprecated | Auf **API-Key-Variante (B)** umsteigen, OAuth ist tot |
| "Manual authorization is required but the current session is non-interactive" | CLI hat kein TTY (Pipe/head/redirection killt PTY) | TUI direkt starten oder `pty=true` für Bash-Tool nutzen |

## Sicherheits-Notiz

- `~/.gemini/.env` immer `chmod 600` — die Datei enthält API-Keys
- `~/.gemini/google_accounts.json` enthält OAuth-Tokens — auch sensible Datei
- API-Keys die im Chat landen → bei Google rotieren! (https://aistudio.google.com/apikey → löschen + neu)
- OAuth-Client-ID/Secret sind **kein Geheimnis** (public im CLI-Repo), nur API-Key + OAuth-Tokens sind sensibel

## Tool-Pfade

| Was | Wo |
|---|---|
| CLI Binary | `~/.nvm/versions/node/v20.20.2/bin/gemini` (oder `/usr/local/bin/gemini`) |
| Settings | `~/.gemini/settings.json` |
| API-Key | `~/.gemini/.env` (mode 600) |
| OAuth-Tokens | `~/.gemini/google_accounts.json` |
| History | `~/.gemini/history/` |
| Logs / tmp | `~/.gemini/tmp/` |