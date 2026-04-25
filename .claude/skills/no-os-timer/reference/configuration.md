# Timer Configuration

This document covers timer initialization, configuration, and key concepts.

## Core Data Structures

### 1. no_os_timer_init_param - Initialization Parameters

```c
struct no_os_timer_init_param {
    uint16_t id;                    // Timer ID (0, 1, 2, etc.)
    uint32_t freq_hz;               // Count frequency in Hz
    uint32_t ticks_count;           // Ticks until auto-reload
    const struct no_os_timer_platform_ops *platform_ops;
    void *extra;                    // Platform-specific parameters
};
```

**Parameters:**
- **id** - Unique timer identifier (platform-dependent, e.g., 0=TMR0, 1=TMR1)
- **freq_hz** - Counting frequency in Hertz (10Hz to 100MHz depending on platform)
- **ticks_count** - Number of ticks before counter resets (auto-reload value)
- **platform_ops** - Pointer to platform-specific function implementations
- **extra** - Platform-specific initialization (e.g., clock source selection, output pins)

### 2. no_os_timer_desc - Runtime Descriptor

```c
struct no_os_timer_desc {
    void *mutex;                    // Thread safety lock
    uint16_t id;                    // Timer ID
    uint32_t freq_hz;               // Configured frequency
    uint32_t ticks_count;           // Configured tick count
    const struct no_os_timer_platform_ops *platform_ops;
    void *extra;                    // Platform-specific data
};
```

### 3. no_os_timer_platform_ops - Platform Function Pointers

```c
struct no_os_timer_platform_ops {
    // Initialization and cleanup
    int32_t (*init)(struct no_os_timer_desc **,
                    const struct no_os_timer_init_param *);
    int32_t (*remove)(struct no_os_timer_desc *);

    // Timer control
    int32_t (*start)(struct no_os_timer_desc *);
    int32_t (*stop)(struct no_os_timer_desc *);

    // Counter management
    int32_t (*counter_get)(struct no_os_timer_desc *, uint32_t *);
    int32_t (*counter_set)(struct no_os_timer_desc *, uint32_t);

    // Frequency management
    int32_t (*count_clk_get)(struct no_os_timer_desc *, uint32_t *);
    int32_t (*count_clk_set)(struct no_os_timer_desc *, uint32_t);

    // Time measurement
    int32_t (*get_elapsed_time_nsec)(struct no_os_timer_desc *, uint64_t *);
};
```

## Timer Concepts

### Frequency vs. Ticks

**Frequency (freq_hz):** The timer clock speed in Hertz
- 10,000 Hz = Each tick is 0.1 ms
- 100,000 Hz = Each tick is 10 µs
- 1,000,000 Hz = Each tick is 1 µs

**Ticks Count (ticks_count):** The number of ticks before auto-reload
- Timer counts: 0 → 1 → 2 → ... → (ticks_count-1) → 0 → 1 → ...
- Counts up or down depending on platform

**Period Calculation:**
```
Period (seconds) = ticks_count / freq_hz
Example: ticks_count=1000, freq_hz=10000 → 1000/10000 = 0.1 seconds = 100ms
```

### Timer Modes

**Counting Up (most common):**
- Starts at 0
- Counts: 0, 1, 2, ..., ticks_count-1, 0, 1, ...
- Interrupts when reaches ticks_count (auto-reloads)

**Counting Down (some platforms):**
- Starts at ticks_count
- Counts down to 0, then reloads
- Useful for countdown timers

## Timer Initialization Workflow

### Basic Timer - Delays Only

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

// Now ready to use for delays or measurements
// ...

// Cleanup
no_os_timer_remove(timer_desc);
```

## Configuration Reference Tables

### Frequency Selection Guide

| Frequency | Tick Period | Use Case |
|-----------|------------|----------|
| 1,000 Hz | 1 ms | General purpose timing |
| 10,000 Hz | 100 µs | Moderate precision |
| 100,000 Hz | 10 µs | High precision timing |
| 1,000,000 Hz | 1 µs | Very precise measurement |
| 10,000,000 Hz | 100 ns | Ultra-precise timing |

### Tick Count Selection Guide

| Tick Count | Purpose |
|-----------|---------|
| 1,000 | ~1 second @ 1000 Hz |
| 10,000 | ~10 seconds @ 1000 Hz |
| 100,000 | ~1.6 minutes @ 1000 Hz |
| 1,000,000 | ~16 minutes @ 1000 Hz |
| 0xFFFFFFFF | Very long periods (32-bit limit) |

## Architecture Overview

```
┌──────────────────────────────────────────┐
│    User Application / Device Driver     │
│  (Platform-independent code)            │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │  no_os_timer.h      │  Platform-agnostic API
    │  (Generic)          │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────────────────┐
    │                                  │
┌───▼──────────┐        ┌──────────────▼───┐
│maxim_timer.c │        │   stm32_timer.c  │
│maxim_timer.h │        │   stm32_timer.h  │
└───┬──────────┘        └──────────┬───────┘
    │ (Optional IRQ)               │
    │ (Optional DMA)               │
    │                              │
┌───▼──────────┐        ┌──────────▼───────┐
│ Maxim HAL    │        │   STM32 HAL      │
│ (Vendor SDK) │        │   (Vendor SDK)   │
└──────────────┘        └──────────────────┘
```

## File Structure

### 1. no_os_timer.h - Platform-Agnostic Interface

Contains generic structures and function prototypes.

**Key components:**
- `no_os_timer_init_param` - Initialization parameters
- `no_os_timer_desc` - Runtime timer descriptor
- `no_os_timer_platform_ops` - Function pointers
- Timer API function declarations

### 2. Platform-Specific Implementation

**Examples:** `maxim_timer.c`, `stm32_timer.c`, `aducm3029_timer.c`, `pico_timer.c`

Platform-specific code interfacing with vendor HAL.

### 3. Platform-Specific Extras

**Examples:** `maxim_timer.h`, `stm32_timer.h`, `aducm3029_timer.h`

Platform-specific parameters (clock source, counter mode, etc.).
