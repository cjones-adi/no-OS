# IIO Channel Configuration

Complete guide to configuring IIO channels for different device types.

## Channel Structure

```c
struct iio_channel {
    const char *name;              // "voltage0", "temp", "accel_x"
    enum iio_chan_type ch_type;    // IIO_VOLTAGE, IIO_TEMP, IIO_ACCEL
    int channel;                   // Channel number
    int channel2;                  // Modifier (IIO_MOD_X, IIO_MOD_Y)
    unsigned long address;         // Driver-specific identifier
    int scan_index;                // Order in buffer
    struct scan_type *scan_type;   // Data format
    struct iio_attribute *attributes;
    bool ch_out;                   // Output channel
    bool indexed;                  // Show channel number
    bool modified;                 // Has modifier
    bool differential;             // Differential channel
};
```

## Channel Types

### Voltage Channels (IIO_VOLTAGE)

For ADCs and voltage measurement devices.

**Example: 4-channel ADC**

```c
static struct iio_channel ad7606_channels[] = {
    {
        .name = "voltage0",
        .ch_type = IIO_VOLTAGE,
        .channel = 0,
        .scan_index = 0,
        .indexed = true,
        .attributes = ad7606_channel_attrs,
    },
    {
        .name = "voltage1",
        .ch_type = IIO_VOLTAGE,
        .channel = 1,
        .scan_index = 1,
        .indexed = true,
        .attributes = ad7606_channel_attrs,
    },
    {
        .name = "voltage2",
        .ch_type = IIO_VOLTAGE,
        .channel = 2,
        .scan_index = 2,
        .indexed = true,
        .attributes = ad7606_channel_attrs,
    },
    {
        .name = "voltage3",
        .ch_type = IIO_VOLTAGE,
        .channel = 3,
        .scan_index = 3,
        .indexed = true,
        .attributes = ad7606_channel_attrs,
    },
};
```

**Differential channels:**

```c
static struct iio_channel diff_channels[] = {
    {
        .name = "voltage0-voltage1",
        .ch_type = IIO_VOLTAGE,
        .channel = 0,
        .channel2 = 1,
        .differential = true,
        .indexed = true,
        .scan_index = 0,
    },
};
```

### Temperature Channels (IIO_TEMP)

For temperature sensors.

```c
static struct iio_channel temp_channels[] = {
    {
        .name = "temp",
        .ch_type = IIO_TEMP,
        .indexed = false,
        .attributes = temp_channel_attrs,
    },
};
```

**Multiple temperature sensors:**

```c
static struct iio_channel multi_temp_channels[] = {
    {
        .name = "temp0",  // Internal sensor
        .ch_type = IIO_TEMP,
        .channel = 0,
        .indexed = true,
        .scan_index = 0,
    },
    {
        .name = "temp1",  // External sensor
        .ch_type = IIO_TEMP,
        .channel = 1,
        .indexed = true,
        .scan_index = 1,
    },
};
```

### IMU Channels (IIO_ACCEL, IIO_ANGL_VEL)

For accelerometers and gyroscopes with axis modifiers.

**Example: 6-axis IMU**

```c
static struct iio_channel adis_channels[] = {
    // Gyroscope X axis
    {
        .name = "anglvel_x",
        .ch_type = IIO_ANGL_VEL,
        .channel2 = IIO_MOD_X,
        .modified = true,
        .scan_index = 0,
        .scan_type = &adis_scan_type,
    },
    // Gyroscope Y axis
    {
        .name = "anglvel_y",
        .ch_type = IIO_ANGL_VEL,
        .channel2 = IIO_MOD_Y,
        .modified = true,
        .scan_index = 1,
        .scan_type = &adis_scan_type,
    },
    // Gyroscope Z axis
    {
        .name = "anglvel_z",
        .ch_type = IIO_ANGL_VEL,
        .channel2 = IIO_MOD_Z,
        .modified = true,
        .scan_index = 2,
        .scan_type = &adis_scan_type,
    },
    // Accelerometer X axis
    {
        .name = "accel_x",
        .ch_type = IIO_ACCEL,
        .channel2 = IIO_MOD_X,
        .modified = true,
        .scan_index = 3,
        .scan_type = &adis_scan_type,
    },
    // Accelerometer Y axis
    {
        .name = "accel_y",
        .ch_type = IIO_ACCEL,
        .channel2 = IIO_MOD_Y,
        .modified = true,
        .scan_index = 4,
        .scan_type = &adis_scan_type,
    },
    // Accelerometer Z axis
    {
        .name = "accel_z",
        .ch_type = IIO_ACCEL,
        .channel2 = IIO_MOD_Z,
        .modified = true,
        .scan_index = 5,
        .scan_type = &adis_scan_type,
    },
};
```

