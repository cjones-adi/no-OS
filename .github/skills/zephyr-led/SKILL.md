---
name: zephyr-led
description: 'Complete guide to Zephyr LED controller drivers for controlling LEDs. Use when implementing LED controller drivers, setting brightness levels, configuring LED blinking, controlling RGB/multicolor LEDs, implementing LED patterns, or debugging LED control issues.'
---

# Zephyr LED Driver Development

This skill provides comprehensive understanding of the Zephyr LED (Light-Emitting Diode) controller driver subsystem.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement LED driver", "step by step", "on/off", "set_brightness", "blink"
- Questions about: driver API, register access, RGB control, color support
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-7) with complete code

**Triggers to read reference/api-usage.md**:
- User asks: "how to use LED", "turn on LED", "set brightness", "configure blinking", "RGB color"
- Questions about: led_on, led_off, led_set_brightness, led_blink, led_set_color
- Need: application-side LED usage examples (5 patterns)

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "LED patterns", "brightness fading", "color cycling", "multi-LED"
- Questions about: status indicators, pattern sequencer, RGB effects
- Need: design patterns (5 detailed patterns)

**Triggers to read reference/debugging.md**:
- User says: "LED not working", "wrong brightness", "debugging", "LED issue"
- Build/runtime errors with LED
- Questions about: device ready, I2C/SPI communication, logging
- Need: debugging steps (5 detailed tips)

---

## When to Use This Skill

Use this skill when you need to:
- Implement LED controller drivers for Zephyr
- Control LED on/off state
- Set LED brightness (0-100%)
- Configure LED blinking patterns
- Control RGB or multicolor LEDs
- Implement LED matrix controllers
- Work with I2C/SPI LED driver chips
- Support PWM-based LED dimming
- Debug LED control issues

## What is an LED Controller?

**LED controllers** are integrated circuits or peripherals that control LEDs, providing features like:

- **On/Off Control**: Basic LED enable/disable
- **Brightness Control**: PWM or current-based dimming (0-100%)
- **Blinking**: Automatic hardware blinking with configurable periods
- **RGB/Multicolor**: Independent control of multiple color channels
- **LED Matrix**: Control arrays of LEDs
- **Current Limiting**: Prevent LED overdrive

### Common LED Controller Types

- **GPIO-based**: Simple LED control via GPIO pins
- **PWM-based**: LED dimming using PWM duty cycle
- **I2C/SPI Drivers**: Dedicated LED driver chips (IS31FL3xxx, LP55xx, etc.)
- **RGB Controllers**: Multi-channel color LED control

## Architecture Overview

```
Application
    ↓
LED API (led.h)
    ↓
LED Driver (led_*.c)
    ↓
Hardware Control (GPIO, PWM, I2C, SPI)
    ↓
Physical LEDs
```

## File Structure (Quick Reference)

- **Driver**: `drivers/led/led_<chip>.c`
- **Binding**: `dts/bindings/led/<vendor>,<chip>-led.yaml`
- **Public Header** (optional): `include/zephyr/drivers/led/<chip>.h`
- **Kconfig**: Update `drivers/led/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **led_info** | LED capabilities | `label`, `num_colors`, `color_mapping`, `index` |
| **led_driver_api** | Driver API table | `on()`, `off()`, `set_brightness()`, `set_color()`, `write_channels()` |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Quick Start Workflow

1. **Define Register Map** (for I2C/SPI chips)
2. **Define Config and Data Structures**
3. **Implement on/off Functions** – Basic LED enable/disable
4. **Implement set_brightness Function** – Brightness control (0-100%)
5. **Implement Blinking** (Optional) – Hardware-based blinking
6. **Implement RGB Control** (Optional) – Multi-color LED control
7. **Define API Structure and Device Instantiation**

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### Turn LED On/Off

```c
led_on(led_dev, 0);   // Turn on LED 0
led_off(led_dev, 0);  // Turn off LED 0
```

### Set LED Brightness

```c
// Set brightness to 50%
led_set_brightness(led_dev, 0, 50);

// Set brightness to full (100%)
led_set_brightness(led_dev, 0, 100);
```

### Configure LED Blinking

```c
// Blink LED 0: 500ms on, 500ms off (1Hz)
led_blink(led_dev, 0, 500, 500);
```

### Set RGB Color

```c
// Set RGB LED to red (100% red, 0% green, 0% blue)
uint8_t rgb[] = {255, 0, 0};
led_set_color(led_dev, 0, 3, rgb);

// Set to purple (100% red, 0% green, 100% blue)
uint8_t purple[] = {255, 0, 255};
led_set_color(led_dev, 0, 3, purple);
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always check device ready state before use
- Use led_set_brightness() for dimming instead of PWM directly
- Clamp brightness values to 0-100%
- Use hardware blinking when available
- Support both on/off and brightness control
- Provide LED info for RGB LEDs
- Test each LED channel individually
- Use appropriate current limiting

❌ **DON'T**:
- Don't exceed LED current ratings
- Don't assume all LEDs support brightness control
- Don't forget to check hardware capabilities
- Don't use software delays for blinking (use hardware blink)
- Don't mix RGB channel order without proper mapping

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **LED API**: `zephyr/include/zephyr/drivers/led.h`
- **LED Drivers**: `zephyr/drivers/led/`
- **Bindings**: `zephyr/dts/bindings/led/`

**Example Drivers**:
- **GPIO LED**: `drivers/led/led_gpio.c`
- **PWM LED**: `drivers/led/led_pwm.c`
- **IS31FL3194**: `drivers/led/is31fl3194.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-7)
- [reference/api-usage.md](reference/api-usage.md) – Application usage (5 patterns)
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (5 detailed)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (5 tips)

## Summary Checklist

### Driver Implementation
- [ ] Register map defined (if I2C/SPI chip)
- [ ] Config structure with bus specs
- [ ] Data structure with runtime state
- [ ] `on()` / `off()` implemented
- [ ] `set_brightness()` implemented
- [ ] `blink()` implemented (if supported)
- [ ] `set_color()` / `write_channels()` implemented (if RGB)
- [ ] API structure defined with function pointers
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created
- [ ] LED properties defined
- [ ] Kconfig entry with dependencies
- [ ] Board DTS defines LEDs

### Testing
- [ ] On/off works
- [ ] Brightness control works
- [ ] Blinking works (if supported)
- [ ] RGB color setting works (if RGB)
- [ ] All LED channels tested
