# HWMON Devicetree Bindings

Reference for creating devicetree bindings and nodes for HWMON sensors.

## Basic HWMON Device Binding

**Devicetree binding** (`Documentation/devicetree/bindings/hwmon/vendor,sensor.yaml`):

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/hwmon/vendor,sensor.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Vendor Temperature and Humidity Sensor

maintainers:
  - Your Name <your.email@example.com>

description:
  Digital temperature and humidity sensor with I2C interface.

properties:
  compatible:
    const: vendor,temp-sensor

  reg:
    maxItems: 1

  vdd-supply:
    description: Power supply for the sensor

required:
  - compatible
  - reg

additionalProperties: false

examples:
  - |
    i2c {
        #address-cells = <1>;
        #size-cells = <0>;

        temp-sensor@48 {
            compatible = "vendor,temp-sensor";
            reg = <0x48>;
            vdd-supply = <&reg_3v3>;
        };
    };
```

## Devicetree Node Examples

### Temperature Sensor (I2C)

```dts
&i2c0 {
	temp_sensor: temperature@48 {
		compatible = "vendor,temp-sensor";
		reg = <0x48>;
		vdd-supply = <&reg_3v3>;
	};
};
```

### Humidity Sensor with Power Control

```dts
&i2c1 {
	sht4x: humidity@44 {
		compatible = "sensirion,sht4x";
		reg = <0x44>;
		vdd-supply = <&reg_3v3>;
		reset-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;
	};
};
```

### Multi-Channel Power Monitor

```dts
&i2c0 {
	power_monitor: ltc2991@48 {
		compatible = "lltc,ltc2991";
		reg = <0x48>;
		vcc-supply = <&reg_5v0>;

		lltc,meas-mode = <
			LTC2991_V1_V2_TR2
			LTC2991_V3_V4_TR2
			LTC2991_V5_V6
			LTC2991_V7_V8
		>;
	};
};
```

### PMIC with HWMON Support

```dts
&i2c0 {
	pmic: pmic@30 {
		compatible = "vendor,pmic";
		reg = <0x30>;

		regulators {
			vdd_core: DCDC1 {
				regulator-name = "vdd-core";
				regulator-min-microvolt = <800000>;
				regulator-max-microvolt = <1200000>;
			};
		};

		// HWMON functionality for voltage/current monitoring
		// typically created automatically by PMIC driver
	};
};
```

## Common Properties

### Power Supplies

```yaml
vdd-supply:
  description: Main power supply

vddio-supply:
  description: I/O power supply
```

**Usage**:
```dts
sensor@48 {
	compatible = "vendor,sensor";
	reg = <0x48>;
	vdd-supply = <&reg_3v3>;
	vddio-supply = <&reg_1v8>;
};
```

### Reset GPIO

```yaml
reset-gpios:
  description: GPIO for hardware reset
  maxItems: 1
```

**Usage**:
```dts
sensor@48 {
	compatible = "vendor,sensor";
	reg = <0x48>;
	reset-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;
};
```

### Interrupt

```yaml
interrupts:
  description: Alert/alarm interrupt
  maxItems: 1
```

**Usage**:
```dts
sensor@48 {
	compatible = "vendor,sensor";
	reg = <0x48>;
	interrupt-parent = <&gpio0>;
	interrupts = <10 IRQ_TYPE_EDGE_FALLING>;
};
```

### Shunt Resistor (for current monitors)

```yaml
shunt-resistor-micro-ohms:
  description: Current sense shunt resistor value in micro-ohms
```

**Usage**:
```dts
current_monitor: ina219@40 {
	compatible = "ti,ina219";
	reg = <0x40>;
	shunt-resistor-micro-ohms = <100000>;  // 0.1Ω = 100mΩ = 100,000µΩ
};
```

## Real-World Examples

### LM75 Temperature Sensor

```yaml
# Documentation/devicetree/bindings/hwmon/lm75.yaml
compatible:
  enum:
    - adi,adt75
    - ti,lm75
    - ti,lm75a
    - ti,lm75b

reg:
  maxItems: 1

