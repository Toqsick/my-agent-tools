# Thinking-Variant Comparison — Runner Pattern

This reference captures the methodology for comparing Thinking-Off, Balanced,
and High-Effort variants of a model on the same reasoning test set.

## When to Use

- "Does thinking-mode help this model for my task?"
- "How much latency/accuracy trade-off comes with thinking ON?"
- You're tuning a model's default config and want to set `think` correctly
  per task category (QA → OFF, complex reasoning → ON).

## The 4 Variants

| Variant | `think` | `temperature` | `num_predict` | Use Case |
|---|---|---|---|---|
| **Off** | `false` | **0.3** ⚠️ | 200 | Fast, structured output (MC, JSON, short code) |
| **Balanced** | `true` | 0.6 | 1500 | Light reasoning with moderate budget |
| **High** | `true` | 0.6 | 8000 | Deep reasoning (multi-step, proof-heavy) |
| **Max** | `true` | 0.6 | 16000 | Maximum reasoning (complex multi-branch logic) |

> **⚠️ Temperature ≥ 0.3 erforderlich für think=False bei qwen35-Family:**
> Empero (qwythos-9b) warnt offiziell: `T ≤ 0.3` + `think=False` → **Repetition-Loops**.
> Das Modell produziert dann endlose Thinking-Blöcke ohne sichtbare Antwort (`response=""`).
> Der Fix: `temperature=0.3` für Off-Variante, `temperature=0.6` für Thinking-Varianten.
> Siehe auch: `references/qwythos-hf-sampling-defaults.md`

## Test Prompt Design

Use 10–15 prompts spanning 2–3 categories:

```json
[
  {
    "id": "math_01",
    "prompt": "If a train leaves Station A at 9:00 AM traveling at 60 mph...",
    "expected_keywords": ["11:43", "11:42"],
    "kind": "math"
  },
  {
    "id": "logic_01",
    "prompt": "You have 12 balls that look identical...",
    "expected_keywords": ["divide", "group", "weigh"],
    "kind": "logic"
  },
  {
    "id": "trick_01",
    "prompt": "A farmer has 17 sheep. All but 9 die...",
    "expected_keywords": ["9"],
    "kind": "trick"
  }
]
```

**Critical rule:** Pre-validate every `expected_keyword` manually before
running. Solve each prompt yourself and verify the keyword matches the real
answer. Wrong keywords (e.g. "11:36" when the answer is "11:43") produce
false 0% scores and waste the run.

## Runner Skeleton

Score from **both** `response` + `thinking` fields:

```python
def _score(response, thinking, expected_keywords):
    combined = (thinking + " " + response).lower()
    for kw in expected_keywords:
        if kw.lower() in combined:
            return 1.0
    return 0.0

def _ask(prompt, *, think, temperature, num_predict):
    r = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": "<model>:latest",  # NEVER use a large-context tag!
            "prompt": prompt,
            "stream": False,
            "think": think,
            "options": {
                "num_ctx": 4096,           # small → full GPU speed
                "num_predict": num_predict,
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 20,
                "repeat_penalty": 1.05,
                "repeat_last_n": 64,
            },
            "keep_alive": "30m",
        },
        timeout=max(300, num_predict / 15 * 1.5),  # safety margin
    )
    d = r.json()
    return d.get("response",""), d.get("thinking",""), d.get("eval_count",0)
```

## Timeout Budget Per Variant

| Variant | num_predict | t/s (GPU, sm ctx) | t/s (CPU-offload, lg ctx) | Safe timeout |
|---|---|---|---|---|
| Off | 200 | 28 | 8 | 60s |
| Balanced | 1500 | 27 | 8 | 300s |
| High | 8000 | 26 | 7 | **900s** |

The High variant with 8000 tokens at CPU-offload speeds (~7 t/s) needs
~1200s wall-time. A 300s default will preempt it silently.

## Output Table (Empero Defaults — qwythos-9b-q6)

After the run, aggregate per variant (example from the 2026-07-17 reference run):

