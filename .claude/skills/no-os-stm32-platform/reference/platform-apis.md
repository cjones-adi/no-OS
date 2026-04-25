# STM32 Platform API Implementations

Complete reference for STM32 HAL-based platform driver implementations in no-OS.

## HAL Library Integration

### HAL vs LL

- All drivers use **STM32 HAL** (Hardware Abstraction Layer)
- **LL** (Low-Level) APIs are NOT used
- Leverages HAL handle structures for all peripherals

### HAL Handle Structures

```c
SPI_HandleTypeDef *hspi       // SPI handle
I2C_HandleTypeDef hi2c        // I2C handle
UART_HandleTypeDef *huart     // UART handle
TIM_HandleTypeDef *htimer     // Timer handle
DMA_HandleTypeDef *hdma       // DMA handle
GPIO_InitTypeDef gpio_config  // GPIO configuration
```

### Static Handle Management

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

---

## SPI Platform Driver

### Descriptor Structure

```c
struct stm32_spi_desc {
    SPI_HandleTypeDef *hspi;              // HAL SPI handle
    uint32_t input_clock;                 // Peripheral clock frequency
    uint32_t alternate;                   // GPIO alternate function
    struct no_os_gpio_desc *chip_select;  // CS GPIO pin
    struct no_os_dma_desc* dma_desc;      // DMA controller
    struct no_os_dma_ch* rxdma_ch;        // RX DMA channel
    struct no_os_dma_ch* txdma_ch;        // TX DMA channel
    bool stm32_spi_dma_done;              // DMA completion flag
    void (*stm32_spi_dma_user_cb)(void *ctx);  // User DMA callback
};
```

### SPI Initialization

```c
int32_t stm32_spi_init(struct no_os_spi_desc **desc,
                       const struct no_os_spi_init_param *param)
{
    // Calculate prescaler based on max_speed_hz
    uint32_t div = sdesc->input_clock / desc->max_speed_hz;
    switch (div) {
    case 0 ... 2:     prescaler = SPI_BAUDRATEPRESCALER_2;     break;
    case 3 ... 4:     prescaler = SPI_BAUDRATEPRESCALER_4;     break;
    case 5 ... 8:     prescaler = SPI_BAUDRATEPRESCALER_8;     break;
    case 9 ... 16:    prescaler = SPI_BAUDRATEPRESCALER_16;    break;
    case 17 ... 32:   prescaler = SPI_BAUDRATEPRESCALER_32;    break;
    case 33 ... 64:   prescaler = SPI_BAUDRATEPRESCALER_64;    break;
    case 65 ... 128:  prescaler = SPI_BAUDRATEPRESCALER_128;   break;
    default:          prescaler = SPI_BAUDRATEPRESCALER_256;   break;
    }

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
    // ... SPI4-SPI6 on STM32H7
    }

    // Configure SPI HAL handle
    sdesc->hspi->Init.Mode = SPI_MODE_MASTER;
    sdesc->hspi->Init.Direction = SPI_DIRECTION_2LINES;
    sdesc->hspi->Init.DataSize = SPI_DATASIZE_8BIT;
    sdesc->hspi->Init.CLKPolarity = (desc->mode & NO_OS_SPI_CPOL) ?
                                    SPI_POLARITY_HIGH : SPI_POLARITY_LOW;
    sdesc->hspi->Init.CLKPhase = (desc->mode & NO_OS_SPI_CPHA) ?
                                 SPI_PHASE_2EDGE : SPI_PHASE_1EDGE;
    sdesc->hspi->Init.NSS = SPI_NSS_SOFT;  // Software CS control
    sdesc->hspi->Init.BaudRatePrescaler = prescaler;
    sdesc->hspi->Init.FirstBit = desc->bit_order ?
                                 SPI_FIRSTBIT_LSB : SPI_FIRSTBIT_MSB;
    sdesc->hspi->Init.TIMode = SPI_TIMODE_DISABLE;
    sdesc->hspi->Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;

    // Initialize SPI peripheral
    ret = HAL_SPI_Init(sdesc->hspi);

    return ret == HAL_OK ? 0 : -EIO;
}
```

### Supported SPI Instances

