# STM32 Platform Troubleshooting Guide

Common issues and debugging techniques for STM32 platform drivers.

## HAL Error Checking

### HAL Return Status Codes

```c
ret = HAL_SPI_Init(sdesc->hspi);
if (ret != HAL_OK) {
    pr_err("SPI init failed: %d\n", ret);
    // HAL_OK = 0       - Success
    // HAL_ERROR = 1    - Generic error
    // HAL_BUSY = 2     - Resource busy
    // HAL_TIMEOUT = 3  - Operation timeout
    return -EIO;
}
```

**Common HAL errors**:
- `HAL_ERROR` - Invalid configuration, peripheral not ready
- `HAL_BUSY` - Peripheral already in use, transfer in progress
- `HAL_TIMEOUT` - Communication timeout, peripheral not responding

---

## Clock Issues

### Issue: Peripheral Not Responding

**Symptoms**:
- HAL_Init returns HAL_ERROR
- Peripheral registers cannot be written
- Communication timeouts

**Solution**: Check if peripheral clock is enabled

```c
// Check peripheral clock enabled
if (!__HAL_RCC_SPI1_IS_CLK_ENABLED()) {
    pr_err("SPI1 clock not enabled\n");
}

// GPIO clocks must be enabled manually
__HAL_RCC_GPIOA_CLK_ENABLE();

// Peripheral clocks enabled by HAL_*_Init()
// If still not enabled, check HAL_*_Init() return value
```

### Issue: Incorrect Baud Rate / Timing

**Symptoms**:
- SPI communication errors
- I2C NACK / timeout
- UART garbled data

**Solution**: Verify clock frequencies

```c
// Check clock frequencies
uint32_t apb1 = HAL_RCC_GetPCLK1Freq();
uint32_t apb2 = HAL_RCC_GetPCLK2Freq();
pr_info("APB1: %u Hz, APB2: %u Hz\n", apb1, apb2);

// Verify prescaler calculation
uint32_t div = input_clock / desired_speed;
pr_info("Prescaler div: %u\n", div);

// Check actual baud rate
uint32_t actual_baud = input_clock / prescaler_value;
pr_info("Actual baud: %u Hz (requested: %u Hz)\n", 
        actual_baud, desired_speed);
```

---

## GPIO Issues

### Issue: GPIO Not Toggling

**Symptoms**:
- HAL_GPIO_WritePin has no effect
- Pin stuck at one level
- Oscilloscope shows no activity

**Solution**: Check GPIO configuration

```c
// Read current pin state
GPIO_PinState state = HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_5);
pr_info("PA5 state: %d\n", state);

// Check GPIO mode
uint32_t mode = (GPIOA->MODER >> (5 * 2)) & 0x3;
pr_info("PA5 mode: 0x%X (0=IN, 1=OUT, 2=AF, 3=ANALOG)\n", mode);

// Verify clock enabled
if (!__HAL_RCC_GPIOA_IS_CLK_ENABLED()) {
    pr_err("GPIOA clock not enabled\n");
}

// Check output type
uint32_t otype = (GPIOA->OTYPER >> 5) & 0x1;
pr_info("PA5 output type: %s\n", otype ? "open-drain" : "push-pull");
```

**Common causes**:
- GPIO clock not enabled
- Wrong mode (analog, input instead of output)
- Open-drain without pull-up
- Alternate function enabled

### Issue: Alternate Function Not Working

**Symptoms**:
- SPI/I2C/UART not communicating
- Peripheral initialized but no signal on pins
- GPIO configured but controlled by software

**Solution**: Verify alternate function configuration

```c
// Check alternate function setting
uint32_t afr = (GPIOA->AFR[0] >> (5 * 4)) & 0xF;  // PA5
pr_info("PA5 alternate function: AF%u\n", afr);

// Verify mode is AF
uint32_t mode = (GPIOA->MODER >> (5 * 2)) & 0x3;
if (mode != 2) {
    pr_err("PA5 not in AF mode (mode=%u)\n", mode);
}

// Check datasheet for correct AF
// PA5: AF5 = SPI1_SCK on STM32H7
if (afr != 5) {
    pr_err("PA5 AF incorrect (expected AF5, got AF%u)\n", afr);
}
```

---

## I2C Issues

### Issue: I2C NACK (Not Acknowledged)

**Symptoms**:
- HAL_I2C_Master_Transmit returns HAL_ERROR
- Error flag: HAL_I2C_ERROR_AF (Acknowledge Failure)
- Communication fails

**Solution**: Check slave address and bus

```c
// Verify slave address (7-bit or 8-bit shifted?)
pr_info("Slave address: 0x%02X (7-bit: 0x%02X)\n", 
        addr, addr >> 1);

// Check I2C bus with oscilloscope
// - SDA and SCL idle high (pull-ups present?)
// - START condition seen?
// - Slave responds with ACK?

// Enable I2C error interrupts
HAL_I2C_RegisterCallback(&hi2c, HAL_I2C_ERROR_CB_ID, i2c_error_callback);
```

