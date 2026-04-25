## Driver Implementation Pattern

### Step 1: Define Register Map and Constants

**Example from ADXL345 (ADI accelerometer)**:

```c
#define DT_DRV_COMPAT adi_adxl345

// Register addresses
#define ADXL345_DEVICE_ID_REG         0x00
#define ADXL345_THRESH_TAP_REG        0x1D
#define ADXL345_OFSX_REG              0x1E
#define ADXL345_RATE_REG              0x2C
#define ADXL345_POWER_CTL_REG         0x2D
#define ADXL345_INT_ENABLE            0x2E
#define ADXL345_INT_MAP               0x2F
#define ADXL345_INT_SOURCE_REG        0x30
#define ADXL345_DATA_FORMAT_REG       0x31
#define ADXL345_DATAX0_REG            0x32  // Data starts here (6 bytes)
#define ADXL345_FIFO_CTL_REG          0x38
#define ADXL345_FIFO_STATUS_REG       0x39

// Bit masks
#define ADXL345_PART_ID               0xE5
#define ADXL345_ENABLE_MEASURE_BIT    BIT(3)
#define ADXL345_DATA_FORMAT_FULL_RES  BIT(3)
#define ADXL345_INT_DATA_RDY_MSK      BIT(7)
#define ADXL345_INT_WATERMARK_MSK     BIT(1)
#define ADXL345_INT_ACTIVITY_MSK      BIT(4)

// Data format
#define ADXL345_READ_CMD              BIT(7)
#define ADXL345_MULTIBYTE_FLAG        BIT(6)

// Ranges
enum adxl345_range {
    ADXL345_RANGE_2G  = 0,
    ADXL345_RANGE_4G  = 1,
    ADXL345_RANGE_8G  = 2,
    ADXL345_RANGE_16G = 3,
};

// ODR (Output Data Rate)
enum adxl345_odr {
    ADXL345_ODR_12_5HZ = 7,
    ADXL345_ODR_25HZ   = 8,
    ADXL345_ODR_50HZ   = 9,
    ADXL345_ODR_100HZ  = 10,
    ADXL345_ODR_200HZ  = 11,
    ADXL345_ODR_400HZ  = 12,
};
```

### Step 2: Implement Bus Abstraction (I2C/SPI)

**Pattern for multi-bus support** (from ADXL345):

```c
union adxl345_bus {
    struct i2c_dt_spec i2c;
    struct spi_dt_spec spi;
};

struct adxl345_dev_config {
    union adxl345_bus bus;
    bool (*bus_is_ready)(const union adxl345_bus *bus);
    int (*reg_access)(const struct device *dev, uint8_t cmd,
                     uint8_t addr, uint8_t *data, size_t len);
    uint8_t range;
    uint8_t odr;
    struct gpio_dt_spec interrupt;
    bool route_to_int2;
};

#if DT_ANY_INST_ON_BUS_STATUS_OKAY(i2c)
static bool adxl345_bus_is_ready_i2c(const union adxl345_bus *bus)
{
    return device_is_ready(bus->i2c.bus);
}

static int adxl345_reg_access_i2c(const struct device *dev, uint8_t cmd,
                                  uint8_t reg_addr, uint8_t *data, size_t length)
{
    const struct adxl345_dev_config *cfg = dev->config;

    if (cmd == ADXL345_READ_CMD) {
        return i2c_burst_read_dt(&cfg->bus.i2c, reg_addr, data, length);
    } else {
        return i2c_burst_write_dt(&cfg->bus.i2c, reg_addr, data, length);
    }
}
#endif

#if DT_ANY_INST_ON_BUS_STATUS_OKAY(spi)
static bool adxl345_bus_is_ready_spi(const union adxl345_bus *bus)
{
    return spi_is_ready_dt(&bus->spi);
}

static int adxl345_reg_access_spi(const struct device *dev, uint8_t cmd,
                                  uint8_t reg_addr, uint8_t *data, size_t length)
{
    const struct adxl345_dev_config *cfg = dev->config;
    uint8_t access = reg_addr | cmd | (length == 1 ? 0 : ADXL345_MULTIBYTE_FLAG);
    const struct spi_buf buf[2] = {
        {.buf = &access, .len = 1},
        {.buf = data, .len = length}
    };
    const struct spi_buf_set rx = {.buffers = buf, .count = 2};
    struct spi_buf_set tx = {.buffers = buf, .count = (cmd == ADXL345_READ_CMD ? 1 : 2)};

    if (cmd == ADXL345_READ_CMD) {
        return spi_transceive_dt(&cfg->bus.spi, &tx, &rx);
    } else {
        return spi_write_dt(&cfg->bus.spi, &tx);
    }
}
#endif
```

