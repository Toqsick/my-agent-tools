---
name: evaluating-llms-harness
description: >-
  Use when user asks for benchmarking LLMs on MMLU, GSM8K, or standard tasks, comparing model quality reproducibly, tracking checkpoint performance, or reporting standardized evaluation metrics. NOT for debugging a broken lm-eval installation or choosing a model by subjective preference. Provides repeatable lm-evaluation-harness workflows for local or hosted models, result capture, and training-progress comparisons.
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies:
  - lm-eval
  - transformers
  - vllm
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['Evaluation', 'LM Evaluation Harness', 'Benchmarking', 'MMLU', 'HumanEval', 'GSM8K', 'EleutherAI', 'Model Quality', 'Academic Benchmarks', 'Industry Standard']
lane: worker-heavy
reasoning_effort: xhigh
agent: Analyst
routing_hint: |
  **Agent-Scope:** Data, ML, modeling, statistics, training, evaluation. Off-scope: visual design, code writing, copy — return to Yuno.
  
  Routing-Spec: `yuno-team-routing`.
trigger_keywords: ['model', 'evaluating-llms-harness', 'benchmarking', 'llms', 'mmlu']
keywords: ['model', 'evaluation', 'user', 'asks', 'benchmarking']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['local-ml-hosting', 'llm-evaluation-troubleshooting', 'mlops-suite']
---
---


# lm-evaluation-harness - LLM Benchmarking

## What's inside

Evaluates LLMs across 60+ academic benchmarks (MMLU, HumanEval, GSM8K, TruthfulQA, HellaSwag). Use when benchmarking model quality, comparing models, reporting academic results, or tracking training progress. Industry standard used by EleutherAI, HuggingFace, and major labs. Supports HuggingFace, vLLM, APIs.

## Quick start

lm-evaluation-harness evaluates LLMs across 60+ academic benchmarks using standardized prompts and metrics.

**⚠️ lm-eval ≥0.4 uses subcommands** — CLI syntax changed! Use `lm_eval run --model hf ...` not `lm_eval --model hf ...`. See [references/hermes-gpu-ml-setup.md](references/hermes-gpu-ml-setup.md) for Hermes PYTHONPATH isolation (critical on this host).

**Installation**:
```bash
# IMPORTANT: on this host, always unset PYTHONPATH first
# (Hermes PYTHONPATH bleeds into new venvs)
unset PYTHONPATH
uv venv .venv --python 3.12
PYTHONPATH="" uv pip install --python .venv/bin/python lm-eval
```

**Evaluate any HuggingFace model**:
```bash
# lm-eval 0.4+ uses subcommands (run, ls)
PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag \
  --device cuda:0 \
  --batch_size 8
```

**View available tasks**:
```bash
PYTHONPATH="" .venv/bin/lm_eval ls tasks
```

## Common workflows

### Workflow 1: Standard benchmark evaluation

Evaluate model on core benchmarks (MMLU, GSM8K, HumanEval).

Copy this checklist:

```

set -euo pipefail
Benchmark Evaluation:
- [ ] Step 1: Choose benchmark suite
- [ ] Step 2: Configure model
- [ ] Step 3: Run evaluation
- [ ] Step 4: Analyze results
```

**Step 1: Choose benchmark suite**

**Core reasoning benchmarks**:
- **MMLU** (Massive Multitask Language Understanding) - 57 subjects, multiple choice
- **GSM8K** - Grade school math word problems
- **HellaSwag** - Common sense reasoning
- **TruthfulQA** - Truthfulness and factuality
- **ARC** (AI2 Reasoning Challenge) - Science questions

**Code benchmarks**:
- **HumanEval** - Python code generation (164 problems)
- **MBPP** (Mostly Basic Python Problems) - Python coding

**Standard suite** (recommended for model releases):
```bash

set -euo pipefail
--tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge
```

**Step 2: Configure model**

**HuggingFace model**:
```bash
PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,dtype=bfloat16 \
  --tasks mmlu \
  --device cuda:0 \
  --batch_size auto  # Auto-detect optimal batch size
```

**Quantized model (4-bit/8-bit)**:
```bash
PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,load_in_4bit=True \
  --tasks mmlu \
  --device cuda:0
```

**Custom checkpoint**:
```bash
PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=/path/to/my-model,tokenizer=/path/to/tokenizer \
  --tasks mmlu \
  --device cuda:0
```

**Step 3: Run evaluation**

```bash
# Full MMLU evaluation (57 subjects)
PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --num_fewshot 5 \  # 5-shot evaluation (standard)
  --batch_size 8 \
  --output_path results/ \
  --log_samples  # Save individual predictions

# Multiple benchmarks at once
PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge \
  --num_fewshot 5 \
  --batch_size 8 \
  --output_path results/llama2-7b-eval.json
```

**Step 4: Analyze results**

Results saved to `results/llama2-7b-eval.json`:

```json
{
  "results": {
    "mmlu": {
      "acc": 0.459,
      "acc_stderr": 0.004
    },
    "gsm8k": {
      "exact_match": 0.142,
      "exact_match_stderr": 0.006
    },
    "hellaswag": {
      "acc_norm": 0.765,
      "acc_norm_stderr": 0.004
    }
  },
  "config": {
    "model": "hf",
    "model_args": "pretrained=meta-llama/Llama-2-7b-hf",
    "num_fewshot": 5
  }
}
```

set -euo pipefail
### Workflow 2: Track training progress

Evaluate checkpoints during training.

```
Training Progress Tracking:
- [ ] Step 1: Set up periodic evaluation
- [ ] Step 2: Choose quick benchmarks
- [ ] Step 3: Automate evaluation
- [ ] Step 4: Plot learning curves
```

set -euo pipefail
**Step 1: Set up periodic evaluation**

Evaluate every N training steps:

```bash
#!/bin/bash
# eval_checkpoint.sh

CHECKPOINT_DIR=$1
STEP=$2

PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=$CHECKPOINT_DIR/checkpoint-$STEP \
  --tasks gsm8k,hellaswag \
  --num_fewshot 0 \  # 0-shot for speed
  --batch_size 16 \
  --output_path results/step-$STEP.json
```

set -euo pipefail
**Step 2: Choose quick benchmarks**

Fast benchmarks for frequent evaluation:
- **HellaSwag**: ~10 minutes on 1 GPU
- **GSM8K**: ~5 minutes
- **PIQA**: ~2 minutes

Avoid for frequent eval (too slow):
- **MMLU**: ~2 hours (57 subjects)
- **HumanEval**: Requires code execution

**Step 3: Automate evaluation**

Integrate with training script:

```python
# In training loop
if step % eval_interval == 0:
    model.save_pretrained(f"checkpoints/step-{step}")

    # Run evaluation
    os.system(f"./eval_checkpoint.sh checkpoints step-{step}")
```

set -euo pipefail
Or use PyTorch Lightning callbacks:

```python
from pytorch_lightning import Callback

class EvalHarnessCallback(Callback):
    def on_validation_epoch_end(self, trainer, pl_module):
        step = trainer.global_step
        checkpoint_path = f"checkpoints/step-{step}"

        # Save checkpoint
        trainer.save_checkpoint(checkpoint_path)

        # Run lm-eval
        os.system(f"lm_eval --model hf --model_args pretrained={checkpoint_path} ...")
```

set -euo pipefail
**Step 4: Plot learning curves**

```python
import json
import matplotlib.pyplot as plt

# Load all results
steps = []
mmlu_scores = []

for file in sorted(glob.glob("results/step-*.json")):
    with open(file) as f:
        data = json.load(f)
        step = int(file.split("-")[1].split(".")[0])
        steps.append(step)
        mmlu_scores.append(data["results"]["mmlu"]["acc"])

# Plot
plt.plot(steps, mmlu_scores)
plt.xlabel("Training Step")
plt.ylabel("MMLU Accuracy")
plt.title("Training Progress")
plt.savefig("training_curve.png")
```

set -euo pipefail
### Workflow 3: Compare multiple models

Benchmark suite for model comparison.

```
Model Comparison:
- [ ] Step 1: Define model list
- [ ] Step 2: Run evaluations
- [ ] Step 3: Generate comparison table
```

set -euo pipefail
**Step 1: Define model list**

```bash
# models.txt
meta-llama/Llama-2-7b-hf
meta-llama/Llama-2-13b-hf
mistralai/Mistral-7B-v0.1
microsoft/phi-2
```

set -euo pipefail
**Step 2: Run evaluations**

```bash
#!/bin/bash
# eval_all_models.sh

TASKS="mmlu,gsm8k,hellaswag,truthfulqa"
VENV=".venv/bin"

while read model; do
    echo "Evaluating $model"
    model_name=$(echo $model | sed 's/\\//-/g')

    PYTHONPATH="" $VENV/lm_eval run --model hf \
      --model_args pretrained=$model,dtype=bfloat16 \
      --tasks $TASKS \
      --num_fewshot 5 \
      --batch_size auto \
      --output_path results/$model_name.json

done < models.txt
```

set -euo pipefail
**Step 3: Generate comparison table**

```python
import json
import pandas as pd

models = [
    "meta-llama-Llama-2-7b-hf",
    "meta-llama-Llama-2-13b-hf",
    "mistralai-Mistral-7B-v0.1",
    "microsoft-phi-2"
]

tasks = ["mmlu", "gsm8k", "hellaswag", "truthfulqa"]

results = []
for model in models:
    with open(f"results/{model}.json") as f:
        data = json.load(f)
        row = {"Model": model.replace("-", "/")}
        for task in tasks:
            # Get primary metric for each task
            metrics = data["results"][task]
            if "acc" in metrics:
                row[task.upper()] = f"{metrics['acc']:.3f}"
            elif "exact_match" in metrics:
                row[task.upper()] = f"{metrics['exact_match']:.3f}"
        results.append(row)

df = pd.DataFrame(results)
print(df.to_markdown(index=False))
```

