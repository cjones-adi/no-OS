#!/bin/bash
# Validate no-OS development environment setup
# Checks for proper fork workflow, remotes, and tools

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_header() {
    echo -e "${BLUE}🔍 $1${NC}"
}

validate_git_repo() {
    echo_header "Validating Git Repository Setup"

    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo_error "Not in a git repository"
        return 1
    fi
    echo_success "In a git repository"

    # Check remotes
    if ! git remote get-url origin > /dev/null 2>&1; then
        echo_error "No 'origin' remote found"
        return 1
    fi
    echo_success "Origin remote configured"

    if ! git remote get-url upstream > /dev/null 2>&1; then
        echo_warning "No 'upstream' remote found"
        echo_info "Consider adding: git remote add upstream https://github.com/analogdevicesinc/no-OS.git"
    else
        echo_success "Upstream remote configured"
    fi

    # Check if origin points to a fork
    origin_url=$(git remote get-url origin)
    if [[ "$origin_url" == *"analogdevicesinc/no-OS"* ]]; then
        echo_warning "Origin points to main repository, not a fork"
        echo_info "Consider forking and updating origin to your fork"
    else
        echo_success "Origin appears to be a fork"
    fi

    return 0
}

validate_tools() {
    echo_header "Validating Development Tools"

    # Check for pre-commit tools
    if [ -f "tools/pre-commit/pre-commit" ]; then
        echo_success "Pre-commit hook found"
    else
        echo_error "Pre-commit hook not found"
        return 1
    fi

    if [ -f ".git/hooks/pre-commit" ]; then
        echo_success "Pre-commit hook installed"
    else
        echo_warning "Pre-commit hook not installed"
        echo_info "Run: ./tools/pre-commit/install-hooks.sh"
    fi

    # Check for required tools
    tools=("python3" "git" "make")
    for tool in "${tools[@]}"; do
        if command -v "$tool" > /dev/null 2>&1; then
            echo_success "$tool available"
        else
            echo_error "$tool not found"
        fi
    done

    # Check optional tools
    optional_tools=("gh" "astyle" "cppcheck")
    for tool in "${optional_tools[@]}"; do
        if command -v "$tool" > /dev/null 2>&1; then
            echo_success "$tool available (optional)"
        else
            echo_warning "$tool not found (optional)"
        fi
    done

    return 0
}

validate_branch_setup() {
    echo_header "Validating Branch Setup"

    current_branch=$(git branch --show-current)
    echo_info "Current branch: $current_branch"

    # Test branch name validation
    if bash tools/pre-commit/check-branch-name.sh > /dev/null 2>&1; then
        echo_success "Branch name follows convention"
    else
        echo_warning "Branch name doesn't follow dev/<device> convention"
        echo_info "This is OK for main/master branches"
    fi

    return 0
}

validate_upstream_sync() {
    echo_header "Checking Upstream Synchronization"

    if ! git remote get-url upstream > /dev/null 2>&1; then
        echo_warning "No upstream remote - skipping sync check"
        return 0
    fi

    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ] && [ "$current_branch" != "master" ]; then
        echo_info "Not on main branch - skipping sync check"
        return 0
    fi

    # Fetch upstream silently
    echo_info "Fetching upstream to check synchronization..."
    if ! git fetch upstream main > /dev/null 2>&1; then
        echo_warning "Could not fetch upstream"
        return 0
    fi

    # Check if behind
    behind_count=$(git rev-list --count HEAD..upstream/main 2>/dev/null || echo "0")
    if [ "$behind_count" -gt 0 ]; then
        echo_warning "Main branch is $behind_count commits behind upstream"
        echo_info "Consider running: git fetch upstream && git rebase upstream/main"
    else
        echo_success "Main branch is up to date with upstream"
    fi

    return 0
}

display_summary() {
    echo ""
    echo_header "Environment Summary"

    # Repository info
    if git remote get-url origin > /dev/null 2>&1; then
        echo_info "Origin: $(git remote get-url origin)"
    fi
    if git remote get-url upstream > /dev/null 2>&1; then
        echo_info "Upstream: $(git remote get-url upstream)"
    fi

    echo_info "Current branch: $(git branch --show-current)"

    # Tools status
    echo_info "Pre-commit hooks: $([ -f ".git/hooks/pre-commit" ] && echo "✅ Installed" || echo "❌ Not installed")"
    echo_info "Branch validation: $([ -f "tools/pre-commit/check-branch-name.sh" ] && echo "✅ Available" || echo "❌ Missing")"
    echo_info "Template generator: $([ -f "tools/pre-commit/create-device-template.py" ] && echo "✅ Available" || echo "❌ Missing")"

    echo ""
    echo_header "Quick Start"
    echo_info "1. Sync with upstream: git fetch upstream && git rebase upstream/main"
    echo_info "2. Create new branch: ./tools/pre-commit/new-dev-branch.sh <device>"
    echo_info "3. Generate template: python3 tools/pre-commit/create-device-template.py <device> <type>"
    echo ""
}

# Main validation
main() {
    echo_header "no-OS Development Environment Validation"
    echo ""

    local exit_code=0

    validate_git_repo || exit_code=1
    echo ""

    validate_tools || exit_code=1
    echo ""

    validate_branch_setup || exit_code=1
    echo ""

    validate_upstream_sync || exit_code=1
    echo ""

    display_summary

    if [ $exit_code -eq 0 ]; then
        echo_success "🎉 Environment validation passed!"
        echo_info "Ready for no-OS development"
    else
        echo_error "💥 Environment validation failed!"
        echo_info "Please fix the issues above"
    fi

    exit $exit_code
}

main "$@"