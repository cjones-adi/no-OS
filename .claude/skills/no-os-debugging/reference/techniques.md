# Advanced Debugging Techniques

Advanced debugging patterns, error handling strategies, and systematic approaches for debugging no-OS embedded applications.

---

## Error Handling Patterns

### Error Propagation Pattern

**Universal Pattern** (used throughout no-OS drivers):
```c
int function_that_can_fail(void)
{
    int ret;

    ret = sub_function_1();
    if (ret)
        return ret;  // Propagate error up

    ret = sub_function_2();
    if (ret)
        goto error_cleanup;  // Cleanup before return

    ret = sub_function_3();
    if (ret)
        goto error_cleanup;

    return 0;  // Success

error_cleanup:
    cleanup_resources();
    return ret;  // Return error code
}
```

**Key Principles**:
- Check return value after **every** function call
- Return immediately on error (fail-fast)
- Use `goto` for cleanup when resources allocated
- Return `0` on success, negative error code on failure

---

### Error Handling Helpers

**Pointer-Based Error Handling**:
```c
#include "no_os_error.h"

// Check if pointer contains an error
if (NO_OS_IS_ERR(ptr)) {
    int err = NO_OS_PTR_ERR(ptr);
    pr_err("Error: %d\n", err);
}

// Encode error as pointer
void *err_ptr = NO_OS_ERR_PTR(-EINVAL);

// Cast error value
int err = NO_OS_ERR_CAST(ptr);
```

---

### Defensive Programming

**NULL Pointer Checks**:
```c
int device_operation(struct device_desc *desc, uint32_t *data)
{
    // Validate all pointers
    if (!desc) {
        pr_err("Device descriptor is NULL\n");
        return -ENODEV;
    }

    if (!desc->comm_desc) {
        pr_err("Communication descriptor is NULL\n");
        return -EINVAL;
    }

    if (!data) {
        pr_err("Data pointer is NULL\n");
        return -EINVAL;
    }

    // Safe to use now
    return device_read(desc, data);
}
```

**Range Validation**:
```c
int device_set_channel(struct device_desc *desc, uint8_t channel)
{
    if (!desc)
        return -ENODEV;

    if (channel >= MAX_CHANNELS) {
        pr_err("Invalid channel %u (max %u)\n", channel, MAX_CHANNELS - 1);
        return -EINVAL;
    }

    return device_write_channel(desc, channel);
}
```

---

## Systematic Debug Approaches

### Binary Search Debugging

When you have a large code section and don't know where failure occurs:

```c
pr_info("DEBUG: Section 1 start\n");
// ... lots of code ...

pr_info("DEBUG: Section 1 middle\n");  // Add checkpoint in middle
// ... more code ...

pr_info("DEBUG: Section 1 end\n");

// If failure between "start" and "middle":
//   - Remove "middle" checkpoint
//   - Add checkpoint at 1/4 point
//   - Repeat until isolated
```

**Process**:
1. Add checkpoint at middle of suspected region
2. If failure before checkpoint: search first half
3. If failure after checkpoint: search second half
4. Repeat until isolated to single function/line

---

### State Dumping

Dump complete device state when error occurs:

```c
void dump_device_state(struct device_desc *desc)
{
    uint16_t reg_val;
    
    pr_info("=== Device State Dump ===\n");
    
    device_reg_read(desc, STATUS_REG, &reg_val);
    pr_info("Status:  0x%04X\n", reg_val);
    
    device_reg_read(desc, CONFIG_REG, &reg_val);
    pr_info("Config:  0x%04X\n", reg_val);
    
    device_reg_read(desc, CONTROL_REG, &reg_val);
    pr_info("Control: 0x%04X\n", reg_val);
    
    pr_info("========================\n");
}

// Use when error occurs
ret = device_operation(desc);
if (ret) {
    dump_device_state(desc);
    return ret;
}
```

---

### Comparative Debugging

Compare working vs. non-working configurations:

```c
// Working configuration
pr_info("WORKING: speed=%u, mode=%u, cs=%u\n",
        working_spi->max_speed_hz,
        working_spi->mode,
        working_spi->chip_select);

// Non-working configuration
pr_info("FAILING: speed=%u, mode=%u, cs=%u\n",
        failing_spi->max_speed_hz,
        failing_spi->mode,
        failing_spi->chip_select);

// Look for differences
```

---

### Incremental Testing

Test each feature in isolation before combining:

```c
int test_device_incremental(void)
{
    int ret;

    // Test 1: Basic init
    pr_info("Test 1: Basic initialization\n");
    ret = device_init_minimal(&dev);
    if (ret) {
        pr_err("Test 1 FAILED\n");
        return ret;
    }
    pr_info("Test 1 PASSED\n");

    // Test 2: Register access
    pr_info("Test 2: Register access\n");
    ret = device_test_register_access(dev);
    if (ret) {
        pr_err("Test 2 FAILED\n");
        return ret;
    }
    pr_info("Test 2 PASSED\n");

    // Test 3: Configuration
    pr_info("Test 3: Configuration\n");
    ret = device_configure(dev);
    if (ret) {
        pr_err("Test 3 FAILED\n");
        return ret;
    }
    pr_info("Test 3 PASSED\n");

    // Test 4: Data acquisition
    pr_info("Test 4: Data acquisition\n");
    ret = device_test_data_acquisition(dev);
    if (ret) {
        pr_err("Test 4 FAILED\n");
        return ret;
    }
    pr_info("Test 4 PASSED\n");

    pr_info("All tests PASSED\n");
    return 0;
}
```

---

## Advanced Logging Techniques

### Conditional Logging

Log only when specific conditions met:

```c
#define DEBUG_CHANNEL 3  // Only debug channel 3

int device_read_channel(struct device_desc *desc, uint8_t channel, uint32_t *data)
{
    int ret;

    if (channel == DEBUG_CHANNEL) {
        pr_debug("Reading channel %u\n", channel);
    }

    ret = device_read(desc, channel, data);

    if (channel == DEBUG_CHANNEL) {
        pr_debug("Channel %u: data=0x%08X, ret=%d\n", channel, *data, ret);
    }

    return ret;
}
```

---

### Rate-Limited Logging

Prevent log spam in loops:

```c
void process_data_stream(void)
{
    static uint32_t log_count = 0;
    uint32_t data;

    while (1) {
        ret = device_read_data(&data);

        // Log every 1000th sample
        if (log_count++ % 1000 == 0) {
            pr_info("Sample %u: data=0x%08X\n", log_count, data);
        }

        process_sample(data);
    }
}
```

---

### Trace Logging

Track function entry/exit:

```c
#define TRACE_ENTRY() pr_debug("→ %s\n", __func__)
#define TRACE_EXIT(ret) pr_debug("← %s: %d\n", __func__, ret)

int device_operation(struct device_desc *desc)
{
    int ret;

    TRACE_ENTRY();

    ret = perform_operation(desc);
    if (ret) {
        TRACE_EXIT(ret);
        return ret;
    }

    TRACE_EXIT(0);
    return 0;
}
```

**Output**:
```
→ device_operation
  → perform_operation
  ← perform_operation: 0
← device_operation: 0
```

---

### Statistical Logging

Track success/failure rates:

```c
struct operation_stats {
    uint32_t total;
    uint32_t success;
    uint32_t failures;
};

static struct operation_stats stats = {0};

int monitored_operation(void)
{
    int ret;

    stats.total++;

    ret = device_operation();

    if (ret) {
        stats.failures++;
        pr_err("Operation failed: %d (failure rate: %.2f%%)\n",
               ret,
               100.0 * stats.failures / stats.total);
    } else {
        stats.success++;
    }

    // Periodic summary
    if (stats.total % 1000 == 0) {
        pr_info("Stats: total=%u, success=%u, failures=%u (%.2f%% success)\n",
                stats.total, stats.success, stats.failures,
                100.0 * stats.success / stats.total);
    }

    return ret;
}
```

---

## Performance Debugging

### Timing Analysis

Measure operation duration:

```c
#include "no_os_timer.h"

uint32_t measure_operation_time(void)
{
    uint32_t start, end, duration;

    start = no_os_timer_get_count();

    perform_operation();

    end = no_os_timer_get_count();
    duration = end - start;  // In timer ticks

    pr_info("Operation took %u ticks\n", duration);

    return duration;
}
```

**With timestamps**:
```c
#define PRINT_TIME
#include "no_os_print_log.h"

pr_info("Operation start\n");
// [123.456789] Operation start

perform_long_operation();

pr_info("Operation end\n");
// [125.789012] Operation end
// Duration: 125.789012 - 123.456789 = 2.332 seconds
```

---

### Bottleneck Identification

Find slowest operations:

```c
void profile_operations(void)
{
    uint32_t t1, t2, t3, t4;

    t1 = no_os_timer_get_count();
    operation1();
    
    t2 = no_os_timer_get_count();
    operation2();
    
    t3 = no_os_timer_get_count();
    operation3();
    
    t4 = no_os_timer_get_count();

    pr_info("Operation 1: %u ticks\n", t2 - t1);
    pr_info("Operation 2: %u ticks\n", t3 - t2);
    pr_info("Operation 3: %u ticks\n", t4 - t3);
    pr_info("Total:       %u ticks\n", t4 - t1);
}
```

---

## Memory Debugging

### Memory Leak Detection

Track allocations and frees:

```c
#ifdef DEBUG_MEMORY
static uint32_t alloc_count = 0;
static uint32_t free_count = 0;

void *debug_malloc(size_t size, const char *file, int line)
{
    void *ptr = no_os_malloc(size);
    if (ptr) {
        alloc_count++;
        pr_debug("ALLOC %zu bytes at %p (%s:%d) [total: %u]\n",
                 size, ptr, file, line, alloc_count - free_count);
    }
    return ptr;
}

void debug_free(void *ptr, const char *file, int line)
{
    if (ptr) {
        free_count++;
        pr_debug("FREE %p (%s:%d) [total: %u]\n",
                 ptr, file, line, alloc_count - free_count);
        no_os_free(ptr);
    }
}

#define no_os_malloc(size) debug_malloc(size, __FILE__, __LINE__)
#define no_os_free(ptr) debug_free(ptr, __FILE__, __LINE__)
#endif
```

---

### Buffer Overflow Detection

Guard bytes around buffers:

```c
#define GUARD_BYTE 0xAA

uint8_t *create_guarded_buffer(size_t size)
{
    // Allocate extra space for guards
    uint8_t *buf = no_os_malloc(size + 2);
    if (!buf)
        return NULL;

    buf[0] = GUARD_BYTE;           // Pre-guard
    buf[size + 1] = GUARD_BYTE;    // Post-guard

    return &buf[1];  // Return pointer to usable area
}

void check_buffer_guards(uint8_t *buf, size_t size)
{
    uint8_t *real_buf = buf - 1;

    if (real_buf[0] != GUARD_BYTE) {
        pr_err("Buffer underflow detected!\n");
    }

    if (real_buf[size + 1] != GUARD_BYTE) {
        pr_err("Buffer overflow detected!\n");
    }
}
```

---

## Communication Protocol Debugging

### Transaction Logging

Log all bus transactions:

```c
int debug_spi_write_and_read(struct no_os_spi_desc *desc,
                              uint8_t *data, uint16_t bytes_number)
{
    int ret;

    pr_debug("SPI TX [%u bytes]: ", bytes_number);
    for (uint16_t i = 0; i < bytes_number; i++) {
        pr_debug("%02X ", data[i]);
    }
    pr_debug("\n");

    ret = no_os_spi_write_and_read(desc, data, bytes_number);

    pr_debug("SPI RX [%u bytes]: ", bytes_number);
    for (uint16_t i = 0; i < bytes_number; i++) {
        pr_debug("%02X ", data[i]);
    }
    pr_debug(" (ret=%d)\n", ret);

    return ret;
}
```

---

### Protocol State Machine Debugging

Track protocol state:

```c
enum protocol_state {
    STATE_IDLE,
    STATE_CMD_SENT,
    STATE_WAIT_RESPONSE,
    STATE_DATA_TRANSFER,
    STATE_ERROR
};

static enum protocol_state current_state = STATE_IDLE;

const char *state_name(enum protocol_state state)
{
    static const char *names[] = {
        "IDLE", "CMD_SENT", "WAIT_RESPONSE", "DATA_TRANSFER", "ERROR"
    };
    return names[state];
}

void set_state(enum protocol_state new_state)
{
    pr_debug("State: %s → %s\n", state_name(current_state), state_name(new_state));
    current_state = new_state;
}
```

---

## Regression Detection

### Known-Good Value Testing

Test against known-good values:

```c
struct test_vector {
    const char *name;
    uint16_t input;
    uint32_t expected_output;
};

static const struct test_vector test_vectors[] = {
    {"Zero input", 0, 0},
    {"Mid-range", 0x8000, 2048000},
    {"Full-scale", 0xFFFF, 4096000},
};

int run_regression_tests(struct device_desc *desc)
{
    int ret;
    uint32_t output;

    for (size_t i = 0; i < NO_OS_ARRAY_SIZE(test_vectors); i++) {
        pr_info("Test: %s\n", test_vectors[i].name);

        ret = device_set_input(desc, test_vectors[i].input);
        if (ret) {
            pr_err("  FAILED: set_input returned %d\n", ret);
            return ret;
        }

        ret = device_get_output(desc, &output);
        if (ret) {
            pr_err("  FAILED: get_output returned %d\n", ret);
            return ret;
        }

        if (output != test_vectors[i].expected_output) {
            pr_err("  FAILED: expected %u, got %u\n",
                   test_vectors[i].expected_output, output);
            return -EIO;
        }

        pr_info("  PASSED\n");
    }

    pr_info("All regression tests PASSED\n");
    return 0;
}
```

---

## Debug Build Configurations

### Multiple Debug Levels

```c
// debug_config.h
#define DEBUG_LEVEL_NONE    0
#define DEBUG_LEVEL_ERRORS  1
#define DEBUG_LEVEL_INFO    2
#define DEBUG_LEVEL_VERBOSE 3

#ifndef DEBUG_LEVEL
#define DEBUG_LEVEL DEBUG_LEVEL_INFO
#endif

#if DEBUG_LEVEL >= DEBUG_LEVEL_ERRORS
#define DEBUG_ERR(fmt, ...) pr_err(fmt, ##__VA_ARGS__)
#else
#define DEBUG_ERR(fmt, ...)
#endif

#if DEBUG_LEVEL >= DEBUG_LEVEL_INFO
#define DEBUG_INFO(fmt, ...) pr_info(fmt, ##__VA_ARGS__)
#else
#define DEBUG_INFO(fmt, ...)
#endif

#if DEBUG_LEVEL >= DEBUG_LEVEL_VERBOSE
#define DEBUG_VERBOSE(fmt, ...) pr_debug(fmt, ##__VA_ARGS__)
#else
#define DEBUG_VERBOSE(fmt, ...)
#endif
```

**Makefile**:
```makefile
# Development build (verbose)
CFLAGS += -DDEBUG_LEVEL=3

# Testing build (info only)
CFLAGS += -DDEBUG_LEVEL=2

# Production build (errors only)
CFLAGS += -DDEBUG_LEVEL=1
```

---

## Debugging Checklist

### Before Starting Debug Session

- [ ] Enable debug logging (`NO_OS_LOG_LEVEL=DEBUG`)
- [ ] Enable debug symbols (`-g3 -O0`)
- [ ] UART console working (or JTAG available)
- [ ] Error checking after all function calls
- [ ] Known-good baseline for comparison

### During Debugging

- [ ] Reproduce issue consistently
- [ ] Add logging at suspected failure points
- [ ] Verify hardware (power, connections, signals)
- [ ] Check error codes and their meanings
- [ ] Compare working vs. non-working configurations
- [ ] Use binary search to isolate issue
- [ ] Verify assumptions with actual measurements

### After Finding Issue

- [ ] Document root cause
- [ ] Add defensive checks to prevent recurrence
- [ ] Add test case to regression suite
- [ ] Review similar code for same issue
- [ ] Update documentation if needed
