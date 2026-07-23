#!/usr/bin/env bash
#===============================================================================
# tdd-enforce.sh - Test-Driven Development enforcement script
# Part of Superpower-10x framework
#===============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
STRICT_MODE=${STRICT_MODE:-true}
ALLOW_DEBUG=${ALLOW_DEBUG:-false}

#-------------------------------------------------------------------------------
# Logging Functions
#-------------------------------------------------------------------------------

log_phase() { echo -e "\n${CYAN}=== $1 ===${NC}"; }
log_pass() { echo -e "${GREEN}✓ PASS${NC}: $1"; }
log_fail() { echo -e "${RED}✗ FAIL${NC}: $1"; }
log_warn() { echo -e "${YELLOW}⚠ WARN${NC}: $1"; }
log_info() { echo -e "${BLUE}ℹ INFO${NC}: $1"; }

#-------------------------------------------------------------------------------
# TDD Phase Functions
#-------------------------------------------------------------------------------

check_red_phase() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .test.*)

    log_phase "RED Phase - Verify Test Fails"

    # Check test file exists
    if [ ! -f "$test_file" ]; then
        log_fail "Test file does not exist: $test_file"
        log_info "Must create test BEFORE implementation"
        return 1
    fi
    log_pass "Test file exists"

    # Run test
    log_info "Running test..."

    local test_output
    local test_exit_code=0

    # Detect test framework and run
    if command -v jest &> /dev/null; then
        test_output=$(npx jest "$test_name" --no-coverage 2>&1) || test_exit_code=$?
    elif command -v pytest &> /dev/null; then
        test_output=$(pytest "$test_file" -v 2>&1) || test_exit_code=$?
    elif command -v go test &> /dev/null; then
        test_output=$(go test -v "$test_file" 2>&1) || test_exit_code=$?
    else
        log_warn "No known test framework detected"
        log_info "Please run tests manually and check that they FAIL"
        return 0
    fi

    # Verify test fails
    if [ $test_exit_code -eq 0 ]; then
        log_fail "Test passes without implementation"
        echo "$test_output"
        echo ""
        log_info "TDD Violation: Write test FIRST, verify it fails"
        log_info "Delete implementation code, write test, verify FAIL"
        return 1
    fi

    log_pass "Test fails as expected (RED phase verified)"
    return 0
}

check_green_phase() {
    local test_file="$1"
    local impl_file="$2"
    local test_name=$(basename "$test_file" .test.*)

    log_phase "GREEN Phase - Verify Implementation"

    # Check implementation exists
    if [ ! -f "$impl_file" ]; then
        log_warn "Implementation file does not exist yet"
        log_info "Proceed with implementation, then re-run GREEN check"
        return 0
    fi
    log_pass "Implementation file exists"

    # Check for debug code
    if [ "$ALLOW_DEBUG" = "false" ]; then
        check_no_debug_code "$impl_file"
    fi

    # Run test
    log_info "Running test..."

    local test_output
    local test_exit_code=0

    # Detect test framework and run
    if command -v jest &> /dev/null; then
        test_output=$(npx jest "$test_name" --no-coverage 2>&1) || test_exit_code=$?
    elif command -v pytest &> /dev/null; then
        test_output=$(pytest "$test_file" -v 2>&1) || test_exit_code=$?
    elif command -v go test &> /dev/null; then
        test_output=$(go test -v "$test_file" 2>&1) || test_exit_code=$?
    else
        log_warn "No known test framework detected"
        log_info "Please run tests manually"
        return 0
    fi

    # Verify test passes
    if [ $test_exit_code -ne 0 ]; then
        log_fail "Test still failing"
        echo "$test_output"
        return 1
    fi

    log_pass "Test passes (GREEN phase verified)"
    return 0
}

check_no_debug_code() {
    local file="$1"

    log_phase "Debug Code Check"

    # JavaScript/TypeScript
    if [[ "$file" == *.js || "$file" == *.ts || "$file" == *.jsx" || "$file" == *.tsx" ]]; then
        local debug_patterns=(
            "console\.log"
            "console\.debug"
            "console\.info"
            "debugger"
            "print("
        )

        for pattern in "${debug_patterns[@]}"; do
            if grep -qE "$pattern" "$file" 2>/dev/null; then
                local matches=$(grep -nE "$pattern" "$file" || true)
                if [ -n "$matches" ]; then
                    log_fail "Debug code found: $pattern"
                    echo "$matches"
                    if [ "$STRICT_MODE" = "true" ]; then
                        return 1
                    fi
                fi
            fi
        done
    fi

    # Python
    if [[ "$file" == *.py ]]; then
        if grep -qE "(print\(|breakpoint\()" "$file" 2>/dev/null; then
            local matches=$(grep -nE "(print\(|breakpoint\()" "$file" || true)
            if [ -n "$matches" ]; then
                log_warn "Debug code found (print/breakpoint)"
                echo "$matches"
                if [ "$STRICT_MODE" = "true" ]; then
                    return 1
                fi
            fi
        fi
    fi

    log_pass "No debug code found"
    return 0
}

#-------------------------------------------------------------------------------
# Usage
#-------------------------------------------------------------------------------

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] <phase> [files...]

Enforce TDD discipline with RED-GREEN-REFACTOR cycle verification.

PHASES:
    red         Check RED phase (test should fail)
    green       Check GREEN phase (test should pass with implementation)
    all         Run full TDD cycle check
    debug       Check for debug code only

FILES:
    test_file   Path to test file (required)
    impl_file   Path to implementation file (required for green/all phases)

OPTIONS:
    --allow-debug    Allow debug code (default: false)
    --strict         Strict mode - fail on any violation (default: true)
    -h, --help       Show this help message

EXAMPLES:
    $(basename "$0") red tests/auth.test.ts
    $(basename "$0") green tests/auth.test.ts src/auth.ts
    $(basename "$0") all tests/auth.test.ts src/auth.ts
    $(basename "$0") debug src/auth.ts

EOF
    exit 1
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

main() {
    local phase=""
    local test_file=""
    local impl_file=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --allow-debug)
                ALLOW_DEBUG=true
                shift
                ;;
            --strict)
                STRICT_MODE=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            red|green|all|debug)
                phase="$1"
                shift
                ;;
            *)
                if [ -z "$test_file" ]; then
                    test_file="$1"
                elif [ -z "$impl_file" ]; then
                    impl_file="$1"
                fi
                shift
                ;;
        esac
    done

    # Validate
    if [ -z "$phase" ]; then
        log_error "Phase required (red, green, all, debug)"
        usage
    fi

    case $phase in
        red)
            if [ -z "$test_file" ]; then
                log_error "Test file required for RED phase"
                usage
            fi
            check_red_phase "$test_file"
            ;;
        green)
            if [ -z "$test_file" ] || [ -z "$impl_file" ]; then
                log_error "Test file and implementation file required for GREEN phase"
                usage
            fi
            check_green_phase "$test_file" "$impl_file"
            ;;
        all)
            if [ -z "$test_file" ] || [ -z "$impl_file" ]; then
                log_error "Test file and implementation file required"
                usage
            fi
            check_red_phase "$test_file" && check_green_phase "$test_file" "$impl_file"
            ;;
        debug)
            if [ -z "$test_file" ]; then
                log_error "File required for debug check"
                usage
            fi
            check_no_debug_code "$test_file"
            ;;
    esac
}

main "$@"
