## Devicetree Binding Pattern

**File**: `dts/bindings/i2c/<vendor>,<chip>-i2c.yaml`

```yaml
# Copyright (C) 2024 Vendor Corporation
# SPDX-License-Identifier: Apache-2.0

description: CHIP I2C controller

compatible: "vendor,chip-i2c"

include: [i2c-controller.yaml, pinctrl-device.yaml]

properties:
  reg:
    required: true

  interrupts:
    required: true

  clock-frequency:
    type: int
    required: true
    description: I2C bus clock frequency in Hz

  pinctrl-0:
    required: true

  pinctrl-names:
    required: true
```

**Devicetree usage**:

```dts
&pinctrl {
    i2c0_default: i2c0_default {
        group1 {
            pinmux = <I2C0_SDA_P0_8>, <I2C0_SCL_P0_9>;
            bias-pull-up;
        };
    };
};

i2c0: i2c@40000000 {
    compatible = "vendor,chip-i2c";
    reg = <0x40000000 0x1000>;
    interrupts = <10 0>;
    #address-cells = <1>;
    #size-cells = <0>;
    clock-frequency = <100000>; /* 100 kHz */
    pinctrl-0 = <&i2c0_default>;
    pinctrl-names = "default";
    status = "okay";

    /* I2C devices on this bus */
    sensor@48 {
        compatible = "vendor,sensor";
        reg = <0x48>;
    };

    eeprom@50 {
        compatible = "atmel,at24";
        reg = <0x50>;
        size = <2048>;
        pagesize = <16>;
    };
};
```

