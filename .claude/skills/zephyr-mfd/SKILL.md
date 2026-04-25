---
name: zephyr-mfd
description: 'Complete guide to Zephyr MFD (Multi-Function Device) drivers for complex chips with multiple subsystems. Use when implementing parent drivers for chips with DAC+ADC+GPIO, PMIC with regulators, or any multi-function hardware sharing a communication bus.'
---

# Zephyr MFD (Multi-Function Device) Driver Development

This skill provides comprehensive understanding of the Zephyr MFD driver architecture for multi-function devices.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "how to implement", "step by step", "create MFD driver", "parent driver", "child driver"
- Questions about: transfer functions, parent init, child driver pattern, bus abstraction
- User mentions: "AD559x example", "MAX22017 example", implementing register access
- Need: detailed implementation steps with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "DTS", "overlay", "YAML"
- Questions about: parent-child DT structure, compatible strings, child nodes
- User asks: "how to define binding", "devicetree example"
- Need: complete binding examples and devicetree usage

**Triggers to read reference/api-usage.md**:
- User asks: "how to use", "example usage", "consumer application", "application layer"
- Questions about: using DAC/ADC/GPIO child devices in applications
- Need: consumer-side code examples

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "common patterns", "thread safety", "init order"
- Questions about: bus abstraction, register access patterns, multi-bus support
- Need: design patterns and recommendations

**Triggers to read reference/advanced-features.md**:
- User mentions: "interrupt", "CRC", "power management", "checksum", "PM"
- Questions about: IRQ handling, error detection, power modes
- Need: advanced integration patterns

**Triggers to read reference/debugging.md**:
- Build/link errors, runtime issues
- User says: "not working", "error", "debugging", "troubleshoot", "child can't see parent"
- Questions about: init order, devicetree issues, transfer function problems
- Need: troubleshooting steps and common issues

**Triggers to read reference/complete-example.md**:
- User asks: "complete example", "real driver", "AD559x", "full implementation"
- Need: reference implementation to study
- Want: overview of a working driver

---

## When to Use This Skill

Use this skill when you need to:
- Implement MFD parent drivers for complex multi-function chips
- Create child drivers that use MFD parent infrastructure
- Integrate DAC, ADC, GPIO, regulator, or other subsystems under a single MFD parent
- Work with devices like AD559x (DAC+ADC+GPIO), MAX22017 (DAC+GPIO), PMICs, I/O expanders
- Understand parent-child driver architecture in Zephyr
- Abstract I2C/SPI communication for multiple child subsystems
- Debug MFD parent-child communication issues

## What is MFD?

**MFD (Multi-Function Device)** is an architecture pattern for complex chips that provide multiple independent functions (subsystems) sharing a common communication bus:

- **Parent Driver** – Manages hardware initialization, bus communication, and provides register access API
- **Child Drivers** – Implement specific subsystem functionality (DAC, ADC, GPIO) using parent's API
- **Bus Abstraction** – Parent handles I2C/SPI details, children only call parent functions
- **Code Reuse** – Multiple subsystems share bus initialization and register access logic

### Common MFD Device Types

- **Configurable I/O** (AD559x) – DAC + ADC + GPIO pins configurable per application
- **Analog Output/Input** (MAX22017) – Dual DAC + dual ADC + GPIO for industrial control
- **PMICs** – Power management ICs with regulators, chargers, fuel gauges
- **I/O Expanders** (ADP5585) – GPIO + keypad + PWM controllers
- **RTC + Alarms** – Real-time clocks with multiple alarm/timer functions

### Benefits

- **Shared Infrastructure** – One parent driver handles bus communication for all child functions
- **Modular** – Enable/disable child subsystems independently via Kconfig and devicetree
- **Maintainability** – Register access logic lives in one place (parent), not duplicated
- **Extensibility** – Easy to add new child subsystem without modifying parent

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Application Layer                      │
│  (Uses sensor API, DAC API, GPIO API, etc.)        │
└─────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬──────────────┐
        │                       │              │
        ▼                       ▼              ▼
┌───────────────┐      ┌───────────────┐   ┌──────────────┐
│   DAC Child   │      │   ADC Child   │   │ GPIO Child   │
│   Driver      │      │   Driver      │   │  Driver      │
├───────────────┤      ├───────────────┤   ├──────────────┤
│ dac_driver_api│      │adc_driver_api │   │gpio_driver_  │
│               │      │               │   │  api         │
└───────────────┘      └───────────────┘   └──────────────┘
        │                       │              │
        │  Call Parent APIs:    │              │
        │  - mfd_xxx_read_reg() │              │
        │  - mfd_xxx_write_reg()│              │
        │  - mfd_xxx_read_dac_chan()           │
        │  - mfd_xxx_write_dac_chan()          │
        │                       │              │
        └───────────────────────┴──────────────┘
                    │
                    ▼
        ┌────────────────────────────┐
        │   MFD Parent Driver        │
        ├────────────────────────────┤
        │ - Bus abstraction          │
        │ - Register access API      │
        │ - Hardware initialization  │
        │ - Reset logic              │
        │ - Interrupt handling       │
        └────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   ┌─────────┐            ┌─────────┐
   │   I2C   │            │   SPI   │
   │  Bus    │            │   Bus   │
   └─────────┘            └─────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
        ┌────────────────────────────┐
        │  Hardware Chip             │
        │  (AD559x, MAX22017, etc.)  │
        └────────────────────────────┘
