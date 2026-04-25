---
name: no-os-frequency
description: 'Complete guide to no-OS frequency synthesis and clock generation drivers. Covers fractional-N PLLs, integer-N PLLs, VCOs, clock distributors, dividers, phase control, lock detection, SYSREF generation, and multi-output synchronization.'
triggers:
  - "frequency"
  - "pll"
  - "synthesizer"
  - "clock"
  - "vco"
  - "adf"
  - "hmc"
  - "ad9"
  - "sysref"
alwaysInclude: false
---

# no-OS Frequency Synthesis Driver Development Guide

Quick-start guide for developing and working with frequency synthesis and clock generation drivers in the no-OS framework.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "device architecture", "PLL types", "structure definition"
- Mentions: device descriptor, init parameters, fractional-N, integer-N, clock distributor
- Questions about: VCO calibration, temperature compensation, phase noise optimization
- Need: IIO integration patterns, device type comparison

**Triggers to read reference/api-usage.md**:
- User asks: "how to use", "API examples", "code examples", "typical usage"
- Mentions: set frequency, configure channels, phase control, lock detection
- Questions about: SYSREF generation, synchronization, modulation, frequency hopping
- Need: Complete function examples, use case implementations

**Triggers to read reference/configuration.md**:
- User asks: "how to configure", "setup", "initialization", "parameters"
- Mentions: reference clock, PFD frequency, loop filter, charge pump
- Questions about: driver modes, SYSREF timing, phase adjustment, power supply
- Need: Configuration guidelines, parameter selection, initialization examples

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "guidelines", "recommendations", "optimization"
- Mentions: phase noise, lock time, PCB layout, power supply
- Questions about: reference quality, error handling, testing, anti-patterns
- Need: Design guidelines, performance optimization, validation procedures

**Triggers to read reference/troubleshooting.md**:
- User says: "not working", "error", "problem", "issue", "fails"
- Mentions: won't lock, wrong frequency, poor phase noise, spurs, SYSREF issues
- Questions about: debugging, diagnostics, hardware problems
- Need: Diagnostic procedures, common causes, solutions, measurement techniques

---

## When to Use This Skill

- Implementing frequency synthesis drivers (PLLs, VCOs, clock distributors)
- Configuring multi-output clock distribution systems
- Setting up JESD204B SYSREF generation
- Phase control and output synchronization
- Lock detection and PLL troubleshooting
- Optimizing phase noise and spurious performance
- Fast frequency hopping applications

## Frequency Synthesis Overview

### Device Types

**Fractional-N PLLs** (ADF4371, ADF4368, ADF5610)
- Precise frequency synthesis (sub-Hz resolution)
- Wide output range (typically GHz)
- Higher phase noise than integer-N
- Use when flexible frequency selection needed

**Integer-N PLLs** (ADF4153, ADF4156)
- Better phase noise performance
- Faster lock time
- Coarser frequency resolution
- Use when frequency is integer multiple of reference

**Clock Distributors** (AD9523, HMC7044, LTC6953)
- Multiple synchronized outputs (up to 14 channels)
- Programmable dividers per channel
- SYSREF generation for JESD204B
- Phase control and delay adjustment

**VCOs** (Voltage Controlled Oscillators)
- Direct frequency control
- Custom PLL designs
- Wide tuning range

### PLL Block Diagram

```
Reference → [÷R] → [PFD] → [Charge Pump] → [Loop Filter] → [VCO] → Output
  (Fref)             ↑                                         ↓
                     └─────────── [÷N] ←──────────────────────┘
                              (Feedback)

Frequency Equation:
  Fout = Fref × (N / R)

For fractional-N:
  Fout = Fref × ((INT + (FRAC1 + FRAC2/MOD2)) / R)
```

---

## Quick Reference

### Driver Locations

```
drivers/frequency/
├── adf4371/          # Wideband fractional-N PLL (62.5 MHz - 8 GHz)
├── adf4368/          # Microwave synthesizer (800 MHz - 12.8 GHz)
├── adf4153/          # Integer-N PLL (500 MHz - 4 GHz)
├── ad9523/           # 14-channel clock distributor
├── hmc7044/          # 14-output clock fanout buffer
└── ltc6953/          # Ultralow jitter clock distributor
```

### Key Header Files

```c
#include "drivers/frequency/adf4371/adf4371.h"    // Fractional-N PLL
#include "drivers/frequency/ad9523/ad9523.h"      // Clock distributor
#include "drivers/frequency/hmc7044/hmc7044.h"    // Multi-output fanout
```

### Typical API Functions

