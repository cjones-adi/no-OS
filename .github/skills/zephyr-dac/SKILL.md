---
name: zephyr-dac
description: 'Complete guide to Zephyr DAC drivers for digital-to-analog converters. Use when implementing DAC drivers, configuring channels and resolution, writing analog output values, supporting multi-channel DACs, understanding buffered vs unbuffered modes, or debugging DAC issues.'
---

# Zephyr DAC Driver Development

This skill provides comprehensive understanding of the Zephyr DAC (Digital-to-Analog Converter) driver subsystem.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement DAC driver", "step by step", "channel_setup", "write_value"
- Questions about: driver API, register access, resolution configuration
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-7) with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "dac-controller", "DTS", "overlay"
- Questions about: DT properties, #io-channel-cells, resolution property
- User asks: "how to define DAC binding", "devicetree example"
- Need: binding patterns (base + device-specific examples)

**Triggers to read reference/api-usage.md**:
- User asks: "how to use DAC", "generate waveform", "sawtooth", "sine wave"
- Questions about: basic output, multi-channel, broadcast mode, voltage conversion
- Need: application-side DAC usage examples (6 patterns)

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "validation", "buffered output", "settling time"
- Questions about: device ready, channel setup, value range, broadcast support
- Need: design patterns (10 detailed patterns)

**Triggers to read reference/debugging.md**:
- User says: "not working", "wrong voltage", "debugging", "DAC issue"
- Build/runtime errors with DAC
- Questions about: bus communication, output measurement, resolution mismatch
- Need: debugging steps (8 detailed tips)

**Triggers to read reference/sample-app.md**:
- User asks: "sample application", "complete example", "project structure"
- Questions about: CMakeLists, prj.conf, overlay, main.c structure
- Need: complete sample application with all files

---

## When to Use This Skill

Use this skill when you need to:
- Implement a new DAC driver for Zephyr
- Configure DAC channels with resolution and buffering options
- Write digital values to generate analog voltage outputs
- Support single-channel or multi-channel DAC devices
- Implement DAC broadcast mode (write to all channels simultaneously)
- Configure buffered vs. unbuffered output modes
- Support internal output paths (on-chip peripheral connections)
- Generate analog waveforms (sine, sawtooth, triangle, DC levels)
- Debug DAC communication or output issues
- Create DAC sample applications
- Write devicetree bindings for DAC devices

## What is a DAC?

**Digital-to-Analog Converters (DACs)** convert discrete digital values into continuous analog voltage signals.

### Key Concepts

- **Resolution**: Number of bits in the DAC input (e.g., 8-bit, 10-bit, 12-bit, 16-bit)
- **Reference Voltage**: Voltage that defines the full-scale output (often VDD or external Vref)
- **Output Range**: Minimum to maximum voltage (e.g., 0V to Vref, or 0V to 2×Vref)
- **Output Buffer**: Optional amplifier to drive loads directly
- **Internal Path**: Direct connection to on-chip peripherals (bypassing external pins)
- **Settling Time**: Time for output to stabilize after a value change
- **Monotonicity**: Output always increases with increasing digital input (no reversals)

### Common DAC Types

- **R-2R Ladder DAC**: Resistor network, moderate speed and accuracy
- **String DAC**: Resistor string, very monotonic, limited resolution
- **Current-Steering DAC**: High speed, used in audio and video
- **Sigma-Delta DAC**: High resolution (16-24 bits), used in precision audio

### Benefits

- **Analog Output Generation** – Create voltage levels for control systems
- **Waveform Synthesis** – Generate sine waves, ramps, arbitrary waveforms
- **Calibration Sources** – Provide reference voltages for testing
- **Audio Generation** – Digital audio playback
- **Motor Control** – Set voltage references for motor drivers

## Architecture Overview

```
Application
    ↓ (dac_channel_setup, dac_write_value)
Zephyr DAC API (include/zephyr/drivers/dac.h)
    ↓ (dac_driver_api callbacks)
DAC Driver Implementation
    ↓ (SPI/I2C/Platform-specific)
Hardware DAC Device
    ↓ (Analog voltage output)
```

### DAC Data Flow

```
1. Channel Configuration
   └─ dac_channel_setup() → Driver configures channel
      ├─ Set resolution (8, 10, 12, 16 bits)
      ├─ Enable/disable output buffer
      └─ Configure internal output path

2. Write Value
   └─ dac_write_value() → Writes digital value to DAC
      └─ Voltage = (value / 2^resolution) × Vref

3. Analog Output
   └─ DAC hardware generates analog voltage
      ├─ Buffered: Drives load directly
      └─ Unbuffered: Requires external amplifier
```

## File Structure (Quick Reference)

