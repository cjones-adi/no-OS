# Temperature Sensor Implementation Patterns

This document covers driver implementation patterns for all temperature sensor types in no-OS.

## Architecture Overview

### Temperature Sensor Types

1. **Digital Temperature Sensors** (ADT7420, ADT75, LM75, MAX31827)
   - Integrated sensor and ADC
   - I2C interface
   - Direct temperature readout (°C)
   - Typical resolution: 0.0625°C (16-bit)
   - Accuracy: ±0.25°C to ±2°C

2. **RTD (Resistance Temperature Detector) Converters** (MAX31865)
   - External Pt100/Pt1000 RTD sensor
   - SPI interface
   - Wide temperature range: -200°C to +850°C
   - High accuracy with proper calibration
   - Ratiometric measurement

3. **Thermocouple Converters** (MAX31855, MAX31856)
   - External K, J, N, T, E, R, S type thermocouples
   - SPI interface
   - Very wide range: -200°C to +1800°C (type K)
   - Cold-junction compensation
   - High-temperature applications

4. **Multi-Sensor Temperature Hub** (LTC2983)
   - Up to 20 temperature sensors
   - Supports RTDs, thermocouples, thermistors, diodes
   - Automatic linearization
   - SPI interface
   - Integrated cold-junction compensation

## Common Design Patterns

### Device Descriptor

```c
struct adt7420_dev {
    struct no_os_i2c_desc *i2c_desc;       // I2C interface
    uint8_t resolution_setting;            // 13-bit or 16-bit
    enum adt7420_op_mode op_mode;          // Continuous, one-shot, etc.
    uint8_t ct_pin_polarity;               // Critical temp alert polarity
    uint8_t int_pin_polarity;              // Interrupt pin polarity
};

struct max31865_dev {
    struct no_os_spi_desc *spi_desc;       // SPI interface
    enum max31865_rtd_type rtd_type;       // PT100 or PT1000
    enum max31865_wire_mode wire_mode;     // 2-wire, 3-wire, or 4-wire
    uint16_t r_ref;                        // Reference resistor (ohms)
    uint8_t filter_mode;                   // 50Hz or 60Hz noise rejection
};

struct ltc2983_dev {
    struct no_os_spi_desc *spi_desc;
    struct ltc2983_sensor sensors[20];     // Up to 20 channels
    uint8_t num_sensors;                   // Active sensor count
    uint32_t mux_delay_us;                 // Mux settling delay
    uint32_t filter_notch_freq;            // 50Hz or 60Hz
};
```

### Initialization Parameters

```c
struct adt7420_init_param {
    struct no_os_i2c_init_param i2c_init;
    uint8_t resolution_setting;            // ADT7420_RESOLUTION_13_BIT or 16
    enum adt7420_op_mode op_mode;          // Operating mode
};

struct max31865_init_param {
    struct no_os_spi_init_param spi_init;
    enum max31865_rtd_type rtd_type;       // PT100 or PT1000
    enum max31865_wire_mode wire_mode;     // Wire configuration
    uint16_t r_ref;                        // Reference resistor value
    uint8_t filter_mode;                   // Noise filter
};
```

## Core Functionality

### Temperature Reading

#### Simple Temperature Read (Digital Sensors)

```c
// Read temperature (blocking)
float temperature;
ret = adt7420_get_temperature(dev, &temperature);
pr_info("Temperature: %.2f C\n", temperature);

// Raw 16-bit read
uint16_t raw_temp;
ret = adt7420_read_raw(dev, &raw_temp);

// Convert to temperature
// 16-bit mode: LSB = 0.0078125°C, sign-extended
int16_t signed_temp = (int16_t)raw_temp;
float temp = (float)signed_temp / 128.0;  // Divide by 128 for 16-bit
```

#### RTD Temperature Read

