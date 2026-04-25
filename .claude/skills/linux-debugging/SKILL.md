---
name: linux-debugging
description: Comprehensive guide to Linux kernel debugging techniques including printk/dynamic debug, ftrace/tracepoints, debugfs, KASAN/UBSAN/KCSAN sanitizers, lockdep, kmemleak, kgdb, perf profiling, and Raspberry Pi 4 testing. Use when debugging kernel drivers, analyzing crashes/oops, tracing execution, detecting memory errors, profiling performance, or troubleshooting issues.
---

# Linux Kernel Debugging

## When to Use This Skill

### AI Detection Triggers

Use this skill when you encounter:

**Error Messages and Crashes**:
- "BUG: unable to handle kernel NULL pointer dereference"
- "kernel panic", "oops", "kernel BUG at"
- "segmentation fault", "general protection fault"
- "stack trace", "call trace", "RIP:", "IP:"

**Memory Errors**:
- "use-after-free", "out-of-bounds", "slab corruption"
- "KASAN:", "UBSAN:", "memory leak"
- "double free", "invalid pointer"

**Locking Issues**:
- "deadlock", "circular locking dependency"
- "lockdep", "possible circular dependency detected"
- "IRQ-safe vs IRQ-unsafe", "lock inversion"

**Performance Issues**:
- "performance profiling", "bottleneck", "slow"
- "CPU usage", "latency", "throughput"

**Driver Debugging**:
- "driver not probing", "device not detected"
- "SPI/I2C communication failure", "timeout"
- "interrupt not firing", "IRQ handler"
- "register dump", "hardware state"

**Testing on Hardware**:
- "Raspberry Pi", "RPi4", "test on hardware"
- "devicetree overlay", "serial console"

## Quick Start Guide

### 1. Basic Logging

**Add debug prints**:
```c
#include <linux/device.h>

static int my_probe(struct spi_device *spi)
{
	dev_info(&spi->dev, "Probe started\n");

	// Use dev_dbg() for verbose debug (needs dynamic debug)
	dev_dbg(&spi->dev, "Register 0x%02x = 0x%08x\n", reg, val);

	// Use dev_err() for errors
	dev_err(&spi->dev, "Initialization failed: %d\n", ret);

	return 0;
}
```

**View logs**:
```bash
# Follow kernel log in real-time
dmesg -w

# Show only errors and warnings
dmesg --level=err,warn
```

### 2. Enable Dynamic Debug

**Runtime control**:
```bash
# Enable all debug messages in a file
echo "file drivers/iio/adc/ad7124.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable for specific function
echo "func ad7124_read_raw +p" > /sys/kernel/debug/dynamic_debug/control

# Enable for entire module
echo "module ad7124 +p" > /sys/kernel/debug/dynamic_debug/control
```

### 3. Function Tracing

**Trace driver functions**:
```bash
cd /sys/kernel/tracing

# Trace specific functions
echo 'ad7124_*' > set_ftrace_filter
echo function > current_tracer

echo 1 > tracing_on
# ... trigger operation ...
echo 0 > tracing_on

cat trace | less
```

### 4. Detect Memory Errors

**Enable KASAN** (kernel config):
```kconfig
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y
```

**Boot and test** - KASAN will automatically report:
- Out-of-bounds accesses
- Use-after-free bugs
- Stack overflows

### 5. Analyze Crashes

**Decode stack trace**:
```bash
# Capture oops
dmesg > oops.txt

# Decode to source lines
./scripts/decode_stacktrace.sh vmlinux /path/to/modules < oops.txt
```

## Common Debugging Workflows

### Workflow 1: Driver Not Probing

```bash
# 1. Check driver loaded
lsmod | grep driver_name

# 2. Check devicetree
ls /sys/firmware/devicetree/base/

# 3. Enable probe debugging
echo "file drivers/iio/adc/ad7124.c +p" > /sys/kernel/debug/dynamic_debug/control
dmesg -w

# 4. Check compatible string matches
grep -r "compatible" /sys/firmware/devicetree/base/

# 5. Verify hardware ID read
# Add dev_info() in probe to print chip ID
```