- **STM32F4**: SPI1-SPI3
- **STM32H7**: SPI1-SPI6
- **STM32L4**: SPI1-SPI3

### SPI Usage Example

```c
struct stm32_spi_init_param spi_extra = {
    .input_clock = 100000000,  // APB2 clock (STM32H7)
    .alternate = GPIO_AF5_SPI1,
};

struct no_os_spi_init_param spi_init = {
    .device_id = 1,  // SPI1
    .max_speed_hz = 10000000,  // 10 MHz
    .mode = NO_OS_SPI_MODE_0,
    .chip_select = 0,
    .extra = &spi_extra,
    .platform_ops = &stm32_spi_ops,
};

ret = no_os_spi_init(&spi, &spi_init);
```

---

## I2C Platform Driver

### Descriptor Structure

```c
struct stm32_i2c_desc {
    I2C_HandleTypeDef hi2c;  // HAL I2C handle (not pointer)
};

struct stm32_i2c_init_param {
    uint32_t i2c_timing;  // Pre-calculated timing register (H7, L4, U5)
};
```

### I2C Initialization

```c
static int32_t stm32_i2c_init(struct no_os_i2c_desc **desc,
                              const struct no_os_i2c_init_param *param)
{
    // Map device_id to I2C instance
    switch (param->device_id) {
    case 1: base = I2C1; break;
    case 2: base = I2C2; break;
    case 3: base = I2C3; break;
#if defined(I2C4)
    case 4: base = I2C4; break;
#endif
    }

    xdesc->hi2c.Instance = base;

#if defined(STM32F4) || defined(STM32F1) || defined(STM32F2) || defined(STM32L1)
    // Older families: Direct clock speed setting
    xdesc->hi2c.Init.ClockSpeed = param->max_speed_hz;
    xdesc->hi2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
#else
    // Newer families (H7, L4, U5): Pre-calculated timing register
    // Use STM32CubeMX I2C timing calculator or datasheet formula
    xdesc->hi2c.Init.Timing = i2cinit->i2c_timing;
#endif

    xdesc->hi2c.Init.OwnAddress1 = 0;
    xdesc->hi2c.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    xdesc->hi2c.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    xdesc->hi2c.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    xdesc->hi2c.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;

    ret = HAL_I2C_Init(&xdesc->hi2c);

    return ret == HAL_OK ? 0 : -EIO;
}
```

### I2C Timing Calculation (STM32H7/L4/U5)

```c
// Use STM32CubeMX or calculate manually
// Example for STM32H7 @ 400 kHz (Fast Mode):
// I2C_TIMING = 0x00F07BFF (depends on clock config)

struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x00F07BFF,  // Pre-calculated for 400 kHz
};
```

### I2C Usage Example

```c
// I2C timing for 400 kHz @ 200 MHz I2C clock
// Use STM32CubeMX or calculation formula
struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x00F07BFF,
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 1,  // I2C1
    .max_speed_hz = 400000,
    .slave_address = 0x48,
    .extra = &i2c_extra,
    .platform_ops = &stm32_i2c_ops,
};

ret = no_os_i2c_init(&i2c, &i2c_init);
```

---

## UART Platform Driver

### Descriptor Structure

```c
struct stm32_uart_desc {
    UART_HandleTypeDef *huart;              // HAL UART handle
    uint32_t timeout;                       // Transaction timeout
    struct no_os_irq_ctrl_desc *nvic;       // NVIC controller
    struct no_os_callback_desc rx_callback; // RX complete callback
};
```

### UART Initialization

