# Ztest Troubleshooting Guide

Common issues encountered when writing Zephyr unit tests and their solutions.

---

## Issue 1: Mixing ZTEST() and ZTEST_F() in Same Suite

**Symptoms**:
```
error: 'struct adxl372_error_fixture' declared inside parameter list will not be visible outside of this definition or declaration
```

**Problem**:
```c
// ❌ Compilation error: fixture struct not defined
ZTEST(adxl372_error, test_null_device) {  // No fixture
    // ...
}

ZTEST_F(adxl372_error, test_invalid_channel) {  // Expects fixture
    sensor_channel_get(fixture->dev, ...);  // ERROR!
}
```

**Solution**: All tests in a suite must use the same macro:
```c
// ✅ All use ZTEST_F
ZTEST_F(adxl372_error, test_null_device) {
    struct sensor_value val;
    int ret = sensor_sample_fetch(NULL);  // Test with NULL
    zassert_equal(ret, -EINVAL);
}

ZTEST_F(adxl372_error, test_invalid_channel) {
    struct sensor_value val;
    int ret = sensor_channel_get(fixture->dev, INVALID_CHAN, &val);
    zassert_not_equal(ret, 0);
}
```

---

## Issue 2: Fixture Allocation with k_malloc()

**Symptoms**:
```
undefined reference to 'k_malloc'
undefined reference to '__device_dts_ord_N'
```

**Problem**:
```c
// ❌ Linker error: undefined reference to 'k_malloc'
static void *sensor_setup(void) {
    struct sensor_fixture *f = k_malloc(sizeof(*f));
    return f;
}
```

**Solution**: Use static allocation to avoid heap dependencies:
```c
// ✅ Static allocation
static void *sensor_setup(void) {
    static struct sensor_fixture fixture;
    fixture.dev = DEVICE_DT_GET(DT_NODELABEL(sensor));
    return &fixture;
}
```

---

## Issue 3: Using device_get_name() (Deprecated)

**Symptoms**:
```
warning: implicit declaration of function 'device_get_name' [-Wimplicit-function-declaration]
```

**Problem**:
```c
// ❌ Warning/Error in Zephyr 4.x+
const char *name = device_get_name(dev);
```

**Solution**: Access the name field directly:
```c
// ✅ Correct for Zephyr 4.x
const char *name = dev->name;
zassert_not_null(name, "Device name is NULL");
```

---

## Issue 4: Missing Emulation Configuration

**Symptoms**:
```
warning: I2C_EMUL (defined at drivers/i2c/Kconfig.i2c_emul:4) was assigned the value 'y' but got the value 'n'. Check these unsatisfied dependencies: DT_HAS_ZEPHYR_I2C_EMUL_CONTROLLER_ENABLED (=n)
```

**Problem**: Build succeeds but devicetree node not found at runtime

**Solution**: Enable emulation in `prj.conf`:
```kconfig
CONFIG_EMUL=y
CONFIG_I2C_EMUL=y  # For I2C emulation
CONFIG_SPI_EMUL=y  # For SPI emulation
```

---

## Issue 5: Wrong testcase.yaml Syntax for Overlays

**Symptoms**: Devicetree overlay not found or devicetree node missing

**Problem**:
```yaml
# ❌ Overlay not applied
tests:
  drivers.sensor.adxl372:
    extra_args: DTC_OVERLAY_FILE=boards/emulated.overlay
```

**Solution**: Use `extra_dtc_overlay_files`:
```yaml
# ✅ Correct syntax
tests:
  drivers.sensor.adxl372:
    extra_dtc_overlay_files:
      - boards/emulated.overlay
```

---

## Issue 6: Missing Devicetree Emulation Properties

**Symptoms**:
```
devicetree error: 'reg' is marked as required
```

**Problem**:
```dts
// ❌ i2c-emul-controller missing required properties
test_i2c: i2c {
    compatible = "zephyr,i2c-emul-controller";
    status = "okay";
    // Missing reg property!
};
```

**Solution**: Add all required properties:
```dts
// ✅ Complete emulation controller
test_i2c: i2c@11112222 {
    #address-cells = <1>;
    #size-cells = <0>;
    compatible = "zephyr,i2c-emul-controller";
    reg = <0x11112222 0x1000>;  // Required
    status = "okay";
    clock-frequency = <400000>;  // Numeric value, not macro
    
    sensor: sensor@1d {
        compatible = "adi,adxl372";
        reg = <0x1d>;
        status = "okay";
    };
};
```

