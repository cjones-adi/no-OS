## Driver Implementation Pattern

### Step 1: Define Register Map

```c
/* SPI controller registers */
#define SPI_CR1         0x00   /* Control register 1 */
#define SPI_CR2         0x04   /* Control register 2 */
#define SPI_SR          0x08   /* Status register */
#define SPI_DR          0x0C   /* Data register */
#define SPI_CRCPR       0x10   /* CRC polynomial */
#define SPI_RXCRCR      0x14   /* RX CRC register */
#define SPI_TXCRCR      0x18   /* TX CRC register */

/* Control register 1 bits */
#define SPI_CR1_CPHA           BIT(0)   /* Clock phase */
#define SPI_CR1_CPOL           BIT(1)   /* Clock polarity */
#define SPI_CR1_MSTR           BIT(2)   /* Master selection */
#define SPI_CR1_BR_SHIFT       3        /* Baud rate control shift */
#define SPI_CR1_BR_MASK        GENMASK(5, 3)  /* Baud rate mask */
#define SPI_CR1_SPE            BIT(6)   /* SPI enable */
#define SPI_CR1_LSBFIRST       BIT(7)   /* Frame format */
#define SPI_CR1_SSI            BIT(8)   /* Internal slave select */
#define SPI_CR1_SSM            BIT(9)   /* Software slave management */
#define SPI_CR1_RXONLY         BIT(10)  /* Receive only */
#define SPI_CR1_DFF            BIT(11)  /* Data frame format (8/16 bit) */
#define SPI_CR1_BIDIMODE       BIT(15)  /* Bidirectional mode */

/* Status register bits */
#define SPI_SR_RXNE            BIT(0)   /* RX buffer not empty */
#define SPI_SR_TXE             BIT(1)   /* TX buffer empty */
#define SPI_SR_BSY             BIT(7)   /* Busy flag */
#define SPI_SR_OVR             BIT(6)   /* Overrun flag */
```

### Step 2: Define Config and Data Structures

**Config structure** (ROM, from devicetree):

```c
struct spi_chip_config {
    uint32_t base;              /* Register base address */
    uint32_t clock_freq;        /* Peripheral clock frequency */
    void (*irq_config_func)(void); /* IRQ configuration function */
#ifdef CONFIG_PINCTRL
    const struct pinctrl_dev_config *pcfg; /* Pin configuration */
#endif
};
```

**Data structure** (RAM, runtime state):

```c
struct spi_chip_data {
    struct k_mutex lock;              /* Bus access mutex */
    struct k_sem sync;                /* Transfer completion semaphore */
    const struct spi_config *config;  /* Current device config */
    const struct spi_buf_set *tx_bufs; /* Current TX buffers */
    const struct spi_buf_set *rx_bufs; /* Current RX buffers */
    size_t tx_buf_idx;                /* Current TX buffer index */
    size_t rx_buf_idx;                /* Current RX buffer index */
    size_t tx_count;                  /* Bytes transmitted */
    size_t rx_count;                  /* Bytes received */
    int status;                       /* Transfer status */
};
```

### Step 3: Implement transceive Function

