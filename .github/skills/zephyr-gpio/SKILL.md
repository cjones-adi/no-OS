---
name: zephyr-gpio
description: 'Complete guide to Zephyr GPIO drivers for General Purpose Input/Output controllers and expanders. Use when implementing GPIO drivers, configuring pin direction/pull-resistors, reading digital inputs, writing digital outputs, handling GPIO interrupts, or working with I2C/SPI GPIO expanders.'
---

# Zephyr GPIO Driver Development

This skill provides comprehensive understanding of the Zephyr GPIO driver subsystem for General Purpose Input/Output controllers.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement GPIO driver", "step by step", "pin_configure", "port_get_raw"
- Questions about: API functions, register access, interrupt handling, port operations
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "gpio-controller", "DTS", "overlay"
- Questions about: DT properties, gpio-cells, ngpios, gpio-reserved-ranges
- User asks: "how to define binding", "devicetree example"
- Need: binding patterns and devicetree usage examples

**Triggers to read reference/api-usage.md**:
- User asks: "how to use GPIO", "consumer example", "configure pin", "read pin", "write pin"
- Questions about: gpio_dt_spec, interrupts, callbacks, port operations
- Need: application-side GPIO usage examples

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "shadow registers", "I2C expander", "locking"
- Questions about: active-low logic, initialization order, validation, non-contiguous pins
- Need: design patterns and recommendations

**Triggers to read reference/debugging.md**:
- Build/runtime errors
- User says: "not working", "interrupt not firing", "debugging", "pin not changing"
- Questions about: troubleshooting GPIO issues, checking pin state, I2C/SPI communication
- Need: debugging steps and common issues

**Triggers to read examples/complete-driver.c**:
- User asks: "complete example", "full driver code", "working implementation"
- Need: reference driver to study
- Want: complete GPIO controller driver

---

## When to Use This Skill

Use this skill when you need to:
- Implement GPIO controller drivers (SoC GPIO banks, I2C/SPI expanders)
- Configure GPIO pins (input/output, pull-up/pull-down, open-drain)
- Read digital input values from GPIO pins
- Write digital output values to GPIO pins
- Toggle output pins or set/clear multiple pins atomically
- Configure GPIO interrupts (edge/level triggered)
- Work with ADI GPIO expanders (ADP5585, MAX14906, MAX22017, MAX14916)
- Implement interrupt callbacks for GPIO events
- Create board overlays for GPIO devices
- Debug GPIO issues (pin states, interrupt configuration)

## What is GPIO?

**GPIO (General Purpose Input/Output)** is a fundamental peripheral for digital I/O control:

- **Flexible Pins** – Pins can be configured as digital inputs or outputs at runtime
- **Pull Resistors** – Support for pull-up, pull-down, or high-impedance configurations
- **Interrupt Capability** – Pins can trigger interrupts on edge or level changes
- **Port Operations** – Atomic read/write/toggle operations on multiple pins simultaneously
- **Expanders** – External GPIO chips provide additional I/O via I2C or SPI

### Common GPIO Device Types

- **SoC GPIO Controllers** – Integrated GPIO banks in microcontrollers (MAX32, STM32, nRF52)
- **I2C GPIO Expanders** – External GPIO chips on I2C bus (ADP5585, PCA9554, TCA6408A)
- **SPI GPIO Expanders** – High-speed GPIO via SPI (MAX14906, MAX14916, MAX7219x)
- **MFD GPIO** – GPIO as part of multi-function device (AD559x GPIO controller)
- **Industrial I/O** – GPIO controllers for industrial control (MAX14906 with diagnostics)

### Benefits

- **Flexibility** – Reconfigure pins at runtime for different functions
- **Efficiency** – Port operations enable atomic multi-pin changes
- **Safety** – Pull resistors ensure defined pin states
- **Responsiveness** – Interrupt-driven I/O avoids polling overhead

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Application Layer                      │
│  (Uses gpio_pin_configure, gpio_pin_set, ...)      │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│         Zephyr GPIO API (gpio.h)                    │
│  - gpio_pin_configure() / gpio_pin_configure_dt()  │
│  - gpio_pin_set() / gpio_pin_get()                 │
│  - gpio_port_set_bits_raw()                        │
│  - gpio_pin_interrupt_configure()                  │
│  - gpio_add_callback()                             │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│         GPIO Driver API Structure                   │
│         (struct gpio_driver_api)                    │
│  - pin_configure()                                  │
│  - port_get_raw()                                   │
│  - port_set_masked_raw()                            │
│  - port_set_bits_raw()                              │
│  - port_clear_bits_raw()                            │
│  - port_toggle_bits()                               │
│  - pin_interrupt_configure()                        │
│  - manage_callback()                                │
└─────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┬──────────────┐
        │                       │              │
        ▼                       ▼              ▼