```c
// Read RTD temperature
float rtd_temp;
ret = max31865_read_temp(dev, &rtd_temp);
pr_info("RTD Temperature: %.3f C\n", rtd_temp);

// Read RTD resistance
uint16_t rtd_raw;
ret = max31865_read_rtd(dev, &rtd_raw);

// Calculate resistance
// RTD = (RTD_data * Rref) / 32768
float rtd_resistance = ((float)rtd_raw * dev->r_ref) / 32768.0;
pr_info("RTD Resistance: %.2f ohms\n", rtd_resistance);

// Convert to temperature using Callendar-Van Dusen equation
// For Pt100: approximate linearization
// R(T) = R0 * (1 + A*T + B*T^2)
// Where R0 = 100 ohms, A = 3.9083e-3, B = -5.775e-7
```

#### Thermocouple Temperature Read

```c
// Read thermocouple temperature
float tc_temp;
ret = max31855_read_temp(dev, &tc_temp);

// Also read internal (cold junction) temperature
float internal_temp;
ret = max31855_read_internal_temp(dev, &internal_temp);

pr_info("Thermocouple: %.2f C, Internal: %.2f C\n",
        tc_temp, internal_temp);

// Check for faults
uint8_t fault;
ret = max31855_read_fault(dev, &fault);
if (fault & MAX31855_FAULT_OPEN) {
    pr_err("Thermocouple open circuit\n");
}
if (fault & MAX31855_FAULT_SHORT_GND) {
    pr_err("Thermocouple short to ground\n");
}
if (fault & MAX31855_FAULT_SHORT_VCC) {
    pr_err("Thermocouple short to VCC\n");
}
```

### Resolution and Mode Configuration

#### Resolution Settings

```c
enum adt7420_resolution {
    ADT7420_RESOLUTION_13_BIT = 0,     // 0.0625°C, 60ms conversion
    ADT7420_RESOLUTION_16_BIT = 1,     // 0.0078°C, 240ms conversion
};

// Set resolution (affects conversion time and precision)
ret = adt7420_set_resolution(dev, ADT7420_RESOLUTION_16_BIT);

// 13-bit: faster conversions, lower power
// 16-bit: higher precision, longer conversion time
```

#### Operating Modes

```c
enum adt7420_op_mode {
    ADT7420_OP_MODE_CONT_CONV = 0,     // Continuous conversion
    ADT7420_OP_MODE_ONE_SHOT = 1,      // Single conversion
    ADT7420_OP_MODE_1_SPS = 2,         // 1 sample/sec
    ADT7420_OP_MODE_SHUTDOWN = 3,      // Low power shutdown
};

// Continuous mode for monitoring
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_CONT_CONV);

// One-shot for low-power applications
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_ONE_SHOT);
ret = adt7420_get_temperature(dev, &temp);  // Triggers conversion
```

#### RTD Wire Configuration

```c
enum max31865_wire_mode {
    MAX31865_2WIRE = 0,  // 2-wire: +1°C error/wire, simple
    MAX31865_3WIRE = 1,  // 3-wire: compensates lead resistance
    MAX31865_4WIRE = 2,  // 4-wire: best accuracy, eliminates lead resistance
};

// For best accuracy, use 4-wire
ret = max31865_set_wires(dev, MAX31865_4WIRE);

// 3-wire common for industrial applications (balanced trade-off)
ret = max31865_set_wires(dev, MAX31865_3WIRE);
```

### Alert and Threshold Configuration

#### Temperature Thresholds

```c
// Set high limit (interrupt threshold)
ret = adt7420_set_high_limit(dev, 50.0);   // Alert at 50°C

// Set low limit
ret = adt7420_set_low_limit(dev, -10.0);   // Alert below -10°C

// Set critical temperature (separate pin)
ret = adt7420_set_critical_limit(dev, 80.0);  // Critical at 80°C

// Set hysteresis to prevent flapping
ret = adt7420_set_hysteresis(dev, 2);  // 2°C hysteresis
```

