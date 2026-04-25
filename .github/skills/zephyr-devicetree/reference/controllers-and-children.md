## Controller Bindings with Cell Specifiers

Devices that provide resources to other devices use **cell specifiers**.

### Pattern: GPIO Controller

**Binding** (`gpio-controller.yaml`):

```yaml
properties:
  gpio-controller:
    type: boolean
    required: true

  "#gpio-cells":
    type: int
    required: true
```

**Devicetree** (provider):
```dts
gpio0: gpio@40000000 {
    compatible = "vendor,gpio";
    gpio-controller;
    #gpio-cells = <2>;  /* pin, flags */
    reg = <0x40000000 0x1000>;
};
```

**Devicetree** (consumer):
```dts
device {
    reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;
    /*              ^      ^  ^
                    |      |  +-- flags (cell 2)
                    |      +----- pin number (cell 1)
                    +------------ phandle to gpio0
    */
};
```

### Pattern: ADC Controller

**Binding** (`adc-controller.yaml`):

```yaml
properties:
  "#io-channel-cells":
    type: int
    required: true

io-channel-cells:
  - input
```

**Devicetree** (provider):
```dts
adc0: adc@40000000 {
    compatible = "vendor,adc";
    #io-channel-cells = <1>;  /* channel ID */
    reg = <0x40000000 0x1000>;
};
```

**Devicetree** (consumer):
```dts
sensor {
    io-channels = <&adc0 5>;
    /*              ^    ^
                    |    +-- channel ID (cell 1)
                    +------- phandle to adc0
    */
};
```

### Pattern: DAC Controller

**Binding** (`dac-controller.yaml`):

```yaml
properties:
  "#io-channel-cells":
    type: int

io-channel-cells:
  - output
```

**Devicetree** (DAC with channels):
```dts
dac0: dac@50000000 {
    compatible = "vendor,dac";
    #io-channel-cells = <1>;  /* channel/output ID */
    reg = <0x50000000 0x1000>;
};
```

## Child Bindings

Child bindings define sub-nodes within a devicetree node. Common for ADCs with channels, PMICs with regulators, etc.

### Pattern: ADC with Channels

**Binding** (`adi,ad4130-adc.yaml`):

```yaml
compatible: "adi,ad4130-adc"

include: [adc-controller.yaml, spi-device.yaml]

properties:
  "#io-channel-cells":
    const: 1
  "#address-cells":
    const: 1
  "#size-cells":
    const: 0

child-binding:
  description: ADC channel configuration

  properties:
    reg:
      type: array
      required: true
      description: Channel identifier

    zephyr,gain:
      type: string
      required: true
      enum:
        - "ADC_GAIN_1"
        - "ADC_GAIN_2"

    zephyr,reference:
      type: string
      required: true
      enum:
        - "ADC_REF_INTERNAL"
        - "ADC_REF_EXTERNAL0"
```

**Devicetree usage**:
```dts
&spi0 {
    ad4130@0 {
        compatible = "adi,ad4130-adc";
        reg = <0>;
        spi-max-frequency = <2700000>;

        #address-cells = <1>;
        #size-cells = <0>;
        #io-channel-cells = <1>;

        channel@1 {
            reg = <1>;
            zephyr,gain = "ADC_GAIN_1";
            zephyr,reference = "ADC_REF_INTERNAL";
            zephyr,resolution = <24>;
        };

        channel@2 {
            reg = <2>;
            zephyr,gain = "ADC_GAIN_2";
            zephyr,reference = "ADC_REF_EXTERNAL0";
            zephyr,resolution = <24>;
        };
    };
};
```

### Pattern: MFD with Child Devices

Multi-Function Devices (MFDs) have multiple child devices (DAC, ADC, GPIO, etc.).

**Binding** (`adi,ad559x-common.yaml`):

```yaml
description: Analog AD559x ADC/DAC/GPIO chip common properties

properties:
  reset-gpios:
    type: phandle-array
    description: RESET pin
```

**Binding** (`adi,ad559x-i2c.yaml`):

```yaml
description: Analog AD559x ADC/DAC/GPIO chip via I2C bus

compatible: "adi,ad559x"

include: [i2c-device.yaml, "adi,ad559x-common.yaml"]
```

**Devicetree usage** (MFD parent with children):

```dts
&i2c0 {
    ad559x: ad559x@8 {
        compatible = "adi,ad559x";
        reg = <0x08>;
        reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;

        ad559x_dac: dac {
            compatible = "adi,ad559x-dac";
            #io-channel-cells = <1>;
        };

        ad559x_adc: adc {
            compatible = "adi,ad559x-adc";
            #io-channel-cells = <1>;
        };

        ad559x_gpio: gpio {
            compatible = "adi,ad559x-gpio";
            gpio-controller;
            #gpio-cells = <2>;
            ngpios = <8>;
        };
    };
};
```

**Child DAC binding** (`adi,ad559x-dac.yaml`):

```yaml
description: Analog AD559x DAC child device

compatible: "adi,ad559x-dac"

include: dac-controller.yaml

properties:
  "#io-channel-cells":
    const: 1
```

**Child GPIO binding** (`adi,ad559x-gpio.yaml`):

```yaml
description: Analog AD559x GPIO child device

compatible: "adi,ad559x-gpio"

include: gpio-controller.yaml
```

