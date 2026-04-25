---
name: no-os-adc
description: 'Complete guide to no-OS ADC (Analog-to-Digital Converter) drivers for data acquisition devices. Use when implementing ADC drivers, configuring channels and setups, working with SAR/Sigma-Delta ADCs, setting reference voltage and gain, performing calibration, implementing conversion modes, integrating with IIO framework, or debugging ADC issues.'
---

# no-OS ADC Driver Guide

Quick-start guide for implementing and using ADC drivers in the no-OS framework, covering SAR and Sigma-Delta architectures.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "how to implement", "create new ADC driver", "driver architecture"
- Questions about: device descriptors, init parameters, standard API patterns
- Mentions: SAR ADC implementation, Sigma-Delta setup architecture
- Need: step-by-step implementation guide, data structure details

**Triggers to read reference/api-usage.md**:
- User asks: "how to use", "read channel", "configure ADC", "example code"
- Questions about: channel configuration, reference voltage, gain settings, conversion modes
- Mentions: single-ended vs differential, bipolar vs unipolar, filter selection
- Need: complete usage examples, configuration patterns, multi-channel setup

**Triggers to read reference/calibration.md**:
- User asks: "how to calibrate", "calibration procedure", "accuracy issues"
- Questions about: system calibration, self-calibration, offset/gain correction
- Mentions: calibration types, zero-scale, full-scale, temperature compensation
- Need: calibration workflow, when to use each type, verification methods

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "code quality", "how to organize", "patterns"
- Questions about: initialization order, resource management, error handling
- Mentions: anti-patterns, code organization, performance optimization
- Need: quality guidelines, recommended patterns, what to avoid

**Triggers to read reference/troubleshooting.md**:
- User says: "not working", "no data", "noisy readings", "error", "timeout"
- Questions about: debugging, SPI errors, incorrect voltages, communication issues
- Specific errors: all zeros, unstable readings, CRC errors, conversion timeout
- Need: diagnostic steps, debug techniques, solutions to common issues

---

## When to Use This Skill

- Implementing a new ADC driver for no-OS
- Understanding ADC driver architecture and patterns
- Configuring ADC channels, setups, and input mapping
- Working with different ADC types (SAR, Sigma-Delta, high-speed)
- Setting reference voltage and PGA gain
- Implementing single, continuous, or burst conversion modes
- Performing system or self-calibration
- Integrating ADC drivers with IIO framework
- Optimizing power modes and performance
- Debug ADC data acquisition issues
- Port existing ADC drivers to new variants

---

## ADC Overview

The no-OS framework includes **60+ ADC drivers** supporting various ADC architectures:

**ADC Types**:
- **SAR ADCs**: Fast, multi-channel (AD4692, AD469x, AD405x, AD7091r family)
- **Sigma-Delta ADCs**: High precision (AD7124, AD717x, AD7768-1, AD7799)
- **High-Speed ADCs**: MHz+ sampling (AD9xxx family)
- **Specialized**: Battery monitors (AD7280a), current sense (MAX9611)

**Key Architecture Patterns**:
- Descriptor-based device management
- Channel setup abstraction (sigma-delta)
- Direct channel configuration (SAR)
- Standard register access API
- IIO integration layer
- Hardware abstraction via SPI/I2C

---

## Quick Reference

### SAR ADC Quick Start (AD4692-like)

**Simple single-channel reading**:
```c
#include "ad4692.h"
#include "no_os_spi.h"

// Init
struct ad4692_desc *dev;
struct ad4692_init_param init_param = {
    .spi_ip = &spi_init,
    .device_id = ID_AD4692,
    .ref_voltage = 5000,  // 5V reference
};

ret = ad4692_init(&dev, &init_param);

// Configure and read
ret = ad4692_set_channel(dev, 0);
ret = ad4692_read_channel(dev, 0, &data);

// Convert to voltage
float voltage = (float)data * 5000.0 / 0xFFFF;

// Cleanup
ad4692_remove(dev);
```

**Characteristics**:
- Fast conversion (kHz to MHz rates)
- Multi-channel (up to 16 channels)
- Lower resolution (12-18 bits)
- Direct channel selection
- Minimal configuration

---

### Sigma-Delta ADC Quick Start (AD7124-like)

