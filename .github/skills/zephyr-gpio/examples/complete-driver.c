## Example: Complete GPIO Driver

Full implementation of a simple I2C GPIO expander.

**Driver** (`drivers/gpio/gpio_simple_expander.c`):

```c
#define DT_DRV_COMPAT vendor_simple_gpio_expander

#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/gpio/gpio_utils.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(gpio_simple, CONFIG_GPIO_LOG_LEVEL);

#define REG_INPUT         0x00
#define REG_OUTPUT        0x01
#define REG_POLARITY      0x02
#define REG_CONFIG        0x03  // 0=output, 1=input

struct simple_gpio_config {
	struct gpio_driver_config common;
	struct i2c_dt_spec i2c;
};

struct simple_gpio_data {
	struct gpio_driver_data common;
	uint8_t output_state;
	struct k_sem lock;
};

static int simple_pin_configure(const struct device *dev, gpio_pin_t pin,
				gpio_flags_t flags)
{
	const struct simple_gpio_config *cfg = dev->config;
	struct simple_gpio_data *data = dev->data;
	int ret;

	if ((BIT(pin) & cfg->common.port_pin_mask) == 0) {
		return -ENOTSUP;
	}

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&data->lock, K_FOREVER);

	if ((flags & GPIO_OUTPUT) != 0) {
		// Set output value first
		if ((flags & GPIO_OUTPUT_INIT_LOW) != 0) {
			data->output_state &= ~BIT(pin);
		} else if ((flags & GPIO_OUTPUT_INIT_HIGH) != 0) {
			data->output_state |= BIT(pin);
		}

		ret = i2c_reg_write_byte_dt(&cfg->i2c, REG_OUTPUT, data->output_state);
		if (ret < 0) {
			goto out;
		}

		// Then set direction to output (config bit = 0)
		uint8_t config;
		ret = i2c_reg_read_byte_dt(&cfg->i2c, REG_CONFIG, &config);
		if (ret < 0) {
			goto out;
		}

		config &= ~BIT(pin);
		ret = i2c_reg_write_byte_dt(&cfg->i2c, REG_CONFIG, config);

	} else if ((flags & GPIO_INPUT) != 0) {
		// Set direction to input (config bit = 1)
		uint8_t config;
		ret = i2c_reg_read_byte_dt(&cfg->i2c, REG_CONFIG, &config);
		if (ret < 0) {
			goto out;
		}

		config |= BIT(pin);
		ret = i2c_reg_write_byte_dt(&cfg->i2c, REG_CONFIG, config);
	} else {
		ret = -ENOTSUP;
	}

out:
	k_sem_give(&data->lock);
	return ret;
}

static int simple_port_get_raw(const struct device *dev, gpio_port_value_t *value)
{
	const struct simple_gpio_config *cfg = dev->config;
	struct simple_gpio_data *data = dev->data;
	uint8_t input;
	int ret;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&data->lock, K_FOREVER);
	ret = i2c_reg_read_byte_dt(&cfg->i2c, REG_INPUT, &input);
	k_sem_give(&data->lock);

	if (ret == 0) {
		*value = input & cfg->common.port_pin_mask;
	}

	return ret;
}

static int simple_port_set_masked_raw(const struct device *dev,
				      gpio_port_pins_t mask,
				      gpio_port_value_t value)
{
	const struct simple_gpio_config *cfg = dev->config;
	struct simple_gpio_data *data = dev->data;
	int ret;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&data->lock, K_FOREVER);

	data->output_state = (data->output_state & ~mask) | (value & mask);
	ret = i2c_reg_write_byte_dt(&cfg->i2c, REG_OUTPUT, data->output_state);

	k_sem_give(&data->lock);
	return ret;
}

static int simple_port_set_bits_raw(const struct device *dev,
				    gpio_port_pins_t pins)
{
	const struct simple_gpio_config *cfg = dev->config;
	struct simple_gpio_data *data = dev->data;
	int ret;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&data->lock, K_FOREVER);

	data->output_state |= pins;
	ret = i2c_reg_write_byte_dt(&cfg->i2c, REG_OUTPUT, data->output_state);

	k_sem_give(&data->lock);
	return ret;
}

static int simple_port_clear_bits_raw(const struct device *dev,
				      gpio_port_pins_t pins)
{
	const struct simple_gpio_config *cfg = dev->config;
	struct simple_gpio_data *data = dev->data;
	int ret;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&data->lock, K_FOREVER);

	data->output_state &= ~pins;
	ret = i2c_reg_write_byte_dt(&cfg->i2c, REG_OUTPUT, data->output_state);

	k_sem_give(&data->lock);
	return ret;
}

static int simple_port_toggle_bits(const struct device *dev,
				   gpio_port_pins_t pins)
{
	const struct simple_gpio_config *cfg = dev->config;
	struct simple_gpio_data *data = dev->data;
	int ret;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&data->lock, K_FOREVER);

	data->output_state ^= pins;
	ret = i2c_reg_write_byte_dt(&cfg->i2c, REG_OUTPUT, data->output_state);

	k_sem_give(&data->lock);
	return ret;
}

static int simple_pin_interrupt_configure(const struct device *dev,
					  gpio_pin_t pin,
					  enum gpio_int_mode mode,
					  enum gpio_int_trig trig)
{
	// Not supported for simple expander
	return -ENOTSUP;
}

static int simple_manage_callback(const struct device *dev,
				  struct gpio_callback *callback,
				  bool set)
{
	struct simple_gpio_data *data = dev->data;

	return gpio_manage_callback(&data->common.callbacks, callback, set);
}

static const struct gpio_driver_api simple_gpio_api = {
	.pin_configure = simple_pin_configure,
	.port_get_raw = simple_port_get_raw,
	.port_set_masked_raw = simple_port_set_masked_raw,
	.port_set_bits_raw = simple_port_set_bits_raw,
	.port_clear_bits_raw = simple_port_clear_bits_raw,
	.port_toggle_bits = simple_port_toggle_bits,
	.pin_interrupt_configure = simple_pin_interrupt_configure,
	.manage_callback = simple_manage_callback,
};

static int simple_gpio_init(const struct device *dev)
{
	const struct simple_gpio_config *cfg = dev->config;
	struct simple_gpio_data *data = dev->data;

	if (!i2c_is_ready_dt(&cfg->i2c)) {
		LOG_ERR("I2C bus not ready");
		return -ENODEV;
	}

	k_sem_init(&data->lock, 1, 1);

	LOG_INF("GPIO expander initialized");
	return 0;
}

#define SIMPLE_GPIO_INIT(inst)                                         \
	static const struct simple_gpio_config simple_gpio_cfg_##inst = { \
		.common = {                                            \
			.port_pin_mask =                               \
				GPIO_PORT_PIN_MASK_FROM_DT_INST(inst), \
		},                                                     \
		.i2c = I2C_DT_SPEC_INST_GET(inst),                     \
	};                                                             \
	static struct simple_gpio_data simple_gpio_data_##inst;        \
	DEVICE_DT_INST_DEFINE(inst, simple_gpio_init, NULL,           \
			      &simple_gpio_data_##inst,                \
			      &simple_gpio_cfg_##inst,                 \
			      POST_KERNEL, CONFIG_GPIO_INIT_PRIORITY,  \
			      &simple_gpio_api);

DT_INST_FOREACH_STATUS_OKAY(SIMPLE_GPIO_INIT)
```

**Binding** (`dts/bindings/gpio/vendor,simple-gpio-expander.yaml`):

```yaml
description: Simple GPIO Expander

compatible: "vendor,simple-gpio-expander"

include: [gpio-controller.yaml, i2c-device.yaml]

properties:
  "#gpio-cells":
    const: 2

  ngpios:
    type: int
    required: true

gpio-cells:
  - pin
  - flags
```

**Devicetree**:

```dts
&i2c1 {
	gpio_exp: gpio-expander@20 {
		compatible = "vendor,simple-gpio-expander";
		reg = <0x20>;
		gpio-controller;
		#gpio-cells = <2>;
		ngpios = <8>;
	};
};

/ {
	leds {
		led_ext: led-ext {
			gpios = <&gpio_exp 0 GPIO_ACTIVE_HIGH>;
		};
	};
};
```

**Application**:

```c
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_NODELABEL(led_ext), gpios);

void main(void)
{
	if (!gpio_is_ready_dt(&led)) {
		printk("LED GPIO not ready\n");
		return;
	}

	gpio_pin_configure_dt(&led, GPIO_OUTPUT_LOW);

	while (1) {
		gpio_pin_toggle_dt(&led);
		k_sleep(K_MSEC(500));
	}
}
```

