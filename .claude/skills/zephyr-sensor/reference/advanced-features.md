## Advanced Features

### FIFO Support

**Purpose**: Buffer multiple samples to reduce interrupt frequency and CPU load.

**Example from ADXL345**:

```c
enum adxl345_fifo_mode {
    ADXL345_FIFO_BYPASSED = 0,  // No FIFO
    ADXL345_FIFO_STREAMED = 2,  // Continuous streaming
    ADXL345_FIFO_TRIGGERED = 3, // Start on trigger, stop when full
};

int adxl345_configure_fifo(const struct device *dev,
                           enum adxl345_fifo_mode mode,
                           enum adxl345_fifo_trigger trigger,
                           uint16_t fifo_samples)
{
    uint8_t fifo_config;

    if (fifo_samples > 32) {
        return -EINVAL;
    }

    fifo_config = (ADXL345_FIFO_CTL_TRIGGER_MODE(trigger) |
                  ADXL345_FIFO_CTL_MODE_MODE(mode) |
                  ADXL345_FIFO_CTL_SAMPLES_MODE(fifo_samples));

    return adxl345_reg_write_byte(dev, ADXL345_FIFO_CTL_REG, fifo_config);
}

// Watermark trigger: fires when FIFO has N samples
static int adxl345_trigger_set_watermark(const struct device *dev, uint8_t watermark)
{
    // Configure FIFO in stream mode with watermark
    adxl345_configure_fifo(dev, ADXL345_FIFO_STREAMED, ADXL345_INT1, watermark);

    // Enable watermark interrupt
    adxl345_reg_write_mask(dev, ADXL345_INT_ENABLE,
                          ADXL345_INT_WATERMARK_MSK,
                          ADXL345_INT_WATERMARK_MSK);

    return 0;
}
```

### Power Management

**Example from ADXL345 PM support**:

```c
#ifdef CONFIG_PM_DEVICE
static int adxl345_pm_action(const struct device *dev,
                             enum pm_device_action action)
{
    struct adxl345_dev_data *data = dev->data;
    int ret;

    switch (action) {
    case PM_DEVICE_ACTION_RESUME:
        // Resume to measurement mode
        ret = adxl345_set_op_mode(dev, ADXL345_MEASURE);
        if (ret == 0) {
            data->op_mode = ADXL345_MEASURE;
        }
        return ret;

    case PM_DEVICE_ACTION_SUSPEND:
        // Enter standby mode for low power
        ret = adxl345_set_op_mode(dev, ADXL345_STANDBY);
        if (ret == 0) {
            data->op_mode = ADXL345_STANDBY;
        }
        return ret;

    default:
        return -ENOTSUP;
    }
}

PM_DEVICE_DT_INST_DEFINE(0, adxl345_pm_action);
#endif
```

