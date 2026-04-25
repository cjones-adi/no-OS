# I2C Best Practices

This document provides best practices for using I2C in no-OS embedded systems.

## Communication Best Practices

### 1. Always Use Repeated Start for Read-After-Write

**Good - Repeated Start:**
```c
// Single atomic transaction
no_os_i2c_write(i2c, &reg_addr, 1, 0);  // No stop
no_os_i2c_read(i2c, data, len, 1);       // Stop after read
```

**Less Efficient - Separate Transactions:**
```c
// Two separate transactions - releases bus
no_os_i2c_write(i2c, &reg_addr, 1, 1);  // Stop
no_os_i2c_read(i2c, data, len, 1);       // Stop
```

**Why repeated start is better:**
- Faster (no bus setup/teardown overhead)
- Atomic operation (prevents other masters from interfering)
- Required by some devices (won't work with separate transactions)
- More reliable in multi-master systems

### 2. Always Check Return Values

**Good:**
```c
int32_t ret;

ret = no_os_i2c_write(i2c, data, len, 1);
if (ret) {
    pr_err("I2C write failed: %d\n", ret);
    return ret;
}

ret = no_os_i2c_read(i2c, buffer, len, 1);
if (ret) {
    pr_err("I2C read failed: %d\n", ret);
    return ret;
}
```

**Bad:**
```c
// Ignoring errors - device may not respond
no_os_i2c_write(i2c, data, len, 1);
no_os_i2c_read(i2c, buffer, len, 1);
```

**Why:**
- I2C devices can NACK (not acknowledge)
- Bus arbitration can fail in multi-master systems
- Wiring issues can cause communication failures
- Early error detection prevents cascading failures

### 3. Verify Slave Address Format

**Good - 7-bit address:**
```c
.slave_address = 0x48,  // 7-bit address
```

**Bad - 8-bit R/W format:**
```c
.slave_address = 0x90,  // Wrong! This is 8-bit (0x48 << 1)
```

**Why:**
- no-OS uses 7-bit addressing
- Hardware automatically adds R/W bit
- Using 8-bit format causes wrong address (0x90 >> 1 = 0x48, but LSB creates issues)

**How to convert datasheet address:**
```c
// Datasheet says "I2C address: 0x90 (write), 0x91 (read)"
// This is 8-bit format with R/W bit included
// 7-bit address = 0x90 >> 1 = 0x48
.slave_address = 0x48,  // Use 7-bit address
```

### 4. Start with Lower Speeds for Debugging

**Good - Debugging:**
```c
.max_speed_hz = 100000,  // 100 kHz for initial testing
```

**Good - Production (after verified):**
```c
.max_speed_hz = 400000,  // 400 kHz for normal operation
```

**Why:**
- Lower speeds more forgiving of electrical issues
- Easier to debug with logic analyzer
- Pull-up resistor tolerance wider
- Cable length less critical

**Recommended progression:**
1. Start at 100 kHz - verify basic communication
2. Test at 400 kHz - check for errors
3. Try 1 MHz if needed - monitor for reliability

### 5. Handle Bus Errors Gracefully

**Good:**
```c
int32_t ret;
uint8_t retries = 3;

for (uint8_t i = 0; i < retries; i++) {
    ret = no_os_i2c_read(i2c, data, len, 1);
    if (ret == 0)
        return 0;  // Success
    
    // Brief delay before retry
    no_os_mdelay(10);
}

pr_err("I2C read failed after %d retries\n", retries);
return ret;
```

**Consider:**
- Not all errors should retry (EINVAL = parameter error)
- Some errors recoverable (EAGAIN, EBUSY)
- Bus lockup may require reset

### 6. Use Mutex for Shared Bus in Multi-threaded Environments

**Already handled by no-OS:**
```c
// Bus mutex automatically managed
no_os_i2c_write(i2c_desc, data, len, 1);
```

**If implementing custom platform:**
```c
int32_t platform_i2c_write(...)
{
    no_os_mutex_lock(desc->bus->mutex);
    ret = hal_i2c_transmit(...);
    no_os_mutex_unlock(desc->bus->mutex);
    return ret;
}
```

### 7. Verify Pull-up Resistors

**Standard mode (100 kHz):**
- Use 4.7 kΩ pull-ups
- Works with long wires and many devices

**Fast mode (400 kHz):**
- Use 2.2 kΩ pull-ups
- Most common configuration

**Fast mode plus (1 MHz):**
- Use 1.0 kΩ pull-ups
- May require active pull-ups for high capacitance

**Too strong (too low resistance):**
- Excessive current when bus is low
- Wastes power
- May violate VOL specifications

**Too weak (too high resistance):**
- Slow rise times
- Unreliable communication
- May not reach VIH threshold

### 8. Account for Bus Capacitance

**Capacitance sources:**
- PCB trace: ~1-2 pF/cm
- Device input: 5-10 pF per device
- Connectors: 2-5 pF each

**Limits:**
- Standard/Fast mode: 400 pF max
- Fast+ mode: 550 pF max

**If exceeded:**
- Reduce wire length
- Use fewer devices
- Add I2C buffer/repeater
- Reduce speed
- Use stronger pull-ups

### 9. Avoid Clock Stretching Issues

**Clock stretching:**
- Slave holds SCL low to slow master
- Not all platforms support it well
- Can cause timeouts

**Solutions:**
```c
// Platform-specific timeout configuration
struct platform_i2c_extra {
    uint32_t timeout_ms;  // Increase if clock stretching needed
};
```

**Or:**
- Use devices that don't require clock stretching
- Ensure platform supports clock stretching
- Increase I2C timeout values

### 10. Free Resources Properly

**Good:**
```c
struct no_os_i2c_desc *i2c;

ret = no_os_i2c_init(&i2c, &init_param);
if (ret)
    return ret;

// ... use I2C ...

// Always cleanup
ret = no_os_i2c_remove(i2c);
```

**Error handling:**
```c
ret = no_os_i2c_init(&i2c, &init_param);
if (ret)
    return ret;

ret = device_operation(i2c);
if (ret)
    goto error;

// Normal cleanup
no_os_i2c_remove(i2c);
return 0;

error:
    no_os_i2c_remove(i2c);
    return ret;
```

## Design Best Practices

### 1. Organize Device-Specific Functions

**Good structure:**
```c
// Device-specific I2C helpers
static int32_t device_read_reg(struct device_desc *dev, uint8_t reg,
                                uint8_t *val)
{
    no_os_i2c_write(dev->i2c, &reg, 1, 0);
    return no_os_i2c_read(dev->i2c, val, 1, 1);
}

static int32_t device_write_reg(struct device_desc *dev, uint8_t reg,
                                 uint8_t val)
{
    uint8_t data[2] = {reg, val};
    return no_os_i2c_write(dev->i2c, data, 2, 1);
}

// Public API uses helpers
int32_t device_set_mode(struct device_desc *dev, enum mode mode)
{
    return device_write_reg(dev, MODE_REG, mode);
}

int32_t device_get_status(struct device_desc *dev, uint8_t *status)
{
    return device_read_reg(dev, STATUS_REG, status);
}
```

### 2. Centralize Register Definitions

**Good:**
```c
// device_regs.h
#define DEVICE_REG_CHIP_ID    0x00
#define DEVICE_REG_CONFIG     0x01
#define DEVICE_REG_STATUS     0x02
#define DEVICE_REG_DATA       0x10

// Config register bits
#define DEVICE_CONFIG_ENABLE  (1 << 0)
#define DEVICE_CONFIG_MODE    (0x3 << 1)
#define DEVICE_CONFIG_RESET   (1 << 7)
```

### 3. Implement Chip ID Verification

**Good:**
```c
int32_t device_init(struct device_desc **device,
                    struct device_init_param *init_param)
{
    int32_t ret;
    uint8_t chip_id;
    
    // ... initialization ...
    
    // Verify device is present and correct
    ret = device_read_reg(*device, CHIP_ID_REG, &chip_id);
    if (ret)
        goto error;
    
    if (chip_id != EXPECTED_CHIP_ID) {
        pr_err("Wrong chip ID: 0x%02X (expected 0x%02X)\n",
               chip_id, EXPECTED_CHIP_ID);
        ret = -ENODEV;
        goto error;
    }
    
    return 0;

error:
    no_os_i2c_remove((*device)->i2c);
    free(*device);
    *device = NULL;
    return ret;
}
```

### 4. Use Bit Manipulation Helpers

**Good:**
```c
// Read-modify-write helper
static int32_t device_update_reg(struct device_desc *dev, uint8_t reg,
                                  uint8_t mask, uint8_t val)
{
    int32_t ret;
    uint8_t current;
    
    ret = device_read_reg(dev, reg, &current);
    if (ret)
        return ret;
    
    current = (current & ~mask) | (val & mask);
    
    return device_write_reg(dev, reg, current);
}

// Usage
ret = device_update_reg(dev, CONFIG_REG,
                        DEVICE_CONFIG_MODE,
                        MODE_CONTINUOUS << 1);
```

### 5. Handle Multi-byte Values Consistently

**Good - Always specify endianness:**
```c
// Big-endian device
int32_t device_read_u16_be(struct device_desc *dev, uint8_t reg,
                           uint16_t *val)
{
    int32_t ret;
    uint8_t data[2];
    
    ret = device_read_burst(dev, reg, data, 2);
    if (ret)
        return ret;
    
    *val = (data[0] << 8) | data[1];  // MSB first
    return 0;
}

// Little-endian device
int32_t device_read_u16_le(struct device_desc *dev, uint8_t reg,
                           uint16_t *val)
{
    int32_t ret;
    uint8_t data[2];
    
    ret = device_read_burst(dev, reg, data, 2);
    if (ret)
        return ret;
    
    *val = data[0] | (data[1] << 8);  // LSB first
    return 0;
}
```

### 6. Provide Meaningful Error Messages

**Good:**
```c
ret = no_os_i2c_init(&dev->i2c, &i2c_init);
if (ret) {
    pr_err("%s: Failed to initialize I2C: %d\n", __func__, ret);
    return ret;
}

ret = device_read_reg(dev, CHIP_ID_REG, &chip_id);
if (ret) {
    pr_err("%s: Failed to read chip ID: %d\n", __func__, ret);
    goto error_i2c;
}

if (chip_id != EXPECTED_CHIP_ID) {
    pr_err("%s: Invalid chip ID 0x%02X (expected 0x%02X)\n",
           __func__, chip_id, EXPECTED_CHIP_ID);
    ret = -ENODEV;
    goto error_i2c;
}
```

## Testing Best Practices

### 1. Test with I2C Scanner

```c
void i2c_scan_bus(struct no_os_i2c_desc *i2c)
{
    uint8_t dummy;
    struct no_os_i2c_desc temp = *i2c;
    
    pr_info("Scanning I2C bus %d:\n", i2c->device_id);
    
    for (uint8_t addr = 0x08; addr < 0x78; addr++) {
        temp.slave_address = addr;
        
        if (no_os_i2c_read(&temp, &dummy, 0, 1) == 0) {
            pr_info("  Device found at 0x%02X\n", addr);
        }
    }
}
```

### 2. Verify Timing with Logic Analyzer

**Check:**
- SCL frequency matches configured speed
- Rise times within spec (<1000ns for 100kHz, <300ns for 400kHz)
- No glitches on SDA during SCL high
- ACK/NACK signals correct
- Repeated start vs stop conditions

### 3. Test Edge Cases

```c
// Test NULL pointer handling
ret = device_init(NULL, &init_param);
TEST_ASSERT_EQUAL(-EINVAL, ret);

// Test invalid parameters
init_param.i2c_init.max_speed_hz = 0;
ret = device_init(&dev, &init_param);
TEST_ASSERT_NOT_EQUAL(0, ret);

// Test I2C failure
i2c_inject_error(-EIO);
ret = device_read_reg(dev, REG, &val);
TEST_ASSERT_EQUAL(-EIO, ret);

// Test device not present (wrong address)
init_param.i2c_init.slave_address = 0x99;
ret = device_init(&dev, &init_param);
TEST_ASSERT_NOT_EQUAL(0, ret);
```

## Common Pitfalls to Avoid

### 1. Forgetting Stop Bit

**Wrong:**
```c
// Both transfers omit stop - bus never released
no_os_i2c_write(i2c, &reg, 1, 0);
no_os_i2c_read(i2c, data, len, 0);  // Bus still held!
```

**Right:**
```c
no_os_i2c_write(i2c, &reg, 1, 0);   // No stop (repeated start)
no_os_i2c_read(i2c, data, len, 1);  // Stop after read
```

### 2. Using 8-bit Address Format

**Wrong:**
```c
.slave_address = 0x90,  // 8-bit write address from datasheet
```

**Right:**
```c
.slave_address = 0x48,  // 7-bit address (0x90 >> 1)
```

### 3. Not Checking for Address Conflicts

**Problem:**
```c
// Both devices use 0x48 on same bus
struct no_os_i2c_init_param temp1 = { .slave_address = 0x48, ... };
struct no_os_i2c_init_param temp2 = { .slave_address = 0x48, ... };
```

**Solution:**
```c
// Check datasheet for ADDR pin configuration
struct no_os_i2c_init_param temp1 = { .slave_address = 0x48, ... };  // ADDR=GND
struct no_os_i2c_init_param temp2 = { .slave_address = 0x49, ... };  // ADDR=VCC
```

### 4. Ignoring Bus Speed Limitations

**Wrong:**
```c
// Long cable run with high speed
.max_speed_hz = 1000000,  // 1 MHz with 2m cable - won't work
```

**Right:**
```c
// Match speed to electrical characteristics
.max_speed_hz = 100000,  // 100 kHz for long cables
```

### 5. Not Handling Errors

**Wrong:**
```c
no_os_i2c_write(i2c, data, len, 1);
// Assume it worked - may have failed
```

**Right:**
```c
ret = no_os_i2c_write(i2c, data, len, 1);
if (ret) {
    pr_err("I2C write failed: %d\n", ret);
    return ret;
}
```
