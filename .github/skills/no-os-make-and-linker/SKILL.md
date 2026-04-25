---
name: no-os-make-and-linker
description: 'Complete guide to Make build system and linker for ADI no-OS embedded projects. Use when setting up builds, adding drivers to src.mk, debugging compilation errors, configuring Makefiles, understanding linker scripts, troubleshooting undefined references, or working with cross-platform compilation for Maxim, STM32, Xilinx platforms.'
---

# Make and Linker Build System for ADI no-OS

This skill provides comprehensive understanding of how Make orchestrates builds and how the linker creates firmware in ADI no-OS projects.

**Key Concepts**:
- **make** orchestrates the build: deciding what to compile, when, and with which flags
- **linker** takes compiled object files and turns them into final executable firmware

## When to Use This Skill

Use this skill when you need to:
- Set up a new no-OS project's build system
- Add drivers or source files to `src.mk`
- Debug compilation or linking errors
- Understand Makefile variable configuration (`EXAMPLE`, `PLATFORM`, `ENABLE_*`)
- Configure conditional compilation with feature flags
- Troubleshoot "undefined reference" errors
- Understand memory layout and linker scripts
- Work with cross-platform builds (Maxim, STM32, Xilinx, Altera)
- Optimize build configurations
- Investigate why changes aren't reflected in builds

## Prerequisites

- Basic understanding of C compilation
- Familiarity with command-line tools
- Access to a no-OS project directory
- Appropriate toolchain installed (arm-none-eabi-gcc, etc.)

## What Make Does

`make` is a build automation tool that handles:

- **Dependency tracking** – Only recompiles files that changed
- **Source file management** – Determines which `.c` files to compile
- **Compiler configuration** – Applies the correct flags for your platform
- **Output generation** – Creates `.elf`, `.bin`, and `.hex` firmware files
- **Cross-platform builds** – Supports Maxim, STM32, Xilinx, Altera, and more

Without make, you would need to manually track hundreds of source files and remember complex compiler commands every time you build.

## Project Directory Structure

```
projects/max20370/
├── Makefile              # Main build configuration
├── src.mk                # Source files and drivers needed
├── src/                  # Project-specific source code
│   ├── common/           # Shared code across examples
│   ├── examples/         # Different example applications
│   │   └── basic/        # The "basic" example
│   └── platform/         # Platform-specific code
│       └── maxim/        # Maxim platform files
├── build/                # Generated during compilation
│   ├── objs/             # Object files (.o)
│   └── max20370.elf      # Final executable
└── README.rst            # Project documentation
```

## The Makefile Structure

A typical no-OS Makefile:

```makefile
EXAMPLE ?= basic
PLATFORM ?= maxim

ENABLE_AMOLED ?= y
ENABLE_REGULATORS ?= y
ENABLE_CHARGER ?= y
ENABLE_FUEL_GAUGE ?= y

include ../../tools/scripts/generic_variables.mk
include ../../tools/scripts/examples.mk
include src.mk
include ../../tools/scripts/generic.mk
```

### User-Configurable Variables

**EXAMPLE** – Which example to build
```makefile
EXAMPLE ?= basic  # Can override: make EXAMPLE=advanced
```

**PLATFORM** – Which hardware platform
```makefile
PLATFORM ?= maxim  # Options: maxim, stm32, xilinx, altera, mbed, pico, linux
```

**Feature Flags** – Conditional compilation
```makefile
ENABLE_CHARGER ?= y  # Set to 'y' (yes) or 'n' (no)
```

## The Include Chain

### 1. generic_variables.mk – Environment Setup

Defines directory paths and auto-detects platform:

```makefile
PROJECT           = /path/to/projects/max20370
NO-OS             = /path/to/no-os-fork
BUILD_DIR         = /path/to/projects/max20370/build
INCLUDE           = /path/to/no-os-fork/include
DRIVERS           = /path/to/no-os-fork/drivers
PLATFORM_DRIVERS  = /path/to/no-os-fork/drivers/platform/maxim
```

### 2. examples.mk – Example-Specific Files

Adds example directories to include paths:

```makefile
NO_OS_INC_DIRS += projects/max20370/src/examples/basic
                  projects/max20370/src/platform/maxim
SRC_DIRS += projects/max20370/src/examples/basic
```

### 3. src.mk – YOUR Project's Sources

