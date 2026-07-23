---
name: deep-model-evaluation
description: "Use when user asks to research, evaluate, or compare open-weight LLMs, verify a Hugging Face model, test GGUF or Ollama performance, assess VRAM fit, or produce a multi-source model verdict. NOT for deploying a model locally or comparing API prices. Covers reproducible coding, reasoning, tool-use, vision, quantization, and hardware-aware evaluation."
version: 1.3.0
author: yuno
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - model-evaluation
    - huggingface
    - research
    - bench-marking
    - comparative-analysis
    related_skills:
    - firecrawl-web
    - llama-cpp
    - tech-fact-check
    - local-ml-hosting
    - huggingface-hub
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['model', 'deep-model-evaluation', 'research', 'evaluate', 'compare']
keywords: ['model', 'user', 'asks', 'research', 'evaluate']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['llama-cpp', 'local-ml-hosting', 'ollama-local-hosting']
---


# Deep Model Evaluation

Evaluate and compare open-weight LLMs on HuggingFace / Reddit / independent blogs using a structured multi-source methodology. Produces a report in German (per user preference) with tables, honest limitations, practical VRAM advice, and concrete "what do I download" conclusion.

## When to load

- User asks to research/evaluate/compare specific open-weight models (e.g. "wie gut ist X", "Y vs Z comparison", "deep research on W").
- User links a HuggingFace model and wants a verdict on quality.
- User wants to know whether a finetune is worth the hype / better than its base.

**Not** for: deploying locally (use `local-ml-hosting`), comparing API model prices (use `model-selector`).

For **head-to-head API coding model evaluation** see Phase 9 below — comparing API-hosted models on real-world tasks (task design, harness, judge, cost metrics, integration recommendation). This is the gap between research (Phases 1-4) and local testing (Phases 5-8).

## Research methodology

### Phase 1 — Parallel source gathering

Always batch independent reads in ONE turn — model card, search results, and community discussions don't depend on each other.

**3-URL structured verification (preferred):** Every candidate model needs three independent source types before entering a final report. See `references/research-verification-protocol-2026.md` for the full protocol.

| URL | Source type | What it verifies |
|---|---|---|
| **URL1** | HF model card / official vendor page | Architecture, size, license, benchmark claims, release date |
| **URL2** | Independent benchmark, Reddit, YouTube, third-party guide | Real-world performance, community sentiment |
| **URL3** | Live download check (HF API JSON, Ollama library page, `ollama pull`) | File availability, download count, last update |

Coverage target: ≥60% of rows with a live-verified URL3. Flag failures explicitly — never fabricate.

| Source | What to look for |
|---|---|
| **Model card (BF16/safetensors repo)** | Architecture, training data, benchmark claims (watch for harness!), license, chat template |
| **GGUF repo** | Quant sizes, MTP availability, discussions (bugs, garbled outputs, KV-cache sensitivity) |
| **Independent benchmarks** | Open LLM Leaderboard, Artificial Analysis, note.com/Medium user tests, YouTube head-to-head |
| **Community discussions (HF + Reddit)** | Bug reports, "works for me" vs "broken" controversy, real-world observations |
| **Base model card** | Compare finetune claims vs base official tables — many gains vanish on matched harness |
| **Creator history** | Other models by same org, version lineage (v1→v2→v3), blog posts explaining updates |
| **YouTube head-to-head** | Practical tests (coding, long-ctx, agency) — especially HumanEval + multi-turn build tests |

### Phase 2 — Information dimensions to cover

| Dimension | Questions |
|---|---|
| **Lineage** | Base model? Version history (v1→v2→v3)? What was fixed/dropped per version? |
| **Architecture** | Dense/MoE? Attention type? Context window? Vision integrated or frozen? |
| **Benchmarks (with caveats)** | Official numbers (own harness? lm-eval? n=?) vs independent replays vs base model |
| **Community sentiment** | Downloads, likes, discussion tone, called-out issues, bug reports |
| **Third-party independent evals** | 1-run vs multi-run variance, flakiness rate, pass@k, difficulty breakdown |
| **Hardware advice** | VRAM fits, quant recommendations, KV-cache sensitivity, MTP impact |
| **Version diff** | What changed from previous version — real improvement or just hygiene? |
| **Honesty assessment** | Did creator publish regression numbers? "Not a cap jump" honesty? Marketing vs reality ratio |

### Phase 3 — Report structure

Follow this outline for the final report (canonical):

