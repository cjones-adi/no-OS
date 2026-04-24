# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) for working with code in this repository, with special focus on driver development workflow.

## About no-OS

This is Analog Devices' no-OS repository containing hardware drivers and reference projects for embedded systems without an operating system. It supports microcontrollers, FPGAs, and other embedded platforms that interface with ADI hardware peripherals.

## Enhanced Driver Development Workflow

The enhanced development process includes automated quality assurance:

1. **Device Assignment** - Receive datasheet and device specifications
2. **Research & Planning** - Study similar drivers and device requirements
3. **Implementation** - Create driver files with IIO support following no-OS patterns
4. **Automated Quality** - Run review pattern detection and style cleanup
5. **Local Testing** - Run CI tools locally before PR submission
6. **PR Creation** - Submit with proper commit messages and complete build system
7. **Review & Iteration** - Address feedback with 62.5% issue prevention
8. **Hardware Testing** - Validate on target hardware
9. **Merge** - Maintainer approval and integration

**🎯 Claude Code Enhanced Features:**
- **Datasheet Analysis**: Automatic PMBus command extraction and interface detection
- **IIO Integration**: Complete Linux subsystem support for all power monitoring devices
- **Build System**: Full CI-ready project structure (Makefile, builds.json, src.mk)
- **Quality Automation**: 62.5% review issue prevention using 6-month pattern analysis

---

## Driver Implementation Patterns

### File Structure and Naming

Every driver should follow this enhanced structure:

```
drivers/<category>/<device_name>/
├── <device_name>.h        # Public API declarations
├── <device_name>.c        # Implementation
├── iio_<device_name>.h    # IIO subsystem interface (REQUIRED for monitoring devices)
├── iio_<device_name>.c    # IIO implementation
├── <device_name>_regs.h   # Register definitions (if complex)
└── README.rst            # Comprehensive documentation

projects/<device_name>-eval/
├── Makefile              # Platform build selection
├── builds.json           # CI build matrix
├── src.mk               # Source dependencies and platform support
├── README.rst            # Complete project documentation
└── src/
    ├── common/
    │   ├── common_data.h
    │   └── common_data.c
    ├── examples/
    │   └── basic/
    └── platform/<target>/
```

**Naming Convention:**
- Use lowercase device name: `ad7980.h`, not `AD7980.h`
- Categories: `adc`, `dac`, `switch`, `sensor`, `power`, `frequency`, etc.
- Include family variants: `ad717x` for AD7175, AD7176, AD7177, etc.

**🚨 Linux Driver Naming Principle:**
> **Critical**: Linux drivers must not rely on generic or wildcard‑style names to represent multiple devices. The kernel driver model requires explicit device matching via ID tables or device tree compatibles, and device naming stability is intentionally delegated to user space.

**Implementation Guidelines:**
- ❌ **Avoid**: Generic names like `device_nameX`, `sensor_driver`, `power_controller`
- ✅ **Use**: Specific device names like `ltm4700`, `adm1275`, `ad7980`
- ✅ **Family Support**: Use explicit device identification in code (e.g., chip_id detection)
- ✅ **Branch Names**: `dev/ltm4700`, `dev/adm1275` (not `dev/ltm470x` or `dev/power_device`)

### Header File Template (`device_name.h`)

> **📝 Template Note**: Replace all `device_name` placeholders with your specific device name (e.g., `ltm4700.h`, `adm1275.c`). Follow Linux kernel principle: use explicit device names, never generic placeholders in actual code.

