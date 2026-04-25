# Devicetree Best Practices

Common patterns, naming conventions, and recommendations for creating devicetree bindings.

## Naming Conventions

### Compatible Strings

**ADI Convention:** Always use `adi,` prefix (not `analog,` or `analogdevices,`)

```yaml
# Correct
compatible:
  enum:
    - adi,ad7944
    - adi,ad7985
    - adi,ad7986

# Wrong
compatible:
  enum:
    - analog,ad7944     # Wrong prefix
    - AD7944            # Wrong: uppercase
    - ad7944            # Wrong: missing vendor
```

**Multi-Chip Families:**

Most specific first, fallback last:

```yaml
# Variant with fallback
compatible:
  items:
    - enum:
        - adi,ad9081-m2  # Specific variant
        - adi,ad9082     # Different chip, same family
    - const: adi,ad9081  # Generic fallback

# In DTS
compatible = "adi,ad9081-m2", "adi,ad9081";
```

Driver matches on either string, uses most specific for variant detection.

### Vendor-Specific Properties

All ADI custom properties use `adi,` prefix:

```yaml
properties:
  adi,vref-out-en:
    type: boolean
    description: Enable internal Vref output to 2.5V

  adi,sdo-drive-strength:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [0, 1, 2, 3]
```

### Supply Properties

Follow datasheet pin names, lowercase with hyphens:

```yaml
# Datasheet: AVDD, DVDD, VIO, VREF
properties:
  avdd-supply:
    description: Analog supply (2.5V)

  dvdd-supply:
    description: Digital supply (2.5V)

  vio-supply:
    description: I/O supply (1.8V to 2.7V)

  vref-supply:
    description: External reference voltage (optional)
```

### GPIO Properties

Use `-gpios` suffix (not `-gpio`):

```yaml
properties:
  reset-gpios:    # Correct
    maxItems: 1

  cnv-gpios:      # Correct
    maxItems: 1

  reset-gpio:     # Wrong: use -gpios
    maxItems: 1
```

Even for single GPIO, use plural `-gpios`.

## Property Organization

Order properties logically in binding:

```yaml
properties:
  # 1. Core identification
  compatible:
  reg:

  # 2. Standard bus properties
  spi-max-frequency:
  interrupts:
  clocks:
  clock-names:

  # 3. Power supplies (alphabetically)
  avdd-supply:
  dvdd-supply:
  vio-supply:
  vref-supply:

  # 4. GPIOs (alphabetically)
  cnv-gpios:
  ldac-gpios:
  reset-gpios:

  # 5. Vendor-specific (alphabetically)
  adi,always-turbo:
  adi,external-reference:
  adi,spi-mode:

  # 6. Child node metadata (if needed)
  '#address-cells':
  '#size-cells':
```

## Description Quality

### Good Descriptions

Explain WHAT the property does, reference datasheet when complex:

```yaml
# Good
cnv-gpios:
  description:
    GPIO connected to CNV (Convert) pin. This input initiates conversions
    and selects the SPI mode. In 'single' mode, this property can be
    omitted if CNV is connected to the SPI controller's CS line.
  maxItems: 1

# Good
adi,oversampling-ratio:
  $ref: /schemas/types.yaml#/definitions/uint32
  enum: [1, 2, 4, 8, 16, 32, 64]
  description:
    Oversampling ratio for noise reduction. Higher values improve SNR
    at the cost of lower output data rate. See datasheet Table 12.

# Bad (too vague)
cnv-gpios:
  description: CNV pin
  maxItems: 1

# Bad (duplicates type info)
adi,oversampling-ratio:
  $ref: /schemas/types.yaml#/definitions/uint32
  description: Oversampling ratio value
```

### Include Units

Always specify units in descriptions:

```yaml
properties:
  spi-max-frequency:
    maximum: 111111111
    description: Maximum SPI clock frequency in Hz

  adi,output-range-microvolt:
    description: Voltage output range in microvolts as <min, max>

  shunt-resistor-micro-ohms:
    description: Current sense resistor value in micro-ohms

  adi,debounce-time-us:
    $ref: /schemas/types.yaml#/definitions/uint32
    description: Debounce time in microseconds
```

## YAML Formatting

### Indentation

Use 2 spaces (not tabs, not 4 spaces):

```yaml
properties:
  compatible:
    enum:
      - adi,ad7944
```

### DTS Examples

Use 4-space indentation for readability:

```yaml
examples:
  - |
    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7944";
            reg = <0>;
        };
    };
```

### Multi-line Descriptions

Don't use `|` for descriptions:

```yaml
# Correct
description:
  Multi-line description text here.
  Second line of description.

# Wrong
description: |
  Multi-line description text here.
  Second line of description.
```

## Examples Quality

### Include All Required Elements

```yaml
examples:
  - |
    #include <dt-bindings/gpio/gpio.h>
    #include <dt-bindings/interrupt-controller/irq.h>

    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7944";
            reg = <0>;
            spi-cpha;
            spi-max-frequency = <111111111>;

            /* Power supplies */
            avdd-supply = <&supply_2_5V>;
            dvdd-supply = <&supply_2_5V>;
            vio-supply = <&supply_1_8V>;

            /* GPIOs */
            cnv-gpios = <&gpio 0 GPIO_ACTIVE_HIGH>;

            /* Optional reference */
            ref-supply = <&vref_2_5V>;
        };
    };
```

### Show Realistic Configurations

