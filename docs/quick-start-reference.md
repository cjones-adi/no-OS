# Quick Start Reference Guide

Essential commands and workflows for no-OS driver development with enhanced QA tools.

## 🚀 Environment Setup

### Initial Repository Setup
```bash
# Fork analogdevicesinc/no-OS to YOUR_USERNAME/no-OS on GitHub

# Clone your fork and set up remotes
git clone https://github.com/YOUR_USERNAME/no-OS.git
cd no-OS
git remote add upstream https://github.com/analogdevicesinc/no-OS.git
git remote set-url origin https://github.com/YOUR_USERNAME/no-OS.git

# Install all development tools
./tools/pre-commit/install-hooks.sh

# Verify environment
./tools/pre-commit/validate-setup.sh
```

### SonarCloud Setup (Optional)
```bash
# Set up local SonarCloud scanner
./tools/pre-commit/setup-local-sonar.sh

# Set your token (get from https://sonarcloud.io/account/security/)
export SONAR_TOKEN="your_sonarcloud_token_here"
echo 'export SONAR_TOKEN="your_sonarcloud_token_here"' >> ~/.bashrc
```

## 🔧 Daily Development Commands

### Start New Device Development
```bash
# Sync with upstream and create branch
./tools/pre-commit/new-dev-branch.sh <specific_device_name>

# Generate device template with project
python3 tools/pre-commit/create-device-template.py <device> <type> --with-project

# Examples:
python3 tools/pre-commit/create-device-template.py ad7980 adc --with-project
python3 tools/pre-commit/create-device-template.py adm1275 pmbus --with-project \
  --commands read_vin,read_vout,read_iin,read_iout
```

### Quality Assurance Workflow
```bash
# Daily code quality check
./tools/pre-commit/quick-sonar-check.sh

# Enhanced review checker (detects 62.5% of common issues)
python3 tools/pre-commit/review-checker.py <file.c>

# Full SonarCloud analysis
export SONAR_TOKEN="your_sonarcloud_token_here"
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export analysis.json
```

### Build and Test
```bash
# Build specific project
python3 tools/scripts/build_projects.py . -project=<project_name>

# Build for multiple platforms
python3 tools/scripts/build_projects.py . -project=<project_name> -platform=xilinx
python3 tools/scripts/build_projects.py . -project=<project_name> -platform=stm32
```

### Unit Testing (Ceedling Framework)
```bash
# Navigate to driver test directory
cd tests/drivers/<category>/<device>/

# Validate configuration and run tests
ceedling summary                    # Validate configuration
ceedling clean clobber test:all     # Run complete test suite
ceedling gcov:all utils:gcov        # Generate coverage reports
```

## 📊 Pattern Automation (NEW)

### Setup Automated Pattern Updates
```bash
# Choose automation strategy (GitHub Actions, Cron, Webhooks, Manual)
./tools/pre-commit/configure-pattern-automation.sh

# Manual pattern updates
python3 tools/pre-commit/auto-update-patterns.py          # Incremental update
python3 tools/pre-commit/auto-update-patterns.py --full   # Force full re-analysis
./tools/pre-commit/configure-pattern-automation.sh --status # Check status
```

## 🤖 Enhanced Claude Code Workflow

### Starting a Claude Code Session
```bash
# Start Claude Code in your repository
claude-code

# Or use web interface at claude.ai/claude-code
```

### Essential Claude Prompts
```
# Start driver development
"I need to develop a driver for the [DEVICE] [TYPE]"

# PMBus device development
"I need to develop a driver for the ADM1275 PMBus power monitoring IC"

# Analyze existing code
"Run SonarCloud analysis on my changes"

# Quality assistance
"Check my driver against no-OS review patterns"
```

## 🌿 Git Workflow

### Branch Management
```bash
# Sync with upstream before starting work
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main

# Branch naming convention: dev/<specific_device_name> (Linux kernel principle)
# ❌ AVOID: dev/ad717x, dev/ltm470x (generic/wildcard names)
# ✅ USE: dev/ad7175, dev/ltm4700 (specific device names)
git checkout -b dev/adm1275
```

