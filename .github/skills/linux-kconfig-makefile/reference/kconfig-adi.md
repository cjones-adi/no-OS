# Kconfig.adi Pattern Reference

## What is Kconfig.adi?

The ADI Linux repository uses a unique pattern: **Kconfig.adi** files that use `imply` statements to group all ADI drivers under a single configuration option.

**Purpose**:
- Enable all ADI drivers with a single config option
- Enforce CI build coverage via `CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT`
- Respect driver dependencies (unlike `select`)
- Allow individual drivers to be disabled if needed

**Location**: Each subsystem has one:
- `drivers/iio/Kconfig.adi` - IIO drivers
- `drivers/hwmon/Kconfig.adi` - HWMON drivers
- `drivers/net/phy/Kconfig.adi` - PHY drivers
- `drivers/clk/Kconfig.adi` - Clock drivers
- `sound/soc/codecs/Kconfig.adi` - Audio codecs
- etc.

## Kconfig.adi Structure

```kconfig
# drivers/iio/Kconfig.adi
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply IIO_BUFFER
	imply IIO_TRIGGERED_BUFFER
	imply AD7124
	imply AD4130
	imply AD9081
	imply AD9467
	imply LTC2497
	imply HMC425
	# ... hundreds more
```

**Key Elements**:
- Single config symbol to enable all ADI drivers in subsystem
- Uses `imply` (not `select`) to respect dependencies
- Alphabetically sorted entries
- Includes both framework dependencies and drivers

## Why imply Instead of select?

### Problem with select

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	select AD7124  # WRONG! Would force AD7124=y even if SPI=n (violates dependency!)
```

**Issue**: `select` ignores dependencies and forces the symbol to be enabled, potentially breaking the build.

### Solution with imply

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD7124  # Correct! Suggests AD7124 but respects "depends on SPI"
```

**Behavior**: If `SPI=n`, then `AD7124` can't be enabled even though it's implied.

### imply Semantics

From the user's perspective:
- When `IIO_ALL_ADI_DRIVERS=y`, all compatible drivers are enabled by default
- Drivers with unsatisfied dependencies remain disabled
- Individual drivers can still be manually disabled

## Conditional imply Patterns

### Bus Dependencies

For drivers with bus dependencies:

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply ADXL345_I2C if I2C
	imply ADXL345_SPI if SPI
	# Only imply if the bus is available
```

**Explanation**:
- `imply ADXL345_I2C if I2C` - Only suggest I2C variant if I2C bus support is enabled
- `imply ADXL345_SPI if SPI` - Only suggest SPI variant if SPI bus support is enabled

### Platform Dependencies

For platform-specific drivers:

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply XILINX_XADC if (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE)
	imply ALTERA_ARRIA10_JESD204_PHY if ARCH_INTEL_SOCFPGA
	imply AXI_ADC if (ARCH_ZYNQ || ARCH_ZYNQMP || COMPILE_TEST)
```

**Purpose**: Only enable platform-specific drivers when building for that platform.

### Complex Conditional Example

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	# Dual-interface accelerometer
	imply ADXL345_I2C if I2C
	imply ADXL345_SPI if SPI

	# Platform-specific FPGA core
	imply CF_AXI_ADC if (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE || COMPILE_TEST)

	# Simple SPI driver
	imply AD7124 if SPI

	# Driver with no special conditions
	imply AD9081
```

## Adding Driver to Kconfig.adi

### Step 1: Find Appropriate Kconfig.adi

Determine which subsystem your driver belongs to:

```bash
# For IIO drivers
vim drivers/iio/Kconfig.adi

# For HWMON drivers
vim drivers/hwmon/Kconfig.adi

# For network PHY drivers
vim drivers/net/phy/Kconfig.adi

# For clock drivers
vim drivers/clk/Kconfig.adi
```

### Step 2: Add imply Statement Alphabetically

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD7123  # Existing entry
	imply AD7124  # <-- Add new driver here (alphabetical)
	imply AD7125  # Existing entry
```

**CRITICAL**: Maintain strict alphabetical order!

### Step 3: Add Conditional if Needed

#### Bus-Specific Driver

```kconfig
# For SPI-only driver
imply AD7124 if SPI

# For I2C-only driver
imply LTC2991 if I2C
```

#### Dual-Interface Driver

```kconfig
# Driver with both I2C and SPI interfaces
imply AD7124_I2C if I2C
imply AD7124_SPI if SPI
```

#### Platform-Specific Driver

