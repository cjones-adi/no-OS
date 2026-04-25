## Consumer API Usage

Applications access child subsystems via standard Zephyr APIs, not MFD-specific APIs.

### Using DAC Child

```c
#include <zephyr/drivers/dac.h>

#define DAC_NODE DT_ALIAS(dac0)
const struct device *dac = DEVICE_DT_GET(DAC_NODE);

void setup_dac(void)
{
	struct dac_channel_cfg ch_cfg = {
		.channel_id = 0,
		.resolution = 12,
	};
	int ret;

	if (!device_is_ready(dac)) {
		printk("DAC device not ready\n");
		return;
	}

	ret = dac_channel_setup(dac, &ch_cfg);
	if (ret < 0) {
		printk("DAC channel setup failed: %d\n", ret);
		return;
	}

	// Write voltage value
	ret = dac_write_value(dac, 0, 2048);  // Mid-scale
	if (ret < 0) {
		printk("DAC write failed: %d\n", ret);
	}
}
```

### Using ADC Child

```c
#include <zephyr/drivers/adc.h>

#define ADC_NODE DT_ALIAS(adc0)
const struct device *adc = DEVICE_DT_GET(ADC_NODE);

void read_adc(void)
{
	struct adc_channel_cfg ch_cfg = {
		.channel_id = 0,
		.gain = ADC_GAIN_1,
		.reference = ADC_REF_INTERNAL,
		.acquisition_time = ADC_ACQ_TIME_DEFAULT,
	};

	uint16_t sample_buffer;
	struct adc_sequence sequence = {
		.channels = BIT(0),
		.buffer = &sample_buffer,
		.buffer_size = sizeof(sample_buffer),
		.resolution = 12,
	};
	int ret;

	if (!device_is_ready(adc)) {
		printk("ADC not ready\n");
		return;
	}

	ret = adc_channel_setup(adc, &ch_cfg);
	if (ret < 0) {
		printk("ADC channel setup failed: %d\n", ret);
		return;
	}

	ret = adc_read(adc, &sequence);
	if (ret < 0) {
		printk("ADC read failed: %d\n", ret);
		return;
	}

	printk("ADC value: %u\n", sample_buffer);
}
```

### Using GPIO Child

```c
#include <zephyr/drivers/gpio.h>

#define GPIO_NODE DT_ALIAS(gpio_ad559x)
const struct device *gpio_dev = DEVICE_DT_GET(GPIO_NODE);

void setup_gpio(void)
{
	int ret;

	if (!device_is_ready(gpio_dev)) {
		printk("GPIO device not ready\n");
		return;
	}

	// Configure pin 0 as output
	ret = gpio_pin_configure(gpio_dev, 0, GPIO_OUTPUT_ACTIVE);
	if (ret < 0) {
		printk("GPIO config failed: %d\n", ret);
		return;
	}

	// Set pin high
	gpio_pin_set(gpio_dev, 0, 1);

	// Configure pin 1 as input
	ret = gpio_pin_configure(gpio_dev, 1, GPIO_INPUT);
	if (ret < 0) {
		printk("GPIO config failed: %d\n", ret);
		return;
	}

	// Read pin state
	int val = gpio_pin_get(gpio_dev, 1);
	printk("GPIO pin 1 value: %d\n", val);
}
```

