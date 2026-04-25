# HWMON Driver Implementation Guide

Complete guide to implementing HWMON (Hardware Monitoring) drivers in the Linux kernel.

## Core Structures

### struct hwmon_ops

Defines the callback functions for hardware access:

```c
#include <linux/hwmon.h>

struct hwmon_ops {
	/**
	 * is_visible - Determine attribute file permissions
	 *
	 * @drvdata: Driver private data passed during registration
	 * @type: Sensor type (temp, voltage, current, etc.)
	 * @attr: Specific attribute (input, min, max, alarm, etc.)
	 * @channel: Channel number (0-based)
	 *
	 * Returns: File mode (0 = hidden, 0444 = read-only, 0644 = read-write)
	 *
	 * Called once during registration for each potential attribute.
	 * Determines which attributes to create and their permissions.
	 */
	umode_t (*is_visible)(const void *drvdata, enum hwmon_sensor_types type,
			      u32 attr, int channel);

	/**
	 * read - Read sensor value
	 *
	 * @dev: Device structure
	 * @type: Sensor type
	 * @attr: Attribute being read
	 * @channel: Channel number
	 * @val: Output value pointer
	 *
	 * Returns: 0 on success, negative errno on error
	 *
	 * Called when userspace reads an attribute file.
	 * Must convert hardware value to standard units.
	 */
	int (*read)(struct device *dev, enum hwmon_sensor_types type,
		    u32 attr, int channel, long *val);

	/**
	 * read_string - Read string attribute (labels)
	 *
	 * @dev: Device structure
	 * @type: Sensor type
	 * @attr: Attribute being read
	 * @channel: Channel number
	 * @str: Output string pointer
	 *
	 * Returns: 0 on success, negative errno on error
	 *
	 * Optional. Used for reading channel labels.
	 */
	int (*read_string)(struct device *dev, enum hwmon_sensor_types type,
			   u32 attr, int channel, const char **str);

	/**
	 * write - Write sensor value
	 *
	 * @dev: Device structure
	 * @type: Sensor type
	 * @attr: Attribute being written
	 * @channel: Channel number
	 * @val: Input value
	 *
	 * Returns: 0 on success, negative errno on error
	 *
	 * Called when userspace writes to a writable attribute.
	 * Must convert from standard units to hardware value.
	 */
	int (*write)(struct device *dev, enum hwmon_sensor_types type,
		     u32 attr, int channel, long val);
};
```

### struct hwmon_channel_info

Describes a group of channels of the same type:

```c
/**
 * struct hwmon_channel_info - Channel information
 * @type: Sensor type
 * @config: Pointer to 0-terminated array of channel attribute configurations
 *
 * Each element in config describes one channel's attributes using bitmask.
 */
struct hwmon_channel_info {
	enum hwmon_sensor_types type;
	const u32 *config;
};

// Helper macro for static channel info
#define HWMON_CHANNEL_INFO(stype, ...)  \
	(&(struct hwmon_channel_info) { \
		.type = hwmon_##stype,  \
		.config = (const u32 []) {  \
			__VA_ARGS__, 0  \
		}  \
	})
```

### struct hwmon_chip_info

Complete chip description:

```c
/**
 * struct hwmon_chip_info - Chip configuration
 * @ops: Pointer to hwmon operations
 * @info: NULL-terminated array of channel info pointers
 */
struct hwmon_chip_info {
	const struct hwmon_ops *ops;
	const struct hwmon_channel_info * const *info;
};
```

## Complete Implementation Example

Based on SHT4x temperature/humidity sensor (drivers/hwmon/sht4x.c):

