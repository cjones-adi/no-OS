---
name: testing-strategies
description: 'Cross-platform testing strategies for embedded driver development. Use when planning test approaches, implementing unit/integration/HIL testing, setting coverage goals, testing across no-OS/Linux/Zephyr platforms, validating driver functionality, or establishing testing workflows.'
---

# Testing Strategies for Embedded Driver Development

## When to Use This Skill

Use this skill when you need to:
- Plan a comprehensive testing strategy for a new driver
- Choose appropriate testing methods (unit, integration, HIL)
- Set coverage goals and acceptance criteria
- Design test cases for driver functionality
- Implement cross-platform testing (no-OS, Linux, Zephyr)
- Validate hardware communication (SPI, I2C, UART)
- Test error handling and edge cases
- Establish CI/CD testing workflows
- Debug failing tests
- Balance testing depth vs. development time

## Overview

Effective embedded driver testing requires a **multi-layered approach**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Testing Pyramid                          │
└─────────────────────────────────────────────────────────────┘

                         ▲
                        ╱ ╲
                       ╱   ╲      Manual Testing
                      ╱─────╲     • Final validation
                     ╱       ╲    • Integration with full system
                    ╱─────────╲   • Real hardware verification
                   ╱           ╲
                  ╱─────────────╲  Hardware-in-Loop (HIL)
                 ╱               ╲ • Automated on real hardware
                ╱─────────────────╲• Device communication tests
               ╱                   ╲• Timing and signal validation
              ╱─────────────────────╲
             ╱                       ╲ Integration Tests
            ╱─────────────────────────╲• Driver + platform APIs
           ╱                           ╲• End-to-end scenarios
          ╱─────────────────────────────╲• Cross-layer validation
         ╱                               ╲
        ╱─────────────────────────────────╲ Unit Tests (Base)
       ╱                                   ╲• Fast, isolated
      ╱                                     ╲• Mocked hardware
     ╱                                       ╲• 80%+ coverage
    ╱─────────────────────────────────────────╲• Automated
   ──────────────────────────────────────────────
         Most Tests               Fewest Tests
         Fastest                  Slowest
         Cheapest                 Most Expensive
