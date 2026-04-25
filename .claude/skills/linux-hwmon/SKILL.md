---
name: linux-hwmon
description: Complete guide to Linux HWMON (Hardware Monitoring) subsystem for voltage sensors, current monitors, temperature sensors, power meters, fan controllers, humidity sensors, and PMIC monitoring. Use when implementing monitoring drivers for power management, thermal management, or system health.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: hwmon
  tags:
    - hwmon
    - temperature
    - voltage
    - current
    - power
    - humidity
    - fan
    - pwm
    - sensors
    - monitoring
    - lm-sensors
  dependencies:
    - linux-i2c-controller
    - linux-regulator
    - linux-devicetree
    - linux-pmbus
  learning_objectives:
    - Implement HWMON drivers with struct hwmon_chip_info
    - Configure sensor channels and attributes
    - Work with standard units (millidegrees, millivolts, milliamperes, microwatts)
    - Implement cached reading with update intervals
    - Create multi-channel power monitors
    - Integrate with lm-sensors userspace tools
    - Debug HWMON drivers using sysfs and dynamic debug
---

# Linux HWMON (Hardware Monitoring) Subsystem

Quick-start guide for implementing HWMON drivers for hardware monitoring sensors.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User mentions: "implement HWMON driver", "hwmon_chip_info", "hwmon_ops", "struct hwmon_channel_info"
- Questions about: is_visible callback, read callback, write callback, read_string callback
- User asks: "how to implement", "step by step", "create HWMON driver", "SHT4x", "temperature sensor"
- Topics: cached reading, update interval, regmap integration, multi-channel configuration
- Keywords: "registration flow", "devm_hwmon_device_register_with_info"

**Triggers to read reference/sensor-types.md**:
- User mentions: "units", "millidegrees", "millivolts", "milliamperes", "microwatts", "milli-percent"
- Questions about: temperature units, voltage units, current units, power units, humidity units
- User asks: "what units", "conversion", "attribute bitmasks", "HWMON_T_INPUT", "HWMON_I_INPUT"
- Topics: hwmon_temp, hwmon_in, hwmon_curr, hwmon_power, hwmon_energy, hwmon_humidity, hwmon_fan, hwmon_pwm
- Keywords: "channel indexing", "temp1_input", "in0_input", "curr1_input", "sysfs filenames"

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "DTS", "YAML schema", "compatible string"
- Questions about: vdd-supply, reset-gpios, shunt-resistor-micro-ohms, interrupts
- User asks: "how to specify sensor in DT", "devicetree example", "create binding"
- Topics: I2C sensor nodes, power supplies, GPIO resets, shunt resistors

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "wrong readings", "sensor timeout", "cache not updating"
- Questions about: lm-sensors, sysfs access, dmesg, dynamic debug, ftrace
- User says: "troubleshoot", "diagnose", "HWMON error", "sensor not detected", "values incorrect"
- Topics: /sys/class/hwmon, sensors command, dev_dbg, checkpatch, validation

---

## When to Use This Skill

- Implementing HWMON drivers for monitoring chips (temperature, voltage, current, power, humidity, fan)
- Creating multi-channel power monitors
- Integrating PMICs with HWMON interface
- Adding thermal management sensors
- Debugging HWMON sensor issues

## What is the Linux HWMON Subsystem?

The HWMON subsystem provides standardized sysfs attributes under `/sys/class/hwmon/hwmonX/` that are automatically compatible with monitoring tools like `sensors`, `lm-sensors`, and system management utilities.

**Key benefits**:
- Automatic sysfs attribute generation
- Standard naming convention (no manual attribute creation needed)
- Userspace tools work automatically
- Type safety through enum-based API
- Resource management with devm_ variants

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Userspace Tools                             │
│            (lm-sensors, monitoring daemons)                  │
│                                                              │
│  sensors, sensors-detect, /sys/class/hwmon/hwmonX/          │
└──────────────────────┬──────────────────────────────────────┘
                       │ Sysfs Interface
