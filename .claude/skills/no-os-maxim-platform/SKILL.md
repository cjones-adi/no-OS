---
name: no-os-maxim-platform
description: 'Complete guide to Maxim (MAX32xxx, MAX78xxx) platform drivers for no-OS embedded systems. Quick-start patterns for SPI/I2C/UART/GPIO with VDDIO configuration, DMA, and platform initialization.'
---

# no-OS Maxim Platform Drivers

Quick-start guide for Maxim (MAX32xxx, MAX78000) platform driver development in the no-OS framework.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/platform-apis.md**:
- User asks: "API implementation", "how to use SPI/I2C/UART", "function signatures"
- Questions about: specific driver functions, register access, HAL integration
- Need: complete API reference for all peripherals, implementation details

**Triggers to read reference/initialization.md**:
- User asks: "platform init", "clock setup", "how to initialize", "startup sequence"
- Mentions: no_os_init, MXC_SYS_ClockEnable, SysTick, peripheral reset
- Questions about: clock gating, resource tracking, reference counting
- Need: detailed initialization sequences, clock management patterns

**Triggers to read reference/peripherals.md**:
- User asks: "pin configuration", "how to configure DMA", "peripheral settings"
- Mentions: MXC_GPIO_Config, prescaler, FIFO, speed modes, flow control
- Questions about: pin multiplexing, DMA priorities, multi-device buses
- Need: detailed peripheral configuration patterns, hardware-specific settings

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "recommendations", "how should I", "design patterns"
- Questions about: VDDIO selection, error handling, resource management
- Need: platform-specific guidelines, common patterns, pitfalls to avoid

**Triggers to read reference/troubleshooting.md**:
- Build/runtime errors in user output
- User says: "doesn't work", "not responding", "error", "fails", "issue"
- Specific issues: no peripheral response, DMA problems, GPIO not working
- Questions about: debugging, why communication fails, voltage issues

---

## When to Use This Skill

- Developing drivers for Maxim MAX32xxx or MAX78xxx MCUs
- Configuring SPI, I2C, UART, GPIO, Timer/PWM, DMA peripherals
- Setting up platform initialization and clock management
- Troubleshooting VDDIO voltage issues or peripheral communication
- Implementing DMA-based transfers
- Managing shared resources (multi-device I2C buses)

## Supported MCU Families

**MAX32xxx Series**:
- MAX32650, MAX32655, MAX32660, MAX32662, MAX32665
- MAX32670, MAX32672, MAX32690

**MAX78xxx Series**:
- MAX78000 (AI/ML accelerator)

**Common Features**:
- Arm Cortex-M4F core
- Maxim SDK (MSDK) HAL integration
- Shared DMA controller
- VDDIO/VDDIOH voltage selection
- Pin multiplexing via MXC_GPIO_Config

---

## Platform Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│              Maxim Platform Architecture                 │
└──────────────────────────────────────────────────────────┘

         ┌────────────────────────────────┐
         │    no-OS Framework Layer       │
         │  (Platform-agnostic)           │
         │  no_os_spi, no_os_i2c, etc.    │
         └───────────┬────────────────────┘
                     │
        ┌────────────┴───────────┐
        │                        │
   ┌────▼────────┐        ┌──────▼──────┐
   │ Maxim       │        │  Common     │
   │ Platform    │        │  Drivers    │
   │ Drivers     │        │  (DMA)      │
   │             │        │             │
   │ max32650/   │        │ common/     │
   │ max32690/   │        │             │
   └─────┬───────┘        └──────┬──────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼──────────────┐
         │   Maxim MSDK HAL         │
         │   MXC_SPI, MXC_I2C, etc. │
         │   Hardware Abstraction   │
         └──────────────────────────┘
```

---

## Quick Start Guide

### 1. Platform Initialization

```c
int main(void)
{
    int ret;

    // 1. Initialize platform (SysTick for 1ms tick)
    ret = no_os_init();
    if (ret)
        return ret;

    // 2. Enable peripheral clocks
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_I2C0);
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_DMA);

    // 3. Initialize peripherals
    // ... (see examples below)

    return 0;
}
```

### 2. SPI Initialization

```c
// SPI with DMA
struct no_os_dma_init_param dma_init = {
    .num_ch = 8,
    .platform_ops = &max_dma_ops,
};
no_os_dma_init(&dma, &dma_init);

