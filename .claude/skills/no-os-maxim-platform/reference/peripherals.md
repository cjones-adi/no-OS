# Maxim Peripheral Configuration Details

Detailed peripheral configuration patterns, register access, and hardware-specific settings for Maxim platform drivers.

## SPI Peripheral Configuration

### Pin Configuration Selection

**Predefined Pin Sets**:
```c
// From maxim_spi.c - Different pin options per SPI instance
static mxc_gpio_cfg_t gpio_cfg_spi0_0;  // Standard SPI0 pins
static mxc_gpio_cfg_t gpio_cfg_spi0_1;  // Alternate SPI0 pins
static mxc_gpio_cfg_t gpio_cfg_spi1;    // SPI1 pins
static mxc_gpio_cfg_t gpio_cfg_spi1_ss; // SPI1 chip select

// Selection logic based on device_id and chip_select
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
```

### SPI Mode Configuration

**CPOL/CPHA Settings**:
```c
// Set SPI mode after initialization
ret = MXC_SPI_SetMode(MXC_SPI_GET_SPI(desc->device_id), desc->mode);

// Supported modes (from no-os framework)
NO_OS_SPI_MODE_0  // CPOL=0, CPHA=0
NO_OS_SPI_MODE_1  // CPOL=0, CPHA=1
NO_OS_SPI_MODE_2  // CPOL=1, CPHA=0
NO_OS_SPI_MODE_3  // CPOL=1, CPHA=1
```

### Data Width and Size

```c
// Set data width (standard/dual/quad)
ret = MXC_SPI_SetWidth(MXC_SPI_GET_SPI(desc->device_id), SPI_WIDTH_STANDARD);

// Available widths
SPI_WIDTH_STANDARD  // Standard SPI (MOSI + MISO)
SPI_WIDTH_DUAL      // Dual SPI (2-bit data)
SPI_WIDTH_QUAD      // Quad SPI (4-bit data)

// Set data size (bits per transfer)
ret = MXC_SPI_SetDataSize(MXC_SPI_GET_SPI(desc->device_id), 8);
// Typically 8-bit for most devices
```

### CS Polarity

```c
struct max_spi_init_param {
    mxc_spi_tscontrol_t polarity;  // SS polarity
};

// Available polarities
MXC_SPI_TSCONTROL_ACTIVE_LO   // CS active low (standard)
MXC_SPI_TSCONTROL_ACTIVE_HI   // CS active high
```

### DMA Priority Configuration

**Critical Requirement**: RX DMA priority must be higher (lower number) than TX DMA

```c
struct max_spi_init_param {
    uint8_t dma_tx_priority;  // Lower priority (higher number)
    uint8_t dma_rx_priority;  // Higher priority (lower number)
};

// Validation in init
if (eparam->dma_rx_priority >= eparam->dma_tx_priority)
    return -EINVAL;  // Invalid priority ordering

// Example configuration
struct max_spi_init_param spi_extra = {
    .dma_tx_priority = 2,  // Lower priority
    .dma_rx_priority = 1,  // Higher priority
};
```

**Why RX Higher Priority?**:
- Prevents RX FIFO overflow in full-duplex transfers
- TX can wait, RX data will be lost if not serviced
- Standard pattern across all Maxim platforms

## I2C Peripheral Configuration

### Speed Mode Selection

**Automatic Speed Selection**:
```c
// Driver selects closest supported speed
if (param->max_speed_hz <= MAX_I2C_STD_MODE)
    desc->max_speed_hz = MAX_I2C_STD_MODE;        // 100 kHz
else if (param->max_speed_hz <= MAX_I2C_FAST_MODE)
    desc->max_speed_hz = MAX_I2C_FAST_MODE;       // 400 kHz
else if (param->max_speed_hz <= MAX_I2C_FAST_PLUS_MODE)
    desc->max_speed_hz = MAX_I2C_FAST_PLUS_MODE;  // 1 MHz
else
    desc->max_speed_hz = MAX_I2C_HS_MODE;         // 3.4 MHz

// Set frequency
MXC_I2C_SetFrequency(i2c_regs, desc->max_speed_hz);
```

**Speed Guidelines**:
- **Standard Mode (100 kHz)**: Default, most compatible
- **Fast Mode (400 kHz)**: Common for sensors, safe default
- **Fast Plus (1 MHz)**: Check device datasheet support
- **High Speed (3.4 MHz)**: Rarely used, check compatibility

### Pin Configuration

