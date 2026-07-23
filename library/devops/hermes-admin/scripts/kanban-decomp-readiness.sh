#!/bin/bash
# kanban-decomp-readiness.sh
# Prüft alle Voraussetzungen für Auto-Decompose produktiv.
# Nutzung: bash kanban-decomp-readiness.sh
#
# Verifiziert:
# 1. Config-Flags (orchestrator_profile, default_assignee, auto_decompose, auto_subscribe_on_create)
# 2. notification_sources als YAML-List (nicht String — Pitfall #14)
# 3. Auxiliary-Models explizit gesetzt (Pitfall #15)
# 4. Alle Profile haben Descriptions (Pitfall #3)

set -e

echo "═══ Auto-Decompose Readiness ═══"
echo

# 1. Config-Flags
echo "─── Config-Flags ───"
for k in orchestrator_profile default_assignee auto_decompose auto_subscribe_on_create; do
  v=$(grep -E "^\s*${k}:" ~/.hermes/config.yaml | head -1 | awk -F': ' '{print $2}' | tr -d "'\"")
  if [ -z "$v" ]; then
    echo "  ❌ $k: NICHT GESETZT"
  else
    echo "  ✅ $k: $v"
  fi
done

# 2. notification_sources Format
echo
echo "─── notification_sources Format ───"
ns=$(grep "notification_sources:" ~/.hermes/config.yaml | awk -F': ' '{print $2}')
if echo "$ns" | grep -q "^'\["; then
  echo "  ⚠️  notification_sources ist STRING, nicht Liste → Pitfall #14 Workaround nötig"
  echo "       aktueller Wert: $ns"
elif echo "$ns" | grep -q "^\["; then
  echo "  ✅ notification_sources ist YAML-Liste: $ns"
else
  echo "  ❌ notification_sources nicht gesetzt"
fi

# 3. Auxiliary-Models explizit?
echo
echo "─── Auxiliary-Models ───"
for k in kanban_decomposer profile_describer; do
  block=$(grep -A 3 "${k}:" ~/.hermes/config.yaml | head -4)
  model=$(echo "$block" | grep "model:" | head -1 | awk -F': ' '{print $2}' | tr -d "'\"")
  provider=$(echo "$block" | grep "provider:" | head -1 | awk -F': ' '{print $2}' | tr -d "'\"")
  if [ -z "$model" ] || [ "$model" = "" ]; then
    echo "  ⚠️  $k: model='' (Default, nicht deterministisch)"
  else
    echo "  ✅ $k: provider=$provider model=$model"
  fi
done

# 4. Profile-Descriptions
echo
echo "─── Profile-Descriptions ───"
for p in default yuno yuno-coder yuno-vision yuno-flash local-9b; do
  desc=$(hermes profile describe "$p" 2>&1 | head -1)
  if echo "$desc" | grep -q "no description"; then
    echo "  ❌ $p: KEINE Description"
  else
    echo "  ✅ $p: ${desc:0:60}..."
  fi
done

echo
echo "═══ Done ═══"