---
name: tiktok-slideshow-design
description: "Use when user asks for TikTok slideshow design, faceless TikTok content, anonymous-account pipelines, slideshow 6-phase workflow. NOT for personal-branded TikTok or live-action video production. TikTok slideshow design pipeline for faceless/anonymous accounts."
version: 1.2.0
author: Yuno (für Basti)
license: MIT
platforms:
- linux
- macos
tags:
- tiktok
- slideshow
- design
- faceless
- canva
- social-media
- viral-content
related_skills:
- tiktok-business-self-improve
- ui-color-system
- ui-design-system
- youtube-creator
- creative-suite
trigger_keywords: ['tiktok', 'slideshow', 'design', 'faceless', 'anonymous']
keywords: ['tiktok', 'slideshow', 'design', 'faceless', 'anonymous']
last_curated: '2026-07-23'
curated_by: 'Yuno'
---

# TikTok-Slideshow-Design-Pipeline

## Wann nutzen

**Trigger:**
- User fragt nach "TikTok-Design", "Slides", "Cover", "Thumbnail", "Canva-Template"
- User fragt nach "virale Themen", "Nischen", "Top-Nischen", "Trends"
- User fragt nach "Design-Ideen", "Farbpalette", "Layout", "Slide-Pattern"
- User sagt "deep search" + Nischen/Design-Kontext
- User sagt "erste Design-Ideen" nach Nischen-Recherche

**Nicht nutzen für:**
- YouTube-Video-Design (→ `youtube-creator`)
- Allgemeine Web-UI/UX (→ `ui-factory`, `ui-design-system`)
- Branding ohne TikTok-Kontext (→ allgemeine Color-Systeme)
- Animierte Poster (→ `dynamic-poster`)

## 6-Phasen-Workflow

### Phase 0 — User-Wahl: Job selbst machen oder Nischen-Auswahl überlassen

**Trigger:** Nachdem 3+ Nischen-Optionen als Tabelle mit Trade-offs präsentiert wurden.

**Zwei Modi:**

1. **User wählt selbst** (Standard) — User sagt "A", "B", "C" oder "Nische X" → direkt Phase 1
2. **"Wähle du" / "Such du aus"** — User will YUNO's Empfehlung OHNE GUI-Pingpong:
   - Yuno trifft eine Top-3-Empfehlung (mit Begründung, warum diese 3 und warum in dieser Reihenfolge)
   - Baut ALLE Deliverables für die gewählte(n) Nische(n)
   - User sieht das Ergebnis, gibt Feedback, dann wird ggf. nachjustiert

**Regel:** Bei "wähle du" KEINE clarify-Fragen stellen. Empfehlung + Execute. Nach "wähle du" heisst "mach" (execute, nicht fragen). Der User will ein ERGEBNIS sehen, nicht noch eine Liste abwägen.

**Anti-Pattern:** Nach "wähle du" nochmal eine clarify mit 4 Optionen schicken. Der User hat bewusst Entscheidungs-Aufwand an mich delegiert.

### "A+B+C" Proposal Pattern

**Trigger:** User hat 3+ Optionen in einer vorherigen Antwort angeboten bekommen und antwortet mit einem Buchstaben (oder "A", "B", "C", "A+B", "A+B+C").

**Regel:** Der Buchstabe IST die Entscheidung. Sofort ausführen, keine Rückfrage. Eine Kombination aus "A+B" bedeutet: beide Optionen nacheinander bauen.

**Beispiel aus der Praxis (2026-07-15):**
```
User: "A + B + C du wählst die top 5 und frägst mich im gui"
→ A: Mehr Posts für laufende Nische erstellen
→ B: Komplettes Kit für neue Nische (Yuno wählt)
→ C: 20 Pitch-Varianten
Yuno: Baut A + C direkt, fragt für B via GUI
```

