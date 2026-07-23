# A2 — Visual Trend Audit 2026

> **Trigger:** Direkt nach Master-Prompt, parallel zu A1.
> **Wann:** Parallel zu A1 (kann beides in separaten Perplexity-Tabs laufen).
> **Ziel:** Brand-System-Validierung — sind meine Farben/Fonts noch 2026-Standard?

## Wann diese Frage stellen

✅ Master-Prompt ist durch, du hast Kandidaten-Nischen
✅ Du willst wissen ob dein aktuelles `brand-system-{nische}.json` (Navy+Gold für KK, Schwarz+Orange für Prod) noch State-of-the-Art ist
❌ NICHT vor Master-Prompt — du brauchst Nischen-Kontext für sinnvolle Design-Empfehlungen

## Daten die du mitgeben musst

- **Aktuelle Brand-System-Specs** (Farben, Fonts) aus `brand-system-{nische}.json`
- **Aktuelle Test-Nischen** (welche umfärben?)

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
Audit the visual-design trends dominating TikTok in Q2-Q3 2026 specifically for faceless text-overlay carousel accounts. I need:

1. Top 10 color combinations used by accounts with >50k followers in this style
2. Top 5 font pairings (heading + body) that perform on small mobile screens
3. The "dark vs light" debate: what's the 2026 data showing for Save-Rate? Are dark-mode accounts still winning or has light-mode caught up?
4. New design movements I might be missing (e.g. Y2K revival, brutalist, neumorphism, AI-aesthetic)
5. The "AI-feel" problem: how do I avoid my Canva designs looking AI-generated? What human-touches convert best?

Reference real @ handles — I will inspect them.
```

## Output-Format von Perplexity erwartet

- 10 Farb-Pairings mit Hex-Codes (falls verfügbar)
- 5 Font-Pairings mit konkreten Schriftnamen
- Dark-vs-Light-Datensatz (Studien, Surveys, Anekdoten)
- Liste neuer Design-Bewegungen 2026
- "Human-Touches"-Liste (Texture, Imperfektion, Hand-gezeichnete Elemente)

## Was du mit der Antwort machst

1. **Vergleich** mit deinem aktuellen `brand-system-{nische}.json`:
   - Sind meine Farben unter den Top-10? → OK
   - Sind meine Farben out? → Patch mit neuer Kombination
   - Sind meine Fonts unter den Top-5? → OK
   - Sind meine Fonts veraltet? → Canva-Font-Update planen
2. **Dark-vs-Light-Entscheidung**: Falls deine aktuelle Nische Dark-Mode ist und Perplexity sagt "Light-Mode holt auf in 2026" → A/B-Test mit 2 Posts in Light-Mode starten (Posts 9-11)
3. **AI-Feel-Check**: Falls deine aktuellen Designs "AI-generiert" wirken könnten → manuelle Texturen/Grain einbauen
4. **Update** `brand-system-{nische}.json` mit `trend_audit_2026`-Block (Datum + Befund + Action)

## Pitfalls

- **Perplexity zieht manchmal 2022-Listen** — explizit "2026" + "current data" im Prompt (ist schon drin, lass es nicht weg)
- **@-Handles verifizieren** — Perplexity halluziniert manchmal Accounts. Jeden @-Handle selbst auf TikTok checken bevor du ihn als Referenz nimmst.
- **DACH vs US Trends** — Default oft US. Deutsche Faceless-Accounts sind oft konservativer (mehr Dunkelmode, weniger Neon). Perplexity-Fundstellen mit deutschen Gegenbeispielen abgleichen.

## Cross-Links

- Phase A: [`01-phase-a-pre-launch.md`](01-phase-a-pre-launch.md)
- Skill: `tiktok-design-assistant` (Brand-System-Generierung)
- Update-Target: `~/10-Projekte/10-active/yuno-anon-tiktok-business/config/design/brand-system-{nische}.json`