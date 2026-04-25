# STM32 Peripheral Configurations

Complete reference for STM32 peripheral configurations across different families.

## Supported STM32 Families

### Cortex-M3/M4 Families

- **STM32F1** - Entry-level Cortex-M3
- **STM32F2** - Cortex-M3 with higher performance
- **STM32F4** - Cortex-M4F with DSP and FPU
- **STM32F7** - Cortex-M7 with cache
- **STM32L1** - Low-power Cortex-M3
- **STM32L4** - Low-power Cortex-M4F
- **STM32G4** - General purpose Cortex-M4F

### Cortex-M7/M33 Families

- **STM32H7** - High-performance Cortex-M7
- **STM32H5** - Newer high-performance
- **STM32U5** - Ultra-low power Cortex-M33

---

## SPI Peripheral Configuration

### Supported Instances by Family

| Family | Instances | Notes |
|--------|-----------|-------|
| STM32F1 | SPI1-SPI3 | Basic SPI |
| STM32F4 | SPI1-SPI3 | Standard SPI |
| STM32H7 | SPI1-SPI6 | Extended SPI support |
| STM32L4 | SPI1-SPI3 | Low-power SPI |

### SPI Configuration Parameters

```c
sdesc->hspi->Init.Mode = SPI_MODE_MASTER;
sdesc->hspi->Init.Direction = SPI_DIRECTION_2LINES;
sdesc->hspi->Init.DataSize = SPI_DATASIZE_8BIT;
sdesc->hspi->Init.CLKPolarity = (desc->mode & NO_OS_SPI_CPOL) ?
                                SPI_POLARITY_HIGH : SPI_POLARITY_LOW;
sdesc->hspi->Init.CLKPhase = (desc->mode & NO_OS_SPI_CPHA) ?
                             SPI_PHASE_2EDGE : SPI_PHASE_1EDGE;
sdesc->hspi->Init.NSS = SPI_NSS_SOFT;  // Software CS control
sdesc->hspi->Init.BaudRatePrescaler = prescaler;
sdesc->hspi->Init.FirstBit = desc->bit_order ?
                             SPI_FIRSTBIT_LSB : SPI_FIRSTBIT_MSB;
sdesc->hspi->Init.TIMode = SPI_TIMODE_DISABLE;
sdesc->hspi->Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
```

### SPI Prescaler Calculation

```c
uint32_t div = sdesc->input_clock / desc->max_speed_hz;
switch (div) {
case 0 ... 2:     prescaler = SPI_BAUDRATEPRESCALER_2;     break;
case 3 ... 4:     prescaler = SPI_BAUDRATEPRESCALER_4;     break;
case 5 ... 8:     prescaler = SPI_BAUDRATEPRESCALER_8;     break;
case 9 ... 16:    prescaler = SPI_BAUDRATEPRESCALER_16;    break;
case 17 ... 32:   prescaler = SPI_BAUDRATEPRESCALER_32;    break;
case 33 ... 64:   prescaler = SPI_BAUDRATEPRESCALER_64;    break;
case 65 ... 128:  prescaler = SPI_BAUDRATEPRESCALER_128;   break;
default:          prescaler = SPI_BAUDRATEPRESCALER_256;   break;
}
```

---

## I2C Peripheral Configuration

### Supported Instances by Family

| Family | Instances | Timing Method |
|--------|-----------|---------------|
| STM32F1 | I2C1-I2C2 | ClockSpeed |
| STM32F2 | I2C1-I2C3 | ClockSpeed |
| STM32F4 | I2C1-I2C3 | ClockSpeed |
| STM32H7 | I2C1-I2C4 | Timing register |
| STM32L4 | I2C1-I2C4 | Timing register |
| STM32U5 | I2C1-I2C4 | Timing register |

### I2C Configuration (Older Families: F1/F2/F4/L1)

```c
#if defined(STM32F4) || defined(STM32F1) || defined(STM32F2) || defined(STM32L1)
    xdesc->hi2c.Init.ClockSpeed = param->max_speed_hz;
    xdesc->hi2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
#endif
```

**ClockSpeed values**:
- 100000 - Standard Mode (100 kHz)
- 400000 - Fast Mode (400 kHz)
- 1000000 - Fast Mode Plus (1 MHz, if supported)

