# Gemma4-Architecture Notes — Ollama Benchmark Specifics

**Source:** Verified via Ollama API smoke-tests on 2026-07-17 (yuxin-tau2:latest, gemma4 11.9B Q4_K_M).
**Relevance:** When benchmarking any Gemma4-family model (Gemma 2/3/4 based) via Ollama.

## Why This Matters

Gemma4 differs from the qwen3.5-family (qwythos) in **three critical ways**
that break a naive benchmark clone:

1. **Thinking format:** Plain-Text, not XML-tagged (no `<|im_start|>think<|im_end|>`)
2. **Tool-Call streaming:** Tool calls arrive in `message.tool_calls` of the **penultimate stream chunk**, not the final one
3. **Empty content on tool-only responses:** When the model returns only a tool call, `content=""` is **expected**, not a bug

## Pre-Smoke-Test: MUST DO before cloning

Before cloning an existing benchmark project for a new model architecture,
run this **45-second smoke test** to understand the model's output format:

```bash
# 1. Thinking format
curl -sf http://127.0.0.1:11434/api/generate -d '{
  "model": "<model>:latest",
  "prompt": "Say OK",
  "stream": false,
  "think": true,
  "options": {"num_predict": 100, "temperature": 0.3}
}' | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print('keys:', list(d.keys()))
print('thinking_snippet:', d.get('thinking','')[:200])
print('response:', d.get('response',''))
print('done_reason:', d.get('done_reason'))
"

# 2. Tool-call format (with stream: false)
curl -sf http://127.0.0.1:11434/api/chat -d '{
  "model": "<model>:latest",
  "messages": [{"role": "user", "content": "Use calculator for 17*24."}],
  "tools": [{"type":"function","function":{"name":"calculator","description":"...","parameters":{"type":"object","properties":{"expression":{"type":"string"}},"required":["expression"]}}}],
  "stream": false,
  "options": {"temperature": 0.3, "num_predict": 200}
}' | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print('tool_calls:', d.get('message',{}).get('tool_calls'))
print('content empty?', d.get('message',{}).get('content','') == '')
print('done_reason:', d.get('done_reason'))
"
```

**Checklist:**
- [ ] `thinking` field: Plain-text vs XML-tagged vs absent
- [ ] `response` with `think=True`: non-empty response returned?
- [ ] Tool-calls: OpenAI-compatible format (`{id, function: {name, arguments}}`)?
- [ ] Tool-calls with `stream: false`: visible in the single JSON response?
- [ ] Empty content on tool-only: `content=""` is normal?
- [ ] `done_reason`: `"stop"` or `"length"`?

## Gemma4 Specific Findings (Verified)

### Thinking Format

```
{
  "thinking": "The user wants me to say \"OK\". This is a direct command with no ambiguity. I should comply and output exactly \"OK\".",
  "response": "OK"
}
```

**Key differences from qwen3.5 (qwythos):**
- ✅ Plain-Text in `thinking` field — **no** `<|im_start|>think\n...<|im_end|>` wrappers
- ✅ `response` field is present and correct — no interleaving with thinking
- ✅ `done_reason: "stop"` — standard behavior
- ⚠️ `temperature=0.3` + `think=True` works fine for simple prompts (no logic-loop issues on gemma4)

### Tool-Call Format

**With `stream: false` (recommended for benchmarks):**

```json
{
  "message": {
    "role": "assistant",
    "content": "",
    "thinking": "The user wants to multiply 17 and 24. I should call the calculator...",
    "tool_calls": [{
      "id": "call_v2roujxs",
      "function": {"index": 0, "name": "calculator", "arguments": {"expression": "17 * 24"}}
    }]
  },
  "done": true,
  "done_reason": "stop"
}
```

**With `stream: true` (NOT recommended for deterministic benchmarks):**

Tool calls arrive in the **penultimate chunk** (the one with `done: false`).
The final chunk (`done: true`) resets `tool_calls` to `None`.

**Accumulator pattern required for stream mode:**

```python
accumulated_tool_calls = []
for line in r.iter_lines(decode_unicode=True):
    chunk = json.loads(line)
    if chunk.get("message",{}).get("tool_calls"):
        accumulated_tool_calls = chunk["message"]["tool_calls"]
    if chunk.get("done"):
        break  # final chunk — tool_calls is None here, use accumulated
```

### Empty Content Behavior

Gemma4 returns `content: ""` when it decides a tool call is the only appropriate
response. **This is correct behavior**, not a bug. The model's response is the
tool call, not natural language text.

**Impact on benchmark scoring:**
- Tools runner: Don't require non-empty `response` for a tool-call test to pass
- Quality runner: Normal behavior — quality prompts always include natural language
- Don't flag empty `response` + existing `tool_calls` as a failure

### Stop Token

Gemma4 uses `<turn|>` as its native stop token. Ollama handles this
**transparently** — you don't need to set it manually. The model naturally
stops on `done_reason: "stop"`.

### Max-Variant Ceiling (num_predict=30000 → Reflection Loop)

During the yuxin-tau2 benchmark (gemma4 11.9B on 8 GB GPU), the Max variant
with `num_predict=30000`, `temperature=0.6`, `think=True` caused the model
to enter a reflection loop — running 18+ minutes on a single logic prompt
without converging. See `references/yuxin-tau2-benchmark-results.md`.

Fix: Cap `num_predict` at 16000 for gemma4-family Max variants.

### No Vision Capability

Gemma4 has no CLIP projector — `ollama show` lists:
```
Capabilities: completion, tools, thinking
```
(no `vision`) 

On Ollama, attempting vision on Gemma4 silently returns empty:
```json
{"response": ""}
```
No error, no crash — just no output. The vision smoke runner MUST be a
**skipped stub**, not a request that expects an answer.

## Clone-and-Rename Pattern (alternative to template scaffold)

When benchmarking a model that shares an architecture with an existing benchmark
(e.g. yuxin-tau2 cloned from qwythos-9b because both use the same benchmark
framework), the clone-and-rename pattern is faster than scaffolding from scratch:

```bash
# 1. Clone
cp -r ~/.../benchmarks/<source-model> ~/.../benchmarks/<target-model>
cd ~/.../benchmarks/<target-model>

# 2. Rename source package
mv src/<source_model>_bench src/<target_model>_bench

# 3. Replace all references
grep -rl "source_model" src/ | xargs sed -i 's/source_model/target_model/g'
grep -rl "source_model" tests/ | xargs sed -i 's/source_model/target_model/g'

# 4. Remove architecture-incompatible components
# (e.g. rm -rf test_images/ for vision-less models)

# 5. New venv
rm -rf .venv && uv venv .venv --python 3.11
source .venv/bin/activate && uv pip install -e ".[test]"

# 6. Inline verify
python -c "from <target_model>_bench.ollama_client import OllamaClient; print('ok')"
```

## Known Pitfalls

- **`stream: false` is critical.** Ollama's default is `stream: true` (NDJSON).
  For Gemma4, streaming tool-calls requires the accumulator pattern. Always
  benchmark with `stream: false` to avoid this complexity.
- **Don't assume qwen35 thinking format.** Gemma4 has NO XML tags in thinking.
  If your benchmark parser strips `<|im_start|>` tags, it'll strip plain-text
  thinking instead.
- **Don't flag empty content as error.** Gemma4 tool-only responses have
  `content: ""`. Your tools runner must check `tool_calls`, not `content`.
- **Vision stub is mandatory.** If you skip creating a stub and just delete
  vision prompts, the runner import will crash (missing `prompts/vision_cases.json`).
  Patch the vision runner FIRST, then delete the prompts file.
