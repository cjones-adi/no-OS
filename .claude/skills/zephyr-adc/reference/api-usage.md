## Application Usage Patterns

### Pattern 1: Single Channel, Synchronous Read

From **samples/drivers/adc/adc_dt/src/main.c**:

```c
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/kernel.h>

/* Get ADC channels from devicetree zephyr,user node */
#define DT_SPEC_AND_COMMA(node_id, prop, idx) \
	ADC_DT_SPEC_GET_BY_IDX(node_id, idx),

static const struct adc_dt_spec adc_channels[] = {
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels, DT_SPEC_AND_COMMA)
};

int main(void)
{
	uint16_t buf;
	struct adc_sequence sequence = {
		.buffer = &buf,
		.buffer_size = sizeof(buf),
	};

	/* Configure channels before use */
	for (size_t i = 0U; i < ARRAY_SIZE(adc_channels); i++) {
		if (!adc_is_ready_dt(&adc_channels[i])) {
			printk("ADC controller device %s not ready\n",
			       adc_channels[i].dev->name);
			return 0;
		}

		int err = adc_channel_setup_dt(&adc_channels[i]);
		if (err < 0) {
			printk("Could not setup channel #%d (%d)\n", i, err);
			return 0;
		}
	}

	/* Read loop */
	while (1) {
		for (size_t i = 0U; i < ARRAY_SIZE(adc_channels); i++) {
			int32_t val_mv;

			printk("- %s, channel %d: ",
			       adc_channels[i].dev->name,
			       adc_channels[i].channel_id);

			/* Initialize sequence from devicetree spec */
			(void)adc_sequence_init_dt(&adc_channels[i], &sequence);

			/* Perform synchronous read */
			int err = adc_read_dt(&adc_channels[i], &sequence);
			if (err < 0) {
				printk("Could not read (%d)\n", err);
				continue;
			}

			/* Handle differential vs. single-ended */
			if (adc_channels[i].channel_cfg.differential) {
				val_mv = (int32_t)((int16_t)buf);
			} else {
				val_mv = (int32_t)buf;
			}

			printk("%d", val_mv);

			/* Convert to millivolts */
			err = adc_raw_to_millivolts_dt(&adc_channels[i], &val_mv);
			if (err < 0) {
				printk(" (value in mV not available)\n");
			} else {
				printk(" = %d mV\n", val_mv);
			}
		}

		k_sleep(K_MSEC(1000));
	}

	return 0;
}
```

**Devicetree overlay** (boards/boardname.overlay):

```dts
/ {
	zephyr,user {
		io-channels = <&adc0 0>, <&adc0 1>;
		io-channel-names = "battery", "temperature";
	};
};

&adc0 {
	#address-cells = <1>;
	#size-cells = <0>;

	channel@0 {
		reg = <0>;
		zephyr,gain = "ADC_GAIN_1";
		zephyr,reference = "ADC_REF_INTERNAL";
		zephyr,vref-mv = <2500>;
		zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
		zephyr,resolution = <12>;
	};

	channel@1 {
		reg = <1>;
		zephyr,gain = "ADC_GAIN_1_6";
		zephyr,reference = "ADC_REF_VDD_1";
		zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
		zephyr,resolution = <12>;
		zephyr,differential;
	};
};
```

### Pattern 2: Multi-Channel Sampling

```c
#define NUM_CHANNELS 4
static uint16_t sample_buffer[NUM_CHANNELS];

void multi_channel_read(const struct device *adc_dev)
{
	struct adc_sequence sequence = {
		.buffer = sample_buffer,
		.buffer_size = sizeof(sample_buffer),
		.channels = BIT(0) | BIT(1) | BIT(2) | BIT(3),  /* Channels 0-3 */
		.resolution = 12,
		.oversampling = 0,
	};

	int err = adc_read(adc_dev, &sequence);
	if (err == 0) {
		/* Samples written in channel order: ch0, ch1, ch2, ch3 */
		printk("CH0: %u, CH1: %u, CH2: %u, CH3: %u\n",
		       sample_buffer[0], sample_buffer[1],
		       sample_buffer[2], sample_buffer[3]);
	}
}
```

### Pattern 3: Asynchronous Read with k_poll_signal

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/adc.h>

void async_adc_read(const struct adc_dt_spec *adc_spec)
{
	uint16_t buf;
	struct adc_sequence sequence = {
		.buffer = &buf,
		.buffer_size = sizeof(buf),
	};
	struct k_poll_signal async_sig = K_POLL_SIGNAL_INITIALIZER(async_sig);
	struct k_poll_event async_evt = K_POLL_EVENT_INITIALIZER(
		K_POLL_TYPE_SIGNAL,
		K_POLL_MODE_NOTIFY_ONLY,
		&async_sig);

	adc_sequence_init_dt(adc_spec, &sequence);

	/* Start asynchronous read */
	int err = adc_read_async_dt(adc_spec, &sequence, &async_sig);
	if (err < 0) {
		printk("ADC read async failed: %d\n", err);
		return;
	}

	/* Do other work while ADC converts */
	printk("Waiting for ADC conversion...\n");

	/* Wait for completion signal */
	k_poll(&async_evt, 1, K_FOREVER);

	int result;
	k_poll_signal_check(&async_sig, NULL, &result);

	if (result == 0) {
		printk("ADC value: %u\n", buf);
	} else {
		printk("ADC read failed: %d\n", result);
	}
}
```

### Pattern 4: Repeated Sampling with Callback

```c
#include <zephyr/drivers/adc.h>

#define SAMPLE_COUNT 100
static uint16_t samples[SAMPLE_COUNT];
static atomic_t sample_index = ATOMIC_INIT(0);

static enum adc_action sampling_callback(const struct device *dev,
                                         const struct adc_sequence *sequence,
                                         uint16_t sampling_index)
{
	atomic_inc(&sample_index);

	if (sampling_index >= SAMPLE_COUNT - 1) {
		printk("Sampling complete: %d samples\n", SAMPLE_COUNT);
		return ADC_ACTION_FINISH;
	}

	return ADC_ACTION_CONTINUE;
}

void continuous_sampling(const struct device *adc_dev)
{
	struct adc_sequence_options options = {
		.interval_us = 1000,  /* 1ms between samples */
		.callback = sampling_callback,
		.extra_samplings = SAMPLE_COUNT - 1,
	};

	struct adc_sequence sequence = {
		.options = &options,
		.buffer = samples,
		.buffer_size = sizeof(samples),
		.channels = BIT(0),
		.resolution = 12,
	};

	int err = adc_read(adc_dev, &sequence);
	if (err == 0) {
		printk("Captured %d samples\n", atomic_get(&sample_index));
	}
}
```

### Pattern 5: Oversampling for Noise Reduction

```c
void oversampled_read(const struct adc_dt_spec *adc_spec)
{
	uint16_t buf;
	struct adc_sequence sequence = {
		.buffer = &buf,
		.buffer_size = sizeof(buf),
		.oversampling = 4,  /* Average 2^4 = 16 samples */
	};

	adc_sequence_init_dt(adc_spec, &sequence);

	int err = adc_read_dt(adc_spec, &sequence);
	if (err == 0) {
		/* Result is averaged from 16 conversions */
		printk("Oversampled ADC value: %u\n", buf);
	}
}
```

