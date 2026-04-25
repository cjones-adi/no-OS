# Best Practices for IRQ Programming

Guidelines for writing robust, maintainable interrupt handlers.

## ISR Design Principles

### 1. Keep ISRs Short and Fast

**Why:** Long ISRs cause:
- Missed interrupts from other sources
- Increased interrupt latency
- System responsiveness issues

**Good Practice:**
```c
volatile bool event_flag = false;

void irq_handler(void *ctx)
{
    // Minimal work in ISR
    event_flag = true;  // Set flag
}

int main(void)
{
    while (1) {
        if (event_flag) {
            event_flag = false;

            // Heavy processing in main loop
            process_complex_algorithm();
            write_to_flash();
            update_display();
        }
    }
}
```

**Bad Practice:**
```c
void irq_handler(void *ctx)
{
    // Too much work in ISR!
    process_complex_algorithm();  // SLOW
    write_to_flash();             // BLOCKING
    update_display();             // TIME-CONSUMING
}
```

### 2. No Blocking Operations in ISRs

**Never do in ISR:**
- `no_os_mdelay()` / `no_os_udelay()` – Busy waiting
- `malloc()` / `free()` – Non-reentrant, slow
- `printf()` – Blocking I/O (debug only, remove in production)
- SPI/I2C transactions – Can be slow
- Complex calculations – Defer to main loop

**Good Practice:**
```c
volatile bool read_sensor = false;

void data_ready_handler(void *ctx)
{
    read_sensor = true;  // Fast flag set
}

int main(void)
{
    while (1) {
        if (read_sensor) {
            read_sensor = false;

            // Blocking I/O in main loop
            read_sensor_data_spi();
            process_samples();
        }
    }
}
```

### 3. Use Volatile for Shared Variables

**Why:** Compiler optimizes away reads if not volatile

**Correct:**
```c
volatile bool data_ready = false;
volatile uint32_t sample_count = 0;

void irq_handler(void *ctx)
{
    data_ready = true;
    sample_count++;
}

int main(void)
{
    while (1) {
        if (data_ready) {  // volatile ensures fresh read
            printf("Count: %u\n", sample_count);
            data_ready = false;
        }
    }
}
```

**Wrong:**
```c
bool data_ready = false;  // NOT volatile - compiler may cache

void irq_handler(void *ctx)
{
    data_ready = true;
}

int main(void)
{
    while (!data_ready) {
        // Compiler might optimize to infinite loop
        // if it caches data_ready as false
    }
}
```

### 4. Protect Shared Data with Critical Sections

**For multi-byte or complex data:**

```c
volatile uint32_t irq_count = 0;

void irq_handler(void *ctx)
{
    irq_count++;  // Modified in ISR
}

void print_stats(void)
{
    uint32_t local_count;

    // Critical section for atomic read
    no_os_irq_global_disable(irq_ctrl);
    local_count = irq_count;
    irq_count = 0;  // Reset
    no_os_irq_global_enable(irq_ctrl);

    // Process local copy (interrupts enabled)
    printf("Interrupts: %u\n", local_count);
}
```

**For structures:**

```c
struct sensor_data {
    uint32_t timestamp;
    int16_t x, y, z;
};

volatile struct sensor_data latest_sample;

void sensor_irq_handler(void *ctx)
{
    // Write in ISR
    latest_sample.timestamp = get_timestamp();
    latest_sample.x = read_x();
    latest_sample.y = read_y();
    latest_sample.z = read_z();
}

void process_sample(void)
{
    struct sensor_data local_copy;

    // Critical section for atomic read
    no_os_irq_global_disable(irq_ctrl);
    local_copy = latest_sample;
    no_os_irq_global_enable(irq_ctrl);

    // Process local copy
    calculate_magnitude(&local_copy);
}
```

## Trigger Mode Selection

### Edge vs Level Guidelines

| Use Edge When | Use Level When |
|---------------|----------------|
| One-shot events (button press) | Continuous conditions |
| Data ready signals | Multiple interrupt sources per line |
| State transitions | Shared interrupt lines |
| Clean signals | Legacy hardware requirements |

**Edge triggering (preferred for most cases):**
```c
// Button with pull-up resistor
struct no_os_callback_desc button_cb = {
    .event = NO_OS_IRQ_EDGE_FALLING,  // Press = falling edge
};

// ADC data ready (active-high DRDY)
struct no_os_callback_desc adc_cb = {
    .event = NO_OS_IRQ_EDGE_RISING,   // DRDY goes high
};
```

**Level triggering (requires careful handling):**
```c
void level_low_handler(void *ctx)
{
    // CRITICAL: Must clear source!
    uint8_t status = read_status_register();  // Clears interrupt

    if (status & DATA_READY) {
        process_data();
    }

    // If source not cleared, interrupt fires again immediately
}
```

## Priority Assignment

### Priority Levels Strategy

**Guidelines:**
1. **Critical timing** → Priority 0 (highest)
2. **Communication** → Priority 1-2
3. **General peripherals** → Priority 3-4
4. **User interface** → Priority 5+ (lowest)

**Example system:**
```c
// Priority 0: Time-critical data acquisition
struct no_os_callback_desc adc_cb = {
    .callback = adc_handler,
    .priority = 0,  // Cannot be interrupted
};

// Priority 1: UART communication
struct no_os_callback_desc uart_cb = {
    .callback = uart_handler,
    .priority = 1,  // Can be interrupted by ADC only
};

// Priority 2: SPI communication
struct no_os_callback_desc spi_cb = {
    .callback = spi_handler,
    .priority = 2,
};

// Priority 5: User button
struct no_os_callback_desc button_cb = {
    .callback = button_handler,
    .priority = 5,  // Can be interrupted by everything else
};
```

