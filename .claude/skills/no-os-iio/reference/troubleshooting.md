# IIO Troubleshooting Guide

Common issues and solutions when implementing and using IIO device interfaces.

## Connection Issues

### "Device not found" in libiio

**Error:**
```bash
$ iio_info -u serial:/dev/ttyUSB0,115200
Unable to create IIO context
```

**Causes and Solutions:**

1. **Physical connection problem**
   - Check USB cable
   - Verify correct COM port (Windows: Device Manager, Linux: `ls /dev/ttyUSB*`)
   - Try different USB port
   - Check UART TX/RX connections (TX→RX, RX→TX)

2. **Wrong baud rate**
   ```c
   // Verify baud rate matches in firmware
   struct no_os_uart_init_param uart_ip = {
       .baud_rate = 115200,  // Must match client
   };
   ```

3. **IIO daemon not running**
   ```c
   // Ensure iio_step() or iio_app_run() is being called
   while (1) {
       ret = iio_app_run(app);  // Must be in main loop
       if (ret)
           break;
   }
   ```

4. **Firewall blocking network connection** (for network transport)
   - Allow TCP port 30431
   - Check with: `telnet <device_ip> 30431`

5. **Device not initialized**
   ```c
   // Verify IIO initialization succeeded
   ret = iio_app_init(&app, &app_init_param);
   if (ret) {
       pr_err("IIO init failed: %d\n", ret);
       return ret;
   }
   ```

### Connection Drops Intermittently

**Symptoms:** Device connects, then disconnects after few seconds

**Causes:**
1. **Blocking operation in callback**
   ```c
   // BAD - blocks IIO daemon
   int get_attr(void *dev, char *buf, uint32_t len, ...)
   {
       no_os_mdelay(1000);  // DON'T DO THIS
       return snprintf(buf, len, "value");
   }
   ```

2. **Buffer overflow in UART**
   - Increase UART buffer size
   - Process data faster in main loop

3. **Watchdog timeout**
   - Feed watchdog in main loop
   - Reduce IIO processing time

## Attribute Issues

### Attributes Not Appearing

**Symptom:** Expected attributes don't show up in `iio_attr` or IIO Oscilloscope

**Causes:**

1. **Missing `END_ATTRIBUTES_ARRAY` terminator**
   ```c
   // WRONG - no terminator
   static struct iio_attribute attrs[] = {
       { .name = "raw", .show = get_raw },
       { .name = "scale", .show = get_scale },
   };

   // CORRECT
   static struct iio_attribute attrs[] = {
       { .name = "raw", .show = get_raw },
       { .name = "scale", .show = get_scale },
       END_ATTRIBUTES_ARRAY  // Required
   };
   ```

2. **Attribute array not linked to channel/device**
   ```c
   // WRONG - attributes not assigned
   static struct iio_channel ch = {
       .name = "voltage0",
       .ch_type = IIO_VOLTAGE,
       // .attributes missing
   };

   // CORRECT
   static struct iio_channel ch = {
       .name = "voltage0",
       .ch_type = IIO_VOLTAGE,
       .attributes = voltage_attrs,  // Assign here
   };
   ```

3. **NULL show/store function pointers**
   ```c
   // WRONG - NULL show function for readable attribute
   { .name = "raw", .show = NULL },

   // CORRECT
   { .name = "raw", .show = get_raw },
   ```

### Attribute Read/Write Fails

**Error:** `-EINVAL` or garbled values

**Causes:**

1. **Buffer overflow in snprintf**
   ```c
   // BAD - doesn't respect length
   int get_attr(void *dev, char *buf, uint32_t len, ...)
   {
       strcpy(buf, "very_long_string_that_overflows");
       return strlen(buf);
   }

   // GOOD
   int get_attr(void *dev, char *buf, uint32_t len, ...)
   {
       return snprintf(buf, len, "value");  // Respects len
   }
   ```

2. **Wrong format in sscanf/snprintf**
   ```c
   // WRONG - format mismatch
   uint32_t value;
   sscanf(buf, "%d", &value);  // Should be %u

   // CORRECT
   uint32_t value;
   sscanf(buf, "%u", &value);
   ```

3. **Device pointer NULL**
   ```c
   int get_attr(void *dev, char *buf, uint32_t len, ...)
   {
       if (!dev)
           return -ENODEV;  // Check device pointer

       struct my_dev *desc = dev;
       // ...
   }
   ```

## Buffer and Streaming Issues

### Buffer Data Incorrect

**Symptoms:** Wrong values, swapped channels, garbage data

**Causes:**

