---
name: no-os-uart
description: 'Guide to no-OS UART platform drivers for serial communication. Provides quick-start workflow, references detailed documentation for platform porting, configuration, and troubleshooting.'
---

# no-OS UART Platform Drivers

Quick-start guide for using UART serial communication in no-OS embedded systems with platform abstraction.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/platform-apis.md**:
- User asks: "port UART", "new platform", "implement UART driver"
- Mentions: platform implementation, vendor HAL, hardware abstraction
- Questions about: init/remove/read/write functions, interrupt handlers
- Creating: new platform UART driver

**Triggers to read reference/api-usage.md**:
- User asks: "how to use UART", "UART examples", "send data", "receive data"
- Mentions: CLI, command line, data logging, Modbus, GPS, NMEA
- Questions about: blocking vs non-blocking, printf redirection, buffer management
- Need: complete usage patterns, multi-UART examples

**Triggers to read reference/configuration.md**:
- User asks: "baud rate", "parity", "stop bits", "serial format"
- Mentions: 8N1, flow control, data bits, async RX
- Questions about: configuration options, platform extras, hardware settings
- Need: detailed parameter reference, configuration examples

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "how to organize", "UART patterns"
- Questions about: error handling, resource management, optimization
- Need: quality guidelines, common patterns, anti-patterns to avoid

**Triggers to read reference/troubleshooting.md**:
- User says: "not working", "no data", "garbled", "error"
- Communication issues in user output
- Questions about: debugging, diagnosis, error codes
- Specific issues: baud rate mismatch, cable problems, interrupts not firing

---

## When to Use This Skill

- Implementing UART communication in device drivers
- Porting UART drivers to new platforms (Maxim, STM32, Mbed)
- Configuring serial communication (baud rate, parity, stop bits)
- Sending and receiving data (blocking and non-blocking)
- Setting up interrupt-driven asynchronous reception
- Redirecting standard I/O (printf/scanf) to UART
- Debugging serial communication issues
- Creating command-line interfaces or debug outputs

## What is UART?

**UART (Universal Asynchronous Receiver-Transmitter)** provides serial communication:

- **Asynchronous** – No clock signal required
- **Two-wire interface** – TX (transmit) and RX (receive)
- **Configurable** – Baud rate, data bits, parity, stop bits
- **Full-duplex** – Can transmit and receive simultaneously
- **Widely supported** – Available on virtually all microcontrollers
- **Essential** – Used for debugging, logging, and user interfaces

## Architecture Overview

```
┌──────────────────────────────────────────┐
│    User Application / Device Driver     │
│  (Platform-independent code)            │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │  no_os_uart.h       │  Platform-agnostic API
    │  (Generic)          │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────────────────┐
    │                                  │
┌───▼──────────┐        ┌──────────────▼───┐
│maxim_uart.c  │        │   mbed_uart.cpp  │
│maxim_uart.h  │        │   mbed_uart.h    │
└───┬──────────┘        └──────────┬───────┘
    │ (With optional IRQ)          │
    │ (Optional DMA)               │
    │                              │
┌───▼──────────┐        ┌──────────▼───────┐
│ Maxim HAL    │        │   Mbed HAL       │
│ (Vendor SDK) │        │   (Vendor SDK)   │
└──────────────┘        └──────────────────┘
```

## Quick Start Guide

### 1. Initialize UART (Blocking Mode)

```c
#include "no_os_uart.h"
#include "maxim_uart.h"  // Platform-specific

struct no_os_uart_desc *uart_desc;

struct no_os_uart_init_param uart_init = {
    .device_id = 0,              // UART 0
    .baud_rate = 115200,         // 115.2k baud
    .size = NO_OS_UART_CS_8,     // 8 data bits
    .parity = NO_OS_UART_PAR_NO, // No parity
    .stop = NO_OS_UART_STOP_1_BIT, // 1 stop bit
    .asynchronous_rx = false,    // Blocking mode
    .platform_ops = &max_uart_ops,
};

// Initialize UART
int ret = no_os_uart_init(&uart_desc, &uart_init);
if (ret) {
    printf("UART init failed\n");
    return ret;
}

// Use UART...

// Cleanup
no_os_uart_remove(uart_desc);
```

