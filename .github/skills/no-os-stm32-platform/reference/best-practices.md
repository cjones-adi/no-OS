# STM32 Platform Best Practices

STM32-specific best practices for no-OS platform driver development.

## HAL Library Usage

### 1. Use HAL for Abstraction

**DO**:
```c
// Let HAL handle low-level details
ret = HAL_SPI_Init(sdesc->hspi);
if (ret != HAL_OK)
    return -EIO;

// Leverage HAL callbacks for event-driven design
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    _common_uart_callback(huart, NO_OS_EVT_UART_RX_COMPLETE);
}
```

**DON'T**:
```c
// Don't bypass HAL to access registers directly
SPI1->CR1 |= SPI_CR1_SPE;  // AVOID - use HAL_SPI_Init() instead

// Don't mix LL and HAL APIs
LL_SPI_Enable(SPI1);  // AVOID - stick to HAL
```

**Why**: HAL provides abstraction across STM32 families. Direct register access breaks portability.

---

## Clock Management

### 2. Enable GPIO Clocks Before Configuration

**DO**:
```c
// Enable clock first
__HAL_RCC_GPIOA_CLK_ENABLE();
extra->port = GPIOA;

// Then configure GPIO
HAL_GPIO_Init(extra->port, &extra->gpio_config);
```

**DON'T**:
```c
// Don't configure GPIO before enabling clock
HAL_GPIO_Init(GPIOA, &gpio_config);  // WRONG - clock not enabled
__HAL_RCC_GPIOA_CLK_ENABLE();
```

**Why**: GPIO configuration requires peripheral clock to be enabled first.

### 3. Peripheral Clocks Enabled Automatically

**DO**:
```c
// HAL_*_Init() enables peripheral clock automatically
ret = HAL_SPI_Init(sdesc->hspi);   // Enables SPI clock
ret = HAL_I2C_Init(&xdesc->hi2c);  // Enables I2C clock
ret = HAL_UART_Init(sud->huart);   // Enables UART clock
```

**DON'T**:
```c
// Don't manually enable peripheral clocks
__HAL_RCC_SPI1_CLK_ENABLE();  // UNNECESSARY - HAL_SPI_Init does this
HAL_SPI_Init(sdesc->hspi);
```

**Why**: HAL initialization functions handle peripheral clock enabling internally.

### 4. Query Clock Frequencies Dynamically

**DO**:
```c
// Query clock at runtime
uint32_t apb1_freq = HAL_RCC_GetPCLK1Freq();
uint32_t apb2_freq = HAL_RCC_GetPCLK2Freq();
uint32_t sysclk = HAL_RCC_GetSysClockFreq();

// Use queried frequency for calculations
uint32_t div = apb2_freq / spi_speed;
```

**DON'T**:
```c
// Don't hardcode clock frequencies
#define APB2_FREQ 100000000  // WRONG - not portable
uint32_t div = APB2_FREQ / spi_speed;
```

**Why**: Clock frequencies vary by family and configuration. Always query dynamically.

---

## GPIO Alternate Functions

### 5. Check Datasheet for AF Assignment

**DO**:
```c
// Check STM32 datasheet for correct AF
struct stm32_gpio_init_param gpio_extra = {
    .alternate = GPIO_AF5_SPI1,  // PA5 = SPI1_SCK on STM32H7
};

// Verify in datasheet: PA5 alternate functions
// AF5 = SPI1_SCK ✓
```

**DON'T**:
```c
// Don't guess AF numbers
struct stm32_gpio_init_param gpio_extra = {
    .alternate = GPIO_AF3_SPI1,  // WRONG - AF3 is not SPI1 on PA5
};
```

**Why**: Alternate function assignments vary by pin and family. Always verify in datasheet.

### 6. Use GPIO_MODE_AF_PP for Alternate Functions

**DO**:
```c
// Set mode to AF when using alternate functions
extra->gpio_config.Alternate = pextra->alternate;
extra->gpio_config.Mode = GPIO_MODE_AF_PP;  // Alternate Function Push-Pull

HAL_GPIO_Init(extra->port, &extra->gpio_config);
```

