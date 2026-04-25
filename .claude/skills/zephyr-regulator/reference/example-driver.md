## Example: Simple Buck Converter Driver

```c
#define DT_DRV_COMPAT vendor_simple_buck

#include <zephyr/drivers/regulator.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/sys/linear_range.h>

#define REG_ENABLE  0x00
#define REG_VOUT    0x01
#define EN_MASK     BIT(0)
#define VOUT_MASK   GENMASK(5, 0)

static const struct linear_range vout_range =
    LINEAR_RANGE_INIT(800000, 50000, 0, 0x1F);  // 800mV-2.35V, 50mV steps

struct regulator_simple_buck_config {
    struct regulator_common_config common;
    struct i2c_dt_spec bus;
};

struct regulator_simple_buck_data {
    struct regulator_common_data data;
};

static int simple_buck_enable(const struct device *dev)
{
    const struct regulator_simple_buck_config *cfg = dev->config;
    return i2c_reg_update_byte_dt(&cfg->bus, REG_ENABLE, EN_MASK, EN_MASK);
}

static int simple_buck_disable(const struct device *dev)
{
    const struct regulator_simple_buck_config *cfg = dev->config;
    return i2c_reg_update_byte_dt(&cfg->bus, REG_ENABLE, EN_MASK, 0);
}

static unsigned int simple_buck_count_voltages(const struct device *dev)
{
    return linear_range_values_count(&vout_range);
}

static int simple_buck_list_voltage(const struct device *dev,
                                    unsigned int idx, int32_t *volt_uv)
{
    return linear_range_get_value(&vout_range, idx, volt_uv);
}

static int simple_buck_set_voltage(const struct device *dev,
                                   int32_t min_uv, int32_t max_uv)
{
    const struct regulator_simple_buck_config *cfg = dev->config;
    uint16_t idx;
    int ret;

    ret = linear_range_get_win_index(&vout_range, min_uv, max_uv, &idx);
    if (ret < 0) {
        return ret;
    }

    return i2c_reg_update_byte_dt(&cfg->bus, REG_VOUT, VOUT_MASK, idx);
}

static int simple_buck_get_voltage(const struct device *dev, int32_t *volt_uv)
{
    const struct regulator_simple_buck_config *cfg = dev->config;
    uint8_t idx;
    int ret;

    ret = i2c_reg_read_byte_dt(&cfg->bus, REG_VOUT, &idx);
    if (ret < 0) {
        return ret;
    }

    return linear_range_get_value(&vout_range, idx & VOUT_MASK, volt_uv);
}

static DEVICE_API(regulator, simple_buck_api) = {
    .enable = simple_buck_enable,
    .disable = simple_buck_disable,
    .count_voltages = simple_buck_count_voltages,
    .list_voltage = simple_buck_list_voltage,
    .set_voltage = simple_buck_set_voltage,
    .get_voltage = simple_buck_get_voltage,
};

static int simple_buck_init(const struct device *dev)
{
    const struct regulator_simple_buck_config *cfg = dev->config;
    bool is_enabled = false;

    if (!i2c_is_ready_dt(&cfg->bus)) {
        return -ENODEV;
    }

    regulator_common_data_init(dev);

    uint8_t reg;
    if (i2c_reg_read_byte_dt(&cfg->bus, REG_ENABLE, &reg) == 0) {
        is_enabled = (reg & EN_MASK) != 0;
    }

    return regulator_common_init(dev, is_enabled);
}

#define SIMPLE_BUCK_DEFINE(inst)                                        \
    static struct regulator_simple_buck_data data_##inst;               \
                                                                        \
    static const struct regulator_simple_buck_config config_##inst = {  \
        .common = REGULATOR_DT_INST_COMMON_CONFIG_INIT(inst),           \
        .bus = I2C_DT_SPEC_INST_GET(inst),                              \
    };                                                                  \
                                                                        \
    DEVICE_DT_INST_DEFINE(inst, simple_buck_init, NULL,                 \
                         &data_##inst, &config_##inst,                  \
                         POST_KERNEL, CONFIG_REGULATOR_INIT_PRIORITY,   \
                         &simple_buck_api);

DT_INST_FOREACH_STATUS_OKAY(SIMPLE_BUCK_DEFINE)
```

