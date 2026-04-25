# API Usage Patterns

Complete usage examples for no-OS IRQ platform drivers.

## Complete Initialization Workflow

### Step 1: Initialize IRQ Controller

```c
struct no_os_irq_ctrl_desc *irq_ctrl;

struct no_os_irq_init_param irq_init = {
    .irq_ctrl_id = 0,                // Controller 0 (NVIC, INTC, etc.)
    .platform_ops = &max_irq_ops,
    .extra = NULL,                   // Platform-specific params
};

ret = no_os_irq_ctrl_init(&irq_ctrl, &irq_init);
if (ret)
    return ret;
```

**Note:** Often only one IRQ controller per system, but some have multiple (e.g., GPIO IRQ controller + peripheral IRQ controller).

### Step 2: Register Callback

```c
struct no_os_callback_desc gpio_callback = {
    .callback = my_gpio_handler,      // Callback function
    .irq_id = 5,                      // GPIO IRQ 5
    .event = NO_OS_IRQ_EDGE_FALLING,  // Falling edge
    .priority = 0,                    // Highest priority
    .ctx = my_device,                 // User context
};

ret = no_os_irq_register_callback(irq_ctrl, gpio_callback.irq_id,
                                  &gpio_callback);
if (ret)
    return ret;
```

### Step 3: Configure Trigger and Priority

```c
// Set trigger mode
no_os_irq_trigger_level_set(irq_ctrl, gpio_callback.irq_id,
                            NO_OS_IRQ_EDGE_FALLING);

// Set priority (0 = highest)
no_os_irq_set_priority(irq_ctrl, gpio_callback.irq_id, 0);
```

### Step 4: Enable Interrupt

```c
// Enable specific IRQ
no_os_irq_enable(irq_ctrl, gpio_callback.irq_id);

// Enable global interrupts
no_os_irq_global_enable(irq_ctrl);
```

### Complete Example

```c
// Device context
struct my_device {
    struct no_os_gpio_desc *gpio;
    struct no_os_irq_ctrl_desc *irq_ctrl;
    volatile uint32_t irq_count;
};

// Interrupt handler
void my_gpio_handler(void *context)
{
    struct my_device *dev = (struct my_device *)context;
    dev->irq_count++;
    printf("Interrupt fired! Count: %u\n", dev->irq_count);

    // Clear interrupt source if needed
    // (platform or peripheral specific)
}

// Setup
int32_t setup_interrupt(struct my_device *dev)
{
    int32_t ret;

    // 1. Initialize IRQ controller
    struct no_os_irq_init_param irq_init = {
        .irq_ctrl_id = 0,
        .platform_ops = &max_irq_ops,
    };

    ret = no_os_irq_ctrl_init(&dev->irq_ctrl, &irq_init);
    if (ret)
        return ret;

    // 2. Register callback
    struct no_os_callback_desc cb = {
        .callback = my_gpio_handler,
        .irq_id = 5,
        .event = NO_OS_IRQ_EDGE_FALLING,
        .priority = 0,
        .ctx = dev,
    };

    ret = no_os_irq_register_callback(dev->irq_ctrl, cb.irq_id, &cb);
    if (ret)
        goto error_irq;

    // 3. Enable IRQ
    no_os_irq_enable(dev->irq_ctrl, cb.irq_id);
    no_os_irq_global_enable(dev->irq_ctrl);

    return 0;

error_irq:
    no_os_irq_ctrl_remove(dev->irq_ctrl);
    return ret;
}
```

## Common Patterns

### Pattern 1: GPIO Interrupt (Button)

```c
volatile bool button_pressed = false;

void button_handler(void *ctx)
{
    button_pressed = true;
}

// Setup
struct no_os_callback_desc button_cb = {
    .callback = button_handler,
    .irq_id = BUTTON_GPIO_IRQ,
    .event = NO_OS_IRQ_EDGE_FALLING,  // Pull-up, active-low
    .priority = 3,
    .ctx = NULL,
};

no_os_irq_register_callback(irq_ctrl, button_cb.irq_id, &button_cb);
no_os_irq_enable(irq_ctrl, button_cb.irq_id);

// Main loop
while (1) {
    if (button_pressed) {
        button_pressed = false;
        printf("Button pressed!\n");
    }
}
```

### Pattern 2: Data Ready Signal

```c
struct adc_device {
    volatile bool data_ready;
    uint32_t latest_sample;
};

void adc_drdy_handler(void *ctx)
{
    struct adc_device *adc = (struct adc_device *)ctx;

    // Read data from ADC
    adc->latest_sample = adc_read_data(adc);
    adc->data_ready = true;
}

// Setup
struct no_os_callback_desc drdy_cb = {
    .callback = adc_drdy_handler,
    .irq_id = ADC_DRDY_IRQ,
    .event = NO_OS_IRQ_EDGE_FALLING,  // /DRDY goes low when ready
    .priority = 0,                     // High priority
    .ctx = &my_adc,
};

no_os_irq_register_callback(irq_ctrl, drdy_cb.irq_id, &drdy_cb);
no_os_irq_enable(irq_ctrl, drdy_cb.irq_id);
```

### Pattern 3: Timer Interrupt

```c
volatile uint32_t tick_count = 0;

void timer_handler(void *ctx)
{
    tick_count++;

    // Clear timer interrupt flag (platform-specific)
    // Example: TIM1->SR &= ~TIM_SR_UIF;
}

// Setup
struct no_os_callback_desc timer_cb = {
    .callback = timer_handler,
    .irq_id = TIMER1_IRQ,
    .event = NO_OS_IRQ_EDGE_RISING,  // Or platform-specific
    .priority = 2,
    .ctx = NULL,
};

no_os_irq_register_callback(irq_ctrl, timer_cb.irq_id, &timer_cb);
no_os_irq_enable(irq_ctrl, timer_cb.irq_id);
```

