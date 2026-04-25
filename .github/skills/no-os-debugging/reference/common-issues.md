# Common Debugging Issues and Solutions

Complete reference for common problems encountered when debugging no-OS embedded applications, with systematic troubleshooting steps.

---

## Device Detection Issues

### Scenario 1: Device Not Detected (ENODEV)

**Symptoms**:
```
[ERROR] ad4692.c:123 (ad4692_init): Product ID mismatch: expected 0x00C2, got 0xFFFF
Device initialization failed: -19
```

**Debug Steps**:

1. **Check return value is ENODEV**:
   ```c
   ret == -ENODEV  // or ret == -19
   ```

2. **Add register read logging**:
   ```c
   pr_debug("Reading product ID from register 0x%02X\n", PRODUCT_ID_REG);
   ret = device_reg_read(desc, PRODUCT_ID_REG, &id);
   pr_debug("Register read returned: %d, value: 0x%04X\n", ret, id);
   ```

3. **Check for 0xFF or 0x00** (indicates no communication):
   - `0xFFFF` or `0xFF`: SPI/I2C line stuck high
     - Check pull-ups
     - Verify connections
     - Check power supply
   - `0x0000` or `0x00`: Line stuck low
     - Check for shorts
     - Verify ground connection
     - Check power supply

4. **Verify hardware**:
   - Power supply voltage correct (measure with multimeter)
   - Ground connection solid
   - Chip select asserted (check with logic analyzer)
   - Clock signal present (check with oscilloscope or logic analyzer)

5. **Check SPI/I2C configuration**:
   - Correct mode, speed, address
   - Chip select pin correct
   - MOSI/MISO not swapped

---

### Product ID Verification Pattern

Every driver should verify product ID during initialization:

```c
int device_init(struct device_desc **device, struct device_init_param *init_param)
{
    struct device_desc *desc;
    uint16_t reg_val;
    int ret;

    // Allocate descriptor
    desc = no_os_calloc(1, sizeof(*desc));
    if (!desc)
        return -ENOMEM;

    // Initialize communication bus (SPI/I2C)
    ret = no_os_spi_init(&desc->spi_desc, init_param->spi_ip);
    if (ret) {
        pr_err("SPI initialization failed: %d\n", ret);
        goto error_desc;
    }

    // Read and verify product ID
    ret = device_reg_read(desc, PRODUCT_ID_REG, &reg_val);
    if (ret) {
        pr_err("Failed to read product ID: %d\n", ret);
        goto error_spi;
    }

    if (reg_val != expected_product_id[desc->id]) {
        pr_err("Product ID mismatch: expected 0x%04X, got 0x%04X\n",
               expected_product_id[desc->id], reg_val);
        ret = -ENODEV;
        goto error_spi;
    }

    pr_info("Device detected: ID 0x%04X\n", reg_val);

    *device = desc;
    return 0;

error_spi:
    no_os_spi_remove(desc->spi_desc);
error_desc:
    no_os_free(desc);
    return ret;
}
```

---

## Communication Bus Issues

### Scenario 2: SPI Communication Failure

**Symptoms**:
```
[ERROR] no_os_spi.c:89 (no_os_spi_write_and_read): SPI transfer failed
SPI transaction failed: -5
```

**Debug Steps**:

1. **Enable SPI debug logging**:
   ```c
   #define NO_OS_LOG_LEVEL NO_OS_LOG_DEBUG
   ```

2. **Check SPI parameters**:
   ```c
   pr_info("SPI: dev=%u, speed=%u, cs=%u, mode=%u\n",
           spi_ip->device_id, spi_ip->max_speed_hz,
           spi_ip->chip_select, spi_ip->mode);
   ```

3. **Reduce SPI speed** (test at lower speed):
   ```c
   spi_ip->max_speed_hz = 100000;  // 100 kHz (very slow, for testing)
   ```

4. **Try different SPI modes**:
   ```c
   // Try all 4 modes
   for (int mode = 0; mode < 4; mode++) {
       spi_ip->mode = mode;
       ret = test_spi_communication();
       pr_info("SPI mode %d: %s\n", mode, ret ? "FAIL" : "PASS");
   }
   ```

5. **Use logic analyzer**:
   - Verify clock signal present
   - Check data on MOSI/MISO
   - Confirm chip select timing
   - Verify correct CPOL/CPHA

**Common SPI Problems**:
1. Wrong SPI mode (CPOL/CPHA)
2. Chip select not configured
3. Clock frequency too high
4. Incorrect byte order
5. MOSI/MISO pins swapped

**SPI Mode Reference**:
```c
NO_OS_SPI_MODE_0  // CPOL=0, CPHA=0 (most common)
NO_OS_SPI_MODE_1  // CPOL=0, CPHA=1
NO_OS_SPI_MODE_2  // CPOL=1, CPHA=0
NO_OS_SPI_MODE_3  // CPOL=1, CPHA=1
```

---

### I2C Communication Issues

**Common I2C Problems**:
1. Wrong I2C address (7-bit vs 8-bit)
2. Missing pull-up resistors
3. Bus speed too high
4. Device stuck in reset

