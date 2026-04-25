# Platform Integration Guide

Complete guide to platform-specific code organization for all supported platforms.

## Platform Files Overview

Each platform requires four files in `src/platform/{PLATFORM}/`:

1. **main.c** - Platform entry point
2. **parameters.h** - Hardware definitions and macros
3. **parameters.c** - Platform-specific structure initialization
4. **platform_src.mk** - Platform driver sources

## Maxim Platform

### Directory: src/platform/maxim/

### main.c (Maxim)

**Simple template**:
```c
#include <stdio.h>
#include "parameters.h"
#include "common_data.h"

// Externally linked from selected example
extern int example_main();

int main(void)
{
    return example_main();
}
```

### parameters.h (Maxim)

```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "maxim_irq.h"
#include "maxim_spi.h"
#include "maxim_gpio.h"
#include "maxim_uart.h"

// Platform detection
#if (TARGET_NUM == 32690)
    #define UART_IRQ_ID      UART0_IRQn
    #define UART_DEVICE_ID   0
    #define UART_BAUDRATE    115200
    #define UART_OPS         &max_uart_ops
    #define UART_EXTRA       &uart_extra_ip

    // SPI Configuration
    #define SPI_DEVICE_ID    1
    #define SPI_BAUDRATE     1000000
    #define SPI_CS           0
    #define SPI_OPS          &max_spi_ops
    #define SPI_EXTRA        &spi_extra_ip

    // GPIO Configuration
    #define GPIO_OPS         &max_gpio_ops
    #define GPIO_EXTRA       &gpio_extra_ip
    #define GPIO_RESET_PIN   10
    #define GPIO_RESET_PORT  0

#elif (TARGET_NUM == 32655)
    // Alternative target configuration
    #define UART_IRQ_ID      UART1_IRQn
    #define UART_DEVICE_ID   1
    #define UART_BAUDRATE    115200
    #define UART_OPS         &max_uart_ops
    #define UART_EXTRA       &uart_extra_ip

    #define SPI_DEVICE_ID    0
    #define SPI_BAUDRATE     1000000
    #define SPI_CS           0
    #define SPI_OPS          &max_spi_ops
    #define SPI_EXTRA        &spi_extra_ip

    #define GPIO_OPS         &max_gpio_ops
    #define GPIO_EXTRA       &gpio_extra_ip
    #define GPIO_RESET_PIN   8
    #define GPIO_RESET_PORT  1
#endif

// External declarations for platform extras
extern struct max_uart_init_param uart_extra_ip;
extern struct max_spi_init_param spi_extra_ip;
extern struct max_gpio_init_param gpio_extra_ip;

#endif /* __PARAMETERS_H__ */
```

### parameters.c (Maxim)

```c
#include "parameters.h"

// Platform-specific extras
struct max_uart_init_param uart_extra_ip = {
    .flow = UART_FLOW_DIS
};

struct max_spi_init_param spi_extra_ip = {
    .num_slaves = 1,
    .polarity = SPI_SS_POL_LOW,
    .vssel = MXC_GPIO_VSSEL_VDDIOH,
};

struct max_gpio_init_param gpio_extra_ip = {
    .vssel = MXC_GPIO_VSSEL_VDDIOH,
};
```

### platform_src.mk (Maxim)

```makefile
# Platform drivers from drivers/platform/maxim/
INCS += $(PLATFORM_DRIVERS)/maxim_gpio.h \
        $(PLATFORM_DRIVERS)/maxim_spi.h \
        $(PLATFORM_DRIVERS)/maxim_uart.h \
        $(PLATFORM_DRIVERS)/maxim_irq.h

SRCS += $(PLATFORM_DRIVERS)/maxim_gpio.c \
        $(PLATFORM_DRIVERS)/maxim_spi.c \
        $(PLATFORM_DRIVERS)/maxim_uart.c \
        $(PLATFORM_DRIVERS)/maxim_irq.c \
        $(PLATFORM_DRIVERS)/maxim_delay.c
```

**Common Maxim platform drivers**:
- `maxim_gpio.c/.h` - GPIO control
- `maxim_spi.c/.h` - SPI interface
- `maxim_i2c.c/.h` - I2C interface
- `maxim_uart.c/.h` - UART interface
- `maxim_irq.c/.h` - Interrupt handling
- `maxim_delay.c/.h` - Delay functions
- `maxim_pwm.c/.h` - PWM generation
- `maxim_timer.c/.h` - Timer control

---

## Mbed Platform

### Directory: src/platform/mbed/

### main.c (Mbed)

