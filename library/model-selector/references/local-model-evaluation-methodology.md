# Local Model Evaluation on 8GB VRAM Systems

> **Eingeführt 2026-07-16** — Aus der Ornith-1.0-9B-Session auf Bastis MEDION ERAZER (RTX 5060 8GB, 15GB RAM).
> Enthält die Methodik und Fallstricke zum Evaluieren lokaler 7B–12B LLMs auf Consumer-Hardware.

## 1. VRAM-Budget-Rechnung (vor jedem Download)

Bevor du ein Modell ziehst, kalkuliere ob es **überhaupt** passt:

```
Nutzbarer VRAM = GPU-Gesamt - reserviert (OS/Display)
Beispiel RTX 5060: 8 GB total → ~7.5 GB nutzbar (0.5 GB für Wayland/Reserve)
```

### Quant-Größen-Tabelle (9B-Klasse)

| Quant | ~File-Größe | ~VRAM geladen | Passt auf 8 GB? | tok/s (Q5_Baseline) |
|-------|-------------|---------------|-----------------|---------------------|
| Q4_K_M | 5.5 GB | ~5.4 GiB | ✅ komplett | ~50–55 |
| **Q5_K_M** | **6.5 GB** | **~6.3 GiB** | **✅ + 1.2 GB Headroom** | **~48–50** |
| Q6_K | 7.5 GB | ~7.3 GiB | ⚠️ knapp (0.2 GB) | ~30–40 |
| Q8_0 | 8.9 GB | ~8.7 GiB | ❌ OOM ohne Layer-Split | ~14–15 (Split) |
| F16 | 18 GB | ~17.5 GiB | ❌ | — |

**Faustregel für 8 GB VRAM:** Q5_K_M ist der Sweet-Spot. Q4_K_M geht (etwas mehr Headroom für KV-Cache), Q8_0 nur mit Layer-Split (→ 3× langsamer).

### KV-Cache-Overhead

Den nicht vergessen:
```
KV-Cache = 2 × layers × n_heads × head_dim × seq_len × bytes_per_elem
9B-32L-32H-128d-8192ctx-Q8: 2 × 32 × 32 × 128 × 8192 × 1 = ~2 GB in Q8
→ Q5 quantisiert ~0.5-1 GB KV-Cache Overhead
→ 8192 ctx = ~192 MB bei Q4-KV, ~384 MB bei Q8-KV (in der Praxis niedriger durch GQA)
```

**Praktischer Test (Ornith-1.0-9B Q5_K_M, 8192 ctx):**
- GPU: 6291 MiB Model + 144 MiB KV-Cache
- CPU: 2784 MiB (Layers auf CPU) + 48 MiB KV-Cache
- Frei: ~1.4 GB VRAM Headroom

### Layer-Split für Q8_0 (wenn unbedingt nötig)

Wenn Q8_0 getestet werden muss und nicht komplett in VRAM passt:

```
Ollama setzt -ngl automatisch. Prüfe den Split via:
  nvidia-smi  # VRAM-Auslastung nach erstem Prompt
  ollama ps   # Zeigt GPU/CPU-Layer-Verteilung

Eigener llama.cpp-Build (CUDA+Vulkan):
  ./llama-cli -m model.gguf -ngl 22  # 22/33 Layers auf GPU, Rest CPU
  → typisch: 25/33 GPU-Layers bei Q8_0 (6.9 GB VRAM), 8 auf CPU
```

**Performance Q8_0 mit Split vs Q5_K_M:**

| Metrik | Q5_K_M (volle GPU) | Q8_0 (22/33 Split) | Faktor |
|--------|-------------------|-------------------|--------|
| Prompt Eval | 234 tok/s | 44 tok/s | 5× langsamer |
| Generation | 49 tok/s | 14-15 tok/s | 3.4× langsamer |
| CPU-Last | ~60% | 372% | 6× mehr |

**Fazit:** Q8_0 mit Layer-Split lohnt sich NUR wenn die Quant-Artefakte von Q5_K_M messbar schlechtere Ergebnisse liefern. Für die meisten Coding-Tasks ist der Speed-Verlust zu hoch.

## 2. GPU-Compute-Verifikation (Dual-GPU-Laptops)

