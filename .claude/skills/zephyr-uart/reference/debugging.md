## Debugging Tips

### 1. Enable UART Logging

```c
#define LOG_LEVEL LOG_LEVEL_DBG
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(uart_app);

LOG_HEXDUMP_DBG(data, len, "UART RX:");
```

### 2. Check Baud Rate

Verify both ends use same baud rate:

```c
struct uart_config cfg;
uart_config_get(uart_dev, &cfg);
printk("Baud rate: %u\n", cfg.baudrate);
```

### 3. Verify Signal Levels with Oscilloscope

- **TX idle**: Should be high (logic 1)
- **RX idle**: Should be high (logic 1)
- **Frame timing**: Measure bit period (1/baudrate)
- **Correct polarity**: Start bit pulls line low

### 4. Common Errors

**-ENOSYS (Not implemented)**:
- API function not supported by driver
- Feature not enabled in Kconfig

**-EBUSY (Busy)**:
- Transfer already in progress (async mode)
- RX already enabled

**-EINVAL (Invalid argument)**:
- Invalid baud rate
- Unsupported configuration

### 5. Loopback Testing

```c
/* Enable internal loopback for testing */
sys_set_bits(base + UART_MCR, UART_MCR_LOOP);

/* TX and RX should match */
uart_poll_out(uart_dev, 'A');
unsigned char c;
uart_poll_in(uart_dev, &c);
if (c == 'A') {
    printk("Loopback test PASSED\n");
}
```

### 6. Check for Overruns

```c
/* Monitor for data loss */
int err = uart_err_check(uart_dev);
if (err & UART_ERROR_OVERRUN) {
    LOG_ERR("RX overrun - increase FIFO size or processing speed");
}
```

