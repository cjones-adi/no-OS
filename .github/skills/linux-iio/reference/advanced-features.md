# IIO Advanced Features

Guide to IIO events, thresholds, hardware FIFO, calibration, and other advanced functionality.

## IIO Events

### What are IIO Events?

IIO events notify userspace when certain conditions occur (thresholds crossed, data ready, motion detected, etc.) without continuous polling.

**Event Types**:
- Threshold events (rising/falling)
- ROC (Rate of Change) events
- Data ready / Sample ready
- Motion detection (tap, free-fall)
- Orientation changes

### Event Architecture

```
┌──────────────────┐
│   Userspace      │
│  poll(/dev/iio:X)│  (blocking wait for events)
└────────┬─────────┘
         │
┌────────┴─────────┐
│  Event Queue     │
│  (kernel)        │
└────────┬─────────┘
         │
┌────────┴─────────┐
│  Hardware IRQ    │
│  (threshold,     │
│   motion, etc.)  │
└──────────────────┘
```

### Implementing Events

```c
#include <linux/iio/events.h>

// Define event codes
static const struct iio_event_spec ad7124_events[] = {
	{
		.type = IIO_EV_TYPE_THRESH,
		.dir = IIO_EV_DIR_RISING,
		.mask_separate = BIT(IIO_EV_INFO_VALUE) |
				BIT(IIO_EV_INFO_ENABLE),
	},
	{
		.type = IIO_EV_TYPE_THRESH,
		.dir = IIO_EV_DIR_FALLING,
		.mask_separate = BIT(IIO_EV_INFO_VALUE) |
				BIT(IIO_EV_INFO_ENABLE),
	},
};

// Add to channel spec
static const struct iio_chan_spec ad7124_channel = {
	.type = IIO_VOLTAGE,
	.indexed = 1,
	.channel = 0,
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
	.event_spec = ad7124_events,
	.num_event_specs = ARRAY_SIZE(ad7124_events),
};
```

### Event Callbacks

```c
static int ad7124_read_event_config(struct iio_dev *indio_dev,
				   const struct iio_chan_spec *chan,
				   enum iio_event_type type,
				   enum iio_event_direction dir)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Return 1 if enabled, 0 if disabled
	return st->threshold_enabled[chan->channel];
}

static int ad7124_write_event_config(struct iio_dev *indio_dev,
				    const struct iio_chan_spec *chan,
				    enum iio_event_type type,
				    enum iio_event_direction dir,
				    int state)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Enable/disable threshold monitoring
	if (state)
		return ad7124_enable_threshold(st, chan->channel);
	else
		return ad7124_disable_threshold(st, chan->channel);
}

static int ad7124_read_event_value(struct iio_dev *indio_dev,
				  const struct iio_chan_spec *chan,
				  enum iio_event_type type,
				  enum iio_event_direction dir,
				  enum iio_event_info info,
				  int *val, int *val2)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Read threshold value
	*val = st->threshold_value[chan->channel];
	return IIO_VAL_INT;
}

static int ad7124_write_event_value(struct iio_dev *indio_dev,
				   const struct iio_chan_spec *chan,
				   enum iio_event_type type,
				   enum iio_event_direction dir,
				   enum iio_event_info info,
				   int val, int val2)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Write threshold value to hardware
	return ad7124_set_threshold(st, chan->channel, val);
}
```

Add to `iio_info`:
```c
static const struct iio_info ad7124_info = {
	.read_raw = ad7124_read_raw,
	.write_raw = ad7124_write_raw,
	.read_event_config = ad7124_read_event_config,
	.write_event_config = ad7124_write_event_config,
	.read_event_value = ad7124_read_event_value,
	.write_event_value = ad7124_write_event_value,
};
```

### Pushing Events

