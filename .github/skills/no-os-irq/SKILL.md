---
name: no-os-irq
description: 'Complete guide to no-OS IRQ (Interrupt Request) platform drivers for embedded systems. Use when implementing interrupt handlers, porting to new platforms (Maxim, STM32, Xilinx), registering interrupt callbacks, configuring trigger levels and priorities, enabling/disabling interrupts, handling nested interrupts, or debugging interrupt issues.'
---

# no-OS IRQ Platform Drivers

Quick-start guide for no-OS IRQ (Interrupt Request) platform driver abstraction layer for embedded systems.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/platform-apis.md**:
- User asks: "how to port", "implement platform", "create new platform driver"
- Mentions: porting to new MCU, platform-specific implementation
- Questions about: platform_ops structure, ISR dispatcher, callback tables
- Need: complete platform implementation guide, porting steps

**Triggers to read reference/api-usage.md**:
- User asks: "how to use", "register callback", "setup interrupt"
- Mentions: usage patterns, common patterns, examples
- Questions about: initialization workflow, enable/disable, priority configuration
- Need: complete usage examples, code patterns for different scenarios

**Triggers to read reference/interrupt-handling.md**:
- User asks: "trigger modes", "edge vs level", "priority levels", "callback context"
- Mentions: nested interrupts, critical sections, volatile, shared data
- Questions about: trigger level selection, priority management, ISR flow
- Need: detailed interrupt handling mechanisms, data structures, synchronization

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "how to write ISR", "coding guidelines"
- Mentions: ISR design, performance, optimization, patterns
- Questions about: ISR length, blocking operations, debouncing, anti-patterns
- Need: quality guidelines, design principles, what to avoid

**Triggers to read reference/troubleshooting.md**:
- User says: "interrupt doesn't work", "not firing", "continuous interrupts", "crash"
- Mentions: debugging, issues, problems, errors
- Questions about: missed interrupts, data corruption, system crashes
- Need: diagnostic techniques, common problems and solutions

---

## When to Use This Skill

- Implementing interrupt handlers for peripherals and GPIOs
- Porting IRQ drivers to new platforms (Maxim, STM32, Xilinx, etc.)
- Registering interrupt callbacks
- Configuring interrupt trigger levels (edge/level, rising/falling)
- Setting interrupt priorities
- Enabling or disabling interrupts
- Handling global interrupt enable/disable
- Implementing nested interrupt handling
- Debugging interrupt-related issues (missed interrupts, latency)

## What is IRQ?

**IRQ (Interrupt Request)** allows hardware events to immediately interrupt program execution:

- **Asynchronous** – Events handled immediately when they occur
- **Low latency** – Fast response to hardware events
- **CPU efficient** – No polling, CPU can sleep
- **Priority-based** – Critical interrupts preempt lower priority
- **Flexible triggers** – Edge or level sensitive

### Architecture Overview

```
┌──────────────────────────────────────────┐
│       Device Driver / Application        │
│   (Registers callback, enables IRQ)      │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │    no_os_irq.h      │  Platform-agnostic API
    │    (Generic)        │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────────────────┐
    │                                  │
┌───▼──────────┐        ┌──────────────▼───┐
│maxim_irq.c   │        │   xilinx_irq.c   │
│maxim_irq.h   │        │   xilinx_irq.h   │
└───┬──────────┘        └──────────┬───────┘
    │                               │
┌───▼──────────┐        ┌──────────▼───────┐
│ Maxim NVIC   │        │   Xilinx INTC    │
│ (Vendor HAL) │        │   (Vendor HAL)   │
└──────────────┘        └──────────────────┘
                │
                │  Hardware interrupt fires
                ▼
        ┌───────────────────┐
        │  Platform ISR     │
        │  (maxim_irq.c)    │
        └───────┬───────────┘
                │  Dispatch to registered callback
                ▼
        ┌───────────────────┐
        │  User Callback    │
        │  (driver code)    │
        └───────────────────┘
```

## Quick Start

### 1. Initialize IRQ Controller

```c
struct no_os_irq_ctrl_desc *irq_ctrl;

struct no_os_irq_init_param irq_init = {
    .irq_ctrl_id = 0,                // Controller 0
    .platform_ops = &max_irq_ops,
    .extra = NULL,
};

ret = no_os_irq_ctrl_init(&irq_ctrl, &irq_init);
if (ret)
    return ret;
```

### 2. Register Callback

```c
void my_irq_handler(void *context)
{
    struct my_device *dev = (struct my_device *)context;
    dev->irq_count++;
    // Handle interrupt (keep short!)
}

struct no_os_callback_desc gpio_callback = {
    .callback = my_irq_handler,       // Handler function
    .irq_id = 5,                      // IRQ number
    .event = NO_OS_IRQ_EDGE_FALLING,  // Trigger mode
    .priority = 0,                    // Priority (0 = highest)
    .ctx = my_device,                 // User context
};

ret = no_os_irq_register_callback(irq_ctrl, gpio_callback.irq_id,
                                  &gpio_callback);
```

