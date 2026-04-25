## Driver Implementation Pattern

### Step 1: Define Register Map

```c
/* UART controller registers */
#define UART_RBR        0x00   /* Receiver Buffer Register (RO) */
#define UART_THR        0x00   /* Transmitter Holding Register (WO) */
#define UART_DLL        0x00   /* Divisor Latch LSB (DLAB=1) */
#define UART_IER        0x04   /* Interrupt Enable Register */
#define UART_DLM        0x04   /* Divisor Latch MSB (DLAB=1) */
#define UART_IIR        0x08   /* Interrupt Identification Register (RO) */
#define UART_FCR        0x08   /* FIFO Control Register (WO) */
#define UART_LCR        0x0C   /* Line Control Register */
#define UART_MCR        0x10   /* Modem Control Register */
#define UART_LSR        0x14   /* Line Status Register */
#define UART_MSR        0x18   /* Modem Status Register */

/* Line Control Register bits */
#define UART_LCR_WLS_5      0x00   /* 5-bit character length */
#define UART_LCR_WLS_6      0x01   /* 6-bit character length */
#define UART_LCR_WLS_7      0x02   /* 7-bit character length */
#define UART_LCR_WLS_8      0x03   /* 8-bit character length */
#define UART_LCR_STB        BIT(2) /* Number of stop bits (0=1, 1=2) */
#define UART_LCR_PEN        BIT(3) /* Parity enable */
#define UART_LCR_EPS        BIT(4) /* Even parity select */
#define UART_LCR_SP         BIT(5) /* Stick parity */
#define UART_LCR_BC         BIT(6) /* Break control */
#define UART_LCR_DLAB       BIT(7) /* Divisor latch access bit */

/* Line Status Register bits */
#define UART_LSR_DR         BIT(0) /* Data ready */
#define UART_LSR_OE         BIT(1) /* Overrun error */
#define UART_LSR_PE         BIT(2) /* Parity error */
#define UART_LSR_FE         BIT(3) /* Framing error */
#define UART_LSR_BI         BIT(4) /* Break interrupt */
#define UART_LSR_THRE       BIT(5) /* Transmit holding register empty */
#define UART_LSR_TEMT       BIT(6) /* Transmitter empty */
#define UART_LSR_FIFOERR    BIT(7) /* Error in RCVR FIFO */

/* Interrupt Enable Register bits */
#define UART_IER_RDI        BIT(0) /* Received data available interrupt */
#define UART_IER_THRI       BIT(1) /* Transmitter holding register empty int */
#define UART_IER_RLSI       BIT(2) /* Receiver line status interrupt */
#define UART_IER_MSI        BIT(3) /* Modem status interrupt */

/* FIFO Control Register bits */
#define UART_FCR_FIFOE      BIT(0) /* FIFO enable */
#define UART_FCR_RFIFOR     BIT(1) /* RX FIFO reset */
#define UART_FCR_XFIFOR     BIT(2) /* TX FIFO reset */
#define UART_FCR_TRIGGER_1  (0 << 6)  /* RX trigger at 1 byte */
#define UART_FCR_TRIGGER_4  (1 << 6)  /* RX trigger at 4 bytes */
#define UART_FCR_TRIGGER_8  (2 << 6)  /* RX trigger at 8 bytes */
#define UART_FCR_TRIGGER_14 (3 << 6)  /* RX trigger at 14 bytes */

/* Modem Control Register bits */
#define UART_MCR_DTR        BIT(0) /* Data Terminal Ready */
#define UART_MCR_RTS        BIT(1) /* Request To Send */
#define UART_MCR_OUT1       BIT(2) /* Output 1 */
#define UART_MCR_OUT2       BIT(3) /* Output 2 */
#define UART_MCR_LOOP       BIT(4) /* Loopback mode */
#define UART_MCR_AFCE       BIT(5) /* Auto flow control enable */
```

### Step 2: Define Config and Data Structures

**Config structure** (ROM, from devicetree):

```c
struct uart_chip_config {
    uint32_t base;              /* Register base address */
    uint32_t sys_clk_freq;      /* System clock frequency */
    struct uart_config uart_cfg; /* Initial UART configuration */
#ifdef CONFIG_UART_INTERRUPT_DRIVEN
    void (*irq_config_func)(const struct device *dev);
#endif
#ifdef CONFIG_PINCTRL
    const struct pinctrl_dev_config *pcfg;
#endif
};
```

**Data structure** (RAM, runtime state):

