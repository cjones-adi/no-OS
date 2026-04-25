## Devicetree Binding Pattern

### Base GPIO Controller Binding

**For standalone I2C GPIO expander** (`dts/bindings/gpio/vendor,chip.yaml`):

```yaml
# Copyright (c) 2024 Company
# SPDX-License-Identifier: Apache-2.0

description: Vendor ChipName GPIO Expander

compatible: "vendor,chip-gpio"

include: [gpio-controller.yaml, i2c-device.yaml]

properties:
  "#gpio-cells":
    const: 2

  ngpios:
    type: int
    required: true
    description: Number of GPIO pins available

  gpio-reserved-ranges:
    type: array
    description: |
      Ranges of GPIOs that are not available (pairs of <start, count>).
      Example: [5, 3] means pins 5, 6, 7 are reserved.

gpio-cells:
  - pin
  - flags
```

**From ADP5585** (`dts/bindings/gpio/adi,adp5585-gpio.yaml`):

```yaml
# Copyright 2024 NXP
# SPDX-License-Identifier: Apache-2.0

description: ADP5585 GPIO Controller

compatible: "adi,adp5585-gpio"

include: gpio-controller.yaml

properties:
  "#gpio-cells":
    const: 2

  ngpios:
    const: 13
    description: |
      Number of GPIOs available on port expander.

  gpio-reserved-ranges:
    required: true
    const: [5, 3]
    description: |
      Ranges of GPIOs reserved unavailable on port expander.
      The ADP5585 has 10 GPIO lines divided in 2 groups. GPIO number
      5, 6, 7 is reserved. That's to say, GPIO R0~R4 occupy line
      number 0~4, GPIO C0~C4 occupy line number 8~12.

gpio-cells:
  - pin
  - flags
```

**For MFD child GPIO** (`dts/bindings/gpio/adi,ad559x-gpio.yaml`):

```yaml
description: AD559x GPIO Controller

compatible: "adi,ad559x-gpio"

include: gpio-controller.yaml

gpio-cells:
  - pin
  - flags
```

### Devicetree Usage Examples

**Standalone I2C GPIO expander**:

```dts
&i2c1 {
	status = "okay";

	gpio_exp: gpio-expander@20 {
		compatible = "vendor,chip-gpio";
		reg = <0x20>;
		gpio-controller;
		#gpio-cells = <2>;
		ngpios = <16>;
		interrupt-parent = <&gpio0>;
		interrupts = <25 GPIO_INT_EDGE_FALLING>;
	};
};

/ {
	aliases {
		gpio-exp = &gpio_exp;
	};

	leds {
		compatible = "gpio-leds";
		led_ext: led-ext {
			gpios = <&gpio_exp 0 GPIO_ACTIVE_HIGH>;
		};
	};

	buttons {
		compatible = "gpio-keys";
		button_ext: button-ext {
			gpios = <&gpio_exp 8 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
		};
	};
};
```

**MFD child GPIO** (from ADP5585):

```dts
&i2c1 {
	adp5585: adp5585@34 {
		compatible = "adi,adp5585";
		reg = <0x34>;
		reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;
		nint-gpios = <&gpio0 11 GPIO_ACTIVE_LOW>;

		adp5585_gpio: gpio-controller {
			compatible = "adi,adp5585-gpio";
			gpio-controller;
			#gpio-cells = <2>;
			ngpios = <13>;
			gpio-reserved-ranges = <5 3>;
		};
	};
};

/ {
	leds {
		led_r0: led-r0 {
			gpios = <&adp5585_gpio 0 GPIO_ACTIVE_HIGH>;
		};
	};
};
```

