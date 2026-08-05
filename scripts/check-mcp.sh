#!/usr/bin/env bash
# check-mcp.sh — Health-Check für alle in plugins/agent-toolkit/.mcp.json
# deklarierten MCP-Server.
#
# Pro Server wird geprüft:
#   1. ist der command (binary) überhaupt im PATH verfügbar?
#   2. sind alle referenzierten env-Vars gesetzt (non-empty)?
#
# Output: JSON-Array von Objekten {server, status, detail}.
# Exit-Code:
#   0 — alle Server "ok"
#   1 — mindestens ein Server "down"
#   2 — Skript-/Konfigurationsfehler (z. B. .mcp.json nicht lesbar)
#
# Nutzung:
#   ./scripts/check-mcp.sh
#   ./scripts/check-mcp.sh --pretty   # menschenlesbares JSON

set -euo pipefail

# --- Pfade & Argumente -------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MCP_CONFIG="${REPO_ROOT}/plugins/agent-toolkit/.mcp.json"

PRETTY=0
for arg in "$@"; do
    case "${arg}" in
        --pretty) PRETTY=1 ;;
        -h|--help)
            echo "Usage: $0 [--pretty]" >&2
            exit 0
            ;;
        *) echo "Unknown argument: ${arg}" >&2; exit 2 ;;
    esac
done

# --- Vorbedingungen prüfen ----------------------------------------------------
if [[ ! -f "${MCP_CONFIG}" ]]; then
    echo "MCP config nicht gefunden: ${MCP_CONFIG}" >&2
    exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "jq wird benötigt, ist aber nicht installiert." >&2
    exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 wird benötigt, ist aber nicht installiert." >&2
    exit 2
fi

# --- MCP-Server parsen --------------------------------------------------------
# jq liefert pro Server: name, command, args[], env{}. Wir bauen daraus
# eine flache Liste von Objekten {server, command, args, env_keys}.
mapfile -t SERVERS < <(jq -r '.mcpServers | keys[]' "${MCP_CONFIG}")

if [[ ${#SERVERS[@]} -eq 0 ]]; then
    echo "Keine MCP-Server in ${MCP_CONFIG} konfiguriert." >&2
    exit 2
fi

# --- Pro Server prüfen --------------------------------------------------------
results_json="["
first=1
# overall_ok = 0 (alles ok), wird auf 1 gesetzt sobald ein Server down ist.
overall_ok=0

for server in "${SERVERS[@]}"; do
    cmd="$(jq -r ".mcpServers[\"${server}\"].command // \"\"" "${MCP_CONFIG}")"
    # `.env // {}` ist nötig, weil `keys[]` auf null wirft — erst mit leerem
    # Objekt fallbacken, dann die Schlüssel auflisten.
    readarray -t env_keys < <(jq -r ".mcpServers[\"${server}\"].env // {} | keys[]" "${MCP_CONFIG}")

    detail_parts=()
    status="ok"

    # (1) command muss im PATH liegen
    if [[ -z "${cmd}" ]]; then
        status="down"
        detail_parts+=("command fehlt in .mcp.json")
    elif ! command -v "${cmd}" >/dev/null 2>&1; then
        status="down"
        detail_parts+=("binary '${cmd}' nicht im PATH")
    fi

    # (2) env-Vars müssen gesetzt sein
    missing_env=()
    for key in "${env_keys[@]}"; do
        # Wert '${VAR}' bedeutet: Var aus env, nicht aus .mcp.json lesen.
        if [[ -z "${!key:-}" ]]; then
            missing_env+=("${key}")
        fi
    done
    if [[ ${#missing_env[@]} -gt 0 ]]; then
        status="down"
        detail_parts+=("env nicht gesetzt: ${missing_env[*]}")
    fi

    if [[ "${status}" == "ok" ]]; then
        # (3) Smoke-Test: für uv-basierte Server, prüfe dass der Entry-Point
        # tatsächlich startbar ist (nicht nur dass uv im PATH liegt).
        # Dies fängt falsche Pfade, fehlende Installationen und kaputte Deps auf.
        if [[ "${cmd}" == "uv" ]] && [[ "${server}" == "basti-tools" ]]; then
            # PYTHONPATH leeren, da Hermes-Runtime einen System-Venv-Pfad setzt,
            # der den Projekt-Venv kapert (Known-Issue in Basti's Environment).
            if ! timeout 10 env -u PYTHONPATH uv run --directory "${REPO_ROOT}" python -c "from mcp_server_basti.server import mcp; print(mcp.name)" >/dev/null 2>&1; then
                status="down"
                detail_parts+=("smoke-test fehlgeschlagen: Server nicht startbar")
            fi
        fi
    fi

    if [[ "${status}" == "ok" ]]; then
        detail="command '${cmd}' verfügbar; alle env-Vars gesetzt; smoke-test ok"
    else
        detail=$(IFS='; '; echo "${detail_parts[*]}")
    fi

    if [[ ${first} -eq 0 ]]; then
        results_json+=","
    fi
    # jq für sauberes Escaping der Detail-Strings
    results_json+="$(jq -nc \
        --arg server "${server}" \
        --arg status "${status}" \
        --arg detail "${detail}" \
        '{server:$server, status:$status, detail:$detail}')"
    first=0

# `overall_ok` wird auf 1 gesetzt, sobald ein Server down ist (Status != "ok").
[[ "${status}" == "ok" ]] || overall_ok=1
done

results_json+="]"

# --- Output -------------------------------------------------------------------
if [[ ${PRETTY} -eq 1 ]]; then
    echo "${results_json}" | jq .
else
    echo "${results_json}"
fi

exit "${overall_ok}"
