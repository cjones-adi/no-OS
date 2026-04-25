# IMU Driver Implementation Patterns

Complete reference for implementing IMU, accelerometer, and gyroscope drivers in the no-OS framework.

## Architecture Overview

### IMU Types

1. **MEMS Accelerometers** (ADXL family)
   - Measure linear acceleration on X, Y, Z axes
   - Ranges: ±2g, ±4g, ±8g, ±16g (some up to ±200g)
   - Digital output via SPI/I2C
   - Motion detection features

2. **MEMS Gyroscopes** (ADXRS, ADXL355)
   - Measure angular velocity (rotation rate)
   - Ranges: ±125°/s to ±2000°/s
   - Temperature compensation
   - Low drift specifications

3. **Combined IMU** (ADIS family)
   - Integrated 3-axis gyroscope + 3-axis accelerometer
   - Often includes magnetometer, barometer
   - Factory calibrated
   - Synchronized burst data reads
   - High-precision tactical/industrial grade

## Device Descriptor Patterns

**Accelerometer Device Descriptor**:
```c
struct adxl345_dev {
    struct no_os_spi_desc *spi_desc;      // Or i2c_desc
    struct no_os_gpio_desc *int1_gpio;    // Interrupt 1 pin
    struct no_os_gpio_desc *int2_gpio;    // Interrupt 2 pin
    enum adxl345_range selected_range;     // Current g-range
    enum adxl345_fifo_mode fifo_mode;      // FIFO configuration
    uint8_t comm_type;                     // SPI or I2C
};
```

**IMU Device Descriptor (ADIS)**:
```c
struct adis_dev {
    struct adis_chip_info *info;           // Device-specific info
    struct no_os_spi_desc *spi_desc;       // SPI interface
    struct no_os_gpio_desc *gpio_reset;    // Hardware reset
    uint32_t current_page;                 // Register page
    struct adis_timeout ext_clk;           // External clock timeout
    enum adis_clk_mode clk_mode;           // Clock mode
    uint32_t clk_freq;                     // Clock frequency
};
```

## Initialization Parameters

**Accelerometer Initialization**:
```c
struct adxl345_init_param {
    struct no_os_spi_init_param spi_init;
    struct no_os_i2c_init_param i2c_init;
    struct no_os_gpio_init_param int1_param;
    struct no_os_gpio_init_param int2_param;
    uint8_t comm_type;                     // ADXL345_SPI_COMM or I2C
};
```

**IMU Initialization**:
```c
struct adis_init_param {
    struct no_os_spi_init_param *spi_init;
    struct no_os_gpio_init_param *gpio_reset;
    uint32_t sync_clk_freq_hz;             // Sync clock (if used)
    uint16_t sync_clk_gating;              // Clock gating config
};
```

## Data Acquisition Patterns

### Simple X/Y/Z Read
```c
// Reading acceleration data
int16_t x, y, z;
ret = adxl345_get_xyz(dev, &x, &y, &z);

// Convert to g units
float x_g = (float)x * dev->scale_factor;  // scale_factor depends on range

// Gyro angular rate
int32_t gyro_x, gyro_y, gyro_z;  // °/s * 100 or similar fixed-point
ret = adxrs290_get_rate_data(dev, ADXRS290_DATAX, &gyro_x);
ret = adxrs290_get_rate_data(dev, ADXRS290_DATAY, &gyro_y);
```

### Burst Data Read (ADIS IMUs)
```c
// Synchronized read of all sensors
struct adis_burst_data data;
ret = adis_read_burst_data(adis, &data);

// Data structure contains:
// - data.accel_x/y/z     (accelerometer)
// - data.gyro_x/y/z      (gyroscope)
// - data.temp            (temperature)
// - data.data_cntr       (sample counter)
// - data.crc             (data integrity)
```

**Why Burst Read?**
- Ensures gyro/accel/temp are time-synchronized
- Single transaction reduces SPI overhead
- Includes data counter for detecting missed samples
- CRC validation for data integrity

## Range and Resolution Configuration