```c
// Fractional-N PLL (ADF4371)
int adf4371_init(struct adf4371_dev **device, struct adf4371_init_param *init);
int adf4371_set_frequency(struct adf4371_dev *dev, uint64_t freq);
int adf4371_wait_for_lock(struct adf4371_dev *dev, uint32_t timeout_ms);
int adf4371_remove(struct adf4371_dev *dev);

// Clock Distributor (AD9523)
int ad9523_init(struct ad9523_dev **device, struct ad9523_init_param *init);
int ad9523_setup_channel(struct ad9523_dev *dev, uint8_t ch, struct ad9523_channel_spec *spec);
int ad9523_sync_outputs(struct ad9523_dev *dev);
int ad9523_remove(struct ad9523_dev *dev);

// Multi-Output Fanout (HMC7044)
int hmc7044_init(struct hmc7044_dev **device, struct hmc7044_init_param *init);
int hmc7044_set_output_frequency(struct hmc7044_dev *dev, uint8_t ch, uint32_t freq);
int hmc7044_configure_sysref(struct hmc7044_dev *dev, struct hmc7044_sysref_config *cfg);
int hmc7044_request_sync(struct hmc7044_dev *dev);
```

---

## Essential Usage Examples

### Simple Frequency Synthesizer

```c
// Initialize ADF4371 for 5.6 GHz output
struct adf4371_dev *pll;
struct adf4371_init_param init = {
    .spi_init = {
        .device_id = 0,
        .max_speed_hz = 1000000,
        .mode = NO_OS_SPI_MODE_0,
        .chip_select = 0,
    },
    .clkin_freq = 100000000,       // 100 MHz reference
    .target_freq = 5600000000,     // 5.6 GHz output
    .channel = ADF4371_CH_RF8,     // RF8 output
    .ref_div = 1,                  // No reference division
    .charge_pump_ua = 2500,        // 2.5 mA CP current
};

ret = adf4371_init(&pll, &init);
if (ret < 0) {
    pr_err("Init failed: %d\n", ret);
    return ret;
}

// Wait for lock
ret = adf4371_wait_for_lock(pll, 100);
if (ret == 0) {
    pr_info("PLL locked at %llu Hz\n", pll->vco_freq / 8);
}
```

### Multi-Channel Clock Distribution

```c
// AD9523 distributing clocks for JESD204B system
struct ad9523_dev *clk_dist;

// Configure channels
struct ad9523_channel_spec channels[] = {
    { 0, 2, AD9523_DRIVER_LVDS, true },   // ADC0: 250 MHz
    { 1, 2, AD9523_DRIVER_LVDS, true },   // ADC1: 250 MHz
    { 4, 2, AD9523_DRIVER_LVDS, true },   // DAC0: 250 MHz
    { 13, 64, AD9523_DRIVER_CMOS, true }, // SYSREF: 7.8125 MHz
};

struct ad9523_init_param init = {
    .channels = channels,
    .num_channels = 4,
    .vcxo_freq = 500000000,  // 500 MHz VCXO
};

ret = ad9523_init(&clk_dist, &init);

// Synchronize all outputs
ret = ad9523_sync_outputs(clk_dist);
```

### SYSREF Configuration (JESD204B)

```c
// Configure SYSREF for JESD204B subclass 1
struct hmc7044_sysref_config sysref = {
    .enable = true,
    .mode = HMC7044_SYSREF_ONESHOT,  // One-shot mode
    .divider = 32,                   // SYSREF = 250 MHz / 32 = 7.8125 MHz
    .pulse_gen_mode = HMC7044_PULSE_GEN_POS_EDGE,
};

ret = hmc7044_configure_sysref(dev, &sysref);

// Trigger SYSREF pulse
ret = hmc7044_request_sysref(dev);
```

### Phase-Synchronized Multi-Output

```c
// HMC7044 with phase control
struct hmc7044_dev *fanout;

// Configure 4 channels with phase offsets
for (int ch = 0; ch < 4; ch++) {
    // Set frequency
    ret = hmc7044_set_output_frequency(fanout, ch, 10000000000);
    
    // Set phase offset (each ~25ps step)
    uint16_t phase = ch * 100;
    ret = hmc7044_set_phase_offset(fanout, ch, phase);
}

// Synchronize all outputs
ret = hmc7044_request_sync(fanout);
```

---

## Common Operations

### Lock Detection

Always verify PLL lock:

```c
// Check lock status
bool locked;
ret = adf4371_get_lock_status(dev, &locked);
if (!locked) {
    pr_warn("PLL not locked\n");
}

// Wait for lock with timeout
ret = adf4371_wait_for_lock(dev, 100);  // 100ms timeout
if (ret < 0) {
    pr_err("Lock timeout\n");
}
```

### Frequency Change

```c
// Set new frequency
uint64_t target_freq = 6000000000ULL;  // 6 GHz
ret = adf4371_set_frequency(dev, target_freq);
if (ret < 0) return ret;

// Verify lock
ret = adf4371_wait_for_lock(dev, 100);
```

### Output Synchronization

Proper synchronization procedure:

```c
// 1. Mute outputs during configuration
ret = hmc7044_mute_all_outputs(dev, true);

// 2. Configure all channels
for (int i = 0; i < num_channels; i++) {
    ret = hmc7044_set_output_frequency(dev, i, freq[i]);
    ret = hmc7044_set_phase_offset(dev, i, phase[i]);
}

// 3. Request synchronization
ret = hmc7044_request_sync(dev);
no_os_mdelay(1);

// 4. Unmute outputs
ret = hmc7044_mute_all_outputs(dev, false);

// 5. Verify lock
bool locked;
ret = hmc7044_get_lock_status(dev, &locked);
```

---

## Key Design Guidelines

### Reference Clock Quality

Critical for overall performance:
- Use TCXO or OCXO for best phase noise
- Clean power supply for reference
- Keep reference traces short and shielded
- Minimize R divider (ideally R=1)

### PFD Frequency Optimization

Phase Frequency Detector frequency affects resolution and noise:
- Typical range: 10-100 MHz
- Higher PFD = finer frequency resolution
- Lower R divider = lower phase noise
- Recommended: 50-100 MHz for best performance

### Integer-N vs Fractional-N

Choose wisely for best performance:
- **Integer-N**: Better phase noise, faster lock, use when possible
- **Fractional-N**: Sub-Hz resolution, more flexible, higher phase noise

### Loop Filter Design

Follow datasheet recommendations:
- Use datasheet loop filter calculator
- Bandwidth typically 1/10 of PFD frequency
- Use C0G/NP0 capacitors (temperature stable)
- Place components close to IC (< 5mm)

### SYSREF Requirements (JESD204B)

- SYSREF = Device_clock / (K × N) where K is frames per multiframe
- Must meet setup/hold timing at all receivers
- Account for PCB trace delays
- Use analog delay for fine tuning

---

## Common Issues - Quick Fixes

### PLL Won't Lock

Check these in order:
1. Verify reference clock present (use scope)
2. Check VCO frequency in valid range
3. Verify PFD frequency 10-100 MHz
4. Check loop filter component values
5. Verify charge pump current setting

**Diagnostic**:
```c
pr_info("Reference: %llu Hz\n", dev->clkin_freq);
pr_info("VCO: %llu Hz\n", dev->vco_freq);
pr_info("PFD: %u Hz\n", dev->clkin_freq / dev->ref_div_factor);
```

### Wrong Output Frequency

Verify calculation:
```c
pr_info("Target: %llu Hz\n", target_freq);
pr_info("INT=%u, FRAC1=%u, R=%u\n", dev->integer, dev->fract1, dev->ref_div_factor);
```

Common causes: Wrong reference frequency, incorrect output channel, integer overflow

### Poor Phase Noise

Improve with:
1. Use Integer-N instead of Fractional-N
2. Minimize R divider (R=1 best)
3. Use quality reference (TCXO/OCXO)
4. Reduce loop bandwidth
5. Improve power supply filtering

### SYSREF Timing Issues

1. Verify SYSREF frequency = Device_clock / (K × N)
2. Check setup/hold timing with scope
3. Match PCB trace lengths for clock and SYSREF
4. Use analog delay compensation

---

## Reference Documentation

**When to read each file** (use Read tool):

### reference/implementation.md
Device architecture patterns, PLL fundamentals, VCO calibration, temperature compensation, phase noise optimization, IIO integration examples.

### reference/api-usage.md
Complete usage examples: frequency setting, clock distribution, phase control, synchronization, lock detection, modulation, frequency hopping, all use cases.

### reference/configuration.md
Configuration reference: reference clock quality, PFD optimization, loop filter design, VCO selection, driver modes, SYSREF setup, power supply filtering, initialization examples.

### reference/best-practices.md
Design guidelines: reference clock quality, PFD optimization, loop filter design, Integer-N selection, VCO operation, PCB layout, error handling, performance optimization, anti-patterns.

### reference/troubleshooting.md
Diagnostic procedures and solutions: PLL won't lock, wrong frequency, poor phase noise, spurious content, SYSREF issues, lock time, temperature drift, synchronization problems, hardware debugging.

---

## Key Takeaways

- **Always verify lock** - Check lock status before using PLL output
- **Use Integer-N when possible** - Better phase noise than Fractional-N
- **Minimize R divider** - Lower phase noise with R=1
- **Quality reference clock** - TCXO/OCXO for best performance
- **Synchronize properly** - Mute, configure, sync, unmute sequence
- **Follow datasheet** - Loop filter design is critical
- **Read reference docs** - Complete details available when needed

**Workflow**: Initialize → Set frequency → Verify lock → Configure outputs → Synchronize → Measure performance

**Result**: High-performance frequency synthesis with low phase noise, precise frequency control, and synchronized multi-output operation for JESD204B and other applications.