#### Interrupt Configuration

```c
// Configure interrupt mode
enum adt7420_int_mode {
    ADT7420_INT_MODE_COMPARATOR = 0,  // Level-triggered
    ADT7420_INT_MODE_INTERRUPT = 1,   // Latch until cleared
};

ret = adt7420_set_int_mode(dev, ADT7420_INT_MODE_INTERRUPT);

// Set interrupt polarity
ret = adt7420_set_int_polarity(dev, ADT7420_INT_ACTIVE_LOW);

// Clear interrupt
ret = adt7420_clear_interrupt(dev);

// Interrupt handler
void temp_alert_isr(void *context)
{
    struct adt7420_dev *dev = context;
    float temp;

    adt7420_get_temperature(dev, &temp);
    pr_warn("Temperature alert: %.2f C\n", temp);

    // Clear interrupt
    adt7420_clear_interrupt(dev);
}
```

#### RTD Fault Detection

```c
// Configure fault detection
ret = max31865_enable_fault_detection(dev, true);

// Automatic or manual fault detection
ret = max31865_set_fault_detection_mode(dev, MAX31865_FAULT_AUTO);

// Read fault status
uint8_t fault_status;
ret = max31865_read_fault_status(dev, &fault_status);

if (fault_status & MAX31865_FAULT_HIGH_THRESHOLD) {
    pr_err("RTD resistance too high (open circuit?)\n");
}
if (fault_status & MAX31865_FAULT_LOW_THRESHOLD) {
    pr_err("RTD resistance too low (short circuit?)\n");
}
if (fault_status & MAX31865_FAULT_REFIN_LOW) {
    pr_err("REFIN- < 0.85 x Vbias\n");
}
if (fault_status & MAX31865_FAULT_VOLTAGE) {
    pr_err("Under/overvoltage fault\n");
}
```

### Multi-Sensor Configuration (LTC2983)

#### Sensor Setup

```c
// Configure different sensor types on different channels

// Channel 1: Type K thermocouple
struct ltc2983_sensor tc_sensor = {
    .type = LTC2983_SENSOR_TYPE_THERMOCOUPLE_K,
    .channel = 1,
    .config = {
        .thermocouple = {
            .cold_junction_ch = 2,         // CJ on channel 2
            .single_ended = true,
            .oc_current = LTC2983_OC_10UA, // Open-circuit detect
            .oc_check = true,
        },
    },
};
ret = ltc2983_setup_sensor(dev, 1, &tc_sensor);

// Channel 2: Internal temperature sensor (for CJ compensation)
struct ltc2983_sensor diode_sensor = {
    .type = LTC2983_SENSOR_TYPE_DIODE,
    .channel = 2,
    .config = {
        .diode = {
            .single_ended = true,
            .num_readings = LTC2983_DIODE_3_READINGS,
            .averaging = true,
            .current = LTC2983_DIODE_CURRENT_10UA,
        },
    },
};
ret = ltc2983_setup_sensor(dev, 2, &diode_sensor);

// Channel 5: PT100 RTD (4-wire)
struct ltc2983_sensor rtd_sensor = {
    .type = LTC2983_SENSOR_TYPE_RTD_PT100,
    .channel = 5,
    .config = {
        .rtd = {
            .rsense_ch = 4,                // Reference resistor on ch 4
            .wire_mode = LTC2983_RTD_4_WIRE,
            .excitation_mode = LTC2983_RTD_EXCITATION_ROTATION_SHARING,
            .excitation_current = LTC2983_RTD_CURRENT_500UA,
            .rtd_curve = LTC2983_RTD_CURVE_EUROPEAN,
        },
    },
};
ret = ltc2983_setup_sensor(dev, 5, &rtd_sensor);

// Channel 10: Thermistor (NTC 10k)
struct ltc2983_sensor thermistor_sensor = {
    .type = LTC2983_SENSOR_TYPE_THERMISTOR_44006,
    .channel = 10,
    .config = {
        .thermistor = {
            .rsense_ch = 9,
            .single_ended = true,
            .excitation_mode = LTC2983_THERMISTOR_EXCITATION_SHARING_NO_ROTATION,
            .excitation_current = LTC2983_THERMISTOR_CURRENT_AUTORANGE,
        },
    },
};
ret = ltc2983_setup_sensor(dev, 10, &thermistor_sensor);
```

