---
name: no-os-imu
description: |
  Complete guide to no-OS IMU, accelerometer, and gyroscope drivers. Covers 3-axis motion
  sensing, FIFO data acquisition, motion detection features (tap, free-fall, activity),
  calibration patterns, and burst read operations for synchronized sensor data.
triggers:
  - "imu"
  - "accelerometer"
  - "gyroscope"
  - "motion sensor"
  - "ADXL"
  - "ADIS"
  - "3-axis"
  - "tap detection"
  - "free-fall"
alwaysInclude: false
---

# no-OS IMU/Accelerometer/Gyroscope Driver Development Guide

Quick-start guide for developing IMU, accelerometer, and gyroscope drivers in the no-OS framework. Based on analysis of 31 drivers including ADXL345, ADXL362, ADXL367, ADXL355, ADXRS290, and the extensive ADIS family.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed documentation when needed:

**Triggers to read reference/implementation.md**:
- User asks: "device descriptor", "init parameters", "driver structure", "ADIS framework"
- Mentions: struct definitions, initialization patterns, IIO integration
- Questions about: page registers, clock configuration, power management, filter setup
- Need: complete implementation patterns, device descriptor examples

**Triggers to read reference/api-usage.md**:
- User asks: "how to use", "example code", "use case", "application"
- Mentions: vibration monitoring, orientation detection, step counter, tap detection
- Questions about: specific applications, testing patterns, real-world usage
- Need: complete usage examples for different applications

**Triggers to read reference/calibration.md**:
- User asks: "calibrate", "offset", "bias", "accuracy", "drift", "temperature compensation"
- Mentions: zero-g calibration, gyro bias, scale factor, auto-calibration
- Questions about: calibration procedures, verification, storing calibration
- Need: complete calibration workflows, temperature compensation tables

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "recommendations", "patterns", "anti-patterns"
- Questions about: burst read vs individual reads, FIFO usage, CRC validation
- Mentions: code quality, error handling, performance optimization
- Need: comprehensive best practices, do's and don'ts

**Triggers to read reference/troubleshooting.md**:
- User says: "not working", "error", "problem", "debug", "issue"
- Mentions: no response, wrong data, noisy data, FIFO overflow, interrupt not firing
- Build/runtime errors in user output
- Need: systematic troubleshooting procedures, common issue solutions

---

## When to Use This Skill

- Implementing IMU, accelerometer, or gyroscope drivers
- Working with ADXL or ADIS family devices
- Configuring motion detection features (tap, free-fall, activity)
- Setting up FIFO data acquisition
- Implementing burst read for synchronized data
- Calibrating sensors for optimal accuracy
- Troubleshooting sensor communication or data quality

## IMU Overview

### Device Types

**MEMS Accelerometers** (ADXL family):
- Measure linear acceleration on X, Y, Z axes
- Ranges: ±2g, ±4g, ±8g, ±16g (some up to ±200g)
- Digital output via SPI/I2C
- Motion detection: tap, free-fall, activity/inactivity

**MEMS Gyroscopes** (ADXRS family):
- Measure angular velocity (rotation rate)
- Ranges: ±125°/s to ±2000°/s
- Temperature compensation
- Low drift specifications

**Combined IMU** (ADIS family):
- Integrated 3-axis gyroscope + 3-axis accelerometer
- Often includes magnetometer, barometer
- Factory calibrated with bias correction
- Synchronized burst data reads with CRC validation
- High-precision tactical/industrial grade

### Common Locations

```
drivers/accel/        # Accelerometer-only devices
drivers/gyro/         # Gyroscope-only devices
drivers/imu/          # Combined IMU devices (ADIS family)
```

**Key Examples**:
- `drivers/accel/adxl345/` - Digital MEMS accelerometer (SPI/I2C)
- `drivers/accel/adxl362/` - Ultra-low power accelerometer
- `drivers/imu/adis.c` - Generic ADIS IMU framework
- `drivers/imu/adis1654x.h` - High-performance tactical IMU

## Quick Reference

### Typical API Functions

```c
// Initialization
int adxl345_init(struct adxl345_dev **device, struct adxl345_init_param init_param);

// Data acquisition
int adxl345_get_xyz(struct adxl345_dev *dev, int16_t *x, int16_t *y, int16_t *z);
int adis_read_burst_data(struct adis_dev *adis, struct adis_burst_data *data);

// Configuration
int adxl345_set_range(struct adxl345_dev *dev, enum adxl345_range range);
int adxl345_set_rate(struct adxl345_dev *dev, enum adxl345_odr odr);

// Motion detection
int adxl345_set_tap_detection(struct adxl345_dev *dev, struct adxl345_tap_config *cfg);
int adxl345_set_thresh_ff(struct adxl345_dev *dev, uint8_t thresh);

// FIFO
int adxl345_set_fifo_mode(struct adxl345_dev *dev, enum adxl345_fifo_mode mode);
int adxl345_get_fifo_entries(struct adxl345_dev *dev, uint8_t *entries);

// Calibration
int adxl345_set_offset(struct adxl345_dev *dev, enum adxl345_axis axis, int8_t offset);
int adis_write_xg_bias(struct adis_dev *adis, int32_t bias);
```

