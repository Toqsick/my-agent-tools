---
name: model-selector
description: >-
  Use when user asks for choosing an LLM from the Nous Portal, comparing models by speed, reasoning, code ability, or price, resolving provider-specific model names, or selecting a local model for limited VRAM. NOT for running formal benchmark evaluations or deploying a model server. Provides workload-based recommendations, price checks, provider naming rules, fallback considerations, and model-switch handoffs.
version: 1.2.0
author: yuno
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - LLM
    - model-selection
    - nous-portal
    - pricing
    related_skills:
    - deep-model-evaluation
    - local-ml-hosting
lane: koenigin
reasoning_effort: xhigh
trigger_keywords: ['model', 'price', 'model-selector', 'choosing', 'llm']
keywords: ['model', 'price', 'provider', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['local-llm-benchmark', 'local-ml-hosting', 'nous-multi-lane-routing']
---



# Model Selector Guide

Welches Modell für welche Aufgabe im Nous Portal / Hermes Agent.

## Schnellauswahl

### Alltag & Schnelligkeit (gratis/niedrig)
- **openrouter/owl-alpha** — Gratis! 0$/token, 1M Context, #1 Free-Modell auf OpenRouter. Perfekt für Subagenten-Scouts im Bienenschwarm
- **qwen/qwen3.6-35b-a3b** — Allrounder, Code, Daily-Workflows, GreyScript, Hermes-Konfiguration (1M ctx, kostenlos)
- **stepfun/step-3.7-flash:free** — Schnellste Antwort, gute Qualität, kostenlos
- **google/gemini-2.0-flash** — Stark, schnell, kostenlos über Nous
- **meta/llama-3.1-8b-instruct** — Klein, schnell, für Simple-Aufgaben

### Code & Architektur (mittel)
- **deepseek/deepseek-v4-flash** — Reasoning + Code-Review, 13B aktiv (284B total), 3 Reasoning-Modi
- **qwen/qwen3.7-max** — Agent-Frontier-Modell (Mai 2026), schlägt Claude Opus 4.6 auf Agent-Benchmarks
  - $1.25/M Input, $3.75/M Output (50% Rabatt aktiv, Stand Jun 2026)
  - 1M Context, 65.5K Output, 54 tok/s, Tool-Error-Rate nur 2.31%
  - Nr. 1 App auf OpenRouter: Hermes Agent (65.1B Tokens)
  - Prompt Caching eingebaut (~47% Cache-Hit-Rate in der Praxis)
  - HINWEIS: qwen3.7-plus auf OpenRouter aktuell NICHT verfügbar — nur Max
- **moonshotai/kimi-k2.6** — Open-Weight Multimodal-Agent (Apr 2026), 1B MoE / 32B aktiv
  - $0.684/M Input, $3.42/M Output — günstiger als Qwen für Input-heavy Workloads
  - 262K Context (kleiner als Qwen), Open-Weight (auf HuggingFace)
  - GPQA Diamond: 91.1%, Agentic Index: 66.0 (besser als 94% der Modelle)
  - Stärken: Long-Horizon Coding, Multi-Agent Orchestration, UI/UX Generation
  - Cache-Pricing: $0.15–$0.37/M (je nach Provider), hohe Cache-Hit-Raten möglich
- **moonshotai/kimi-k3** — Frontier-Tier Coding-Modell (Jul 2026), 2.8T MoE / ~50B aktiv
  - **OpenRouter Model-ID bestätigt:** `moonshotai/kimi-k3` (Stand 19.07.2026, live getestet)
  - **Alias:** `~moonshotai/kimi-latest` zeigt auf die aktuelle K3-Version
  - **Let's-open-3T-Klasse**, #4 von 189 auf AA Intelligence Index
  - **SWE Marathon 42.0 🥇 + Program Bench 77.8 🥇** — beste Coding-Benchmarks ever
  - 1M Context-Window, native Vision, MXFP4-Quant (QAT-trained, nicht Post-Hoc)
  - K3 Max (Chat/Agent) + K3 Swarm Max (Parallel-Processing) Varianten
  - **Preis:** $3/M Input, $15/M Output (cached: $0.30/M) — teuerstes chinesisches Modell
  - **Open Weights:** 27.07.2026 (~1.4 TB! Nur mit Multi-Node-Cluster self-hostbar)
  - **Limitations:** Always-on reasoning (79% Token overhead!), keine Effort-Level, überschätzt sich bei Ambiguity
  - Für 8GB-VRAM-Setup API-only — Self-Hosting nicht möglich
  - **OpenRouter API-Verifikation:** `moonshotai/kimi-k3` ist unter den 338+ OpenRouter-Modellen gelistet. Abfrage über `GET /api/v1/models` mit `Authorization: Bearer $KEY` und Filter auf `moonshotai/` oder `kimi` im ID-Feld bestätigt Verfügbarkeit.

### Tiefe Analyse & Reasoning (höher)
- **anthropic/claude-sonnet-4.6** — Nuance, tiefes Verständnis, präzise Formatierung (aktueller Sonnet)
- **anthropic/claude-opus-4.8** — Premium-Frontier (Jun 2026), GPQA Diamond 93.5%, Code-Agent-Sweep. Bester Single-Call für tiefe Architektur, komplexe System-Designs, und LLM-Persona-Work. Teuer — nur einsetzen wenn's drauf ankommt. Modell-ID: `anthropic/claude-opus-4.8`
- **gpt-4o** — Allgemein stark, teurer
- **claude-3-opus** — Goldstandard für komplexe Logik (älter, teurer)

### Reasoning-Modelle (speziell)
- **deepseek/deepseek-v4-flash** — 3 Modi: Non-Think (direkt), Think High (mittel), Think Max (voll, bis 384K Token)
  - Reasoning-Nähe zu V4-Pro, 13B aktive Parameter (284B total)
  - V4 vereint Standard- und Reasoning-Fähigkeiten in einem Modell
  - **Hermes Config Mapping:** Reasoning-Modus über `agent.reasoning_effort` steuern.
    `none/minimal` = Non-Think, `low/medium` = Think High, `high/xhigh` = Think Max.
    ⚠️ **NICHT xhigh global setzen!** Kostet 20-30% extra Output-Tokens bei JEDER Nachricht.
    Global auf `medium` lassen, nur bei Bedarf per `/reasoning xhigh` aktivieren:
    `hermes config set agent.reasoning_effort medium`  # global
    `/reasoning xhigh`  # nur für komplexe Multi-Step-Analysen
- **qwen/qwen3.7-max** — Unterstützt `enable_thinking` + `preserve_thinking` (für Agentic Tasks empfohlen)
  - GPQA Diamond: 92.4% (besser als Opus 4.6 mit 91.3% und DS-V4-Pro mit 90.1%)

## Wichtige Fakten

### ⚠️ Provider-spezifische Modell-Namen
Die Modell-Namen unterscheiden sich je nach Provider — nicht davon ausgehen dass das OpenRouter-Format überall gilt!

| Provider | V4 Flash Name | V4 Pro Name |
|---|---|---|
| **Nous Portal** | `deepseek-v4-flash` | `deepseek-v4-pro` |
| **OpenRouter** | `deepseek/deepseek-v4-flash` | `deepseek/deepseek-v4-pro` |
| **DeepSeek direkt** | `deepseek-v4-flash` (via API) | `deepseek-v4-pro` |

⚠️ **V4 Flash ≠ Reasoning-Modus!** DeepSeek V4 Flash und V4 Pro sind separate Modelle, JEDES mit eigenen Reasoning-Modi (Think High / Think Max). Nicht verwechseln! Die Benennung "deepseek-v4-flash" ist der Modell-Name, nicht eine Einstellung.

- Größeres Tier (Plus/Max) = bessere Qualität, NICHT mehr Kontextfenster
- Kontextfenster ist eine harte Grenze: Qwen unterstützt bis 1M Token (~Roman)
- Reasoning-Modus wird via `agent.reasoning_effort` in Hermes config gesteuert:
  `hermes config set agent.reasoning_effort medium` (global sparsam)
  `high/xhigh` nur per `/reasoning xhigh` für komplexe Analysen.
  CLI-Persistenz: Braucht keinen `/reset` — wirkt sofort auf nächsten LLM-Call.
- ⚠️ **delegation.model/provider MÜSSEN gesetzt sein!** Wenn leer, nutzen Sub-Agenten das Default-Modell (→ kann teuer werden).
  `hermes config set delegation.model "deepseek/deepseek-v4-flash"` (free via Nous)
  `hermes config set delegation.provider "nous"`
  Ohne diese Settings hat Basti ~$174/Woche nur für Sub-Agenten mit Opus 4.8 verloren.
- Yuno-Default: Qwen3.6 oder Step-Flash für 90% der Aufgaben
- Agent-Schwerarbeit (Discord-Bot, Cron-Architektur): qwen3.7-max empfohlen
- Premium-Analyse (Persona, Architektur, System-Design): claude-opus-4.8
- qwen3.7-plus auf OpenRouter aktuell nicht verfügbar (Stand Jun 2026)
- Nur bei echten Analyse-Aufgaben Claude Sonnet/DeepSeek-Reasoning einplanen

## Modell-Handoff nach Wechsel

Jeder Modell-Wechsel braucht ein Briefing, damit das neue Modell ohne Reibungsverlust weiterarbeiten kann.

- **Automatisch:** Der Morning-Cron generiert ein Kurzbriefing (`~/MODEL_HANDOFF_SHORT.md`)
  mit Projekt-Status + Blocker.
- **Ausführlich:** Volles Handoff (`~/MODEL_HANDOFF.md`) mit "Tips for the new model"-Sektion,
  in der selbst erlernte Pitfalls weitgegeben werden. Halte sie aktuell — das nächste Modell startet damit.

Referenzen
- `references/model-details.md` — Detaillierte Vergleiche, Reasoning-Modi, Benchmarks
- `references/deepseek-pricing.md` — DeepSeek V4 Flash & V4 Pro Preis-Details (Provider, Cache, Effektivkosten)
- `references/model-handoff-guide.md` — Leitfaden: Modell-Handoff generieren und pflegen
- `references/local-model-evaluation-methodology.md` — **NEU 2026-07-16:** Methodik für lokale Modelle auf 8 GB VRAM (Quant-Wahl, Benchmarking, MoE-Feasibility, iGPU-Split, Ornith-Fix)
- `references/zai-coding-plan-lane-routing.md` — **NEU 2026-07-16:** GLM-5 vs 5.2 Vergleich, z.ai Coding-Plan Tiers (Lite/Pro/Max), Skill-Lane Allokation unter Plan-Kosten-Druck, `hermes config set` CLI für gesperrte Config

## Lokale Modelle auf 8 GB VRAM

> Vollständige Methodik mit Code-Blöcken, Command-Sequenzen und echten Benchmarks: `references/local-model-evaluation-methodology.md`

**Sweet-Spot für 8 GB VRAM (RTX 5060, validiert Ornith-1.0-9B)**

| Quant | File | VRAM | Speed | Empfehlung |
|-------|------|------|-------|------------|
| Q5_K_M | 6.5 GB | ~6.3 GiB | 48-50 tok/s | ✅ Beste Wahl |
| Q8_0 | 8.9 GB | ~8.7 GiB (Split) | 14-15 tok/s | ❌ Nur nötig bei messbaren Quant-Artefakten |
| MoE 80B/3B | 48 GB Q4 | >9 GB aktiv | — | ❌ Weder Disk noch VRAM für 8-GB-System |

**Wichtige Fallstricke (alle validiert 2026-07-16):**

1. **Ollama RENDERER/PARSER:** Ornith-1.0-9B braucht `RENDERER qwen3.5` + `PARSER qwen3.5` im Modelfile, sonst buggen Reasoning + Tool-Calls (bekannt von Perplexity + reproduziert).

2. **Stop-Tokens:** `<end>` aus Stop-Tokens entfernen, sonst bricht Reasoning-Output ab.

3. **iGPU-False-Negative:** Auf PRIME-Dual-GPU zeigt `vulkaninfo` nur NVIDIA. Intel iGPU existiert (Mesa Vulkan via VK_ICD_FILENAMES), aber llama.cpp erkennt sie nicht als Tensor-Split.

4. **MoE-Feasibility prüfen:** Vor MoE-Empfehlung File-Größe (48 GB für 80B!) + VRAM (aktive Parameter×Quant + Attention) checken. Die meisten MoE passen nicht auf 8 GB VRAM + 55 GB Disk.

**Vollständiger Evaluations-Flow:** Discovery → VRAM-Rechnung → Download+SHA256 → Benchmark (3 Tests: FizzBuzz, Tool-Call, Max-Reasoning) → Side-by-Side-Vergleich → Doku.

## Preis-Check Workflow

Bei Preis-Check-Anfragen (z.B. "preis-check Deepseek"):
1. Aktuelles Modell checken: `hermes config | grep -i <modell>`
2. **NICHT web_extract auf OpenRouter-Seiten** — Preise sind oft als Bilder eingebettet und nicht extrahierbar. Stattdessen `web_search` mit Query wie "deepseek v4 flash pricing costs per million tokens" — die Suchergebnis-Beschreibungen enthalten bereits die Kern-Preise
3. **OpenRouter-API direkt abfragen** (zuverlässigster Weg, kein Bild-Scraping):
   ```python
   import urllib.request, json
   req = urllib.request.Request(
       "https://openrouter.ai/api/v1/models",
       headers={"Authorization": f"Bearer {API_KEY}"}
   )
   with urllib.request.urlopen(req, timeout=30) as resp:
       data = json.loads(resp.read())
   models = data.get("data", [])
   # Filtere auf bestimmten Provider / Modell-Namen
   target = [m for m in models if "moonshot" in m["id"].lower()]
   for m in target:
       p = m.get("pricing", {})
       print(f"{m['id']}: ${p.get('prompt')}/M in | ${p.get('completion')}/M out")
   ```
   **Wichtig:** Nicht als `terminal()`-Inline mit `curl | python3 -c` nutzen — Quoting-Breaks durch geschachtelte Anführungszeichen. Stattdessen `execute_code` mit `urllib.request` oder die Datei vorher per `write_file` ablegen.
4. Für tiefere Daten: `hermes insights --days 7` für reale Nutzungsdaten
5. Effektivpreise (cache-bereinigt) notieren — die Listenpreise sind oft irrelevant
6. Vergleichstabelle bauen: Provider × Kosten für Session/Tag/Monat
7. Nous Portal Free-Tier als Bonus hervorheben (falls zutreffend)