```c
int32_t stm32_uart_init(struct no_os_uart_desc **desc,
                        const struct no_os_uart_init_param *param)
{
    // Map device_id to UART instance
    switch (param->device_id) {
#if defined(USART1)
    case 1: sud->huart->Instance = USART1; break;
#endif
#if defined(USART2)
    case 2: sud->huart->Instance = USART2; break;
#endif
    // ... UART3-UART8
    }

    // Configure UART
    sud->huart->Init.BaudRate = param->baud_rate;
    sud->huart->Init.WordLength = UART_WORDLENGTH_8B;
    sud->huart->Init.StopBits = UART_STOPBITS_1;
    sud->huart->Init.Parity = UART_PARITY_NONE;
    sud->huart->Init.Mode = UART_MODE_TX_RX;
    sud->huart->Init.HwFlowCtl = UART_HWCONTROL_NONE;
    sud->huart->Init.OverSampling = UART_OVERSAMPLING_16;

    ret = HAL_UART_Init(sud->huart);

    // Configure async RX if requested
    if (param->asynchronous_rx) {
        lf256fifo_init(&descriptor->rx_fifo);

        // Setup NVIC interrupt
        struct no_os_irq_init_param nvic_ip = {
            .platform_ops = &stm32_irq_ops,
            .extra = sud->huart,
        };
        no_os_irq_ctrl_init(&sud->nvic, &nvic_ip);

        // Register RX callback
        sud->rx_callback.callback = uart_rx_callback;
        sud->rx_callback.ctx = descriptor;
        sud->rx_callback.event = NO_OS_EVT_UART_RX_COMPLETE;
        sud->rx_callback.peripheral = NO_OS_UART_IRQ;
        sud->rx_callback.handle = sud->huart;

        no_os_irq_register_callback(sud->nvic, descriptor->irq_id,
                                    &sud->rx_callback);
        no_os_irq_enable(sud->nvic, descriptor->irq_id);

        // Start async RX
        HAL_UART_Receive_IT(sud->huart, (uint8_t *)&c, 1);
    }

    return ret == HAL_OK ? 0 : -EIO;
}
```

### UART RX Callback

```c
static uint8_t c;  // Global buffer for character

void uart_rx_callback(void *context)
{
    struct no_os_uart_desc *d = context;

    // Write received character to FIFO
    lf256fifo_write(d->rx_fifo, c);

    // Re-enable interrupt for next character
    HAL_UART_Receive_IT(((struct stm32_uart_desc *)d->extra)->huart, &c, 1);
}
```

### UART Usage Example

```c
struct no_os_uart_init_param uart_init = {
    .device_id = 1,  // UART1
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,  // Enable interrupt-driven RX
    .platform_ops = &stm32_uart_ops,
};

ret = no_os_uart_init(&uart, &uart_init);

// Non-blocking read from FIFO
uint8_t buffer[64];
ret = no_os_uart_read(uart, buffer, 64);
```

---

## GPIO Platform Driver

### GPIO Configuration

```c
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
#ifdef GPIOC
    else if (param->port == 2) {
        __HAL_RCC_GPIOC_CLK_ENABLE();
        extra->port = GPIOC;
    }
#endif
    // ... GPIOD-GPIOK

    // Configure GPIO
    extra->gpio_config.Pin = NO_OS_BIT(param->number);
    extra->gpio_config.Mode = mode;        // GPIO_MODE_INPUT, GPIO_MODE_OUTPUT_PP
    extra->gpio_config.Speed = speed;      // GPIO_SPEED_FREQ_LOW/MEDIUM/HIGH
    extra->gpio_config.Pull = pull_mode;   // GPIO_NOPULL, GPIO_PULLUP, GPIO_PULLDOWN
    extra->gpio_config.Alternate = pextra->alternate;  // For AF mode

    HAL_GPIO_Init(extra->port, &extra->gpio_config);

    return 0;
}
```

### Supported GPIO Ports

- **STM32F4**: GPIOA-GPIOI (9 ports)
- **STM32H7**: GPIOA-GPIOK (11 ports)
- **STM32L4**: GPIOA-GPIOH (8 ports)

### GPIO Usage Example

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

## Timer/PWM Platform Driver

