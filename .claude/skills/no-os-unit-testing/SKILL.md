---
name: no-os-unit-testing
description: 'Guide to unit testing no-OS drivers using Ceedling, Unity, CMock, and gcov. Provides quick-start workflow, references detailed documentation, and coverage-driven testing strategies for achieving 80%+ coverage.'
---

# no-OS Unit Testing

Quick-start guide for writing unit tests for no-OS drivers using the Ceedling/Unity/CMock framework and coverage-driven development with gcov.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/assertions.md**:
- User asks: "what assertions", "how to verify", "how to check values"
- Questions about: TEST_ASSERT_* macros, assertion types, validation patterns
- Need: complete assertion reference, examples for different data types

**Triggers to read reference/mocking.md**:
- User asks: "how to mock", "mock I2C", "mock SPI", "simulate hardware"
- Mentions: CMock, stubs, callbacks, register simulation
- Questions about: IgnoreAndReturn vs ExpectAndReturn vs Stub, mock patterns
- Need: hardware simulation strategies, complete mocking examples

**Triggers to read reference/coverage.md**:
- User asks: "how to get coverage", "interpret coverage", "increase coverage"
- Mentions: gcov, coverage report, red lines, yellow lines
- Questions about: coverage-driven workflow, gap analysis, prioritization
- Need: systematic approach to achieving 80%+ coverage

**Triggers to read reference/project-yml.md**:
- User asks: "project.yml", "configure Ceedling", "setup test project"
- Build/configuration errors in user output
- Questions about: CMock configuration, gcov setup, compiler flags
- Creating new test project for driver

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "how to organize tests", "testing patterns"
- Questions about: test organization, naming conventions, mock management
- Need: quality guidelines, common patterns, anti-patterns to avoid

**Triggers to read reference/troubleshooting.md**:
- Build/link/runtime errors in user output
- User says: "build fails", "error", "doesn't work", "tests won't compile"
- Specific errors: mock not found, undefined reference, segfault, silent failure
- Coverage issues: 0% coverage, report not generated

**Triggers to read reference/lessons-learned.md**:
- User asks: "common issues", "lessons learned", "tips", "what went wrong"
- Errors: CRC undefined reference, calloc failures, missing mocks
- Questions about: CRC mocking, memory allocation in tests, utility function mocks
- Need: practical examples from real driver testing, debugging strategies

---

## When to Use This Skill

- Setting up Ceedling test projects for no-OS drivers
- Writing test functions with Unity assertions and CMock mocks
- Mocking platform APIs (I2C, SPI, GPIO, IRQ)
- Generating and analyzing gcov coverage reports
- Achieving 80%+ line coverage through iterative testing
- Troubleshooting test build and runtime issues

## Testing Ecosystem Overview

```
┌──────────────────────────────────────────────────────────┐
│                 no-OS Unit Testing Stack                 │
└──────────────────────────────────────────────────────────┘

         ┌────────────────────────────────┐
         │        Ceedling                │
         │  (Build & Orchestration)       │
         │  - Project configuration       │
         │  - Test discovery & execution  │
         │  - Coverage report generation  │
         └───────────┬────────────────────┘
                     │
        ┌────────────┴───────────┐
        │                        │
   ┌────▼────────┐        ┌──────▼──────┐
   │   Unity     │        │   CMock     │
   │(Assertions) │        │  (Mocks)    │
   │- TEST_ASSERT│        │- auto-gen   │
   │- Fixtures   │        │- Expect/Stub│
   └─────────────┘        └─────────────┘
                                 │
                     ┌───────────┴──────────────┐
                     │  Hardware Abstraction    │
                     │  Mocks (Generated)       │
                     │  - mock_no_os_i2c.c      │
                     │  - mock_no_os_spi.c      │
                     │  - mock_no_os_gpio.c     │
                     └──────────────────────────┘

         ┌────────────────────────────────┐
         │          gcov                  │
         │  (Coverage Analysis)           │
         │  - Line coverage               │
         │  - Branch coverage             │
         │  - HTML reports                │
         └────────────────────────────────┘
```

---

## Quick Start Guide

### 1. Create Test Project Structure

```
tests/drivers/[subsystem]/[driver]/
├── test/
│   ├── test_[driver].c          # Main test file
│   └── test_[driver]_feature.c  # Additional tests
└── project.yml                  # Ceedling configuration
```

**Example**: MAX20370 driver tests
```
tests/drivers/power/max20370/
├── test/
│   ├── test_max20370.c
│   └── test_max20370_regulator.c
└── project.yml
```

