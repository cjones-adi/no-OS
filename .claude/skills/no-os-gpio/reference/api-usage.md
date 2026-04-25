# API Usage Patterns and Examples

Complete guide to using no-OS GPIO API in device drivers.

## GPIO Initialization Workflow

### Basic GPIO – Always Required

```c
struct no_os_gpio_desc *gpio_desc;

struct no_os_gpio_init_param gpio_init = {
    .port = 0,                    // Port 0
    .number = 5,                  // Pin 5
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
};

// Get GPIO (fails if not available)
ret = no_os_gpio_get(&gpio_desc, &gpio_init);
if (ret)
    return ret;

// Configure as output, set HIGH
no_os_gpio_direction_output(gpio_desc, NO_OS_GPIO_HIGH);
```

### Optional GPIO – May Not Be Present

Used for optional features (e.g., LED that may not exist on all boards):

```c
struct no_os_gpio_desc *led_gpio = NULL;

struct no_os_gpio_init_param led_init = {
    .port = 1,
    .number = 10,
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
};

// Get optional - returns success even if pin doesn't exist
ret = no_os_gpio_get_optional(&led_gpio, &led_init);

// Check if GPIO is available before using
if (led_gpio) {
    no_os_gpio_direction_output(led_gpio, NO_OS_GPIO_HIGH);
}
```

**To mark GPIO as not present:**
```c
struct no_os_gpio_init_param led_init = {
    .number = -1,  // -1 means not present
    // ... other fields
};

no_os_gpio_get_optional(&led_gpio, &led_init);
// led_gpio will be NULL, no error returned
```

## GPIO Operations

### 1. Configure Direction

**Set as Input:**
```c
int32_t no_os_gpio_direction_input(struct no_os_gpio_desc *desc);
```

**Set as Output (with initial value):**
```c
int32_t no_os_gpio_direction_output(struct no_os_gpio_desc *desc,
                                    uint8_t value);
```

**Get Current Direction:**
```c
int32_t no_os_gpio_get_direction(struct no_os_gpio_desc *desc,
                                 uint8_t *direction);

// direction: NO_OS_GPIO_IN (0) or NO_OS_GPIO_OUT (1)
```

**Example:**
```c
// Configure as input
no_os_gpio_direction_input(button_gpio);

// Configure as output, initially LOW
no_os_gpio_direction_output(led_gpio, NO_OS_GPIO_LOW);

// Check direction
uint8_t dir;
no_os_gpio_get_direction(led_gpio, &dir);
if (dir == NO_OS_GPIO_OUT)
    printf("Pin is output\n");
```

### 2. Read/Write Values

**Set Output Value:**
```c
int32_t no_os_gpio_set_value(struct no_os_gpio_desc *desc,
                             uint8_t value);
```

**Get Input/Output Value:**
```c
int32_t no_os_gpio_get_value(struct no_os_gpio_desc *desc,
                             uint8_t *value);
```

**Example:**
```c
// Set output HIGH
no_os_gpio_set_value(led_gpio, NO_OS_GPIO_HIGH);

// Set output LOW
no_os_gpio_set_value(led_gpio, NO_OS_GPIO_LOW);

// Read input
uint8_t button_state;
no_os_gpio_get_value(button_gpio, &button_state);
if (button_state == NO_OS_GPIO_HIGH)
    printf("Button pressed\n");

// Read output (reads back what was written)
uint8_t led_state;
no_os_gpio_get_value(led_gpio, &led_state);
```

### 3. Cleanup

```c
int32_t no_os_gpio_remove(struct no_os_gpio_desc *desc);
```

**Example:**
```c
no_os_gpio_remove(gpio_desc);
```

## Common GPIO Patterns

### Pattern 1: LED Control

