# Frequency Configuration Guide

Complete configuration reference for frequency synthesis drivers in the no-OS framework.

## Driver Locations

All frequency synthesis devices are located in:
- `drivers/frequency/` - All frequency synthesis devices

## Key Header Files

```c
#include "drivers/frequency/adf4371/adf4371.h"    // Wideband fractional-N PLL
#include "drivers/frequency/ad9523/ad9523.h"      // Multi-output clock distributor
#include "drivers/frequency/adf4368/adf4368.h"    // Microwave synthesizer
#include "drivers/frequency/hmc7044/hmc7044.h"    // 14-output clock fanout buffer
#include "drivers/frequency/ltc6953/ltc6953.h"    // Ultralow jitter clock distributor
```

## PLL Configuration Parameters

### Reference Clock Quality

Critical for overall system performance:

**Reference clock types** (in order of quality):
1. **OCXO** (Oven-Controlled Crystal Oscillator) - Best stability and phase noise
2. **TCXO** (Temperature-Compensated Crystal Oscillator) - Good stability
3. **Crystal** - Basic oscillator
4. **External clock** - Quality depends on source

**Requirements**:
- Use low-jitter reference (TCXO, OCXO)
- Clean power supply for reference
- Keep reference traces short
- Shield from switching noise

### PFD Frequency Optimization

Phase Frequency Detector frequency affects resolution and noise:

**Guidelines**:
- Typical range: 10-100 MHz
- Higher PFD = finer frequency resolution
- Lower R divider = lower phase noise
- Balance between resolution and noise

**PFD calculation**:
```
PFD_freq = (input_freq × ref_doubler) / R_divider

Recommended: 50-100 MHz for best performance
```

### Loop Filter Design

External passive filter for PLL stability:

**Guidelines**:
- Follow datasheet loop filter calculator
- Bandwidth typically 1/10 of PFD frequency
- Type 2 or Type 3 filter for stability
- Use quality capacitors (C0G/NP0)

**Loop bandwidth calculation**:
```
Loop_BW ≈ PFD_freq / 10

Example:
  PFD = 100 MHz → Loop BW ≈ 10 MHz
  PFD = 50 MHz  → Loop BW ≈ 5 MHz
```

### VCO Selection

Voltage-Controlled Oscillator operating point:

**Best practices**:
- Operate VCO mid-band for best performance
- Avoid VCO edges where tuning gain varies
- Check VCO calibration after power-up

**VCO frequency ranges** (device-specific):
```
ADF4371: 4 - 8 GHz VCO
ADF4368: 6.4 - 12.8 GHz VCO
ADF4153: 2.05 - 4.1 GHz VCO
```

### Integer-N vs Fractional-N Selection

Choose based on requirements:

**Integer-N PLLs**:
- Better phase noise than fractional-N
- Lower spurious content
- Faster lock time
- Use fractional-N only when resolution required

**Fractional-N PLLs**:
- Sub-Hz frequency resolution
- More flexible frequency selection
- Higher phase noise
- Required for non-integer frequency ratios

**When to use each**:
```c
// Use Integer-N when possible (exact ratio)
// Fout = 2.4 GHz, Fref = 10 MHz → N = 240 (integer)
ret = adf4153_set_frequency(dev, 10000000, 240, 1);

// Use Fractional-N when needed (non-integer ratio)
// Fout = 2.4123 GHz, Fref = 10 MHz → N = 241.23 (fractional)
ret = adf4371_set_frequency(dev, 2412300000ULL);
```

## Clock Distribution Configuration

### Multi-Output Channel Setup

Configure multiple synchronized outputs:

**Channel parameters**:
- Channel number (0-13 depending on device)
- Divider value (power of 2 or any integer, device-specific)
- Driver mode (LVDS, LVPECL, HSTL, CMOS)
- Enable/disable state

**Example configuration**:
```c
struct ad9523_channel_spec channel = {
    .channel_num = 0,           // Channel 0
    .channel_divider = 2,       // Divide by 2
    .driver_mode = AD9523_DRIVER_LVDS,
    .output_enable = true,
};
```

### Output Driver Types

Different electrical standards for output drivers:

**LVDS** (Low-Voltage Differential Signaling):
- 350 mV differential swing
- Low EMI
- Good for high-speed clocks
- Low power consumption

**LVPECL** (Low-Voltage Positive Emitter-Coupled Logic):
- 800 mV differential swing
- Higher swing than LVDS
- Better noise immunity
- More power consumption

**HSTL** (High-Speed Transceiver Logic):
- Single-ended signaling
- FPGA-compatible
- Moderate speed

**CMOS**:
- Rail-to-rail swing
- Simple interfacing
- Lower speeds
- SYSREF applications

### SYSREF Configuration

For JESD204B systems:

**SYSREF modes**:
- **Continuous**: SYSREF runs continuously (easier debug)
- **One-shot**: Single SYSREF pulse on request (normal operation)
- **N-shot**: Multiple pulses on request

**SYSREF requirements**:
- Frequency = Device_clock / K (where K is integer)
- Must meet setup/hold at all receivers
- Account for clock distribution delays
- Use analog delay for fine tuning

**Example**:
```c
// For 250 MHz device clock, 32K frame format:
// SYSREF = 250 MHz / 32 = 7.8125 MHz
struct hmc7044_sysref_config sysref = {
    .enable = true,
    .mode = HMC7044_SYSREF_ONESHOT,
    .divider = 32,
    .pulse_gen_mode = HMC7044_PULSE_GEN_POS_EDGE,
};
```

## Phase Control Configuration

### Digital Phase Adjustment

Coarse phase control (90° steps):

