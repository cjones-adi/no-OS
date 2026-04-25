## Common Patterns and Best Practices

### 1. Always Validate Device Ready State

**Good**:
```c
if (!device_is_ready(dac_dev)) {
	LOG_ERR("DAC device not ready");
	return -ENODEV;
}
```

**Bad**:
```c
/* Assuming device is ready without checking */
dac_channel_setup(dac_dev, &cfg);
```

### 2. Always Call dac_channel_setup() Before First Write

**Good**:
```c
/* Configure channel once during initialization */
ret = dac_channel_setup(dac_dev, &ch_cfg);
if (ret < 0) {
	return ret;
}

/* Now safe to write values */
dac_write_value(dac_dev, 0, 2048);
```

**Bad**:
```c
/* Writing without prior channel setup */
dac_write_value(dac_dev, 0, 2048);  /* May fail or produce incorrect output */
```

### 3. Validate Value Range

**Good**:
```c
uint32_t max_value = (1U << resolution) - 1;

if (value > max_value) {
	LOG_WRN("Value %u exceeds DAC range %u, clamping", value, max_value);
	value = max_value;
}

dac_write_value(dac_dev, channel, value);
```

**Bad**:
```c
/* Writing value without range check */
dac_write_value(dac_dev, channel, 65535);  /* May exceed DAC resolution */
```

### 4. Use Buffered Output for Direct Load Driving

**Good** (driving LED, resistive load):
```c
struct dac_channel_cfg ch_cfg = {
	.channel_id = 0,
	.resolution = 12,
	.buffered = true,  /* Enable buffer to drive load directly */
};
```

**Bad** (unbuffered with low-impedance load):
```c
struct dac_channel_cfg ch_cfg = {
	.channel_id = 0,
	.resolution = 12,
	.buffered = false,  /* May not drive load properly */
};
```

**When to use unbuffered**:
- High-impedance loads (op-amp inputs, MOSFET gates)
- External buffer amplifier is present
- Lower power consumption required

### 5. Check Broadcast Support Before Use

**Good**:
```c
int ret = dac_write_value(dac_dev, DAC_CHANNEL_BROADCAST, value);

if (ret == -EINVAL) {
	/* Broadcast not supported, fall back to individual writes */
	for (uint8_t ch = 0; ch < num_channels; ch++) {
		dac_write_value(dac_dev, ch, value);
	}
} else if (ret < 0) {
	LOG_ERR("DAC write failed: %d", ret);
}
```

**Bad**:
```c
/* Assuming broadcast works without checking return value */
dac_write_value(dac_dev, DAC_CHANNEL_BROADCAST, value);
```

### 6. Consider Settling Time for Accuracy

**Good** (precision application):
```c
/* Write new value */
dac_write_value(dac_dev, 0, new_value);

/* Wait for output to settle (check datasheet for settling time) */
k_usleep(10);  /* e.g., 10µs settling time */

/* Now output is stable for ADC sampling or measurement */
adc_sample_fetch(adc_dev);
```

**Bad** (may read unstable output):
```c
dac_write_value(dac_dev, 0, new_value);
adc_sample_fetch(adc_dev);  /* Too fast, DAC output still settling */
```

### 7. Use POST_KERNEL Priority for DAC Initialization

**Good** (in driver):
```c
DEVICE_DT_INST_DEFINE(inst, dac_init, NULL,
                      &dac_data##inst, &dac_config##inst,
                      POST_KERNEL, CONFIG_DAC_INIT_PRIORITY,
                      &dac_api);

BUILD_ASSERT(CONFIG_DAC_INIT_PRIORITY > CONFIG_SPI_INIT_PRIORITY,
             "DAC must initialize after SPI");
```

**Why**: DAC drivers depend on SPI/I2C being initialized first.

### 8. Cache Last Written Value (if needed)

**Good** (for read-modify-write or status queries):
```c
struct dac_data {
	uint32_t last_value[MAX_CHANNELS];
};

static int dac_write_value(const struct device *dev, uint8_t channel, uint32_t value)
{
	struct dac_data *data = dev->data;
	int ret;

	ret = hardware_write(dev, channel, value);
	if (ret == 0) {
		/* Cache successful write */
		data->last_value[channel] = value;
	}

	return ret;
}
```

**Use case**: Some DACs don't support readback, caching allows status queries.

### 9. Handle Multi-Compatible Device Families

**Good** (support AD5601/AD5611/AD5621 with one driver):
```c
/* Define instantiation macro with resolution parameter */
#define DAC_AD56X1_INST_DEFINE(index, name, res) \
	static const struct ad56x1_config config_##name##_##index = { \
		.bus = SPI_DT_SPEC_INST_GET(index, ...), \
		.resolution = res \
	}; \
	DEVICE_DT_INST_DEFINE(index, ad56x1_init, NULL, NULL, \
	                      &config_##name##_##index, POST_KERNEL, \
	                      CONFIG_DAC_AD56X1_INIT_PRIORITY, \
	                      &ad56x1_driver_api);

/* Instantiate for each compatible string */
#define DT_DRV_COMPAT adi_ad5601
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)
DT_INST_FOREACH_STATUS_OKAY_VARGS(DAC_AD56X1_INST_DEFINE, DT_DRV_COMPAT, 8)
#endif
#undef DT_DRV_COMPAT

#define DT_DRV_COMPAT adi_ad5611
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)
DT_INST_FOREACH_STATUS_OKAY_VARGS(DAC_AD56X1_INST_DEFINE, DT_DRV_COMPAT, 10)
#endif
#undef DT_DRV_COMPAT
```

### 10. Validate Channel ID in Both Functions

**Good**:
```c
static int dac_channel_setup(..., const struct dac_channel_cfg *cfg)
{
	if (cfg->channel_id >= MAX_CHANNELS) {
		return -EINVAL;
	}
	/* ... */
}

static int dac_write_value(..., uint8_t channel, uint32_t value)
{
	if (channel >= MAX_CHANNELS) {
		return -EINVAL;
	}
	/* ... */
}
```

**Why**: Validation in both functions prevents invalid access even if setup is skipped.

