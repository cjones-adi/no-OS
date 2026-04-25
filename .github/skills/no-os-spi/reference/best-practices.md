# SPI Best Practices

Guidelines and recommendations for reliable SPI communication in no-OS drivers.

## General Best Practices

### 1. Always Check Return Values

```c
// BAD
no_os_spi_init(&spi_desc, &spi_init);
no_os_spi_write_and_read(spi_desc, data, 2);

// GOOD
int ret;

ret = no_os_spi_init(&spi_desc, &spi_init);
if (ret) {
    printf("SPI init failed: %d\n", ret);
    return ret;
}

ret = no_os_spi_write_and_read(spi_desc, data, 2);
if (ret) {
    printf("SPI transfer failed: %d\n", ret);
    goto error_cleanup;
}

error_cleanup:
    no_os_spi_remove(spi_desc);
    return ret;
```

### 2. Use Mutex Locking for Shared Bus

The framework provides automatic bus-level locking, but if you need additional synchronization:

```c
// Automatic bus locking (built-in)
no_os_spi_write_and_read(spi_desc, data, len);
// Bus mutex automatically locked/unlocked

// Additional application-level locking if needed
void *app_mutex;
no_os_mutex_init(&app_mutex);

no_os_mutex_lock(app_mutex);
// Multiple SPI operations
no_os_spi_write_and_read(spi_desc, cmd, 1);
no_os_spi_write_and_read(spi_desc, data, 10);
no_os_mutex_unlock(app_mutex);
```

### 3. Verify SPI Mode Matches Device Datasheet

```c
// Always check device datasheet for required SPI mode
// Example: Device requires CPOL=0, CPHA=0
struct no_os_spi_init_param spi_init = {
    .mode = NO_OS_SPI_MODE_0,  // Match datasheet exactly
    // ...
};

// Document the requirement in driver code
/**
 * @brief Initialize device
 * @note Device requires SPI Mode 0 (CPOL=0, CPHA=0)
 * @note Max SPI clock: 10 MHz (datasheet section 8.1)
 */
int device_init(struct device_desc **dev)
{
    // ...
}
```

### 4. Set Appropriate Clock Speed

```c
// Start slow for initial development and debugging
struct no_os_spi_init_param spi_init_debug = {
    .max_speed_hz = 100000,  // 100 kHz - reliable for debugging
    // ...
};

// Increase for production after validation
struct no_os_spi_init_param spi_init_prod = {
    .max_speed_hz = 10000000,  // 10 MHz - production speed
    // ...
};

// Document maximum speed from datasheet
#define DEVICE_MAX_SPI_SPEED_HZ  10000000  // From datasheet table 5
```

**Speed selection guidelines:**

- **Development/Debug**: 100 kHz - 1 MHz
- **Production**: Match device maximum (verify with scope)
- **High-speed**: > 10 MHz (requires careful PCB design)

### 5. Handle CS Timing Carefully

```c
// For devices with strict CS timing requirements
struct no_os_spi_msg msg = {
    .tx_buff = data,
    .rx_buff = NULL,
    .bytes_number = len,
    .cs_delay_first = 100,   // 100ns setup time
    .cs_delay_last = 50,     // 50ns hold time
    .cs_change = 1,          // Deassert CS after
};

// Document timing requirements
/**
 * CS setup time: min 100ns (datasheet figure 12)
 * CS hold time: min 50ns (datasheet figure 12)
 */
```

### 6. Use DMA for Large Transfers

```c
// Use polling for small transfers
if (len < 64) {
    ret = no_os_spi_write_and_read(spi_desc, data, len);
} else {
    // Use DMA for larger transfers (more efficient)
    struct no_os_spi_msg msg = {
        .tx_buff = tx_data,
        .rx_buff = rx_data,
        .bytes_number = len,
        .cs_change = 1,
    };
    ret = no_os_spi_transfer_dma(spi_desc, &msg, 1);
}
```

**DMA benefits:**
- Lower CPU utilization
- Higher throughput
- More consistent timing
- Better for real-time systems

**DMA considerations:**
- Buffer must be in DMA-accessible memory
- May require specific alignment
- Setup overhead (only worth it for larger transfers)

### 7. Check Platform-Specific Limitations

