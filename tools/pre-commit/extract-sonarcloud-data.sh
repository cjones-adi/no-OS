#!/bin/bash
# Extract SonarCloud data for Claude analysis
# Usage: ./extract-sonarcloud-data.sh <project_key> [branch]

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
    echo "Extract SonarCloud data for Claude analysis"
    echo ""
    echo "Usage: $0 <project_key> [branch] [token]"
    echo ""
    echo "Arguments:"
    echo "  project_key    SonarCloud project key (e.g., cjones-adi_no-OS)"
    echo "  branch         Branch to analyze (default: main)"
    echo "  token          SonarCloud token (optional, uses environment SONAR_TOKEN)"
    echo ""
    echo "Examples:"
    echo "  $0 cjones-adi_no-OS"
    echo "  $0 cjones-adi_no-OS main"
    echo "  $0 cjones-adi_no-OS main YOUR_SONAR_TOKEN"
    echo ""
    echo "Environment variables:"
    echo "  SONAR_TOKEN    Your SonarCloud authentication token"
    echo ""
}

extract_issues() {
    local project_key="$1"
    local branch="$2"
    local token="$3"
    local auth_header=""

    if [ -n "$token" ]; then
        auth_header="-H \"Authorization: Bearer $token\""
    fi

    echo_info "Extracting issues for project: $project_key (branch: $branch)"

    # SonarCloud API endpoints
    local base_url="https://sonarcloud.io/api"

    # Extract issues
    echo_info "Fetching issues..."
    local issues_url="$base_url/issues/search?componentKeys=$project_key&branch=$branch&resolved=false&ps=500"

    if [ -n "$token" ]; then
        curl -s -H "Authorization: Bearer $token" "$issues_url" > "sonarcloud-issues.json"
    else
        curl -s "$issues_url" > "sonarcloud-issues.json"
    fi

    if [ $? -eq 0 ] && [ -s "sonarcloud-issues.json" ]; then
        echo_success "Issues extracted to sonarcloud-issues.json"
    else
        echo_warning "Failed to extract issues (may need authentication)"
    fi

    # Extract measures (quality metrics)
    echo_info "Fetching quality measures..."
    local measures_url="$base_url/measures/component?component=$project_key&branch=$branch&metricKeys=ncloc,complexity,duplicated_lines_density,coverage,sqale_rating,reliability_rating,security_rating"

    if [ -n "$token" ]; then
        curl -s -H "Authorization: Bearer $token" "$measures_url" > "sonarcloud-measures.json"
    else
        curl -s "$measures_url" > "sonarcloud-measures.json"
    fi

    if [ $? -eq 0 ] && [ -s "sonarcloud-measures.json" ]; then
        echo_success "Measures extracted to sonarcloud-measures.json"
    else
        echo_warning "Failed to extract measures"
    fi

    # Try to get project status
    echo_info "Fetching project quality gate status..."
    local qualitygate_url="$base_url/qualitygates/project_status?projectKey=$project_key&branch=$branch"

    if [ -n "$token" ]; then
        curl -s -H "Authorization: Bearer $token" "$qualitygate_url" > "sonarcloud-qualitygate.json"
    else
        curl -s "$qualitygate_url" > "sonarcloud-qualitygate.json"
    fi

    if [ $? -eq 0 ] && [ -s "sonarcloud-qualitygate.json" ]; then
        echo_success "Quality gate status extracted to sonarcloud-qualitygate.json"
    else
        echo_warning "Failed to extract quality gate status"
    fi
}

