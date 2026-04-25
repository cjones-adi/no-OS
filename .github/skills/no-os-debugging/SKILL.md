---
name: no-os-debugging
description: 'Complete guide to debugging no-OS embedded applications. Use when troubleshooting initialization failures, communication errors, device detection issues, adding debug logging, using JTAG/SWD debugging, analyzing error codes, or resolving common embedded issues.'
---

# no-OS Debugging Guide

Quick-start guide for debugging no-OS embedded applications using logging, UART console, JTAG/SWD, hardware tools, and systematic troubleshooting approaches.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/printf-debugging.md**:
- User asks: "how to add logging", "pr_info vs pr_debug", "log levels", "UART console"
- Questions about: logging macros, printf debugging, timestamp logging
- Need: complete logging API reference, UART setup patterns, checkpoint logging

**Triggers to read reference/gdb-debugging.md**:
- User asks: "how to use GDB", "JTAG debugging", "set breakpoint", "OpenOCD"
- Mentions: debugger, breakpoints, step through code, inspect variables
- Questions about: SVD files, debug configuration, GDB commands
- Need: JTAG/SWD setup, GDB workflow, register inspection, stack traces

**Triggers to read reference/tools.md**:
- User asks: "logic analyzer", "oscilloscope", "what hardware tools"
- Mentions: signal integrity, protocol analyzer, measure voltage/current
- Questions about: SPI/I2C debugging with hardware, signal quality, power issues
- Need: hardware debugging tools reference, systematic hardware debug approach

**Triggers to read reference/common-issues.md**:
- User reports: ENODEV, device not found, communication failure, init hangs
- Symptoms: product ID mismatch, 0xFFFF readings, timeout errors, crashes
- Questions about: "why EINVAL", "device not detected", "SPI not working"
- Need: systematic troubleshooting steps, error code meanings, specific scenarios

**Triggers to read reference/techniques.md**:
- User asks: "best practices", "debugging patterns", "error handling"
- Questions about: error propagation, defensive programming, performance debugging
- Need: advanced techniques, memory debugging, protocol debugging, regression testing

---

## When to Use This Skill

- Debug initialization failures in device drivers
- Troubleshoot SPI, I2C, or UART communication issues
- Add debug logging to drivers or applications
- Understand error codes and their meanings
- Resolve "device not found" (ENODEV) errors
- Use JTAG/SWD debugging with platform-specific tools
- Diagnose timing and synchronization issues
- Debug memory allocation failures
- Trace register read/write sequences
- Resolve build or runtime errors in no-OS projects

---

## Debugging Ecosystem Overview

The no-OS framework provides a comprehensive debugging infrastructure:

- **Structured logging system** with severity levels (emerg, alert, crit, err, warning, notice, info, debug)
- **Standard error codes** compatible with Linux errno values
- **UART-based console debugging** for printf-style debugging
- **Platform-specific JTAG/SWD support** for breakpoint debugging
- **Product ID verification** for device detection
- **Error propagation patterns** throughout driver stack

---

## Quick Start: Adding Debug Logging

### Step 1: Setup UART Console

```c
#include "no_os_uart.h"
#include "no_os_print_log.h"

int example_main(void)
{
    struct no_os_uart_desc *uart_desc;
    int ret;

    // Initialize UART
    ret = no_os_uart_init(&uart_desc, &uart_ip);
    if (ret)
        return ret;

    // Redirect logging to UART
    no_os_uart_stdio(uart_desc);

    // Now logging works
    pr_info("Debug console ready\n");

    // Rest of application
    return 0;
}
```

**UART Configuration** (from parameters.h):
```c
struct no_os_uart_init_param uart_ip = {
    .device_id = UART_DEVICE_ID,
    .baud_rate = 115200,  // Standard debug baud rate
    .platform_ops = UART_OPS,
    .extra = UART_EXTRA,
};
```

---

### Step 2: Add Logging to Your Code

```c
#include "no_os_print_log.h"

int device_init(struct device_desc **device, struct device_init_param *init_param)
{
    struct device_desc *desc;
    int ret;

    pr_info("Starting device initialization\n");

    // Allocate descriptor
    desc = no_os_calloc(1, sizeof(*desc));
    if (!desc) {
        pr_err("Memory allocation failed\n");
        return -ENOMEM;
    }

    // Initialize SPI
    ret = no_os_spi_init(&desc->spi_desc, init_param->spi_ip);
    if (ret) {
        pr_err("SPI initialization failed: %d\n", ret);
        goto error_desc;
    }

    pr_debug("SPI initialized successfully\n");

    // Read product ID
    ret = device_reg_read(desc, PRODUCT_ID_REG, &id);
    if (ret) {
        pr_err("Failed to read product ID: %d\n", ret);
        goto error_spi;
    }

    pr_info("Device detected: ID 0x%04X\n", id);

    *device = desc;
    return 0;

error_spi:
    no_os_spi_remove(desc->spi_desc);
error_desc:
    no_os_free(desc);
    return ret;
}
```

---

### Step 3: Configure Log Level

