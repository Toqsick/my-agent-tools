#!/usr/bin/env bash
#===============================================================================
# setup-superpower-10x.sh - Setup script for Superpower-10x
# Part of Superpower-10x framework
#===============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         SUPERPOWER-10X SETUP                                 ║${NC}"
echo -e "${BLUE}║         10x Productivity for Coding Agents                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
SUPERPOWER_DIR="${SUPERPOWER_DIR:-.superpower-10x}"
PROJECT_ROOT="$(pwd)"

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

#-------------------------------------------------------------------------------
# Setup Functions
#-------------------------------------------------------------------------------

create_directories() {
    log_info "Creating directory structure..."

    mkdir -p "$PROJECT_ROOT/docs/superpowers/specs"
    mkdir -p "$PROJECT_ROOT/docs/superpowers/plans"
    mkdir -p "$PROJECT_ROOT/.worktrees"
    mkdir -p "$PROJECT_ROOT/$SUPERPOWER_DIR/templates"
    mkdir -p "$PROJECT_ROOT/$SUPERPOWER_DIR/configs"
    mkdir -p "$PROJECT_ROOT/tests/debug

    log_success "Directories created"
}

setup_gitignore() {
    log_info "Configuring gitignore..."

    # Add to .gitignore if not present
    if [ -f ".gitignore" ]; then
        if ! grep -q ".worktrees" .gitignore 2>/dev/null; then
            echo "" >> .gitignore
            echo "# Superpower-10x" >> .gitignore
            echo ".worktrees/" >> .gitignore
            echo "worktrees/" >> .gitignore
            echo "$SUPERPOWER_DIR/" >> .gitignore
            log_success "Added to .gitignore"
        else
            log_info ".gitignore already configured"
        fi
    else
        log_warn "No .gitignore found - please create one"
    fi

    # Initialize git repo if not present
    if [ ! -d ".git" ]; then
        log_info "Initializing git repository..."
        git init
        log_success "Git repository initialized"
    fi
}

make_scripts_executable() {
    log_info "Setting script permissions..."

    # Make all shell scripts executable
    find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true

    # Make Python scripts executable
    find . -name "*.py" -type f -exec chmod +x {} \; 2>/dev/null || true

    log_success "Permissions set"
}

create_config() {
    log_info "Creating configuration..."

    cat > "$PROJECT_ROOT/$SUPERPOWER_DIR/config.json" << 'EOF'
{
    "version": "1.0.0",
    "project": {
        "name": "default",
        "testCommand": "npm test",
        "lintCommand": "npm run lint",
        "buildCommand": "npm run build"
    },
    "quality": {
        "minCoverage": 80,
        "maxComplexity": 10,
        "strictMode": true
    },
    "paths": {
        "specsDir": "docs/superpowers/specs",
        "plansDir": "docs/superpowers/plans",
        "worktreesDir": ".worktrees"
    },
    "git": {
        "baseBranches": ["main", "master", "develop"],
        "defaultBranch": "main"
    }
}
EOF

    log_success "Configuration created"
}