```c
// Some platforms have maximum transfer size
#define MAX_SPI_TRANSFER_SIZE  4096  // Platform limitation

int large_transfer(struct no_os_spi_desc *spi, uint8_t *data, uint32_t len)
{
    uint32_t offset = 0;
    int ret;

    // Break into smaller chunks if needed
    while (offset < len) {
        uint32_t chunk = (len - offset > MAX_SPI_TRANSFER_SIZE) ?
                         MAX_SPI_TRANSFER_SIZE : (len - offset);
        
        ret = no_os_spi_write_and_read(spi, &data[offset], chunk);
        if (ret)
            return ret;
        
        offset += chunk;
    }

    return 0;
}
```

### 8. Free Resources Properly

```c
int driver_init(struct device_desc **dev)
{
    struct device_desc *device;
    struct no_os_spi_desc *spi_desc;
    int ret;

    device = calloc(1, sizeof(*device));
    if (!device)
        return -ENOMEM;

    ret = no_os_spi_init(&spi_desc, &spi_init);
    if (ret) {
        free(device);  // Free device on SPI init failure
        return ret;
    }

    device->spi_desc = spi_desc;
    *dev = device;
    return 0;
}

int driver_remove(struct device_desc *dev)
{
    if (!dev)
        return -EINVAL;

    // Free SPI resources
    if (dev->spi_desc)
        no_os_spi_remove(dev->spi_desc);

    // Free device
    free(dev);
    return 0;
}
```

### 9. Test with Oscilloscope/Logic Analyzer

```c
// Add test points in critical paths for debugging
ret = no_os_spi_write_and_read(spi_desc, data, len);
// ← Connect logic analyzer here to verify:
//   - Clock frequency matches max_speed_hz
//   - SPI mode is correct (CPOL/CPHA)
//   - CS timing meets requirements
//   - Data integrity
```

**What to verify:**
- Clock frequency (actual vs requested)
- Clock polarity and phase
- CS assertion/deassertion timing
- Setup and hold times
- Data on MOSI/MISO lines

### 10. Document Platform Extras

```c
/**
 * @file max20370.c
 * @brief MAX20370 driver implementation
 * 
 * Platform-specific notes:
 * 
 * Maxim Platform:
 * - Requires max_spi_init_param.num_slaves = 1
 * - Requires max_spi_init_param.vssel = MXC_GPIO_VSSEL_VDDIO
 * - DMA support available via max_spi_init_param.dma_param
 * 
 * STM32 Platform:
 * - Uses Hardware CS on SPI_NSS pin
 * - Maximum speed limited by APB clock
 * 
 * Mbed Platform:
 * - Software CS recommended (use_sw_csb = true)
 * - Pin names must match target board
 */
```

## Code Organization Best Practices

### 1. Separate Platform-Specific Code

```c
// device_driver.c - Platform-independent
int device_init(struct device_desc **dev,
                struct device_init_param *param)
{
    // Generic device initialization
    // Uses no_os_spi.h interface only
}

// device_driver_platform.c - Platform helpers (optional)
#ifdef MAXIM_PLATFORM
int device_setup_maxim_extras(struct device_desc *dev)
{
    // Maxim-specific setup if needed
}
#endif
```

### 2. Use Consistent Error Handling

```c
// Define error codes consistently
#define DEVICE_SUCCESS      0
#define DEVICE_ERR_INIT    -1
#define DEVICE_ERR_COMM    -2
#define DEVICE_ERR_TIMEOUT -3

// Or use standard errno codes
#include <errno.h>
// -EINVAL, -ENOMEM, -EIO, -ETIMEDOUT, etc.
```

### 3. Implement Helper Functions

```c
// Create reusable helper functions for common operations
static int device_read_reg(struct device_desc *dev,
                          uint8_t reg, uint8_t *val)
{
    uint8_t data[2] = {reg | 0x80, 0x00};
    int ret;

    ret = no_os_spi_write_and_read(dev->spi_desc, data, 2);
    if (!ret)
        *val = data[1];
    
    return ret;
}

static int device_write_reg(struct device_desc *dev,
                           uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg & 0x7F, val};
    return no_os_spi_write_and_read(dev->spi_desc, data, 2);
}

// Use helpers in public API functions
int device_set_config(struct device_desc *dev, uint8_t config)
{
    if (!dev)
        return -EINVAL;

    return device_write_reg(dev, CONFIG_REG, config);
}
```