### I2C Configuration (Newer Families: H7/L4/U5/G4)

```c
#if !defined(STM32F4) && !defined(STM32F1) && !defined(STM32F2) && !defined(STM32L1)
    xdesc->hi2c.Init.Timing = i2cinit->i2c_timing;
#endif
```

**Timing register calculation**:
- Use STM32CubeMX I2C Timing Configuration tool
- Or use timing calculation formula from datasheet
- Pre-calculate and store in platform init param

**Example timing values (STM32H7 @ 200 MHz I2C clock)**:
```c
// 100 kHz Standard Mode
struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x307075B1,
};

// 400 kHz Fast Mode
struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x00F07BFF,
};

// 1 MHz Fast Mode Plus
struct stm32_i2c_init_param i2c_extra = {
    .i2c_timing = 0x00702991,
};
```

### I2C Common Parameters

```c
xdesc->hi2c.Init.OwnAddress1 = 0;
xdesc->hi2c.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
xdesc->hi2c.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
xdesc->hi2c.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
xdesc->hi2c.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
```

---

## UART Peripheral Configuration

### Supported Instances by Family

| Family | Instances | Notes |
|--------|-----------|-------|
| STM32F1 | USART1-USART3 | Basic UART |
| STM32F4 | USART1-USART6, UART4-UART5 | Mixed USART/UART |
| STM32H7 | USART1-USART6, UART4-UART8 | Extended UART |
| STM32L4 | USART1-USART3, UART4-UART5 | Low-power UART |

### UART Configuration Parameters

```c
sud->huart->Init.BaudRate = param->baud_rate;
sud->huart->Init.WordLength = UART_WORDLENGTH_8B;
sud->huart->Init.StopBits = UART_STOPBITS_1;
sud->huart->Init.Parity = UART_PARITY_NONE;
sud->huart->Init.Mode = UART_MODE_TX_RX;
sud->huart->Init.HwFlowCtl = UART_HWCONTROL_NONE;
sud->huart->Init.OverSampling = UART_OVERSAMPLING_16;
```

**Common baud rates**:
- 9600
- 19200
- 38400
- 57600
- 115200
- 230400
- 460800
- 921600

### UART Asynchronous RX

```c
if (param->asynchronous_rx) {
    // Initialize FIFO
    lf256fifo_init(&descriptor->rx_fifo);

    // Setup NVIC interrupt
    struct no_os_irq_init_param nvic_ip = {
        .platform_ops = &stm32_irq_ops,
        .extra = sud->huart,
    };
    no_os_irq_ctrl_init(&sud->nvic, &nvic_ip);

    // Register RX callback
    sud->rx_callback.callback = uart_rx_callback;
    sud->rx_callback.ctx = descriptor;
    sud->rx_callback.event = NO_OS_EVT_UART_RX_COMPLETE;
    sud->rx_callback.peripheral = NO_OS_UART_IRQ;
    sud->rx_callback.handle = sud->huart;

    no_os_irq_register_callback(sud->nvic, descriptor->irq_id,
                                &sud->rx_callback);
    no_os_irq_enable(sud->nvic, descriptor->irq_id);

    // Start async RX
    HAL_UART_Receive_IT(sud->huart, (uint8_t *)&c, 1);
}
```

---

## Timer Peripheral Configuration

### Supported Instances by Family

| Family | Instances | Notes |
|--------|-----------|-------|
| STM32F1 | TIM1-TIM14 | Basic timers |
| STM32F4 | TIM1-TIM14 | Advanced timers |
| STM32H7 | TIM1-TIM17 | Extended timers |
| STM32L4 | TIM1-TIM17 | Low-power timers |

### Timer APB Bus Assignment

**APB2 Timers** (High-speed):
- TIM1, TIM8, TIM9, TIM10, TIM11, TIM15, TIM16, TIM17

**APB1 Timers** (Standard):
- TIM2, TIM3, TIM4, TIM5, TIM6, TIM7, TIM12, TIM13, TIM14

### Timer Configuration

