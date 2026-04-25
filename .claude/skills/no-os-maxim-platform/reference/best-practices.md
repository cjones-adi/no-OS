# Maxim Platform Best Practices

Best practices, patterns, and recommendations for developing with Maxim platform drivers in no-OS.

## VDDIO Configuration

### Always Set VDDIO Voltage Selection

**Critical Requirement**: Always set `vssel` in init parameters to match hardware design.

```c
// WRONG - Missing vssel (undefined behavior)
struct max_spi_init_param spi_extra = {
    .num_slaves = 1,
    .polarity = MXC_SPI_TSCONTROL_ACTIVE_LO,
    // Missing .vssel!
};

// CORRECT - Explicitly set vssel
struct max_spi_init_param spi_extra = {
    .num_slaves = 1,
    .polarity = MXC_SPI_TSCONTROL_ACTIVE_LO,
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // Match hardware
};
```

### Match VDDIO to Hardware Design

**Decision Tree**:
```
Is VDDIO rail 1.8V?
├─ YES → Use MXC_GPIO_VSSEL_VDDIO
│         Peripheral must support 1.8V
│
└─ NO (VDDIO is 3.3V)
    ├─ Peripheral needs 3.3V → Use MXC_GPIO_VSSEL_VDDIO
    └─ System has VDDIOH rail → Can use MXC_GPIO_VSSEL_VDDIOH
```

**Examples**:
```c
// 1.8V SPI flash on 1.8V VDDIO system
struct max_spi_init_param spi_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // 1.8V
};

// SD card (3.3V) on system with 1.8V VDDIO + 3.3V VDDIOH
struct max_spi_init_param sd_spi = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // 3.3V for SD card
};

// RS232 transceiver (3.3V) with VDDIOH
struct max_uart_init_param uart_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // 3.3V for RS232
};
```

### Document VDDIO Choice

```c
// GOOD - Comment explains voltage selection
struct max_spi_init_param spi_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // 3.3V required for SD card
};

// BETTER - Comment references schematic
struct max_i2c_init_param i2c_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // Matches VDDIO rail (see U5 schematic)
};
```

## Clock Management

### Enable Clocks Before Peripheral Init

**Correct Order**:
```c
// 1. Enable clock
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);

// 2. Optional: Reset peripheral
MXC_SYS_Reset_Periph(MXC_SYS_PERIPH_RESET_SPI0);

// 3. Initialize peripheral
ret = no_os_spi_init(&spi, &spi_init);
```

**Wrong Order**:
```c
// WRONG - Init before clock enable
ret = no_os_spi_init(&spi, &spi_init);  // May fail silently
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);  // Too late
```

### Check Clock Status

```c
// Defensive check before init
if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_SPI0)) {
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
}
```

### Reset After Clock Enable for Clean State

```c
// Enable and reset for known-good state
if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_DMA)) {
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_DMA);
    MXC_SYS_Reset_Periph(MAX_DMA_GCR_RST_POS);  // Reset clears registers
}
```

## DMA Configuration

### Always Set RX Priority Higher Than TX

**Critical Rule**: RX DMA priority must be higher (lower number) than TX DMA.

```c
// WRONG - TX priority higher or equal to RX
struct max_spi_init_param spi_extra = {
    .dma_tx_priority = 1,  // Higher priority
    .dma_rx_priority = 2,  // Lower priority - WRONG!
};

// CORRECT - RX priority higher
struct max_spi_init_param spi_extra = {
    .dma_tx_priority = 2,  // Lower priority
    .dma_rx_priority = 1,  // Higher priority - CORRECT
};
```

**Why?**:
- RX FIFO can overflow if not serviced quickly
- TX can wait without data loss
- Full-duplex transfers require RX serviced first
- Validation enforced in driver init

### Validate Priority in Driver Code

```c
// From maxim_spi.c
if (eparam->dma_rx_priority >= eparam->dma_tx_priority)
    return -EINVAL;  // Prevents incorrect configuration
```

### Share DMA Controller

