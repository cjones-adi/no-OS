# Temperature Sensor Troubleshooting Guide

Common issues, diagnostic procedures, and solutions for temperature sensor drivers.

## Communication Issues

### No Device Response (I2C)

**Symptom**: I2C read/write fails, device not found.

```c
// Check I2C address
uint8_t dev_id;
ret = adt7420_read_reg(dev, ADT7420_REG_ID, &dev_id);
if (ret < 0) {
    pr_err("I2C read failed: %d\n", ret);
    pr_info("Check: I2C address (default 0x48-0x4B), pull-ups, bus speed\n");
}
if (dev_id != ADT7420_ID_VALUE) {
    pr_err("Wrong device ID: 0x%02X (expected 0x%02X)\n",
           dev_id, ADT7420_ID_VALUE);
}
```

**Common causes**:
- Wrong I2C address
  - ADT7420: 0x48 (A1=A0=GND), 0x49, 0x4A, 0x4B
  - LM75: 0x48-0x4F (A2:A0 configurable)
- Missing pull-up resistors (4.7k typical)
- I2C bus speed too high (max 400kHz for most sensors)
- SDA/SCL swapped
- Power supply issues

**Diagnostic steps**:
1. Verify correct I2C address from schematic
2. Check pull-up resistors present (measure 3.3V on SDA/SCL when idle)
3. Reduce I2C clock speed to 100kHz
4. Use logic analyzer to verify clock and data signals
5. Check power supply voltage (3.3V typically)

**Solution**:
```c
// Try lower I2C speed
struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 100000,  // Start with 100kHz
    .slave_address = 0x48,   // Verify from schematic
    .platform_ops = &i2c_ops,
};
```

### No Device Response (SPI)

**Symptom**: SPI communication fails, invalid data.

```c
// Check SPI communication
uint8_t config;
ret = max31865_read_register(dev, MAX31865_REG_CONFIG, &config);
if (ret < 0) {
    pr_err("SPI read failed: %d\n", ret);
    pr_info("Check: SPI mode (1 or 3), chip select, connections\n");
}
```

**Common causes**:
- Wrong SPI mode
  - MAX31865: Mode 1 or 3
  - MAX31855: Mode 0
  - LTC2983: Mode 0
- Chip select polarity incorrect
- MOSI/MISO swapped
- Clock speed too high
- Incorrect clock polarity/phase

**Diagnostic steps**:
1. Verify SPI mode from datasheet
2. Check chip select active low/high
3. Reduce SPI clock to 1MHz or lower
4. Use logic analyzer to verify MOSI, MISO, SCLK, CS signals
5. Verify power and ground connections

**Solution**:
```c
// Correct SPI configuration for MAX31865
struct no_os_spi_init_param spi_init = {
    .device_id = 0,
    .max_speed_hz = 1000000,     // Start with 1MHz
    .mode = NO_OS_SPI_MODE_1,    // Mode 1 for MAX31865
    .chip_select = 0,
    .platform_ops = &spi_ops,
};
```

## Invalid Temperature Readings

### Always Reads Zero or Maximum

**Symptom**: Temperature stuck at 0C, -128C, or maximum value.

```c
// Check for conversion completion
uint8_t status;
ret = adt7420_read_reg(dev, ADT7420_REG_STATUS, &status);
if (!(status & ADT7420_STATUS_RDY)) {
    pr_warn("Conversion not ready\n");
}

// Check if device is in shutdown mode
uint8_t config;
ret = adt7420_read_reg(dev, ADT7420_REG_CONFIG, &config);
if (config & ADT7420_CONFIG_SHUTDOWN) {
    pr_err("Device in shutdown mode\n");
    adt7420_set_operation_mode(dev, ADT7420_OP_MODE_CONT_CONV);
}
```

**Common causes**:
- Device in shutdown/standby mode
- Conversion not started or not complete
- Wrong register address
- Data format misinterpreted (13-bit vs 16-bit)

**Solution**:
```c
// Ensure device is in continuous conversion mode
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_CONT_CONV);

// Wait for first conversion
no_os_mdelay(250);

// Read temperature
float temp;
ret = adt7420_get_temperature(dev, &temp);
```

### RTD Reads Invalid Temperature

**Symptom**: RTD temperature way off or unstable.

```c
// RTD: Check bias voltage enabled
ret = max31865_read_register(dev, MAX31865_REG_CONFIG, &config);
if (!(config & MAX31865_CONFIG_VBIAS)) {
    pr_err("RTD bias voltage not enabled\n");
    max31865_enable_bias(dev, true);
    no_os_mdelay(10);  // Wait for bias to settle
}

// Verify reference resistor value
pr_info("Rref configured: %u ohms\n", dev->r_ref);

// Check if one-shot conversion triggered
if (!(config & MAX31865_CONFIG_1SHOT) && !(config & MAX31865_CONFIG_AUTO)) {
    pr_err("No conversion mode enabled\n");
}
```

