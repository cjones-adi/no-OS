# DAC API Usage Examples

Detailed API usage patterns and code examples for DAC drivers.

## Output Configuration

### Voltage Output Ranges

**Unipolar Ranges** (0V to positive):
```c
enum ad5758_output_range {
    RANGE_0V_5V = 0,     // 0V to 5V
    RANGE_0V_10V = 1,    // 0V to 10V
    RANGE_0V_12V = 3,    // 0V to 12V
};
```

**Bipolar Ranges** (negative to positive):
```c
enum ad5758_output_range {
    RANGE_M5V_5V = 2,     // -5V to +5V
    RANGE_M10V_10V = 3,   // -10V to +10V
};
```

**Advanced Spans** (AD5766 asymmetric ranges):
```c
enum ad5766_span {
    AD5766_M_20V_TO_0V,      // -20V to 0V
    AD5766_M_16V_TO_0V,      // -16V to 0V
    AD5766_M_12V_TO_P_14V,   // -12V to +14V
    AD5766_M_16V_TO_P_10V,   // -16V to +10V
    AD5766_M_5V_TO_P_6V,     // -5V to +6V
    AD5766_M_10V_TO_P_10V,   // -10V to +10V (most common)
};
```

**Setting Output Range**:
```c
// AD5758 example
ret = ad5758_set_out_range(dev, RANGE_0V_10V);

// AD5766 example (per-channel)
ret = ad5766_set_span(dev, AD5766_DAC_0, AD5766_M_10V_TO_P_10V);
```

---

### Current Output Modes

**Standard Current Ranges**:
```c
enum ad5758_output_range {
    RANGE_0mA_20mA = 8,    // 0mA to 20mA (loop powered)
    RANGE_0mA_24mA = 9,    // 0mA to 24mA (loop powered)
    RANGE_4mA_20mA = 10,   // 4mA to 20mA (live-zero)
    RANGE_M20mA_20mA = 11, // -20mA to +20mA (bipolar)
};
```

**4-20mA Loop Example** (industrial standard):
```c
// Configure for 4-20mA output
ret = ad5758_set_out_range(dev, RANGE_4mA_20mA);

// 4mA = 0% scale, 20mA = 100% scale
// Example: Output 12mA (50% of range)
uint16_t code = 0x8000;  // Midscale for 16-bit DAC
ret = ad5758_dac_input_write(dev, code);
```

---

### Reference Voltage Selection

**Internal Reference**:
```c
// AD5758: Internal 2.5V reference
ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);
```

**External Reference**:
```c
// AD5770R: External reference selection
enum ad5770r_reference_voltage ref = AD5770R_EXT_REF_2_5_V;
ret = ad5770r_set_reference(dev, true, ref);
```

**Reference Voltage Impact**:
```
Output Voltage = (DAC_Code / Full_Scale) × Vref × Gain

Example: 16-bit DAC, Vref = 2.5V, 0V to 10V range
  Gain = 4 (internal scaling)
  Code 0x0000 → 0V
  Code 0xFFFF → 10V
  Code 0x8000 → 5V
```

---

## Update Modes and Synchronization

### Immediate (Asynchronous) Update

**Direct Write** (output changes immediately):
```c
// AD5449: Simple immediate update
void ad5449_load_update_channel(struct ad5449_dev *dev,
                                uint8_t channel,
                                uint16_t dac_value);

// AD5758: Single-channel immediate
int32_t ad5758_dac_input_write(struct ad5758_dev *dev,
                               uint16_t code);
```

**Use Cases**:
- Single-channel applications
- Fast-changing signals
- Non-critical timing applications

---

### Synchronous (LDAC) Update

**Two-Step Update Process**:
```c
// Step 1: Write to input registers (no output change yet)
ret = ad5686_write_register(dev, AD5686_CH_0, code_ch0);
ret = ad5686_write_register(dev, AD5686_CH_1, code_ch1);
ret = ad5686_write_register(dev, AD5686_CH_2, code_ch2);

// Step 2: Load all DAC registers simultaneously
ret = ad5686_update_register(dev, AD5686_CH_ALL);
```

