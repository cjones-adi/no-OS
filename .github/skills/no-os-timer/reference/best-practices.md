# Timer Best Practices

This document provides guidelines for effective timer usage in no-OS embedded systems.

## Best Practices

1. **Always initialize before use** - Call `no_os_timer_init()` with proper parameters

2. **Choose appropriate frequency** - Match resolution needed (1 MHz for µs, 1 kHz for ms)

3. **Reset counter before use** - Set to 0 with `counter_set()` before starting

4. **Start after configuration** - Call `no_os_timer_start()` when ready

5. **Stop when done** - Call `no_os_timer_stop()` to save power

6. **Verify tick calculations** - Double-check period = ticks_count / freq_hz

7. **Use timer 0 sparingly** - Often reserved for system delays

8. **Handle platform differences** - Some platforms (e.g., ADUCM) have fixed frequencies

9. **Poll frequently in delays** - Avoid long polling intervals

10. **Check return values** - Verify all operations succeed

11. **Free resources** - Call `no_os_timer_remove()` on cleanup

12. **Use for accurate timing** - Hardware timers more reliable than software

13. **Consider IIO triggers** - Use timers with IIO for data acquisition

14. **Document timer assignments** - Track which timer for which task

15. **Test on target platform** - Verify frequency accuracy

## Timer Selection Strategy

### When to use which timer

**Timer 0:**
- Often reserved for system delays (no_os_mdelay, no_os_udelay)
- Avoid using unless necessary
- Check platform documentation

**Timer 1+:**
- Application-specific timing
- Data acquisition triggers
- Measurement and profiling
- PWM generation

### Frequency Selection

**Low frequency (1-10 kHz):**
- General timing (seconds, milliseconds)
- Low-rate sampling (< 100 Hz)
- Status updates
- User interface timing

**Medium frequency (10-100 kHz):**
- Moderate precision timing
- Sensor sampling (100 Hz - 10 kHz)
- Control loops
- PWM generation

**High frequency (100 kHz - 1 MHz):**
- Precise timing measurements
- High-speed data acquisition
- Performance profiling
- Communication protocols

**Very high frequency (> 1 MHz):**
- Microsecond/nanosecond measurements
- Ultra-precise timing
- High-speed triggers
- May not be available on all platforms

## Common Patterns and Anti-Patterns

### Good Pattern: Resource Management

```c
struct no_os_timer_desc *timer_desc = NULL;

// Initialize
int ret = no_os_timer_init(&timer_desc, &timer_init);
if (ret)
    return ret;

// Use timer
no_os_timer_start(timer_desc);
// ... do work ...
no_os_timer_stop(timer_desc);

// Always cleanup
no_os_timer_remove(timer_desc);
timer_desc = NULL;
```

### Anti-Pattern: Forgetting to Start

```c
// BAD: Initialized but never started
no_os_timer_init(&timer_desc, &timer_init);
no_os_timer_counter_get(timer_desc, &count);  // Counter not incrementing!
```

### Good Pattern: Error Handling

```c
int ret = no_os_timer_init(&timer_desc, &timer_init);
if (ret) {
    printf("Timer init failed: %d\n", ret);
    return ret;
}

ret = no_os_timer_start(timer_desc);
if (ret) {
    printf("Timer start failed: %d\n", ret);
    no_os_timer_remove(timer_desc);
    return ret;
}
```

### Good Pattern: Period Calculation Verification

```c
// Calculate expected period
uint32_t freq_hz = 10000;      // 10 kHz
uint32_t ticks_count = 1000;   // 1000 ticks
double period_s = (double)ticks_count / freq_hz;

printf("Timer period: %.3f ms\n", period_s * 1000.0);
// Output: Timer period: 100.000 ms

// Verify matches requirements
assert(period_s == 0.1);  // 100 ms = 0.1 seconds
```

### Anti-Pattern: Assuming Exact Frequency

```c
// BAD: Some platforms (ADUCM) can't achieve exact frequency
struct no_os_timer_init_param timer_init = {
    .freq_hz = 12345,  // May be adjusted to nearest achievable
};

// GOOD: Verify actual frequency
no_os_timer_init(&timer_desc, &timer_init);
uint32_t actual_freq;
no_os_timer_count_clk_get(timer_desc, &actual_freq);
printf("Requested: %u Hz, Actual: %u Hz\n", 12345, actual_freq);
```