**Debug I2C Transactions**:
```c
int device_i2c_write(struct device_desc *desc, uint8_t reg, uint8_t data)
{
    int ret;
    uint8_t buf[2] = {reg, data};

    pr_debug("I2C write: addr=0x%02X, reg=0x%02X, data=0x%02X\n",
             desc->i2c_desc->slave_address, reg, data);

    ret = no_os_i2c_write(desc->i2c_desc, buf, 2, 1);
    if (ret) {
        pr_err("I2C write failed: %d (NACK or timeout)\n", ret);
        return ret;
    }

    return 0;
}
```

**Verify I2C Address**:
```c
// 7-bit address (most common)
i2c_ip->slave_address = 0x48;  // Not shifted

// If datasheet shows 8-bit address, shift right by 1
// 8-bit address: 0x90 → 7-bit: 0x48
i2c_ip->slave_address = 0x90 >> 1;
```

**Check Pull-up Resistors**:
```
Use multimeter to measure:
- SDA to VDD: Should be 2.2kΩ - 10kΩ
- SCL to VDD: Should be 2.2kΩ - 10kΩ

If open circuit (∞Ω): Missing pull-ups, add them
If ~0Ω: Short circuit, check wiring
```

---

### UART Communication Issues

**Common UART Problems**:
1. Baud rate mismatch
2. Wrong parity/stop bits
3. TX/RX pins swapped
4. Flow control misconfiguration

**Debug UART**:
```c
pr_debug("UART config: baud=%u, device=%u\n",
         uart_ip->baud_rate,
         uart_ip->device_id);

ret = no_os_uart_init(&uart, uart_ip);
if (ret) {
    // Can't use pr_err yet - no UART!
    // Need platform-specific debugging (JTAG, LED blink, etc.)
    return ret;
}
```

**UART Loopback Test**:
```c
const char *test_msg = "UART test\n";
ret = no_os_uart_write(uart, (uint8_t *)test_msg, strlen(test_msg));
if (ret) {
    pr_err("UART write failed: %d\n", ret);
}
```

---

## Initialization Issues

### Scenario 3: Initialization Hangs or Crashes

**Symptoms**:
- Application stops responding during init
- No console output after certain point
- Reset loop

**Debug Steps**:

1. **Add initialization checkpoints**:
   ```c
   pr_info("Checkpoint 1: Starting init\n");
   ret = step1_init();
   pr_info("Checkpoint 2: Step 1 complete\n");
   ret = step2_init();
   pr_info("Checkpoint 3: Step 2 complete\n");
   // Find where it stops
   ```

2. **Check for NULL pointer dereference**:
   ```c
   if (!desc) {
       pr_err("Descriptor is NULL!\n");
       return -EINVAL;
   }
   
   if (!desc->spi_desc) {
       pr_err("SPI descriptor is NULL!\n");
       return -EINVAL;
   }
   ```

3. **Verify memory allocation**:
   ```c
   desc = no_os_calloc(1, sizeof(*desc));
   if (!desc) {
       pr_err("Memory allocation failed\n");
       return -ENOMEM;
   }
   pr_debug("Allocated %zu bytes at %p\n", sizeof(*desc), (void*)desc);
   ```

4. **Use JTAG debugger**:
   - Set breakpoint at suspected location
   - Step through code
   - Inspect variable values
   - Check stack trace on crash

**Common Causes**:
- NULL pointer dereference
- Stack overflow
- Memory allocation failure
- Uninitialized variables
- Missing platform initialization
- Infinite loop

---

## Data Reading Issues

### Scenario 4: Incorrect Data Readings

**Symptoms**:
- Data values don't match expected range
- All zeros or all ones
- Random/noisy data

**Debug Steps**:

1. **Verify register read sequence**:
   ```c
   pr_debug("Reading data register 0x%02X\n", DATA_REG);
   ret = device_reg_read(desc, DATA_REG, &data);
   pr_debug("Raw data: 0x%08X (%u)\n", data, data);
   ```

2. **Check bit shifting and masking**:
   ```c
   uint32_t raw = 0x12345678;
   uint16_t extracted = (raw >> 8) & 0xFFFF;
   pr_debug("Extract: raw=0x%08X → extracted=0x%04X\n", raw, extracted);
   ```

3. **Verify configuration registers**:
   ```c
   // Read back configuration to verify write succeeded
   ret = device_reg_write(desc, CONFIG_REG, config_val);
   ret = device_reg_read(desc, CONFIG_REG, &readback);
   if (readback != config_val) {
       pr_err("Config mismatch: wrote 0x%04X, read 0x%04X\n",
              config_val, readback);
   }
   ```

4. **Test with known values**:
   ```c
   // Apply known input (e.g., reference voltage)
   // Check if reading matches expected value
   pr_info("Expected: %u, Actual: %u, Error: %d\n",
           expected, actual, (int)(actual - expected));
   ```

**Common Causes**:
- Wrong bit order (MSB vs LSB)
- Incorrect bit shifting
- Sign extension issues
- Configuration not applied
- Wrong register address
- Data not ready (conversion incomplete)

---

## Timing Issues

