# DAC Troubleshooting Guide

Common issues and debugging strategies for DAC drivers.

## Issue: No Output or Zero Voltage

### Symptoms
- DAC appears to initialize successfully
- Writing codes produces no output voltage
- Output stuck at 0V or floating

### Possible Causes
1. Channel powered down
2. Wrong output range configured
3. Reference voltage not enabled
4. SPI communication error
5. Output buffer disabled

### Debug Steps

```c
// 1. Verify device ID (SPI communication working)
uint32_t id;
ret = ad5758_reg_read(dev, AD5758_DIGITAL_DIAG_RESULTS, &id);
pr_debug("Device ID: 0x%04X (expected 0x%04X)\n", id, EXPECTED_ID);
if (id != EXPECTED_ID) {
    pr_err("SPI communication error or wrong device\n");
}

// 2. Check power-down status
uint32_t pwr_reg;
ret = ad5758_reg_read(dev, AD5758_DAC_CONFIG, &pwr_reg);
pr_debug("Power config: 0x%04X\n", pwr_reg);
if (pwr_reg & POWER_DOWN_MASK) {
    pr_err("DAC channel is powered down\n");
}

// 3. Verify output range configuration
uint32_t range_reg;
ret = ad5758_reg_read(dev, AD5758_OUTPUT_RANGE, &range_reg);
pr_debug("Output range: 0x%04X (expected 0x%04X)\n", 
         range_reg, expected_range);

// 4. Check DAC register value
uint32_t dac_value;
ret = ad5758_reg_read(dev, AD5758_DAC_INPUT, &dac_value);
pr_debug("DAC input register: 0x%04X\n", dac_value);
if (dac_value == 0) {
    pr_debug("DAC code is 0 - this is expected to produce minimum output\n");
}

// 5. Verify reference voltage
uint32_t ref_reg;
ret = ad5758_reg_read(dev, AD5758_DIGITAL_DIAG_CONFIG, &ref_reg);
pr_debug("Reference config: 0x%04X\n", ref_reg);
if (!(ref_reg & REF_EN_MASK)) {
    pr_err("Reference voltage not enabled\n");
}
```

### Solutions

```c
// Enable reference voltage
ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);

// Verify and set correct output range
ret = ad5758_set_out_range(dev, RANGE_0V_10V);

// Power up channel
ret = ad5766_set_pwr_dac(dev, 0x0000);  // All channels on

// Write known test code
ret = ad5758_dac_input_write(dev, 0x8000);  // Midscale
pr_info("DAC set to midscale (0x8000), measure output voltage\n");
```

---

## Issue: Wrong Output Voltage

### Symptoms
- Output voltage present but incorrect value
- Voltage offset from expected
- Non-linear relationship between code and voltage

### Possible Causes
1. Incorrect range configuration
2. Wrong reference voltage
3. Calibration needed
4. Load impedance too low
5. Code-to-voltage conversion error

### Debug Steps

```c
// Verify range matches application
pr_info("=== Output Range Verification ===\n");
pr_info("Expected range: 0-10V\n");
pr_info("Configured range: %s\n",
        (dev->output_range == RANGE_0V_10V) ? "0-10V" : "MISMATCH");

// Check reference voltage
pr_info("=== Reference Configuration ===\n");
pr_info("Reference enabled: %s\n", dev->ref_en ? "YES" : "NO");
pr_info("Reference type: %s\n", 
        dev->ref_en ? "Internal 2.5V" : "External or disabled");

// Test known codes and measure
pr_info("=== Code vs Voltage Test ===\n");
const struct {
    uint16_t code;
    float expected_v;  // For 0-10V range, 16-bit
} test_points[] = {
    {0x0000, 0.0},
    {0x4000, 2.5},
    {0x8000, 5.0},
    {0xC000, 7.5},
    {0xFFFF, 10.0},
};

for (int i = 0; i < 5; i++) {
    ret = ad5758_dac_input_write(dev, test_points[i].code);
    no_os_mdelay(100);  // Settling time
    pr_info("Code 0x%04X: Expected %.3fV - MEASURE NOW\n",
            test_points[i].code, test_points[i].expected_v);
    no_os_mdelay(5000);  // Time to measure with DMM
}
```