### Timer Base Configuration

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
    // ... TIM9-TIM17
    }

    return 0;
}
```

### PWM Period Calculation

```c
static uint32_t _compute_period_ticks(uint32_t (*get_timer_clock)(void),
                                      uint32_t clock_divider,
                                      uint32_t prescaler,
                                      uint32_t period_ns)
{
    // Timer frequency = (timer clock / (prescaler + 1))
    // PWM frequency = 1 / period_ns
    // Period ticks = (timer frequency / PWM frequency) - 1

    uint32_t timer_frequency_hz = get_timer_clock();
    timer_frequency_hz *= clock_divider;
    timer_frequency_hz /= (prescaler + 1);

    double pwm_frequency = (1.0 / period_ns);  // Hz
    uint32_t period = (uint32_t)(timer_frequency_hz /
                                 (pwm_frequency * 1000000000.0)) - 1;

    return period;
}
```

### PWM Initialization

```c
htimer->Instance = TIM1/TIM2/TIM3...;
htimer->Init.Prescaler = sparam->prescaler;
htimer->Init.CounterMode = TIM_COUNTERMODE_UP;
htimer->Init.Period = period;
htimer->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
htimer->Init.AutoReloadPreload = sparam->timer_autoreload ?
                                 TIM_AUTORELOAD_PRELOAD_ENABLE :
                                 TIM_AUTORELOAD_PRELOAD_DISABLE;
htimer->Init.RepetitionCounter = sparam->repetitions;

ret = HAL_TIM_Base_Init(htimer);
ret = HAL_TIM_PWM_Init(htimer);

// Configure PWM channel
sConfigOC.OCMode = TIM_OCMODE_PWM1;
sConfigOC.Pulse = duty_cycle_ticks;
sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;

ret = HAL_TIM_PWM_ConfigChannel(htimer, &sConfigOC, channel);
ret = HAL_TIM_PWM_Start(htimer, channel);
```

### Supported Timers

- **STM32F4**: TIM1-TIM14
- **STM32H7**: TIM1-TIM17
- **STM32L4**: TIM1-TIM17

---

## DMA Platform Driver

### DMA Channel Configuration

```c
struct stm32_dma_channel {
    DMA_HandleTypeDef *hdma;
    uint32_t ch_num;                          // Channel/stream number
    bool mem_increment;                       // Auto-increment memory address
    bool per_increment;                       // Auto-increment peripheral address
    enum stm32_dma_data_alignment mem_data_alignment;   // BYTE/HALFWORD/WORD
    enum stm32_dma_data_alignment per_data_alignment;
    enum stm32_dma_mode dma_mode;            // NORMAL or CIRCULAR
    struct stm32_dma_trigger *trig;
    uint8_t* src;
    uint8_t* dst;
    uint32_t length;
};
```

### DMA Transfer Configuration

```c
int stm32_dma_config_xfer(struct no_os_dma_ch *channel,
                         struct no_os_dma_xfer_desc *xfer)
{
#if defined(STM32F2) || defined(STM32F4) || defined(STM32F7)
    // F2/F4/F7: Channel in Init structure
    sdma_ch->hdma->Init.Channel = sdma_ch->ch_num;
#else
    // Newer families: Channel in Instance
    sdma_ch->hdma->Instance = sdma_ch->ch_num;
#endif

    // Increment modes
    sdma_ch->hdma->Init.MemInc = sdma_ch->mem_increment ?
                                 DMA_MINC_ENABLE : DMA_MINC_DISABLE;
    sdma_ch->hdma->Init.PeriphInc = sdma_ch->per_increment ?
                                    DMA_PINC_ENABLE : DMA_PINC_DISABLE;

    // Data alignment
    switch (sdma_ch->mem_data_alignment) {
    case DATA_ALIGN_BYTE:
        hdma->Init.MemDataAlignment = DMA_MDATAALIGN_BYTE;
        break;
    case DATA_ALIGN_HALF_WORD:
        hdma->Init.MemDataAlignment = DMA_MDATAALIGN_HALFWORD;
        break;
    case DATA_ALIGN_WORD:
        hdma->Init.MemDataAlignment = DMA_MDATAALIGN_WORD;
        break;
    }

    switch (sdma_ch->per_data_alignment) {
    case DATA_ALIGN_BYTE:
        hdma->Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
        break;
    case DATA_ALIGN_HALF_WORD:
        hdma->Init.PeriphDataAlignment = DMA_PDATAALIGN_HALFWORD;
        break;
    case DATA_ALIGN_WORD:
        hdma->Init.PeriphDataAlignment = DMA_PDATAALIGN_WORD;
        break;
    }

