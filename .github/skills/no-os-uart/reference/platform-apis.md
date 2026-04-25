# Platform API Implementation Details

Complete reference for implementing UART platform drivers for new platforms.

## Porting to New Platforms

### Step 1: Create Platform Files

```
drivers/platform/myplatform/
├── myplatform_uart.c      # Implementation
└── myplatform_uart.h      # Platform extras
```

### Step 2: Define Platform Extras (if needed)

In `myplatform_uart.h`:

```c
#ifndef _MYPLATFORM_UART_H_
#define _MYPLATFORM_UART_H_

struct myplatform_uart_init_param {
    uint32_t flow_control;    // Hardware flow control enable
    uint32_t dma_enabled;     // DMA mode
    // ... other platform specifics
};

#endif
```

### Step 3: Implement Platform Operations

In `myplatform_uart.c`:

```c
#include "no_os_uart.h"
#include "myplatform_uart.h"

int32_t myplatform_uart_init(struct no_os_uart_desc **desc,
                              struct no_os_uart_init_param *param)
{
    // 1. Allocate descriptor
    *desc = calloc(1, sizeof(**desc));
    if (!*desc)
        return -ENOMEM;

    // 2. Configure UART using vendor HAL
    // - Enable UART peripheral clock
    // - Set baud rate divider
    // - Configure data bits, parity, stop bits
    // Example: HAL_UART_Init(UART0, param->baud_rate);

    // 3. Configure interrupt if async RX enabled
    if (param->asynchronous_rx) {
        // Create RX FIFO buffer
        (*desc)->rx_fifo = lf256fifo_new();
        // Register RX interrupt handler
        // Example: HAL_UART_EnableRxInterrupt(UART0);
    }

    // 4. Copy parameters
    (*desc)->device_id = param->device_id;
    (*desc)->irq_id = param->irq_id;
    (*desc)->baud_rate = param->baud_rate;

    return 0;
}

int32_t myplatform_uart_remove(struct no_os_uart_desc *desc)
{
    if (!desc)
        return -EINVAL;

    // Disable UART
    // Example: HAL_UART_Disable(UART0);

    // Free RX FIFO if allocated
    if (desc->rx_fifo)
        lf256fifo_free(desc->rx_fifo);

    free(desc);
    return 0;
}

int32_t myplatform_uart_read(struct no_os_uart_desc *desc,
                              uint8_t *data,
                              uint32_t bytes_number)
{
    uint32_t idx = 0;

    if (!desc || !data || bytes_number == 0)
        return -EINVAL;

    // Blocking read: poll until all bytes received
    while (idx < bytes_number) {
        if (HAL_UART_HasData(desc->device_id)) {
            data[idx++] = HAL_UART_ReadByte(desc->device_id);
        }
        // Optionally add timeout here
    }

    return idx;
}

int32_t myplatform_uart_write(struct no_os_uart_desc *desc,
                               const uint8_t *data,
                               uint32_t bytes_number)
{
    uint32_t idx = 0;

    if (!desc || !data || bytes_number == 0)
        return -EINVAL;

    // Blocking write: wait for each byte to be transmitted
    while (idx < bytes_number) {
        HAL_UART_WriteByte(desc->device_id, data[idx++]);
        while (!HAL_UART_IsTxComplete(desc->device_id))
            ;  // Wait for byte sent
    }

    return idx;
}

int32_t myplatform_uart_read_nonblocking(struct no_os_uart_desc *desc,
                                          uint8_t *data,
                                          uint32_t bytes_number)
{
    uint32_t idx = 0;

    if (!desc || !data)
        return -EINVAL;

    // Read from RX FIFO (populated by interrupt handler)
    if (desc->rx_fifo) {
        while (idx < bytes_number &&
               lf256fifo_pop(desc->rx_fifo, &data[idx]) == 0)
            idx++;
    }

    return idx;
}

int32_t myplatform_uart_write_nonblocking(struct no_os_uart_desc *desc,
                                           const uint8_t *data,
                                           uint32_t bytes_number)
{
    uint32_t idx = 0;

    if (!desc || !data)
        return -EINVAL;

    // Queue bytes for TX (interrupt-driven transmission)
    while (idx < bytes_number) {
        if (tx_fifo_push(...) < 0)
            break;  // TX FIFO full
        idx++;
    }

    // Enable TX interrupt if not already enabled
    if (idx > 0)
        HAL_UART_EnableTxInterrupt(desc->device_id);

    return idx;
}

uint32_t myplatform_uart_get_errors(struct no_os_uart_desc *desc)
{
    if (!desc)
        return -EINVAL;

    // Return current error count
    // Example: return HAL_UART_GetErrors(desc->device_id);
}

// RX interrupt handler (if async RX enabled)
void UART0_RxIsr(void)
{
    uint8_t byte = HAL_UART_ReadByte(UART0);
    if (uart_desc->rx_fifo)
        lf256fifo_push(uart_desc->rx_fifo, byte);
}
```

### Step 4: Define Platform Ops

```c
const struct no_os_uart_platform_ops myplatform_uart_ops = {
    .init = &myplatform_uart_init,
    .read = &myplatform_uart_read,
    .write = &myplatform_uart_write,
    .read_nonblocking = &myplatform_uart_read_nonblocking,
    .write_nonblocking = &myplatform_uart_write_nonblocking,
    .remove = &myplatform_uart_remove,
    .get_errors = &myplatform_uart_get_errors,
};
```

## Platform-Specific Implementation Notes

