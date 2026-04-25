# PMBus Driver Implementation

Detailed guide for implementing PMBus device drivers, covering probe functions, identify callbacks, device-specific quirks, and the pmbus_driver_info structure.

## Basic PMBus Driver Pattern

Simple PMBus device using standard linear format:

```c
// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * Hardware monitoring driver for Example PMBus DC-DC Converter
 *
 * Copyright (c) 2024 Analog Devices Inc.
 */

#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/of.h>
#include "pmbus.h"

static struct pmbus_driver_info example_info = {
	.pages = 1,
	.format[PSC_VOLTAGE_IN] = linear,
	.format[PSC_VOLTAGE_OUT] = linear,
	.format[PSC_CURRENT_OUT] = linear,
	.format[PSC_TEMPERATURE] = linear,
	.func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_STATUS_INPUT |
	           PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT |
	           PMBUS_HAVE_IOUT | PMBUS_HAVE_STATUS_IOUT |
	           PMBUS_HAVE_TEMP | PMBUS_HAVE_STATUS_TEMP,
};

static int example_probe(struct i2c_client *client)
{
	return pmbus_do_probe(client, &example_info);
}

static const struct i2c_device_id example_id[] = {
	{ "example_pmbus", 0 },
	{}
};
MODULE_DEVICE_TABLE(i2c, example_id);

static const struct of_device_id example_of_match[] = {
	{ .compatible = "example,pmbus" },
	{}
};
MODULE_DEVICE_TABLE(of, example_of_match);

static struct i2c_driver example_driver = {
	.driver = {
		.name = "example_pmbus",
		.of_match_table = example_of_match,
	},
	.probe = example_probe,
	.id_table = example_id,
};
module_i2c_driver(example_driver);

MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("PMBus driver for Example Device");
MODULE_LICENSE("GPL");
MODULE_IMPORT_NS(PMBUS);
```

## Direct Format with Coefficients

ADM1275 hot-swap controller using direct format with coefficient calculation:

