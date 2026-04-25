# DAC Best Practices

Guidelines for implementing robust and maintainable DAC drivers.

## Initialization Best Practices

### 1. Initialization Order

**Correct sequence**:
```c
1. Reset device (hardware or software)
2. Configure SPI interface
3. Enable reference voltage
4. Set output ranges
5. Configure power modes
6. Set default DAC codes
7. Enable outputs
```

**Example**:
```c
int init_dac_properly(void)
{
    struct ad5758_dev *dev;
    struct ad5758_init_param init = {
        .spi_ip = &spi_init,
    };
    int ret;

    // Step 1-2: Init with SPI
    ret = ad5758_init(&dev, &init);
    if (ret) {
        pr_err("DAC init failed: %d\n", ret);
        return ret;
    }

    // Step 3: Enable reference
    ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);
    if (ret) {
        pr_err("Reference enable failed: %d\n", ret);
        goto cleanup;
    }

    // Step 4: Set output range
    ret = ad5758_set_out_range(dev, RANGE_0V_10V);
    if (ret) {
        pr_err("Range config failed: %d\n", ret);
        goto cleanup;
    }

    // Step 6: Set safe default output (midscale)
    ret = ad5758_dac_input_write(dev, 0x8000);
    if (ret) {
        pr_err("Default value write failed: %d\n", ret);
        goto cleanup;
    }

    return 0;

cleanup:
    ad5758_remove(dev);
    return ret;
}
```

---

### 2. Error Handling

**Always check return values**:
```c
// BAD: Ignoring return values
ad5758_init(&dev, &init);
ad5758_set_out_range(dev, RANGE_0V_10V);
ad5758_dac_input_write(dev, 0x8000);

// GOOD: Checking all return values
ret = ad5758_init(&dev, &init);
if (ret) {
    pr_err("Init failed: %d\n", ret);
    return ret;
}

ret = ad5758_set_out_range(dev, RANGE_0V_10V);
if (ret) {
    pr_err("Range config failed: %d\n", ret);
    ad5758_remove(dev);
    return ret;
}

ret = ad5758_dac_input_write(dev, 0x8000);
if (ret) {
    pr_err("DAC write failed: %d\n", ret);
    ad5758_remove(dev);
    return ret;
}
```

---

### 3. Verify Critical Configuration

**Readback verification** (when available):
```c
// Write configuration
ret = ad5758_set_out_range(dev, RANGE_0V_10V);
if (ret)
    return ret;

// Verify configuration was applied
uint32_t range_reg;
ret = ad5758_reg_read(dev, AD5758_OUTPUT_RANGE, &range_reg);
if ((range_reg & 0x0F) != RANGE_0V_10V) {
    pr_err("Range configuration mismatch! Expected 0x%02X, got 0x%02X\n",
           RANGE_0V_10V, range_reg & 0x0F);
    return -EIO;
}
```

---

## Resource Management

### 1. Allocation and Cleanup

**Proper memory management**:
```c
// Allocate in init
struct ad5758_dev *dev;
dev = no_os_calloc(1, sizeof(*dev));
if (!dev) {
    pr_err("Failed to allocate device structure\n");
    return -ENOMEM;
}

dev->spi_desc = no_os_calloc(1, sizeof(*dev->spi_desc));
if (!dev->spi_desc) {
    no_os_free(dev);
    return -ENOMEM;
}

// Free in remove (check for NULL)
void ad5758_remove(struct ad5758_dev *dev)
{
    if (!dev)
        return;

    if (dev->spi_desc)
        no_os_spi_remove(dev->spi_desc);
    
    if (dev->gpio_reset)
        no_os_gpio_remove(dev->gpio_reset);

    no_os_free(dev);
}
```

---

### 2. Safe Cleanup on Error

**Use goto for cleanup paths**:
```c
int ad5766_init(struct ad5766_dev **device, struct ad5766_init_param *init)
{
    struct ad5766_dev *dev;
    int ret;

    dev = no_os_calloc(1, sizeof(*dev));
    if (!dev)
        return -ENOMEM;

    ret = no_os_spi_init(&dev->spi_desc, init->spi_ip);
    if (ret)
        goto error_dev;

    ret = no_os_gpio_get_optional(&dev->gpio_reset, init->gpio_reset_ip);
    if (ret)
        goto error_spi;

    ret = no_os_gpio_get_optional(&dev->gpio_ldac, init->gpio_ldac_ip);
    if (ret)
        goto error_reset;

    *device = dev;
    return 0;

error_reset:
    no_os_gpio_remove(dev->gpio_reset);
error_spi:
    no_os_spi_remove(dev->spi_desc);
error_dev:
    no_os_free(dev);
    return ret;
}
```

---

## Safe Startup Values

### 1. Configure Before Enable

