# Architecture Guide

**Complete no-OS architecture overview and development patterns**

This guide provides comprehensive understanding of the no-OS architecture, platform abstraction, and development patterns for effective driver development.

## Repository Overview

### About no-OS

This is Analog Devices' no-OS repository containing hardware drivers and reference projects for embedded systems without an operating system. It supports microcontrollers, FPGAs, and other embedded platforms that interface with ADI hardware peripherals.

### Directory Structure

- **drivers/**: Hardware drivers organized by function (adc, dac, power, frequency, etc.)
- **drivers/platform/**: Platform abstraction layer for different microcontrollers/FPGAs
- **projects/**: Complete reference applications for specific hardware boards
- **libraries/**: Third-party libraries (FreeRTOS, MQTT, FATFS, etc.)
- **include/**: Common headers and utility functions
- **tests/**: Unit tests organized by driver category
- **tools/scripts/**: Build scripts and automation tools
- **doc/**: Documentation source (Doxygen and Sphinx)

## Platform Abstraction

### Supported Platforms

The codebase supports multiple embedded platforms through `drivers/platform/`:

- **Xilinx FPGAs** (primary)
- **STM32 microcontrollers**
- **Maxim microcontrollers**
- **Mbed framework**
- **Raspberry Pi Pico**
- **ADuCM3029 microcontrollers**
- **Lattice FPGAs**
- **Linux** (for testing)

Each platform implements a common API for GPIO, SPI, I2C, UART, and other peripherals.

### Platform API Structure

```c
/* Example: GPIO platform abstraction */
struct no_os_gpio_platform_ops {
    int32_t (*gpio_ops_get)(struct no_os_gpio_desc **desc,
                           const struct no_os_gpio_init_param *param);
    int32_t (*gpio_ops_get_optional)(struct no_os_gpio_desc **desc,
                                    const struct no_os_gpio_init_param *param);
    int32_t (*gpio_ops_remove)(struct no_os_gpio_desc *desc);
    int32_t (*gpio_ops_direction_input)(struct no_os_gpio_desc *desc);
    int32_t (*gpio_ops_direction_output)(struct no_os_gpio_desc *desc,
                                        uint8_t value);
    int32_t (*gpio_ops_get_direction)(struct no_os_gpio_desc *desc,
                                     uint8_t *direction);
    int32_t (*gpio_ops_set_value)(struct no_os_gpio_desc *desc,
                                 uint8_t value);
    int32_t (*gpio_ops_get_value)(struct no_os_gpio_desc *desc,
                                 uint8_t *value);
};
```

### Platform-Specific Constants

Each platform defines specific constants and configurations:

**Maxim Platform:**
```c
/* drivers/platform/maxim/maxim_uart.h */
#define MAX_UART_FLOW_DIS           0
#define MAX_UART_FLOW_EN            1
#define MAX_UART_PARITY_DISABLE     0
#define MAX_UART_PARITY_EVEN        2
#define MAX_UART_PARITY_ODD         3
```

**STM32 Platform:**
```c
/* drivers/platform/stm32/stm32_hal.h */
#define STM32_HAL_SPI_CS_LOW        GPIO_PIN_RESET
#define STM32_HAL_SPI_CS_HIGH       GPIO_PIN_SET
```

**Xilinx Platform:**
```c
/* drivers/platform/xilinx/xilinx_gpio.h */
#define XILINX_GPIO_DIR_INPUT       1
#define XILINX_GPIO_DIR_OUTPUT      0
```

## Driver Organization

### Standard Driver Pattern

Drivers follow a consistent pattern:

1. **Header file** defining device API and structures
2. **Implementation file** with platform-agnostic logic
3. **Platform-specific code** abstracted through the platform layer
4. **Optional IIO (Industrial I/O)** support for Linux compatibility

### Driver Categories

**Analog Front-End:**
- `drivers/adc/` - Analog-to-Digital Converters
- `drivers/dac/` - Digital-to-Analog Converters
- `drivers/amplifiers/` - Instrumentation amplifiers

**Power Management:**
- `drivers/power/` - Power regulators, monitors, controllers
- `drivers/battery/` - Battery management systems

**RF/Microwave:**
- `drivers/frequency/` - PLLs, synthesizers, VCOs
- `drivers/rf-transceiver/` - RF front-ends

**Digital Interface:**
- `drivers/digital-io/` - GPIO expanders, level shifters
- `drivers/imu/` - Inertial measurement units
- `drivers/temperature/` - Temperature sensors

### Device Structure Pattern

```c
struct device_dev {
    /* Communication interface */
    struct no_os_spi_desc       *spi_desc;    /* or i2c_desc */
    struct no_os_gpio_desc      *gpio_reset;  /* Optional control pins */

