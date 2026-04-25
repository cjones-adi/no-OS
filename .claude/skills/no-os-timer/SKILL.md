---
name: no-os-timer
description: 'Complete guide to no-OS Timer platform drivers for embedded systems. Use when implementing hardware timers, porting to new platforms (Maxim, STM32, Mbed, ADUCM), configuring timer frequency and tick counts, creating time delays, measuring elapsed time, generating time-triggered interrupts, or debugging timing issues.'
---

# no-OS Timer Platform Drivers

Quick-start guide for using no-OS timer platform drivers for hardware-based timing, delays, and measurements.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/platform-apis.md**:
- User asks: "port timer", "new platform", "how to implement timer for X"
- Questions about: platform-specific extras, STM32 HAL handles, ADUCM clock sources
- Mentions: Maxim, STM32, ADUCM, Pico, Xilinx, Mbed platform support
- Need: complete porting guide, platform ops implementation

**Triggers to read reference/api-usage.md**:
- User asks: "how to use timer", "timer examples", "patterns", "how to measure time"
- Questions about: specific timer functions (start, stop, counter_get, etc.)
- Mentions: delays, interrupts, IIO triggers, sampling, elapsed time
- Need: complete usage patterns, code examples, multi-timer coordination

**Triggers to read reference/configuration.md**:
- User asks: "configure timer", "timer setup", "data structures", "frequency vs ticks"
- Questions about: init_param, timer_desc, platform_ops, period calculation
- Mentions: architecture, file structure, timer concepts
- Need: detailed configuration reference, frequency/tick tables

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "timer guidelines", "recommendations"
- Questions about: timer selection, resource management, power management
- Mentions: patterns/anti-patterns, timer assignment strategy
- Need: quality guidelines, testing strategies, documentation practices

**Triggers to read reference/troubleshooting.md**:
- Build/runtime errors in user output
- User says: "timer not working", "not counting", "inaccurate", "interrupt not firing"
- Questions about: debugging techniques, platform-specific issues
- Specific errors: counter stuck, timing wrong, high CPU usage
- Need: systematic debugging, error solutions, verification techniques

---

## When to Use This Skill

- Implement hardware timer functionality in device drivers
- Port timer drivers to new platforms (Maxim, STM32, Mbed, ADUCM, Xilinx, Pico)
- Configure timer frequency and tick counts
- Create precise time delays
- Generate time-triggered interrupts
- Measure elapsed time in nanoseconds
- Implement periodic tasks or data acquisition
- Control PWM (Pulse Width Modulation) timing
- Debug timing synchronization issues
- Interface with IIO hardware triggers
- Implement real-time sampling

## Timer Overview

**Hardware Timer** provides time measurement and time-based triggering on microcontrollers:

- **Time measurement** - Count clock cycles to measure time intervals
- **Precise timing** - Independent of software execution
- **Interrupt capability** - Generate periodic or one-shot interrupts
- **Configurable frequency** - Set counting speed independently
- **Auto-reload** - Automatically reset after reaching tick count
- **Full-duplex operation** - Measures while application runs

**Benefits:**
- Accurate timing (hardware-based, not software-dependent)
- Low overhead (minimal CPU impact once started)
- Precise delays (better than software delays)
- Interrupt-driven (enable event-based programming)
- Multiple options (supports multiple timer peripherals)
- Portable (abstracted across all platforms)

**Architecture:**
```
Application → no_os_timer.h → platform_timer.c → Vendor HAL
```

## Quick Start

### 1. Basic Timer Initialization

```c
struct no_os_timer_desc *timer_desc;

struct no_os_timer_init_param timer_init = {
    .id = 0,                        // Timer 0
    .freq_hz = 10000,               // 10 kHz = 0.1 ms per tick
    .ticks_count = 1000,            // 1000 ticks = 100 ms period
    .platform_ops = &max_timer_ops,
};

// Initialize timer
int ret = no_os_timer_init(&timer_desc, &timer_init);
if (ret) {
    printf("Timer init failed\n");
    return ret;
}

// Start timer
no_os_timer_start(timer_desc);

// Use timer...

// Cleanup
no_os_timer_stop(timer_desc);
no_os_timer_remove(timer_desc);
```

### 2. Key Concepts: Frequency vs. Ticks

**Frequency (freq_hz):** Timer clock speed in Hertz
- 10,000 Hz = Each tick is 0.1 ms
- 100,000 Hz = Each tick is 10 µs
- 1,000,000 Hz = Each tick is 1 µs

**Ticks Count (ticks_count):** Number of ticks before auto-reload
- Timer counts: 0 → 1 → 2 → ... → (ticks_count-1) → 0 → 1 → ...

**Period Calculation:**
```
Period (seconds) = ticks_count / freq_hz
Example: ticks_count=1000, freq_hz=10000 → 1000/10000 = 0.1 seconds = 100ms
```

