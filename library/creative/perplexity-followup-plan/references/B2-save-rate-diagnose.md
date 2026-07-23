# B2 — Save-Rate-Diagnose

> **Trigger:** Views kommen aber Save-Rate flach (~0.5-1%).
> **Wann:** Tag 7-10 (nach B1, weil du erst verstehen musst welche Posts laufen bevor du Save-Probleme diagnostizierst).
> **Ziel:** Verstehen warum Save-Rate flach bleibt + 3 konkrete A/B-Test-Varianten.

## Wann diese Frage stellen

✅ Views auf Posts: 500-2000+ (Hook funktioniert)
✅ Save-Rate konstant < 1% über mehrere Posts
✅ Du hast schon B1 gemacht (sonst fehlt Kontext)
❌ NICHT wenn Save-Rate > 2% stabil → dann läuft's, kein A/B-Test nötig
❌ NICHT wenn Views < 500 → dann ist Hook-Problem vorrangig, B1 zuerst

## Daten die du mitgeben musst

- Aktuelle Save-Rate (Durchschnitt + pro Post)
- 2-3 Beispielposts mit ihren Carousel-Inhalten (alle 7 Cards)
- Aktueller Pitch-Text auf Card 7

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
My Save-Rate is flat (~0.5-1%) despite getting views (500-2000 per post). The views prove the hook works, but people aren't saving. Diagnose:

1. What does Save-Rate actually signal in TikTok's algorithm? (Intent signal vs preference signal)
2. Which Carousel-Arc types correlate with high Save-Rate (e.g. checklists, swipe-files, step-by-step) vs low Save-Rate (e.g. pure entertainment, storytelling)?
3. For my two niches (Kreditkarten, Produktivität), what SPECIFIC post formats in these niches typically hit >3% Save-Rate? Give me 5 concrete examples in German.
4. Is my Card 7 (the pitch card) killing Save-Rate? Should I move the pitch to bio/profile and keep Card 7 purely value?
5. Quick experiment: give me 3 A/B-test variations of Card 1 + Card 7 that might unlock Save-Rate. I'll test them on posts 9-11.
```

## Output-Format von Perplexity erwartet

- Algorithmus-Erklärung: Save-Rate = Intent-Signal (TikTok pusht Content mit hoher Save-Rate an ähnliche User)
- Liste von Carousel-Arc-Typen mit Save-Rate-Korrelation
- 5 deutsche Post-Beispiele mit >3% Save-Rate (in deiner Nische)
- Ja/Nein-Antwort zu "Card 7 Pitch killt Saves"
- 3 A/B-Test-Varianten: jeweils Card-1-Hook-Variante + Card-7-Variante

## Was du mit der Antwort machst

1. **Posts 9-11** als A/B-Test anlegen:
   - Post 9: Original-Pattern (Baseline)
   - Post 10: Card-1-Variante A (Perplexity-Vorschlag 1)
   - Post 11: Card-7-Variante B (Perplexity-Vorschlag 2)
2. **Tracking-Sheet** um A/B-Test-Spalte erweitern ("Variante: A/B/C")
3. **Nach 3 Posts vergleichen**: Welche Variante hat höhere Save-Rate?
4. **Bei klarem Sieger**: Gewinner-Variante als neuen Standard in `pitch-variants.json` und `canva-bulk-create-{nische}.csv`
5. **Falls Card 7 Pitch das Problem ist**: Pitch-Default von Card 7 auf Bio verschieben (Card 7 wird dann Value-Abschluss)

## Pitfalls

- **Save-Rate ≠ Conversion-Rate** — Save bedeutet "ich will das später nochmal anschauen", nicht "ich will das kaufen". Aber: Save-Rate korreliert stark mit späterer Conversion, weil Save-User öfter zurückkommen.
- **"Save-Prompt"-Wortlaut zählt**: "Speicher dir das für später" performt anders als "Screenshot das" oder gar kein Save-Prompt. Perplexity kann das analysieren wenn du explizit fragst.
- **Card 7 Pitch killt nicht zwangsläufig Saves** — manchmal ist das Problem früher (Card 4-5 zu werblich, oder Card 7 pitch-Text zu lang). Perplexity schaut nur auf das was du pastest.

## Cross-Links

- Phase B: [`02-phase-b-during-test.md`](02-phase-b-during-test.md)
- Daten-Quelle: `~/Dokumente/Obsidian Vault/03 Projekte/Yuno-Anon-TikTok-Business/14-Tage-Test-Tracking.md`
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/data/canva-bulk-create-{nische}.csv` (Posts 9-11 als A/B-Test)