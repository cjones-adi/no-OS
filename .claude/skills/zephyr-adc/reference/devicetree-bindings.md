## Devicetree Binding Pattern

### Base Binding: adc-controller.yaml

All ADC bindings include `adc-controller.yaml`:

```yaml
# From dts/bindings/adc/adc-controller.yaml
include: base.yaml

properties:
  "#io-channel-cells":
    type: int
    required: true

  "#address-cells":
    const: 1

  "#size-cells":
    const: 0

child-binding:
  description: Channel configuration

  properties:
    reg:
      type: array
      required: true
      description: Channel identifier

    zephyr,gain:
      type: string
      required: true
      enum: ["ADC_GAIN_1_6", "ADC_GAIN_1_5", ..., "ADC_GAIN_128"]

    zephyr,reference:
      type: string
      required: true
      enum: ["ADC_REF_VDD_1", "ADC_REF_INTERNAL", "ADC_REF_EXTERNAL0", ...]

    zephyr,vref-mv:
      type: int
      description: Reference voltage in millivolts

    zephyr,acquisition-time:
      type: int
      required: true
      description: Acquisition time (use ADC_ACQ_TIME macro)

    zephyr,differential:
      type: boolean
      description: Enable differential mode

    zephyr,input-positive:
      type: int
      description: Positive input (CONFIG_ADC_CONFIGURABLE_INPUTS)

    zephyr,input-negative:
      type: int
      description: Negative input (CONFIG_ADC_CONFIGURABLE_INPUTS)

    zephyr,resolution:
      type: int
      description: ADC resolution

    zephyr,oversampling:
      type: int
      description: Oversampling setting (2^N samples averaged)
```

### Device-Specific Binding Example: AD4130

From **dts/bindings/adc/adi,ad4130-adc.yaml**:

```yaml
description: |
  Bindings for the ADI AD4130 Analog-to-Digital Converter.

  Sample usage:
  &spi0 {
      ad4130: ad4130@0 {
          compatible = "adi,ad4130-adc";
          reg = <0x0>;
          spi-max-frequency = <2700000>;
          #address-cells = <1>;
          #size-cells = <0>;
          #io-channel-cells = <1>;

          channel@1 {
              reg = <1>;
              zephyr,gain = "ADC_GAIN_1";
              zephyr,reference = "ADC_REF_INTERNAL";
              zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
              zephyr,resolution = <24>;
              zephyr,input-positive = <AD4130_ADC_AIN8>;
              zephyr,input-negative = <AD4130_ADC_AIN9>;
          };
      };
  };

compatible: "adi,ad4130-adc"

include: [adc-controller.yaml, spi-device.yaml]

properties:
  bipolar:
    type: boolean
    description: Bipolar configuration for AD4130

  internal-reference-value:
    type: int
    enum: [0, 1]
    default: 0
    description: |
      Internal reference value selection:
      - 0: AD4130_INTREF_2_5V
      - 1: AD4130_INTREF_1_25V

  adc-mode:
    type: int
    enum: [0, 1, 2, 3, 4]
    default: 0
    description: |
      ADC operating mode:
      - 0: AD4130_CONTINUOUS
      - 1: AD4130_SINGLE
      - 2: AD4130_STANDBY
      - 3: AD4130_POWER_DOWN
      - 4: AD4130_IDLE

  clock-type:
    type: int
    enum: [0, 1, 2, 3]
    default: 0
    description: |
      Clock selection:
      - 0: AD4130_INT_76_8_KHZ_OUT_OFF
      - 1: AD4130_INT_76_8_KHZ_OUT_ON
      - 2: AD4130_EXT_76_8KHZ
      - 3: AD4130_EXT_153_6_KHZ_DIV_2

  "#io-channel-cells":
    const: 1

io-channel-cells:
  - input
```

### Simpler Binding Example: AD4114

From **dts/bindings/adc/adi,ad4114-adc.yaml**:

```yaml
include: [adc-controller.yaml, spi-device.yaml]

compatible: "adi,ad4114-adc"

description: Binding for the ADI AD4114 ADC

properties:
  map-inputs:
    type: array
    required: true
    description: |
      Array of 16 values corresponding to CHANNEL REGISTER 0 TO CHANNEL REGISTER 15.
      Each value configures the input multiplexer and setup selection for that channel.
```

