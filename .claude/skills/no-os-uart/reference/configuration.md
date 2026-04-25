# UART Configuration Reference

Complete reference for UART configuration parameters, baud rates, and serial settings.

## Core Data Structures

### 1. no_os_uart_size – Character Size Options

```c
enum no_os_uart_size {
    NO_OS_UART_CS_5,   // 5 data bits
    NO_OS_UART_CS_6,   // 6 data bits
    NO_OS_UART_CS_7,   // 7 data bits
    NO_OS_UART_CS_8,   // 8 data bits (most common)
    NO_OS_UART_CS_9,   // 9 data bits (rare, Modbus RTU)
};
```

**Typical usage:**
- **8 bits** – Standard for ASCII, JSON, binary protocols
- **7 bits** – Legacy systems with parity
- **9 bits** – Modbus RTU, address detection

### 2. no_os_uart_parity – Parity Options

```c
enum no_os_uart_parity {
    NO_OS_UART_PAR_NO,     // No parity check
    NO_OS_UART_PAR_MARK,   // Mark parity (rare)
    NO_OS_UART_PAR_SPACE,  // Space parity (rare)
    NO_OS_UART_PAR_ODD,    // Odd parity (P=1 if data has even 1s)
    NO_OS_UART_PAR_EVEN,   // Even parity (P=1 if data has odd 1s)
};
```

**Typical usage:**
- **NO_OS_UART_PAR_NO** – Default for modern systems (CRC in data protocol)
- **NO_OS_UART_PAR_EVEN** – Legacy systems, Modbus RTU
- **NO_OS_UART_PAR_ODD** – Industrial equipment

### 3. no_os_uart_stop – Stop Bits Configuration

```c
enum no_os_uart_stop {
    NO_OS_UART_STOP_1_BIT,   // 1 stop bit (standard)
    NO_OS_UART_STOP_2_BIT,   // 2 stop bits (legacy)
};
```

**Typical usage:**
- **1 stop bit** – Standard for all modern systems
- **2 stop bits** – Legacy systems, low baud rates

### 4. no_os_uart_init_param – Initialization Parameters

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

### 5. no_os_uart_desc – Runtime Descriptor

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

### 6. no_os_uart_platform_ops – Platform Function Pointers

```c
struct no_os_uart_platform_ops {
    // Initialization and cleanup
    int32_t (*init)(struct no_os_uart_desc **,
                    struct no_os_uart_init_param *);
    int32_t (*remove)(struct no_os_uart_desc *);

    // Blocking I/O
    int32_t (*read)(struct no_os_uart_desc *, uint8_t *, uint32_t);
    int32_t (*write)(struct no_os_uart_desc *, const uint8_t *, uint32_t);

    // Non-blocking I/O
    int32_t (*read_nonblocking)(struct no_os_uart_desc *,
                                uint8_t *, uint32_t);
    int32_t (*write_nonblocking)(struct no_os_uart_desc *,
                                 const uint8_t *, uint32_t);

    // Error handling
    uint32_t (*get_errors)(struct no_os_uart_desc *);
};
```

## Baud Rate Reference

| Baud Rate | Use Case | Typical |
|-----------|----------|---------|
| 300-1200 | Legacy phones | Rare |
| 9600 | Industrial/Modbus | Common |
| 19200-38400 | Serial devices | Modbus RTU |
| 115200 | Debug/high-speed | Most common |
| 250000-1000000 | Very fast logging | Oscilloscope logging |

### Common Baud Rates

**Standard rates:**
- 300, 1200, 2400, 4800, 9600
- 14400, 19200, 38400, 57600
- 115200, 230400, 460800, 921600

**High-speed rates:**
- 1000000 (1 Mbaud)
- 2000000 (2 Mbaud)
- 3000000 (3 Mbaud)

### Baud Rate Selection Guidelines

**Debugging/Logging (115200)**:
```c
.baud_rate = 115200,  // Fast enough for real-time debug
```

**Industrial protocols (9600-19200)**:
```c
.baud_rate = 9600,    // Modbus RTU standard
.baud_rate = 19200,   // High-speed Modbus
```

**GPS/NMEA (9600)**:
```c
.baud_rate = 9600,    // NMEA-0183 standard
```

**High-speed data logging (250000+)**:
```c
.baud_rate = 250000,  // For fast sensor logging
```

### Baud Rate vs Cable Length

| Baud Rate | Max Cable Length |
|-----------|------------------|
| 9600 | 300m (1000ft) |
| 19200 | 150m (500ft) |
| 38400 | 75m (250ft) |
| 115200 | 15m (50ft) |
| 230400 | 7.5m (25ft) |
| 460800 | 3.5m (12ft) |

**Note**: These are approximate values for RS-232. Actual limits depend on cable quality, EMI, and receiver sensitivity.

## Serial Format Configurations

### Standard "8N1" Configuration (Most Common)

```c
struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,        // 8 data bits
    .parity = NO_OS_UART_PAR_NO,    // No parity
    .stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};
```

### Modbus RTU "8E1" Configuration

```c
struct no_os_uart_init_param modbus_init = {
    .device_id = 1,
    .baud_rate = 9600,              // or 19200
    .size = NO_OS_UART_CS_8,        // 8 data bits
    .parity = NO_OS_UART_PAR_EVEN,  // Even parity
    .stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};
```

### Modbus RTU "9E1" (Alternative)

```c
struct no_os_uart_init_param modbus_9bit_init = {
    .device_id = 1,
    .baud_rate = 19200,
    .size = NO_OS_UART_CS_9,        // 9 data bits
    .parity = NO_OS_UART_PAR_EVEN,  // Even parity
    .stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};
```

