## Example: Complete AD559x Driver Summary

### Files

1. **include/zephyr/drivers/mfd/ad559x.h** – Public API, register definitions
2. **drivers/mfd/mfd_ad559x.h** – Private header, transfer function, structures
3. **drivers/mfd/mfd_ad559x.c** – Core parent driver
4. **drivers/mfd/mfd_ad559x_i2c.c** – I2C implementation
5. **drivers/mfd/mfd_ad559x_spi.c** – SPI implementation
6. **drivers/dac/dac_ad559x.c** – DAC child driver
7. **drivers/adc/adc_ad559x.c** – ADC child driver
8. **drivers/gpio/gpio_ad559x.c** – GPIO child driver
9. **dts/bindings/mfd/adi,ad559x-common.yaml** – Common devicetree properties
10. **dts/bindings/mfd/adi,ad559x-i2c.yaml** – I2C parent binding
11. **dts/bindings/mfd/adi,ad559x-spi.yaml** – SPI parent binding (implied, uses default spi-device.yaml)
12. **dts/bindings/dac/adi,ad559x-dac.yaml** – DAC child binding
13. **dts/bindings/adc/adi,ad559x-adc.yaml** – ADC child binding
14. **dts/bindings/gpio/adi,ad559x-gpio.yaml** – GPIO child binding

### Key Functions

**Parent public API**:
- `int mfd_ad559x_read_reg(const struct device *dev, uint8_t reg, uint8_t reg_data, uint16_t *val)`
- `int mfd_ad559x_write_reg(const struct device *dev, uint8_t reg, uint16_t val)`
- `int mfd_ad559x_read_raw(const struct device *dev, uint8_t *val, size_t len)`
- `int mfd_ad559x_write_raw(const struct device *dev, uint8_t *val, size_t len)`
- `int mfd_ad559x_read_adc_chan(const struct device *dev, uint8_t channel, uint16_t *result)`
- `int mfd_ad559x_write_dac_chan(const struct device *dev, uint8_t channel, uint16_t value)`
- `int mfd_ad559x_gpio_port_get_raw(const struct device *dev, uint8_t gpio, uint16_t *value)`
- `bool mfd_ad559x_has_pointer_byte_map(const struct device *dev)`

**DAC child API** (standard Zephyr DAC):
- `int dac_ad559x_channel_setup(const struct device *dev, const struct dac_channel_cfg *channel_cfg)`
- `int dac_ad559x_write_value(const struct device *dev, uint8_t channel, uint32_t value)`

**ADC child API** (standard Zephyr ADC):
- `int adc_ad559x_channel_setup(const struct device *dev, const struct adc_channel_cfg *channel_cfg)`
- `int adc_ad559x_read(const struct device *dev, const struct adc_sequence *sequence)`
- `int adc_ad559x_read_async(const struct device *dev, const struct adc_sequence *sequence, struct k_poll_signal *async)`

**GPIO child API** (standard Zephyr GPIO):
- `int gpio_ad559x_configure(const struct device *dev, gpio_pin_t pin, gpio_flags_t flags)`
- `int gpio_ad559x_port_get_raw(const struct device *dev, uint32_t *value)`
- `int gpio_ad559x_port_set_bits_raw(const struct device *dev, gpio_port_pins_t pins)`
- `int gpio_ad559x_port_clear_bits_raw(const struct device *dev, gpio_port_pins_t pins)`

### Devicetree Example

```dts
&i2c1 {
	ad559x: ad559x@13 {
		compatible = "adi,ad559x";
		reg = <0x13>;
		reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;

		ad559x_dac: dac-controller {
			compatible = "adi,ad559x-dac";
			#io-channel-cells = <1>;
			double-output-range;
		};

		ad559x_adc: adc-controller {
			compatible = "adi,ad559x-adc";
			#io-channel-cells = <1>;
			double-input-range;
		};

		ad559x_gpio: gpio-controller {
			compatible = "adi,ad559x-gpio";
			gpio-controller;
			#gpio-cells = <2>;
		};
	};
};
```

### Application Usage

```c
#include <zephyr/drivers/dac.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/gpio.h>

const struct device *dac = DEVICE_DT_GET(DT_NODELABEL(ad559x_dac));
const struct device *adc = DEVICE_DT_GET(DT_NODELABEL(ad559x_adc));
const struct device *gpio_dev = DEVICE_DT_GET(DT_NODELABEL(ad559x_gpio));

void main(void)
{
	// Configure DAC channel 0
	struct dac_channel_cfg dac_ch_cfg = {
		.channel_id = 0,
		.resolution = 12,
	};
	dac_channel_setup(dac, &dac_ch_cfg);

	// Write DAC value
	dac_write_value(dac, 0, 2048);  // Mid-scale

	// Configure ADC channel 1
	struct adc_channel_cfg adc_ch_cfg = {
		.channel_id = 1,
		.gain = ADC_GAIN_1,
		.reference = ADC_REF_INTERNAL,
		.acquisition_time = ADC_ACQ_TIME_DEFAULT,
	};
	adc_channel_setup(adc, &adc_ch_cfg);

	// Read ADC
	uint16_t sample_buffer;
	struct adc_sequence sequence = {
		.channels = BIT(1),
		.buffer = &sample_buffer,
		.buffer_size = sizeof(sample_buffer),
		.resolution = 12,
	};
	adc_read(adc, &sequence);
	printk("ADC value: %u\n", sample_buffer);

	// Configure GPIO pin 2 as output
	gpio_pin_configure(gpio_dev, 2, GPIO_OUTPUT_ACTIVE);
	gpio_pin_set(gpio_dev, 2, 1);

	// Configure GPIO pin 3 as input
	gpio_pin_configure(gpio_dev, 3, GPIO_INPUT);
	int val = gpio_pin_get(gpio_dev, 3);
	printk("GPIO pin 3: %d\n", val);
}
```