┌───────────────┐      ┌───────────────┐   ┌──────────────┐
│   SoC GPIO    │      │  I2C Expander │   │ SPI Expander │
│   Driver      │      │   Driver      │   │  Driver      │
├───────────────┤      ├───────────────┤   ├──────────────┤
│ Direct HW     │      │ I2C reg R/W   │   │ SPI reg R/W  │
│ register      │      │ with locking  │   │ with CS      │
│ access        │      │               │   │              │
└───────────────┘      └───────────────┘   └──────────────┘
        │                       │              │
        └───────────┬───────────┴──────────────┘
                    ▼
        ┌────────────────────────────┐
        │  Hardware GPIO Pins        │
        └────────────────────────────┘
```

## GPIO Configuration Flags (Quick Reference)

```
gpio_flags_t (32 bits):

Common flags:
  GPIO_INPUT (BIT(16))               - Configure as input
  GPIO_OUTPUT (BIT(17))              - Configure as output
  GPIO_OUTPUT_INIT_LOW               - Output initialized to low
  GPIO_OUTPUT_INIT_HIGH              - Output initialized to high
  GPIO_PULL_UP                       - Enable pull-up resistor
  GPIO_PULL_DOWN                     - Enable pull-down resistor
  GPIO_OPEN_DRAIN                    - Open-drain output
  GPIO_ACTIVE_LOW                    - Pin is active-low (0 = active)

Interrupt flags:
  GPIO_INT_DISABLE                   - Disable interrupt
  GPIO_INT_EDGE_RISING               - Rising edge trigger
  GPIO_INT_EDGE_FALLING              - Falling edge trigger
  GPIO_INT_EDGE_BOTH                 - Both edges trigger
  GPIO_INT_LEVEL_LOW                 - Low level trigger
  GPIO_INT_LEVEL_HIGH                - High level trigger
```

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **gpio_dt_spec** | GPIO pin from devicetree | `port` (device), `pin` (number), `dt_flags` (config) |
| **gpio_driver_config** | Driver configuration | `port_pin_mask` (valid pins), `ngpios` (pin count) |
| **gpio_driver_data** | Driver runtime data | Device-specific state |
| **gpio_driver_api** | Driver API table | Function pointers for all GPIO operations |
| **gpio_callback** | Interrupt callback | `handler`, `pin_mask`, list node |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation steps.

## Quick Start Workflow

1. **Define Register Map** and bit definitions for GPIO hardware
2. **Implement pin_configure()** – Set pin direction, pull resistors, drive mode
3. **Implement port_get_raw()** – Read current pin state
4. **Implement port_set_masked_raw()** – Write pins with mask
5. **Implement port_set_bits_raw() / port_clear_bits_raw()** – Set/clear pins
6. **Implement port_toggle_bits()** – Toggle pins
7. **Implement pin_interrupt_configure()** – Configure interrupt triggers
8. **Implement manage_callback()** – Register interrupt callbacks
9. **Define API Structure** with all function pointers
10. **Create Devicetree Binding** with gpio-controller property
11. **Implement Init Function** – Initialize hardware and register driver
12. **Device Instantiation Macro** – `DEVICE_DT_INST_DEFINE()` with API

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### Using gpio_dt_spec

```c
// From devicetree
const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

// Configure
gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);

// Write
gpio_pin_set_dt(&led, 1);
```

### Shadow Registers for I2C/SPI Expanders

```c
struct gpio_expander_data {
    uint8_t output_shadow;  // Cache of output register
    struct k_mutex lock;     // Thread safety
};

