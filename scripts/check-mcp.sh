#!/bin/bash
# =============================================================
# MCP Server Health Check
# Toqsick/my-agent-tools
#
# Usage:
#   chmod +x scripts/check-mcp.sh
#   ./scripts/check-mcp.sh
#
# Optional: source your .env first
#   set -a && source .env && set +a && ./scripts/check-mcp.sh
# =============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

ok()   { echo -e "  ${GREEN}✅ $1${NC}";  ((PASS++)); }
fail() { echo -e "  ${RED}❌ $1${NC}";   ((FAIL++)); }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; ((WARN++)); }
info() { echo -e "  ${BLUE}ℹ️  $1${NC}"; }

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     MCP Server Health Check              ║${NC}"
echo -e "${BOLD}║     Toqsick/my-agent-tools               ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

# -------------------------------------------------------------
echo -e "${BOLD}── 1. Runtime Dependencies ─────────────────${NC}"
# -------------------------------------------------------------

# Docker
if docker info > /dev/null 2>&1; then
  DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
  ok "Docker running ($DOCKER_VER)"
else
  fail "Docker not running — required for 'github' MCP server"
  info "Install: https://docs.docker.com/get-docker/"
fi

# Node / npx
if command -v npx > /dev/null 2>&1; then
  NODE_VER=$(node -v 2>/dev/null || echo 'unknown')
  NPX_VER=$(npx --version 2>/dev/null || echo 'unknown')
  if [[ "$NODE_VER" =~ ^v([0-9]+) ]] && [ "${BASH_REMATCH[1]}" -ge 18 ]; then
    ok "Node.js $NODE_VER + npx $NPX_VER"
  else
    warn "Node.js $NODE_VER detected — recommend Node 18+ for all MCP servers"
  fi
else
  fail "Node.js / npx not found — required for 7 MCP servers"
  info "Install: https://nodejs.org"
fi
echo ""

# -------------------------------------------------------------
echo -e "${BOLD}── 2. Environment Variables ─────────────────${NC}"
# -------------------------------------------------------------

check_var() {
  local VAR_NAME="$1"
  local SERVER="$2"
  local OPTIONAL="${3:-false}"
  local VAL="${!VAR_NAME}"
  if [ -n "$VAL" ]; then
    # Show only first 8 chars + masked
    PREVIEW="${VAL:0:8}..."
    ok "$VAR_NAME set ($PREVIEW) [$SERVER]"
  else
    if [ "$OPTIONAL" = "true" ]; then
      warn "$VAR_NAME not set (optional, default used) [$SERVER]"
    else
      fail "$VAR_NAME missing [$SERVER]"
    fi
  fi
}

# GitHub
check_var "GITHUB_PERSONAL_ACCESS_TOKEN" "github"

# Gmail
check_var "GMAIL_OAUTH_CLIENT_ID"     "gmail"
check_var "GMAIL_OAUTH_CLIENT_SECRET" "gmail"
check_var "GMAIL_OAUTH_REFRESH_TOKEN" "gmail"

# Google Calendar
check_var "GOOGLE_CLIENT_ID"     "google-calendar"
check_var "GOOGLE_CLIENT_SECRET" "google-calendar"
check_var "GOOGLE_REFRESH_TOKEN" "google-calendar"

# Brave Search
check_var "BRAVE_API_KEY" "brave-search"

# Optional
check_var "WORKSPACE_PATH"    "filesystem"        "true"
check_var "MEMORY_FILE_PATH"  "memory"            "true"
echo ""

# -------------------------------------------------------------
echo -e "${BOLD}── 3. MCP Package Availability ─────────────${NC}"
# -------------------------------------------------------------

