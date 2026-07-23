#!/usr/bin/env bash
#===============================================================================
# auto-plan.sh - Automated implementation plan generator
# Part of Superpower-10x framework
#===============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PLAN_DIR="docs/superpowers/plans"
TEMPLATE_DIR=".superpower-10x/templates"

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] <feature-name>

Generate an implementation plan for a feature.

OPTIONS:
    -d, --dir <path>       Plan output directory (default: $PLAN_DIR)
    -t, --template <name>  Use specific template
    -i, --interactive     Interactive mode with prompts
    -h, --help            Show this help message

EXAMPLES:
    $(basename "$0") user-authentication
    $(basename "$0") -i payment-integration
    $(basename "$0") -t api-rest api-endpoints

EOF
    exit 1
}

#-------------------------------------------------------------------------------
# Setup
#-------------------------------------------------------------------------------

setup_directories() {
    log_info "Setting up directories..."
    mkdir -p "$PLAN_DIR"
    mkdir -p "$TEMPLATE_DIR"

    # Create default template if not exists
    if [ ! -f "$TEMPLATE_DIR/plan.md" ]; then
        cat > "$TEMPLATE_DIR/plan.md" << 'TEMPLATE'
# [FEATURE_NAME] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpower-10x:subagent-driven-execution
> **Plan Status:** Draft | In Progress | Complete
> **Created:** $(date '+%Y-%m-%d %H:%M')
> **Author:** Auto-generated

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about the approach]

**Tech Stack:** [Key technologies/libraries]

---

## Task Breakdown

### Task 1: [Component Name]

**Files:**
- Create: \`path/to/file.ext\`
- Modify: \`path/to/existing.ext:line-range\`
- Test: \`tests/path/test.ext\`

**Prerequisites:** [Any dependencies or context needed]

- [ ] **Step 1: Write the failing test**

\`\`\`language
test('specific behavior', () => {
  // test code
});
\`\`\`

- [ ] **Step 2: Run test to verify it fails**
  \`\`\`bash
  npm test -- --testPathPattern="test-name"
  # Expected: FAIL
  \`\`\`

- [ ] **Step 3: Write minimal implementation**
  \`\`\`language
  function implementation() {
    // minimal code
  }
  \`\`\`

- [ ] **Step 4: Run test to verify it passes**
  \`\`\`bash
  npm test -- --testPathPattern="test-name"
  # Expected: PASS
  \`\`\`

- [ ] **Step 5: Commit with conventional message**
  \`\`\`bash
  git add . && git commit -m "feat: add specific behavior"
  \`\`\`

---

### Task 2: [Next Component]
[Repeat structure above]

---

## Verification Checklist

Before marking complete:
- [ ] All tests pass
- [ ] No console errors
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No debug code left
- [ ] Types are correct
- [ ] Edge cases handled

## Rollout Plan

1. **Development** - Implement all tasks
2. **Testing** - Run full test suite
3. **Review** - Code review
4. **Merge** - Integrate into main branch
5. **Deploy** - Release to production

## Success Metrics

- [ ] Feature complete by: [DATE]
- [ ] Test coverage: [TARGET]%
- [ ] Performance: [METRICS]

## Open Questions

- [ ] [Question 1]
- [ ] [Question 2]

---

*Generated with Superpower-10x*
TEMPLATE
        log_success "Default template created"
    fi
}

#-------------------------------------------------------------------------------
# Plan Generation
#-------------------------------------------------------------------------------

generate_plan() {
    local feature_name="$1"
    local output_dir="${2:-$PLAN_DIR}"
    local template_file="$TEMPLATE_DIR/plan.md"

    # Sanitize feature name
    local safe_name=$(echo "$feature_name" | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9-]//g')
    local date_prefix=$(date '+%Y-%m-%d')
    local output_file="${output_dir}/${date_prefix}-${safe_name}.md"

    log_info "Generating plan for: $feature_name"
    log_info "Output file: $output_file"

    # Ensure output directory exists
    mkdir -p "$output_dir"

    # Generate plan from template
    local plan_content
    plan_content=$(cat "$template_file")

    # Replace placeholders
    plan_content="${plan_content//\[FEATURE_NAME\]/$feature_name}"
    plan_content="${plan_content//\$\(date /$(date }"

    # Write plan
    echo "$plan_content" > "$output_file"

    log_success "Plan generated: $output_file"
    echo ""
    echo "Next steps:"
    echo "  1. Edit the plan: nano $output_file"
    echo "  2. Fill in task details"
    echo "  3. Execute: superpower-10x:execute-plan $output_file"
}

#-------------------------------------------------------------------------------
# Interactive Mode
#-------------------------------------------------------------------------------

interactive_mode() {
    echo ""
    echo "================================================"
    echo "       SUPERPOWER-10X PLAN GENERATOR"
    echo "================================================"
    echo ""

    read -rp "Feature name: " feature_name
    if [ -z "$feature_name" ]; then
        log_error "Feature name cannot be empty"
        exit 1
    fi

    read -rp "Plan directory [$PLAN_DIR]: " custom_dir
    PLAN_DIR="${custom_dir:-$PLAN_DIR}"

    read -rp "Template (default/api/etc.) [default]: " template
    if [ -n "$template" ] && [ -f "$TEMPLATE_DIR/${template}.md" ]; then
        export TEMPLATE_FILE="$TEMPLATE_DIR/${template}.md"
    fi

    echo ""
    generate_plan "$feature_name" "$PLAN_DIR"
}

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

main() {
    local feature_name=""
    local interactive=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dir)
                PLAN_DIR="$2"
                shift 2
                ;;
            -t|--template)
                TEMPLATE_FILE="$TEMPLATE_DIR/${2}.md"
                shift 2
                ;;
            -i|--interactive)
                interactive=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                ;;
            *)
                feature_name="$1"
                shift
                ;;
        esac
    done

    # Setup
    setup_directories

    # Run in appropriate mode
    if [ "$interactive" = true ]; then
        interactive_mode
    elif [ -z "$feature_name" ]; then
        log_error "Feature name required"
        echo "Use --interactive for guided plan generation"
        usage
    else
        generate_plan "$feature_name"
    fi
}

main "$@"
