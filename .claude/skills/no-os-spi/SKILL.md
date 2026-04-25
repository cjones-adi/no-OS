---
name: no-os-spi
description: 'Complete guide to no-OS SPI (Serial Peripheral Interface) platform drivers for embedded systems. Use when implementing SPI device drivers, porting to new platforms (Maxim, STM32, Mbed), understanding platform abstraction layer, working with SPI transfers, configuring SPI modes and speeds, handling chip select, implementing DMA transfers, or debugging SPI communication issues.'
---

# no-OS SPI Platform Drivers

Quick-start guide for using the no-OS SPI platform driver abstraction layer in embedded systems.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/platform-apis.md**:
- User asks: "port to new platform", "platform-specific", "Maxim SPI", "STM32 SPI", "Mbed SPI"
- Mentions: platform extras, vendor HAL, new platform implementation
- Questions about: platform init parameters, porting steps, platform delays
- Need: Complete platform implementation examples

**Triggers to read reference/api-usage.md**:
- User asks: "how to use SPI", "read register", "write register", "burst transfer"
- Mentions: transfer patterns, message sequences, register access
- Questions about: write_and_read vs transfer, DMA async, timing diagrams
- Need: Complete usage examples, common patterns

**Triggers to read reference/configuration.md**:
- User asks: "SPI mode", "CPOL", "CPHA", "clock speed", "chip select", "data structures"
- Mentions: SPI modes 0-3, bit order, bus management, configuration
- Questions about: mode selection, clock configuration, multi-slave setup
- Need: Detailed configuration reference, timing diagrams

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "how to organize", "coding standards", "reliability"
- Questions about: error handling, thread safety, performance, code quality
- Need: Guidelines, anti-patterns, safety practices

**Triggers to read reference/troubleshooting.md**:
- User reports: errors, issues, "not working", "no data", "corruption"
- Mentions: debugging, oscilloscope, logic analyzer, wiring issues
- Questions about: specific error codes, diagnostic techniques
- Need: Problem-solving, systematic debugging

---

## When to Use This Skill

- Implementing SPI device drivers using no-OS framework
- Porting SPI drivers to new platforms (Maxim, STM32, Mbed, etc.)
- Understanding platform abstraction layer architecture
- Configuring SPI modes, speeds, and chip select
- Implementing SPI read/write operations
- Working with SPI message transfers
- Implementing DMA-based SPI transfers
- Debug SPI communication issues
- Adding platform-specific SPI features
- Handling multi-slave SPI bus configurations

## What are Platform Drivers?

Platform drivers are **hardware abstraction layers (HAL)** that wrap platform-specific APIs, providing independence from underlying hardware and software platforms.

### Purpose

Platform drivers wrap low-level platform-specific functionality:
- **SPI/I2C** initialization and read/write
- **GPIO** initialization and read/write
- **UART** initialization and receive/transmit
- **Delays** and timing
- **Interrupts** and DMA

### Benefits

- **Portability** – Device drivers work across multiple platforms
- **Abstraction** – Hide platform-specific details
- **Consistency** – Common API for all platforms
- **Maintainability** – Changes isolated to platform layer

## Architecture Overview

```
┌──────────────────────────────────────────┐
│    User Application / Device Driver     │
│  (Platform-independent code)            │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │   no_os_spi.h       │  Platform-agnostic API
    │   (Generic)         │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────────────────┐
    │                                  │
┌───▼──────────┐        ┌──────────────▼───┐
│ maxim_spi.c  │        │   mbed_spi.cpp   │
│ maxim_spi.h  │        │   mbed_spi.h     │
└───┬──────────┘        └──────────┬───────┘
    │                               │
┌───▼──────────┐        ┌──────────▼───────┐
│ Maxim HAL    │        │   Mbed HAL       │
│ (Vendor SDK) │        │   (Vendor SDK)   │
└──────────────┘        └──────────────────┘
```

## Quick Start

### 1. Define Platform-Specific Parameters

```c
// Maxim platform example
struct max_spi_init_param max_spi_extra = {
    .num_slaves = 1,
    .polarity = 0,
    .vssel = MXC_GPIO_VSSEL_VDDIO,
};

// Mbed platform example
struct mbed_spi_init_param mbed_spi_extra = {
    .spi_miso_pin = SPI_MISO,
    .spi_mosi_pin = SPI_MOSI,
    .spi_clk_pin = SPI_SCK,
    .use_sw_csb = false,
};
```

