# Frequency Driver Troubleshooting Guide

Diagnostic procedures and solutions for common frequency synthesis issues in the no-OS framework.

## Common Issues

### PLL Won't Lock

**Symptoms**:
- Lock detect pin stays low
- `adf4371_wait_for_lock()` times out
- Frequency unstable or incorrect

**Diagnostic procedure**:

```c
// Check lock status
bool locked;
ret = adf4371_get_lock_status(dev, &locked);
if (!locked) {
    // Diagnostic 1: Check reference clock
    pr_info("Reference freq: %llu Hz\n", dev->clkin_freq);
    // Verify reference is actually present with scope
    
    // Diagnostic 2: Check VCO frequency range
    pr_info("VCO freq: %llu Hz (valid: %llu - %llu)\n",
            dev->vco_freq, VCO_MIN, VCO_MAX);
    
    // Diagnostic 3: Verify R divider and PFD frequency
    uint32_t pfd_freq = dev->clkin_freq / dev->ref_div_factor;
    pr_info("PFD freq: %u Hz (recommended: 10-100 MHz)\n", pfd_freq);
    
    // Diagnostic 4: Check charge pump current
    pr_info("CP current: %u uA\n", dev->charge_pump_ua);
    
    // Diagnostic 5: Read VCO calibration status
    uint8_t vco_band;
    ret = adf4371_get_vco_band(dev, &vco_band);
    pr_info("VCO band: %d\n", vco_band);
}
```

**Common causes and solutions**:

1. **No reference clock**
   - Check reference oscillator power
   - Verify reference enable signal
   - Use scope to confirm clock present
   - Solution: Fix reference clock hardware

2. **VCO frequency out of range**
   - Check requested frequency
   - Verify output divider selection
   - Solution: Choose frequency within VCO range

3. **PFD frequency too low**
   - R divider too high
   - Reference frequency too low
   - Solution: Reduce R divider or increase reference frequency

4. **Loop filter incorrect**
   - Wrong component values
   - Poor PCB layout
   - Solution: Follow datasheet loop filter design exactly

5. **Charge pump current incorrect**
   - Too low for loop bandwidth
   - Too high causing instability
   - Solution: Use datasheet recommended value (typically 2.5 mA)

### Wrong Output Frequency

**Symptoms**:
- Output frequency doesn't match requested
- Frequency error > 1%

**Diagnostic procedure**:

```c
// Calculate and display PLL parameters
pr_info("Target freq: %llu Hz\n", target_freq);
pr_info("INT: %u, FRAC1: %u, FRAC2: %u, MOD2: %u\n",
        dev->integer, dev->fract1, dev->fract2, dev->mod2);
pr_info("R divider: %u\n", dev->ref_div_factor);

// Verify calculation
uint64_t calc_freq = (dev->clkin_freq *
    (dev->integer + ((double)dev->fract1 / (1 << 24)) +
     ((double)dev->frac2 / dev->mod2))) / dev->ref_div_factor;

pr_info("Calculated freq: %llu Hz (error: %lld Hz)\n",
        calc_freq, (int64_t)(calc_freq - target_freq));

// Check output divider
pr_info("Output divider: %u\n", dev->output_div);
uint64_t output_freq = calc_freq / dev->output_div;
pr_info("Output freq: %llu Hz\n", output_freq);
```

**Common causes and solutions**:

1. **Integer overflow in calculation**
   - Use 64-bit arithmetic
   - Solution: Ensure all frequency calculations use uint64_t

2. **Wrong output channel selected**
   - ADF4371 has RF8, RF16, RF32 outputs
   - Solution: Verify channel parameter matches desired output

3. **Reference frequency incorrect**
   - Wrong reference clock frequency in init parameters
   - Solution: Measure reference frequency, update init params

4. **Rounding errors**
   - Fractional-N has finite resolution
   - Solution: Accept small error or adjust reference frequency

### Poor Phase Noise