**Set known-safe values**:
```c
// Configure all channels to safe defaults before enabling
int configure_safe_startup(struct ad5766_dev *dev)
{
    int ret;

    // 1. Set all channels to midscale
    for (int ch = 0; ch < 16; ch++) {
        ret = ad5766_write_register(dev, ch, 0x8000);
        if (ret)
            return ret;
    }

    // 2. Configure span for all channels
    for (int ch = 0; ch < 16; ch++) {
        ret = ad5766_set_span(dev, ch, AD5766_M_10V_TO_P_10V);
        if (ret)
            return ret;
    }

    // 3. Configure clear code (for emergency shutdown)
    ret = ad5766_set_clr_span(dev, AD5766_MID, AD5766_M_10V_TO_P_10V);
    if (ret)
        return ret;

    // 4. Power up all channels
    ret = ad5766_set_pwr_dac(dev, 0x0000);  // 0 = power up
    
    return ret;
}
```

---

### 2. Clear Code Configuration

**Configure hardware reset behavior**:
```c
// Set safe state for CLR pin assertion
ret = ad5766_set_clr_span(dev, AD5766_MID, span);

// Benefits:
// - CLR pin assertion → outputs go to 0V (midscale)
// - Emergency shutdown without software
// - Predictable power-on state
```

---

## Multi-Channel Synchronization

### 1. Use LDAC for Glitch-Free Updates

**DON'T: Multiple immediate updates (causes glitches)**:
```c
// BAD: Channels update at different times
ad5686_write_update_register(dev, AD5686_CH_0, 0x1000);
ad5686_write_update_register(dev, AD5686_CH_1, 0x2000);
ad5686_write_update_register(dev, AD5686_CH_2, 0x3000);
// Glitches visible during transitions
```

**DO: Synchronous update**:
```c
// GOOD: All channels update simultaneously
ad5686_write_register(dev, AD5686_CH_0, 0x1000);
ad5686_write_register(dev, AD5686_CH_1, 0x2000);
ad5686_write_register(dev, AD5686_CH_2, 0x3000);
ad5686_update_register(dev, AD5686_CH_ALL);
// Glitch-free simultaneous update
```

---

### 2. Minimize SPI Transactions

**Batch updates efficiently**:
```c
// Write all channels first (fast SPI transactions)
for (int ch = 0; ch < num_channels; ch++) {
    ad5766_write_register(dev, ch, codes[ch]);
}

// Single update command
uint16_t ldac_mask = (1 << num_channels) - 1;
ad5766_set_sw_ldac(dev, ldac_mask);

// vs. individual write-update calls (slower)
for (int ch = 0; ch < num_channels; ch++) {
    ad5766_write_update_register(dev, ch, codes[ch]);  // Slower
}
```

---

## Output Range Configuration

### 1. Match Range to Application

**Select appropriate range**:
```c
// For sensor biasing (0-5V)
ret = ad5758_set_out_range(dev, RANGE_0V_5V);

// For industrial control (4-20mA)
ret = ad5758_set_out_range(dev, RANGE_4mA_20mA);

// For precision bipolar signals (±10V)
ret = ad5766_set_span(dev, ch, AD5766_M_10V_TO_P_10V);
```

**Benefits**:
- Maximize resolution for required range
- Avoid overdriving circuits
- Better noise performance

---

### 2. Document Range Assumptions

**Add comments for clarity**:
```c
// Configure DAC for 0-10V output
// Resolution: 16-bit → 152.6 μV/LSB
// Midscale (0x8000) → 5.000V
ret = ad5758_set_out_range(dev, RANGE_0V_10V);
```

---

## Calibration and Accuracy

### 1. Apply Calibration When Needed

**Two-point calibration workflow**:
```c
int calibrate_dac_output(struct ad3552r_desc *dev, uint8_t channel)
{
    int ret;
    float measured_zero, measured_full;

    // Measure zero-scale error
    ret = ad3552r_write_raw(dev, channel, 0x0000);
    no_os_mdelay(100);  // Settling time
    measured_zero = measure_output_dmm();  // User measurement

    // Measure full-scale error
    ret = ad3552r_write_raw(dev, channel, 0xFFFF);
    no_os_mdelay(100);
    measured_full = measure_output_dmm();

    // Calculate corrections
    float expected_range = 10.0;  // 0-10V
    float actual_range = measured_full - measured_zero;
    float offset_mv = measured_zero * 1000.0;
    float gain_error = (actual_range / expected_range) - 1.0;

    // Apply corrections
    ret = ad3552r_set_offset(dev, channel, -(int32_t)offset_mv, 0);
    ret = ad3552r_set_scale(dev, channel, 1, (int32_t)(gain_error * 1000000));

    pr_info("Calibration applied: offset=%.3fmV, gain_err=%.4f%%\n",
            offset_mv, gain_error * 100.0);

    return 0;
}
```

---

### 2. Store Calibration Values

**Persist calibration in NVM**:
```c
struct dac_calibration {
    int32_t offset_mv;
    int32_t gain_ppb;  // parts per billion
};

// Save to EEPROM/flash
void save_calibration(struct dac_calibration *cal);

// Load on startup
void load_calibration(struct ad3552r_desc *dev, uint8_t ch)
{
    struct dac_calibration cal;
    load_from_nvm(&cal);

    ad3552r_set_offset(dev, ch, cal.offset_mv, 0);
    ad3552r_set_scale(dev, ch, 1, cal.gain_ppb / 1000);
}
```

