---
name: no-os-stm32-platform
description: 'Complete guide to STM32 platform drivers for no-OS embedded systems. Covers HAL library integration, SPI/I2C/UART/GPIO/Timer drivers, DMA configuration, RCC clock management, GPIO alternate functions, NVIC interrupt handling, and family-specific patterns across STM32F1/F2/F4/F7/H7/L1/L4/G4/U5/H5.'
---

# no-OS STM32 Platform Drivers

Quick-start guide for developing STM32 platform drivers in the no-OS framework using STM32 HAL library across 10+ STM32 families.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/platform-apis.md**:
- User asks: "how to implement", "SPI driver", "I2C driver", "UART driver"
- Questions about: HAL API usage, descriptor structures, peripheral initialization
- Need: complete API implementations, configuration examples, handle management
- Mentions: HAL_SPI_Init, HAL_I2C_Init, HAL_UART_Init, peripheral APIs

**Triggers to read reference/initialization.md**:
- User asks: "how to initialize", "clock setup", "peripheral init sequence"
- Questions about: RCC clocks, GPIO alternate functions, instance mapping
- Need: complete initialization sequences, clock configuration, family-specific init
- Mentions: __HAL_RCC, HAL_RCC_GetPCLK, device_id mapping, static handles

**Triggers to read reference/peripherals.md**:
- User asks: "peripheral configuration", "family differences", "what instances"
- Questions about: supported peripherals by family, configuration parameters
- Need: peripheral availability tables, configuration options, family comparison
- Mentions: STM32F4 vs STM32H7, peripheral instances, timing registers

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "how should I", "correct way", "recommendations"
- Questions about: HAL usage patterns, clock management, GPIO AF, error handling
- Need: coding guidelines, do's and don'ts, portability practices
- Implementation questions: "should I use", "is it better to"

**Triggers to read reference/troubleshooting.md**:
- Build/runtime errors in user output
- User says: "doesn't work", "error", "not responding", "build fails"
- Specific issues: peripheral not working, clock issues, GPIO not toggling
- Questions about: debugging techniques, HAL errors, register inspection
- Mentions: HAL_ERROR, HAL_BUSY, NACK, timeout, segfault

---

## When to Use This Skill

- Implementing STM32 platform drivers (SPI, I2C, UART, GPIO, Timer, PWM, DMA)
- Configuring STM32 HAL library for no-OS framework
- Managing RCC clocks and GPIO alternate functions
- Handling NVIC interrupts and HAL callbacks
- Supporting multiple STM32 families (F1/F2/F4/F7/H7/L1/L4/G4/U5/H5)
- Debugging STM32 peripheral issues

## STM32 Platform Overview

```
┌──────────────────────────────────────────────────────────┐
│            no-OS STM32 Platform Architecture             │
└──────────────────────────────────────────────────────────┘

         ┌────────────────────────────────┐
         │   no-OS Generic Interface      │
         │  (no_os_spi, no_os_i2c, etc.)  │
         └────────────┬───────────────────┘
                      │
         ┌────────────▼───────────────────┐
         │   STM32 Platform Drivers       │
         │  (stm32_spi, stm32_i2c, etc.)  │
         └────────────┬───────────────────┘
                      │
         ┌────────────▼───────────────────┐
         │      STM32 HAL Library         │
         │  (HAL_SPI_*, HAL_I2C_*, etc.)  │
         └────────────┬───────────────────┘
                      │
         ┌────────────▼───────────────────┐
         │   STM32 Hardware Peripherals   │
         │  (SPI1-6, I2C1-4, USART1-6)    │
         └────────────────────────────────┘

Supported Families:
  Cortex-M3/M4:  F1, F2, F4, F7, L1, L4, G4
  Cortex-M7/M33: H7, H5, U5
```

---

## Quick Reference

### Common Driver Locations

```
drivers/platform/stm32/
├── stm32_hal.c/h          # HAL initialization
├── stm32_spi.c/h          # SPI driver
├── stm32_i2c.c/h          # I2C driver
├── stm32_uart.c/h         # UART driver
├── stm32_gpio.c/h         # GPIO configuration
├── stm32_timer.c/h        # Timer/counter
├── stm32_pwm.c/h          # PWM generation
├── stm32_dma.c/h          # DMA controller
├── stm32_irq.c/h          # NVIC interrupt handling
└── stm32_gpio_irq.c/h     # GPIO external interrupts
```

### Platform Operations Structure