```c
static void _max_i2c_pins_config(uint8_t device_id, mxc_gpio_vssel_t vssel)
{
    mxc_gpio_cfg_t i2c_pins;

    // Get pin configuration for I2C instance
    switch (device_id) {
    case 0:
        i2c_pins = gpio_cfg_i2c0;
        break;
    case 1:
        i2c_pins = gpio_cfg_i2c1;
        break;
    case 2:
        i2c_pins = gpio_cfg_i2c2;
        break;
    }

    // Apply voltage selection
    i2c_pins.vssel = vssel;

    // Configure pins
    MXC_GPIO_Config(&i2c_pins);
}
```

### Multi-Descriptor Pattern

**Shared I2C Peripheral**:
```c
// Global tracking (one per I2C instance)
static uint8_t nb_created_desc[MXC_I2C_INSTANCES] = {0};

// First descriptor initializes
if (nb_created_desc[param->device_id] == 0) {
    MXC_I2C_Shutdown(max_i2c->handler);
    MXC_I2C_Init(i2c_regs, I2C_MASTER_MODE, 0);
}
nb_created_desc[param->device_id]++;

// Example: Two devices on same bus
struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,
    .slave_address = 0x48,  // First device
};
no_os_i2c_init(&i2c_sensor1, &i2c_init);

i2c_init.slave_address = 0x76;  // Second device
no_os_i2c_init(&i2c_sensor2, &i2c_init);
// Both share same I2C0 peripheral
```

## UART Peripheral Configuration

### Flow Control Settings

```c
enum max_uart_flow_ctrl {
    MAX_UART_FLOW_DIS,   // No flow control (default)
    UART_FLOW_LOW,       // CTS/RTS active low
    UART_FLOW_HIGH,      // CTS/RTS active high
};

struct max_uart_init_param {
    enum max_uart_flow_ctrl flow;
    mxc_gpio_vssel_t vssel;
};

// Example: RS232 with hardware flow control
struct max_uart_init_param uart_extra = {
    .flow = UART_FLOW_LOW,              // RTS/CTS active low
    .vssel = MXC_GPIO_VSSEL_VDDIOH,     // 3.3V for RS232
};
```

### FIFO Configuration

**FIFO Depth**:
```c
#define MXC_UART_FIFO_DEPTH  // Device-specific (typically 8 or 32)

// FIFO used for async RX
struct no_os_uart_init_param uart_init = {
    .asynchronous_rx = true,  // Enable RX FIFO
};
```

**Write with FIFO Management**:
```c
static int32_t max_uart_write(struct no_os_uart_desc *desc,
                              const uint8_t *data, uint32_t bytes_number)
{
    uint32_t transfered = 0;

    while (bytes_number) {
        // Break into FIFO-sized chunks
        int block_size = no_os_min(MXC_UART_FIFO_DEPTH, bytes_number);

        // Wait for TX FIFO empty
        while (!(MXC_UART_GetStatus(MXC_UART_GET_UART(desc->device_id)) &
                 MXC_F_UART_STAT_TX_EMPTY));

        // Write block to FIFO
        MXC_UART_Write(MXC_UART_GET_UART(desc->device_id),
                      (uint8_t *)(data + transfered), &block_size);

        transfered += block_size;
        bytes_number -= block_size;
    }

    return transfered;
}
```

### Baud Rate Configuration

```c
// Baud rates automatically configured by HAL
struct no_os_uart_init_param uart_init = {
    .baud_rate = 115200,  // Standard rates supported
};

// Common baud rates
9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600
```

## GPIO Configuration

### Pull Resistor Mapping

```c
// Map no-OS pull configuration to Maxim HAL
switch (param->pull) {
case NO_OS_PULL_NONE:
    m_pad = MXC_GPIO_PAD_NONE;
    break;
case NO_OS_PULL_UP:
    m_pad = MXC_GPIO_PAD_WEAK_PULL_UP;   // ~40kΩ
    break;
case NO_OS_PULL_DOWN:
    m_pad = MXC_GPIO_PAD_WEAK_PULL_DOWN; // ~40kΩ
    break;
}
```

### Pin Configuration

```c
mxc_gpio_cfg_t g_cfg;

g_cfg.port = MXC_GPIO_GET_GPIO(param->port);  // Port number
g_cfg.mask = NO_OS_BIT(param->number);        // Pin mask
g_cfg.pad = m_pad;                            // Pull config
g_cfg.func = MXC_GPIO_FUNC_IN;                // Start as input
g_cfg.vssel = pextra->vssel;                  // Voltage level

// Initialize port and configure pin
MXC_GPIO_Init(param->port);
MXC_GPIO_Config(&g_cfg);
```

### Register Access for Performance

