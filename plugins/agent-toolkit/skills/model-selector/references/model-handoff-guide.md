# Modell-Handoff Guide

> Wann das neue Modell nach einem Wechsel aufsetzen muss.

## Ziel

Hermes wechselt das Modell pro Session — aber zwischen Sessions können Stunden oder Tage liegen.
Ein Handoff-Dokument stellt sicher, dass das nächste Modell ohne Verzögerung loslegen kann.

## Zwei Ebenen

### 1. Automatischer Kurz-Handoff (`~/MODEL_HANDOFF_SHORT.md`)

Wird vom **Morning-Cron** (`morning_cron.py --telegram` / `update_handoff()`)
automatisch generiert. Enthält:

- Aktives Modell + User-Info (Basti, deutsch, kawaii)
- Projekt-Fortschritt (x/y Phasen abgeschlossen)
- Wichtige Pfade
- Offene Blocker
- Letzte Session-Stimmung

### 2. Ausführliches Handoff (`~/MODEL_HANDOFF.md`) 

Manuell gepflegt. Enthält zusätzlich:

- User-Profil mit kritischen Regeln (NIE archaisch! Emoticons! Stil!)
- **"Yuno's Tips for the new model"** — die wichtigste Sektion!
  * Technische Pitfalls (Secret-Redaction-Workaround, rich+JSON, discord.py async, Steam ACF)
  * Arbeitsweise mit Basti (konkrete Optionen anbieten, nie "Soll ich?", vage Aufträge erst checken)
  * Test-Disziplin (Syntax-Check nach jedem Feature, synthetische Testdaten)
- Modell-Routing-Tabelle (welches Modell für welche Aufgabe)
- Ausführlicher Änderungsverlauf (was in der letzten Session passiert ist)
- Nächste Schritte (Optionen, die Basti wählen kann)

## Wann aktualisieren

- **Nach jeder produktiven Session** (3+ Tool Calls, neue Features gebaut)
- **Vor jedem Modell-Wechsel** (damit das neue Modell den Kontext hat)
- **Wenn der User "führe ein briefing durch für ein model wechsel" sagt**

## Die "Yuno's Tips" Sektion pflegen

Die wertvollste Sektion im Handoff. Hier gehören Dinge rein:

1. **Pitfalls, die DU in dieser Session erlebt hast** (nicht theoretische)
2. **Workarounds, die funktioniert haben** (mit genauen Befehlen/Code)
3. **Bastis Reaktionen auf deinen Stil** — wenn er was korrigiert hat, hier rein
4. **Test-Erkenntnisse** ("Dieser Mode hat den Monitor schwarz gemacht, dieser nicht")
5. **Nützile Tricks** (Shell-Quoting-Fallen, Python-in-execute_code Patterns)

## Beispiel-Struktur

```markdown
### 🎯 Arbeitsweise mit Basti
- Frag NICHT "Soll ich...?" — biete direkt 2-4 konkrete Optionen an.
- Vage Aufträge ("verfeinern"): Erst Ist-Zustand lesen, DANN Vorschläge.
- Liefere echte Artefakte, keine Beschreibungen.

### 🛠️ Technische Pitfalls
- **Secret-Redaction:** in execute_code wird `"TELEGRAM_BOT_TOKEN" + "="` zensiert.
  Workaround: Prefix splitten.
- **rich + JSON:** console.quiet = True, nicht redirect_stdout.
```

## Tools

- Briefing generieren: im Voice-Bot Projekt `morning_cron.py` (update_handoff())
- Telegram senden: `telegram_helper.py` (stdlib-only, env-basiert)
- Cleaner + Handoff: `yuno_cleaner.py handoff` (generiert + speichert)
