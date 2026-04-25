# Unit Testing Best Practices

Best practices for no-OS driver unit testing with Ceedling, Unity, and CMock.

## CRITICAL: Always Verify Results

**Never assume tests pass or coverage is achieved without verification.**

### Required Verification Steps

1. **Run the tests**: `ceedling test:[driver_name]`
2. **Verify 100% pass rate**: Check output for PASSED count
3. **Generate coverage**: `ceedling gcov:[driver_name]`
4. **Verify coverage target**: Open HTML report and confirm ≥80% line coverage
5. **Report actual numbers**: Document real test count, pass/fail, and coverage percentage

### Why This Matters

- Mock configuration issues cause test failures
- Coverage may be lower than expected
- Tests reveal driver bugs
- Real results guide next iteration
- Assumptions lead to incomplete testing

### Never Do These

- ❌ Skip running tests and assume they work
- ❌ Skip coverage generation and estimate coverage
- ❌ Report estimated coverage percentages
- ❌ Proceed without verified test results

**Always provide actual test run results with real numbers.**

## Test Organization

1. **Group tests logically** - Initialization, configuration, operation, error handling
2. **Use descriptive names** - `test_driver_init_null_device` not `test_1`
3. **One assertion focus per test** - Easy to identify failures
4. **Keep tests short** - 5-15 lines per test typically
5. **Separate test files by feature** - `test_driver_init.c`, `test_driver_config.c`, etc.

### Example Organization

```
test/
├── test_max20370.c              # Core functionality
├── test_max20370_regulator.c    # Regulator-specific tests
└── test_max20370_error.c        # Error handling tests
```

### Test Naming Convention

```c
// Good naming - descriptive and clear
void test_driver_init_success(void);
void test_driver_init_null_device_pointer(void);
void test_driver_init_null_param(void);
void test_driver_init_i2c_failure(void);

// Bad naming - unclear purpose
void test_1(void);
void test_init(void);
void test_error(void);
```

## Mock Management

5. **Default success in setUp()** - Use `_IgnoreAndReturn(0)` for happy-path baseline
6. **Override for error tests** - Change specific mock returns in test body
7. **Use stubs for state** - Simulate hardware registers with callbacks
8. **Don't over-mock** - Avoid validating exact platform call sequences unless critical

### Mock Setup Pattern

```c
void setUp(void) {
    test_dev = NULL;
    
    // Default: all platform calls succeed
    no_os_i2c_init_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_read_IgnoreAndReturn(0);
    no_os_i2c_remove_IgnoreAndReturn(0);
}

void test_driver_error_handling(void) {
    // Override for this specific test
    no_os_i2c_write_IgnoreAndReturn(-EIO);
    
    int ret = driver_configure(test_dev);
    TEST_ASSERT_EQUAL_INT(-EIO, ret);
}
```

## Coverage Strategy

9. **Start with functions** - Ensure all exported APIs have at least one test
10. **Target error paths** - Red lines are usually missing error tests
11. **Iterate to 80%** - Generate → analyze → test → repeat
12. **Don't chase 100%** - Focus on meaningful coverage, not perfection

### Coverage Workflow

```
1. Write initial tests (init, basic functionality)
2. Generate coverage: ceedling gcov:driver_name
3. Open HTML report, identify red lines/functions
4. Add targeted tests for gaps (error paths, edge cases)
5. Repeat steps 2-4 until 80%+ reached
```

## Test Quality

13. **Test error codes** - Verify `-EINVAL`, `-ENODEV`, etc.
14. **Test NULL safety** - All pointer parameters should have NULL tests
15. **Test ranges** - Min/max values, boundary conditions
16. **Test cleanup** - Verify resources freed on failure paths

### Error Code Testing

```c
// Test all error paths
void test_driver_configure_null_device(void) {
    int ret = driver_configure(NULL, 100);
    TEST_ASSERT_EQUAL_INT(-ENODEV, ret);
}

void test_driver_configure_invalid_value(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = driver_configure(test_dev, 999999);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}

void test_driver_configure_platform_failure(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    no_os_i2c_write_IgnoreAndReturn(-EIO);
    
    int ret = driver_configure(test_dev, 100);
    TEST_ASSERT_EQUAL_INT(-EIO, ret);
}
```

### NULL Safety Testing

```c
// Test every pointer parameter
void test_driver_init_null_device_pointer(void) {
    struct driver_init_param init = { /* valid */ };
    int ret = driver_init(NULL, &init);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}

void test_driver_init_null_param(void) {
    struct driver_dev *dev = NULL;
    int ret = driver_init(&dev, NULL);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
    TEST_ASSERT_NULL(dev);
}

void test_driver_get_value_null_output(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = driver_get_value(test_dev, NULL);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}
```

### Range Testing

