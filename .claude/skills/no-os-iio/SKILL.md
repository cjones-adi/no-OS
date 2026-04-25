---
name: no-os-iio
description: 'Comprehensive guide to no-OS IIO (Industrial I/O) framework for analog and digital sensors. Use when implementing IIO drivers for ADCs, DACs, IMUs, temperature sensors, working with channels and attributes, setting up buffered data acquisition, configuring remote device control, streaming sensor data, or integrating with libiio and IIO Oscilloscope tools.'
---

# no-OS IIO (Industrial I/O) Framework

Quick-start guide for implementing IIO device interfaces in no-OS for remote control and data streaming.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "IIO structures", "iio_device", "iio_channel", "scan_type"
- Questions about: core data structures, initialization workflow, transport layers
- Need: complete structure definitions, initialization patterns, buffer callbacks

**Triggers to read reference/channels.md**:
- User asks: "channel types", "configure channels", "scan_index", "channel modifiers"
- Mentions: IIO_VOLTAGE, IIO_TEMP, IIO_ACCEL, differential channels, IMU axes
- Questions about: channel naming, scan types, buffer layout
- Need: channel configuration examples for different device types

**Triggers to read reference/api-usage.md**:
- User asks: "complete example", "IIO Oscilloscope", "libiio", "how to use"
- Mentions: Python/C client code, streaming data, calibration, events
- Questions about: attribute patterns, custom transport, firmware update
- Need: working examples, client integration, advanced patterns

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "optimization", "performance", "how to organize"
- Questions about: attribute design, buffer optimization, error handling, testing
- Need: guidelines, performance optimization, error handling patterns

**Triggers to read reference/troubleshooting.md**:
- Build/runtime errors in user output
- User says: "not working", "error", "fails", "connection problem"
- Specific errors: device not found, attributes missing, buffer data incorrect
- Questions about: debugging techniques, common issues

---

## When to Use This Skill

- Implementing IIO drivers for ADCs, DACs, IMUs, or sensors
- Defining IIO channels and attributes for device control
- Setting up buffered data acquisition and streaming
- Configuring device attributes (gain, sampling rate, filters)
- Working with libiio client applications
- Integrating sensors with IIO Oscilloscope
- Debugging IIO communication issues

## What is IIO?

IIO (Industrial I/O) is a standardized framework for interfacing with analog and digital sensors that enables:

- **Remote device control** - Configure and monitor devices from a host PC
- **Real-time data streaming** - Acquire sensor data at high speed
- **Unified interface** - Same API for ADCs, DACs, IMUs, temperature sensors
- **Multiple transport layers** - UART, USB, Ethernet, or custom backends

### Benefits

- **Interoperability** - Works with libiio and IIO Oscilloscope from Analog Devices
- **Standardization** - Consistent attribute/channel model across all devices
- **Efficiency** - Optimized for bare-metal, real-time systems

## IIO Architecture

```
┌─────────────────────────────────────────┐
│       Host PC (IIO Client)              │
│   ┌───────────────────────────┐         │
│   │ libiio / IIO Oscilloscope │         │
│   └──────────┬────────────────┘         │
└──────────────┼──────────────────────────┘
               │
    Physical Link (UART/Network/USB)
               │
┌──────────────┼──────────────────────────┐
│   Embedded Device (no-OS)               │
│   ┌──────────┴────────────┐             │
│   │  IIO Daemon (iiod)    │             │
│   │  - Command parser     │             │
│   └──────────┬────────────┘             │
│              │                          │
│   ┌──────────┴────────────┐             │
│   │  struct iio_device    │             │
│   │  - Channels           │             │
│   │  - Attributes         │             │
│   └──────────┬────────────┘             │
│              │                          │
│   ┌──────────┴────────────┐             │
│   │  Device Driver        │             │
│   │  (max31827, ad7606)   │             │
│   └───────────────────────┘             │
└─────────────────────────────────────────┘
```

## Quick Start Guide

### 1. Define Channels

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

**Common channel types:**
- `IIO_VOLTAGE` - Voltage measurement (ADC)
- `IIO_CURRENT` - Current measurement
- `IIO_TEMP` - Temperature
- `IIO_ACCEL` - Acceleration (with IIO_MOD_X/Y/Z)
- `IIO_ANGL_VEL` - Angular velocity (gyroscope)
- `IIO_POWER` - Power measurement

