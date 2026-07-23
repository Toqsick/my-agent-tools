---
name: google-oauth-setup
description: "Use when user asks for Google Workspace API setup, OAuth for Gmail/Calendar/Drive, Client Secret configuration. NOT for non-Google APIs or service-account-only setups. Guide for Google Workspace API setup (Gmail, Calendar, Drive) with OAuth."
version: 1.0.0
author: yuno
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - google
    - oauth
    - gmail
    - workspace
    - setup
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['google', 'workspace', 'setup', 'oauth', 'gmail']
keywords: ['google', 'workspace', 'setup', 'oauth', 'gmail']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['google-workspace']
---



# Google Workspace & OAuth Setup

Leitfaden zum Einrichten von Google Workspace API (Gmail, Calendar, Drive) mit OAuth2 via Hermes Agent.

## Voraussetzungen
- Google Cloud Projekt mit OAuth Client ID (Desktop-App Typ)
- Heruntergeladene `client_secret_*.json`
- Python 3.x mit Paketen: `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`

## Setup-Schritte

### 1. Client Secret bereitstellen
```bash
cp ~/Downloads/client_secret_*.json ~/.hermes/google_client_secret.json
```

### 2. OAuth-URL generieren
```bash
python3 ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py --auth-url
```
— URL im Browser des **gleichen Geräts** öffnen, das bei Google eingeloggt ist.

### 3. Google OAuth-Consent Screen konfigurieren (CRITICAL)
Google blockiert selbst erstellte Apps mit **Error 403: access_denied**. Lösung:
1. Öffne [Google Cloud Console - OAuth consent screen](https://console.cloud.google.com/auth/oauth2consent)
2. Stelle sicher, das richtige Projekt ist ausgewählt (ganz oben links)
3. Scroll nach unten zu **"Testbenutzer"**
4. Klick auf **"+ Benutzer hinzufügen"** → eigene E-Mail-Adresse eintragen
5. Klick auf **"+ Hinzufügen"** → Eintrag erscheint in der Liste
6. Ganz nach unten scrollen → **"Speichern"** klicken

### 4. Auth-Code einreichen
Nach Schritt 3:
- OAuth-URL erneut im Browser öffnen
- Google gibt Zugriff frei (erkennt den User als Test)
- Seite landet auf `http://localhost:1/?code=4/0A...`
- **Komplette URL aus der Adresszeile kopieren** (nicht nur den Code!)
- Zurück in Chat: `$GSETUP --auth-code <komplette-URL>`

### 5. Verifizierung
```bash
ls ~/.hermes/google_token.json  # Sollte existieren
```

## Pitfalls & Troubleshooting

### PEP 668: externall-managed-environment
`pip install` scheitert auf Ubuntu/Debian mit:
```
error: externally-managed-environment
```
**Fix:** `pip install --break-system-packages <paket>`
*Oder besser:* `venv` erstellen, aber Root-Privilegien für `apt install python3.x-venv` nötig.

### Docker-Gruppe nach Installation
Nach Docker-Installation zur Docker-Gruppe hinzufügen:
```bash
sudo usermod -aG docker $USER
```
— Neue Shell oder `newgrp docker` nötig damit Groups greifen.

### OAuth Redirect leert
`http://localhost:1` wird leer geladen oder mit Fehler — **das ist normal!** Einfach URL kopieren.

## Referenzen
- `references/oauth-quickref.md` — Kurzübersicht der Schritte