**High-precision measurement with setup**:
```c
#include "ad7124.h"
#include "no_os_spi.h"

// Init
struct ad7124_desc *dev;
struct ad7124_init_param init_param = {
    .spi_ip = &spi_init,
    .vref_mv = 2500,  // 2.5V reference
};

ret = ad7124_init(&dev, &init_param);

// Configure setup
struct ad7124_channel_setup setup0 = {
    .bi_unipolar = AD7124_BIPOLAR,     // Signed measurements
    .ref_source = AD7124_INT_REF,      // Internal reference
    .pga = AD7124_PGA_GAIN_1,          // Gain = 1
    .ref_buff = true,
    .input_buff = true,
};

struct ad7124_filtcon filter0 = {
    .filter = AD7124_SINC4_FILTER,     // SINC4 filter
    .odr = AD7124_ODR_100_SPS,         // 100 samples/sec
    .enhfilten = false,
};

// Configure channel
struct ad7124_channel_map ch0_map = {
    .channel_enable = true,
    .setup_sel = 0,
    .ainp = AD7124_AIN0,               // Positive input
    .ainm = AD7124_AVSS,               // Ground (single-ended)
};

ret = ad7124_setup_channel(dev, 0, setup0, ch0_map, filter0);

// Start continuous conversion
ret = ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);

// Read data
ret = ad7124_wait_for_ready(dev, 1000);
ret = ad7124_read_data(dev, &data, &channel);

// Cleanup
ad7124_remove(dev);
```

**Characteristics**:
- High precision (16-24 bits)
- Lower sample rates (Hz to kHz)
- Multiple "setups" (config profiles)
- Advanced filtering (SINC3, SINC5)
- Excellent noise performance

---

## Common Patterns

### Channel Configuration

**Single-Ended** (measure relative to ground):
```c
.ainp = AD7124_AIN0,      // Signal input
.ainm = AD7124_AVSS,      // Ground reference
```

**Differential** (measure difference):
```c
.ainp = AD7124_AIN0,      // Positive input
.ainm = AD7124_AIN1,      // Negative input
```

---

### Reference Voltage

**External Reference**:
```c
.ref_source = AD7124_REFIN1,    // External ref on REFIN1+/-
```

**Internal Reference**:
```c
.ref_source = AD7124_INT_REF,   // Internal 2.5V reference
```

---

### Gain Configuration

**PGA Gain** (affects input range):
```c
.pga = AD7124_PGA_GAIN_1,       // Gain = 1 (full range)
.pga = AD7124_PGA_GAIN_8,       // Gain = 8 (1/8 range, 8x amplitude)
.pga = AD7124_PGA_GAIN_128,     // Gain = 128 (for small signals)
```

**Effective Input Range**:
```
Range = Vref / Gain

Example: Vref = 2.5V, Gain = 8
  → Bipolar: ±312.5 mV
  → Unipolar: 0 to 312.5 mV
```

---

### Conversion Modes

**Continuous Mode** (streaming):
```c
ret = ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE);

while (1) {
    ret = ad7124_wait_for_ready(dev, timeout);
    ret = ad7124_read_data(dev, &data, &channel);
}
```

**Single Mode** (low power):
```c
ret = ad7124_set_adc_mode(dev, AD7124_SINGLE_MODE);
ret = ad7124_wait_for_ready(dev, timeout);
ret = ad7124_read_data(dev, &data);
```

---

### Data Conversion

**Bipolar Mode**:
```c
int32_t signed_code = (int32_t)raw_code - 0x800000;
float voltage_mv = ((float)signed_code / 0x800000) * (vref_mv / gain);
```

**Unipolar Mode**:
```c
float voltage_mv = ((float)raw_code / 0xFFFFFF) * (vref_mv / gain);
```

---

### Calibration

**Internal (Self) Calibration**:
```c
// At startup
ret = ad7124_calibrate(dev, AD7124_INT_ZERO_SCALE_CAL, channel);
ret = ad7124_calibrate(dev, AD7124_INT_FULL_SCALE_CAL, channel);
```

**System Calibration** (external reference):
```c
// Apply 0V input
apply_zero_voltage();
ret = ad7124_calibrate(dev, AD7124_SYS_ZERO_SCALE_CAL, channel);

// Apply known reference voltage
apply_reference_voltage(2500);  // 2.5V
ret = ad7124_calibrate(dev, AD7124_SYS_FULL_SCALE_CAL, channel);
```

---

### Filter Selection (Sigma-Delta)

**Precision DC measurements**:
```c
.filter = AD7124_SINC5_FILTER,    // Best noise performance
.odr = AD7124_ODR_19_SPS,         // Slow for precision
.enhfilten = true,                 // 50/60Hz rejection
```

**Fast scanning**:
```c
.filter = AD7124_SINC3_FILTER,    // Fast settling
.odr = AD7124_ODR_500_SPS,        // High speed
.enhfilten = false,
```

---

## Standard API Pattern

All ADC drivers follow this pattern:

```c
// Initialization
int ad_xxxx_init(struct ad_xxxx_desc **device,
                 struct ad_xxxx_init_param *init_param);

// Remove
int ad_xxxx_remove(struct ad_xxxx_desc *dev);

// Register access
int ad_xxxx_reg_read(struct ad_xxxx_desc *dev, uint32_t reg, uint32_t *data);
int ad_xxxx_reg_write(struct ad_xxxx_desc *dev, uint32_t reg, uint32_t data);
int ad_xxxx_reg_update(struct ad_xxxx_desc *dev, uint32_t reg,
                       uint32_t mask, uint32_t val);

// Data acquisition
int ad_xxxx_read_data(struct ad_xxxx_desc *dev, uint32_t *data);
int ad_xxxx_read_channel(struct ad_xxxx_desc *dev, uint8_t ch, uint32_t *data);
```

