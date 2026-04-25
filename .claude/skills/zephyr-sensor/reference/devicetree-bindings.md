## Devicetree Binding Pattern

### Basic Sensor Binding Structure

**Example from ADT7420** (`adi,adt7420.yaml`):

```yaml
# Copyright (c) 2018 Analog Devices Inc.
# SPDX-License-Identifier: Apache-2.0

description: ADT7420 high accuracy digital I2C temperature sensor

compatible: "adi,adt7420"

include: [sensor-device.yaml, i2c-device.yaml]

properties:
  int-gpios:
    type: phandle-array
    description: |
      Interrupt GPIO pin. The INT output defaults to active low
      when an interrupt is triggered.
```

**Example from ADXL345** (multi-bus with common properties):

`adi,adxl345-common.yaml`:
```yaml
# Copyright (c) 2022 Analog Devices Inc.
# SPDX-License-Identifier: Apache-2.0

description: |
  ADXL345 3-axis accelerometer
  Use includes and macros from adxl345.h in devicetree:

  Example:
  #include <zephyr/dt-bindings/sensor/adxl345.h>

  adxl345: adxl345@1d {
    compatible = "adi,adxl345-i2c";
    reg = <0x1d>;
    range = <ADXL345_DT_RANGE_8G>;
    odr = <ADXL345_DT_ODR_100>;
    int1-gpios = <&gpio0 11 GPIO_ACTIVE_HIGH>;
  };

include: sensor-device.yaml

properties:
  range:
    type: int
    default: 2
    description: |
      Accelerometer range.
    enum:
      - 0  # ADXL345_DT_RANGE_2G
      - 1  # ADXL345_DT_RANGE_4G
      - 2  # ADXL345_DT_RANGE_8G
      - 3  # ADXL345_DT_RANGE_16G

  odr:
    type: int
    default: 10
    description: |
      Output data rate (ODR). Default is power-on reset value.
    enum:
      - 7   # ADXL345_DT_ODR_12_5
      - 8   # ADXL345_DT_ODR_25
      - 9   # ADXL345_DT_ODR_50
      - 10  # ADXL345_DT_ODR_100
      - 11  # ADXL345_DT_ODR_200
      - 12  # ADXL345_DT_ODR_400

  fifo-watermark:
    type: int
    description: |
      FIFO watermark level in frame count. Valid range: 1-31

  int1-gpios:
    type: phandle-array
    description: |
      INT1 signal (active high). Either INT1 or INT2 will be used.
      If both defined, INT1 is prioritized.

  int2-gpios:
    type: phandle-array
    description: |
      INT2 signal (active high).
```

`adi,adxl345-i2c.yaml`:
```yaml
# Copyright (c) 2022 Analog Devices Inc.
# SPDX-License-Identifier: Apache-2.0

description: ADXL345 3-axis accelerometer (I2C)

compatible: "adi,adxl345-i2c"

include: [i2c-device.yaml, ./adi,adxl345-common.yaml]
```

`adi,adxl345-spi.yaml`:
```yaml
# Copyright (c) 2022 Analog Devices Inc.
# SPDX-License-Identifier: Apache-2.0

description: ADXL345 3-axis accelerometer (SPI)

compatible: "adi,adxl345-spi"

include: [spi-device.yaml, ./adi,adxl345-common.yaml]
```

### DT-Bindings Header (Optional)

For exposing constants to devicetree:

`include/zephyr/dt-bindings/sensor/adxl345.h`:
```c
#ifndef ZEPHYR_INCLUDE_DT_BINDINGS_SENSOR_ADXL345_H_
#define ZEPHYR_INCLUDE_DT_BINDINGS_SENSOR_ADXL345_H_

/* Range */
#define ADXL345_DT_RANGE_2G   0
#define ADXL345_DT_RANGE_4G   1
#define ADXL345_DT_RANGE_8G   2
#define ADXL345_DT_RANGE_16G  3

/* Output Data Rate */
#define ADXL345_DT_ODR_12_5   7
#define ADXL345_DT_ODR_25     8
#define ADXL345_DT_ODR_50     9
#define ADXL345_DT_ODR_100    10
#define ADXL345_DT_ODR_200    11
#define ADXL345_DT_ODR_400    12

#endif /* ZEPHYR_INCLUDE_DT_BINDINGS_SENSOR_ADXL345_H_ */
```

