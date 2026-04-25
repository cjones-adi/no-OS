## Devicetree Binding Pattern

**File**: `dts/bindings/spi/<vendor>,<chip>-spi.yaml`

```yaml
# Copyright (C) 2024 Vendor Corporation
# SPDX-License-Identifier: Apache-2.0

description: CHIP SPI controller

compatible: "vendor,chip-spi"

include: [spi-controller.yaml, pinctrl-device.yaml]

properties:
  reg:
    required: true

  interrupts:
    required: true

  clock-frequency:
    type: int
    required: true
    description: SPI controller clock frequency in Hz

  pinctrl-0:
    required: true

  pinctrl-names:
    required: true
```

**Devicetree usage** (SPI controller):

```dts
&pinctrl {
    spi1_default: spi1_default {
        group1 {
            pinmux = <SPI1_MOSI_P0_12>, <SPI1_MISO_P0_13>,
                     <SPI1_SCK_P0_14>;
        };
    };
};

spi1: spi@40004000 {
    compatible = "vendor,chip-spi";
    reg = <0x40004000 0x1000>;
    interrupts = <15 0>;
    #address-cells = <1>;
    #size-cells = <0>;
    clock-frequency = <48000000>;
    pinctrl-0 = <&spi1_default>;
    pinctrl-names = "default";
    status = "okay";

    /* GPIO chip selects (optional) */
    cs-gpios = <&gpio0 15 GPIO_ACTIVE_LOW>,
               <&gpio0 16 GPIO_ACTIVE_LOW>;

    /* SPI devices on this bus */
    sensor@0 {
        compatible = "vendor,sensor";
        reg = <0>;  /* CS index 0 */
        spi-max-frequency = <8000000>;  /* 8 MHz */
    };

    flash@1 {
        compatible = "vendor,flash";
        reg = <1>;  /* CS index 1 */
        spi-max-frequency = <25000000>;  /* 25 MHz */
    };
};
```

**Devicetree usage** (SPI device):

```dts
&spi1 {
    status = "okay";

    accel: accel@0 {
        compatible = "adi,adxl345";
        reg = <0>;
        spi-max-frequency = <5000000>;

        /* Clock mode: Mode 3 (CPOL=1, CPHA=1) */
        spi-cpol;
        spi-cpha;

        /* Optional properties */
        spi-cs-setup-delay-ns = <100>;
        spi-cs-hold-delay-ns = <100>;
        spi-interframe-delay-ns = <500>;
    };
};
```

