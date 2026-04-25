---
name: linux-kconfig-makefile
description: Guide to Linux kernel Kconfig and Makefile build system integration, including ADI-specific Kconfig.adi patterns. Use when adding drivers to build system, creating Kconfig entries, working with dependencies, or troubleshooting build issues.
---

# Linux Kernel Kconfig and Makefile Build System

## AI Skill Triggers

This skill provides guidance on the Linux kernel build system. Activate this skill when the user mentions:

**Build System Integration**:
- "add driver to build system"
- "create Kconfig entry"
- "add to Makefile"
- "driver not compiling"
- "undefined reference"

**Configuration**:
- "Kconfig"
- "menuconfig"
- "defconfig"
- "tristate"
- "depends on"
- "select"
- "imply"

**ADI-Specific**:
- "Kconfig.adi"
- "IIO_ALL_ADI_DRIVERS"
- "CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT"
- "CI not building driver"

**Debugging**:
- "driver not building"
- "dependency issue"
- "circular dependency"
- "module not loading"
- "symbol not found"

## Quick Start: Adding a New Driver

When adding a new driver to the Linux kernel build system, follow this workflow:

### Step 1: Create Kconfig Entry

**Location**: Subsystem-specific Kconfig (e.g., `drivers/iio/adc/Kconfig`)

**Template**:

```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	select AD_SIGMA_DELTA
	select REGMAP_SPI
	help
	  Say yes here to build support for Analog Devices AD7124, AD7124-4
	  and AD7124-8 SPI Sigma-Delta ADC.

	  To compile this driver as a module, choose M here: the module will be
	  called ad7124.
```

**Key Elements**:
- **tristate**: Allows built-in (y), module (m), or disabled (n)
- **depends on**: Required dependencies (bus, subsystems)
- **select**: Helper libraries to auto-enable
- **help**: User-visible description

**Insert alphabetically** among existing entries.

### Step 2: Add Makefile Entry

**Location**: Same directory as Kconfig (e.g., `drivers/iio/adc/Makefile`)

**Template**:

```makefile
obj-$(CONFIG_AD7124) += ad7124.o
```

**Insert alphabetically** among existing entries.

**For multi-file drivers**:

```makefile
obj-$(CONFIG_AD9467) += ad9467.o
ad9467-y := ad9467_core.o ad9467_regs.o
```

### Step 3: Add to Kconfig.adi

**Location**: Subsystem Kconfig.adi (e.g., `drivers/iio/Kconfig.adi`)

**Template**:

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD7123  # Existing entry
	imply AD7124  # <-- Add new driver here (alphabetically)
	imply AD7125  # Existing entry
```

**With bus dependency**:

```kconfig
imply AD7124 if SPI
imply ADXL345_I2C if I2C
imply ADXL345_SPI if SPI
```

**CRITICAL**: Always use `imply`, never `select`. See `reference/kconfig-adi.md` for details.

### Step 4: Build and Test

```bash
# Configure kernel
make ARCH=arm zynq_xcomm_adv7511_defconfig

# Enable driver (IIO_ALL_ADI_DRIVERS already enabled in defconfig)
grep AD7124 .config  # Verify enabled

# Build
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# Verify object file
ls drivers/iio/adc/ad7124.o  # Should exist
```

## Core Concepts

### Kconfig Configuration Types

```kconfig
# Boolean (on/off)
config EXAMPLE_BOOL
	bool "Enable feature"

# Tristate (built-in/module/off) - Use for drivers!
config EXAMPLE_TRISTATE
	tristate "Driver support"

# String
config EXAMPLE_STRING
	string "Configuration value"
	default "default"

# Integer
config EXAMPLE_INT
	int "Buffer size"
	default 1024

# Hexadecimal
config EXAMPLE_HEX
	hex "Base address"
	default 0x44000000
```

**Best Practice**: Use `tristate` for drivers to allow module compilation.

### Kconfig Dependencies

**depends on** - Restricts visibility:

```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	depends on GPIOLIB
	# Only visible if SPI and GPIOLIB are enabled
```

**select** - Forces dependency:

```kconfig
config AD7124
	select AD_SIGMA_DELTA  # Automatically enables AD_SIGMA_DELTA
	select REGMAP_SPI
