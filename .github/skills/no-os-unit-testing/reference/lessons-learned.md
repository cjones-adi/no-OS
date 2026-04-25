# Lessons Learned from AD7606 Unit Testing

Real-world lessons from creating unit tests for complex drivers.

---

## **CRITICAL: Testing Complex Init Functions**

### Pattern: Provide Real Implementations Instead of Mocking

**Problem**: Complex init functions with many internal calls cause "Function called more times than expected" errors with CMock.

**Example Error**:
```
Test: test_driver_init_success
At line (264): "Function no_os_calloc. Called more times than expected."
```

**Why CMock Fails**:
Init functions often call helper functions internally:
```c
int32_t driver_init(struct driver_dev **device, struct init_param *params) {
    dev = no_os_calloc(1, sizeof(*dev));  // Call #1
    dev->config = no_os_calloc(1, sizeof(*config));  // Call #2
    dev->ranges = no_os_calloc(8, sizeof(*ranges));  // Call #3

    // ... 20+ more function calls internally ...

    no_os_field_get(MASK, reg);  // Multiple calls
    no_os_field_prep(MASK, val);  // Multiple calls
    no_os_spi_init(&dev->spi, &params->spi);
}
```

CMock tracks call counts even with `_StubWithCallback()`, causing failures when functions are called multiple times.

**✅ SOLUTION: Provide Real Implementations**

Instead of mocking simple utility functions, provide simple real implementations in your test file:

```c
/******************************************************************************/
/*********************** Real no_os_alloc Implementation **********************/
/******************************************************************************/

/* Global flag to simulate allocation failure when needed */
static bool simulate_alloc_failure = false;

void *no_os_calloc(size_t nmemb, size_t size)
{
    if (simulate_alloc_failure)
        return NULL;
    return calloc(nmemb, size);
}

void no_os_free(void *ptr)
{
    free(ptr);
}

/******************************************************************************/
/*********************** Real no_os_util Implementation **********************/
/******************************************************************************/

uint32_t no_os_field_get(uint32_t mask, uint32_t word)
{
    uint32_t shift = 0, temp = mask;
    while (temp && !(temp & 1)) {
        shift++;
        temp >>= 1;
    }
    return (word & mask) >> shift;
}

uint32_t no_os_field_prep(uint32_t mask, uint32_t val)
{
    uint32_t shift = 0, temp = mask;
    while (temp && !(temp & 1)) {
        shift++;
        temp >>= 1;
    }
    return (val << shift) & mask;
}

int32_t no_os_sign_extend32(uint32_t value, int index)
{
    uint8_t shift = 31 - index;
    return (int32_t)(value << shift) >> shift;
}

/******************************************************************************/
/*********************** Real no_os_spi Implementation ************************/
/******************************************************************************/

/* Global control flags */
static int  simulate_spi_init_error = 0;  /* 0=success, else error code */
static uint8_t stub_reg_values[256];
static int stub_spi_return = 0;

int32_t no_os_spi_init(struct no_os_spi_desc **desc,
                       const struct no_os_spi_init_param *param)
{
    if (simulate_spi_init_error)
        return simulate_spi_init_error;

    if (desc) {
        static struct no_os_spi_desc mock_desc;
        *desc = &mock_desc;
    }
    return 0;
}

int32_t no_os_spi_remove(struct no_os_spi_desc *desc)
{
    return 0;
}

int32_t no_os_spi_write_and_read(struct no_os_spi_desc *desc,
                                 uint8_t *data, uint16_t bytes_number)
{
    if (data && bytes_number >= 2) {
        /* Simulate register access */
        if (data[0] & 0x40) {  /* Read operation */
            uint8_t reg_addr = data[0] & 0x3F;
            data[1] = stub_reg_values[reg_addr];
        }
    }
    return stub_spi_return;
}
```

**Test File Header - Don't Mock These**:
```c
#include "unity.h"
#include "driver.h"
/* DON'T mock alloc, util, or spi - we provide real implementations */
/* #include "mock_no_os_alloc.h" */
/* #include "mock_no_os_util.h" */
/* #include "mock_no_os_spi.h" */
#include "mock_no_os_gpio.h"
#include "mock_no_os_delay.h"
#include "mock_no_os_crc8.h"
```

**Using the Real Implementations in Tests**:

```c
void setUp(void) {
    /* Reset simulation flags */
    simulate_alloc_failure = false;
    simulate_spi_init_error = 0;
    memset(stub_reg_values, 0, sizeof(stub_reg_values));
    stub_spi_return = 0;

    /* Only mock GPIO, delay, CRC */
    no_os_gpio_get_optional_IgnoreAndReturn(0);
    no_os_gpio_direction_output_IgnoreAndReturn(0);
    no_os_gpio_set_value_IgnoreAndReturn(0);
    no_os_mdelay_Ignore();no_os_udelay_Ignore();
    no_os_crc8_populate_msb_Ignore();
    no_os_crc16_populate_msb_Ignore();
}

void test_driver_init_success(void) {
    struct driver_dev *dev = NULL;
    struct init_param params = {...};

    /* Set register values for ID check */
    stub_reg_values[REG_ID] = 0x10;  /* Expected device ID */

    int ret = driver_init(&dev, &params);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_NOT_NULL(dev);
}

void test_driver_init_alloc_failure(void) {
    struct driver_dev *dev = NULL;
    struct init_param params = {...};

    /* Simulate allocation failure */
    simulate_alloc_failure = true;

    int ret = driver_init(&dev, &params);

    TEST_ASSERT_EQUAL_INT(-ENOMEM, ret);
    TEST_ASSERT_NULL(dev);
}

void test_driver_init_spi_failure(void) {
    struct driver_dev *dev = NULL;
    struct init_param params = {...};

    /* Simulate SPI init failure */
    simulate_spi_init_error = -EIO;

    int ret = driver_init(&dev, &params);

    TEST_ASSERT_EQUAL_INT(-EIO, ret);
}
```

**Key Benefits**:
1. ✅ No CMock call counting issues
2. ✅ Simple utility functions behave correctly
3. ✅ Can still inject failures via global flags
4. ✅ Tests are more readable
5. ✅ Works for complex multi-call scenarios

**When to Use This Pattern**:
- Init functions with 20+ internal calls
- Functions that allocate memory multiple times
- Functions using field_get/field_prep repeatedly
- Complex SPI/I2C transaction sequences

**Decision Matrix**:

| Function Complexity | Mock or Real |
|---------------------|--------------|
| Simple utility (field_get, field_prep) | **Real implementation** |
| Memory allocation (calloc, free) | **Real implementation** |
| SPI/I2C for complex drivers | **Real implementation with control flags** |
| GPIO (varies by test) | **Mock - behavior changes per test** |
| Delay (udelay, mdelay) | **Mock - no side effects** |
| CRC | **Mock - complex internal state** |

**Real-World Results**:
- AD7606 driver: 82/82 tests passing (was 78/82 with mocks)
- Coverage: 53% (up from 42% with mock issues)
- Init tests: 4/4 passing (were all failing with CMock)
- Build time: No change
- Test maintainability: Much better

---

## Critical Mock Configuration Issues

### Issue 1: CRC Functions Must Be Mocked

**Problem**: Drivers using CRC functions fail to link without proper mocking.

**Symptoms**:
```
collect2.exe: error: ld returned 1 exit status
undefined reference to `no_os_crc8_populate_msb`
undefined reference to `no_os_crc16`
```

**Solution**: When driver uses CRC, add to `project.yml`:
```yaml
:test_driver_name:
  :includes:
    - no_os_spi.h
    - no_os_gpio.h
    - no_os_util.h
    - no_os_crc8.h      # Add CRC headers
    - no_os_crc16.h
```

**Test file includes**:
```c
#include "mock_no_os_crc8.h"
#include "mock_no_os_crc16.h"
```

**setUp() configuration**:
```c
void setUp(void) {
    /* CRC function mocks */
    no_os_crc8_populate_msb_Ignore();
    no_os_crc8_IgnoreAndReturn(0);
    no_os_crc16_populate_msb_Ignore();
    no_os_crc16_IgnoreAndReturn(0);
}
```

---

### Issue 2: Calloc Must Actually Allocate Memory

**Problem**: Using `no_os_calloc_IgnoreAndReturn(NULL)` by default breaks initialization tests.

**Wrong Approach**:
```c
void setUp(void) {
    /* This breaks most tests! */
    no_os_calloc_IgnoreAndReturn(NULL);
}
```

**Correct Approach**: Use stub that actually allocates:
```c
static void *stub_calloc(size_t nmemb, size_t size, int cmock_num_calls)
{
    return calloc(nmemb, size);
}

void setUp(void) {
    /* Use real allocation by default */
    no_os_calloc_StubWithCallback(stub_calloc);
    no_os_free_Ignore();
}
```

