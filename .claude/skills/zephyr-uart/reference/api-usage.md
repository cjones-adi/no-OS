## Consumer API Usage

### Polling Mode (Blocking)

```c
#include <zephyr/drivers/uart.h>

const struct device *uart_dev = DEVICE_DT_GET(DT_NODELABEL(uart0));

void uart_polling_example(void)
{
    if (!device_is_ready(uart_dev)) {
        printk("UART device not ready\n");
        return;
    }

    /* Send string */
    const char *msg = "Hello UART!\n";
    for (size_t i = 0; msg[i] != '\0'; i++) {
        uart_poll_out(uart_dev, msg[i]);
    }

    /* Receive character (non-blocking) */
    unsigned char c;
    if (uart_poll_in(uart_dev, &c) == 0) {
        printk("Received: %c\n", c);
    }
}
```

### Interrupt-Driven Mode (FIFO with Callback)

```c
static void uart_irq_handler(const struct device *dev, void *user_data)
{
    uart_irq_update(dev);

    /* Handle RX */
    if (uart_irq_rx_ready(dev)) {
        uint8_t buf[32];
        int len = uart_fifo_read(dev, buf, sizeof(buf));
        if (len > 0) {
            /* Process received data */
            printk("RX: %d bytes\n", len);
        }
    }

    /* Handle TX */
    if (uart_irq_tx_ready(dev)) {
        /* Send more data if available */
        static const char *msg = "Response\n";
        static int pos = 0;

        if (msg[pos] != '\0') {
            int sent = uart_fifo_fill(dev, (const uint8_t *)&msg[pos], 1);
            pos += sent;
        } else {
            /* All sent, disable TX interrupt */
            uart_irq_tx_disable(dev);
            pos = 0;
        }
    }

    /* Handle errors */
    int err = uart_err_check(dev);
    if (err) {
        printk("UART error: 0x%x\n", err);
    }
}

void uart_interrupt_example(void)
{
    uart_irq_callback_user_data_set(uart_dev, uart_irq_handler, NULL);

    /* Enable RX interrupt */
    uart_irq_rx_enable(uart_dev);
}
```

### Async Mode (DMA with Events)

```c
#define RX_BUF_SIZE 128
static uint8_t rx_buf1[RX_BUF_SIZE];
static uint8_t rx_buf2[RX_BUF_SIZE];

static void uart_async_callback(const struct device *dev,
                                 struct uart_event *evt,
                                 void *user_data)
{
    switch (evt->type) {
    case UART_TX_DONE:
        printk("TX complete: %d bytes\n", evt->data.tx.len);
        break;

    case UART_TX_ABORTED:
        printk("TX aborted: %d bytes sent\n", evt->data.tx.len);
        break;

    case UART_RX_RDY:
        printk("RX ready: %d bytes at offset %d\n",
               evt->data.rx.len, evt->data.rx.offset);
        /* Process received data from evt->data.rx.buf */
        break;

    case UART_RX_BUF_REQUEST:
        /* Provide next buffer for continuous reception */
        uart_rx_buf_rsp(dev, rx_buf2, sizeof(rx_buf2));
        break;

    case UART_RX_BUF_RELEASED:
        printk("RX buffer released\n");
        /* Buffer can be reused */
        break;

    case UART_RX_DISABLED:
        printk("RX disabled\n");
        break;

    case UART_RX_STOPPED:
        printk("RX stopped due to error: %d\n",
               evt->data.rx_stop.reason);
        break;
    }
}

void uart_async_example(void)
{
    /* Set async callback */
    uart_callback_set(uart_dev, uart_async_callback, NULL);

    /* Start reception */
    uart_rx_enable(uart_dev, rx_buf1, sizeof(rx_buf1), 1000);

    /* Transmit data */
    const char *msg = "Async TX test\n";
    uart_tx(uart_dev, (const uint8_t *)msg, strlen(msg), SYS_FOREVER_US);
}
```

### Runtime Configuration

```c
void uart_configure_example(void)
{
    struct uart_config cfg = {
        .baudrate = 9600,
        .parity = UART_CFG_PARITY_EVEN,
        .stop_bits = UART_CFG_STOP_BITS_2,
        .data_bits = UART_CFG_DATA_BITS_8,
        .flow_ctrl = UART_CFG_FLOW_CTRL_RTS_CTS,
    };

    int ret = uart_configure(uart_dev, &cfg);
    if (ret < 0) {
        printk("Failed to configure UART: %d\n", ret);
    }
}
```

