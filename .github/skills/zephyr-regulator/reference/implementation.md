## Driver Implementation Pattern

### Step 1: Define Register Map and Bit Masks

```c
#define DT_DRV_COMPAT vendor_chipname_regulator

// Register addresses
#define CHIP_BUCK1_CTRL    0x10
#define CHIP_BUCK1_VSEL    0x11
#define CHIP_LDO1_CTRL     0x20
#define CHIP_LDO1_VSEL     0x21

// Bit masks
#define CHIP_BUCK_EN_MASK      BIT(0)
#define CHIP_BUCK_MODE_MASK    GENMASK(2, 1)
#define CHIP_BUCK_VSEL_MASK    GENMASK(5, 0)
#define CHIP_BUCK_ACTDSC_MASK  BIT(4)
```

### Step 2: Define Linear Ranges

```c
static const struct linear_range buck1_voltage_range =
    LINEAR_RANGE_INIT(700000, 25000U, 0x0U, 0x3FU);

static const struct linear_range ldo1_voltage_range =
    LINEAR_RANGE_INIT(800000, 100000U, 0x0U, 0x1FU);

static const struct linear_range buck1_current_range =
    LINEAR_RANGE_INIT(50000, 25000U, 0x02U, 0x0FU);
```

### Step 3: Define Regulator Descriptors

```c
struct regulator_chip_desc {
    uint8_t enable_reg;
    uint8_t enable_mask;
    uint8_t vsel_reg;
    uint8_t vsel_mask;
    uint8_t mode_reg;
    uint8_t mode_mask;
    const struct linear_range *voltage_range;
    const struct linear_range *current_range;
};

static const struct regulator_chip_desc buck1_desc = {
    .enable_reg = CHIP_BUCK1_CTRL,
    .enable_mask = CHIP_BUCK_EN_MASK,
    .vsel_reg = CHIP_BUCK1_VSEL,
    .vsel_mask = CHIP_BUCK_VSEL_MASK,
    .mode_reg = CHIP_BUCK1_CTRL,
    .mode_mask = CHIP_BUCK_MODE_MASK,
    .voltage_range = &buck1_voltage_range,
    .current_range = &buck1_current_range,
};
```

### Step 4: Define Config and Data Structures

```c
struct regulator_chip_config {
    struct regulator_common_config common;  // MUST be first
    struct i2c_dt_spec bus;                 // I2C bus (or SPI, MFD, etc.)
    const struct regulator_chip_desc *desc; // Descriptor
};

struct regulator_chip_data {
    struct regulator_common_data data;      // MUST be first
};
```

### Step 5: Implement API Functions

#### Enable Function

```c
static int regulator_chip_enable(const struct device *dev)
{
    const struct regulator_chip_config *config = dev->config;

    return i2c_reg_update_byte_dt(&config->bus,
                                  config->desc->enable_reg,
                                  config->desc->enable_mask,
                                  config->desc->enable_mask);
}
```

#### Disable Function

```c
static int regulator_chip_disable(const struct device *dev)
{
    const struct regulator_chip_config *config = dev->config;

    return i2c_reg_update_byte_dt(&config->bus,
                                  config->desc->enable_reg,
                                  config->desc->enable_mask,
                                  0);
}
```

#### Count Voltages

```c
static unsigned int regulator_chip_count_voltages(const struct device *dev)
{
    const struct regulator_chip_config *config = dev->config;

    return linear_range_values_count(config->desc->voltage_range);
}
```

#### List Voltage

```c
static int regulator_chip_list_voltage(const struct device *dev,
                                       unsigned int idx,
                                       int32_t *volt_uv)
{
    const struct regulator_chip_config *config = dev->config;

    return linear_range_get_value(config->desc->voltage_range, idx, volt_uv);
}
```

#### Set Voltage

```c
static int regulator_chip_set_voltage(const struct device *dev,
                                      int32_t min_uv,
                                      int32_t max_uv)
{
    const struct regulator_chip_config *config = dev->config;
    uint16_t idx;
    int ret;

    ret = linear_range_get_win_index(config->desc->voltage_range,
                                     min_uv, max_uv, &idx);
    if (ret == -EINVAL) {
        return ret;
    }

    return i2c_reg_update_byte_dt(&config->bus,
                                  config->desc->vsel_reg,
                                  config->desc->vsel_mask,
                                  idx);
}
```

#### Get Voltage

