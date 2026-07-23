---
name: mlops-suite
description: >-
  Use when user asks for choosing an MLOps tool for a task, comparing vLLM with llama.cpp, finding workflows for Hub, experiment tracking, audio, segmentation, or evaluation, or routing a broad ML operations request. NOT for deep troubleshooting of one tool or non-ML productivity automation. Acts as a compact gateway to model serving, local inference, Hub operations, W&B, AudioCraft, SAM, and evaluation references.
version: 1.0.0
author: Hermes Agent (curator consolidation)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - mlops
    - vllm
    - llama-cpp
    - huggingface
    - wandb
    - audiocraft
    - sam
    - evaluation
lane: worker-heavy
reasoning_effort: xhigh
agent: Analyst
routing_hint: '**Agent-Scope:** Data, ML, modeling, statistics, training, evaluation.
  Off-scope: visual design, code writing, copy — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['tool', 'hub', 'evaluation', 'operations', 'mlops-suite']
keywords: ['tool', 'evaluation', 'operations', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['productivity-suite', 'huggingface-hub', 'evaluating-llms-harness']
---

---


# MLOps Suite

Covers: model serving, local inference, model hub, experiment tracking, audio/image generation.

## Model Serving (vLLM)
```bash

set -euo pipefail
# High-throughput LLM serving with OpenAI API
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B --dtype auto
```

## Local Inference (llama.cpp / GGUF)
```bash

set -euo pipefail
# GGUF inference
llama-cli -m model.gguf -p "Hello" -n 128
```

## HuggingFace Hub
```bash

set -euo pipefail
hf search "llama"
hf download meta-llama/Llama-3.1-8B
hf upload ./my-model
```

## Experiment Tracking (Weights & Biases)
```python
import wandb
wandb.init(project="my-project")
wandb.log({"loss": 0.5})
```

set -euo pipefail
## Audio Generation (AudioCraft / MusicGen)
```python
# Text-to-music, text-to-sound
# See references/audiocraft.md
```

set -euo pipefail
## Image Segmentation (SAM)
```python
# Zero-shot segmentation via points, boxes, masks
# See references/sam.md
```

## LLM Evaluation
See `local-ml-hosting` skill for lm-eval-harness details.
