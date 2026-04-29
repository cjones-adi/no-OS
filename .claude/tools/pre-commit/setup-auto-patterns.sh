#!/bin/bash
"""
Setup automated pattern updates using cron jobs.
Alternative to GitHub Actions for local development environments.
"""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔧 Setting up automated review pattern updates..."

# Make scripts executable
chmod +x "$SCRIPT_DIR/auto-update-patterns.py"

# Create wrapper script for cron
cat > "$SCRIPT_DIR/cron-update-patterns.sh" << 'EOF'
#!/bin/bash
# Cron wrapper for pattern updates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

# Ensure git is clean
if ! git diff --quiet; then
    echo "❌ Repository has uncommitted changes. Skipping pattern update."
    exit 1
fi

# Update from upstream
git fetch upstream 2>/dev/null || git fetch origin 2>/dev/null || echo "Warning: Could not fetch updates"

# Run pattern update
echo "🔄 Running automated pattern update..."
python3 "$SCRIPT_DIR/auto-update-patterns.py" > /tmp/pattern_update.log 2>&1

# Check if patterns were updated
if git diff --quiet review_patterns_6month.json; then
    echo "ℹ️ No pattern updates needed"
else
    echo "✅ Patterns updated, committing changes..."
    git add review_patterns_6month.json .review_patterns_state.json 2>/dev/null || true
    git commit -m "auto: update review patterns ($(date +%Y-%m-%d))

    Automated weekly update of PR review patterns
    - Maintains rolling 6-month analysis window
    - Added new comments from recent merged PRs

    Co-Authored-By: Automated Pattern Updater <noreply@analogdevices.com>"
fi

echo "📊 Pattern update complete"
EOF

chmod +x "$SCRIPT_DIR/cron-update-patterns.sh"

# Check if cron is available
if ! command -v crontab &> /dev/null; then
    echo "⚠️ cron not available. Manual setup required."
    echo "📋 To manually run updates: $SCRIPT_DIR/cron-update-patterns.sh"
    exit 0
fi

# Setup cron job (weekly on Monday at 9 AM)
CRON_JOB="0 9 * * 1 $SCRIPT_DIR/cron-update-patterns.sh >> /tmp/pattern_update.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "cron-update-patterns.sh"; then
    echo "ℹ️ Cron job already exists"
else
    echo "📅 Setting up weekly cron job (Mondays at 9 AM)..."
    (crontab -l 2>/dev/null || true; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added"
fi

echo ""
echo "🎯 Setup complete!"
echo ""
echo "📋 What's been configured:"
echo "  ✅ Incremental update script: $SCRIPT_DIR/auto-update-patterns.py"
echo "  ✅ Cron wrapper: $SCRIPT_DIR/cron-update-patterns.sh"
echo "  ✅ Weekly cron job: Mondays at 9 AM"
echo "  ✅ Log file: /tmp/pattern_update.log"
echo ""
echo "🔧 Manual commands:"
echo "  Update patterns now:     python3 $SCRIPT_DIR/auto-update-patterns.py"
echo "  Force full re-analysis:  python3 $SCRIPT_DIR/auto-update-patterns.py --full"
echo "  Check cron jobs:         crontab -l"
echo "  View logs:               tail -f /tmp/pattern_update.log"
echo ""
echo "📊 Current patterns: $(wc -c < review_patterns_6month.json) bytes"