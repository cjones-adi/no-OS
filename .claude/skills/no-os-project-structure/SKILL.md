---
name: no-os-project-structure
description: 'Complete guide to creating and organizing no-OS projects. Use when creating new projects, understanding project layout, integrating drivers, configuring builds, setting up multi-platform support, organizing examples, or troubleshooting project structure issues.'
---

# no-OS Project Structure

Quick-start guide for creating and organizing no-OS projects with modular, multi-platform architecture.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/directory-structure.md**:
- User asks: "project layout", "directory structure", "how to organize files"
- Creating new project and needs detailed structure
- Questions about: src/common vs src/platform, file organization patterns
- Need: complete directory layouts, separation of concerns, best practices

**Triggers to read reference/makefile-guide.md**:
- User asks: "Makefile", "build system", "include chain", "how does build work"
- Mentions: generic_variables.mk, examples.mk, generic.mk
- Questions about: variable resolution, include order, build chain
- Build configuration issues or need complete Makefile syntax

**Triggers to read reference/src-mk-guide.md**:
- User asks: "src.mk", "what goes in src.mk", "how to add drivers"
- Questions about: INCS, SRCS, HAL interfaces, path variables
- Need: complete src.mk examples, conditional compilation, IIO integration
- Adding device drivers or utilities to project

**Triggers to read reference/platform-integration.md**:
- User asks: "add platform support", "platform-specific", "parameters.h"
- Mentions: Maxim, Mbed, STM32, Xilinx, Pico platforms
- Questions about: platform files, parameters.c, platform_src.mk
- Creating platform-specific code or porting to new platform

**Triggers to read reference/examples.md**:
- User asks: "step-by-step", "complete example", "walk me through"
- Need: full project creation workflow from scratch
- Questions about: ADC project, PMIC project, multi-example setup
- Want complete working examples with all files

---

## When to Use This Skill

- Creating a new no-OS project from scratch
- Understanding the project directory layout and file organization
- Integrating device drivers into a project
- Configuring the build system (Makefile, src.mk, builds.json)
- Adding multi-platform support (Maxim, Mbed, STM32, Xilinx)
- Organizing multiple examples within a single project
- Porting an existing project to a new platform
- Troubleshooting build configuration issues

## Architecture Overview

The no-OS framework uses **modular, layered architecture** with clear separation:

```
┌──────────────────────────────────────────────┐
│         Application Layer                    │
│  (src/examples/basic/, src/examples/iio/)    │
│  - Use case implementation                   │
│  - Device operation logic                    │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│         Device Layer                         │
│  (src/common/)                               │
│  - Device driver init params                 │
│  - Device configuration (portable)           │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│         Platform Layer                       │
│  (src/platform/maxim/, src/platform/mbed/)   │
│  - Hardware pin assignments                  │
│  - MCU-specific initialization               │
└──────────────────────────────────────────────┘
```

**Benefits**:
- Easy porting across multiple MCU platforms
- Reusable device drivers
- Multiple examples per project
- Flexible build configuration

---

## Quick Start: Essential Project Structure

### Minimal Project (Single Example)

```
projects/PROJECT_NAME/
├── Makefile                    # Build orchestration
├── builds.json                 # Build configurations
├── src.mk                      # Project drivers/dependencies
└── src/
    ├── common/
    │   ├── common_data.h       # Device init declarations
    │   └── common_data.c       # Device init definitions
    ├── examples/
    │   └── basic/
    │       └── basic_example.c # Application code
    └── platform/
        └── maxim/
            ├── main.c          # Platform entry point
            ├── parameters.h    # Hardware definitions
            ├── parameters.c    # Platform extras
            └── platform_src.mk # Platform drivers
```

### Multi-Example Project

```
projects/PROJECT_NAME/
├── Makefile
├── builds.json
├── src.mk
└── src/
    ├── common/
    │   ├── common_data.h
    │   └── common_data.c
    ├── examples/
    │   ├── basic/
    │   │   └── basic_example.c
    │   ├── iio/
    │   │   ├── example.mk      # Example-specific config
    │   │   └── iio_example.c
    │   └── advanced/
    │       └── advanced_example.c
    └── platform/
        ├── maxim/              # 4 files
        └── mbed/               # 4 files
```

---

