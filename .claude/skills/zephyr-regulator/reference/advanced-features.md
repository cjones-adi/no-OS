## Advanced Features

### DVS (Dynamic Voltage Scaling)

Some PMICs support multiple voltage states that can be switched via GPIO or software:

```c
struct regulator_parent_driver_api {
    regulator_dvs_state_set_t dvs_state_set;
    regulator_ship_mode_t ship_mode;
};

static int regulator_chip_parent_dvs_state_set(const struct device *dev,
                                               regulator_dvs_state_t state)
{
    const struct regulator_chip_pconfig *config = dev->config;

    // Write state to hardware
    return i2c_reg_write_byte_dt(&config->bus, CHIP_DVS_REG, state);
}
```

### Active Discharge

Allows faster discharge of output capacitor when regulator is disabled:

```c
static int regulator_chip_set_active_discharge(const struct device *dev,
                                               bool active_discharge)
{
    const struct regulator_chip_config *config = dev->config;

    return i2c_reg_update_byte_dt(&config->bus,
                                  CHIP_CTRL_REG,
                                  CHIP_ACT_DISCHARGE_MASK,
                                  active_discharge ? CHIP_ACT_DISCHARGE_MASK : 0);
}
```

### Error Flags

Report hardware error conditions:

```c
static int regulator_chip_get_error_flags(const struct device *dev,
                                         regulator_error_flags_t *flags)
{
    const struct regulator_chip_config *config = dev->config;
    uint8_t status;
    int ret;

    *flags = 0;

    ret = i2c_reg_read_byte_dt(&config->bus, CHIP_STATUS_REG, &status);
    if (ret < 0) {
        return ret;
    }

    if (status & CHIP_OV_FLAG) {
        *flags |= REGULATOR_ERROR_OVER_VOLTAGE;
    }
    if (status & CHIP_OC_FLAG) {
        *flags |= REGULATOR_ERROR_OVER_CURRENT;
    }
    if (status & CHIP_OT_FLAG) {
        *flags |= REGULATOR_ERROR_OVER_TEMP;
    }

    return 0;
}
```

### MFD (Multi-Function Device) Integration

For complex PMICs with many subsystems, use MFD parent:

```c
#define MFD_REG_READ(dev, reg, val) \
    chip_mfd_reg_read(((const struct regulator_chip_config *)(dev)->config)->mfd_dev, \
                      (reg), (val))

#define MFD_REG_WRITE(dev, reg, val) \
    chip_mfd_reg_write(((const struct regulator_chip_config *)(dev)->config)->mfd_dev, \
                       (reg), (val))

struct regulator_chip_config {
    struct regulator_common_config common;
    const struct device *mfd_dev;    // Parent MFD device
    const struct regulator_chip_desc *desc;
};
```

