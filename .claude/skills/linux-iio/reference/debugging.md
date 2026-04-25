# IIO Debugging

Complete guide to debugging IIO drivers using sysfs, debugfs, dynamic debug, libiio tools, and common troubleshooting techniques.

## Verify Device Registration

```bash
# List all IIO devices
ls /sys/bus/iio/devices/

# Should see iio:device0, iio:device1, etc.

# Check device name
cat /sys/bus/iio/devices/iio:device0/name

# List all attributes
ls -la /sys/bus/iio/devices/iio:device0/

# Check device tree binding
cat /proc/device-tree/<path>/compatible
```

## Test Single Channel Reads

```bash
# Read raw value
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw

# Read scale
cat /sys/bus/iio/devices/iio:device0/in_voltage0_scale

# Read offset (if available)
cat /sys/bus/iio/devices/iio:device0/in_voltage0_offset

# Calculate voltage
# voltage = (raw + offset) * scale

# Read sampling frequency
cat /sys/bus/iio/devices/iio:device0/sampling_frequency

# Check available values
cat /sys/bus/iio/devices/iio:device0/sampling_frequency_available
```

## Enable Dynamic Debug

```bash
# Enable debug for specific driver
echo "file drivers/iio/adc/ad7124.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable for all IIO
echo "file drivers/iio/* +p" > /sys/kernel/debug/dynamic_debug/control

# Enable for IIO core
echo "module industrialio +p" > /sys/kernel/debug/dynamic_debug/control

# Watch logs
dmesg -w

# Or use journal
journalctl -kf
```

## Check Buffer Configuration

```bash
# Check buffer exists
ls /sys/bus/iio/devices/iio:device0/buffer/

# Check buffer attributes
cat /sys/bus/iio/devices/iio:device0/buffer/length
cat /sys/bus/iio/devices/iio:device0/buffer/enable

# Check scan elements
ls /sys/bus/iio/devices/iio:device0/scan_elements/

# Check what's enabled
cat /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_en
cat /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_index
cat /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_type

# Check active channels
grep "" /sys/bus/iio/devices/iio:device0/scan_elements/*_en
```

## Test Buffered Mode

```bash
# Enable channel 0
echo 1 > /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_en

# Set buffer length
echo 128 > /sys/bus/iio/devices/iio:device0/buffer/length

# Check current trigger
cat /sys/bus/iio/devices/iio:device0/trigger/current_trigger

# List available triggers
cat /sys/bus/iio/devices/trigger*/name

# Set trigger (if needed)
echo "trigger0" > /sys/bus/iio/devices/iio:device0/trigger/current_trigger

# Enable buffer
echo 1 > /sys/bus/iio/devices/iio:device0/buffer/enable

# Read data (binary)
dd if=/dev/iio:device0 bs=1024 count=10 | hexdump -C

# Disable buffer when done
echo 0 > /sys/bus/iio/devices/iio:device0/buffer/enable
```

## Test with libiio Tools

```bash
# Install tools
apt-get install libiio-utils

# List devices
iio_info

# Read all attributes
iio_attr -a -c ad7124-4

# Read specific attribute
iio_attr -d ad7124-4 in_voltage0_raw

# Capture buffered data (256 samples, 100 Hz)
iio_readdev -b 256 -s 100 ad7124-4

# Network mode (if iiod running on target)
iio_info -n 192.168.1.100
```

## Debugfs Register Access

If driver implements `.debugfs_reg_access`:

```bash
# Check debugfs exists
ls /sys/kernel/debug/iio/iio:device0/

# Read register 0x01
echo 0x01 > /sys/kernel/debug/iio/iio:device0/direct_reg_access
cat /sys/kernel/debug/iio/iio:device0/direct_reg_access

# Write register 0x01 with value 0x55
echo "0x01 0x55" > /sys/kernel/debug/iio/iio:device0/direct_reg_access

# Verify write
echo 0x01 > /sys/kernel/debug/iio/iio:device0/direct_reg_access
cat /sys/kernel/debug/iio/iio:device0/direct_reg_access
```

## Check Kernel Messages

```bash
# View kernel ring buffer
dmesg | grep -i iio
dmesg | grep -i ad7124

# Watch live
dmesg -w | grep --line-buffered -i iio

# Check for errors
dmesg | grep -i "error\|fail\|warn"

# Check probe status
dmesg | grep "probe"

# Check device tree parsing
dmesg | grep "of_"
```

## Verify Device Tree

