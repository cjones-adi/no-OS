# Bus-Specific Devicetree Bindings

Complete guide to creating devicetree bindings for SPI, I2C, and platform (MMIO) devices.

## SPI Device Bindings

SPI devices must reference `/schemas/spi/spi-peripheral-props.yaml`.

### Basic SPI Binding

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/iio/adc/adi,ad7944.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Analog Devices AD7944 18-bit PulSAR ADC

maintainers:
  - Michael Hennerich <Michael.Hennerich@analog.com>

$ref: /schemas/spi/spi-peripheral-props.yaml#

properties:
  compatible:
    enum:
      - adi,ad7944
      - adi,ad7985
      - adi,ad7986

  reg:
    maxItems: 1

  spi-max-frequency:
    maximum: 111111111  # 111.111 MHz

  spi-cpol: true  # Clock polarity (idle high)
  spi-cpha: true  # Clock phase (sample on trailing edge)

  # Power supplies
  avdd-supply:
    description: 2.5V analog supply

  dvdd-supply:
    description: 2.5V digital supply

  vio-supply:
    description: 1.8V to 2.7V I/O supply

  # GPIOs
  cnv-gpios:
    maxItems: 1
    description: Convert input GPIO (triggers conversion)

  turbo-gpios:
    maxItems: 1
    description: Turbo mode GPIO

  # Vendor-specific properties
  adi,always-turbo:
    type: boolean
    description: Keep turbo mode permanently enabled

required:
  - compatible
  - reg
  - avdd-supply
  - dvdd-supply
  - vio-supply

unevaluatedProperties: false

examples:
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
        };
    };
```

### Key SPI Properties

| Property | Type | Description |
|----------|------|-------------|
| `reg` | uint32 | Chip select number (0, 1, 2, ...) |
| `spi-max-frequency` | uint32 | Maximum SPI clock frequency in Hz |
| `spi-cpol` | boolean | Clock polarity: idle high if present |
| `spi-cpha` | boolean | Clock phase: sample on trailing edge if present |
| `spi-cs-high` | boolean | Chip select active high (default is active low) |
| `spi-3wire` | boolean | 3-wire mode (MOSI/MISO shared) |
| `spi-lsb-first` | boolean | LSB-first bit order (default is MSB-first) |
| `spi-tx-bus-width` | uint32 | Transmit bus width (1, 2, 4, 8 for SPI modes) |
| `spi-rx-bus-width` | uint32 | Receive bus width (1, 2, 4, 8 for SPI modes) |

### SPI Modes

```yaml
# Mode 0: CPOL=0, CPHA=0 (default)
adc@0 {
    reg = <0>;
    spi-max-frequency = <50000000>;
};

# Mode 1: CPOL=0, CPHA=1
adc@0 {
    reg = <0>;
    spi-cpha;
    spi-max-frequency = <50000000>;
};

# Mode 2: CPOL=1, CPHA=0
adc@0 {
    reg = <0>;
    spi-cpol;
    spi-max-frequency = <50000000>;
};

# Mode 3: CPOL=1, CPHA=1
adc@0 {
    reg = <0>;
    spi-cpol;
    spi-cpha;
    spi-max-frequency = <50000000>;
};
```

### SPI with Interrupts

```yaml
properties:
  interrupts:
    maxItems: 1
    description: Data ready interrupt

examples:
  - |
    #include <dt-bindings/interrupt-controller/irq.h>

    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7768-1";
            reg = <0>;
            spi-max-frequency = <25000000>;

            interrupts = <25 IRQ_TYPE_EDGE_RISING>;

            avdd-supply = <&vdd>;
            reset-gpios = <&gpio 22 GPIO_ACTIVE_LOW>;
        };
    };
```

## I2C Device Bindings

I2C devices must reference `/schemas/i2c/i2c-device.yaml`.

### Basic I2C Binding

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/hwmon/adi,ltc2991.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Analog Devices LTC2991 Octal I2C Voltage, Current, and Temperature Monitor

maintainers:
  - Antoniu Miclaus <antoniu.miclaus@analog.com>

$ref: /schemas/i2c/i2c-device.yaml#

properties:
  compatible:
    const: adi,ltc2991

  reg:
    maxItems: 1

  vcc-supply:
    description: Main power supply

required:
  - compatible
  - reg
  - vcc-supply

additionalProperties: false

examples:
  - |
    i2c {
        #address-cells = <1>;
        #size-cells = <0>;

        hwmon@48 {
            compatible = "adi,ltc2991";
            reg = <0x48>;
            vcc-supply = <&vcc>;
        };
    };
```

### Key I2C Properties

| Property | Type | Description |
|----------|------|-------------|
| `reg` | uint32 | I2C slave address (7-bit: 0x00-0x7F) |
| `interrupts` | phandle | Interrupt line |
| `wakeup-source` | boolean | Device can wake system from sleep |

