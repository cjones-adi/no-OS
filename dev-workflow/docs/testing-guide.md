# Testing Guide

**Comprehensive testing framework for no-OS driver development**

This guide covers unit testing with Ceedling, hardware validation requirements, and CI integration for no-OS drivers.

## Testing Framework Overview

### Unit Tests (Ceedling Framework)

```bash
# Run all tests in a test directory
cd tests/drivers/<test_category>/
ceedling test:all

# Generate coverage reports
ceedling gcov:all utils:gcov

# Clean test workspace
ceedling clean
```

### Available Test Categories

- `tests/drivers/imu/`
- `tests/drivers/led/`
- `tests/drivers/power/`

## Ceedling Configuration

### Modern Configuration Format (1.0.1)

```yaml
---
:project:
  :use_exceptions: FALSE
  :use_test_preprocessor: :all
  :use_auxiliary_dependencies: TRUE
  :build_root: build
  :release_build: TRUE
  :test_file_prefix: test_
  :which_ceedling: gem
  :ceedling_version: 1.0.1
  :default_tasks:
    - test:all

# Rest of configuration...
```

**🚨 Critical**: Always use Ceedling 1.0.1+ with modern configuration format.

### Test Structure

```
tests/drivers/<category>/<device>/
├── project.yml           # Ceedling configuration
├── src/
│   ├── test_<device>.c   # Core driver tests
│   ├── test_iio_<device>.c  # IIO tests (if applicable)
│   └── support/
│       ├── test_<device>_data.h   # Test data definitions
│       └── test_<device>_utils.c  # Test utilities
├── mocks/                # Auto-generated mocks
├── build/                # Build artifacts
└── vendor/               # Ceedling dependencies
```

## Unit Test Patterns

### Basic Test Template

```c
#include "unity.h"
#include "ltm4700.h"
#include "mock_no_os_i2c.h"
#include "mock_no_os_gpio.h"
#include "test_ltm4700_data.h"

/* Test fixtures */
static struct ltm4700_dev *test_dev;
static struct ltm4700_init_param test_init_param;

void setUp(void)
{
    test_dev = NULL;

    /* Initialize test parameters */
    test_init_param.i2c_init.device_id = 0;
    test_init_param.i2c_init.slave_address = 0x5A;
    test_init_param.device_id = LTM4700_DEVICE_ID;
}

void tearDown(void)
{
    if (test_dev) {
        ltm4700_remove(test_dev);
        test_dev = NULL;
    }
}

void test_ltm4700_init_success(void)
{
    /* Setup mocks */
    no_os_i2c_init_ExpectAndReturn(&mock_i2c_desc, &test_init_param.i2c_init, 0);

    /* Device ID verification */
    uint8_t device_id = LTM4700_DEVICE_ID;
    no_os_i2c_write_ExpectAndReturn(mock_i2c_desc, test_page_cmd, 2, 0);
    no_os_i2c_write_ExpectAndReturn(mock_i2c_desc, test_device_id_cmd, 1, 0);
    no_os_i2c_read_ExpectAndReturn(mock_i2c_desc, &device_id, 1, 0);

    /* Execute test */
    int32_t ret = ltm4700_init(&test_dev, test_init_param);

    /* Verify results */
    TEST_ASSERT_EQUAL(0, ret);
    TEST_ASSERT_NOT_NULL(test_dev);
    TEST_ASSERT_EQUAL(LTM4700_DEVICE_ID, test_dev->device_id);
}

void test_ltm4700_init_null_device(void)
{
    int32_t ret = ltm4700_init(NULL, test_init_param);
    TEST_ASSERT_EQUAL(-EINVAL, ret);
}

void test_ltm4700_init_i2c_failure(void)
{
    no_os_i2c_init_ExpectAndReturn(&mock_i2c_desc, &test_init_param.i2c_init, -EIO);

    int32_t ret = ltm4700_init(&test_dev, test_init_param);
    TEST_ASSERT_EQUAL(-EIO, ret);
    TEST_ASSERT_NULL(test_dev);
}
```

### Mock Usage Patterns

**✅ Proper Mock Signatures:**
```c
// Complete function signature matching
no_os_i2c_write_ExpectAndReturn(mock_desc, test_data, 2, 0);
no_os_i2c_read_ExpectAndReturn(mock_desc, response_buffer, 2, 0);

// Parameter validation with mock expectations
no_os_i2c_write_ExpectWithArrayAndReturn(mock_desc, expected_cmd, 2, 0);
```

**❌ Incomplete Mock Patterns:**
```c
// Wrong: Missing parameters
no_os_i2c_write_ExpectAndReturn(-EINVAL);

// Wrong: Wrong parameter count
no_os_i2c_write_ExpectAndReturn(mock_desc, -EIO);
```

### IIO Testing Patterns

```c
void test_iio_ltm4700_read_vin(void)
{
    /* Setup test device */
    ltm4700_init(&test_dev, test_init_param);

    /* Mock IIO channel setup */
    struct iio_ch_info test_channel = {
        .ch_num = 0,  /* VIN channel */
        .type = IIO_VOLTAGE,
        .address = LTM4700_VIN_CHAN
    };

    /* Mock register read for VIN */
    uint8_t vin_data[3] = {0x12, 0x34};  /* LINEAR11 format */
    no_os_i2c_write_ExpectAndReturn(mock_i2c_desc, page_cmd, 2, 0);
    no_os_i2c_write_ExpectAndReturn(mock_i2c_desc, vin_cmd, 1, 0);
    no_os_i2c_read_ExpectAndReturn(mock_i2c_desc, vin_data, 2, 0);

    /* Execute IIO read */
    uint32_t vin_value;
    int32_t ret = iio_ltm4700_attr_read(test_dev, (char*)&vin_value, 4, &test_channel, NULL);

    /* Verify results */
    TEST_ASSERT_EQUAL(0, ret);
    /* Verify LINEAR11 conversion */
    TEST_ASSERT_EQUAL(expected_vin_mv, vin_value);
}
```

