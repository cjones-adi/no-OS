---
name: zephyr-adc
description: 'Complete guide to Zephyr ADC drivers for analog-to-digital converters. Use when implementing ADC drivers, configuring channels, acquiring voltage measurements, working with gain/reference settings, performing calibration, or debugging ADC issues.'
---

# Zephyr ADC Driver Development

This skill provides comprehensive understanding of the Zephyr ADC (Analog-to-Digital Converter) driver subsystem.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement ADC driver", "channel_setup", "read API", "adc_context"
- Questions about: driver implementation, async read, acquisition thread, callbacks
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-10) with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "adc-controller", "DTS", "overlay"
- Questions about: channel configuration, DT properties, #io-channel-cells
- User asks: "how to define ADC binding", "devicetree example"
- Need: binding patterns (base + device-specific examples)

**Triggers to read reference/api-usage.md**:
- User asks: "how to use ADC", "read channel", "multi-channel", "async read"
- Questions about: synchronous vs async, oversampling, callbacks, sequences
- Need: application-side ADC usage examples (5 patterns)

**Triggers to read reference/value-conversion.md**:
- User asks: "convert to millivolts", "raw to voltage", "ADC conversion", "gain calculation"
- Questions about: adc_raw_to_millivolts, differential conversion
- Need: voltage conversion utilities

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "validation", "buffer size", "adc_sequence_init_dt"
- Questions about: differential vs single-ended, error handling, ADC context
- Need: design patterns (10 detailed patterns)

**Triggers to read reference/debugging.md**:
- User says: "not working", "wrong value", "clipping", "saturation", "debugging"
- Build/runtime errors with ADC
- Questions about: bus communication, reference voltage, overflow
- Need: debugging steps (8 detailed tips)

**Triggers to read reference/sample-app.md**:
- User asks: "complete example", "sample application", "project structure"
- Questions about: CMakeLists, prj.conf, overlay setup, main.c structure
- Need: complete sample application with all files

---

## When to Use This Skill

Use this skill when you need to:
- Implement a new ADC driver for Zephyr
- Configure ADC channels with gain, reference, and acquisition time
- Set up ADC sequences for single or multiple channel sampling
- Perform synchronous or asynchronous ADC reads
- Convert raw ADC values to millivolts/microvolts
- Work with differential or single-ended channels
- Implement calibration support
- Configure resolution and oversampling
- Debug ADC communication or conversion issues
- Create ADC sample applications
- Write devicetree bindings for ADC devices

## What is an ADC?

**Analog-to-Digital Converters (ADCs)** convert continuous analog signals (voltages) into discrete digital values that can be processed by a microcontroller or SoC.

### Key Concepts

- **Resolution**: Number of bits in the ADC output (e.g., 12-bit, 16-bit, 24-bit)
- **Reference Voltage**: Voltage used as the full-scale reference (VDD, internal, external)
- **Gain**: Amplification applied to the input signal before conversion
- **Single-Ended**: Measure voltage relative to ground
- **Differential**: Measure voltage difference between two inputs
- **Acquisition Time**: Time allowed for the ADC sample-and-hold circuit to capture the voltage
- **Oversampling**: Average multiple conversions to reduce noise

### Common ADC Types

- **SAR ADC (Successive Approximation)**: Fast, medium resolution (8-16 bits), low power
- **Sigma-Delta ADC**: High resolution (16-24 bits), slower, excellent for precision measurements
- **Pipeline ADC**: Very fast, used in high-speed applications

### Benefits

- **Precision Measurement** – High-resolution ADCs enable accurate voltage and current sensing
- **Flexibility** – Configurable gain and reference for different signal ranges
- **Differential Mode** – Reject common-mode noise for cleaner measurements
- **Multi-Channel** – Sample multiple analog inputs using channel sequencing

## Architecture Overview

```
Application
    ↓ (adc_channel_setup, adc_read, adc_read_async)
Zephyr ADC API (include/zephyr/drivers/adc.h)
    ↓ (adc_driver_api callbacks)
ADC Driver Implementation
    ↓ (SPI/I2C/Platform-specific)
Hardware ADC Device
```

### ADC Data Flow

```
1. Channel Configuration
   └─ adc_channel_setup() → Driver configures channel
      ├─ Set gain (ADC_GAIN_1, ADC_GAIN_2, etc.)
      ├─ Set reference (ADC_REF_INTERNAL, ADC_REF_VDD_1, etc.)
      ├─ Set acquisition time
      └─ Configure differential/single-ended mode

2. Sequence Initialization
   └─ struct adc_sequence setup
      ├─ Select channels (bitmask)
      ├─ Set resolution
      ├─ Set oversampling
      └─ Provide buffer

3. ADC Read
   ├─ Synchronous: adc_read() → blocks until complete
   └─ Asynchronous: adc_read_async() → non-blocking

4. Value Conversion
   └─ adc_raw_to_millivolts_dt() → Convert to mV
```

## File Structure (Quick Reference)