```c
struct uart_chip_data {
#ifdef CONFIG_UART_INTERRUPT_DRIVEN
    uart_irq_callback_user_data_t cb;  /* IRQ callback */
    void *cb_data;                     /* Callback user data */
#endif
#ifdef CONFIG_UART_ASYNC_API
    uart_callback_t async_cb;          /* Async callback */
    void *async_user_data;             /* Async user data */
    const uint8_t *tx_buf;             /* Current TX buffer */
    size_t tx_len;                     /* TX length */
    size_t tx_sent;                    /* Bytes sent */
    uint8_t *rx_buf;                   /* Current RX buffer */
    size_t rx_len;                     /* RX buffer length */
    size_t rx_received;                /* Bytes received */
    uint8_t *rx_next_buf;              /* Next RX buffer */
    size_t rx_next_len;                /* Next buffer length */
    struct k_work_delayable rx_timeout_work; /* RX timeout */
#endif
};
```

### Step 3: Implement Polling API

```c
static int uart_chip_poll_in(const struct device *dev, unsigned char *p_char)
{
    const struct uart_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;

    /* Check if data is available */
    if (!(sys_read32(base + UART_LSR) & UART_LSR_DR)) {
        return -1;  /* No data */
    }

    /* Read byte */
    *p_char = sys_read32(base + UART_RBR) & 0xFF;

    return 0;
}

static void uart_chip_poll_out(const struct device *dev, unsigned char out_char)
{
    const struct uart_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;

    /* Wait until TX holding register is empty */
    while (!(sys_read32(base + UART_LSR) & UART_LSR_THRE)) {
        /* Busy wait */
    }

    /* Send byte */
    sys_write32(out_char, base + UART_THR);
}

static int uart_chip_err_check(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;
    uint32_t lsr = sys_read32(base + UART_LSR);
    int errors = 0;

    if (lsr & UART_LSR_OE) {
        errors |= UART_ERROR_OVERRUN;
    }
    if (lsr & UART_LSR_PE) {
        errors |= UART_ERROR_PARITY;
    }
    if (lsr & UART_LSR_FE) {
        errors |= UART_ERROR_FRAMING;
    }
    if (lsr & UART_LSR_BI) {
        errors |= UART_BREAK;
    }

    return errors;
}
```

### Step 4: Implement Configuration API

```c
static int uart_chip_configure(const struct device *dev,
                                const struct uart_config *cfg)
{
    const struct uart_chip_config *dev_cfg = dev->config;
    uint32_t base = dev_cfg->base;
    uint32_t lcr = 0;
    uint32_t divisor;

    /* Calculate baud rate divisor */
    divisor = dev_cfg->sys_clk_freq / (16 * cfg->baudrate);
    if (divisor == 0) {
        return -EINVAL;
    }

    /* Set data bits */
    switch (cfg->data_bits) {
    case UART_CFG_DATA_BITS_5:
        lcr |= UART_LCR_WLS_5;
        break;
    case UART_CFG_DATA_BITS_6:
        lcr |= UART_LCR_WLS_6;
        break;
    case UART_CFG_DATA_BITS_7:
        lcr |= UART_LCR_WLS_7;
        break;
    case UART_CFG_DATA_BITS_8:
        lcr |= UART_LCR_WLS_8;
        break;
    default:
        return -ENOTSUP;
    }

    /* Set parity */
    switch (cfg->parity) {
    case UART_CFG_PARITY_NONE:
        break;
    case UART_CFG_PARITY_ODD:
        lcr |= UART_LCR_PEN;
        break;
    case UART_CFG_PARITY_EVEN:
        lcr |= UART_LCR_PEN | UART_LCR_EPS;
        break;
    case UART_CFG_PARITY_MARK:
        lcr |= UART_LCR_PEN | UART_LCR_SP;
        break;
    case UART_CFG_PARITY_SPACE:
        lcr |= UART_LCR_PEN | UART_LCR_EPS | UART_LCR_SP;
        break;
    default:
        return -ENOTSUP;
    }

    /* Set stop bits */
    switch (cfg->stop_bits) {
    case UART_CFG_STOP_BITS_1:
        break;
    case UART_CFG_STOP_BITS_2:
        lcr |= UART_LCR_STB;
        break;
    default:
        return -ENOTSUP;
    }

    /* Set divisor latch access bit */
    sys_write32(UART_LCR_DLAB, base + UART_LCR);

    /* Set baud rate */
    sys_write32(divisor & 0xFF, base + UART_DLL);
    sys_write32((divisor >> 8) & 0xFF, base + UART_DLM);

    /* Clear divisor latch access bit and set line control */
    sys_write32(lcr, base + UART_LCR);

    /* Configure flow control */
    if (cfg->flow_ctrl == UART_CFG_FLOW_CTRL_RTS_CTS) {
        sys_set_bits(base + UART_MCR, UART_MCR_AFCE);
    } else {
        sys_clear_bits(base + UART_MCR, UART_MCR_AFCE);
    }

    return 0;
}

static int uart_chip_config_get(const struct device *dev,
                                 struct uart_config *cfg)
{
    const struct uart_chip_config *dev_cfg = dev->config;

    /* Return initial configuration or stored runtime config */
    *cfg = dev_cfg->uart_cfg;

    return 0;
}
```

