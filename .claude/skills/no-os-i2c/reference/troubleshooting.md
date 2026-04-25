# I2C Troubleshooting Guide

This document provides systematic troubleshooting for common I2C issues.

## Communication Failures

### No ACK Received

**Symptoms:**
- Function returns error (typically -EIO or -ENXIO)
- Device doesn't respond to I2C transactions
- I2C scanner doesn't find device

**Diagnostic steps:**

1. **Check wiring**
   - Verify SDA and SCL connections
   - Check for loose connections
   - Verify correct pin assignment

2. **Verify slave address**
   ```c
   // Use 7-bit address, not 8-bit R/W format
   .slave_address = 0x48,  // Correct
   // NOT:
   .slave_address = 0x90,  // Wrong (8-bit format)
   ```

3. **Check pull-up resistors**
   - Both SDA and SCL need pull-ups
   - Typical values: 4.7kΩ (100kHz), 2.2kΩ (400kHz)
   - Measure voltage - should be VCC when idle
   - Check with multimeter or oscilloscope

4. **Verify device power**
   - Check VDD voltage at device
   - Verify GND connection
   - Check power supply current capacity
   - Some devices need specific power-up sequence

5. **Try lower speed**
   ```c
   // Start with slow speed for testing
   .max_speed_hz = 100000,  // 100 kHz
   ```

6. **Test with I2C scanner**
   ```c
   void i2c_scan_bus(struct no_os_i2c_desc *i2c)
   {
       uint8_t dummy;
       struct no_os_i2c_desc temp = *i2c;
       
       pr_info("Scanning I2C bus:\n");
       for (uint8_t addr = 0x08; addr < 0x78; addr++) {
           temp.slave_address = addr;
           if (no_os_i2c_read(&temp, &dummy, 0, 1) == 0)
               pr_info("Device at 0x%02X\n", addr);
       }
   }
   ```

**Solutions:**

- **Wrong wiring**: Swap SDA/SCL if reversed
- **Wrong address**: Check datasheet, account for ADDR pin configuration
- **Missing pull-ups**: Add 4.7kΩ resistors to VCC
- **Device not powered**: Verify power supply
- **Wrong speed**: Reduce to 100 kHz

### Data Corruption or Wrong Values

**Symptoms:**
- Random or incorrect data read
- Intermittent failures
- Values change between reads

**Diagnostic steps:**

1. **Check pull-up resistor values**
   - Too weak (high resistance): slow rise times
   - Too strong (low resistance): excessive current
   - Measure rise time with oscilloscope
   - Should be < 1000ns (100kHz) or < 300ns (400kHz)

2. **Reduce I2C speed**
   ```c
   // Try slower speed
   .max_speed_hz = 100000,  // Down from 400kHz
   ```

3. **Check for noise**
   - Inspect signals with oscilloscope
   - Look for glitches on SDA during SCL high
   - Check for ringing on signal edges
   - Verify ground connection quality

4. **Verify timing requirements**
   - Some devices need delays between transfers
   - Check datasheet for timing constraints
   ```c
   no_os_i2c_write(i2c, data, len, 1);
   no_os_mdelay(10);  // Device-specific delay
   no_os_i2c_read(i2c, buffer, len, 1);
   ```

5. **Check bus capacitance**
   - Long wires increase capacitance
   - Many devices increase capacitance
   - Connectors add capacitance
   - Limit: 400pF (standard/fast), 550pF (fast+)

**Solutions:**

- **Weak pull-ups**: Use stronger resistors (lower value)
- **High speed issues**: Reduce to 100-400 kHz
- **Noise**: Shield wires, improve grounding, add ferrite beads
- **Timing issues**: Add delays, use repeated start
- **High capacitance**: Shorten wires, reduce device count

### Bus Stuck (SDA or SCL Always Low)

**Symptoms:**
- SDA or SCL stuck at 0V
- No communication possible
- Bus doesn't release

**Diagnostic steps:**

1. **Check which line is stuck**
   - Measure SDA and SCL with multimeter
   - Should be ~VCC when idle
   - If 0V, that line is stuck low

2. **Identify cause**
   - Clock stretching: slave holding SCL low
   - Bus lockup: incomplete transaction
   - Short circuit: wiring issue
   - Powered-off device: device pulling line low

3. **Try bus reset sequence**
   ```c
   int32_t i2c_reset_bus(struct no_os_i2c_desc *i2c)
   {
       // Remove I2C
       no_os_i2c_remove(i2c);
       
       // Platform-specific GPIO wiggle (send 9 clocks)
       // This releases any stuck slave
       
       // Re-initialize
       return no_os_i2c_init(&i2c, &init_param);
   }
   ```

**Solutions:**

- **Clock stretching**: Increase timeout, verify platform support
- **Bus lockup**: Send 9 clock pulses on SCL to release
- **Short circuit**: Check for solder bridges, damaged wires
- **Powered-off device**: Verify all devices powered
- **Faulty device**: Disconnect devices one-by-one to identify

### Cannot Communicate After First Transfer

