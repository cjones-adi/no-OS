# ADC Calibration Procedures

Complete guide to ADC calibration methods for achieving measurement accuracy.

---

## Calibration Types

### Factory Calibration

**Description**:
- Pre-programmed at manufacturing
- No user action required
- Automatically applied

---

### System Calibration (measure external reference)

**Zero-Scale Calibration** (offset):
```c
ret = ad7124_calibrate(dev, AD7124_SYS_ZERO_SCALE_CAL, channel);
```

**Full-Scale Calibration** (gain):
```c
ret = ad7124_calibrate(dev, AD7124_SYS_FULL_SCALE_CAL, channel);
```

---

### Self-Calibration (internal calibration)

**Internal Zero-Scale**:
```c
ret = ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, channel);
```

**Internal Full-Scale**:
```c
ret = ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, channel);
```

---

## System Calibration Workflow

**Complete Example**:
```c
// 1. Apply zero-scale input (short inputs or connect to ground)
pr_info("Apply zero-scale input (0V), press enter\n");
getchar();

// 2. Perform zero-scale calibration
ret = ad7124_calibrate(dev, AD7124_SYS_ZERO_SCALE_CAL, 0);
if (ret) {
    pr_err("Zero-scale calibration failed: %d\n", ret);
    return ret;
}

// 3. Apply full-scale input (known reference voltage)
pr_info("Apply full-scale input (e.g., 2.5V), press enter\n");
getchar();

// 4. Perform full-scale calibration
ret = ad7124_calibrate(dev, AD7124_SYS_FULL_SCALE_CAL, 0);
if (ret) {
    pr_err("Full-scale calibration failed: %d\n", ret);
    return ret;
}

pr_info("Calibration complete\n");
```

---

## When to Use Each Calibration Type

### Internal (Self) Calibration

**When to use**:
- Initial device setup
- After power-on
- Periodically for drift compensation
- No external equipment available

**Advantages**:
- Fully automated
- No user intervention required
- Quick execution

**Limitations**:
- Corrects internal errors only
- Does not account for external components (resistors, references)

**Example**:
```c
// Perform self-calibration at startup
ret = ad7124_init(&dev, &init_param);

// Internal calibration
ret = ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 0);
ret = ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, 0);
```

---

### System Calibration

**When to use**:
- Precision measurements required
- Compensate for external component errors
- PCB trace resistance affects readings
- Initial factory test/calibration

**Advantages**:
- Calibrates entire signal chain
- Accounts for external resistances, references
- Highest accuracy

**Limitations**:
- Requires known reference voltages
- User intervention needed
- Manual test procedure

**Example**:
```c
// Manufacturing test station calibration
// 1. Apply precision 0V (short inputs)
apply_zero_scale_voltage();
ret = ad7124_calibrate(dev, AD7124_SYS_ZERO_SCALE_CAL, 0);

// 2. Apply precision reference (2.500V)
apply_full_scale_voltage(2500);  // 2.500V reference
ret = ad7124_calibrate(dev, AD7124_SYS_FULL_SCALE_CAL, 0);
```

---

## Digital Offset/Gain Correction

**Manual Correction** (AD7768-1 example):
```c
// Apply digital offset correction
int32_t offset = -1000;  // Negative offset
ret = ad77681_apply_offset(dev, offset);

// Apply digital gain correction
uint32_t gain = 0x555555;  // Adjust gain slightly
ret = ad77681_apply_gain(dev, gain);
```

**Use Cases**:
- Fine-tune calibration
- Software-based correction
- Compensate for known systematic errors

---

## Calibration Best Practices

### 1. Calibration Frequency

**At startup**: Always perform internal calibration
```c
ret = ad7124_init(&dev, &init_param);
ret = ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 0);
ret = ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, 0);
```

**Periodic**: Re-calibrate based on temperature drift
```c
// Every N minutes or after temperature change
if (temperature_changed || time_elapsed > RECAL_INTERVAL) {
    ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 0);
    ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, 0);
}
```

---

### 2. Calibration Settling Time

**Wait for settling** after applying calibration voltage:
```c
// Apply zero-scale input
apply_zero_voltage();

// Wait for input to settle
no_os_mdelay(100);  // 100ms settling time

// Perform calibration
ret = ad7124_calibrate(dev, AD7124_SYS_ZERO_SCALE_CAL, 0);
```

---

### 3. Per-Setup Calibration (Sigma-Delta)

Different setups (gain, reference) require separate calibration:
```c
// Setup 0: Gain=1, calibrate
ad7124_setup_channel(dev, 0, setup0, ch0_map, filter0);
ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 0);

// Setup 1: Gain=8, calibrate separately
ad7124_setup_channel(dev, 1, setup1, ch1_map, filter1);
ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 1);
```

