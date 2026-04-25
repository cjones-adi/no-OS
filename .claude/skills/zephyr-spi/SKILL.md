---
name: zephyr-spi
description: 'Complete guide to Zephyr SPI controller drivers for serial peripheral interface. Use when implementing SPI controller drivers, configuring clock modes (CPOL/CPHA), working with chip select control, performing full-duplex transfers, implementing scatter-gather I/O, or debugging SPI communication issues.'
---

# Zephyr SPI Controller Driver Development

This skill provides comprehensive understanding of the Zephyr SPI (Serial Peripheral Interface) controller driver subsystem.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement SPI driver", "step by step", "spi_configure", "spi_transceive"
- Questions about: driver API, register access, clock configuration, CS control
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-9) with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "spi-controller", "DTS", "overlay"
- Questions about: DT properties, #address-cells, #size-cells, cs-gpios
- User asks: "how to define SPI binding", "devicetree example"
- Need: binding patterns (base + device-specific examples)

**Triggers to read reference/api-usage.md**:
- User asks: "how to use SPI", "spi_transceive", "spi_write", "spi_read"
- Questions about: basic transfers, scatter-gather, async operations
- Need: application-side SPI usage examples (6 patterns)

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "validation", "clock mode", "CS management"
- Questions about: transceive vs write/read, error handling, scatter-gather
- Need: design patterns (6 detailed patterns)

**Triggers to read reference/debugging.md**:
- User says: "not working", "wrong data", "debugging", "SPI issue"
- Build/runtime errors with SPI
- Questions about: bus communication, clock polarity, CS timing
- Need: debugging steps (6 detailed tips)

---

## When to Use This Skill

Use this skill when you need to:
- Implement SPI controller drivers for Zephyr
- Configure SPI clock modes (CPOL/CPHA)
- Handle chip select (CS) control (hardware or GPIO)
- Perform full-duplex SPI transfers
- Implement scatter-gather I/O for efficient DMA transfers
- Support synchronous or asynchronous SPI operations
- Configure SPI word size, bit order, and frame format
- Debug SPI communication issues
- Create devicetree bindings for SPI controllers
- Write SPI sample applications

## What is SPI?

**Serial Peripheral Interface (SPI)** is a synchronous serial communication protocol commonly used for short-distance communication in embedded systems.

### Key Concepts

- **4-Wire Interface**: SCLK (clock), MOSI (master out), MISO (master in), CS (chip select)
- **Full-Duplex**: Simultaneous bidirectional data transfer
- **Master/Slave**: Controller initiates all transfers
- **Clock Modes**: CPOL (polarity) and CPHA (phase) define clock edges for data sampling
- **Chip Select**: Dedicated line per device, active low by default
- **Word Size**: 4-32 bits per word (8 bits most common)

### SPI Clock Modes

| Mode | CPOL | CPHA | Clock Polarity | Sample Edge |
|------|------|------|----------------|-------------|
| 0    | 0    | 0    | Idle low       | Rising edge |
| 1    | 0    | 1    | Idle low       | Falling edge|
| 2    | 1    | 0    | Idle high      | Falling edge|
| 3    | 1    | 1    | Idle high      | Rising edge |

### Benefits

- **High Speed** – Up to several MHz clock rates
- **Full-Duplex** – Simultaneous read and write
- **Simple Protocol** – No addressing, no ACK/NAK
- **Multi-Device** – Dedicated CS line per peripheral
- **Flexible** – Configurable clock, word size, bit order

## Architecture Overview

```
Application
    ↓ (spi_transceive, spi_write, spi_read)
Zephyr SPI API (include/zephyr/drivers/spi.h)
    ↓ (spi_driver_api callbacks)
SPI Controller Driver
    ↓ (Platform-specific register access)
Hardware SPI Controller
    ↓ (SCLK, MOSI, MISO, CS pins)
SPI Peripheral Devices
```

### SPI Data Flow

```
1. Configuration
   └─ spi_configure() → Driver configures:
      ├─ Clock frequency and mode (CPOL/CPHA)
      ├─ Word size (4-32 bits)
      ├─ Bit order (MSB/LSB first)
      └─ CS control (hardware or GPIO)

2. Transfer
   ├─ spi_transceive() → Full-duplex (simultaneous TX/RX)
   ├─ spi_write() → TX only (RX ignored)
   └─ spi_read() → RX only (TX zeros/dummy)

3. Scatter-Gather (Optional)
   └─ Multiple spi_buf in spi_buf_set for efficient DMA
```

## File Structure (Quick Reference)

- **Driver**: `drivers/spi/spi_<chip>.c`
- **Binding**: `dts/bindings/spi/<vendor>,<chip>.yaml`
- **Kconfig**: Update `drivers/spi/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **spi_dt_spec** | Devicetree SPI spec | `bus` (device), `config` (word size, operation) |
| **spi_config** | SPI configuration | `frequency`, `operation` (mode, word size, bit order) |
| **spi_buf** | Transfer buffer | `buf`, `len` |
| **spi_buf_set** | Buffer set (scatter-gather) | `buffers`, `count` |
| **spi_driver_api** | Driver API table | `transceive()`, `release()` |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## SPI Operation Flags (Quick Reference)

```c
// Word size (bits per word)
#define SPI_WORD_SIZE_SHIFT 0
#define SPI_WORD_SIZE_MASK  0x3F
#define SPI_WORD_SET(x)     (((x) - 1) << SPI_WORD_SIZE_SHIFT)

