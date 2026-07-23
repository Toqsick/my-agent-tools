# D1 — Content-Multiplikations-Strategie

> **Trigger:** Nische bestätigt, 1-2 Posts/Tag konsistent.
> **Wann:** Anfang Monat 2 (kurz nach C2-Entscheidung).
> **Ziel:** 10× Content-Output ohne Burnout + Wochen-Batch-Workflow.

## Wann diese Frage stellen

✅ Gewinner-Nische aus 14-Tage-Test steht
✅ Du hast schon 14+ Posts produziert, das Pattern ist klar
✅ Du willst auf 30 Posts/Woche hoch ohne Content-Quality-Verlust
❌ NICHT vor Tag 14 — du brauchst erst Winning-Pattern (C2)
❌ NICHT wenn du schon burnout-gefährdet bist (lieber D4 zuerst)

## Daten die du mitgeben musst

- Aktuelle Posts/Woche (z.B. 14)
- Ziel-Posts/Woche (z.B. 30)
- Verfügbare Content-Production-Stunden pro Woche
- Optional: Aktuelle Burnout-Signale (zu viel, zu wenig Variation, etc.)

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
I have a winning niche + a winning post-pattern. Now I need to multiply content 10× without burning out or losing quality. Build me a content-multiplication system:

1. How do I generate 30 posts/week from 1 winning template without audience fatigue?
2. The "topic-cluster" method: what are 7 sub-topic clusters in my niche that I can rotate through for 6 months without overlap?
3. User-Generated Content hack: how do I ethically recycle comments, DMs, and questions from my audience into new posts?
4. Trend-jacking without face/voice: how do I jump on trending TikTok sounds/audio without showing face? (audio-only carousels work?)
5. The "evergreen vs trending" balance: what % of my posts should be evergreen (always-relevant) vs trending (time-sensitive)?
6. Batch-production workflow: what's the minimum-viable weekly workflow to produce 14 posts in 1-2 days?

Reference faceless German accounts that scaled from 0 to 100k — what did their content calendar look like?
```

## Output-Format von Perplexity erwartet

- 30-Posts/Woche-Generation-System (Template + Variation)
- **7 Topic-Cluster** mit jeweils 5-10 Sub-Themen
- UGC-Recycling-Strategie (welche Comment-Typen eignen sich?)
- Audio-Only-Carousel-Trendjacking-Mechanik
- Evergreen/Trending-Ratio-Empfehlung (typisch 70/30)
- Wochen-Batch-Workflow (welche Tage, welche Stunden, welche Tasks)

## Was du mit der Antwort machst

1. **Topic-Cluster** in `docs/content-strategy/{nische}-topic-clusters.md` speichern
2. **Wochen-Batch-Workflow** als Cron-Job-Definition in `~/.hermes/scripts/yuno-tiktok-batch.sh` (oder vergleichbar) ablegen
3. **UGC-Recycling-Pipeline**: Comments aus B3 als Post-Ideen in `canva-bulk-create-{nische}.csv` Posts 33-50 einpflegen
4. **Audio-Trendjacking-Liste**: Sounds auf TikTok bookmarken die zu faceless carousels passen
5. **Skalierungs-Realitätscheck**: Falls Perplexity 30 Posts/Woche empfiehlt aber du nur 14 schaffst → D1-Output ist idealisiert, Manuell anpassen

## Pitfalls

- **Audience-Fatigue ist real**: Wenn du 30 Posts/Woche mit dem exakt gleichen Template postest, merkt das die Audience nach 2-3 Wochen. Variation im Hook-Wording ist Pflicht.
- **Topic-Cluster ≠ endlos**: 7 Cluster × 10 Themen = 70 Posts. Dann ist Schluss mit Evergreen. Du brauchst laufend neue Cluster oder eine Trendjacking-Pipeline.
- **Batch-Production ≠ Bulk-Upload**: Du kannst 14 Posts in 2 Tagen produzieren aber nicht 14 Posts an einem Tag hochladen (TikTok penalty für Mass-Upload).
- **Burnout-Symptome ernst nehmen**: Wenn D1 antwortet "30 Posts/Woche sind machbar mit diszipliniertem Workflow" und du fühlst dich schon bei 14 Posts erschöpft → erst D4 (Risk-Audit) für Burnout-Prevention.

## Cross-Links

- Phase D: [`04-phase-d-scale-mode.md`](04-phase-d-scale-mode.md)
- Cron-Integration: Skill `tiktok-business-self-improve`
- Output-Template: `~/10-Projekte/10-active/yuno-anon-tiktok-business/docs/content-strategy/`