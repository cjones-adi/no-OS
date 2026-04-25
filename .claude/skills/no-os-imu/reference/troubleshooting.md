# IMU Troubleshooting Guide

Comprehensive troubleshooting guide for common IMU, accelerometer, and gyroscope driver issues.

## Device Communication Issues

### No Device Response

**Symptom**: Driver initialization fails, device ID read returns wrong value or error.

**Diagnostic Steps**:
```c
// Check device ID
uint8_t dev_id;
ret = adxl345_get_device_id(dev, &dev_id);
if (dev_id != ADXL345_DEVICE_ID) {
    pr_err("Wrong device ID: 0x%02X (expected 0x%02X)\n",
           dev_id, ADXL345_DEVICE_ID);
}
```

**Common Causes**:

1. **Wrong SPI Mode**
   - ADXL345: SPI Mode 3 (CPOL=1, CPHA=1)
   - ADIS: SPI Mode 3
   ```c
   // Fix: Set correct SPI mode
   struct no_os_spi_init_param spi_init = {
       .mode = NO_OS_SPI_MODE_3,  // Correct mode
       .chip_select = 0,
       .max_speed_hz = 5000000,
   };
   ```

2. **Incorrect Chip Select Polarity**
   ```c
   // Some platforms need active-low CS
   spi_init.cs_polarity = NO_OS_SPI_CS_ACTIVE_LOW;
   ```

3. **SPI Clock Too Fast**
   - ADXL345 max: 5 MHz
   - ADIS max: typically 2 MHz (check datasheet)
   ```c
   spi_init.max_speed_hz = 2000000;  // Reduce to 2 MHz
   ```

4. **Power Supply Issues**
   - Check VDD is stable (typically 2.0V-3.6V)
   - Verify power-on delay (1-5ms after power applied)
   ```c
   // Add power-on delay
   no_os_mdelay(5);
   ret = adxl345_init(&dev, &init_param);
   ```

5. **I2C Address Mismatch** (for I2C devices)
   ```c
   // ADXL345: 0x53 (ALT low) or 0x1D (ALT high)
   i2c_init.slave_address = 0x53;  // Check schematic
   ```

### ADIS Status Check

```c
// Check diagnostic status
uint16_t diag_stat;
ret = adis_read_diag_stat(adis, &diag_stat);

if (diag_stat & ADIS_DIAG_CHECKSUM_ERR) {
    pr_err("Flash checksum error - device may be damaged\n");
}
if (diag_stat & ADIS_DIAG_SENSOR_FAIL) {
    pr_err("Sensor self-test failure\n");
}
if (diag_stat & ADIS_DIAG_MEM_FAIL) {
    pr_err("Memory failure\n");
}
if (diag_stat & ADIS_DIAG_OVERRANGE) {
    pr_err("Sensor overrange - reduce input or increase range\n");
}
```

## Data Quality Issues

### Incorrect Data Values

**Symptom**: Data readings don't match expected values (e.g., Z-axis doesn't read 1g at rest).

**Diagnostic Steps**:

1. **Verify Range Setting**
   ```c
   enum adxl345_range range;
   adxl345_get_range(dev, &range);
   pr_info("Current range: ±%dg\n", 2 << range);
   
   // Check data format register
   uint8_t data_format;
   adxl345_read_reg(dev, ADXL345_REG_DATA_FORMAT, &data_format);
   pr_info("Full resolution: %s\n",
           (data_format & 0x08) ? "enabled" : "disabled");
   pr_info("Justify: %s\n",
           (data_format & 0x04) ? "left" : "right");
   ```

2. **Verify Scale Factor**
   ```c
   float scale = get_scale_factor(range);
   pr_info("Scale: %.3f mg/LSB\n", scale * 1000);
   
   // At ±2g range: expect 256 LSB/g (3.9 mg/LSB)
   // Z-axis at rest should read ~256 LSB (1g)
   ```

3. **Check Offset Registers**
   ```c
   int8_t offset_x, offset_y, offset_z;
   adxl345_get_offset(dev, ADXL345_X_AXIS, &offset_x);
   adxl345_get_offset(dev, ADXL345_Y_AXIS, &offset_y);
   adxl345_get_offset(dev, ADXL345_Z_AXIS, &offset_z);
   pr_info("Offsets: X=%d, Y=%d, Z=%d (15.6mg/LSB)\n",
           offset_x, offset_y, offset_z);
   
   // Clear and re-test
   adxl345_set_offset(dev, ADXL345_X_AXIS, 0);
   adxl345_set_offset(dev, ADXL345_Y_AXIS, 0);
   adxl345_set_offset(dev, ADXL345_Z_AXIS, 0);
   ```