```c
static irqreturn_t ad7124_event_handler(int irq, void *p)
{
	struct iio_dev *indio_dev = p;
	struct ad7124_state *st = iio_priv(indio_dev);
	u32 status;
	int channel;
	s64 timestamp = iio_get_time_ns(indio_dev);

	// Read status register to determine which channel triggered
	ad7124_read_status(st, &status);
	channel = (status >> 4) & 0xF;

	// Push event to userspace
	if (status & AD7124_STATUS_THRESH_HIGH) {
		iio_push_event(indio_dev,
			      IIO_UNMOD_EVENT_CODE(IIO_VOLTAGE,
						  channel,
						  IIO_EV_TYPE_THRESH,
						  IIO_EV_DIR_RISING),
			      timestamp);
	}

	if (status & AD7124_STATUS_THRESH_LOW) {
		iio_push_event(indio_dev,
			      IIO_UNMOD_EVENT_CODE(IIO_VOLTAGE,
						  channel,
						  IIO_EV_TYPE_THRESH,
						  IIO_EV_DIR_FALLING),
			      timestamp);
	}

	return IRQ_HANDLED;
}
```

### Userspace Event Handling

```c
#include <linux/iio/events.h>
#include <poll.h>

int fd = open("/dev/iio:device0", O_RDONLY | O_NONBLOCK);

struct pollfd pfd = {
	.fd = fd,
	.events = POLLIN,
};

while (1) {
	poll(&pfd, 1, -1);  // Wait for event

	struct iio_event_data event;
	read(fd, &event, sizeof(event));

	// Decode event
	int channel = IIO_EVENT_CODE_EXTRACT_CHAN(event.id);
	enum iio_event_type type = IIO_EVENT_CODE_EXTRACT_TYPE(event.id);
	enum iio_event_direction dir = IIO_EVENT_CODE_EXTRACT_DIR(event.id);

	printf("Channel %d threshold %s crossed\n",
	       channel, dir == IIO_EV_DIR_RISING ? "high" : "low");
}
```

## Hardware FIFO Support

### When to Use Hardware FIFO

- Reduce interrupt rate for high-frequency sampling
- Batch samples to save power (wake less often)
- Handle bursty data without loss
- Timestamp accuracy (watermark interrupts)

### FIFO Implementation

```c
static int ad7124_hwfifo_set_watermark(struct iio_dev *indio_dev, unsigned int val)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Set FIFO watermark (interrupt triggers when N samples available)
	if (val > AD7124_FIFO_MAX_SIZE)
		val = AD7124_FIFO_MAX_SIZE;

	st->watermark = val;
	return ad7124_write_fifo_watermark(st, val);
}

static int ad7124_hwfifo_flush(struct iio_dev *indio_dev, unsigned int count)
{
	struct ad7124_state *st = iio_priv(indio_dev);
	u32 *data;
	int i, ret;

	// Allocate buffer for FIFO data
	data = kmalloc(count * sizeof(u32), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	// Read all samples from FIFO
	ret = ad7124_read_fifo(st, data, count);
	if (ret < 0)
		goto out;

	// Push to IIO buffer
	for (i = 0; i < count; i++) {
		iio_push_to_buffers(indio_dev, &data[i]);
	}

	ret = count;
out:
	kfree(data);
	return ret;
}

static const struct iio_buffer_setup_ops ad7124_buffer_ops = {
	.preenable = ad7124_buffer_preenable,
	.postdisable = ad7124_buffer_postdisable,
	.hwfifo_set_watermark = ad7124_hwfifo_set_watermark,
	.hwfifo_flush_to_buffer = ad7124_hwfifo_flush,
};
```

### FIFO Interrupt Handler

```c
static irqreturn_t ad7124_fifo_handler(int irq, void *p)
{
	struct iio_dev *indio_dev = p;
	struct ad7124_state *st = iio_priv(indio_dev);
	unsigned int count;

	// Read FIFO level
	ad7124_read_fifo_level(st, &count);

	// Flush FIFO to buffer
	ad7124_hwfifo_flush(indio_dev, count);

	return IRQ_HANDLED;
}
```

## Calibration

### Self-Calibration

