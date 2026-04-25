## Driver Implementation Pattern

### Step 1: Define Register Map (for I2C/SPI chips)

```c
/* LED controller registers */
#define LED_CTRL_REG       0x00  /* Control register */
#define LED_PWM_BASE       0x10  /* PWM duty cycle base */
#define LED_CURRENT_BASE   0x20  /* Current control base */
#define LED_BLINK_REG      0x30  /* Blink configuration */

/* Control bits */
#define LED_EN             BIT(0)  /* Enable LED */
#define LED_BLINK_EN       BIT(1)  /* Enable blinking */
```

### Step 2: Define Config and Data Structures

**Config structure** (ROM, from devicetree):

```c
struct led_chip_config {
    struct i2c_dt_spec i2c;       /* I2C bus */
    uint8_t num_leds;             /* Number of LEDs */
    const struct led_info *led_info; /* LED information array */
};
```

**Data structure** (RAM, runtime state):

```c
struct led_chip_data {
    uint8_t brightness[MAX_LEDS];  /* Current brightness (0-100) */
    uint8_t state[MAX_LEDS];       /* LED on/off state */
    struct k_mutex lock;           /* Thread-safe access */
};
```

### Step 3: Implement on/off Functions

**LED on**:

```c
static int led_chip_on(const struct device *dev, uint32_t led)
{
    const struct led_chip_config *cfg = dev->config;
    struct led_chip_data *data = dev->data;
    int ret;

    if (led >= cfg->num_leds) {
        return -EINVAL;
    }

    k_mutex_lock(&data->lock, K_FOREVER);

    /* Set full brightness */
    uint8_t pwm_val = 255;  /* Full duty cycle */
    ret = i2c_reg_write_byte_dt(&cfg->i2c, LED_PWM_BASE + led, pwm_val);
    if (ret == 0) {
        data->state[led] = 1;
        data->brightness[led] = 100;
    }

    k_mutex_unlock(&data->lock);

    return ret;
}
```

**LED off**:

```c
static int led_chip_off(const struct device *dev, uint32_t led)
{
    const struct led_chip_config *cfg = dev->config;
    struct led_chip_data *data = dev->data;
    int ret;

    if (led >= cfg->num_leds) {
        return -EINVAL;
    }

    k_mutex_lock(&data->lock, K_FOREVER);

    /* Set zero brightness */
    ret = i2c_reg_write_byte_dt(&cfg->i2c, LED_PWM_BASE + led, 0);
    if (ret == 0) {
        data->state[led] = 0;
        data->brightness[led] = 0;
    }

    k_mutex_unlock(&data->lock);

    return ret;
}
```

### Step 4: Implement set_brightness Function

```c
static int led_chip_set_brightness(const struct device *dev,
                                    uint32_t led,
                                    uint8_t value)
{
    const struct led_chip_config *cfg = dev->config;
    struct led_chip_data *data = dev->data;
    int ret;

    if (led >= cfg->num_leds) {
        return -EINVAL;
    }

    /* Clamp to 0-100 */
    if (value > LED_BRIGHTNESS_MAX) {
        value = LED_BRIGHTNESS_MAX;
    }

    k_mutex_lock(&data->lock, K_FOREVER);

    /* Convert 0-100 to 0-255 PWM value */
    uint8_t pwm_val = (value * 255) / 100;

    ret = i2c_reg_write_byte_dt(&cfg->i2c, LED_PWM_BASE + led, pwm_val);
    if (ret == 0) {
        data->brightness[led] = value;
        data->state[led] = (value > 0) ? 1 : 0;
    }

    k_mutex_unlock(&data->lock);

    return ret;
}
```

### Step 5: Implement Blinking (Optional)

