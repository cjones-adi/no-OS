# no-OS Driver Development Workflow

Complete workflow for creating a new no-OS driver using the automated development tools and quality checks.

## Overview

This guide walks through the complete process of developing a new driver for the no-OS repository, leveraging the automated tools to minimize review iterations and ensure code quality from day one.

**Target Audience:** Driver developers working on ADI hardware peripherals
**Development Focus:** Power management devices (ADC, PMBus) for MAX32655 and Raspberry Pi 4 platforms
**Repository Setup:** Fork-based workflow (upstream/origin)

---

## 🔧 Prerequisites

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

### 2. Install Development Tools
```bash
# Install all hooks and tools in one command
./tools/pre-commit/install-hooks.sh

# Validate environment
./tools/pre-commit/validate-setup.sh
```

### 3. Configure SonarCloud (Optional but Recommended)
```bash
# Set up local SonarCloud scanner
./tools/pre-commit/setup-local-sonar.sh

# Set your token (get from https://sonarcloud.io/account/security/)
export SONAR_TOKEN="your_token_here"

# Add to ~/.bashrc for persistence
echo 'export SONAR_TOKEN="your_token_here"' >> ~/.bashrc
```

---

## 🚀 Development Workflow

### Step 1: Sync and Create Development Branch

```bash
# Always start with latest upstream
git checkout main
git fetch upstream
git rebase upstream/main
git push origin main

# Create properly named development branch
./tools/pre-commit/new-dev-branch.sh ad7980
# → Creates and switches to dev/ad7980
# → Validates upstream sync
# → Suggests device type and templates
```

**Branch naming enforced:** `dev/<device_name>` format
**Automatic detection:** Script suggests ADC/PMBus templates based on device name

### Step 2: Generate Device Template

Based on the device type detected by the branch creation script:

```bash
# For ADC devices (power management optimized)
python3 tools/pre-commit/create-device-template.py ad7980 adc --with-project

# For PMBus devices (full command set + telemetry)
python3 tools/pre-commit/create-device-template.py adm1275 pmbus --with-project

# For power management devices
python3 tools/pre-commit/create-device-template.py ltc2978 power --with-project
```

**What gets created:**
- ✅ Driver files: `drivers/<category>/<device>/<device>.h/.c`
- ✅ Project files: `projects/<device>-eval/` (MAX32655 + Pi4 support)
- ✅ IIO integration for Linux compatibility
- ✅ Device-specific documentation templates
- ✅ Platform abstraction examples

### Step 3: Development with Continuous Quality Checks

```bash
# Make your changes
vim drivers/adc/ad7980/ad7980.c

# Quick quality check during development
./tools/pre-commit/quick-sonar-check.sh
# → Analyzes only YOUR changes vs upstream/main
# → Shows immediate feedback on code quality

# Check for review patterns manually
python3 tools/pre-commit/review-checker.py drivers/adc/ad7980/ad7980.c
# → Detects common PR issues before submission
```

### Step 4: Commit with Automatic Quality Gates

```bash
# Stage your changes
git add drivers/adc/ad7980/

# Commit (triggers all automated checks)
git commit -s -m "drivers: adc: ad7980: add initial driver implementation"

# Automated checks run:
# ✅ Branch naming validation (dev/ad7980)
# ✅ Code style (AStyle - Linux kernel style)
# ✅ Static analysis (Cppcheck)
# ✅ Documentation validation (Doxygen format)
# ✅ Review pattern detection (common PR issues)
# ✅ Build validation (optional)
```

**If hooks fail:**
```bash
# Fix style issues
./build/astyle/build/gcc/bin/astyle --options=ci/astyle_config drivers/adc/ad7980/ad7980.c

# Fix static analysis warnings
# (Address Cppcheck warnings in code)

# Fix review patterns
# (Address suggestions from review-checker.py)

# Re-commit
git add drivers/adc/ad7980/ad7980.c
git commit --amend --no-edit
```

### Step 5: Pre-PR Quality Analysis

```bash
# Comprehensive analysis before creating PR
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export pr-analysis.json

# Generate Claude review report
python3 tools/pre-commit/sonar-report-analyzer.py pr-analysis.json --export-claude claude-review.json

# Review results yourself first
cat claude-review.json
```

### Step 6: Push and Create Pull Request

```bash
# Push to your fork
git push origin dev/ad7980

# Create PR using GitHub CLI (recommended)
gh pr create --repo analogdevicesinc/no-OS \
  --title "drivers: adc: ad7980: add support for AD7980 18-bit ADC" \
  --body "$(cat << 'EOF'
## Summary
Add driver support for AD7980 18-bit SAR ADC for power management applications.

## Changes
- Initial driver implementation with standard no-OS API
- Support for MAX32655 and Raspberry Pi 4 platforms
- IIO integration for Linux compatibility
- Comprehensive documentation and examples

## Testing
- [x] Code style validation (AStyle)
- [x] Static analysis (Cppcheck)
- [x] Review pattern analysis (185-pattern database)
- [x] Local SonarCloud analysis
- [ ] Hardware testing on MAX32655 platform
- [ ] Hardware testing on Raspberry Pi 4

## Device Details
- 18-bit resolution SAR ADC
- 1 MSPS conversion rate
- SPI interface
- Power management applications

Signed-off-by: Your Name <your.email@analog.com>
EOF
)"
```

---

## 🎯 Quality Assurance Features

### Automated Prevention of Common Issues

Based on analysis of 50 merged PRs with 185 review comments:

| Issue Category | Auto-Detection | Prevention Method |
|---|---|---|
| **Error Handling** (30 occurrences) | ✅ Pattern matching | Detects missing null checks, return value validation |
| **Documentation** (18 occurrences) | ✅ Format validation | Enforces Doxygen comments, parameter documentation |
| **Header Guards** (9 occurrences) | ✅ Format checking | Validates `#ifndef DEVICE_H_` patterns |
| **Magic Numbers** (9 occurrences) | ✅ Constant detection | Suggests `#define` for hardcoded values |
| **Type Safety** (5 occurrences) | ✅ Cast analysis | Detects unsafe pointer casts |
| **Naming Conventions** (6 occurrences) | ✅ Prefix validation | Enforces device prefix in function names |
| **Bit Operations** | ✅ Macro detection | Suggests `NO_OS_BIT()` usage |

### SonarCloud Integration Benefits

✅ **Changed Files Only:** Analyzes only your modifications vs upstream/main
✅ **No Git History Pollution:** Local analysis, no merge/revert needed
✅ **Unlimited Analysis:** Preview mode bypasses free tier limitations
✅ **Claude Integration:** Export reports for detailed AI review

---

## 🔍 Troubleshooting

### Hook Failures

**Branch naming rejected:**
```bash
# Current branch: feature/new-adc
# Error: Branch name must follow 'dev/<device_name>' format

git checkout main
./tools/pre-commit/new-dev-branch.sh ad7980  # Creates dev/ad7980
git cherry-pick feature/new-adc  # Move your changes
```

**AStyle formatting issues:**
```bash
# Fix automatically
git diff --cached --name-only | grep -E '\.(c|h)$' | \
  xargs ./build/astyle/build/gcc/bin/astyle --options=ci/astyle_config

git add .
git commit --amend --no-edit
```

**Cppcheck warnings:**
```bash
# Review specific warnings
cppcheck --enable=all drivers/adc/ad7980/ad7980.c

# Common fixes:
# - Add null pointer checks
# - Initialize variables before use
# - Handle all return values
```

### SonarCloud Issues

**Scanner not found:**
```bash
./tools/pre-commit/setup-local-sonar.sh  # Re-run setup
```

**Token authentication:**
```bash
echo $SONAR_TOKEN  # Verify token is set
export SONAR_TOKEN="your_token"  # Set if missing
```

**No changes detected:**
```bash
git fetch upstream  # Update upstream reference
git diff --name-only upstream/main...HEAD  # Verify changes
```

---

## 🎛️ Configuration Options

### Custom Pre-commit Configuration

```bash
# Copy default configuration
cp tools/pre-commit/pre-commit-config.example .pre-commit-config

# Edit settings
nano .pre-commit-config
```

**Key settings for power management development:**
```bash
# Platform focus
BUILD_PLATFORMS="maxim"          # MAX32655 feather boards
MAXIM_PLATFORM_ONLY=true

# Device types
PMBUS_DEVICES="adm1266 adm1275 ltc2978"
POWER_MGMT_CHECKS=true

# Quality checks
ENABLE_BRANCH_CHECK=true         # Enforce dev/<device> naming
ENABLE_ASTYLE=true              # Code style validation
ENABLE_CPPCHECK=true            # Static analysis
ENABLE_REVIEW_CHECK=true        # Review pattern detection
ENABLE_BUILD_CHECK=false        # Build validation (slow)
```

### Device Template Customization

```bash
# ADC template with specific features
python3 tools/pre-commit/create-device-template.py ad7980 adc \
  --with-project \
  --platforms maxim,linux \
  --resolution 18 \
  --interface spi

# PMBus template with telemetry
python3 tools/pre-commit/create-device-template.py adm1275 pmbus \
  --with-project \
  --commands read_vout,read_iout,read_temp \
  --pages 1
```

---

## 📊 Success Metrics

### Review Efficiency Improvements

- ✅ **80%+ review issues** caught before PR submission
- ✅ **2-3 → 1 review cycles** (fewer iterations needed)
- ✅ **Zero git history pollution** (local SonarCloud analysis)
- ✅ **Professional code quality** from first commit

### Automated Quality Standards

- ✅ **Consistent style** (Linux kernel style, 8-space tabs)
- ✅ **Memory safety** (Cppcheck + review patterns)
- ✅ **Documentation coverage** (Doxygen enforcement)
- ✅ **Platform compatibility** (abstraction patterns)

---

## 📚 Additional Resources

### Quick Commands Reference

```bash
# Environment validation
./tools/pre-commit/validate-setup.sh

# New device development
./tools/pre-commit/new-dev-branch.sh <device>
python3 tools/pre-commit/create-device-template.py <device> <type> --with-project

# Quality checks
./tools/pre-commit/quick-sonar-check.sh
python3 tools/pre-commit/review-checker.py <files>

# SonarCloud analysis
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export analysis.json
```

### Documentation

- **Tool Documentation:** `tools/pre-commit/README.md`
- **SonarCloud Guide:** `tools/pre-commit/sonar-local-guide.md`
- **Main Documentation:** `CLAUDE.md`
- **API Documentation:** https://analogdevicesinc.github.io/no-OS/doxygen/

### Transfer to Innersource

```bash
# Transfer complete environment to innersource repository
./tools/transfer-to-repository.sh /path/to/innersource-no-OS
```

---

## 🏆 Ready to Develop!

This workflow provides a complete professional development environment that:
- ✅ **Catches issues before PR submission**
- ✅ **Maintains consistent code quality**
- ✅ **Supports dual repository workflows**
- ✅ **Integrates with AI-powered review**
- ✅ **Follows industry best practices**

**Start your next driver with:** `./tools/pre-commit/new-dev-branch.sh <your_device>`