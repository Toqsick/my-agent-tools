---
name: tiktok-business-self-improve
description: |
  Use when running the iterative self-improvement loop for the Yuno anonymous TikTok business, reviewing outcomes, or selecting the next measurable experiment.
  NOT for general TikTok content creation, account actions without approval, or changing strategy from unverified vanity metrics alone.
  Defines a project-specific observe-evaluate-experiment cycle that turns performance evidence into prioritized business improvements.
version: 1.2.0
author: Yuno (für Basti)
license: MIT
platforms:
- linux
- macos
tags:
- self-improve
- cron
- tiktok-business
- learning-loop
trigger_keywords: ['tiktok', 'business', 'experiment', 'running', 'iterative']
keywords: ['tiktok', 'business', 'experiment', 'running', 'iterative']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['tiktok-slideshow-design', 'tiktok-design-assistant']
---


# TikTok-Business Self-Improve

## Wann nutzen

Trigger:
- **Cron** `yuno-tiktok-evening-reflect` (Mo-Fr 20:00) — Selbst-Reflexion
- **Cron** `yuno-tiktok-morning-plan` (Mo-Fr 10:00) — Tages-Plan-Nudge
- **Cron** `yuno-tiktok-afternoon-check` (Mo-Fr 14:00) — Halbzeit-Check
- **Cron** `yuno-tiktok-weekly-review` (So 20:00) — Wochen-Bilanz
- Basti fragt "was soll ich heute am TikTok-Business machen"
- Basti erwähnt "Self-Improve" + "TikTok"

## Touch-Point-Architektur (4 Slots/Tag, alle no_agent-Scripts)

| Zeit | Cron-Name | Wann | Was |
|---|---|---|---|
| 10:00 | yuno-tiktok-morning-plan | Mo-Fr | Tages-Plan-Nudge: "Welche Phase + 1 Mini-Ziel?" |
| 14:00 | yuno-tiktok-afternoon-check | Mo-Fr | Halbzeit-Check: "Bist du auf Kurs?" |
| 20:00 | yuno-tiktok-evening-reflect | Mo-Fr | Selbst-Reflexion: "Was hast du umgesetzt, was morgen?" |
| 20:00 | yuno-tiktok-weekly-review | So | Wochen-Bilanz: "Wie lief die Woche?" |

**Scripts:** `~/.hermes/scripts/yuno-tiktok-{morning-plan,afternoon-check,evening-reflect,weekly-review}.sh`
**Cron-IDs:** 13ff6a9072e7 (morning), a00bba205c69 (afternoon), 3b92e3103455 (evening), 8fe741c101c0 (weekly)

**Design-Entscheidung:** 3 Touch-Points/Tag sind Bastis Sweet-Spot — weniger fuehlt sich nach "Yuno hat das Projekt vergessen" an, mehr wird zum Laerm. Sonntag = ruhiger Wochen-Abschluss, nicht zusaetzlich belastend.

## Zero-Response Escalation (Frust-Pause)

**Wann:** Wenn Basti an 2 aufeinanderfolgenden Werktagen auf **alle** Touch-Points (10:00 + 14:00 + 20:00) keine Antwort gegeben hat.

### Ladder (Tag-fuer-Tag)

| Tag ohne Antwort | Verhalten | Output |
|---|---|---|
| 1-2 | **Normalbetrieb** | Alle Anker wie geplant. Fragen offen lassen, aber immer **1 konkrete 1-Klick-Aufgabe** anbieten (z.B. "Sag go ich mache X"). |
| 3 | **Frust-Pause ausloesen** | Komplette Stille — **kein Daily-Notiz-Beruehrung, kein Nudge**. Cron laeuft trotzdem und liefert Output, aber NUR ein Pause-Statement (s. Output-Format). Basti kriegt einen Tag Luft. |
| 4 | **Mini-Reset** | Wieder mit 1 kurzem Nudge pro Slot. Aber **keine offenen Fragen mehr**. Stattdessen nur 1 ultimativen 1-Klick-Vorschlag (s. Output-Format). "Ich committe die offenen Files, wenn du nichts sagst -- sag halt." |
| 5+ | **Eskalation** | Telegram-DM mit ehrlicher Frage: "Hey Basti -- das TikTok-Projekt liegt seit N Tagen still. Sollen wir es auf Eis legen oder brauchst du einen anderen Einstieg?" |