### Step 3: Implement sample_fetch (Required)

**Purpose**: Trigger sensor measurement and read all channel data.

**Example from ADXL345**:

```c
static int adxl345_sample_fetch(const struct device *dev, enum sensor_channel chan)
{
    struct adxl345_dev_data *data = dev->data;
    const struct adxl345_dev_config *cfg = dev->config;
    uint8_t buf[6];  // X, Y, Z (2 bytes each)

    // Read all axes in one burst
    if (cfg->reg_access(dev, ADXL345_READ_CMD, ADXL345_DATAX0_REG, buf, 6) < 0) {
        return -EIO;
    }

    // Store raw values (little-endian, signed 16-bit)
    data->accel_x = (int16_t)((buf[1] << 8) | buf[0]);
    data->accel_y = (int16_t)((buf[3] << 8) | buf[2]);
    data->accel_z = (int16_t)((buf[5] << 8) | buf[4]);

    return 0;
}
```

**Example from ADT7420 (temperature sensor)**:

```c
static int adt7420_sample_fetch(const struct device *dev,
                                enum sensor_channel chan)
{
    struct adt7420_data *data = dev->data;
    const struct adt7420_dev_config *cfg = dev->config;
    int16_t raw_temp;

    if (i2c_burst_read_dt(&cfg->i2c, ADT7420_REG_TEMP_MSB,
                         (uint8_t *)&raw_temp, 2) < 0) {
        return -EIO;
    }

    data->sample = sys_be16_to_cpu(raw_temp);
    return 0;
}
```

### Step 4: Implement channel_get (Required)

**Purpose**: Convert cached raw data to standard sensor_value format.

**Example from ADXL345**:

```c
static int adxl345_channel_get(const struct device *dev,
                               enum sensor_channel chan,
                               struct sensor_value *val)
{
    struct adxl345_dev_data *data = dev->data;
    const struct adxl345_dev_config *cfg = dev->config;
    int64_t micro_ms2;

    // Calculate scale based on range
    // Full-res mode: 4 mg/LSB regardless of range
    // Fixed-res mode: depends on range setting
    uint32_t scale_factor;  // in micro-g per LSB

    if (data->is_full_res) {
        scale_factor = 3900;  // 3.9 mg/LSB = 3900 µg/LSB
    } else {
        switch (cfg->range) {
        case ADXL345_RANGE_2G:
            scale_factor = 3900;
            break;
        case ADXL345_RANGE_4G:
            scale_factor = 7800;
            break;
        case ADXL345_RANGE_8G:
            scale_factor = 15600;
            break;
        case ADXL345_RANGE_16G:
            scale_factor = 31200;
            break;
        default:
            return -EINVAL;
        }
    }

    switch (chan) {
    case SENSOR_CHAN_ACCEL_X:
        // Convert to m/s²: (raw * scale_µg/LSB * g) / 1000000
        // where g = 9.80665 m/s²
        micro_ms2 = ((int64_t)data->accel_x * scale_factor * 980665LL) / 100000LL;
        val->val1 = micro_ms2 / 1000000;
        val->val2 = micro_ms2 % 1000000;
        break;

    case SENSOR_CHAN_ACCEL_Y:
        micro_ms2 = ((int64_t)data->accel_y * scale_factor * 980665LL) / 100000LL;
        val->val1 = micro_ms2 / 1000000;
        val->val2 = micro_ms2 % 1000000;
        break;

    case SENSOR_CHAN_ACCEL_Z:
        micro_ms2 = ((int64_t)data->accel_z * scale_factor * 980665LL) / 100000LL;
        val->val1 = micro_ms2 / 1000000;
        val->val2 = micro_ms2 % 1000000;
        break;

    case SENSOR_CHAN_ACCEL_XYZ:
        // Return X in val[0], Y in val[1], Z in val[2]
        micro_ms2 = ((int64_t)data->accel_x * scale_factor * 980665LL) / 100000LL;
        val[0].val1 = micro_ms2 / 1000000;
        val[0].val2 = micro_ms2 % 1000000;

        micro_ms2 = ((int64_t)data->accel_y * scale_factor * 980665LL) / 100000LL;
        val[1].val1 = micro_ms2 / 1000000;
        val[1].val2 = micro_ms2 % 1000000;

        micro_ms2 = ((int64_t)data->accel_z * scale_factor * 980665LL) / 100000LL;
        val[2].val1 = micro_ms2 / 1000000;
        val[2].val2 = micro_ms2 % 1000000;
        break;

    default:
        return -ENOTSUP;
    }

    return 0;
}
```