```c
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/of.h>
#include "pmbus.h"

#define ADM1275_PMON_CONFIG		0xD4
#define ADM1275_VRANGE			BIT(0)
#define ADM1275_PEAK_IOUT		0xD0
#define ADM1275_PEAK_VIN		0xD1

struct coefficients {
	s16 m;  // Multiplier
	s16 b;  // Offset
	s16 R;  // Exponent
};

// Coefficients for different voltage/current ranges
static const struct coefficients adm1275_coefficients[] = {
	[0] = { 19199, 0, -2 },   // Voltage, VRANGE set (0-60V)
	[1] = { 6720, 0, -1 },    // Voltage, VRANGE not set (0-20V)
	[2] = { 807, 20475, -1 }, // Current (before shunt scaling)
};

struct adm1275_data {
	int id;
	bool have_pin_max;
	bool have_power_sampling;
	struct pmbus_driver_info info;
};

#define to_adm1275_data(x)  container_of(x, struct adm1275_data, info)

static int adm1275_read_word_data(struct i2c_client *client, int page,
                                  int phase, int reg)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	const struct adm1275_data *data = to_adm1275_data(info);
	int ret = 0;

	if (page > 0)
		return -ENXIO;

	switch (reg) {
	case PMBUS_VIRT_READ_IOUT_MAX:
		ret = pmbus_read_word_data(client, 0, 0xff, ADM1275_PEAK_IOUT);
		break;
	case PMBUS_VIRT_READ_VIN_MAX:
		ret = pmbus_read_word_data(client, 0, 0xff, ADM1275_PEAK_VIN);
		break;
	case PMBUS_VIRT_RESET_IOUT_HISTORY:
	case PMBUS_VIRT_RESET_VIN_HISTORY:
		ret = 0;
		break;
	default:
		ret = -ENODATA;
		break;
	}

	return ret;
}

static int adm1275_write_word_data(struct i2c_client *client, int page,
                                   int reg, u16 word)
{
	int ret;

	switch (reg) {
	case PMBUS_VIRT_RESET_IOUT_HISTORY:
		ret = pmbus_write_word_data(client, 0, ADM1275_PEAK_IOUT, 0);
		break;
	case PMBUS_VIRT_RESET_VIN_HISTORY:
		ret = pmbus_write_word_data(client, 0, ADM1275_PEAK_VIN, 0);
		break;
	default:
		ret = -ENODATA;
		break;
	}

	return ret;
}

static int adm1275_probe(struct i2c_client *client)
{
	struct adm1275_data *data;
	struct pmbus_driver_info *info;
	int config, vindex, cindex;
	u32 shunt;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	info = &data->info;
	info->pages = 1;
	info->format[PSC_VOLTAGE_IN] = direct;
	info->format[PSC_VOLTAGE_OUT] = direct;
	info->format[PSC_CURRENT_OUT] = direct;
	info->format[PSC_POWER] = direct;

	info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_VOUT |
	                PMBUS_HAVE_IOUT | PMBUS_HAVE_PIN;

	info->read_word_data = adm1275_read_word_data;
	info->write_word_data = adm1275_write_word_data;

	// Read device configuration
	config = i2c_smbus_read_byte_data(client, ADM1275_PMON_CONFIG);
	if (config < 0)
		return config;

	// Read shunt resistor from devicetree
	if (of_property_read_u32(client->dev.of_node,
	                         "shunt-resistor-micro-ohms", &shunt))
		shunt = 1000; // Default: 1 mOhm

	// Select coefficients based on VRANGE bit
	vindex = (config & ADM1275_VRANGE) ? 0 : 1;
	cindex = 2;

	// Voltage coefficients
	info->m[PSC_VOLTAGE_IN] = adm1275_coefficients[vindex].m;
	info->b[PSC_VOLTAGE_IN] = adm1275_coefficients[vindex].b;
	info->R[PSC_VOLTAGE_IN] = adm1275_coefficients[vindex].R;

	info->m[PSC_VOLTAGE_OUT] = adm1275_coefficients[vindex].m;
	info->b[PSC_VOLTAGE_OUT] = adm1275_coefficients[vindex].b;
	info->R[PSC_VOLTAGE_OUT] = adm1275_coefficients[vindex].R;

	// Current coefficients: scale by shunt resistor value
	// Current = Vsense / Rshunt, so m scales with shunt value
	info->m[PSC_CURRENT_OUT] = adm1275_coefficients[cindex].m * shunt / 1000;
	info->b[PSC_CURRENT_OUT] = adm1275_coefficients[cindex].b;
	info->R[PSC_CURRENT_OUT] = adm1275_coefficients[cindex].R;

	// Power coefficients (derived from V and I coefficients)
	// P = V * I, so m_power = m_voltage * m_current
	info->m[PSC_POWER] = info->m[PSC_VOLTAGE_IN] * info->m[PSC_CURRENT_OUT];
	info->b[PSC_POWER] = 0;
	info->R[PSC_POWER] = info->R[PSC_VOLTAGE_IN] + info->R[PSC_CURRENT_OUT];

	return pmbus_do_probe(client, info);
}

static const struct i2c_device_id adm1275_id[] = {
	{ "adm1275", 0 },
	{}
};
MODULE_DEVICE_TABLE(i2c, adm1275_id);

static const struct of_device_id adm1275_of_match[] = {
	{ .compatible = "adi,adm1275" },
	{}
};
MODULE_DEVICE_TABLE(of, adm1275_of_match);

static struct i2c_driver adm1275_driver = {
	.driver = {
		.name = "adm1275",
		.of_match_table = adm1275_of_match,
	},
	.probe = adm1275_probe,
	.id_table = adm1275_id,
};
module_i2c_driver(adm1275_driver);

MODULE_AUTHOR("Analog Devices Inc.");
MODULE_DESCRIPTION("PMBus driver for ADM1275 Hot Swap Controller");
MODULE_LICENSE("GPL");
MODULE_IMPORT_NS(PMBUS);
```

## Using identify() Callback

The `identify()` callback allows runtime device detection and configuration:

```c
static int ltc2978_identify(struct i2c_client *client,
                            struct pmbus_driver_info *info)
{
	int ret;
	u8 id;

	// Read manufacturer-specific ID register
	ret = i2c_smbus_read_byte_data(client, LTC2978_MFR_SPECIAL_ID);
	if (ret < 0)
		return ret;

	id = ret;

	switch (id) {
	case LTC2974_ID:
		info->pages = 4;
		info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_STATUS_INPUT |
		                PMBUS_HAVE_TEMP2;
		for (i = 0; i < info->pages; i++)
			info->func[i] |= PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT;
		break;

	case LTC2978_ID:
		info->pages = 8;
		info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_STATUS_INPUT |
		                PMBUS_HAVE_TEMP | PMBUS_HAVE_STATUS_TEMP;
		for (i = 1; i < info->pages; i++)
			info->func[i] = PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT;
		break;

	default:
		dev_err(&client->dev, "Unknown chip ID 0x%02x\n", id);
		return -ENODEV;
	}

	return 0;
}

static struct pmbus_driver_info ltc2978_info = {
	.pages = 8,  // Maximum, refined by identify()
	.format[PSC_VOLTAGE_IN] = linear,
	.format[PSC_VOLTAGE_OUT] = linear,
	.format[PSC_TEMPERATURE] = linear,
	.identify = ltc2978_identify,
};

static int ltc2978_probe(struct i2c_client *client)
{
	return pmbus_do_probe(client, &ltc2978_info);
}
```

