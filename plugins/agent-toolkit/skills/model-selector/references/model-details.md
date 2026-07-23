# Model Details — Vergleich & Benchmarks
Stand: Juni 2026

## Qwen3.7-Max vs Qwen3.6-Plus

| Eigenschaft          | qwen3.6-35b-a3b     | qwen3.7-max              |
|----------------------|---------------------|--------------------------|
| Released             | Apr 2026            | Mai 2026                 |
| Context Window       | 1M Token            | 1M Token                 |
| Max Output           | 66K Token           | 65.5K Token              |
| Preis Input          | kostenlos / $0.33/M | $1.25/M (50% Rabatt)     |
| Preis Output         | kostenlos / $1.95/M | $3.75/M (50% Rabatt)     |
| Throughput           | ~80 tok/s           | 54 tok/s                 |
| Tool-Error-Rate      | n/a                 | 2.31%                    |
| Prompt Caching       | nein                | ja (~47% Hit-Rate)       |
| OpenRouter Plus      | verfügbar           | nur Max verfügbar        |
| Thinking-Modus       | ja (Portal)         | enable_thinking + preserve_thinking |

## Qwen3.7-Max Benchmark-Highlights

### Coding Agent (vs Konkurrenz)
| Benchmark              | Claude Opus 4.6 | DS-V4-Pro | Qwen3.7-Max |
|------------------------|-----------------|-----------|-------------|
| Terminal Bench 2.0     | 65.4            | 67.9      | 69.7 (BEST) |
| SWE-Verified           | 80.8            | 80.6      | 80.4        |
| SWE-Pro                | 57.3            | 59.0      | 60.6 (BEST) |
| SWE-Multilingual       | 77.5            | 76.2      | 78.3 (BEST) |

### Reasoning
| Benchmark    | Claude Opus 4.6 | DS-V4-Pro | Qwen3.7-Max |
|--------------|-----------------|-----------|-------------|
| GPQA Diamond | 91.3            | 90.1      | 92.4 (BEST) |
| HLE          | 40.0            | 37.7      | 41.4 (BEST) |
| HMMT 2026    | 96.2            | 95.2      | 97.1 (BEST) |
| Apex         | 34.5            | 38.3      | 44.5 (BEST) |

### General Agent
| Benchmark      | Claude Opus 4.6 | Kimi K2.6 | Qwen3.7-Max |
|----------------|-----------------|-----------|-------------|
| MCP-Mark       | 56.7            | 55.9      | 60.8 (BEST) |
| MCP-Atlas      | 75.8            | 66.6      | 76.4 (BEST) |

### Kernel-Optimierung (autonome 35h-Session)
| Modell         | Speedup |
|----------------|---------|
| Qwen3.7-Max    | 10.0x   |
| GLM 5.1        | 7.3x    |
| Kimi K2.6      | 5.0x    |
| DeepSeek V4 Pro| 3.3x    |
| Qwen3.6-Plus   | 1.1x    |

## DeepSeek V4 Flash — Reasoning-Modi

| Modus      | Wann nutzen                        | Token-Verbrauch |
|------------|------------------------------------|-----------------|
| Non-Think  | Direkte Antworten, Code-Snippets   | niedrig         |
| Think High | Code-Review, Architektur-Planung   | mittel          |
| Think Max  | Komplexe Multi-Step Probleme       | hoch (384K max) |

Aktivierung: Hermes config `agent.reasoning_effort` setzen — `none/minimal`=Non-Think, `low/medium`=Think High, `high/xhigh`=Think Max. Befehl: `hermes config set agent.reasoning_effort xhigh`. Oder im Nous Portal "Thinking Mode" einschalten (Portal-Alternative).

## Kimi K2.6 (Open-Weight Multimodal)

| Eigenschaft       | Kimi K2.6              | Qwen3.7-Max           |
|-------------------|------------------------|-----------------------|
| Entwickler        | Moonshot AI            | Alibaba Cloud         |
| Release           | Apr 2026               | Mai 2026              |
| Architektur       | 1B MoE / 32B aktiv     | proprietär            |
| Context           | 262K Token             | 1M Token              |
| Preis Input       | $0.684/M               | $1.25/M               |
| Preis Output      | $3.42/M                | $3.75/M               |
| Cache Read        | $0.15–$0.37/M          | ~$0.25/M              |
| Open-Weight       | ✓ JA (HuggingFace)     | ✗ Nein                |
| Weekly Tokens     | 512B                   | 215B                  |
| Throughput        | bis 138 tok/s          | 54 tok/s              |