1. **Wrong scan_type**
   ```c
   // Example: 12-bit ADC with data left-aligned in 16-bit word
   static struct scan_type scan = {
       .sign = 'u',
       .realbits = 12,
       .storagebits = 16,
       .shift = 4,  // Must match hardware alignment
       .is_big_endian = false,
   };
   ```

2. **Incorrect scan_index order**
   ```c
   // Buffer layout: [ch0][ch1][ch2][ch3]
   static struct iio_channel channels[] = {
       { .name = "voltage0", .scan_index = 0 },  // First
       { .name = "voltage1", .scan_index = 1 },  // Second
       { .name = "voltage2", .scan_index = 2 },  // Third
       { .name = "voltage3", .scan_index = 3 },  // Fourth
   };
   ```

3. **Wrong active_mask usage**
   ```c
   int32_t submit(struct iio_device_data *dev_data)
   {
       uint32_t mask = dev_data->buffer->active_mask;

       // Read ONLY enabled channels
       for (int i = 0; i < MAX_CH; i++) {
           if (mask & (1 << i)) {
               // Read channel i
           }
       }
   }
   ```

4. **Endianness mismatch**
   ```c
   // Device outputs big-endian, but scan_type says little-endian
   static struct scan_type scan = {
       .is_big_endian = true,  // Must match hardware
   };
   ```

### No Data in Buffer

**Symptom:** `iio_readdev` returns 0 samples or times out

**Causes:**

1. **submit callback not implemented**
   ```c
   static struct iio_device dev = {
       .submit = adc_submit,  // Required for buffered mode
   };
   ```

2. **submit returns error**
   ```c
   int32_t submit(struct iio_device_data *dev_data)
   {
       int ret;

       ret = read_hardware(dev_data->dev);
       if (ret) {
           pr_err("Read failed: %d\n", ret);
           return ret;  // Error propagates to client
       }

       return iio_buffer_push_scan(dev_data->buffer, data);
   }
   ```

3. **pre_enable fails silently**
   ```c
   int32_t pre_enable(void *dev, uint32_t mask)
   {
       int ret = configure_channels(dev, mask);
       if (ret) {
           pr_err("Channel config failed: %d\n", ret);
           return ret;  // Must return error
       }
       return 0;
   }
   ```

### Slow Streaming Performance

**Symptoms:** Low sample rate, dropped samples, laggy response

**Optimizations:**

1. **Use burst/block reads**
   ```c
   // SLOW - 6 separate I2C transactions
   for (int i = 0; i < 6; i++)
       data[i] = read_register(base_reg + i);

   // FAST - single I2C burst read
   i2c_burst_read(base_reg, data, 6);
   ```

2. **Increase buffer sizes**
   ```c
   // Transport buffer
   struct tcp_socket_init_param tcp_ip = {
       .max_buff_size = 4096,  // Larger = fewer transfers
   };
   ```

3. **Enable DMA** (if available)
   ```c
   int32_t submit(struct iio_device_data *dev_data)
   {
       return adc_dma_read(dev, dev_data->buffer->buff,
                          dev_data->buffer->samples);
   }
   ```

4. **Avoid blocking calls**
   ```c
   // BAD
   int32_t submit(...)
   {
       no_os_mdelay(10);  // Blocks streaming
   }

   // GOOD - use hardware FIFO or DMA
   int32_t submit(...)
   {
       return read_fifo_nonblocking(...);
   }
   ```

## Build and Runtime Errors

### Linker Error: Undefined Reference to IIO Functions

**Error:**
```
undefined reference to `iio_init'
undefined reference to `iio_step'
```

**Solution:** Add IIO library to build

For Makefile projects:
```makefile
SRCS += $(NO-OS)/iio/iio.c
INCS += $(NO-OS)/iio/iio.h
```

### Runtime Crash in iio_step()

**Symptom:** Segmentation fault or hard fault

**Common causes:**

1. **NULL device pointer**
   ```c
   struct iio_app_device devices[] = {
       IIO_APP_DEVICE("mydev", NULL, &desc, ...) // NULL device
   };
   ```

2. **Stack overflow in attribute callback**
   ```c
   int get_attr(...)
   {
       char huge_buffer[10000];  // Too large for stack
   }
   ```

3. **Uninitialized IIO descriptor**
   ```c
   struct iio_desc *iio;
   // Forgot to call iio_init()
   iio_step(iio);  // CRASH - iio is uninitialized
   ```

### Memory Corruption

**Symptoms:** Random crashes, data corruption, watchdog resets

**Debugging:**

1. **Check buffer bounds**
   ```c
   int get_attr(void *dev, char *buf, uint32_t len, ...)
   {
       // WRONG - no length check
       sprintf(buf, "%s", very_long_string);

       // CORRECT
       return snprintf(buf, len, "%s", string);
   }
   ```

