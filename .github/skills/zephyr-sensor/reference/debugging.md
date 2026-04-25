## Debugging Tips

### 1. Verify Device ID

```c
uint8_t dev_id;
sensor_reg_read(dev, REG_DEVICE_ID, &dev_id);
LOG_INF("Device ID: 0x%02x (expected: 0x%02x)", dev_id, EXPECTED_ID);
```

### 2. Enable Debug Logging

In `prj.conf`:
```conf
CONFIG_LOG=y
CONFIG_SENSOR_LOG_LEVEL_DBG=y
CONFIG_I2C_LOG_LEVEL_DBG=y
```

In driver:
```c
LOG_MODULE_REGISTER(SENSOR_NAME, CONFIG_SENSOR_LOG_LEVEL);

LOG_DBG("sample_fetch called for chan %d", chan);
LOG_DBG("Read register 0x%02x: 0x%02x", reg, val);
```

### 3. Check Bus Communication

```c
if (!device_is_ready(cfg->i2c.bus)) {
    LOG_ERR("I2C bus not ready");
    return -ENODEV;
}
```

### 4. Verify Interrupt Configuration

```c
LOG_DBG("INT GPIO: port=%s pin=%d", cfg->int_gpio.port->name, cfg->int_gpio.pin);
if (!gpio_is_ready_dt(&cfg->int_gpio)) {
    LOG_ERR("INT GPIO not ready");
    return -ENODEV;
}
```

### 5. Dump Registers

```c
static void sensor_dump_regs(const struct device *dev)
{
    uint8_t val;
    for (uint8_t reg = 0; reg < 0x40; reg++) {
        if (sensor_reg_read(dev, reg, &val) == 0) {
            LOG_INF("Reg 0x%02x: 0x%02x", reg, val);
        }
    }
}
```

