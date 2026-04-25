# YAML Schema Binding Syntax

Detailed YAML schema syntax for Linux devicetree bindings.

## Complete Binding Template

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/[subsystem]/[vendor],[device].yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: One-line hardware description

maintainers:
  - Maintainer Name <email@example.com>

description:
  Multi-line detailed description of hardware capabilities,
  standards compliance, and datasheet references.

allOf:
  - $ref: /schemas/spi/spi-peripheral-props.yaml#  # For SPI devices
  # OR
  - $ref: /schemas/i2c/i2c-device.yaml#  # For I2C devices

properties:
  compatible:
    enum:
      - vendor,device-name

  reg:
    maxItems: 1

  # Additional properties defined here

required:
  - compatible
  - reg

unevaluatedProperties: false  # Use with $ref
# OR
additionalProperties: false   # Use without $ref

examples:
  - |
    #include <dt-bindings/gpio/gpio.h>

    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        device@0 {
            compatible = "vendor,device-name";
            reg = <0>;
            // Example properties
        };
    };
```

## Top-Level Properties

### $id (Unique Identifier)

```yaml
$id: http://devicetree.org/schemas/iio/adc/adi,ad7944.yaml#
```

- Must begin with `http://devicetree.org/schemas/`
- Path should match file location: `iio/adc/adi,ad7944.yaml`
- Must end with `#`
- Establishes unique URI for this binding

### $schema (Meta-Schema)

```yaml
$schema: http://devicetree.org/meta-schemas/core.yaml#
```

Always use `core.yaml#` for devicetree bindings.

### title (One-Line Description)

```yaml
title: Analog Devices AD7944 18-bit PulSAR ADC
```

- Single line, concise
- Describe the hardware, not the driver
- Include key specifications (resolution, type)

### maintainers (Email List)

```yaml
maintainers:
  - Michael Hennerich <Michael.Hennerich@analog.com>
  - Lars-Peter Clausen <lars@metafoo.de>
```

- Must be valid kernel developers
- List format with `- ` prefix
- Include email addresses

### description (Detailed Information)

```yaml
description:
  The AD7944 is a 14-bit successive approximation ADC with
  dual-channel multiplexed inputs. It operates from a single 2.5V
  supply and features low power consumption at high throughput rates.

  For complete specifications, see the product datasheet:
  https://www.analog.com/ad7944
```

- Multi-line text without `|` indicator
- Reference datasheets
- Mention key capabilities
- Optional (can be omitted if title is sufficient)

## Property Definitions

### Compatible Strings

**Single device:**
```yaml
properties:
  compatible:
    const: adi,ad7944
```

**Device family (enum):**
```yaml
properties:
  compatible:
    enum:
      - adi,ad7944
      - adi,ad7985
      - adi,ad7986
```

**Chip variants with fallback:**
```yaml
properties:
  compatible:
    oneOf:
      - const: adi,ad3541r
      - items:
          - enum:
              - adi,ad3542r
              - adi,ad3551r
              - adi,ad3552r
          - const: adi,ad3541r  # Fallback compatible
```

**Multi-variant with required fallback:**
```yaml
properties:
  compatible:
    items:
      - enum:
          - adi,ad9081-m2
          - adi,ad9082
      - const: adi,ad9081  # Generic fallback
```

### Register Address (reg)

**Single address:**
```yaml
properties:
  reg:
    maxItems: 1
```

**Multiple addresses:**
```yaml
properties:
  reg:
    items:
      - description: Control registers
      - description: Data buffer
```

**Flexible count:**
```yaml
properties:
  reg:
    minItems: 1
    maxItems: 4
```

### Interrupts

**Single interrupt:**
```yaml
properties:
  interrupts:
    maxItems: 1
    description: Data ready interrupt line
```

**Named interrupts:**
```yaml
properties:
  interrupts:
    items:
      - description: Data ready interrupt
      - description: Overrun interrupt

  interrupt-names:
    items:
      - const: drdy
      - const: overrun
```

### Clocks