Auf Bastis MEDION ERAZER (Intel i7-13620H iGPU + RTX 5060 dGPU) gab es einen False-Negative-Bug:

```
# ❌ FALSCH: "Intel iGPU hat kein Vulkan"
vulkaninfo | grep deviceName  # → zeigt nur NVIDIA

# ✅ RICHTIG: ICD forcieren
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_icd.json vulkaninfo | grep deviceName
# → Intel(R) Graphics (RPL-P), apiVersion 1.4.318, subgroupSize=32

# ✅ Sysfs-Kernel-Walk
ls /sys/class/drm/renderD*/device/driver
# → renderD128: i915 (Intel), renderD129: nvidia

# ✅ Vulkaninfo enumerate
vulkaninfo --summary 2>&1 | grep -E "deviceType|deviceName"
# → deviceType = INTEGRATED_GPU / DISCRETE_GPU
```

**Lektion (bestätigt 2026-07-16):** "Nicht gefunden" ≠ "nicht vorhanden" auf Dual-GPU. Default-Tools priorisieren den primären Display-Output. Auf Wayland/NVIDIA-PRIME wird die Intel-iGPU vom Vulkan-Loader ausgeblendet, existiert aber und hat Compute-Fähigkeiten.

**llama.cpp Dual-GPU-Test (CUDA+Vulkan):**

```bash
cmake -B build -DGGML_CUDA=ON -DGGML_VULKAN=ON -DCUDACXX=/usr/local/cuda/bin/nvcc
cmake --build build --config Release -j$(nproc)

# Split test
./build/bin/llama-cli -m model.gguf -t 4 -ngl 20 --tensor-split 7.5,0.0 -p "Hello" -n 10 2>&1
```

**Befund:** Intel iGPU wird von llama.cpp's Vulkan-Backend nicht als separater Split-Slot erkannt, wenn NVIDIA-PRIME aktiv ist. Tensor-Split auf NVIDIA+Intel ist auf diesem System nicht realisierbar.

## 3. Quellen-Verifikation für Modelle (Subagent-Output-Falle)

**Problem:** Bei Modell-Recherche liefern Subagenten oft Phantom-URLs (nicht-existierende Modelle auf HuggingFace).

**Konkreter Fall (2026-07-16):**
```
Subagent claim: huggingface.co/Qwen/Qwen3-Coder-7B → 404 ❌
Realität:      huggingface.co/Qwen/Qwen3-Coder-Next  → 1.089M pulls ✅
               huggingface.co/Qwen/Qwen3-Coder-Next-05B → 3.44M pulls ✅
```

**Verifikations-Workflow (Parent-Seite, nach JEDEM Subagenten):**

```python
# Template: Parent verifiziert Subagent-Modell-Claims
from hermes_tools import web_extract, web_search

# Schritt 1: Subagent-Claims extrahieren
claimed_url = "https://huggingface.co/Qwen/Qwen3-Coder-7B"

# Schritt 2: web_extract auf die URL
result = web_extract(urls=[claimed_url])
if "404" in result["results"][0].get("content", ""):
    # ❌ 404 — Modell existiert nicht unter diesem Namen
    # Schritt 3: HF suchen nach ähnlichen Modellen
    search = web_search(query="huggingface Qwen Coder GGUF site:huggingface.co")
    # → echte Modelle finden (z.B. Qwen/Qwen3-Coder-Next)
```

**Regel:** Bei jeder Modell-Empfehlung eines Subagenten:
1. `web_extract()` auf die Claim-URL
2. Bei 404 → HF-Suche mit `site:huggingface.co`
3. SHA256 des gefundenen Modells verifizieren (falls bereits heruntergeladen)
4. In Path-A-Prompt die pre-verified sources einbauen

## 4. Benchmark-Methodik (deterministisch + reproduzierbar)

### Minimaler Benchmark-Code

```python
import requests, time

def benchmark_model(model_name, prompt, max_tokens=600, temp=1.0):
    t0 = time.time()
    r = requests.post("http://127.0.0.1:11434/v1/chat/completions", json={
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temp,
        "max_tokens": max_tokens,
        "stream": False
    }, timeout=120)
    t1 = time.time()
    j = r.json()
    msg = j["choices"][0]["message"]
    ct = j["usage"]["completion_tokens"]
    return {
        "latency": t1-t0,
        "tokens_per_sec": ct/(t1-t0),
        "tokens": ct,
        "reasoning_len": len(msg.get("reasoning") or ""),
        "content": msg.get("content", ""),
        "finish_reason": j["choices"][0].get("finish_reason")
    }
```

