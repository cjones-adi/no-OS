# Git Workflow Standards for no-OS

Standardized Git workflow for no-OS driver development with automated quality enforcement.

## 📋 Repository Setup (Required)

### Standard Fork Workflow

**Repository Structure:**
```bash
upstream = analogdevicesinc/no-OS (main repository)
origin = YOUR_USERNAME/no-OS (your fork)
```

### Initial Setup Commands
```bash
# 1. Fork analogdevicesinc/no-OS to YOUR_USERNAME/no-OS on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/no-OS.git
cd no-OS

# 3. Set up remotes (CRITICAL for automated tools)
git remote add upstream https://github.com/analogdevicesinc/no-OS.git
git remote set-url origin https://github.com/YOUR_USERNAME/no-OS.git

# 4. Verify setup
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/no-OS.git (fetch)
# origin    https://github.com/YOUR_USERNAME/no-OS.git (push)
# upstream  https://github.com/analogdevicesinc/no-OS.git (fetch)
# upstream  https://github.com/analogdevicesinc/no-OS.git (push)
```

### Why This Setup Matters
- ✅ **Automated tools** require `upstream` remote for syncing
- ✅ **Branch scripts** use upstream for latest changes
- ✅ **Quality checks** compare against upstream/main
- ✅ **PR creation** works with proper fork setup

## 🌿 Branch Convention (Enforced)

### Branch Naming Patterns (AUTOMATED VALIDATION)
```bash
dev/<device_name>           # dev/adm1275, dev/ltc2978
dev/<device>-<platform>     # dev/adm1275-maxim
dev/<device>-fix-<issue>    # dev/adm1275-fix-telemetry
```

### Automated Branch Creation
```bash
# Recommended: Use helper script
./tools/pre-commit/new-dev-branch.sh <device_name>

# What it does:
# ✅ Syncs with upstream automatically
# ✅ Creates properly named branch (dev/<device>)
# ✅ Suggests device type and templates
# ✅ Validates environment setup

# Manual alternative (if needed)
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main
git checkout -b dev/<device_name>
```

### Branch Validation
- **Pre-commit hook** automatically validates branch naming
- **Prevents commits** on incorrectly named branches
- **Suggests corrections** for common naming mistakes

## 💬 Commit Standards (Enforced)

### Commit Message Format (AUTOMATED VALIDATION)
```bash
# Format: <scope>: <component>: <description>
<scope>: <component>: <brief description>

[Optional detailed description]

Signed-off-by: Your Name <your.email@analog.com>
```

### Scope Categories
| Scope | Usage | Examples |
|-------|-------|----------|
| `drivers` | Driver code changes | `drivers: adc: ad7980: add initial implementation` |
| `projects` | Project/example code | `projects: ad7980-eval: add evaluation support` |
| `docs` | Documentation | `docs: adc: ad7980: add driver documentation` |
| `ci` | Build/CI changes | `ci: build: add ad7980-eval to build matrix` |
| `tools` | Development tools | `tools: pre-commit: enhance pattern detection` |

### Example Commit Messages
```bash
# Good examples
drivers: power: adm1275: add initial PMBus implementation
drivers: adc: ad7980: fix initialization sequence timing
projects: adm1275-eval: add MAX32655 platform support
docs: power: adm1275: add comprehensive API documentation
ci: build: add adm1275-eval to build matrix

# Bad examples (will be rejected)
Add ADM1275 driver                    # Missing scope and component
drivers: Add device                   # Too generic
adm1275: Initial implementation       # Wrong scope format
drivers: power: Add ADM1275           # Inconsistent capitalization
```

### Signed Commits (REQUIRED)
```bash
# All commits MUST be signed off
git commit -s -m "drivers: power: adm1275: add telemetry functions"

# This adds: Signed-off-by: Your Name <your.email@analog.com>

# Configure git to sign by default
git config user.name "Your Name"
git config user.email "your.email@analog.com"
```

## 🔄 Daily Workflow

### Starting New Work
```bash
# 1. Always sync before starting
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main

# 2. Create development branch (automated)
./tools/pre-commit/new-dev-branch.sh <device_name>

# 3. Generate template (if new driver)
python3 tools/pre-commit/create-device-template.py <device> <type> --with-project
```

### During Development
```bash
# Regular commits with automated quality checks
git add .
git commit -s -m "drivers: power: adm1275: implement telemetry functions"

# Quality checks run automatically:
# ✅ Code style (Linux kernel style, 8-space tabs)
# ✅ Static analysis (Cppcheck)
# ✅ Documentation validation
# ✅ Review pattern detection (62.5% coverage)
# ✅ Branch naming validation

# Periodic sync with upstream (if main has updates)
git fetch upstream
git rebase upstream/main
```

### Preparing for PR
```bash
# Final sync and cleanup
git fetch upstream
git rebase upstream/main

# Push to your fork
git push origin dev/<device_name>

# If you need to force push after rebasing (be careful!)
git push --force-with-lease origin dev/<device_name>
```

## 📝 Pull Request Workflow

### Creating Pull Requests
```bash
# Create PR from your fork to upstream
gh pr create --repo analogdevicesinc/no-OS \
             --title "drivers: power: adm1275: add support for ADM1275 PMBus monitor" \
             --body "$(cat << 'EOF'
## Summary
- Add ADM1275 digital power monitor driver
- Support for voltage, current, and power telemetry
- PMBus interface with I2C communication
- MAX32655 and Linux platform support

## Testing
- [x] Hardware tested on MAX32655 evaluation board
- [x] IIO subsystem tested on Raspberry Pi 4
- [x] All pre-commit checks passed
- [x] Builds successfully on target platforms

## Documentation
- [x] Doxygen documentation complete
- [x] README added to project
- [x] Register definitions documented
EOF
)"
```