```

### Parent-Child Relationship

```
devicetree:
    mfd_parent: chip@addr {
        compatible = "adi,ad559x";  // Parent driver
        reg = <0xaddr>;
        reset-gpios = <&gpio0 1 0>;

        child_dac: dac-controller {
            compatible = "adi,ad559x-dac";  // Child driver
            #io-channel-cells = <1>;
        };

        child_adc: adc-controller {
            compatible = "adi,ad559x-adc";  // Child driver
            #io-channel-cells = <1>;
        };

        child_gpio: gpio-controller {
            compatible = "adi,ad559x-gpio";  // Child driver
            gpio-controller;
            #gpio-cells = <2>;
        };
    };

Child gets parent:  const struct device *parent = DEVICE_DT_GET(DT_INST_PARENT(inst));
Child calls parent: ret = mfd_ad559x_write_reg(parent, reg, val);
```

## File Structure

For a new MFD driver, you typically need:

### 1. Parent Driver Implementation: `drivers/mfd/mfd_<chip>.c`

**Key components:**
- Register map and bit definitions (private)
- Transfer function structure (bus abstraction)
- Config and data structures
- Bus initialization function pointers
- Device initialization (reset, startup)
- Device instantiation macro

### 2. Bus-Specific Implementations (if supporting multiple buses)

**For I2C variant**: `drivers/mfd/mfd_<chip>_i2c.c`
- I2C read/write/read_reg/write_reg implementations
- I2C-specific transfer function structure
- I2C bus init function

**For SPI variant**: `drivers/mfd/mfd_<chip>_spi.c`
- SPI read/write/read_reg/write_reg implementations
- SPI-specific transfer function structure
- SPI bus init function

### 3. Public Header: `include/zephyr/drivers/mfd/<chip>.h`

**Defines:**
- Register addresses (for children to use)
- Bit field definitions
- Public API functions (register access)
- Child-specific helper functions

### 4. Private Header (Optional): `drivers/mfd/mfd_<chip>.h`

**For:**
- Shared structures between parent and bus-specific implementations
- Private register definitions
- Transfer function interface definition

### 5. Devicetree Bindings

**Parent binding**: `dts/bindings/mfd/<vendor>,<chip>.yaml` or `<vendor>,<chip>-i2c.yaml`, `<vendor>,<chip>-spi.yaml`
- I2C/SPI bus properties
- Reset GPIO
- Interrupt GPIO
- Bus-specific properties

**Common binding** (if multi-bus): `dts/bindings/mfd/<vendor>,<chip>-common.yaml`
- Shared properties between I2C and SPI variants

**Child bindings** (separate files):
- `dts/bindings/dac/<vendor>,<chip>-dac.yaml`
- `dts/bindings/adc/<vendor>,<chip>-adc.yaml`
- `dts/bindings/gpio/<vendor>,<chip>-gpio.yaml`

### 6. Kconfig: `drivers/mfd/Kconfig.<chip>`

Enable parent driver and dependencies:
```kconfig
config MFD_AD559X
  bool "AD559X Multi-Function Device driver"
  default y
  depends on DT_HAS_ADI_AD559X_ENABLED
  select I2C if $(dt_compat_on_bus,$(DT_COMPAT_ADI_AD559X),i2c)
  select SPI if $(dt_compat_on_bus,$(DT_COMPAT_ADI_AD559X),spi)
  help
    Enable driver for AD559X multi-function device.
```

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **Transfer Function** | Bus abstraction | `read_raw()`, `write_raw()`, `read_reg()`, `write_reg()` |
| **Config (Parent)** | Compile-time config | `i2c_dt_spec` or `spi_dt_spec`, `reset_gpio`, `bus_init()` |
| **Data (Parent)** | Runtime state | `transfer_function` pointer, optional `k_mutex lock` |
| **Config (Child)** | Child config | `const struct device *mfd_dev`, child-specific properties |
| **Data (Child)** | Child runtime state | Child-specific runtime data |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures with complete code examples.

## Quick Start Workflow

1. **Define Register Map** in public header (`include/zephyr/drivers/mfd/<chip>.h`)
2. **Implement Transfer Functions** for I2C and/or SPI
3. **Implement Parent Driver** with init and public API functions
4. **Create Devicetree Bindings** for parent and children
5. **Implement Child Drivers** that call parent APIs
6. **Configure Kconfig** for parent and children

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### Bus Abstraction via Transfer Functions

```c
struct mfd_xxx_transfer_function {
    int (*read_reg)(const struct device *dev, uint8_t reg, uint16_t *val);
    int (*write_reg)(const struct device *dev, uint8_t reg, uint16_t val);
};

