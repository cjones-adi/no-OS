## Driver Implementation Pattern

### Step 1: Define Register Map

```c
/* I2C controller registers */
#define I2C_CON         0x00   /* Control register */
#define I2C_TAR         0x04   /* Target address */
#define I2C_DATA_CMD    0x10   /* Data buffer and command */
#define I2C_SS_SCL_HCNT 0x14   /* Standard speed SCL high count */
#define I2C_SS_SCL_LCNT 0x18   /* Standard speed SCL low count */
#define I2C_FS_SCL_HCNT 0x1C   /* Fast speed SCL high count */
#define I2C_FS_SCL_LCNT 0x20   /* Fast speed SCL low count */
#define I2C_INTR_STAT   0x2C   /* Interrupt status */
#define I2C_INTR_MASK   0x30   /* Interrupt mask */
#define I2C_RAW_INTR_STAT 0x34 /* Raw interrupt status */
#define I2C_CLR_INTR    0x40   /* Clear interrupt */
#define I2C_ENABLE      0x6C   /* Enable control */
#define I2C_STATUS      0x70   /* Status register */

/* Control register bits */
#define I2C_CON_MASTER_MODE        BIT(0)
#define I2C_CON_SPEED_MASK         GENMASK(2, 1)
#define I2C_CON_SPEED_STD          (1 << 1)
#define I2C_CON_SPEED_FAST         (2 << 1)
#define I2C_CON_10BIT_ADDR_MASTER  BIT(4)
#define I2C_CON_RESTART_EN         BIT(5)

/* Data command register bits */
#define I2C_DATA_CMD_DAT_MASK      GENMASK(7, 0)
#define I2C_DATA_CMD_CMD_READ      BIT(8)
#define I2C_DATA_CMD_STOP          BIT(9)
#define I2C_DATA_CMD_RESTART       BIT(10)

/* Status bits */
#define I2C_STATUS_ACTIVITY        BIT(0)
#define I2C_STATUS_TFNF            BIT(1)  /* TX FIFO not full */
#define I2C_STATUS_TFE             BIT(2)  /* TX FIFO empty */
#define I2C_STATUS_RFNE            BIT(3)  /* RX FIFO not empty */
#define I2C_STATUS_RFF             BIT(4)  /* RX FIFO full */
```

### Step 2: Define Config and Data Structures

**Config structure** (ROM, from devicetree):

```c
struct i2c_chip_config {
    uint32_t base;              /* Register base address */
    uint32_t clock_freq;        /* Input clock frequency */
    uint32_t bitrate;           /* I2C bus speed (from DT) */
    void (*irq_config_func)(void); /* IRQ configuration function */
#ifdef CONFIG_PINCTRL
    const struct pinctrl_dev_config *pcfg; /* Pin configuration */
#endif
};
```

**Data structure** (RAM, runtime state):

```c
struct i2c_chip_data {
    struct k_mutex lock;        /* Bus access mutex */
    struct k_sem device_sync_sem; /* Transfer completion semaphore */
    uint32_t dev_config;        /* Current configuration */
    struct i2c_msg *msgs;       /* Current message array */
    uint8_t msg_count;          /* Number of messages */
    uint8_t msg_index;          /* Current message index */
    uint32_t bytes_transferred; /* Bytes transferred in current msg */
    int transfer_status;        /* Transfer result */
};
```

### Step 3: Implement configure Function

```c
static int i2c_chip_configure(const struct device *dev, uint32_t dev_config)
{
    const struct i2c_chip_config *cfg = dev->config;
    struct i2c_chip_data *data = dev->data;
    uint32_t base = cfg->base;
    uint32_t speed = I2C_SPEED_GET(dev_config);
    uint32_t ic_con = 0;
    uint32_t hcnt, lcnt;

    /* Disable I2C controller */
    sys_write32(0, base + I2C_ENABLE);

    /* Configure speed */
    ic_con = I2C_CON_MASTER_MODE | I2C_CON_RESTART_EN;

    switch (speed) {
    case I2C_SPEED_STANDARD:
        ic_con |= I2C_CON_SPEED_STD;
        /* Calculate timing for 100kHz */
        hcnt = (cfg->clock_freq / 100000) / 2;
        lcnt = hcnt;
        sys_write32(hcnt, base + I2C_SS_SCL_HCNT);
        sys_write32(lcnt, base + I2C_SS_SCL_LCNT);
        break;

    case I2C_SPEED_FAST:
        ic_con |= I2C_CON_SPEED_FAST;
        /* Calculate timing for 400kHz */
        hcnt = (cfg->clock_freq / 400000) / 2;
        lcnt = hcnt;
        sys_write32(hcnt, base + I2C_FS_SCL_HCNT);
        sys_write32(lcnt, base + I2C_FS_SCL_LCNT);
        break;

    default:
        return -ENOTSUP;
    }

    /* Check for 10-bit addressing */
    if (dev_config & I2C_ADDR_10_BITS) {
        ic_con |= I2C_CON_10BIT_ADDR_MASTER;
    }

    /* Write control register */
    sys_write32(ic_con, base + I2C_CON);

    /* Store configuration */
    data->dev_config = dev_config;

    /* Enable controller */
    sys_write32(1, base + I2C_ENABLE);

    return 0;
}
```

