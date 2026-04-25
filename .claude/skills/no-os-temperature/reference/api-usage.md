# Temperature Sensor API Usage Examples

This document provides complete usage examples for common temperature sensor operations.

## Common Use Cases

### 1. Simple Temperature Monitoring

```c
// Basic temperature logging
struct adt7420_dev *temp_sensor;
struct adt7420_init_param init = {
    .resolution_setting = ADT7420_RESOLUTION_16_BIT,
    .op_mode = ADT7420_OP_MODE_CONT_CONV,
};

ret = adt7420_init(&temp_sensor, init);

while (monitoring) {
    float temp;
    ret = adt7420_get_temperature(temp_sensor, &temp);
    log_temperature(temp);
    no_os_mdelay(1000);  // 1 second interval
}
```

### 2. Overheat Protection

```c
// Configure critical temperature alert
ret = adt7420_set_critical_limit(dev, 85.0);  // Shutdown at 85°C
ret = adt7420_set_ct_polarity(dev, ADT7420_CT_ACTIVE_LOW);

// Configure CT pin as interrupt
struct no_os_gpio_init_param ct_gpio_init = {
    .number = CT_PIN,
    .platform_ops = &gpio_ops,
};
ret = no_os_gpio_get(&ct_gpio, &ct_gpio_init);
ret = no_os_gpio_direction_input(ct_gpio);

// Interrupt triggers emergency shutdown
void critical_temp_isr(void *context)
{
    pr_err("CRITICAL TEMPERATURE EXCEEDED!\n");
    emergency_shutdown();
}
```

### 3. Industrial RTD Measurement

```c
// High-precision 4-wire PT100 measurement
struct max31865_init_param init = {
    .rtd_type = MAX31865_PT100,
    .wire_mode = MAX31865_4WIRE,
    .r_ref = 4020,               // 4.02k reference resistor (measured)
    .filter_mode = MAX31865_FILTER_60HZ,
};

ret = max31865_init(&dev, &init);

// Continuous monitoring with fault detection
while (1) {
    float temp;
    uint8_t fault;

    ret = max31865_read_temp(dev, &temp);
    ret = max31865_read_fault_status(dev, &fault);

    if (fault) {
        pr_err("RTD fault: 0x%02X\n", fault);
        handle_rtd_fault(fault);
    } else {
        pr_info("Temperature: %.3f C\n", temp);
    }

    no_os_mdelay(500);
}
```

### 4. Multi-Point Temperature System (LTC2983)

```c
// Monitor multiple temperature points
struct ltc2983_dev *temp_hub;

// Setup 4 thermocouples + 4 RTDs + 2 thermistors
// ... (setup code from Multi-Sensor section) ...

// Periodic scan of all sensors
while (1) {
    ret = ltc2983_start_conversion(dev, LTC2983_CONVERSION_ALL);
    ret = ltc2983_wait_for_conversion(dev, 5000);  // 5s timeout

    float temps[20];
    for (int ch = 1; ch <= 20; ch++) {
        if (dev->sensors[ch].type != LTC2983_SENSOR_TYPE_NONE) {
            ltc2983_read_channel_temp(dev, ch, &temps[ch]);
            pr_info("Ch%d: %.2f C\n", ch, temps[ch]);
        }
    }

    no_os_mdelay(10000);  // 10 second interval
}
```

## Digital Temperature Sensors (I2C)

### ADT7420 High-Precision Sensor

```c
// Initialize ADT7420
struct adt7420_dev *dev;
struct adt7420_init_param init = {
    .i2c_init = {
        .device_id = 0,
        .max_speed_hz = 400000,  // 400kHz
        .slave_address = 0x48,    // A1=A0=GND
        .platform_ops = &i2c_ops,
    },
    .resolution_setting = ADT7420_RESOLUTION_16_BIT,
    .op_mode = ADT7420_OP_MODE_CONT_CONV,
};

ret = adt7420_init(&dev, &init);

// Configure thresholds for alert
ret = adt7420_set_high_limit(dev, 45.0);
ret = adt7420_set_low_limit(dev, 15.0);
ret = adt7420_set_critical_limit(dev, 60.0);
ret = adt7420_set_hysteresis(dev, 2);

// Read temperature continuously
while (1) {
    float temp;
    ret = adt7420_get_temperature(dev, &temp);
    
    if (ret == 0) {
        pr_info("Temperature: %.4f C\n", temp);
    }
    
    no_os_mdelay(1000);
}
```

