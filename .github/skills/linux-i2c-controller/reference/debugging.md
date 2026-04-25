# I2C Controller Debugging

Comprehensive guide to debugging I2C controller drivers.

## Dynamic Debug

Enable I2C subsystem debug messages:

```bash
# Enable I2C core debug messages
echo 'file i2c-core-* +p' > /sys/kernel/debug/dynamic_debug/control

# Enable specific driver debug (e.g., i2c-cadence.c)
echo 'file i2c-cadence.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable all I2C bus drivers
echo 'file drivers/i2c/busses/* +p' > /sys/kernel/debug/dynamic_debug/control

# View messages
dmesg -w
```

## I2C Tools

Essential userspace tools for testing I2C controllers:

### i2cdetect - Scan for Devices

```bash
# List all I2C buses
i2cdetect -l

# Scan bus 0 for devices (read mode)
i2cdetect -y 0

# Scan bus 0 using write mode (safer for some devices)
i2cdetect -y -r 0

# Example output:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 40: -- -- -- -- -- -- -- -- 48 -- -- -- -- -- -- --
# 50: 50 -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 70: -- -- -- -- -- -- -- --
```

### i2cget - Read from Device

```bash
# Read byte from device 0x50, register 0x00
i2cget -y 0 0x50 0x00

# Read word (16-bit) from device 0x48, register 0x01
i2cget -y 0 0x48 0x01 w

# Read byte using SMBus block read
i2cget -y 0 0x50 0x00 i
```

### i2cset - Write to Device

```bash
# Write byte 0x42 to device 0x50, register 0x10
i2cset -y 0 0x50 0x10 0x42

# Write word (16-bit) to device 0x48, register 0x01
i2cset -y 0 0x48 0x01 0x1234 w

# Write with confirmation prompt (safer)
i2cset 0 0x50 0x10 0x42
```

### i2cdump - Dump All Registers

```bash
# Dump all registers from device 0x50
i2cdump -y 0 0x50

# Dump in word mode
i2cdump -y 0 0x50 w

# Dump specific register range
i2cdump -y 0 0x50 b 0x00 0x10
```

### i2ctransfer - Advanced Transfers

```bash
# Write 2 bytes then read 4 bytes (combined transaction)
i2ctransfer -y 0 w2@0x50 0x00 0x10 r4@0x50

# Multiple reads
i2ctransfer -y 0 r1@0x48 r2@0x49
```

## Common Issues and Solutions

### Issue: Bus Stuck / SDA Low

**Symptoms**:
- All transfers timeout
- `i2cdetect` shows timeout or all addresses respond
- SDA line stuck low

**Diagnosis**:
```bash
# Check if bus recovery is configured
cat /sys/kernel/debug/i2c/i2c-0/bus_recovery

# Manually trigger recovery (if supported)
echo 1 > /sys/kernel/debug/i2c/i2c-0/bus_recovery
```

**Solution**:
```c
// In driver probe, configure bus recovery
id->adap.bus_recovery_info = &my_i2c_recovery_info;
```

**Hardware check**:
- Verify pull-up resistors on SDA/SCL (typically 4.7kΩ for 100kHz, 2.2kΩ for 400kHz)
- Check if a slave device is holding SDA low
- Measure SDA/SCL voltage levels (should be at VDD when idle)

### Issue: Transfer Timeout

**Symptoms**:
- Transfers timeout on every transaction
- No response from controller

**Diagnosis**:
```c
// Add debug in driver
dev_err(&adap->dev, "Transfer timeout, status: 0x%x\n",
	readl(i2c->base + STATUS_REG));

// Check interrupt routing
cat /proc/interrupts | grep i2c
```

**Solutions**:

1. **Increase timeout**:
```c
// In probe
id->adap.timeout = msecs_to_jiffies(5000);  // 5 seconds
```

2. **Check clock configuration**:
```c
// Verify clock is enabled
ret = clk_prepare_enable(id->clk);
if (ret) {
	dev_err(&pdev->dev, "Failed to enable clock\n");
	return ret;
}

// Check clock frequency
dev_info(&pdev->dev, "I2C clock rate: %lu Hz\n", clk_get_rate(id->clk));
```

3. **Verify interrupt**:
```c
// Check if interrupt fires
static irqreturn_t my_i2c_isr(int irq, void *ptr)
{
	dev_info(&adap->dev, "IRQ fired, status: 0x%x\n", status);
	// ...
}
```

### Issue: NACK on Every Transfer

**Symptoms**:
- All transactions return `-ENXIO`
- `i2cdetect` shows no devices

**Diagnosis**:
```bash
# Verify device address with logic analyzer or scope
# Common mistakes:
# - 7-bit vs 8-bit address confusion (driver uses 7-bit)
# - Wrong address (check device datasheet)

# Test with known-good device
i2cdetect -y 0
```

**Solutions**:

1. **Verify address format**:
```c
// I2C subsystem uses 7-bit addresses
// If datasheet shows 0xA0 (8-bit write), use 0x50 (7-bit)
#define DEVICE_ADDR	0x50	// NOT 0xA0
```

2. **Check clock speed**:
```dts
i2c0: i2c@e0004000 {
	clock-frequency = <100000>;  // Try slower speed first
};
```

