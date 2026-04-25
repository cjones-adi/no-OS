# GPIO Troubleshooting

Common GPIO issues and their solutions.

## GPIO Always Reads Same Value

### Problem
Input GPIO always reads HIGH (or always reads LOW), regardless of external signal.

### Possible Causes

**1. Direction not configured as input**

Check:
```c
uint8_t dir;
no_os_gpio_get_direction(gpio, &dir);
printf("Direction: %s\n", dir == NO_OS_GPIO_IN ? "INPUT" : "OUTPUT");
```

Solution:
```c
no_os_gpio_direction_input(gpio);
```

**2. Floating input (no pull resistor)**

Symptom: Reading oscillates or reads random values.

Check configuration:
```c
// Current config
struct no_os_gpio_init_param init = {
    .pull = NO_OS_PULL_NONE,  // Floating!
};
```

Solution:
```c
// Add pull resistor
struct no_os_gpio_init_param init = {
    .pull = NO_OS_PULL_UP,  // Or NO_OS_PULL_DOWN
};
```

**3. Wrong wiring**

Check:
- Verify connections with multimeter
- Measure voltage at pin (should change with signal)
- Check for reversed polarity
- Verify ground connection

**4. Pin mux conflict (pin assigned to different peripheral)**

Symptom: GPIO reads work in bare-metal but not when other peripherals enabled.

Check platform configuration:
```c
// STM32 example - ensure GPIO mode selected
HAL_GPIO_DeInit(GPIOx, GPIO_PIN_x);  // Clear alternate function
HAL_GPIO_Init(GPIOx, &GPIO_InitStruct);  // Reconfigure as GPIO
```

Solution: Review pin assignment, ensure pin not used by UART/SPI/I2C/etc.

## Output Doesn't Change

### Problem
Setting GPIO output value has no effect on pin voltage.

### Possible Causes

**1. Direction not configured as output**

Check:
```c
uint8_t dir;
no_os_gpio_get_direction(gpio, &dir);
if (dir != NO_OS_GPIO_OUT) {
    printf("ERROR: Pin is input, not output\n");
}
```

Solution:
```c
no_os_gpio_direction_output(gpio, NO_OS_GPIO_LOW);
```

**2. Insufficient drive strength**

Symptom: Output voltage correct with no load, but drops under load.

Check with oscilloscope:
- Slow rise/fall times
- Voltage sag under load
- Distorted waveform

Solution (platform-specific):
```c
// Maxim example - increase drive strength
struct maxim_gpio_init_param max_extra = {
    .strength = MXC_GPIO_DRVSTR_3,  // Maximum drive strength
};

struct no_os_gpio_init_param init = {
    .extra = &max_extra,
};
```

**3. Pin mux conflict**

Another peripheral driving the pin.

Check:
```c
// Disable conflicting peripherals
no_os_spi_remove(spi);  // If SPI using same pin
// Then reconfigure as GPIO
```

**4. External hardware issue**

Check:
- Measure voltage at MCU pin vs external circuit
- Check for short circuit
- Verify load impedance reasonable
- Check for conflicting pull resistors

**5. Open-drain output without pull-up**

Some platforms configure outputs as open-drain by default.

Solution:
```c
// Add pull-up resistor in hardware
// OR configure as push-pull in platform extras
```

## Inconsistent Readings

### Problem
Input GPIO reading fluctuates, gives different values on repeated reads.

### Possible Causes

**1. Floating input**

Solution:
```c
struct no_os_gpio_init_param init = {
    .pull = NO_OS_PULL_UP,  // Or NO_OS_PULL_DOWN
};
```

**2. Mechanical button bounce**

Symptom: Single button press detected as multiple presses.

Solution - Software debouncing:
```c
bool button_debounced(struct no_os_gpio_desc *button) {
    uint8_t state1, state2;
    
    no_os_gpio_get_value(button, &state1);
    no_os_mdelay(10);  // Wait 10ms
    no_os_gpio_get_value(button, &state2);
    
    return (state1 == state2) && (state1 == NO_OS_GPIO_LOW);
}
```

**3. Electrical noise on long wires**

