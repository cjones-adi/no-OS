# CMock Mocking Strategy Guide

Complete guide to mocking hardware abstraction layers for no-OS driver unit testing using CMock.

## Why Mocking is Essential

**Problem**: no-OS drivers interact with hardware through platform APIs (I2C, SPI, GPIO, IRQ, delays). You cannot run unit tests on real hardware because tests run on development machine, hardware may not be available, and you cannot simulate error conditions.

**Solution**: Mock the hardware abstraction layer

```
Driver Under Test (max20370.c)
    ↓ Calls platform APIs
Hardware Abstraction Layer (no_os_i2c_*, no_os_spi_*)
    ↓
Production: Physical I2C Hardware
Unit Tests: mock_no_os_i2c.c (CMock generated, simulated)
```

## Platform APIs to Mock

| API Category | Functions |
|--------------|-----------|
| **I2C** | `no_os_i2c_init`, `no_os_i2c_write`, `no_os_i2c_read`, `no_os_i2c_remove` |
| **SPI** | `no_os_spi_init`, `no_os_spi_write_and_read`, `no_os_spi_remove` |
| **GPIO** | `no_os_gpio_get`, `no_os_gpio_set_value`, `no_os_gpio_get_value`, `no_os_gpio_remove` |
| **IRQ** | `no_os_irq_register_callback`, `no_os_irq_enable`, `no_os_irq_disable` |
| **Delay** | `no_os_mdelay`, `no_os_udelay` |
| **Memory** | `no_os_calloc`, `no_os_malloc`, `no_os_free` |
| **Utilities** | `no_os_field_prep`, `no_os_field_get` |

## CMock: Automatic Mock Generation

CMock parses C header files and generates mock implementations automatically.

**Input**: `include/no_os_i2c.h`
```c
int32_t no_os_i2c_write(struct no_os_i2c_desc *desc,
                        uint8_t *data,
                        uint8_t bytes_number,
                        uint8_t stop_bit);
```

**Output**: `mock_no_os_i2c.c/h` with auto-generated functions:
```c
void no_os_i2c_write_ExpectAndReturn(/* params */, int32_t retval);
void no_os_i2c_write_IgnoreAndReturn(int32_t retval);
void no_os_i2c_write_Stub(CMOCK_no_os_i2c_write_CALLBACK callback);
```

**Configuration** in `project.yml`:
```yaml
:cmock:
  :mock_prefix: mock_
  :when_no_prototypes: :warn
  :enforce_strict_ordering: false
  :plugins:
    - :ignore      # Enable _Ignore functions
    - :callback    # Enable _Stub functions
```

**Generation**: Automatic when running `ceedling test:driver_name`. Mocks generated from headers listed in `project.yml` `:includes:` section.

## CMock Mock Functions (3 Types)

### 1. IgnoreAndReturn (Most Common - 95% of cases)

**Pattern**: `function_IgnoreAndReturn(return_value)`

```c
void setUp(void) {
    // Default "success" behavior - all platform calls succeed
    no_os_i2c_init_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_read_IgnoreAndReturn(0);
    no_os_gpio_set_value_IgnoreAndReturn(0);
}
```

**Use for**: Default happy-path behavior, tests focusing on driver logic

### 2. ExpectAndReturn (Strict Validation - rarely needed)

**Pattern**: `function_ExpectAndReturn(exact_params..., return_value)`

```c
// Expect EXACT call with EXACT parameters
no_os_i2c_write_ExpectAndReturn(test_dev->i2c_desc, expected_data, 2, 1, 0);
```

**Use for**: When you must verify exact parameters passed to platform API

### 3. Stub (Hardware Simulation - when needed)

**Pattern**: `function_Stub(callback_function)`

```c
static int32_t stub_i2c_read(struct no_os_i2c_desc *desc, uint8_t *data,
                             uint8_t bytes_number, uint8_t stop_bit,
                             int cmock_num_calls)
{
    // Custom implementation - simulate hardware behavior
    data[0] = mock_registers[data[0]];  // Return register value
    return 0;
}

void test_driver_read_chip_id(void) {
    mock_registers[0x00] = 0x12;  // Chip ID
    no_os_i2c_read_Stub(stub_i2c_read);
    
    uint8_t chip_id;
    int ret = driver_read_chip_id(test_dev, &chip_id);
    TEST_ASSERT_EQUAL_HEX8(0x12, chip_id);
}
```

**Use for**: Simulating register maps, chip IDs, sensor readings, hardware state

## Common Mock Patterns

### Pattern 1: Default Success in setUp() (Use This!)

