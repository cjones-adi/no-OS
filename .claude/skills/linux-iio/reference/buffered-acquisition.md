# IIO Buffered Data Acquisition

Complete guide to IIO buffers, triggers, DMA integration, and IIO backend framework for high-speed data streaming.

## When to Use Buffers

Use IIO buffers for:
- **High-speed continuous sampling** (> 1 kHz typical)
- **Streaming data to userspace** efficiently
- **DMA-based data transfer** (zero-copy on supported platforms)
- **Multi-channel synchronized acquisition**

"Multiple data channels can be read at once from `/dev/iio:deviceX` character device node, thus reducing the CPU load."

## Buffer Architecture

```
┌──────────────────┐
│   Userspace      │
│  read(/dev/iio:X)│
└────────┬─────────┘
         │
┌────────┴─────────┐
│  IIO Buffer      │  (kfifo, DMA, etc.)
│  - length        │
│  - enable        │
└────────┬─────────┘
         │
┌────────┴─────────┐
│  IIO Trigger     │  (timer, GPIO, data ready, etc.)
│  → triggers      │
│  trigger_handler │
└────────┬─────────┘
         │
┌────────┴─────────┐
│  Hardware Read   │
│  (ADC conversion)│
└──────────────────┘
```

## Scan Elements

Each channel in buffered mode has scan element properties:

**Sysfs Location**: `/sys/bus/iio/devices/iio:deviceX/scan_elements/`

| Attribute | Description | Example |
|-----------|-------------|---------|
| `in_voltage0_en` | Enable channel in buffer | `echo 1 > in_voltage0_en` |
| `in_voltage0_index` | Position in buffer | `0` (first), `1` (second), etc. |
| `in_voltage0_type` | Data format | `le:s24/32>>0` (see below) |

**Type Format**: `[be|le]:[s|u]bits/storagebits[>>shift]`
- `le`/`be`: Little/big endian
- `s`/`u`: Signed/unsigned
- `bits`: Real data bits
- `storagebits`: Storage size (must be ≥ bits)
- `shift`: Bit offset in storage

## Triggered Buffer Setup

```c
// In probe, after setting up indio_dev
ret = devm_iio_triggered_buffer_setup(&spi->dev, indio_dev,
				     &iio_pollfunc_store_time,  // Top half (store timestamp)
				     &ad7124_trigger_handler,    // Bottom half (read data)
				     NULL);  // Optional buffer_setup_ops
if (ret)
	return ret;
```

### Parameters

- **Top half** (`iio_pollfunc_store_time`): Runs in hard IRQ context, typically just stores timestamp
- **Bottom half** (`ad7124_trigger_handler`): Runs in threaded context, reads hardware and pushes to buffer
- **buffer_setup_ops** (optional): Callbacks for buffer enable/disable

## Trigger Handler Implementation

```c
static irqreturn_t ad7124_trigger_handler(int irq, void *p)
{
	struct iio_poll_func *pf = p;
	struct iio_dev *indio_dev = pf->indio_dev;
	struct ad7124_state *st = iio_priv(indio_dev);

	// Buffer structure (packed)
	struct {
		u32 values[8];  // Max channels (adjust to actual)
		s64 timestamp __aligned(8);  // Must be 64-bit aligned!
	} data;

	int i, j = 0;

	// Read only ENABLED channels (check active_scan_mask)
	for_each_set_bit(i, indio_dev->active_scan_mask, indio_dev->masklength) {
		// Read channel i from hardware
		ad7124_read_channel(st, i, &data.values[j++]);
	}

	// Push data to buffer with timestamp
	iio_push_to_buffers_with_timestamp(indio_dev, &data,
					  iio_get_time_ns(indio_dev));

	// CRITICAL: Notify IIO core we're done
	iio_trigger_notify_done(indio_dev->trig);

	return IRQ_HANDLED;
}
```