Check:
- Shield signal wires
- Reduce wire length
- Add external RC filter (resistor + capacitor)

Solution:
```c
// Hardware: Add 100nF capacitor to ground near MCU pin
// Software: Average multiple readings
uint8_t avg_reading(struct no_os_gpio_desc *gpio) {
    int count = 0;
    for (int i = 0; i < 10; i++) {
        uint8_t val;
        no_os_gpio_get_value(gpio, &val);
        count += val;
        no_os_udelay(100);
    }
    return (count > 5) ? NO_OS_GPIO_HIGH : NO_OS_GPIO_LOW;
}
```

**4. Platform requires delay between reads**

Some platforms need time for input buffer to settle.

Solution:
```c
no_os_gpio_get_value(gpio, &val1);
no_os_udelay(10);  // 10us delay
no_os_gpio_get_value(gpio, &val2);
```

## High Power Consumption

### Problem
System power consumption higher than expected when using GPIO.

### Possible Causes

**1. Floating inputs**

Symptom: Inputs without pull resistors oscillate, causing input buffers to switch continuously.

Check:
```c
// All inputs should have pull resistors
struct no_os_gpio_init_param init = {
    .pull = NO_OS_PULL_NONE,  // Bad for power
};
```

Solution:
```c
struct no_os_gpio_init_param init = {
    .pull = NO_OS_PULL_DOWN,  // Prevents oscillation
};
```

**2. Output driving unnecessary load**

Check:
- Remove unnecessary external pull resistors
- Use high-Z when not driving bus

Solution:
```c
// When not driving
no_os_gpio_set_value(gpio, NO_OS_GPIO_HIGH_Z);
```

**3. Unnecessary toggling**

Check:
```c
// Bad - constant toggling
while (1) {
    no_os_gpio_set_value(led, NO_OS_GPIO_HIGH);
    no_os_mdelay(1);
    no_os_gpio_set_value(led, NO_OS_GPIO_LOW);
    no_os_mdelay(1);
}
```

Solution:
```c
// Only change when needed
if (status_changed) {
    no_os_gpio_set_value(led, new_state);
}
```

**4. Excessive drive strength**

Higher drive strength = more power.

Solution:
```c
// Use minimum drive strength needed
struct maxim_gpio_init_param max_extra = {
    .strength = MXC_GPIO_DRVSTR_0,  // Minimum drive
};
```

**5. Current loop through GPIOs**

Check for accidental current paths:
- Two outputs driving against each other
- Output connected to supply or ground

**6. Unused GPIOs not configured**

Solution:
```c
// Configure all unused GPIOs as inputs with pull-down
// Or disable unused GPIO peripheral clocks
```

## Platform Porting Issues

### Missing platform_ops Functions

