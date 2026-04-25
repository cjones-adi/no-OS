# Interrupt Handling Details

Complete reference for interrupt handling mechanisms in no-OS.

## Core Data Structures

### 1. no_os_irq_init_param – Controller Initialization

```c
struct no_os_irq_init_param {
    uint32_t irq_ctrl_id;                    // Controller ID
    const struct no_os_irq_platform_ops *platform_ops;
    void *extra;                             // Platform-specific params
};
```

### 2. no_os_irq_ctrl_desc – Controller Descriptor

```c
struct no_os_irq_ctrl_desc {
    uint32_t irq_ctrl_id;                    // Controller ID
    const struct no_os_irq_platform_ops *platform_ops;
    void *extra;                             // Platform-specific data
};
```

### 3. no_os_callback_desc – Callback Registration

```c
struct no_os_callback_desc {
    void (*callback)(void *context);         // User callback function
    uint32_t irq_id;                         // IRQ number
    enum no_os_irq_trigger_level event;      // Trigger mode
    uint32_t priority;                       // Priority level
    void *ctx;                               // User context (passed to callback)
    void *handle;                            // Platform-specific handle
};
```

**Callback function signature:**
```c
void my_irq_handler(void *context)
{
    struct my_device *dev = (struct my_device *)context;
    // Handle interrupt...
}
```

### 4. no_os_irq_trigger_level – Trigger Modes

```c
enum no_os_irq_trigger_level {
    NO_OS_IRQ_EDGE_RISING,          // Rising edge (LOW→HIGH)
    NO_OS_IRQ_EDGE_FALLING,         // Falling edge (HIGH→LOW)
    NO_OS_IRQ_EDGE_BOTH,            // Both edges
    NO_OS_IRQ_LEVEL_HIGH,           // High level (continuous HIGH)
    NO_OS_IRQ_LEVEL_LOW             // Low level (continuous LOW)
};
```

## Trigger Modes Explained

### Edge vs Level

- **Edge** – Triggered once per transition
- **Level** – Triggered continuously while asserted (must clear source)

### Use Cases

| Trigger Mode | When to Use | Example |
|--------------|-------------|---------|
| `NO_OS_IRQ_EDGE_RISING` | Button press (pull-down), data ready active-high | GPIO rising edge |
| `NO_OS_IRQ_EDGE_FALLING` | Button press (pull-up), chip /DRDY signal | Active-low interrupt |
| `NO_OS_IRQ_EDGE_BOTH` | Quadrature encoder, state changes | Any transition |
| `NO_OS_IRQ_LEVEL_HIGH` | Continuous high signal (must clear source) | Active-high level |
| `NO_OS_IRQ_LEVEL_LOW` | Active-low interrupt outputs (must clear source) | Active-low level |

### Edge Triggering

**Characteristics:**
- Fires once per edge transition
- Does not require clearing interrupt source
- Good for one-shot events
- Less susceptible to noise (with debouncing)

**Example: Button with pull-up**
```c
struct no_os_callback_desc button_cb = {
    .callback = button_handler,
    .irq_id = BUTTON_GPIO_IRQ,
    .event = NO_OS_IRQ_EDGE_FALLING,  // Pull-up, press = falling edge
    .priority = 3,
    .ctx = NULL,
};
```

**Example: Data ready with active-high**
```c
struct no_os_callback_desc drdy_cb = {
    .callback = data_ready_handler,
    .irq_id = DRDY_GPIO_IRQ,
    .event = NO_OS_IRQ_EDGE_RISING,   // DRDY goes high when ready
    .priority = 0,
    .ctx = &my_device,
};
```

### Level Triggering

**Characteristics:**
- Fires continuously while signal is asserted
- **MUST** clear interrupt source in handler
- Can cause interrupt storm if source not cleared
- Good for continuous conditions

