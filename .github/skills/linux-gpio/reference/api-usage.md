# GPIO Consumer API Usage

Complete guide for using GPIOs in device drivers. This covers the modern descriptor-based GPIO API (gpiod_* functions) for requesting, configuring, and using GPIOs.

## Descriptor-Based GPIO API (gpiod_*)

Modern Linux GPIO consumer API uses descriptors instead of GPIO numbers.

```c
#include <linux/gpio/consumer.h>

struct my_device {
	struct device *dev;
	struct gpio_desc *reset_gpio;
	struct gpio_desc *enable_gpio;
	struct gpio_desc *irq_gpio;
};

static int my_device_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct my_device *mydev;
	int ret;

	mydev = devm_kzalloc(dev, sizeof(*mydev), GFP_KERNEL);
	if (!mydev)
		return -ENOMEM;

	mydev->dev = dev;

	// Get GPIO descriptors from devicetree
	// Devicetree: reset-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;
	mydev->reset_gpio = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(mydev->reset_gpio))
		return dev_err_probe(dev, PTR_ERR(mydev->reset_gpio),
				     "Failed to get reset GPIO\n");

	// Optional GPIO (may not be present)
	mydev->enable_gpio = devm_gpiod_get_optional(dev, "enable", GPIOD_OUT_LOW);
	if (IS_ERR(mydev->enable_gpio))
		return dev_err_probe(dev, PTR_ERR(mydev->enable_gpio),
				     "Failed to get enable GPIO\n");

	// Get GPIO for interrupt
	mydev->irq_gpio = devm_gpiod_get(dev, "irq", GPIOD_IN);
	if (IS_ERR(mydev->irq_gpio))
		return dev_err_probe(dev, PTR_ERR(mydev->irq_gpio),
				     "Failed to get IRQ GPIO\n");

	// Get IRQ number from GPIO
	int irq = gpiod_to_irq(mydev->irq_gpio);
	if (irq < 0)
		return irq;

	ret = devm_request_threaded_irq(dev, irq, NULL, my_device_irq_handler,
					IRQF_TRIGGER_FALLING | IRQF_ONESHOT,
					dev_name(dev), mydev);
	if (ret)
		return ret;

	platform_set_drvdata(pdev, mydev);

	return 0;
}

// Device control functions
static int my_device_reset(struct my_device *mydev)
{
	// Assert reset (GPIO_ACTIVE_LOW polarity handled automatically)
	gpiod_set_value_cansleep(mydev->reset_gpio, 1);
	usleep_range(10000, 20000);     // 10-20ms reset pulse

	// Deassert reset
	gpiod_set_value_cansleep(mydev->reset_gpio, 0);
	usleep_range(5000, 10000);      // 5-10ms recovery time

	return 0;
}

static void my_device_enable(struct my_device *mydev, bool enable)
{
	if (!mydev->enable_gpio)
		return;

	gpiod_set_value_cansleep(mydev->enable_gpio, enable ? 1 : 0);
}

static int my_device_read_status(struct my_device *mydev)
{
	// Read GPIO value (polarity handled automatically)
	return gpiod_get_value_cansleep(mydev->irq_gpio);
}
```

### GPIO Descriptor Functions

```c
// Get GPIO descriptors
struct gpio_desc *devm_gpiod_get(struct device *dev, const char *con_id,
				 enum gpiod_flags flags);
struct gpio_desc *devm_gpiod_get_optional(struct device *dev,
					  const char *con_id,
					  enum gpiod_flags flags);
struct gpio_desc *devm_gpiod_get_index(struct device *dev,
				       const char *con_id,
				       unsigned int idx,
				       enum gpiod_flags flags);
struct gpio_descs *devm_gpiod_get_array(struct device *dev,
					const char *con_id,
					enum gpiod_flags flags);

// Flags for initial direction/value:
// GPIOD_IN          - input
// GPIOD_OUT_LOW     - output, initially low
// GPIOD_OUT_HIGH    - output, initially high
// GPIOD_OUT_LOW_OPEN_DRAIN  - output, open-drain, initially low

// Set direction
int gpiod_direction_input(struct gpio_desc *desc);
int gpiod_direction_output(struct gpio_desc *desc, int value);

// Get/set value (non-sleeping context only)
int gpiod_get_value(const struct gpio_desc *desc);
void gpiod_set_value(struct gpio_desc *desc, int value);

// Get/set value (may sleep - use for I2C/SPI GPIO expanders)
int gpiod_get_value_cansleep(const struct gpio_desc *desc);
void gpiod_set_value_cansleep(struct gpio_desc *desc, int value);

// Multi-GPIO operations
int gpiod_get_array_value(unsigned int array_size,
			  struct gpio_desc **desc_array,
			  struct gpio_array *array_info,
			  unsigned long *value_bitmap);
void gpiod_set_array_value(unsigned int array_size,
			   struct gpio_desc **desc_array,
			   struct gpio_array *array_info,
			   unsigned long *value_bitmap);

// Get IRQ from GPIO
int gpiod_to_irq(const struct gpio_desc *desc);

// Configure electrical properties
int gpiod_set_config(struct gpio_desc *desc, unsigned long config);
int gpiod_set_debounce(struct gpio_desc *desc, unsigned int debounce);

// Query GPIO properties
int gpiod_get_direction(const struct gpio_desc *desc);  // 0=out, 1=in
int gpiod_is_active_low(const struct gpio_desc *desc);
```

