# Creating Emulators for Zephyr Driver Testing

Guide to implementing I2C and SPI emulators for testing Zephyr drivers without hardware.

## Overview

Emulators simulate hardware devices, allowing you to:
- Test drivers without physical hardware
- Run tests in CI/CD pipelines
- Simulate error conditions and edge cases
- Achieve fast, repeatable test execution

## SPI Emulator Pattern

### Complete Implementation

```c
/* ============= emulator_header.h ============= */
#ifndef DRIVER_EMUL_H_
#define DRIVER_EMUL_H_

#include <zephyr/drivers/emul.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/drivers/spi_emul.h>

/* Define register constants (used by driver and tests) */
#define DRIVER_REG_DEVID        0x00
#define DRIVER_REG_STATUS       0x01
#define DRIVER_REG_DATA_X_L     0x08
#define DRIVER_REG_DATA_X_H     0x09
#define DRIVER_REG_SOFT_RESET   0x1F
#define DRIVER_REG_CONTROL      0x2C

/* Command bytes */
#define DRIVER_WRITE_CMD        0x0A
#define DRIVER_READ_CMD         0x0B

/* Device IDs */
#define DRIVER_DEVID_VALUE      0xAD

/* Status bits */
#define DRIVER_STATUS_DATA_RDY  (1 << 0)

/* Emulator data structure */
struct driver_emul_data {
    uint8_t regs[256];  /* 256-byte register map */
};

/* Helper functions */
void driver_emul_set_reg(const struct emul *target, uint8_t reg, uint8_t val);
uint8_t driver_emul_get_reg(const struct emul *target, uint8_t reg);
void driver_emul_reset(const struct emul *target);
void driver_emul_set_data(const struct emul *target, int16_t x, int16_t y, int16_t z);

#endif /* DRIVER_EMUL_H_ */
```