**Example: Active-low interrupt**
```c
void level_low_handler(void *ctx)
{
    struct my_device *dev = (struct my_device *)ctx;

    // Read and process data
    process_data(dev);

    // CRITICAL: Clear interrupt source
    // (peripheral-specific - read status register, write ack, etc.)
    clear_peripheral_interrupt(dev);
}

struct no_os_callback_desc level_cb = {
    .callback = level_low_handler,
    .irq_id = PERIPHERAL_IRQ,
    .event = NO_OS_IRQ_LEVEL_LOW,
    .priority = 1,
    .ctx = &my_device,
};
```

## Priority Management

### Priority Levels

- **0** – Highest priority (pre-empts all others)
- **Higher numbers** – Lower priority
- **Platform-specific range** – Varies by platform

**Typical platform ranges:**
- ARM Cortex-M: 0-255 (often fewer bits implemented)
- RISC-V PLIC: 0-7 or 0-31
- Xilinx INTC: 0-31

### Priority Guidelines

| Priority | Typical Use |
|----------|-------------|
| 0 (highest) | Critical data acquisition, DMA |
| 1-2 | Communication (UART, SPI, I2C) |
| 3-4 | Timers, ADC/DAC |
| 5+ (lowest) | User interface, buttons, LEDs |

### Nested Interrupts

Higher priority interrupts can preempt lower priority ones:

```c
// Priority 0 - can interrupt everything
struct no_os_callback_desc critical_cb = {
    .callback = critical_handler,
    .irq_id = CRITICAL_IRQ,
    .priority = 0,  // Highest
};

// Priority 5 - can be interrupted by priority 0-4
struct no_os_callback_desc low_cb = {
    .callback = low_priority_handler,
    .irq_id = LOW_PRIORITY_IRQ,
    .priority = 5,
};
```

**Execution scenario:**
1. `low_priority_handler()` starts executing
2. Critical interrupt fires
3. `low_priority_handler()` paused (context saved)
4. `critical_handler()` executes
5. `critical_handler()` completes
6. `low_priority_handler()` resumes

## Callback Context

### Why Use Context?

Pass device-specific data to interrupt handler:

```c
struct my_device {
    struct no_os_spi_desc *spi;
    volatile bool data_ready;
    uint8_t *rx_buffer;
    uint32_t buffer_size;
};

void my_irq_handler(void *context)
{
    struct my_device *dev = (struct my_device *)context;

    // Access device state
    spi_read(dev->spi, dev->rx_buffer, dev->buffer_size);
    dev->data_ready = true;
}

// Register with device context
struct no_os_callback_desc cb = {
    .callback = my_irq_handler,
    .irq_id = IRQ_ID,
    .event = NO_OS_IRQ_EDGE_FALLING,
    .priority = 0,
    .ctx = &my_device_instance,  // Pass device pointer
};
```

### Multiple Devices

Handle multiple instances of same device:

```c
struct adc_device adc1, adc2;

void adc_handler(void *context)
{
    struct adc_device *adc = (struct adc_device *)context;
    // Handle specific ADC instance
    adc->data = read_adc(adc);
}

// Register separate callbacks for each device
struct no_os_callback_desc adc1_cb = {
    .callback = adc_handler,
    .irq_id = ADC1_IRQ,
    .ctx = &adc1,  // Instance 1
};

struct no_os_callback_desc adc2_cb = {
    .callback = adc_handler,
    .irq_id = ADC2_IRQ,
    .ctx = &adc2,  // Instance 2
};
```

## Interrupt Service Routine (ISR) Flow

### Platform ISR → User Callback

```
Hardware Event
      │
      ▼
┌─────────────────────┐
│  Hardware IRQ Line  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────┐
│  Platform ISR           │
│  (e.g., GPIO5_IRQHandler)│
└──────────┬──────────────┘
           │
           │  Lookup callback in table
           │  using irq_id
           ▼
┌─────────────────────────┐
│  User Callback          │
│  (registered via        │
│   register_callback)    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  User Handler Code      │
│  - Read data            │
│  - Set flags            │
│  - Clear source         │
└─────────────────────────┘
```

### Minimal ISR Example (Platform Code)

