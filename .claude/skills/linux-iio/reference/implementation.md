# IIO Driver Implementation

Detailed guide for implementing IIO device drivers including probe flow, device registration, and core callback implementations.

## Device Registration Pattern

### Complete Probe Flow

```c
static int ad7124_probe(struct spi_device *spi)
{
	struct iio_dev *indio_dev;
	struct ad7124_state *st;
	int ret;

	// 1. Allocate IIO device with private data (use devm_ for auto cleanup)
	indio_dev = devm_iio_device_alloc(&spi->dev, sizeof(*st));
	if (!indio_dev)
		return -ENOMEM;

	st = iio_priv(indio_dev);
	st->spi = spi;

	// 2. Get device tree properties
	ret = device_property_read_u32(&spi->dev, "adi,sample-rate", &st->sample_rate);
	if (ret)
		st->sample_rate = 1000;  // Default value

	// 3. Get resources (regulators, clocks, GPIOs)
	st->vref = devm_regulator_get(&spi->dev, "vref");
	if (IS_ERR(st->vref))
		return PTR_ERR(st->vref);

	ret = regulator_enable(st->vref);
	if (ret)
		return ret;

	st->clk = devm_clk_get_enabled(&spi->dev, "mclk");
	if (IS_ERR(st->clk) && PTR_ERR(st->clk) != -ENOENT)
		goto err_regulator_disable;

	// 4. Initialize hardware communication
	ret = ad7124_setup(st);
	if (ret)
		goto err_regulator_disable;

	// 5. Setup IIO device structure
	indio_dev->name = spi_get_device_id(spi)->name;
	indio_dev->modes = INDIO_DIRECT_MODE;
	indio_dev->channels = ad7124_channels;
	indio_dev->num_channels = ARRAY_SIZE(ad7124_channels);
	indio_dev->info = &ad7124_info;

	// 6. Optional: Setup triggered buffer for continuous sampling
	ret = devm_iio_triggered_buffer_setup(&spi->dev, indio_dev,
					     &iio_pollfunc_store_time,
					     &ad7124_trigger_handler,
					     NULL);
	if (ret)
		goto err_regulator_disable;

	// 7. Register IIO device (MUST BE LAST! Device goes live immediately)
	ret = devm_iio_device_register(&spi->dev, indio_dev);
	if (ret)
		goto err_regulator_disable;

	return 0;

err_regulator_disable:
	regulator_disable(st->vref);
	return ret;
}
```

**CRITICAL Rules**:
1. **Use `devm_*` functions** for automatic cleanup
2. **Register device LAST** - device is immediately live after `devm_iio_device_register()`
3. **Handle -EPROBE_DEFER** for resources not yet available
4. **Enable resources before** hardware access

## read_raw Callback Implementation

The `read_raw()` callback is the **core** of IIO device interaction - it reads channel values:

```c
static int ad7124_read_raw(struct iio_dev *indio_dev,
			  struct iio_chan_spec const *chan,
			  int *val, int *val2, long info)
{
	struct ad7124_state *st = iio_priv(indio_dev);
	int ret;

	switch (info) {
	case IIO_CHAN_INFO_RAW:
		// CRITICAL: Claim direct mode to prevent buffered mode conflicts
		ret = iio_device_claim_direct_mode(indio_dev);
		if (ret)
			return ret;

		// Read hardware for this channel
		ret = ad7124_single_conversion(st, chan, val);
		iio_device_release_direct_mode(indio_dev);

		if (ret < 0)
			return ret;

		return IIO_VAL_INT;  // Return type: single integer

	case IIO_CHAN_INFO_SCALE:
		// Calculate: voltage = (raw - offset) * scale
		// For ADC: scale = vref_mv / 2^realbits
		// Return as fractional: vref / 2^realbits
		*val = st->vref_mv;
		*val2 = chan->scan_type.realbits;
		return IIO_VAL_FRACTIONAL_LOG2;  // val / 2^val2

	case IIO_CHAN_INFO_OFFSET:
		// For bipolar ADC: offset = -2^(bits-1)
		// For unipolar ADC: offset = 0
		if (st->bipolar)
			*val = -(1 << (chan->scan_type.realbits - 1));
		else
			*val = 0;
		return IIO_VAL_INT;

	case IIO_CHAN_INFO_SAMP_FREQ:
		// Sample frequency as integer + micro
		*val = st->sample_rate / 1000;       // Integer part
		*val2 = (st->sample_rate % 1000) * 1000;  // Fractional part
		return IIO_VAL_INT_PLUS_MICRO;  // val.val2 Hz

	default:
		return -EINVAL;
	}
}
```

### IIO_VAL Return Types

Return types tell the IIO core how to interpret `*val` and `*val2`:

| Return Type | Format | Interpretation | Example |
|-------------|--------|----------------|---------|
| IIO_VAL_INT | Single int | `*val` | `*val = 12345` → 12345 |
| IIO_VAL_INT_PLUS_MICRO | int + micro | `*val + *val2/1000000` | `*val=1, *val2=500000` → 1.5 |
| IIO_VAL_INT_PLUS_NANO | int + nano | `*val + *val2/1000000000` | High precision |
| IIO_VAL_FRACTIONAL | Numerator/denominator | `*val / *val2` | `*val=3, *val2=4` → 0.75 |
| IIO_VAL_FRACTIONAL_LOG2 | val / 2^val2 | `*val / (1 << *val2)` | `*val=2500, *val2=16` → 2500/65536 |
| IIO_VAL_INT_MULTIPLE | Array of ints | Multiple values | Complex data |

**ADI Pattern**: For ADC scale, use `IIO_VAL_FRACTIONAL_LOG2` with `vref_mv` and `realbits`:
```c
*val = st->vref_mv;  // 2500 (2.5V reference)
*val2 = 24;          // 24-bit ADC
// Result: 2500 / 2^24 = 0.000149 mV/count
```

## write_raw Callback

Implements writable attributes:

```c
static int ad7124_write_raw(struct iio_dev *indio_dev,
			   struct iio_chan_spec const *chan,
			   int val, int val2, long info)
{
	struct ad7124_state *st = iio_priv(indio_dev);
	unsigned int freq;

	switch (info) {
	case IIO_CHAN_INFO_SAMP_FREQ:
		// Reconstruct frequency from val + val2
		freq = val * 1000 + val2 / 1000;
		return ad7124_set_sample_rate(st, freq);

	case IIO_CHAN_INFO_SCALE:
		// Set hardware gain/range
		return ad7124_set_scale(st, chan, val, val2);

	default:
		return -EINVAL;
	}
}
```

## read_avail Callback

Provides available values for writable attributes (creates `*_available` sysfs files):

```c
static int ad7124_read_avail(struct iio_dev *indio_dev,
			    struct iio_chan_spec const *chan,
			    const int **vals, int *type, int *length,
			    long mask)
{
	static const int sample_rates[] = {10, 100, 1000, 10000};  // Hz

	switch (mask) {
	case IIO_CHAN_INFO_SAMP_FREQ:
		*vals = sample_rates;
		*type = IIO_VAL_INT;
		*length = ARRAY_SIZE(sample_rates);
		return IIO_AVAIL_LIST;  // Discrete list

	default:
		return -EINVAL;
	}
}
```

Userspace sees: `/sys/bus/iio/devices/iio:device0/sampling_frequency_available`

## ADI-Specific Patterns

### 1. JESD204 Integration

For high-speed converters (> 100 MSPS) using JESD204:

```c
#include <linux/jesd204/jesd204.h>

static const struct jesd204_dev_data ad9081_jesd204_data = {
	.state_ops = &ad9081_jesd204_state_ops,
	.max_num_links = 2,
	.num_lanes = 8,
	// ... JESD204 configuration
};

// In probe:
ret = devm_jesd204_dev_register(&spi->dev, &ad9081_jesd204_data);
if (ret)
	return ret;
```

**Important**: Consult **linux-jesd204 skill** for detailed JESD204 integration.

### 2. Sigma-Delta ADC Helper

For precision Sigma-Delta ADCs (AD7124, AD7173, AD4134):

```c
#include <linux/iio/adc/ad_sigma_delta.h>

static const struct ad_sigma_delta_info ad7124_sd_info = {
	.set_channel = ad7124_set_channel,
	.set_mode = ad7124_set_mode,
	.has_registers = true,
	.addr_shift = 0,
	.read_mask = BIT(6),
	.data_reg = AD7124_DATA,
};

// In probe:
ret = ad_sd_init(&st->sd, indio_dev, spi, &ad7124_sd_info);
if (ret)
	return ret;
```

### 3. AXI DMA Buffer (FPGA Platforms)

For Zynq/ZynqMP platforms with AXI DMA:

```c
#include <linux/iio/buffer-dmaengine.h>

// In probe, after channel setup
ret = devm_iio_dmaengine_buffer_setup(&pdev->dev, indio_dev, "rx");
if (ret)
	return ret;
```

Device tree:
```dts
axi_adc: axi-adc@44a00000 {
	dmas = <&rx_dma 0>;
	dma-names = "rx";
};
```

### 4. Multi-Channel Macro Pattern

For devices with many similar channels:

```c
#define AD7124_VOLTAGE_CHANNEL(_index) { \
	.type = IIO_VOLTAGE, \
	.indexed = 1, \
	.channel = _index, \
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW), \
	.info_mask_shared_by_type = BIT(IIO_CHAN_INFO_SCALE) | \
				   BIT(IIO_CHAN_INFO_SAMP_FREQ), \
	.scan_index = _index, \
	.scan_type = { \
		.sign = 's', \
		.realbits = 24, \
		.storagebits = 32, \
		.endianness = IIO_BE, \
	}, \
}

static const struct iio_chan_spec ad7124_channels[] = {
	AD7124_VOLTAGE_CHANNEL(0),
	AD7124_VOLTAGE_CHANNEL(1),
	AD7124_VOLTAGE_CHANNEL(2),
	AD7124_VOLTAGE_CHANNEL(3),
};
```

## Common Pitfalls

### 1. Forgetting iio_device_claim_direct_mode()

**Problem**: Direct reads can conflict with buffered mode.

```c
// WRONG - Can cause data corruption
static int bad_read_raw(...)
{
	return read_hardware();  // Conflict with buffer!
}

// CORRECT - Claim direct mode first
static int good_read_raw(...)
{
	int ret = iio_device_claim_direct_mode(indio_dev);
	if (ret)
		return ret;  // Buffer is active, can't do direct read

	ret = read_hardware();
	iio_device_release_direct_mode(indio_dev);
	return ret;
}
```

### 2. Registering Device Too Early

**Problem**: Device is live immediately after `iio_device_register()`.

```c
// WRONG - Userspace can access before ready
iio_device_register(indio_dev);
setup_interrupts();  // Too late! Already live!

// CORRECT - Register LAST
setup_interrupts();
iio_device_register(indio_dev);  // Last step!
```

## Reference Drivers

Study these excellent examples in the Linux kernel:

### ADC Drivers

| Driver | Type | File | Key Features |
|--------|------|------|--------------|
| AD7124 | Sigma-Delta | drivers/iio/adc/ad7124.c | Calibration, buffered, sigma-delta helper |
| AD4630 | SAR | drivers/iio/adc/ad4630.c | High-speed, buffered, DMA |
| AD7606 | Multi-channel SAR | drivers/iio/adc/ad7606.c | Parallel/SPI, oversampling, triggered buffer |
| AD4695 | 16-ch SAR | drivers/iio/adc/ad4695.c | Multi-channel pattern |

### DAC Drivers

| Driver | Type | File | Key Features |
|--------|------|------|--------------|
| AD3552R | High-speed DAC | drivers/iio/dac/ad3552r.c | Backend integration, DMA |
| AD5686 | Multi-channel DAC | drivers/iio/dac/ad5686.c | SPI/I2C variants |
| AD5764 | Quad DAC | drivers/iio/dac/ad5764.c | Output channels |

### IMU/Sensor Drivers

| Driver | Type | File | Key Features |
|--------|------|------|--------------|
| ADIS16480 | IMU | drivers/iio/imu/adis16480.c | Multi-sensor, buffered, burst read |
| ADXL345 | Accelerometer | drivers/iio/accel/adxl345_core.c | Interrupt-driven, FIFO |

### RF/Frequency Drivers

| Driver | Type | File | Key Features |
|--------|------|------|--------------|
| AD9081 | RF Transceiver | drivers/iio/frequency/ad9081.c | JESD204, backend, complex |
| ADF4371 | PLL | drivers/iio/frequency/adf4371.c | Frequency synthesis |

## Minimal IIO Driver Template

```c
#include <linux/iio/iio.h>
#include <linux/spi/spi.h>

static int mydev_read_raw(struct iio_dev *indio_dev,
			 struct iio_chan_spec const *chan,
			 int *val, int *val2, long mask)
{
	switch (mask) {
	case IIO_CHAN_INFO_RAW:
		*val = read_adc_value();
		return IIO_VAL_INT;
	default:
		return -EINVAL;
	}
}

static const struct iio_info mydev_info = {
	.read_raw = mydev_read_raw,
};

static const struct iio_chan_spec mydev_channels[] = {
	{
		.type = IIO_VOLTAGE,
		.indexed = 1,
		.channel = 0,
		.info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
	},
};

static int mydev_probe(struct spi_device *spi)
{
	struct iio_dev *indio_dev;

	indio_dev = devm_iio_device_alloc(&spi->dev, sizeof(*st));
	if (!indio_dev)
		return -ENOMEM;

	indio_dev->name = "mydev";
	indio_dev->modes = INDIO_DIRECT_MODE;
	indio_dev->channels = mydev_channels;
	indio_dev->num_channels = ARRAY_SIZE(mydev_channels);
	indio_dev->info = &mydev_info;

	return devm_iio_device_register(&spi->dev, indio_dev);
}
```
