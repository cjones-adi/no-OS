# Frequency Driver API Usage and Examples

Complete usage examples for frequency synthesis drivers in the no-OS framework.

## Core Functionality

### 1. Frequency Setting

#### Fractional-N Frequency Synthesis

Automatic PLL calculation for precise frequency synthesis:

```c
// Set output frequency (automatic PLL calculation)
uint64_t target_freq = 5000000000ULL;  // 5 GHz
ret = adf4371_set_frequency(dev, target_freq);

// PLL will calculate optimal INT, FRAC1, FRAC2 values
pr_info("Requested: %llu Hz\n", target_freq);
pr_info("Actual VCO: %llu Hz\n", dev->vco_freq);

// For ADF4371, three output channels available:
// - RF8:  VCO / 8   (500 MHz - 1000 MHz)
// - RF16: VCO / 16  (250 MHz - 500 MHz)
// - RF32: VCO / 32  (125 MHz - 250 MHz)
```

#### Manual PLL Configuration

For custom control of PLL parameters:

```c
// Calculate PLL parameters manually
uint64_t fref = 100000000;    // 100 MHz reference
uint64_t fout = 4800000000;   // 4.8 GHz output
uint8_t r_div = 1;            // R divider

// Calculate N = Fout / (Fref / R)
// N = INT + (FRAC1 + FRAC2/MOD2)
uint16_t integer = 48;        // INT portion
uint32_t frac1 = 0;           // No fractional part
uint32_t frac2 = 0;
uint32_t mod2 = 16384;        // Default modulus

// Write PLL registers
ret = adf4371_set_rfout(dev, integer, frac1, frac2, mod2, r_div);
```

#### Integer-N PLL

For lowest phase noise:

```c
// Integer-N for lowest phase noise
uint32_t fref = 10000000;     // 10 MHz reference
uint32_t fout = 2400000000;   // 2.4 GHz output
uint16_t r_div = 1;
uint16_t n_div = 240;         // Fout / Fref = 240

ret = adf4153_set_frequency(dev, fref, n_div, r_div);
```

### 2. Clock Distribution

#### Multi-Output Configuration (AD9523)

Configure multiple synchronized output channels:

```c
// Configure multiple output channels
struct ad9523_channel_spec channels[] = {
    {
        .channel_num = 0,
        .channel_divider = 2,      // Divide by 2
        .driver_mode = AD9523_DRIVER_LVDS,
        .output_enable = true,
    },
    {
        .channel_num = 1,
        .channel_divider = 4,      // Divide by 4
        .driver_mode = AD9523_DRIVER_LVDS,
        .output_enable = true,
    },
    {
        .channel_num = 4,
        .channel_divider = 1,      // No division (full rate)
        .driver_mode = AD9523_DRIVER_HSTL,
        .output_enable = true,
    },
};

// Setup each channel
for (int i = 0; i < 3; i++) {
    ret = ad9523_setup_channel(dev, channels[i].channel_num, &channels[i]);
}

// Calculate output frequencies
// Fout_ch = Fvco / channel_divider
```

#### HMC7044 14-Output Fanout

Configure different output frequencies:

```c
// Configure HMC7044 with different output frequencies
const struct {
    uint8_t channel;
    uint32_t freq_hz;
} output_config[] = {
    { 0, 250000000 },  // 250 MHz - ADC clock
    { 1, 250000000 },  // 250 MHz - ADC clock (phase matched)
    { 2, 125000000 },  // 125 MHz - FPGA reference
    { 8, 250000000 },  // 250 MHz - DAC clock
    { 13, 7812500 },   // 7.8125 MHz - SYSREF
};

for (int i = 0; i < ARRAY_SIZE(output_config); i++) {
    ret = hmc7044_set_output_frequency(dev,
        output_config[i].channel,
        output_config[i].freq_hz);
}
```

### 3. Phase Control and Synchronization

#### Phase Adjustment

Digital and analog phase control:

```c
// Digital phase adjust (coarse)
enum ad9523_phase {
    AD9523_PHASE_0_DEG = 0,
    AD9523_PHASE_90_DEG = 1,
    AD9523_PHASE_180_DEG = 2,
    AD9523_PHASE_270_DEG = 3,
};

ret = ad9523_set_channel_phase(dev, 0, AD9523_PHASE_90_DEG);

// Analog phase adjust (fine)
// Typical: ~25ps steps
uint16_t phase_offset = 100;  // Device-specific units
ret = hmc7044_set_phase_offset(dev, 0, phase_offset);
```

#### Output Synchronization

Synchronize multiple outputs for phase coherence:

```c
// Synchronize multiple outputs (phase coherent)
ret = ad9523_sync_outputs(dev);

// HMC7044: Use SYNC pin for synchronization
ret = hmc7044_request_sync(dev);
no_os_mdelay(1);

// Verify lock after sync
bool locked;
ret = hmc7044_get_lock_status(dev, &locked);
if (!locked) {
    pr_err("PLL not locked after sync\n");
}
```

#### SYSREF Generation (JESD204B)

Configure SYSREF for JESD204B subclass 1:

```c
// Configure SYSREF for JESD204B subclass 1
struct hmc7044_sysref_config sysref = {
    .enable = true,
    .mode = HMC7044_SYSREF_CONTINUOUS,  // or ONESHOT, NSHOT
    .divider = 32,                      // SYSREF = Fout / 32
    .pulse_gen_mode = HMC7044_PULSE_GEN_POS_EDGE,
};

ret = hmc7044_configure_sysref(dev, &sysref);

// Trigger SYSREF pulse (for one-shot mode)
ret = hmc7044_request_sysref(dev);
```

### 4. Lock Detection

#### PLL Lock Status

Read and wait for PLL lock:

```c
// Read digital lock detect
bool locked;
ret = adf4371_get_lock_status(dev, &locked);
if (locked) {
    pr_info("PLL locked\n");
} else {
    pr_warn("PLL not locked\n");
}

// Wait for lock with timeout
uint32_t timeout_ms = 100;
ret = adf4371_wait_for_lock(dev, timeout_ms);
if (ret < 0) {
    pr_err("Lock timeout\n");
    return ret;
}
```

#### Lock Detect Configuration

Configure lock detect parameters:

```c
// Lock detect window (number of consecutive cycles)
enum adf4371_ld_window {
    ADF4371_LD_WINDOW_3NS = 0,
    ADF4371_LD_WINDOW_6NS = 1,
    ADF4371_LD_WINDOW_9NS = 2,
    ADF4371_LD_WINDOW_12NS = 3,
};

ret = adf4371_set_ld_window(dev, ADF4371_LD_WINDOW_6NS);

// Lock detect pin configuration
ret = adf4371_enable_lock_detect_output(dev, true);
```

### 5. Reference Clock Configuration

#### Reference Input Selection

Select reference source and configure auto-switching:

```c
enum hmc7044_ref_source {
    HMC7044_REF_CLK0 = 0,      // External reference 0
    HMC7044_REF_CLK1 = 1,      // External reference 1
    HMC7044_REF_CLKIN = 2,     // CLKIN input
};

// Select reference source
ret = hmc7044_set_ref_source(dev, HMC7044_REF_CLK0);

// Reference auto-switch configuration
ret = hmc7044_enable_ref_auto_switch(dev, true);
```

#### Reference Doubler/Divider

Adjust reference frequency:

```c
// Reference doubler (2x input frequency)
ret = adf4371_enable_ref_doubler(dev, true);
// Effective Fref = 2 × input frequency

// Reference divider (÷R)
uint8_t r_div = 2;  // Divide by 2
ret = adf4371_set_ref_divider(dev, r_div);
// Fref = input_freq / r_div

// PFD frequency = (input_freq × doubler) / r_div
```

### 6. Output Configuration

#### Output Power Level

Configure output power:

```c
// Set output power (device-specific range)
enum adf4371_output_power {
    ADF4371_OUTPUT_POWER_N4_DBM = 0,
    ADF4371_OUTPUT_POWER_N1_DBM = 1,
    ADF4371_OUTPUT_POWER_2_DBM = 2,
    ADF4371_OUTPUT_POWER_5_DBM = 3,
};

ret = adf4371_set_output_power(dev, ADF4371_OUTPUT_POWER_2_DBM);
```

#### Output Enable/Disable

Control output channels:

```c
// Enable specific output channel
ret = hmc7044_enable_output(dev, 0, true);

// Disable channel
ret = hmc7044_enable_output(dev, 1, false);

// Mute all outputs (for synchronization setup)
ret = hmc7044_mute_all_outputs(dev, true);
// ... configure ...
ret = hmc7044_mute_all_outputs(dev, false);  // Unmute
```

#### Output Driver Mode

Select output driver type:

```c
enum ad9523_driver_mode {
    AD9523_DRIVER_LVPECL = 0,
    AD9523_DRIVER_LVDS = 1,
    AD9523_DRIVER_HSTL = 2,
    AD9523_DRIVER_CMOS = 3,
};

ret = ad9523_set_driver_mode(dev, 0, AD9523_DRIVER_LVDS);
```

### 7. Charge Pump and Loop Filter

#### Charge Pump Current

Configure charge pump for loop dynamics:

```c
// Affects loop bandwidth and lock time
// Typical range: 0.3 mA to 5 mA
uint16_t cp_current_ua = 2500;  // 2.5 mA
ret = adf4371_set_charge_pump_current(dev, cp_current_ua);

// Higher current = faster lock, potentially more noise
// Lower current = slower lock, cleaner spectrum
```

#### Charge Pump Polarity

Invert charge pump if needed:

```c
// Invert charge pump polarity if needed (loop filter design)
ret = adf4371_set_cp_polarity(dev, true);  // Inverted
```

### 8. Modulation and Frequency Hopping

#### Frequency Shift Keying (FSK)

Configure two-point FSK modulation:

```c
// Configure two-point FSK modulation
struct adf4371_fsk_config fsk = {
    .enable = true,
    .freq_dev_hz = 100000,     // ±100 kHz deviation
    .rate_hz = 10000,          // 10 kHz modulation rate
};

ret = adf4371_configure_fsk(dev, &fsk);
```

#### Fast Frequency Hopping

Pre-program frequency table for fast hopping:

```c
// Pre-program frequency table
uint64_t freq_table[] = {
    2400000000,  // 2.4 GHz
    2450000000,  // 2.45 GHz
    2500000000,  // 2.5 GHz
};

for (int i = 0; i < 3; i++) {
    ret = adf4371_program_frequency_table(dev, i, freq_table[i]);
}

// Fast hop to frequency (no recalculation needed)
ret = adf4371_hop_to_frequency(dev, 1);  // Switch to 2.45 GHz
```

## Common Use Cases

### 1. Simple Frequency Synthesizer

Generate a single RF frequency:

```c
// Generate 5.6 GHz for RF application
struct adf4371_dev *pll;
struct adf4371_init_param init = {
    .clkin_freq = 100000000,       // 100 MHz reference
    .target_freq = 5600000000,     // 5.6 GHz output
    .channel = ADF4371_CH_RF8,     // RF8 output
    .ref_div = 1,
    .charge_pump_ua = 2500,
};

ret = adf4371_init(&pll, &init);

// Wait for lock
ret = adf4371_wait_for_lock(pll, 100);
if (ret == 0) {
    pr_info("PLL locked at %llu Hz\n", pll->vco_freq / 8);
}
```

### 2. Multi-Channel Clock Distribution (JESD204B)

Distribute clocks for ADC/DAC system:

```c
// AD9523 distributing clocks for ADC/DAC system
struct ad9523_dev *clk_dist;

// 250 MHz JESD204B clock distribution
struct ad9523_channel_spec channels[] = {
    { 0, 2, AD9523_DRIVER_LVDS, true },  // ADC0 clock (250 MHz)
    { 1, 2, AD9523_DRIVER_LVDS, true },  // ADC1 clock (250 MHz)
    { 4, 2, AD9523_DRIVER_LVDS, true },  // DAC0 clock (250 MHz)
    { 5, 2, AD9523_DRIVER_LVDS, true },  // DAC1 clock (250 MHz)
    { 13, 64, AD9523_DRIVER_CMOS, true }, // SYSREF (7.8125 MHz)
};

struct ad9523_init_param init = {
    .channels = channels,
    .num_channels = 5,
    .vcxo_freq = 500000000,  // 500 MHz VCXO
};

ret = ad9523_init(&clk_dist, &init);

// Synchronize all outputs
ret = ad9523_sync_outputs(clk_dist);
```

### 3. Agile Frequency Hopper

Fast frequency hopping for SDR application:

```c
// Fast frequency hopping for SDR application
uint64_t hop_frequencies[] = {
    2412000000,  // WiFi Ch 1
    2437000000,  // WiFi Ch 6
    2462000000,  // WiFi Ch 11
};

// Pre-program all frequencies
for (int i = 0; i < 3; i++) {
    adf4371_program_frequency_table(dev, i, hop_frequencies[i]);
}

// Hop quickly between channels (< 100µs)
while (scanning) {
    for (int ch = 0; ch < 3; ch++) {
        adf4371_hop_to_frequency(dev, ch);
        no_os_udelay(100);  // Settling time
        scan_channel(ch);
    }
}
```

### 4. Phase-Synchronized Multi-Output System

Phased array radar application:

```c
// HMC7044 for phased array radar
struct hmc7044_dev *fanout;

// 4 channels at 10 GHz with precise phase control
for (int ch = 0; ch < 4; ch++) {
    ret = hmc7044_set_output_frequency(fanout, ch, 10000000000);

    // Set phase offset for beam steering
    // Each ~25ps step ≈ 0.9° at 10 GHz
    uint16_t phase = ch * 100;  // Progressive phase shift
    ret = hmc7044_set_phase_offset(fanout, ch, phase);
}

// Synchronize all outputs
ret = hmc7044_request_sync(fanout);
```

## Typical API Functions

### Fractional-N PLLs (ADF4371)

```c
int adf4371_init(struct adf4371_dev **device, struct adf4371_init_param *init_param);
int adf4371_set_frequency(struct adf4371_dev *dev, uint64_t freq);
int adf4371_get_lock_status(struct adf4371_dev *dev, bool *locked);
int adf4371_wait_for_lock(struct adf4371_dev *dev, uint32_t timeout_ms);
int adf4371_set_output_power(struct adf4371_dev *dev, enum adf4371_output_power power);
int adf4371_remove(struct adf4371_dev *dev);
```

### Clock Distributors (AD9523)

```c
int ad9523_init(struct ad9523_dev **device, struct ad9523_init_param *init_param);
int ad9523_setup_channel(struct ad9523_dev *dev, uint8_t channel, struct ad9523_channel_spec *spec);
int ad9523_set_channel_phase(struct ad9523_dev *dev, uint8_t channel, enum ad9523_phase phase);
int ad9523_sync_outputs(struct ad9523_dev *dev);
int ad9523_remove(struct ad9523_dev *dev);
```

### Multi-Output Fanout (HMC7044)

```c
int hmc7044_init(struct hmc7044_dev **device, struct hmc7044_init_param *init_param);
int hmc7044_set_output_frequency(struct hmc7044_dev *dev, uint8_t ch, uint32_t freq);
int hmc7044_set_phase_offset(struct hmc7044_dev *dev, uint8_t ch, uint16_t offset);
int hmc7044_configure_sysref(struct hmc7044_dev *dev, struct hmc7044_sysref_config *config);
int hmc7044_request_sync(struct hmc7044_dev *dev);
int hmc7044_remove(struct hmc7044_dev *dev);
```