**Axis Modifiers:**
- `IIO_MOD_X` - X axis
- `IIO_MOD_Y` - Y axis
- `IIO_MOD_Z` - Z axis

### Current Channels (IIO_CURRENT)

For current measurement devices.

```c
static struct iio_channel current_channels[] = {
    {
        .name = "current0",
        .ch_type = IIO_CURRENT,
        .channel = 0,
        .indexed = true,
        .scan_index = 0,
    },
};
```

### Power Channels (IIO_POWER)

For power measurement devices.

```c
static struct iio_channel power_channels[] = {
    {
        .name = "power",
        .ch_type = IIO_POWER,
        .indexed = false,
    },
};
```

### Magnetometer Channels (IIO_MAGN)

For magnetic field sensors.

```c
static struct iio_channel mag_channels[] = {
    {
        .name = "magn_x",
        .ch_type = IIO_MAGN,
        .channel2 = IIO_MOD_X,
        .modified = true,
        .scan_index = 0,
    },
    {
        .name = "magn_y",
        .ch_type = IIO_MAGN,
        .channel2 = IIO_MOD_Y,
        .modified = true,
        .scan_index = 1,
    },
    {
        .name = "magn_z",
        .ch_type = IIO_MAGN,
        .channel2 = IIO_MOD_Z,
        .modified = true,
        .scan_index = 2,
    },
};
```

## Output Channels (DACs)

For DAC (Digital-to-Analog Converter) devices.

```c
static struct iio_channel dac_channels[] = {
    {
        .name = "voltage0",
        .ch_type = IIO_VOLTAGE,
        .channel = 0,
        .ch_out = true,        // Output channel
        .indexed = true,
        .scan_index = 0,
        .attributes = dac_attrs,
    },
    {
        .name = "voltage1",
        .ch_type = IIO_VOLTAGE,
        .channel = 1,
        .ch_out = true,
        .indexed = true,
        .scan_index = 1,
        .attributes = dac_attrs,
    },
};
```

## Channel Naming Conventions

### Indexed Channels

Use `indexed = true` and set `channel` number:
- `voltage0`, `voltage1`, `voltage2`
- `temp0`, `temp1`
- `current0`, `current1`

### Modified Channels

Use `modified = true` and set `channel2` modifier:
- `accel_x`, `accel_y`, `accel_z`
- `anglvel_x`, `anglvel_y`, `anglvel_z`
- `magn_x`, `magn_y`, `magn_z`

### Single Channels

Use `indexed = false` and no `channel` number:
- `temp` (single temperature sensor)
- `power` (single power meter)
- `current` (single current sensor)

### Differential Channels

Set both `channel` and `channel2` with `differential = true`:
- `voltage0-voltage1` (differential between channels 0 and 1)
- Name format: `voltage{ch}-voltage{ch2}`

## Scan Index and Buffer Order

The `scan_index` determines the order channels appear in buffered data.

**Example: 4-channel ADC buffer layout**

```c
static struct iio_channel adc_channels[] = {
    { .name = "voltage0", .scan_index = 0 },  // First in buffer
    { .name = "voltage1", .scan_index = 1 },  // Second in buffer
    { .name = "voltage2", .scan_index = 2 },  // Third in buffer
    { .name = "voltage3", .scan_index = 3 },  // Fourth in buffer
};
```

**Buffer layout:**
```
[voltage0_data][voltage1_data][voltage2_data][voltage3_data]
```

**If selective channels enabled (e.g., channels 0 and 2):**
```
[voltage0_data][voltage2_data]
```

The framework automatically packs only enabled channels based on `scan_index` order.

## Scan Type - Data Format

Defines how channel data is packed in the buffer.

```c
struct scan_type {
    char sign;              // 's' = signed, 'u' = unsigned
    uint8_t realbits;       // Valid data bits
    uint8_t storagebits;    // Total bits with padding
    uint8_t shift;          // Right shift before extraction
    bool is_big_endian;
};
```

