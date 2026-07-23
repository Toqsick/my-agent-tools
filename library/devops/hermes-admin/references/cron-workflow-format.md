# Cron-Workflow-Datei-Format (.md)

> **Kontext:** Hermes-Cron-Jobs können mit einer `.md`-Workflow-Datei als Prompt-Vorlage arbeiten.
> Der Agent liest die Datei als Instruction und handelt autonom.
> **Silent-on-Success-Pattern:** Nur bei echtem Alarm oder Fortschritt wird Telegram benachrichtigt.

---

## Header-Struktur

Jede Workflow-Datei beginnt mit einem konsistenten Header in der ersten Zeile:

```
**Typ:** <Job-Typ> · **Zeitpunkt:** <menschlich> · **Modell:** `<modell>` · **Deliver:** <Ziel>
```

| Feld | Bedeutung | Werte |
|------|-----------|-------|
| **Typ** | Rolle des Jobs | `Cron-Job (Watchdog)` — deterministisch/meist silent |
| | | `Cron-Job` — LLM-basiert mit Reasoning |
| | | `Cron-Job (Shell)` — reines Bash, kein LLM |
| **Zeitpunkt** | Menschliche Schedule-Beschreibung | `alle 30 Minuten`, `alle 4 Stunden`, `Mo/Mi/Fr 20:00` |
| **Modell** | LLM-Klasse | `heartbeat` — kein LLM, deterministisch (≈0€) |
| | | `main` — günstiges Modell für einfaches Reasoning |
| | | `heavy` — teures Modell für Synthesis/Refactoring |
| | | `shell` — reines Bash-Script, kein LLM-Aufruf |
| **Deliver** | Ziel der Ausgabe | `Telegram` — nur bei Alarm/Änderung |
| | | `local` — nur Log/Filesystem |
| **Skills** (optional) | Komma-separierte Skills | `greyhack,greyhack-sandbox,greyscript-compiler-debugging` |

Optional in Zeile 2-3: **Skills-Angabe** für den Agenten.

## Gliederung

Nach dem Header folgt diese Struktur:

```markdown
## Ziel

Ein Satz: Was passiert hier, wann schlägt Alarm.

## Schritt 1 — <Name>

Konkrete Anweisung an den Agenten.
- Was prüfen
- Wann ist alles OK (silent)
- Wann Alarm schlagen

## Schritt 2 — <Name> (optional)

Nächster Schritt, falls Schritt 1 geändert hat.

## Pitfalls

Bekannte Fallstricke für diesen Job:
- <Fallstrick 1>
- <Fallstrick 2>
```

## Watchdog-Pattern

Die wichtigste Regel: **Silent on Success.**

- Wenn alles OK ist → **keine Telegram-Nachricht.** Der Job läuft durch und terminiert still.
- Nur bei **echtem Alarm** oder **echtem Fortschritt** → eine kurze (max. 10-15 Zeilen) Telegram-Nachricht.
- Ausnahme: Der Check-in-Job (Basti-Checkin) darf auch bei Erfolg kurz antworten — max. 12 Zeilen, lockerer Ton.

## Typische Job-Profile

| Profil | Modell | Schedule | Beispiel |
|--------|--------|----------|----------|
| **Watchdog** | `heartbeat` | alle 30-60 min | Savegame-Diff, Build-Status |
| **Scheduler** | `main` | alle 4-6 h | Missions-Tracker, PR-Monitor |
| **Heavy Lifter** | `heavy` | 1-2×/Tag oder Woche | Autonomes Refactoring, Wochen-Synthese |
| **Shell-Only** | `shell` | alle 6 h | Dirty-Tree-Prüfung, git-Status |
| **Check-in** | `main` | 3×/Woche | Persönlicher Anstoß mit Session-Kontext |

## Beispiel (Watchdog)

```markdown
# Workflow: GreyHack Datenbank-Wächter

**Typ:** Cron-Job (Watchdog) · **Zeitpunkt:** alle 30 Minuten · **Modell:** `heartbeat` · **Deliver:** Telegram

## Ziel

Savegame-DB-Snapshots vergleichen. Nur bei neuen Computern, Mails oder Bank-Bewegungen
eine Telegram-Benachrichtigung senden.

## Schritt 1 — Snapshot erstellen

1. Savegame-Verzeichnis scannen nach `.db`-Dateien
2. SHA256-Hash des aktuellen Snapshots berechnen
3. Mit letztem Snapshot vergleichen

Wenn Hash identisch → **stumm beenden** (silent).

## Schritt 2 — Alarm bei Änderung

Wenn Hash abweicht → Änderungen extrahieren via `sqlite3`-Query:
- Neue Computer: `SELECT name, ip FROM computers ORDER BY id DESC LIMIT 5`
- Neue Mails: `SELECT subject FROM mails ORDER BY id DESC LIMIT 3`
- Bank-Transaktionen: `SELECT amount, description FROM logs ORDER BY id DESC LIMIT 3`

Telegram-Nachricht: max. 10 Zeilen, nur signifikante Änderungen.

## Pitfalls

- cp auf aktive SQLite-DB → korrupte Backups (immer `.backup` + `PRAGMA integrity_check`)
- Hash-Vergleich nur auf Datei-Mtime → echte Diff ignorieren (immer SHA256 des Inhalts)