---

### 4. Verify Calibration

**Read calibration coefficients**:
```c
uint32_t offset_coeff, gain_coeff;

// Read stored calibration values
ret = ad7124_reg_read(dev, AD7124_OFFSET_REG(setup), &offset_coeff);
ret = ad7124_reg_read(dev, AD7124_GAIN_REG(setup), &gain_coeff);

pr_info("Calibration - Offset: 0x%06X, Gain: 0x%06X\n",
        offset_coeff, gain_coeff);
```

**Verify with known input**:
```c
// Apply known voltage (e.g., 1.000V)
apply_test_voltage(1000);

// Read and compare
uint32_t data;
float voltage;
ad7124_read_data(dev, &data, &channel);
ad7124_convert_sample_to_voltage(dev, channel, data, &voltage);

float error = voltage - 1000.0;
pr_info("Error: %.2f mV (%.2f%%)\n", error, (error / 1000.0) * 100);
```

---

## Calibration Error Handling

```c
int perform_calibration_with_retry(struct ad7124_desc *dev, uint8_t channel)
{
    int ret;
    int retry_count = 0;
    const int MAX_RETRIES = 3;

    // Zero-scale calibration with retry
    for (retry_count = 0; retry_count < MAX_RETRIES; retry_count++) {
        ret = ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, channel);
        if (ret == 0)
            break;

        pr_warn("Zero-scale calibration failed, retry %d/%d\n",
                retry_count + 1, MAX_RETRIES);
        no_os_mdelay(10);
    }

    if (ret) {
        pr_err("Zero-scale calibration failed after retries\n");
        return ret;
    }

    // Full-scale calibration with retry
    for (retry_count = 0; retry_count < MAX_RETRIES; retry_count++) {
        ret = ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, channel);
        if (ret == 0)
            break;

        pr_warn("Full-scale calibration failed, retry %d/%d\n",
                retry_count + 1, MAX_RETRIES);
        no_os_mdelay(10);
    }

    if (ret) {
        pr_err("Full-scale calibration failed after retries\n");
        return ret;
    }

    pr_info("Calibration successful\n");
    return 0;
}
```

---

## Temperature Compensation

**Monitor temperature and re-calibrate**:
```c
float last_temp = 25.0;
const float TEMP_THRESHOLD = 5.0;  // 5°C threshold

while (1) {
    float current_temp = read_temperature_sensor();

    // Re-calibrate if temperature changed significantly
    if (fabs(current_temp - last_temp) > TEMP_THRESHOLD) {
        pr_info("Temperature drift detected (%.1f°C), re-calibrating\n",
                current_temp - last_temp);

        ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 0);
        ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, 0);

        last_temp = current_temp;
    }

    // Normal measurement
    ad7124_read_data(dev, &data, &channel);
    // Process data...

    no_os_mdelay(1000);
}
```

---

## Calibration Storage (Optional)

**Save calibration to non-volatile memory**:
```c
struct calibration_data {
    uint32_t offset_coeff;
    uint32_t gain_coeff;
    uint32_t checksum;
};

int save_calibration(struct ad7124_desc *dev, uint8_t setup)
{
    struct calibration_data cal_data;
    int ret;

    // Read calibration coefficients
    ret = ad7124_reg_read(dev, AD7124_OFFSET_REG(setup), &cal_data.offset_coeff);
    ret = ad7124_reg_read(dev, AD7124_GAIN_REG(setup), &cal_data.gain_coeff);

    // Calculate checksum
    cal_data.checksum = cal_data.offset_coeff ^ cal_data.gain_coeff;

    // Write to EEPROM or flash
    ret = eeprom_write(CAL_ADDR, &cal_data, sizeof(cal_data));

    return ret;
}

int restore_calibration(struct ad7124_desc *dev, uint8_t setup)
{
    struct calibration_data cal_data;
    int ret;

    // Read from EEPROM or flash
    ret = eeprom_read(CAL_ADDR, &cal_data, sizeof(cal_data));
    if (ret)
        return ret;

    // Verify checksum
    uint32_t checksum = cal_data.offset_coeff ^ cal_data.gain_coeff;
    if (checksum != cal_data.checksum) {
        pr_err("Calibration data corrupted\n");
        return -EINVAL;
    }

    // Restore calibration coefficients
    ret = ad7124_reg_write(dev, AD7124_OFFSET_REG(setup), cal_data.offset_coeff);
    ret = ad7124_reg_write(dev, AD7124_GAIN_REG(setup), cal_data.gain_coeff);

    pr_info("Calibration restored from memory\n");
    return 0;
}
```
