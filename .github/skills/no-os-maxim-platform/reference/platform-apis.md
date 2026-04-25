# Maxim Platform API Implementations

Complete reference for all Maxim platform driver APIs including SPI, I2C, UART, GPIO, Timer/PWM, DMA, and IRQ.

## SPI Platform Driver

### Descriptor Structure

```c
struct max_spi_state {
    struct max_spi_init_param *init_param;
    mxc_spi_regs_t *regs;              // SPI register pointer
    struct no_os_dma_desc *dma;        // DMA controller
    uint8_t dma_req_tx;                // TX DMA request signal
    uint8_t dma_req_rx;                // RX DMA request signal
    struct no_os_dma_ch *dma_ch_tx;    // TX DMA channel
    struct no_os_dma_ch *dma_ch_rx;    // RX DMA channel
};

struct max_spi_init_param {
    uint32_t num_slaves;
    mxc_spi_tscontrol_t polarity;  // SS polarity
    mxc_gpio_vssel_t vssel;        // Voltage level
    struct no_os_dma_init_param *dma_param;
    uint8_t dma_tx_priority;
    uint8_t dma_rx_priority;
};
```

### SPI Initialization

```c
int32_t max_spi_init(struct no_os_spi_desc **desc,
                     const struct no_os_spi_init_param *param)
{
    // 1. Initialize SPI module
    ret = MXC_SPI_Init(MXC_SPI_GET_SPI(desc->device_id),
                      SPI_MASTER_MODE,
                      SPI_SINGLE_MODE,     // Single slave
                      eparam->num_slaves,
                      eparam->polarity,
                      desc->max_speed_hz);

    // 2. Configure GPIO pins
    _max_spi_config_pins(desc);

    // 3. Set SPI mode (CPOL/CPHA)
    ret = MXC_SPI_SetMode(MXC_SPI_GET_SPI(desc->device_id), desc->mode);

    // 4. Set data width
    ret = MXC_SPI_SetWidth(MXC_SPI_GET_SPI(desc->device_id), SPI_WIDTH_STANDARD);

    // 5. Set data size (8-bit)
    ret = MXC_SPI_SetDataSize(MXC_SPI_GET_SPI(desc->device_id), 8);

    // 6. Initialize DMA if requested
    if (eparam->dma_param) {
        // RX priority must be higher than TX
        if (eparam->dma_rx_priority >= eparam->dma_tx_priority)
            return -EINVAL;

        ret = no_os_dma_init(&st->dma, eparam->dma_param);
        _max_dma_set_req(desc);  // Set DMA request signals
    }

    return 0;
}
```

### CS Delay Configuration

```c
#define MAX_DELAY_SCLK 255  // Max delay in SCLK periods

static void _max_delay_config(struct no_os_spi_desc *desc,
                              struct no_os_spi_msg *msg)
{
    mxc_spi_regs_t *spi = MXC_SPI_GET_SPI(desc->device_id);

    // Get peripheral clock frequency
    uint32_t clk_rate = MXC_SPI_GetPeripheralClock(spi);
    uint32_t ticks_ns = NO_OS_DIV_ROUND_CLOSEST(NANO, clk_rate);

    // Calculate delay in SCLK ticks
    uint32_t ticks_delay = NO_OS_DIV_ROUND_CLOSEST(msg->cs_delay_first, ticks_ns);
    ticks_delay = no_os_min(ticks_delay, MAX_DELAY_SCLK);

    // Configure SSACT1 (CS assert delay)
    spi->ss_time &= ~MXC_F_SPI_SS_TIME_SSACT1;
    spi->ss_time |= no_os_field_prep(MXC_F_SPI_SS_TIME_SSACT1, ticks_delay);

    // Configure SSACT2 (CS de-assert delay)
    spi->ss_time &= ~MXC_F_SPI_SS_TIME_SSACT2;
    spi->ss_time |= no_os_field_prep(MXC_F_SPI_SS_TIME_SSACT2, ticks_delay);
}
```