**Hardware LDAC Pin Control**:
```c
// Toggle LDAC pin low to trigger update
ret = no_os_gpio_set_value(dev->gpio_ldac, NO_OS_GPIO_LOW);
no_os_udelay(1);  // Meet tLDAC timing
ret = no_os_gpio_set_value(dev->gpio_ldac, NO_OS_GPIO_HIGH);
```

**Software LDAC Trigger** (AD5766):
```c
// Software-triggered simultaneous update of selected channels
uint16_t ldac_mask = AD5766_LDAC(0) | AD5766_LDAC(1) | AD5766_LDAC(2);
ret = ad5766_set_sw_ldac(dev, ldac_mask);
```

**Use Cases**:
- Multi-channel waveform generation
- Synchronized signal output
- Glitch-free updates
- Phase-aligned outputs

---

### Slew Rate Control (Advanced)

**Configurable Slew** (AD5460, AD5758, AD5754R):
```c
enum ad5460_slew_lin_step {
    AD5460_STEP_0_8_PERCENT,    // 0.8% step size
    AD5460_STEP_1_5_PERCENT,    // 1.5% step size
    AD5460_STEP_6_1_PERCENT,    // 6.1% step size
    AD5460_STEP_22_2_PERCENT,   // 22.2% step size
};

enum ad5460_lin_rate {
    AD5460_LIN_RATE_4KHZ8,      // 4.8 kHz update rate
    AD5460_LIN_RATE_76KHZ8,     // 76.8 kHz
    AD5460_LIN_RATE_153KHZ6,    // 153.6 kHz
    AD5460_LIN_RATE_230KHZ4,    // 230.4 kHz (fastest)
};

// Enable slew rate control
ret = ad5460_dac_slew_enable(dev, channel,
                             AD5460_STEP_1_5_PERCENT,
                             AD5460_LIN_RATE_76KHZ8);
```

**Benefits**:
- Reduces output glitches
- Limits inrush current
- Smooth voltage/current transitions
- EMI reduction

---

## Offset and Gain Calibration

### Factory Calibration

**Pre-Programmed** (most devices):
- Stored in device memory
- Automatically applied
- No user action required

---

### User Calibration

**Digital Offset/Gain Correction** (AD3552R):
```c
// Set offset correction (signed, mV)
int ad3552r_set_offset(struct ad3552r_desc *dev,
                       uint32_t ch,
                       int32_t offset_int,
                       int32_t offset_frac);

// Set gain/scale correction
int ad3552r_set_scale(struct ad3552r_desc *dev,
                      uint32_t ch,
                      int32_t scale_int,
                      int32_t scale_frac);
```

**Register-Based Calibration** (AD5791):
```c
// Offset binary register (24-bit)
#define AD5791_REG_OFFSET 0x03

// Directly write offset value
ret = ad5791_set_register_value(dev,
                                AD5791_REG_OFFSET,
                                offset_value);
```

---

### Calibration Workflow

**Two-Point Calibration Example**:
```c
// 1. Measure zero-scale output with DMM
ret = ad5758_dac_input_write(dev, 0x0000);
no_os_mdelay(100);  // Allow settling
// DMM reads: 0.005V (expected 0V) → offset = +5mV

// 2. Measure full-scale output
ret = ad5758_dac_input_write(dev, 0xFFFF);
no_os_mdelay(100);
// DMM reads: 9.98V (expected 10V) → gain error = -0.2%

// 3. Apply corrections
ret = ad3552r_set_offset(dev, 0, -5, 0);      // -5mV offset
ret = ad3552r_set_scale(dev, 0, 1, 2000);     // +0.2% gain (+1.002x)

// 4. Verify corrected output
ret = ad5758_dac_input_write(dev, 0x8000);  // Midscale
// DMM should now read 5.000V ± error spec
```

---

## Code to Voltage/Current Conversion

### Voltage Conversion

**Unipolar (0V to Vmax)**:
```c
// Vout = (Code / Full_Scale) × Vrange
float code_to_voltage_unipolar(uint16_t code,
                                uint8_t resolution,
                                float vrange)
{
    uint32_t full_scale = (1 << resolution) - 1;
    return ((float)code / full_scale) * vrange;
}

// Example: 16-bit, 0-10V range, code = 0x8000
// Vout = (32768 / 65535) × 10V = 5.000V
```

