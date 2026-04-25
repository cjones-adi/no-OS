## Driver Implementation Pattern

### Part 1: MFD Parent Driver

#### Step 1: Define Register Map and Bit Masks

**From AD559x** (`include/zephyr/drivers/mfd/ad559x.h`):

```c
#define AD559X_REG_SEQ_ADC        0x02U
#define AD559X_REG_GEN_CTRL       0x03U
#define AD559X_REG_ADC_CONFIG     0x04U
#define AD559X_REG_LDAC_EN        0x05U
#define AD559X_REG_GPIO_PULLDOWN  0x06U
#define AD559X_REG_READ_AND_LDAC  0x07U
#define AD559X_REG_GPIO_OUTPUT_EN 0x08U
#define AD559X_REG_GPIO_SET       0x09U
#define AD559X_REG_GPIO_INPUT_EN  0x0AU
#define AD559X_REG_PD_REF_CTRL    0x0BU
#define AD559X_REG_IO_TS_CONFIG   0x0DU

#define AD559X_DAC_RANGE BIT(4)
#define AD559X_ADC_RANGE BIT(5)
#define AD559X_EN_REF    BIT(9)

#define AD559X_PIN_MAX 8U
```

**From MAX22017** (`include/zephyr/drivers/mfd/max22017.h`):

```c
#define MAX22017_GEN_CNFG_OFF                0x03
#define MAX22017_GEN_CNFG_OPENWIRE_DTCT_CNFG GENMASK(15, 14)
#define MAX22017_GEN_CNFG_TMOUT_SEL          GENMASK(13, 10)
#define MAX22017_GEN_CNFG_TMOUT_CNFG         BIT(9)
#define MAX22017_GEN_CNFG_TMOUT_EN           BIT(8)
#define MAX22017_GEN_CNFG_CRC_EN             BIT(1)
#define MAX22017_GEN_CNFG_DACREF_SEL         BIT(0)

#define MAX22017_AO_CMD_OFF        0x40
#define MAX22017_AO_CMD_AO_LD_CTRL GENMASK(15, 14)
```

**Best practices:**
- Define all registers in public header (children need access)
- Use `GENMASK()` for multi-bit fields
- Use `BIT()` for single-bit flags
- Group related registers with comments

#### Step 2: Define Transfer Function Structure

**From AD559x** (`drivers/mfd/mfd_ad559x.h`):

```c
struct mfd_ad559x_transfer_function {
	int (*read_raw)(const struct device *dev, uint8_t *val, size_t len);
	int (*write_raw)(const struct device *dev, uint8_t *val, size_t len);
	int (*read_reg)(const struct device *dev, uint8_t reg, uint8_t reg_data, uint16_t *val);
	int (*write_reg)(const struct device *dev, uint8_t reg, uint16_t val);
};
```

**Function pointer meanings:**
- **read_raw / write_raw** – Raw buffer transfer (for custom protocols)
- **read_reg / write_reg** – Register-level access (most common)

#### Step 3: Define Config and Data Structures

**Config** (compile-time, from devicetree):

```c
struct mfd_ad559x_config {
	struct gpio_dt_spec reset_gpio;
#if DT_ANY_INST_ON_BUS_STATUS_OKAY(i2c)
	struct i2c_dt_spec i2c;
#endif
#if DT_ANY_INST_ON_BUS_STATUS_OKAY(spi)
	struct spi_dt_spec spi;
#endif
	int (*bus_init)(const struct device *dev);
	bool has_pointer_byte_map;
};
```

**Data** (runtime state):

```c
struct mfd_ad559x_data {
	const struct mfd_ad559x_transfer_function *transfer_function;
};
```

**With locking** (for multi-threaded access):

```c
struct max22017_data {
	struct k_mutex lock;
	bool crc_enabled;
};
```

#### Step 4: Implement Public API Functions

These functions are called by child drivers. They forward to the transfer function.

**From AD559x** (`drivers/mfd/mfd_ad559x.c`):

```c
int mfd_ad559x_read_reg(const struct device *dev, uint8_t reg, uint8_t reg_data, uint16_t *val)
{
	struct mfd_ad559x_data *data = dev->data;

	return data->transfer_function->read_reg(dev, reg, reg_data, val);
}

int mfd_ad559x_write_reg(const struct device *dev, uint8_t reg, uint16_t val)
{
	struct mfd_ad559x_data *data = dev->data;

	return data->transfer_function->write_reg(dev, reg, val);
}
```