```c
// Single DMA controller per platform
struct no_os_dma_init_param dma_init = {
    .num_ch = 8,
    .platform_ops = &max_dma_ops,
};

// Initialize once
ret = no_os_dma_init(&dma, &dma_init);

// Share across peripherals
struct max_spi_init_param spi_extra = {
    .dma_param = &dma_init,  // Reference same DMA
};

struct max_uart_init_param uart_extra = {
    .dma_param = &dma_init,  // Share DMA
};
```

## Pin Multiplexing

### Use Predefined Pin Configurations When Available

```c
// GOOD - Use driver's predefined pin sets
// Driver selects correct pins based on device_id
struct no_os_spi_init_param spi_init = {
    .device_id = 0,  // Driver handles pin selection
};

// Avoid manual pin configuration unless necessary
```

### Verify Pin Assignments in Datasheet

**Check**:
- Pin number matches alternate function
- Alternate function number (ALT1, ALT2, etc.)
- Pin conflicts with other peripherals
- Voltage compatibility

### Configure Pins After Clock Enable

```c
// CORRECT
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
MXC_GPIO_Config(&spi_pins);  // After clock enable

// WRONG
MXC_GPIO_Config(&spi_pins);  // May fail without clock
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
```

## Resource Tracking

### Use Reference Counting for Shared Peripherals

**I2C Multi-Descriptor Pattern**:
```c
// Multiple devices on same I2C bus
struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,
};

// First descriptor initializes peripheral
no_os_i2c_init(&i2c_sensor1, &i2c_init);

// Second descriptor reuses peripheral
i2c_init.slave_address = 0x76;
no_os_i2c_init(&i2c_sensor2, &i2c_init);

// Remove in reverse order or any order
no_os_i2c_remove(i2c_sensor1);
no_os_i2c_remove(i2c_sensor2);  // Last remove shuts down peripheral
```

### Track Descriptor Count

```c
// Internal tracking (driver implementation)
static uint8_t nb_created_desc[MXC_I2C_INSTANCES] = {0};

// Init increments
nb_created_desc[param->device_id]++;

// Remove decrements
nb_created_desc[desc->device_id]--;
if (nb_created_desc[desc->device_id] == 0) {
    MXC_I2C_Shutdown(handler);  // Last descriptor shuts down
}
```

### Don't Re-Initialize Active Peripherals

```c
// WRONG - Re-initializing active I2C
no_os_i2c_init(&i2c_dev1, &i2c_init);
no_os_i2c_init(&i2c_dev1, &i2c_init);  // WRONG - already initialized

// CORRECT - Remove before re-init
no_os_i2c_remove(i2c_dev1);
no_os_i2c_init(&i2c_dev1, &i2c_init);  // OK
```

## Error Handling

### Use Standard errno Codes

**Consistent Error Codes**:
```c
-EINVAL  // Invalid parameter (NULL pointer, out of range)
-ENOMEM  // Memory allocation failed
-EIO     // I/O error (communication failure)
-ENODEV  // Device not found or not initialized
-EBUSY   // Resource busy (channel in use)
-EAGAIN  // Try again (FIFO empty, no data available)
-ETIMEDOUT  // Operation timed out
```

**Examples**:
```c
// Parameter validation
if (!desc || !param)
    return -EINVAL;

// Memory allocation
dev = calloc(1, sizeof(*dev));
if (!dev)
    return -ENOMEM;

// Hardware error
if (ret < 0)
    return -EIO;
```

### Implement Cleanup Paths with goto Labels

```c
int driver_init(struct driver_dev **device, struct driver_init_param *param)
{
    int ret;
    struct driver_dev *dev;

    dev = calloc(1, sizeof(*dev));
    if (!dev)
        return -ENOMEM;

    ret = no_os_spi_init(&dev->spi, &param->spi);
    if (ret)
        goto error_spi;

    ret = no_os_gpio_get(&dev->reset_gpio, &param->reset);
    if (ret)
        goto error_gpio;

    ret = hardware_init(dev);
    if (ret)
        goto error_hw;

    *device = dev;
    return 0;

error_hw:
    no_os_gpio_remove(dev->reset_gpio);
error_gpio:
    no_os_spi_remove(dev->spi);
error_spi:
    free(dev);
    return ret;
}
```

### Validate device_id Against Instance Count