// Read-modify-write with shadow register
static int expander_port_set_bits_raw(const struct device *dev, gpio_port_pins_t pins)
{
    struct gpio_expander_data *data = dev->data;
    
    k_mutex_lock(&data->lock, K_FOREVER);
    data->output_shadow |= pins;
    ret = i2c_reg_write_byte_dt(&config->i2c, OUTPUT_REG, data->output_shadow);
    k_mutex_unlock(&data->lock);
    
    return ret;
}
```

### Interrupt Handling

```c
// In ISR or work queue
static void gpio_isr(const struct device *dev)
{
    struct gpio_data *data = dev->data;
    uint8_t int_status = read_interrupt_status(dev);
    
    // Fire callbacks for pins that triggered
    gpio_fire_callbacks(&data->callbacks, dev, int_status);
}
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Use `gpio_dt_spec` for devicetree integration
- Always check `device_is_ready()` or `gpio_is_ready_dt()`
- Use shadow registers for I2C/SPI expanders (caching)
- Handle active-low logic correctly (use `GPIO_ACTIVE_LOW` flag)
- Initialize outputs before configuring direction
- Use locking (`k_mutex`) for I2C/SPI expanders (thread safety)
- Return `-EWOULDBLOCK` from ISR context for operations that need to wait
- Validate pin number against `port_pin_mask`
- Fire callbacks from interrupt handler using `gpio_fire_callbacks()`

❌ **DON'T**:
- Don't assume contiguous pin layout (use `port_pin_mask` to validate)
- Don't read hardware in `port_set_*()` for expanders (use shadow registers)
- Don't ignore active-low pins (they invert logic)
- Don't configure direction before setting output value (glitches)
- Don't block in ISR context
- Don't forget to include optional APIs (`port_toggle_bits` is optional)

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with code examples.

## Devicetree Integration (Quick Reference)

### GPIO Controller Binding

```yaml
compatible: "vendor,gpio-controller"
include: gpio-controller.yaml

properties:
  ngpios:
    type: int
    required: true
    description: Number of GPIO pins

  gpio-reserved-ranges:
    type: array
    description: Reserved pin ranges (non-GPIO functions)

gpio-cells:
  - pin
  - flags
```

### Consumer Usage

```dts
gpio_controller: gpio@40000 {
    compatible = "vendor,gpio-controller";
    reg = <0x40000 0x1000>;
    gpio-controller;
    #gpio-cells = <2>;
    ngpios = <32>;
};

led0 {
    gpios = <&gpio_controller 5 GPIO_ACTIVE_HIGH>;
};
```

**See**: [reference/devicetree-bindings.md](reference/devicetree-bindings.md) for complete binding patterns and examples.

## References

**Zephyr Documentation**:
- **GPIO API**: `zephyr/include/zephyr/drivers/gpio.h`
- **GPIO Drivers**: `zephyr/drivers/gpio/`
- **Bindings**: `zephyr/dts/bindings/gpio/`

**Example Drivers**:
- **ADP5585** (I2C): `drivers/gpio/gpio_adp5585.c`
- **MAX14906** (SPI with diagnostics): `drivers/gpio/gpio_max14906.c`
- **AD559x** (MFD child): `drivers/gpio/gpio_ad559x.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-12)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Binding patterns and examples
- [reference/api-usage.md](reference/api-usage.md) – Consumer GPIO usage examples
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (10 detailed patterns)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (10 debug tips)
- [examples/complete-driver.c](examples/complete-driver.c) – Complete GPIO driver example

## Summary Checklist

### Driver Implementation
- [ ] Register map defined with bit masks
- [ ] Config structure with `port_pin_mask`, `ngpios`
- [ ] Data structure with device-specific runtime state
- [ ] `pin_configure()` implemented (direction, pull, drive)
- [ ] `port_get_raw()` implemented (read pins)
- [ ] `port_set_masked_raw()` implemented (write with mask)
- [ ] `port_set_bits_raw()` and `port_clear_bits_raw()` implemented
- [ ] `port_toggle_bits()` implemented (optional)
- [ ] `pin_interrupt_configure()` implemented (if interrupt support)
- [ ] `manage_callback()` implemented (if interrupt support)
- [ ] API structure defined with all function pointers
- [ ] Init function initializes hardware
- [ ] Device instantiation macro with API

### Devicetree
- [ ] Binding created with `gpio-controller.yaml` include
- [ ] `gpio-cells` = 2 (pin, flags)
- [ ] `ngpios` property defined
- [ ] Board overlay uses `gpio-controller` and `#gpio-cells`

### Testing
- [ ] Pin configuration works (input, output, pull resistors)
- [ ] Read/write operations work
- [ ] Port operations work (multi-pin)
- [ ] Interrupts trigger and callbacks fire (if supported)
- [ ] Active-low pins work correctly
- [ ] I2C/SPI communication works (for expanders)