**Common causes**:
- Wrong slave address (7-bit vs 8-bit)
- Slave not powered / not on bus
- Missing pull-up resistors (SDA/SCL)
- Incorrect I2C timing (H7/L4/U5)

### Issue: I2C Timing Incorrect (STM32H7/L4/U5)

**Symptoms**:
- I2C communication unreliable
- Random NAKs
- Bus hangs

**Solution**: Recalculate timing register

```c
// Use STM32CubeMX to calculate timing
// 1. Open CubeMX, select MCU
// 2. Configure clock tree (I2C clock source)
// 3. Enable I2C peripheral
// 4. Set desired speed (100/400/1000 kHz)
// 5. Copy timing value from Initialization Code

// Verify timing register
pr_info("I2C Timing: 0x%08X\n", hi2c.Init.Timing);

// Example values for STM32H7 @ 200 MHz I2C clock:
// 100 kHz:  0x307075B1
// 400 kHz:  0x00F07BFF
// 1 MHz:    0x00702991
```

---

## SPI Issues

### Issue: SPI Clock Not Generated

**Symptoms**:
- HAL_SPI_Transmit hangs
- No clock signal on SCK pin
- Data not transmitted

**Solution**: Check SPI configuration and GPIO AF

```c
// Verify SPI enabled
if (!(SPI1->CR1 & SPI_CR1_SPE)) {
    pr_err("SPI1 not enabled\n");
}

// Check GPIO alternate function for SCK
// PA5 (SPI1_SCK): should be AF5 on STM32H7
uint32_t afr = (GPIOA->AFR[0] >> (5 * 4)) & 0xF;
if (afr != 5) {
    pr_err("PA5 AF incorrect (expected AF5, got AF%u)\n", afr);
}

// Verify mode is master
if (!(SPI1->CR1 & SPI_CR1_MSTR)) {
    pr_err("SPI1 not in master mode\n");
}
```

### Issue: SPI Data Corrupted

**Symptoms**:
- Received data incorrect
- MOSI/MISO swapped
- Clock polarity/phase wrong

**Solution**: Verify SPI mode and bit order

```c
// Check SPI mode (CPOL/CPHA)
uint32_t cpol = (SPI1->CR1 & SPI_CR1_CPOL) ? 1 : 0;
uint32_t cpha = (SPI1->CR1 & SPI_CR1_CPHA) ? 1 : 0;
pr_info("SPI mode: CPOL=%u, CPHA=%u\n", cpol, cpha);
// Mode 0: CPOL=0, CPHA=0
// Mode 1: CPOL=0, CPHA=1
// Mode 2: CPOL=1, CPHA=0
// Mode 3: CPOL=1, CPHA=1

// Check bit order
uint32_t lsbfirst = (SPI1->CR1 & SPI_CR1_LSBFIRST) ? 1 : 0;
pr_info("Bit order: %s\n", lsbfirst ? "LSB first" : "MSB first");

// Verify prescaler
uint32_t br = (SPI1->CR1 >> 3) & 0x7;
uint32_t prescaler = 2 << br;
pr_info("Prescaler: %u (BR=%u)\n", prescaler, br);
```

---

## UART Issues

### Issue: UART No Data Received

**Symptoms**:
- HAL_UART_Receive times out
- RX interrupt not firing
- Transmit works, receive doesn't

**Solution**: Check UART RX configuration

```c
// Verify UART RX enabled
if (!(USART1->CR1 & USART_CR1_RE)) {
    pr_err("UART RX not enabled\n");
}

// Check GPIO alternate function for RX pin
// PA10 (USART1_RX): should be AF7 on STM32H7
uint32_t afr = (GPIOA->AFR[1] >> ((10-8) * 4)) & 0xF;
if (afr != 7) {
    pr_err("PA10 AF incorrect (expected AF7, got AF%u)\n", afr);
}

// Verify baud rate
uint32_t brr = USART1->BRR;
pr_info("UART BRR: 0x%04X\n", brr);

// Check for framing errors
if (USART1->ISR & USART_ISR_FE) {
    pr_err("UART framing error (wrong baud rate?)\n");
}
```

### Issue: UART Async RX Not Working

**Symptoms**:
- Callback not called
- FIFO empty
- Interrupt not firing

**Solution**: Verify interrupt configuration

