# IMU Calibration and Accuracy

Comprehensive guide to calibrating IMU, accelerometer, and gyroscope sensors for optimal accuracy.

## Offset Calibration (ADXL345)

### Understanding Offset
- Offset registers correct for zero-g bias
- Resolution: 15.6 mg/LSB (independent of range setting)
- Range: ±2g offset correction
- Applied automatically to all measurements

### Reading Current Offset
```c
// Read current offset
int8_t offset_x, offset_y, offset_z;
ret = adxl345_get_offset(dev, ADXL345_X_AXIS, &offset_x);
ret = adxl345_get_offset(dev, ADXL345_Y_AXIS, &offset_y);
ret = adxl345_get_offset(dev, ADXL345_Z_AXIS, &offset_z);

pr_info("Current offsets: X=%d, Y=%d, Z=%d (15.6mg/LSB)\n",
        offset_x, offset_y, offset_z);
```

### Setting Offset Manually
```c
// Set offset (15.6 mg/LSB in all ranges)
ret = adxl345_set_offset(dev, ADXL345_X_AXIS, -5);  // -78mg
ret = adxl345_set_offset(dev, ADXL345_Y_AXIS, 3);   // +47mg
ret = adxl345_set_offset(dev, ADXL345_Z_AXIS, 12);  // +187mg
```

### Auto-Calibration Routine (Zero-g)
```c
/**
 * @brief Auto-calibrate accelerometer offsets
 * @param dev - Device descriptor
 * @note Device must be at rest on level surface
 * @note Z-axis should be vertical (facing up or down)
 * @return 0 on success, error code otherwise
 */
int adxl345_auto_calibrate(struct adxl345_dev *dev)
{
    int32_t avg_x = 0, avg_y = 0, avg_z = 0;
    int16_t x, y, z;
    int ret;

    // Set to ±2g range for maximum resolution
    ret = adxl345_set_range(dev, ADXL345_RANGE_PM_2G);
    if (ret)
        return ret;

    // Clear existing offsets
    adxl345_set_offset(dev, ADXL345_X_AXIS, 0);
    adxl345_set_offset(dev, ADXL345_Y_AXIS, 0);
    adxl345_set_offset(dev, ADXL345_Z_AXIS, 0);

    // Collect 100 samples
    for (int i = 0; i < 100; i++) {
        ret = adxl345_get_xyz(dev, &x, &y, &z);
        if (ret)
            return ret;
        
        avg_x += x;
        avg_y += y;
        avg_z += z;
        
        no_os_mdelay(10);
    }

    // Calculate averages
    avg_x /= 100;
    avg_y /= 100;
    avg_z /= 100;

    // At ±2g range: 256 LSB/g
    // Offset resolution: 15.6 mg/LSB = 4 LSB offset per 1 LSB data
    
    // X and Y should read 0g
    int8_t cal_x = -(avg_x / 4);
    int8_t cal_y = -(avg_y / 4);
    
    // Z should read +1g (256) or -1g (-256) depending on orientation
    int32_t z_target = (avg_z > 0) ? 256 : -256;
    int8_t cal_z = -(avg_z - z_target) / 4;

    // Apply calibration
    adxl345_set_offset(dev, ADXL345_X_AXIS, cal_x);
    adxl345_set_offset(dev, ADXL345_Y_AXIS, cal_y);
    adxl345_set_offset(dev, ADXL345_Z_AXIS, cal_z);

    pr_info("Calibration complete: X=%d, Y=%d, Z=%d\n",
            cal_x, cal_y, cal_z);

    return 0;
}
```

### Verification After Calibration
```c
// Verify calibration
int16_t x, y, z;
adxl345_get_xyz(dev, &x, &y, &z);

float x_g = (float)x / 256.0;
float y_g = (float)y / 256.0;
float z_g = (float)z / 256.0;

pr_info("Calibrated readings: X=%.3fg, Y=%.3fg, Z=%.3fg\n",
        x_g, y_g, z_g);

// Expected: X ≈ 0g, Y ≈ 0g, Z ≈ ±1g
```

## Bias Correction (ADIS IMUs)

### Understanding Bias
- Gyroscope bias = offset in angular rate measurement
- Accelerometer bias = offset in acceleration measurement
- Factory calibration stored in flash
- User bias correction can be applied on top

### Reading Current Bias
```c
// Read current bias
int32_t gyro_bias_x, gyro_bias_y, gyro_bias_z;
ret = adis_read_xg_bias(adis, &gyro_bias_x);
ret = adis_read_yg_bias(adis, &gyro_bias_y);
ret = adis_read_zg_bias(adis, &gyro_bias_z);

pr_info("Gyro bias: X=%d, Y=%d, Z=%d\n",
        gyro_bias_x, gyro_bias_y, gyro_bias_z);

int32_t accel_bias_x, accel_bias_y, accel_bias_z;
ret = adis_read_xa_bias(adis, &accel_bias_x);
ret = adis_read_ya_bias(adis, &accel_bias_y);
ret = adis_read_za_bias(adis, &accel_bias_z);

pr_info("Accel bias: X=%d, Y=%d, Z=%d\n",
        accel_bias_x, accel_bias_y, accel_bias_z);
```

