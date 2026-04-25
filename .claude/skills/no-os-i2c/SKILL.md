---
name: no-os-i2c
description: 'Guide to no-OS I2C (Inter-Integrated Circuit) platform drivers for embedded systems. Provides quick-start workflow, references detailed documentation for platform implementations, usage patterns, configuration, best practices, and troubleshooting.'
---

# no-OS I2C Platform Drivers

Quick-start guide for using and porting no-OS I2C platform drivers for embedded systems.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/platform-apis.md**:
- User asks: "how to port I2C", "new platform", "implement platform"
- Mentions: vendor HAL, platform-specific, Maxim, STM32, Mbed
- Questions about: platform operations, porting guide, platform extras
- Need: complete platform implementation examples and porting steps

**Triggers to read reference/api-usage.md**:
- User asks: "how to read", "how to write", "I2C transaction", "communication pattern"
- Mentions: register read/write, burst transfer, EEPROM, sensor
- Questions about: repeated start, stop condition, multi-byte values
- Need: complete usage examples, device-specific patterns, advanced patterns

**Triggers to read reference/configuration.md**:
- User asks: "configure I2C", "speed mode", "addressing", "data structures"
- Mentions: 100kHz, 400kHz, 1MHz, pull-up resistors, bus capacitance
- Questions about: init parameters, descriptor structure, bus management
- Need: detailed configuration options, speed selection, electrical specs

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "how should I", "recommended approach"
- Questions about: code organization, error handling, testing
- Need: quality guidelines, design patterns, common pitfalls to avoid

**Triggers to read reference/troubleshooting.md**:
- Communication errors in user output
- User says: "not working", "no ACK", "bus stuck", "data corruption"
- Specific errors: NACK, timeout, bus lockup, wrong values
- Questions about: debugging, logic analyzer, testing
- Need: systematic troubleshooting steps, error diagnosis

---

## When to Use This Skill

- Implementing I2C device drivers using no-OS framework
- Porting I2C drivers to new platforms (Maxim, STM32, Mbed, etc.)
- Configuring I2C speed, addressing, and bus parameters
- Working with I2C read/write operations and repeated start
- Debugging I2C communication issues
- Understanding I2C platform abstraction layer
- Managing multi-slave I2C bus configurations

## What is I2C?

I2C (Inter-Integrated Circuit) is a two-wire serial communication protocol:

- Two wires: SDA (data) and SCL (clock)
- Multi-master/multi-slave capable
- 7-bit or 10-bit addressing
- Built-in acknowledgment (ACK/NACK)
- Speeds: 100 kHz (standard), 400 kHz (fast), 1 MHz (fast+)

Benefits:
- Simple wiring - only two wires for multiple devices
- Built-in addressing - each device has unique address
- Widely supported - most sensors and peripherals

## Architecture Overview

```
┌──────────────────────────────────────────┐
│    User Application / Device Driver     │
│  (Platform-independent code)            │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │   no_os_i2c.h       │  Platform-agnostic API
    │   (Generic)         │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────────────────┐
    │                                  │
┌───▼──────────┐        ┌──────────────▼───┐
│ maxim_i2c.c  │        │   mbed_i2c.cpp   │
│ maxim_i2c.h  │        │   mbed_i2c.h     │
└───┬──────────┘        └──────────┬───────┘
    │                               │
┌───▼──────────┐        ┌──────────▼───────┐
│ Maxim HAL    │        │   Mbed HAL       │
│ (Vendor SDK) │        │   (Vendor SDK)   │
└──────────────┘        └──────────────────┘
```

## Quick Start Guide

### 1. Include Required Headers

```c
#include "no_os_i2c.h"
#include "maxim_i2c.h"  // Or platform-specific header
```

### 2. Configure I2C Initialization Parameters

```c
struct no_os_i2c_desc *i2c_desc;

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,                  // I2C bus number (I2C0)
    .max_speed_hz = 400000,          // 400 kHz (fast mode)
    .slave_address = 0x48,           // 7-bit slave address
    .platform_ops = &max_i2c_ops,    // Platform operations
    .extra = &max_i2c_extra,         // Platform-specific (optional)
};
```

**Speed modes:**
- `100000` Hz - Standard mode (100 kHz) - long wires, debugging
- `400000` Hz - Fast mode (400 kHz) - most common, default choice
- `1000000` Hz - Fast+ mode (1 MHz) - short wires, high speed

**Slave address:**
- Use 7-bit address (NOT 8-bit R/W format)
- Range: 0x08 to 0x77
- Example: 0x48, not 0x90

### 3. Initialize I2C Device

```c
int32_t ret;

ret = no_os_i2c_init(&i2c_desc, &i2c_init);
if (ret) {
    pr_err("I2C init failed: %d\n", ret);
    return ret;
}
```

### 4. Perform I2C Transactions

**Simple register write:**
```c
uint8_t write_data[2] = {0x10, 0x55};  // Register address + value
ret = no_os_i2c_write(i2c_desc, write_data, 2, 1);  // stop_bit = 1
```

