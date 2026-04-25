## Driver Implementation Pattern

### Step 1: Define Register Map and Commands

From **drivers/dac/dac_ad56x1.c** (SPI-based 8/10/12-bit single-channel DAC):

```c
#define DT_DRV_COMPAT adi_ad5601  /* or adi_ad5611, adi_ad5621 */

#include <zephyr/drivers/dac.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/byteorder.h>

LOG_MODULE_REGISTER(dac_ad56x1, CONFIG_DAC_LOG_LEVEL);

/* Command/mode definitions */
#define DAC_AD56X1_MODE_NORMAL                 0x0000
#define DAC_AD56X1_MODE_POWER_DOWN_1K          0x4000
#define DAC_AD56X1_MODE_POWER_DOWN_100K        0x8000
#define DAC_AD56X1_MODE_POWER_DOWN_THREE_STATE 0xC000
```

From **drivers/dac/dac_ad559x.c** (MFD-based multi-channel DAC):

```c
#define DT_DRV_COMPAT adi_ad559x_dac

#include <zephyr/drivers/dac.h>
#include <zephyr/drivers/mfd/ad559x.h>

#define AD559X_DAC_RESOLUTION        12
#define AD559X_DAC_WR_POINTER        0x10
#define AD559X_DAC_WR_MSB_BIT        BIT(15)
#define AD559X_DAC_CHANNEL_SHIFT_VAL 12
```

### Step 2: Define Config and Data Structures

From **drivers/dac/dac_ad56x1.c** (standalone SPI):

```c
struct ad56x1_config {
	struct spi_dt_spec bus;  /* SPI bus specification */
	uint8_t resolution;      /* DAC resolution (8, 10, or 12 bits) */
};

/* No data structure needed for stateless single-channel DAC */
```

From **drivers/dac/dac_ad559x.c** (MFD multi-channel):

```c
struct dac_ad559x_config {
	const struct device *mfd_dev;    /* Parent MFD device */
	bool double_output_range;        /* 0-Vref or 0-2×Vref */
};

struct dac_ad559x_data {
	uint8_t dac_conf;  /* Cached channel enable bits */
};
```

**Pattern**:
- **Config structure**: Bus interface, resolution, hardware-specific settings
- **Data structure**: Runtime state, cached values (optional for simple DACs)

### Step 3: Implement channel_setup API

From **drivers/dac/dac_ad56x1.c** (single-channel validation):

```c
static int ad56x1_channel_setup(const struct device *dev,
                                const struct dac_channel_cfg *channel_cfg)
{
	const struct ad56x1_config *config = dev->config;

	/* Validate channel ID (single-channel DAC) */
	if (channel_cfg->channel_id != 0) {
		LOG_ERR("invalid channel %i", channel_cfg->channel_id);
		return -EINVAL;
	}

	/* Validate resolution matches hardware capability */
	if (channel_cfg->resolution != config->resolution) {
		LOG_ERR("invalid resolution %i", channel_cfg->resolution);
		return -EINVAL;
	}

	/* Check unsupported features */
	if (channel_cfg->internal) {
		LOG_ERR("Internal channels not supported");
		return -ENOTSUP;
	}

	/* No hardware configuration needed for this simple DAC */
	return 0;
}
```

From **drivers/dac/dac_ad559x.c** (multi-channel with LDAC enable):

```c
static int dac_ad559x_channel_setup(const struct device *dev,
                                    const struct dac_channel_cfg *channel_cfg)
{
	const struct dac_ad559x_config *config = dev->config;
	struct dac_ad559x_data *data = dev->data;

	/* Validate channel ID (multi-channel DAC) */
	if (channel_cfg->channel_id >= AD559X_PIN_MAX) {
		LOG_ERR("Invalid channel number %d", channel_cfg->channel_id);
		return -EINVAL;
	}

	/* Validate resolution */
	if (channel_cfg->resolution != AD559X_DAC_RESOLUTION) {
		LOG_ERR("Invalid resolution %d", channel_cfg->resolution);
		return -EINVAL;
	}

	/* Check unsupported features */
	if (channel_cfg->internal) {
		LOG_ERR("Internal channels not supported");
		return -ENOTSUP;
	}

	/* Enable LDAC (Load DAC) for this channel */
	data->dac_conf |= BIT(channel_cfg->channel_id);

	return mfd_ad559x_write_reg(config->mfd_dev, AD559X_REG_LDAC_EN, data->dac_conf);
}
```

**Common validation pattern**:
1. Validate channel ID
2. Validate resolution
3. Check for unsupported features
4. Configure hardware registers (if needed)

