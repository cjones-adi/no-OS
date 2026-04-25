## Advanced Features

### Interrupt Handling in Parent

For devices with interrupt capabilities (alarms, GPIOs, etc.), parent can handle interrupts and notify children.

**From ADP5585** (`drivers/mfd/mfd_adp5585.c`):

```c
struct mfd_adp5585_data {
	struct k_work work;
	struct gpio_callback int_gpio_cb;
	struct k_sem lock;
	const struct device *dev;
	struct {
#ifdef CONFIG_GPIO_ADP5585
		const struct device *gpio_dev;
#endif
	} child;
};

static void mfd_adp5585_int_gpio_handler(const struct device *dev,
					 struct gpio_callback *gpio_cb,
					 uint32_t pins)
{
	struct mfd_adp5585_data *data = CONTAINER_OF(gpio_cb,
						      struct mfd_adp5585_data,
						      int_gpio_cb);

	k_work_submit(&data->work);
}

static void mfd_adp5585_work_handler(struct k_work *work)
{
	struct mfd_adp5585_data *data = CONTAINER_OF(work, struct mfd_adp5585_data, work);
	const struct mfd_adp5585_config *config = data->dev->config;
	uint8_t reg_int_status;
	int ret;

	k_sem_take(&data->lock, K_FOREVER);

	// Read interrupt flag
	ret = i2c_reg_read_byte_dt(&config->i2c_bus, ADP5585_INT_STATUS, &reg_int_status);

	// Clear interrupt flag
	if (ret == 0) {
		ret = i2c_reg_write_byte_dt(&config->i2c_bus, ADP5585_INT_STATUS, reg_int_status);
	}

	k_sem_give(&data->lock);

	// Notify GPIO child
#ifdef CONFIG_GPIO_ADP5585
	if ((reg_int_status & ADP5585_INT_GPI) && device_is_ready(data->child.gpio_dev)) {
		(void)gpio_adp5585_irq_handler(data->child.gpio_dev);
	}
#endif
}

static int mfd_adp5585_init(const struct device *dev)
{
	const struct mfd_adp5585_config *config = dev->config;
	struct mfd_adp5585_data *data = dev->data;

	// Configure interrupt GPIO
	if (gpio_is_ready_dt(&config->nint_gpio)) {
		gpio_pin_configure_dt(&config->nint_gpio, GPIO_INPUT);
		gpio_pin_interrupt_configure_dt(&config->nint_gpio, GPIO_INT_EDGE_TO_ACTIVE);

		gpio_init_callback(&data->int_gpio_cb, mfd_adp5585_int_gpio_handler,
				   BIT(config->nint_gpio.pin));
		gpio_add_callback_dt(&config->nint_gpio, &data->int_gpio_cb);
	}

	// Store child device pointers
#ifdef CONFIG_GPIO_ADP5585
	data->child.gpio_dev = DEVICE_DT_GET(DT_INST_CHILD(0, gpio_controller));
#endif

	return 0;
}
```

**Pattern:**
1. Parent configures interrupt GPIO
2. Interrupt triggers work queue
3. Work handler reads interrupt status register
4. Work handler clears interrupt
5. Work handler calls child driver's IRQ handler function

### CRC/Checksum Support

Some devices (like MAX22017) support CRC for data integrity.

**From MAX22017** (`drivers/mfd/mfd_max22017.c`):

```c
struct max22017_config {
	struct spi_dt_spec spi;
	bool crc_mode;  // From devicetree
};

struct max22017_data {
	bool crc_enabled;  // Runtime state
};

int max22017_reg_write(const struct device *dev, uint8_t addr, uint16_t value)
{
	uint8_t crc;
	size_t crc_len = 0;
	const struct max22017_config *config = dev->config;
	const struct max22017_data *data = dev->data;

	addr = FIELD_PREP(MAX22017_SPI_TRANS_ADDR, addr) |
	       FIELD_PREP(MAX22017_SPI_TRANS_DIR, 0);
	value = sys_cpu_to_be16(value);

	if (data->crc_enabled) {
		uint8_t crc_in[] = {addr, ((uint8_t *)&value)[0], ((uint8_t *)&value)[1]};

		crc_len = 1;
		crc = crc8(crc_in, 3, MAX22017_CRC_POLY, 0, true);
	}

	const struct spi_buf buf[] = {
		{ .buf = &addr, .len = 1 },
		{ .buf = &value, .len = 2 },
		{ .buf = &crc, .len = crc_len },  // CRC byte appended if enabled
	};

	struct spi_buf_set tx = { .buffers = buf, .count = ARRAY_SIZE(buf) };

	return spi_write_dt(&config->spi, &tx);
}
```

### Power Management

MFD parent can implement power management callbacks affecting all children.

**Pattern** (not in current drivers, but recommended):

```c
#ifdef CONFIG_PM_DEVICE
static int mfd_xxx_pm_action(const struct device *dev, enum pm_device_action action)
{
	switch (action) {
	case PM_DEVICE_ACTION_SUSPEND:
		// Put device in low-power mode
		return mfd_xxx_write_reg(dev, POWER_CTRL_REG, POWER_MODE_SLEEP);
	case PM_DEVICE_ACTION_RESUME:
		// Wake device
		return mfd_xxx_write_reg(dev, POWER_CTRL_REG, POWER_MODE_ACTIVE);
	default:
		return -ENOTSUP;
	}
}

PM_DEVICE_DT_INST_DEFINE(0, mfd_xxx_pm_action);

DEVICE_DT_INST_DEFINE(0, mfd_xxx_init, PM_DEVICE_DT_INST_GET(0),
		      &data, &config,
		      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,
		      NULL);
#else
DEVICE_DT_INST_DEFINE(0, mfd_xxx_init, NULL,
		      &data, &config,
		      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,
		      NULL);
#endif
```

