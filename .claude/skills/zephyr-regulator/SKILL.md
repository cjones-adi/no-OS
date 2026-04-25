---
name: zephyr-regulator
description: 'Complete guide to Zephyr regulator (voltage/current) drivers for PMICs and power management ICs. Use when implementing regulator drivers for buck converters, LDOs, boost converters, charge pumps, implementing voltage/current control, DVS (Dynamic Voltage Scaling), operating modes, active discharge, devicetree bindings, or debugging power management issues.'
---

# Zephyr Regulator Driver Development

This skill provides comprehensive understanding of the Zephyr regulator driver subsystem for power management integrated circuits (PMICs) and voltage/current regulators.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement regulator driver", "step by step", "enable/disable", "set voltage"
- Questions about: driver API, linear ranges, descriptors, init function
- User mentions: implementing driver functions, register access, reference counting
- Need: detailed implementation steps (Steps 1-8) with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "regulator", "DTS", "overlay"
- Questions about: regulator bindings, properties, always-on, boot-on
- User asks: "how to define regulator binding", "overlay example", "board overlay"
- Need: binding patterns and complete overlay examples

**Triggers to read reference/advanced-features.md**:
- User mentions: "DVS", "dynamic voltage scaling", "active discharge", "error flags"
- Questions about: voltage switching, OV/OC/OT protection, MFD integration
- Need: advanced regulator features and patterns

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "common patterns", "linear range", "validation"
- Questions about: common structures, descriptor usage, read-modify-write
- Need: design patterns (7 detailed patterns)

**Triggers to read reference/api-usage.md**:
- User asks: "how to use regulator", "consumer example", "enable regulator"
- Questions about: reference-counted enable, set voltage, set current, modes
- Need: consumer-side regulator usage

**Triggers to read reference/debugging.md**:
- User says: "not working", "wrong voltage", "debugging", "regulator issue"
- Build/runtime errors
- Questions about: devicetree check, register access, reference counting
- Need: debugging steps (6 detailed tips)

**Triggers to read reference/example-driver.md**:
- User asks: "complete example", "buck converter example", "simple driver"
- Need: full working driver code to study

**Triggers to read reference/sample-app.md**:
- User asks: "sample application", "how to test", "example usage"
- Questions about: CMakeLists, prj.conf, main.c structure
- Need: complete sample application with all files

---

## When to Use This Skill

Use this skill when you need to:
- Implement regulator drivers for PMICs (Power Management ICs)
- Add support for buck converters, LDOs, boost converters, or charge pumps
- Control voltage and current output dynamically
- Implement DVS (Dynamic Voltage Scaling) support
- Configure operating modes (PWM, PFM, auto, low-power)
- Handle active discharge functionality
- Create devicetree bindings for new regulators
- Implement parent-child regulator relationships
- Debug voltage/current control issues
- Add error detection (over-voltage, over-current, over-temperature)
- Work with reference-counted enable/disable
- Support always-on or boot-on regulators

## What is a Regulator?

**A regulator** is a hardware component that maintains a constant voltage or current output despite variations in input voltage or load conditions:

- **Voltage regulation**: Buck, boost, LDO (Low Dropout) converters
- **Current regulation**: Current limiting and current sources
- **Dynamic control**: Runtime voltage/current adjustment
- **Multiple modes**: Optimized for different power/efficiency trade-offs
- **Safety**: Over-voltage, over-current, thermal protection

### Common Regulator Types

- **Buck Converter (Step-Down)**: High input voltage → Lower output voltage, high efficiency
- **Boost Converter (Step-Up)**: Low input voltage → Higher output voltage
- **LDO (Low Dropout)**: Linear regulation, simple, lower efficiency but low noise
- **Charge Pump**: Voltage multiplication/inversion using capacitors
- **Load Switch**: Simple on/off control with minimal regulation

### Benefits

