## Consumer API Usage

Applications use standard Zephyr GPIO APIs to interact with GPIO devices.

### Configure Pin

```c
#include <zephyr/drivers/gpio.h>

// From devicetree
#define LED_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED_NODE, gpios);

void setup_led(void)
{
	int ret;

	// Check GPIO device is ready
	if (!gpio_is_ready_dt(&led)) {
		printk("LED GPIO not ready\n");
		return;
	}

	// Configure as output, initially low
	ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_LOW);
	if (ret < 0) {
		printk("LED config failed: %d\n", ret);
		return;
	}
}
```

### Write  Output Pin

```c
// Set pin high
gpio_pin_set_dt(&led, 1);

// Set pin low
gpio_pin_set_dt(&led, 0);

// Toggle pin
gpio_pin_toggle_dt(&led);

// With manual pin/port specification (no devicetree):
gpio_pin_set(led_gpio_dev, led_pin, 1);
```

### Read Input Pin

```c
#define BUTTON_NODE DT_ALIAS(sw0)
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(BUTTON_NODE, gpios);

void setup_button(void)
{
	int ret;

	if (!gpio_is_ready_dt(&button)) {
		printk("Button GPIO not ready\n");
		return;
	}

	// Configure as input with pull-up
	ret = gpio_pin_configure_dt(&button, GPIO_INPUT);
	if (ret < 0) {
		printk("Button config failed: %d\n", ret);
		return;
	}
}

void read_button(void)
{
	int val = gpio_pin_get_dt(&button);
	if (val < 0) {
		printk("Failed to read button: %d\n", val);
	} else {
		printk("Button state: %d\n", val);
	}
}
```

### Port Operations (Multi-Pin)

```c
const struct device *gpio_port = DEVICE_DT_GET(DT_NODELABEL(gpio0));

void port_operations(void)
{
	gpio_port_value_t port_value;

	// Read entire port
	gpio_port_get_raw(gpio_port, &port_value);
	printk("Port value: 0x%08x\n", port_value);

	// Set multiple pins (pins 3, 5, 7)
	gpio_port_set_bits_raw(gpio_port, BIT(3) | BIT(5) | BIT(7));

	// Clear multiple pins (pins 1, 2, 4)
	gpio_port_clear_bits_raw(gpio_port, BIT(1) | BIT(2) | BIT(4));

	// Set pins using mask (set pins 10-12 to 0b101)
	gpio_port_set_masked_raw(gpio_port,
				 BIT(10) | BIT(11) | BIT(12),  // mask
				 BIT(10) | BIT(12));           // value

	// Toggle pins
	gpio_port_toggle_bits(gpio_port, BIT(8) | BIT(9));
}
```

### GPIO Interrupts

```c
static struct gpio_callback button_cb_data;

static void button_pressed(const struct device *dev,
			   struct gpio_callback *cb,
			   uint32_t pins)
{
	printk("Button pressed on pin(s): 0x%x\n", pins);
}

void setup_button_interrupt(void)
{
	int ret;

	// Configure pin
	ret = gpio_pin_configure_dt(&button, GPIO_INPUT);
	if (ret != 0) {
		printk("Error configuring button: %d\n", ret);
		return;
	}

	// Configure interrupt for rising edge
	ret = gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_RISING);
	if (ret != 0) {
		printk("Error configuring interrupt: %d\n", ret);
		return;
	}

	// Initialize callback
	gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));

	// Add callback to GPIO device
	ret = gpio_add_callback(button.port, &button_cb_data);
	if (ret != 0) {
		printk("Error adding callback: %d\n", ret);
		return;
	}

	printk("Button interrupt configured\n");
}

// Disable interrupt later:
void disable_button_interrupt(void)
{
	gpio_pin_interrupt_configure_dt(&button, GPIO_INT_DISABLE);
}

// Remove callback:
void remove_button_callback(void)
{
	gpio_remove_callback(button.port, &button_cb_data);
}
```

### Multiple Interrupts on Same Port

```c
static struct gpio_callback multi_cb_data;

static void multi_gpio_handler(const struct device *dev,
			       struct gpio_callback *cb,
			       uint32_t pins)
{
	if (pins & BIT(button1_pin)) {
		printk("Button 1 pressed\n");
	}
	if (pins & BIT(button2_pin)) {
		printk("Button 2 pressed\n");
	}
	if (pins & BIT(encoder_a_pin)) {
		printk("Encoder A edge\n");
	}
}

void setup_multi_interrupt(void)
{
	// Configure all pins
	gpio_pin_configure(gpio_dev, button1_pin, GPIO_INPUT);
	gpio_pin_configure(gpio_dev, button2_pin, GPIO_INPUT);
	gpio_pin_configure(gpio_dev, encoder_a_pin, GPIO_INPUT);

	// Configure interrupts
	gpio_pin_interrupt_configure(gpio_dev, button1_pin, GPIO_INT_EDGE_FALLING);
	gpio_pin_interrupt_configure(gpio_dev, button2_pin, GPIO_INT_EDGE_FALLING);
	gpio_pin_interrupt_configure(gpio_dev, encoder_a_pin, GPIO_INT_EDGE_BOTH);

	// Single callback for multiple pins
	gpio_init_callback(&multi_cb_data, multi_gpio_handler,
			   BIT(button1_pin) | BIT(button2_pin) | BIT(encoder_a_pin));

	gpio_add_callback(gpio_dev, &multi_cb_data);
}
```

