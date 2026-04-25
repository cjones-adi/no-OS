# Complete Project Examples

Step-by-step examples for creating different types of no-OS projects from scratch.

## Example 1: Simple ADC Project

Complete walkthrough for creating a basic ADC project with single example.

### Step 1: Create Project Directory

```bash
cd projects
mkdir ad4692
cd ad4692
```

### Step 2: Create Makefile

```bash
cat > Makefile << 'EOF'
include ../../tools/scripts/generic_variables.mk

EXAMPLE ?= basic

include ../../tools/scripts/examples.mk
include src.mk
include ../../tools/scripts/generic.mk
EOF
```

### Step 3: Create src.mk

```bash
cat > src.mk << 'EOF'
# Device driver
INCS += $(DRIVERS)/adc/ad4692/ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/ad4692.c

# HAL abstractions
INCS += $(INCLUDE)/no_os_spi.h
INCS += $(INCLUDE)/no_os_gpio.h
INCS += $(INCLUDE)/no_os_uart.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_error.h

SRCS += $(DRIVERS)/api/no_os_spi.c
SRCS += $(DRIVERS)/api/no_os_gpio.c
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
SRCS += $(NO-OS)/util/no_os_util.c
EOF
```

### Step 4: Create builds.json

```bash
cat > builds.json << 'EOF'
{
  "maxim": {
    "basic_example_max32690": {
      "flags": "EXAMPLE=basic TARGET=max32690"
    }
  }
}
EOF
```

### Step 5: Create Directory Structure

```bash
mkdir -p src/common
mkdir -p src/examples/basic
mkdir -p src/platform/maxim
```

### Step 6: Create common_data.h

```bash
cat > src/common/common_data.h << 'EOF'
#ifndef __COMMON_DATA_H__
#define __COMMON_DATA_H__

#include "parameters.h"
#include "ad4692.h"
#include "no_os_uart.h"
#include "no_os_spi.h"
#include "no_os_gpio.h"

extern struct no_os_uart_init_param ad4692_uart_ip;
extern struct no_os_spi_init_param ad4692_spi_ip;
extern struct no_os_gpio_init_param ad4692_gpio_reset_ip;
extern struct ad4692_init_param ad4692_ip;

#endif
EOF
```

### Step 7: Create common_data.c

```bash
cat > src/common/common_data.c << 'EOF'
#include "common_data.h"

struct ad4692_init_param ad4692_ip = {
    .spi_ip = &ad4692_spi_ip,
    .gpio_reset = &ad4692_gpio_reset_ip,
    .ref_voltage = 5000,
    .device_id = ID_AD4692,
};

struct no_os_uart_init_param ad4692_uart_ip = {
    .device_id = UART_DEVICE_ID,
    .irq_id = UART_IRQ_ID,
    .baud_rate = UART_BAUDRATE,
    .platform_ops = UART_OPS,
    .extra = UART_EXTRA,
};

struct no_os_spi_init_param ad4692_spi_ip = {
    .device_id = SPI_DEVICE_ID,
    .max_speed_hz = SPI_BAUDRATE,
    .chip_select = SPI_CS,
    .mode = NO_OS_SPI_MODE_0,
    .platform_ops = SPI_OPS,
    .extra = SPI_EXTRA,
};

struct no_os_gpio_init_param ad4692_gpio_reset_ip = {
    .port = GPIO_RESET_PORT,
    .number = GPIO_RESET_PIN,
    .platform_ops = GPIO_OPS,
    .extra = GPIO_EXTRA,
};
EOF
```

### Step 8: Create Platform Files

**src/platform/maxim/parameters.h**:
```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "maxim_uart.h"
#include "maxim_spi.h"
#include "maxim_gpio.h"

#if (TARGET_NUM == 32690)
#define UART_DEVICE_ID   0
#define UART_IRQ_ID      UART0_IRQn
#define UART_BAUDRATE    115200
#define UART_OPS         &max_uart_ops
#define UART_EXTRA       &uart_extra_ip

#define SPI_DEVICE_ID    1
#define SPI_BAUDRATE     1000000
#define SPI_CS           0
#define SPI_OPS          &max_spi_ops
#define SPI_EXTRA        &spi_extra_ip

#define GPIO_RESET_PORT  0
#define GPIO_RESET_PIN   10
#define GPIO_OPS         &max_gpio_ops
#define GPIO_EXTRA       &gpio_extra_ip
#endif

extern struct max_uart_init_param uart_extra_ip;
extern struct max_spi_init_param spi_extra_ip;
extern struct max_gpio_init_param gpio_extra_ip;

#endif
```

**src/platform/maxim/parameters.c**:
```c
#include "parameters.h"

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

**src/platform/maxim/main.c**:
```c
#include "parameters.h"
#include "common_data.h"

