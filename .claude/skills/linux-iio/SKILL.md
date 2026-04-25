---
name: linux-iio
description: Comprehensive guide to Linux IIO (Industrial I/O) subsystem for ADC, DAC, IMU, and sensor drivers. Use when implementing IIO drivers, defining channels and attributes, setting up buffered data acquisition, integrating with IIO backend framework, working with triggers and events, or debugging IIO drivers.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: iio
  tags:
    - iio
    - industrial-io
    - adc
    - dac
    - imu
    - sensor
    - buffered-acquisition
    - iio-backend
    - iio-trigger
    - iio-event
  dependencies:
    - linux-spi-controller
    - linux-i2c-controller
    - linux-devicetree
    - linux-dma
    - linux-kconfig-makefile
  learning_objectives:
    - Implement IIO device drivers for ADC/DAC/sensors
    - Define channel specifications with info masks
    - Implement read_raw/write_raw callbacks
    - Set up buffered data acquisition with triggers
    - Integrate IIO backend/frontend architecture
    - Handle IIO events and thresholds
    - Debug IIO drivers using sysfs/libiio
---

# Linux IIO (Industrial I/O) Subsystem

Quick-start guide for implementing IIO drivers for ADCs, DACs, IMUs, and sensors.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User mentions: "implement driver", "probe function", "device registration", "iio_info callbacks"
- Questions about: read_raw, write_raw, read_avail, complete probe flow, devm_* functions
- User asks: "how to implement", "step by step", "ADI patterns", "sigma-delta helper", "JESD204 integration"
- Topics: IIO_VAL return types, minimal driver template, error handling

**Triggers to read reference/channels.md**:
- User mentions: "channel", "iio_chan_spec", "info_mask", "scan_type", "indexed vs modified"
- Questions about: channel types (IIO_VOLTAGE, IIO_ACCEL), modifiers (IIO_MOD_X/Y/Z), info masks
- User asks: "how to define channels", "differential channels", "scan_index", "extended info"
- Topics: storagebits vs realbits, endianness, IIO_CHAN_INFO_*, channel macros

**Triggers to read reference/buffered-acquisition.md**:
- User mentions: "buffer", "trigger", "DMA", "streaming", "continuous sampling", "iio_backend"
- Questions about: triggered buffer setup, trigger handler, scan elements, active_scan_mask
- User asks: "high-speed acquisition", "buffered mode", "push to buffer", "AXI DMA", "frontend/backend"
- Topics: iio_push_to_buffers_with_timestamp, iio_trigger_notify_done, watermark, FIFO

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "YAML", "DTS", "platform-specific examples"
- Questions about: creating bindings, io-backends property, channel child nodes
- User asks: "Zynq example", "ZynqMP example", "Raspberry Pi overlay", "multi-platform"
- Topics: validation, dt_binding_check, supply properties, GPIO properties

**Triggers to read reference/advanced-features.md**:
- User mentions: "events", "threshold", "calibration", "FIFO", "extended attributes", "filter"
- Questions about: IIO_EV_TYPE_THRESH, hwfifo, calibscale/calibbias, custom sysfs
- User asks: "motion detection", "data ready", "oversampling", "performance monitoring"
- Topics: iio_push_event, IIO_DEVICE_ATTR, iio_chan_spec_ext_info, debugfs_reg_access

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "test", "verify", "libiio", "IIO Oscilloscope"
- Questions about: sysfs interface, dynamic debug, buffer testing, trace
- User says: "troubleshoot", "diagnose", "wrong values", "device not appearing"
- Topics: dmesg, debugfs register access, common issues, ftrace, network mode

---

## When to Use This Skill

- Implementing IIO drivers for ADCs, DACs, sensors, IMUs, or frequency devices
- Defining IIO channel specifications (iio_chan_spec)
- Implementing read_raw/write_raw callbacks
- Setting up buffered data acquisition with triggers
- Working with IIO backend/frontend architecture (for high-speed converters)
- Integrating with userspace tools (libiio, IIO Oscilloscope)
- Handling IIO events (thresholds, data ready)
- Debugging IIO drivers and data paths

## IIO Subsystem Overview

### What is IIO?

Industrial I/O (IIO) is the Linux kernel subsystem for:
- **Analog-to-Digital Converters** (ADCs)
- **Digital-to-Analog Converters** (DACs)
- **Inertial Measurement Units** (IMUs - accelerometers, gyroscopes, magnetometers)
- **Sensors** (temperature, pressure, light, proximity)
- **Frequency devices** (PLLs, oscillators, DDS, RF transceivers)

**Key Concept**: An `iio_dev` structure typically represents a single hardware sensor.