**DON'T**:
```c
// Don't leave mode as output when using AF
extra->gpio_config.Alternate = GPIO_AF5_SPI1;
extra->gpio_config.Mode = GPIO_MODE_OUTPUT_PP;  // WRONG
```

**Why**: GPIO must be in AF mode for peripheral control.

### 7. Set Alternate Before HAL_GPIO_Init

**DO**:
```c
// Configure alternate function before init
extra->gpio_config.Pin = NO_OS_BIT(param->number);
extra->gpio_config.Mode = GPIO_MODE_AF_PP;
extra->gpio_config.Alternate = pextra->alternate;  // Set before init

HAL_GPIO_Init(extra->port, &extra->gpio_config);
```

**DON'T**:
```c
// Don't set alternate after init
HAL_GPIO_Init(extra->port, &extra->gpio_config);
extra->gpio_config.Alternate = pextra->alternate;  // TOO LATE
```

**Why**: HAL_GPIO_Init applies the configuration, including alternate function.

---

## I2C Timing (STM32H7/L4/U5)

### 8. Use STM32CubeMX Timing Calculator

**DO**:
```c
// Use STM32CubeMX to calculate timing register
// 1. Open STM32CubeMX
// 2. Select MCU and configure clocks
// 3. Enable I2C peripheral
// 4. Set I2C speed (100 kHz, 400 kHz, 1 MHz)
// 5. Copy generated timing value

struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x00F07BFF,  // From CubeMX for 400 kHz @ 200 MHz I2C clock
};
```

**DON'T**:
```c
// Don't guess timing values
struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x12345678,  // WRONG - random value
};
```

**Why**: I2C timing register is complex and family/clock-specific. Use CubeMX calculator.

### 9. Pre-Calculate and Store Timing Values

**DO**:
```c
// Pre-calculate timing for common speeds
#define I2C_TIMING_100KHZ  0x307075B1  // 100 kHz
#define I2C_TIMING_400KHZ  0x00F07BFF  // 400 kHz
#define I2C_TIMING_1MHZ    0x00702991  // 1 MHz

struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = I2C_TIMING_400KHZ,
};
```

**DON'T**:
```c
// Don't calculate at runtime (not straightforward)
uint32_t timing = calculate_i2c_timing(400000);  // Complex formula
```

**Why**: Timing calculation is complex. Pre-calculate and document values.

---

## DMA Configuration

### 10. Understand Family-Specific DMA

**DO**:
```c
// Use conditional compilation for family differences
#if defined(STM32F2) || defined(STM32F4) || defined(STM32F7)
    // F2/F4/F7: Channel in Init structure
    sdma_ch->hdma->Init.Channel = sdma_ch->ch_num;
#else
    // H7/U5: Channel in Instance
    sdma_ch->hdma->Instance = sdma_ch->ch_num;
#endif
```

**DON'T**:
```c
// Don't hardcode for one family
sdma_ch->hdma->Init.Channel = sdma_ch->ch_num;  // Breaks on H7/U5
```

**Why**: DMA configuration differs between families. Use conditional compilation.

### 11. Set Appropriate DMA Priority

**DO**:
```c
// Higher priority for time-critical peripherals
// RX DMA typically higher than TX
sdma_ch->hdma->Init.Priority = DMA_PRIORITY_HIGH;  // RX
sdma_ch->hdma->Init.Priority = DMA_PRIORITY_MEDIUM;  // TX

// Balance priorities to avoid starvation
```

**DON'T**:
```c
// Don't set all DMA to highest priority
sdma_ch->hdma->Init.Priority = DMA_PRIORITY_VERY_HIGH;  // Everything
```

**Why**: DMA priority affects real-time performance. Balance across channels.

---

## NVIC Interrupt Configuration

### 12. Understand NVIC Priority

**DO**:
```c
// Lower number = higher priority (0 is highest)
HAL_NVIC_SetPriority(UART1_IRQn, 1, 0);  // High priority
HAL_NVIC_SetPriority(UART2_IRQn, 2, 0);  // Medium priority
HAL_NVIC_SetPriority(UART3_IRQn, 3, 0);  // Lower priority

// Group priorities with NVIC_SetPriorityGrouping()
NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4);
```