**Example from ADT7420 (simpler, single channel)**:

```c
static int adt7420_channel_get(const struct device *dev,
                               enum sensor_channel chan,
                               struct sensor_value *val)
{
    struct adt7420_data *data = dev->data;

    if (chan != SENSOR_CHAN_AMBIENT_TEMP) {
        return -ENOTSUP;
    }

    // ADT7420: 16-bit signed, 0.0078125 °C per LSB
    // raw >> 3 to get 13-bit signed value
    int64_t temp_micro = ((int64_t)(data->sample >> 3) * 7812500LL) / 1000LL;

    val->val1 = temp_micro / 1000000;
    val->val2 = temp_micro % 1000000;

    return 0;
}
```

### Step 5: Implement attr_set (Optional)

**Purpose**: Configure sensor attributes (frequency, range, thresholds).

**Example from ADXL345 (set sampling frequency)**:

```c
static int adxl345_attr_set(const struct device *dev,
                            enum sensor_channel chan,
                            enum sensor_attribute attr,
                            const struct sensor_value *val)
{
    if (chan != SENSOR_CHAN_ACCEL_XYZ &&
        chan != SENSOR_CHAN_ACCEL_X &&
        chan != SENSOR_CHAN_ACCEL_Y &&
        chan != SENSOR_CHAN_ACCEL_Z) {
        return -ENOTSUP;
    }

    switch (attr) {
    case SENSOR_ATTR_SAMPLING_FREQUENCY:
        return adxl345_attr_set_odr(dev, chan, attr, val);

    case SENSOR_ATTR_FULL_SCALE:
        return adxl345_set_range(dev, val->val1);

    default:
        return -ENOTSUP;
    }
}

static int adxl345_attr_set_odr(const struct device *dev,
                                enum sensor_channel chan,
                                enum sensor_attribute attr,
                                const struct sensor_value *val)
{
    enum adxl345_odr odr;

    switch (val->val1) {
    case 12:
        odr = ADXL345_ODR_12_5HZ;
        break;
    case 25:
        odr = ADXL345_ODR_25HZ;
        break;
    case 50:
        odr = ADXL345_ODR_50HZ;
        break;
    case 100:
        odr = ADXL345_ODR_100HZ;
        break;
    case 200:
        odr = ADXL345_ODR_200HZ;
        break;
    case 400:
        odr = ADXL345_ODR_400HZ;
        break;
    default:
        return -EINVAL;
    }

    return adxl345_reg_write_byte(dev, ADXL345_RATE_REG, odr);
}
```

**Example from ADT7420 (set threshold)**:

```c
static int adt7420_attr_set(const struct device *dev,
                            enum sensor_channel chan,
                            enum sensor_attribute attr,
                            const struct sensor_value *val)
{
    if (chan != SENSOR_CHAN_AMBIENT_TEMP) {
        return -ENOTSUP;
    }

    switch (attr) {
    case SENSOR_ATTR_UPPER_THRESH:
        return adt7420_temp_reg_write(dev, ADT7420_REG_T_HIGH_MSB,
                                     sensor_value_to_adt7420_raw(val));

    case SENSOR_ATTR_LOWER_THRESH:
        return adt7420_temp_reg_write(dev, ADT7420_REG_T_LOW_MSB,
                                     sensor_value_to_adt7420_raw(val));

    default:
        return -ENOTSUP;
    }
}
```

### Step 6: Implement trigger_set (Optional)

**Purpose**: Configure interrupt triggers for data-ready, threshold, or motion events.

**Trigger patterns**:
1. **Global thread**: Use `k_work` submitted to system workqueue
2. **Own thread**: Create dedicated thread with `k_sem`
3. **Directly in ISR**: Minimal processing only

**Example from ADXL345 (data ready trigger)**:

```c
int adxl345_trigger_set(const struct device *dev,
                        const struct sensor_trigger *trig,
                        sensor_trigger_handler_t handler)
{
    const struct adxl345_dev_config *cfg = dev->config;
    struct adxl345_dev_data *data = dev->data;
    uint8_t int_mask, int_en;

    // Disable interrupt during configuration
    gpio_pin_interrupt_configure_dt(&cfg->interrupt, GPIO_INT_DISABLE);

    switch (trig->type) {
    case SENSOR_TRIG_DATA_READY:
        data->drdy_handler = handler;
        data->drdy_trigger = trig;
        int_mask = ADXL345_INT_DATA_RDY_MSK;
        break;

    case SENSOR_TRIG_MOTION:
        data->act_handler = handler;
        data->act_trigger = trig;
        int_mask = ADXL345_INT_ACTIVITY_MSK;

        // Configure activity detection
        adxl345_reg_write_byte(dev, ADXL345_ACT_INACT_CTL_REG,
                              ADXL345_ACT_AC_DC | ADXL345_ACT_X_EN |
                              ADXL345_ACT_Y_EN | ADXL345_ACT_Z_EN);
        break;

    default:
        return -ENOTSUP;
    }

    int_en = handler ? int_mask : 0;

    // Enable/disable interrupt in sensor
    adxl345_reg_write_mask(dev, ADXL345_INT_ENABLE, int_mask, int_en);

    // Route to INT1 or INT2 pin
    adxl345_reg_write_mask(dev, ADXL345_INT_MAP, int_mask,
                          cfg->route_to_int2 ? int_en : ~int_en);

    // Clear pending interrupts
    uint8_t status;
    adxl345_reg_read_byte(dev, ADXL345_INT_SOURCE_REG, &status);

    // Re-enable GPIO interrupt
    if (handler) {
        gpio_pin_interrupt_configure_dt(&cfg->interrupt, GPIO_INT_EDGE_TO_ACTIVE);
    }

    return 0;
}
```

**GPIO callback and work dispatch**:

```c
static void adxl345_gpio_callback(const struct device *dev,
                                  struct gpio_callback *cb, uint32_t pins)
{
    struct adxl345_dev_data *data =
        CONTAINER_OF(cb, struct adxl345_dev_data, gpio_cb);
    const struct adxl345_dev_config *cfg = data->dev->config;

    // Disable interrupt to avoid re-trigger
    gpio_pin_interrupt_configure_dt(&cfg->interrupt, GPIO_INT_DISABLE);

#if defined(CONFIG_ADXL345_TRIGGER_OWN_THREAD)
    k_sem_give(&data->gpio_sem);
#elif defined(CONFIG_ADXL345_TRIGGER_GLOBAL_THREAD)
    k_work_submit(&data->work);
#endif
}

#if defined(CONFIG_ADXL345_TRIGGER_GLOBAL_THREAD)
static void adxl345_work_cb(struct k_work *work)
{
    struct adxl345_dev_data *data =
        CONTAINER_OF(work, struct adxl345_dev_data, work);

    adxl345_thread_cb(data->dev);
}
#endif

static void adxl345_thread_cb(const struct device *dev)
{
    struct adxl345_dev_data *data = dev->data;
    const struct adxl345_dev_config *cfg = dev->config;
    uint8_t int_status;

    // Read interrupt source to clear
    adxl345_reg_read_byte(dev, ADXL345_INT_SOURCE_REG, &int_status);

    if ((data->drdy_handler != NULL) && (int_status & ADXL345_INT_DATA_RDY_MSK)) {
        data->drdy_handler(dev, data->drdy_trigger);
    }

    if ((data->act_handler != NULL) && (int_status & ADXL345_INT_ACTIVITY_MSK)) {
        data->act_handler(dev, data->act_trigger);
    }

    // Re-enable interrupt
    gpio_pin_interrupt_configure_dt(&cfg->interrupt, GPIO_INT_EDGE_TO_ACTIVE);
}
```