### Basic Data Acquisition

**Simple Read** (Accelerometer):
```c
int16_t x, y, z;
ret = adxl345_get_xyz(dev, &x, &y, &z);

// Convert to g units
float x_g = (float)x * scale_factor;  // scale_factor depends on range
```

**Burst Read** (IMU - Synchronized Data):
```c
struct adis_burst_data data;
ret = adis_read_burst_data(adis, &data);

// All data from same sample instant:
// - data.accel_x/y/z, data.gyro_x/y/z
// - data.temp, data.data_cntr, data.crc
```

### Range Configuration

```c
// Accelerometer ranges (wider range = less sensitivity)
enum adxl345_range {
    ADXL345_RANGE_PM_2G = 0,   // ±2g, 3.9 mg resolution
    ADXL345_RANGE_PM_4G = 1,   // ±4g, 7.8 mg resolution
    ADXL345_RANGE_PM_8G = 2,   // ±8g, 15.6 mg resolution
    ADXL345_RANGE_PM_16G = 3,  // ±16g, 31.2 mg resolution
};

ret = adxl345_set_range(dev, ADXL345_RANGE_PM_4G);
```

### FIFO Configuration

```c
// Enable FIFO with watermark
adxl345_set_fifo_mode(dev, ADXL345_FIFO_STREAM);  // Circular buffer
adxl345_set_fifo_samples(dev, 20);  // Interrupt every 20 samples

// Read FIFO in interrupt handler
uint8_t entries;
adxl345_get_fifo_entries(dev, &entries);
for (int i = 0; i < entries; i++) {
    adxl345_get_xyz(dev, &x, &y, &z);
    process_sample(x, y, z);
}
```

### Motion Detection

**Tap Detection**:
```c
struct adxl345_tap_config tap = {
    .tap_axes = ADXL345_TAP_Z_EN,
    .tap_dur = 20,      // ~12.5 ms duration
    .tap_thresh = 48,   // ~3g threshold
};
adxl345_set_tap_detection(dev, &tap);

// Map to interrupt pin
adxl345_set_interrupt_mapping(dev, ADXL345_SINGLE_TAP, ADXL345_INT1);
adxl345_enable_interrupt(dev, ADXL345_SINGLE_TAP, true);
```

**Free-Fall Detection**:
```c
adxl345_set_thresh_ff(dev, 7);   // ~437mg threshold
adxl345_set_time_ff(dev, 20);    // 100ms minimum duration
adxl345_enable_interrupt(dev, ADXL345_FREE_FALL, true);
```

**Activity/Inactivity**:
```c
adxl345_set_thresh_act(dev, 10);      // 625mg activity threshold
adxl345_set_thresh_inact(dev, 5);     // 312mg inactivity
adxl345_set_time_inact(dev, 30);      // 30 seconds idle
```

### Simple Calibration

**Offset Calibration** (Device at rest):
```c
// Collect samples
int32_t avg_x = 0, avg_y = 0, avg_z = 0;
for (int i = 0; i < 100; i++) {
    int16_t x, y, z;
    adxl345_get_xyz(dev, &x, &y, &z);
    avg_x += x; avg_y += y; avg_z += z;
    no_os_mdelay(10);
}
avg_x /= 100; avg_y /= 100; avg_z /= 100;

// Calculate offsets (X/Y should be 0g, Z should be ±1g)
int8_t cal_x = -(avg_x / 4);  // Offset resolution: 15.6mg/LSB
int8_t cal_y = -(avg_y / 4);
int32_t z_target = (avg_z > 0) ? 256 : -256;
int8_t cal_z = -(avg_z - z_target) / 4;

// Apply calibration
adxl345_set_offset(dev, ADXL345_X_AXIS, cal_x);
adxl345_set_offset(dev, ADXL345_Y_AXIS, cal_y);
adxl345_set_offset(dev, ADXL345_Z_AXIS, cal_z);
```

**Gyro Bias Calibration** (Device stationary):
```c
// Average over 1000 samples
int64_t sum_x = 0, sum_y = 0, sum_z = 0;
for (int i = 0; i < 1000; i++) {
    struct adis_burst_data data;
    adis_read_burst_data(adis, &data);
    sum_x += data.gyro_x;
    sum_y += data.gyro_y;
    sum_z += data.gyro_z;
    no_os_mdelay(10);
}

// Apply negative of measured bias
adis_write_xg_bias(adis, -(sum_x / 1000));
adis_write_yg_bias(adis, -(sum_y / 1000));
adis_write_zg_bias(adis, -(sum_z / 1000));
adis_write_gyro_bias_corr_en(adis, 1);
```