**Error:**
```
undefined reference to `gpio_ops_get'
```

Solution:
```c
// Implement all required functions in platform ops
const struct no_os_gpio_platform_ops myplatform_gpio_ops = {
    .gpio_ops_get = &myplatform_gpio_get,
    .gpio_ops_get_optional = &myplatform_gpio_get_optional,
    .gpio_ops_remove = &myplatform_gpio_remove,
    .gpio_ops_direction_input = &myplatform_gpio_direction_input,
    .gpio_ops_direction_output = &myplatform_gpio_direction_output,
    .gpio_ops_get_direction = &myplatform_gpio_get_direction,
    .gpio_ops_set_value = &myplatform_gpio_set_value,
    .gpio_ops_get_value = &myplatform_gpio_get_value,
};
```

### Vendor HAL Errors

**Symptom:** Platform GPIO functions return errors.

Debug:
```c
int32_t myplatform_gpio_get(struct no_os_gpio_desc **desc,
                            const struct no_os_gpio_init_param *param)
{
    // Enable debug output from vendor HAL
    HAL_StatusTypeDef hal_ret = HAL_GPIO_Init(...);
    
    printf("HAL_GPIO_Init returned: %d\n", hal_ret);
    
    if (hal_ret != HAL_OK)
        return -EIO;
    
    return 0;
}
```

Common HAL issues:
- GPIO peripheral clock not enabled
- Invalid port/pin number
- Pin already configured by other peripheral

### Pin Numbering Mismatch

**Symptom:** Configuring GPIO pin affects wrong physical pin.

Check platform numbering scheme:
```c
// Platform A: Port=0, Pin=5 → Physical PA5
// Platform B: Port=0, Pin=5 → Physical GPIO5
// Platform C: Port=0, Pin=5 → Physical P0.5
```

Solution: Review platform datasheet and HAL documentation for correct numbering.

### GPIO Peripheral Clock Not Enabled

**Symptom (common on STM32):** GPIO functions do nothing or hard fault.

Solution:
```c
int32_t stm32_gpio_get(struct no_os_gpio_desc **desc,
                       const struct no_os_gpio_init_param *param)
{
    // Enable GPIO peripheral clock
    switch (param->port) {
    case 0:  // GPIOA
        __HAL_RCC_GPIOA_CLK_ENABLE();
        break;
    case 1:  // GPIOB
        __HAL_RCC_GPIOB_CLK_ENABLE();
        break;
    // ... other ports
    }
    
    // Now safe to configure GPIO
    HAL_GPIO_Init(...);
    
    return 0;
}
```

## Debugging Techniques

### 1. Verify Direction

```c
uint8_t dir;
no_os_gpio_get_direction(gpio, &dir);
printf("GPIO direction: %s\n", dir == NO_OS_GPIO_IN ? "INPUT" : "OUTPUT");
```

### 2. Read Back Output Value

```c
no_os_gpio_set_value(gpio, NO_OS_GPIO_HIGH);

uint8_t readback;
no_os_gpio_get_value(gpio, &readback);
printf("Set HIGH, read back: %d\n", readback);
```

### 3. Toggle with Delay

```c
// Verify output working with oscilloscope/LED
while (1) {
    no_os_gpio_set_value(gpio, NO_OS_GPIO_HIGH);
    no_os_mdelay(500);
    no_os_gpio_set_value(gpio, NO_OS_GPIO_LOW);
    no_os_mdelay(500);
}
```

### 4. Check Platform-Specific Registers

```c
// Example: Maxim platform
printf("GPIO port %d pin %d registers:\n", port, pin);
printf("  EN0:  0x%08X\n", MXC_GPIO_GET_EN(port));
printf("  OUT:  0x%08X\n", MXC_GPIO_GET_OUT(port));
printf("  IN:   0x%08X\n", MXC_GPIO_GET_IN(port));
printf("  OUTEN: 0x%08X\n", MXC_GPIO_GET_OUTEN(port));
```

### 5. Isolate Issue

Test GPIO in isolation:
```c
// Minimal test program
int main(void) {
    struct no_os_gpio_desc *gpio;
    struct no_os_gpio_init_param init = {
        .port = 0,
        .number = 5,
        .platform_ops = &platform_gpio_ops,
    };
    
    no_os_gpio_get(&gpio, &init);
    no_os_gpio_direction_output(gpio, NO_OS_GPIO_HIGH);
    
    // Measure pin voltage - should be VDD
    
    return 0;
}
```

### 6. Use Multimeter

Measure:
- Pin voltage (should match set value)
- Current draw (detect shorts)
- Resistance to ground/VDD (detect conflicts)

### 7. Check Schematic

Verify:
- Correct pin assignment
- Pull resistor values
- External connections
- Voltage levels compatible

## Common Error Messages

**"GPIO already in use"**
- Pin configured by another GPIO descriptor
- Solution: Call `no_os_gpio_remove()` before reinitializing

**"Invalid GPIO port/pin"**
- Port or pin number out of range for platform
- Solution: Check platform datasheet for valid GPIO numbers

**"GPIO init failed with -EINVAL"**
- Invalid parameter passed to `no_os_gpio_get()`
- Solution: Check all init_param fields are valid

**"GPIO init failed with -ENODEV"**
- GPIO peripheral not available on platform
- Solution: Verify GPIO peripheral supported and enabled

**"GPIO init failed with -EIO"**
- Hardware error during initialization
- Solution: Check vendor HAL error codes, verify peripheral clock enabled
