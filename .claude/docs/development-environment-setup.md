# Development Environment Setup Guide

Complete guide for setting up the enhanced no-OS development environment with automated quality tools and AI integration.

## 📊 What You're Getting

**Enhanced QA System Based on 6-Month Analysis:**
- **144 PRs analyzed** (Aug 2025 - Feb 2026)
- **507 review comments** processed
- **62.5% issue prevention** coverage
- **AI-powered Claude Code integration** with datasheet analysis
- **Automated pattern updates** with 4 automation strategies

## 🔧 Prerequisites

### Required Software
```bash
# Git and GitHub CLI
sudo apt-get install git gh

# Python 3.9+
sudo apt-get install python3 python3-pip

# Development tools
sudo apt-get install build-essential

# Optional: AStyle for code formatting
wget "https://sourceforge.net/projects/astyle/files/astyle/astyle 3.1/astyle_3.1_linux.tar.gz"
tar -xzf astyle_3.1_linux.tar.gz
cd astyle/build/gcc && make -j$(nproc)
```

### GitHub Setup
```bash
# Authenticate GitHub CLI
gh auth login

# Verify access to no-OS repository
gh repo view analogdevicesinc/no-OS
```

## 🚀 Quick Setup (5 Minutes)

### 1. Repository Setup
```bash
# Fork analogdevicesinc/no-OS to YOUR_USERNAME/no-OS on GitHub

# Clone your fork
git clone https://github.com/YOUR_USERNAME/no-OS.git
cd no-OS

# Set up remotes (critical for tools)
git remote add upstream https://github.com/analogdevicesinc/no-OS.git
git remote set-url origin https://github.com/YOUR_USERNAME/no-OS.git

# Verify setup
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/no-OS.git (fetch/push)
# upstream  https://github.com/analogdevicesinc/no-OS.git (fetch/push)
```

### 2. Install Enhanced Development Tools
```bash
# Install all hooks and tools in one command
./tools/pre-commit/install-hooks.sh

# Validate environment
./tools/pre-commit/validate-setup.sh
# Should show "✅ Enhanced QA tools with 6-month analysis"
```

### 3. Configure Pattern Automation
```bash
# Choose automation strategy (GitHub Actions recommended)
./tools/pre-commit/configure-pattern-automation.sh
# Select option 1 for GitHub Actions (most users)
```

### 4. Optional: SonarCloud Setup
```bash
# Set up local SonarCloud scanner
./tools/pre-commit/setup-local-sonar.sh

# Get token from https://sonarcloud.io/account/security/
export SONAR_TOKEN="your_sonarcloud_token_here"

# Make persistent
echo 'export SONAR_TOKEN="your_sonarcloud_token_here"' >> ~/.bashrc
```

## 📋 Detailed Components

### 1. Pre-commit Hook System
**Location**: `tools/pre-commit/`
**Purpose**: Automated quality checks on every commit

**Components:**
- `install-hooks.sh` - One-command setup
- `pre-commit` - Main hook (AStyle, Cppcheck, review patterns, branch validation)
- `commit-msg` - Commit message format validation
- `review-checker.py` - Pattern detection with unused headers/variables
- `check-branch-name.sh` - Enforces `dev/<specific_device_name>` convention (Linux kernel principle)
- `validate-setup.sh` - Environment verification

**What it does:**
- ✅ **Code style**: Linux kernel style with 8-space tabs
- ✅ **Static analysis**: Cppcheck with no-OS configuration
- ✅ **Documentation**: Doxygen format validation
- ✅ **Branch naming**: Enforces `dev/<specific_device_name>` convention (no wildcards)
- ✅ **Review patterns**: Detects 62.5% of common issues
- ✅ **Build validation**: Ensures projects compile

### 2. Review Pattern Automation
**Location**: `tools/pre-commit/review-checker.py`
**Source**: 6-month analysis (144 PRs, 507 comments)
**Coverage**: 62.5% of historical review issues

**Top Patterns Detected:**
1. **Error Handling (107 occurrences, 21.1%)** - Null checks, return validation
2. **Documentation (62 occurrences, 12.2%)** - Doxygen format, completeness
3. **Type Safety (31 occurrences, 6.1%)** - Unsafe casts, buffer overflows
4. **Header Guards (24 occurrences, 4.7%)** - Format validation, includes
5. **Testing (22 occurrences, 4.3%)** - Coverage, edge cases
6. **Code Organization (21 occurrences, 4.1%)** - Modular design

**Enhanced Features:**
- **Unused Headers Detection**: Identifies potentially unused #include statements
- **Unused Variables Detection**: Finds declared but unused local variables
- **Bit Operations**: Suggests `NO_OS_BIT`/`NO_OS_GENMASK` usage

### 3. Pattern Update Automation
**Purpose**: Keep review patterns automatically up-to-date

**4 Automation Strategies:**

#### GitHub Actions (Recommended)
```bash
# Setup
./tools/pre-commit/configure-pattern-automation.sh → Select 1

# Features
- Weekly automation (Mondays 9 AM UTC)
- Manual triggers in Actions tab
- Zero maintenance after setup
- Works on GitHub's infrastructure
```

#### Local Cron Jobs
```bash
# Setup
./tools/pre-commit/configure-pattern-automation.sh → Select 2

# Features
- Weekly cron job (Mondays 9 AM)
- Works with forks and private repos
- Full local control
- Logging to /tmp/pattern_update.log
```

#### Real-time Webhooks
```bash
# Setup
./tools/pre-commit/configure-pattern-automation.sh → Select 3

# Features
- Immediate updates on PR events
- Requires server setup
- Most responsive system
- Production-ready
```