**Critical Points**:
- Only read **enabled** channels (check `active_scan_mask`)
- Timestamp must be **64-bit aligned** in buffer structure
- **MUST call** `iio_trigger_notify_done()` at the end
- Use `iio_push_to_buffers_with_timestamp()` for timestamped data

## IIO Triggers

### Purpose

Triggers enable **event-based data capture** instead of periodic polling. A trigger represents an event that causes one or more IIO devices to capture data.

**Key Concept**: "Triggers can be completely unrelated to the sensor itself or may be derived from sensors."

### Trigger Types

Common trigger sources:
- **Hardware interrupts**: Data ready signal, GPIO edge
- **Timer-based**: hrtimer, periodic interrupts
- **Sysfs writes**: Manual trigger via sysfs
- **Software triggers**: User-defined events
- **Chained triggers**: Trigger from another IIO device

### Using Existing Triggers

**Sysfs Location**: `/sys/bus/iio/devices/triggerY/`

```bash
# List available triggers
ls /sys/bus/iio/devices/

# Assign trigger to device
echo "trigger0" > /sys/bus/iio/devices/iio:device0/trigger/current_trigger

# Check current trigger
cat /sys/bus/iio/devices/iio:device0/trigger/current_trigger
```

### Creating a Trigger (Driver)

**Basic trigger creation**:

```c
#include <linux/iio/trigger.h>

static const struct iio_trigger_ops ad7124_trigger_ops = {
	.set_trigger_state = ad7124_set_trigger_state,
	.validate_device = iio_trigger_validate_own_device,  // Only for this device
};

// In probe
struct iio_trigger *trig;

trig = devm_iio_trigger_alloc(&spi->dev, "%s-dev%d",
			     indio_dev->name, iio_device_id(indio_dev));
if (!trig)
	return -ENOMEM;

trig->ops = &ad7124_trigger_ops;

ret = devm_iio_trigger_register(&spi->dev, trig);
if (ret)
	return ret;
```

**Trigger callback**:

```c
static int ad7124_set_trigger_state(struct iio_trigger *trig, bool state)
{
	struct iio_dev *indio_dev = iio_trigger_get_drvdata(trig);
	struct ad7124_state *st = iio_priv(indio_dev);

	if (state) {
		// Enable hardware interrupt/data ready
		return ad7124_enable_irq(st);
	} else {
		// Disable hardware interrupt
		return ad7124_disable_irq(st);
	}
}
```

### Data Ready Interrupt Pattern

Common pattern for ADCs with data ready signal:

```c
// In probe after buffer setup
ret = devm_request_threaded_irq(&spi->dev, spi->irq,
			       NULL,                    // Hard IRQ (can be NULL)
			       &ad7124_irq_handler,     // Threaded handler
			       IRQF_ONESHOT,
			       indio_dev->name, indio_dev);

static irqreturn_t ad7124_irq_handler(int irq, void *p)
{
	struct iio_dev *indio_dev = p;

	// Trigger buffer update
	iio_trigger_poll(indio_dev->trig);

	return IRQ_HANDLED;
}
```

## Userspace Buffer Access

```bash
# Enable channels for buffered capture
echo 1 > /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_en
echo 1 > /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage1_en

# Set buffer length (number of samples)
echo 128 > /sys/bus/iio/devices/iio:device0/buffer/length

# Enable buffer
echo 1 > /sys/bus/iio/devices/iio:device0/buffer/enable

# Read binary data stream
cat /dev/iio:device0 | hexdump -C

# Disable buffer when done
echo 0 > /sys/bus/iio/devices/iio:device0/buffer/enable
```

## IIO Backend/Frontend Architecture

### When to Use Backend

For complex high-speed data converters with separate control and data paths:
- **JESD204-based converters** (AD9081, AD9680, ADRV9002)
- **FPGA-based data acquisition** (AXI ADC/DAC cores)
- **Shared DMA infrastructure** between multiple converters
- **Separate control and streaming** interfaces