### Output-Formate in Frust-Pause und Mini-Reset

**Tag 3 (Frust-Pause) — Cron laeuft, Output ist ein Pause-Statement:**
```
🌙 Yuno Self-Improve Check-in — [Datum] ([Tag X/30])

> Frust-Pause aktiv. [Tag X] in Folge ohne Antwort auf alle Anker.
  Heute kein Nudge, keine Frage, kein Touch — du kriegst einen Tag Luft.

**Cron-Status:** [name] (ID: [id]) — stabil, [N] Runs completed.

**Repo-Stand (eingefroren, kein Commit):**
- HEAD: [sha] ([titel])
- Uncommitted: [liste] [seit X Tagen]
- Kein neuer Commit, keine Daily-Antworten seit gestern.

**Reflect-Befund (mein Wert heute):**
- <1 Satz Pattern-Erkennung>
- <Hinweis auf Cron-Plan (morgen Sa/So kein Cron, naechster Slot)>

**Was ich NICHT gemacht habe:**
- Keine Daily-Note-Beruehrung (Tag 3 = Stille).
- Kein Telegram-Nudge.
- Kein Commit / Push.
```

**Tag 4 (Mini-Reset)— Cron liefert 1 ultimativen Vorschlag:**
```
🌅 Yuno Self-Improve Check-in — [Datum] ([Tag X/30])

⚠️ Tag [X] in Folge ohne Antwort — Mini-Reset aktiv.

**Repo-Stand:**
- Letzter Commit: [sha] ([titel]) [vor X Tagen]
- Offene Files: [liste] [seit X Tagen]

**Angebot (1-Klick):**
Ich habe 2 fertige Commits vorbereitet:
1. `chore: [Self-Improve] [file1] — [beschreibung]`
2. `chore: [Self-Improve] [file2] — [beschreibung]`

Sag **"go"** → ich committe beide + sende dir das Ergebnis.
Sag **"halt"** → wir reden drueber, was du brauchst.

Keine offene Frage — du musst nur ein Wort sagen.
```

### Erkennung

- Zaehle **consecutive days** ohne Antwort in Daily-Notiz (pruefe ob die `## ☀️ 10:00-Addendum`- und `## 🕑 14:00-Addendum`-Sections erweitert wurden seit deinem letzten Schreiben).
- Pruefe **Repo-Aktivitaet** (`git log --oneline -3`) als sekundaeres Signal -- ein Commit am Tag zaehlt als Antwort.
- **Pattern-Alert im Evening-Reflect:** Wenn Tag >=2 ohne Antwort, fuehre ***jeden** Evening-Reflect mit der Zeile `⚠️ Tag N in Folge ohne Antwort` an -- als explizites Signal im Output an Basti.

### Re-Entry-Strategie

Nach Frust-Pause (Tag 3) gilt:
1. **Keine Schuldzuweisung** -- kein "du hast nicht geantwortet", sondern "Projekt liegt still, neuer Versuch".
2. **Angebot statt Frage** -- biete eine fertige Aktion an (Commit + Message, CSV-Render-Befehl), die Basti mit einem Wort freigeben kann.
3. **Keine Akkumulation** -- die 2 offenen Files werden nicht "mehr" offen, sie sind einfach da. Keine Dringlichkeit konstruieren.

## Lern-Schleife (4 Phasen)

### Phase 0 — Cron-Sanity-Check