### Good Pattern: Multiple Timer Coordination

```c
// Different timers for different purposes
struct no_os_timer_desc *timer_sampling;  // High-rate sampling
struct no_os_timer_desc *timer_status;    // Low-rate status
struct no_os_timer_desc *timer_measure;   // Performance measurement

// Initialize all
no_os_timer_init(&timer_sampling, &sampling_init);
no_os_timer_init(&timer_status, &status_init);
no_os_timer_init(&timer_measure, &measure_init);

// Start in order
no_os_timer_start(timer_sampling);
no_os_timer_start(timer_status);
no_os_timer_start(timer_measure);

// Cleanup in reverse order
no_os_timer_stop(timer_measure);
no_os_timer_stop(timer_status);
no_os_timer_stop(timer_sampling);

no_os_timer_remove(timer_measure);
no_os_timer_remove(timer_status);
no_os_timer_remove(timer_sampling);
```

## Power Management

### Stop timers when not needed

```c
// Before entering low-power mode
no_os_timer_stop(timer_desc);

// Enter low-power mode
enter_sleep_mode();

// After waking up
no_os_timer_start(timer_desc);
```

### Use lowest frequency that meets requirements

```c
// BAD: Unnecessarily high frequency
.freq_hz = 1000000,  // 1 MHz for millisecond timing

// GOOD: Match frequency to precision needed
.freq_hz = 10000,    // 10 kHz sufficient for millisecond timing
```

## Interrupt-Based Timing

### Keep ISR handlers short

```c
void timer_callback(void *context)
{
    // GOOD: Set flag, do minimal work
    data_ready_flag = true;
    
    // BAD: Don't do heavy processing in ISR
    // process_sensor_data();  // Wrong!
}

// Main loop processes flag
while (1) {
    if (data_ready_flag) {
        data_ready_flag = false;
        process_sensor_data();
    }
}
```

### Avoid nested timer interrupts

```c
// Configure interrupt priority to prevent nesting
struct no_os_irq_init_param irq_init = {
    .irq_ctrl_id = 0,
    .platform_ops = &platform_irq_ops,
    .extra = &irq_extra,  // Set appropriate priority
};
```

## Testing and Validation

### Verify timer accuracy on target hardware

```c
// Measure actual timer period
no_os_timer_start(timer_desc);
uint64_t start_time, end_time;

no_os_timer_get_elapsed_time_nsec(timer_desc, &start_time);
no_os_mdelay(1000);  // Wait 1 second
no_os_timer_get_elapsed_time_nsec(timer_desc, &end_time);

uint64_t actual_ns = end_time - start_time;
printf("Expected: 1000000000 ns, Actual: %llu ns\n", actual_ns);
printf("Error: %.2f%%\n", ((double)actual_ns / 1000000000.0 - 1.0) * 100.0);
```

### Test edge cases

```c
// Test maximum tick count
uint32_t max_ticks = 0xFFFFFFFF;
no_os_timer_counter_set(timer_desc, max_ticks - 10);
// Verify auto-reload works

// Test minimum frequency
no_os_timer_count_clk_set(timer_desc, 1);
// Verify still functions

// Test counter wrap-around
uint32_t count;
no_os_timer_counter_get(timer_desc, &count);
// Verify count < ticks_count always true
```

## Documentation

### Document timer usage in code

```c
/**
 * @brief Timer allocation for MyDevice driver
 * 
 * Timer 0: Reserved by no-OS for system delays
 * Timer 1: Data acquisition sampling (1 kHz)
 * Timer 2: Status LED blink (1 Hz)
 * Timer 3: Performance profiling (1 MHz)
 */
```

### Comment non-obvious configurations

```c
// ADUCM3029: Timer 0 used by no-OS mdelay, must use Timer 1+
struct no_os_timer_init_param timer_init = {
    .id = 1,  // Not 0!
    .freq_hz = 10000,
    .ticks_count = 1000,
    .extra = &aducm_extra,
    .platform_ops = &aducm3029_timer_ops,
};

// STM32: Using TIM13 configured in CubeMX
// Clock: 80 MHz APB1
// Prescaler: 800-1 (100 kHz)
// Period: 1000-1 (10 Hz)
```
