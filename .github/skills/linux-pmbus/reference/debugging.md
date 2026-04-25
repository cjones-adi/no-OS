# PMBus Debugging Techniques

Detailed guide for debugging PMBus drivers, covering sysfs interface, debugfs, dynamic debug, I2C tracing, and common issues.

## Sysfs HWMON Interface

PMBus drivers expose monitoring attributes via sysfs:

### Finding PMBus Devices

```bash
# List all HWMON devices
ls /sys/class/hwmon/

# Find PMBus device by name
grep -r "adm1275" /sys/class/hwmon/*/name
# Output: /sys/class/hwmon/hwmon2/name:adm1275

cd /sys/class/hwmon/hwmon2/device/
```

### Voltage Monitoring

```bash
# Input voltage
cat in0_input       # VIN (millivolts)
cat in0_min         # VIN minimum limit
cat in0_max         # VIN maximum limit
cat in0_lcrit       # VIN critical low
cat in0_crit        # VIN critical high
cat in0_label       # "vin" or custom label
cat in0_alarm       # 1 = alarm active

# Output voltage (multi-page: in1, in2, in3...)
cat in1_input       # VOUT page 0 (millivolts)
cat in2_input       # VOUT page 1
cat in1_lcrit       # VOUT critical low
cat in1_crit        # VOUT overvoltage limit
cat in1_alarm       # VOUT alarm status
```

### Current Monitoring

```bash
# Input current
cat curr1_input     # IIN (milliamps)
cat curr1_max       # IIN max limit
cat curr1_alarm     # IIN alarm

# Output current
cat curr2_input     # IOUT (milliamps)
cat curr2_max       # IOUT overcurrent limit
cat curr2_crit      # IOUT critical limit
cat curr2_alarm     # IOUT alarm
cat curr2_label     # "iout1" or custom
```

### Power Monitoring

```bash
# Input power
cat power1_input    # PIN (microwatts)
cat power1_max      # PIN max limit
cat power1_alarm    # PIN alarm

# Output power
cat power2_input    # POUT (microwatts)
cat power2_max      # POUT max limit
```

### Temperature Monitoring

```bash
cat temp1_input     # Temperature sensor 1 (millidegrees Celsius)
cat temp1_max       # Temperature warning limit
cat temp1_crit      # Temperature critical limit
cat temp1_alarm     # Temperature alarm status
cat temp1_label     # "temp1" or custom
```

### Peak Value Tracking

```bash
# Peak values (if supported by device)
cat in1_highest     # Peak output voltage
cat in1_lowest      # Minimum output voltage
cat curr2_highest   # Peak output current
cat power1_highest  # Peak input power

# Reset peak tracking
echo 1 > in1_reset_history      # Reset VOUT history
echo 1 > curr2_reset_history    # Reset IOUT history
echo 1 > power1_reset_history   # Reset PIN history
```

### Status Registers

```bash
# Fault status (if exposed)
cat status_word     # PMBus STATUS_WORD register (hex)
cat status_vout     # VOUT fault bits
cat status_iout     # IOUT fault bits
cat status_input    # VIN fault bits
cat status_temp     # Temperature fault bits
```

## Debugfs

Some PMBus devices expose additional debug info via debugfs:

```bash
# Enable debugfs (if not mounted)
mount -t debugfs none /sys/kernel/debug

# PMBus debugfs entries
ls /sys/kernel/debug/pmbus/

# ADM1266 example: sequencer state
cat /sys/kernel/debug/pmbus/1-0042/sequencer_state

# Device-specific debug registers
cat /sys/kernel/debug/pmbus/1-0040/registers
```

## Dynamic Debug

Enable verbose PMBus kernel messages:

```bash
# Enable PMBus core debug
echo 'file pmbus_core.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable specific driver debug
echo 'file adm1275.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable all PMBus directory debug
echo 'file drivers/hwmon/pmbus/* +p' > /sys/kernel/debug/dynamic_debug/control

# Check kernel messages
dmesg | grep -i pmbus
dmesg | tail -f | grep pmbus  # Live monitoring
```

### Useful Debug Messages

PMBus core prints:
- Page switching: `"switching to page %d"`
- Register access: `"read word data: page=%d reg=0x%02x"`
- Coefficient application: `"using direct format: m=%d b=%d R=%d"`
- Virtual command handling: `"virtual command 0x%03x not supported"`

## I2C Bus Tracing

### i2c-tools

```bash
# Scan I2C bus
i2cdetect -y 0          # Scan bus 0
i2cdetect -y -r 0       # Use read byte for probing

# Dump all registers
i2cdump -y 0 0x40       # Dump device at address 0x40
i2cdump -y 0 0x40 w     # Word (16-bit) dump

# Read specific register
i2cget -y 0 0x40 0x88   # Read READ_VIN (0x88)
i2cget -y 0 0x40 0x8B w # Read READ_VOUT (word)

# Write register
i2cset -y 0 0x40 0x00 0x02  # Set PAGE to 2
i2cset -y 0 0x40 0x21 0x3000 w  # Set VOUT_COMMAND
```