extern int example_main();

int main(void)
{
    return example_main();
}
```

**src/platform/maxim/platform_src.mk**:
```makefile
INCS += $(PLATFORM_DRIVERS)/maxim_uart.h \
        $(PLATFORM_DRIVERS)/maxim_spi.h \
        $(PLATFORM_DRIVERS)/maxim_gpio.h

SRCS += $(PLATFORM_DRIVERS)/maxim_uart.c \
        $(PLATFORM_DRIVERS)/maxim_spi.c \
        $(PLATFORM_DRIVERS)/maxim_gpio.c \
        $(PLATFORM_DRIVERS)/maxim_delay.c
```

### Step 9: Create Example

**src/examples/basic/basic_example.c**:
```c
#include <stdio.h>
#include "ad4692.h"
#include "common_data.h"
#include "no_os_uart.h"
#include "no_os_print_log.h"
#include "no_os_util.h"

int example_main(void)
{
    struct ad4692_desc *dev;
    struct no_os_uart_desc *uart;
    int ret;
    uint32_t data;

    ret = no_os_uart_init(&uart, &ad4692_uart_ip);
    if (ret)
        return ret;

    no_os_uart_stdio(uart);
    pr_info("Starting AD4692 basic example\n");

    ret = ad4692_init(&dev, &ad4692_ip);
    if (ret) {
        pr_err("Init failed: %d\n", ret);
        goto error_uart;
    }

    while (1) {
        ret = ad4692_read_channel(dev, 0, &data);
        if (ret) {
            pr_err("Read failed: %d\n", ret);
            continue;
        }

        pr_info("Channel 0: %u\n", data);
        no_os_mdelay(1000);
    }

    ad4692_remove(dev);
error_uart:
    no_os_uart_remove(uart);
    return ret;
}
```

### Step 10: Build

```bash
make EXAMPLE=basic TARGET=max32690
```

---

## Example 2: Multi-Example IIO Project

Complete walkthrough for project with multiple examples (basic + IIO).

### Additional Steps Beyond Example 1

After completing Example 1, add IIO support:

### Create IIO Example Directory

```bash
mkdir -p src/examples/iio
```

### Create IIO Example Code

**src/examples/iio/iio_example.c**:
```c
#include <stdio.h>
#include "ad4692.h"
#include "iio_ad4692.h"
#include "common_data.h"
#include "no_os_uart.h"
#include "no_os_print_log.h"
#include "iio_app.h"

int example_main(void)
{
    struct ad4692_desc *dev;
    struct ad4692_iio_dev *iio_dev;
    struct no_os_uart_desc *uart;
    int ret;

    ret = no_os_uart_init(&uart, &ad4692_uart_ip);
    if (ret)
        return ret;

    no_os_uart_stdio(uart);
    pr_info("Starting AD4692 IIO example\n");

    ret = ad4692_init(&dev, &ad4692_ip);
    if (ret) {
        pr_err("Device init failed: %d\n", ret);
        goto error_uart;
    }

    struct ad4692_iio_init_param iio_init = {
        .dev = dev,
    };

    ret = ad4692_iio_init(&iio_dev, &iio_init);
    if (ret) {
        pr_err("IIO init failed: %d\n", ret);
        goto error_dev;
    }

    struct iio_app_desc *app;
    struct iio_app_init_param app_init = {
        .iio_devices = &iio_dev->iio_dev,
        .nb_devices = 1,
    };

    ret = iio_app_init(&app, &app_init);
    if (ret) {
        pr_err("IIO app init failed: %d\n", ret);
        goto error_iio;
    }

    pr_info("IIO server started\n");
    return iio_app_run(app);

error_iio:
    ad4692_iio_remove(iio_dev);
error_dev:
    ad4692_remove(dev);
error_uart:
    no_os_uart_remove(uart);
    return ret;
}
```

### Create IIO Example Configuration

**src/examples/iio/example.mk**:
```makefile
# Enable IIO daemon
IIOD = y

# Include IIO driver variant
INCS += $(DRIVERS)/adc/ad4692/iio_ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/iio_ad4692.c
```

### Update builds.json

```json
{
  "maxim": {
    "basic_example_max32690": {
      "flags": "EXAMPLE=basic TARGET=max32690"
    },
    "iio_example_max32690": {
      "flags": "EXAMPLE=iio TARGET=max32690"
    }
  }
}
```

### Build IIO Example

```bash
make EXAMPLE=iio TARGET=max32690
```

---

## Example 3: Multi-Platform Project

Building on Example 2, add Mbed platform support.

### Create Mbed Platform Directory

```bash
mkdir -p src/platform/mbed
```

### Create Mbed Platform Files

**src/platform/mbed/parameters.h**:
```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "mbed_uart.h"
#include "mbed_spi.h"
#include "mbed_gpio.h"

