# GPIO Best Practices

Guidelines and recommendations for using GPIO effectively in no-OS drivers.

## General Best Practices

### 1. Always Configure Direction Before Use

**Wrong:**
```c
no_os_gpio_get(&gpio, &init);
no_os_gpio_set_value(gpio, NO_OS_GPIO_HIGH);  // Direction unknown!
```

**Right:**
```c
no_os_gpio_get(&gpio, &init);
no_os_gpio_direction_output(gpio, NO_OS_GPIO_LOW);  // Set direction + initial value
no_os_gpio_set_value(gpio, NO_OS_GPIO_HIGH);
```

**Why:** Undefined behavior if direction not configured. Some platforms default to input, causing output writes to be ignored.

### 2. Set Initial Value When Configuring as Output

**Wrong:**
```c
no_os_gpio_direction_output(reset, NO_OS_GPIO_LOW);  // Initial value
no_os_gpio_set_value(reset, NO_OS_GPIO_LOW);         // Redundant
```

**Right:**
```c
no_os_gpio_direction_output(reset, NO_OS_GPIO_LOW);  // Sets direction AND value
```

**Why:** `no_os_gpio_direction_output()` sets both direction and initial value atomically, preventing glitches.

### 3. Use Pull Resistors for Floating Inputs

**Wrong:**
```c
// Button with no pull resistor
struct no_os_gpio_init_param button_init = {
    .pull = NO_OS_PULL_NONE,  // Pin floats when button not pressed
};
```

**Right:**
```c
// Active-low button with pull-up
struct no_os_gpio_init_param button_init = {
    .pull = NO_OS_PULL_UP,  // Pulled high, grounded when pressed
};
```

**Why:** Floating inputs read random values, cause oscillations, waste power.

### 4. Always Check Optional GPIOs Before Use

**Wrong:**
```c
no_os_gpio_get_optional(&led, &led_init);
no_os_gpio_set_value(led, NO_OS_GPIO_HIGH);  // Crash if led is NULL!
```

**Right:**
```c
no_os_gpio_get_optional(&led, &led_init);
if (led) {
    no_os_gpio_set_value(led, NO_OS_GPIO_HIGH);
}
```

**Why:** Optional GPIOs may not exist on all boards. NULL check prevents crashes.

### 5. Free Resources with no_os_gpio_remove()

**Wrong:**
```c
int driver_init(struct driver_dev **dev) {
    no_os_gpio_get(&(*dev)->gpio, &gpio_init);
    // ... error occurs ...
    return -EIO;  // Leaked GPIO!
}
```

**Right:**
```c
int driver_init(struct driver_dev **dev) {
    ret = no_os_gpio_get(&(*dev)->gpio, &gpio_init);
    if (ret)
        return ret;
    
    // ... error occurs ...
    no_os_gpio_remove((*dev)->gpio);  // Clean up
    return -EIO;
}
```

**Why:** Platform resources (GPIO peripheral, clocks) remain allocated. May prevent reinitialization.

### 6. Avoid Unnecessary Toggling

**Wrong:**
```c
while (1) {
    no_os_gpio_set_value(led, NO_OS_GPIO_HIGH);
    no_os_mdelay(1);
    no_os_gpio_set_value(led, NO_OS_GPIO_LOW);
    no_os_mdelay(1);
}
```

**Better:**
```c
// Only toggle when needed for status indication
if (status_changed) {
    no_os_gpio_set_value(led, status ? NO_OS_GPIO_HIGH : NO_OS_GPIO_LOW);
}
```

**Why:** Unnecessary toggling wastes power, generates EMI, wears out flash if pin controlled by state machine.

### 7. Use Platform-Appropriate Drive Strength

**Wrong:**
```c
// Using default drive strength for high-capacitance load
struct no_os_gpio_init_param init = {
    .platform_ops = &max_gpio_ops,
    // No extra configuration
};
```

**Right:**
```c
struct maxim_gpio_init_param max_extra = {
    .strength = MXC_GPIO_DRVSTR_3,  // High drive strength
};

struct no_os_gpio_init_param init = {
    .platform_ops = &max_gpio_ops,
    .extra = &max_extra,
};
```

**Why:** Low drive strength can't drive capacitive loads fast enough. High drive strength wastes power on light loads.

### 8. Debounce Buttons in Software

**Example:**
```c
bool button_debounced(struct no_os_gpio_desc *button) {
    uint8_t state1, state2;
    
    no_os_gpio_get_value(button, &state1);
    no_os_mdelay(10);  // Wait 10ms
    no_os_gpio_get_value(button, &state2);
    
    return (state1 == state2) && (state1 == NO_OS_GPIO_LOW);
}
```

**Why:** Mechanical switches bounce for 5-20ms. Without debouncing, single press detected as multiple presses.

