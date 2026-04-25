## Driver Implementation Pattern

### Step 1: Define Register Map and Bit Definitions

**From ADP5585** (`drivers/gpio/gpio_adp5585.c`):

```c
#define DT_DRV_COMPAT adi_adp5585_gpio

// Register addresses (from MFD parent header)
// #define ADP5585_GPI_STATUS_A       0x15
// #define ADP5585_GPIO_DIRECTION_A   0x27
// #define ADP5585_GPO_DATA_OUT_A     0x23

// Helper macros for non-contiguous pin layout
#define ADP5585_BANK(offs) (offs >> 3)
#define ADP5585_BIT(offs)  (offs & GENMASK(2, 0))

enum adp5585_gpio_pin_direction {
	adp5585_pin_input = 0U,
	adp5585_pin_output,
};

enum adp5585_gpio_pin_drive_mode {
	adp5585_pin_drive_pp = 0U,  // Push-pull
	adp5585_pin_drive_od,       // Open-drain
};

enum adp5585_gpio_pull_config {
	adp5585_pull_up_300k = 0U,
	adp5585_pull_dn_300k,
	adp5585_pull_up_100k,  // Not used
	adp5585_pull_disable,
};
```

**From MAX22017** (`drivers/gpio/gpio_max22017.c`):

```c
#define DT_DRV_COMPAT adi_max22017_gpio

// Register field macros (from MFD parent header)
// #define MAX22017_GEN_GPIO_CTRL_OFF      0x04
// #define MAX22017_GEN_GPIO_CTRL_GPIO_EN  GENMASK(13, 8)
// #define MAX22017_GEN_GPIO_CTRL_GPIO_DIR GENMASK(5, 0)
// #define MAX22017_GEN_GPIO_DATA_OFF      0x05
// #define MAX22017_GEN_GPIO_DATA_GPO_DATA GENMASK(13, 8)
// #define MAX22017_GEN_GPIO_DATA_GPI_DATA GENMASK(5, 0)
```

### Step 2: Define Config and Data Structures

**Standalone I2C Expander**:

```c
struct my_gpio_config {
	/* gpio_driver_config needs to be first */
	struct gpio_driver_config common;
	struct i2c_dt_spec i2c;  // I2C bus specification
};

struct my_gpio_data {
	/* gpio_driver_data needs to be first */
	struct gpio_driver_data common;
	uint8_t output_state;     // Shadow register
	struct k_sem lock;        // I2C access synchronization
};
```

**MFD Child GPIO** (from ADP5585):

```c
struct adp5585_gpio_config {
	/* gpio_driver_config needs to be first */
	struct gpio_driver_config common;
	const struct device *mfd_dev;       // Parent MFD device
	const struct gpio_dt_spec gpio_int; // Interrupt pin (optional)
};

struct adp5585_gpio_data {
	/* gpio_driver_data needs to be first */
	struct gpio_driver_data common;
	uint16_t output;           // Output shadow register
	sys_slist_t callbacks;     // Already in common, but shown for clarity
};
```

### Step 3: Implement pin_configure()

This is the most important function – configures pin direction, pull resistors, and initial output value.

**From ADP5585** (`drivers/gpio/gpio_adp5585.c`):