```c
enum ad9523_phase {
    AD9523_PHASE_0_DEG = 0,     // 0°
    AD9523_PHASE_90_DEG = 1,    // 90°
    AD9523_PHASE_180_DEG = 2,   // 180°
    AD9523_PHASE_270_DEG = 3,   // 270°
};
```

**Use cases**:
- Quadrature clock generation (I/Q)
- Simple phase alignment
- 90° increments sufficient

### Analog Phase Adjustment

Fine phase control (typically ~25ps steps):

**HMC7044**:
- Analog delay range: 0-800 ps
- Resolution: ~25 ps
- Per-channel independent control

**Calculation**:
```
Phase_deg = (delay_ps / period_ps) × 360°

Example at 10 GHz (100 ps period):
  25 ps delay = (25/100) × 360° = 90°
  100 ps delay = (100/100) × 360° = 360° (full cycle)
```

## Output Synchronization

### Phase-Coherent Outputs

Synchronize multiple outputs for phase coherence:

**AD9523 synchronization**:
```c
// Synchronize all enabled outputs
ret = ad9523_sync_outputs(dev);
```

**HMC7044 synchronization**:
```c
// Step 1: Mute outputs during setup
ret = hmc7044_mute_all_outputs(dev, true);

// Step 2: Configure all channels
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
```

### Trace Delay Matching

Account for PCB trace delays:

**Requirements**:
- Match trace lengths within ±100 ps for phase-critical applications
- Use serpentine routing for length matching
- Consider trace impedance (typically 50Ω or 100Ω differential)

**Compensation**:
```c
// Compensate for trace length differences
// Trace 1: 5 inch = ~850 ps delay
// Trace 2: 6 inch = ~1020 ps delay
// Difference: 170 ps

// Add 170 ps to channel 0 to match channel 1
ret = hmc7044_set_phase_offset(dev, 0, 170/25);  // 170ps / 25ps per step
```

## Power Supply Configuration

### Supply Filtering

Critical for low phase noise:

**Requirements**:
- Separate analog and digital supplies
- Low-noise LDOs for sensitive supplies
- Ferrite beads for isolation
- Proper grounding and decoupling

**Decoupling network**:
```
VCC → [Ferrite Bead] → [10µF bulk] → [1µF ceramic] → [0.1µF ceramic] → IC pin
                                      ↓              ↓
                                     GND            GND
```

### Charge Pump Current

Affects loop dynamics and lock time:

**Guidelines**:
- Typical range: 0.3 mA to 5 mA
- Higher current = faster lock, potentially more noise
- Lower current = slower lock, cleaner spectrum
- Follow datasheet recommendations for loop filter design

**Configuration**:
```c
// Moderate setting for balanced performance
uint16_t cp_current_ua = 2500;  // 2.5 mA
ret = adf4371_set_charge_pump_current(dev, cp_current_ua);
```

## Advanced Configuration

### Frequency Hopping Configuration

For fast frequency changes:

**Pre-programmed frequencies**:
```c
// Program frequency table (one-time setup)
uint64_t freq_table[] = {
    2400000000,  // Channel 0
    2450000000,  // Channel 1
    2500000000,  // Channel 2
};

for (int i = 0; i < 3; i++) {
    ret = adf4371_program_frequency_table(dev, i, freq_table[i]);
}

// Fast hop (< 100µs)
ret = adf4371_hop_to_frequency(dev, 1);  // Switch to channel 1
```

### FSK Modulation Configuration

For frequency shift keying:

```c
struct adf4371_fsk_config fsk = {
    .enable = true,
    .freq_dev_hz = 100000,     // ±100 kHz deviation
    .rate_hz = 10000,          // 10 kHz modulation rate
};

ret = adf4371_configure_fsk(dev, &fsk);
```

### Reference Auto-Switching

Automatic failover to backup reference:

```c
// Enable automatic reference switching
ret = hmc7044_enable_ref_auto_switch(dev, true);

// Configure priority: CLK0 primary, CLK1 backup
ret = hmc7044_set_ref_source(dev, HMC7044_REF_CLK0);
```

## Initialization Examples

### Basic PLL Initialization

```c
struct adf4371_dev *pll;
struct adf4371_init_param init = {
    .spi_init = {
        .device_id = 0,
        .max_speed_hz = 1000000,
        .mode = NO_OS_SPI_MODE_0,
        .chip_select = 0,
    },
    .clkin_freq = 100000000,       // 100 MHz reference
    .target_freq = 5000000000,     // 5 GHz output
    .channel = ADF4371_CH_RF8,     // RF8 output
    .ref_div = 1,                  // No reference division
    .charge_pump_ua = 2500,        // 2.5 mA CP current
    .ref_doubler_en = false,       // No reference doubler
};

ret = adf4371_init(&pll, &init);
```

### Clock Distributor Initialization

```c
struct ad9523_dev *clk_dist;

struct ad9523_channel_spec channels[] = {
    { 0, 2, AD9523_DRIVER_LVDS, true },   // 250 MHz ADC clock
    { 1, 4, AD9523_DRIVER_LVDS, true },   // 125 MHz FPGA clock
    { 13, 64, AD9523_DRIVER_CMOS, true }, // 7.8125 MHz SYSREF
};

struct ad9523_init_param init = {
    .spi_init = {
        .device_id = 0,
        .max_speed_hz = 1000000,
        .mode = NO_OS_SPI_MODE_0,
        .chip_select = 1,
    },
    .channels = channels,
    .num_channels = 3,
    .vcxo_freq = 500000000,  // 500 MHz VCXO
    .spi3wire = false,
};

ret = ad9523_init(&clk_dist, &init);
```