### 9. Consider Interrupt-Driven Buttons

**Polling (inefficient):**
```c
while (1) {
    no_os_gpio_get_value(button, &state);
    if (state == NO_OS_GPIO_LOW)
        handle_button();
    no_os_mdelay(10);
}
```

**Interrupt-driven (efficient):**
```c
// Setup GPIO interrupt
struct no_os_irq_ctrl_desc *irq_ctrl;
no_os_irq_ctrl_init(&irq_ctrl, &irq_init);
no_os_irq_register_callback(irq_ctrl, GPIO_IRQ, button_handler);

// Handler runs only when button pressed
void button_handler(void *ctx) {
    handle_button();
}
```

**Why:** Polling wastes CPU cycles, increases power. Interrupts allow CPU to sleep until event occurs.

### 10. Document Pin Assignments Clearly

**Example:**
```c
/**
 * @brief MAX20370 GPIO pin assignments
 * 
 * Required GPIOs:
 *   - I2C_SDA: Port 0, Pin 10 (pull-up required)
 *   - I2C_SCL: Port 0, Pin 11 (pull-up required)
 * 
 * Optional GPIOs:
 *   - STAT_LED:  Port 1, Pin 5  (active-high, set to -1 if not present)
 *   - INT_PIN:   Port 0, Pin 15 (active-low interrupt, pull-up)
 * 
 * Platform: Maxim MAX32xxx
 */
struct max20370_init_param {
    struct no_os_i2c_init_param i2c_init;
    struct no_os_gpio_init_param stat_led_init;  // Optional
    struct no_os_gpio_init_param int_init;       // Optional
};
```

**Why:** Clear documentation prevents pin assignment errors, helps board designers, assists debugging.

## Design Patterns

### Pattern: Safe Optional GPIO Handling

```c
struct driver_dev {
    struct no_os_gpio_desc *required_gpio;  // Must exist
    struct no_os_gpio_desc *optional_gpio;  // May be NULL
};

int driver_init(struct driver_dev **dev, struct driver_init_param *init) {
    // Required GPIO - fail if not available
    ret = no_os_gpio_get(&(*dev)->required_gpio, &init->required_init);
    if (ret)
        goto error_dev;
    
    // Optional GPIO - don't fail if unavailable
    ret = no_os_gpio_get_optional(&(*dev)->optional_gpio, &init->optional_init);
    // Continue even if optional GPIO not available
    
    return 0;

error_dev:
    free(*dev);
    return ret;
}

int driver_function(struct driver_dev *dev) {
    // Always use required GPIO
    no_os_gpio_set_value(dev->required_gpio, NO_OS_GPIO_HIGH);
    
    // Check before using optional GPIO
    if (dev->optional_gpio)
        no_os_gpio_set_value(dev->optional_gpio, NO_OS_GPIO_HIGH);
    
    return 0;
}
```

### Pattern: Active-Low Chip Select

```c
/**
 * @brief Assert chip select (select device)
 */
static int spi_select(struct driver_dev *dev) {
    return no_os_gpio_set_value(dev->cs, NO_OS_GPIO_LOW);
}

/**
 * @brief Deassert chip select (deselect device)
 */
static int spi_deselect(struct driver_dev *dev) {
    return no_os_gpio_set_value(dev->cs, NO_OS_GPIO_HIGH);
}

/**
 * @brief SPI transaction with automatic CS control
 */
static int spi_transaction(struct driver_dev *dev, uint8_t *data, size_t len) {
    spi_select(dev);
    
    int ret = no_os_spi_write_and_read(dev->spi, data, len);
    
    spi_deselect(dev);
    
    return ret;
}
```

### Pattern: Reset Sequence

```c
/**
 * @brief Hardware reset sequence
 * 
 * @param dev - Device descriptor
 * @return 0 on success, negative error code on failure
 */
static int device_reset(struct driver_dev *dev) {
    // Assert reset (active-low)
    int ret = no_os_gpio_set_value(dev->reset, NO_OS_GPIO_LOW);
    if (ret)
        return ret;
    
    // Hold for minimum reset pulse width (10ms)
    no_os_mdelay(10);
    
    // Release reset
    ret = no_os_gpio_set_value(dev->reset, NO_OS_GPIO_HIGH);
    if (ret)
        return ret;
    
    // Wait for device to initialize (100ms)
    no_os_mdelay(100);
    
    return 0;
}
```

### Pattern: Bidirectional Pin

