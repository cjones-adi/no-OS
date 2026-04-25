---
name: zephyr-fuel-gauge
description: 'Complete guide to Zephyr fuel gauge drivers for battery capacity monitoring. Use when implementing fuel gauge drivers for Li-ion/Li-Po batteries, reading state of charge (SoC), voltage, current, temperature, capacity, cycle count, or implementing battery management features.'
---

# Zephyr Fuel Gauge Driver Development

This skill provides comprehensive understanding of the Zephyr fuel gauge driver subsystem for battery capacity monitoring.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement fuel gauge driver", "step by step", "get_property", "set_property"
- Questions about: driver API, register access, property handlers, battery properties
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-7) with complete code

**Triggers to read reference/api-usage.md**:
- User asks: "how to use fuel gauge", "read SoC", "battery voltage", "charging status"
- Questions about: reading properties, unit conversion, battery monitoring
- Need: application-side fuel gauge usage examples (5 patterns)

**Triggers to read reference/debugging.md**:
- User says: "fuel gauge not working", "wrong SoC", "debugging", "battery issue"
- Build/runtime errors with fuel gauge
- Questions about: device ID, I2C communication, calibration, property errors
- Need: debugging steps (5 detailed tips)

---

## When to Use This Skill

Use this skill when you need to:
- Implement fuel gauge drivers for Zephyr
- Read battery state of charge (SoC), voltage, current, temperature
- Monitor battery capacity, cycle count, time-to-empty/full
- Implement battery protection features
- Handle fuel gauge events and interrupts
- Support multiple battery chemistries
- Debug fuel gauge communication or reporting issues

## What is a Fuel Gauge?

**Fuel gauges** measure and report battery state information including remaining capacity, voltage, current, temperature, and health.

### Key Metrics

- **State of Charge (SoC)**: Remaining capacity as percentage (0-100%)
- **Voltage**: Current battery voltage (mV)
- **Current**: Charging or discharging current (mA, ±)
- **Temperature**: Battery temperature (°C × 10)
- **Capacity**: Full charge capacity and remaining capacity (mAh or mWh)
- **Cycle Count**: Number of charge/discharge cycles
- **Time-to-Empty/Full**: Estimated time until empty or fully charged

## File Structure (Quick Reference)

- **Driver**: `drivers/fuel_gauge/fuel_gauge_<chip>.c`
- **Binding**: `dts/bindings/fuel_gauge/<vendor>,<chip>.yaml`
- **Kconfig**: Update `drivers/fuel_gauge/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **fuel_gauge_driver_api** | Driver API table | `get_property()`, `set_property()`, `get_buffer_property()` |

**Properties**: VOLTAGE, CURRENT, AVG_CURRENT, STATE_OF_CHARGE, FULL_CHARGE_CAPACITY, REMAINING_CAPACITY, RUNTIME_TO_EMPTY, RUNTIME_TO_FULL, TEMP, CYCLE_COUNT, CHARGE_VOLTAGE, CHARGE_CURRENT, STATUS, etc.

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Key Patterns

### Read Battery State of Charge

```c
union fuel_gauge_prop_val val;
fuel_gauge_get_property(fg_dev, FUEL_GAUGE_PROP_STATE_OF_CHARGE, &val);
printk("Battery SoC: %d%%\n", val.fg_status.state_of_charge);
```

### Read Battery Voltage and Current

```c
fuel_gauge_get_property(fg_dev, FUEL_GAUGE_PROP_VOLTAGE, &val);
printk("Voltage: %d mV\n", val.voltage);

fuel_gauge_get_property(fg_dev, FUEL_GAUGE_PROP_CURRENT, &val);
printk("Current: %d mA\n", val.current);
```

### Monitor Battery Status

```c
fuel_gauge_get_property(fg_dev, FUEL_GAUGE_PROP_STATUS, &val);
if (val.fg_status.flags & FUEL_GAUGE_STATUS_FLAGS_CHARGING) {
    printk("Battery charging\n");
}
if (val.fg_status.flags & FUEL_GAUGE_STATUS_FLAGS_DISCHARGING) {
    printk("Battery discharging\n");
}
```

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Config and Data Structures**
3. **Implement get_property Function** – Read battery properties
4. **Implement set_property Function** (Optional) – Configure parameters
5. **Implement get_buffer_property** (Optional) – Read buffer data
6. **Define API Structure** and **Init Function**
7. **Device Instantiation Macro**

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always check device ready state before use
- Handle all relevant properties for the fuel gauge
- Return -ENOTSUP for unsupported properties
- Use correct units (mV, mA, mAh, °C × 10)
- Validate property ranges
- Support battery status flags
- Document supported properties in binding

❌ **DON'T**:
- Don't assume all properties are supported
- Don't ignore calibration requirements
- Don't forget to convert units correctly
- Don't skip battery chemistry configuration

**See**: [reference/api-usage.md](reference/api-usage.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **Fuel Gauge API**: `zephyr/include/zephyr/drivers/fuel_gauge.h`
- **Fuel Gauge Drivers**: `zephyr/drivers/fuel_gauge/`
- **Bindings**: `zephyr/dts/bindings/fuel_gauge/`

**Example Drivers**:
- **MAX17048**: `drivers/fuel_gauge/max17048.c`
- **SBS Gauge**: `drivers/fuel_gauge/sbs_gauge.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-7)
- [reference/api-usage.md](reference/api-usage.md) – Application usage (5 patterns)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (5 tips)

## Summary Checklist

### Driver Implementation
- [ ] Register map defined
- [ ] Config structure with I2C/battery specs
- [ ] Data structure with runtime state
- [ ] `get_property()` implemented
- [ ] `set_property()` implemented (if supported)
- [ ] API structure defined
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created
- [ ] Battery properties defined
- [ ] Kconfig entry with dependencies
- [ ] Board DTS defines fuel gauge

### Testing
- [ ] SoC reading works
- [ ] Voltage/current readings work
- [ ] Temperature reading works (if supported)
- [ ] Capacity readings work
- [ ] Status flags work correctly
