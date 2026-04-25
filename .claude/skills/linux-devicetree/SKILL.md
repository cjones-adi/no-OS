---
name: linux-devicetree
description: Comprehensive guide to Linux devicetree bindings in YAML schema format for hardware description. Use when creating devicetree bindings, validating DT schemas, working with bus-specific properties, or debugging devicetree issues.
---

# Linux Devicetree Bindings

Quick reference for creating and validating Linux devicetree bindings in YAML schema format.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/binding-syntax.md**:
- User mentions: "create binding", "YAML schema", "binding template", "$id", "$schema", "allOf/if/then"
- Questions about: top-level properties, conditional constraints, patternProperties, child nodes
- User asks: "how to structure", "binding format", "schema syntax", "complete template"
- Topics: $ref usage, additionalProperties vs unevaluatedProperties, examples section

**Triggers to read reference/property-types.md**:
- User mentions: "property types", "uint32", "string", "boolean", "array", "phandle"
- Questions about: type definitions, constraints (enum, minimum, maximum), oneOf/anyOf
- User asks: "what type", "how to define", "property syntax", "array format"
- Topics: /schemas/types.yaml, integer arrays, string arrays, GPIO flags, supply properties

**Triggers to read reference/validation.md**:
- User mentions: "validate", "dt_binding_check", "dtbs_check", "error", "warning"
- Questions about: validation errors, schema errors, binding warnings, fixing issues
- User asks: "how to validate", "check binding", "validation failed", "fix error"
- Topics: make commands, common errors and solutions, debugging validation, CI integration

**Triggers to read reference/bus-bindings.md**:
- User mentions: "SPI", "I2C", "platform device", "MMIO", "bus binding"
- Questions about: spi-peripheral-props.yaml, i2c-device.yaml, SPI modes, I2C addressing
- User asks: "SPI device", "I2C device", "bus properties", "complete example"
- Topics: reg property, interrupts, clocks, io-backends, AXI/FPGA integration

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "naming convention", "common patterns", "guidelines"
- Questions about: compatible strings, property naming, organization, description quality
- Topics: vendor prefixes, adi conventions, platform independence, pitfalls to avoid

---

## When to Use This Skill

- Creating YAML schema bindings for new hardware devices
- Adding devicetree support to Linux kernel drivers
- Validating devicetree bindings with dt_binding_check
- Working with bus-specific bindings (SPI, I2C, platform)
- Understanding devicetree properties and constraints
- Debugging devicetree compilation or validation errors
- Creating devicetree examples for driver documentation
- Supporting multi-platform devicetrees (Zynq, ZynqMP, Versal, SoCFPGA, Raspberry Pi)

## Devicetree Overview

### What is Devicetree?

The devicetree describes hardware topology, not software. It enables the kernel to discover hardware configuration at runtime.

**Device Registration Flow:**
```
Bootloader → FDT (binary) → Kernel → of_platform_populate() → Platform Devices
                                   ↓
                          Bus Drivers (SPI/I2C) → Child Devices
```

Platform devices at the tree's root are registered through `of_platform_populate()`. Child devices of buses (I2C, SPI) are registered by their parent bus driver.

### YAML Schema Format

Devicetree bindings use YAML-formatted JSON-schema:
- More readable than JSON
- Supports comments
- Compatible with JSON-schema validation tools
- Standard format enforced by kernel maintainers since 2019

## Quick Reference

### Common Property Types

| Type | Schema Reference | Example |
|------|-----------------|---------|
| Boolean | `type: boolean` | `adi,external-reference: true` |
| String | `$ref: /schemas/types.yaml#/definitions/string` | `adi,spi-mode = "chain"` |
| Uint32 | `$ref: /schemas/types.yaml#/definitions/uint32` | `adi,value = <100>` |
| Int32 | `$ref: /schemas/types.yaml#/definitions/int32` | `adi,offset = <-50>` |
| Uint64 | `$ref: /schemas/types.yaml#/definitions/uint64` | `/bits/ 64 <4000000000>` |
| Array | `$ref: /schemas/types.yaml#/definitions/uint32-array` | `values = <1 2 3 4>` |
| Phandle | (automatic) | `vref-supply = <&vref_ext>` |
| GPIO | (automatic) | `reset-gpios = <&gpio 10 GPIO_ACTIVE_LOW>` |

### Standard Bus Properties

