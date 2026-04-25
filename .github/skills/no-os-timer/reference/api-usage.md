# Timer API Usage Patterns

This document provides detailed usage patterns and examples for common timer operations.

## Timer Operations

### 1. Start and Stop

**Start Timer:**
```c
int32_t no_os_timer_start(struct no_os_timer_desc *desc);
```

Starts the timer counting at the configured frequency.

```c
ret = no_os_timer_start(timer_desc);
if (ret) {
    printf("Start failed: %d\n", ret);
    return ret;
}
// Timer now counting
```

**Stop Timer:**
```c
int32_t no_os_timer_stop(struct no_os_timer_desc *desc);
```

Stops the timer (pauses counting).

```c
ret = no_os_timer_stop(timer_desc);
if (ret)
    return ret;
// Timer paused
```

### 2. Counter Management

**Get Current Counter Value:**
```c
int32_t no_os_timer_counter_get(struct no_os_timer_desc *desc,
                                 uint32_t *counter);
```

Reads the current count value (0 to ticks_count-1).

```c
uint32_t count;
ret = no_os_timer_counter_get(timer_desc, &count);
if (ret)
    return ret;

printf("Current count: %u\n", count);

// Example: Wait for specific count
uint32_t target_count = 100;  // 10 ms delay at 10 kHz
do {
    no_os_timer_counter_get(timer_desc, &count);
} while (count < target_count);
```

**Set Counter Value:**
```c
int32_t no_os_timer_counter_set(struct no_os_timer_desc *desc,
                                 uint32_t new_val);
```

Sets counter to specific value (must be < ticks_count).

```c
// Reset counter to 0
ret = no_os_timer_counter_set(timer_desc, 0);
if (ret)
    return ret;

// Start from specific value (countdown)
ret = no_os_timer_counter_set(timer_desc, 500);  // Start at 500
```

### 3. Frequency Management

**Get Timer Frequency:**
```c
int32_t no_os_timer_count_clk_get(struct no_os_timer_desc *desc,
                                  uint32_t *freq_hz);
```

Reads the actual timer clock frequency.

```c
uint32_t freq;
ret = no_os_timer_count_clk_get(timer_desc, &freq);
if (ret)
    return ret;

printf("Timer frequency: %u Hz\n", freq);
printf("Period per tick: %.2f µs\n", 1000000.0 / freq);
```

**Set Timer Frequency:**
```c
int32_t no_os_timer_count_clk_set(struct no_os_timer_desc *desc,
                                  uint32_t freq_hz);
```

Changes the counting frequency dynamically.

```c
// Change to 100 kHz
ret = no_os_timer_count_clk_set(timer_desc, 100000);
if (ret)
    return ret;

// Note: Some platforms (ADUCM) don't support dynamic frequency changes
```

### 4. Elapsed Time Measurement

**Get Elapsed Time in Nanoseconds:**
```c
int32_t no_os_timer_get_elapsed_time_nsec(struct no_os_timer_desc *desc,
                                            uint64_t *elapsed_time);
```

Measures time since timer initialization (in nanoseconds).

```c
uint64_t elapsed_ns;
ret = no_os_timer_get_elapsed_time_nsec(timer_desc, &elapsed_ns);
if (ret)
    return ret;

double elapsed_ms = elapsed_ns / 1000000.0;
printf("Elapsed: %.3f ms\n", elapsed_ms);
```

## Common Timer Patterns

### Pattern 1: Hardware-Based Delay

```c
struct no_os_timer_desc *timer_desc;

// Initialize 10 kHz timer (0.1 ms per tick)
struct no_os_timer_init_param timer_init = {
    .id = 0,
    .freq_hz = 10000,
    .ticks_count = 10000,  // 1 second max
    .platform_ops = &max_timer_ops,
};

no_os_timer_init(&timer_desc, &timer_init);

// Function to delay N milliseconds
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

### Pattern 2: Periodic Interrupt (IIO Trigger)

```c
// Initialize timer with interrupt
struct no_os_timer_init_param timer_init = {
    .id = 0,
    .freq_hz = 1000,                      // 1 kHz = 1 ms per tick
    .ticks_count = 100,                   // 100 ms period
    .platform_ops = &stm32_timer_ops,
    .extra = &stm32_timer_extra,
};

