#!/usr/bin/env bash
# hermes-min-context-patch.sh
#
# Idempotent restore of MINIMUM_CONTEXT_LENGTH in agent/model_metadata.py.
# Hermes hardcodes this at 64_000 to enforce a "minimum viable context" for
# tool-calling workflows, but local 9B/14B models on 8-12GB VRAM cannot
# physically run 64k context. `hermes update` re-pulls source from git and
# overwrites the patched line, so this script + a cron (e.g. every 6h) is
# needed to keep the override persistent.
#
# Idempotent: exit 0 if already applied, exit 2 if the line is missing or
# has an unexpected value (so the cron delivers the failure alert instead
# of silently doing nothing).
#
# Adjust MINIMUM_CONTEXT_LENGTH_TARGET for your model:
#   9B on 8GB  → 16000
#   14B on 12GB → 24000
#   70B on 24GB+ → 64000 (no patch needed)

set -e

FILE="${HERMES_METADATA_FILE:-$HOME/.hermes/hermes-agent/agent/model_metadata.py}"
TARGET="${MINIMUM_CONTEXT_LENGTH_TARGET:-16000}"
BACKUP="${HERMES_METADATA_BACKUP:-$HOME/docs/system/hermes-minimum-context-backup.py}"

# 1. File present?
if [[ ! -f "$FILE" ]]; then
    echo "X  $FILE not found - Hermes not installed at default path?" >&2
    exit 2
fi

# 2. Already patched?
if grep -qE "^MINIMUM_CONTEXT_LENGTH = ${TARGET}\b" "$FILE"; then
    echo "OK Patch already active (MINIMUM_CONTEXT_LENGTH = ${TARGET})"
    exit 0
fi

# 3. Known upstream value? Patch it.
if grep -qE "^MINIMUM_CONTEXT_LENGTH = [0-9]+$" "$FILE"; then
    # Backup if not done already
    if [[ ! -f "$BACKUP" ]]; then
        cp "$FILE" "$BACKUP"
        echo "OK Pre-patch backup written to $BACKUP"
    fi
    sed -i -E "s/^(MINIMUM_CONTEXT_LENGTH = )[0-9]+$/\1${TARGET}/" "$FILE"

    # Also add the explanation comment if not present
    if ! grep -q "BASTI-OVERRIDE\|LOCAL-MODEL-OVERRIDE" "$FILE"; then
        sed -i "/^MINIMUM_CONTEXT_LENGTH = ${TARGET}$/a\\
\\
# LOCAL-MODEL-OVERRIDE: lowered from upstream 64_000 to ${TARGET} for local\\
# model on consumer GPU. ${TARGET} is the largest context that fits in the\\
# available VRAM (see VRAM math in hermes-maintenance skill ->\\
# references/local-llm-ollama-primary.md).\\
# Restore-script: ${BASH_SOURCE[0]}\\
# Cron: hermes-patch-restore (every 6h, no-agent, telegram on failure)" "$FILE"
    fi
    echo "OK Patch applied: MINIMUM_CONTEXT_LENGTH = ${TARGET} (was 64_000)"
    echo "  Re-run hermes to pick up the new value."
    exit 0
fi

# 4. Unexpected state - don't silently no-op
echo "WARN  MINIMUM_CONTEXT_LENGTH line not found in $FILE in expected form." >&2
echo "   Current state:" >&2
grep -n "MINIMUM_CONTEXT_LENGTH" "$FILE" | head -3 >&2
echo "   Manual review needed." >&2
exit 2