```c
#include <linux/hwmon.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/jiffies.h>

#define SHT4X_MIN_POLL_INTERVAL	2000  // 2 seconds

/**
 * struct sht4x_data - Driver private data
 * @client: I2C client
 * @lock: Mutex for atomic updates
 * @valid: Data validity flag
 * @update_interval: Minimum polling interval (milliseconds)
 * @last_updated: Last update time (jiffies)
 * @temperature: Cached temperature (millidegrees C)
 * @humidity: Cached humidity (milli-percent)
 */
struct sht4x_data {
	struct i2c_client	*client;
	struct mutex		lock;
	bool			valid;
	long			update_interval;
	long			last_updated;
	s32			temperature;
	s32			humidity;
};

/**
 * sht4x_read_values - Read and cache sensor values
 *
 * Returns: 0 on success, negative errno on error
 *
 * This function implements cached reading with configurable update interval.
 * Only performs I2C transaction if cache is invalid or expired.
 */
static int sht4x_read_values(struct sht4x_data *data)
{
	unsigned long next_update;
	int ret;
	u16 t_ticks, rh_ticks;
	u8 cmd = SHT4X_CMD_MEASURE;
	u8 raw_data[6];

	mutex_lock(&data->lock);

	// Check if cached data is still valid
	next_update = data->last_updated +
		      msecs_to_jiffies(data->update_interval);
	if (data->valid && time_before_eq(jiffies, next_update)) {
		mutex_unlock(&data->lock);
		return 0;  // Return cached data
	}

	// Trigger measurement
	ret = i2c_master_send(data->client, &cmd, 1);
	if (ret < 0)
		goto unlock;

	// Wait for conversion (8.2 ms for high precision)
	usleep_range(8200, 10000);

	// Read results with CRC
	ret = i2c_master_recv(data->client, raw_data, sizeof(raw_data));
	if (ret != sizeof(raw_data)) {
		ret = (ret >= 0) ? -ENODATA : ret;
		goto unlock;
	}

	// Verify CRC (omitted for brevity - see actual driver)

	// Parse temperature and humidity ticks
	t_ticks = (raw_data[0] << 8) | raw_data[1];
	rh_ticks = (raw_data[3] << 8) | raw_data[4];

	// Convert to standard units
	// Temperature: -45°C to +125°C mapped to 0-65535
	data->temperature = ((21875 * (int32_t)t_ticks) >> 13) - 45000;  // m°C

	// Humidity: 0-100% mapped to 0-65535
	data->humidity = ((15625 * (int32_t)rh_ticks) >> 13) - 6000;  // milli-percent

	data->last_updated = jiffies;
	data->valid = true;
	ret = 0;

unlock:
	mutex_unlock(&data->lock);
	return ret;
}

/**
 * sht4x_hwmon_visible - Determine attribute visibility
 *
 * Returns: File mode or 0 to hide attribute
 */
static umode_t sht4x_hwmon_visible(const void *drvdata,
				   enum hwmon_sensor_types type,
				   u32 attr, int channel)
{
	switch (type) {
	case hwmon_temp:
	case hwmon_humidity:
		// Temperature and humidity are read-only
		return 0444;
	case hwmon_chip:
		// Update interval is read-write
		return 0644;
	default:
		return 0;
	}
}

/**
 * sht4x_hwmon_read - Read attribute value
 */
static int sht4x_hwmon_read(struct device *dev, enum hwmon_sensor_types type,
			    u32 attr, int channel, long *val)
{
	struct sht4x_data *data = dev_get_drvdata(dev);
	int ret;

	switch (type) {
	case hwmon_temp:
		if (attr == hwmon_temp_input) {
			ret = sht4x_read_values(data);
			if (ret)
				return ret;
			*val = data->temperature;
			return 0;
		}
		break;

	case hwmon_humidity:
		if (attr == hwmon_humidity_input) {
			ret = sht4x_read_values(data);
			if (ret)
				return ret;
			*val = data->humidity;
			return 0;
		}
		break;

	case hwmon_chip:
		if (attr == hwmon_chip_update_interval) {
			*val = data->update_interval;
			return 0;
		}
		break;

	default:
		break;
	}

	return -EOPNOTSUPP;
}

/**
 * sht4x_hwmon_write - Write attribute value
 */
static int sht4x_hwmon_write(struct device *dev, enum hwmon_sensor_types type,
			     u32 attr, int channel, long val)
{
	struct sht4x_data *data = dev_get_drvdata(dev);

	if (type == hwmon_chip && attr == hwmon_chip_update_interval) {
		// Clamp to valid range
		data->update_interval = clamp_val(val, SHT4X_MIN_POLL_INTERVAL, INT_MAX);
		return 0;
	}

	return -EOPNOTSUPP;
}

static const struct hwmon_ops sht4x_hwmon_ops = {
	.is_visible = sht4x_hwmon_visible,
	.read = sht4x_hwmon_read,
	.write = sht4x_hwmon_write,
};

/**
 * Channel configuration using HWMON_CHANNEL_INFO macro
 *
 * This creates:
 * - /sys/class/hwmon/hwmonX/update_interval
 * - /sys/class/hwmon/hwmonX/temp1_input
 * - /sys/class/hwmon/hwmonX/humidity1_input
 */
static const struct hwmon_channel_info * const sht4x_info[] = {
	HWMON_CHANNEL_INFO(chip, HWMON_C_UPDATE_INTERVAL),
	HWMON_CHANNEL_INFO(temp, HWMON_T_INPUT),
	HWMON_CHANNEL_INFO(humidity, HWMON_H_INPUT),
	NULL  // Sentinel
};

static const struct hwmon_chip_info sht4x_chip_info = {
	.ops = &sht4x_hwmon_ops,
	.info = sht4x_info,
};

static int sht4x_probe(struct i2c_client *client)
{
	struct device *hwmon_dev;
	struct sht4x_data *data;

	// Verify I2C functionality
	if (!i2c_check_functionality(client->adapter, I2C_FUNC_I2C))
		return -EOPNOTSUPP;

	// Allocate driver data
	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	data->client = client;
	data->update_interval = SHT4X_MIN_POLL_INTERVAL;
	mutex_init(&data->lock);

	// Reset sensor (optional)
	// ...

	// Register HWMON device with automatic resource management
	hwmon_dev = devm_hwmon_device_register_with_info(&client->dev,
							 client->name,
							 data,
							 &sht4x_chip_info,
							 NULL);
	return PTR_ERR_OR_ZERO(hwmon_dev);
}

static const struct i2c_device_id sht4x_id[] = {
	{ "sht4x" },
	{ }
};
MODULE_DEVICE_TABLE(i2c, sht4x_id);

static const struct of_device_id sht4x_of_match[] = {
	{ .compatible = "sensirion,sht4x" },
	{ }
};
MODULE_DEVICE_TABLE(of, sht4x_of_match);

static struct i2c_driver sht4x_driver = {
	.driver = {
		.name = "sht4x",
		.of_match_table = sht4x_of_match,
	},
	.probe = sht4x_probe,
	.id_table = sht4x_id,
};
module_i2c_driver(sht4x_driver);

MODULE_AUTHOR("Navin Sankar Velliangiri");
MODULE_DESCRIPTION("SHT4x humidity and temperature sensor driver");
MODULE_LICENSE("GPL");
```

