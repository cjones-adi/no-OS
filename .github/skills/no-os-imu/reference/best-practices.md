# IMU Best Practices

Essential best practices for developing robust and accurate IMU, accelerometer, and gyroscope drivers.

## Data Acquisition

### 1. Always Read Burst Data for IMU

**Why Burst Read?**
- Ensures gyro/accel/temp are time-synchronized
- Single transaction reduces SPI overhead
- Includes data counter for detecting missed samples
- CRC validates data integrity

**Good - Burst Read**:
```c
struct adis_burst_data data;
ret = adis_read_burst_data(adis, &data);

// All data from same sample instant
process_imu_data(data.gyro_x, data.gyro_y, data.gyro_z,
                 data.accel_x, data.accel_y, data.accel_z,
                 data.temp);
```

**Bad - Individual Reads**:
```c
// DON'T DO THIS - data not synchronized
int32_t gyro_x, gyro_y, gyro_z;
adis_read_x_gyro(adis, &gyro_x);  // Sample N
adis_read_y_gyro(adis, &gyro_y);  // Sample N+1 (different time!)
adis_read_z_gyro(adis, &gyro_z);  // Sample N+2 (different time!)
```

### 2. Use FIFO for High-Rate Applications

**Benefits**:
- Reduces interrupt frequency
- Prevents data loss during processing
- Batches data for efficient processing

**Implementation**:
```c
// Configure FIFO
adxl345_set_fifo_mode(dev, ADXL345_FIFO_STREAM);
adxl345_set_fifo_samples(dev, 20);  // Interrupt every 20 samples

// In interrupt handler
void data_ready_isr(void) {
    uint8_t entries;
    adxl345_get_fifo_entries(dev, &entries);
    
    // Read all available data
    for (int i = 0; i < entries; i++) {
        adxl345_get_xyz(dev, &x, &y, &z);
        buffer[i] = process_sample(x, y, z);
    }
    
    // Batch processing
    process_batch(buffer, entries);
}
```

**Monitor FIFO Status**:
```c
// Check for overflow
uint8_t fifo_status;
adxl345_read_reg(dev, ADXL345_REG_FIFO_STATUS, &fifo_status);
if (fifo_status & 0x80) {
    pr_warn("FIFO overflow - data lost\n");
    fifo_overflow_count++;
}
```

### 3. Check CRC on Burst Data (ADIS)

**Why CRC Matters**:
- Validates data integrity
- Essential for safety-critical applications
- Detects SPI transmission errors

```c
// Read with CRC validation
struct adis_burst_data data;
ret = adis_read_burst_data(adis, &data);

// Validate CRC
uint16_t calculated_crc = calculate_crc16(&data, sizeof(data) - 2);
if (data.crc != calculated_crc) {
    pr_err("CRC mismatch: expected 0x%04X, got 0x%04X\n",
           calculated_crc, data.crc);
    
    // Re-read on CRC failure
    ret = adis_read_burst_data(adis, &data);
    if (ret == 0 && validate_crc(&data)) {
        // Recovered
    } else {
        // Report error to system
        return -EIO;
    }
}
```

## Calibration

### 4. Calibrate at Operating Temperature

**Temperature Effects**:
- Bias varies with temperature
- Factory calibration usually at 25°C
- Critical for <1 °/hr drift

```c
// Wait for thermal equilibrium before calibration
int32_t temp, last_temp = 0;
int stable_count = 0;

pr_info("Waiting for thermal stability...\n");
while (stable_count < 10) {
    adis_read_temp_out(adis, &temp);
    float temp_c = (float)temp * adis->info->temp_scale;
    
    pr_info("Current temp: %.2f°C\n", temp_c);
    
    if (abs(temp - last_temp) < 10) {  // <0.1°C change
        stable_count++;
    } else {
        stable_count = 0;
    }
    
    last_temp = temp;
    no_os_mdelay(1000);
}

pr_info("Temperature stable - starting calibration\n");
// Now perform calibration...
```

### 5. Use On-Chip Temperature for Compensation

