# Local Benchmark Suite Architecture

> **Source:** Qwythos-9B-Q6 Deep-Benchmark auf Basti's RTX 5060 8GB (2026-07-17)
> **Projekt-Struktur:** `~/10-Projekte/10-active/greyhack-tools/benchmarks/qwythos-9b/`
> **Wiederverwendbar als Template** für andere lokale Model-Benchmarks.

## 7-Dimensionen-Architektur

| # | Dimension | Runner | Testet | Metrik |
|---|---|---|---|---|
| 1 | **Speed** | `speed.py` | Throughput bei 5 Output-Größen (128→8k Tokens) | t/s, VRAM Peak |
| 2 | **Context-Scaling** | `context_scaling.py` | Prompt-Verarbeitung bei 4 Context-Stufen (1k→64k) | prompt t/s |
| 3 | **Needle-in-Haystack** | `needle_haystack.py` | Retrieval-Genauigkeit bei 131k/262k Context | Hit/Miss |
| 4 | **Quality** | `quality.py` | 3 Sub-Scores: MMLU, GSM8K, HumanEval | Score % |
| 5 | **Thinking A/B** | `thinking_ab.py` | Modellqualität mit/ohne `think=True` | Score % Δ |
| 6 | **Vision-Smoke** | `vision_smoke.py` | Bilderkennung (5 Bilder, einfache Fragen) | Hit/Miss |
| 7 | **Tools/Function-Calling** | `tools_smoke.py` | Tool-Erkennung + Args-Match | % detected, % match |

### Kombiniert durch

| Komponente | Job | 
|---|---|
| **Master-Runner** (`run_all.py`) | Orchestriert alle 7 Runner sequenziell, Pre-Flight-Check, `--brief`-Flag |
| **Aggregator** (`aggregate.py`) | Liest alle Roh-JSONs aus `results/raw/`, berechnet Scores, schreibt REPORT.md |
| **Chart-Renderer** (`chart_renderer.py`) | 5 matplotlib-Charts (Speed, Context, Needle, Quality, Thinking) |
| **Dashboard-Template** (`dashboard_template.html`) | Bootstrap-Report mit eingebetteten Charts + Zusammenfassung |
| **SystemSampler** (`system_metrics.py`) | Periodische GPU/RAM-Samples während Calls (Hintergrund-Thread) |

## num_predict Parameter Guidelines (für Thinking-Modelle)

Dies ist die **wichtigste Lektion** aus dem ersten Run. Thinking-Modelle (qwythos, qwen35-family) produzieren einen Thinking-Block VOR der finalen Antwort. `num_predict` muss BUFFER dafür haben:

### Faustregel: num_predict = (erwartete Antwort in Tokens) × 10 + 500

| Dimension | Erwartete Antwort | num_predict (v1) | Ergebnis v1 | num_predict (fix) | Ergebnis v2 |
|---|---|---|---|---|---|
| MMLU (Multiple Choice) | 1 Buchstabe (~3 tok) | **4** | ❌ Leere Antworten (alle 15) | **80** | Erwartet: ~80% |
| HumanEval (Code) | 20-60 Zeilen (~200 tok) | **200** | ❌ Nur Thinking, kein Code | **500** | Erwartet: ~60% |
| GSM8K (Mathe) | 5-10 Zeilen + Zahl (~150 tok) | **400** | ✅ 8/12 korrekt | 400 | 🟰 gleich |
| Thinking A/B ON | 300-1500 tok Thinking | **800** | ❌ Abgeschnitten (ON=70% < OFF=90%) | **1500** | Erwartet: ON > OFF |
| Vision (einfach) | 1 Wort (~5 tok) | **100** | ❌ Nur Thinking + CUDA OOM | **200** (mit CPU) | Erwartet: ~80% |
| Tools/FC | JSON-Body (~200 tok) | **500** | ✅ 5/5 | 500 | 🟰 gleich |

### Erkennungs-Regel: leere Antwort ≠ Modell-Fehler

Wenn der Runner leere oder stark verkürzte Antworten zurückmeldet:
1. **Prüfe Finish-Reason** im Ollama-Response (im Roh-JSON)
   - `"done_reason": "stop"` = Modell hat geantwortet (Zeichen ist hoch)
   - `"done_reason": "length"` = num_predict zu knapp
2. **Prüfe `thinking`-Feld** — wenn da Inhalt ist, hat das Modell gedacht, aber nicht geantwortet
3. **Erhöhe num_predict um Faktor 3** und wiederhole den Test

## Hardware-Constraints (RTX 5060 8GB)

Diese Parameter sind auf der Ziel-Hardware empirisch validiert:

| Konstellation | VRAM | Läuft? | Workaround |
|---|---|---|---|
| Text-LLM 9B Q6, 64k Context | ~7.5 GB | ✅ Native | — |
| Text-LLM 9B Q6, 256k Context | ~7.3 GB | ✅ Native | — |
| Text-LLM 9B Q8, any Context | >8 GB | ❌ Layer-Split | Q6 reicht qualitativ |
| Vision + Text-LLM 9B Q6 | >8 GB (CLIP+LM) | ❌ OOM | `num_gpu=20` CPU-Offload (3-5× langsamer) |
| Speed-Test bis 8k Output | ~7.6 GB | ✅ Native | — |
| Needle 256k @ 75% Position | ~7.3 GB | ⚠️ Instabil | Attention-Decay / Prompt-Format |

### Pre-Flight Checklist (vor jedem Benchmark-Run)

```bash
# 1. nvidia_oc deaktivieren (sonst 8% VRAM-Schwankung)
systemctl stop nvidia_oc

# 2. Nur ZIEL-MODELL laden, keine anderen
ollama list | grep -v "NAME\|qwythos-9b-q6"

# 3. Power-Limit checken (Stock 80W)
nvidia-smi -q -d POWER | grep "Power Limit"

# 4. VRAM-Frei prüfen (soll <200 MB used sein nach Modell-Load)
nvidia-smi --query-gpu=memory.used --format=csv,noheader

# 5. Modell-keep_alive setzen (Modell kühlt nicht zwischen Phasen aus)
# → Im OllamaClient-Constructor als Default: keep_alive="30m"

# 6. Plattenplatz checken (Logs + Charts + Dashboard)
df -h / | tail -1

# 7. GPU-Temperatur checken (soll <55°C sein vor Start)
nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader
```

## Pitfalls aus diesem Run

### SystemSampler Race-Condition (VRAM=0 in Rohdaten)

Der SystemSampler läuft als Hintergrund-Thread, der alle 500ms GPU-Metriken sampled. Bei sehr langen Ollama-Calls (>60s) stoppt der Thread, bevor ausreichend Samples geschrieben sind. Folge: `vram_peak=0` in den Rohdaten (sieht aus wie fehlgeschlagen, war aber erfolgreich).

**Betroffen:** Needle-Haystack-Runner (131k Context, ~60s) → VRAM=0 in Rohdaten.
**Fix ausstehend:** Thread-safe `join()` mit Timeout in `system_metrics.py`.

### Path.parents-Zählung in Sub-Runnern

Runner in `src/qwythos_bench/runners/` brauchen:
```python
# Runner in runners/: parents[3] für Project-Root (src/qwythos_bench/runners/file.py)
# → parents[0]=runners, [1]=qwythos_bench, [2]=src, [3]=project-root
PROMPTS_FILE = Path(__file__).resolve().parents[3] / "prompts" / "vision_cases.json"
```

Häufiger Fehler: `parents[2]` statt `parents[3]`, weil man vom Package-Root zählt statt vom File-Location. Die Regel: **zähle vom File aus alle Elternverzeichnisse bis zum Project-Root**.

### JSON-Export via String-Konkatenation (statt json.dumps)

Prompt-Dateien (MMLU, GSM8K, HumanEval) via F-String/Concatenation zu schreiben verursacht **unsichtbare JSON-Fehler** (trailing commas, falsche Escapes). Nutze immer `json.dumps()` mit `indent=2` für menschenlesbare JSON-Ausgaben.

## Template: Benchmark-Ordnung

```
benchmarks/<model-name>/
├── src/
│   └── <model_name>_bench/
│       ├── __init__.py
│       ├── ollama_client.py      # Client mit keep_alife-Default
│       ├── system_metrics.py     # GPU-Sampler-Thread
│       ├── runners/
│       │   ├── speed.py
│       │   ├── context_scaling.py
│       │   ├── needle_haystack.py
│       │   ├── quality.py
│       │   ├── thinking_ab.py
│       │   ├── vision_smoke.py
│       │   └── tools_smoke.py
│       ├── chart_renderer.py
│       ├── aggregate.py
│       └── dashboard_template.html
├── prompts/                      # JSON-Files pro Runner
├── test_images/                  # Vision-Test-Bilder
├── results/
│   ├── raw/                      # JSON pro Run pro Runner
│   ├── charts/                   # 5 PNGs
│   ├── logs/                     # Terminal-Logs
│   ├── REPORT.md
│   └── dashboard.html
├── run_all.py                    # Master-Runner
├── requirements.txt              # (optional, deps in pyproject)
├── pyproject.toml
├── .gitignore
└── README.md
```

## Verwandte Skills

- `deep-model-evaluation` — die Research-Phase + GGUF-Verifikation vor dem Build
- `systematic-debugging` — falls Runner-Fehler unerwartet sind (wie hier CUDA OOM/num_predict)
- `plan-review-and-orchestrate` — falls die Suite als Multi-Step-Projekt gebaut wird
