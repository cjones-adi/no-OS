# Platform API Implementations

This document covers platform-specific timer implementations and how to port the timer driver to new platforms.

## Supported Platforms

| Platform | Notes | Max Frequency | Multi-Timer |
|----------|-------|---------------|-------------|
| Maxim | No extra params needed | 32 MHz | Yes (multiple TMRx) |
| STM32 | Requires HAL handle from CubeMX | 160+ MHz | Yes (multiple TIMx) |
| ADUCM3029 | Fixed freq steps (PCLK dividers) | ~26 MHz | Yes (Timer 1 available) |
| Mbed | Limited support, object-based | Platform dependent | Limited |
| Pico | Alarm-based timers | 125 MHz | Yes (4 alarms) |
| Xilinx | Programmable logic timer core | 100+ MHz | Yes |

## Platform-Specific Initialization

### Platform-Specific Extras - ADUCM3029

```c
// ADUCM3029 requires clock source selection
#include "aducm3029_timer.h"

struct aducm_timer_init_param aducm_extra = {
    .source_freq = PCLK_DIV256,  // Peripherial clock / 256
};

struct no_os_timer_init_param timer_init = {
    .id = 1,                        // Timer 1 (Timer 0 used by no-OS)
    .freq_hz = 10000,               // Desired frequency (actual may differ)
    .ticks_count = 1000,
    .extra = &aducm_extra,          // Platform-specific
    .platform_ops = &aducm3029_timer_ops,
};

no_os_timer_init(&timer_desc, &timer_init);
```

### Platform-Specific Extras - STM32

```c
// STM32 requires HAL timer handle from CubeMX
#include "stm32_timer.h"

// htim13 defined in STM32 CubeMX generated code
extern TIM_HandleTypeDef htim13;

struct stm32_timer_init_param stm32_extra = {
    .htimer = &htim13,              // HAL timer handle
};

struct no_os_timer_init_param timer_init = {
    .id = 0,
    .freq_hz = 100000,              // 100 kHz
    .ticks_count = 10000,           // 100 ms period
    .extra = &stm32_extra,          // Platform-specific
    .platform_ops = &stm32_timer_ops,
};

no_os_timer_init(&timer_desc, &timer_init);
```

## Porting to New Platforms

### Step 1: Create Platform Files

```
drivers/platform/myplatform/
├── myplatform_timer.c      # Implementation
└── myplatform_timer.h      # Platform extras
```

### Step 2: Define Platform Extras (if needed)

In `myplatform_timer.h`:

```c
#ifndef _MYPLATFORM_TIMER_H_
#define _MYPLATFORM_TIMER_H_

struct myplatform_timer_init_param {
    uint32_t clock_source;     // Clock source selection
    uint8_t prescaler;         // Clock divider
    // ... other platform specifics
};

struct myplatform_timer_desc {
    void *hw_timer;            // Hardware timer instance
    uint64_t last_time_ns;     // For elapsed time tracking
    bool started;
    // ... other platform-specific fields
};

#endif
```

### Step 3: Implement Platform Operations

In `myplatform_timer.c`:

```c
#include "no_os_timer.h"
#include "myplatform_timer.h"

int32_t myplatform_timer_init(struct no_os_timer_desc **desc,
                               const struct no_os_timer_init_param *param)
{
    // 1. Allocate descriptor
    *desc = calloc(1, sizeof(**desc));
    if (!*desc)
        return -ENOMEM;

    // 2. Allocate platform-specific extra
    struct myplatform_timer_desc *extra = calloc(1, sizeof(*extra));
    if (!extra) {
        free(*desc);
        return -ENOMEM;
    }

    // 3. Configure timer using vendor HAL
    // Example: HAL_TIMER_SetFrequency(freq_hz);
    // Example: HAL_TIMER_SetPeriod(ticks_count);

    // 4. Copy parameters
    (*desc)->id = param->id;
    (*desc)->freq_hz = param->freq_hz;
    (*desc)->ticks_count = param->ticks_count;
    (*desc)->extra = extra;

    return 0;
}

int32_t myplatform_timer_start(struct no_os_timer_desc *desc)
{
    if (!desc)
        return -EINVAL;

    // Example: HAL_TIMER_Enable(desc->id);
    struct myplatform_timer_desc *extra = desc->extra;
    extra->started = true;

    return 0;
}

int32_t myplatform_timer_stop(struct no_os_timer_desc *desc)
{
    if (!desc)
        return -EINVAL;

    // Example: HAL_TIMER_Disable(desc->id);
    struct myplatform_timer_desc *extra = desc->extra;
    extra->started = false;

    return 0;
}

int32_t myplatform_timer_counter_get(struct no_os_timer_desc *desc,
                                      uint32_t *counter)
{
    if (!desc || !counter)
        return -EINVAL;

    // Example: *counter = HAL_TIMER_GetCounter(desc->id);
    return 0;
}

int32_t myplatform_timer_counter_set(struct no_os_timer_desc *desc,
                                      uint32_t new_val)
{
    if (!desc)
        return -EINVAL;

    if (new_val >= desc->ticks_count)
        return -EINVAL;

    // Example: HAL_TIMER_SetCounter(desc->id, new_val);
    return 0;
}

int32_t myplatform_timer_count_clk_get(struct no_os_timer_desc *desc,
                                        uint32_t *freq_hz)
{
    if (!desc || !freq_hz)
        return -EINVAL;

    *freq_hz = desc->freq_hz;
    return 0;
}

int32_t myplatform_timer_count_clk_set(struct no_os_timer_desc *desc,
                                        uint32_t freq_hz)
{
    if (!desc)
        return -EINVAL;

    // Example: HAL_TIMER_SetFrequency(freq_hz);
    desc->freq_hz = freq_hz;

    return 0;
}

int32_t myplatform_timer_get_elapsed_time_nsec(struct no_os_timer_desc *desc,
                                                uint64_t *elapsed_time)
{
    if (!desc || !elapsed_time)
        return -EINVAL;

    struct myplatform_timer_desc *extra = desc->extra;
    uint32_t count;
    myplatform_timer_counter_get(desc, &count);

    uint64_t time_ns = ((uint64_t)count * 1000000000) / desc->freq_hz;
    *elapsed_time = time_ns - extra->last_time_ns;

    return 0;
}

int32_t myplatform_timer_remove(struct no_os_timer_desc *desc)
{
    if (!desc)
        return -EINVAL;

    // Disable timer
    // Example: HAL_TIMER_Disable(desc->id);

    free(desc->extra);
    free(desc);
    return 0;
}
```

### Step 4: Define Platform Ops

```c
const struct no_os_timer_platform_ops myplatform_timer_ops = {
    .init = &myplatform_timer_init,
    .start = &myplatform_timer_start,
    .stop = &myplatform_timer_stop,
    .counter_get = &myplatform_timer_counter_get,
    .counter_set = &myplatform_timer_counter_set,
    .count_clk_get = &myplatform_timer_count_clk_get,
    .count_clk_set = &myplatform_timer_count_clk_set,
    .get_elapsed_time_nsec = &myplatform_timer_get_elapsed_time_nsec,
    .remove = &myplatform_timer_remove,
};
```
