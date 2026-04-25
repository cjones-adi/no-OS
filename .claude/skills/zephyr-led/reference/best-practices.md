## Common Patterns and Best Practices

### 1. Status Indicator Pattern

```c
void set_status_led(enum status_code code)
{
    const struct device *led = DEVICE_DT_GET(DT_NODELABEL(status_led));

    switch (code) {
    case STATUS_OK:
        led_on(led, 0);          /* Solid on = OK */
        break;
    case STATUS_WARNING:
        led_blink(led, 0, 500, 500); /* Slow blink = warning */
        break;
    case STATUS_ERROR:
        led_blink(led, 0, 100, 100); /* Fast blink = error */
        break;
    case STATUS_OFF:
        led_off(led, 0);         /* Off = disabled */
        break;
    }
}
```

### 2. Brightness Fading

```c
void led_fade_in(const struct device *led, uint32_t led_num, uint32_t duration_ms)
{
    for (uint8_t brightness = 0; brightness <= 100; brightness++) {
        led_set_brightness(led, led_num, brightness);
        k_msleep(duration_ms / 100);
    }
}

void led_fade_out(const struct device *led, uint32_t led_num, uint32_t duration_ms)
{
    for (uint8_t brightness = 100; brightness > 0; brightness--) {
        led_set_brightness(led, led_num, brightness);
        k_msleep(duration_ms / 100);
    }
}
```

### 3. RGB Color Cycling

```c
void rgb_cycle(const struct device *led, uint32_t led_num)
{
    uint8_t color[3];

    /* Red */
    color[0] = 100; color[1] = 0;   color[2] = 0;
    led_set_color(led, led_num, 3, color);
    k_msleep(1000);

    /* Green */
    color[0] = 0;   color[1] = 100; color[2] = 0;
    led_set_color(led, led_num, 3, color);
    k_msleep(1000);

    /* Blue */
    color[0] = 0;   color[1] = 0;   color[2] = 100;
    led_set_color(led, led_num, 3, color);
    k_msleep(1000);
}
```

### 4. LED Pattern Sequencer

```c
struct led_pattern {
    uint8_t brightness;
    uint16_t duration_ms;
};

void led_run_pattern(const struct device *led,
                     uint32_t led_num,
                     const struct led_pattern *pattern,
                     size_t pattern_len)
{
    for (size_t i = 0; i < pattern_len; i++) {
        led_set_brightness(led, led_num, pattern[i].brightness);
        k_msleep(pattern[i].duration_ms);
    }
}

/* Example: SOS pattern */
static const struct led_pattern sos_pattern[] = {
    {100, 200}, {0, 200}, /* S (short) */
    {100, 200}, {0, 200},
    {100, 200}, {0, 400},
    {100, 600}, {0, 200}, /* O (long) */
    {100, 600}, {0, 200},
    {100, 600}, {0, 400},
    {100, 200}, {0, 200}, /* S (short) */
    {100, 200}, {0, 200},
    {100, 200}, {0, 1000},
};
```

### 5. Multi-LED Control

```c
void leds_all_on(const struct device *led, uint8_t num_leds)
{
    for (uint8_t i = 0; i < num_leds; i++) {
        led_on(led, i);
    }
}

void leds_all_off(const struct device *led, uint8_t num_leds)
{
    for (uint8_t i = 0; i < num_leds; i++) {
        led_off(led, i);
    }
}

void leds_set_bar(const struct device *led, uint8_t num_leds, uint8_t level)
{
    for (uint8_t i = 0; i < num_leds; i++) {
        if (i < level) {
            led_on(led, i);
        } else {
            led_off(led, i);
        }
    }
}
```