| Variant | Score | Avg Tok | Avg s | t/s | Saturation |
|---|---|---|---|---|---|
| off (np=200, T=0.3, think=F) | 70.0% | 173 | 6.8 | 28.0 | 8/10 |
| balanced (np=1500, T=0.6, think=T) | 90.0% | 848 | 30.7 | 27.4 | 3/10 |
| high (np=8000, T=0.6, think=T) | 100.0% | 1019 | 36.1 | 26.8 | 1/10 |
| max (np=16000, T=0.6, think=T) | 100.0% | 988 | 36.4 | 27.6 | 1/10 |

"Saturation count" = prompts where `done_reason == "length"` — the model
was cut off mid-answer. High saturation in Balanced/High means you need a
larger `num_predict`.

## Known Pitfalls

- **Wrong tag kills comparability.** Using `:128k` vs `:latest` isn't just
  a speed difference — it changes the model's memory layout (CPU-offload
  introduces latency variance). All variants MUST use the same tag.
- **Single-run variance is real at T≥0.6.** For stable scores, run each
  variant 2–3 times and report the mean. With T=0.3 (Off), variance is low.
- **`done_reason="length"` masks a correct answer.** The model may have
  answered correctly before `num_predict` ran out. Check the response
  truncation — if it ends mid-word, increase `num_predict`.
- **Thinking-Off doesn't mean no thinking.** Some models (qwen35 family)
  produce thinking blocks even with `think=False`. The difference is:
  with `think=False`, the thinking is shorter and you PAY for it in
  token cost but don't get the benefit. Always check `response` content.
- **Temperature=0.0 kills think=False too.** Empero warns that T≤0.3
  causes repetition loops on qwen35 family — even with `think=False`.
  The model writes the entire answer inside the `thinking` block and
  leaves `response=""`. Fix: `temperature>=0.3` for think=False,
  `temperature>=0.6` for think=True (per Empero default).
- **Max variant doesn't waste budget.** With `num_predict=16000`, the
  model only uses ~1000 tok avg (same as `num_predict=8000`). The extra
  budget doesn't hurt — the model stops naturally when done. Useful for
  edge-case prompts that need deep reasoning (e.g. 12-ball logic problem
  used 4045 tokens).

## Reference Run (2026-07-17)

**Model:** qwythos-9b-q6 on RTX 5060 8GB (80W TGP, no OC)
**Setup:** `:latest` tag, `num_ctx=4096`, official Empero sampling defaults:
`temperature=0.6`, `top_p=0.95`, `top_k=20`, `repeat_penalty=1.05`, `repeat_last_n=64`
**Prompts:** 10 mixed reasoning (math, logic, trick)

| Variant | Score | Avg Tok | Avg s | t/s | Sat |
|---|---|---|---|---|---|
| off (np=200, T=0.3, think=F) | 70.0% | 173 | 6.8 | 28.0 | 8/10 |
| balanced (np=1500, T=0.6, think=T) | 90.0% | 848 | 30.7 | 27.4 | 3/10 |
| high (np=8000, T=0.6, think=T) | 100.0% | 1019 | 36.1 | 26.8 | 1/10 |
| max (np=16000, T=0.6, think=T) | 100.0% | 988 | 36.4 | 27.6 | 1/10 |

**Key findings:**

1. **Off scores 70%** — the 3 missed prompts had empty responses (temperature=0.3+think=False triggered the known qwen35 thinking-loop bug on complex logic). **Not recommended for complex reasoning.**
2. **Balanced scores 90%** — missed 1 trick question. Good latency/accuracy trade-off.
3. **High and Max both 100%** — and Max used FEWER avg tokens than High (988 vs 1019). The model doesn't "waste" extra `num_predict` budget — it produces the same answer at the same speed.
4. **Saturation drops from 8/10 (Off) to 1/10 (High/Max).** Thinking ON eliminates mid-answer cutoffs.
5. **Verdict:** For this model, `think=True` with `temperature=0.6` and `num_predict=8000` is the clear winner — 100% accuracy at acceptable latency.

**Contrast with the PRE-Empero-defaults run (same hardware, T=0.0, repeat=1.0):**
That run showed Off 90%, Balanced 80%, High 90% — suggesting "thinking ON adds no accuracy gain."
**That was wrong.** With official defaults, thinking ON adds +30% accuracy.
