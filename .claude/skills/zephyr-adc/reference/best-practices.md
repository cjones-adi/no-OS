## Common Patterns and Best Practices

### 1. Always Validate Device Ready State

**Good**:
```c
if (!adc_is_ready_dt(&adc_spec)) {
	LOG_ERR("ADC device not ready");
	return -ENODEV;
}
```

**Bad**:
```c
/* Assuming device is ready without checking */
adc_channel_setup_dt(&adc_spec);
```

### 2. Always Call adc_channel_setup() Before First Read

**Good**:
```c
/* Configure channel once during initialization */
err = adc_channel_setup_dt(&adc_spec);
if (err < 0) {
	return err;
}

/* Now safe to read */
err = adc_read_dt(&adc_spec, &sequence);
```

**Bad**:
```c
/* Reading without prior channel setup */
err = adc_read_dt(&adc_spec, &sequence);
```

### 3. Validate Buffer Size

**Good**:
```c
uint8_t num_channels = POPCOUNT(sequence.channels);
size_t needed = num_channels * sizeof(uint16_t);

if (sequence.buffer_size < needed) {
	LOG_ERR("Buffer too small: need %zu, have %zu", needed, sequence.buffer_size);
	return -ENOMEM;
}
```

**Bad**:
```c
/* Undersized buffer causes memory corruption */
uint16_t buffer[2];
sequence.channels = BIT(0) | BIT(1) | BIT(2);  /* 3 channels! */
sequence.buffer = buffer;
sequence.buffer_size = sizeof(buffer);  /* Only 2 elements */
```

### 4. Use adc_sequence_init_dt() for DT-Defined Channels

**Good**:
```c
struct adc_sequence sequence = {
	.buffer = &buf,
	.buffer_size = sizeof(buf),
};

/* Initialize channels, resolution, oversampling from DT */
adc_sequence_init_dt(&adc_spec, &sequence);

adc_read_dt(&adc_spec, &sequence);
```

**Bad**:
```c
/* Manually duplicating DT configuration */
struct adc_sequence sequence = {
	.buffer = &buf,
	.buffer_size = sizeof(buf),
	.channels = BIT(adc_spec.channel_id),  /* Redundant */
	.resolution = adc_spec.resolution,     /* Redundant */
	.oversampling = adc_spec.oversampling, /* Redundant */
};
```

### 5. Handle Differential vs. Single-Ended Correctly

**Good**:
```c
int32_t val;

if (adc_spec.channel_cfg.differential) {
	/* Sign-extend for differential */
	val = (int32_t)((int16_t)buf);
} else {
	/* Unsigned for single-ended */
	val = (int32_t)buf;
}

adc_raw_to_millivolts_dt(&adc_spec, &val);
```

**Bad**:
```c
/* Always treating as unsigned loses sign information */
int32_t val = (int32_t)buf;
adc_raw_to_millivolts_dt(&adc_spec, &val);
```

### 6. Check Conversion Support

**Good**:
```c
int32_t val_mv = (int32_t)raw;
int err = adc_raw_to_millivolts_dt(&adc_spec, &val_mv);

if (err == 0) {
	printk("Voltage: %d mV\n", val_mv);
} else if (err == -ENOTSUP) {
	printk("Raw value: %u (mV conversion not supported)\n", raw);
} else if (err == -EINVAL) {
	printk("Gain not reversible\n");
}
```

**Bad**:
```c
/* Assuming conversion always works */
int32_t val_mv = (int32_t)raw;
adc_raw_to_millivolts_dt(&adc_spec, &val_mv);
printk("Voltage: %d mV\n", val_mv);  /* May be wrong if conversion failed */
```

### 7. Use ADC Context Helpers in Drivers

**Good** (from AD4114 driver):
```c
#define ADC_CONTEXT_USES_KERNEL_TIMER
#include "adc_context.h"

struct driver_data {
	struct adc_context ctx;  /* First member */
	/* ... other fields ... */
};

static int driver_read_async(const struct device *dev,
                             const struct adc_sequence *sequence,
                             struct k_poll_signal *async)
{
	struct driver_data *data = dev->data;
	int ret;

	adc_context_lock(&data->ctx, async ? true : false, async);
	ret = driver_start_read(dev, sequence);
	adc_context_release(&data->ctx, ret);

	return ret;
}
```

**Bad**:
```c
/* Reimplementing locking and async signaling from scratch */
static int driver_read_async(const struct device *dev,
                             const struct adc_sequence *sequence,
                             struct k_poll_signal *async)
{
	/* Complex manual locking and signaling logic */
	/* Prone to race conditions and bugs */
}
```

### 8. Provide Internal Reference Voltage in API

**Good**:
```c
static DEVICE_API(adc, driver_api) = {
	.channel_setup = driver_channel_setup,
	.read = driver_read,
	.ref_internal = 2500,  /* 2.5V internal reference */
};
```

**Why**: Allows `adc_raw_to_millivolts_dt()` to work with internal reference.

### 9. Validate Channel IDs

**Good**:
```c
static int driver_channel_setup(const struct device *dev,
                                const struct adc_channel_cfg *channel_cfg)
{
	if (channel_cfg->channel_id >= MAX_CHANNELS) {
		LOG_ERR("Invalid channel ID %d (max %d)",
		        channel_cfg->channel_id, MAX_CHANNELS - 1);
		return -EINVAL;
	}

	/* Proceed with configuration */
}
```

**Bad**:
```c
/* No validation, causes array out-of-bounds access */
config->channel_regs[channel_cfg->channel_id] = value;
```

### 10. Document Acquisition Time Units

**Good** (in binding):
```yaml
zephyr,acquisition-time:
  type: int
  required: true
  description: |
    Acquisition time in ADC clock cycles.
    Use ADC_ACQ_TIME_DEFAULT for driver default,
    or ADC_ACQ_TIME(ADC_ACQ_TIME_MICROSECONDS, 10) for 10µs.
```

From application:
```c
/* Devicetree */
zephyr,acquisition-time = <ADC_ACQ_TIME(ADC_ACQ_TIME_MICROSECONDS, 20)>;

/* Or use driver default */
zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
```