### Accelerometer Range
```c
// Set measurement range (affects sensitivity and scale)
enum adxl345_range {
    ADXL345_RANGE_PM_2G = 0,   // ±2g, most sensitive
    ADXL345_RANGE_PM_4G = 1,   // ±4g
    ADXL345_RANGE_PM_8G = 2,   // ±8g
    ADXL345_RANGE_PM_16G = 3,  // ±16g, least sensitive
};

ret = adxl345_set_range(dev, ADXL345_RANGE_PM_4G);

// Scale factors (LSB/g):
// ±2g:  256 LSB/g  (3.9 mg resolution)
// ±4g:  128 LSB/g  (7.8 mg resolution)
// ±8g:  64 LSB/g   (15.6 mg resolution)
// ±16g: 32 LSB/g   (31.2 mg resolution)
```

### Data Rate Configuration
```c
// Output Data Rate (ODR)
enum adxl345_odr {
    ADXL345_ODR_3200_HZ = 0xF,   // 3200 Hz
    ADXL345_ODR_1600_HZ = 0xE,   // 1600 Hz
    ADXL345_ODR_800_HZ = 0xD,    // 800 Hz
    ADXL345_ODR_400_HZ = 0xC,    // 400 Hz
    ADXL345_ODR_200_HZ = 0xB,    // 200 Hz
    ADXL345_ODR_100_HZ = 0xA,    // 100 Hz (typical)
    // ... down to 0.10 Hz
};

ret = adxl345_set_rate(dev, ADXL345_ODR_100_HZ);
```

## FIFO Implementation

### FIFO Modes
```c
enum adxl345_fifo_mode {
    ADXL345_FIFO_BYPASS = 0,      // FIFO disabled
    ADXL345_FIFO_FIFO = 1,        // Stop when full
    ADXL345_FIFO_STREAM = 2,      // Circular buffer (oldest data lost)
    ADXL345_FIFO_TRIGGER = 3,     // Collect around trigger event
};

// Enable FIFO with watermark
ret = adxl345_set_fifo_mode(dev, ADXL345_FIFO_STREAM);
ret = adxl345_set_fifo_samples(dev, 20);  // Interrupt when 20 samples

// Read FIFO entries
uint8_t entries;
ret = adxl345_get_fifo_entries(dev, &entries);
for (int i = 0; i < entries; i++) {
    adxl345_get_xyz(dev, &x, &y, &z);
    // Process data...
}
```

### Decimation (ADIS)
```c
// Reduce output data rate via decimation
uint16_t dec_rate = 100;  // Decimate by 100
ret = adis_write_dec_rate(adis, dec_rate);
// Effective ODR = Base_Rate / dec_rate
```

## Motion Detection Features

### Tap Detection
```c
struct adxl345_tap_config {
    uint8_t tap_axes;           // X, Y, Z enable
    uint8_t tap_dur;            // Duration threshold (625 µs/LSB)
    uint8_t tap_latent;         // Latency between taps
    uint8_t tap_window;         // Window for double-tap
    uint8_t tap_thresh;         // Tap threshold (62.5 mg/LSB)
};

struct adxl345_tap_config tap = {
    .tap_axes = ADXL345_TAP_Z_EN,
    .tap_dur = 20,              // ~12.5 ms
    .tap_thresh = 48,           // ~3g
};
ret = adxl345_set_tap_detection(dev, &tap);
```

### Activity/Inactivity Detection
```c
// Activity threshold (motion detection)
ret = adxl345_set_thresh_act(dev, 10);  // 10 * 62.5mg = 625mg threshold

// Inactivity threshold and time
ret = adxl345_set_thresh_inact(dev, 5);   // 312.5mg
ret = adxl345_set_time_inact(dev, 30);    // 30 seconds

// Free-fall detection
ret = adxl345_set_thresh_ff(dev, 7);      // ~437mg
ret = adxl345_set_time_ff(dev, 20);       // 100ms (5ms/LSB)
```

### Interrupt Mapping
```c
// Map events to INT1 or INT2 pins
enum adxl345_int_pin {
    ADXL345_INT1 = 0,
    ADXL345_INT2 = 1,
};

// Single tap to INT1, double tap to INT2
ret = adxl345_set_interrupt_mapping(dev,
    ADXL345_SINGLE_TAP, ADXL345_INT1);
ret = adxl345_set_interrupt_mapping(dev,
    ADXL345_DOUBLE_TAP, ADXL345_INT2);

// Enable interrupts
ret = adxl345_enable_interrupt(dev, ADXL345_SINGLE_TAP, true);
ret = adxl345_enable_interrupt(dev, ADXL345_DOUBLE_TAP, true);
```