check_npx_pkg() {
  local PKG="$1"
  local SERVER="$2"
  # Dry-run: check if package resolves without installing
  if npx --yes --quiet "$PKG" --version > /dev/null 2>&1 || \
     npm view "$PKG" version > /dev/null 2>&1; then
    LATEST=$(npm view "$PKG" version 2>/dev/null || echo 'unknown')
    ok "$PKG@$LATEST [$SERVER]"
  else
    warn "$PKG — not yet cached (will auto-install on first use) [$SERVER]"
  fi
}

check_npx_pkg "@gongrzhe/server-gmail-autoauth-mcp"         "gmail"
check_npx_pkg "@cocal/google-calendar-mcp"                  "google-calendar"
check_npx_pkg "@modelcontextprotocol/server-filesystem"     "filesystem"
check_npx_pkg "@modelcontextprotocol/server-brave-search"   "brave-search"
check_npx_pkg "@modelcontextprotocol/server-memory"         "memory"
check_npx_pkg "@modelcontextprotocol/server-puppeteer"      "puppeteer"
check_npx_pkg "@modelcontextprotocol/server-sequential-thinking" "sequential-thinking"
echo ""

# -------------------------------------------------------------
echo -e "${BOLD}── 4. Docker Image ──────────────────────────${NC}"
# -------------------------------------------------------------

if docker info > /dev/null 2>&1; then
  if docker image inspect toqsick/github-mcp-server:develop > /dev/null 2>&1; then
    ok "toqsick/github-mcp-server:develop image cached locally [github]"
  else
    warn "toqsick/github-mcp-server:develop not cached — will pull on first use [github]"
    info "Pre-pull: docker pull toqsick/github-mcp-server:develop"
  fi
else
  fail "Cannot check Docker image — Docker not running"
fi
echo ""

# -------------------------------------------------------------
echo -e "${BOLD}── 5. Config Files ──────────────────────────${NC}"
# -------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
MCP_JSON="$REPO_ROOT/plugins/agent-toolkit/.mcp.json"
ENV_EXAMPLE="$REPO_ROOT/.env.example"

if [ -f "$MCP_JSON" ]; then
  SERVER_COUNT=$(grep -c '"command"' "$MCP_JSON" 2>/dev/null || echo 0)
  ok ".mcp.json found ($SERVER_COUNT servers declared)"
else
  fail ".mcp.json not found at $MCP_JSON"
fi

if [ -f "$ENV_EXAMPLE" ]; then
  ok ".env.example present"
else
  warn ".env.example not found — run: git pull"
fi

if [ -f "$REPO_ROOT/.env" ]; then
  ok ".env file exists locally"
else
  warn ".env file missing — copy: cp .env.example .env"
fi
echo ""

# -------------------------------------------------------------
echo -e "${BOLD}── Summary ──────────────────────────────────${NC}"
# -------------------------------------------------------------

TOTAL=$((PASS + FAIL + WARN))
echo -e "  Checks: $TOTAL  |  ${GREEN}✅ $PASS passed${NC}  |  ${RED}❌ $FAIL failed${NC}  |  ${YELLOW}⚠️  $WARN warnings${NC}"
echo ""

if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
  echo -e "  ${GREEN}${BOLD}🎉 All systems go — all 8 MCP servers should start cleanly.${NC}"
elif [ "$FAIL" -eq 0 ]; then
  echo -e "  ${YELLOW}${BOLD}⚠️  Core checks passed but some warnings need attention.${NC}"
  echo -e "  ${YELLOW}Optional servers with missing tokens will be skipped by the MCP client.${NC}"
else
  echo -e "  ${RED}${BOLD}❌ $FAIL critical issue(s) found. Fix before starting Claude Desktop.${NC}"
  echo ""
  echo -e "  ${BOLD}Quick fix guide:${NC}"
  echo -e "  1. Missing env vars  → cp .env.example .env  then fill in values"
  echo -e "  2. Docker not running → open Docker Desktop"
  echo -e "  3. Node.js missing   → brew install node  (macOS)"
  echo -e "  4. Gmail tokens      → npx @gongrzhe/server-gmail-autoauth-mcp auth"
fi
echo ""
