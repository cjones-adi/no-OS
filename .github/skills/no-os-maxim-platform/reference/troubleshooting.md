# Maxim Platform Troubleshooting

Common issues, debugging techniques, and solutions for Maxim platform drivers.

## No Peripheral Response

### Symptom
- SPI/I2C/UART doesn't respond
- Registers read as 0x00000000 or 0xFFFFFFFF
- Communication fails silently

### Root Causes and Solutions

#### 1. Clock Not Enabled

**Check**:
```c
if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_SPI0)) {
    pr_err("SPI0 clock not enabled\n");
    return -ENODEV;
}
```

**Fix**:
```c
// Enable clock before peripheral init
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
ret = no_os_spi_init(&spi, &spi_init);
```

#### 2. Pins Not Configured

**Check**:
```c
mxc_gpio_cfg_t pin_cfg;
// Read pin configuration
pr_info("Pin function: 0x%08X\n", pin_cfg.func);
pr_info("Pin VSSEL: %d\n", pin_cfg.vssel);
```

**Fix**:
```c
// Ensure pins configured after clock enable
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
_max_spi_config_pins(desc);  // Configure SPI pins
```

#### 3. Wrong VDDIO Voltage

**Symptom**: Communication works sometimes, fails intermittently

**Check**:
```c
// Verify voltage selection matches hardware
pr_info("SPI VSSEL: %s\n",
        (vssel == MXC_GPIO_VSSEL_VDDIO) ? "VDDIO" : "VDDIOH");
```

**Fix**:
```c
// Match to hardware design
struct max_spi_init_param spi_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // Use correct voltage rail
};
```

#### 4. Device ID Out of Range

**Check**:
```c
if (param->device_id >= MXC_SPI_INSTANCES) {
    pr_err("Invalid SPI device_id: %d (max: %d)\n",
           param->device_id, MXC_SPI_INSTANCES - 1);
    return -EINVAL;
}
```

**Fix**: Use valid device_id (0, 1, 2, etc. within range)

## DMA Issues

### DMA Transfer Doesn't Start

#### 1. Invalid Priority Configuration

**Symptom**: Init fails with -EINVAL

**Check**:
```c
pr_info("DMA priorities - TX: %d, RX: %d\n",
        dma_tx_priority, dma_rx_priority);
```

**Fix**:
```c
// RX priority must be higher (lower number)
struct max_spi_init_param spi_extra = {
    .dma_tx_priority = 2,  // Lower priority
    .dma_rx_priority = 1,  // Higher priority - CORRECT
};
```

#### 2. DMA Request Signals Not Set

**Check**:
```c
pr_info("TX DMA req: %u, RX DMA req: %u\n",
        st->dma_req_tx, st->dma_req_rx);
```

**Fix**: Verify `_max_dma_set_req()` called in init

#### 3. DMA Channel Not Available

**Check**:
```c
if (!channel->free) {
    pr_err("DMA channel %d busy\n", channel->id);
    return -EBUSY;
}
```

**Fix**: Release channels after use or increase channel count

```c
struct no_os_dma_init_param dma_init = {
    .num_ch = 8,  // Increase if needed (max varies by family)
};
```

### DMA Transfer Completes But Data Wrong

#### 1. FIFO Not Cleared

**Fix**:
```c
// Clear FIFOs before DMA transfer
spi->dma |= MXC_F_SPI_DMA_RX_FIFO_CLEAR | MXC_F_SPI_DMA_TX_FIFO_CLEAR;
```

#### 2. Wrong Transfer Size

**Check**:
```c
pr_info("Transfer size: %u bytes\n", transfer_size);
pr_info("CTRL1: 0x%08X\n", spi->ctrl1);
```

**Fix**: Verify transfer size matches buffer

## GPIO Problems

### GPIO Pin Not Changing State

#### 1. Pin Not Enabled

**Check**:
```c
mxc_gpio_regs_t *regs = MXC_GPIO_GET_GPIO(port);
pr_info("GPIO port EN: 0x%08X\n", regs->en);
pr_info("Expected mask: 0x%08X\n", NO_OS_BIT(pin));
```

