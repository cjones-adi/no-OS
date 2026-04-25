---
name: linux-checkpatch-sparse
description: Complete guide to Linux kernel code quality tools (checkpatch.pl, sparse, coccinelle). Use when checking code style, finding bugs, or preparing patches for submission.
metadata:
  version: "2.0"
  platform: linux
  category: tools
  tags:
    - checkpatch
    - sparse
    - coccinelle
    - code-quality
    - static-analysis
    - coding-style
    - patch-submission
  dependencies:
    - linux-debugging
    - linux-kconfig-makefile
  learning_objectives:
    - Use checkpatch.pl to verify kernel coding style compliance
    - Apply sparse static analyzer to detect type errors and bugs
    - Write and run coccinelle semantic patches for pattern detection
    - Understand Linux kernel coding style conventions
    - Prepare clean patches for upstream submission
    - Automate code quality checks in CI/CD pipelines
---

# Linux Kernel Code Quality Tools

Quick-start guide for using checkpatch.pl, sparse, and coccinelle to ensure code quality for Linux kernel submissions.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/coding-style.md**:
- User mentions: "coding style", "indentation rules", "naming conventions", "how to format code"
- Questions about: braces placement, pointer syntax, typedefs, function size, macro formatting
- User asks: "why 8-space tabs", "where do braces go", "how to name variables"

**Triggers to read reference/checkpatch.md**:
- User mentions: "checkpatch", "line too long", "brace error", "trailing whitespace"
- Build/CI errors from checkpatch.pl
- User says: "checkpatch failed", "checkpatch warning", "ERROR:", "WARNING:"
- Questions about: fixing specific checkpatch errors, checkpatch options

**Triggers to read reference/sparse.md**:
- User mentions: "sparse", "address space", "__iomem", "__user", "endianness", "__le32", "__be32"
- Questions about: static analysis, annotations, __bitwise, locking annotations
- Sparse warnings in output: "incorrect type", "cast removes address space", "context imbalance"

**Triggers to read reference/coccinelle.md**:
- User mentions: "coccinelle", "semantic patch", "SmPL", "coccicheck"
- Questions about: writing semantic patches, automated refactoring, pattern matching
- User asks: "how to run coccicheck", "create semantic patch"

**Triggers to read reference/ci-integration.md**:
- User asks: "git hooks", "pre-commit", "CI/CD", "GitHub Actions", "automate checks"
- Questions about: automation, continuous integration setup

---

## When to Use This Skill

- Checking kernel code style before committing
- Fixing checkpatch.pl errors and warnings
- Running sparse to find type errors and bugs
- Using coccinelle for pattern-based bug detection
- Preparing patches for upstream submission
- Setting up automated code quality checks in CI/CD

## Overview

The Linux kernel provides three primary static analysis tools:
- **checkpatch.pl**: Coding style checker for patches and source files
- **sparse**: Semantic checker for type errors, locking issues, and annotations
- **coccinelle**: Semantic patching engine for pattern-based code transformation

## Quick Start

### Pre-Commit Workflow

```bash
# 1. Check style
git diff --cached | ./scripts/checkpatch.pl -

# 2. Build with sparse
make C=1 W=1 <file>.o

# 3. Run coccicheck (optional)
make coccicheck MODE=report M=<directory>
```

### Patch Submission Workflow

```bash
# 1. Format patch
git format-patch -1 HEAD

# 2. Check patch
./scripts/checkpatch.pl --strict 0001-*.patch

# 3. Test build multiple arch
make ARCH=arm allmodconfig && make ARCH=arm -j$(nproc)
make ARCH=arm64 allmodconfig && make ARCH=arm64 -j$(nproc)

# 4. Build documentation
make htmldocs
```

## Quick Reference: Coding Style Essentials

### Indentation

- **8-character tabs** for indentation (never spaces)
- Align `switch` and `case` at same column
- Deep nesting (>3 levels) = code needs refactoring

```c
if (condition) {
	do_something();          // 8-space tab
	if (nested_condition) {
		nested_action();  // 16 spaces (2 tabs)
	}
}
```

### Line Length

- **80 columns** maximum (100 acceptable in some cases)
- Exception: Never break user-visible strings (enables grepping)

### Braces

- **Functions**: Opening brace on new line
- **Control statements**: Opening brace on same line

```c
// Function
static int my_function(void)
{
	/* body */
}

// Control statement
if (condition) {
	action();
}
```

### Spacing

- Space after keywords: `if (`, `for (`, `while (`
- No space after function-like keywords: `sizeof(`, `typeof(`
- Asterisk attaches to variable name: `char *linux_banner;`

### Common Patterns

```c
// Use kernel types
u8, u16, u32, u64    // Not uint8_t, uint32_t

// Use devm_* functions
dev = devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL);

// Use dev_err_probe for probe errors
return dev_err_probe(&pdev->dev, PTR_ERR(clk), "Failed to get clock\n");

// Static for file-scope functions
static int helper_function(void)

// SPDX license at top
// SPDX-License-Identifier: GPL-2.0
```

## Quick Reference: Common checkpatch Errors

