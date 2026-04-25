# Temperature Sensor Best Practices

This document provides best practices for temperature sensor implementation, configuration, and deployment.

## Sensor Selection

### Choosing the Right Sensor Type

**Digital Temperature Sensors** (ADT7420, ADT75, LM75):
- Use for: Board-level monitoring, ambient sensing
- Advantages: Simple integration, I2C interface, low cost
- Range: -40°C to +125°C typical
- Accuracy: ±0.25°C to ±2°C

**RTD Converters** (MAX31865):
- Use for: Industrial process control, precision lab equipment
- Advantages: Wide range, high accuracy, standardized (PT100/PT1000)
- Range: -200°C to +850°C
- Accuracy: ±0.5°C with calibration

**Thermocouple Converters** (MAX31855, MAX31856):
- Use for: High-temperature applications, kilns, engines
- Advantages: Very wide range, rugged, low cost sensors
- Range: -200°C to +1800°C (type dependent)
- Accuracy: ±2°C to ±4°C typical

**Multi-Sensor Hub** (LTC2983):
- Use for: Multiple measurement points, mixed sensor types
- Advantages: Up to 20 channels, automatic linearization
- Flexibility: RTDs, thermocouples, thermistors, diodes
- Cost: Higher per-chip, lower per-channel

### Decision Matrix

```
Application              | Recommended Sensor | Alternative
-------------------------|-------------------|-------------
CPU temperature monitor  | ADT7420 (I2C)     | LM75
Industrial process       | MAX31865 (PT100)  | LTC2983
HVAC control             | LM75 (I2C)        | ADT75
Oven/furnace             | MAX31855 (K-type) | LTC2983
Multi-point system       | LTC2983           | Multiple MAX31865
Battery temperature      | ADT7420           | Thermistor + LTC2983
Medical device           | ADT7420 (±0.25°C) | RTD + MAX31865
Automotive engine        | MAX31855 (K-type) | Type N thermocouple
```

## Configuration Best Practices

### 1. Choose Appropriate Resolution

Higher resolution increases conversion time and power consumption.

```c
// ADT7420: 13-bit vs 16-bit
// 13-bit: 0.0625°C, 60ms conversion
// 16-bit: 0.0078°C, 240ms conversion

// For monitoring (1 sample/sec): Use 16-bit
ret = adt7420_set_resolution(dev, ADT7420_RESOLUTION_16_BIT);

// For fast updates (>4 samples/sec): Use 13-bit
ret = adt7420_set_resolution(dev, ADT7420_RESOLUTION_13_BIT);

// For low-power (battery): Use 13-bit or one-shot
ret = adt7420_set_resolution(dev, ADT7420_RESOLUTION_13_BIT);
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_ONE_SHOT);
```

**Guidelines**:
- Resolution should match application requirements
- Don't use 16-bit resolution for 1°C accuracy requirements
- Consider conversion time impact on system response
- Match resolution to application requirements

### 2. Use Proper Wire Configuration (RTD)

Wire configuration dramatically affects RTD accuracy.

```c
// 4-wire: Best accuracy, eliminates lead resistance
// Use for: Lab equipment, precision measurement, long cables
enum max31865_wire_mode wire_mode = MAX31865_4WIRE;

// 3-wire: Good accuracy, compensates lead resistance
// Use for: Industrial installations, balanced trade-off
enum max31865_wire_mode wire_mode = MAX31865_3WIRE;

// 2-wire: Simple, acceptable for short leads only
// Use for: Very short leads (<1m), non-critical applications
enum max31865_wire_mode wire_mode = MAX31865_2WIRE;
```

**Lead resistance impact**:
- Copper wire: ~0.017Ω/meter (20°C)
- PT100: 0.385Ω/°C temperature coefficient
- Error: ~0.4°C per ohm of lead resistance (2-wire)

**Example**:
```
10m cable × 0.017Ω/m × 2 wires = 0.34Ω lead resistance
Error (2-wire): 0.34Ω / 0.385Ω/°C = +0.9°C
Error (3-wire): ~0°C (compensated)
Error (4-wire): 0°C (eliminated)
```

### 3. Implement Fault Detection

Always check for sensor faults in production systems.

