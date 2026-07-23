---
name: daily-report-trigger
description: >-
  Use when user asks for checking for an empty Vault daily at session start, reminding the user to fill today daily report, or detecting a missing daily-note entry. NOT for sending scheduled cron notifications or building the full daily briefing. Implements a gentle inline-only session-start reminder with edge-case handling, fallback behavior, and no background push delivery.
version: 1.0.0
author: Yuno (Plan 2026-07-16_230642-daily-report-session-trigger.md)
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - daily stub
  - daily fehlt
  - daily vergessen
  - tagesbericht
  - leere daily
  - daily-report trigger
keywords:
  - daily-note
  - vault-hygiene
  - session-start
  - reminder-pattern
  - quiet-trigger
related_skills:
  - daily-briefing
  - self-improving
  - subagent-driven-development
  - mnemosyne-memory-provider
last_curated: 2026-07-16
curated_by: Yuno (Subagent Dispatch 2026-07-16 23:35)
routing_hint: Lädt automatisch via daily-briefing Skill §0.9 Session-Start-Gate. Passive Erinnerung statt Push-Notification. Multi-Marker-Heuristik erkennt Variations-Space in Vault-Section-Headern.
---

# Daily Report Trigger

## Zweck

Dieser Skill sorgt dafür, dass Basti beim Start jeder Hermes-Session eine leise Erinnerung bekommt, falls die heutige Vault-Daily (`~/Dokumente/Obsidian Vault/06 Daily Notes/<YYYY-MM-DD>.md`) leer, verstubbt oder fehlend ist. Er setzt Bastis Wunsch vom 16.07.2026 ("vergiss bitte die tages berichte nicht mehr") um, ohne fixe Cron-Zeiten oder Push-Notifications. Die Erinnerung hängt am Session-Start-Gate des daily-briefing Skills, bleibt aber passiv: Basti entscheidet. Andere Profile, die daily-briefing nicht laden, können diesen Skill einzeln anziehen und dieselbe Session-Start-Hygiene bekommen.

## Architecture

Reine Doku-Spezifikation. Detektion liegt in zwei bestehenden, getesteten Artefakten, die nicht angefasst werden:

- Detection-Script: `~/.hermes/scripts/daily-note-health.py` (8473 Bytes, 9/9 grün). Liest die heutige Daily, klassifiziert, gibt JSON mit `status` (`HEALTHY`, `PARTIAL`, `STUB`, `MISSING`) zurück.
- Loader-Bridge: `~/.hermes/scripts/daily_note_health.py`.
- Test-Suite: `~/.hermes/scripts/test_daily_note_health.py` (9671 Bytes).

Der daily-briefing Skill v1.3.0 hat in §0.9 bereits dieselbe Workflow-Definition eingebettet. v1.0.0 dieses Skills führt die §0.9-Definition logisch zurück: §0.9 bleibt Aufrufstelle, Workflow und Verhaltensregeln sind hier versioniert, damit andere Profile den daily-report-trigger ohne daily-briefing-Inheritance laden können.

## Workflow

Detection läuft als allererster Schritt nach Skill-Loading, vor §1 des daily-briefing Skills.

Schritt 1: Detection-Script aufrufen via `python3 ~/.hermes/scripts/daily-note-health.py --json`. Bei Exit-Fehler kommt `MISSING` als Default.

Schritt 2: Status interpretieren und Reminder-Verhalten wählen.

| Status   | Bedeutung                          | Reminder-Satz (unten im Briefing)                                                            |
|----------|------------------------------------|----------------------------------------------------------------------------------------------|
| HEALTHY  | echter Inhalt                      | still, keine Zeile                                                                            |
| PARTIAL  | Addenda da, Hauptteil leer         | `📝 Daily heute hat Addenda aber kein Hauptinhalt, update ich später.`                       |
| STUB     | Template-Kopie, <1000 Bytes        | `📝 Daily für heute ist noch leer, kommt wenn wir fertig sind.`                              |
| MISSING  | keine Datei                        | `📝 Keine Daily für heute, erstelle ich wenn du willst, oder auto bei Session-Ende.`         |

Schritt 3: Reminder platzieren. Steht ganz unten im Briefing, nach "Bin bereit!", als leiser Footer.

## Edge Cases

PARTIAL/STUB-Toleranz ist explizit dokumentiert. Eine Daily kann unter 1000 Bytes haben und trotzdem HEALTHY sein, wenn die "Was lief"-Section echten Text enthält. Umgekehrt kann sie über 3000 Bytes groß und PARTIAL bleiben, wenn Cron-Addenda sie aufblähen, der Hauptinhalt aber leer bleibt (2026-07-16-Fall). Das Script prüft Section-Content, nicht nur Bytesize.

