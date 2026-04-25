## Driver Implementation Pattern

### Step 1: Define SBS Register Map

For SBS-compliant fuel gauges:

```c
/* SBS standard registers */
#define SBS_REG_MANUFACTURER_ACCESS   0x00
#define SBS_REG_REMAINING_CAPACITY    0x0F  /* mAh */
#define SBS_REG_FULL_CHARGE_CAPACITY  0x10  /* mAh */
#define SBS_REG_VOLTAGE               0x09  /* mV */
#define SBS_REG_CURRENT               0x0A  /* mA */
#define SBS_REG_AVERAGE_CURRENT       0x0B  /* mA */
#define SBS_REG_TEMPERATURE           0x08  /* 0.1 K */
#define SBS_REG_RELATIVE_SOC          0x0D  /* % */
#define SBS_REG_ABSOLUTE_SOC          0x0E  /* % */
#define SBS_REG_CYCLE_COUNT           0x17
#define SBS_REG_DESIGN_CAPACITY       0x18  /* mAh */
#define SBS_REG_DESIGN_VOLTAGE        0x19  /* mV */
#define SBS_REG_BATTERY_STATUS        0x16
#define SBS_REG_MANUFACTURER_NAME     0x20  /* String (21 bytes) */
#define SBS_REG_DEVICE_NAME           0x21  /* String (21 bytes) */
#define SBS_REG_DEVICE_CHEMISTRY      0x22  /* String (5 bytes) */

/* Battery status bits */
#define SBS_STATUS_FULLY_CHARGED      BIT(5)
#define SBS_STATUS_FULLY_DISCHARGED   BIT(4)
```

### Step 2: Define Config and Data Structures

**Config structure**:

```c
struct fg_chip_config {
    struct i2c_dt_spec i2c;
    uint32_t design_capacity_mah;     /* From devicetree */
    uint32_t design_voltage_mv;       /* From devicetree */
};
```

**Data structure**:

```c
struct fg_chip_data {
    uint16_t voltage;              /* Cached voltage (mV) */
    int16_t current;               /* Cached current (m struct k_mutex lock;
};
```

### Step 3: Implement get_property Function

```c
static int fg_chip_get_property(const struct device *dev,
                                 fuel_gauge_prop_t prop,
                                 union fuel_gauge_prop_val *val)
{
    const struct fg_chip_config *cfg = dev->config;
    struct fg_chip_data *data = dev->data;
    int ret = 0;
    uint16_t reg_val;

    k_mutex_lock(&data->lock, K_FOREVER);

    switch (prop) {
    case FUEL_GAUGE_VOLTAGE:
        /* Read voltage (mV) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_VOLTAGE, &reg_val);
        if (ret == 0) {
            /* Convert mV to µV */
            val->voltage = reg_val * 1000;
            data->voltage = reg_val;
        }
        break;

    case FUEL_GAUGE_CURRENT:
        /* Read current (mA, signed) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_CURRENT, (uint16_t *)&reg_val);
        if (ret == 0) {
            /* Convert mA to µA (signed) */
            val->current = (int16_t)reg_val * 1000;
            data->current = (int16_t)reg_val;
        }
        break;

    case FUEL_GAUGE_AVG_CURRENT:
        /* Read average current (mA, signed) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_AVERAGE_CURRENT,
                                (uint16_t *)&reg_val);
        if (ret == 0) {
            val->avg_current = (int16_t)reg_val * 1000;
        }
        break;

    case FUEL_GAUGE_TEMPERATURE:
        /* Read temperature (0.1 K) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_TEMPERATURE, &reg_val);
        if (ret == 0) {
            val->temperature = reg_val;
        }
        break;

    case FUEL_GAUGE_RELATIVE_STATE_OF_CHARGE:
        /* Read SOC (%) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_RELATIVE_SOC, &reg_val);
        if (ret == 0) {
            /* Clamp to 0-100% */
            val->relative_state_of_charge = MIN(reg_val, 100);
            data->soc = val->relative_state_of_charge;
        }
        break;

    case FUEL_GAUGE_REMAINING_CAPACITY:
        /* Read remaining capacity (mAh) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_REMAINING_CAPACITY, &reg_val);
        if (ret == 0) {
            /* Convert mAh to µAh */
            val->remaining_capacity = reg_val * 1000;
        }
        break;

    case FUEL_GAUGE_FULL_CHARGE_CAPACITY:
        /* Read full charge capacity (mAh) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_FULL_CHARGE_CAPACITY, &reg_val);
        if (ret == 0) {
            val->full_charge_capacity = reg_val * 1000;
        }
        break;

    case FUEL_GAUGE_CYCLE_COUNT:
        /* Read cycle count */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_CYCLE_COUNT, &reg_val);
        if (ret == 0) {
            val->cycle_count = reg_val;
        }
        break;

    case FUEL_GAUGE_DESIGN_CAPACITY:
        /* Read design capacity (mAh) */
        ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_DESIGN_CAPACITY, &reg_val);
        if (ret == 0) {
            val->design_capacity = reg_val;
        }
        break;

    default:
        ret = -ENOTSUP;
        break;
    }

    k_mutex_unlock(&data->lock);
    return ret;
}
```

