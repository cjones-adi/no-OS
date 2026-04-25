# Maxim Platform Initialization

Complete guide to platform initialization sequences, clock management, and peripheral setup for Maxim MCUs.

## System Initialization

### Platform Init Function

```c
// In maxim_init.c
__weak int no_os_init(void)
{
    // Configure SysTick for 1ms tick
    SysTick_Config(SystemCoreClock / 1000);
    return MXC_Delay(1);  // Initial delay
}
```

**Key Points**:
- Marked `__weak` to allow override in user code
- Configures SysTick timer for 1ms intervals
- SystemCoreClock is set by MCU startup code
- Initial delay stabilizes system

## Clock Management

### Peripheral Clock Enable

**Clock Gating Pattern**:
```c
// Enable peripheral clock before use
if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_DMA)) {
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_DMA);
    MXC_SYS_Reset_Periph(MAX_DMA_GCR_RST_POS);
}

// SPI example
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);

// I2C example
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_I2C0);
```

**Available Clock Gates**:
- `MXC_SYS_PERIPH_CLOCK_DMA` - DMA controller
- `MXC_SYS_PERIPH_CLOCK_SPI0/1/2/3` - SPI peripherals
- `MXC_SYS_PERIPH_CLOCK_I2C0/1/2` - I2C peripherals
- `MXC_SYS_PERIPH_CLOCK_UART0/1/2` - UART peripherals
- `MXC_SYS_PERIPH_CLOCK_GPIO0/1/2` - GPIO ports
- `MXC_SYS_PERIPH_CLOCK_TMR0/1/2/3` - Timers

### Clock Check Before Init

```c
// Check if peripheral clock is already enabled
if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_SPI0)) {
    pr_err("SPI0 clock not enabled\n");
    return -ENODEV;
}
```

### Peripheral Reset After Clock Enable

```c
// Reset peripheral for clean state
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_DMA);
MXC_SYS_Reset_Periph(MAX_DMA_GCR_RST_POS);
```

**Reset Positions**:
- Each peripheral has a specific reset bit position
- Reset clears all peripheral registers
- Always reset after enabling clock
- Ensures clean initialization state

## Pin Multiplexing (MXC_GPIO_Config)

### GPIO Configuration Structure

```c
typedef struct {
    mxc_gpio_regs_t *port;      // GPIO port pointer
    uint32_t mask;              // Pin mask (can be multiple pins)
    mxc_gpio_func_t func;       // Pin function (GPIO, ALT1, ALT2, ALT3)
    mxc_gpio_pad_t pad;         // Pull-up/pull-down configuration
    mxc_gpio_vssel_t vssel;     // Voltage selection (VDDIO or VDDIOH)
} mxc_gpio_cfg_t;
```

### GPIO Configuration Pattern

```c
mxc_gpio_cfg_t pin_config;

// Configure SPI pins
pin_config.port = MXC_GPIO_GET_GPIO(0);  // GPIO Port 0
pin_config.mask = MXC_GPIO_PIN_5 | MXC_GPIO_PIN_6 | MXC_GPIO_PIN_7;  // MOSI, MISO, SCK
pin_config.func = MXC_GPIO_FUNC_ALT1;     // Alternate function 1 (SPI)
pin_config.pad = MXC_GPIO_PAD_NONE;       // No pull resistor
pin_config.vssel = MXC_GPIO_VSSEL_VDDIO;  // VDDIO voltage level

MXC_GPIO_Config(&pin_config);
```

### Predefined Pin Configurations (SPI Example)

```c
// From maxim_spi.c
static mxc_gpio_cfg_t gpio_cfg_spi0_0;  // Standard pins
static mxc_gpio_cfg_t gpio_cfg_spi0_1;  // Alternate pins

// Selection based on device_id and chip_select
switch (desc->device_id) {
case 0:
    spi_pins = gpio_cfg_spi0_1;
    cs = gpio_cfg_spi0_0;
    break;
case 1:
    spi_pins = gpio_cfg_spi1;
    cs = gpio_cfg_spi1_ss;
    break;
}

// Apply VDDIO voltage selection
spi_pins.vssel = st->init_param->vssel;
MXC_GPIO_Config(&spi_pins);
```

### Pin Function Selection

**Available Functions**:
```c
typedef enum {
    MXC_GPIO_FUNC_IN,      // GPIO input
    MXC_GPIO_FUNC_OUT,     // GPIO output
    MXC_GPIO_FUNC_ALT1,    // Alternate function 1
    MXC_GPIO_FUNC_ALT2,    // Alternate function 2
    MXC_GPIO_FUNC_ALT3,    // Alternate function 3
    MXC_GPIO_FUNC_ALT4,    // Alternate function 4 (some families)
} mxc_gpio_func_t;
```