### Step 4: Implement transfer Function

```c
static int i2c_chip_transfer(const struct device *dev,
                              struct i2c_msg *msgs,
                              uint8_t num_msgs,
                              uint16_t addr)
{
    const struct i2c_chip_config *cfg = dev->config;
    struct i2c_chip_data *data = dev->data;
    uint32_t base = cfg->base;
    int ret = 0;

    if (!num_msgs) {
        return 0;
    }

    /* Lock bus */
    k_mutex_lock(&data->lock, K_FOREVER);

    /* Store transfer context */
    data->msgs = msgs;
    data->msg_count = num_msgs;
    data->msg_index = 0;
    data->bytes_transferred = 0;
    data->transfer_status = 0;

    /* Set target address */
    sys_write32(addr, base + I2C_TAR);

    /* Execute transfer (polled or interrupt-driven) */
    for (uint8_t i = 0; i < num_msgs; i++) {
        struct i2c_msg *msg = &msgs[i];

        if (msg->flags & I2C_MSG_READ) {
            ret = i2c_chip_msg_read(dev, msg, (i == num_msgs - 1));
        } else {
            ret = i2c_chip_msg_write(dev, msg, (i == num_msgs - 1));
        }

        if (ret < 0) {
            break;
        }
    }

    /* Unlock bus */
    k_mutex_unlock(&data->lock);

    return ret;
}

static int i2c_chip_msg_write(const struct device *dev,
                               struct i2c_msg *msg,
                               bool is_last_msg)
{
    const struct i2c_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;

    for (uint32_t i = 0; i < msg->len; i++) {
        uint32_t cmd = msg->buf[i];

        /* Add STOP on last byte of last message if requested */
        if (i == (msg->len - 1) && is_last_msg && (msg->flags & I2C_MSG_STOP)) {
            cmd |= I2C_DATA_CMD_STOP;
        }

        /* Add RESTART on first byte if requested */
        if (i == 0 && (msg->flags & I2C_MSG_RESTART)) {
            cmd |= I2C_DATA_CMD_RESTART;
        }

        /* Wait for TX FIFO not full */
        while (!(sys_read32(base + I2C_STATUS) & I2C_STATUS_TFNF)) {
            /* Could add timeout here */
        }

        /* Write data */
        sys_write32(cmd, base + I2C_DATA_CMD);
    }

    /* Wait for completion */
    while (sys_read32(base + I2C_STATUS) & I2C_STATUS_ACTIVITY) {
        /* Could add timeout here */
    }

    return 0;
}

static int i2c_chip_msg_read(const struct device *dev,
                              struct i2c_msg *msg,
                              bool is_last_msg)
{
    const struct i2c_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;

    for (uint32_t i = 0; i < msg->len; i++) {
        uint32_t cmd = I2C_DATA_CMD_CMD_READ;

        /* Add STOP on last byte of last message if requested */
        if (i == (msg->len - 1) && is_last_msg && (msg->flags & I2C_MSG_STOP)) {
            cmd |= I2C_DATA_CMD_STOP;
        }

        /* Add RESTART on first byte if requested */
        if (i == 0 && (msg->flags & I2C_MSG_RESTART)) {
            cmd |= I2C_DATA_CMD_RESTART;
        }

        /* Send read command */
        sys_write32(cmd, base + I2C_DATA_CMD);

        /* Wait for RX data */
        while (!(sys_read32(base + I2C_STATUS) & I2C_STATUS_RFNE)) {
            /* Could add timeout here */
        }

        /* Read data */
        msg->buf[i] = sys_read32(base + I2C_DATA_CMD) & 0xFF;
    }

    return 0;
}
```

