# Phase A — Pre-Launch Research

> **Wann:** JETZT — parallel zum Master-Prompt oder direkt danach.
> **Ziel:** Lücken füllen die der Master-Prompt nicht abdeckt (White-Space, Visual-Trends, Algorithmus-Wortliste).
> **Sprache:** Prompts auf Englisch (Perplexity performt besser), dieser Wrapper auf Deutsch.

## Verfügbare Folge-Fragen in dieser Phase

| Datei | Frage | Trigger | Output |
|---|---|---|---|
| [`A1-niche-white-space.md`](A1-niche-white-space.md) | Welche der Top-Nischen hat echten White-Space (Demand > Supply)? | Nach Master-Prompt | Top-3-Nischen + Sub-Niche-Angles |
| [`A2-visual-trend-audit.md`](A2-visual-trend-audit.md) | Welche Design-Trends dominieren 2026 faceless TikTok? | Parallel zu A1 | Brand-System-Updates für Test-Nischen |
| [`A3-algorithmus-wortliste.md`](A3-algorithmus-wortliste.md) | Welche deutschen Wörter triggern TikToks Commercial-Intent-Filter? | Vor erstem Upload | Safe-Word-Liste für alle Card-1-Hooks |

## Warum diese Phase kritisch ist

Bevor du 1-2 Posts/Tag produzierst, willst du 3 Dinge wissen:
1. **Existiert die Nische überhaupt ohne 50 etablierte Accounts?** (A1)
2. **Sind meine Farben/Fonts noch 2026-tauglich?** (A2)
3. **Schieße ich mir mit falschen Wörtern selbst ins Knie?** (A3)

Alle drei dauern jeweils 3-5 Min Perplexity-Run und können Wochen falscher Content-Produktion sparen.

## Workflow

1. Wähle die passende A-Frage aus obiger Tabelle
2. Lade die entsprechende `.md`-Datei aus `references/`
3. Fülle die im Prompt genannten Variablen (z.B. "Top-5 aus Master-Prompt")
4. Kopiere den Prompt 1:1 in Perplexity Deep Research
5. Warte 3-5 Min auf die Antwort
6. Paste die Antwort zurück an Yuno → ich übersetz die Kern-Insights und integriere sie in `pitch-variants.json` oder `brand-system-{nische}.json`

## Reihenfolge-Empfehlung

```
Master-Prompt (Initial-Session)
    │
    ├──→ A1 (sofort) — Nischen-White-Space
    │
    ├──→ A2 (parallel zu A1) — Visual-Trends
    │
    └──→ A3 (vor erstem Upload, ASAP) — Algorithmus-Wortliste
```