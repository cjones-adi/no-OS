## Debugging Tips

### 1. Enable DAC Logging

**In prj.conf**:
```conf
CONFIG_DAC_LOG_LEVEL_DBG=y
CONFIG_LOG=y
```

**In driver code**:
```c
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(dac_mydevice, CONFIG_DAC_LOG_LEVEL);

LOG_DBG("Channel %d configured: resolution=%d, buffered=%d",
        ch, resolution, buffered);
LOG_ERR("SPI transfer failed: %d", ret);
```

### 2. Verify SPI/I2C Bus Communication

```c
/* Check bus ready */
if (!spi_is_ready_dt(&config->bus)) {
	LOG_ERR("SPI bus not ready");
	return -ENODEV;
}

/* Test write with known value */
uint8_t test_pattern = 0xAA;
int ret = spi_write_dt(&config->bus, &tx_buf);
if (ret < 0) {
	LOG_ERR("SPI test write failed: %d", ret);
	return ret;
}
LOG_INF("SPI communication verified");
```

### 3. Measure Output with Multimeter/Oscilloscope

```c
/* Set known voltage and measure */
uint32_t mid_scale = (1U << resolution) / 2;
dac_write_value(dac_dev, 0, mid_scale);

printk("DAC output should be Vref/2 = %.2fV\n", vref / 2.0);
printk("Measure with multimeter and verify\n");

k_sleep(K_SECONDS(5));  /* Time to measure */
```

**Expected voltage**: `Vout = (value / 2^resolution) × Vref`

### 4. Log DAC Write Operations

```c
static int dac_write_value(const struct device *dev, uint8_t channel, uint32_t value)
{
	const struct dac_config *config = dev->config;

	LOG_DBG("Writing channel %d: value=0x%04X (%u), resolution=%d",
	        channel, value, value, config->resolution);

	/* Calculate expected voltage */
	float expected_voltage = (float)value / (1U << config->resolution) * config->vref;
	LOG_DBG("Expected output: %.3fV", expected_voltage);

	int ret = hardware_write(dev, channel, value);

	if (ret == 0) {
		LOG_DBG("Write successful");
	} else {
		LOG_ERR("Write failed: %d", ret);
	}

	return ret;
}
```

### 5. Check Resolution Configuration

```c
LOG_DBG("DAC resolution: %d bits, max value: %u",
        resolution, (1U << resolution) - 1);

if (value > (1U << resolution) - 1) {
	LOG_ERR("Value %u exceeds maximum %u for %d-bit DAC",
	        value, (1U << resolution) - 1, resolution);
	return -EINVAL;
}
```

### 6. Verify SPI Mode and Bit Order

```c
/* Check SPI configuration matches datasheet */
struct spi_config spi_cfg = {
	.frequency = 30000000,  /* 30 MHz max for AD56x1 */
	.operation = SPI_OP_MODE_MASTER | SPI_MODE_CPHA | SPI_WORD_SET(8),
};

LOG_DBG("SPI mode: CPOL=%d, CPHA=%d, MSB-first",
        (spi_cfg.operation & SPI_MODE_CPOL) ? 1 : 0,
        (spi_cfg.operation & SPI_MODE_CPHA) ? 1 : 0);
```

### 7. Test with Simple Pattern

```c
void dac_self_test(const struct device *dac_dev)
{
	uint32_t test_values[] = {0, 1024, 2048, 3072, 4095};  /* 12-bit values */

	printk("DAC self-test: cycling through known values\n");

	for (int i = 0; i < ARRAY_SIZE(test_values); i++) {
		int ret = dac_write_value(dac_dev, 0, test_values[i]);
		printk("Value %u: %s\n", test_values[i],
		       ret == 0 ? "OK" : "FAILED");
		k_sleep(K_SECONDS(1));
	}
}
```

### 8. Check Power Supply and Reference

```c
LOG_INF("DAC configuration:");
LOG_INF("  VDD: %.2fV (supply voltage)", vdd);
LOG_INF("  Vref: %.2fV (reference voltage)", vref);
LOG_INF("  Output range: 0V to %.2fV", vref);

if (config->double_output_range) {
	LOG_INF("  Double range enabled: 0V to %.2fV", 2.0 * vref);
	if (vdd < 2.0 * vref) {
		LOG_WRN("VDD (%.2fV) < 2×Vref (%.2fV), may cause clipping",
		        vdd, 2.0 * vref);
	}
}
```

