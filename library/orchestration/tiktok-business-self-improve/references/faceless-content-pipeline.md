# Faceless TikTok Content Pipeline — Reference

> Ergänzung zum tiktok-business-self-improve Skill.
> Enthält die vollständige Pipeline von Nischen-Research bis Canva Bulk Create.

## Pipeline Overview

```
Nischen Deep-Research → Brand System Design → Canva Bulk CSV → Pitch-Varianten → Production Guide
```

---

## 1. Nischen Deep-Research

### Scoring-Kriterien (pro Nische)
| Kriterium | Beschreibung | Gewichtung |
|---|---|---|
| CPM (RPM) | Einnahmen pro 1000 Views | 25% |
| Save-Rate | Wie oft wird gespeichert (Aspiration) | 25% |
| Hook-Stärke | Virale Trigger-Patterns möglich? | 20% |
| Anonym-Tauglichkeit | Gesicht zeigen nötig? | 15% |
| Produkt-Passung | PDF/Tracker/Checkliste verkaufbar? | 15% |

### Top-Nischen (Deep Search 2026-07-15)
| Rang | Nische | CPM Range | Save-Rate | Hook-Stärke | Anonym |
|---|---|---|---|---|---|
| 1 | Kreditkarten & Cashback | $20-30+ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ |
| 2 | Schulden-Tilgung / Credit Repair | $10-16 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ |
| 3 | Steuer-Tipps | $13-19 (saisonal) | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ |
| 4 | Altersvorsorge / ETF-Sparplan | $12-18 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ |
| 5 | Side-Hustle / Nebeneinkommen | $9-15 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ |
| 6 | Produktivität & Zeitmanagement | $8-15 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ |

### Deep-Search Workflow
1. `web_search(query, limit=5)` nach CPM/Save-Rate/Hook-Patterns
2. `web_extract(urls, char_limit=8000)` auf Top-Quellen
3. Mehrere Iterationen (3-5 Quellen-Runden)
4. Synthese in Markdown-Tabelle mit Quellenangaben

---

## 2. Brand System Design

### Pflicht-Felder im Brand-JSON
```json
{
  "brand_name_vorschlaege": [],
  "tagline_vorschlaege": [],
  "color_palette": {
    "primary": "#HEX",
    "secondary": "#HEX",
    "accent": "#HEX",
    "neutral_dark": "#HEX",
    "neutral_light": "#HEX",
    "neutral_mid": "#HEX",
    "usage_rules": []
  },
  "fonts": {
    "headline": "FontName Weight",
    "body": "FontName",
    "mono": "optional",
    "sizes_canva": {"card_1_headline": "60-72pt", "card_2_7_body": "32-40pt", "card_8_pitch": "48pt"}
  },
  "voice": {
    "tone": [],
    "do": [],
    "dont": []
  },
  "konsistenz_regeln": []
}
```

### Farb-Regeln
- Titelfolie (Slide 1): Primary bg + weißer/akzent Text
- Body-Karten (Slides 2-7): Alternierend neutral_dark / neutral_light
- Pitch (Slide 8): Primary bg + Accent Headline + weißer Body
- Accent-Farbe NUR für: CTAs, wichtige Zahlen, Schlüsselwörter

### Font-Regeln
- Headline (Slide 1+8): Bold/Black Weight, Caps, 48-72pt
- Body (Slides 2-7): Regular, normal-case, 28-40pt
- Mono (optional): Für Code, Zahlen, Zeitangaben in Akzentfarbe

---

## 3. Canva Bulk Create CSV

### Schema (11 Spalten)
```
post_id,card_1_title,card_2,card_3,card_4,card_5,card_6,card_7,pitch,nische,bild_keyword
```

### Slide-Mapping
| CSV-Spalte | Canva Slide | Inhalt |
|---|---|---|
| card_1_title | Slide 1 | Headline / Hook |
| card_2 | Slide 2 | Body 1 |
| card_3 | Slide 3 | Body 2 |
| card_4 | Slide 4 | Body 3 |
| card_5 | Slide 5 | Body 4 |
| card_6 | Slide 6 | Body 5 |
| card_7 | Slide 7 | Body 6 |
| pitch | Slide 8 | CTA (immer "Mehr in meinem Profil") |

### Content-Regeln
- Jeder Card: max 18 Wörter, genau 1 Satz
- Jeder Post: 8 Slides total (1 Title + 6 Body + 1 Pitch)
- 10 Posts pro Batch = 1 CSV-Datei
- Pitch NIEMALS "Link in Bio", "Swipe up", "Klick hier" — immer "Mehr in meinem Profil"

### Bulk-Erstellung
1. Canva → Apps → Bulk Create
2. CSV-Inhalt kopieren
3. Spalten auf Slides mappen
4. Generate → 10 Posts in ~30 Sekunden

---

## 4. Pitch-Varianten (20 pro Nische)

### Psychologie-Typen
| Typ | Wirkung | Best For |
|---|---|---|
| loss-aversion | Verlust-Trigger | Spar-Posts, hohe CTR |
| social-proof | Bandwagon-Effekt | Trust-Aufbau |
| curiosity-question | Gehirn-Aktivierung | Quiz-Content |
| fomo-quantified | Handlungsdruck | Conversion |
| contrast | Vorher-Nachher | Erfolgs-Story |
| identity | Aspiration | Community |
| objection-handler | Einwand-Adressierung | Skeptiker |
| free-value | Gratis + Exklusivität | Follower-Akquise |

### Build-Workflow
1. 20 Varianten pro Nische erstellen (basierend auf Nischen-Spezifika)
2. Jede Variante: {id, type, text, psychology, best_for, expected_ctr}
3. Anti-Patterns dokumentieren (was NEVER sagen)
4. Nutzungs-Phasen empfehlen (Phase 1-4)

---

## 5. Production Guide

### Canva Master-Template (1x pro Nische, 15-20 Min)
1. Neues Canva-Design: Instagram-Beitrag (1080×1350 px, 4:5)
2. Slide 1: Primary bg, Headline-Font, Caps, 72pt
3. Slides 2-7: Abwechselnd dark/light bg + Body-Font
4. Slide 8: Primary bg + Accent Headline + weißer Body
5. Template speichern als "TikTok Slideshow Master — {Nische}"

### Bulk Create Workflow
1. CSV-Datei aus data/ öffnen
2. In Bulk Create einfügen
3. Spalten mapping: card_1_title → Slide 1, card_2 → Slide 2, etc.
4. Generate
5. Herunterladen in Playlist-Ordner

### Posting Schedule
- Phase 1 (Tag 1-14): 1 Post/Tag, gleiche Nische, Hook-Test
- Phase 2 (Tag 15-30): 2 Posts/Tag, gleiche Nische, A/B Pitch
- Phase 3: Multi-Account parallel

---

## Session-Kontext (2026-07-15)

Diese Pipeline wurde in der Session vom 2026-07-15 entwickelt. 
3 Nischen wurden komplett ausgebaut:

| Nische | Brand | Posts |
|---|---|---|
| Kreditkarten & Cashback | Navy + Gold, Trust-Vibe | 20 |
| Schulden-Tilgung | analog KK, Empathy-Vibe | 10 |
| Produktivität | Schwarz + Orange, Brutalist | 10 |

Gespeichert: ~/10-Projekte/10-active/yuno-anon-tiktok-business/