## Essential Files Quick Reference

### 1. Makefile (Standard Template)

```makefile
include ../../tools/scripts/generic_variables.mk

EXAMPLE ?= basic  # Default example

include ../../tools/scripts/examples.mk
include src.mk
include ../../tools/scripts/generic.mk
```

**Key**: Order of includes matters. This is standard for all projects.

---

### 2. src.mk (Device Drivers)

```makefile
# Device driver
INCS += $(DRIVERS)/adc/ad4692/ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/ad4692.c

# HAL interfaces (SPI, GPIO, UART)
INCS += $(INCLUDE)/no_os_spi.h
INCS += $(INCLUDE)/no_os_gpio.h
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_spi.c
SRCS += $(DRIVERS)/api/no_os_gpio.c
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
SRCS += $(NO-OS)/util/no_os_util.c
```

**Common HAL Interfaces**:
- `no_os_spi.h` - SPI communication
- `no_os_i2c.h` - I2C communication
- `no_os_uart.h` - UART serial
- `no_os_gpio.h` - GPIO control
- `no_os_irq.h` - Interrupt handling
- `no_os_pwm.h` - PWM generation
- `no_os_timer.h` - Timer control

---

### 3. builds.json (Build Configurations)

```json
{
  "maxim": {
    "basic_example_max32690": {
      "flags": "EXAMPLE=basic TARGET=max32690"
    },
    "iio_example_max32690": {
      "flags": "EXAMPLE=iio TARGET=max32690"
    }
  },
  "mbed": {
    "basic_example": {
      "flags": "RELEASE=y EXAMPLE=basic"
    }
  }
}
```

**Format**: `{platform: {build_name: {flags: "MAKE_VARS"}}}`

---

### 4. common_data.h (Device Declarations)

```c
#ifndef __COMMON_DATA_H__
#define __COMMON_DATA_H__

#include "parameters.h"
#include "ad4692.h"
#include "no_os_uart.h"
#include "no_os_spi.h"
#include "no_os_gpio.h"

// Declare device init params (defined in common_data.c)
extern struct no_os_uart_init_param ad4692_uart_ip;
extern struct no_os_spi_init_param ad4692_spi_ip;
extern struct no_os_gpio_init_param ad4692_gpio_reset_ip;
extern struct ad4692_init_param ad4692_ip;

#endif
```

---

### 5. common_data.c (Device Definitions)

```c
#include "common_data.h"

// Device configuration (portable across platforms)
struct ad4692_init_param ad4692_ip = {
    .spi_ip = &ad4692_spi_ip,
    .gpio_reset = &ad4692_gpio_reset_ip,
    .ref_voltage = 5000,  // Device-specific
    .device_id = ID_AD4692,
};

// Platform init params use macros from parameters.h
struct no_os_uart_init_param ad4692_uart_ip = {
    .device_id = UART_DEVICE_ID,    // From parameters.h
    .irq_id = UART_IRQ_ID,
    .baud_rate = UART_BAUDRATE,
    .platform_ops = UART_OPS,
    .extra = UART_EXTRA,
};

struct no_os_spi_init_param ad4692_spi_ip = {
    .device_id = SPI_DEVICE_ID,     // From parameters.h
    .max_speed_hz = SPI_BAUDRATE,
    .chip_select = SPI_CS,
    .mode = NO_OS_SPI_MODE_0,
    .platform_ops = SPI_OPS,
    .extra = SPI_EXTRA,
};

struct no_os_gpio_init_param ad4692_gpio_reset_ip = {
    .port = GPIO_RESET_PORT,        // From parameters.h
    .number = GPIO_RESET_PIN,
    .platform_ops = GPIO_OPS,
    .extra = GPIO_EXTRA,
};
```

**Pattern**: Device params use macros from parameters.h, which are defined per-platform.

---

### 6. Platform Files (4 Files Per Platform)

#### parameters.h (Hardware Definitions)