### Step 4: Implement get_buffer_property (for strings)

```c
static int fg_chip_get_buffer_property(const struct device *dev,
                                        fuel_gauge_prop_t prop,
                                        void *dst, size_t dst_len)
{
    const struct fg_chip_config *cfg = dev->config;
    uint8_t buf[32];
    uint8_t len;
    int ret;

    switch (prop) {
    case FUEL_GAUGE_MANUFACTURER_NAME:
        /* Read SBS manufacturer name (block read) */
        ret = i2c_burst_read_dt(&cfg->i2c, SBS_REG_MANUFACTURER_NAME,
                                buf, sizeof(buf));
        if (ret < 0) {
            return ret;
        }

        /* First byte is length */
        len = buf[0];
        if (len > dst_len - 1) {
            len = dst_len - 1;
        }

        memcpy(dst, &buf[1], len);
        ((char *)dst)[len] = '\0';
        break;

    case FUEL_GAUGE_DEVICE_NAME:
        /* Read device name */
        ret = i2c_burst_read_dt(&cfg->i2c, SBS_REG_DEVICE_NAME,
                                buf, sizeof(buf));
        if (ret < 0) {
            return ret;
        }

        len = buf[0];
        if (len > dst_len - 1) {
            len = dst_len - 1;
        }

        memcpy(dst, &buf[1], len);
        ((char *)dst)[len] = '\0';
        break;

    case FUEL_GAUGE_DEVICE_CHEMISTRY:
        /* Read chemistry (e.g., "LION") */
        ret = i2c_burst_read_dt(&cfg->i2c, SBS_REG_DEVICE_CHEMISTRY,
                                buf, sizeof(buf));
        if (ret < 0) {
            return ret;
        }

        len = buf[0];
        if (len > dst_len - 1) {
            len = dst_len - 1;
        }

        memcpy(dst, &buf[1], len);
        ((char *)dst)[len] = '\0';
        break;

    default:
        return -ENOTSUP;
    }

    return 0;
}
```

### Step 5: Implement set_property (if applicable)

Some fuel gauges allow configuration:

```c
static int fg_chip_set_property(const struct device *dev,
                                 fuel_gauge_prop_t prop,
                                 union fuel_gauge_prop_val val)
{
    /* Most SBS properties are read-only */
    /* Some chips support writing manufacturer access commands */

    return -ENOTSUP;  /* Read-only for most SBS registers */
}
```

### Step 6: Implement battery_cutoff (ship mode)

