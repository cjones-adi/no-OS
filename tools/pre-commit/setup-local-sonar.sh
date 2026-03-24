#!/bin/bash
# Setup local SonarCloud scanner for no-OS development
# Allows analysis of development branches without affecting main branch

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

SONAR_VERSION="4.8.0.2856"
SONAR_DIR="sonar-scanner-${SONAR_VERSION}-linux"
SONAR_ZIP="${SONAR_DIR}.zip"
SONAR_URL="https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/${SONAR_ZIP}"

setup_directories() {
    echo_info "Setting up directories..."

    mkdir -p tools/sonar
    cd tools/sonar

    echo_success "Created tools/sonar directory"
}

download_scanner() {
    echo_info "Downloading SonarCloud scanner..."

    if [ -f "$SONAR_ZIP" ]; then
        echo_info "Scanner already downloaded, skipping..."
        return 0
    fi

    if command -v wget > /dev/null 2>&1; then
        wget "$SONAR_URL"
    elif command -v curl > /dev/null 2>&1; then
        curl -L -o "$SONAR_ZIP" "$SONAR_URL"
    else
        echo_error "Neither wget nor curl found. Please install one of them."
        exit 1
    fi

    echo_success "Scanner downloaded"
}

install_scanner() {
    echo_info "Installing scanner..."

    if [ ! -f "$SONAR_ZIP" ]; then
        echo_error "Scanner zip file not found"
        exit 1
    fi

    # Extract if not already extracted
    if [ ! -d "$SONAR_DIR" ]; then
        unzip -q "$SONAR_ZIP"
        echo_success "Scanner extracted"
    else
        echo_info "Scanner already extracted"
    fi

    # Make executable
    chmod +x "${SONAR_DIR}/bin/sonar-scanner"

    # Create symlink for easy access
    ln -sf "${SONAR_DIR}/bin/sonar-scanner" sonar-scanner

    echo_success "Scanner installed"
}

