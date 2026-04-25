## Common Patterns and Best Practices

### 1. Check Device Ready

Always verify I2C bus is ready before use:

```c
const struct i2c_dt_spec sensor = I2C_DT_SPEC_GET(DT_NODELABEL(accel));

if (!i2c_is_ready_dt(&sensor)) {
    LOG_ERR("I2C bus not ready");
    return -ENODEV;
}
```

### 2. Retry on NACK

```c
int i2c_write_with_retry(const struct i2c_dt_spec *spec,
                         const uint8_t *data,
                         size_t len,
                         int max_retries)
{
    int ret;

    for (int i = 0; i < max_retries; i++) {
        ret = i2c_write_dt(spec, data, len);
        if (ret == 0) {
            return 0;  /* Success */
        }

        if (ret == -EIO) {
            /* NACK - device not responding, retry */
            k_msleep(10);
            continue;
        }

        /* Other error - don't retry */
        break;
    }

    return ret;
}
```

### 3. Device Scanning

```c
void i2c_scan_bus(const struct device *i2c_dev)
{
    printk("Scanning I2C bus...\n");

    for (uint8_t addr = 0x08; addr < 0x78; addr++) {
        struct i2c_msg msg = {
            .buf = NULL,
            .len = 0,
            .flags = I2C_MSG_WRITE | I2C_MSG_STOP,
        };

        int ret = i2c_transfer(i2c_dev, &msg, 1, addr);
        if (ret == 0) {
            printk("  Device found at 0x%02X\n", addr);
        }
    }
}
```

### 4. 10-Bit Addressing

```c
/* Configure for 10-bit address */
uint32_t cfg = I2C_MODE_CONTROLLER | I2C_SPEED_SET(I2C_SPEED_FAST) | I2C_ADDR_10_BITS;
i2c_configure(i2c_dev, cfg);

/* Use 10-bit address */
uint16_t addr_10bit = 0x0123;
uint8_t data[] = {0x00, 0xFF};
i2c_write(i2c_dev, data, sizeof(data), addr_10bit);
```

### 5. Clock Stretching Support

Some I2C devices pull SCL low to pause master:

```c
/* Most hardware supports clock stretching automatically */
/* Ensure sufficient timeout in driver implementation */
```

### 6. Multi-Master Support

Handle arbitration loss gracefully:

```c
int i2c_write_multi_master(const struct i2c_dt_spec *spec,
                           const uint8_t *data,
                           size_t len)
{
    int ret = i2c_write_dt(spec, data, len);

    if (ret == -EAGAIN) {
        /* Arbitration lost - retry */
        k_msleep(1);
        ret = i2c_write_dt(spec, data, len);
    }

    return ret;
}
```

