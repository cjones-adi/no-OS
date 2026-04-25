## Debugging Tips

### 1. Check PWM Output with Oscilloscope

Verify:
- Period matches expected value
- Pulse width matches expected duty cycle
- Signal polarity is correct
- No glitches during configuration changes

### 2. Enable PWM Logging

```c
#define PWM_LOG_LEVEL LOG_LEVEL_DBG
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(pwm_app);

LOG_DBG("PWM period: %u ns, pulse: %u ns", period, pulse);
```

### 3. Validate Calculations

```c
void pwm_debug_info(const struct pwm_dt_spec *pwm, uint32_t pulse)
{
    uint8_t duty = (pulse * 100) / pwm->period;
    uint32_t freq = 1000000000UL / pwm->period;

    printk("PWM Info:\n");
    printk("  Frequency: %u Hz\n", freq);
    printk("  Period: %u ns\n", pwm->period);
    printk("  Pulse: %u ns\n", pulse);
    printk("  Duty: %u%%\n", duty);
}
```

### 4. Check Clock Configuration

```c
uint64_t cycles_per_sec;
const struct device *pwm = DEVICE_DT_GET(DT_NODELABEL(pwm0));

pwm_get_cycles_per_sec(pwm, 0, &cycles_per_sec);
printk("PWM clock: %llu Hz\n", cycles_per_sec);
```

### 5. Common Issues and Solutions

**PWM not outputting**:
- Check device_is_ready()
- Verify pin mux configuration
- Ensure pulse > 0 (0 = disabled)
- Check polarity flags

**Wrong frequency/duty cycle**:
- Verify clock_frequency in devicetree
- Check period calculation
- Validate pulse width
- Confirm prescaler configuration

**Glitches during updates**:
- Some hardware doesn't support glitch-free updates
- Update during period boundary if supported
- Disable channel before major changes