**Direct Register Operations**:
```c
// Enable/disable pin (output enable)
static void set_enable(mxc_gpio_regs_t *regs, uint32_t mask, uint8_t is_enabled)
{
    if (is_enabled)
        regs->en |= mask;
    else
        regs->en &= ~mask;
}

// Set/clear output
static void set_output(mxc_gpio_regs_t *regs, uint32_t mask, uint8_t value)
{
    if (value)
        regs->out_set = mask;  // Atomic set
    else
        regs->out_clr = mask;  // Atomic clear
}

// Read input
static uint8_t get_input(mxc_gpio_regs_t *regs, uint32_t mask)
{
    return !!(regs->in & mask);
}
```

**Why Direct Access?**:
- HAL calls have overhead
- Direct register access is faster
- Atomic set/clear registers prevent race conditions
- Common pattern for high-speed GPIO toggling

## Timer/PWM Configuration

### Prescaler Calculation

**Prescaler Selection Logic**:
```c
static int _get_prescaler(uint32_t div, mxc_tmr_pres_t *prescaler)
{
    if (div > 4096)
        return -EINVAL;

    // Binary search for closest prescaler
    if (div < 2)
        *prescaler = TMR_PRES_1;
    else if (div < 4)
        *prescaler = TMR_PRES_2;
    else if (div < 8)
        *prescaler = TMR_PRES_4;
    // ... continues through all power-of-2 values ...
    else
        *prescaler = TMR_PRES_4096;

    return 0;
}
```

**Available Prescalers**:
- 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096
- All power-of-2 values
- Max divider = 4096

### Timer Frequency Calculation

```c
// Timer frequency
uint32_t clk_div = SOURCE_CLOCK_FREQ / param->freq_hz;
_get_prescaler(clk_div, &prescaler);

// Example: 1kHz timer from 96MHz clock
// clk_div = 96,000,000 / 1,000 = 96,000
// Prescaler = 4096 (closest power of 2)
// Actual freq = 96MHz / 4096 = 23.4kHz base
// Compare value = 23.4kHz / 1kHz = 23
```

### PWM Period and Duty Cycle

```c
// Period calculation
uint32_t div = PeripheralClock / NO_OS_DIV_ROUND_CLOSEST_ULL(NANO, period_ns);
_get_prescaler(div, &prescaler);

uint32_t period_ticks = PeripheralClock / (
    NO_OS_DIV_ROUND_CLOSEST_ULL(NANO, period_ns) *
    MAX_PWM_PRESCALER_TRUE(prescaler)
);

// Duty cycle (percentage 0-100)
uint32_t duty_ticks = (period_ticks * duty_cycle) / 100;

// Configure timer
cfg.pres = prescaler;
cfg.cmp_cnt = period_ticks;
cfg.pol = 1;  // Polarity
```

## DMA Configuration

### Channel Allocation

```c
// Configure channels during init
for (i = 0; i < param->num_ch; i++) {
    descriptor->channels[i].id = i;
    descriptor->channels[i].irq_num = max_dma_get_irq(descriptor->id, i);
    descriptor->channels[i].extra = (void *)&MAX_DMA->ch[i];
    descriptor->channels[i].free = true;  // Initially free
}
```

### Acquire/Release Pattern

```c
// Acquire channel
struct no_os_dma_ch *tx_ch;
ret = no_os_dma_acquire_channel(max_spi->dma, &tx_ch);

// Use channel
// ... configure and start transfer ...

// Release channel
ret = no_os_dma_release_channel(max_spi->dma, tx_ch);
```

### DMA Request Signal Mapping

**Request Signals Per Peripheral**:
```c
// SPI request signals
MXC_V_DMA_CFG_REQSEL_SPI0TX
MXC_V_DMA_CFG_REQSEL_SPI0RX
MXC_V_DMA_CFG_REQSEL_SPI1TX
MXC_V_DMA_CFG_REQSEL_SPI1RX

// UART request signals
MXC_V_DMA_CFG_REQSEL_UART0TX
MXC_V_DMA_CFG_REQSEL_UART0RX
MXC_V_DMA_CFG_REQSEL_UART1TX
MXC_V_DMA_CFG_REQSEL_UART1RX

// I2C request signals
MXC_V_DMA_CFG_REQSEL_I2C0TX
MXC_V_DMA_CFG_REQSEL_I2C0RX
```

### FIFO Clear Before Transfer

```c
// Clear FIFOs before DMA transfer
spi->dma |= MXC_F_SPI_DMA_RX_FIFO_CLEAR | MXC_F_SPI_DMA_TX_FIFO_CLEAR;

// Enable FIFOs
spi->dma |= MXC_F_SPI_DMA_TX_FIFO_EN | MXC_F_SPI_DMA_RX_FIFO_EN;

// Enable DMA
spi->dma |= MXC_F_SPI_DMA_RX_DMA_EN | MXC_F_SPI_DMA_TX_DMA_EN;
```