### 2. Send Data (Blocking)

```c
const char *message = "Hello, World!\n";
int ret = no_os_uart_write(uart_desc, (uint8_t *)message,
                           strlen(message));
if (ret < 0)
    printf("Write failed: %d\n", ret);
```

### 3. Receive Data (Blocking)

```c
uint8_t buffer[128];
int bytes = no_os_uart_read(uart_desc, buffer, 128);
if (bytes > 0)
    printf("Received %d bytes\n", bytes);
```

### 4. Redirect printf to UART

```c
no_os_uart_stdio(uart_desc);  // After this, printf works

printf("This goes to UART!\n");
printf("Temperature: %d°C\n", temp_value);
```

### 5. Async RX for CLI (Non-Blocking)

```c
struct no_os_uart_init_param async_init = {
    .device_id = 0,
    .irq_id = 2,                 // IRQ for RX interrupt
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,     // Enable interrupt-driven RX
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&uart_desc, &async_init);

// Main loop - non-blocking reads
while (1) {
    uint8_t buffer[64];
    int bytes = no_os_uart_read_nonblocking(uart_desc, buffer, 64);
    
    if (bytes > 0) {
        // Process received data
        process_data(buffer, bytes);
    }
    
    // Do other work...
}
```

## Core Data Structures

### no_os_uart_init_param

```c
struct no_os_uart_init_param {
    uint8_t device_id;              // UART Device ID (0, 1, 2, etc.)
    uint32_t irq_id;                // Interrupt ID (if using async RX)
    bool asynchronous_rx;           // Enable interrupt-driven reception
    uint32_t baud_rate;             // Baud rate (9600, 115200, etc.)
    enum no_os_uart_size size;      // Data bits (5-9)
    enum no_os_uart_parity parity;  // Parity check
    enum no_os_uart_stop stop;      // Stop bits (1 or 2)
    const struct no_os_uart_platform_ops *platform_ops;
    void *extra;                    // Platform-specific parameters
};
```

### no_os_uart_desc

```c
struct no_os_uart_desc {
    void *mutex;                    // Thread safety lock
    uint8_t device_id;              // UART Device ID
    uint32_t irq_id;                // Interrupt ID
    struct lf256fifo *rx_fifo;      // Software RX buffer (async mode)
    uint32_t baud_rate;             // Configured baud rate
    const struct no_os_uart_platform_ops *platform_ops;
    void *extra;                    // Platform-specific data
};
```

## Common Configurations

### Standard "8N1" (Most Common)

```c
.size = NO_OS_UART_CS_8,        // 8 data bits
.parity = NO_OS_UART_PAR_NO,    // No parity
.stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
```

**Use for:** Debug output, logging, most modern protocols

### Modbus RTU "8E1"

```c
.baud_rate = 9600,              // or 19200
.size = NO_OS_UART_CS_8,        // 8 data bits
.parity = NO_OS_UART_PAR_EVEN,  // Even parity
.stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
```

**Use for:** Industrial Modbus RTU protocol

### Legacy "7E1"

```c
.baud_rate = 9600,
.size = NO_OS_UART_CS_7,        // 7 data bits
.parity = NO_OS_UART_PAR_EVEN,  // Even parity
.stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
```

**Use for:** Legacy equipment, old serial protocols

## Quick Reference

### UART Functions

| Function | Purpose |
|----------|---------|
| `no_os_uart_init()` | Initialize UART device |
| `no_os_uart_remove()` | Free UART resources |
| `no_os_uart_write()` | Blocking transmit |
| `no_os_uart_read()` | Blocking receive |
| `no_os_uart_write_nonblocking()` | Non-blocking transmit |
| `no_os_uart_read_nonblocking()` | Non-blocking receive |
| `no_os_uart_get_errors()` | Get error count |
| `no_os_uart_stdio()` | Redirect printf to UART |

### Configuration Enums

**Character Size:**
```c
NO_OS_UART_CS_5    // 5 data bits
NO_OS_UART_CS_6    // 6 data bits
NO_OS_UART_CS_7    // 7 data bits
NO_OS_UART_CS_8    // 8 data bits (most common)
NO_OS_UART_CS_9    // 9 data bits (Modbus RTU)
```

