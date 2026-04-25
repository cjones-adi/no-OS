# IIO Channel Specifications

Complete guide to defining IIO channel specifications, types, modifiers, and info masks.

## Channel Specification Structure

```c
static const struct iio_chan_spec ad7124_channel = {
	.type = IIO_VOLTAGE,              // Channel type (voltage, current, etc.)
	.indexed = 1,                      // Use channel index for naming
	.channel = 0,                      // Channel number (index)
	.channel2 = 1,                     // Second channel (for differential)
	.differential = 1,                 // Differential input
	.address = 0,                      // Driver-specific address/config

	// Sysfs attributes this channel supports
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
			     BIT(IIO_CHAN_INFO_SCALE) |
			     BIT(IIO_CHAN_INFO_OFFSET),
	.info_mask_shared_by_type = BIT(IIO_CHAN_INFO_SAMP_FREQ),
	.info_mask_shared_by_dir = 0,
	.info_mask_shared_by_all = 0,

	// For buffered mode
	.scan_index = 0,                   // Position in buffer (-1 to disable buffering)
	.scan_type = {
		.sign = 's',                   // Signed data
		.realbits = 24,                // Actual data bits
		.storagebits = 32,             // Storage size (must be >= realbits)
		.shift = 0,                    // Bit shift in storage
		.endianness = IIO_BE,          // Byte order
	},
};
```

## Channel Types

IIO defines standardized channel types:

| Type | Description | Typical Use | Sysfs Prefix |
|------|-------------|-------------|--------------|
| IIO_VOLTAGE | Voltage measurement | ADC inputs | `in_voltage` |
| IIO_CURRENT | Current measurement | Current sensors | `in_current` |
| IIO_POWER | Power measurement | Power monitors | `in_power` |
| IIO_TEMP | Temperature | Temp sensors | `in_temp` |
| IIO_ACCEL | Acceleration | Accelerometers | `in_accel` |
| IIO_ANGL_VEL | Angular velocity | Gyroscopes | `in_anglvel` |
| IIO_MAGN | Magnetic field | Magnetometers | `in_magn` |
| IIO_PRESSURE | Pressure | Barometers | `in_pressure` |
| IIO_ALTVOLTAGE | Alternative voltage | PLLs, DDS, RF | `out_altvoltage` |
| IIO_PHASE | Phase | Phase measurements | `in_phase` |
| IIO_RESISTANCE | Resistance | RTD measurements | `in_resistance` |

**ADI Pattern**: For RF transceivers and frequency synthesizers, use `IIO_ALTVOLTAGE` with `.output = 1`.

**Direction**: Inputs use `in_`, outputs use `out_` prefix in sysfs.

## Modified vs Indexed Channels

### Indexed Channels

**Indexed channels** (`.indexed = 1`):
- Use `.channel` for index number
- Sysfs: `in_voltage0_raw`, `in_voltage1_raw`, etc.
- Use for: Multiple identical channels

```c
static const struct iio_chan_spec adc_channels[] = {
	{
		.type = IIO_VOLTAGE,
		.indexed = 1,
		.channel = 0,
		.info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
	},
	{
		.type = IIO_VOLTAGE,
		.indexed = 1,
		.channel = 1,
		.info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
	},
};
// Creates: in_voltage0_raw, in_voltage1_raw
```

### Modified Channels

**Modified channels** (`.modified = 1`):
- Use `.channel2` for modifier type
- Modifiers: `IIO_MOD_X`, `IIO_MOD_Y`, `IIO_MOD_Z`, `IIO_MOD_LIGHT_IR`, etc.
- Sysfs: `in_accel_x_raw`, `in_accel_y_raw`, `in_intensity_ir_raw`, etc.
- Use for: Directional sensors, spectral sensors

