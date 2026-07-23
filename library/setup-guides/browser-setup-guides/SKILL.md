---
name: browser-setup-guides
description: "Use when user asks for a structured, manual browser setup guide involving OAuth, bot tokens, API keys, billing, or vendor portals. NOT for a simple browser question or an automated browser action. Produces dated step-by-step UI instructions with warnings, a completion checklist, vendor notes, and troubleshooting."
version: 1.0.0
author: agent
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - setup
    - guide
    - discord
    - gcp
    - browser
    - checklist
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['browser', 'vendor', 'browser-setup-guides', 'structured', 'manual']
keywords: ['browser', 'vendor', 'step', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['pretext']
---



# Browser Setup Guides

Für Multi-Schritt Browser-Aufgaben, die manuell durchgeführt werden müssen (Bot-Token, API-Keys, Billing, etc.), wird ein strukturierter Markdown-Guide erstellt statt einer kurzen Beschreibung.

## Format-Pflicht

Jeder Guide muss enthalten:

1. **Header:** Ziel, Stand-Datum, Projekt-Pfad
2. **Schritt-für-Schritt (1–10):** Jeder Schritt hat Überschrift, Beschreibung, konkrete UI-Elemente mit """, Warnungen mit ⚠️
3. **Checkliste:** Am Ende eine durchgehbare `[ ]` Liste aller Schritte
4. **Troubleshooting:** Die 3-5 häufigsten Fehler mit Lösung
5. **Kosteninfo:** Was kostet das langfristig? Free Tier vs. paid

## Wichtige Regeln

- **NIEMALS "ich kann das für dich machen"** bei Browser-Aufgaben. Der User muss es manuell machen.
- **Warnungen prominent:** Kritische Stellen (Billing-Typ, JSON vs P12, Permission-Box) immer mit ⚠️ und explizit benennen.
- **Konkrete UI-Pfade:** Nicht "geh zur Einstellung" sondern "Links im Menü: APIs & Services → Bibliothek"
- **Token/Key als Code-Block:** Immer als `code` formatiert, nie als Fließtext
- **Checkliste mit `[ ]`:** User kann abhaken. Wenn alle `[x]` → nächster Schritt anbieten.
- **OAuth-URLs NIEMALS aus dem Chat-Output pasten.** Lange OAuth-Authorize-URLs mit `code_challenge`, `state` etc. werden vom Chat-Rendering, Browser-Autocomplete oder Copy-Paste-Handlern fast immer kaputt gemacht (`%20` → Space, Parameter truncated). User muss die URL frisch im eigenen Terminal generieren (z.B. `NO_BROWSER=true <tool>`). Das ist die #1-Fehlerquelle bei OAuth-Login-Flows, nicht das Tool selbst.

## Erstellungs-Workflow

1. Frage: "Braucht der User einen Guide für [Browser-Prozess]?"
2. Falls ja → `write_file` mit `GUIDE_NAME.md` im Projekt-Ordner
3. Guide enthält Header + Steps + Checkliste + Troubleshooting + Kosten
4. Nach dem Guide → nächstes Thema anbieten (Optionenliste)

## Backend-CLI OAuth-Authenticators (OAuth-Dance via lokales CLI + Browser)

Wenn ein lokales CLI-Tool einen Browser-OAuth-Login braucht (z.B. `gemini`, `gh`, `gcloud`, `aws sso`), sind drei Auth-Varianten möglich — alle müssen dokumentiert werden:

| Variante | Command | Wann sinnvoll |
|---|---|---|
| **A. Browser öffnet automatisch** | `<tool>` | Default, geht nur wenn das Terminal echten Browser-Zugriff hat (nicht headless, nicht in Docker ohne X) |
| **B. Manueller URL + Code** | `NO_BROWSER=true <tool>` | Headless / SSH / kein Browser — CLI druckt URL, User öffnet sie selbst, kopiert Code zurück |
| **C. API-Key / Token direkt** | `GEMINI_API_KEY=... <tool>` oder `export TOKEN=...` | Wenn OAuth-Capriolen nicht lohnen oder Abo/API direkt verfügbar |

Pitfalls bei Variante B:
- URL ist **zeitlich begrenzt** (code_challenge läuft nach ~Minuten ab) — bei Fehlschlag immer **frischen Prozess starten**, alten Code nicht mehrfach versuchen.
- Falls "Failed to sign in" oder "malformed request" kommt → meist URL-Mangling, nicht Service-Fehler. Lösung: im eigenen Terminal neu generieren.
- Wenn die CLI dann doch "Auth successful" meldet aber das Backend anschließend "This client is no longer supported" sagt → der OAuth-Client wurde vom Anbieter deprecated (Beispiel: Gemini CLI 0.49.0 für individuals → Antigravity-Migration). **Mit User klären**: entweder API-Key-Variante (C) für sofortigen Zugriff, oder Watchdog-Cron-Variante (D) für offiziellen Migrations-Pfad. Siehe `references/cli-news-watchdog-pattern.md`.
- Nach erfolgreichem Login: Token landet in `~/.config/<tool>/` oder `~/.<tool>` — Pfad vorher checken, nicht wundern wenn Datei neu auftaucht.

## Vendor-spezifische OAuth/Auth-Notizen

Anbieter ändern ihre Auth-Setups häufiger als die Tools dokumentiert sind. Bekannte aktuelle Deprecation-Fallen:

- **Google Gemini CLI (`@google/gemini-cli`) v0.49.0+**: OAuth für individuals ist **deprecated**. Login klappt technisch, Backend antwortet aber mit "This client is no longer supported for Gemini Code Assist for individuals. To continue using Gemini, please migrate to the Antigravity suite of products". Für User mit Google AI Pro Abo gibt es **zwei realistische Wege**:
  - **B. API-Key über AI Studio** (sofort lauffähig, eigener AI-Studio-Billing-Account oder Free-Tier 60 RPM)
  - **D. Auf Antigravity-Migration warten** und parallel einen **News-Watchdog-Cron** einrichten — passt zu Usern, die offizielle Migration-Pfade bevorzugen statt erzwungene Workarounds.
  - **Default-Empfehlung prüfen:** Vor dem Wechsel auf API-Key mit dem User klären, ob er nicht lieber wartet. Basti hat sich 2026-07-05 explizit für Variante D entschieden, obwohl B technisch sofort verfügbar war.
  - Siehe `references/gemini-cli-auth.md` für die komplette Schritt-für-Schritt-Anleitung.
  - Siehe `references/cli-news-watchdog-pattern.md` für den Watchdog-Cron-Template (curl + sha256-hash + silent-on-no-change + Telegram-on-change).

## Beispiele

- Discord Bot erstellen: `~/yuno-voice-bot/DISCORD_BOT_SETUP.md`
- GCP Billing + API + Service Account: `~/yuno-voice-bot/GCP_SETUP.md`
- Ähnliche Guides können für jede Browser-Aufgabe erstellt werden

## Zugehörige Reference-Files

- `references/gemini-cli-auth.md` — Gemini CLI Auth-Setup komplett (alle 3 Auth-Varianten, häufige Fehler, Sicherheit)
- `references/cli-news-watchdog-pattern.md` — Watchdog-Cron-Pattern wenn auf Vendor-Migration gewartet wird (curl + hash + silent + Telegram)