### PR Title Standards
```bash
# Good titles (under 70 characters)
drivers: power: adm1275: add support for ADM1275 PMBus monitor
projects: adm1275-eval: add evaluation project with IIO example
docs: power: adm1275: add comprehensive driver documentation

# Use description/body for details, not title
```

### After PR Merge
```bash
# Clean up local branches
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main

# Delete merged branch
git branch -d dev/<device_name>
git push origin --delete dev/<device_name>
```

## 🔧 Commit Organization Strategy

### Logical Commit Sequence
```bash
# 1. Core driver implementation
git commit -s -m "drivers: power: adm1275: add initial driver implementation"

# 2. Register definitions (if complex)
git commit -s -m "drivers: power: adm1275: add PMBus register definitions"

# 3. Project/example code
git commit -s -m "projects: adm1275-eval: add evaluation board project"

# 4. Documentation
git commit -s -m "docs: power: adm1275: add driver documentation"

# 5. Build integration
git commit -s -m "ci: build: add adm1275 projects to build matrix"
```

### Commit Best Practices
- ✅ **Logical separation**: Each commit should be a complete, logical change
- ✅ **Buildable commits**: Each commit should leave the code in a buildable state
- ✅ **Focused changes**: Don't mix unrelated changes in one commit
- ✅ **Good descriptions**: Explain the "why" not just the "what"

## 🛠️ Git Helper Commands

### Recommended Git Aliases
```bash
# Add these to ~/.gitconfig
[alias]
    # Sync with upstream
    sync = !git fetch upstream && git rebase upstream/main

    # Push to origin with tracking
    pushup = !git push --set-upstream origin $(git branch --show-current)

    # Signed commit shortcut
    cs = commit -s

    # Show commits vs upstream
    status-upstream = !git log --oneline upstream/main..HEAD

    # Clean merged branches
    clean-branches = !git branch --merged | grep -E "dev/" | xargs -r git branch -d
```

### Usage Examples
```bash
git sync                    # Update from upstream
git pushup                  # Push current branch to origin
git cs -m "commit message"  # Signed commit
git status-upstream         # See your commits vs upstream
git clean-branches          # Remove merged dev/ branches
```

## 🔒 Git Safety Protocols (CRITICAL)

### What's Automated vs Manual
**✅ Automated by pre-commit hooks:**
- Code style validation (AStyle)
- Static analysis (Cppcheck)
- Documentation validation
- Branch naming enforcement
- Commit message format validation
- Review pattern detection

**⚠️ Manual responsibility (NEVER automated):**
- Git config updates
- Destructive operations (reset --hard, force push to main)
- Hook bypassing (--no-verify)
- Amending published commits

### Git Safety Rules
```bash
# ✅ SAFE: Regular development operations
git add <files>
git commit -s -m "message"
git push origin dev/<branch>
git rebase upstream/main

# ⚠️ CAUTION: Potentially destructive
git push --force-with-lease origin dev/<branch>  # Only on your dev branches
git reset --soft HEAD~1                         # Only on unpushed commits

# ❌ NEVER: Destructive operations (unless explicitly requested)
git push --force origin main                    # Can destroy work
git reset --hard HEAD~5                         # Loses commits
git rebase --interactive upstream/main          # Complex, easy to break
git commit --amend                              # On published commits
```

## 📊 Quality Integration

### Automated Quality Gates
Every commit triggers:
1. **Code Style**: Linux kernel style (8-space tabs, 80-char lines)
2. **Static Analysis**: Cppcheck with no-OS configuration
3. **Documentation**: Doxygen format validation
4. **Pattern Detection**: 62.5% of review issues caught
5. **Build Validation**: Project compilation checks

### Manual Quality Commands
```bash
# Run quality checks manually
./tools/pre-commit/quick-sonar-check.sh
python3 tools/pre-commit/review-checker.py <file.c>

# Full analysis
export SONAR_TOKEN="your_token"
./tools/pre-commit/run-local-sonar.sh --changed-only --preview
```

## 🎯 Troubleshooting

### Common Git Issues

**"Unable to rebase" / Conflicts**
```bash
# Stop rebase and retry
git rebase --abort
git fetch upstream
git checkout main
git reset --hard upstream/main
git push --force-with-lease origin main
```

**"Branch name validation failed"**
```bash
# Rename branch to correct format
git branch -m dev/<correct-device-name>
```

**"Pre-commit hook failed"**
```bash
# Check what failed
git commit -s -m "test" --dry-run

# Fix issues and retry
./tools/pre-commit/validate-setup.sh
```

**"Upstream not configured"**
```bash
# Add upstream remote
git remote add upstream https://github.com/analogdevicesinc/no-OS.git
```

### Recovery Commands
```bash
# Get back to clean state
git checkout main
git fetch upstream
git reset --hard upstream/main
git push --force-with-lease origin main

# Start fresh branch
./tools/pre-commit/new-dev-branch.sh <device>
```

---

**This workflow ensures**:
- ✅ **Consistent branching** across all developers
- ✅ **Quality commits** that pass review
- ✅ **Clean history** for easy maintenance
- ✅ **Automated validation** to prevent common mistakes
- ✅ **Safe operations** that protect repository integrity