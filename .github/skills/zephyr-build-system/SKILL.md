---
name: zephyr-build-system
description: 'Complete guide to Zephyr build system including west commands, CMake integration, Kconfig, prj.conf, board overlays, virtual environment setup, and build troubleshooting. Use when setting up builds, creating samples, configuring drivers, debugging compilation errors, managing dependencies, or resolving build failures.'
---

# Zephyr Build System

This skill provides comprehensive understanding of the Zephyr build system, covering west commands, CMake integration, Kconfig configuration, devicetree overlays, and troubleshooting.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/west-commands.md**:
- User asks: "west commands", "west build", "west flash", "build options"
- Questions about: -p auto, -p always, -t menuconfig, build flags
- User mentions: "how to build", "west update", "west config"
- Need: complete west command reference with examples

**Triggers to read reference/cmake-patterns.md**:
- User mentions: "CMakeLists", "zephyr_library", "add driver to build"
- Questions about: application CMakeLists.txt, subsystem integration, source files
- User asks: "how to add driver", "CMake patterns"
- Need: CMakeLists.txt patterns for applications and drivers

**Triggers to read reference/kconfig-integration.md**:
- User mentions: "Kconfig", "CONFIG_", "depends on", "select", "menuconfig"
- Questions about: driver dependencies, configuration options, default values
- User asks: "add Kconfig entry", "driver configuration"
- Need: Kconfig patterns, dependency syntax, subsystem integration

**Triggers to read reference/app-config-overlays.md**:
- User mentions: "prj.conf", "overlay", "board overlay", "devicetree overlay"
- Questions about: application configuration, DT modifications, board-specific config
- User asks: "how to configure", "add overlay", "enable feature"
- Need: prj.conf patterns and devicetree overlay examples

**Triggers to read reference/troubleshooting.md**:
- User says: "build error", "not building", "CMake error", "undefined reference"
- Build/compilation errors
- Questions about: build failures, devicetree errors, linking issues
- Need: debugging steps for 8 common build errors

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "clean build", "incremental", "init priority"
- Questions about: build workflow, dependency checking, sorted order
- Need: 7 best practice patterns

---

## When to Use This Skill

Use this skill when you need to:
- Set up a Zephyr development environment
- Build Zephyr applications and samples
- Integrate new drivers into the build system
- Configure driver dependencies with Kconfig
- Create and manage board overlays
- Debug build errors and configuration issues
- Manage virtual environment (.venv) setup
- Troubleshoot west command failures

## What is the Zephyr Build System?

The **Zephyr build system** is a CMake-based infrastructure that manages:

- **West**: Meta-tool for workspace and build management
- **CMake**: Build system generator (creates Makefiles/Ninja files)
- **Kconfig**: Configuration system (enables/disables features)
- **Devicetree**: Hardware description and board-specific configuration
- **Python environment**: Virtual environment for west and build tools

### Key Components

- **West workspace**: Multi-repository structure managed by west manifest
- **CMakeLists.txt**: Build recipe for applications and drivers
- **Kconfig files**: Configuration options and dependencies
- **prj.conf**: Application-specific configuration
- **Board overlays**: Board-specific devicetree modifications
- **.venv**: Python virtual environment for isolated tool installation

### Benefits

- **Reproducible builds** – Consistent configuration across environments
- **Modular** – Easy driver and subsystem integration
- **Board-agnostic** – Same source builds for multiple targets
- **Configuration management** – Kconfig ensures consistent dependencies
- **Incremental builds** – Fast rebuilds after changes

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  West Workspace (zephyrproject/)                            │
│  ├── zephyr/           (Zephyr RTOS repository)             │
│  ├── bootloader/       (MCUboot)                            │
│  ├── modules/          (HALs, libraries)                    │
│  ├── tools/            (Build tools)                        │
│  └── .venv/            (Python virtual environment)         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴────────────────────┐
        │                                          │