## Advanced Features

### Clock Configuration (ADIS)
```c
// Internal clock
ret = adis_initial_startup(adis);

// External sync clock
struct adis_init_param init = {
    .spi_init = &spi_init,
    .gpio_reset = &gpio_reset_init,
    .sync_clk_freq_hz = 2000,        // 2 kHz sync
    .sync_clk_gating = 0,             // No gating
};
ret = adis_init(&adis, &init);

// Scaled sync mode
ret = adis_write_sync_mode(adis, ADIS_SYNC_SCALED);
ret = adis_write_up_scale(adis, 100);  // Scale factor
```

### Power Management
```c
// Low power mode (ADXL362)
enum adxl362_power_mode {
    ADXL362_STANDBY = 0,
    ADXL362_MEASUREMENT = 1,
};
ret = adxl362_set_power_mode(dev, ADXL362_MEASUREMENT);

// Ultra-low noise mode (higher power)
ret = adxl362_set_low_noise(dev, true);

// Auto-sleep (wake on motion)
ret = adxl362_setup_activity_detection(dev, ...);
ret = adxl362_set_autosleep(dev, true);
```

### Filter Configuration
```c
// Digital filter selection
enum adxl345_filter {
    ADXL345_FILTER_HPF = 0,  // High-pass filter
    ADXL345_FILTER_LPF = 1,  // Low-pass filter (default)
};

// Low-pass filter for anti-aliasing
ret = adxl345_set_filter(dev, ADXL345_FILTER_LPF);

// Bartlett FIR filter (ADIS)
ret = adis_write_filt_size_var_b(adis, 16);  // 16-tap filter
```

## IIO Integration

### IIO Channels
```c
static struct iio_channel adxl345_channels[] = {
    {
        .name = "accel_x",
        .ch_type = IIO_ACCEL,
        .modified = true,
        .channel2 = IIO_MOD_X,
        .scan_type = &adxl345_scan_type,
        .attributes = adxl345_channel_attributes,
    },
    {
        .name = "accel_y",
        .ch_type = IIO_ACCEL,
        .modified = true,
        .channel2 = IIO_MOD_Y,
        // ...
    },
    // Z channel, temperature channel...
};

// Read callback
static int adxl345_iio_read_raw(void *dev, char *buf, uint32_t len,
                                const struct iio_ch_info *channel,
                                intptr_t priv)
{
    struct adxl345_dev *adxl345 = dev;
    int16_t x, y, z;
    int ret;

    ret = adxl345_get_xyz(adxl345, &x, &y, &z);
    if (ret)
        return ret;

    switch (channel->ch_num) {
    case 0:  // X
        return iio_format_value(buf, len, IIO_VAL_INT, 1, &x);
    case 1:  // Y
        return iio_format_value(buf, len, IIO_VAL_INT, 1, &y);
    case 2:  // Z
        return iio_format_value(buf, len, IIO_VAL_INT, 1, &z);
    default:
        return -EINVAL;
    }
}
```

### IIO Attributes
```c
static struct iio_attribute adxl345_attrs[] = {
    {
        .name = "sampling_frequency",
        .show = adxl345_get_sampling_freq,
        .store = adxl345_set_sampling_freq,
    },
    {
        .name = "range",
        .show = adxl345_get_range_attr,
        .store = adxl345_set_range_attr,
    },
    END_ATTRIBUTES_ARRAY
};
```

## ADIS Page Register Management

Many ADIS devices use paged register addressing:

```c
// Select page before register access
ret = adis_write_reg(adis, 0x00, 0x02, 2);  // Select page 2

// Always verify page before register access
uint16_t current_page;
adis_read_reg(adis, 0x00, &current_page, 2);
if (current_page != expected_page) {
    pr_err("Wrong page: %d (expected %d)\n",
           current_page, expected_page);
}
```

## Reference Examples

- **ADXL345 Example**: `projects/adxl345/src/examples/basic/basic_example.c`
- **ADXL362 Example**: `projects/adxl362/src/examples/`
- **ADIS16475 Example**: `projects/adis16475/src/examples/`
- **IIO Integration**: `drivers/imu/adis_iio.c`
