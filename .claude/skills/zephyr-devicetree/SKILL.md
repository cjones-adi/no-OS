---
name: zephyr-devicetree
description: 'Complete guide to creating Zephyr devicetree bindings (YAML files that define hardware device interfaces). Use when implementing devicetree bindings for new devices, understanding property types, configuring bus-specific bindings (I2C/SPI), creating controller bindings (GPIO/ADC/DAC), implementing parent-child hierarchies for MFDs, or debugging devicetree issues.'
---

# Zephyr Devicetree Binding Development

This skill provides comprehensive understanding of Zephyr devicetree bindings - the YAML files that define how hardware devices are described in devicetree files.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/property-types.md**:
- User asks: "property types", "int", "boolean", "string", "array", "phandle"
- Questions about: property constraints (required, const, default, enum)
- User mentions: "what type should I use", "property syntax"
- Need: complete property type reference with examples

**Triggers to read reference/base-bindings.md**:
- User mentions: "base binding", "include", "i2c-device", "spi-device", "sensor-device"
- Questions about: common base bindings, bus-specific bindings, subsystem bindings
- User asks: "what should I include", "base.yaml", "power.yaml"
- Need: complete list of base bindings and their purposes

**Triggers to read reference/controllers-and-children.md**:
- User mentions: "#cells", "gpio-cells", "io-channel-cells", "child-binding"
- Questions about: controller bindings, phandle arrays, parent-child relationships
- User asks: "GPIO controller binding", "ADC controller", "MFD parent-child"
- Need: controller patterns and child binding examples

**Triggers to read reference/examples.md**:
- User asks: "complete example", "full binding", "I2C sensor example", "SPI ADC example"
- Questions about: real-world bindings, complete YAML files
- Need: 4 complete binding examples (sensor, ADC, DAC, GPIO)

**Triggers to read reference/validation-testing.md**:
- User asks: "validate binding", "test devicetree", "DTC errors"
- Questions about: devicetree compiler validation, testing bindings
- Need: validation steps and testing procedures

**Triggers to read reference/binding-patterns.md**:
- User asks: "common patterns", "best practices", "bus variants", "GPIO interrupt"
- Questions about: include patterns, voltage ranges, operating modes
- Need: 6 common binding patterns with examples

**Triggers to read reference/debugging-and-best-practices.md**:
- User says: "error", "unknown compatible", "missing required property", "cells mismatch"
- Build/devicetree errors
- Questions about: debugging DTS issues, generated macros, best practices
- Need: debugging steps, common errors, and best practices

---

## When to Use This Skill

Use this skill when you need to:
- Create a new devicetree binding (`.yaml`) for a hardware device
- Understand devicetree property types (int, boolean, string, array, phandle, etc.)
- Configure bus-specific bindings (I2C, SPI devices)
- Create controller bindings (GPIO, ADC, DAC controllers)
- Implement parent-child devicetree hierarchies (MFD devices)
- Define vendor-specific properties for custom hardware
- Debug devicetree validation errors
- Understand the `include` mechanism for base bindings
- Configure `child-binding` patterns for complex devices
- Work with `#cells` and cell specifiers

## What is a Devicetree Binding?

**Devicetree bindings** are YAML files that define the schema for devicetree nodes. They specify:

- **Compatible strings** – What devices the binding describes
- **Properties** – Configuration options (type, required/optional, valid values)
- **Includes** – Base bindings to extend (i2c-device, gpio-controller, etc.)
- **Child bindings** – Structure for parent-child relationships
- **Bus constraints** – Which bus the device connects to
- **Cell specifications** – How phandles encode device-specific data

### Why Bindings Matter

- **Validation**: Devicetree compiler validates DTS files against bindings
- **Documentation**: Bindings document valid properties and values
- **Type Safety**: Property types prevent configuration errors
- **Code Generation**: Macros generated from bindings for driver access
- **Reusability**: Include mechanism allows extending base bindings

### Zephyr Binding Organization

Bindings are organized by subsystem in `zephyr/dts/bindings/`:

```
zephyr/dts/bindings/
├── base/               # Base bindings (base.yaml, power.yaml)
├── i2c/                # I2C bus and devices
├── spi/                # SPI bus and devices
├── gpio/               # GPIO controllers
├── adc/                # ADC controllers
├── dac/                # DAC controllers
├── sensor/             # Sensor devices
├── mfd/                # Multi-Function Devices
└── ... (80+ subsystems)
```