### Priority Inversion Awareness

**Problem:** Low-priority ISR blocks resource needed by high-priority ISR

**Solution:** Keep ISRs independent, minimize shared resources

## Error Handling

### 1. Always Check Return Values

```c
int32_t setup_interrupt(void)
{
    int32_t ret;

    ret = no_os_irq_ctrl_init(&irq_ctrl, &irq_init);
    if (ret) {
        printf("IRQ init failed: %d\n", ret);
        return ret;
    }

    ret = no_os_irq_register_callback(irq_ctrl, irq_id, &callback);
    if (ret) {
        printf("Callback registration failed: %d\n", ret);
        goto error_cleanup;
    }

    ret = no_os_irq_enable(irq_ctrl, irq_id);
    if (ret) {
        printf("IRQ enable failed: %d\n", ret);
        goto error_unregister;
    }

    return 0;

error_unregister:
    no_os_irq_unregister_callback(irq_ctrl, irq_id, &callback);
error_cleanup:
    no_os_irq_ctrl_remove(irq_ctrl);
    return ret;
}
```

### 2. Graceful Cleanup

```c
int32_t cleanup_interrupt(void)
{
    // Disable before unregistering
    no_os_irq_disable(irq_ctrl, irq_id);

    // Unregister callback
    no_os_irq_unregister_callback(irq_ctrl, irq_id, &callback);

    // Remove controller
    no_os_irq_ctrl_remove(irq_ctrl);

    return 0;
}
```

## Debouncing

### Hardware Debouncing

**Add RC filter to button:**
```
Button ----[10kΩ]---- GPIO
            |
           [100nF]
            |
           GND
```

### Software Debouncing

**Simple timer-based debouncing:**
```c
#define DEBOUNCE_MS 50

volatile uint32_t last_press_time = 0;

void button_handler(void *ctx)
{
    uint32_t current_time = get_tick_count();

    // Ignore if within debounce window
    if (current_time - last_press_time < DEBOUNCE_MS)
        return;

    last_press_time = current_time;

    // Process valid button press
    button_pressed = true;
}
```

## Testing and Debugging

### 1. Debug Counters

```c
struct irq_debug {
    volatile uint32_t total_count;
    volatile uint32_t error_count;
    volatile uint32_t spurious_count;
};

struct irq_debug debug;

void irq_handler(void *ctx)
{
    debug.total_count++;

    uint8_t status = read_status_register();

    if (status & ERROR_BIT) {
        debug.error_count++;
    }

    if (!(status & EXPECTED_BITS)) {
        debug.spurious_count++;
    }

    // Normal handling
    process_interrupt(status);
}
```

### 2. Toggle GPIO for Timing Analysis

```c
void timing_critical_handler(void *ctx)
{
    // Set debug pin HIGH at ISR entry
    no_os_gpio_set_value(debug_gpio, 1);

    // ISR work
    process_data();

    // Set debug pin LOW at ISR exit
    no_os_gpio_set_value(debug_gpio, 0);

    // Use oscilloscope to measure pulse width = ISR duration
}
```

### 3. Conditional Debug Output

```c
#ifdef DEBUG_IRQ
    #define IRQ_DEBUG(fmt, ...) printf(fmt, ##__VA_ARGS__)
#else
    #define IRQ_DEBUG(fmt, ...)
#endif

void irq_handler(void *ctx)
{
    // Disabled in release builds
    IRQ_DEBUG("IRQ fired\n");

    process_data();
}
```

## Common Anti-Patterns

### Anti-Pattern 1: Polling Instead of Interrupts

**Bad:**
```c
// Wastes CPU, high latency
while (1) {
    if (gpio_read() == 0) {
        handle_event();
    }
    no_os_mdelay(10);  // Still might miss events
}
```

**Good:**
```c
// Efficient, immediate response
void gpio_handler(void *ctx)
{
    event_flag = true;
}

while (1) {
    if (event_flag) {
        event_flag = false;
        handle_event();
    }
    // CPU can sleep waiting for interrupt
}
```

### Anti-Pattern 2: Complex Logic in ISR

**Bad:**
```c
void irq_handler(void *ctx)
{
    // Too much work in ISR!
    read_100_samples();
    apply_fft();
    update_lcd();
}
```

**Good:**
```c
volatile bool process_buffer = false;

void irq_handler(void *ctx)
{
    read_single_sample();  // Fast
    process_buffer = true;
}

int main(void)
{
    while (1) {
        if (process_buffer) {
            process_buffer = false;
            apply_fft();      // Heavy processing in main
            update_lcd();
        }
    }
}
```

### Anti-Pattern 3: Forgetting Cleanup

**Bad:**
```c
// Memory leak, interrupts still firing
void shutdown_device(void)
{
    free(device);
    // Forgot to disable IRQ!
}
```

**Good:**
```c
void shutdown_device(void)
{
    // Proper cleanup sequence
    no_os_irq_disable(irq_ctrl, irq_id);
    no_os_irq_unregister_callback(irq_ctrl, irq_id, &callback);
    no_os_irq_ctrl_remove(irq_ctrl);
    free(device);
}
```

## Summary of Best Practices

**DO:**
- Keep ISRs short (set flags, read single register)
- Use `volatile` for shared variables
- Protect multi-byte data with critical sections
- Clear interrupt sources (especially level-triggered)
- Assign appropriate priorities
- Test with oscilloscope/logic analyzer
- Implement debouncing for mechanical inputs
- Clean up interrupts on shutdown

**DON'T:**
- Block in ISRs (delays, malloc, printf, I/O)
- Do complex processing in ISRs
- Forget to clear level-triggered interrupts
- Share data without protection
- Ignore return values
- Leave interrupts enabled during cleanup
- Rely on compiler optimization for shared data
