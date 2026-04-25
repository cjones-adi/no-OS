## Consumer API Usage

How drivers/applications use regulators:

### Enable/Disable (Reference-Counted)

```c
const struct device *reg = DEVICE_DT_GET(DT_NODELABEL(vdd_cpu));

// Enable - increments refcount
ret = regulator_enable(reg);

// Disable - decrements refcount, turns off when refcount reaches 0
ret = regulator_disable(reg);

// Check state
bool enabled = regulator_is_enabled(reg);
```

### Set Voltage

```c
// Set voltage to closest supported voltage in range
ret = regulator_set_voltage(reg, 1000000, 1100000);  // 1.0V-1.1V

// Get actual voltage
int32_t actual_uv;
ret = regulator_get_voltage(reg, &actual_uv);
```

### Set Current Limit

```c
ret = regulator_set_current_limit(reg, 100000, 150000);  // 100-150 mA

int32_t actual_ua;
ret = regulator_get_current_limit(reg, &actual_ua);
```

### Set Mode

```c
#include <zephyr/dt-bindings/regulator/vendor_chip.h>

ret = regulator_set_mode(reg, CHIP_MODE_LOW_POWER);

regulator_mode_t mode;
ret = regulator_get_mode(reg, &mode);
```
