## Common Binding Patterns

### Pattern 1: Include Common Base Binding

**Use case**: Multiple device variants share common properties.

**Base binding** (`adi,ad569x-base.yaml`):
```yaml
include: [dac-controller.yaml]

properties:
  voltage-reference:
    type: string
    enum: ["internal", "external"]

  gain:
    type: string
    enum: ["gain-1", "gain-2"]
```

**Variant bindings**:

`adi,ad5691.yaml`:
```yaml
description: Driver for AD5691 (12-bit) DAC.
compatible: "adi,ad5691"
include: adi,ad569x-base.yaml
```

`adi,ad5693.yaml`:
```yaml
description: Driver for AD5693 (16-bit) DAC.
compatible: "adi,ad5693"
include: adi,ad569x-base.yaml
```

### Pattern 2: Bus-Specific Variants

**Use case**: Same device supports I2C and SPI buses.

**Common properties** (`adi,ad559x-common.yaml`):
```yaml
properties:
  reset-gpios:
    type: phandle-array
    description: RESET pin
```

**I2C variant** (`adi,ad559x-i2c.yaml`):
```yaml
compatible: "adi,ad559x"
include: [i2c-device.yaml, "adi,ad559x-common.yaml"]
```

**SPI variant** (`adi,ad559x-spi.yaml`):
```yaml
compatible: "adi,ad559x"
include: [spi-device.yaml, "adi,ad559x-common.yaml"]
```

### Pattern 3: GPIO Interrupt Pins

**Use case**: Device has interrupt outputs.

```yaml
properties:
  int1-gpios:
    type: phandle-array
    description: |
      Interrupt 1 pin. Defaults to active high as produced by sensor.

  int2-gpios:
    type: phandle-array
    description: |
      Interrupt 2 pin. Defaults to active high as produced by sensor.
```

**Devicetree usage**:
```dts
sensor {
    compatible = "vendor,sensor";
    int1-gpios = <&gpio0 5 GPIO_ACTIVE_HIGH>;
    int2-gpios = <&gpio0 6 GPIO_ACTIVE_HIGH>;
};
```

### Pattern 4: Optional Enable/Reset GPIOs

**Use case**: Device has enable or reset control pins.

```yaml
properties:
  enable-gpios:
    type: phandle-array
    description: Enable GPIO pin

  reset-gpios:
    type: phandle-array
    description: Reset GPIO pin (active low)
```

**Devicetree usage**:
```dts
device {
    compatible = "vendor,chip";
    enable-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
    reset-gpios = <&gpio0 11 GPIO_ACTIVE_LOW>;
};
```

### Pattern 5: Voltage/Current Ranges

**Use case**: Regulators or power devices with voltage/current limits.

```yaml
properties:
  regulator-min-microvolt:
    type: int
    description: Minimum voltage in microvolts

  regulator-max-microvolt:
    type: int
    description: Maximum voltage in microvolts

  regulator-min-microamp:
    type: int
    description: Minimum current in microamps

  regulator-max-microamp:
    type: int
    description: Maximum current in microamps

  regulator-always-on:
    type: boolean
    description: Regulator should never be disabled
```

### Pattern 6: Operating Modes

**Use case**: Devices with multiple operating modes.

```yaml
properties:
  operating-mode:
    type: int
    default: 0
    enum:
      - 0  # MODE_NORMAL
      - 1  # MODE_LOW_POWER
      - 2  # MODE_HIGH_SPEED
    description: |
      Device operating mode:
      - 0: Normal mode (default)
      - 1: Low power mode
      - 2: High speed mode
```