```c
// RTD fault detection
ret = max31865_enable_fault_detection(dev, true);

uint8_t fault_status;
ret = max31865_read_fault_status(dev, &fault_status);

if (fault_status) {
    log_error("RTD fault detected: 0x%02X", fault_status);
    
    if (fault_status & MAX31865_FAULT_HIGH_THRESHOLD) {
        // Open circuit or disconnected RTD
        set_system_error(ERROR_RTD_OPEN);
    }
    if (fault_status & MAX31865_FAULT_LOW_THRESHOLD) {
        // Short circuit
        set_system_error(ERROR_RTD_SHORT);
    }
    
    // Don't use invalid temperature reading
    return -EFAULT;
}

// Thermocouple fault detection
uint8_t tc_fault;
ret = max31855_read_fault(dev, &tc_fault);

if (tc_fault != 0) {
    if (tc_fault & MAX31855_FAULT_OPEN)
        log_error("Thermocouple open circuit");
    if (tc_fault & MAX31855_FAULT_SHORT_GND)
        log_error("Thermocouple short to ground");
    if (tc_fault & MAX31855_FAULT_SHORT_VCC)
        log_error("Thermocouple short to VCC");
        
    return -EFAULT;
}
```

**Why this matters**:
- Prevents incorrect control decisions
- Enables predictive maintenance
- Improves system safety
- Aids troubleshooting

### 4. Configure Noise Filtering

Set line frequency rejection based on location.

```c
// Configure 50Hz/60Hz notch filter
// Americas: 60Hz
// Europe/Asia/Africa: 50Hz

#ifdef REGION_AMERICAS
    enum max31865_filter filter = MAX31865_FILTER_60HZ;
#else
    enum max31865_filter filter = MAX31865_FILTER_50HZ;
#endif

ret = max31865_set_filter(dev, filter);

// LTC2983 global filter
ret = ltc2983_set_filter_notch(dev, 60);  // or 50
```

**Impact**:
- Wrong setting: increased noise, reduced accuracy
- Correct setting: better noise rejection, stable readings

**Additional filtering**:
```c
// Software averaging for noisy environments
#define NUM_SAMPLES 8

float read_averaged_temperature(struct adt7420_dev *dev)
{
    float sum = 0;
    int valid_samples = 0;
    
    for (int i = 0; i < NUM_SAMPLES; i++) {
        float temp;
        int ret = adt7420_get_temperature(dev, &temp);
        
        if (ret == 0) {
            sum += temp;
            valid_samples++;
        }
        
        no_os_mdelay(10);
    }
    
    if (valid_samples > 0)
        return sum / valid_samples;
    else
        return NAN;  // No valid readings
}
```

### 5. Calibrate at Operating Temperature

Self-heating and thermal gradients affect accuracy.

```c
// BAD: Calibrate at room temp, use at 50°C
// Self-heating changes with ambient temperature

// GOOD: Calibrate in representative environment
// For system operating at 50°C:
// 1. Heat enclosure to 50°C
// 2. Wait for thermal equilibrium (15-30 minutes)
// 3. Perform calibration
// 4. Use same environment for verification

// Store multiple calibration points if wide range
struct calibration_data {
    float offset_25c;   // Offset at 25°C
    float offset_50c;   // Offset at 50°C
    float offset_75c;   // Offset at 75°C
};

// Apply temperature-dependent correction
float get_calibration_offset(float raw_temp)
{
    if (raw_temp < 37.5)
        return cal_data.offset_25c;
    else if (raw_temp < 62.5)
        return cal_data.offset_50c;
    else
        return cal_data.offset_75c;
}
```

### 6. Cold Junction Compensation (Thermocouples)

Ensure proper CJ sensor placement and thermal design.

```c
// Best practices for cold junction:
// 1. CJ sensor at same temperature as terminals
// 2. Good thermal contact (thermal paste/compound)
// 3. Minimize air gaps
// 4. Shield from drafts and airflow
// 5. Thermal mass for stability

// Verify CJ temperature is reasonable
float cj_temp;
max31855_read_internal_temp(dev, &cj_temp);

// Sanity check
if (cj_temp < -40 || cj_temp > 85) {
    pr_warn("CJ temperature unusual: %.1f C\n", cj_temp);
    pr_warn("Check: thermal contact, ambient, airflow\n");
}

// For critical applications, use external precision CJ
// LTC2983 supports external diode as CJ reference
struct ltc2983_sensor diode_sensor = {
    .type = LTC2983_SENSOR_TYPE_DIODE,
    .channel = 2,
    .config.diode = {
        .single_ended = true,
        .num_readings = LTC2983_DIODE_3_READINGS,
        .averaging = true,
        .current = LTC2983_DIODE_CURRENT_10UA,
    },
};

struct ltc2983_sensor tc_sensor = {
    .type = LTC2983_SENSOR_TYPE_THERMOCOUPLE_K,
    .channel = 1,
    .config.thermocouple = {
        .cold_junction_ch = 2,  // Use external diode
        // ...
    },
};
```

