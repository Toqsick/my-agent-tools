#!/usr/bin/env bash
# api-discovery.sh — Quick-Probe einer REST/HTTP-API auf aktuelle Endpoints und Auth-Mode.
# Usage: ./api-discovery.sh <host> <base_path> [token_env_var_name]
#
# Beispiel: ./api-discovery.sh api.todoist.com /api/v1 TODOIST_API_TOKEN
# Beispiel: ./api-discovery.sh api.notion.com /v1 NOTION_API_TOKEN

set -euo pipefail

HOST="${1:?host required (e.g. api.todoist.com)}"
BASE_PATH="${2:-/api/v1}"
TOKEN_VAR="${3:-API_TOKEN}"

# Source .env falls vorhanden
if [[ -f ~/.hermes/.env ]]; then
    set -a
    # shellcheck disable=SC1090
    source ~/.hermes/.env
    set +a
fi

TOKEN="${!TOKEN_VAR:-}"
if [[ -z "$TOKEN" ]]; then
    echo "ERROR: $TOKEN_VAR env var not set. Set in ~/.hermes/.env or export inline."
    exit 1
fi

echo "=== API Discovery: https://${HOST}${BASE_PATH} ==="
echo "Token: ${TOKEN:0:8}..."
echo

# Test 1: Basic connectivity (HEAD /)
echo "--- Test 1: Basic Connectivity (HEAD /) ---"
curl -sI "https://${HOST}/" | head -3

# Test 2: Common list endpoint (GET /projects or /me)
echo
echo "--- Test 2: GET ${BASE_PATH}/projects ---"
HTTP_CODE=$(curl -s -o /tmp/api-discovery-body.json -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "User-Agent: hermes-v7.2-api-discovery/1.0" \
    "https://${HOST}${BASE_PATH}/projects")
echo "HTTP $HTTP_CODE"
echo "Body (first 500 chars):"
head -c 500 /tmp/api-discovery-body.json
echo

# Test 3: Pagination pattern detection
echo
echo "--- Test 3: Pagination Pattern ---"
if command -v jq >/dev/null 2>&1; then
    RESULTS_TYPE=$(jq -r 'if (.results|type) == "array" then "paginated_wrapper" elif (.data|type) == "array" then "data_wrapper" elif (.|type) == "array" then "direct_array" elif (.items|type) == "array" then "items_wrapper" else "unknown" end' /tmp/api-discovery-body.json 2>/dev/null || echo "jq_failed")
    echo "Detected pattern: $RESULTS_TYPE"
    echo "Sample unwrap: response.results OR response.data OR response.items OR response"
else
    echo "jq not installed — install with: sudo apt install jq"
fi

# Test 4: Auth failure modes
echo
echo "--- Test 4: Auth Failure Mode (no token) ---"
NO_AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://${HOST}${BASE_PATH}/projects")
echo "HTTP $NO_AUTH_CODE (401 = needs auth, 200 = public endpoint)"

# Summary
echo
echo "=== Summary ==="
echo "Host:           $HOST"
echo "Base path:      $BASE_PATH"
echo "Auth endpoint:  HTTP $HTTP_CODE with token, HTTP $NO_AUTH_CODE without"
echo "Response body:  $(wc -c < /tmp/api-discovery-body.json) bytes"

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "✓ Endpoint reachable + authenticated"
elif [[ "$HTTP_CODE" == "401" ]]; then
    echo "✗ Token invalid or missing scopes"
elif [[ "$HTTP_CODE" == "410" ]]; then
    echo "⚠ Endpoint deprecated — try legacy path or check API docs"
elif [[ "$HTTP_CODE" == "404" ]]; then
    echo "✗ Endpoint not found — check base_path"
else
    echo "? Unexpected status — see body above"
fi