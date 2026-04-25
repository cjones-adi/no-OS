# SPI Troubleshooting Guide

Common SPI issues, symptoms, causes, and solutions.

## No Data Received

### Symptom

- MISO always reads 0xFF or 0x00
- No response from device
- All transfers appear to succeed but data is wrong

### Possible Causes and Solutions

#### 1. Wiring Issue - MISO Not Connected

**Check:**
```c
// Read a known register multiple times
uint8_t data[2];
for (int i = 0; i < 5; i++) {
    data[0] = CHIP_ID_REG | 0x80;
    data[1] = 0x00;
    no_os_spi_write_and_read(spi_desc, data, 2);
    printf("Read %d: 0x%02X\n", i, data[1]);
}
// If always 0xFF or 0x00 → wiring issue
```

**Solution:**
- Verify MISO connection with multimeter (continuity test)
- Check for cold solder joints
- Verify correct pin assignment in platform init

#### 2. SPI Mode Mismatch

**Check device datasheet for required CPOL/CPHA:**

```c
// Try all SPI modes systematically
const enum no_os_spi_mode modes[] = {
    NO_OS_SPI_MODE_0,
    NO_OS_SPI_MODE_1,
    NO_OS_SPI_MODE_2,
    NO_OS_SPI_MODE_3,
};

for (int i = 0; i < 4; i++) {
    spi_init.mode = modes[i];
    no_os_spi_init(&spi_desc, &spi_init);
    
    // Try reading chip ID
    if (device_read_chip_id(spi_desc, &chip_id) == 0) {
        printf("Mode %d works! Chip ID: 0x%02X\n", i, chip_id);
    }
    
    no_os_spi_remove(spi_desc);
}
```

**Solution:**
- Match SPI mode to datasheet specification exactly
- Verify with oscilloscope if unsure

#### 3. CS Polarity Wrong

**Symptom:** Device never responds, CS appears inverted

**Check:**
```c
// Maxim platform - try both polarities
max_extra.polarity = 0;  // Active-low (standard)
// vs
max_extra.polarity = 1;  // Active-high (uncommon)
```

**Solution:**
- Most devices use active-low CS (polarity = 0)
- Check datasheet for CS polarity requirement
- Verify with oscilloscope (CS should be LOW during transfer)

#### 4. Clock Speed Too Fast

**Symptom:** Intermittent errors, corrupted data

**Check:**
```c
// Reduce speed and retry
spi_init.max_speed_hz = 100000;  // 100 kHz
ret = no_os_spi_init(&spi_desc, &spi_init);
```

**Solution:**
- Start with 100 kHz for debugging
- Check device datasheet for maximum SPI clock
- Consider PCB trace length (long traces = lower max speed)
- Verify actual clock frequency with oscilloscope

#### 5. Device Not Powered or Initialized

**Check:**
```c
// Verify power supply voltage with multimeter
// Check enable/reset pins if applicable

// Add initialization sequence before first SPI transfer
no_os_gpio_set_value(enable_gpio, 1);  // Enable device
no_os_mdelay(10);                       // Wait for power-up
no_os_gpio_set_value(reset_gpio, 1);   // Release reset
no_os_mdelay(100);                      // Wait for device ready
```

**Solution:**
- Verify supply voltage is within datasheet spec
- Check enable/reset GPIO control
- Add appropriate power-up delays

## Data Corruption

### Symptom

- Occasionally wrong values
- First byte correct, subsequent bytes wrong
- Random bit errors

### Possible Causes and Solutions

#### 1. Setup/Hold Time Violations

**Symptom:** Inconsistent data, fails at higher speeds

**Solution:**
```c
// Add CS delays
struct no_os_spi_msg msg = {
    .tx_buff = data,
    .rx_buff = data,
    .bytes_number = len,
    .cs_delay_first = 100,   // 100ns setup time
    .cs_delay_last = 50,     // 50ns hold time
    .cs_change = 1,
};
no_os_spi_transfer(spi_desc, &msg, 1);
```

#### 2. Noise/Crosstalk