---

## IIO Integration

**IIO Wrapper**:
```c
struct ad4692_iio_desc {
    struct ad4692_desc *ad4692_desc;     // Core driver
    struct iio_device *iio_dev;          // IIO device
    uint32_t active_channels;            // Channel mask
};

// IIO init
ret = ad4692_iio_init(&iio_desc, &iio_init);
```

**IIO Attributes** (raw, scale, offset):
```c
int ad4692_iio_read_raw(void *dev, char *buf, uint32_t len,
                        const struct iio_ch_info *channel, intptr_t priv)
{
    struct ad4692_iio_desc *iio_desc = dev;
    uint32_t raw_value;
    
    ret = ad4692_read_channel(iio_desc->ad4692_desc,
                              channel->ch_num, &raw_value);
    if (ret)
        return ret;
    
    return snprintf(buf, len, "%u", raw_value);
}
```

---

## Quick Troubleshooting

**No data or all zeros**:
- Check channel is enabled: `.channel_enable = true`
- Verify conversion mode: `ad7124_set_adc_mode(dev, AD7124_CONTINUOUS_MODE)`
- Confirm reference voltage configured: `init_param.vref_mv = 2500`

**Noisy readings**:
- Enable buffers: `.ref_buff = true`, `.input_buff = true`
- Use slower filter: `AD7124_SINC5_FILTER`, lower ODR
- Increase gain for small signals: `.pga = AD7124_PGA_GAIN_32`

**Incorrect voltages**:
- Verify reference voltage matches actual
- Check bipolar/unipolar mode matches signal
- Perform calibration

**Timeout**:
- Increase timeout for slow ODR
- Check status register for errors
- Verify ADC is in active mode

---

## Reference Drivers

**Recommended Examples**:
- **AD4692**: `drivers/adc/ad4692/` - Modern SAR ADC, IIO support
- **AD7124**: `drivers/adc/ad7124/` - Sigma-Delta, full features
- **AD7768-1**: `drivers/adc/ad7768-1/` - Single-channel precision
- **AD717x**: `drivers/adc/ad717x/` - Sigma-Delta family

**Key Files**:
- `drivers/adc/ad4692/ad4692.h` - SAR ADC API
- `drivers/adc/ad7124/ad7124.h` - Sigma-Delta API
- `drivers/adc/ad4692/iio_ad4692.c` - IIO integration
- `drivers/adc/ad7124/ad7124.c` - Full implementation

---

## Reference Documentation

**When to read each file** (use Read tool):

### reference/implementation.md
Step-by-step driver implementation guide: device descriptors, init parameters, standard API patterns, SAR vs Sigma-Delta architecture, resource management, error handling.

### reference/api-usage.md
Detailed API usage examples: single-channel SAR, multi-channel Sigma-Delta, precision measurement with calibration, channel configuration, reference voltage, gain settings, conversion modes, data conversion, power management.

### reference/calibration.md
Complete calibration procedures: system vs self-calibration, calibration workflow, when to use each type, digital offset/gain correction, verification methods, temperature compensation, calibration storage.

### reference/best-practices.md
Best practices and patterns: initialization order, resource management, error handling, channel setup reuse, input buffering, filter selection, performance optimization, IIO integration, code organization, anti-patterns to avoid.

### reference/troubleshooting.md
Common issues and solutions: no data, noisy readings, conversion timeout, incorrect voltages, SPI errors, CRC errors, debugging techniques, register dumps, diagnostic checklist.

---

## Summary

**ADC Types**:
- SAR: Fast (kHz-MHz), multi-channel, 12-18 bits, simple config
- Sigma-Delta: Precision (16-24 bits), Hz-kHz, advanced filtering, setup-based

**Key Concepts**:
- **Descriptor**: Runtime device state
- **Init Param**: Configuration parameters
- **Setup** (Sigma-Delta): Reusable config profile (gain, ref, filter)
- **Channel Map**: Input pin configuration (single-ended/differential)

**Workflow**:
1. Init ADC with reference voltage
2. Configure channel setup (Sigma-Delta) or direct channel (SAR)
3. Set conversion mode (continuous/single)
4. Calibrate (optional but recommended)
5. Read data and convert to voltage

**Best Practices**:
- Always check return values
- Enable buffers for high-impedance sources
- Use appropriate filter for application
- Perform calibration after init
- Share setups across channels (Sigma-Delta)

**See reference/ files for complete details on implementation, API usage, calibration, best practices, and troubleshooting.**