```c
// Check device_id in range
if (param->device_id >= MXC_SPI_INSTANCES)
    return -EINVAL;

// Safe to use
mxc_spi_regs_t *spi = MXC_SPI_GET_SPI(param->device_id);
```

## Family-Specific Code

### Use Conditional Compilation for Features

```c
// Check feature availability
#ifdef MXC_I2C2
    // I2C2 available (MAX32690, not MAX32660)
    case 2:
        i2c_pins = gpio_cfg_i2c2;
        break;
#endif

#ifdef MXC_DMA1
    // Dual DMA support (MAX32690)
    if (param->id == 1) {
        MAX_DMA = MXC_DMA1;
    }
#endif
```

### Check TARGET_NUM for Family-Specific Code

```c
#if TARGET_NUM == 32650
    // MAX32650-specific code
#elif TARGET_NUM == 32690
    // MAX32690-specific code
#elif TARGET_NUM == 78000
    // MAX78000-specific code
#else
    #error "Unsupported target"
#endif
```

### Test on Multiple Families When Possible

**Testing Priority**:
1. **Primary target** - Must work
2. **Reference implementation** (MAX32650) - Should work
3. **Other supported families** - Best effort

## Interrupt Management

### Clear Interrupt Flags in Handlers

```c
void GPIO0_IRQHandler(void)
{
    MXC_GPIO_Handler(0);  // HAL clears flags

    // Or manual clear
    uint32_t flags = MXC_GPIO_GetFlags(MXC_GPIO0);
    MXC_GPIO_ClearFlags(MXC_GPIO0, flags);
}
```

### Register Callbacks Before Enabling Interrupts

```c
// CORRECT order
MXC_GPIO_RegisterCallback(port, pin, callback, context);
MXC_GPIO_EnableInt(port, mask);

// WRONG order
MXC_GPIO_EnableInt(port, mask);  // May trigger before callback set
MXC_GPIO_RegisterCallback(port, pin, callback, context);
```

### Handle HAL Async Callbacks Promptly

```c
static void _uart_common_handler(mxc_uart_regs_t *uart)
{
    mxc_uart_req_t *req = &uart_irq_state[MXC_UART_GET_IDX(uart)];
    MXC_UART_AsyncHandler(uart);  // HAL handler

    // Handle new transactions immediately
    if (req->uart && ((req->rxCnt == 0 && req->rxLen != 0) ||
                     (req->txLen != 0)))
        MXC_UART_TransactionAsync(req);
}
```

## Code Organization

### Keep Platform-Specific Code in Platform Drivers

**Good Separation**:
```
drivers/
├── power/
│   └── max20370/
│       ├── max20370.c           # Device driver (platform-agnostic)
│       └── max20370.h
└── platform/
    └── maxim/
        └── max32650/
            ├── maxim_spi.c      # Platform-specific SPI
            └── maxim_init.c     # Platform initialization
```

**Anti-Pattern**:
```c
// WRONG - Platform-specific code in device driver
#ifdef MAXIM_PLATFORM
    MXC_SPI_Init(...);  // Don't do this in device driver
#endif

// CORRECT - Use platform abstraction
ret = no_os_spi_write(dev->spi, data, len);  // Platform-agnostic
```

### Use Platform Operations Structure

```c
// Platform operations
const struct no_os_spi_platform_ops max_spi_ops = {
    .init = &max_spi_init,
    .write_and_read = &max_spi_write_and_read,
    .remove = &max_spi_remove,
};

// Device driver uses platform ops
struct no_os_spi_init_param spi_init = {
    .platform_ops = &max_spi_ops,  // Select platform
};
```

## Performance Optimization

### Use Direct Register Access for High-Speed GPIO

```c
// SLOW - HAL function call overhead
for (int i = 0; i < 1000; i++) {
    MXC_GPIO_OutSet(port, pin);
    MXC_GPIO_OutClr(port, pin);
}

// FAST - Direct register access
mxc_gpio_regs_t *regs = MXC_GPIO_GET_GPIO(port);
uint32_t mask = NO_OS_BIT(pin);
for (int i = 0; i < 1000; i++) {
    regs->out_set = mask;  // Atomic set
    regs->out_clr = mask;  // Atomic clear
}
```

### Minimize HAL Calls in Critical Paths

