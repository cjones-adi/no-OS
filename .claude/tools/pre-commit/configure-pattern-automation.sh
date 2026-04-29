#!/bin/bash
"""
Configure automated PR pattern updates.
Choose from multiple automation strategies based on your environment.
"""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} PR Pattern Automation Setup ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    echo "🔍 Checking dependencies..."

    # Check GitHub CLI
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) not found. Install from: https://cli.github.com/"
        exit 1
    fi

    # Check GitHub CLI auth
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI not authenticated. Run: gh auth login"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi

    print_success "All dependencies satisfied"
}

show_automation_options() {
    echo
    echo "📋 Choose your automation strategy:"
    echo
    echo "1. GitHub Actions (Recommended for repositories)"
    echo "   - Runs weekly on GitHub's infrastructure"
    echo "   - No local setup required"
    echo "   - Requires repository admin access"
    echo
    echo "2. Local Cron Jobs"
    echo "   - Runs on your local machine"
    echo "   - Works with forks and private repos"
    echo "   - Requires machine to be running"
    echo
    echo "3. Real-time Webhooks"
    echo "   - Updates immediately on PR events"
    echo "   - Requires server setup and webhook configuration"
    echo "   - Best for production repositories"
    echo
    echo "4. Manual Only"
    echo "   - Run updates manually as needed"
    echo "   - Full control over timing"
    echo "   - Minimal automation"
    echo
}

setup_github_actions() {
    echo "🔄 Setting up GitHub Actions automation..."

    # Check if we're in the main repository
    REMOTE_URL=$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || "")
    if [[ "$REMOTE_URL" != *"analogdevicesinc/no-OS"* ]]; then
        print_warning "This appears to be a fork. GitHub Actions should be set up in the main repository."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi

    # Create .github directory if it doesn't exist
    mkdir -p "$REPO_ROOT/.github/workflows"

    print_success "GitHub Actions workflow created at: .github/workflows/update-review-patterns.yml"
    echo
    echo "📋 Next steps:"
    echo "1. Commit and push the workflow file"
    echo "2. GitHub will run weekly updates automatically"
    echo "3. Manual runs available in Actions tab"
}

setup_local_cron() {
    echo "🔄 Setting up local cron job automation..."

    # Run the cron setup script
    "$SCRIPT_DIR/setup-auto-patterns.sh"

    print_success "Local cron automation configured"
    echo
    echo "📋 Next steps:"
    echo "1. Cron will run weekly updates (Mondays 9 AM)"
    echo "2. Check logs: tail -f /tmp/pattern_update.log"
    echo "3. Manual run: python3 $SCRIPT_DIR/auto-update-patterns.py"
}

setup_webhooks() {
    echo "🔄 Setting up real-time webhook automation..."

    # Check if Flask is available
    if ! python3 -c "import flask" 2>/dev/null; then
        print_warning "Flask not installed. Installing..."
        pip3 install flask || {
            print_error "Failed to install Flask. Install manually: pip3 install flask"
            return
        }
    fi

    # Make webhook server executable
    chmod +x "$SCRIPT_DIR/webhook-pattern-server.py"

    echo
    echo "📋 Webhook server configuration:"
    echo
    echo "1. Start webhook server:"
    echo "   python3 $SCRIPT_DIR/webhook-pattern-server.py"
    echo
    echo "2. Configure GitHub webhook (repository admin required):"
    echo "   - URL: http://your-server:5000/webhook/github"
    echo "   - Content type: application/json"
    echo "   - Events: Pull requests, Pull request reviews"
    echo "   - Secret: Set GITHUB_WEBHOOK_SECRET environment variable"
    echo
    echo "3. Test webhook:"
    echo "   curl -X GET http://localhost:5000/status"

    print_warning "Webhook setup requires manual GitHub configuration"
}

setup_manual_only() {
    echo "🔄 Setting up manual-only mode..."

    chmod +x "$SCRIPT_DIR/auto-update-patterns.py"

    print_success "Manual mode configured"
    echo
    echo "📋 Manual commands:"
    echo "  Update patterns:         python3 $SCRIPT_DIR/auto-update-patterns.py"
    echo "  Force full re-analysis:  python3 $SCRIPT_DIR/auto-update-patterns.py --full"
    echo "  Check current patterns:  wc -l review_patterns_6month.json"
}

show_status() {
    echo
    echo "📊 Current status:"
    echo

    # Check pattern file
    if [[ -f "$REPO_ROOT/review_patterns_6month.json" ]]; then
        SIZE=$(wc -c < "$REPO_ROOT/review_patterns_6month.json")
        MODIFIED=$(stat -c %y "$REPO_ROOT/review_patterns_6month.json" 2>/dev/null || stat -f %Sm "$REPO_ROOT/review_patterns_6month.json" 2>/dev/null || "unknown")
        echo "  Patterns file: ${SIZE} bytes, modified: ${MODIFIED}"

        # Show pattern counts
        python3 -c "
import json
try:
    with open('$REPO_ROOT/review_patterns_6month.json') as f:
        data = json.load(f)
    print(f\"  Total PRs: {data['analysis_scope']['total_prs']}\")
    print(f\"  Total comments: {data['analysis_scope']['total_comments']}\")
    print('  Top categories:')
    for cat, count in sorted(data['category_counts'].items(), key=lambda x: x[1], reverse=True)[:3]:
        percentage = count / data['analysis_scope']['total_comments'] * 100
        print(f\"    {cat}: {count} ({percentage:.1f}%)\")
except:
    print('  Could not parse patterns file')
"
    else
        print_error "  No patterns file found"
    fi

    # Check cron jobs
    if command -v crontab &> /dev/null && crontab -l 2>/dev/null | grep -q "pattern"; then
        echo "  Cron job: ✅ Active"
    else
        echo "  Cron job: ❌ Not configured"
    fi

    # Check GitHub Actions
    if [[ -f "$REPO_ROOT/.github/workflows/update-review-patterns.yml" ]]; then
        echo "  GitHub Actions: ✅ Workflow exists"
    else
        echo "  GitHub Actions: ❌ Not configured"
    fi
}

main() {
    print_header

    check_dependencies

    show_status

    show_automation_options

    read -p "Select option (1-4): " -n 1 -r
    echo
    echo

    case $REPLY in
        1)
            setup_github_actions
            ;;
        2)
            setup_local_cron
            ;;
        3)
            setup_webhooks
            ;;
        4)
            setup_manual_only
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac

    echo
    print_success "Setup complete!"
    echo
    echo "🔧 To reconfigure: $0"
    echo "📊 To check status: python3 $SCRIPT_DIR/auto-update-patterns.py --status"
}

# Add status flag
if [[ "$1" == "--status" ]]; then
    check_dependencies
    show_status
    exit 0
fi

main