### Step 5: Implement Interrupt-Driven API

```c
static int uart_chip_fifo_fill(const struct device *dev,
                                const uint8_t *tx_data,
                                int size)
{
    const struct uart_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;
    int count = 0;

    while (count < size &&
           (sys_read32(base + UART_LSR) & UART_LSR_THRE)) {
        sys_write32(tx_data[count], base + UART_THR);
        count++;
    }

    return count;
}

static int uart_chip_fifo_read(const struct device *dev,
                                uint8_t *rx_data,
                                const int size)
{
    const struct uart_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;
    int count = 0;

    while (count < size &&
           (sys_read32(base + UART_LSR) & UART_LSR_DR)) {
        rx_data[count] = sys_read32(base + UART_RBR) & 0xFF;
        count++;
    }

    return count;
}

static void uart_chip_irq_tx_enable(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    sys_set_bits(cfg->base + UART_IER, UART_IER_THRI);
}

static void uart_chip_irq_tx_disable(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    sys_clear_bits(cfg->base + UART_IER, UART_IER_THRI);
}

static int uart_chip_irq_tx_ready(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    return !!(sys_read32(cfg->base + UART_LSR) & UART_LSR_THRE);
}

static int uart_chip_irq_tx_complete(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    return !!(sys_read32(cfg->base + UART_LSR) & UART_LSR_TEMT);
}

static void uart_chip_irq_rx_enable(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    sys_set_bits(cfg->base + UART_IER, UART_IER_RDI);
}

static void uart_chip_irq_rx_disable(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    sys_clear_bits(cfg->base + UART_IER, UART_IER_RDI);
}

static int uart_chip_irq_rx_ready(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    return !!(sys_read32(cfg->base + UART_LSR) & UART_LSR_DR);
}

static void uart_chip_irq_err_enable(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    sys_set_bits(cfg->base + UART_IER, UART_IER_RLSI);
}

static void uart_chip_irq_err_disable(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    sys_clear_bits(cfg->base + UART_IER, UART_IER_RLSI);
}

static int uart_chip_irq_is_pending(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    /* Return 1 if interrupt is pending (IIR bit 0 clear) */
    return !(sys_read32(cfg->base + UART_IIR) & BIT(0));
}

static int uart_chip_irq_update(const struct device *dev)
{
    /* Clear/acknowledge interrupts */
    return 1;
}

static void uart_chip_irq_callback_set(const struct device *dev,
                                        uart_irq_callback_user_data_t cb,
                                        void *user_data)
{
    struct uart_chip_data *data = dev->data;

    data->cb = cb;
    data->cb_data = user_data;
}

static void uart_chip_isr(const struct device *dev)
{
    struct uart_chip_data *data = dev->data;

    if (data->cb) {
        data->cb(dev, data->cb_data);
    }
}
```

### Step 6: Define API Structure

```c
static const struct uart_driver_api uart_chip_driver_api = {
    .poll_in = uart_chip_poll_in,
    .poll_out = uart_chip_poll_out,
    .err_check = uart_chip_err_check,
#ifdef CONFIG_UART_USE_RUNTIME_CONFIGURE
    .configure = uart_chip_configure,
    .config_get = uart_chip_config_get,
#endif
#ifdef CONFIG_UART_INTERRUPT_DRIVEN
    .fifo_fill = uart_chip_fifo_fill,
    .fifo_read = uart_chip_fifo_read,
    .irq_tx_enable = uart_chip_irq_tx_enable,
    .irq_tx_disable = uart_chip_irq_tx_disable,
    .irq_tx_ready = uart_chip_irq_tx_ready,
    .irq_tx_complete = uart_chip_irq_tx_complete,
    .irq_rx_enable = uart_chip_irq_rx_enable,
    .irq_rx_disable = uart_chip_irq_rx_disable,
    .irq_rx_ready = uart_chip_irq_rx_ready,
    .irq_err_enable = uart_chip_irq_err_enable,
    .irq_err_disable = uart_chip_irq_err_disable,
    .irq_is_pending = uart_chip_irq_is_pending,
    .irq_update = uart_chip_irq_update,
    .irq_callback_set = uart_chip_irq_callback_set,
#endif
};
```