```c
static int gpio_adp5585_config(const struct device *dev, gpio_pin_t pin,
			       gpio_flags_t flags)
{
	const struct adp5585_gpio_config *cfg = dev->config;
	struct adp5585_gpio_data *data = dev->data;
	const struct mfd_adp5585_config *parent_cfg =
		(struct mfd_adp5585_config *)(cfg->mfd_dev->config);
	struct mfd_adp5585_data *parent_data =
		(struct mfd_adp5585_data *)(cfg->mfd_dev->data);

	int ret = 0;
	uint8_t reg_value;

	// ADP5585 has non-contiguous GPIO pin layouts
	if ((BIT(pin) & cfg->common.port_pin_mask) == 0) {
		return -ENOTSUP;
	}

	uint8_t bank = ADP5585_BANK(pin);
	uint8_t bank_pin = ADP5585_BIT(pin);

	// Can't do I2C bus operations from an ISR
	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	// Simultaneous PU & PD mode not supported
	if (((flags & GPIO_PULL_UP) != 0) && ((flags & GPIO_PULL_DOWN) != 0)) {
		return -ENOTSUP;
	}

	// Simultaneous input & output mode not supported
	if (((flags & GPIO_INPUT) != 0) && ((flags & GPIO_OUTPUT) != 0)) {
		return -ENOTSUP;
	}

	k_sem_take(&parent_data->lock, K_FOREVER);

	// Configure drive mode (push-pull or open-drain)
	if ((flags & GPIO_SINGLE_ENDED) != 0) {
		reg_value = adp5585_pin_drive_od << bank_pin;
	} else {
		reg_value = adp5585_pin_drive_pp << bank_pin;
	}
	ret = i2c_reg_update_byte_dt(&parent_cfg->i2c_bus,
				     ADP5585_GPO_OUT_MODE_A + bank,
				     BIT(bank_pin), reg_value);
	if (ret != 0) {
		goto out;
	}

	// Configure pull resistors
	uint8_t regaddr = ADP5585_RPULL_CONFIG_A + (bank << 1);
	uint8_t shift = bank_pin << 1;

	if (bank_pin > 3U) {
		regaddr += 1U;
		shift = (bank_pin - 3U) << 1;
	}

	if ((flags & GPIO_PULL_UP) != 0) {
		reg_value = adp5585_pull_up_300k << shift;
	} else if ((flags & GPIO_PULL_DOWN) != 0) {
		reg_value = adp5585_pull_dn_300k << shift;
	} else {
		reg_value = adp5585_pull_disable << shift;
	}

	ret = i2c_reg_update_byte_dt(&parent_cfg->i2c_bus, regaddr,
				     0b11U << shift, reg_value);
	if (ret != 0) {
		goto out;
	}

	// Configure direction and initial value
	if ((flags & GPIO_OUTPUT) != 0) {
		// Set initial output value
		if ((flags & GPIO_OUTPUT_INIT_LOW) != 0) {
			data->output &= ~BIT(pin);
		} else if ((flags & GPIO_OUTPUT_INIT_HIGH) != 0) {
			data->output |= BIT(pin);
		}

		// Write output data register
		if (bank == 0) {
			reg_value = (uint8_t)data->output;
		} else {
			reg_value = (uint8_t)(data->output >> 8);
		}
		ret = i2c_reg_write_byte_dt(&parent_cfg->i2c_bus,
					    ADP5585_GPO_DATA_OUT_A + bank,
					    reg_value);
		if (ret != 0) {
			goto out;
		}

		// Set direction to output
		reg_value = adp5585_pin_output << bank_pin;
	} else if ((flags & GPIO_INPUT) != 0) {
		// Set direction to input
		reg_value = adp5585_pin_input << bank_pin;
	}

	ret = i2c_reg_update_byte_dt(&parent_cfg->i2c_bus,
				     ADP5585_GPIO_DIRECTION_A + bank,
				     BIT(bank_pin), reg_value);

out:
	k_sem_give(&parent_data->lock);
	if (ret != 0) {
		LOG_ERR("pin configure error: %d", ret);
	}
	return ret;
}
```

**From MAX22017** (MFD GPIO):