```c
/* ============= emulator_source.c ============= */
#define DT_DRV_COMPAT vendor_driver

#include <zephyr/device.h>
#include <zephyr/drivers/emul.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/drivers/spi_emul.h>
#include <zephyr/logging/log.h>

#include "driver_emul.h"

LOG_MODULE_REGISTER(driver_emul, CONFIG_SENSOR_LOG_LEVEL);

/* Helper function implementations */
void driver_emul_set_reg(const struct emul *target, uint8_t reg, uint8_t val)
{
    struct driver_emul_data *data = target->data;
    data->regs[reg] = val;
}

uint8_t driver_emul_get_reg(const struct emul *target, uint8_t reg)
{
    struct driver_emul_data *data = target->data;
    return data->regs[reg];
}

void driver_emul_reset(const struct emul *target)
{
    struct driver_emul_data *data = target->data;

    memset(data->regs, 0, sizeof(data->regs));

    /* Set default register values */
    data->regs[DRIVER_REG_DEVID] = DRIVER_DEVID_VALUE;
    data->regs[DRIVER_REG_CONTROL] = 0x13;  /* Default config */
}

void driver_emul_set_data(const struct emul *target, int16_t x, int16_t y, int16_t z)
{
    struct driver_emul_data *data = target->data;

    /* Store 16-bit signed values in register pairs */
    data->regs[DRIVER_REG_DATA_X_L] = (uint8_t)(x & 0xFF);
    data->regs[DRIVER_REG_DATA_X_H] = (uint8_t)((x >> 8) & 0xFF);

    /* Set data ready bit */
    data->regs[DRIVER_REG_STATUS] |= DRIVER_STATUS_DATA_RDY;
}

/* SPI I/O handler */
static int driver_emul_io(const struct emul *target, const struct spi_config *config,
                          const struct spi_buf_set *tx_bufs,
                          const struct spi_buf_set *rx_bufs)
{
    struct driver_emul_data *data = target->data;
    const struct spi_buf *tx_buf = tx_bufs->buffers;
    const struct spi_buf *rx_buf = NULL;
    uint8_t *tx_data = tx_buf->buf;
    uint8_t cmd;
    uint8_t reg_addr;
    size_t data_len;

    if (!tx_data || tx_buf->len < 2) {
        return -EINVAL;
    }

    cmd = tx_data[0];
    reg_addr = tx_data[1];

    if (cmd == DRIVER_WRITE_CMD) {
        /* Write operation: [CMD][REG_ADDR][DATA...] */
        if (tx_bufs->count < 2) {
            return -EINVAL;
        }

        tx_buf++;  /* Move to data buffer */
        tx_data = tx_buf->buf;
        data_len = tx_buf->len;

        LOG_DBG("Write: reg=0x%02x, len=%d", reg_addr, data_len);

        for (size_t i = 0; i < data_len && (reg_addr + i) < 256; i++) {
            data->regs[reg_addr + i] = tx_data[i];
            LOG_DBG("  [0x%02x] = 0x%02x", reg_addr + i, tx_data[i]);
        }

        /* Handle soft reset */
        if (reg_addr == DRIVER_REG_SOFT_RESET && tx_data[0] == 0x52) {
            driver_emul_reset(target);
        }

    } else if (cmd == DRIVER_READ_CMD) {
        /* Read operation: [CMD][REG_ADDR] -> [DATA...] */
        if (!rx_bufs || rx_bufs->count < 2) {
            return -EINVAL;
        }

        rx_buf = &rx_bufs->buffers[1];  /* Skip command/address buffer */
        uint8_t *rx_data = rx_buf->buf;
        data_len = rx_buf->len;

        LOG_DBG("Read: reg=0x%02x, len=%d", reg_addr, data_len);

        for (size_t i = 0; i < data_len && (reg_addr + i) < 256; i++) {
            rx_data[i] = data->regs[reg_addr + i];
            LOG_DBG("  [0x%02x] = 0x%02x", reg_addr + i, rx_data[i]);
        }

        /* Clear data ready bit on data read */
        if (reg_addr >= DRIVER_REG_DATA_X_L && reg_addr <= DRIVER_REG_DATA_X_H) {
            data->regs[DRIVER_REG_STATUS] &= ~DRIVER_STATUS_DATA_RDY;
        }
    }

    return 0;
}

/* Initialization */
static int driver_emul_init(const struct emul *target, const struct device *parent)
{
    ARG_UNUSED(parent);

    driver_emul_reset(target);

    LOG_INF("Driver emulator initialized");
    return 0;
}

/* Instance definition macro - CRITICAL: avoids unused variable warnings */
#define DRIVER_EMUL_DEFINE(n)                              \
    static struct driver_emul_data driver_emul_data_##n;   \
    static const struct spi_emul_api driver_emul_api_##n = { \
        .io = driver_emul_io,                              \
    };                                                     \
    EMUL_DT_INST_DEFINE(n, driver_emul_init,              \
                        &driver_emul_data_##n, NULL,       \
                        &driver_emul_api_##n, NULL)

DT_INST_FOREACH_STATUS_OKAY(DRIVER_EMUL_DEFINE)
```

### Key Points for SPI Emulators

**✅ DO**:
- Define register constants in emulator header (visible to tests)
- Use `DT_INST_FOREACH_STATUS_OKAY` macro to avoid unused variable warnings
- Implement proper SPI protocol: command byte, register address, data
- Log all register accesses (helps debugging tests)
- Handle special register behavior (soft reset, data ready clear)
- Support both single and multi-byte reads/writes

**❌ DON'T**:
- Define standalone `static const struct spi_emul_api` outside macros
- Hardcode register values in implementation
- Forget to validate buffer lengths
- Skip ARG_UNUSED() on unused parameters

### SPI Protocol Implementation

```
Write:
  TX: [WRITE_CMD][REG_ADDR][DATA_BYTE_0][DATA_BYTE_1]...
  RX: (ignored)

Read:
  TX: [READ_CMD][REG_ADDR]
  RX: [DUMMY][DUMMY][DATA_BYTE_0][DATA_BYTE_1]...
```

