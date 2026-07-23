# Phase B — During Test (Tag 1-14)

> **Wann:** Sobald echte Performance-Daten vorliegen (frühestens Tag 5).
> **Ziel:** Daten-getriebene Kurs-Korrekturen während des 14-Tage-Tests.
> **Sprache:** Prompts auf Englisch, dieser Wrapper auf Deutsch.

## Verfügbare Folge-Fragen in dieser Phase

| Datei | Frage | Trigger | Output |
|---|---|---|---|
| [`B1-halbzeit-hook-audit.md`](B1-halbzeit-hook-audit.md) | Welche Card-1-Hooks performen wirklich und warum? | Tag 5-7, 5+ Posts/Account | Top-3-Hook-Patterns + Posts 8-14-Vorschläge |
| [`B2-save-rate-diagnose.md`](B2-save-rate-diagnose.md) | Warum ist Save-Rate flach trotz Views? | Tag 7-10, Save-Rate <1% | Diagnose + 3 A/B-Test-Varianten |
| [`B3-comment-mining.md`](B3-comment-mining.md) | Welche Product-Ideen verbergen sich in den Comments? | Tag 8+, sobald Comments kommen | 5 Product-Ideen + Pain-Point-Liste |

## Warum diese Phase kritisch ist

Perplexity kann **Muster in 14 Posts erkennen** die du manuell übersiehst. Besonders die Psychologie hinter den Hooks ("warum funktioniert Post #3 aber nicht Post #7?") ist maschinell leichter zu finden.

## Wichtigste Regel in dieser Phase

**NIEMALS vor Tag 5** fragen — die Datenbasis ist zu dünn. Auch wenn du ungeduldig bist, warte bis du mindestens 5 Posts/Account mit echten Views hast.

## Workflow

1. Tracking-Sheet `14-Tage-Test-Tracking.md` öffnen, relevante Daten extrahieren
2. Passende B-Frage wählen (B1/B2/B3)
3. Daten in den Prompt pasten
4. Perplexity-Run (3-5 Min)
5. Yuno bekommt Antwort → integriert in nächste Posts oder Pitch-Varianten

## Reihenfolge

```
Tag 5-7:  B1 (Halbzeit-Hook-Audit)
           │
           ├── Views kommen aber Save-Rate flach → B2 (Save-Rate-Diagnose)
           │
           └── Comments kommen → B3 (Comment-Mining)
           
Tag 14:    → Phase C (Post-Test Decision)
```