### Pattern 4: UART Receive

```c
#define RX_BUFFER_SIZE 256

struct uart_rx {
    uint8_t buffer[RX_BUFFER_SIZE];
    volatile uint32_t write_idx;
    uint32_t read_idx;
};

void uart_rx_handler(void *ctx)
{
    struct uart_rx *rx = (struct uart_rx *)ctx;

    // Read byte from UART (platform-specific)
    uint8_t data = UART1->RDR;

    rx->buffer[rx->write_idx] = data;
    rx->write_idx = (rx->write_idx + 1) % RX_BUFFER_SIZE;
}
```

### Pattern 5: Multiple Interrupts with Priorities

```c
// Priority 0: Critical data acquisition (highest)
struct no_os_callback_desc adc_cb = {
    .callback = adc_handler,
    .irq_id = ADC_IRQ,
    .priority = 0,
};

// Priority 1: Communication (high)
struct no_os_callback_desc uart_cb = {
    .callback = uart_handler,
    .irq_id = UART_IRQ,
    .priority = 1,
};

// Priority 3: User interface (low)
struct no_os_callback_desc button_cb = {
    .callback = button_handler,
    .irq_id = BUTTON_IRQ,
    .priority = 3,
};

// Register all
no_os_irq_register_callback(irq_ctrl, adc_cb.irq_id, &adc_cb);
no_os_irq_register_callback(irq_ctrl, uart_cb.irq_id, &uart_cb);
no_os_irq_register_callback(irq_ctrl, button_cb.irq_id, &button_cb);

// Enable all
no_os_irq_enable(irq_ctrl, adc_cb.irq_id);
no_os_irq_enable(irq_ctrl, uart_cb.irq_id);
no_os_irq_enable(irq_ctrl, button_cb.irq_id);

no_os_irq_global_enable(irq_ctrl);
```

### Pattern 6: Shared Data with Protection

```c
volatile uint32_t shared_data = 0;

void irq_handler(void *ctx)
{
    shared_data++;  // Modified in ISR
}

// Main code accessing shared data
void process_data(void)
{
    uint32_t local_copy;

    // Critical section
    no_os_irq_global_disable(irq_ctrl);
    local_copy = shared_data;
    shared_data = 0;
    no_os_irq_global_enable(irq_ctrl);

    // Process local copy (interrupts enabled)
    printf("Received %u events\n", local_copy);
}
```

## IRQ Operations

### 1. Enable/Disable Specific IRQ

```c
int32_t no_os_irq_enable(struct no_os_irq_ctrl_desc *desc,
                        uint32_t irq_id);

int32_t no_os_irq_disable(struct no_os_irq_ctrl_desc *desc,
                         uint32_t irq_id);
```

**Example:**
```c
// Enable GPIO IRQ 5
no_os_irq_enable(irq_ctrl, 5);

// Temporarily disable
no_os_irq_disable(irq_ctrl, 5);

// Re-enable
no_os_irq_enable(irq_ctrl, 5);
```

### 2. Global Enable/Disable

```c
int32_t no_os_irq_global_enable(struct no_os_irq_ctrl_desc *desc);

int32_t no_os_irq_global_disable(struct no_os_irq_ctrl_desc *desc);
```

**Use cases:**
- **Critical sections** – Temporarily disable all interrupts
- **System initialization** – Enable after setup complete
- **Debugging** – Disable interrupts during debug output

**Example:**
```c
// Critical section
no_os_irq_global_disable(irq_ctrl);

// Access shared data
shared_counter++;

no_os_irq_global_enable(irq_ctrl);
```

### 3. Set Priority

```c
int32_t no_os_irq_set_priority(struct no_os_irq_ctrl_desc *desc,
                              uint32_t irq_id, uint32_t priority);
```

**Priority levels:**
- **0** – Highest priority (pre-empts all others)
- **Higher numbers** – Lower priority
- **Platform-specific range** – Check platform documentation

**Example:**
```c
// High priority for data acquisition
no_os_irq_set_priority(irq_ctrl, ADC_IRQ, 0);

// Lower priority for user button
no_os_irq_set_priority(irq_ctrl, BUTTON_IRQ, 5);
```

### 4. Set Trigger Level

```c
int32_t no_os_irq_trigger_level_set(struct no_os_irq_ctrl_desc *desc,
                                   uint32_t irq_id,
                                   enum no_os_irq_trigger_level level);
```

**Example:**
```c
// Change to rising edge
no_os_irq_trigger_level_set(irq_ctrl, irq_id, NO_OS_IRQ_EDGE_RISING);

// Change to both edges
no_os_irq_trigger_level_set(irq_ctrl, irq_id, NO_OS_IRQ_EDGE_BOTH);
```

### 5. Unregister Callback

```c
int32_t no_os_irq_unregister_callback(struct no_os_irq_ctrl_desc *desc,
                                     uint32_t irq_id,
                                     struct no_os_callback_desc *callback);
```

**Example:**
```c
no_os_irq_disable(irq_ctrl, irq_id);
no_os_irq_unregister_callback(irq_ctrl, irq_id, &callback);
```

### 6. Cleanup

```c
int32_t no_os_irq_ctrl_remove(struct no_os_irq_ctrl_desc *desc);
```
