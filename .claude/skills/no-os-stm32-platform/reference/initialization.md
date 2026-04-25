# STM32 Platform Initialization Sequences

Complete reference for platform initialization, clock management, and GPIO alternate function configuration.

## RCC Clock Management

### Clock Enable Macros

```c
// GPIO Port Clock Enable
__HAL_RCC_GPIOA_CLK_ENABLE();
__HAL_RCC_GPIOB_CLK_ENABLE();
__HAL_RCC_GPIOC_CLK_ENABLE();
// ... GPIOD-GPIOK

// Peripheral clocks (handled internally by HAL_*_Init)
// HAL_SPI_Init() enables SPI clock
// HAL_I2C_Init() enables I2C clock
// HAL_UART_Init() enables UART clock
```

### Clock Frequency Retrieval

```c
// Get APB clock frequencies
uint32_t apb1_freq = HAL_RCC_GetPCLK1Freq();  // TIM2-7, I2C, SPI2-3, UART2-3
uint32_t apb2_freq = HAL_RCC_GetPCLK2Freq();  // TIM1, TIM8, SPI1, UART1
uint32_t sysclk = HAL_RCC_GetSysClockFreq();  // System clock
```

### Clock Tree (STM32H7 Example)

```
HSE/HSI → PLL → System Clock (e.g., 400 MHz)
    ├── AHB (200 MHz) → GPIO, DMA, XSPI
    ├── APB1 (100 MHz) → TIM2-7, I2C, SPI2-3, UART2-3
    └── APB2 (200 MHz) → TIM1, TIM8, SPI1, UART1, ADC
```

### Clock Initialization Example

```c
// GPIO clocks are enabled during GPIO init
static int32_t _gpio_init(struct no_os_gpio_desc *desc,
                         const struct no_os_gpio_init_param *param)
{
    // Enable GPIO port clock
    if (param->port == 0) {
        __HAL_RCC_GPIOA_CLK_ENABLE();
        extra->port = GPIOA;
    }
#ifdef GPIOB
    else if (param->port == 1) {
        __HAL_RCC_GPIOB_CLK_ENABLE();
        extra->port = GPIOB;
    }
#endif
    // ... rest of ports

    HAL_GPIO_Init(extra->port, &extra->gpio_config);
    return 0;
}
```

---

## GPIO Alternate Functions

### Alternate Function Assignment

```c
struct stm32_gpio_init_param {
    uint32_t alternate;  // GPIO_AF0 through GPIO_AF15
};

// Applied during GPIO configuration
extra->gpio_config.Alternate = pextra->alternate;
extra->gpio_config.Mode = GPIO_MODE_AF_PP;  // Alternate Function Push-Pull
```

### Common Alternate Functions (STM32H7)

```c
GPIO_AF0   // System functions (JTAG, SWDIO, etc.)
GPIO_AF1   // TIM1/2, LPTIM
GPIO_AF2   // TIM3/4/5, SAI
GPIO_AF3   // TIM8, LPTIM2
GPIO_AF4   // I2C
GPIO_AF5   // SPI
GPIO_AF6   // SPI5
GPIO_AF7   // USART
GPIO_AF8   // UART4-8
GPIO_AF9   // TIMERS
GPIO_AF10  // QUADSPI
GPIO_AF11  // COMP/OPAMP
GPIO_AF12  // FMC
GPIO_AF13  // DCMI
GPIO_AF14  // Reserved
GPIO_AF15  // EVENTOUT
```

### GPIO Initialization with Alternate Function

```c
struct stm32_gpio_init_param gpio_extra = {
    .alternate = GPIO_AF7_USART1,  // UART1 TX
};

struct no_os_gpio_init_param gpio_init = {
    .port = 0,  // GPIOA
    .number = 9,  // PA9
    .pull = NO_OS_PULL_NONE,
    .extra = &gpio_extra,
    .platform_ops = &stm32_gpio_ops,
};

ret = no_os_gpio_get(&gpio_tx, &gpio_init);
ret = no_os_gpio_direction_output(gpio_tx, NO_OS_GPIO_HIGH);
```

---