### 2. Create project.yml Configuration

**CRITICAL**: Always copy from existing working example: `tests/drivers/power/max20370/project.yml`

Do NOT create from scratch - use the complete template from max20370 and adjust paths/driver name.

**Key sections needed**:
- `:project:` - Basic configuration
- `:paths:` - Source/test/include directories
- `:cmock:` with `:plugins:` - Mock generation
- `:gcov:` - Coverage reporting
- `:plugins:` - Test execution and reporting
- `:flags:` - Compiler options
- `:test_[driver]:` `:includes:` - Headers to mock

**See**: `reference/project-yml.md` for complete template and explanation.

### 3. Write Test File

```c
/**
 * @file test_max20370.c
 * @brief Unit tests for MAX20370 driver
 */

#include "unity.h"                   // Unity test framework
#include "max20370.h"                // Driver under test
#include "mock_no_os_i2c.h"          // Generated mocks
#include "mock_no_os_gpio.h"
#include "mock_no_os_util.h"
#include <errno.h>
#include <stdlib.h>

/*******************************************************************************
 * Test Globals
 ******************************************************************************/
static struct max20370_dev *test_dev = NULL;

/*******************************************************************************
 * Stub Callbacks
 ******************************************************************************/

/**
 * @brief Stub for calloc - allocates memory (CRITICAL: use this, not IgnoreAndReturn!)
 */
static void *stub_calloc(size_t nmemb, size_t size, int cmock_num_calls) {
    return calloc(nmemb, size);
}

/*******************************************************************************
 * Test Fixtures - setUp() and tearDown()
 ******************************************************************************/

/**
 * @brief setUp - Called BEFORE each test
 */
void setUp(void) {
    test_dev = NULL;

    // Configure default mock behavior - all platform calls succeed
    no_os_i2c_init_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_read_IgnoreAndReturn(0);
    no_os_i2c_remove_IgnoreAndReturn(0);

    // Utility function mocks
    no_os_field_prep_IgnoreAndReturn(0);
    no_os_field_get_IgnoreAndReturn(0);
    no_os_sign_extend32_IgnoreAndReturn(0);

    // CRC mocks (if driver uses CRC - check driver.c for #include "no_os_crc")
    no_os_crc8_populate_msb_Ignore();
    no_os_crc8_IgnoreAndReturn(0);
    no_os_crc16_populate_msb_Ignore();
    no_os_crc16_IgnoreAndReturn(0);

    // Memory allocation - use stub for real allocation!
    no_os_calloc_StubWithCallback(stub_calloc);
    no_os_free_Ignore();
}

/**
 * @brief tearDown - Called AFTER each test
 */
void tearDown(void) {
    if (test_dev) {
        if (test_dev->i2c_desc)
            free(test_dev->i2c_desc);
        free(test_dev);
        test_dev = NULL;
    }
}

/*******************************************************************************
 * Helper Functions
 ******************************************************************************/

static int create_mock_device(void) {
    test_dev = calloc(1, sizeof(struct max20370_dev));
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

/*******************************************************************************
 * Test Cases - Initialization Tests
 ******************************************************************************/

void test_max20370_init_success(void) {
    struct max20370_dev *dev = NULL;
    struct max20370_init_param init = {
        .i2c_init = { /* I2C config */ }
    };

    int ret = max20370_init(&dev, &init);

    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_NOT_NULL(dev);

    max20370_remove(dev);
}

void test_max20370_init_null_device_pointer(void) {
    struct max20370_init_param init = { /* config */ };

    int ret = max20370_init(NULL, &init);

    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}

void test_max20370_init_null_param(void) {
    struct max20370_dev *dev = NULL;

    int ret = max20370_init(&dev, NULL);

    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
    TEST_ASSERT_NULL(dev);
}

/*******************************************************************************
 * Test Cases - Configuration Tests
 ******************************************************************************/

void test_max20370_configure_null_device(void) {
    int ret = max20370_set_voltage(NULL, 0, 3300);
    TEST_ASSERT_EQUAL_INT(-ENODEV, ret);
}

void test_max20370_configure_valid(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());

    int ret = max20370_set_voltage(test_dev, 0, 3300);

    TEST_ASSERT_EQUAL_INT(0, ret);
}

void test_max20370_configure_i2c_failure(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());

    // Override default success - inject I2C error
    no_os_i2c_write_IgnoreAndReturn(-EIO);

    int ret = max20370_set_voltage(test_dev, 0, 3300);

    TEST_ASSERT_EQUAL_INT(-EIO, ret);
}
```

