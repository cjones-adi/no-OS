# IIO API Usage Examples

Complete examples for implementing IIO device interfaces.

## Complete Example: Temperature Sensor

```c
// Define channels
static struct iio_channel temp_channels[] = {
    {
        .name = "temp",
        .ch_type = IIO_TEMP,
        .indexed = false,
        .attributes = temp_channel_attrs,
    },
};

// Define attributes
enum temp_attrs { TEMP_RAW, TEMP_SCALE };

static struct iio_attribute temp_channel_attrs[] = {
    { .name = "raw", .priv = TEMP_RAW, .show = temp_attr_get },
    { .name = "scale", .priv = TEMP_SCALE, .show = temp_attr_get },
    END_ATTRIBUTES_ARRAY
};

int temp_attr_get(void *device, char *buf, uint32_t len,
                  const struct iio_ch_info *ch, intptr_t priv)
{
    struct temp_sensor_desc *desc = device;
    int32_t raw_temp;

    switch (priv) {
    case TEMP_RAW:
        temp_sensor_read(desc, &raw_temp);
        return snprintf(buf, len, "%d", raw_temp);
    case TEMP_SCALE:
        return snprintf(buf, len, "0.0625");  // 0.0625°C/LSB
    default:
        return -EINVAL;
    }
}

// Define IIO device
static struct iio_device temp_iio_device = {
    .num_ch = 1,
    .channels = temp_channels,
};
```

## Common Patterns

### Multi-channel ADC with Per-channel Scale

```c
enum adc_attrs { ADC_RAW, ADC_SCALE, ADC_OFFSET };

static struct iio_attribute adc_ch_attrs[] = {
    { .name = "raw", .priv = ADC_RAW, .show = adc_get_attr },
    { .name = "scale", .priv = ADC_SCALE, .show = adc_get_attr },
    { .name = "offset", .priv = ADC_OFFSET, .show = adc_get_attr },
    END_ATTRIBUTES_ARRAY
};

// Apply to all channels
for (int i = 0; i < num_channels; i++) {
    channels[i].attributes = adc_ch_attrs;
}
```

### Global Sampling Rate Attribute

```c
static struct iio_attribute global_attrs[] = {
    {
        .name = "sampling_frequency",
        .shared = IIO_SHARED_BY_ALL,
        .show = get_sampling_freq,
        .store = set_sampling_freq,
    },
    END_ATTRIBUTES_ARRAY
};
```

### Debug Register Access

```c
int32_t debug_reg_read(void *dev, uint32_t reg, uint32_t *val)
{
    return device_read_register(dev, reg, val);
}

int32_t debug_reg_write(void *dev, uint32_t reg, uint32_t val)
{
    return device_write_register(dev, reg, val);
}
```

## IIO Oscilloscope Integration

### Using IIO Oscilloscope with no-OS Devices

IIO Oscilloscope is a GUI application for viewing and controlling IIO devices.

**Connection over UART:**

```c
struct no_os_uart_init_param uart_ip = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
};

struct iio_app_init_param app_init_param = {
    .devices = iio_devices,
    .nb_devices = 1,
    .uart_init_params = &uart_ip,
};

struct iio_app_desc *app;
iio_app_init(&app, &app_init_param);

while (1) {
    iio_app_run(app);
}
```

**In IIO Oscilloscope:**
1. Select "Serial" transport
2. Choose COM port (e.g., COM3)
3. Set baud rate to 115200
4. Click "Refresh" to scan for devices
5. Device appears in device list

**Connection over Network:**

```c
struct tcp_socket_init_param tcp_socket_ip = {
    .max_buff_size = 2048,
};

struct iio_init_param iio_init = {
    .phy_type = USE_NETWORK,
    .tcp_socket_init_param = &tcp_socket_ip,
};
```

**In IIO Oscilloscope:**
1. Select "Network" transport
2. Enter IP address (e.g., 192.168.1.100)
3. Port: 30431 (default)
4. Click "Refresh"

### Reading Attributes

**From command line (libiio):**

```bash
# Read temperature
iio_attr -d max31827 temp raw
1234

iio_attr -d max31827 temp scale
0.0625

# Calculate actual temperature
python3 -c "print(1234 * 0.0625)"
77.125
```