struct max_spi_init_param spi_extra = {
    .num_slaves = 1,
    .polarity = MXC_SPI_TSCONTROL_ACTIVE_LO,
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // Match hardware voltage
    .dma_param = &dma_init,
    .dma_tx_priority = 2,   // Lower priority
    .dma_rx_priority = 1,   // Higher priority (CRITICAL!)
};

struct no_os_spi_init_param spi_init = {
    .device_id = 0,
    .max_speed_hz = 10000000,  // 10 MHz
    .mode = NO_OS_SPI_MODE_0,
    .extra = &spi_extra,
    .platform_ops = &max_spi_ops,
};

ret = no_os_spi_init(&spi, &spi_init);
```

**Critical**: RX DMA priority must be higher (lower number) than TX!

### 3. I2C Initialization

```c
struct max_i2c_init_param i2c_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // Match hardware voltage
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,  // Fast mode (400 kHz)
    .slave_address = 0x48,
    .extra = &i2c_extra,
    .platform_ops = &max_i2c_ops,
};

ret = no_os_i2c_init(&i2c, &i2c_init);

// Multiple devices on same bus (reference counting handled automatically)
i2c_init.slave_address = 0x76;
ret = no_os_i2c_init(&i2c2, &i2c_init);
```

### 4. UART Initialization

```c
struct max_uart_init_param uart_extra = {
    .flow = MAX_UART_FLOW_DIS,           // No flow control
    .vssel = MXC_GPIO_VSSEL_VDDIOH,      // 3.3V for RS232
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .asynchronous_rx = true,  // Enable RX FIFO
    .extra = &uart_extra,
    .platform_ops = &max_uart_ops,
};

ret = no_os_uart_init(&uart, &uart_init);
```

### 5. GPIO Initialization

```c
struct max_gpio_init_param gpio_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // Match hardware voltage
};

struct no_os_gpio_init_param gpio_init = {
    .port = 0,
    .number = 5,
    .pull = NO_OS_PULL_NONE,
    .extra = &gpio_extra,
    .platform_ops = &max_gpio_ops,
};

ret = no_os_gpio_get(&gpio, &gpio_init);
ret = no_os_gpio_direction_output(gpio, NO_OS_GPIO_HIGH);
```

---

## Critical Platform Concepts

### VDDIO Voltage Selection

**Most Critical Setting**: Always set `vssel` to match hardware design!

```c
// VDDIO rail voltage selection
MXC_GPIO_VSSEL_VDDIO   // Use VDDIO rail (1.8V or 3.3V - depends on hardware)
MXC_GPIO_VSSEL_VDDIOH  // Use VDDIOH rail (always 3.3V)
```

**Decision Tree**:
```
Is VDDIO 1.8V?
├─ YES + peripheral needs 1.8V → MXC_GPIO_VSSEL_VDDIO
├─ YES + peripheral needs 3.3V → MXC_GPIO_VSSEL_VDDIOH
└─ NO (VDDIO is 3.3V)          → MXC_GPIO_VSSEL_VDDIO
```

**Examples**:
```c
// 1.8V SPI flash on 1.8V VDDIO system
.vssel = MXC_GPIO_VSSEL_VDDIO,

// SD card (3.3V) on 1.8V VDDIO + 3.3V VDDIOH system
.vssel = MXC_GPIO_VSSEL_VDDIOH,

// RS232 (3.3V) with VDDIOH
.vssel = MXC_GPIO_VSSEL_VDDIOH,
```

### Clock Management

**Required Before Peripheral Init**:
```c
// Enable peripheral clock
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);

// Optional: Reset for clean state
MXC_SYS_Reset_Periph(MXC_SYS_PERIPH_RESET_SPI0);

// Then initialize peripheral
no_os_spi_init(&spi, &spi_init);
```

**Check Clock Status**:
```c
if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_SPI0)) {
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
}
```

### DMA Priority Rule

**Critical Requirement**: RX priority must be higher (lower number) than TX

```c
// WRONG - Will be rejected
.dma_tx_priority = 1,
.dma_rx_priority = 2,  // Lower priority - WRONG!

