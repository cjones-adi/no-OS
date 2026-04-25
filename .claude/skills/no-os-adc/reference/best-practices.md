# ADC Driver Best Practices and Patterns

Guidelines for writing high-quality ADC drivers in no-OS.

---

## Initialization Best Practices

### 1. Initialization Order

**Correct order**:
```c
int ad7124_init(struct ad7124_desc **device, struct ad7124_init_param *init_param)
{
    int ret;
    struct ad7124_desc *dev;
    uint32_t id;

    // 1. Validate parameters
    if (!device || !init_param)
        return -EINVAL;

    // 2. Allocate descriptor
    dev = no_os_calloc(1, sizeof(*dev));
    if (!dev)
        return -ENOMEM;

    // 3. Initialize SPI/I2C interface
    ret = no_os_spi_init(&dev->spi_desc, init_param->spi_ip);
    if (ret)
        goto error_dev;

    // 4. Reset device (hardware or software)
    ret = ad7124_reset(dev);
    if (ret)
        goto error_spi;

    // 5. Verify device ID
    ret = ad7124_reg_read(dev, AD7124_ID_REG, &id);
    if (ret)
        goto error_spi;

    if (id != AD7124_CHIP_ID) {
        pr_err("Invalid chip ID: 0x%02X (expected 0x14)\n", id);
        ret = -ENODEV;
        goto error_spi;
    }

    // 6. Configure reference and power
    dev->vref_mv = init_param->ref_voltage;
    ret = ad7124_set_power_mode(dev, AD7124_FULL_POWER);
    if (ret)
        goto error_spi;

    // 7. Set up default configuration
    ret = ad7124_setup_defaults(dev);
    if (ret)
        goto error_spi;

    *device = dev;
    return 0;

error_spi:
    no_os_spi_remove(dev->spi_desc);
error_dev:
    no_os_free(dev);
    return ret;
}
```

---

### 2. Resource Management

**Allocate in init**:
```c
// Use calloc to zero-initialize
dev = no_os_calloc(1, sizeof(*dev));
if (!dev)
    return -ENOMEM;
```

**Free in remove**:
```c
int ad7124_remove(struct ad7124_desc *dev)
{
    if (!dev)
        return -EINVAL;

    // Free platform resources first
    if (dev->spi_desc)
        no_os_spi_remove(dev->spi_desc);

    if (dev->gpio_reset)
        no_os_gpio_remove(dev->gpio_reset);

    // Free descriptor last
    no_os_free(dev);

    return 0;
}
```

---

### 3. Error Handling

**Always check return values**:
```c
ret = ad7124_init(&dev, &init_param);
if (ret) {
    pr_err("Init failed: %d\n", ret);
    return ret;
}

// Clean up on error
error_cleanup:
    ad7124_remove(dev);
    return ret;
```

**Use error labels for cleanup**:
```c
int function(void)
{
    ret = step1();
    if (ret)
        goto error_step1;

    ret = step2();
    if (ret)
        goto error_step2;

    return 0;

error_step2:
    cleanup_step1();
error_step1:
    return ret;
}
```

---

## Configuration Best Practices

### 1. Channel Setup Reuse (Sigma-Delta)

**Efficient: Share one setup across multiple channels**:
```c
// Setup 0: Bipolar, gain=1, external ref
struct ad7124_channel_setup setup0 = {
    .bi_unipolar = AD7124_BIPOLAR,
    .ref_source = AD7124_REFIN1,
    .pga = AD7124_PGA_GAIN_1,
    .ref_buff = true,
    .input_buff = true,
};

// All channels use setup 0
ch0_map.setup_sel = 0;
ch1_map.setup_sel = 0;
ch2_map.setup_sel = 0;
```

**Inefficient: Creating separate setups for identical configurations**:
```c
// DON'T DO THIS - wastes setup slots
setup0 = {.pga = AD7124_PGA_GAIN_1, ...};
setup1 = {.pga = AD7124_PGA_GAIN_1, ...};  // Same as setup0!
setup2 = {.pga = AD7124_PGA_GAIN_1, ...};  // Same as setup0!
```

---

### 2. Input Buffering

**Enable buffers for high-impedance sources**:
```c
setup.ref_buff = true;    // Reference buffer
setup.input_buff = true;  // Input buffer
```

**Disable for low-impedance sources** (to reduce power):
```c
// Low-impedance source (< 1kΩ)
setup.ref_buff = false;
setup.input_buff = false;
```

---

### 3. Filter Selection

**Use appropriate filter for application**:
```c
// Precision DC measurements
filter.filter = AD7124_SINC5_FILTER;
filter.odr = AD7124_ODR_19_SPS;    // Slow for best noise performance
filter.enhfilten = true;            // 50/60Hz rejection

// Fast scanning
filter.filter = AD7124_SINC3_FILTER;
filter.odr = AD7124_ODR_500_SPS;   // Fast sampling
filter.enhfilten = false;
```

---

## Data Acquisition Best Practices

### 1. Performance Optimization

