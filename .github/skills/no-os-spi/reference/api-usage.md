# SPI API Usage Patterns

Common usage patterns and practical examples for SPI operations.

## SPI Transfer Functions

### 1. no_os_spi_write_and_read() - Simple Transfer

**Function signature:**

```c
int32_t no_os_spi_write_and_read(struct no_os_spi_desc *desc,
                                 uint8_t *data,
                                 uint16_t bytes_number);
```

**Use case:** Basic full-duplex transfer (same buffer for TX/RX)

**Behavior:**
1. Assert CS
2. Shift out `data` on MOSI
3. Simultaneously shift in on MISO
4. Replace `data` buffer with received data
5. Deassert CS

**Example: Read register**

```c
uint8_t cmd[2] = {0x80, 0x00};  // Read command + dummy byte
ret = no_os_spi_write_and_read(spi_desc, cmd, 2);
// cmd[1] now contains register value

printf("Register value: 0x%02X\n", cmd[1]);
```

**Example: Write register**

```c
uint8_t cmd[2] = {0x01, 0xAB};  // Write command + data
ret = no_os_spi_write_and_read(spi_desc, cmd, 2);
// Register 0x01 now contains 0xAB
```

### 2. no_os_spi_transfer() - Multiple Messages

**Function signature:**

```c
int32_t no_os_spi_transfer(struct no_os_spi_desc *desc,
                           struct no_os_spi_msg *msgs,
                           uint32_t len);
```

**Use case:** Complex multi-transfer sequences with separate TX/RX buffers

**Example: Write then read with separate buffers**

```c
uint8_t tx_cmd[1] = {0x03};      // Read command
uint8_t rx_data[4];              // Receive buffer

struct no_os_spi_msg msgs[] = {
    {
        .tx_buff = tx_cmd,
        .rx_buff = NULL,         // Discard RX during command
        .bytes_number = 1,
        .cs_change = 0,          // Keep CS asserted
    },
    {
        .tx_buff = NULL,         // Send 0x00 during read
        .rx_buff = rx_data,
        .bytes_number = 4,
        .cs_change = 1,          // Deassert CS after
    },
};

ret = no_os_spi_transfer(spi_desc, msgs, 2);
// rx_data now contains 4 bytes read from device
```

**Example: Complex sequence with timing**

```c
struct no_os_spi_msg msgs[] = {
    {
        .tx_buff = command,
        .rx_buff = NULL,
        .bytes_number = 1,
        .cs_change = 0,
        .cs_delay_first = 100,    // 100ns delay after CS assert
    },
    {
        .tx_buff = address,
        .rx_buff = NULL,
        .bytes_number = 2,
        .cs_change = 0,
    },
    {
        .tx_buff = NULL,
        .rx_buff = data,
        .bytes_number = 256,
        .cs_change = 1,
        .cs_delay_last = 50,      // 50ns delay before CS deassert
    },
};

ret = no_os_spi_transfer(spi_desc, msgs, 3);
```

### 3. no_os_spi_transfer_dma() - DMA Transfer (Blocking)

**Function signature:**

```c
int32_t no_os_spi_transfer_dma(struct no_os_spi_desc *desc,
                               struct no_os_spi_msg *msgs,
                               uint32_t len);
```

**Use case:** High-speed transfers with DMA, wait for completion

**Example: Large buffer transfer**

```c
uint8_t large_tx_buffer[1024];
uint8_t large_rx_buffer[1024];

// Fill TX buffer with data
for (int i = 0; i < 1024; i++)
    large_tx_buffer[i] = i & 0xFF;

struct no_os_spi_msg dma_msg = {
    .tx_buff = large_tx_buffer,
    .rx_buff = large_rx_buffer,
    .bytes_number = 1024,
    .cs_change = 1,
};

ret = no_os_spi_transfer_dma(spi_desc, &dma_msg, 1);
// Blocks until transfer complete
// large_rx_buffer now contains received data
```

**When to use DMA:**
- Transfers > 64 bytes (platform-dependent threshold)
- High-speed continuous data streams
- CPU-intensive applications (free CPU for other tasks)
- Real-time requirements (lower latency jitter)

### 4. no_os_spi_transfer_dma_async() - DMA Transfer (Non-blocking)

**Function signature:**

```c
int32_t no_os_spi_transfer_dma_async(struct no_os_spi_desc *desc,
                                     struct no_os_spi_msg *msgs,
                                     uint32_t len,
                                     void (*callback)(void *),
                                     void *ctx);
```

**Use case:** Start DMA transfer and return immediately, callback when done

**Example: Asynchronous transfer with callback**

