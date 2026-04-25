# Platform API Implementations

Complete reference for implementing platform-specific IRQ drivers.

## Platform Operations Structure

```c
struct no_os_irq_platform_ops {
    int32_t (*init)(struct no_os_irq_ctrl_desc **,
                    const struct no_os_irq_init_param *);
    int32_t (*register_callback)(struct no_os_irq_ctrl_desc *,
                                 uint32_t irq_id,
                                 struct no_os_callback_desc *);
    int32_t (*unregister_callback)(struct no_os_irq_ctrl_desc *,
                                   uint32_t irq_id,
                                   struct no_os_callback_desc *);
    int32_t (*global_enable)(struct no_os_irq_ctrl_desc *);
    int32_t (*global_disable)(struct no_os_irq_ctrl_desc *);
    int32_t (*enable)(struct no_os_irq_ctrl_desc *, uint32_t irq_id);
    int32_t (*disable)(struct no_os_irq_ctrl_desc *, uint32_t irq_id);
    int32_t (*set_priority)(struct no_os_irq_ctrl_desc *,
                           uint32_t irq_id, uint32_t priority);
    int32_t (*trigger_level_set)(struct no_os_irq_ctrl_desc *,
                                uint32_t irq_id,
                                enum no_os_irq_trigger_level);
    int32_t (*remove)(struct no_os_irq_ctrl_desc *);
};
```

## Porting to New Platforms

### Step 1: Create Platform Files

```
drivers/platform/myplatform/
├── myplatform_irq.c      # Implementation
└── myplatform_irq.h      # Platform extras
```

### Step 2: Define Platform Extras

In `myplatform_irq.h`:

```c
struct myplatform_irq_init_param {
    // Platform-specific controller params
};

struct myplatform_irq_desc {
    // Platform-specific controller state
    // Example: interrupt table, enabled flags, etc.
};
```

### Step 3: Implement Platform Operations

In `myplatform_irq.c`:

```c
int32_t myplatform_irq_ctrl_init(struct no_os_irq_ctrl_desc **desc,
                                 const struct no_os_irq_init_param *param)
{
    // 1. Allocate descriptor
    *desc = calloc(1, sizeof(**desc));

    // 2. Initialize interrupt controller (vendor HAL)
    // Example: NVIC_Init(), HAL_IRQ_Init(), etc.

    // 3. Allocate platform-specific data
    (*desc)->extra = calloc(1, sizeof(struct myplatform_irq_desc));

    return 0;
}

int32_t myplatform_irq_register_callback(struct no_os_irq_ctrl_desc *desc,
                                        uint32_t irq_id,
                                        struct no_os_callback_desc *callback)
{
    // Store callback in platform-specific table
    irq_table[irq_id] = callback;

    return 0;
}

int32_t myplatform_irq_enable(struct no_os_irq_ctrl_desc *desc,
                              uint32_t irq_id)
{
    // Enable specific IRQ using vendor HAL
    // Example: NVIC_EnableIRQ(irq_id);

    return 0;
}

int32_t myplatform_irq_disable(struct no_os_irq_ctrl_desc *desc,
                               uint32_t irq_id)
{
    // Disable specific IRQ
    // Example: NVIC_DisableIRQ(irq_id);

    return 0;
}

int32_t myplatform_irq_global_enable(struct no_os_irq_ctrl_desc *desc)
{
    // Enable global interrupts
    // Example: __enable_irq();

    return 0;
}

int32_t myplatform_irq_global_disable(struct no_os_irq_ctrl_desc *desc)
{
    // Disable global interrupts
    // Example: __disable_irq();

    return 0;
}

int32_t myplatform_irq_set_priority(struct no_os_irq_ctrl_desc *desc,
                                   uint32_t irq_id, uint32_t priority)
{
    // Set priority
    // Example: NVIC_SetPriority(irq_id, priority);

    return 0;
}

int32_t myplatform_irq_trigger_level_set(struct no_os_irq_ctrl_desc *desc,
                                        uint32_t irq_id,
                                        enum no_os_irq_trigger_level level)
{
    // Configure trigger mode
    // Platform-specific implementation

    return 0;
}

int32_t myplatform_irq_unregister_callback(struct no_os_irq_ctrl_desc *desc,
                                          uint32_t irq_id,
                                          struct no_os_callback_desc *callback)
{
    // Remove callback from table
    irq_table[irq_id] = NULL;

    return 0;
}

int32_t myplatform_irq_ctrl_remove(struct no_os_irq_ctrl_desc *desc)
{
    // Cleanup platform resources
    free(desc->extra);
    free(desc);

    return 0;
}
```

### Step 4: Implement Platform ISR Dispatcher

**Critical:** Platform ISR must call registered callback:

```c
// Platform-specific interrupt table
static struct no_os_callback_desc *irq_table[MAX_IRQS];

// Example ISR for GPIO interrupt
void GPIO5_IRQHandler(void)
{
    uint32_t irq_id = 5;

    // Check if callback registered
    if (irq_table[irq_id] && irq_table[irq_id]->callback) {
        // Call user callback with context
        irq_table[irq_id]->callback(irq_table[irq_id]->ctx);
    }

    // Clear interrupt flag (platform-specific)
    // Example: GPIO->IFR = (1 << 5);
}
```

### Step 5: Define Platform Ops

```c
const struct no_os_irq_platform_ops myplatform_irq_ops = {
    .init = &myplatform_irq_ctrl_init,
    .register_callback = &myplatform_irq_register_callback,
    .unregister_callback = &myplatform_irq_unregister_callback,
    .global_enable = &myplatform_irq_global_enable,
    .global_disable = &myplatform_irq_global_disable,
    .enable = &myplatform_irq_enable,
    .disable = &myplatform_irq_disable,
    .set_priority = &myplatform_irq_set_priority,
    .trigger_level_set = &myplatform_irq_trigger_level_set,
    .remove = &myplatform_irq_ctrl_remove,
};
```

## Implementation Notes

### Callback Table Management

Most platforms use a static callback table to map IRQ IDs to callbacks:

```c
#define MAX_IRQ_NB 64
static struct no_os_callback_desc *irq_callbacks[MAX_IRQ_NB];
```

### Priority Mapping

Different platforms have different priority schemes:
- **ARM Cortex-M (NVIC)**: 0 = highest, larger = lower priority
- **RISC-V PLIC**: Priority levels platform-specific
- **Xilinx**: 0-31 priority levels

Map generic priority to platform-specific values in `set_priority()`.

### Trigger Level Configuration

Platform-specific registers control edge/level sensitivity:
- **GPIO controllers**: Often have separate edge/level registers
- **External interrupt controllers**: Configuration registers
- **Some platforms**: Limited trigger mode support

Implement as much as hardware supports, return error for unsupported modes.

### Global Enable/Disable

Usually maps to CPU interrupt enable/disable:
```c
// ARM Cortex-M
__enable_irq();   // CPSIE i
__disable_irq();  // CPSID i

// RISC-V
set_csr(mstatus, MSTATUS_MIE);
clear_csr(mstatus, MSTATUS_MIE);
```

### Critical Sections

Platform implementation must be **reentrant** and **interrupt-safe**:
- Disable interrupts when modifying shared state
- Use atomic operations where applicable
- Keep critical sections short