```c
const struct no_os_spi_platform_ops stm32_spi_ops = {
    .init = &stm32_spi_init,
    .write_and_read = &stm32_spi_write_and_read,
    .remove = &stm32_spi_remove
};

const struct no_os_i2c_platform_ops stm32_i2c_ops = {
    .init = &stm32_i2c_init,
    .write = &stm32_i2c_write,
    .read = &stm32_i2c_read,
    .remove = &stm32_i2c_remove
};
```

### Peripheral Instances by Family

| Peripheral | STM32F4 | STM32H7 | STM32L4 |
|------------|---------|---------|---------|
| SPI        | 1-3     | 1-6     | 1-3     |
| I2C        | 1-3     | 1-4     | 1-4     |
| USART      | 1-6     | 1-6     | 1-3     |
| UART       | 4-5     | 4-8     | 4-5     |
| TIM        | 1-14    | 1-17    | 1-17    |
| GPIO       | A-I     | A-K     | A-H     |

---

## Essential Patterns

### 1. SPI Initialization

```c
struct stm32_spi_init_param spi_extra = {
    .input_clock = 100000000,  // APB2 clock (STM32H7)
    .alternate = GPIO_AF5_SPI1,
};

struct no_os_spi_init_param spi_init = {
    .device_id = 1,            // SPI1
    .max_speed_hz = 10000000,  // 10 MHz
    .mode = NO_OS_SPI_MODE_0,
    .chip_select = 0,
    .extra = &spi_extra,
    .platform_ops = &stm32_spi_ops,
};

ret = no_os_spi_init(&spi, &spi_init);
```

### 2. I2C Initialization (STM32H7/L4/U5 - Timing Register)

```c
// Use STM32CubeMX to calculate timing register
struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x00F07BFF,  // 400 kHz @ 200 MHz I2C clock
};

struct no_os_i2c_init_param i2c_init = {
    .device_id = 1,            // I2C1
    .max_speed_hz = 400000,
    .slave_address = 0x48,
    .extra = &i2c_extra,
    .platform_ops = &stm32_i2c_ops,
};

ret = no_os_i2c_init(&i2c, &i2c_init);
```

### 3. I2C Initialization (STM32F1/F2/F4/L1 - ClockSpeed)

```c
// Older families use ClockSpeed directly
struct no_os_i2c_init_param i2c_init = {
    .device_id = 1,            // I2C1
    .max_speed_hz = 400000,    // 400 kHz
    .slave_address = 0x48,
    .platform_ops = &stm32_i2c_ops,
    // No extra needed - HAL uses ClockSpeed
};

ret = no_os_i2c_init(&i2c, &i2c_init);
```

### 4. UART with Asynchronous RX

```c
struct no_os_uart_init_param uart_init = {
    .device_id = 1,            // UART1
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,   // Enable interrupt-driven RX
    .platform_ops = &stm32_uart_ops,
};

ret = no_os_uart_init(&uart, &uart_init);

// Non-blocking read from FIFO
uint8_t buffer[64];
ret = no_os_uart_read(uart, buffer, 64);
```

### 5. GPIO with Alternate Function

```c
struct stm32_gpio_init_param gpio_extra = {
    .alternate = GPIO_AF7_USART1,  // UART1 TX
};

struct no_os_gpio_init_param gpio_init = {
    .port = 0,                 // GPIOA
    .number = 9,               // PA9
    .pull = NO_OS_PULL_NONE,
    .extra = &gpio_extra,
    .platform_ops = &stm32_gpio_ops,
};

ret = no_os_gpio_get(&gpio_tx, &gpio_init);
ret = no_os_gpio_direction_output(gpio_tx, NO_OS_GPIO_HIGH);
```

---

## Key Concepts

### HAL Library Integration

**All drivers use STM32 HAL** (not LL):
- HAL_SPI_Init, HAL_I2C_Init, HAL_UART_Init for peripheral setup
- HAL callbacks for event-driven design
- HAL handle structures (SPI_HandleTypeDef, I2C_HandleTypeDef, etc.)

**Static handle management**:
```c
// Global static table for peripheral instances
static SPI_HandleTypeDef hspi_table[SPI_MAX_BUS_NUMBER + 1];

// Point to static handle during init
sdesc->hspi = &hspi_table[param->device_id];
```

### RCC Clock Management

**GPIO clocks** - Enable manually:
```c
__HAL_RCC_GPIOA_CLK_ENABLE();
__HAL_RCC_GPIOB_CLK_ENABLE();
```

