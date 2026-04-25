# Makefile Guide

Complete guide to no-OS project Makefiles including syntax, variables, and build chain.

## Standard Makefile Template

**Location**: `projects/PROJECT_NAME/Makefile`

**Standard Content**:
```makefile
include ../../tools/scripts/generic_variables.mk

# Optional: Set default example
EXAMPLE ?= iio

# Include example handling
include ../../tools/scripts/examples.mk

# Include project-specific sources
include src.mk

# Include generic build rules
include ../../tools/scripts/generic.mk
```

## Makefile Include Chain

The order of includes is critical:

```
1. generic_variables.mk      → Sets NO-OS, INCLUDE, DRIVERS, PLATFORM_DRIVERS
   ↓
2. examples.mk               → Includes platform_src.mk and example.mk
   ↓
3. src.mk                    → Project-specific drivers and sources
   ↓
4. platform_src.mk           → Platform-specific driver implementations
   ↓
5. example.mk                → Example-specific configuration
   ↓
6. generic.mk                → Actual build rules and targets
```

## What Each Makefile Provides

### generic_variables.mk
Sets up foundational path variables:
- `NO-OS` - Path to no-OS root directory
- `INCLUDE` - Path to include/ directory
- `DRIVERS` - Path to drivers/ directory
- `PLATFORM_DRIVERS` - Path to platform-specific drivers
- Platform/target detection logic

### examples.mk
- Auto-includes `src/platform/$(PLATFORM)/platform_src.mk`
- Auto-includes `src/examples/$(EXAMPLE)/*.mk` if exists
- Adds `src/examples/$(EXAMPLE)` to `SRC_DIRS`
- Enables example selection mechanism

### src.mk
Project-created file that defines:
- Device driver sources and headers (INCS, SRCS)
- Generic HAL interfaces needed
- Utility functions
- IIO framework dependencies

### platform_src.mk
Platform-created file that adds:
- Platform-specific driver sources (GPIO, SPI, I2C, etc.)
- Platform headers
- Platform-specific utilities (delay, etc.)

### example.mk
Example-created file (optional) that sets:
- Example-specific flags (IIOD, ENABLE_IIO_NETWORK)
- Example-specific sources
- Example-specific includes

### generic.mk
Provides all build rules and targets:
- Compilation rules
- Linking rules
- Clean targets
- Platform detection logic

## Variable Resolution Order

Variables are resolved in order (last definition wins):

```
generic_variables.mk  (defaults: PLATFORM, TARGET detection)
  ↓
src.mk               (device drivers: INCS, SRCS)
  ↓
platform_src.mk      (platform drivers override/extend INCS, SRCS)
  ↓
example.mk           (example-specific: IIOD, ENABLE_IIO_NETWORK, etc.)
```

## Key Makefile Variables

### Path Variables (Set by generic_variables.mk)

```makefile
NO-OS              # Root directory of no-OS framework
INCLUDE            # $(NO-OS)/include
DRIVERS            # $(NO-OS)/drivers
PLATFORM_DRIVERS   # $(NO-OS)/drivers/platform/$(PLATFORM)
```

### Build Variables

```makefile
PLATFORM           # Platform name: maxim, mbed, stm32, xilinx, pico
TARGET             # Specific target: max32690, max32655, etc.
EXAMPLE            # Example name: basic, iio, iio_trigger, etc.
RELEASE            # Release build flag (mainly for Mbed)
```

### Source Variables

```makefile
INCS               # Header files to include (.h)
SRCS               # Source files to compile (.c, .cpp)
SRC_DIRS           # Additional source directories (auto-scanned)
```

### Feature Flags

```makefile
IIOD               # Enable IIO daemon (set to 'y')
ENABLE_IIO_NETWORK # Enable IIO network transport (set to 'y')
```

## Example Selection Mechanism

When you run:
```bash
make EXAMPLE=iio TARGET=max32690
```

The build system:
1. Sets `EXAMPLE=iio` variable
2. Includes `src/examples/iio/*.mk` (if exists)
3. Adds `src/examples/iio/` to source search paths
4. Compiles `src/examples/iio/iio_example.c`
5. Linker resolves `example_main()` from compiled example
6. `main.c` calls `extern int example_main()`

## Default Example Pattern

Use `?=` to set a default but allow override:

```makefile
# Set default example (user can override with EXAMPLE=other)
EXAMPLE ?= basic
```

This allows:
- `make` → Uses EXAMPLE=basic
- `make EXAMPLE=iio` → Uses EXAMPLE=iio

## Build Commands

### Basic Commands

```bash
# Build with defaults
make

# Build specific example and target
make EXAMPLE=iio TARGET=max32690

# Clean build artifacts
make clean

# Complete rebuild
make clean && make

# List all build configurations
make list_of_builds
```

### Platform/Target Selection

```bash
# Auto-detect platform from TARGET
make TARGET=max32690  # Detects PLATFORM=maxim

# Explicit platform
make PLATFORM=maxim TARGET=max32690

# Platform-specific (Mbed example)
make PLATFORM=mbed RELEASE=y
```

### Verbose Build

```bash
# Show detailed compilation commands
make VERBOSE=y
```

## Common Makefile Patterns

### Conditional Platform Code

```makefile
# In src.mk or platform_src.mk
ifeq ($(PLATFORM), maxim)
    # Maxim-specific sources
    SRCS += platform_specific_maxim.c
endif

ifeq ($(PLATFORM), mbed)
    # Mbed-specific sources  
    SRCS += platform_specific_mbed.cpp
endif
```

### Multi-Target Support

```makefile
# In platform/maxim/parameters.h
#if (TARGET_NUM == 32690)
    #define UART_DEVICE_ID   0
    #define SPI_DEVICE_ID    1
#elif (TARGET_NUM == 32655)
    #define UART_DEVICE_ID   1
    #define SPI_DEVICE_ID    0
#endif
```

## Best Practices

**DO**:
- Keep Makefile minimal (just includes)
- Use EXAMPLE ?= for defaults
- Follow include order exactly
- Define sources in src.mk
- Use builds.json for configurations

**DON'T**:
- Hardcode EXAMPLE (prevents override)
- Mix build rules with includes
- Duplicate framework includes
- Put device drivers in Makefile
- Skip generic_variables.mk

## Troubleshooting

**"No rule to make target"**:
- Check include order in Makefile
- Verify src.mk paths are correct
- Ensure generic.mk is last include

**"PLATFORM not detected"**:
- Set TARGET explicitly: `make TARGET=max32690`
- Or set PLATFORM: `make PLATFORM=maxim`

**"EXAMPLE not working"**:
- Verify examples.mk is included
- Check src/examples/$(EXAMPLE)/ exists
- Ensure example file has test_* prefix in function

**Variables not taking effect**:
- Check variable resolution order
- Later includes override earlier ones
- Use VERBOSE=y to debug