### 2. Initialize SPI

```c
struct no_os_spi_desc *spi_desc;

struct no_os_spi_init_param spi_init = {
    .device_id = 0,                  // SPI0
    .max_speed_hz = 1000000,         // 1 MHz
    .chip_select = 0,                // CS0
    .mode = NO_OS_SPI_MODE_0,
    .bit_order = NO_OS_SPI_BIT_ORDER_MSB_FIRST,
    .platform_ops = &max_spi_ops,    // Platform-specific
    .extra = &max_spi_extra,         // Platform-specific
};

ret = no_os_spi_init(&spi_desc, &spi_init);
if (ret)
    return ret;
```

### 3. Use SPI

```c
// Simple transfer (same buffer for TX/RX)
uint8_t data[3] = {0x01, 0x02, 0x03};
ret = no_os_spi_write_and_read(spi_desc, data, 3);

// Message-based transfer (separate TX/RX)
uint8_t tx_cmd[1] = {0x03};
uint8_t rx_data[4];

struct no_os_spi_msg msgs[] = {
    {
        .tx_buff = tx_cmd,
        .rx_buff = NULL,
        .bytes_number = 1,
        .cs_change = 0,  // Keep CS asserted
    },
    {
        .tx_buff = NULL,
        .rx_buff = rx_data,
        .bytes_number = 4,
        .cs_change = 1,  // Deassert CS
    },
};

ret = no_os_spi_transfer(spi_desc, msgs, 2);
```

### 4. Cleanup

```c
ret = no_os_spi_remove(spi_desc);
```

## Core Data Structures (Quick Reference)

### no_os_spi_init_param - Initialization

```c
struct no_os_spi_init_param {
    uint32_t device_id;              // SPI bus number (0, 1, 2...)
    uint32_t max_speed_hz;           // Maximum SPI clock speed
    uint8_t chip_select;             // CS pin number
    enum no_os_spi_mode mode;        // SPI mode (0-3)
    enum no_os_spi_bit_order bit_order; // MSB/LSB first
    const struct no_os_spi_platform_ops *platform_ops;
    void *extra;                     // Platform-specific params
};
```

### no_os_spi_mode - Clock Configuration

```c
enum no_os_spi_mode {
    NO_OS_SPI_MODE_0 = (0 | 0),      // CPOL=0, CPHA=0 (most common)
    NO_OS_SPI_MODE_1,                // CPOL=0, CPHA=1
    NO_OS_SPI_MODE_2,                // CPOL=1, CPHA=0
    NO_OS_SPI_MODE_3,                // CPOL=1, CPHA=1 (common)
};
```

**SPI Mode Selection:**

| Mode | CPOL | CPHA | Clock Idle | Sample Edge |
|------|------|------|------------|-------------|
| 0 | 0 | 0 | Low | Rising |
| 1 | 0 | 1 | Low | Falling |
| 2 | 1 | 0 | High | Falling |
| 3 | 1 | 1 | High | Rising |

**How to choose:** Check device datasheet for required mode. Mode 0 is most common, Mode 3 is second most common.

### no_os_spi_msg - Transfer Message

```c
struct no_os_spi_msg {
    uint8_t *tx_buff;           // Transmit buffer (NULL = send 0x00)
    uint8_t *rx_buff;           // Receive buffer (NULL = discard)
    uint32_t bytes_number;      // Transfer length
    uint8_t cs_change;          // 1 = deassert CS after transfer
    uint32_t cs_change_delay;   // Delay (us) before next CS assert
    uint32_t cs_delay_first;    // Delay (ns) after CS assert
    uint32_t cs_delay_last;     // Delay (ns) before CS deassert
};
```

## SPI Transfer Functions

### no_os_spi_write_and_read() - Simple Transfer

**Use case:** Basic full-duplex transfer (same buffer for TX/RX)

```c
int32_t no_os_spi_write_and_read(struct no_os_spi_desc *desc,
                                 uint8_t *data,
                                 uint16_t bytes_number);
```

**Example:**
```c
uint8_t cmd[2] = {0x80, 0x00};  // Read command + dummy byte
ret = no_os_spi_write_and_read(spi_desc, cmd, 2);
// cmd[1] now contains register value
```

### no_os_spi_transfer() - Multiple Messages

**Use case:** Complex multi-transfer sequences with separate TX/RX buffers

