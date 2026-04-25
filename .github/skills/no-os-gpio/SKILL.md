---
name: no-os-gpio
description: 'Complete guide to no-OS GPIO (General Purpose Input/Output) platform drivers for embedded systems. Use when implementing GPIO control, porting to new platforms (Maxim, STM32, Mbed), configuring pin direction and pull-up/pull-down resistors, reading digital inputs, writing digital outputs, handling GPIO interrupts, or debugging GPIO issues.'
---

# no-OS GPIO Platform Drivers

Quick-start guide for using no-OS GPIO platform driver abstraction layer for embedded systems.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/configuration.md**:
- User asks: "data structures", "init param", "pull resistor", "GPIO values", "pin numbering"
- Questions about: no_os_gpio_desc, no_os_gpio_init_param, NO_OS_PULL_*, NO_OS_GPIO_HIGH_Z
- Need: complete structure definitions, field explanations, platform extras
- Mentions: port/pin numbering, platform-specific configuration

**Triggers to read reference/api-usage.md**:
- User asks: "how to use", "example code", "patterns", "initialize GPIO"
- Questions about: required vs optional GPIO, direction control, read/write operations
- Need: complete usage examples, LED/button/CS/reset patterns
- Implementing: device driver using GPIO, control signals

**Triggers to read reference/platform-apis.md**:
- User asks: "port to new platform", "implement platform driver", "platform ops"
- Questions about: myplatform_gpio.c, platform_ops function pointers
- Need: platform implementation template, vendor HAL integration
- Creating: new platform GPIO driver, porting guide

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "recommendations", "power optimization"
- Questions about: anti-patterns, design patterns, performance
- Need: quality guidelines, common mistakes, optimization strategies
- Reviewing: GPIO usage in driver, improving existing code

**Triggers to read reference/troubleshooting.md**:
- Build/runtime errors in user output
- User says: "doesn't work", "not reading", "not changing", "high power"
- Questions about: debugging techniques, GPIO not working, inconsistent readings
- Specific issues: floating input, pin mux conflict, drive strength, platform porting

---

## When to Use This Skill

- Implement GPIO control in device drivers
- Port GPIO drivers to new platforms (Maxim, STM32, Mbed, etc.)
- Configure GPIO pins as inputs or outputs
- Set pull-up, pull-down, or high-impedance states
- Read digital input values
- Write digital output values (HIGH/LOW/HIGH-Z)
- Handle optional GPIOs (may or may not be present)
- Debug GPIO configuration issues
- Control LEDs, buttons, chip select, reset pins, etc.

## What is GPIO?

**GPIO (General Purpose Input/Output)** provides digital control of microcontroller pins:

- **Flexible direction**: Configure as input or output
- **Digital states**: HIGH (1), LOW (0), or HIGH-Z (tri-state)
- **Pull resistors**: Built-in pull-up or pull-down
- **Simple interface**: Set, get, and configure
- **Platform abstraction**: Works across all MCUs

### Benefits

- **Simple control** - Direct hardware pin control
- **Flexible** - Same pin can be input or output
- **Portable** - Abstracted across platforms
- **Essential** - Used by almost every driver

## Architecture Overview

```
┌──────────────────────────────────────────┐
│    User Application / Device Driver     │
│  (Platform-independent code)            │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │   no_os_gpio.h      │  Platform-agnostic API
    │   (Generic)         │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────────────────┐
    │                                  │
┌───▼──────────┐        ┌──────────────▼───┐
│maxim_gpio.c  │        │   mbed_gpio.cpp  │
│maxim_gpio.h  │        │   mbed_gpio.h    │
└───┬──────────┘        └──────────┬───────┘
    │                               │
┌───▼──────────┐        ┌──────────▼───────┐
│ Maxim HAL    │        │   Mbed HAL       │
│ (Vendor SDK) │        │   (Vendor SDK)   │
└──────────────┘        └──────────────────┘
```

## Quick Start

### Basic GPIO Initialization

