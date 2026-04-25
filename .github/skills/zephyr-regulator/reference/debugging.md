## Debugging Tips

### 1. Check Devicetree

```bash
# Check generated devicetree
west build -t devicetree_unfold
# Look in build/zephyr/zephyr.dts
```

### 2. Enable Logging

```c
LOG_MODULE_REGISTER(regulator_mychip, CONFIG_REGULATOR_LOG_LEVEL);

LOG_DBG("Setting voltage to %d uV (index %d)", volt_uv, idx);
LOG_ERR("Failed to enable regulator: %d", ret);
```

### 3. Verify Register Access

```c
uint8_t val;
ret = i2c_reg_read_byte_dt(&config->bus, reg, &val);
LOG_DBG("Read reg 0x%02X = 0x%02X (ret=%d)", reg, val, ret);
```

### 4. Check Init Priority

Regulators typically use `POST_KERNEL` with appropriate priority:

```c
DEVICE_DT_DEFINE(node, init_fn, NULL, &data, &config,
                 POST_KERNEL,
                 CONFIG_REGULATOR_MYCHIP_INIT_PRIORITY,
                 &api);
```

### 5. Test Reference Counting

```c
// Enable twice
regulator_enable(reg);
regulator_enable(reg);

// Should still be enabled after one disable
regulator_disable(reg);
assert(regulator_is_enabled(reg));

// Should be off after second disable
regulator_disable(reg);
assert(!regulator_is_enabled(reg));
```

### 6. Verify Linear Range Calculations

```c
// Test boundary conditions
int32_t uv;
linear_range_get_value(&range, 0, &uv);  // Min value
linear_range_get_value(&range, max_idx, &uv);  // Max value

uint16_t idx;
linear_range_get_win_index(&range, min_uv, max_uv, &idx);
```