| Property | Description |
|----------|-------------|
| `compatible` | Device identifier (vendor,device-name) |
| `reg` | Address on bus (SPI chip select, I2C address, or MMIO address) |
| `interrupts` | Interrupt specifier |
| `clocks` | Clock phandle references |
| `clock-names` | Clock identifier strings |
| `*-supply` | Regulator/power supply phandles |
| `*-gpios` | GPIO specifiers |

### SPI-Specific Properties

| Property | Description |
|----------|-------------|
| `spi-max-frequency` | Maximum SPI clock in Hz |
| `spi-cpol` | Clock polarity (idle high) |
| `spi-cpha` | Clock phase (sample on trailing edge) |
| `spi-cs-high` | Chip select active high |

### I2C-Specific Properties

| Property | Description |
|----------|-------------|
| `reg` | I2C slave address (7-bit: 0x00-0x7F) |

### Validation Commands

```bash
# Validate binding schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad7944.yaml

# Validate compiled devicetree
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- dtbs_check

# Validate specific DTS against binding
make ARCH=arm64 DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad9081.yaml dtbs_check
```

## Quick Start: Binding Templates

Complete YAML binding templates are available in the [examples](examples/) folder:

- **[spi-device-binding.yaml](examples/spi-device-binding.yaml)** - SPI device binding template (AD7944 ADC)
- **[i2c-device-binding.yaml](examples/i2c-device-binding.yaml)** - I2C device binding template (LTC2991 monitor)
- **[platform-device-binding.yaml](examples/platform-device-binding.yaml)** - Platform/MMIO device binding template (AXI-DMAC)

## Essential Patterns

### Compatible Strings (ADI Convention)

Always use `adi,` prefix in lowercase:

```yaml
# Single device
properties:
  compatible:
    const: adi,ad7944

# Device family
properties:
  compatible:
    enum:
      - adi,ad7944
      - adi,ad7985
      - adi,ad7986

# Variants with fallback
properties:
  compatible:
    oneOf:
      - const: adi,ad3541r
      - items:
          - enum:
              - adi,ad3542r
              - adi,ad3551r
          - const: adi,ad3541r  # Fallback
```

### Supply Properties

Power supplies use `-supply` suffix:

```yaml
properties:
  avdd-supply:
    description: Analog supply voltage (2.5V)

  dvdd-supply:
    description: Digital supply voltage (2.5V)

  vio-supply:
    description: I/O supply voltage (1.8V to 2.7V)
```

In DTS:
```dts
adc@0 {
    avdd-supply = <&supply_2_5V>;
    dvdd-supply = <&supply_2_5V>;
    vio-supply = <&supply_1_8V>;
};
```

### GPIO Properties

GPIO properties use `-gpios` suffix:

```yaml
properties:
  reset-gpios:
    maxItems: 1
    description: Hardware reset GPIO (active low)

  cnv-gpios:
    maxItems: 1
    description: Convert input GPIO (active high)
```

In DTS:
```dts
#include <dt-bindings/gpio/gpio.h>

adc@0 {
    reset-gpios = <&gpio 10 GPIO_ACTIVE_LOW>;
    cnv-gpios = <&gpio 11 GPIO_ACTIVE_HIGH>;
};
```

GPIO flags:
- `GPIO_ACTIVE_HIGH` (0)
- `GPIO_ACTIVE_LOW` (1)
- `GPIO_OPEN_DRAIN` (2)
- `GPIO_PULL_UP` (8)
- `GPIO_PULL_DOWN` (16)

### Clock Properties

```yaml
# Single clock
properties:
  clocks:
    maxItems: 1

  clock-names:
    const: mclk

# Multiple clocks
properties:
  clocks:
    items:
      - description: Master clock
      - description: Sample clock

  clock-names:
    items:
      - const: mclk
      - const: sclk
```

### Vendor-Specific Properties

All ADI custom properties use `adi,` prefix:

```yaml
properties:
  adi,sdo-drive-strength:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [0, 1, 2, 3]
    description: SDO drive strength level

  adi,always-turbo:
    type: boolean
    description: Keep turbo mode permanently enabled
```

### Child Nodes with Channels

```yaml
properties:
  '#address-cells':
    const: 1

  '#size-cells':
    const: 0

patternProperties:
  "^channel@([0-1])$":
    type: object
    description: DAC channel configurations

    properties:
      reg:
        description: Channel number
        enum: [0, 1]

      adi,output-range-microvolt:
        description: Voltage output range as <min, max>
        oneOf:
          - items:
              - const: 0
              - enum: [2500000, 5000000, 10000000]

    required:
      - reg
      - adi,output-range-microvolt

    additionalProperties: false
```