**Why**: Most driver functions need actual memory allocation to function. Only override in specific failure tests:
```c
void test_driver_init_calloc_failure(void) {
    /* Override just for this test */
    no_os_calloc_IgnoreAndReturn(NULL);

    int ret = driver_init(&dev, &init_param);
    TEST_ASSERT_EQUAL_INT(-ENOMEM, ret);
}
```

---

### Issue 3: Utility Functions Need Complete Mocking

**Problem**: Missing utility function mocks cause undefined references.

**Common Missing Mocks**:
```c
void setUp(void) {
    /* Always mock these utility functions */
    no_os_field_prep_IgnoreAndReturn(0);
    no_os_field_get_IgnoreAndReturn(0);
    no_os_sign_extend32_IgnoreAndReturn(0);  // Often forgotten!
}
```

**How to Find**: Check linker errors for undefined references:
```bash
nm build/test/out/test_driver/driver.o | grep " U "
```

---

## Project.yml Configuration Lessons

### Lesson 1: Explicit Source Files > Wildcards

**Problem**: Using `../../../../util/*.c` doesn't always compile what you need.

**Better Approach**:
```yaml
:files:
  :source:
    - ../../../../drivers/category/driver/driver.c
    - +:../../../../util/no_os_crc8.c
    - +:../../../../util/no_os_crc16.c
```

**Why**: Explicit file lists are clearer and more reliable than wildcards.

---

### Lesson 2: Include Paths for Utility Files

**Problem**: CRC headers not found during compilation.

**Solution**: Add util to include paths:
```yaml
:paths:
  :include:
    - ../../../../include
    - ../../../../drivers/category/driver
    - ../../../../util          # Add this!
```

---

## Test Organization Patterns

### Pattern 1: Mock Device Helper Function

**Standard Pattern**:
```c
static struct driver_dev *test_dev = NULL;

static int create_mock_device(void)
{
    test_dev = calloc(1, sizeof(struct driver_dev));
    if (!test_dev)
        return -ENOMEM;

    test_dev->i2c_desc = calloc(1, sizeof(struct no_os_i2c_desc));
    if (!test_dev->i2c_desc) {
        free(test_dev);
        test_dev = NULL;
        return -ENOMEM;
    }

    /* Set minimal valid defaults */
    test_dev->device_id = ID_DEVICE;
    test_dev->num_channels = 8;

    return 0;
}
```

**Usage in Tests**:
```c
void test_driver_operation(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());

    /* Now test_dev is ready to use */
    int ret = driver_operation(test_dev);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

---

### Pattern 2: Complex Drivers Need Multiple Test Files

**Single vs Multiple Files**:

**Small Driver (< 20 functions)**: One file
```
test/
└── test_driver.c          # All tests
```

**Large Driver (20+ functions)**: Split by functionality
```
test/
├── test_driver_core.c         # Init, remove, register access
├── test_driver_operations.c   # Data acquisition, conversions
└── test_driver_calibration.c  # Calibration, configuration
```

**Benefits**:
- Faster compilation (parallel builds)
- Better organization
- Easier to navigate
- Can run specific tests: `ceedling test:test_driver_core`

---

## Debugging Failing Tests

### Debug Technique 1: Run Single Test

```bash
# Run just one test file
ceedling test:test_driver_core

# With verbose output
ceedling test:test_driver_core --verbosity=obnoxious
```

### Debug Technique 2: Check Undefined Symbols

```bash
# Build test
ceedling test:test_driver_core