```c
/***************************************************************************//**
 *   @file   device_name.h
 *   @brief  Header file of DEVICE_NAME Driver.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright 2024(c) Analog Devices, Inc.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of Analog Devices, Inc. nor the names of its
 *    contributors may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES, INC. "AS IS" AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
 * EVENT SHALL ANALOG DEVICES, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
 * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*******************************************************************************/
#ifndef __DEVICE_NAME_H__
#define __DEVICE_NAME_H__

#include <stdint.h>
#include "no_os_spi.h"    // or no_os_i2c.h
#include "no_os_gpio.h"   // if GPIO pins used

/* Register definitions */
#define DEVICE_NAME_REG_EXAMPLE    0x00

/* Bit field definitions */
#define DEVICE_NAME_EXAMPLE_MSK    NO_OS_GENMASK(7, 0)
#define DEVICE_NAME_EXAMPLE(x)     no_os_field_prep(DEVICE_NAME_EXAMPLE_MSK, x)

/**
 * @struct device_name_dev
 * @brief Device driver handler.
 */
struct device_name_dev {
	/* Communication interface */
	struct no_os_spi_desc		*spi_desc;
	/* Optional GPIO pins */
	struct no_os_gpio_desc		*gpio_reset;
	/* Device configuration */
	uint8_t				device_id;
};

/**
 * @struct device_name_init_param
 * @brief Device initialization parameters.
 */
struct device_name_init_param {
	/* Communication interface */
	struct no_os_spi_init_param	spi_init;
	/* Optional GPIO pins */
	struct no_os_gpio_init_param	gpio_reset;
	/* Device configuration */
	uint8_t				device_id;
};

/* Initialize the device */
int32_t device_name_init(struct device_name_dev **device,
			 struct device_name_init_param init_param);

/* Remove resources allocated by device_name_init() */
int32_t device_name_remove(struct device_name_dev *dev);

/* Device-specific functions */
int32_t device_name_read_register(struct device_name_dev *dev,
				  uint8_t reg_addr,
				  uint8_t *reg_data);

int32_t device_name_write_register(struct device_name_dev *dev,
				   uint8_t reg_addr,
				   uint8_t reg_data);

#endif /* __DEVICE_NAME_H__ */
```

### Implementation File Template (`device_name.c`)

```c
/***************************************************************************//**
 *   @file   device_name.c
 *   @brief  Implementation of DEVICE_NAME Driver.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright 2024(c) Analog Devices, Inc.
 * [... same license text as header ...]
*******************************************************************************/

#include <stdlib.h>
#include <string.h>
#include "device_name.h"
#include "no_os_alloc.h"
#include "no_os_error.h"
#include "no_os_delay.h"

/**
 * @brief Initialize the device.
 *
 * @param device     - The device structure.
 * @param init_param - The structure that contains the device initial
 *                     parameters.
 *
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t device_name_init(struct device_name_dev **device,
			 struct device_name_init_param init_param)
{
	struct device_name_dev *dev;
	int32_t ret;

	if (!device)
		return -EINVAL;

	dev = no_os_calloc(1, sizeof(*dev));
	if (!dev)
		return -ENOMEM;

	/* Initialize SPI communication */
	ret = no_os_spi_init(&dev->spi_desc, &init_param.spi_init);
	if (ret < 0)
		goto error_spi;

	/* Initialize GPIO pins if used */
	if (init_param.gpio_reset.number != NO_OS_GPIO_UNASSIGNED) {
		ret = no_os_gpio_init(&dev->gpio_reset, &init_param.gpio_reset);
		if (ret < 0)
			goto error_gpio;

		/* Reset device */
		ret = no_os_gpio_set_value(dev->gpio_reset, NO_OS_GPIO_LOW);
		if (ret < 0)
			goto error_gpio;
		no_os_mdelay(1);
		ret = no_os_gpio_set_value(dev->gpio_reset, NO_OS_GPIO_HIGH);
		if (ret < 0)
			goto error_gpio;
		no_os_mdelay(10);
	}

	/* Store configuration */
	dev->device_id = init_param.device_id;

	/* Verify device ID */
	uint8_t chip_id;
	ret = device_name_read_register(dev, DEVICE_NAME_REG_ID, &chip_id);
	if (ret < 0)
		goto error_gpio;

	if (chip_id != EXPECTED_DEVICE_ID) {
		ret = -ENODEV;
		goto error_gpio;
	}

	*device = dev;

	return 0;

error_gpio:
	if (dev->gpio_reset)
		no_os_gpio_remove(dev->gpio_reset);
	no_os_spi_remove(dev->spi_desc);
error_spi:
	no_os_free(dev);

	return ret;
}

/**
 * @brief Free resources allocated by device_name_init().
 *
 * @param dev - The device structure.
 *
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t device_name_remove(struct device_name_dev *dev)
{
	if (!dev)
		return -EINVAL;

	if (dev->gpio_reset)
		no_os_gpio_remove(dev->gpio_reset);

	no_os_spi_remove(dev->spi_desc);
	no_os_free(dev);

	return 0;
}
```

