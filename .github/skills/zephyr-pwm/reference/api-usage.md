## Consumer API Usage

Applications use PWM outputs via the consumer API.

### Set PWM Period and Pulse Width

**Using nanoseconds**:

```c
#include <zephyr/drivers/pwm.h>

/* Get PWM spec from devicetree */
static const struct pwm_dt_spec my_pwm = PWM_DT_SPEC_GET(DT_NODELABEL(led0));

/* Set50% duty cycle */
int ret = pwm_set_dt(&my_pwm, my_pwm.period, my_pwm.period / 2);
```

**Set pulse width only** (keep period):

```c
uint32_t pulse_ns = 500000;  /* 500us */
int ret = pwm_set_pulse_dt(&my_pwm, pulse_ns);
```

**Disable PWM output**:

```c
int ret = pwm_set_pulse_dt(&my_pwm, 0);  /* 0% duty cycle */
```

### Set Duty Cycle by Percentage

```c
int pwm_set_duty_cycle_percent(const struct pwm_dt_spec *spec, uint8_t percent)
{
    if (percent > 100) {
        return -EINVAL;
    }

    uint32_t pulse = (spec->period * percent) / 100;
    return pwm_set_pulse_dt(spec, pulse);
}
```

### Motor Control Example

```c
#define MOTOR_PWM_PERIOD_NS  20000000  /* 20ms (50Hz) */

void motor_set_speed(uint8_t speed_percent)
{
    static const struct pwm_dt_spec motor_pwm =
        PWM_DT_SPEC_GET(DT_NODELABEL(motor));

    /* Convert 0-100% to pulse width */
    uint32_t pulse = (MOTOR_PWM_PERIOD_NS * speed_percent) / 100;

    pwm_set_pulse_dt(&motor_pwm, pulse);
}
```

### Servo Control Example

```c
#define SERVO_MIN_PULSE_NS   1000000  /* 1ms */
#define SERVO_MAX_PULSE_NS   2000000  /* 2ms */
#define SERVO_PERIOD_NS      20000000 /* 20ms */

void servo_set_angle(int16_t angle)
{
    static const struct pwm_dt_spec servo =
        PWM_DT_SPEC_GET(DT_NODELABEL(servo1));

    /* Clamp angle to -90 to +90 degrees */
    if (angle < -90) angle = -90;
    if (angle > 90) angle = 90;

    /* Convert angle to pulse width */
    uint32_t pulse = SERVO_MIN_PULSE_NS +
                     ((angle + 90) * (SERVO_MAX_PULSE_NS - SERVO_MIN_PULSE_NS)) / 180;

    pwm_set_pulse_dt(&servo, pulse);
}
```

## Advanced Features

### 1. PWM Capture

Measure incoming PWM signals:

```c
#include <zephyr/drivers/pwm.h>

static void pwm_capture_callback(const struct device *dev,
                                 uint32_t channel,
                                 uint32_t period_cycles,
                                 uint32_t pulse_cycles,
                                 int status,
                                 void *user_data)
{
    if (status < 0) {
        printk("Capture error: %d\n", status);
        return;
    }

    /* Convert cycles to nanoseconds */
    uint64_t cycles_per_sec;
    pwm_get_cycles_per_sec(dev, channel, &cycles_per_sec);

    uint32_t period_ns = (period_cycles * 1000000000ULL) / cycles_per_sec;
    uint32_t pulse_ns = (pulse_cycles * 1000000000ULL) / cycles_per_sec;

    printk("Period: %u ns, Pulse: %u ns\n", period_ns, pulse_ns);
}

void setup_pwm_capture(void)
{
    const struct device *pwm = DEVICE_DT_GET(DT_NODELABEL(pwm_input));
    uint32_t channel = 0;

    /* Configure capture */
    pwm_configure_capture(pwm, channel,
                          PWM_CAPTURE_TYPE_BOTH | PWM_CAPTURE_MODE_CONTINUOUS,
                          pwm_capture_callback, NULL);

    /* Enable capture */
    pwm_enable_capture(pwm, channel);
}
```

### 2. Cycle-Based API

For precise timing control:

```c
uint64_t cycles_per_sec;
uint32_t period_cycles = 48000;   /* 1ms at 48MHz */
uint32_t pulse_cycles = 24000;    /* 500us (50% duty) */

const struct device *pwm = DEVICE_DT_GET(DT_NODELABEL(pwm0));

/* Get clock frequency */
pwm_get_cycles_per_sec(pwm, 0, &cycles_per_sec);

/* Set using cycles */
pwm_set_cycles(pwm, 0, period_cycles, pulse_cycles, PWM_POLARITY_NORMAL);
```

### 3. PWM Events and Callbacks

Handle PWM period events:

```c
#ifdef CONFIG_PWM_EVENT

static void pwm_period_callback(const struct device *dev,
                                uint32_t channel,
                                void *user_data)
{
    /* Called every PWM period */
    printk("PWM period event on channel %u\n", channel);
}

void setup_pwm_events(void)
{
    const struct device *pwm = DEVICE_DT_GET(DT_NODELABEL(pwm0));

    struct pwm_event_callback cb = {
        .handler = pwm_period_callback,
        .user_data = NULL,
        .event_types = PWM_EVENT_TYPE_PERIOD,
    };

    pwm_set_event_callback(pwm, &cb);
}

#endif
```