# Check undefined references
nm build/test/out/test_driver_core/driver.o | grep " U "
```

**Common Issues**:
- Missing CRC mocks
- Missing utility function mocks
- Missing platform API mocks

---

### Debug Technique 3: Manual Linking to See Errors

```bash
# Try linking manually
gcc build/test/out/test_driver/*.o -o test.out -lm 2>&1
```

**Reveals**:
- Missing object files
- Duplicate symbols
- Undefined references

---

## Quick Checklist for New Driver Tests

### Before Starting
- [ ] Check if driver uses CRC (grep for `crc` in driver.c)
- [ ] List all `no_os_*` includes in driver.c
- [ ] Copy project.yml from working example (max20362 or max20370)

### project.yml Configuration
- [ ] All source files explicitly listed
- [ ] All platform headers in `:includes:` section
- [ ] CRC headers added if driver uses CRC
- [ ] util/ in include paths if using CRC

### Test File Setup
- [ ] Include all `mock_*.h` files
- [ ] Create `stub_calloc()` function
- [ ] setUp() uses `no_os_calloc_StubWithCallback(stub_calloc)`
- [ ] setUp() mocks all utility functions (field_prep, field_get, sign_extend32)
- [ ] setUp() mocks CRC functions if needed
- [ ] Create `create_mock_device()` helper

### Running Tests
- [ ] `ceedling test:all` compiles without errors
- [ ] At least some tests pass (target 50%+ initial)
- [ ] `ceedling gcov:all` generates coverage report
- [ ] Coverage HTML report opens successfully

---

## Common Error Messages and Fixes

### "Function no_os_calloc. Called more times than expected"

**Fix**: Use `stub_calloc` in setUp():
```c
no_os_calloc_StubWithCallback(stub_calloc);
```

### "undefined reference to `no_os_crc8`"

**Fix**: Add to project.yml `:includes:`:
```yaml
- no_os_crc8.h
- no_os_crc16.h
```

### "Test case crashed"

**Causes**:
1. NULL pointer dereference
2. Missing mock setup
3. Accessing uninitialized memory

**Debug**:
```bash
# Run with gdb (if configured)
ceedling test:testfile --verbosity=obnoxious

# Or add debug output in test
printf("Debug: test_dev = %p\n", test_dev);
```

### "Unity Double Precision Disabled"

**Meaning**: Can't use `TEST_ASSERT_DOUBLE_WITHIN()` assertions.

**Fix**: Use integer comparisons or enable double precision in project.yml (usually not needed).

---

## Coverage-Driven Testing Strategy

### Initial Test Development (Target: 50-60%)

**Focus**: Core functionality
1. Init tests (success + all error paths)
2. Remove/cleanup tests
3. Basic operation tests
4. NULL pointer tests

**Don't**: Try to test everything upfront

---

### Iteration 1 (Target: 70%)

**Focus**: Error handling
1. Run `ceedling gcov:all`
2. Open HTML report
3. Find red lines (not covered)
4. Add tests for error paths

**Common Red Lines**:
- Error return paths
- Edge case validation
- Cleanup after failures

---

### Iteration 2 (Target: 80%+)

**Focus**: Branch coverage
1. Identify yellow lines (partial coverage)
2. Test both branches of conditionals
3. Test all switch/case statements
4. Test boundary conditions

**Stop When**: 80-85% coverage achieved (industry standard)

---

## Key Takeaways

1. **Always use stub_calloc in setUp()** - Don't IgnoreAndReturn(NULL)
2. **Mock CRC functions** - If driver uses CRC, add crc8/crc16 mocks
3. **Mock all utility functions** - field_prep, field_get, sign_extend32
4. **Split large drivers** - Multiple test files for organization
5. **Copy working templates** - Use max20362/max20370 as reference
6. **Iterate to 80%** - Don't chase 100% coverage
7. **Debug systematically** - Check undefined symbols, run single tests
8. **Test error paths** - These are usually the red lines in coverage

---

## Template: Minimal Working setUp()

```c
/**
 * @brief Stub for calloc - allocates memory
 */
static void *stub_calloc(size_t nmemb, size_t size, int cmock_num_calls)
{
    return calloc(nmemb, size);
}

void setUp(void)
{
    test_dev = NULL;

    /* Platform API mocks - ignore and succeed */
    no_os_spi_init_IgnoreAndReturn(0);
    no_os_spi_write_and_read_IgnoreAndReturn(0);
    no_os_spi_remove_IgnoreAndReturn(0);

    no_os_i2c_init_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_read_IgnoreAndReturn(0);
    no_os_i2c_remove_IgnoreAndReturn(0);

    no_os_gpio_get_IgnoreAndReturn(0);
    no_os_gpio_get_optional_IgnoreAndReturn(0);
    no_os_gpio_direction_output_IgnoreAndReturn(0);
    no_os_gpio_set_value_IgnoreAndReturn(0);
    no_os_gpio_remove_IgnoreAndReturn(0);

    no_os_delay_Ignore();
    no_os_mdelay_Ignore();
    no_os_udelay_Ignore();

    /* Utility function mocks */
    no_os_field_prep_IgnoreAndReturn(0);
    no_os_field_get_IgnoreAndReturn(0);
    no_os_sign_extend32_IgnoreAndReturn(0);

    /* CRC mocks (if driver uses CRC) */
    no_os_crc8_populate_msb_Ignore();
    no_os_crc8_IgnoreAndReturn(0);
    no_os_crc16_populate_msb_Ignore();
    no_os_crc16_IgnoreAndReturn(0);

    /* Memory allocation - use real allocation! */
    no_os_calloc_StubWithCallback(stub_calloc);
    no_os_free_Ignore();
}
```

This template works for most no-OS drivers. Adjust based on which APIs your driver actually uses.