### Test-Suite (3 Kerntests)

```python
# Test 1: Coding (deterministisch, 30 tok/s Baseline)
result = benchmark_model("model", "Write Python FizzBuzz 1..15. No comments.", temp=0.6)

# Test 2: Tool-Call Multi-Turn (reasoning + function calling)
messages = [
    {"role": "user", "content": "Run `date` and tell me the time."},
    {"role": "assistant", "reasoning": "...", "tool_calls": [...]},
    {"role": "tool", "content": "Thu Jul 16 18:15:00 CEST 2026"}
]
r = requests.post("http://127.0.0.1:11434/v1/chat/completions", json={
    "model": "model",
    "messages": messages, "tools": [...],
    "temperature": 1.0, "max_tokens": 400
})

# Test 3: Max Reasoning (erzwingt Reasoning-Pfad)
result = benchmark_model("model", "Explain the Sieve of Eratosthenes step by step.")
# Erwartet: reasoning_len > 500 chars
```

### Temperature-Effekt auf Speed (Ornith Q5_K_M)

| Temperature | FizzBuzz Speed | Output-Charakter |
|---|---|---|
| 0.0 (deterministisch) | 49 tok/s | Präzise, reproduzierbar |
| 0.6 (empfohlen) | 49 tok/s | Gute Balance |
| 1.0 (Qwen-default) | 30 tok/s | Kreativer, 40% langsamer |

**Takeaway:** Höhere Temperature = deutlich mehr Output-Tokens (Reasoning wird ausführlicher). Für Speed-Vergleiche immer temperature=0.0 oder 0.6 verwenden. Für echte Quality-Vergleiche beide Temperaturen testen.

### Multi-Model Vergleich (3-Wege-Pattern)

Wenn Basti mehrere Modelle parallel evaluieren will, diese Struktur verwenden:

```python
models = [
    ("ornith-9b-q5", "Ornith-9B Q5_K_M"),
    ("gemma4-e4b", "Gemma 4 E4B Q4_K_M"),
    ("qwen-dsv4-flash", "DeepSeek-V4-Flash Q4_K_M"),
]

tasks = [
    ("T1: FizzBuzz", "Print FizzBuzz 1..15. No comments."),
    ("T2: Bug-Diagnose", "Find the bug in: def avg(nums): return sum(nums)/len(nums)"),
    ("T3: German-Explain", "Erkläre Decorators auf Deutsch in 2 Sätzen."),
    ("T4: Palindrome", "Write is_palindrome(s: str) -> bool. 8 lines max."),
]

# Zwei Durchläufe:
# 1. temperature=0.6, max_tokens=400 → Speed-Vergleich (kurz)
# 2. temperature=0.0, max_tokens=2048 → Quality-Vergleich (deterministisch, vollständig)
```

**Wichtige Erkenntnis aus dem 3-Wege-Test (2026-07-16):**

Mit `max_tokens=400` und `temperature=0.6` wurden bei ALLEN Modellen die Antworten oft leer (`A=0c`) weil das Reasoning den gesamten Token-Budget verbrauchte. Erst mit `max_tokens=2048` und `temperature=0.0` kamen vollständige Antworten.

**Regel:** Für Speed-Vergleiche: `temperature=0.6, max_tokens=400` (klarer Speed-Unterschied sichtbar). Für Quality-Vergleiche: `temperature=0.0, max_tokens=2048` (vollständige, deterministische Antworten).

### Wichtige Metriken (echte Daten von Ornith-1.0-9B Q5_K_M)

| Metrik | Wert | Quelle |
|--------|------|--------|
| Generation Speed | **48–50 tok/s** konsistent | Konstanter Prompt-Eval + Eval-Loop |
| Latenz 300-500 Token | 6–10 s | Typisch für 9B auf RTX 5060 |
| First-Token-Latenz | ~2-3 s (warm) | Nach VRAM-Load |
| Q5_K_M VRAM | 6.3 GiB | Passt komplett |
| Q8_0 VRAM | ~6.9 GiB (+ Split) | CPU wird zur Bremse |
| Reasoning aktiv? | ⚠️ Ja, aber Stop-Token `<end>` buggt | Fix: PARSER qwen3.5 |

