---
name: zephyr-charger
description: 'Complete guide to Zephyr battery charger drivers for charging Li-ion/Li-Po batteries. Use when implementing charger drivers, configuring charge current and voltage, monitoring charging status and health, implementing charge algorithms, working with PMICs, detecting external power, or debugging charging issues.'
---

# Zephyr Battery Charger Driver Development

This skill provides comprehensive understanding of the Zephyr battery charger driver subsystem for charging Li-ion/Li-Po batteries.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement charger driver", "step by step", "get_property", "set_property", "charge_enable"
- Questions about: driver API, register access, property handlers, charge current/voltage
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-7) with complete code

**Triggers to read reference/api-usage.md**:
- User asks: "how to use charger", "enable charging", "set charge current", "charge status"
- Questions about: enabling/disabling charging, monitoring charge state, safety limits
- Need: application-side charger usage examples (5 patterns)

**Triggers to read reference/debugging.md**:
- User says: "charger not working", "not charging", "debugging", "safety timeout"
- Build/runtime errors with charger
- Questions about: external power detection, charge status, safety limits
- Need: debugging steps (5 detailed tips)

---

## When to Use This Skill

Use this skill when you need to:
- Implement battery charger drivers for Zephyr
- Configure charge current and voltage limits
- Monitor charging status (precharge, fast charge, trickle, complete)
- Detect external power and charger presence
- Implement safety features (over-current, over-voltage, thermal protection)
- Support different charge algorithms (CC-CV, JEITA compliance)
- Handle charge enable/disable control
- Debug charging issues

## What is a Battery Charger?

**Battery chargers** control the charging process for rechargeable batteries, implementing charge algorithms and safety features.

### Key Charge Phases

- **Trickle/Precharge**: Low current charging for deeply discharged batteries
- **Constant Current (CC)**: Fast charging at constant current
- **Constant Voltage (CV)**: Final charging at constant voltage as current tapers
- **Termination**: Charging complete when current drops below threshold

### Key Properties

- **Charge Current**: Fast charge current limit (mA)
- **Charge Voltage**: Target charge voltage (mV)
- **Precharge Current**: Low current for deeply discharged cells (mA)
- **External Power**: Presence of charging source
- **Status**: Current charge state (discharging, charging, not charging, complete)
- **Health**: Battery health status

## File Structure (Quick Reference)

- **Driver**: `drivers/charger/charger_<chip>.c`
- **Binding**: `dts/bindings/charger/<vendor>,<chip>.yaml`
- **Kconfig**: Update `drivers/charger/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **charger_driver_api** | Driver API table | `get_property()`, `set_property()`, `charge_enable()` |

**Properties**: STATUS, ONLINE, PRESENT, HEALTH, CONSTANT_CHARGE_CURRENT_UA, CONSTANT_CHARGE_VOLTAGE_UV, PRECHARGE_CURRENT_UA, CHARGE_TERM_CURRENT_UA, etc.

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Key Patterns

### Enable/Disable Charging

```c
charger_charge_enable(charger_dev, true);   // Enable charging
charger_charge_enable(charger_dev, false);  // Disable charging
```

### Set Charge Current and Voltage

```c
union charger_propval val;

// Set fast charge current to 500mA
val.const_charge_current_ua = 500000;
charger_set_property(charger_dev, CHARGER_PROPERTY_CONSTANT_CHARGE_CURRENT_UA, &val);

// Set charge voltage to 4.2V
val.const_charge_voltage_uv = 4200000;
charger_set_property(charger_dev, CHARGER_PROPERTY_CONSTANT_CHARGE_VOLTAGE_UV, &val);
```

### Monitor Charging Status

```c
union charger_propval val;

// Check if external power is present
charger_get_property(charger_dev, CHARGER_PROPERTY_ONLINE, &val);
if (val.online) {
    printk("External power connected\n");
}

// Get charging status
charger_get_property(charger_dev, CHARGER_PROPERTY_STATUS, &val);
switch (val.status) {
case CHARGER_STATUS_CHARGING:
    printk("Charging\n");
    break;
case CHARGER_STATUS_FULL:
    printk("Charge complete\n");
    break;
}
```

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Config and Data Structures**
3. **Implement get_property Function** – Read charger properties
4. **Implement set_property Function** – Configure charge parameters
5. **Implement charge_enable Function** – Enable/disable charging
6. **Define API Structure** and **Init Function**
7. **Device Instantiation Macro**

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always check device ready state before use
- Handle all relevant properties for the charger
- Return -ENOTSUP for unsupported properties
- Use correct units (uA for current, uV for voltage)
- Validate charge current/voltage limits
- Implement safety features (over-current, over-voltage, thermal)
- Support charge status reporting
- Document supported properties in binding

❌ **DON'T**:
- Don't assume all properties are supported
- Don't exceed battery charge limits
- Don't ignore safety features
- Don't skip external power detection

**See**: [reference/api-usage.md](reference/api-usage.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **Charger API**: `zephyr/include/zephyr/drivers/charger.h`
- **Charger Drivers**: `zephyr/drivers/charger/`
- **Bindings**: `zephyr/dts/bindings/charger/`

**Example Drivers**:
- **BQ24190**: `drivers/charger/bq24190.c`
- **MAX20335**: `drivers/charger/max20335_charger.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-7)
- [reference/api-usage.md](reference/api-usage.md) – Application usage (5 patterns)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (5 tips)

## Summary Checklist

### Driver Implementation
- [ ] Register map defined
- [ ] Config structure with I2C/charge specs
- [ ] Data structure with runtime state
- [ ] `get_property()` implemented
- [ ] `set_property()` implemented
- [ ] `charge_enable()` implemented
- [ ] API structure defined
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created
- [ ] Charge properties defined
- [ ] Kconfig entry with dependencies
- [ ] Board DTS defines charger

### Testing
- [ ] Charge enable/disable works
- [ ] Charge current/voltage setting works
- [ ] Status reporting works
- [ ] External power detection works
- [ ] Safety features work
