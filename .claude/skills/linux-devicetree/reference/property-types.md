# Property Types and Constraints

Complete reference for devicetree property types using JSON-schema.

## Core Property Types

Reference types from `/schemas/types.yaml`:

### Boolean Properties

Presence = true, absence = false. No value needed in DTS.

```yaml
properties:
  adi,external-reference:
    type: boolean
    description: Use external reference voltage
```

**In DTS:**
```dts
adc@0 {
    adi,external-reference;  // Property present = true
};

adc@1 {
    // Property absent = false
};
```

### String Properties

```yaml
properties:
  adi,spi-mode:
    $ref: /schemas/types.yaml#/definitions/string
    enum: [single, chain]
    description: SPI wiring configuration
```

**In DTS:**
```dts
dac@0 {
    adi,spi-mode = "chain";
};
```

**String with constraints:**
```yaml
properties:
  clock-output-names:
    $ref: /schemas/types.yaml#/definitions/string
    description: Clock output name
    pattern: "^clk[0-9]+$"  // Must match pattern
```

### Unsigned 32-bit Integer (uint32)

```yaml
properties:
  adi,sdo-drive-strength:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [0, 1, 2, 3]
    description: SDO drive strength level (0-3)

  adi,sample-rate:
    $ref: /schemas/types.yaml#/definitions/uint32
    minimum: 1000
    maximum: 1000000
    description: Sample rate in Hz
```

**In DTS:**
```dts
adc@0 {
    adi,sdo-drive-strength = <2>;
    adi,sample-rate = <250000>;
};
```

### Signed 32-bit Integer (int32)

```yaml
properties:
  adi,gain-offset:
    $ref: /schemas/types.yaml#/definitions/int32
    minimum: -511
    maximum: 511
    description: Gain calibration offset
```

**In DTS:**
```dts
adc@0 {
    adi,gain-offset = <-25>;
};
```

### Unsigned 64-bit Integer (uint64)

```yaml
properties:
  adi,frequency-hz:
    $ref: /schemas/types.yaml#/definitions/uint64
    minimum: 1000000000
    maximum: 6000000000
    description: Frequency in Hz (1-6 GHz)
```

**In DTS:**
```dts
synthesizer@0 {
    adi,frequency-hz = /bits/ 64 <4000000000>;
};
```

## Array Properties

### Integer Array (Fixed Size)

```yaml
properties:
  adi,output-range-microvolt:
    description: Voltage output range as <min, max>
    items:
      - description: Minimum voltage
        minimum: -10000000
      - description: Maximum voltage
        maximum: 10000000
```

**In DTS:**
```dts
dac@0 {
    adi,output-range-microvolt = <0 5000000>;  // 0V to 5V
};
```

### Integer Array (Variable Size)

```yaml
properties:
  adi,gain-values:
    $ref: /schemas/types.yaml#/definitions/uint32-array
    minItems: 1
    maxItems: 8
    description: Array of gain calibration values
```

**In DTS:**
```dts
adc@0 {
    adi,gain-values = <100 200 300 400>;
};
```

### Array with Enum Choices (oneOf)

```yaml
properties:
  adi,output-range-microvolt:
    description: Voltage output range as <min, max>
    oneOf:
      - items:
          - const: 0
          - enum: [2500000, 5000000, 10000000]
      - items:
          - const: -5000000
          - const: 5000000
      - items:
          - const: -10000000
          - const: 10000000
```

**In DTS:**
```dts
dac@0 {
    adi,output-range-microvolt = <0 5000000>;     // Valid
};

dac@1 {
    adi,output-range-microvolt = <-5000000 5000000>;  // Valid
};

dac@2 {
    adi,output-range-microvolt = <0 3000000>;     // Invalid
};
```

### String Array

```yaml
properties:
  clock-output-names:
    items:
      - const: clk_out0
      - const: clk_out1
      - const: clk_out2
```

**In DTS:**
```dts
clock-gen {
    clock-output-names = "clk_out0", "clk_out1", "clk_out2";
};
```

## Phandle Properties

### Simple Phandle (Reference)

```yaml
properties:
  vref-supply:
    description: External reference voltage regulator
```

**In DTS:**
```dts
vref_ext: regulator@0 {
    regulator-name = "vref-2.5V";
    // ...
};

adc@0 {
    vref-supply = <&vref_ext>;
};
```

### Phandle with Arguments

```yaml
properties:
  clocks:
    maxItems: 1
    description: Master clock input

  clock-names:
    const: mclk
```

**In DTS:**
```dts
clkgen: clock-generator {
    #clock-cells = <1>;  // Takes 1 argument (clock index)
};

adc@0 {
    clocks = <&clkgen 0>;  // Reference clkgen, clock 0
    clock-names = "mclk";
};
```

### Multiple Phandles

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

**In DTS:**
```dts
adc@0 {
    clocks = <&clk_master>, <&clk_sample>;
    clock-names = "mclk", "sclk";
};
```

### Phandle Array

```yaml
properties:
  io-backends:
    description: IIO backend controllers
    maxItems: 2
```

**In DTS:**
```dts
adc@0 {
    io-backends = <&axi_adc_0>, <&axi_adc_1>;
};
```

## GPIO Properties

GPIO properties use `-gpios` suffix:

```yaml
properties:
  reset-gpios:
    maxItems: 1
    description: GPIO connected to RESET pin (active low)

  cnv-gpios:
    maxItems: 1
    description: Convert input GPIO (active high)

  range-gpios:
    minItems: 1
    maxItems: 3
    description: Range select GPIOs
```

**In DTS:**
```dts
#include <dt-bindings/gpio/gpio.h>

adc@0 {
    reset-gpios = <&gpio 10 GPIO_ACTIVE_LOW>;
    cnv-gpios = <&gpio 11 GPIO_ACTIVE_HIGH>;
    range-gpios = <&gpio 20 GPIO_ACTIVE_HIGH>,
                  <&gpio 21 GPIO_ACTIVE_HIGH>,
                  <&gpio 22 GPIO_ACTIVE_HIGH>;
};
```

**GPIO Flags:**
- `GPIO_ACTIVE_HIGH` (0): Active high
- `GPIO_ACTIVE_LOW` (1): Active low (inverted)
- `GPIO_OPEN_DRAIN` (2): Open-drain output
- `GPIO_OPEN_SOURCE` (4): Open-source output
- `GPIO_PULL_UP` (8): Enable pull-up
- `GPIO_PULL_DOWN` (16): Enable pull-down

## Supply Properties

Regulator/supply properties use `-supply` suffix:

```yaml
properties:
  avdd-supply:
    description: 2.5V analog supply

  dvdd-supply:
    description: 2.5V digital supply

  vio-supply:
    description: 1.8V to 2.7V I/O supply

  vref-supply:
    description: External reference voltage (optional)

required:
  - avdd-supply
  - dvdd-supply
  - vio-supply
  # vref-supply is optional
```

**In DTS:**
```dts
regulators {
    vdd_2_5: regulator-2v5 {
        compatible = "regulator-fixed";
        regulator-name = "2.5V";
        regulator-min-microvolt = <2500000>;
        regulator-max-microvolt = <2500000>;
    };
};

adc@0 {
    avdd-supply = <&vdd_2_5>;
    dvdd-supply = <&vdd_2_5>;
    vio-supply = <&vdd_1_8>;
};
```

## Constraints and Validation

### Enum (Fixed Choices)

```yaml
properties:
  adi,reference-voltage:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [2500000, 4096000, 5000000]
    description: Internal reference voltage in microvolts
```

### Minimum/Maximum

```yaml
properties:
  spi-max-frequency:
    maximum: 111111111  // 111.111 MHz

  adi,sample-rate:
    $ref: /schemas/types.yaml#/definitions/uint32
    minimum: 1000
    maximum: 1000000
    description: Sample rate in Hz
```

### Multiple Of

```yaml
properties:
  adi,clock-divider:
    $ref: /schemas/types.yaml#/definitions/uint32
    multipleOf: 2
    minimum: 2
    maximum: 512
    description: Clock divider (must be even)
```

### Pattern (Regex)

```yaml
properties:
  label:
    $ref: /schemas/types.yaml#/definitions/string
    pattern: "^adc[0-9]+$"
    description: Device label (adc0, adc1, etc.)
```

### Default Value

```yaml
properties:
  adi,oversampling-ratio:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [1, 2, 4, 8, 16, 32, 64]
    default: 1
    description: Oversampling ratio (default 1 = no oversampling)
```

**Note:** Defaults are informational; drivers should implement the default behavior.

## Complex Combinations

### oneOf (Exactly One Match)

```yaml
properties:
  adi,reference-source:
    oneOf:
      - description: Internal 2.5V reference
        properties:
          adi,internal-ref:
            type: boolean
      - description: External reference via REFIN pin
        properties:
          refin-supply: true
```

### anyOf (At Least One Match)

```yaml
# At least one of these must be present
anyOf:
  - required: [vref-supply]
  - required: [adi,internal-reference]
```

### allOf (All Must Match)

Used for combining constraints:

```yaml
allOf:
  - $ref: /schemas/spi/spi-peripheral-props.yaml#
  - if:
      properties:
        compatible:
          const: adi,ad7606-16
    then:
      properties:
        adi,oversampling-ratio:
          enum: [1, 2, 4, 8, 16, 32, 64]
```

## Special Types

### #address-cells and #size-cells

For parent nodes with children:

```yaml
properties:
  '#address-cells':
    const: 1

  '#size-cells':
    const: 0
```

**In DTS:**
```dts
dac@0 {
    #address-cells = <1>;
    #size-cells = <0>;

    channel@0 {
        reg = <0>;  // Address is 1 cell, size is 0 cells
    };
};
```

### #clock-cells, #gpio-cells, etc.

Provider cells for phandle arguments:

```yaml
properties:
  '#clock-cells':
    const: 1
    description: Clock specifier is clock index

  '#gpio-cells':
    const: 2
    description: GPIO specifier is <gpio_number flags>
```

### interrupts

```yaml
properties:
  interrupts:
    maxItems: 1
    description: Data ready interrupt

  interrupt-names:
    const: drdy
```

**In DTS:**
```dts
#include <dt-bindings/interrupt-controller/irq.h>

adc@0 {
    interrupts = <0 57 IRQ_TYPE_LEVEL_HIGH>;
    interrupt-names = "drdy";
};
```

## Deprecated Properties

Mark old properties as deprecated:

```yaml
properties:
  adi,old-property:
    deprecated: true
    description: Deprecated; use adi,new-property instead

  adi,new-property:
    $ref: /schemas/types.yaml#/definitions/uint32
    description: Replacement for adi,old-property
```