```

**WARNING**: `select` ignores dependencies. Use for helper libraries only.

**imply** - Suggests without forcing:

```kconfig
config IIO_ALL_ADI_DRIVERS
	imply AD7124  # Suggests AD7124 but respects dependencies
```

**Key Difference**:
- `select FOO`: Forces FOO to be enabled (ignoring FOO's dependencies)
- `imply FOO`: Suggests FOO but can still be disabled

### Makefile Integration

**Basic pattern**:

```makefile
obj-$(CONFIG_SYMBOL) += driver.o
```

**How it works**:
- If `CONFIG_SYMBOL=y`: becomes `obj-y += driver.o` (built-in)
- If `CONFIG_SYMBOL=m`: becomes `obj-m += driver.o` (module)
- If `CONFIG_SYMBOL=n`: becomes `obj- += driver.o` (not compiled)

**Multi-file driver**:

```makefile
obj-$(CONFIG_AD9467) += ad9467.o
ad9467-y := ad9467_core.o ad9467_regs.o ad9467_spi.o
```

### ADI Kconfig.adi Pattern

**Purpose**: Group all ADI drivers under single config option for CI build coverage.

**Structure**:

```kconfig
# drivers/iio/Kconfig.adi
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply IIO_BUFFER
	imply IIO_TRIGGERED_BUFFER
	imply AD7124 if SPI
	imply AD9081 if SPI
	imply ADXL345_I2C if I2C
	imply ADXL345_SPI if SPI
	# ... all IIO ADI drivers
```

**Why imply?**
- Respects driver dependencies (unlike `select`)
- Allows individual drivers to be disabled if needed
- Enables CI to verify all drivers can be built

**CI Check**: `CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT=1` verifies all drivers in Kconfig.adi are built.

## Common Patterns

### Pattern 1: Simple SPI Driver

**Kconfig** (`drivers/iio/adc/Kconfig`):
```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	select AD_SIGMA_DELTA
	select REGMAP_SPI
	help
	  Say yes here to build support for Analog Devices AD7124 ADC.

	  To compile this driver as a module, choose M here: the module will be
	  called ad7124.
```

**Makefile** (`drivers/iio/adc/Makefile`):
```makefile
obj-$(CONFIG_AD7124) += ad7124.o
```

**Kconfig.adi** (`drivers/iio/Kconfig.adi`):
```kconfig
imply AD7124 if SPI
```

### Pattern 2: Dual-Interface Driver (I2C + SPI)

**Kconfig** (`drivers/iio/imu/Kconfig`):
```kconfig
config ADXL345
	tristate

config ADXL345_I2C
	tristate "Analog Devices ADXL345 I2C Driver"
	depends on I2C
	select ADXL345
	select REGMAP_I2C

config ADXL345_SPI
	tristate "Analog Devices ADXL345 SPI Driver"
	depends on SPI
	select ADXL345
	select REGMAP_SPI
```

**Makefile** (`drivers/iio/imu/Makefile`):
```makefile
obj-$(CONFIG_ADXL345) += adxl345_core.o
obj-$(CONFIG_ADXL345_I2C) += adxl345_i2c.o
obj-$(CONFIG_ADXL345_SPI) += adxl345_spi.o
```

**Kconfig.adi** (`drivers/iio/Kconfig.adi`):
```kconfig
imply ADXL345_I2C if I2C
imply ADXL345_SPI if SPI
```

### Pattern 3: Platform-Specific Driver (AXI FPGA Core)

**Kconfig** (`drivers/iio/adc/Kconfig`):
```kconfig
config CF_AXI_ADC
	tristate "Analog Devices AXI ADC driver"
	depends on (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE || COMPILE_TEST)
	select IIO_BUFFER
	select IIO_BUFFER_DMA
	help
	  Say yes here to build support for Analog Devices AXI ADC IP core.
```

**Makefile** (`drivers/iio/adc/Makefile`):
```makefile
obj-$(CONFIG_CF_AXI_ADC) += cf_axi_adc.o
```

**Kconfig.adi** (`drivers/iio/Kconfig.adi`):
```kconfig
imply CF_AXI_ADC if (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE || COMPILE_TEST)
```

### Pattern 4: Helper Library

**Kconfig** (`drivers/iio/adc/Kconfig`):
```kconfig
config AD_SIGMA_DELTA
	tristate  # No prompt - can't be selected directly
	select IIO_BUFFER
	select IIO_TRIGGERED_BUFFER