### Ollama-Konfiguration für Ornith-1.0-9B (wichtig)

Das offizielle GGUF von `deepreinforce-ai/Ornith-1.0-9B-GGUF` hat einen **broken chat_template** für Ollama. Symptome: Reasoning hovert als `<end>` ohne Output, Tool-Calls fehlerhaft, Repetition-Loops bei längeren Sessions.

**Fix (Modelfile):**
```
FROM hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q5_K_M
RENDERER qwen3.5
PARSER qwen3.5
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER top_k 20
PARAMETER repeat_penalty 1.0
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
```

**Nicht vergessen:** Weniger Stop-Tokens (ohne `<end>`) verhindert Abbruch des Reasoning-Outputs.

## 5. MoE-Feasibility für 8GB VRAM

### Rechnung für Qwen3-Coder-Next (80B/3B MoE)

```
Parametertyp          | Größe | Berechnung
----------------------|-------|-----------
Total Parameter       | 80B   | (80×10⁹)
Aktive Parameter      | 3B    | MoE sparsity ~96%
Experts (total)       | ~256  | 80B / 314M pro Expert
Active per Token      | ~8    | Top-K Routing
Model Q4 File Disk    | 48 GB | Q4_K_M GGUF (80B, 48 GB)
VRAM aktiv (Q4)       | ~1.8 GB | 3B aktive × 0.6 bytes (Q4)
Attention (Q4)        | ~7.5 GB | 16 heads × 2 KV × 128d × 8192ctx × 16 layers
Total VRAM aktiv      | ~9.3 GB | zu groß für 7.5 GB nutzbar
Disk (weiteres MoE)   | 48 GB  | zu groß für 55 GB frei
```

**Ergebnis:** Qwen3-Coder-Next (80B/3B) passt weder in 7.5 GB VRAM noch auf 55 GB Disk. MoE auf 8 GB VRAM ist nicht praktikabel.

### Alternative: Echte 7B/9B Dense Modelle

| Modell | Größe | VRAM Q5 | Disk | Speed | Reasoning | Status |
|--------|-------|---------|------|-------|-----------|--------|
| Ornith-1.0-9B | 9B dense | 6.3 GiB | 6.5 GB | 24-49 tok/s (temp-abhängig) | ✅ aktiv (chat_template-Fix nötig) | ✅ Getestet |
| Qwen3.5-9B-DeepSeek-V4-Flash | 9B dense | ~5.5 GiB | 6.6 GB | 14-27 tok/s | ✅ SFT-Distill von V4-Reasoning | ✅ Getestet |
| Gemma 4 E4B-it | 8B MoE (4B active) | ~3.5 GiB | 6.0 GB | 1.9-26.8 tok/s (längenabhängig) | ✅ tief aber variabel | ✅ Getestet |
| Qwen3-Coder-Next | 80B/3B MoE | ~9.3 GB ❌ | 48 GB ❌ | — | — | ❌ Nicht testbar |

### Multi-Model Routing für 8 GB VRAM

Statt einem Modell für alles, je nach Task das passende verwenden (alle passen in 8 GB, aber nur 1 gleichzeitig live via `OLLAMA_MAX_LOADED_MODELS=1`):

| Use-Case | Bestes Modell | Warum | Größe |
|---|---|---|---|
| Coding-Agent (Primary) | **Ornith-1.0-9B Q5_K_M** | Stabilste Speed über alle Task-Längen, SWE-Bench 69.4 | 6.5 GB |
| Reasoning-Tasks | **Qwen3.5-9B-DeepSeek-V4-Flash Q4_K_M** | SFT-Distillation von V4 Reasoning-Struktur, Apache 2.0 | 6.6 GB |
| Tool-Call / Short Prompts | **Ornith (oder Gemma bei Tool-Fokus)** | Gemma nur wenn lange Outputs (>300 tok) erwartet | 6.0-6.5 GB |