```c
int32_t no_os_spi_transfer(struct no_os_spi_desc *desc,
                           struct no_os_spi_msg *msgs,
                           uint32_t len);
```

**Example:**
```c
struct no_os_spi_msg msgs[] = {
    { .tx_buff = cmd, .rx_buff = NULL, .bytes_number = 1, .cs_change = 0 },
    { .tx_buff = NULL, .rx_buff = data, .bytes_number = 4, .cs_change = 1 },
};
ret = no_os_spi_transfer(spi_desc, msgs, 2);
```

### no_os_spi_transfer_dma() - DMA Transfer (Blocking)

**Use case:** High-speed transfers with DMA, wait for completion

```c
int32_t no_os_spi_transfer_dma(struct no_os_spi_desc *desc,
                               struct no_os_spi_msg *msgs,
                               uint32_t len);
```

**When to use:** Transfers > 64 bytes (platform-dependent)

### no_os_spi_transfer_dma_async() - DMA Transfer (Non-blocking)

**Use case:** Start DMA transfer, return immediately, callback when done

```c
int32_t no_os_spi_transfer_dma_async(struct no_os_spi_desc *desc,
                                     struct no_os_spi_msg *msgs,
                                     uint32_t len,
                                     void (*callback)(void *),
                                     void *ctx);
```

## Common Patterns

### Pattern 1: Register Read/Write

```c
// Write register
int32_t spi_write_reg(struct no_os_spi_desc *spi, uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg & 0x7F, val};
    return no_os_spi_write_and_read(spi, data, 2);
}

// Read register
int32_t spi_read_reg(struct no_os_spi_desc *spi, uint8_t reg, uint8_t *val)
{
    uint8_t data[2] = {reg | 0x80, 0x00};
    int ret = no_os_spi_write_and_read(spi, data, 2);
    if (!ret)
        *val = data[1];
    return ret;
}
```

### Pattern 2: Burst Read

```c
int32_t spi_read_burst(struct no_os_spi_desc *spi, uint8_t reg,
                       uint8_t *data, uint16_t len)
{
    struct no_os_spi_msg msgs[] = {
        { .tx_buff = &reg, .rx_buff = NULL, .bytes_number = 1, .cs_change = 0 },
        { .tx_buff = NULL, .rx_buff = data, .bytes_number = len, .cs_change = 1 },
    };
    return no_os_spi_transfer(spi, msgs, 2);
}
```

### Pattern 3: Multi-Slave Bus

```c
struct no_os_spi_init_param spi_init_template = {
    .device_id = 0,              // Same bus
    .max_speed_hz = 1000000,
    .mode = NO_OS_SPI_MODE_0,
    .platform_ops = &max_spi_ops,
    .extra = &max_extra,
};

// Initialize multiple slaves on same bus
spi_init_template.chip_select = 0;
no_os_spi_init(&spi_adc, &spi_init_template);

spi_init_template.chip_select = 1;
no_os_spi_init(&spi_dac, &spi_init_template);

// Automatic bus locking ensures no conflicts
no_os_spi_write_and_read(spi_adc, adc_data, 2);
no_os_spi_write_and_read(spi_dac, dac_data, 2);
```

## SPI Bus Management

The no-OS SPI framework supports **multi-slave configurations** with automatic bus sharing:

```c
// SPI Bus 0
// ├── Slave 0 (CS0) - ADC
// ├── Slave 1 (CS1) - DAC
// └── Slave 2 (CS2) - EEPROM
```

**Automatic behavior:**
1. First `no_os_spi_init()` on a bus creates shared bus descriptor
2. Bus mutex allocated for thread safety
3. Subsequent devices on same bus share the bus
4. Each transfer automatically locks/unlocks bus mutex
5. Bus freed when last device removed

**Key rule:** All devices on same physical SPI bus must use same `device_id`.

## Quick Reference

### Functions

| Function | Purpose |
|----------|---------|
| `no_os_spi_init()` | Initialize SPI device |
| `no_os_spi_remove()` | Free SPI resources |
| `no_os_spi_write_and_read()` | Simple full-duplex transfer |
| `no_os_spi_transfer()` | Multi-message transfer |
| `no_os_spi_transfer_dma()` | DMA transfer (blocking) |
| `no_os_spi_transfer_dma_async()` | DMA transfer (non-blocking) |

### Configuration Tips