| Error | Bad | Good |
|-------|-----|------|
| Spaces around '=' | `int ret=0;` | `int ret = 0;` |
| Function brace placement | `static int func(void) {` | `static int func(void)\n{` |
| Trailing whitespace | `int x = 0; ␣` | `int x = 0;` |
| Assignment in if | `if ((ret = init(dev)) < 0)` | `ret = init(dev);\nif (ret < 0)` |
| Control statement brace | `if (cond)\n{` | `if (cond) {` |
| SPDX license | Missing | `// SPDX-License-Identifier: GPL-2.0` |

## Quick Reference: Common checkpatch Warnings

| Warning | Fix |
|---------|-----|
| Line over 80 characters | Split into multiple lines or shorten message |
| Missing space after return type | `int*func()` → `int *func()` |
| Unnecessary braces | `if (ret) { return ret; }` → `if (ret)\n	return ret;` |
| Use __func__ | `dev_dbg(&dev, "my_func: err")` → `dev_dbg(&dev, "%s: err", __func__)` |
| Prefer unsigned int | `unsigned offset` → `unsigned int offset` |
| EXPORT_SYMBOL placement | Move to immediately after function |

## Quick Reference: Common sparse Warnings

| Annotation | Purpose | Example |
|------------|---------|---------|
| `__iomem` | I/O memory (MMIO) | `void __iomem *base;` |
| `__user` | Userspace pointer | `char __user *buf` |
| `__le32`, `__be32` | Endianness | `__le32 reg_val;` |
| `__bitwise` | Type-safe integers | `typedef u32 __bitwise pm_request_t;` |
| `__must_hold` | Lock must be held | `void func(void) __must_hold(&lock)` |
| `__acquires` | Function acquires lock | `void lock_fn(void) __acquires(&lock)` |
| `__releases` | Function releases lock | `void unlock_fn(void) __releases(&lock)` |

**Common fixes**:
- Use `readl()`/`writel()` for `__iomem` pointers, not direct dereference
- Use `copy_to_user()`/`copy_from_user()` for `__user` pointers
- Use `be32_to_cpu()`/`cpu_to_be32()` for endianness conversions
- Make file-scope functions `static` to avoid "should it be static?" warnings

## Tool Usage

### checkpatch.pl

```bash
# Check patch file
./scripts/checkpatch.pl 0001-my-patch.patch

# Check uncommitted changes
git diff | ./scripts/checkpatch.pl -

# Check file directly
./scripts/checkpatch.pl -f drivers/iio/adc/ad7124.c

# Strict mode (includes style suggestions)
./scripts/checkpatch.pl --strict patch.patch

# Fix simple issues automatically
./scripts/checkpatch.pl --fix-inplace -f file.c

# Ignore specific warnings
./scripts/checkpatch.pl --ignore=LINE_SPACING,LONG_LINE patch.patch
```

### sparse

```bash
# Check specific file (re-compile with sparse)
make C=1 drivers/iio/adc/ad7124.o

# Check all files
make C=2

# Enable additional warnings
make C=1 W=1 drivers/iio/adc/ad7124.o
```

**Warning levels** (W=):
- `W=1`: Enable extra build warnings
- `W=2`: Enable more warnings (usually false positives)
- `W=3`: Enable even more warnings (likely false positives)

### coccinelle

```bash
# Run all semantic patches
make coccicheck MODE=report

# Run specific semantic patch
make coccicheck MODE=report COCCI=scripts/coccinelle/free/devm_free.cocci

# Propose fixes (patch mode)
make coccicheck MODE=patch

# Run on specific directory
make coccicheck M=drivers/iio MODE=report
```

## Patch Submission Checklist

Before submitting patches to the kernel mailing list:

### 1. checkpatch.pl Clean

```bash
# Generate and check patch
git format-patch -1 HEAD
./scripts/checkpatch.pl 0001-*.patch

# Should output: total: 0 errors, 0 warnings, 0 checks
./scripts/checkpatch.pl --strict 0001-*.patch  # Optional
```

### 2. sparse Clean

```bash
# Check with sparse
make C=1 W=1 drivers/iio/adc/ad7124.o

# Should have no warnings related to your changes
```

### 3. coccicheck Clean

```bash
# Run semantic checks
make coccicheck MODE=report M=drivers/iio

# Review and fix any findings
```

### 4. Build Testing

```bash
# Build for multiple architectures
make ARCH=arm allmodconfig && make ARCH=arm -j$(nproc)
make ARCH=arm64 allmodconfig && make ARCH=arm64 -j$(nproc)
make ARCH=x86_64 allmodconfig && make ARCH=x86_64 -j$(nproc)

# Build with warnings enabled
make W=1 drivers/iio/adc/ad7124.o
```

### 5. Documentation Build

```bash
# Check kernel-doc comments
./scripts/kernel-doc -none drivers/iio/adc/ad7124.c

# Build HTML documentation
make htmldocs
```

### 6. Module Load Test