generate_claude_summary() {
    local project_key="$1"
    local branch="$2"

    echo_info "Generating Claude-friendly summary..."

    cat > "claude-sonar-analysis.md" << EOF
# SonarCloud Analysis for Claude Review

**Project:** $project_key
**Branch:** $branch
**Generated:** $(date)
**SonarCloud URL:** https://sonarcloud.io/summary/new_code?id=$project_key&branch=$branch

## How to share this with Claude:

### Option 1: Share the summary below
Copy and paste the following analysis into your conversation with Claude.

### Option 2: Share specific files
- \`sonarcloud-issues.json\` - Detailed issues list
- \`sonarcloud-measures.json\` - Quality metrics
- \`sonarcloud-qualitygate.json\` - Quality gate status

### Option 3: Process with analyzer
\`\`\`bash
python3 tools/pre-commit/sonar-report-analyzer.py sonarcloud-issues.json --export-claude claude-review.json
\`\`\`

## Quick Summary

EOF

    # Parse basic info from issues file if it exists
    if [ -f "sonarcloud-issues.json" ]; then
        echo_info "Parsing issues summary..."
        python3 -c "
import json, sys
try:
    with open('sonarcloud-issues.json', 'r') as f:
        data = json.load(f)

    issues = data.get('issues', [])
    total = len(issues)

    by_severity = {}
    for issue in issues:
        severity = issue.get('severity', 'UNKNOWN')
        by_severity[severity] = by_severity.get(severity, 0) + 1

    print(f'**Total Issues:** {total}')
    print()
    print('**By Severity:**')
    for severity in ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']:
        count = by_severity.get(severity, 0)
        if count > 0:
            icon = '🔴' if severity in ['BLOCKER', 'CRITICAL'] else '🟡' if severity == 'MAJOR' else '🟢'
            print(f'- {icon} {severity}: {count} issues')

    # Top files with issues
    files = {}
    for issue in issues:
        file_path = issue.get('component', '').replace('project:', '')
        files[file_path] = files.get(file_path, 0) + 1

    if files:
        print()
        print('**Top Files with Issues:**')
        sorted_files = sorted(files.items(), key=lambda x: x[1], reverse=True)
        for file_path, count in sorted_files[:5]:
            print(f'- {file_path}: {count} issues')

except Exception as e:
    print(f'Error parsing issues: {e}')
" >> "claude-sonar-analysis.md"
    fi

    # Add quality measures if available
    if [ -f "sonarcloud-measures.json" ]; then
        echo_info "Adding quality measures..."
        echo "" >> "claude-sonar-analysis.md"
        echo "## Quality Metrics" >> "claude-sonar-analysis.md"
        echo "" >> "claude-sonar-analysis.md"

        python3 -c "
import json
try:
    with open('sonarcloud-measures.json', 'r') as f:
        data = json.load(f)

    measures = data.get('component', {}).get('measures', [])
    for measure in measures:
        metric = measure.get('metric', '')
        value = measure.get('value', 'N/A')

        # Format metrics nicely
        if metric == 'ncloc':
            print(f'- **Lines of Code:** {value}')
        elif metric == 'complexity':
            print(f'- **Complexity:** {value}')
        elif metric == 'duplicated_lines_density':
            print(f'- **Duplicated Lines:** {value}%')
        elif metric == 'coverage':
            print(f'- **Test Coverage:** {value}%')
        elif metric == 'sqale_rating':
            rating = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E'}.get(value, value)
            print(f'- **Maintainability:** {rating}')
        elif metric == 'reliability_rating':
            rating = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E'}.get(value, value)
            print(f'- **Reliability:** {rating}')
        elif metric == 'security_rating':
            rating = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E'}.get(value, value)
            print(f'- **Security:** {rating}')

except Exception as e:
    print(f'Error parsing measures: {e}')
" >> "claude-sonar-analysis.md"
    fi

    echo "" >> "claude-sonar-analysis.md"
    echo "---" >> "claude-sonar-analysis.md"
    echo "" >> "claude-sonar-analysis.md"
    echo "**Claude Analysis Request:**" >> "claude-sonar-analysis.md"
    echo "" >> "claude-sonar-analysis.md"
    echo "Hi Claude, please analyze this SonarCloud report for my no-OS repository. I'd like:" >> "claude-sonar-analysis.md"
    echo "1. Prioritized list of issues to fix" >> "claude-sonar-analysis.md"
    echo "2. Specific fix suggestions for top issues" >> "claude-sonar-analysis.md"
    echo "3. no-OS specific recommendations" >> "claude-sonar-analysis.md"
    echo "4. Integration suggestions with local pre-commit tools" >> "claude-sonar-analysis.md"
    echo "" >> "claude-sonar-analysis.md"

    echo_success "Claude summary generated: claude-sonar-analysis.md"
}

main() {
    if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage
        exit 0
    fi

    local project_key="$1"
    local branch="${2:-main}"
    local token="${3:-$SONAR_TOKEN}"

    echo_info "SonarCloud Data Extraction for Claude Analysis"
    echo_info "Project: $project_key"
    echo_info "Branch: $branch"
    echo ""

    if [ -z "$token" ]; then
        echo_warning "No authentication token provided"
        echo_info "Some endpoints may require authentication. Set SONAR_TOKEN environment variable or pass as argument"
        echo_info "Get token from: https://sonarcloud.io/account/security/"
        echo ""
    fi

    # Extract data
    extract_issues "$project_key" "$branch" "$token"

    # Generate Claude-friendly summary
    generate_claude_summary "$project_key" "$branch"

    echo ""
    echo_success "🎉 Data extraction completed!"
    echo ""
    echo_info "Files generated:"
    echo "  📄 claude-sonar-analysis.md (share this summary with Claude)"
    echo "  📊 sonarcloud-issues.json (detailed issues)"
    echo "  📈 sonarcloud-measures.json (quality metrics)"
    echo "  ✅ sonarcloud-qualitygate.json (quality gate status)"
    echo ""
    echo_info "Next steps:"
    echo "  1. Review claude-sonar-analysis.md"
    echo "  2. Copy/paste the content to Claude for analysis"
    echo "  3. Or use: python3 tools/pre-commit/sonar-report-analyzer.py sonarcloud-issues.json"
    echo ""
}

main "$@"