#### Multi-Channel Measurement

```c
// Start conversion on all channels
ret = ltc2983_start_conversion(dev, LTC2983_CONVERSION_ALL);

// Wait for completion
uint8_t status;
do {
    ret = ltc2983_get_conversion_status(dev, &status);
    no_os_mdelay(10);
} while (status & LTC2983_STATUS_BUSY);

// Read all temperatures
for (int ch = 1; ch <= dev->num_sensors; ch++) {
    if (dev->sensors[ch].type != LTC2983_SENSOR_TYPE_NONE) {
        float temp;
        ret = ltc2983_read_channel_temp(dev, ch, &temp);
        pr_info("Channel %d: %.3f C\n", ch, temp);
    }
}

// Or single-channel conversion
ret = ltc2983_start_conversion(dev, 5);  // Just channel 5
ret = ltc2983_wait_for_conversion(dev, 1000);  // 1s timeout
float rtd_temp;
ret = ltc2983_read_channel_temp(dev, 5, &rtd_temp);
```

### Noise Filtering

#### 50Hz/60Hz Line Noise Rejection

```c
// Configure notch filter for power line frequency
enum max31865_filter {
    MAX31865_FILTER_60HZ = 0,  // 60Hz rejection (Americas)
    MAX31865_FILTER_50HZ = 1,  // 50Hz rejection (Europe/Asia)
};

ret = max31865_set_filter(dev, MAX31865_FILTER_60HZ);

// LTC2983 global filter
ret = ltc2983_set_filter_notch(dev, 60);  // 60Hz
```

#### Averaging (Digital Sensors)

```c
// Software averaging for noise reduction
float temp_sum = 0;
const int num_samples = 16;

for (int i = 0; i < num_samples; i++) {
    float temp;
    adt7420_get_temperature(dev, &temp);
    temp_sum += temp;
    no_os_mdelay(10);
}

float avg_temp = temp_sum / num_samples;
pr_info("Averaged temperature: %.3f C\n", avg_temp);
```

## IIO Integration

### IIO Channels (Example: ADT7420)

```c
static struct iio_channel adt7420_channels[] = {
    {
        .name = "temp",
        .ch_type = IIO_TEMP,
        .indexed = false,
        .scan_type = &adt7420_scan_type,
        .attributes = adt7420_channel_attributes,
    },
};

static int adt7420_iio_read_raw(void *dev, char *buf, uint32_t len,
                                const struct iio_ch_info *channel,
                                intptr_t priv)
{
    struct adt7420_dev *adt7420 = dev;
    float temp;
    int ret;

    ret = adt7420_get_temperature(adt7420, &temp);
    if (ret)
        return ret;

    // Convert to milli-degrees Celsius for IIO
    int32_t temp_millicelsius = (int32_t)(temp * 1000);

    return iio_format_value(buf, len, IIO_VAL_INT, 1, &temp_millicelsius);
}
```

### IIO Attributes

```c
static struct iio_attribute adt7420_attrs[] = {
    {
        .name = "resolution",
        .show = adt7420_get_resolution_attr,
        .store = adt7420_set_resolution_attr,
    },
    {
        .name = "high_threshold",
        .show = adt7420_get_high_limit_attr,
        .store = adt7420_set_high_limit_attr,
    },
    {
        .name = "low_threshold",
        .show = adt7420_get_low_limit_attr,
        .store = adt7420_set_low_limit_attr,
    },
    END_ATTRIBUTES_ARRAY
};
```
