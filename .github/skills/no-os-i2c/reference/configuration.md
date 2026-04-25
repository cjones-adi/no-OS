# I2C Configuration Details

This document covers I2C configuration including data structures, speed modes, addressing, and bus management.

## Core Data Structures

### no_os_i2c_init_param - Initialization Parameters

```c
struct no_os_i2c_init_param {
    uint32_t device_id;              // I2C bus number (0, 1, 2...)
    uint32_t max_speed_hz;           // Max I2C speed (100k, 400k, 1M)
    uint8_t slave_address;           // 7-bit slave address
    const struct no_os_i2c_platform_ops *platform_ops;
    void *extra;                     // Platform-specific params
};
```

**Field details:**

**device_id:**
- Hardware I2C bus number
- 0 = I2C0, 1 = I2C1, 2 = I2C2, etc.
- Maps to physical I2C controller on microcontroller

**max_speed_hz:**
- Maximum I2C clock frequency in Hertz
- See Speed Modes section below

**slave_address:**
- 7-bit I2C slave address (NOT 8-bit R/W format)
- Range: 0x08 to 0x77 (0x00-0x07 and 0x78-0x7F reserved)
- Example: 0x48, not 0x90

**platform_ops:**
- Pointer to platform-specific function table
- Example: `&max_i2c_ops`, `&stm32_i2c_ops`, `&mbed_i2c_ops`

**extra:**
- Pointer to platform-specific initialization parameters
- Can be NULL if platform doesn't need extra config
- Example: GPIO configuration, DMA settings, etc.

### no_os_i2c_desc - Runtime Descriptor

```c
struct no_os_i2c_desc {
    struct no_os_i2cbus_desc *bus;   // Shared bus descriptor
    uint32_t device_id;              // I2C bus number
    uint32_t max_speed_hz;           // Max speed
    uint8_t slave_address;           // Slave address
    const struct no_os_i2c_platform_ops *platform_ops;
    void *extra;                     // Platform-specific data
};
```

**Purpose:**
- Created by `no_os_i2c_init()`
- Represents one I2C slave device
- Multiple descriptors can share same bus
- Contains pointer to shared bus descriptor

### no_os_i2cbus_desc - Shared Bus Descriptor

```c
struct no_os_i2cbus_desc {
    void *mutex;                     // Bus mutex (thread safety)
    uint8_t slave_number;            // Number of slaves on bus
    uint32_t device_id;              // Bus number
    uint32_t max_speed_hz;           // Bus max speed
    const struct no_os_i2c_platform_ops *platform_ops;
    void *extra;                     // Platform-specific
};
```

**Purpose:**
- Automatically created when first device is initialized
- Shared by all devices on same bus (same device_id)
- Provides thread-safe access via mutex
- Reference counted (freed when last device removed)

### no_os_i2c_platform_ops - Platform Function Pointers

```c
struct no_os_i2c_platform_ops {
    int32_t (*i2c_ops_init)(struct no_os_i2c_desc **,
                            const struct no_os_i2c_init_param *);
    int32_t (*i2c_ops_write)(struct no_os_i2c_desc *, uint8_t *,
                             uint8_t, uint8_t);
    int32_t (*i2c_ops_read)(struct no_os_i2c_desc *, uint8_t *,
                            uint8_t, uint8_t);
    int32_t (*i2c_ops_remove)(struct no_os_i2c_desc *);
};
```

**Purpose:**
- Platform abstraction layer
- Platform implements these functions
- Device driver calls generic API, which calls platform ops

## I2C Speed Modes

### Standard Mode (Sm) - 100 kHz

```c
.max_speed_hz = 100000,  // 100 kHz
```

**Characteristics:**
- Original I2C speed
- Maximum capacitive load: 400 pF
- Pull-up resistors: 4.7 kΩ typical

**Use when:**
- Long cable runs (>1 meter)
- Many devices on bus (high capacitance)
- Debugging I2C issues
- Device only supports standard mode

### Fast Mode (Fm) - 400 kHz

```c
.max_speed_hz = 400000,  // 400 kHz
```

**Characteristics:**
- Most commonly used speed
- Maximum capacitive load: 400 pF
- Pull-up resistors: 2.2 kΩ typical