### Coverage Requirements

**Target: 80%+ code coverage**

```bash
# Generate coverage report
ceedling gcov:all utils:gcov

# View coverage summary
cat build/gcov/GcovCoverageResults.html

# Check specific file coverage
gcov build/gcov/ltm4700.gcda
```

## Hardware Testing Requirements

Before PR approval, hardware testing is **mandatory** for:

1. **Device Communication** - SPI/I2C transactions work correctly
2. **Register Access** - Read/write operations function as expected
3. **Reset Sequences** - Proper device initialization
4. **Error Conditions** - Graceful handling of communication failures
5. **Multiple Platforms** - Test on primary target platforms

### Hardware Testing Checklist

- [ ] Device ID verification works
- [ ] All driver functions execute without errors
- [ ] Reset functionality operates correctly
- [ ] Register read/write operations succeed
- [ ] Error paths handle failures gracefully
- [ ] Memory cleanup prevents leaks
- [ ] Multiple init/remove cycles work
- [ ] Project builds and runs on target hardware

### Platform-Specific Testing

**MAX32655 Platform:**
```bash
# Build for MAX32655
cd projects/<device>/
make PLATFORM=maxim TARGET=max32655

# Flash and test
openocd -f max32655.cfg -c "program <device>.elf verify reset exit"
```

**STM32 Platform:**
```bash
# Build for STM32
make PLATFORM=stm32 TARGET=stm32f4xx

# Flash with ST-Link
st-flash write <device>.bin 0x8000000
```

**Linux Platform (IIO Testing):**
```bash
# Build for Linux with IIO
make PLATFORM=linux

# Test IIO integration
sudo ./linux_<device>
ls /sys/bus/iio/devices/  # Should show iio:deviceX
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
```

## Test Data Management

### Test Data Organization

```c
/* test_ltm4700_data.h */
#ifndef TEST_LTM4700_DATA_H
#define TEST_LTM4700_DATA_H

/* Device identification data */
#define LTM4700_TEST_DEVICE_ID          0x21
#define LTM4777_TEST_DEVICE_ID          0x26

/* PMBus command test data */
extern const uint8_t test_page_cmd[];
extern const uint8_t test_device_id_cmd[];
extern const uint8_t test_vin_cmd[];

/* Expected register values */
extern const uint16_t test_vin_linear11;
extern const uint16_t test_vout_linear16;

/* Test utility functions */
uint32_t convert_linear11_to_mv(uint16_t linear11_value);
uint16_t convert_mv_to_linear16(uint32_t mv_value);

#endif /* TEST_LTM4700_DATA_H */
```

```c
/* test_ltm4700_data.c */
#include "test_ltm4700_data.h"

const uint8_t test_page_cmd[] = {PMBUS_PAGE, 0x00};
const uint8_t test_device_id_cmd[] = {PMBUS_IC_DEVICE_ID};
const uint8_t test_vin_cmd[] = {PMBUS_READ_VIN};

const uint16_t test_vin_linear11 = 0x1234;  /* Example LINEAR11 value */
const uint16_t test_vout_linear16 = 0x5678; /* Example LINEAR16 value */

uint32_t convert_linear11_to_mv(uint16_t linear11_value)
{
    /* Implement LINEAR11 to millivolts conversion for testing */
    int16_t exponent = (linear11_value >> 11) & 0x1F;
    int16_t mantissa = linear11_value & 0x7FF;

    if (exponent > 15)
        exponent -= 32;  /* Two's complement */
    if (mantissa > 1023)
        mantissa -= 2048;  /* Two's complement */

    return (mantissa * 1000) >> (-exponent);
}
```

## CI Integration

### Automated Testing Pipeline

```yaml
# .github/workflows/test.yml
name: Unit Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Ceedling
        run: gem install ceedling

      - name: Run Unit Tests
        run: |
          cd tests/drivers/power/ltm4700/
          ceedling test:all

      - name: Generate Coverage
        run: |
          cd tests/drivers/power/ltm4700/
          ceedling gcov:all utils:gcov

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          file: tests/drivers/power/ltm4700/build/gcov/gcov.info
```

### Build Testing

```bash
# Multi-platform build testing
python3 tools/scripts/build_projects.py . -project=<device>

# Specific platform testing
python3 tools/scripts/build_projects.py . -project=<device> -platform=xilinx
python3 tools/scripts/build_projects.py . -project=<device> -platform=stm32
python3 tools/scripts/build_projects.py . -project=<device> -platform=maxim
```

## Troubleshooting Tests

### Common Test Issues

**Mock Setup Errors:**
```bash
# Clear mock cache
ceedling clean

# Regenerate mocks
ceedling mock:clean
ceedling test:all
```

**Coverage Issues:**
```bash
# Enable coverage flags
export CFLAGS="--coverage"
export LDFLAGS="--coverage"
ceedling gcov:all
```

**Platform Dependencies:**
```bash
# Install required packages
sudo apt-get install build-essential gcc-arm-none-eabi
```

---

Comprehensive testing ensures driver reliability across all supported platforms and use cases.