### 7. Reference Resistor Accuracy (RTD)

Measure and use actual Rref value for best accuracy.

```c
// DON'T: Use nominal value
struct max31865_init_param init = {
    .r_ref = 4000,  // Nominal 4.0kΩ
};

// DO: Measure actual value with precision DMM
// Example: Measured 4.023kΩ
struct max31865_init_param init = {
    .r_ref = 4023,  // Measured value
};

// Impact:
// Rref error = temperature error (1:1)
// 0.5% Rref error = 0.5% temp error
// At 100°C: 0.5% = 0.5°C error

// Best practice:
// 1. Use 0.1% or better precision resistor
// 2. Measure with calibrated 6.5 digit DMM
// 3. Update firmware with measured value
// 4. Account for Rref temperature coefficient if needed
```

### 8. Power Management

Optimize for low-power applications.

```c
// Battery-powered: One-shot mode
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_SHUTDOWN);

// When measurement needed
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_ONE_SHOT);
no_os_mdelay(240);  // Wait for 16-bit conversion

float temp;
ret = adt7420_get_temperature(dev, &temp);

// Return to shutdown
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_SHUTDOWN);

// RTD: Disable bias when not measuring
ret = max31865_enable_bias(dev, false);  // ~0µA

// When measurement needed
ret = max31865_enable_bias(dev, true);
no_os_mdelay(10);  // Bias settling
ret = max31865_start_one_shot(dev);
no_os_mdelay(65);  // Conversion

float rtd_temp;
ret = max31865_read_temp(dev, &rtd_temp);

ret = max31865_enable_bias(dev, false);  // Save power
```

## Testing Strategies

### Unit Tests

```c
void test_temp_sensor_init(void) {
    struct adt7420_dev *dev;
    ret = adt7420_init(&dev, &init_param);
    TEST_ASSERT_EQUAL(0, ret);
    TEST_ASSERT_NOT_NULL(dev);
}

void test_resolution_setting(void) {
    ret = adt7420_set_resolution(dev, ADT7420_RESOLUTION_16_BIT);
    uint8_t res;
    adt7420_get_resolution(dev, &res);
    TEST_ASSERT_EQUAL(ADT7420_RESOLUTION_16_BIT, res);
}
```

### Integration Tests

```c
// Room temperature sanity check
void test_room_temperature(void) {
    float temp;
    ret = adt7420_get_temperature(dev, &temp);
    TEST_ASSERT_EQUAL(0, ret);

    // Should be reasonable room temperature
    TEST_ASSERT_FLOAT_WITHIN(15.0, 22.0, temp);  // 22°C ± 15°C
}

// Stability test
void test_temperature_stability(void) {
    float temps[10];
    for (int i = 0; i < 10; i++) {
        adt7420_get_temperature(dev, &temps[i]);
        no_os_mdelay(100);
    }

    // Calculate standard deviation
    float std_dev = calculate_std_dev(temps, 10);
    TEST_ASSERT_LESS_THAN(0.5, std_dev);  // Should be stable
}
```

## Common Pitfalls to Avoid

### 1. Ignoring Thermal Settling Time

```c
// BAD: Read immediately after power-on or configuration change
ret = adt7420_init(&dev, &init);
float temp;
ret = adt7420_get_temperature(dev, &temp);  // May be inaccurate!

// GOOD: Allow settling time
ret = adt7420_init(&dev, &init);
no_os_mdelay(100);  // Wait for first conversion
float temp;
ret = adt7420_get_temperature(dev, &temp);  // Accurate
```

### 2. Mixing Resolution with Accuracy

```c
// WRONG: Reporting 16-bit resolution (0.0078°C) when accuracy is ±0.25°C
pr_info("Temperature: %.4f C\n", temp);  // False precision!

// RIGHT: Report appropriate significant figures
pr_info("Temperature: %.2f C\n", temp);  // Matches ±0.25°C accuracy
```

### 3. Not Checking Return Values

```c
// BAD: Ignoring errors
adt7420_get_temperature(dev, &temp);
use_temperature(temp);  // May be invalid!

// GOOD: Check return values
ret = adt7420_get_temperature(dev, &temp);
if (ret == 0) {
    use_temperature(temp);
} else {
    log_error("Temperature read failed: %d", ret);
    use_default_temperature();
}
```