```kconfig
# Xilinx FPGA driver
imply AXI_ADC if (ARCH_ZYNQ || ARCH_ZYNQMP || COMPILE_TEST)

# Intel SoCFPGA driver
imply ALTERA_ARRIA10_JESD204_PHY if ARCH_INTEL_SOCFPGA
```

## CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT

### What is it?

The ADI CI system uses `CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT=1` to verify that all ADI drivers can be built.

**Process**:
1. Enable `IIO_ALL_ADI_DRIVERS=y` (or other subsystem equivalents)
2. Build with multiple defconfigs (ARM, ARM64, x86_64)
3. Verify all implied drivers compiled successfully
4. Fail the build if any ADI driver was not compiled

### Why is this Important?

**Problem**: Without this check, a driver could be:
- Added to Kconfig and Makefile but forgotten in Kconfig.adi
- Never built by CI
- Silently bitrot without anyone noticing

**Solution**: The CI check ensures every ADI driver is built at least once.

### CI Build Targets

ADI defconfigs that enable all drivers:

```bash
# ARM (Zynq)
make ARCH=arm zynq_xcomm_adv7511_defconfig
# Has: CONFIG_IIO_ALL_ADI_DRIVERS=y

# ARM64 (ZynqMP)
make ARCH=arm64 adi_zynqmp_defconfig
# Has: CONFIG_IIO_ALL_ADI_DRIVERS=y

# ARM (SoCFPGA)
make ARCH=arm socfpga_adi_defconfig
# Has: CONFIG_IIO_ALL_ADI_DRIVERS=y

# ARM64 (Versal)
make ARCH=arm64 adi_versal_defconfig
# Has: CONFIG_IIO_ALL_ADI_DRIVERS=y
```

All these defconfigs enable `*_ALL_ADI_DRIVERS` options.

### What Triggers CI Failure?

**Scenario 1**: Driver not in Kconfig.adi
```kconfig
# drivers/iio/adc/Kconfig
config AD9999
	tristate "Analog Devices AD9999 ADC driver"
	...

# drivers/iio/adc/Makefile
obj-$(CONFIG_AD9999) += ad9999.o

# drivers/iio/Kconfig.adi
# <-- MISSING: imply AD9999
```

**Result**: CI fails because `ad9999.o` was not built.

**Scenario 2**: Wrong conditional
```kconfig
# Driver depends on SPI
config AD9999
	depends on SPI

# But Kconfig.adi has no condition
imply AD9999  # WRONG! Should be: imply AD9999 if SPI
```

**Result**: On builds without SPI, driver won't be built, CI fails.

### Compile Exceptions

Some drivers are intentionally excluded from specific platforms:

**File**: `ci/travis/zynq_xcomm_adv7511_defconfig_compile_exceptions`

```
# Drivers that can't be built on Zynq ARM platform
CONFIG_SOME_X86_ONLY_DRIVER
CONFIG_ARCH_SPECIFIC_DRIVER
```

**Purpose**: Allow platform-specific drivers to be excluded from certain builds.

## Hierarchical Kconfig.adi Structure

### Top-Level Kconfig.adi

**File**: `Kconfig.adi` (repository root)

```kconfig
config KERNEL_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices drivers"
	imply IIO_ALL_ADI_DRIVERS
	imply HWMON_ALL_ADI_DRIVERS
	imply CLK_ALL_ADI_DRIVERS
	imply SND_SOC_ALL_ADI_CODECS
	help
	  Enable support for all Analog Devices drivers in the kernel.
```

**Purpose**: Single option to enable ALL ADI drivers across all subsystems.

### Subsystem-Level Kconfig.adi

Each subsystem has its own:

```kconfig
# drivers/iio/Kconfig.adi
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD7124
	imply AD9081
	# ... all IIO drivers

# drivers/hwmon/Kconfig.adi
config HWMON_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices HWMON Drivers"
	imply LTC2991
	imply LTC4245
	# ... all HWMON drivers

# drivers/clk/Kconfig.adi
config CLK_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices Clock Drivers"
	imply COMMON_CLK_AXI_CLKGEN
	imply AD9508
	# ... all clock drivers
```

## Real-World Examples

### IIO Subsystem

**File**: `drivers/iio/Kconfig.adi`

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	# Core framework dependencies
	imply IIO_BUFFER
	imply IIO_TRIGGERED_BUFFER

	# Helper libraries
	imply AD_SIGMA_DELTA
	imply AD_PULSAR

	# ADC drivers
	imply AD4000 if SPI
	imply AD4030 if SPI
	imply AD4130 if SPI
	imply AD7124 if SPI
	imply AD7606
	imply AD9081 if SPI

	# DAC drivers
	imply AD5758 if SPI
	imply AD9739A if SPI

	# Accelerometers
	imply ADXL345_I2C if I2C
	imply ADXL345_SPI if SPI

	# Platform-specific
	imply CF_AXI_ADC if (ARCH_ZYNQ || ARCH_ZYNQMP || COMPILE_TEST)
	imply XILINX_XADC if (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE)