**Feedback-First-Regel (Basti-Preference, 2026-07-15):** Basti will zuerst das **ERGEBNIS sehen** bevor etwas persistiert wird. Bei neuen Inhalten (Nischen-Kits, Brand-Systeme, Pitch-Varianten):
- Deliverables präsentieren (via write_file oder terminal)
- Kurzer Summary + "Sieht das gut aus?"
- User gibt OK oder Feedback
- **Erst dann** commit ins Git-Repo, persist in Obsidian, oder cron-enable

**Anti-Pattern:** Nach "ok" / "start" sofort in Git committen + alles für immer speichern. Basti sagt explizit: "ich gebe dir erst feedback bevor wir es fix machen". Der Commit kommt NACH dem Feedback.

### Phase 1 — Nischen-Recherche (Perplexity Pro / Deep Search)

Suche aus 6+ Quellen, cross-validiere:
- **vidIQ.com** — CPM/RPM-Daten nach Nische (aktuellstes 2026)
- **OutlierKit.com** — Sub-Nischen-RPM-Breakdown (z.B. Credit Cards $20-30+, Tax $13-19)
- **AttentionClaw.com** — Algorithmus-Analyse, Hook-Formeln, Slide-Formate
- **SlideStorm.ai** — Engagement-Vergleich Slideshow vs. Video (Completion Rate 68% vs 52%)
- **Koro.app** — Swipe-Through-Rate Benchmarks, 5-7 Slide Sweet-Spot
- **Whop.com** — Faceless-Ideen-Pool, 30 Nischen-Katalog

Bewerte jede Nische auf 3 Achsen:
1. **RPM $** — Ertrag pro 1000 Views (höchste: Finance $20-50, Legal $15-45, Insurance $20-50)
2. **Hook-Stärke** — virale Tauglichkeit (Schmerz-Faktor, Neugier, Teilbarkeit)
3. **Produkt-Potential** — was kann man als PDF/Tracker/Workbook verkaufen

### Phase 2 — Branding-System (GLM 5.2 — kostenfrei)

Generiere strukturiertes JSON-Branding:
```json
{
  "color_palette": {
    "primary": "<Hex>",
    "secondary": "<Hex>",
    "accent": "<Hex>",
    "neutral_dark": "<Hex>",
    "neutral_light": "<Hex>",
    "usage_rules": "<wann welche Farbe>"
  },
  "fonts": {
    "headline": "<Name + Fallback>",
    "body": "<Name + Fallback>",
    "why": "<1-Satz-Begründung pro Font>"
  },
  "voice": {
    "tone": "<3 Adjektive, DE>",
    "do": ["<3 Dinge>"],
    "dont": ["<3 Dinge>"],
    "example_caption": "<1 Post-Caption>"
  }
}
```

**3 bewährte Paletten** (aus Referenz-Dateien):

| Nische | Palette-Name | Primary | Stimmung |
|---|---|---|---|
| Finance/Kreditkarten | Trust & Calm | #1A2B47 (Deep Navy) | sachlich, vertrauenswürdig |
| Lifestyle/Selbstoptimierung | Soft Power | #6B7C5F (Sage Green) | weiblich, kompetent, ruhig |
| Minimalismus/Produktivität | Clean Focus | #000000 (Pure Black) | brutalistisch, modern, klar |

### Phase 2.5 — Username-Brainstorming (nach Brand-System)

Nachdem das Brand-System steht aber bevor Canva-Templates gebaut werden, 10 Usernamen brainstormen (5 pro Nische):

1. **Aus Brand ableiten** (2-3): `brand_name_vorschlaege` TikTok-tauglich machen (z.B. FinanzFreiraum → @finanzfreiraum)
2. **Nischen-Keywords + Spin** (2-3): Kern-Keyword + kreativer Zusatz (z.B. cashback → @cashback_lab)
3. **Ein-Wort + Domain-Play** (1): Kurz, merkbar, auf allen Plattformen verfügbar (z.B. @credithub)
4. **Yuno-Empfehlung**: Top-1 pro Nische mit Begründung (kurz, Nische klar, Domain frei, Brand-Vibe)
5. **Verfügbarkeits-Check**: User prüft in App (Falls blockiert → nächster aus Liste)