## Binding File Naming Convention

```
<vendor>,<chip>[-subsystem].yaml

Examples:
- adi,adxl345.yaml              (sensor)
- adi,ad4130-adc.yaml           (ADC)
- adi,ad559x-dac.yaml           (DAC child of MFD)
- maxim,max20370-regulator.yaml (regulator child of MFD)
```

## Basic Binding Structure (Quick Reference)

### Minimal Binding

```yaml
description: Short description of the device
compatible: "vendor,chip"
include: i2c-device.yaml  # or spi-device.yaml

properties:
  resolution:
    type: int
    required: true
    description: ADC resolution in bits
```

### Complete Binding Template

```yaml
description: Comprehensive device description

compatible: "vendor,chip"

include: base-binding.yaml  # i2c-device, spi-device, sensor-device, etc.

properties:
  property-name:
    type: int | boolean | string | array | phandle | phandle-array
    required: true | false
    default: value
    const: value
    enum: [value1, value2]
    description: Property description

bus: i2c | spi  # Optional bus constraint

on-bus: i2c | spi  # Alternate bus specification
```

**See**: [reference/property-types.md](reference/property-types.md) for complete property type reference.

## Property Types (Quick Reference)

| Type | Description | Example |
|------|-------------|---------|
| `int` | Integer value | `resolution: 12` |
| `boolean` | True if present | `buffered;` |
| `string` | Text value | `label = "TEMP_SENSOR";` |
| `array` | Numeric array | `thresholds = <100 200 300>;` |
| `uint8-array` | Byte array | `init-sequence = [01 02 03];` |
| `string-array` | String array | `modes = "pwm", "pfm", "auto";` |
| `phandle` | Device reference | `parent = <&mfd_dev>;` |
| `phandle-array` | Reference with cells | `gpios = <&gpio0 5 GPIO_ACTIVE_HIGH>;` |
| `path` | Node path | `zephyr,console = &uart0;` |
| `compound` | Complex structure | Custom structure |

**See**: [reference/property-types.md](reference/property-types.md) for detailed examples and constraints.

## Common Base Bindings (Quick Reference)

| Base Binding | When to Include | Provides |
|--------------|-----------------|----------|
| `base.yaml` | All devices | Common properties (status, compatible) |
| `power.yaml` | Devices with PM | Power management properties |
| `i2c-device.yaml` | I2C devices | `reg`, I2C bus properties |
| `spi-device.yaml` | SPI devices | `reg`, `spi-max-frequency`, SPI mode |
| `sensor-device.yaml` | Sensors | Sensor-specific properties |
| `adc-controller.yaml` | ADC controllers | `#io-channel-cells`, `io-channel-controller` |
| `dac-controller.yaml` | DAC controllers | `#io-channel-cells`, `io-channel-controller` |
| `gpio-controller.yaml` | GPIO controllers | `gpio-controller`, `#gpio-cells`, `ngpios` |

**See**: [reference/base-bindings.md](reference/base-bindings.md) for complete list with examples.

## Controller Bindings (Quick Reference)

Controllers use `#cells` to define how phandles reference them:

```yaml
# GPIO Controller
gpio-controller: true
"#gpio-cells": 2  # <pin flags>

# Usage in DTS:
led0 {
    gpios = <&gpio0 5 GPIO_ACTIVE_HIGH>;
           # ^^^^^^ ^ ^^^^^^^^^^^^^^^^^
           # device pin flags
};

# ADC/DAC Controller
io-channel-controller: true
"#io-channel-cells": 1  # <channel>

# Usage in DTS:
io-channels = <&adc0 3>;
              # ^^^^ ^
              # device channel
```

**See**: [reference/controllers-and-children.md](reference/controllers-and-children.md) for detailed patterns.

## Quick Start Workflow

1. **Choose Base Binding** – Include `i2c-device.yaml` or `spi-device.yaml`
2. **Define Compatible** – `compatible: "vendor,chip"`
3. **Add Properties** – Define device-specific properties with types
4. **Set Constraints** – Mark required properties, add defaults
5. **Add Child Bindings** (if needed) – For MFD or multi-channel devices
6. **Define #cells** (if controller) – For GPIO/ADC/DAC controllers
7. **Validate** – Build and check for devicetree errors