### LM75 Basic Temperature Sensor

```c
// Initialize LM75
struct lm75_dev *dev;
struct lm75_init_param init = {
    .i2c_init = {
        .device_id = 0,
        .max_speed_hz = 400000,
        .slave_address = 0x48,
        .platform_ops = &i2c_ops,
    },
};

ret = lm75_init(&dev, &init);

// Simple temperature reading
float temp;
ret = lm75_get_temperature(dev, &temp);
pr_info("Temperature: %.2f C\n", temp);

// Configure shutdown mode for power saving
ret = lm75_set_shutdown_mode(dev, true);

// Wake up and read
ret = lm75_set_shutdown_mode(dev, false);
no_os_mdelay(1);  // Wait for conversion
ret = lm75_get_temperature(dev, &temp);
```

## RTD Temperature Measurement (SPI)

### MAX31865 RTD-to-Digital Converter

```c
// PT100 4-wire configuration
struct max31865_dev *dev;
struct max31865_init_param init = {
    .spi_init = {
        .device_id = 0,
        .max_speed_hz = 5000000,  // 5MHz
        .mode = NO_OS_SPI_MODE_1,
        .chip_select = 0,
        .platform_ops = &spi_ops,
    },
    .rtd_type = MAX31865_PT100,
    .wire_mode = MAX31865_4WIRE,
    .r_ref = 4000,  // 4k reference resistor
    .filter_mode = MAX31865_FILTER_60HZ,
};

ret = max31865_init(&dev, &init);

// Enable bias voltage
ret = max31865_enable_bias(dev, true);
no_os_mdelay(10);  // Wait for bias to settle

// Enable automatic conversion
ret = max31865_enable_auto_convert(dev, true);

// Continuous reading
while (1) {
    float temp;
    uint8_t fault;
    
    ret = max31865_read_temp(dev, &temp);
    ret = max31865_read_fault_status(dev, &fault);
    
    if (fault == 0) {
        pr_info("RTD Temperature: %.3f C\n", temp);
    } else {
        pr_err("RTD Fault: 0x%02X\n", fault);
        
        if (fault & MAX31865_FAULT_HIGH_THRESHOLD)
            pr_err("  - RTD resistance too high\n");
        if (fault & MAX31865_FAULT_LOW_THRESHOLD)
            pr_err("  - RTD resistance too low\n");
        
        // Clear fault and retry
        max31865_clear_fault(dev);
    }
    
    no_os_mdelay(1000);
}
```

### PT1000 3-Wire Configuration

```c
// PT1000 3-wire for industrial use
struct max31865_init_param init = {
    .spi_init = { /* SPI config */ },
    .rtd_type = MAX31865_PT1000,
    .wire_mode = MAX31865_3WIRE,
    .r_ref = 4000,
    .filter_mode = MAX31865_FILTER_50HZ,  // Europe
};

ret = max31865_init(&dev, &init);

// One-shot measurement for low power
ret = max31865_enable_bias(dev, true);
no_os_mdelay(10);

ret = max31865_start_one_shot(dev);
no_os_mdelay(65);  // Wait for conversion (60Hz filter)

float temp;
ret = max31865_read_temp(dev, &temp);

ret = max31865_enable_bias(dev, false);  // Save power
```

## Thermocouple Temperature Measurement (SPI)

### MAX31855 Thermocouple-to-Digital Converter

```c
// Type K thermocouple
struct max31855_dev *dev;
struct max31855_init_param init = {
    .spi_init = {
        .device_id = 0,
        .max_speed_hz = 5000000,
        .mode = NO_OS_SPI_MODE_0,
        .chip_select = 0,
        .platform_ops = &spi_ops,
    },
};

ret = max31855_init(&dev, &init);

// Read thermocouple and internal temperature
while (1) {
    float tc_temp, internal_temp;
    uint8_t fault;
    
    ret = max31855_read_temp(dev, &tc_temp);
    ret = max31855_read_internal_temp(dev, &internal_temp);
    ret = max31855_read_fault(dev, &fault);
    
    if (fault == 0) {
        pr_info("Thermocouple: %.2f C\n", tc_temp);
        pr_info("Cold Junction: %.2f C\n", internal_temp);
    } else {
        pr_err("Fault detected: 0x%02X\n", fault);
        
        if (fault & MAX31855_FAULT_OPEN)
            pr_err("  - Thermocouple open circuit\n");
        if (fault & MAX31855_FAULT_SHORT_GND)
            pr_err("  - Short to ground\n");
        if (fault & MAX31855_FAULT_SHORT_VCC)
            pr_err("  - Short to VCC\n");
    }
    
    no_os_mdelay(250);  // MAX31855 updates every 100ms
}
```

