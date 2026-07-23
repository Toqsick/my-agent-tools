---
title: "05 — Ollama/Lokales LLM-Setup"
tags: [workflow-template, ollama, llm, ai, gpu, nvidia]
aliases: ["Ollama-Template", "LLM-Setup"]
parent_skill: workflow-template
---

# Template 05: Ollama / Lokales LLM-Setup

> **Bewertung**: ⭐⭐⭐⭐ — Mit v2-Features: GPU-Exklusivität, Idle-Service-Lifecycle, Quant-Tabelle, num_gpu-Formel, Config-Persistenz.

## Profile

| Profil | Trigger |
|--------|---------|
| `greenfield` | Erst-Setup auf neuem System |
| `optimize` | Bestehendes Setup auf Performance trimmen |
| `idle-mgmt` | Idle-Problem lösen (Modell resident, GPU-Konflikt) — **Basti-spezifisch** |
| `routing` | Multi-Modell-Routing aufsetzen |

## 🟥🟧🟨🟩 Priorisierung

- 🟥 **Kritisch**: OOM-Fehler, Abstürze, System-Unbenutzbarkeit
- 🟧 **Hoch**: Token/Sekunde spürbar verbessern
- 🟨 **Mittel**: Ladezeiten, Speicher-Effizienz
- 🟩 **Optional**: Feinschliff, Multi-Modell-Routing

## Phase Abarbeitung

```
1. 🟥 BASELINE: Token/Sekunde messen, VRAM-Auslastung, Ladezeit pro Modell
2. 🟧 QUANTISIERUNG: Passende Quant-Stufe (siehe Tabelle)
3. 🟧 KONTEXT-FENSTER: num_ctx passend zur Aufgabe
4. 🟧 GPU-OFFLOADING: num_gpu-Layers korrekt (Formel unten)
5. 🟥 NVIDIA-EXKLUSIVITÄT (Basti-spezifisch)
6. 🟨 NEBENLÄUFIGKEIT: Parallel-Requests vs Gaming-GPU-Bedarf
7. 🟧 MONITORING: nvtop + nvidia-smi --loop=1 + ollama ps
8. 🟥 DOKUMENTATION: Modelfiles in Git
```

## 🟥 Hardware-Inventur (ZWINGEND zuerst)

```bash
# GPU + VRAM
nvidia-smi -q -d MEMORY

# Aktuelle VRAM-Belegung
nvidia-smi --query-compute-apps=pid,used_memory --format=csv

# Andere VRAM-Konsumenten
systemctl list-units --type=service | grep -E "(ollama|jellyfin|docker|emulationstation)"

# Power-Management-Status
nvidia-smi -q -d POWER
```

## 🟧 Quant-Stufen-Tabelle

| Quant | VRAM/7B | Quality vs FP16 | Speed | Use-Case (Basti) |
|-------|---------|-----------------|-------|------------------|
| Q2_K  | 3.0 GB  | ~70%            | fastest | Throwaway, Notfall |
| Q4_K_M| 4.1 GB  | ~85%            | fast    | **Coding default** |
| Q5_K_M| 4.7 GB  | ~90%            | ok      | Sweet-Spot für 7B |
| Q6_K  | 5.5 GB  | ~94%            | ok      | Quality-Fokus |
| Q8_0  | 7.0 GB  | ~96%            | slow    | Höchste Qualität |
| FP16  | 14.0 GB | 100%            | slowest | Unnötig lokal |

**Basti-Default**: Q5_K_M für 7B, Q4_K_M für 13B+, extern (API) für 70B+.

## num_gpu-Layers-Formel

```
verfügbar_VRAM_MB = total_VRAM_MB − 2 GB (System-Headroom)
layer_size_MB    = ~120 (Mistral-7B) | ~200 (Llama-13B) | ~390 (Mixtral)
num_gpu_layers   = floor(verfügbar_VRAM_MB / layer_size_MB)

Basti-Setup (RTX 5060 8GB, 7B):
  verfügbar = 8192 − 2048 = 6144 MB
  num_gpu   = 6144 / 120 = 51
```

## 🟥 NVIDIA-Exklusivität (Basti-Setup-spezifisch)