**Fix**:
```c
// Enable pin as output
no_os_gpio_direction_output(gpio, NO_OS_GPIO_HIGH);
```

#### 2. Wrong Direction

**Check**:
```c
// Read current pin value
uint32_t pin_value = MXC_GPIO_InGet(port, NO_OS_BIT(pin));
pr_info("Pin %d value: %u\n", pin, pin_value);
```

**Fix**:
```c
// Set direction explicitly
no_os_gpio_direction_output(gpio, initial_state);
// Or for input
no_os_gpio_direction_input(gpio);
```

#### 3. Conflicting Pin Function

**Check**: Pin may be assigned to peripheral (SPI, I2C, etc.)

**Fix**: Remove peripheral or choose different pin

### GPIO Interrupt Not Firing

#### 1. Interrupt Not Enabled

**Check**:
```c
// Verify interrupt configuration
pr_info("IRQ enabled for pin %d: %d\n", pin,
        MXC_GPIO_IntEnabled(port, mask));
```

**Fix**:
```c
// Enable interrupt
MXC_GPIO_EnableInt(port, mask);
```

#### 2. Interrupt Flag Not Cleared

**Fix**:
```c
void GPIO0_IRQHandler(void)
{
    uint32_t flags = MXC_GPIO_GetFlags(MXC_GPIO0);
    MXC_GPIO_ClearFlags(MXC_GPIO0, flags);  // Clear all flags
    MXC_GPIO_Handler(0);
}
```

#### 3. Callback Not Registered

**Check**:
```c
// Verify callback registered
if (!action->callback) {
    pr_warn("No callback registered for GPIO IRQ\n");
}
```

**Fix**: Register callback before enabling interrupt

```c
MXC_GPIO_RegisterCallback(port, pin, callback, context);
MXC_GPIO_EnableInt(port, mask);
```

## I2C Communication Failures

### I2C Write/Read Returns Error

#### 1. Device Not Responding (NAK)

**Symptom**: Returns -EIO

**Check**:
```c
// Verify slave address
pr_info("I2C slave address: 0x%02X\n", desc->slave_address);

// Try I2C bus scan
for (uint8_t addr = 0x08; addr < 0x78; addr++) {
    if (i2c_probe(desc, addr) == 0)
        pr_info("Device found at 0x%02X\n", addr);
}
```

**Fix**:
- Verify slave address correct (7-bit vs 8-bit)
- Check pull-up resistors (4.7kΩ typical)
- Verify device powered and not in reset

#### 2. Bus Speed Too High

**Symptom**: Intermittent failures, NAKs

**Fix**:
```c
// Reduce I2C speed
struct no_os_i2c_init_param i2c_init = {
    .max_speed_hz = 100000,  // Try standard mode first
};
```

#### 3. SDA/SCL Shorted or Stuck

**Check**:
```c
// Read pin states (should be high at idle)
uint32_t scl = MXC_GPIO_InGet(i2c_port, scl_pin);
uint32_t sda = MXC_GPIO_InGet(i2c_port, sda_pin);
pr_info("I2C idle: SCL=%u SDA=%u\n", scl, sda);
```

**Fix**: Check hardware - both should be high when idle

### Multiple I2C Devices Conflict

**Symptom**: Second device init corrupts first device

**Fix**: Use multi-descriptor pattern (automatically handled)

```c
// Both share same I2C peripheral
no_os_i2c_init(&i2c_dev1, &i2c_init);
i2c_init.slave_address = 0x76;
no_os_i2c_init(&i2c_dev2, &i2c_init);
// Reference counting handles this automatically
```

## SPI Communication Failures

### SPI Transfer Returns No Data or Wrong Data

#### 1. Wrong SPI Mode

**Symptom**: Data garbled or all 0xFF/0x00

**Check**:
```c
pr_info("SPI mode: %d (CPOL=%d, CPHA=%d)\n",
        desc->mode,
        (desc->mode & 0x2) >> 1,  // CPOL
        (desc->mode & 0x1));       // CPHA
```

**Fix**: Match device datasheet (usually mode 0 or 3)

```c
struct no_os_spi_init_param spi_init = {
    .mode = NO_OS_SPI_MODE_0,  // Try different modes
};
```

