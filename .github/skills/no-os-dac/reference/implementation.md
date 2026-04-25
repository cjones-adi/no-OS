# DAC Driver Implementation Guide

Step-by-step guide for implementing DAC drivers in the no-OS framework.

## DAC Driver Architecture

### Core Data Structures

**Device Descriptor** (runtime state):
```c
struct ad5766_dev {
    struct no_os_spi_desc *spi_desc;      // SPI communication
    struct no_os_gpio_desc *gpio_reset;   // Hardware reset
    struct no_os_gpio_desc *gpio_ldac;    // Load DAC control

    // Configuration state
    enum ad5766_span span[16];            // Per-channel output spans
    uint32_t daisy_chain_en;              // Daisy-chain mode
    uint16_t pwr_down_mask;               // Power-down channels
};
```

**Initialization Parameters**:
```c
struct ad5766_init_param {
    struct no_os_spi_init_param *spi_ip;     // SPI configuration
    struct no_os_gpio_init_param *gpio_reset_ip;
    struct no_os_gpio_init_param *gpio_ldac_ip;

    // Device-specific configuration
    enum ad5766_span output_range[16];       // Per-channel spans
    enum ad5766_state daisy_chain_en;        // Enable daisy-chain
};
```

---

## Standard API Pattern

### Initialization

```c
// Initialize DAC device
int32_t ad5766_init(struct ad5766_dev **device,
                    struct ad5766_init_param init_param);

// Remove DAC device and free resources
int32_t ad5766_remove(struct ad5766_dev *dev);
```

### Data Output

```c
// Write to DAC input register (no update yet)
int32_t ad5766_write_register(struct ad5766_dev *dev,
                               enum ad5766_dac dac,
                               uint16_t data);

// Write and immediately update DAC output
int32_t ad5766_write_update_register(struct ad5766_dev *dev,
                                      enum ad5766_dac dac,
                                      uint16_t data);

// Trigger synchronous update (LDAC)
int32_t ad5766_set_sw_ldac(struct ad5766_dev *dev,
                           uint16_t setting);
```

### Configuration

```c
// Set output voltage span
int32_t ad5766_set_span(struct ad5766_dev *dev,
                        enum ad5766_dac dac,
                        enum ad5766_span span);

// Power down/up channels
int32_t ad5766_set_pwr_dac(struct ad5766_dev *dev,
                           uint16_t setting);
```

---

## DAC Types and Implementation Patterns

### Simple DACs

**Examples**: AD5421, AD5449

**Characteristics**:
- 1-2 channels
- 12-16 bit resolution
- Direct voltage output
- Minimal configuration
- Fast update rate

**Typical Use Cases**:
- Basic waveform generation
- Simple control voltages
- Biasing circuits
- Test equipment

**API Pattern**:
```c
// Direct write and update (immediate output change)
void ad5449_load_update_channel(struct ad5449_dev *dev,
                                uint8_t channel,
                                uint16_t dac_value);

// Update all channels simultaneously
void ad5449_update_all(struct ad5449_dev *dev);
```

---

### Standard Multi-Channel DACs

**Examples**: AD5686, AD5766, AD5791, AD5754R

**Characteristics**:
- 2-16 channels
- 12-20 bit resolution
- LDAC synchronization support
- Daisy-chain capable
- Per-channel power control

**Typical Use Cases**:
- Multi-channel signal generation
- Synchronized waveform output
- Precision voltage sources
- Multi-point calibration

**API Pattern**:
```c
// Two-step update: write then load
void ad5686_write_register(struct ad5686_dev *dev,
                           enum ad5686_dac_channels channel,
                           uint16_t data);

void ad5686_update_register(struct ad5686_dev *dev,
                            enum ad5686_dac_channels channel);

// Or combined: write and update together
void ad5686_write_update_register(struct ad5686_dev *dev,
                                  enum ad5686_dac_channels channel,
                                  uint16_t data);
```

---

### Advanced Programmable DACs

**Examples**: AD5758, AD5460, AD3552R, AD5770R

**Characteristics**:
- 1-6 channels (multi-function)
- 12-16 bit resolution
- Voltage AND current output modes
- Slew rate control
- Diagnostic features (temperature, status)
- CRC/error detection
- Offset/gain calibration

**Typical Use Cases**:
- Industrial process control (4-20mA loops)
- Precision instrumentation
- Automated test equipment
- Mixed-signal control systems

**API Pattern**:
```c
// High-level abstraction with mode handling
int ad5758_set_out_range(struct ad5758_dev *dev,
                         enum ad5758_output_range range);

int32_t ad5758_dac_input_write(struct ad5758_dev *dev,
                               uint16_t code);

// Advanced features
int ad5460_dac_slew_enable(struct ad5460_desc *dev,
                           uint32_t channel,
                           enum ad5460_slew_lin_step step,
                           enum ad5460_lin_rate rate);
```

---

## Initialization Order

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
int init_dac_system(void)
{
    struct ad5758_dev *dev;
    struct ad5758_init_param init = {
        .spi_ip = &spi_init,
    };
    int ret;

    // Step 1-2: Init with SPI
    ret = ad5758_init(&dev, &init);
    if (ret)
        return ret;

    // Step 3: Enable reference
    ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);
    if (ret)
        goto error;

    // Step 4: Set output range
    ret = ad5758_set_out_range(dev, RANGE_0V_10V);
    if (ret)
        goto error;

    // Step 5: Configure power mode (normal operation)
    // Usually handled in init

    // Step 6: Set safe default output
    ret = ad5758_dac_input_write(dev, 0x8000);  // Midscale
    if (ret)
        goto error;

    // Step 7: Enable outputs
    // Usually automatic or via power control register

    return 0;

error:
    ad5758_remove(dev);
    return ret;
}
```

---

## Error Handling

**Always check return values**:
```c
ret = ad5758_init(&dev, &init);
if (ret) {
    pr_err("Init failed: %d\n", ret);
    return ret;
}

// Verify critical configuration
uint32_t range_reg;
ret = ad5758_reg_read(dev, AD5758_OUTPUT_RANGE, &range_reg);
if ((range_reg & 0x0F) != expected_range) {
    pr_err("Range configuration mismatch!\n");
}
```

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
void ad5758_remove(struct ad5758_dev *dev)
{
    if (!dev)
        return;

    no_os_spi_remove(dev->spi_desc);
    no_os_gpio_remove(dev->gpio_reset);
    no_os_free(dev);
}
```

---

## Safe Startup Values

**Set safe default outputs before enabling**:
```c
// Set safe default outputs before enabling
for (int ch = 0; ch < num_channels; ch++) {
    ret = ad5766_write_register(dev, ch, 0x8000);  // Midscale
}

// Configure clear code for safe reset
ret = ad5766_set_clr_span(dev, AD5766_MID, span);

// Then enable outputs
ret = ad5766_set_pwr_dac(dev, 0x0000);  // Power up all
```

---

## Reference Drivers

**Recommended Examples**:
- **AD5766**: 16-channel voltage DAC with advanced features
- **AD5758**: Single-channel voltage/current with diagnostics
- **AD5686**: Standard multi-channel family (SPI/I2C)
- **AD3552R**: Modern high-speed DAC with CRC
- **AD5460**: Mixed-signal 4-channel DAC with monitoring

**Files to Study**:
- `drivers/dac/ad5766/ad5766.h` - Multi-channel API
- `drivers/dac/ad5758/ad5758.h` - Advanced features API
- `drivers/dac/ad3552r/iio_ad3552r.c` - IIO integration