**This is where YOU define what gets compiled:**

```makefile
# API Headers
INCS += $(INCLUDE)/no_os_i2c.h
        $(INCLUDE)/no_os_gpio.h

# API Sources
SRCS += $(DRIVERS)/api/no_os_i2c.c
        $(DRIVERS)/api/no_os_gpio.c

# Driver files
INCS += $(DRIVERS)/power/max20370/max20370.h
SRCS += $(DRIVERS)/power/max20370/max20370.c

# Conditional compilation
ifeq (y,$(ENABLE_CHARGER))
INCS += $(DRIVERS)/power/max20370/max20370-charger.h
SRCS += $(DRIVERS)/power/max20370/max20370-charger.c
CFLAGS += -DENABLE_CHARGER
endif
```

**Key variables:**
- `INCS` – Header files (for dependency tracking)
- `SRCS` – C source files to compile
- `CFLAGS` – Compiler flags (preprocessor defines, optimization levels)

### 4. generic.mk – Build Orchestrator

Defines build rules and includes platform-specific makefiles:

```makefile
ifeq 'maxim' '$(PLATFORM)'
include $(NO-OS)/tools/scripts/maxim.mk
endif
```

Each platform file defines:
- `CC` – C compiler (e.g., `arm-none-eabi-gcc`)
- `LD` – Linker
- Platform-specific `CFLAGS` and `LDFLAGS`
- Linker script path

## Build Process Flow

```
1. Read Makefile → Set EXAMPLE and PLATFORM

2. Include generic_variables.mk → Define paths

3. Include examples.mk → Add example directories

4. Include src.mk → Add all SRCS and INCS

5. Include generic.mk → Set up toolchain

6. Compile sources
   For each .c in SRCS:
   arm-none-eabi-gcc -c file.c -o build/objs/file.o

7. Link object files
   arm-none-eabi-gcc build/objs/*.o -o build/max20370.elf

8. Generate binary formats
   arm-none-eabi-objcopy max20370.elf → max20370.bin
```

## Compiler Flags (CFLAGS)

```makefile
CFLAGS += -DNO_OS_VERSION=$(GIT_VERSION)  # Define macros
CFLAGS += -DENABLE_CHARGER                # Conditional compilation
CFLAGS += -O2                             # Optimization level
CFLAGS += -g3                             # Debug symbols
CFLAGS += -Wall                           # Enable warnings
CFLAGS += -mcpu=cortex-m4                 # Target CPU
```

Enables conditional code in C:

```c
#ifdef ENABLE_CHARGER
    max20370_charger_init(&charger);
#endif
```

## The Linker's Role

The linker combines `.o` (object) files into one executable.

### Linker Script (.ld)

Defines:
- **Memory regions** – Where Flash and RAM are located
- **Section placement** – Where `.text` (code), `.data`, `.bss` go
- **Stack and heap sizes**
- **Entry point** – First function (usually `Reset_Handler`)

Example:

```ld
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x10000000, LENGTH = 512K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

SECTIONS
{
    .text : { *(.text*) } > FLASH
    .data : { *(.data*) } > RAM AT> FLASH
    .bss  : { *(.bss*)  } > RAM
}
```

### Linker Flags (LDFLAGS)

```makefile
LDFLAGS += -T linker_script.ld    # Use this linker script
LDFLAGS += -Wl,--gc-sections      # Remove unused code
LDFLAGS += -Wl,-Map=output.map    # Generate memory map
```

### Output Files

- `.elf` – Executable with debug info
- `.bin` – Raw binary for Flash programming
- `.hex` – Intel HEX format
- `.map` – Memory map showing placement

## How to Customize Builds

### Enable/Disable Features

In Makefile:
```makefile
ENABLE_FUEL_GAUGE ?= n
```

Command line:
```bash
make ENABLE_CHARGER=n
```

### Add a New Driver

In `src.mk`:
```makefile
INCS += $(DRIVERS)/power/max77779/max77779.h
SRCS += $(DRIVERS)/power/max77779/max77779.c
```

### Add Custom Compiler Flags

```makefile
CFLAGS += -DMY_CUSTOM_DEFINE
CFLAGS += -Os  # Optimize for size
```

### Change Example

```bash
make EXAMPLE=advanced
```

### Build for Different Platform

```bash
make PLATFORM=stm32
```