### 2. Define Attributes

```c
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
```

### 3. Define IIO Device

```c
static struct iio_device temp_iio_device = {
    .num_ch = NO_OS_ARRAY_SIZE(temp_channels),
    .channels = temp_channels,
    .attributes = temp_global_attrs,
    .debug_attributes = temp_debug_attrs,
    .pre_enable = temp_pre_enable,
    .trigger_handler = temp_trigger_handler,
};
```

### 4. Initialize IIO Application

```c
#include "iio_app.h"

struct iio_app_device iio_devices[] = {
    IIO_APP_DEVICE("temp_sensor", temp_dev,
                   &temp_iio_device, NULL, NULL, NULL)
};

struct iio_app_init_param app_init_param = {
    .devices = iio_devices,
    .nb_devices = NO_OS_ARRAY_SIZE(iio_devices),
    .uart_init_params = &uart_ip,
};

struct iio_app_desc *app;
ret = iio_app_init(&app, &app_init_param);
if (ret)
    return ret;
```

### 5. Run IIO Event Loop

```c
while (1) {
    ret = iio_app_run(app);
    if (ret)
        return ret;
}
```

## Buffered Data Acquisition

For high-speed continuous streaming:

### Define Scan Type

```c
static struct scan_type adc_scan_type = {
    .sign = 's',           // 's' = signed, 'u' = unsigned
    .realbits = 16,        // Valid data bits
    .storagebits = 16,     // Total bits with padding
    .shift = 0,            // Right shift before extraction
    .is_big_endian = false,
};
```

### Implement Buffer Callbacks

```c
int32_t adc_submit(struct iio_device_data *dev_data)
{
    struct adc_desc *desc = dev_data->dev;
    struct iio_buffer *buffer = dev_data->buffer;
    uint16_t adc_data[8];
    int ret;

    // Read all enabled channels
    for (uint32_t i = 0; i < buffer->samples; i++) {
        ret = adc_read_channels(desc, adc_data, buffer->active_mask);
        if (ret)
            return ret;

        ret = iio_buffer_push_scan(buffer, adc_data);
        if (ret)
            return ret;
    }

    return buffer->samples;
}

int32_t adc_pre_enable(void *dev, uint32_t ch_mask)
{
    struct adc_desc *desc = dev;

    // Configure ADC for enabled channels only
    return adc_set_channel_mask(desc, ch_mask);
}

static struct iio_device adc_iio = {
    .pre_enable = adc_pre_enable,      // Before buffer starts
    .submit = adc_submit,              // Transfer data
    .post_disable = adc_post_disable,  // After buffer stops
};
```

## Transport Layers

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

## Client Tools

### Using IIO Oscilloscope

1. Select "Serial" or "Network" transport
2. Configure connection (COM port + baud rate, or IP address)
3. Click "Refresh" to scan for devices
4. Read/write attributes in attribute panel
5. Enable channels and click "Play" to stream data

### Using libiio Command Line

```bash
# List devices
iio_info -u serial:/dev/ttyUSB0,115200

# Read attribute
iio_attr -d mydevice -c voltage0 raw

# Write attribute
iio_attr -d mydevice sampling_frequency 1000

# Stream data
iio_readdev -u serial:/dev/ttyUSB0,115200 mydevice -s 100
```

### Python Example

```python
import iio

ctx = iio.Context('serial:/dev/ttyUSB0,115200')
dev = ctx.find_device('temp_sensor')
ch = dev.find_channel('temp')

raw = int(ch.attrs['raw'].value)
scale = float(ch.attrs['scale'].value)
temp_c = raw * scale

print(f"Temperature: {temp_c}°C")
```

## Quick Reference

| Component | Purpose |
|-----------|---------|
| `struct iio_device` | Device interface (channels, attributes, callbacks) |
| `struct iio_channel` | One data stream (voltage, temp, accel_x) |
| `struct iio_attribute` | Readable/writable parameters |
| `struct scan_type` | Data format for buffered acquisition |
| `iio_app_init()` | Initialize IIO with transport layer |
| `iio_app_run()` | Process IIO commands (main loop) |
| `pre_enable()` | Prepare device before buffer starts |
| `submit()` | Transfer data to/from buffer |
| `trigger_handler()` | Handle trigger events |

### Attribute Sharing Levels

