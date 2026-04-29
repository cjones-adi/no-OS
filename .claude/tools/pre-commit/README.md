# no-OS Pre-commit Tools

A comprehensive suite of development tools for no-OS driver development that catches common issues before PR submission.

## 🔧 Installation

### Repository Setup (Required)

Set up the standard fork workflow before installing hooks:

```bash
# 1. Fork the repository on GitHub (analogdevicesinc/no-OS → YOUR_USERNAME/no-OS)

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/no-OS.git
cd no-OS

# 3. Set up remotes
git remote add upstream https://github.com/analogdevicesinc/no-OS.git
git remote set-url origin https://github.com/YOUR_USERNAME/no-OS.git

# 4. Verify setup
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/no-OS.git (fetch/push)
# upstream  https://github.com/analogdevicesinc/no-OS.git (fetch/push)

# 5. Install hooks
./tools/pre-commit/install-hooks.sh
```

**Important:** The tools expect this upstream/origin setup for proper workflow.

### Environment Validation

Validate your setup with the included checker:

```bash
# Check your development environment
./tools/pre-commit/validate-setup.sh
```

This validates:
- ✅ Git repository and remote setup
- ✅ Fork workflow configuration
- ✅ Required and optional tools
- ✅ Branch naming compliance
- ✅ Upstream synchronization status
- ✅ Development tool availability

This installs:
- **Branch naming validation** (dev/<device_name> convention)
- **Code style checks** (AStyle)
- **Static analysis** (Cppcheck)
- **Documentation validation**
- **Review pattern detection**
- **Commit message format validation**
- **Build validation** (optional)

## 📋 Available Tools

### 1. Pre-commit Hook (`pre-commit`)

Automatically runs before each commit to catch issues early.

**What it checks:**
- Code style compliance (Linux kernel style, 8-space tabs, 80-char lines)
- Static analysis warnings (memory leaks, potential bugs)
- Documentation completeness (Doxygen format)
- Common review issues (error handling, naming conventions)
- Header guard format
- Build validation (if enabled)

### 2. Commit Message Validation (`commit-msg`)

Ensures commit messages follow no-OS standards.

**Expected format:**
```
<scope>: <component>: <brief description>

[Optional detailed description]

Signed-off-by: Your Name <your.email@analog.com>
```

**Examples:**
```
drivers: adc: ad7980: add initial driver implementation
projects: ad7980-eval: add evaluation board support
docs: adc: ad7980: add driver documentation
```

### 3. Automated Review Checker (`review-checker.py`)

Analyzes code for patterns found in comprehensive 6-month analysis (144 PRs, 507 review comments).

**Usage:**
```bash
# Check specific files
python3 tools/pre-commit/review-checker.py drivers/adc/mydevice/mydevice.c

# Check all staged files
git diff --cached --name-only | grep -E '\.(c|h)$' | xargs python3 tools/pre-commit/review-checker.py
```

**What it detects:**
- Missing error handling (30 review occurrences)
- Poor documentation (18 occurrences)
- Header guard issues (9 occurrences)
- Magic numbers (9 occurrences)
- Type safety issues (5 occurrences)
- Naming convention problems (6 occurrences)

### 4. Branch Management Tools

**Branch Name Validator (`check-branch-name.sh`)**
Enforces `dev/<device_name>` naming convention automatically in pre-commit hooks.

**Branch Creation Helper (`new-dev-branch.sh`)**
Creates properly named development branches with device detection.

**Usage:**
```bash
# Create basic development branch
./tools/pre-commit/new-dev-branch.sh adm1275
# → Creates: dev/adm1275

# Create evaluation branch
./tools/pre-commit/new-dev-branch.sh adm1275 eval
# → Creates: dev/adm1275-eval

# Create platform-specific branch
./tools/pre-commit/new-dev-branch.sh adm1275 maxim
# → Creates: dev/adm1275-maxim

# Create bug fix branch
./tools/pre-commit/new-dev-branch.sh adm1275 fix-telemetry
# → Creates: dev/adm1275-fix-telemetry
```