config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	select AD_SIGMA_DELTA  # Pulls in helper
```

**Makefile** (`drivers/iio/adc/Makefile`):
```makefile
obj-$(CONFIG_AD_SIGMA_DELTA) += ad_sigma_delta.o
obj-$(CONFIG_AD7124) += ad7124.o
```

**Kconfig.adi** (`drivers/iio/Kconfig.adi`):
```kconfig
# Library is auto-enabled by drivers, no need to imply
imply AD7124 if SPI
```

## Troubleshooting Guide

### Driver Not Building

**Check 1**: Verify config is enabled
```bash
grep CONFIG_AD7124 .config
# Should see: CONFIG_AD7124=y or CONFIG_AD7124=m
```

**Check 2**: Verify dependencies are met
```bash
make ARCH=arm menuconfig
# Navigate to driver location
# If grayed out, check "Depends on:" line
```

**Check 3**: Verify Makefile entry exists
```bash
grep AD7124 drivers/iio/adc/Makefile
# Should see: obj-$(CONFIG_AD7124) += ad7124.o
```

**Check 4**: Verify source file exists
```bash
ls drivers/iio/adc/ad7124.c
```

### Undefined Reference Error

**Problem**: `undefined reference to 'ad_sd_read_reg'`

**Solution**: Add missing library to Kconfig

```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	select AD_SIGMA_DELTA  # <-- Add this
```

**How to find symbol**:
```bash
grep -r "ad_sd_read_reg" drivers/iio/
# Shows symbol is in ad_sigma_delta.c
# So select AD_SIGMA_DELTA
```

### CI Build Failure

**Problem**: `CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT` fails

**Cause**: Driver not in Kconfig.adi

**Solution**: Add to appropriate Kconfig.adi
```kconfig
imply AD7124 if SPI
```

### Circular Dependency

**Problem**: `recursive dependency detected!`

**Cause**: Dependency cycle
```kconfig
config FOO
	select BAR

config BAR
	depends on FOO  # Circular!
```

**Solution**: Break the cycle - change one to `depends on` or remove.

## Defconfig Management

### Loading Defconfig

```bash
# Zynq (ARM)
make ARCH=arm zynq_xcomm_adv7511_defconfig

# ZynqMP (ARM64)
make ARCH=arm64 adi_zynqmp_defconfig

# SoCFPGA (ARM)
make ARCH=arm socfpga_adi_defconfig
```

### Enabling Drivers

```bash
# Enable all ADI drivers (already in defconfigs)
grep IIO_ALL_ADI_DRIVERS .config
# Should see: CONFIG_IIO_ALL_ADI_DRIVERS=y

# Enable specific driver
scripts/config --enable AD7124

# Rebuild .config (resolves dependencies)
make ARCH=arm olddefconfig
```

### Updating Defconfig

```bash
# 1. Load defconfig
make ARCH=arm zynq_xcomm_adv7511_defconfig

# 2. Make changes via menuconfig or scripts/config
make ARCH=arm menuconfig

# 3. Save minimal defconfig
make ARCH=arm savedefconfig

# 4. Update defconfig file
cp defconfig arch/arm/configs/zynq_xcomm_adv7511_defconfig

# 5. Verify diff is minimal
git diff arch/arm/configs/zynq_xcomm_adv7511_defconfig
```

**Best Practice**: For new drivers, if they're already in Kconfig.adi, you don't need to modify defconfigs.

## Cross-Platform Testing

### ARM (32-bit)

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- zynq_xcomm_adv7511_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc) KCFLAGS="-Werror"
```

### ARM64 (64-bit)

```bash
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- adi_zynqmp_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) KCFLAGS="-Werror"
```

### x86_64 (Compile Test)

```bash
make defconfig
scripts/config --enable COMPILE_TEST
scripts/config --enable IIO_ALL_ADI_DRIVERS
make -j$(nproc) KCFLAGS="-Werror"
```

## Best Practices

### 1. Always Use Tristate for Drivers