```c
static int adi_max22017_gpio_set_output(const struct device *dev,
					uint8_t pin, bool initial_value)
{
	int ret;
	uint16_t gpio_data, gpio_ctrl;
	struct max22017_data *data = dev->data;

	k_mutex_lock(&data->lock, K_FOREVER);

	// Read current GPIO data and control registers
	ret = max22017_reg_read(dev, MAX22017_GEN_GPIO_DATA_OFF, &gpio_data);
	if (ret) {
		goto fail;
	}

	ret = max22017_reg_read(dev, MAX22017_GEN_GPIO_CTRL_OFF, &gpio_ctrl);
	if (ret) {
		goto fail;
	}

	// Set initial output value
	if (initial_value) {
		gpio_data |= FIELD_PREP(MAX22017_GEN_GPIO_DATA_GPO_DATA, BIT(pin));
	} else {
		gpio_data &= ~FIELD_PREP(MAX22017_GEN_GPIO_DATA_GPO_DATA, BIT(pin));
	}

	// Enable GPIO and set direction to output
	gpio_ctrl |= FIELD_PREP(MAX22017_GEN_GPIO_CTRL_GPIO_EN, BIT(pin)) |
		     FIELD_PREP(MAX22017_GEN_GPIO_CTRL_GPIO_DIR, BIT(pin));

	ret = max22017_reg_write(dev, MAX22017_GEN_GPIO_DATA_OFF, gpio_data);
	if (ret) {
		goto fail;
	}

	ret = max22017_reg_write(dev, MAX22017_GEN_GPIO_CTRL_OFF, gpio_ctrl);

fail:
	k_mutex_unlock(&data->lock);
	return ret;
}

static int adi_max22017_gpio_pin_configure(const struct device *dev,
					   gpio_pin_t pin,
					   gpio_flags_t flags)
{
	if ((flags & GPIO_OUTPUT) != 0) {
		bool init_high = (flags & GPIO_OUTPUT_INIT_HIGH) != 0;
		return adi_max22017_gpio_set_output(dev, pin, init_high);
	} else if ((flags & GPIO_INPUT) != 0) {
		return adi_max22017_gpio_set_input(dev, pin);
	} else {
		return adi_max22017_gpio_deconfigure(dev, pin);
	}
}
```

### Step 4: Implement port_get_raw()

Read all GPIO pins atomically.

**From ADP5585**:

```c
static int gpio_adp5585_port_read(const struct device *dev,
				  gpio_port_value_t *value)
{
	const struct adp5585_gpio_config *cfg = dev->config;
	const struct mfd_adp5585_config *parent_cfg =
		(struct mfd_adp5585_config *)(cfg->mfd_dev->config);
	struct mfd_adp5585_data *parent_data =
		(struct mfd_adp5585_data *)(cfg->mfd_dev->data);

	uint16_t input_data = 0;
	int ret = 0;

	// Can't do I2C bus operations from an ISR
	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&parent_data->lock, K_FOREVER);

	// Read both GPIO status registers (2 banks)
	uint8_t gpi_status_reg = ADP5585_GPI_STATUS_A;
	uint8_t gpi_status_buf[2];

	ret = i2c_write_read_dt(&parent_cfg->i2c_bus, &gpi_status_reg, 1U,
				gpi_status_buf, 2U);
	if (ret == 0) {
		// Combine 2 8-bit registers into 16-bit value
		input_data = (gpi_status_buf[1] << 8) | gpi_status_buf[0];
		*value = (gpio_port_value_t)(input_data & cfg->common.port_pin_mask);
	}

	k_sem_give(&parent_data->lock);

	return ret;
}
```

**From MAX22017**:

```c
static int adi_max22017_gpio_port_get_raw(const struct device *dev,
					 gpio_port_value_t *value)
{
	int ret;
	uint16_t gpio_data;
	struct max22017_data *data = dev->data;

	k_mutex_lock(&data->lock, K_FOREVER);

	ret = max22017_reg_read(dev, MAX22017_GEN_GPIO_DATA_OFF, &gpio_data);
	if (ret == 0) {
		// Extract input data field from register
		*value = FIELD_GET(MAX22017_GEN_GPIO_DATA_GPI_DATA, gpio_data);
	}

	k_mutex_unlock(&data->lock);
	return ret;
}
```

### Step 5: Implement port_set_masked_raw()

Set multiple pins using a mask (atomic operation).

**From MAX22017**:

```c
static int adi_max22017_gpio_port_set_masked_raw(const struct device *dev,
						 gpio_port_pins_t mask,
						 gpio_port_value_t value)
{
	int ret;
	uint16_t gpio_data, tmp_val;
	struct max22017_data *data = dev->data;

	k_mutex_lock(&data->lock, K_FOREVER);

	// Read current GPIO data register
	ret = max22017_reg_read(dev, MAX22017_GEN_GPIO_DATA_OFF, &gpio_data);
	if (ret) {
		goto fail;
	}

	// Extract current output data field
	tmp_val = FIELD_GET(MAX22017_GEN_GPIO_DATA_GPO_DATA, gpio_data);

	// Apply mask: clear masked bits, set new values
	tmp_val = (tmp_val & ~mask) | (value & mask);

	// Reconstruct register value (preserve input data field)
	gpio_data = FIELD_PREP(MAX22017_GEN_GPIO_DATA_GPO_DATA, tmp_val) |
		    FIELD_PREP(MAX22017_GEN_GPIO_DATA_GPI_DATA,
			       FIELD_GET(MAX22017_GEN_GPIO_DATA_GPI_DATA, gpio_data));

	ret = max22017_reg_write(dev, MAX22017_GEN_GPIO_DATA_OFF, gpio_data);

fail:
	k_mutex_unlock(&data->lock);
	return ret;
}
```

### Step 6: Implement port_set_bits_raw() and port_clear_bits_raw()

Set or clear multiple pins (set to 1 or 0).

**From ADP5585**:

```c
static int gpio_adp5585_port_set_bits(const struct device *dev,
				      gpio_port_pins_t pins)
{
	const struct adp5585_gpio_config *cfg = dev->config;
	struct adp5585_gpio_data *data = dev->data;
	const struct mfd_adp5585_config *parent_cfg =
		(struct mfd_adp5585_config *)(cfg->mfd_dev->config);
	struct mfd_adp5585_data *parent_data =
		(struct mfd_adp5585_data *)(cfg->mfd_dev->data);

	int ret = 0;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&parent_data->lock, K_FOREVER);

	// Update shadow register
	data->output |= pins;

	// Write both output registers
	ret = i2c_reg_write_byte_dt(&parent_cfg->i2c_bus,
				    ADP5585_GPO_DATA_OUT_A,
				    (uint8_t)data->output);
	if (ret == 0) {
		ret = i2c_reg_write_byte_dt(&parent_cfg->i2c_bus,
					    ADP5585_GPO_DATA_OUT_B,
					    (uint8_t)(data->output >> 8));
	}

	k_sem_give(&parent_data->lock);
	return ret;
}

static int gpio_adp5585_port_clear_bits(const struct device *dev,
					gpio_port_pins_t pins)
{
	const struct adp5585_gpio_config *cfg = dev->config;
	struct adp5585_gpio_data *data = dev->data;
	const struct mfd_adp5585_config *parent_cfg =
		(struct mfd_adp5585_config *)(cfg->mfd_dev->config);
	struct mfd_adp5585_data *parent_data =
		(struct mfd_adp5585_data *)(cfg->mfd_dev->data);

	int ret = 0;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&parent_data->lock, K_FOREVER);

	// Update shadow register
	data->output &= ~pins;

	// Write both output registers
	ret = i2c_reg_write_byte_dt(&parent_cfg->i2c_bus,
				    ADP5585_GPO_DATA_OUT_A,
				    (uint8_t)data->output);
	if (ret == 0) {
		ret = i2c_reg_write_byte_dt(&parent_cfg->i2c_bus,
					    ADP5585_GPO_DATA_OUT_B,
					    (uint8_t)(data->output >> 8));
	}

	k_sem_give(&parent_data->lock);
	return ret;
}
```

### Step 7: Implement port_toggle_bits()

Toggle output pins (invert current value).

**From ADP5585**:

```c
static int gpio_adp5585_port_toggle_bits(const struct device *dev,
					gpio_port_pins_t pins)
{
	const struct adp5585_gpio_config *cfg = dev->config;
	struct adp5585_gpio_data *data = dev->data;
	const struct mfd_adp5585_config *parent_cfg =
		(struct mfd_adp5585_config *)(cfg->mfd_dev->config);
	struct mfd_adp5585_data *parent_data =
		(struct mfd_adp5585_data *)(cfg->mfd_dev->data);

	int ret = 0;

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&parent_data->lock, K_FOREVER);

	// Toggle pins in shadow register
	data->output ^= pins;

	// Write both output registers
	ret = i2c_reg_write_byte_dt(&parent_cfg->i2c_bus,
				    ADP5585_GPO_DATA_OUT_A,
				    (uint8_t)data->output);
	if (ret == 0) {
		ret = i2c_reg_write_byte_dt(&parent_cfg->i2c_bus,
					    ADP5585_GPO_DATA_OUT_B,
					    (uint8_t)(data->output >> 8));
	}

	k_sem_give(&parent_data->lock);
	return ret;
}
```

### Step 8: Implement pin_interrupt_configure()

Configure interrupt trigger mode for a pin.

**From ADP5585**:

```c
static int gpio_adp5585_pin_interrupt_configure(const struct device *dev,
						gpio_pin_t pin,
						enum gpio_int_mode mode,
						enum gpio_int_trig trig)
{
	const struct adp5585_gpio_config *cfg = dev->config;
	const struct mfd_adp5585_config *parent_cfg =
		(struct mfd_adp5585_config *)(cfg->mfd_dev->config);
	struct mfd_adp5585_data *parent_data =
		(struct mfd_adp5585_data *)(cfg->mfd_dev->data);

	int ret = 0;

	// Check pin is valid
	if ((BIT(pin) & cfg->common.port_pin_mask) == 0) {
		return -ENOTSUP;
	}

	uint8_t bank = ADP5585_BANK(pin);
	uint8_t bank_pin = ADP5585_BIT(pin);

	if (k_is_in_isr()) {
		return -EWOULDBLOCK;
	}

	k_sem_take(&parent_data->lock, K_FOREVER);

	if (mode == GPIO_INT_MODE_DISABLED) {
		// Disable interrupt for this pin
		ret = i2c_reg_update_byte_dt(&parent_cfg->i2c_bus,
					     ADP5585_GPI_INTERRUPT_EN_A + bank,
					     BIT(bank_pin), 0);
	} else {
		// Configure interrupt level (active high/low)
		uint8_t level_val = 0;
		if (trig == GPIO_INT_TRIG_HIGH) {
			level_val = BIT(bank_pin);  // Active high
		}

		ret = i2c_reg_update_byte_dt(&parent_cfg->i2c_bus,
					     ADP5585_GPI_INT_LEVEL_A + bank,
					     BIT(bank_pin), level_val);
		if (ret != 0) {
			goto out;
		}

		// Enable interrupt for this pin
		ret = i2c_reg_update_byte_dt(&parent_cfg->i2c_bus,
					     ADP5585_GPI_INTERRUPT_EN_A + bank,
					     BIT(bank_pin), BIT(bank_pin));
	}

out:
	k_sem_give(&parent_data->lock);
	return ret;
}
```

### Step 9: Implement manage_callback()

Add or remove interrupt callbacks.

**Simple implementation** (uses gpio_utils.h helper):

```c
static int gpio_my_manage_callback(const struct device *dev,
				   struct gpio_callback *callback,
				   bool set)
{
	struct my_gpio_data *data = dev->data;

	// Use gpio_utils.h helper function
	return gpio_manage_callback(&data->common.callbacks, callback, set);
}
```

### Step 10: Define API Structure

**From ADP5585**:

```c
static DEVICE_API(gpio, adp5585_gpio_api) = {
	.pin_configure = gpio_adp5585_config,
	.port_get_raw = gpio_adp5585_port_read,
	.port_set_masked_raw = gpio_adp5585_port_set_masked,
	.port_set_bits_raw = gpio_adp5585_port_set_bits,
	.port_clear_bits_raw = gpio_adp5585_port_clear_bits,
	.port_toggle_bits = gpio_adp5585_port_toggle_bits,
	.pin_interrupt_configure = gpio_adp5585_pin_interrupt_configure,
	.manage_callback = gpio_adp5585_manage_callback,
};
```

