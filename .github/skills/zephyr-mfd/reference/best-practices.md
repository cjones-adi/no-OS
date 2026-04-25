## Common Patterns and Best Practices

### 1. Bus Abstraction via Transfer Functions

**Good** – Use transfer function pointers:

```c
struct mfd_xxx_data *data = dev->data;
return data->transfer_function->write_reg(dev, reg, val);
```

**Bad** – Direct bus access in parent:

```c
// DON'T DO THIS - violates abstraction
if (on_i2c_bus) {
	return i2c_reg_write_byte_dt(...);
} else {
	return spi_write_dt(...);
}
```

**Why:** Transfer functions allow single parent driver to support multiple buses cleanly.

### 2. Parent Initialization Before Children

**Good** – MFD parent uses early init priority:

```c
DEVICE_DT_INST_DEFINE(inst, mfd_xxx_init, NULL,
		      &mfd_xxx_data_##inst,
		      &mfd_xxx_config_##inst,
		      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,  // Early priority
		      NULL);
```

Children use same or later priority:

```c
DEVICE_DT_INST_DEFINE(inst, dac_xxx_init, NULL,
		      &dac_xxx_data##inst,
		      &dac_xxx_config##inst,
		      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,  // Same as parent
		      &dac_xxx_api);
```

**Why:** Children call parent APIs in their init, so parent must initialize first. Zephyr initializes devices at same priority level in devicetree order (parent before children).

### 3. No Driver API for MFD Parent

**Good** – Parent has no driver API:

```c
DEVICE_DT_INST_DEFINE(inst, mfd_xxx_init, NULL,
		      &data, &config,
		      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,
		      NULL);  // No API structure
```

**Why:** MFD parent is infrastructure, not a controller. Children use parent via C function calls, not driver API structure.

### 4. Children Check Parent Ready

**Good** – Check parent in child init:

```c
static int dac_xxx_init(const struct device *dev)
{
	const struct dac_xxx_config *config = dev->config;

	if (!device_is_ready(config->mfd_dev)) {
		return -ENODEV;
	}

	// ... use parent APIs ...
}
```

**Bad** – Assume parent is ready:

```c
// DON'T DO THIS - parent might not be initialized
static int dac_xxx_init(const struct device *dev)
{
	const struct dac_xxx_config *config = dev->config;

	// Directly call parent API without checking ready
	mfd_xxx_write_reg(config->mfd_dev, reg, val);
}
```

### 5. Thread-Safe Register Access (If Needed)

**Good** – Parent provides mutex, children use it:

```c
// Parent data structure
struct mfd_xxx_data {
	struct k_mutex lock;
};

// Parent init
k_mutex_init(&data->lock);

// Child uses parent's lock
static int dac_xxx_write_value(const struct device *dev, uint8_t channel, uint32_t value)
{
	const struct dac_xxx_config *config = dev->config;
	const struct device *parent = config->mfd_dev;
	struct mfd_xxx_data *parent_data = parent->data;
	int ret;

	k_mutex_lock(&parent_data->lock, K_FOREVER);

	ret = mfd_xxx_write_reg(parent, reg1, val1);
	if (ret == 0) {
		ret = mfd_xxx_write_reg(parent, reg2, val2);
	}

	k_mutex_unlock(&parent_data->lock);
	return ret;
}
```

**When needed:**
- Child drivers from multiple threads
- Read-modify-write sequences must be atomic
- Parent register access is not inherently thread-safe

### 6. Device-Specific vs Generic Register Access

**Device-specific** (recommended for complex protocols):

```c
// Parent public API provides high-level functions
int mfd_ad559x_write_dac_chan(const struct device *dev, uint8_t channel, uint16_t value);
int mfd_ad559x_read_adc_chan(const struct device *dev, uint8_t channel, uint16_t *result);

// Child calls device-specific API
ret = mfd_ad559x_write_dac_chan(config->mfd_dev, channel, value);
```

**Generic** (simpler for register-based devices):

