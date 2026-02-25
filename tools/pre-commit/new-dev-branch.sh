#!/bin/bash
# Helper script to create properly named development branches for no-OS

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

usage() {
    echo "Create a new development branch following no-OS naming convention"
    echo ""
    echo "Usage: $0 <device_name> [branch_type]"
    echo ""
    echo "Arguments:"
    echo "  device_name   Device name (e.g., adm1275, ltc2978, ad7091r5)"
    echo "  branch_type   Optional branch type:"
    echo "                - eval       (dev/<device>-eval)"
    echo "                - <platform> (dev/<device>-maxim, dev/<device>-linux)"
    echo "                - fix-<desc> (dev/<device>-fix-<description>)"
    echo ""
    echo "Examples:"
    echo "  $0 adm1275                    → dev/adm1275"
    echo "  $0 adm1275 eval               → dev/adm1275-eval"
    echo "  $0 adm1275 maxim              → dev/adm1275-maxim"
    echo "  $0 adm1275 fix-telemetry      → dev/adm1275-fix-telemetry"
    echo "  $0 ad717x                     → dev/ad717x"
}

# Validate device name
validate_device_name() {
    local device="$1"

    # Check if device name is reasonable (letters, numbers, common patterns)
    if [[ ! "$device" =~ ^[a-z0-9][a-z0-9_-]*[a-z0-9]?$ ]] && [[ ! "$device" =~ ^[a-z]+[0-9]+[a-z]*$ ]]; then
        echo "❌ Invalid device name format: '$device'"
        echo "   Device names should be lowercase alphanumeric (e.g., adm1275, ad717x)"
        return 1
    fi

    return 0
}

# Main function
main() {
    if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage
        exit 0
    fi

    local device_name="$1"
    local branch_type="$2"

    # Convert to lowercase
    device_name=$(echo "$device_name" | tr '[:upper:]' '[:lower:]')

    # Validate device name
    if ! validate_device_name "$device_name"; then
        exit 1
    fi

    # Construct branch name
    local branch_name="dev/$device_name"

    if [ -n "$branch_type" ]; then
        branch_name="$branch_name-$branch_type"
    fi

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo "❌ Not in a git repository"
        exit 1
    fi

    # Check if branch already exists
    if git show-ref --verify --quiet "refs/heads/$branch_name"; then
        echo "❌ Branch '$branch_name' already exists"
        echo_info "Switch to it with: git checkout $branch_name"
        exit 1
    fi

    # Get current branch for reference
    current_branch=$(git branch --show-current)

    # Check if we should sync with upstream first
    if git remote get-url upstream > /dev/null 2>&1; then
        if [ "$current_branch" = "main" ]; then
            echo_info "Checking if main branch is up to date with upstream..."

            # Fetch upstream to compare
            git fetch upstream main > /dev/null 2>&1

            # Check if main is behind upstream
            behind_count=$(git rev-list --count HEAD..upstream/main 2>/dev/null || echo "0")
            if [ "$behind_count" -gt 0 ]; then
                echo_warning "Your main branch is $behind_count commits behind upstream/main"
                echo_info "Recommendation: sync with upstream first:"
                echo_info "  git fetch upstream && git rebase upstream/main"
                echo_info "  git push origin main"
                echo ""
                read -p "Continue creating branch anyway? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    echo_info "Aborting branch creation. Please sync with upstream first."
                    exit 1
                fi
            fi
        fi
    else
        echo_warning "No 'upstream' remote found. Consider setting up fork workflow:"
        echo_warning "  git remote add upstream https://github.com/analogdevicesinc/no-OS.git"
    fi

    # Create and switch to new branch
    echo_info "Creating new development branch: $branch_name"
    echo_info "Based on current branch: $current_branch"

    git checkout -b "$branch_name"

    echo_success "Created and switched to branch: $branch_name"
    echo ""
    echo "📋 Next steps:"
    echo "1. Install pre-commit hooks (if not done): ./tools/pre-commit/install-hooks.sh"
    echo "2. Create driver template: python3 tools/pre-commit/create-device-template.py $device_name <type>"
    echo "3. Start development and commit with signed-off commits: git commit -s"
    echo "4. Push to your fork when ready: git push origin $branch_name"
    echo "5. Create PR to upstream: gh pr create --repo analogdevicesinc/no-OS"
    echo ""

    # Show some helpful device-specific suggestions
    case "$device_name" in
        adm127*|ltc29*|max20*|ltc38*|ltc70*)
            echo "💡 PMBus device detected. Create template with:"
            echo "   python3 tools/pre-commit/create-device-template.py $device_name pmbus --with-project"
            ;;
        ad70*|ad71*|ad72*|ad73*|ad74*|ad76*|ad77*|ad78*|ad79*|adaq*)
            echo "💡 ADC device detected. Create template with:"
            echo "   python3 tools/pre-commit/create-device-template.py $device_name adc --with-project"
            ;;
        ad41*|ad42*|ad50*|ad51*|ad52*|ad53*|ad54*)
            echo "💡 DAC device detected. Consider creating DAC template (not yet implemented)"
            ;;
    esac
}

main "$@"