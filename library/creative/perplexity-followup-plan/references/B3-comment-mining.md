# B3 — Comment-Mining

> **Trigger:** Sobald du nennenswerte Comments bekommst (10+ pro Post auf den Top-Posts).
> **Wann:** Tag 8-10 (parallel zu B1/B2 möglich, weil andere Daten-Quelle).
> **Ziel:** Kommentare sind kostenlose Marktforschung — direkt umsetzbare Product-Ideen extrahieren.

## Wann diese Frage stellen

✅ Mindestens 30 echte Comments aggregiert über mehrere Posts
✅ Comments auf Deutsch (DACH-Audience)
✅ Du willst wissen welche Fragen die Audience hat (= Product-Ideen)
❌ NICHT wenn nur 1-2 Comments pro Post — Sample zu klein
❌ NICHT wenn Comments fast nur Spam/Bots sind — manuell filtern vor Perplexity

## Daten die du mitgeben musst

- 30+ echte Kommentare (gemischte Posts, anonymisiert falls nötig)
- Optional: Welche Posts die Comments bekommen haben (für Context)

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
Here are 30 actual comments from my TikTok posts (paste them below):
[COMMENTS]

MINE these for:
1. Top 5 questions people are asking → product-idea gold (each question = a potential PDF)
2. Pain points mentioned → which sub-niche angles am I missing?
3. Emotional language used → which feelings should my next 10 posts amplify?
4. Negative comments / objections → how do I address these in Card 2-6 to remove friction?
5. Profile-visit signals → are comments like "wo finde ich das?" appearing? (means people want the product)

[paste 30+ German comments]
```

## Output-Format von Perplexity erwartet

- Top-5-Fragen (jede Frage = 1 PDF-Produkt-Idee)
- Pain-Point-Liste (Emotionen + konkrete Probleme)
- Emotional-Language-Wordlist (welche Trigger-Wörter häufig vorkommen)
- Objection-Handling-Vorschläge (wie in Card 2-6 einbauen)
- Profile-Visit-Signal-Count ("wo finde ich das?" / "mehr infos?" / "wie geht das?")

## Was du mit der Antwort machst

1. **Top-5-Product-Ideen** in neues File `docs/product-ideen-aus-comments-{datum}.md` speichern
2. **Pain-Points** in `pitch-variants.json` als neue Hook-Patterns aufnehmen (z.B. "Schmerz-X-Trigger" Variante)
3. **Emotional-Language-Wordlist** als Card-2-3-Vokabular in `canva-bulk-create-{nische}.csv` einbauen
4. **Objection-Handling**: Neue Posts 12-14 mit Adressierung der Top-3-Objections draften
5. **Profile-Visit-Signals > 5**: Das ist Conversion-Indikator → Digistore24-Landingpage checken (kann sie die Nachfrage bedienen?)

## Pitfalls

- **"Mehr davon!" ist KEIN Product-Idea** — Perplexity kann das mit echten Fragen verwechseln. Im Prompt klar trennen.
- **Spam/Bot-Kommentare vorher filtern** — Perplexity kann nicht erkennen welche Comments echt sind. Manuell aussortieren.
- **Negativ-Kommentare sind wertvoll** — Perplexity neigt dazu Negative als "ignorieren" zu werten. Im Prompt ("how do I address these in Card 2-6") steht explizit das du sie nutzen willst.
- **Sprache beachten** — Perplexity übersetzt manchmal deutsche Kommentare ins Englische und verliert dabei Nuancen. Antwort auf Deutsch anfordern wenn nötig.

## Cross-Links

- Phase B: [`02-phase-b-during-test.md`](02-phase-b-during-test.md)
- Daten-Quelle: TikTok-App Comments exportieren (Copy-Paste)
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/config/design/pitch-variants.json`
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/data/canva-bulk-create-{nische}.csv`