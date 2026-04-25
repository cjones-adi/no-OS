# ADC API Usage Examples

Detailed examples for common ADC usage patterns.

---

## Pattern 1: Simple Single-Channel Reading (SAR ADC)

```c
#include "ad4692.h"
#include "no_os_spi.h"
#include "no_os_print_log.h"

int main(void)
{
    struct ad4692_desc *dev;
    struct ad4692_init_param init_param = {
        .spi_ip = &spi_init,
        .device_id = ID_AD4692,
        .ref_voltage = 5000,  // 5V reference
    };
    uint32_t data;
    int ret;

    // Initialize ADC
    ret = ad4692_init(&dev, &init_param);
    if (ret) {
        pr_err("Init failed: %d\n", ret);
        return ret;
    }

    // Configure channel 0
    ret = ad4692_set_channel(dev, 0);

    // Read channel 0 continuously
    while (1) {
        ret = ad4692_read_channel(dev, 0, &data);
        if (ret) {
            pr_err("Read failed: %d\n", ret);
            continue;
        }

        // Convert to voltage
        float voltage = (float)data * 5000.0 / 0xFFFF;
        pr_info("Channel 0: %u (%.2f mV)\n", data, voltage);

        no_os_mdelay(100);
    }

    ad4692_remove(dev);
    return 0;
}
```

---

## Pattern 2: Multi-Channel Setup (Sigma-Delta)

```c
#include "ad7124.h"
#include "no_os_spi.h"
#include "no_os_print_log.h"

int configure_multi_channel_adc(void)
{
    struct ad7124_desc *dev;
    struct ad7124_init_param init_param = {
        .spi_ip = &spi_init,
        .vref_mv = 2500,
    };
    int ret;

    // Initialize ADC
    ret = ad7124_init(&dev, &init_param);
    if (ret)
        return ret;

    // Setup 0: Single-ended, gain=1, SINC4 filter
    struct ad7124_channel_setup setup0 = {
        .bi_unipolar = AD7124_UNIPOLAR,
        .ref_source = AD7124_INT_REF,
        .pga = AD7124_PGA_GAIN_1,
        .ref_buff = true,
        .input_buff = true,
    };

    struct ad7124_filtcon filter0 = {
        .filter = AD7124_SINC4_FILTER,
        .odr = AD7124_ODR_100_SPS,
        .enhfilten = false,
    };

    // Channel 0: AIN0 vs AVSS (ground)
    struct ad7124_channel_map ch0_map = {
        .channel_enable = true,
        .setup_sel = 0,
        .ainp = AD7124_AIN0,
        .ainm = AD7124_AVSS,
    };

    // Channel 1: AIN1 vs AVSS
    struct ad7124_channel_map ch1_map = {
        .channel_enable = true,
        .setup_sel = 0,
        .ainp = AD7124_AIN1,
        .ainm = AD7124_AVSS,
    };

    // Configure setup and channels
    ret = ad7124_setup_channel(dev, 0, setup0, ch0_map, filter0);
    ret = ad7124_setup_channel(dev, 1, setup0, ch1_map, filter0);

    // Start continuous conversion
    ret = ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);

    // Read channels in loop
    while (1) {
        uint32_t data;
        uint8_t channel;

        ret = ad7124_wait_for_ready(dev, 1000);
        if (ret)
            continue;

        ret = ad7124_read_data(dev, &data, &channel);

        float voltage;
        ad7124_convert_sample_to_voltage(dev, channel, data, &voltage);

        pr_info("Channel %u: %u (%.3f mV)\n", channel, data, voltage);
    }

    ad7124_remove(dev);
    return 0;
}
```

---

## Pattern 3: Calibrated Precision Measurement

