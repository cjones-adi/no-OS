# Troubleshooting IRQ Issues

Common interrupt problems and solutions.

## Interrupt Never Fires

### Symptom
Callback never executes, no interrupt events.

### Possible Causes and Solutions

#### 1. Interrupt Not Enabled

**Check:**
```c
// Did you enable specific IRQ?
no_os_irq_enable(irq_ctrl, irq_id);

// Did you enable global interrupts?
no_os_irq_global_enable(irq_ctrl);
```

**Solution:**
```c
// Complete enable sequence
ret = no_os_irq_enable(irq_ctrl, irq_id);
if (ret) {
    printf("Enable failed: %d\n", ret);
    return ret;
}

no_os_irq_global_enable(irq_ctrl);
```

#### 2. Callback Not Registered

**Check:**
```c
// Did you call register_callback()?
ret = no_os_irq_register_callback(irq_ctrl, irq_id, &callback);
if (ret) {
    printf("Registration failed: %d\n", ret);
}
```

**Debug:**
```c
// Add debug output after registration
printf("Callback registered for IRQ %u\n", irq_id);
printf("Callback address: %p\n", (void *)callback.callback);
```

#### 3. Wrong Trigger Mode

**Check:**
- Edge vs level mismatch
- Rising vs falling mismatch
- Signal polarity

**Example Issues:**
```c
// Signal goes LOW but trigger set to RISING
struct no_os_callback_desc cb = {
    .event = NO_OS_IRQ_EDGE_RISING,  // WRONG for active-low signal
};

// Should be:
struct no_os_callback_desc cb = {
    .event = NO_OS_IRQ_EDGE_FALLING,  // Correct for active-low
};
```

**Debug with oscilloscope:**
- Verify signal actually transitions
- Check edge direction (rising/falling)
- Measure signal voltage levels

#### 4. GPIO Not Configured

**Check:**
```c
// GPIO must be configured as input
struct no_os_gpio_init_param gpio_init = {
    .number = GPIO_PIN,
    .platform_ops = &gpio_ops,
    .extra = &gpio_extra,
};

// Missing: GPIO direction!
ret = no_os_gpio_get(&gpio_desc, &gpio_init);

// Should include:
ret = no_os_gpio_direction_input(gpio_desc);
```

**Complete GPIO setup:**
```c
// 1. Initialize GPIO
no_os_gpio_get(&gpio_desc, &gpio_init);

// 2. Set direction to input
no_os_gpio_direction_input(gpio_desc);

// 3. Configure pull-up/pull-down if needed
no_os_gpio_set_pull_mode(gpio_desc, NO_OS_PULL_UP);

// 4. Then setup interrupt
no_os_irq_register_callback(irq_ctrl, irq_id, &callback);
```

#### 5. Platform Mux Not Configured

**Issue:** Pin not muxed to GPIO interrupt function

**Platform-specific examples:**

**STM32:**
```c
// Ensure GPIO clock enabled
__HAL_RCC_GPIOA_CLK_ENABLE();

// Configure EXTI line
HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
```

**Maxim:**
```c
// Configure pin mux for GPIO
MXC_GPIO_Config(&gpio_cfg);
```

**Check datasheet:** Verify pin supports interrupt function.

#### 6. Hardware Issue

**Verify with hardware:**
- Use oscilloscope to confirm signal transitions
- Check signal voltage levels (3.3V, 5V, etc.)
- Verify pull-up/pull-down resistors
- Test with known-good signal source

**Simple test:**
```c
// Poll GPIO to verify signal changes
while (1) {
    uint8_t value;
    no_os_gpio_get_value(gpio_desc, &value);
    printf("GPIO state: %u\n", value);
    no_os_mdelay(100);
}
```

If polling shows changes but interrupt doesn't fire, issue is in IRQ configuration.

## Interrupt Fires Continuously

### Symptom
ISR executes repeatedly without pause, system appears hung.