3. **Verify pull-ups**:
- Measure SDA/SCL with oscilloscope
- Should see clean rising edges
- Rise time should be < 1μs for 100kHz, < 300ns for 400kHz

### Issue: Arbitration Lost

**Symptoms**:
- Transfers return `-EAGAIN`
- Error messages about arbitration loss

**Diagnosis**:
```bash
# Check for multiple masters on bus
dmesg | grep -i arbitration

# Verify no other I2C master is active
# Check for malfunctioning device acting as master
```

**Solution**:
```c
// In probe, set retry count
id->adap.retries = 3;  // Retry 3 times on arbitration loss

// In interrupt handler, return -EAGAIN for arbitration loss
if (status & ARB_LOST) {
	id->err_status = -EAGAIN;
	complete(&id->xfer_done);
	return IRQ_HANDLED;
}
```

### Issue: Clock Stretching Not Working

**Symptoms**:
- Some devices timeout or return corrupt data
- Devices that use clock stretching don't work

**Solution**:

If controller doesn't support clock stretching:
```c
static const struct i2c_adapter_quirks my_i2c_quirks = {
	.flags = I2C_AQ_NO_CLK_STRETCH,
};

id->adap.quirks = &my_i2c_quirks;
```

If controller supports it, ensure it's enabled:
```c
// Enable clock stretching in control register
reg = readl(i2c->base + CTRL_REG);
reg |= CLK_STRETCH_ENABLE;
writel(reg, i2c->base + CTRL_REG);
```

## Debugging with Logic Analyzer

### Essential Signals to Probe

1. **SCL (Serial Clock)**: Clock line
2. **SDA (Serial Data)**: Data line
3. **Interrupt line** (optional): Verify interrupt timing

### What to Look For

**Normal I2C Transfer**:
```
START - ADDR[7:1] + R/W - ACK - DATA - ACK - ... - STOP
```

**Common Issues**:
- Missing START condition: Check controller initialization
- Missing ACK: Device not responding (wrong address or not present)
- Clock stretching: SDA holds SCL low (device needs more time)
- Bus stuck: SDA stuck low, no clock pulses

### Signal Quality Checks

```bash
# Check rise time (should be < 1μs for 100kHz)
# - Too slow: Increase pull-up resistor value or reduce capacitance
# - Too fast: May cause signal integrity issues

# Check for ringing or overshoot
# - Add series resistor (e.g., 100Ω) close to master

# Check voltage levels
# - Logic high should be > 0.7 * VDD
# - Logic low should be < 0.3 * VDD
```

## Kernel Debug Options

Enable additional kernel debugging:

```kconfig
# In kernel config
CONFIG_I2C_DEBUG_CORE=y      # I2C core debug messages
CONFIG_I2C_DEBUG_ALGO=y      # Algorithm debug messages
CONFIG_I2C_DEBUG_BUS=y       # Bus driver debug messages
```

## Sysfs Debugging Interface

Useful sysfs entries for debugging:

```bash
# List I2C adapters
ls /sys/class/i2c-adapter/

# Check adapter name
cat /sys/class/i2c-adapter/i2c-0/name

# List devices on bus
ls /sys/bus/i2c/devices/

# Check device presence
cat /sys/bus/i2c/devices/0-0050/name

# Check device tree node
cat /sys/firmware/devicetree/base/i2c@e0004000/compatible
```

## Performance Analysis

### Measuring Transfer Time

```c
// In driver
ktime_t start, end;
s64 delta_us;

start = ktime_get();
ret = i2c_master_xfer(adap, msgs, num);
end = ktime_get();

delta_us = ktime_us_delta(end, start);
dev_info(&adap->dev, "Transfer took %lld us\n", delta_us);
```

### Expected Transfer Times

```
# 100 kHz mode (Standard)
# ~10 μs per byte (start + addr + ack + 8 bits + ack + stop)

# 400 kHz mode (Fast)
# ~2.5 μs per byte

# Example: 16-byte read at 400 kHz
# Expected: ~40-50 μs
```

## Testing Checklist

1. **Basic functionality**:
   - [ ] `i2cdetect -l` shows adapter
   - [ ] `i2cdetect -y 0` scans successfully
   - [ ] Known device responds at correct address

2. **Clock configuration**:
   - [ ] Clock enabled in probe
   - [ ] Clock frequency matches devicetree
   - [ ] Clock divisor calculated correctly

3. **Interrupt handling**:
   - [ ] IRQ registered successfully
   - [ ] `/proc/interrupts` shows interrupt count increasing
   - [ ] ISR clears interrupt status

4. **Bus recovery**:
   - [ ] `bus_recovery_info` configured (if supported)
   - [ ] Recovery works when SDA stuck low
   - [ ] GPIO recovery pins accessible

5. **Error handling**:
   - [ ] NACK returns `-ENXIO`
   - [ ] Timeout returns `-ETIMEDOUT`
   - [ ] Arbitration loss returns `-EAGAIN`

6. **Quirks**:
   - [ ] Hardware limitations documented in `quirks`
   - [ ] Large transfers split correctly
   - [ ] Unsupported operations return `-EOPNOTSUPP`