**Use when:**
- Normal operation (default choice)
- Moderate cable lengths (<50 cm)
- Good balance of speed and reliability

### Fast Mode Plus (Fm+) - 1 MHz

```c
.max_speed_hz = 1000000,  // 1 MHz
```

**Characteristics:**
- Requires compatible devices
- Maximum capacitive load: 550 pF
- Pull-up resistors: 1 kΩ typical
- May require active pull-ups or current source

**Use when:**
- Short connections (<20 cm)
- Few devices on bus
- Speed is critical
- All devices support Fm+

### High-Speed Mode (Hs) - 3.4 MHz

```c
.max_speed_hz = 3400000,  // 3.4 MHz
```

**Characteristics:**
- Rarely used in embedded systems
- Requires special current-source pull-ups
- Complex electrical requirements
- Not supported by all platforms

**Use when:**
- Specialized high-speed applications
- Very short connections
- Platform and all devices support Hs mode

## Speed Mode Selection Guidelines

**Start with 400 kHz:**
- Best default for most applications
- Good speed/reliability trade-off

**Use 100 kHz when:**
- I2C communication unstable at higher speeds
- Long cable runs
- Many devices on same bus
- Debugging communication issues

**Use 1 MHz when:**
- High data throughput needed (sensors, cameras)
- Short PCB traces
- All devices rated for Fm+
- Testing shows stable operation

## I2C Addressing

### 7-bit Addressing (Standard)

```c
.slave_address = 0x48,  // 7-bit address
```

**Format:**
- 7 bits for device address
- 1 bit for R/W (added automatically by hardware)
- Range: 0x08 to 0x77

**Reserved addresses:**
- 0x00-0x07: Reserved (general call, etc.)
- 0x78-0x7F: Reserved (10-bit addressing, etc.)

**Common device addresses:**
- 0x48-0x4F: Typical sensor range
- 0x50-0x57: EEPROM range
- 0x68-0x6F: IMU/motion sensors

### 10-bit Addressing (Rare)

Not commonly used in no-OS. If needed:
- Uses special address format
- Requires platform support
- Address range: 0x000 to 0x3FF

### Address Conflicts

**Problem:**
Multiple devices with same address on bus.

**Solutions:**

1. **Use devices with different addresses**
   ```c
   // Two temp sensors - check datasheet for address options
   .slave_address = 0x48,  // Sensor 1 (ADDR pin = GND)
   .slave_address = 0x49,  // Sensor 2 (ADDR pin = VCC)
   ```

2. **Use I2C multiplexer**
   ```c
   // Switch MUX to channel 0
   mux_select_channel(0);
   i2c_read_reg(temp_sensor, reg, &data);  // Address 0x48 on channel 0
   
   // Switch MUX to channel 1
   mux_select_channel(1);
   i2c_read_reg(temp_sensor, reg, &data);  // Address 0x48 on channel 1
   ```

3. **Use multiple I2C buses**
   ```c
   struct no_os_i2c_init_param bus0_init = {
       .device_id = 0,  // I2C0
       .slave_address = 0x48,
   };
   
   struct no_os_i2c_init_param bus1_init = {
       .device_id = 1,  // I2C1
       .slave_address = 0x48,  // Same address, different bus
   };
   ```

## I2C Bus Management

### Shared Bus Architecture

```
I2C Bus 0
├── Slave 0x48 (Temp sensor)   - i2c_desc_temp
├── Slave 0x50 (EEPROM)        - i2c_desc_eeprom
└── Slave 0x68 (IMU)           - i2c_desc_imu
```

**How it works:**
1. First `no_os_i2c_init()` on bus creates shared `no_os_i2cbus_desc`
2. Subsequent inits on same bus reuse shared bus descriptor
3. Each device has own `no_os_i2c_desc` with unique slave address
4. Transfers automatically lock bus mutex

### Automatic Bus Creation