**Automatic device detection:**
- PMBus devices: `adm127*`, `ltc29*`, `max20*` → suggests PMBus template
- ADC devices: `ad70*`-`ad79*`, `adaq*` → suggests ADC template
- Provides next steps and template generation commands

### 5. Local SonarCloud Scanner (`setup-local-sonar.sh`)

**Solves the free tier branch limitation problem!**

Runs SonarCloud analysis locally on development branches without affecting main branch.

**Key Features:**
- 🎯 **Analyze only YOUR changes** vs upstream/main (ignores baseline issues)
- 🚀 **No git history pollution** (local analysis, no merge/revert needed)
- ♾️ **Unlimited analysis** (preview mode, no free tier limits)
- 🔍 **Claude integration** (export reports for detailed review)

**Setup:**
```bash
# One-time setup
./tools/pre-commit/setup-local-sonar.sh

# Set your token
export SONAR_TOKEN="your_token_here"

# Quick daily check
./tools/pre-commit/quick-sonar-check.sh

# Full analysis with Claude export
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export analysis.json
```

**Perfect for your workflow:** Analyze unreleased device drivers in development branches without triggering public SonarCloud scans.

### 6. Device Template Generator (`create-device-template.py`)

Creates driver templates optimized for specific device types.

**Usage:**
```bash
# Create ADC driver template
python3 tools/pre-commit/create-device-template.py ad7980 adc --with-project

# Create PMBus device template
python3 tools/pre-commit/create-device-template.py adm1266 pmbus --with-project

# Specify output directory
python3 tools/pre-commit/create-device-template.py ltc2978 power -o /path/to/output
```

**Templates available:**
- **ADC drivers** - Optimized for power management applications
- **PMBus drivers** - Full PMBus command set with telemetry
- **Project templates** - MAX32655 and Pi4 platform support with IIO

## ⚙️ Configuration

Customize behavior by editing `.pre-commit-config` in the repository root:

```bash
# Copy default configuration
cp tools/pre-commit/pre-commit-config.example .pre-commit-config

# Edit settings
nano .pre-commit-config
```

**Key settings:**
```bash
# Enable/disable specific checks
ENABLE_BRANCH_CHECK=true     # Branch naming convention validation
ENABLE_ASTYLE=true           # Code style checking
ENABLE_CPPCHECK=true         # Static analysis
ENABLE_BUILD_CHECK=false     # Build validation (slow)
ENABLE_DOC_CHECK=true        # Documentation checks
ENABLE_REVIEW_CHECK=true     # Review pattern checks

# Platform-specific settings for MAX32655 development
MAXIM_PLATFORM_ONLY=true
BUILD_PLATFORMS="maxim"

# Power management / PMBus development
PMBUS_DEVICES="adm1266 adm1275 ltc2978"
POWER_MGMT_CHECKS=true
```

## 🚀 Typical Workflow

### 1. Start New Development

```bash
# Sync with upstream first
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main

# Create properly named branch (checks for upstream sync)
./tools/pre-commit/new-dev-branch.sh ad7123
# → Creates and switches to dev/ad7123

# Generate template (as suggested by branch creation script)
python3 tools/pre-commit/create-device-template.py ad7123 adc --with-project
```

### 2. Development Cycle

```bash
# Make changes
vim drivers/adc/ad7123/ad7123.c

# Stage changes
git add drivers/adc/ad7123/

# Commit (hooks run automatically)
git commit -s -m "drivers: adc: ad7123: add initial driver implementation"

# Push to your fork
git push origin dev/ad7123
```

### 3. Create Pull Request

```bash
# Create PR from your fork to upstream
gh pr create --repo analogdevicesinc/no-OS \
             --title "drivers: adc: ad7123: add support for AD7123 ADC" \
             --body "Add driver for AD7123 16-bit ADC..."
```

