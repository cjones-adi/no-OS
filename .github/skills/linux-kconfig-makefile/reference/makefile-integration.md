# Makefile Integration Reference

## Makefile Structure

**Location**: Same directory as Kconfig:
- `drivers/iio/adc/Makefile`
- `drivers/iio/dac/Makefile`
- `drivers/hwmon/Makefile`

**Basic Syntax**:

```makefile
# SPDX-License-Identifier: GPL-2.0-only
#
# Makefile for IIO ADC drivers
#

obj-$(CONFIG_SYMBOL) += driver_name.o
```

## obj-$(CONFIG_*) Pattern

This is the core Makefile pattern:

```makefile
obj-$(CONFIG_AD7124) += ad7124.o
```

**How it works**:
- If `CONFIG_AD7124=y`: becomes `obj-y += ad7124.o` (built-in)
- If `CONFIG_AD7124=m`: becomes `obj-m += ad7124.o` (module)
- If `CONFIG_AD7124=n`: becomes `obj- += ad7124.o` (not compiled)

## Single-File Drivers

Most ADI drivers are single-file:

```makefile
obj-$(CONFIG_AD7124) += ad7124.o
obj-$(CONFIG_AD4130) += ad4130.o
obj-$(CONFIG_AD9081) += ad9081.o
```

This compiles `ad7124.c` → `ad7124.o` → `ad7124.ko` (if module).

## Multi-File Drivers

For drivers with multiple source files:

```makefile
# Core object name
obj-$(CONFIG_AD9467) += ad9467.o

# Multiple source files linked into one module
ad9467-y := ad9467_core.o ad9467_regs.o
```

**Pattern Explanation**:
- `obj-$(CONFIG_AD9467) += ad9467.o` - Defines the output module/object
- `ad9467-y := ad9467_core.o ad9467_regs.o` - Specifies source files to link together
- Result: `ad9467_core.c` + `ad9467_regs.c` → `ad9467.o` → `ad9467.ko`

## Composite Objects Pattern

### Basic Composite Object

```makefile
# Create composite object from multiple files
obj-$(CONFIG_AD7606) += ad7606.o
ad7606-y := ad7606_base.o ad7606_core.o
```

### Conditional Compilation

```makefile
# Main driver
obj-$(CONFIG_AD7606) += ad7606.o

# Interface implementations
obj-$(CONFIG_AD7606_IFACE_PARALLEL) += ad7606_par.o
obj-$(CONFIG_AD7606_IFACE_SPI) += ad7606_spi.o
```

### Complex Multi-File Example

```makefile
# Main module
obj-$(CONFIG_AXI_ADC) += axi_adc.o

# Core files always included
axi_adc-y := axi_adc_core.o axi_adc_buffer.o

# Conditionally add files based on sub-options
axi_adc-$(CONFIG_AXI_ADC_DEBUG) += axi_adc_debug.o
axi_adc-$(CONFIG_AXI_ADC_DMA) += axi_adc_dma.o
```

## Library Symbols

Helper libraries (symbols with no prompt):

```makefile
obj-$(CONFIG_AD_SIGMA_DELTA) += ad_sigma_delta.o
obj-$(CONFIG_AD_PULSAR) += ad_pulsar.o
```

These are automatically built when selected by drivers.

## Alphabetical Ordering

**CRITICAL**: Keep Makefile entries in **alphabetical order**:

```makefile
obj-$(CONFIG_AD4000) += ad4000.o
obj-$(CONFIG_AD4030) += ad4030.o
obj-$(CONFIG_AD4062) += ad4062.o
obj-$(CONFIG_AD4130) += ad4130.o  # <-- Insert alphabetically
obj-$(CONFIG_AD4134) += ad4134.o
obj-$(CONFIG_AD4170_4) += ad4170-4.o
```

**Exception**: Helper libraries often go first:

```makefile
obj-$(CONFIG_AD_SIGMA_DELTA) += ad_sigma_delta.o  # Library first
obj-$(CONFIG_AD7091R) += ad7091r-base.o  # Base driver

# Then alphabetical drivers
obj-$(CONFIG_AD7124) += ad7124.o
obj-$(CONFIG_AD7173) += ad7173.o
```

## Common Patterns

### Pattern 1: Bus Interface Variants

**Makefile**:

```makefile
obj-$(CONFIG_ADXL345) += adxl345_core.o
obj-$(CONFIG_ADXL345_I2C) += adxl345_i2c.o
obj-$(CONFIG_ADXL345_SPI) += adxl345_spi.o
```

### Pattern 2: Sigma-Delta Helper

```makefile
obj-$(CONFIG_AD_SIGMA_DELTA) += ad_sigma_delta.o
obj-$(CONFIG_AD7124) += ad7124.o
```

### Pattern 3: Conditional Components

```makefile
# Core driver
obj-$(CONFIG_AXI_SPI_ENGINE) += axi-spi-engine.o

# Optional components
axi-spi-engine-$(CONFIG_AXI_SPI_ENGINE_DEBUG) += axi-spi-engine-debug.o
```

## File Naming Conventions

### Module Names

