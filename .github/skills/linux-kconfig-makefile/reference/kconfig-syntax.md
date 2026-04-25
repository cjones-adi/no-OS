# Kconfig Syntax Reference

## Language Overview

Kconfig is the Linux kernel's configuration system that organizes build options in a tree structure with dependencies. It enables users to select which components to include in the kernel (built-in or as modules).

**Key Concepts:**
- **Hierarchical Structure**: Options organized in menus and submenus
- **Dependencies**: Child options only appear if parents are visible
- **Tristate**: Three states - yes (y = built-in), module (m), or no (n)
- **Visibility Control**: Options shown/hidden based on dependencies
- **Symbol Naming**: Convention is CONFIG_SYMBOL_NAME (all uppercase with underscores)

## Configuration Entry Structure

Basic configuration entry:

```kconfig
config SYMBOL_NAME
	tristate "User-visible prompt text"
	depends on DEPENDENCY
	select REQUIRED_SYMBOL
	help
	  Help text explaining what this option does.
	  Must be indented with spaces or tab.
```

**IMPORTANT**: Indentation matters! Help text extent is determined by indentation level.

## Configuration Types

### Five Configuration Types

```kconfig
# Boolean: yes/no choice
config EXAMPLE_BOOL
	bool "Enable example feature"

# Tristate: yes/module/no choice (most common for drivers)
config EXAMPLE_TRISTATE
	tristate "Example driver support"

# String: text input
config EXAMPLE_STRING
	string "Enter configuration string"
	default "default value"

# Hexadecimal: hex values
config EXAMPLE_HEX
	hex "Memory address"
	default 0x44a00000

# Integer: integer values
config EXAMPLE_INT
	int "Buffer size"
	default 1024
	range 512 4096
```

**Best Practice**: Use `tristate` for drivers to allow module compilation.

## Tristate Explained

Tristate enables three states:
- **y** (yes): Compiled into kernel (built-in)
- **m** (module): Compiled as loadable module (.ko file)
- **n** (no): Not compiled at all

```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	# Can be built-in (y), module (m), or disabled (n)
```

Users see in menuconfig:
```
[ ] AD7124  # Disabled (n)
<M> AD7124  # Module (m)
<*> AD7124  # Built-in (y)
```

## Dependencies and Selection

### depends on

Restricts when an option is visible/selectable:

```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	# Only visible if SPI support is enabled
```

**Multiple dependencies** (logical AND):

```kconfig
config AD4130
	tristate "Analog Device AD4130 ADC Driver"
	depends on SPI
	depends on GPIOLIB
	depends on COMMON_CLK
	# All three must be enabled
```

**Conditional dependencies**:

```kconfig
config XILINX_XADC
	tristate "Xilinx XADC driver"
	depends on (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE)
	# Visible only on Xilinx platforms
```

### select

Forces another symbol to be enabled (minimum value):

```kconfig
config AD_SIGMA_DELTA
	tristate
	select IIO_BUFFER
	select IIO_TRIGGERED_BUFFER
	# When AD_SIGMA_DELTA is enabled, automatically enable these
```

**WARNING**: `select` ignores dependencies! Use carefully.

**Common Pattern** - Library symbol:

```kconfig
config AD_SIGMA_DELTA
	tristate  # No prompt - can't be selected directly

config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	select AD_SIGMA_DELTA  # Pulls in helper library
```

### imply

Weaker form of `select` - suggests a symbol but doesn't force it:

```kconfig
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD7124
	imply AD4130
	imply AD9081
	# These are suggested but can still be disabled
```

**Key Difference**:
- `select FOO`: FOO is forced to minimum value (ignoring dependencies)
- `imply FOO`: FOO is suggested, but can still be set to 'n'

This is the **core of Kconfig.adi pattern**!

## Kconfig Entry Template for IIO Drivers

### Standard IIO Driver Entry

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

### Key Elements

**Prompt String** (`"Analog Devices AD7124 ADC driver"`):
- User-visible in menuconfig
- Should be concise but descriptive
- Mention chip family if applicable

**depends on**:
```kconfig
depends on SPI  # Requires SPI bus support
depends on GPIOLIB  # Uses GPIO functions
depends on COMMON_CLK  # Uses common clock framework
depends on (ARCH_ZYNQ || ARCH_ZYNQMP)  # Platform-specific
```

**select**:
```kconfig
select AD_SIGMA_DELTA  # Helper library (no prompt)
select REGMAP_SPI  # REGMAP SPI bus support
select IIO_BUFFER  # IIO buffering
select IIO_TRIGGERED_BUFFER  # Triggered buffer support
```

**Help text**:
- First line: "Say yes here to build support for..."
- List supported chip variants
- Add datasheet link if helpful
- End with module compilation instructions