```c
struct no_os_gpio_desc *gpio_desc;

struct no_os_gpio_init_param gpio_init = {
    .port = 0,                    // Port 0
    .number = 5,                  // Pin 5
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
};

// Get GPIO (fails if not available)
ret = no_os_gpio_get(&gpio_desc, &gpio_init);
if (ret)
    return ret;

// Configure as output, set HIGH
no_os_gpio_direction_output(gpio_desc, NO_OS_GPIO_HIGH);
```

### Optional GPIO

```c
struct no_os_gpio_desc *led_gpio = NULL;

struct no_os_gpio_init_param led_init = {
    .port = 1,
    .number = 10,  // Set to -1 if not present
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
};

// Get optional - returns success even if pin doesn't exist
no_os_gpio_get_optional(&led_gpio, &led_init);

// Check if GPIO is available before using
if (led_gpio) {
    no_os_gpio_direction_output(led_gpio, NO_OS_GPIO_HIGH);
}
```

## Core Data Structures (Quick Reference)

### no_os_gpio_init_param

```c
struct no_os_gpio_init_param {
    int32_t port;                    // Port number
    int32_t number;                  // Pin number (-1 = not present)
    enum no_os_gpio_pull_up pull;   // Pull resistor config
    const struct no_os_gpio_platform_ops *platform_ops;
    void *extra;                     // Platform-specific params
};
```

### no_os_gpio_pull_up

```c
enum no_os_gpio_pull_up {
    NO_OS_PULL_NONE,           // No pull resistor
    NO_OS_PULL_UP,             // Strong pull-up
    NO_OS_PULL_DOWN,           // Strong pull-down
    NO_OS_PULL_UP_WEAK,        // Weak pull-up
    NO_OS_PULL_DOWN_WEAK       // Weak pull-down
};
```

### no_os_gpio_values

```c
enum no_os_gpio_values {
    NO_OS_GPIO_LOW,            // Logic low (0V)
    NO_OS_GPIO_HIGH,           // Logic high (VDD)
    NO_OS_GPIO_HIGH_Z          // High impedance (tri-state)
};
```

**See**: `reference/configuration.md` for complete structure definitions and platform extras.

## GPIO Operations (Quick Reference)

### Configure Direction

```c
// Set as input
no_os_gpio_direction_input(gpio_desc);

// Set as output with initial value
no_os_gpio_direction_output(gpio_desc, NO_OS_GPIO_LOW);

// Get current direction
uint8_t dir;
no_os_gpio_get_direction(gpio_desc, &dir);
// dir: NO_OS_GPIO_IN (0) or NO_OS_GPIO_OUT (1)
```

### Read/Write Values

```c
// Set output value
no_os_gpio_set_value(gpio_desc, NO_OS_GPIO_HIGH);

// Get input/output value
uint8_t value;
no_os_gpio_get_value(gpio_desc, &value);
```

### Cleanup

```c
no_os_gpio_remove(gpio_desc);
```

**See**: `reference/api-usage.md` for complete usage patterns and examples.

## Common Patterns (Quick Reference)

### LED Control

```c
struct no_os_gpio_desc *led;

no_os_gpio_get(&led, &led_init);
no_os_gpio_direction_output(led, NO_OS_GPIO_LOW);  // LED off

// Turn on
no_os_gpio_set_value(led, NO_OS_GPIO_HIGH);
```

### Button with Pull-up

```c
struct no_os_gpio_init_param button_init = {
    .port = 0,
    .number = 15,
    .pull = NO_OS_PULL_UP,  // Active-low button
    .platform_ops = &max_gpio_ops,
};

no_os_gpio_get(&button, &button_init);
no_os_gpio_direction_input(button);

// Read button (LOW when pressed)
uint8_t pressed;
no_os_gpio_get_value(button, &pressed);
if (pressed == NO_OS_GPIO_LOW)
    printf("Button pressed\n");
```

### Chip Select (Active-Low)

