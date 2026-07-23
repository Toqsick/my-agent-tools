# B1 — Halbzeit-Hook-Audit

> **Trigger:** Sobald du 5+ Posts pro Account mit echten Views hast.
> **Wann:** Tag 5-7 (passt zum Halbzeit-Check im `14-Tage-Test-Tracking.md`).
> **Ziel:** Top-Hook-Patterns identifizieren + Posts 8-14 strategisch planen.

## Wann diese Frage stellen

✅ Mindestens 5 Posts pro Account gepostet
✅ Alle haben echte Views (nicht 0)
✅ Save-Rate + Completion% sind dokumentiert
❌ NICHT vor Tag 5 — Datenbasis zu dünn für Muster
❌ NICHT wenn beide Accounts < 200 Views auf allen Posts — dann ist das Hook-Problem grundlegender, andere Strategie nötig

## Daten die du mitgeben musst

Format-Vorschlag (entnommen aus `14-Tage-Test-Tracking.md`):

```
Account A (@finanzfreiraum, Kreditkarten):
Post #1 — "5 Karten die jeder Vielreisende kennen sollte" — 1200 Views, 45 Likes, 12 Saves, 67% Completion
Post #2 — "Du nutzt deine Karte falsch" — 800 Views, 28 Likes, 8 Saves, 71% Completion
... (alle Posts)

Account B (@fokusfabrik, Produktivität):
[same format]
```

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
Here is my actual 7-day TikTok data from a faceless German test (2 accounts):

ACCOUNT 1 — `@finanzfreiraum` (Kreditkarten):
[paste: post title / views-24h / likes / saves / completion%]

ACCOUNT 2 — `@fokusfabrik` (Produktivität):
[paste same columns]

ANALYZE:
1. Which specific post titles (Card 1 hooks) are working best, and WHY (psychology pattern: loss-aversion? curiosity? listicle?)
2. Which specific topics are outperforming within each niche?
3. Are there signals that ONE niche is clearly winning, or is it still too early?
4. What should I change in posts 8-14 to maximize the winner?
5. Any specific German phrases in the Card-1 text that correlate with high Save-Rate?

Be brutally honest — if neither account is working, say so.
```

## Output-Format von Perplexity erwartet

- Ranking der Top-3-Hooks pro Account mit Psychologie-Analyse
- Cross-Account-Vergleich (welche Nische gewinnt?)
- Konkrete Posts 8-14-Vorschläge (Card-1-Hooks in German)
- Ehrliches Fazit: "Funktioniert" / "Funktioniert nicht" / "Braucht mehr Daten"

## Was du mit der Antwort machst

1. **Top-3-Hook-Patterns** in `pitch-variants.json` als neue `variants` hinzufügen (mit `type: hook-pattern-X`)
2. **Posts 8-14** in `canva-bulk-create-{nische}.csv` mit den empfohlenen Hooks draften
3. **Wenn Perplexity "weder funktioniert" sagt**: Stop-Kriterium aus `14-Tage-Test-Tracking.md` anwenden, Hooks neu brainstormen (ggf. Phase A1 nochmal)
4. **Wenn klare Nischen-Wahl**: Fokus auf Gewinner, Posts im Verlierer-Account pausieren

## Pitfalls

- **Sample-Size-Irrtum**: 5 Posts sind statistisch nicht signifikant. Perplexity kann Trends zeigen, aber nicht "beweisen".
- **Views ≠ Erfolg**: 5000 Views mit 0.1% Save-Rate ist schlechter als 500 Views mit 5% Save-Rate (Conversion-Indikator!). Perplexity kann das verwechseln wenn du nicht explizit Save-Rate betonst.
- **Completion% vs Saves**: Completion% zeigt ob Content fesselt, Saves zeigen ob Content wertvoll ist. Beide zählen — getrennt analysieren.

## Cross-Links

- Phase B: [`02-phase-b-during-test.md`](02-phase-b-during-test.md)
- Daten-Quelle: `~/Dokumente/Obsidian Vault/03 Projekte/Yuno-Anon-TikTok-Business/14-Tage-Test-Tracking.md`
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/config/design/pitch-variants.json`
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/data/canva-bulk-create-{nische}.csv`