```c
static int led_chip_blink(const struct device *dev,
                          uint32_t led,
                          uint32_t delay_on,
                          uint32_t delay_off)
{
    const struct led_chip_config *cfg = dev->config;
    int ret;

    if (led >= cfg->num_leds) {
        return -EINVAL;
    }

    /* Convert ms to hardware-specific units */
    uint8_t on_time = delay_on / 100;   /* 100ms units */
    uint8_t off_time = delay_off / 100;

    /* Configure blink timing */
    uint8_t blink_cfg[2] = {on_time, off_time};
    ret = i2c_burst_write_dt(&cfg->i2c, LED_BLINK_REG + (led * 2),
                             blink_cfg, sizeof(blink_cfg));
    if (ret < 0) {
        return ret;
    }

    /* Enable blinking */
    return i2c_reg_update_byte_dt(&cfg->i2c, LED_CTRL_REG,
                                  LED_BLINK_EN, LED_BLINK_EN);
}
```

### Step 6: Implement RGB Color Control (Optional)

```c
static int led_chip_set_color(const struct device *dev,
                               uint32_t led,
                               uint8_t num_colors,
                               const uint8_t *color)
{
    const struct led_chip_config *cfg = dev->config;
    const struct led_info *info;
    int ret;

    if (led >= cfg->num_leds) {
        return -EINVAL;
    }

    /* Get LED info for color mapping */
    info = &cfg->led_info[led];
    if (num_colors != info->num_colors) {
        return -EINVAL;
    }

    /* Write each color channel */
    for (uint8_t i = 0; i < num_colors; i++) {
        uint8_t channel = info->color_mapping[i];
        uint8_t pwm_val = (color[i] * 255) / 100;

        ret = i2c_reg_write_byte_dt(&cfg->i2c,
                                    LED_PWM_BASE + channel,
                                    pwm_val);
        if (ret < 0) {
            return ret;
        }
    }

    return 0;
}
```

### Step 7: Implement get_info (Optional)

```c
static int led_chip_get_info(const struct device *dev,
                              uint32_t led,
                              const struct led_info **info)
{
    const struct led_chip_config *cfg = dev->config;

    if (led >= cfg->num_leds) {
        return -EINVAL;
    }

    *info = &cfg->led_info[led];

    return 0;
}
```

### Step 8: Define API Structure

```c
static const struct led_driver_api led_chip_driver_api = {
    .on = led_chip_on,
    .off = led_chip_off,
    .set_brightness = led_chip_set_brightness,
    .blink = led_chip_blink,
    .get_info = led_chip_get_info,
    .set_color = led_chip_set_color,
};
```

### Step 9: Implement Init Function

```c
static int led_chip_init(const struct device *dev)
{
    const struct led_chip_config *cfg = dev->config;
    struct led_chip_data *data = dev->data;
    int ret;

    /* Check I2C bus ready */
    if (!device_is_ready(cfg->i2c.bus)) {
        return -ENODEV;
    }

    /* Initialize mutex */
    k_mutex_init(&data->lock);

    /* Reset LED controller */
    ret = i2c_reg_write_byte_dt(&cfg->i2c, LED_CTRL_REG, 0);
    if (ret < 0) {
        return ret;
    }

    /* Turn off all LEDs */
    for (uint8_t i = 0; i < cfg->num_leds; i++) {
        ret = i2c_reg_write_byte_dt(&cfg->i2c, LED_PWM_BASE + i, 0);
        if (ret < 0) {
            return ret;
        }
        data->brightness[i] = 0;
        data->state[i] = 0;
    }

    /* Enable controller */
    return i2c_reg_write_byte_dt(&cfg->i2c, LED_CTRL_REG, LED_EN);
}
```

### Step 10: Device Instantiation Macro

**For I2C LED controller**:

```c
#define LED_CHIP_DEFINE(inst)                                           \
    static struct led_chip_data led_chip_data_##inst;                   \
                                                                        \
    /* LED info array */                                                \
    static const struct led_info led_chip_info_##inst[] = {             \
        {.label = "LED0", .index = 0, .num_colors = 1},                 \
        {.label = "LED1", .index = 1, .num_colors = 1},                 \
    };                                                                  \
                                                                        \
    static const struct led_chip_config led_chip_config_##inst = {      \
        .i2c = I2C_DT_SPEC_INST_GET(inst),                              \
        .num_leds = ARRAY_SIZE(led_chip_info_##inst),                  \
        .led_info = led_chip_info_##inst,                               \
    };                                                                  \
                                                                        \
    DEVICE_DT_INST_DEFINE(inst,                                         \
                          led_chip_init,                                \
                          NULL,                                         \
                          &led_chip_data_##inst,                        \
                          &led_chip_config_##inst,                      \
                          POST_KERNEL,                                  \
                          CONFIG_LED_INIT_PRIORITY,                     \
                          &led_chip_driver_api);

DT_INST_FOREACH_STATUS_OKAY(LED_CHIP_DEFINE)
```