┌───────▼────────┐                     ┌───────────▼──────────┐
│  Application   │                     │  Zephyr Build System │
│  (or Sample)   │                     │                      │
│                │                     │  CMake + Kconfig     │
│  CMakeLists.txt│────────────────────>│  + Devicetree        │
│  prj.conf      │                     │                      │
│  src/main.c    │                     │  Generates:          │
│  boards/*.overlay                    │  - Build config      │
└────────────────┘                     │  - Devicetree binary │
                                       │  - Makefiles/Ninja   │
                                       └──────────┬───────────┘
                                                  │
                                       ┌──────────▼───────────┐
                                       │  Build Tool          │
                                       │  (Make or Ninja)     │
                                       │                      │
                                       │  Compiles & Links    │
                                       └──────────┬───────────┘
                                                  │
                                       ┌──────────▼───────────┐
                                       │  zephyr.elf          │
                                       │  zephyr.bin          │
                                       │  zephyr.hex          │
                                       └──────────────────────┘
```

## Python Virtual Environment (.venv)

### Why Virtual Environment?

Zephyr requires specific Python packages (west, zcbor, etc.) that may conflict with system-wide installations. A virtual environment isolates these dependencies.

### Setup Virtual Environment

**Windows (Git Bash)**:
```bash
cd /path/to/zephyrproject
python -m venv .venv
source .venv/Scripts/activate
pip install west
west init -l zephyr
west update
pip install -r zephyr/scripts/requirements.txt
```

**Linux/macOS**:
```bash
cd /path/to/zephyrproject
python3 -m venv .venv
source .venv/bin/activate
pip install west
west init -l zephyr
west update
pip install -r zephyr/scripts/requirements.txt
```

### Activating Virtual Environment

**CRITICAL**: Always activate .venv before running west commands.

**Windows (Git Bash)**: `source .venv/Scripts/activate`  
**Windows (CMD)**: `.venv\Scripts\activate.bat`  
**Windows (PowerShell)**: `.venv\Scripts\Activate.ps1`  
**Linux/macOS**: `source .venv/bin/activate`

After activation, your prompt shows `(.venv)`:
```bash
(.venv) user@host:~/zephyrproject$
```

Verify west is from .venv:
```bash
which west  # Should show: /path/to/.venv/bin/west or .venv/Scripts/west
```

## Essential West Commands (Quick Reference)

| Command | Purpose |
|---------|---------|
| `west build -p auto -b <board> <app>` | Build application (auto-reconfigure) |
| `west build -p always -b <board> <app>` | Clean build (pristine) |
| `west build -t menuconfig` | Interactive configuration |
| `west flash` | Flash to target board |
| `west debug` | Launch debugger |
| `west update` | Update all west projects |
| `west boards` | List supported boards |

**See**: [reference/west-commands.md](reference/west-commands.md) for complete command reference.

## Key Build Files (Quick Reference)

| File | Purpose | Location |
|------|---------|----------|
| **CMakeLists.txt** | Build recipe | Application root, driver subsystem |
| **Kconfig** | Configuration options | Driver subsystem |
| **prj.conf** | Application config | Application root |
| **boards/*.overlay** | Board-specific DT | Application `boards/` directory |

## Common Build Patterns (Quick Reference)

### Application CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_app)

target_sources(app PRIVATE src/main.c)
```

### Driver Kconfig

```kconfig
config I2C_MYDEVICE
    bool "My I2C Controller"
    default y
    depends on DT_HAS_VENDOR_MYDEVICE_ENABLED
    select I2C
    help
      Enable I2C controller driver for MyDevice.
```

### prj.conf

```ini
# Minimal configuration
CONFIG_SERIAL=y
CONFIG_UART_CONSOLE=y

# Enable specific driver
CONFIG_I2C=y
CONFIG_I2C_MYDEVICE=y
```

### Board Overlay

```dts
&i2c0 {
    status = "okay";
    my_sensor: sensor@48 {
        compatible = "vendor,sensor";
        reg = <0x48>;
    };
};
```

**See**: [reference/cmake-patterns.md](reference/cmake-patterns.md) and [reference/kconfig-integration.md](reference/kconfig-integration.md) for detailed patterns.

## Quick Start Workflow

1. **Activate virtual environment**: `source .venv/Scripts/activate`
2. **Build application**: `west build -p auto -b <board> <app-path>`
3. **Flash to target**: `west flash`
4. **View console output**: Connect serial terminal (115200 baud)

**For troubleshooting**: Read [reference/troubleshooting.md](reference/troubleshooting.md)

## Sample Application Structure

```
my_sample/
├── CMakeLists.txt          # Build recipe
├── prj.conf                # Configuration
├── sample.yaml             # Test metadata
├── src/
│   └── main.c              # Application code
├── boards/
│   └── <board>.overlay     # Board-specific DT (optional)
└── README.rst              # Documentation
```

## Common Build Errors (Summary)

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `west: command not found` | .venv not activated | Activate .venv |
| `CMake Error: Could not find CMAKE_MAKE_PROGRAM` | Toolchain not in PATH | Check Zephyr SDK setup |
| `No board named 'X' found` | Invalid board name | Use `west boards` to list |
| `compatible not found` | Missing devicetree binding | Create `.yaml` binding |
| `undefined reference to symbol` | Missing Kconfig dependency | Add `select` in Kconfig |
| `CONFIG option not recognized` | Typo or non-existent option | Check Kconfig files |

**See**: [reference/troubleshooting.md](reference/troubleshooting.md) for detailed debugging steps.

## Best Practices (Summary)

✅ **DO**:
- Always use virtual environment (.venv)
- Use `-p auto` for most builds (auto-reconfigure)
- Use `-p always` for major changes (clean build)
- Check dependencies in Kconfig (`select`, `depends on`)
- Set correct init priorities (APPLICATION, POST_KERNEL, etc.)
- Keep source files sorted alphabetically in CMakeLists.txt
- Use logging (`LOG_MODULE_REGISTER`) for debugging

❌ **DON'T**:
- Don't skip .venv activation
- Don't ignore Kconfig dependencies
- Don't hardcode board-specific values in drivers
- Don't forget to add source files to CMakeLists.txt

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns.

## Integration with driver-coder-zephyr

The driver-coder-zephyr agent uses this skill's patterns:

1. **Phase 1 - Setup**: Activate .venv, create CMakeLists.txt and Kconfig
2. **Phase 2 - Build Files**: Generate subsystem CMakeLists.txt and Kconfig entries
3. **Phase 3 - Build Verification**: Run `west build`, check for errors
4. **Phase 4 - Troubleshooting**: Fix build errors using troubleshooting patterns

## References

**Zephyr Documentation**:
- **Build System**: https://docs.zephyrproject.org/latest/build/
- **West Tool**: https://docs.zephyrproject.org/latest/develop/west/
- **Kconfig**: https://docs.zephyrproject.org/latest/build/kconfig/
- **CMake**: https://docs.zephyrproject.org/latest/build/cmake/

**Reference Guides**:
- [reference/west-commands.md](reference/west-commands.md) – Complete west command reference
- [reference/cmake-patterns.md](reference/cmake-patterns.md) – CMakeLists.txt patterns
- [reference/kconfig-integration.md](reference/kconfig-integration.md) – Kconfig patterns and dependencies
- [reference/app-config-overlays.md](reference/app-config-overlays.md) – prj.conf and overlay patterns
- [reference/troubleshooting.md](reference/troubleshooting.md) – 8 common build errors with solutions
- [reference/best-practices.md](reference/best-practices.md) – 7 build system best practices

## Summary Checklist

### Environment Setup
- [ ] Python virtual environment (.venv) created
- [ ] .venv activated before running west commands
- [ ] West installed in .venv
- [ ] West workspace initialized (`west init`)
- [ ] All projects updated (`west update`)

### Application Build
- [ ] CMakeLists.txt created
- [ ] prj.conf configured
- [ ] Board specified in build command
- [ ] Build succeeds (`west build`)
- [ ] Flashing works (`west flash`)

### Driver Integration
- [ ] Driver source added to subsystem CMakeLists.txt
- [ ] Kconfig entry created with correct dependencies
- [ ] Devicetree binding created (if new compatible)
- [ ] Board overlay provided (if needed for testing)
- [ ] Build succeeds with driver enabled