```

**Key Principle**: More unit tests, fewer integration tests, minimal manual testing.

---

## Testing Layers

### 1. Unit Testing (Foundation)

**Purpose**: Test driver logic in isolation with mocked hardware.

**Characteristics**:
- ✅ **Fast**: Runs in milliseconds
- ✅ **Isolated**: No hardware required
- ✅ **Repeatable**: Same result every time
- ✅ **Comprehensive**: Test error paths easily
- ✅ **Automated**: Part of CI/CD pipeline

**What to Test**:
- Initialization sequences
- Register read/write logic
- Configuration functions
- Data conversion and calculations
- Error handling and validation
- State machine transitions
- API contract compliance

**Frameworks by Platform**:
- **no-OS**: Ceedling + Unity + CMock + gcov
- **Linux**: KUnit (kernel) or CUnit/Check (userspace)
- **Zephyr**: Ztest framework

**Coverage Goal**: **80%+ line coverage** minimum

**When to Use**: Every driver should have unit tests.

---

### 2. Integration Testing (Middle Layer)

**Purpose**: Test driver interaction with real platform APIs and other subsystems.

**Characteristics**:
- ⚠️ **Slower**: May require hardware or emulation
- ⚠️ **Dependent**: Relies on platform initialization
- ✅ **Realistic**: Tests actual integration points
- ✅ **End-to-end**: Validates complete scenarios

**What to Test**:
- Driver + platform driver (SPI, I2C, GPIO) integration
- Multi-device scenarios (shared bus)
- Interrupt handling with real IRQ controller
- DMA transfers
- IIO subsystem integration (no-OS, Linux)
- Devicetree/Kconfig integration (Zephyr, Linux)
- Example application workflows

**Approaches**:
1. **QEMU/Emulation**: Run on virtual hardware
2. **Real Hardware**: Deploy to eval board
3. **Semi-automated**: Scripts drive hardware tests

**Coverage Goal**: Key integration paths (not 100%)

**When to Use**: After unit tests pass, before hardware validation.

---

### 3. Hardware-in-Loop (HIL) Testing (Top Layer)

**Purpose**: Validate driver behavior on actual hardware with real signals.

**Characteristics**:
- ❌ **Slowest**: Real-time hardware operation
- ❌ **Expensive**: Requires hardware setup
- ✅ **Definitive**: Proves actual functionality
- ✅ **Signal-level**: Validates timing, electrical specs

**What to Test**:
- Product ID detection
- SPI/I2C communication with actual device
- ADC/DAC conversion accuracy
- Timing requirements (setup, hold, conversion time)
- Interrupt latency
- Power modes and transitions
- Thermal behavior

**Test Equipment**:
- Logic analyzer (verify SPI/I2C signals)
- Oscilloscope (check timing, analog signals)
- Multimeter (verify voltage levels)
- Signal generator (provide test inputs)
- Power supply (test voltage ranges)

**Automation Options**:
1. **Test harness**: Script-based automation
2. **IIO tools**: `iio_info`, `iio_attr`, `iio_readdev`
3. **Custom scripts**: Python/Bash for automated testing

**When to Use**: Final validation before release, regression testing.

---

## Platform-Specific Testing Approaches

### no-OS Testing Strategy

**Unit Testing** (Primary Focus):
- **Framework**: Ceedling + Unity + CMock
- **Location**: `tests/drivers/test/test_{driver}/`
- **Mock Strategy**: Mock all platform APIs (SPI, I2C, GPIO, IRQ, etc.)
- **Coverage**: Target 80%+ with gcov
- **See**: `/no-os-unit-testing` skill for comprehensive guide

**Integration Testing** (Example Apps):
- **Framework**: Manual testing with example applications
- **Location**: `projects/{project}/src/examples/`
- **Approach**: Deploy to eval board, verify functionality
- **Automation**: IIO Oscilloscope for IIO-enabled drivers

**HIL Testing**:
- Deploy to Maxim/STM32/Mbed/Xilinx platforms
- Use logic analyzer to verify SPI/I2C transactions
- Validate sensor readings against known inputs

**CI/CD**:
```bash
# Run unit tests
cd tests/drivers/test/test_ad4692
ceedling test:all
ceedling gcov:all