**Key points**:
- Test files MUST start with `test_` prefix
- Test functions MUST start with `test_` prefix
- Use setUp() for default mock behavior (IgnoreAndReturn)
- Use tearDown() for cleanup
- Create helper functions for common operations

### 4. Run Tests

```bash
# Navigate to test directory
cd tests/drivers/power/max20370/

# Run all tests
ceedling test:all

# Run specific test file
ceedling test:test_max20370

# Clean and rebuild
ceedling clobber
ceedling test:all
```

**Example output**:
```
-----------------------
OVERALL TEST SUMMARY
-----------------------
TESTED:  32
PASSED:  32
FAILED:  0
IGNORED: 0
```

### 5. Generate Coverage Report

```bash
# Generate coverage
ceedling gcov:all

# Or for specific driver
ceedling gcov:max20370
```

**Example output**:
```
Coverage Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File: drivers/power/max20370/max20370.c
  Lines:    245/298   (82.21%)
  Branches: 124/124   (100.00%)
  Functions: 28/28    (100.00%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HTML report: build/artifacts/gcov/gcovr/coverage_report.max20370.c.*.html
```

### 6. Analyze Coverage and Iterate

```bash
# Open HTML coverage report
# Linux/Mac:
open build/artifacts/gcov/gcovr/coverage_report.*.html

# Windows:
start build/artifacts/gcov/gcovr/coverage_report.*.html
```

**Look for**:
- 🔴 Red lines: NOT covered - add tests
- 🟡 Yellow lines: Partially covered - test both branches
- 🟢 Green lines: Fully covered - good

**Iterate**:
1. Identify red lines and untested functions in HTML report
2. Add targeted tests for gaps (error paths, edge cases)
3. Re-run coverage: `ceedling gcov:all`
4. Repeat until 80%+ coverage achieved

**See**: `reference/coverage.md` for complete coverage-driven workflow.

---

## Essential Assertions (Quick Reference)

```c
// Return value / error codes
TEST_ASSERT_EQUAL_INT(0, ret);              // Success
TEST_ASSERT_EQUAL_INT(-EINVAL, ret);        // Error code

// Pointers
TEST_ASSERT_NOT_NULL(dev);                  // Device created
TEST_ASSERT_NULL(dev);                      // Device not created

// Register values (hex)
TEST_ASSERT_EQUAL_HEX8(0xAB, reg_value);    // 8-bit register
TEST_ASSERT_EQUAL_HEX16(0x1234, value);     // 16-bit value

// Booleans
TEST_ASSERT_TRUE(condition);
TEST_ASSERT_FALSE(condition);

// Arrays / buffers
TEST_ASSERT_EQUAL_UINT8_ARRAY(expected, actual, length);
TEST_ASSERT_EQUAL_HEX8_ARRAY(expected, actual, length);

// Custom messages
TEST_ASSERT_EQUAL_INT_MESSAGE(0, ret, "Init failed");
TEST_ASSERT_NOT_NULL_MESSAGE(dev, "Device creation failed");
```

**See**: `reference/assertions.md` for complete assertion reference with examples.

---

## Essential Mock Patterns (Quick Reference)

### Pattern 1: Default Success in setUp() (Use This!)

```c
void setUp(void) {
    test_dev = NULL;

    // All platform calls succeed by default
    no_os_i2c_init_IgnoreAndReturn(0);
    no_os_i2c_write_IgnoreAndReturn(0);
    no_os_i2c_read_IgnoreAndReturn(0);
}

void test_driver_function(void) {
    // No mock configuration needed - uses defaults
    int ret = driver_function(test_dev);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

### Pattern 2: Override for Error Testing

```c
void test_driver_i2c_failure(void) {
    // Override default success
    no_os_i2c_write_IgnoreAndReturn(-EIO);

    int ret = driver_function(test_dev);

    TEST_ASSERT_EQUAL_INT(-EIO, ret);
}
```

### Pattern 3: Stub for Hardware Simulation

```c
static uint8_t mock_regs[256];  // Simulated register map

static int32_t stub_i2c_read(struct no_os_i2c_desc *desc,
                             uint8_t *data, uint8_t bytes,
                             uint8_t stop, int cmock_num_calls)
{
    uint8_t reg_addr = data[0];
    data[0] = mock_regs[reg_addr];  // Return register value
    return 0;
}

