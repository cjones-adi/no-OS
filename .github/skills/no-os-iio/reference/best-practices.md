# IIO Best Practices

Guidelines for implementing robust and maintainable IIO device interfaces.

## General Principles

### 1. Always Terminate Attribute Arrays

**Required:**

```c
static struct iio_attribute attrs[] = {
    { .name = "raw", .show = get_raw },
    { .name = "scale", .show = get_scale },
    END_ATTRIBUTES_ARRAY  // REQUIRED
};
```

**Why:** The framework iterates through attributes until it finds the terminator. Missing terminators cause buffer overruns and undefined behavior.

### 2. Use Enums for Attribute IDs

**Good:**

```c
enum sensor_attrs {
    SENSOR_RAW,
    SENSOR_SCALE,
    SENSOR_OFFSET,
    SENSOR_SAMPLING_FREQ,
};

static struct iio_attribute attrs[] = {
    { .name = "raw", .priv = SENSOR_RAW, .show = get_attr },
    { .name = "scale", .priv = SENSOR_SCALE, .show = get_attr },
    { .name = "offset", .priv = SENSOR_OFFSET, .show = get_attr },
    { .name = "sampling_frequency", .priv = SENSOR_SAMPLING_FREQ,
      .show = get_attr, .store = set_attr },
    END_ATTRIBUTES_ARRAY
};
```

**Bad:**

```c
// Magic numbers - hard to maintain
{ .name = "raw", .priv = 0, .show = get_attr },
{ .name = "scale", .priv = 1, .show = get_attr },
```

**Why:** Enums make code self-documenting, prevent ID collisions, and enable compiler warnings.

### 3. Validate Channel Masks

Always validate the requested channel mask in `pre_enable()`:

```c
int32_t adc_pre_enable(void *dev, uint32_t ch_mask)
{
    struct adc_desc *desc = dev;
    uint32_t max_mask = (1 << desc->num_channels) - 1;

    // Validate mask
    if (ch_mask == 0 || ch_mask > max_mask)
        return -EINVAL;

    // Configure hardware for enabled channels
    return adc_set_channel_mask(desc, ch_mask);
}
```

### 4. Return Proper Error Codes

Use standard errno values:

```c
int get_attr(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    struct sensor_desc *desc = dev;

    if (!desc)
        return -ENODEV;  // Device not found

    if (ch->ch_num >= desc->num_channels)
        return -EINVAL;  // Invalid parameter

    int ret = sensor_read(desc);
    if (ret)
        return -EIO;  // I/O error

    return snprintf(buf, len, "%d", desc->value);
}
```

**Common error codes:**
- `-EINVAL` - Invalid parameter
- `-ENODEV` - Device not found
- `-EIO` - I/O error
- `-ENOMEM` - Out of memory
- `-EBUSY` - Device busy
- `-ENOTSUP` - Operation not supported

### 5. Keep show/store Functions Lightweight

**Good:**

```c
int get_temp(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    struct temp_sensor *desc = dev;

    // Quick register read - returns immediately
    int32_t temp = temp_sensor_read_cached(desc);
    return snprintf(buf, len, "%d", temp);
}
```

**Bad:**

```c
int get_temp(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    struct temp_sensor *desc = dev;

    // SLOW - blocks for 100ms
    no_os_mdelay(100);  // DON'T DO THIS
    int32_t temp = temp_sensor_read(desc);
    return snprintf(buf, len, "%d", temp);
}
```

**Why:** IIO commands are synchronous. Long delays block the entire IIO daemon and make clients unresponsive.

### 6. Use scan_index to Define Buffer Order

```c
static struct iio_channel channels[] = {
    { .name = "voltage0", .scan_index = 0 },  // First in buffer
    { .name = "voltage1", .scan_index = 1 },  // Second
    { .name = "voltage2", .scan_index = 2 },  // Third
    { .name = "temp", .scan_index = 3 },      // Last
};
```

The framework uses `scan_index` to pack enabled channels in the correct order.

### 7. Test with libiio Tools

Before writing custom applications, test with standard tools:

```bash
# List devices
iio_info -u serial:/dev/ttyUSB0,115200

# Read attributes
iio_attr -d mydevice -c voltage0 raw

# Write attributes
iio_attr -d mydevice -c voltage0 sampling_frequency 1000

# Read buffer
iio_readdev -u serial:/dev/ttyUSB0,115200 mydevice -s 100
```

### 8. Document Attribute Units

**Good:**

```c
// ADC attributes
enum adc_attrs {
    ADC_RAW,           // Raw ADC value (0-4095)
    ADC_SCALE,         // mV per LSB (e.g., 0.805664)
    ADC_OFFSET,        // Offset in mV
    ADC_SAMPLING_FREQ, // Sampling rate in Hz (10-10000)
};
```