set -euo pipefail
Output:
```
| Model                  | MMLU  | GSM8K | HELLASWAG | TRUTHFULQA |
|------------------------|-------|-------|-----------|------------|
| meta-llama/Llama-2-7b  | 0.459 | 0.142 | 0.765     | 0.391      |
| meta-llama/Llama-2-13b | 0.549 | 0.287 | 0.801     | 0.430      |
| mistralai/Mistral-7B   | 0.626 | 0.395 | 0.812     | 0.428      |
| microsoft/phi-2        | 0.560 | 0.613 | 0.682     | 0.447      |
```

set -euo pipefail
### Workflow 4: Evaluate with vLLM (faster inference)

Use vLLM backend for 5-10x faster evaluation.

```
vLLM Evaluation:
- [ ] Step 1: Install vLLM
- [ ] Step 2: Configure vLLM backend
- [ ] Step 3: Run evaluation
```

set -euo pipefail
**Step 1: Install vLLM**

```bash
pip install vllm
**Step 2: Configure vLLM backend**

```bash
PYTHONPATH="" .venv/bin/lm_eval run --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=1,dtype=auto,gpu_memory_utilization=0.8 \
  --tasks mmlu \
  --batch_size auto
```

**Step 3: Speed comparison**

vLLM is 5-10× faster than standard HuggingFace:

```bash
# Standard HF: ~2 hours for MMLU on 7B model
PYTHONPATH="" .venv/bin/lm_eval run --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --batch_size 8

# vLLM: ~15-20 minutes for MMLU on 7B model
PYTHONPATH="" .venv/bin/lm_eval run --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=2 \
  --tasks mmlu \
  --batch_size auto
```

set -euo pipefail
## When to use vs alternatives

**Use lm-evaluation-harness when:**
- Benchmarking models for academic papers
- Comparing model quality across standard tasks
- Tracking training progress
- Reporting standardized metrics (everyone uses same prompts)
- Need reproducible evaluation

**Use alternatives instead:**
- **HELM** (Stanford): Broader evaluation (fairness, efficiency, calibration)
- **AlpacaEval**: Instruction-following evaluation with LLM judges
- **MT-Bench**: Conversational multi-turn evaluation
- **Custom scripts**: Domain-specific evaluation

## Common issues

**Issue: Evaluation too slow**

Use vLLM backend:
```bash
lm_eval --model vllm \
  --model_args pretrained=model-name,tensor_parallel_size=2
```

set -euo pipefail
Or reduce fewshot examples:
```bash
--num_fewshot 0  # Instead of 5
```

set -euo pipefail
Or evaluate subset of MMLU:
```bash
--tasks mmlu_stem  # Only STEM subjects
```

set -euo pipefail
**Issue: Out of memory**

Reduce batch size:
```bash
--batch_size 1  # Or --batch_size auto
```

set -euo pipefail
Use quantization:
```bash
--model_args pretrained=model-name,load_in_8bit=True
```

set -euo pipefail
Enable CPU offloading:
```bash
--model_args pretrained=model-name,device_map=auto,offload_folder=offload
```

set -euo pipefail
**Issue: Different results than reported**

Check fewshot count:
```bash
--num_fewshot 5  # Most papers use 5-shot
```

set -euo pipefail
Check exact task name:
```bash
--tasks mmlu  # Not mmlu_direct or mmlu_fewshot
```

set -euo pipefail
Verify model and tokenizer match:
```bash
--model_args pretrained=model-name,tokenizer=same-model-name
```

set -euo pipefail
**Issue: HumanEval not executing code**

Install execution dependencies:
```bash
pip install human-eval
```

set -euo pipefail
Enable code execution:
```bash
lm_eval --model hf \
  --model_args pretrained=model-name \
  --tasks humaneval \
  --allow_code_execution  # Required for HumanEval
```

## Advanced topics

**Benchmark descriptions**: See [references/benchmark-guide.md](references/benchmark-guide.md) for detailed description of all 60+ tasks, what they measure, and interpretation.

**Custom tasks**: See [references/custom-tasks.md](references/custom-tasks.md) for creating domain-specific evaluation tasks.

**API evaluation**: See [references/api-evaluation.md](references/api-evaluation.md) for evaluating OpenAI, Anthropic, and other API models.

**Multi-GPU strategies**: See [references/distributed-eval.md](references/distributed-eval.md) for data parallel and tensor parallel evaluation.

## Hardware requirements

- **GPU**: NVIDIA (CUDA 11.8+), works on CPU (very slow)
- **VRAM**:
  - 7B model: 16GB (bf16) or 8GB (8-bit)
  - 13B model: 28GB (bf16) or 14GB (8-bit)
  - 70B model: Requires multi-GPU or quantization
- **Time** (7B model, single A100):
  - HellaSwag: 10 minutes
  - GSM8K: 5 minutes
  - MMLU (full): 2 hours
  - HumanEval: 20 minutes

## Resources

- GitHub: https://github.com/EleutherAI/lm-evaluation-harness
- Docs: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/docs
- Task library: 60+ tasks including MMLU, GSM8K, HumanEval, TruthfulQA, HellaSwag, ARC, WinoGrande, etc.
- Leaderboard: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard (uses this harness)