```

### HWMON Subsystem

**File**: `drivers/hwmon/Kconfig.adi`

```kconfig
config HWMON_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices HWMON Drivers"
	imply ADM1266 if I2C
	imply ADM1275 if I2C
	imply LTC2945 if I2C
	imply LTC2991 if I2C
	imply LTC4245 if I2C
```

## Common Mistakes

### Mistake 1: Using select Instead of imply

**WRONG**:
```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	select AD7124  # WRONG! Ignores dependencies
```

**RIGHT**:
```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD7124  # Correct! Respects dependencies
```

### Mistake 2: Forgetting Bus Conditions

**WRONG**:
```kconfig
imply ADXL345_I2C  # Will fail if I2C is disabled
```

**RIGHT**:
```kconfig
imply ADXL345_I2C if I2C
imply ADXL345_SPI if SPI
```

### Mistake 3: Not Adding New Driver

**Problem**: Added driver to Kconfig and Makefile but forgot Kconfig.adi.

**Result**: CI doesn't build it, `CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT` fails.

**Solution**: Always add to Kconfig.adi when adding a new ADI driver!

### Mistake 4: Wrong Alphabetical Order

**WRONG**:
```kconfig
imply AD9081
imply AD7124  # Should come before AD9081!
imply AD4130  # Should come first!
```

**RIGHT**:
```kconfig
imply AD4130
imply AD7124
imply AD9081
```

### Mistake 5: Incomplete Conditionals

**WRONG**:
```kconfig
# Driver depends on both SPI and GPIOLIB
config AD4130
	depends on SPI
	depends on GPIOLIB

# But Kconfig.adi only checks SPI
imply AD4130 if SPI  # Missing GPIOLIB check!
```

**RIGHT**:
```kconfig
imply AD4130 if (SPI && GPIOLIB)
```

## Testing

### Local Testing

```bash
# 1. Clean build
make mrproper

# 2. Load defconfig
make ARCH=arm zynq_xcomm_adv7511_defconfig

# 3. Verify IIO_ALL_ADI_DRIVERS is enabled
grep IIO_ALL_ADI_DRIVERS .config
# Should see: CONFIG_IIO_ALL_ADI_DRIVERS=y

# 4. Verify your driver is enabled
grep AD9999 .config
# Should see: CONFIG_AD9999=y or CONFIG_AD9999=m

# 5. Build
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# 6. Verify driver was built
ls drivers/iio/adc/ad9999.o  # Should exist
```

### Using CI Scripts

```bash
# Set environment variables
export DEFCONFIG=zynq_xcomm_adv7511_defconfig
export ARCH=arm
export CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT=1

# Run CI build script
./ci/travis/run-build.sh
```

## Best Practices

### 1. Always Use imply, Never select

```kconfig
# Good
imply AD7124

# Bad
select AD7124
```

### 2. Add Conditionals for Bus Dependencies

```kconfig
# Good
imply AD7124 if SPI
imply ADXL345_I2C if I2C

# Bad
imply AD7124  # Missing SPI condition
```

### 3. Maintain Alphabetical Order

```kconfig
# Good
imply AD4130
imply AD7124
imply AD9081

# Bad
imply AD9081
imply AD4130
```

### 4. Add All New ADI Drivers

When adding a new driver:
1. Add to Kconfig
2. Add to Makefile
3. **Add to Kconfig.adi** (don't forget!)

### 5. Test with Multiple Architectures

```bash
# Test ARM
make ARCH=arm zynq_xcomm_adv7511_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# Test ARM64
make ARCH=arm64 adi_zynqmp_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)

# Test x86_64 (with COMPILE_TEST)
make defconfig
scripts/config --enable COMPILE_TEST
scripts/config --enable IIO_ALL_ADI_DRIVERS
make -j$(nproc)
```

## References

- `Kconfig.adi` - Top-level ADI driver configuration
- `drivers/iio/Kconfig.adi` - IIO ADI drivers
- `drivers/hwmon/Kconfig.adi` - HWMON ADI drivers
- `ci/travis/*_defconfig_compile_exceptions` - Platform-specific exceptions
- [Kconfig Language Documentation](https://docs.kernel.org/kbuild/kconfig-language.html)