    /* Device configuration */
    uint8_t                     device_id;
    uint32_t                    sampling_freq;
    bool                        continuous_mode;

    /* Platform-specific data */
    void                        *platform_data;
};

struct device_init_param {
    /* Communication setup */
    struct no_os_spi_init_param spi_init;
    struct no_os_gpio_init_param gpio_reset;

    /* Device parameters */
    uint8_t                     device_id;
    uint32_t                    sampling_freq;
    bool                        continuous_mode;
};
```

## Project Structure

### Project Organization

Each project in `projects/` contains:

- **`Makefile`**: Platform-specific build configuration
- **`builds.json`**: Multi-platform build definitions
- **`src/`**: Source code specific to the project
- **`src.mk`**: Source file list and build dependencies
- **`README.rst`**: Project documentation

### Project Structure Template

```
projects/<device_name>/
├── Makefile              # Platform build selection
├── builds.json           # CI build matrix
├── src.mk               # Source dependencies and platform support
├── README.rst            # Complete project documentation
└── src/
    ├── common/
    │   ├── common_data.h  # Shared definitions
    │   └── common_data.c  # Platform-agnostic code
    ├── examples/
    │   └── basic/         # Usage examples
    │       ├── basic_example.c
    │       └── basic_example.h
    └── platform/
        ├── maxim/         # MAX32xxx platform files
        │   ├── main.c
        │   └── parameters.h
        ├── stm32/         # STM32 platform files
        │   ├── main.c
        │   └── parameters.h
        └── xilinx/        # Xilinx FPGA files
            ├── main.c
            └── parameters.h
```

### Build System Integration

**Project `src.mk` Template:**
```makefile
# Include common definitions
include $(NO-OS)/tools/scripts/generic_variables.mk

# Driver source files (individual files only - NO WILDCARDS)
SRCS += $(DRIVERS)/power/ltm4700/ltm4700.c
SRCS += $(DRIVERS)/power/ltm4700/iio_ltm4700.c

# Driver headers (individual directories)
INCS += $(DRIVERS)/power/ltm4700
INCS += $(INCLUDE)

# Required no-OS APIs
SRCS += $(DRIVERS)/api/no_os_i2c.c
SRCS += $(DRIVERS)/api/no_os_gpio.c
SRCS += $(DRIVERS)/api/no_os_crc8.c
SRCS += $(NO-OS)/util/no_os_alloc.c

# Platform drivers (based on PLATFORM variable)
SRCS += $(PLATFORM_DRIVERS)/$(PLATFORM)_gpio.c
SRCS += $(PLATFORM_DRIVERS)/$(PLATFORM)_i2c.c

# Platform headers
INCS += $(PLATFORM_DRIVERS)

# IIO support (if applicable)
ifeq ($(ENABLE_IIO),y)
SRCS += $(NO-OS)/iio/iio.c
INCS += $(NO-OS)/iio
endif

# Project source files
SRCS += $(PROJECT)/src/common/common_data.c
SRCS += $(PROJECT)/src/platform/$(PLATFORM)/main.c

# Include examples
include $(PROJECT)/src/examples.mk

# Include platform-specific makefile
include $(NO-OS)/tools/scripts/platform/$(PLATFORM)/platform.mk
```

## Build System

### Multi-Platform Build Commands

```bash
# Build all projects
python3 tools/scripts/build_projects.py . -export_dir exports -log_dir logs

# Build specific project
python3 tools/scripts/build_projects.py . -project=<project_name>

# Build for specific platform
python3 tools/scripts/build_projects.py . -platform=<platform> -project=<project_name>