### DMA-Based SPI Transfer

```c
static int32_t max_config_dma_and_start(struct no_os_spi_desc *desc,
                                        struct no_os_spi_msg *msgs,
                                        uint32_t len,
                                        void (*callback)(void *),
                                        void *ctx, bool is_async)
{
    mxc_spi_regs_t *spi = MXC_SPI_GET_SPI(desc->device_id);

    // Clear FIFOs
    spi->dma |= MXC_F_SPI_DMA_RX_FIFO_CLEAR | MXC_F_SPI_DMA_TX_FIFO_CLEAR;

    // Configure transfer size
    spi->ctrl1 = msgs[0].bytes_number;
    spi->ctrl1 |= no_os_field_prep(MXC_F_SPI_CTRL1_RX_NUM_CHAR, msgs[0].bytes_number);

    // Enable FIFOs and DMA
    spi->dma |= MXC_F_SPI_DMA_TX_FIFO_EN | MXC_F_SPI_DMA_RX_FIFO_EN;
    spi->dma |= MXC_F_SPI_DMA_RX_DMA_EN | MXC_F_SPI_DMA_TX_DMA_EN;

    // Acquire DMA channels
    no_os_dma_acquire_channel(max_spi->dma, &tx_ch);
    no_os_dma_acquire_channel(max_spi->dma, &rx_ch);

    // Configure and start DMA transfer
    // ... DMA configuration ...

    return 0;
}
```

## I2C Platform Driver

### Speed Modes

```c
enum max_i2c_speed {
    MAX_I2C_STD_MODE = 100000,        // 100 kHz
    MAX_I2C_FAST_MODE = 400000,       // 400 kHz
    MAX_I2C_FAST_PLUS_MODE = 1000000, // 1 MHz
    MAX_I2C_HS_MODE = 3400000,        // 3.4 MHz
};
```

### I2C Initialization

```c
static int32_t max_i2c_init(struct no_os_i2c_desc **desc,
                            const struct no_os_i2c_init_param *param)
{
    // Get I2C peripheral pointer
    mxc_i2c_regs_t *i2c_regs = MXC_I2C_GET_I2C(param->device_id);
    max_i2c->handler = i2c_regs;

    // Select speed mode
    if (param->max_speed_hz <= MAX_I2C_STD_MODE)
        desc->max_speed_hz = MAX_I2C_STD_MODE;
    else if (param->max_speed_hz <= MAX_I2C_FAST_MODE)
        desc->max_speed_hz = MAX_I2C_FAST_MODE;
    else if (param->max_speed_hz <= MAX_I2C_FAST_PLUS_MODE)
        desc->max_speed_hz = MAX_I2C_FAST_PLUS_MODE;
    else
        desc->max_speed_hz = MAX_I2C_HS_MODE;

    // Configure GPIO pins
    _max_i2c_pins_config(device_id, eparam->vssel);

    // Initialize I2C module (only on first descriptor for this I2C)
    if (nb_created_desc[param->device_id] == 0) {
        MXC_I2C_Shutdown(max_i2c->handler);
        MXC_I2C_Init(i2c_regs, I2C_MASTER_MODE, 0);
    }

    // Configure frequency
    uint32_t freq = MXC_I2C_GetFrequency(i2c_regs);
    freq = no_os_min(freq, desc->max_speed_hz);
    MXC_I2C_SetFrequency(i2c_regs, freq);

    // Track descriptor count
    nb_created_desc[param->device_id]++;

    return 0;
}
```

### Write-Repeated Start-Read Pattern

```c
struct max_i2c_extra {
    mxc_i2c_regs_t *handler;
    uint8_t *prologue_data;      // Write data for write-read transaction
    uint8_t prologue_size;       // Number of bytes to write
};

// Example: Write register address, then read data
max_i2c->prologue_data = &register_addr;
max_i2c->prologue_size = 1;

ret = no_os_i2c_read(desc, data, bytes_number);
// Performs: START | ADDR+W | REG_ADDR | RESTART | ADDR+R | DATA... | STOP
```