2. **Validate iio_buffer_push_scan() data size**
   ```c
   uint8_t data[8];
   // Must match total size of enabled channels
   iio_buffer_push_scan(buffer, data);
   ```

3. **Check for double-free**
   ```c
   // Make sure post_disable cleanup is idempotent
   int32_t post_disable(void *dev)
   {
       if (desc->buffer) {
           free(desc->buffer);
           desc->buffer = NULL;  // Prevent double-free
       }
   }
   ```

## IIO Oscilloscope Issues

### Device Appears but Channels Missing

**Cause:** Channel definition incomplete

```c
// WRONG - missing required fields
static struct iio_channel ch = {
    .name = "voltage0",
};

// CORRECT
static struct iio_channel ch = {
    .name = "voltage0",
    .ch_type = IIO_VOLTAGE,
    .indexed = true,
    .channel = 0,
};
```

### "Failed to enable buffer" Error

**Causes:**

1. **pre_enable returns error**
   - Add debug logging to pre_enable
   - Verify channel mask is valid

2. **No scan_type defined for buffered channels**
   ```c
   static struct iio_channel ch = {
       .name = "voltage0",
       .scan_type = &voltage_scan,  // Required for buffering
   };
   ```

### DMM Tab Shows "N/A"

**Cause:** Missing `raw` and `scale` attributes

```c
static struct iio_attribute ch_attrs[] = {
    { .name = "raw", .show = get_raw },      // Required for DMM
    { .name = "scale", .show = get_scale },  // Required for DMM
    END_ATTRIBUTES_ARRAY
};
```

## Debugging Techniques

### Enable Debug Logging

```c
#define DEBUG
#include "no_os_print_log.h"

int get_attr(...)
{
    pr_debug("get_attr: priv=%d, ch=%d\n", priv, ch->ch_num);
    // ...
}
```

### Trace IIO Commands

Add logging to show/store callbacks:

```c
int get_attr(void *dev, char *buf, uint32_t len,
             const struct iio_ch_info *ch, intptr_t priv)
{
    pr_info("IIO READ: ch=%s attr=%d\n", ch->name, priv);
    // ... actual implementation
}
```

### Verify Buffer Contents

```c
int32_t submit(struct iio_device_data *dev_data)
{
    uint16_t data[4];

    adc_read_channels(desc, data, mask);

    // Debug: print buffer contents
    pr_debug("Buffer: %04X %04X %04X %04X\n",
             data[0], data[1], data[2], data[3]);

    return iio_buffer_push_scan(buffer, data);
}
```

### Use libiio Verbosity

```bash
# Maximum verbosity
iio_info -u serial:/dev/ttyUSB0,115200 -v

# See raw protocol
export LIBIIO_LOG_LEVEL=DEBUG
iio_attr -d mydev temp raw
```

### Test with Command-line Tools First

Before using IIO Oscilloscope or custom apps:

```bash
# 1. Verify device detected
iio_info -u <uri>

# 2. Check attribute read
iio_attr -d mydev -c voltage0 raw

# 3. Test attribute write
iio_attr -d mydev sampling_frequency 1000

# 4. Verify buffer mode
iio_readdev -u <uri> mydev -s 10
```

## Common Error Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| `-EINVAL` | Invalid argument | Bad parameter, out of range value |
| `-ENODEV` | No such device | Device pointer NULL or not initialized |
| `-EIO` | I/O error | I2C/SPI communication failure |
| `-ENOMEM` | Out of memory | malloc/calloc failed |
| `-EBUSY` | Device busy | Operation in progress, can't reconfigure |
| `-ENOTSUP` | Not supported | Feature not implemented |
| `-ENOBUFS` | No buffer space | IIO buffer full |
| `-ETIMEDOUT` | Timeout | Hardware not responding |

## Performance Profiling

### Measure Callback Execution Time

```c
int get_attr(...)
{
    uint32_t start = get_time_us();

    // ... implementation

    uint32_t elapsed = get_time_us() - start;
    if (elapsed > 1000)  // > 1ms is slow
        pr_warning("Slow callback: %u us\n", elapsed);

    return ret;
}
```

### Monitor Sample Rate

```c
static uint32_t sample_count = 0;
static uint32_t last_report_time = 0;

int32_t submit(...)
{
    sample_count++;

    uint32_t now = get_time_ms();
    if (now - last_report_time >= 1000) {
        pr_info("Sample rate: %u Hz\n", sample_count);
        sample_count = 0;
        last_report_time = now;
    }

    // ... normal submit implementation
}
```
