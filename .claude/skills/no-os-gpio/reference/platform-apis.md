# Platform API Implementations

Complete reference for implementing GPIO platform drivers for new platforms.

## Porting to New Platforms

### Step 1: Create Platform Files

```
drivers/platform/myplatform/
├── myplatform_gpio.c      # Implementation
└── myplatform_gpio.h      # Platform extras
```

### Step 2: Define Platform Extras (if needed)

In `myplatform_gpio.h`:

```c
struct myplatform_gpio_init_param {
    uint32_t drive_strength;     // Output drive strength
    uint32_t slew_rate;          // Slew rate control
    // ... other platform specifics
};
```

### Step 3: Implement Platform Operations

In `myplatform_gpio.c`:

```c
int32_t myplatform_gpio_get(struct no_os_gpio_desc **desc,
                            const struct no_os_gpio_init_param *param)
{
    // 1. Allocate descriptor
    *desc = calloc(1, sizeof(**desc));

    // 2. Configure GPIO using vendor HAL
    // Example: HAL_GPIO_Init(...);

    // 3. Copy parameters
    (*desc)->port = param->port;
    (*desc)->number = param->number;
    (*desc)->pull = param->pull;

    return 0;
}

int32_t myplatform_gpio_direction_input(struct no_os_gpio_desc *desc)
{
    // Configure as input using vendor HAL
    // Example: HAL_GPIO_SetDirection(port, pin, INPUT);

    return 0;
}

int32_t myplatform_gpio_direction_output(struct no_os_gpio_desc *desc,
                                         uint8_t value)
{
    // Set initial value
    myplatform_gpio_set_value(desc, value);

    // Configure as output
    // Example: HAL_GPIO_SetDirection(port, pin, OUTPUT);

    return 0;
}

int32_t myplatform_gpio_set_value(struct no_os_gpio_desc *desc,
                                  uint8_t value)
{
    // Write value using vendor HAL
    // Example: HAL_GPIO_WritePin(port, pin, value);

    return 0;
}

int32_t myplatform_gpio_get_value(struct no_os_gpio_desc *desc,
                                  uint8_t *value)
{
    // Read value using vendor HAL
    // Example: *value = HAL_GPIO_ReadPin(port, pin);

    return 0;
}

int32_t myplatform_gpio_remove(struct no_os_gpio_desc *desc)
{
    // Cleanup
    // Example: HAL_GPIO_DeInit(port, pin);

    free(desc);
    return 0;
}
```

### Step 4: Define Platform Ops

```c
const struct no_os_gpio_platform_ops myplatform_gpio_ops = {
    .gpio_ops_get = &myplatform_gpio_get,
    .gpio_ops_get_optional = &myplatform_gpio_get,  // Can reuse
    .gpio_ops_remove = &myplatform_gpio_remove,
    .gpio_ops_direction_input = &myplatform_gpio_direction_input,
    .gpio_ops_direction_output = &myplatform_gpio_direction_output,
    .gpio_ops_get_direction = &myplatform_gpio_get_direction,
    .gpio_ops_set_value = &myplatform_gpio_set_value,
    .gpio_ops_get_value = &myplatform_gpio_get_value,
};
```

## Platform Function Pointers

```c
struct no_os_gpio_platform_ops {
    int32_t (*gpio_ops_get)(struct no_os_gpio_desc **,
                            const struct no_os_gpio_init_param *);
    int32_t (*gpio_ops_get_optional)(struct no_os_gpio_desc **,
                                     const struct no_os_gpio_init_param *);
    int32_t (*gpio_ops_remove)(struct no_os_gpio_desc *);
    int32_t (*gpio_ops_direction_input)(struct no_os_gpio_desc *);
    int32_t (*gpio_ops_direction_output)(struct no_os_gpio_desc *, uint8_t);
    int32_t (*gpio_ops_get_direction)(struct no_os_gpio_desc *, uint8_t *);
    int32_t (*gpio_ops_set_value)(struct no_os_gpio_desc *, uint8_t);
    int32_t (*gpio_ops_get_value)(struct no_os_gpio_desc *, uint8_t *);
};
```

**Required functions:**
- `gpio_ops_get` - Initialize and acquire GPIO pin
- `gpio_ops_get_optional` - Initialize optional GPIO (can be same as get)
- `gpio_ops_remove` - Free GPIO resources
- `gpio_ops_direction_input` - Configure as input
- `gpio_ops_direction_output` - Configure as output with initial value
- `gpio_ops_get_direction` - Read current direction (optional on some platforms)
- `gpio_ops_set_value` - Write output value
- `gpio_ops_get_value` - Read input/output value

## Implementation Tips

**Allocating descriptors:**
- Always use `calloc()` to zero-initialize
- Store platform-specific data in `desc->extra`
- Copy init parameters to descriptor

**Error handling:**
- Return 0 on success
- Return negative errno codes on failure (-EINVAL, -ENODEV, -EIO)
- Validate parameters before hardware access

**Direction changes:**
- Set initial value BEFORE configuring as output
- Clear interrupts when changing direction
- Update cached state if needed

**Vendor HAL integration:**
- Enable GPIO peripheral clock if needed
- Configure alternate function / pin mux
- Apply platform-specific settings (drive strength, slew rate)
- Handle vendor HAL error codes

**Optional GPIO handling:**
- `gpio_ops_get_optional` can usually reuse `gpio_ops_get`
- Return success with NULL descriptor if pin number is -1
- Don't fail initialization if optional pin unavailable

## Common Platform Issues

**Missing GPIO clock**
```c
// Enable GPIO peripheral clock before configuration
HAL_RCC_GPIOx_CLK_ENABLE();
```

**Pin numbering differences**
```c
// Platform uses 0-based numbering
platform_pin = param->number;

// Platform uses 1-based numbering
platform_pin = param->number + 1;

// Platform uses port + pin
platform_port = param->port;
platform_pin = param->number;
```

**Alternate function conflicts**
```c
// Ensure GPIO function selected (not UART/SPI/etc.)
HAL_GPIO_SetAlternateFunction(port, pin, GPIO_AF_NONE);
```

**Pull resistor mapping**
```c
switch (param->pull) {
case NO_OS_PULL_NONE:
    platform_pull = PLATFORM_NOPULL;
    break;
case NO_OS_PULL_UP:
    platform_pull = PLATFORM_PULLUP;
    break;
case NO_OS_PULL_DOWN:
    platform_pull = PLATFORM_PULLDOWN;
    break;
}
```