```c
// First init on I2C0 creates bus
struct no_os_i2c_init_param temp_init = {
    .device_id = 0,  // I2C0
    .slave_address = 0x48,
    ...
};
no_os_i2c_init(&i2c_desc_temp, &temp_init);
// Bus created internally

// Subsequent inits share the bus
struct no_os_i2c_init_param eeprom_init = {
    .device_id = 0,  // Same I2C0
    .slave_address = 0x50,
    ...
};
no_os_i2c_init(&i2c_desc_eeprom, &eeprom_init);
// Reuses existing bus

struct no_os_i2c_init_param imu_init = {
    .device_id = 0,  // Same I2C0
    .slave_address = 0x68,
    ...
};
no_os_i2c_init(&i2c_desc_imu, &imu_init);
// Reuses existing bus
```

### Thread-Safe Transfers

Bus mutex automatically locks during transfers:

```c
int32_t no_os_i2c_write(struct no_os_i2c_desc *desc, ...)
{
    // Acquire bus lock
    no_os_mutex_lock(desc->bus->mutex);
    
    // Perform transfer
    ret = desc->platform_ops->i2c_ops_write(desc, data, bytes, stop);
    
    // Release bus lock
    no_os_mutex_unlock(desc->bus->mutex);
    
    return ret;
}
```

**Implications:**
- Transfers are atomic
- Other threads wait for bus to be free
- No manual locking needed by user
- Prevents bus conflicts in multi-threaded systems

### Bus Speed Negotiation

When multiple devices on same bus have different speed requirements:

```c
// Device 1: supports up to 1 MHz
struct no_os_i2c_init_param dev1_init = {
    .device_id = 0,
    .max_speed_hz = 1000000,
    ...
};

// Device 2: only supports 100 kHz
struct no_os_i2c_init_param dev2_init = {
    .device_id = 0,  // Same bus
    .max_speed_hz = 100000,  // Slower device
    ...
};

// Initialize both
no_os_i2c_init(&dev1, &dev1_init);
no_os_i2c_init(&dev2, &dev2_init);

// Bus will operate at slowest speed (100 kHz)
// All devices must support this speed
```

**Best practice:**
Set `max_speed_hz` to slowest device on bus for all devices.

## Electrical Configuration

### Pull-up Resistors

I2C requires pull-up resistors on SDA and SCL:

**Calculation:**
```
R_min = (VCC - VOL_max) / IOL
R_max = tr / (0.8473 × Cb)

Where:
- VOL_max: Maximum low-level output voltage (typically 0.4V)
- IOL: Low-level output current (3mA for standard, 6mA for fast mode)
- tr: Maximum rise time (1000ns standard, 300ns fast mode)
- Cb: Total bus capacitance (pF)
```

**Typical values:**

| Speed Mode | Typical Resistor |
|------------|-----------------|
| 100 kHz    | 4.7 kΩ          |
| 400 kHz    | 2.2 kΩ          |
| 1 MHz      | 1.0 kΩ          |

**Guidelines:**
- Stronger pull-ups (lower resistance) = faster rise times
- Weaker pull-ups (higher resistance) = lower power consumption
- Too strong = excessive current when bus is low
- Too weak = slow rise times, unreliable communication

### Bus Capacitance

Total capacitance = wire capacitance + device capacitance

**Typical values:**
- PCB trace: ~1-2 pF/cm
- Device input: 5-10 pF per device
- Connector: 2-5 pF

**Example:**
- 10 cm trace: 20 pF
- 3 devices × 7 pF: 21 pF
- Total: ~40 pF (well within limits)

**Limits:**
- Standard/Fast mode: 400 pF
- Fast+ mode: 550 pF

## Platform-Specific Configuration Examples

### Maxim Platform

```c
#include "maxim_i2c.h"

struct max_i2c_init_param max_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // VDDIO voltage level
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,
    .platform_ops = &max_i2c_ops,
    .extra = &max_extra,
};
```

### STM32 Platform

```c
#include "stm32_i2c.h"

struct stm32_i2c_init_param stm32_extra = {
    .i2c_timing = 0x00000000,  // Auto-calculated if 0
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,
    .platform_ops = &stm32_i2c_ops,
    .extra = &stm32_extra,
};
```

### Mbed Platform

```c
#include "mbed_i2c.h"

struct mbed_i2c_init_param mbed_extra = {
    .i2c_sda_pin = I2C_SDA,  // PinName from mbed
    .i2c_scl_pin = I2C_SCL,  // PinName from mbed
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,
    .platform_ops = &mbed_i2c_ops,
    .extra = &mbed_extra,
};
```