### 3. Enable Interrupt

```c
// Enable specific IRQ
no_os_irq_enable(irq_ctrl, gpio_callback.irq_id);

// Enable global interrupts
no_os_irq_global_enable(irq_ctrl);
```

### 4. Cleanup

```c
// Disable IRQ
no_os_irq_disable(irq_ctrl, irq_id);

// Unregister callback
no_os_irq_unregister_callback(irq_ctrl, irq_id, &callback);

// Remove controller
no_os_irq_ctrl_remove(irq_ctrl);
```

## Core Data Structures

### no_os_callback_desc – Callback Registration

```c
struct no_os_callback_desc {
    void (*callback)(void *context);         // User callback function
    uint32_t irq_id;                         // IRQ number
    enum no_os_irq_trigger_level event;      // Trigger mode
    uint32_t priority;                       // Priority level (0 = highest)
    void *ctx;                               // User context
    void *handle;                            // Platform-specific handle
};
```

### no_os_irq_trigger_level – Trigger Modes

```c
enum no_os_irq_trigger_level {
    NO_OS_IRQ_EDGE_RISING,          // Rising edge (LOW→HIGH)
    NO_OS_IRQ_EDGE_FALLING,         // Falling edge (HIGH→LOW)
    NO_OS_IRQ_EDGE_BOTH,            // Both edges
    NO_OS_IRQ_LEVEL_HIGH,           // High level (continuous, must clear source)
    NO_OS_IRQ_LEVEL_LOW             // Low level (continuous, must clear source)
};
```

**When to use:**
- **EDGE_FALLING** – Button press (pull-up), chip /DRDY signal
- **EDGE_RISING** – Button press (pull-down), data ready active-high
- **EDGE_BOTH** – Quadrature encoder, any state change
- **LEVEL_HIGH/LOW** – Continuous conditions (must clear source in ISR!)

## API Quick Reference

### Initialization and Cleanup

| Function | Purpose |
|----------|---------|
| `no_os_irq_ctrl_init()` | Initialize IRQ controller |
| `no_os_irq_ctrl_remove()` | Free IRQ controller |

### Callback Management

| Function | Purpose |
|----------|---------|
| `no_os_irq_register_callback()` | Register interrupt callback |
| `no_os_irq_unregister_callback()` | Unregister callback |

### Interrupt Control

| Function | Purpose |
|----------|---------|
| `no_os_irq_enable()` | Enable specific IRQ |
| `no_os_irq_disable()` | Disable specific IRQ |
| `no_os_irq_global_enable()` | Enable all interrupts |
| `no_os_irq_global_disable()` | Disable all interrupts |

### Configuration

| Function | Purpose |
|----------|---------|
| `no_os_irq_set_priority()` | Set interrupt priority |
| `no_os_irq_trigger_level_set()` | Set trigger edge/level |

## Common Pattern: GPIO Interrupt

```c
volatile bool button_pressed = false;

void button_handler(void *ctx)
{
    button_pressed = true;  // Set flag (keep ISR short!)
}

// Setup
struct no_os_callback_desc button_cb = {
    .callback = button_handler,
    .irq_id = BUTTON_GPIO_IRQ,
    .event = NO_OS_IRQ_EDGE_FALLING,  // Pull-up, active-low
    .priority = 3,                     // Lower priority
    .ctx = NULL,
};

no_os_irq_register_callback(irq_ctrl, button_cb.irq_id, &button_cb);
no_os_irq_enable(irq_ctrl, button_cb.irq_id);
no_os_irq_global_enable(irq_ctrl);

// Main loop
while (1) {
    if (button_pressed) {
        button_pressed = false;
        printf("Button pressed!\n");
        // Heavy processing here (not in ISR)
    }
}
```

## Critical Best Practices

### 1. Keep ISRs Short and Fast

**Good:**
```c
volatile bool event_flag = false;

void irq_handler(void *ctx)
{
    event_flag = true;  // Minimal work in ISR
}

int main(void)
{
    while (1) {
        if (event_flag) {
            event_flag = false;
            // Heavy processing in main loop
            process_data();
        }
    }
}
```

**Bad:**
```c
void irq_handler(void *ctx)
{
    // Too much work in ISR!
    process_complex_algorithm();  // SLOW
    write_to_flash();             // BLOCKING
}
```

### 2. Use Volatile for Shared Variables

```c
volatile bool data_ready = false;  // MUST be volatile
volatile uint32_t sample_count = 0;

void irq_handler(void *ctx)
{
    data_ready = true;
    sample_count++;
}
```

### 3. Protect Shared Data

```c
volatile uint32_t irq_count = 0;

void irq_handler(void *ctx)
{
    irq_count++;  // Modified in ISR
}

void print_stats(void)
{
    uint32_t local_copy;

    // Critical section for atomic read
    no_os_irq_global_disable(irq_ctrl);
    local_copy = irq_count;
    irq_count = 0;
    no_os_irq_global_enable(irq_ctrl);

    printf("Count: %u\n", local_copy);
}
```

