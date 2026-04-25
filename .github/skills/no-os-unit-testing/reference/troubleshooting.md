# Troubleshooting Common Issues

Common errors and solutions for no-OS driver unit testing with Ceedling, Unity, and CMock.

## Build Errors

### Error: Mock includes not found

```
fatal error: mock_no_os_i2c.h: No such file or directory
 #include "mock_no_os_i2c.h"
```

**Cause**: Mock not generated or header not listed in `project.yml`

**Solution**: Add header to `:test_[driver]:` `:includes:` section
```yaml
:test_max20370:
  :compile:
    :includes:
      - ../../../../include/no_os_i2c.h  # Add this
```

### Error: Undefined reference to mock functions

```
undefined reference to `no_os_i2c_write_IgnoreAndReturn'
```

**Cause**: CMock plugins not enabled in `project.yml`

**Solution**: Verify `:cmock:` `:plugins:` section
```yaml
:cmock:
  :plugins:
    - :ignore    # Enables _IgnoreAndReturn
    - :callback  # Enables _Stub
```

### Error: Source file not found

```
ERROR: Ceedling could not find source file for test
```

**Cause**: Wrong path in `:paths:` `:source:` section

**Solution**: Verify driver path relative to project.yml
```yaml
:paths:
  :source:
    - ../../../../drivers/power/max20370  # Adjust path
```

### Error: Multiple definition of functions

```
multiple definition of `driver_init'
```

**Cause**: Driver source included multiple times or in wrong section

**Solution**: Check `:files:` section - driver should be in `:source:`, not `:test:`
```yaml
:files:
  :test:
    - test/*.c       # Only test files here
  :source:
    - ../../../../drivers/power/max20370/*.c  # Driver here
```

## Runtime Errors

### Error: Test expects mock call but driver doesn't call it

```
ERROR: Function no_os_i2c_write called with unexpected parameters
```

**Cause**: Using `_ExpectAndReturn` with wrong parameters

**Solution**: Use `_IgnoreAndReturn` instead
```c
// Bad: Strict parameter matching
no_os_i2c_write_ExpectAndReturn(desc, data, 2, 1, 0);

// Good: Accept any parameters
no_os_i2c_write_IgnoreAndReturn(0);
```

### Error: Test fails with "unexpected call"

```
ERROR: Function no_os_i2c_write called but no mock configured
```

**Cause**: Forgot to configure mock in setUp()

**Solution**: Add default mock behavior in setUp()
```c
void setUp(void) {
    no_os_i2c_write_IgnoreAndReturn(0);  // Add this
}
```

### Error: Segmentation fault during test

```
Segmentation fault (core dumped)
```

**Cause**: NULL pointer dereference or use-after-free

**Common causes**:
1. Forgot to initialize test_dev
2. Accessing freed memory in tearDown()
3. Driver expects hardware that doesn't exist

**Solution**: Check test setup
```c
void test_driver_configure(void) {
    // Make sure device is created first!
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    
    int ret = driver_configure(test_dev);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

## Coverage Issues

### Issue: Coverage is 0% but tests pass

**Cause**: Coverage not enabled or wrong configuration

**Solution**: Verify `:gcov:` section complete in project.yml
```yaml
:gcov:
  :html_report: TRUE
  :html_report_type: detailed
  :reports:
    - HtmlDetailed
  :gcovr:
    # ... all gcovr options ...
```

### Issue: Coverage report not generated

**Cause**: `gcov` plugin not enabled

**Solution**: Add to `:plugins:` `:enabled:`
```yaml
:plugins:
  :enabled:
    - gcov  # Add this
    - report_tests_pretty_stdout
    - module_generator
```

### Issue: Coverage report excludes driver files

**Cause**: Wrong `:gcov:` `:gcovr:` `:report_include:` filter

**Solution**: Update include pattern
```yaml
:gcov:
  :gcovr:
    :report_include: ".*max20370.*"  # Match your driver name
    :report_exclude: ".*test.*"
```

## Ceedling Behavior

### Issue: Ceedling does nothing (silent failure)

**Cause**: Missing or incomplete `:plugins:` section

**Solution**: Add complete plugins section
```yaml
:plugins:
  :enabled:
    - report_tests_pretty_stdout
    - module_generator
    - report_tests_raw_output_log
    - gcov
    - report_tests_log_factory
```

### Issue: Tests not discovered

**Cause**: Test file doesn't start with `test_` prefix

**Solution**: Rename files
```
max20370_test.c  ❌  → test_max20370.c  ✅
```

### Issue: Test functions not executed

**Cause**: Functions don't start with `test_` prefix

**Solution**: Rename functions
```c
validate_init()  ❌  → test_driver_init()  ✅
```

### Issue: clobber doesn't work

```
ERROR: Don't know how to build task 'clobber'
```

**Cause**: Old or minimal project.yml

**Solution**: Use complete template from max20370/project.yml

## Compiler Warnings/Errors

### Warning: Unused parameter

```
warning: unused parameter 'cmock_num_calls' [-Wunused-parameter]
```

**Cause**: Stub callback has unused parameters

**Solution**: Already handled in flags - verify `:flags:` section
```yaml
:flags:
  :test:
    :compile:
      :*:
        - -Wno-unused-parameter  # Suppresses this warning
