## Consumer API Usage

### Turn LED On/Off

```c
#include <zephyr/drivers/led.h>

const struct device *led_dev = DEVICE_DT_GET(DT_NODELABEL(led_ctrl));

/* Turn LED on */
led_on(led_dev, 0);  /* LED index 0 */

/* Turn LED off */
led_off(led_dev, 0);
```

### Set LED Brightness

```c
/* Set to 50% brightness */
led_set_brightness(led_dev, 0, 50);

/* Set to full brightness */
led_set_brightness(led_dev, 0, 100);

/* Turn off via brightness */
led_set_brightness(led_dev, 0, 0);
```

### Configure LED Blinking

```c
/* Blink: 500ms on, 500ms off */
led_blink(led_dev, 0, 500, 500);

/* Fast blink: 100ms on, 100ms off */
led_blink(led_dev, 0, 100, 100);

/* Slow blink: 1s on, 1s off */
led_blink(led_dev, 0, 1000, 1000);
```

### Set RGB Color

```c
/* Set RGB LED to red (100% red, 0% green, 0% blue) */
uint8_t red[3] = {100, 0, 0};
led_set_color(led_dev, 0, 3, red);

/* Set to purple (100% red, 0% green, 100% blue) */
uint8_t purple[3] = {100, 0, 100};
led_set_color(led_dev, 0, 3, purple);

/* Set to white at 50% brightness */
uint8_t white[3] = {50, 50, 50};
led_set_color(led_dev, 0, 3, white);
```

### Get LED Information

```c
const struct led_info *info;

led_get_info(led_dev, 0, &info);
printk("LED: %s, Channels: %u\n", info->label, info->num_colors);
```