### Step 7: Define API Structure

```c
static const struct sensor_driver_api adxl345_api = {
    .attr_set = adxl345_attr_set,
    .attr_get = adxl345_attr_get,
    .sample_fetch = adxl345_sample_fetch,
    .channel_get = adxl345_channel_get,
#ifdef CONFIG_ADXL345_TRIGGER
    .trigger_set = adxl345_trigger_set,
#endif
#ifdef CONFIG_ADXL345_STREAM
    .submit = adxl345_submit,
    .get_decoder = adxl345_get_decoder,
#endif
};
```

### Step 8: Implement Init Function

**Pattern**: Check bus ready → Read device ID → Configure defaults → Enable sensor

**Example from ADXL345**:

```c
static int adxl345_init(const struct device *dev)
{
    const struct adxl345_dev_config *cfg = dev->config;
    struct adxl345_dev_data *data = dev->data;
    uint8_t dev_id;
    int ret;

    // Check bus is ready
    if (!adxl345_bus_is_ready(dev)) {
        LOG_ERR("Bus not ready");
        return -ENODEV;
    }

    // Read and verify device ID
    ret = adxl345_reg_read_byte(dev, ADXL345_DEVICE_ID_REG, &dev_id);
    if (ret < 0) {
        LOG_ERR("Failed to read PART ID: %d", ret);
        return -EIO;
    }

    if (dev_id != ADXL345_PART_ID) {
        LOG_ERR("Invalid PART ID: 0x%02x (expected 0x%02x)", dev_id, ADXL345_PART_ID);
        return -ENODEV;
    }

    // Configure range from devicetree
    ret = adxl345_set_range(dev, cfg->range);
    if (ret < 0) {
        return ret;
    }

    // Configure ODR from devicetree
    ret = adxl345_set_odr(dev, cfg->odr);
    if (ret < 0) {
        return ret;
    }

    // Enable measurement mode
    ret = adxl345_reg_write_byte(dev, ADXL345_POWER_CTL_REG,
                                 ADXL345_ENABLE_MEASURE_BIT);
    if (ret < 0) {
        LOG_ERR("Failed to enable measurement mode");
        return -EIO;
    }

#ifdef CONFIG_ADXL345_TRIGGER
    ret = adxl345_init_interrupt(dev);
    if (ret < 0) {
        LOG_ERR("Failed to initialize interrupt");
        return ret;
    }
#endif

    return 0;
}

int adxl345_init_interrupt(const struct device *dev)
{
    const struct adxl345_dev_config *cfg = dev->config;
    struct adxl345_dev_data *data = dev->data;
    int ret;

    if (!gpio_is_ready_dt(&cfg->interrupt)) {
        LOG_ERR("GPIO port %s not ready", cfg->interrupt.port->name);
        return -EINVAL;
    }

    ret = gpio_pin_configure_dt(&cfg->interrupt, GPIO_INPUT);
    if (ret < 0) {
        return ret;
    }

    gpio_init_callback(&data->gpio_cb, adxl345_gpio_callback,
                      BIT(cfg->interrupt.pin));

    ret = gpio_add_callback(cfg->interrupt.port, &data->gpio_cb);
    if (ret < 0) {
        return ret;
    }

    data->dev = dev;

#if defined(CONFIG_ADXL345_TRIGGER_OWN_THREAD)
    k_sem_init(&data->gpio_sem, 0, 1);
    k_thread_create(&data->thread, data->thread_stack,
                   CONFIG_ADXL345_THREAD_STACK_SIZE,
                   adxl345_thread, data, NULL, NULL,
                   K_PRIO_COOP(CONFIG_ADXL345_THREAD_PRIORITY),
                   0, K_NO_WAIT);
#elif defined(CONFIG_ADXL345_TRIGGER_GLOBAL_THREAD)
    data->work.handler = adxl345_work_cb;
#endif

    return 0;
}
```