### Workflow 2: SPI/I2C Communication Failure

```c
// Add register access debugging
static int my_spi_write(struct spi_device *spi, u8 reg, u32 val)
{
	int ret;

	dev_dbg(&spi->dev, "Write: reg=0x%02x val=0x%08x\n", reg, val);

	ret = spi_write(...);
	if (ret)
		dev_err(&spi->dev, "SPI write failed: %d\n", ret);

	return ret;
}

static int my_spi_read(struct spi_device *spi, u8 reg, u32 *val)
{
	int ret;

	ret = spi_read(...);
	if (ret) {
		dev_err(&spi->dev, "SPI read failed: %d\n", ret);
		return ret;
	}

	dev_dbg(&spi->dev, "Read: reg=0x%02x val=0x%08x\n", reg, *val);
	return 0;
}
```

```bash
# Enable SPI debug
echo "module spi_bcm2835 +p" > /sys/kernel/debug/dynamic_debug/control
echo "module ad7124 +p" > /sys/kernel/debug/dynamic_debug/control

# Dump SPI transfers
echo 1 > /sys/kernel/debug/tracing/events/spi/enable
cat /sys/kernel/debug/tracing/trace_pipe
```

### Workflow 3: Memory Corruption

**Enable sanitizers** (kernel config):
```kconfig
CONFIG_KASAN=y           # Detect out-of-bounds and use-after-free
CONFIG_UBSAN=y           # Detect undefined behavior
CONFIG_DEBUG_KMEMLEAK=y  # Detect memory leaks
CONFIG_PROVE_LOCKING=y   # Detect deadlocks
```

**Test with sanitizers enabled**:
```bash
# Build kernel with sanitizers
make menuconfig  # Enable options above
make -j$(nproc)

# Boot and test
# Sanitizers will automatically report issues
dmesg | grep -E "KASAN|UBSAN|kmemleak|lockdep"
```

### Workflow 4: Interrupt Not Firing

```c
static irqreturn_t my_irq_handler(int irq, void *dev_id)
{
	struct my_device *dev = dev_id;

	dev_dbg(&dev->spi->dev, "IRQ fired\n");

	u32 status = read_status_reg(dev);
	dev_dbg(&dev->spi->dev, "Status: 0x%08x\n", status);

	return IRQ_HANDLED;
}

static int my_probe(struct spi_device *spi)
{
	// ...

	ret = devm_request_threaded_irq(&spi->dev, spi->irq, NULL,
					my_irq_handler,
					IRQF_TRIGGER_FALLING | IRQF_ONESHOT,
					spi_get_device_id(spi)->name, st);
	if (ret) {
		dev_err(&spi->dev, "Failed to request IRQ %d: %d\n", spi->irq, ret);
		return ret;
	}

	dev_info(&spi->dev, "IRQ %d registered\n", spi->irq);

	// Verify IRQ is not masked
	dev_dbg(&spi->dev, "IRQ flags: 0x%08lx\n", irq_get_trigger_type(spi->irq));

	return 0;
}
```

```bash
# Check interrupt stats
cat /proc/interrupts | grep -i driver_name

# Trace interrupts
echo 1 > /sys/kernel/debug/tracing/events/irq/enable
cat /sys/kernel/debug/tracing/trace_pipe
```

### Workflow 5: Performance Profiling

```bash
# Record CPU profiling for 10 seconds
perf record -a -g sleep 10

# View report
perf report

# Function statistics
perf stat -a sleep 10

# Live top view
perf top
```

## Debugging Tools Reference

### Kernel Logging
- **printk/pr_*()**: Basic kernel logging with log levels
- **dev_*()**: Device-specific logging (includes device name)
- **dynamic debug**: Runtime-controllable debug messages
- **print_hex_dump()**: Binary buffer dumping
- **debugfs**: Custom debug interfaces