**Details:** `references/username-brainstorming.md` — Vollständige Methodik mit Beispielen, 5 Brainstorm-Schritten, Pitfalls.

### Phase 3 — Copy / Slide-Texte (Kimi K2.6 — 262K Context)

Generiere 5-10 komplette Posts à 7-8 Slides:

**Hook-Pattern (1 aus 5):**
1. **Listen-Pattern:** "5 Fehler die [Zielgruppe] [macht]"
2. **Umkehr-Pattern:** "Du schaffst X nicht, weil [versteckter Grund]"
3. **Contrarian-Pattern:** "Hör auf [Standardweg]. Mach [Weg]."
4. **Mythen-Pattern:** "[Zahl] [Nischen]-Mythen die dir schaden"
5. **Outcome-Pattern:** "How I [Result] in [Timeframe]"

**Slide-Struktur (7 Karten + Pitch):**
- Karte 1: Headline (groß, Caps, auf Bild)
- Karten 2-7: je 1 Satz, max 18 Wörter, Du-Form, A2-B1 Lesbarkeit
- Karte 8: Pitch (max 2 Sätze, "klick auf mein Profil")

**Regeln:**
- KEINE Emojis auf Content-Slides
- KEIN "Link in Bio" — immer "klick auf mein Profil"
- KEINE Clickbait-Versprechen
- DEUTSCHE Sprache, alltagsnah, kein Marketing-Sprech
- Spannungsbogen: Problem → 4 Punkte → Überleitung → CTA

### Phase 4 — Design-Visual (Kimi K2.6 / Claude Design Pro)

Pro Nische generieren:
- 3 Farbschemata mit Hex-Codes + Font-Pairings
- 3 Slide-Layout-Patterns (siehe `references/slide-layouts.md`)
- Canva-Implementierungs-Hinweise (Template-Struktur, Stock-Keywords)

**3 bewährte Layout-Patterns:**

| Pattern | Slides | Struktur | Am besten für |
|---|---|---|---|
| Schmerz-Ultimatum | 7 | Hook → Problem → Symptom → 3 Schritte → Brücke | Finance, Schulden |
| Myth-vs-Reality | 5 | Headline → 3× Mythos+Realität → CTA | ETF, Steuern, Produkte |
| Before/After | 4 | Outcome → Start → Ziel → Trick | Side-Hustle, Fitness |

### Phase 5 — Canva Bulk-Create (GLM 5.2 — JSON/CSV-Output)

Konvertiere Slide-Texte in Canva-Bulk-Create-CSV:

```csv
post_id,card_1,card_2,card_3,card_4,card_5,card_6,card_7,pitch,bild_keyword
```

**Regeln:**
- UTF-8 Codierung
- Umlaute erlaubt (für Canva-Import besser als ASCII; siehe `tiktok-design-assistant` für Auto-strip BOM + Encoding-Checks)
- Anführungszeichen in Headlines escapen
- Keine Erklärungen — nur CSV-Block
- Max 18 Wörter pro Zelle
- **Pitch-Spalte MUSS gefüllt sein** — Canva Bulk-Create skippt Slide 8 bei leerer Zelle (produktionsvalidierter Bug 2026-07-15)
- **20 Pitch-Varianten pro Nische** mit psychology-types (direct-offer, loss-aversion, curiosity-question, social-proof, fomo-quantified, shortcut, revelation, question-empathy, milestone, problem-solution, contrast, specificity, time-saving, anti-status-quo, identity, concrete-list, personal-story, objection-handler, urgency-soft, free-value)

**Siehe:** `tiktok-design-assistant` SKILL.md Schritt 5 für den vollständigen 20-Type-Pitch-Katalog + Canva-Bulk-Create-CSV-Schema mit Validierung (21 Self-Tests).

### Phase 6 — 14-Tage-Validierung (Test-Run)

Nach Canva Bulk Create die Accounts validieren, bevor Blind weiterproduziert wird.