In DTS:
```dts
dac@0 {
    #address-cells = <1>;
    #size-cells = <0>;

    channel@0 {
        reg = <0>;
        adi,output-range-microvolt = <0 5000000>;
    };

    channel@1 {
        reg = <1>;
        adi,output-range-microvolt = <0 10000000>;
    };
};
```

### Conditional Constraints

Use `allOf` with `if/then` for variant-specific behavior:

```yaml
allOf:
  # Mutually exclusive properties
  - if:
      required:
        - ref-supply
    then:
      properties:
        refin-supply: false

  # Variant-specific constraints
  - if:
      properties:
        compatible:
          contains:
            const: adi,ad3541r  # Single channel
    then:
      properties:
        channel@1: false  # Prevent second channel
```

## Common Property Patterns

### Boolean (Presence/Absence)

```yaml
properties:
  adi,external-reference:
    type: boolean
    description: Use external reference voltage
```

### Enum (Fixed Choices)

```yaml
properties:
  adi,spi-mode:
    $ref: /schemas/types.yaml#/definitions/string
    enum: [single, chain]

  adi,oversampling-ratio:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [1, 2, 4, 8, 16, 32, 64]
```

### Range (Min/Max)

```yaml
properties:
  spi-max-frequency:
    maximum: 111111111

  adi,sample-rate:
    $ref: /schemas/types.yaml#/definitions/uint32
    minimum: 1000
    maximum: 1000000
```

### Array (Fixed Size)

```yaml
properties:
  adi,output-range-microvolt:
    description: Voltage range as <min, max>
    items:
      - description: Minimum voltage
      - description: Maximum voltage
```

### Array (Variable Size)

```yaml
properties:
  adi,gain-values:
    $ref: /schemas/types.yaml#/definitions/uint32-array
    minItems: 1
    maxItems: 8
```

## Key Differences: additionalProperties vs unevaluatedProperties

**Use `unevaluatedProperties: false` with `$ref`:**
```yaml
$ref: /schemas/spi/spi-peripheral-props.yaml#

properties:
  compatible:
    const: adi,ad7944

unevaluatedProperties: false  # Considers $ref properties
```

**Use `additionalProperties: false` without `$ref`:**
```yaml
properties:
  compatible:
    const: adi,platform-device

  reg:
    maxItems: 1

additionalProperties: false  # Only local properties
```

**Why?** `additionalProperties` validates only locally defined properties. `unevaluatedProperties` validates after considering all `$ref` schemas. Using `additionalProperties` with `$ref` blocks inherited properties.

## Validation Workflow

```bash
# 1. Create/modify YAML binding
vim Documentation/devicetree/bindings/iio/adc/adi,ad9083.yaml

# 2. Validate binding schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad9083.yaml

# 3. Fix any errors, repeat step 2 until clean

# 4. Create/modify DTS file
vim arch/arm64/boot/dts/xilinx/zynqmp-zcu102-rev10-ad9083.dts

# 5. Compile DTS to DTB
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- zynqmp-zcu102-rev10-ad9083.dtb

# 6. Validate DTS against binding
make ARCH=arm64 DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad9083.yaml dtbs_check

# 7. Fix warnings, repeat until clean
```

## ADI-Specific Patterns

### JESD204 Topology

For high-speed converters using JESD204:

```yaml
properties:
  adi,jesd204-topology:
    $ref: /schemas/types.yaml#/definitions/uint32-array
    description: JESD204 link topology configuration

  clocks:
    items:
      - description: JESD204 device clock
      - description: JESD204 link clock
```

Reference: See `linux-jesd204` skill for detailed topology configuration.

### IIO Backend (FPGA Integration)

For devices connected to FPGA IP cores:

```yaml
properties:
  io-backends:
    description:
      IIO backend reference for FPGA-based controller
      (e.g., axi-ad3552r for high-speed QSPI+DDR).
    maxItems: 1
```

In DTS:
```dts
axi_ad3552r: axi-ad3552r@44a70000 {
    compatible = "adi,axi-ad3552r";
    reg = <0x44a70000 0x1000>;
    #io-backend-cells = <0>;
};

&spi0 {
    dac@0 {
        compatible = "adi,ad3552r";
        reg = <0>;
        io-backends = <&axi_ad3552r>;
    };
};
```

## Multi-Platform Examples

### Xilinx Zynq (ARM 32-bit)