┌──────────────────────▼──────────────────────────────────────┐
│                     HWMON Core                               │
│         (drivers/hwmon/hwmon.c)                              │
│                                                              │
│  - Automatic sysfs attribute creation from channel info     │
│  - Standard naming (temp1_input, in0_input, curr1_input)    │
│  - Permission management via is_visible callback            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HWMON Driver API
┌──────────────────────▼──────────────────────────────────────┐
│                HWMON Device Drivers                          │
│           (Temperature, voltage, current, power sensors)     │
│                                                              │
│  struct hwmon_chip_info, hwmon_ops callbacks                │
└──────────────────────────────────────────────────────────────┘
```

## Quick Reference

### Key Structures

| Structure | Purpose | Header |
|-----------|---------|--------|
| `struct hwmon_chip_info` | Complete chip configuration | `<linux/hwmon.h>` |
| `struct hwmon_ops` | Callback functions | `<linux/hwmon.h>` |
| `struct hwmon_channel_info` | Channel configuration | `<linux/hwmon.h>` |
| `enum hwmon_sensor_types` | Sensor type enumeration | `<linux/hwmon.h>` |

### HWMON Callbacks

| Callback | Purpose | Required? |
|----------|---------|-----------|
| `is_visible` | Determine attribute permissions | Yes |
| `read` | Read sensor value | Yes |
| `write` | Write sensor value | Optional |
| `read_string` | Read string attribute (labels) | Optional |

### Sensor Types

| Type | Units | Index Start | Example |
|------|-------|-------------|---------|
| `hwmon_temp` | millidegrees Celsius (m°C) | 1 | temp1_input |
| `hwmon_in` | millivolts (mV) | 0 | in0_input |
| `hwmon_curr` | milliamperes (mA) | 1 | curr1_input |
| `hwmon_power` | microwatts (µW) | 1 | power1_input |
| `hwmon_energy` | microjoules (µJ) | 1 | energy1_input |
| `hwmon_humidity` | milli-percent (0.001%) | 1 | humidity1_input |
| `hwmon_fan` | RPM | 1 | fan1_input |
| `hwmon_pwm` | 0-255 | 1 | pwm1 |
| `hwmon_chip` | Chip-level attributes | N/A | update_interval |

### Common Attribute Bitmasks

```c
// Temperature
HWMON_T_INPUT           // Current temperature (read-only)
HWMON_T_MIN             // Minimum threshold
HWMON_T_MAX             // Maximum threshold
HWMON_T_CRIT            // Critical threshold
HWMON_T_ALARM           // Alarm flag
HWMON_T_LABEL           // Channel label (string)

// Voltage
HWMON_I_INPUT           // Current voltage (read-only)
HWMON_I_MIN             // Minimum threshold
HWMON_I_MAX             // Maximum threshold
HWMON_I_ALARM           // Alarm flag
HWMON_I_LABEL           // Channel label

// Current
HWMON_C_INPUT           // Current in mA
HWMON_C_MAX             // Maximum threshold
HWMON_C_ALARM           // Alarm flag
HWMON_C_LABEL           // Channel label

// Power
HWMON_P_INPUT           // Instantaneous power in µW
HWMON_P_AVERAGE         // Average power
HWMON_P_CAP             // Power cap limit
HWMON_P_LABEL           // Channel label

// Humidity
HWMON_H_INPUT           // Relative humidity
HWMON_H_LABEL           // Channel label

// Chip-level
HWMON_C_UPDATE_INTERVAL // Polling interval (milliseconds)
HWMON_C_ALARMS          // Consolidated alarm bitmap
```

## Quick Start: Simple Temperature Sensor

### Driver Structure

```c
#include <linux/hwmon.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/mutex.h>

struct temp_sensor_data {
	struct i2c_client *client;
	struct mutex lock;
	bool valid;
	unsigned long last_updated;
	unsigned long update_interval;
	s32 temperature;
};

static int temp_sensor_read_values(struct temp_sensor_data *data)
{
	unsigned long next_update;
	int ret;
	u8 raw_data[2];

	mutex_lock(&data->lock);

	// Check cache validity
	next_update = data->last_updated +
		      msecs_to_jiffies(data->update_interval);
	if (data->valid && time_before_eq(jiffies, next_update)) {
		mutex_unlock(&data->lock);
		return 0;  // Use cached data
	}

	// Read from hardware
	ret = i2c_master_recv(data->client, raw_data, sizeof(raw_data));
	if (ret != sizeof(raw_data)) {
		mutex_unlock(&data->lock);
		return ret < 0 ? ret : -EIO;
	}

	// Convert to millidegrees Celsius
	data->temperature = ((raw_data[0] << 8) | raw_data[1]) * 125 / 32;

	data->last_updated = jiffies;
	data->valid = true;

	mutex_unlock(&data->lock);
	return 0;
}

static umode_t temp_sensor_is_visible(const void *drvdata,
				      enum hwmon_sensor_types type,
				      u32 attr, int channel)
{
	switch (type) {
	case hwmon_temp:
		return 0444;  // Read-only
	case hwmon_chip:
		return 0644;  // Read-write (update_interval)
	default:
		return 0;
	}
}

