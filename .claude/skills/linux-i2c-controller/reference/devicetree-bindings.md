# I2C Controller Devicetree Bindings

Guide to creating devicetree bindings and nodes for I2C controllers.

## I2C Controller Binding Schema

Device tree bindings must be in YAML schema format. Example for an I2C controller:

```yaml
# Documentation/devicetree/bindings/i2c/vendor,my-i2c.yaml
%YAML 1.2
---
$id: http://devicetree.org/schemas/i2c/vendor,my-i2c.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Vendor My I2C Controller

maintainers:
  - Your Name <your.email@example.com>

allOf:
  - $ref: /schemas/i2c/i2c-controller.yaml#

properties:
  compatible:
    const: vendor,my-i2c

  reg:
    maxItems: 1

  interrupts:
    maxItems: 1

  clocks:
    items:
      - description: I2C controller clock
      - description: APB/peripheral clock

  clock-names:
    items:
      - const: i2c
      - const: pclk

  clock-frequency:
    description:
      Desired I2C bus frequency in Hz
    minimum: 1000
    maximum: 400000
    default: 100000

  scl-gpios:
    description: GPIO for SCL (for bus recovery)
    maxItems: 1

  sda-gpios:
    description: GPIO for SDA (for bus recovery)
    maxItems: 1

required:
  - compatible
  - reg
  - interrupts
  - clocks
  - clock-names

unevaluatedProperties: false

examples:
  - |
    #include <dt-bindings/interrupt-controller/arm-gic.h>
    #include <dt-bindings/clock/vendor-clk.h>
    #include <dt-bindings/gpio/gpio.h>

    i2c@e0004000 {
        compatible = "vendor,my-i2c";
        reg = <0xe0004000 0x1000>;
        interrupts = <GIC_SPI 25 IRQ_TYPE_LEVEL_HIGH>;
        clocks = <&clkc 38>, <&clkc 15>;
        clock-names = "i2c", "pclk";
        clock-frequency = <400000>;
        #address-cells = <1>;
        #size-cells = <0>;

        scl-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
        sda-gpios = <&gpio0 11 GPIO_ACTIVE_HIGH>;

        eeprom@50 {
            compatible = "atmel,24c64";
            reg = <0x50>;
            pagesize = <32>;
        };
    };
```

## Required I2C Controller Properties

All I2C controller bindings must include `$ref: /schemas/i2c/i2c-controller.yaml#` which provides:

- `#address-cells = <1>`: I2C device addresses are 1 cell
- `#size-cells = <0>`: I2C devices have no size
- Standard I2C properties like `clock-frequency`, `i2c-scl-falling-time-ns`, etc.

## Standard I2C Properties

These properties are inherited from `i2c-controller.yaml`:

| Property | Type | Description |
|----------|------|-------------|
| `clock-frequency` | u32 | I2C bus frequency in Hz (100000, 400000, 1000000, 3400000) |
| `i2c-scl-falling-time-ns` | u32 | SCL falling edge time in nanoseconds |
| `i2c-scl-rising-time-ns` | u32 | SCL rising edge time in nanoseconds |
| `i2c-sda-falling-time-ns` | u32 | SDA falling edge time in nanoseconds |
| `i2c-analog-filter` | bool | Enable analog noise filter |
| `i2c-digital-filter` | bool | Enable digital noise filter |
| `i2c-digital-filter-width-ns` | u32 | Digital filter width in nanoseconds |
| `scl-gpios` | phandle | GPIO for SCL (bus recovery) |
| `sda-gpios` | phandle | GPIO for SDA (bus recovery) |

## I2C Controller Devicetree Node

Example controller node with all common properties:

```dts
i2c0: i2c@e0004000 {
	compatible = "cdns,i2c-r1p10";
	reg = <0xe0004000 0x1000>;
	interrupts = <GIC_SPI 25 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clkc 38>, <&clkc 15>;
	clock-names = "i2c", "pclk";

	// I2C bus configuration
	clock-frequency = <400000>;  // 400 kHz fast mode
	#address-cells = <1>;
	#size-cells = <0>;

	// Optional: GPIO-based bus recovery
	scl-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
	sda-gpios = <&gpio0 11 GPIO_ACTIVE_HIGH>;

	// I2C devices on this bus
	eeprom@50 {
		compatible = "atmel,24c64";
		reg = <0x50>;
		pagesize = <32>;
	};

	sensor@48 {
		compatible = "ti,tmp102";
		reg = <0x48>;
		interrupt-parent = <&gpio0>;
		interrupts = <5 IRQ_TYPE_EDGE_FALLING>;
	};
};
```

## Bus Number Assignment

Use devicetree aliases to assign specific I2C bus numbers:

```dts
/ {
	aliases {
		i2c0 = &i2c_main;
		i2c1 = &i2c_aux;
		i2c2 = &i2c_pmic;
	};

	i2c_main: i2c@e0004000 {
		compatible = "vendor,my-i2c";
		// ... will be /dev/i2c-0
	};

	i2c_aux: i2c@e0005000 {
		compatible = "vendor,my-i2c";
		// ... will be /dev/i2c-1
	};

	i2c_pmic: i2c@e0006000 {
		compatible = "vendor,my-i2c";
		// ... will be /dev/i2c-2
	};
};
```

In driver probe:
```c
// Use i2c_add_adapter() - the core will use alias number automatically
ret = i2c_add_adapter(&id->adap);
```

## I2C Speed Modes

Standard I2C bus frequencies:

```dts
i2c@... {
	clock-frequency = <100000>;   // Standard mode (100 kHz)
	clock-frequency = <400000>;   // Fast mode (400 kHz)
	clock-frequency = <1000000>;  // Fast mode plus (1 MHz)
	clock-frequency = <3400000>;  // High speed mode (3.4 MHz)
};
```

## Bus Recovery GPIO Properties

For GPIO-based bus recovery:

```dts
i2c@e0004000 {
	compatible = "vendor,my-i2c";
	reg = <0xe0004000 0x1000>;

	// GPIOs for bus recovery
	scl-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
	sda-gpios = <&gpio0 11 GPIO_ACTIVE_HIGH>;

	// Optionally specify recovery delay (microseconds)
	i2c-scl-recovery-delay-us = <2>;
};
```

In driver:
```c
i2c->scl_gpio = devm_gpiod_get_optional(&pdev->dev, "scl", GPIOD_OUT_HIGH);
i2c->sda_gpio = devm_gpiod_get_optional(&pdev->dev, "sda", GPIOD_IN);

if (i2c->scl_gpio && i2c->sda_gpio) {
	i2c->adap.bus_recovery_info = &(struct i2c_bus_recovery_info){
		.recover_bus = i2c_generic_scl_recovery,
		.get_scl = i2c_get_scl_gpio_value,
		.set_scl = i2c_set_scl_gpio_value,
		.get_sda = i2c_get_sda_gpio_value,
		.scl_gpiod = i2c->scl_gpio,
		.sda_gpiod = i2c->sda_gpio,
	};
}
```

## I2C Client Device Nodes

Devices on the I2C bus are children of the controller:

```dts
i2c0: i2c@e0004000 {
	compatible = "vendor,my-i2c";
	#address-cells = <1>;
	#size-cells = <0>;

	// 7-bit address device
	device1@50 {
		compatible = "vendor,device1";
		reg = <0x50>;
	};

	// 10-bit address device
	device2@3ff {
		compatible = "vendor,device2";
		reg = <0x3ff>;
	};

	// Device with interrupt
	device3@48 {
		compatible = "vendor,device3";
		reg = <0x48>;
		interrupt-parent = <&gpio0>;
		interrupts = <5 IRQ_TYPE_LEVEL_LOW>;
	};

	// Device with reset GPIO
	device4@4a {
		compatible = "vendor,device4";
		reg = <0x4a>;
		reset-gpios = <&gpio0 12 GPIO_ACTIVE_LOW>;
	};
};
```

## Validating Devicetree Bindings

Always validate bindings before submitting:

```bash
# Validate binding schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/i2c/vendor,my-i2c.yaml

# Validate devicetree files against schema
make dtbs_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/i2c/vendor,my-i2c.yaml

# Check specific device tree
make ARCH=arm64 xilinx/zynqmp-zcu102-rev1.0.dtb
```

## Example: Cadence I2C Controller

Real-world example from `Documentation/devicetree/bindings/i2c/cdns,i2c-r1p10.yaml`:

```yaml
properties:
  compatible:
    enum:
      - cdns,i2c-r1p10  # cadence i2c controller version 1.0
      - cdns,i2c-r1p14  # cadence i2c controller version 1.4

  reg:
    maxItems: 1

  clocks:
    minItems: 1
    items:
      - description: Main I2C clock
      - description: Peripheral clock

  interrupts:
    maxItems: 1

  clock-frequency:
    minimum: 1000
    maximum: 400000
    default: 100000

  clock-name:
    minItems: 1
    items:
      - const: pclk
      - const: i2c_clk
```

Used in devicetree:
```dts
i2c0: i2c@e0004000 {
	compatible = "cdns,i2c-r1p10";
	reg = <0xe0004000 0x1000>;
	interrupts = <0 25 4>;
	clocks = <&clkc 38>;
	clock-frequency = <400000>;
	#address-cells = <1>;
	#size-cells = <0>;
};
```
