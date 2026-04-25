# Multi-Page Device Support

Detailed guide for implementing multi-page PMBus devices (power sequencers, multi-rail PMICs). Covers page management, per-page functionality, and page switching.

## What Are Multi-Page Devices?

Multi-page PMBus devices provide multiple voltage rails (outputs) controlled through a single I2C address. Each "page" represents an independent voltage regulator or monitor.

**Common multi-page devices**:
- **LTC2978**: 8-channel voltage supervisor
- **LTC2974**: 4-channel voltage regulator with monitoring
- **ADM1266**: 17-channel power sequencer and monitor
- **LTC7106**: Multi-phase buck controller (6 phases)

## PAGE Command

PMBus uses the PAGE command (0x00) to select the active rail:

```c
// PAGE command format
i2c_smbus_write_byte_data(client, PMBUS_PAGE, page_number);

// Now subsequent commands operate on selected page
i2c_smbus_read_word_data(client, PMBUS_READ_VOUT);  // Reads VOUT for selected page
```

The PMBus core automatically handles page switching when you use the `page` parameter:

```c
// Core automatically switches to page 2 before reading
ret = pmbus_read_word_data(client, 2, 0xff, PMBUS_READ_VOUT);
```

## Basic Multi-Page Driver

ADM1266 power sequencer with 17 voltage monitors:

```c
#include <linux/i2c.h>
#include <linux/module.h>
#include "pmbus.h"

struct adm1266_data {
	struct pmbus_driver_info info;
};

static int adm1266_probe(struct i2c_client *client)
{
	struct adm1266_data *data;
	int i;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	// Configure 17 pages (voltage monitors)
	data->info.pages = 17;
	data->info.format[PSC_VOLTAGE_OUT] = linear;

	// Each page monitors VOUT with status
	for (i = 0; i < data->info.pages; i++)
		data->info.func[i] = PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT;

	return pmbus_do_probe(client, &data->info);
}

static const struct i2c_device_id adm1266_id[] = {
	{ "adm1266", 0 },
	{}
};
MODULE_DEVICE_TABLE(i2c, adm1266_id);

static const struct of_device_id adm1266_of_match[] = {
	{ .compatible = "adi,adm1266" },
	{}
};
MODULE_DEVICE_TABLE(of, adm1266_of_match);

static struct i2c_driver adm1266_driver = {
	.driver = {
		.name = "adm1266",
		.of_match_table = adm1266_of_match,
	},
	.probe = adm1266_probe,
	.id_table = adm1266_id,
};
module_i2c_driver(adm1266_driver);

MODULE_LICENSE("GPL");
MODULE_IMPORT_NS(PMBUS);
```

## Per-Page Functionality

Different pages can have different capabilities:

```c
static int ltc2974_probe(struct i2c_client *client)
{
	struct pmbus_driver_info *info;
	int i;

	info = devm_kzalloc(&client->dev, sizeof(*info), GFP_KERNEL);
	if (!info)
		return -ENOMEM;

	info->pages = 4;
	info->format[PSC_VOLTAGE_IN] = linear;
	info->format[PSC_VOLTAGE_OUT] = linear;
	info->format[PSC_CURRENT_OUT] = linear;
	info->format[PSC_TEMPERATURE] = linear;

	// Page 0: VIN, VOUT, IOUT, TEMP monitoring
	info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_STATUS_INPUT |
	                PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT |
	                PMBUS_HAVE_IOUT | PMBUS_HAVE_STATUS_IOUT |
	                PMBUS_HAVE_TEMP | PMBUS_HAVE_STATUS_TEMP;

	// Pages 1-3: VOUT and IOUT only
	for (i = 1; i < info->pages; i++)
		info->func[i] = PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT |
		                PMBUS_HAVE_IOUT | PMBUS_HAVE_STATUS_IOUT;

	return pmbus_do_probe(client, info);
}
```

## LTC2978: 8-Channel Supervisor

Full implementation with VIN sharing and per-page VOUT:

```c
struct ltc2978_data {
	enum chips id;
	u16 vin_min, vin_max;
	u16 vout_min[8], vout_max[8];
	u16 temp_min, temp_max;
	struct pmbus_driver_info info;
};

#define to_ltc2978_data(x)  container_of(x, struct ltc2978_data, info)

static int ltc2978_read_word_data(struct i2c_client *client, int page,
                                  int phase, int reg)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ltc2978_data *data = to_ltc2978_data(info);
	int ret;

	switch (reg) {
	case PMBUS_VIRT_READ_VIN_MAX:
		// VIN is shared across all pages
		ret = pmbus_read_word_data(client, 0, 0xff, LTC2978_MFR_VIN_PEAK);
		if (ret >= 0) {
			if (lin11_to_val(ret) > lin11_to_val(data->vin_max))
				data->vin_max = ret;
			ret = data->vin_max;
		}
		break;

	case PMBUS_VIRT_READ_VOUT_MAX:
		// VOUT is per-page
		ret = pmbus_read_word_data(client, page, 0xff, LTC2978_MFR_VOUT_PEAK);
		if (ret >= 0) {
			if (ret > data->vout_max[page])
				data->vout_max[page] = ret;
			ret = data->vout_max[page];
		}
		break;

	case PMBUS_VIRT_RESET_VOUT_HISTORY:
	case PMBUS_VIRT_RESET_VIN_HISTORY:
		ret = 0;
		break;

	default:
		ret = -ENODATA;
		break;
	}

	return ret;
}

static int ltc2978_write_word_data(struct i2c_client *client, int page,
                                   int reg, u16 word)
{
	const struct pmbus_driver_info *info = pmbus_get_driver_info(client);
	struct ltc2978_data *data = to_ltc2978_data(info);
	int ret;

	switch (reg) {
	case PMBUS_VIRT_RESET_VOUT_HISTORY:
		// Reset for specific page
		data->vout_min[page] = 0xffff;
		data->vout_max[page] = 0;
		ret = pmbus_write_byte(client, page, PMBUS_CLEAR_FAULTS);
		break;

	case PMBUS_VIRT_RESET_VIN_HISTORY:
		// VIN is shared, reset for all pages
		data->vin_min = 0x7bff;
		data->vin_max = 0x7c00;
		ret = pmbus_write_byte(client, page, PMBUS_CLEAR_FAULTS);
		break;

	default:
		ret = -ENODATA;
		break;
	}

	return ret;
}

static int ltc2978_probe(struct i2c_client *client)
{
	struct ltc2978_data *data;
	struct pmbus_driver_info *info;
	int i;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	info = &data->info;

	info->pages = 8;
	info->format[PSC_VOLTAGE_IN] = linear;
	info->format[PSC_VOLTAGE_OUT] = linear;
	info->format[PSC_TEMPERATURE] = linear;

	info->read_word_data = ltc2978_read_word_data;
	info->write_word_data = ltc2978_write_word_data;

	// Page 0: VIN, VOUT, TEMP
	info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_STATUS_INPUT |
	                PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT |
	                PMBUS_HAVE_TEMP | PMBUS_HAVE_STATUS_TEMP;

	// Pages 1-7: VOUT only
	for (i = 1; i < info->pages; i++)
		info->func[i] = PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT;

	return pmbus_do_probe(client, info);
}
```

## Sysfs Interface for Multi-Page Devices

Multi-page devices create numbered attributes:

```bash
cd /sys/class/hwmon/hwmon*/device/

# Shared input (page 0)
cat in0_input       # VIN (shared across all pages)

# Per-page outputs
cat in1_input       # VOUT page 0
cat in2_input       # VOUT page 1
cat in3_input       # VOUT page 2
cat in4_input       # VOUT page 3

# Per-page current
cat curr1_input     # IOUT page 0
cat curr2_input     # IOUT page 1

# Per-page status
cat in1_alarm       # VOUT page 0 alarm
cat in2_alarm       # VOUT page 1 alarm
```

## Page Broadcast

Some devices support page broadcast (0xff = all pages):

