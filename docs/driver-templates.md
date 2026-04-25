# Driver Implementation Templates

This document provides standard templates for no-OS driver development, following established patterns and conventions.

## Header File Template (`device_name.h`)

> **📝 Template Note**: Replace all `device_name` placeholders with your specific device name (e.g., `ltm4700.h`, `adm1275.c`). Follow Linux kernel principle: use explicit device names, never generic placeholders in actual code. **@author field should only contain human developer information** - never include AI attribution.

```c
/***************************************************************************//**
 *   @file   device_name.h
 *   @brief  Header file of DEVICE_NAME Driver.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright 2024(c) Analog Devices, Inc.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of Analog Devices, Inc. nor the names of its
 *    contributors may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES, INC. "AS IS" AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
 * EVENT SHALL ANALOG DEVICES, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
 * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*******************************************************************************/
#ifndef __DEVICE_NAME_H__
#define __DEVICE_NAME_H__

#include <stdint.h>
#include "no_os_spi.h"    // or no_os_i2c.h
#include "no_os_gpio.h"   // if GPIO pins used

/* Register definitions */
#define DEVICE_NAME_REG_EXAMPLE    0x00

/* Bit field definitions */
#define DEVICE_NAME_EXAMPLE_MSK    NO_OS_GENMASK(7, 0)
#define DEVICE_NAME_EXAMPLE(x)     no_os_field_prep(DEVICE_NAME_EXAMPLE_MSK, x)

/**
 * @struct device_name_dev
 * @brief Device driver handler.
 */
struct device_name_dev {
	/* Communication interface */
	struct no_os_spi_desc		*spi_desc;
	/* Optional GPIO pins */
	struct no_os_gpio_desc		*gpio_reset;
	/* Device configuration */
	uint8_t				device_id;
};

/**
 * @struct device_name_init_param
 * @brief Device initialization parameters.
 */
struct device_name_init_param {
	/* Communication interface */
	struct no_os_spi_init_param	spi_init;
	/* Optional GPIO pins */
	struct no_os_gpio_init_param	gpio_reset;
	/* Device configuration */
	uint8_t				device_id;
};

/* Initialize the device */
int32_t device_name_init(struct device_name_dev **device,
			 struct device_name_init_param init_param);

/* Remove resources allocated by device_name_init() */
int32_t device_name_remove(struct device_name_dev *dev);

/* Device-specific functions */
int32_t device_name_read_register(struct device_name_dev *dev,
				  uint8_t reg_addr,
				  uint8_t *reg_data);

int32_t device_name_write_register(struct device_name_dev *dev,
				   uint8_t reg_addr,
				   uint8_t reg_data);

#endif /* __DEVICE_NAME_H__ */
```

## Implementation File Template (`device_name.c`)

> **📝 Note**: @author field should only contain human developer information - never include AI attribution.

```c
/***************************************************************************//**
 *   @file   device_name.c
 *   @brief  Implementation of DEVICE_NAME Driver.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright 2024(c) Analog Devices, Inc.
 * [... same license text as header ...]
*******************************************************************************/

#include <stdlib.h>
#include <string.h>
#include "device_name.h"
#include "no_os_alloc.h"
#include "no_os_error.h"
#include "no_os_delay.h"

/**
 * @brief Initialize the device.
 *
 * @param device     - The device structure.
 * @param init_param - The structure that contains the device initial
 *                     parameters.
 *
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t device_name_init(struct device_name_dev **device,
			 struct device_name_init_param init_param)
{
	struct device_name_dev *dev;
	int32_t ret;

	if (!device)
		return -EINVAL;

	dev = no_os_calloc(1, sizeof(*dev));
	if (!dev)
		return -ENOMEM;

	/* Initialize SPI communication */
	ret = no_os_spi_init(&dev->spi_desc, &init_param.spi_init);
	if (ret < 0)
		goto error_spi;

	/* Initialize GPIO pins if used */
	if (init_param.gpio_reset.number != NO_OS_GPIO_UNASSIGNED) {
		ret = no_os_gpio_init(&dev->gpio_reset, &init_param.gpio_reset);
		if (ret < 0)
			goto error_gpio;

		/* Reset device */
		ret = no_os_gpio_set_value(dev->gpio_reset, NO_OS_GPIO_LOW);
		if (ret < 0)
			goto error_gpio;
		no_os_mdelay(1);
		ret = no_os_gpio_set_value(dev->gpio_reset, NO_OS_GPIO_HIGH);
		if (ret < 0)
			goto error_gpio;
		no_os_mdelay(10);
	}

	/* Store configuration */
	dev->device_id = init_param.device_id;

	/* Verify device ID */
	uint8_t chip_id;
	ret = device_name_read_register(dev, DEVICE_NAME_REG_ID, &chip_id);
	if (ret < 0)
		goto error_gpio;

	if (chip_id != EXPECTED_DEVICE_ID) {
		ret = -ENODEV;
		goto error_gpio;
	}

	*device = dev;

	return 0;

error_gpio:
	if (dev->gpio_reset)
		no_os_gpio_remove(dev->gpio_reset);
	no_os_spi_remove(dev->spi_desc);
error_spi:
	no_os_free(dev);

	return ret;
}

/**
 * @brief Free resources allocated by device_name_init().
 *
 * @param dev - The device structure.
 *
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t device_name_remove(struct device_name_dev *dev)
{
	if (!dev)
		return -EINVAL;

	if (dev->gpio_reset)
		no_os_gpio_remove(dev->gpio_reset);

	no_os_spi_remove(dev->spi_desc);
	no_os_free(dev);

	return 0;
}
```

