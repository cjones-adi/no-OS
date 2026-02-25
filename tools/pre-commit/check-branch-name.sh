#!/bin/bash
# Branch name validation for no-OS development
# Enforces dev/<device_name> naming convention

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Get current branch name
current_branch=$(git branch --show-current)

# Skip validation for main/master and release branches
if [[ "$current_branch" =~ ^(main|master|20[0-9][0-9]_R[0-9]+)$ ]]; then
    echo_success "Branch name validation skipped for protected branch: $current_branch"
    exit 0
fi

# Check if branch follows dev/<device_name> pattern
if [[ "$current_branch" =~ ^dev/[a-z0-9][a-z0-9_-]*[a-z0-9]$ ]]; then
    echo_success "Branch name '$current_branch' follows naming convention"
    exit 0
fi

# Check for common valid patterns
valid_patterns=(
    "^dev/[a-z0-9]+$"                          # dev/adm1275
    "^dev/[a-z0-9]+-[a-z0-9]+$"                # dev/adm1275-eval
    "^dev/[a-z0-9]+-fix-[a-z0-9-]+$"          # dev/adm1275-fix-telemetry
    "^dev/[a-z0-9]+-[a-z]+$"                   # dev/adm1275-maxim
    "^dev/[a-z]+[0-9]+[a-z]*$"                 # dev/ad717x, dev/ltc2978a
)

for pattern in "${valid_patterns[@]}"; do
    if [[ "$current_branch" =~ $pattern ]]; then
        echo_success "Branch name '$current_branch' follows naming convention"
        exit 0
    fi
done

# Branch name doesn't follow convention
echo_error "Invalid branch name: '$current_branch'"
echo ""
echo "📋 Branch naming convention:"
echo "   dev/<device_name>           - For new device drivers"
echo "   dev/<family_name>           - For device families (e.g., ad717x)"
echo "   dev/<device>-<platform>     - For platform-specific work"
echo "   dev/<device>-fix-<issue>    - For bug fixes"
echo ""
echo "✅ Valid examples:"
echo "   dev/adm1275                 - ADM1275 PMBus monitor"
echo "   dev/ltc2978                 - LTC2978 power supply"
echo "   dev/ad7091r5                - AD7091R5 ADC"
echo "   dev/ad717x                  - AD717x family drivers"
echo "   dev/adm1275-maxim           - ADM1275 on MAX32655"
echo "   dev/adm1275-fix-telemetry   - Fix telemetry bug"
echo ""
echo "❌ Invalid examples:"
echo "   feature/add-adm1275         - Use dev/ prefix instead"
echo "   adm1275                     - Missing dev/ prefix"
echo "   dev/ADM1275                 - Use lowercase"
echo "   dev/my-device               - Use actual device name"
echo ""
echo "🔧 To rename your branch:"
echo "   git branch -m dev/$(echo '$current_branch' | sed 's/.*\///g' | tr '[:upper:]' '[:lower:]')"
echo ""

exit 1