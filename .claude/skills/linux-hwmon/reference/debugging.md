# HWMON Debugging Guide

Complete guide to debugging HWMON drivers and troubleshooting sensor issues.

## Userspace Access Tools

### lm-sensors

The standard tool for accessing HWMON sensors.

```bash
# Detect sensors
sensors-detect

# View all sensor readings
sensors

# View specific sensor
sensors hwmon0

# Continuous monitoring
watch -n 1 sensors

# Show sensor configuration
sensors -u
```

**Example output**:
```
sht4x-i2c-0-44
Adapter: i2c-0-mux (chan_id 0)
temp1:        +24.5°C
humidity1:     45.2 %RH
```

### Raw Sysfs Access

Direct access to HWMON sysfs attributes:

```bash
# Find HWMON devices
ls -l /sys/class/hwmon/

# Read device name
cat /sys/class/hwmon/hwmon0/name

# Read temperature (in millidegrees Celsius)
cat /sys/class/hwmon/hwmon0/temp1_input

# Set update interval to 5 seconds
echo 5000 > /sys/class/hwmon/hwmon0/update_interval

# Read all attributes
find /sys/class/hwmon/hwmon0 -type f -exec sh -c 'echo "{}:"; cat {}' \;
```

### Debugfs

Some HWMON drivers provide additional debug information:

```bash
# Check for HWMON debugfs entries
ls /sys/kernel/debug/hwmon/

# Read debug information
cat /sys/kernel/debug/hwmon/hwmon0/registers
```

## Kernel Debug Techniques

### Enable Dynamic Debug

Enable verbose logging for HWMON subsystem:

```bash
# Enable debug for specific driver
echo "module sht4x +p" > /sys/kernel/debug/dynamic_debug/control

# Enable debug for all HWMON drivers
echo "file drivers/hwmon/* +p" > /sys/kernel/debug/dynamic_debug/control

# View kernel messages
dmesg | grep -i sht4x
```

### Add pr_debug Statements

```c
#include <linux/dev_printk.h>

static int sht4x_probe(struct i2c_client *client)
{
	dev_dbg(&client->dev, "Probing SHT4x sensor\n");

	// ... probe code ...

	dev_dbg(&client->dev, "Sensor initialized successfully\n");
	return 0;
}

static int sht4x_read_values(struct sht4x_data *data)
{
	dev_dbg(&data->client->dev, "Reading sensor values\n");

	// ... read code ...

	dev_dbg(&data->client->dev, "Temperature: %d m°C, Humidity: %d m%%\n",
		data->temperature, data->humidity);
	return 0;
}
```

### printk Logging Levels

```c
dev_err(&dev->dev, "Failed to read sensor: %d\n", ret);   // Error
dev_warn(&dev->dev, "Sensor out of range\n");             // Warning
dev_info(&dev->dev, "Sensor detected: %s\n", name);       // Info
dev_dbg(&dev->dev, "Register 0x%02x = 0x%04x\n", reg, val); // Debug
```

## Common Issues and Solutions

### Issue: Sensor Not Detected

**Symptoms**:
- Driver probe not called
- Device not appearing in `/sys/class/hwmon/`

**Debug steps**:

1. Check devicetree:
```bash
# Verify devicetree node
ls /proc/device-tree/i2c@*/sensor@*

# Check compatible string
cat /proc/device-tree/i2c@*/sensor@*/compatible
```

2. Check I2C bus:
```bash
# List I2C buses
ls /sys/bus/i2c/devices/

# Scan I2C bus (if i2c-tools installed)
i2cdetect -y 0
```

3. Check driver registration:
```bash
# Verify driver is loaded
lsmod | grep sht4x

# Check driver registration
ls /sys/bus/i2c/drivers/sht4x/
```

**Solution**:
- Verify devicetree binding matches driver's `of_device_id` table
- Check I2C address in devicetree matches hardware
- Ensure driver is compiled and loaded (`CONFIG_SENSORS_SHT4X=y` or `=m`)

### Issue: Wrong Sensor Readings

**Symptoms**:
- Values are scaled incorrectly
- Negative temperatures shown as large positive numbers
- Humidity > 100%

**Debug steps**:

1. Add debug logging to read function:
```c
static int sht4x_hwmon_read(struct device *dev, enum hwmon_sensor_types type,
			    u32 attr, int channel, long *val)
{
	// ... read code ...

	dev_dbg(dev, "Raw value: 0x%04x, Converted: %ld\n", raw, *val);
	return 0;
}
```

2. Verify unit conversion:
```c
// Temperature: -45°C to +125°C mapped to 0-65535
// Check conversion formula matches datasheet
data->temperature = ((21875 * (int32_t)t_ticks) >> 13) - 45000;

// Test with known values
// Example: 0x0000 should give -45000 m°C
// Example: 0xFFFF should give ~125000 m°C
```

**Solution**:
- Verify conversion formula matches datasheet
- Check for integer overflow in calculations
- Use appropriate data types (s32 for signed values)
- Test with known calibration points

### Issue: Sensor Read Timeouts

**Symptoms**:
- I/O errors when reading sensor
- Timeout errors in dmesg

**Debug steps**:

1. Check timing:
```c
// Add timing measurement
ktime_t start, end;

start = ktime_get();
ret = i2c_master_recv(client, data, len);
end = ktime_get();

dev_dbg(&client->dev, "I2C read took %lld us\n",
	ktime_us_delta(end, start));
```

2. Verify delays:
```c
// Check conversion time matches datasheet
// SHT4x high precision: 8.2 ms
usleep_range(8200, 10000);
```

**Solution**:
- Increase delay after triggering measurement
- Check I2C bus clock speed (some sensors have max speed)
- Verify power supply is stable
- Check for I2C bus errors in `dmesg`

### Issue: Cached Values Not Updating

**Symptoms**:
- Same value returned repeatedly
- Value doesn't change when sensor environment changes

**Debug steps**:

1. Check cache logic:
```c
static int sht4x_read_values(struct sht4x_data *data)
{
	unsigned long next_update;

	next_update = data->last_updated +
		      msecs_to_jiffies(data->update_interval);

	dev_dbg(&data->client->dev, "Cache check: jiffies=%lu, last=%lu, next=%lu\n",
		jiffies, data->last_updated, next_update);

	if (data->valid && time_before_eq(jiffies, next_update)) {
		dev_dbg(&data->client->dev, "Returning cached value\n");
		return 0;  // Return cached data
	}

	dev_dbg(&data->client->dev, "Reading fresh value\n");
	// ... perform actual read ...
}
```

2. Check update interval:
```bash
# Verify update interval
cat /sys/class/hwmon/hwmon0/update_interval

# Set shorter interval for testing
echo 100 > /sys/class/hwmon/hwmon0/update_interval
```

**Solution**:
- Verify `time_before_eq()` logic is correct
- Check that `data->valid` is set after successful read
- Ensure `data->last_updated` is updated with current jiffies
- Test with shorter update interval

### Issue: Attributes Not Appearing

**Symptoms**:
- Expected sysfs attributes missing
- `temp1_max` not appearing even though configured

**Debug steps**:

1. Check `is_visible` callback:
```c
static umode_t sht4x_hwmon_visible(const void *drvdata,
				   enum hwmon_sensor_types type,
				   u32 attr, int channel)
{
	// Add debug logging
	pr_debug("is_visible: type=%d, attr=0x%x, channel=%d\n",
		 type, attr, channel);

	switch (type) {
	case hwmon_temp:
		if (attr == hwmon_temp_input) {
			pr_debug("Returning 0444 for temp_input\n");
			return 0444;  // Read-only
		}
		break;
	}

	pr_debug("Hiding attribute (returning 0)\n");
	return 0;  // Hide attribute
}
```

2. Verify channel info:
```c
static const struct hwmon_channel_info * const sht4x_info[] = {
	// Check that attributes are listed in config
	HWMON_CHANNEL_INFO(temp,
			   HWMON_T_INPUT | HWMON_T_MIN | HWMON_T_MAX),
	NULL
};
```

**Solution**:
- Ensure attribute bitmask is set in channel info
- Verify `is_visible` returns non-zero mode (0444, 0644, etc.)
- Check for typos in attribute names

### Issue: Write Operations Not Working

**Symptoms**:
- Writing to sysfs attribute has no effect
- Permission denied when writing

**Debug steps**:

1. Check permissions:
```bash
# Verify attribute is writable
ls -l /sys/class/hwmon/hwmon0/temp1_max
# Should show: -rw-r--r-- (0644) or similar
```