## Family-Specific Configuration

### Conditional Compilation for I2C

```c
#if defined(STM32F4) || defined(STM32F1) || defined(STM32F2) || defined(STM32L1)
    // Older families: ClockSpeed parameter
    xdesc->hi2c.Init.ClockSpeed = param->max_speed_hz;
    xdesc->hi2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
#else
    // Newer families (H7, L4, U5, G4): Timing register
    xdesc->hi2c.Init.Timing = i2cinit->i2c_timing;
#endif
```

### DMA Channel vs Stream (Family Differences)

```c
#if defined(STM32F2) || defined(STM32F4) || defined(STM32F7)
    // F2/F4/F7: Channel in Init structure
    sdma_ch->hdma->Init.Channel = sdma_ch->ch_num;
#else
    // Newer families: Channel in Instance
    sdma_ch->hdma->Instance = sdma_ch->ch_num;
#endif
```

---

## Peripheral Instance Mapping

### SPI Instance Mapping

```c
// Map device_id to SPI instance
switch (param->device_id) {
#if defined(SPI1)
    case 1: sdesc->hspi->Instance = SPI1; break;
#endif
#if defined(SPI2)
    case 2: sdesc->hspi->Instance = SPI2; break;
#endif
#if defined(SPI3)
    case 3: sdesc->hspi->Instance = SPI3; break;
#endif
#if defined(SPI4)
    case 4: sdesc->hspi->Instance = SPI4; break;
#endif
#if defined(SPI5)
    case 5: sdesc->hspi->Instance = SPI5; break;
#endif
#if defined(SPI6)
    case 6: sdesc->hspi->Instance = SPI6; break;
#endif
    default:
        return -EINVAL;
}
```

### I2C Instance Mapping

```c
// Map device_id to I2C instance
switch (param->device_id) {
    case 1: base = I2C1; break;
    case 2: base = I2C2; break;
    case 3: base = I2C3; break;
#if defined(I2C4)
    case 4: base = I2C4; break;
#endif
    default:
        return -EINVAL;
}

xdesc->hi2c.Instance = base;
```

### UART Instance Mapping

```c
// Map device_id to UART instance
switch (param->device_id) {
#if defined(USART1)
    case 1: sud->huart->Instance = USART1; break;
#endif
#if defined(USART2)
    case 2: sud->huart->Instance = USART2; break;
#endif
#if defined(USART3)
    case 3: sud->huart->Instance = USART3; break;
#endif
#if defined(UART4)
    case 4: sud->huart->Instance = UART4; break;
#endif
#if defined(UART5)
    case 5: sud->huart->Instance = UART5; break;
#endif
#if defined(USART6)
    case 6: sud->huart->Instance = USART6; break;
#endif
#if defined(UART7)
    case 7: sud->huart->Instance = UART7; break;
#endif
#if defined(UART8)
    case 8: sud->huart->Instance = UART8; break;
#endif
    default:
        return -EINVAL;
}
```

### Timer Instance Mapping

```c
static int get_timer_base(uint32_t device_id, TIM_TypeDef **base,
                         uint32_t *clk_freq)
{
    uint32_t apb2_freq = HAL_RCC_GetPCLK2Freq();
    *clk_freq = HAL_RCC_GetPCLK1Freq();  // Default APB1

    switch (device_id) {
    case 1:  *base = TIM1;  *clk_freq = apb2_freq;  break;  // TIM1 on APB2
    case 2:  *base = TIM2;  break;   // TIM2-7 on APB1
    case 3:  *base = TIM3;  break;
    case 4:  *base = TIM4;  break;
    case 5:  *base = TIM5;  break;
    case 6:  *base = TIM6;  break;
    case 7:  *base = TIM7;  break;
    case 8:  *base = TIM8;  *clk_freq = apb2_freq;  break;
    case 9:  *base = TIM9;  *clk_freq = apb2_freq;  break;
    case 10: *base = TIM10; *clk_freq = apb2_freq;  break;
    case 11: *base = TIM11; *clk_freq = apb2_freq;  break;
    case 12: *base = TIM12; break;
    case 13: *base = TIM13; break;
    case 14: *base = TIM14; break;
#if defined(TIM15)
    case 15: *base = TIM15; *clk_freq = apb2_freq;  break;
#endif
#if defined(TIM16)
    case 16: *base = TIM16; *clk_freq = apb2_freq;  break;
#endif
#if defined(TIM17)
    case 17: *base = TIM17; *clk_freq = apb2_freq;  break;
#endif
    default:
        return -EINVAL;
    }

    return 0;
}
```

