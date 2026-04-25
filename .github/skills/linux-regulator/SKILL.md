---
name: linux-regulator
description: Complete guide to Linux regulator framework for voltage/current regulators and PMICs. Use when implementing regulator drivers, working with MFD parents, using linear ranges, or managing power supplies.
---

# Linux Regulator Framework

## When to Use This Skill

Use when implementing voltage regulators, current limiters, PMICs, or power supply controllers. Covers standalone regulators and MFD-integrated regulators.

## Core Structures

### struct regulator_ops

```c
struct regulator_ops {
	// Voltage control
	int (*set_voltage_sel)(struct regulator_dev *, unsigned selector);
	int (*get_voltage_sel)(struct regulator_dev *);
	int (*list_voltage)(struct regulator_dev *, unsigned selector);

	// Current control
	int (*set_current_limit)(struct regulator_dev *, int min_uA, int max_uA);
	int (*get_current_limit)(struct regulator_dev *);

	// Enable/disable
	int (*enable)(struct regulator_dev *);
	int (*disable)(struct regulator_dev *);
	int (*is_enabled)(struct regulator_dev *);

	// Mode control
	int (*set_mode)(struct regulator_dev *, unsigned int mode);
	unsigned int (*get_mode)(struct regulator_dev *);

	// Status
	int (*get_status)(struct regulator_dev *);
};
```

### struct regulator_desc

```c
struct regulator_desc {
	const char *name;
	const char *supply_name;      // Parent supply name
	const char *of_match;          // DT node name

	int id;
	unsigned int n_voltages;
	const struct regulator_ops *ops;
	int type;  // REGULATOR_VOLTAGE or REGULATOR_CURRENT

	// Linear voltage range
	const struct linear_range *linear_ranges;
	int n_linear_ranges;

	// Or simple linear
	int min_uV;
	int uV_step;
	unsigned int linear_min_sel;

	// REGMAP integration
	unsigned int vsel_reg;
	unsigned int vsel_mask;
	unsigned int enable_reg;
	unsigned int enable_mask;
	unsigned int enable_val;
	unsigned int disable_val;

	// Devicetree parsing
	int (*of_parse_cb)(struct device_node *np,
			   const struct regulator_desc *desc,
			   struct regulator_config *config);
};
```

## Linear Ranges (Recommended Pattern)

### Using REGULATOR_LINEAR_RANGE

```c
#include <linux/regulator/driver.h>

// Example: ADP5055 voltage range
// From 408mV to 790.5mV in 1.5mV steps
static const struct linear_range adp5055_voltage_ranges[] = {
	REGULATOR_LINEAR_RANGE(408000, 0, 255, 1500),
};

// Complex multi-range example
static const struct linear_range max77541_current_ranges[] = {
	// 0.025A to 0.1750A in 0.025A steps (selectors 0-6)
	REGULATOR_LINEAR_RANGE(25000, 0, 6, 25000),
	// 0.200A to 1.5A in 0.050A steps (selectors 7-32)
	REGULATOR_LINEAR_RANGE(200000, 7, 32, 50000),
	// 1.6A to 4.0A in 0.1A steps (selectors 33-56)
	REGULATOR_LINEAR_RANGE(1600000, 33, 56, 100000),
};
```

### Regulator Descriptor with Linear Ranges

```c
static const struct regulator_desc adp5055_regulators_desc[] = {
	{
		.name = "VOUT0",
		.of_match = "vout0",
		.id = 0,
		.ops = &adp5055_regulator_ops,
		.type = REGULATOR_VOLTAGE,
		.n_voltages = 256,
		.linear_ranges = adp5055_voltage_ranges,
		.n_linear_ranges = ARRAY_SIZE(adp5055_voltage_ranges),
		.vsel_reg = ADP5055_VID0,
		.vsel_mask = 0xFF,
		.enable_reg = ADP5055_CTRL123,
		.enable_mask = BIT(0),
		.owner = THIS_MODULE,
		.of_parse_cb = adp5055_of_parse_cb,
	},
};
```

### Using Linear Range Helpers

```c
static const struct regulator_ops adp5055_regulator_ops = {
	// Use helper for linear ranges
	.list_voltage = regulator_list_voltage_linear_range,
	.map_voltage = regulator_map_voltage_linear_range,
	.set_voltage_sel = regulator_set_voltage_sel_regmap,
	.get_voltage_sel = regulator_get_voltage_sel_regmap,
	.enable = regulator_enable_regmap,
	.disable = regulator_disable_regmap,
	.is_enabled = regulator_is_enabled_regmap,
};
```

## Macro-Based Regulator Descriptions

### Define Macros for Readability