**For detailed property types and constraints**: Read [reference/property-types.md](reference/property-types.md)

**For complete examples**: Read [reference/examples.md](reference/examples.md)

## Debugging Devicetree Issues (Quick Reference)

Common errors:

| Error | Cause | Solution |
|-------|-------|----------|
| `unknown compatible` | Missing binding file | Create `.yaml` binding for compatible string |
| `missing required property` | Required property not in DTS | Add property or make it optional |
| `value not in enum` | Invalid enum value | Use one of the enum values from binding |
| `duplicate node name` | Same node name twice | Use unique node names or unit addresses |
| `#cells mismatch` | Wrong number of cells in phandle array | Match number of cells to `#cells` definition |

**View generated devicetree**:
```bash
west build -t devicetree_generated
# Output: build/zephyr/zephyr.dts
```

**View generated macros**:
```bash
# Output: build/zephyr/include/generated/devicetree_generated.h
```

**See**: [reference/debugging-and-best-practices.md](reference/debugging-and-best-practices.md) for complete debugging guide.

## Best Practices (Summary)

✅ **DO**:
- Use descriptive property names (`sampling-frequency` not `sf`)
- Provide clear descriptions for all properties
- Include appropriate base bindings (`i2c-device.yaml`, etc.)
- Use sensible defaults for optional properties
- Document register values with enums or constants
- Use `vendor,property` for vendor-specific properties
- Define `#cells` for controller bindings
- Test bindings with real devicetree files

❌ **DON'T**:
- Don't use generic property names without vendor prefix
- Don't omit property descriptions
- Don't forget to include base bindings
- Don't hardcode values that should be configurable
- Don't create duplicate bindings (reuse existing ones)

**See**: [reference/debugging-and-best-practices.md](reference/debugging-and-best-practices.md) for detailed best practices.

## References

**Zephyr Documentation**:
- **Bindings**: `zephyr/dts/bindings/`
- **Base Bindings**: `zephyr/dts/bindings/base/`
- **Devicetree Guide**: https://docs.zephyrproject.org/latest/build/dts/

**Example Bindings**:
- **I2C Sensor**: `dts/bindings/sensor/adi,adxl345.yaml`
- **SPI ADC**: `dts/bindings/adc/adi,ad4130-adc.yaml`
- **GPIO Controller**: `dts/bindings/gpio/gpio-controller.yaml`
- **MFD Parent-Child**: `dts/bindings/mfd/adi,ad559x.yaml` + `dts/bindings/dac/adi,ad559x-dac.yaml`

**Reference Guides**:
- [reference/property-types.md](reference/property-types.md) – Complete property type reference (10 types + constraints)
- [reference/base-bindings.md](reference/base-bindings.md) – Common, bus-specific, and subsystem base bindings
- [reference/controllers-and-children.md](reference/controllers-and-children.md) – Controller patterns and child bindings
- [reference/examples.md](reference/examples.md) – 4 complete binding examples
- [reference/validation-testing.md](reference/validation-testing.md) – Validation and testing procedures
- [reference/binding-patterns.md](reference/binding-patterns.md) – 6 common binding patterns
- [reference/debugging-and-best-practices.md](reference/debugging-and-best-practices.md) – Debugging, errors, and best practices

## Summary Checklist

### Binding File
- [ ] File named `<vendor>,<chip>[-subsystem].yaml`
- [ ] Description provided
- [ ] Compatible string defined
- [ ] Appropriate base binding included
- [ ] Properties defined with types
- [ ] Required properties marked
- [ ] Defaults provided for optional properties
- [ ] Property descriptions written

### Controller Bindings (if applicable)
- [ ] `gpio-controller: true` or `io-channel-controller: true`
- [ ] `#gpio-cells` or `#io-channel-cells` defined
- [ ] Cell meaning documented

### Parent-Child (if applicable)
- [ ] Parent binding defines `child-binding:`
- [ ] Child compatible strings defined
- [ ] Child properties defined

### Testing
- [ ] Binding validates without errors
- [ ] DTS file using binding builds successfully
- [ ] Generated macros are correct
- [ ] Properties accessible from driver code
