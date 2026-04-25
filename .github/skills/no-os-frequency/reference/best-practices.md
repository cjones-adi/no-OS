# Frequency Driver Best Practices

Guidelines and best practices for developing frequency synthesis drivers in the no-OS framework.

## Design Guidelines

### 1. Reference Clock Quality

The reference clock quality directly impacts output phase noise and jitter.

**Best practices**:
- Use low-jitter reference (TCXO, OCXO)
- Clean power supply for reference
- Keep reference traces short
- Shield from switching noise

**Reference quality hierarchy**:
1. **OCXO** (Oven-Controlled Crystal Oscillator) - Best
   - Phase noise: -170 dBc/Hz @ 10 kHz
   - Stability: ±0.1 ppm
   - Cost: High
   
2. **TCXO** (Temperature-Compensated Crystal Oscillator) - Good
   - Phase noise: -150 dBc/Hz @ 10 kHz
   - Stability: ±0.5 ppm
   - Cost: Medium
   
3. **Crystal** - Basic
   - Phase noise: -140 dBc/Hz @ 10 kHz
   - Stability: ±10 ppm
   - Cost: Low

### 2. PFD Frequency Optimization

Optimize phase frequency detector for best performance.

**Guidelines**:
- Typical range: 10-100 MHz
- Higher PFD = finer frequency resolution
- Lower R divider = lower phase noise
- Balance between resolution and noise

**Example**:
```c
// Good: PFD = 100 MHz (R = 1)
uint64_t ref_freq = 100000000;
uint8_t r_div = 1;  // No division
// PFD = 100 MHz (optimal)

// Acceptable: PFD = 50 MHz (R = 2)
uint64_t ref_freq = 100000000;
uint8_t r_div = 2;  // Divide by 2
// PFD = 50 MHz (still good)

// Poor: PFD = 10 MHz (R = 10)
uint64_t ref_freq = 100000000;
uint8_t r_div = 10;  // Divide by 10
// PFD = 10 MHz (higher phase noise)
```

### 3. Loop Filter Design

Follow datasheet recommendations for loop filter design.

**Best practices**:
- Follow datasheet loop filter calculator
- Bandwidth typically 1/10 of PFD frequency
- Type 2 or Type 3 filter for stability
- Use quality capacitors (C0G/NP0)

**Loop bandwidth calculation**:
```
Recommended Loop BW = PFD_freq / 10

Example:
  PFD = 100 MHz → Loop BW ≈ 10 MHz
  PFD = 50 MHz  → Loop BW ≈ 5 MHz
```

**Component selection**:
- Use C0G/NP0 capacitors (temperature stable)
- 1% resistors for accuracy
- Follow exact component values from datasheet calculator
- Do not substitute with "close enough" values

### 4. Integer-N When Possible

Use Integer-N mode when frequency allows.

**Why Integer-N is better**:
- Better phase noise than fractional-N
- Lower spurious content
- Faster lock time
- Use fractional-N only when resolution required

**Decision tree**:
```
Is Fout/Fref an integer?
├─ Yes → Use Integer-N PLL (ADF4153, ADF4156)
│         Better phase noise, lower cost
│
└─ No  → Is sub-Hz resolution needed?
          ├─ Yes → Use Fractional-N PLL (ADF4371, ADF4368)
          │         Higher phase noise, more flexible
          │
          └─ No  → Adjust reference frequency to make ratio integer
                   Or use clock distributor with dividers
```

### 5. VCO Selection

Operate VCO in optimal range.

**Best practices**:
- Operate VCO mid-band for best performance
- Avoid VCO edges where tuning gain varies
- Check VCO calibration after power-up

**Example**:
```c
// ADF4371 VCO range: 4-8 GHz
// Good: 6 GHz (mid-band)
ret = adf4371_set_frequency(dev, 6000000000ULL);

// Acceptable: 5 GHz or 7 GHz
ret = adf4371_set_frequency(dev, 5000000000ULL);

// Poor: 4.1 GHz or 7.9 GHz (near edges)
ret = adf4371_set_frequency(dev, 4100000000ULL);
```

### 6. Output Synchronization

Properly synchronize multi-output systems.

**Best practices**:
- Use SYNC mechanism for phase coherence
- Mute outputs during configuration
- Account for trace delay matching
- Verify phase relationship with scope

**Synchronization procedure**:
```c
// Step 1: Mute all outputs
ret = hmc7044_mute_all_outputs(dev, true);

// Step 2: Configure channels
for (int i = 0; i < num_channels; i++) {
    ret = hmc7044_set_output_frequency(dev, i, freq[i]);
    ret = hmc7044_set_phase_offset(dev, i, phase[i]);
}

// Step 3: Request synchronization
ret = hmc7044_request_sync(dev);
no_os_mdelay(1);

// Step 4: Unmute outputs
ret = hmc7044_mute_all_outputs(dev, false);

// Step 5: Verify lock
bool locked;
ret = hmc7044_get_lock_status(dev, &locked);
if (!locked) {
    pr_err("Sync failed - PLL not locked\n");
}
```

### 7. SYSREF Alignment (JESD204B)