- `IIO_SEPARATE` - Each channel has its own value
- `IIO_SHARED_BY_TYPE` - Shared across channels of same type
- `IIO_SHARED_BY_DIR` - Shared by input or output channels
- `IIO_SHARED_BY_ALL` - Global to all channels

### Common Error Codes

- `-EINVAL` - Invalid parameter
- `-ENODEV` - Device not found
- `-EIO` - I/O error
- `-ENOMEM` - Out of memory
- `-EBUSY` - Device busy
- `-ENOTSUP` - Operation not supported

## Best Practices

1. **Always terminate attribute arrays** with `END_ATTRIBUTES_ARRAY`
2. **Use enums for attribute IDs** instead of magic numbers
3. **Validate channel masks** in `pre_enable()` callback
4. **Return proper error codes** (`-EINVAL`, `-ENODEV`, etc.)
5. **Keep show/store functions lightweight** - avoid long delays
6. **Use scan_index** to define buffer data order
7. **Test with libiio tools** before custom applications
8. **Document attribute units** in driver comments

## Common Patterns

### Multi-channel ADC

```c
static struct iio_channel adc_channels[] = {
    {
        .name = "voltage0",
        .ch_type = IIO_VOLTAGE,
        .channel = 0,
        .indexed = true,
        .scan_index = 0,
        .attributes = adc_ch_attrs,
    },
    {
        .name = "voltage1",
        .ch_type = IIO_VOLTAGE,
        .channel = 1,
        .indexed = true,
        .scan_index = 1,
        .attributes = adc_ch_attrs,
    },
    // Additional channels...
};
```

### IMU with Axis Modifiers

```c
static struct iio_channel imu_channels[] = {
    {
        .name = "accel_x",
        .ch_type = IIO_ACCEL,
        .channel2 = IIO_MOD_X,
        .modified = true,
        .scan_index = 0,
    },
    {
        .name = "accel_y",
        .ch_type = IIO_ACCEL,
        .channel2 = IIO_MOD_Y,
        .modified = true,
        .scan_index = 1,
    },
    {
        .name = "accel_z",
        .ch_type = IIO_ACCEL,
        .channel2 = IIO_MOD_Z,
        .modified = true,
        .scan_index = 2,
    },
};
```

### Global Sampling Rate

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

## Common Issues

**"Device not found"**:
- Check physical connection (UART baudrate, network IP)
- Verify IIO daemon is running (`iio_app_run()` being called)
- Check firewall for network connections

**Attributes not appearing**:
- Verify `END_ATTRIBUTES_ARRAY` terminator
- Check attribute array pointer in channel/device struct
- Ensure show/store functions are not NULL

**Buffer data incorrect**:
- Verify scan_type matches actual data format
- Check scan_index order in channel definitions
- Validate active_mask usage in submit function

**Slow performance**:
- Increase buffer size in transport layer
- Optimize submit function - minimize register reads
- Use DMA if available for bulk transfers
- Check for blocking calls in show/store functions

## Reference Documentation

**When to read each file** (use Read tool):

### reference/implementation.md
Complete IIO data structures, initialization workflow, transport layers, buffer callbacks, and context attributes.

### reference/channels.md
Channel configuration for all device types: voltage, temperature, IMU, current, power, magnetometer. Includes scan types and buffer layout.

### reference/api-usage.md
Complete working examples, libiio integration, IIO Oscilloscope usage, Python/C client code, advanced patterns (calibration, events, firmware update).

### reference/best-practices.md
Implementation guidelines, attribute design patterns, buffer optimization, performance tuning, error handling, testing checklist.

### reference/troubleshooting.md
Connection issues, attribute problems, buffer/streaming issues, build errors, runtime crashes, debugging techniques, common error codes.

---

## Summary

The IIO framework provides:
- **Standardized interface** for sensors and converters
- **Remote control** via libiio and IIO Oscilloscope
- **Flexible architecture** supporting multiple device types
- **Efficient streaming** with buffered acquisition
- **Easy integration** with existing no-OS drivers

**Key steps to implement IIO support:**
1. Define channels with appropriate types and modifiers
2. Implement show/store functions for attributes
3. Configure scan_type for buffer data format
4. Implement buffer callbacks (pre_enable, submit, trigger_handler)
5. Initialize IIO framework with transport layer
6. Run `iio_app_run()` in main loop

The framework handles all protocol details, letting you focus on hardware driver implementation.