**Setup:**
```bash
# Alle drei parallel installiert, aber nur 1 gleichzeitig aktiv
ollama run ornith-9b-q5        # 6.5 GB — default
ollama run gemma4-e4b          # 6.0 GB — tool-call secondary
ollama run qwen-dsv4-flash     # 6.6 GB — reasoning fallback

# Wichtig: 8 GB VRAM → nur 1 Modell zur Zeit laden
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=5m    # 5 Min nach letztem Request entladen
```

### Bekannte Phantom-URLs (2026-07-16)

| Subagent-Claim | Realität |
|---|---|
| `huggingface.co/Qwen/Qwen3-Coder-7B` | ❌ 404 — existiert nicht. Echt: `Qwen/Qwen3-Coder-Next` |
| `registry.ollama.ai/v2/library/ornith-9b` | ❌ 404 — kein offizielles Ollama-Repo. Echt: `deepreinforce-ai/Ornith-1.0-9B-GGUF` |
| `maxwell1500/ornith-35b` auf Ollama | ❌ Phantom. `.PHANTOM` marker gesetzt |

### MoE Variable-Speed Behavior (Gemma 4 E4B — getestet 2026-07-16)

**Wichtige Entdeckung:** MoE-Modelle haben eine **variable Token-Geschwindigkeit**, die von der Output-Länge abhängt:

| Output-Typ | Ornith (Dense) | Gemma 4 E4B (MoE) | Ursache |
|---|---|---|---|
| Kurz (57 Tokens, FizzBuzz) | 24.9 tok/s ✅ stabil | **1.9 tok/s** 🔴 | Router-Overhead dominiert kurze Runs |
| Mittel (250 Tokens, Palindrome) | 21.8 tok/s ✅ stabil | **6.4 tok/s** ⚠️ | Router noch signifikant |
| Lang (550 Tokens, Bug-Diagnose) | 24.6 tok/s ✅ stabil | **26.8 tok/s** ✅ | Compute dominiert, Router-Overhead amortisiert |

**Mechanismus:** Bei MoE-Modellen muss jeder Token **alle aktiven Experts** durch den Router schicken + die Top-K auswählen. Bei kurzen Outputs (<100 tok) ist dieser Routing-Overhead relativ zum Compute-Aufwand dominant. Bei langen Outputs (>500 tok) amortisiert sich der Router über mehr Tokens.

**Konsequenz für 8 GB VRAM:**
- MoE-Modelle (Gemma 4 E4B) sind **schlecht für Tool-Calls** (kurze Antworten, Router-Penalty)
- MoE-Modelle sind **akzeptabel für Reasoning-Tasks** (lange Outputs, Compute-Amortisation)
- Dense Modelle (Ornith, Qwen) sind **stabil über ALLE Task-Längen** — wichtigsten für Bastis Coding-Workflow

**MoE-Check-Box (vor Dispatch)**

Bevor du ein MoE-Modell empfiehlst, prüfe:

```
- [ ] File Size (Q4) < 30% der freien Disk
- [ ] Aktive Parameter × Quant-Faktor < (VRAM - 1 GB Reserve)
- [ ] Attention-Layers passen in VRAM (2 × layers × head_dim × n_kv_heads × seq_len × bytes)
- [ ] Anzahl Experts × Expert-Größe × (Anzahl online Experts) < VRAM
- [ ] Steam/RAM für CPU-Offload der inaktiven Experts vorhanden
- [ ] Output-Länge des Tasks > 300 Token? (sonst Router-Penalty)
- [ ] Temperature < 1.0? (höhere Temp = mehr Output-Varianz)
```

Bei 8 GB VRAM + 15 GB RAM + 55 GB Disk fallen 80B-MoE-Modelle durch alle Checks.

## 6. Perplexity Deep-Research Prompt (für Path-A Custom-Aware Research)

Nachdem Modell-Kandidaten identifiziert sind, soll der Prompt folgende Struktur haben (generiert vom `custom-aware-research-prompt` Skill):

```
# Prompt-Struktur

## Custom-Aware Pre-Block
- Hardware: GPU [Modell] [GB VRAM], RAM [GB], Disk [GB frei]
- Einschränkungen: Kein MoE >20B aktiv, Q4/Q5 Quant präferiert
- Use-Case: Coding Assistant (Tool-Use, Reasoning, Multi-Turn)

## Research-Goal
- Welche lokal hostbaren 7B-12B Modelle laufen auf o.g. Hardware?
- Benchmark-Vergleiche für Coding/Agent-Tasks
- Quant-Empfehlungen pro Modell
- Bekannte Fallstricke (Ollama chat_template, Stop-Token-Bugs)

## Pre-Verified Sources (aus Subagent + Parent-Check)
- Liste der bestätigt existierenden Modelle mit HF-URL
- Liste der Phantom-URLs (404) als Warnung
```

