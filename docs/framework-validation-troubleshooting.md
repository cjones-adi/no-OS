# Framework Validation Troubleshooting Guide

## 🚨 Common Framework Validation Failures & Quick Fixes

This guide provides immediate solutions for framework validation failures encountered during driver development.

## **Quick Diagnostic Commands**

```bash
# Run framework validation
./tools/scripts/framework_validation.sh <device> <category> <platform>

# Check platform headers exist
find drivers/platform/maxim/ -name 'maxim_uart.h' | head -1

# Verify Ceedling configuration
grep "ceedling_version" tests/drivers/*/project.yml | head -1

# Check IIO structure
grep -n "ch_num" iio/iio_types.h
```

## **Error 1: Platform API Validation Failures**

```
❌ Checking maxim_uart.h header... FAIL
```

**Root Cause**: Maxim platform uses chip-specific directories, not generic paths.

**Quick Fix**: Platform headers are located in chip-specific subdirectories:
```bash
# Headers exist here:
ls drivers/platform/maxim/max32665/maxim_uart.h  ✅
ls drivers/platform/maxim/max32655/maxim_uart.h  ✅

# NOT here (validation was looking here):
ls drivers/platform/maxim/maxim_uart.h           ❌
```

**Solution**: Framework validation script has been updated to detect chip-specific paths.

## **Error 2: Ceedling Version Mismatch**

```
❌ Ceedling version mismatch: ceedling_version (expected 1.0.1)
```

**Root Cause**: Incorrect YAML field parsing.

**Quick Fix**: The YAML structure creates multiple fields:
```yaml
:project:
  :ceedling_version: 1.0.1
#     ^field1^  ^field2^ ^field3^
```

**Solution**: Framework validation script has been updated to parse field 3.

## **Error 3: IIO Channel Structure Validation**

```
❌ IIO channel structure... FAIL
```

**Root Cause**: Wrong header file being checked for IIO structures.

**Quick Fix**: The `ch_num` field is in `iio_types.h`, not `iio.h`:
```c
// In iio/iio_types.h (CORRECT)
struct iio_ch_info {
    int16_t ch_num;  ✅
    // ...
};

// NOT in iio/iio.h (validation was looking here)
```

**Solution**: Framework validation script has been updated to check correct header.

## **Error 4: Build System Platform Configuration**

```
❌ fatal error: maxim_dma.h: No such file or directory
```

**Root Cause**: Missing platform source configuration.

**Quick Fix**: Platform configuration must include common directory:
```makefile
# REQUIRED in platform_src.mk
NO_OS_INC_DIRS += \
        $(PLATFORM_DRIVERS) \
        $(PLATFORM_DRIVERS)/../common/    # ← This was missing

SRCS += $(PLATFORM_DRIVERS)/../common/maxim_dma.c  # ← This was missing
```

**Solution**: Use working project (LTM4686) as template for platform configuration.

## **Error 5: IIO API Type Compatibility**

```
❌ warning: passing argument X of 'iio_format_value' from incompatible pointer type
```

**Root Cause**: IIO API expects `int32_t *`, driver used `int *`.

**Quick Fix**: Use consistent types for IIO interface:
```c
// ✅ CORRECT
int32_t val;
int32_t vals[2];

// ❌ WRONG (causes warnings)
int val;
int vals[2];
```

**Solution**: Always use `int32_t` for IIO interface variables.

## **Error 6: Unit Test Mock Generation Issues**

```
❌ error: invalid application of 'sizeof' to incomplete type 'struct iio_desc'
```

**Root Cause**: Attempting to mock complex IIO subsystem structures.

**Quick Fix**: Don't mock the IIO subsystem for IIO driver tests:
```c
// ❌ DON'T DO THIS
#include "mock_iio.h"       // Causes mock generation failures

// ✅ DO THIS INSTEAD
#include "mock_ltm4700.h"   // Mock the underlying driver
#include "mock_no_os_alloc.h"
// Test with real IIO library
```

**Solution**: Follow MAX17616 testing pattern - mock driver, not IIO subsystem.

## **Error 7: Missing Standard Includes**

```
❌ error: 'EINVAL' undeclared
❌ error: 'true' undeclared
```

**Root Cause**: Missing standard library includes in test files.

**Quick Fix**: Add required includes to all test files:
```c
#include "unity.h"
#include <errno.h>     // For EINVAL, ENOMEM, EIO
#include <stdbool.h>   // For true, false
```

**Solution**: Standard includes added to all test template files.

## **Prevention Workflow**

### **Step 1: Always Run Framework Validation First**
```bash
# MANDATORY before any implementation
./tools/scripts/framework_validation.sh ltm4700 power maxim
```

### **Step 2: Use Working Project References**
```bash
# For platform configuration
cp projects/ltm4686/src/platform/maxim/platform_src.mk projects/NEW_PROJECT/src/platform/maxim/

# For IIO testing patterns
cp tests/drivers/power/max17616/test/test_iio_max17616.c tests/drivers/power/NEW_DEVICE/test/
```

### **Step 3: Verify API Compatibility**
```bash
# Check for IIO type consistency
grep -r "int32_t.*val" drivers/power/NEW_DEVICE/iio_*.c
```

## **Success Validation**

After fixes, framework validation should show:
```
🎉 Framework Validation PASSED
   Safe to proceed with driver implementation planning
```

**Build Success Indicators**:
- ✅ Framework validation: All checks pass
- ✅ Project compilation: `NEW_DEVICE.hex is ready`
- ✅ Unit tests: Mock compilation successful

## **Emergency Debug Commands**

If validation still fails:
```bash
# Check platform structure
find drivers/platform/ -name "*uart*" | grep maxim

# Verify test configuration
cd tests/drivers/power/NEW_DEVICE
ceedling summary

# Check for missing dependencies
grep -r "No such file" build/ 2>/dev/null || echo "No missing file errors"
```

## **Documentation References**

- **Complete lessons learned**: `memory/framework-validation-lessons.md`
- **Platform standards**: `docs/architecture-standards.md`
- **Testing patterns**: `docs/testing-guide.md`

---
**Last Updated**: April 2026 based on LTM4700 implementation lessons
**Validation Accuracy**: 100% (5/5 checks) after corrections