**Kconfig symbol** → **Module filename**:
- `CONFIG_AD7124` → `ad7124.o` / `ad7124.ko`
- `CONFIG_AXI_ADC` → `axi_adc.o` / `axi_adc.ko`
- `CONFIG_AD4170_4` → `ad4170-4.o` / `ad4170-4.ko`

**Rules**:
- Use lowercase for module names
- Use hyphens for multi-part numbers: `ad4170-4.o` (not `ad4170_4.o`)
- Use underscores for word separation: `axi_adc.o`

### Source File Names

**Source file** → **Object file**:
- `ad7124.c` → `ad7124.o`
- `ad9467_core.c` → `ad9467_core.o`

**Convention**:
- Match Kconfig symbol in lowercase: `CONFIG_AD7124` → `ad7124.c`
- For multi-file drivers: `<base>_<component>.c` (e.g., `ad9467_core.c`)

## Integration with Kconfig

Makefile entries must match Kconfig symbols:

**Kconfig**:
```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	...
```

**Makefile**:
```makefile
obj-$(CONFIG_AD7124) += ad7124.o
```

**CRITICAL**: The symbol name must match exactly!

## Complete Integration Example

### Single-File Driver

**1. Kconfig** (`drivers/iio/adc/Kconfig`):
```kconfig
config AD9999
	tristate "Analog Devices AD9999 ADC driver"
	depends on SPI
	select IIO_BUFFER
```

**2. Makefile** (`drivers/iio/adc/Makefile`):
```makefile
obj-$(CONFIG_AD9999) += ad9999.o
```

**3. Source** (`drivers/iio/adc/ad9999.c`):
```c
// Driver implementation
```

### Multi-File Driver

**1. Kconfig** (`drivers/iio/adc/Kconfig`):
```kconfig
config AD9999
	tristate "Analog Devices AD9999 ADC driver"
	depends on SPI
```

**2. Makefile** (`drivers/iio/adc/Makefile`):
```makefile
obj-$(CONFIG_AD9999) += ad9999.o
ad9999-y := ad9999_core.o ad9999_spi.o ad9999_regs.o
```

**3. Source files**:
- `drivers/iio/adc/ad9999_core.c` - Core functionality
- `drivers/iio/adc/ad9999_spi.c` - SPI interface
- `drivers/iio/adc/ad9999_regs.c` - Register definitions

## Verification

### Check Compilation

```bash
# Configure kernel
make ARCH=arm zynq_xcomm_adv7511_defconfig

# Enable driver
scripts/config --enable AD9999

# Build
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# Verify object file exists
ls -la drivers/iio/adc/ad9999.o
ls -la drivers/iio/adc/ad9999.ko  # If built as module
```

### Check Symbol Definition

```bash
# Check if symbol is defined in .config
grep CONFIG_AD9999 .config

# Should see:
# CONFIG_AD9999=y  (built-in)
# or
# CONFIG_AD9999=m  (module)
```

## Best Practices

### 1. Maintain Alphabetical Order

Always keep entries alphabetically sorted:

```makefile
# Good
obj-$(CONFIG_AD7124) += ad7124.o
obj-$(CONFIG_AD7173) += ad7173.o
obj-$(CONFIG_AD7606) += ad7606.o

# Bad - out of order
obj-$(CONFIG_AD7606) += ad7606.o
obj-$(CONFIG_AD7124) += ad7124.o
obj-$(CONFIG_AD7173) += ad7173.o
```

### 2. Library Symbols First

Place helper libraries before drivers:

```makefile
# Helper libraries
obj-$(CONFIG_AD_SIGMA_DELTA) += ad_sigma_delta.o
obj-$(CONFIG_AD_PULSAR) += ad_pulsar.o

# Drivers (alphabetically)
obj-$(CONFIG_AD7124) += ad7124.o
obj-$(CONFIG_AD7173) += ad7173.o
```

### 3. Group Related Components

Keep related files together:

```makefile
# Core driver
obj-$(CONFIG_AD7606) += ad7606.o

# Interface variants
obj-$(CONFIG_AD7606_IFACE_PARALLEL) += ad7606_par.o
obj-$(CONFIG_AD7606_IFACE_SPI) += ad7606_spi.o
```

### 4. Use Consistent Naming

Follow naming conventions:
- Lowercase for filenames
- Hyphens for multi-part numbers: `ad4170-4.o`
- Underscores for word separation: `axi_adc.o`

### 5. Comment Complex Patterns

Add comments for non-obvious patterns:

```makefile
# AXI ADC core with optional DMA support
obj-$(CONFIG_AXI_ADC) += axi_adc.o
axi_adc-y := axi_adc_core.o
axi_adc-$(CONFIG_AXI_ADC_DMA) += axi_adc_dma.o
```

## Checkpatch Validation

```bash
# Check Makefile syntax
./scripts/checkpatch.pl --no-tree -f drivers/iio/adc/Makefile
```

## References

- [Kbuild Makefile Documentation](https://docs.kernel.org/kbuild/makefiles.html)
- [Kbuild Documentation](https://docs.kernel.org/kbuild/)