**Common causes**:
- Bias voltage not enabled
- Wrong reference resistor value
- Wrong RTD type (PT100 vs PT1000)
- Wire mode mismatch (2/3/4-wire)
- Conversion not triggered

**Solution**:
```c
// Proper RTD initialization sequence
ret = max31865_init(&dev, &init);

// Enable bias voltage
ret = max31865_enable_bias(dev, true);
no_os_mdelay(10);  // Critical: wait for bias settling

// Enable automatic conversion
ret = max31865_enable_auto_convert(dev, true);
no_os_mdelay(65);  // Wait for first conversion

// Now can read temperature
float temp;
ret = max31865_read_temp(dev, &temp);
```

### Thermocouple Faults

**Symptom**: Thermocouple fault flags set, invalid readings.

```c
// Read fault status
uint8_t fault;
ret = max31855_read_fault(dev, &fault);

if (fault & MAX31855_FAULT_OPEN) {
    pr_err("Thermocouple open circuit - check connections\n");
    // Check: TC wires connected, no breaks
}
if (fault & MAX31855_FAULT_SHORT_GND) {
    pr_err("Thermocouple shorted to ground\n");
    // Check: insulation, shielding
}
if (fault & MAX31855_FAULT_SHORT_VCC) {
    pr_err("Thermocouple shorted to VCC\n");
    // Check: insulation, proper wiring
}

// Check cold junction temperature is reasonable
float cj_temp;
max31855_read_internal_temp(dev, &cj_temp);
if (cj_temp < -40 || cj_temp > 85) {
    pr_warn("Unusual cold junction temp: %.1f C\n", cj_temp);
    // Check: IC temperature, airflow, thermal contact
}
```

**Common causes**:
- Thermocouple not connected (open circuit)
- Thermocouple wires shorted together
- Thermocouple touching ground or power
- Poor cold junction thermal design
- Wrong thermocouple type selected

**Diagnostic procedure**:
1. Disconnect thermocouple → Should see OPEN fault
2. Short TC+ to TC- → Should see fault cleared (reads CJ temp)
3. Check continuity of TC wires with multimeter
4. Verify CJ temperature reasonable (near ambient)
5. Check TC polarity (+ and - correct)

**Solution**:
```c
// Clear fault and retry
max31855_clear_fault(dev);
no_os_mdelay(100);

// Reread fault status
ret = max31855_read_fault(dev, &fault);
if (fault == 0) {
    // Fault cleared, retry temperature reading
    ret = max31855_read_temp(dev, &temp);
}
```

## LTC2983 Conversion Issues

### Conversion Timeout

**Symptom**: Conversion never completes, timeout occurs.

```c
// Check for conversion timeout
ret = ltc2983_start_conversion(dev, channel);
uint32_t timeout = 1000;  // 1 second
while (timeout--) {
    ltc2983_get_conversion_status(dev, &status);
    if (!(status & LTC2983_STATUS_BUSY)) break;
    no_os_mdelay(1);
}
if (timeout == 0) {
    pr_err("Conversion timeout on channel %d\n", channel);
}

// Read error status
uint32_t error_flags;
ret = ltc2983_read_error_flags(dev, channel, &error_flags);
if (error_flags) {
    pr_err("Channel %d error: 0x%08X\n", channel, error_flags);
    // Decode specific error flags from datasheet
}
```

**Common causes**:
- Channel not properly configured
- Invalid sensor type
- Missing sense resistor configuration
- Cold junction channel not configured
- Timeout too short for sensor type

**Error codes**:
- `0x01`: Sensor hard failure
- `0x02`: ADC hard failure
- `0x04`: CJ hard failure
- `0x08`: CJ soft failure
- `0x10`: Sensor over/under range

**Solution**:
```c
// Verify channel configuration
struct ltc2983_sensor *sensor = &dev->sensors[channel];
if (sensor->type == LTC2983_SENSOR_TYPE_NONE) {
    pr_err("Channel %d not configured\n", channel);
    return -EINVAL;
}

// For thermocouple, verify CJ channel configured
if (sensor->type >= LTC2983_SENSOR_TYPE_THERMOCOUPLE_J) {
    uint8_t cj_ch = sensor->config.thermocouple.cold_junction_ch;
    if (dev->sensors[cj_ch].type == LTC2983_SENSOR_TYPE_NONE) {
        pr_err("CJ channel %d not configured\n", cj_ch);
        return -EINVAL;
    }
}
```

### Result Out of Range

**Symptom**: LTC2983 reports valid but unreasonable temperature.