**With locking** (from MAX22017):

```c
int max22017_reg_read(const struct device *dev, uint8_t addr, uint16_t *value)
{
	const struct max22017_config *config = dev->config;
	const struct max22017_data *data = dev->data;

	// SPI transaction with CRC if enabled
	// ...
	return 0;
}

int max22017_reg_write(const struct device *dev, uint8_t addr, uint16_t value)
{
	const struct max22017_config *config = dev->config;
	const struct max22017_data *data = dev->data;

	// SPI transaction with CRC if enabled
	// ...
	return 0;
}
```

**Child-specific helpers** (optional, from AD559x):

```c
int mfd_ad559x_read_adc_chan(const struct device *dev, uint8_t channel, uint16_t *result)
{
	// Helper specifically for ADC child driver
	// Implements ADC-specific protocol
	// ...
}

int mfd_ad559x_write_dac_chan(const struct device *dev, uint8_t channel, uint16_t value)
{
	// Helper specifically for DAC child driver
	// ...
}

int mfd_ad559x_gpio_port_get_raw(const struct device *dev, uint8_t gpio, uint16_t *value)
{
	// Helper specifically for GPIO child driver
	// ...
}
```

#### Step 5: Implement Init Function

**From AD559x** (`drivers/mfd/mfd_ad559x.c`):

```c
static int mfd_add559x_software_reset(const struct device *dev)
{
	return mfd_ad559x_write_reg(dev, AD559X_REG_SOFTWARE_RESET,
				    AD559X_SOFTWARE_RESET_MAGIC_VAL);
}

static int mfd_ad559x_init(const struct device *dev)
{
	const struct mfd_ad559x_config *config = dev->config;
	int ret;

	// 1. Initialize communication bus (I2C or SPI)
	ret = config->bus_init(dev);
	if (ret < 0) {
		return ret;
	}

	// 2. Configure reset GPIO
	if (!gpio_is_ready_dt(&config->reset_gpio)) {
		return -ENODEV;
	}

	ret = gpio_pin_configure_dt(&config->reset_gpio, GPIO_OUTPUT_INACTIVE);
	if (ret < 0) {
		return ret;
	}

	// 3. Perform software reset
	ret = mfd_add559x_software_reset(dev);
	if (ret < 0) {
		return ret;
	}

	return 0;
}
```

**From MAX22017** (with hardware reset):

```c
static int max22017_reset(const struct device *dev)
{
	const struct max22017_config *config = dev->config;

	if (config->gpio_reset.port != NULL) {
		// Hardware reset via GPIO
		gpio_pin_set_dt(&config->gpio_reset, 0);
		k_sleep(K_MSEC(100));
		gpio_pin_set_dt(&config->gpio_reset, 1);
		k_sleep(K_MSEC(500));
	} else {
		// Software reset via register
		max22017_reg_write(dev, MAX22017_GEN_RST_CTRL_OFF,
				   FIELD_PREP(MAX22017_GEN_RST_CTRL_GEN_RST, 1));
	}
	return 0;
}

static int max22017_init(const struct device *dev)
{
	const struct max22017_config *config = dev->config;
	struct max22017_data *data = dev->data;

	// Initialize mutex
	k_mutex_init(&data->lock);

	// Check SPI bus ready
	if (!spi_is_ready_dt(&config->spi)) {
		return -ENODEV;
	}

	// Configure GPIO pins
	if (config->gpio_reset.port != NULL) {
		gpio_pin_configure_dt(&config->gpio_reset, GPIO_OUTPUT_ACTIVE);
	}

	// Perform reset
	return max22017_reset(dev);
}
```

#### Step 6: Device Instantiation Macro

**Single-bus pattern** (from MAX22017 - SPI only):

```c
#define MFD_MAX22017_DEFINE(inst)                                         \
	static struct max22017_data max22017_data_##inst = {              \
		.lock = Z_MUTEX_INITIALIZER(max22017_data_##inst.lock),   \
	};                                                                \
	static const struct max22017_config max22017_config_##inst = {    \
		.spi = SPI_DT_SPEC_INST_GET(                              \
			inst, SPI_WORD_SET(8) | SPI_TRANSFER_MSB, 0),     \
		.gpio_reset = GPIO_DT_SPEC_INST_GET_OR(inst, reset_gpios, {0}), \
		.gpio_int = GPIO_DT_SPEC_INST_GET_OR(inst, int_gpios, {0}),    \
		.crc_mode = DT_INST_PROP(inst, crc_mode),                 \
	};                                                                \
	DEVICE_DT_INST_DEFINE(inst, max22017_init, NULL,                  \
			      &max22017_data_##inst,                      \
			      &max22017_config_##inst,                    \
			      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,      \
			      NULL);

DT_INST_FOREACH_STATUS_OKAY(MFD_MAX22017_DEFINE)
```

