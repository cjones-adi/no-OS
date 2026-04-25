# Ztest Test Macros Reference

Complete reference for all Ztest test macros and when to use each one.

## Quick Reference Table

| Macro | Fixture | Parameters | Userspace | Use Case |
|-------|---------|------------|-----------|----------|
| `ZTEST(suite, test)` | ❌ No | ❌ No | ❌ No | Simple tests without shared state |
| `ZTEST_F(suite, test)` | ✅ Yes | ❌ No | ❌ No | Tests accessing fixture data |
| `ZTEST_P(suite, test)` | ❌ No | ✅ Yes | ❌ No | Parameterized tests (same logic, different inputs) |
| `ZTEST_P_F(suite, test)` | ✅ Yes | ✅ Yes | ❌ No | Parameterized tests with fixture |
| `ZTEST_USER(suite, test)` | ❌ No | ❌ No | ✅ Yes | Userspace thread tests |
| `ZTEST_USER_F(suite, test)` | ✅ Yes | ❌ No | ✅ Yes | Userspace tests with fixture |

**Key**:
- **Fixture**: Access to suite fixture via `fixture` pointer
- **Parameters**: Access to test parameters via `data` pointer
- **Userspace**: Runs in userspace thread (requires `CONFIG_USERSPACE`)

---

## ZTEST() - Standard Test Function

**Usage**: Basic tests without fixtures

```c
ZTEST(suite_name, test_name)
{
    // Test implementation
    // No fixture available
}
```

**When to use**:
- Simple tests that don't need shared state
- Tests that get resources directly from devicetree
- Stateless API validation

**Example**:
```c
ZTEST(sensor_api, test_null_device_handling)
{
    struct sensor_value val;
    int ret = sensor_sample_fetch(NULL);  // Test NULL device
    zassert_equal(ret, -EINVAL, "Should reject NULL device");
}
```

---

## ZTEST_F() - Test with Fixture

**Usage**: Tests that access fixture data

```c
ZTEST_F(suite_name, test_name)
{
    // Access fixture via 'fixture' pointer
    const struct device *dev = fixture->dev;
    // Test implementation
}
```

**When to use**:
- Tests need access to initialized devices or resources
- Sharing state across tests in a suite
- Avoiding repeated initialization in each test

**Critical**: All tests in a suite must use the **same macro**. Mixing `ZTEST()` and `ZTEST_F()` in one suite causes compilation errors.

**Example**:
```c
struct sensor_fixture {
    const struct device *dev;
};

static void *sensor_setup(void) {
    static struct sensor_fixture fix;
    fix.dev = DEVICE_DT_GET(DT_NODELABEL(sensor));
    return &fix;
}

ZTEST_F(sensor_tests, test_sample_fetch)
{
    // 'fixture' automatically available
    int ret = sensor_sample_fetch(fixture->dev);
    zassert_ok(ret);
}

ZTEST_SUITE(sensor_tests, NULL, sensor_setup, NULL, NULL, NULL);
```

---

## ZTEST_P() - Parameterized Tests

**Usage**: Run the same test logic with different input parameters

```c
ZTEST_P(suite_name, test_name)
{
    // Access parameter via 'data' pointer
    const struct test_param *param = data;
    // Test implementation using param
}
```

**When to use**:
- Testing the same functionality with different inputs
- Validating behavior across multiple configurations
- Reducing code duplication for similar test cases

**Complete Example**: Testing sensor ODR settings