### Setting Bias Correction
```c
// Set bias correction
ret = adis_write_xg_bias(adis, -150);  // Device-specific units
ret = adis_write_yg_bias(adis, 75);
ret = adis_write_zg_bias(adis, -200);

// Enable bias correction
ret = adis_write_gyro_bias_corr_en(adis, 1);
ret = adis_write_accl_bias_corr_en(adis, 1);
```

### Factory Calibration Restore
```c
// Restore factory calibration
ret = adis_write_gyro_bias_corr_en(adis, 1);
ret = adis_write_accl_bias_corr_en(adis, 1);

// Clear user bias
ret = adis_write_xg_bias(adis, 0);
ret = adis_write_yg_bias(adis, 0);
ret = adis_write_zg_bias(adis, 0);
```

### Gyro Bias Auto-Calibration (Static)
```c
/**
 * @brief Auto-calibrate gyroscope bias
 * @param adis - ADIS device descriptor
 * @note Device must be stationary (not rotating)
 * @return 0 on success, error code otherwise
 */
int adis_auto_calibrate_gyro(struct adis_dev *adis)
{
    struct adis_burst_data data;
    int64_t sum_x = 0, sum_y = 0, sum_z = 0;
    int ret;

    // Collect 1000 samples at rest
    for (int i = 0; i < 1000; i++) {
        ret = adis_read_burst_data(adis, &data);
        if (ret)
            return ret;

        sum_x += data.gyro_x;
        sum_y += data.gyro_y;
        sum_z += data.gyro_z;

        no_os_mdelay(10);
    }

    // Calculate average bias
    int32_t avg_x = sum_x / 1000;
    int32_t avg_y = sum_y / 1000;
    int32_t avg_z = sum_z / 1000;

    // Apply negative of measured bias
    ret = adis_write_xg_bias(adis, -avg_x);
    ret = adis_write_yg_bias(adis, -avg_y);
    ret = adis_write_zg_bias(adis, -avg_z);

    // Enable bias correction
    ret = adis_write_gyro_bias_corr_en(adis, 1);

    pr_info("Gyro calibration: X=%d, Y=%d, Z=%d\n",
            -avg_x, -avg_y, -avg_z);

    return 0;
}
```

## Temperature Compensation

### Why Temperature Matters
- Bias drifts with temperature (typically 0.01-0.1 °/s/°C for gyros)
- Sensitivity varies with temperature
- Factory calibration usually at 25°C
- Long-term drift accelerated at temperature extremes

### Reading Temperature
```c
// ADIS temperature
int32_t temp;
ret = adis_read_temp_out(adis, &temp);
float temp_c = (float)temp * adis->info->temp_scale;

// ADXL345 doesn't have temp sensor - external sensor needed
```

### Temperature Compensation Table
```c
// Build compensation table during calibration
struct temp_cal_point {
    float temp;           // Temperature (°C)
    int32_t gyro_bias_x;  // Bias at this temperature
    int32_t gyro_bias_y;
    int32_t gyro_bias_z;
};

struct temp_cal_point cal_table[] = {
    { -20.0, -150, 75, -200 },
    {   0.0, -145, 78, -195 },
    {  25.0, -140, 80, -190 },  // Room temp
    {  50.0, -135, 82, -185 },
    {  70.0, -130, 85, -180 },
};

// Linear interpolation
int32_t interpolate_bias(float current_temp, int axis)
{
    // Find surrounding points and interpolate
    // ...
}
```

### Runtime Temperature Compensation
```c
// During operation
int32_t temp;
adis_read_temp_out(adis, &temp);
float temp_c = (float)temp * adis->info->temp_scale;

// Interpolate bias for current temperature
int32_t bias_x = interpolate_bias(temp_c, 0);
int32_t bias_y = interpolate_bias(temp_c, 1);
int32_t bias_z = interpolate_bias(temp_c, 2);

// Apply temperature-compensated bias
adis_write_xg_bias(adis, bias_x);
adis_write_yg_bias(adis, bias_y);
adis_write_zg_bias(adis, bias_z);
```

## Scale Factor Calibration

### Understanding Scale Factor
- Converts raw LSB to engineering units (g, °/s)
- Factory calibrated, but can verify/adjust
- Sensitivity varies with range setting