**Symptoms**:
- High phase noise measurement
- Degraded system performance

**Diagnostic procedure**:

```c
// Check settings affecting phase noise
pr_info("Reference divider: %u (lower is better)\n", dev->ref_div_factor);
pr_info("Fractional mode: %s (integer-N is cleaner)\n",
        (dev->fract1 || dev->fract2) ? "yes" : "no");

// Loop bandwidth should be ~1/10 of PFD freq
uint32_t pfd_freq = dev->clkin_freq / dev->ref_div_factor;
pr_info("PFD freq: %u Hz\n", pfd_freq);
pr_info("Recommended loop BW: ~%u Hz\n", pfd_freq / 10);

// Check reference quality
pr_info("Reference type: OCXO/TCXO/Crystal?\n");
pr_info("Using clean, low-noise reference clock?\n");
```

**Common causes and solutions**:

1. **High R divider**
   - Each doubling of R adds ~6 dB phase noise
   - Solution: Minimize R divider (ideally R=1)

2. **Fractional-N mode**
   - 10-15 dB worse than integer-N
   - Solution: Use integer-N when possible

3. **Poor reference quality**
   - Noisy reference propagates to output
   - Solution: Use TCXO or OCXO instead of crystal

4. **Loop bandwidth too high**
   - Amplifies VCO noise
   - Solution: Reduce loop bandwidth to ~PFD/10

5. **Poor power supply filtering**
   - Switching noise couples into PLL
   - Solution: Use LDOs and proper decoupling

6. **PCB layout issues**
   - Long traces, poor grounding
   - Solution: Follow PCB layout best practices

### SYSREF Timing Issues

**Symptoms**:
- JESD204B link fails to establish
- Data errors on JESD204B link
- Intermittent link failures

**Diagnostic procedure**:

```c
// Verify SYSREF configuration
struct hmc7044_sysref_config sysref;
ret = hmc7044_get_sysref_config(dev, &sysref);

pr_info("SYSREF enabled: %s\n", sysref.enable ? "yes" : "no");
pr_info("SYSREF mode: %d\n", sysref.mode);
pr_info("SYSREF divider: %u\n", sysref.divider);

uint32_t sysref_freq = output_freq / sysref.divider;
pr_info("SYSREF frequency: %u Hz\n", sysref_freq);

// Check SYSREF meets JESD204B requirements
// Typically: Fdevice_clock / N, where N is multiple of frames per multiframe
pr_info("Device clock: %u Hz\n", device_clock);
pr_info("Frames per multiframe (K): %u\n", k_value);
pr_info("Expected SYSREF: %u Hz\n", device_clock / (k_value * n));
```

**Common causes and solutions**:

1. **SYSREF frequency incorrect**
   - Must be submultiple of device clock / K
   - Solution: Set SYSREF = Device_clock / (K × N) where N is integer

2. **Setup/hold violations**
   - SYSREF arrives too close to clock edge
   - Solution: Use analog delay to adjust timing

3. **Trace delays not matched**
   - Clock and SYSREF arrive at different times
   - Solution: Match PCB trace lengths or add delay compensation

4. **SYSREF mode incorrect**
   - Continuous mode used in production
   - Solution: Use one-shot mode after initial link setup

5. **Multiple SYSREF sources**
   - Phase relationship not maintained
   - Solution: Use single SYSREF distributor for all devices

**Scope verification**:
```
1. Trigger on SYSREF rising edge
2. Measure device clock phase at SYSREF edge
3. Verify setup time > 1 ns
4. Verify hold time > 1 ns
5. Check at all receiver inputs
```

### Spurious Content

**Symptoms**:
- Unwanted frequency components in output spectrum
- Spurs at specific offsets from carrier

**Diagnostic procedure**:

```c
// Identify spur type and offset
pr_info("Spur offset: %u Hz\n", spur_offset);

// Check for reference spurs
uint32_t ref_freq = dev->clkin_freq;
pr_info("Reference freq: %u Hz\n", ref_freq);
if (spur_offset % ref_freq == 0) {
    pr_warn("Reference spur at %dx Fref\n", spur_offset / ref_freq);
}

// Check for fractional spurs
uint32_t pfd_freq = ref_freq / dev->ref_div_factor;
pr_info("PFD freq: %u Hz\n", pfd_freq);
if (dev->fract1 || dev->fract2) {
    pr_warn("Fractional mode - expect some spurs\n");
}

// Check for integer boundary spurs
if (dev->integer == 16 || dev->integer == 32 || dev->integer == 64) {
    pr_warn("Integer value at power of 2 boundary - may cause spurs\n");
}
```

**Common causes and solutions**:

1. **Reference spurs**
   - Appear at multiples of reference frequency
   - Solution: Use higher order loop filter

2. **Fractional spurs**
   - Inherent to fractional-N PLLs
   - Solution: Enable dithering (if available) or use integer-N

3. **PFD spurs**
   - At PFD frequency offset
   - Solution: Increase PFD frequency or improve loop filter

4. **Charge pump leakage**
   - DC offset causes spurs
   - Solution: Verify charge pump current setting

5. **Power supply noise**
   - Switching frequency couples into PLL
   - Solution: Improve power supply filtering

### Lock Time Too Long

**Symptoms**:
- PLL takes > 50ms to lock
- Frequency hopping slow

**Diagnostic procedure**:

```c
// Measure lock time
uint32_t start_time = no_os_get_time_ms();

ret = adf4371_set_frequency(dev, target_freq);
ret = adf4371_wait_for_lock(dev, 1000);

uint32_t lock_time = no_os_get_time_ms() - start_time;
pr_info("Lock time: %u ms\n", lock_time);

// Check parameters affecting lock time
pr_info("Loop bandwidth: ~%u Hz\n", pfd_freq / 10);
pr_info("CP current: %u uA\n", dev->charge_pump_ua);
pr_info("Frequency step: %llu Hz\n", 
        (int64_t)(target_freq - dev->vco_freq));
```

**Common causes and solutions**:

1. **Loop bandwidth too low**
   - Small loop BW = slow settling
   - Solution: Increase loop bandwidth (higher CP current)

2. **Large frequency step**
   - VCO calibration takes time
   - Solution: Use frequency hopping with pre-programmed values

3. **Charge pump current too low**
   - Slow loop response
   - Solution: Increase CP current (trades phase noise for speed)

4. **VCO calibration enabled**
   - Adds calibration time to lock time
   - Solution: Disable auto-calibration for fast hopping

**Fast hopping optimization**:
```c
// Pre-program frequency table
for (int i = 0; i < num_freqs; i++) {
    ret = adf4371_program_frequency_table(dev, i, freqs[i]);
}

// Fast hop without recalculation (< 100µs)
ret = adf4371_hop_to_frequency(dev, channel);
```

### Temperature Drift

**Symptoms**:
- Frequency changes with temperature
- Phase noise degrades at temperature extremes

**Diagnostic procedure**:

```c
// Monitor temperature
int16_t die_temp;
ret = hmc7044_get_die_temperature(dev, &die_temp);
pr_info("Die temperature: %d C\n", die_temp);

// Check reference stability
pr_info("Reference type: %s\n", ref_type);
// OCXO: ±0.1 ppm
// TCXO: ±0.5 ppm
// Crystal: ±10 ppm

// Calculate expected drift
double ppm_drift = temp_coefficient * (die_temp - 25);
uint64_t freq_drift = (dev->vco_freq * ppm_drift) / 1000000;
pr_info("Expected drift: %llu Hz (%.2f ppm)\n", freq_drift, ppm_drift);
```

**Common causes and solutions**:

1. **Reference drift**
   - Crystal has poor temperature stability
   - Solution: Use TCXO or OCXO

2. **VCO temperature coefficient**
   - VCO frequency changes with temp
   - Solution: Use temperature compensation (if available)