**Common Alternate Functions**:
- ALT1: SPI, I2C, UART (primary peripherals)
- ALT2: Timer, PWM, secondary peripherals
- ALT3: Additional peripheral functions
- ALT4: Special functions (family-specific)

**Check Datasheet**: Pin function mapping varies by MCU family and pin number.

### Pull Resistor Configuration

```c
typedef enum {
    MXC_GPIO_PAD_NONE,              // No pull resistor
    MXC_GPIO_PAD_WEAK_PULL_UP,      // Weak pull-up (~40kΩ)
    MXC_GPIO_PAD_WEAK_PULL_DOWN,    // Weak pull-down (~40kΩ)
} mxc_gpio_pad_t;
```

**Usage Guidelines**:
- **NONE**: For SPI/I2C/UART when external pull-ups present
- **WEAK_PULL_UP**: For I2C (if no external pull-ups), buttons
- **WEAK_PULL_DOWN**: For unused inputs (reduce power)

## VDDIO Voltage Selection

### Voltage Level Configuration

```c
// Available voltage levels (mxc_gpio_vssel_t)
MXC_GPIO_VSSEL_VDDIO   // Use VDDIO rail (1.8V or 3.3V)
MXC_GPIO_VSSEL_VDDIOH  // Use VDDIOH rail (always 3.3V)
```

### Setting VDDIO in Init Parameters

**SPI Example**:
```c
struct max_spi_init_param {
    mxc_gpio_vssel_t vssel;  // Voltage selection for SPI pins
};

struct max_spi_init_param spi_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // Use VDDIO (1.8V or 3.3V)
};
```

**GPIO Example**:
```c
struct max_gpio_init_param {
    mxc_gpio_vssel_t vssel;  // Voltage selection for GPIO
};

struct max_gpio_init_param gpio_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // Use VDDIOH (3.3V)
};
```

**I2C Example**:
```c
struct max_i2c_init_param {
    mxc_gpio_vssel_t vssel;  // Voltage selection for I2C pins
};

struct max_i2c_init_param i2c_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,  // Use VDDIO
};
```

### Voltage Selection Guidelines

**Use VDDIO when**:
- Interfacing with 1.8V devices
- Operating in low-power mode
- VDDIO rail matches peripheral voltage

**Use VDDIOH when**:
- Interfacing with 3.3V devices (RS232, SD cards)
- VDDIO is 1.8V but peripheral needs 3.3V
- Mixed-voltage system

**Critical**: Always match voltage selection to hardware design!

## Resource Tracking

### I2C Reference Counting

**Pattern**:
```c
// Global tracking array (one per I2C instance)
static uint8_t nb_created_desc[MXC_I2C_INSTANCES] = {0};

// In max_i2c_init():
if (nb_created_desc[param->device_id] == 0) {
    // First descriptor - initialize peripheral
    MXC_I2C_Shutdown(max_i2c->handler);
    MXC_I2C_Init(i2c_regs, I2C_MASTER_MODE, 0);
}

// Track descriptor count
nb_created_desc[param->device_id]++;

// In max_i2c_remove():
nb_created_desc[desc->device_id]--;
if (nb_created_desc[desc->device_id] == 0) {
    // Last descriptor - shutdown peripheral
    MXC_I2C_Shutdown(max_i2c->handler);
}
```

**Why Reference Counting?**:
- Multiple devices can share same I2C bus
- Only first descriptor initializes peripheral
- Peripheral shutdown only when all descriptors removed
- Prevents re-initialization conflicts

### DMA Single Instance Pattern

```c
static struct no_os_dma_desc *dma_descriptor = NULL;

static int maxim_dma_init(struct no_os_dma_desc **desc,
                          struct no_os_dma_init_param *param)
{
    // Single DMA controller per platform
    if (dma_descriptor) {
        *desc = dma_descriptor;
        return 0;  // Return existing descriptor
    }

    // First time - initialize DMA
    // ... initialization code ...

    dma_descriptor = descriptor;
    return 0;
}
```

**Pattern**:
- Only one DMA controller exists
- First call initializes hardware
- Subsequent calls return existing descriptor
- All peripherals share same DMA instance

## SysTick Configuration

### SysTick Handler Setup

```c
// Configure SysTick for 1ms tick
SysTick_Config(SystemCoreClock / 1000);
```

**Parameters**:
- `SystemCoreClock`: Core clock frequency (set by startup code)
- Dividing by 1000 gives 1ms tick period
- SysTick generates interrupt every 1ms