```yaml
setup:
  gpu: "RTX 5060 Laptop 8GB"
  shared_with: ["Gaming", "Display"]

probleme:
  - "LLM-Inferenz allokiert VRAM exklusiv"
  - "Gaming während Inferenz → Driver-Reset / Crash"
  - "nvidia-powerd drosselt GPU-Limit für thermisches Headroom"
  - "ollama.service läuft standardmäßig enabled+active — ~12GB Modell resident"

workarounds:
  - ollama.keep_alive via API-Header (default 5min, für Gaming auf 0)
  - OLLAMA_NUM_GPU explizit setzen
  - nvidia-smi -pl Power-Limit vor Gaming fixen
  - systemd timer: ollama 02:00–06:00 disable wenn nachts Gaming

recommendation:
  default: "keep_alive=5min via API"
  gaming_mode: "ollama stop + num_gpu=0"
  coding_mode: "Q5_K_M, num_gpu=51, num_ctx=8192"
```

## 🟧 Multi-Modell-Routing

| Task-Typ | Empfehlung | Warum? |
|----------|------------|--------|
| Coding (schnell) | Qwen2.5-Coder 7B Q5_K_M (lokal) | Latenz < 200ms |
| Coding (komplex) | Claude/Gemini via API | Quality > 90% |
| Reasoning | Llama-3.3 70B via API | 7B versagt |
| Plan-Modus | Qwen2.5-1.5B oder kein LLM | Deterministisch |
| Voice-Pipeline | Distil-Whisper + Edge-TTS | Spezialisiert |

## 🟨 Monitoring-Tool-Auswahl

- `nvtop` — Live GPU+VRAM+Temp
- `nvidia-smi --loop=1` — Scriptbar
- `ollama ps` — Modell-Status
- `systemctl status ollama` — Service-Health
- `journalctl -u ollama -f` — Live-Logs

## 🟧 Service-Lebenszyklus (Idle-Problematik)

```yaml
default_verhalten:
  service: "ollama.service"
  start: "enabled + active nach boot"
  keep_alive: "5min (default)"

problem:
  - "~12GB Modell resident nach letztem Request"
  - "GPU-Memory blockiert für Gaming"
  - "~24GB Model-Weights auf Disk dauerhaft"

optionen:
  A_stop_on_idle:
    cmd: "sudo systemctl stop ollama"
    pro: "Sofort GPU + RAM frei"
    con: "Re-Latency ~3s"
  B_sleep_on_idle:
    cmd: "API-Call mit keep_alive=0"
    pro: "Modell wird aus GPU entladen"
    con: "Service läuft weiter, ~100MB Overhead"
  C_timer_based:
    cmd: "systemd timer: stop 02:00, start 07:00"
    pro: "Optimal für fixe Gaming-Zeiten"

recommendation: "B + C hybrid: keep_alive=0 default, timer für Gaming-Sessions"
```

## Harte Regeln

- 🟥 **Hardware-Inventur zuerst** — ohne Baseline keine Optimierung
- 🟥 **Service stoppen vor destruktiven Aktionen** (Modell-Delete, Config-Reset)
- 🟧 **Quant nicht unter Q4_K_M** für Coding
- 🟧 **num_ctx nicht über 32768** für 8GB GPU

## Pitfalls

- ⚠️ Modell-Download ohne `--name`-Tag: default-Tag `latest` — Updates unklar
- ⚠️ `num_ctx=32768` ohne Grund: VRAM-Explosion
- ⚠️ `num_gpu=99` + kleines Modell: scheitert bei Layer-Mismatch
- ⚠️ Modelfile ohne `FROM`-Zeile: crasht beim Build
- ⚠️ Ollama läuft als root nach `curl | sh`-Install: Sicherheitsproblem

## Beispiel-Modelfile

```dockerfile
# ~/dotfiles/ollama/Modelfiles/qwen-coder-7b-q5.modelfile
FROM qwen2.5-coder:7b-instruct-q5_K_M

PARAMETER num_ctx 8192
PARAMETER num_gpu 33
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

SYSTEM """
Du bist ein präziser Coding-Assistent. Antworte auf Deutsch.
Code-Kommentare IMMER auf Deutsch.
"""
```

## Mnemosyne-Hook

```python
mnemosyne_remember(
    content="Ollama-Setup Basti: Models=<list>, Quant=<default>, num_ctx=<default>, Service-Mode=<always/idle/timer>, GPU-Konflikt=<gelöst/offen>",
    importance=0.8, source="ai-infrastructure", extract_entities=True, veracity="tool"
)
```