```c
// Write VOUT_COMMAND to all pages simultaneously
ret = pmbus_write_word_data(client, 0xff, PMBUS_VOUT_COMMAND, 0x3000);
```

**Note**: Not all devices support broadcast. Check datasheet.

## Page Switching Optimization

The PMBus core caches the current page to avoid redundant PAGE writes:

```c
// Core automatically optimizes:
pmbus_read_word_data(client, 2, 0xff, PMBUS_READ_VOUT);  // Switches to page 2
pmbus_read_word_data(client, 2, 0xff, PMBUS_READ_IOUT);  // No page switch (already on 2)
pmbus_read_word_data(client, 3, 0xff, PMBUS_READ_VOUT);  // Switches to page 3
```

## Multi-Phase Support

Some pages support multi-phase operation (e.g., multi-phase buck converters):

```c
struct pmbus_driver_info info = {
	.pages = 1,           // Single output
	.phases[0] = 6,       // 6 phases on page 0
	.format[PSC_VOLTAGE_OUT] = linear,
	.format[PSC_CURRENT_OUT] = linear,
	.func[0] = PMBUS_HAVE_VOUT | PMBUS_HAVE_IOUT,
};
```

Read per-phase current:

```c
// Read phase 0 current
ret = pmbus_read_word_data(client, 0, 0, PMBUS_READ_IOUT);

// Read total current (sum of all phases)
ret = pmbus_read_word_data(client, 0, 0xff, PMBUS_READ_IOUT);
```

## Common Patterns

### Shared VIN, Per-Page VOUT

```c
// Page 0 has VIN
info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_VOUT;

// Pages 1+ have VOUT only
for (i = 1; i < info->pages; i++)
	info->func[i] = PMBUS_HAVE_VOUT;
```

### Independent Regulators

```c
// Each page has full functionality
for (i = 0; i < info->pages; i++) {
	info->func[i] = PMBUS_HAVE_VIN | PMBUS_HAVE_VOUT |
	                PMBUS_HAVE_IIN | PMBUS_HAVE_IOUT |
	                PMBUS_HAVE_PIN | PMBUS_HAVE_POUT |
	                PMBUS_HAVE_TEMP;
}
```

### Monitor-Only Pages

```c
// Voltage monitoring without control
for (i = 0; i < info->pages; i++)
	info->func[i] = PMBUS_HAVE_VMON | PMBUS_HAVE_STATUS_VOUT;
```

## Devicetree Example

Multi-page devices don't require special devicetree properties:

```dts
&i2c0 {
	ltc2978@5c {
		compatible = "lltc,ltc2978";
		reg = <0x5c>;
		// PMBus core handles 8 pages automatically
	};

	adm1266@42 {
		compatible = "adi,adm1266";
		reg = <0x42>;
		// 17 pages detected automatically
	};
};
```

## Debugging Multi-Page Devices

### Check Page Count

```bash
# Count number of VOUT attributes (= number of pages)
ls /sys/class/hwmon/hwmon*/device/in*_label | wc -l
```

### Verify Page Switching

Enable PMBus core debug:

```bash
echo 'file pmbus_core.c +p' > /sys/kernel/debug/dynamic_debug/control
dmesg | grep -i "page"

# Should see:
# pmbus: switching to page 0
# pmbus: switching to page 1
# ...
```

### I2C Tracing

```bash
echo 1 > /sys/kernel/debug/tracing/events/i2c/enable
cat /sys/kernel/debug/tracing/trace | grep PMBUS_PAGE

# You should see:
# i2c_write: i2c-0 #0 a=05c f=0000 l=2 [00-02]  # PAGE=2
# i2c_read:  i2c-0 #0 a=05c f=0001 l=2 [...]    # Read data
```

## Page vs Phase Confusion

**Important distinction**:
- **Pages**: Different voltage rails (VOUT1, VOUT2, VOUT3)
- **Phases**: Multiple phases powering the same rail (for high current)

```c
// 4 independent voltage rails (4 pages)
info->pages = 4;

// Page 0 has 6 phases (high-current output)
info->phases[0] = 6;
```