// Clock mode
#define SPI_MODE_CPOL       BIT(1)  // Clock polarity (idle high)
#define SPI_MODE_CPHA       BIT(2)  // Clock phase (sample on trailing edge)
#define SPI_MODE_LOOP       BIT(3)  // Loopback mode

// Bit order
#define SPI_TRANSFER_LSB    BIT(4)  // LSB first (default: MSB first)

// Lines (standard, dual, quad)
#define SPI_LINES_SINGLE    (0 << 11)
#define SPI_LINES_DUAL      (1 << 11)
#define SPI_LINES_QUAD      (2 << 11)

// CS control
#define SPI_CS_ACTIVE_HIGH  BIT(14)
#define SPI_LOCK_ON         BIT(15)  // Keep CS asserted between transfers
#define SPI_HOLD_ON_CS      BIT(16)  // CS controlled by driver
```

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Config and Data Structures** with platform-specific data
3. **Implement Register Access Helpers** (read/write/modify)
4. **Implement spi_configure API** – Set clock mode, frequency, word size
5. **Implement spi_transceive API** – Full-duplex transfer
6. **Implement spi_release API** (Optional) – Release CS lock
7. **Implement Init Function** – Initialize hardware, set defaults
8. **Define API Structure** with function pointers
9. **Device Instantiation Macro** – Register driver

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### SPI Configuration

```c
struct spi_config spi_cfg = {
    .frequency = 1000000,  // 1 MHz
    .operation = SPI_WORD_SET(8) |      // 8-bit words
                 SPI_MODE_CPOL |         // CPOL=1
                 SPI_MODE_CPHA |         // CPHA=1 (Mode 3)
                 SPI_TRANSFER_MSB,       // MSB first
    .slave = 0,  // CS line index
};
spi_configure(spi_dev, &spi_cfg);
```

### Full-Duplex Transfer

```c
uint8_t tx_buf[] = {0x01, 0x02, 0x03};
uint8_t rx_buf[3];

struct spi_buf tx = { .buf = tx_buf, .len = sizeof(tx_buf) };
struct spi_buf rx = { .buf = rx_buf, .len = sizeof(rx_buf) };
struct spi_buf_set tx_set = { .buffers = &tx, .count = 1 };
struct spi_buf_set rx_set = { .buffers = &rx, .count = 1 };

spi_transceive(spi_dev, &spi_cfg, &tx_set, &rx_set);
```

### Write-Only Transfer

```c
uint8_t data[] = {0xAA, 0xBB, 0xCC};
struct spi_buf tx = { .buf = data, .len = sizeof(data) };
struct spi_buf_set tx_set = { .buffers = &tx, .count = 1 };

spi_write(spi_dev, &spi_cfg, &tx_set);
```

### Using Devicetree Spec

```c
// Devicetree:
// my_sensor: my-sensor@0 {
//     compatible = "vendor,sensor";
//     reg = <0>;  // CS line
//     spi-max-frequency = <1000000>;
// };

static const struct spi_dt_spec spi_spec = SPI_DT_SPEC_GET(
    DT_NODELABEL(my_sensor), SPI_WORD_SET(8) | SPI_TRANSFER_MSB, 0);

// Use directly
spi_write_dt(&spi_spec, &tx_set);
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Use `spi_transceive()` for full-duplex transfers
- Validate device ready state before use
- Check return values from all SPI operations
- Use scatter-gather (multiple buffers) for efficient DMA
- Configure CS as GPIO if hardware CS has limitations
- Document clock mode requirements for peripherals
- Use `spi_dt_spec` for devicetree-defined devices
- Set appropriate SPI frequency for device limits

❌ **DON'T**:
- Don't assume CS is automatically controlled
- Don't ignore clock mode mismatches (CPOL/CPHA)
- Don't exceed maximum SPI frequency for peripheral
- Don't modify buffers during active transfer
- Don't forget to release CS lock if using `SPI_LOCK_ON`
- Don't assume word size support beyond 8/16 bits

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **SPI API**: `zephyr/include/zephyr/drivers/spi.h`
- **SPI Drivers**: `zephyr/drivers/spi/`
- **Bindings**: `zephyr/dts/bindings/spi/`

**Example Drivers**:
- **MAX32 SPI**: `drivers/spi/spi_max32.c`
- **nRF SPIM**: `drivers/spi/spi_nrfx_spim.c`
- **STM32 SPI**: `drivers/spi/spi_ll_stm32.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-9)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Binding patterns and examples
- [reference/api-usage.md](reference/api-usage.md) – Application usage (6 patterns)
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (6 detailed)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (6 tips)

## Summary Checklist

### Driver Implementation
- [ ] Register map defined with bit masks
- [ ] Config structure with platform-specific data
- [ ] Data structure with runtime state
- [ ] Register access helpers (read/write/modify)
- [ ] `transceive()` implemented (full-duplex)
- [ ] `release()` implemented (if CS locking supported)
- [ ] API structure defined with function pointers
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created (include spi-controller.yaml)
- [ ] #address-cells and #size-cells defined
- [ ] cs-gpios property (if GPIO CS support)
- [ ] Kconfig entry with dependencies
- [ ] Board DTS defines SPI controller

### Testing
- [ ] Configuration works (clock mode, frequency, word size)
- [ ] Full-duplex transfer works (transceive)
- [ ] Write-only works
- [ ] Read-only works
- [ ] Multiple devices on same bus work
- [ ] CS control works (hardware and/or GPIO)
- [ ] Scatter-gather transfers work (if supported)