// CORRECT
.dma_tx_priority = 2,  // Lower priority
.dma_rx_priority = 1,  // Higher priority - CORRECT
```

**Why?**: RX FIFO can overflow if not serviced quickly; TX can wait without data loss.

### Pin Multiplexing

**GPIO Configuration Structure**:
```c
mxc_gpio_cfg_t pin_config = {
    .port = MXC_GPIO_GET_GPIO(0),           // Port 0
    .mask = MXC_GPIO_PIN_5,                 // Pin 5
    .func = MXC_GPIO_FUNC_ALT1,             // Alternate function 1
    .pad = MXC_GPIO_PAD_NONE,               // No pull resistor
    .vssel = MXC_GPIO_VSSEL_VDDIO,          // Voltage level
};

MXC_GPIO_Config(&pin_config);
```

**Pin Functions**:
- `MXC_GPIO_FUNC_IN/OUT` - GPIO
- `MXC_GPIO_FUNC_ALT1` - SPI, I2C, UART (primary)
- `MXC_GPIO_FUNC_ALT2` - Timer, PWM
- `MXC_GPIO_FUNC_ALT3` - Additional functions

Check datasheet for pin-specific function mapping.

---

## Quick Reference: Driver Locations

```
drivers/platform/maxim/
├── common/
│   └── maxim_dma.c/h         # Shared DMA controller
├── max32650/                  # Reference implementation
│   ├── maxim_init.c           # Platform initialization
│   ├── maxim_spi.c/h          # SPI driver
│   ├── maxim_i2c.c/h          # I2C driver
│   ├── maxim_uart.c/h         # UART driver
│   ├── maxim_gpio.c/h         # GPIO driver
│   ├── maxim_gpio_irq.c/h     # GPIO interrupts
│   ├── maxim_timer.c/h        # Timer/counter
│   ├── maxim_pwm.c/h          # PWM generation
│   ├── maxim_irq.c/h          # IRQ controller
│   └── maxim_delay.c          # Delay functions
└── max32655/                  # Same structure for each family
└── max32660/
└── max32690/
└── max78000/
```

---

## Common Use Cases

### SPI with DMA for High-Speed Transfers

```c
// 10 MHz SPI with DMA
struct max_spi_init_param spi_extra = {
    .num_slaves = 1,
    .polarity = MXC_SPI_TSCONTROL_ACTIVE_LO,
    .vssel = MXC_GPIO_VSSEL_VDDIO,
    .dma_param = &dma_init,
    .dma_tx_priority = 2,
    .dma_rx_priority = 1,
};

struct no_os_spi_init_param spi_init = {
    .device_id = 0,
    .max_speed_hz = 10000000,
    .mode = NO_OS_SPI_MODE_0,
    .extra = &spi_extra,
    .platform_ops = &max_spi_ops,
};
```

### I2C Multi-Device Bus

```c
// Multiple sensors on same I2C bus
struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,
    .extra = &i2c_extra,
};

no_os_i2c_init(&i2c_temp, &i2c_init);  // Temperature sensor

i2c_init.slave_address = 0x76;
no_os_i2c_init(&i2c_pressure, &i2c_init);  // Pressure sensor

// Both share same I2C peripheral (reference counting automatic)
```

### UART with Async RX

```c
// Non-blocking UART with RX FIFO
struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .asynchronous_rx = true,  // Enable RX FIFO
    .extra = &uart_extra,
};

no_os_uart_init(&uart, &uart_init);

// Non-blocking read
uint8_t buffer[64];
int ret = no_os_uart_read(uart, buffer, 64);
if (ret == -EAGAIN) {
    // No data available
}
```

---

## Essential Patterns

### Error Handling with Cleanup

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

    ret = no_os_gpio_get(&dev->gpio, &param->gpio);
    if (ret)
        goto error_gpio;

    *device = dev;
    return 0;

error_gpio:
    no_os_spi_remove(dev->spi);
error_spi:
    free(dev);
    return ret;
}
```