**Bad:**

```c
// No documentation
enum adc_attrs {
    ADC_RAW,
    ADC_SCALE,
    ADC_OFFSET,
};
```

### 9. Handle Buffer Overruns Gracefully

```c
int32_t adc_submit(struct iio_device_data *dev_data)
{
    struct adc_desc *desc = dev_data->dev;
    struct iio_buffer *buffer = dev_data->buffer;
    uint16_t data[MAX_CHANNELS];
    int ret;

    for (uint32_t i = 0; i < buffer->samples; i++) {
        ret = adc_read_channels(desc, data, buffer->active_mask);
        if (ret)
            return ret;

        ret = iio_buffer_push_scan(buffer, data);
        if (ret == -ENOBUFS) {
            // Buffer full - not an error for streaming
            break;
        }
        if (ret)
            return ret;
    }

    return i;  // Return actual number of samples written
}
```

### 10. Use Context Attributes for Device Identification

```c
struct iio_ctx_attr ctx_attrs[] = {
    { .name = "hw_serial", .value = "SN12345" },
    { .name = "hw_model", .value = "AD7606-EVK" },
    { .name = "hw_carrier", .value = "MAX32670EVKIT" },
    { .name = "fw_version", .value = "1.2.3" },
};
```

**Benefits:**
- Clients can verify they're connected to the correct device
- Useful for device farm management
- Enables firmware version checking

## Attribute Design Patterns

### Read-Only Attributes

For fixed device properties:

```c
int get_chip_id(void *dev, char *buf, uint32_t len,
                const struct iio_ch_info *ch, intptr_t priv)
{
    return snprintf(buf, len, "0x%04X", CHIP_ID);
}

static struct iio_attribute attrs[] = {
    { .name = "chip_id", .show = get_chip_id },  // No .store
    END_ATTRIBUTES_ARRAY
};
```

### Read-Write Attributes

For configurable parameters:

```c
int get_gain(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    struct adc_desc *desc = dev;
    return snprintf(buf, len, "%u", desc->gain);
}

int set_gain(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    struct adc_desc *desc = dev;
    uint32_t gain;

    sscanf(buf, "%u", &gain);

    if (gain > MAX_GAIN)
        return -EINVAL;

    return adc_set_gain(desc, gain);
}

static struct iio_attribute attrs[] = {
    { .name = "gain", .show = get_gain, .store = set_gain },
    END_ATTRIBUTES_ARRAY
};
```

### Enumerated Attributes

For selecting from a list of options:

```c
int get_filter_mode(void *dev, char *buf, uint32_t len,
                    const struct iio_ch_info *ch, intptr_t priv)
{
    struct adc_desc *desc = dev;
    const char *modes[] = { "none", "low_pass", "high_pass" };

    return snprintf(buf, len, "%s", modes[desc->filter_mode]);
}

int set_filter_mode(void *dev, char *buf, uint32_t len,
                    const struct iio_ch_info *ch, intptr_t priv)
{
    struct adc_desc *desc = dev;

    if (strcmp(buf, "none") == 0)
        desc->filter_mode = 0;
    else if (strcmp(buf, "low_pass") == 0)
        desc->filter_mode = 1;
    else if (strcmp(buf, "high_pass") == 0)
        desc->filter_mode = 2;
    else
        return -EINVAL;

    return adc_set_filter(desc, desc->filter_mode);
}

// Also provide _available variant
int get_filter_mode_available(void *dev, char *buf, uint32_t len,
                               const struct iio_ch_info *ch, intptr_t priv)
{
    return snprintf(buf, len, "none low_pass high_pass");
}

static struct iio_attribute attrs[] = {
    { .name = "filter_mode", .show = get_filter_mode, .store = set_filter_mode },
    { .name = "filter_mode_available", .show = get_filter_mode_available },
    END_ATTRIBUTES_ARRAY
};
```

## Buffer Callback Patterns

### Pre-enable: Channel Configuration

```c
int32_t adc_pre_enable(void *dev, uint32_t ch_mask)
{
    struct adc_desc *desc = dev;
    int ret;

    // 1. Validate mask
    if (ch_mask == 0 || ch_mask >= (1 << desc->num_channels))
        return -EINVAL;

    // 2. Configure hardware for enabled channels
    ret = adc_set_active_channels(desc, ch_mask);
    if (ret)
        return ret;

    // 3. Pre-allocate buffers if needed
    desc->sample_buffer = malloc(desc->buffer_size);
    if (!desc->sample_buffer)
        return -ENOMEM;

    // 4. Start hardware (if applicable)
    return adc_start_continuous(desc);
}
```

### Submit: Data Transfer