2. Add debug to write function:
```c
static int temp_sensor_write(struct device *dev, enum hwmon_sensor_types type,
			      u32 attr, int channel, long val)
{
	dev_dbg(dev, "Write: type=%d, attr=0x%x, channel=%d, val=%ld\n",
		type, attr, channel, val);

	if (type == hwmon_temp && attr == hwmon_temp_max) {
		dev_dbg(dev, "Setting temp_max to %ld\n", val);
		return write_threshold(dev, val);
	}

	dev_dbg(dev, "Unsupported write operation\n");
	return -EOPNOTSUPP;
}
```

**Solution**:
- Verify `is_visible` returns writable mode (0644, 0200, etc.)
- Implement `write` callback in `hwmon_ops`
- Handle the specific attribute in write callback
- Return 0 on success, negative errno on error

## ftrace for HWMON

Trace HWMON operations:

```bash
# Enable HWMON tracing
echo 1 > /sys/kernel/debug/tracing/events/hwmon/enable

# Read sensor
cat /sys/class/hwmon/hwmon0/temp1_input

# View trace
cat /sys/kernel/debug/tracing/trace

# Disable tracing
echo 0 > /sys/kernel/debug/tracing/events/hwmon/enable
```

## Testing with hwmon-test

Some HWMON drivers include test suites:

```bash
# Load test module (if available)
modprobe hwmon_test

# Check test results in dmesg
dmesg | grep hwmon_test
```

## Validation Checklist

Before submitting a HWMON driver, verify:

- [ ] Device detected and probe succeeds
- [ ] All expected sysfs attributes appear
- [ ] Reading attributes returns correct values
- [ ] Writing to writable attributes works
- [ ] Units match HWMON standards (m°C, mV, mA, µW, etc.)
- [ ] Labels provide meaningful names
- [ ] Update interval is configurable
- [ ] Cached reads work correctly
- [ ] lm-sensors displays values correctly
- [ ] No errors in dmesg
- [ ] Devicetree binding validates with `make dt_binding_check`
- [ ] Code passes checkpatch: `scripts/checkpatch.pl`

## Example Debug Session

```bash
# 1. Check device registration
dmesg | grep -i sht4x
[    2.123456] sht4x: probe of 0-0044 successful

# 2. Verify sysfs attributes
ls /sys/class/hwmon/hwmon0/
name  temp1_input  humidity1_input  update_interval

# 3. Read values
cat /sys/class/hwmon/hwmon0/temp1_input
24500

cat /sys/class/hwmon/hwmon0/humidity1_input
45200

# 4. Enable debug logging
echo "module sht4x +p" > /sys/kernel/debug/dynamic_debug/control

# 5. Read again and check debug output
cat /sys/class/hwmon/hwmon0/temp1_input
dmesg | tail -20
[   10.123456] sht4x 0-0044: Reading sensor values
[   10.123789] sht4x 0-0044: Temperature: 24500 m°C, Humidity: 45200 m%

# 6. Test with lm-sensors
sensors
sht4x-i2c-0-44
Adapter: i2c-0-mux (chan_id 0)
temp1:        +24.5°C
humidity1:     45.2 %RH
```

## Debugging Tools Summary

| Tool | Purpose | Command |
|------|---------|---------|
| sensors | View sensor readings | `sensors` |
| sysfs | Raw attribute access | `cat /sys/class/hwmon/hwmon0/temp1_input` |
| dmesg | Kernel messages | `dmesg \| grep hwmon` |
| dynamic_debug | Enable verbose logging | `echo "file drivers/hwmon/* +p" > /sys/kernel/debug/dynamic_debug/control` |
| i2cdetect | Scan I2C bus | `i2cdetect -y 0` |
| ftrace | Trace HWMON operations | `echo 1 > /sys/kernel/debug/tracing/events/hwmon/enable` |
| checkpatch | Code style validation | `scripts/checkpatch.pl` |
| dt_binding_check | Devicetree validation | `make dt_binding_check` |

## References

- **HWMON Documentation**: `Documentation/hwmon/`
- **HWMON sysfs Interface**: `Documentation/hwmon/sysfs-interface.rst`
- **lm-sensors**: https://github.com/lm-sensors/lm-sensors
- **ftrace Documentation**: `Documentation/trace/ftrace.rst`