### I2C Interrupt Handlers

```c
void I2C0_IRQHandler(void) {
    MXC_I2C_AsyncHandler(MXC_I2C0);
}

void I2C1_IRQHandler(void) {
    MXC_I2C_AsyncHandler(MXC_I2C1);
}

#ifdef MXC_I2C2
void I2C2_IRQHandler(void) {
    MXC_I2C_AsyncHandler(MXC_I2C2);
}
#endif
```

## GPIO Platform Driver

### GPIO Configuration

```c
int32_t max_gpio_get(struct no_os_gpio_desc **desc,
                     const struct no_os_gpio_init_param *param)
{
    mxc_gpio_cfg_t g_cfg;
    uint32_t m_pad;

    // Map pull configuration
    switch (param->pull) {
    case NO_OS_PULL_NONE:
        m_pad = MXC_GPIO_PAD_NONE;
        break;
    case NO_OS_PULL_UP:
        m_pad = MXC_GPIO_PAD_WEAK_PULL_UP;
        break;
    case NO_OS_PULL_DOWN:
        m_pad = MXC_GPIO_PAD_WEAK_PULL_DOWN;
        break;
    }

    // Configure GPIO
    g_cfg.port = MXC_GPIO_GET_GPIO(param->port);
    g_cfg.mask = NO_OS_BIT(param->number);
    g_cfg.pad = m_pad;
    g_cfg.func = MXC_GPIO_FUNC_IN;  // Input initially
    g_cfg.vssel = pextra->vssel;     // Voltage selection

    // Initialize GPIO port and configure pin
    MXC_GPIO_Init(param->port);
    MXC_GPIO_Config(&g_cfg);

    return 0;
}
```

### GPIO Port Operations

```c
// Direct register access for efficiency
static void set_enable(mxc_gpio_regs_t *regs, uint32_t mask, uint8_t is_enabled)
{
    if (is_enabled)
        regs->en |= mask;
    else
        regs->en &= ~mask;
}

static void set_output(mxc_gpio_regs_t *regs, uint32_t mask, uint8_t value)
{
    if (value)
        regs->out_set = mask;
    else
        regs->out_clr = mask;
}
```

## GPIO IRQ (External Interrupts)

### IRQ Handler Registration

```c
#define N_PINS  MXC_CFG_GPIO_PINS_PORT   // Pins per port
#define N_PORTS MXC_CFG_GPIO_INSTANCES   // Number of GPIO ports

void GPIO0_IRQHandler() {
    MXC_GPIO_Handler(0);
}

#ifdef MXC_GPIO1
void GPIO1_IRQHandler() {
    MXC_GPIO_Handler(1);
}
#endif

#ifdef MXC_GPIO2
void GPIO2_IRQHandler() {
    MXC_GPIO_Handler(2);
}
#endif
```

### Callback Chain

```c
static void gpio_irq_callback(void *cbdata)
{
    struct irq_action *action;
    struct irq_action *key = cbdata;

    // Extract GPIO port from key->handle
    uint32_t id = MXC_GPIO_GET_IDX(key->handle);

    // Find registered action in list
    no_os_list_read_find(actions[id], (void **)&action, key);

    // Execute user callback
    if (action->callback)
        action->callback(action->ctx);
}
```

## UART Platform Driver

### Flow Control

```c
enum max_uart_flow_ctrl {
    MAX_UART_FLOW_DIS,   // Disabled
    UART_FLOW_LOW,       // CTS/RTS low-asserted
    UART_FLOW_HIGH,      // CTS/RTS high-asserted
};

struct max_uart_init_param {
    enum max_uart_flow_ctrl flow;
    mxc_gpio_vssel_t vssel;
};
```

### UART Read with FIFO

