# A1 — Nischen-White-Space-Check

> **Trigger:** Nachdem der Master-Prompt die Top-15-Nischen geliefert hat.
> **Wann:** Sofort danach (vor A2/A3, weil die Antwort beeinflusst welche Nischen überhaupt in Frage kommen).
> **Ziel:** Aus den Master-Empfehlungen die 3 mit echtem First-Mover-Vorteil isolieren.

## Wann diese Frage stellen

✅ Du hast vom Master-Prompt eine Liste mit 15-20 Nischen bekommen
✅ Du willst vor der Brand-System-Erstellung wissen welche 3 du wirklich angehen sollst
❌ NICHT vor dem Master-Prompt — du brauchst Input-Material

## Daten die du mitgeben musst

- **Top-5-Nischen aus Master-Prompt** (Namen + kurze Beschreibung)
- Optional: Welche CPM-/Save-Rate-Schätzungen der Master-Prompt gegeben hat

## Prompt (1:1 in Perplexity Deep Research einfügen)

```
Given these 5 niches: [paste top 5 from master prompt], check each for "white space" — i.e. demand signals (search volume, rising TikTok hashtags, Reddit threads in r/Finanzen, r/Selbststaendig, r/productivity, etc.) BUT low supply of faceless German accounts in this exact sub-niche.

Use: TikTok Creative Center (Germany filter), Google Trends DE-AT-CH, Reddit search, Amazon DE bestseller lists in matching categories, Digistore24 vendor count.

For each:
- White-space score (1-10)
- 3 sub-niche angles that are UNDERSERVED (e.g. "Kreditkarten für Selbstständige" instead of generic "Kreditkarten")
- First-mover advantage timeline: how long before saturation?
```

## Output-Format von Perplexity erwartet

- Tabelle mit 5 Zeilen (eine pro Nische) + 8 Spalten (Score, Sub-Angle 1-3, Sättigungs-Timeline)
- Optional: Sub-Nischen-Hierarchie als Bullet-Tree
- Realitätscheck: Wenn Perplexity keine konkreten Daten findet, sag das — nicht erfinden

## Was du mit der Antwort machst

1. **Top-3 nach White-Space-Score** in dein Tracking-Sheet eintragen
2. **Sub-Nischen-Angles** als neue Test-Ideen für Posts markieren (z.B. "Kreditkarten für Selbstständige" statt nur "Kreditkarten")
3. Falls eine Nische **Score < 4** hat: aus dem 14-Tage-Test rausnehmen und durch bessere Alternative ersetzen
4. Sub-Nischen-Angles fließen in `pitch-variants.json` (Phase `best_for`-Tags) und in `canva-bulk-create-{nische}.csv` (neue Card-1-Hooks) ein

## Pitfalls

- **Perplexity unterschätzt oft deutsche Reddit-Aktivität** — DACH-Subreddits wie r/Finanzen, r/Selbststaendig, r/Pflege, r/azubis sind klein aber hochrelevant. Falls keine Reddit-Treffer: manuell in den Subreddits suchen.
- **TikTok Creative Center ist nur für Werbe-Treibende zugänglich** — Perplexity nutzt manchmal öffentliche Daten, dann sind die Zahlen niedriger als die Realität. Mit Skepsis lesen.
- **"Underserved" ≠ "kein Interesse"** — Wenn Perplexity keine Faceless-Accounts findet, kann das heißen: (a) echter White-Space oder (b) das Format funktioniert in der Nische nicht. Manuell prüfen.

## Cross-Links

- Phase A: [`01-phase-a-pre-launch.md`](01-phase-a-pre-launch.md)
- Master-Prompt: Initial-Session (separat, nicht Teil dieses Skills)
- Output-Integration: `~/10-Projekte/10-active/yuno-anon-tiktok-business/config/design/pitch-variants.json`