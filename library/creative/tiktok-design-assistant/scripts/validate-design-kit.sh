#!/bin/bash
# Backward-compat wrapper: delegates to Python validator
exec python3 "$(dirname "$0")/validate-design-kit.py" "$@"