```bash
# Build as module
make M=drivers/iio/adc

# Check module info
modinfo drivers/iio/adc/ad7124.ko

# Load/unload module
sudo insmod drivers/iio/adc/ad7124.ko
dmesg | tail
sudo rmmod ad7124
```

## Common Coding Patterns

### Device Managed Resources (devm_*)

```c
static int probe(struct platform_device *pdev)
{
	struct my_device *dev;
	int ret;

	dev = devm_kzalloc(&pdev->dev, sizeof(*dev), GFP_KERNEL);
	if (!dev)
		return -ENOMEM;

	dev->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(dev->base))
		return PTR_ERR(dev->base);

	dev->clk = devm_clk_get(&pdev->dev, "adc");
	if (IS_ERR(dev->clk))
		return PTR_ERR(dev->clk);

	ret = devm_request_irq(&pdev->dev, dev->irq, handler,
			       0, pdev->name, dev);
	if (ret)
		return ret;

	// All resources auto-freed on error or remove
	return 0;
}

// No remove function needed!
```

### Error Handling with dev_err_probe

```c
static int probe(struct platform_device *pdev)
{
	struct clk *clk;

	clk = devm_clk_get(&pdev->dev, "adc");
	if (IS_ERR(clk))
		return dev_err_probe(&pdev->dev, PTR_ERR(clk),
				     "Failed to get clock\n");

	// Automatically handles -EPROBE_DEFER silently
	return 0;
}
```

### Guard Notation for Locking (Linux 6.5+)

```c
#include <linux/cleanup.h>

static int process_data(struct my_device *dev)
{
	guard(mutex)(&dev->lock);

	// Lock automatically acquired here
	update_data(dev);

	if (error_condition)
		return -EIO;  // Lock automatically released

	process_more(dev);

	return 0;  // Lock automatically released
}
```

### Goto for Cleanup

```c
static int probe(struct platform_device *pdev)
{
	struct my_device *mydev;
	int ret;

	mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
	if (!mydev)
		return -ENOMEM;

	ret = clk_prepare_enable(mydev->clk);
	if (ret)
		goto err_free;

	ret = device_init(mydev);
	if (ret)
		goto err_disable_clk;

	return 0;

err_disable_clk:
	clk_disable_unprepare(mydev->clk);
err_free:
	kfree(mydev);
	return ret;
}
```

## Tools Configuration

### EditorConfig (.editorconfig)

```ini
[*.{c,h}]
indent_style = tab
indent_size = 8
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{dts,dtsi}]
indent_style = tab
indent_size = 8

[Kconfig*]
indent_style = space
indent_size = 2
```

### clang-format

```bash
# Format file according to kernel style
clang-format -i --style=file drivers/iio/adc/ad7124.c

# Check without modifying
clang-format --dry-run --Werror drivers/iio/adc/ad7124.c
```

### vim Configuration

```vim
" .vimrc
set tabstop=8
set shiftwidth=8
set noexpandtab
set textwidth=80
```

### emacs Configuration

```elisp
;; .emacs
(add-hook 'c-mode-common-hook
          (lambda ()
            (setq indent-tabs-mode t)
            (setq tab-width 8)
            (setq c-basic-offset 8)))
```

## References

### Documentation

- `Documentation/process/coding-style.rst` - Kernel coding style
- `Documentation/dev-tools/sparse.rst` - Sparse documentation
- `Documentation/dev-tools/coccinelle.rst` - Coccinelle usage
- `Documentation/process/submit-checklist.rst` - Submission checklist

### Scripts

- `scripts/checkpatch.pl` - Style checker
- `scripts/coccicheck` - Coccinelle wrapper
- `scripts/Lindent` - Reindent code
- `scripts/kernel-doc` - Documentation checker

### Online Resources

- https://sparse.docs.kernel.org - Sparse documentation
- https://coccinelle.gitlabpages.inria.fr/website - Coccinelle website
- https://www.kernel.org/doc/html/latest - Kernel documentation

## Summary

### Essential Rules

1. **Indentation**: 8-character tabs, never spaces
2. **Line length**: 80 columns max (100 acceptable)
3. **Braces**: Functions on new line, control statements on same line
4. **Spacing**: Space after keywords, asterisk with variable name
5. **Types**: Use kernel types (u8, u16, u32, u64)
6. **Static**: File-scope functions must be static
7. **SPDX**: Add license identifier at top of file
8. **devm_***: Prefer device-managed resource functions
9. **Annotations**: Use sparse annotations (__iomem, __user, __le32, etc.)
10. **Testing**: Run checkpatch, sparse, and coccicheck before submitting

### Before Committing

```bash
# Style check
git diff --cached | ./scripts/checkpatch.pl -

# Static analysis
make C=1 W=1 <file>.o

# Semantic checks
make coccicheck MODE=report M=<directory>
```

### Before Submitting

```bash
# Patch validation
./scripts/checkpatch.pl --strict 0001-*.patch

# Multi-arch build
make ARCH=arm allmodconfig && make ARCH=arm -j$(nproc)
make ARCH=arm64 allmodconfig && make ARCH=arm64 -j$(nproc)

# Documentation
make htmldocs
```