## File Structure Template

Every driver should follow this enhanced structure:

```
drivers/<category>/<device_name>/
├── <device_name>.h        # Public API declarations
├── <device_name>.c        # Implementation
├── iio_<device_name>.h    # IIO subsystem interface (REQUIRED for monitoring devices)
├── iio_<device_name>.c    # IIO implementation
├── <device_name>_regs.h   # Register definitions (if complex)
└── README.rst            # Comprehensive documentation

projects/<device_name>/
├── Makefile              # Platform build selection
├── builds.json           # CI build matrix
├── src.mk               # Source dependencies and platform support
├── README.rst            # Complete project documentation
└── src/
    ├── common/
    │   ├── common_data.h
    │   └── common_data.c
    ├── examples/
    │   └── basic/
    └── platform/<target>/
```

## Naming Conventions

**Device Naming:**
- Use lowercase device name: `ad7980.h`, not `AD7980.h`
- Categories: `adc`, `dac`, `switch`, `sensor`, `power`, `frequency`, etc.
- Include family variants: `ad717x` for AD7175, AD7176, AD7177, etc.

**🚨 Linux Driver Naming Principle:**
> **Critical**: Linux drivers must not rely on generic or wildcard‑style names to represent multiple devices. The kernel driver model requires explicit device matching via ID tables or device tree compatibles, and device naming stability is intentionally delegated to user space.

**Implementation Guidelines:**
- ❌ **Avoid**: Generic names like `device_nameX`, `sensor_driver`, `power_controller`
- ✅ **Use**: Specific device names like `ltm4700`, `adm1275`, `ad7980`
- ✅ **Family Support**: Use explicit device identification in code (e.g., chip_id detection)
- ✅ **Branch Names**: `dev/ltm4700`, `dev/adm1275` (not `dev/ltm470x` or `dev/power_device`)

## Build System Integration Template

```makefile
# Driver source files (individual files only)
SRCS += $(DRIVERS)/<category>/<device>/<device>.c
SRCS += $(DRIVERS)/<category>/<device>/iio_<device>.c

# Driver headers (individual headers only)
INCS += $(DRIVERS)/<category>/<device>
INCS += $(INCLUDE)

# Required no-OS APIs (verified signatures)
SRCS += $(DRIVERS)/api/no_os_i2c.c
SRCS += $(DRIVERS)/api/no_os_gpio.c
SRCS += $(NO-OS)/util/no_os_alloc.c

# Platform drivers (verified platform constants)
SRCS += $(PLATFORM_DRIVERS)/$(PLATFORM)_gpio.c
SRCS += $(PLATFORM_DRIVERS)/$(PLATFORM)_i2c.c

# Platform headers (verified existence)
INCS += $(PLATFORM_DRIVERS)

# IIO support (if applicable)
SRCS += $(NO-OS)/iio/iio.c
INCS += $(NO-OS)/iio

# Examples integration (required)
include $(PROJECT)/src/examples.mk
```

## Documentation Templates

### Driver README Template

```rst
<DEVICE_NAME> Driver
===================

Overview
--------
The <DEVICE_NAME> driver provides support for the <Device Description> family of devices.

Supported Devices
-----------------
* <DEVICE_NAME> - <Description>
* <Variant Names> - <Descriptions>

Features
--------
* Device initialization and configuration
* Register read/write operations
* <Device-specific features>
* IIO subsystem integration (if applicable)

Hardware Setup
--------------
<Connection details, pin configurations>

Usage Example
-------------
.. code-block:: c

   struct <device>_dev *dev;
   struct <device>_init_param init = {
       // initialization parameters
   };

   ret = <device>_init(&dev, init);
   if (ret < 0)
       return ret;

API Reference
-------------
See <device>.h for complete API documentation.
```

---

These templates ensure consistency across all no-OS drivers and follow established patterns for maintainability and review efficiency.