```c
#define MXC_UART_FIFO_DEPTH  // Device-specific

static int32_t max_uart_read(struct no_os_uart_desc *desc,
                             uint8_t *data, uint32_t bytes_number)
{
    // Check if RX FIFO is configured
    if (desc->rx_fifo) {
        for (i = 0; i < bytes_number; i++) {
            ret = lf256fifo_read(desc->rx_fifo, &data[i]);
            if (ret)
                return i ? (int32_t)i : -EAGAIN;  // Return bytes read or EAGAIN
        }
        return i;
    }

    // Use HAL blocking read
    ret = MXC_UART_Read(MXC_UART_GET_UART(desc->device_id),
                       data, (int *)&bytes_number);
    return ret < 0 ? ret : (int32_t)bytes_number;
}
```

### UART Write with TX Empty Wait

```c
static int32_t max_uart_write(struct no_os_uart_desc *desc,
                              const uint8_t *data, uint32_t bytes_number)
{
    uint32_t transfered = 0;

    while (bytes_number) {
        int block_size = no_os_min(MXC_UART_FIFO_DEPTH, bytes_number);

        // Wait for TX FIFO empty
        while (!(MXC_UART_GetStatus(MXC_UART_GET_UART(desc->device_id)) &
                 MXC_F_UART_STAT_TX_EMPTY));

        // Write block
        MXC_UART_Write(MXC_UART_GET_UART(desc->device_id),
                      (uint8_t *)(data + transfered), &block_size);

        transfered += block_size;
        bytes_number -= block_size;
    }

    return transfered;
}
```

### UART IRQ Handlers

```c
mxc_uart_req_t uart_irq_state[MXC_UART_INSTANCES];

static void _uart_common_handler(mxc_uart_regs_t *uart)
{
    mxc_uart_req_t *req = &uart_irq_state[MXC_UART_GET_IDX(uart)];
    MXC_UART_AsyncHandler(uart);

    // Handle new transactions registered in callbacks
    if (req->uart && ((req->rxCnt == 0 && req->rxLen != 0) ||
                     (req->txLen != 0)))
        MXC_UART_TransactionAsync(req);
}

void UART0_IRQHandler() {
    _uart_common_handler(MXC_UART0);
}

#ifdef MXC_UART1
void UART1_IRQHandler() {
    _uart_common_handler(MXC_UART1);
}
#endif
```

## Timer/PWM Platform Driver

### Prescaler Selection

```c
static int _get_prescaler(uint32_t div, mxc_tmr_pres_t *prescaler)
{
    if (div > 4096)
        return -EINVAL;

    if (div < 2)
        *prescaler = TMR_PRES_1;
    else if (div < 4)
        *prescaler = TMR_PRES_2;
    else if (div < 8)
        *prescaler = TMR_PRES_4;
    else if (div < 16)
        *prescaler = TMR_PRES_8;
    else if (div < 32)
        *prescaler = TMR_PRES_16;
    else if (div < 64)
        *prescaler = TMR_PRES_32;
    else if (div < 128)
        *prescaler = TMR_PRES_64;
    else if (div < 256)
        *prescaler = TMR_PRES_128;
    else if (div < 512)
        *prescaler = TMR_PRES_256;
    else if (div < 1024)
        *prescaler = TMR_PRES_512;
    else if (div < 2048)
        *prescaler = TMR_PRES_1024;
    else if (div < 4096)
        *prescaler = TMR_PRES_2048;
    else
        *prescaler = TMR_PRES_4096;

    return 0;
}
```

### Timer Initialization

```c
int max_timer_init(struct no_os_timer_desc **desc,
                   const struct no_os_timer_init_param *param)
{
    mxc_tmr_cfg_t cfg;
    mxc_tmr_regs_t *tmr_regs = MXC_TMR_GET_TMR(param->id);

    // Calculate prescaler
    uint32_t clk_div = SOURCE_CLOCK_FREQ / param->freq_hz;
    _get_prescaler(clk_div, &prescaler);

    // Configure timer
    cfg.mode = TMR_MODE_CONTINUOUS;
    cfg.cmp_cnt = descriptor->ticks_count;  // Match value
    cfg.pol = 1;
    cfg.pres = prescaler;

    // Initialize hardware
    MXC_TMR_Shutdown(tmr_regs);
    MXC_TMR_Init(tmr_regs, &cfg);

    return 0;
}
```