**From MAX22017**:

```c
static const struct gpio_driver_api adi_max22017_gpio_api = {
	.pin_configure = adi_max22017_gpio_pin_configure,
	.port_get_raw = adi_max22017_gpio_port_get_raw,
	.port_set_masked_raw = adi_max22017_gpio_port_set_masked_raw,
	.port_set_bits_raw = adi_max22017_gpio_port_set_bits_raw,
	.port_clear_bits_raw = adi_max22017_gpio_port_clear_bits_raw,
	.port_toggle_bits = adi_max22017_gpio_port_toggle_bits,
	.pin_interrupt_configure = adi_max22017_gpio_pin_interrupt_configure,
	.manage_callback = adi_max22017_gpio_manage_callback,
};
```

### Step 11: Implement Init Function

**From ADP5585** (MFD child):

```c
static int gpio_adp5585_init(const struct device *dev)
{
	const struct adp5585_gpio_config *cfg = dev->config;

	// Check parent MFD device is ready
	if (!device_is_ready(cfg->mfd_dev)) {
		LOG_ERR("MFD parent device %s not ready", cfg->mfd_dev->name);
		return -ENODEV;
	}

	// Initialize callback list
	// (already done by gpio_driver_data common structure)

	return 0;
}
```

**Standalone I2C expander** (pattern):

```c
static int gpio_my_init(const struct device *dev)
{
	const struct my_gpio_config *cfg = dev->config;
	struct my_gpio_data *data = dev->data;

	// Check I2C bus ready
	if (!i2c_is_ready_dt(&cfg->i2c)) {
		return -ENODEV;
	}

	// Initialize semaphore for I2C access
	k_sem_init(&data->lock, 1, 1);

	// Read initial state from device (optional)
	// ...

	return 0;
}
```

### Step 12: Device Instantiation Macro

**Standalone I2C expander**:

```c
#define MY_GPIO_INIT(inst)                                             \
	static const struct my_gpio_config my_gpio_config_##inst = {   \
		.common = {                                            \
			.port_pin_mask =                               \
				GPIO_PORT_PIN_MASK_FROM_DT_INST(inst), \
		},                                                     \
		.i2c = I2C_DT_SPEC_INST_GET(inst),                     \
	};                                                             \
	static struct my_gpio_data my_gpio_data_##inst;                \
	DEVICE_DT_INST_DEFINE(inst, gpio_my_init, NULL,                \
			      &my_gpio_data_##inst,                    \
			      &my_gpio_config_##inst,                  \
			      POST_KERNEL,                             \
			      CONFIG_GPIO_INIT_PRIORITY,               \
			      &my_gpio_api);

DT_INST_FOREACH_STATUS_OKAY(MY_GPIO_INIT)
```

**MFD child** (from ADP5585):

```c
#define ADP5585_GPIO_DEVICE_DEFINE(inst)                               \
	static const struct adp5585_gpio_config adp5585_gpio_config_##inst = { \
		.common = {                                            \
			.port_pin_mask =                               \
				GPIO_PORT_PIN_MASK_FROM_DT_INST(inst), \
		},                                                     \
		.mfd_dev = DEVICE_DT_GET(DT_INST_PARENT(inst)),        \
		.gpio_int = GPIO_DT_SPEC_INST_GET_OR(inst, nint_gpios, {0}), \
	};                                                             \
	static struct adp5585_gpio_data adp5585_gpio_data_##inst;      \
	DEVICE_DT_INST_DEFINE(inst, gpio_adp5585_init, NULL,           \
			      &adp5585_gpio_data_##inst,               \
			      &adp5585_gpio_config_##inst,             \
			      POST_KERNEL, CONFIG_GPIO_INIT_PRIORITY,  \
			      &adp5585_gpio_api);

DT_INST_FOREACH_STATUS_OKAY(ADP5585_GPIO_DEVICE_DEFINE)
```