### 🚨 Linux Driver Naming Principle
```bash
# Linux drivers must use explicit device names, never wildcards
# Device naming stability delegated to user space

# ❌ PROHIBITED patterns:
dev/ad717x          # Generic family name
dev/ltm470x         # Wildcard-style name
dev/power-device    # Category-based name

# ✅ CORRECT patterns:
dev/ltm4700         # Primary device (supports LTM4777 via chip_id)
dev/ad7175          # Specific device (supports AD7176/7177 via chip_id)
dev/adm1275         # Explicit device identification

# Family drivers use primary device name with chip_id detection
struct ltm4700_dev {
    uint8_t chip_id;    // 0x01=LTM4700, 0x02=LTM4777
    enum variant;       // Detected during init
};
```

### Commit Standards
```bash
# Signed commits required
git commit -s -m "drivers: power: adm1275: add initial driver implementation"

# Format: <scope>: <component>: <description>
# Examples:
git commit -s -m "drivers: adc: ad7980: fix initialization sequence"
git commit -s -m "projects: adm1275-eval: add evaluation board support"
git commit -s -m "docs: power: adm1275: add driver documentation"
```

### PR Workflow
```bash
# Before creating PR
git fetch upstream && git rebase upstream/main
git push origin dev/adm1275

# Create PR with GitHub CLI
gh pr create --repo analogdevicesinc/no-OS \
             --title "drivers: power: adm1275: add support for ADM1275 PMBus monitor" \
             --body "Add driver for ADM1275 digital power monitor..."
```

## 📁 Critical Files Reference

### Primary Documentation
- `CLAUDE.md` - Complete development guide
- `docs/claude-code-integration-guide.md` - AI-assisted workflow
- `docs/new-driver-workflow.md` - Manual workflow
- `docs/review-pattern-automation-guide.md` - Pattern automation

### QA System Files
- `review_patterns_6month.json` - 6-month analysis dataset (507 comments)
- `tools/pre-commit/review-checker.py` - Pattern detection (62.5% coverage)
- `docs/no-os-review-pattern-analysis.md` - Analysis documentation

### Configuration Files
- `.pre-commit-config` - Hook settings
- `sonar-project.properties` - SonarCloud configuration
- `tools/pre-commit/pre-commit-config.example` - Template settings

### Example Implementations
- `drivers/power/ltm4700/` - Complete family driver example (Linux-compliant naming)
- `projects/ltm4700-eval/` - CI-ready project with IIO
- `tests/drivers/power/ltm4700/` - Unit testing framework example

## 🎯 Platform-Specific Commands

### MAX32655 (Maxim) Platform
```bash
# Build for MAX32655
python3 tools/scripts/build_projects.py . -platform=maxim -project=<project>

# Platform-specific includes
INCS += $(PLATFORM_DRIVERS)/maxim_spi.h \
        $(PLATFORM_DRIVERS)/maxim_gpio.h
```

### Raspberry Pi 4 (Linux/IIO)
```bash
# Build IIO example
make EXAMPLE=iio_example

# IIO testing
cd projects/<device>-eval/src/examples/iio_example/
make
```

## 🔍 Common Issue Prevention

### Top Review Issues (Automated Detection)
1. **Error Handling (21.1%)** - Null checks, return validation
2. **Documentation (12.2%)** - Doxygen format, completeness
3. **Type Safety (6.1%)** - Unsafe casts, buffer overflows
4. **Header Guards (4.7%)** - Format validation, includes
5. **Testing (4.3%)** - Coverage, edge cases

### Pre-Commit Validation
```bash
# Automatic checks on every commit:
# ✅ Code style (AStyle 3.1, Linux kernel style)
# ✅ Static analysis (Cppcheck)
# ✅ Documentation validation
# ✅ Branch naming (dev/<specific_device_name> - no wildcards)
# ✅ Review pattern detection (62.5% coverage)
```

## 📚 Additional Resources

- **Build System**: `tools/scripts/build_projects.py --help`
- **Platform Support**: `docs/platform-guide.md`
- **Testing Framework**: `tests/README.md`
- **API Documentation**: http://analogdevicesinc.github.io/no-OS/doxygen/

---

**For AI-assisted development**: Use Claude Code with the prompt `"I need to develop a driver for the [DEVICE]"`
**For manual development**: Follow `docs/new-driver-workflow.md`
**For quality automation**: Run `./tools/pre-commit/configure-pattern-automation.sh`