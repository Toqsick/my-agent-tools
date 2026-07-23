# Daily Note Format

## Frontmatter Schema

```yaml
---
tags:
  - daily
  - journal
datum: YYYY-MM-DD
session-id: daily-journal
modell: <provider/model>
stimmung: <one-word mood>
zeitzone: Europe/Berlin
---
```

### Fields

- `session-id`: Optional but recommended — set to `daily-journal` for normal days, or omit for retrospective entries
- `modell`: Active model that drove the session (e.g. `deepseek/deepseek-v4-flash`, `openrouter/owl-alpha`)
- `stimmung`: One-word mood from established vocabulary
- `zeitzone`: Always `Europe/Berlin` since 2026-07-09 (Basti's explicit instruction)
- `emoji-präfix`: In rich variant, mood can get an emoji prefix for visual flavour (e.g. `🍯 produktiv-flüssig`)

## Mood Vocabulary

| Stimmung | Bedeutung | Erstes Beispiel |
|---|---|---|
| `produktiv-konsolidierend` | Konsolidierungs-Tag, wenig Chaos | 2026-07-04 |
| `fokussiert` | Konsolidierungs-Welle, klare Themen | 2026-07-05 |
| `troubleshooting-durchbruch` | Kritischer Bug gefunden + gefixt | 2026-06-29 |
| `forschungslastig` | Reine Research-/Recherche-Session | 2026-07-02 |
| `setup-phase` | Setup-Phase, strukturiert aufbauend | 2026-07-03 |
| `setup-phase-frühe` | Frühe Setup-Phase, vieles improvisiert | 2026-06-30 |
| `produktiv` | Normaler produktiver Tag | (geplant ab 2026-07-06) |
| `chaotisch-aufregend` | Viele Bälle gleichzeitig in der Luft | (Reserviert) |

## Body Structure

| Section | Pflicht? | Inhalt |
|---|---|---|
| `## Was lief` | ✅ | Bullet-Liste mit Status-Emojis (`✅` erledigt, `🟡` in Bewegung, `🔴` blockiert, `⚠️` Caveat) oder 🐝-Bullets pro Themen-Block |
| `## Erkenntnisse` | ✅ | 2–5 nummerierte Items; idealerweise mit `[[Wiki-Links]]` |
| `## Offene Punkte` | ✅ | Checkliste `- [ ] …` |
| `## Wiki-Links` | ✅ | Mindestens 3, vorzugsweise 5–7 `[[Links]]` zu Notes in anderen Ordnern |
| `## Mögliche nächste Schritte` | ✅ | Checkliste mit Migration-Targets: was bleibt über morgen, was wandert wohin (`04 Bereiche/`, `05 Ressourcen/`, `03 Projekte/`) |
| `## Review-Notiz` | ✅ | Letzte Sektion — Begründung bei dünner/rückwirkender Note + Quellenangabe |
| `## 🐝 Yuno's Reflexion` | optional | Persönliche, nicht-technische Reflexion — nur bei besonderen Tagen (neue Metapher, Kommunikations-Durchbruch, Lob von Basti) |
| `## Stats` | optional | Metrik-Tabelle (Notes gesamt, Erkenntnisse, Offene Punkte, Wiki-Links) |

## Rich Variant

For sessions with **3+ Themen-Blöcken, parallelen Subagenten, oder besonderen Tagen**:
→ See [Rich Daily Note Template](rich-daily-note-template.md) for emoji-prefixed topic blocks, per-insight 💡-headers, Yuno's Reflexion section, and the full example from 2026-07-09.

## What NOT to Put in Daily Notes

- Long code blocks (put in a Resource or Projekt note)
- Session logs (document in the agent session, reference it by date)
- Binary attachments (put in `08 Anhaenge/` with _README link)
- Anything with a lifespan > 7 days that isn't daily-timeline-relevant

## Conversion Workflow

Erkenntnisse that are **durable** (not day-specific) should migrate:

| If it describes... | Move to |
|---|---|
| A tool or pattern | `05 Ressourcen/<Name>.md` |
| A life domain habit | `04 Bereiche/<Bereich>.md` |
| A project decision | `03 Projekte/<Projekt>/README.md` |
| An identity fact | `01 Kontext/<Name>.md` |
| A permanent process | `01 Kontext/Working Agreement.md` |