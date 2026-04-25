# Unity Assertions Reference

Complete guide to Unity assertion macros for verifying test results in no-OS unit tests.

## Integer Assertions

### Equality

```c
TEST_ASSERT_EQUAL_INT(expected, actual);
TEST_ASSERT_EQUAL_INT8(expected, actual);
TEST_ASSERT_EQUAL_INT16(expected, actual);
TEST_ASSERT_EQUAL_INT32(expected, actual);
TEST_ASSERT_EQUAL_UINT(expected, actual);
TEST_ASSERT_EQUAL_UINT8(expected, actual);
TEST_ASSERT_EQUAL_UINT16(expected, actual);
TEST_ASSERT_EQUAL_UINT32(expected, actual);
```

### Hexadecimal Comparison

Same behavior as EQUAL but formats output in hexadecimal:

```c
TEST_ASSERT_EQUAL_HEX8(0xAB, actual);
TEST_ASSERT_EQUAL_HEX16(0x1234, actual);
TEST_ASSERT_EQUAL_HEX32(0xDEADBEEF, actual);
```

**Use for**: Register values, bitmasks, hardware addresses

### Ranges and Comparisons

```c
TEST_ASSERT_INT_WITHIN(delta, expected, actual);
TEST_ASSERT_GREATER_THAN(threshold, actual);
TEST_ASSERT_LESS_THAN(threshold, actual);
TEST_ASSERT_GREATER_OR_EQUAL(threshold, actual);
TEST_ASSERT_LESS_OR_EQUAL(threshold, actual);
```

## Pointer & NULL Assertions

```c
TEST_ASSERT_NULL(pointer);
TEST_ASSERT_NOT_NULL(pointer);
TEST_ASSERT_EQUAL_PTR(expected, actual);
TEST_ASSERT_NOT_EQUAL_PTR(expected, actual);
```

## Boolean Assertions

```c
TEST_ASSERT_TRUE(condition);
TEST_ASSERT_FALSE(condition);
TEST_ASSERT(condition);  // Alias for TEST_ASSERT_TRUE
```

## Array & Memory Assertions

### Array Comparison

```c
TEST_ASSERT_EQUAL_UINT8_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_UINT16_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_UINT32_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_INT8_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_INT16_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_INT32_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_HEX8_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_HEX16_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_HEX32_ARRAY(expected, actual, num_elements);
```

### Memory Comparison

```c
TEST_ASSERT_EQUAL_MEMORY(expected, actual, num_bytes);
TEST_ASSERT_EQUAL_MEMORY_ARRAY(expected, actual, len, num_elements);
```

## Float & Double Assertions

```c
TEST_ASSERT_EQUAL_FLOAT(expected, actual);
TEST_ASSERT_EQUAL_DOUBLE(expected, actual);
TEST_ASSERT_FLOAT_WITHIN(delta, expected, actual);
TEST_ASSERT_DOUBLE_WITHIN(delta, expected, actual);
```

## String Assertions

```c
TEST_ASSERT_EQUAL_STRING(expected, actual);
TEST_ASSERT_EQUAL_STRING_LEN(expected, actual, length);
TEST_ASSERT_EQUAL_STRING_ARRAY(expected, actual, num_elements);
```

## Custom Messages

All assertions support custom messages via `_MESSAGE` suffix:

```c
TEST_ASSERT_EQUAL_INT_MESSAGE(expected, actual, "Custom error message");
TEST_ASSERT_NOT_NULL_MESSAGE(ptr, "Pointer should not be NULL");
TEST_ASSERT_TRUE_MESSAGE(condition, "Condition should be true");
```

## Assertion Examples

### Error Code Checking

```c
// Success validation
int ret = driver_init(&dev, &init);
TEST_ASSERT_EQUAL_INT(0, ret);

// Error code validation
ret = driver_configure(NULL, 100);
TEST_ASSERT_EQUAL_INT(-EINVAL, ret);

ret = driver_read_value(dev, INVALID_INDEX);
TEST_ASSERT_EQUAL_INT(-ENODEV, ret);
```

### Pointer Validation

```c
// Device creation
struct driver_dev *dev = NULL;
int ret = driver_init(&dev, &init);
TEST_ASSERT_EQUAL_INT(0, ret);
TEST_ASSERT_NOT_NULL(dev);
TEST_ASSERT_NOT_NULL(dev->i2c_desc);

// NULL parameter handling
ret = driver_configure(NULL, 100);
TEST_ASSERT_EQUAL_INT(-ENODEV, ret);

// Optional features
TEST_ASSERT_NULL(dev->optional_callback);
```

### Register Value Verification

```c
// Read register and verify value
uint8_t reg_value = 0;
int ret = driver_read_register(dev, REG_ADDR, &reg_value);
TEST_ASSERT_EQUAL_INT(0, ret);
TEST_ASSERT_EQUAL_HEX8(0xAB, reg_value);

// Verify bitmask
uint16_t control_reg = 0x1234;
TEST_ASSERT_EQUAL_HEX16(0x1234, control_reg);

// Verify bit field
uint8_t status = 0x05;
TEST_ASSERT_TRUE(status & STATUS_READY);
TEST_ASSERT_FALSE(status & STATUS_ERROR);
```

### Array and Buffer Checking

