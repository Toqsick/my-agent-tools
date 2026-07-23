# LLM Evaluation — Full Reference

Extracted from the `evaluating-llms-harness` and `llm-evaluation-troubleshooting` skills.

## Installation
```bash
pip install lm-eval
```

## Running Benchmarks
```bash
# HuggingFace model
lm_eval --model hf --model_args pretrained=meta-llama/Llama-3.1-8B \
  --tasks mmlu,gsm8k --batch_size auto

# Ollama model
lm_eval --model ollama --model_args model=deepseek-r1:8b \
  --tasks mmlu

# Specific tasks
lm_eval --model ollama --model_args model=deepseek-r1:8b \
  --tasks hellaswag,arc_easy,winogrande
```

## Common Benchmarks
| Benchmark | What it measures |
|-----------|-----------------|
| MMLU | Multitask knowledge (57 subjects) |
| GSM8K | Math reasoning (grade school) |
| HellaSwag | Sentence completion |
| ARC | Science questions |
| Winogrande | Pronoun resolution |
| TruthfulQA | Truthfulness |

## Troubleshooting
- **OOM:** Reduce batch size (`--batch_size 1`) or use smaller model
- **Slow:** Use GPU, reduce task count, use quantized models
- **Task not found:** `lm_eval --tasks list` to see available tasks
- **Ollama connection:** Ensure Ollama is running on expected port

## Interpreting Results
- Scores are typically 0-100% (accuracy)
- Compare against baseline: random chance = 25% for 4-choice tasks
- 7B models: ~50-60% MMLU is good
- 14B+ models: ~65-75% MMLU is good