```c
// Check NVIC enabled
if (!NVIC_GetEnableIRQ(USART1_IRQn)) {
    pr_err("UART1 interrupt not enabled in NVIC\n");
}

// Verify UART RX interrupt enabled
if (!(USART1->CR1 & USART_CR1_RXNEIE)) {
    pr_err("UART RXNE interrupt not enabled\n");
}

// Check callback registered
if (!sud->rx_callback.callback) {
    pr_err("UART RX callback not registered\n");
}

// Verify HAL_UART_Receive_IT called
// Must re-enable after each byte in callback
```

---

## DMA Issues

### Issue: DMA Not Transferring Data

**Symptoms**:
- HAL_SPI_Transmit_DMA hangs
- DMA complete callback not called
- Peripheral ready, but no data movement

**Solution**: Check DMA configuration

```c
// Check DMA state
HAL_DMA_StateTypeDef state = HAL_DMA_GetState(hdma);
pr_info("DMA state: %d\n", state);
// HAL_DMA_STATE_RESET, HAL_DMA_STATE_READY, HAL_DMA_STATE_BUSY, etc.

// Check DMA error
uint32_t error = HAL_DMA_GetError(hdma);
if (error != HAL_DMA_ERROR_NONE) {
    pr_err("DMA error: 0x%08X\n", error);
}

// Verify DMA enabled
if (!(DMA1_Stream0->CR & DMA_SxCR_EN)) {
    pr_err("DMA stream not enabled\n");
}

// Check peripheral DMA enabled
if (!(SPI1->CR2 & SPI_CR2_TXDMAEN)) {
    pr_err("SPI TX DMA not enabled\n");
}
```

### Issue: DMA Transfer Incomplete

**Symptoms**:
- Partial data transferred
- DMA stops mid-transfer
- Transfer count not zero

**Solution**: Check DMA configuration and alignment

```c
// Check remaining transfer count
uint32_t ndtr = DMA1_Stream0->NDTR;
pr_info("DMA remaining: %u items\n", ndtr);

// Verify memory/peripheral alignment
// Word (32-bit) transfers require 4-byte alignment
if (((uint32_t)src_addr & 0x3) && (alignment == DMA_MDATAALIGN_WORD)) {
    pr_err("Source address not word-aligned: 0x%08X\n", src_addr);
}

// Check FIFO configuration (F4/F7)
if (DMA1_Stream0->FCR & DMA_SxFCR_FEIE) {
    pr_info("DMA FIFO enabled\n");
}
```

---

## Interrupt Issues

### Issue: Interrupt Not Firing

**Symptoms**:
- Callback never called
- Expected event doesn't trigger
- Peripheral generates event but no ISR

**Solution**: Verify NVIC and interrupt enables

```c
// Check NVIC enabled
if (!NVIC_GetEnableIRQ(EXTI0_IRQn)) {
    pr_err("EXTI0 interrupt not enabled in NVIC\n");
    HAL_NVIC_EnableIRQ(EXTI0_IRQn);
}

// Check peripheral interrupt enable
if (!(TIM1->DIER & TIM_DIER_UIE)) {
    pr_err("TIM1 update interrupt not enabled\n");
}

// Verify interrupt priority
uint32_t priority = HAL_NVIC_GetPriority(TIM1_UP_IRQn);
pr_info("TIM1 interrupt priority: %u\n", priority);

// Check if interrupt pending
if (NVIC_GetPendingIRQ(TIM1_UP_IRQn)) {
    pr_info("TIM1 interrupt pending (not being serviced)\n");
}
```

### Issue: Callback Context Lost

**Symptoms**:
- Callback executes but context is NULL
- Segmentation fault in callback
- Cannot access descriptor

**Solution**: Verify callback registration

```c
// Ensure context passed during registration
sud->rx_callback.callback = uart_rx_callback;
sud->rx_callback.ctx = descriptor;  // IMPORTANT - pass context

// In callback, verify context
void uart_rx_callback(void *context)
{
    if (!context) {
        pr_err("Callback context is NULL\n");
        return;
    }

    struct no_os_uart_desc *d = context;
    // Use descriptor
}
```

---

## Build Issues

### Issue: Undefined Reference to HAL Functions

**Symptoms**:
```
undefined reference to `HAL_SPI_Init'
undefined reference to `HAL_GPIO_Init'
```

**Solution**: Link HAL library

```makefile
# Add HAL source files to build
SRCS += $(STM32_HAL_DIR)/Src/stm32h7xx_hal_spi.c
SRCS += $(STM32_HAL_DIR)/Src/stm32h7xx_hal_gpio.c
SRCS += $(STM32_HAL_DIR)/Src/stm32h7xx_hal_rcc.c

# Or link prebuilt HAL library
LIBS += -lhal_stm32h7
```

### Issue: Multiple Definition of HAL Callbacks

**Symptoms**:
```
multiple definition of `HAL_UART_RxCpltCallback'
```

**Solution**: Use weak callbacks or conditional compilation

```c
// Option 1: Weak callbacks (default)
__weak void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    // Default implementation
}