### 4. Clear Level-Triggered Interrupts

```c
void level_irq_handler(void *ctx)
{
    // MUST clear source for level-triggered interrupts!
    uint8_t status = read_status_register();  // Clears interrupt

    if (status & DATA_READY) {
        process_data();
    }
}
```

## Priority Guidelines

| Priority | Typical Use |
|----------|-------------|
| 0 (highest) | Critical data acquisition, DMA |
| 1-2 | Communication (UART, SPI, I2C) |
| 3-4 | Timers, ADC/DAC |
| 5+ (lowest) | User interface, buttons, LEDs |

Higher priority interrupts can preempt lower priority ones.

## Common Issues - Quick Fixes

| Issue | Common Causes | Quick Fix |
|-------|---------------|-----------|
| Interrupt never fires | Not enabled, callback not registered | Call `no_os_irq_enable()` and `no_os_irq_global_enable()` |
| | Wrong trigger mode | Check edge vs level, rising vs falling |
| | GPIO not configured | Set GPIO as input with correct pull resistor |
| Interrupt fires continuously | Level-triggered source not cleared | Read status register or clear interrupt flag in ISR |
| | Wrong trigger (LEVEL instead of EDGE) | Change to edge-triggered |
| Missed interrupts | ISR too long | Move processing to main loop, keep ISR short |
| | Priority too low | Increase priority for critical interrupts |
| Data corruption | Missing volatile keyword | Add `volatile` to shared variables |
| | No critical section | Use `global_disable/enable` around shared data |

**See**: `reference/troubleshooting.md` for complete diagnostic guide.

## ISR Rules (Critical!)

**NEVER do in ISR:**
- `no_os_mdelay()` / `no_os_udelay()` – Busy waiting
- `malloc()` / `free()` – Non-reentrant, slow
- `printf()` – Blocking I/O (debug only, remove in production)
- Complex calculations – Defer to main loop
- Long SPI/I2C transactions – Can be slow

**ALWAYS:**
- Keep ISRs short (< 10 microseconds ideal)
- Use `volatile` for shared variables
- Clear interrupt sources (level-triggered)
- Protect multi-byte shared data with critical sections
- Set appropriate priorities

## Official Documentation

For authoritative and up-to-date information about the no-OS Interrupt platform driver, refer to these official resources:

### Primary Interrupt Documentation
- **no-OS Interrupt Driver Documentation**: https://wiki.analog.com/resources/no-os/drivers/interrupt
  - Complete interrupt driver API reference
  - Platform-specific implementation details
  - Configuration examples and usage patterns
  - Trigger modes and priority configuration
  - Troubleshooting and debugging guidance

### Related Documentation
- **no-OS Build Guide**: https://wiki.analog.com/resources/no-os/build
  - How to build projects using interrupt drivers
  - Platform-specific build configurations

- **no-OS Driver Development Guide**: https://wiki.analog.com/resources/no-os/drivers-guide
  - General driver architecture and patterns
  - Best practices for interrupt-driven drivers
  - Event-driven programming patterns

- **no-OS GitHub Repository**: https://github.com/analogdevicesinc/no-OS
  - Source code for interrupt platform implementations
  - Example drivers using interrupts
  - Platform-specific IRQ code (`drivers/platform/[platform]/[platform]_irq.c`)

- **no-OS Wiki**: https://wiki.analog.com/resources/tools-software/uc-drivers/no-os
  - General no-OS framework documentation
  - Getting started guides

**When to consult**: Use the official interrupt driver documentation as the authoritative reference for API specifications, platform support, callback mechanisms, and interrupt configuration. This skill provides conceptual understanding and patterns; official docs provide precise specifications.

## Summary

The no-OS IRQ platform driver provides:
- **Event-driven programming** – Respond immediately to hardware events
- **Low latency** – Fast interrupt handling
- **Priority-based** – Critical interrupts preempt lower priority
- **Platform portability** – Works across all MCUs
- **Simple interface** – Register callback, configure, enable

**Key workflow:**
1. Initialize IRQ controller with `no_os_irq_ctrl_init()`
2. Register callback with `no_os_irq_register_callback()`
3. Configure trigger mode and priority
4. Enable specific IRQ and global interrupts
5. Handle event in callback (keep short!)
6. Protect shared data with global disable/enable

**Critical rules:**
- Keep ISRs short and fast (< 10 μs ideal)
- Use `volatile` for shared variables
- Clear interrupt sources (especially level-triggered)
- Never block in ISRs (no delays, no malloc)
- Set appropriate priorities for nested interrupts

**For detailed information**, use the Read tool to access reference documentation:
- `reference/platform-apis.md` – Porting to new platforms
- `reference/api-usage.md` – Complete usage examples
- `reference/interrupt-handling.md` – Detailed interrupt mechanisms
- `reference/best-practices.md` – ISR design guidelines
- `reference/troubleshooting.md` – Common issues and solutions