### Possible Causes and Solutions

#### 1. Level-Triggered Interrupt Source Not Cleared

**Problem:**
```c
void level_irq_handler(void *ctx)
{
    // Process interrupt
    process_data();

    // BUG: Forgot to clear interrupt source!
    // Interrupt fires again immediately
}
```

**Solution:**
```c
void level_irq_handler(void *ctx)
{
    // MUST clear source for level-triggered
    uint8_t status = read_status_register();  // Clears interrupt

    if (status & DATA_READY) {
        process_data();
    }

    // Now interrupt is cleared, won't fire again immediately
}
```

#### 2. Wrong Trigger Type

**Using LEVEL when should use EDGE:**
```c
// BUG: Level-triggered on GPIO button
struct no_os_callback_desc button_cb = {
    .event = NO_OS_IRQ_LEVEL_LOW,  // WRONG - fires continuously
};

// Should be edge-triggered:
struct no_os_callback_desc button_cb = {
    .event = NO_OS_IRQ_EDGE_FALLING,  // Correct - fires once per press
};
```

#### 3. Hardware Signal Stuck

**Check:**
- Signal stuck low/high due to hardware fault
- Short circuit
- Broken pull-up/pull-down resistor

**Debug:**
```c
void debug_irq_handler(void *ctx)
{
    static uint32_t count = 0;

    count++;

    if (count > 10) {
        // Too many interrupts - disable and investigate
        no_os_irq_disable(irq_ctrl, irq_id);
        printf("Interrupt storm detected! Disabled.\n");
    }

    // Read and log GPIO state
    uint8_t gpio_state;
    no_os_gpio_get_value(gpio_desc, &gpio_state);
    printf("IRQ #%u, GPIO state: %u\n", count, gpio_state);
}
```

#### 4. Missing Platform-Specific Acknowledge

**Some platforms require explicit ACK:**
```c
void platform_irq_handler(void *ctx)
{
    // Process interrupt
    process_data();

    // Platform-specific clear
    // Example: Write to interrupt clear register
    PERIPHERAL->ICR = IRQ_CLEAR_BIT;

    // Or call platform HAL
    HAL_IRQ_Clear(IRQ_ID);
}
```

## Missed Interrupts

### Symptom
Some interrupt events not handled, data loss.

### Possible Causes and Solutions

#### 1. ISR Takes Too Long

**Problem:**
```c
void slow_irq_handler(void *ctx)
{
    // Too much work in ISR!
    for (int i = 0; i < 1000; i++) {
        process_sample(i);  // SLOW
    }

    // While processing, other interrupts missed
}
```

**Solution:**
```c
volatile bool process_flag = false;

void fast_irq_handler(void *ctx)
{
    // Minimal work in ISR
    read_one_sample();
    process_flag = true;
}

int main(void)
{
    while (1) {
        if (process_flag) {
            process_flag = false;

            // Heavy processing in main loop
            for (int i = 0; i < 1000; i++) {
                process_sample(i);
            }
        }
    }
}
```

#### 2. Priority Too Low

**Problem:**
```c
// Low priority interrupt pre-empted by higher priorities
struct no_os_callback_desc low_priority_cb = {
    .callback = important_handler,
    .priority = 10,  // Too low - frequently interrupted
};
```

**Solution:**
```c
// Increase priority for critical interrupts
struct no_os_callback_desc high_priority_cb = {
    .callback = important_handler,
    .priority = 0,  // Highest - won't be pre-empted
};
```

#### 3. Global Interrupts Disabled Too Long

**Problem:**
```c
void process_data(void)
{
    no_os_irq_global_disable(irq_ctrl);

    // Long critical section - interrupts missed!
    complex_processing();  // Takes 10ms
    write_to_flash();      // Takes 50ms

    no_os_irq_global_enable(irq_ctrl);
}
```

