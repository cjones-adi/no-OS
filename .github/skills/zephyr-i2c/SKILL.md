---
name: zephyr-i2c
description: 'Complete guide to Zephyr I2C controller drivers for serial communication. Use when implementing I2C controller drivers, configuring I2C speed modes (standard 100kHz to ultra-fast 5MHz), managing multi-master buses, supporting 7-bit and 10-bit addressing, implementing bus recovery, or debugging I2C communication issues.'
---

# Zephyr I2C Controller Driver Development

This skill provides comprehensive understanding of the Zephyr I2C (Inter-Integrated Circuit) controller driver subsystem.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement I2C driver", "step by step", "configure", "transfer"
- Questions about: driver API, register access, bus recovery, IRQ handlers
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-8) with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "i2c-controller", "DTS", "overlay"
- Questions about: DT properties, #address-cells, #size-cells, clock-frequency
- User asks: "how to define I2C binding", "devicetree example"
- Need: binding patterns and examples

**Triggers to read reference/api-usage.md**:
- User asks: "how to use I2C", "i2c_write", "i2c_read", "i2c_transfer"
- Questions about: basic transfers, i2c_dt_spec, register helpers, burst operations
- Need: application-side I2C usage examples (6 patterns)

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "retry on NACK", "device scanning", "10-bit addressing"
- Questions about: device ready check, multi-master, clock stretching
- Need: design patterns (6 detailed patterns)

**Triggers to read reference/debugging.md**:
- User says: "not working", "NACK", "timeout", "debugging", "I2C issue"
- Build/runtime errors with I2C
- Questions about: pull-up resistors, clock frequency, bus state, logic analyzer
- Need: debugging steps (6 detailed tips)

---

## When to Use This Skill

Use this skill when you need to:
- Implement I2C controller drivers for Zephyr
- Configure I2C bus speed (Standard 100kHz, Fast 400kHz, Fast+ 1MHz, High-Speed 3.4MHz, Ultra-Fast 5MHz)
- Support 7-bit and 10-bit I2C addressing
- Implement I2C master (controller) mode
- Implement I2C target (slave) mode
- Handle multi-master bus arbitration
- Implement bus recovery mechanisms
- Support clock stretching
- Debug I2C communication errors (NACK, timeout, arbitration loss)

## What is I2C?

**I2C (Inter-Integrated Circuit)** is a synchronous, multi-master, multi-slave serial communication bus invented by Philips (now NXP).

### Key Concepts

- **Two-Wire Interface**: SDA (data) and SCL (clock)
- **Multi-Master**: Multiple controllers can coexist on the same bus
- **Multi-Slave**: Multiple devices can share the bus (up to 128 with 7-bit addressing)
- **Bidirectional**: Half-duplex communication (one direction at a time)
- **Addressing**: 7-bit (standard) or 10-bit (extended) device addresses
- **Acknowledgment**: Each byte transfer is acknowledged by the receiver

### I2C Bus Speeds

```c
I2C_SPEED_STANDARD    100 kHz   (default, most common)
I2C_SPEED_FAST        400 kHz   (common for modern devices)
I2C_SPEED_FAST_PLUS   1 MHz     (requires special pull-ups)
I2C_SPEED_HIGH        3.4 MHz   (high-speed mode)
I2C_SPEED_ULTRA       5 MHz     (ultra-fast mode)
```

### I2C Transaction

```
START → [Address + R/W] → ACK → [Data Byte] → ACK → ... → STOP

Example Write:
S [0x48|W] A [0x01] A [0xFF] A P
  ↑        ↑  ↑      ↑  ↑      ↑ ↑
  Start    ACK Reg   ACK Value ACK Stop

Example Read:
S [0x48|W] A [0x01] A Sr [0x48|R] A [Data] A P
  ↑        ↑  ↑      ↑ ↑  ↑        ↑  ↑     ↑ ↑
  Start    ACK Reg   ACK Restart   ACK Data  ACK Stop
```

## Architecture Overview

```
Application
    ↓
I2C API (i2c.h)
    ↓
I2C Controller Driver (i2c_*.c)
    ↓
Hardware I2C Controller
    ↓
I2C Bus (SDA, SCL) ← Connected to I2C devices
```

## File Structure (Quick Reference)