### Step 4: Implement write_value API

From **drivers/dac/dac_ad56x1.c** (SPI-based):

```c
static int ad56x1_write_value(const struct device *dev, uint8_t channel, uint32_t value)
{
	const struct ad56x1_config *config = dev->config;
	uint8_t buffer_tx[2];
	uint16_t command = DAC_AD56X1_MODE_NORMAL;
	int result;

	/* Validate value is within resolution range */
	if (value > BIT(config->resolution) - 1) {
		LOG_ERR("invalid value %i", value);
		return -EINVAL;
	}

	/* Validate channel */
	if (channel != 0) {
		LOG_ERR("invalid channel %i", channel);
		return -EINVAL;
	}

	/* Build SPI command: mode (2 bits) + value (14 bits, left-aligned) */
	command |= value << (14 - config->resolution);
	sys_put_be16(command, buffer_tx);  /* Convert to big-endian */

	/* Transmit via SPI */
	const struct spi_buf tx_buf[] = {{
		.buf = buffer_tx,
		.len = ARRAY_SIZE(buffer_tx),
	}};
	const struct spi_buf_set tx = {
		.buffers = tx_buf,
		.count = ARRAY_SIZE(tx_buf),
	};

	LOG_DBG("sending to DAC %s command 0x%02X, (value 0x%04X, normal mode)",
	        dev->name, command, value);

	result = spi_write_dt(&config->bus, &tx);
	if (result != 0) {
		LOG_ERR("spi_transceive failed with error %i", result);
		return result;
	}

	return 0;
}
```

From **drivers/dac/dac_ad559x.c** (MFD multi-channel):

```c
static int dac_ad559x_write_value(const struct device *dev, uint8_t channel, uint32_t value)
{
	const struct dac_ad559x_config *config = dev->config;
	uint16_t msg;

	/* Validate channel */
	if (channel >= AD559X_PIN_MAX) {
		LOG_ERR("Invalid channel number %d", channel);
		return -EINVAL;
	}

	/* Validate value */
	if (value >= (1 << AD559X_DAC_RESOLUTION)) {
		LOG_ERR("Value %d out of range", value);
		return -EINVAL;
	}

	/* Write via MFD parent device */
	/* Two methods: pointer-byte map or legacy format */
	if (mfd_ad559x_has_pointer_byte_map(config->mfd_dev)) {
		/* Method 1: Use pointer byte to select channel */
		return mfd_ad559x_write_reg(config->mfd_dev,
		                            AD559X_DAC_WR_POINTER | channel,
		                            value);
	} else {
		/* Method 2: Pack channel and value into 16-bit message */
		msg = sys_cpu_to_be16(AD559X_DAC_WR_MSB_BIT |
		                      channel << AD559X_DAC_CHANNEL_SHIFT_VAL | value);

		return mfd_ad559x_write_raw(config->mfd_dev, (uint8_t *)&msg, sizeof(msg));
	}
}
```

**Common write_value pattern**:
1. Validate channel and value
2. Format data for hardware (endianness, bit shifts)
3. Transmit via SPI/I2C/MFD
4. Return status

### Step 5: Implement Init Function

From **drivers/dac/dac_ad56x1.c** (simple SPI DAC):

```c
static int ad56x1_init(const struct device *dev)
{
	const struct ad56x1_config *config = dev->config;

	/* Check if SPI bus is ready */
	if (!spi_is_ready_dt(&config->bus)) {
		LOG_ERR("SPI bus %s not ready", config->bus.bus->name);
		return -ENODEV;
	}

	/* No additional initialization needed */
	return 0;
}
```

From **drivers/dac/dac_ad559x.c** (MFD with configuration):

```c
static int dac_ad559x_init(const struct device *dev)
{
	const struct dac_ad559x_config *config = dev->config;
	int ret;
	uint16_t reg_val;

	/* Check if parent MFD device is ready */
	if (!device_is_ready(config->mfd_dev)) {
		return -ENODEV;
	}

	/* Read current general control register */
	ret = mfd_ad559x_read_reg(config->mfd_dev, AD559X_REG_GEN_CTRL, 0, &reg_val);
	if (ret < 0) {
		return ret;
	}

	/* Configure output range (0-Vref or 0-2×Vref) */
	if (config->double_output_range) {
		reg_val |= AD559X_DAC_RANGE;
	} else {
		reg_val &= ~AD559X_DAC_RANGE;
	}

	ret = mfd_ad559x_write_reg(config->mfd_dev, AD559X_REG_GEN_CTRL, reg_val);
	if (ret < 0) {
		return ret;
	}

	/* Enable internal reference */
	ret = mfd_ad559x_write_reg(config->mfd_dev, AD559X_REG_PD_REF_CTRL, AD559X_EN_REF);
	if (ret < 0) {
		return ret;
	}

	return 0;
}
```