**DON'T**:
```c
// Don't assume higher number = higher priority
HAL_NVIC_SetPriority(UART1_IRQn, 15, 0);  // WRONG - lowest priority
```

**Why**: NVIC uses inverted priority (0 = highest). Critical interrupts get priority 0-3.

### 13. Register Callbacks Properly

**DO**:
```c
// Register callback with proper context
sud->rx_callback.callback = uart_rx_callback;
sud->rx_callback.ctx = descriptor;  // Pass context
sud->rx_callback.event = NO_OS_EVT_UART_RX_COMPLETE;
sud->rx_callback.handle = sud->huart;  // Pass HAL handle

no_os_irq_register_callback(sud->nvic, descriptor->irq_id,
                            &sud->rx_callback);
```

**DON'T**:
```c
// Don't forget context or handle
sud->rx_callback.callback = uart_rx_callback;
sud->rx_callback.ctx = NULL;  // WRONG - callback can't access descriptor
```

**Why**: Callbacks need context to access descriptor and HAL handle for operations.

---

## Error Handling

### 14. Check HAL Return Values

**DO**:
```c
ret = HAL_SPI_Init(sdesc->hspi);
if (ret != HAL_OK) {
    pr_err("SPI init failed: %d\n", ret);
    // HAL_OK = 0, HAL_ERROR = 1, HAL_BUSY = 2, HAL_TIMEOUT = 3
    free(sdesc);
    free(descriptor);
    return -EIO;
}
```

**DON'T**:
```c
// Don't ignore HAL return values
HAL_SPI_Init(sdesc->hspi);  // WRONG - no error check
```

**Why**: HAL functions can fail. Always check return values and handle errors.

### 15. Convert HAL Errors to errno Codes

**DO**:
```c
// Convert HAL status to standard errno
ret = HAL_I2C_Init(&xdesc->hi2c);
if (ret != HAL_OK)
    return -EIO;  // I/O error

// Use appropriate errno codes
if (!descriptor)
    return -ENOMEM;  // Out of memory

if (param->device_id > MAX_SPI)
    return -EINVAL;  // Invalid argument
```

**DON'T**:
```c
// Don't return HAL status codes directly
ret = HAL_SPI_Init(sdesc->hspi);
return ret;  // WRONG - HAL_OK=0, HAL_ERROR=1 (not standard errno)
```

**Why**: no-OS uses standard errno codes. Convert HAL status to errno.

### 16. Implement Cleanup Paths

**DO**:
```c
int32_t stm32_spi_init(struct no_os_spi_desc **desc,
                       const struct no_os_spi_init_param *param)
{
    descriptor = calloc(1, sizeof(*descriptor));
    if (!descriptor)
        return -ENOMEM;

    sdesc = calloc(1, sizeof(*sdesc));
    if (!sdesc) {
        free(descriptor);  // Clean up
        return -ENOMEM;
    }

    ret = HAL_SPI_Init(sdesc->hspi);
    if (ret != HAL_OK) {
        free(sdesc);       // Clean up
        free(descriptor);
        return -EIO;
    }

    return 0;
}
```

**DON'T**:
```c
// Don't leak memory on error paths
int32_t stm32_spi_init(...)
{
    descriptor = calloc(1, sizeof(*descriptor));
    sdesc = calloc(1, sizeof(*sdesc));

    ret = HAL_SPI_Init(sdesc->hspi);
    if (ret != HAL_OK)
        return -EIO;  // WRONG - memory leak
}
```

**Why**: Clean up allocated resources on error paths to prevent memory leaks.

---

## Family Portability

### 17. Use Conditional Compilation

**DO**:
```c
// Use family-specific macros
#if defined(STM32F4) || defined(STM32F1) || defined(STM32F2) || defined(STM32L1)
    xdesc->hi2c.Init.ClockSpeed = param->max_speed_hz;
    xdesc->hi2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
#else
    xdesc->hi2c.Init.Timing = i2cinit->i2c_timing;
#endif
```