### Step 5: Implement Bus Recovery (Optional)

```c
static int i2c_chip_recover_bus(const struct device *dev)
{
    const struct i2c_chip_config *cfg = dev->config;
    uint32_t base = cfg->base;

    /* Disable controller */
    sys_write32(0, base + I2C_ENABLE);

    /* Toggle SCL 9 times to clear stuck SDA */
    /* This is hardware-specific - some chips have automatic recovery */

    /* Re-enable controller */
    sys_write32(1, base + I2C_ENABLE);

    return 0;
}
```

### Step 6: Define API Structure

```c
static const struct i2c_driver_api i2c_chip_driver_api = {
    .configure = i2c_chip_configure,
    .transfer = i2c_chip_transfer,
    .recover_bus = i2c_chip_recover_bus,
};
```

### Step 7: Implement Init Function

```c
static int i2c_chip_init(const struct device *dev)
{
    const struct i2c_chip_config *cfg = dev->config;
    struct i2c_chip_data *data = dev->data;
    uint32_t bitrate_cfg;
    int ret;

    /* Initialize mutex and semaphore */
    k_mutex_init(&data->lock);
    k_sem_init(&data->device_sync_sem, 0, 1);

#ifdef CONFIG_PINCTRL
    /* Apply pin configuration */
    ret = pinctrl_apply_state(cfg->pcfg, PINCTRL_STATE_DEFAULT);
    if (ret < 0) {
        return ret;
    }
#endif

    /* Configure IRQ (if interrupt-driven) */
    if (cfg->irq_config_func) {
        cfg->irq_config_func();
    }

    /* Configure initial bus speed from devicetree */
    bitrate_cfg = I2C_MODE_CONTROLLER | I2C_SPEED_SET(I2C_SPEED_DT);
    ret = i2c_chip_configure(dev, bitrate_cfg);
    if (ret < 0) {
        return ret;
    }

    return 0;
}
```

### Step 8: Device Instantiation Macro

```c
#ifdef CONFIG_PINCTRL
#define I2C_CHIP_PINCTRL_DEFINE(n) PINCTRL_DT_INST_DEFINE(n);
#define I2C_CHIP_PINCTRL_INIT(n) .pcfg = PINCTRL_DT_INST_DEV_CONFIG_GET(n),
#else
#define I2C_CHIP_PINCTRL_DEFINE(n)
#define I2C_CHIP_PINCTRL_INIT(n)
#endif

#define I2C_CHIP_IRQ_CONFIG(n)                                          \
static void i2c_chip_irq_config_##n(void)                               \
{                                                                       \
    IRQ_CONNECT(DT_INST_IRQN(n),                                        \
                DT_INST_IRQ(n, priority),                               \
                i2c_chip_isr,                                           \
                DEVICE_DT_INST_GET(n),                                  \
                0);                                                     \
    irq_enable(DT_INST_IRQN(n));                                        \
}

#define I2C_CHIP_INIT(n)                                                \
    I2C_CHIP_PINCTRL_DEFINE(n)                                          \
                                                                        \
    I2C_CHIP_IRQ_CONFIG(n)                                              \
                                                                        \
    static struct i2c_chip_data i2c_chip_data_##n;                      \
                                                                        \
    static const struct i2c_chip_config i2c_chip_config_##n = {         \
        .base = DT_INST_REG_ADDR(n),                                    \
        .clock_freq = DT_INST_PROP(n, clock_frequency),                 \
        .bitrate = DT_INST_PROP(n, clock_frequency),                    \
        .irq_config_func = i2c_chip_irq_config_##n,                     \
        I2C_CHIP_PINCTRL_INIT(n)                                        \
    };                                                                  \
                                                                        \
    I2C_DEVICE_DT_INST_DEFINE(n,                                        \
                              i2c_chip_init,                            \
                              NULL,                                     \
                              &i2c_chip_data_##n,                       \
                              &i2c_chip_config_##n,                     \
                              POST_KERNEL,                              \
                              CONFIG_I2C_INIT_PRIORITY,                 \
                              &i2c_chip_driver_api);

DT_INST_FOREACH_STATUS_OKAY(I2C_CHIP_INIT)
```