**Common init pattern**:
1. Check bus/parent device ready
2. Configure hardware settings (reference, range, modes)
3. Enable outputs or references
4. Return status

### Step 6: Define API Structure

From **drivers/dac/dac_ad56x1.c**:

```c
static DEVICE_API(dac, ad56x1_driver_api) = {
	.channel_setup = ad56x1_channel_setup,
	.write_value = ad56x1_write_value,
};
```

From **drivers/dac/dac_ad559x.c**:

```c
static DEVICE_API(dac, dac_ad559x_api) = {
	.channel_setup = dac_ad559x_channel_setup,
	.write_value = dac_ad559x_write_value,
};
```

### Step 7: Device Instantiation Macro

From **drivers/dac/dac_ad56x1.c** (multi-compatible support):

```c
BUILD_ASSERT(CONFIG_DAC_AD56X1_INIT_PRIORITY > CONFIG_SPI_INIT_PRIORITY,
             "CONFIG_DAC_AD56X1_INIT_PRIORITY must be higher than CONFIG_SPI_INIT_PRIORITY");

#define DAC_AD56X1_INST_DEFINE(index, name, res)                                   \
	static const struct ad56x1_config config_##name##_##index = {              \
		.bus = SPI_DT_SPEC_INST_GET(index,                                 \
		                            SPI_OP_MODE_MASTER | SPI_MODE_CPHA |    \
		                            SPI_WORD_SET(8)),                       \
		.resolution = res                                                   \
	};                                                                         \
	DEVICE_DT_INST_DEFINE(index, ad56x1_init, NULL, NULL,                      \
	                      &config_##name##_##index, POST_KERNEL,               \
	                      CONFIG_DAC_AD56X1_INIT_PRIORITY,                     \
	                      &ad56x1_driver_api);

/* Support multiple compatible strings with different resolutions */
#define DT_DRV_COMPAT adi_ad5601
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)
#define DAC_AD5601_RESOLUTION 8
DT_INST_FOREACH_STATUS_OKAY_VARGS(DAC_AD56X1_INST_DEFINE, DT_DRV_COMPAT, DAC_AD5601_RESOLUTION)
#endif
#undef DT_DRV_COMPAT

#define DT_DRV_COMPAT adi_ad5611
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)
#define DAC_AD5611_RESOLUTION 10
DT_INST_FOREACH_STATUS_OKAY_VARGS(DAC_AD56X1_INST_DEFINE, DT_DRV_COMPAT, DAC_AD5611_RESOLUTION)
#endif
#undef DT_DRV_COMPAT

#define DT_DRV_COMPAT adi_ad5621
#if DT_HAS_COMPAT_STATUS_OKAY(DT_DRV_COMPAT)
#define DAC_AD5621_RESOLUTION 12
DT_INST_FOREACH_STATUS_OKAY_VARGS(DAC_AD56X1_INST_DEFINE, DT_DRV_COMPAT, DAC_AD5621_RESOLUTION)
#endif
#undef DT_DRV_COMPAT
```

From **drivers/dac/dac_ad559x.c** (MFD child device):

```c
#define DAC_AD559X_DEFINE(inst)                                                    \
	static const struct dac_ad559x_config dac_ad559x_config##inst = {          \
		.mfd_dev = DEVICE_DT_GET(DT_INST_PARENT(inst)),                    \
		.double_output_range = DT_INST_PROP(inst, double_output_range),    \
	};                                                                         \
	                                                                           \
	struct dac_ad559x_data dac_ad559x_data##inst;                              \
	                                                                           \
	DEVICE_DT_INST_DEFINE(inst, dac_ad559x_init, NULL,                         \
	                      &dac_ad559x_data##inst,                              \
	                      &dac_ad559x_config##inst, POST_KERNEL,               \
	                      CONFIG_MFD_INIT_PRIORITY, &dac_ad559x_api);

DT_INST_FOREACH_STATUS_OKAY(DAC_AD559X_DEFINE)
```

**Key patterns**:
- **Standalone SPI/I2C**: Use `SPI_DT_SPEC_INST_GET()` or `I2C_DT_SPEC_INST_GET()`
- **MFD child**: Use `DEVICE_DT_GET(DT_INST_PARENT(inst))` for parent device
- **Multi-compatible**: Support multiple chip variants with different resolutions
- **Init priority**: Ensure DAC initializes after SPI/I2C/MFD

