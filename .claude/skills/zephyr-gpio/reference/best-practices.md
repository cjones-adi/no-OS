## Common Patterns and Best Practices

### 1. Use gpio_dt_spec for Devicetree Integration

**Good** – Use gpio_dt_spec structure:

```c
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

if (gpio_is_ready_dt(&led)) {
	gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
	gpio_pin_set_dt(&led, 1);
}
```

**Bad** – Manual device/pin lookups:

```c
// DON'T DO THIS - error-prone and verbose
const struct device *gpio_dev = DEVICE_DT_GET(DT_NODELABEL(gpio0));
gpio_pin_t led_pin = 13;
gpio_dt_flags_t flags = GPIO_ACTIVE_LOW;

gpio_pin_configure(gpio_dev, led_pin, GPIO_OUTPUT | flags);
```

**Why:** gpio_dt_spec handles active-low logic, device lookup, and pin number automatically.

### 2. Always Check device_is_ready() or gpio_is_ready_dt()

**Good** – Check before use:

```c
if (!gpio_is_ready_dt(&led)) {
	LOG_ERR("LED GPIO not ready");
	return -ENODEV;
}
gpio_pin_configure_dt(&led, GPIO_OUTPUT);
```

**Bad** – Assume device is ready:

```c
// DON'T DO THIS - may crash if device not initialized
gpio_pin_configure_dt(&led, GPIO_OUTPUT);
```

### 3. Use Shadow Registers for Bus-Connected Expanders

**Good** – Maintain shadow register:

```c
struct my_gpio_data {
	struct gpio_driver_data common;
	uint16_t output_state;  // Shadow register
};

static int my_port_set_bits_raw(const struct device *dev, gpio_port_pins_t pins)
{
	struct my_gpio_data *data = dev->data;

	// Update shadow
	data->output_state |= pins;

	// Write to hardware
	return i2c_reg_write_byte_dt(&cfg->i2c, REG_OUTPUT, data->output_state);
}
```

**Bad** – Read-modify-write over I2C/SPI every time:

```c
// DON'T DO THIS - slow and error-prone
static int my_port_set_bits_raw(const struct device *dev, gpio_port_pins_t pins)
{
	uint8_t val;
	i2c_reg_read_byte_dt(&cfg->i2c, REG_OUTPUT, &val);  // Slow I2C read
	val |= pins;
	return i2c_reg_write_byte_dt(&cfg->i2c, REG_OUTPUT, val);
}
```

**Why:** Shadow register avoids slow I2C/SPI reads, ensures atomic operations.

### 4. Handle Active-Low Logic Correctly

**Good** – Let Zephyr handle it:

```c
// Devicetree:
//   led-gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

// Turn LED on (Zephyr inverts for active-low)
gpio_pin_set_dt(&led, 1);  // Writes 0 to HW
```

**Bad** – Manual inversion:

```c
// DON'T DO THIS
if (led.dt_flags & GPIO_ACTIVE_LOW) {
	gpio_pin_set(led.port, led.pin, !value);
} else {
	gpio_pin_set(led.port, led.pin, value);
}
```

**Why:** gpio_pin_set_dt() handles active-low automatically.

### 5. Initialize Outputs Before Configuring Direction

**Good** – Set output value first:

```c
static int my_pin_configure(const struct device *dev, gpio_pin_t pin,
			    gpio_flags_t flags)
{
	if ((flags & GPIO_OUTPUT) != 0) {
		// 1. Update shadow register FIRST
		if ((flags & GPIO_OUTPUT_INIT_LOW) != 0) {
			data->output_state &= ~BIT(pin);
		} else if ((flags & GPIO_OUTPUT_INIT_HIGH) != 0) {
			data->output_state |= BIT(pin);
		}

		// 2. Write output data register
		write_output_register(dev, data->output_state);

		// 3. THEN configure direction to output
		set_direction_output(dev, pin);
	}
}
```

**Bad** – Configure direction first:

```c
// DON'T DO THIS - pin may glitch
set_direction_output(dev, pin);  // Pin outputs old value
write_output_register(dev, new_value);  // Then changes
```

**Why:** Setting direction before output value causes glitches.

### 6. Use Locking for I2C/SPI GPIO Expanders

**Good** – Synchronize bus access:

```c
struct my_gpio_data {
	struct gpio_driver_data common;
	struct k_sem lock;  // or k_mutex for MFD parent's lock
};

static int my_port_set_bits_raw(const struct device *dev, gpio_port_pins_t pins)
{
	struct my_gpio_data *data = dev->data;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;  // Can't do I2C/SPI in ISR
	}

	k_sem_take(&data->lock, K_FOREVER);

	// I2C/SPI operations here
	int ret = i2c_reg_write_byte_dt(...);

	k_sem_give(&data->lock);
	return ret;
}
```

**Bad** – No locking:

```c
// DON'T DO THIS - race conditions possible
static int my_port_set_bits_raw(const struct device *dev, gpio_port_pins_t pins)
{
	// No locking - multiple threads could corrupt bus
	return i2c_reg_write_byte_dt(...);
}
```

**Why:** Multiple threads accessing I2C/SPI simultaneously causes corruption.

### 7. Return -EWOULDBLOCK from ISR Context

**Good** – Check and return error:

```c
static int my_port_get_raw(const struct device *dev, gpio_port_value_t *value)
{
	if (k_is_in_isr()) {
		return -EWOULDBLOCK;  // Can't block in ISR
	}

	k_sem_take(&data->lock, K_FOREVER);
	// ... I2C/SPI operations
	k_sem_give(&data->lock);
}
```

**Bad** – Block in ISR:

```c
// DON'T DO THIS
static int my_port_get_raw(const struct device *dev, gpio_port_value_t *value)
{
	k_sem_take(&data->lock, K_FOREVER);  // DEADLOCK in ISR!
	// ...
}
```

### 8. Validate Pin Number Against port_pin_mask

**Good** – Check pin is supported:

```c
static int my_pin_configure(const struct device *dev, gpio_pin_t pin,
			    gpio_flags_t flags)
{
	const struct my_gpio_config *cfg = dev->config;

	// Check pin is valid
	if ((BIT(pin) & cfg->common.port_pin_mask) == 0) {
		return -ENOTSUP;
	}

	// ... configure pin
}
```

**Bad** – No validation:

```c
// DON'T DO THIS - may access invalid hardware
static int my_pin_configure(const struct device *dev, gpio_pin_t pin,
			    gpio_flags_t flags)
{
	// No check - pin 37 on 16-pin device!
	write_config_register(pin, ...);
}
```

### 9. Handle Non-Contiguous Pin Layouts

Some GPIO expanders have non-contiguous pin numbering (e.g., ADP5585).

**Good** – Use gpio-reserved-ranges:

```yaml
# devicetree binding
gpio-reserved-ranges:
  const: [5, 3]  # pins 5, 6, 7 reserved

# Port has pins 0-4 and 8-12, total 10 pins
```

**Driver uses port_pin_mask**:

```c
#define ADP5585_BANK(offs) (offs >> 3)  // Which register bank
#define ADP5585_BIT(offs)  (offs & GENMASK(2, 0))  // Bit within bank

static int gpio_adp5585_config(const struct device *dev, gpio_pin_t pin, ...)
{
	if ((BIT(pin) & cfg->common.port_pin_mask) == 0) {
		return -ENOTSUP;  // Reserved pin
	}

	uint8_t bank = ADP5585_BANK(pin);  // 0 or 1
	uint8_t bank_pin = ADP5585_BIT(pin);  // 0-7 within bank
	// ...
}
```

### 10. Fire Callbacks from Interrupt Handler

**Good** – Call gpio_fire_callbacks():

```c
static void my_gpio_isr(const struct device *dev)
{
	const struct my_gpio_config *cfg = dev->config;
	struct my_gpio_data *data = dev->data;
	uint8_t int_status;

	// Read interrupt status register
	read_int_status(dev, &int_status);

	// Clear interrupt
	clear_interrupt(dev, int_status);

	// Fire callbacks for pins with pending interrupts
	gpio_fire_callbacks(&data->common.callbacks, dev, int_status);
}
```

**Bad** – Call callbacks directly:

```c
// DON'T DO THIS
static void my_gpio_isr(const struct device *dev)
{
	// Manually iterate callbacks - error-prone
	struct gpio_callback *cb;
	SYS_SLIST_FOR_EACH_CONTAINER(&data->common.callbacks, cb, node) {
		if (cb->pin_mask & int_status) {
			cb->handler(dev, cb, int_status);
		}
	}
}
```

**Why:** gpio_fire_callbacks() handles filtering and safe iteration.