```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "maxim_uart.h"
#include "maxim_spi.h"
#include "maxim_gpio.h"

// Platform-specific hardware definitions
#if (TARGET_NUM == 32690)
    #define UART_DEVICE_ID   0
    #define UART_IRQ_ID      UART0_IRQn
    #define UART_BAUDRATE    115200
    #define UART_OPS         &max_uart_ops
    #define UART_EXTRA       &uart_extra_ip

    #define SPI_DEVICE_ID    1
    #define SPI_BAUDRATE     1000000
    #define SPI_CS           0
    #define SPI_OPS          &max_spi_ops
    #define SPI_EXTRA        &spi_extra_ip

    #define GPIO_RESET_PORT  0
    #define GPIO_RESET_PIN   10
    #define GPIO_OPS         &max_gpio_ops
    #define GPIO_EXTRA       &gpio_extra_ip
#endif

extern struct max_uart_init_param uart_extra_ip;
extern struct max_spi_init_param spi_extra_ip;
extern struct max_gpio_init_param gpio_extra_ip;

#endif
```

#### parameters.c (Platform Extras)

```c
#include "parameters.h"

struct max_uart_init_param uart_extra_ip = {
    .flow = UART_FLOW_DIS
};

struct max_spi_init_param spi_extra_ip = {
    .num_slaves = 1,
    .polarity = SPI_SS_POL_LOW,
    .vssel = MXC_GPIO_VSSEL_VDDIOH,
};

struct max_gpio_init_param gpio_extra_ip = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,
};
```

#### main.c (Platform Entry Point)

```c
#include "parameters.h"
#include "common_data.h"

extern int example_main();

int main(void)
{
    return example_main();
}
```

#### platform_src.mk (Platform Drivers)

```makefile
INCS += $(PLATFORM_DRIVERS)/maxim_uart.h \
        $(PLATFORM_DRIVERS)/maxim_spi.h \
        $(PLATFORM_DRIVERS)/maxim_gpio.h

SRCS += $(PLATFORM_DRIVERS)/maxim_uart.c \
        $(PLATFORM_DRIVERS)/maxim_spi.c \
        $(PLATFORM_DRIVERS)/maxim_gpio.c \
        $(PLATFORM_DRIVERS)/maxim_delay.c
```

---

### 7. Example File (Application Code)

**src/examples/basic/basic_example.c**:
```c
#include <stdio.h>
#include "ad4692.h"
#include "common_data.h"
#include "no_os_uart.h"
#include "no_os_print_log.h"
#include "no_os_util.h"

int example_main(void)
{
    struct ad4692_desc *dev;
    struct no_os_uart_desc *uart;
    int ret;

    // Initialize UART
    ret = no_os_uart_init(&uart, &ad4692_uart_ip);
    if (ret)
        return ret;

    no_os_uart_stdio(uart);
    pr_info("Starting AD4692 example\n");

    // Initialize device
    ret = ad4692_init(&dev, &ad4692_ip);
    if (ret) {
        pr_err("Init failed: %d\n", ret);
        goto error_uart;
    }

    // Application logic here
    pr_info("Device initialized successfully\n");

    // Cleanup
    ad4692_remove(dev);
error_uart:
    no_os_uart_remove(uart);
    return ret;
}
```

**Key**: Function signature is always `int example_main(void)`.

---

## Build System Overview

### Include Chain (Order Matters)

```
generic_variables.mk  → Sets paths (NO-OS, INCLUDE, DRIVERS)
         ↓
examples.mk          → Handles example selection
         ↓
src.mk               → Project device drivers
         ↓
platform_src.mk      → Platform-specific drivers
         ↓
example.mk           → Example-specific config (optional)
         ↓
generic.mk           → Build rules and targets
```

### Example Selection

When you run:
```bash
make EXAMPLE=iio TARGET=max32690
```

The build system:
1. Includes `src/examples/iio/*.mk` (if exists)
2. Compiles `src/examples/iio/iio_example.c`
3. Links `example_main()` from iio_example.c
4. Platform `main()` calls `example_main()`

---

## Common Build Commands

```bash
# Build with defaults
make

# Build specific example and target
make EXAMPLE=iio TARGET=max32690

# Clean
make clean

# List all build configurations
make list_of_builds

# Complete rebuild
make clean && make

# Verbose build
make VERBOSE=y
```

---

## Common Variables

### Platform Selection
```makefile
PLATFORM=maxim    # Maxim MCUs
PLATFORM=mbed     # Arm Mbed
PLATFORM=stm32    # STM32 MCUs
PLATFORM=xilinx   # Xilinx FPGAs
PLATFORM=pico     # Raspberry Pi Pico
```