## Multi-Channel Example

Power monitor with multiple voltage/current/power channels:

```c
/**
 * Example: LTC2991 8-channel monitor
 * - 4 temperature channels
 * - 8 voltage channels
 * - 4 current channels (differential voltage / shunt)
 */

static const struct hwmon_channel_info * const ltc2991_info[] = {
	// Temperature channels 0-3
	HWMON_CHANNEL_INFO(temp,
			   HWMON_T_INPUT | HWMON_T_LABEL,  // Channel 0
			   HWMON_T_INPUT | HWMON_T_LABEL,  // Channel 1
			   HWMON_T_INPUT | HWMON_T_LABEL,  // Channel 2
			   HWMON_T_INPUT | HWMON_T_LABEL), // Channel 3

	// Voltage channels 0-7
	HWMON_CHANNEL_INFO(in,
			   HWMON_I_INPUT | HWMON_I_LABEL,  // VCC
			   HWMON_I_INPUT | HWMON_I_LABEL,  // V1
			   HWMON_I_INPUT | HWMON_I_LABEL,  // V2
			   HWMON_I_INPUT | HWMON_I_LABEL,  // V3
			   HWMON_I_INPUT | HWMON_I_LABEL,  // V4
			   HWMON_I_INPUT | HWMON_I_LABEL,  // V5
			   HWMON_I_INPUT | HWMON_I_LABEL,  // V6
			   HWMON_I_INPUT | HWMON_I_LABEL), // V7

	// Current channels 0-3 (calculated from differential voltage)
	HWMON_CHANNEL_INFO(curr,
			   HWMON_C_INPUT | HWMON_C_LABEL,
			   HWMON_C_INPUT | HWMON_C_LABEL,
			   HWMON_C_INPUT | HWMON_C_LABEL,
			   HWMON_C_INPUT | HWMON_C_LABEL),

	// Power channels 0-3 (voltage * current)
	HWMON_CHANNEL_INFO(power,
			   HWMON_P_INPUT | HWMON_P_LABEL,
			   HWMON_P_INPUT | HWMON_P_LABEL,
			   HWMON_P_INPUT | HWMON_P_LABEL,
			   HWMON_P_INPUT | HWMON_P_LABEL),
	NULL
};
```

## Labels and String Attributes

Provide human-readable names for channels:

```c
/**
 * read_string callback for channel labels
 */
static int ltc2991_read_string(struct device *dev,
			       enum hwmon_sensor_types type,
			       u32 attr, int channel, const char **str)
{
	if (attr != hwmon_temp_label && attr != hwmon_in_label)
		return -EOPNOTSUPP;

	// Provide meaningful channel names
	static const char * const temp_labels[] = {
		"Internal Temperature",
		"Remote 1",
		"Remote 2",
		"Remote 3"
	};

	static const char * const voltage_labels[] = {
		"VCC",
		"12V Rail",
		"5V Rail",
		"3.3V Rail",
		"1.8V Rail",
		"1.2V Core",
		"DDR VDD",
		"PCIe"
	};

	if (type == hwmon_temp && channel < ARRAY_SIZE(temp_labels)) {
		*str = temp_labels[channel];
		return 0;
	}

	if (type == hwmon_in && channel < ARRAY_SIZE(voltage_labels)) {
		*str = voltage_labels[channel];
		return 0;
	}

	return -EINVAL;
}
```