**Symptom:** Errors increase with wire length or nearby switching signals

**Solution:**
- Shorten SPI wires
- Add ground wire between SPI signals
- Route SPI away from noisy signals (PWM, power lines)
- Lower clock speed
- Add series resistors (22-100Ω) on SCLK/MOSI/MISO

#### 3. Wrong Bit Order

**Check:**
```c
// Try both bit orders
spi_init.bit_order = NO_OS_SPI_BIT_ORDER_MSB_FIRST;  // Most common
// vs
spi_init.bit_order = NO_OS_SPI_BIT_ORDER_LSB_FIRST;  // Uncommon
```

**Solution:**
- Most devices use MSB-first
- Check datasheet
- Verify with oscilloscope (watch bit pattern)

#### 4. Buffer Alignment (DMA)

**Symptom:** Corruption only with DMA transfers

**Solution:**
```c
// Ensure buffers are properly aligned
uint8_t tx_buffer[256] __attribute__((aligned(4)));
uint8_t rx_buffer[256] __attribute__((aligned(4)));

// Or allocate dynamically (usually aligned)
uint8_t *tx_buffer = malloc(256);
uint8_t *rx_buffer = malloc(256);
```

## CS Not Toggling

### Symptom

- CS stuck HIGH or LOW
- CS toggles but at wrong times
- Multiple devices respond simultaneously

### Possible Causes and Solutions

#### 1. Hardware vs Software CS Conflict

**Check platform configuration:**

```c
// Mbed - ensure software CS if needed
mbed_extra.use_sw_csb = true;  // Software CS control

// Maxim - CS configured in GPIO init
// STM32 - May use hardware CS by default
```

**Solution:**
- Use software CS for fine control
- Check platform documentation for CS control method

#### 2. Missing cs_change Flag

**Problem:**
```c
// CS never deasserts between messages
struct no_os_spi_msg msgs[] = {
    { .tx_buff = cmd, .bytes_number = 1, .cs_change = 0 },  // OK
    { .rx_buff = data, .bytes_number = 4, .cs_change = 0 }, // MISSING
    //                                                ↑ Should be 1
};
```

**Solution:**
```c
// Set cs_change = 1 on last message
msgs[1].cs_change = 1;  // Deassert CS after transfer
```

#### 3. Wrong CS Pin Number

**Check:**
```c
// Verify CS pin assignment
spi_init.chip_select = 0;  // Using CS0

// Check platform schematic - is device connected to CS0?
// If device on CS1, use:
spi_init.chip_select = 1;
```

#### 4. GPIO CS Not Configured

**For software CS:**
```c
// Configure CS GPIO before SPI init
struct no_os_gpio_init_param cs_gpio_param = {
    .number = CS_PIN,
    .platform_ops = &gpio_ops,
};
struct no_os_gpio_desc *cs_gpio;
no_os_gpio_get_optional(&cs_gpio, &cs_gpio_param);
if (cs_gpio)
    no_os_gpio_direction_output(cs_gpio, 1);  // Set HIGH (idle)
```

## Bus Contention (Multi-Slave)

### Symptom

- Random failures when using multiple devices
- Works when using one device, fails with two
- Occasional bus lockup

### Possible Causes and Solutions

#### 1. Different device_id for Same Bus

**Problem:**
```c
// BAD - Same physical bus, different device_id
spi_init_adc.device_id = 0;   // SPI0
spi_init_dac.device_id = 1;   // SPI1 (wrong!)
```

**Solution:**
```c
// GOOD - Same device_id for same physical bus
spi_init_adc.device_id = 0;   // SPI0
spi_init_dac.device_id = 0;   // SPI0 (same bus)
spi_init_adc.chip_select = 0; // CS0
spi_init_dac.chip_select = 1; // CS1
```

#### 2. Mutex Not Working

**Check:**
```c
// Verify bus mutex exists
if (spi_desc->bus->mutex == NULL) {
    printf("ERROR: Bus mutex not initialized!\n");
}

// Check if platform supports mutex
// Some bare-metal platforms may not have mutex implementation
```