## Common Make Commands

| Command | Description |
|---------|-------------|
| `make` | Build the project |
| `make clean` | Remove all build artifacts |
| `make re` | Clean and rebuild |
| `make VERBOSE=y` | Show full compiler commands |
| `make EXAMPLE=advanced` | Build different example |
| `make ENABLE_CHARGER=n` | Build with feature disabled |

## Troubleshooting

### "No HARDWARE found"
- **Problem**: Can't detect platform
- **Solution**: Set `PLATFORM` explicitly in Makefile

### "undefined reference to..."
- **Problem**: Linker can't find function/variable
- **Solution**: Check that source file is in `SRCS` in `src.mk`

### "No such file or directory"
- **Problem**: Missing header file
- **Solution**: Add header path to `INCS`

### Changes not reflected in build
- **Problem**: Using cached object files
- **Solution**: Run `make clean` then `make`

### Feature not compiling
- **Problem**: Feature flag not propagated
- **Solution**: Check `ifeq (y,$(ENABLE_FEATURE))` and `CFLAGS += -DENABLE_FEATURE`

## Best Practices

1. **Always `make clean`** after changing feature flags
2. **Check `src.mk` first** when debugging missing symbols
3. **Use conditional compilation** with `ifeq` for optional features
4. **Keep platform code** in `src/platform/$(PLATFORM)/`
5. **Use make variables** like `$(DRIVERS)` instead of hardcoded paths
6. **Test with `VERBOSE=y`** to see exact commands
7. **Review `.map` file** to understand memory layout

## Common Patterns

### Conditional Driver Module

```makefile
ifeq (y,$(ENABLE_MY_FEATURE))
INCS += $(DRIVERS)/power/my_driver/my_driver.h
SRCS += $(DRIVERS)/power/my_driver/my_driver.c
CFLAGS += -DENABLE_MY_FEATURE
endif
```

### Platform-Specific Implementations

```makefile
SRCS += $(PLATFORM_DRIVERS)/$(PLATFORM)_i2c.c
SRCS += $(PLATFORM_DRIVERS)/$(PLATFORM)_gpio.c
```

### Utility Functions

```makefile
SRCS += $(NO-OS)/util/no_os_util.c
SRCS += $(NO-OS)/util/no_os_alloc.c
SRCS += $(NO-OS)/util/no_os_list.c
```

## Quick Reference

### Files to Modify
- **Makefile** – Set `EXAMPLE`, `PLATFORM`, `ENABLE_*` flags
- **src.mk** – Add/remove source files and drivers

### Files Generated
- `build/objs/*.o` – Object files
- `build/*.elf` – Executable with symbols
- `build/*.bin` – Raw binary firmware
- `build/*.map` – Memory map

### Key Variables
- `SRCS` – Source files to compile
- `INCS` – Header files
- `CFLAGS` – Compiler flags
- `LDFLAGS` – Linker flags
- `EXAMPLE` – Which example to build
- `PLATFORM` – Hardware platform

## Build Flow Diagram

```
┌─────────────────────────────────────┐
│ Makefile                            │
│  - EXAMPLE = basic                  │
│  - PLATFORM = maxim                 │
│  - ENABLE_* = y/n                   │
└────────────┬────────────────────────┘
             │
     ┌───────┴────────┐
     ▼                ▼
┌─────────────┐  ┌──────────────┐
│generic_vars │  │ examples.mk  │
│- Paths      │  │- Directories │
└──────┬──────┘  └──────┬───────┘
       │                │
       └────────┬───────┘
                ▼
        ┌───────────────┐
        │    src.mk     │
        │ - SRCS list   │
        │ - INCS list   │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │  generic.mk   │
        │- Build rules  │
        └───────┬───────┘
                ▼
     ┌──────────────────┐
     │ Compile & Link   │
     │ .c → .o → .elf   │
     └──────────────────┘
```

## Summary

This structure allows no-OS to support multiple platforms, examples, and configurations from a single, maintainable build system. Understanding these files helps you:
- Customize builds for different hardware
- Debug compilation and linking issues
- Add new features and drivers
- Optimize build configurations
- Maintain clean, portable projects

The key is understanding the include chain: `Makefile` → `generic_variables.mk` → `examples.mk` → `src.mk` → `generic.mk` → platform makefiles, each adding layers that determine what gets compiled and how.