### Architecture

```
┌──────────────────────────────────────┐
│   Frontend Driver (e.g., AD9081)     │
│   - SPI control interface            │
│   - Device configuration             │
│   - Channel/gain/filter setup        │
│   - Registers as IIO device          │
└────────────┬─────────────────────────┘
             │ IIO Backend API
             │ (iio_backend_*)
┌────────────┴─────────────────────────┐
│   Backend Driver (e.g., AXI ADC)     │
│   - High-speed data path             │
│   - JESD204 link management          │
│   - DMA configuration                │
│   - Buffered data streaming          │
└──────────────────────────────────────┘
```

### Backend Operations

```c
#include <linux/iio/backend.h>

// Key backend operations
struct iio_backend_ops {
	int (*enable)(struct iio_backend *back);
	void (*disable)(struct iio_backend *back);
	int (*data_stream_enable)(struct iio_backend *back);
	int (*data_stream_disable)(struct iio_backend *back);
	// ... more operations
};
```

### Frontend Driver Pattern

```c
static int ad9081_probe(struct spi_device *spi)
{
	struct iio_dev *indio_dev;
	struct ad9081_state *st;
	struct iio_backend *back;
	int ret;

	indio_dev = devm_iio_device_alloc(&spi->dev, sizeof(*st));
	st = iio_priv(indio_dev);

	// Get backend from device tree
	back = devm_iio_backend_get(&spi->dev, NULL);
	if (IS_ERR(back))
		return PTR_ERR(back);

	st->back = back;

	// Configure device via SPI
	ret = ad9081_setup(st);
	if (ret)
		return ret;

	// Enable backend data path
	ret = iio_backend_enable(back);
	if (ret)
		return ret;

	// Setup IIO device
	indio_dev->info = &ad9081_info;
	indio_dev->channels = ad9081_channels;
	indio_dev->num_channels = ARRAY_SIZE(ad9081_channels);

	// Start data streaming
	ret = iio_backend_data_stream_enable(back);
	if (ret)
		goto err_backend_disable;

	return devm_iio_device_register(&spi->dev, indio_dev);

err_backend_disable:
	iio_backend_disable(back);
	return ret;
}
```

### Device Tree Linkage

```dts
// Frontend device (control)
adc@0 {
	compatible = "adi,ad9081";
	reg = <0>;
	spi-max-frequency = <1000000>;

	// Link to backend
	io-backends = <&axi_ad9081_rx>;
};

// Backend device (data path)
axi_ad9081_rx: axi-ad9081-rx@44a00000 {
	compatible = "adi,axi-ad9081-rx-1.0";
	reg = <0x44a00000 0x8000>;

	dmas = <&rx_dma 0>;
	dma-names = "rx";

	clocks = <&axi_ad9081_rx_clkgen>;

	#io-backend-cells = <0>;
};
```

## DMA Integration

### AXI DMA Buffer (FPGA Platforms)

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

### Custom DMA Buffer

For custom DMA implementations:

```c
#include <linux/iio/buffer.h>
#include <linux/iio/buffer-dma.h>

static const struct iio_buffer_setup_ops custom_buffer_ops = {
	.preenable = custom_buffer_preenable,
	.postdisable = custom_buffer_postdisable,
};

// In probe
struct iio_buffer *buffer;

buffer = devm_iio_dma_buffer_alloc(&pdev->dev, &custom_buffer_ops);
if (IS_ERR(buffer))
	return PTR_ERR(buffer);

iio_device_attach_buffer(indio_dev, buffer);
```

## Buffer Setup Callbacks