**Solution:**
```c
void process_data(void)
{
    uint8_t local_buffer[256];

    // Short critical section - just copy data
    no_os_irq_global_disable(irq_ctrl);
    memcpy(local_buffer, shared_buffer, sizeof(local_buffer));
    no_os_irq_global_enable(irq_ctrl);

    // Process local copy with interrupts enabled
    complex_processing(local_buffer);
    write_to_flash(local_buffer);
}
```

#### 4. Buffer Overflow

**Problem:**
```c
#define BUFFER_SIZE 32  // Too small

struct ring_buffer {
    uint8_t data[BUFFER_SIZE];
    volatile uint32_t write_idx;
    uint32_t read_idx;
};

void uart_rx_handler(void *ctx)
{
    struct ring_buffer *rb = (struct ring_buffer *)ctx;

    // No overflow check - data lost if buffer full
    rb->data[rb->write_idx] = UART_ReadByte();
    rb->write_idx = (rb->write_idx + 1) % BUFFER_SIZE;
}
```

**Solution:**
```c
#define BUFFER_SIZE 256  // Larger buffer

void uart_rx_handler(void *ctx)
{
    struct ring_buffer *rb = (struct ring_buffer *)ctx;
    uint32_t next_write;

    next_write = (rb->write_idx + 1) % BUFFER_SIZE;

    // Check for overflow
    if (next_write == rb->read_idx) {
        // Buffer full - increment error counter
        rb->overflow_count++;
        return;
    }

    // Store data
    rb->data[rb->write_idx] = UART_ReadByte();
    rb->write_idx = next_write;
}
```

## System Crash in ISR

### Symptom
System hangs, resets, or hard faults during interrupt handling.

### Possible Causes and Solutions

#### 1. Stack Overflow

**Symptoms:**
- Crash during interrupt
- Corrupt local variables
- Hard fault

**Solution:**
```c
// Increase interrupt stack size in linker script or startup code

// STM32 example (startup_stm32.s):
Stack_Size      EQU     0x1000  // Increase from 0x400

// Or in linker script:
_Min_Stack_Size = 0x1000 ;
```

#### 2. Invalid Pointer/Context

**Problem:**
```c
void bad_irq_handler(void *ctx)
{
    struct my_device *dev = (struct my_device *)ctx;

    // BUG: ctx is NULL or invalid pointer
    dev->data_ready = true;  // CRASH
}
```

**Solution:**
```c
void safe_irq_handler(void *ctx)
{
    // Validate pointer
    if (!ctx) {
        error_count++;
        return;
    }

    struct my_device *dev = (struct my_device *)ctx;

    // Safe to use
    dev->data_ready = true;
}

// Ensure valid context at registration
struct no_os_callback_desc cb = {
    .callback = safe_irq_handler,
    .ctx = &my_device,  // Valid pointer
};
```

#### 3. Recursive Interrupt

**Problem:**
```c
void recursive_handler(void *ctx)
{
    // Triggers same interrupt from within ISR
    trigger_same_interrupt();  // BUG: Infinite recursion
}
```

**Solution:**
```c
void safe_handler(void *ctx)
{
    static volatile bool handler_active = false;

    // Prevent recursion
    if (handler_active) {
        recursion_count++;
        return;
    }

    handler_active = true;

    // Process interrupt
    process_data();

    handler_active = false;
}
```

#### 4. Non-Reentrant Code

**Problem:**
```c
void bad_handler(void *ctx)
{
    // malloc/free are NOT reentrant
    uint8_t *buffer = malloc(256);  // CRASH if interrupted malloc
    process_buffer(buffer);
    free(buffer);
}
```

**Solution:**
```c
static uint8_t static_buffer[256];  // Statically allocated

void safe_handler(void *ctx)
{
    // Use static buffer - no malloc
    process_buffer(static_buffer);
}
```

## Data Corruption

### Symptom
Shared variables have incorrect or inconsistent values.

### Possible Causes and Solutions

#### 1. Missing Volatile