### Legacy "7E1" Configuration

```c
struct no_os_uart_init_param legacy_init = {
    .device_id = 2,
    .baud_rate = 9600,
    .size = NO_OS_UART_CS_7,        // 7 data bits
    .parity = NO_OS_UART_PAR_EVEN,  // Even parity
    .stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};
```

### Legacy "7O2" Configuration

```c
struct no_os_uart_init_param old_system_init = {
    .device_id = 3,
    .baud_rate = 1200,
    .size = NO_OS_UART_CS_7,        // 7 data bits
    .parity = NO_OS_UART_PAR_ODD,   // Odd parity
    .stop = NO_OS_UART_STOP_2_BIT,  // 2 stop bits
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};
```

## Asynchronous RX Configuration

### Blocking RX (Simple Applications)

```c
struct no_os_uart_init_param blocking_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = false,       // Blocking mode
    .platform_ops = &max_uart_ops,
};

// Usage: blocks until data received
uint8_t buffer[64];
int bytes = no_os_uart_read(uart_desc, buffer, 64);
```

### Async RX (CLI/Interactive Applications)

```c
struct no_os_uart_init_param async_init = {
    .device_id = 0,
    .irq_id = 2,                    // IRQ for RX interrupt
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,        // Interrupt-driven RX
    .platform_ops = &max_uart_ops,
};

// Usage: returns immediately with available bytes
uint8_t buffer[64];
int bytes = no_os_uart_read_nonblocking(uart_desc, buffer, 64);
```

## Platform-Specific Configuration

### Maxim Platform Extras

```c
struct max_uart_init_param maxim_extra = {
    .flow_control = true,   // Enable RTS/CTS hardware flow control
    .dma_enabled = false,   // Use DMA for high-speed transfers
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .extra = &maxim_extra,  // Platform-specific settings
    .platform_ops = &max_uart_ops,
};
```

### STM32 Platform Extras

```c
struct stm32_uart_init_param stm32_extra = {
    .mode = UART_MODE_TX_RX,        // TX and RX mode
    .hw_flow_ctl = UART_HWCONTROL_NONE,  // No flow control
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .extra = &stm32_extra,
    .platform_ops = &stm32_uart_ops,
};
```

### Mbed Platform Extras

```c
struct mbed_uart_init_param mbed_extra = {
    .tx_pin = USBTX,        // Physical TX pin
    .rx_pin = USBRX,        // Physical RX pin
    .flow_control = false,  // No RTS/CTS
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .extra = &mbed_extra,
    .platform_ops = &mbed_uart_ops,
};
```

## Hardware Flow Control

### RTS/CTS Flow Control

```c
// Enable hardware flow control
struct max_uart_init_param flow_ctl_extra = {
    .flow_control = true,   // RTS/CTS enabled
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .extra = &flow_ctl_extra,
    .platform_ops = &max_uart_ops,
};
```

**Benefits:**
- Prevents data loss at high speeds
- Automatic TX/RX buffering management
- Essential for unreliable or slow receivers

**When to use:**
- High baud rates (>115200)
- Large data transfers
- Slow processing on receiving side
- Prevention of buffer overflow

## Configuration Verification

### Verify Baud Rate Match

```c
// Transmitter
struct no_os_uart_init_param tx_init = {
    .baud_rate = 115200,
};

// Receiver (MUST match)
struct no_os_uart_init_param rx_init = {
    .baud_rate = 115200,  // MUST be identical
};
```

### Verify Serial Format Match

```c
// Both sides MUST have identical settings
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_NO,
.stop = NO_OS_UART_STOP_1_BIT,
```

**Mismatch symptoms:**
- Garbled data
- No communication
- Framing errors
- Incorrect characters received

## Configuration Examples by Use Case

### Debug Console

```c
// Simple, fast, no error checking needed
.device_id = 0,
.baud_rate = 115200,
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_NO,
.stop = NO_OS_UART_STOP_1_BIT,
.asynchronous_rx = true,  // For interactive CLI
```

### Industrial Modbus

```c
// Reliable, error-checked, standard speed
.device_id = 1,
.baud_rate = 9600,
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_EVEN,  // Error detection
.stop = NO_OS_UART_STOP_1_BIT,
.asynchronous_rx = false,  // Polling for deterministic timing
```

### GPS Receiver

```c
// Standard NMEA-0183, async for background reception
.device_id = 2,
.baud_rate = 9600,
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_NO,
.stop = NO_OS_UART_STOP_1_BIT,
.asynchronous_rx = true,  // Background sentence buffering
```

### High-Speed Data Logger

```c
// Fast, high bandwidth, flow control recommended
.device_id = 3,
.baud_rate = 250000,
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_NO,
.stop = NO_OS_UART_STOP_1_BIT,
.asynchronous_rx = false,
.extra = &(struct max_uart_init_param){
    .flow_control = true,   // Prevent overflow
    .dma_enabled = true,    // Reduce CPU load
}
```

## Summary

**Standard configuration (8N1)**:
- 8 data bits, no parity, 1 stop bit
- Most common, used in 90% of applications
- Baud rate: 115200 for debug, 9600 for industrial

**When to use parity**:
- Industrial protocols (Modbus)
- Legacy systems
- Error-sensitive applications
- Long cable distances

**When to use async RX**:
- Command-line interfaces
- Interactive applications
- Background data reception
- When CPU should not block on reads

**When to use flow control**:
- High baud rates (>115200)
- Large data transfers
- Slow receivers
- Prevention of buffer overflow

**Always verify**:
- Baud rate matches on both TX and RX
- Data bits, parity, stop bits identical
- Platform-specific extras configured properly