#### 2. Clock Speed Too High

**Symptom**: Intermittent failures, wrong data

**Fix**:
```c
// Reduce SPI speed
struct no_os_spi_init_param spi_init = {
    .max_speed_hz = 1000000,  // Start low (1 MHz)
};
```

#### 3. CS Timing Issues

**Symptom**: First byte wrong, rest correct

**Fix**: Add CS delay

```c
struct no_os_spi_msg msg = {
    .tx_buff = tx_data,
    .rx_buff = rx_data,
    .bytes_number = len,
    .cs_delay_first = 100,  // 100ns delay after CS assert
    .cs_delay_last = 100,   // 100ns delay before CS de-assert
};
```

### SPI DMA Transfer Fails

**Check**:
1. Verify DMA priorities correct (RX > TX)
2. Check channel availability
3. Verify FIFO cleared before transfer

**Debug**:
```c
pr_info("DMA TX ch: %d (free: %d)\n", tx_ch->id, tx_ch->free);
pr_info("DMA RX ch: %d (free: %d)\n", rx_ch->id, rx_ch->free);
pr_info("DMA priorities: TX=%d RX=%d\n", dma_tx_priority, dma_rx_priority);
```

## UART Communication Failures

### UART RX No Data

#### 1. Baud Rate Mismatch

**Fix**:
```c
// Match exact baud rate
struct no_os_uart_init_param uart_init = {
    .baud_rate = 115200,  // Must match exactly
};
```

#### 2. RX FIFO Not Enabled

**Fix**:
```c
struct no_os_uart_init_param uart_init = {
    .asynchronous_rx = true,  // Enable RX FIFO
};
```

#### 3. Wrong Voltage Level

**Symptom**: Corrupted data, intermittent reception

**Fix**:
```c
// Match RS232 transceiver voltage
struct max_uart_init_param uart_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // 3.3V for RS232
};
```

### UART TX Hangs

**Symptom**: Blocks indefinitely in write

**Fix**: Check TX FIFO empty status

```c
// Verify TX empty wait logic
while (!(MXC_UART_GetStatus(uart) & MXC_F_UART_STAT_TX_EMPTY)) {
    // Add timeout
    if (timeout_elapsed())
        return -ETIMEDOUT;
}
```

## System-Level Issues

### SysTick Not Running

**Symptom**: Delays don't work, timeouts fail

**Check**:
```c
pr_info("SysTick->CTRL: 0x%08X\n", SysTick->CTRL);
pr_info("SysTick enabled: %d\n", SysTick->CTRL & SysTick_CTRL_ENABLE_Msk);
```

**Fix**:
```c
// Initialize platform
no_os_init();  // Configures SysTick

// Or manually
SysTick_Config(SystemCoreClock / 1000);  // 1ms tick
```

### Interrupt Priority Issues

**Symptom**: Interrupts not firing or interfering

**Fix**: Set priorities appropriately

```c
// Higher number = lower priority
NVIC_SetPriority(GPIO0_IRQn, 3);  // Lower priority
NVIC_SetPriority(DMA0_IRQn, 1);   // Higher priority
```

### Memory Corruption

**Symptom**: Random crashes, data corruption

**Check**:
1. Stack overflow - increase stack size
2. Buffer overruns - check array bounds
3. Double-free - verify cleanup paths
4. Uninitialized pointers

**Debug**:
```c
// Add guards
#define GUARD_VALUE 0xDEADBEEF
struct {
    uint32_t guard_start;
    uint8_t data[256];
    uint32_t guard_end;
} buffer = {
    .guard_start = GUARD_VALUE,
    .guard_end = GUARD_VALUE,
};

// Check guards
assert(buffer.guard_start == GUARD_VALUE);
assert(buffer.guard_end == GUARD_VALUE);
```

## Debugging Techniques

### Enable Debug Prints

```c
// Use pr_debug, pr_info, pr_err
#define DEBUG
#include "no_os_print_log.h"

pr_debug("SPI init: device_id=%d, speed=%u\n",
         param->device_id, param->max_speed_hz);
pr_info("Device initialized successfully\n");
pr_err("SPI init failed: %d\n", ret);
```