```c
// From adp5055-regulator.c pattern
#define ADP5055_REGULATOR_DESC(_id, _name) \
{									\
	.name = (_name),						\
	.of_match = of_match_ptr("vout" #_id),			\
	.regulators_node = of_match_ptr("regulators"),		\
	.id = (_id),							\
	.ops = &adp5055_regulator_ops,				\
	.type = REGULATOR_VOLTAGE,					\
	.n_voltages = 256,						\
	.linear_ranges = adp5055_voltage_ranges,			\
	.n_linear_ranges = ARRAY_SIZE(adp5055_voltage_ranges),	\
	.vsel_reg = ADP5055_VID0 + (_id),				\
	.vsel_mask = 0xFF,						\
	.enable_reg = ADP5055_CTRL123,				\
	.enable_mask = BIT(_id),					\
	.owner = THIS_MODULE,					\
	.of_parse_cb = adp5055_of_parse_cb,				\
}

static const struct regulator_desc adp5055_regulators_desc[] = {
	ADP5055_REGULATOR_DESC(0, "VOUT0"),
	ADP5055_REGULATOR_DESC(1, "VOUT1"),
	ADP5055_REGULATOR_DESC(2, "VOUT2"),
};
```

**Benefits**:
- Single source of truth for register layout
- Easy to maintain and extend
- Prevents copy-paste errors
- Clear parameter dependency

## MFD Integration

### MFD Parent Driver

Multi-Function Devices (MFDs) combine multiple sub-functions (regulators, GPIOs, clocks, etc.) in one chip.

```c
// drivers/mfd/max77541.c
#include <linux/mfd/core.h>
#include <linux/mfd/max77541.h>

static const struct mfd_cell max77541_devs[] = {
	MFD_CELL_NAME("max77541-regulator"),
	MFD_CELL_NAME("max77541-adc"),
};

static int max77541_probe(struct i2c_client *client)
{
	struct max77541 *max77541;
	struct regmap_config regmap_cfg = {
		.reg_bits = 8,
		.val_bits = 8,
		.max_register = 0xFF,
	};

	max77541 = devm_kzalloc(&client->dev, sizeof(*max77541), GFP_KERNEL);
	if (!max77541)
		return -ENOMEM;

	max77541->dev = &client->dev;

	max77541->regmap = devm_regmap_init_i2c(client, &regmap_cfg);
	if (IS_ERR(max77541->regmap))
		return PTR_ERR(max77541->regmap);

	i2c_set_clientdata(client, max77541);

	// Register sub-devices
	return devm_mfd_add_devices(&client->dev, PLATFORM_DEVID_NONE,
				    max77541_devs, ARRAY_SIZE(max77541_devs),
				    NULL, 0, NULL);
}
```

### MFD Regulator Child Driver

```c
// drivers/regulator/max77541-regulator.c
#include <linux/mfd/max77541.h>
#include <linux/platform_device.h>
#include <linux/regulator/driver.h>

struct max77541_regulator {
	struct device *dev;
	struct regmap *regmap;
};

static const struct regulator_ops max77541_buck_ops = {
	.list_voltage = regulator_list_voltage_linear_range,
	.map_voltage = regulator_map_voltage_linear_range,
	.set_voltage_sel = regulator_set_voltage_sel_regmap,
	.get_voltage_sel = regulator_get_voltage_sel_regmap,
	.enable = regulator_enable_regmap,
	.disable = regulator_disable_regmap,
	.is_enabled = regulator_is_enabled_regmap,
};

static const struct linear_range max77541_buck_ranges[] = {
	REGULATOR_LINEAR_RANGE(500000, 0, 0x74, 5000),
};

#define MAX77541_BUCK(_id) \
{							\
	.name = "BUCK" #_id,				\
	.of_match = of_match_ptr("buck" #_id),	\
	.regulators_node = of_match_ptr("regulators"),\
	.id = MAX77541_BUCK##_id,			\
	.ops = &max77541_buck_ops,			\
	.type = REGULATOR_VOLTAGE,			\
	.n_voltages = 0x75,				\
	.linear_ranges = max77541_buck_ranges,	\
	.n_linear_ranges = 1,			\
	.vsel_reg = MAX77541_BUCK_VOUT_##_id,	\
	.vsel_mask = 0x7F,				\
	.enable_reg = MAX77541_EN_CTRL,		\
	.enable_mask = BIT(_id),			\
	.owner = THIS_MODULE,			\
}

static const struct regulator_desc max77541_regulators_desc[] = {
	MAX77541_BUCK(1),
	MAX77541_BUCK(2),
};

static int max77541_regulator_probe(struct platform_device *pdev)
{
	struct max77541 *max77541 = dev_get_drvdata(pdev->dev.parent);
	struct max77541_regulator *regulator;
	struct regulator_config config = {};
	struct regulator_dev *rdev;
	int i;

	regulator = devm_kzalloc(&pdev->dev, sizeof(*regulator), GFP_KERNEL);
	if (!regulator)
		return -ENOMEM;

	regulator->dev = &pdev->dev;
	regulator->regmap = max77541->regmap;  // Get parent's regmap

	config.dev = &pdev->dev;
	config.dev->of_node = pdev->dev.parent->of_node;  // Use parent DT node
	config.regmap = regulator->regmap;

	for (i = 0; i < ARRAY_SIZE(max77541_regulators_desc); i++) {
		rdev = devm_regulator_register(&pdev->dev,
					       &max77541_regulators_desc[i],
					       &config);
		if (IS_ERR(rdev))
			return PTR_ERR(rdev);
	}

	return 0;
}

static struct platform_driver max77541_regulator_driver = {
	.driver = {
		.name = "max77541-regulator",
	},
	.probe = max77541_regulator_probe,
};
module_platform_driver(max77541_regulator_driver);
```

