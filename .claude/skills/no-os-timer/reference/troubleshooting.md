# Timer Troubleshooting Guide

This document provides solutions to common timer-related issues.

## Timer not counting

### Symptom
Counter value remains at 0 or doesn't increment.

### Causes and Solutions

**Start not called**
- Must call `no_os_timer_start()` after init
```c
no_os_timer_init(&timer_desc, &timer_init);
no_os_timer_start(timer_desc);  // Don't forget this!
```

**Counter not reset**
- Call `counter_set(0)` before starting
```c
no_os_timer_counter_set(timer_desc, 0);
no_os_timer_start(timer_desc);
```

**Wrong frequency**
- Verify freq_hz is correct for platform
- Check platform limitations
```c
uint32_t actual_freq;
no_os_timer_count_clk_get(timer_desc, &actual_freq);
printf("Requested: %u Hz, Actual: %u Hz\n", timer_init.freq_hz, actual_freq);
```

**Clock disabled**
- Check peripheral clock enabled in HAL
```c
// STM32 example: Verify timer clock enabled in CubeMX
// Maxim example: Check clock gating registers
```

**Interrupt conflict**
- Another peripheral using same timer
- Check timer ID availability
```c
// ADUCM3029: Timer 0 used by no-OS, use Timer 1+
struct no_os_timer_init_param timer_init = {
    .id = 1,  // Not 0!
    // ...
};
```

## Timing inaccurate

### Symptom
Timer period doesn't match expected calculation.

### Causes and Solutions

**Frequency mismatch**
- Verify actual vs. requested frequency
```c
uint32_t actual_freq;
no_os_timer_count_clk_get(timer_desc, &actual_freq);

double expected_period = (double)timer_init.ticks_count / timer_init.freq_hz;
double actual_period = (double)timer_init.ticks_count / actual_freq;

printf("Expected period: %.3f ms\n", expected_period * 1000.0);
printf("Actual period: %.3f ms\n", actual_period * 1000.0);
```

**Tick calculation wrong**
- Verify: Period = ticks_count / freq_hz
```c
// Example: 100 ms period
// freq_hz = 10000 (10 kHz)
// ticks_count = 1000
// Period = 1000 / 10000 = 0.1 s = 100 ms ✓

// Wrong calculation:
// freq_hz = 1000
// ticks_count = 1000  
// Period = 1000 / 1000 = 1 s = 1000 ms ✗ (10x error!)
```

**Platform limitations**
- Some platforms have fixed frequency steps
```c
// ADUCM3029: Clock derived from PCLK with dividers
// May not achieve exact requested frequency
// Solution: Accept nearest available frequency
```

**CPU overload**
- Interrupt latency causes jitter
- Reduce interrupt handler complexity
- Increase interrupt priority
```c
// Keep timer ISR minimal
void timer_callback(void *context)
{
    flag = true;  // Set flag only
    // Don't do heavy processing here!
}
```

**Prescaler wrong**
- Check platform clock divider settings
```c
// STM32: Verify CubeMX prescaler configuration
// Maxim: Check timer prescaler register
```

## Interrupt not firing

### Symptom
Timer callback never executes.

### Causes and Solutions

**Interrupt not enabled**
- Call `no_os_irq_enable()`
```c
no_os_irq_register_callback(irq_desc, TIMER_IRQ_ID, &irq_cb);
no_os_irq_enable(irq_desc, TIMER_IRQ_ID);  // Must enable!
```

**Callback not registered**
- Call `no_os_irq_register_callback()`
```c
struct no_os_callback_desc irq_cb = {
    .callback = timer_callback,
    .ctx = NULL,
    .event = NO_OS_EVT_TIM_ELAPSED,
    .peripheral = NO_OS_TIM_IRQ,
    .handle = &htim13,
};

no_os_irq_register_callback(irq_desc, TIMER_IRQ_ID, &irq_cb);
```

**IRQ ID wrong**
- Verify correct IRQ number for platform
```c
// STM32: Check interrupt vector table
// Maxim: Verify timer IRQ number in datasheet
```

**Timer stopped**
- Must call `start()` for interrupts
```c
no_os_timer_start(timer_desc);  // Enables counting and interrupts
```

**IRQ handler issues**
- Check interrupt controller configuration
```c
// Verify IRQ controller initialized
struct no_os_irq_init_param irq_init = {
    .irq_ctrl_id = 0,
    .platform_ops = &platform_irq_ops,
};

struct no_os_irq_ctrl_desc *irq_desc;
int ret = no_os_irq_ctrl_init(&irq_desc, &irq_init);
if (ret) {
    printf("IRQ init failed: %d\n", ret);
}
```

**Interrupt priority**
- Lower priority interrupts may be blocked
```c
// Increase timer interrupt priority
// Platform-specific configuration
```

## Counter value unexpected

### Symptom
Counter reads show unexpected values.

### Causes and Solutions

**Counter should be < ticks_count**
- If not, hardware auto-reloads
```c
uint32_t count;
no_os_timer_counter_get(timer_desc, &count);

if (count >= timer_init.ticks_count) {
    printf("WARNING: Counter overflow! count=%u, max=%u\n",
           count, timer_init.ticks_count);
}
```

**Direction platform-dependent**
- Some count up, some down
```c
// Counting up (most platforms):
// 0 → 1 → 2 → ... → (ticks_count-1) → 0

// Counting down (some platforms):
// ticks_count → ... → 2 → 1 → 0 → ticks_count
```

