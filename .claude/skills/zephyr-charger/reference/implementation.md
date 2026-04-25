## Driver Implementation Pattern

### Step 1: Define Register Map

```c
/* Charger registers */
#define CHG_CTRL_REG         0x00
#define CHG_STATUS_REG       0x01
#define CHG_CURRENT_REG      0x02
#define CHG_VOLTAGE_REG      0x03
#define CHG_TERM_CURRENT_REG 0x04
#define CHG_INPUT_LIMIT_REG  0x05

/* Control register bits */
#define CHG_EN               BIT(0)
#define CHG_WD_RST           BIT(1)

/* Status register bits */
#define CHG_STAT_MASK        GENMASK(4, 3)
#define CHG_STAT_NOT_CHG     (0 << 3)
#define CHG_STAT_PRECHARGE   (1 << 3)
#define CHG_STAT_FAST_CHG    (2 << 3)
#define CHG_STAT_TERMINATED  (3 << 3)
```

### Step 2: Define Config and Data Structures

**Config structure**:

```c
struct charger_chip_config {
    struct i2c_dt_spec i2c;
    uint32_t max_charge_current_ua;     /* devicetree */
    uint32_t max_charge_voltage_uv;     /* devicetree */
    uint32_t input_current_limit_ua;    /* devicetree */
};
```

**Data structure**:

```c
struct charger_chip_data {
    enum charger_status status;
    enum charger_online online;
    enum charger_health health;
    bool charging_enabled;
    struct k_mutex lock;
};
```

### Step 3: Implement get_property Function

```c
static int charger_chip_get_property(const struct device *dev,
                                      charger_prop_t prop,
                                      union charger_propval *val)
{
    const struct charger_chip_config *cfg = dev->config;
    struct charger_chip_data *data = dev->data;
    int ret = 0;
    uint8_t reg_val;

    k_mutex_lock(&data->lock, K_FOREVER);

    switch (prop) {
    case CHARGER_PROP_STATUS:
        /* Read status register */
        ret = i2c_reg_read_byte_dt(&cfg->i2c, CHG_STATUS_REG, &reg_val);
        if (ret == 0) {
            uint8_t chg_stat = reg_val & CHG_STAT_MASK;

            switch (chg_stat) {
            case CHG_STAT_NOT_CHG:
                val->status = CHARGER_STATUS_NOT_CHARGING;
                break;
            case CHG_STAT_PRECHARGE:
            case CHG_STAT_FAST_CHG:
                val->status = CHARGER_STATUS_CHARGING;
                break;
            case CHG_STAT_TERMINATED:
                val->status = CHARGER_STATUS_FULL;
                break;
            }

            data->status = val->status;
        }
        break;

    case CHARGER_PROP_ONLINE:
        /* Read power good status */
        ret = i2c_reg_read_byte_dt(&cfg->i2c, CHG_STATUS_REG, &reg_val);
        if (ret == 0) {
            if (reg_val & CHG_PG_STAT) {
                val->online = CHARGER_ONLINE_FIXED;
            } else {
                val->online = CHARGER_ONLINE_OFFLINE;
            }
            data->online = val->online;
        }
        break;

    case CHARGER_PROP_CONSTANT_CHARGE_CURRENT_UA:
        /* Read configured charge current */
        ret = i2c_reg_read_byte_dt(&cfg->i2c, CHG_CURRENT_REG, &reg_val);
        if (ret == 0) {
            /* Convert register value to µA */
            val->const_charge_current_ua = reg_val * 64000; /* 64mA steps */
        }
        break;

    case CHARGER_PROP_CONSTANT_CHARGE_VOLTAGE_UV:
        /* Read configured charge voltage */
        ret = i2c_reg_read_byte_dt(&cfg->i2c, CHG_VOLTAGE_REG, &reg_val);
        if (ret == 0) {
            /* Convert register value to µV */
            val->const_charge_voltage_uv = (3840000 + (reg_val * 16000));
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

### Step 4: Implement set_property Function

```c
static int charger_chip_set_property(const struct device *dev,
                                      charger_prop_t prop,
                                      const union charger_propval *val)
{
    const struct charger_chip_config *cfg = dev->config;
    struct charger_chip_data *data = dev->data;
    int ret = 0;
    uint8_t reg_val;

    k_mutex_lock(&data->lock, K_FOREVER);

    switch (prop) {
    case CHARGER_PROP_CONSTANT_CHARGE_CURRENT_UA:
        /* Validate against max */
        if (val->const_charge_current_ua > cfg->max_charge_current_ua) {
            ret = -EINVAL;
            break;
        }

        /* Convert µA to register value (64mA steps) */
        reg_val = val->const_charge_current_ua / 64000;
        ret = i2c_reg_write_byte_dt(&cfg->i2c, CHG_CURRENT_REG, reg_val);
        break;

    case CHARGER_PROP_CONSTANT_CHARGE_VOLTAGE_UV:
        /* Validate against max */
        if (val->const_charge_voltage_uv > cfg->max_charge_voltage_uv) {
            ret = -EINVAL;
            break;
        }

        /* Convert µV to register value (16mV steps above 3.84V) */
        if (val->const_charge_voltage_uv < 3840000) {
            ret = -EINVAL;
            break;
        }
        reg_val = (val->const_charge_voltage_uv - 3840000) / 16000;
        ret = i2c_reg_write_byte_dt(&cfg->i2c, CHG_VOLTAGE_REG, reg_val);
        break;

    case CHARGER_PROP_INPUT_REGULATION_CURRENT_UA:
        /* Set input current limit */
        reg_val = val->input_current_regulation_current_ua / 100000; /* 100mA steps */
        ret = i2c_reg_write_byte_dt(&cfg->i2c, CHG_INPUT_LIMIT_REG, reg_val);
        break;

    default:
        ret = -ENOTSUP;
        break;
    }

    k_mutex_unlock(&data->lock);
    return ret;
}
```

### Step 5: Implement charge_enable Function

```c
static int charger_chip_charge_enable(const struct device *dev, bool enable)
{
    const struct charger_chip_config *cfg = dev->config;
    struct charger_chip_data *data = dev->data;
    int ret;

    k_mutex_lock(&data->lock, K_FOREVER);

    if (enable) {
        /* Enable charging */
        ret = i2c_reg_update_byte_dt(&cfg->i2c, CHG_CTRL_REG,
                                     CHG_EN, CHG_EN);
    } else {
        /* Disable charging */
        ret = i2c_reg_update_byte_dt(&cfg->i2c, CHG_CTRL_REG,
                                     CHG_EN, 0);
    }

    if (ret == 0) {
        data->charging_enabled = enable;
    }

    k_mutex_unlock(&data->lock);
    return ret;
}
```

### Step 6: Define API Structure

```c
static const struct charger_driver_api charger_chip_driver_api = {
    .get_property = charger_chip_get_property,
    .set_property = charger_chip_set_property,
    .charge_enable = charger_chip_charge_enable,
};
```

### Step 7: Implement Init Function

```c
static int charger_chip_init(const struct device *dev)
{
    const struct charger_chip_config *cfg = dev->config;
    struct charger_chip_data *data = dev->data;
    int ret;

    /* Check I2C bus */
    if (!device_is_ready(cfg->i2c.bus)) {
        return -ENODEV;
    }

    /* Initialize mutex */
    k_mutex_init(&data->lock);

    /* Reset watchdog */
    ret = i2c_reg_update_byte_dt(&cfg->i2c, CHG_CTRL_REG,
                                 CHG_WD_RST, CHG_WD_RST);
    if (ret < 0) {
        return ret;
    }

    /* Configure charge current from devicetree */
    union charger_propval val;
    val.const_charge_current_ua = cfg->max_charge_current_ua;
    ret = charger_chip_set_property(dev, CHARGER_PROP_CONSTANT_CHARGE_CURRENT_UA, &val);
    if (ret < 0) {
        return ret;
    }

    /* Configure charge voltage from devicetree */
    val.const_charge_voltage_uv = cfg->max_charge_voltage_uv;
    ret = charger_chip_set_property(dev, CHARGER_PROP_CONSTANT_CHARGE_VOLTAGE_UV, &val);
    if (ret < 0) {
        return ret;
    }

    /* Configure input current limit */
    val.input_current_regulation_current_ua = cfg->input_current_limit_ua;
    ret = charger_chip_set_property(dev, CHARGER_PROP_INPUT_REGULATION_CURRENT_UA, &val);
    if (ret < 0) {
        return ret;
    }

    /* Enable charging */
    return charger_chip_charge_enable(dev, true);
}
```

### Step 8: Device Instantiation Macro

```c
#define CHARGER_CHIP_DEFINE(inst)                                       \
    static struct charger_chip_data charger_chip_data_##inst;           \
                                                                        \
    static const struct charger_chip_config charger_chip_config_##inst = { \
        .i2c = I2C_DT_SPEC_INST_GET(inst),                              \
        .max_charge_current_ua = DT_INST_PROP(inst, constant_charge_current_max_microamp), \
        .max_charge_voltage_uv = DT_INST_PROP(inst, constant_charge_voltage_max_microvolt), \
        .input_current_limit_ua = DT_INST_PROP(inst, input_current_limit_microamp), \
    };                                                                  \
                                                                        \
    DEVICE_DT_INST_DEFINE(inst,                                         \
                          charger_chip_init,                            \
                          NULL,                                         \
                          &charger_chip_data_##inst,                    \
                          &charger_chip_config_##inst,                  \
                          POST_KERNEL,                                  \
                          CONFIG_CHARGER_INIT_PRIORITY,                 \
                          &charger_chip_driver_api);