**Workflow:**
1. Zwei Accounts parallel erstellen (gleiche Upload-Frequenz, unterschiedliche Nischen)
2. 14 Tage lang testen (1 Post/Tag pro Account, Sonntag Pause)
3. Tag 7: Halbzeit-Check mit Stop-Kriterien
4. Tag 14: Final-Decision (welche Nische, welche Strategie, welcher Rhythmus)

**Lieferung:**
- 2 Cron-Nudges (12:30 Upload, 21:00 Tracking) als no_agent-Scripts
- Obsidian-Tracking-Sheet im Vault (03 Projekte/<Projekt>/14-Tage-Test-Tracking.md)
- Entscheidungs-Matrix nach Tag 14

**Details:** `references/14-tage-test-run.md` — Vollständige Methodik mit Setup, Schedule, Tracking-Sheet, Halbzeit-Check, Final-Decision-Template.

**Regel:** Bei "testen" / "test-run" / "14 tage" / "C parallel" diesen Workflow initialisieren. Kein separates Nachfragen ob der User Test-Run will — wenn er "C beide" oder "parallel" sagt, ist die Entscheidung gefallen.

## Modell-Routing-Matrix

| Phase | Modell | Grund | Kosten |
|---|---|---|---|
| Nischen-Recherche | Perplexity Pro (Claude/Default) | Web-Search + Quellen eingebaut | Perplexity Pro |
| Branding-JSON | GLM 5.2 (zai) | Exzellenter strukturierter Output | Kostenfrei |
| Lange Briefings / Varianten | Kimi K2.6 | 262K Context, Multimodal | Kostenfrei |
| Copy / Microcopy | GPT (via Perplexity Pro) | Kreativ, DE-Social-Media-Ton | Perplexity Pro |
| UI/UX Specs / Critique | Claude Design Pro | Bestes Design-Reasoning | Claude Pro |
| Bulk-Create CSV | GLM 5.2 (zai) | Strukturierter JSON-Output | Kostenfrei |

## Schnell-Referenz: Top-Nischen (DE-Sprachraum 2026)

| Rang | Nische | RPM | Hook-Stärke | Produkt-Idee |
|---|---|---|---|---|
| 1 | Kreditkarten-Vergleich & Cashback | $20-30+ | ⭐⭐⭐⭐⭐ | Cashback-Guide PDF |
| 2 | Schulden-Tilgung (anonym) | $10-16 | ⭐⭐⭐⭐⭐ | 30-Day-Tracker PDF |
| 3 | Steuer-Tipps für Angestellte | $13-19 | ⭐⭐⭐⭐ | Tax-Checkliste PDF |
| 4 | ETF/Sparplan-Basics | $12-18 | ⭐⭐⭐⭐ | ETF-Starter-Guide PDF |
| 5 | Side-Hustle (anonym) | $9-15 | ⭐⭐⭐⭐⭐ | Side-Hustle-Guide PDF |
| 6 | Produktivität/Zeitmanagement | $4-10 | ⭐⭐⭐⭐⭐ | Habit-Tracker PDF |
| 7 | Schlaf-Optimierung/Morning Routines | $4-10 | ⭐⭐⭐⭐⭐ | Routinen-Workbook PDF |
| 8 | Minimalismus/Capsule Wardrobe | $4-10 | ⭐⭐⭐⭐ | Outfit-Checkliste PDF |
| 9 | Mental Health/Stress-Management | $4-10 | ⭐⭐⭐⭐⭐ | Breathwork-Tracker PDF |
| 10 | BookTok (Bücher nach Stimmung) | $2-6 | ⭐⭐⭐⭐⭐ | Lese-Tracker PDF |

## Pitfalls