**For GPIO-based LED**:

```c
struct led_gpio_config {
    struct gpio_dt_spec gpio;
};

static int led_gpio_on(const struct device *dev, uint32_t led)
{
    const struct led_gpio_config *cfg = dev->config;
    return gpio_pin_set_dt(&cfg->gpio, 1);
}

static int led_gpio_off(const struct device *dev, uint32_t led)
{
    const struct led_gpio_config *cfg = dev->config;
    return gpio_pin_set_dt(&cfg->gpio, 0);
}

static int led_gpio_init(const struct device *dev)
{
    const struct led_gpio_config *cfg = dev->config;

    if (!device_is_ready(cfg->gpio.port)) {
        return -ENODEV;
    }

    return gpio_pin_configure_dt(&cfg->gpio, GPIO_OUTPUT_INACTIVE);
}

#define LED_GPIO_DEFINE(inst)                                           \
    static const struct led_gpio_config led_gpio_config_##inst = {      \
        .gpio = GPIO_DT_SPEC_INST_GET(inst, gpios),                     \
    };                                                                  \
                                                                        \
    DEVICE_DT_INST_DEFINE(inst, led_gpio_init, NULL, NULL,             \
                          &led_gpio_config_##inst, POST_KERNEL,         \
                          CONFIG_LED_INIT_PRIORITY,                     \
                          &led_gpio_driver_api);
```

## Devicetree Binding Pattern

### Simple LED Binding

**File**: `dts/bindings/led/<vendor>,<chip>-led.yaml`

```yaml
# Copyright (C) 2024 Vendor Corporation
# SPDX-License-Identifier: Apache-2.0

description: CHIP LED controller

compatible: "vendor,chip-led"

include: i2c-device.yaml

properties:
  num-leds:
    type: int
    required: true
    description: Number of LEDs controlled
```

### RGB LED Binding

```yaml
description: RGB LED controller

compatible: "vendor,rgb-led"

include: i2c-device.yaml

properties:
  num-leds:
    type: int
    required: true
    description: Number of RGB LEDs

child-binding:
  description: Individual LED configuration

  properties:
    label:
      type: string
      description: LED label

    color-mapping:
      type: array
      description: |
        Mapping of color channels to hardware channels.
        For RGB LED: [red_channel, green_channel, blue_channel]
```

### GPIO LED Binding

```yaml
description: GPIO-controlled LED

compatible: "gpio-leds"

child-binding:
  description: GPIO LED configuration

  properties:
    gpios:
      type: phandle-array
      required: true
      description: GPIO pin for LED control

    label:
      type: string
      description: LED label
```

### Devicetree Usage

**I2C LED controller**:

```dts
&i2c0 {
    led_ctrl: led-controller@60 {
        compatible = "vendor,chip-led";
        reg = <0x60>;
        num-leds = <8>;
    };
};
```

**GPIO LEDs**:

```dts
leds {
    compatible = "gpio-leds";

    led0: led_0 {
        gpios = <&gpio0 13 GPIO_ACTIVE_HIGH>;
        label = "Status LED";
    };

    led1: led_1 {
        gpios = <&gpio0 14 GPIO_ACTIVE_HIGH>;
        label = "Error LED";
    };
};
```

**RGB LED**:

```dts
&i2c1 {
    rgb_ctrl: rgb-led@40 {
        compatible = "vendor,rgb-led";
        reg = <0x40>;
        num-leds = <4>;

        rgb0: rgb_0 {
            label = "RGB LED 0";
            color-mapping = <0 1 2>; /* R=ch0, G=ch1, B=ch2 */
        };
    };
};
```