**Bipolar (-Vmax to +Vmax)**:
```c
// Vout = ((Code / Full_Scale) - 0.5) × Vrange
float code_to_voltage_bipolar(uint16_t code,
                               uint8_t resolution,
                               float vrange)
{
    uint32_t full_scale = (1 << resolution);
    return (((float)code / full_scale) - 0.5) * vrange;
}

// Example: 16-bit, ±10V range, code = 0x8000
// Vout = ((32768 / 65536) - 0.5) × 20V = 0.000V
// Code 0x0000 → -10V, 0xFFFF → +10V
```

---

### Current Conversion

**4-20mA Loop**:
```c
// Iout = 4mA + (Code / Full_Scale) × 16mA
float code_to_current_4_20(uint16_t code, uint8_t resolution)
{
    uint32_t full_scale = (1 << resolution) - 1;
    return 4.0 + ((float)code / full_scale) * 16.0;  // mA
}

// Example: 16-bit, code = 0x8000
// Iout = 4mA + (32768/65535) × 16mA = 12.0mA (50%)
```

**0-20mA**:
```c
// Iout = (Code / Full_Scale) × 20mA
float code_to_current_0_20(uint16_t code, uint8_t resolution)
{
    uint32_t full_scale = (1 << resolution) - 1;
    return ((float)code / full_scale) * 20.0;  // mA
}
```

---

## Power Management

### Per-Channel Power Control

**Power Down Channels** (AD5766, AD5686, AD5754R):
```c
// AD5766: Bitmask for power-down control
uint16_t pwr_down = AD5766_PWDN(0) | AD5766_PWDN(1);
ret = ad5766_set_pwr_dac(dev, pwr_down);

// AD5754R: Enumerated power states
enum ad5754r_pwr_dac_ch_pwrup state = AD5754R_POWERUP_NORMAL;
ret = ad5754r_set_ch_pwrup(dev, channel, state);
```

**Power-Down Modes**:
- **Normal**: Full power, DAC operational
- **1kΩ to GND**: Output pulled to ground through 1kΩ
- **100kΩ to GND**: High-impedance power-down
- **Three-State**: Output disconnected (high-Z)

---

### Clear Code / Power-On Reset

**Clear Code Configuration** (AD5766):
```c
enum ad5766_clr {
    AD5766_ZERO,   // Output goes to zero scale
    AD5766_MID,    // Output goes to midscale
    AD5766_FULL,   // Output goes to full scale
};

// Configure clear behavior
ret = ad5766_set_clr_span(dev, AD5766_MID, AD5766_M_10V_TO_P_10V);

// When CLR pin asserted:
// - All outputs go to 0V (midscale of ±10V range)
```

**Use Cases**:
- Safe startup state
- Emergency shutdown
- Controlled reset behavior

---

## Daisy-Chain Configuration

### Multi-Device Cascading

**Enable Daisy-Chain** (AD5766, AD5686, AD5449):
```c
// AD5766: Enable in init parameters
struct ad5766_init_param init = {
    .daisy_chain_en = AD5766_ENABLE,
    // ...
};

// AD5686: Enable via control register
void ad5686_daisy_chain_en(struct ad5686_dev *dev, uint8_t value);
```

**Daisy-Chain Operation**:
```
MCU → DAC1(SDI) → DAC1(SDO) → DAC2(SDI) → DAC2(SDO) → ...
       ↓ CS (shared)          ↓ CS (shared)
```

**SPI Transaction** (3 devices):
```c
// Single SPI transaction updates all devices
uint8_t tx_buf[9] = {
    // DAC 3 data (24-bit)
    addr3, data3_msb, data3_lsb,
    // DAC 2 data
    addr2, data2_msb, data2_lsb,
    // DAC 1 data
    addr1, data1_msb, data1_lsb,
};

ret = no_os_spi_write_and_read(spi_desc, tx_buf, 9);
// All DACs update simultaneously when CS goes high
```

---

## Advanced Features

### Readback Capability

**Register Readback** (AD5766, AD5791, AD5754R):
```c
// Read DAC register to verify write
uint32_t readback_value;
ret = ad5766_spi_readback_reg(dev, AD5766_DAC_0, &readback_value);

if (readback_value != written_value) {
    pr_err("DAC register mismatch!\n");
}
```

**Use Cases**:
- Verify configuration
- Detect SPI errors
- Safety-critical applications

