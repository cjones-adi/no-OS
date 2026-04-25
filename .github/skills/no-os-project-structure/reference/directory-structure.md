# Directory Structure Reference

Complete directory layouts and file organization patterns for no-OS projects.

## Modern Multi-Example Project Layout

```
projects/PROJECT_NAME/
├── Makefile                           # Top-level build orchestration
├── README.rst                         # Sphinx-compatible documentation
├── builds.json                        # Build configurations (platforms/examples)
├── src.mk                             # Project-specific build variables
└── src/
    ├── common/
    │   ├── common_data.c              # Device initialization parameters
    │   └── common_data.h              # Device configuration declarations
    ├── examples/
    │   ├── basic/
    │   │   └── basic_example.c        # Basic usage example
    │   ├── iio/
    │   │   ├── example.mk             # IIO-specific build config
    │   │   └── iio_example.c          # IIO example implementation
    │   └── iio_trigger/
    │       ├── example.mk
    │       └── iio_trigger_example.c
    └── platform/
        ├── maxim/
        │   ├── main.c                 # Platform entry point
        │   ├── parameters.c           # Platform hardware initialization
        │   ├── parameters.h           # Platform-specific defines/configs
        │   └── platform_src.mk        # Platform-specific build sources
        └── mbed/
            ├── main.c
            ├── parameters.c
            ├── parameters.h
            └── platform_src.mk
```

## Legacy/Simple Project Layout

For simple projects with a single example:

```
projects/PROJECT_NAME/
├── Makefile
├── README.rst
├── builds.json
├── src.mk
└── src/
    └── project_name.c                 # Monolithic implementation
```

## Directory Purposes

### src/common/
- **common_data.h**: Device initialization parameter declarations (extern)
- **common_data.c**: Device initialization parameter definitions
- Shared across all platforms and examples
- Contains device-specific configuration (not platform-specific)

### src/examples/{EXAMPLE}/
- **{name}_example.c**: Application code with `int example_main(void)` function
- **example.mk**: (Optional) Example-specific build configuration
- Each example is independently buildable
- Selected via `EXAMPLE` make variable

### src/platform/{PLATFORM}/
- **main.c**: Platform entry point that calls `example_main()`
- **parameters.h**: Platform-specific hardware definitions (pins, device IDs)
- **parameters.c**: Platform-specific structure initialization
- **platform_src.mk**: Platform-specific driver sources
- One subdirectory per supported platform

## File Organization Best Practices

### Separation of Concerns

**Device Code (src/common/)**:
- Device driver initialization parameters
- Device-specific configuration (ref voltage, device ID, etc.)
- Independent of physical hardware pins
- Portable across platforms

**Platform Code (src/platform/{PLATFORM}/)**:
- MCU-specific pin assignments
- Hardware peripheral IDs
- Platform-specific extras (GPIO voltage levels, etc.)
- Board-specific initialization

**Application Code (src/examples/{EXAMPLE}/)**:
- Use case implementation
- Device operation and control
- User interaction logic
- Independent of platform details

### When to Use Which Layout

**Use Multi-Example Layout when**:
- Multiple use cases (basic + IIO + advanced features)
- Supporting multiple platforms (Maxim + Mbed + STM32)
- Complex driver with different operating modes
- Need example-specific dependencies

**Use Simple Layout when**:
- Single example, single platform
- Proof-of-concept or minimal project
- Very simple driver with one use case
- Quick prototyping

## Common Directory Mistakes

**DON'T**:
- Mix platform and device code in same file
- Put hardware pin definitions in common_data.c
- Duplicate code between platforms
- Create platform-specific examples (examples should be portable)

**DO**:
- Keep clear separation: common/ vs platform/
- Use parameters.h macros for platform-specific values
- Share examples across all platforms
- Organize by logical function (common, platform, examples)
