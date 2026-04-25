## Common Patterns and Best Practices

### 1. Check Device Ready

Always verify UART is ready before use:

```c
if (!device_is_ready(uart_dev)) {
    LOG_ERR("UART device not ready");
    return -ENODEV;
}
```

### 2. Choose the Right API

- **Polling**: Simple, blocking, low throughput (console, debug)
- **Interrupt-driven**: Medium throughput, FIFO-based, CPU overhead
- **Async**: High throughput, DMA-based, event-driven

### 3. Handle FIFO Properly in Interrupt Mode

```c
/* Always drain RX FIFO completely */
while (uart_irq_rx_ready(dev)) {
    int len = uart_fifo_read(dev, buf, sizeof(buf));
    if (len <= 0) {
        break;
    }
    /* Process data */
}
```

### 4. Buffer Management in Async Mode

```c
/* Use double buffering for continuous reception */
static uint8_t rx_buf[2][256];
static int current_buf = 0;

/* In UART_RX_BUF_REQUEST event */
current_buf = 1 - current_buf;  /* Toggle */
uart_rx_buf_rsp(dev, rx_buf[current_buf], 256);
```

### 5. Error Handling

```c
int err = uart_err_check(dev);
if (err & UART_ERROR_OVERRUN) {
    LOG_WRN("UART RX overrun - data lost");
}
if (err & UART_ERROR_PARITY) {
    LOG_ERR("UART parity error");
}
if (err & UART_ERROR_FRAMING) {
    LOG_ERR("UART framing error");
}
```

### 6. Flow Control for Reliable Communication

```c
/* Enable RTS/CTS for high-speed or unreliable links */
struct uart_config cfg = {
    .baudrate = 921600,
    .parity = UART_CFG_PARITY_NONE,
    .stop_bits = UART_CFG_STOP_BITS_1,
    .data_bits = UART_CFG_DATA_BITS_8,
    .flow_ctrl = UART_CFG_FLOW_CTRL_RTS_CTS,
};
```