```
1. TL;DR (2-4 sentence bottom line)
2. Lineage & Architecture (table)
3. Benchmarks (one table, caveats in footnotes)
4. Third-party real-world testing (multi-run variance if available)
5. Community findings / known issues
6. Version comparison matrix (v1 vs v2 vs v3 vs base)
7. Hardware & quant guide (8 GB vs 12+ GB VRAM)
8. Honesty/Marketing check
9. Scoring (per dimension, 1-10)
10. Concrete download recommendation (Option A/B/C with ⭐ ratings)
```

### Phase 4 — Real-World GGUF Testing (Practical Verification)

After research, when the user says "test it" or "download it", execute a live-test phase. Catches model-card noise, real VRAM constraints, Ollama quirks, and code-quality gaps that research alone cannot detect.

#### Step 1 — Multi-Source GGUF Verification

Before trusting any model file, verify through **independent parallel paths**:

| Source | What it verifies |
|---|---|
| HF API | Repo exists, public, license, sha commit |
| HF Tree (LFS blob) | File size + SHA256 per quant (`lfs.oid` — canonical) |
| config.json | Architecture, layer count, hidden size, attention type |
| Ollama Registry | Whether `ollama run <name>` works (most repos NOT registered) |
| Disk / SHA256 | Downloaded file matches HF Tree LFS-oid |
| Ollama API `/api/tags` | Whether model actually loaded |

**Convention:** Cross-reference at least 3 sources before claiming a model is "real". See `references/example-ornith-9b-real-test.md` for a worked example.

### Pitfall (Self-Deception Blindness): Single-source verification is vulnerable to model-card hallucination. Always get `config.json` via `hf download <org>/<repo> --local-dir /tmp/v` — it's the only canonical source for layer count, attention type, and vocab size.

### 🪤 Qwen3.5-Family Reasoning-Loop on Ollama (Critical for 8B-9B Testing)

**Symptom:** Model produces 14K+ chars of reasoning content without ever reaching a final answer. `finish_reason='length'`, output empty. Observed on `qwen35-9b` Q4_K_M at max_tokens=4096.

**Root cause:** Ollama's GGUF chat-template export for Qwen3.5 base models has broken stop-token handling. The `RENDERER qwen3.5` + `PARSER qwen3.5` Modelfile patch (see `ollama-local-hosting` → Critical Warnings) fixes blank-output but does NOT eliminate the loop — only SFT/RL post-trained models (Qwythos, Ornith, DSV4-Flash) banish it structurally.

**Verification (RTX 5060 8 GB, T=0, FizzBuzz):**
| Modell | Reasoning | Output | Status |
|---|---|---|---|
| **Qwen3.5-Original** (mit Fix) | 14.869 chars | 0c | ❌ Loop |
| **Qwythos Q4_K_M** (Claude-SFT) | 1.238 chars | 57c | ✅ Stop |
| **Ornith Q5_K_M** (DeepReinforce RL) | 836 chars | 57c | ✅ Stop |
| **DSV4-Flash Q5_K_M** (distill SFT) | 1.193 chars | 54c | ✅ Stop |

**Rule:** Test every Qwen3.5-family model with FizzBuzz + max_tokens=4096 first. If reasoning >3000c without answer → base model without proper post-training, not suitable for agentic use. See `references/qwen35-family-loop-bug.md` for full 5-way benchmark. Also check the `qwythos-9b-evaluation` reference for an already-working setup.

#### Step 2 — Ollama Setup for Non-Registered Models

Most GGUF HuggingFace repos are **not** in the Ollama registry. Three approaches:

**A) Modelfile with `FROM hf.co/...`** (recommended):
```
FROM hf.co/<org>/<repo>:<quant>
PARAMETER temperature 0.6
PARAMETER top_p 0.95
PARAMETER num_ctx 12288
```
→ `ollama create <name> -f /tmp/<name>.modelfile`

**B) Manual GGUF download + local Modelfile** (offline):
```
hf download <org>/<repo> <file>.gguf --local-dir ~/models/<name>
# Modelfile: FROM ~/models/<name>/<file>.gguf
```

**C) `ollama pull hf.co/<org>/<repo>:<quant>`** (≥0.30, only for known quant tags)

**🪤 Silent Pull Hang:** Progress bar stalls >5 min despite 8+ ESTAB connections to Cloudflare (`54.230.x.x:443`). Verified on Ollama v0.30.11 with 9.5 GB GGUF behind Cloudflare CDN. Do NOT retry — same CDN connection hangs again.

**Fix:** Kill (`pkill -f "ollama pull"`), switch to method B (`hf download`), which achieves 5-11 MB/s on the same connection. If `hf download` also starts slowly, wait 30s (Cloudflare rate-limit cooldown) and retry.

