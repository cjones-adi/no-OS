# Ceedling Configuration (project.yml)

Complete guide to creating and configuring `project.yml` for no-OS driver unit tests.

## CRITICAL Requirement

**Always use a complete, working project.yml** - Do not create from scratch or use minimal templates.

**Template Source**: Copy from `tests/drivers/power/max20370/project.yml`

## Complete Working Template

```yaml
---
:project:
  :use_exceptions: FALSE
  :use_test_preprocessor: :all
  :use_auxiliary_dependencies: TRUE
  :build_root: build
  :test_file_prefix: test_
  :which_ceedling: gem
  :ceedling_version: 1.0.1
  :default_tasks:
    - test:all

:environment:

:extension:
  :executable: .out

:paths:
  :test:
    - test
  :source:
    - ../../../../drivers/[subsystem]/[driver]
  :include:
    - ../../../../include
    - ../../../../drivers/[subsystem]/[driver]
  :support:
  :libraries: []

:files:
  :test:
    - test/*.c
  :source:
    - ../../../../drivers/[subsystem]/[driver]/*.c
  :support:

:defines:
  :common: &common_defines
    - TEST
  :test:
    - *common_defines
  :test_preprocess:
    - *common_defines

:cmock:
  :mock_prefix: mock_
  :when_no_prototypes: :warn
  :callback_include_count: TRUE
  :callback_after_arg_check: TRUE
  :enforce_strict_ordering: TRUE
  :plugins:
    - :ignore
    - :callback
  :treat_as:
    uint8_t:  HEX8
    uint16_t: HEX16
    uint32_t: UINT32
    int8_t:   INT8
    int16_t:  INT16
    int32_t:  INT32
    bool:     UINT8

:gcov:
  :html_report: TRUE
  :html_report_type: detailed
  :reports:
    - HtmlDetailed
  :gcovr:
    :html_medium_threshold: 75
    :html_high_threshold: 90
    :html_artifact_filename: coverage_report.html
    :report_root: "."
    :report_include: ".*[driver_name].*"
    :report_exclude: ".*test.*"
    :branches: TRUE
    :fail_under_line: 0
    :fail_under_branch: 0

:libraries:
  :placement: :end
  :flag: "-l${1}"
  :path_flag: "-L ${1}"
  :system: [m]
  :test: []
  :release: []

:junit_tests_report:
  :artifact_filename: report_junit.xml

:plugins:
  :enabled:
    - report_tests_pretty_stdout
    - module_generator
    - report_tests_raw_output_log
    - gcov
    - report_tests_log_factory

:flags:
  :test:
    :compile:
      :*:
        - -std=c99
        - -Wall
        - -Wextra
        - -Wno-unused-parameter
        - -Wno-missing-field-initializers
        - -g
        - -O0
        - -I../../../../include
        - -include no_os_alloc.h

:test_max20370:
  :compile:
    :includes:
      - ../../../../include/no_os_i2c.h
      - ../../../../include/no_os_gpio.h
      - ../../../../include/no_os_irq.h
      - ../../../../include/no_os_util.h
      - ../../../../include/no_os_alloc.h
```

## Critical Sections Explained

### :project Section

```yaml
:project:
  :use_exceptions: FALSE          # No C++ exceptions
  :use_test_preprocessor: :all    # Enable test preprocessing
  :use_auxiliary_dependencies: TRUE
  :build_root: build              # Output directory
  :test_file_prefix: test_        # Test file naming
  :which_ceedling: gem            # Use gem-installed Ceedling
  :ceedling_version: 1.0.1        # Lock version
```

**If missing**: Ceedling may fail silently or use wrong defaults

### :paths Section

```yaml
:paths:
  :test:
    - test                                    # Test files directory
  :source:
    - ../../../../drivers/power/max20370     # Driver source
  :include:
    - ../../../../include                    # no-OS headers
    - ../../../../drivers/power/max20370     # Driver headers
```

**Adjust paths** based on your driver location relative to `tests/drivers/[subsystem]/[driver]/`

### :cmock Section

```yaml
:cmock:
  :mock_prefix: mock_              # Mocks named mock_*.c
  :when_no_prototypes: :warn       # Warn if no prototypes
  :callback_include_count: TRUE    # Enable cmock_num_calls
  :callback_after_arg_check: TRUE
  :enforce_strict_ordering: TRUE
  :plugins:
    - :ignore                      # Enable _IgnoreAndReturn
    - :callback                    # Enable _Stub
  :treat_as:                       # Format output in hex
    uint8_t:  HEX8
    uint16_t: HEX16
    uint32_t: UINT32
```

**If missing `:plugins:`**: `_IgnoreAndReturn()` and `_Stub()` functions won't be generated

**If missing `:treat_as:`**: Hex values displayed as decimal in failures

### :gcov Section

