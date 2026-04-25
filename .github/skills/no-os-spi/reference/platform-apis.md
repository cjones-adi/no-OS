# Platform API Implementations

Detailed information about platform-specific SPI implementations and hardware abstraction layers.

## Platform-Specific Extras

Different platforms require different initialization parameters beyond the generic interface.

### Maxim Platform

**maxim_spi.h** - Platform-specific parameters

```c
struct max_spi_init_param {
    uint8_t num_slaves;              // Number of slaves
    uint8_t polarity;                // CS polarity
    mxc_gpio_vssel_t vssel;          // VDDIO level
    struct no_os_dma_init_param *dma_param;  // DMA (optional)
    uint8_t dma_tx_priority;         // DMA TX priority
    uint8_t dma_rx_priority;         // DMA RX priority
};
```

**Example initialization:**

```c
struct max_spi_init_param max_spi_extra = {
    .num_slaves = 1,
    .polarity = 0,
    .vssel = MXC_GPIO_VSSEL_VDDIO,
};

struct no_os_spi_init_param spi_init = {
    .device_id = 0,                  // SPI0
    .max_speed_hz = 1000000,         // 1 MHz
    .chip_select = 0,                // CS0
    .mode = NO_OS_SPI_MODE_0,
    .bit_order = NO_OS_SPI_BIT_ORDER_MSB_FIRST,
    .platform_ops = &max_spi_ops,
    .extra = &max_spi_extra,
};

ret = no_os_spi_init(&spi_desc, &spi_init);
```

### Mbed Platform

**mbed_spi.h** - Platform-specific parameters

```c
struct mbed_spi_init_param {
    PinName spi_miso_pin;            // MISO pin
    PinName spi_mosi_pin;            // MOSI pin
    PinName spi_clk_pin;             // CLK pin
    bool use_sw_csb;                 // Software CS control
};
```

**Example initialization:**

```c
struct mbed_spi_init_param mbed_spi_extra = {
    .spi_miso_pin = SPI_MISO,
    .spi_mosi_pin = SPI_MOSI,
    .spi_clk_pin = SPI_SCK,
    .use_sw_csb = false,
};

struct no_os_spi_init_param spi_init = {
    .device_id = 0,
    .max_speed_hz = 1000000,
    .chip_select = 0,
    .mode = NO_OS_SPI_MODE_0,
    .platform_ops = &mbed_spi_ops,
    .extra = &mbed_spi_extra,
};

ret = no_os_spi_init(&spi_desc, &spi_init);
```

## Porting to New Platforms

Step-by-step guide for implementing SPI support on a new platform.

### Step 1: Create Platform Files

```
drivers/platform/myplatform/
├── myplatform_spi.c       # Implementation
└── myplatform_spi.h       # Platform-specific extras
```

### Step 2: Define Platform Init Parameters

In `myplatform_spi.h`:

```c
#ifndef MYPLATFORM_SPI_H
#define MYPLATFORM_SPI_H

#include "no_os_spi.h"

struct myplatform_spi_init_param {
    // Platform-specific parameters
    uint32_t spi_clk_pin;
    uint32_t spi_mosi_pin;
    uint32_t spi_miso_pin;
    uint32_t cs_pin;
    // ... other platform specifics
};

extern const struct no_os_spi_platform_ops myplatform_spi_ops;

#endif // MYPLATFORM_SPI_H
```

### Step 3: Implement Platform Operations

In `myplatform_spi.c`:

#### Initialize Function

```c
int32_t myplatform_spi_init(struct no_os_spi_desc **desc,
                            const struct no_os_spi_init_param *param)
{
    struct myplatform_spi_init_param *extra = param->extra;
    struct myplatform_spi_desc *myplatform_desc;
    int ret;

    if (!desc || !param)
        return -EINVAL;

    // 1. Allocate descriptor
    *desc = calloc(1, sizeof(**desc));
    if (!(*desc))
        return -ENOMEM;

    // Allocate platform-specific descriptor
    myplatform_desc = calloc(1, sizeof(*myplatform_desc));
    if (!myplatform_desc) {
        free(*desc);
        return -ENOMEM;
    }

    // 2. Configure GPIO pins (vendor HAL)
    // Example: HAL_GPIO_Init(...);

    // 3. Configure SPI peripheral (vendor HAL)
    // Example:
    // SPI_HandleTypeDef *hspi = &myplatform_desc->hspi;
    // hspi->Instance = SPI1;
    // hspi->Init.Mode = SPI_MODE_MASTER;
    // hspi->Init.BaudRatePrescaler = calculate_prescaler(param->max_speed_hz);
    // hspi->Init.CLKPolarity = (param->mode & NO_OS_SPI_CPOL) ? 
    //                          SPI_POLARITY_HIGH : SPI_POLARITY_LOW;
    // hspi->Init.CLKPhase = (param->mode & NO_OS_SPI_CPHA) ? 
    //                       SPI_PHASE_2EDGE : SPI_PHASE_1EDGE;
    // ret = HAL_SPI_Init(hspi);
    // if (ret != HAL_OK) {
    //     free(myplatform_desc);
    //     free(*desc);
    //     return -EIO;
    // }

    // 4. Store configuration in descriptor
    (*desc)->device_id = param->device_id;
    (*desc)->max_speed_hz = param->max_speed_hz;
    (*desc)->chip_select = param->chip_select;
    (*desc)->mode = param->mode;
    (*desc)->bit_order = param->bit_order;
    (*desc)->extra = myplatform_desc;

    return 0;
}
```

#### Write and Read Function