## Performance Best Practices

### 1. Minimize Transfers

```c
// BAD - Multiple transfers
device_write_reg(dev, REG_A, 0x01);
device_write_reg(dev, REG_B, 0x02);
device_write_reg(dev, REG_C, 0x03);

// GOOD - Burst write if supported
uint8_t config[] = {0x01, 0x02, 0x03};
device_write_burst(dev, REG_A, config, 3);
```

### 2. Use Transfer Messages for Sequences

```c
// BAD - Separate transfers (2x CS toggling)
device_write_reg(dev, CMD_REG, READ_CMD);
device_read_burst(dev, DATA_REG, data, 16);

// GOOD - Single transfer sequence
struct no_os_spi_msg msgs[] = {
    {
        .tx_buff = &read_cmd,
        .rx_buff = NULL,
        .bytes_number = 1,
        .cs_change = 0,  // Keep CS asserted
    },
    {
        .tx_buff = NULL,
        .rx_buff = data,
        .bytes_number = 16,
        .cs_change = 1,  // Deassert after
    },
};
no_os_spi_transfer(dev->spi_desc, msgs, 2);
```

### 3. Cache Frequently Read Values

```c
struct device_desc {
    struct no_os_spi_desc *spi_desc;
    uint8_t config_cache;     // Cached configuration
    bool config_valid;        // Cache validity flag
};

int device_get_config(struct device_desc *dev, uint8_t *config)
{
    int ret;

    if (!dev || !config)
        return -EINVAL;

    // Return cached value if valid
    if (dev->config_valid) {
        *config = dev->config_cache;
        return 0;
    }

    // Read from device
    ret = device_read_reg(dev, CONFIG_REG, config);
    if (!ret) {
        dev->config_cache = *config;
        dev->config_valid = true;
    }

    return ret;
}

int device_set_config(struct device_desc *dev, uint8_t config)
{
    int ret;

    if (!dev)
        return -EINVAL;

    ret = device_write_reg(dev, CONFIG_REG, config);
    if (!ret) {
        // Update cache
        dev->config_cache = config;
        dev->config_valid = true;
    }

    return ret;
}
```

## Safety and Reliability Best Practices

### 1. Validate Input Parameters

```c
int device_set_voltage(struct device_desc *dev, uint32_t mv)
{
    // Validate device pointer
    if (!dev)
        return -EINVAL;

    // Validate voltage range
    if (mv < DEVICE_MIN_VOLTAGE_MV || mv > DEVICE_MAX_VOLTAGE_MV) {
        printf("Voltage %u mV out of range [%u, %u]\n",
               mv, DEVICE_MIN_VOLTAGE_MV, DEVICE_MAX_VOLTAGE_MV);
        return -EINVAL;
    }

    // Proceed with valid parameters
    return device_set_voltage_internal(dev, mv);
}
```

### 2. Implement Retry Logic for Critical Operations

```c
#define SPI_RETRY_COUNT  3
#define SPI_RETRY_DELAY_MS  10

int device_critical_write(struct device_desc *dev,
                         uint8_t reg, uint8_t val)
{
    int ret;
    int retry;

    for (retry = 0; retry < SPI_RETRY_COUNT; retry++) {
        ret = device_write_reg(dev, reg, val);
        if (ret == 0)
            return 0;  // Success

        printf("SPI write failed (attempt %d/%d): %d\n",
               retry + 1, SPI_RETRY_COUNT, ret);

        if (retry < SPI_RETRY_COUNT - 1)
            no_os_mdelay(SPI_RETRY_DELAY_MS);
    }

    return ret;  // Failed after retries
}
```

### 3. Verify Critical Writes

```c
int device_write_and_verify(struct device_desc *dev,
                           uint8_t reg, uint8_t val)
{
    uint8_t readback;
    int ret;

    // Write
    ret = device_write_reg(dev, reg, val);
    if (ret)
        return ret;

    // Delay for write to settle
    no_os_udelay(100);

    // Read back
    ret = device_read_reg(dev, reg, &readback);
    if (ret)
        return ret;

    // Verify
    if (readback != val) {
        printf("Verify failed: wrote 0x%02X, read 0x%02X\n",
               val, readback);
        return -EIO;
    }

    return 0;
}
```