```c
static int spi_chip_transceive(const struct device *dev,
                                const struct spi_config *config,
                                const struct spi_buf_set *tx_bufs,
                                const struct spi_buf_set *rx_bufs)
{
    const struct spi_chip_config *cfg = dev->config;
    struct spi_chip_data *data = dev->data;
    uint32_t base = cfg->base;
    int ret = 0;

    /* Validate parameters */
    if (!config) {
        return -EINVAL;
    }

    /* Only master mode supported */
    if (SPI_OP_MODE_GET(config->operation) != SPI_OP_MODE_MASTER) {
        return -ENOTSUP;
    }

    /* Lock bus */
    k_mutex_lock(&data->lock, K_FOREVER);

    /* Configure SPI if config changed */
    if (data->config != config) {
        ret = spi_chip_configure(dev, config);
        if (ret < 0) {
            goto done;
        }
        data->config = config;
    }

    /* Assert chip select */
    ret = spi_chip_cs_ctrl(dev, config, true);
    if (ret < 0) {
        goto done;
    }

    /* Store transfer context */
    data->tx_bufs = tx_bufs;
    data->rx_bufs = rx_bufs;
    data->tx_buf_idx = 0;
    data->rx_buf_idx = 0;
    data->tx_count = 0;
    data->rx_count = 0;
    data->status = 0;

    /* Execute transfer (polled or interrupt-driven) */
    ret = spi_chip_transfer_sync(dev, tx_bufs, rx_bufs);

    /* Deassert chip select (if not holding) */
    if (!(config->operation & SPI_HOLD_ON_CS)) {
        spi_chip_cs_ctrl(dev, config, false);
    }

done:
    /* Unlock bus (unless locked) */
    if (!(config->operation & SPI_LOCK_ON)) {
        k_mutex_unlock(&data->lock);
    }

    return ret;
}

static int spi_chip_transfer_sync(const struct device *dev,
                                   const struct spi_buf_set *tx_bufs,
                                   const struct spi_buf_set *rx_bufs)
{
    const struct spi_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;
    size_t tx_len = 0, rx_len = 0;

    /* Calculate total lengths */
    if (tx_bufs) {
        for (size_t i = 0; i < tx_bufs->count; i++) {
            tx_len += tx_bufs->buffers[i].len;
        }
    }
    if (rx_bufs) {
        for (size_t i = 0; i < rx_bufs->count; i++) {
            rx_len += rx_bufs->buffers[i].len;
        }
    }

    size_t transfer_len = MAX(tx_len, rx_len);
    size_t tx_idx = 0, rx_idx = 0;
    size_t tx_buf_pos = 0, rx_buf_pos = 0;
    size_t tx_buf_num = 0, rx_buf_num = 0;

    /* Transfer loop */
    for (size_t i = 0; i < transfer_len; i++) {
        uint8_t tx_byte = 0xFF;  /* Default TX byte (idle) */

        /* Get TX byte if available */
        if (tx_bufs && tx_buf_num < tx_bufs->count) {
            const struct spi_buf *buf = &tx_bufs->buffers[tx_buf_num];

            if (buf->buf) {
                tx_byte = ((uint8_t *)buf->buf)[tx_buf_pos];
            }

            tx_buf_pos++;
            if (tx_buf_pos >= buf->len) {
                tx_buf_pos = 0;
                tx_buf_num++;
            }
        }

        /* Wait for TX buffer empty */
        while (!(sys_read32(base + SPI_SR) & SPI_SR_TXE)) {
            /* Timeout handling */
        }

        /* Send byte */
        sys_write32(tx_byte, base + SPI_DR);

        /* Wait for RX buffer not empty */
        while (!(sys_read32(base + SPI_SR) & SPI_SR_RXNE)) {
            /* Timeout handling */
        }

        /* Receive byte */
        uint8_t rx_byte = sys_read32(base + SPI_DR);

        /* Store RX byte if buffer available */
        if (rx_bufs && rx_buf_num < rx_bufs->count) {
            const struct spi_buf *buf = &rx_bufs->buffers[rx_buf_num];

            if (buf->buf) {
                ((uint8_t *)buf->buf)[rx_buf_pos] = rx_byte;
            }

            rx_buf_pos++;
            if (rx_buf_pos >= buf->len) {
                rx_buf_pos = 0;
                rx_buf_num++;
            }
        }
    }

    /* Wait until not busy */
    while (sys_read32(base + SPI_SR) & SPI_SR_BSY) {
        /* Timeout handling */
    }

    return 0;
}
```

### Step 4: Implement Configuration

```c
static int spi_chip_configure(const struct device *dev,
                               const struct spi_config *config)
{
    const struct spi_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;
    uint32_t cr1 = 0;
    uint32_t word_size = SPI_WORD_SIZE_GET(config->operation);

    /* Disable SPI during configuration */
    sys_clear_bits(base + SPI_CR1, SPI_CR1_SPE);

    /* Master mode */
    cr1 |= SPI_CR1_MSTR;

    /* Clock polarity and phase */
    if (config->operation & SPI_MODE_CPOL) {
        cr1 |= SPI_CR1_CPOL;
    }
    if (config->operation & SPI_MODE_CPHA) {
        cr1 |= SPI_CR1_CPHA;
    }

    /* Bit order */
    if (config->operation & SPI_TRANSFER_LSB) {
        cr1 |= SPI_CR1_LSBFIRST;
    }

    /* Calculate baud rate divisor */
    uint32_t divisor = cfg->clock_freq / config->frequency;
    uint32_t br = 0;

    /* Find closest power of 2 divisor (2, 4, 8, 16, 32, 64, 128, 256) */
    for (br = 0; br < 7; br++) {
        if (divisor <= (2U << br)) {
            break;
        }
    }

    cr1 |= (br << SPI_CR1_BR_SHIFT) & SPI_CR1_BR_MASK;

    /* Word size */
    if (word_size == 16) {
        cr1 |= SPI_CR1_DFF;  /* 16-bit mode */
    } else if (word_size != 8) {
        return -ENOTSUP;  /* Only 8 or 16 bit supported */
    }

    /* Software slave management for GPIO CS */
    if (spi_cs_is_gpio(config)) {
        cr1 |= SPI_CR1_SSM | SPI_CR1_SSI;
    }

    /* Write configuration */
    sys_write32(cr1, base + SPI_CR1);

    /* Enable SPI */
    sys_set_bits(base + SPI_CR1, SPI_CR1_SPE);

    return 0;
}
```

