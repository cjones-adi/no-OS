---
name: no-os-dac
description: 'Complete guide to no-OS DAC (Digital-to-Analog Converter) drivers for signal generation and control. Use when implementing DAC drivers, configuring output ranges, working with voltage/current output modes, implementing synchronous updates, performing offset/gain calibration, using LDAC signals, integrating with IIO framework, or debugging DAC output issues.'
---

# no-OS DAC Driver Guide

Quick-start guide for implementing and using DAC drivers in the no-OS framework. Detailed documentation available in reference files.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement DAC driver", "DAC architecture", "driver structure"
- Questions about: device descriptors, init parameters, standard API patterns
- Need: step-by-step implementation guide, initialization order, resource management
- Creating new DAC driver or porting existing one

**Triggers to read reference/api-usage.md**:
- User asks: "configure output range", "voltage output", "current output", "4-20mA"
- Mentions: output spans, reference voltage, LDAC, slew rate, calibration
- Questions about: synchronous updates, power management, daisy-chain, advanced features
- Need: detailed API examples, configuration patterns, IIO integration

**Triggers to read reference/waveform-generation.md**:
- User asks: "generate waveform", "sine wave", "multi-channel", "signal generation"
- Mentions: triangle wave, sawtooth, square wave, arbitrary waveform, DMA
- Questions about: phase-shifted outputs, synchronized updates, lookup tables
- Need: waveform examples, performance optimization, batch updates

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "how to organize", "initialization order", "error handling"
- Questions about: resource management, safe startup, calibration workflow
- Need: code quality guidelines, anti-patterns to avoid, debugging techniques
- Code review or improving existing implementation

**Triggers to read reference/troubleshooting.md**:
- User says: "not working", "wrong voltage", "glitches", "no output", "error"
- Issues mentioned: SPI errors, noise, slow settling, current loop problems
- Questions about: debugging, diagnostics, measurement techniques
- Need: systematic debugging approach, common issues, solutions

---

## When to Use This Skill

- Implementing a new DAC driver for no-OS
- Configuring voltage or current output ranges
- Working with different DAC types (simple, standard, advanced)
- Implementing synchronous multi-channel updates (LDAC)
- Performing offset and gain calibration
- Generating waveforms (sine, triangle, arbitrary)
- Integrating DAC drivers with IIO framework
- Debugging DAC output issues

## DAC Overview

The no-OS framework includes **31 DAC drivers** supporting various output types.

### DAC Categories

**Simple DACs**:
- 1-2 channels, 12-16 bit resolution
- Direct voltage output, minimal configuration
- Examples: AD5421, AD5449
- Use: Basic waveform generation, control voltages

**Standard Multi-Channel DACs**:
- 2-16 channels, 12-20 bit resolution
- LDAC synchronization, daisy-chain capable
- Examples: AD5686, AD5766, AD5791, AD5754R
- Use: Multi-channel signal generation, synchronized outputs

**Advanced Programmable DACs**:
- 1-6 channels, 12-16 bit resolution
- Voltage AND current modes, slew rate control
- Diagnostic features, CRC/error detection
- Examples: AD5758, AD5460, AD3552R, AD5770R
- Use: Industrial control (4-20mA), precision instrumentation

### Key Architecture Patterns

- Descriptor-based device management
- Immediate vs synchronous update modes
- GPIO-controlled LDAC synchronization
- Voltage and current output configuration
- Offset/gain calibration support
- IIO integration layer

---

## Quick Reference

### Simple DAC (AD5449-like)

```c
#include "ad5449.h"

// Initialize
struct ad5449_dev *dev;
struct ad5449_init_param init = {
    .spi_init = &spi_init,
    .resolution = 12,
};
ret = ad5449_init(&dev, &init);

// Output voltage (immediate update)
ad5449_load_update_channel(dev, channel, code);

// Waveform generation
for (int i = 0; i < 4096; i++) {
    ad5449_load_update_channel(dev, 0, i);
    no_os_udelay(10);  // 100kHz update rate
}

// Cleanup
ad5449_remove(dev);
```