struct no_os_timer_desc *timer_desc;
no_os_timer_init(&timer_desc, &timer_init);

// Setup IRQ for timer interrupt
struct no_os_irq_init_param irq_init = {
    .irq_ctrl_id = 0,
    .platform_ops = &stm32_irq_ops,
};

struct no_os_irq_ctrl_desc *irq_desc;
no_os_irq_ctrl_init(&irq_desc, &irq_init);

// Register callback (fires every 100 ms)
void timer_callback(void *context)
{
    // This runs every 100 ms
    sensor_read_callback();
}

struct no_os_callback_desc irq_cb = {
    .callback = timer_callback,
    .ctx = NULL,
    .event = NO_OS_EVT_TIM_ELAPSED,
    .peripheral = NO_OS_TIM_IRQ,
    .handle = &htim13,
};

no_os_irq_register_callback(irq_desc, TIMER_IRQ_ID, &irq_cb);
no_os_irq_enable(irq_desc, TIMER_IRQ_ID);

// Start timer (interrupts now firing)
no_os_timer_start(timer_desc);
```

### Pattern 3: Time Measurement

```c
struct no_os_timer_desc *timer_desc;

// Initialize high-frequency timer for precise measurement
struct no_os_timer_init_param timer_init = {
    .id = 2,
    .freq_hz = 1000000,              // 1 MHz = 1 µs per tick
    .ticks_count = 0xFFFFFFFF,       // Large count
    .platform_ops = &max_timer_ops,
};

no_os_timer_init(&timer_desc, &timer_init);
no_os_timer_start(timer_desc);

// Measure function execution time
uint64_t elapsed_start;
no_os_timer_get_elapsed_time_nsec(timer_desc, &elapsed_start);

// Do something...
slow_function();

uint64_t elapsed_end;
no_os_timer_get_elapsed_time_nsec(timer_desc, &elapsed_end);

uint64_t duration_ns = elapsed_end - elapsed_start;
printf("Function took %.3f µs\n", duration_ns / 1000.0);
```

### Pattern 4: Configurable Sample Rate

```c
struct no_os_timer_desc *timer_desc;
uint32_t sample_rate_hz = 1000;  // 1 kHz

struct no_os_timer_init_param timer_init = {
    .id = 0,
    .freq_hz = 100000,              // Base 100 kHz
    .ticks_count = 100000 / sample_rate_hz,  // Divider
    .platform_ops = &max_timer_ops,
};

no_os_timer_init(&timer_desc, &timer_init);
// Interrupt fires at sample_rate_hz

// Change sample rate dynamically
void set_sample_rate(struct no_os_timer_desc *timer, uint32_t rate_hz)
{
    uint32_t new_ticks = 100000 / rate_hz;
    // Counter will auto-reload with new period
    printf("Sample rate set to %u Hz\n", rate_hz);
}
```

### Pattern 5: Multiple Timers for Different Tasks

```c
struct no_os_timer_desc *timer_fast;   // 1 kHz sensor sampling
struct no_os_timer_desc *timer_slow;   // 100 ms status update
struct no_os_timer_desc *timer_measure; // µs resolution timing

// Fast sampling (1000 Hz)
struct no_os_timer_init_param timer_fast_init = {
    .id = 0,
    .freq_hz = 100000,
    .ticks_count = 100,
    .platform_ops = &max_timer_ops,
};

// Slow update (10 Hz)
struct no_os_timer_init_param timer_slow_init = {
    .id = 1,
    .freq_hz = 100,
    .ticks_count = 10,
    .platform_ops = &max_timer_ops,
};

// Measurement (1 MHz)
struct no_os_timer_init_param timer_measure_init = {
    .id = 2,
    .freq_hz = 1000000,
    .ticks_count = 0xFFFFFFFF,
    .platform_ops = &max_timer_ops,
};

no_os_timer_init(&timer_fast, &timer_fast_init);
no_os_timer_init(&timer_slow, &timer_slow_init);
no_os_timer_init(&timer_measure, &timer_measure_init);

no_os_timer_start(timer_fast);
no_os_timer_start(timer_slow);
no_os_timer_start(timer_measure);
```