### Step 5: Implement Chip Select Control

```c
static int spi_chip_cs_ctrl(const struct device *dev,
                             const struct spi_config *config,
                             bool active)
{
    if (!spi_cs_is_gpio(config)) {
        /* Hardware CS - nothing to do */
        return 0;
    }

    const struct gpio_dt_spec *cs_gpio = &config->cs.gpio;

    if (!gpio_is_ready_dt(cs_gpio)) {
        return -ENODEV;
    }

    /* Apply CS delay if activating */
    if (active && config->cs.delay) {
        k_busy_wait(config->cs.delay);
    }

    /* Set GPIO level (respect CS polarity) */
    int level = active ? 1 : 0;
    if (!(config->operation & SPI_CS_ACTIVE_HIGH)) {
        level = !level;  /* Active low */
    }

    int ret = gpio_pin_set_dt(cs_gpio, level);

    /* Apply CS delay if deactivating */
    if (!active && config->cs.delay) {
        k_busy_wait(config->cs.delay);
    }

    return ret;
}
```

### Step 6: Implement Release Function

```c
static int spi_chip_release(const struct device *dev,
                             const struct spi_config *config)
{
    struct spi_chip_data *data = dev->data;

    /* Only release if this config owns the lock */
    if (data->config == config) {
        k_mutex_unlock(&data->lock);
        data->config = NULL;
        return 0;
    }

    return -EINVAL;
}
```

### Step 7: Define API Structure

```c
static const struct spi_driver_api spi_chip_driver_api = {
    .transceive = spi_chip_transceive,
    .release = spi_chip_release,
};
```

### Step 8: Implement Init Function

```c
static int spi_chip_init(const struct device *dev)
{
    const struct spi_chip_config *cfg = dev->config;
    struct spi_chip_data *data = dev->data;

    /* Initialize mutex and semaphore */
    k_mutex_init(&data->lock);
    k_sem_init(&data->sync, 0, 1);

#ifdef CONFIG_PINCTRL
    /* Apply pin configuration */
    int ret = pinctrl_apply_state(cfg->pcfg, PINCTRL_STATE_DEFAULT);
    if (ret < 0) {
        return ret;
    }
#endif

    /* Configure IRQ (if interrupt-driven) */
    if (cfg->irq_config_func) {
        cfg->irq_config_func();
    }

    /* Perform hardware initialization */
    /* ... reset controller, set defaults, etc. ... */

    return 0;
}
```

### Step 9: Device Instantiation Macro

```c
#ifdef CONFIG_PINCTRL
#define SPI_CHIP_PINCTRL_DEFINE(n) PINCTRL_DT_INST_DEFINE(n);
#define SPI_CHIP_PINCTRL_INIT(n) .pcfg = PINCTRL_DT_INST_DEV_CONFIG_GET(n),
#else
#define SPI_CHIP_PINCTRL_DEFINE(n)
#define SPI_CHIP_PINCTRL_INIT(n)
#endif

#define SPI_CHIP_IRQ_CONFIG(n)                                          \
static void spi_chip_irq_config_##n(void)                               \
{                                                                       \
    IRQ_CONNECT(DT_INST_IRQN(n),                                        \
                DT_INST_IRQ(n, priority),                               \
                spi_chip_isr,                                           \
                DEVICE_DT_INST_GET(n),                                  \
                0);                                                     \
    irq_enable(DT_INST_IRQN(n));                                        \
}

#define SPI_CHIP_INIT(n)                                                \
    SPI_CHIP_PINCTRL_DEFINE(n)                                          \
                                                                        \
    SPI_CHIP_IRQ_CONFIG(n)                                              \
                                                                        \
    static struct spi_chip_data spi_chip_data_##n;                      \
                                                                        \
    static const struct spi_chip_config spi_chip_config_##n = {         \
        .base = DT_INST_REG_ADDR(n),                                    \
        .clock_freq = DT_INST_PROP(n, clock_frequency),                 \
        .irq_config_func = spi_chip_irq_config_##n,                     \
        SPI_CHIP_PINCTRL_INIT(n)                                        \
    };                                                                  \
                                                                        \
    SPI_DEVICE_DT_INST_DEFINE(n,                                        \
                              spi_chip_init,                            \
                              NULL,                                     \
                              &spi_chip_data_##n,                       \
                              &spi_chip_config_##n,                     \
                              POST_KERNEL,                              \
                              CONFIG_SPI_INIT_PRIORITY,                 \
                              &spi_chip_driver_api);

DT_INST_FOREACH_STATUS_OKAY(SPI_CHIP_INIT)
```