```c
htimer->Instance = TIM1/TIM2/TIM3...;
htimer->Init.Prescaler = sparam->prescaler;
htimer->Init.CounterMode = TIM_COUNTERMODE_UP;
htimer->Init.Period = period;
htimer->Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
htimer->Init.AutoReloadPreload = sparam->timer_autoreload ?
                                 TIM_AUTORELOAD_PRELOAD_ENABLE :
                                 TIM_AUTORELOAD_PRELOAD_DISABLE;
htimer->Init.RepetitionCounter = sparam->repetitions;
```

### PWM Configuration

```c
sConfigOC.OCMode = TIM_OCMODE_PWM1;
sConfigOC.Pulse = duty_cycle_ticks;
sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;

ret = HAL_TIM_PWM_ConfigChannel(htimer, &sConfigOC, channel);
ret = HAL_TIM_PWM_Start(htimer, channel);
```

**PWM channels**:
- TIM_CHANNEL_1
- TIM_CHANNEL_2
- TIM_CHANNEL_3
- TIM_CHANNEL_4

---

## GPIO Peripheral Configuration

### Supported Ports by Family

| Family | Ports | Count |
|--------|-------|-------|
| STM32F1 | GPIOA-GPIOG | 7 |
| STM32F4 | GPIOA-GPIOI | 9 |
| STM32H7 | GPIOA-GPIOK | 11 |
| STM32L4 | GPIOA-GPIOH | 8 |

### GPIO Modes

```c
GPIO_MODE_INPUT           // Digital input
GPIO_MODE_OUTPUT_PP       // Push-pull output
GPIO_MODE_OUTPUT_OD       // Open-drain output
GPIO_MODE_AF_PP           // Alternate function push-pull
GPIO_MODE_AF_OD           // Alternate function open-drain
GPIO_MODE_ANALOG          // Analog mode
GPIO_MODE_IT_RISING       // External interrupt rising edge
GPIO_MODE_IT_FALLING      // External interrupt falling edge
GPIO_MODE_IT_RISING_FALLING  // External interrupt both edges
```

### GPIO Speed

```c
GPIO_SPEED_FREQ_LOW       // Low speed (2-10 MHz)
GPIO_SPEED_FREQ_MEDIUM    // Medium speed (10-50 MHz)
GPIO_SPEED_FREQ_HIGH      // High speed (50-100 MHz)
GPIO_SPEED_FREQ_VERY_HIGH // Very high speed (100-180 MHz)
```

### GPIO Pull Configuration

```c
GPIO_NOPULL    // No pull-up or pull-down
GPIO_PULLUP    // Pull-up enabled
GPIO_PULLDOWN  // Pull-down enabled
```

### GPIO Configuration Example

```c
extra->gpio_config.Pin = NO_OS_BIT(param->number);
extra->gpio_config.Mode = GPIO_MODE_OUTPUT_PP;
extra->gpio_config.Speed = GPIO_SPEED_FREQ_LOW;
extra->gpio_config.Pull = GPIO_NOPULL;
extra->gpio_config.Alternate = 0;  // Not used for output

HAL_GPIO_Init(extra->port, &extra->gpio_config);
```

---

## DMA Peripheral Configuration

### DMA Architecture by Family

**STM32F2/F4/F7** - Stream-based DMA:
- DMA1: 8 streams
- DMA2: 8 streams
- Each stream has 8 channels
- Channel configured in Init structure

**STM32H7** - DMAMUX-based:
- DMA1/DMA2 with DMAMUX
- Flexible request routing
- Channel configured in Instance

**STM32U5/H5** - GPDMA:
- General Purpose DMA
- Linked-list mode
- Advanced features

### DMA Configuration (F2/F4/F7)

```c
#if defined(STM32F2) || defined(STM32F4) || defined(STM32F7)
    sdma_ch->hdma->Init.Channel = sdma_ch->ch_num;
    sdma_ch->hdma->Instance = DMA1_Stream0/DMA2_Stream0...;
#endif
```

### DMA Configuration (H7/U5/H5)

```c
#if !defined(STM32F2) && !defined(STM32F4) && !defined(STM32F7)
    sdma_ch->hdma->Instance = sdma_ch->ch_num;  // Channel in Instance
#endif
```

### DMA Transfer Configuration