**DON'T**:
```c
// Don't assume one configuration works everywhere
xdesc->hi2c.Init.ClockSpeed = param->max_speed_hz;  // Breaks on H7
```

**Why**: Configuration differs between families. Use conditional compilation.

### 18. Test on Multiple Families

**DO**:
- Test driver on STM32F4 (older family)
- Test driver on STM32H7 (newer family)
- Verify peripheral instances exist (#if defined(SPI4))
- Check datasheet for family-specific features

**DON'T**:
- Only test on one family
- Assume all families have same peripherals
- Ignore conditional compilation warnings

**Why**: Subtle differences exist between families. Test on representative samples.

### 19. Abstract Family-Specific Code

**DO**:
```c
// Abstract family differences in helper functions
static int get_timer_base(uint32_t device_id, TIM_TypeDef **base,
                         uint32_t *clk_freq)
{
    uint32_t apb2_freq = HAL_RCC_GetPCLK2Freq();
    *clk_freq = HAL_RCC_GetPCLK1Freq();

    switch (device_id) {
    case 1:  *base = TIM1;  *clk_freq = apb2_freq;  break;
    case 2:  *base = TIM2;  break;
    // ... family-specific timer mapping
    }

    return 0;
}
```

**DON'T**:
```c
// Don't scatter family-specific code everywhere
#if defined(STM32H7)
    *base = TIM1;
#elif defined(STM32F4)
    *base = TIM1;
#endif
// Repeated in multiple places
```

**Why**: Centralize family-specific logic for maintainability.

---

## Static Handle Management

### 20. Use Static Tables for Shared Peripherals

**DO**:
```c
// Global static table for peripheral instances
static SPI_HandleTypeDef hspi_table[SPI_MAX_BUS_NUMBER + 1];

// During init - point to static handle
sdesc->hspi = &hspi_table[param->device_id];

// Multiple descriptors can share same peripheral
```

**DON'T**:
```c
// Don't dynamically allocate HAL handles
sdesc->hspi = malloc(sizeof(SPI_HandleTypeDef));  // AVOID
```

**Why**: Static tables avoid dynamic allocation, allow descriptor sharing, and simplify cleanup.

---

## Performance Optimization

### 21. Use DMA for Large Transfers

**DO**:
```c
// Use DMA for transfers > 64 bytes
if (len > 64) {
    HAL_SPI_Transmit_DMA(hspi, data, len);
} else {
    HAL_SPI_Transmit(hspi, data, len, timeout);
}
```

**DON'T**:
```c
// Don't use polling for large transfers
HAL_SPI_Transmit(hspi, data, 4096, timeout);  // Slow, blocks CPU
```

**Why**: DMA frees CPU for other tasks during large transfers.

### 22. Use Interrupt-Driven UART RX

**DO**:
```c
// Enable asynchronous RX for non-blocking reads
struct no_os_uart_init_param uart_init = {
    .asynchronous_rx = true,  // Enable interrupt-driven RX
};

// Read from FIFO (non-blocking)
ret = no_os_uart_read(uart, buffer, 64);
```

**DON'T**:
```c
// Don't use blocking UART reads for continuous reception
while (1) {
    HAL_UART_Receive(huart, &c, 1, HAL_MAX_DELAY);  // Blocks forever
}
```

**Why**: Interrupt-driven RX allows CPU to do other work while waiting for data.

---

## Summary of Key Practices

1. **HAL Usage**: Use HAL, avoid direct register access
2. **Clocks**: Enable GPIO clocks before config, query frequencies dynamically
3. **GPIO AF**: Check datasheet, set AF before init, use AF mode
4. **I2C Timing**: Use CubeMX calculator for H7/L4/U5
5. **DMA**: Understand family differences, set appropriate priorities
6. **NVIC**: Lower number = higher priority, register callbacks properly
7. **Errors**: Check HAL returns, convert to errno, implement cleanup
8. **Portability**: Use conditional compilation, test on multiple families
9. **Handles**: Use static tables for shared peripherals
10. **Performance**: Use DMA for large transfers, interrupt-driven UART