**Simple register read (with repeated start):**
```c
uint8_t reg_addr = 0x10;
uint8_t read_data[1];

// Write register address (no stop - repeated start)
ret = no_os_i2c_write(i2c_desc, &reg_addr, 1, 0);
if (ret)
    return ret;

// Read data (with stop)
ret = no_os_i2c_read(i2c_desc, read_data, 1, 1);
```

**Burst read (multiple bytes):**
```c
uint8_t reg_addr = 0x10;
uint8_t data[4];

ret = no_os_i2c_write(i2c_desc, &reg_addr, 1, 0);  // No stop
if (ret)
    return ret;

ret = no_os_i2c_read(i2c_desc, data, 4, 1);  // Read 4 bytes, then stop
```

### 5. Cleanup

```c
ret = no_os_i2c_remove(i2c_desc);
```

## Core Data Structures (Quick Reference)

### no_os_i2c_init_param - Initialization Parameters

```c
struct no_os_i2c_init_param {
    uint32_t device_id;              // I2C bus number (0, 1, 2...)
    uint32_t max_speed_hz;           // Max I2C speed (100k, 400k, 1M)
    uint8_t slave_address;           // 7-bit slave address
    const struct no_os_i2c_platform_ops *platform_ops;
    void *extra;                     // Platform-specific params
};
```

### no_os_i2c_desc - Runtime Descriptor

```c
struct no_os_i2c_desc {
    struct no_os_i2cbus_desc *bus;   // Shared bus descriptor
    uint32_t device_id;              // I2C bus number
    uint32_t max_speed_hz;           // Max speed
    uint8_t slave_address;           // Slave address
    const struct no_os_i2c_platform_ops *platform_ops;
    void *extra;                     // Platform-specific data
};
```

## I2C Transfer Functions

### no_os_i2c_write()

```c
int32_t no_os_i2c_write(struct no_os_i2c_desc *desc,
                        uint8_t *data,
                        uint8_t bytes_number,
                        uint8_t stop_bit);
```

**Parameters:**
- `desc` - I2C descriptor
- `data` - Data to write
- `bytes_number` - Number of bytes
- `stop_bit` - 1 = send STOP, 0 = no STOP (repeated start)

### no_os_i2c_read()

```c
int32_t no_os_i2c_read(struct no_os_i2c_desc *desc,
                       uint8_t *data,
                       uint8_t bytes_number,
                       uint8_t stop_bit);
```

**Parameters:**
- `desc` - I2C descriptor
- `data` - Buffer for received data
- `bytes_number` - Number of bytes to read
- `stop_bit` - 1 = send STOP after read, 0 = no STOP

## Common Usage Patterns

### Pattern 1: Simple Register Write

```c
int32_t i2c_write_reg(struct no_os_i2c_desc *i2c, uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg, val};
    return no_os_i2c_write(i2c, data, 2, 1);
}
```

### Pattern 2: Simple Register Read

```c
int32_t i2c_read_reg(struct no_os_i2c_desc *i2c, uint8_t reg, uint8_t *val)
{
    int32_t ret;

    // Write register address with repeated start
    ret = no_os_i2c_write(i2c, &reg, 1, 0);
    if (ret)
        return ret;

    // Read register value
    return no_os_i2c_read(i2c, val, 1, 1);
}
```

### Pattern 3: Device Scan

```c
void i2c_scan_bus(struct no_os_i2c_desc *i2c)
{
    uint8_t dummy;
    struct no_os_i2c_desc temp = *i2c;
    
    pr_info("Scanning I2C bus:\n");
    
    for (uint8_t addr = 0x08; addr < 0x78; addr++) {
        temp.slave_address = addr;
        
        if (no_os_i2c_read(&temp, &dummy, 0, 1) == 0) {
            pr_info("Device found at 0x%02X\n", addr);
        }
    }
}
```

## Repeated Start vs Stop Condition

**With STOP (two separate transactions):**
```
START - ADDR(W) - REG - STOP
START - ADDR(R) - DATA - STOP
```

**With Repeated START (single atomic transaction):**
```
START - ADDR(W) - REG - RESTART - ADDR(R) - DATA - STOP
```

**Always use repeated start for read-after-write:**
```c
// GOOD - repeated start (faster, atomic, required by some devices)
no_os_i2c_write(i2c, &reg, 1, 0);  // No stop
no_os_i2c_read(i2c, data, len, 1);  // Stop after read

// LESS EFFICIENT - separate transactions
no_os_i2c_write(i2c, &reg, 1, 1);  // Stop - releases bus
no_os_i2c_read(i2c, data, len, 1);  // Stop
```

## Multi-Device Bus Sharing

Multiple devices on same bus automatically share resources:

```c
// First device creates shared bus descriptor
struct no_os_i2c_init_param temp_init = {
    .device_id = 0,          // I2C0
    .slave_address = 0x48,   // Temp sensor
    .max_speed_hz = 400000,
    .platform_ops = &max_i2c_ops,
};
no_os_i2c_init(&temp_sensor, &temp_init);

// Second device reuses bus (same device_id)
struct no_os_i2c_init_param eeprom_init = {
    .device_id = 0,          // Same I2C0
    .slave_address = 0x50,   // EEPROM
    .max_speed_hz = 400000,
    .platform_ops = &max_i2c_ops,
};
no_os_i2c_init(&eeprom, &eeprom_init);

// Transfers automatically lock bus mutex (thread-safe)
i2c_read_reg(temp_sensor, 0x00, &temp);  // Locks bus
i2c_read_reg(eeprom, 0x00, &data);       // Locks bus
```

## Best Practices (Quick Reference)

1. Always use repeated start for read-after-write when possible
2. Always check return values - I2C operations can NACK
3. Verify slave address is 7-bit format (not 8-bit R/W format)
4. Start with lower speeds (100 kHz) for debugging
5. Handle bus errors gracefully - implement retry logic
6. Use mutex for shared bus (automatic in no-OS)
7. Add pull-up resistors - 4.7kΩ (100kHz) or 2.2kΩ (400kHz)
8. Check bus capacitance - limit 400pF (standard/fast)
9. Free resources with `no_os_i2c_remove()` when done

**See**: `reference/best-practices.md` for complete guidelines.

## Troubleshooting (Quick Reference)

**No ACK received:**
- Check wiring (SDA/SCL)
- Verify 7-bit slave address
- Check pull-up resistors
- Verify device power
- Try lower speed (100 kHz)

**Data corruption:**
- Check pull-up resistor values
- Reduce I2C speed
- Check for noise
- Verify bus capacitance < 400pF

**Bus stuck (SDA/SCL low):**
- Clock stretching issue
- Send 9 clock pulses to release
- Reset I2C peripheral
- Check for shorts

**See**: `reference/troubleshooting.md` for complete troubleshooting guide.

## Quick Reference Tables

### API Functions

| Function | Purpose |
|----------|---------|
| `no_os_i2c_init()` | Initialize I2C device |
| `no_os_i2c_remove()` | Free I2C resources |
| `no_os_i2c_write()` | Write data to slave |
| `no_os_i2c_read()` | Read data from slave |

### Speed Modes

| Mode | Frequency | Use Case |
|------|-----------|----------|
| Standard | 100 kHz | Long wires, many devices, debugging |
| Fast | 400 kHz | Most common, good balance |
| Fast+ | 1 MHz | Short wires, fewer devices |

### Pull-up Resistor Values

| Speed | Typical Resistor |
|-------|-----------------|
| 100 kHz | 4.7 kΩ |
| 400 kHz | 2.2 kΩ |
| 1 MHz | 1.0 kΩ |

## Reference Documentation

**When to read each file** (use Read tool):

### reference/platform-apis.md
Complete platform implementation and porting guide. Platform-specific extras, vendor HAL integration, step-by-step porting instructions.

### reference/api-usage.md
Complete usage patterns and examples. Device-specific patterns (EEPROM, sensor, IMU), advanced transactions, error handling patterns.

### reference/configuration.md
Detailed configuration guide. Data structure details, speed mode selection, electrical configuration, bus management, platform examples.

### reference/best-practices.md
Complete best practices. Communication patterns, design guidelines, testing strategies, common pitfalls to avoid.

### reference/troubleshooting.md
Systematic troubleshooting guide. Communication failures, platform porting issues, debugging techniques, error code reference.

## Official Documentation

For authoritative and up-to-date information:

**Primary I2C Documentation:**
- no-OS I2C Driver Documentation: https://wiki.analog.com/resources/no-os/drivers/i2c
  - Complete API reference
  - Platform-specific implementations
  - Configuration and usage

**Related Documentation:**
- no-OS Build Guide: https://wiki.analog.com/resources/no-os/build
- no-OS Driver Development: https://wiki.analog.com/resources/no-os/drivers-guide
- no-OS GitHub Repository: https://github.com/analogdevicesinc/no-OS
- no-OS Wiki: https://wiki.analog.com/resources/tools-software/uc-drivers/no-os

## Summary

The no-OS I2C platform driver provides:

- Platform abstraction for portable device drivers
- Simple API with read and write functions
- Multi-slave management with automatic bus locking
- Repeated start support for efficient transfers
- Easy porting via platform ops structure
- Thread safety with bus-level mutex

**Key concepts:**
1. Generic API in `no_os_i2c.h` works across all platforms
2. Platform code wraps vendor HAL functions
3. Automatic shared bus management for multiple slaves
4. Use repeated start (`stop_bit=0`) for efficient read-after-write
5. Always check return values - I2C can NACK

**Workflow:**
Initialize → Configure → Write/Read → Cleanup

I2C is simpler than SPI (only 2 wires, built-in addressing) but requires attention to electrical characteristics (pull-ups, capacitance, speed vs distance).