4. **Check Measurement Mode**
   ```c
   uint8_t power_ctl;
   adxl345_read_reg(dev, ADXL345_REG_POWER_CTL, &power_ctl);
   if (!(power_ctl & 0x08)) {
       pr_err("Device in standby - enable measurement mode\n");
       adxl345_set_power_mode(dev, ADXL345_MEASUREMENT);
   }
   ```

### Noisy Data

**Symptom**: Data fluctuates excessively, high variance.

**Solutions**:

1. **Enable Low-Pass Filter**
   ```c
   adxl345_set_filter(dev, ADXL345_FILTER_LPF);
   ```

2. **Reduce Sample Rate**
   ```c
   // Lower rate = more filtering
   adxl345_set_rate(dev, ADXL345_ODR_100_HZ);  // From 3200 Hz
   ```

3. **Increase Filter Taps (ADIS)**
   ```c
   // More taps = lower noise (but higher latency)
   adis_write_filt_size_var_b(adis, 16);  // From 2
   ```

4. **Software Averaging**
   ```c
   int32_t avg_x = 0;
   for (int i = 0; i < 10; i++) {
       int16_t x;
       adxl345_get_xyz(dev, &x, NULL, NULL);
       avg_x += x;
       no_os_mdelay(10);
   }
   avg_x /= 10;  // 10-sample average
   ```

5. **Check Mechanical Isolation**
   - Vibrations from fans, motors propagate to sensor
   - Use vibration damping mounts
   - Place sensor away from noise sources

### Data Saturation

**Symptom**: Data stuck at maximum values (±512 at ±2g range).

```c
int16_t x, y, z;
adxl345_get_xyz(dev, &x, &y, &z);

if (abs(x) >= 500 || abs(y) >= 500 || abs(z) >= 500) {
    pr_warn("Saturation detected - increase range\n");
    
    // Increase range
    enum adxl345_range range;
    adxl345_get_range(dev, &range);
    if (range < ADXL345_RANGE_PM_16G) {
        adxl345_set_range(dev, range + 1);
        pr_info("Increased to ±%dg range\n", 2 << (range + 1));
    } else {
        pr_err("Already at maximum range - input exceeds sensor capability\n");
    }
}
```

## FIFO Issues

### FIFO Overflow

**Symptom**: FIFO overflow bit set, data lost.

**Diagnostic**:
```c
uint8_t fifo_status;
adxl345_read_reg(dev, ADXL345_REG_FIFO_STATUS, &fifo_status);

uint8_t entries = fifo_status & 0x3F;
bool overflow = fifo_status & 0x80;

pr_info("FIFO entries: %d\n", entries);
if (overflow) {
    pr_warn("FIFO overflow - data lost\n");
}
```

**Solutions**:

1. **Increase Read Rate**
   ```c
   // Read FIFO more frequently
   // If ODR=100Hz, FIFO=32 samples → read every 320ms max
   ```

2. **Reduce Watermark**
   ```c
   adxl345_set_fifo_samples(dev, 16);  // From 32
   // Interrupt fires sooner, less risk of overflow
   ```

3. **Use Stream Mode**
   ```c
   // Oldest data discarded on overflow (vs. stop collecting)
   adxl345_set_fifo_mode(dev, ADXL345_FIFO_STREAM);
   ```

4. **Check Interrupt Service Latency**
   ```c
   // Measure ISR response time
   void fifo_isr(void) {
       static uint32_t last_time = 0;
       uint32_t now = get_tick_count();
       
       pr_debug("ISR latency: %u ms\n", now - last_time);
       last_time = now;
       
       // Read FIFO...
   }
   ```

### FIFO Not Filling

**Symptom**: FIFO entries always 0 or 1.

**Checks**:
```c
// Verify FIFO enabled
uint8_t fifo_ctl;
adxl345_read_reg(dev, ADXL345_REG_FIFO_CTL, &fifo_ctl);

uint8_t mode = (fifo_ctl >> 6) & 0x03;
uint8_t samples = fifo_ctl & 0x1F;

pr_info("FIFO mode: %d (0=bypass, 1=FIFO, 2=stream, 3=trigger)\n", mode);
pr_info("FIFO watermark: %d samples\n", samples);

if (mode == 0) {
    pr_err("FIFO in bypass mode - enable FIFO/stream mode\n");
}
```

## Interrupt Issues

### Interrupt Not Firing

**Symptom**: Interrupt callback never executes.

**Diagnostic Steps**:

1. **Check Interrupt Source**
   ```c
   uint8_t int_source;
   adxl345_read_reg(dev, ADXL345_REG_INT_SOURCE, &int_source);
   pr_info("INT source: 0x%02X\n", int_source);
   
   if (int_source & ADXL345_DATA_READY) {
       pr_info("Data ready interrupt occurred\n");
   } else {
       pr_warn("No data ready interrupt\n");
   }
   ```