### Complete Real Example (AD4130)

```kconfig
config AD4130
	tristate "Analog Device AD4130 ADC Driver"
	depends on SPI
	depends on GPIOLIB
	select IIO_BUFFER
	select IIO_KFIFO_BUF
	select REGMAP_SPI
	depends on COMMON_CLK
	help
	  Say yes here to build support for Analog Devices AD4130-8 SPI analog
	  to digital converters (ADC).

	  To compile this driver as a module, choose M here: the module will be
	  called ad4130.
```

## Common Patterns

### Pattern 1: Bus Interface Variants

For chips with multiple bus interfaces:

**Kconfig**:

```kconfig
config ADXL345
	tristate

config ADXL345_I2C
	tristate "Analog Devices ADXL345 3-Axis Accelerometer I2C Driver"
	depends on I2C
	select ADXL345
	select REGMAP_I2C

config ADXL345_SPI
	tristate "Analog Devices ADXL345 3-Axis Accelerometer SPI Driver"
	depends on SPI
	select ADXL345
	select REGMAP_SPI
```

### Pattern 2: Sigma-Delta Helper

Many ADI ADCs use the Sigma-Delta helper:

```kconfig
config AD_SIGMA_DELTA
	tristate  # No prompt - library symbol
	select IIO_BUFFER
	select IIO_TRIGGERED_BUFFER

config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	select AD_SIGMA_DELTA
```

### Pattern 3: REGMAP Selection

Most SPI/I2C drivers use REGMAP:

```kconfig
config AD4130
	tristate "Analog Device AD4130 ADC Driver"
	depends on SPI
	select REGMAP_SPI  # Automatically pulls in REGMAP framework

config LTC2991
	tristate "Analog Devices LTC2991 Voltage/Current/Temperature Monitor"
	depends on I2C
	select REGMAP_I2C
```

### Pattern 4: Platform-Specific AXI Drivers

FPGA IP cores for Xilinx platforms:

```kconfig
config CF_AXI_ADC
	tristate "Analog Devices AXI ADC driver"
	depends on (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE || COMPILE_TEST)
	select IIO_BUFFER
	select IIO_BUFFER_DMA
	help
	  Say yes here to build support for Analog Devices AXI ADC IP core.
	  The core is used in FPGA designs for interfacing high-speed ADCs.
```

### Pattern 5: COMPILE_TEST for Cross-Platform Testing

For exotic hardware, add `|| COMPILE_TEST` to dependencies:

```kconfig
config AXI_ADC
	tristate "Analog Devices AXI ADC driver"
	depends on (ARCH_ZYNQ || ARCH_ZYNQMP || COMPILE_TEST)
	# Can compile-test on any architecture
```

This allows CI to build-test drivers without requiring actual hardware platform.

## Alphabetical Ordering

**CRITICAL**: Keep Kconfig entries in **alphabetical order** within their menu:

```kconfig
config AD4000
	tristate "Analog Devices AD4000 ADC Driver"
	...

config AD4030
	tristate "Analog Devices AD4030 ADC Driver"
	...

config AD4062
	tristate "Analog Devices AD4062 Driver"
	...

config AD4130  # <-- Insert alphabetically
	tristate "Analog Device AD4130 ADC Driver"
	...

config AD4134
	tristate "Analog Device AD4134 ADC Driver"
	...
```

## Best Practices

### 1. Naming Conventions

**Kconfig symbols**:
- All uppercase: `CONFIG_AD7124`
- Use underscores: `CONFIG_AXI_SPI_ENGINE`
- Chip name as-is: `AD7124` not `AD_7124`

**Module names** (in help text):
- Lowercase: "called ad7124"
- Use hyphens for multi-word: "called ad4170-4"

### 2. Dependency Ordering

Order `depends on` and `select` logically:

```kconfig
config AD4130
	tristate "Analog Device AD4130 ADC Driver"
	depends on SPI        # Bus first
	depends on GPIOLIB    # Then subsystems
	depends on COMMON_CLK # Alphabetically
	select IIO_BUFFER           # Select frameworks
	select IIO_KFIFO_BUF        # Alphabetically
	select REGMAP_SPI
```

### 3. Help Text Quality

**Good**:

```kconfig
help
  Say yes here to build support for Analog Devices AD7124, AD7124-4
  and AD7124-8 SPI Sigma-Delta ADC.

  To compile this driver as a module, choose M here: the module will be
  called ad7124.
```

**Bad**:

```kconfig
help
  AD7124 driver  # Too brief, not helpful
```

## References

- [Kconfig Language Documentation](https://docs.kernel.org/kbuild/kconfig-language.html)
- [Kbuild Documentation](https://docs.kernel.org/kbuild/)