```c
/* Define parameter structure */
struct odr_test_param {
    int odr_hz;
    uint8_t expected_reg_value;
};

/* Define parameter array */
static const struct odr_test_param odr_params[] = {
    { .odr_hz = 400,  .expected_reg_value = 0x00 },
    { .odr_hz = 800,  .expected_reg_value = 0x01 },
    { .odr_hz = 1600, .expected_reg_value = 0x02 },
    { .odr_hz = 3200, .expected_reg_value = 0x03 },
    { .odr_hz = 6400, .expected_reg_value = 0x04 },
};

/* Parameterized test */
ZTEST_P(sensor_odr, test_odr_configuration)
{
    const struct odr_test_param *param = data;
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(sensor));
    struct sensor_value odr;
    int ret;
    
    /* Set ODR */
    odr.val1 = param->odr_hz;
    odr.val2 = 0;
    ret = sensor_attr_set(dev, SENSOR_CHAN_ACCEL_XYZ,
                          SENSOR_ATTR_SAMPLING_FREQUENCY, &odr);
    zassert_ok(ret, "Failed to set ODR=%d Hz", param->odr_hz);
    
    /* Verify register value */
    uint8_t reg_val;
    ret = sensor_read_reg(dev, ODR_REG, &reg_val);
    zassert_equal(reg_val, param->expected_reg_value,
                  "ODR=%d Hz: expected reg=0x%02x, got 0x%02x",
                  param->odr_hz, param->expected_reg_value, reg_val);
}

/* Register parameterized test */
ZTEST_SUITE_P(sensor_odr, NULL, NULL, NULL, NULL, NULL);

/* Define parameter set */
ZTEST_P_SET(sensor_odr, odr_params);
```

**How it works**:
1. Define parameter structure and array
2. Use `ZTEST_P()` macro - access parameters via `data` pointer
3. Register suite with `ZTEST_SUITE_P()` 
4. Define parameter set with `ZTEST_P_SET()`

**Benefits**:
- Single test function runs multiple times with different inputs
- Each parameter combination appears as separate test case in reports
- Reduces boilerplate for similar tests
- Easy to add new test cases by extending parameter array

**Test output example**:
```
START - sensor_odr.test_odr_configuration[0]  # 400 Hz
 PASS - sensor_odr.test_odr_configuration[0] in 0.001 seconds
START - sensor_odr.test_odr_configuration[1]  # 800 Hz
 PASS - sensor_odr.test_odr_configuration[1] in 0.001 seconds
...
```

---

## ZTEST_P_F() - Parameterized Tests with Fixture

Combine parameterized tests with fixtures:

```c
ZTEST_P_F(suite_name, test_name)
{
    const struct param_type *param = data;
    const struct device *dev = fixture->dev;
    // Test using both fixture and parameter
}
```

---

## ZTEST_USER() and ZTEST_USER_F() - Userspace Tests

**Usage**: Tests running in userspace thread (requires `CONFIG_USERSPACE`)

```c
ZTEST_USER(suite_name, test_name)        // Userspace, no fixture
ZTEST_USER_F(suite_name, test_name)      // Userspace with fixture
```

**When to use**:
- Testing userspace APIs and system calls
- Validating permission checks
- Testing kernel/user boundary behavior

**Note**: Fixtures must use `ZTEST_DMEM` or `ZTEST_BMEM` for kernel/userspace shared memory.

---

## Test Rules - Cross-Suite Logic

**Test rules** execute custom logic across **all tests** regardless of suite membership.

**Signature**:
```c
ZTEST_RULE(rule_name, before_fn, after_fn)
```

**When to use**:
- Resetting mocks or emulators before every test
- Clearing UART buffers
- Resetting global state that affects multiple suites

**Example**:
```c
static void reset_emulators(const struct ztest_unit_test *test, void *fixture)
{
    i2c_emul_reset_all();
    spi_emul_reset_all();
}

ZTEST_RULE(emulator_reset, reset_emulators, NULL);
```

---

## Critical Rules

1. **Consistent macro usage**: All tests in a suite must use the same macro type
2. **Fixture pointer**: Only available in `ZTEST_F()`, `ZTEST_P_F()`, `ZTEST_USER_F()`
3. **Parameter pointer**: Only available in `ZTEST_P()` and `ZTEST_P_F()`
4. **Suite registration**: Use matching `ZTEST_SUITE()` or `ZTEST_SUITE_P()`