#### Step 3 — Real Coding Task Taxonomy

Test at least **4-6 diverse tasks**:

| Category | Example | Tests |
|---|---|---|
| Simple coding | `is_prime(n)` type hints | Spec adherence |
| Algorithmic | Quicksort + partition + types | Algorithm design |
| Domain-specific | SQL recursive CTE with depth | Domain syntax |
| Pattern/Maths | RFC 5322 email regex, 3 tests | Pattern construction |
| Bug detection | `avg(lst) = sum(lst)/len(lst)` | Code review |
| Language generation | German explanation 3 Sätze | Multi-language |

**Procedure:** Run ALL tasks on new model AND trusted baseline (same quant). Same env, same max_tokens.

**Pitfall (False-Alarm Truncation):** Multi-line code with `max_tokens` too small (e.g. 400) silently truncates — looks like model bug but is test bug. Always use `max_tokens >= 2000` for coding, check `finish_reason` (`"stop"`=complete, `"length"`=truncated).

#### Step 4 — Tool-Use / Agentic Testing

**Test 1 — Single Tool Call:** Model calls calculator/read_file → `finish_reason="tool_calls"`. Verify `tool_calls[0].function` is well-formed.

**Test 2 — Multi-Turn Loop:** Tool result injected → model synthesizes answer. Verify answer references specific tool result content.

