# Waveform Generation Patterns

Signal generation patterns and common DAC usage scenarios.

## Common Usage Patterns

### Pattern 1: Simple Voltage Output

```c
#include "ad5449.h"
#include "no_os_spi.h"

int main(void)
{
    struct ad5449_dev *dev;
    struct ad5449_init_param init = {
        .spi_init = &spi_init,
        .resolution = 12,  // 12-bit DAC
    };
    int ret;

    // Initialize DAC
    ret = ad5449_init(&dev, &init);
    if (ret)
        return ret;

    // Output 2.5V (mid-scale for 0-5V range, 12-bit)
    // Code = 2048 (0x800) for midscale
    ad5449_load_update_channel(dev, 0, 0x800);

    // Waveform generation
    for (int i = 0; i < 4096; i++) {
        ad5449_load_update_channel(dev, 0, i);
        no_os_udelay(10);  // 100kHz update rate
    }

    ad5449_remove(dev);
    return 0;
}
```

---

### Pattern 2: Multi-Channel Synchronized Update

```c
#include "ad5766.h"
#include "no_os_spi.h"

int synchronized_multi_channel_dac(void)
{
    struct ad5766_dev *dev;
    struct ad5766_init_param init = {
        .spi_ip = &spi_init,
        .gpio_ldac_ip = &gpio_ldac_init,
        .daisy_chain_en = AD5766_DISABLE,
    };
    int ret;

    ret = ad5766_init(&dev, &init);
    if (ret)
        return ret;

    // Configure all channels for ±10V output
    for (int ch = 0; ch < 16; ch++) {
        ret = ad5766_set_span(dev, ch, AD5766_M_10V_TO_P_10V);
    }

    // Generate synchronized multi-channel output
    while (1) {
        // Write all channels (no output change yet)
        ret = ad5766_write_register(dev, AD5766_DAC_0, 0x8000);
        ret = ad5766_write_register(dev, AD5766_DAC_1, 0xC000);
        ret = ad5766_write_register(dev, AD5766_DAC_2, 0x4000);

        // Trigger simultaneous update of all 3 channels
        uint16_t ldac_mask = AD5766_LDAC(0) |
                             AD5766_LDAC(1) |
                             AD5766_LDAC(2);
        ret = ad5766_set_sw_ldac(dev, ldac_mask);

        // Outputs change simultaneously (glitch-free)

        no_os_mdelay(1);
    }

    ad5766_remove(dev);
    return 0;
}
```

---

### Pattern 3: Industrial 4-20mA Current Loop

```c
#include "ad5758.h"
#include "no_os_spi.h"

int industrial_current_loop(void)
{
    struct ad5758_dev *dev;
    struct ad5758_init_param init = {
        .spi_ip = &spi_init,
    };
    int ret;

    ret = ad5758_init(&dev, &init);
    if (ret)
        return ret;

    // Configure for 4-20mA output
    ret = ad5758_set_out_range(dev, RANGE_4mA_20mA);

    // Enable slew rate control for smooth transitions
    ret = ad5758_slew_rate_config(dev,
                                  AD5758_SR_EN,
                                  AD5758_SR_STEP_64_CODES,
                                  AD5758_SR_RATE_4_KHZ);

    // Sensor reading loop
    while (1) {
        // Read sensor value (0-100%)
        float sensor_percent = read_sensor();

        // Convert to 16-bit DAC code
        // 0% → 0x0000 (4mA), 100% → 0xFFFF (20mA)
        uint16_t dac_code = (uint16_t)(sensor_percent * 0xFFFF / 100.0);

        // Update output (slew rate applied automatically)
        ret = ad5758_dac_input_write(dev, dac_code);

        no_os_mdelay(100);  // 10Hz update rate
    }

    ad5758_remove(dev);
    return 0;
}
```

---

## Waveform Examples

### Sine Wave Generation

```c
#include <math.h>

void generate_sine_wave(struct ad5449_dev *dev, uint8_t channel)
{
    const uint16_t samples = 256;
    const uint16_t amplitude = 2048;  // Half of 12-bit range
    const uint16_t offset = 2048;     // Midscale

    while (1) {
        for (uint16_t i = 0; i < samples; i++) {
            // Calculate sine value
            float angle = (2.0 * M_PI * i) / samples;
            float sine_val = sin(angle);

            // Convert to DAC code
            uint16_t dac_code = offset + (uint16_t)(sine_val * amplitude);

            // Update output
            ad5449_load_update_channel(dev, channel, dac_code);

            no_os_udelay(100);  // 10kHz sample rate
        }
    }
}
```

---

### Triangle Wave Generation

```c
void generate_triangle_wave(struct ad5449_dev *dev, uint8_t channel)
{
    uint16_t code = 0;
    int8_t direction = 1;  // 1 = rising, -1 = falling
    const uint16_t step = 16;
    const uint16_t max_code = 4095;

    while (1) {
        ad5449_load_update_channel(dev, channel, code);

        // Update code
        if (direction == 1) {
            code += step;
            if (code >= max_code) {
                code = max_code;
                direction = -1;
            }
        } else {
            if (code < step) {
                code = 0;
                direction = 1;
            } else {
                code -= step;
            }
        }

        no_os_udelay(50);  // 20kHz update rate
    }
}
```

---

### Sawtooth Wave Generation

```c
void generate_sawtooth_wave(struct ad5449_dev *dev, uint8_t channel)
{
    uint16_t code = 0;
    const uint16_t step = 8;
    const uint16_t max_code = 4095;

    while (1) {
        ad5449_load_update_channel(dev, channel, code);

        code += step;
        if (code > max_code) {
            code = 0;  // Reset to zero (ramp down)
        }

        no_os_udelay(50);
    }
}
```