```c
int precision_measurement_with_calibration(void)
{
    struct ad7124_desc *dev;
    struct ad7124_init_param init_param = {
        .spi_ip = &spi_init,
        .vref_mv = 2500,
    };
    int ret;

    ret = ad7124_init(&dev, &init_param);
    if (ret)
        return ret;

    // Configure high-precision setup
    struct ad7124_channel_setup setup0 = {
        .bi_unipolar = AD7124_BIPOLAR,
        .ref_source = AD7124_REFIN1,  // External precision ref
        .pga = AD7124_PGA_GAIN_8,     // 8x gain for small signals
        .ref_buff = true,
        .input_buff = true,
    };

    struct ad7124_filtcon filter0 = {
        .filter = AD7124_SINC5_FILTER,  // Best noise performance
        .odr = AD7124_ODR_19_SPS,       // Slow for precision
        .enhfilten = true,               // 50/60Hz rejection
    };

    struct ad7124_channel_map ch0_map = {
        .channel_enable = true,
        .setup_sel = 0,
        .ainp = AD7124_AIN0,
        .ainm = AD7124_AIN1,  // Differential
    };

    ret = ad7124_setup_channel(dev, 0, setup0, ch0_map, filter0);

    // Perform internal calibration
    pr_info("Performing self-calibration...\n");
    ret = ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, 0);
    ret = ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, 0);

    // Take multiple averaged readings
    #define NUM_SAMPLES 10
    uint32_t sum = 0;

    ret = ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);

    for (int i = 0; i < NUM_SAMPLES; i++) {
        uint32_t data;
        uint8_t channel;

        ret = ad7124_wait_for_ready(dev, 2000);
        ret = ad7124_read_data(dev, &data, &channel);
        sum += data;
    }

    uint32_t average = sum / NUM_SAMPLES;
    float voltage;
    ad7124_convert_sample_to_voltage(dev, 0, average, &voltage);

    pr_info("Averaged result: %.4f mV\n", voltage);

    ad7124_remove(dev);
    return 0;
}
```

---

## Channel Configuration

### Single-Ended vs Differential

**Single-Ended** (measure relative to ground):
```c
struct ad7124_channel_map ch_map = {
    .channel_enable = true,
    .setup_sel = 0,
    .ainp = AD7124_AIN0,      // Signal input
    .ainm = AD7124_AVSS,      // Ground reference
};
```

**Differential** (measure difference between two inputs):
```c
struct ad7124_channel_map ch_map = {
    .channel_enable = true,
    .setup_sel = 0,
    .ainp = AD7124_AIN0,      // Positive input
    .ainm = AD7124_AIN1,      // Negative input
};
```

---

## Reference Voltage Selection

**External Reference**:
```c
.ref_source = AD7124_REFIN1,  // External ref on REFIN1+/-
.ref_source = AD7124_REFIN2,  // External ref on REFIN2+/-
```

**Internal Reference**:
```c
.ref_source = AD7124_INT_REF,  // Internal 2.5V reference
```

**Supply as Reference**:
```c
.ref_source = AD7124_AVDD_AVSS,  // Power supply (AVDD-AVSS)
```

**Reference Voltage in Descriptor**:
```c
// Store reference voltage for data conversion
init_param.ref_voltage = 2500;  // 2.5V in mV
init_param.ref_voltage = 5000;  // 5.0V in mV
```

---

## Gain Configuration (PGA)

**Programmable Gain Amplifier** (typical values):
```c
enum ad7124_pga {
    AD7124_PGA_GAIN_1 = 0,     // Gain = 1
    AD7124_PGA_GAIN_2 = 1,     // Gain = 2
    AD7124_PGA_GAIN_4 = 2,     // Gain = 4
    AD7124_PGA_GAIN_8 = 3,     // Gain = 8
    AD7124_PGA_GAIN_16 = 4,    // Gain = 16
    AD7124_PGA_GAIN_32 = 5,    // Gain = 32
    AD7124_PGA_GAIN_64 = 6,    // Gain = 64
    AD7124_PGA_GAIN_128 = 7,   // Gain = 128
};
```

**Effective Input Range**:
```
Effective Range = Vref / Gain

Example: Vref = 2.5V, Gain = 8
  → Input Range = ±312.5 mV (bipolar)
  → Input Range = 0 to 312.5 mV (unipolar)
```

**Usage**:
```c
// For small signals, use higher gain
setup.pga = AD7124_PGA_GAIN_128;  // ±19.5 mV range (2.5V ref)

// For larger signals, use lower gain
setup.pga = AD7124_PGA_GAIN_1;    // ±2.5V range (2.5V ref)
```

---

## Bipolar vs Unipolar Mode

**Bipolar** (signed, negative and positive):
```c
setup.bi_unipolar = AD7124_BIPOLAR;
// Input range: -Vref/Gain to +Vref/Gain
// Code range: 0x800000 (negative full-scale) to 0x7FFFFF (positive full-scale)
```