**Check reasoning field name:** Ollama v0.30 returns `reasoning` (not OpenAI's `reasoning_content`). Affects Hermes/OpenCode integration.

#### Step 5 — Side-by-Side Comparison

Same tasks, same env, same temperature (0.6 coding). Record: latency, tok/s, completion_tokens, reasoning length (chars), output quality, finish_reason.

**🪤 "Reply only: OK" Warmup Protocol:** Before running any benchmark on a newly loaded model, send a minimal probe:
```
Reply only: OK
```
A correct model responds `OK`. This verifies:
- Model is loaded and responsive (not in pull/create race)
- Tokenizer works correctly
- Reasoning-pipeline (visible as "Thinking...") doesn't break simple replies

**Always discard the first real benchmark run** — it includes cold-start model load time.
Run a 4-token warm-up first, then use the SECOND call for comparison.

Present as table:
| Test | Model A | Model B | Winner |
|---|---|---|---|
| Quicksort | 12.2s, 49 tok/s | 39.3s, 15 tok/s | 🏆 A |

#### Step 6 — Document Results

Save report to `~/.hermes/docus/audits/<model>-real-test-<date>.md`:
- Quellen-Verifikation
- Performance-Daten (VRAM, tok/s, latency)
- Code-Quality-Tests (tasks × result)
- Agentic/Tool-Use (field naming quirks)
- Vergleich vs Baseline (apples-to-apples)
- Setup-Reproduktion (exact commands)
- Empfehlung

See `references/example-ornith-9b-real-test.md` for a worked example.

#### Step 7 — Layer-Split & Quant-Comparison Testing (VRAM-Constrained GPUs)

When testing multiple quants (e.g. Q5_K_M vs Q8_0) on GPUs where the higher quant doesn't fit entirely in VRAM, add this step to quantify the speed/quality trade-off.

**Procedure:**

1. **Check raw GGUF size** against usable VRAM (`nvidia-smi --query-gpu=memory.total --format=csv,noheader` minus ~500 MB system headroom).
2. **For quants that exceed VRAM:** let Ollama auto-split. Capture layer allocation from journalctl:
   ```
   journalctl -u ollama --no-pager | grep "offload\|offloaded\|CUDA0 model buffer\|CPU_Mapped"
   ```
   Record: `GPU: X/Y layers, CPU: Z MiB`, graph split count.
3. **Run identical tasks** (same prompt, same temperature=0.6, same max_tokens) on BOTH quants.
   - Record latency, tok/s, completion_tokens, reasoning length, output quality.
   - **Pitfall (Cold-Start Skew):** The very first request to a newly loaded model includes disk→VRAM/CPU load time. Run a 4-token warm-up call (`"hi"`) first, discard its timing. Use the second call for comparison. Verified: Ornith-9B Q8_0 first-load = 21s (includes 25/33 layer load), warm = 37s → cold skew is ~-20s.
4. **Benchmark table template:**
   | Metrik | Q5_K_M (Full-GPU) | Q8_0 (Layer-Split) | Faktor |
   |---|---|---|---|
   | Generation Speed | **49 tok/s** | **14 tok/s** | ❌ 3.4× langsamer |
   | Prompt-Eval | 234 tok/s | 43 tok/s | ❌ 5.4× langsamer |
   | VRAM | 6.3 GB | 6.9 GB | ähnlich |
   | Code-Quality | ✅ korrekt | ✅ korrekt | 🟰 gleich |
5. **Conclusion rule:** If the higher quant costs >2× speed at identical quality on your benchmark tasks, record the finding as "full-GPU lower quant is the sweet spot". Flag this in the recommendation with specific tok/s data.

**🪤 Mamba / Linear-Attention layers penalize CPU offload hard:** Models with Mamba-2 or linear-attention heads (e.g. Ornith-9B: 24/32 linear layers) generate **130 graph splits** at batch_size=512 vs 14 at bs=1 when partially offloaded to CPU. Each split = GPU↔CPU sync. Result: 3.4× slower despite only 8/32 layers on CPU. Full-attention models degrade more gracefully under split.

**🪤 Q8_0 on <8 GB VRAM is quality-neutral, speed-negative:** On RTX 5060 8 GB, Q8_0 (8.87 GiB) with 25/33 GPU-layer split matched Q5_K_M identically on every coding task (FizzBuzz, quicksort, SQL, regex, bug detection), but at 14 tok/s vs 49 tok/s. Only worth it if the model has >32K context requirement that forces Q5_K_M KV-cache below needed depth (uncommon — tune `num_ctx` first).

#### Step 7b (optional) — Dual-GPU Compute Detection (PRIME/Optimus Laptops)

When testing on NVIDIA PRIME or Optimus laptops (discrete + integrated GPU), the iGPU may be **Vulkan-compute-capable but invisible** to the Vulkan-Loader by default. This unlocks a `--tensor-split` option: offload embedding + some layers to the iGPU without CPU bottleneck.

**Detection procedure:**

1. **Identify DRM devices** — check which GPU owns which `/dev/dri/renderD*`:
   ```bash
   for d in /sys/class/drm/renderD*; do
     echo "$(basename $d) → $(readlink $d/device/driver 2>/dev/null | xargs basename 2>/dev/null)"
   done
   ```
   Output: `renderD128 → i915` (Intel), `renderD129 → nvidia` (NVIDIA).

2. **Check Vulkan ICDs present:**
   ```bash
   ls /usr/share/vulkan/icd.d/
   ```
   Expected: `intel_icd.x86_64.json` (Mesa) + `nvidia_icd.json` (proprietary). If Intel is missing, `vulkaninfo` shows only NVIDIA.

3. **Force Intel ICD to check compute capability:**
   ```bash
   VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_icd.x86_64.json vulkaninfo --summary
   ```
   Key fields: `deviceType = INTEGRATED_GPU`, `subgroupSize >= 32` (needed for matrix ops), `maxComputeWorkGroupInvocations >= 1024`.

4. **Build llama.cpp with multi-backend support:**
   ```bash
   cmake -B build \
     -DGGML_CUDA=ON \
     -DGGML_VULKAN=ON \
     -DCMAKE_CUDA_COMPILER=$(which nvcc) \
     -DCUDACXX=$(which nvcc)
   cmake --build build --config Release -j$(nproc)
   ```
   Requires: `libvulkan-dev`, `glslc` (shaderc), `SPIRV-Headers`.

5. **Tensor-split test:**
   ```bash
   build/bin/llama-cli \
     -m ~/models/<name>/<quant>.gguf \
     --tensor-split 8,2 \
     -ngl 99 \
     -c 12288 \
     --main-gpu 0 \
     -p "Hello"
   ```
   `--tensor-split 8,2` = 80% weights on GPU0 (NVIDIA), 20% on GPU1 (Intel iGPU).

**🪤 Vulkan-Loader ICD Priority Bias:** The Vulkan-Loader picks the **first available ICD** by default. On PRIME/Wayland systems, NVIDIA loads first → Intel is invisible. `vulkaninfo` returning only NVIDIA devices is NOT evidence that Intel lacks Vulkan compute. Always force the Intel ICD explicitly with `VK_ICD_FILENAMES`.

**🪤 Wayland ≠ Compute-Block:** `xrandr --listproviders` showing "number 0" is Wayland-normal, not a sign of missing GPUs. Wayland hides outputs, not compute devices. The iGPU's DRM device and Vulkan compute-pipeline exist independently of the display compositor.

**🪤 Mamba layers amplify cross-GPU sync costs even more:** On iGPU + NVIDIA split, each Mamba linear-attention pass triggers GPU↔GPU sync across PCIe. Expected: 2-3× slower than full-NVIDIA even with only 20% on iGPU. Full-attention models fare better. Benchmark before committing to a split.

See `references/dual-gpu-compute-detection.md` for the full detailed workflow with diagnostic commands and expected output tables.

#### Step 8 — Multi-Source Verification Priority (Basti preference)

Basti's explicit correction (session 2026-07-16): **always verify through Ollama/llama.cpp source first, not just HF web scraping.** The correct verification order is:

1. **Ollama Registry** — is the model registered? (fastest check)
2. **HF API + config.json** — does the model exist? What architecture?
3. **HF Tree SHA256** (`lfs.oid`) — canonical file identity
4. **Download + local SHA256** — confirm byte-identical

Do NOT present HF page-scraping findings as primary evidence before the Ollama/llama.cpp path is exhausted. When the user says "check das Modell", start with `ollama pull` or `hf download` + `sha256sum`, not `web_extract` of the model card.

### Phase 9 — API Coding Model Evaluation Plan

This phase closes the gap between research (Phases 1-4) and local testing (Phases 5-8): **head-to-head comparison of API-hosted coding models on real-world tasks**. Used when evaluating how a new model performs on the user's actual daily workload.

#### When to use

- User asks to compare two or more API models on coding tasks ("test K3 vs M3 on real work")
- New model released → user wants a practical eval before integrating into the stack
- Tuning model selection for multi-agent orchestration routing

#### Phase structure

| Step | What | Output |
|---|---|---|
| 9.1 | **Setup** — isolate profile + eval repo | Hermes eval profile, harness scripts, task dirs |
| 9.2 | **Task design** — real workload taxonomy | 5-8 tasks matching daily work categories |
| 9.3 | **Eval run** — automated sequential execution | Raw logs, tokens, cost, duration per (task, model) |
| 9.4 | **Judging** — LLM-as-Judge + acceptance tests | Score per criterion (1-10), pass/fail per test |
| 9.5 | **Reporting** — comparison matrix + raw metrics | Structured markdown report |
| 9.6 | **Integration recommendation** — 3 path options | Niche ↔ Tier-1 ↔ Stay-local |

#### 9.1 — Setup

**Wahl der Eval-Plattform — zwei Varianten je nach Budget und Modell-Zugang:**

| Variante | Plattform | Wann |
|---|---|---|
| **Hermes Profile** | `hermes -p yuno-eval-<model>` | Modelle über Hermes-Provider (MiniMax, DeepSeek, OpenRouter) |
| **Kimi Code CLI** | `kimi --model <id> -p "..." -y` | Kimi-K3/Moonshot-Modelle, besonders bei Promo-Cup-Tokens |

Nutze **Kimi Code CLI** wenn der User Token-Cup-Guthaben hat (z.B. Kimi WM-Tippspiel), kein Cash-Budget, oder K3 spezifisch getestet werden soll. Siehe `references/kimi-code-cli-eval-platform.md` für vollständiges Setup (Provider-Catalog, OAuth-Login, Token-Burn-Strategie, Bash-Quoting-Pitfalls).

Nutze **Hermes Profile** für alle anderen Modelle — voller Tool-Stack, Automatisierung, Cost-Tracking.

Create an **isolated Hermes profile** so eval runs don't collide with production config:

```bash
hermes profile create yuno-eval-<model> --from yuno-coder
# Then patch default model to target API model:
# model.default: openrouter/moonshotai/kimi-k3
```

**Eval repo structure:**
```
eval-repo/
├── README.md
├── tasks/
│   ├── task-01-<domain>-<type>.md     # spec with acceptance criteria
│   └── ...
├── runs/                              # model output per task
│   ├── <model-A>/
│   └── <model-B>/
├── harness/
│   ├── run_task.py                    # executes task with model, logs everything
│   ├── judge.py                       # LLM-as-Judge (neutral model, not in eval set)
│   └── report.py                      # generates comparison matrix
└── results/
    └── eval-YYYY-MM-DD.md
```

#### 9.2 — Task Design

Build from **user's real daily workload** — NOT synthetic benchmarks. Weight by frequency:

| # | Category | Typical task | Weight |
|---|---|---|---|
| 1 | **Domain-specific refactor** | Split a file, modularize, rename imports | 25% |
| 2 | **Feature implementation** | New CLI subcommand, new endpoint | 25% |
| 3 | **Bash/system script fix** | Race condition repair, edge case handling | 15% |
| 4 | **Multi-file refactor** | Cross-file restructure, layer extraction | 20% |
| 5 | **Long-context synthesis** | Full-repo analysis, multi-doc summary | 15% |

Each task MUST include:
- **Spec file** with ✅ acceptance criteria (checkbox list)
- **Verify command** (e.g. `pytest tests/`, `bash verify.sh`, `python -c "..."`)
- **Pinned working state** (git commit or diff snapshot BEFORE task, so diff is measurable)

#### 9.3 — Eval Run Harness

```python
"""
harness/run_task.py — Executes task X with model Y, logs all metrics.
"""
import json, time, subprocess, sys
from pathlib import Path

def run_task(task_path: str, model: str, profile: str):
    task_text = Path(task_path).read_text()
    model_safe = model.replace("/", "_")
    task_name = task_path.split("/")[-1].replace(".md", "")
    worktree = Path(f"runs/{model_safe}/{task_name}")
    worktree.mkdir(parents=True, exist_ok=True)

    cmd = [
        "hermes", "-p", profile,
        "--task", task_text,
        "--max-turns", "20",
        "--model", model,
        "--no-interactive",
        "--output", str(worktree / "output.md"),
    ]

    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    duration = time.time() - start

    metrics = {
        "model": model,
        "task": task_path,
        "duration_sec": round(duration, 1),
        "exit_code": result.returncode,
        "stdout_chars": len(result.stdout),
    }
    # Extract token/cost from Hermes stderr logs
    for line in result.stderr.split("\n"):
        if "tokens" in line.lower() and "cost" in line.lower():
            metrics["cost_log"] = line.strip()

    (worktree / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics

if __name__ == "__main__":
    run_task(sys.argv[1], sys.argv[2], sys.argv[3])
```

**Run order:** Sequential per model (parallel risks rate limits + cost spikes). Each task runs through ALL models before moving to next task:

```bash
for task in tasks/task-*.md; do
  for model in "<model-A>" "<model-B>"; do
    python3 harness/run_task.py "$task" "$model" "yuno-eval-<profile>"
  done
done
```

#### 9.4 — Judging

**Two-layer evaluation:**

1. **Hard acceptance tests** — run actual verify commands. These are pass/fail and cost-free.
2. **LLM-as-Judge** — uses a **neutral model** (one NOT in the eval set, e.g. GLM 5.2 when comparing K3 vs M3).

**Judge prompt template:**

```
You are a neutral Senior Engineer. Rate the following code output against the spec.

TASK SPEC:
{task_spec}

MODEL OUTPUT:
{model_output}

SCORE each 1-10:
1. Correctness — does the code do what the spec requires?
2. Completeness — are all acceptance criteria met?
3. Style — readable code, appropriate comments?
4. Robustness — edge cases, error handling?
5. Testability — is the code structured for testing?

OUTPUT as JSON:
{"correctness": N, "completeness": N, "style": N,
 "robustness": N, "testability": N, "overall": N, "reasoning": "..."}
```

#### 9.5 — Reporting Matrix

| Task | Model A | Model B | Cost (A/B) | Winner |
|---|---|---|---|---|
| Domain refactor | 8.2 | 7.8 | $0.34 / $0.12 | 🥇 A |
| Feature impl | 7.9 | 8.1 | $0.41 / $0.09 | 🥇 B |
| Bash fix | 8.5 | 7.6 | $0.28 / $0.02 | 🥇 A |
| Multi-file refactor | 8.7 | 7.4 | $0.67 / $0.15 | 🥇 A |
| Long-ctx synthesis | 8.9 | 6.2 | $1.24 / $0.08 | 🥇 A |
| **GESAMT** | **8.44** | **7.42** | **$2.94** | 🥇 |

Also include raw metrics: duration (s), output tokens, reasoning tokens, input tokens per task.

#### 9.6 — Integration Path Recommendation

| Path | What | When |
|---|---|---|
| **Niche Specialist** | Model only for long-refactor + doc-synthesis; rest stays on current stack | If strong on long-ctx but expensive for daily use |
| **Tier-1 Coder** | Model as primary coding model, config fallback chain | If consistently >8.0 overall AND cost/task < user budget |
| **Stay-Local-First** | Only for 1M-context tasks; daily work on Ollama/local | If 5-10× more expensive than local with marginal quality gain |

#### 9.7 — Pitfalls specific to API eval plans

- **Cold-start cost spike:** First task includes model-warmup + reasoning preamble. Run a warm-up call ("Reply only: OK") and discard its timing.
- **Reasoning token explosion:** Always-on reasoning models can spend 60-80% of output tokens on chain-of-thought. Cost per task is often much higher than token prices suggest — report it.
- **Harness mismatch:** A model evaluated in harness A (e.g. Kimi Code) is NOT comparable to the same model in harness B (Hermes). Run ALL models in the SAME harness.
- **Cache warm-up:** First run pays full price; repeat runs on similar inputs may get cache discounts. Report both "first run cost" and "steady-state cost".
- **Reasoning effort pinning:** Models with configurable reasoning levels (low/medium/high) should be pinned to the SAME level for all models in comparison.
- **Context window ≠ usable context:** Models with 1M-ctx may degrade at lower effective lengths due to attention decay. Test at 300K+ tokens to verify.
- **Vendor-reported benchmarks are directional only.** Always cross-reference with independent sources (Artificial Analysis, community reproductions) before treating vendor numbers as ground truth.
- **Hidden system prompts inflate input cost:** Some models (K3, K2.6) count 85+ tokens for "hi" due to baked-in system prompts. Account for this in cost-per-task.

- **Shell quoting breaks complex eval harnesses in terminal():** Piping `curl | python3 -c "..."` from bash with nested quotes, f-strings, and JSON structures reliably fails on quoting. The working patterns are: (1) write the probe to a script file (`python3 harness/discover_models.py`), (2) use `execute_code` with `urllib.request`, (3) use `write_file` + `terminal` as separate calls. Never inline multi-line JSON-processing pipelines in a single `terminal()` call. The `scripts/eval-runner.sh` support file uses script files, not inline quoting — load it for the proven pattern.

- **Budget-constrained eval design (staircase pattern):** When the user has a hard monthly cap, structure the eval as a staircase: (1) freeze baseline first (free/minimal cost), (2) define a "kill switch" — if premium model underperforms baseline on the first 1-2 tasks, cancel remaining runs, (3) cap premium-model run budget at $N total. Report both first-run cost (no cache) and steady-state cost (after OpenRouter/direct cache warms up). First-run cost can be 2-5× higher than steady-state — a model that looks unaffordable on first call may be fine for daily use once cached.
- **Kimi Code CLI als alternative Eval-Plattform bei Budget-Knappheit:** Wenn der User sagt "kein Budget diesen Monat" → sofort pivoten zu Kimi Code CLI mit OAuth-Login (`kimi login`), der Cup-Tokens/Promo-Credits verbraucht statt Cash. Pattern: (a) Kimi CLI installieren + `kimi login`, (b) `kimi provider catalog add moonshotai` für K3-Zugriff, (c) `kimi --model moonshotai/kimi-k3 -p "$(cat task.md)" -y` für non-interactive Eval, (d) Token-Burn-Strategie mit Phasen + Hard-Deadline via Cron-Reminder. Siehe `references/kimi-code-cli-eval-platform.md`.

---

## Output format preferences (Basti)

- **Language:** German (all sections, code comments, report text).
- **Structure:** Tables for quantitative data, bullet points for findings, bold for bottom-line verdicts.
- **Honesty over marketing:** Explicitly flag if creator published regressions. Never claim "beats base" without confirming matched harness.
- **Practical conclusion:** Must answer "so what do I actually download?" as the last section, with specific GGUF filenames, VRAM requirement, and llama.cpp flags.
- **Version lineage:** Clarify naming confusion (e.g. "v3" GGUF export vs "v3" training iteration — they're different things).
- **Avoid:** Polishing away flaws, claiming superiority without evidence, ignoring community bug reports.

## Pitfalls

### Single-run variance is huge
Never treat 1-run benchmark results as conclusive for a model comparison. When independent 5-run coding tests exist, use them as primary. Know that 1-run champions are often 5-run also-rans — baked into the research methodology, not a footnote.

### Harness noise masks real differences
Empero's internal bench (+34 MMLU on v1) vs official Qwen numbers uses a *different harness, different CoT template, and different routing* — not comparable. Flag when creator numbers disagree with official base-model releases.

### "v3" can mean anything
GGUF "v3" often means a re-export with template fixes, not a new training run. Always verify whether a version bump reflects:
- New training (capability change) → epoch bump (v1→v2)
- Export/fix revision → may have "v3" in filename but same weights
- Chat template hotfix → night-and-day behavior variance without param change

### Model names drift between creators and community
- "Qwen3.6 9B" often mentioned in comparisons DOES NOT EXIST as an official open weight. The actual comparison is Qwen3.5-9B vs a Qwythos finetune.
- Cross-check model cards before reporting comparisons — never assume a community filenaming convention matches HuggingFace reality.

### Quantized feedback is not model feedback
- KV-cache quantization breaks Qwen3.5 hybrid attention → garbled outputs (discussion #3 in Qwythos GGUF repo).
- A bug report about Q8_0 garbled output is about llama.cpp config, not the model.
- Separate "model behavior" from "deployment config failure" in your analysis.

### Second-order effects of training interventions
FTPO or DPO passes often fix one problem (looping) and introduce subtle others (flaky outputs, reduced code accuracy, HumanEval regression). A fix-is-fix narrative in the model card omits these trade-offs — dig for them in community posts and multi-run evals.

### Content-length bias in YouTube tests
Many model comparison videos test only 1–3 coding tasks. A 3-task sample is statistically meaningless for ranking 9B models. Note sample sizes explicitly when citing video evidence.

## Quick-start template

```markdown
## Research plan

1. Load model card(s) + GGUF repo(s) + discussions in parallel → web_extract
2. Search for independent benchmarks + community discussion → web_search
3. Search YouTube for head-to-head → web_search
4. (Optional) Check creator org for version history + blog → web_extract

## Report dimensions (check each when writing)

- [ ] Lineage — base model, version history, what changed
- [ ] Architecture — params, attn type, MTP, vision, context
- [ ] Official benchmarks vs base model vs independent
- [ ] Third-party multi-run evals if available
- [ ] Community findings — known bugs, garbled issues, KV-cache sensitivity
- [ ] Hardware/quant table with size + VRAM recommendation for 8GB / 12GB / 16GB
- [ ] Honesty check — regressions published? Community trust level?
- [ ] Concrete download: exact GGUF filename + context/flags per target GPU
```

## Related skills

- `firecrawl-web` — for web_extract of model cards and discussions
- `llama-cpp` — GGUF quant info, inference flags, MTP setup
- `tech-fact-check` — for verifying specific claims made by model creators
- `local-ml-hosting` — for local deployment once a model is chosen
- `model-selector` — model pricing comparison across providers

## Scripts

- `scripts/eval-runner.sh` — Sequential model-vs-model eval runner. Takes a profile, comma-separated model list, and task directory. Runs every task through every model sequentially (task→all-models, next-task). Handles output isolation, cost-log extraction, and accepts—check for GreyScript tasks. Load and adapt for any new API model eval.

## References

- `references/research-verification-protocol-2026.md` — Three-URL verification framework (URL1/URL2/URL3), hidden-gems methodology, family inventory approach, and API pitfalls documented from a live multi-model research session (2026-07-16). Read before starting any multi-model comparison.
- `references/example-qwythos-qwen-deep-dive.md` — Full worked example from this session (Qwythos v1→v2→v3 vs Qwen3.5-9B vs Qwen3.6-27B), showing the complete methodology applied to a real comparison. Use as a template for future research-phase reports.
- `references/example-ornith-9b-real-test.md` — Full worked example from this session (Ornith-1.0-9B), showing multi-source GGUF verification, real coding tests, tool-use testing, and side-by-side comparison methodology. Use as a template for future real-world testing phases.
- `references/dual-gpu-compute-detection.md` — Full workflow for finding and verifying secondary GPU (e.g. Intel iGPU) compute capability on PRIME/Optimus laptops for tensor-split inference.
- `references/qwythos-9b-evaluation-2026-07-16.md` — Real 3-way benchmark (Qwythos vs Ornith vs Gemma 4 E4B) on RTX 5060 8GB, 4 coding tasks, warmup protocol, aggregate scoring. Template for future real-testing phases.
- `references/qwen35-family-loop-bug.md` — Qwen3.5-family reasoning-loop root cause, 5-way speed/quality benchmark data, family analysis table, and concrete per-model recommendations for 8GB VRAM. Load when testing any Qwen3.5-9B based model on Ollama.
- `references/local-benchmark-suite-architecture.md` — 7-dimension benchmark suite architecture, num_predict guidelines for thinking models (10-20× buffer needed), Vision OOM workaround on 8GB, Pre-Flight checklist. Template for building your own benchmark project.
- `references/kimi-code-cli-eval-platform.md` — **NEU 2026-07-19:** Kimi Code CLI als alternative Eval-Plattform. Provider-Catalog-System, OAuth-Login für Cup-Token-Verbrauch, Token-Burn-Strategie mit Phasen, Bash-Quoting-Pitfalls, Hybrid-Eval mit Hermes-Profiles. Lade wenn: User kein Cash-Budget hat aber Promo-Tokens besitzt (WM-Tippspiel), oder wenn Kimi-K3 gegen M3 getestet werden soll.