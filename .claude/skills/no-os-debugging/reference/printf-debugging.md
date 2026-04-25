# Printf Debugging Techniques

Complete guide to logging and printf-style debugging in no-OS embedded applications.

---

## Logging System

### Core Logging API (`no_os_print_log.h`)

The no-OS framework provides a syslog-compatible logging system with 8 severity levels.

**Header**: `include/no_os_print_log.h`

**Severity Levels** (from highest to lowest):
```c
NO_OS_LOG_EMERG    // 0x0 - System unusable
NO_OS_LOG_ALERT    // 0x1 - Action must be taken immediately
NO_OS_LOG_CRIT     // 0x2 - Critical conditions
NO_OS_LOG_ERR      // 0x3 - Error conditions
NO_OS_LOG_WARNING  // 0x4 - Warning conditions
NO_OS_LOG_NOTICE   // 0x5 - Normal but significant
NO_OS_LOG_INFO     // 0x6 - Informational (default)
NO_OS_LOG_DEBUG    // 0x7 - Debug-level messages
```

---

### Logging Macros

**High-Severity Macros** (include file, line, and function context):
```c
pr_emerg(msg, ...)    // Emergency: system unusable
pr_alert(msg, ...)    // Alert: immediate action required
pr_crit(msg, ...)     // Critical: critical condition
pr_err(msg, ...)      // Error: error condition
```

**Low-Severity Macros** (minimal overhead):
```c
pr_warning(msg, ...)  // Warning
pr_notice(msg, ...)   // Notice
pr_info(msg, ...)     // Info (most common)
pr_debug(msg, ...)    // Debug (only when NO_OS_LOG_LEVEL == DEBUG)
```

---

### Usage Examples

**Basic Logging**:
```c
#include "no_os_print_log.h"

int example_main(void)
{
    pr_info("Starting application...\n");

    ret = device_init(&dev, &init_params);
    if (ret) {
        pr_err("Device initialization failed: %d\n", ret);
        return ret;
    }

    pr_info("Device initialized successfully\n");

    // Application logic

    pr_debug("Register value: 0x%04X\n", reg_val);

    return 0;
}
```

**Error Context Logging** (includes file:line and function name):
```c
ret = no_os_spi_init(&spi_desc, &spi_init);
if (ret) {
    pr_err("SPI initialization failed: %d\n", ret);
    // Output: [ERROR] file.c:42 (function_name): SPI initialization failed: -22
    return ret;
}
```

---

### Configuring Log Level

**Compile-Time Configuration**:
```c
// In your code or Makefile
#define NO_OS_LOG_LEVEL NO_OS_LOG_DEBUG  // Show all messages
#define NO_OS_LOG_LEVEL NO_OS_LOG_INFO   // Default (hide debug)
#define NO_OS_LOG_LEVEL NO_OS_LOG_ERR    // Only errors and above
```

**Makefile Configuration**:
```makefile
# In src.mk or platform_src.mk
CFLAGS += -DNO_OS_LOG_LEVEL=NO_OS_LOG_DEBUG
```

**Effects**:
- Messages below configured level compile to no-ops (zero overhead)
- Debug messages (`pr_debug`) only appear when level is `NO_OS_LOG_DEBUG`
- Default level is `NO_OS_LOG_INFO`

---

### Optional Timestamp Logging

Enable timestamps to track timing issues:

```c
#define PRINT_TIME  // Before including no_os_print_log.h
#include "no_os_print_log.h"
```

**Output Format**:
```
[123.456789] Starting application...
[123.567890] Device initialized successfully
```

Uses `no_os_get_time()` to provide `[seconds.microseconds]` precision.

---

## UART Console Debugging

### Setting Up Debug Console

**Standard Pattern** (in main.c or example):
```c
#include "no_os_uart.h"
#include "no_os_print_log.h"

int example_main(void)
{
    struct no_os_uart_desc *uart_desc;
    int ret;

    // Initialize UART (parameters from common_data.h/parameters.h)
    ret = no_os_uart_init(&uart_desc, &uart_ip);
    if (ret) {
        // Can't log yet - UART failed!
        return ret;
    }

    // Redirect printf/pr_* to UART
    no_os_uart_stdio(uart_desc);

    // Now logging works
    pr_info("Debug console ready\n");

    // Rest of application

    return 0;
}
```

---

### UART Configuration

**Common Parameters** (from parameters.h):
```c
struct no_os_uart_init_param uart_ip = {
    .device_id = UART_DEVICE_ID,    // Platform-specific (e.g., 0 for UART0)
    .baud_rate = 115200,            // Standard debug baud rate
    .irq_id = UART_IRQ_ID,          // For interrupt-driven UART
    .platform_ops = UART_OPS,       // Platform driver ops
    .extra = UART_EXTRA,            // Platform-specific config
};
```

**IIO Serial Console**:
For IIO applications, use 57600 baud:
```c
.baud_rate = 57600,  // IIO standard baud rate
```

Connect with:
```bash
iio_info -u serial:/dev/ttyUSB0,57600,8n1
```

---

### Printf-Style Debugging

After `no_os_uart_stdio()`, you can use standard `printf()`:

```c
no_os_uart_stdio(uart_desc);

printf("Value: %u (0x%08X)\n", value, value);
printf("Error code: %d\n", ret);
printf("Register 0x%02X = 0x%04X\n", reg, val);
```

**Best Practice**: Use `pr_info()` instead of `printf()` for consistency:
- Allows runtime filtering by log level
- Consistent formatting
- Can be disabled at compile time

---

## Debug Logging Patterns

### Checkpoint Logging

Add checkpoints to track execution flow:

```c
pr_info("Checkpoint 1: Starting init\n");
ret = step1_init();
pr_info("Checkpoint 2: Step 1 complete\n");
ret = step2_init();
pr_info("Checkpoint 3: Step 2 complete\n");
// Find where it stops
```

### Register Access Logging

Debug register read/write sequences:

```c
int device_reg_read(struct device_desc *desc, uint16_t reg, uint16_t *data)
{
    int ret;
    
    pr_debug("Reading register 0x%04X\n", reg);
    
    ret = hardware_read(desc, reg, data);
    if (ret) {
        pr_err("Register read failed: reg=0x%04X, ret=%d\n", reg, ret);
        return ret;
    }
    
    pr_debug("Register 0x%04X = 0x%04X\n", reg, *data);
    return 0;
}
```

### SPI/I2C Transaction Logging

Debug communication bus transactions:

```c
int ad4692_spi_reg_read(struct ad4692_desc *desc, uint16_t reg, uint16_t *data)
{
    int ret;
    uint8_t buf[3];

    pr_debug("SPI read: reg=0x%04X\n", reg);

    buf[0] = (reg >> 8) & 0xFF;
    buf[1] = reg & 0xFF;
    buf[2] = 0x00;  // Dummy byte

    ret = no_os_spi_write_and_read(desc->spi_desc, buf, 3);
    if (ret) {
        pr_err("SPI transaction failed: %d\n", ret);
        return ret;
    }

    *data = (buf[1] << 8) | buf[2];
    pr_debug("SPI read result: 0x%04X\n", *data);

    return 0;
}
```

### Configuration Verification Logging

Verify configuration is correct:

```c
pr_debug("SPI config: device_id=%u, max_speed=%u, cs=%u, mode=%u\n",
         spi_ip->device_id,
         spi_ip->max_speed_hz,
         spi_ip->chip_select,
         spi_ip->mode);

pr_debug("I2C write: addr=0x%02X, reg=0x%02X, data=0x%02X\n",
         desc->i2c_desc->slave_address, reg, data);

pr_debug("UART config: baud=%u, device=%u\n",
         uart_ip->baud_rate,
         uart_ip->device_id);
```

### Memory Allocation Logging

Track memory allocations:

```c
desc = no_os_calloc(1, sizeof(*desc));
if (!desc) {
    pr_err("Memory allocation failed\n");
    return -ENOMEM;
}
pr_debug("Allocated %zu bytes at %p\n", sizeof(*desc), (void*)desc);
```

### Data Value Logging

Debug data readings and conversions:

```c
pr_debug("Reading data register 0x%02X\n", DATA_REG);
ret = device_reg_read(desc, DATA_REG, &data);
pr_debug("Raw data: 0x%08X (%u)\n", data, data);

// Bit extraction
uint32_t raw = 0x12345678;
uint16_t extracted = (raw >> 8) & 0xFFFF;
pr_debug("Extract: raw=0x%08X → extracted=0x%04X\n", raw, extracted);

// Expected vs actual
pr_info("Expected: %u, Actual: %u, Error: %d\n",
        expected, actual, (int)(actual - expected));
```

### Timing Measurements

Add timing information to debug performance:

```c
#define PRINT_TIME
#include "no_os_print_log.h"

pr_info("Starting operation\n");
ret = long_operation();
pr_info("Operation complete\n");
// Timestamps show duration
```

---

## Build-Time Debug Configuration

### Enable Debug Symbols

**In Makefile**:
```makefile
# Add debug symbols
CFLAGS += -g3 -O0

# Disable optimizations for debugging
CFLAGS += -O0
```

### Add Debug Defines

```makefile
# Enable debug logging
CFLAGS += -DNO_OS_LOG_LEVEL=NO_OS_LOG_DEBUG

# Enable timestamp logging
CFLAGS += -DPRINT_TIME

# Platform-specific debug
CFLAGS += -DDEBUG_PLATFORM
```

---

## Essential Headers

```c
#include "no_os_print_log.h"  // Logging
#include "no_os_error.h"      // Error codes
#include "no_os_uart.h"       // UART console
#include "no_os_delay.h"      // Delays
#include "no_os_util.h"       // Utilities
```

---

## Common Logging Patterns

### Standard Function Logging

```c
pr_info("Starting %s\n", __func__);

ret = operation();
if (ret) {
    pr_err("%s failed: %d\n", __func__, ret);
    return ret;
}

pr_debug("Operation successful, result: 0x%08X\n", result);
```

### UART Setup Pattern

```c
ret = no_os_uart_init(&uart, &uart_ip);
if (ret)
    return ret;

no_os_uart_stdio(uart);
pr_info("Debug console ready\n");
```