```c
// Increment modes
sdma_ch->hdma->Init.MemInc = sdma_ch->mem_increment ?
                             DMA_MINC_ENABLE : DMA_MINC_DISABLE;
sdma_ch->hdma->Init.PeriphInc = sdma_ch->per_increment ?
                                DMA_PINC_ENABLE : DMA_PINC_DISABLE;

// Data alignment
sdma_ch->hdma->Init.MemDataAlignment = DMA_MDATAALIGN_BYTE/HALFWORD/WORD;
sdma_ch->hdma->Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE/HALFWORD/WORD;

// Transfer direction
sdma_ch->hdma->Init.Direction = DMA_MEMORY_TO_MEMORY;
sdma_ch->hdma->Init.Direction = DMA_MEMORY_TO_PERIPH;
sdma_ch->hdma->Init.Direction = DMA_PERIPH_TO_MEMORY;

// Mode
sdma_ch->hdma->Init.Mode = DMA_NORMAL;      // One-shot transfer
sdma_ch->hdma->Init.Mode = DMA_CIRCULAR;    // Continuous transfer

// Priority
sdma_ch->hdma->Init.Priority = DMA_PRIORITY_LOW;
sdma_ch->hdma->Init.Priority = DMA_PRIORITY_MEDIUM;
sdma_ch->hdma->Init.Priority = DMA_PRIORITY_HIGH;
sdma_ch->hdma->Init.Priority = DMA_PRIORITY_VERY_HIGH;
```

---

## Extended Peripherals

### Extended SPI (XSPI)

Available on STM32H7/U5/H5:
- Quad SPI (4-bit)
- Octo SPI (8-bit)
- Extended addressing modes
- Memory-mapped mode

### I3C

Available on newer families:
- I3C bus support
- Dynamic addressing
- In-band interrupts
- Higher speeds than I2C

### TDM Audio

Available on STM32H7:
- Time Division Multiplexing
- Multi-channel audio
- SAI peripheral

### USB Virtual COM Port

Available across families:
- CDC ACM class
- Virtual COM port over USB
- Alternative to hardware UART

---

## Directory Structure Reference

```
drivers/platform/stm32/
├── stm32_hal.c/h              # HAL initialization
├── stm32_spi.c/h              # SPI driver
├── stm32_i2c.c/h              # I2C driver
├── stm32_uart.c/h             # UART driver
├── stm32_gpio.c/h             # GPIO configuration
├── stm32_gpio_irq.c/h         # GPIO interrupts (EXTI)
├── stm32_timer.c/h            # Timer/counter
├── stm32_pwm.c/h              # PWM generation
├── stm32_dma.c/h              # DMA controller
├── stm32_irq.c/h              # NVIC management
├── stm32_delay.c              # Delay functions
├── stm32_i3c.c/h              # I3C protocol
├── stm32_xspi.c/h             # Extended SPI (Quad/Octo)
├── stm32_tdm.c/h              # TDM audio
└── stm32_usb_uart.c/h         # USB Virtual COM
```

---

## Peripheral Instance Summary

| Peripheral | STM32F1 | STM32F4 | STM32H7 | STM32L4 |
|------------|---------|---------|---------|---------|
| SPI        | 1-3     | 1-3     | 1-6     | 1-3     |
| I2C        | 1-2     | 1-3     | 1-4     | 1-4     |
| USART      | 1-3     | 1-6     | 1-6     | 1-3     |
| UART       | -       | 4-5     | 4-8     | 4-5     |
| TIM        | 1-14    | 1-14    | 1-17    | 1-17    |
| GPIO       | A-G     | A-I     | A-K     | A-H     |
| DMA        | 1-2     | 1-2     | 1-2+MUX | 1-2     |

---

## Common Header Files

```c
#include "stm32_hal.h"          // HAL initialization
#include "stm32_spi.h"          // SPI platform driver
#include "stm32_i2c.h"          // I2C platform driver
#include "stm32_uart.h"         // UART platform driver
#include "stm32_gpio.h"         // GPIO configuration
#include "stm32_timer.h"        // Timer/counter
#include "stm32_pwm.h"          // PWM generation
#include "stm32_dma.h"          // DMA controller
#include "stm32_irq.h"          // NVIC interrupt handling
#include "stm32_gpio_irq.h"     // GPIO external interrupts
```