### Kernel I2C Tracing

```bash
# Enable I2C tracepoints
echo 1 > /sys/kernel/debug/tracing/events/i2c/enable
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Trigger PMBus access (e.g., read sysfs)
cat /sys/class/hwmon/hwmon2/in1_input

# View trace
cat /sys/kernel/debug/tracing/trace

# Disable tracing
echo 0 > /sys/kernel/debug/tracing/tracing_on
echo 0 > /sys/kernel/debug/tracing/events/i2c/enable
```

**Example trace output**:
```
i2c_write: i2c-0 #0 a=040 f=0000 l=2 [00-02]     # Write PAGE=2
i2c_read:  i2c-0 #1 a=040 f=0001 l=1 [8B]        # Write READ_VOUT reg
i2c_read:  i2c-0 #1 a=040 f=0001 l=2 [50-0C]     # Read VOUT value
```

### SMBus vs I2C

PMBus uses SMBus protocol (subset of I2C):
- **SMBus Block Read**: Used for manufacturer-specific commands
- **SMBus Word Read**: Standard 16-bit reads (READ_VIN, READ_VOUT)
- **PEC (Packet Error Checking)**: Optional CRC byte

```bash
# Check if PEC is enabled
cat /sys/bus/i2c/devices/0-0040/pec
# 0 = disabled, 1 = enabled

# Enable PEC
echo 1 > /sys/bus/i2c/devices/0-0040/pec
```

## Common Issues and Solutions

### 1. Device Not Detected

**Symptoms**: Driver doesn't probe, no `/sys/class/hwmon/` entry

**Debugging**:
```bash
# Check I2C bus
i2cdetect -y 0

# Check devicetree
ls /sys/firmware/devicetree/base/soc/i2c*/

# Check kernel log
dmesg | grep -E "i2c|pmbus"
```

**Solutions**:
- Verify I2C address in devicetree matches hardware
- Check pull-up resistors on I2C bus
- Verify SMBALERT# pin (some devices require pull-up)
- Check power supply to device

### 2. Incorrect Voltage/Current Readings

**Symptoms**: Values are off by 10x, 100x, or completely wrong

**Debugging**:
```bash
# Read raw register value
i2cget -y 0 0x40 0x8B w  # READ_VOUT

# Enable PMBus debug to see coefficient application
echo 'file pmbus_core.c +p' > /sys/kernel/debug/dynamic_debug/control
cat /sys/class/hwmon/hwmon*/in1_input
dmesg | tail
```

**Solutions**:
- **Direct format**: Verify m, b, R coefficients match datasheet
- **Shunt resistor**: Check `shunt-resistor-micro-ohms` in devicetree
- **Voltage range**: Verify VRANGE configuration bit
- **Linear format**: Ensure format is set to `linear`, not `direct`

**Example fix**:
```c
// Wrong: m is off by 10x
info->m[PSC_CURRENT_OUT] = 80;   // ❌

// Correct: account for mA units
info->m[PSC_CURRENT_OUT] = 807;  // ✅
info->R[PSC_CURRENT_OUT] = -1;   // Divide by 10
```

### 3. Virtual Command Failures

**Symptoms**: `cat in1_highest` returns error or wrong value

**Debugging**:
```bash
# Enable driver debug
echo 'file adm1275.c +p' > /sys/kernel/debug/dynamic_debug/control

# Try to read peak value
cat /sys/class/hwmon/hwmon*/in1_highest

# Check kernel log
dmesg | grep "virtual command"
```

**Solutions**:
- Ensure `read_word_data` callback handles virtual command
- Return `-ENODATA` for unsupported virtual commands
- Return `-ENXIO` for feature-dependent commands (e.g., PMBUS_HAVE_PIN_MAX not set)

**Example fix**:
```c
static int mypmbus_read_word_data(struct i2c_client *client, int page,
                                  int phase, int reg)
{
	switch (reg) {
	case PMBUS_VIRT_READ_IOUT_MAX:
		return pmbus_read_word_data(client, 0, 0xff, MFR_PEAK_IOUT);

	case PMBUS_VIRT_RESET_IOUT_HISTORY:
		return 0;  // Signal supported

	default:
		return -ENODATA;  // ✅ Must return -ENODATA
	}
}
```

### 4. Multi-Page Issues

**Symptoms**: Wrong values on pages > 0, or only page 0 works

**Debugging**:
```bash
# Check page count
ls /sys/class/hwmon/hwmon*/in* | wc -l

# Enable PMBus debug to see page switching
echo 'file pmbus_core.c +p' > /sys/kernel/debug/dynamic_debug/control
cat /sys/class/hwmon/hwmon*/in2_input  # Page 1
dmesg | grep "page"
```

**Solutions**:
- Verify `info->pages` matches device page count
- Check per-page functionality flags `info->func[i]`
- Ensure PAGE command (0x00) is supported
- Some devices auto-increment page; check if core needs to handle it

### 5. Write Protection Errors

**Symptoms**: `echo 5000 > in1_max` returns `-EPERM` or no effect

