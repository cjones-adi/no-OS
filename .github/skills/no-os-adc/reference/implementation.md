# ADC Driver Implementation Guide

Step-by-step guide to implementing ADC drivers in the no-OS framework.

---

## ADC Driver Architecture

### Core Data Structures

**Device Descriptor** (runtime state):
```c
struct ad4692_desc {
    struct no_os_spi_desc *spi_desc;      // SPI communication interface
    struct no_os_gpio_desc *reset_desc;   // Optional reset GPIO
    enum ad4692_device_id id;             // Device variant

    // Configuration cache
    uint8_t num_channels;                 // Number of channels
    uint32_t vref_mv;                     // Reference voltage (mV)

    // Internal state
    uint8_t buff[FRAME_SIZE];             // SPI transaction buffer
};
```

**Initialization Parameters**:
```c
struct ad4692_init_param {
    struct no_os_spi_init_param *spi_ip;     // SPI configuration
    struct no_os_gpio_init_param *gpio_reset; // Optional reset
    enum ad4692_device_id device_id;          // Part variant
    uint32_t ref_voltage;                     // Reference (mV)
};
```

---

### Standard API Pattern

**Initialization**:
```c
// Initialize ADC device
int ad4692_init(struct ad4692_desc **device,
                struct ad4692_init_param *init_param);

// Remove ADC device and free resources
int ad4692_remove(struct ad4692_desc *dev);
```

**Register Access**:
```c
// Read register
int ad4692_reg_read(struct ad4692_desc *dev,
                    uint32_t reg_addr,
                    uint32_t *reg_data);

// Write register
int ad4692_reg_write(struct ad4692_desc *dev,
                     uint32_t reg_addr,
                     uint32_t reg_data);

// Read-modify-write (update bits)
int ad4692_reg_update(struct ad4692_desc *dev,
                      uint32_t reg_addr,
                      uint32_t mask,
                      uint32_t val);
```

**Data Acquisition**:
```c
// Read single conversion result
int ad4692_read_data(struct ad4692_desc *dev,
                     uint32_t *data);

// Read specific channel
int ad4692_read_channel(struct ad4692_desc *dev,
                        uint8_t channel,
                        uint32_t *data);

// Burst read (multiple samples)
int ad4692_burst_read(struct ad4692_desc *dev,
                      uint32_t *buffer,
                      uint16_t samples);
```

---

## SAR (Successive Approximation Register) ADCs

**Examples**: AD4692, AD469x, AD405x, AD7091r

**Characteristics**:
- Fast conversion (kHz to MHz sample rates)
- Multi-channel (up to 16 channels typical)
- Lower resolution (12-18 bits)
- Direct channel selection
- Minimal configuration required

**Typical Use Cases**:
- Multi-channel data acquisition
- Fast scanning applications
- Control loop feedback
- Signal monitoring

**Configuration Pattern**:
```c
// Simple channel selection
ret = ad4692_set_channel(dev, channel_num);

// Read channel data
ret = ad4692_read_channel(dev, channel_num, &data);

// Configure input range
ret = ad4692_set_input_range(dev, range);
```

---

## Sigma-Delta ADCs

**Examples**: AD7124, AD717x, AD7768-1, AD7799

**Characteristics**:
- High precision (16-24 bits)
- Lower sample rates (Hz to kHz)
- Multiple "setups" (configuration profiles)
- Advanced filtering (SINC3, SINC5)
- Per-setup gain, reference, filter configuration
- Excellent noise performance

**Typical Use Cases**:
- Precision measurements
- Sensor interfaces (temperature, pressure, weight)
- Industrial process control
- Medical instrumentation

**Configuration Pattern** (Setup-Based):
```c
// Define setup 0: bipolar, external ref, gain=1
struct ad7124_channel_setup setup0 = {
    .bi_unipolar = AD7124_BIPOLAR,
    .ref_source = AD7124_REFIN1,
    .pga = AD7124_PGA_GAIN_1,
    .ref_buff = true,
    .input_buff = true,
};

// Assign channel 0 to setup 0
struct ad7124_channel_map ch0_map = {
    .channel_enable = true,
    .setup_sel = 0,
    .ainp = AD7124_AIN0,      // Positive input
    .ainm = AD7124_AVSS,      // Negative input (ground)
};

ret = ad7124_setup_channel(dev, 0, setup0, ch0_map);
```

---

## Initialization Order Best Practices

**Correct order**:
1. Reset device (hardware or software)
2. Configure SPI interface (CRC if used)
3. Verify device ID
4. Configure reference and power
5. Set up channels and filters
6. Perform calibration (if needed)
7. Set conversion mode
8. Enable channels

---

## Resource Management

**Allocate in init**:
```c
dev = no_os_calloc(1, sizeof(*dev));
if (!dev)
    return -ENOMEM;
```

**Free in remove**:
```c
void ad7124_remove(struct ad7124_desc *dev)
{
    if (!dev)
        return;

    no_os_spi_remove(dev->spi_desc);
    no_os_free(dev);
}
```

---

## Error Handling

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

---

## Reference Drivers

**Recommended Examples**:
- **AD4692**: Modern SAR ADC, well-documented, IIO support
- **AD7124**: Sigma-Delta, full setup/channel/filter configuration
- **AD7768-1**: Single-channel precision, digital calibration
- **AD717x**: Sigma-Delta family with extensive features

**Files to Study**:
- `drivers/adc/ad4692/ad4692.h` - SAR ADC API
- `drivers/adc/ad7124/ad7124.h` - Sigma-Delta API
- `drivers/adc/ad4692/iio_ad4692.c` - IIO integration
- `drivers/adc/ad7124/ad7124.c` - Full implementation