create_template() {
    log_info "Creating default templates..."

    cat > "$PROJECT_ROOT/$SUPERPOWER_DIR/templates/spec.md" << 'EOF'
# [FEATURE NAME] Design Specification

> **Created:** YYYY-MM-DD HH:MM
> **Status:** Draft | Under Review | Approved | Implemented
> **Author:** [Author Name]

## Executive Summary
[One paragraph: What problem does this solve?]

## Goals
- [Specific, measurable goal 1]
- [Specific, measurable goal 2]

## Non-Goals
- [Explicitly out of scope]

## Background
[Why does this need to be built now?]

## Detailed Design

### Architecture
[High-level architecture description]

### Data Model
[Data structures, schemas, relationships]

### API Design
[Endpoints, request/response formats]

### User Flows
[Step-by-step user interactions]

## Implementation Approach
- [Approach with rationale]
- [Technology choices with justification]

## Testing Strategy
- Unit tests for [what]
- Integration tests for [what]
- E2E tests for [what]

## Rollout Plan
- Phase 1: [What]
- Phase 2: [What]

## Open Questions
- [ ] [Question 1]
- [ ] [Question 2]

## Approval
- [ ] Design reviewed by stakeholders
- [ ] Technical feasibility confirmed
- [ ] Timeline agreed
EOF

    cat > "$PROJECT_ROOT/$SUPERPOWER_DIR/templates/plan.md" << 'EOF'
# [FEATURE NAME] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpower-10x:subagent-driven-execution
> **Plan Status:** Draft | In Progress | Complete

**Goal:** [One sentence]

**Architecture:** [2-3 sentences]

**Tech Stack:** [Key technologies]

---

## Task Breakdown

### Task 1: [Component Name]
**Files:**
- Create: `path/to/file.ext`
- Modify: `path/to/existing.ext`
- Test: `tests/path/test.ext`

- [ ] **Step 1: Write the failing test**
  ```language
  test('specific behavior', () => {
    // test code
  });
  ```

- [ ] **Step 2: Run test to verify it fails**
  ```bash
  npm test -- --testPathPattern="test-name"
  # Expected: FAIL
  ```

- [ ] **Step 3: Write minimal implementation**
  ```language
  function implementation() {
    // minimal code
  }
  ```

- [ ] **Step 4: Run test to verify it passes**
  ```bash
  npm test -- --testPathPattern="test-name"
  # Expected: PASS
  ```

- [ ] **Step 5: Commit**
  ```bash
  git add . && git commit -m "feat: add specific behavior"
  ```

---

## Verification Checklist
- [ ] All tests pass
- [ ] No console errors
- [ ] Code follows style guide
- [ ] Documentation updated
EOF

    log_success "Templates created"
}

create_hooks() {
    log_info "Setting up git hooks..."

    HOOKS_DIR=".git/hooks"
    mkdir -p "$HOOKS_DIR"

    # Pre-commit hook for TDD enforcement
    cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook for TDD enforcement

echo "Running pre-commit checks..."

# Check for test files
TESTS_CHANGED=$(git diff --cached --name-only | grep -E "test|spec" | head -1 || true)
SOURCE_CHANGED=$(git diff --cached --name-only | grep -vE "test|spec|md|json" | head -1 || true)

if [ -n "$SOURCE_CHANGED" ] && [ -z "$TESTS_CHANGED" ]; then
    echo "⚠️  Source files changed without tests"
    echo "Consider adding tests following TDD methodology"
fi

echo "Pre-commit checks complete"
EOF

    chmod +x "$HOOKS_DIR/pre-commit"
    log_success "Git hooks configured"
}

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    SETUP COMPLETE                             ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Superpower-10x has been set up successfully!"
    echo ""
    echo "Directory Structure:"
    echo "  docs/superpowers/specs/   - Design specifications"
    echo "  docs/superpowers/plans/   - Implementation plans"
    echo "  .worktrees/               - Isolated workspaces"
    echo "  $SUPERPOWER_DIR/          - Configuration & templates"
    echo ""
    echo "Available Commands:"
    echo "  ./scripts/auto-plan.sh <feature>       - Generate implementation plan"
    echo "  ./scripts/tdd-enforce.sh <phase>       - Enforce TDD discipline"
    echo "  ./scripts/quality-gate.sh             - Run quality checks"
    echo "  python scripts/subagent_executor.py    - Execute plan with subagents"
    echo "  python scripts/debug_engine.py         - Systematic debugging"
    echo "  python scripts/finish_pipeline.py      - Complete branch workflow"
    echo ""
    echo "Next Steps:"
    echo "  1. Start a new brainstorming session"
    echo "  2. Create a design specification"
    echo "  3. Generate an implementation plan"
    echo "  4. Execute with subagents"
    echo ""
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

main() {
    # Check for existing setup
    if [ -d "$PROJECT_ROOT/$SUPERPOWER_DIR" ]; then
        echo ""
        log_warn "Superpower-10x appears to already be set up."
        read -p "Re-run setup? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Setup cancelled"
            exit 0
        fi
    fi

    # Run setup steps
    create_directories
    setup_gitignore
    make_scripts_executable
    create_config
    create_template
    create_hooks

    # Print summary
    print_summary
}

main "$@"