# Check coverage threshold
# Fail CI if coverage < 80%
```

---

### Linux Testing Strategy

**Unit Testing** (KUnit Framework):
- **Framework**: KUnit (in-kernel unit testing)
- **Location**: `drivers/*/tests/` or separate `tools/testing/kunit/`
- **Mock Strategy**: Use `kunit_kzalloc()`, mock subsystem APIs
- **Build**: `make ARCH=um defconfig && make ARCH=um`
- **Run**: `./tools/testing/kunit/kunit.py run`

**Integration Testing** (Device Tree):
- **Framework**: Deploy to target board with device tree
- **Validation**: Check `dmesg`, `sysfs` attributes, IIO tools
- **Example**:
  ```bash
  # Check driver probe
  dmesg | grep ad4692

  # Verify IIO device
  iio_info
  iio_attr -d ad4692
  ```

**HIL Testing**:
- Load kernel module on target hardware
- Validate via sysfs/IIO interface
- Test with real sensor/actuator

**CI/CD**:
```bash
# Compile kernel module
make M=drivers/iio/adc

# Run checkpatch
./scripts/checkpatch.pl --strict --terse --file drivers/iio/adc/ad4692.c

# KUnit tests (if available)
./tools/testing/kunit/kunit.py run --kunitconfig=drivers/iio/adc
```

---

### Zephyr Testing Strategy

**Unit Testing** (Ztest Framework):
- **Framework**: Ztest (Zephyr native testing)
- **Location**: `tests/drivers/{subsystem}/{driver}/`
- **Build**: `west build -b native_posix tests/drivers/sensor/ad7420`
- **Run**: `./build/zephyr/zephyr.exe` (on native_posix)
- **Mock Strategy**: Emulate APIs or use `native_posix` board

**Integration Testing** (Samples):
- **Framework**: Sample applications with board overlays
- **Location**: `samples/drivers/{subsystem}/`
- **Approach**: Deploy to real board (nRF52, STM32)
- **Validation**: Check console output, use debugger

**HIL Testing**:
- Flash to actual board (`west flash`)
- Validate sensor readings
- Test devicetree configuration variants

**CI/CD**:
```bash
# Build for native_posix (simulation)
west build -b native_posix -t run tests/drivers/sensor/ad7420

# Build for real hardware
west build -b nrf52840dk_nrf52840 samples/drivers/sensor/

# Twister test framework
twister -p native_posix -T tests/drivers/
```

---

## Test Planning: What to Test

### Essential Test Categories

#### 1. Initialization Testing

**Test Cases**:
- [ ] Successful initialization with valid parameters
- [ ] Initialization failure with NULL parameters
- [ ] Initialization failure with invalid device ID
- [ ] Product ID verification (correct and incorrect)
- [ ] Memory allocation failure handling
- [ ] Platform resource allocation failures (SPI/I2C init fails)
- [ ] Partial initialization cleanup on error
- [ ] Re-initialization after remove

**Example (no-OS)**:
```c
void test_init_success(void)
{
    struct ad4692_desc *dev = NULL;

    // Setup mocks for successful init
    no_os_calloc_ExpectAndReturn(1, sizeof(struct ad4692_desc), &mock_desc);
    no_os_spi_init_ExpectAndReturn(&spi_desc, &spi_ip, 0);
    ad4692_reg_read_ExpectAndReturn(dev, PRODUCT_ID_REG, 0);
    ad4692_reg_read_ReturnThruPtr_data(&expected_id);

    int ret = ad4692_init(&dev, &init_params);

    TEST_ASSERT_EQUAL(0, ret);
    TEST_ASSERT_NOT_NULL(dev);
}

void test_init_null_param(void)
{
    struct ad4692_desc *dev = NULL;

    int ret = ad4692_init(&dev, NULL);

    TEST_ASSERT_EQUAL(-EINVAL, ret);
    TEST_ASSERT_NULL(dev);
}

void test_init_product_id_mismatch(void)
{
    struct ad4692_desc *dev = NULL;
    uint16_t wrong_id = 0xDEAD;

    no_os_calloc_ExpectAndReturn(1, sizeof(struct ad4692_desc), &mock_desc);
    no_os_spi_init_ExpectAndReturn(&spi_desc, &spi_ip, 0);
    ad4692_reg_read_ExpectAndReturn(dev, PRODUCT_ID_REG, 0);
    ad4692_reg_read_ReturnThruPtr_data(&wrong_id);
    no_os_spi_remove_ExpectAndReturn(spi_desc, 0);
    no_os_free_Expect(&mock_desc);

    int ret = ad4692_init(&dev, &init_params);

    TEST_ASSERT_EQUAL(-ENODEV, ret);
    TEST_ASSERT_NULL(dev);
}
```

---

#### 2. Configuration Testing

**Test Cases**:
- [ ] Valid configuration parameters
- [ ] Out-of-range parameter rejection
- [ ] Configuration before initialization (should fail)
- [ ] Read-back verification of configuration
- [ ] Multi-step configuration sequences
- [ ] Configuration conflicts (mutually exclusive settings)

**Example**:
```c
void test_set_channel_valid(void)
{
    uint8_t channel = 0;

    ad4692_reg_write_ExpectAndReturn(dev, CHANNEL_REG, channel, 0);

    int ret = ad4692_set_channel(dev, channel);

    TEST_ASSERT_EQUAL(0, ret);
}

void test_set_channel_out_of_range(void)
{
    uint8_t invalid_channel = 99;

    int ret = ad4692_set_channel(dev, invalid_channel);

    TEST_ASSERT_EQUAL(-EINVAL, ret);
}

void test_set_channel_null_device(void)
{
    int ret = ad4692_set_channel(NULL, 0);

    TEST_ASSERT_EQUAL(-EINVAL, ret);
}
```

---

#### 3. Data Acquisition Testing

**Test Cases**:
- [ ] Single sample read
- [ ] Multi-sample read (buffered)
- [ ] Channel switching
- [ ] Data format conversion (raw to engineering units)
- [ ] Overflow/underflow handling
- [ ] Timeout on data ready
- [ ] Invalid channel read

**Example**:
```c
void test_read_sample_success(void)
{
    uint32_t sample = 0;
    uint32_t expected_raw = 0x12345678;

    ad4692_reg_read_ExpectAndReturn(dev, DATA_REG, 0);
    ad4692_reg_read_ReturnThruPtr_data(&expected_raw);

    int ret = ad4692_read_sample(dev, &sample);

    TEST_ASSERT_EQUAL(0, ret);
    TEST_ASSERT_EQUAL(expected_raw, sample);
}

void test_read_sample_timeout(void)
{
    uint32_t sample = 0;

    // Simulate data not ready
    ad4692_reg_read_ExpectAndReturn(dev, STATUS_REG, 0);
    ad4692_reg_read_ReturnThruPtr_data(&status_not_ready);
    // Timeout after polling

    int ret = ad4692_read_sample(dev, &sample);

    TEST_ASSERT_EQUAL(-ETIMEDOUT, ret);
}
```

---

#### 4. Error Handling Testing

**Test Cases**:
- [ ] Communication failures (SPI/I2C errors)
- [ ] Register write verification failures
- [ ] Device timeout scenarios
- [ ] Resource exhaustion (memory, descriptors)
- [ ] Concurrent access (if applicable)
- [ ] Invalid state transitions
- [ ] Cleanup on partial failures

**Example**:
```c
void test_reg_write_spi_failure(void)
{
    // Simulate SPI transaction failure
    no_os_spi_write_and_read_ExpectAndReturn(spi_desc, buf, 3, -EIO);

    int ret = ad4692_reg_write(dev, TEST_REG, test_val);

    TEST_ASSERT_EQUAL(-EIO, ret);
}

void test_init_cleanup_on_spi_failure(void)
{
    struct ad4692_desc *dev = NULL;

    no_os_calloc_ExpectAndReturn(1, sizeof(*dev), &mock_desc);
    no_os_spi_init_ExpectAndReturn(&spi_desc, &spi_ip, -EIO);
    no_os_free_Expect(&mock_desc);  // Verify cleanup

    int ret = ad4692_init(&dev, &init_params);

    TEST_ASSERT_EQUAL(-EIO, ret);
    TEST_ASSERT_NULL(dev);
}
```

---

#### 5. State Machine Testing

**Test Cases**:
- [ ] Valid state transitions
- [ ] Invalid state transitions (should fail)
- [ ] State persistence across operations
- [ ] Reset to initial state
- [ ] State query functions

---

#### 6. IIO Integration Testing (no-OS/Linux)

**Test Cases**:
- [ ] Channel registration
- [ ] Attribute read/write
- [ ] Buffer setup and data acquisition
- [ ] Trigger configuration
- [ ] Event generation

**IIO Validation Commands**:
```bash
# List IIO devices
iio_info

# Read attributes
iio_attr -d ad4692 -c voltage0 raw

# Buffered acquisition
iio_readdev -u ip:192.168.1.100 -b 256 -s 1024 ad4692

# Trigger setup
iio_attr -d ad4692 trigger/current_trigger ad4692-dev0
```

---

## Coverage Goals and Metrics

### Coverage Targets by Code Category

| Code Type | Line Coverage | Branch Coverage | Priority |
|-----------|---------------|-----------------|----------|
| **Initialization** | 95%+ | 90%+ | Critical |
| **Configuration** | 90%+ | 85%+ | High |
| **Data Paths** | 85%+ | 80%+ | High |
| **Error Handling** | 80%+ | 75%+ | Medium |
| **Utility Functions** | 75%+ | 70%+ | Medium |
| **Debug/Logging** | Optional | Optional | Low |

### Overall Target: **80%+ Line Coverage**

---

### Analyzing Coverage Reports

**Generate Coverage (no-OS with Ceedling)**:
```bash
ceedling gcov:all
```

**View HTML Report**:
```bash
open build/artifacts/gcov/GcovCoverageResults.html
```

**Identify Gaps**:
1. Look for **red/orange lines** (uncovered code)
2. Focus on **branches** (if/else, switch cases)
3. Prioritize **critical paths** (init, data acquisition)
4. **Ignore** debug logging and unreachable code

**Iterative Improvement**:
```
1. Run coverage → Identify gaps
2. Write tests for uncovered lines
3. Re-run coverage → Verify improvement
4. Repeat until target met
```

---

## Testing Workflow Best Practices

### Test-Driven Development (TDD)

**Process**:
1. **Write test first** (it will fail)
2. **Write minimal code** to pass the test
3. **Refactor** code while keeping tests passing
4. **Repeat** for next feature

**Benefits**:
- Forces you to think about API design
- Ensures testable code
- Provides instant feedback
- Prevents regressions

---

### Coverage-Driven Testing

**Process**:
1. Write initial tests for happy path
2. Run coverage analysis
3. Identify untested code paths
4. Write tests for gaps (especially error paths)
5. Repeat until target coverage met

**Example Workflow**:
```bash
# Initial test run
ceedling test:ad4692
# Coverage: 45%

# Add error handling tests
# Write test_init_null_param, test_init_spi_fail, etc.

ceedling test:ad4692
# Coverage: 68%

# Add edge cases
# Write test_channel_boundary, test_overflow, etc.

ceedling test:ad4692
# Coverage: 82% ✓ Target met!
```

---

### Continuous Integration (CI) Testing

**CI Pipeline Steps**:
```yaml
# {WORKSPACE}/workflows/test.yml
name: Driver Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Ceedling
        run: gem install ceedling
      - name: Run Unit Tests
        run: |
          cd tests/drivers/test/test_ad4692
          ceedling test:all
      - name: Check Coverage
        run: |
          ceedling gcov:all
          # Fail if coverage < 80%
          coverage=$(grep -oP 'TOTAL.*\K[0-9.]+' coverage.txt)
          if (( $(echo "$coverage < 80" | bc -l) )); then
            echo "Coverage $coverage% is below 80%"
            exit 1
          fi

  build-examples:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Examples
        run: |
          cd projects/ad4692_ardz
          make EXAMPLE=basic TARGET=max32690
```

---

## Common Testing Challenges and Solutions

### Challenge 1: Mocking Complex Hardware Interactions

**Problem**: Real hardware has complex timing, state machines, interrupts.

**Solution**:
- Use **stateful mocks** to simulate device state
- Implement **callback mocks** for interrupt simulation
- Create **test fixtures** for common hardware states
- Use **multi-call mocks** for sequential operations

**Example (Sequential SPI transactions)**:
```c
void test_burst_read(void)
{
    uint8_t expected_data[4] = {0x11, 0x22, 0x33, 0x44};

    // First call: send read command
    no_os_spi_write_and_read_ExpectAndReturn(spi, cmd_buf, 1, 0);

    // Second call: read data
    no_os_spi_write_and_read_ExpectAndReturn(spi, data_buf, 4, 0);
    no_os_spi_write_and_read_ReturnArrayThruPtr_data(expected_data, 4);

    int ret = ad4692_burst_read(dev, buffer, 4);

    TEST_ASSERT_EQUAL(0, ret);
    TEST_ASSERT_EQUAL_HEX8_ARRAY(expected_data, buffer, 4);
}
```

---

### Challenge 2: Testing Asynchronous Operations

**Problem**: Interrupts, callbacks, DMA complete events are asynchronous.

**Solution**:
- **Trigger callbacks** manually in tests
- Use **synchronous test doubles** (replace async with sync for testing)
- Test **callback registration** separately from invocation
- Verify **callback behavior** with mock expectations

**Example (Interrupt callback)**:
```c
void test_interrupt_callback(void)
{
    // Register callback
    ad4692_register_callback(dev, my_callback, user_data);

    // Simulate interrupt by calling callback directly
    dev->callback(dev->user_data);

    // Verify callback was executed
    TEST_ASSERT_TRUE(callback_executed);
}
```

---

### Challenge 3: Platform-Specific Code

**Problem**: Platform-specific code (inline assembly, vendor SDK) is hard to test.

**Solution**:
- **Abstract platform dependencies** behind interfaces
- **Test interface contracts** not implementation
- Use **conditional compilation** for platform-specific code
- **Minimize** platform-specific code in driver logic

---

### Challenge 4: Non-Deterministic Behavior

**Problem**: Timing-dependent code, random values, timestamps.

**Solution**:
- **Mock time functions** (`no_os_get_time()`)
- **Inject random seed** for reproducibility
- Use **stub implementations** that return fixed values
- **Control timing** through mocked delays

**Example (Mocking time)**:
```c
void test_timeout_detection(void)
{
    uint32_t timestamps[] = {0, 100, 200, 1000};  // Simulate time passing
    int call_count = 0;

    no_os_get_time_StubWithCallback(mock_get_time);
    // mock_get_time returns timestamps[call_count++]

    int ret = ad4692_wait_ready(dev);

    TEST_ASSERT_EQUAL(-ETIMEDOUT, ret);
}
```

---

## Testing Checklist

### Before Writing Tests
- [ ] Review driver API and identify testable functions
- [ ] Set coverage goal (80%+ recommended)
- [ ] Identify critical paths (init, data acquisition, config)
- [ ] List error scenarios to test
- [ ] Choose appropriate testing framework

### While Writing Tests
- [ ] Test happy path first
- [ ] Add error handling tests
- [ ] Test boundary conditions
- [ ] Verify cleanup on failures
- [ ] Mock all external dependencies
- [ ] Use descriptive test function names
- [ ] Keep tests independent (no shared state)
- [ ] Add comments for complex test logic

### After Writing Tests
- [ ] Run all tests and verify they pass
- [ ] Generate coverage report
- [ ] Analyze gaps and add missing tests
- [ ] Refactor tests for clarity
- [ ] Document test approach in README
- [ ] Set up CI/CD integration
- [ ] Review tests in code review

---

## Quick Reference

### Unit Test Structure (Unity/Ceedling)
```c
#include "unity.h"
#include "driver.h"
#include "mock_no_os_spi.h"

void setUp(void) {
    // Run before each test
}

void tearDown(void) {
    // Run after each test
}

void test_feature_success(void) {
    // Arrange: Set up mocks and data
    // Act: Call function under test
    // Assert: Verify results
}
```

### Common Unity Assertions
```c
TEST_ASSERT_EQUAL(expected, actual);
TEST_ASSERT_EQUAL_HEX8(expected, actual);
TEST_ASSERT_NULL(pointer);
TEST_ASSERT_NOT_NULL(pointer);
TEST_ASSERT_TRUE(condition);
TEST_ASSERT_EQUAL_MEMORY(expected, actual, size);
```

### CMock Patterns
```c
// Expect function call with specific parameters
func_Expect(param1, param2);

// Expect and return value
func_ExpectAndReturn(param1, param2, return_value);

// Return value through pointer
func_ReturnThruPtr_output(&value);

// Ignore specific parameter
func_IgnoreArg_param1();

// Stub with callback for custom behavior
func_StubWithCallback(custom_callback);
```

---

## Additional Resources

- **no-OS Unit Testing**: `/no-os-unit-testing` skill (comprehensive Ceedling/Unity/CMock guide)
- **Zephyr Testing**: https://docs.zephyrproject.org/latest/develop/test/index.html
- **Linux KUnit**: https://www.kernel.org/doc/html/latest/dev-tools/kunit/index.html
- **Unity**: https://github.com/ThrowTheSwitch/Unity
- **CMock**: https://github.com/ThrowTheSwitch/CMock
- **Ceedling**: https://github.com/ThrowTheSwitch/Ceedling