**Debugging**:
```bash
# Check write protection status
i2cget -y 0 0x40 0x10  # WRITE_PROTECT register (if exists)

# Try with PMBus core write protection handling
modprobe pmbus_core wp=3  # Try to clear protection
```

**Solutions**:
- Check WRITE_PROTECT register (command 0x10)
- Add platform data flag: `PMBUS_WRITE_PROTECTED`
- Implement `write_word_data` callback to handle write protection

### 6. Status/Alarm Issues

**Symptoms**: Alarms don't trigger, or always show 1

**Debugging**:
```bash
# Check status registers
cat /sys/class/hwmon/hwmon*/status_*

# Read raw status bytes
i2cget -y 0 0x40 0x78  # STATUS_BYTE
i2cget -y 0 0x40 0x79 w  # STATUS_WORD
i2cget -y 0 0x40 0x7A  # STATUS_VOUT
```

**Solutions**:
- Ensure `PMBUS_HAVE_STATUS_*` flags are set
- Check fault limit configuration (OV/UV/OC limits)
- Some devices need `PMBUS_SKIP_STATUS_CHECK` flag
- Clear faults: `echo 1 > /sys/class/hwmon/hwmon*/clear_faults` (if exposed)

### 7. Regulator Integration Issues

**Symptoms**: Regulator not registered, or voltage control doesn't work

**Debugging**:
```bash
# Check regulator registration
ls /sys/class/regulator/regulator*/name

# Check PMBus regulator
cat /sys/class/regulator/regulator*/name | grep -i vout
```

**Solutions**:
- Ensure `CONFIG_SENSORS_*_REGULATOR=y` in kernel config
- Set `info->num_regulators` and `info->reg_desc`
- Add `regulators` node in devicetree
- Check voltage range matches regulator min/max in DT

## Performance Debugging

### Slow sysfs Reads

If reading sysfs attributes is slow:

```bash
# Time sysfs read
time cat /sys/class/hwmon/hwmon*/in1_input

# Check for unnecessary page switching
echo 'file pmbus_core.c +p' > /sys/kernel/debug/dynamic_debug/control
cat /sys/class/hwmon/hwmon*/in*_input > /dev/null
dmesg | grep "switching to page" | wc -l
```

**Solutions**:
- Use cached peak values instead of polling hardware
- Batch reads with `get_multiple` callback
- Reduce I2C bus frequency if communication errors occur

### Busy-Wait Devices

LT7170/LTC3883 require polling before access:

```bash
# Check for timeouts
dmesg | grep -i timeout

# Increase timeout if needed (in driver source)
#define LTC_POLL_TIMEOUT  500  // Increase from 100ms
```

## Kernel Oops/Crash Debugging

If PMBus driver causes kernel crash:

```bash
# Enable KASAN (kernel must be built with CONFIG_KASAN=y)
# Reboot and reproduce crash

# Check for null pointer dereferences
# Common issue: accessing pmbus_driver_info before initialization

# Enable lockdep (CONFIG_PROVE_LOCKING=y)
# Checks for locking issues (e.g., mutex in atomic context)
```

**Common crash causes**:
- Using non-`_cansleep` functions in I2C driver (atomic context violation)
- Null pointer: forgetting to allocate driver data
- Use-after-free: not using `devm_*` functions
- Locking: holding mutex during `i2c_smbus_*` call (which may sleep)

## Useful Kernel Configs for Debugging

```kconfig
CONFIG_DEBUG_DRIVER=y           # Driver core debug messages
CONFIG_I2C_DEBUG_CORE=y         # I2C core debug
CONFIG_I2C_DEBUG_ALGO=y         # I2C algorithm debug
CONFIG_I2C_DEBUG_BUS=y          # I2C bus debug
CONFIG_DYNAMIC_DEBUG=y          # Enable dynamic debug
CONFIG_HWMON_DEBUG_CHIP=y       # HWMON chip-level debug
CONFIG_DEBUG_GPIO=y             # GPIO debug (if using GPIO)
CONFIG_REGULATOR_DEBUG=y        # Regulator debug
```

## Quick Diagnostic Script

```bash
#!/bin/bash
# pmbus_debug.sh - Quick PMBus diagnostic

echo "=== PMBus Devices ==="
ls /sys/class/hwmon/hwmon*/name

echo -e "\n=== I2C Devices ==="
i2cdetect -y 0

echo -e "\n=== PMBus Attributes ==="
find /sys/class/hwmon/hwmon*/ -name "in*_input" -exec sh -c 'echo -n "$1: "; cat $1' _ {} \;

echo -e "\n=== PMBus Errors ==="
dmesg | grep -iE "pmbus|i2c.*error|i2c.*fail"

echo -e "\n=== Enable PMBus Debug ==="
echo 'file drivers/hwmon/pmbus/* +p' > /sys/kernel/debug/dynamic_debug/control
echo "PMBus debug enabled. Run: dmesg | tail -f"
```

Run with:
```bash
chmod +x pmbus_debug.sh
./pmbus_debug.sh
```