Ensure proper SYSREF timing for JESD204B systems.

**Best practices**:
- SYSREF must meet setup/hold at all devices
- Account for clock distribution delays
- Use HMC7044 analog delay for fine tuning
- Verify with scope at receiver inputs

**SYSREF frequency selection**:
```c
// SYSREF = Device_clock / K (where K is integer)
// For 250 MHz device clock, K × Multiframe must be integer

// Good: K = 32 (SYSREF = 7.8125 MHz)
struct hmc7044_sysref_config sysref = {
    .divider = 32,  // 250 MHz / 32 = 7.8125 MHz
};

// Also good: K = 64 (SYSREF = 3.90625 MHz)
sysref.divider = 64;  // 250 MHz / 64 = 3.90625 MHz
```

### 8. Power Supply Filtering

Proper power supply filtering is critical.

**Best practices**:
- Separate analog and digital supplies
- Low-noise LDOs for sensitive supplies
- Ferrite beads for isolation
- Proper grounding and decoupling

**Decoupling network**:
```
VCC (3.3V) → [Ferrite Bead 100Ω@100MHz] → VCC_PLL
                                            ↓
                                     [10µF Bulk Tantalum]
                                            ↓
                                     [1µF X7R Ceramic]
                                            ↓
                                     [0.1µF X7R Ceramic] → IC Pin
                                            ↓
                                           GND

Place 0.1µF closest to IC pin (< 5mm)
```

## PCB Layout Guidelines

### Trace Routing

**Critical traces**:
1. **Reference clock** - Most critical
   - Controlled impedance (50Ω single-ended)
   - Shield with ground plane
   - Keep away from switching signals
   - Minimize stubs

2. **VCO output** - High frequency
   - Controlled impedance (50Ω)
   - Minimize trace length
   - Avoid vias when possible

3. **Loop filter** - Sensitive analog
   - Star ground configuration
   - Keep components close to IC
   - Shield from digital signals

### Ground Plane

**Best practices**:
- Solid ground plane under entire circuit
- Separate analog and digital grounds (connect at single point)
- No ground plane splits under sensitive traces
- VCO ground should be very low impedance

### Component Placement

**Guidelines**:
- Loop filter components: < 5mm from IC
- Decoupling capacitors: < 3mm from IC pins
- Reference oscillator: as close as possible to REF input
- Clock outputs: route to edge connectors with minimal vias

## Error Handling

### Lock Detection

Always verify PLL lock before use:

```c
// Check lock after frequency change
ret = adf4371_set_frequency(dev, target_freq);
if (ret < 0) {
    pr_err("Failed to set frequency: %d\n", ret);
    return ret;
}

// Wait for lock with timeout
ret = adf4371_wait_for_lock(dev, 100);  // 100ms timeout
if (ret < 0) {
    pr_err("PLL failed to lock\n");
    // Diagnostic information
    pr_info("Target freq: %llu Hz\n", target_freq);
    pr_info("VCO freq: %llu Hz\n", dev->vco_freq);
    pr_info("PFD freq: %u Hz\n", dev->clkin_freq / dev->ref_div_factor);
    return ret;
}
```

### VCO Calibration

Handle VCO calibration failures:

```c
// Trigger VCO calibration
ret = adf4371_calibrate_vco(dev);
if (ret < 0) {
    pr_err("VCO calibration failed\n");
    return ret;
}

// Wait for calibration with timeout
uint32_t timeout = 100;
while (timeout--) {
    bool cal_done;
    ret = adf4371_get_calibration_status(dev, &cal_done);
    if (cal_done) break;
    no_os_mdelay(1);
}

if (timeout == 0) {
    pr_err("VCO calibration timeout\n");
    return -ETIMEDOUT;
}

// Read and log VCO band
uint8_t vco_band;
ret = adf4371_get_vco_band(dev, &vco_band);
pr_info("VCO calibrated to band %d\n", vco_band);
```

### Reference Clock Monitoring

Monitor reference clock health:

```c
// Check reference clock present
bool ref_present;
ret = hmc7044_get_ref_status(dev, &ref_present);
if (!ref_present) {
    pr_err("Reference clock not detected\n");
    return -ENODEV;
}

// Enable reference auto-switch for redundancy
ret = hmc7044_enable_ref_auto_switch(dev, true);
```

## Performance Optimization

### Phase Noise Optimization

Minimize phase noise:

```c
// Settings for low phase noise
struct adf4371_init_param init = {
    .clkin_freq = 100000000,
    .ref_div = 1,              // Minimize R divider
    .ref_doubler_en = false,   // Avoid doubler noise
    .charge_pump_ua = 1250,    // Moderate CP current
};

// Use integer-N when possible
// Disable dithering if not needed
```

**Phase noise hierarchy**:
1. Best: Integer-N, R=1, quality reference
2. Good: Fractional-N, R=1, quality reference
3. Acceptable: Integer-N, R=2, TCXO
4. Poor: Fractional-N, R>2, crystal

### Lock Time Optimization

Minimize lock time for frequency hopping:

```c
// Pre-program frequency table
for (int i = 0; i < num_freqs; i++) {
    ret = adf4371_program_frequency_table(dev, i, freqs[i]);
}

// Fast hop (< 100µs) without recalculation
ret = adf4371_hop_to_frequency(dev, channel);

// For even faster hopping: increase charge pump current
// (trades lock time for phase noise)
ret = adf4371_set_charge_pump_current(dev, 5000);  // 5 mA
```

### Spurious Reduction

Minimize spurious content:

**Techniques**:
1. Use integer-N when possible
2. Optimize PFD frequency (avoid specific values)
3. Use higher order loop filter
4. Enable dithering in fractional-N mode (if available)
5. Avoid reference frequencies that create spurs

## Testing and Validation

### Power-Up Sequence

Proper power-up sequence:

```c
// 1. Apply power supplies
// 2. Assert reset (if available)
no_os_mdelay(10);

// 3. Release reset
// 4. Wait for power stable
no_os_mdelay(10);

// 5. Initialize device
ret = adf4371_init(&dev, &init_param);
if (ret < 0) return ret;

// 6. Wait for VCO calibration
ret = adf4371_wait_for_lock(dev, 100);
if (ret < 0) return ret;

// 7. Verify output frequency (use counter or spectrum analyzer)
```

### Functional Verification

Verify all features:

```c
// Test lock across frequency range
uint64_t test_freqs[] = {
    4000000000ULL,  // Low end
    6000000000ULL,  // Mid band
    8000000000ULL,  // High end
};

for (int i = 0; i < 3; i++) {
    ret = adf4371_set_frequency(dev, test_freqs[i]);
    TEST_ASSERT_EQUAL(0, ret);
    
    ret = adf4371_wait_for_lock(dev, 100);
    TEST_ASSERT_EQUAL(0, ret);
    
    pr_info("Locked at %llu Hz\n", test_freqs[i]);
}

// Test output power levels
for (int power = 0; power < 4; power++) {
    ret = adf4371_set_output_power(dev, power);
    TEST_ASSERT_EQUAL(0, ret);
}

// Test phase control
for (int phase = 0; phase < 4; phase++) {
    ret = ad9523_set_channel_phase(dev, 0, phase);
    TEST_ASSERT_EQUAL(0, ret);
}
```

### Performance Measurement

Measure key parameters:

**Phase noise**:
- Use spectrum analyzer with phase noise option
- Measure at 100 Hz, 1 kHz, 10 kHz, 100 kHz offsets
- Compare to datasheet specifications

**Spurious**:
- Full span spectrum analysis
- Identify spurs and their offset frequencies
- Should be < -60 dBc typically

**Lock time**:
- Measure time from frequency change to lock detect
- Should be < 50ms typically
- Verify across frequency range

**SYSREF timing** (JESD204B):
- Use oscilloscope to verify timing
- Check setup/hold margins at all receivers
- Verify alignment after power cycle

## Common Anti-Patterns

### Anti-Pattern 1: Ignoring Lock Status

**Bad**:
```c
// Set frequency and immediately use
ret = adf4371_set_frequency(dev, 5000000000ULL);
// Assume it worked - NO!
```

**Good**:
```c
// Set frequency and verify lock
ret = adf4371_set_frequency(dev, 5000000000ULL);
if (ret < 0) return ret;

ret = adf4371_wait_for_lock(dev, 100);
if (ret < 0) {
    pr_err("PLL failed to lock\n");
    return ret;
}
```

### Anti-Pattern 2: Poor Reference Quality

**Bad**:
```c
// Using noisy 3.3V system clock as reference
init.clkin_freq = 25000000;  // 25 MHz from MCU
```

**Good**:
```c
// Using dedicated TCXO
init.clkin_freq = 100000000;  // 100 MHz TCXO
```

### Anti-Pattern 3: Excessive R Divider

**Bad**:
```c
// High R divider increases phase noise
init.ref_div = 10;  // PFD = 10 MHz
```

**Good**:
```c
// Minimize R divider
init.ref_div = 1;   // PFD = 100 MHz
```

### Anti-Pattern 4: Skipping Synchronization

**Bad**:
```c
// Configure channels without synchronization
for (int i = 0; i < 4; i++) {
    hmc7044_set_output_frequency(dev, i, freq);
}
// Outputs may have random phase relationship
```

**Good**:
```c
// Proper synchronization
hmc7044_mute_all_outputs(dev, true);
for (int i = 0; i < 4; i++) {
    hmc7044_set_output_frequency(dev, i, freq);
}
hmc7044_request_sync(dev);
hmc7044_mute_all_outputs(dev, false);
```

### Anti-Pattern 5: Poor Error Handling

**Bad**:
```c
// Ignore return values
adf4371_init(&dev, &init_param);
adf4371_set_frequency(dev, freq);
```

**Good**:
```c
// Check all return values
ret = adf4371_init(&dev, &init_param);
if (ret < 0) {
    pr_err("Init failed: %d\n", ret);
    return ret;
}

ret = adf4371_set_frequency(dev, freq);
if (ret < 0) {
    pr_err("Set frequency failed: %d\n", ret);
    adf4371_remove(dev);
    return ret;
}
```
