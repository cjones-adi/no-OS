---
name: zephyr-pwm
description: 'Complete guide to Zephyr PWM drivers for generating PWM signals. Use when implementing PWM controller drivers, configuring period and duty cycle, working with PWM capture, handling PWM events, implementing motor control or LED dimming, or debugging PWM output issues.'
---

# Zephyr PWM Driver Development

This skill provides comprehensive understanding of the Zephyr PWM (Pulse Width Modulation) driver subsystem.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement PWM driver", "step by step", "set_cycles", "get_cycles_per_sec"
- Questions about: driver API, register access, clock calculations, polarity control
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-8) with complete code

**Triggers to read reference/api-usage.md**:
- User asks: "how to use PWM", "set period", "duty cycle", "pwm_set_dt", "motor control", "LED dimming"
- Questions about: basic PWM output, polarity, capture mode, servo control
- Need: application-side PWM usage examples (6 patterns)

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "clock calculations", "frequency limits", "polarity support"
- Questions about: period/pulse constraints, timer overflow, capture mode
- Need: design patterns (6 detailed patterns)

**Triggers to read reference/debugging.md**:
- User says: "PWM not working", "wrong frequency", "debugging", "oscilloscope"
- Build/runtime errors with PWM
- Questions about: verify output, clock source, period calculations
- Need: debugging steps (5 detailed tips)

---

## When to Use This Skill

Use this skill when you need to:
- Implement PWM controller drivers for Zephyr
- Configure PWM period and pulse width (duty cycle)
- Generate PWM signals for motor control, LED dimming, or analog output
- Implement PWM input capture
- Work with PWM polarity (normal or inverted)
- Configure multi-channel PWM controllers
- Debug PWM signal generation issues

## What is PWM?

**PWM (Pulse Width Modulation)** is a technique for generating analog-like signals using digital outputs by rapidly switching between high and low states.

### Key Concepts

- **Period**: Total time for one complete PWM cycle (nanoseconds)
- **Pulse Width**: Duration of high portion (duty cycle)
- **Duty Cycle**: Percentage of time signal is high (pulse_width / period × 100%)
- **Frequency**: Number of cycles per second (1 / period)
- **Polarity**: Normal (high = active) or inverted (low = active)

### Common Applications

- **Motor Control**: Variable speed DC motors, servo positioning
- **LED Dimming**: Adjustable brightness
- **Analog Output**: Generate variable voltage via filtering
- **Audio**: Simple tone generation
- **Power Conversion**: DC-DC converters

## File Structure (Quick Reference)

- **Driver**: `drivers/pwm/pwm_<chip>.c`
- **Binding**: `dts/bindings/pwm/<vendor>,<chip>-pwm.yaml`
- **Kconfig**: Update `drivers/pwm/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **pwm_dt_spec** | Devicetree PWM spec | `dev` (device), `channel`, `period`, `flags` |
| **pwm_driver_api** | Driver API table | `set_cycles()`, `get_cycles_per_sec()`, `configure_capture()` |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Key Patterns

### Set PWM Output

```c
// Set 1kHz PWM with 50% duty cycle (period 1ms, pulse 500us)
pwm_set(pwm_dev, 0, PWM_USEC(1000), PWM_USEC(500), 0);

// Or using nanoseconds
pwm_set(pwm_dev, 0, 1000000, 500000, 0);  // 1ms period, 500us pulse
```

### Using pwm_dt_spec

```c
static const struct pwm_dt_spec pwm_led = PWM_DT_SPEC_GET(DT_ALIAS(pwm_led0));

// Set 1kHz, 75% duty cycle
pwm_set_dt(&pwm_led, PWM_USEC(1000), PWM_USEC(750));
```

### Duty Cycle Calculation

```c
// Calculate pulse width for given duty cycle percentage
uint32_t period_ns = 1000000;  // 1ms = 1kHz
uint8_t duty_percent = 75;
uint32_t pulse_ns = (period_ns * duty_percent) / 100;  // 750000ns

pwm_set(pwm_dev, 0, period_ns, pulse_ns, 0);
```

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Config and Data Structures**
3. **Implement set_cycles Function** – Configure period and pulse width
4. **Implement get_cycles_per_sec Function** – Return PWM clock frequency
5. **Implement configure_capture** (Optional) – PWM input capture
6. **Define API Structure** and **Init Function**
7. **Device Instantiation Macro**

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always check device ready state before use
- Use pwm_dt_spec for devicetree-defined PWMs
- Validate period and pulse constraints
- Check hardware supports required frequency range
- Handle polarity in both hardware and API
- Use get_cycles_per_sec for accurate timing
- Document minimum/maximum period limits

❌ **DON'T**:
- Don't assume arbitrary frequencies are supported
- Don't exceed hardware timer limits
- Don't ignore period/pulse validation
- Don't forget to enable PWM clock
- Don't use pulse width larger than period

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **PWM API**: `zephyr/include/zephyr/drivers/pwm.h`
- **PWM Drivers**: `zephyr/drivers/pwm/`
- **Bindings**: `zephyr/dts/bindings/pwm/`

**Example Drivers**:
- **MAX32 PWM**: `drivers/pwm/pwm_max32.c`
- **nRF PWM**: `drivers/pwm/pwm_nrfx.c`
- **STM32 PWM**: `drivers/pwm/pwm_stm32.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-8)
- [reference/api-usage.md](reference/api-usage.md) – Application usage (6 patterns)
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (6 detailed)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (5 tips)

## Summary Checklist

### Driver Implementation
- [ ] Register map defined
- [ ] Config structure with clock source
- [ ] Data structure with runtime state
- [ ] `set_cycles()` implemented
- [ ] `get_cycles_per_sec()` implemented
- [ ] `configure_capture()` implemented (if supported)
- [ ] API structure defined
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created (include pwm-controller.yaml)
- [ ] #pwm-cells defined
- [ ] Kconfig entry with dependencies
- [ ] Board DTS defines PWM

### Testing
- [ ] PWM output verified with oscilloscope
- [ ] Period and duty cycle accurate
- [ ] Polarity control works
- [ ] Multiple channels work
- [ ] Frequency range tested