```c
int32_t adc_submit(struct iio_device_data *dev_data)
{
    struct adc_desc *desc = dev_data->dev;
    struct iio_buffer *buffer = dev_data->buffer;
    uint16_t data[MAX_CHANNELS];
    uint32_t samples_written = 0;
    int ret;

    // Transfer requested number of samples
    for (uint32_t i = 0; i < buffer->samples; i++) {
        // Read from hardware
        ret = adc_read_sample(desc, data, buffer->active_mask);
        if (ret)
            return ret;

        // Push to IIO buffer
        ret = iio_buffer_push_scan(buffer, data);
        if (ret)
            return ret;

        samples_written++;
    }

    return samples_written;
}
```

### Post-disable: Cleanup

```c
int32_t adc_post_disable(void *dev)
{
    struct adc_desc *desc = dev;

    // 1. Stop hardware
    adc_stop_continuous(desc);

    // 2. Free buffers
    if (desc->sample_buffer) {
        free(desc->sample_buffer);
        desc->sample_buffer = NULL;
    }

    // 3. Reset state
    desc->active_channels = 0;

    return 0;
}
```

## Performance Optimization

### 1. Cache Frequently Read Values

**Good:**

```c
struct sensor_desc {
    int32_t cached_temp;
    uint32_t cache_time_ms;
};

int get_temp(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    struct sensor_desc *desc = dev;
    uint32_t now = get_time_ms();

    // Refresh cache if older than 100ms
    if (now - desc->cache_time_ms > 100) {
        sensor_read(desc, &desc->cached_temp);
        desc->cache_time_ms = now;
    }

    return snprintf(buf, len, "%d", desc->cached_temp);
}
```

### 2. Optimize Buffer Transfers

Use DMA if available:

```c
int32_t adc_submit(struct iio_device_data *dev_data)
{
    struct adc_desc *desc = dev_data->dev;
    struct iio_buffer *buffer = dev_data->buffer;

    // Configure DMA transfer
    return adc_dma_transfer(desc, buffer->buff, buffer->samples);
}
```

### 3. Minimize Register Accesses

**Good - Single burst read:**

```c
int32_t imu_submit(struct iio_device_data *dev_data)
{
    uint8_t raw_data[14];  // All axes in one buffer

    // Single I2C/SPI transaction for all channels
    imu_read_burst(desc, raw_data, sizeof(raw_data));

    return iio_buffer_push_scan(buffer, raw_data);
}
```

**Bad - Multiple single reads:**

```c
int32_t imu_submit(struct iio_device_data *dev_data)
{
    uint16_t data[6];

    // 6 separate I2C/SPI transactions - SLOW
    data[0] = imu_read_reg(desc, GYRO_X_REG);
    data[1] = imu_read_reg(desc, GYRO_Y_REG);
    data[2] = imu_read_reg(desc, GYRO_Z_REG);
    data[3] = imu_read_reg(desc, ACCEL_X_REG);
    data[4] = imu_read_reg(desc, ACCEL_Y_REG);
    data[5] = imu_read_reg(desc, ACCEL_Z_REG);

    return iio_buffer_push_scan(buffer, data);
}
```

## Error Handling

### Graceful Degradation

```c
int get_temp(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    struct sensor_desc *desc = dev;
    int32_t temp;
    int ret;

    ret = sensor_read(desc, &temp);
    if (ret) {
        // Return cached value on error, but log it
        pr_warning("Temperature read failed, using cached value\n");
        temp = desc->last_valid_temp;
    } else {
        desc->last_valid_temp = temp;
    }

    return snprintf(buf, len, "%d", temp);
}
```

### Input Validation

```c
int set_sampling_freq(void *dev, char *buf, uint32_t len,
                      const struct iio_ch_info *ch, intptr_t priv)
{
    struct adc_desc *desc = dev;
    uint32_t freq;
    int ret;

    // Parse input
    ret = sscanf(buf, "%u", &freq);
    if (ret != 1)
        return -EINVAL;

    // Validate range
    if (freq < desc->min_freq || freq > desc->max_freq)
        return -EINVAL;

    // Apply configuration
    return adc_set_sampling_rate(desc, freq);
}
```

## Testing Checklist

Before releasing IIO driver:

- [ ] All attributes return valid values
- [ ] Write attributes reject invalid inputs
- [ ] `END_ATTRIBUTES_ARRAY` terminators present
- [ ] Buffer callbacks handle all enabled channel combinations
- [ ] Error codes are appropriate and consistent
- [ ] Tested with `iio_info`, `iio_attr`, `iio_readdev`
- [ ] Works with IIO Oscilloscope
- [ ] Performance acceptable (no blocking delays)
- [ ] Memory leaks checked (valgrind or similar)
- [ ] Context attributes populated correctly