**Parity:**
```c
NO_OS_UART_PAR_NO     // No parity (most common)
NO_OS_UART_PAR_ODD    // Odd parity
NO_OS_UART_PAR_EVEN   // Even parity (Modbus RTU)
NO_OS_UART_PAR_MARK   // Mark parity (rare)
NO_OS_UART_PAR_SPACE  // Space parity (rare)
```

**Stop Bits:**
```c
NO_OS_UART_STOP_1_BIT   // 1 stop bit (standard)
NO_OS_UART_STOP_2_BIT   // 2 stop bits (legacy)
```

### Common Baud Rates

| Baud Rate | Use Case |
|-----------|----------|
| 9600 | Industrial/Modbus, GPS |
| 19200 | High-speed Modbus RTU |
| 115200 | Debug/high-speed (most common) |
| 250000 | Very fast data logging |

**Baud Rate vs Cable Length:**
- 9600: ~300m max
- 19200: ~150m max
- 115200: ~15m max
- 230400: ~7.5m max

## Blocking vs Non-Blocking I/O

### Blocking I/O (Simple)

```c
.asynchronous_rx = false,  // No interrupts needed

// Write blocks until all bytes sent
no_os_uart_write(uart_desc, data, len);

// Read blocks until bytes received (or timeout)
no_os_uart_read(uart_desc, buffer, len);
```

**Use when:** Simple applications, no other tasks, straightforward code

### Non-Blocking I/O (Advanced)

```c
.asynchronous_rx = true,   // Requires interrupt setup
.irq_id = 2,               // Specify IRQ number

// Write returns immediately (may queue less than requested)
int queued = no_os_uart_write_nonblocking(uart_desc, data, len);

// Read returns immediately (may return 0 if no data)
int available = no_os_uart_read_nonblocking(uart_desc, buffer, len);
```

**Use when:** CLI, interactive apps, multiple tasks, background data reception

## Platform-Specific Extras

### Maxim Platform

```c
#include "maxim_uart.h"

struct max_uart_init_param maxim_extra = {
    .flow_control = true,   // Enable RTS/CTS
    .dma_enabled = false,   // Use DMA for high-speed
};

struct no_os_uart_init_param uart_init = {
    // ... standard parameters ...
    .extra = &maxim_extra,
    .platform_ops = &max_uart_ops,
};
```

### STM32 Platform

```c
#include "stm32_uart.h"

struct stm32_uart_init_param stm32_extra = {
    .mode = UART_MODE_TX_RX,
    .hw_flow_ctl = UART_HWCONTROL_NONE,
};

struct no_os_uart_init_param uart_init = {
    // ... standard parameters ...
    .extra = &stm32_extra,
    .platform_ops = &stm32_uart_ops,
};
```

### Mbed Platform

```c
#include "mbed_uart.h"

struct mbed_uart_init_param mbed_extra = {
    .tx_pin = USBTX,
    .rx_pin = USBRX,
    .flow_control = false,
};

struct no_os_uart_init_param uart_init = {
    // ... standard parameters ...
    .extra = &mbed_extra,
    .platform_ops = &mbed_uart_ops,
};
```

## Common Usage Patterns

### Debug Console

```c
no_os_uart_init(&uart, &uart_init);
no_os_uart_stdio(uart);  // Redirect printf

printf("System initialized\n");
printf("Temperature: %d°C\n", temp);
```

### Command-Line Interface

```c
// Init with async RX
uart_init.asynchronous_rx = true;
uart_init.irq_id = 2;
no_os_uart_init(&uart, &uart_init);

no_os_uart_write(uart, (uint8_t *)"> ", 2);  // Prompt

while (1) {
    uint8_t char_received;
    int bytes = no_os_uart_read_nonblocking(uart, &char_received, 1);
    
    if (bytes > 0) {
        if (char_received == '\n') {
            process_command(cmd_buffer);
        } else {
            cmd_buffer[cmd_index++] = char_received;
            no_os_uart_write(uart, &char_received, 1);  // Echo
        }
    }
}
```

### Multi-UART System