create_project_config() {
    echo_info "Creating project configuration..."

    # Go back to repo root
    cd ../..

    # Create sonar-project.properties
    cat > sonar-project.properties << EOF
# SonarCloud configuration for no-OS
sonar.projectKey=cjones-adi_no-OS
sonar.organization=cjones-adi

# Project metadata
sonar.projectName=no-OS
sonar.projectVersion=1.0
sonar.sourceEncoding=UTF-8

# Source directories and files
sonar.sources=drivers,include,util,iio
sonar.tests=tests

# File patterns
sonar.inclusions=**/*.c,**/*.h
sonar.exclusions=**/libraries/**,**/build/**,**/*.mk,**/tests/**

# Language settings
sonar.c.file.suffixes=.c
sonar.cpp.file.suffixes=.h

# Analysis settings
sonar.analysis.mode=publish
sonar.host.url=https://sonarcloud.io

# Quality settings
sonar.qualitygate.wait=false
EOF

    echo_success "Created sonar-project.properties"
}

create_scanner_script() {
    echo_info "Creating scanner scripts..."

    # Create main scanner script
    cat > tools/pre-commit/run-local-sonar.sh << 'EOF'
#!/bin/bash
# Run local SonarCloud analysis on development branch

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

usage() {
    echo "Run SonarCloud analysis on local development branch"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --changed-only     Analyze only files changed vs upstream/main"
    echo "  --preview         Run in preview mode (no upload to SonarCloud)"
    echo "  --export FILE     Export results to file for Claude review"
    echo "  --help           Show this help"
    echo ""
    echo "Environment variables:"
    echo "  SONAR_TOKEN      Your SonarCloud authentication token"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Full analysis"
    echo "  $0 --changed-only                     # Only changed files"
    echo "  $0 --preview --export claude-report.json  # Preview + export"
}

check_prerequisites() {
    echo_info "Checking prerequisites..."

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo_error "Not in a git repository"
        exit 1
    fi

    # Check for scanner
    if [ ! -f "tools/sonar/sonar-scanner" ]; then
        echo_error "SonarCloud scanner not found. Run ./tools/pre-commit/setup-local-sonar.sh first"
        exit 1
    fi

    # Check for token
    if [ -z "$SONAR_TOKEN" ]; then
        echo_error "SONAR_TOKEN environment variable not set"
        echo_info "Set your token: export SONAR_TOKEN=your_token"
        exit 1
    fi

    # Check for sonar-project.properties
    if [ ! -f "sonar-project.properties" ]; then
        echo_error "sonar-project.properties not found"
        echo_info "Run ./tools/pre-commit/setup-local-sonar.sh to create it"
        exit 1
    fi

    echo_success "Prerequisites check passed"
}

get_changed_files() {
    echo_info "Getting changed files vs upstream/main..."

    # Fetch upstream if it exists
    if git remote get-url upstream > /dev/null 2>&1; then
        git fetch upstream main > /dev/null 2>&1 || true
        BASE_BRANCH="upstream/main"
    else
        BASE_BRANCH="origin/main"
    fi

    # Get changed files
    changed_files=$(git diff --name-only "$BASE_BRANCH"...HEAD | grep -E '\.(c|h)$' | tr '\n' ',' | sed 's/,$//')

    if [ -z "$changed_files" ]; then
        echo_warning "No C/C++ files changed vs $BASE_BRANCH"
        return 1
    fi

    echo_success "Found changed files: $changed_files"
    echo "$changed_files"
}

run_analysis() {
    local mode="$1"
    local changed_only="$2"
    local export_file="$3"

    echo_info "Running SonarCloud analysis..."

    # Prepare scanner arguments
    scanner_args=("-Dsonar.login=$SONAR_TOKEN")

    if [ "$mode" = "preview" ]; then
        scanner_args+=("-Dsonar.analysis.mode=preview")
        echo_info "Running in preview mode (no upload)"
    fi

    if [ "$changed_only" = "true" ]; then
        changed_files=$(get_changed_files)
        if [ $? -eq 0 ] && [ -n "$changed_files" ]; then
            scanner_args+=("-Dsonar.inclusions=$changed_files")
            echo_info "Analyzing only changed files"
        else
            echo_warning "No changed files found, analyzing all files"
        fi
    fi

    # Add export path if specified
    if [ -n "$export_file" ]; then
        scanner_args+=("-Dsonar.report.export.path=$export_file")
        echo_info "Will export results to: $export_file"
    fi

    # Run the scanner
    echo_info "Executing scanner..."
    current_branch=$(git branch --show-current)
    echo_info "Branch: $current_branch"

    # Add branch info if not main
    if [ "$current_branch" != "main" ]; then
        scanner_args+=("-Dsonar.branch.name=$current_branch")
    fi

    # Execute scanner
    ./tools/sonar/sonar-scanner "${scanner_args[@]}"

    echo_success "Analysis completed"
}

process_results() {
    local export_file="$1"

    if [ -n "$export_file" ] && [ -f "$export_file" ]; then
        echo_info "Processing results for Claude review..."

        # Use our analyzer if available
        if [ -f "tools/pre-commit/sonar-report-analyzer.py" ]; then
            python3 tools/pre-commit/sonar-report-analyzer.py "$export_file" --export-claude "claude-sonar-review.json"
            echo_success "Claude review file generated: claude-sonar-review.json"
        fi
    fi
}

main() {
    local mode="publish"
    local changed_only="false"
    local export_file=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --changed-only)
                changed_only="true"
                shift
                ;;
            --preview)
                mode="preview"
                shift
                ;;
            --export)
                export_file="$2"
                shift 2
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                echo_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    echo_info "🔍 Local SonarCloud Analysis"
    echo ""

    check_prerequisites
    run_analysis "$mode" "$changed_only" "$export_file"
    process_results "$export_file"

    echo ""
    echo_success "🎉 Analysis completed!"

    if [ "$mode" = "preview" ]; then
        echo_info "Results are local only (preview mode)"
    else
        echo_info "Results uploaded to SonarCloud"
    fi

    if [ -f "claude-sonar-review.json" ]; then
        echo_info "📄 Share claude-sonar-review.json with Claude for detailed analysis"
    fi
}

main "$@"
EOF

    chmod +x tools/pre-commit/run-local-sonar.sh
    echo_success "Created tools/pre-commit/run-local-sonar.sh"

    # Create quick analysis script
    cat > tools/pre-commit/quick-sonar-check.sh << 'EOF'
#!/bin/bash
# Quick SonarCloud analysis of changed files only (preview mode)

export SONAR_TOKEN="${SONAR_TOKEN:-92225eb7678387de74ed8914019e259f64b6f47d}"

echo "🚀 Quick SonarCloud check on your changes..."

./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export sonar-changes.json

if [ -f "sonar-changes.json" ]; then
    echo ""
    echo "📊 Quick Summary:"
    python3 -c "
import json
try:
    with open('sonar-changes.json', 'r') as f:
        data = json.load(f)

    issues = data.get('issues', [])
    if not issues:
        print('✅ No issues found in your changes!')
    else:
        print(f'Found {len(issues)} issues in your changes:')

        by_severity = {}
        for issue in issues:
            severity = issue.get('severity', 'UNKNOWN')
            by_severity[severity] = by_severity.get(severity, 0) + 1

        for severity in ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']:
            if severity in by_severity:
                icon = '🔴' if severity in ['BLOCKER', 'CRITICAL'] else '🟡' if severity == 'MAJOR' else '🟢'
                print(f'  {icon} {severity}: {by_severity[severity]} issues')

except Exception as e:
    print(f'Error processing results: {e}')
"

    echo ""
    echo "💡 For detailed analysis, share sonar-changes.json with Claude"
fi
EOF

    chmod +x tools/pre-commit/quick-sonar-check.sh
    echo_success "Created tools/pre-commit/quick-sonar-check.sh"
}

create_integration() {
    echo_info "Creating integration with existing tools..."

    # Update pre-commit hook to include optional sonar check
    if [ -f "tools/pre-commit/pre-commit" ]; then
        echo_info "Adding SonarCloud integration to pre-commit hook..."

        # Add to pre-commit-config.example
        if [ -f "tools/pre-commit/pre-commit-config.example" ]; then
            cat >> tools/pre-commit/pre-commit-config.example << 'EOF'

# SonarCloud integration
ENABLE_SONAR_CHECK=false     # Local SonarCloud analysis (optional)
SONAR_MODE=preview          # preview or publish
SONAR_CHANGED_ONLY=true     # Analyze only changed files vs upstream
EOF
        fi
    fi

    echo_success "Integration completed"
}

verify_installation() {
    echo_info "Verifying installation..."

    # Check scanner executable
    if [ -x "tools/sonar/sonar-scanner" ]; then
        echo_success "Scanner executable: ✅"
    else
        echo_error "Scanner not executable"
        return 1
    fi

    # Check configuration
    if [ -f "sonar-project.properties" ]; then
        echo_success "Project configuration: ✅"
    else
        echo_error "Project configuration missing"
        return 1
    fi

    # Check scripts
    if [ -x "tools/pre-commit/run-local-sonar.sh" ]; then
        echo_success "Scanner script: ✅"
    else
        echo_error "Scanner script not executable"
        return 1
    fi

    echo_success "Installation verified"
}

main() {
    echo_info "🔧 Setting up Local SonarCloud Scanner"
    echo_info "This will install SonarCloud scanner for local development branch analysis"
    echo ""

    setup_directories
    download_scanner
    install_scanner
    create_project_config
    create_scanner_script
    create_integration
    verify_installation

    echo ""
    echo_success "🎉 Local SonarCloud Scanner setup completed!"
    echo ""
    echo_info "📋 What was installed:"
    echo "  • SonarCloud scanner (tools/sonar/)"
    echo "  • Project configuration (sonar-project.properties)"
    echo "  • Analysis scripts (tools/pre-commit/run-local-sonar.sh)"
    echo "  • Quick check script (tools/pre-commit/quick-sonar-check.sh)"
    echo ""
    echo_info "🚀 Quick start:"
    echo "  1. Set token: export SONAR_TOKEN=92225eb7678387de74ed8914019e259f64b6f47d"
    echo "  2. Quick check: ./tools/pre-commit/quick-sonar-check.sh"
    echo "  3. Full analysis: ./tools/pre-commit/run-local-sonar.sh --changed-only"
    echo ""
    echo_info "💡 The scanner will only analyze YOUR changes vs upstream/main"
    echo_info "💡 Use --preview mode to avoid uploading to SonarCloud"
    echo ""
}

main "$@"