```c
static ssize_t ad7124_calibrate_store(struct device *dev,
				     struct device_attribute *attr,
				     const char *buf, size_t len)
{
	struct iio_dev *indio_dev = dev_to_iio_dev(dev);
	struct ad7124_state *st = iio_priv(indio_dev);
	int ret;
	bool calib;

	ret = kstrtobool(buf, &calib);
	if (ret)
		return ret;

	if (!calib)
		return -EINVAL;

	// Perform self-calibration
	ret = ad7124_self_calibrate(st);
	if (ret)
		return ret;

	return len;
}

static IIO_DEVICE_ATTR(calibrate, 0200, NULL, ad7124_calibrate_store, 0);

static struct attribute *ad7124_attributes[] = {
	&iio_dev_attr_calibrate.dev_attr.attr,
	NULL
};

static const struct attribute_group ad7124_attribute_group = {
	.attrs = ad7124_attributes,
};

static const struct iio_info ad7124_info = {
	// ... other callbacks ...
	.attrs = &ad7124_attribute_group,
};
```

Userspace:
```bash
# Trigger calibration
echo 1 > /sys/bus/iio/devices/iio:device0/calibrate
```

### Calibration Scale/Bias

Using standard IIO calibration attributes:

```c
case IIO_CHAN_INFO_CALIBSCALE:
	// Read calibration scale (as INT_PLUS_MICRO: 1.0 = 1000000)
	*val = 1;
	*val2 = st->calibscale[chan->channel];
	return IIO_VAL_INT_PLUS_MICRO;

case IIO_CHAN_INFO_CALIBBIAS:
	// Read calibration bias (in ADC counts)
	*val = st->calibbias[chan->channel];
	return IIO_VAL_INT;
```

Formula: `calibrated = (raw + calibbias) * calibscale`

## Extended Attributes

### Custom Sysfs Attributes

For device-specific functionality:

```c
static ssize_t ad7124_test_mode_show(struct device *dev,
				     struct device_attribute *attr,
				     char *buf)
{
	struct iio_dev *indio_dev = dev_to_iio_dev(dev);
	struct ad7124_state *st = iio_priv(indio_dev);

	return sprintf(buf, "%d\n", st->test_mode);
}

static ssize_t ad7124_test_mode_store(struct device *dev,
				      struct device_attribute *attr,
				      const char *buf, size_t len)
{
	struct iio_dev *indio_dev = dev_to_iio_dev(dev);
	struct ad7124_state *st = iio_priv(indio_dev);
	unsigned int mode;
	int ret;

	ret = kstrtouint(buf, 10, &mode);
	if (ret)
		return ret;

	if (mode > 3)
		return -EINVAL;

	ret = ad7124_set_test_mode(st, mode);
	if (ret)
		return ret;

	st->test_mode = mode;
	return len;
}

static IIO_DEVICE_ATTR(test_mode, 0644,
		      ad7124_test_mode_show,
		      ad7124_test_mode_store, 0);
```

### Channel-Specific Extended Info

```c
static ssize_t ad7124_read_settling_time(struct iio_dev *indio_dev,
					uintptr_t private,
					const struct iio_chan_spec *chan,
					char *buf)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	return sprintf(buf, "%d\n", st->settling_time[chan->channel]);
}

static ssize_t ad7124_write_settling_time(struct iio_dev *indio_dev,
					 uintptr_t private,
					 const struct iio_chan_spec *chan,
					 const char *buf, size_t len)
{
	struct ad7124_state *st = iio_priv(indio_dev);
	unsigned int time_us;
	int ret;

	ret = kstrtouint(buf, 10, &time_us);
	if (ret)
		return ret;

	ret = ad7124_set_settling_time(st, chan->channel, time_us);
	if (ret)
		return ret;

	st->settling_time[chan->channel] = time_us;
	return len;
}

static const struct iio_chan_spec_ext_info ad7124_ext_info[] = {
	{
		.name = "settling_time_us",
		.read = ad7124_read_settling_time,
		.write = ad7124_write_settling_time,
		.shared = IIO_SEPARATE,
	},
	{ }
};

static const struct iio_chan_spec ad7124_channel = {
	// ... other fields ...
	.ext_info = ad7124_ext_info,
};
```