**Key MFD Patterns**:
1. **Parent driver**: Creates regmap, registers MFD cells
2. **Child driver**: Platform driver, gets regmap from parent via `dev_get_drvdata(pdev->dev.parent)`
3. **DT node sharing**: Child uses parent's of_node: `config.dev->of_node = pdev->dev.parent->of_node`

## Complete Standalone Example

```c
// drivers/regulator/adp5055-regulator.c
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/regmap.h>
#include <linux/regulator/driver.h>
#include <linux/regulator/of_regulator.h>

#define ADP5055_CTRL123	0xD1
#define ADP5055_VID0		0xD8
#define ADP5055_VID1		0xD9
#define ADP5055_VID2		0xDA

#define ADP5055_MIN_VOUT	408000
#define ADP5055_NUM_CH	3

struct adp5055 {
	struct device *dev;
	struct regmap *regmap;
};

static const struct regmap_config adp5055_regmap_config = {
	.reg_bits = 8,
	.val_bits = 8,
	.max_register = 0xE0,
};

static const struct linear_range adp5055_voltage_ranges[] = {
	REGULATOR_LINEAR_RANGE(ADP5055_MIN_VOUT, 0, 255, 1500),
};

static int adp5055_of_parse_cb(struct device_node *np,
			       const struct regulator_desc *desc,
			       struct regulator_config *config)
{
	// Parse custom devicetree properties
	// config->ena_gpiod is already parsed by framework
	return 0;
}

static const struct regulator_ops adp5055_regulator_ops = {
	.list_voltage = regulator_list_voltage_linear_range,
	.map_voltage = regulator_map_voltage_linear_range,
	.set_voltage_sel = regulator_set_voltage_sel_regmap,
	.get_voltage_sel = regulator_get_voltage_sel_regmap,
	.enable = regulator_enable_regmap,
	.disable = regulator_disable_regmap,
	.is_enabled = regulator_is_enabled_regmap,
};

#define ADP5055_REGULATOR_DESC(_id, _name) \
{									\
	.name = (_name),						\
	.of_match = of_match_ptr("vout" #_id),			\
	.regulators_node = of_match_ptr("regulators"),		\
	.id = (_id),							\
	.ops = &adp5055_regulator_ops,				\
	.type = REGULATOR_VOLTAGE,					\
	.n_voltages = 256,						\
	.linear_ranges = adp5055_voltage_ranges,			\
	.n_linear_ranges = ARRAY_SIZE(adp5055_voltage_ranges),	\
	.vsel_reg = ADP5055_VID0 + (_id),				\
	.vsel_mask = 0xFF,						\
	.enable_reg = ADP5055_CTRL123,				\
	.enable_mask = BIT(_id),					\
	.owner = THIS_MODULE,					\
	.of_parse_cb = adp5055_of_parse_cb,				\
}

static const struct regulator_desc adp5055_regulators_desc[] = {
	ADP5055_REGULATOR_DESC(0, "VOUT0"),
	ADP5055_REGULATOR_DESC(1, "VOUT1"),
	ADP5055_REGULATOR_DESC(2, "VOUT2"),
};

static int adp5055_probe(struct i2c_client *client)
{
	struct adp5055 *adp5055;
	struct regulator_config config = {};
	struct regulator_dev *rdev;
	int i;

	adp5055 = devm_kzalloc(&client->dev, sizeof(*adp5055), GFP_KERNEL);
	if (!adp5055)
		return -ENOMEM;

	adp5055->dev = &client->dev;
	adp5055->regmap = devm_regmap_init_i2c(client, &adp5055_regmap_config);
	if (IS_ERR(adp5055->regmap))
		return PTR_ERR(adp5055->regmap);

	config.dev = &client->dev;
	config.regmap = adp5055->regmap;

	for (i = 0; i < ARRAY_SIZE(adp5055_regulators_desc); i++) {
		rdev = devm_regulator_register(&client->dev,
					       &adp5055_regulators_desc[i],
					       &config);
		if (IS_ERR(rdev))
			return dev_err_probe(&client->dev, PTR_ERR(rdev),
					     "Failed to register regulator %d\n", i);
	}

	return 0;
}

static const struct of_device_id adp5055_of_match[] = {
	{ .compatible = "adi,adp5055" },
	{}
};
MODULE_DEVICE_TABLE(of, adp5055_of_match);

static struct i2c_driver adp5055_driver = {
	.driver = {
		.name = "adp5055-regulator",
		.of_match_table = adp5055_of_match,
	},
	.probe = adp5055_probe,
};
module_i2c_driver(adp5055_driver);

MODULE_AUTHOR("Analog Devices");
MODULE_DESCRIPTION("ADP5055 Regulator Driver");
MODULE_LICENSE("GPL");
```