### Architecture

```
┌──────────────────────────────────────────────┐
│         Userspace                            │
│  ┌────────────┐    ┌──────────────┐         │
│  │ libiio     │    │ IIO Osc      │         │
│  │ (network)  │    │ (GUI tool)   │         │
│  └────────────┘    └──────────────┘         │
└───────┬──────────────────┬───────────────────┘
        │                  │
   ┌────┴──────────────────┴──────┐
   │ Character Device /dev/iio:X  │  (buffered data, events)
   └────────────┬──────────────────┘
   ┌────────────┴──────────────────┐
   │ Sysfs /sys/bus/iio/devices/   │  (configuration, single reads)
   │   iio:deviceX/                │
   └────────────┬──────────────────┘
                │
   ┌────────────┴──────────────────┐
   │   IIO Core (kernel)           │
   │  - Device management          │
   │  - Buffer handling            │
   │  - Trigger management         │
   └────────────┬──────────────────┘
                │
   ┌────────────┴──────────────────┐
   │   IIO Device Driver           │
   │  (your driver code)           │
   │  - struct iio_dev             │
   │  - struct iio_info callbacks  │
   │  - struct iio_chan_spec []    │
   └────────────┬──────────────────┘
                │
   ┌────────────┴──────────────────┐
   │   Hardware (ADC/DAC/Sensor)   │
   └───────────────────────────────┘
```

## Quick Reference

### Key Data Structures

| Structure | Purpose | Location |
|-----------|---------|----------|
| `struct iio_dev` | Main IIO device | `<linux/iio/iio.h>` |
| `struct iio_chan_spec` | Channel specification | `<linux/iio/iio.h>` |
| `struct iio_info` | Callback functions | `<linux/iio/iio.h>` |
| `struct iio_buffer` | Buffered data acquisition | `<linux/iio/buffer.h>` |
| `struct iio_trigger` | Trigger for synchronized sampling | `<linux/iio/trigger.h>` |
| `struct iio_backend` | Backend/frontend split | `<linux/iio/backend.h>` |

### Channel Types

| Type | Description | Sysfs Prefix |
|------|-------------|--------------|
| IIO_VOLTAGE | Voltage measurement | `in_voltage` |
| IIO_CURRENT | Current measurement | `in_current` |
| IIO_TEMP | Temperature | `in_temp` |
| IIO_ACCEL | Acceleration | `in_accel` |
| IIO_ANGL_VEL | Angular velocity | `in_anglvel` |
| IIO_MAGN | Magnetic field | `in_magn` |
| IIO_PRESSURE | Pressure | `in_pressure` |
| IIO_ALTVOLTAGE | Alternative voltage (PLLs, RF) | `out_altvoltage` |

### Common Info Masks

| Info Type | Sysfs Attribute | Usage |
|-----------|-----------------|-------|
| IIO_CHAN_INFO_RAW | `in_voltage0_raw` | Raw ADC counts |
| IIO_CHAN_INFO_SCALE | `in_voltage0_scale` | Scale factor (V/count) |
| IIO_CHAN_INFO_OFFSET | `in_voltage0_offset` | Offset (counts) |
| IIO_CHAN_INFO_SAMP_FREQ | `sampling_frequency` | Sample rate (Hz) |
| IIO_CHAN_INFO_CALIBSCALE | `in_voltage0_calibscale` | Calibration scale |

**Conversion Formula**: `processed = (raw + offset) * scale`

### IIO_VAL Return Types

| Return Type | Interpretation | Example |
|-------------|----------------|---------|
| IIO_VAL_INT | `*val` | 12345 |
| IIO_VAL_INT_PLUS_MICRO | `*val + *val2/1000000` | 1.5 (val=1, val2=500000) |
| IIO_VAL_FRACTIONAL_LOG2 | `*val / (1 << *val2)` | 2500/65536 (ADC scale) |

## Quick Start: Minimal IIO Driver

