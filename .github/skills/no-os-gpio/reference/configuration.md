# GPIO Configuration Details

Complete reference for GPIO data structures and configuration options.

## Core Data Structures

### 1. no_os_gpio_init_param – Initialization Parameters

```c
struct no_os_gpio_init_param {
    int32_t port;                    // Port number (e.g., PORTA, PORTB)
    int32_t number;                  // Pin number (0-31 typically)
    enum no_os_gpio_pull_up pull;   // Pull resistor config
    const struct no_os_gpio_platform_ops *platform_ops;
    void *extra;                     // Platform-specific params
};
```

**Fields:**
- `port` - GPIO port number (platform-specific numbering)
- `number` - GPIO pin number within port (set to -1 for optional GPIO not present)
- `pull` - Pull resistor configuration (see no_os_gpio_pull_up)
- `platform_ops` - Pointer to platform function table
- `extra` - Platform-specific initialization parameters (cast to platform struct)

### 2. no_os_gpio_desc – Runtime Descriptor

```c
struct no_os_gpio_desc {
    int32_t port;                    // Port number
    int32_t number;                  // Pin number
    enum no_os_gpio_pull_up pull;   // Pull resistor config
    const struct no_os_gpio_platform_ops *platform_ops;
    void *extra;                     // Platform-specific data
};
```

**Fields:**
- Same as init_param but represents active GPIO instance
- Allocated by `no_os_gpio_get()`, freed by `no_os_gpio_remove()`
- Passed to all GPIO operations
- `extra` may contain platform runtime state (not just init params)

### 3. no_os_gpio_pull_up – Pull Resistor Configuration

```c
enum no_os_gpio_pull_up {
    NO_OS_PULL_NONE,           // No pull resistor
    NO_OS_PULL_UP,             // Strong pull-up
    NO_OS_PULL_DOWN,           // Strong pull-down
    NO_OS_PULL_UP_WEAK,        // Weak pull-up
    NO_OS_PULL_DOWN_WEAK       // Weak pull-down
};
```

**Use cases:**