## Regulator Consumer API

### Device Drivers Using Regulators

```c
struct regulator *vdd_reg;
struct regulator *vio_reg;

// Get regulators
vdd_reg = devm_regulator_get(dev, "vdd");
if (IS_ERR(vdd_reg))
	return PTR_ERR(vdd_reg);

vio_reg = devm_regulator_get_optional(dev, "vio");
if (IS_ERR(vio_reg) && PTR_ERR(vio_reg) != -ENODEV)
	return PTR_ERR(vio_reg);

// Set voltage
regulator_set_voltage(vdd_reg, 3300000, 3300000);  // 3.3V

// Enable
regulator_enable(vdd_reg);

// Disable
regulator_disable(vdd_reg);

// Get current voltage
int uV = regulator_get_voltage(vdd_reg);
```

## Devicetree Bindings

### Standalone Regulator

```yaml
# Documentation/devicetree/bindings/regulator/adi,adp5055.yaml
properties:
  compatible:
    const: adi,adp5055

  reg:
    maxItems: 1

  regulators:
    type: object
    patternProperties:
      "^vout[0-2]$":
        type: object
        $ref: /schemas/regulator/regulator.yaml#

# DTS
adp5055@50 {
	compatible = "adi,adp5055";
	reg = <0x50>;

	regulators {
		vout0 {
			regulator-name = "vdd_cpu";
			regulator-min-microvolt = <408000>;
			regulator-max-microvolt = <790500>;
			regulator-boot-on;
			regulator-always-on;
		};

		vout1 {
			regulator-name = "vdd_ddr";
			regulator-min-microvolt = <500000>;
			regulator-max-microvolt = <750000>;
		};
	};
};
```

### MFD Regulator

```dts
max77541@48 {
	compatible = "adi,max77541";
	reg = <0x48>;

	regulators {
		buck1 {
			regulator-name = "vdd_core";
			regulator-min-microvolt = <500000>;
			regulator-max-microvolt = <1075000>;
			regulator-boot-on;
		};

		buck2 {
			regulator-name = "vdd_io";
			regulator-min-microvolt = <500000>;
			regulator-max-microvolt = <1075000>;
		};
	};
};
```

## Best Practices

### 1. Use Linear Ranges

```c
// Preferred
static const struct linear_range voltage_ranges[] = {
	REGULATOR_LINEAR_RANGE(500000, 0, 100, 10000),
};

// Avoid deprecated patterns
.min_uV = 500000,
.uV_step = 10000,
.linear_min_sel = 0,
```

### 2. Use Macro Definitions

```c
// Maintainable
#define MY_REGULATOR_DESC(_id) { ... }

// Avoid copy-paste
{ .name = "VOUT0", .id = 0, ... },
{ .name = "VOUT1", .id = 1, ... },
{ .name = "VOUT2", .id = 2, ... },
```

### 3. Use REGMAP Helpers

```c
static const struct regulator_ops my_ops = {
	.set_voltage_sel = regulator_set_voltage_sel_regmap,  // Helper
	.get_voltage_sel = regulator_get_voltage_sel_regmap,  // Helper
	.enable = regulator_enable_regmap,                     // Helper
	.disable = regulator_disable_regmap,                   // Helper
	.is_enabled = regulator_is_enabled_regmap,            // Helper
};
```

### 4. MFD Structure

- **Parent MFD driver**: I2C/SPI driver, creates regmap, registers cells
- **Child regulator driver**: Platform driver, gets regmap from parent
- **Share DT node**: Child uses parent's of_node

## Related Skills

- **linux-hwmon**: Hardware monitoring (voltage/current sensing)
- **linux-pmbus**: PMBus power management
- **linux-devicetree**: Regulator bindings