static int temp_sensor_read(struct device *dev,
			    enum hwmon_sensor_types type,
			    u32 attr, int channel, long *val)
{
	struct temp_sensor_data *data = dev_get_drvdata(dev);
	int ret;

	switch (type) {
	case hwmon_temp:
		if (attr == hwmon_temp_input) {
			ret = temp_sensor_read_values(data);
			if (ret)
				return ret;
			*val = data->temperature;
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

static int temp_sensor_write(struct device *dev,
			     enum hwmon_sensor_types type,
			     u32 attr, int channel, long val)
{
	struct temp_sensor_data *data = dev_get_drvdata(dev);

	if (type == hwmon_chip && attr == hwmon_chip_update_interval) {
		data->update_interval = clamp_val(val, 1000, INT_MAX);
		return 0;
	}

	return -EOPNOTSUPP;
}

static const struct hwmon_ops temp_sensor_hwmon_ops = {
	.is_visible = temp_sensor_is_visible,
	.read = temp_sensor_read,
	.write = temp_sensor_write,
};

static const struct hwmon_channel_info * const temp_sensor_info[] = {
	HWMON_CHANNEL_INFO(chip, HWMON_C_UPDATE_INTERVAL),
	HWMON_CHANNEL_INFO(temp, HWMON_T_INPUT),
	NULL
};

static const struct hwmon_chip_info temp_sensor_chip_info = {
	.ops = &temp_sensor_hwmon_ops,
	.info = temp_sensor_info,
};

static int temp_sensor_probe(struct i2c_client *client)
{
	struct device *hwmon_dev;
	struct temp_sensor_data *data;

	if (!i2c_check_functionality(client->adapter, I2C_FUNC_I2C))
		return -EOPNOTSUPP;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	data->client = client;
	data->update_interval = 2000;  // 2 seconds default
	mutex_init(&data->lock);

	hwmon_dev = devm_hwmon_device_register_with_info(&client->dev,
							 client->name,
							 data,
							 &temp_sensor_chip_info,
							 NULL);
	return PTR_ERR_OR_ZERO(hwmon_dev);
}

static const struct i2c_device_id temp_sensor_id[] = {
	{ "temp-sensor" },
	{ }
};
MODULE_DEVICE_TABLE(i2c, temp_sensor_id);

static const struct of_device_id temp_sensor_of_match[] = {
	{ .compatible = "vendor,temp-sensor" },
	{ }
};
MODULE_DEVICE_TABLE(of, temp_sensor_of_match);

static struct i2c_driver temp_sensor_driver = {
	.driver = {
		.name = "temp-sensor",
		.of_match_table = temp_sensor_of_match,
	},
	.probe = temp_sensor_probe,
	.id_table = temp_sensor_id,
};
module_i2c_driver(temp_sensor_driver);

MODULE_AUTHOR("Your Name <your.email@example.com>");
MODULE_DESCRIPTION("Temperature sensor HWMON driver");
MODULE_LICENSE("GPL");
```

### Devicetree Node

```dts
&i2c0 {
	temp_sensor: temperature@48 {
		compatible = "vendor,temp-sensor";
		reg = <0x48>;
		vdd-supply = <&reg_3v3>;
	};
};
```

### Userspace Access

```bash
# View sensor readings
sensors

# Output:
# temp-sensor-i2c-0-48
# Adapter: i2c-0
# temp1:        +24.5°C

# Raw sysfs access
cat /sys/class/hwmon/hwmon0/temp1_input
# 24500

# Set update interval to 5 seconds
echo 5000 > /sys/class/hwmon/hwmon0/update_interval
```

## Essential Patterns

### Multi-Channel Sensor

```c
static const struct hwmon_channel_info * const multi_sensor_info[] = {
	// Temperature channels 1-2
	HWMON_CHANNEL_INFO(temp,
			   HWMON_T_INPUT | HWMON_T_LABEL,
			   HWMON_T_INPUT | HWMON_T_LABEL),

	// Voltage channels 0-3 (note: starts at 0)
	HWMON_CHANNEL_INFO(in,
			   HWMON_I_INPUT | HWMON_I_LABEL,  // VCC
			   HWMON_I_INPUT | HWMON_I_LABEL,  // 3.3V
			   HWMON_I_INPUT | HWMON_I_LABEL,  // 1.8V
			   HWMON_I_INPUT | HWMON_I_LABEL), // 1.2V

	// Current channels 1-2
	HWMON_CHANNEL_INFO(curr,
			   HWMON_C_INPUT | HWMON_C_LABEL,
			   HWMON_C_INPUT | HWMON_C_LABEL),

	NULL
};
```

### Channel Labels

```c
static int sensor_read_string(struct device *dev,
			       enum hwmon_sensor_types type,
			       u32 attr, int channel, const char **str)
{
	static const char * const temp_labels[] = {
		"Internal Temperature",
		"Remote Temperature"
	};

	static const char * const voltage_labels[] = {
		"VCC",
		"3.3V Rail",
		"1.8V Rail",
		"1.2V Core"
	};

	if (type == hwmon_temp && attr == hwmon_temp_label &&
	    channel < ARRAY_SIZE(temp_labels)) {
		*str = temp_labels[channel];
		return 0;
	}

	if (type == hwmon_in && attr == hwmon_in_label &&
	    channel < ARRAY_SIZE(voltage_labels)) {
		*str = voltage_labels[channel];
		return 0;
	}

	return -EOPNOTSUPP;
}
```

### Unit Conversion Examples

```c
// Temperature: Raw 16-bit value to millidegrees Celsius
// Example: -45°C to +125°C mapped to 0-65535
s32 temp_mc = ((21875 * (int32_t)raw_temp) >> 13) - 45000;

// Voltage: 12-bit ADC, 5V full scale to millivolts
u32 voltage_mv = (raw_adc * 5000) / 4095;

// Current: Shunt voltage to milliamperes (0.1Ω shunt)
// V = I * R, so I = V / R
s32 current_ma = (shunt_voltage_uv / 100);  // 100µΩ = 0.1Ω

// Power: Voltage (mV) * Current (mA) = µW
u64 power_uw = (u64)voltage_mv * current_ma;

// Humidity: Raw 16-bit to milli-percent
s32 humidity_mp = ((15625 * (int32_t)raw_rh) >> 13) - 6000;
```

## Build System Integration

### Kconfig Entry

```kconfig
config SENSORS_TEMP_SENSOR
	tristate "Temperature Sensor support"
	depends on I2C
	help
	  If you say yes here you get support for the Temperature Sensor
	  family of hardware monitoring chips.

	  This driver can also be built as a module. If so, the module
	  will be called temp-sensor.
```

### Makefile Entry

```makefile
obj-$(CONFIG_SENSORS_TEMP_SENSOR) += temp-sensor.o
```

### Add to Kconfig.adi (ADI kernel)

```kconfig
config HWMON_ALL_ADI_DRIVERS
	bool "Analog Devices HWMON drivers"
	imply SENSORS_TEMP_SENSOR
```

## Debugging Quick Reference

```bash
# Check device registration
dmesg | grep -i temp-sensor

# List HWMON devices
ls /sys/class/hwmon/

# Read all attributes
find /sys/class/hwmon/hwmon0 -type f -exec sh -c 'echo "{}:"; cat {}' \;

# Enable debug logging
echo "module temp_sensor +p" > /sys/kernel/debug/dynamic_debug/control

# View with lm-sensors
sensors
```

## Key Takeaways

### Implementation Checklist

- [ ] Define sensor types and channels in `hwmon_channel_info` array
- [ ] Implement `is_visible` callback to set attribute permissions
- [ ] Implement `read` callback for reading sensor values
- [ ] Implement `write` callback for writable attributes (optional)
- [ ] Implement `read_string` for channel labels (optional)
- [ ] Convert hardware values to standard HWMON units
- [ ] Use cached reading pattern with update interval
- [ ] Use mutex for I2C/SPI access (not spinlock)
- [ ] Register with `devm_hwmon_device_register_with_info()`
- [ ] Create devicetree binding in YAML format
- [ ] Test with `sensors` command and raw sysfs access

### Common Mistakes to Avoid

- **Wrong units**: Always use millidegrees (m°C), millivolts (mV), milliamperes (mA), microwatts (µW)
- **Wrong index start**: Voltage starts at 0, all others start at 1
- **Integer overflow**: Use appropriate types (s32, u64) for calculations
- **Missing mutex**: I2C/SPI operations require mutex protection
- **Wrong permissions**: `is_visible` must return file mode (0444, 0644), not boolean
- **Hardcoded values**: Use `clamp_val()` for range validation
- **No caching**: Implement update interval to avoid excessive bus traffic

## References

- **HWMON Documentation**: `Documentation/hwmon/`
- **HWMON sysfs Interface**: `Documentation/hwmon/sysfs-interface.rst`
- **Header File**: `include/linux/hwmon.h`
- **Example Drivers**:
  - `drivers/hwmon/sht4x.c` - Temperature/humidity sensor
  - `drivers/hwmon/lm75.c` - Temperature sensor
  - `drivers/hwmon/ina2xx.c` - Current/power monitor
  - `drivers/hwmon/ltc2991.c` - Multi-channel monitor
- **lm-sensors**: https://github.com/lm-sensors/lm-sensors
