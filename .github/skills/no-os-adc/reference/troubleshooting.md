# ADC Troubleshooting Guide

Common issues and debugging techniques for ADC drivers.

---

## Issue: No Data or All Zeros

### Symptoms
- `ad7124_read_data()` returns 0x000000
- Continuous reading gives same value
- Channel appears inactive

### Possible Causes
- Reference voltage not configured
- Channel not enabled
- Wrong conversion mode
- SPI communication error

### Debug Steps

**1. Verify device ID**:
```c
uint32_t id;
ret = ad7124_reg_read(dev, AD7124_ID_REG, &id);
pr_debug("Device ID: 0x%02X (expected 0x14)\n", id);
```

**2. Check reference configuration**:
```c
uint32_t config;
ret = ad7124_reg_read(dev, AD7124_CONFIG_REG(0), &config);
pr_debug("Config reg: 0x%06X\n", config);
```

**3. Verify channel is enabled**:
```c
uint32_t ch_reg;
ret = ad7124_reg_read(dev, AD7124_CHANNEL_REG(0), &ch_reg);
pr_debug("Channel 0 reg: 0x%04X, enabled: %s\n",
         ch_reg, (ch_reg & AD7124_CH_ENABLE) ? "yes" : "no");
```

**4. Check ADC mode**:
```c
uint32_t mode_reg;
ret = ad7124_reg_read(dev, AD7124_ADC_CTRL_REG, &mode_reg);
pr_debug("ADC mode: %u\n", (mode_reg >> 2) & 0x7);
```

**5. Verify SPI communication**:
```c
// Read multiple times to check consistency
for (int i = 0; i < 5; i++) {
    ret = ad7124_reg_read(dev, AD7124_ID_REG, &id);
    pr_debug("Read %d: ID = 0x%02X, ret = %d\n", i, id, ret);
}
```

### Solutions

**Enable channel properly**:
```c
struct ad7124_channel_map ch_map = {
    .channel_enable = true,          // CRITICAL!
    .setup_sel = 0,
    .ainp = AD7124_AIN0,
    .ainm = AD7124_AVSS,
};
```

**Set conversion mode**:
```c
ret = ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);
```

**Configure reference voltage**:
```c
init_param.vref_mv = 2500;  // 2.5V
```

---

## Issue: Noisy or Unstable Readings

### Symptoms
- Readings fluctuate significantly
- Inconsistent values for same input
- Large deviation in measurements

### Possible Causes
- Reference buffer disabled (high impedance source)
- Input buffer disabled
- Incorrect filter selection
- ODR too high for application
- Poor PCB layout (noise coupling)

### Debug Steps

**1. Check buffer configuration**:
```c
uint32_t config;
ret = ad7124_reg_read(dev, AD7124_CONFIG_REG(0), &config);
pr_debug("Ref buffer: %s\n", (config & AD7124_REF_BUFF) ? "ON" : "OFF");
pr_debug("Input buffer: %s\n", (config & AD7124_IN_BUFF) ? "ON" : "OFF");
```

**2. Verify filter settings**:
```c
uint32_t filter_reg;
ret = ad7124_reg_read(dev, AD7124_FILTER_REG(0), &filter_reg);
pr_debug("Filter: %u, ODR: %u\n",
         (filter_reg >> 21) & 0x7,
         filter_reg & 0x7FF);
```

**3. Take multiple readings to measure noise**:
```c
#define NUM_SAMPLES 100
uint32_t samples[NUM_SAMPLES];
float sum = 0, sum_sq = 0;

for (int i = 0; i < NUM_SAMPLES; i++) {
    ad7124_read_data(dev, &samples[i], &channel);
    sum += samples[i];
    sum_sq += samples[i] * samples[i];
}

float mean = sum / NUM_SAMPLES;
float variance = (sum_sq / NUM_SAMPLES) - (mean * mean);
float std_dev = sqrt(variance);

pr_debug("Mean: %.2f, Std Dev: %.2f\n", mean, std_dev);
```

### Solutions

**Enable buffers for high-impedance sources**:
```c
setup.ref_buff = true;
setup.input_buff = true;
```

**Use slower filter for better noise performance**:
```c
filter.filter = AD7124_SINC5_FILTER;
filter.odr = AD7124_ODR_19_SPS;  // Slow ODR
filter.enhfilten = true;          // 50/60Hz rejection
```

**Increase gain if signal is small**:
```c
setup.pga = AD7124_PGA_GAIN_32;
```

**Check PCB layout**:
- Separate analog and digital ground planes
- Keep ADC traces short
- Shield sensitive analog traces
- Use proper decoupling capacitors

---

## Issue: Conversion Timeout

### Symptoms
- `ad7124_wait_for_ready()` returns -ETIMEDOUT
- RDY signal never asserts
- No conversion results available

### Possible Causes
- RDY signal not configured
- Filter settling time too long
- Device stuck in error state
- Wrong conversion mode

### Debug Steps