### Check Register Values

```c
// Read peripheral registers
mxc_spi_regs_t *spi = MXC_SPI_GET_SPI(0);
pr_info("SPI0->CTRL0: 0x%08X\n", spi->ctrl0);
pr_info("SPI0->CTRL1: 0x%08X\n", spi->ctrl1);
pr_info("SPI0->STAT: 0x%08X\n", spi->stat);
pr_info("SPI0->DMA: 0x%08X\n", spi->dma);
```

### Use Logic Analyzer

**Signals to Monitor**:
- SPI: MOSI, MISO, SCK, CS
- I2C: SDA, SCL
- UART: TX, RX
- GPIO: State changes

**Common Issues Found**:
- Wrong clock polarity/phase
- CS timing violations
- Clock speed too high
- Missing ACK on I2C

### Oscilloscope Checks

**Voltage Levels**:
- Verify VDDIO/VDDIOH voltages correct
- Check signal swing (0V to VDDIO)
- Look for overshoot/undershoot

**Timing**:
- Measure setup/hold times
- Verify clock frequency
- Check CS to clock timing

### Use Debugger Breakpoints

```c
// Set breakpoint at error return
if (ret < 0) {
    // Breakpoint here - examine variables
    pr_err("Operation failed: %d\n", ret);
    return ret;
}
```

## Family-Specific Issues

### MAX32660 (Limited Resources)

**Issues**:
- Only 1 GPIO port (vs 3 on other families)
- No I2C2/SPI2 instances
- Limited DMA channels

**Fix**: Check availability with `#ifdef`

```c
#ifndef MXC_I2C2
    #error "I2C2 not available on this target"
#endif
```

### MAX32690 (Dual DMA)

**Issue**: Wrong DMA controller selected

**Fix**:
```c
#ifdef MXC_DMA1
    // Select correct DMA
    struct no_os_dma_init_param dma_init = {
        .id = 0,  // Or 1 for DMA1
    };
#endif
```

### MAX78000 (AI Accelerator)

**Issue**: Different power domains, clock configuration

**Fix**: Consult MAX78000-specific documentation

## When to Escalate

**Contact support if**:
1. Hardware verified correct but still fails
2. Issue reproduces across multiple boards
3. Driver returns success but peripheral doesn't work
4. Suspect silicon errata

**Provide**:
- Target family (MAX32650, MAX32690, etc.)
- Full error log with debug enabled
- Minimal reproducible code
- Oscilloscope/logic analyzer captures
- Schematic (if possible)

## Quick Diagnostic Checklist

```c
// Copy this diagnostic routine
void platform_diagnostic(void)
{
    pr_info("=== Platform Diagnostic ===\n");

    // System clock
    pr_info("SystemCoreClock: %u Hz\n", SystemCoreClock);

    // SysTick
    pr_info("SysTick enabled: %d\n",
            !!(SysTick->CTRL & SysTick_CTRL_ENABLE_Msk));

    // Peripheral clocks
    pr_info("SPI0 clock: %d\n",
            MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_SPI0));
    pr_info("I2C0 clock: %d\n",
            MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_I2C0));
    pr_info("DMA clock: %d\n",
            MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_DMA));

    // GPIO states
    for (int port = 0; port < MXC_CFG_GPIO_INSTANCES; port++) {
        mxc_gpio_regs_t *gpio = MXC_GPIO_GET_GPIO(port);
        pr_info("GPIO%d: EN=0x%08X OUT=0x%08X IN=0x%08X\n",
                port, gpio->en, gpio->out, gpio->in);
    }

    pr_info("=========================\n");
}
```

## Summary

**Most Common Issues**:
1. Clock not enabled (50% of problems)
2. Wrong VDDIO voltage (20%)
3. Incorrect DMA priorities (10%)
4. Pin configuration issues (10%)
5. Wrong SPI mode or speed (10%)

**Debug Priority**:
1. Verify clocks enabled
2. Check voltage levels (VDDIO/VDDIOH)
3. Validate init parameters
4. Enable debug logging
5. Use hardware tools (scope/analyzer)