```

### Warning: Missing field initializers

```
warning: missing field initializers [-Wmissing-field-initializers]
```

**Solution**: Already handled in flags
```yaml
:flags:
  :test:
    :compile:
      :*:
        - -Wno-missing-field-initializers
```

### Error: implicit declaration of function

```
warning: implicit declaration of function 'calloc'
```

**Cause**: Missing standard library includes

**Solution**: Add includes to test file
```c
#include <stdlib.h>  // For calloc, malloc, free
#include <errno.h>   // For error codes
#include <string.h>  // For memset, memcpy
```

## Mock-Specific Issues

### Issue: Stub callback not called

**Cause**: `_Stub` called but `:callback:` plugin not enabled

**Solution**: Verify CMock plugins
```yaml
:cmock:
  :plugins:
    - :callback  # Required for _Stub
```

### Issue: ReturnThruPtr doesn't work

**Cause**: `:return_thru_ptr:` plugin not enabled

**Solution**: Add plugin
```yaml
:cmock:
  :plugins:
    - :return_thru_ptr  # Required for ReturnThruPtr
```

### Issue: Mock call count wrong

**Cause**: Mock configured multiple times or not reset between tests

**Solution**: Only configure mocks in setUp(), not in individual tests (unless overriding)
```c
void setUp(void) {
    // Configure once here
    no_os_i2c_write_IgnoreAndReturn(0);
}

void test_case_1(void) {
    // Don't reconfigure - uses setUp() default
    driver_function();
}

void test_case_2(void) {
    // Override only if needed
    no_os_i2c_write_IgnoreAndReturn(-EIO);
    driver_function();
}
```

## Platform-Specific Issues

### Linux: Permission denied

```
bash: ./build/test/out/test_driver.out: Permission denied
```

**Solution**: Executable permissions not needed - Ceedling handles this

### Windows: Path too long

```
ERROR: The system cannot find the path specified
```

**Cause**: Windows has path length limitations

**Solution**: Move project closer to root
```
C:\no-os\tests\...  ✅  Better
C:\Users\VeryLongUsername\Documents\Projects\no-os-fork\tests\...  ❌  Too long
```

## Common Test Mistakes

### Mistake: Not checking helper function return values

```c
void test_driver_configure(void) {
    create_mock_device();  // ❌ Doesn't check return value
    driver_configure(test_dev);  // test_dev might be NULL!
}
```

**Solution**: Always check helpers
```c
void test_driver_configure(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());  // ✅
    int ret = driver_configure(test_dev);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

### Mistake: Memory leaks in tests

```c
void test_driver_function(void) {
    struct driver_dev *dev = malloc(sizeof(*dev));
    driver_function(dev);
    // ❌ Memory leak - never freed
}
```

**Solution**: Free in tearDown() or end of test
```c
void tearDown(void) {
    if (test_dev) {
        free(test_dev);  // ✅ Cleanup
        test_dev = NULL;
    }
}
```

### Mistake: Shared state between tests

```c
static int test_counter = 0;  // ❌ Shared between tests

void test_1(void) {
    test_counter++;  // Affects test_2
}

void test_2(void) {
    // test_counter is now 1, not 0!
}
```

**Solution**: Reset state in setUp()
```c
static int test_counter = 0;

void setUp(void) {
    test_counter = 0;  // ✅ Reset before each test
}
```

## Debug Techniques

### Technique 1: Verbose output

```bash
ceedling test:driver_name --verbosity=obnoxious
```

Shows:
- All compiler commands
- Mock generation details
- Detailed failure information

### Technique 2: Check generated files

```bash
# See what mocks were generated
ls build/test/mocks/

# See test runner
cat build/test/runners/test_driver_runner.c

# See compilation commands
ceedling test:driver --verbosity=obnoxious 2>&1 | grep "gcc"
```

### Technique 3: Isolate the test

```bash
# Run only one test file
ceedling test:test_max20370

# Not all tests
ceedling test:all
```

### Technique 4: Clean build

```bash
# Remove all build artifacts
ceedling clobber

# Rebuild from scratch
ceedling test:all
```

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Mock not found | Add header to `:test_[driver]:` `:includes:` |
| _IgnoreAndReturn undefined | Add `:ignore:` to `:cmock:` `:plugins:` |
| Coverage is 0% | Verify `:gcov:` section complete |
| Ceedling does nothing | Add `:plugins:` `:enabled:` section |
| Test not found | Rename to `test_*.c` |
| Segfault | Check NULL pointers, add create_mock_device() |
| Unexpected call | Add mock config to setUp() |
| Source not found | Fix `:paths:` `:source:` path |

## When All Else Fails

1. **Compare with working example**: `tests/drivers/power/max20370/`
2. **Start fresh**: Copy max20370/project.yml and adapt
3. **Clean build**: `ceedling clobber` then `ceedling test:all`
4. **Check paths**: All paths relative to project.yml location
5. **Verify Ruby/Ceedling version**: `ceedling version`

## Getting Help

When asking for help, provide:
1. Full error message
2. Relevant section of project.yml
3. Test file snippet
4. Ceedling version: `ceedling version`
5. Output of verbose run: `ceedling test:name --verbosity=obnoxious`