```c
#include <linux/iio/iio.h>
#include <linux/spi/spi.h>
#include <linux/module.h>

struct mydev_state {
	struct spi_device *spi;
	u32 vref_mv;
};

static int mydev_read_raw(struct iio_dev *indio_dev,
			 struct iio_chan_spec const *chan,
			 int *val, int *val2, long mask)
{
	struct mydev_state *st = iio_priv(indio_dev);
	int ret;

	switch (mask) {
	case IIO_CHAN_INFO_RAW:
		// CRITICAL: Claim direct mode to prevent buffered mode conflicts
		ret = iio_device_claim_direct_mode(indio_dev);
		if (ret)
			return ret;

		// Read hardware
		ret = spi_read(st->spi, (u8 *)val, 2);
		iio_device_release_direct_mode(indio_dev);

		if (ret < 0)
			return ret;

		return IIO_VAL_INT;

	case IIO_CHAN_INFO_SCALE:
		// ADC scale = vref_mv / 2^realbits
		*val = st->vref_mv;
		*val2 = chan->scan_type.realbits;
		return IIO_VAL_FRACTIONAL_LOG2;

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
		.info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
				     BIT(IIO_CHAN_INFO_SCALE),
		.scan_index = 0,
		.scan_type = {
			.sign = 'u',
			.realbits = 16,
			.storagebits = 16,
			.endianness = IIO_BE,
		},
	},
};

static int mydev_probe(struct spi_device *spi)
{
	struct iio_dev *indio_dev;
	struct mydev_state *st;
	int ret;

	// 1. Allocate IIO device with private data
	indio_dev = devm_iio_device_alloc(&spi->dev, sizeof(*st));
	if (!indio_dev)
		return -ENOMEM;

	st = iio_priv(indio_dev);
	st->spi = spi;
	st->vref_mv = 2500;  // 2.5V reference

	// 2. Setup IIO device structure
	indio_dev->name = spi_get_device_id(spi)->name;
	indio_dev->modes = INDIO_DIRECT_MODE;
	indio_dev->channels = mydev_channels;
	indio_dev->num_channels = ARRAY_SIZE(mydev_channels);
	indio_dev->info = &mydev_info;

	// 3. Register IIO device (MUST BE LAST!)
	return devm_iio_device_register(&spi->dev, indio_dev);
}

static const struct spi_device_id mydev_id[] = {
	{ "mydev", 0 },
	{ }
};
MODULE_DEVICE_TABLE(spi, mydev_id);

static const struct of_device_id mydev_of_match[] = {
	{ .compatible = "adi,mydev" },
	{ }
};
MODULE_DEVICE_TABLE(of, mydev_of_match);

static struct spi_driver mydev_driver = {
	.driver = {
		.name = "mydev",
		.of_match_table = mydev_of_match,
	},
	.probe = mydev_probe,
	.id_table = mydev_id,
};
module_spi_driver(mydev_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("My IIO ADC Driver");
```

## Essential Patterns

### Device Registration

```c
// Use devm_* for automatic cleanup
indio_dev = devm_iio_device_alloc(&spi->dev, sizeof(*st));
st = iio_priv(indio_dev);

// Setup channels and info
indio_dev->channels = mydev_channels;
indio_dev->num_channels = ARRAY_SIZE(mydev_channels);
indio_dev->info = &mydev_info;

// Register LAST (device goes live immediately)
return devm_iio_device_register(&spi->dev, indio_dev);
```

### Channel Definition

```c
#define MYDEV_VOLTAGE_CHANNEL(_index) { \
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

static const struct iio_chan_spec mydev_channels[] = {
	MYDEV_VOLTAGE_CHANNEL(0),
	MYDEV_VOLTAGE_CHANNEL(1),
	MYDEV_VOLTAGE_CHANNEL(2),
	MYDEV_VOLTAGE_CHANNEL(3),
};
```

### Buffered Mode Setup

```c
// In probe, after channel setup
ret = devm_iio_triggered_buffer_setup(&spi->dev, indio_dev,
				     &iio_pollfunc_store_time,
				     &mydev_trigger_handler,
				     NULL);
if (ret)
	return ret;
```

### Trigger Handler

```c
static irqreturn_t mydev_trigger_handler(int irq, void *p)
{
	struct iio_poll_func *pf = p;
	struct iio_dev *indio_dev = pf->indio_dev;
	struct mydev_state *st = iio_priv(indio_dev);

	struct {
		u32 values[4];
		s64 timestamp __aligned(8);  // MUST be aligned!
	} data;

	int i, j = 0;

	// Read only ENABLED channels
	for_each_set_bit(i, indio_dev->active_scan_mask, indio_dev->masklength) {
		mydev_read_channel(st, i, &data.values[j++]);
	}

	// Push to buffer
	iio_push_to_buffers_with_timestamp(indio_dev, &data,
					  iio_get_time_ns(indio_dev));

	// MUST call this!
	iio_trigger_notify_done(indio_dev->trig);

	return IRQ_HANDLED;
}
```

## Common Pitfalls

### 1. Forgetting iio_device_claim_direct_mode()

