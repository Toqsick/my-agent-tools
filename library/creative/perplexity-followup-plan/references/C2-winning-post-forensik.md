# C2 — Winning-Post-Forensik

> **Trigger:** Direkt nach C1-Entscheidung (welche Nische skaliert wird).
> **Wann:** 31.07.2026 (einen Tag nach C1).
> **Ziel:** Aus den Top-3-Posts ein wiederverwendbares Template extrahieren, das mit ChatGPT in 1 Std 30 neue Posts generiert.

## Wann diese Frage stellen

✅ C1 ist durch, du weißt welche Nische weiter läuft
✅ Du hast die Top-3-Posts dieser Nische identifiziert
✅ Du willst auf Autopilot skalieren ohne jeden Post manuell zu brainstormen
❌ NICHT vor C1 — du brauchst erst die Entscheidung welche Posts relevant sind

## Daten die du mitgeben musst

- Top-3-Posts der Gewinner-Nische als **vollständiger Carousel-Text** (alle 7 Cards, nicht nur Titel)
- Views/Save-Rate pro Post (für Ranking)
- Optional: Welche Posts besonders gut funktionierten (subjektiv)

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
Here are my 3 best-performing posts from the 14-day test (titles + cards breakdown):
[PASTE TOP 3 FULL CAROUSEL TEXT]

Reverse-engineer WHY they worked:
1. What psychology pattern does each trigger? (loss-aversion, curiosity, social-proof, fomo, etc.)
2. What Card 1 → Card 2 transition creates the "swipe-pull"?
3. What's the "save-trigger" — the specific card that makes people save vs just like?
4. How can I create 20 MORE posts using the EXACT same pattern but different topics?
5. What's the "fingerprint" I should apply to ALL future posts in this niche?

Output: A reusable post-template (Hook-Pattern → Arc-Pattern → Pitch-Pattern) I can hand to ChatGPT to generate 30 posts in 1 hour.
```

## Output-Format von Perplexity erwartet

- Psychologie-Analyse pro Post (welcher Trigger, warum)
- Card-1→Card-2-Transition-Mechanik
- Save-Trigger-Identifikation
- **20 neue Post-Themen** die das gleiche Pattern nutzen
- **Template-Skelett** (Hook-Pattern → Arc-Pattern → Pitch-Pattern) als wiederverwendbares Format

## Was du mit der Antwort machst

1. **Template-Skelett** in `docs/content-templates/{nische}-winning-pattern.md` speichern
2. **20 neuen Post-Themen** in `canva-bulk-create-{nische}.csv` als Posts 13-32 einpflegen
3. **Mit ChatGPT** (oder Yuno) aus dem Skelett 30 Posts in 1 Std generieren lassen (Prompt: "Wende Template-Skelett-X auf Topic-Liste an, behalte Psychologie-Pattern, varriere Hook-Wording")
4. **A/B-Test-Plan**: Erste 10 der 30 Posts laufen lassen, Save-Rate tracken, vergleichen mit Baseline
5. **Update `pitch-variants.json`**: Neue Hook-Pattern-Typen als `variants` aufnehmen

## Pitfalls

- **Top-3 ≠ repräsentativ**: 14 Posts Sample ist klein. Perplexity kann das Top-Pattern identifizieren, aber ein anderes Pattern könnte mit größerem Sample besser performen.
- **Psychologie ≠ Kausalität**: Perplexity kann sagen "Post #3 funktioniert wegen Loss-Aversion" — aber ob das wirklich die Ursache ist, lässt sich nur mit A/B-Tests bestätigen.
- **Template zu starr**: Wenn du das Template 1:1 auf 30 Posts anwendest, wird die Audience das spüren ("schon wieder das gleiche Pattern"). Variation im Wording ist Pflicht, im Pattern bleibt.
- **Card-2-Transition ist oft subtil**: Was wie ein kleiner Unterschied aussieht, kann den Swipe-Pull ausmachen. Perplexity erkennt das manchmal nicht. Manuell die Übergänge lesen + nachfühlen.

## Cross-Links

- Phase C: [`03-phase-c-post-test.md`](03-phase-c-post-test.md)
- Skill: `tiktok-design-assistant` (Bulk-CSV-Generierung)
- Output-Template: `~/10-Projekte/10-active/yuno-anon-tiktok-business/docs/content-templates/`
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/data/canva-bulk-create-{nische}.csv` (Posts 13-32)
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/config/design/pitch-variants.json`