---

## Build System Integration

### Adding Driver to Projects

To use your driver in a project, update the project's `src.mk` file:

```makefile
# Add driver source
SRCS += $(DRIVERS)/<category>/<device_name>/<device_name>.c

# Add driver headers
INCS += $(DRIVERS)/<category>/<device_name>/<device_name>.h

# Add required no-OS APIs
SRCS += $(DRIVERS)/api/no_os_spi.c \
        $(DRIVERS)/api/no_os_gpio.c \
        $(NO-OS)/util/no_os_alloc.c

# Add platform drivers (example for Xilinx)
SRCS += $(PLATFORM_DRIVERS)/xilinx_spi.c \
        $(PLATFORM_DRIVERS)/xilinx_gpio.c

# Add platform headers
INCS += $(PLATFORM_DRIVERS)/$(PLATFORM)_spi.h \
        $(PLATFORM_DRIVERS)/$(PLATFORM)_gpio.h

# Add no-OS headers
INCS += $(INCLUDE)/no_os_spi.h \
        $(INCLUDE)/no_os_gpio.h \
        $(INCLUDE)/no_os_error.h
```

### Primary Build Commands

```bash
# Build all projects
python3 tools/scripts/build_projects.py . -export_dir exports -log_dir logs

# Build specific project
python3 tools/scripts/build_projects.py . -project=<project_name>

# Build for specific platform
python3 tools/scripts/build_projects.py . -platform=<platform> -project=<project_name>

# Supported platforms: xilinx, stm32, maxim, mbed, pico, aducm3029, lattice
```

---

## Local CI Testing

Before submitting a PR, run the same tools that CI uses:

### 1. Code Style (AStyle)

```bash
# Install AStyle 3.1
wget "https://sourceforge.net/projects/astyle/files/astyle/astyle 3.1/astyle_3.1_linux.tar.gz"
tar -xzf astyle_3.1_linux.tar.gz
cd astyle/build/gcc && make -j$(nproc)

# Check your files (only modified files in git)
git diff --name-only HEAD~1 | grep -E '\.(c|h)$' | while read file; do
    ./astyle/build/gcc/bin/astyle --options=ci/astyle_config "$file"
done

# Check if any formatting changes were needed
git diff --exit-code || echo "Code style issues found!"
```

**AStyle Configuration:**
- Linux kernel style
- 8-space tabs (not spaces!)
- 80-character line limit
- Spaces around operators
- Spaces after commas
- Unpad parentheses

### 2. Static Analysis (Cppcheck)

```bash
# Install cppcheck
sudo apt-get install cppcheck

# Run analysis (same as CI)
cppcheck -j$(nproc) --quiet --force --error-exitcode=1 \
         --enable=warning,style,performance \
         --suppressions-list=.cppcheckignore \
         --library=./ci/config.cppcheck .

# Enhanced review pattern detection
python3 tools/pre-commit/review-checker.py drivers/power/your_device/your_device.c
```

### 3. Local SonarCloud Analysis

```bash
# Setup (one-time)
./tools/pre-commit/setup-local-sonar.sh
export SONAR_TOKEN="your_sonar_token"

# Quick check of your changes only (ignores baseline issues)
./tools/pre-commit/quick-sonar-check.sh

# Full analysis with Claude integration
./tools/pre-commit/run-local-sonar.sh --changed-only --preview --export analysis.json
```

