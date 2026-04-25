# I2C API Usage Patterns

This document provides comprehensive usage patterns and examples for the no-OS I2C API.

## Basic I2C Workflow

### Complete Initialization and Use Example

```c
struct no_os_i2c_desc *i2c_desc;

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,                  // I2C0
    .max_speed_hz = 400000,          // 400 kHz (fast mode)
    .slave_address = 0x48,           // 7-bit address
    .platform_ops = &max_i2c_ops,
    .extra = &max_i2c_extra,         // Platform-specific (optional)
};

ret = no_os_i2c_init(&i2c_desc, &i2c_init);
if (ret)
    return ret;

// Use I2C for communication
uint8_t reg_addr = 0x00;
uint8_t data[2];

// Write to register
data[0] = 0xAB;
ret = no_os_i2c_write(i2c_desc, data, 1, 1);  // stop_bit = 1

// Read from register
ret = no_os_i2c_write(i2c_desc, &reg_addr, 1, 0);  // No stop (repeated start)
ret = no_os_i2c_read(i2c_desc, data, 2, 1);   // Read 2 bytes, then stop

// Cleanup
ret = no_os_i2c_remove(i2c_desc);
```

## I2C Transfer Functions

### no_os_i2c_write() - Write Data

```c
int32_t no_os_i2c_write(struct no_os_i2c_desc *desc,
                        uint8_t *data,
                        uint8_t bytes_number,
                        uint8_t stop_bit);
```

**Parameters:**
- `desc` - I2C descriptor
- `data` - Data to write
- `bytes_number` - Number of bytes
- `stop_bit` - 1 = send STOP, 0 = no STOP (repeated start)

**Example: Write register**

```c
uint8_t write_data[2] = {0x10, 0x55};  // Reg addr + value
ret = no_os_i2c_write(i2c_desc, write_data, 2, 1);
```

### no_os_i2c_read() - Read Data

```c
int32_t no_os_i2c_read(struct no_os_i2c_desc *desc,
                       uint8_t *data,
                       uint8_t bytes_number,
                       uint8_t stop_bit);
```

**Parameters:**
- `desc` - I2C descriptor
- `data` - Buffer for received data
- `bytes_number` - Number of bytes to read
- `stop_bit` - 1 = send STOP after read, 0 = no STOP

**Example: Read register**

```c
uint8_t reg_addr = 0x10;
uint8_t read_data[1];

// Write register address (no stop)
no_os_i2c_write(i2c_desc, &reg_addr, 1, 0);

// Read data (with stop)
no_os_i2c_read(i2c_desc, read_data, 1, 1);
```

## Common I2C Communication Patterns

### Pattern 1: Simple Register Write

```c
int32_t i2c_write_reg(struct no_os_i2c_desc *i2c, uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg, val};
    return no_os_i2c_write(i2c, data, 2, 1);
}
```

### Pattern 2: Simple Register Read

```c
int32_t i2c_read_reg(struct no_os_i2c_desc *i2c, uint8_t reg, uint8_t *val)
{
    int32_t ret;

    // Write register address with repeated start
    ret = no_os_i2c_write(i2c, &reg, 1, 0);
    if (ret)
        return ret;

    // Read register value
    return no_os_i2c_read(i2c, val, 1, 1);
}
```

### Pattern 3: Burst Read

```c
int32_t i2c_read_burst(struct no_os_i2c_desc *i2c, uint8_t reg,
                       uint8_t *data, uint8_t len)
{
    int32_t ret;

    // Write start register address
    ret = no_os_i2c_write(i2c, &reg, 1, 0);
    if (ret)
        return ret;

    // Read multiple bytes
    return no_os_i2c_read(i2c, data, len, 1);
}
```

### Pattern 4: Burst Write

```c
int32_t i2c_write_burst(struct no_os_i2c_desc *i2c, uint8_t reg,
                        uint8_t *data, uint8_t len)
{
    uint8_t *buffer = malloc(len + 1);
    int32_t ret;

    if (!buffer)
        return -ENOMEM;

    buffer[0] = reg;  // Start register
    memcpy(&buffer[1], data, len);

    ret = no_os_i2c_write(i2c, buffer, len + 1, 1);
    free(buffer);

    return ret;
}
```

### Pattern 5: Device Scan

```c
bool i2c_device_exists(struct no_os_i2c_desc *i2c, uint8_t addr)
{
    struct no_os_i2c_desc temp_desc = *i2c;
    uint8_t dummy;

    temp_desc.slave_address = addr;

    // Try to read - if ACK received, device exists
    return (no_os_i2c_read(&temp_desc, &dummy, 0, 1) == 0);
}
```

