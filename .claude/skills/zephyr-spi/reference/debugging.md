## Debugging Tips

### 1. Enable SPI Logging

```c
#define LOG_LEVEL LOG_LEVEL_DBG
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(spi_app);

LOG_HEXDUMP_DBG(tx_data, len, "SPI TX:");
LOG_HEXDUMP_DBG(rx_data, len, "SPI RX:");
```

### 2. Check Signal Quality with Logic Analyzer

Capture SPI signals:
- **SCLK**: Verify frequency matches config
- **MOSI/MISO**: Check data transitions
- **CS**: Verify active low/high polarity
- **Setup/Hold times**: Measure against datasheet

### 3. Verify Clock Mode

If communication fails, try different modes:

```c
/* Try all 4 modes */
const spi_operation_t modes[] = {
    SPI_OP_MODE_MASTER | SPI_WORD_SET(8),  /* Mode 0 */
    SPI_OP_MODE_MASTER | SPI_WORD_SET(8) | SPI_MODE_CPHA,  /* Mode 1 */
    SPI_OP_MODE_MASTER | SPI_WORD_SET(8) | SPI_MODE_CPOL,  /* Mode 2 */
    SPI_OP_MODE_MASTER | SPI_WORD_SET(8) | SPI_MODE_CPOL | SPI_MODE_CPHA,  /* Mode 3 */
};
```

### 4. Check Word Size

Ensure word size matches hardware:

```c
/* 8-bit transfers (most common) */
operation |= SPI_WORD_SET(8);

/* 16-bit transfers */
operation |= SPI_WORD_SET(16);
```

### 5. Common Errors

**-ENOTSUP (Not supported)**:
- Unsupported SPI mode
- Unsupported frequency
- Feature not implemented (e.g., slave mode)

**-EINVAL (Invalid argument)**:
- Invalid configuration
- NULL buffer with non-zero length
- Word size out of range

**-ENODEV (No device)**:
- SPI controller not ready
- CS GPIO not ready

**-EBUSY (Bus busy)**:
- Another transaction in progress
- Bus locked by another caller

### 6. Loopback Testing

Test hardware with loopback mode:

```c
struct spi_config test_config = {
    .frequency = 1000000,
    .operation = SPI_OP_MODE_MASTER | SPI_MODE_LOOP | SPI_WORD_SET(8),
    .slave = 0,
};

/* Connect MOSI to MISO, or use hardware loopback */
uint8_t tx_data[] = {0xAA, 0x55, 0xF0, 0x0F};
uint8_t rx_data[4] = {0};

/* TX and RX should match in loopback */
spi_transceive(dev, &test_config, &tx, &rx);
if (memcmp(tx_data, rx_data, 4) == 0) {
    printk("Loopback test PASSED\n");
}
```