**Nur relevant wenn du als Cron-Job läufst.** Prüfe vor jeder Aktion:

1. **Job-Health:** Lese `/home/bratan/.hermes/cron/jobs.json` für deine Cron-ID. 
   - `last_run_at: null` + Schedule vor >1h → Job wurde nie gefeuert, melde das.
   - `last_run_at` älter als 3 Cycles → Job ist ausgefallen, investigate.
   - `repeat.completed: 0` bei enabled=true + non-fresh Job → Warnsignal.
2. **Delivery-Kanal checken:** Prüfe ob Telegram/Send-Tools verfügbar sind (via `deliver`-Feld im job-JSON). Falls nicht → **Fallback auf Phase 1 + Daily-Note-Schreiben** (kein Telegram-Output erzwingen).
3. **Profil-Kontext:** Lauf ich im richtigen Hermes-Profil? (Cron-Jobs ohne `profile`-Feld laufen im default-Profil — okay.)

Output: Ein Satz im Antwort-Format: "Cron `{name}` (ID: {id}) läuft stabil, letztes Fire: {zeit}" oder "⚠️ Job hatte noch nie gefeuert — ab {next_run_at} regulär."

### Phase 1 — Beobachtung

Sammle Fakten aus:
1. **Obsidian Daily-Note** des aktuellen Tages
   - *Morning-Plan (10:00):* Suche nach `## ☀️ 10:00-Addendum` und prüfe ob Basti geantwortet hat (Text unter "Yuno fragt:").
   - *Afternoon-Check (14:00):* Suche nach `## 🕑 14:00-Addendum` und prüfe ob Basti geantwortet hat.
   - *Evening-Reflect (20:00):* Suche NACH Antworten in den ☀️ und 🕑 Sectionen (Basti antwortet oft dort). Falls keine → suche/erzeuge `## 🌙 20:00-Addendum`.
   - *Weekly-Review (So):* Suche nach `## 📅 Wochenbilanz`.
2. **Repo-Stand**: `git log --oneline -10` + `git status --short` (uncommitted changes sind Signal für aktuelle Arbeit) + `gh issue list --state open`
3. **Mnemosyne**: Lade letzte 5 memories mit tag `tiktok` oder `business`
4. **Cron-Output**: Letzte 3 Self-Improve-Runs aus `~/.hermes/cron/output/` (success/error patterns) — nützlich vor allem für Weekly-Review, da einzelne Runs wenig History haben

### Phase 2 — Synthese

Antworten auf 3 Fragen destillieren:
1. **Was hat Basti letzte Woche tatsächlich gemacht?** (vs. was er geplant hatte)
2. **Welche Hindernisse tauchen wiederholt auf?** (Patterns erkennen)
3. **Welche Skills/Tools braucht er neu?** (Repo-Erweiterungen)

### Phase 3 — Anpassung

**Repo-Anpassungen** (commit + push lokaler Branch):
- Neue Docs in `docs/06-learnings/` aus wiederkehrenden Problemen
- Tests für neue Funktionen (TDD)
- Skill-Patches fuer `anon-tiktok`

**1-Klick-Aufgaben (neu: Barriere senken):**
Wenn Basti seit 2+ Tagen nicht geantwortet hat, biete **keine offenen Fragen** mehr an, sondern fertige Aktionen:
- **Pre-schreibe Commit-Messages** als 1-Satz-Angebot: "Sag go -> ich committe die 2 offenen Files mit `chore: [Self-Improve] <was>`"
- **Pre-schreibe Render-Commands** als Copy-Paste-fertig: "1 Canva-CSV fuer KK-Nische rendern + visuell checken"
- **Ein-Wort-Freigabe:** Basti muss nur "go" oder "halt" sagen -- keine git-Commands selbst tippen
- **Nach Freigabe:** Sofort ausfuehren + Resultat im naechsten Slot melden