```c
struct transfer_context {
    uint8_t *buffer;
    uint32_t length;
    volatile bool complete;
};

void spi_complete_callback(void *ctx)
{
    struct transfer_context *context = ctx;
    context->complete = true;
    printf("SPI transfer of %u bytes complete!\n", context->length);
}

int main(void)
{
    struct transfer_context ctx = {
        .buffer = rx_buffer,
        .length = 512,
        .complete = false,
    };

    struct no_os_spi_msg async_msg = {
        .tx_buff = tx_buffer,
        .rx_buff = rx_buffer,
        .bytes_number = 512,
        .cs_change = 1,
    };

    ret = no_os_spi_transfer_dma_async(spi_desc, &async_msg, 1,
                                       spi_complete_callback, &ctx);
    // Returns immediately
    
    // Do other work while transfer in progress
    do_other_work();
    
    // Wait for completion
    while (!ctx.complete);
    
    // Process received data
    process_data(ctx.buffer, ctx.length);
}
```

## Common Patterns

### Pattern 1: Register Read/Write

```c
// Write register
int32_t spi_write_reg(struct no_os_spi_desc *spi, uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg & 0x7F, val};  // Clear MSB for write
    return no_os_spi_write_and_read(spi, data, 2);
}

// Read register
int32_t spi_read_reg(struct no_os_spi_desc *spi, uint8_t reg, uint8_t *val)
{
    uint8_t data[2] = {reg | 0x80, 0x00};  // Set MSB for read
    int ret = no_os_spi_write_and_read(spi, data, 2);
    if (!ret)
        *val = data[1];
    return ret;
}

// Usage
uint8_t reg_value;
ret = spi_read_reg(spi_desc, 0x01, &reg_value);
if (!ret)
    printf("Register 0x01 = 0x%02X\n", reg_value);
```

### Pattern 2: Burst Read

```c
int32_t spi_read_burst(struct no_os_spi_desc *spi, uint8_t reg,
                       uint8_t *data, uint16_t len)
{
    struct no_os_spi_msg msgs[] = {
        {
            .tx_buff = &reg,
            .rx_buff = NULL,
            .bytes_number = 1,
            .cs_change = 0,
        },
        {
            .tx_buff = NULL,
            .rx_buff = data,
            .bytes_number = len,
            .cs_change = 1,
        },
    };

    return no_os_spi_transfer(spi, msgs, 2);
}

// Usage
uint8_t fifo_data[128];
ret = spi_read_burst(spi_desc, 0x40, fifo_data, 128);
```

### Pattern 3: Burst Write

```c
int32_t spi_write_burst(struct no_os_spi_desc *spi, uint8_t reg,
                        uint8_t *data, uint16_t len)
{
    struct no_os_spi_msg msgs[] = {
        {
            .tx_buff = &reg,
            .rx_buff = NULL,
            .bytes_number = 1,
            .cs_change = 0,
        },
        {
            .tx_buff = data,
            .rx_buff = NULL,
            .bytes_number = len,
            .cs_change = 1,
        },
    };

    return no_os_spi_transfer(spi, msgs, 2);
}

// Usage
uint8_t config_data[10] = {0x01, 0x02, 0x03, ...};
ret = spi_write_burst(spi_desc, 0x20, config_data, 10);
```

### Pattern 4: Multi-slave Selection

```c
struct no_os_spi_init_param spi_init_template = {
    .device_id = 0,
    .max_speed_hz = 1000000,
    .mode = NO_OS_SPI_MODE_0,
    .platform_ops = &max_spi_ops,
    .extra = &max_extra,
};

// Initialize multiple slaves on same bus
struct no_os_spi_desc *spi_adc, *spi_dac;

spi_init_template.chip_select = 0;
no_os_spi_init(&spi_adc, &spi_init_template);

spi_init_template.chip_select = 1;
no_os_spi_init(&spi_dac, &spi_init_template);

// Automatic bus locking ensures no conflicts
no_os_spi_write_and_read(spi_adc, adc_data, 2);
no_os_spi_write_and_read(spi_dac, dac_data, 2);
```

### Pattern 5: Read-Modify-Write

```c
int32_t spi_update_reg(struct no_os_spi_desc *spi, uint8_t reg,
                       uint8_t mask, uint8_t value)
{
    uint8_t reg_val;
    int ret;

    // Read current value
    ret = spi_read_reg(spi, reg, &reg_val);
    if (ret)
        return ret;

    // Modify
    reg_val = (reg_val & ~mask) | (value & mask);

    // Write back
    return spi_write_reg(spi, reg, reg_val);
}

// Usage: Set bits [3:0] to 0xA, preserve bits [7:4]
ret = spi_update_reg(spi_desc, 0x05, 0x0F, 0x0A);
```

### Pattern 6: Verify Write

```c
int32_t spi_write_and_verify(struct no_os_spi_desc *spi,
                             uint8_t reg, uint8_t value)
{
    uint8_t readback;
    int ret;

    // Write
    ret = spi_write_reg(spi, reg, value);
    if (ret)
        return ret;

    // Small delay for write to settle
    no_os_udelay(10);

    // Read back
    ret = spi_read_reg(spi, reg, &readback);
    if (ret)
        return ret;

    // Verify
    if (readback != value)
        return -EIO;

    return 0;
}
```

### Pattern 7: Chip ID Verification