## I2C Emulator Pattern

### Complete Implementation

```c
/* ============= i2c_emulator.c ============= */
#define DT_DRV_COMPAT vendor_i2c_device

#include <zephyr/device.h>
#include <zephyr/drivers/emul.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/i2c_emul.h>

struct i2c_device_emul_data {
    uint8_t regs[256];
    uint8_t current_reg;  /* For sequential reads */
};

static int i2c_device_emul_transfer(const struct emul *target, struct i2c_msg *msgs,
                                    int num_msgs, int addr)
{
    struct i2c_device_emul_data *data = target->data;

    ARG_UNUSED(addr);

    for (int i = 0; i < num_msgs; i++) {
        struct i2c_msg *msg = &msgs[i];

        if (msg->flags & I2C_MSG_READ) {
            /* Read operation */
            for (size_t j = 0; j < msg->len; j++) {
                msg->buf[j] = data->regs[data->current_reg];
                data->current_reg++;  /* Auto-increment */
            }
        } else {
            /* Write operation - first byte is register address */
            data->current_reg = msg->buf[0];

            for (size_t j = 1; j < msg->len; j++) {
                data->regs[data->current_reg] = msg->buf[j];
                data->current_reg++;
            }
        }
    }

    return 0;
}

static int i2c_device_emul_init(const struct emul *target, const struct device *parent)
{
    struct i2c_device_emul_data *data = target->data;

    ARG_UNUSED(parent);

    memset(data->regs, 0, sizeof(data->regs));

    /* Set device ID */
    data->regs[0x00] = 0x42;

    return 0;
}

#define I2C_DEVICE_EMUL_DEFINE(n)                          \
    static struct i2c_device_emul_data i2c_emul_data_##n;  \
    static const struct i2c_emul_api i2c_emul_api_##n = {  \
        .transfer = i2c_device_emul_transfer,              \
    };                                                     \
    EMUL_DT_INST_DEFINE(n, i2c_device_emul_init,          \
                        &i2c_emul_data_##n, NULL,          \
                        &i2c_emul_api_##n, NULL)

DT_INST_FOREACH_STATUS_OKAY(I2C_DEVICE_EMUL_DEFINE)
```

### Key Points for I2C Emulators

**Protocol**:
- Write: [REG_ADDR][DATA_BYTE_0][DATA_BYTE_1]...
- Read: [REG_ADDR] | [READ_DATA...]
- Auto-increment register address for multi-byte transfers

**Critical Details**:
- Implement `.transfer` function (not `.read`/`.write`)
- Handle combined write-read transactions (restart condition)
- Support both 7-bit and 10-bit addressing if needed
- Track current register for sequential reads

## Common Emulator Patterns

### Simulating Hardware Behavior

```c
/* Temperature sensor with conversion time */
struct temp_emul_data {
    uint8_t regs[256];
    uint64_t conversion_start;  /* Timestamp */
    bool conversion_busy;
};

static int temp_emul_io(const struct emul *target, ...)
{
    struct temp_emul_data *data = target->data;

    if (cmd == START_CONVERSION) {
        data->conversion_start = k_uptime_get();
        data->conversion_busy = true;
        data->regs[STATUS_REG] |= BUSY_BIT;
    }

    if (cmd == READ_RESULT) {
        /* Check if conversion time elapsed (e.g., 10ms) */
        if (data->conversion_busy) {
            uint64_t elapsed = k_uptime_get() - data->conversion_start;
            if (elapsed >= 10) {
                data->conversion_busy = false;
                data->regs[STATUS_REG] &= ~BUSY_BIT;
            } else {
                /* Still busy, return old data */
                return 0;
            }
        }
    }
}
```

### Error Injection for Testing

