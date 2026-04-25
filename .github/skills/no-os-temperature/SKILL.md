---
name: no-os-temperature
description: Guide to no-OS temperature sensor drivers. Covers digital temperature sensors, RTD converters, thermocouple converters, multi-sensor hubs, and calibration. Provides quick reference with detailed implementation guides, usage examples, calibration procedures, best practices, and troubleshooting.
---

# no-OS Temperature Sensor Drivers

Quick-start guide for developing temperature sensor drivers in the no-OS framework. Covers digital sensors, RTDs, thermocouples, and multi-sensor hubs.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed documentation when needed:

**Triggers to read reference/implementation.md**:
- User asks: "how to implement", "driver structure", "device descriptor"
- Questions about: sensor types, architecture, core functionality, IIO integration
- Mentions: multi-sensor configuration, resolution settings, operating modes
- Need: complete implementation patterns, detailed API examples

**Triggers to read reference/api-usage.md**:
- User asks: "how to use", "example code", "usage", "how to read temperature"
- Questions about: specific sensor usage (ADT7420, MAX31865, MAX31855, LTC2983)
- Mentions: overheat protection, RTD measurement, thermocouple setup
- Need: complete working examples, use case patterns, power management

**Triggers to read reference/calibration.md**:
- User asks: "how to calibrate", "improve accuracy", "calibration procedure"
- Mentions: offset, gain, two-point calibration, reference temperature
- Questions about: accuracy budget, ice bath, boiling water, dry block calibrator
- Need: calibration methods, accuracy considerations, detailed procedures

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "recommendations", "what should I", "guidelines"
- Questions about: sensor selection, wire configuration, fault detection
- Mentions: resolution choice, noise filtering, cold junction compensation
- Need: decision matrix, configuration guidelines, testing strategies, common pitfalls

**Triggers to read reference/troubleshooting.md**:
- User says: "not working", "error", "invalid reading", "fault", "problem"
- Questions about: communication issues, invalid temperatures, conversion timeout
- Error symptoms: no device response, always zero, noisy readings, faults
- Need: diagnostic procedures, solutions, troubleshooting checklist

---

## When to Use This Skill

- Implementing temperature sensor drivers (digital, RTD, thermocouple)
- Configuring resolution, operating modes, and wire configurations
- Setting up temperature alerts and fault detection
- Calibrating temperature sensors for accuracy
- Multi-sensor hub configuration (LTC2983)
- Troubleshooting communication or accuracy issues

---

## Temperature Sensor Types Overview

| Type | Interface | Range | Accuracy | Use Case |
|------|-----------|-------|----------|----------|
| **Digital** (ADT7420, LM75) | I2C | -40 to +125C | 0.25C | Board monitoring |
| **RTD** (MAX31865) | SPI | -200 to +850C | 0.5C | Industrial, precision |
| **Thermocouple** (MAX31855) | SPI | -200 to +1800C | 2C | High temp, ovens |
| **Multi-Hub** (LTC2983) | SPI | Varies | Varies | Multiple points |

---

## Quick Reference

### Common Locations
- `drivers/temperature/adt7420/` - High-precision digital I2C sensor
- `drivers/temperature/max31865/` - RTD-to-digital converter (PT100/PT1000)
- `drivers/temperature/max31855/` - Thermocouple-to-digital converter
- `drivers/temperature/ltc2983/` - 20-channel multi-sensor hub

### Typical API

```c
// Digital sensors (I2C)
int adt7420_init(struct adt7420_dev **device, struct adt7420_init_param *init);
int adt7420_get_temperature(struct adt7420_dev *dev, float *temp);
int adt7420_set_resolution(struct adt7420_dev *dev, enum adt7420_resolution res);

// RTD converters (SPI)
int max31865_init(struct max31865_dev **device, struct max31865_init_param *init);
int max31865_read_temp(struct max31865_dev *dev, float *temp);
int max31865_set_wires(struct max31865_dev *dev, enum max31865_wire_mode mode);

// Thermocouple converters (SPI)
int max31855_init(struct max31855_dev **device, struct max31855_init_param *init);
int max31855_read_temp(struct max31855_dev *dev, float *temp);
int max31855_read_fault(struct max31855_dev *dev, uint8_t *fault);

// Multi-sensor hub (SPI)
int ltc2983_setup_sensor(struct ltc2983_dev *dev, uint8_t ch, struct ltc2983_sensor *sensor);
int ltc2983_read_channel_temp(struct ltc2983_dev *dev, uint8_t ch, float *temp);
```