### 3. Common Operations

**Start/Stop Timer:**
```c
no_os_timer_start(timer_desc);   // Start counting
no_os_timer_stop(timer_desc);    // Stop counting
```

**Read Counter:**
```c
uint32_t count;
no_os_timer_counter_get(timer_desc, &count);
printf("Current count: %u\n", count);
```

**Reset Counter:**
```c
no_os_timer_counter_set(timer_desc, 0);  // Reset to 0
```

**Measure Elapsed Time:**
```c
uint64_t elapsed_ns;
no_os_timer_get_elapsed_time_nsec(timer_desc, &elapsed_ns);
double elapsed_ms = elapsed_ns / 1000000.0;
printf("Elapsed: %.3f ms\n", elapsed_ms);
```

**Change Frequency:**
```c
no_os_timer_count_clk_set(timer_desc, 100000);  // 100 kHz
```

### 4. Simple Hardware Delay Pattern

```c
void delay_ms(struct no_os_timer_desc *timer, uint32_t ms)
{
    uint32_t ticks_needed = (ms * 10);  // 10 ticks per ms @ 10 kHz

    no_os_timer_counter_set(timer, 0);
    no_os_timer_start(timer);

    uint32_t count;
    do {
        no_os_timer_counter_get(timer, &count);
    } while (count < ticks_needed);

    no_os_timer_stop(timer);
}

// Usage
delay_ms(timer_desc, 100);  // 100 ms delay
```

## Quick Reference

### API Functions

| Function | Purpose |
|----------|---------|
| `no_os_timer_init()` | Initialize timer |
| `no_os_timer_remove()` | Free timer resources |
| `no_os_timer_start()` | Start counting |
| `no_os_timer_stop()` | Stop counting |
| `no_os_timer_counter_get()` | Read current count |
| `no_os_timer_counter_set()` | Set counter value |
| `no_os_timer_count_clk_get()` | Get frequency |
| `no_os_timer_count_clk_set()` | Change frequency |
| `no_os_timer_get_elapsed_time_nsec()` | Measure elapsed time |

### Frequency Selection Guide

| Frequency | Tick Period | Use Case |
|-----------|------------|----------|
| 1,000 Hz | 1 ms | General purpose timing |
| 10,000 Hz | 100 µs | Moderate precision |
| 100,000 Hz | 10 µs | High precision timing |
| 1,000,000 Hz | 1 µs | Very precise measurement |
| 10,000,000 Hz | 100 ns | Ultra-precise timing |

### Platform Support

| Platform | Notes | Max Frequency | Multi-Timer |
|----------|-------|---------------|-------------|
| Maxim | No extra params needed | 32 MHz | Yes (multiple TMRx) |
| STM32 | Requires HAL handle from CubeMX | 160+ MHz | Yes (multiple TIMx) |
| ADUCM3029 | Fixed freq steps (PCLK dividers) | ~26 MHz | Yes (Timer 1 available) |
| Mbed | Limited support, object-based | Platform dependent | Limited |
| Pico | Alarm-based timers | 125 MHz | Yes (4 alarms) |
| Xilinx | Programmable logic timer core | 100+ MHz | Yes |

### Data Structures

```c
struct no_os_timer_init_param {
    uint16_t id;                    // Timer ID (0, 1, 2, etc.)
    uint32_t freq_hz;               // Count frequency in Hz
    uint32_t ticks_count;           // Ticks until auto-reload
    const struct no_os_timer_platform_ops *platform_ops;
    void *extra;                    // Platform-specific parameters
};

struct no_os_timer_desc {
    void *mutex;                    // Thread safety lock
    uint16_t id;                    // Timer ID
    uint32_t freq_hz;               // Configured frequency
    uint32_t ticks_count;           // Configured tick count
    const struct no_os_timer_platform_ops *platform_ops;
    void *extra;                    // Platform-specific data
};
```

## Common Patterns

### Pattern: Time Measurement

```c
// Initialize high-frequency timer
struct no_os_timer_init_param timer_init = {
    .id = 2,
    .freq_hz = 1000000,              // 1 MHz = 1 µs per tick
    .ticks_count = 0xFFFFFFFF,       // Large count
    .platform_ops = &max_timer_ops,
};

no_os_timer_init(&timer_desc, &timer_init);
no_os_timer_start(timer_desc);

// Measure function execution time
uint64_t start, end;
no_os_timer_get_elapsed_time_nsec(timer_desc, &start);
slow_function();
no_os_timer_get_elapsed_time_nsec(timer_desc, &end);

printf("Function took %.3f µs\n", (end - start) / 1000.0);
```

### Pattern: Periodic Interrupt