**Solution:**
- Ensure platform implements `no_os_mutex_init()`
- Add application-level locking if platform mutex unavailable

#### 3. Bypassing Mutex in Custom Code

**Problem:**
```c
// BAD - Direct platform call bypasses mutex
spi_desc->platform_ops->write_and_read(spi_desc, data, len);
```

**Solution:**
```c
// GOOD - Use generic API (includes mutex)
no_os_spi_write_and_read(spi_desc, data, len);
```

## DMA Transfer Fails

### Symptom

- DMA transfer returns error
- Polling works but DMA doesn't
- System hangs during DMA transfer

### Possible Causes and Solutions

#### 1. DMA Not Initialized

**Check:**
```c
// Maxim platform - DMA must be initialized
struct max_spi_init_param max_extra = {
    .dma_param = &dma_init,  // Required for DMA
    .dma_tx_priority = 0,
    .dma_rx_priority = 0,
};
```

**Solution:**
- Initialize DMA in platform extras
- Check if platform supports DMA for SPI

#### 2. Buffer Not in DMA-Accessible Memory

**Problem:**
```c
// Stack buffer may not be DMA-accessible
uint8_t buffer[256];
no_os_spi_transfer_dma(spi_desc, &msg, 1);  // May fail
```

**Solution:**
```c
// Allocate in heap (usually DMA-accessible)
uint8_t *buffer = malloc(256);
no_os_spi_transfer_dma(spi_desc, &msg, 1);
free(buffer);

// Or use static global
static uint8_t dma_buffer[256];
```

#### 3. Buffer Not Aligned

**Symptom:** DMA error or hardfault

**Solution:**
```c
// Ensure proper alignment (4-byte or 8-byte)
uint8_t tx_buffer[256] __attribute__((aligned(8)));
uint8_t rx_buffer[256] __attribute__((aligned(8)));
```

#### 4. DMA Priority Conflict

**Check:**
```c
// Adjust DMA channel priorities
max_extra.dma_tx_priority = 1;  // Lower priority
max_extra.dma_rx_priority = 0;  // Higher priority
```

## Platform Porting Issues

### Symptom

- Build errors
- Link errors
- Runtime crashes
- Functions not implemented

### Possible Causes and Solutions

#### 1. Missing Platform Ops Implementation

**Error:**
```
undefined reference to `myplatform_spi_init'
```

**Solution:**
```c
// Implement all required platform ops
const struct no_os_spi_platform_ops myplatform_spi_ops = {
    .init = &myplatform_spi_init,
    .write_and_read = &myplatform_spi_write_and_read,
    .transfer = &myplatform_spi_transfer,
    .remove = &myplatform_spi_remove,
};
```

#### 2. Vendor HAL Errors

**Check vendor HAL return codes:**
```c
int32_t myplatform_spi_init(...)
{
    HAL_StatusTypeDef hal_ret;
    
    hal_ret = HAL_SPI_Init(&hspi);
    if (hal_ret != HAL_OK) {
        printf("HAL_SPI_Init failed: %d\n", hal_ret);
        return -EIO;  // Convert to no-OS error code
    }
    
    return 0;
}
```

#### 3. Pin Configuration Wrong

**Verify GPIO mux settings:**
```c
// STM32 example - configure SPI pins
GPIO_InitTypeDef GPIO_InitStruct = {0};
GPIO_InitStruct.Pin = GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_7;
GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
GPIO_InitStruct.Pull = GPIO_NOPULL;
GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
GPIO_InitStruct.Alternate = GPIO_AF5_SPI1;
HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
```

#### 4. Clock Not Enabled

**Enable peripheral clock:**
```c
// STM32 example
__HAL_RCC_SPI1_CLK_ENABLE();
__HAL_RCC_GPIOA_CLK_ENABLE();
```

## Debugging Tools and Techniques

### 1. Logic Analyzer Checklist

Connect logic analyzer to SPI bus and verify:

- [ ] Clock frequency matches `max_speed_hz` (or closest divisor)
- [ ] Clock idle state matches mode (CPOL)
- [ ] Data sampled on correct edge (CPHA)
- [ ] CS asserted before first clock, deasserted after last clock
- [ ] Data on MOSI matches expected command/data
- [ ] Data on MISO contains valid device response
- [ ] CS timing meets datasheet setup/hold requirements

### 2. Oscilloscope Measurements

Measure with oscilloscope:

- **Clock frequency**: Should match requested speed
- **Clock edges**: Clean, no ringing or overshoot
- **Signal levels**: 0V / 3.3V (or 5V) - no intermediate voltages
- **Rise/fall times**: < 10% of clock period
- **CS timing**: Meets datasheet specifications

### 3. Software Debug Prints

```c
#define SPI_DEBUG 1