**1. Check status register**:
```c
uint32_t status;
ret = ad7124_read_status(dev, &status);
pr_debug("Status: 0x%02X\n", status);
pr_debug("  RDY: %u\n", (status & AD7124_STATUS_RDY) ? 1 : 0);
pr_debug("  ERROR: %u\n", (status & AD7124_STATUS_ERROR) ? 1 : 0);
pr_debug("  CHANNEL: %u\n", status & 0x0F);
```

**2. Verify ADC mode**:
```c
uint32_t ctrl_reg;
ret = ad7124_reg_read(dev, AD7124_ADC_CTRL_REG, &ctrl_reg);
pr_debug("ADC Control: 0x%04X\n", ctrl_reg);
pr_debug("  Mode: %u\n", (ctrl_reg >> 2) & 0x7);
```

**3. Check filter settling time**:
```c
// Calculate expected settling time
uint32_t odr = get_odr_value(dev, 0);  // Get ODR in SPS
float settling_time_ms = (1000.0 / odr) * 3;  // 3x ODR period
pr_debug("Expected settling time: %.2f ms\n", settling_time_ms);
```

### Solutions

**Increase timeout**:
```c
// Use longer timeout for slow ODR
ret = ad7124_wait_for_ready(dev, 5000);  // 5 second timeout
```

**Reset ADC**:
```c
ret = ad7124_reset(dev);

// Re-initialize
ret = ad7124_init(&dev, &init_param);
```

**Verify conversion mode**:
```c
// Ensure ADC is in active mode
ret = ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);
```

---

## Issue: Incorrect Voltage Readings

### Symptoms
- Voltage calculation doesn't match expected value
- Readings are offset or scaled incorrectly
- Negative values when expecting positive

### Possible Causes
- Wrong reference voltage in descriptor
- Incorrect gain setting
- Bipolar/unipolar mismatch
- Calibration needed
- Code conversion formula error

### Debug Steps

**1. Verify reference voltage**:
```c
pr_debug("Reference voltage: %u mV\n", dev->vref_mv);
```

**2. Check gain**:
```c
uint32_t config;
ret = ad7124_reg_read(dev, AD7124_CONFIG_REG(0), &config);
uint8_t pga = (config >> 0) & 0x7;
pr_debug("PGA gain: %u\n", 1 << pga);
```

**3. Verify bipolar/unipolar**:
```c
pr_debug("Mode: %s\n",
         (config & AD7124_BIPOLAR) ? "BIPOLAR" : "UNIPOLAR");
```

**4. Check raw codes**:
```c
uint32_t raw_code;
ret = ad7124_read_data(dev, &raw_code, &channel);
pr_debug("Raw code: 0x%06X (%u)\n", raw_code, raw_code);
```

**5. Verify conversion formula**:
```c
// Bipolar: -Vref/Gain to +Vref/Gain
// Code 0x800000 = 0V
// Code 0x7FFFFF = +Vref/Gain
// Code 0x000000 = -Vref/Gain (actually wraps to 0x800000)

// Unipolar: 0 to Vref/Gain
// Code 0x000000 = 0V
// Code 0xFFFFFF = Vref/Gain
```

### Solutions

**Set correct reference voltage**:
```c
init_param.vref_mv = 2500;  // Must match actual reference
```

**Verify conversion formula** (bipolar):
```c
int32_t signed_code = (int32_t)raw_code - 0x800000;
float voltage = ((float)signed_code / 0x800000) * (vref_mv / gain);
```

**Verify conversion formula** (unipolar):
```c
float voltage = ((float)raw_code / 0xFFFFFF) * (vref_mv / gain);
```

**Perform calibration**:
```c
ret = ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 0);
ret = ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, 0);
```

---

## Issue: SPI Communication Errors

### Symptoms
- All register reads return 0xFF or 0x00
- Cannot read device ID
- Write operations don't take effect

### Possible Causes
- Wrong SPI mode (CPOL/CPHA)
- Incorrect SPI clock frequency
- CS signal not working
- MOSI/MISO swapped
- Power supply issue

### Debug Steps

**1. Verify SPI configuration**:
```c
pr_debug("SPI mode: %u\n", spi_desc->mode);
pr_debug("SPI clock: %u Hz\n", spi_desc->max_speed_hz);
```

**2. Check power supply**:
```c
// Measure AVDD, DVDD, IOVDD
// Verify all within spec (typically 2.7V - 5.25V)
```

**3. Probe SPI signals**:
- Use logic analyzer to verify CS, SCLK, MOSI, MISO
- Check timing meets ADC requirements
- Verify data on MOSI matches expected write data

**4. Try different SPI speed**:
```c
// Reduce SPI clock for debugging
spi_init.max_speed_hz = 100000;  // 100 kHz (slow)
```

### Solutions

**Set correct SPI mode**:
```c
// Most ADCs use SPI Mode 3 (CPOL=1, CPHA=1)
spi_init.mode = NO_OS_SPI_MODE_3;
```

**Reduce SPI clock frequency**:
```c
spi_init.max_speed_hz = 1000000;  // 1 MHz
```

**Verify pin connections**:
- CS (Chip Select)
- SCLK (Serial Clock)
- MOSI (Master Out, Slave In)
- MISO (Master In, Slave Out)