Don't just show minimal example, show common usage:

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
            dvdd-supply = <&vdd>;
            vio-supply = <&vdd_io>;
        };
    };

  # Example 2: With optional features
  - |
    #include <dt-bindings/gpio/gpio.h>

    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7944";
            reg = <0>;
            spi-cpha;
            spi-max-frequency = <111111111>;

            avdd-supply = <&supply_2_5V>;
            dvdd-supply = <&supply_2_5V>;
            vio-supply = <&supply_1_8V>;

            cnv-gpios = <&gpio 0 GPIO_ACTIVE_HIGH>;
            turbo-gpios = <&gpio 1 GPIO_ACTIVE_HIGH>;

            adi,always-turbo;
        };
    };
```

## Common Patterns

### Boolean Properties

Use `type: boolean` for presence/absence flags:

```yaml
properties:
  adi,external-reference:
    type: boolean
    description: Use external reference voltage instead of internal
```

No `true` or `false` needed - presence = true.

### Mutually Exclusive Properties

Use `allOf` with `if/then`:

```yaml
allOf:
  - if:
      required:
        - ref-supply
    then:
      properties:
        refin-supply: false
        adi,internal-ref: false
```

### Optional vs Required Properties

Be explicit about optionality:

```yaml
properties:
  reset-gpios:
    maxItems: 1
    description: Hardware reset GPIO (optional, can use software reset)

  avdd-supply:
    description: Analog supply voltage (required for operation)

required:
  - compatible
  - reg
  - avdd-supply
  # reset-gpios is not in required list = optional
```

### Default Values

Document defaults in description:

```yaml
properties:
  adi,oversampling-ratio:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [1, 2, 4, 8, 16, 32, 64]
    default: 1
    description:
      Oversampling ratio for noise reduction. Defaults to 1 (no oversampling).
```

Drivers must implement the default; binding just documents it.

## Validation Checklist

Before submitting binding:

- [ ] Run `make dt_binding_check` with no errors
- [ ] Run `make dtbs_check` on affected platforms
- [ ] SPDX license identifier on line 1
- [ ] Compatible strings use vendor prefix (`adi,`)
- [ ] All required properties documented
- [ ] Properties have descriptions
- [ ] Examples compile and pass validation
- [ ] Examples show realistic usage
- [ ] Use `unevaluatedProperties: false` with `$ref`
- [ ] Use `additionalProperties: false` without `$ref`
- [ ] Property names follow conventions
- [ ] Units specified in descriptions
- [ ] 2-space indentation in YAML, 4-space in DTS examples

## Platform Independence

### Avoid Platform-Specific Details

Keep device bindings platform-agnostic:

```yaml
# Good: Platform-agnostic
properties:
  reset-gpios:
    maxItems: 1
    description: Hardware reset GPIO

# Bad: Platform-specific
properties:
  reset-gpios:
    maxItems: 1
    description: Hardware reset GPIO (use Zynq GPIO 100)
```

Platform specifics go in DTS files, not in binding schema.

### Multi-Platform Support

Bindings should work across Zynq, ZynqMP, SoCFPGA, Versal, Raspberry Pi:

```yaml
# Binding supports all platforms
$ref: /schemas/spi/spi-peripheral-props.yaml#

properties:
  compatible:
    const: adi,ad7944

  reg:
    maxItems: 1

  spi-max-frequency:
    maximum: 111111111
```

Platform-specific DTS:

```dts
// Zynq
&spi0 {
    adc@0 {
        compatible = "adi,ad7944";
        reg = <0>;
        spi-max-frequency = <50000000>;
        // Zynq-specific GPIO controller
        reset-gpios = <&gpio 54 GPIO_ACTIVE_LOW>;
    };
};

// Raspberry Pi
&spi0 {
    adc@0 {
        compatible = "adi,ad7944";
        reg = <0>;
        spi-max-frequency = <50000000>;
        // RPi-specific GPIO controller
        reset-gpios = <&gpio 22 GPIO_ACTIVE_LOW>;
    };
};
```

## Common Pitfalls to Avoid

### Don't Use `|` for Descriptions

```yaml
# Wrong
description: |
  Multi-line description

# Correct
description:
  Multi-line description
```

### Don't Forget Anchors in Patterns

```yaml
# Wrong
patternProperties:
  "channel@[0-1]":  # Matches "channel@0abc"

# Correct
patternProperties:
  "^channel@[0-1]$":  # Only matches "channel@0" or "channel@1"
```

### Don't Mix additionalProperties with $ref

```yaml
# Wrong
$ref: /schemas/spi/spi-peripheral-props.yaml#
additionalProperties: false  # Blocks properties from $ref!

# Correct
$ref: /schemas/spi/spi-peripheral-props.yaml#
unevaluatedProperties: false
```

### Always Include reg-names with Multiple reg

```yaml
# If multiple reg entries
properties:
  reg:
    items:
      - description: Control registers
      - description: Data buffer

  reg-names:
    items:
      - const: ctrl
      - const: buffer
```

### Always Include clock-names with Multiple clocks

```yaml
# If multiple clocks
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

## References

- Linux Documentation: `Documentation/devicetree/bindings/writing-schema.rst`
- JSON-schema spec: https://json-schema.org/
- DT-schema repository: https://github.com/devicetree-org/dt-schema
- Kernel submission checklist: `Documentation/devicetree/bindings/submitting-patches.rst`
