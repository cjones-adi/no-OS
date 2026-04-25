## Debugging Tips

### 1. Verify Device Ready

```c
const struct device *led = DEVICE_DT_GET(DT_NODELABEL(led_ctrl));

if (!device_is_ready(led)) {
    printk("ERROR: LED device not ready\n");
    return -ENODEV;
}
```

### 2. Test Each LED Individually

```c
void test_all_leds(const struct device *led, uint8_t num_leds)
{
    printk("Testing %u LEDs...\n", num_leds);

    for (uint8_t i = 0; i < num_leds; i++) {
        printk("  LED %u ON\n", i);
        led_on(led, i);
        k_msleep(500);

        printk("  LED %u OFF\n", i);
        led_off(led, i);
        k_msleep(200);
    }
}
```

### 3. Check I2C/SPI Communication

```c
/* For I2C LED controllers */
const struct led_chip_config *cfg = dev->config;

uint8_t test_val;
int ret = i2c_reg_read_byte_dt(&cfg->i2c, LED_CTRL_REG, &test_val);
if (ret < 0) {
    printk("I2C read failed: %d\n", ret);
}
```

### 4. Enable Logging

```c
#define LED_LOG_LEVEL LOG_LEVEL_DBG
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(led_driver);

LOG_DBG("Setting LED %u brightness to %u%%", led, brightness);
```

### 5. Common Issues and Solutions

**LED not turning on**:
- Check device_is_ready()
- Verify I2C/SPI bus configuration
- Check GPIO pin configuration
- Verify power supply to LED
- Check current limiting resistors

**Wrong brightness**:
- Verify PWM duty cycle calculation
- Check gamma correction (if needed)
- Validate brightness scaling (0-100 to 0-255)

**RGB color incorrect**:
- Verify color_mapping array
- Check color channel order (RGB vs GRB vs BGR)
- Validate multi-color LED wiring