## 7. Complete Evaluation Flowchart

```
Phase 1: Discovery
  ├─ Subagent oder web_search → Model-Kandidaten sammeln
  ├─ Parent: JEDE URL per web_extract verifizieren
  └─ Phase 1 Output: Pre-verified Sources List

Phase 2: Feasibility
  ├─ VRAM-Rechnung (siehe §1)
  ├─ Disk-Rechnung (File-Größe + Manifest)
  ├─ MoE-Check (siehe §5 — variable-speed beachten!)
  ├─ Lizenz-Prüfung (Apache 2.0 > MIT > andere)
  └─ Entscheidung: Machbar? → Phase 3 | Nicht machbar → Warum dokumentieren + Alternative

Phase 3: Download + Verification
  ├─ SHA256 gegen HF-Manifest prüfen
  ├─ hf download für Bulk (>2 GB, besser sichtbar)
  ├─ ollama pull für Managed Registration
  └─ Modelfile erstellen (mit RENDERER/PARSER für exotische Modelle)

Phase 4: Speed Benchmark (temperature=0.6, max_tokens=400)
  ├─ Test 1: FizzBuzz → Speed-Messung bei Kurz-Output
  ├─ Test 2: Tool-Call Multi-Turn → Reasoning + Function Calling
  ├─ Test 3: Max Reasoning → Reasoning-Tiefe
  └─ Phase 4 Output: Metrik-Tabelle (tok/s, VRAM, Reasoning-Länge)

Phase 5: Quality Benchmark (temperature=0.0, max_tokens=2048)
  ├─ Gleiche Tests wie Phase 4, aber deterministisch
  ├─ Output auf Korrektheit prüfen (FizzBuzz 15, nicht 100!)
  ├─ Bei side-by-side: alle Modelle antreten lassen
  └─ Bewertung: welches Modell liefert besseren Output?

Phase 6: Comparison (bei Mehrfach-Test)
  ├─ Side-by-Side-Tabelle: Speed, Reasoning-Tiefe, Output-Qualität
  ├─ MoE-Router-Effekt checken (Speed bei Kurz vs Lang)
  └─ Empfehlung: Sweet-Spot + Task-Mapping (Routing)

Phase 7: Documentation
  ├─ Memory speichern (Modell + Ergebnisse + Fixes + Benchmarks)
  ├─ Skill-Update (wenn neues Pattern entdeckt)
  └─ Vault-Doku (bei relevantem Erkenntnisgewinn)
```

## 8. Perplexity Cross-Validation (Real vs Benchmarks)

Perplexity Deep Research liefert Benchmark-Charts die auf **optimierten Testbedingungen** basieren. Real-Tests auf Bastis Hardware weichen signifikant ab:

| Perplexity-Claim | Echte Messung (RTX 5060) | Abweichung |
|---|---|---|
| Qwen3.5-9B Q4_K_M: 55 tok/s | 14-27 tok/s (DeepSeek-V4-Flash) | 2-4× langsamer |
| Ornith-9B Q5_K_M: 48 tok/s | 18-49 tok/s (temp-abhängig) | ⚠️ Faktor hängt von Temp ab |
| Llama-3.1-8B Q5_K_M: 58 tok/s | Nicht getestet | — |

**Ursachen der Diskrepanz:**
- Perplexity verwendet vermutlich `num_ctx=4096` (wir testen mit `8192` → längere Pre-fill)
- Perplexity verwendet `temperature=0.0` für Speed-Messungen (wir testen oft mit `0.6`)
- Perplexity Benchmark-Cards sind auf **server-class GPUs** (A100, H100) — kein direkter Transfer auf Laptop-RTX
- CPU-Bottleneck durch große Modelle auf Consumer-Hardware

**Regel:** Perplexity-Charts sind ORIENTIERUNG, nicht Garantie. Immer selbst testen bevor Empfehlung.