```c
// Runtime temperature compensation
int32_t temp;
adis_read_temp_out(adis, &temp);
float temp_c = (float)temp * adis->info->temp_scale;

// Apply temperature-dependent bias correction
int32_t bias_x = interpolate_bias_table(temp_c, AXIS_X);
int32_t bias_y = interpolate_bias_table(temp_c, AXIS_Y);
int32_t bias_z = interpolate_bias_table(temp_c, AXIS_Z);

adis_write_xg_bias(adis, bias_x);
adis_write_yg_bias(adis, bias_y);
adis_write_zg_bias(adis, bias_z);
```

## Filtering and Signal Processing

### 6. Configure Filters Appropriately

**Match Filter to Application**:
```c
// High-speed vibration monitoring
adxl345_set_rate(dev, ADXL345_ODR_3200_HZ);
adxl345_set_filter(dev, ADXL345_FILTER_LPF);  // Anti-aliasing

// Low-speed orientation
adxl345_set_rate(dev, ADXL345_ODR_50_HZ);
adxl345_set_filter(dev, ADXL345_FILTER_LPF);  // Smooth noise
```

**ADIS Filter Configuration**:
```c
// Higher filter taps = lower noise, higher latency
adis_write_filt_size_var_b(adis, 16);  // 16-tap Bartlett filter

// Trade-offs:
// 2 taps:  Low latency, higher noise
// 16 taps: Low noise, higher latency (8 samples delay)
```

**Avoid Aliasing**:
- Low-pass filter bandwidth should be < ODR/2
- Example: 100 Hz ODR → 50 Hz max signal frequency

## Data Validation

### 7. Handle Overruns Gracefully

**Monitor Data Counter**:
```c
static uint16_t last_data_cntr = 0;

struct adis_burst_data data;
ret = adis_read_burst_data(adis, &data);

// Check for missed samples
uint16_t expected = (last_data_cntr + 1) & 0xFFFF;
if (data.data_cntr != expected && last_data_cntr != 0) {
    uint16_t missed = data.data_cntr - expected;
    pr_warn("Missed %u samples (counter jump: %u → %u)\n",
            missed, last_data_cntr, data.data_cntr);
    overrun_count += missed;
}
last_data_cntr = data.data_cntr;
```

**Log Overrun Events**:
```c
// Track system health
struct imu_stats {
    uint32_t total_samples;
    uint32_t missed_samples;
    uint32_t crc_errors;
    uint32_t fifo_overflows;
};

// Report periodically
if (stats.total_samples % 10000 == 0) {
    float miss_rate = (float)stats.missed_samples / stats.total_samples * 100;
    pr_info("IMU stats: %.2f%% missed, %u CRC errors, %u FIFO overflows\n",
            miss_rate, stats.crc_errors, stats.fifo_overflows);
}
```

### 8. Validate Range Selection

**Check for Saturation**:
```c
// Read data
int16_t x, y, z;
adxl345_get_xyz(dev, &x, &y, &z);

// At ±2g range: max value is ±512 (full scale)
// If seeing max values, range too small
if (abs(x) > 500 || abs(y) > 500 || abs(z) > 500) {
    pr_warn("Acceleration near saturation - consider wider range\n");
    pr_warn("Current: X=%d, Y=%d, Z=%d (max ±512)\n", x, y, z);
}
```

**Auto-Range Selection**:
```c
// Automatically select appropriate range
void auto_select_range(struct adxl345_dev *dev)
{
    int16_t x, y, z;
    adxl345_get_xyz(dev, &x, &y, &z);
    
    int16_t max_val = max(abs(x), max(abs(y), abs(z)));
    
    // Leave 20% headroom
    if (max_val > 410) {  // >80% of ±512
        // Increase range
        enum adxl345_range range;
        adxl345_get_range(dev, &range);
        if (range < ADXL345_RANGE_PM_16G) {
            adxl345_set_range(dev, range + 1);
            pr_info("Increased range to ±%dg\n", 2 << (range + 1));
        }
    }
}
```

## Interrupt Management