### Pattern 6: 16-bit Register Read

```c
int32_t i2c_read_reg16(struct no_os_i2c_desc *i2c, uint8_t reg, uint16_t *val)
{
    int32_t ret;
    uint8_t data[2];

    // Write register address with repeated start
    ret = no_os_i2c_write(i2c, &reg, 1, 0);
    if (ret)
        return ret;

    // Read 2 bytes
    ret = no_os_i2c_read(i2c, data, 2, 1);
    if (ret)
        return ret;

    // Combine bytes (assuming big-endian)
    *val = (data[0] << 8) | data[1];

    return 0;
}
```

### Pattern 7: Multi-byte Register Write

```c
int32_t i2c_write_reg16(struct no_os_i2c_desc *i2c, uint8_t reg, uint16_t val)
{
    uint8_t data[3];

    data[0] = reg;                // Register address
    data[1] = (val >> 8) & 0xFF;  // MSB
    data[2] = val & 0xFF;         // LSB

    return no_os_i2c_write(i2c, data, 3, 1);
}
```

### Pattern 8: Read-Modify-Write

```c
int32_t i2c_update_reg(struct no_os_i2c_desc *i2c, uint8_t reg,
                       uint8_t mask, uint8_t val)
{
    int32_t ret;
    uint8_t current_val;

    // Read current value
    ret = i2c_read_reg(i2c, reg, &current_val);
    if (ret)
        return ret;

    // Modify
    current_val = (current_val & ~mask) | (val & mask);

    // Write back
    return i2c_write_reg(i2c, reg, current_val);
}
```

## Advanced Usage Examples

### Multi-device Communication

```c
// Configure multiple devices on same bus
struct no_os_i2c_desc *temp_sensor;
struct no_os_i2c_desc *eeprom;
struct no_os_i2c_desc *imu;

struct no_os_i2c_init_param temp_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,  // Temp sensor
    .platform_ops = &max_i2c_ops,
};

struct no_os_i2c_init_param eeprom_init = {
    .device_id = 0,  // Same bus
    .max_speed_hz = 400000,
    .slave_address = 0x50,  // EEPROM
    .platform_ops = &max_i2c_ops,
};

struct no_os_i2c_init_param imu_init = {
    .device_id = 0,  // Same bus
    .max_speed_hz = 400000,
    .slave_address = 0x68,  // IMU
    .platform_ops = &max_i2c_ops,
};

// Initialize all devices - bus sharing is automatic
no_os_i2c_init(&temp_sensor, &temp_init);
no_os_i2c_init(&eeprom, &eeprom_init);
no_os_i2c_init(&imu, &imu_init);

// Each transfer automatically locks the bus
uint8_t temp_data;
i2c_read_reg(temp_sensor, 0x00, &temp_data);

uint8_t imu_data[6];
i2c_read_burst(imu, 0x3B, imu_data, 6);
```

### EEPROM Sequential Read

```c
int32_t eeprom_sequential_read(struct no_os_i2c_desc *i2c,
                                uint16_t addr, uint8_t *data, uint16_t len)
{
    int32_t ret;
    uint8_t addr_bytes[2];

    // EEPROM uses 16-bit addressing
    addr_bytes[0] = (addr >> 8) & 0xFF;  // MSB
    addr_bytes[1] = addr & 0xFF;         // LSB

    // Write address with repeated start
    ret = no_os_i2c_write(i2c, addr_bytes, 2, 0);
    if (ret)
        return ret;

    // Read data
    return no_os_i2c_read(i2c, data, len, 1);
}
```

### EEPROM Page Write

```c
int32_t eeprom_page_write(struct no_os_i2c_desc *i2c,
                          uint16_t addr, uint8_t *data, uint8_t len)
{
    uint8_t *buffer;
    int32_t ret;

    // Allocate buffer for address + data
    buffer = malloc(len + 2);
    if (!buffer)
        return -ENOMEM;

    // Prepare address + data
    buffer[0] = (addr >> 8) & 0xFF;  // MSB
    buffer[1] = addr & 0xFF;         // LSB
    memcpy(&buffer[2], data, len);

    // Write in one transaction
    ret = no_os_i2c_write(i2c, buffer, len + 2, 1);

    free(buffer);
    return ret;
}
```

## Repeated Start vs Stop Condition