## Multi-Sensor Hub (LTC2983)

### Complete Multi-Sensor System

```c
// Initialize LTC2983
struct ltc2983_dev *dev;
struct ltc2983_init_param init = {
    .spi_init = {
        .device_id = 0,
        .max_speed_hz = 1000000,  // 1MHz
        .mode = NO_OS_SPI_MODE_0,
        .chip_select = 0,
        .platform_ops = &spi_ops,
    },
    .filter_notch_freq = 60,  // 60Hz
};

ret = ltc2983_init(&dev, &init);

// Channel 1: Type K thermocouple with CJ on channel 2
struct ltc2983_sensor tc_sensor = {
    .type = LTC2983_SENSOR_TYPE_THERMOCOUPLE_K,
    .channel = 1,
    .config.thermocouple = {
        .cold_junction_ch = 2,
        .single_ended = true,
        .oc_current = LTC2983_OC_10UA,
        .oc_check = true,
    },
};
ret = ltc2983_setup_sensor(dev, 1, &tc_sensor);

// Channel 2: Diode for cold junction
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
ret = ltc2983_setup_sensor(dev, 2, &diode_sensor);

// Channel 5: PT100 RTD (4-wire) with Rsense on channel 4
struct ltc2983_sensor rtd_sensor = {
    .type = LTC2983_SENSOR_TYPE_RTD_PT100,
    .channel = 5,
    .config.rtd = {
        .rsense_ch = 4,
        .wire_mode = LTC2983_RTD_4_WIRE,
        .excitation_mode = LTC2983_RTD_EXCITATION_ROTATION_SHARING,
        .excitation_current = LTC2983_RTD_CURRENT_500UA,
        .rtd_curve = LTC2983_RTD_CURVE_EUROPEAN,
    },
};
ret = ltc2983_setup_sensor(dev, 5, &rtd_sensor);

// Continuous multi-channel measurement
while (1) {
    // Start all channels
    ret = ltc2983_start_conversion(dev, LTC2983_CONVERSION_ALL);
    
    // Wait for completion
    ret = ltc2983_wait_for_conversion(dev, 5000);
    
    // Read all channels
    float temp;
    
    ret = ltc2983_read_channel_temp(dev, 1, &temp);
    pr_info("Thermocouple: %.2f C\n", temp);
    
    ret = ltc2983_read_channel_temp(dev, 5, &temp);
    pr_info("RTD: %.3f C\n", temp);
    
    no_os_mdelay(1000);
}
```

### Single Channel Conversion

```c
// Read only one channel at a time for faster updates
while (1) {
    float temp;
    
    // Start conversion on channel 5 only
    ret = ltc2983_start_conversion(dev, 5);
    
    // Wait for completion (much faster than all channels)
    ret = ltc2983_wait_for_conversion(dev, 1000);
    
    // Read result
    ret = ltc2983_read_channel_temp(dev, 5, &temp);
    pr_info("RTD: %.3f C\n", temp);
    
    no_os_mdelay(100);  // Fast update rate
}
```

## Power Management

### Low-Power One-Shot Mode

```c
// ADT7420 one-shot mode
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_SHUTDOWN);

// When measurement needed
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_ONE_SHOT);

// Wait for conversion (240ms for 16-bit)
no_os_mdelay(240);

float temp;
ret = adt7420_get_temperature(dev, &temp);

// Return to shutdown
ret = adt7420_set_operation_mode(dev, ADT7420_OP_MODE_SHUTDOWN);
```

### RTD Power Cycling

```c
// Disable bias when not measuring
ret = max31865_enable_bias(dev, false);

// When measurement needed
ret = max31865_enable_bias(dev, true);
no_os_mdelay(10);  // Bias settling time

ret = max31865_start_one_shot(dev);
no_os_mdelay(65);  // Conversion time

float temp;
ret = max31865_read_temp(dev, &temp);

// Disable bias again
ret = max31865_enable_bias(dev, false);
```

## Reference Examples

Complete project examples available at:

- **ADT7420**: `projects/adt7420/src/examples/`
- **LTC2983**: `projects/ltc2983/src/examples/`
- **MAX31865**: `projects/max31865/src/examples/`
- **IIO Integration**: Check `drivers/temperature/*/iio_*.c` files