### Solutions

```c
// 1. Verify and correct range
ret = ad5758_set_out_range(dev, RANGE_0V_10V);

// 2. Enable correct reference
ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);

// 3. Check load impedance
// - Most DACs require high-impedance load (>10kΩ)
// - Low impedance loads can cause voltage drop
// - Use buffer amplifier if needed

// 4. Apply calibration if systematic error
float measured_zero = 0.005;  // DMM reading at code 0x0000
float measured_full = 9.98;   // DMM reading at code 0xFFFF
float offset_mv = measured_zero * 1000.0;
float gain_error = ((measured_full - measured_zero) / 10.0) - 1.0;

pr_info("Calibration needed:\n");
pr_info("  Offset: %.3f mV\n", offset_mv);
pr_info("  Gain error: %.4f %%\n", gain_error * 100.0);

// Apply calibration (if device supports)
ret = ad3552r_set_offset(dev, 0, -(int32_t)offset_mv, 0);
ret = ad3552r_set_scale(dev, 0, 1, (int32_t)(gain_error * 1000000));
```

---

## Issue: Glitches During Multi-Channel Updates

### Symptoms
- Visible glitches when updating multiple channels
- Outputs don't change simultaneously
- Transient incorrect values

### Cause
Using immediate updates instead of synchronous LDAC

### Debug Steps

```c
// Identify update mode being used
pr_info("=== Update Mode Check ===\n");
pr_info("Current implementation uses:\n");

// BAD: Immediate updates (causes glitches)
#if 0
ad5686_write_update_register(dev, AD5686_CH_0, 0x1000);
ad5686_write_update_register(dev, AD5686_CH_1, 0x2000);
ad5686_write_update_register(dev, AD5686_CH_2, 0x3000);
pr_info("  Immediate mode - CAUSES GLITCHES\n");
#endif

// GOOD: Synchronous updates
#if 1
ad5686_write_register(dev, AD5686_CH_0, 0x1000);
ad5686_write_register(dev, AD5686_CH_1, 0x2000);
ad5686_write_register(dev, AD5686_CH_2, 0x3000);
ad5686_update_register(dev, AD5686_CH_ALL);
pr_info("  Synchronous mode - GLITCH-FREE\n");
#endif
```

### Solution

```c
// Use synchronous update pattern
void update_multiple_channels_glitch_free(struct ad5686_dev *dev)
{
    // Step 1: Write all channels (no output change)
    ad5686_write_register(dev, AD5686_CH_0, code0);
    ad5686_write_register(dev, AD5686_CH_1, code1);
    ad5686_write_register(dev, AD5686_CH_2, code2);
    ad5686_write_register(dev, AD5686_CH_3, code3);

    // Step 2: Trigger simultaneous update
    ad5686_update_register(dev, AD5686_CH_ALL);
    // All outputs change at exactly the same time
}

// Or use hardware LDAC pin
void update_with_hardware_ldac(struct ad5766_dev *dev)
{
    // Write all channels
    for (int ch = 0; ch < num_channels; ch++) {
        ad5766_write_register(dev, ch, codes[ch]);
    }

    // Toggle LDAC pin to trigger update
    no_os_gpio_set_value(dev->gpio_ldac, NO_OS_GPIO_LOW);
    no_os_udelay(1);  // Meet tLDAC timing
    no_os_gpio_set_value(dev->gpio_ldac, NO_OS_GPIO_HIGH);
}
```

---

## Issue: Slow Output Settling

### Symptoms
- Output takes long time to reach final value
- Slew-limited transitions
- Slow response to code changes

### Possible Causes
1. Slew rate control enabled (intentional)
2. Capacitive load too high
3. Output buffer current limited
4. Thermal limiting

### Debug Steps

