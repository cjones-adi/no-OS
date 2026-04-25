## Driver Implementation Pattern

### Step 1: Define Register Map and Bit Masks

From **drivers/adc/adc_ad4114.c** (24-bit Sigma-Delta ADC):

```c
#define DT_DRV_COMPAT adi_ad4114_adc

#define AD4114_CMD_READ       0x40
#define AD4114_CMD_WRITE      0x0
#define AD4114_CHAN_NUMBER    16
#define AD4114_ADC_RESOLUTION 24U

enum ad4114_reg {
	AD4114_STATUS_REG = 0x00,
	AD4114_MODE_REG = 0x01,
	AD4114_IFMODE_REG = 0x02,
	AD4114_DATA_REG = 0x04,
	AD4114_ID_REG = 0x07,
	AD4114_CHANNEL_0_REG = 0x10,
	AD4114_SETUPCON0_REG = 0x20,
	AD4114_FILTCON0_REG = 0x28,
	AD4114_OFFSET0_REG = 0x30,
	AD4114_GAIN0_REG = 0x38,
	/* ... channels 1-15 registers ... */
};
```

### Step 2: Define Config and Data Structures

From **drivers/adc/adc_ad4114.c**:

```c
struct adc_ad4114_config {
	struct spi_dt_spec spi;          /* SPI bus specification */
	uint16_t resolution;             /* ADC resolution (bits) */
	uint16_t map_input[AD4114_CHAN_NUMBER]; /* Channel input mapping */
};

struct adc_ad4114_data {
	struct adc_context ctx;          /* ADC context (Zephyr helper) */
	const struct device *dev;
	struct k_thread thread;
	struct k_sem sem;
	uint16_t channels;               /* Active channels */
	uint16_t channels_cfg;           /* Configured channels */
	uint32_t *buffer;                /* Output buffer */
	uint32_t *repeat_buffer;

	K_KERNEL_STACK_MEMBER(stack, CONFIG_ADC_AD4114_ACQUISITION_THREAD_STACK_SIZE);
};
```

**Key pattern**: Use `struct adc_context` to simplify async/sync operation handling.

### Step 3: Implement Register Read/Write Functions

From **drivers/adc/adc_ad4114.c** (SPI example):

```c
static int ad4114_write_reg(const struct device *dev, enum ad4114_reg reg_addr,
                            uint8_t *buffer, size_t reg_size)
{
	const struct adc_ad4114_config *config = dev->config;
	uint8_t buffer_tx[5] = {0}; /* 1 byte command + max 4 bytes data */

	const struct spi_buf tx_buf[] = {{
		.buf = buffer_tx,
		.len = ARRAY_SIZE(buffer_tx),
	}};
	const struct spi_buf_set tx = {
		.buffers = tx_buf,
		.count = ARRAY_SIZE(tx_buf),
	};

	buffer_tx[0] = AD4114_CMD_WRITE | reg_addr;

	/* Fill data bytes */
	for (uint8_t i = 0; i < reg_size; i++) {
		buffer_tx[1 + i] = buffer[i];
	}

	return spi_write_dt(&config->spi, &tx);
}

static int ad4114_read_reg(const struct device *dev, enum ad4114_reg reg_addr,
                           uint8_t *buffer, size_t reg_size)
{
	const struct adc_ad4114_config *config = dev->config;
	uint8_t buffer_tx[6] = {0};
	uint8_t buffer_rx[6] = {0xFF};

	const struct spi_buf tx_buf[] = {{ .buf = buffer_tx, .len = ARRAY_SIZE(buffer_tx) }};
	const struct spi_buf rx_buf[] = {{ .buf = buffer_rx, .len = ARRAY_SIZE(buffer_rx) }};
	const struct spi_buf_set tx = { .buffers = tx_buf, .count = ARRAY_SIZE(tx_buf) };
	const struct spi_buf_set rx = { .buffers = rx_buf, .count = ARRAY_SIZE(rx_buf) };

	buffer_tx[0] = AD4114_CMD_READ | reg_addr;

	int ret = spi_transceive_dt(&config->spi, &tx, &rx);

	/* Copy received data (skip command byte) */
	for (uint8_t i = 0; i < reg_size; i++) {
		buffer[i] = buffer_rx[i + 1];
	}

	return ret;
}
```