### With STOP (Two separate transactions)

```
START - ADDR(W) - REG - STOP
START - ADDR(R) - DATA - STOP
```

```c
// Less efficient - releases bus between transfers
no_os_i2c_write(i2c, &reg, 1, 1);  // Stop
// Bus is released here
no_os_i2c_read(i2c, data, len, 1);  // Stop
```

### With Repeated START (Single transaction)

```
START - ADDR(W) - REG - RESTART - ADDR(R) - DATA - STOP
```

```c
// More efficient - bus stays locked
no_os_i2c_write(i2c, &reg, 1, 0);  // No stop (repeated start)
no_os_i2c_read(i2c, data, len, 1);  // Stop after read
```

**Benefits of repeated start:**
- Faster (no bus setup/teardown overhead)
- Atomic operation (no other master can interfere)
- Required by some devices (won't work with separate transactions)

## Device-Specific Patterns

### Temperature Sensor (Single Register)

```c
float read_temperature(struct no_os_i2c_desc *i2c)
{
    int32_t ret;
    uint8_t data[2];

    ret = i2c_read_burst(i2c, TEMP_REG, data, 2);
    if (ret)
        return -EINVAL;

    // Convert to temperature (device-specific)
    int16_t raw = (data[0] << 8) | data[1];
    return raw * 0.0625;  // Example conversion
}
```

### IMU/Accelerometer (Burst Read)

```c
int32_t read_accel_xyz(struct no_os_i2c_desc *i2c, int16_t *x, int16_t *y, int16_t *z)
{
    int32_t ret;
    uint8_t data[6];

    // Read all 6 bytes in one transaction
    ret = i2c_read_burst(i2c, ACCEL_X_REG, data, 6);
    if (ret)
        return ret;

    // Parse data
    *x = (data[1] << 8) | data[0];  // Little-endian
    *y = (data[3] << 8) | data[2];
    *z = (data[5] << 8) | data[4];

    return 0;
}
```

### RTC (BCD Encoding)

```c
int32_t rtc_read_time(struct no_os_i2c_desc *i2c, struct time_t *time)
{
    int32_t ret;
    uint8_t data[7];

    // Read seconds, minutes, hours, day, date, month, year
    ret = i2c_read_burst(i2c, 0x00, data, 7);
    if (ret)
        return ret;

    // Convert BCD to binary
    time->seconds = ((data[0] >> 4) * 10) + (data[0] & 0x0F);
    time->minutes = ((data[1] >> 4) * 10) + (data[1] & 0x0F);
    time->hours = ((data[2] >> 4) * 10) + (data[2] & 0x0F);
    time->day = data[3] & 0x07;
    time->date = ((data[4] >> 4) * 10) + (data[4] & 0x0F);
    time->month = ((data[5] >> 4) * 10) + (data[5] & 0x0F);
    time->year = ((data[6] >> 4) * 10) + (data[6] & 0x0F);

    return 0;
}
```

## Error Handling Patterns

### Pattern 1: Retry on Temporary Failure

```c
int32_t i2c_read_with_retry(struct no_os_i2c_desc *i2c, uint8_t reg,
                            uint8_t *data, uint8_t retries)
{
    int32_t ret;

    for (uint8_t i = 0; i <= retries; i++) {
        ret = i2c_read_reg(i2c, reg, data);
        if (ret == 0)
            return 0;  // Success

        // Wait before retry
        no_os_mdelay(10);
    }

    return ret;  // Failed after all retries
}
```

### Pattern 2: Validate Data After Read

```c
int32_t i2c_read_chip_id(struct no_os_i2c_desc *i2c)
{
    int32_t ret;
    uint8_t chip_id;

    ret = i2c_read_reg(i2c, CHIP_ID_REG, &chip_id);
    if (ret)
        return ret;

    if (chip_id != EXPECTED_CHIP_ID)
        return -ENODEV;

    return 0;
}
```

### Pattern 3: Recover from Bus Lockup

```c
int32_t i2c_recover_bus(struct no_os_i2c_desc *i2c)
{
    // Platform-specific recovery
    // Usually involves sending 9 clock pulses

    // Re-initialize I2C
    struct no_os_i2c_init_param init = {
        .device_id = i2c->device_id,
        .max_speed_hz = i2c->max_speed_hz,
        .slave_address = i2c->slave_address,
        .platform_ops = i2c->platform_ops,
    };

    no_os_i2c_remove(i2c);
    return no_os_i2c_init(&i2c, &init);
}
```