```yaml
:gcov:
  :html_report: TRUE                    # Generate HTML report
  :html_report_type: detailed           # Detailed view
  :reports:
    - HtmlDetailed
  :gcovr:
    :html_medium_threshold: 75          # Yellow threshold
    :html_high_threshold: 90            # Green threshold
    :html_artifact_filename: coverage_report.html
    :report_root: "."
    :report_include: ".*[driver_name].*"  # Only driver files
    :report_exclude: ".*test.*"           # Exclude test files
    :branches: TRUE                       # Branch coverage
    :fail_under_line: 0                   # Don't fail (warn only)
    :fail_under_branch: 0
```

**If missing**: No coverage reports generated

### :plugins Section

```yaml
:plugins:
  :enabled:
    - report_tests_pretty_stdout    # Nice test output
    - module_generator              # Generate test templates
    - report_tests_raw_output_log   # Detailed logs
    - gcov                          # Coverage analysis
    - report_tests_log_factory      # Test logs
```

**If missing**: Silent failures, no reports, no coverage

### :flags Section

```yaml
:flags:
  :test:
    :compile:
      :*:
        - -std=c99                          # C99 standard
        - -Wall                             # All warnings
        - -Wextra                           # Extra warnings
        - -Wno-unused-parameter             # Allow unused params
        - -Wno-missing-field-initializers   # Allow partial init
        - -g                                # Debug symbols
        - -O0                               # No optimization
        - -I../../../../include             # no-OS headers
        - -include no_os_alloc.h            # Pre-include allocator
```

**If missing**: Compilation errors, warnings as errors

### :test_[driver_name] Section

```yaml
:test_max20370:
  :compile:
    :includes:
      - ../../../../include/no_os_i2c.h    # → mock_no_os_i2c.c/h
      - ../../../../include/no_os_gpio.h   # → mock_no_os_gpio.c/h
      - ../../../../include/no_os_irq.h    # → mock_no_os_irq.c/h
      - ../../../../include/no_os_util.h   # → mock_no_os_util.c/h
      - ../../../../include/no_os_alloc.h  # → mock_no_os_alloc.c/h
```

**CMock generates mocks from these headers automatically**

**Add headers for**:
- I2C driver: `no_os_i2c.h`
- SPI driver: `no_os_spi.h`
- GPIO usage: `no_os_gpio.h`
- Interrupts: `no_os_irq.h`
- Bit fields: `no_os_util.h`
- Memory: `no_os_alloc.h`

## Common Mistakes

1. **Creating from scratch** → Use max20370/project.yml as template
2. **Omitting `:plugins:`** → Silent build failures
3. **Missing `:flags:`** → Compile errors
4. **Incomplete `:cmock:`** → Mocks don't work
5. **Missing `:gcov:` details** → Coverage doesn't generate
6. **Wrong paths** → Source files not found
7. **Missing includes** → Mocks not generated for platform APIs

## Verification After Creating project.yml

```bash
# 1. Clean any stale configuration
ceedling clobber

# 2. Run tests - should compile and execute
ceedling test:all

# 3. Generate coverage - should produce HTML report
ceedling gcov:[driver_name]
```

If Ceedling fails silently, compare your project.yml with max20370/project.yml line-by-line.

## Customization Examples

### For SPI Driver

```yaml
:test_ad7124:
  :compile:
    :includes:
      - ../../../../include/no_os_spi.h    # SPI instead of I2C
      - ../../../../include/no_os_gpio.h
      - ../../../../include/no_os_util.h
      - ../../../../include/no_os_alloc.h
```

### For Multi-Interface Driver

```yaml
:test_multi_if:
  :compile:
    :includes:
      - ../../../../include/no_os_i2c.h    # I2C
      - ../../../../include/no_os_spi.h    # SPI
      - ../../../../include/no_os_uart.h   # UART
      - ../../../../include/no_os_gpio.h
      - ../../../../include/no_os_util.h
      - ../../../../include/no_os_alloc.h
```

### For Driver with Delay

```yaml
:test_sensor:
  :compile:
    :includes:
      - ../../../../include/no_os_i2c.h
      - ../../../../include/no_os_delay.h  # Add delay mock
      - ../../../../include/no_os_util.h
      - ../../../../include/no_os_alloc.h
```

## Troubleshooting

**Problem**: `ceedling test:all` does nothing
**Solution**: Check `:plugins:` section exists and includes required plugins

**Problem**: Mocks not generated
**Solution**: Verify `:test_[driver]:` `:includes:` lists all needed headers

**Problem**: Coverage report not generated
**Solution**: Check `:gcov:` section is complete with all sub-options

**Problem**: Compiler warnings cause failure
**Solution**: Add `-Wno-[warning]` flags to `:flags:` `:test:` `:compile:`

**Problem**: Source files not found
**Solution**: Verify `:paths:` `:source:` points to driver directory

## Summary

**Essential Sections**:
- `:project:` - Basic configuration
- `:paths:` - Source/test/include directories
- `:cmock:` with `:plugins:` - Mock generation
- `:gcov:` with `:gcovr:` - Coverage reports
- `:plugins:` - Test reporting and coverage
- `:flags:` - Compiler options
- `:test_[driver]:` `:includes:` - Headers to mock

**Always start from max20370/project.yml template** - it's complete and proven to work.

**Key Rule**: If Ceedling fails silently or mocks don't work, you're missing a section. Compare with template.