Path: `arch/arm/boot/dts/xilinx/`

```dts
#include "zynq-zc706.dtsi"

&spi0 {
    status = "okay";

    adc@0 {
        compatible = "adi,ad9467";
        reg = <0>;
        spi-max-frequency = <10000000>;
        clocks = <&axi_ad9467_clkgen>;
        io-backends = <&axi_ad9467>;
    };
};
```

### Xilinx ZynqMP (ARM64)

Path: `arch/arm64/boot/dts/xilinx/`

```dts
#include "zynqmp-zcu102-rev1.0.dts"

&spi0 {
    status = "okay";

    adc@0 {
        compatible = "adi,ad9081";
        reg = <0>;
        spi-max-frequency = <5000000>;
        reset-gpios = <&gpio 133 GPIO_ACTIVE_LOW>;

        vdd1-supply = <&reg_1v8>;
        avdd1-supply = <&reg_1v3>;

        clocks = <&axi_ad9081_rx_jesd 0>;
        io-backends = <&axi_ad9081_rx>;
    };
};
```

### Raspberry Pi (Overlay)

```dts
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2711";  // RPi 4

    fragment@0 {
        target = <&spi0>;
        __overlay__ {
            status = "okay";

            adc@0 {
                compatible = "adi,ad7606-8";
                reg = <0>;
                spi-max-frequency = <10000000>;

                avcc-supply = <&reg_5v0>;
                reset-gpios = <&gpio 22 GPIO_ACTIVE_LOW>;
                convst-gpios = <&gpio 17 GPIO_ACTIVE_HIGH>;
            };
        };
    };
};
```

## Common Pitfalls

### Missing SPDX License

```yaml
# WRONG - missing SPDX
%YAML 1.2
---

# CORRECT
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
```

### Incorrect List Syntax

```yaml
# WRONG
compatible:
  enum:
    adi,ad7944

# CORRECT
compatible:
  enum:
    - adi,ad7944
```

### Wrong Property Type with $ref

```yaml
# WRONG
$ref: /schemas/spi/spi-peripheral-props.yaml#
additionalProperties: false

# CORRECT
$ref: /schemas/spi/spi-peripheral-props.yaml#
unevaluatedProperties: false
```

### Missing Anchors in Patterns

```yaml
# WRONG - matches "channel@0abc"
patternProperties:
  "channel@[0-1]":

# CORRECT
patternProperties:
  "^channel@[0-1]$":
```

## Best Practices Checklist

- [ ] SPDX license identifier on line 1
- [ ] Use `adi,` prefix for compatible strings
- [ ] All device names in lowercase
- [ ] Required properties in `required` list
- [ ] Properties have descriptions with units
- [ ] Use `unevaluatedProperties: false` with `$ref`
- [ ] Use `additionalProperties: false` without `$ref`
- [ ] Examples compile and validate
- [ ] Run `make dt_binding_check` with no errors
- [ ] Run `make dtbs_check` on affected platforms
- [ ] Pattern properties use `^...$` anchors
- [ ] GPIO properties use `-gpios` suffix (plural)
- [ ] Supply properties use `-supply` suffix

## References

### Kernel Documentation

- Writing Devicetree Bindings: `Documentation/devicetree/bindings/writing-schema.rst`
- Devicetree Usage Model: `Documentation/devicetree/usage-model.rst`
- Submitting Patches: `Documentation/devicetree/bindings/submitting-patches.rst`

### Schema Files

- Property types: `/schemas/types.yaml`
- SPI devices: `/schemas/spi/spi-peripheral-props.yaml`
- I2C devices: `/schemas/i2c/i2c-device.yaml`
- Core schemas: `/schemas/dt-schema/`

### ADI Examples

- ADC bindings: `Documentation/devicetree/bindings/iio/adc/adi,*.yaml`
- DAC bindings: `Documentation/devicetree/bindings/iio/dac/adi,*.yaml`
- HWMON bindings: `Documentation/devicetree/bindings/hwmon/adi,*.yaml`
- Zynq DTS: `arch/arm/boot/dts/xilinx/zynq-*.dts`
- ZynqMP DTS: `arch/arm64/boot/dts/xilinx/zynqmp-*.dts`

### Related Skills

- **linux-iio**: IIO subsystem patterns for ADC/DAC drivers
- **linux-gpio**: GPIO consumer and controller patterns
- **linux-regulator**: Regulator framework for power supplies
- **linux-clk**: Common Clock Framework
- **linux-kconfig-makefile**: Build system integration
