## Common Patterns and Best Practices

### 1. Check Device Ready

Always verify SPI bus is ready before use:

```c
if (!spi_is_ready_dt(&spi_dev)) {
    LOG_ERR("SPI device not ready");
    return -ENODEV;
}
```

### 2. Configure Clock Mode Correctly

Match device datasheet requirements:

```c
/* Mode 0: CPOL=0, CPHA=0 (most common) */
#define SPI_MODE_0  SPI_OP_MODE_MASTER | SPI_WORD_SET(8)

/* Mode 3: CPOL=1, CPHA=1 */
#define SPI_MODE_3  SPI_OP_MODE_MASTER | SPI_WORD_SET(8) | \
                    SPI_MODE_CPOL | SPI_MODE_CPHA
```

### 3. Use Static Buffers for DMA

Some drivers use DMA which requires specific memory regions:

```c
/* Use static or K_HEAP allocated buffers for DMA compatibility */
static uint8_t tx_buffer[256];
static uint8_t rx_buffer[256];
```

### 4. Handle CS Timing Requirements

Some devices need setup/hold delays:

```dts
sensor@0 {
    compatible = "vendor,sensor";
    reg = <0>;
    spi-max-frequency = <8000000>;
    spi-cs-setup-delay-ns = <100>;   /* 100ns before first clock */
    spi-cs-hold-delay-ns = <150>;    /* 150ns after last clock */
};
```

### 5. Optimize Transfers with Scatter-Gather

Avoid copying data - use multiple buffers:

```c
/* Good: No copying, efficient DMA */
struct spi_buf tx_bufs[] = {
    {.buf = &command, .len = 1},
    {.buf = large_data_block, .len = 1024},
};

/* Bad: Copying overhead */
uint8_t combined[1025];
combined[0] = command;
memcpy(&combined[1], large_data_block, 1024);
```

### 6. Bus Locking for Multi-Step Transactions

```c
/* Lock bus for exclusive access */
struct spi_config config_locked = spi_dev.config;
config_locked.operation |= SPI_LOCK_ON;

/* Do multi-step transaction */
spi_transceive(..., &config_locked, ...);  /* Locks */
/* ... more operations ... */

/* Release when done */
spi_release(spi_dev.bus, &config_locked);
```