### Step 4: Implement channel_setup API

From **drivers/adc/adc_ad4114.c**:

```c
static int adc_ad4114_channel_setup(const struct device *dev,
                                    const struct adc_channel_cfg *channel_cfg)
{
	/* Validate channel ID */
	if (channel_cfg->channel_id >= AD4114_CHAN_NUMBER) {
		LOG_ERR("invalid channel id %d", channel_cfg->channel_id);
		return -EINVAL;
	}

	/* TODO: Configure per-channel settings:
	 *  - Gain (channel_cfg->gain)
	 *  - Reference (channel_cfg->reference)
	 *  - Differential mode (channel_cfg->differential)
	 *  - Input pins (channel_cfg->input_positive/negative)
	 *  - Filter settings
	 */

	return 0;
}
```

**Advanced example** from **drivers/adc/adc_ad7124.c** with full configuration:

```c
static int ad7124_channel_setup(const struct device *dev,
                                const struct adc_channel_cfg *channel_cfg)
{
	const struct ad7124_config *cfg = dev->config;
	struct ad7124_data *data = dev->data;
	uint8_t ch = channel_cfg->channel_id;

	/* Validate channel */
	if (ch >= AD7124_MAX_CHANNELS) {
		return -EINVAL;
	}

	/* Map gain to hardware value */
	uint8_t pga = ad7124_gain_to_pga(channel_cfg->gain);

	/* Configure channel input selection */
	uint16_t channel_reg = AD7124_CH_MAP_REG_CH_ENABLE |
	                       (cfg->input_positive[ch] << 5) |
	                       (cfg->input_negative[ch] << 0) |
	                       (cfg->setup_sel[ch] << 12);

	ad7124_write_register(dev, AD7124_CHANNEL(ch), channel_reg);

	/* Configure setup register (PGA, reference, buffers) */
	uint16_t setup_reg = (pga << 0) |
	                     (ad7124_ref_sel(channel_cfg->reference) << 3) |
	                     AD7124_CFG_REG_AIN_BUFP | AD7124_CFG_REG_AINN_BUFM;

	if (channel_cfg->differential) {
		setup_reg |= AD7124_CFG_REG_BIPOLAR;
	}

	ad7124_write_register(dev, AD7124_CONFIG(cfg->setup_sel[ch]), setup_reg);

	data->channel_enabled[ch] = true;

	return 0;
}
```

### Step 5: Implement read API (Synchronous)

From **drivers/adc/adc_ad4114.c**:

```c
static int adc_ad4114_start_read(const struct device *dev,
                                 const struct adc_sequence *sequence)
{
	struct adc_ad4114_data *data = dev->data;
	const struct adc_ad4114_config *config = dev->config;
	uint8_t write_reg[2];
	uint8_t status;

	/* Validate buffer size */
	uint8_t num_channels = POPCOUNT(sequence->channels);
	size_t needed = num_channels * sizeof(uint32_t);

	if (sequence->buffer_size < needed) {
		LOG_ERR("insufficient buffer size");
		return -ENOMEM;
	}

	/* Enable selected channels */
	data->channels_cfg = sequence->channels;
	for (uint32_t i = 0U; i < AD4114_CHAN_NUMBER; i++) {
		if ((BIT(i) & sequence->channels) != 0) {
			/* Enable channel with configured mapping */
			write_reg[0] = 0x80 | (uint8_t)((config->map_input[i] >> 8) & 0xFF);
			write_reg[1] = (uint8_t)(config->map_input[i] & 0xFF);
			ad4114_write_reg(dev, AD4114_CHANNEL_0_REG + i, write_reg, 2);
		} else {
			/* Disable channel */
			write_reg[0] = 0x0;
			write_reg[1] = 0x0;
			ad4114_write_reg(dev, AD4114_CHANNEL_0_REG + i, write_reg, 2);
		}
	}

	/* Configure the buffer */
	data->buffer = sequence->buffer;

	/* Wait for acquisition to start (status bit 7 = ready) */
	do {
		ad4114_read_reg(dev, AD4114_STATUS_REG, &status, 1);
		k_usleep(10);
	} while ((status & 0x80) != 0x80);

	adc_context_start_read(&data->ctx, sequence);

	return adc_context_wait_for_completion(&data->ctx);
}

static int adc_ad4114_read(const struct device *dev,
                           const struct adc_sequence *sequence)
{
	return adc_ad4114_read_async(dev, sequence, NULL);
}
```

