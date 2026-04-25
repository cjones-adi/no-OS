# IMU API Usage Examples

Common use cases and patterns for using IMU, accelerometer, and gyroscope drivers.

## Common Use Cases

### 1. Vibration Monitoring

**Application**: Machine health monitoring, structural vibration analysis
**Requirements**: High sample rate, wide bandwidth, FIFO buffering

```c
// High sample rate, wide bandwidth
adxl345_set_rate(dev, ADXL345_ODR_3200_HZ);
adxl345_set_range(dev, ADXL345_RANGE_PM_16G);
adxl345_set_fifo_mode(dev, ADXL345_FIFO_STREAM);
adxl345_set_fifo_samples(dev, 32);

// Read FIFO in interrupt handler
void vibration_isr(void) {
    uint8_t samples;
    adxl345_get_fifo_entries(dev, &samples);
    for (int i = 0; i < samples; i++) {
        adxl345_get_xyz(dev, &x, &y, &z);
        fft_process(x, y, z);  // FFT analysis
    }
}
```

**Key Points**:
- Use highest sample rate supported (3200 Hz for ADXL345)
- Wide range (±16g) to avoid saturation on strong vibrations
- Stream mode FIFO prevents data loss
- Process in frequency domain (FFT) for vibration signatures

### 2. Motion-Triggered Wake

**Application**: Ultra-low power systems, battery-powered devices
**Requirements**: Activity detection, interrupt-driven wake

```c
// Ultra-low power with activity detection
adxl362_set_power_mode(dev, ADXL362_STANDBY);
adxl362_setup_activity_detection(dev,
    150,   // Threshold (mg)
    10,    // Time (samples)
    true); // Referenced mode

// Configure interrupt
adxl362_set_interrupt_mapping(dev,
    ADXL362_ACT, ADXL362_INT1);
adxl362_enable_interrupt(dev, ADXL362_ACT, true);

// Device wakes system on motion via GPIO interrupt
```

**Key Points**:
- ADXL362 is ultra-low power (1.8 µA in standby)
- Activity detection runs continuously
- Referenced mode compares to baseline, not absolute threshold
- GPIO interrupt wakes main processor

### 3. Orientation Detection

**Application**: Device orientation, tilt sensing, inclinometer
**Requirements**: Moderate rate, sensitive range, angle calculation

```c
// Low rate, sensitive range
adxl345_set_rate(dev, ADXL345_ODR_50_HZ);
adxl345_set_range(dev, ADXL345_RANGE_PM_2G);

// Read and calculate tilt
int16_t x, y, z;
adxl345_get_xyz(dev, &x, &y, &z);

// Convert to g
float x_g = (float)x / 256.0;
float y_g = (float)y / 256.0;
float z_g = (float)z / 256.0;

// Calculate angles (assumes small pitch/roll)
float pitch = atan2(y_g, z_g) * 180.0 / M_PI;
float roll = atan2(x_g, z_g) * 180.0 / M_PI;
```

**Key Points**:
- Low rate saves power (50 Hz sufficient)
- ±2g range maximizes resolution (3.9 mg/LSB)
- At rest, one axis reads ~1g (gravity)
- atan2() handles quadrant correctly

### 4. High-Precision IMU Data Logging (ADIS)

**Application**: Navigation, UAV control, robotics
**Requirements**: Synchronized data, CRC validation, filtering

```c
// Configure for maximum precision
adis_write_dec_rate(adis, 10);      // 200 Hz ODR (2000 Hz base / 10)
adis_write_filt_size_var_b(adis, 16); // 16-tap Bartlett filter
adis_write_sync_mode(adis, ADIS_SYNC_SCALED);

// Burst read for synchronized data
struct adis_burst_data data;
while (logging) {
    ret = adis_read_burst_data(adis, &data);

    // Log all sensor data
    log_imu_data(data.gyro_x, data.gyro_y, data.gyro_z,
                 data.accel_x, data.accel_y, data.accel_z,
                 data.temp, data.data_cntr);

    // CRC validation
    if (data.crc != calculate_crc(&data)) {
        pr_err("CRC mismatch\n");
    }
}
```

**Key Points**:
- Burst read ensures time synchronization
- Data counter detects missed samples
- CRC validates data integrity
- Bartlett filter reduces noise without excessive lag
- External sync for precise timing

### 5. Tap Detection for User Interface

**Application**: Input detection, gesture recognition
**Requirements**: Tap/double-tap discrimination, axis selection

```c
// Configure tap detection
struct adxl345_tap_config tap = {
    .tap_axes = ADXL345_TAP_Z_EN,  // Z-axis only
    .tap_dur = 20,                  // ~12.5 ms duration
    .tap_latent = 40,               // 50 ms between taps
    .tap_window = 160,              // 200 ms double-tap window
    .tap_thresh = 48,               // ~3g threshold
};
adxl345_set_tap_detection(dev, &tap);

// Map to different interrupt pins
adxl345_set_interrupt_mapping(dev, ADXL345_SINGLE_TAP, ADXL345_INT1);
adxl345_set_interrupt_mapping(dev, ADXL345_DOUBLE_TAP, ADXL345_INT2);

// Enable both
adxl345_enable_interrupt(dev, ADXL345_SINGLE_TAP, true);
adxl345_enable_interrupt(dev, ADXL345_DOUBLE_TAP, true);

// Interrupt handlers
void int1_handler(void) {
    // Single tap detected
    handle_single_tap();
}

void int2_handler(void) {
    // Double tap detected
    handle_double_tap();
}
```

**Key Points**:
- Tap duration sets minimum impact time
- Latency prevents bounce triggering multiple taps
- Window defines maximum time between double-taps
- Threshold avoids false triggers from handling

