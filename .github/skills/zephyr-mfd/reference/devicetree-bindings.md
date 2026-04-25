## Devicetree Binding Pattern

### Parent Binding

**For I2C-only device** (`dts/bindings/mfd/<vendor>,<chip>-i2c.yaml`):

```yaml
# Copyright (c) 2025 Company
# SPDX-License-Identifier: Apache-2.0

description: Vendor ChipName Multi-Function Device via I2C

compatible: "vendor,chip"

include: [i2c-device.yaml, "vendor,chip-common.yaml"]
```

**For SPI-only device** (`dts/bindings/mfd/<vendor>,<chip>-spi.yaml`):

```yaml
# Copyright (c) 2025 Company
# SPDX-License-Identifier: Apache-2.0

description: Vendor ChipName Multi-Function Device via SPI

compatible: "vendor,chip"

include: [spi-device.yaml, "vendor,chip-common.yaml"]
```

**Common properties** (`dts/bindings/mfd/<vendor>,<chip>-common.yaml`):

```yaml
# Copyright (c) 2025 Company
# SPDX-License-Identifier: Apache-2.0

description: Vendor ChipName common properties

properties:
  reset-gpios:
    type: phandle-array
    description: RESET pin

  int-gpios:
    type: phandle-array
    description: Interrupt pin (optional)
```

**From AD559x bindings**:

`adi,ad559x-i2c.yaml`:
```yaml
description: Analog AD559x ADC/DAC/GPIO chip via I2C bus

compatible: "adi,ad559x"

include: [i2c-device.yaml, "adi,ad559x-common.yaml"]
```

`adi,ad559x-common.yaml`:
```yaml
description: Analog AD559x ADC/DAC/GPIO chip common properties

properties:
  reset-gpios:
    type: phandle-array
    description: RESET pin
```

### Child Bindings

**DAC child** (`dts/bindings/dac/<vendor>,<chip>-dac.yaml`):

```yaml
# Copyright (c) 2025 Company
# SPDX-License-Identifier: Apache-2.0

description: ChipName DAC Controller

compatible: "vendor,chip-dac"

include: dac-controller.yaml

properties:
  "#io-channel-cells":
    const: 1

  double-output-range:
    type: boolean
    description: |
      Default DAC output range is 0V to Vref.
      This option increases the range from 0V to 2 x Vref.

io-channel-cells:
  - output
```

**ADC child** (`dts/bindings/adc/<vendor>,<chip>-adc.yaml`):

```yaml
description: ChipName ADC Controller

compatible: "vendor,chip-adc"

include: adc-controller.yaml

properties:
  "#io-channel-cells":
    const: 1

  double-input-range:
    type: boolean
    description: |
      Default ADC input range is 0V to Vref.
      This option increases the range from 0V to 2 x Vref.

io-channel-cells:
  - input
```

**GPIO child** (`dts/bindings/gpio/<vendor>,<chip>-gpio.yaml`):

```yaml
description: ChipName GPIO Controller

compatible: "vendor,chip-gpio"

include: gpio-controller.yaml

gpio-cells:
  - pin
  - flags
```

### Devicetree Usage Example

**Board overlay** (`boards/boardname.overlay`):

```dts
&i2c1 {
	status = "okay";

	ad559x: ad559x@13 {
		compatible = "adi,ad559x";
		reg = <0x13>;
		reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;

		ad559x_dac: dac-controller {
			compatible = "adi,ad559x-dac";
			#io-channel-cells = <1>;
			double-output-range;
		};

		ad559x_adc: adc-controller {
			compatible = "adi,ad559x-adc";
			#io-channel-cells = <1>;
			double-input-range;
		};

		ad559x_gpio: gpio-controller {
			compatible = "adi,ad559x-gpio";
			gpio-controller;
			#gpio-cells = <2>;
		};
	};
};

/ {
	aliases {
		dac0 = &ad559x_dac;
		adc0 = &ad559x_adc;
		gpio-ad559x = &ad559x_gpio;
	};
};
```

**SPI variant**:

```dts
&spi2 {
	status = "okay";
	cs-gpios = <&gpio0 25 GPIO_ACTIVE_LOW>;

	ad559x_spi: ad559x@0 {
		compatible = "adi,ad559x";
		reg = <0>;
		spi-max-frequency = <10000000>;
		reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;

		ad559x_dac_spi: dac-controller {
			compatible = "adi,ad559x-dac";
			#io-channel-cells = <1>;
		};

		ad559x_adc_spi: adc-controller {
			compatible = "adi,ad559x-adc";
			#io-channel-cells = <1>;
		};

		ad559x_gpio_spi: gpio-controller {
			compatible = "adi,ad559x-gpio";
			gpio-controller;
			#gpio-cells = <2>;
		};
	};
};
```

**MAX22017 example** (SPI only):

```dts
&spi1 {
	status = "okay";

	max22017: max22017@0 {
		compatible = "adi,max22017";
		reg = <0>;
		spi-max-frequency = <8000000>;
		reset-gpios = <&gpio0 15 GPIO_ACTIVE_HIGH>;
		int-gpios = <&gpio0 16 GPIO_ACTIVE_LOW>;
		crc-mode;

		max22017_dac: dac {
			compatible = "adi,max22017-dac";
			#io-channel-cells = <1>;
		};

		max22017_gpio: gpio {
			compatible = "adi,max22017-gpio";
			gpio-controller;
			#gpio-cells = <2>;
		};
	};
};
```