### I2C Addressing

```yaml
# 7-bit addressing (standard)
properties:
  reg:
    maxItems: 1
    description: I2C slave address

# 10-bit addressing (rare)
properties:
  reg:
    maxItems: 1
    description: I2C 10-bit slave address
```

**In DTS:**
```dts
i2c {
    // 7-bit address: 0x48
    sensor@48 {
        compatible = "adi,ltc2991";
        reg = <0x48>;
    };

    // 10-bit address: 0x350 (use I2C_TEN_BIT_ADDRESS flag in driver)
    sensor@350 {
        compatible = "vendor,device";
        reg = <0x350>;
    };
};
```

### I2C with Child Nodes

For devices with channels or sub-devices:

```yaml
properties:
  compatible:
    const: adi,ltc2991

  reg:
    maxItems: 1

  '#address-cells':
    const: 1

  '#size-cells':
    const: 0

patternProperties:
  "^channel@[0-3]$":
    type: object
    description: Measurement channels

    properties:
      reg:
        description: Channel number
        enum: [0, 1, 2, 3]

      shunt-resistor-micro-ohms:
        description: Current sense resistor value

      adi,temperature-enable:
        type: boolean
        description: Enable temperature measurement mode

    required:
      - reg

required:
  - compatible
  - reg
  - vcc-supply

additionalProperties: false

examples:
  - |
    i2c {
        #address-cells = <1>;
        #size-cells = <0>;

        hwmon@48 {
            compatible = "adi,ltc2991";
            reg = <0x48>;
            vcc-supply = <&vcc>;

            #address-cells = <1>;
            #size-cells = <0>;

            channel@0 {
                reg = <0>;
                shunt-resistor-micro-ohms = <100000>;
            };

            channel@2 {
                reg = <2>;
                adi,temperature-enable;
            };
        };
    };
```

## Platform Device Bindings (MMIO)

Platform devices are memory-mapped and don't reference a bus schema.

### Basic Platform Binding

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/dma/adi,axi-dmac.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Analog Devices AXI-DMAC DMA Controller

maintainers:
  - Lars-Peter Clausen <lars@metafoo.de>

properties:
  compatible:
    enum:
      - adi,axi-dmac-1.00.a

  reg:
    maxItems: 1
    description: Memory-mapped register base address and size

  interrupts:
    maxItems: 1
    description: DMA transfer complete interrupt

  clocks:
    maxItems: 1
    description: AXI bus clock

  clock-names:
    const: s_axi_aclk

  '#dma-cells':
    const: 1
    description: DMA channel specifier

  dma-channels:
    description: Number of DMA channels
    minimum: 1
    maximum: 16

required:
  - compatible
  - reg
  - interrupts
  - clocks

additionalProperties: false

examples:
  - |
    #include <dt-bindings/interrupt-controller/irq.h>

    axi_dmac@44a30000 {
        compatible = "adi,axi-dmac-1.00.a";
        reg = <0x44a30000 0x1000>;
        interrupts = <0 57 IRQ_TYPE_LEVEL_HIGH>;
        clocks = <&clkc 15>;
        clock-names = "s_axi_aclk";

        #dma-cells = <1>;
        dma-channels = <1>;
    };
```

### Platform Device Address Ranges

```yaml
# Single register block
properties:
  reg:
    maxItems: 1

# Multiple register blocks
properties:
  reg:
    items:
      - description: Control registers
      - description: Data buffer
      - description: DMA registers

  reg-names:
    items:
      - const: ctrl
      - const: buffer
      - const: dma
```

**In DTS:**
```dts
device@40000000 {
    reg = <0x40000000 0x1000>,    // Control registers
          <0x40001000 0x4000>,    // Data buffer
          <0x40010000 0x1000>;    // DMA registers
    reg-names = "ctrl", "buffer", "dma";
};
```

## Supply and GPIO Properties

### Supply Properties

Use for regulators/power supplies:

```yaml
properties:
  avdd-supply:
    description: Analog supply voltage (2.5V)

  dvdd-supply:
    description: Digital supply voltage (2.5V)

  vio-supply:
    description: I/O supply voltage (1.8V to 2.7V)

  vref-supply:
    description: External reference voltage (optional)
```

**Naming Convention:**
- Use datasheet pin names when possible
- Convert to lowercase: `AVDD` → `avdd-supply`
- Add `-supply` suffix

### GPIO Properties

Use for GPIO connections:

```yaml
properties:
  reset-gpios:
    maxItems: 1
    description: GPIO connected to RESET pin (active low)

  cnv-gpios:
    maxItems: 1
    description: Convert input GPIO (active high)

  ldac-gpios:
    maxItems: 1
    description: LDAC pin for hardware trigger

  range-gpios:
    minItems: 1
    maxItems: 3
    description: Range select GPIOs (up to 3 pins)