---

## Basic Usage Example

```c
// Digital temperature sensor (I2C)
struct adt7420_dev *temp_dev;
struct adt7420_init_param init = {
    .i2c_init = {
        .max_speed_hz = 400000,
        .slave_address = 0x48,
        .platform_ops = &i2c_ops,
    },
    .resolution_setting = ADT7420_RESOLUTION_16_BIT,
    .op_mode = ADT7420_OP_MODE_CONT_CONV,
};

ret = adt7420_init(&temp_dev, &init);

float temperature;
ret = adt7420_get_temperature(temp_dev, &temperature);
pr_info("Temperature: %.2f C\n", temperature);

// RTD temperature (SPI)
struct max31865_dev *rtd_dev;
struct max31865_init_param rtd_init = {
    .spi_init = { .mode = NO_OS_SPI_MODE_1, /* ... */ },
    .rtd_type = MAX31865_PT100,
    .wire_mode = MAX31865_4WIRE,  // Best accuracy
    .r_ref = 4020,  // Measured value, not nominal!
    .filter_mode = MAX31865_FILTER_60HZ,
};

ret = max31865_init(&rtd_dev, &rtd_init);
ret = max31865_enable_bias(rtd_dev, true);
no_os_mdelay(10);

float rtd_temp;
ret = max31865_read_temp(rtd_dev, &rtd_temp);
```

---

## Key Configuration Options

**Resolution vs Conversion Time**:
- 13-bit: 0.0625C, 60ms (fast updates, low power)
- 16-bit: 0.0078C, 240ms (precision monitoring)

**RTD Wire Modes**:
- 2-wire: Simple, high error (+1C/wire)
- 3-wire: Industrial standard, compensates lead resistance
- 4-wire: Best accuracy, eliminates all lead resistance

**Operating Modes**:
- Continuous: Always converting (monitoring)
- One-shot: Single conversion (low power)
- Shutdown: Ultra-low power (battery)

---

## Common Patterns

**Temperature Alerts**:
```c
ret = adt7420_set_high_limit(dev, 50.0);
ret = adt7420_set_critical_limit(dev, 85.0);
ret = adt7420_set_hysteresis(dev, 2);  // 2C hysteresis
```

**Fault Detection**:
```c
// RTD
uint8_t fault;
ret = max31865_read_fault_status(dev, &fault);
if (fault & MAX31865_FAULT_HIGH_THRESHOLD)
    pr_err("RTD open circuit\n");

// Thermocouple
ret = max31855_read_fault(dev, &fault);
if (fault & MAX31855_FAULT_OPEN)
    pr_err("Thermocouple open circuit\n");
```

**Calibration**:
```c
// Single-point offset
float measured, reference = 25.0;
ret = adt7420_get_temperature(dev, &measured);
float offset = reference - measured;
// Apply offset in software to future readings
```

---

## Reference Documentation

Use Read tool to load detailed reference when needed:

- **reference/implementation.md** - Driver patterns, device descriptors, core functionality, IIO integration
- **reference/api-usage.md** - Complete usage examples, use cases, power management
- **reference/calibration.md** - Calibration methods, accuracy budgets, procedures
- **reference/best-practices.md** - Sensor selection, configuration guidelines, testing, pitfalls
- **reference/troubleshooting.md** - Communication issues, faults, diagnostics, solutions

---

## Summary

**Sensor Selection**:
- Digital (I2C): Board-level monitoring, ambient sensing
- RTD (SPI): Industrial process, precision lab equipment
- Thermocouple (SPI): High-temperature applications (ovens, engines)
- LTC2983 (SPI): Multiple measurement points, mixed sensor types

**Key Principles**:
- Use 4-wire mode for RTD best accuracy
- Always check fault registers for RTD/thermocouple
- Set correct 50Hz/60Hz filter based on location
- Measure actual Rref value (don't use nominal)
- Calibrate at operating temperature
- Higher resolution = longer conversion time + more power

**Related Skills**: `/no-os-debugging`, `/no-os-iio`, `/no-os-project-structure`, `/no-os-unit-testing`

**Example Projects**: `projects/adt7420/`, `projects/ltc2983/`, `projects/max31865/`