### 6. Free-Fall Detection

**Application**: Device drop protection, hard drive parking
**Requirements**: Fast detection, reliable threshold

```c
// Configure free-fall detection
adxl345_set_thresh_ff(dev, 7);      // ~437mg threshold
adxl345_set_time_ff(dev, 20);       // 100ms minimum duration

// Map to interrupt
adxl345_set_interrupt_mapping(dev, ADXL345_FREE_FALL, ADXL345_INT1);
adxl345_enable_interrupt(dev, ADXL345_FREE_FALL, true);

// Interrupt handler
void freefall_isr(void) {
    // Device is falling - park hard drive head, prepare for impact
    park_disk_heads();
    activate_airbag();  // For product protection
}
```

**Key Points**:
- Free-fall = all axes < threshold (low acceleration)
- Time parameter prevents false triggers from bumps
- Fast response critical (typically < 30ms to impact)
- Can combine with activity detection for impact event

### 7. Step Counter / Pedometer

**Application**: Fitness tracking, activity monitoring
**Requirements**: Activity detection, data filtering

```c
// Configure for step detection
adxl345_set_rate(dev, ADXL345_ODR_100_HZ);
adxl345_set_range(dev, ADXL345_RANGE_PM_2G);
adxl345_set_filter(dev, ADXL345_FILTER_LPF);  // Smooth noise

// Activity detection for step events
adxl345_set_thresh_act(dev, 10);    // 625mg threshold
adxl345_set_thresh_inact(dev, 5);   // 312mg threshold
adxl345_set_time_inact(dev, 1);     // 1 second

// Read data continuously
uint32_t step_count = 0;
bool last_active = false;

while (1) {
    // Read acceleration
    adxl345_get_xyz(dev, &x, &y, &z);
    
    // Calculate magnitude
    float mag = sqrt(x*x + y*y + z*z);
    
    // Detect step (peak in magnitude)
    bool active = (mag > step_threshold);
    if (active && !last_active) {
        step_count++;
    }
    last_active = active;
    
    no_os_mdelay(10);  // 100 Hz
}
```

**Key Points**:
- 100 Hz captures walking/running cadence (2-3 Hz typical)
- Low-pass filter smooths high-frequency noise
- Peak detection on magnitude (vector sum)
- Hysteresis prevents double-counting

### 8. Inactivity / Activity State Machine

**Application**: Auto-sleep, activity tracking
**Requirements**: Dual threshold detection

```c
// Configure activity/inactivity detection
adxl345_set_thresh_act(dev, 10);      // 625mg activity
adxl345_set_thresh_inact(dev, 5);     // 312mg inactivity
adxl345_set_time_inact(dev, 30);      // 30 seconds idle
adxl345_set_act_inact_ctl(dev, 
    ADXL345_ACT_ACDC_AC |  // AC-coupled (relative)
    ADXL345_INACT_ACDC_AC);

// Map to interrupts
adxl345_set_interrupt_mapping(dev, ADXL345_ACTIVITY, ADXL345_INT1);
adxl345_set_interrupt_mapping(dev, ADXL345_INACTIVITY, ADXL345_INT2);

// State machine
enum device_state {
    STATE_ACTIVE,
    STATE_IDLE,
    STATE_SLEEP
};

void activity_isr(void) {
    // Device active - wake from sleep
    state = STATE_ACTIVE;
    enable_full_functionality();
}

void inactivity_isr(void) {
    // Device idle for 30s - enter sleep
    state = STATE_SLEEP;
    disable_non_essential_peripherals();
}
```

**Key Points**:
- Activity = short burst above threshold
- Inactivity = sustained time below threshold
- AC-coupled mode detects changes, not absolute levels
- Use for power management state machine

## Testing Patterns

### Gravity Test (Device at Rest)
```c
void test_gravity_detection(void) {
    int16_t x, y, z;

    // Average over 100 samples
    int32_t sum_z = 0;
    for (int i = 0; i < 100; i++) {
        adxl345_get_xyz(dev, &x, &y, &z);
        sum_z += z;
        no_os_mdelay(10);
    }
    int16_t avg_z = sum_z / 100;

    // Should read ~1g (256 LSB/g at ±2g range)
    TEST_ASSERT_INT16_WITHIN(20, 256, avg_z);
}
```

### Motion Detection Test
```c
void test_tap_detection(void) {
    // Configure tap detection
    setup_tap_detection(dev);

    // Tap device (manual test)
    pr_info("Tap device now...\n");
    no_os_mdelay(3000);

    // Check interrupt source
    uint8_t int_source;
    adxl345_read_reg(dev, ADXL345_REG_INT_SOURCE, &int_source);
    TEST_ASSERT_TRUE(int_source & ADXL345_SINGLE_TAP);
}
```

### Self-Test Validation
```c
void test_self_test(void) {
    // Enable self-test (applies electrostatic force)
    ret = adxl345_set_self_test(dev, true);

    // Read self-test values
    int16_t st_x, st_y, st_z;
    ret = adxl345_get_xyz(dev, &st_x, &st_y, &st_z);

    // Disable self-test
    ret = adxl345_set_self_test(dev, false);

    // Read normal values
    int16_t norm_x, norm_y, norm_z;
    ret = adxl345_get_xyz(dev, &norm_x, &norm_y, &norm_z);

    // Check self-test change is within spec
    int16_t delta_x = st_x - norm_x;
    // Datasheet specifies acceptable range (e.g., 6 LSB minimum)
    TEST_ASSERT_GREATER_THAN(6, abs(delta_x));
}
```