**Use continuous mode instead of repeated single conversions**:
```c
// GOOD: Continuous mode
ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);
while (1) {
    ad7124_wait_for_ready(dev, timeout);
    ad7124_read_data(dev, &data, &channel);
}

// BAD: Repeated single conversions (slower)
while (1) {
    ad7124_set_adc_mode(dev, AD7124_SINGLE_MODE);
    ad7124_wait_for_ready(dev, timeout);
    ad7124_read_data(dev, &data, &channel);
}
```

---

### 2. Wait for Data Ready

**Polling Method** (use timeout):
```c
int ad7124_wait_for_ready(struct ad7124_desc *dev, uint32_t timeout_ms)
{
    uint32_t status;
    uint32_t start_time = no_os_get_time();

    do {
        ret = ad7124_read_status(dev, &status);
        if (ret)
            return ret;

        if (!(status & AD7124_STATUS_RDY))
            return 0;  // Data ready

        no_os_mdelay(1);

    } while ((no_os_get_time() - start_time) < timeout_ms);

    return -ETIMEDOUT;
}
```

**Interrupt Method** (preferred for low power):
```c
// Configure RDY GPIO as input with interrupt
struct no_os_irq_init_param irq_ip = {
    .irq_ctrl_id = IRQ_CTRL_ID,
    .platform_ops = IRQ_OPS,
};

// Register callback
ret = no_os_irq_register_callback(irq_desc, RDY_IRQ_ID,
                                   &irq_callback, dev);
ret = no_os_irq_trigger_level_set(irq_desc, RDY_IRQ_ID,
                                   NO_OS_IRQ_EDGE_FALLING);
ret = no_os_irq_enable(irq_desc, RDY_IRQ_ID);
```

---

### 3. Status Register Monitoring

**Check for errors**:
```c
uint32_t status;
ret = ad7124_read_status(dev, &status);

if (status & AD7124_STATUS_ERROR) {
    pr_err("ADC error detected\n");

    // Check specific error flags
    if (status & AD7124_STATUS_ADC_ERROR)
        pr_err("ADC conversion error\n");

    if (status & AD7124_STATUS_REG_ERROR)
        pr_err("Register access error\n");

    if (status & AD7124_STATUS_CRC_ERROR)
        pr_err("CRC error\n");
}
```

---

## IIO Integration Best Practices

### 1. IIO Wrapper Structure

**Proper descriptor separation**:
```c
struct ad4692_iio_desc {
    struct ad4692_desc *ad4692_desc;     // Core driver instance
    struct iio_device *iio_dev;          // IIO device
    uint32_t active_channels;            // Active channel mask
    uint8_t no_of_active_channels;       // Count
};
```

---

### 2. IIO Attribute Handlers

**Clean attribute implementation**:
```c
int ad4692_iio_read_raw(void *dev, char *buf, uint32_t len,
                        const struct iio_ch_info *channel,
                        intptr_t priv)
{
    struct ad4692_iio_desc *iio_desc = dev;
    uint32_t raw_value;
    int ret;

    ret = ad4692_read_channel(iio_desc->ad4692_desc,
                              channel->ch_num,
                              &raw_value);
    if (ret)
        return ret;

    return snprintf(buf, len, "%u", raw_value);
}
```

---

### 3. IIO Buffer Support

**Efficient buffer update**:
```c
int ad4692_iio_update_buffer(void *dev, uint32_t *buff, uint32_t samples)
{
    struct ad4692_iio_desc *iio_desc = dev;
    uint32_t ch_mask = iio_desc->active_channels;
    uint8_t ch_num;
    int ret;
    uint32_t idx = 0;

    for (uint32_t i = 0; i < samples; i++) {
        for (ch_num = 0; ch_num < 16; ch_num++) {
            if (ch_mask & (1 << ch_num)) {
                ret = ad4692_read_channel(iio_desc->ad4692_desc,
                                          ch_num,
                                          &buff[idx++]);
                if (ret)
                    return ret;
            }
        }
    }

    return 0;
}
```

---

## Power Management Best Practices

### 1. Power Mode Selection

**Choose appropriate power mode**:
```c
// Low-speed application (< 100 SPS)
ret = ad7768_set_power_mode(dev, AD7768_LOW_POWER);

// Medium-speed application (100-1k SPS)
ret = ad7768_set_power_mode(dev, AD7768_MEDIAN_POWER);

// High-speed application (> 1k SPS)
ret = ad7768_set_power_mode(dev, AD7768_FAST);
```

---

### 2. Standby Mode for Periodic Sampling

**Enter standby between samples**:
```c
while (1) {
    // Wake up and perform single conversion
    ad7124_set_adc_mode(dev, AD7124_SINGLE_MODE);
    ad7124_wait_for_ready(dev, timeout);
    ad7124_read_data(dev, &data, &channel);

    // Process data
    process_sample(data);

    // Enter standby for low power
    ad7124_set_adc_mode(dev, AD7124_STANDBY_MODE);

    // Sleep until next sample
    no_os_mdelay(SAMPLE_INTERVAL_MS);
}
```

---

## Debugging Best Practices

### 1. Register Dumps

