## Consumer API Usage

### Using spi_dt_spec

```c
#include <zephyr/drivers/spi.h>

static const struct spi_dt_spec spi_dev = SPI_DT_SPEC_GET(
    DT_NODELABEL(accel),
    SPI_OP_MODE_MASTER | SPI_WORD_SET(8) | SPI_TRANSFER_MSB,
    0  /* Extra delay */
);

int sensor_init(void)
{
    if (!spi_is_ready_dt(&spi_dev)) {
        printk("SPI device not ready\n");
        return -ENODEV;
    }

    /* SPI is ready to use */
    return 0;
}
```

### Basic SPI Write

```c
int spi_write_reg(uint8_t reg, uint8_t value)
{
    uint8_t tx_data[2] = {reg, value};

    struct spi_buf tx_buf = {
        .buf = tx_data,
        .len = sizeof(tx_data),
    };

    struct spi_buf_set tx = {
        .buffers = &tx_buf,
        .count = 1,
    };

    return spi_write_dt(&spi_dev, &tx);
}
```

### Basic SPI Read

```c
int spi_read_reg(uint8_t reg, uint8_t *value)
{
    uint8_t tx_data = reg | 0x80;  /* Set read bit */
    uint8_t rx_data[2];

    struct spi_buf tx_buf = {
        .buf = &tx_data,
        .len = 1,
    };

    struct spi_buf rx_buf = {
        .buf = rx_data,
        .len = sizeof(rx_data),
    };

    struct spi_buf_set tx = {
        .buffers = &tx_buf,
        .count = 1,
    };

    struct spi_buf_set rx = {
        .buffers = &rx_buf,
        .count = 1,
    };

    int ret = spi_transceive_dt(&spi_dev, &tx, &rx);
    if (ret == 0) {
        *value = rx_data[1];  /* Data is in second byte */
    }

    return ret;
}
```

### Burst Read

```c
int spi_burst_read(uint8_t start_reg, uint8_t *data, size_t len)
{
    uint8_t tx_cmd = start_reg | 0x80 | 0x40;  /* Read + auto-increment */

    struct spi_buf tx_buf = {
        .buf = &tx_cmd,
        .len = 1,
    };

    struct spi_buf rx_bufs[2] = {
        {
            .buf = NULL,      /* Discard first byte (during command) */
            .len = 1,
        },
        {
            .buf = data,
            .len = len,
        },
    };

    struct spi_buf_set tx = {
        .buffers = &tx_buf,
        .count = 1,
    };

    struct spi_buf_set rx = {
        .buffers = rx_bufs,
        .count = 2,
    };

    return spi_transceive_dt(&spi_dev, &tx, &rx);
}
```

### Scatter-Gather Transfer

```c
int spi_write_multi_buffers(void)
{
    static const uint8_t header[] = {0x02, 0x00, 0x00};  /* Write command */
    static uint8_t data_block1[256];
    static uint8_t data_block2[256];

    struct spi_buf tx_bufs[3] = {
        {
            .buf = (void *)header,
            .len = sizeof(header),
        },
        {
            .buf = data_block1,
            .len = sizeof(data_block1),
        },
        {
            .buf = data_block2,
            .len = sizeof(data_block2),
        },
    };

    struct spi_buf_set tx = {
        .buffers = tx_bufs,
        .count = 3,
    };

    /* This will transfer all three buffers without releasing CS */
    return spi_write_dt(&spi_dev, &tx);
}
```

### Holding Chip Select Across Multiple Calls

```c
int spi_transaction_with_hold(void)
{
    /* Modify config to hold CS */
    struct spi_config config_hold = spi_dev.config;
    config_hold.operation |= SPI_HOLD_ON_CS;

    struct spi_dt_spec spi_hold = spi_dev;
    spi_hold.config = config_hold;

    /* First transfer - CS stays active */
    uint8_t cmd1 = 0x01;
    struct spi_buf tx1 = {.buf = &cmd1, .len = 1};
    struct spi_buf_set tx_set1 = {.buffers = &tx1, .count = 1};
    spi_write_dt(&spi_hold, &tx_set1);

    /* Second transfer - still holding CS */
    uint8_t cmd2 = 0x02;
    struct spi_buf tx2 = {.buf = &cmd2, .len = 1};
    struct spi_buf_set tx_set2 = {.buffers = &tx2, .count = 1};
    spi_write_dt(&spi_hold, &tx_set2);

    /* Final transfer - release CS */
    uint8_t cmd3 = 0x03;
    struct spi_buf tx3 = {.buf = &cmd3, .len = 1};
    struct spi_buf_set tx_set3 = {.buffers = &tx3, .count = 1};
    spi_write_dt(&spi_dev, &tx_set3);  /* Normal config, CS releases */

    return 0;
}
```

