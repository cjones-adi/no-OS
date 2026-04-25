---
name: zephyr-unit-testing
description: 'Guide to unit testing Zephyr drivers using Ztest framework and Twister. Provides quick-start workflow, references detailed documentation, and example code for comprehensive driver test coverage.'
---

# Zephyr Unit Testing

Quick-start guide for writing unit tests for Zephyr drivers using the Ztest framework and Twister test runner.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/test-macros.md**:
- User mentions: "ZTEST_P", "parameterized", "ZTEST_USER", "userspace", "test rules"
- Question about: fixture vs parameter access, which test macro to use

**Triggers to read reference/troubleshooting.md**:
- Build/link errors in user output
- User says: "build fails", "error", "doesn't work", "tests won't compile"
- Specific errors: fixture struct, k_malloc undefined, devicetree node not found

**Triggers to read reference/virtual-environment.md**:
- User says: "west not found", "command not found", "how to run tests"
- Questions about: virtual environment, activating venv, CI/CD setup
- Errors: twister not working, west not available

**Triggers to read reference/emulators.md**:
- User asks: "how to create emulator", "SPI emulator", "I2C emulator"
- Questions about: emulator patterns, register map, protocol implementation
- Need: complete emulator code, helper functions, devicetree integration

**Triggers to read reference/lessons-learned.md**:
- User asks: "real examples", "what problems did you encounter", "best practices"
- Questions about: common mistakes, debugging tips, project case studies
- Need: practical experience, troubleshooting patterns, metrics

**Triggers to read reference/achieving-100-percent.md**:
- Tests are failing at runtime (not build errors)
- User says: "tests fail", "wrong values", "assertions fail", "not passing"
- Questions about: scaling issues, register values, emulator problems
- User asks: "how to achieve 100%", "fix failing tests", "debugging tests"
- Specific errors: expected X got Y, register is 0x00, scaling mismatch

**Triggers to read examples/sensor-with-emulation.c**:
- User asks: "show me example", "complete example", "how do I structure tests"
- Creating first test suite
- Need concrete code to adapt

---

## When to Use This Skill

- Setting up Ztest test projects for Zephyr drivers
- Writing test functions with assertions and fixtures
- Configuring tests for emulation or hardware
- Running tests with Twister
- Troubleshooting common test issues
- **Achieving 100% test pass rate** (see dedicated section below)

## 🚀 Quick Wins for 100% Pass Rate

If tests are failing at runtime (not build errors), check these first:

1. **Read driver's conversion formula** - Don't assume scaling, check actual code
2. **Don't reset emulator in `before` hook** - Preserve driver init state
3. **Use workaround for I2C writes** - Manually set registers if emulator doesn't capture
4. **Match test expectations to driver behavior** - Not to theoretical expectations
5. **Activate virtual environment** - Always run `source .venv/bin/activate` first

**For systematic debugging**: Read `reference/achieving-100-percent.md` for complete step-by-step guide with code examples and real-world case study (ADXL345: 29/29 tests passing).

---

## Prerequisites

### Virtual Environment Setup

**CRITICAL**: West must be available in your environment. Check which setup you have:

```bash
# Check if west is in virtual environment
ls -la .venv/bin/west

# If yes, activate it before ALL west/twister commands:
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Verify west is available
west --version
```

**Always activate .venv before running tests!** Otherwise you'll see `Command 'west' not found`.

---

## Quick Start Workflow

### 1. Create Test Project Structure

```
zephyr/tests/drivers/[subsystem]/[driver]/
├── src/
│   ├── main.c                    # Test suites and fixtures
│   ├── test_init.c               # Initialization tests
│   ├── test_sample.c             # Functional tests
│   ├── test_error.c              # Error handling tests
│   └── [driver]_emul.c/.h       # Emulator (if needed)
├── boards/
│   └── qemu_cortex_m3.overlay   # Devicetree for emulation
├── CMakeLists.txt
├── testcase.yaml
└── prj.conf
```

### 2. Configure Build (CMakeLists.txt)

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(driver_test)

target_sources(app PRIVATE
    src/main.c
    src/test_init.c
    src/test_sample.c
    src/test_error.c
)
```

### 3. Configure Kconfig (prj.conf)

```
CONFIG_ZTEST=y
CONFIG_SENSOR=y
CONFIG_I2C=y

# For emulation testing
CONFIG_EMUL=y
CONFIG_I2C_EMUL=y

# Verbose output
CONFIG_ZTEST_ASSERT_VERBOSE=1
CONFIG_LOG=y
```

### 4. Configure Twister (testcase.yaml)

```yaml
common:
  integration_platforms:
    - qemu_cortex_m3  # Windows-compatible

tests:
  drivers.sensor.mysensor:
    tags:
      - drivers
      - sensor
    extra_dtc_overlay_files:
      - boards/emulated.overlay