---

### Standard DAC with LDAC (AD5766-like)

```c
#include "ad5766.h"

// Initialize with LDAC support
struct ad5766_dev *dev;
struct ad5766_init_param init = {
    .spi_ip = &spi_init,
    .gpio_ldac_ip = &gpio_ldac_init,
    .daisy_chain_en = AD5766_DISABLE,
};
ret = ad5766_init(&dev, &init);

// Configure output spans
ret = ad5766_set_span(dev, ch, AD5766_M_10V_TO_P_10V);

// ASYNCHRONOUS: Immediate update (one channel)
ret = ad5766_write_update_register(dev, ch, code);

// SYNCHRONOUS: Glitch-free multi-channel update
ret = ad5766_write_register(dev, AD5766_DAC_0, code0);
ret = ad5766_write_register(dev, AD5766_DAC_1, code1);
ret = ad5766_write_register(dev, AD5766_DAC_2, code2);

// Trigger simultaneous update
uint16_t ldac_mask = AD5766_LDAC(0) | AD5766_LDAC(1) | AD5766_LDAC(2);
ret = ad5766_set_sw_ldac(dev, ldac_mask);

// Cleanup
ad5766_remove(dev);
```

---

### Advanced DAC (AD5758-like)

```c
#include "ad5758.h"

// Initialize
struct ad5758_dev *dev;
struct ad5758_init_param init = {
    .spi_ip = &spi_init,
};
ret = ad5758_init(&dev, &init);

// Enable internal reference
ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);

// Configure voltage output (0-10V)
ret = ad5758_set_out_range(dev, RANGE_0V_10V);

// Configure current output (4-20mA)
ret = ad5758_set_out_range(dev, RANGE_4mA_20mA);

// Enable slew rate control
ret = ad5758_slew_rate_config(dev,
                              AD5758_SR_EN,
                              AD5758_SR_STEP_64_CODES,
                              AD5758_SR_RATE_4_KHZ);

// Write DAC code
ret = ad5758_dac_input_write(dev, code);

// Cleanup
ad5758_remove(dev);
```

---

## Output Ranges

### Voltage Ranges

**Unipolar** (0V to positive):
- `RANGE_0V_5V` - 0V to 5V
- `RANGE_0V_10V` - 0V to 10V
- `RANGE_0V_12V` - 0V to 12V

**Bipolar** (negative to positive):
- `RANGE_M5V_5V` - -5V to +5V
- `RANGE_M10V_10V` - -10V to +10V

**Advanced Spans** (AD5766):
- `AD5766_M_10V_TO_P_10V` - -10V to +10V (most common)
- `AD5766_M_20V_TO_0V` - -20V to 0V
- `AD5766_M_12V_TO_P_14V` - -12V to +14V
- More asymmetric ranges available

### Current Ranges

**Standard Current**:
- `RANGE_0mA_20mA` - 0mA to 20mA
- `RANGE_4mA_20mA` - 4mA to 20mA (live-zero, industrial standard)
- `RANGE_0mA_24mA` - 0mA to 24mA
- `RANGE_M20mA_20mA` - -20mA to +20mA (bipolar)

**Setting Range**:
```c
// Voltage
ret = ad5758_set_out_range(dev, RANGE_0V_10V);

// Current (industrial control)
ret = ad5758_set_out_range(dev, RANGE_4mA_20mA);

// Per-channel span
ret = ad5766_set_span(dev, channel, AD5766_M_10V_TO_P_10V);
```

---

## Code to Voltage/Current Conversion

### Voltage Conversion

**Unipolar (0V to Vmax)**:
```
Vout = (Code / Full_Scale) × Vrange

Example: 16-bit, 0-10V range, code = 0x8000
Vout = (32768 / 65535) × 10V = 5.000V
```

