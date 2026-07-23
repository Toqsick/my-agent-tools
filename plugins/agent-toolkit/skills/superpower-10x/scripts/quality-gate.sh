#!/usr/bin/env bash
#===============================================================================
# quality-gate.sh - Comprehensive quality enforcement pipeline
# Part of Superpower-10x framework
#===============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
QUALITY_SCORE=100
MIN_COVERAGE=80
MAX_COMPLEXITY=10
MAX_WARNINGS=0

# Track results
declare -a PASSED_GATES=()
declare -a FAILED_GATES=()
declare -a WARNED_GATES=()

#-------------------------------------------------------------------------------
# Logging
#-------------------------------------------------------------------------------

print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}           SUPERPOWER-10X QUALITY GATE CHECK                  ${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_gate() { echo -e "${BLUE}[GATE]${NC} $1"; }
log_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    PASSED_GATES+=("$1")
}
log_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    FAILED_GATES+=("$1")
    ((QUALITY_SCORE-=10))
}
log_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    WARNED_GATES+=("$1")
    ((QUALITY_SCORE-=5))
}
log_info() { echo -e "${BLUE}ℹ INFO${NC}: $1"; }

print_summary() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}                    QUALITY SUMMARY                              ${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    echo -e "Gates Passed: ${GREEN}${#PASSED_GATES[@]}${NC}"
    echo -e "Gates Failed: ${RED}${#FAILED_GATES[@]}${NC}"
    echo -e "Warnings:     ${YELLOW}${#WARNED_GATES[@]}${NC}"
    echo ""

    echo -e "Quality Score: ${BOLD}${QUALITY_SCORE}/100${NC}"
    echo ""

    if [ ${#FAILED_GATES[@]} -gt 0 ]; then
        echo -e "${RED}Failed Gates:${NC}"
        for gate in "${FAILED_GATES[@]}"; do
            echo -e "  • $gate"
        done
        echo ""
    fi

    if [ ${#WARNED_GATES[@]} -gt 0 ]; then
        echo -e "${YELLOW}Warnings:${NC}"
        for gate in "${WARNED_GATES[@]}"; do
            echo -e "  • $gate"
        done
        echo ""
    fi

    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"

    if [ "$QUALITY_SCORE" -ge 80 ]; then
        echo -e "${GREEN}${BOLD}✓ QUALITY GATE: PASSED${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}${BOLD}✗ QUALITY GATE: FAILED${NC}"
        echo ""
        return 1
    fi
}

#-------------------------------------------------------------------------------
# Gate 1: Test Coverage
#-------------------------------------------------------------------------------

gate_test_coverage() {
    print_gate "Test Coverage"

    local min=${1:-$MIN_COVERAGE}

    if ! command -v jest &> /dev/null && ! command -v pytest &> /dev/null && ! command -v go test &> /dev/null; then
        log_warn "No test coverage tool detected, skipping"
        return 0
    fi

    local coverage=0
    local output=""

    if command -v jest &> /dev/null; then
        output=$(npx jest --coverage --coverageReporters=text 2>&1 || true)
        coverage=$(echo "$output" | grep -oP 'All files[^%]*\K\d+' | tail -1 || echo "0")
    elif command -v pytest &> /dev/null; then
        output=$(pytest --cov=. --cov-report=term 2>&1 || true)
        coverage=$(echo "$output" | grep -oP 'TOTAL\s+\d+\s+\d+\s+\K\d+' | tail -1 || echo "0")
    elif command -v go test &> /dev/null; then
        output=$(go test -coverprofile=coverage.out ./... 2>&1 || true)
        coverage=$(go tool cover -func=coverage.out 2>&1 | grep total | grep -oP '\K\d+' || echo "0")
        rm -f coverage.out
    fi

    coverage=${coverage:-0}

    if [ "$coverage" -ge "$min" ]; then
        log_pass "Test coverage: ${coverage}% (minimum: ${min}%)"
    else
        log_fail "Test coverage: ${coverage}% (minimum: ${min}%)"
    fi
}

#-------------------------------------------------------------------------------
# Gate 2: Linting
#-------------------------------------------------------------------------------

gate_linting() {
    print_gate "Code Linting"

    if ! command -v eslint &> /dev/null && ! command -v ruff &> /dev/null && ! command -v golangci-lint &> /dev/null; then
        log_warn "No linter detected, skipping"
        return 0
    fi

    local errors=0

    if command -v eslint &> /dev/null; then
        log_info "Running ESLint..."
        if eslint src --max-warnings $MAX_WARNINGS 2>/dev/null; then
            log_pass "No linting errors"
        else
            errors=$((errors+1))
            log_fail "ESLint errors found"
        fi
    fi

    if command -v ruff &> /dev/null; then
        log_info "Running Ruff..."
        if ruff check src --output-format=text 2>/dev/null; then
            log_pass "No Ruff errors"
        else
            errors=$((errors+1))
            log_fail "Ruff errors found"
        fi
    fi

    if command -v golangci-lint &> /dev/null; then
        log_info "Running golangci-lint..."
        if golangci-lint run ./... 2>/dev/null; then
            log_pass "No golangci-lint errors"
        else
            errors=$((errors+1))
            log_fail "golangci-lint errors found"
        fi
    fi
}

#-------------------------------------------------------------------------------
# Gate 3: Type Checking
#-------------------------------------------------------------------------------

gate_type_checking() {
    print_gate "Type Checking"

    if ! command -v tsc &> /dev/null && ! command -v mypy &> /dev/null && ! command -v go vet &> /dev/null; then
        log_warn "No type checker detected, skipping"
        return 0
    fi

    if command -v tsc &> /dev/null; then
        log_info "Running TypeScript compiler..."
        if npx tsc --noEmit 2>/dev/null; then
            log_pass "Type checking passed"
        else
            log_fail "Type errors found"
        fi
    fi

    if command -v mypy &> /dev/null; then
        log_info "Running MyPy..."
        if mypy src 2>/dev/null; then
            log_pass "MyPy passed"
        else
            log_fail "MyPy errors found"
        fi
    fi

    if command -v go vet &> /dev/null; then
        log_info "Running go vet..."
        if go vet ./... 2>/dev/null; then
            log_pass "go vet passed"
        else
            log_fail "go vet errors found"
        fi
    fi
}

#-------------------------------------------------------------------------------
# Gate 4: Security Scan
#-------------------------------------------------------------------------------

gate_security() {
    print_gate "Security Scan"

    if ! command -v npm-audit &> /dev/null && ! command -v pip-audit &> /dev/null; then
        log_warn "No security scanner detected, skipping"
        return 0
    fi

    if command -v npm-audit &> /dev/null; then
        log_info "Running npm audit..."
        if npm audit --audit-level=high 2>/dev/null; then
            log_pass "No high-severity vulnerabilities"
        else
            log_warn "Security vulnerabilities found (review recommended)"
        fi
    fi

    if command -v pip-audit &> /dev/null; then
        log_info "Running pip-audit..."
        if pip-audit 2>/dev/null; then
            log_pass "No pip vulnerabilities"
        else
            log_warn "pip vulnerabilities found"
        fi
    fi
}

#-------------------------------------------------------------------------------
# Gate 5: Code Complexity
#-------------------------------------------------------------------------------

gate_complexity() {
    print_gate "Code Complexity"

    if ! command -v escomplex &> /dev/null && ! command -v radon &> /dev/null; then
        log_warn "No complexity tool detected, skipping"
        return 0
    fi

    local max_complexity=${1:-$MAX_COMPLEXITY}
    local violations=0

    if command -v escomplex &> /dev/null; then
        log_info "Checking JavaScript complexity..."
        violations=$(escomplex -m src --output text 2>/dev/null | grep -c "complexity.*$max_complexity" || echo "0")
    fi

    if command -v radon &> /dev/null; then
        log_info "Checking Python complexity..."
        local py_violations=$(radon cc src -a -n "$max_complexity" 2>/dev/null | grep -c "F" || echo "0")
        violations=$((violations + py_violations))
    fi

    if [ "$violations" -eq 0 ]; then
        log_pass "Complexity within limits (max: $max_complexity)"
    else
        log_fail "Complexity violations: $violations functions exceed limit"
    fi
}

#-------------------------------------------------------------------------------
# Gate 6: Debug Code Check
#-------------------------------------------------------------------------------

gate_debug_code() {
    print_gate "Debug Code Check"

    local found_debug=false

    # JavaScript/TypeScript
    if ls src/**/*.ts src/**/*.js 2>/dev/null | head -1 > /dev/null; then
        local debug_logs=$(grep -r "console\.\(log\|debug\)" src --include="*.ts" --include="*.js" 2>/dev/null || true)
        if [ -n "$debug_logs" ]; then
            log_fail "Debug console logs found:"
            echo "$debug_logs" | head -5
            found_debug=true
        fi

        if grep -rq "debugger" src --include="*.ts" --include="*.js" 2>/dev/null; then
            log_fail "debugger statements found"
            found_debug=true
        fi
    fi

    # Python
    if ls src/**/*.py 2>/dev/null | head -1 > /dev/null; then
        if grep -rq "print(" src --include="*.py" 2>/dev/null | grep -v "# print(" | head -1 > /dev/null; then
            log_fail "print statements found (likely debug code)"
            found_debug=true
        fi
    fi

    if [ "$found_debug" = false ]; then
        log_pass "No debug code detected"
    fi
}

#-------------------------------------------------------------------------------
# Gate 7: Documentation Check
#-------------------------------------------------------------------------------

gate_documentation() {
    print_gate "Documentation Check"

    local doc_count=$(find docs -name "*.md" 2>/dev/null | wc -l)

    if [ "$doc_count" -gt 0 ]; then
        log_pass "Documentation exists: $doc_count files"
    else
        log_warn "No documentation found"
    fi

    # Check for README
    if [ -f "README.md" ]; then
        log_pass "README.md exists"
    else
        log_warn "README.md missing"
    fi
}

#-------------------------------------------------------------------------------
# Gate 8: Git Status Check
#-------------------------------------------------------------------------------

gate_git_status() {
    print_gate "Git Status Check"

    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_warn "Not a git repository, skipping"
        return 0
    fi

    local status=$(git status --porcelain 2>/dev/null | wc -l)

    if [ "$status" -eq 0 ]; then
        log_pass "Working directory clean"
    else
        log_warn "Working directory has $status uncommitted changes"
    fi

    # Check branch name
    local branch=$(git branch --show-current 2>/dev/null || echo "detached")
    if [[ "$branch" == feature/* || "$branch" == fix/* || "$branch" == "main" || "$branch" == "master" ]]; then
        log_pass "On appropriate branch: $branch"
    else
        log_info "Current branch: $branch"
    fi
}

#-------------------------------------------------------------------------------
# Usage
#-------------------------------------------------------------------------------

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run comprehensive quality gate checks for the project.

OPTIONS:
    --skip-coverage      Skip test coverage check
    --skip-linting       Skip linting check
    --skip-types         Skip type checking
    --skip-security      Skip security scan
    --skip-complexity    Skip complexity check
    --skip-debug         Skip debug code check
    --skip-docs          Skip documentation check
    --min-coverage N     Minimum coverage required (default: $MIN_COVERAGE)
    --max-complexity N   Maximum complexity allowed (default: $MAX_COMPLEXITY)
    -h, --help           Show this help message

EXAMPLES:
    $(basename "$0")
    $(basename "$0") --min-coverage 90
    $(basename "$0") --skip-security --skip-docs

EOF
    exit 1
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

main() {
    local skip_coverage=false
    local skip_linting=false
    local skip_types=false
    local skip_security=false
    local skip_complexity=false
    local skip_debug=false
    local skip_docs=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-coverage) skip_coverage=true; shift ;;
            --skip-linting) skip_linting=true; shift ;;
            --skip-types) skip_types=true; shift ;;
            --skip-security) skip_security=true; shift ;;
            --skip-complexity) skip_complexity=true; shift ;;
            --skip-debug) skip_debug=true; shift ;;
            --skip-docs) skip_docs=true; shift ;;
            --min-coverage) MIN_COVERAGE="$2"; shift 2 ;;
            --max-complexity) MAX_COMPLEXITY="$2"; shift 2 ;;
            -h|--help) usage ;;
            *) shift ;;
        esac
    done

    print_header

    # Run gates
    [ "$skip_coverage" = false ] && gate_test_coverage
    [ "$skip_linting" = false ] && gate_linting
    [ "$skip_types" = false ] && gate_type_checking
    [ "$skip_security" = false ] && gate_security
    [ "$skip_complexity" = false ] && gate_complexity
    [ "$skip_debug" = false ] && gate_debug_code
    [ "$skip_docs" = false ] && gate_documentation
    gate_git_status

    # Print summary
    print_summary
}

main "$@"