```c
// 1. Check slew rate configuration
pr_info("=== Slew Rate Status ===\n");
uint32_t slew_reg;
ret = ad5758_reg_read(dev, AD5758_SLEW_RATE_CONFIG, &slew_reg);
if (slew_reg & SLEW_ENABLE_MASK) {
    pr_info("Slew rate control: ENABLED\n");
    pr_info("  Step size: %u\n", (slew_reg >> STEP_SHIFT) & STEP_MASK);
    pr_info("  Rate: %u kHz\n", (slew_reg >> RATE_SHIFT) & RATE_MASK);
} else {
    pr_info("Slew rate control: DISABLED\n");
}

// 2. Measure settling time
pr_info("\n=== Settling Time Test ===\n");
ret = ad5758_dac_input_write(dev, 0x0000);  // Min
no_os_mdelay(100);

uint32_t start_time = no_os_get_time_us();
ret = ad5758_dac_input_write(dev, 0xFFFF);  // Max

// Measure output with scope
pr_info("Triggering full-scale step. Measure settling time.\n");
pr_info("Expected: <100us for fast DAC without slew rate\n");
no_os_mdelay(1000);

// 3. Check load capacitance
pr_info("\n=== Load Check ===\n");
pr_info("Verify output load:\n");
pr_info("  - Impedance: >10kΩ recommended\n");
pr_info("  - Capacitance: <100pF for fast settling\n");
pr_info("  - Cable length: <1m for minimal capacitance\n");
```

### Solutions

```c
// 1. Disable slew rate control for testing
ret = ad5758_slew_rate_config(dev, AD5758_SR_DIS, 0, 0);
pr_info("Slew rate disabled. Check if settling improved.\n");

// 2. Reduce load capacitance
// - Use shorter cables
// - Add external buffer amplifier for capacitive loads
// - Check for parallel capacitors in circuit

// 3. If slew rate needed, optimize settings
ret = ad5758_slew_rate_config(dev,
                              AD5758_SR_EN,
                              AD5758_SR_STEP_256_CODES,  // Larger steps
                              AD5758_SR_RATE_230_KHZ);   // Faster rate
pr_info("Slew rate optimized for faster transitions.\n");

// 4. Check datasheet for maximum load specs
// Example: AD5758 can drive 1nF || 10kΩ
```

---

## Issue: SPI Communication Errors

### Symptoms
- Device ID readback incorrect or 0xFFFF
- Register writes don't take effect
- Intermittent communication failures

### Debug Steps

```c
// 1. Verify SPI configuration
pr_info("=== SPI Configuration ===\n");
pr_info("Mode: %u (expected: 1 or 3)\n", spi_init.mode);
pr_info("Clock: %u Hz (max per datasheet)\n", spi_init.max_speed_hz);
pr_info("Chip select: GPIO %u\n", spi_init.chip_select);

// 2. Test basic SPI transaction
pr_info("\n=== SPI Loopback Test ===\n");
uint8_t tx_data[] = {0xAA, 0x55, 0xAA, 0x55};
uint8_t rx_data[4] = {0};

ret = no_os_spi_write_and_read(spi_desc, tx_data, 4);
pr_info("SPI transaction result: %d\n", ret);

// 3. Read device ID multiple times
pr_info("\n=== Device ID Consistency Test ===\n");
for (int i = 0; i < 10; i++) {
    uint32_t id;
    ret = ad5758_reg_read(dev, AD5758_DEVICE_ID, &id);
    pr_info("Read %d: 0x%04X (ret=%d)\n", i, id, ret);
    no_os_mdelay(10);
}

// 4. Check signal integrity with scope
pr_info("\n=== Signal Integrity Check ===\n");
pr_info("Use oscilloscope to verify:\n");
pr_info("  - SCLK: Clean edges, correct frequency\n");
pr_info("  - MOSI: Valid data transitions\n");
pr_info("  - MISO: Device responding with data\n");
pr_info("  - CS: Proper timing, active during transaction\n");
```

### Solutions

