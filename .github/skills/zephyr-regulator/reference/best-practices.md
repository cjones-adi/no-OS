## Common Patterns and Best Practices

### 1. Always Start with Common Structures

```c
struct my_regulator_config {
    struct regulator_common_config common;  // MUST be first
    // ... your fields
};

struct my_regulator_data {
    struct regulator_common_data data;      // MUST be first
    // ... your fields
};
```

### 2. Use Linear Ranges for Voltage/Current

```c
// Good - reusable, maintainable
static const struct linear_range range = LINEAR_RANGE_INIT(min, step, idx_min, idx_max);
linear_range_get_win_index(&range, min_uv, max_uv, &idx);

// Avoid - manual calculations prone to errors
idx = (voltage - min) / step;  // Don't do this
```

### 3. Validate Hardware State in Init

```c
static int my_init(const struct device *dev)
{
    bool is_enabled = false;

    regulator_common_data_init(dev);

    // Read actual hardware state
    uint8_t reg;
    if (i2c_reg_read_byte_dt(&config->bus, ENABLE_REG, &reg) == 0) {
        is_enabled = (reg & ENABLE_MASK) != 0;
    }

    // Let common init handle boot-on/always-on/init voltage
    return regulator_common_init(dev, is_enabled);
}
```

### 4. Return -ENOTSUP for Unsupported Features

```c
static int my_set_mode(const struct device *dev, regulator_mode_t mode)
{
    // LDOs may not support modes
    if (config->type == TYPE_LDO) {
        return -ENOTSUP;
    }

    // Or validate mode value
    if (mode > MAX_MODE) {
        return -ENOTSUP;
    }

    // ... implement
}
```

### 5. Don't Implement Optional Functions

If hardware doesn't support a feature, don't implement the function. Leave it as `NULL` in the API table.

```c
static DEVICE_API(regulator, my_api) = {
    .enable = my_enable,
    .disable = my_disable,
    // No set_mode - hardware doesn't support it
    .set_mode = NULL,  // or just omit
    // ...
};
```

### 6. Use Descriptors for Multiple Regulators

```c
static const struct regulator_desc buck1_desc = { /* ... */ };
static const struct regulator_desc buck2_desc = { /* ... */ };
static const struct regulator_desc ldo1_desc = { /* ... */ };

// In config, just point to the right descriptor
.desc = &buck1_desc,
```

### 7. Handle Read-Modify-Write Carefully

```c
// Good - uses helper that does RMW atomically
i2c_reg_update_byte_dt(&bus, reg, mask, value);

// Manual RMW - be careful with errors
uint8_t val;
ret = i2c_reg_read_byte_dt(&bus, reg, &val);
if (ret < 0) return ret;
val = (val & ~mask) | (value & mask);
ret = i2c_reg_write_byte_dt(&bus, reg, val);
```

