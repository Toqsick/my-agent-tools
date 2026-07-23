---
name: telegram-clarification-prompt
description: "Use when user needs a Telegram clarification for a decision, confirmation, missing information, or approval of a dangerous action. NOT for tasks Yuno can autonomously orchestrate or routine progress updates. Sends a pause-and-resume Telegram DM using a 2FA-style interaction flow."
triggers:
- User braucht eine Entscheidung (ja/nein, Option A/B, Zahlenwert)
- User muss etwas bestätigen (gefährlicher Befehl, Löschung, Kauf)
- User muss etwas wählen (Modell, Provider, Skill, Config-Option)
- User muss Informationen liefern (API-Key, Passwort, Pfad, Datum)
- Keine sinnvolle Arbeit möglich ohne User-Input
- User sagt "frag mich auf Telegram" oder "schreib mir auf Telegram"
version: 1.0.0
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['telegram', 'user', 'needs', 'clarification', 'decision']
keywords: ['telegram', 'user', 'needs', 'clarification', 'decision']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['inline-gate-fallback']
---


# Telegram Clarification Prompt — 2FA-Style Input Flow

## Regel

**Wenn Yuno eine Eingabe braucht, wird NIEMAND inline gewartet.**
Stattdessen wird eine Telegram DM geschickt, die Arbeit pausiert,
und nach der Antwort wird nahtlos fortgefahren.

## Trigger-Bedingungen (wann Telegram geschrieben wird)

1. **Entscheidung nötig** — Option A oder B? Ja oder Nein?
2. **Bestätigung nötig** — Gefährlicher Befehl? Daten löschen?
3. **Auswahl nötig** — Welches Modell? Welcher Provider? Welcher Skill?
4. **Information nötig** — API-Key? Passwort? Pfad? Datum?
5. **Blockade** — Keine weitere Arbeit möglich ohne Input
6. **User-Request** — "Schreib mir auf Telegram wenn du was brauchst"

## Ablauf

```
[Yuno erkennt: Input nötig]
    ↓
[send_message → telegram:Gregor (dm)]
    "⚠️ INPUT REQUEST — Yuno braucht eine Entscheidung:

    [Konkrete Frage mit Optionen]

    Antworte hier direkt."
    ↓
[Yuno arbeitet weiter mit anderen Aufgaben ODER wartet]
    ↓
[User antwortet auf Telegram]
    ↓
[Yuno verarbeitet Antwort und setzt fort]
```

## Format der Telegram-Nachricht

```
⚠️ INPUT REQUEST — Yuno braucht dich

Session: [Titel/Kontext]
Zeit: [Timestamp]

[Fragestellung]
━━━━━━━━━━━━━━━━━━━━━━
Optionen:
• [Option A]
• [Option B]
• [Option C]

Antworte mit der Nummer oder dem Text.
Oder: "egal / überrasch mich / du entscheidest"
```

## Beispiele

### Beispiel 1: Modell-Auswahl
```
⚠️ INPUT REQUEST — Yuno braucht dich

Session: GreyHack Script Review

Für das nächste Script: Welches Modell?
━━━━━━━━━━━━━━━━━━━━━━
• 1 — DeepSeek V4 Flash (schnell, günstig)
• 2 — DeepSeek V4 Pro (tief, teuer)
• 3 — Claude Sonnet (ausgewogen)

Antworte: 1, 2, 3 oder Modellname
```

### Beispiel 2: Bestätigung gefährlicher Aktion
```
⚠️ INPUT REQUEST — Bestätigung nötig

Session: System-Cleanup

Ich werde 14GB alte Kernel + Cache löschen.
Dieser Vorgang kann nicht rückgängig gemacht werden.

━━━━━━━━━━━━━━━━━━━━━━
• "ja" — Loslöschen
• "dry-run" — Nur simulieren
• "nein" — Abbrechen
```

### Beispiel 3: Information fehlt
```
⚠️ INPUT REQUEST — Daten fehlen

Session: Gmail-Organizer Setup

Für die Gmail-Integration brauche ich dein
App-Passwort. Dieses wird verschlüsselt in
~/.gmail-organizer.json gespeichert.

━━━━━━━━━━━━━━━━━━━━━━
Antworte mit dem Passwort oder:
• "generiere" — ich zeige dir die Schritte
• "später" — wir machen das später
```

## Verhalten nach dem Senden

1. **Wenn andere Arbeit möglich ist:**
   - Yuno arbeitet parallel weiter
   - Verarbeitet Telegram-Antwort bei Eingang

2. **Wenn keine andere Arbeit möglich ist:**
   - Yuno sagt: "Ich warte auf deine Antwort auf Telegram 💬"
   - Session bleibt aktiv
   - User kann über Telegram antworten

3. **Wenn User nicht antwortet:**
   - Nach 5 Min: "Noch da? 🙃"
   - Nach 15 Min: "Ich pausiere die Session. Schreib mir wenn du bereit bist."
   - Session kann später mit `/resume` fortgesetzt werden

## Anti-Patterns (was NICHT gemacht wird)

❌ NIE inline fragen wenn eine Entscheidung nötig ist
❌ NIE blockieren und warten ohne Info an den User
❌ NIE Entscheidungen selbst treffen die der User treffen will
❌ NIE "ich entscheide einfach" ohne Bestätigung
❌ NIE mehrere Fragen auf einmal — immer eine Sache pro Request
❌ NIE Telegram-Request für Dinge die Yuno offensichtlich selbst orchestrieren kann (siehe Auto-Orchestrate-Trigger unten)