```bash
# Check DT node exists
ls /proc/device-tree/amba/spi@e0007000/adc@0/

# Check compatible string
cat /proc/device-tree/amba/spi@e0007000/adc@0/compatible

# Check properties
hexdump -C /proc/device-tree/amba/spi@e0007000/adc@0/spi-max-frequency

# Verify phandle references
cat /proc/device-tree/amba/spi@e0007000/adc@0/vref-supply
# Then look up the phandle
find /proc/device-tree -name "phandle" -exec grep -l "<value>" {} \;
```

## Test Triggers

```bash
# List all triggers
ls /sys/bus/iio/devices/trigger*/

# Check trigger name
cat /sys/bus/iio/devices/trigger0/name

# Check trigger owner
cat /sys/bus/iio/devices/trigger0/uevent

# Assign trigger to device
echo "trigger0" > /sys/bus/iio/devices/iio:device0/trigger/current_trigger

# Verify assignment
cat /sys/bus/iio/devices/iio:device0/trigger/current_trigger
```

## Check Events

```bash
# Monitor events (blocking)
cat /dev/iio:device0

# Or use hexdump for formatted output
cat /dev/iio:device0 | hexdump -C

# Configure event threshold
echo 1000 > /sys/bus/iio/devices/iio:device0/events/in_voltage0_thresh_rising_value

# Enable event
echo 1 > /sys/bus/iio/devices/iio:device0/events/in_voltage0_thresh_rising_en

# Check event configuration
cat /sys/bus/iio/devices/iio:device0/events/in_voltage0_thresh_rising_en
cat /sys/bus/iio/devices/iio:device0/events/in_voltage0_thresh_rising_value
```

## IIO Oscilloscope Testing

### Network Mode

On target:
```bash
# Start IIO daemon
systemctl start iiod

# Check service status
systemctl status iiod

# Check port (default 30431)
netstat -tuln | grep 30431

# Manual start (for debugging)
iiod -D -d -n
```

On host:
```bash
# Install IIO Oscilloscope
# Download from: https://github.com/analogdevicesinc/iio-oscilloscope

# Connect to target
# Settings → Connect → <target-ip>:30431
```

### Verification Checklist

- [ ] Device appears in device list
- [ ] All channels visible
- [ ] DMM tab shows channel values
- [ ] Capture tab works (buffered mode)
- [ ] Sampling frequency adjustable
- [ ] All attributes read/write correctly

## Common Issues and Solutions

### Device Not Appearing

**Symptom**: No `/sys/bus/iio/devices/iio:deviceX`

**Check**:
```bash
# 1. Verify driver loaded
lsmod | grep ad7124

# 2. Check for probe errors
dmesg | grep -i "ad7124\|probe"

# 3. Verify SPI/I2C device registered
ls /sys/bus/spi/devices/
cat /sys/bus/spi/devices/spi0.0/modalias

# 4. Check compatible string match
cat /proc/device-tree/amba/spi@e0007000/adc@0/compatible
grep "ad7124" drivers/iio/adc/ad7124.c
```

### Cannot Read Attribute

**Symptom**: `cat: read error: Device or resource busy`

**Cause**: Trying to read while buffer is enabled

**Solution**:
```bash
# Disable buffer first
echo 0 > /sys/bus/iio/devices/iio:device0/buffer/enable

# Then read attribute
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
```

### Buffer Always Returns 0

**Check**:
1. Trigger assigned and working
2. Channels enabled in scan_elements
3. Device is actually sampling
4. Check trigger handler is called

```bash
# Enable function tracing for trigger handler
echo 'ad7124_trigger_handler' > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Check trace
cat /sys/kernel/debug/tracing/trace
```

### Buffer Stops After Few Samples

**Symptom**: First few reads work, then hangs

**Cause**: Missing `iio_trigger_notify_done()` in trigger handler

**Fix**: Add to trigger handler:
```c
iio_trigger_notify_done(indio_dev->trig);
```

### Wrong Data Values

**Check**:
1. `scan_type.endianness` matches hardware
2. `scan_type.realbits` and `storagebits` correct
3. `scan_type.shift` accounts for bit alignment
4. Scale and offset calculations

```bash
# Check scan type
cat /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_type

# Verify with known input
# Apply known voltage and check raw value
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
cat /sys/bus/iio/devices/iio:device0/in_voltage0_scale
# voltage = raw * scale (if offset = 0)
```

### SPI Communication Errors