### Kimi K2.6 Benchmarks
| Benchmark        | Score | Beschreibung                          |
|------------------|-------|---------------------------------------|
| GPQA Diamond     | 91.1% | Graduate-Level Reasoning              |
| τ²-Bench Telecom | 95.9% | Conversational AI Agents              |
| HLE              | 35.9% | Humanity's Last Exam                  |
| Agentic Index    | 66.0  | besser als 94% aller Modelle          |
| Coding Index     | 47.1  | besser als 93% aller Modelle          |

### Kimi K2.6 Provider-Vergleich (günstigste Optionen)
| Provider     | Input $/M | Output $/M | Cache $/M | Besonderheit              |
|--------------|-----------|------------|-----------|---------------------------|
| Parasail     | $0.60     | $2.80      | —         | Günstigster Blended-Preis |
| DeepInfra    | $0.75     | $3.50      | $0.15     | Bestes Cache-Pricing      |
| Fireworks    | $0.95     | $4.00      | —         | Niedrigste Latenz (0.71s) |

**Wann Kimi K2.6 nutzen:**
- Input-heavy Workloads (günstiger als Qwen)
- Open-Weight erforderlich (Local Hosting, Custom Fine-Tuning)
- Multi-Agent Orchestration mit vielen parallelen Sub-Agenten
- UI/UX Generation aus Text + Bild

**Wann Qwen3.7-Max nutzen:**
- Lange Dokumente (1M Context vs 262K)
- Agent-Benchmarks kritisch (MCP-Mark, SWE-Pro)
- Prompt-Caching mit hoher Hit-Rate

## Claude Opus 4.8 (Premium-Frontier, Jun 2026)

- Release: Jun 2026
- Context: 200K Token
- Stärke: GPQA Diamond 93.5%, Code-Agent-Sweep, tiefe Architektur-Arbeit
- Preis: $15/M Input, $75/M Output (Premium)
- Gut für: System-Design, komplexe Multi-Step, LLM-Persona-Work, Bundle-Sessions
- Modell-ID: anthropic/claude-opus-4.8
- **NICHT einsetzen für:** einfache Daily-Tasks, GreyScript, Quick-Code
- **Wegen Bastis Preisbewusstsein:** Opus 4.8 nur bei echten Analyse-Aufgaben

## Claude Sonnet 4.6

- Stärke: Nuance, präzise Formatierung, natürliche Sprache
- Gut für: Dokumentation, Analyse langer Texte, Persona-Output (z.B. Yuno-Texte)
- Schwäche: teurer als Qwen für reine Code-Tasks
- Modell-ID: anthropic/claude-sonnet-4.6

## Empfohlenes Modell-Routing (Yuno Workflow)

| Aufgabe                          | Modell                      | Grund                        |
|----------------------------------|-----------------------------|------------------------------|
| Daily Chat, GreyScript, Config   | qwen/qwen3.6-35b-a3b        | kostenlos, schnell, gut genug|
| Discord-Bot, Docker, Architektur | qwen/qwen3.7-max            | Agent-Frontier, Tool-Support |
| Cron-Job Design, State-Mgmt      | qwen/qwen3.7-max            | Long-horizon Planung         |
| Code-Review mit Reasoning        | deepseek/deepseek-v4-flash  | Think-Modi, günstiger        |
| Input-Heavy Workloads            | moonshotai/kimi-k2.6        | $0.684/M, Open-Weight        |
| Multi-Agent Orchestration        | moonshotai/kimi-k2.6        | 100+ parallele Sub-Agenten   |
| Lange Analyse, Persona-Text      | anthropic/claude-sonnet-4.6 | Nuance + Formatierung        |
| Premium-Architektur, System-Design | anthropic/claude-opus-4.8 | GPQA 93.5%, beste Qualität   |
| Kritische Architektur            | qwen/qwen3.7-max            | GPQA 92.4%, MCP-Mark Top     |