Example - Accelerometer with X/Y/Z axes:
```c
#define AD_ACCEL_CHANNEL(axis, _address) { \
	.type = IIO_ACCEL, \
	.modified = 1, \
	.channel2 = IIO_MOD_##axis, \
	.address = _address, \
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW), \
	.info_mask_shared_by_type = BIT(IIO_CHAN_INFO_SCALE), \
}

static const struct iio_chan_spec adxl345_channels[] = {
	AD_ACCEL_CHANNEL(X, 0),  // in_accel_x_raw
	AD_ACCEL_CHANNEL(Y, 1),  // in_accel_y_raw
	AD_ACCEL_CHANNEL(Z, 2),  // in_accel_z_raw
};
```

## Info Masks and Sysfs Attributes

Info masks control which sysfs attributes are created for each channel. The **scope** determines sharing behavior:

### Info Mask Scopes

```c
// Separate (unique per channel)
.info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |      // in_voltage0_raw, in_voltage1_raw
		     BIT(IIO_CHAN_INFO_SCALE) |     // in_voltage0_scale, in_voltage1_scale
		     BIT(IIO_CHAN_INFO_OFFSET);     // in_voltage0_offset, in_voltage1_offset

// Shared by all channels of same TYPE (e.g., all voltage channels)
.info_mask_shared_by_type = BIT(IIO_CHAN_INFO_SAMP_FREQ);  // sampling_frequency (shared)

// Shared by all channels of same DIRECTION (input vs output)
.info_mask_shared_by_dir = BIT(IIO_CHAN_INFO_CALIBBIAS);   // Shared input or output channels

// Shared by ALL channels in the device
.info_mask_shared_by_all = BIT(IIO_CHAN_INFO_OVERSAMPLING_RATIO);  // oversampling_ratio (global)
```

### Common Info Types

| Info Type | Sysfs Attribute | Typical read_raw Return | Usage |
|-----------|-----------------|-------------------------|-------|
| IIO_CHAN_INFO_RAW | `in_voltage0_raw` | IIO_VAL_INT | Raw ADC counts |
| IIO_CHAN_INFO_PROCESSED | `in_voltage0_input` | IIO_VAL_INT | Processed value (mV, mA) |
| IIO_CHAN_INFO_SCALE | `in_voltage0_scale` | IIO_VAL_FRACTIONAL_LOG2 | Scale factor (V/count) |
| IIO_CHAN_INFO_OFFSET | `in_voltage0_offset` | IIO_VAL_INT | Offset (counts) |
| IIO_CHAN_INFO_CALIBSCALE | `in_voltage0_calibscale` | IIO_VAL_INT_PLUS_MICRO | Calibration scale |
| IIO_CHAN_INFO_CALIBBIAS | `in_voltage0_calibbias` | IIO_VAL_INT | Calibration bias |
| IIO_CHAN_INFO_SAMP_FREQ | `sampling_frequency` | IIO_VAL_INT_PLUS_MICRO | Sample rate (Hz) |
| IIO_CHAN_INFO_OVERSAMPLING_RATIO | `oversampling_ratio` | IIO_VAL_INT | Oversampling ratio |

**Conversion Formula**: `processed = (raw + offset) * scale`

## Scan Type Configuration

Must match hardware data format for buffered mode:

```c
.scan_type = {
	.sign = 's',           // 's' for signed, 'u' for unsigned
	.realbits = 24,        // Actual valid bits from hardware
	.storagebits = 32,     // Storage size in buffer (must be >= realbits)
	.shift = 0,            // Bit shift within storage
	.endianness = IIO_BE,  // IIO_BE, IIO_LE, or IIO_CPU
},
```

**Important**:
- `scan_index = -1` disables buffering for a channel
- Lower `scan_index` values appear first in buffer
- `storagebits` should be power-of-2 aligned for performance

### Scan Type Examples

**24-bit big-endian signed in 32-bit storage**:
```c
.scan_type = {
	.sign = 's',
	.realbits = 24,
	.storagebits = 32,
	.shift = 0,
	.endianness = IIO_BE,
},
```
Sysfs: `be:s24/32>>0`

