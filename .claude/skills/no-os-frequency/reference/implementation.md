# Frequency Driver Implementation Patterns

Complete reference for implementing frequency synthesis and clock generation drivers in the no-OS framework.

## Device Architecture Patterns

### Fractional-N PLLs

Architecture for precise frequency synthesis with sub-Hz resolution:

```c
struct adf4371_dev {
    struct no_os_spi_desc *spi_desc;      // SPI interface
    uint64_t clkin_freq;                  // Reference frequency
    uint64_t vco_freq;                    // VCO frequency
    uint32_t ref_div_factor;              // R divider
    uint8_t integer;                      // INT portion
    uint32_t fract1;                      // FRAC1 numerator
    uint32_t fract2;                      // FRAC2 numerator
    uint32_t mod2;                        // FRAC2 modulus
    enum adf4371_output_channel channel;  // Output channel
};

struct adf4371_init_param {
    struct no_os_spi_init_param spi_init;
    uint64_t clkin_freq;                  // Reference clock (Hz)
    uint64_t target_freq;                 // Desired output (Hz)
    enum adf4371_output_channel channel;  // RF8, RF16, or RF32
    bool ref_doubler_en;                  // Reference doubler
    uint8_t ref_div;                      // R divider (1-64)
    uint8_t charge_pump_ua;               // Charge pump current
};
```

**Key characteristics**:
- Synthesize precise frequencies
- Fine frequency resolution (sub-Hz)
- Wide output range (typically GHz)
- Phase-locked to reference
- Supports integer and fractional divide ratios

**Example devices**: ADF4371, ADF4368, ADF5610

### Integer-N PLLs

Simpler architecture for better phase noise performance:

```c
// Integer-N for lowest phase noise
uint32_t fref = 10000000;     // 10 MHz reference
uint32_t fout = 2400000000;   // 2.4 GHz output
uint16_t r_div = 1;
uint16_t n_div = 240;         // Fout / Fref = 240

ret = adf4153_set_frequency(dev, fref, n_div, r_div);
```

**Key characteristics**:
- Simpler architecture
- Lower phase noise than fractional-N
- Coarser frequency resolution
- Faster lock time
- Lower spurious emissions

**Example devices**: ADF4153, ADF4156

### Clock Distributors/Fanout Buffers

Multi-output synchronized clock distribution:

```c
struct ad9523_dev {
    struct no_os_spi_desc *spi_desc;
    struct ad9523_channel_spec channels[14];  // Channel configs
    struct ad9523_vcxo_config vcxo;           // VCXO parameters
    uint32_t vco_freq;                        // VCO frequency
    uint8_t num_channels;                     // Active channels
    bool sysref_enable;                       // SYSREF enabled
};

struct hmc7044_dev {
    struct no_os_spi_desc *spi_desc;
    struct hmc7044_channel_config ch[14];     // Per-channel config
    uint64_t pll1_pfd;                        // PLL1 phase detector freq
    uint64_t pll2_freq;                       // PLL2 output freq
    uint32_t clkin_freq;                      // Input clock
    uint8_t pll1_r_div;                       // PLL1 R divider
    uint16_t pll2_n_div;                      // PLL2 N divider
};
```

**Key characteristics**:
- Multiple synchronized outputs (up to 14)
- Programmable dividers per channel
- Low additive jitter
- SYSREF generation (JESD204B)
- Phase control and delay adjustment

**Example devices**: AD9523, HMC7044, LTC6953

### VCOs (Voltage Controlled Oscillators)

Direct frequency control for custom PLL designs:

**Key characteristics**:
- Wide tuning range
- External loop filter
- Direct frequency control
- Used in custom PLL designs

## PLL Fundamentals

### Basic PLL Architecture

```
Reference → [÷R] → [PFD] → [Charge Pump] → [Loop Filter] → [VCO] → Output
  (Fref)             ↑                                         ↓
                     └─────────── [÷N] ←──────────────────────┘
                              (Feedback)

Output Frequency:
  Fout = Fref × (N / R)

For fractional-N:
  Fout = Fref × ((INT + (FRAC1 + FRAC2/MOD2)) / R)
```

### VCO Calibration

Manual VCO calibration (usually automatic):

```c
// Trigger VCO calibration
ret = adf4371_calibrate_vco(dev);

// Wait for calibration
uint32_t timeout = 100;
while (timeout--) {
    bool cal_done;
    ret = adf4371_get_calibration_status(dev, &cal_done);
    if (cal_done) break;
    no_os_mdelay(1);
}

// Read VCO band selection
uint8_t vco_band;
ret = adf4371_get_vco_band(dev, &vco_band);
pr_info("VCO calibrated to band %d\n", vco_band);
```

### Temperature Compensation

Some devices have internal temperature sensors:

```c
// Read die temperature
int16_t die_temp;
ret = hmc7044_get_die_temperature(dev, &die_temp);
pr_info("Die temperature: %d C\n", die_temp);

// Temperature compensation adjustment
if (die_temp > 85) {
    pr_warn("High temperature, may affect phase noise\n");
}
```

### Phase Noise Optimization

Settings for low phase noise:

```c
struct adf4371_low_noise_config {
    bool ref_doubler;          // false - avoid doubler noise
    uint8_t r_div;             // 1 - minimize R divider
    uint16_t cp_current_ua;    // 1250 - moderate CP current
    bool dither_enable;        // false - disable for integer-N
};

// Integer-N has better phase noise than fractional-N
// Use lowest R divider that maintains PFD within limits
// Optimize loop bandwidth (typically 1/10 of PFD frequency)
```

## IIO Integration

### IIO Channels Example (ADF4371)

```c
static struct iio_channel adf4371_channels[] = {
    {
        .name = "altvoltage0",
        .ch_type = IIO_ALTVOLTAGE,
        .indexed = true,
        .channel = 0,
        .attributes = adf4371_attributes,
    },
};

static int adf4371_iio_read_frequency(void *dev, char *buf, uint32_t len,
                                      const struct iio_ch_info *channel,
                                      intptr_t priv)
{
    struct adf4371_dev *adf4371 = dev;
    uint64_t freq = adf4371->vco_freq;

    return iio_format_value(buf, len, IIO_VAL_INT_64, 1, (int64_t*)&freq);
}

static int adf4371_iio_write_frequency(void *dev, char *buf, uint32_t len,
                                       const struct iio_ch_info *channel,
                                       intptr_t priv)
{
    struct adf4371_dev *adf4371 = dev;
    int64_t freq;

    iio_parse_value(buf, IIO_VAL_INT_64, (int32_t*)&freq, NULL);
    return adf4371_set_frequency(adf4371, (uint64_t)freq);
}
```

## Reference Examples

- **ADF4371 Example**: `projects/adf4371/src/examples/`
- **AD9523 Example**: `projects/ad9523/src/examples/`
- **HMC7044 Example**: `projects/hmc7044/src/examples/`
- **IIO Integration**: `drivers/frequency/*/iio_*.c`