```c
struct driver_emul_data {
    uint8_t regs[256];
    bool inject_error;
    int error_code;
};

/* Test helper function */
void driver_emul_inject_error(const struct emul *target, int error)
{
    struct driver_emul_data *data = target->data;
    data->inject_error = true;
    data->error_code = error;
}

static int driver_emul_io(...)
{
    struct driver_emul_data *data = target->data;

    /* Check for injected errors */
    if (data->inject_error) {
        data->inject_error = false;
        return data->error_code;
    }

    /* Normal operation */
    ...
}
```

### Simulating FIFO Behavior

```c
struct fifo_emul_data {
    uint8_t regs[256];
    uint16_t fifo[512];  /* FIFO buffer */
    uint16_t fifo_count;
    uint16_t fifo_read_ptr;
    uint16_t fifo_write_ptr;
};

void fifo_emul_push_data(const struct emul *target, uint16_t data)
{
    struct fifo_emul_data *emul = target->data;

    if (emul->fifo_count < 512) {
        emul->fifo[emul->fifo_write_ptr] = data;
        emul->fifo_write_ptr = (emul->fifo_write_ptr + 1) % 512;
        emul->fifo_count++;

        /* Update FIFO count registers */
        emul->regs[FIFO_COUNT_L] = emul->fifo_count & 0xFF;
        emul->regs[FIFO_COUNT_H] = (emul->fifo_count >> 8) & 0xFF;
    }
}
```

## Devicetree Integration

### SPI Emulator Device Node

```dts
/ {
    test_spi: spi@33334444 {
        #address-cells = <1>;
        #size-cells = <0>;
        compatible = "zephyr,spi-emul-controller";
        reg = <0x33334444 0x1000>;
        status = "okay";
        clock-frequency = <8000000>;

        my_device: my_device@0 {
            compatible = "vendor,my-device";
            reg = <0>;
            spi-max-frequency = <8000000>;
            status = "okay";
        };
    };

    aliases {
        device0 = &my_device;
    };
};
```

### I2C Emulator Device Node

```dts
/ {
    test_i2c: i2c@11112222 {
        #address-cells = <1>;
        #size-cells = <0>;
        compatible = "zephyr,i2c-emul-controller";
        reg = <0x11112222 0x1000>;
        status = "okay";
        clock-frequency = <400000>;

        my_i2c_device: my_i2c_device@1d {
            compatible = "vendor,my-i2c-device";
            reg = <0x1d>;
            status = "okay";
        };
    };
};
```

## Common Test Patterns Using Emulators

### Testing with Different Input Values

```c
ZTEST_F(driver, test_various_inputs)
{
    const int16_t test_values[] = { 0, 100, -100, 1000, -1000, 2047, -2048 };

    for (int i = 0; i < ARRAY_SIZE(test_values); i++) {
        driver_emul_set_data(fixture->emul, test_values[i], 0, 0);

        ret = sensor_sample_fetch(fixture->dev);
        zassert_ok(ret, "Sample fetch failed for value %d", test_values[i]);

        ret = sensor_channel_get(fixture->dev, SENSOR_CHAN_ACCEL_X, &val);
        zassert_ok(ret, "Channel get failed");

        double actual = sensor_value_to_double(&val);
        /* Verify value is in expected range */
    }
}
```

### Testing Error Conditions

```c
ZTEST_F(driver, test_communication_error)
{
    /* Inject SPI error */
    driver_emul_inject_error(fixture->emul, -EIO);

    ret = sensor_sample_fetch(fixture->dev);
    zassert_equal(ret, -EIO, "Should propagate communication error");
}
```

### Testing Configuration Changes