**Memory-Updates** (Mnemosyne):
- Wichtige Erkenntnisse: `importance=0.7, source=task, scope=session`
- User-Präferenzen: `scope=global, importance=0.85`

**Cron-Anpassungen** (selten):
- Schedule anpassen wenn Basti andere Zeiten braucht
- Prompt verfeinern wenn Antwort-Format nicht passt

## Antwort-Format (fuer Basti)

**Standard-Format (Normalbetrieb, Tag 1-2):**

```
🌅 Self-Improve Check-in [Datum]

📊 Was passiert ist:
- <kurze Zusammenfassung letzte Aktivitaet>

💡 Learnings:
- <1-2 Saetze pro Learning>

🔧 Was ich angepasst habe:
- <konkrete Aenderungen mit Commit-IDs>

📋 Morgen-Vorschlag:
- <max 3 konkrete naechste Schritte, mindestens 1 als 1-Klick-Aufgabe>
```

**Zero-Response-Format (Tag >=2 ohne Antwort):**

```
🌙 Yuno Self-Improve Check-in -- [Datum] ([Tag X/30])

⚠️ Tag N in Folge ohne Antwort auf alle Anker.

📊 Repo-Stand:
- Letzter Commit: <sha> (<titel>) [vor X Tagen]
- Uncommitted: <liste> [seit X Tagen offen]
- Keine neuen Antworten auf 10:00/14:00-Anker

💡 Beobachtung:
- <1 Satz, was das Signal bedeutet>
- <1 Satz, was ich vorschlage>

🔧 Was ich angepasst habe:
- <Daily-Notiz erweitert, keine Repo-Aenderungen>

⚠️ **Pattern-Alert:** Wenn morgen wieder keine Antwort -> Frust-Pause (Tag 3 komplett still).

📋 Morgen (Tag X+1/30):
- **Mini-Aufgabe 1:** Sag "go" -> ich committe die offenen Files <liste> mit fertiger Message.
- **Mini-Aufgabe 2:** Danach: <1 konkrete naechste Aktion, kein Upload>
```

## Pitfalls

- **Niemals Push** ohne Basti-Freigabe
- **Niemals mehr als 3 Anpassungen** pro Run (sonst Overload)
- **Immer commit-message mit "chore: [Self-Improve]" prefix** (fuer klares Tracking)
- **Telegram-Nachricht max 1000 Zeichen** (Telegram-Limit)
- **Telegram-Tools nicht immer verfuegbar** -- in Cron-Kontexten (no_agent-Scripts, kein messaging-toolset) sind `telegram:`-Delivery und send_message-Tools oft deaktiviert. Fallback: schreibe das Nudge in die Daily-Notiz als `## ☀️ 10:00-Addendum` oder `## 🌙 20:00-Addendum`. Der Text erreicht Basti beim naechsten Daily-Read. Liefere den Nudge-Trotzdem im Cron-Output.
- **Daily-Notiz-Section pro Slot-Typ** -- Such nicht blind nach einem bestimmten Section-Namen. Jeder Slot hat sein eigenes Prefix: `☀️ 10:00` (morning), `🕑 14:00` (afternoon), `🌙 20:00` (evening), `📅` (weekly). Der evening-Slot sucht zuerst nach Bastis Antworten in den `☀️` und `🕑` Sections (weil er oft dort antwortet), erzeugt erst dann seine eigene `🌙` Section.
- **Uncommitted Files sind Signale** -- `git status --short` zeigt was Basti gerade aktiv bearbeitet hat (oft aussagekraeftiger als alte Commits). In den Beobachtungsteil aufnehmen, aber NIEMALS ohne Freigabe committen
- **Daily-Notiz niemals ueberschreiben** -- append-only
- **Bei Frust-Signal** in Bastis Antwort: lieber 1 Tag Pause als forciertes Weitermachen
- **Tag-Zaehlung nicht zuruecksetzen** -- die `Tag X/30`-Zaehlung im Kickstart-Plan LAEUFT WEITER, auch wenn Basti nichts tut. Nicht kuenstlich pausieren nur weil keine Antwort kam. Der Ladder-Mechanismus (Frust-Pause Tag 3) geht trotzdem weiter.
- **Nicht dreimal dasselbe Angebot wiederholen** -- wenn du eine 1-Klick-Aufgabe anbietest und sie wird ignoriert, biete beim naechsten Mal eine ANDERE an. Nicht "ich frag nochmal wegen pitch-variants" -- Variiere die Angebote pro Run.
- **Keine Dringlichkeit kuenstlich erzeugen** -- "seit X Tagen offen" ist ein Fakt, kein Vorwurf. Sag den Fakt ohne Emotion, biete die Loesung ohne "muss" oder "sollte". Basti entscheidet, nicht du.
- **Evening-Reflect muss auch ohne Daily-Notiz-Antwort Sinn machen** -- der Reflect-Cron darf nie "es gab keine Antwort, also nichts zu tun" sagen. Der Wert liegt im Erkennen des Patterns, im Angebot des naechsten Schritts und in der Pausen-Entscheidung. READ the silence, don't just echo it.
- **Frust-Pause-Cron-Feuer ist KEIN Bug** -- der Cron laeuft auch an Tag 3. Er muss nicht manuell deaktiviert werden. Die Erkennung (Tag 3 erreicht) ist im Cron-Code embedded; der Output wird automatisch auf ein Pause-Statement reduziert. Schedule bleibt erhalten, kein manueller Eingriff noetig.