### 4. Wrong I2C/SPI Configuration

```c
// MAX31865 requires SPI Mode 1 or 3
struct no_os_spi_init_param spi_init = {
    .mode = NO_OS_SPI_MODE_0,  // WRONG!
};

// Correct
struct no_os_spi_init_param spi_init = {
    .mode = NO_OS_SPI_MODE_1,  // or MODE_3
};

// ADT7420 supports 400kHz I2C, not 1MHz
struct no_os_i2c_init_param i2c_init = {
    .max_speed_hz = 1000000,  // WRONG!
};

// Correct
struct no_os_i2c_init_param i2c_init = {
    .max_speed_hz = 400000,  // 400kHz max
};
```

### 5. Forgetting to Enable RTD Bias

```c
// BAD: Read without enabling bias
ret = max31865_read_temp(dev, &temp);  // Returns invalid data

// GOOD: Enable bias before reading
ret = max31865_enable_bias(dev, true);
no_os_mdelay(10);  // Wait for bias to settle
ret = max31865_read_temp(dev, &temp);
```

### 6. Not Clearing Faults

```c
// BAD: Fault stays latched, no new measurements
max31865_read_fault_status(dev, &fault);
// Fault stays set!

// GOOD: Clear fault and retry
max31865_read_fault_status(dev, &fault);
if (fault) {
    max31865_clear_fault(dev);
    // Optionally retry measurement
}
```

## Production Deployment Checklist

- [ ] Sensor type matches application requirements
- [ ] Resolution configured appropriately
- [ ] Wire mode correct (RTD: 2/3/4-wire)
- [ ] Line frequency filter set correctly (50Hz/60Hz)
- [ ] Fault detection enabled
- [ ] Calibration performed in operating environment
- [ ] Reference resistor value measured and programmed
- [ ] Cold junction properly designed (thermocouples)
- [ ] Power management implemented (if battery-powered)
- [ ] Error handling for all sensor operations
- [ ] Thermal settling time allowed after power-on
- [ ] Sanity checks for out-of-range readings
- [ ] Logging for diagnostics and maintenance
- [ ] Unit and integration tests passing
- [ ] Documentation updated

## Performance Optimization

### Minimize Conversion Time

```c
// Use 13-bit resolution for faster updates
ret = adt7420_set_resolution(dev, ADT7420_RESOLUTION_13_BIT);
// 60ms instead of 240ms per reading

// RTD: Use continuous conversion instead of one-shot
ret = max31865_enable_auto_convert(dev, true);
// Always ready, no conversion delay
```

### Reduce I2C/SPI Transactions

```c
// BAD: Multiple separate reads
float temp1, temp2, temp3;
adt7420_get_temperature(dev1, &temp1);
adt7420_get_temperature(dev2, &temp2);
adt7420_get_temperature(dev3, &temp3);

// BETTER: Batch reads if possible
// Or use multi-channel LTC2983 for multiple points
ret = ltc2983_start_conversion(dev, LTC2983_CONVERSION_ALL);
ret = ltc2983_wait_for_conversion(dev, 5000);
// Read all channels with minimal bus traffic
```

### Use Interrupts for Alerts

```c
// Instead of polling for over-temperature
void setup_temperature_alert(void)
{
    // Configure threshold
    ret = adt7420_set_high_limit(dev, 50.0);
    
    // Configure interrupt pin
    ret = adt7420_set_int_mode(dev, ADT7420_INT_MODE_INTERRUPT);
    
    // Setup GPIO interrupt handler
    struct no_os_irq_init_param irq_init = { /* ... */ };
    ret = no_os_irq_register_callback(irq_desc, INT_PIN, 
                                       temp_alert_isr, dev);
}

// Interrupt handler
void temp_alert_isr(void *context)
{
    struct adt7420_dev *dev = context;
    
    // Handle over-temperature condition
    emergency_shutdown();
    
    // Clear interrupt
    adt7420_clear_interrupt(dev);
}
```

## Summary

Key principles for successful temperature sensor implementation:

1. **Select appropriate sensor** for application requirements
2. **Configure correctly** (resolution, wire mode, filtering)
3. **Implement fault detection** for production reliability
4. **Calibrate properly** in operating environment
5. **Handle errors** and edge cases
6. **Test thoroughly** (unit, integration, environmental)
7. **Document** configuration and calibration procedures
8. **Optimize** for power and performance requirements