Multi-Marker-Strategie. Header-Match case-insensitive als Substring gegen fünf Marker, damit Varianten wie `## Was lief (vermutet aus Mnemosyne-Recall)` korrekt als HEALTHY zählen:

1. `was lief`
2. `erkenntnisse`
3. `lessons learned`
4. `hauptaufgaben`
5. `hauptphase`

Bytesize-Limit. Unter 1000 Bytes gilt automatisch STUB solange keine Section-Inhalte gefunden werden. Oberhalb 3000 Bytes wird die Section-Heuristik gegen die Bytesize abgewogen, nicht überschrieben.

Root-level stubs im Vault-Root greift daily-briefing §2.7b auf, dieser Skill erkennt sie nicht selbst.

## Fallback

Fehlt `~/.hermes/scripts/daily-note-health.py` oder schlägt fehl: prüfen ob `~/Dokumente/Obsidian Vault/06 Daily Notes/<YYYY-MM-DD>.md` existiert und kleiner 1000 Bytes ist. Wenn ja, derselbe Reminder wie bei STUB. Fehler werden nicht eskaliert, das Briefing läuft weiter. Liefern weder Script noch Datei-Check etwas, schweigt der Reminder komplett.

## Verhaltensregeln

- NIEMALS die Daily ungefragt erstellen oder einen Stub heilen. Reminder ist passiv, Basti entscheidet.
- NIEMALS mehr als einen Satz. Kein Aufdrängen, keine Erklärung, kein "soll ich …"-Vorschlag.
- Wenn Basti mit konkreter Aufgabe startet (nicht "was gibt's Neues?"), Reminder überspringen.
- Bei HEALTHY: komplett still. Keine Zeile, kein Wort, keine Emoji-Footnote.
- Daily-Erstellung passiert beim Session-Close (daily-briefing §2.9) oder auf Anfrage, niemals beim Start.
- Reminder steht ganz unten als Footer, nicht mittendrin.

## Cross-References

Mnemosyne-Memory 38633f3e32adc109 (Trigger-Pattern, Stub-Heuristik, Original-Wunsch). daily-briefing §0.9 "Daily-Note Health Check: Session-Start Gate" ist die Aufrufstelle. Detection-Script `~/.hermes/scripts/daily-note-health.py` (8473 Bytes), Loader-Bridge `~/.hermes/scripts/daily_note_health.py`, Test-Suite `~/.hermes/scripts/test_daily_note_health.py` (9671 Bytes, 9/9 grün), alle drei NICHT anfassen. Plan-Quelle `2026-07-16_230642-daily-report-session-trigger.md`. Ship-Handoff `/home/bratan/.hermes/docus/handoffs/2026-07-16-daily-note-session-trigger-shipped.md`. daily-briefing Querverweise: §0.5 Reconstruction Mode, §2.7b Root-stubs, §2.8 Sync-Discipline, §2.9 Session-Close.

**Fall-Study (Provenance):** Der vollständige Audit-Report, der die 5 falsch klassifizierten Files entlarvte und die Multi-Marker-Heuristik begründet, liegt unter `~/.hermes/docus/reports/2026-07-16-subagent-self-test-deception-fallstudy.md` (54 KB, 5 Sections, 4 Appendices). Enthält: vollständige Real-Vault-Header-Inventur aller 18 Daily-Files, Subagent-Report-Analyse der Welle-1-Deception, Queen-Audit-Methodik, Pitfall-Einbettung (Pitfalls #38, #39, #40). Dieses Dokument ist die Primärquelle für die Architektur-Entscheidung "Multi-Marker statt Exact-Match".

## Wartung

Wenn neue Vault-Marker entstehen (Basti führt z. B. `## Kernerkenntnisse` ein):

1. Marker-Liste im Multi-Marker-Abschnitt um Substring appenden. Reihenfolge egal.
2. Trigger-Keywords im YAML-Frontmatter ergänzen, falls neuer Reminder-Anlass.
3. Test in `~/.hermes/scripts/test_daily_note_health.py` mit Mini-Daily, die neuen Marker als einzigen Header hat. Erwartung: `HEALTHY`. 9/9 → N/N grün.
4. `last_curated` und `curated_by` im YAML auf aktuelles Datum und Subagent-Welle setzen.
5. Version-Bump: Patch für Marker-Appends, Minor für neue Verhaltensregeln, Major für Architektur-Brüche.
6. Handoff in `~/.hermes/docus/handoffs/` mit Datum, Trigger-Anlass und Diff zur Vorgängerversion.

Der Handoff `2026-07-16-daily-note-session-trigger-shipped.md` bleibt der kanonische Erst-Record für v1.0.0.