```c
// Platform-specific interrupt table
static struct no_os_callback_desc *irq_table[MAX_IRQS];

// Platform ISR (generated by linker/startup)
void GPIO5_IRQHandler(void)
{
    uint32_t irq_id = 5;

    // Clear hardware interrupt flag (platform-specific)
    CLEAR_GPIO_IRQ_FLAG(5);

    // Check if callback registered
    if (irq_table[irq_id] && irq_table[irq_id]->callback) {
        // Call user callback with context
        irq_table[irq_id]->callback(irq_table[irq_id]->ctx);
    }
}
```

## Shared Data and Synchronization

### Volatile Keyword

Variables modified in ISR MUST be declared `volatile`:

```c
// WRONG - compiler may optimize away reads
bool data_ready = false;

// CORRECT - volatile prevents optimization
volatile bool data_ready = false;

void irq_handler(void *ctx)
{
    data_ready = true;  // Modified in ISR
}

int main(void)
{
    while (!data_ready) {
        // Without volatile, compiler might cache 'data_ready'
        // and never see the change from ISR
    }
}
```

### Critical Sections

Protect shared data with global disable/enable:

```c
volatile uint32_t shared_counter = 0;

void irq_handler(void *ctx)
{
    shared_counter++;  // Modified in ISR
}

void process_data(void)
{
    uint32_t local_copy;

    // Enter critical section
    no_os_irq_global_disable(irq_ctrl);

    // Access shared data safely
    local_copy = shared_counter;
    shared_counter = 0;

    // Exit critical section
    no_os_irq_global_enable(irq_ctrl);

    // Process local copy (interrupts enabled)
    printf("Count: %u\n", local_copy);
}
```

### Ring Buffers for Producer-Consumer

```c
#define BUFFER_SIZE 128

struct ring_buffer {
    uint8_t data[BUFFER_SIZE];
    volatile uint32_t write_idx;  // Modified in ISR
    uint32_t read_idx;            // Modified in main
};

void uart_rx_handler(void *ctx)
{
    struct ring_buffer *rb = (struct ring_buffer *)ctx;

    // Read from UART
    uint8_t byte = UART_ReadByte();

    // Write to buffer
    rb->data[rb->write_idx] = byte;
    rb->write_idx = (rb->write_idx + 1) % BUFFER_SIZE;
}

uint32_t ring_buffer_available(struct ring_buffer *rb)
{
    uint32_t write_idx;

    // Read volatile once
    write_idx = rb->write_idx;

    if (write_idx >= rb->read_idx)
        return write_idx - rb->read_idx;
    else
        return BUFFER_SIZE - rb->read_idx + write_idx;
}

bool ring_buffer_read(struct ring_buffer *rb, uint8_t *data)
{
    if (ring_buffer_available(rb) == 0)
        return false;

    *data = rb->data[rb->read_idx];
    rb->read_idx = (rb->read_idx + 1) % BUFFER_SIZE;
    return true;
}
```

## Clearing Interrupt Sources

### Why Clear Interrupts?

**Edge-triggered:** Usually auto-clears after edge detection

**Level-triggered:** MUST manually clear source or interrupt fires continuously

### Common Clearing Mechanisms

**1. Read status register:**
```c
void irq_handler(void *ctx)
{
    // Reading status automatically clears interrupt
    uint8_t status = read_status_register();

    // Process based on status
    if (status & DATA_READY_BIT) {
        process_data();
    }
}
```

**2. Write to clear register:**
```c
void irq_handler(void *ctx)
{
    // Write to interrupt clear register
    write_clear_register(IRQ_CLEAR_BIT);

    // Handle interrupt
    process_event();
}
```

**3. Read data register:**
```c
void uart_rx_handler(void *ctx)
{
    // Reading data register clears RX interrupt
    uint8_t data = UART->RDR;

    // Store data
    store_received_byte(data);
}
```

**4. Platform-specific acknowledge:**
```c
void peripheral_handler(void *ctx)
{
    // Platform/peripheral may require explicit ACK
    peripheral_acknowledge_interrupt();

    // Handle interrupt
    process_peripheral_event();
}
```