```bash
# Enable SPI debug
echo "file drivers/spi/* +p" > /sys/kernel/debug/dynamic_debug/control

# Check SPI transfers
dmesg -w | grep spi

# Verify SPI settings in DT
cat /proc/device-tree/amba/spi@e0007000/adc@0/spi-max-frequency
cat /proc/device-tree/amba/spi@e0007000/adc@0/spi-cpol
cat /proc/device-tree/amba/spi@e0007000/adc@0/spi-cpha
```

### Device Tree Binding Errors

```bash
# Validate binding schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad7124.yaml

# Validate compiled DT
make ARCH=arm64 dtbs_check

# Check for DT errors during boot
dmesg | grep -i "devicetree\|of_"
```

## Tracing

### Function Tracing

```bash
# Enable function tracing for IIO driver
echo 'ad7124*' > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Perform operation
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw

# View trace
cat /sys/kernel/debug/tracing/trace

# Disable tracing
echo 0 > /sys/kernel/debug/tracing/tracing_on
```

### Event Tracing

```bash
# Enable IIO events
echo 1 > /sys/kernel/debug/tracing/events/iio/enable

# View events
cat /sys/kernel/debug/tracing/trace_pipe
```

## Performance Analysis

```bash
# Profile trigger handler
perf record -e sched:sched_switch -a -g -- sleep 10
perf report

# Check interrupt rate
cat /proc/interrupts | grep -i iio

# Monitor CPU usage
top -p $(pgrep iiod)
```

## Memory Debugging

```bash
# Enable KASAN (requires kernel rebuild with CONFIG_KASAN=y)

# Check for memory leaks
echo scan > /sys/kernel/debug/kmemleak
cat /sys/kernel/debug/kmemleak

# Check slab allocations
cat /proc/slabinfo | grep iio
```

## Network Debugging (libiio)

```bash
# On target
# Start iiod in debug mode
iiod -D -d -n

# Check network connectivity
nc -zv <target-ip> 30431

# On host
# Test connection
iio_info -n <target-ip>

# Capture network traffic
tcpdump -i eth0 port 30431 -w iio.pcap
```

## Stress Testing

```bash
# Continuous buffer read
while true; do
    echo 1 > /sys/bus/iio/devices/iio:device0/buffer/enable
    dd if=/dev/iio:device0 bs=1024 count=100 of=/dev/null
    echo 0 > /sys/bus/iio/devices/iio:device0/buffer/enable
done

# Monitor for errors
dmesg -w
```

## Driver Development Debugging

### Add Debug Prints

```c
// Use dev_dbg for debug messages (enabled via dynamic debug)
dev_dbg(&spi->dev, "Reading channel %d\n", channel);

// Use dev_err for errors
dev_err(&spi->dev, "Failed to read register 0x%02x: %d\n", reg, ret);

// Use dev_warn for warnings
dev_warn(&spi->dev, "Sample rate too high, clamping to %d Hz\n", max_rate);

// Use dev_info for important info
dev_info(&spi->dev, "Device initialized successfully\n");
```

### Print Hex Dumps

```c
#include <linux/printk.h>

// Print buffer contents
print_hex_dump(KERN_DEBUG, "IIO buffer: ", DUMP_PREFIX_OFFSET,
	      16, 1, buffer, length, true);
```

### Verify Callback Execution

```c
static int ad7124_read_raw(struct iio_dev *indio_dev,
			  struct iio_chan_spec const *chan,
			  int *val, int *val2, long info)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	dev_dbg(&st->spi->dev, "%s: chan=%d info=%ld\n",
		__func__, chan->channel, info);

	// ... rest of function
}
```

## Debugging Checklist

- [ ] Device appears in `/sys/bus/iio/devices/`
- [ ] Driver loaded (`lsmod`)
- [ ] No probe errors in `dmesg`
- [ ] All channels readable
- [ ] Scale/offset values reasonable
- [ ] Buffer mode works (if implemented)
- [ ] Trigger assigned and working (if buffered)
- [ ] Events working (if implemented)
- [ ] libiio can connect
- [ ] IIO Oscilloscope shows device
- [ ] No kernel warnings or errors
- [ ] Performance acceptable

## Resources

- **Kernel Documentation**: https://docs.kernel.org/driver-api/iio/
- **IIO Utils**: `tools/iio/` in kernel source
- **libiio**: https://github.com/analogdevicesinc/libiio
- **IIO Oscilloscope**: https://github.com/analogdevicesinc/iio-oscilloscope