```c
int32_t myplatform_spi_write_and_read(struct no_os_spi_desc *desc,
                                      uint8_t *data,
                                      uint16_t bytes_number)
{
    struct myplatform_spi_desc *myplatform_desc;
    int ret;

    if (!desc || !data)
        return -EINVAL;

    myplatform_desc = desc->extra;

    // Assert chip select (if using software CS)
    // Example: HAL_GPIO_WritePin(CS_PORT, CS_PIN, GPIO_PIN_RESET);

    // Perform SPI transfer using vendor HAL
    // Example:
    // ret = HAL_SPI_TransmitReceive(&myplatform_desc->hspi,
    //                               data, data, bytes_number,
    //                               TIMEOUT_MS);
    // if (ret != HAL_OK)
    //     return -EIO;

    // Deassert chip select
    // Example: HAL_GPIO_WritePin(CS_PORT, CS_PIN, GPIO_PIN_SET);

    return 0;
}
```

#### Transfer Function (Message-based)

```c
int32_t myplatform_spi_transfer(struct no_os_spi_desc *desc,
                                struct no_os_spi_msg *msgs,
                                uint32_t len)
{
    struct myplatform_spi_desc *myplatform_desc;
    uint32_t i;
    int ret;

    if (!desc || !msgs)
        return -EINVAL;

    myplatform_desc = desc->extra;

    for (i = 0; i < len; i++) {
        struct no_os_spi_msg *msg = &msgs[i];

        // Apply CS delay before first transfer
        if (i == 0 && msg->cs_delay_first)
            udelay(msg->cs_delay_first / 1000);

        // Assert CS
        // Example: HAL_GPIO_WritePin(CS_PORT, CS_PIN, GPIO_PIN_RESET);

        // Perform transfer based on message type
        if (msg->tx_buff && msg->rx_buff) {
            // Full-duplex: transmit and receive
            // ret = HAL_SPI_TransmitReceive(..., msg->tx_buff, msg->rx_buff,
            //                                msg->bytes_number, TIMEOUT_MS);
        } else if (msg->tx_buff) {
            // Transmit only
            // ret = HAL_SPI_Transmit(..., msg->tx_buff, msg->bytes_number,
            //                        TIMEOUT_MS);
        } else if (msg->rx_buff) {
            // Receive only
            // ret = HAL_SPI_Receive(..., msg->rx_buff, msg->bytes_number,
            //                        TIMEOUT_MS);
        }

        // Apply CS delay before deasserting
        if (msg->cs_delay_last)
            udelay(msg->cs_delay_last / 1000);

        // Deassert CS if requested
        if (msg->cs_change) {
            // Example: HAL_GPIO_WritePin(CS_PORT, CS_PIN, GPIO_PIN_SET);
            
            // Apply delay after CS deassert
            if (msg->cs_change_delay)
                udelay(msg->cs_change_delay);
        }
    }

    // Ensure CS is deasserted at end
    // Example: HAL_GPIO_WritePin(CS_PORT, CS_PIN, GPIO_PIN_SET);

    return 0;
}
```

#### Remove Function

```c
int32_t myplatform_spi_remove(struct no_os_spi_desc *desc)
{
    struct myplatform_spi_desc *myplatform_desc;

    if (!desc)
        return -EINVAL;

    myplatform_desc = desc->extra;

    // Cleanup platform resources
    // Example: HAL_SPI_DeInit(&myplatform_desc->hspi);

    free(myplatform_desc);
    free(desc);

    return 0;
}
```

### Step 4: Define Platform Ops Structure

```c
const struct no_os_spi_platform_ops myplatform_spi_ops = {
    .init = &myplatform_spi_init,
    .write_and_read = &myplatform_spi_write_and_read,
    .transfer = &myplatform_spi_transfer,
    .remove = &myplatform_spi_remove,
    // Optional: implement DMA functions
    // .transfer_dma = &myplatform_spi_transfer_dma,
    // .transfer_dma_async = &myplatform_spi_transfer_dma_async,
};
```

### Step 5: Use in Application

```c
#include "myplatform_spi.h"

struct myplatform_spi_init_param extra = {
    .spi_clk_pin = 5,
    .spi_mosi_pin = 6,
    .spi_miso_pin = 7,
    .cs_pin = 8,
};

struct no_os_spi_init_param spi_init = {
    .device_id = 0,
    .max_speed_hz = 1000000,
    .mode = NO_OS_SPI_MODE_0,
    .platform_ops = &myplatform_spi_ops,
    .extra = &extra,
};

ret = no_os_spi_init(&spi_desc, &spi_init);
```

## Platform-Specific Delays

Some platforms have signal path delays that affect timing requirements.

### Delay Structure

```c
struct no_os_platform_spi_delays {
    uint32_t cs_delay_first;  // ns from CS assert to first SCLK
    uint32_t cs_delay_last;   // ns from last SCLK to CS deassert
};
```

### Delay Calculation

**Total delay** = `msg->cs_delay_first` + `platform_delays.cs_delay_first`

### Maxim Example

```c
// Platform has 50ns inherent delay
spi_init.platform_delays.cs_delay_first = 50;
spi_init.platform_delays.cs_delay_last = 50;

// Message requests additional 1us delay
msg.cs_delay_first = 1000;  // ns
// Total: 1050ns delay after CS assert
```

### Why Platform Delays?

- **Signal propagation delays** - GPIO mux, buffers, PCB traces
- **Hardware limitations** - Some peripherals have minimum setup/hold times
- **Timing compensation** - Ensure device timing requirements are met
- **Cross-platform consistency** - Same application code works on different platforms

### Implementation Tips

1. **Measure actual delays** - Use oscilloscope/logic analyzer
2. **Document in platform header** - Make delays visible to users
3. **Add to message delays** - Platform delays are additive with message delays
4. **Consider worst-case** - Account for process, voltage, temperature variations