2. **Verify Interrupt Enable**
   ```c
   uint8_t int_enable;
   adxl345_read_reg(dev, ADXL345_REG_INT_ENABLE, &int_enable);
   pr_info("INT enable: 0x%02X\n", int_enable);
   
   if (!(int_enable & ADXL345_DATA_READY)) {
       pr_err("Data ready interrupt not enabled\n");
       adxl345_enable_interrupt(dev, ADXL345_DATA_READY, true);
   }
   ```

3. **Check Interrupt Mapping**
   ```c
   uint8_t int_map;
   adxl345_read_reg(dev, ADXL345_REG_INT_MAP, &int_map);
   pr_info("INT map (1=INT2): 0x%02X\n", int_map);
   
   // If bit is 0, event goes to INT1
   // If bit is 1, event goes to INT2
   ```

4. **Verify GPIO Configuration**
   ```c
   // Check GPIO direction (input)
   // Check GPIO pull-up/pull-down
   // Check GPIO interrupt edge (rising/falling)
   
   struct no_os_gpio_init_param int1_param = {
       .number = INT1_PIN,
       .platform_ops = &platform_gpio_ops,
       .extra = &gpio_extra,
       .pull = NO_OS_PULL_NONE,  // ADXL345 has internal pull-down
   };
   
   no_os_gpio_direction_input(dev->int1_gpio);
   no_os_gpio_set_edge(dev->int1_gpio, NO_OS_GPIO_EDGE_RISING);
   ```

5. **Test Interrupt Manually**
   ```c
   // Force interrupt by reading data
   int16_t x, y, z;
   adxl345_get_xyz(dev, &x, &y, &z);
   
   // Check if INT source cleared
   adxl345_read_reg(dev, ADXL345_REG_INT_SOURCE, &int_source);
   pr_info("After read, INT source: 0x%02X\n", int_source);
   ```

### Interrupt Firing Continuously

**Symptom**: Interrupt handler called repeatedly, system locked.

**Cause**: Interrupt source not cleared.

**Solution**:
```c
void data_ready_isr(void) {
    // Read interrupt source to clear it
    uint8_t int_source;
    adxl345_read_reg(dev, ADXL345_REG_INT_SOURCE, &int_source);
    
    // Process interrupt
    if (int_source & ADXL345_DATA_READY) {
        adxl345_get_xyz(dev, &x, &y, &z);
        // Reading data clears DATA_READY flag
    }
    
    // Interrupt automatically de-asserts
}
```

## ADIS-Specific Issues

### Page Register Problems

**Symptom**: Register reads/writes fail or return unexpected values.

**Cause**: Wrong register page selected.

```c
// Many ADIS devices use paged register addressing
// Always select page before register access

// Bad
ret = adis_write_reg(adis, 0x80, value, 2);  // Which page?

// Good
ret = adis_write_reg(adis, 0x00, 0x02, 2);  // Select page 2
ret = adis_write_reg(adis, 0x80, value, 2);  // Write to page 2 register

// Always verify page
uint16_t current_page;
adis_read_reg(adis, 0x00, &current_page, 2);
if (current_page != expected_page) {
    pr_err("Wrong page: %d (expected %d)\n",
           current_page, expected_page);
}
```

### Burst Data CRC Errors

**Symptom**: CRC validation fails frequently.

**Diagnostic**:
```c
struct adis_burst_data data;
ret = adis_read_burst_data(adis, &data);

uint16_t calc_crc = calculate_crc16(&data, sizeof(data) - 2);
if (data.crc != calc_crc) {
    pr_err("CRC error: expected 0x%04X, got 0x%04X\n",
           calc_crc, data.crc);
    
    // Dump raw data for analysis
    pr_debug("Raw burst data:\n");
    for (int i = 0; i < sizeof(data); i++) {
        pr_debug("%02X ", ((uint8_t*)&data)[i]);
    }
}
```

**Solutions**:

1. **Reduce SPI Clock Speed**
   ```c
   // CRC errors often indicate signal integrity issues
   spi_init.max_speed_hz = 1000000;  // Reduce to 1 MHz
   ```

2. **Check SPI Wiring**
   - Keep traces short (<6 inches)
   - Use ground plane
   - Add series termination resistor (22-47Ω) on SCLK

3. **Verify Timing**
   ```c
   // Some ADIS devices need delay between burst trigger and read
   adis_write_reg(adis, ADIS_REG_GLOB_CMD, ADIS_BURST_CMD, 2);
   no_os_udelay(10);  // 10µs delay
   adis_read_burst_data(adis, &data);
   ```

### Clock Synchronization Issues

**Symptom**: External sync clock not working, data rate incorrect.