#### Manual Only
```bash
# Setup
./tools/pre-commit/configure-pattern-automation.sh → Select 4

# Commands
python3 tools/pre-commit/auto-update-patterns.py          # Update
python3 tools/pre-commit/auto-update-patterns.py --full   # Full re-analysis
```

### 4. SonarCloud Integration
**Location**: `tools/pre-commit/run-local-sonar.sh`
**Purpose**: Advanced code quality analysis with AI integration

**Key Features:**
- **Changed-only analysis**: Analyzes only YOUR changes vs upstream/main
- **No baseline noise**: Ignores existing no-OS issues
- **Claude integration**: Export reports for AI analysis
- **Free tier friendly**: Unlimited preview mode usage

**Usage:**
```bash
# Quick check
./tools/pre-commit/quick-sonar-check.sh

# Full analysis with Claude export
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export analysis.json

# Process for Claude review
python3 tools/pre-commit/sonar-report-analyzer.py analysis.json --export-claude claude-review.json
```

### 5. Device Template Generator
**Location**: `tools/pre-commit/create-device-template.py`
**Purpose**: Generate optimized driver templates

**Capabilities:**
- **Device-specific templates**: ADC, PMBus, power management optimized
- **Project generation**: Complete CI-ready projects
- **Platform support**: MAX32655, Raspberry Pi 4, STM32, Xilinx
- **IIO integration**: Linux subsystem support

**Examples:**
```bash
# ADC device with project
python3 tools/pre-commit/create-device-template.py ad7980 adc --with-project

# PMBus device with specific commands
python3 tools/pre-commit/create-device-template.py adm1275 pmbus \
  --with-project \
  --commands read_vin,read_vout,read_iin,read_iout \
  --with-iio

# Power management device
python3 tools/pre-commit/create-device-template.py ltc2978 power --with-project
```

### 6. Unit Testing Framework
**Location**: `tests/drivers/<category>/<device>/`
**Framework**: Ceedling/Unity/CMock

**Features:**
- **Complete test infrastructure**: Mocking, coverage, reporting
- **Test support patterns**: PMBus testing, LINEAR format validation
- **Integration examples**: LTM4700 family demonstration (Linux-compliant naming)
- **Coverage reporting**: GCov integration with analysis

**Usage:**
```bash
cd tests/drivers/power/<device>/
ceedling summary                    # Validate configuration
ceedling clean clobber test:all     # Run complete test suite
ceedling gcov:all utils:gcov        # Generate coverage reports
```

## 🎯 Verification Checklist

### After Setup Verification
```bash
# 1. Environment validation
./tools/pre-commit/validate-setup.sh
# Should show: "✅ Enhanced QA tools with 6-month analysis"

# 2. Pattern detection version
python3 tools/pre-commit/review-checker.py --version
# Should show: "Based on 6-month analysis (144 PRs, 507 comments)"

# 3. Git hooks installed
ls -la .git/hooks/
# Should show: pre-commit, commit-msg (not .sample)

# 4. Pattern file exists
ls -la review_patterns_6month.json
# Should show: 23KB+ file with recent timestamp

# 5. SonarCloud works (if configured)
./tools/pre-commit/quick-sonar-check.sh
# Should show: analysis results without errors
```

### Test First Development Session
```bash
# 1. Create test branch
./tools/pre-commit/new-dev-branch.sh test-device

# 2. Generate template
python3 tools/pre-commit/create-device-template.py test-device adc

# 3. Test commit
git add drivers/adc/test-device/
git commit -s -m "test: add test device template"
# Should show: all quality checks passing

# 4. Clean up
git checkout main
git branch -D dev/ltm4700
```

## 🚀 Next Steps

### Start Development
1. **Choose workflow**: Claude Code AI-assisted OR manual workflow
2. **Read documentation**: `docs/claude-code-integration-guide.md` OR `docs/new-driver-workflow.md`
3. **Join support**: Ask questions in development channels
4. **Reference guide**: Use `docs/quick-start-reference.md` for daily commands

### For AI-Enhanced Development
```bash
# Start Claude Code session
claude-code

# Use enhanced prompt
"I need to develop a driver for the [DEVICE] [TYPE]"
```

### For Manual Development
```bash
# Follow manual workflow
./tools/pre-commit/new-dev-branch.sh <device>
python3 tools/pre-commit/create-device-template.py <device> <type> --with-project
```

## 🔧 Troubleshooting

### Common Issues

**"Upstream not configured"**
```bash
git remote add upstream https://github.com/analogdevicesinc/no-OS.git
```

**"GitHub CLI not authenticated"**
```bash
gh auth login
```

**"Pre-commit hook not running"**
```bash
./tools/pre-commit/install-hooks.sh
chmod +x .git/hooks/pre-commit
```

**"SonarCloud token issues"**
```bash
# Check token is set
echo $SONAR_TOKEN
# Set if missing
export SONAR_TOKEN="your_token_here"
```

**"Pattern file missing"**
```bash
# Regenerate patterns
python3 extract_review_patterns_6month.py
```

### Getting Help
- **Documentation**: Check `docs/` directory
- **Scripts help**: Most scripts have `--help` flags
- **Issues**: Report problems to repository maintainers
- **Validation**: Run `./tools/pre-commit/validate-setup.sh` for diagnostics

---

**Setup Time**: 5-10 minutes for complete environment
**Maintenance**: Zero (fully automated)
**Benefits**: 62.5% review issue prevention + AI-powered development