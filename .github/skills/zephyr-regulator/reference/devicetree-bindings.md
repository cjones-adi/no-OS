## Devicetree Binding Pattern

### Basic Binding Structure

**File:** `dts/bindings/regulator/vendor,chipname.yaml`

```yaml
description: |
  Vendor ChipName PMIC

  The PMIC has two buck converters and two LDOs. All need to be defined as
  children nodes, strictly following the BUCK1, BUCK2, LDO1, LDO2 node names.

  Example:

  pmic@50 {
    compatible = "vendor,chipname";
    reg = <0x50>;

    BUCK1 {
      regulator-min-microvolt = <700000>;
      regulator-max-microvolt = <1500000>;
      regulator-boot-on;
    };
    BUCK2 {
      regulator-min-microvolt = <700000>;
      regulator-max-microvolt = <3300000>;
    };
    LDO1 {
      regulator-min-microvolt = <800000>;
      regulator-max-microvolt = <3300000>;
      regulator-always-on;
    };
  };

compatible: "vendor,chipname"

include: [base.yaml, i2c-device.yaml]

properties:
  # Chip-specific properties
  vendor,enable-xyz:
    type: boolean
    description: Enable XYZ feature

  vendor,current-limit-microamp:
    type: int
    enum:
      - 100000
      - 200000
      - 500000
    description: Global current limit in microamps

child-binding:
  include:
    - name: regulator.yaml
      property-allowlist:
        - regulator-init-microvolt
        - regulator-min-microvolt
        - regulator-max-microvolt
        - regulator-init-microamp
        - regulator-min-microamp
        - regulator-max-microamp
        - regulator-always-on
        - regulator-boot-on
        - regulator-boot-off
        - regulator-initial-mode
        - regulator-allowed-modes
        - regulator-active-discharge
        - startup-delay-us
        - off-on-delay-us
```

### Mode Definitions

If your regulator supports modes, define them in a header:

**File:** `include/zephyr/dt-bindings/regulator/vendor_chipname.h`

```c
#ifndef ZEPHYR_INCLUDE_DT_BINDINGS_REGULATOR_VENDOR_CHIPNAME_H_
#define ZEPHYR_INCLUDE_DT_BINDINGS_REGULATOR_VENDOR_CHIPNAME_H_

/** Operating modes for VENDOR CHIPNAME regulators */
#define CHIPNAME_MODE_AUTO      0
#define CHIPNAME_MODE_PWM       1
#define CHIPNAME_MODE_PFM       2
#define CHIPNAME_MODE_LOW_POWER 3

#endif
```

**Use in devicetree:**
```dts
#include <zephyr/dt-bindings/regulator/vendor_chipname.h>

&pmic {
    BUCK1 {
        regulator-initial-mode = <CHIPNAME_MODE_AUTO>;
        regulator-allowed-modes = <CHIPNAME_MODE_AUTO>, <CHIPNAME_MODE_PWM>;
    };
};
```

## Board Devicetree Overlays

Board overlays configure hardware-specific settings for your driver on specific boards.

### Overlay File Location

```
samples/drivers/<subsystem>/<sample>/boards/<board_name>.overlay
```

Example: `boards/nrf52840dk_nrf52840.overlay`

### Basic Overlay Structure

#### Standalone I2C Regulator

```dts
/*
 * Copyright (c) 2024 Your Company
 * SPDX-License-Identifier: Apache-2.0
 */

&i2c0 {
	status = "okay";

	pmic@28 {
		compatible = "maxim,max20335-regulator";
		reg = <0x28>;

		regulators {
			compatible = "maxim,max20335-regulator";

			buck1: BUCK1 {
				regulator-name = "BUCK1";
				regulator-min-microvolt = <700000>;
				regulator-max-microvolt = <1500000>;
				regulator-init-microvolt = <1200000>;
				regulator-boot-on;
			};

			ldo1: LDO1 {
				regulator-name = "LDO1";
				regulator-min-microvolt = <800000>;
				regulator-max-microvolt = <3300000>;
				regulator-init-microvolt = <1800000>;
				regulator-always-on;
			};
		};
	};
};
```

#### Standalone SPI Regulator

```dts
&spi1 {
	status = "okay";
	cs-gpios = <&gpio0 25 GPIO_ACTIVE_LOW>;

	regulator@0 {
		compatible = "vendor,chip-regulator";
		reg = <0>;
		spi-max-frequency = <8000000>;

		regulator-name = "VOUT";
		regulator-min-microvolt = <800000>;
		regulator-max-microvolt = <3300000>;
	};
};
```

#### MFD-based PMIC with Multiple Regulators

```dts
&i2c1 {
	status = "okay";

	pmic: pmic@50 {
		compatible = "adi,max20370";
		reg = <0x50>;

		max20370_converters: converters {
			compatible = "adi,max20370-converters";

			buck1: BUCK1 {
				compatible = "adi,max20370-regulator";
				regulator-name = "VDD_CORE";
				regulator-min-microvolt = <500000>;
				regulator-max-microvolt = <1800000>;
				regulator-init-microvolt = <1200000>;
				regulator-boot-on;
			};

			buck2: BUCK2 {
				compatible = "adi,max20370-regulator";
				regulator-name = "VDD_IO";
				regulator-min-microvolt = <1800000>;
				regulator-max-microvolt = <3300000>;
				regulator-always-on;
			};

			ldo1: LDO1 {
				compatible = "adi,max20370-regulator";
				regulator-name = "VDD_ANALOG";
				regulator-min-microvolt = <800000>;
				regulator-max-microvolt = <3300000>;
				regulator-initial-mode = <0>;  /* Auto mode */
			};
		};
	};
};
```

#### With GPIO Control

```dts
&i2c0 {
	pmic@60 {
		compatible = "vendor,pmic";
		reg = <0x60>;

		/* Optional GPIO for enable/reset */
		enable-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
		reset-gpios = <&gpio0 11 GPIO_ACTIVE_LOW>;

		buck1: regulator {
			regulator-name = "VOUT";
			regulator-min-microvolt = <800000>;
			regulator-max-microvolt = <1800000>;
		};
	};
};
```

### Aliasing for Sample Code

To make sample code board-agnostic, use aliases:

```dts
/ {
	aliases {
		regulator0 = &buck1;
		regulator1 = &ldo1;
	};
};

/* Then in code: */
/* #define REGULATOR_NODE DT_ALIAS(regulator0) */
```

### Multiple Board Support

Create overlays for each supported board:

**boards/nrf52840dk_nrf52840.overlay**:
```dts
/* NRF52840 uses I2C1 */
&i2c1 {
	status = "okay";
	/* ... PMIC config */
};
```

**boards/nucleo_f767zi.overlay**:
```dts
/* STM32 uses I2C2 */
&i2c2 {
	status = "okay";
	/* ... PMIC config */
};
```

**boards/esp32_devkitc_wrover.overlay**:
```dts
/* ESP32 uses I2C0 */
&i2c0 {
	status = "okay";
	/* ... PMIC config */
};
```

### Board-Specific Configuration (Optional)

**boards/nrf52840dk_nrf52840.conf**:
```conf
# Board-specific Kconfig options
CONFIG_I2C_NRFX=y
CONFIG_GPIO=y

# Increase stack size for this board
CONFIG_MAIN_STACK_SIZE=2048
```