## Siehe auch

- `tiktok-slideshow-design` — Design-Pipeline fuer TikTok-Slides (Nischen-Recherche -> Branding -> Canva-Bulk-Create)
- `references/faceless-content-pipeline.md` — Vollstaendige Content-Produktion-Pipeline: Nischen-Research, Brand System Design, Canva Bulk CSV Schema, 20 Pitch-Varianten pro Nische (Psychologie-Typen), Production Guides. Enthaelt auch die Session-Ergebnisse vom 2026-07-15 (3 Nischen: Kreditkarten, Schulden, Produktivitaet).
- `references/zero-response-pattern-2026-07-16.md` — Erste dokumentierte Frust-Pause-Erkennung (Tag 2/30 ohne Antwort). Konkrete Messwerte, Ladder-Entscheidung, Lessons. Nutzen bei zukuenftigen Zero-Response-Situationen als Vergleichsbasis.
- `references/frust-pause-execution-2026-07-17.md` — Erste Frust-Pause-Ausfuehrung (Tag 3/30, komplett ohne Antwort). Cron lief, Output wurde auf Pause-Statement reduziert. Lessons zur Cron-Feuer-Tag3-Kombination.
- `~/.hermes/plans/2026-07-15_032500-30-day-kickstart-anon-tiktok-business.md`
- `~/10-Projekte/10-active/yuno-anon-tiktok-business/README.md`
- `~/Dokumente/Obsidian Vault/03 Projekte/Yuno-Anon-TikTok-Business.md`

## Modell-Toolset (Stand 2026-07-15)

Basti hat aktuell:
- **Lokal:** Hermes/Yuno (Text-Pipeline, 11 Prompts)
- **Cloud:** agent.minimax.io M3 Built-ins (21 Design-Skills)
- **Perplexity Pro:** + Canva-Integration, Modell-Wahl (GPT, GLM 5.2, Kimi K2.6)
- **Claude Design Pro:** UI/UX Specs, Design-Critique, Code-zu-Canva
- **Canva Premium:** Bulk Create + Magic Switch (KEINE Connect API — nur Enterprise)

Design-Routing: Nischen-Recherche → Perplexity Pro | Branding-JSON → GLM 5.2 | Varianten → Kimi K2.6 | Copy → GPT | Critique → Claude Design Pro
