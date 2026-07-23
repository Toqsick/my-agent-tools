---
name: local-llm-benchmark
description: "Use when user asks to benchmark a local Ollama model across speed, context, needle retrieval, reasoning, thinking mode, vision, or function calling, or wants JSON data, charts, and an HTML report. NOT for API-model comparisons or deploying a local model. Runs the single-GPU benchmark suite with preflight checks, reproducible tasks, and post-run documentation."
version: 0.3.0
author: Hermes
platforms:
- linux
metadata:
  hermes:
    tags:
    - benchmark
    - ollama
    - llm
    - profiling
    - gpu
license: MIT
trigger_keywords: ['benchmark', 'local', 'model', 'and', 'local-llm-benchmark']
keywords: ['model', 'benchmark', 'local', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['local-ml-hosting', 'model-selector', 'deep-model-evaluation']
---

# Local LLM Benchmark

Benchmark a local Ollama model across seven dimensions (speed, context-scaling,
needle-in-haystack, reasoning-quality, thinking-mode A/B, vision, function-calling)
and emit JSON raw data, a Markdown report, PNG charts, and an interactive HTML
dashboard. Designed for single-GPU laptops (8 GB VRAM proven on RTX 5060).

This is the generalizable procedure — pick the dimensions you need, adapt the
test sets, run the suite. The bundled template project (`scripts/benchmark_suite_template/`)
gives you the file layout; you fill in your model's name and prompts.

## When to Use

- "How fast is <model> on my GPU?"
- "Can <model> handle 64k context?"
- "Compare thinking-mode ON vs OFF for <model>"
- "Does <model> support vision / function-calling?"
- "Tiefen-Profil / Benchmark für <lokal installiertes Modell>"

## Prerequisites

- Ollama running locally (`ollama serve`, default `127.0.0.1:11434`)
- Target model pulled (`ollama pull <model>`)
- Python 3.11+ with `uv` installed (`pip install uv`)
- NVIDIA GPU with `nvidia-smi` on PATH
- Optional: `systemctl` if you have a custom OC service (nvidia_oc etc.) to stop

## How to Run

Invoke through the `terminal` tool from your project root:

```bash
# 1. Scaffold from the template
cp -r ~/.hermes/skills/local-llm-benchmark/scripts/benchmark_suite_template ./bench-<model>
cd ./bench-<model>

# 2. Set up venv + deps
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[test]"

# 3. Edit src/qwythos_bench/runners/*.py → set MODEL = "<your-model>"

# 4. Pre-flight (stops nvidia_oc, checks disk + Ollama)
python -m qwythos_bench.run_all --no-preflight=false

# 5. Background-run for full suite (45–90 min)
python -m qwythos_bench.run_all --brief

# 6. Open dashboard
xdg-open results/dashboard.html
```

## Quick Reference

| Dimension | Output JSON | Test Count |
|---|---|---|
| Speed | `raw/speed_*.json` | 5 output sizes (128–8192 tok) |
| Context | `raw/context_scaling_*.json` | 4 sizes (1k/4k/16k/64k) |
| Needle | `raw/needle_haystack_*.json` | 6 runs (128k/256k × 3 pos) |
| Quality | `raw/quality_*.json` | 37 (15 MMLU + 12 GSM + 10 HE) |
| Thinking | `raw/thinking_ab_*.json` | 10 prompts × 2 modes |
| Vision | `raw/vision_smoke_*.json` | 5 images |
| Tools | `raw/tools_smoke_*.json` | 5 tool calls |

Key flags:
- `--brief` — concise output (one line per runner)
- `--skip <name>` — skip a runner (e.g. `--skip needle_haystack`)
- `--no-preflight` — skip GPU/Ollama checks

## Procedure

1. **Check HF card for official sampling defaults.** Before writing any
   benchmark code, visit the model's Hugging Face card and extract the
   official sampling defaults (temperature, top_p, top_k, repeat_penalty).
   Many reasoning models have non-obvious requirements — e.g. qwythos
   (qwen35 family) officially warns that `T≤0.3` causes **repetition
   loops** on long reasoning generations. Record these in the project's
   `references/` dir. *This single step can prevent 2–3 wasted re-run
   iterations.*

2. **Plan review first.** Before writing code, scan the plan with the
   `orchestration/plan-review-and-orchestrate` skill. Five categories of
   weakness to check: (1) Mnemosyne-ID placeholders, (2) section-anchor
   vagueness, (3) test-cluster-at-end, (4) output-bomb risk, (5) bite-sized
   tasks with hard output-bounds. Do not skip this — it catches 3+ bugs
   before any code is written.

3. **Pre-Smoke-Test the target model before building anything.** Before
   scaffolding or cloning, send 2–3 direct API calls to determine the model's
   output format. This single 60-second step prevents the most common source
   of re-runs (wrong thinking-format, wrong tool-call parsing, wrong vision
   capability). See `references/gemma4-architecture-notes.md` for exact
   shell commands and checklist.

4. **Scaffold project structure.** Either clone from an existing benchmark
   project (same framework, different model — see
   `references/gemma4-architecture-notes.md` for the clone-and-rename
   pattern) or create from the template layout:
   ```
   bench-<model>/
   ├── src/<name>_bench/
   │   ├── ollama_client.py    # keep_alive="30m" default
   │   ├── system_metrics.py   # nvidia-smi + psutil sampler
   │   ├── runners/            # one file per dimension
   │   ├── charts.py           # matplotlib, dark theme, 150 dpi
   │   ├── aggregate.py        # REPORT.md + dashboard.html
   │   ├── run_all.py          # master with --brief + preflight
   │   └── templates/          # jinja2 dashboard + CSS
   ├── prompts/                # deterministic test sets
   ├── tests/                  # pytest for client + sampler
   ├── results/                # raw/, charts/, REPORT.md, dashboard.html
   └── pyproject.toml

5. **Wire the Ollama client.** Critical defaults that prevent benchmark
   pollution: `keep_alive="30m"` in `__init__`, `default_timeout=600`,
   `base_url="http://127.0.0.1:11434"`. Wrap `/api/generate`, `/api/chat`
   (for tools), `images=[base64]` parameter for vision, `think=True/False`
   for thinking-mode. Never let `requests` time out mid-inference.

   **Gemma4-specific:** The `chat()` method must handle tool-call streaming
   correctly. Gemma4 emits tool_calls in the penultimate stream chunk
   (done=False), and resets them to None in the final done=True chunk.
   Use the accumulator pattern: iterate all NDJSON lines, save the last
   non-None tool_calls, and return that. Always benchmark with
   `stream: false` to avoid this complexity entirely.

6. **Pick `num_predict` generously.** Thinking-models write the answer
   inside the thinking block when `num_predict` is too small — `response`
   comes back empty. Minimums by task:
   - Multiple-choice: `num_predict >= 80` + `think=False`
   - Code completion: `num_predict >= 500`
   - Thinking ON/OFF A/B: `num_predict >= 1500`
   - Free-form generation: `num_predict >= 400`

7. **Pre-flight before every run.** Verify in `run_all.py`:
   - `systemctl is-active nvidia_oc` → stop if active (sudo)
   - `nvidia-smi --query-gpu=power.limit` → 80W baseline
   - `curl -sf http://127.0.0.1:11434/api/tags` → Ollama up
   - `df -BG $HOME` → ≥5 GiB free
   - `ollama stop` other models to free VRAM

8. **Handle VRAM pressure per dimension.** On 8 GB GPUs the language
   model alone uses ~7.5 GB. Vision models with CLIP projectors (456M+)
   WILL OOM. Workaround for vision: `options={"num_gpu": 20}` forces
   CPU offload. Accept the ~4x latency hit; document it in the report.

9. **Run in background.** Use `terminal(background=true,
   notify_on_complete=true)`. A full 7-dimension suite takes 45–90 min.
   Always `tee results/logs/run-<timestamp>.log` for postmortem.

9. **Optional: Thinking-Variant comparison (Off / Balanced / High).**
  Use this when you need to decide whether thinking-mode helps your
  specific task. The pattern: run the *same* 10+ reasoning prompts
  across three settings:

  | Variant | `think` | `temperature` | `num_predict` | Expected latency |
  |---|---|---|---|---|
  | **Off** | `false` | 0.3 | 200 | ~7s/test (~2x tokens after cutoff) |
  | **Balanced** | `true` | 0.6 | 1000–1500 | ~30s/test (thinking + answer) |
  | **High** | `true` | 0.6 | 4000–8000 | ~60–90s/test (deep reasoning) |

  Critical rules for a fair comparison:
  - **Use `:latest` tag** (not a large-context custom tag). Override
    `num_ctx=4096` per-request — the test prompts are <100 tokens.
    Using a 131k-context tag drops throughput 3–4× and invalidates
    the comparison.
  - **Expected-keywords must be pre-validated.** Score each prompt's
    expected answer manually before the run. A wrong keyword produces
    a false 0% score and wastes the entire run.
  - **Score from combined response + thinking.** Many models write the
    answer in `thinking` when `num_predict` is tight. Check both fields.
  - **Compute timeout per variant:** `max(300, num_predict / expected_tps * 1.5)`.
    The High variant with 8000 tok at 8 t/s needs 1500s — a 300s default
    will preempt it before the model finishes.
  - **Use `--brief` output.** One line per result — critical for
    monitoring a 30-test run without scrolling.

  Reference implementation: see `references/thinking-variant-methodology.md`
  for a complete runner skeleton.

  Example summary table after all 4 × 10 tests (using official Empero defaults
  as shown in `references/qwythos-hf-sampling-defaults.md`):
  ```
        Variant |  Score | Avg Tok |  Avg s |  t/s | Sat
  -------- | ------ | ------- | ------ | ---- | ---
        off |  70.0% |     173 |   6.80 | 28.0 | 8/10
   balanced |  90.0% |     848 |  30.70 | 27.4 | 3/10
       high | 100.0% |    1019 |  36.10 | 26.8 | 1/10
        max | 100.0% |     988 |  36.37 | 27.6 | 1/10
  ```
  > ⚠️ **Temperature matters!** The Off variant scores only 70% because
  > `temperature=0.3` + `think=False` triggers the qwen35-family thinking-loop
  > bug on complex logic prompts. With the old wrong defaults (T=0.0), Off had
  > 90% — but the model wasn't producing real answers, only reproductions.
  > With official defaults, thinking ON adds +30% accuracy at ~5× latency cost.

10. **Validate atomically.** Each runner writes one JSON to `results/raw/`.
  The aggregator reads the *latest* JSON per dimension, so partial runs
  still produce useful output. Schema validation in `aggregate.py` flags
  `"⚠ partial: <missing fields>"` instead of crashing.

11. **Iterate on bugs found in run 1.** Expect 1–3 runner-config bugs on
  first run (typically `num_predict` too low, vision OOM, think-mode wrong).
  Re-run only the broken dimensions, then regenerate the dashboard. Document
  each fix in the report's Executive Summary.

12. **Save the run as a skill.** Once the suite is green, write a
   Mnemosyne memory with the headline numbers + every bug found. Future
   runs of the same model start at "what changed since last time?"

13. **Re-run with official sampling defaults (critical quality step).**
   The first benchmark run almost always uses suboptimal sampling defaults
   (typically `temperature=0.0` or Ollama defaults `T=0.8`). The model's
   HF card specifies officially recommended defaults — applying them in a
   second run can improve aggregate quality by **10–15%**.

   After fixing runner bugs (Step 11), apply the model-author defaults:
   - Set `temperature`, `top_p`, `top_k`, `repeat_penalty` from the HF card
   - Use `think=False` with `T=0.3` for structured QA / MC / code tasks
   - Use `think=True` with `T=0.6` for complex reasoning tasks
   - Verify `min_p` and `repeat_last_n` — not every model card specifies these

   **Proven impact (2026-07-17 qwythos benchmark):**
   | Metric | Wrong Defaults (T=0.0) | Empero Defaults (T=0.6) | Δ |
   |---|---|---|---|
   | GSM8K-Lite | 66.7% | **91.7%** | +24.7% |
   | HumanEval-Lite | 60% | **70%** | +10% |
   | Aggregate Reasoning | 75.6% | **87.2%** | +11.6% |
   | Thinking ON score | 80% (showed no benefit) | **100%** (proven benefit) | +25% |

   The Thinking-Effort comparison (Step 9) MUST be run with official defaults
   — the old run with `T=0.0` produced the wrong conclusion ("thinking adds
   no value"). With correct defaults, thinking ON adds +30% accuracy.

   **Expected re-run time:** ~10-15 min for Quality + Thinking-Variants.
   Re-run only the Quality + Thinking runners, not the full 7-dimension suite.
   After the re-run, regenerate the aggregator report and update the dashboard.

14. **Cross-Compare with a second model (optional, high-value).** Once one
   model is fully benchmarked, running the *same suite* on a second model
   provides far more insight than either benchmark alone. The marginal cost
   is low (~25 min for a straightforward clone+run) because the test prompts
   and aggregator are already built.

   **Clone-and-Rename workflow (proven 2026-07-17, qwythos → yuxin-tau2 and qwythos → qwen-dsv4-q5):**

   **Phase 1: Pre-rename inventory.** Before touching any files, find ALL references to the old project name AND the old model tag. This is critical — the plan usually only lists obvious refs, but `MODEL = "old-name"` constants in runner files are easy to miss:

   ```bash
   cd ./benchmarks/<model-B>

   # Find ALL references — both package namespace AND model tag
   echo "=== Package namespace refs ==="
   grep -rn "qwythos_bench\|qwythos_" . --include="*.py" --include="*.toml" --include="*.j2" --include="*.md" | grep -v ".venv" | grep -v "__pycache__"

   echo "=== Model tag refs ==="
   grep -rn "qwythos-9b-q6" . --include="*.py" --include="*.toml" --include="*.j2" --include="*.md" | grep -v ".venv" | grep -v "__pycache__"
   ```

   The inventory tells you exactly which files need renaming. Do NOT skip this — plans routinely miss 3-5 files (proven 2026-07-17: the qwen-dsv4-q5 plan only listed `pyproject.toml` + 1 test, but source had `MODEL` constants in 8 runner files).

   **Phase 2: Two-pattern rename.** The package namespace and the model tag are SEPARATE targets — a single `sed` pass cannot cover both if the strings differ:

   ```bash
   # 1. Rename package directory
   mv src/<model_a>_bench src/<model_b>_bench

   # 2. Rename package namespace in source + tests (sed -i)
   grep -rl "<model_a>" src/ tests/ pyproject.toml | xargs sed -i 's/<model_a>/<model_b>/g'

   # 3. Rename model tag in runner constants, prompts, tests (sed -i)
   #    The model tag (e.g. "qwythos-9b-q6:latest") is DIFFERENT from the
   #    package namespace (e.g. "qwythos_bench") — this is a SECOND pass!
   grep -rl "qwythos-9b-q6" src/ tests/ pyproject.toml README.md 2>/dev/null | \
     xargs sed -i 's/qwythos-9b-q6/qwen-dsv4-q5:latest/g'

   # 4. Rename model-agnostic refs (bare model name without tag)
   grep -rl '"qwythos"' src/ tests/ 2>/dev/null | xargs sed -i 's/"qwythos"/"qwen-dsv4-q5"/g'

   # 5. Update README model name in prose (title, description, command examples)
   ```

   **Phase 3: Post-rename verification.** Confirm zero residual old names remain in active code:

   ```bash
   grep -rn "qwythos" . --include="*.py" --include="*.toml" --include="*.j2" --include="*.md" | grep -v ".venv" | grep -v "__pycache__" | grep -v "results/raw/" || echo "ALL CLEAN"
   ```

   Residual old names in `results/raw/*.json` (historical benchmark data) are EXPECTED — do NOT modify them as they're legitimate prior-run artifacts. Also check test assertions that might reference the old model name.

   **Phase 4: Inline-verify.** After venv setup, verify the package imports correctly:

   ```bash
   source .venv/bin/activate
   # ⚠️ PYTHONPATH=src required! pyproject.toml's [tool.pytest.ini_options] pythonpath
   # only works for pytest, NOT for standalone `python -c`.
   PYTHONPATH=src python -c "from <model_b>_bench.ollama_client import OllamaClient; print('client_ok')"
   ```

   Then run pytest to confirm the config picks up the package automatically:

   ```bash
   python -m pytest tests/ -q 2>&1 | tail -5
   ```

   **The `test_list_models_returns_*` test** asserts a model name string — it MUST be updated to the new model name, or it will fail on the first test run. This is the most commonly forgotten test after a rename. Always check test assertions, not just import paths.

   ```bash
   rm -rf .venv test_images/   # new venv + remove incompatible artifacts
   ```

   **Before cloning — MUST run the Pre-Smoke-Test (Step 3).** Send 2–3
   direct API calls to the NEW model to determine its exact output format
   BEFORE touching any code. Thinking-format differences (plain-text vs
   XML-tagged), tool-call differences (penultimate chunk vs final chunk),
   and vision detect are the top-3 breakers. This single 60-second step
   prevents the most common source of re-runs — the yuxin-tau2 clone had
   0 runner bugs because the pre-smoke caught format differences first.

   **Key risks when cloning to a different architecture:**
   - **Thinking format** — qwen35 uses XML tags (`<|im_start|>think`),
     gemma4 uses plain-text. If your parser strips tags from thinking,
     it'll strip non-tag content from gemma4.
   - **Tool-call streaming** — Some architectures emit `tool_calls` in the
     penultimate chunk (gemma4) vs final chunk (qwythos/qwen35). Always
     use `stream: false` for benchmarks to avoid this complexity.
   - **Empty content** — Gemma4 returns `content: ""` on tool-only responses.
     Score from `tool_calls`, not `content` non-emptiness.
   - **Vision** — If model-B has no CLIP projector, delete vision runner
     prompts AND patch the vision runner to be a skipped stub (otherwise
     the import crashes when `prompts/vision_cases.json` is missing).
   - **VRAM budget** — A bigger model on the same GPU means less headroom.
     Model-A may fit 64k context on GPU; model-B (+29% params) may not.
     Check `ollama ps` after loading model-B.

   **Phase 6: Test-set propagation (critical maintenance rule).** When a
   shared test-set (e.g. `prompts/thinking_prompts.json`, `prompts/mmlu_cases.json`)
   is fixed OR extended in one benchmark project, propagate the fix to ALL
   cloned benchmark projects immediately — otherwise the other models' scores
   are silently wrong.

   ```bash
   # After fixing thinking_prompts.json in qwythos-9b:
   md5sum benchmarks/{qwythos-9b,yuxin-tau2,qwen-dsv4-q5}/prompts/thinking_prompts.json
   # If any differ, overwrite all from the canonical source:
   cp benchmarks/qwythos-9b/prompts/thinking_prompts.json \
      benchmarks/yuxin-tau2/prompts/thinking_prompts.json
   cp benchmarks/qwythos-9b/prompts/thinking_prompts.json \
      benchmarks/qwen-dsv4-q5/prompts/thinking_prompts.json
   git add benchmarks/*/prompts/thinking_prompts.json
   git commit -m "bench: propagate test-set fix to all clones"
   ```

   This rule exists because test-set bugs are discovered during ANALYSIS
   (after all runs complete), but fixing them only in the original means
   the other 2+ models' scores remain wrong until the next re-run.
   produce a side-by-side table with:
   - Speed (t/s per output size)
   - Reasoning accuracy (MMLU, GSM8K, HumanEval)
   - Thinking-mode effectiveness
   - Function-calling success
   - Context scaling performance
   - **Winner per category** (for routing decisions)

   See `references/yuxin-tau2-benchmark-results.md` for a complete
   cross-comparison example (qwythos vs yuxin-tau2 on RTX 5060).

## GPU Contention Factor (Cross-Comparison Caveat)

**Critical discovery (2026-07-17):** The same model on the same GPU yields
dramatically different speed depending on how many other models are loaded:

| Model | Alone (dedicated GPU) | Shared VRAM | Δ |
|---|---|---|---|
| qwen-dsv4-q5 (9.0B Q5) | **50.7 t/s** | — (only loaded model) | baseline |
| qwythos-9b-q6 (9.2B Q6) | 22.5 t/s | 23.5 t/s | +4% (negligible) |
| yuxin-tau2 (11.9B Q4) | 18 t/s | 20.2 t/s | +12% (negligible) |

The 2× gap between qwen-dsv4-q5 (50 t/s) and the others (~22 t/s) is NOT
entirely architectural — qwen-dsv4-q5 was the **only loaded model** at test
time, while qwythos and yuxin shared VRAM with multiple loaded models.

**Rule:** Speed comparisons between models MUST be run with identical GPU
load state. Either stop all other models with `ollama stop <name>` before
each run, or document which models were loaded during each benchmark. The
50 t/s number is a valid "dedicated GPU" speed; the 22 t/s number is a
valid "daily driver with other models" speed — but they cannot be compared
directly without this caveat.

## `num_predict` Practical Ceiling

For reasoning tasks on 8 GB GPUs, `num_predict` beyond 16000 causes
pathological wall-clock times:

| `num_predict` | Task | Wall Time | Outcome |
|---|---|---|---|
| 16000 | 12-balls logic (4045 tokens used) | 147s | ✅ Score 100% |
| 30000 | Same task | >26 min (aborted) | ❌ Reflexion loop |

The model uses dynamic budget — it stops when `done_reason=stop`, but with
a large predict-limit a reasoning loop that doesn't converge runs unbounded.

**Rule:** Cap `num_predict` at **16000** for reasoning benchmarks on 8 GB.
Add an explicit timeout catch on each runner:

```python
computed_budget = max(300, num_predict / expected_tps * 1.5)
capped_budget = min(computed_budget, 600)  # hard cap at 10 minutes
```

## Documentation Reaction (Mandatory Post-Benchmark Phase)

After each benchmark reaches final results, create ALL of the following before
moving on to the next task:

1. **Reference Wiki** → `09 System-Doku/<model>-reference.md` in Obsidian vault
   (template: `09 System-Doku/qwythos-9b-reference.md`)
2. **Inbox note** → `02 Inbox/<model>-benchmark-<date>.md` with raw results
3. **Cross-links** — reference Wiki links TO and FROM other model references
   (e.g. qwythos-ref → yuxin-ref, yuxin-ref → qwythos-ref + cross-comparison)
4. **Mnemosyne memory** with headline numbers for each dimension
5. **Optional but recommended:** Side-by-side comparison table against all
   previously benchmarked models on the same GPU

This phase takes ~5 minutes but prevents "we benchmarked that — where are
the numbers?" post-hoc searches. See the `references/` dir for examples.

## Pitfalls

- **Thinking-Loop on `temperature=0.0`:** qwythos (and similar qwen35
  variants) write the answer in `thinking` when given small `num_predict`,
  leaving `response=""`. Workaround: `think=False` for structured output,
  or `temperature >= 0.3`.
- **Comparison benchmarks must NOT use a large-context tag.** If you
  created a custom tag (e.g. `qwythos-9b-q6:128k`), the model allocates
  13 GB KV-cache (49%/51% CPU/GPU), dropping throughput from ~28 t/s to
  ~8 t/s. For comparison runs (thinking ON/OFF, temperature sweeps, etc.)
  that don't need large context, use `:latest` and override `num_ctx=4096`
  per-request. The speed difference is 3–4×.
- **Expected-keywords in test prompts must be verified for correctness.**
  Before running a benchmark, manually validate each expected_keyword
  against the actual correct answer. Getting the math wrong (e.g. 11:36
  instead of 11:43 for a train problem) produces false-negative scores
  and wastes 30+ minutes on re-runs. **Queen-Verify protocol:** have the
  agent solve the problem independently (write a calculator script), then
  compare the known-correct answer against every expected_keyword. Add
  tolerance variants (e.g. `"11:42", "11:43 AM", "1 hour 43"`) to catch
  different phrasing. This single verification step prevented a 60-minute
  re-run on the 2026-07-17 3-model benchmark day (think_01 keywords were
  `["11:30", "11:36", "11:00"]` but correct answer is 11:42).
- **Timeout budgets differ per variant.** A `num_predict=8000` thinking
  variant needs ~300s at 8 t/s (large context) but only ~60s at 28 t/s
  (small context). Always compute max_wall = (num_predict / expected_tps)
  × 1.5 safety margin. Cap `timeout` at `max(300, max_wall)`.
- **Vision OOM on 8 GB:** CLIP projector + 8.5 GB language model > 8 GB.
  Don't waste time debugging — go straight to `num_gpu=20`. Note that
  `num_gpu=30` WILL CUDA-OOM on 9B + CLIP models (Q5_K_M quantization).
  The sweet spot is 20 — enough GPU to keep evaluation fast, low enough
  to leave ~400 MB headroom for the CLIP projector. Expect 4× latency.
- **`Path.parents[X]` off-by-one:** Runner in `src/<pkg>/runners/` needs
  `parents[3]` for project root, not `parents[2]`. Easy to miss.
- **`statistics.max` doesn't exist:** it's `max()` (builtin). LSP false
  positive.
- **`stream=false` required for single-response:** Ollama's default is
  `stream=true`, which emits NDJSON — one JSON object per token. If your
  parser expects a single JSON response it fails with `Extra data`. Always
  pass `stream=false` in benchmark code.
- **`keep_alive` defaults vary:** 5m in older Ollama builds, longer in
  newer. Always pass `keep_alive="30m"` explicitly to avoid mid-suite
  re-loads that pollute throughput measurements.
- **SystemSampler race:** background nvidia-smi thread stops ~1s after
  `stop()` returns, so very-long calls (>1 min) may report `vram_peak=0`.
  Pre-flight power/temp snapshots are more reliable than the sampler
  for needle-haystack-style long calls.
- **Loading-time pollution:** If the model isn't loaded yet, the first
  request reports `load_duration > 5s`. Use a warmup call before
  starting measurements.
- **128k-context on 8GB GPU forces CPU-offload:** Setting `num_ctx=131072`
  on an 8 GB GPU causes Ollama to split 49%/51% CPU/GPU, uses 13 GB
  process memory, and drops throughput from ~22 t/s to ~10 t/s. The
  practical upper limit for reliable single-GPU benchmarks on 8 GB is
  ~64k context. Document the split in every report.
- **Empty response on structured output (qwen35-family):** With
  `think=True`, qwen35-family models (qwythos, qwen-dsv4-q5) write the
  entire answer inside the `thinking` block and leave `response=""`.
  This affects ALL structured output: multiple-choice, single-word QA,
  vision answers, and code. It's NOT a model-quality bug — the answer is
  there, just not where the parser expects it. Fix: `think=False` for
  structured/QA/vision outputs. The fix alone turned MMLU from 6.7% →
  100% in the qwythos run. **Temperature is not the root cause** — even
  at `T=0.3` the model writes answers into `thinking` on structured tasks.
  High-complexity tasks like needle-in-haystack also suffer: the answer
  is produced inside `thinking` but `response` comes back empty.
- **Re-run iteration pattern:** Expect 1–3 config bugs on first run
  (num_predict too low, vision OOM, think-mode wrong). Don't restart
  the full suite — re-run only broken dimensions via their individual
  runners, then regenerate the aggregator. Each re-run adds ~3–5 min.
- **Subagent double-tag bug (`:latest:latest`):** Subagents (delegate_task)
  consistently produce `MODEL = "old-name:latest:latest"` on rename — they
  treat the combined variable `"qwythos-9b-q6:latest"` as a base string and
  append another `:latest`. Mandatory Queen-Verify check:
  ```bash
  grep -n ':latest:latest:latest' src/*/runners/*.py
  # or the simpler pattern
  grep -En '":latest:latest"' src/<pkg>/runners/*.py
  ```
  Fix with `sed -i 's/:latest:latest/:latest/g'` before running tests.

## Verification

```bash
# 1. Unit tests pass
pytest tests/ -v   # expect 8 passed

# 2. All 7 raw JSONs exist
ls results/raw/*.json | wc -l   # expect 7 (one per dimension)

# 3. Dashboard opens
xdg-open results/dashboard.html

# 4. Headline numbers plausible
cat results/REPORT.md | head -10
# expect: Throughput 15-30 t/s, MMLU >50%, Tools 4+/5
```

If any check fails, the most likely culprits (in order): `num_predict` too
low, vision OOM, `Path.parents[X]` off-by-one, `keep_alive` forgotten.

## See Also

- Reference run: `~/10-Projekte/10-active/greyhack-tools/benchmarks/qwythos-9b/`
- Reference results: skill `local-llm-benchmark` → `references/qwythos-9b-8gb-results.md`
- Qwythos official sampling defaults: skill `local-llm-benchmark` → `references/qwythos-hf-sampling-defaults.md`
- Yuxin-Tau2 (gemma4) benchmark: skill `local-llm-benchmark` → `references/yuxin-tau2-benchmark-results.md`
- Thinking-variant methodology: skill `local-llm-benchmark` → `references/thinking-variant-methodology.md`
- Thinking-variant runner (reference impl): `~/10-Projekte/10-active/greyhack-tools/benchmarks/qwythos-9b/src/qwythos_bench/runners/thinking_variants.py`
- Lessons: Mnemosyne `279820cc5c448b6c` (plan-review), `3bf6b93439f29549` (run results)
- Plan-review skill: `orchestration/plan-review-and-orchestrate`
- Custom Modelfile tags for context tuning: skill `ollama-local-hosting` (Section: `Critical Warnings` → Method D)
- Qwen-DSV4-Q5 benchmark clone (2026-07-17): `~/10-Projekte/10-active/greyhack-tools/benchmarks/qwen-dsv4-q5/` — first project where the two-pattern rename was discovered. Plan missed 8 runner `MODEL` constants.
- Qwen-DSV4-Q5 benchmark results: skill `local-llm-benchmark` → `references/qwen-dsv4-q5-benchmark-results.md`