vs-supply:
  description: phandle to the regulator that provides the +VS supply
```

```dts
&i2c0 {
	lm75: temperature-sensor@48 {
		compatible = "ti,lm75";
		reg = <0x48>;
		vs-supply = <&reg_3v3>;
	};
};
```

### INA219 Current/Power Monitor

```yaml
# Documentation/devicetree/bindings/hwmon/ti,ina2xx.yaml
compatible:
  enum:
    - ti,ina219
    - ti,ina220
    - ti,ina226
    - ti,ina230
    - ti,ina231

shunt-resistor:
  description: shunt resistor value in micro-ohms
```

```dts
&i2c0 {
	ina219: power-monitor@40 {
		compatible = "ti,ina219";
		reg = <0x40>;
		shunt-resistor = <100000>;  // 0.1Ω
	};
};
```

### SHT4x Humidity Sensor

```dts
&i2c0 {
	sht4x: humidity-sensor@44 {
		compatible = "sensirion,sht4x";
		reg = <0x44>;
		vdd-supply = <&reg_3v3>;
	};
};
```

## Accessing from Driver

### Getting Supply Regulators

```c
#include <linux/regulator/consumer.h>

static int sensor_probe(struct i2c_client *client)
{
	struct regulator *vdd;

	// Get required supply
	vdd = devm_regulator_get(&client->dev, "vdd");
	if (IS_ERR(vdd))
		return dev_err_probe(&client->dev, PTR_ERR(vdd),
				     "Failed to get vdd supply\n");

	// Enable supply
	ret = regulator_enable(vdd);
	if (ret)
		return ret;

	// ... rest of probe ...
}
```

### Getting Reset GPIO

```c
#include <linux/gpio/consumer.h>

static int sensor_probe(struct i2c_client *client)
{
	struct gpio_desc *reset_gpio;

	// Get optional reset GPIO
	reset_gpio = devm_gpiod_get_optional(&client->dev, "reset",
					     GPIOD_OUT_HIGH);
	if (IS_ERR(reset_gpio))
		return PTR_ERR(reset_gpio);

	// Reset sequence if GPIO is present
	if (reset_gpio) {
		gpiod_set_value_cansleep(reset_gpio, 0);  // Assert reset
		msleep(10);
		gpiod_set_value_cansleep(reset_gpio, 1);  // De-assert reset
		msleep(10);
	}

	// ... rest of probe ...
}
```

### Reading Properties

```c
#include <linux/property.h>

static int sensor_probe(struct i2c_client *client)
{
	u32 shunt_resistor;

	// Read shunt resistor value (in micro-ohms)
	ret = device_property_read_u32(&client->dev,
				       "shunt-resistor-micro-ohms",
				       &shunt_resistor);
	if (ret)
		shunt_resistor = 100000;  // Default: 0.1Ω

	// ... rest of probe ...
}
```

## Validation

### Validate Binding Schema

```bash
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/hwmon/vendor,sensor.yaml
```

### Validate Devicetree

```bash
make dtbs_check
```

## Best Practices

1. **Use YAML schema format** - All new bindings must be YAML, not .txt
2. **Provide examples** - Include at least one example in the binding
3. **Document all properties** - Every property should have a description
4. **Use standard property names** - Follow existing conventions:
   - `vdd-supply`, `vddio-supply` for power
   - `reset-gpios` for reset GPIO
   - `shunt-resistor-micro-ohms` for current monitor shunts
5. **Set additionalProperties: false** - Catch typos in devicetree nodes
6. **Add maintainer** - Include your name and email
7. **Test validation** - Run `make dt_binding_check` before submitting

## References

- **Devicetree Specification**: https://www.devicetree.org/
- **Kernel Documentation**: `Documentation/devicetree/bindings/hwmon/`
- **Writing Schemas**: `Documentation/devicetree/writing-schema.rst`
- **Example Bindings**:
  - `Documentation/devicetree/bindings/hwmon/lm75.yaml`
  - `Documentation/devicetree/bindings/hwmon/ti,ina2xx.yaml`
  - `Documentation/devicetree/bindings/hwmon/adi,ltc2991.yaml`