### PWM Period Calculation

```c
#define MAX_PWM_TMR_MAX_VAL         NO_OS_GENMASK(15, 0)  // 16-bit timer
#define MAX_PWM_PRESCALER_VAL(n)    ((n - 1) * 16)
#define MAX_PWM_PRESCALER_TRUE(n)   NO_OS_BIT((n) / 16)
#define MAX_PWM_GET_PRESCALER(n)    NO_OS_BIT((n) - 1)

int max_pwm_set_period(struct no_os_pwm_desc *desc, uint32_t period_ns)
{
    // Calculate required divider
    uint32_t div = PeripheralClock / NO_OS_DIV_ROUND_CLOSEST_ULL(NANO, period_ns);
    _get_prescaler(div, &prescaler);

    // Calculate period in timer ticks
    uint32_t period_ticks = PeripheralClock / (
        NO_OS_DIV_ROUND_CLOSEST_ULL(NANO, period_ns) *
        MAX_PWM_PRESCALER_TRUE(prescaler)
    );

    cfg.pres = prescaler;
    cfg.cmp_cnt = period_ticks;

    return 0;
}
```

## DMA Controller

### DMA Register Structure

```c
struct max_dma_ch_regs {
    volatile uint32_t cfg;      // Channel configuration
    volatile uint32_t st;       // Status
    volatile uint32_t src;      // Source address
    volatile uint32_t dst;      // Destination address
    volatile uint32_t cnt;      // Byte count
    volatile uint32_t src_rld;  // Source reload
    volatile uint32_t dst_rld;  // Destination reload
    volatile uint32_t cnt_rld;  // Count reload
};

struct max_dma_regs {
    volatile uint32_t cn;                               // Control
    volatile const uint32_t intr;                       // Interrupt status
    const uint32_t rsv_0x8_0xff[62];                   // Reserved
    volatile struct max_dma_ch_regs ch[MXC_DMA_CHANNELS];
};
```

### DMA Initialization

```c
static int maxim_dma_init(struct no_os_dma_desc **desc,
                          struct no_os_dma_init_param *param)
{
    // Single DMA controller per platform
    if (dma_descriptor) {
        *desc = dma_descriptor;
        return 0;
    }

    // Enable DMA clock
    if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_DMA)) {
        MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_DMA);
        MXC_SYS_Reset_Periph(MAX_DMA_GCR_RST_POS);
    }

    // Configure channels
    for (i = 0; i < param->num_ch; i++) {
        descriptor->channels[i].id = i;
        descriptor->channels[i].irq_num = max_dma_get_irq(descriptor->id, i);
        descriptor->channels[i].extra = (void *)&MAX_DMA->ch[i];
        descriptor->channels[i].free = true;
    }

    // Enable all channel interrupts
    MAX_DMA->cn |= MAX_DMA_IRQ_EN_ALL_CH;

    return 0;
}
```

### DMA Request Signal Selection (SPI Example)

```c
static void _max_dma_set_req(struct no_os_spi_desc *desc)
{
    struct max_spi_state *st = desc->extra;

    switch (desc->device_id) {
    case 0:
        st->dma_req_tx = MXC_V_DMA_CFG_REQSEL_SPI0TX;
        st->dma_req_rx = MXC_V_DMA_CFG_REQSEL_SPI0RX;
        break;
    case 1:
        st->dma_req_tx = MXC_V_DMA_CFG_REQSEL_SPI1TX;
        st->dma_req_rx = MXC_V_DMA_CFG_REQSEL_SPI1RX;
        break;
    case 2:
        st->dma_req_tx = MXC_V_DMA_CFG_REQSEL_SPI2TX;
        st->dma_req_rx = MXC_V_DMA_CFG_REQSEL_SPI2RX;
        break;
    case 3:
        st->dma_req_tx = MXC_V_DMA_CFG_REQSEL_SPI3TX;
        st->dma_req_rx = MXC_V_DMA_CFG_REQSEL_SPI3RX;
        break;
    }
}
```