### 4. Add Sanity Checks

```c
int device_init(struct device_desc **dev,
                struct device_init_param *param)
{
    uint8_t chip_id;
    int ret;

    // Initialize SPI
    ret = no_os_spi_init(&spi_desc, &param->spi_init);
    if (ret)
        return ret;

    // Verify chip ID
    ret = device_read_reg_internal(spi_desc, CHIP_ID_REG, &chip_id);
    if (ret)
        goto error_spi;

    if (chip_id != EXPECTED_CHIP_ID) {
        printf("Chip ID mismatch: expected 0x%02X, got 0x%02X\n",
               EXPECTED_CHIP_ID, chip_id);
        ret = -ENODEV;
        goto error_spi;
    }

    // Allocate device
    *dev = calloc(1, sizeof(**dev));
    if (!*dev) {
        ret = -ENOMEM;
        goto error_spi;
    }

    (*dev)->spi_desc = spi_desc;
    return 0;

error_spi:
    no_os_spi_remove(spi_desc);
    return ret;
}
```

## Thread Safety Best Practices

### 1. Document Thread Safety

```c
/**
 * @brief Read device temperature
 * @param dev Device descriptor
 * @param temp Temperature in milli-degrees Celsius
 * @return 0 on success, negative error code otherwise
 * @note This function is thread-safe (uses internal SPI bus mutex)
 */
int device_read_temperature(struct device_desc *dev, int32_t *temp);
```

### 2. Protect Device State

```c
struct device_desc {
    struct no_os_spi_desc *spi_desc;
    void *state_mutex;       // Protect device state
    uint32_t sample_rate;    // Protected by mutex
    bool is_running;         // Protected by mutex
};

int device_set_sample_rate(struct device_desc *dev, uint32_t rate)
{
    int ret;

    if (!dev)
        return -EINVAL;

    no_os_mutex_lock(dev->state_mutex);
    
    // Update hardware
    ret = device_write_sample_rate_reg(dev, rate);
    if (!ret)
        dev->sample_rate = rate;  // Update cached value
    
    no_os_mutex_unlock(dev->state_mutex);
    
    return ret;
}
```

## Debugging Best Practices

### 1. Add Debug Prints (Conditional)

```c
#ifdef DEBUG_SPI
#define SPI_DEBUG(fmt, ...) printf("[SPI] " fmt "\n", ##__VA_ARGS__)
#else
#define SPI_DEBUG(fmt, ...)
#endif

int device_write_reg(struct device_desc *dev, uint8_t reg, uint8_t val)
{
    int ret;

    SPI_DEBUG("Write reg 0x%02X = 0x%02X", reg, val);
    
    ret = device_write_reg_internal(dev, reg, val);
    
    SPI_DEBUG("Write result: %d", ret);
    
    return ret;
}
```

### 2. Implement Register Dump Function

```c
void device_dump_registers(struct device_desc *dev)
{
    uint8_t val;
    int i;

    printf("Register dump:\n");
    for (i = 0; i < 0x20; i++) {
        if (device_read_reg(dev, i, &val) == 0)
            printf("  [0x%02X] = 0x%02X\n", i, val);
        else
            printf("  [0x%02X] = <read error>\n", i);
    }
}
```

### 3. Add Statistics Tracking

```c
struct device_desc {
    struct no_os_spi_desc *spi_desc;
    struct {
        uint32_t transfers;
        uint32_t errors;
        uint32_t retries;
    } stats;
};

int device_transfer_with_stats(struct device_desc *dev, ...)
{
    int ret;

    dev->stats.transfers++;
    
    ret = no_os_spi_write_and_read(dev->spi_desc, data, len);
    
    if (ret)
        dev->stats.errors++;
    
    return ret;
}

void device_print_stats(struct device_desc *dev)
{
    printf("SPI Statistics:\n");
    printf("  Transfers: %u\n", dev->stats.transfers);
    printf("  Errors: %u\n", dev->stats.errors);
    printf("  Error rate: %.2f%%\n",
           100.0 * dev->stats.errors / dev->stats.transfers);
}
```