### Step 7: Implement Init Function

```c
static int uart_chip_init(const struct device *dev)
{
    const struct uart_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;

#ifdef CONFIG_PINCTRL
    /* Apply pin configuration */
    int ret = pinctrl_apply_state(cfg->pcfg, PINCTRL_STATE_DEFAULT);
    if (ret < 0) {
        return ret;
    }
#endif

    /* Disable all interrupts */
    sys_write32(0, base + UART_IER);

    /* Enable and reset FIFOs */
    sys_write32(UART_FCR_FIFOE | UART_FCR_RFIFOR | UART_FCR_XFIFOR |
                UART_FCR_TRIGGER_14,
                base + UART_FCR);

    /* Apply initial UART configuration */
    uart_chip_configure(dev, &cfg->uart_cfg);

#ifdef CONFIG_UART_INTERRUPT_DRIVEN
    /* Configure IRQ */
    if (cfg->irq_config_func) {
        cfg->irq_config_func(dev);
    }
#endif

    return 0;
}
```

### Step 8: Device Instantiation Macro

```c
#ifdef CONFIG_PINCTRL
#define UART_CHIP_PINCTRL_DEFINE(n) PINCTRL_DT_INST_DEFINE(n);
#define UART_CHIP_PINCTRL_INIT(n) .pcfg = PINCTRL_DT_INST_DEV_CONFIG_GET(n),
#else
#define UART_CHIP_PINCTRL_DEFINE(n)
#define UART_CHIP_PINCTRL_INIT(n)
#endif

#ifdef CONFIG_UART_INTERRUPT_DRIVEN
#define UART_CHIP_IRQ_CONFIG(n)                                         \
static void uart_chip_irq_config_##n(const struct device *dev)          \
{                                                                       \
    IRQ_CONNECT(DT_INST_IRQN(n),                                        \
                DT_INST_IRQ(n, priority),                               \
                uart_chip_isr,                                          \
                DEVICE_DT_INST_GET(n),                                  \
                0);                                                     \
    irq_enable(DT_INST_IRQN(n));                                        \
}
#define UART_CHIP_IRQ_FUNC(n) .irq_config_func = uart_chip_irq_config_##n,
#else
#define UART_CHIP_IRQ_CONFIG(n)
#define UART_CHIP_IRQ_FUNC(n)
#endif

#define UART_CHIP_INIT(n)                                               \
    UART_CHIP_PINCTRL_DEFINE(n)                                         \
                                                                        \
    UART_CHIP_IRQ_CONFIG(n)                                             \
                                                                        \
    static struct uart_chip_data uart_chip_data_##n;                    \
                                                                        \
    static const struct uart_chip_config uart_chip_config_##n = {      \
        .base = DT_INST_REG_ADDR(n),                                    \
        .sys_clk_freq = DT_INST_PROP(n, clock_frequency),               \
        .uart_cfg = {                                                   \
            .baudrate = DT_INST_PROP_OR(n, current_speed, 115200),      \
            .parity = UART_CFG_PARITY_NONE,                             \
            .stop_bits = UART_CFG_STOP_BITS_1,                          \
            .data_bits = UART_CFG_DATA_BITS_8,                          \
            .flow_ctrl = UART_CFG_FLOW_CTRL_NONE,                       \
        },                                                              \
        UART_CHIP_IRQ_FUNC(n)                                           \
        UART_CHIP_PINCTRL_INIT(n)                                       \
    };                                                                  \
                                                                        \
    DEVICE_DT_INST_DEFINE(n,                                            \
                          uart_chip_init,                               \
                          NULL,                                         \
                          &uart_chip_data_##n,                          \
                          &uart_chip_config_##n,                        \
                          PRE_KERNEL_1,                                 \
                          CONFIG_SERIAL_INIT_PRIORITY,                  \
                          &uart_chip_driver_api);

DT_INST_FOREACH_STATUS_OKAY(UART_CHIP_INIT)
```