## IRQ Controller

### Event Types

```c
static struct event_list _events[] = {
    [NO_OS_EVT_GPIO]            = {.event = NO_OS_EVT_GPIO},
    [NO_OS_EVT_UART_TX_COMPLETE] = {.event = NO_OS_EVT_UART_TX_COMPLETE},
    [NO_OS_EVT_UART_RX_COMPLETE] = {.event = NO_OS_EVT_UART_RX_COMPLETE},
    [NO_OS_EVT_UART_ERROR]       = {.event = NO_OS_EVT_UART_ERROR},
    [NO_OS_EVT_RTC]              = {.event = NO_OS_EVT_RTC},
    [NO_OS_EVT_TIM_ELAPSED]      = {.event = NO_OS_EVT_TIM_ELAPSED},
    [NO_OS_EVT_DMA_RX_COMPLETE]  = {.event = NO_OS_EVT_DMA_RX_COMPLETE},
    [NO_OS_EVT_DMA_TX_COMPLETE]  = {.event = NO_OS_EVT_DMA_TX_COMPLETE},
    [NO_OS_EVT_USB]              = {.event = NO_OS_EVT_USB},
};
```

### Timer IRQ Callback

```c
static void _timer_common_callback(mxc_tmr_regs_t *tmr)
{
    struct irq_action key = {
        .irq_id = MXC_TMR_GET_IRQ(MXC_TMR_GET_IDX(tmr))
    };
    struct irq_action *action;
    struct event_list *evt_list = &_events[NO_OS_EVT_TIM_ELAPSED];

    // Find and execute callback
    no_os_list_read_find(evt_list->actions, (void **)&action, &key);
    if (action->callback)
        action->callback(action->ctx);

    MXC_TMR_ClearFlags(tmr);
}
```

## Delay Functions

### SysTick Handler

```c
static volatile unsigned long long _system_ticks = 0;

void SysTick_Handler(void)
{
    MXC_DelayHandler();   // HAL delay handler
    _system_ticks++;      // Track milliseconds
}
```

### Microsecond and Millisecond Delays

```c
void no_os_udelay(uint32_t usecs)
{
    MXC_Delay(MXC_DELAY_USEC(usecs));
}

void no_os_mdelay(uint32_t msecs)
{
    MXC_Delay(MXC_DELAY_MSEC(msecs));
}
```

### System Time Tracking

```c
struct no_os_time no_os_get_time(void)
{
    struct no_os_time t;
    uint64_t sub_ms;
    uint32_t systick_val;
    uint64_t ticks;

    // Disable SysTick to read consistent state
    SysTick->CTRL &= ~(SysTick_CTRL_TICKINT_Msk | SysTick_CTRL_ENABLE_Msk);
    systick_val = SysTick->VAL;
    ticks = _system_ticks;
    SysTick->CTRL |= SysTick_CTRL_TICKINT_Msk | SysTick_CTRL_ENABLE_Msk;

    // Calculate fractional milliseconds
    sub_ms = ((SysTick->LOAD - systick_val) * 1000) / SysTick->LOAD;
    t.s = ticks / 1000;
    t.us = (ticks - t.s * 1000) * 1000 + sub_ms;

    return t;
}
```

## Reference Examples

- **SPI Driver**: `drivers/platform/maxim/max32650/maxim_spi.c`
- **I2C Driver**: `drivers/platform/maxim/max32650/maxim_i2c.c`
- **UART Driver**: `drivers/platform/maxim/max32650/maxim_uart.c`
- **GPIO Driver**: `drivers/platform/maxim/max32650/maxim_gpio.c`
- **DMA Controller**: `drivers/platform/maxim/common/maxim_dma.c`