```c
// Check for soft failures (out of range but valid)
float temp;
ret = ltc2983_read_channel_temp(dev, channel, &temp);

if (temp < -300 || temp > 2000) {
    pr_warn("Temperature out of expected range: %.1f C\n", temp);
    
    // Check configuration
    uint32_t error_flags;
    ltc2983_read_error_flags(dev, channel, &error_flags);
    
    if (error_flags & LTC2983_ERROR_SENSOR_OVER_RANGE) {
        pr_err("Sensor over range - check connections\n");
    }
    if (error_flags & LTC2983_ERROR_SENSOR_UNDER_RANGE) {
        pr_err("Sensor under range - check connections\n");
    }
}
```

**Common causes**:
- Wrong sensor type selected
- Incorrect sense resistor value
- Excitation current too low/high
- Sensor disconnected or faulty

## Accuracy Issues

### Temperature Offset Error

**Symptom**: Consistent offset from expected temperature.

```c
// Measure offset
float measured, expected = 25.0;  // Known reference
ret = sensor_read_temp(dev, &measured);

float offset = expected - measured;
pr_info("Offset error: %.3f C\n", offset);

// Too large offset check
if (fabs(offset) > 5.0) {
    pr_warn("Large offset detected\n");
    pr_info("Check: calibration, sensor placement, self-heating\n");
}
```

**Common causes**:
- No calibration performed
- Self-heating from power dissipation
- Thermal gradient from nearby components
- Wrong reference resistor value (RTD)
- Poor thermal contact

**Solution**:
- Perform calibration at operating temperature
- Reduce excitation current (RTD)
- Improve thermal isolation
- Verify reference resistor actual value
- Use thermal paste for better contact

### Noisy Readings

**Symptom**: Temperature fluctuates rapidly.

```c
// Check stability
#define NUM_SAMPLES 10
float temps[NUM_SAMPLES];

for (int i = 0; i < NUM_SAMPLES; i++) {
    ret = sensor_read_temp(dev, &temps[i]);
    no_os_mdelay(100);
}

float std_dev = calculate_std_dev(temps, NUM_SAMPLES);
if (std_dev > 0.5) {
    pr_warn("High noise: std dev = %.3f C\n", std_dev);
}
```

**Common causes**:
- Wrong 50Hz/60Hz filter setting
- Electrical noise on sensor wires
- Poor grounding
- Switching power supply noise
- Inadequate filtering

**Solution**:
```c
// Correct filter setting
enum max31865_filter filter = MAX31865_FILTER_60HZ;  // or 50HZ
ret = max31865_set_filter(dev, filter);

// Add software averaging
float read_averaged_temp(struct sensor_dev *dev)
{
    float sum = 0;
    const int n = 16;
    
    for (int i = 0; i < n; i++) {
        float temp;
        sensor_read_temp(dev, &temp);
        sum += temp;
        no_os_mdelay(10);
    }
    
    return sum / n;
}

// Improve wiring
// - Twisted pair for RTD/TC wires
// - Shielded cable if EMI present
// - Separate analog and digital grounds
// - Add ferrite beads on signal lines
```

## Power and Performance Issues

### High Power Consumption

**Symptom**: Battery drains quickly.

```c
// Check operating mode
uint8_t mode;
ret = adt7420_get_operation_mode(dev, &mode);
if (mode == ADT7420_OP_MODE_CONT_CONV) {
    pr_info("Continuous mode - high power\n");
    pr_info("Consider: one-shot or shutdown mode\n");
}

// Check RTD bias
ret = max31865_read_register(dev, MAX31865_REG_CONFIG, &config);
if (config & MAX31865_CONFIG_VBIAS) {
    pr_info("RTD bias enabled - consuming power\n");
    pr_info("Disable when not measuring\n");
}
```

**Solution**:
```c
// Use one-shot mode for low power
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_SHUTDOWN);

// Measure periodically
while (1) {
    // Wake up and measure
    adt7420_set_operation_mode(dev, ADT7420_OP_MODE_ONE_SHOT);
    no_os_mdelay(240);  // Conversion time
    
    float temp;
    adt7420_get_temperature(dev, &temp);
    
    // Return to shutdown
    adt7420_set_operation_mode(dev, ADT7420_OP_MODE_SHUTDOWN);
    
    // Sleep for interval
    no_os_mdelay(60000);  // 1 minute
}

// RTD power cycling
max31865_enable_bias(dev, false);  // Disable when not measuring
// ... sleep ...
max31865_enable_bias(dev, true);   // Enable for measurement
no_os_mdelay(10);
max31865_read_temp(dev, &temp);
max31865_enable_bias(dev, false);  // Disable again
```

### Slow Conversion Time

**Symptom**: Temperature updates too slow.