**Bipolar (-Vmax to +Vmax)**:
```
Vout = ((Code / Full_Scale) - 0.5) × Vrange

Example: 16-bit, ±10V range, code = 0x8000
Vout = ((32768 / 65536) - 0.5) × 20V = 0.000V
```

### Current Conversion

**4-20mA Loop**:
```
Iout = 4mA + (Code / Full_Scale) × 16mA

Example: 16-bit, code = 0x8000
Iout = 4mA + (32768/65535) × 16mA = 12.0mA (50%)
```

---

## Update Modes

### Immediate (Asynchronous) Update

Output changes immediately when code written:

```c
// Simple DAC
ad5449_load_update_channel(dev, channel, code);

// Standard DAC (immediate mode)
ad5686_write_update_register(dev, channel, code);

// Advanced DAC
ad5758_dac_input_write(dev, code);
```

**Use when**: Single channel, fast updates, non-critical timing

### Synchronous (LDAC) Update

Multi-channel glitch-free updates:

```c
// Step 1: Write all channels (no output change)
ad5686_write_register(dev, AD5686_CH_0, code0);
ad5686_write_register(dev, AD5686_CH_1, code1);
ad5686_write_register(dev, AD5686_CH_2, code2);

// Step 2: Trigger simultaneous update
ad5686_update_register(dev, AD5686_CH_ALL);
```

**Use when**: Multi-channel waveforms, synchronized outputs, phase-aligned signals

---

## Common Patterns

### Pattern 1: Simple Voltage Output

```c
ret = ad5449_init(&dev, &init);

// Output 2.5V (midscale for 0-5V range, 12-bit)
ad5449_load_update_channel(dev, 0, 0x800);

ad5449_remove(dev);
```

### Pattern 2: Synchronized Multi-Channel

```c
ret = ad5766_init(&dev, &init);

// Configure channels
for (int ch = 0; ch < 4; ch++)
    ad5766_set_span(dev, ch, AD5766_M_10V_TO_P_10V);

// Write all channels
ad5766_write_register(dev, 0, code0);
ad5766_write_register(dev, 1, code1);
ad5766_write_register(dev, 2, code2);

// Simultaneous update
uint16_t ldac_mask = AD5766_LDAC(0) | AD5766_LDAC(1) | AD5766_LDAC(2);
ad5766_set_sw_ldac(dev, ldac_mask);

ad5766_remove(dev);
```

### Pattern 3: Industrial 4-20mA Current Loop

```c
ret = ad5758_init(&dev, &init);

// Configure for 4-20mA output
ret = ad5758_set_out_range(dev, RANGE_4mA_20mA);

// Enable slew rate for smooth transitions
ret = ad5758_slew_rate_config(dev, AD5758_SR_EN,
                              AD5758_SR_STEP_64_CODES,
                              AD5758_SR_RATE_4_KHZ);

// Sensor reading loop
while (1) {
    float sensor_percent = read_sensor();  // 0-100%
    uint16_t dac_code = (uint16_t)(sensor_percent * 0xFFFF / 100.0);
    
    ret = ad5758_dac_input_write(dev, dac_code);
    no_os_mdelay(100);  // 10Hz update
}

ad5758_remove(dev);
```

---

## Power Management

### Power Down Channels

```c
// AD5766: Bitmask for channels 0 and 1
uint16_t pwr_down = AD5766_PWDN(0) | AD5766_PWDN(1);
ret = ad5766_set_pwr_dac(dev, pwr_down);

// Power-down modes: Normal, 1kΩ to GND, 100kΩ to GND, Three-State
```

### Safe Startup (Clear Code)

```c
// Set safe state for CLR pin assertion
ret = ad5766_set_clr_span(dev, AD5766_MID, AD5766_M_10V_TO_P_10V);

// When CLR asserted: outputs go to 0V (midscale of ±10V)
```

---

## Debugging Quick Checks

### No Output or Zero Voltage

