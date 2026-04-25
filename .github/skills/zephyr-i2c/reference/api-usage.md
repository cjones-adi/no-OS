## Consumer API Usage

### Basic I2C Write

```c
#include <zephyr/drivers/i2c.h>

const struct device *i2c_dev = DEVICE_DT_GET(DT_NODELABEL(i2c0));
uint16_t addr = 0x48;

uint8_t data[] = {0x01, 0xFF};  /* Register address, value */

/* Write 2 bytes */
int ret = i2c_write(i2c_dev, data, sizeof(data), addr);
if (ret < 0) {
    printk("I2C write failed: %d\n", ret);
}
```

### Basic I2C Read

```c
uint8_t reg = 0x00;
uint8_t value;

/* Write register address, then read 1 byte */
int ret = i2c_write_read(i2c_dev, addr, &reg, 1, &value, 1);
if (ret < 0) {
    printk("I2C read failed: %d\n", ret);
} else {
    printk("Register 0x%02X = 0x%02X\n", reg, value);
}
```

### Using i2c_dt_spec

```c
static const struct i2c_dt_spec sensor = I2C_DT_SPEC_GET(DT_NODELABEL(accel));

int sensor_init(void)
{
    if (!i2c_is_ready_dt(&sensor)) {
        printk("I2C device not ready\n");
        return -ENODEV;
    }

    /* Write to sensor using DT spec */
    uint8_t config[] = {0x20, 0x27};
    return i2c_write_dt(&sensor, config, sizeof(config));
}
```

### Register Read/Write Helpers

```c
/* Read single register */
uint8_t i2c_reg_read(const struct i2c_dt_spec *spec, uint8_t reg)
{
    uint8_t value;
    i2c_write_read_dt(spec, &reg, 1, &value, 1);
    return value;
}

/* Write single register */
int i2c_reg_write(const struct i2c_dt_spec *spec, uint8_t reg, uint8_t value)
{
    uint8_t data[] = {reg, value};
    return i2c_write_dt(spec, data, sizeof(data));
}

/* Update register bits */
int i2c_reg_update(const struct i2c_dt_spec *spec,
                   uint8_t reg,
                   uint8_t mask,
                   uint8_t value)
{
    uint8_t old_value, new_value;

    /* Read current value */
    i2c_write_read_dt(spec, &reg, 1, &old_value, 1);

    /* Modify */
    new_value = (old_value & ~mask) | (value & mask);

    /* Write back */
    uint8_t data[] = {reg, new_value};
    return i2c_write_dt(spec, data, sizeof(data));
}
```

### Burst Read/Write

```c
/* Burst read multiple bytes */
int sensor_read_data(const struct i2c_dt_spec *spec, uint8_t *buf, size_t len)
{
    uint8_t start_reg = 0x28;  /* Auto-increment register */
    return i2c_write_read_dt(spec, &start_reg, 1, buf, len);
}

/* Burst write */
int eeprom_write_page(const struct i2c_dt_spec *spec,
                      uint16_t addr,
                      const uint8_t *data,
                      size_t len)
{
    uint8_t buf[66];  /* 2 byte address + 64 byte page */

    buf[0] = (addr >> 8) & 0xFF;
    buf[1] = addr & 0xFF;
    memcpy(&buf[2], data, len);

    return i2c_write_dt(spec, buf, len + 2);
}
```

### Advanced: Manual Message Construction

```c
int read_sensor_with_restart(const struct i2c_dt_spec *spec)
{
    uint8_t reg = 0x00;
    uint8_t data[6];

    struct i2c_msg msgs[2] = {
        {
            .buf = &reg,
            .len = 1,
            .flags = I2C_MSG_WRITE | I2C_MSG_RESTART,
        },
        {
            .buf = data,
            .len = sizeof(data),
            .flags = I2C_MSG_READ | I2C_MSG_STOP,
        },
    };

    return i2c_transfer(spec->bus, msgs, 2, spec->addr);
}
```