// Option 2: Conditional compilation
#ifdef HAL_UART_MODULE_ENABLED
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    // Implementation
}
#endif
```

---

## Runtime Issues

### Issue: Hard Fault / Segmentation Fault

**Symptoms**:
- Program crashes
- Debugger stops at HardFault_Handler
- Stack overflow

**Solution**: Debug stack and pointers

```c
// Check NULL pointers before dereferencing
if (!descriptor) {
    pr_err("Descriptor is NULL\n");
    return -EINVAL;
}

if (!descriptor->extra) {
    pr_err("Extra is NULL\n");
    return -EINVAL;
}

// Verify memory allocations
descriptor = calloc(1, sizeof(*descriptor));
if (!descriptor) {
    pr_err("Failed to allocate descriptor\n");
    return -ENOMEM;
}

// Check stack usage
#include "stm32h7xx_hal.h"
uint32_t stack_ptr;
__asm volatile ("mov %0, sp" : "=r" (stack_ptr));
pr_info("Stack pointer: 0x%08X\n", stack_ptr);
```

### Issue: Watchdog Reset

**Symptoms**:
- System resets periodically
- Watchdog timeout message
- Long blocking operations

**Solution**: Feed watchdog or disable during development

```c
// Feed watchdog in long operations
HAL_IWDG_Refresh(&hiwdg);

// Or disable watchdog during development
// (via STM32CubeMX or option bytes)

// Use DMA/interrupts instead of blocking calls
// DON'T: HAL_SPI_Transmit(hspi, data, 4096, HAL_MAX_DELAY);  // Blocks
// DO:    HAL_SPI_Transmit_DMA(hspi, data, 4096);             // Non-blocking
```

---

## Debugging Techniques

### Enable Debug Output

```c
// Use no-OS print utilities
#include "no_os_print_log.h"

pr_info("SPI init: device_id=%u, speed=%u Hz\n", 
        param->device_id, param->max_speed_hz);
pr_err("SPI init failed: ret=%d\n", ret);
pr_debug("Prescaler: div=%u, prescaler=0x%X\n", div, prescaler);
```

### Use Debugger Breakpoints

```c
// Set breakpoint at error paths
ret = HAL_SPI_Init(sdesc->hspi);
if (ret != HAL_OK) {
    // BREAKPOINT HERE - inspect hspi configuration
    __asm volatile ("bkpt #0");
    return -EIO;
}
```

### Dump Register Values

```c
// Dump SPI registers
pr_info("SPI1->CR1:  0x%08X\n", SPI1->CR1);
pr_info("SPI1->CR2:  0x%08X\n", SPI1->CR2);
pr_info("SPI1->SR:   0x%08X\n", SPI1->SR);

// Dump GPIO registers
pr_info("GPIOA->MODER:  0x%08X\n", GPIOA->MODER);
pr_info("GPIOA->OTYPER: 0x%08X\n", GPIOA->OTYPER);
pr_info("GPIOA->AFR[0]: 0x%08X\n", GPIOA->AFR[0]);
```

### Use Logic Analyzer / Oscilloscope

- **SPI**: Monitor SCK, MOSI, MISO, CS signals
- **I2C**: Check SDA, SCL for START/STOP/ACK/NACK
- **UART**: Verify baud rate, framing, parity
- **GPIO**: Confirm pin toggling, voltage levels

---

## Common Error Codes

| Error Code | Meaning | Common Causes |
|------------|---------|---------------|
| -EINVAL | Invalid argument | NULL pointer, out-of-range value |
| -ENOMEM | Out of memory | calloc/malloc failed |
| -EIO | I/O error | HAL function returned HAL_ERROR |
| -ENODEV | No such device | device_id invalid, peripheral not available |
| -EBUSY | Device busy | Peripheral already initialized |
| -ETIMEDOUT | Timeout | Communication timeout, peripheral not responding |

---

## Quick Debugging Checklist

1. **Clock enabled?** - Check `__HAL_RCC_*_IS_CLK_ENABLED()`
2. **HAL return checked?** - Verify HAL_OK returned
3. **GPIO configured?** - Check mode, AF, speed, pull
4. **Interrupt enabled?** - Verify NVIC and peripheral IE bits
5. **Callback registered?** - Check callback and context not NULL
6. **DMA configured?** - Verify stream/channel, direction, alignment
7. **Timing correct?** - Check prescaler, baud rate, I2C timing
8. **Family differences?** - Use conditional compilation for F4 vs H7

---

## Related Resources

- **STM32 HAL Documentation** - ST Microelectronics
- **STM32 Reference Manual** - Peripheral register details
- **STM32 Datasheet** - GPIO alternate functions, electrical specs
- **STM32CubeMX** - Clock configuration, I2C timing calculator
- `/no-os-debugging` - General no-OS debugging techniques