**Symptoms:**
- First transfer works
- Subsequent transfers fail
- Must reset to work again

**Diagnostic steps:**

1. **Check stop condition**
   ```c
   // BAD - no stop bit sent
   no_os_i2c_write(i2c, data, len, 0);  // Bus not released!
   
   // GOOD - stop bit sent
   no_os_i2c_write(i2c, data, len, 1);  // Bus released
   ```

2. **Verify repeated start usage**
   ```c
   // CORRECT pattern
   no_os_i2c_write(i2c, &reg, 1, 0);   // No stop (repeated start)
   no_os_i2c_read(i2c, data, len, 1);  // Stop after read
   ```

3. **Check for platform repeated start support**
   - Not all platforms support repeated start
   - May need to use separate transactions
   ```c
   // Alternative for platforms without repeated start
   no_os_i2c_write(i2c, &reg, 1, 1);   // Stop
   no_os_i2c_read(i2c, data, len, 1);  // Stop
   ```

4. **Verify bus mutex is released**
   - Check for mutex deadlock
   - Ensure error paths unlock mutex

**Solutions:**

- **Missing stop**: Always set `stop_bit = 1` on final transfer
- **Repeated start issue**: Use separate transactions with stop bits
- **Mutex deadlock**: Verify error handling releases mutex

### Multiple Devices Interfere

**Symptoms:**
- Communication works with one device
- Fails when multiple devices connected
- Intermittent failures

**Diagnostic steps:**

1. **Check for address conflicts**
   ```c
   // BAD - same address
   .slave_address = 0x48,  // Device 1
   .slave_address = 0x48,  // Device 2 - CONFLICT!
   
   // GOOD - different addresses
   .slave_address = 0x48,  // Device 1
   .slave_address = 0x49,  // Device 2
   ```

2. **Verify bus speed compatibility**
   ```c
   // All devices must support configured speed
   .max_speed_hz = 100000,  // Use slowest device's max speed
   ```

3. **Check bus capacitance**
   - Each device adds capacitance
   - Total capacitance = wires + all devices
   - May exceed 400pF limit

4. **Test devices individually**
   - Connect one device at a time
   - Verify each works independently
   - Add devices incrementally

**Solutions:**

- **Address conflict**: Configure devices for different addresses (ADDR pin)
- **Speed mismatch**: Use slowest device's max speed
- **High capacitance**: Use I2C buffer/repeater, reduce speed
- **Faulty device**: Identify and replace problematic device

## Platform Porting Issues

### Missing Platform Ops

**Symptoms:**
- Compile error: undefined reference to platform ops
- Linker error: function not found

**Solution:**

```c
// Implement all required platform operations
const struct no_os_i2c_platform_ops myplatform_i2c_ops = {
    .i2c_ops_init = &myplatform_i2c_init,
    .i2c_ops_write = &myplatform_i2c_write,
    .i2c_ops_read = &myplatform_i2c_read,
    .i2c_ops_remove = &myplatform_i2c_remove,
};

// Use in init
.platform_ops = &myplatform_i2c_ops,
```

### Vendor HAL Errors

**Symptoms:**
- Platform functions return errors
- HAL initialization fails

**Diagnostic steps:**

1. **Check HAL return codes**
   ```c
   HAL_StatusTypeDef status;
   status = HAL_I2C_Master_Transmit(...);
   
   if (status != HAL_OK) {
       pr_err("HAL error: %d\n", status);
       // Map to no-OS error code
       return -EIO;
   }
   ```

2. **Verify peripheral clock enabled**
   ```c
   // STM32 example
   __HAL_RCC_I2C1_CLK_ENABLE();
   ```

3. **Check pin configuration**
   - Verify pins configured for I2C alternate function
   - Check GPIO initialization

**Solutions:**

- Map HAL errors to standard no-OS error codes
- Enable peripheral clocks before initialization
- Configure GPIO pins correctly
- Check HAL library version compatibility

### Pin Configuration Issues

**Symptoms:**
- Bus idle voltage not VCC
- Signals don't toggle
- Pull-ups not working

**Diagnostic steps:**

1. **Verify pin mux settings**
   ```c
   // Platform-specific pin configuration
   GPIO_InitTypeDef GPIO_InitStruct = {0};
   GPIO_InitStruct.Pin = GPIO_PIN_8 | GPIO_PIN_9;
   GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;  // Open-drain
   GPIO_InitStruct.Pull = GPIO_PULLUP;       // Internal pull-up
   GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
   GPIO_InitStruct.Alternate = GPIO_AF4_I2C1;
   HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);
   ```

2. **Check for open-drain configuration**
   - I2C requires open-drain outputs
   - Not push-pull

3. **Verify alternate function number**
   - Check datasheet for correct AF number
   - Different pins may have different AF numbers

**Solutions:**

- Configure pins for I2C alternate function
- Set to open-drain mode
- Enable internal pull-ups or add external ones
- Verify correct AF number from datasheet

### Clock Not Enabled