---

### Square Wave Generation

```c
void generate_square_wave(struct ad5449_dev *dev, uint8_t channel)
{
    const uint16_t high_level = 4095;  // Full scale
    const uint16_t low_level = 0;      // Zero scale
    const uint32_t period_us = 1000;   // 1kHz square wave

    while (1) {
        // High phase
        ad5449_load_update_channel(dev, channel, high_level);
        no_os_udelay(period_us / 2);

        // Low phase
        ad5449_load_update_channel(dev, channel, low_level);
        no_os_udelay(period_us / 2);
    }
}
```

---

## Multi-Channel Waveforms

### Phase-Shifted Sine Waves

```c
void generate_three_phase_sine(struct ad5766_dev *dev)
{
    const uint16_t samples = 256;
    const uint16_t amplitude = 32768;  // Half of 16-bit range
    const uint16_t offset = 32768;     // Midscale

    while (1) {
        for (uint16_t i = 0; i < samples; i++) {
            // Phase A (0°)
            float angle_a = (2.0 * M_PI * i) / samples;
            uint16_t code_a = offset + (uint16_t)(sin(angle_a) * amplitude);

            // Phase B (120°)
            float angle_b = angle_a + (2.0 * M_PI / 3.0);
            uint16_t code_b = offset + (uint16_t)(sin(angle_b) * amplitude);

            // Phase C (240°)
            float angle_c = angle_a + (4.0 * M_PI / 3.0);
            uint16_t code_c = offset + (uint16_t)(sin(angle_c) * amplitude);

            // Write all channels
            ad5766_write_register(dev, AD5766_DAC_0, code_a);
            ad5766_write_register(dev, AD5766_DAC_1, code_b);
            ad5766_write_register(dev, AD5766_DAC_2, code_c);

            // Trigger simultaneous update
            uint16_t ldac_mask = AD5766_LDAC(0) | AD5766_LDAC(1) | AD5766_LDAC(2);
            ad5766_set_sw_ldac(dev, ldac_mask);

            no_os_udelay(100);  // 10kHz sample rate
        }
    }
}
```

---

### Synchronized Multi-Channel Ramps

```c
void generate_staircase_pattern(struct ad5766_dev *dev)
{
    const uint8_t num_channels = 4;
    const uint16_t max_code = 65535;
    const uint16_t steps = 16;
    const uint16_t step_size = max_code / steps;

    for (uint16_t step = 0; step <= steps; step++) {
        uint16_t code = step * step_size;

        // Write all channels with same value
        for (uint8_t ch = 0; ch < num_channels; ch++) {
            ad5766_write_register(dev, ch, code);
        }

        // Trigger simultaneous update
        uint16_t ldac_mask = 0;
        for (uint8_t ch = 0; ch < num_channels; ch++) {
            ldac_mask |= AD5766_LDAC(ch);
        }
        ad5766_set_sw_ldac(dev, ldac_mask);

        no_os_mdelay(100);  // 100ms per step
    }
}
```

---

## Arbitrary Waveform Generation

### Lookup Table Pattern

```c
// Pre-computed waveform samples
const uint16_t waveform_lut[256] = {
    // Custom waveform data
    0x8000, 0x8324, 0x8647, 0x896A, /* ... */
};

void generate_arbitrary_waveform(struct ad5449_dev *dev, uint8_t channel)
{
    const uint16_t num_samples = sizeof(waveform_lut) / sizeof(waveform_lut[0]);

    while (1) {
        for (uint16_t i = 0; i < num_samples; i++) {
            ad5449_load_update_channel(dev, channel, waveform_lut[i]);
            no_os_udelay(50);  // 20kHz sample rate
        }
    }
}
```

---

### DMA-Based Continuous Waveform

```c
// For high-speed continuous waveform generation
void setup_dma_waveform(struct ad5449_dev *dev)
{
    // 1. Prepare waveform buffer
    uint16_t *waveform_buffer = malloc(BUFFER_SIZE * sizeof(uint16_t));
    
    // 2. Fill buffer with waveform data
    for (int i = 0; i < BUFFER_SIZE; i++) {
        waveform_buffer[i] = compute_waveform_sample(i);
    }

    // 3. Configure DMA for circular buffer transfer
    // (Platform-specific DMA setup)
    
    // 4. Start DMA transfer
    // DMA continuously sends samples to DAC without CPU intervention
}
```

---

## Performance Optimization

### Minimizing Update Latency

```c
// Pre-compute waveform to reduce real-time processing
void optimized_waveform_generation(struct ad5449_dev *dev)
{
    // Pre-compute all samples
    uint16_t samples[1024];
    for (int i = 0; i < 1024; i++) {
        samples[i] = compute_sample(i);  // Done once
    }

    // Fast playback loop
    while (1) {
        for (int i = 0; i < 1024; i++) {
            ad5449_load_update_channel(dev, 0, samples[i]);
            no_os_udelay(10);
        }
    }
}
```

---

### Batch Updates for Multi-Channel

```c
// Minimize SPI transactions by batching updates
void batch_update_channels(struct ad5766_dev *dev, uint16_t *codes, uint8_t num_ch)
{
    // Write all channels in quick succession
    for (uint8_t ch = 0; ch < num_ch; ch++) {
        ad5766_write_register(dev, ch, codes[ch]);
    }

    // Single simultaneous update
    uint16_t ldac_mask = (1 << num_ch) - 1;
    ad5766_set_sw_ldac(dev, ldac_mask);
}
```