```c
// Parent provides generic register access
int mfd_xxx_read_reg(const struct device *dev, uint8_t reg, uint16_t *val);
int mfd_xxx_write_reg(const struct device *dev, uint8_t reg, uint16_t val);

// Child does protocol itself
ret = mfd_xxx_write_reg(config->mfd_dev, DAC_CH0_REG + channel, value);
```

**Trade-off:**
- **Device-specific**: Parent encapsulates complex protocol, children simpler, but parent grows
- **Generic**: Children handle protocol details, parent stays simple, children more complex

### 7. Conditional Multi-Bus Support

**Good** – Conditional compilation for bus support:

```c
struct mfd_xxx_config {
#if DT_ANY_INST_ON_BUS_STATUS_OKAY(i2c)
	struct i2c_dt_spec i2c;
#endif
#if DT_ANY_INST_ON_BUS_STATUS_OKAY(spi)
	struct spi_dt_spec spi;
#endif
	int (*bus_init)(const struct device *dev);
};

#define MFD_XXX_DEFINE_BUS(inst) \
	COND_CODE_1(DT_INST_ON_BUS(inst, i2c), \
		    (MFD_XXX_DEFINE_I2C_BUS(inst)), \
		    (MFD_XXX_DEFINE_SPI_BUS(inst)))
```

**Why:** Avoid including I2C or SPI headers if not used on any instance. Saves code space.

### 8. Reset Logic in Parent

**Good** – Parent handles all reset logic:

```c
static int mfd_xxx_init(const struct device *dev)
{
	const struct mfd_xxx_config *config = dev->config;
	int ret;

	// Bus init
	ret = config->bus_init(dev);
	if (ret < 0) {
		return ret;
	}

	// Hardware reset (if GPIO available)
	if (gpio_is_ready_dt(&config->reset_gpio)) {
		gpio_pin_configure_dt(&config->reset_gpio, GPIO_OUTPUT_INACTIVE);
		k_sleep(K_MSEC(100));
		gpio_pin_set_dt(&config->reset_gpio, 1);
		k_sleep(K_MSEC(500));
	}

	// Software reset (via register)
	ret = mfd_xxx_write_reg(dev, RESET_REG, RESET_MAGIC);

	return ret;
}
```

**Bad** – Children perform reset:

```c
// DON'T DO THIS - children shouldn't reset parent hardware
static int dac_xxx_init(const struct device *dev)
{
	const struct dac_xxx_config *config = dev->config;

	// Resetting in child driver - BAD!
	mfd_xxx_write_reg(config->mfd_dev, RESET_REG, RESET_MAGIC);
}
```

**Why:** Parent owns the hardware, should manage reset. Children might step on each other.

### 9. Child-Specific Configuration in Child Binding

**Good** – Child properties in child binding:

```yaml
# dts/bindings/dac/adi,ad559x-dac.yaml
description: AD559x DAC Controller

compatible: "adi,ad559x-dac"

properties:
  double-output-range:
    type: boolean
    description: Increase DAC range from 0-Vref to 0-2xVref
```

Devicetree:
```dts
ad559x_dac: dac-controller {
	compatible = "adi,ad559x-dac";
	double-output-range;  // Child-specific property
};
```

**Bad** – Child properties in parent binding:

```yaml
# DON'T DO THIS
# dts/bindings/mfd/adi,ad559x.yaml
properties:
  dac-double-output-range:  # BAD - DAC-specific in parent
    type: boolean
```

**Why:** Child properties belong to child bindings for modularity.

### 10. Separate Bus-Specific Code into Files

**Good** – Dedicated files for I2C and SPI:

```
drivers/mfd/
  mfd_xxx.c         # Core parent driver
  mfd_xxx.h         # Private header
  mfd_xxx_i2c.c     # I2C-specific implementation
  mfd_xxx_spi.c     # SPI-specific implementation
```

**Bad** – All bus code in single file with ifdefs:

```c
// DON'T DO THIS - messy single file
#ifdef CONFIG_I2C
static int mfd_xxx_i2c_read_reg(...) { ... }
#endif

#ifdef CONFIG_SPI
static int mfd_xxx_spi_read_reg(...) { ... }
#endif
```

**Why:** Separate files are cleaner, easier to review, and compile conditionally based on bus usage.