---

### Dither Support (AD5766)

**Dithering for Resolution Enhancement**:
```c
// Enable dither on selected channels
uint32_t dither_en = AD5766_DITHER(0) | AD5766_DITHER(1);
ret = ad5766_set_dither_signal(dev, dither_en);

// Configure dither scaling (amplitude)
ret = ad5766_set_dither_scale(dev, dither_scale);

// Optionally invert dither
ret = ad5766_set_inv_dither(dev, invert_mask);
```

**Benefits**:
- Effective resolution increase
- Reduced quantization noise
- Smoother analog output

---

### Diagnostic and Monitoring

**Temperature Monitoring** (AD5758, AD5460):
```c
// AD5758: Select ADC input for temperature
ret = ad5758_select_adc_ip(dev, ADC_IP_MAIN_DIE_TEMP);

// Read temperature (device-specific scaling)
uint16_t temp_code;
ret = ad5758_adc_code_read(dev, &temp_code);

// Convert to temperature (°C)
float temp_c = (temp_code * 0.125) - 273.15;
```

**Status Monitoring** (AD5460):
```c
union ad5460_live_status status;
ret = ad5460_get_live(dev, &status);

if (status.status_bits.ANALOG_IO_OC_STATUS_A) {
    pr_err("Overcurrent detected on channel A!\n");
}

if (status.status_bits.ANALOG_IO_SC_STATUS_A) {
    pr_err("Short circuit detected on channel A!\n");
}
```

---

### CRC/Error Detection (AD5758, AD3552R)

**Enable CRC** (AD5758):
```c
// Enable 8-bit CRC on SPI transactions
ret = ad5758_set_crc(dev, AD5758_CRC_ENABLE);

// Driver automatically computes and verifies CRC
// Returns error if CRC mismatch detected
```

**Status Checking** (AD3552R):
```c
enum ad3552r_status status;
ret = ad3552r_read_status(dev, &status);

if (status & AD3552R_CLOCK_COUNTING_ERROR) {
    pr_err("SPI clock error detected\n");
}

if (status & AD3552R_INVALID_OR_NO_CRC) {
    pr_err("CRC validation failed\n");
}
```

---

## IIO Integration

### IIO Wrapper Structure

```c
struct iio_ad3552r_desc {
    struct iio_channel channels[AD3552R_MAX_NUM_CH];
    struct iio_device iio_desc;
    struct ad3552r_desc *dac;  // Core driver instance
    uint32_t mask;             // Active channel mask
};
```

### IIO Initialization

```c
struct ad3552r_init_param dac_init = {
    .spi_ip = &spi_init,
    // ...
};

struct iio_ad3552r_desc *iio_dac;
ret = iio_ad3552r_init(&iio_dac, &dac_init);

// Get IIO device descriptor for registration
struct iio_device *iio_dev;
iio_ad3552r_get_descriptor(iio_dac, &iio_dev);
```

---

### IIO Channel Attributes

**Standard DAC Attributes**:
```c
static struct iio_attribute ad3552r_ch_attributes[] = {
    {
        .name = "raw",           // Raw DAC code
        .show = iio_ad3552r_attr_get,
        .store = iio_ad3552r_attr_set,
        .priv = AD3552R_IIO_ATTR_RAW,
    },
    {
        .name = "scale",         // Output scaling factor
        .show = iio_ad3552r_attr_get,
        .priv = AD3552R_IIO_ATTR_SCALE,
    },
    {
        .name = "offset",        // Calibration offset
        .show = iio_ad3552r_attr_get,
        .store = iio_ad3552r_attr_set,
        .priv = AD3552R_IIO_ATTR_OFFSET,
    },
    {
        .name = "powerdown",     // Power-down control
        .show = iio_ad3552r_attr_get,
        .store = iio_ad3552r_attr_set,
        .priv = AD3552R_IIO_ATTR_EN,
    },
    END_ATTRIBUTES_ARRAY
};
```

**Attribute Access via IIO**:
```bash
# Read raw DAC code
iio_attr -c -C out_voltage0 raw

# Write DAC code (0 to 65535 for 16-bit)
iio_attr -c -C out_voltage0 raw 32768

# Read output scale
iio_attr -c -C out_voltage0 scale
```