3. **Loop filter components**
   - Capacitor values change with temp
   - Solution: Use C0G/NP0 temperature-stable capacitors

4. **Operating beyond spec**
   - Outside rated temperature range
   - Solution: Add thermal management

### Multiple Outputs Not Synchronized

**Symptoms**:
- Random phase relationship between outputs
- Phase changes after power cycle

**Diagnostic procedure**:

```c
// Check synchronization status
bool sync_done;
ret = hmc7044_get_sync_status(dev, &sync_done);
pr_info("Sync completed: %s\n", sync_done ? "yes" : "no");

// Verify all channels configured
for (int ch = 0; ch < num_channels; ch++) {
    bool enabled;
    ret = hmc7044_get_output_enable(dev, ch, &enabled);
    pr_info("Channel %d enabled: %s\n", ch, enabled ? "yes" : "no");
}

// Check lock status
bool locked;
ret = hmc7044_get_lock_status(dev, &locked);
pr_info("PLL locked: %s\n", locked ? "yes" : "no");
```

**Common causes and solutions**:

1. **Synchronization not requested**
   - Forgot to call sync function
   - Solution: Call `hmc7044_request_sync()` after configuration

2. **Outputs not muted during setup**
   - Configuration changes affect running outputs
   - Solution: Mute outputs, configure, sync, then unmute

3. **PLL not locked during sync**
   - Sync request ignored if not locked
   - Solution: Verify lock before requesting sync

4. **Power-up sequence incorrect**
   - Random initial phase
   - Solution: Follow proper power-up and sync sequence

**Proper synchronization sequence**:
```c
// 1. Mute outputs
ret = hmc7044_mute_all_outputs(dev, true);

// 2. Configure all channels
for (int i = 0; i < num_channels; i++) {
    ret = hmc7044_set_output_frequency(dev, i, freq[i]);
    ret = hmc7044_set_phase_offset(dev, i, phase[i]);
}

// 3. Wait for lock
ret = hmc7044_wait_for_lock(dev, 100);

// 4. Request sync
ret = hmc7044_request_sync(dev);
no_os_mdelay(1);

// 5. Verify sync
ret = hmc7044_get_sync_status(dev, &sync_done);
if (!sync_done) {
    pr_err("Sync failed\n");
}

// 6. Unmute outputs
ret = hmc7044_mute_all_outputs(dev, false);
```

## Hardware Issues

### Reference Clock Problems

**Symptoms**:
- No PLL lock
- Intermittent lock
- Frequency instability

**Checks**:
1. **Measure reference clock with scope**
   - Verify frequency
   - Check amplitude (should be 0.5V to 1.5V typically)
   - Look for noise or ringing

2. **Check reference oscillator power**
   - Verify supply voltage
   - Check enable signal (if present)

3. **Inspect PCB**
   - No broken traces
   - Clean solder joints
   - No shorts to ground

### Loop Filter Issues

**Symptoms**:
- Won't lock
- Slow lock time
- High phase noise

**Checks**:
1. **Verify component values**
   - Use datasheet loop filter calculator
   - Measure actual capacitor/resistor values
   - Check for correct component types (C0G/NP0)

2. **Check PCB layout**
   - Components close to IC (< 5mm)
   - Star ground configuration
   - No coupling to digital signals

3. **Measure voltages**
   - Charge pump voltage should be ~Vcc/2
   - No AC coupling on scope

### Power Supply Issues

**Symptoms**:
- Poor phase noise
- Spurious content
- Intermittent operation

**Checks**:
1. **Measure supply voltage**
   - Within ±5% of nominal
   - Low ripple (< 10 mV)
   - Fast transient response

2. **Check decoupling**
   - Capacitors close to IC pins
   - Multiple values (0.1µF, 1µF, 10µF)
   - Low ESR capacitors

3. **Verify grounding**
   - Solid ground plane
   - No ground loops
   - Single point ground for analog/digital