**Clock speed:**
- Development/Debug: 100 kHz - 1 MHz
- Production: Match device maximum (verify with scope)
- Start slow, increase after validation

**SPI mode:**
- Mode 0 (CPOL=0, CPHA=0) - Most common, default for many devices
- Mode 3 (CPOL=1, CPHA=1) - Second most common
- Always check device datasheet

**Chip select:**
- Most devices use active-low CS
- Use software CS for fine timing control
- Ensure correct `chip_select` pin number

### Common Error Codes

| Error Code | Meaning | Typical Cause |
|------------|---------|---------------|
| 0 | Success | Operation completed |
| -EINVAL | Invalid argument | NULL pointer, invalid parameter |
| -ENOMEM | Out of memory | malloc() failed |
| -ENODEV | No device | Device not found, wrong bus |
| -EIO | I/O error | Transfer failed, timeout |

### Troubleshooting Quick Checks

When SPI isn't working, check in this order:

1. Power supply voltage correct
2. Wiring connections (MOSI, MISO, SCLK, CS)
3. SPI mode matches datasheet
4. Clock speed within device limits (try 100 kHz first)
5. CS polarity correct (usually active-low)
6. Device initialized and out of reset
7. Platform-specific extras configured
8. Try reading chip ID as first test

**See reference/troubleshooting.md for detailed debugging guide.**

## Best Practices

1. **Always check return values** from SPI functions
2. **Verify SPI mode** matches device datasheet requirements
3. **Set appropriate clock speed** - start slow (100 kHz) for debugging
4. **Use DMA for large transfers** (>64 bytes typically)
5. **Free resources** with `no_os_spi_remove()` when done
6. **Test with oscilloscope/logic analyzer** when debugging
7. **Document platform extras** for your specific hardware

**See reference/best-practices.md for complete guidelines.**

## Reference Documentation

**When to read each file** (use Read tool):

### reference/platform-apis.md
Platform-specific implementations, porting guide, Maxim/STM32/Mbed examples, platform delays.

### reference/api-usage.md
Complete API usage examples, transfer patterns, register access, burst operations, DMA examples.

### reference/configuration.md
Detailed configuration reference, SPI modes, data structures, timing diagrams, bus management.

### reference/best-practices.md
Coding guidelines, error handling, performance optimization, thread safety, debugging techniques.

### reference/troubleshooting.md
Common issues and solutions, debugging tools, diagnostic checklists, logic analyzer usage.

## Official Documentation

For authoritative and up-to-date information about the no-OS SPI platform driver, refer to these official resources:

### Primary SPI Documentation
- **no-OS SPI Driver Documentation**: https://wiki.analog.com/resources/no-os/drivers/spi
  - Complete SPI driver API reference
  - Platform-specific implementation details
  - Configuration examples and usage patterns
  - Troubleshooting and debugging guidance

### Related Documentation
- **no-OS Build Guide**: https://wiki.analog.com/resources/no-os/build
  - How to build projects using SPI drivers
  - Platform-specific build configurations

- **no-OS Driver Development Guide**: https://wiki.analog.com/resources/no-os/drivers-guide
  - General driver architecture and patterns
  - Best practices for driver implementation

- **no-OS GitHub Repository**: https://github.com/analogdevicesinc/no-OS
  - Source code for SPI platform implementations
  - Example drivers using SPI
  - Platform-specific SPI code (`drivers/platform/[platform]/[platform]_spi.c`)

**When to consult**: Use the official SPI driver documentation as the authoritative reference for API specifications, platform support, and implementation details. This skill provides conceptual understanding and patterns; official docs provide precise specifications.

## Summary

The no-OS SPI platform driver provides:
- **Platform abstraction** for portable device drivers
- **Multi-slave bus management** with automatic locking
- **Flexible transfer modes** (simple, message-based, DMA)
- **Easy porting** to new platforms via platform ops
- **Thread safety** with bus-level mutex
- **Extensibility** via platform-specific extras

**Key workflow:**
1. Define platform-specific extras
2. Initialize SPI with `no_os_spi_init()`
3. Use transfer functions (`write_and_read`, `transfer`, `transfer_dma`)
4. Cleanup with `no_os_spi_remove()`

**Architecture:** Generic API in `no_os_spi.h` works across all platforms. Platform-specific code in `[platform]_spi.c` wraps vendor HAL. Automatic bus management for multi-slave configurations.

This enables efficient SPI communication across diverse hardware platforms while maintaining code portability and consistency.
