## Devicetree Binding Pattern

**File**: `dts/bindings/serial/<vendor>,<chip>-uart.yaml`

```yaml
# Copyright (C) 2024 Vendor Corporation
# SPDX-License-Identifier: Apache-2.0

description: CHIP UART controller

compatible: "vendor,chip-uart"

include: [uart-controller.yaml, pinctrl-device.yaml]

properties:
  reg:
    required: true

  interrupts:
    required: true

  clock-frequency:
    type: int
    required: true
    description: UART controller clock frequency in Hz

  current-speed:
    type: int
    description: Initial baud rate setting (default: 115200)

  pinctrl-0:
    required: true

  pinctrl-names:
    required: true
```

**Devicetree usage**:

```dts
&pinctrl {
    uart0_default: uart0_default {
        group1 {
            pinmux = <UART0_TX_P0_6>, <UART0_RX_P0_7>;
        };
    };
};

uart0: uart@40028000 {
    compatible = "vendor,chip-uart";
    reg = <0x40028000 0x1000>;
    interrupts = <2 0>;
    clock-frequency = <16000000>;
    current-speed = <115200>;
    pinctrl-0 = <&uart0_default>;
    pinctrl-names = "default";
    status = "okay";
};
```