**16-bit little-endian unsigned in 16-bit storage**:
```c
.scan_type = {
	.sign = 'u',
	.realbits = 16,
	.storagebits = 16,
	.shift = 0,
	.endianness = IIO_LE,
},
```
Sysfs: `le:u16/16>>0`

**12-bit unsigned shifted 4 bits in 16-bit storage**:
```c
.scan_type = {
	.sign = 'u',
	.realbits = 12,
	.storagebits = 16,
	.shift = 4,
	.endianness = IIO_LE,
},
```
Sysfs: `le:u12/16>>4`

## Differential Channels

Differential channels measure voltage difference between two inputs:

```c
static const struct iio_chan_spec ad7124_diff_channel = {
	.type = IIO_VOLTAGE,
	.indexed = 1,
	.differential = 1,     // Enable differential mode
	.channel = 0,          // Positive input
	.channel2 = 1,         // Negative input
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW),
	.scan_index = 0,
	.scan_type = {
		.sign = 's',
		.realbits = 24,
		.storagebits = 32,
		.endianness = IIO_BE,
	},
};
```

Sysfs naming: `in_voltage0-voltage1_raw` (positive - negative)

## Extended Info Attributes

For custom attributes beyond standard info masks:

```c
static const struct iio_chan_spec_ext_info ad7124_ext_info[] = {
	{
		.name = "test_mode",
		.read = ad7124_read_test_mode,
		.write = ad7124_write_test_mode,
		.shared = IIO_SEPARATE,
	},
	{ }  // NULL terminator
};

static const struct iio_chan_spec ad7124_channel = {
	.type = IIO_VOLTAGE,
	// ... other fields ...
	.ext_info = ad7124_ext_info,
};
```

Creates: `/sys/bus/iio/devices/iio:device0/in_voltage0_test_mode`

## Output Channels

For DACs and output devices:

```c
static const struct iio_chan_spec dac_channel = {
	.type = IIO_VOLTAGE,
	.indexed = 1,
	.output = 1,           // Output channel
	.channel = 0,
	.info_mask_separate = BIT(IIO_CHAN_INFO_RAW) |
			     BIT(IIO_CHAN_INFO_SCALE),
	.scan_index = -1,      // Usually no buffering for DACs
};
```

Sysfs naming: `out_voltage0_raw`, `out_voltage0_scale`

## Multi-Channel Patterns

### Using Macros for Similar Channels

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

### Timestamp Channel

For buffered mode with timestamps:

```c
static const struct iio_chan_spec ad7124_channels[] = {
	// Regular channels
	AD7124_VOLTAGE_CHANNEL(0),
	AD7124_VOLTAGE_CHANNEL(1),
	// Timestamp channel (must be last)
	IIO_CHAN_SOFT_TIMESTAMP(2),  // scan_index = 2
};
```

The `IIO_CHAN_SOFT_TIMESTAMP` macro creates a special timestamp channel automatically.

## Common Pitfalls

### 1. scan_index = 0 for Disabled Channel

**Problem**: Channel appears in buffer when it shouldn't.

```c
// To DISABLE buffering for a channel:
.scan_index = -1,  // Not 0!

// 0 is a VALID index (first position)
```

### 2. Incorrect scan_type Endianness

**Problem**: Userspace reads garbage data.

```c
// Must match hardware byte order
.scan_type = {
	.endianness = IIO_BE,  // Check your hardware!
	// Not IIO_LE if hardware is big-endian
}
```

### 3. storagebits < realbits

**Problem**: Data corruption in buffer.

```c
// WRONG
.scan_type = {
	.realbits = 24,
	.storagebits = 16,  // Too small!
}

// CORRECT
.scan_type = {
	.realbits = 24,
	.storagebits = 32,  // Must be >= realbits
}
```

### 4. Missing Timestamp Alignment

**Problem**: Kernel panic or data corruption in buffer.

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