**Multi-bus pattern** (from AD559x - I2C and SPI support):

```c
#define MDF_AD559X_DEFINE_I2C_BUS(inst)                             \
	.i2c = I2C_DT_SPEC_INST_GET(inst),                          \
	.bus_init = mfd_ad559x_i2c_init,                            \
	.has_pointer_byte_map = true

#define MDF_AD559X_DEFINE_SPI_BUS_FLAGS                              \
	(SPI_WORD_SET(8) | SPI_TRANSFER_MSB | SPI_OP_MODE_MASTER |  \
	 SPI_MODE_CPOL)

#define MDF_AD559X_DEFINE_SPI_BUS(inst)                             \
	.spi = SPI_DT_SPEC_INST_GET(inst, MDF_AD559X_DEFINE_SPI_BUS_FLAGS), \
	.bus_init = mfd_ad559x_spi_init,                            \
	.has_pointer_byte_map = false

#define MFD_AD559X_DEFINE_BUS(inst)                                 \
	COND_CODE_1(DT_INST_ON_BUS(inst, i2c),                      \
		    (MDF_AD559X_DEFINE_I2C_BUS(inst)),               \
		    (MDF_AD559X_DEFINE_SPI_BUS(inst)))

#define MFD_AD559X_DEFINE(inst)                                     \
	static struct mfd_ad559x_data mfd_ad559x_data_##inst;       \
	static const struct mfd_ad559x_config mfd_ad559x_config_##inst = { \
		.reset_gpio = GPIO_DT_SPEC_INST_GET(inst, reset_gpios), \
		MFD_AD559X_DEFINE_BUS(inst),                         \
	};                                                           \
	DEVICE_DT_INST_DEFINE(inst, mfd_ad559x_init, NULL,          \
			      &mfd_ad559x_data_##inst,               \
			      &mfd_ad559x_config_##inst,             \
			      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY, \
			      NULL);

DT_INST_FOREACH_STATUS_OKAY(MFD_AD559X_DEFINE)
```

**Key points:**
- No driver API structure (NULL in `DEVICE_DT_INST_DEFINE`) – MFD parent is infrastructure, not a controller
- Init priority: `CONFIG_MFD_INIT_PRIORITY` (must initialize before children)
- Multi-bus support uses `COND_CODE_1()` and `DT_INST_ON_BUS()`

### Part 2: Bus-Specific Implementations

#### I2C Implementation

**From AD559x** (`drivers/mfd/mfd_ad559x_i2c.c`):

```c
static int mfd_ad559x_i2c_read_raw(const struct device *dev, uint8_t *val, size_t len)
{
	const struct mfd_ad559x_config *config = dev->config;

	return i2c_read_dt(&config->i2c, val, len);
}

static int mfd_ad559x_i2c_write_raw(const struct device *dev, uint8_t *val, size_t len)
{
	const struct mfd_ad559x_config *config = dev->config;

	return i2c_write_dt(&config->i2c, val, len);
}

static int mfd_ad559x_i2c_read_reg(const struct device *dev, uint8_t reg, uint8_t reg_data,
				   uint16_t *val)
{
	const struct mfd_ad559x_config *config = dev->config;
	uint8_t buf[sizeof(*val)];
	int ret;

	ARG_UNUSED(reg_data);

	// AD559x I2C uses read pointer register
	if (reg >= AD559X_REG_SEQ_ADC || reg <= AD559X_REG_IO_TS_CONFIG) {
		reg |= AD559X_REG_RD_POINTER;
	}

	ret = i2c_write_read_dt(&config->i2c, &reg, sizeof(reg), buf, sizeof(buf));
	if (ret < 0) {
		return ret;
	}

	*val = sys_get_be16(buf);

	return 0;
}

static int mfd_ad559x_i2c_write_reg(const struct device *dev, uint8_t reg, uint16_t val)
{
	uint8_t buf[sizeof(reg) + sizeof(val)];

	buf[0] = reg;
	sys_put_be16(val, &buf[1]);

	return mfd_ad559x_i2c_write_raw(dev, buf, sizeof(buf));
}

static const struct mfd_ad559x_transfer_function mfd_ad559x_i2c_transfer_function = {
	.read_raw = mfd_ad559x_i2c_read_raw,
	.write_raw = mfd_ad559x_i2c_write_raw,
	.read_reg = mfd_ad559x_i2c_read_reg,
	.write_reg = mfd_ad559x_i2c_write_reg,
};

int mfd_ad559x_i2c_init(const struct device *dev)
{
	const struct mfd_ad559x_config *config = dev->config;
	struct mfd_ad559x_data *data = dev->data;

	// Set transfer function pointer to I2C implementation
	data->transfer_function = &mfd_ad559x_i2c_transfer_function;

	// Check I2C bus ready
	if (!i2c_is_ready_dt(&config->i2c)) {
		return -ENODEV;
	}

	return 0;
}
```