### 9. Use Interrupts for Efficiency

**Avoid Polling**:
```c
// Bad - wastes CPU
while (1) {
    uint8_t status;
    adxl345_read_reg(dev, ADXL345_REG_INT_SOURCE, &status);
    if (status & ADXL345_DATA_READY) {
        adxl345_get_xyz(dev, &x, &y, &z);
        process_data(x, y, z);
    }
    no_os_udelay(100);  // Polling overhead
}

// Good - interrupt-driven
void data_ready_isr(void) {
    adxl345_get_xyz(dev, &x, &y, &z);
    process_data(x, y, z);
}

// Setup
adxl345_set_interrupt_mapping(dev, ADXL345_DATA_READY, ADXL345_INT1);
adxl345_enable_interrupt(dev, ADXL345_DATA_READY, true);
no_os_gpio_set_irq_callback(dev->int1_gpio, data_ready_isr);
```

**Map Different Events to INT1/INT2**:
```c
// Critical events to INT1 (high priority)
adxl345_set_interrupt_mapping(dev, ADXL345_FREE_FALL, ADXL345_INT1);

// Less critical to INT2
adxl345_set_interrupt_mapping(dev, ADXL345_ACTIVITY, ADXL345_INT2);
adxl345_set_interrupt_mapping(dev, ADXL345_INACTIVITY, ADXL345_INT2);

// Handle with different priorities
```

## Power Management

### 10. Optimize for Application Power Requirements

**Ultra-Low Power (Battery)**:
```c
// ADXL362 - 1.8 µA in standby
adxl362_set_power_mode(dev, ADXL362_STANDBY);

// Activity detection wakes on motion
adxl362_setup_activity_detection(dev, 150, 10, true);
adxl362_set_autosleep(dev, true);

// Device wakes automatically on motion, returns to sleep when idle
```

**Balanced Performance**:
```c
// Moderate sample rate with low-power mode
adxl345_set_rate(dev, ADXL345_ODR_100_HZ);  // 100 Hz sufficient
adxl345_set_range(dev, ADXL345_RANGE_PM_2G);  // Sensitive range
adxl345_set_power_mode(dev, ADXL345_LOW_POWER);  // Reduced noise filtering
```

**Maximum Performance**:
```c
// High rate, ultra-low noise
adxl362_set_rate(dev, ADXL362_ODR_400_HZ);
adxl362_set_low_noise(dev, true);  // Higher power consumption
```

## Code Quality

### 11. Consistent Error Handling

```c
// Always check return values
int ret;

ret = adxl345_init(&dev, &init_param);
if (ret) {
    pr_err("Failed to initialize ADXL345: %d\n", ret);
    goto error_init;
}

ret = adxl345_set_range(dev, ADXL345_RANGE_PM_4G);
if (ret) {
    pr_err("Failed to set range: %d\n", ret);
    goto error_config;
}

return 0;

error_config:
    adxl345_remove(dev);
error_init:
    return ret;
```

### 12. Use Device Descriptor Accessors

```c
// Good - encapsulated access
int adxl345_get_scale_factor(struct adxl345_dev *dev, float *scale)
{
    if (!dev || !scale)
        return -EINVAL;
    
    switch (dev->selected_range) {
    case ADXL345_RANGE_PM_2G:
        *scale = 0.00391;  // 3.9 mg/LSB
        break;
    case ADXL345_RANGE_PM_4G:
        *scale = 0.00781;
        break;
    // ...
    }
    return 0;
}

// Bad - direct access
float scale = dev->scale_factor;  // Fragile, no validation
```

### 13. Document Units and Conventions

```c
/**
 * @brief Read gyroscope angular rate
 * @param adis - ADIS device descriptor
 * @param gyro_x - [out] X-axis angular rate (°/s * 100)
 * @param gyro_y - [out] Y-axis angular rate (°/s * 100)
 * @param gyro_z - [out] Z-axis angular rate (°/s * 100)
 * @return 0 on success, error code otherwise
 * @note Output is scaled by 100 for fixed-point representation
 *       Example: gyro_x = 15000 means 150.00 °/s
 */
int adis_read_gyro_rate(struct adis_dev *adis,
                        int32_t *gyro_x,
                        int32_t *gyro_y,
                        int32_t *gyro_z);
```