### Accelerometer Scale Verification
```c
/**
 * @brief Verify accelerometer scale factor
 * @note Flip device between +1g and -1g on each axis
 */
void verify_accel_scale(struct adxl345_dev *dev)
{
    int16_t pos_z, neg_z;

    // Device Z-up
    pr_info("Place device Z-axis up, press enter\n");
    wait_for_input();
    adxl345_get_xyz(dev, NULL, NULL, &pos_z);

    // Device Z-down
    pr_info("Flip device Z-axis down, press enter\n");
    wait_for_input();
    adxl345_get_xyz(dev, NULL, NULL, &neg_z);

    // Calculate scale factor
    // Should span 2g (from +1g to -1g)
    int16_t delta = pos_z - neg_z;
    float scale = 2.0 / (float)delta;  // g per LSB

    // At ±2g range, expect 256 LSB/g (0.00391 g/LSB)
    pr_info("Measured scale: %.5f g/LSB\n", scale);
    pr_info("Expected: 0.00391 g/LSB (±2g range)\n");
    pr_info("Error: %.2f%%\n", (scale - 0.00391) / 0.00391 * 100);
}
```

### Gyro Scale Verification
```c
/**
 * @brief Verify gyroscope scale factor
 * @note Use rate table or Earth's rotation (15.04 °/hr)
 */
void verify_gyro_scale(struct adis_dev *adis)
{
    // Earth rotation rate: 15.04 °/hr = 0.00417 °/s
    // Point sensor axis north or south and measure
    
    struct adis_burst_data data;
    int64_t sum_z = 0;

    // Average over 10 minutes
    for (int i = 0; i < 600; i++) {
        adis_read_burst_data(adis, &data);
        sum_z += data.gyro_z;
        no_os_mdelay(1000);
    }

    int32_t avg_z = sum_z / 600;
    float measured_rate = (float)avg_z * adis->info->gyro_scale;

    pr_info("Measured Earth rotation: %.5f °/s\n", measured_rate);
    pr_info("Expected: ±0.00417 °/s (depends on latitude)\n");
}
```

## Calibration Best Practices

### 1. Calibrate at Operating Temperature
```c
// Wait for thermal equilibrium
int32_t temp, last_temp = 0;
int stable_count = 0;

while (stable_count < 10) {
    adis_read_temp_out(adis, &temp);
    
    if (abs(temp - last_temp) < 10) {  // Less than 0.1°C change
        stable_count++;
    } else {
        stable_count = 0;
    }
    
    last_temp = temp;
    no_os_mdelay(1000);
}

pr_info("Temperature stable - ready to calibrate\n");
```

### 2. Use Adequate Sample Size
- Minimum 100 samples for offset calibration
- 1000+ samples for bias calibration (reduce noise impact)
- Average over multiple seconds to filter vibration

### 3. Verify Calibration Quality
```c
// After calibration, measure noise
int32_t sum = 0, sum_sq = 0;
for (int i = 0; i < 100; i++) {
    int16_t x;
    adxl345_get_xyz(dev, &x, NULL, NULL);
    sum += x;
    sum_sq += x * x;
}

int32_t mean = sum / 100;
int32_t variance = (sum_sq / 100) - (mean * mean);
float std_dev = sqrt(variance);

pr_info("Mean: %d LSB, Std Dev: %.2f LSB\n", mean, std_dev);
// Low mean (<5 LSB) and low std dev (<10 LSB) indicate good calibration
```

### 4. Store Calibration in Non-Volatile Memory
```c
// Save to EEPROM/flash
struct calibration_data {
    int8_t accel_offset_x;
    int8_t accel_offset_y;
    int8_t accel_offset_z;
    int32_t gyro_bias_x;
    int32_t gyro_bias_y;
    int32_t gyro_bias_z;
    uint32_t crc;
};

// Save
struct calibration_data cal = { /* populated values */ };
cal.crc = calculate_crc32(&cal, sizeof(cal) - sizeof(cal.crc));
eeprom_write(CAL_DATA_ADDR, &cal, sizeof(cal));

// Load on startup
struct calibration_data cal;
eeprom_read(CAL_DATA_ADDR, &cal, sizeof(cal));
if (validate_crc32(&cal)) {
    adxl345_set_offset(dev, ADXL345_X_AXIS, cal.accel_offset_x);
    // ... apply all calibration values
}
```

### 5. Periodic Re-Calibration
- Re-calibrate gyro bias on startup (while device stationary)
- Monitor drift over time
- Flag if bias exceeds threshold (sensor aging/damage)

```c
// Check if re-calibration needed
int32_t current_bias;
adis_read_xg_bias(adis, &current_bias);

if (abs(current_bias - stored_bias) > BIAS_DRIFT_THRESHOLD) {
    pr_warn("Bias drift detected - re-calibration recommended\n");
    // Optionally trigger auto-calibration
}
```

## Accuracy Specifications

### Typical Performance After Calibration

**ADXL345 (after offset calibration)**:
- Zero-g offset: ±10 mg (from ±40 mg uncalibrated)
- Noise density: 250 µg/√Hz
- Resolution: 3.9 mg (±2g range)

**ADIS16475 (factory calibrated)**:
- Gyro bias stability: 0.5 °/hr
- Gyro noise density: 0.0035 °/s/√Hz
- Accel bias: ±0.9 mg
- Accel noise density: 0.063 mg/√Hz

**After user calibration**:
- Can improve bias stability by 50-80%
- Temperature compensation critical for <1 °/hr drift