**Peripheral clocks** - Enabled automatically by HAL_*_Init():
```c
HAL_SPI_Init(sdesc->hspi);   // Enables SPI clock
HAL_I2C_Init(&xdesc->hi2c);  // Enables I2C clock
```

**Query clock frequencies** dynamically:
```c
uint32_t apb1_freq = HAL_RCC_GetPCLK1Freq();  // TIM2-7, I2C, SPI2-3
uint32_t apb2_freq = HAL_RCC_GetPCLK2Freq();  // TIM1, SPI1, USART1
```

### GPIO Alternate Functions

**Check datasheet** for correct AF assignment:
```c
// STM32H7 examples
GPIO_AF4   // I2C
GPIO_AF5   // SPI
GPIO_AF7   // USART
GPIO_AF8   // UART4-8
```

**Configure before HAL_GPIO_Init**:
```c
extra->gpio_config.Alternate = pextra->alternate;
extra->gpio_config.Mode = GPIO_MODE_AF_PP;  // Alternate Function Push-Pull
HAL_GPIO_Init(extra->port, &extra->gpio_config);
```

### Family-Specific Configuration

**I2C timing** (varies by family):
```c
#if defined(STM32F4) || defined(STM32F1) || defined(STM32F2) || defined(STM32L1)
    // Older families: ClockSpeed parameter
    xdesc->hi2c.Init.ClockSpeed = param->max_speed_hz;
    xdesc->hi2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
#else
    // Newer families (H7, L4, U5): Timing register
    xdesc->hi2c.Init.Timing = i2cinit->i2c_timing;
#endif
```

**DMA configuration** (varies by family):
```c
#if defined(STM32F2) || defined(STM32F4) || defined(STM32F7)
    // F2/F4/F7: Channel in Init structure
    sdma_ch->hdma->Init.Channel = sdma_ch->ch_num;
#else
    // H7/U5: Channel in Instance
    sdma_ch->hdma->Instance = sdma_ch->ch_num;
#endif
```

---

## Common Use Cases

### SPI Communication

```c
// Initialize SPI
struct stm32_spi_init_param spi_extra = {
    .input_clock = HAL_RCC_GetPCLK2Freq(),  // Query dynamically
    .alternate = GPIO_AF5_SPI1,
};
no_os_spi_init(&spi, &spi_init);

// Write and read
uint8_t tx_data[4] = {0x01, 0x02, 0x03, 0x04};
uint8_t rx_data[4];
no_os_spi_write_and_read(spi, tx_data, 4);
```

### I2C Register Access

```c
// Initialize I2C (STM32H7)
struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x00F07BFF,  // From STM32CubeMX
};
no_os_i2c_init(&i2c, &i2c_init);

// Write register
uint8_t reg_addr = 0x10;
uint8_t reg_data = 0xAB;
no_os_i2c_write(i2c, &reg_addr, 1, 1);  // Write address
no_os_i2c_write(i2c, &reg_data, 1, 1);  // Write data

// Read register
no_os_i2c_write(i2c, &reg_addr, 1, 0);  // Write address (no stop)
no_os_i2c_read(i2c, &reg_data, 1, 1);   // Read data
```

### UART Communication

```c
// Initialize UART with async RX
no_os_uart_init(&uart, &uart_init);

// Blocking write
uint8_t msg[] = "Hello, STM32!\n";
no_os_uart_write(uart, msg, sizeof(msg) - 1);

// Non-blocking read (from interrupt FIFO)
uint8_t buffer[64];
uint32_t bytes_read;
no_os_uart_read(uart, buffer, 64);  // Returns available bytes
```

---

## Essential Quick Reference

### Common GPIO Alternate Functions (STM32H7)

| Peripheral | AF Number | Example Pins |
|------------|-----------|--------------|
| I2C        | AF4       | PB6(SCL), PB7(SDA) |
| SPI1       | AF5       | PA5(SCK), PA6(MISO), PA7(MOSI) |
| USART1     | AF7       | PA9(TX), PA10(RX) |
| UART4      | AF8       | PA0(TX), PA1(RX) |

### I2C Timing Register Examples (STM32H7 @ 200 MHz)

| Speed | Timing Register | Notes |
|-------|----------------|-------|
| 100 kHz | 0x307075B1 | Standard Mode |
| 400 kHz | 0x00F07BFF | Fast Mode |
| 1 MHz | 0x00702991 | Fast Mode Plus |

**Generate with**: STM32CubeMX → I2C Configuration → Timing Calculator

### SPI Prescaler Values