```

### 5. Write Tests (main.c)

```c
#include <zephyr/ztest.h>
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>

#define SENSOR_NODE DT_NODELABEL(mysensor)

/* Fixture structure */
struct sensor_fixture {
    const struct device *dev;
};

/* Setup - runs once before suite */
static void *sensor_setup(void)
{
    static struct sensor_fixture fixture;
    fixture.dev = DEVICE_DT_GET(SENSOR_NODE);
    zassume_true(device_is_ready(fixture.dev), "Device not ready");
    return &fixture;
}

/* Before - runs before each test */
static void sensor_before(void *f)
{
    /* Reset to known state */
}

/* Test using fixture */
ZTEST_F(sensor_tests, test_sample_fetch)
{
    int ret = sensor_sample_fetch(fixture->dev);
    zassert_ok(ret, "Sample fetch failed");
}

/* Register test suite */
ZTEST_SUITE(sensor_tests, NULL, sensor_setup, sensor_before, NULL, NULL);
```

### 6. Run Tests

```bash
# Build and run for qemu_cortex_m3
west build -p auto -b qemu_cortex_m3 tests/drivers/sensor/mysensor \
  -- -DDTC_OVERLAY_FILE=boards/emulated.overlay

# Run with Twister
west twister -T tests/drivers/sensor/mysensor -p qemu_cortex_m3

# Build only (if QEMU not available)
west twister -T tests/drivers/sensor/mysensor --build-only
```

---

## Test Macro Quick Reference

Choose the right macro for your test:

| Macro | Use When... |
|-------|-------------|
| `ZTEST(suite, test)` | Simple test, no shared state needed |
| `ZTEST_F(suite, test)` | Test needs access to fixture data (**most common**) |
| `ZTEST_P(suite, test)` | Same test logic, different input parameters |
| `ZTEST_USER(suite, test)` | Testing userspace APIs (requires CONFIG_USERSPACE) |

**Critical**: All tests in a suite must use the **same macro type**.

**See**: `reference/test-macros.md` for complete details on all test macros including ZTEST_P_F, ZTEST_USER_F, and test rules.

---

## ZTEST_SUITE Parameters

```c
ZTEST_SUITE(suite_name,   // Unique suite identifier
            predicate,     // NULL or condition function
            setup,         // Runs once before suite
            before,        // Runs before each test
            after,         // Runs after each test
            teardown);     // Runs once after suite
```

**Common pattern**:
- **setup**: Initialize device, allocate fixture (use static allocation)
- **before**: Reset device to clean state
- **after**: Usually `NULL`
- **teardown**: Usually `NULL`

---

## Common Assertions

```c
/* Success/failure */
zassert_ok(ret, "msg");              // ret == 0
zassert_true(cond, "msg");           // cond == true
zassert_false(cond, "msg");          // cond == false

/* Equality */
zassert_equal(a, b, "msg");          // a == b
zassert_not_equal(a, b, "msg");      // a != b

/* NULL checks */
zassert_not_null(ptr, "msg");        // ptr != NULL
zassert_is_null(ptr, "msg");         // ptr == NULL

/* Assumptions (skip test if fails) */
zassume_true(cond, "msg");           // Skip test if false
zassume_not_null(ptr, "msg");        // Skip if NULL
```

---

## Devicetree Overlay for Emulation

Create `boards/emulated.overlay`:

```dts
/ {
    test_i2c: i2c@11112222 {
        #address-cells = <1>;
        #size-cells = <0>;
        compatible = "zephyr,i2c-emul-controller";
        reg = <0x11112222 0x1000>;
        status = "okay";
        clock-frequency = <400000>;

        mysensor: mysensor@1d {
            compatible = "vendor,mysensor";
            reg = <0x1d>;
            status = "okay";
        };
    };

    aliases {
        sensor0 = &mysensor;
    };
};
```

---

## Test Organization Best Practices

✅ **DO**:
- One test file per feature (init, sample, attributes, errors)
- Use `ZTEST_F()` when tests need fixture access
- Reset device state in `before` function for test isolation
- Use static fixture allocation (avoid `k_malloc`)
- Include descriptive assertion messages
- Use `zassume_*` in setup (skips suite if fails)
- Define register constants in emulator header (not driver private header)
- Use Zephyr-provided helpers (e.g., `sensor_value_to_double`)
- Remove unused static variables (causes -Werror failures)

❌ **DON'T**:
- Mix `ZTEST()` and `ZTEST_F()` in same suite
- Include driver private headers (e.g., `#include "driver.h"`) - not in include path
- Redefine Zephyr functions (check if they exist first)
- Use deprecated APIs (`device_get_name()` → use `dev->name`)
- Hardcode hardware details (use devicetree macros)
- Create test dependencies (tests must be independent)
- Use `k_malloc()` in fixtures (causes linker errors)
- Command 'west' not found**
→ Activate virtual environment: `source .venv/bin/activate`

