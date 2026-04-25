# IIO Implementation Patterns

Complete guide to implementing IIO device interfaces in no-OS.

## Core Data Structures

### 1. struct iio_device - Device Descriptor

The main structure defining how hardware appears to IIO clients:

```c
struct iio_device {
    uint16_t num_ch;                    // Number of channels
    struct iio_channel *channels;       // Channel array
    struct iio_attribute *attributes;   // Device attributes
    struct iio_attribute *debug_attributes;
    struct iio_attribute *buffer_attributes;

    // Callbacks
    int32_t (*pre_enable)(void *dev, uint32_t mask);
    int32_t (*post_disable)(void *dev);
    int32_t (*submit)(struct iio_device_data *dev);
    int32_t (*trigger_handler)(struct iio_device_data *dev);
    int32_t (*debug_reg_read)(void *dev, uint32_t reg, uint32_t *val);
    int32_t (*debug_reg_write)(void *dev, uint32_t reg, uint32_t val);
};
```

**Example: Temperature sensor**

```c
static struct iio_device max31827_iio_device = {
    .num_ch = NO_OS_ARRAY_SIZE(max31827_channels),
    .channels = max31827_channels,
    .attributes = max31827_attrs,
    .debug_attributes = max31827_debug_attrs,
    .pre_enable = max31827_iio_prepare_buf,
    .trigger_handler = max31827_iio_trigger_handler,
    .debug_reg_read = max31827_iio_reg_read,
    .debug_reg_write = max31827_iio_reg_write,
};
```

### 2. struct iio_channel - Channel Definition

Represents a single data stream (voltage, temperature, accelerometer axis):

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

**Channel Types:**
- `IIO_VOLTAGE` - Voltage measurement
- `IIO_CURRENT` - Current measurement
- `IIO_TEMP` - Temperature
- `IIO_ACCEL` - Acceleration
- `IIO_ANGL_VEL` - Angular velocity (gyroscope)
- `IIO_MAGN` - Magnetic field
- `IIO_POWER` - Power measurement

### 3. struct iio_attribute - Device Settings

Readable/writable parameters like gain, sampling rate, filters:

```c
struct iio_attribute {
    const char *name;              // Attribute name
    intptr_t priv;                 // Private ID
    enum iio_attribute_shared shared;

    // Read attribute
    int (*show)(void *device, char *buf, uint32_t len,
                const struct iio_ch_info *channel, intptr_t priv);

    // Write attribute
    int (*store)(void *device, char *buf, uint32_t len,
                 const struct iio_ch_info *channel, intptr_t priv);
};
```

**Sharing Levels:**
- `IIO_SEPARATE` - Each channel has its own value
- `IIO_SHARED_BY_TYPE` - Shared across channels of same type
- `IIO_SHARED_BY_DIR` - Shared by input or output channels
- `IIO_SHARED_BY_ALL` - Global to all channels

**Example: Sampling frequency and scale**

```c
enum adc_attrs {
    ADC_SAMPLING_FREQUENCY,
    ADC_CHANNEL_SCALE,
};

static struct iio_attribute adc_attrs[] = {
    {
        .name = "sampling_frequency",
        .priv = ADC_SAMPLING_FREQUENCY,
        .shared = IIO_SHARED_BY_ALL,
        .show = adc_get_attr,
        .store = adc_set_attr,
    },
    {
        .name = "scale",
        .priv = ADC_CHANNEL_SCALE,
        .shared = IIO_SEPARATE,
        .show = adc_get_attr,
        .store = adc_set_attr,
    },
    END_ATTRIBUTES_ARRAY
};

int adc_get_attr(void *device, char *buf, uint32_t len,
                 const struct iio_ch_info *channel, intptr_t priv)
{
    struct my_adc_desc *desc = device;

    switch (priv) {
    case ADC_SAMPLING_FREQUENCY:
        return snprintf(buf, len, "%u", desc->sample_rate);
    case ADC_CHANNEL_SCALE:
        return snprintf(buf, len, "%.6f", desc->scale[channel->ch_num]);
    default:
        return -EINVAL;
    }
}
```

### 4. struct scan_type - Data Format

Defines how raw data is packed in the buffer:

```c
struct scan_type {
    char sign;              // 's' = signed, 'u' = unsigned
    uint8_t realbits;       // Valid data bits
    uint8_t storagebits;    // Total bits with padding
    uint8_t shift;          // Right shift before extraction
    bool is_big_endian;
};
```

**Example: 16-bit signed ADC**

```c
static struct scan_type ad7606_scan_type = {
    .sign = 's',
    .realbits = 16,
    .storagebits = 16,
    .shift = 0,
    .is_big_endian = false,
};
```

**Example: 12-bit ADC in 16-bit word (left-aligned)**

```c
static struct scan_type ad7476_scan_type = {
    .sign = 'u',
    .realbits = 12,
    .storagebits = 16,
    .shift = 4,  // Data in upper 12 bits
    .is_big_endian = false,
};
```

## Initialization Workflow

### Step 1: Define IIO Device Structure

```c
// In iio_mydevice.c
static struct iio_device mydevice_iio_descriptor = {
    .num_ch = 4,
    .channels = mydevice_channels,
    .attributes = mydevice_global_attrs,
    .debug_attributes = mydevice_debug_attrs,
    .pre_enable = mydevice_pre_enable,
    .submit = mydevice_submit,
};
```

### Step 2: Initialize Device-Specific IIO Interface