- ❌ **Emojis in Slide-Texten** — killt die Save-Rate und wirkt unseriös
- ❌ **"Link in Bio"** — weniger CTA-Kraft als "klick auf mein Profil" (14% mehr CTR)
- ❌ **Mehr als 7 Slides** — Completion-Rate bricht massiv ein (Sweet Spot: 5-7)
- ❌ **Text in den Under-/Overlay-Zonen** — Safe Zone: mittlere 60% des Bildschirms
- ❌ **Video-Mode statt Photo-Mode** — killt Swipe-Interaction (Photo Mode = manuelles Swipen)
- ❌ **Höflichkeits-Floskeln** ("bitte", "wenn du magst") — senken Authority
- ❌ **Archaische Anreden** ("mein lieber", "werte/r", "hochachtungsvoll") — NIEMALS
- ❌ **Canva Connect API** — nur Enterprise (~30€/User/Mo), Pro/Teams Bulk Create reicht
- ❌ **Unnötig formelle Sprache** — locker, natürlich, wie ein Freund der Ahnung hat
- ❌ **Englische Headlines im DE-Sprachraum** — verliert 40% der Zielgruppe
- ❌ **Keine Quellen angeben** — cross-validierte Daten sind der USP
- ❌ **Nur ein Modell für alles** — jedes Modell hat eine Kern-Stärke, nutze Routing

## Verification

Vor Auslieferung prüfen:

- [ ] Jeder Post: 5-7 Slides (max 8)
- [ ] CTA auf letzter Slide: "klick auf mein Profil" (nie "Link in Bio")
- [ ] Keine Emojis auf Content-Slides
- [ ] Text in TikTok Safe Zone (mittlere 60%)
- [ ] Photo Mode selected (nicht Video Mode)
- [ ] Trending Audio aus Commercial Sounds Library
- [ ] Deutsche Sprache, alltagsnah, Du-Form
- [ ] Headline-Text auf Slide 1 ist lesbar auf 1080×1350px
- [ ] Farben: WCAG AA Kontrast (mindestens 4.5:1 für Text-Inhalt)
- [ ] Quellen: mindestens 3 unabhängige für Nischen-RPM-Daten

### Bei Test-Run (Phase 6) zusätzlich:

- [ ] Beide Accounts: Creator-Account, Profile leer (kein Bio/Link/Profilbild)
- [ ] Canva Master-Templates pro Nische gebaut (15-20 Min/Nische)
- [ ] 10+ Posts pro Nische via Bulk Create generiert
- [ ] 2 Cron-Nudges eingerichtet (12:30 Upload, 21:00 Tracking)
- [ ] Obsidian Tracking-Sheet im Vault angelegt (03 Projekte/<Projekt>/14-Tage-Test-Tracking.md)
- [ ] Cron-Skripte haben self-limiting Datums-Check (kein Spam nach Test-Ende)
- [ ] Sonntag als Pause-Tag konfiguriert
- [ ] Usernames eingetragen: __ und __

## Reference Files

- `references/viral-niches-rpm-2026.md` — Vollständige RPM-Daten + Sub-Nischen-Breakdown
- `references/hook-patterns.md` — 10+ Hook-Formeln mit Beispielen
- `references/design-palettes.md` — 3 ausgearbeitete Farbschemata + Font-Pairings
- `references/slide-layouts.md` — 3 Slide-Layout-Patterns mit Struktur
- `references/username-brainstorming.md` — Username-Generierung (5 pro Nische, 4 Schritte, Yuno-Empfehlung, Verfügbarkeits-Check)
- `references/14-tage-test-run.md` — 14-Tage-Validierungs-Methodik (Setup, Schedule, Tracking-Sheet, Halbzeit-Check, Final-Decision, Cron-Script-Pattern)
- `references/faceless-content-pipeline.md` — Vollständige Content-Produktion-Pipeline inkl. Pitch-Varianten (von `tiktok-business-self-improve`)

## Siehe auch

- `tiktok-business-self-improve` — Meta-Loop für das Projekt (Cron, Learning, Anpassung)
- `ui-color-system` — WCAG-konforme Farbpaletten-Generierung
- `ui-design-system` — Komplette Design-Systeme (Token, Typography, Spacing)
- `youtube-creator` — YouTube-Pipeline (anderes Format, aber ähnliche Copy-Struktur)