**From IIO Oscilloscope:**
- Navigate to device in device tree
- Expand channel
- Read/write attributes in attribute panel

### Streaming Data

**Enable buffered capture:**

```c
struct iio_device adc_iio = {
    .pre_enable = adc_pre_enable,
    .submit = adc_submit,
    .post_disable = adc_post_disable,
};
```

**In IIO Oscilloscope:**
1. Select channels to capture
2. Set buffer size (samples per buffer)
3. Click "Play" to start streaming
4. View waveforms in real-time

## libiio Client Examples

### Python Example

```python
import iio

# Connect to device
ctx = iio.Context('serial:/dev/ttyUSB0,115200')

# Get device
dev = ctx.find_device('max31827')

# Read attributes
temp_ch = dev.find_channel('temp')
raw = int(temp_ch.attrs['raw'].value)
scale = float(temp_ch.attrs['scale'].value)
temp_c = raw * scale

print(f"Temperature: {temp_c}°C")

# Set sampling frequency
dev.attrs['sampling_frequency'].value = '10'

# Create buffer for streaming
buffer = iio.Buffer(dev, 100)  # 100 samples
buffer.refill()
data = buffer.read()
```

### C Example

```c
#include <iio.h>

int main(void)
{
    struct iio_context *ctx;
    struct iio_device *dev;
    struct iio_channel *ch;
    char buf[64];

    // Connect
    ctx = iio_create_context_from_uri("serial:/dev/ttyUSB0,115200");
    if (!ctx)
        return -1;

    // Get device
    dev = iio_context_find_device(ctx, "max31827");
    if (!dev)
        return -1;

    // Read attribute
    ch = iio_device_find_channel(dev, "temp", false);
    iio_channel_attr_read(ch, "raw", buf, sizeof(buf));
    printf("Raw temperature: %s\n", buf);

    // Cleanup
    iio_context_destroy(ctx);
    return 0;
}
```

## Advanced Patterns

### Dynamic Channel Configuration

```c
struct iio_channel *create_voltage_channels(int num_channels)
{
    struct iio_channel *channels;

    channels = calloc(num_channels, sizeof(*channels));
    if (!channels)
        return NULL;

    for (int i = 0; i < num_channels; i++) {
        channels[i].ch_type = IIO_VOLTAGE;
        channels[i].channel = i;
        channels[i].indexed = true;
        channels[i].scan_index = i;
        channels[i].attributes = voltage_attrs;
    }

    return channels;
}
```

### State-dependent Attributes

```c
int adc_get_sampling_freq(void *dev, char *buf, uint32_t len,
                          const struct iio_ch_info *ch, intptr_t priv)
{
    struct adc_desc *desc = dev;
    uint32_t freq;

    // Return current sampling frequency based on device state
    if (desc->continuous_mode)
        freq = desc->continuous_freq;
    else
        freq = desc->single_shot_freq;

    return snprintf(buf, len, "%u", freq);
}

int adc_set_sampling_freq(void *dev, char *buf, uint32_t len,
                          const struct iio_ch_info *ch, intptr_t priv)
{
    struct adc_desc *desc = dev;
    uint32_t freq;

    sscanf(buf, "%u", &freq);

    // Validate and apply
    if (freq > desc->max_freq)
        return -EINVAL;

    if (desc->continuous_mode)
        return adc_set_continuous_freq(desc, freq);
    else
        return adc_set_single_shot_freq(desc, freq);
}
```

### Multiple Device Types

```c
struct iio_app_device devices[] = {
    // Temperature sensor
    IIO_APP_DEVICE("temp_sensor",
                   temp_dev,
                   &temp_iio_desc,
                   NULL, NULL, NULL),

    // ADC
    IIO_APP_DEVICE("adc",
                   adc_dev,
                   &adc_iio_desc,
                   NULL, NULL, NULL),

    // DAC
    IIO_APP_DEVICE("dac",
                   dac_dev,
                   &dac_iio_desc,
                   NULL, NULL, NULL),
};

struct iio_app_init_param app_init = {
    .devices = devices,
    .nb_devices = 3,
    .uart_init_params = &uart_ip,
};
```

### Custom Transport Layer