#### SPI Implementation

**From AD559x** (`drivers/mfd/mfd_ad559x_spi.c`):

```c
static int mfd_ad559x_spi_read_raw(const struct device *dev, uint8_t *val, size_t len)
{
	const struct mfd_ad559x_config *config = dev->config;
	uint16_t nop_msg = 0;

	struct spi_buf tx_buf[] = {{.buf = &nop_msg, .len = sizeof(nop_msg)}};
	const struct spi_buf_set tx = {.buffers = tx_buf, .count = 1};

	struct spi_buf rx_buf[] = {{.buf = val, .len = len}};
	const struct spi_buf_set rx = {.buffers = rx_buf, .count = 1};

	return spi_transceive_dt(&config->spi, &tx, &rx);
}

static int mfd_ad559x_spi_write_raw(const struct device *dev, uint8_t *val, size_t len)
{
	const struct mfd_ad559x_config *config = dev->config;

	struct spi_buf tx_buf[] = {{.buf = val, .len = len}};
	const struct spi_buf_set tx = {.buffers = tx_buf, .count = 1};

	return spi_write_dt(&config->spi, &tx);
}

static int mfd_ad559x_spi_read_reg(const struct device *dev, uint8_t reg, uint8_t reg_data,
				   uint16_t *val)
{
	uint16_t data;
	uint16_t msg;
	int ret;

	switch (reg) {
	case AD559X_REG_GPIO_INPUT_EN:
		msg = sys_cpu_to_be16(AD559X_GPIO_READBACK_EN |
				      (AD559X_REG_GPIO_INPUT_EN << AD559X_REG_SHIFT_VAL) |
				      reg_data);
		break;
	default:
		msg = sys_cpu_to_be16(AD559X_LDAC_READBACK_EN |
				      (AD559X_REG_READ_AND_LDAC << AD559X_REG_SHIFT_VAL) |
				      reg << AD559X_REG_READBACK_SHIFT_VAL);
		break;
	}

	ret = mfd_ad559x_spi_write_raw(dev, (uint8_t *)&msg, sizeof(msg));
	if (ret < 0) {
		return ret;
	}

	ret = mfd_ad559x_spi_read_raw(dev, (uint8_t *)&data, sizeof(data));
	if (ret < 0) {
		return ret;
	}

	*val = sys_be16_to_cpu(data);

	return 0;
}

static int mfd_ad559x_spi_write_reg(const struct device *dev, uint8_t reg, uint16_t val)
{
	uint16_t write_mask;
	uint16_t msg;

	switch (reg) {
	case AD559X_REG_SOFTWARE_RESET:
		write_mask = AD559X_REG_RESET_VAL_MASK;
		break;
	default:
		write_mask = AD559X_REG_VAL_MASK;
		break;
	}

	msg = sys_cpu_to_be16((reg << AD559X_REG_SHIFT_VAL) | (val & write_mask));

	return mfd_ad559x_spi_write_raw(dev, (uint8_t *)&msg, sizeof(msg));
}

static const struct mfd_ad559x_transfer_function mfd_ad559x_spi_transfer_function = {
	.read_raw = mfd_ad559x_spi_read_raw,
	.write_raw = mfd_ad559x_spi_write_raw,
	.read_reg = mfd_ad559x_spi_read_reg,
	.write_reg = mfd_ad559x_spi_write_reg,
};

int mfd_ad559x_spi_init(const struct device *dev)
{
	const struct mfd_ad559x_config *config = dev->config;
	struct mfd_ad559x_data *data = dev->data;

	// Set transfer function pointer to SPI implementation
	data->transfer_function = &mfd_ad559x_spi_transfer_function;

	// Check SPI bus ready
	if (!spi_is_ready_dt(&config->spi)) {
		return -ENODEV;
	}

	return 0;
}
```