# Supported platforms
PLATFORMS = xilinx stm32 maxim mbed pico aducm3029 lattice
```

### Build Configuration

**`builds.json` Template:**
```json
{
    "builds": [
        {
            "project": "ltm4700",
            "platforms": ["maxim", "stm32", "linux"],
            "flags": ["ENABLE_IIO=y"],
            "artifacts": {
                "maxim": "ltm4700.elf",
                "stm32": "ltm4700.bin",
                "linux": "ltm4700"
            }
        }
    ]
}
```

## Linux Kernel Naming Principle

**🚨 Critical Architecture Principle**

> Linux drivers must not rely on generic or wildcard‑style names to represent multiple devices. The kernel driver model requires explicit device matching via ID tables or device tree compatibles, and device naming stability is intentionally delegated to user space.

### Implementation Guidelines

**❌ Avoid Generic Names:**
- `device_nameX`, `sensor_driver`, `power_controller`
- `dev/ad717x` or `dev/adm127x` (generic family names)
- Directory wildcards in build system (`INCS += dir/**`)

**✅ Use Specific Device Names:**
- `ltm4700`, `adm1275`, `ad7980`
- `dev/ltm4700`, `dev/adm1275` (specific branch names)
- Individual file includes (`INCS += $(DRIVERS)/power/ltm4700`)

**✅ Family Support Through Code:**
```c
/* Support multiple devices through runtime identification */
switch (dev->device_id) {
case LTM4700_DEVICE_ID:
    /* LTM4700-specific handling */
    break;
case LTM4777_DEVICE_ID:
    /* LTM4777-specific handling */
    break;
default:
    return -ENODEV;
}
```

## IIO (Industrial I/O) Integration

### IIO Architecture

For monitoring devices (ADCs, power monitors, sensors), IIO integration provides standardized Linux kernel interface:

```c
struct iio_device {
    int                     num_channels;
    struct iio_ch_info      *channels;
    struct iio_attribute    *attributes;
    char                    *name;
    /* Driver-specific operations */
    int32_t (*read_raw)(void *device, char *buf, uint32_t len,
                       const struct iio_ch_info *channel,
                       intptr_t priv);
    int32_t (*write_raw)(void *device, char *buf, uint32_t len,
                        const struct iio_ch_info *channel,
                        intptr_t priv);
};
```

### IIO Channel Definition

```c
/* Example: Power monitor channels */
static struct iio_ch_info ltm4700_iio_channels[] = {
    {
        .name = "vin",
        .ch_num = 0,
        .type = IIO_VOLTAGE,
        .address = LTM4700_VIN_CHAN,
        .scan_index = 0,
        .scan_type = {
            .sign = 's',
            .realbits = 16,
            .storagebits = 16,
            .endianness = IIO_LE
        }
    },
    {
        .name = "iin",
        .ch_num = 1,
        .type = IIO_CURRENT,
        .address = LTM4700_IIN_CHAN,
        .scan_index = 1,
        .scan_type = {
            .sign = 's',
            .realbits = 16,
            .storagebits = 16,
            .endianness = IIO_LE
        }
    }
    /* Additional channels... */
};
```

## Documentation Standards

### Auto-Generated Documentation

Documentation is auto-generated and available at:
- **Doxygen API docs**: http://analogdevicesinc.github.io/no-OS/doxygen/
- **Wiki**: https://wiki.analog.com/resources/no-os

### Documentation Requirements

1. **Driver Header** - Full Doxygen documentation for all public functions
2. **Project README** - Clear setup and usage instructions
3. **Register Definitions** - Document complex register layouts
4. **Examples** - Working code examples in project files

### Doxygen Comment Format

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
int32_t device_configure_mode(struct device_dev *dev, uint8_t mode);
```

## Development Environment

### Required Tools

- **GCC toolchain** for target platforms
- **Build system** (make, CMake)
- **Ceedling** for unit testing
- **Git** for version control
- **Doxygen** for documentation

### Platform-Specific Requirements

**Xilinx Development:**
- Vivado/Vitis toolchain
- JTAG programmer

**STM32 Development:**
- ARM GCC toolchain
- ST-Link programmer
- STM32CubeMX (optional)

**Maxim Development:**
- MSDK (Maxim Software Development Kit)
- DAP-Link programmer

### Environment Setup

```bash
# Install common tools
sudo apt-get install build-essential git doxygen

# Install Ceedling for testing
gem install ceedling

# Install platform-specific toolchains
# (varies by platform - see platform-specific guides)
```

---

This architecture guide provides the foundation for understanding no-OS structure and developing effective drivers that integrate seamlessly with the platform abstraction layer.