#if SPI_DEBUG
#define SPI_DBG(fmt, ...) printf("[SPI] " fmt "\n", ##__VA_ARGS__)
#else
#define SPI_DBG(fmt, ...)
#endif

int device_write_reg(struct device_desc *dev, uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg, val};
    int ret;

    SPI_DBG("Write reg 0x%02X = 0x%02X", reg, val);
    
    ret = no_os_spi_write_and_read(dev->spi_desc, data, 2);
    
    if (ret)
        SPI_DBG("Write failed: %d", ret);
    else
        SPI_DBG("Write OK");
    
    return ret;
}
```

### 4. Register Dump

```c
void debug_dump_spi_registers(struct device_desc *dev)
{
    uint8_t val;
    int i;

    printf("\n=== SPI Register Dump ===\n");
    for (i = 0; i < 0x20; i++) {
        if (device_read_reg(dev, i, &val) == 0)
            printf("[0x%02X] = 0x%02X\n", i, val);
        else
            printf("[0x%02X] = <ERROR>\n", i);
    }
    printf("========================\n\n");
}
```

### 5. Loopback Test

```c
// Short MOSI to MISO for loopback test
int spi_loopback_test(struct no_os_spi_desc *spi)
{
    uint8_t test_pattern[] = {0x00, 0xFF, 0xAA, 0x55, 0x12, 0x34};
    uint8_t buffer[6];
    int i;

    printf("SPI Loopback Test (short MOSI to MISO)\n");
    
    for (i = 0; i < 6; i++) {
        buffer[i] = test_pattern[i];
    }
    
    no_os_spi_write_and_read(spi, buffer, 6);
    
    for (i = 0; i < 6; i++) {
        printf("TX: 0x%02X  RX: 0x%02X  %s\n",
               test_pattern[i], buffer[i],
               (test_pattern[i] == buffer[i]) ? "PASS" : "FAIL");
    }
    
    return 0;
}
```

## Quick Diagnostic Checklist

When SPI isn't working, check in this order:

1. [ ] Power supply voltage correct (measure with multimeter)
2. [ ] Wiring connections correct (MOSI, MISO, SCLK, CS)
3. [ ] SPI mode matches datasheet (CPOL, CPHA)
4. [ ] Clock speed within device limits (try 100 kHz first)
5. [ ] CS polarity correct (usually active-low)
6. [ ] Device initialized and out of reset
7. [ ] Platform-specific extras configured correctly
8. [ ] Verify with logic analyzer/oscilloscope
9. [ ] Try reading chip ID as first test
10. [ ] Check datasheet for initialization sequence

## Common Error Codes

| Error Code | Meaning | Common Cause |
|------------|---------|--------------|
| 0 | Success | Operation completed |
| -EINVAL (-22) | Invalid argument | NULL pointer, bad parameter |
| -ENOMEM (-12) | Out of memory | malloc() failed |
| -ENODEV (-19) | No device | Wrong bus, chip ID mismatch |
| -EIO (-5) | I/O error | Transfer failed, timeout |
| -EBUSY (-16) | Device busy | Bus locked, DMA active |
| -ETIMEDOUT (-110) | Timeout | Transfer too slow, no response |
| -ENOTSUP (-95) | Not supported | Feature not available on platform |