### PCB Layout Issues

**Symptoms**:
- Poor phase noise
- Spurious content
- EMI/EMC failures

**Checks**:
1. **Reference clock trace**
   - Controlled impedance (50Ω)
   - Shielded with ground
   - Short as possible
   - No vias or stubs

2. **VCO output trace**
   - Controlled impedance
   - Minimize length
   - Avoid sharp corners

3. **Loop filter routing**
   - Star ground
   - Components close to IC
   - Shield from digital signals

## Debugging Tools

### Software Tools

**Enable debug output**:
```c
// Enable verbose logging
#define DEBUG_FREQUENCY 1

#ifdef DEBUG_FREQUENCY
#define freq_dbg(fmt, ...) pr_info("[FREQ] " fmt, ##__VA_ARGS__)
#else
#define freq_dbg(fmt, ...)
#endif

// Use in driver code
freq_dbg("Setting frequency to %llu Hz\n", target_freq);
freq_dbg("INT=%u, FRAC1=%u, FRAC2=%u\n", integer, frac1, frac2);
```

**Register dump**:
```c
// Dump all registers for analysis
void adf4371_reg_dump(struct adf4371_dev *dev)
{
    uint8_t reg_val;
    
    pr_info("ADF4371 Register Dump:\n");
    for (int addr = 0; addr < 0x80; addr++) {
        ret = adf4371_spi_read(dev, addr, &reg_val);
        if (ret == 0) {
            pr_info("  Reg 0x%02X = 0x%02X\n", addr, reg_val);
        }
    }
}
```

### Hardware Tools

**Essential tools**:
1. **Oscilloscope** (> 1 GHz bandwidth)
   - Measure reference clock
   - Verify lock detect signal
   - Check SYSREF timing
   - Measure phase relationships

2. **Spectrum Analyzer**
   - Measure output frequency
   - Identify spurious content
   - Measure harmonic distortion
   - Phase noise measurements (with option)

3. **Frequency Counter**
   - Accurate frequency measurement
   - Stability over time
   - Temperature drift

4. **Logic Analyzer**
   - SPI communication debug
   - Digital control signals
   - Timing analysis

**Measurement techniques**:
```
1. Lock detect verification:
   - Scope probe on LD pin
   - Should be high when locked
   - Should go low when frequency changed
   - Should return high after lock time

2. Reference clock quality:
   - Scope AC coupled to REF input
   - Measure peak-to-peak voltage
   - Check for overshoot/ringing
   - FFT to check for spurs

3. Output spectrum:
   - Spectrum analyzer on output
   - Center on carrier frequency
   - Span ±10 MHz for close-in spurs
   - Span to DC for reference spurs
   - Marker on peak for power measurement

4. Phase noise:
   - Spectrum analyzer with phase noise option
   - Measure at 100 Hz, 1 kHz, 10 kHz, 100 kHz
   - Compare to datasheet typical values
```

## Error Code Reference

Common return codes and meanings:

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 0 | Success | - |
| -EINVAL | Invalid parameter | NULL pointer, out of range value |
| -ENODEV | Device not found | SPI communication failure, wrong chip ID |
| -EIO | I/O error | SPI read/write failure |
| -ETIMEDOUT | Timeout | Lock timeout, VCO cal timeout |
| -EBUSY | Device busy | Operation in progress |
| -ENOMEM | Out of memory | Malloc failure |

**Example error handling**:
```c
ret = adf4371_set_frequency(dev, freq);
switch (ret) {
case 0:
    pr_info("Frequency set successfully\n");
    break;
case -EINVAL:
    pr_err("Invalid frequency: %llu Hz\n", freq);
    break;
case -ETIMEDOUT:
    pr_err("PLL lock timeout\n");
    // Run diagnostics
    break;
case -EIO:
    pr_err("SPI communication error\n");
    // Check SPI bus
    break;
default:
    pr_err("Unknown error: %d\n", ret);
    break;
}
```