See: [reference/printk-debug.md](reference/printk-debug.md)

### Function Tracing
- **ftrace**: Function and event tracing infrastructure
- **function tracer**: Trace all function calls
- **function_graph**: Show call hierarchy with timing
- **tracepoints**: Trace specific kernel events

See: [reference/ftrace.md](reference/ftrace.md)

### Memory Error Detection
- **KASAN**: Detects out-of-bounds and use-after-free (3 modes: generic, sw-tags, hw-tags)
- **UBSAN**: Detects undefined behavior (overflow, division by zero, shifts)
- **KCSAN**: Detects data races and concurrency issues
- **lockdep**: Detects deadlocks and lock ordering issues
- **kmemleak**: Detects memory leaks

See: [reference/sanitizers.md](reference/sanitizers.md)

### Advanced Tools
- **kgdb**: GDB-based kernel debugging
- **perf**: Performance counters and profiling
- **crash**: Kernel crash dump analysis
- **BPF/bpftrace**: Dynamic tracing and filtering
- **decode_stacktrace.sh**: Convert addresses to source lines

See: [reference/advanced-tools.md](reference/advanced-tools.md)

### Hardware Testing
- **Raspberry Pi 4**: Serial console, network boot, overlays
- **Serial debugging**: Early printk, console output
- **Device tree**: Overlays, verification, debugging

See: [reference/raspberry-pi.md](reference/raspberry-pi.md)

## Debugfs Integration for IIO Drivers

### Add Register Access Interface

```c
#include <linux/debugfs.h>
#include <linux/seq_file.h>

/**
 * debugfs_reg_access - Direct register access via debugfs
 *
 * Allows reading/writing registers through:
 * /sys/kernel/debug/iio/iio:deviceX/direct_reg_access
 */
static int ad7124_debugfs_reg_access(struct iio_dev *indio_dev,
				     unsigned int reg, unsigned int writeval,
				     unsigned int *readval)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	if (readval)
		return ad7124_spi_read(st, reg, readval);
	else
		return ad7124_spi_write(st, reg, writeval);
}

static const struct iio_info ad7124_info = {
	.read_raw = ad7124_read_raw,
	.write_raw = ad7124_write_raw,
	.debugfs_reg_access = ad7124_debugfs_reg_access,
};
```

**Usage**:
```bash
# Read register 0x10
echo 0x10 > /sys/kernel/debug/iio/iio:device0/direct_reg_access
cat /sys/kernel/debug/iio/iio:device0/direct_reg_access

# Write register 0x10 with value 0x1234
echo "0x10 0x1234" > /sys/kernel/debug/iio/iio:device0/direct_reg_access
```

### Add Custom Status Display

```c
static int ad7124_status_show(struct seq_file *s, void *unused)
{
	struct ad7124_state *st = s->private;
	int i;

	seq_puts(s, "AD7124 Status\n");
	seq_puts(s, "=============\n");

	// Read and display registers
	for (i = 0; i < 16; i++) {
		u32 val;
		ad7124_spi_read(st, i, &val);
		seq_printf(s, "Reg[0x%02x] = 0x%08x\n", i, val);
	}

	seq_printf(s, "\nActive channels: 0x%02x\n", st->active_channels);
	seq_printf(s, "Sample rate: %d SPS\n", st->sample_rate);

	return 0;
}
DEFINE_SHOW_ATTRIBUTE(ad7124_status);

static int ad7124_probe(struct spi_device *spi)
{
	// ... after iio_device_register ...

	// Create custom debugfs file
	if (iio_get_debugfs_dentry(indio_dev)) {
		debugfs_create_devm_seqfile(&spi->dev, "status",
					    iio_get_debugfs_dentry(indio_dev),
					    ad7124_status_show);
	}

	return 0;
}
```

**Usage**:
```bash
cat /sys/kernel/debug/iio/iio:device0/status
```