## Coefficient Calculation Formula

The direct format conversion is:

```
real_value = (register_value * m - b) * 10^R
```

**Example**: ADM1275 with VRANGE=1 (60V range)
- m = 19199
- b = 0
- R = -2
- Register reads 0x1234 (4660 decimal)

```
voltage = (4660 * 19199 - 0) * 10^-2
        = 89447340 * 0.01
        = 894473.4 mV
        = 894.47 V
```

**Shunt resistor scaling** for current measurements:
```c
// Current = Vsense / Rshunt
// If datasheet assumes 1 mOhm, but actual shunt is 2 mOhm:
m_actual = m_datasheet * shunt_actual_uohm / 1000
```

## Handling Chip Variants

Use chip ID or devicetree compatible to handle variants:

```c
enum chips { adm1275, adm1276, adm1278, adm1293, adm1294 };

static const struct i2c_device_id adm1275_id[] = {
	{ "adm1275", adm1275 },
	{ "adm1276", adm1276 },
	{ "adm1278", adm1278 },
	{ "adm1293", adm1293 },
	{ "adm1294", adm1294 },
	{}
};

struct adm1275_data {
	enum chips id;
	bool have_pin_max;
	bool have_iout_min;
	struct pmbus_driver_info info;
};

static int adm1275_probe(struct i2c_client *client)
{
	struct adm1275_data *data;
	const struct i2c_device_id *mid;

	mid = i2c_match_id(adm1275_id, client);

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	data->id = mid->driver_data;

	// Variant-specific features
	switch (data->id) {
	case adm1275:
		data->have_pin_max = false;
		data->have_iout_min = false;
		break;
	case adm1276:
	case adm1278:
		data->have_pin_max = true;
		data->have_iout_min = false;
		break;
	case adm1293:
	case adm1294:
		data->have_pin_max = true;
		data->have_iout_min = true;
		break;
	}

	// Configure info based on variant
	// ...

	return pmbus_do_probe(client, &data->info);
}
```

## Busy-Wait for Complex Devices

Some devices (LT7170, LTC3883) require polling before I2C access:

```c
#define LTC_POLL_TIMEOUT  100  // ms

static int ltc_wait_ready(struct i2c_client *client)
{
	unsigned long timeout = jiffies + msecs_to_jiffies(LTC_POLL_TIMEOUT);
	int status;

	do {
		status = pmbus_read_byte_data(client, 0, LTC2978_MFR_COMMON);
		if (status == -EBADMSG || status == -ENXIO) {
			// PEC error or NACK: chip busy
			usleep_range(50, 100);
			continue;
		}
		if (status < 0)
			return status;

		if ((status & (LTC_NOT_BUSY | LTC_NOT_PENDING)) ==
		    (LTC_NOT_BUSY | LTC_NOT_PENDING))
			return 0;

		usleep_range(50, 100);
	} while (time_before(jiffies, timeout));

	return -ETIMEDOUT;
}

static int ltc_read_word_data(struct i2c_client *client, int page,
                              int phase, int reg)
{
	int ret;

	ret = ltc_wait_ready(client);
	if (ret < 0)
		return ret;

	return pmbus_read_word_data(client, page, 0xff, reg);
}
```

## IEEE 754 Format Support

LT7170/LT7171 use IEEE 754 single-precision floating point:

```c
static struct pmbus_driver_info lt7170_info = {
	.pages = 1,
	.format[PSC_VOLTAGE_IN] = ieee754,
	.format[PSC_VOLTAGE_OUT] = ieee754,
	.format[PSC_CURRENT_IN] = ieee754,
	.format[PSC_CURRENT_OUT] = ieee754,
	.format[PSC_POWER] = ieee754,
	.format[PSC_TEMPERATURE] = ieee754,
	.func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_VOUT |
	           PMBUS_HAVE_IIN | PMBUS_HAVE_IOUT |
	           PMBUS_HAVE_PIN | PMBUS_HAVE_POUT |
	           PMBUS_HAVE_TEMP | PMBUS_HAVE_STATUS_VOUT |
	           PMBUS_HAVE_STATUS_IOUT | PMBUS_HAVE_STATUS_TEMP,
};
```

The PMBus core automatically converts IEEE 754 to/from kernel integer representation.