If hooks fail:
```bash
# Fix issues reported by hooks
./build/astyle/build/gcc/bin/astyle --options=ci/astyle_config drivers/adc/ad7123/ad7123.c

# Re-stage and commit
git add drivers/adc/ad7123/ad7123.c
git commit -s -m "drivers: adc: ad7123: add initial driver implementation"
```

### 3. Manual Checks

Run tools manually for testing:

```bash
# Check code style
git diff --cached --name-only | grep -E '\.(c|h)$' | xargs ./build/astyle/build/gcc/bin/astyle --options=ci/astyle_config

# Run static analysis
python3 tools/pre-commit/review-checker.py drivers/adc/ad7123/ad7123.c

# Build validation
python3 tools/scripts/build_projects.py . -project=ad7123-eval
```

## 📊 Review Pattern Analysis

Based on analysis of 50 merged PRs with 185 review comments:

| Issue Category | Occurrences | Automation |
|---|---|---|
| Error Handling | 30 | ✅ Automated detection |
| Documentation | 18 | ✅ Format validation |
| Header Guards | 9 | ✅ Format checking |
| Magic Numbers | 9 | ✅ Pattern detection |
| Type Safety | 5 | ✅ Cast analysis |
| Naming Conventions | 6 | ✅ Prefix validation |

## 🎯 Platform-Specific Notes

### MAX32655 Development

Configuration for Maxim platform development:

```bash
# .pre-commit-config
ENABLE_BUILD_CHECK=true
BUILD_PLATFORMS="maxim"
MAXIM_PLATFORM_ONLY=true
```

### Raspberry Pi 4 / IIO Development

```bash
# .pre-commit-config
IIO_DOCUMENTATION_REQUIRED=true
LINUX_COMPATIBILITY_CHECK=true
```

Project templates include:
- IIO device integration
- Linux platform compatibility
- Proper device tree binding examples

### Power Management / PMBus

```bash
# .pre-commit-config
PMBUS_DEVICES="adm1266 adm1275 ltc2978"
POWER_MGMT_CHECKS=true
```

Templates include:
- Full PMBus command set
- Telemetry data structures
- Page management utilities
- Linear data format conversion

## 🔍 Bypass Options

Sometimes you may need to bypass checks:

```bash
# Skip all pre-commit hooks
git commit --no-verify -m "message"

# Skip specific checks (edit .pre-commit-config)
ENABLE_ASTYLE=false

# Skip review suggestions (they're warnings, not errors)
# Review checker suggestions don't block commits
```

## 🛠️ Troubleshooting

### AStyle Build Fails

```bash
# Manual AStyle build
cd build
wget "https://sourceforge.net/projects/astyle/files/astyle/astyle 3.1/astyle_3.1_linux.tar.gz"
tar -xzf astyle_3.1_linux.tar.gz
cd astyle/build/gcc && make -j$(nproc)
```

### Cppcheck Not Found

```bash
# Install Cppcheck
sudo apt-get install cppcheck

# Or use the CI build script
./ci/cppcheck.sh
```

### Build Validation Slow

```bash
# Disable build validation for faster commits
echo "ENABLE_BUILD_CHECK=false" >> .pre-commit-config
```

## 📖 Integration with IDEs

### VS Code

Add to `.vscode/settings.json`:
```json
{
    "files.associations": {
        "*.h": "c",
        "*.c": "c"
    },
    "C_Cpp.clang_format_fallbackStyle": "file",
    "editor.formatOnSave": true
}
```

### Vim/Neovim

Add to `.vimrc`:
```vim
" Auto-format on save
autocmd BufWritePre *.c,*.h !astyle --options=ci/astyle_config %
```

## 🤝 Contributing

To improve these tools:

1. Update review pattern analysis: `python3 extract_review_patterns.py`
2. Add new device template: Edit `create-device-template.py`
3. Enhance review checker: Add patterns to `review-checker.py`
4. Test thoroughly before submitting PR

---

**Questions or issues?** Check the main no-OS documentation or create an issue in the repository.