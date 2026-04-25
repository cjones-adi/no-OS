# Platform API Implementations

This document covers platform-specific implementations and porting guide for I2C drivers.

## Platform-Specific Implementations

### Platform Files Structure

```
drivers/platform/myplatform/
├── myplatform_i2c.c       # Implementation
└── myplatform_i2c.h       # Platform extras
```

### Platform-Specific Extras

Platform-specific parameters extend the generic interface with vendor-specific features.

**Example: Maxim platform**

```c
struct max_i2c_init_param {
    mxc_gpio_vssel_t vssel;          // VDDIO level for I2C pins
};
```

**Example: Custom platform**

```c
struct myplatform_i2c_init_param {
    uint32_t i2c_scl_pin;
    uint32_t i2c_sda_pin;
    // ... other platform specifics
};
```

## Porting to New Platforms

### Step 1: Create Platform Files

```
drivers/platform/myplatform/
├── myplatform_i2c.c       # Implementation
└── myplatform_i2c.h       # Platform extras
```

### Step 2: Define Platform Extras (if needed)

In `myplatform_i2c.h`:

```c
struct myplatform_i2c_init_param {
    uint32_t i2c_scl_pin;
    uint32_t i2c_sda_pin;
    // ... other platform specifics
};
```

### Step 3: Implement Platform Operations

In `myplatform_i2c.c`:

```c
int32_t myplatform_i2c_init(struct no_os_i2c_desc **desc,
                            const struct no_os_i2c_init_param *param)
{
    // 1. Allocate descriptor
    *desc = calloc(1, sizeof(**desc));

    // 2. Configure I2C peripheral using vendor HAL
    // Example: HAL_I2C_Init(...);

    // 3. Copy parameters
    (*desc)->device_id = param->device_id;
    (*desc)->max_speed_hz = param->max_speed_hz;
    (*desc)->slave_address = param->slave_address;

    return 0;
}

int32_t myplatform_i2c_write(struct no_os_i2c_desc *desc,
                             uint8_t *data,
                             uint8_t bytes_number,
                             uint8_t stop_bit)
{
    // Call vendor HAL I2C transmit function
    // Example: HAL_I2C_Master_Transmit(...);

    return 0;
}

int32_t myplatform_i2c_read(struct no_os_i2c_desc *desc,
                            uint8_t *data,
                            uint8_t bytes_number,
                            uint8_t stop_bit)
{
    // Call vendor HAL I2C receive function
    // Example: HAL_I2C_Master_Receive(...);

    return 0;
}

int32_t myplatform_i2c_remove(struct no_os_i2c_desc *desc)
{
    // Cleanup
    // Example: HAL_I2C_DeInit(...);

    free(desc);
    return 0;
}
```

### Step 4: Define Platform Ops Structure

```c
const struct no_os_i2c_platform_ops myplatform_i2c_ops = {
    .i2c_ops_init = &myplatform_i2c_init,
    .i2c_ops_write = &myplatform_i2c_write,
    .i2c_ops_read = &myplatform_i2c_read,
    .i2c_ops_remove = &myplatform_i2c_remove,
};
```

### Step 5: Use in Application

```c
#include "myplatform_i2c.h"

struct myplatform_i2c_init_param extra = {
    .i2c_scl_pin = 5,
    .i2c_sda_pin = 6,
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,
    .platform_ops = &myplatform_i2c_ops,
    .extra = &extra,
};

no_os_i2c_init(&i2c_desc, &i2c_init);
```

## Platform Implementation Details

### Init Function Requirements

The platform `i2c_ops_init` function must:

1. Allocate descriptor memory
2. Configure I2C peripheral using vendor HAL
3. Copy initialization parameters
4. Configure GPIO pins for I2C function
5. Enable I2C peripheral clock
6. Set up I2C speed/timing
7. Handle platform-specific extras

### Write Function Requirements

The platform `i2c_ops_write` function must:

1. Set slave address
2. Transmit data bytes
3. Handle stop bit parameter (STOP vs repeated START)
4. Return error codes on failure (NACK, arbitration loss)
5. Implement timeout mechanisms

### Read Function Requirements

The platform `i2c_ops_read` function must:

1. Set slave address with read bit
2. Receive data bytes
3. Handle stop bit parameter
4. Send ACK for all bytes except last (send NACK on last byte)
5. Return error codes on failure

### Remove Function Requirements

The platform `i2c_ops_remove` function must:

1. Disable I2C peripheral
2. Free descriptor memory
3. Release GPIO pins (optional)
4. Disable peripheral clock (optional)

## Common Platform Considerations

### Pin Configuration

Many platforms require explicit pin mux configuration:

```c
// Platform-specific extras
struct platform_i2c_extra {
    uint32_t scl_pin;
    uint32_t sda_pin;
    uint32_t alternate_function;  // AF number for I2C
};
```

### Clock Configuration

Some platforms need explicit clock setup:

```c
// Enable I2C peripheral clock
__HAL_RCC_I2C1_CLK_ENABLE();

// Calculate timing register based on speed
uint32_t timing = calculate_i2c_timing(param->max_speed_hz);
```

### DMA Support (Optional)

Advanced implementations may support DMA:

```c
struct platform_i2c_extra {
    bool use_dma;
    uint32_t tx_dma_channel;
    uint32_t rx_dma_channel;
};
```

### Interrupt Support (Optional)

Some platforms may use interrupts instead of polling:

```c
struct platform_i2c_extra {
    bool use_interrupts;
    void (*transfer_complete_callback)(void);
};
```

## Platform-Specific Error Handling

Map vendor HAL error codes to no-OS standard errors:

```c
int32_t myplatform_i2c_write(...)
{
    HAL_StatusTypeDef status;
    
    status = HAL_I2C_Master_Transmit(...);
    
    switch (status) {
    case HAL_OK:
        return 0;
    case HAL_ERROR:
        return -EIO;
    case HAL_BUSY:
        return -EBUSY;
    case HAL_TIMEOUT:
        return -ETIMEDOUT;
    default:
        return -EFAULT;
    }
}
```

## Testing Platform Implementation

Verify platform implementation with device scan:

```c
// Test: Scan for I2C devices
for (uint8_t addr = 0x08; addr < 0x78; addr++) {
    struct no_os_i2c_desc temp_desc = *i2c;
    temp_desc.slave_address = addr;
    
    uint8_t dummy;
    if (no_os_i2c_read(&temp_desc, &dummy, 0, 1) == 0) {
        printf("Device found at 0x%02X\n", addr);
    }
}
```

## Platform Examples

### Maxim Platform

Files: `drivers/platform/maxim/maxim_i2c.c`, `maxim_i2c.h`

Key features:
- VSSEL voltage level selection
- GPIO configuration handled by platform
- Uses Maxim Peripheral Drivers (PeriphDrivers)

### Mbed Platform

Files: `drivers/platform/mbed/mbed_i2c.cpp`, `mbed_i2c.h`

Key features:
- C++ implementation
- Uses Mbed OS I2C API
- Pin names specified in extras

### STM32 Platform

Files: `drivers/platform/stm32/stm32_i2c.c`, `stm32_i2c.h`

Key features:
- HAL library integration
- Timing register calculation
- Alternate function configuration
