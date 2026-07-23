# C1 — Kill-vs-Double-Down Decision

> **Trigger:** Tag 14 erreicht, alle Daten im Tracking-Sheet.
> **Wann:** 30.07.2026 (Final-Decision-Datum).
> **Ziel:** Daten-getriebene Entscheidung welche Nische weiter läuft — Kill, Double-Down, Pivot oder Hybrid.

## Wann diese Frage stellen

✅ Tag 14 abgeschlossen, alle Posts dokumentiert
✅ Du hast finale Zahlen für beide Accounts (Views, Likes, Saves, Save-Rate, Follower-Delta)
✅ Du hast DM/Comment-Sentiment dokumentiert
❌ NICHT vor Tag 14 — Datenbasis zu dünn
❌ NICHT wenn du schon vorher emotional entschieden hast — Perplexity ist hier der Rationalitäts-Anker

## Daten die du mitgeben musst

Format-Vorschlag:

```
ACCOUNT A (Kreditkarten, @finanzfreiraum):
- Total views (alle 12 Posts): 8.450
- Avg views pro Post: 704
- Total likes: 312
- Total saves: 67
- Avg Save-Rate: 0.79%
- Avg Engagement-Rate: 4.7%
- Follower-Delta: +89
- Beste 3 Posts (Views): #3 "Die eine Karte..." (1.8k), #1 "5 Karten..." (1.2k), #5 (920)
- DM/Comment-Sentiment: "Viel Nachfrage nach Karte-Empfehlung, einige wollen PDF"

ACCOUNT B (Produktivität, @fokusfabrik):
[same format]
```

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
FINAL 14-day test data:

ACCOUNT A (Kreditkarten):
- Total views / avg views / total likes / total saves / save-rate / follower delta: [NUMBERS]
- Top 3 posts (title + views): [LISTE]
- DM/Comment sentiment: [BESCHREIBUNG]

ACCOUNT B (Produktivität):
[same fields]

DECISION NEEDED: Should I
(A) Double down on the winning account,
(B) Kill both and pivot to a new niche (suggest top 3 from earlier research),
(C) Run a hybrid angle (e.g. "Finanzen für Selbstständige" crossover),
(D) Run both in parallel for another 30 days?

Score each option on: probability of 10k followers in 6 months, expected monthly revenue at month 3, time-cost-per-week, risk.

Give me a CONCRETE 30-day rollout plan for the recommended option, with weekly milestones and specific posts to create.
```

## Output-Format von Perplexity erwartet

- Scoring-Matrix: 4 Optionen × 4 Kriterien (Follower-Probability, Revenue, Time-Cost, Risk)
- Empfehlung mit Begründung
- 30-Tage-Rollout-Plan: 4 Wochen × konkrete Posts/Meilensteine

## Was du mit der Antwort machst

1. **Entscheidung in Tracking-Sheet eintragen** unter "Final-Decision"-Block
2. **Wenn (A) Double-Down**: Brand-System der Gewinner-Nische ausbauen, Posts 13-30 draften, ggf. C2 für Template-Extraktion
3. **Wenn (B) Pivot**: Zurück zu Phase A1 mit den 3 neuen Nischen-Vorschlägen
4. **Wenn (C) Hybrid**: Neue Nische "Finanzen für Selbstständige" als dritte Brand-Pipeline aufsetzen
5. **Wenn (D) Parallel**: 30 Tage verlängern mit angepasstem Test-Plan

## Pitfalls

- **Daten-Liebe kann täuschen**: 14 Posts sind immer noch wenig. Perplexity kann Trends zeigen, aber eine zweite 14-Tage-Runde kann andere Ergebnisse liefern.
- **Save-Rate > Views**: Wenn Account A mehr Views hat aber Account B 3× höhere Save-Rate → B ist langfristig besser (bessere Conversion), auch wenn A "mehr Reichweite" hat. Perplexity kann das verwechseln wenn du nicht explizit betont.
- **Bauchgefühl vs Daten**: Wenn Perplexity klar Option A empfiehlt aber dein Bauchgefühl B sagt → nicht sofort Bauch ignorieren. Perplexity hat keine Information über deine Freude-Quote, deine Lerneffekte, deine Domain-Expertise.

## Cross-Links

- Phase C: [`03-phase-c-post-test.md`](03-phase-c-post-test.md)
- Daten-Quelle: `~/Dokumente/Obsidian Vault/03 Projekte/Yuno-Anon-TikTok-Business/14-Tage-Test-Tracking.md` (Final-Decision-Block)
- Bei Pivot zurück zu: [`A1-niche-white-space.md`](A1-niche-white-space.md)