void test_driver_read_chip_id(void) {
    mock_regs[CHIP_ID_REG] = 0x12;  // Expected chip ID

    no_os_i2c_read_Stub(stub_i2c_read);

    uint8_t chip_id;
    int ret = driver_read_chip_id(test_dev, &chip_id);

    TEST_ASSERT_EQUAL_HEX8(0x12, chip_id);
}
```

**Mock Types**:
- **IgnoreAndReturn**: Use 95% of the time (default behavior)
- **Stub**: Use for hardware simulation (register maps, chip ID)
- **ExpectAndReturn**: Rarely needed (strict parameter validation)

**See**: `reference/mocking.md` for complete mocking guide with advanced patterns.

---

## Common Commands

| Task | Command |
|------|---------|
| Run all tests | `ceedling test:all` |
| Run specific test | `ceedling test:test_driver_name` |
| Generate coverage | `ceedling gcov:driver_name` |
| Clean build | `ceedling clobber` |
| Verbose output | `ceedling test:name --verbosity=obnoxious` |

---

## Coverage-Driven Workflow

1. **Write initial tests** (init, basic functionality)
2. **Run tests**: `ceedling test:all` → verify all pass
3. **Generate coverage**: `ceedling gcov:all` → get baseline (e.g., 45%)
4. **Open HTML report** → identify red lines (untested code)
5. **Add targeted tests** → error paths, edge cases, untested functions
6. **Repeat steps 2-5** until 80%+ coverage achieved

**Target**: 80-85% line coverage (industry standard for embedded drivers)

**Prioritize**:
- HIGH: Untested functions (0% coverage)
- HIGH: Error handling paths (red lines)
- MEDIUM: Partial branches (yellow lines)
- LOW: Already well-covered code

**See**: `reference/coverage.md` for systematic gap analysis and prioritization.

---

## Common Issues & Quick Fixes

**Mock not found**:
```
fatal error: mock_no_os_i2c.h: No such file or directory
```
→ Add header to `:test_[driver]:` `:includes:` in project.yml

**_IgnoreAndReturn undefined**:
```
undefined reference to `no_os_i2c_write_IgnoreAndReturn'
```
→ Add `:ignore:` to `:cmock:` `:plugins:` in project.yml

**Coverage is 0%**:
→ Verify `:gcov:` section complete in project.yml

**Ceedling does nothing (silent failure)**:
→ Add `:plugins:` `:enabled:` section to project.yml

**Test not discovered**:
→ Rename to `test_*.c` and functions to `test_*()`

**Segmentation fault**:
→ Check NULL pointers, call create_mock_device() before using test_dev

**See**: `reference/troubleshooting.md` and `reference/lessons-learned.md` for complete solutions.

---

## Best Practices

- Group tests logically (init, config, operation, errors)
- Use descriptive names: `test_driver_init_null_device` not `test_1`
- Default to stub_calloc in setUp() - allocate real memory
- Mock CRC functions if driver uses CRC (check for #include "no_os_crc")
- Target 80% coverage, focus on error paths

**See**: `reference/best-practices.md` for complete guidelines.

---

## Reference Documentation

**When to read each file** (use Read tool):

- **reference/assertions.md** - Complete Unity assertion reference with examples
- **reference/mocking.md** - Complete CMock guide: IgnoreAndReturn, Stub patterns, hardware simulation
- **reference/coverage.md** - Coverage-driven workflow: gcov, HTML analysis, gap identification, 80%+ strategies
- **reference/project-yml.md** - Complete project.yml template and configuration
- **reference/best-practices.md** - Testing best practices: organization, naming, mock management, quality
- **reference/troubleshooting.md** - Common errors and solutions: build/runtime/coverage issues
- **reference/lessons-learned.md** - Real-world lessons: CRC mocking, calloc stubs, debugging strategies

---

## Key Takeaways

- **Always verify results** - Run tests and generate coverage, report actual numbers
- **Copy working template** - Use max20362/max20370 project.yml as base
- **Use stub_calloc in setUp()** - Don't IgnoreAndReturn(NULL), allocate real memory
- **Mock CRC if driver uses it** - Add no_os_crc8.h and no_os_crc16.h to includes
- **Mock utility functions** - field_prep, field_get, sign_extend32
- **Target 80% coverage** - Industry standard for embedded drivers
- **Focus on error paths** - Red lines usually indicate missing error tests
- **Read reference docs** - Complete details available when needed

**Workflow**: Setup project.yml → Write tests → Run → Generate coverage → Analyze gaps → Add tests → Repeat until 80%+

**Result**: High-quality, maintainable unit tests that validate driver functionality, error handling, and edge cases without requiring real hardware.