**Enable Debug Logging** (Makefile):
```makefile
# Show all debug messages
CFLAGS += -DNO_OS_LOG_LEVEL=NO_OS_LOG_DEBUG

# Enable timestamps (optional)
CFLAGS += -DPRINT_TIME
```

**Log Levels**:
```c
NO_OS_LOG_DEBUG    // Show everything (development)
NO_OS_LOG_INFO     // Default (normal operation)
NO_OS_LOG_ERR      // Errors only (production)
```

---

## Essential Logging Macros

### High-Severity Macros (with file/line/function context)

```c
pr_err("Device initialization failed: %d\n", ret);
// Output: [ERROR] file.c:42 (function_name): Device initialization failed: -22

pr_crit("Critical hardware failure\n");
pr_alert("Immediate action required\n");
pr_emerg("System unusable\n");
```

### Low-Severity Macros (minimal overhead)

```c
pr_info("Device initialized successfully\n");
pr_debug("Register 0x%02X = 0x%04X\n", reg, val);
pr_warning("Using default configuration\n");
pr_notice("Device ready for operation\n");
```

**Usage Guidelines**:
- Use `pr_err()` for errors
- Use `pr_info()` for normal operation messages
- Use `pr_debug()` for detailed debugging (only shows when DEBUG level enabled)
- Use `pr_warning()` for non-fatal issues

---

## Common Error Codes

### Standard Error Codes (from `no_os_error.h`)

```c
EINVAL      // -22: Invalid argument or parameter
EIO         // -5:  Input/output error (communication failure)
ENOMEM      // -12: Out of memory
ENODEV      // -19: No such device (device not found)
ENOTSUPP    // -524: Operation not supported
ETIMEDOUT   // -110: Timeout occurred
EBUSY       // -16: Device or resource busy
```

### Quick Error Diagnosis

**ENODEV** (-19) - Device not found:
- Check hardware connections (power, ground, SPI/I2C lines)
- Verify chip select (SPI) or address (I2C)
- Check SPI mode (CPOL/CPHA)
- Read value: 0xFFFF = line stuck high, 0x0000 = line stuck low

**EINVAL** (-22) - Invalid argument:
- NULL pointer passed to function
- Parameter out of valid range
- Invalid configuration value

**EIO** (-5) - Communication error:
- SPI/I2C transaction failed
- Bus timeout
- NACK received (I2C)

**ENOMEM** (-12) - Out of memory:
- Heap exhausted
- Increase heap size in linker script
- Check for memory leaks

---

## Error Handling Pattern

**Universal pattern used throughout no-OS**:

```c
int function_that_can_fail(void)
{
    int ret;

    ret = sub_function_1();
    if (ret)
        return ret;  // Propagate error

    ret = sub_function_2();
    if (ret)
        goto error_cleanup;  // Cleanup before return

    return 0;  // Success

error_cleanup:
    cleanup_resources();
    return ret;
}
```

**Key principles**:
- Check return value after every function call
- Return 0 on success, negative error code on failure
- Use `goto` for cleanup when resources allocated
- Propagate errors up the call stack

---

## Quick Debugging Scenarios

### Scenario 1: Device Not Detected (ENODEV)

**Symptom**:
```
[ERROR] Product ID mismatch: expected 0x00C2, got 0xFFFF
Device initialization failed: -19
```

**Quick Fix**:
1. Check hardware: power supply, ground, connections
2. Verify SPI/I2C configuration (speed, mode, address)
3. Use logic analyzer to verify signals
4. Add debug logging to register read:
   ```c
   pr_debug("Reading product ID from register 0x%02X\n", PRODUCT_ID_REG);
   ret = device_reg_read(desc, PRODUCT_ID_REG, &id);
   pr_debug("Read returned: %d, value: 0x%04X\n", ret, id);
   ```

**See**: `reference/common-issues.md` for complete troubleshooting steps.

---

### Scenario 2: SPI Communication Failure

**Symptom**:
```
SPI transaction failed: -5
```

**Quick Fix**:
1. Enable debug logging:
   ```c
   #define NO_OS_LOG_LEVEL NO_OS_LOG_DEBUG
   ```
2. Reduce SPI speed to test:
   ```c
   spi_ip->max_speed_hz = 100000;  // 100 kHz
   ```
3. Try different SPI modes (0-3)
4. Use logic analyzer to verify clock, data, chip select

**SPI Modes**:
```c
NO_OS_SPI_MODE_0  // CPOL=0, CPHA=0 (most common)
NO_OS_SPI_MODE_1  // CPOL=0, CPHA=1
NO_OS_SPI_MODE_2  // CPOL=1, CPHA=0
NO_OS_SPI_MODE_3  // CPOL=1, CPHA=1
```

**See**: `reference/common-issues.md` for systematic SPI debugging.

---

### Scenario 3: Initialization Hangs

**Symptom**: Application stops responding, no console output.

**Quick Fix**:
1. Add checkpoint logging:
   ```c
   pr_info("Checkpoint 1: Starting init\n");
   ret = step1_init();
   pr_info("Checkpoint 2: Step 1 complete\n");
   ret = step2_init();
   pr_info("Checkpoint 3: Step 2 complete\n");
   // Find where it stops
   ```