**Perfect for development branches:** Analyzes only YOUR changes vs upstream/main, avoiding baseline issues and free tier limitations.

### 4. Build Testing

```bash
# Test build for your project
python3 tools/scripts/build_projects.py . -project=your_project_name

# Test multiple platforms if supported
python3 tools/scripts/build_projects.py . -project=your_project_name -platform=xilinx
python3 tools/scripts/build_projects.py . -project=your_project_name -platform=stm32
```

---

## 🤖 Enhanced Development with Claude Code

For the ultimate development experience, consider using **Claude Code** as your AI development partner. Instead of manually following this guide, Claude can:

### **Intelligent Driver Development**
- **Datasheet Analysis**: Upload device datasheets for automated interface detection and command extraction
- **Linux-Compliant Multi-Device Support**: Use explicit device identification (chip_id detection) for family drivers while maintaining specific device names (e.g., `ltm4700` supporting LTM4777 via ID detection)
- **Smart Template Generation**: Generate device-specific templates with explicit names based on actual datasheet capabilities

**Example Session:**
```
Developer: "I need to develop a driver for the ADM1275 PMBus power monitoring IC"

Claude: "Perfect! ADM1275 is a PMBus power monitoring IC. Let me guide you through
the complete no-OS driver development workflow.

First, I'll create your development branch following no-OS conventions..."
# → Runs: ./tools/pre-commit/new-dev-branch.sh adm1275

Claude: "✅ Branch 'dev/adm1275' created and checked out
Device family: ADM127x PMBus power monitoring

Now let me present the available PMBus commands for selection:

📊 **ADM1275 PMBus Commands Available:**
- READ_VIN, READ_VOUT, READ_IIN, READ_IOUT (Essential monitoring)
- READ_PIN, READ_POUT (Power calculations)
- Status and thermal management commands

Which command categories should I include in your driver?
□ Essential monitoring (VIN, VOUT, IIN, IOUT)
□ Full power monitoring (add PIN, POUT)
□ Complete implementation (all commands)

[User selects option]

Claude: "Generating optimized PMBus template with selected commands..."
```

### **Automated Quality Assurance**
- **Real-time Pattern Detection**: Uses our 6-month analysis of 507 review comments
- **Pre-commit Integration**: Automatically runs all quality checks
- **Issue Prevention**: Catches 62.5% of review issues before submission

**📋 Complete Guide:** See [Claude Code Integration Guide](docs/claude-code-integration-guide.md) for the full AI-assisted workflow.

> **💡 Quick Start with Claude Code:** Simply start a Claude Code session and type:
> `"I need to develop a driver for the [DEVICE] [TYPE]"`
> Claude will automatically create your branch and guide you through PMBus command selection.

---

## Common Review Issues & Avoidance

**📊 QA Automation based on 6-month analysis (144 PRs, 507 comments, Aug 2025 - Feb 2026):**

> **📋 Primary Analysis:** Our automated quality tools use patterns from [6-Month Review Analysis](docs/no-os-review-pattern-analysis.md) providing 62.5% issue prevention coverage.

### 1. Error Handling (107 occurrences, 21.1%)

**❌ Common Issues:**
```c
// Missing null pointer checks
int32_t my_func(struct my_dev *dev) {
    return dev->spi_desc->transfer(); // Could crash if dev is NULL
}

// Not checking return values
no_os_spi_write_and_read(dev->spi_desc, data, 2); // Should check return
```