```c
static int fg_chip_battery_cutoff(const struct device *dev)
{
    const struct fg_chip_config *cfg = dev->config;

    /* Send ship mode command (chip-specific) */
    /* Example: write manufacturer access command */
    uint16_t ship_mode_cmd = 0x0010;

    return i2c_reg_write_word(&cfg->i2c,
                              SBS_REG_MANUFACTURER_ACCESS,
                              ship_mode_cmd);
}
```

### Step 7: Define API Structure

```c
static const struct fuel_gauge_driver_api fg_chip_driver_api = {
    .get_property = fg_chip_get_property,
    .set_property = fg_chip_set_property,
    .get_buffer_property = fg_chip_get_buffer_property,
    .battery_cutoff = fg_chip_battery_cutoff,
};
```

### Step 8: Implement Init Function

```c
static int fg_chip_init(const struct device *dev)
{
    const struct fg_chip_config *cfg = dev->config;
    struct fg_chip_data *data = dev->data;
    uint16_t design_cap;
    int ret;

    /* Check I2C bus */
    if (!device_is_ready(cfg->i2c.bus)) {
        return -ENODEV;
    }

    /* Initialize mutex */
    k_mutex_init(&data->lock);

    /* Verify fuel gauge communication */
    ret = i2c_reg_read_word(&cfg->i2c, SBS_REG_DESIGN_CAPACITY, &design_cap);
    if (ret < 0) {
        LOG_ERR("Failed to read fuel gauge: %d", ret);
        return ret;
    }

    LOG_INF("Fuel gauge initialized, design capacity: %u mAh", design_cap);

    /* Read initial SOC */
    union fuel_gauge_prop_val val;
    fg_chip_get_property(dev, FUEL_GAUGE_RELATIVE_STATE_OF_CHARGE, &val);
    LOG_INF("Initial SOC: %u%%", val.relative_state_of_charge);

    return 0;
}
```

### Step 9: Device Instantiation Macro

```c
#define FG_CHIP_DEFINE(inst)                                            \
    static struct fg_chip_data fg_chip_data_##inst;                     \
                                                                        \
    static const struct fg_chip_config fg_chip_config_##inst = {        \
        .i2c = I2C_DT_SPEC_INST_GET(inst),                              \
        .design_capacity_mah = DT_INST_PROP_OR(inst, design_capacity, 0), \
        .design_voltage_mv = DT_INST_PROP_OR(inst, design_voltage, 0),  \
    };                                                                  \
                                                                        \
    DEVICE_DT_INST_DEFINE(inst,                                         \
                          fg_chip_init,                                 \
                          NULL,                                         \
                          &fg_chip_data_##inst,                         \
                          &fg_chip_config_##inst,                       \
                          POST_KERNEL,                                  \
                          CONFIG_FUEL_GAUGE_INIT_PRIORITY,              \
                          &fg_chip_driver_api);

DT_INST_FOREACH_STATUS_OKAY(FG_CHIP_DEFINE)
```

## Devicetree Binding Pattern

**File**: `dts/bindings/fuel-gauge/<vendor>,<chip>.yaml`

```yaml
# Copyright (C) 2024 Vendor Corporation
# SPDX-License-Identifier: Apache-2.0

description: CHIP fuel gauge (SBS-compliant)

compatible: "vendor,chip-fuel-gauge"

include: i2c-device.yaml

properties:
  design-voltage:
    type: int
    description: Design voltage in millivolts

  design-capacity:
    type: int
    description: Design capacity in milliamp-hours

  sense-resistor-micro-ohms:
    type: int
    description: Current sense resistor value in micro-ohms
```

**Devicetree usage**:

```dts
&i2c0 {
    fuel_gauge: fuel-gauge@55 {
        compatible = "vendor,chip-fuel-gauge";
        reg = <0x55>;  /* SBS standard address: 0x0B or 0x55 */

        design-voltage = <3700>;    /* 3.7V nominal */
        design-capacity = <2000>;   /* 2000 mAh */
        sense-resistor-micro-ohms = <10000>; /* 10 mΩ */
    };
};
```