```c
// Verify data buffer
uint8_t expected[] = {0x01, 0x02, 0x03, 0x04};
uint8_t actual[4];
int ret = driver_read_buffer(dev, actual, 4);
TEST_ASSERT_EQUAL_INT(0, ret);
TEST_ASSERT_EQUAL_UINT8_ARRAY(expected, actual, 4);

// Verify hex array
uint8_t reg_values[] = {0xAB, 0xCD, 0xEF};
uint8_t read_values[3];
driver_read_registers(dev, read_values, 3);
TEST_ASSERT_EQUAL_HEX8_ARRAY(reg_values, read_values, 3);
```

### Range Validation

```c
// Voltage within tolerance
int voltage_mv = 1250;
TEST_ASSERT_INT_WITHIN(10, 1250, voltage_mv);  // 1240-1260 accepted

// Temperature range
int temp_c = 25;
TEST_ASSERT_GREATER_THAN(0, temp_c);
TEST_ASSERT_LESS_THAN(100, temp_c);

// ADC value bounds
uint16_t adc_value = 2048;
TEST_ASSERT_GREATER_OR_EQUAL(0, adc_value);
TEST_ASSERT_LESS_OR_EQUAL(4095, adc_value);
```

### Float and Voltage Validation

```c
// Voltage measurement
float voltage_v = 3.3f;
TEST_ASSERT_FLOAT_WITHIN(0.1f, 3.3f, voltage_v);

// Current measurement (within 1mA)
float current_a = 0.150f;
TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.150f, current_a);

// Exact float comparison (avoid if possible due to precision)
TEST_ASSERT_EQUAL_FLOAT(3.3f, voltage_v);
```

### Memory Comparison

```c
// Verify structure contents
struct config expected_config = {
    .mode = MODE_FAST,
    .threshold = 100,
    .enable = true
};

struct config actual_config;
driver_get_config(dev, &actual_config);
TEST_ASSERT_EQUAL_MEMORY(&expected_config, &actual_config, sizeof(struct config));
```

## Common Patterns

### Pattern 1: Init Function Validation

```c
void test_driver_init_success(void) {
    struct driver_dev *dev = NULL;
    struct driver_init_param init = { /* valid config */ };
    
    int ret = driver_init(&dev, &init);
    
    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_NOT_NULL(dev);
    TEST_ASSERT_NOT_NULL(dev->i2c_desc);
    
    driver_remove(dev);
}
```

### Pattern 2: NULL Parameter Checking

```c
void test_driver_init_null_device_pointer(void) {
    struct driver_init_param init = { /* valid config */ };
    
    int ret = driver_init(NULL, &init);
    
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}

void test_driver_init_null_param(void) {
    struct driver_dev *dev = NULL;
    
    int ret = driver_init(&dev, NULL);
    
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
    TEST_ASSERT_NULL(dev);
}
```

### Pattern 3: Range Validation

```c
void test_driver_set_voltage_out_of_range(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    
    // Test below minimum
    int ret = driver_set_voltage(test_dev, -100);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
    
    // Test above maximum
    ret = driver_set_voltage(test_dev, 10000);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}
```

### Pattern 4: Register Read/Write Verification

```c
void test_driver_read_register(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    
    uint8_t expected_value = 0xAB;
    
    // Configure mock to return expected value
    no_os_i2c_read_Stub(mock_i2c_read_callback);
    
    uint8_t actual_value = 0;
    int ret = driver_read_register(test_dev, REG_STATUS, &actual_value);
    
    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_HEX8(expected_value, actual_value);
}
```

### Pattern 5: Error Injection

```c
void test_driver_init_i2c_failure(void) {
    struct driver_dev *dev = NULL;
    struct driver_init_param init = { /* valid config */ };
    
    // Override default mock behavior to inject I2C error
    no_os_i2c_init_IgnoreAndReturn(-EIO);
    
    int ret = driver_init(&dev, &init);
    
    TEST_ASSERT_EQUAL_INT(-EIO, ret);
    TEST_ASSERT_NULL(dev);
}
```

## Best Practices

1. **Use specific assertions**: `TEST_ASSERT_EQUAL_HEX8` for registers, not `TEST_ASSERT_EQUAL_INT`
2. **Add custom messages**: Use `_MESSAGE` variants for complex tests
3. **Check return codes**: Always validate error codes, not just success
4. **Verify all outputs**: Check both return value and output parameters
5. **Test NULL safety**: Every pointer parameter should have NULL test
6. **Use ranges for floats**: Use `WITHIN` for floating-point comparisons
7. **Test boundaries**: Min, max, and out-of-range values
8. **One assertion focus**: Each test should focus on one behavior

## Common Mistakes

- **Swapped expected/actual**: Unity convention is `(expected, actual)`, not `(actual, expected)`
- **Using EQUAL_INT for hex**: Use `EQUAL_HEX8` for register values (better output formatting)
- **Exact float comparison**: Use `FLOAT_WITHIN` instead of `EQUAL_FLOAT` due to precision
- **Forgetting cleanup**: Always free resources in tearDown or end of test
- **Testing multiple things**: Keep tests focused on one behavior
- **Missing error cases**: Don't forget to test failure paths

## Summary

Unity assertions provide comprehensive validation capabilities for embedded driver testing:

- **Type-safe comparisons**: Specific assertions for integers, floats, pointers, arrays
- **Clear failure messages**: Automatic formatting shows expected vs actual values
- **Flexible validation**: Ranges, bounds, memory comparison, custom messages
- **Error handling**: Validate error codes and edge cases
- **Array support**: Verify data buffers and register sequences

Use the right assertion for each validation to get clear, informative test failures that guide debugging.