**✅ Best Practices:**
```c
// Proper error handling
int32_t my_func(struct my_dev *dev) {
    int32_t ret;

    if (!dev || !dev->spi_desc)
        return -EINVAL;

    ret = no_os_spi_write_and_read(dev->spi_desc, data, 2);
    if (ret < 0)
        return ret;

    return 0;
}

// Cleanup on error
int32_t my_init(struct my_dev **device, struct my_init_param init) {
    struct my_dev *dev;
    int32_t ret;

    dev = no_os_calloc(1, sizeof(*dev));
    if (!dev)
        return -ENOMEM;

    ret = no_os_spi_init(&dev->spi_desc, &init.spi_init);
    if (ret < 0)
        goto error_free;

    ret = no_os_gpio_init(&dev->gpio_reset, &init.gpio_reset);
    if (ret < 0)
        goto error_spi;

    *device = dev;
    return 0;

error_spi:
    no_os_spi_remove(dev->spi_desc);
error_free:
    no_os_free(dev);
    return ret;
}
```

### 2. Documentation Issues (62 occurrences, 12.2%)

**❌ Common Issues:**
```c
// Missing Doxygen comments
int32_t configure_device(struct my_dev *dev, uint8_t mode);

// Incomplete parameter documentation
/**
 * @brief Configure device.
 * @param dev - Device.
 * @return Status.
 */
```

**✅ Best Practices:**
```c
/**
 * @brief Configure device operating mode.
 *
 * Sets the device to the specified operating mode and validates
 * the configuration was applied correctly.
 *
 * @param dev  - The device structure.
 * @param mode - Operating mode to set:
 *               0 - Normal mode
 *               1 - Low power mode
 *               2 - High performance mode
 *
 * @return 0 in case of success, negative error code otherwise.
 *         -EINVAL if dev is NULL or mode is invalid.
 *         -EIO if SPI communication fails.
 */
int32_t configure_device(struct my_dev *dev, uint8_t mode);
```

### 3. Type Safety Issues (31 occurrences, 6.1%)

**❌ Common Issues:**
```c
// Wrong header guard format
#ifndef AD7980_H
#define AD7980_H

// Missing includes
struct no_os_spi_desc *spi; // no_os_spi.h not included
```

**✅ Best Practices:**
```c
// Correct header guard format
#ifndef __DEVICE_NAME_H__
#define __DEVICE_NAME_H__

#include <stdint.h>
#include "no_os_spi.h"    // For SPI structures
#include "no_os_gpio.h"   // For GPIO structures
#include "no_os_error.h"  // For error codes

// ... declarations ...

#endif /* __DEVICE_NAME_H__ */
```

### 4. Header Guards & Includes (24 occurrences, 4.7%)

**❌ Common Issues:**
```c
// Magic numbers
no_os_mdelay(100);        // What is this delay for?
if (status & 0x80) {      // What does bit 7 mean?
    result = data * 3.3;  // Magic voltage reference
}
```

**✅ Best Practices:**
```c
// Named constants
#define DEVICE_RESET_DELAY_MS       100
#define DEVICE_STATUS_READY_MSK     NO_OS_BIT(7)
#define DEVICE_VREF_VOLTAGE_V       3.3f

no_os_mdelay(DEVICE_RESET_DELAY_MS);
if (status & DEVICE_STATUS_READY_MSK) {
    result = data * DEVICE_VREF_VOLTAGE_V;
}
```

### 5. Testing Issues (22 occurrences, 4.3%)

**❌ Common Issues:**
```c
// Unsafe casting
uint8_t *ptr = (uint8_t*)&data[1];  // Potential buffer overflow
*((uint16_t*)ptr) = value;         // Alignment issues

// Mixed signed/unsigned
int32_t count = -1;
if (count > sizeof(buffer)) {      // Always false due to unsigned comparison
```

**✅ Best Practices:**
```c
// Safe data handling
uint16_t value_be = no_os_get_unaligned_be16(&data[0]);
uint16_t value_le = no_os_get_unaligned_le16(&data[2]);

// Consistent types
uint32_t count = 0;
if (count >= sizeof(buffer)) {
```

### 6. Code Organization Issues (21 occurrences, 4.1%)