```c
no_os_gpio_get(&cs, &cs_init);
no_os_gpio_direction_output(cs, NO_OS_GPIO_HIGH);  // Deasserted

// Assert CS (select device)
no_os_gpio_set_value(cs, NO_OS_GPIO_LOW);
// ... SPI transfer ...
// Deassert CS
no_os_gpio_set_value(cs, NO_OS_GPIO_HIGH);
```

### Reset Pin

```c
// Hold in reset
no_os_gpio_direction_output(reset, NO_OS_GPIO_LOW);
no_os_mdelay(10);

// Release reset
no_os_gpio_set_value(reset, NO_OS_GPIO_HIGH);
no_os_mdelay(100);  // Wait for device to initialize
```

**See**: `reference/api-usage.md` for additional patterns (bidirectional I/O, optional GPIO handling).

## Function Reference Table

| Function | Purpose |
|----------|---------|
| `no_os_gpio_get()` | Get GPIO (required) |
| `no_os_gpio_get_optional()` | Get GPIO (optional, can be absent) |
| `no_os_gpio_remove()` | Free GPIO resources |
| `no_os_gpio_direction_input()` | Configure as input |
| `no_os_gpio_direction_output()` | Configure as output with initial value |
| `no_os_gpio_get_direction()` | Read current direction |
| `no_os_gpio_set_value()` | Write output value |
| `no_os_gpio_get_value()` | Read input/output value |

## Pull Resistor Reference Table

| Pull Mode | Use Case |
|-----------|----------|
| `NO_OS_PULL_NONE` | Outputs, inputs with external pull |
| `NO_OS_PULL_UP` | Active-low buttons, I2C/SPI |
| `NO_OS_PULL_DOWN` | Active-high buttons |
| `NO_OS_PULL_UP_WEAK` | Lower power pull-up |
| `NO_OS_PULL_DOWN_WEAK` | Lower power pull-down |

## Value Reference Table

| Value | State |
|-------|-------|
| `NO_OS_GPIO_LOW` | Logic 0 (0V) |
| `NO_OS_GPIO_HIGH` | Logic 1 (VDD) |
| `NO_OS_GPIO_HIGH_Z` | High impedance (tri-state) |

## Best Practices (Quick Reference)

1. **Always configure direction** before use
2. **Set initial value** when configuring as output
3. **Use pull resistors** for floating inputs
4. **Check optional GPIOs** before accessing
5. **Free resources** with `no_os_gpio_remove()`
6. **Avoid unnecessary toggling** - wastes power
7. **Use platform-appropriate drive strength** for outputs
8. **Debounce buttons** in software if no hardware debounce
9. **Consider interrupt-driven** buttons instead of polling
10. **Document pin assignments** clearly

**See**: `reference/best-practices.md` for complete guidelines, design patterns, and anti-patterns.

## Common Issues (Quick Reference)

**GPIO always reads same value**
- Check direction configured as input
- Add pull resistor for floating inputs
- Verify wiring
- Check pin mux (not assigned to other peripheral)

**Output doesn't change**
- Check direction configured as output
- Verify drive strength adequate for load
- Check for pin mux conflict
- Measure voltage to verify

**Inconsistent readings**
- Add pull resistor for floating inputs
- Debounce buttons in software
- Shield long wires from noise

**High power consumption**
- Enable pull resistors on floating inputs
- Use HIGH-Z outputs when not driving
- Reduce unnecessary toggling

**See**: `reference/troubleshooting.md` for complete troubleshooting guide with solutions.

## Porting to New Platforms (Quick Reference)

### Step 1: Create Platform Files

```
drivers/platform/myplatform/
├── myplatform_gpio.c      # Implementation
└── myplatform_gpio.h      # Platform extras
```

### Step 2: Implement Platform Operations