**Key differences I2C vs SPI:**
- **I2C**: Register address in write, combined write-read for register read
- **SPI**: Command encoding in data (register address + R/W bit in message)
- **Byte order**: I2C often little-endian, SPI often big-endian (device-specific)

### Part 3: Child Driver Implementation

Child drivers reference their MFD parent and call parent APIs for register access.

#### Child Config Structure

**From DAC AD559x** (`drivers/dac/dac_ad559x.c`):

```c
#define DT_DRV_COMPAT adi_ad559x_dac

struct dac_ad559x_config {
	const struct device *mfd_dev;  // Parent device pointer
	bool double_output_range;      // Child-specific config from devicetree
};

struct dac_ad559x_data {
	uint8_t dac_conf;  // Child-specific runtime state
};
```

**From DAC MAX22017** (`drivers/dac/dac_max22017.c`):

```c
#define DT_DRV_COMPAT adi_max22017_dac

struct dac_adi_max22017_config {
	const struct device *parent;   // Parent device pointer
	uint8_t resolution;
	uint8_t nchannels;
	const struct gpio_dt_spec gpio_ldac;
	const struct gpio_dt_spec gpio_busy;
	uint8_t latch_mode[MAX22017_MAX_CHANNEL];
	uint8_t polarity_mode[MAX22017_MAX_CHANNEL];
	uint8_t dac_mode[MAX22017_MAX_CHANNEL];
	uint8_t ovc_mode[MAX22017_MAX_CHANNEL];
	uint16_t timeout;
};
```

#### Child API Implementation

**Channel Setup** (from DAC AD559x):

```c
static int dac_ad559x_channel_setup(const struct device *dev,
				    const struct dac_channel_cfg *channel_cfg)
{
	const struct dac_ad559x_config *config = dev->config;
	struct dac_ad559x_data *data = dev->data;

	if (channel_cfg->channel_id >= AD559X_PIN_MAX) {
		LOG_ERR("Invalid channel number %d", channel_cfg->channel_id);
		return -EINVAL;
	}

	if (channel_cfg->resolution != AD559X_DAC_RESOLUTION) {
		LOG_ERR("Invalid resolution %d", channel_cfg->resolution);
		return -EINVAL;
	}

	if (channel_cfg->internal) {
		LOG_ERR("Internal channels not supported");
		return -ENOTSUP;
	}

	data->dac_conf |= BIT(channel_cfg->channel_id);

	// Call parent API to write register
	return mfd_ad559x_write_reg(config->mfd_dev, AD559X_REG_LDAC_EN, data->dac_conf);
}
```

**Write Value** (from DAC AD559x):

```c
static int dac_ad559x_write_value(const struct device *dev, uint8_t channel, uint32_t value)
{
	const struct dac_ad559x_config *config = dev->config;
	uint16_t msg;

	if (channel >= AD559X_PIN_MAX) {
		LOG_ERR("Invalid channel number %d", channel);
		return -EINVAL;
	}

	if (value >= (1 << AD559X_DAC_RESOLUTION)) {
		LOG_ERR("Value %d out of range", value);
		return -EINVAL;
	}

	// Check if I2C or SPI variant (different protocols)
	if (mfd_ad559x_has_pointer_byte_map(config->mfd_dev)) {
		// I2C variant - use write_reg
		return mfd_ad559x_write_reg(config->mfd_dev,
		                            AD559X_DAC_WR_POINTER | channel,
					    value);
	} else {
		// SPI variant - use write_raw with encoded message
		msg = sys_cpu_to_be16(AD559X_DAC_WR_MSB_BIT |
				      channel << AD559X_DAC_CHANNEL_SHIFT_VAL | value);

		return mfd_ad559x_write_raw(config->mfd_dev, (uint8_t *)&msg, sizeof(msg));
	}
}
```

**With locking** (from DAC MAX22017):