**Single clock:**
```yaml
properties:
  clocks:
    maxItems: 1
    description: Master clock input

  clock-names:
    const: mclk
```

**Multiple clocks:**
```yaml
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

**Optional clock:**
```yaml
properties:
  clocks:
    minItems: 1
    maxItems: 2

  clock-names:
    minItems: 1
    items:
      - const: mclk
      - const: sclk  # Optional
```

## Conditional Constraints (allOf/if/then)

### Mutually Exclusive Properties

```yaml
allOf:
  - if:
      required:
        - ref-supply
    then:
      properties:
        refin-supply: false
```

### Variant-Specific Constraints

```yaml
allOf:
  - if:
      properties:
        compatible:
          contains:
            enum:
              - adi,ad3541r  # Single channel variant
    then:
      properties:
        channel@1: false  # Prevent second channel
      required:
        - channel@0
```

### Mode-Specific Requirements

```yaml
allOf:
  - if:
      properties:
        adi,spi-mode:
          const: chain
    then:
      properties:
        spi-max-frequency:
          maximum: 90909090
      required:
        - '#daisy-chained-devices'
    else:
      properties:
        '#daisy-chained-devices': false
```

### Conditional Property Values

```yaml
allOf:
  - if:
      properties:
        compatible:
          contains:
            const: adi,ad7606-8
    then:
      properties:
        adi,oversampling-ratio:
          enum: [1, 2, 4, 8, 16, 32, 64]
    else:
      properties:
        adi,oversampling-ratio:
          enum: [1, 2, 4, 8, 16, 32, 64, 128, 256]
```

## Child Node Patterns

### Pattern Properties

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

    additionalProperties: false

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
          - items:
              - const: -5000000
              - const: 5000000

    required:
      - reg
      - adi,output-range-microvolt
```

### Common Pattern Regex

| Pattern | Matches | Use Case |
|---------|---------|----------|
| `"^channel@([0-1])$"` | channel@0, channel@1 | Two channels |
| `"^channel@[0-3]$"` | channel@0 to channel@3 | Four channels |
| `"^channel@[0-9]$"` | channel@0 to channel@9 | Ten channels |
| `"^port@[0-9a-f]$"` | port@0 to port@f | Hex addressed ports |
| `"^.*@[0-9a-f]+$"` | Any node with hex address | Generic child nodes |

## Disallowing Extra Properties

### additionalProperties vs unevaluatedProperties

**Use `unevaluatedProperties: false` when using `$ref`:**
```yaml
$ref: /schemas/spi/spi-peripheral-props.yaml#

properties:
  compatible:
    const: adi,ad7944

  # Device-specific properties

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

**Why the difference?**
- `additionalProperties` validates only locally defined properties
- `unevaluatedProperties` validates after considering all `$ref` schemas
- Using `additionalProperties` with `$ref` blocks inherited properties

## Examples Section

### Basic Example

```yaml
examples:
  - |
    #include <dt-bindings/gpio/gpio.h>

    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7944";
            reg = <0>;
            spi-max-frequency = <111111111>;

            avdd-supply = <&supply_2_5V>;
            dvdd-supply = <&supply_2_5V>;
            vio-supply = <&supply_1_8V>;

            cnv-gpios = <&gpio 0 GPIO_ACTIVE_HIGH>;
        };
    };
```

### Multiple Examples

```yaml
examples:
  # Example 1: Basic configuration
  - |
    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7944";
            reg = <0>;
            spi-max-frequency = <50000000>;
            avdd-supply = <&vdd>;
        };
    };

  # Example 2: Advanced configuration with channels
  - |
    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        dac@1 {
            compatible = "adi,ad3552r";
            reg = <1>;
            spi-max-frequency = <30000000>;

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
    };
```

### Example Guidelines

- Use 4-space indentation in DTS examples
- Include all required properties
- Show realistic, working configurations
- Use `#include` for constants (GPIO flags, IRQ types)
- Add comments for clarity when needed
- Include parent bus node (`spi`, `i2c`, etc.)