Creates: `/sys/bus/iio/devices/iio:device0/in_voltage0_settling_time_us`

## Oversampling Ratio

```c
case IIO_CHAN_INFO_OVERSAMPLING_RATIO:
	*val = st->osr[chan->channel];
	return IIO_VAL_INT;

// write_raw:
case IIO_CHAN_INFO_OVERSAMPLING_RATIO:
	// Validate and set oversampling ratio
	if (val < 1 || val > 2048)
		return -EINVAL;

	// Check if power-of-2
	if (!is_power_of_2(val))
		return -EINVAL;

	return ad7124_set_osr(st, chan->channel, val);
```

Add to info_mask:
```c
.info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
		     BIT(IIO_CHAN_INFO_OVERSAMPLING_RATIO),
```

## Filter Configuration

For devices with configurable filters:

```c
static const char * const ad7124_filter_modes[] = {
	"sinc4", "sinc3", "sinc3+sinc1", "average",
};

static int ad7124_get_filter_mode(struct iio_dev *indio_dev,
				 const struct iio_chan_spec *chan)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	return st->filter_mode[chan->channel];
}

static int ad7124_set_filter_mode(struct iio_dev *indio_dev,
				 const struct iio_chan_spec *chan,
				 unsigned int mode)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	return ad7124_write_filter_mode(st, chan->channel, mode);
}

static const struct iio_enum ad7124_filter_enum = {
	.items = ad7124_filter_modes,
	.num_items = ARRAY_SIZE(ad7124_filter_modes),
	.get = ad7124_get_filter_mode,
	.set = ad7124_set_filter_mode,
};

static const struct iio_chan_spec_ext_info ad7124_ext_info[] = {
	IIO_ENUM("filter_mode", IIO_SEPARATE, &ad7124_filter_enum),
	IIO_ENUM_AVAILABLE("filter_mode", &ad7124_filter_enum),
	{ }
};
```

Creates:
- `/sys/bus/iio/devices/iio:device0/in_voltage0_filter_mode`
- `/sys/bus/iio/devices/iio:device0/in_voltage0_filter_mode_available`

## Debugfs Register Access

```c
static int ad7124_reg_access(struct iio_dev *indio_dev,
			    unsigned int reg, unsigned int writeval,
			    unsigned int *readval)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	if (readval)
		return ad7124_read_register(st, reg, readval);
	else
		return ad7124_write_register(st, reg, writeval);
}

static const struct iio_info ad7124_info = {
	// ... other callbacks ...
	.debugfs_reg_access = ad7124_reg_access,
};
```

Usage:
```bash
# Read register 0x01
echo 0x01 > /sys/kernel/debug/iio/iio:device0/direct_reg_access
cat /sys/kernel/debug/iio/iio:device0/direct_reg_access

# Write register 0x01 with value 0x55
echo "0x01 0x55" > /sys/kernel/debug/iio/iio:device0/direct_reg_access
```

## Multi-Device Synchronization

For synchronized sampling across multiple devices:

```c
// Device 1: Master
static int ad7124_master_sync_enable(struct iio_dev *indio_dev)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Configure as sync master
	return ad7124_set_sync_master(st);
}

// Device 2: Slave
static int ad7124_slave_sync_enable(struct iio_dev *indio_dev)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	// Configure as sync slave
	return ad7124_set_sync_slave(st);
}
```

## Performance Monitoring

Add performance counters:

```c
struct ad7124_state {
	// ... other fields ...
	atomic_t samples_captured;
	atomic_t buffer_overruns;
};

// In trigger handler
atomic_inc(&st->samples_captured);

// Expose via sysfs
static ssize_t ad7124_samples_show(struct device *dev,
				  struct device_attribute *attr,
				  char *buf)
{
	struct iio_dev *indio_dev = dev_to_iio_dev(dev);
	struct ad7124_state *st = iio_priv(indio_dev);

	return sprintf(buf, "%d\n", atomic_read(&st->samples_captured));
}

static IIO_DEVICE_ATTR(samples_captured, 0444, ad7124_samples_show, NULL, 0);
```
