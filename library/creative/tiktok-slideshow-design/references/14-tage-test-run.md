# 14-Tage-Test-Run — TikTok Content Validation Methodology

> Validierte Methode aus dem Parallel-Test Kreditkarten (finanzfreiraum) vs Produktivität (fokusfabrik), 2026-07-15 bis 2026-07-30.
> Kann auf jede Nische angewendet werden.

---

## Use Case

Zwei Accounts parallel starten (gleiche Upload-Frequenz) → nach 14 Tagen harte Daten-Entscheidung welcher Account weiterläuft.

**Nicht geeignet für:** Etablierte Accounts mit Publikum, Big-Bang-Launches, Multi-Plattform-Strategien.

---

## Setup (Phase 0, 60-90 Min)

### Accounts anlegen (20 Min)

Beide Accounts auf TikTok als **Creator-Account** anlegen:

1. Account A (Nische 1): Username aus Brand-System
2. Account B (Nische 2): Username aus Brand-System

**Profil anlegen:** Leer lassen (kein Bio, kein Link, kein Profilbild — erst nach Test-Decision)

### Canva Master-Templates (40 Min)

Pro Nische ein Master-Template in Canva bauen (Instagram-Beitrag 4:5, 1080×1350px):

1. Template mit Brand-Farben + Fonts (siehe `references/design-palettes.md`)
2. Bulk-Create-CSV aus data/ importieren
3. 10 Posts pro Batch generieren (~30 Sekunden pro Nische)

### Cron-Nudges einrichten (10 Min)

Zwei no_agent-Scripts:

| Nudge | Zeit | Was |
|---|---|---|
| Upload-Nudge | 12:30 | Welche Posts heute hochladen + Caption |
| Tracking-Nudge | 21:00 | Metriken eintragen + Formeln |

**Script-Design-Pattern (no_agent, self-limiting):**
- Skript checkt selbst ob TODAY innerhalb [START, END] liegt
- Außerhalb des Zeitfensters → silent exit (kein Telegram-Spam)
- Sonntag = Pause-Tag → eigene Meldung (Wochen-Review statt Upload)
- Telegram-Token aus `~/.hermes/.env` (kein Hardcode)

### Obsidian Tracking-Sheet (5 Min)

Eine Tracking-Note im Vault anlegen:

```
📁 03 Projekte/<Projekt>/14-Tage-Test-Tracking.md
```

Mit:
- Tabelle mit allen Metriken
- Stop-Kriterien für Tag 7
- Entscheidungs-Template für Tag 14
- Cross-Links zur Projekt-MOC

---

## Ablauf (Phase 1-14)

### Täglicher Rhythmus

| Uhrzeit | Action | Wer |
|---|---|---|
| 12:30 | 📱 Upload-Nudge (Telegram): Post #N heute hochladen | Cron-Script |
| (wann immer) | Upload in TikTok App | User |
| 21:00 | 📊 Tracking-Nudge (Telegram): Metriken eintragen | Cron-Script |
| (Abend) | Tracking-Sheet im Vault ausfüllen | User |

**Upload-Format:** TikTok Photo Mode (manuelles Swipen, kein Video).

**Sonntag:** Pause-Tag. Kein Upload. Abends Wochen-Review statt Standard-Tracking.

### Posting-Schedule (2 Accounts, 12 Posts pro Account)

| Tag | Account A | Account B |
|---|---|---|
| Tag 1 (Fr) | Post #1 | Post #1 |
| Tag 2 (Sa) | Post #2 | Post #2 |
| Tag 3 (So) | 📴 PAUSE | 📴 PAUSE |
| Tag 4 (Mo) | Post #3 | Post #3 |
| Tag 5 (Di) | Post #4 | Post #4 |
| Tag 6 (Mi) | Post #5 | Post #5 |
| Tag 7 (Do) | Post #6 | Post #6 |
| — | 📋 HALBZEIT-CHECK (Stop-Kriterien) | 📋 HALBZEIT-CHECK |
| Tag 8 (Fr) | Post #7 | Post #7 |
| Tag 9 (Sa) | Post #8 | Post #8 |
| Tag 10 (So) | 📴 PAUSE | 📴 PAUSE |
| Tag 11 (Mo) | Post #9 | Post #9 |
| Tag 12 (Di) | Post #10 | Post #10 |
| Tag 13 (Mi) | Post #11 | Post #11 |
| Tag 14 (Do) | Post #12 | Post #12 |
| — | 🎯 FINAL-DECISION | 🎯 FINAL-DECISION |

---

## Tracking-Sheet

### Tabellen-Schema (Obsidian Markdown)

```markdown
| Datum | Account | Post# | Views (24h) | Likes | Comments | Shares | Saves | Completion% | Follower-Delta | Notiz |
|---|---|---|---|---|---|---|---|---|---|---|
```