**Diagnostic**:
```c
// Check sync mode
uint16_t sync_mode;
adis_read_sync_mode(adis, &sync_mode);
pr_info("Sync mode: %u\n", sync_mode);

// Check decimation
uint16_t dec_rate;
adis_read_dec_rate(adis, &dec_rate);
pr_info("Decimation: %u\n", dec_rate);

// Expected ODR = Base_ODR / (dec_rate + 1)
```

**Solution**:
```c
// Configure external sync
adis_write_sync_mode(adis, ADIS_SYNC_SCALED);
adis_write_up_scale(adis, 0);  // No upscaling
adis_write_dec_rate(adis, 9);  // Divide by 10

// Verify sync clock signal with oscilloscope
// Check frequency, duty cycle, voltage levels
```

## Calibration Issues

### Calibration Doesn't Improve Accuracy

**Symptom**: After calibration, offset still large.

**Checks**:

1. **Device Not at Rest**
   ```c
   // Verify device stationary during calibration
   int16_t x1, x2;
   adxl345_get_xyz(dev, &x1, NULL, NULL);
   no_os_mdelay(100);
   adxl345_get_xyz(dev, &x2, NULL, NULL);
   
   if (abs(x2 - x1) > 10) {
       pr_err("Device moving - calibration invalid\n");
       return -EINVAL;
   }
   ```

2. **Temperature Not Stable**
   ```c
   // Wait for thermal equilibrium
   int32_t temp1, temp2;
   adis_read_temp_out(adis, &temp1);
   no_os_mdelay(10000);  // 10 seconds
   adis_read_temp_out(adis, &temp2);
   
   if (abs(temp2 - temp1) > 100) {  // >1°C change
       pr_warn("Temperature unstable - wait longer\n");
   }
   ```

3. **Insufficient Sample Size**
   ```c
   // Use at least 100 samples for calibration
   #define CAL_SAMPLES 1000  // More = better averaging
   ```

## Performance Issues

### Data Rate Lower Than Expected

**Symptom**: Getting fewer samples than configured ODR.

**Diagnostic**:
```c
// Measure actual sample rate
uint32_t start_time = get_tick_count();
uint32_t sample_count = 0;

for (int i = 0; i < 1000; i++) {
    adxl345_get_xyz(dev, &x, &y, &z);
    sample_count++;
}

uint32_t elapsed = get_tick_count() - start_time;
float actual_rate = (float)sample_count / (elapsed / 1000.0);

pr_info("Configured: 100 Hz, Actual: %.2f Hz\n", actual_rate);
```

**Causes**:
- SPI transaction overhead
- Interrupt latency
- Processing time too long

**Solutions**:
```c
// Use FIFO to batch reads
adxl345_set_fifo_mode(dev, ADXL345_FIFO_STREAM);
adxl345_set_fifo_samples(dev, 20);

// Use DMA for SPI transfers
spi_init.use_dma = true;

// Optimize interrupt handler (defer processing)
void data_ready_isr(void) {
    // Quick read, defer processing
    adxl345_get_xyz(dev, &buffer[index++], NULL, NULL);
    if (index >= BUFFER_SIZE) {
        signal_process_data();  // Process in main loop
        index = 0;
    }
}
```

## Debugging Techniques

### Register Dump

```c
void adxl345_dump_registers(struct adxl345_dev *dev)
{
    pr_info("ADXL345 Register Dump:\n");
    
    uint8_t regs[] = {
        0x00,  // DEVID
        0x1D,  // THRESH_TAP
        0x2D,  // POWER_CTL
        0x2E,  // INT_ENABLE
        0x2F,  // INT_MAP
        0x30,  // INT_SOURCE
        0x31,  // DATA_FORMAT
        0x38,  // FIFO_CTL
        0x39,  // FIFO_STATUS
    };
    
    for (int i = 0; i < sizeof(regs); i++) {
        uint8_t val;
        adxl345_read_reg(dev, regs[i], &val);
        pr_info("  [0x%02X] = 0x%02X\n", regs[i], val);
    }
}
```

### Continuous Monitoring

```c
// Monitor for anomalies
void monitor_imu_health(struct adis_dev *adis)
{
    static uint16_t last_cntr = 0;
    static uint32_t crc_errors = 0;
    
    struct adis_burst_data data;
    ret = adis_read_burst_data(adis, &data);
    
    // Check data counter
    uint16_t expected = (last_cntr + 1) & 0xFFFF;
    if (data.data_cntr != expected && last_cntr != 0) {
        pr_warn("Missed samples: %u\n", data.data_cntr - expected);
    }
    last_cntr = data.data_cntr;
    
    // Check CRC
    if (!validate_crc(&data)) {
        crc_errors++;
        pr_warn("CRC error count: %u\n", crc_errors);
    }
    
    // Check diagnostic status
    uint16_t diag;
    adis_read_diag_stat(adis, &diag);
    if (diag != 0) {
        pr_warn("Diagnostic errors: 0x%04X\n", diag);
    }
}
```