```c
// Initialize timer (100 ms period)
struct no_os_timer_init_param timer_init = {
    .id = 0,
    .freq_hz = 1000,                      // 1 kHz
    .ticks_count = 100,                   // 100 ms
    .platform_ops = &stm32_timer_ops,
};

no_os_timer_init(&timer_desc, &timer_init);

// Setup IRQ
struct no_os_callback_desc irq_cb = {
    .callback = timer_callback,
    .event = NO_OS_EVT_TIM_ELAPSED,
    .peripheral = NO_OS_TIM_IRQ,
};

no_os_irq_register_callback(irq_desc, TIMER_IRQ_ID, &irq_cb);
no_os_irq_enable(irq_desc, TIMER_IRQ_ID);
no_os_timer_start(timer_desc);
```

## Best Practices

1. **Always initialize before use** - Call `no_os_timer_init()` with proper parameters
2. **Choose appropriate frequency** - Match resolution needed (1 MHz for µs, 1 kHz for ms)
3. **Reset counter before use** - Set to 0 with `counter_set()` before starting
4. **Start after configuration** - Call `no_os_timer_start()` when ready
5. **Stop when done** - Call `no_os_timer_stop()` to save power
6. **Verify tick calculations** - Double-check period = ticks_count / freq_hz
7. **Use timer 0 sparingly** - Often reserved for system delays
8. **Check return values** - Verify all operations succeed
9. **Free resources** - Call `no_os_timer_remove()` on cleanup
10. **Test on target platform** - Verify frequency accuracy

## Common Issues

**Timer not counting:**
- Ensure `no_os_timer_start()` was called
- Reset counter with `counter_set(0)` before starting
- Verify peripheral clock enabled

**Timing inaccurate:**
- Check actual vs. requested frequency with `count_clk_get()`
- Verify period calculation: `period = ticks_count / freq_hz`
- Some platforms (ADUCM) have fixed frequency steps

**Interrupt not firing:**
- Call `no_os_irq_enable()` and `no_os_irq_register_callback()`
- Verify correct IRQ number for platform
- Ensure timer is started

**See**: `reference/troubleshooting.md` for complete debugging guide.

## Official Documentation

For authoritative and up-to-date information about the no-OS timer platform driver:

**Primary Documentation:**
- **no-OS Timer Driver**: https://wiki.analog.com/resources/no-os/drivers/timer
  - Complete API reference and platform details
  - Time delay and interrupt examples
  - Supported platforms and limitations

**Related Documentation:**
- **no-OS GitHub Repository**: https://github.com/analogdevicesinc/no-OS
  - Source code: `drivers/platform/[platform]/[platform]_timer.c`
  - Timer API: `drivers/api/no_os_timer.c`
- **no-OS IRQ Driver**: https://wiki.analog.com/resources/no-os/drivers/irq
  - Required for timer interrupt functionality
- **no-OS Wiki**: https://wiki.analog.com/resources/tools-software/uc-drivers/no-os
  - General no-OS framework documentation

## Reference Documentation

**When to read each file** (use Read tool):

### reference/platform-apis.md
Platform-specific timer implementations and complete porting guide for new platforms. Covers Maxim, STM32, ADUCM, Pico, Xilinx, Mbed platform details and platform ops implementation.

### reference/api-usage.md
Complete timer API usage patterns and examples: start/stop, counter management, frequency control, elapsed time measurement. Includes 5 common patterns (delays, interrupts, measurement, configurable rates, multiple timers).

### reference/configuration.md
Timer configuration details: data structures, frequency vs. ticks concepts, timer modes, initialization workflow, architecture overview, file structure.

### reference/best-practices.md
Timer usage guidelines: resource management, frequency selection, power management, error handling, testing strategies, common patterns and anti-patterns.

### reference/troubleshooting.md
Complete debugging guide: timer not counting, timing inaccurate, interrupt issues, counter problems, high CPU usage, platform-specific issues, debugging techniques.

## Summary

The no-OS timer platform driver provides:
- **Simple abstraction** for hardware timer control
- **Flexible configuration** - Frequency and tick count independent
- **Accurate timing** - Hardware-based precision
- **Interrupt capability** - Time-triggered events
- **Time measurement** - Nanosecond resolution elapsed time
- **Platform portability** - Works across all MCUs (with varying capabilities)

**Key workflow:**
1. Initialize with `no_os_timer_init()` specifying frequency and tick count
2. Calculate period as: `Period = ticks_count / freq_hz`
3. Reset counter with `counter_set(0)` before use
4. Use `start()` and `stop()` to control counting
5. Poll `counter_get()` for delay loops
6. Register IRQ callbacks for time-triggered tasks
7. Use `get_elapsed_time_nsec()` for precise measurements

Timers are fundamental to embedded systems, essential for creating delays, generating periodic interrupts for data acquisition, measuring execution time, and implementing real-time sampling in sensor applications.
