#!/bin/bash

# no-OS Development Workflow Transfer Script
# Transfers complete development workflow to target repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 no-OS Development Workflow Transfer"
echo "======================================"
echo "Source: $SCRIPT_DIR"
echo "Target: $TARGET_DIR"
echo ""

# Function to backup existing files
backup_existing() {
    local file="$1"
    if [[ -f "$TARGET_DIR/$file" ]]; then
        echo "📁 Backing up existing $file"
        mv "$TARGET_DIR/$file" "$TARGET_DIR/${file}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
}

# Function to copy with verification
copy_with_verification() {
    local src="$1"
    local dst="$2"
    local description="$3"

    echo "📋 Installing $description..."
    if [[ -d "$SCRIPT_DIR/$src" ]]; then
        mkdir -p "$TARGET_DIR/$dst"
        cp -r "$SCRIPT_DIR/$src"/* "$TARGET_DIR/$dst/"
    elif [[ -f "$SCRIPT_DIR/$src" ]]; then
        mkdir -p "$(dirname "$TARGET_DIR/$dst")"
        cp "$SCRIPT_DIR/$src" "$TARGET_DIR/$dst"
    else
        echo "⚠️  Warning: $src not found, skipping"
        return 1
    fi
    echo "✅ $description installed"
}

echo "🔄 Starting workflow transfer..."
echo ""

# 1. Install main CLAUDE.md guide
echo "📖 Installing main development guide..."
backup_existing "CLAUDE.md"
copy_with_verification "CLAUDE.md" "CLAUDE.md" "main development guide"
echo ""

# 2. Install documentation
copy_with_verification "docs" "docs" "complete documentation suite"
echo ""

# 3. Install automation tools
copy_with_verification "tools" "tools" "automation tools and scripts"
echo ""

# 4. Install configuration files
copy_with_verification "config/sonar-project.properties" "sonar-project.properties" "SonarCloud configuration"
echo ""

# 5. Install data files
copy_with_verification "data/review_patterns_6month.json" "review_patterns_6month.json" "review pattern analysis data"
echo ""

# 6. Install GitHub integration (optional)
read -p "📊 Install GitHub Actions and review agents? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    copy_with_verification "github-integration/agents" ".github/agents" "GitHub review automation agents"
    copy_with_verification "github-integration/workflows" ".github/workflows" "GitHub workflow automation"
    echo ""
fi

# 7. Install and configure pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
if [[ -f "$TARGET_DIR/tools/pre-commit/install-hooks.sh" ]]; then
    cd "$TARGET_DIR"
    chmod +x tools/pre-commit/install-hooks.sh
    ./tools/pre-commit/install-hooks.sh
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  Pre-commit installation script not found"
fi
echo ""

# 8. Validate installation
echo "🔍 Validating installation..."
validation_errors=0

# Check essential files
essential_files=(
    "CLAUDE.md"
    "docs/development-environment-setup.md"
    "docs/framework-validation-lessons.md"
    "tools/scripts/framework_validation.sh"
    "tools/pre-commit/review-checker.py"
    "tools/pre-commit/validate-setup.sh"
)

for file in "${essential_files[@]}"; do
    if [[ -f "$TARGET_DIR/$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file (MISSING)"
        ((validation_errors++))
    fi
done

echo ""

# 9. Run environment validation
if [[ -f "$TARGET_DIR/tools/pre-commit/validate-setup.sh" ]]; then
    echo "🧪 Running environment validation..."
    cd "$TARGET_DIR"
    if ./tools/pre-commit/validate-setup.sh; then
        echo "✅ Environment validation passed"
    else
        echo "⚠️  Environment validation failed - manual setup may be required"
        ((validation_errors++))
    fi
else
    echo "⚠️  Cannot run environment validation - script missing"
    ((validation_errors++))
fi

echo ""
echo "📊 Transfer Summary"
echo "=================="

if [[ $validation_errors -eq 0 ]]; then
    echo "✅ Transfer completed successfully!"
    echo "✅ All essential files installed"
    echo "✅ Environment validation passed"
    echo ""
    echo "🎯 Quick Start:"
    echo "1. Validate setup: ./tools/pre-commit/validate-setup.sh"
    echo "2. Start development: ./tools/pre-commit/new-dev-branch.sh <device_name>"
    echo "3. Run quality check: ./tools/pre-commit/review-checker.py <file.c>"
    echo ""
    echo "📚 Documentation: See docs/quick-start-reference.md for daily workflows"
else
    echo "⚠️  Transfer completed with $validation_errors warnings"
    echo "📋 Manual setup may be required for some components"
    echo "📚 See docs/development-environment-setup.md for manual setup instructions"
fi

echo ""
echo "🚀 Development workflow ready!"
echo "📁 Workflow files transferred to: $TARGET_DIR"

# Optional: Clean up dev-workflow directory
read -p "🗑️  Remove dev-workflow transfer directory? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up transfer directory..."
    cd "$TARGET_DIR"
    rm -rf dev-workflow
    echo "✅ Transfer directory removed"
fi

echo ""
echo "✨ Transfer complete! Happy developing!"