```c
// Check resolution setting
uint8_t resolution;
ret = adt7420_get_resolution(dev, &resolution);
if (resolution == ADT7420_RESOLUTION_16_BIT) {
    pr_info("16-bit resolution: 240ms conversion\n");
    pr_info("Use 13-bit for faster: 60ms conversion\n");
}

// Check if using one-shot when continuous better
uint8_t mode;
ret = adt7420_get_operation_mode(dev, &mode);
if (mode == ADT7420_OP_MODE_ONE_SHOT) {
    pr_info("One-shot mode - must trigger each reading\n");
    pr_info("Use continuous mode for faster updates\n");
}
```

**Solution**:
```c
// Use lower resolution for speed
ret = adt7420_set_resolution(dev, ADT7420_RESOLUTION_13_BIT);

// Use continuous conversion mode
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_CONT_CONV);

// RTD: Use automatic conversion
ret = max31865_enable_auto_convert(dev, true);
// No delay needed, always ready to read
```

## Diagnostic Tools

### I2C Bus Scanner

```c
void scan_i2c_bus(struct no_os_i2c_desc *i2c_desc)
{
    pr_info("Scanning I2C bus...\n");
    
    for (uint8_t addr = 0x08; addr < 0x78; addr++) {
        uint8_t dummy;
        int ret = no_os_i2c_write(i2c_desc, &dummy, 1, 0);
        
        if (ret == 0) {
            pr_info("Device found at address 0x%02X\n", addr);
        }
    }
    
    pr_info("Scan complete\n");
}
```

### Register Dump

```c
void dump_temp_sensor_registers(struct adt7420_dev *dev)
{
    pr_info("ADT7420 Register Dump:\n");
    
    const char *reg_names[] = {
        "TEMP_MSB", "TEMP_LSB", "STATUS", "CONFIG",
        "T_HIGH_MSB", "T_HIGH_LSB", "T_LOW_MSB", "T_LOW_LSB",
        "T_CRIT_MSB", "T_CRIT_LSB", "HIST", "ID",
    };
    
    for (int i = 0; i < 12; i++) {
        uint8_t value;
        int ret = adt7420_read_reg(dev, i, &value);
        
        if (ret == 0) {
            pr_info("  [0x%02X] %-12s = 0x%02X\n", i, reg_names[i], value);
        } else {
            pr_err("  [0x%02X] %-12s = READ FAILED\n", i, reg_names[i]);
        }
    }
}
```

### Temperature Sanity Check

```c
bool temperature_is_reasonable(float temp)
{
    // Basic sanity checks
    if (isnan(temp) || isinf(temp)) {
        pr_err("Temperature is NaN or Inf\n");
        return false;
    }
    
    // Reasonable range for typical applications
    if (temp < -50 || temp > 150) {
        pr_warn("Temperature out of typical range: %.1f C\n", temp);
        return false;
    }
    
    // Rate of change check (optional)
    static float last_temp = 25.0;
    float delta = fabs(temp - last_temp);
    
    if (delta > 10.0) {
        pr_warn("Large temperature change: %.1f C in one reading\n", delta);
        // May be valid for thermocouples, but suspicious for digital sensors
    }
    
    last_temp = temp;
    return true;
}
```

## Quick Troubleshooting Checklist

**No communication**:
- [ ] Verify I2C/SPI address/mode
- [ ] Check pull-up resistors (I2C)
- [ ] Verify power supply voltage
- [ ] Check wiring (SDA/SCL or MOSI/MISO/SCLK)
- [ ] Try lower bus speed
- [ ] Use logic analyzer to verify signals

**Invalid readings**:
- [ ] Check device not in shutdown mode
- [ ] Verify conversion started/completed
- [ ] Wait for thermal settling after power-on
- [ ] Check RTD bias enabled (RTD sensors)
- [ ] Verify correct data format (13/16-bit)
- [ ] Read fault registers for errors

**Accuracy problems**:
- [ ] Perform calibration
- [ ] Verify reference resistor value (RTD)
- [ ] Check wire mode configuration (RTD 2/3/4-wire)
- [ ] Set correct 50Hz/60Hz filter
- [ ] Reduce excitation current (RTD self-heating)
- [ ] Improve thermal contact

**Thermocouple faults**:
- [ ] Check TC wires connected
- [ ] Verify no shorts to ground/VCC
- [ ] Confirm correct TC type selected
- [ ] Check cold junction temperature reasonable
- [ ] Ensure good CJ thermal design

**LTC2983 errors**:
- [ ] Verify channel configured
- [ ] Check sense resistor channel configured
- [ ] Confirm CJ channel configured (thermocouples)
- [ ] Read error flags register
- [ ] Increase conversion timeout if needed
- [ ] Verify sensor type matches physical sensor

**Performance issues**:
- [ ] Use appropriate resolution for application
- [ ] Enable continuous mode if fast updates needed
- [ ] Use one-shot/shutdown for low power
- [ ] Disable RTD bias when not measuring
- [ ] Consider automatic conversion mode (RTD)