- **Power efficiency** – Optimize power consumption for different load conditions
- **Voltage scaling** – Adjust voltage dynamically based on performance needs
- **Reference counted** – Multiple consumers can share same regulator safely
- **Safety** – Built-in protection against dangerous conditions
- **Devicetree integration** – Hardware description and constraints

## Architecture Overview

```
┌────────────────────────────────────────────────────┐
│         Application / Peripheral Drivers           │
│      (Consumers using regulator_enable(), etc.)    │
└────────────────────┬───────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │  regulator.h API          │  Reference-counted enable/disable
        │  (Generic Interface)      │  Voltage/current control
        └────────────┬──────────────┘  Mode management
                     │
    ┌────────────────┴────────────────────────┐
    │                                         │
┌───▼─────────────────────┐     ┌────────────▼──────────────┐
│ regulator_max20370.c    │     │  regulator_pca9420.c      │
│ (Buck/LDO/Boost/CP)     │     │  (Buck/LDO with DVS)      │
└───┬─────────────────────┘     └────────┬──────────────────┘
    │                                     │
┌───▼─────────────────────┐     ┌────────▼──────────────────┐
│ MFD or I2C Driver       │     │  I2C Driver               │
│ (max20370_converters)   │     │  (Direct register access) │
└─────────────────────────┘     └───────────────────────────┘
```

### Parent-Child Relationship

For complex PMICs with multiple regulators:

```
┌─────────────────────────────────────────────────┐
│         PMIC Parent Device                      │
│   (ship mode, DVS state control)                │
└─────────┬─────────┬──────────┬──────────────────┘
          │         │          │
    ┌─────▼────┐  ┌─▼──────┐ ┌─▼──────┐
    │  BUCK1   │  │ BUCK2  │ │  LDO1  │  (Child Regulators)
    └──────────┘  └────────┘ └────────┘
```

## File Structure (Quick Reference)

- **Driver**: `drivers/regulator/regulator_<chip>.c`
- **Binding**: `dts/bindings/regulator/<vendor>,<chip>.yaml`
- **Public Header** (optional): `include/zephyr/drivers/regulator/<chip>.h`
- **DT Include** (optional): `include/zephyr/dt-bindings/regulator/<chip>.h`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **regulator_common_config** | Common configuration | `min_uv`, `max_uv`, `init_uv`, `min_ua`, `max_ua`, `always_on`, `boot_on` |
| **regulator_common_data** | Common runtime data | `refcount` (reference counting for enable/disable) |
| **regulator_driver_api** | Driver API table | `enable()`, `disable()`, `set_voltage()`, `get_voltage()`, `set_current_limit()`, `set_mode()` |
| **linear_range** | Voltage/current mapping | `min_val`, `min_sel`, `max_sel`, `step` (for calculating register values) |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Linear Ranges** for voltage/current mappings
3. **Define Regulator Descriptors** (one per regulator output)
4. **Define Config and Data Structures** with common structures
5. **Implement API Functions** (enable, disable, set_voltage, get_voltage, set_mode, etc.)
6. **Define API Structure** with function pointers
7. **Implement Init Function** – Initialize hardware, validate state
8. **Device Instantiation Macro** – Register driver with common structures

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### Linear Range for Voltage Mapping

```c
static const struct linear_range buck_range = {
    .min_val = 600000,   // 0.6V minimum
    .min_sel = 0,
    .max_sel = 127,
    .step = 12500        // 12.5mV step
};
// Register value 0 = 0.6V, value 127 = 2.1875V
```

### Common Structures

```c
struct my_regulator_config {
    struct regulator_common_config common;  // MUST be first
    struct i2c_dt_spec i2c;
    const struct linear_range *ranges;
    uint8_t enable_reg;
    uint8_t vsel_reg;
};

struct my_regulator_data {
    struct regulator_common_data common;  // MUST be first
};
```

### API Implementation

