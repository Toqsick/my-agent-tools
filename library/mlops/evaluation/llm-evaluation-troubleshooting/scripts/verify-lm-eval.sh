#!/usr/bin/env bash
# Quick verification script for lm-eval-harness installation
# Run: bash scripts/verify-lm-eval.sh

set -euo pipefail

echo "=== lm-eval-harness Installation Verification ==="
echo ""

# Check Python version
echo "Python version:"
python3 --version
echo ""

# Check lm-eval version
echo "lm-eval version:"
lm-eval --version 2>/dev/null || echo "lm-eval not in PATH, trying python -m..."
python3 -m lm_eval --version 2>/dev/null || echo "  Not found"
echo ""

# Check key dependencies
echo "Key dependencies:"
for pkg in torch transformers accelerate tenacity datasets evaluate; do
    python3 -c "import $pkg; print(f'  $pkg: OK')" 2>/dev/null || echo "  $pkg: MISSING"
done
echo ""

# Test task listing (verifies TypedDict fix)
echo "Testing task listing (verifies Python 3.12 compat)..."
if lm-eval ls tasks >/dev/null 2>&1; then
    echo "  Task listing: OK"
else
    echo "  Task listing: FAILED"
    echo "  Run: lm-eval ls tasks 2>&1 | head -20"
fi
echo ""

# Quick GPT-2 test (if HF backend works)
echo "Quick GPT-2 GSM8K test (limit=5)..."
if timeout 120 lm-eval run \
    --model hf \
    --model_args pretrained=gpt2,dtype=float \
    --tasks gsm8k \
    --limit 5 \
    --batch_size 1 \
    2>&1 | tail -20; then
    echo "  GPT-2 test: OK"
else
    echo "  GPT-2 test: FAILED or TIMEOUT"
fi
echo ""

echo "=== Verification Complete ==="
echo ""
echo "If all checks pass, you're ready to run evaluations."
echo "For Ollama/local models, see: skill_view(name='llm-evaluation-troubleshooting', file_path='references/ollama-integration.md')"