**Unipolar** (unsigned, positive only):
```c
setup.bi_unipolar = AD7124_UNIPOLAR;
// Input range: 0 to Vref/Gain
// Code range: 0x000000 to 0xFFFFFF
```

---

## Conversion Modes

### Continuous Conversion Mode

**Description**: ADC continuously converts enabled channels in sequence.

**Use Case**: Streaming data acquisition.

**Configuration**:
```c
ret = ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);

// Data ready signal (interrupt or polling)
while (1) {
    ret = ad7124_wait_for_ready(dev, TIMEOUT_MS);
    if (ret)
        break;

    ret = ad7124_read_data(dev, &data);
    // Process data
}
```

---

### Single Conversion Mode

**Description**: Performs one conversion per enabled channel, then returns to standby.

**Use Case**: Low-power periodic sampling.

**Configuration**:
```c
ret = ad7124_set_adc_mode(dev, AD7124_SINGLE_MODE);

// Trigger conversion
ret = ad7124_wait_for_ready(dev, TIMEOUT_MS);
ret = ad7124_read_data(dev, &data);
```

---

### Standby / Power-Down Modes

**Standby** (low power, fast wake-up):
```c
ret = ad7124_set_adc_mode(dev, AD7124_STANDBY_MODE);
// Can quickly return to active mode
```

**Power-Down** (minimal power, slow wake-up):
```c
ret = ad7124_set_adc_mode(dev, AD7124_POWER_DOWN_MODE);
// Requires full re-initialization
```

---

## Data Conversion

### Raw to Voltage Conversion

**Bipolar Mode**:
```c
int32_t raw_code = 0x400000;  // 24-bit signed code
uint32_t vref_mv = 2500;       // 2.5V reference
uint8_t gain = 1;              // PGA gain

// Convert to voltage (mV)
float voltage_mv = ((float)raw_code / 0x800000) * (vref_mv / gain);
```

**Unipolar Mode**:
```c
uint32_t raw_code = 0x800000;  // 24-bit unsigned code
uint32_t vref_mv = 2500;
uint8_t gain = 1;

// Convert to voltage (mV)
float voltage_mv = ((float)raw_code / 0xFFFFFF) * (vref_mv / gain);
```

**Helper Functions** (typical pattern):
```c
int ad7124_convert_sample_to_voltage(struct ad7124_desc *dev,
                                      uint8_t channel,
                                      uint32_t sample,
                                      float *voltage)
{
    struct ad7124_channel_setup *setup = &dev->setups[channel];
    float vref = dev->vref_mv;
    uint8_t gain = 1 << setup->pga;  // Convert enum to actual gain

    if (setup->bi_unipolar == AD7124_BIPOLAR) {
        int32_t signed_code = (int32_t)sample - 0x800000;
        *voltage = ((float)signed_code / 0x800000) * (vref / gain);
    } else {
        *voltage = ((float)sample / 0xFFFFFF) * (vref / gain);
    }

    return 0;
}
```

---

## Performance Optimization

**Channel Setup Reuse (Sigma-Delta)**:
```c
// Efficient: Share one setup across multiple channels
// Setup 0: Bipolar, gain=1, external ref
setup0 = {...};

// All channels use setup 0
ch0_map.setup_sel = 0;
ch1_map.setup_sel = 0;
ch2_map.setup_sel = 0;
```

**Batch Reads for Multi-Channel**:
```c
for (ch = 0; ch < num_channels; ch++) {
    ad7124_read_data(dev, &buffer[ch], &channel);
}

// Use continuous mode instead of repeated single conversions
ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);
```

---

## Power Management

### Power Modes

**Low Power Mode**:
```c
ret = ad7768_set_power_mode(dev, AD7768_LOW_POWER);
// Reduced clock frequency, lower power consumption
// Suitable for low-speed applications
```

**Median Power Mode**:
```c
ret = ad7768_set_power_mode(dev, AD7768_MEDIAN_POWER);
// Balanced performance and power
```

**High Power Mode**:
```c
ret = ad7768_set_power_mode(dev, AD7768_FAST);
// Maximum performance
// Highest power consumption
```

---

### Clock Configuration

**Internal Oscillator**:
```c
ret = ad7768_set_clk_source(dev, AD7768_INT_CLK);
// Use internal oscillator (default)
```

**External Clock**:
```c
ret = ad7768_set_clk_source(dev, AD7768_EXT_CLK);
// Use external clock input
// Allows synchronization with other devices
```