2. Use JTAG debugger to set breakpoints and step through
3. Check for NULL pointer dereferences
4. Verify memory allocation succeeded

**See**: `reference/gdb-debugging.md` for JTAG/SWD debugging workflow.

---

## Build Configuration for Debugging

### Enable Debug Symbols (Makefile)

```makefile
# Add debug symbols and disable optimizations
CFLAGS += -g3 -O0

# Enable all warnings
CFLAGS += -Wall -Wextra -Wpedantic

# Enable debug logging
CFLAGS += -DNO_OS_LOG_LEVEL=NO_OS_LOG_DEBUG

# Enable timestamps (optional)
CFLAGS += -DPRINT_TIME
```

---

## Essential Headers

```c
#include "no_os_print_log.h"  // Logging macros
#include "no_os_error.h"      // Error codes
#include "no_os_uart.h"       // UART console
#include "no_os_delay.h"      // Delays (for timing debug)
#include "no_os_util.h"       // Utilities
```

---

## Debugging Workflow

### 1. Setup Debug Environment

- [ ] UART console configured and tested
- [ ] Log level set to DEBUG
- [ ] Debug symbols enabled (`-g3 -O0`)
- [ ] Error checking after every function call

### 2. Reproduce and Isolate Issue

- [ ] Add checkpoint logging to isolate failure point
- [ ] Enable debug logging for suspected subsystem
- [ ] Verify hardware connections
- [ ] Check error codes

### 3. Investigate Root Cause

- [ ] Add detailed logging at failure point
- [ ] Use JTAG debugger to inspect variables
- [ ] Use logic analyzer for bus signals
- [ ] Compare working vs. non-working configuration

### 4. Fix and Verify

- [ ] Implement fix
- [ ] Test with debug logging enabled
- [ ] Verify fix resolves issue
- [ ] Add defensive checks to prevent recurrence

---

## Common Debugging Tools

### Software Tools
- **UART console** - printf-style debugging
- **GDB + JTAG/SWD** - breakpoint debugging, variable inspection
- **OpenOCD / JLink** - debug server for JTAG/SWD

### Hardware Tools
- **Logic analyzer** - verify SPI/I2C/UART signals
- **Oscilloscope** - check signal integrity, power supply
- **Multimeter** - verify voltage levels, continuity

**See**: `reference/tools.md` for complete hardware debugging guide.

---

## Logging Best Practices

### Standard Function Logging Pattern

```c
pr_info("Starting %s\n", __func__);

ret = operation();
if (ret) {
    pr_err("%s failed: %d\n", __func__, ret);
    return ret;
}

pr_debug("Operation result: 0x%08X\n", result);
return 0;
```

### Register Access Logging

```c
pr_debug("Reading register 0x%02X\n", reg);
ret = device_reg_read(desc, reg, &val);
pr_debug("Register 0x%02X = 0x%04X (ret=%d)\n", reg, val, ret);
```

### Configuration Verification

```c
pr_debug("SPI config: device=%u, speed=%u, mode=%u, cs=%u\n",
         spi_ip->device_id, spi_ip->max_speed_hz,
         spi_ip->mode, spi_ip->chip_select);
```

---

## Quick Reference: GDB Commands

### Basic Commands

```gdb
# Set breakpoint
break device_init

# Run to main
break main
continue

# Step through code
next          # Step over
step          # Step into
finish        # Step out

# Print variables
print ret
print *desc

# View call stack
backtrace
```

**See**: `reference/gdb-debugging.md` for complete GDB reference.

---

## Reference Documentation

**When to read each file** (use Read tool):

### reference/printf-debugging.md
Complete logging API reference: logging macros, UART setup, checkpoint patterns, timing measurements, build configuration.

### reference/gdb-debugging.md
JTAG/SWD debugging guide: debug configuration, GDB workflow, commands, register inspection, platform-specific setup.

### reference/tools.md
Hardware debugging tools: logic analyzers, oscilloscopes, multimeters, protocol analyzers, systematic hardware debug.

### reference/common-issues.md
Common debugging scenarios: ENODEV troubleshooting, SPI/I2C issues, initialization hangs, data reading problems, timing issues.

### reference/techniques.md
Advanced debugging techniques: error handling patterns, systematic approaches, performance debugging, memory debugging, regression testing.

---

## Key Takeaways

- **Setup UART first** - Essential for printf-style debugging
- **Check return values** - After every function call
- **Use pr_err() for errors** - Includes file/line/function context
- **ENODEV = hardware issue** - Check connections and configuration
- **Enable debug logging** - Set `NO_OS_LOG_LEVEL=NO_OS_LOG_DEBUG`
- **Use JTAG for crashes** - When UART output stops
- **Read reference docs** - Complete details available when needed

**Workflow**: Setup UART → Add logging → Reproduce issue → Isolate with checkpoints → Investigate with detailed logging/JTAG → Fix → Verify

**Result**: Systematic debugging approach that quickly identifies and resolves embedded system issues using appropriate tools and techniques.