```c
// WRONG - Can conflict with buffered mode
static int bad_read_raw(...)
{
	return read_hardware();
}

// CORRECT - Claim direct mode first
static int good_read_raw(...)
{
	int ret = iio_device_claim_direct_mode(indio_dev);
	if (ret)
		return ret;

	ret = read_hardware();
	iio_device_release_direct_mode(indio_dev);
	return ret;
}
```

### 2. Registering Device Too Early

```c
// WRONG
iio_device_register(indio_dev);
setup_interrupts();  // Too late!

// CORRECT - Register LAST
setup_interrupts();
iio_device_register(indio_dev);
```

### 3. Not Calling iio_trigger_notify_done()

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

### 4. Misaligned Timestamp in Buffer

```c
// WRONG
struct {
	u32 ch[8];
	s64 timestamp;  // May not be aligned!
} data;

// CORRECT
struct {
	u32 ch[8];
	s64 timestamp __aligned(8);  // Explicitly aligned
} data;
```

## Testing

### Sysfs Interface

```bash
# List devices
ls /sys/bus/iio/devices/

# Read channel
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
cat /sys/bus/iio/devices/iio:device0/in_voltage0_scale

# Test buffered mode
echo 1 > /sys/bus/iio/devices/iio:device0/scan_elements/in_voltage0_en
echo 128 > /sys/bus/iio/devices/iio:device0/buffer/length
echo 1 > /sys/bus/iio/devices/iio:device0/buffer/enable
dd if=/dev/iio:device0 bs=1024 count=10 | hexdump -C
echo 0 > /sys/bus/iio/devices/iio:device0/buffer/enable
```

### libiio Tools

```bash
# Install tools
apt-get install libiio-utils

# List devices
iio_info

# Read attribute
iio_attr -d mydev in_voltage0_raw

# Capture buffered data
iio_readdev -b 256 -s 100 mydev
```

### IIO Oscilloscope

On target:
```bash
systemctl start iiod
```

On host: Connect to `<target-ip>:30431` in IIO Oscilloscope GUI.

## Implementation Checklist

When implementing an IIO driver:

- [ ] Use `devm_iio_device_alloc()` for allocation
- [ ] Define complete `iio_chan_spec` array
- [ ] Implement `read_raw()` callback (minimum)
- [ ] Use `iio_device_claim_direct_mode()` in read_raw
- [ ] Return correct `IIO_VAL_*` types
- [ ] Set `scan_type` correctly (if buffered mode used)
- [ ] Set `scan_index = -1` for non-buffered channels
- [ ] Call `iio_trigger_notify_done()` in trigger handler
- [ ] Align timestamp in buffer struct (`__aligned(8)`)
- [ ] Register with `devm_iio_device_register()` as LAST step
- [ ] Test with sysfs attributes
- [ ] Test buffered mode (if implemented)
- [ ] Test with libiio tools
- [ ] Test with IIO Oscilloscope

## Reference Drivers

Excellent examples in the Linux kernel:

**ADC Drivers**:
- `drivers/iio/adc/ad7124.c` - Sigma-Delta, calibration, buffered
- `drivers/iio/adc/ad4630.c` - High-speed SAR, DMA
- `drivers/iio/adc/ad7606.c` - Multi-channel, oversampling

**DAC Drivers**:
- `drivers/iio/dac/ad3552r.c` - Backend integration, DMA
- `drivers/iio/dac/ad5686.c` - Multi-channel, SPI/I2C variants

**IMU Drivers**:
- `drivers/iio/imu/adis16480.c` - Multi-sensor, buffered, burst read

**RF/Frequency Drivers**:
- `drivers/iio/frequency/ad9081.c` - JESD204, backend, complex
- `drivers/iio/frequency/adf4371.c` - PLL, frequency synthesis

## Related Skills

- **linux-jesd204**: JESD204 high-speed serial interface integration
- **linux-devicetree**: Device tree bindings for IIO devices
- **linux-dma**: DMA integration for high-speed buffers
- **linux-spi-controller**: SPI controllers (for SPI-based converters)
- **linux-debugging**: Debug techniques for IIO drivers

## Documentation References

- **Kernel Docs**: https://docs.kernel.org/driver-api/iio/
  - Core: https://docs.kernel.org/driver-api/iio/core.html
  - Buffers: https://docs.kernel.org/driver-api/iio/buffers.html
  - Triggers: https://docs.kernel.org/driver-api/iio/triggers.html
- **IIO Headers**: `include/linux/iio/iio.h`
- **ADI Wiki**: https://wiki.analog.com/resources/tools-software/linux-drivers/iio-adc
- **libiio**: https://github.com/analogdevicesinc/libiio
- **IIO Oscilloscope**: https://github.com/analogdevicesinc/iio-oscilloscope