**Problem:**
```c
bool data_ready = false;  // NOT volatile

void irq_handler(void *ctx)
{
    data_ready = true;
}

int main(void)
{
    while (!data_ready) {
        // Compiler may cache data_ready - infinite loop
    }
}
```

**Solution:**
```c
volatile bool data_ready = false;  // volatile keyword

void irq_handler(void *ctx)
{
    data_ready = true;
}

int main(void)
{
    while (!data_ready) {
        // Compiler re-reads data_ready each iteration
    }
}
```

#### 2. No Critical Section Protection

**Problem:**
```c
uint32_t shared_counter = 0;  // Multi-byte variable

void irq_handler(void *ctx)
{
    shared_counter++;  // Modifies in ISR
}

void print_counter(void)
{
    // BUG: Non-atomic read of 32-bit value
    printf("Count: %u\n", shared_counter);
    // Could read partially updated value
}
```

**Solution:**
```c
volatile uint32_t shared_counter = 0;

void irq_handler(void *ctx)
{
    shared_counter++;
}

void print_counter(void)
{
    uint32_t local_copy;

    // Atomic read using critical section
    no_os_irq_global_disable(irq_ctrl);
    local_copy = shared_counter;
    no_os_irq_global_enable(irq_ctrl);

    printf("Count: %u\n", local_copy);
}
```

#### 3. Alignment Issues

**Problem:**
```c
struct data {
    uint8_t status;
    uint32_t value;  // May not be aligned
} __attribute__((packed));

volatile struct data shared;  // Non-atomic access possible
```

**Solution:**
```c
// Use properly aligned structures
struct data {
    uint32_t value;  // Aligned to 4-byte boundary
    uint8_t status;
    uint8_t padding[3];  // Explicit padding
};

// Or access with critical section
void read_data(struct data *output)
{
    no_os_irq_global_disable(irq_ctrl);
    *output = shared;
    no_os_irq_global_enable(irq_ctrl);
}
```

## Debugging Techniques

### 1. Interrupt Counters

```c
struct irq_stats {
    volatile uint32_t total_count;
    volatile uint32_t error_count;
    volatile uint32_t max_latency_us;
};

struct irq_stats stats = {0};

void instrumented_handler(void *ctx)
{
    uint32_t entry_time = get_timestamp_us();

    stats.total_count++;

    // Normal processing
    process_interrupt();

    uint32_t exit_time = get_timestamp_us();
    uint32_t latency = exit_time - entry_time;

    if (latency > stats.max_latency_us) {
        stats.max_latency_us = latency;
    }
}

// Monitor stats in main loop
void print_stats(void)
{
    printf("IRQ count: %u\n", stats.total_count);
    printf("Errors: %u\n", stats.error_count);
    printf("Max latency: %u us\n", stats.max_latency_us);
}
```

### 2. GPIO Toggle for Timing

```c
void timing_debug_handler(void *ctx)
{
    // Toggle GPIO at ISR entry
    no_os_gpio_set_value(debug_gpio, 1);

    process_interrupt();

    // Toggle GPIO at ISR exit
    no_os_gpio_set_value(debug_gpio, 0);

    // Measure pulse width with oscilloscope = ISR duration
}
```

### 3. Watchdog for Stuck ISR

```c
#define ISR_TIMEOUT_MS 100

uint32_t isr_entry_time = 0;

void watchdog_protected_handler(void *ctx)
{
    isr_entry_time = get_tick_count();

    process_interrupt();

    isr_entry_time = 0;  // Clear on exit
}

// Watchdog check in timer or main loop
void check_isr_timeout(void)
{
    if (isr_entry_time != 0) {
        uint32_t duration = get_tick_count() - isr_entry_time;

        if (duration > ISR_TIMEOUT_MS) {
            printf("ERROR: ISR stuck for %u ms!\n", duration);
            // Take corrective action
            no_os_irq_disable(irq_ctrl, irq_id);
        }
    }
}
```