**Sysfs result**:
```bash
$ cat /sys/class/hwmon/hwmon0/temp1_label
Internal Temperature

$ cat /sys/class/hwmon/hwmon0/in1_label
12V Rail
```

## Alarms and Thresholds

Implementing alarm monitoring:

```c
/**
 * Example: Temperature sensor with min/max alarms
 */
static const struct hwmon_channel_info * const temp_alarm_info[] = {
	HWMON_CHANNEL_INFO(temp,
			   HWMON_T_INPUT |
			   HWMON_T_MIN | HWMON_T_MAX |
			   HWMON_T_MIN_ALARM | HWMON_T_MAX_ALARM |
			   HWMON_T_CRIT | HWMON_T_CRIT_ALARM),
	NULL
};

static int temp_sensor_read(struct device *dev, enum hwmon_sensor_types type,
			    u32 attr, int channel, long *val)
{
	struct temp_data *data = dev_get_drvdata(dev);
	u8 status;

	switch (attr) {
	case hwmon_temp_input:
		return read_temperature(data, val);

	case hwmon_temp_min:
		*val = data->temp_min;
		return 0;

	case hwmon_temp_max:
		*val = data->temp_max;
		return 0;

	case hwmon_temp_crit:
		*val = data->temp_crit;
		return 0;

	case hwmon_temp_min_alarm:
		status = read_status_reg(data);
		*val = !!(status & TEMP_LOW_ALARM);
		return 0;

	case hwmon_temp_max_alarm:
		status = read_status_reg(data);
		*val = !!(status & TEMP_HIGH_ALARM);
		return 0;

	case hwmon_temp_crit_alarm:
		status = read_status_reg(data);
		*val = !!(status & TEMP_CRIT_ALARM);
		return 0;

	default:
		return -EOPNOTSUPP;
	}
}

static int temp_sensor_write(struct device *dev, enum hwmon_sensor_types type,
			      u32 attr, int channel, long val)
{
	struct temp_data *data = dev_get_drvdata(dev);

	// Validate range
	if (val < -55000 || val > 125000)
		return -EINVAL;

	switch (attr) {
	case hwmon_temp_min:
		return write_min_threshold(data, val);

	case hwmon_temp_max:
		return write_max_threshold(data, val);

	case hwmon_temp_crit:
		return write_crit_threshold(data, val);

	default:
		return -EOPNOTSUPP;
	}
}
```

## Common Patterns

### Cached Reading with Update Interval

```c
struct sensor_data {
	struct mutex lock;
	unsigned long last_update;
	unsigned long update_interval;  // milliseconds
	bool valid;
	long cached_value;
};

static int read_with_cache(struct sensor_data *data, long *val)
{
	unsigned long next_update;

	mutex_lock(&data->lock);

	next_update = data->last_update + msecs_to_jiffies(data->update_interval);
	if (data->valid && time_before_eq(jiffies, next_update)) {
		*val = data->cached_value;
		mutex_unlock(&data->lock);
		return 0;
	}

	// Perform actual hardware read
	*val = read_hardware(data);
	data->cached_value = *val;
	data->last_update = jiffies;
	data->valid = true;

	mutex_unlock(&data->lock);
	return 0;
}
```

### Regmap Integration

For MMIO or I2C/SPI devices using regmap:

```c
#include <linux/regmap.h>

static int regmap_hwmon_read(struct device *dev, enum hwmon_sensor_types type,
			     u32 attr, int channel, long *val)
{
	struct regmap_data *data = dev_get_drvdata(dev);
	unsigned int reg_val;
	int ret;

	ret = regmap_read(data->regmap, TEMP_REG(channel), &reg_val);
	if (ret)
		return ret;

	// Convert hardware format to millidegrees
	*val = reg_val * 125;  // Example: 0.125°C per LSB
	return 0;
}
```

## Registration Flow

1. Driver allocates device-specific data structure
2. Driver creates `struct hwmon_chip_info` describing channels
3. Driver calls `devm_hwmon_device_register_with_info()`
4. Kernel creates sysfs attributes based on channel info
5. Userspace accesses `/sys/class/hwmon/hwmonX/` files

## Key Benefits

- Automatic sysfs attribute generation
- Standard naming convention (no manual attribute creation needed)
- Userspace tools work automatically
- Type safety through enum-based API
- Resource management with devm_ variants