*Additional categories with lower frequency: Constants/Magic Numbers (2.4%), Code Style (2.4%), Naming Conventions (1.8%)*

**❌ Common Issues:**
```c
// Inconsistent naming
#define AD7980_REG1     0x01      // Should specify what REG1 is
#define ad7980_READY    0x80      // Mixed case
int32_t AD7980_Init();            // Wrong case for function
```

**✅ Best Practices:**
```c
// Consistent device prefix + descriptive names
#define AD7980_REG_STATUS           0x01
#define AD7980_REG_CONFIG           0x02
#define AD7980_STATUS_READY_MSK     NO_OS_BIT(7)
int32_t ad7980_init();            // Lowercase function names
```

---

## Git Workflow & Commit Patterns

### Repository Setup

**Standard Fork Workflow (Recommended):**

The no-OS repository should be set up with two remotes for proper contribution workflow:

```bash
# Initial setup (one-time only)
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/no-OS.git
cd no-OS

# 3. Set up remotes
git remote add upstream https://github.com/analogdevicesinc/no-OS.git
git remote set-url origin https://github.com/YOUR_USERNAME/no-OS.git

# Verify setup
git remote -v
# Should show:
# origin    https://github.com/YOUR_USERNAME/no-OS.git (fetch)
# origin    https://github.com/YOUR_USERNAME/no-OS.git (push)
# upstream  https://github.com/analogdevicesinc/no-OS.git (fetch)
# upstream  https://github.com/analogdevicesinc/no-OS.git (push)
```

**Staying Current with Upstream:**

```bash
# Regularly sync with upstream (recommended before starting new work)
git checkout main
git fetch upstream
git rebase upstream/main
git push origin main

# Or use the shorthand helper
git pull --rebase upstream main
git push origin main
```

**Remote Naming Convention:**
- **`upstream`** = Original ADI no-OS repository (analogdevicesinc/no-OS)
- **`origin`** = Your personal fork (YOUR_USERNAME/no-OS)

This setup allows you to:
- ✅ **Stay current** with latest no-OS changes
- ✅ **Push work** to your fork without affecting the main repository
- ✅ **Create PRs** from your fork back to upstream
- ✅ **Collaborate** with other developers safely

### Branching Strategy

**Branch Naming Convention:**
All development branches must follow the pattern: `dev/<specific_device_name>`

**🚨 Linux Kernel Principle**: Use explicit device names, never generic wildcards

```bash
# Sync with upstream before starting new work
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main

# Create development branch for new device
git checkout -b dev/adm1275          # For ADM1275 PMBus device
git checkout -b dev/ltc2978          # For LTC2978 power supply
git checkout -b dev/ad7091r5         # For AD7091R5 ADC

# Work on your changes
git add drivers/power/adm1275/
git commit -s -m "drivers: power: adm1275: add initial driver implementation"

# Add project support
git add projects/adm1275-eval/
git commit -s -m "projects: adm1275-eval: add evaluation project"

# Push to your fork
git push origin dev/adm1275

# Submit PR from your fork to upstream
gh pr create --repo analogdevicesinc/no-OS \
             --title "drivers: power: adm1275: add support for ADM1275 PMBus monitor" \
             --body "Add driver for ADM1275 digital power monitor with I2C interface..."
```

**Branching Rules:**
- **Device drivers**: `dev/<specific_device_name>` (e.g., `dev/adm1275`, `dev/ltc2978`)
- **Family drivers**: `dev/<primary_device_name>` (e.g., `dev/ltm4700` for LTM470x family)
- **Platform support**: `dev/<device_name>-<platform>` (e.g., `dev/adm1275-maxim`)
- **Bug fixes**: `dev/<device_name>-fix-<issue>` (e.g., `dev/adm1275-fix-telemetry`)