### Resource Tracking (I2C Multi-Descriptor)

```c
// Automatic reference counting (internal to driver)
// First descriptor initializes peripheral
no_os_i2c_init(&i2c_dev1, &i2c_init);

// Subsequent descriptors reuse peripheral
i2c_init.slave_address = 0x76;
no_os_i2c_init(&i2c_dev2, &i2c_init);

// Remove in any order
no_os_i2c_remove(i2c_dev1);
no_os_i2c_remove(i2c_dev2);  // Last remove shuts down peripheral
```

---

## Common Issues & Quick Fixes

**No peripheral response**:
```c
// Fix 1: Enable clock first
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);

// Fix 2: Check VDDIO voltage
.vssel = MXC_GPIO_VSSEL_VDDIO,  // Match hardware
```

**DMA init fails with -EINVAL**:
```c
// Fix: RX priority must be higher (lower number)
.dma_tx_priority = 2,
.dma_rx_priority = 1,  // Higher priority
```

**I2C communication fails**:
```c
// Fix 1: Reduce speed
.max_speed_hz = 100000,  // Standard mode

// Fix 2: Check pull-up resistors (4.7kΩ typical)
```

**GPIO not changing state**:
```c
// Fix: Set direction
no_os_gpio_direction_output(gpio, NO_OS_GPIO_HIGH);
```

**See**: `reference/troubleshooting.md` for complete troubleshooting guide.

---

## Family-Specific Considerations

### Check Feature Availability

```c
#ifdef MXC_I2C2
    // I2C2 available (MAX32690, not MAX32660)
#endif

#ifdef MXC_DMA1
    // Dual DMA (MAX32690)
#endif
```

### Validate device_id

```c
if (param->device_id >= MXC_SPI_INSTANCES)
    return -EINVAL;
```

---

## Best Practices Summary

1. **Always set VDDIO** - Match `vssel` to hardware voltage design
2. **Enable clocks first** - Before peripheral initialization
3. **RX DMA higher priority** - Lower number than TX (critical!)
4. **Use reference counting** - For shared I2C buses (automatic)
5. **Validate parameters** - Check device_id, NULL pointers
6. **Implement cleanup paths** - Use goto labels for error handling
7. **Family-specific code** - Use `#ifdef` for conditional features
8. **Document VDDIO choice** - Comment why specific voltage selected

---

## Reference Documentation

**When to read each file** (use Read tool):

### reference/platform-apis.md
Complete API reference for all Maxim platform drivers: SPI, I2C, UART, GPIO, Timer/PWM, DMA, IRQ. Includes function signatures, register access patterns, and HAL integration details.

### reference/initialization.md
Platform initialization sequences: clock management, SysTick setup, pin multiplexing (MXC_GPIO_Config), VDDIO configuration, resource tracking patterns.

### reference/peripherals.md
Detailed peripheral configuration: pin selection, speed modes, DMA priorities, FIFO management, prescaler calculation, multi-device patterns.

### reference/best-practices.md
Platform-specific best practices: VDDIO selection guidelines, clock management, DMA configuration, error handling, resource tracking, code organization, performance optimization.

### reference/troubleshooting.md
Common issues and solutions: no peripheral response, DMA problems, GPIO issues, I2C/SPI/UART failures, debugging techniques, family-specific issues.

---

## Related Resources

- `/no-os-spi` - Generic SPI driver interface
- `/no-os-i2c` - Generic I2C driver interface  
- `/no-os-uart` - Generic UART driver interface
- `/no-os-gpio` - Generic GPIO driver interface
- `/no-os-debugging` - Debugging techniques
- Maxim Integrated SDK documentation (MSDK)

---

## Key Takeaways

- **VDDIO is critical** - Always match hardware voltage design
- **Clock before init** - Enable peripheral clocks first
- **RX > TX for DMA** - RX priority must be higher (lower number)
- **Reference counting** - I2C multi-descriptor pattern automatic
- **Family differences** - Check feature availability with `#ifdef`
- **Read reference docs** - Complete details available when needed

**Quick Start**: Enable clocks → Set VDDIO → Configure DMA priorities → Initialize peripheral → Handle errors with goto cleanup