```c
struct no_os_gpio_desc *led;

// Initialize
struct no_os_gpio_init_param led_init = {
    .port = 1,
    .number = 3,
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
};

no_os_gpio_get(&led, &led_init);
no_os_gpio_direction_output(led, NO_OS_GPIO_LOW);  // LED off

// Turn on
no_os_gpio_set_value(led, NO_OS_GPIO_HIGH);

// Turn off
no_os_gpio_set_value(led, NO_OS_GPIO_LOW);

// Toggle
uint8_t state;
no_os_gpio_get_value(led, &state);
no_os_gpio_set_value(led, !state);
```

### Pattern 2: Button with Pull-up

```c
struct no_os_gpio_desc *button;

struct no_os_gpio_init_param button_init = {
    .port = 0,
    .number = 15,
    .pull = NO_OS_PULL_UP,  // Active-low button
    .platform_ops = &max_gpio_ops,
};

no_os_gpio_get(&button, &button_init);
no_os_gpio_direction_input(button);

// Read button (LOW when pressed due to pull-up)
uint8_t pressed;
no_os_gpio_get_value(button, &pressed);
if (pressed == NO_OS_GPIO_LOW)
    printf("Button pressed\n");
```

### Pattern 3: Chip Select (Active-Low)

```c
struct no_os_gpio_desc *cs;

struct no_os_gpio_init_param cs_init = {
    .port = 2,
    .number = 0,
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
};

no_os_gpio_get(&cs, &cs_init);
no_os_gpio_direction_output(cs, NO_OS_GPIO_HIGH);  // Deasserted

// Assert CS (select device)
no_os_gpio_set_value(cs, NO_OS_GPIO_LOW);

// ... SPI transfer ...

// Deassert CS (deselect device)
no_os_gpio_set_value(cs, NO_OS_GPIO_HIGH);
```

### Pattern 4: Reset Pin

```c
struct no_os_gpio_desc *reset;

struct no_os_gpio_init_param reset_init = {
    .port = 1,
    .number = 7,
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
};

no_os_gpio_get(&reset, &reset_init);

// Hold in reset
no_os_gpio_direction_output(reset, NO_OS_GPIO_LOW);
no_os_mdelay(10);  // Wait 10ms

// Release reset
no_os_gpio_set_value(reset, NO_OS_GPIO_HIGH);
no_os_mdelay(100);  // Wait for device to initialize
```

### Pattern 5: Bidirectional I/O

```c
struct no_os_gpio_desc *data_pin;

// Initialize with high-impedance
no_os_gpio_get(&data_pin, &data_init);

// Write mode
no_os_gpio_direction_output(data_pin, NO_OS_GPIO_HIGH);
// ... write data ...

// Read mode
no_os_gpio_direction_input(data_pin);
uint8_t value;
no_os_gpio_get_value(data_pin, &value);

// Back to high-impedance (releases bus)
no_os_gpio_set_value(data_pin, NO_OS_GPIO_HIGH_Z);
```

### Pattern 6: Optional GPIO Handling

```c
struct no_os_gpio_desc *optional_led = NULL;

struct no_os_gpio_init_param led_init = {
    .port = 1,
    .number = 10,
    .platform_ops = &max_gpio_ops,
};

// Try to get LED (won't fail if not present)
no_os_gpio_get_optional(&optional_led, &led_init);

// Safe to call even if NULL
if (optional_led) {
    no_os_gpio_direction_output(optional_led, NO_OS_GPIO_HIGH);
}

// Later...
if (optional_led) {
    no_os_gpio_set_value(optional_led, NO_OS_GPIO_LOW);
}
```

## Function Reference

| Function | Purpose |
|----------|---------|
| `no_os_gpio_get()` | Get GPIO (required) |
| `no_os_gpio_get_optional()` | Get GPIO (optional, can be absent) |
| `no_os_gpio_remove()` | Free GPIO resources |
| `no_os_gpio_direction_input()` | Configure as input |
| `no_os_gpio_direction_output()` | Configure as output with initial value |
| `no_os_gpio_get_direction()` | Read current direction |
| `no_os_gpio_set_value()` | Write output value |
| `no_os_gpio_get_value()` | Read input/output value |