### Berechnungs-Formeln

```
Like-Rate      = Likes / Views × 100
Share-Rate     = Shares / Views × 100
Save-Rate      = Saves / Views × 100          ← Conversion-Indikator!
Engagement     = (Likes + Comments + Shares + Saves) / Views × 100
```

**Save-Rate ist der wichtigste Early-Indicator:** Hohe Save-Rate bei niedrigen Views = Content hat Potenzial, Algorithmus fand noch nicht die richtige Audience. Niedrige Save-Rate + hohe Views = Content ist Unterhaltung, kein Conversion-Content.

---

## Halbzeit-Check (Tag 7)

### Stop-Kriterien

```
WEITERLAUFEN wenn:
✅ Beide Accounts: 500+ Views auf mindestens 1 Post
✅ Mindestens 1 Account: 2%+ Save-Rate auf einem Post

STOPPEN wenn:
❌ Beide Accounts: alle Posts unter 200 Views → Hook-Problem, Content neu generieren
❌ 1 Account komplett flach, anderer lebendig → nur den lebendigen weiterführen

KURS-KORREKTUR wenn:
⚠️ Account hat einzelne Performer (300+ Views) aber kein konsistentes Pattern
   → Hook-Pattern variieren, Upload-Zeit ändern, Sound tauschen
⚠️ Ein Post performt deutlich besser (2×+ Views) als alle anderen
   → Das Pattern analysieren und für nächste Woche replizieren
```

---

## Final-Decision (Tag 14)

### Entscheidungs-Matrix

| Metrik | Account A | Account B | Gewinner |
|---|---|---|---|
| Total Views (alle 12 Posts) | | | |
| Avg Views pro Post | | | |
| Total Likes | | | |
| Total Saves | | | |
| Final Follower | | | |
| Avg Save-Rate | | | |
| Avg Engagement-Rate | | | |
| Beste 3 Posts (Views) | | | |
| DMs / Fragen erhalten | | | |
| Spaß beim Posten (User-Subjektiv) | | | |

### Mögliche Entscheidungen

- [ ] **Beide weiterführen** → Cross-Promo-Strategie entwickeln
- [ ] **Nur Account A** → Brand-Vertiefung, 2. Batch Posts, Landingpage
- [ ] **Nur Account B** → Brand-Vertiefung, 2. Batch Posts, Landingpage
- [ ] **Weder** → Hooks generisch, Content neu brainstormen
- [ ] **Neustart mit Hybrid-Nische** → z.B. "Finanzen für Selbstständige"

---

## Yuno-Rolle nach Tag 14

Wenn User nach Feedback fragt (oder automatisch am Tag 14):

1. **Vergleichsanalyse** — Metriken gegenüberstellen, Gewinner ermitteln
2. **Warum-Analyse** — Welche Posts haben warum performt? (Hook-Patterns, Tageszeit, Sounds)
3. **Empfehlung** — Welche Nische, mit welcher Strategie, in welchem Rhythmus weiter?
4. **30-Tage-Plan für Gewinner** — Batch 2 (10 neue Posts), Posting-Rhythmus (2/Tag?), Landingpage
5. **Alternative bei "weder"** — Neue Nischen-Recherche mit Top-Learnings

---

## Pitfalls

- ❌ **Test starten ohne Canva-Templates** — dann hast du nix zum Posten
- ❌ **Beide Accounts gleiche Hook-Patterns** — testest Nische, nicht Content-Stil
- ❌ **Tracking-Sheet nicht ausfüllen** — ohne Daten ist Entscheidung willkürlich
- ❌ **Cron-Skript ohne Datums-Check** — spamt nach Test-Ende weiter
- ❌ **Profile vor Decision befüllen** — Bio/Link/Profilbild = Einfluss auf Algorithmus
- ❌ **Video Mode statt Photo Mode** — killt Swipe-Interaction
- ❌ **Nur einen Sound verwenden** — Sound ist Ranking-Faktor
- ❌ **Zu früh aufgeben** — 14 Tage Minimum. Algorithmus braucht Zeit
- ❌ **7-Tage-Hook-Pattern-Lock** — Wenn Posts 1-3 floppen, sofort variieren

---

## Siehe auch

- `references/faceless-content-pipeline.md` — Brand System + Canva Bulk Create + Pitch-Varianten
- `references/design-palettes.md` — Farbschemata + Font-Pairings pro Nische
- `references/hook-patterns.md` — 5 Kern-Patterns + Nischen-spezifische Hooks
- `references/slide-layouts.md` — 3 Slide-Layouts mit Build-Anleitung
- `tiktok-business-self-improve` — Meta-Loop für das TikTok-Projekt