**❌ Linux Principle Violations - Avoid these patterns:**
- ❌ `dev/ad717x` or `dev/adm127x` (generic family names)
- ❌ `dev/power-device` or `dev/adc-driver` (wildcard-style names)
- ❌ `feature/add-device` (too generic)
- ❌ `my-device-branch` (not following convention)
- ❌ `dev-branch` (not specific)
- ❌ `adm1275` (missing dev/ prefix)

**✅ Correct Linux-compliant patterns:**
- ✅ `dev/ltm4700` (even if supporting LTM4777 too - use primary device name)
- ✅ `dev/ad7175` (even if supporting AD7176/AD7177 - specific device identification)

### Common Git Operations

**Starting New Work:**
```bash
# Always start from updated main
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main

# Create new development branch
./tools/pre-commit/new-dev-branch.sh adm1275
# This creates dev/adm1275 and switches to it
```

**During Development:**
```bash
# Regular commits
git add .
git commit -s -m "drivers: power: adm1275: implement telemetry functions"

# Periodic sync with upstream (if main branch has updates)
git fetch upstream
git rebase upstream/main  # Rebase your branch on latest upstream
```

**Preparing for PR:**
```bash
# Final sync and cleanup
git fetch upstream
git rebase upstream/main

# Push to your fork
git push origin dev/adm1275

# If you need to force push after rebasing (be careful!)
git push --force-with-lease origin dev/adm1275
```

**Creating Pull Request:**
```bash
# Create PR from your fork to upstream
gh pr create --repo analogdevicesinc/no-OS \
             --head YOUR_USERNAME:dev/adm1275 \
             --base main \
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

**After PR Merge:**
```bash
# Clean up local branches
git checkout main
git fetch upstream && git rebase upstream/main
git push origin main

# Delete merged branch
git branch -d dev/adm1275
git push origin --delete dev/adm1275
```

### Git Helper Commands

Create these aliases in your `.gitconfig` for easier workflow:

```ini
[alias]
    # Sync with upstream
    sync = !git fetch upstream && git rebase upstream/main

    # Push to origin with tracking
    pushup = !git push --set-upstream origin $(git branch --show-current)

    # Create signed commit
    cs = commit -s

    # Show branch status vs upstream
    status-upstream = !git log --oneline upstream/main..HEAD

    # Clean merged branches
    clean-branches = !git branch --merged | grep -E "dev/" | xargs -r git branch -d
```

Usage:
```bash
git sync                    # Update from upstream
git pushup                  # Push current branch to origin
git cs -m "commit message"  # Signed commit
git status-upstream         # See your commits vs upstream
git clean-branches          # Remove merged dev/ branches
```

### Commit Message Format

Follow this pattern consistently:

```
<scope>: <component>: <brief description>

[Optional detailed description]