**Requires runtime platform configuration**:
```c
#include "parameters.h"
#include "common_data.h"
#include <stdio.h>

extern int example_main();

int main()
{
    int ret;

    // Runtime platform configuration (Mbed-specific)
    // Connect device init params to platform SPI
    ad4692_ip.spi_ip = &ad4692_spi_ip;

    // Initialize UART for stdio
    struct no_os_uart_desc* uart;
    ret = no_os_uart_init(&uart, &ad4692_uart_ip);
    if (ret)
        return ret;

    no_os_uart_stdio(uart);

    return example_main();
}
```

### parameters.h (Mbed)

```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "mbed_uart.h"
#include "mbed_spi.h"
#include "mbed_gpio.h"

// UART Configuration
#define UART_DEVICE_ID   0
#define UART_BAUDRATE    115200
#define UART_OPS         &mbed_uart_ops
#define UART_EXTRA       &uart_extra_ip

// SPI Configuration
#define SPI_DEVICE_ID    0
#define SPI_BAUDRATE     1000000
#define SPI_CS           SPI_CS_PIN
#define SPI_OPS          &mbed_spi_ops
#define SPI_EXTRA        &spi_extra_ip

// GPIO Configuration
#define GPIO_OPS         &mbed_gpio_ops
#define GPIO_EXTRA       NULL
#define GPIO_RESET_PIN   ARDUINO_UNO_D7

// Pin definitions (board-specific)
#define SPI_CS_PIN       ARDUINO_UNO_D10
#define SPI_MISO_PIN     ARDUINO_UNO_D12
#define SPI_MOSI_PIN     ARDUINO_UNO_D11
#define SPI_SCK_PIN      ARDUINO_UNO_D13

extern struct mbed_uart_init_param uart_extra_ip;
extern struct mbed_spi_init_param spi_extra_ip;

#endif /* __PARAMETERS_H__ */
```

### parameters.c (Mbed)

```c
#include "parameters.h"

struct mbed_uart_init_param uart_extra_ip = {
    .uart_tx_pin = CONSOLE_TX,
    .uart_rx_pin = CONSOLE_RX,
};

struct mbed_spi_init_param spi_extra_ip = {
    .spi_miso_pin = SPI_MISO_PIN,
    .spi_mosi_pin = SPI_MOSI_PIN,
    .spi_clk_pin = SPI_SCK_PIN,
    .use_sw_csb = false,
};
```

### platform_src.mk (Mbed)

```makefile
# Platform drivers from drivers/platform/mbed/
INCS += $(PLATFORM_DRIVERS)/mbed_uart.h \
        $(PLATFORM_DRIVERS)/mbed_spi.h \
        $(PLATFORM_DRIVERS)/mbed_gpio.h

SRCS += $(PLATFORM_DRIVERS)/mbed_uart.cpp \
        $(PLATFORM_DRIVERS)/mbed_spi.cpp \
        $(PLATFORM_DRIVERS)/mbed_gpio.cpp \
        $(PLATFORM_DRIVERS)/mbed_delay.cpp
```

**Common Mbed platform drivers**:
- `mbed_gpio.cpp/.h` - GPIO control
- `mbed_spi.cpp/.h` - SPI interface
- `mbed_i2c.cpp/.h` - I2C interface
- `mbed_uart.cpp/.h` - UART interface
- `mbed_irq.cpp/.h` - Interrupt handling
- `mbed_delay.cpp/.h` - Delay functions

**Note**: Mbed drivers use `.cpp` extension (C++).

---

## STM32 Platform

### Directory: src/platform/stm32/

### main.c (STM32)

```c
#include "parameters.h"
#include "common_data.h"

extern int example_main();

int main(void)
{
    // STM32 HAL initialization
    stm32_system_init();

    return example_main();
}
```

### parameters.h (STM32)

```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "stm32_uart.h"
#include "stm32_spi.h"
#include "stm32_gpio.h"

// UART Configuration
#define UART_DEVICE_ID   1
#define UART_BAUDRATE    115200
#define UART_OPS         &stm32_uart_ops
#define UART_EXTRA       &uart_extra_ip

// SPI Configuration
#define SPI_DEVICE_ID    1
#define SPI_BAUDRATE     1000000
#define SPI_CS           10
#define SPI_OPS          &stm32_spi_ops
#define SPI_EXTRA        &spi_extra_ip

// GPIO Configuration
#define GPIO_OPS         &stm32_gpio_ops
#define GPIO_EXTRA       NULL
#define GPIO_RESET_PORT  0   // GPIOA
#define GPIO_RESET_PIN   4

extern struct stm32_uart_init_param uart_extra_ip;
extern struct stm32_spi_init_param spi_extra_ip;

#endif
```