```c
static int my_regulator_enable(const struct device *dev)
{
    const struct my_regulator_config *config = dev->config;
    struct my_regulator_data *data = dev->data;
    
    // Reference counting handled by common layer
    if (data->common.refcount > 0) {
        data->common.refcount++;
        return 0;
    }
    
    // Enable regulator hardware
    int ret = i2c_reg_update_byte_dt(&config->i2c, config->enable_reg,
                                      ENABLE_BIT, ENABLE_BIT);
    if (ret == 0) {
        data->common.refcount = 1;
    }
    return ret;
}
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always start with `regulator_common_config` and `regulator_common_data` (MUST be first member)
- Use `linear_range` for voltage/current calculations
- Validate hardware state in init function
- Return `-ENOTSUP` for unsupported features (don't implement stub functions)
- Use descriptors for PMICs with multiple regulators
- Handle read-modify-write carefully (use proper locking)
- Support devicetree properties: `regulator-always-on`, `regulator-boot-on`

❌ **DON'T**:
- Don't implement optional API functions you don't support
- Don't forget reference counting in enable/disable
- Don't assume voltage is already correct in init
- Don't use hardcoded voltage values (use linear_range)
- Don't modify registers without read-modify-write for shared registers

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## Consumer API Usage (Quick Reference)

```c
// Get regulator from devicetree
const struct device *reg = DEVICE_DT_GET(DT_NODELABEL(buck1));

// Enable (reference counted)
regulator_enable(reg);

// Set voltage
regulator_set_voltage(reg, 1800000, 1800000);  // 1.8V

// Set current limit
regulator_set_current_limit(reg, 0, 500000);  // 500mA max

// Set mode
regulator_set_mode(reg, REGULATOR_MODE_PWM);

// Disable (reference counted)
regulator_disable(reg);
```

**See**: [reference/api-usage.md](reference/api-usage.md) for complete consumer examples.

## References

**Zephyr Documentation**:
- **Regulator API**: `zephyr/include/zephyr/drivers/regulator.h`
- **Regulator Drivers**: `zephyr/drivers/regulator/`
- **Bindings**: `zephyr/dts/bindings/regulator/`

**Example Drivers**:
- **MAX20370** (Buck/LDO/Boost/CP): `drivers/regulator/regulator_max20370.c`
- **PCA9420** (Buck/LDO with DVS): `drivers/regulator/regulator_pca9420.c`
- **NPM1300** (PMIC with multiple regulators): `drivers/regulator/regulator_npm1300.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-8)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Binding patterns and overlay examples
- [reference/advanced-features.md](reference/advanced-features.md) – DVS, active discharge, error flags, MFD
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (7 detailed)
- [reference/api-usage.md](reference/api-usage.md) – Consumer API usage
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (6 tips)
- [reference/example-driver.md](reference/example-driver.md) – Complete buck converter driver
- [reference/sample-app.md](reference/sample-app.md) – Sample application with all files

## Summary Checklist

### Driver Implementation
- [ ] Register map defined with bit masks
- [ ] Linear ranges defined for voltage/current
- [ ] Regulator descriptors defined (one per output)
- [ ] Config structure with `regulator_common_config` first
- [ ] Data structure with `regulator_common_data` first
- [ ] `enable()` implemented with reference counting
- [ ] `disable()` implemented with reference counting
- [ ] `set_voltage()` implemented with linear_range
- [ ] `get_voltage()` implemented
- [ ] `set_current_limit()` implemented (if supported)
- [ ] `set_mode()` / `get_mode()` implemented (if supported)
- [ ] API structure defined with function pointers
- [ ] Init function validates hardware state
- [ ] Device instantiation macro

### Devicetree
- [ ] Binding created (include regulator.yaml)
- [ ] Properties defined (min/max voltage/current)
- [ ] Mode definitions (if applicable)
- [ ] Board overlay for testing

### Testing
- [ ] Enable/disable works (reference counting)
- [ ] Voltage set/get works
- [ ] Current limit works (if supported)
- [ ] Mode switching works (if supported)
- [ ] Always-on regulators stay enabled
- [ ] Boot-on regulators enabled at init
- [ ] Multiple consumers work (reference counting)