```c
// 1. Verify device ID (SPI working?)
uint32_t id;
ret = ad5758_reg_read(dev, AD5758_DEVICE_ID, &id);
pr_debug("Device ID: 0x%04X\n", id);

// 2. Check reference enabled
ret = ad5758_internal_buffers_en(dev, AD5758_EN_INT_REF);

// 3. Verify output range
ret = ad5758_set_out_range(dev, RANGE_0V_10V);

// 4. Write test code
ret = ad5758_dac_input_write(dev, 0x8000);  // Midscale
pr_info("Measure output - should be 5.0V for 0-10V range\n");
```

### Multi-Channel Glitches

```c
// DON'T: Causes glitches
ad5686_write_update_register(dev, 0, code0);  // Updates immediately
ad5686_write_update_register(dev, 1, code1);  // Different time
// Result: Channels update at different times

// DO: Glitch-free
ad5686_write_register(dev, 0, code0);  // No update yet
ad5686_write_register(dev, 1, code1);  // No update yet
ad5686_update_register(dev, AD5686_CH_ALL);  // Simultaneous
```

---

## Reference Drivers

**Recommended Study**:
- **AD5766**: 16-channel voltage DAC with advanced features
  - `drivers/dac/ad5766/ad5766.h`
- **AD5758**: Single-channel voltage/current with diagnostics
  - `drivers/dac/ad5758/ad5758.h`
- **AD5686**: Standard multi-channel family (SPI/I2C)
  - `drivers/dac/ad5686/ad5686.h`
- **AD3552R**: Modern high-speed DAC with CRC
  - `drivers/dac/ad3552r/iio_ad3552r.c` - IIO integration

**Project Examples**:
- `projects/*dac*/` - Complete application examples

---

## Reference Documentation

**When to read each file** (use Read tool):

### reference/implementation.md
Step-by-step driver implementation guide: architecture, API patterns, initialization order, error handling, resource management, reference drivers.

### reference/api-usage.md
Detailed API usage: output configuration (voltage/current ranges), update modes (immediate/LDAC), slew rate control, calibration, power management, daisy-chain, advanced features (dither, CRC, diagnostics), IIO integration.

### reference/waveform-generation.md
Signal generation patterns: common usage patterns, waveform examples (sine, triangle, sawtooth, square), multi-channel phase-shifted outputs, arbitrary waveform generation, performance optimization.

### reference/best-practices.md
Implementation best practices: initialization order, error handling, resource management, safe startup, multi-channel synchronization, output range configuration, calibration workflow, performance optimization, debugging, anti-patterns to avoid.

### reference/troubleshooting.md
Debugging guide: no output issues, wrong voltage problems, glitches during updates, slow settling, SPI communication errors, output noise, current loop issues, diagnostic tools and techniques.

---

## Summary

**Quick Start**:
1. Initialize DAC: `ad5xxx_init(&dev, &init)`
2. Configure range: `ad5xxx_set_out_range(dev, RANGE_0V_10V)`
3. Write code: `ad5xxx_dac_input_write(dev, code)`
4. Cleanup: `ad5xxx_remove(dev)`

**Key Concepts**:
- **Immediate update**: Fast, single-channel, output changes on write
- **Synchronous update**: Multi-channel, glitch-free, LDAC-triggered
- **Output ranges**: Voltage (unipolar/bipolar), Current (0-20mA, 4-20mA)
- **Slew rate**: Controlled transitions, reduces glitches/EMI

**Common Applications**:
- Simple waveform generation (simple DACs)
- Multi-channel synchronized signals (standard DACs)
- Industrial current loops 4-20mA (advanced DACs)
- Precision voltage sources with calibration

**When Stuck**:
- No output → Check reference voltage, output range, power-down status
- Wrong voltage → Verify range configuration, apply calibration
- Glitches → Use synchronous LDAC updates, not immediate
- Read reference/troubleshooting.md for systematic debugging

**Result**: Functional DAC driver with proper output configuration, synchronization, and error handling for signal generation and control applications.