```c
ZTEST_F(driver, test_config_affects_reading)
{
    struct sensor_value range_2g = { .val1 = 2, .val2 = 0 };
    struct sensor_value range_4g = { .val1 = 4, .val2 = 0 };

    /* Set 2G range and read */
    sensor_attr_set(fixture->dev, SENSOR_CHAN_ACCEL_XYZ,
                    SENSOR_ATTR_FULL_SCALE, &range_2g);
    driver_emul_set_data(fixture->emul, 1000, 0, 0);
    sensor_sample_fetch(fixture->dev);
    sensor_channel_get(fixture->dev, SENSOR_CHAN_ACCEL_X, &val_2g);

    /* Verify control register was updated */
    uint8_t ctrl = driver_emul_get_reg(fixture->emul, DRIVER_REG_CONTROL);
    zassert_equal((ctrl >> 6) & 0x03, 0x00, "2G range bits incorrect");

    /* Set 4G range and read same LSB value */
    sensor_attr_set(fixture->dev, SENSOR_CHAN_ACCEL_XYZ,
                    SENSOR_ATTR_FULL_SCALE, &range_4g);
    driver_emul_set_data(fixture->emul, 1000, 0, 0);
    sensor_sample_fetch(fixture->dev);
    sensor_channel_get(fixture->dev, SENSOR_CHAN_ACCEL_X, &val_4g);

    /* 4G range should give larger m/s^2 value */
    double val_2g_d = sensor_value_to_double(&val_2g);
    double val_4g_d = sensor_value_to_double(&val_4g);
    zassert_true(val_4g_d > val_2g_d * 1.9, "4G should be ~2x 2G");
}
```

## Best Practices

### 1. Register Map Organization
```c
/* Use clear naming and grouping */
#define DEVICE_REG_ID_START     0x00
#define DEVICE_REG_DEVID        0x00
#define DEVICE_REG_PARTID       0x01
#define DEVICE_REG_REVID        0x02

#define DEVICE_REG_DATA_START   0x08
#define DEVICE_REG_DATA_X_L     0x08
#define DEVICE_REG_DATA_X_H     0x09

#define DEVICE_REG_CTRL_START   0x20
#define DEVICE_REG_FILTER_CTL   0x2C
#define DEVICE_REG_POWER_CTL    0x2D
```

### 2. Logging for Debugging
```c
LOG_DBG("Write: reg=0x%02x, len=%d", reg_addr, data_len);
for (size_t i = 0; i < data_len; i++) {
    LOG_DBG("  [0x%02x] = 0x%02x", reg_addr + i, tx_data[i]);
}
```

### 3. Reset Functionality
```c
void driver_emul_reset(const struct emul *target)
{
    struct driver_emul_data *data = target->data;

    /* Clear all registers */
    memset(data->regs, 0, sizeof(data->regs));

    /* Restore power-on defaults */
    data->regs[DEVICE_REG_DEVID] = DEVICE_DEVID_VALUE;
    data->regs[DEVICE_REG_CONTROL] = 0x13;
}
```

### 4. Helper Functions for Tests
```c
/* In emulator header */
void driver_emul_set_data(const struct emul *target, int16_t x, int16_t y, int16_t z);
void driver_emul_set_temperature(const struct emul *target, int16_t temp);
void driver_emul_trigger_interrupt(const struct emul *target);
void driver_emul_inject_error(const struct emul *target, int error);
```

## Debugging Emulators

### Enable Emulator Logging
```conf
# In prj.conf
CONFIG_LOG=y
CONFIG_SENSOR_LOG_LEVEL_DBG=y
```

### Check Devicetree
```bash
# After building, check if emulator is instantiated
grep -r "emulator initialized" build/zephyr/
```

### Verify Register Access
Add logs to see all reads/writes:
```c
LOG_DBG("Read: reg=0x%02x -> 0x%02x", reg, data->regs[reg]);
LOG_DBG("Write: reg=0x%02x <- 0x%02x", reg, value);
```

## Summary

**Key Takeaways**:
- ✅ Use `DT_INST_FOREACH_STATUS_OKAY` macro to avoid unused warnings
- ✅ Define register constants in emulator header
- ✅ Implement proper bus protocol (SPI command bytes, I2C address)
- ✅ Add logging for debugging
- ✅ Provide helper functions for tests
- ✅ Support reset functionality
- ✅ Handle special register behavior (read-clear, write-only, etc.)
- ✅ Use emulators to simulate error conditions