#define UART_DEVICE_ID   0
#define UART_BAUDRATE    115200
#define UART_OPS         &mbed_uart_ops
#define UART_EXTRA       &uart_extra_ip

#define SPI_DEVICE_ID    0
#define SPI_BAUDRATE     1000000
#define SPI_CS           SPI_CS_PIN
#define SPI_OPS          &mbed_spi_ops
#define SPI_EXTRA        &spi_extra_ip

#define GPIO_OPS         &mbed_gpio_ops
#define GPIO_EXTRA       NULL
#define GPIO_RESET_PIN   ARDUINO_UNO_D7

#define SPI_CS_PIN       ARDUINO_UNO_D10
#define SPI_MISO_PIN     ARDUINO_UNO_D12
#define SPI_MOSI_PIN     ARDUINO_UNO_D11
#define SPI_SCK_PIN      ARDUINO_UNO_D13

extern struct mbed_uart_init_param uart_extra_ip;
extern struct mbed_spi_init_param spi_extra_ip;

#endif
```

**src/platform/mbed/parameters.c**:
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

**src/platform/mbed/main.c**:
```c
#include "parameters.h"
#include "common_data.h"
#include <stdio.h>

extern int example_main();

int main()
{
    int ret;

    // Runtime platform configuration
    ad4692_ip.spi_ip = &ad4692_spi_ip;

    struct no_os_uart_desc* uart;
    ret = no_os_uart_init(&uart, &ad4692_uart_ip);
    if (ret)
        return ret;

    no_os_uart_stdio(uart);

    return example_main();
}
```

**src/platform/mbed/platform_src.mk**:
```makefile
INCS += $(PLATFORM_DRIVERS)/mbed_uart.h \
        $(PLATFORM_DRIVERS)/mbed_spi.h \
        $(PLATFORM_DRIVERS)/mbed_gpio.h

SRCS += $(PLATFORM_DRIVERS)/mbed_uart.cpp \
        $(PLATFORM_DRIVERS)/mbed_spi.cpp \
        $(PLATFORM_DRIVERS)/mbed_gpio.cpp \
        $(PLATFORM_DRIVERS)/mbed_delay.cpp
```

### Update builds.json

```json
{
  "maxim": {
    "basic_example_max32690": {
      "flags": "EXAMPLE=basic TARGET=max32690"
    },
    "iio_example_max32690": {
      "flags": "EXAMPLE=iio TARGET=max32690"
    }
  },
  "mbed": {
    "basic_example": {
      "flags": "RELEASE=y EXAMPLE=basic"
    },
    "iio_example": {
      "flags": "RELEASE=y EXAMPLE=iio"
    }
  }
}
```

### Build for Mbed

```bash
make PLATFORM=mbed EXAMPLE=basic RELEASE=y
make PLATFORM=mbed EXAMPLE=iio RELEASE=y
```

---

## Example 4: PMIC/Power Management Project

Complete example for I2C-based PMIC with regulator support.

### Project Structure

```
projects/max20370/
├── Makefile
├── builds.json
├── src.mk
└── src/
    ├── common/
    │   ├── common_data.c
    │   └── common_data.h
    ├── examples/
    │   ├── basic/
    │   │   └── basic_example.c
    │   └── regulator/
    │       └── regulator_example.c
    └── platform/
        └── maxim/
            ├── main.c
            ├── parameters.c
            ├── parameters.h
            └── platform_src.mk
```

### src.mk (I2C Device)

```makefile
# Device drivers
INCS += $(DRIVERS)/power/max20370/max20370.h
SRCS += $(DRIVERS)/power/max20370/max20370.c

INCS += $(DRIVERS)/power/max20370/max20370-regulator.h
SRCS += $(DRIVERS)/power/max20370/max20370-regulator.c

# Communication interfaces
INCS += $(INCLUDE)/no_os_i2c.h
SRCS += $(DRIVERS)/api/no_os_i2c.c

# Control interfaces
INCS += $(INCLUDE)/no_os_gpio.h
SRCS += $(DRIVERS)/api/no_os_gpio.c

INCS += $(INCLUDE)/no_os_irq.h
SRCS += $(DRIVERS)/api/no_os_irq.c

# Console
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
INCS += $(INCLUDE)/no_os_error.h
INCS += $(INCLUDE)/no_os_alloc.h
SRCS += $(NO-OS)/util/no_os_util.c
SRCS += $(NO-OS)/util/no_os_alloc.c
```

### common_data.h (I2C Device)

```c
#ifndef __COMMON_DATA_H__
#define __COMMON_DATA_H__

#include "parameters.h"
#include "max20370.h"
#include "no_os_uart.h"
#include "no_os_i2c.h"
#include "no_os_gpio.h"