- **Driver**: `drivers/dac/dac_<chip>.c`
- **Binding**: `dts/bindings/dac/<vendor>,<chip>-dac.yaml`
- **Kconfig**: Update `drivers/dac/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **dac_channel_cfg** | Channel configuration | `channel_id`, `resolution`, `buffered`, `internal` |
| **dac_driver_api** | Driver API table | `channel_setup()`, `write_value()` |
| **DAC_CHANNEL_BROADCAST** | Special channel ID | Write to all channels simultaneously (if supported) |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Quick Start Workflow

1. **Define Register Map and Commands** for DAC hardware
2. **Define Config and Data Structures** with bus specs
3. **Implement channel_setup API** – Configure resolution, buffering, internal path
4. **Implement write_value API** – Write digital value to DAC
5. **Implement Init Function** – Initialize hardware, set defaults
6. **Define API Structure** with function pointers
7. **Device Instantiation Macro** – Register driver

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### Channel Setup

```c
struct dac_channel_cfg channel_cfg = {
    .channel_id = 0,
    .resolution = 12,     // 12-bit DAC
    .buffered = true,     // Enable output buffer
    .internal = false     // External pin output
};
dac_channel_setup(dac_dev, &channel_cfg);
```

### Write Value

```c
// Set DAC to mid-scale (12-bit: 2048 = 2^12 / 2)
uint32_t value = 2048;
dac_write_value(dac_dev, 0, value);

// Full scale (12-bit: 4095 = 2^12 - 1)
dac_write_value(dac_dev, 0, 4095);
```

### Broadcast Mode

```c
// Write same value to all channels simultaneously
dac_write_value(dac_dev, DAC_CHANNEL_BROADCAST, value);
```

### Voltage to DAC Value Conversion

```c
// Convert voltage to DAC value
// voltage_mv: desired voltage in millivolts
// vref_mv: reference voltage in millivolts
// resolution: DAC resolution in bits
uint32_t voltage_to_dac(uint32_t voltage_mv, uint32_t vref_mv, uint8_t resolution)
{
    uint32_t max_value = (1 << resolution) - 1;
    return (voltage_mv * max_value) / vref_mv;
}

// Example: Generate 1.8V on 12-bit DAC with 3.3V reference
uint32_t value = voltage_to_dac(1800, 3300, 12);  // Returns 2233
dac_write_value(dac_dev, 0, value);
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always validate device ready state before use
- Always call `dac_channel_setup()` before first write
- Validate value range (must be < 2^resolution)
- Use buffered output for direct load driving
- Check broadcast support before use
- Consider settling time for accuracy
- Use POST_KERNEL priority for DAC initialization
- Cache last written value if hardware doesn't support read-back
- Handle multi-compatible device families (different resolutions)
- Validate channel ID in both `channel_setup()` and `write_value()`

❌ **DON'T**:
- Don't assume all channels have same resolution
- Don't write out-of-range values
- Don't use broadcast mode if not supported
- Don't ignore settling time in waveform generation
- Don't assume buffered output is always available

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **DAC API**: `zephyr/include/zephyr/drivers/dac.h`
- **DAC Drivers**: `zephyr/drivers/dac/`
- **Bindings**: `zephyr/dts/bindings/dac/`

**Example Drivers**:
- **AD56x1** (SPI single-channel): `drivers/dac/dac_ad56x1.c`
- **AD559x** (I2C/SPI multi-channel MFD): `drivers/dac/dac_ad559x.c`
- **MAX22017** (SPI dual-channel MFD): `drivers/dac/dac_max22017.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-7)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Binding patterns and examples
- [reference/api-usage.md](reference/api-usage.md) – Application usage (6 patterns + voltage conversion)
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (10 detailed)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (8 tips)
- [reference/sample-app.md](reference/sample-app.md) – Complete sample application

## Summary Checklist

### Driver Implementation
- [ ] Register map and commands defined
- [ ] Config structure with bus specs and properties
- [ ] Data structure with runtime state
- [ ] `channel_setup()` implemented (resolution, buffering, internal path)
- [ ] `write_value()` implemented (write digital value)
- [ ] API structure defined with function pointers
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created (include dac-controller.yaml)
- [ ] #io-channel-cells defined
- [ ] Resolution property defined (if fixed)
- [ ] Kconfig entry with dependencies
- [ ] Board overlay for testing

### Testing
- [ ] Channel setup works (resolution, buffering)
- [ ] Write value works (digital to analog conversion)
- [ ] Output voltage measured correctly
- [ ] Multi-channel works (if supported)
- [ ] Broadcast mode works (if supported)
- [ ] Waveform generation works (sine, sawtooth)