```c
int32_t myplatform_gpio_get(struct no_os_gpio_desc **desc,
                            const struct no_os_gpio_init_param *param);
int32_t myplatform_gpio_direction_input(struct no_os_gpio_desc *desc);
int32_t myplatform_gpio_direction_output(struct no_os_gpio_desc *desc, uint8_t value);
int32_t myplatform_gpio_set_value(struct no_os_gpio_desc *desc, uint8_t value);
int32_t myplatform_gpio_get_value(struct no_os_gpio_desc *desc, uint8_t *value);
int32_t myplatform_gpio_remove(struct no_os_gpio_desc *desc);
```

### Step 3: Define Platform Ops

```c
const struct no_os_gpio_platform_ops myplatform_gpio_ops = {
    .gpio_ops_get = &myplatform_gpio_get,
    .gpio_ops_get_optional = &myplatform_gpio_get,
    .gpio_ops_remove = &myplatform_gpio_remove,
    .gpio_ops_direction_input = &myplatform_gpio_direction_input,
    .gpio_ops_direction_output = &myplatform_gpio_direction_output,
    .gpio_ops_get_direction = &myplatform_gpio_get_direction,
    .gpio_ops_set_value = &myplatform_gpio_set_value,
    .gpio_ops_get_value = &myplatform_gpio_get_value,
};
```

**See**: `reference/platform-apis.md` for complete platform implementation guide with vendor HAL integration.

## Official Documentation

For authoritative and up-to-date information about the no-OS GPIO platform driver, refer to these official resources:

### Primary GPIO Documentation
- **no-OS GPIO Driver Documentation**: https://wiki.analog.com/resources/no-os/drivers/gpio
  - Complete GPIO driver API reference
  - Platform-specific implementation details
  - Configuration examples and usage patterns
  - Troubleshooting and debugging guidance

### Related Documentation
- **no-OS Build Guide**: https://wiki.analog.com/resources/no-os/build
  - How to build projects using GPIO drivers
  - Platform-specific build configurations

- **no-OS Driver Development Guide**: https://wiki.analog.com/resources/no-os/drivers-guide
  - General driver architecture and patterns
  - Best practices for driver implementation

- **no-OS GitHub Repository**: https://github.com/analogdevicesinc/no-OS
  - Source code for GPIO platform implementations
  - Example drivers using GPIO
  - Platform-specific GPIO code (`drivers/platform/[platform]/[platform]_gpio.c`)

- **no-OS Wiki**: https://wiki.analog.com/resources/tools-software/uc-drivers/no-os
  - General no-OS framework documentation
  - Getting started guides

**When to consult**: Use the official GPIO driver documentation as the authoritative reference for API specifications, platform support, and implementation details. This skill provides conceptual understanding and patterns; official docs provide precise specifications.

## Reference Documentation

**When to read each file** (use Read tool):

### reference/configuration.md
Complete data structure reference: no_os_gpio_init_param, no_os_gpio_desc, pull resistor modes, GPIO values, pin numbering, platform extras.

### reference/api-usage.md
Complete API usage guide: initialization workflow, required vs optional GPIO, direction control, read/write operations, common patterns.

### reference/platform-apis.md
Platform implementation guide: porting to new platforms, platform ops, vendor HAL integration, implementation tips.

### reference/best-practices.md
Best practices and guidelines: design patterns, anti-patterns, power optimization, quality recommendations.

### reference/troubleshooting.md
Troubleshooting guide: common issues, debugging techniques, platform porting problems, solutions.

## Summary

The no-OS GPIO platform driver provides:
- **Simple abstraction** for digital I/O control
- **Flexible configuration** - Input, output, pull resistors
- **Optional GPIO support** - Handle absent pins gracefully
- **Platform portability** - Works across all MCUs
- **Easy porting** via platform ops structure

**Key concepts:**
1. Use `no_os_gpio_get()` for required GPIOs (fails if absent)
2. Use `no_os_gpio_get_optional()` for optional GPIOs (succeeds even if absent)
3. Always configure direction before use
4. Set initial value when configuring as output
5. Use appropriate pull resistors for inputs

GPIO is the simplest and most fundamental platform driver in no-OS, used by nearly every device driver for control signals, chip selects, resets, interrupts, and status indication.