---

## Static Handle Management

### SPI Handle Table

```c
// Global static table for peripheral instances
static SPI_HandleTypeDef hspi_table[SPI_MAX_BUS_NUMBER + 1];

// During init:
struct stm32_spi_desc {
    SPI_HandleTypeDef *hspi;  // Points to hspi_table[device_id]
};

// Avoids dynamic allocation, allows multiple SPI descriptors
sdesc->hspi = &hspi_table[param->device_id];
```

**Why static tables?**
- Avoids dynamic memory allocation
- Allows multiple descriptors to share same peripheral instance
- HAL requires stable handle addresses
- Simplifies cleanup on error paths

### I2C Handle (Direct Embedding)

```c
struct stm32_i2c_desc {
    I2C_HandleTypeDef hi2c;  // HAL I2C handle (not pointer, directly embedded)
};
```

**I2C uses direct embedding** instead of a table because:
- Each I2C descriptor typically maps 1:1 with peripheral
- Simpler memory model
- No need for shared handle management

---

## Initialization Sequences

### Complete SPI Initialization

```c
int32_t stm32_spi_init(struct no_os_spi_desc **desc,
                       const struct no_os_spi_init_param *param)
{
    struct no_os_spi_desc *descriptor;
    struct stm32_spi_desc *sdesc;
    
    // 1. Allocate descriptor
    descriptor = calloc(1, sizeof(*descriptor));
    if (!descriptor)
        return -ENOMEM;

    // 2. Allocate platform-specific descriptor
    sdesc = calloc(1, sizeof(*sdesc));
    if (!sdesc) {
        free(descriptor);
        return -ENOMEM;
    }

    // 3. Get static handle from table
    sdesc->hspi = &hspi_table[param->device_id];

    // 4. Map device_id to peripheral instance
    switch (param->device_id) {
        case 1: sdesc->hspi->Instance = SPI1; break;
        case 2: sdesc->hspi->Instance = SPI2; break;
        // ... more instances
        default: 
            free(sdesc);
            free(descriptor);
            return -EINVAL;
    }

    // 5. Calculate prescaler from max_speed_hz
    uint32_t div = sdesc->input_clock / param->max_speed_hz;
    uint32_t prescaler;
    switch (div) {
        case 0 ... 2:     prescaler = SPI_BAUDRATEPRESCALER_2;   break;
        case 3 ... 4:     prescaler = SPI_BAUDRATEPRESCALER_4;   break;
        case 5 ... 8:     prescaler = SPI_BAUDRATEPRESCALER_8;   break;
        // ... more cases
    }

    // 6. Configure HAL handle
    sdesc->hspi->Init.Mode = SPI_MODE_MASTER;
    sdesc->hspi->Init.Direction = SPI_DIRECTION_2LINES;
    sdesc->hspi->Init.DataSize = SPI_DATASIZE_8BIT;
    sdesc->hspi->Init.BaudRatePrescaler = prescaler;
    // ... more configuration

    // 7. Initialize HAL peripheral
    ret = HAL_SPI_Init(sdesc->hspi);
    if (ret != HAL_OK) {
        free(sdesc);
        free(descriptor);
        return -EIO;
    }

    // 8. Link descriptors
    descriptor->extra = sdesc;
    *desc = descriptor;

    return 0;
}
```

### Complete I2C Initialization