**NO_OS_PULL_NONE** - No pull resistor
- Output pins (don't need pull)
- Inputs with external pull resistors
- Analog inputs
- High-speed signals

**NO_OS_PULL_UP** - Strong pull-up resistor
- Active-low buttons (button grounds pin when pressed)
- I2C pins (if no external pull-ups)
- SPI chip select when not driving
- Open-drain signals

**NO_OS_PULL_DOWN** - Strong pull-down resistor
- Active-high buttons (button connects to VDD when pressed)
- Signals that default to low when not driven
- Detecting cable presence (pulled high when connected)

**NO_OS_PULL_UP_WEAK** - Weak pull-up
- Lower power consumption than strong pull-up
- When multiple devices share pull resistor
- Slow signals that don't need strong drive

**NO_OS_PULL_DOWN_WEAK** - Weak pull-down
- Lower power consumption than strong pull-down
- Detecting presence of external device
- Default low state with minimal current

**Note**: Not all platforms support weak variants. May fall back to strong pull.

### 4. no_os_gpio_values – Output States

```c
enum no_os_gpio_values {
    NO_OS_GPIO_LOW,            // Logic low (0V)
    NO_OS_GPIO_HIGH,           // Logic high (VDD)
    NO_OS_GPIO_HIGH_Z          // High impedance (tri-state)
};
```

**NO_OS_GPIO_LOW** - Logic 0
- Output drives to ground (0V)
- Used for: active-low signals, reset asserted, LED on (if active-low)

**NO_OS_GPIO_HIGH** - Logic 1
- Output drives to supply voltage (VDD, typically 3.3V or 1.8V)
- Used for: active-high signals, reset released, LED on (if active-high)

**NO_OS_GPIO_HIGH_Z** - High impedance (tri-state)
- Output driver disabled, pin floats
- Useful for:
  - Bus sharing (multiple devices on same signal)
  - Preventing conflicts during initialization
  - Power saving (no drive current)
  - Bidirectional pins (switch between input/output)
  - Testing with external equipment

**Note**: Not all platforms support HIGH_Z. May require changing direction to input instead.

## Architecture Overview

```
┌──────────────────────────────────────────┐
│    User Application / Device Driver     │
│  (Platform-independent code)            │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┴──────────┐
    │   no_os_gpio.h      │  Platform-agnostic API
    │   (Generic)         │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────────────────┐
    │                                  │
┌───▼──────────┐        ┌──────────────▼───┐
│maxim_gpio.c  │        │   mbed_gpio.cpp  │
│maxim_gpio.h  │        │   mbed_gpio.h    │
└───┬──────────┘        └──────────┬───────┘
    │                               │
┌───▼──────────┐        ┌──────────▼───────┐
│ Maxim HAL    │        │   Mbed HAL       │
│ (Vendor SDK) │        │   (Vendor SDK)   │
└──────────────┘        └──────────────────┘
```

## File Structure

### 1. no_os_gpio.h – Platform-Agnostic Interface

Location: `include/no_os_gpio.h`

Contains generic structures and function prototypes.

**Key components:**
- `no_os_gpio_init_param` – Initialization parameters
- `no_os_gpio_desc` – Runtime GPIO descriptor
- `no_os_gpio_platform_ops` – Function pointers
- `no_os_gpio_values` – Output states (HIGH/LOW/HIGH-Z)
- `no_os_gpio_pull_up` – Pull resistor configuration

### 2. Platform-Specific Implementation

**Example:** `drivers/platform/maxim/maxim_gpio.c`

Platform-specific code interfacing with vendor HAL:
- Implements platform ops functions
- Calls vendor HAL functions
- Handles platform quirks
- Manages GPIO peripheral clocks

### 3. Platform-Specific Extras

**Example:** `drivers/platform/maxim/maxim_gpio.h`

Platform-specific parameters:
- Drive strength settings
- Voltage level configuration
- Slew rate control
- Other hardware-specific features

**Example struct:**
```c
struct maxim_gpio_init_param {
    mxc_gpio_vssel_t vssel;      // Voltage select
    mxc_gpio_drvstr_t strength;  // Drive strength
};
```

## Pin Numbering

**Platform-specific numbering:**
- Each platform defines its own port/pin numbering
- Usually matches vendor HAL or datasheet numbering
- Common schemes:

**Scheme 1: Separate port and pin**
```c
.port = 0,    // Port A
.number = 5,  // Pin 5
// Physical pin: PA5 or GPIO0_5
```

**Scheme 2: Flat GPIO numbering**
```c
.port = 0,     // Ignored
.number = 37,  // GPIO 37
// Physical pin: GPIO37
```

**Scheme 3: Encoded port/pin**
```c
.port = 2,    // Port C (0=A, 1=B, 2=C)
.number = 13, // Pin 13
// Physical pin: PC13
```

**Check platform documentation for correct numbering scheme.**

## Direction Values

```c
#define NO_OS_GPIO_OUT  1    // Output direction
#define NO_OS_GPIO_IN   0    // Input direction
```

Used with `no_os_gpio_get_direction()`:
```c
uint8_t dir;
no_os_gpio_get_direction(gpio, &dir);
if (dir == NO_OS_GPIO_OUT) {
    // Pin is configured as output
}
```

## Platform Extras Examples

### Maxim Platform

```c
#include "maxim_gpio.h"

struct maxim_gpio_init_param max_gpio_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // 3.3V I/O
    .strength = MXC_GPIO_DRVSTR_0,   // Normal drive
};

struct no_os_gpio_init_param gpio_init = {
    .port = 0,
    .number = 5,
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &max_gpio_ops,
    .extra = &max_gpio_extra,  // Platform-specific config
};
```

### STM32 Platform

```c
#include "stm32_gpio.h"

struct stm32_gpio_init_param stm32_gpio_extra = {
    .mode = GPIO_MODE_OUTPUT_PP,     // Push-pull output
    .speed = GPIO_SPEED_FREQ_HIGH,   // High speed
    .alternate = 0,                  // No alternate function
};

struct no_os_gpio_init_param gpio_init = {
    .port = 0,  // GPIOA
    .number = 5,
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &stm32_gpio_ops,
    .extra = &stm32_gpio_extra,
};
```

### Mbed Platform

```c
#include "mbed_gpio.h"

// Mbed uses pin names, not port/number
struct mbed_gpio_init_param mbed_gpio_extra = {
    .pin_mode = PullNone,
};

struct no_os_gpio_init_param gpio_init = {
    .port = 0,     // Not used on Mbed
    .number = LED1,  // Mbed pin name (e.g., LED1, PA_5)
    .pull = NO_OS_PULL_NONE,
    .platform_ops = &mbed_gpio_ops,
    .extra = &mbed_gpio_extra,
};
```