```c
static int max22017_channel_setup(const struct device *dev,
				  const struct dac_channel_cfg *channel_cfg)
{
	const struct dac_adi_max22017_config *config = dev->config;
	const struct device *parent = config->parent;
	struct max22017_data *data = parent->data;  // Get parent's data for mutex
	uint16_t ao_cnfg, gen_cnfg;
	uint8_t chan = channel_cfg->channel_id;
	int ret;

	if (chan > config->nchannels - 1) {
		return -ENOTSUP;
	}

	// Take parent's lock before register access
	k_mutex_lock(&data->lock, K_FOREVER);

	// Read-modify-write using parent APIs
	ret = max22017_reg_read(parent, MAX22017_AO_CNFG_OFF, &ao_cnfg);
	if (ret) {
		goto fail;
	}

	ao_cnfg |= FIELD_PREP(MAX22017_AO_CNFG_AO_EN, BIT(chan));

	ret = max22017_reg_write(parent, MAX22017_AO_CNFG_OFF, ao_cnfg);
	if (ret) {
		goto fail;
	}

	// ... more configuration ...

fail:
	k_mutex_unlock(&data->lock);
	return ret;
}
```

#### Child Init Function

**From DAC AD559x**:

```c
static int dac_ad559x_init(const struct device *dev)
{
	const struct dac_ad559x_config *config = dev->config;
	int ret;
	uint16_t reg_val;

	// 1. Check parent device is ready
	if (!device_is_ready(config->mfd_dev)) {
		return -ENODEV;
	}

	// 2. Read current configuration from parent
	ret = mfd_ad559x_read_reg(config->mfd_dev, AD559X_REG_GEN_CTRL, 0, &reg_val);
	if (ret < 0) {
		return ret;
	}

	// 3. Configure child-specific settings
	if (config->double_output_range) {
		reg_val |= AD559X_DAC_RANGE;
	} else {
		reg_val &= ~AD559X_DAC_RANGE;
	}

	ret = mfd_ad559x_write_reg(config->mfd_dev, AD559X_REG_GEN_CTRL, reg_val);
	if (ret < 0) {
		return ret;
	}

	// 4. Enable internal reference
	ret = mfd_ad559x_write_reg(config->mfd_dev, AD559X_REG_PD_REF_CTRL, AD559X_EN_REF);
	if (ret < 0) {
		return ret;
	}

	return 0;
}
```

**From ADC AD559x**:

```c
static int adc_ad559x_init(const struct device *dev)
{
	const struct adc_ad559x_config *config = dev->config;
	struct adc_ad559x_data *data = dev->data;
	int ret;
	uint16_t reg_val;

	data->dev = dev;

	// Check parent ready
	if (!device_is_ready(config->mfd_dev)) {
		return -ENODEV;
	}

	// Initialize ADC context (for async operation)
	adc_context_init(&data->ctx);

	// Configure ADC range
	ret = mfd_ad559x_read_reg(config->mfd_dev, AD559X_REG_GEN_CTRL, 0, &reg_val);
	if (ret < 0) {
		return ret;
	}

	if (config->double_input_range) {
		reg_val |= AD559X_ADC_RANGE;
	} else {
		reg_val &= ~AD559X_ADC_RANGE;
	}

	ret = mfd_ad559x_write_reg(config->mfd_dev, AD559X_REG_GEN_CTRL, reg_val);
	if (ret < 0) {
		return ret;
	}

	// ... more init ...

	return 0;
}
```

#### Child Device Instantiation

**From DAC AD559x**:

```c
#define DAC_AD559X_DEFINE(inst)                                          \
	static const struct dac_ad559x_config dac_ad559x_config##inst = { \
		.mfd_dev = DEVICE_DT_GET(DT_INST_PARENT(inst)),           \
		.double_output_range = DT_INST_PROP(inst, double_output_range), \
	};                                                                \
                                                                          \
	struct dac_ad559x_data dac_ad559x_data##inst;                     \
                                                                          \
	DEVICE_DT_INST_DEFINE(inst, dac_ad559x_init, NULL,                \
			      &dac_ad559x_data##inst,                     \
			      &dac_ad559x_config##inst,                   \
			      POST_KERNEL, CONFIG_MFD_INIT_PRIORITY,      \
			      &dac_ad559x_api);

DT_INST_FOREACH_STATUS_OKAY(DAC_AD559X_DEFINE)
```

**Key points:**
- Use `DT_INST_PARENT(inst)` to get parent device
- Child init priority: `CONFIG_MFD_INIT_PRIORITY` (same as parent, children init after parent)
- Child provides driver API structure (e.g., `&dac_ad559x_api`)