### parameters.c (STM32)

```c
#include "parameters.h"

struct stm32_uart_init_param uart_extra_ip = {
    .mode = UART_MODE_TX_RX,
    .hw_flow_ctl = UART_HWCONTROL_NONE,
    .over_sampling = UART_OVERSAMPLING_16,
};

struct stm32_spi_init_param spi_extra_ip = {
    .chip_select_port = 0,  // GPIOA
    .get_input_clock = HAL_RCC_GetPCLK2Freq,
};
```

### platform_src.mk (STM32)

```makefile
# Platform drivers
INCS += $(PLATFORM_DRIVERS)/stm32_gpio.h \
        $(PLATFORM_DRIVERS)/stm32_spi.h \
        $(PLATFORM_DRIVERS)/stm32_uart.h

SRCS += $(PLATFORM_DRIVERS)/stm32_gpio.c \
        $(PLATFORM_DRIVERS)/stm32_spi.c \
        $(PLATFORM_DRIVERS)/stm32_uart.c \
        $(PLATFORM_DRIVERS)/stm32_delay.c
```

---

## Xilinx Platform

### Directory: src/platform/xilinx/

### main.c (Xilinx)

```c
#include "parameters.h"
#include "common_data.h"
#include "xil_cache.h"

extern int example_main();

int main(void)
{
    #ifdef XPAR_XUARTNS550_NUM_INSTANCES
        Xil_ICacheEnable();
        Xil_DCacheEnable();
    #endif

    return example_main();
}
```

### parameters.h (Xilinx)

```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "xilinx_uart.h"
#include "xilinx_spi.h"
#include "xilinx_gpio.h"

// UART Configuration
#define UART_DEVICE_ID   XPAR_XUARTPS_0_DEVICE_ID
#define UART_BAUDRATE    115200
#define UART_OPS         &xil_uart_ops
#define UART_EXTRA       &uart_extra_ip

// SPI Configuration
#define SPI_DEVICE_ID    XPAR_SPI_0_DEVICE_ID
#define SPI_BAUDRATE     1000000
#define SPI_CS           0
#define SPI_OPS          &xil_spi_ops
#define SPI_EXTRA        &spi_extra_ip

// GPIO Configuration
#define GPIO_DEVICE_ID   XPAR_GPIO_0_DEVICE_ID
#define GPIO_OPS         &xil_gpio_ops
#define GPIO_EXTRA       &gpio_extra_ip
#define GPIO_RESET_PIN   54

extern struct xil_uart_init_param uart_extra_ip;
extern struct xil_spi_init_param spi_extra_ip;
extern struct xil_gpio_init_param gpio_extra_ip;

#endif
```

### parameters.c (Xilinx)

```c
#include "parameters.h"

struct xil_uart_init_param uart_extra_ip = {
    .type = UART_PS,
};

struct xil_spi_init_param spi_extra_ip = {
    .type = SPI_PS,
    .flags = 0,
};

struct xil_gpio_init_param gpio_extra_ip = {
    .type = GPIO_PS,
    .device_id = GPIO_DEVICE_ID,
};
```

### platform_src.mk (Xilinx)

```makefile
# Platform drivers
INCS += $(PLATFORM_DRIVERS)/xilinx_gpio.h \
        $(PLATFORM_DRIVERS)/xilinx_spi.h \
        $(PLATFORM_DRIVERS)/xilinx_uart.h

SRCS += $(PLATFORM_DRIVERS)/xilinx_gpio.c \
        $(PLATFORM_DRIVERS)/xilinx_spi.c \
        $(PLATFORM_DRIVERS)/xilinx_uart.c \
        $(PLATFORM_DRIVERS)/xilinx_delay.c
```

---

## Pico Platform

### Directory: src/platform/pico/

### main.c (Pico)

```c
#include "parameters.h"
#include "common_data.h"

extern int example_main();

int main(void)
{
    return example_main();
}
```

### parameters.h (Pico)

```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "pico_uart.h"
#include "pico_spi.h"
#include "pico_gpio.h"

// UART Configuration
#define UART_DEVICE_ID   0
#define UART_BAUDRATE    115200
#define UART_OPS         &pico_uart_ops
#define UART_EXTRA       &uart_extra_ip

// SPI Configuration
#define SPI_DEVICE_ID    0
#define SPI_BAUDRATE     1000000
#define SPI_CS           17
#define SPI_OPS          &pico_spi_ops
#define SPI_EXTRA        &spi_extra_ip

// GPIO Configuration
#define GPIO_OPS         &pico_gpio_ops
#define GPIO_EXTRA       NULL
#define GPIO_RESET_PIN   20

extern struct pico_uart_init_param uart_extra_ip;
extern struct pico_spi_init_param spi_extra_ip;

#endif
```