```c
static int32_t stm32_i2c_init(struct no_os_i2c_desc **desc,
                              const struct no_os_i2c_init_param *param)
{
    struct no_os_i2c_desc *descriptor;
    struct stm32_i2c_desc *xdesc;
    
    // 1. Allocate descriptor
    descriptor = calloc(1, sizeof(*descriptor));
    if (!descriptor)
        return -ENOMEM;

    // 2. Allocate platform-specific descriptor
    xdesc = calloc(1, sizeof(*xdesc));
    if (!xdesc) {
        free(descriptor);
        return -ENOMEM;
    }

    // 3. Map device_id to I2C instance
    I2C_TypeDef *base;
    switch (param->device_id) {
        case 1: base = I2C1; break;
        case 2: base = I2C2; break;
        case 3: base = I2C3; break;
        default:
            free(xdesc);
            free(descriptor);
            return -EINVAL;
    }
    xdesc->hi2c.Instance = base;

    // 4. Configure based on family
#if defined(STM32F4) || defined(STM32F1) || defined(STM32F2) || defined(STM32L1)
    // Older families: Direct clock speed
    xdesc->hi2c.Init.ClockSpeed = param->max_speed_hz;
    xdesc->hi2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
#else
    // Newer families: Timing register
    struct stm32_i2c_init_param *i2cinit = param->extra;
    xdesc->hi2c.Init.Timing = i2cinit->i2c_timing;
#endif

    // 5. Configure common parameters
    xdesc->hi2c.Init.OwnAddress1 = 0;
    xdesc->hi2c.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    xdesc->hi2c.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    xdesc->hi2c.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    xdesc->hi2c.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;

    // 6. Initialize HAL peripheral
    ret = HAL_I2C_Init(&xdesc->hi2c);
    if (ret != HAL_OK) {
        free(xdesc);
        free(descriptor);
        return -EIO;
    }

    // 7. Link descriptors
    descriptor->extra = xdesc;
    *desc = descriptor;

    return 0;
}
```

### Complete GPIO Initialization

```c
static int32_t _gpio_init(struct no_os_gpio_desc *desc,
                         const struct no_os_gpio_init_param *param)
{
    struct stm32_gpio_desc *extra;
    struct stm32_gpio_init_param *pextra = param->extra;

    // 1. Allocate platform descriptor
    extra = calloc(1, sizeof(*extra));
    if (!extra)
        return -ENOMEM;

    // 2. Enable GPIO port clock and map port
    if (param->port == 0) {
        __HAL_RCC_GPIOA_CLK_ENABLE();
        extra->port = GPIOA;
    }
#ifdef GPIOB
    else if (param->port == 1) {
        __HAL_RCC_GPIOB_CLK_ENABLE();
        extra->port = GPIOB;
    }
#endif
    // ... more ports

    // 3. Configure GPIO parameters
    extra->gpio_config.Pin = NO_OS_BIT(param->number);
    extra->gpio_config.Mode = GPIO_MODE_OUTPUT_PP;  // or INPUT
    extra->gpio_config.Speed = GPIO_SPEED_FREQ_LOW;
    extra->gpio_config.Pull = GPIO_NOPULL;
    
    // 4. Set alternate function if provided
    if (pextra && pextra->alternate) {
        extra->gpio_config.Alternate = pextra->alternate;
        extra->gpio_config.Mode = GPIO_MODE_AF_PP;
    }

    // 5. Initialize HAL GPIO
    HAL_GPIO_Init(extra->port, &extra->gpio_config);

    // 6. Link descriptor
    desc->extra = extra;

    return 0;
}
```

---

## Initialization Best Practices

1. **Clock Management**
   - Enable GPIO clocks before configuration
   - Peripheral clocks enabled automatically by HAL_*_Init()
   - Query clock frequencies with HAL_RCC_GetPCLK*Freq()

2. **Error Handling**
   - Check HAL_OK return values
   - Free allocated memory on error paths
   - Convert HAL errors to errno codes

3. **Resource Allocation**
   - Allocate descriptors with calloc() (zero-initialized)
   - Use static handle tables for shared peripherals
   - Clean up on initialization failure

4. **Family Portability**
   - Use conditional compilation for family differences
   - Test on multiple families when possible
   - Abstract family-specific code

5. **GPIO Configuration**
   - Enable port clocks first
   - Set alternate function before HAL_GPIO_Init()
   - Check datasheet for correct AF assignment