```

**In DTS:**
```dts
#include <dt-bindings/gpio/gpio.h>

device@0 {
    reset-gpios = <&gpio 10 GPIO_ACTIVE_LOW>;
    cnv-gpios = <&gpio 11 GPIO_ACTIVE_HIGH>;
    ldac-gpios = <&gpio 12 GPIO_ACTIVE_HIGH>;
    range-gpios = <&gpio 20 GPIO_ACTIVE_HIGH>,
                  <&gpio 21 GPIO_ACTIVE_HIGH>,
                  <&gpio 22 GPIO_ACTIVE_HIGH>;
};
```

## Clock Properties

### Single Clock

```yaml
properties:
  clocks:
    maxItems: 1
    description: Master clock input

  clock-names:
    const: mclk
```

### Multiple Clocks

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

### Optional Clocks

```yaml
properties:
  clocks:
    minItems: 1
    maxItems: 2
    description: Required master clock, optional sample clock

  clock-names:
    minItems: 1
    items:
      - const: mclk
      - const: sclk  # Optional
```

**In DTS:**
```dts
// Single clock
device@0 {
    clocks = <&clk_master>;
    clock-names = "mclk";
};

// Multiple clocks
device@1 {
    clocks = <&clk_master>, <&clk_sample>;
    clock-names = "mclk", "sclk";
};

// With clock arguments
device@2 {
    clocks = <&clkgen 0>, <&clkgen 1>;  // Clock index argument
    clock-names = "mclk", "sclk";
};
```

## IIO Backend Property (ADI-Specific)

For IIO devices using the backend framework:

```yaml
properties:
  io-backends:
    description:
      IIO backend reference. Device can be optionally connected to an
      FPGA-based backend controller (e.g., axi-ad3552r for high-speed QSPI+DDR).
    maxItems: 1
```

**In DTS:**
```dts
axi_ad3552r: axi-ad3552r@44a70000 {
    compatible = "adi,axi-ad3552r";
    reg = <0x44a70000 0x1000>;
    clocks = <&clkc 15>;

    #io-backend-cells = <0>;
};

&spi0 {
    dac@0 {
        compatible = "adi,ad3552r";
        reg = <0>;
        spi-max-frequency = <30000000>;

        io-backends = <&axi_ad3552r>;

        reset-gpios = <&gpio 22 GPIO_ACTIVE_LOW>;
        ldac-gpios = <&gpio 21 GPIO_ACTIVE_HIGH>;
    };
};
```

This connects a physical SPI DAC to an FPGA IP core that provides high-speed buffered access.

## Complete Examples

### SPI ADC with FPGA Integration

```yaml
# Binding
$ref: /schemas/spi/spi-peripheral-props.yaml#

properties:
  compatible:
    const: adi,ad9467

  reg:
    maxItems: 1

  spi-max-frequency:
    maximum: 25000000

  clocks:
    maxItems: 1
    description: ADC sampling clock

  clock-names:
    const: adc-clk

  io-backends:
    maxItems: 1

  reset-gpios:
    maxItems: 1

required:
  - compatible
  - reg
  - clocks
  - io-backends

unevaluatedProperties: false

examples:
  - |
    #include <dt-bindings/gpio/gpio.h>

    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad9467";
            reg = <0>;
            spi-max-frequency = <10000000>;

            clocks = <&axi_ad9467_clkgen>;
            clock-names = "adc-clk";

            io-backends = <&axi_ad9467>;

            reset-gpios = <&gpio 100 GPIO_ACTIVE_LOW>;
        };
    };
```

### I2C Multi-Channel Monitor

```yaml
# Binding with child channel nodes
$ref: /schemas/i2c/i2c-device.yaml#

properties:
  compatible:
    const: adi,ltc2991

  reg:
    maxItems: 1

  vcc-supply: true

  '#address-cells':
    const: 1

  '#size-cells':
    const: 0

patternProperties:
  "^channel@[0-3]$":
    type: object

    properties:
      reg:
        enum: [0, 1, 2, 3]

      shunt-resistor-micro-ohms:
        description: Shunt resistor value

      adi,temperature-enable:
        type: boolean

    required:
      - reg

required:
  - compatible
  - reg
  - vcc-supply

additionalProperties: false

examples:
  - |
    i2c {
        #address-cells = <1>;
        #size-cells = <0>;

        monitor@48 {
            compatible = "adi,ltc2991";
            reg = <0x48>;
            vcc-supply = <&reg_3v3>;

            #address-cells = <1>;
            #size-cells = <0>;

            channel@0 {
                reg = <0>;
                shunt-resistor-micro-ohms = <10000>;
            };

            channel@1 {
                reg = <1>;
                shunt-resistor-micro-ohms = <10000>;
            };

            channel@2 {
                reg = <2>;
                adi,temperature-enable;
            };
        };
    };
```