### Step 9: Device Instantiation Macro

**Pattern for I2C-only sensor**:

```c
#define ADT7420_INST_DEFINE(inst)                                   \
    static struct adt7420_data adt7420_data_##inst;                \
                                                                    \
    static const struct adt7420_dev_config adt7420_config_##inst = {\
        .i2c = I2C_DT_SPEC_INST_GET(inst),                         \
        COND_CODE_1(DT_INST_NODE_HAS_PROP(inst, int_gpios),        \
            (.int_gpio = GPIO_DT_SPEC_INST_GET(inst, int_gpios),), \
            ())                                                     \
    };                                                              \
                                                                    \
    SENSOR_DEVICE_DT_INST_DEFINE(inst,                             \
                                 adt7420_init,                      \
                                 NULL,                              \
                                 &adt7420_data_##inst,              \
                                 &adt7420_config_##inst,            \
                                 POST_KERNEL,                       \
                                 CONFIG_SENSOR_INIT_PRIORITY,       \
                                 &adt7420_api);

DT_INST_FOREACH_STATUS_OKAY(ADT7420_INST_DEFINE)
```

**Pattern for I2C or SPI sensor** (from ADXL345):

```c
#define ADXL345_CONFIG_I2C(inst)                                    \
    {                                                               \
        .bus.i2c = I2C_DT_SPEC_INST_GET(inst),                     \
        .bus_is_ready = adxl345_bus_is_ready_i2c,                  \
        .reg_access = adxl345_reg_access_i2c,                      \
    }

#define ADXL345_CONFIG_SPI(inst)                                    \
    {                                                               \
        .bus.spi = SPI_DT_SPEC_INST_GET(inst,                      \
                       SPI_OP_MODE_MASTER | SPI_WORD_SET(8) |      \
                       SPI_TRANSFER_MSB, 0),                        \
        .bus_is_ready = adxl345_bus_is_ready_spi,                  \
        .reg_access = adxl345_reg_access_spi,                      \
    }

#define ADXL345_INST_DEFINE(inst)                                   \
    static struct adxl345_dev_data adxl345_data_##inst;            \
                                                                    \
    static const struct adxl345_dev_config adxl345_config_##inst = {\
        COND_CODE_1(DT_INST_ON_BUS(inst, i2c),                     \
            (ADXL345_CONFIG_I2C(inst)),                            \
            (ADXL345_CONFIG_SPI(inst)))                            \
        .range = DT_INST_PROP(inst, range),                        \
        .odr = DT_INST_PROP(inst, odr),                            \
        IF_ENABLED(CONFIG_ADXL345_TRIGGER,                         \
            (.interrupt = GPIO_DT_SPEC_INST_GET_OR(inst, int1_gpios, \
                          GPIO_DT_SPEC_INST_GET(inst, int2_gpios)),))\
    };                                                              \
                                                                    \
    SENSOR_DEVICE_DT_INST_DEFINE(inst,                             \
                                 adxl345_init,                      \
                                 NULL,                              \
                                 &adxl345_data_##inst,              \
                                 &adxl345_config_##inst,            \
                                 POST_KERNEL,                       \
                                 CONFIG_SENSOR_INIT_PRIORITY,       \
                                 &adxl345_api);

DT_INST_FOREACH_STATUS_OKAY(ADXL345_INST_DEFINE)
```