### Scenario 5: Timing Issues

**Symptoms**:
- Intermittent failures
- Works at slow speed, fails at high speed
- Timeout errors

**Debug Steps**:

1. **Add timing measurements**:
   ```c
   #define PRINT_TIME
   #include "no_os_print_log.h"

   pr_info("Starting operation\n");
   ret = long_operation();
   pr_info("Operation complete\n");
   // Timestamps show duration
   ```

2. **Add delays for testing**:
   ```c
   ret = device_write_config(desc, config);
   no_os_mdelay(10);  // Add delay to test if timing issue
   ret = device_read_data(desc, &data);
   ```

3. **Check datasheet timing requirements**:
   - Setup time, hold time
   - Power-up delays
   - Conversion time
   - Communication timing

4. **Increase timeout values**:
   ```c
   // If using polling
   uint32_t timeout = 1000;  // Increase for testing
   while (timeout-- && !ready()) {
       no_os_udelay(100);
   }
   if (!timeout) {
       pr_err("Timeout waiting for ready\n");
       return -ETIMEDOUT;
   }
   ```

**Common Causes**:
- Missing required delays
- Timeout too short
- Clock frequency too high
- Bus speed exceeds device capability
- Setup/hold time violations

---

## Error Code Reference

### Standard Error Codes

Common error codes from `no_os_error.h`:

```c
EINVAL      // -22: Invalid argument or parameter
EIO         // -5:  Input/output error (communication failure)
ENOMEM      // -12: Out of memory
ENODEV      // -19: No such device (device not found)
ENOTSUPP    // -524: Operation not supported
ETIMEDOUT   // -110: Timeout occurred
EBUSY       // -16: Device or resource busy
```

**Custom Error Code**:
```c
NO_OS_EOVERRUN  // -2001: Circular buffer overrun
```

---

### Error Code Meanings in Context

**EINVAL** (Invalid Argument):
- Invalid parameter passed to function
- Register value out of acceptable range
- Configuration parameter not supported by hardware
- NULL pointer where valid pointer expected

**Example**:
```c
ret = ad4692_set_channel(dev, 99);  // Channel out of range
if (ret == -EINVAL) {
    pr_err("Invalid channel number\n");
}
```

**ENODEV** (No Such Device):
- Device not responding on SPI/I2C bus
- Product ID mismatch (wrong device or connection issue)
- Device not powered or in reset

**EIO** (Input/Output Error):
- SPI/I2C transaction failed
- Communication timeout
- Bus error or NACK received

**ENOMEM** (Out of Memory):
- Dynamic allocation failed (`no_os_malloc()`, `no_os_calloc()`)
- Insufficient heap space

**ENOTSUPP** (Not Supported):
- Feature not implemented for this device variant
- Platform doesn't support requested operation

---

## Memory Issues

### Memory Allocation Failures

**Symptoms**:
```
[ERROR] Device initialization failed: -12
Memory allocation failed
```

**Debug Steps**:
```c
desc = no_os_calloc(1, sizeof(*desc));
if (!desc) {
    pr_err("Failed to allocate %zu bytes\n", sizeof(*desc));
    return -ENOMEM;
}
pr_debug("Allocated descriptor at %p\n", (void*)desc);
```

**Common Causes**:
- Heap size too small
- Memory leak (previous allocations not freed)
- Fragmentation
- Stack/heap collision

**Solutions**:
- Increase heap size in linker script
- Check for memory leaks (verify all `no_os_free()` calls)
- Use static allocation if dynamic not needed

---

### Stack Overflow

**Symptoms**:
- Random crashes
- Variables corrupted
- Hard fault

**Debug Steps**:
- Check stack usage in linker map
- Reduce local variable sizes
- Move large buffers to heap or static
- Increase stack size in linker script

---

## Configuration Issues

### Wrong Platform Configuration

**Symptoms**:
- Initialization fails with platform-specific errors
- GPIO/SPI/I2C not working

**Maxim Platform**:
```c
#include "mxc_device.h"
#include "mxc_sys.h"

pr_debug("Initializing GPIO port %u, pin %u\n", port, pin);
pr_debug("SPI%d configuration: speed=%u, mode=%u\n",
         spi_desc->device_id,
         spi_desc->max_speed_hz,
         spi_desc->mode);
```

**Mbed Platform**:
```c
// Runtime platform configuration needed
device_ip.spi_ip = spi_ip;  // Set before init

pr_debug("Mbed platform: assigning SPI instance\n");
```

---

## Build Issues

### Missing Debug Symbols

**Problem**: Can't debug effectively without symbols.

**Solution**:
```makefile
# Add to Makefile
CFLAGS += -g3 -O0
```

### Optimizations Interfere with Debugging

**Problem**: Code behaves differently with optimizations.

**Solution**:
```makefile
# Disable optimizations for debugging
CFLAGS += -O0
```

### Warnings Not Enabled

**Problem**: Missing potential bugs.

**Solution**:
```makefile
CFLAGS += -Wall -Wextra -Wpedantic
CFLAGS += -Wformat=2
CFLAGS += -Wno-unused-parameter
```