DT_INST_FOREACH_STATUS_OKAY(CHARGER_CHIP_DEFINE)
```

## Devicetree Binding Pattern

**File**: `dts/bindings/charger/<vendor>,<chip>-charger.yaml`

```yaml
# Copyright (C) 2024 Vendor Corporation
# SPDX-License-Identifier: Apache-2.0

description: CHIP battery charger

compatible: "vendor,chip-charger"

include: i2c-device.yaml

properties:
  constant-charge-current-max-microamp:
    type: int
    required: true
    description: Maximum charge current in microamps

  constant-charge-voltage-max-microvolt:
    type: int
    required: true
    description: Maximum charge voltage in microvolts

  precharge-current-microamp:
    type: int
    description: Precharge current in microamps

  charge-term-current-microamp:
    type: int
    description: Charge termination current in microamps (end of charge)

  input-current-limit-microamp:
    type: int
    description: Input current regulation limit in microamps

  input-voltage-limit-microvolt:
    type: int
    description: Input voltage regulation threshold in microvolts
```

**Devicetree usage**:

```dts
&i2c0 {
    charger: charger@6b {
        compatible = "vendor,chip-charger";
        reg = <0x6b>;

        constant-charge-current-max-microamp = <1000000>; /* 1A */
        constant-charge-voltage-max-microvolt = <4200000>; /* 4.2V */
        precharge-current-microamp = <128000>;             /* 128mA */
        charge-term-current-microamp = <50000>;            /* 50mA */
        input-current-limit-microamp = <500000>;           /* 500mA USB */
    };
};
```