**Implement register dump for debugging**:
```c
void ad7124_dump_registers(struct ad7124_desc *dev)
{
    uint32_t reg_val;

    pr_debug("=== AD7124 Register Dump ===\n");

    ad7124_reg_read(dev, AD7124_ID_REG, &reg_val);
    pr_debug("ID:         0x%02X\n", reg_val);

    ad7124_reg_read(dev, AD7124_STATUS_REG, &reg_val);
    pr_debug("STATUS:     0x%02X\n", reg_val);

    ad7124_reg_read(dev, AD7124_ADC_CTRL_REG, &reg_val);
    pr_debug("ADC_CTRL:   0x%04X\n", reg_val);

    for (int i = 0; i < 16; i++) {
        ad7124_reg_read(dev, AD7124_CHANNEL_REG(i), &reg_val);
        pr_debug("CH%d:        0x%04X\n", i, reg_val);
    }
}
```

---

### 2. Verification Steps

**Verify device ID**:
```c
uint32_t id;
ret = ad7124_reg_read(dev, AD7124_ID_REG, &id);
pr_debug("Device ID: 0x%02X (expected 0x14)\n", id);
```

**Verify channel enabled**:
```c
uint32_t ch_reg;
ret = ad7124_reg_read(dev, AD7124_CHANNEL_REG(0), &ch_reg);
pr_debug("Channel 0 reg: 0x%04X, enabled: %s\n",
         ch_reg, (ch_reg & AD7124_CH_ENABLE) ? "yes" : "no");
```

---

## Code Organization Best Practices

### 1. Header File Structure

```c
// ad4692.h
#ifndef AD4692_H_
#define AD4692_H_

#include "no_os_spi.h"
#include "no_os_gpio.h"

// Device ID enumeration
enum ad4692_device_id {
    ID_AD4692,
    ID_AD4696,
};

// Device descriptor
struct ad4692_desc {
    struct no_os_spi_desc *spi_desc;
    struct no_os_gpio_desc *reset_desc;
    enum ad4692_device_id id;
    uint8_t num_channels;
    uint32_t vref_mv;
};

// Initialization parameters
struct ad4692_init_param {
    struct no_os_spi_init_param *spi_ip;
    struct no_os_gpio_init_param *gpio_reset;
    enum ad4692_device_id device_id;
    uint32_t ref_voltage;
};

// API functions
int ad4692_init(struct ad4692_desc **device,
                struct ad4692_init_param *init_param);
int ad4692_remove(struct ad4692_desc *dev);
int ad4692_read_channel(struct ad4692_desc *dev,
                        uint8_t channel,
                        uint32_t *data);

#endif // AD4692_H_
```

---

### 2. Source File Organization

```c
// ad4692.c
#include "ad4692.h"
#include "no_os_error.h"
#include "no_os_print_log.h"

/******************************************************************************/
/************************** Register Definitions ******************************/
/******************************************************************************/
#define AD4692_REG_CONFIG       0x01
#define AD4692_REG_CONV_CTRL    0x02

/******************************************************************************/
/************************** Internal Functions ********************************/
/******************************************************************************/
static int ad4692_reg_read(struct ad4692_desc *dev, ...)
{
    // Implementation
}

static int ad4692_reg_write(struct ad4692_desc *dev, ...)
{
    // Implementation
}

/******************************************************************************/
/************************** Public API Functions ******************************/
/******************************************************************************/
int ad4692_init(struct ad4692_desc **device, ...)
{
    // Implementation
}

int ad4692_remove(struct ad4692_desc *dev)
{
    // Implementation
}
```

---

## Anti-Patterns to Avoid

### 1. Don't Ignore Return Values

**BAD**:
```c
ad7124_reg_write(dev, REG_ADDR, value);  // Ignoring return value
ad7124_read_data(dev, &data, &channel);  // Ignoring return value
```

**GOOD**:
```c
ret = ad7124_reg_write(dev, REG_ADDR, value);
if (ret)
    return ret;

ret = ad7124_read_data(dev, &data, &channel);
if (ret)
    return ret;
```

---

### 2. Don't Leak Resources

**BAD**:
```c
dev = no_os_calloc(1, sizeof(*dev));
ret = no_os_spi_init(&dev->spi_desc, &spi_ip);
if (ret)
    return ret;  // Memory leak!
```

**GOOD**:
```c
dev = no_os_calloc(1, sizeof(*dev));
ret = no_os_spi_init(&dev->spi_desc, &spi_ip);
if (ret) {
    no_os_free(dev);
    return ret;
}
```

---

### 3. Don't Use Magic Numbers

**BAD**:
```c
ad7124_reg_write(dev, 0x01, 0x0860);  // What do these mean?
```

**GOOD**:
```c
#define AD7124_ADC_CTRL_REG     0x01
#define AD7124_CONTINUOUS_MODE  (2 << 2)
#define AD7124_FULL_POWER       (0 << 6)

uint16_t ctrl_val = AD7124_CONTINUOUS_MODE | AD7124_FULL_POWER;
ad7124_reg_write(dev, AD7124_ADC_CTRL_REG, ctrl_val);
```