---

## Issue 7: Platform Incompatibility (native_sim on Windows)

**Symptoms**:
```
The POSIX architecture only works on Linux
```

**Problem**:
```yaml
# ❌ Fails on Windows
common:
  integration_platforms:
    - native_sim
```

**Solution**: Use QEMU platforms for Windows compatibility:
```yaml
# ✅ Works on Windows, Linux, macOS
common:
  integration_platforms:
    - qemu_cortex_m3
```

---

## Issue 8: Obsolete Kconfig Options

**Symptoms**:
```
warning: CONFIG_ZTEST_NEW_API doesn't exist
```

**Problem**:
```kconfig
# ❌ Warning in Zephyr 4.x+
CONFIG_ZTEST_NEW_API=y
```

**Solution**: Remove obsolete options:
```kconfig
# ✅ Minimal required config
CONFIG_ZTEST=y
CONFIG_SENSOR=y
CONFIG_I2C=y
CONFIG_ZTEST_ASSERT_VERBOSE=1
```

---

## Issue 9: Shared Header for Multiple Test Files

**Problem**: Each test file defines its own fixture structure, causing conflicts

**Solution**: Create a shared header:

**test_sensor.h**:
```c
#ifndef TEST_SENSOR_H_
#define TEST_SENSOR_H_

#include <zephyr/device.h>

#define SENSOR_NODE DT_NODELABEL(sensor)

/* Separate fixture for each suite */
struct sensor_init_fixture {
    const struct device *dev;
};

struct sensor_sample_fixture {
    const struct device *dev;
};

struct sensor_attr_fixture {
    const struct device *dev;
};

#endif /* TEST_SENSOR_H_ */
```

Then include in all test files:
```c
#include "test_sensor.h"
```

---

## Issue 10: QEMU Not Available for Test Execution

**Symptoms**:
```
'QEMU-NOTFOUND' is not recognized as an internal or external command
```

**Problem**: Tests build but can't run due to missing QEMU

**Solution**: Use Twister build-only mode or install QEMU:
```bash
# Build without running
west twister -T tests/drivers/sensor/adxl372 --build-only

# Or install QEMU (Windows: Chocolatey)
choco install qemu
```

---

## Issue 11: Test Not Discovered by Twister

**Symptoms**: Twister reports "0 test scenarios selected"

**Common causes**:
1. Missing or incorrect `testcase.yaml`
2. Test files not included in `CMakeLists.txt`
3. Platform filter excluding test
4. Syntax error in test macros

**Solution checklist**:
```yaml
# testcase.yaml must exist
tests:
  drivers.sensor.mysensor:
    tags: [drivers, sensor]
    integration_platforms:
      - qemu_cortex_m3
```

```cmake
# CMakeLists.txt must include test sources
target_sources(app PRIVATE
    src/main.c
    src/test_init.c
    src/test_sample.c
)
```

---

## Issue 12: Devicetree Node Not Found

**Symptoms**:
```
static assertion failed: "DT_N_NODELABEL_sensor"
```

**Problem**: Node label doesn't exist in devicetree or overlay not applied

**Solution**:
1. Check node exists in overlay:
   ```dts
   sensor: sensor@1d {  // 'sensor' is the nodelabel
       compatible = "vendor,device";
       reg = <0x1d>;
   };
   ```

2. Verify overlay is applied in `testcase.yaml`:
   ```yaml
   extra_dtc_overlay_files:
     - boards/my_overlay.overlay
   ```

3. Check build output for overlay confirmation:
   ```
   -- Found devicetree overlay: boards/my_overlay.overlay
   ```

---

## Debugging Tips

### Enable Verbose Build Output

```bash
west build -v
```

### Check Generated Devicetree

```bash
# View final devicetree after overlays applied
cat build/zephyr/zephyr.dts
```

### View Twister Build Log

```bash
# Detailed build log for specific test
cat twister-out/<platform>/<test_path>/build.log
```

### Test Single Suite Manually

```bash
# Build and run specific test
west build -p -b qemu_cortex_m3 tests/drivers/sensor/adxl372
west build -t run
```

### Enable Ztest Debug Output

```kconfig
CONFIG_ZTEST_ASSERT_VERBOSE=1
CONFIG_LOG=y
CONFIG_LOG_MODE_IMMEDIATE=y
CONFIG_SENSOR_LOG_LEVEL_DBG=y
```