---

## Issue: CRC Errors (if enabled)

### Symptoms
- Status register shows CRC error bit set
- Intermittent read failures

### Possible Causes
- SPI timing issues
- Electrical noise
- CRC calculation mismatch

### Solutions

**Disable CRC for debugging**:
```c
// Disable CRC in ADC control register
ret = ad7124_reg_update(dev, AD7124_ERR_REG,
                        AD7124_CRC_EN_MASK, 0);
```

**Implement proper CRC**:
```c
uint8_t calculate_crc8(uint8_t *data, uint8_t len)
{
    uint8_t crc = 0;
    for (uint8_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x80)
                crc = (crc << 1) ^ 0x07;
            else
                crc <<= 1;
        }
    }
    return crc;
}
```

---

## General Debugging Techniques

### 1. Register Dump

```c
void ad7124_dump_all_registers(struct ad7124_desc *dev)
{
    uint32_t reg_val;

    pr_info("=== AD7124 Complete Register Dump ===\n");

    ad7124_reg_read(dev, AD7124_STATUS_REG, &reg_val);
    pr_info("STATUS:     0x%02X\n", reg_val);

    ad7124_reg_read(dev, AD7124_ADC_CTRL_REG, &reg_val);
    pr_info("ADC_CTRL:   0x%04X\n", reg_val);

    ad7124_reg_read(dev, AD7124_DATA_REG, &reg_val);
    pr_info("DATA:       0x%06X\n", reg_val);

    ad7124_reg_read(dev, AD7124_IO_CTRL1_REG, &reg_val);
    pr_info("IO_CTRL1:   0x%06X\n", reg_val);

    ad7124_reg_read(dev, AD7124_IO_CTRL2_REG, &reg_val);
    pr_info("IO_CTRL2:   0x%04X\n", reg_val);

    ad7124_reg_read(dev, AD7124_ID_REG, &reg_val);
    pr_info("ID:         0x%02X\n", reg_val);

    ad7124_reg_read(dev, AD7124_ERR_REG, &reg_val);
    pr_info("ERROR:      0x%06X\n", reg_val);

    for (int i = 0; i < 16; i++) {
        ad7124_reg_read(dev, AD7124_CHANNEL_REG(i), &reg_val);
        if (reg_val & AD7124_CH_ENABLE)
            pr_info("CH%d:        0x%04X (ENABLED)\n", i, reg_val);
    }

    for (int i = 0; i < 8; i++) {
        ad7124_reg_read(dev, AD7124_CONFIG_REG(i), &reg_val);
        pr_info("CONFIG%d:    0x%04X\n", i, reg_val);

        ad7124_reg_read(dev, AD7124_FILTER_REG(i), &reg_val);
        pr_info("FILTER%d:    0x%06X\n", i, reg_val);

        ad7124_reg_read(dev, AD7124_OFFSET_REG(i), &reg_val);
        pr_info("OFFSET%d:    0x%06X\n", i, reg_val);

        ad7124_reg_read(dev, AD7124_GAIN_REG(i), &reg_val);
        pr_info("GAIN%d:      0x%06X\n", i, reg_val);
    }
}
```

---

### 2. Continuous Monitoring

```c
void monitor_adc_status(struct ad7124_desc *dev)
{
    uint32_t status, data;
    uint8_t channel;

    while (1) {
        ret = ad7124_read_status(dev, &status);
        pr_info("[%lu] Status: 0x%02X, RDY: %u, ERR: %u, CH: %u\n",
                no_os_get_time(),
                status,
                !(status & AD7124_STATUS_RDY),
                !!(status & AD7124_STATUS_ERROR),
                status & 0x0F);

        if (!(status & AD7124_STATUS_RDY)) {
            ret = ad7124_read_data(dev, &data, &channel);
            pr_info("  Data: 0x%06X from channel %u\n", data, channel);
        }

        no_os_mdelay(100);
    }
}
```

---

### 3. Loopback Test (if available)

```c
// Some ADCs support internal loopback for testing
ret = ad7124_enable_loopback(dev);  // Connect AIN to internal reference

// Read and verify
ret = ad7124_read_data(dev, &data, &channel);
pr_info("Loopback data: 0x%06X (expected mid-scale or full-scale)\n", data);
```

---

## Quick Diagnostic Checklist

**Power-On Checks**:
- [ ] Power supplies within spec (AVDD, DVDD, IOVDD)
- [ ] Device ID reads correctly
- [ ] SPI communication functional
- [ ] Reset successful

**Configuration Checks**:
- [ ] Reference voltage configured
- [ ] Channels enabled
- [ ] Conversion mode set (continuous/single)
- [ ] Filter and ODR appropriate

**Runtime Checks**:
- [ ] Status register shows no errors
- [ ] RDY signal toggles
- [ ] Data register updates
- [ ] Voltage calculations match expected

**Calibration Checks**:
- [ ] Calibration performed after init
- [ ] Calibration coefficients stored
- [ ] Readings match known inputs