```c
static int regulator_chip_get_voltage(const struct device *dev,
                                      int32_t *volt_uv)
{
    const struct regulator_chip_config *config = dev->config;
    uint8_t idx;
    int ret;

    ret = i2c_reg_read_byte_dt(&config->bus, config->desc->vsel_reg, &idx);
    if (ret < 0) {
        return ret;
    }

    idx &= config->desc->vsel_mask;

    return linear_range_get_value(config->desc->voltage_range, idx, volt_uv);
}
```

#### Set Mode

```c
static int regulator_chip_set_mode(const struct device *dev,
                                   regulator_mode_t mode)
{
    const struct regulator_chip_config *config = dev->config;

    // Validate mode against allowed_modes if needed
    if (mode > CHIP_MODE_MAX) {
        return -ENOTSUP;
    }

    return i2c_reg_update_byte_dt(&config->bus,
                                  config->desc->mode_reg,
                                  config->desc->mode_mask,
                                  mode << MODE_SHIFT);
}
```

#### Get Mode

```c
static int regulator_chip_get_mode(const struct device *dev,
                                   regulator_mode_t *mode)
{
    const struct regulator_chip_config *config = dev->config;
    uint8_t val;
    int ret;

    ret = i2c_reg_read_byte_dt(&config->bus, config->desc->mode_reg, &val);
    if (ret < 0) {
        return ret;
    }

    *mode = (val & config->desc->mode_mask) >> MODE_SHIFT;

    return 0;
}
```

### Step 6: Define API Structure

```c
static DEVICE_API(regulator, regulator_chip_api) = {
    .enable = regulator_chip_enable,
    .disable = regulator_chip_disable,
    .count_voltages = regulator_chip_count_voltages,
    .list_voltage = regulator_chip_list_voltage,
    .set_voltage = regulator_chip_set_voltage,
    .get_voltage = regulator_chip_get_voltage,
    .set_mode = regulator_chip_set_mode,
    .get_mode = regulator_chip_get_mode,
    // Add other functions as supported
};
```

### Step 7: Implement Init Function

```c
static int regulator_chip_init(const struct device *dev)
{
    const struct regulator_chip_config *config = dev->config;
    bool is_enabled = false;
    int ret;

    // Check I2C bus ready
    if (!i2c_is_ready_dt(&config->bus)) {
        return -ENODEV;
    }

    // Initialize common data (sets up reference count)
    regulator_common_data_init(dev);

    // Determine if regulator is already enabled
    uint8_t val;
    ret = i2c_reg_read_byte_dt(&config->bus, config->desc->enable_reg, &val);
    if (ret == 0) {
        is_enabled = (val & config->desc->enable_mask) != 0;
    }

    // Common init handles boot-on, always-on, initial voltage/mode
    return regulator_common_init(dev, is_enabled);
}
```

### Step 8: Device Instantiation Macro

For simple single-regulator devices:

```c
#define REGULATOR_CHIP_DEFINE(inst, source_name, desc_ptr)                    \
    static struct regulator_chip_data data_##inst##_##source_name;            \
                                                                               \
    static const struct regulator_chip_config config_##inst##_##source_name = {\
        .common = REGULATOR_DT_COMMON_CONFIG_INIT(                            \
                    DT_INST_CHILD(inst, source_name)),                        \
        .bus = I2C_DT_SPEC_INST_GET(inst),                                    \
        .desc = desc_ptr,                                                     \
    };                                                                        \
                                                                               \
    DEVICE_DT_DEFINE(DT_INST_CHILD(inst, source_name),                        \
                     regulator_chip_init,                                     \
                     NULL,                                                    \
                     &data_##inst##_##source_name,                            \
                     &config_##inst##_##source_name,                          \
                     POST_KERNEL,                                             \
                     CONFIG_REGULATOR_CHIP_INIT_PRIORITY,                     \
                     &regulator_chip_api);

#define REGULATOR_CHIP_DEFINE_COND(inst, child)                               \
    COND_CODE_1(DT_NODE_EXISTS(DT_INST_CHILD(inst, child)),                   \
                (REGULATOR_CHIP_DEFINE(inst, child, &child##_desc)),          \
                ())

#define REGULATOR_CHIP_DEFINE_ALL(inst)                                       \
    REGULATOR_CHIP_DEFINE_COND(inst, BUCK1)                                   \
    REGULATOR_CHIP_DEFINE_COND(inst, BUCK2)                                   \
    REGULATOR_CHIP_DEFINE_COND(inst, LDO1)                                    \
    REGULATOR_CHIP_DEFINE_COND(inst, LDO2)

DT_INST_FOREACH_STATUS_OKAY(REGULATOR_CHIP_DEFINE_ALL)
```