**Symptoms:**
- No communication
- Peripheral doesn't respond
- Registers read as 0x00

**Solution:**

```c
// Enable I2C peripheral clock (platform-specific)
// STM32:
__HAL_RCC_I2C1_CLK_ENABLE();

// Maxim:
// Clock automatically enabled by PeriphDrivers

// Check if enabled (read-back test)
uint32_t reg = READ_REG(I2C1->CR1);
if (reg == 0) {
    pr_err("I2C clock not enabled\n");
}
```

## Debugging Techniques

### 1. Enable Debug Logging

```c
#define DEBUG_I2C 1

int32_t device_read_reg(struct device_desc *dev, uint8_t reg, uint8_t *val)
{
    int32_t ret;
    
#ifdef DEBUG_I2C
    pr_debug("Reading reg 0x%02X\n", reg);
#endif
    
    ret = no_os_i2c_write(dev->i2c, &reg, 1, 0);
    if (ret) {
#ifdef DEBUG_I2C
        pr_err("Write failed: %d\n", ret);
#endif
        return ret;
    }
    
    ret = no_os_i2c_read(dev->i2c, val, 1, 1);
#ifdef DEBUG_I2C
    if (ret)
        pr_err("Read failed: %d\n", ret);
    else
        pr_debug("Read 0x%02X = 0x%02X\n", reg, *val);
#endif
    
    return ret;
}
```

### 2. Use Logic Analyzer

**What to check:**
- SCL frequency matches configured speed
- SDA changes only when SCL is low
- Start/stop conditions correct
- ACK/NACK bits
- Repeated start vs separate transactions
- Address format (7-bit vs 8-bit)

**Common issues visible:**
- Wrong address (device doesn't ACK address byte)
- Wrong data format (endianness issues)
- Timing violations (setup/hold time)
- Glitches on signals

### 3. Test with Known-Good Device

```c
// Test with simple I2C EEPROM (24C02)
// Known address: 0x50
// Simple read/write operations
// Helps isolate hardware vs software issues
```

### 4. Incremental Testing

```c
// Step 1: Test I2C init
ret = no_os_i2c_init(&i2c, &init);
pr_info("I2C init: %d\n", ret);

// Step 2: Test basic write
uint8_t test_data = 0xAA;
ret = no_os_i2c_write(i2c, &test_data, 1, 1);
pr_info("I2C write: %d\n", ret);

// Step 3: Test device presence
struct no_os_i2c_desc temp = *i2c;
uint8_t dummy;
for (uint8_t addr = 0x08; addr < 0x78; addr++) {
    temp.slave_address = addr;
    if (no_os_i2c_read(&temp, &dummy, 0, 1) == 0)
        pr_info("Device at 0x%02X\n", addr);
}

// Step 4: Test register read
uint8_t chip_id;
ret = device_read_reg(device, CHIP_ID_REG, &chip_id);
pr_info("Chip ID: 0x%02X (ret=%d)\n", chip_id, ret);
```

### 5. Verify With Multimeter/Oscilloscope

**Multimeter tests:**
- VCC at device: Should be stable, correct voltage
- SDA/SCL idle: Should be ~VCC (pull-up working)
- SDA/SCL during transfer: Should toggle
- GND: Should be 0V, good connection

**Oscilloscope tests:**
- SCL frequency: Should match configured speed ±10%
- Rise time: < 1000ns (100kHz) or < 300ns (400kHz)
- Signal levels: VIH > 0.7*VCC, VOL < 0.3*VCC
- Noise/ringing: Should be minimal

## Error Code Reference

| Error Code | Meaning | Common Causes |
|------------|---------|---------------|
| 0 | Success | - |
| -EINVAL | Invalid parameter | NULL pointer, invalid speed, bad address |
| -ENOMEM | Out of memory | Failed to allocate descriptor |
| -EIO | I/O error | NACK, bus error, timeout |
| -ENODEV | No such device | Wrong address, device not present |
| -EBUSY | Resource busy | Bus locked, previous transfer not complete |
| -ETIMEDOUT | Timeout | Clock stretching, slow device, bus stuck |
| -EAGAIN | Try again | Temporary failure, can retry |
| -EFAULT | Bad address | Memory access error |

## Quick Diagnostic Checklist

**Hardware checks:**
- [ ] SDA and SCL connected correctly
- [ ] Pull-up resistors present (4.7kΩ typical)
- [ ] Device powered (VDD = correct voltage)
- [ ] GND connected
- [ ] No shorts between SDA/SCL or to GND/VCC

**Configuration checks:**
- [ ] Correct 7-bit slave address
- [ ] Appropriate I2C speed (start with 100kHz)
- [ ] Platform ops correctly assigned
- [ ] Peripheral clock enabled (platform-specific)
- [ ] Pins configured for I2C function

**Software checks:**
- [ ] Return values checked
- [ ] Stop bit set correctly (usually 1)
- [ ] Repeated start used properly (stop_bit=0 then stop_bit=1)
- [ ] Error handling implemented
- [ ] Mutex/thread safety considered (if multi-threaded)
