## Value Conversion Utilities

### Raw to Millivolts Conversion

```c
#include <zephyr/drivers/adc.h>

void convert_to_millivolts(const struct adc_dt_spec *spec, uint16_t raw_value)
{
	int32_t val_mv = (int32_t)raw_value;

	int err = adc_raw_to_millivolts_dt(spec, &val_mv);
	if (err == 0) {
		printk("Raw: %u → %d mV\n", raw_value, val_mv);
	} else {
		printk("Conversion not supported\n");
	}
}
```

### Manual Conversion Using Gain

```c
int32_t manual_conversion(uint16_t raw, enum adc_gain gain,
                          uint8_t resolution, int32_t vref_mv)
{
	int64_t val_mv = (int64_t)raw * (int64_t)vref_mv;

	/* Invert gain (e.g., ADC_GAIN_1_2 means multiply by 2) */
	adc_gain_invert_64(gain, &val_mv);

	/* Normalize by resolution */
	val_mv = val_mv >> resolution;

	return (int32_t)val_mv;
}
```

### Differential Channel Conversion

```c
void differential_conversion(const struct adc_dt_spec *spec, uint16_t raw_value)
{
	int32_t val_mv;

	/* For differential channels, interpret as signed 2's complement */
	if (spec->channel_cfg.differential) {
		val_mv = (int32_t)((int16_t)raw_value);
	} else {
		val_mv = (int32_t)raw_value;
	}

	/* Convert to millivolts (accounts for differential in resolution) */
	int err = adc_raw_to_millivolts_dt(spec, &val_mv);
	if (err == 0) {
		printk("Differential voltage: %d mV\n", val_mv);
	}
}
```