    // Transfer direction
    switch (xfer->xfer_type) {
    case MEM_TO_MEM:
        hdma->Init.Direction = DMA_MEMORY_TO_MEMORY;
        break;
    case MEM_TO_DEV:
        hdma->Init.Direction = DMA_MEMORY_TO_PERIPH;
        break;
    case DEV_TO_MEM:
        hdma->Init.Direction = DMA_PERIPH_TO_MEMORY;
        break;
    }

    // Mode
    sdma_ch->hdma->Init.Mode = sdma_ch->dma_mode == DMA_NORMAL_MODE ?
                               DMA_NORMAL : DMA_CIRCULAR;

    // Priority
    sdma_ch->hdma->Init.Priority = DMA_PRIORITY_HIGH;

    ret = HAL_DMA_Init(sdma_ch->hdma);

    return ret == HAL_OK ? 0 : -EIO;
}
```

### DMA Streams and Channels

- **STM32F4/F7**: DMA1 (8 streams), DMA2 (8 streams), each stream has 8 channels
- **STM32H7**: DMA1/DMA2 with DMAMUX for flexible request routing
- **STM32U5/H5**: GPDMA with linked-list mode

---

## NVIC Interrupt Management

### Event Mapping

```c
struct event_list {
    enum no_os_irq_event event;
    uint32_t hal_event;             // HAL callback ID
    struct no_os_list_desc *actions;  // List of callbacks
};

static struct event_list _events[] = {
    [NO_OS_EVT_GPIO] = {
        .event = NO_OS_EVT_GPIO,
        .hal_event = HAL_EXTI_COMMON_CB_ID
    },
    [NO_OS_EVT_UART_TX_COMPLETE] = {
        .event = NO_OS_EVT_UART_TX_COMPLETE,
        .hal_event = HAL_UART_TX_COMPLETE_CB_ID
    },
    [NO_OS_EVT_UART_RX_COMPLETE] = {
        .event = NO_OS_EVT_UART_RX_COMPLETE,
        .hal_event = HAL_UART_RX_COMPLETE_CB_ID
    },
    [NO_OS_EVT_UART_ERROR] = {
        .event = NO_OS_EVT_UART_ERROR,
        .hal_event = HAL_UART_ERROR_CB_ID
    },
#ifdef HAL_TIM_MODULE_ENABLED
    [NO_OS_EVT_TIM_ELAPSED] = {
        .event = NO_OS_EVT_TIM_ELAPSED,
        .hal_event = HAL_TIM_PERIOD_ELAPSED_CB_ID
    },
    [NO_OS_EVT_TIM_PWM_PULSE_FINISHED] = {
        .event = NO_OS_EVT_TIM_PWM_PULSE_FINISHED,
        .hal_event = HAL_TIM_PWM_PULSE_FINISHED_CB_ID
    },
#endif
#ifdef HAL_DMA_MODULE_ENABLED
    [NO_OS_EVT_DMA_RX_COMPLETE] = {
        .event = NO_OS_EVT_DMA_RX_COMPLETE,
        .hal_event = HAL_DMA_XFER_CPLT_CB_ID
    },
#endif
};
```

### HAL Callback Handlers

```c
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    struct event_list *ee = &_events[NO_OS_EVT_TIM_ELAPSED];
    struct irq_action *a;
    struct irq_action key = {.handle = htim};

    // Find callback by timer handle
    no_os_list_read_find(ee->actions, (void **)&a, &key);
    if (a && a->callback)
        a->callback(a->ctx);
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    _common_uart_callback(huart, NO_OS_EVT_UART_RX_COMPLETE);
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    _common_uart_callback(huart, NO_OS_EVT_UART_TX_COMPLETE);
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    _common_uart_callback(huart, NO_OS_EVT_UART_ERROR);
}
```

---

## Reference Examples

- **SPI Driver**: `drivers/platform/stm32/stm32_spi.c`
- **I2C Driver**: `drivers/platform/stm32/stm32_i2c.c`
- **UART Driver**: `drivers/platform/stm32/stm32_uart.c`
- **GPIO Driver**: `drivers/platform/stm32/stm32_gpio.c`
- **PWM Driver**: `drivers/platform/stm32/stm32_pwm.c`
- **DMA Controller**: `drivers/platform/stm32/stm32_dma.c`
- **IRQ Controller**: `drivers/platform/stm32/stm32_irq.c`