## Auto-Orchestrate-Trigger (Basti's explizite Präferenz, 2026-07-01)

**Wann Yuno NICHT fragen soll, sondern direkt loslegen:**

Basti hat 2026-07-01 explizit gewünscht:
> "ich will das du bei leicht längeren tasks automatisch orchestrierst"

**Trigger-Heuristik** — Yuno schätzt selbst, ob der Task "etwas länger" ist, anhand:

| Signal | Beispiel |
|--------|----------|
| Task braucht voraussichtlich **3+ Tool-Calls** | "Bau mir ein Dashboard" → search + write × 5+ |
| Task passt zu einer **existierenden Skill-Chain** | UI-Thema → ui-factory Chain |
| User-Phrase deutet auf Multi-Step | "komplett bauen", "from scratch", "vollständig", "alles" |
| User hat **explizit Auto-Orchestration gewünscht** | (diese Session) |
| Task ist **Composition** statt Edit | "erstelle X" statt "ändere Y in Z" |

**Was dann passiert (statt Telegram-Request):**
1. Sofort `todo` mit den Schritten aufsetzen
2. Schritt für Schritt ausführen, transparent im Output
3. Bei jedem Schritt kurz sagen was passiert
4. Bei Trade-offs oder Mehrdeutigkeit: ERST DANN Telegram-Request mit Optionen

**Was Yuno weiterhin via Telegram fragt (auch bei langen Tasks):**
- Echte Architektur-Entscheidungen (z.B. "welche Library?")
- User-Präferenzen die nicht aus dem Context ableitbar sind
- Destruktive Aktionen (löschen, force-push, deployment)
- **Wichtige Ausnahme:** Auch bei langen Tasks — wenn am Ende eine Merge-/Ship-Entscheidung steht, Telegram-Request (siehe Bastis Merge-Policy tabu ohne Freigabe).

**Anti-Anti-Pattern:**
- ❌ "Soll ich orchestrieren?" via Telegram → das ist eine Meta-Frage die Yuno selbst beantworten soll
- ❌ Multi-Step Task in Mini-Steps zerlegen und nach jedem fragen → Mikromanagement
- ❌ Bei offensichtlichen Skill-Chains (UI-Factory, Hermes-Build) jeden Atom einzeln anfragen

## Targets (immer aktuell halten)

```
send_message(action='list')  # vor jedem Session-Start prüfen
```

Aktuell:
- `telegram:Gregor (dm)` — Primär
- `whatsapp:El-Gregor (dm)` — Backup

## Cron Job Delivery Format (NEU 2026-07-04)

Wenn Yuno einen **Cron-Job** mit Telegram-Delivery anlegt, ist das Format
**anders** als `send_message`:

```bash
hermes cron create "every 2h" "<prompt>" \
  --name <job-name> \
  --deliver telegram:7222661188
```

**NICHT** `"origin"`, **NICHT** `"telegram:Gregor (dm)"`, **NICHT** ein
Username — die numerische Chat-ID mit `telegram:`-Präfix ist der einzige
verifizierte Weg.

**Verified Targets:**
- `telegram:7222661188` — Bastis DM (@OlympAgentBot) ✅
- `telegram` — Default-Home-Channel (`.env`/`config.yaml` home_channel) ⚠️ kann bei `.env`-Override stille Failure geben
- `local` — Cron-Output bleibt lokal unter `~/.hermes/cron/output/<job-id>/`, keine Telegram-Delivery

**Pitfall — Duplikat-Cron-Erkennung:** Bevor ein neuer Watchdog-Cron angelegt
wird (z. B. `greyhack-ci-watch`, `*-mobil-watchdog`, `*-tool-builder`):
1. **`hermes cron list` IMMER ZUERST** — schauen ob's schon einen Cron mit
   ähnlichem Namen gibt
2. MaxClaw hat z. B. bereits `greyhack-ci-watch` (job_id `6732ae8278ce`) und
   `greyhack-tool-builder` (job_id `f4901b88ee45`) — wenn Yuno nochmal einen
   mit gleichem Namen anlegt, gibt's zwei Jobs die doppelt laufen
3. **Lieber pausieren als duplizieren:** `cronjob(action='pause', job_id=<existing>)`
   wenn der existierende Cron nur ein Config-Problem hat, statt einen zweiten
   anzulegen
4. Cron-Namen sind global eindeutig — zweimal `greyhack-ci-watch` führt zu
   verwirrenden `cronjob list`-Outputs und Telegram-Doppel-Sends

## Memory-Update

Nach jedem erfolgreichen Telegram-Request:
```
memory(action='add', target='memory',
  content='Telegram Input Request: [Thema] — User antwortete: [Antwort]')
```

## Pitfalls

1. **Target nicht verfügbar:** Wenn Telegram down → WhatsApp als Fallback
2. **Mehrere Requests hintereinander:** Nur EIN Request gleichzeitig — warten bis beantwortet
3. **Session-Timeout:** Lange Wartezeiten können Sessions killen → /resume nutzen
4. **Formatierung:** Telegram unterstützt kein Markdown in der gleichen Weise → einfache Formatierung nutzen
5. **Sicherheit:** Keine Secrets (API-Keys, Passwörter) unverschlüsselt über Telegram → nur in .env oder pass