```c
int32_t spi_verify_chip_id(struct no_os_spi_desc *spi,
                           uint8_t id_reg, uint8_t expected_id)
{
    uint8_t chip_id;
    int ret;

    ret = spi_read_reg(spi, id_reg, &chip_id);
    if (ret)
        return ret;

    if (chip_id != expected_id) {
        printf("Chip ID mismatch: expected 0x%02X, got 0x%02X\n",
               expected_id, chip_id);
        return -ENODEV;
    }

    return 0;
}

// Usage in driver init
ret = spi_verify_chip_id(spi_desc, CHIP_ID_REG, 0x12);
if (ret)
    return ret;
```

## SPI Initialization Workflow

### Complete Example

```c
#include "no_os_spi.h"
#include "maxim_spi.h"

int main(void)
{
    struct no_os_spi_desc *spi_desc;
    int ret;

    // Step 1: Define platform-specific parameters
    struct max_spi_init_param max_spi_extra = {
        .num_slaves = 1,
        .polarity = 0,
        .vssel = MXC_GPIO_VSSEL_VDDIO,
    };

    // Step 2: Define generic SPI parameters
    struct no_os_spi_init_param spi_init = {
        .device_id = 0,                  // SPI0
        .max_speed_hz = 1000000,         // 1 MHz
        .chip_select = 0,                // CS0
        .mode = NO_OS_SPI_MODE_0,
        .bit_order = NO_OS_SPI_BIT_ORDER_MSB_FIRST,
        .platform_ops = &max_spi_ops,
        .extra = &max_spi_extra,
    };

    // Step 3: Initialize SPI
    ret = no_os_spi_init(&spi_desc, &spi_init);
    if (ret) {
        printf("SPI init failed: %d\n", ret);
        return ret;
    }

    // Step 4: Use SPI
    uint8_t data[3] = {0x01, 0x02, 0x03};
    ret = no_os_spi_write_and_read(spi_desc, data, 3);
    if (ret) {
        printf("SPI transfer failed: %d\n", ret);
        goto cleanup;
    }

    printf("Received: 0x%02X 0x%02X 0x%02X\n",
           data[0], data[1], data[2]);

cleanup:
    // Step 5: Cleanup
    ret = no_os_spi_remove(spi_desc);
    if (ret)
        printf("SPI remove failed: %d\n", ret);

    return ret;
}
```

## Message Transfer Timing

### CS Delay Fields Explained

```c
struct no_os_spi_msg {
    uint8_t *tx_buff;
    uint8_t *rx_buff;
    uint32_t bytes_number;
    uint8_t cs_change;          // 1 = deassert CS after transfer
    uint32_t cs_change_delay;   // Delay (us) before next CS assert
    uint32_t cs_delay_first;    // Delay (ns) after CS assert
    uint32_t cs_delay_last;     // Delay (ns) before CS deassert
};
```

### Timing Diagram

```
CS:     ‾‾‾|___________________|‾‾‾‾‾‾|______________|‾‾‾‾
           ^                   ^      ^              ^
           |                   |      |              |
         assert          deassert   assert      deassert
           |<-cs_delay_first   |      |              |
           |                   |->|<--|              |
           |               cs_change_delay           |
           |                          |<-cs_delay_first
           |                                         |
           |                          |<-cs_delay_last->|

SCLK:      _/‾\_/‾\_/‾\_/‾\_/‾\_      _/‾\_/‾\_/‾\_
```

### Example with Timing

```c
struct no_os_spi_msg msgs[] = {
    {
        .tx_buff = cmd,
        .rx_buff = NULL,
        .bytes_number = 1,
        .cs_change = 1,           // Deassert CS
        .cs_delay_first = 100,    // 100ns after CS assert
        .cs_delay_last = 50,      // 50ns before CS deassert
        .cs_change_delay = 10,    // 10us before next transfer
    },
    {
        .tx_buff = NULL,
        .rx_buff = data,
        .bytes_number = 4,
        .cs_change = 1,
    },
};

ret = no_os_spi_transfer(spi_desc, msgs, 2);
```

## Error Handling

### Proper Error Checking

```c
int ret;

// Check return values
ret = no_os_spi_init(&spi_desc, &spi_init);
if (ret) {
    printf("SPI init failed: %d\n", ret);
    return ret;
}

ret = no_os_spi_write_and_read(spi_desc, data, 10);
if (ret) {
    printf("SPI transfer failed: %d\n", ret);
    goto error_remove;
}

// Success path
no_os_spi_remove(spi_desc);
return 0;

error_remove:
    no_os_spi_remove(spi_desc);
    return ret;
```

### Common Error Codes

| Error Code | Meaning | Typical Cause |
|------------|---------|---------------|
| 0 | Success | Operation completed |
| -EINVAL | Invalid argument | NULL pointer, invalid parameter |
| -ENOMEM | Out of memory | malloc() failed |
| -ENODEV | No device | Device not found, wrong bus |
| -EIO | I/O error | Transfer failed, timeout |
| -EBUSY | Device busy | Bus locked, DMA in progress |
| -ETIMEDOUT | Timeout | Transfer took too long |