```c
// SLOW - Multiple HAL calls
for (int i = 0; i < count; i++) {
    MXC_GPIO_OutSet(cs_port, cs_pin);
    MXC_SPI_MasterTransaction(spi, &data[i]);
    MXC_GPIO_OutClr(cs_port, cs_pin);
}

// FAST - Batch operations
MXC_GPIO_OutSet(cs_port, cs_pin);
MXC_SPI_MasterTransaction(spi, data);  // Single transaction
MXC_GPIO_OutClr(cs_port, cs_pin);
```

### Use DMA for Large Transfers

```c
// Use DMA for transfers > 64 bytes
if (transfer_size > 64) {
    struct max_spi_init_param spi_extra = {
        .dma_param = &dma_init,  // Enable DMA
    };
} else {
    // Polling mode sufficient for small transfers
}
```

## Documentation

### Document Hardware Dependencies

```c
/**
 * @brief Initialize MAX20370 device
 *
 * Hardware requirements:
 * - I2C bus at 400kHz (Fast mode)
 * - VDDIO must be 1.8V (device limitation)
 * - nRST GPIO (active low reset)
 *
 * @param device Output device descriptor
 * @param init_param Initialization parameters
 * @return 0 on success, negative error code otherwise
 */
int max20370_init(struct max20370_dev **device,
                  struct max20370_init_param *init_param);
```

### Comment Non-Obvious VDDIO Choices

```c
struct max_spi_init_param spi_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,
    // VDDIOH required: SD card spec requires 3.3V signaling,
    // but VDDIO is 1.8V for other components
};
```

### Document Platform-Specific Limitations

```c
/**
 * MAX32660 Limitations:
 * - Only 1 GPIO port (vs 3 on MAX32650)
 * - No I2C2 instance
 * - Lower max SPI speed (12MHz vs 50MHz)
 */
```

## Common Pitfalls to Avoid

### Don't Assume Default VDDIO

```c
// WRONG - Uninitialized vssel (undefined behavior)
struct max_spi_init_param spi_extra = {
    .num_slaves = 1,
};

// CORRECT - Always set explicitly
struct max_spi_init_param spi_extra = {
    .num_slaves = 1,
    .vssel = MXC_GPIO_VSSEL_VDDIO,
};
```

### Don't Skip Clock Enable

```c
// WRONG - No clock enable
ret = no_os_spi_init(&spi, &spi_init);  // May fail silently

// CORRECT - Enable clock first
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
ret = no_os_spi_init(&spi, &spi_init);
```

### Don't Reverse DMA Priorities

```c
// WRONG - TX higher priority than RX
.dma_tx_priority = 1,
.dma_rx_priority = 2,  // Will be rejected by driver

// CORRECT - RX higher priority than TX
.dma_tx_priority = 2,
.dma_rx_priority = 1,
```

### Don't Re-Initialize Shared I2C Without Tracking

```c
// WRONG - Manual I2C init breaks reference counting
MXC_I2C_Init(MXC_I2C0, I2C_MASTER_MODE, 0);  // Don't do this
no_os_i2c_init(&i2c_dev, &i2c_init);  // Driver loses track

// CORRECT - Let driver handle init
no_os_i2c_init(&i2c_dev, &i2c_init);  // Driver manages peripheral
```

### Don't Ignore Family Differences

```c
// WRONG - Assumes all families same
gpio_pins = gpio_cfg_i2c2;  // I2C2 may not exist

// CORRECT - Check availability
#ifdef MXC_I2C2
    gpio_pins = gpio_cfg_i2c2;
#else
    return -EINVAL;  // I2C2 not available on this family
#endif
```

## Summary of Key Best Practices

1. **Always set VDDIO** - Match hardware voltage levels
2. **Enable clocks first** - Before peripheral initialization
3. **RX DMA higher priority** - Lower number than TX
4. **Use reference counting** - For shared peripherals (I2C)
5. **Validate parameters** - Check device_id, NULL pointers
6. **Implement cleanup paths** - Use goto labels for error handling
7. **Family-specific code** - Use conditional compilation
8. **Clear interrupt flags** - In all interrupt handlers
9. **Document hardware deps** - VDDIO, clocks, pin assignments
10. **Test on multiple families** - When possible