```c
void setUp(void) {
    test_dev = NULL;
    no_os_i2c_init_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_read_IgnoreAndReturn(0);
    no_os_i2c_remove_IgnoreAndReturn(0);
}

void test_driver_init_success(void) {
    // No mock configuration needed - uses defaults
    int ret = driver_init(&dev, &init);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

### Pattern 2: Override for Error Testing

```c
void test_driver_init_i2c_failure(void) {
    // Override default success
    no_os_i2c_init_IgnoreAndReturn(-EIO);
    
    int ret = driver_init(&dev, &init);
    TEST_ASSERT_EQUAL_INT(-EIO, ret);
    TEST_ASSERT_NULL(dev);
}
```

### Pattern 3: Stub for Register Simulation

```c
static uint8_t mock_regs[256];

static int32_t stub_spi_rw(struct no_os_spi_desc *desc, uint8_t *data,
                           uint16_t bytes, int cmock_num_calls)
{
    uint8_t addr = data[0] & 0x7F;
    if (data[0] & 0x80) {  // Read
        data[1] = mock_regs[addr];
    } else {  // Write
        mock_regs[addr] = data[1];
    }
    return 0;
}

void test_driver_register_ops(void) {
    no_os_spi_write_and_read_Stub(stub_spi_rw);
    mock_regs[0x10] = 0xAB;
    
    uint8_t value;
    driver_read_register(test_dev, 0x10, &value);
    TEST_ASSERT_EQUAL_HEX8(0xAB, value);
}
```

### Pattern 4: Error Injection Sequence

```c
void test_driver_partial_failure(void) {
    // First 3 calls succeed, 4th fails
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(-EIO);
    
    int ret = driver_write_sequence(test_dev);
    TEST_ASSERT_EQUAL_INT(-EIO, ret);
}
```

### Pattern 5: State Machine Simulation

```c
static int32_t stub_read_status(struct no_os_i2c_desc *desc, uint8_t *data,
                                uint8_t bytes, uint8_t stop, int cmock_num_calls)
{
    // Simulate state progression: busy → busy → ready
    data[0] = (cmock_num_calls < 2) ? STATE_BUSY : STATE_READY;
    return 0;
}

void test_driver_wait_for_ready(void) {
    no_os_i2c_read_Stub(stub_read_status);
    int ret = driver_wait_until_ready(test_dev);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

## Complete I2C Register Map Example

```c
static uint8_t mock_i2c_regs[256];
static uint8_t mock_last_reg_addr = 0;

static int32_t stub_i2c_write(struct no_os_i2c_desc *desc, uint8_t *data,
                              uint8_t bytes, uint8_t stop, int cmock_num_calls)
{
    if (bytes == 1) {
        mock_last_reg_addr = data[0];  // Set register address
    } else if (bytes == 2) {
        mock_i2c_regs[data[0]] = data[1];  // Write register
    }
    return 0;
}

static int32_t stub_i2c_read(struct no_os_i2c_desc *desc, uint8_t *data,
                             uint8_t bytes, uint8_t stop, int cmock_num_calls)
{
    data[0] = mock_i2c_regs[mock_last_reg_addr];  // Read register
    return 0;
}

void test_driver_register_access(void) {
    no_os_i2c_write_Stub(stub_i2c_write);
    no_os_i2c_read_Stub(stub_i2c_read);
    
    // Test write
    driver_write_register(test_dev, 0x10, 0xAB);
    TEST_ASSERT_EQUAL_HEX8(0xAB, mock_i2c_regs[0x10]);
    
    // Test read
    uint8_t value;
    driver_read_register(test_dev, 0x10, &value);
    TEST_ASSERT_EQUAL_HEX8(0xAB, value);
}
```

## Best Practices

1. **Default to IgnoreAndReturn in setUp()** - Simplifies 95% of tests
2. **Use Stub for register simulation** - More realistic than ExpectAndReturn
3. **Use Expect sparingly** - Only when exact validation needed (rarely)
4. **Reset mock state in setUp()** - Ensure test isolation
5. **Test error paths** - Override success defaults to inject errors
6. **Keep stubs simple** - Complex logic indicates test doing too much

## Common Mistakes

- **Forgetting to configure mocks in setUp()** → Tests fail with "unexpected call" errors
- **Using Expect instead of Ignore** → Brittle tests that break on implementation changes
- **Not resetting mock state** → Tests depend on execution order
- **Complex stub logic** → Tests become hard to understand
- **Not testing error paths** → Missing coverage of failure handling

## Summary

**Three Mock Types**:
- **IgnoreAndReturn**: Use for 95% of cases (default behavior)
- **Stub**: Use for hardware simulation (register maps, state)
- **ExpectAndReturn**: Use rarely (strict parameter validation)

**Workflow**:
1. Configure default success in setUp() with IgnoreAndReturn
2. Override in specific tests for error injection
3. Use Stub when simulating hardware behavior (registers, chip ID)
4. Keep tests simple and focused on driver logic