**Counter_set failed**
- Value must be < ticks_count
```c
int ret = no_os_timer_counter_set(timer_desc, new_val);
if (ret) {
    printf("Counter_set failed: %d\n", ret);
    printf("Value: %u, Max: %u\n", new_val, timer_init.ticks_count);
}
```

**Reading during transition**
- Timing races on counter reads
```c
// Read multiple times and compare
uint32_t count1, count2;
no_os_timer_counter_get(timer_desc, &count1);
no_os_timer_counter_get(timer_desc, &count2);

if (count2 < count1) {
    printf("Counter wrapped between reads\n");
}
```

## High CPU usage

### Symptom
High CPU utilization when using timers.

### Causes and Solutions

**Polling too fast**
- Add small delay between reads
```c
// BAD: Tight polling loop
while (1) {
    no_os_timer_counter_get(timer_desc, &count);
    if (count >= target)
        break;
}

// GOOD: Add delay between polls
while (1) {
    no_os_timer_counter_get(timer_desc, &count);
    if (count >= target)
        break;
    no_os_udelay(10);  // Small delay
}
```

**ISR taking too long**
- Keep interrupt handler short
```c
// BAD: Heavy processing in ISR
void timer_callback(void *context)
{
    process_data();      // Takes 10 ms!
    calculate_results(); // Takes 5 ms!
    update_display();    // Takes 3 ms!
}

// GOOD: Minimal ISR, defer processing
void timer_callback(void *context)
{
    data_ready = true;  // Just set flag
}

// Process in main loop
while (1) {
    if (data_ready) {
        data_ready = false;
        process_data();
        calculate_results();
        update_display();
    }
}
```

**Timer interrupts too frequent**
- Increase ticks_count
```c
// BAD: Interrupt every 100 µs (10 kHz rate)
struct no_os_timer_init_param timer_init = {
    .freq_hz = 100000,
    .ticks_count = 10,  // Too frequent!
};

// GOOD: Interrupt every 1 ms (1 kHz rate)
struct no_os_timer_init_param timer_init = {
    .freq_hz = 100000,
    .ticks_count = 100,  // More reasonable
};
```

**Multiple timers busy**
- Consolidate tasks
```c
// Consider using single timer with multiple tasks
void timer_callback(void *context)
{
    static uint32_t tick_count = 0;
    tick_count++;
    
    // Fast task: every tick (1 ms)
    fast_task();
    
    // Slow task: every 100 ticks (100 ms)
    if (tick_count % 100 == 0)
        slow_task();
    
    // Very slow task: every 1000 ticks (1 s)
    if (tick_count % 1000 == 0)
        very_slow_task();
}
```

## Platform-Specific Issues

### ADUCM3029

**Issue:** Can't set exact frequency
```c
// Solution: Accept nearest available frequency
struct aducm_timer_init_param aducm_extra = {
    .source_freq = PCLK_DIV256,  // Fixed divider
};

// Verify actual frequency
uint32_t actual_freq;
no_os_timer_count_clk_get(timer_desc, &actual_freq);
```

**Issue:** Timer 0 already in use
```c
// Solution: Use Timer 1 or higher
struct no_os_timer_init_param timer_init = {
    .id = 1,  // Timer 0 reserved by no-OS
    // ...
};
```

### STM32

**Issue:** HAL handle not configured
```c
// Solution: Configure timer in CubeMX, include generated code
extern TIM_HandleTypeDef htim13;

struct stm32_timer_init_param stm32_extra = {
    .htimer = &htim13,  // From CubeMX
};
```

**Issue:** Clock not enabled
```c
// Solution: Enable timer clock in CubeMX
// System Core → RCC → Enable TIMx clock
```

### Maxim

**Issue:** Timer conflicts with other peripherals
```c
// Solution: Check timer availability in datasheet
// Some timers shared with other functions (PWM, capture)
```

### Pico

**Issue:** Limited number of timers (4 alarms)
```c
// Solution: Share alarms or use alternate timing methods
// Consider using hardware PWM or PIO for some tasks
```

## Debugging Techniques

### Add debug prints

```c
int ret = no_os_timer_init(&timer_desc, &timer_init);
printf("Timer init: ret=%d\n", ret);

ret = no_os_timer_start(timer_desc);
printf("Timer start: ret=%d\n", ret);

uint32_t count;
no_os_timer_counter_get(timer_desc, &count);
printf("Counter: %u / %u\n", count, timer_init.ticks_count);

uint32_t freq;
no_os_timer_count_clk_get(timer_desc, &freq);
printf("Frequency: %u Hz (requested %u Hz)\n", freq, timer_init.freq_hz);
```

### Measure actual timing

```c
// Use GPIO toggle to measure with oscilloscope
void timer_callback(void *context)
{
    static bool state = false;
    state = !state;
    no_os_gpio_set_value(debug_gpio, state);  // Measure with scope
}
```

### Verify register values (platform-specific)

```c
// Maxim example: Check timer registers
printf("Timer CNT: 0x%08X\n", MXC_TMR_GET_IDX(timer_id)->cnt);
printf("Timer CMP: 0x%08X\n", MXC_TMR_GET_IDX(timer_id)->cmp);
printf("Timer CTRL: 0x%08X\n", MXC_TMR_GET_IDX(timer_id)->ctrl);
```

### Check interrupt firing

```c
// Add counter in ISR
volatile uint32_t isr_count = 0;

void timer_callback(void *context)
{
    isr_count++;
}

// Monitor in main loop
uint32_t last_count = 0;
while (1) {
    if (isr_count != last_count) {
        printf("ISR fired: count=%u\n", isr_count);
        last_count = isr_count;
    }
    no_os_mdelay(1000);
}
```