## Interrupt Configuration

### GPIO External Interrupts

**Interrupt Triggers**:
```c
typedef enum {
    MXC_GPIO_INT_LEVEL,      // Level triggered
    MXC_GPIO_INT_EDGE,       // Edge triggered
} mxc_gpio_int_mode_t;

typedef enum {
    MXC_GPIO_INT_FALLING,    // Falling edge
    MXC_GPIO_INT_RISING,     // Rising edge
    MXC_GPIO_INT_BOTH,       // Both edges
    MXC_GPIO_INT_LOW,        // Low level
    MXC_GPIO_INT_HIGH,       // High level
} mxc_gpio_int_pol_t;
```

**Configuration**:
```c
// Configure interrupt
MXC_GPIO_IntConfig(port, mask, MXC_GPIO_INT_EDGE, MXC_GPIO_INT_RISING);

// Enable interrupt
MXC_GPIO_EnableInt(port, mask);

// Clear flag
MXC_GPIO_ClearFlags(port, mask);
```

### Interrupt Handler Chain

**GPIO IRQ Handlers**:
```c
void GPIO0_IRQHandler() {
    MXC_GPIO_Handler(0);  // HAL handler
}

void GPIO1_IRQHandler() {
    MXC_GPIO_Handler(1);
}
```

**Callback Registration**:
```c
// Register callback for specific pin
MXC_GPIO_RegisterCallback(port, pin, gpio_irq_callback, context);
```

## Common Use Cases

### SPI with DMA for High-Speed Transfers

```c
struct max_spi_init_param spi_extra = {
    .num_slaves = 1,
    .polarity = MXC_SPI_TSCONTROL_ACTIVE_LO,
    .vssel = MXC_GPIO_VSSEL_VDDIO,
    .dma_param = &dma_init,
    .dma_tx_priority = 2,   // Lower priority
    .dma_rx_priority = 1,   // Higher priority
};

struct no_os_spi_init_param spi_init = {
    .device_id = 0,
    .max_speed_hz = 10000000,  // 10 MHz
    .mode = NO_OS_SPI_MODE_0,
    .extra = &spi_extra,
    .platform_ops = &max_spi_ops,
};

ret = no_os_spi_init(&spi, &spi_init);
```

### I2C Multi-Device Bus

```c
struct max_i2c_init_param i2c_extra = {
    .vssel = MXC_GPIO_VSSEL_VDDIO,
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 0,
    .max_speed_hz = 400000,  // Fast mode
    .slave_address = 0x48,
    .extra = &i2c_extra,
    .platform_ops = &max_i2c_ops,
};

// Multiple descriptors share same I2C peripheral
ret = no_os_i2c_init(&i2c_sensor1, &i2c_init);

i2c_init.slave_address = 0x76;
ret = no_os_i2c_init(&i2c_sensor2, &i2c_init);
```

### UART with Async RX

```c
struct max_uart_init_param uart_extra = {
    .flow = MAX_UART_FLOW_DIS,
    .vssel = MXC_GPIO_VSSEL_VDDIOH,  // 3.3V for RS232
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .asynchronous_rx = true,  // Enable async RX with FIFO
    .extra = &uart_extra,
    .platform_ops = &max_uart_ops,
};

ret = no_os_uart_init(&uart, &uart_init);

// Non-blocking read from FIFO
uint8_t buffer[64];
ret = no_os_uart_read(uart, buffer, 64);
if (ret == -EAGAIN) {
    // No data available yet
}
```

## Device-Specific Variations

### MAX32690 Dual-DMA Support

```c
#ifdef MXC_DMA1
    // MAX32690 has two DMA controllers
    if (param->id == 1) {
        MAX_DMA = MXC_DMA1;  // Use second DMA
    } else {
        MAX_DMA = MXC_DMA0;  // Use first DMA
    }
#else
    // Single DMA controller
    MAX_DMA = MXC_DMA0;
#endif
```

### MAX78000 AI Accelerator Considerations

```c
#if TARGET_NUM == 78000
    // MAX78000-specific configuration
    // Consider power domains for CNN
    // May need different clock configuration
#endif
```

### Family-Specific Pin Counts

```c
#define N_PINS  MXC_CFG_GPIO_PINS_PORT   // Varies by family
#define N_PORTS MXC_CFG_GPIO_INSTANCES   // Varies by family

// MAX32650: 32 pins/port, 3 ports
// MAX32660: 32 pins/port, 1 port
// MAX32690: 32 pins/port, 4 ports
```