```c
static const struct iio_buffer_setup_ops ad7124_buffer_ops = {
	.preenable = ad7124_buffer_preenable,
	.postdisable = ad7124_buffer_postdisable,
};

static int ad7124_buffer_preenable(struct iio_dev *indio_dev)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Called before buffer is enabled
	// - Configure hardware for enabled channels
	// - Setup DMA if needed

	return ad7124_configure_channels(st);
}

static int ad7124_buffer_postdisable(struct iio_dev *indio_dev)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Called after buffer is disabled
	// - Stop DMA
	// - Reset hardware to single-shot mode

	return ad7124_reset_mode(st);
}
```

## Update Scan Mode Callback

```c
static int ad7124_update_scan_mode(struct iio_dev *indio_dev,
				  const unsigned long *scan_mask)
{
	struct ad7124_state *st = iio_priv(indio_dev);
	int i;

	// Called when user changes enabled channels
	// scan_mask contains bitmask of enabled channels

	for_each_set_bit(i, scan_mask, indio_dev->masklength) {
		// Configure channel i for buffered mode
		ad7124_configure_channel(st, i);
	}

	return 0;
}
```

Add to `iio_info`:
```c
static const struct iio_info ad7124_info = {
	.read_raw = ad7124_read_raw,
	.write_raw = ad7124_write_raw,
	.update_scan_mode = ad7124_update_scan_mode,
};
```

## Common Pitfalls

### 1. Not Calling iio_trigger_notify_done()

**Problem**: Buffer hangs, no more data captured.

```c
static irqreturn_t trigger_handler(int irq, void *p)
{
	// ... read data ...
	iio_push_to_buffers_with_timestamp(indio_dev, &data, ts);

	// MUST CALL THIS!
	iio_trigger_notify_done(indio_dev->trig);
	return IRQ_HANDLED;
}
```

### 2. Misaligned Timestamp in Buffer

**Problem**: Kernel panic or data corruption.

```c
// WRONG - Timestamp not aligned
struct {
	u32 ch[8];
	s64 timestamp;  // May not be 64-bit aligned!
} data;

// CORRECT - Force alignment
struct {
	u32 ch[8];
	s64 timestamp __aligned(8);  // Explicitly aligned
} data;
```

### 3. Reading All Channels Instead of Enabled Ones

**Problem**: Wasted CPU cycles, incorrect data order.

```c
// WRONG - Reading all channels
for (i = 0; i < num_channels; i++) {
	read_channel(i);
}

// CORRECT - Read only enabled channels
for_each_set_bit(i, indio_dev->active_scan_mask, indio_dev->masklength) {
	read_channel(i);
}
```

### 4. Incorrect Buffer Size Calculation

**Problem**: Buffer overflow or underflow.

```c
// Buffer must hold all enabled channels + timestamp
struct {
	u32 channels[MAX_CHANNELS];  // Must be large enough
	s64 timestamp __aligned(8);
} data;

// Verify size before use
BUILD_BUG_ON(sizeof(data) < (MAX_CHANNELS * 4 + 8));
```

## Testing Buffered Mode

```bash
# Check buffer exists
ls /sys/bus/iio/devices/iio:device0/buffer/

# Check scan elements
ls /sys/bus/iio/devices/iio:device0/scan_elements/

# Check what's enabled
cat /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_en
cat /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_index
cat /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_type

# Enable and read
echo 1 > /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_en
echo 128 > /sys/bus/iio/devices/iio:device0/buffer/length
echo 1 > /sys/bus/iio/devices/iio:device0/buffer/enable
dd if=/dev/iio:device0 bs=1024 count=10 | hexdump -C
echo 0 > /sys/bus/iio/devices/iio:device0/buffer/enable
```

## libiio Buffer Access

```bash
# Install tools
apt-get install libiio-utils

# Capture buffered data
iio_readdev -b 256 -s 100 ad7124-4
```

## Performance Considerations

- Use DMA when available (reduces CPU usage)
- Keep trigger handler fast (offload processing to bottom half)
- Align data structures for cache efficiency
- Use power-of-2 buffer sizes
- Consider using kfifo for software buffers
- Profile with `perf` to identify bottlenecks
