# Kostenlose Cloud-Modelle — Limits, Quotas und "der Haken"
Stand: Juni 2026

## Übersicht: Die besten kostenlosen Optionen

| Rang | Modell | Provider | Kosten | Limit | Haken |
|------|--------|----------|--------|-------|-------|
| 1 | MiniMax-M3 | Nous/Direct | €0 | ~20 req/min, ~200/day | Session-Limit ~30, dann 10min Cool-down |
| 2 | DeepSeek V4 Flash | Nous Portal | €0 | ~20 req/min, ~200/day | Rate-Limit bei Multi-Agent |
| 3 | Qwen3.6-35b | Nous Portal | €0 | ~20 req/min, ~200/day | Praktisches Limit nach ~50 schnellen Requests |
| 4 | Step-3.7-Flash | Nous Portal | €0 | ~20 req/min, ~200/day | Kleinere Modelle schwächer |
| 5 | Gemini 2.0 Flash | Google AI Studio | €0 | 15 req/min, 1500/day | Google-Konto nötig |
| 6 | Groq Llama 3.1 70B | Groq | €0 | 30 req/min, 10K tokens/min | Kleinster Context |
| 7 | OpenRouter Free | OpenRouter | €0 | 50/day (1 key) oder 200/day ($10+) | Freetier unstabil |

## Nous Portal Free-Tier

### Verfügbare Free-Modelle
- deepseek-v4-flash: 1M Context, Reasoning + Code, Rate-Limit bei Multi-Agent
- minimax-m3: 1M Context, Allrounder/Agentic, Session-Limit ~30 Requests
- qwen/qwen3.6-35b-a3b: 1M Context, kostenlos, stark
- stepfun/step-3.7-flash: 128K Context, schnell, gut
- meta/llama-3.1-8b: 128K Context, klein, schnell

### Limits
- Free Tier: ~20 req/min, ~200/day praktisches Limit
- 429 Error ohne Warning — Hermes retryed automatisch (3x)
- MiniMax M3 Session-Limit: ~30 Requests → 10-min Cool-down
- Kein Prioritätsserver: Free-Tier wird bei Hochlast deprioritisiert

## MiniMax M3 — Details
- Release: 1. Juni 2026 (frisch!)
- Architektur: Open-Weight MoE, 1M Context
- Direct: Together AI (100 queries/day free), MiniMax Direct (10K ops free)
- Via Nous: ~20 req/min, ~200/day
- Stärken: Frontier Coding, Agentic Work, ultra-long context
- Benchmark: GPQA Diamond ~91%, Terminal Bench ~69.7
- Session-Limit: ~30 Requests → 10min Cool-down

## Empfohlene kostenlose Kombination für Hermes
```
Primär:         lokale qwen3.5-9b (Ollama) — UNLIMITED
Cloud-Fallback: deepseek-v4-flash (Nous Free) — ~200/day
Lange Docs:     minimax-m3 (Nous Free) — ~200/day
Schnelle Tasks: step-3.7-flash (Nous Free) — ~200/day
Total:          ~600+ Cloud-Requests/day + Unlimited lokal
```

## Anti-Patterns
- 3 parallele Sub-Agenten auf Nous Free → 429 bei allen → Sequentiell oder lokalen Critic
- Think Max bei jedem Request → 2x Output-Tokens → Non-Think für einfache Tasks
- Free-Tier für Production → Ausfall bei 429 → Paid-Tier oder lokal
- MiniMax M3 Session ignoriert → Cool-down nach 30 → Batches <20 Requests
