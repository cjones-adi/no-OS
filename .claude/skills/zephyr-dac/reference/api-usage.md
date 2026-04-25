## Application Usage Patterns

### Pattern 1: Basic DAC Output (from sample)

From **samples/drivers/dac/src/main.c**:

```c
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/drivers/dac.h>

#define ZEPHYR_USER_NODE DT_PATH(zephyr_user)

/* Get DAC configuration from devicetree */
#if (DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, dac) && \
     DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, dac_channel_id) && \
     DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, dac_resolution))
#define DAC_NODE        DT_PHANDLE(ZEPHYR_USER_NODE, dac)
#define DAC_CHANNEL_ID  DT_PROP(ZEPHYR_USER_NODE, dac_channel_id)
#define DAC_RESOLUTION  DT_PROP(ZEPHYR_USER_NODE, dac_resolution)
#else
#error "Unsupported board: see README and check /zephyr,user node"
#endif

static const struct device *const dac_dev = DEVICE_DT_GET(DAC_NODE);

static const struct dac_channel_cfg dac_ch_cfg = {
	.channel_id  = DAC_CHANNEL_ID,
	.resolution  = DAC_RESOLUTION,
	.buffered    = true,  /* Enable output buffer */
};

int main(void)
{
	int ret;

	/* Check if DAC device is ready */
	if (!device_is_ready(dac_dev)) {
		printk("DAC device %s is not ready\n", dac_dev->name);
		return 0;
	}

	/* Configure DAC channel */
	ret = dac_channel_setup(dac_dev, &dac_ch_cfg);
	if (ret != 0) {
		printk("Setting up of DAC channel failed with code %d\n", ret);
		return 0;
	}

	/* Write a single value (mid-scale) */
	const uint32_t mid_scale = (1U << DAC_RESOLUTION) / 2;
	ret = dac_write_value(dac_dev, DAC_CHANNEL_ID, mid_scale);
	if (ret != 0) {
		printk("dac_write_value() failed with code %d\n", ret);
		return 0;
	}

	printk("DAC output set to mid-scale: %u\n", mid_scale);

	return 0;
}
```

**Devicetree overlay** (boards/boardname.overlay):

```dts
/ {
	zephyr,user {
		dac = <&dac_ad5621>;
		dac-channel-id = <0>;
		dac-resolution = <12>;
	};
};

&spi0 {
	status = "okay";
	cs-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;

	dac_ad5621: ad5621@0 {
		compatible = "adi,ad5621";
		reg = <0>;
		spi-max-frequency = <30000000>;
		#io-channel-cells = <1>;
	};
};
```

### Pattern 2: Sawtooth Waveform Generation

From **samples/drivers/dac/src/main.c**:

```c
int main(void)
{
	const struct device *const dac_dev = DEVICE_DT_GET(DAC_NODE);

	if (!device_is_ready(dac_dev)) {
		return 0;
	}

	/* Configure channel */
	dac_channel_setup(dac_dev, &dac_ch_cfg);

	printk("Generating sawtooth signal at DAC channel %d.\n", DAC_CHANNEL_ID);

	while (1) {
		/* Number of valid DAC values (e.g., 4096 for 12-bit DAC) */
		const int dac_values = 1U << DAC_RESOLUTION;

		/* Sleep time to achieve ~4 second period */
		const int sleep_time = MAX(1, 4096 / dac_values);

		/* Generate sawtooth: ramp from 0 to max */
		for (int i = 0; i < dac_values; i++) {
			dac_write_value(dac_dev, DAC_CHANNEL_ID, i);
			k_sleep(K_MSEC(sleep_time));
		}
	}

	return 0;
}
```

**Output**: Generates a sawtooth wave with ~4 second period.

### Pattern 3: Multi-Channel DAC Control

```c
#include <zephyr/drivers/dac.h>

#define NUM_CHANNELS 4

void configure_multi_channel_dac(const struct device *dac_dev)
{
	struct dac_channel_cfg ch_cfg = {
		.resolution = 12,
		.buffered = true,
	};

	/* Configure all channels */
	for (uint8_t ch = 0; ch < NUM_CHANNELS; ch++) {
		ch_cfg.channel_id = ch;

		int ret = dac_channel_setup(dac_dev, &ch_cfg);
		if (ret != 0) {
			printk("Channel %d setup failed: %d\n", ch, ret);
		}
	}
}

void set_multi_channel_values(const struct device *dac_dev)
{
	/* Set different values on each channel */
	dac_write_value(dac_dev, 0, 1024);  /* Channel 0: ~25% */
	dac_write_value(dac_dev, 1, 2048);  /* Channel 1: ~50% */
	dac_write_value(dac_dev, 2, 3072);  /* Channel 2: ~75% */
	dac_write_value(dac_dev, 3, 4095);  /* Channel 3: 100% */
}
```

### Pattern 4: Broadcast Mode (All Channels Simultaneously)

```c
#include <zephyr/drivers/dac.h>

void set_all_channels_same_value(const struct device *dac_dev)
{
	/* Write same value to all channels at once */
	uint32_t value = 2048;  /* Mid-scale */

	int ret = dac_write_value(dac_dev, DAC_CHANNEL_BROADCAST, value);
	if (ret == 0) {
		printk("All channels set to %u\n", value);
	} else if (ret == -EINVAL) {
		printk("Broadcast not supported on this DAC\n");

		/* Fall back to individual writes */
		for (uint8_t ch = 0; ch < 8; ch++) {
			dac_write_value(dac_dev, ch, value);
		}
	}
}
```

### Pattern 5: Sine Wave Generation

```c
#include <math.h>
#include <zephyr/drivers/dac.h>

#define SINE_SAMPLES 100
#define DAC_MAX_VALUE 4095  /* 12-bit DAC */

void generate_sine_wave(const struct device *dac_dev, uint8_t channel)
{
	while (1) {
		for (int i = 0; i < SINE_SAMPLES; i++) {
			/* Calculate sine value: [0, DAC_MAX_VALUE] */
			double angle = 2.0 * M_PI * i / SINE_SAMPLES;
			double sine_val = (sin(angle) + 1.0) / 2.0;  /* Normalize to [0, 1] */
			uint32_t dac_value = (uint32_t)(sine_val * DAC_MAX_VALUE);

			dac_write_value(dac_dev, channel, dac_value);
			k_usleep(100);  /* 10 kHz update rate → 100 Hz sine */
		}
	}
}
```

### Pattern 6: Voltage to DAC Value Conversion

```c
#include <zephyr/drivers/dac.h>

/* Convert desired voltage to DAC value */
uint32_t voltage_to_dac_value(float voltage_v, float vref_v, uint8_t resolution)
{
	if (voltage_v < 0.0f) {
		voltage_v = 0.0f;
	}
	if (voltage_v > vref_v) {
		voltage_v = vref_v;
	}

	uint32_t max_value = (1U << resolution) - 1;
	return (uint32_t)((voltage_v / vref_v) * max_value);
}

/* Example: Set 1.65V output on 12-bit DAC with 3.3V reference */
void set_voltage_output(const struct device *dac_dev)
{
	float desired_voltage = 1.65f;  /* 1.65V */
	float vref = 3.3f;              /* 3.3V reference */
	uint8_t resolution = 12;        /* 12-bit DAC */

	uint32_t dac_value = voltage_to_dac_value(desired_voltage, vref, resolution);

	dac_write_value(dac_dev, 0, dac_value);

	printk("Set DAC to %u (%.2fV)\n", dac_value, desired_voltage);
}
```

