# Local SonarCloud Scanner Guide

Complete guide for running SonarCloud analysis locally on your development branches without affecting the main branch.

## 🚀 Quick Setup

```bash
# 1. Run the setup script
./tools/pre-commit/setup-local-sonar.sh

# 2. Set your token
export SONAR_TOKEN="92225eb7678387de74ed8914019e259f64b6f47d"

# 3. Quick check of your changes
./tools/pre-commit/quick-sonar-check.sh
```

## 📋 What Gets Installed

The setup script installs:

- **SonarCloud Scanner** (`tools/sonar/sonar-scanner`) - Local analysis engine
- **Project Configuration** (`sonar-project.properties`) - Your project settings
- **Analysis Scripts** (`run-local-sonar.sh`, `quick-sonar-check.sh`) - Easy-to-use commands
- **Integration** - Works with existing pre-commit tools

## 🔧 Usage Scenarios

### Scenario 1: Quick Check During Development

**Perfect for:** Daily development, checking your changes before commit

```bash
# Check only files you've changed
./tools/pre-commit/quick-sonar-check.sh

# Output:
# 🚀 Quick SonarCloud check on your changes...
# ✅ No issues found in your changes!
# OR
# Found 3 issues in your changes:
#   🔴 CRITICAL: 1 issues
#   🟡 MAJOR: 2 issues
```

### Scenario 2: Full Dev Branch Analysis

**Perfect for:** Pre-PR analysis, comprehensive review

```bash
# Analyze only changed files vs upstream/main
export SONAR_TOKEN="92225eb7678387de74ed8914019e259f64b6f47d"
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export my-analysis.json

# For Claude review
python3 tools/pre-commit/sonar-report-analyzer.py my-analysis.json --export-claude claude-review.json
```

### Scenario 3: Full Repository Analysis

**Perfect for:** Major refactoring, baseline understanding

```bash
# Analyze entire repository (preview mode - no upload)
./tools/pre-commit/run-local-sonar.sh --preview --export full-analysis.json
```

## 📊 Analysis Modes

### Preview Mode (Recommended for Development)
```bash
# Runs analysis locally, no upload to SonarCloud
./tools/pre-commit/run-local-sonar.sh --preview
```

**Benefits:**
- ✅ No pollution of SonarCloud dashboard
- ✅ Unlimited analysis (no free tier limits)
- ✅ Perfect for development branches
- ✅ Generate reports for Claude review

### Publish Mode
```bash
# Uploads results to SonarCloud
./tools/pre-commit/run-local-sonar.sh
```

**Use when:**
- You want results in SonarCloud dashboard
- Final analysis before PR
- Sharing results with team

## 🎯 Focus on Your Changes Only

The key feature that solves your problem:

```bash
# This analyzes ONLY files you've changed vs upstream/main
./tools/pre-commit/run-local-sonar.sh --changed-only

# Ignores all existing no-OS baseline issues
# Focuses on issues YOU introduced
```

**How it works:**
1. Compares your branch vs `upstream/main`
2. Gets list of changed files: `git diff --name-only upstream/main...HEAD`
3. Tells SonarCloud to analyze only those files: `-Dsonar.inclusions=file1.c,file2.h`
4. Results show only issues in your changes

## 🔧 Advanced Usage

### Custom File Analysis
```bash
# Analyze specific files
./tools/pre-commit/run-local-sonar.sh --preview \
  -Dsonar.inclusions="drivers/power/adm1275/*,projects/adm1275-eval/*"
```

### Different Base Branch
```bash
# Compare against different branch
git diff --name-only origin/main...HEAD | grep -E '\.(c|h)$' | tr '\n' ',' > files.txt
./tools/pre-commit/run-local-sonar.sh --preview -Dsonar.inclusions="$(cat files.txt)"
```

### Export for Multiple Tools
```bash
# Export for both Claude and other tools
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export sonar-raw.json

# Process for Claude
python3 tools/pre-commit/sonar-report-analyzer.py sonar-raw.json --export-claude claude-review.json

# Process for dashboard
python3 tools/pre-commit/sonar-report-analyzer.py sonar-raw.json --format json > processed-report.json
```

## 🔍 Integration with Claude Review

### Step 1: Run Analysis
```bash
export SONAR_TOKEN="92225eb7678387de74ed8914019e259f64b6f47d"
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export my-changes.json
```

### Step 2: Generate Claude Report
```bash
python3 tools/pre-commit/sonar-report-analyzer.py my-changes.json --export-claude claude-review.json
```

### Step 3: Share with Claude
```
Hi Claude, I ran SonarCloud analysis on my development branch changes. Please review:

Context:
- Working on: [device name/feature]
- Branch: dev/device-name
- Only analyzing MY changes vs upstream/main
- Target platforms: MAX32655, Pi4

[Paste content of claude-review.json]

Please provide:
1. Priority ranking of issues
2. Specific fix suggestions
3. no-OS specific recommendations
4. Pre-commit tool improvements
```

## 🛠️ Troubleshooting

### Scanner Not Found
```bash
# Re-run setup
./tools/pre-commit/setup-local-sonar.sh

# Check installation
ls -la tools/sonar/sonar-scanner
```

### Token Issues
```bash
# Verify token is set
echo $SONAR_TOKEN

# Test token access
curl -H "Authorization: Bearer $SONAR_TOKEN" \
  "https://sonarcloud.io/api/authentication/validate"
```

### No Changes Detected
```bash
# Check what files changed
git diff --name-only upstream/main...HEAD

# Fetch upstream first
git fetch upstream
```

### Permission Issues
```bash
# Fix permissions
chmod +x tools/pre-commit/run-local-sonar.sh
chmod +x tools/pre-commit/quick-sonar-check.sh
chmod +x tools/sonar/sonar-scanner
```

## ⚡ Performance Tips

### Faster Analysis
```bash
# Analyze only C/H files in drivers you're working on
./tools/pre-commit/run-local-sonar.sh --preview \
  -Dsonar.inclusions="drivers/power/**/*.c,drivers/power/**/*.h"
```

### Exclude Large Directories
```bash
# Skip libraries and build artifacts (already in config)
# sonar.exclusions=**/libraries/**,**/build/**
```

## 🎯 Workflow Integration

### Pre-Commit Integration
Add to your development workflow:

```bash
# Before committing major changes
./tools/pre-commit/quick-sonar-check.sh

# Before creating PR
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export pr-analysis.json
python3 tools/pre-commit/sonar-report-analyzer.py pr-analysis.json --export-claude claude-review.json
# Share claude-review.json with Claude
```

### CI Integration (Future)
```yaml
# .github/workflows/sonar-local.yml (for your fork)
- name: Local SonarCloud Analysis
  run: |
    export SONAR_TOKEN=${{ secrets.SONAR_TOKEN }}
    ./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export results.json
```

---

## 🚀 Ready to Use!

Your local SonarCloud scanner setup gives you:

✅ **Analysis of only YOUR changes** (ignores baseline issues)
✅ **No git history pollution** (local analysis)
✅ **No free tier limitations** (preview mode)
✅ **Claude integration** (export reports for review)
✅ **Development workflow** (quick daily checks)

**Start with:** `./tools/pre-commit/quick-sonar-check.sh`