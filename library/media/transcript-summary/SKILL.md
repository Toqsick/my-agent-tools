---
name: transcript-summary
description: >-
  Use when user asks for summarizing a saved transcript, extracting key takeaways from a video transcript, or turning transcript text into structured notes. NOT for fetching captions from YouTube or producing a verbatim transcription. Parses an existing stage-3 transcript and writes a compact German summary with themes, takeaways, quick wins, and references.
version: 1.0.0
author: Yuno (für Basti)
license: MIT
platforms:
- linux
- macos
tags:
- youtube
- transcript
- summary
- documentation
metadata:
  hermes:
    tags:
    - youtube
    - transcript
    - summary
trigger_keywords: ['transcript', 'takeaways', 'from', 'and', 'transcript-summary']
keywords: ['transcript', 'takeaways', 'user', 'asks', 'summarizing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['youtube-content', 'youtube-transcript-saver']
---


# Transcript Summary

Erstellt kompakte Zusammenfassungen aus polierten YouTube-Transkripten.

## Wann nutzen

Trigger:
- "Fass das Transkript zusammen"
- "Was sind die Key-Takeaways aus [datei]?"
- "Mach mir eine Zusammenfassung von [video]"

## Workflow

### 1. Datei identifizieren
- Pfad: `~/docs/youtube/YYYY-MM-DD_<slug>_<VIDEOID>.md`
- Wenn nicht klar: `ls ~/docs/youtube/*.md` und neueste/älteste/größte fragen

### 2. Struktur parsen

Aus dem Frontmatter extrahieren:
- Title, Channel, Upload-Date, Duration, Views, Likes
- Description + Tags aus dem Header

### 3. Transkript analysieren

Lese die `## 📝 Transkript (Stufe 3 poliert)` Sektion:
- Minuten-Marker `## [MM:SS]` als natürliche Sektions-Breakpoints
- Eigennamen und Tools extrahieren
- "Use Cases" / "Methoden" / "Bausteine" / "Tipps" Listen identifizieren
- Kernaussagen mit Zeitstempel

### 4. Zusammenfassung schreiben

**Struktur:**
1. **Video-Metadaten** (1-2 Zeilen)
2. **TL;DR** (1-3 Sätze)
3. **Die Kernaussagen** (Bullet-Liste mit Zeitstempel)
4. **Die Hauptthemen / Use-Cases / Methoden** (Tabelle)
5. **Quick-Wins für mich (Basti)** (1-5 Sätze)
6. **Verweise** (Querverweise zu anderen Videos in der Library)

### 5. Speichern

Default-Speicherort:
- Inline im Chat (wenn kurz)
- `~/docs/youtube/summaries/YYYY-MM-DD_<slug>_summary.md` (wenn ausführlich)
- Ins INDEX.md als Quick-Link eintragen

## Pitfalls

1. **Zu lang** — Maximal 1 Bildschirmseite, alles Eigennamen + Tools rausziehen ist wichtiger als Vollständigkeit
2. **Eigennamen falsch geschrieben** — IMMER aus dem polierten Transkript-Block kopieren, nicht aus Roh-Material
3. **Zeitstempel vergessen** — Jede Kernaussage mit `## [MM:SS]`-Marker referenzieren für Navigation
4. **Ohne Context** — Querverweise zu anderen Videos sind wertvoller als isolierte Zusammenfassungen
5. **Original-Wortlaut klauen** — Zusammenfassen ist OK, aber Originalzitate mit "..." wenn sie prägnant sind

## Beispiel-Output

```markdown
# Zusammenfassung: [Video-Titel]

**Video:** [Datum] · [Dauer] · [Views] Likes · [Channel]

## TL;DR
[1-3 Sätze — was ist die Hauptaussage?]

## Kernaussagen

- **[00:00]** [Kernaussage 1]
- **[02:14]** [Kernaussage 2 mit Bezug auf Use-Case X]
- **[12:30]** [Tool-Empfehlung Y]

## Hauptthemen / Methoden

| # | Thema | Zeitstempel | Key-Takeaway |
|---|-------|-------------|--------------|
| 1 | [Name] | [MM:SS] | [1 Satz] |

## Quick-Wins für mich

- [Direkt anwendbare Erkenntnis 1]
- [Direkt anwendbare Erkenntnis 2]

## Verweise

- Siehe auch Video X (`2026-XX-XX_<slug>.md`)
- Siehe auch Video Y (`2026-XX-XX_<slug>.md`)
```

## Siehe auch

- `youtube-transcript-saver` — der Skill der die Source-Transkripte erstellt
- `ai-os-architect` — für strukturierte Architektur-Wissen aus Videos