**Build error: driver.h: No such file or directory**
→ Don't include driver private headers. Define needed constants in emulator header

**Build error: redefinition of 'sensor_value_to_double'**
→ Remove your version. Zephyr provides it in `<zephyr/drivers/sensor.h>`

**Build error: 'xxx_emul_api' defined but not used [-Werror=unused-const-variable]**
→ Remove unused static const structs. Only define them inside macros if not used directly

**Build error: fixture struct not defined**
→ All tests in suite must use same macro (ZTEST_F vs ZTEST)

**Linker error: undefined reference to k_malloc**
→ Use static allocation in setup function

**Warning: device_get_name implicit declaration**
→ Use `dev->name` instead (Zephyr 4.x)

**Error: DT_HAS_ZEPHYR_I2C_EMUL_CONTROLLER_ENABLED (=n)**
→ Add `CONFIG_EMUL=y` and `CONFIG_I2C_EMUL=y` to prj.conf (or `CONFIG_SPI_EMUL` for SPI)

**Error: overlay not applied**
→ Use `extra_dtc_overlay_files:` not `extra_args:` in testcase.yaml

**Error: POSIX architecture only works on Linux**
→ Use `qemu_cortex_m3` instead of `native_sim` on Windows

**Twister finds 0 tests (filters all configurations)**
→ Add `-p qemu_cortex_m3` to explicitly specify platform

**Tests fail at runtime (wrong values, assertions)**
→ See [Achieving 100% Test Pass Rate](#-achieving-100-test-pass-rate) section below for systematic debugging

**Test expects X but got Y (scaling issues)**
→ Read driver conversion code, update expectations to match actual formula

**Register values are 0x00 after driver init**
→ Don't reset emulator in `before` hook - preserve driver initialization state

**See**: `reference/troubleshooting.md` for 12 common issues with detailed solutions.

---

## Reference Documentation

**When to read each file** (use Read tool):

### reference/test-macros.md
**Read when**:
- User asks about ZTEST_P (parameterized tests)
- Need details on ZTEST_USER (userspace tests)
- Want complete examples of test rules
- Confused about fixture vs parameter access

### reference/troubleshooting.md
**Read when**:
- Build fails with fixture struct errors
- Linker errors (k_malloc, __device_dts_ord)
- Devicetree node not found
- Platform incompatibility issues
- Any error mentioned in quick fixes above

### reference/virtual-environment.md
**Read when**:
- User asks: "west not found", "how to set up environment"
- Questions about: virtual environment activation, pip install west
- CI/CD integration (GitHub Actions, GitLab CI)
- IDE integration (VS Code settings)
- Best practices for environment management

### reference/emulators.md
**Read when**:
- Creating SPI or I2C emulator for tests
- Questions about: emulator patterns, protocol implementation, register maps
- Need: complete emulator code with SPI/I2C protocol
- Want: error injection, FIFO simulation, devicetree integration
- Debugging emulator issues

### reference/lessons-learned.md
**Read when**:
- Want to see real-world project experience (ADXL362 case study)
- Questions about: common mistakes, pitfalls, debugging strategies
- Need: project metrics, test organization examples
- Understanding: what works, what doesn't, why tests fail

### examples/sensor-with-emulation.c
**Read when**:
- Creating first test suite
- Need complete working example to copy/adapt
- Unsure about fixture lifecycle
- Want to see multi-suite organization

---

## Key Takeaways

✅ **Always activate .venv** before running west/twister
✅ Use **ZTEST_F()** for tests that need fixture access
✅ All tests in a suite must use **same macro type**
✅ **Don't include driver private headers** - define constants in emulator
✅ Use **Zephyr-provided helpers** (sensor_value_to_double, etc.)
✅ Use **static fixture allocation** to avoid heap dependencies
✅ Use **emulation drivers** for testing without hardware
✅ Reset device state in **before hook** for test isolation
✅ Use **zassume** in setup, **zassert** in tests
✅ **Remove unused static variables** to avoid -Werror failures
✅ Run tests with **Twister** for CI/CD integration
✅ **Specify platform** with `-p qemu_cortex_m3` to avoid filtering

> **For complete systematic debugging guide, code examples, and ADXL345 case study**:
> Read [reference/achieving-100-percent.md](reference/achieving-100-percent.md)

---

## External Resources

- **Ztest Framework**: https://docs.zephyrproject.org/latest/develop/test/ztest.html
- **Twister**: https://docs.zephyrproject.org/latest/develop/test/twister.html
- **Example Tests**: `zephyr/tests/drivers/gpio/gpio_basic_api/`
- **ADXL345 Complete Suite**: `zephyr/tests/drivers/sensor/adxl345/` (100% pass rate example)
- **Reference Guides**: See reference/ folder for detailed documentation on emulators, troubleshooting, virtual environment setup, and lessons learned