extern struct no_os_uart_init_param max20370_uart_ip;
extern struct no_os_i2c_init_param max20370_i2c_ip;
extern struct no_os_gpio_init_param max20370_gpio_int_ip;
extern struct max20370_init_param max20370_ip;

#endif
```

### common_data.c (I2C Device)

```c
#include "common_data.h"

struct max20370_init_param max20370_ip = {
    .i2c_init = &max20370_i2c_ip,
    .int_gpio = &max20370_gpio_int_ip,
};

struct no_os_uart_init_param max20370_uart_ip = {
    .device_id = UART_DEVICE_ID,
    .irq_id = UART_IRQ_ID,
    .baud_rate = UART_BAUDRATE,
    .platform_ops = UART_OPS,
    .extra = UART_EXTRA,
};

struct no_os_i2c_init_param max20370_i2c_ip = {
    .device_id = I2C_DEVICE_ID,
    .max_speed_hz = I2C_BAUDRATE,
    .slave_address = MAX20370_I2C_ADDR,
    .platform_ops = I2C_OPS,
    .extra = I2C_EXTRA,
};

struct no_os_gpio_init_param max20370_gpio_int_ip = {
    .port = GPIO_INT_PORT,
    .number = GPIO_INT_PIN,
    .platform_ops = GPIO_OPS,
    .extra = GPIO_EXTRA,
};
```

### parameters.h (I2C Platform)

```c
#ifndef __PARAMETERS_H__
#define __PARAMETERS_H__

#include "maxim_uart.h"
#include "maxim_i2c.h"
#include "maxim_gpio.h"

#if (TARGET_NUM == 32690)
#define UART_DEVICE_ID   0
#define UART_IRQ_ID      UART0_IRQn
#define UART_BAUDRATE    115200
#define UART_OPS         &max_uart_ops
#define UART_EXTRA       &uart_extra_ip

#define I2C_DEVICE_ID    2
#define I2C_BAUDRATE     400000
#define I2C_OPS          &max_i2c_ops
#define I2C_EXTRA        &i2c_extra_ip

#define GPIO_OPS         &max_gpio_ops
#define GPIO_EXTRA       &gpio_extra_ip
#define GPIO_INT_PORT    0
#define GPIO_INT_PIN     20
#endif

extern struct max_uart_init_param uart_extra_ip;
extern struct max_i2c_init_param i2c_extra_ip;
extern struct max_gpio_init_param gpio_extra_ip;

#endif
```

### Example Application (Regulator Control)

**src/examples/regulator/regulator_example.c**:
```c
#include <stdio.h>
#include "max20370.h"
#include "max20370-regulator.h"
#include "common_data.h"
#include "no_os_uart.h"
#include "no_os_print_log.h"
#include "no_os_delay.h"

int example_main(void)
{
    struct max20370_dev *dev;
    struct no_os_uart_desc *uart;
    int ret;

    ret = no_os_uart_init(&uart, &max20370_uart_ip);
    if (ret)
        return ret;

    no_os_uart_stdio(uart);
    pr_info("MAX20370 Regulator Example\n");

    ret = max20370_init(&dev, &max20370_ip);
    if (ret) {
        pr_err("Device init failed: %d\n", ret);
        goto error_uart;
    }

    // Enable LDO0 at 3.3V
    ret = max20370_reg_enable(dev, MAX20370_LDO0);
    if (ret) {
        pr_err("LDO0 enable failed: %d\n", ret);
        goto error_dev;
    }

    ret = max20370_reg_set_voltage(dev, MAX20370_LDO0, 3300000);
    if (ret) {
        pr_err("Set voltage failed: %d\n", ret);
        goto error_dev;
    }

    pr_info("LDO0 enabled at 3.3V\n");

    while (1) {
        uint32_t voltage;
        ret = max20370_reg_get_voltage(dev, MAX20370_LDO0, &voltage);
        if (ret == 0)
            pr_info("LDO0 voltage: %u uV\n", voltage);

        no_os_mdelay(5000);
    }

error_dev:
    max20370_remove(dev);
error_uart:
    no_os_uart_remove(uart);
    return ret;
}
```

---

## Common Patterns Summary

### Minimal Project (Single Example, Single Platform)
- Makefile
- src.mk
- builds.json
- src/common/ (common_data.h/c)
- src/platform/maxim/ (4 files)
- src/examples/basic/ (example.c)

### Multi-Example Project
- Add src/examples/{example2}/
- Add example.mk if needed
- Update builds.json

### Multi-Platform Project
- Add src/platform/{platform2}/
- Same 4 files per platform
- Update builds.json

### Complex Multi-Device Project
- Multiple drivers in src.mk
- Multiple init params in common_data
- Potentially multiple examples
- Multiple platforms in builds.json