```c
struct mydevice_iio_desc *mydevice_iio;
struct mydevice_iio_init_param mydevice_iio_ip = {
    .base_dev_init = &mydevice_init_param,
};

ret = mydevice_iio_init(&mydevice_iio, &mydevice_iio_ip);
if (ret)
    return ret;
```

### Step 3: Set Up IIO Application

```c
#include "iio_app.h"

struct iio_app_device iio_devices[] = {
    IIO_APP_DEVICE("mydevice", mydevice_iio->dev,
                   &mydevice_iio_descriptor, NULL, NULL, NULL)
};

struct iio_app_init_param app_init_param = {
    .devices = iio_devices,
    .nb_devices = NO_OS_ARRAY_SIZE(iio_devices),
    .uart_init_params = uart_ip,
};

struct iio_app_desc *app;
ret = iio_app_init(&app, &app_init_param);
if (ret)
    return ret;
```

### Step 4: Run IIO Event Loop

```c
while (1) {
    ret = iio_app_run(app);
    if (ret)
        return ret;
}
```

**Alternative: Low-level initialization**

```c
struct iio_init_param iio_init_param = {
    .phy_type = USE_UART,
    .uart_desc = uart_desc,
    .devs = iio_device_inits,
    .nb_devs = 1,
};

struct iio_desc *iio_desc;
ret = iio_init(&iio_desc, &iio_init_param);

while (1) {
    iio_step(iio_desc);  // Process one command
}
```

## Physical Communication Links

### UART (Serial)

```c
struct iio_init_param iio_init = {
    .phy_type = USE_UART,
    .uart_desc = uart_desc,
};
```

**Use case:** USB-to-serial adapters, direct UART to PC

### Network (TCP/IP)

```c
struct tcp_socket_init_param tcp_socket_ip = {
    .max_buff_size = 2048,
};

struct iio_init_param iio_init = {
    .phy_type = USE_NETWORK,
    .tcp_socket_init_param = &tcp_socket_ip,
};
```

**Requires:** `NO_OS_NETWORKING`, `NO_OS_LWIP_NETWORKING`, or `NO_OS_W5500_NETWORKING`

### Local Backend (Custom)

```c
struct iio_local_backend local_backend = {
    .local_backend_event_read = my_read_function,
    .local_backend_event_write = my_write_function,
};

struct iio_init_param iio_init = {
    .phy_type = USE_LOCAL_BACKEND,
    .local_backend = &local_backend,
};
```

**Use case:** Custom protocols, USB bulk endpoints

## Buffered Data Acquisition

High-speed continuous data streaming through buffers.

### Buffer Callbacks

```c
struct iio_device mydevice_iio = {
    .pre_enable = mydevice_pre_enable,      // Before buffer starts
    .post_disable = mydevice_post_disable,  // After buffer stops
    .submit = mydevice_submit,              // Transfer data
    .trigger_handler = mydevice_trigger,    // Trigger event
};
```

### Example: ADC Submit Function

```c
int32_t adc_submit(struct iio_device_data *dev_data)
{
    struct adc_desc *desc = dev_data->dev;
    struct iio_buffer *buffer = dev_data->buffer;
    uint32_t active_ch_mask = buffer->active_mask;
    uint16_t adc_data[8];
    int ret;

    // Read all enabled channels
    for (uint32_t i = 0; i < buffer->samples; i++) {
        ret = adc_read_channels(desc, adc_data, active_ch_mask);
        if (ret)
            return ret;

        ret = iio_buffer_push_scan(buffer, adc_data);
        if (ret)
            return ret;
    }

    return buffer->samples;
}
```

### Example: Pre-enable Callback

```c
int32_t adc_pre_enable(void *dev, uint32_t ch_mask)
{
    struct adc_desc *desc = dev;

    // Configure ADC for enabled channels only
    return adc_set_channel_mask(desc, ch_mask);
}
```

### Example: Trigger Handler

```c
int32_t imu_trigger_handler(struct iio_device_data *dev_data)
{
    struct imu_desc *imu = dev_data->dev;
    struct iio_buffer *buffer = dev_data->buffer;
    uint8_t data[32];

    // Read sensor data (from interrupt or iio_step)
    imu_read_fifo(imu, data, sizeof(data));

    return iio_buffer_push_scan(buffer, data);
}
```

## Context Attributes

System-level information visible to clients:

```c
struct iio_ctx_attr ctx_attrs[] = {
    { .name = "hw_serial", .value = "SN12345" },
    { .name = "hw_model", .value = "MAX20370-EVK" },
    { .name = "fw_version", .value = "1.2.3" },
};

struct iio_init_param iio_init = {
    .ctx_attrs = ctx_attrs,
    .nb_ctx_attr = NO_OS_ARRAY_SIZE(ctx_attrs),
};
```

**View with libiio:**

```bash
$ iio_info
hw_serial: SN12345
hw_model: MAX20370-EVK
fw_version: 1.2.3
```

## How IIO Commands Work

**Client sends:**
```
READ voltage0 raw
```

**IIO framework:**
1. Parses: "READ attribute 'raw' from channel 'voltage0'"
2. Finds channel in `iio_device.channels`
3. Looks up `raw` attribute in `channel.attributes`
4. Calls the `show()` callback
5. Returns result to client

**Your driver's callback:**
```c
int adc_attr_show(void *dev, char *buf, uint32_t len,
                  const struct iio_ch_info *ch, intptr_t priv)
{
    if (priv == ADC_ATTR_RAW) {
        uint16_t data;
        adc_read_channel(dev, ch->ch_num, &data);
        return snprintf(buf, len, "%u", data);
    }
}
```
