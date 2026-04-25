## Debugging Tips

### 1. Enable GPIO Logging

```conf
# prj.conf
CONFIG_LOG=y
CONFIG_GPIO_LOG_LEVEL_DBG=y
```

Logs show pin configuration, port operations, interrupt events.

### 2. Check Device Ready

Add logging to init function:

```c
static int gpio_my_init(const struct device *dev)
{
	const struct my_gpio_config *cfg = dev->config;

	if (!i2c_is_ready_dt(&cfg->i2c)) {
		LOG_ERR("I2C bus not ready: %s", cfg->i2c.bus->name);
		return -ENODEV;
	}

	LOG_INF("GPIO device initialized: %s", dev->name);
	return 0;
}
```

### 3. Verify Pin Configuration

Read back hardware state after configuration:

```c
static int gpio_my_config(const struct device *dev, gpio_pin_t pin,
			  gpio_flags_t flags)
{
	// Configure pin
	int ret = write_config_register(dev, pin, flags);
	if (ret < 0) {
		return ret;
	}

	// Read back to verify
	uint8_t readback;
	read_config_register(dev, pin, &readback);
	LOG_DBG("Pin %d configured, readback: 0x%02x", pin, readback);

	return 0;
}
```

### 4. Dump Port State

Add a debug function to dump entire port:

```c
#ifdef CONFIG_GPIO_LOG_LEVEL_DBG
static void dump_port_state(const struct device *dev)
{
	gpio_port_value_t value;
	gpio_port_get_raw(dev, &value);
	LOG_DBG("Port %s state: 0x%08x", dev->name, value);
}
#endif
```

### 5. Check Interrupt Status

Log interrupt status in ISR:

```c
static void my_gpio_isr(const struct device *dev)
{
	uint8_t int_status;

	read_int_status(dev, &int_status);
	LOG_DBG("GPIO ISR: int_status=0x%02x", int_status);

	if (int_status == 0) {
		LOG_WRN("Spurious interrupt on %s", dev->name);
		return;
	}

	// ... handle interrupts
}
```

### 6. Verify I2C/SPI Communication

Test basic register read/write:

```c
static int gpio_my_init(const struct device *dev)
{
	// ... bus ready check

	// Test communication with device ID register
	uint8_t device_id;
	int ret = i2c_reg_read_byte_dt(&cfg->i2c, REG_DEVICE_ID, &device_id);
	if (ret < 0) {
		LOG_ERR("Failed to read device ID: %d", ret);
		return ret;
	}

	LOG_INF("Device ID: 0x%02x (expected: 0x%02x)", device_id, EXPECTED_ID);

	if (device_id != EXPECTED_ID) {
		LOG_ERR("Device ID mismatch!");
		return -EIO;
	}

	return 0;
}
```

### 7. Check Devicetree Configuration

Verify port_pin_mask generation:

```c
static int gpio_my_init(const struct device *dev)
{
	const struct my_gpio_config *cfg = dev->config;

	LOG_INF("Port pin mask: 0x%08x", cfg->common.port_pin_mask);
	LOG_INF("Number of GPIOs: %d", POPCOUNT(cfg->common.port_pin_mask));

	// ...
}
```

### 8. Use Shell Commands for Testing

Add GPIO shell commands (if CONFIG_GPIO_SHELL=y):

```bash
# List GPIO devices
gpio list

# Configure pin
gpio conf gpio@40000000 13 oh  # output high

# Read pin
gpio get gpio@40000000 13

# Set pin
gpio set gpio@40000000 13 1

# Toggle pin
gpio toggle gpio@40000000 13

# Configure interrupt
gpio int gpio@40000000 13 rising
```

### 9. Verify Callback Registration

Log callback operations:

```c
static int gpio_my_manage_callback(const struct device *dev,
				   struct gpio_callback *cb,
				   bool set)
{
	struct my_gpio_data *data = dev->data;

	LOG_DBG("%s callback, pin_mask=0x%08x",
		set ? "Adding" : "Removing", cb->pin_mask);

	return gpio_manage_callback(&data->common.callbacks, cb, set);
}
```

### 10. Check for Hardware Faults

Some industrial GPIO controllers have fault detection (e.g., MAX14906):

```c
static int check_faults(const struct device *dev)
{
	uint8_t fault_status;

	read_fault_register(dev, &fault_status);

	if (fault_status & FAULT_OVERCURRENT) {
		LOG_ERR("Overcurrent fault detected!");
	}
	if (fault_status & FAULT_OVERVOLTAGE) {
		LOG_ERR("Overvoltage fault detected!");
	}
	if (fault_status & FAULT_THERMAL) {
		LOG_ERR("Thermal shutdown fault!");
	}

	return (fault_status != 0) ? -EIO : 0;
}
```

