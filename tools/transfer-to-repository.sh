#!/bin/bash
# Transfer no-OS development tools and configuration to another repository
# Handles both innersource and public repository transfers

set -e

# Colors
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
    echo "Transfer no-OS development tools to another repository"
    echo ""
    echo "Usage: $0 <target_repo_path>"
    echo ""
    echo "Arguments:"
    echo "  target_repo_path    Path to target repository (e.g., /path/to/innersource-no-OS)"
    echo ""
    echo "This script will copy:"
    echo "  • CLAUDE.md (enhanced documentation)"
    echo "  • tools/pre-commit/ (all development tools)"
    echo "  • Local SonarCloud scanner setup"
    echo "  • .pre-commit-config (if exists)"
    echo "  • review_patterns.json (if exists)"
    echo ""
    echo "Example:"
    echo "  $0 /home/user/innersource-no-OS"
}

validate_source() {
    echo_info "Validating source repository..."

    if [ ! -f "CLAUDE.md" ]; then
        echo "❌ CLAUDE.md not found. Are you in the correct source repository?"
        exit 1
    fi

    if [ ! -d "tools/pre-commit" ]; then
        echo "❌ tools/pre-commit directory not found"
        exit 1
    fi

    echo_success "Source repository validated"
}

validate_target() {
    local target_path="$1"

    echo_info "Validating target repository: $target_path"

    if [ ! -d "$target_path" ]; then
        echo "❌ Target path does not exist: $target_path"
        exit 1
    fi

    if [ ! -d "$target_path/.git" ]; then
        echo "❌ Target path is not a git repository: $target_path"
        exit 1
    fi

    # Check if it looks like a no-OS repository
    if [ ! -d "$target_path/drivers" ] || [ ! -d "$target_path/projects" ]; then
        echo_warning "Target doesn't appear to be a no-OS repository (missing drivers/ or projects/)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Transfer cancelled"
            exit 1
        fi
    fi

    echo_success "Target repository validated"
}

transfer_files() {
    local target_path="$1"

    echo_info "Transferring files to $target_path..."

    # Create backup of existing files
    if [ -f "$target_path/CLAUDE.md" ]; then
        echo_info "Backing up existing CLAUDE.md"
        cp "$target_path/CLAUDE.md" "$target_path/CLAUDE.md.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Transfer CLAUDE.md
    echo_info "Transferring CLAUDE.md..."
    cp CLAUDE.md "$target_path/"
    echo_success "CLAUDE.md transferred"

    # Transfer tools directory
    echo_info "Transferring tools/pre-commit/..."
    mkdir -p "$target_path/tools"
    if [ -d "$target_path/tools/pre-commit" ]; then
        echo_info "Backing up existing tools/pre-commit"
        mv "$target_path/tools/pre-commit" "$target_path/tools/pre-commit.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    cp -r tools/pre-commit "$target_path/tools/"
    echo_success "tools/pre-commit/ transferred"

    # Transfer optional files
    optional_files=(".pre-commit-config" "review_patterns.json" "extract_review_patterns.py")
    for file in "${optional_files[@]}"; do
        if [ -f "$file" ]; then
            echo_info "Transferring $file..."
            cp "$file" "$target_path/"
            echo_success "$file transferred"
        fi
    done

    # Make scripts executable
    echo_info "Setting executable permissions..."
    find "$target_path/tools/pre-commit" -name "*.sh" -exec chmod +x {} \;
    find "$target_path/tools/pre-commit" -name "*.py" -exec chmod +x {} \;
    chmod +x "$target_path/tools/pre-commit/pre-commit"
    chmod +x "$target_path/tools/pre-commit/commit-msg"
    echo_success "Permissions set"
}

update_documentation() {
    local target_path="$1"

    echo_info "Updating documentation for target repository..."

    # Get target repository remote info
    cd "$target_path"
    origin_url=$(git remote get-url origin 2>/dev/null || echo "")

    if [[ "$origin_url" == *"innersource"* ]] || [[ "$origin_url" == *"internal"* ]]; then
        echo_info "Detected innersource/internal repository"

        # Update CLAUDE.md for innersource
        sed -i 's/analogdevicesinc\/no-OS/YOUR_INNERSOURCE_ORG\/no-OS/g' CLAUDE.md
        sed -i 's/github\.com\/analogdevicesinc/your-git-server\/YOUR_INNERSOURCE_ORG/g' CLAUDE.md

        echo_warning "Updated repository URLs in CLAUDE.md"
        echo_warning "Please manually update git server URLs if needed"
    fi

    echo_success "Documentation updated for target repository"
    cd - > /dev/null
}

generate_migration_report() {
    local target_path="$1"

    echo ""
    echo_info "📋 Transfer Summary"
    echo_info "Source: $(pwd)"
    echo_info "Target: $target_path"
    echo ""
    echo_success "✅ Files transferred:"
    echo "   • CLAUDE.md (enhanced development guide)"
    echo "   • tools/pre-commit/ (all development tools)"
    echo "   • Optional configuration files"
    echo ""
    echo_info "🔧 Next steps in target repository:"
    echo "   1. cd $target_path"
    echo "   2. ./tools/pre-commit/validate-setup.sh"
    echo "   3. ./tools/pre-commit/install-hooks.sh"
    echo "   4. Review and customize .pre-commit-config if needed"
    echo ""
    echo_warning "⚠️  Remember to:"
    echo "   • Update git server URLs in CLAUDE.md if using internal git"
    echo "   • Customize tools/pre-commit/pre-commit-config.example for your environment"
    echo "   • Test the tools with ./tools/pre-commit/new-dev-branch.sh test-device"
    echo ""
}

main() {
    if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage
        exit 0
    fi

    local target_path="$1"

    echo_info "no-OS Development Tools Transfer"
    echo ""

    validate_source
    validate_target "$target_path"

    transfer_files "$target_path"
    update_documentation "$target_path"

    generate_migration_report "$target_path"

    echo_success "🎉 Transfer completed successfully!"
}

main "$@"