```c
/**
 * @brief Write data to bidirectional pin
 */
static int write_data(struct driver_dev *dev, uint8_t value) {
    // Switch to output
    int ret = no_os_gpio_direction_output(dev->data_pin, value);
    if (ret)
        return ret;
    
    no_os_udelay(10);  // Allow data to settle
    
    return 0;
}

/**
 * @brief Read data from bidirectional pin
 */
static int read_data(struct driver_dev *dev, uint8_t *value) {
    // Switch to input
    int ret = no_os_gpio_direction_input(dev->data_pin);
    if (ret)
        return ret;
    
    no_os_udelay(10);  // Allow input to settle
    
    return no_os_gpio_get_value(dev->data_pin, value);
}

/**
 * @brief Release bidirectional pin (high-Z)
 */
static int release_data(struct driver_dev *dev) {
    // Set to high-impedance
    return no_os_gpio_set_value(dev->data_pin, NO_OS_GPIO_HIGH_Z);
}
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Not Checking Return Values

**Wrong:**
```c
no_os_gpio_get(&gpio, &init);  // Ignoring return value
no_os_gpio_set_value(gpio, NO_OS_GPIO_HIGH);  // May crash if get() failed
```

**Right:**
```c
ret = no_os_gpio_get(&gpio, &init);
if (ret)
    return ret;
no_os_gpio_set_value(gpio, NO_OS_GPIO_HIGH);
```

### Anti-Pattern 2: Hardcoding Platform Ops

**Wrong:**
```c
struct no_os_gpio_init_param init = {
    .platform_ops = &max_gpio_ops,  // Only works on Maxim!
};
```

**Right:**
```c
// Pass platform ops from application/board config
struct no_os_gpio_init_param init = {
    .platform_ops = board_config->gpio_ops,  // Platform-agnostic
};
```

### Anti-Pattern 3: Mixing GPIO and Peripheral Functions

**Wrong:**
```c
// Configure pin as GPIO
no_os_gpio_get(&gpio, &init);
// Also configure same pin as SPI
no_os_spi_init(&spi, &spi_init);  // Conflict!
```

**Right:**
```c
// Use GPIO OR peripheral, not both
// If pin used for SPI, don't configure as GPIO
```

### Anti-Pattern 4: Not Initializing Optional GPIO Pointer

**Wrong:**
```c
struct driver_dev *dev;  // Uninitialized
dev->optional_gpio = ???;  // Random value

if (dev->optional_gpio)  // False positive if contains garbage
    no_os_gpio_set_value(dev->optional_gpio, NO_OS_GPIO_HIGH);
```

**Right:**
```c
struct driver_dev *dev = calloc(1, sizeof(*dev));  // Zero-initialize
// dev->optional_gpio is now NULL

if (dev->optional_gpio)  // Safe check
    no_os_gpio_set_value(dev->optional_gpio, NO_OS_GPIO_HIGH);
```

### Anti-Pattern 5: Changing Direction Frequently

**Wrong:**
```c
while (1) {
    no_os_gpio_direction_output(pin, NO_OS_GPIO_HIGH);
    no_os_gpio_direction_input(pin);
    // Rapid direction changes
}
```

**Right:**
```c
// Set direction once during initialization
no_os_gpio_direction_output(pin, NO_OS_GPIO_LOW);

// Only change value
while (1) {
    no_os_gpio_set_value(pin, NO_OS_GPIO_HIGH);
    no_os_mdelay(100);
    no_os_gpio_set_value(pin, NO_OS_GPIO_LOW);
    no_os_mdelay(100);
}
```

## Power Optimization

### Enable Pull Resistors to Prevent Floating Inputs

**Problem:** Floating inputs oscillate between high/low, causing:
- Excessive power consumption (input buffers switching)
- Incorrect readings
- EMI generation

**Solution:**
```c
struct no_os_gpio_init_param init = {
    .pull = NO_OS_PULL_DOWN,  // Prevent floating
};
```

### Use HIGH-Z for Unused Outputs

**Problem:** Driving outputs when not needed wastes power.

**Solution:**
```c
// When not driving bus
no_os_gpio_set_value(data_pin, NO_OS_GPIO_HIGH_Z);
```

### Disable Unused GPIOs

```c
// During low-power mode
no_os_gpio_remove(unused_gpio);  // Free resources
// Re-initialize when needed
```

## Platform-Specific Considerations

### Maxim (MAX32xxx, MAX78xxx)

- **Enable GPIO clock** before use (done by platform driver)
- **Voltage select** (VDDIO vs VDDIOH) via `vssel` in extras
- **Drive strength** configurable (0-3, higher = stronger drive)

### STM32

- **Alternate functions** must be disabled for GPIO mode
- **Speed grade** affects slew rate and power
- **Output mode** (push-pull vs open-drain) configurable

### Mbed

- **Pin names** instead of port/number (e.g., LED1, PA_5)
- **Limited configuration** - some settings not exposed
- **Platform abstraction** may hide low-level control