```c
// 1. Verify SPI mode (typically mode 1 or 3 for DACs)
spi_init.mode = NO_OS_SPI_MODE_1;

// 2. Reduce clock speed for debugging
spi_init.max_speed_hz = 1000000;  // 1 MHz (slow but reliable)

// 3. Check wiring
// - Short connections (<10cm for breadboard)
// - Proper ground connections
// - Pull-up resistors on MISO if needed

// 4. Verify CS timing
// Some DACs need minimum CS high time between transactions
ret = no_os_spi_write_and_read(spi_desc, tx_buf, len);
no_os_udelay(1);  // Minimum CS high time
ret = no_os_spi_write_and_read(spi_desc, tx_buf2, len);

// 5. Enable CRC if device supports (AD5758, AD3552R)
ret = ad5758_set_crc(dev, AD5758_CRC_ENABLE);
pr_info("CRC enabled for error detection.\n");
```

---

## Issue: Output Noise or Instability

### Symptoms
- Noisy output voltage (AC-coupled scope shows fluctuations)
- Unstable readings on DMM
- Output varies with time

### Possible Causes
1. Reference voltage noise
2. Poor power supply filtering
3. Ground loops
4. Excessive load capacitance
5. PCB layout issues

### Debug Steps

```c
// 1. Test with different codes
pr_info("=== Noise Test ===\n");
pr_info("Setting DAC to midscale (0x8000)...\n");
ret = ad5758_dac_input_write(dev, 0x8000);
no_os_mdelay(100);

pr_info("Measure output with:\n");
pr_info("  - DMM: Check for drift/instability\n");
pr_info("  - Scope (AC-coupled): Check for noise amplitude\n");
pr_info("  - Spectrum analyzer: Identify noise frequencies\n");

// 2. Check reference stability
pr_info("\n=== Reference Voltage Test ===\n");
pr_info("If external reference used:\n");
pr_info("  - Measure reference pin directly\n");
pr_info("  - Should be stable within ±0.01%%\n");

// 3. Test power supply rejection
pr_info("\n=== Power Supply Test ===\n");
pr_info("Vary supply voltage by ±5%% and observe output.\n");
pr_info("Good PSRR: <1 LSB change for 10%% supply variation\n");
```

### Solutions

```c
// 1. Use internal reference if stable
ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);

// 2. Add power supply filtering
// Hardware: 10μF + 100nF bypass caps near DAC

// 3. Check grounding
// - Single-point ground for analog signals
// - Separate digital and analog ground planes
// - Star ground at DAC

// 4. Enable dithering if available (AD5766)
ret = ad5766_set_dither_signal(dev, AD5766_DITHER(0));
pr_info("Dithering enabled to reduce quantization noise.\n");

// 5. Add external filtering
// Low-pass RC filter on output: R=1kΩ, C=100nF → fc=1.6kHz
```

---

## Issue: Incorrect Current Loop Output (4-20mA)

### Symptoms
- Current output not matching expected value
- 4mA minimum not achieved
- 20mA maximum exceeded

### Debug Steps

```c
// 1. Verify current range configuration
pr_info("=== Current Loop Configuration ===\n");
uint32_t range;
ret = ad5758_reg_read(dev, AD5758_OUTPUT_RANGE, &range);
pr_info("Configured range: 0x%02X\n", range & 0x0F);
pr_info("Expected: 0x%02X (4-20mA)\n", RANGE_4mA_20mA);

// 2. Test current at known codes
pr_info("\n=== Current Output Test ===\n");
const struct {
    uint16_t code;
    float expected_ma;  // For 4-20mA range
} current_test[] = {
    {0x0000, 4.0},
    {0x4000, 8.0},
    {0x8000, 12.0},
    {0xC000, 16.0},
    {0xFFFF, 20.0},
};

for (int i = 0; i < 5; i++) {
    ret = ad5758_dac_input_write(dev, current_test[i].code);
    no_os_mdelay(100);
    pr_info("Code 0x%04X: Expected %.2fmA - MEASURE\n",
            current_test[i].code, current_test[i].expected_ma);
    no_os_mdelay(3000);
}

// 3. Check loop compliance
pr_info("\n=== Loop Compliance Check ===\n");
pr_info("Measure voltage drop across current loop.\n");
pr_info("DAC must maintain regulation up to compliance voltage.\n");
pr_info("Example: 12V supply, max 600Ω loop = 12V drop at 20mA\n");
```

