## Complete Binding Examples

### Example 1: Simple I2C Sensor

**File**: `dts/bindings/sensor/adi,adxl345.yaml`

```yaml
# Copyright (c) 2024 Analog Devices Inc.
# SPDX-License-Identifier: Apache-2.0

description: |
  ADXL345 3-axis accelerometer.
  When setting the accelerometer DTS properties, make sure to include
  adxl345.h and use the macros defined there.

compatible: "adi,adxl345"

include: [i2c-device.yaml, sensor-device.yaml]

properties:
  range:
    type: int
    default: 2
    description: |
      Accelerometer range.
    enum:
      - 0 # ADXL345_DT_RANGE_2G
      - 1 # ADXL345_DT_RANGE_4G
      - 2 # ADXL345_DT_RANGE_8G
      - 3 # ADXL345_DT_RANGE_16G

  odr:
    type: int
    default: 10
    description: |
      Accelerometer sampling frequency (ODR). Default is power on reset value.
    enum:
      - 7  # ADXL345_DT_ODR_12_5
      - 8  # ADXL345_DT_ODR_25
      - 10 # ADXL345_DT_ODR_100

  int1-gpios:
    type: phandle-array
    description: |
      The INT1 signal defaults to active high as produced by the
      sensor. The property value should ensure the flags properly
      describe the signal that is presented to the driver.
```

### Example 2: SPI ADC with Channels

**File**: `dts/bindings/adc/adi,ad4130-adc.yaml`

```yaml
# Copyright (c) 2025 Analog Devices, Inc.
# SPDX-License-Identifier: Apache-2.0

description: |
  Bindings for the ADI AD4130 Analog-to-Digital Converter.

  This device is controlled over SPI and exposes one or more ADC input channels.
  Each child node corresponds to a channel and supports standard ADC properties
  such as gain, reference, resolution, and input configuration.

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
      ADC operating mode for AD4130:
      - 0: AD4130_CONTINUOUS
      - 1: AD4130_SINGLE
      - 2: AD4130_STANDBY
      - 3: AD4130_POWER_DOWN
      - 4: AD4130_IDLE

  "#io-channel-cells":
    const: 1

  spi-cs-setup-delay-ns:
    default: 1000

  spi-cs-hold-delay-ns:
    default: 1000

io-channel-cells:
  - input
```

### Example 3: I2C DAC with Voltage Reference

**File**: `dts/bindings/dac/adi,ad569x-base.yaml`

```yaml
# Copyright (c) 2024 Jan Kubiznak <jan.kubiznak@deveritec.com>
# SPDX-License-Identifier: Apache-2.0

include: [dac-controller.yaml]

properties:
  "#io-channel-cells":
    const: 1

  voltage-reference:
    type: string
    default: "internal"
    enum:
      - "internal"
      - "external"
    description: |
      DAC voltage reference select.
      - Internal voltage reference - 2.5V (reg: 0).
      - External voltage reference (reg: 1).
      The default corresponds to the reset value of the register field.

  gain:
    type: string
    default: "gain-1"
    enum:
      - "gain-1"
      - "gain-2"
    description: |
      Gain selection bit.
      - Gain of 1 (reg: 0).
      - Gain of 2 (reg: 1).
      The default corresponds to the reset value of the register field.

  power-down-mode:
    type: string
    default: "normal"
    enum:
      - "normal"
      - "power-down-1k"
      - "power-down-100k"
      - "power-down-3-state"
    description: |
      Power-down mode select.
      - Normal mode (reg: 0).
      - 1 kOhm output impedance (reg: 1).
      - 100 kOhm output impedance (reg: 2).
      - Three-state output impedance (reg: 3).
      The default corresponds to the reset value of the register field.

io-channel-cells:
  - output
```

**File**: `dts/bindings/dac/adi,ad5693.yaml`

```yaml
# Copyright (c) 2024 Jan Kubiznak <jan.kubiznak@deveritec.com>
# SPDX-License-Identifier: Apache-2.0

description: Driver for AD5693 (16-bit) DAC.

compatible: "adi,ad5693"

include: adi,ad569x-base.yaml
```

### Example 4: GPIO Controller

**File**: `dts/bindings/gpio/adi,adp5585-gpio.yaml`

```yaml
# Copyright (c) 2024 Analog Devices Inc.
# SPDX-License-Identifier: Apache-2.0

description: ADP5585 GPIO controller

compatible: "adi,adp5585-gpio"

include: gpio-controller.yaml

properties:
  ngpios:
    default: 11
    description: Number of GPIO pins (R0-R4, C0-C5)

  "#gpio-cells":
    const: 2
```

