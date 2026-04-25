## Debugging Tips

### 1. Enable I2C Logging

```c
#define LOG_LEVEL LOG_LEVEL_DBG
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(i2c_app);

LOG_DBG("I2C write to 0x%02X: %02X %02X", addr, data[0], data[1]);
```

### 2. Check Pull-Up Resistors

I2C requires external pull-up resistors on SDA and SCL:
- **Standard/Fast mode**: 4.7kΩ - 10kΩ
- **Fast+ mode**: 2kΩ - 4.7kΩ
- Verify with oscilloscope: signals should rise to VDD

### 3. Verify Clock Frequency

```c
/* Read back I2C configuration */
uint32_t config;
i2c_get_config(i2c_dev, &config);

uint32_t speed = I2C_SPEED_GET(config);
printk("I2C speed mode: %u\n", speed);
```

### 4. Check Bus State

```c
/* If bus appears stuck, try recovery */
int ret = i2c_recover_bus(i2c_dev);
if (ret < 0) {
    printk("Bus recovery failed\n");
}
```

### 5. Common Errors

**-EIO (I/O error)**:
- Device NACK'd address or data
- Check device address is correct
- Verify device is powered and connected
- Check pull-up resistors

**-ETIMEDOUT (Timeout)**:
- No response from device
- Clock stretching too long
- Bus stuck (SDA or SCL held low)

**-EAGAIN (Try again)**:
- Arbitration lost (multi-master)
- Retry the operation

**-ENOTSUP (Not supported)**:
- Unsupported speed mode
- 10-bit addressing not supported
- Feature not implemented

### 6. Logic Analyzer Debugging

Capture I2C traffic:
- Check START/STOP conditions
- Verify address (7-bit vs 10-bit)
- Check ACK/NACK responses
- Measure clock frequency
- Look for glitches or noise

