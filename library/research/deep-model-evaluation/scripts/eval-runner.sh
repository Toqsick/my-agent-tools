#!/bin/bash
# eval-runner.sh — Sequential model-vs-model eval runner
# Part of the deep-model-evaluation skill
#
# Usage:
#   ./eval-runner.sh [-p PROFILE] [-m "MODEL_A,MODEL_B..."] [-t TASKS_DIR] [-c COST_CAP]
#
# Runs every task through every model sequentially (each task → all models,
# then next task), isolating output per model+task pair.
#
# Example:
#   ./eval-runner.sh \
#     -p yuno-coder \
#     -m "minimax/MiniMax-M3,openrouter/moonshotai/kimi-k3" \
#     -t ./tasks \
#     -c 5.00
#
# Design: sequential per model (parallel risks rate limits + cost spikes).
# Each task runs through ALL models before moving to next task.

set -euo pipefail

PROFILE="yuno-coder"
MODELS=""
TASKS_DIR="./tasks"
COST_CAP=""        # $ dollar cap for premium models — script logs warning, doesn't enforce
DRY_RUN=false

usage() {
    echo "Usage: $0 [-p PROFILE] [-m MODEL_A,MODEL_B,...] [-t TASKS_DIR] [-c COST_CAP] [-n]"
    echo "  -p PROFILE   Hermes profile to use (default: yuno-coder)"
    echo "  -m MODELS    Comma-separated model specs (e.g. minimax/MiniMax-M3,openrouter/...)"
    echo "  -t DIR       Task specs directory (default: ./tasks)"
    echo "  -c DOLLARS   Optional cost cap for premium models"
    echo "  -n           Dry-run (show what would run without executing)"
    exit 1
}

while getopts "p:m:t:c:nh" opt; do
    case $opt in
        p) PROFILE="$OPTARG" ;;
        m) MODELS="$OPTARG" ;;
        t) TASKS_DIR="$OPTARG" ;;
        c) COST_CAP="$OPTARG" ;;
        n) DRY_RUN=true ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [ -z "$MODELS" ]; then
    echo "❌ Must specify at least one model with -m"
    usage
fi

# Parse model list
IFS=',' read -ra MODEL_LIST <<< "$MODELS"

# Count tasks
TASK_FILES=($(ls "$TASKS_DIR"/task-*.md 2>/dev/null || true))
TASK_COUNT=${#TASK_FILES[@]}
MODEL_COUNT=${#MODEL_LIST[@]}

if [ $TASK_COUNT -eq 0 ]; then
    echo "❌ No task-*.md files found in $TASKS_DIR"
    exit 1
fi

# Create output directories
mkdir -p runs

echo "━━━ Eval Runner — ${MODEL_COUNT} model(s) × ${TASK_COUNT} task(s) ━━━"
echo "  Profile:   ${PROFILE}"
echo "  Models:    ${MODELS}"
[ -n "$COST_CAP" ] && echo "  Cost cap:  \$${COST_CAP}"
echo ""

for task_file in "${TASK_FILES[@]}"; do
    task_name=$(basename "$task_file" .md)
    task_text=$(cat "$task_file")

    echo "┌─ Task: ${task_name}"

    for model_spec in "${MODEL_LIST[@]}"; do
        # Parse provider/model
        provider="${model_spec%%/*}"
        model="${model_spec#*/}"

        # Safe directory name
        model_safe=$(echo "$model_spec" | sed 's|/|_|g')

        # Output dir
        outdir="runs/${model_safe}/${task_name}"
        mkdir -p "$outdir"

        echo "│  ├─ ${model_spec}"
        echo "│  │  → ${outdir}/output.md"

        # Check: if output already exists and content has actual output, skip
        if [ -f "${outdir}/output.md" ] && [ -s "${outdir}/output.md" ]; then
            # Check if it's more than just a stub
            line_count=$(wc -l < "${outdir}/output.md" 2>/dev/null || echo 0)
            if [ "$line_count" -gt 5 ]; then
                echo "│  │  ⏩ cached (${line_count} lines) — delete to re-run"
                continue
            fi
        fi

        # Run
        if [ "$DRY_RUN" = true ]; then
            echo "│  │  ⚡ (dry-run) hermes -p $PROFILE -m $model --provider $provider ..."
        else
            # Sequential run — captures to output.md
            hermes -p "$PROFILE" \
                -m "$model" \
                --provider "$provider" \
                -z "$task_text" \
                --yolo --no-restore-cwd \
                2>&1 | tee "${outdir}/output.md" || true

            # Extract cost info from stderr (hermes logs cost to stderr)
            # Cost line pattern varies by provider; capture any line with $
            if [ -f "${outdir}/output.md" ]; then
                grep -i '\$[0-9]\|token\|cost' "${outdir}/output.md" | head -5 > "${outdir}/cost.log" 2>/dev/null || true
            fi
        fi
    done

    echo "└─ Done: ${task_name}"
    echo ""
done

echo "━━━ Summary ━━━"
echo "  Total: ${MODEL_COUNT} model(s) × ${TASK_COUNT} task(s) = $((MODEL_COUNT * TASK_COUNT)) runs"
echo "  Outputs: $(pwd)/runs/"
echo ""

# Run acceptance check on Task 01 if present
for model_spec in "${MODEL_LIST[@]}"; do
    model_safe=$(echo "$model_spec" | sed 's|/|_|g')
    outdir="runs/${model_safe}"

    # Try to verify Task 01 output (GreyScript modular split)
    for task_dir in "$outdir"/task-01*; do
        [ -d "$task_dir" ] || continue
        echo "📋 Verifying Task 01 for ${model_spec}:"
        if [ -f "${task_dir}/output.md" ]; then
            lines=$(wc -l < "${task_dir}/output.md")
            echo "  Output file: ${lines} lines"
            # Check for source files if they were written to workdir
            grep -c "nscan_core.src" "${task_dir}/output.md" 2>/dev/null && echo "  ✅ nscan_core.src referenced"
            grep -c "router_helper.src" "${task_dir}/output.md" 2>/dev/null && echo "  ✅ router_helper.src referenced"
            grep -c "service_info.src" "${task_dir}/output.md" 2>/dev/null && echo "  ✅ service_info.src referenced"
        else
            echo "  ❌ No output.md found"
        fi
        echo ""
    done
done