### Solutions

```c
// 1. Set correct current range
ret = ad5758_set_out_range(dev, RANGE_4mA_20mA);

// 2. Verify loop resistance
// Total loop resistance = Load + Wiring
// Must be within DAC compliance spec

// 3. Check power supply voltage
// Supply must be high enough for loop voltage drop
// Vsupply > (I_max × R_loop) + V_compliance_min

// 4. Apply current calibration
float measured_4ma = 4.05;   // Actual at code 0x0000
float measured_20ma = 19.92; // Actual at code 0xFFFF
float offset_ma = measured_4ma - 4.0;
float gain_error = ((measured_20ma - measured_4ma) / 16.0) - 1.0;

pr_info("Current calibration:\n");
pr_info("  Offset: %.3f mA\n", offset_ma);
pr_info("  Gain error: %.4f %%\n", gain_error * 100.0);

// Apply corrections (if device supports)
```

---

## Debugging Tools and Techniques

### 1. Register Dump Function

```c
void dump_all_dac_registers(struct ad5758_dev *dev)
{
    pr_info("=== AD5758 Full Register Dump ===\n");
    
    uint32_t regs[] = {
        AD5758_DEVICE_ID,
        AD5758_OUTPUT_RANGE,
        AD5758_DAC_INPUT,
        AD5758_DAC_CONFIG,
        AD5758_SW_RESET,
        AD5758_DIGITAL_DIAG_CONFIG,
        AD5758_DIGITAL_DIAG_RESULTS,
        // ... add all registers
    };
    
    for (int i = 0; i < ARRAY_SIZE(regs); i++) {
        uint32_t value;
        int ret = ad5758_reg_read(dev, regs[i], &value);
        pr_info("Reg 0x%02X: 0x%04X (ret=%d)\n", regs[i], value, ret);
    }
}
```

---

### 2. Automated Test Sequence

```c
int run_dac_diagnostics(struct ad5758_dev *dev)
{
    pr_info("=== Starting DAC Diagnostics ===\n");
    
    // 1. Communication test
    pr_info("\n1. SPI Communication Test\n");
    uint32_t id;
    if (ad5758_reg_read(dev, AD5758_DEVICE_ID, &id) != 0) {
        pr_err("FAIL: Cannot read device ID\n");
        return -1;
    }
    pr_info("PASS: Device ID = 0x%04X\n", id);
    
    // 2. Register readback test
    pr_info("\n2. Register Readback Test\n");
    uint16_t test_code = 0x5A5A;
    ad5758_dac_input_write(dev, test_code);
    uint32_t readback;
    ad5758_reg_read(dev, AD5758_DAC_INPUT, &readback);
    if (readback == test_code) {
        pr_info("PASS: Readback matches written value\n");
    } else {
        pr_err("FAIL: Readback 0x%04X != written 0x%04X\n", 
               readback, test_code);
    }
    
    // 3. Output range test
    pr_info("\n3. Output Range Configuration Test\n");
    ad5758_set_out_range(dev, RANGE_0V_10V);
    ad5758_reg_read(dev, AD5758_OUTPUT_RANGE, &readback);
    if ((readback & 0x0F) == RANGE_0V_10V) {
        pr_info("PASS: Range configured correctly\n");
    } else {
        pr_err("FAIL: Range mismatch\n");
    }
    
    pr_info("\n=== Diagnostics Complete ===\n");
    return 0;
}
```

---

### 3. Oscilloscope Triggers

```c
// Use GPIO toggle for scope triggering
void dac_update_with_trigger(struct ad5758_dev *dev, uint16_t code)
{
    // Set trigger GPIO high
    no_os_gpio_set_value(debug_gpio, NO_OS_GPIO_HIGH);
    
    // Perform DAC update
    ad5758_dac_input_write(dev, code);
    
    // Set trigger GPIO low
    no_os_gpio_set_value(debug_gpio, NO_OS_GPIO_LOW);
    
    // Now scope can trigger on rising edge and capture DAC settling
}
```