```c
struct no_os_uart_desc *debug_uart;   // UART0 - Debug (115200)
struct no_os_uart_desc *modbus_uart;  // UART1 - Modbus (9600, 8E1)
struct no_os_uart_desc *gps_uart;     // UART2 - GPS (9600, async)

// Initialize each independently
no_os_uart_init(&debug_uart, &debug_init);
no_os_uart_init(&modbus_uart, &modbus_init);
no_os_uart_init(&gps_uart, &gps_init);

// Use each for different purpose
no_os_uart_write(debug_uart, (uint8_t *)"Debug\n", 6);
no_os_uart_write(modbus_uart, modbus_frame, len);
// GPS data buffered automatically in gps_uart->rx_fifo
```

## Error Handling

```c
// Check initialization
int ret = no_os_uart_init(&uart_desc, &uart_init);
if (ret) {
    printf("UART init failed: %d\n", ret);
    return ret;
}

// Check write return value
ret = no_os_uart_write(uart_desc, data, len);
if (ret < 0) {
    printf("Write error: %d\n", ret);
}

// Monitor errors
uint32_t errors = no_os_uart_get_errors(uart_desc);
if (errors > 0) {
    printf("UART errors: %u\n", errors);
    // Handle: overrun, framing, parity errors
}
```

## Troubleshooting Quick Fixes

**No data received:**
- Verify baud rate matches on both TX and RX
- Check cable: TX→RX, RX→TX, GND→GND
- Verify serial format (8N1) matches
- Enable async RX if using non-blocking reads

**Garbled data:**
- Baud rate mismatch (most common)
- Parity/data bits/stop bits mismatch
- Cable too long for baud rate
- Electrical noise - use shielded cable

**Printf not working:**
- Call `no_os_uart_stdio()` after init
- Add `\n` to printf or call `fflush(stdout)`

**RX buffer overflow:**
- Enable async RX for background buffering
- Process data more frequently
- Reduce baud rate or increase processing speed

**See**: `reference/troubleshooting.md` for complete diagnostic guide.

## Reference Documentation

**When to read each file** (use Read tool):

### reference/platform-apis.md
Complete guide to porting UART drivers to new platforms: implementing init/remove/read/write functions, interrupt handlers, baud rate configuration, platform-specific extras.

### reference/api-usage.md
Complete usage examples and patterns: CLI implementation, data logging, Modbus RTU, GPS parsing, multi-UART management, protocol conversion.

### reference/configuration.md
Detailed configuration reference: baud rates, serial formats (8N1, 8E1, etc.), async RX setup, platform-specific parameters, flow control.

### reference/best-practices.md
Best practices for UART usage: initialization, error handling, buffer management, multi-threading, optimization, common anti-patterns to avoid.

### reference/troubleshooting.md
Complete troubleshooting guide: diagnostic techniques, common issues and solutions, error codes, debugging checklist, oscilloscope verification.

---

## Official Documentation

For authoritative and up-to-date information:

- **no-OS UART Driver Documentation**: https://wiki.analog.com/resources/no-os/drivers/uart
- **no-OS Build Guide**: https://wiki.analog.com/resources/no-os/build
- **no-OS Driver Development Guide**: https://wiki.analog.com/resources/no-os/drivers-guide
- **no-OS GitHub Repository**: https://github.com/analogdevicesinc/no-OS
- **no-OS Wiki**: https://wiki.analog.com/resources/tools-software/uc-drivers/no-os

## Summary

The no-OS UART platform driver provides:
- **Simple abstraction** for serial communication across all platforms
- **Flexible configuration** – Baud rate, data bits, parity, stop bits
- **Multiple I/O modes** – Blocking, non-blocking, interrupt-driven
- **Platform portability** – Works on Maxim, STM32, Mbed, and more
- **Easy integration** – Standard printf/scanf redirection

**Key workflow:**
1. Initialize with `no_os_uart_init()` specifying device ID and serial settings
2. Use blocking I/O for simple applications (write/read)
3. Use async RX (with IRQ) for CLI and interactive applications
4. Always match baud rate and serial format on both TX and RX sides
5. Call `no_os_uart_remove()` to free resources when done

**Most common configuration:** 115200 baud, 8N1 (8 data bits, no parity, 1 stop bit)

UART is essential for debugging, logging, command-line interfaces, and communicating with external serial devices in embedded systems.