```c
static int32_t my_backend_read(void *conn, char *buf, size_t len)
{
    // Custom read implementation
    return custom_read_function(conn, buf, len);
}

static int32_t my_backend_write(void *conn, const char *buf, size_t len)
{
    // Custom write implementation
    return custom_write_function(conn, buf, len);
}

struct iio_local_backend local_backend = {
    .local_backend_event_read = my_backend_read,
    .local_backend_event_write = my_backend_write,
};

struct iio_init_param iio_init = {
    .phy_type = USE_LOCAL_BACKEND,
    .local_backend = &local_backend,
};
```

## Firmware Update Pattern

```c
enum fw_attrs {
    FW_VERSION,
    FW_UPDATE,
};

static struct iio_attribute ctx_attrs[] = {
    {
        .name = "fw_version",
        .priv = FW_VERSION,
        .show = fw_attr_get,
    },
    {
        .name = "fw_update",
        .priv = FW_UPDATE,
        .store = fw_attr_set,
    },
    END_ATTRIBUTES_ARRAY
};

int fw_attr_get(void *dev, char *buf, uint32_t len,
                const struct iio_ch_info *ch, intptr_t priv)
{
    switch (priv) {
    case FW_VERSION:
        return snprintf(buf, len, "1.2.3");
    default:
        return -EINVAL;
    }
}

int fw_attr_set(void *dev, char *buf, uint32_t len,
                const struct iio_ch_info *ch, intptr_t priv)
{
    if (priv == FW_UPDATE) {
        // Trigger firmware update
        return start_firmware_update(buf);
    }
    return -EINVAL;
}
```

## Calibration Pattern

```c
enum cal_attrs {
    CAL_BIAS,
    CAL_SCALE,
    CAL_APPLY,
};

static struct iio_attribute cal_attrs[] = {
    {
        .name = "calibbias",
        .priv = CAL_BIAS,
        .show = cal_get_attr,
        .store = cal_set_attr,
    },
    {
        .name = "calibscale",
        .priv = CAL_SCALE,
        .show = cal_get_attr,
        .store = cal_set_attr,
    },
    {
        .name = "calibrate",
        .priv = CAL_APPLY,
        .store = cal_set_attr,
    },
    END_ATTRIBUTES_ARRAY
};

int cal_set_attr(void *dev, char *buf, uint32_t len,
                 const struct iio_ch_info *ch, intptr_t priv)
{
    struct sensor_desc *desc = dev;
    int value;

    switch (priv) {
    case CAL_BIAS:
        sscanf(buf, "%d", &value);
        desc->cal_bias = value;
        return 0;
    case CAL_SCALE:
        sscanf(buf, "%d", &value);
        desc->cal_scale = value;
        return 0;
    case CAL_APPLY:
        // Trigger calibration sequence
        return sensor_calibrate(desc);
    default:
        return -EINVAL;
    }
}
```

## Event/Alarm Pattern

```c
enum event_attrs {
    THRESH_RISING_VALUE,
    THRESH_FALLING_VALUE,
    THRESH_RISING_EN,
};

static struct iio_attribute event_attrs[] = {
    {
        .name = "thresh_rising_value",
        .priv = THRESH_RISING_VALUE,
        .show = event_get_attr,
        .store = event_set_attr,
    },
    {
        .name = "thresh_falling_value",
        .priv = THRESH_FALLING_VALUE,
        .show = event_get_attr,
        .store = event_set_attr,
    },
    {
        .name = "thresh_rising_en",
        .priv = THRESH_RISING_EN,
        .show = event_get_attr,
        .store = event_set_attr,
    },
    END_ATTRIBUTES_ARRAY
};

int event_set_attr(void *dev, char *buf, uint32_t len,
                   const struct iio_ch_info *ch, intptr_t priv)
{
    struct sensor_desc *desc = dev;
    int value;

    sscanf(buf, "%d", &value);

    switch (priv) {
    case THRESH_RISING_VALUE:
        return sensor_set_high_thresh(desc, value);
    case THRESH_FALLING_VALUE:
        return sensor_set_low_thresh(desc, value);
    case THRESH_RISING_EN:
        return sensor_enable_high_alarm(desc, value);
    default:
        return -EINVAL;
    }
}
```