### Common Troubleshooting

**No Device Response**:
```c
// Check device ID
uint8_t dev_id;
adxl345_get_device_id(dev, &dev_id);
if (dev_id != ADXL345_DEVICE_ID) {
    // Check: SPI mode (Mode 3), chip select, power supply
    // Reduce SPI speed if needed
}

// ADIS diagnostic check
uint16_t diag_stat;
adis_read_diag_stat(adis, &diag_stat);
if (diag_stat != 0) {
    pr_err("ADIS diagnostic errors: 0x%04X\n", diag_stat);
}
```

**Incorrect Data**:
```c
// Verify range and scale factor
enum adxl345_range range;
adxl345_get_range(dev, &range);
pr_info("Range: ±%dg\n", 2 << range);

// Check measurement mode (not standby)
uint8_t power_ctl;
adxl345_read_reg(dev, ADXL345_REG_POWER_CTL, &power_ctl);
if (!(power_ctl & 0x08)) {
    adxl345_set_power_mode(dev, ADXL345_MEASUREMENT);
}
```

**FIFO Overflow**:
```c
uint8_t fifo_status;
adxl345_read_reg(dev, ADXL345_REG_FIFO_STATUS, &fifo_status);
if (fifo_status & 0x80) {
    pr_warn("FIFO overflow - read more frequently\n");
    // Solution: Reduce watermark or increase read rate
}
```

## Essential Best Practices

1. **Always Use Burst Read for IMU** - Ensures gyro/accel/temp are time-synchronized
2. **Use FIFO for High-Rate Applications** - Reduces interrupt frequency, prevents data loss
3. **Calibrate at Operating Temperature** - Bias drifts with temperature
4. **Check CRC on Burst Data (ADIS)** - Validates data integrity, essential for safety-critical apps
5. **Configure Filters Appropriately** - Match filter to application bandwidth
6. **Handle Overruns Gracefully** - Monitor data counter for gaps, log overrun events
7. **Use Interrupts for Efficiency** - Avoid polling for data ready
8. **Validate Range Selection** - Check for saturation, ensure accelerations stay within range

## Common Use Cases

**Vibration Monitoring**: High sample rate (3200 Hz), wide range (±16g), FIFO buffering

**Motion-Triggered Wake**: Ultra-low power, activity detection, interrupt-driven

**Orientation Detection**: Low rate (50 Hz), sensitive range (±2g), angle calculation

**High-Precision IMU Logging**: Burst read, CRC validation, decimation filtering

**Tap Detection**: Configure tap duration/threshold, map to interrupt pins

**Step Counter**: Activity detection, data filtering, peak detection on magnitude

See `reference/api-usage.md` for complete examples.

## Reference Examples

- **ADXL345**: `projects/adxl345/src/examples/basic/basic_example.c`
- **ADXL362**: `projects/adxl362/src/examples/`
- **ADIS16475**: `projects/adis16475/src/examples/`
- **IIO Integration**: `drivers/imu/adis_iio.c`

## Reference Documentation

**When to read each file** (use Read tool):

### reference/implementation.md
Complete implementation patterns: device descriptors, initialization, data acquisition, FIFO, motion detection, power management, filters, IIO integration, page registers (ADIS).

### reference/api-usage.md
Complete usage examples for all common applications: vibration monitoring, motion wake, orientation, IMU logging, tap detection, free-fall, step counting, activity/inactivity state machines. Includes testing patterns.

### reference/calibration.md
Comprehensive calibration guide: offset calibration (ADXL), bias correction (ADIS), temperature compensation, scale factor verification, auto-calibration routines, storing calibration data, accuracy specifications.

### reference/best-practices.md
Essential best practices: burst read patterns, FIFO usage, CRC validation, calibration timing, filter configuration, data validation, interrupt management, power optimization, code quality, testing, performance.

### reference/troubleshooting.md
Systematic troubleshooting: no device response, incorrect data, noisy data, saturation, FIFO overflow, interrupt issues, ADIS page registers, burst CRC errors, clock sync, calibration problems, performance issues, debugging techniques.

---

## Summary

**Quick Start**: Use ADXL345 for general-purpose acceleration, ADXL362 for ultra-low power, ADIS for high-precision synchronized IMU data.

**Key Patterns**: Burst read for synchronized data, FIFO for high-rate acquisition, interrupt-driven for efficiency, calibration for accuracy.

**Essential Functions**: init → set_range → set_rate → configure FIFO/interrupts → calibrate → read_xyz/burst_data

**Read reference files for**: Complete implementation details, specific use cases, calibration procedures, best practices, troubleshooting.