### Blocking vs Non-Blocking

**Blocking I/O**:
- Must wait until ALL bytes transmitted/received
- May use polling or hardware status flags
- Should implement timeout to prevent infinite loops
- Common for simple applications

**Non-blocking I/O**:
- Returns immediately with number of bytes processed
- Requires interrupt-driven background processing
- Needs software FIFO for buffering
- Essential for CLI and streaming applications

### Interrupt-Driven Reception

**Requirements**:
1. Create software FIFO buffer (lf256fifo)
2. Register interrupt handler for UART RX
3. Store incoming bytes in FIFO from ISR
4. Implement read_nonblocking() to drain FIFO

**Example interrupt handler pattern**:
```c
void UART_RX_IRQHandler(void)
{
    while (HAL_UART_DataAvailable()) {
        uint8_t byte = HAL_UART_ReadByte();
        if (uart_desc && uart_desc->rx_fifo) {
            lf256fifo_push(uart_desc->rx_fifo, byte);
        }
    }
    HAL_UART_ClearRxInterrupt();
}
```

### Baud Rate Configuration

Most platforms use clock divisor formula:
```
divisor = (peripheral_clock / (oversampling * baud_rate)) - 1
```

**Common oversampling values**: 8x or 16x

**Example**:
```c
// For 115200 baud with 48MHz clock and 16x oversampling
uint32_t divisor = (48000000 / (16 * 115200)) - 1;
// divisor = 25
```

**Edge cases**:
- Very high baud rates may exceed peripheral limits
- Verify divisor results in acceptable error (<2%)
- Some platforms have fixed baud rate tables

### Platform-Specific Parameters

Many platforms support additional features in `.extra`:

**Maxim platform example**:
```c
struct max_uart_init_param {
    bool flow_control;   // RTS/CTS hardware flow control
    bool dma_enabled;    // Use DMA for TX/RX
};
```

**STM32 platform example**:
```c
struct stm32_uart_init_param {
    uint32_t mode;       // TX_ONLY, RX_ONLY, TX_RX
    bool hw_flow_ctl;    // Hardware flow control
};
```

**Mbed platform example**:
```c
struct mbed_uart_init_param {
    PinName tx_pin;      // Physical TX pin
    PinName rx_pin;      // Physical RX pin
    bool flow_control;   // RTS/CTS pins
};
```

### Error Handling

Platforms should track and report:
- **Overrun errors** – Data lost because RX FIFO full
- **Framing errors** – Invalid stop bit detected
- **Parity errors** – Parity check failed
- **Break errors** – Line held low too long

**Implementation**:
```c
static struct {
    uint32_t overrun_count;
    uint32_t framing_count;
    uint32_t parity_count;
} uart_errors[MAX_UART_COUNT];

uint32_t myplatform_uart_get_errors(struct no_os_uart_desc *desc)
{
    uint32_t id = desc->device_id;
    return uart_errors[id].overrun_count +
           uart_errors[id].framing_count +
           uart_errors[id].parity_count;
}
```

### Multi-Instance Support

Platform implementations must support multiple UART instances:

```c
static struct no_os_uart_desc *uart_instances[MAX_UART_COUNT];

int32_t myplatform_uart_init(struct no_os_uart_desc **desc,
                              struct no_os_uart_init_param *param)
{
    uint8_t id = param->device_id;
    
    if (id >= MAX_UART_COUNT)
        return -EINVAL;
    
    if (uart_instances[id])
        return -EBUSY;  // Already initialized
    
    // ... initialization ...
    
    uart_instances[id] = *desc;
    return 0;
}
```

## Standard I/O Redirection

Platform implementations may need to provide hooks for stdio:

```c
// Example: Redirect putchar/getchar to UART
static struct no_os_uart_desc *stdio_uart = NULL;

void no_os_uart_stdio(struct no_os_uart_desc *desc)
{
    stdio_uart = desc;
}

// Override weak putchar implementation
int _write(int fd, char *ptr, int len)
{
    if (stdio_uart && fd == 1) {  // stdout
        no_os_uart_write(stdio_uart, (uint8_t *)ptr, len);
        return len;
    }
    return 0;
}

// Override weak getchar implementation
int _read(int fd, char *ptr, int len)
{
    if (stdio_uart && fd == 0) {  // stdin
        return no_os_uart_read(stdio_uart, (uint8_t *)ptr, len);
    }
    return 0;
}
```

## Testing Platform Implementations

Recommended testing approach:
1. Test basic init/remove with all valid device IDs
2. Test write with varying data sizes (1 byte, 64 bytes, 1KB)
3. Test read blocking vs non-blocking behavior
4. Test async RX with interrupt-driven reception
5. Verify error handling (invalid parameters, hardware failures)
6. Test multiple simultaneous UART instances
7. Verify baud rate accuracy with oscilloscope
8. Test standard I/O redirection (printf)

## Summary

Platform implementations must provide:
- **init()** – Allocate descriptor, configure hardware, setup interrupts
- **remove()** – Free resources, disable peripheral
- **read()** – Blocking receive
- **write()** – Blocking transmit
- **read_nonblocking()** – Non-blocking receive from FIFO
- **write_nonblocking()** – Non-blocking transmit to FIFO
- **get_errors()** – Return error count

Key considerations:
- Support multiple UART instances
- Implement interrupt-driven async RX with software FIFO
- Calculate correct baud rate divisors
- Handle platform-specific extras properly
- Provide stdio redirection hooks
- Robust error handling and validation