```c
// Test boundary conditions
void test_set_voltage_min_value(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = set_voltage(test_dev, 0, MIN_VOLTAGE);
    TEST_ASSERT_EQUAL_INT(0, ret);
}

void test_set_voltage_max_value(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = set_voltage(test_dev, 0, MAX_VOLTAGE);
    TEST_ASSERT_EQUAL_INT(0, ret);
}

void test_set_voltage_below_min(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = set_voltage(test_dev, 0, MIN_VOLTAGE - 1);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}

void test_set_voltage_above_max(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = set_voltage(test_dev, 0, MAX_VOLTAGE + 1);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}
```

## Debugging

17. **Read compiler errors carefully** - Missing mock includes are common
18. **Check mock call counts** - `_Expect` functions are strict
19. **Use verbose mode** - `ceedling test:name --verbosity=obnoxious`
20. **Verify test runs** - Sometimes tests compile but don't execute

### Debugging Techniques

**Verbose output**:
```bash
ceedling test:driver_name --verbosity=obnoxious
```

**Check test discovery**:
```bash
# Ensure tests are found
ceedling files:test
```

**Verify mocks generated**:
```bash
# Check build directory for mock files
ls build/test/mocks/
```

**Clean build**:
```bash
# Remove stale builds
ceedling clobber
ceedling test:all
```

## Common Patterns

### Pattern 1: Helper Function for Device Creation

```c
static int create_mock_device(void) {
    test_dev = calloc(1, sizeof(struct driver_dev));
    if (!test_dev)
        return -ENOMEM;
    
    test_dev->i2c_desc = calloc(1, sizeof(struct no_os_i2c_desc));
    if (!test_dev->i2c_desc) {
        free(test_dev);
        test_dev = NULL;
        return -ENOMEM;
    }
    
    return 0;
}

void test_driver_configure(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    
    int ret = driver_configure(test_dev, 100);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

### Pattern 2: Fixture Setup and Teardown

```c
void setUp(void) {
    // Reset state before EACH test
    test_dev = NULL;
    
    // Configure default mock behavior
    no_os_i2c_init_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
}

void tearDown(void) {
    // Clean up after EACH test
    if (test_dev) {
        if (test_dev->i2c_desc)
            free(test_dev->i2c_desc);
        free(test_dev);
        test_dev = NULL;
    }
}
```

### Pattern 3: Testing Initialization Sequence

```c
void test_driver_init_verifies_chip_id(void) {
    // Simulate chip ID register read
    static uint8_t mock_regs[256];
    mock_regs[CHIP_ID_REG] = EXPECTED_CHIP_ID;
    
    no_os_i2c_read_Stub(stub_i2c_read);
    
    struct driver_dev *dev = NULL;
    struct driver_init_param init = { /* config */ };
    
    int ret = driver_init(&dev, &init);
    
    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_NOT_NULL(dev);
    
    driver_remove(dev);
}
```

## Testing Anti-Patterns (Avoid These)

❌ **Testing implementation details**
```c
// Bad: Testing internal function call order
no_os_i2c_write_ExpectAndReturn(desc, data1, 2, 1, 0);
no_os_i2c_write_ExpectAndReturn(desc, data2, 2, 1, 0);
```

✅ **Testing behavior**
```c
// Good: Testing outcome
no_os_i2c_write_IgnoreAndReturn(0);
int ret = driver_configure(dev);
TEST_ASSERT_EQUAL_INT(0, ret);
```

❌ **Complex test logic**
```c
// Bad: Test has loops and complex logic
for (int i = 0; i < 10; i++) {
    if (i % 2 == 0) {
        // test even case
    } else {
        // test odd case
    }
}
```

✅ **Simple, focused tests**
```c
// Good: Separate tests for each case
void test_even_case(void) { /* ... */ }
void test_odd_case(void) { /* ... */ }
```

❌ **Testing multiple things**
```c
// Bad: Testing init, config, and operation together
void test_driver_complete_flow(void) {
    driver_init(&dev, &init);
    driver_configure(dev, 100);
    driver_start(dev);
    driver_read(dev, &value);
    // If this fails, which part failed?
}
```

✅ **One focus per test**
```c
// Good: Separate tests
void test_driver_init(void) { /* ... */ }
void test_driver_configure(void) { /* ... */ }
void test_driver_start(void) { /* ... */ }
void test_driver_read(void) { /* ... */ }
```

## Summary Checklist

Before considering testing complete, verify:

- ✅ All exported functions have at least one test
- ✅ All pointer parameters tested with NULL
- ✅ All error codes tested (EINVAL, ENODEV, etc.)
- ✅ Range checks tested (min, max, out-of-bounds)
- ✅ Platform failures tested (I2C/SPI errors injected)
- ✅ Coverage ≥80% verified with HTML report
- ✅ All tests pass (100% pass rate)
- ✅ Tests run successfully with `ceedling test:all`
- ✅ Coverage report generated with `ceedling gcov:all`
- ✅ Actual numbers documented (test count, coverage %)

**Quality over quantity** - 100 well-written tests covering error paths are better than 500 tests that only test happy paths.
