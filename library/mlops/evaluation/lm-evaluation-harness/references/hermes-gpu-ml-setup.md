# Hermes GPU ML Setup — PYTHONPATH Isolation & RTX 5060 (sm_120 Blackwell)

## The Problem

When installing GPU ML tooling (lm-eval, vLLM, PyTorch) alongside Hermes Agent:

1. **PYTHONPATH contamination**: Hermes injects `PYTHONPATH=/home/bratan/.hermes/hermes-agent/venv/lib/python3.11/site-packages`. Every `pip install` in a new venv sees Hermes' packages (numpy ABI mismatches).
2. **RTX 5060 (sm_120 Blackwell)**: Requires CUDA 13.0+ (cu130) — PyTorch 2.5.1+cu121 does NOT support sm_120. Minimum: PyTorch 2.13.0+cu130.
3. **7.5 GB VRAM**: 7B models only in 4-bit/8-bit quantization.

## The Fix (3-Step Pattern)

### Step 1: PYTHONPATH=""
```bash
# ❌ pulls Hermes python3.11
lm_eval run --model hf --model_args pretrained=gpt2 --tasks hellaswag
# ✅ isolated
PYTHONPATH="" .venv/bin/lm_eval run --model hf ...
```

Wrapper script: unset PYTHONPATH + PYTHONHOME before exec.

### Step 2: Isolated venv with system Python
```bash
uv venv .venv --python 3.12
PYTHONPATH="" uv pip install --python .venv/bin/python \
  torch --index-url https://download.pytorch.org/whl/cu130
```

### Step 3: Manual CUDA 13.0 runtime packages
PyTorch cu130 auto-resolve fails (large downloads timeout):
```bash
PYTHONPATH="" uv pip install --python .venv/bin/python \
  --index-url https://pypi.nvidia.com \
  nvidia-cusparselt-cu13==0.9.1 \
  nvidia-nvshmem-cu13==3.7.1 \
  nvidia-nccl-cu13==2.30.7 \
  nvidia-cuda-cccl==13.3.3.4.1
```

## Missing Symbols Guide
| Symbol | Package |
|--------|---------|
| `libcusparseLt.so.0` | `nvidia-cusparselt-cu13` |
| `libnvshmem_host.so.3` | `nvidia-nvshmem-cu13` |
| `ncclCommResume` | `nvidia-nccl-cu13` |
| `CUCCcl@Base` | `nvidia-cuda-cccl` |

## Known Good Stack (RTX 5060, 2026-07-16)
- Python 3.12.3, PyTorch 2.13.0+cu130, lm-eval 0.4.12
- NCCL 2.30.7, cuSPARSELt 0.9.1 (all cu13)

## VRAM Budget (8 GB)
| Size | bf16 | 8-bit | 4-bit |
|------|:----:|:-----:|:-----:|
| 7B | ❌ | ⚠️ | ✅ |
| 13B | ❌ | ❌ | ⚠️ |

## Verification
```bash
PYTHONPATH="" .venv/bin/python -c "
import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))
"
```