| Prescaler | Value | Example: 100 MHz → |
|-----------|-------|-------------------|
| /2        | SPI_BAUDRATEPRESCALER_2 | 50 MHz |
| /4        | SPI_BAUDRATEPRESCALER_4 | 25 MHz |
| /8        | SPI_BAUDRATEPRESCALER_8 | 12.5 MHz |
| /16       | SPI_BAUDRATEPRESCALER_16 | 6.25 MHz |
| /32       | SPI_BAUDRATEPRESCALER_32 | 3.125 MHz |

---

## Best Practices

1. **Use HAL for Abstraction**
   - Let HAL handle low-level details
   - Use HAL_*_Init() for peripheral setup
   - Leverage HAL callbacks for events

2. **Clock Management**
   - Enable GPIO clocks before configuration
   - Peripheral clocks enabled by HAL_*_Init()
   - Query frequencies with HAL_RCC_GetPCLK*Freq()

3. **GPIO Alternate Functions**
   - Check datasheet for correct AF assignment
   - Set alternate before HAL_GPIO_Init()
   - Use GPIO_MODE_AF_PP for AF mode

4. **I2C Timing (H7/L4/U5)**
   - Use STM32CubeMX timing calculator
   - Pre-calculate timing register values
   - Store in platform-specific init param

5. **Error Handling**
   - Check HAL_OK return values
   - Convert to standard errno codes (-EIO, -EINVAL, etc.)
   - Implement cleanup paths on error

6. **Family Portability**
   - Use conditional compilation (#if defined(STM32H7))
   - Test on multiple families
   - Abstract family-specific code

---

## Debugging Quick Start

### HAL Error Checking

```c
ret = HAL_SPI_Init(sdesc->hspi);
if (ret != HAL_OK) {
    pr_err("SPI init failed: %d\n", ret);
    // HAL_OK = 0, HAL_ERROR = 1, HAL_BUSY = 2, HAL_TIMEOUT = 3
    return -EIO;
}
```

### Clock Verification

```c
// Check peripheral clock enabled
if (!__HAL_RCC_SPI1_IS_CLK_ENABLED()) {
    pr_err("SPI1 clock not enabled\n");
}

// Check clock frequencies
uint32_t apb1 = HAL_RCC_GetPCLK1Freq();
uint32_t apb2 = HAL_RCC_GetPCLK2Freq();
pr_info("APB1: %u Hz, APB2: %u Hz\n", apb1, apb2);
```

### GPIO State Check

```c
// Read current pin state
GPIO_PinState state = HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_5);

// Check GPIO mode (0=IN, 1=OUT, 2=AF, 3=ANALOG)
uint32_t mode = (GPIOA->MODER >> (5 * 2)) & 0x3;
pr_info("PA5 mode: 0x%X\n", mode);
```

---

## Reference Documentation

**When to read each file** (use Read tool):

### reference/platform-apis.md
Complete HAL-based platform driver implementations: SPI, I2C, UART, GPIO, Timer, DMA, NVIC. Includes descriptor structures, initialization sequences, and usage examples.

### reference/initialization.md
Platform initialization sequences: RCC clock management, GPIO alternate function configuration, peripheral instance mapping, static handle management, complete init sequences.

### reference/peripherals.md
Peripheral configurations across STM32 families: supported instances, configuration parameters, family-specific differences, peripheral availability tables.

### reference/best-practices.md
STM32-specific best practices: HAL usage patterns, clock management, GPIO AF configuration, error handling, family portability, performance optimization.

### reference/troubleshooting.md
Common issues and debugging: HAL errors, clock issues, GPIO problems, I2C/SPI/UART debugging, DMA issues, interrupt debugging, register inspection.

---

## Summary

**Workflow**: Select family → Configure clocks → Initialize peripheral → Handle errors → Test on hardware

**Key Points**:
- **Use HAL** - Don't bypass HAL with direct register access
- **Enable GPIO clocks** - Before GPIO configuration
- **Check AF** - Verify alternate function in datasheet
- **I2C timing** - Use CubeMX calculator for H7/L4/U5
- **Family differences** - Use conditional compilation
- **Error handling** - Check HAL returns, convert to errno

**Tools**:
- **STM32CubeMX** - Clock configuration, I2C timing calculator
- **Datasheet** - GPIO alternate functions, peripheral specs
- **Reference Manual** - Peripheral register details
- **Logic Analyzer** - Signal debugging (SPI/I2C/UART)

**Result**: Portable, maintainable STM32 platform drivers supporting multiple families with proper HAL integration and error handling.