- **Driver**: `drivers/adc/adc_<chip>.c`
- **Binding**: `dts/bindings/adc/<vendor>,<chip>-adc.yaml`
- **DT Include** (optional): `include/zephyr/dt-bindings/adc/<chip>-adc.h`
- **Kconfig**: Update `drivers/adc/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **adc_channel_cfg** | Channel configuration | `gain`, `reference`, `acquisition_time`, `differential` |
| **adc_dt_spec** | Devicetree ADC spec | `dev` (device), `channel_id`, `resolution`, `vref_mv` |
| **adc_sequence** | Sampling sequence | `channels` (bitmask), `buffer`, `resolution`, `oversampling` |
| **adc_sequence_options** | Multi-sampling options | `extra_samplings`, `interval_us`, `callback` |
| **adc_driver_api** | Driver API table | `channel_setup()`, `read()`, `read_async()`, `ref_internal()` |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## ADC Gain and Reference (Quick Reference)

### Gain Settings

```c
enum adc_gain {
    ADC_GAIN_1_6,  // × 1/6
    ADC_GAIN_1_5,  // × 1/5
    ADC_GAIN_1_4,  // × 1/4
    ADC_GAIN_1_3,  // × 1/3
    ADC_GAIN_1_2,  // × 1/2
    ADC_GAIN_2_3,  // × 2/3
    ADC_GAIN_1,    // × 1 (default)
    ADC_GAIN_2,    // × 2
    ADC_GAIN_3,    // × 3
    ADC_GAIN_4,    // × 4
    // ... up to ADC_GAIN_128
};
```

### Reference Settings

```c
enum adc_reference {
    ADC_REF_VDD_1,      // VDD
    ADC_REF_VDD_1_2,    // VDD / 2
    ADC_REF_VDD_1_3,    // VDD / 3
    ADC_REF_VDD_1_4,    // VDD / 4
    ADC_REF_INTERNAL,   // Internal reference (device-specific)
    ADC_REF_EXTERNAL0,  // External reference 0
    ADC_REF_EXTERNAL1,  // External reference 1
};
```

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Config and Data Structures** with bus specs
3. **Implement Register Read/Write Functions** (I2C/SPI helpers)
4. **Implement channel_setup API** – Configure channel gain, reference, mode
5. **Implement read API (Synchronous)** – Block until conversion complete
6. **Implement read_async API (Asynchronous)** – Non-blocking with signal
7. **Implement ADC Context Callbacks** (if using adc_context helpers)
8. **Implement Acquisition Thread** (optional, for background conversion)
9. **Implement Init Function** – Initialize hardware, set defaults
10. **Define API Structure and Device Instantiation** – Register driver

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### Channel Setup

```c
struct adc_channel_cfg channel_cfg = {
    .gain = ADC_GAIN_1,
    .reference = ADC_REF_INTERNAL,
    .acquisition_time = ADC_ACQ_TIME_DEFAULT,
    .channel_id = 0,
    .differential = 0  // Single-ended
};
adc_channel_setup(adc_dev, &channel_cfg);
```

### Synchronous Read

```c
uint16_t sample_buffer[1];
struct adc_sequence sequence = {
    .channels = BIT(0),
    .buffer = sample_buffer,
    .buffer_size = sizeof(sample_buffer),
    .resolution = 12,
};
int ret = adc_read(adc_dev, &sequence);
```

### Asynchronous Read

```c
struct k_poll_signal async_sig = K_POLL_SIGNAL_INITIALIZER(async_sig);
struct adc_sequence_options options = {
    .extra_samplings = 0,
    .user_data = &async_sig,
};
sequence.options = &options;
adc_read_async(adc_dev, &sequence, &async_sig);
```

### Value Conversion

```c
int32_t val_mv = adc_raw_to_millivolts_dt(&adc_dt_spec, &raw_value);
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always validate device ready state before use
- Always call `adc_channel_setup()` before first read
- Validate buffer size matches channel count × bytes per sample
- Use `adc_sequence_init_dt()` for DT-defined channels
- Handle differential vs. single-ended correctly
- Check conversion support (not all drivers support all features)
- Use ADC context helpers in drivers (simplifies state management)
- Provide internal reference voltage in API (`ref_internal()`)
- Validate channel IDs against hardware limits
- Document acquisition time units in binding

❌ **DON'T**:
- Don't assume buffer is pre-zeroed
- Don't ignore resolution limits
- Don't use floating point in drivers
- Don't forget to enable ADC power/clock in init
- Don't block indefinitely in synchronous read

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **ADC API**: `zephyr/include/zephyr/drivers/adc.h`
- **ADC Drivers**: `zephyr/drivers/adc/`
- **Bindings**: `zephyr/dts/bindings/adc/`

**Example Drivers**:
- **AD4130** (SPI Sigma-Delta ADC): `drivers/adc/adc_ad4130.c`
- **AD4114** (SPI multi-channel ADC): `drivers/adc/adc_ad4114.c`
- **LTC2451** (I2C delta-sigma ADC): `drivers/adc/adc_ltc2451.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-10)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Binding patterns (base + examples)
- [reference/api-usage.md](reference/api-usage.md) – Application usage (5 patterns)
- [reference/value-conversion.md](reference/value-conversion.md) – Voltage conversion utilities
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (10 detailed)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (8 tips)
- [reference/sample-app.md](reference/sample-app.md) – Complete sample application

## Summary Checklist

### Driver Implementation
- [ ] Register map defined with bit masks
- [ ] Config structure with bus specs and properties
- [ ] Data structure with runtime state
- [ ] Bus read/write helper functions
- [ ] `channel_setup()` implemented
- [ ] `read()` implemented (synchronous)
- [ ] `read_async()` implemented (optional)
- [ ] `ref_internal()` implemented (if internal reference)
- [ ] ADC context integration (if using helpers)
- [ ] API structure defined with function pointers
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created (include adc-controller.yaml)
- [ ] #io-channel-cells defined
- [ ] Kconfig entry with dependencies
- [ ] Board overlay for testing

### Testing
- [ ] Channel setup works (gain, reference, mode)
- [ ] Synchronous read works
- [ ] Asynchronous read works (if implemented)
- [ ] Value conversion to millivolts is correct
- [ ] Multi-channel sampling works
- [ ] Oversampling works (if supported)
- [ ] Differential mode works (if supported)