## Best Practices

### 1. Progressive Debug Logging

Start with minimal logging, add more as needed:

```c
// Level 1: Always log probe and errors
dev_info(&spi->dev, "Probe started, chip ID: 0x%04x\n", id);
dev_err(&spi->dev, "Operation failed: %d\n", ret);

// Level 2: Debug-level state changes (dynamic debug)
dev_dbg(&spi->dev, "Switching to channel %d\n", channel);

// Level 3: Verbose register access (dynamic debug)
dev_dbg(&spi->dev, "Write: reg=0x%02x val=0x%08x\n", reg, val);

// Level 4: Binary dumps (dynamic debug)
print_hex_dump_debug("SPI TX: ", DUMP_PREFIX_OFFSET, 16, 1, buf, len, true);
```

### 2. Validate Assumptions

```c
// Check return values
ret = regmap_read(regmap, reg, &val);
if (ret) {
	dev_err(dev, "Failed to read register 0x%02x: %d\n", reg, ret);
	return ret;
}

// Validate pointers
if (WARN_ON(!st || !st->spi)) {
	dev_err(dev, "Invalid state\n");
	return -EINVAL;
}

// Check hardware state
if (val != expected) {
	dev_warn(dev, "Unexpected value: 0x%08x (expected 0x%08x)\n",
		 val, expected);
}
```

### 3. Use WARN Appropriately

```c
// WARN for unexpected but recoverable conditions
if (WARN_ON(channel >= st->num_channels)) {
	dev_err(dev, "Invalid channel %d\n", channel);
	return -EINVAL;
}

// Avoid BUG_ON - use WARN_ON with error return instead
if (WARN_ON(!st))
	return -EINVAL;
```

### 4. Add Context to Error Messages

```c
// Bad: Generic error
dev_err(dev, "Failed\n");

// Good: Specific error with context
dev_err(dev, "Failed to initialize channel %d: %d\n", channel, ret);

// Better: Include hardware state
dev_err(dev, "Failed to initialize channel %d (status=0x%08x): %d\n",
	channel, status, ret);
```

## Kernel Configuration for Debugging

Essential debug options:

```kconfig
# Memory error detection
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y
CONFIG_UBSAN=y
CONFIG_DEBUG_KMEMLEAK=y

# Lock debugging
CONFIG_PROVE_LOCKING=y
CONFIG_DEBUG_LOCK_ALLOC=y
CONFIG_LOCK_STAT=y

# Stack unwinding
CONFIG_FRAME_POINTER=y
CONFIG_STACK_VALIDATION=y

# Debug information
CONFIG_DEBUG_INFO=y
CONFIG_DEBUG_INFO_DWARF4=y

# Dynamic debug
CONFIG_DYNAMIC_DEBUG=y

# Debugfs
CONFIG_DEBUG_FS=y

# Ftrace
CONFIG_FUNCTION_TRACER=y
CONFIG_FUNCTION_GRAPH_TRACER=y
CONFIG_DYNAMIC_FTRACE=y
CONFIG_STACK_TRACER=y
```

## Related Skills

- **linux-checkpatch-sparse**: Code quality and static analysis
- **linux-iio**: IIO subsystem debugging and testing
- **linux-devicetree**: Devicetree debugging and validation
- **linux-kconfig-makefile**: Enabling debug options in kernel config

## Additional Resources

**Documentation**:
- Dynamic debug: Documentation/admin-guide/dynamic-debug-howto.rst
- KASAN: Documentation/dev-tools/kasan.rst
- UBSAN: Documentation/dev-tools/ubsan.rst
- Ftrace: Documentation/trace/ftrace.rst
- Lockdep: Documentation/locking/lockdep-design.rst

**Tools**:
- scripts/decode_stacktrace.sh - Decode kernel oops
- scripts/checkpatch.pl - Code style checking
- scripts/get_maintainer.pl - Find subsystem maintainers