### Common Scan Types

**16-bit signed (no padding):**

```c
static struct scan_type signed16_scan = {
    .sign = 's',
    .realbits = 16,
    .storagebits = 16,
    .shift = 0,
    .is_big_endian = false,
};
```

**12-bit unsigned (16-bit storage, left-aligned):**

```c
static struct scan_type unsigned12_scan = {
    .sign = 'u',
    .realbits = 12,
    .storagebits = 16,
    .shift = 4,  // Data in upper 12 bits
    .is_big_endian = false,
};
```

**24-bit signed (32-bit storage):**

```c
static struct scan_type signed24_scan = {
    .sign = 's',
    .realbits = 24,
    .storagebits = 32,
    .shift = 0,
    .is_big_endian = false,
};
```

**16-bit big-endian:**

```c
static struct scan_type be16_scan = {
    .sign = 's',
    .realbits = 16,
    .storagebits = 16,
    .shift = 0,
    .is_big_endian = true,
};
```

## Channel Attributes

Each channel can have attributes for configuration and data access.

**Common channel attributes:**
- `raw` - Raw ADC value
- `scale` - Scale factor to convert raw to real units
- `offset` - Offset to apply after scaling
- `calibbias` - Calibration bias
- `calibscale` - Calibration scale

**Example:**

```c
enum channel_attrs {
    CH_RAW,
    CH_SCALE,
    CH_OFFSET,
};

static struct iio_attribute ch_attrs[] = {
    {
        .name = "raw",
        .priv = CH_RAW,
        .show = ch_attr_get,
    },
    {
        .name = "scale",
        .priv = CH_SCALE,
        .show = ch_attr_get,
    },
    {
        .name = "offset",
        .priv = CH_OFFSET,
        .show = ch_attr_get,
        .store = ch_attr_set,
    },
    END_ATTRIBUTES_ARRAY
};
```

## Complete Examples

### Temperature Sensor

```c
static struct iio_channel temp_channels[] = {
    {
        .name = "temp",
        .ch_type = IIO_TEMP,
        .indexed = false,
        .attributes = temp_channel_attrs,
    },
};
```

### 8-Channel ADC

```c
static struct iio_channel adc_channels[8];

// Initialize in driver init function
for (int i = 0; i < 8; i++) {
    adc_channels[i].ch_type = IIO_VOLTAGE;
    adc_channels[i].channel = i;
    adc_channels[i].indexed = true;
    adc_channels[i].scan_index = i;
    adc_channels[i].scan_type = &adc_scan_type;
    adc_channels[i].attributes = adc_ch_attrs;
}
```

### 9-Axis IMU (Accel + Gyro + Mag)

```c
static struct iio_channel imu_channels[] = {
    // Gyroscope
    { .name = "anglvel_x", .ch_type = IIO_ANGL_VEL, .channel2 = IIO_MOD_X,
      .modified = true, .scan_index = 0 },
    { .name = "anglvel_y", .ch_type = IIO_ANGL_VEL, .channel2 = IIO_MOD_Y,
      .modified = true, .scan_index = 1 },
    { .name = "anglvel_z", .ch_type = IIO_ANGL_VEL, .channel2 = IIO_MOD_Z,
      .modified = true, .scan_index = 2 },
    // Accelerometer
    { .name = "accel_x", .ch_type = IIO_ACCEL, .channel2 = IIO_MOD_X,
      .modified = true, .scan_index = 3 },
    { .name = "accel_y", .ch_type = IIO_ACCEL, .channel2 = IIO_MOD_Y,
      .modified = true, .scan_index = 4 },
    { .name = "accel_z", .ch_type = IIO_ACCEL, .channel2 = IIO_MOD_Z,
      .modified = true, .scan_index = 5 },
    // Magnetometer
    { .name = "magn_x", .ch_type = IIO_MAGN, .channel2 = IIO_MOD_X,
      .modified = true, .scan_index = 6 },
    { .name = "magn_y", .ch_type = IIO_MAGN, .channel2 = IIO_MOD_Y,
      .modified = true, .scan_index = 7 },
    { .name = "magn_z", .ch_type = IIO_MAGN, .channel2 = IIO_MOD_Z,
      .modified = true, .scan_index = 8 },
};
```