// Parent provides generic API, forwards to bus-specific implementation
int mfd_xxx_read_reg(const struct device *dev, uint8_t reg, uint16_t *val)
{
    struct mfd_xxx_data *data = dev->data;
    return data->transfer_function->read_reg(dev, reg, val);
}
```

### Child Gets Parent Device

```c
// In child config macro
.mfd_dev = DEVICE_DT_GET(DT_INST_PARENT(inst))

// In child driver
const struct my_child_config *config = dev->config;
ret = mfd_parent_write_reg(config->mfd_dev, reg, val);
```

### Init Priority

```c
// Parent must initialize before children
DEVICE_DT_INST_DEFINE(inst, mfd_xxx_init, NULL,
                      &mfd_xxx_data_##inst,
                      &mfd_xxx_config_##inst,
                      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,  // 55
                      NULL);  // No driver API for MFD parent
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Use transfer function pointers for bus abstraction (I2C vs SPI)
- Define registers in public header (children need access)
- Initialize parent before children (CONFIG_MFD_INIT_PRIORITY)
- MFD parent has no driver API (NULL in DEVICE_DT_INST_DEFINE)
- Children check `device_is_ready()` on parent in init
- Use mutex in parent data structure if thread-safe access needed
- Separate bus-specific code into different files (_i2c.c, _spi.c)
- Provide child-specific helper functions in parent (optional but recommended)
- Use common binding for shared I2C/SPI properties

❌ **DON'T**:
- Don't duplicate bus access code in multiple child drivers
- Don't give MFD parent a driver API – it's infrastructure, not a controller
- Don't initialize children before parent (will fail device_is_ready checks)
- Don't access bus directly from child drivers (use parent APIs)
- Don't hardcode I2C or SPI – use transfer functions for multi-bus support

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with code examples.

## References

**Zephyr Documentation**:
- **MFD Drivers**: `zephyr/drivers/mfd/`
- **MFD Headers**: `zephyr/include/zephyr/drivers/mfd/`
- **Bindings**: `zephyr/dts/bindings/mfd/`

**Example Drivers**:
- **AD559x** (I2C + SPI): `drivers/mfd/mfd_ad559x*.c`, child drivers in `drivers/dac/dac_ad559x.c`, `drivers/gpio/gpio_ad559x.c`
- **MAX22017** (SPI only): `drivers/mfd/mfd_max22017.c`, `drivers/dac/dac_max22017.c`
- **ADP5585** (I2C): `drivers/mfd/mfd_adp5585.c`, `drivers/gpio/gpio_adp5585.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed step-by-step driver implementation
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Complete binding patterns and examples
- [reference/api-usage.md](reference/api-usage.md) – Consumer application examples
- [reference/best-practices.md](reference/best-practices.md) – Design patterns and recommendations
- [reference/advanced-features.md](reference/advanced-features.md) – Interrupts, CRC, power management
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide
- [reference/complete-example.md](reference/complete-example.md) – AD559x driver overview

## Summary Checklist

### Parent Driver
- [ ] Register map defined in public header
- [ ] Transfer function structure defined
- [ ] Config structure with bus specs (I2C/SPI), reset GPIO, bus_init()
- [ ] Data structure with transfer_function pointer (and optional mutex)
- [ ] Public API functions (read_reg, write_reg, child helpers)
- [ ] Init function (bus init, reset, startup)
- [ ] Device instantiation macro with NULL driver API
- [ ] Kconfig entry with bus dependencies
- [ ] Parent binding (YAML)

### Bus-Specific Implementations
- [ ] I2C transfer functions (_i2c.c)
- [ ] SPI transfer functions (_spi.c)
- [ ] Transfer function structure instances
- [ ] Bus init functions that set transfer_function pointer

### Child Drivers
- [ ] Child config with parent device pointer
- [ ] Child init checks parent ready
- [ ] Child APIs call parent functions
- [ ] Child binding (YAML) with parent reference
- [ ] Child Kconfig depends on parent

### Testing
- [ ] Parent initializes successfully
- [ ] Children can get parent device
- [ ] Register access works (I2C and/or SPI)
- [ ] Child subsystems function correctly
- [ ] Multi-bus support tested (if applicable)