```kconfig
# Good
config AD7124
	tristate "Analog Devices AD7124 ADC driver"

# Bad
config AD7124
	bool "Analog Devices AD7124 ADC driver"  # Can't be module!
```

### 2. Maintain Alphabetical Order

Keep entries sorted in:
- Kconfig files
- Makefile files
- Kconfig.adi files

### 3. Use imply in Kconfig.adi, Never select

```kconfig
# Good
imply AD7124 if SPI

# Bad
select AD7124  # Violates dependencies!
```

### 4. Add Conditionals for Bus Dependencies

```kconfig
# Good
imply AD7124 if SPI
imply ADXL345_I2C if I2C

# Bad
imply AD7124  # Missing SPI condition
```

### 5. Test on Multiple Architectures

Before submitting, test on:
- ARM (zynq_xcomm_adv7511_defconfig)
- ARM64 (adi_zynqmp_defconfig)
- x86_64 (with COMPILE_TEST)

### 6. Run Checkpatch

```bash
./scripts/checkpatch.pl --no-tree -f drivers/iio/adc/Kconfig
./scripts/checkpatch.pl --no-tree -f drivers/iio/adc/Makefile
```

## Complete Integration Example

Adding a new driver `AD9999`:

**1. Create Kconfig entry** (`drivers/iio/adc/Kconfig`):
```kconfig
config AD9999
	tristate "Analog Devices AD9999 ADC driver"
	depends on SPI
	select IIO_BUFFER
	select IIO_TRIGGERED_BUFFER
	select REGMAP_SPI
	help
	  Say yes here to build support for Analog Devices AD9999 high-speed
	  analog to digital converter.

	  To compile this driver as a module, choose M here: the module will be
	  called ad9999.
```

**2. Add Makefile entry** (`drivers/iio/adc/Makefile`):
```makefile
obj-$(CONFIG_AD9999) += ad9999.o
```

**3. Add to Kconfig.adi** (`drivers/iio/Kconfig.adi`):
```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD9998  # Existing
	imply AD9999  # <-- Add here
	imply ADA4250  # Existing
```

**4. Test**:
```bash
# Configure
make ARCH=arm zynq_xcomm_adv7511_defconfig

# Verify enabled
grep AD9999 .config

# Build
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# Verify object
ls drivers/iio/adc/ad9999.o
```

## Reference Documentation

For detailed information, see the reference documentation:

- **`reference/kconfig-syntax.md`** - Complete Kconfig language reference, types, dependencies, best practices
- **`reference/makefile-integration.md`** - Makefile patterns, obj-y/m, multi-file drivers, naming conventions
- **`reference/kconfig-adi.md`** - ADI-specific Kconfig.adi patterns, imply vs select, CI integration
- **`reference/debugging.md`** - Troubleshooting build issues, dependency problems, CI failures

## Related Skills

- **linux-devicetree**: Device tree bindings complement Kconfig/Makefile
- **linux-iio**: IIO subsystem patterns for driver implementation
- **linux-checkpatch-sparse**: Code quality checking before submission

## External References

- [Kconfig Language Documentation](https://docs.kernel.org/kbuild/kconfig-language.html)
- [Kbuild Documentation](https://docs.kernel.org/kbuild/)
- [Kbuild Makefiles](https://docs.kernel.org/kbuild/makefiles.html)

## ADI Repository Specifics

**Kconfig.adi locations**:
- `Kconfig.adi` - Top-level (all ADI drivers)
- `drivers/iio/Kconfig.adi` - IIO drivers
- `drivers/hwmon/Kconfig.adi` - HWMON drivers
- `drivers/clk/Kconfig.adi` - Clock drivers
- `sound/soc/codecs/Kconfig.adi` - Audio codecs

**Defconfig files**:
- `arch/arm/configs/zynq_xcomm_adv7511_defconfig` - Zynq reference
- `arch/arm64/configs/adi_zynqmp_defconfig` - ZynqMP reference
- `arch/arm/configs/socfpga_adi_defconfig` - SoCFPGA reference
- `arch/arm64/configs/adi_versal_defconfig` - Versal reference

**CI scripts**:
- `ci/travis/run-build.sh` - Build script
- `ci/travis/*_defconfig_compile_exceptions` - Platform-specific exceptions