### parameters.c (Pico)

```c
#include "parameters.h"

struct pico_uart_init_param uart_extra_ip = {
    .uart_tx_pin = 0,
    .uart_rx_pin = 1,
};

struct pico_spi_init_param spi_extra_ip = {
    .spi_rx_pin = 16,
    .spi_tx_pin = 19,
    .spi_sck_pin = 18,
    .spi_cs_pin = SPI_CS,
};
```

### platform_src.mk (Pico)

```makefile
# Platform drivers
INCS += $(PLATFORM_DRIVERS)/pico_gpio.h \
        $(PLATFORM_DRIVERS)/pico_spi.h \
        $(PLATFORM_DRIVERS)/pico_uart.h

SRCS += $(PLATFORM_DRIVERS)/pico_gpio.c \
        $(PLATFORM_DRIVERS)/pico_spi.c \
        $(PLATFORM_DRIVERS)/pico_uart.c \
        $(PLATFORM_DRIVERS)/pico_delay.c
```

---

## Common Patterns Across Platforms

### parameters.h Pattern

All platforms follow this pattern:
```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

// Include platform-specific headers
#include "platform_uart.h"
#include "platform_spi.h"
#include "platform_gpio.h"

// Define macros for common_data.c to use
#define UART_DEVICE_ID   [platform_specific]
#define UART_BAUDRATE    115200
#define UART_OPS         &platform_uart_ops
#define UART_EXTRA       &uart_extra_ip

#define SPI_DEVICE_ID    [platform_specific]
#define SPI_BAUDRATE     1000000
#define SPI_CS           [platform_specific]
#define SPI_OPS          &platform_spi_ops
#define SPI_EXTRA        &spi_extra_ip

// Declare platform extras
extern struct platform_uart_init_param uart_extra_ip;
extern struct platform_spi_init_param spi_extra_ip;

#endif
```

### parameters.c Pattern

All platforms follow this pattern:
```c
#include "parameters.h"

// Define platform-specific extras
struct platform_uart_init_param uart_extra_ip = {
    // Platform-specific fields
};

struct platform_spi_init_param spi_extra_ip = {
    // Platform-specific fields
};
```

### platform_src.mk Pattern

All platforms follow this pattern:
```makefile
# Include platform-specific driver headers
INCS += $(PLATFORM_DRIVERS)/platform_gpio.h \
        $(PLATFORM_DRIVERS)/platform_spi.h \
        $(PLATFORM_DRIVERS)/platform_uart.h

# Include platform-specific driver sources
SRCS += $(PLATFORM_DRIVERS)/platform_gpio.c \
        $(PLATFORM_DRIVERS)/platform_spi.c \
        $(PLATFORM_DRIVERS)/platform_uart.c \
        $(PLATFORM_DRIVERS)/platform_delay.c
```

---

## Best Practices

### DO

- Keep main.c minimal (just call example_main)
- Use macros in parameters.h for all platform-specific values
- Define extras in parameters.c
- Include only needed platform drivers in platform_src.mk
- Support multiple targets via #if (TARGET_NUM == xxx)

### DON'T

- Put device logic in main.c
- Hardcode pin numbers in common_data.c
- Mix platform and device initialization
- Duplicate driver includes between src.mk and platform_src.mk
- Put application code in platform files

---

## Adding Multi-Platform Support

To add a new platform to an existing project:

1. Create directory: `mkdir -p src/platform/newplatform/`
2. Copy reference files from similar platform
3. Update parameters.h with platform-specific pin definitions
4. Update parameters.c with platform-specific extras
5. Update platform_src.mk with platform drivers
6. Update main.c if platform needs special initialization
7. Add build config to builds.json
8. Test build: `make PLATFORM=newplatform`

---

## Platform Selection

Platforms are auto-detected based on:
- `TARGET` variable (e.g., TARGET=max32690 → PLATFORM=maxim)
- Explicit `PLATFORM` variable
- Hardware files in project directory

Build examples:
```bash
make TARGET=max32690           # Auto-detects PLATFORM=maxim
make PLATFORM=mbed RELEASE=y   # Explicit platform
make PLATFORM=stm32            # Explicit platform
```