### Target Selection
```makefile
TARGET=max32690   # Specific MCU
TARGET=max32655
TARGET=max32670
```

### Feature Flags
```makefile
IIOD=y                  # Enable IIO daemon
ENABLE_IIO_NETWORK=y    # Enable IIO network
RELEASE=y               # Release build (Mbed)
```

---

## Project Creation Workflow

### Step 1: Create Structure
```bash
cd projects
mkdir my_project
cd my_project
mkdir -p src/common src/examples/basic src/platform/maxim
```

### Step 2: Create Build Files
- Create `Makefile` (standard template)
- Create `src.mk` (device drivers + HAL)
- Create `builds.json` (build configurations)

### Step 3: Create Common Files
- Create `src/common/common_data.h` (declarations)
- Create `src/common/common_data.c` (definitions)

### Step 4: Create Platform Files
- Create `src/platform/maxim/parameters.h` (hardware defs)
- Create `src/platform/maxim/parameters.c` (platform extras)
- Create `src/platform/maxim/main.c` (entry point)
- Create `src/platform/maxim/platform_src.mk` (platform drivers)

### Step 5: Create Example
- Create `src/examples/basic/basic_example.c` (application)

### Step 6: Build and Test
```bash
make EXAMPLE=basic TARGET=max32690
```

**See**: `reference/examples.md` for complete step-by-step examples.

---

## Adding Features

### Add New Example
1. Create `src/examples/new_example/`
2. Create `new_example.c` with `int example_main(void)`
3. (Optional) Create `example.mk` for special config
4. Add to `builds.json`
5. Build: `make EXAMPLE=new_example`

### Add New Platform
1. Create `src/platform/new_platform/`
2. Create 4 platform files (parameters.h/c, main.c, platform_src.mk)
3. Add to `builds.json`
4. Build: `make PLATFORM=new_platform`

### Add IIO Support
Create `src/examples/iio/example.mk`:
```makefile
IIOD = y
INCS += $(DRIVERS)/adc/ad4692/iio_ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/iio_ad4692.c
```

---

## Best Practices

### Separation of Concerns
**DO**:
- Device config in `src/common/`
- Platform config in `src/platform/{PLATFORM}/`
- Application code in `src/examples/{EXAMPLE}/`
- Use macros from parameters.h for platform values

**DON'T**:
- Mix platform and device code
- Hardcode pin numbers in common_data.c
- Put device logic in main.c

### Build Configuration
**DO**:
- Use `builds.json` for all build variants
- Set `EXAMPLE ?= default` in Makefile
- Follow standard include order
- Document build commands in README

**DON'T**:
- Hardcode EXAMPLE (prevents override)
- Skip generic_variables.mk or generic.mk
- Put device drivers in platform_src.mk

---

## Troubleshooting

### "No rule to make target..."
- Check driver path in src.mk is correct
- Verify driver file exists
- Ensure variables use correct prefixes: `$(DRIVERS)`, `$(INCLUDE)`

### "Undefined reference to example_main"
- Verify EXAMPLE variable is set
- Check `src/examples/$(EXAMPLE)/` exists
- Ensure function signature is `int example_main(void)`
- Verify examples.mk is included in Makefile

### "Platform not detected"
- Set explicitly: `make PLATFORM=maxim TARGET=max32690`
- Check builds.json for valid combinations

### "Conflicting types for parameters"
- Declare `extern` in .h files
- Define in .c files (not both)
- Never define same struct in common_data.c AND parameters.c

---

## Key Takeaways

- **Layered architecture**: Platform → Device → Application
- **Standard Makefile**: Always use the same include chain
- **Makefile variables**: Use `$(DRIVERS)`, `$(INCLUDE)`, `$(NO-OS)`, `$(PLATFORM_DRIVERS)`
- **parameters.h pattern**: Define macros for platform-specific values
- **common_data.c pattern**: Use macros from parameters.h
- **Example selection**: Via `EXAMPLE` variable, calls `example_main()`
- **Four files per platform**: parameters.h/c, main.c, platform_src.mk
- **builds.json**: Defines all valid build configurations

**For complete examples, detailed guides, and step-by-step walkthroughs, read the appropriate reference file based on triggers listed at the top of this document.**