## Testing

### 14. Test All Error Paths

```c
// Test NULL pointer handling
void test_adxl345_init_null_device(void) {
    struct adxl345_init_param init = { /* valid */ };
    int ret = adxl345_init(NULL, &init);
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}

// Test resource allocation failure
void test_adxl345_init_i2c_failure(void) {
    no_os_i2c_init_IgnoreAndReturn(-ENOMEM);
    
    struct adxl345_dev *dev = NULL;
    int ret = adxl345_init(&dev, &init_param);
    
    TEST_ASSERT_EQUAL_INT(-ENOMEM, ret);
    TEST_ASSERT_NULL(dev);
}

// Test invalid parameters
void test_adxl345_set_range_invalid(void) {
    int ret = adxl345_set_range(dev, 99);  // Invalid range
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}
```

### 15. Validate Against Datasheet

```c
// Verify register values match datasheet
void test_adxl345_device_id(void) {
    uint8_t dev_id;
    int ret = adxl345_get_device_id(dev, &dev_id);
    
    TEST_ASSERT_EQUAL_INT(0, ret);
    TEST_ASSERT_EQUAL_HEX8(0xE5, dev_id);  // From datasheet
}

// Verify timing constraints
void test_adxl345_power_on_delay(void) {
    // Datasheet: 1.1ms typical, 5ms max power-on time
    adxl345_init(&dev, &init_param);
    no_os_mdelay(5);  // Wait for power-on
    
    // Device should respond
    uint8_t dev_id;
    int ret = adxl345_get_device_id(dev, &dev_id);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

## Performance Optimization

### 16. Minimize SPI Transactions

```c
// Bad - multiple transactions
uint8_t reg1, reg2, reg3;
adxl345_read_reg(dev, 0x30, &reg1);
adxl345_read_reg(dev, 0x31, &reg2);
adxl345_read_reg(dev, 0x32, &reg3);

// Good - burst read (if registers consecutive)
uint8_t regs[3];
adxl345_read_regs(dev, 0x30, regs, 3);
```

### 17. Use DMA for High-Rate Data

```c
// For high sample rates (>1 kHz), use DMA
struct no_os_spi_init_param spi_init = {
    .mode = NO_OS_SPI_MODE_3,
    .chip_select = 0,
    .max_speed_hz = 5000000,
    .use_dma = true,  // Enable DMA transfers
};
```

## Common Anti-Patterns to Avoid

### Don't: Mix Synchronous and Asynchronous Data

```c
// BAD - gyro and accel from different sample times
int32_t gyro_x;
adis_read_x_gyro(adis, &gyro_x);  // Sample N
no_os_mdelay(10);  // Delay!
int32_t accel_x;
adis_read_x_accl(adis, &accel_x);  // Sample N+10

// GOOD - burst read for synchronized data
struct adis_burst_data data;
adis_read_burst_data(adis, &data);
// data.gyro_x and data.accel_x from same instant
```

### Don't: Ignore Temperature Drift

```c
// BAD - calibrate once at startup
adis_auto_calibrate_gyro(adis);
// Over hours/days, temperature changes, bias drifts

// GOOD - monitor temperature, re-calibrate or compensate
int32_t startup_temp;
adis_read_temp_out(adis, &startup_temp);

// Periodically check
int32_t current_temp;
adis_read_temp_out(adis, &current_temp);
if (abs(current_temp - startup_temp) > 10°C) {
    // Re-calibrate or apply temp compensation
}
```

### Don't: Process Raw Data Without Scaling

```c
// BAD - comparing raw LSB values across different ranges
if (raw_accel > 1000) { /* what does this mean? */ }

// GOOD - convert to engineering units first
float accel_g = (float)raw_accel * scale_factor;
if (accel_g > 2.0) {  // Clear: 2g threshold
    handle_high_g_event();
}
```
