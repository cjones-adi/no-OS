# Advanced Debugging Tools

## Analyzing Kernel Oops and Panics

### Decoding Stack Traces

**Using decode_stacktrace.sh**:
```bash
# Capture oops output
dmesg > oops.txt

# Decode with vmlinux and modules
./scripts/decode_stacktrace.sh vmlinux /path/to/modules < oops.txt

# Shows exact source file and line numbers
```

**Using addr2line manually**:
```bash
addr2line -e vmlinux -f -i 0xffffffffa0123456

# Or for modules
addr2line -e drivers/iio/adc/ad7124.ko -f -i 0x1234
```

### Common Oops Causes

**NULL pointer dereference**:
```c
struct data *ptr = NULL;
ptr->field = 123;  // BUG: unable to handle kernel NULL pointer dereference
```

**Use-after-free** (enable KASAN to detect):
```c
kfree(buffer);
memcpy(buffer, src, len);  // Corrupted or crashes
```

**Stack overflow**:
```c
char huge_buffer[1024*1024];  // Too large for kernel stack (typically 8-16KB)
```

### Interpreting Oops Messages

```
BUG: unable to handle kernel NULL pointer dereference at 0000000000000010
IP: [<ffffffffa0123456>] ad7124_read+0x56/0x123 [ad7124]
PGD 0
Oops: 0000 [#1] SMP
CPU: 0 PID: 1234 Comm: cat Not tainted 6.5.0 #1
...
```

- `NULL pointer dereference at 0x10`: Tried to access offset 0x10 of NULL pointer
- `IP`: Instruction pointer (where crash occurred)
- `Oops: 0000`: Error code (0000 = read, 0002 = write)
- `[#1]`: First oops (number increments with each oops)
- `SMP`: Symmetric multiprocessing enabled

## Performance Profiling

### perf - Performance Counters

**Record CPU profiling**:
```bash
# Record all CPUs for 10 seconds
perf record -a -g sleep 10

# Record specific command
perf record -g ./my_test_app

# Record specific events
perf record -e cycles,cache-misses -a sleep 10

# View report
perf report

# Show annotated source
perf annotate
```

**Function statistics**:
```bash
perf stat -a sleep 10

# Shows:
# - CPU cycles
# - Instructions executed
# - Cache hits/misses
# - Branch prediction
```

**Live top-like view**:
```bash
perf top
```

## KGDB - Kernel Debugger

KGDB provides GDB-based kernel debugging over serial or ethernet.

### Setup

**Kernel configuration**:
```kconfig
CONFIG_KGDB=y
CONFIG_KGDB_SERIAL_CONSOLE=y
CONFIG_KGDB_KDB=y
```

**Boot parameters**:
```bash
# Serial console
kgdboc=ttyS0,115200 kgdbwait

# KDB mode (built-in debugger)
kgdboc=kbd kgdbwait
```

### Usage

**On target (serial)**:
```bash
# Trigger breakpoint
echo g > /proc/sysrq-trigger
```

**On host**:
```bash
# Connect via serial
gdb vmlinux
(gdb) target remote /dev/ttyUSB0
(gdb) continue

# Set breakpoint
(gdb) break ad7124_probe
(gdb) continue

# Examine variables
(gdb) print st->regs[0]
(gdb) backtrace
```

## Crash Dump Analysis

### kdump - Kernel Crash Dumps

**Setup**:
```kconfig
CONFIG_KEXEC=y
CONFIG_CRASH_DUMP=y
```

```bash
# Reserve memory for crash kernel
crashkernel=256M
```

**Analyzing dumps**:
```bash
# Use crash utility
crash vmlinux vmcore

crash> bt  # backtrace
crash> log  # kernel log
crash> ps  # process list
crash> dis <function>  # disassemble
```

## System Tap and BPF

### BPF Tracing

**BCC tools**:
```bash
# Trace all kernel functions matching pattern
funccount 'ad7124_*'

# Trace function calls with arguments
trace 'ad7124_read_raw "%d", arg1'

# Profile on-CPU time
profile -F 99 -a -g

# Trace file I/O
filetop
```

**bpftrace**:
```bash
# Trace function entry/exit
bpftrace -e 'kprobe:ad7124_probe { printf("Probe called\n"); }'

# Trace with timestamp
bpftrace -e 'kprobe:ad7124_read_raw { printf("%lld: read\n", nsecs); }'
```

## Debugging Best Practices

### Add Debug Logging Strategically

```c
// At function entry
dev_dbg(dev, "%s: entry\n", __func__);

// Before critical operations
dev_dbg(dev, "Writing reg 0x%02x = 0x%08x\n", reg, val);

// After hardware operations
dev_dbg(dev, "Read reg 0x%02x = 0x%08x\n", reg, val);

// Error paths
dev_err(dev, "%s: failed at line %d, ret=%d\n", __func__, __LINE__, ret);
```

### Validate Assumptions

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
	dev_warn(dev, "Unexpected register value: 0x%08x (expected 0x%08x)\n",
		 val, expected);
}
```

### Use WARN/BUG Macros Appropriately

```c
// WARN for unexpected but recoverable conditions
if (WARN_ON(channel >= st->num_channels)) {
	dev_err(dev, "Invalid channel %d\n", channel);
	return -EINVAL;
}

// BUG_ON only for truly impossible conditions
BUG_ON(!st);  // Avoid - use WARN_ON instead

// Better alternative
if (WARN_ON(!st))
	return -EINVAL;
```