### SysTick Handler

```c
static volatile unsigned long long _system_ticks = 0;

void SysTick_Handler(void)
{
    MXC_DelayHandler();   // HAL delay handler
    _system_ticks++;      // Track milliseconds
}
```

**Responsibilities**:
- Call HAL delay handler (MXC_Delay support)
- Increment system tick counter
- Used by `no_os_get_time()` and delay functions

## Initialization Sequence

### Typical Platform Initialization Order

```c
int main(void)
{
    // 1. Platform init (SysTick setup)
    ret = no_os_init();

    // 2. Enable peripheral clocks
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_I2C0);
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_DMA);

    // 3. Initialize DMA (shared resource)
    struct no_os_dma_init_param dma_init = {
        .num_ch = 8,
        .platform_ops = &max_dma_ops,
    };
    ret = no_os_dma_init(&dma, &dma_init);

    // 4. Initialize peripherals (SPI, I2C, etc.)
    struct max_spi_init_param spi_extra = {
        .vssel = MXC_GPIO_VSSEL_VDDIO,
        .dma_param = &dma_init,
    };
    struct no_os_spi_init_param spi_init = {
        .device_id = 0,
        .max_speed_hz = 10000000,
        .extra = &spi_extra,
        .platform_ops = &max_spi_ops,
    };
    ret = no_os_spi_init(&spi, &spi_init);

    // 5. Application code
    // ...

    return 0;
}
```

### Error Handling in Initialization

```c
int main(void)
{
    int ret;

    ret = no_os_init();
    if (ret)
        goto error;

    ret = no_os_spi_init(&spi, &spi_init);
    if (ret)
        goto error_spi;

    ret = no_os_i2c_init(&i2c, &i2c_init);
    if (ret)
        goto error_i2c;

    // Application code
    return 0;

error_i2c:
    no_os_spi_remove(spi);
error_spi:
    // Platform-level cleanup
error:
    return ret;
}
```

## Family-Specific Considerations

### Conditional Compilation

```c
// Check for dual-DMA support
#ifdef MXC_DMA1
    // MAX32690 has two DMA controllers
    if (param->id == 1) {
        MAX_DMA = MXC_DMA1;
    }
#endif

// Check I2C instance availability
#ifdef MXC_I2C2
void I2C2_IRQHandler(void) {
    MXC_I2C_AsyncHandler(MXC_I2C2);
}
#endif
```

### Target-Specific Code

```c
// Use TARGET_NUM to identify MCU family
#if TARGET_NUM == 32650
    // MAX32650-specific code
#elif TARGET_NUM == 32690
    // MAX32690-specific code
#endif
```

## Common Initialization Errors

### Clock Not Enabled

**Symptom**: Peripheral doesn't respond, registers read as 0

**Fix**:
```c
if (!MXC_SYS_IsClockEnabled(MXC_SYS_PERIPH_CLOCK_SPI0)) {
    MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
}
```

### Wrong VDDIO Selection

**Symptom**: Communication fails, voltage level mismatch

**Fix**: Match `vssel` to hardware design
```c
// If VDDIO is 1.8V but peripheral needs 3.3V
spi_extra.vssel = MXC_GPIO_VSSEL_VDDIOH;  // Use 3.3V rail
```

### Pin Not Configured

**Symptom**: No signal on pin, peripheral doesn't work

**Fix**: Always configure pins after clock enable
```c
MXC_SYS_ClockEnable(MXC_SYS_PERIPH_CLOCK_SPI0);
_max_spi_config_pins(desc);  // Configure pins
```

### Multiple I2C Init on Same Bus

**Symptom**: Second descriptor fails or corrupts I2C state

**Fix**: Reference counting handles this automatically
```c
// Both descriptors share same I2C peripheral
no_os_i2c_init(&i2c_dev1, &i2c_init);  // First init
i2c_init.slave_address = 0x76;
no_os_i2c_init(&i2c_dev2, &i2c_init);  // Reuses peripheral
```

## Best Practices

1. **Always Enable Clocks First**: Enable peripheral clock before any configuration
2. **Reset After Clock Enable**: Reset peripheral for clean state
3. **Configure Pins Early**: Set up pin muxing before peripheral init
4. **Match VDDIO to Hardware**: Always verify voltage selection matches PCB design
5. **Use Reference Counting**: For shared resources (I2C, DMA)
6. **Check Family Support**: Use conditional compilation for family-specific features
7. **Implement Error Paths**: Handle initialization failures with cleanup
8. **Document VDDIO Choice**: Comment why specific voltage level selected