### Step 6: Implement read_async API (Asynchronous)

From **drivers/adc/adc_ad4114.c**:

```c
static int adc_ad4114_read_async(const struct device *dev,
                                 const struct adc_sequence *sequence,
                                 struct k_poll_signal *async)
{
	struct adc_ad4114_data *data = dev->data;
	int ret;

	adc_context_lock(&data->ctx, async ? true : false, async);
	ret = adc_ad4114_start_read(dev, sequence);
	adc_context_release(&data->ctx, ret);

	return ret;
}
```

**Pattern**: `adc_context` helper handles locking, async signaling, and completion.

### Step 7: Implement ADC Context Callbacks

Required when using `struct adc_context`:

```c
static void adc_context_start_sampling(struct adc_context *ctx)
{
	struct adc_ad4114_data *data = CONTAINER_OF(ctx, struct adc_ad4114_data, ctx);

	data->channels = ctx->sequence.channels;
	data->repeat_buffer = data->buffer;

	k_sem_give(&data->sem);  /* Signal acquisition thread */
}

static void adc_context_update_buffer_pointer(struct adc_context *ctx, bool repeat_sampling)
{
	struct adc_ad4114_data *data = CONTAINER_OF(ctx, struct adc_ad4114_data, ctx);

	if (repeat_sampling) {
		data->buffer = data->repeat_buffer;
	}
}
```

### Step 8: Implement Acquisition Thread (if using background conversion)

From **drivers/adc/adc_ad4114.c**:

```c
static void adc_ad4114_acquisition_thread(struct adc_ad4114_data *data)
{
	uint8_t value[4] = {0};
	uint32_t buffer_values[AD4114_CHAN_NUMBER];
	bool is_ended = false;

	while (true) {
		/* Wait for read request */
		k_sem_take(&data->sem, K_FOREVER);

		/* Read all enabled channels */
		while (data->channels != 0) {
			ad4114_read_reg(data->dev, AD4114_DATA_REG, value, 4);

			/* Check which channel provided data (encoded in status byte) */
			uint8_t ch = value[3] & 0x0F;

			if ((value[3] & 0xF0) == 0) {  /* No error */
				/* Reconstruct 24-bit value */
				buffer_values[ch] = (value[0] << 16) | (value[1] << 8) | value[2];

				/* Mark channel as read */
				WRITE_BIT(data->channels, ch, 0);

				/* Disable channel after successful read */
				uint8_t write_reg[2] = {0};
				ad4114_write_reg(data->dev, AD4114_CHANNEL_0_REG + ch, write_reg, 2);
			}

			if (data->channels == 0) {
				is_ended = true;
			}

			k_usleep(10);  /* Poll delay */
		}

		/* Copy results to output buffer in channel order */
		if (is_ended) {
			is_ended = false;
			for (uint8_t i = 0U; i < AD4114_CHAN_NUMBER; i++) {
				if ((BIT(i) & data->channels_cfg) != 0) {
					*data->buffer++ = buffer_values[i];
				}
			}
			adc_context_on_sampling_done(&data->ctx, data->dev);
		}

		k_usleep(1000);
	}
}
```

### Step 9: Implement Init Function

From **drivers/adc/adc_ad4114.c**:

```c
static int adc_ad4114_init(const struct device *dev)
{
	const struct adc_ad4114_config *config = dev->config;
	struct adc_ad4114_data *data = dev->data;
	uint8_t id[2] = {0};
	uint8_t gain[3];
	uint8_t write_reg[2];
	uint8_t status = 0;
	k_tid_t tid;

	data->dev = dev;
	k_sem_init(&data->sem, 0, 1);
	adc_context_init(&data->ctx);

	/* Check SPI bus ready */
	if (!spi_is_ready_dt(&config->spi)) {
		LOG_ERR("spi bus %s not ready", config->spi.bus->name);
		return -ENODEV;
	}

	/* Read and verify device ID */
	ad4114_read_reg(dev, AD4114_ID_REG, id, 2);
	if ((((id[0] << 8) | id[1]) & 0xFFF0) != 0x30D0) {
		LOG_ERR("Read wrong ID register 0x%X 0x%X", id[0], id[1]);
		return -EIO;
	}

	ad4114_read_reg(dev, AD4114_STATUS_REG, &status, 1);
	LOG_INF("Found AD4114 with status %d", status);

	/* Configure gain registers to 0x400000 (unity gain) */
	gain[0] = 0x40;
	gain[1] = 0x00;
	gain[2] = 0x00;
	ad4114_write_reg(dev, AD4114_GAIN0_REG, gain, 3);
	ad4114_write_reg(dev, AD4114_GAIN1_REG, gain, 3);

	/* Enable data status in interface mode register */
	write_reg[0] = 0x0;
	write_reg[1] = 0x40;  /* DATA_STAT = 1 */
	ad4114_write_reg(dev, AD4114_IFMODE_REG, write_reg, 2);

	/* Configure setup 0: unipolar, input buffers enabled */
	write_reg[0] = 0x3;   /* INBUFx = 11 */
	write_reg[1] = 0x0;
	ad4114_write_reg(dev, AD4114_SETUPCON0_REG, write_reg, 2);

	/* Configure setup 1: bipolar, input buffers enabled */
	write_reg[0] = 0x13;  /* BI_UNIPOLARx = 1, INBUFx = 11 */
	write_reg[1] = 0x0;
	ad4114_write_reg(dev, AD4114_SETUPCON1_REG, write_reg, 2);

	/* Enable internal reference and configure clock */
	write_reg[0] = 0x80;  /* REF_EN = 1 */
	write_reg[1] = 0xC;   /* CLOCKSEL = 11 */
	ad4114_write_reg(dev, AD4114_MODE_REG, write_reg, 2);

	/* Create acquisition thread */
	tid = k_thread_create(&data->thread, data->stack,
	                      K_KERNEL_STACK_SIZEOF(data->stack),
	                      (k_thread_entry_t)adc_ad4114_acquisition_thread,
	                      data, NULL, NULL,
	                      CONFIG_ADC_AD4114_ACQUISITION_THREAD_PRIO, 0,
	                      K_NO_WAIT);

	if (IS_ENABLED(CONFIG_THREAD_NAME)) {
		k_thread_name_set(tid, "adc_ad4114");
	}

	adc_context_unlock_unconditionally(&data->ctx);

	return 0;
}
```

### Step 10: Define API Structure and Device Instantiation

From **drivers/adc/adc_ad4114.c**:

```c
static DEVICE_API(adc, adc_ad4114_api) = {
	.channel_setup = adc_ad4114_channel_setup,
	.read = adc_ad4114_read,
#ifdef CONFIG_ADC_ASYNC
	.read_async = adc_ad4114_read_async,
#endif
	.ref_internal = 2500,  /* 2.5V internal reference */
};

#define ADC_AD4114_DEVICE(inst)                                                    \
	static struct adc_ad4114_data adc_ad4114_data_##inst;                      \
	static const struct adc_ad4114_config adc_ad4114_config_##inst = {         \
		.spi = SPI_DT_SPEC_INST_GET(inst, SPI_WORD_SET(8)),                \
		.resolution = AD4114_ADC_RESOLUTION,                               \
		.map_input = DT_INST_PROP(inst, map_inputs),                       \
	};                                                                         \
	DEVICE_DT_INST_DEFINE(inst, adc_ad4114_init, NULL,                         \
	                      &adc_ad4114_data_##inst,                             \
	                      &adc_ad4114_config_##inst,                           \
	                      POST_KERNEL, CONFIG_ADC_INIT_PRIORITY,               \
	                      &adc_ad4114_api);                                    \
	BUILD_ASSERT(DT_INST_PROP_LEN(inst, map_inputs) == AD4114_CHAN_NUMBER);

DT_INST_FOREACH_STATUS_OKAY(ADC_AD4114_DEVICE)
```