```

**Examples:**
```
drivers: adc: ad7980: add initial driver implementation
drivers: adc: ad7980: fix initialization sequence
projects: ad7980-eval: add evaluation board support
docs: adc: ad7980: add driver documentation
ci: build: add ad7980-eval to build matrix
```

### Commit Organization

Organize changes across multiple logical commits:

1. **Core driver** - `drivers: <category>: <device>: add initial driver`
2. **Register definitions** - `drivers: <category>: <device>: add register definitions`
3. **Project/Example** - `projects: <device>-eval: add evaluation project`
4. **Documentation** - `docs: <category>: <device>: add driver documentation`
5. **Build integration** - `ci: build: add <device> projects to build matrix`

### Required Sign-offs

All commits **must** be signed off:

```bash
git commit -s -m "commit message"
```

This adds: `Signed-off-by: Your Name <your.email@analog.com>`

---

## Hardware Testing Requirements

Before PR approval, hardware testing is **mandatory** for:

1. **Device Communication** - SPI/I2C transactions work correctly
2. **Register Access** - Read/write operations function as expected
3. **Reset Sequences** - Proper device initialization
4. **Error Conditions** - Graceful handling of communication failures
5. **Multiple Platforms** - Test on primary target platforms

### Testing Checklist

- [ ] Device ID verification works
- [ ] All driver functions execute without errors
- [ ] Reset functionality operates correctly
- [ ] Register read/write operations succeed
- [ ] Error paths handle failures gracefully
- [ ] Memory cleanup prevents leaks
- [ ] Multiple init/remove cycles work
- [ ] Project builds and runs on target hardware

---

## Architecture Overview

### Directory Structure
- **drivers/**: Hardware drivers organized by function (adc, dac, power, frequency, etc.)
- **drivers/platform/**: Platform abstraction layer for different microcontrollers/FPGAs
- **projects/**: Complete reference applications for specific hardware boards
- **libraries/**: Third-party libraries (FreeRTOS, MQTT, FATFS, etc.)
- **include/**: Common headers and utility functions
- **tests/**: Unit tests organized by driver category
- **tools/scripts/**: Build scripts and automation tools
- **doc/**: Documentation source (Doxygen and Sphinx)

### Platform Abstraction
The codebase supports multiple embedded platforms through `drivers/platform/`:
- Xilinx FPGAs (primary)
- STM32 microcontrollers
- Maxim microcontrollers
- Mbed framework
- Raspberry Pi Pico
- ADuCM3029 microcontrollers
- Lattice FPGAs
- Linux (for testing)

Each platform implements a common API for GPIO, SPI, I2C, UART, and other peripherals.

### Driver Organization
Drivers follow a consistent pattern:
- Header file defining device API and structures
- Implementation file with platform-agnostic logic
- Platform-specific code abstracted through the platform layer
- Optional IIO (Industrial I/O) support for Linux compatibility

### Project Structure
Each project in `projects/` contains:
- `Makefile`: Platform-specific build configuration
- `builds.json`: Multi-platform build definitions
- `src/`: Source code specific to the project
- `src.mk`: Source file list and build dependencies
- `README.rst`: Project documentation

## Testing Framework

### Unit Tests (Ceedling Framework)
```bash
# Run all tests in a test directory
cd tests/drivers/<test_category>/
ceedling test:all

# Generate coverage reports
ceedling gcov:all utils:gcov

# Clean test workspace
ceedling clean
```

### Available Test Categories
- `tests/drivers/imu/`
- `tests/drivers/led/`
- `tests/drivers/power/`

---

## Documentation Standards

Documentation is auto-generated and available at:
- Doxygen API docs: http://analogdevicesinc.github.io/no-OS/doxygen/
- Wiki: https://wiki.analog.com/resources/no-os

When adding new drivers or modifying APIs, follow Doxygen comment format for automatic documentation generation.

### Required Documentation

1. **Driver Header** - Full Doxygen documentation for all public functions
2. **Project README** - Clear setup and usage instructions
3. **Register Definitions** - Document complex register layouts
4. **Examples** - Working code examples in project files

---

## Pre-Submission Checklist

Before creating a PR, verify:

### Code Quality
- [ ] AStyle formatting passes (`ci/astyle.sh`)
- [ ] Cppcheck analysis passes (`ci/cppcheck.sh`)
- [ ] No compiler warnings
- [ ] All functions have Doxygen documentation
- [ ] Error handling for all failure paths
- [ ] Consistent naming conventions

### Build System
- [ ] Driver builds successfully
- [ ] Project integrates without errors
- [ ] Multiple platforms compile (if applicable)
- [ ] `src.mk` includes all required dependencies

### Testing
- [ ] Hardware validation completed
- [ ] All driver functions tested
- [ ] Error conditions verified
- [ ] Memory leaks checked

### Documentation
- [ ] Header file fully documented
- [ ] Project README written (if new project)
- [ ] Commit messages follow format
- [ ] All commits signed off (`-s`)

### Review Preparation
- [ ] Compare against similar existing drivers
- [ ] Address common review issues proactively
- [ ] Clean, logical commit history
- [ ] PR description explains changes clearly

---

This guide provides the foundation for efficient driver development that aligns with no-OS standards and minimizes review iterations.