---

## Performance Optimization

### 1. Pre-compute Waveforms

**Avoid real-time computation**:
```c
// BAD: Computing in real-time
while (1) {
    for (int i = 0; i < 1024; i++) {
        float angle = (2.0 * M_PI * i) / 1024.0;
        uint16_t code = 32768 + (uint16_t)(sin(angle) * 32768);
        ad5449_load_update_channel(dev, 0, code);
        no_os_udelay(10);
    }
}

// GOOD: Pre-computed lookup table
uint16_t sine_lut[1024];

void init_sine_lut(void)
{
    for (int i = 0; i < 1024; i++) {
        float angle = (2.0 * M_PI * i) / 1024.0;
        sine_lut[i] = 32768 + (uint16_t)(sin(angle) * 32768);
    }
}

// Fast playback
while (1) {
    for (int i = 0; i < 1024; i++) {
        ad5449_load_update_channel(dev, 0, sine_lut[i]);
        no_os_udelay(10);
    }
}
```

---

### 2. Use DMA for High-Speed Waveforms

**Offload CPU for continuous output**:
```c
// Configure DMA for circular buffer
void setup_high_speed_waveform(void)
{
    // 1. Prepare waveform buffer
    prepare_waveform_buffer(buffer, size);

    // 2. Configure SPI with DMA
    spi_init.mode = NO_OS_SPI_DMA_MODE;
    no_os_spi_init(&spi_desc, &spi_init);

    // 3. Start circular DMA transfer
    no_os_spi_write_dma(spi_desc, buffer, size, NO_OS_DMA_CIRCULAR);

    // DMA continuously updates DAC without CPU
}
```

---

## Debugging Best Practices

### 1. Add Debug Logging

**Conditional debug output**:
```c
#ifdef DEBUG_DAC
    #define dac_debug(fmt, ...) pr_debug("DAC: " fmt, ##__VA_ARGS__)
#else
    #define dac_debug(fmt, ...) do {} while(0)
#endif

int ad5758_dac_input_write(struct ad5758_dev *dev, uint16_t code)
{
    dac_debug("Writing code 0x%04X\n", code);
    
    int ret = ad5758_reg_write(dev, AD5758_DAC_INPUT, code);
    
    if (ret)
        dac_debug("Write failed with error %d\n", ret);
    
    return ret;
}
```

---

### 2. Implement Register Dumps

**Diagnostic helper functions**:
```c
void ad5758_dump_registers(struct ad5758_dev *dev)
{
    uint32_t value;
    
    pr_info("=== AD5758 Register Dump ===\n");
    
    ad5758_reg_read(dev, AD5758_OUTPUT_RANGE, &value);
    pr_info("Output Range: 0x%04X\n", value);
    
    ad5758_reg_read(dev, AD5758_DAC_INPUT, &value);
    pr_info("DAC Input: 0x%04X\n", value);
    
    ad5758_reg_read(dev, AD5758_DAC_CONFIG, &value);
    pr_info("DAC Config: 0x%04X\n", value);
    
    // ... more registers
}
```

---

## Common Anti-Patterns to Avoid

### 1. Don't Ignore Settling Time

```c
// BAD: No settling time
ad5758_dac_input_write(dev, 0xFFFF);
measure_output();  // May read transitional value

// GOOD: Allow settling
ad5758_dac_input_write(dev, 0xFFFF);
no_os_mdelay(10);  // Wait for output to settle
measure_output();  // Accurate reading
```

---

### 2. Don't Assume Default Configuration

```c
// BAD: Assuming power-on defaults
ad5758_dac_input_write(dev, 0x8000);  // Might not output expected voltage

// GOOD: Explicitly configure
ad5758_set_out_range(dev, RANGE_0V_10V);
ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);
ad5758_dac_input_write(dev, 0x8000);  // Now outputs 5V as expected
```

---

### 3. Don't Mix Immediate and Synchronous Updates

```c
// BAD: Inconsistent update mode
ad5686_write_update_register(dev, 0, code0);  // Immediate
ad5686_write_register(dev, 1, code1);         // Delayed
ad5686_update_register(dev, 1);               // Update

// GOOD: Consistent approach
// Either all immediate OR all synchronous
```

---

## Code Organization

### 1. Separate Configuration from Operation

```c
// Configuration phase (init/setup)
int setup_dac_system(void)
{
    // All configuration here
    ad5758_init(&dev, &init);
    ad5758_set_out_range(dev, RANGE_0V_10V);
    ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);
    
    return 0;
}

// Operational phase (runtime)
void run_dac_operation(void)
{
    // Only DAC updates here
    ad5758_dac_input_write(dev, code);
}
```

---

### 2. Use Descriptive Function Names

```c
// BAD: Vague names
void init_dac(void);
void set_val(uint16_t val);

// GOOD: Clear intent
void init_voltage_dac_0_10v(void);
void set_dac_voltage_code(uint16_t code);
void update_current_loop_4_20ma(float current_ma);
```
