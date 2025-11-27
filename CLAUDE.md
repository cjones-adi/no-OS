# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About no-OS

This is Analog Devices' no-OS repository containing hardware drivers and reference projects for embedded systems without an operating system. It supports microcontrollers, FPGAs, and other embedded platforms that interface with ADI hardware peripherals.

## Build System

### Primary Build Command
```bash
python3 tools/scripts/build_projects.py . -export_dir exports -log_dir logs
```

### Build Specific Projects
```bash
# Build specific project
python3 tools/scripts/build_projects.py . -project=<project_name>

# Build for specific platform
python3 tools/scripts/build_projects.py . -platform=<platform> -project=<project_name>

# Supported platforms: xilinx, stm32, maxim, mbed, pico, aducm3029
```

### Individual Project Builds
Within a project directory (e.g., `projects/max17616/`):
```bash
make
```

## Testing

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

## Code Quality & Linting

### Code Style (Astyle)
```bash
# CI runs this automatically, but for local checking:
astyle --options=ci/astyle_config <file.c>
```
Style: Linux kernel style, 8-space tabs, 80-character line limit

### Static Analysis (Cppcheck)
```bash
cppcheck -j$(nproc) --quiet --force --error-exitcode=1 --suppressions-list=.cppcheckignore .
```

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
- Xilinx FPGAs
- STM32 microcontrollers
- Maxim microcontrollers
- Mbed framework
- Raspberry Pi Pico
- ADuCM3029 microcontrollers
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

## Common Development Tasks

### Adding a New Driver
1. Create driver files in appropriate `drivers/<category>/` directory
2. Follow existing naming convention: `<device_name>.h/.c`
3. Implement standard initialization, read/write, and cleanup functions
4. Add platform-agnostic code using the platform abstraction layer
5. Update relevant project `src.mk` files if driver will be used

### Adding a New Project
1. Create project directory in `projects/`
2. Copy `Makefile` and `builds.json` from similar project
3. Create `src/` directory with application code
4. Create `src.mk` listing source files and dependencies
5. Add project to CI build matrix if needed

### Multi-Platform Development
- Use platform abstraction APIs from `include/` headers
- Test builds on multiple platforms using the build script
- Platform-specific code should be minimal and isolated
- Prefer platform-agnostic implementations when possible

## Documentation

Documentation is auto-generated and available at:
- Doxygen API docs: http://analogdevicesinc.github.io/no-OS/doxygen/
- Wiki: https://wiki.analog.com/resources/no-os

When adding new drivers or modifying APIs, follow Doxygen comment format for automatic documentation generation.

## Git Workflow

- Main development branch: `main`
- Stable releases: `20XX_R*` branches
- PRs should target `main` unless targeting specific release
- Follow the pull request template requirements
- All commits must be signed off (`git commit -s`)
- Hardware testing required for affected boards before merge