- **Driver**: `drivers/i2c/i2c_<chip>.c`
- **Binding**: `dts/bindings/i2c/<vendor>,<chip>-i2c.yaml`
- **Kconfig**: Update `drivers/i2c/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **i2c_dt_spec** | Devicetree I2C spec | `bus` (device), `addr` (7-bit or 10-bit address) |
| **i2c_msg** | I2C message | `buf`, `len`, `flags` (I2C_MSG_WRITE, I2C_MSG_READ, I2C_MSG_STOP) |
| **i2c_driver_api** | Driver API table | `configure()`, `transfer()`, `target_register()`, `recover_bus()` |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Config and Data Structures** with platform-specific data
3. **Implement configure Function** – Set speed, addressing mode
4. **Implement transfer Function** – Execute I2C transfers
5. **Implement Bus Recovery** (Optional) – Reset bus on lockup
6. **Define API Structure** with function pointers
7. **Implement Init Function** – Initialize hardware, set defaults
8. **Device Instantiation Macro** – Register driver

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### I2C Configuration

```c
struct i2c_config cfg = {
    .speed = I2C_SPEED_FAST,  // 400kHz
    .addr_10_bit = false       // 7-bit addressing
};
i2c_configure(i2c_dev, &cfg);
```

### Basic Write

```c
uint8_t data[] = {0x01, 0xFF};  // Register 0x01, value 0xFF
i2c_write(i2c_dev, data, sizeof(data), 0x48);
```

### Basic Read

```c
uint8_t reg = 0x01;
uint8_t value;
i2c_write_read(i2c_dev, 0x48, &reg, sizeof(reg), &value, sizeof(value));
```

### Using i2c_dt_spec

```c
// Devicetree:
// my_sensor: sensor@48 {
//     compatible = "vendor,sensor";
//     reg = <0x48>;
// };

static const struct i2c_dt_spec sensor = I2C_DT_SPEC_GET(DT_NODELABEL(my_sensor));

// Use directly
uint8_t data[] = {0x01, 0xFF};
i2c_write_dt(&sensor, data, sizeof(data));
```

### Register Read Helper

```c
int i2c_reg_read_byte_dt(const struct i2c_dt_spec *spec,
                         uint8_t reg_addr, uint8_t *value)
{
    return i2c_write_read_dt(spec, &reg_addr, sizeof(reg_addr),
                             value, sizeof(*value));
}
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always check device ready state before use
- Retry on NACK (device might be busy)
- Use i2c_dt_spec for devicetree-defined devices
- Check for bus recovery support
- Implement proper error handling
- Support clock stretching if hardware allows
- Use 7-bit addressing unless 10-bit required
- Test with logic analyzer for signal integrity

❌ **DON'T**:
- Don't assume I2C device is always ready
- Don't ignore NACK errors
- Don't exceed bus speed limits for devices
- Don't forget pull-up resistors (typically 4.7kΩ)
- Don't use clock stretching without hardware support
- Don't mix 7-bit and 10-bit addresses without proper handling

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **I2C API**: `zephyr/include/zephyr/drivers/i2c.h`
- **I2C Drivers**: `zephyr/drivers/i2c/`
- **Bindings**: `zephyr/dts/bindings/i2c/`

**Example Drivers**:
- **MAX32 I2C**: `drivers/i2c/i2c_max32.c`
- **nRF TWIM**: `drivers/i2c/i2c_nrfx_twim.c`
- **STM32 I2C**: `drivers/i2c/i2c_ll_stm32.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-8)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Binding patterns and examples
- [reference/api-usage.md](reference/api-usage.md) – Application usage (6 patterns)
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (6 detailed)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (6 tips)

## Summary Checklist

### Driver Implementation
- [ ] Register map defined with bit masks
- [ ] Config structure with platform-specific data
- [ ] Data structure with runtime state
- [ ] `configure()` implemented (set speed, addressing mode)
- [ ] `transfer()` implemented (execute I2C transfers)
- [ ] `recover_bus()` implemented (if supported)
- [ ] API structure defined with function pointers
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created (include i2c-controller.yaml)
- [ ] #address-cells and #size-cells defined
- [ ] clock-frequency property
- [ ] Pinctrl integration
- [ ] Kconfig entry with dependencies
- [ ] Board DTS defines I2C controller

### Testing
- [ ] Configuration works (speed, addressing mode)
- [ ] Write works (i2c_write)
- [ ] Read works (i2c_read)
- [ ] Write-read works (i2c_write_read)
- [ ] Multiple devices on same bus work
- [ ] NACK handling works
- [ ] Bus recovery works (if implemented)
- [ ] Logic analyzer shows correct signals
