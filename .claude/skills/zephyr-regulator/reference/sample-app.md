## Sample Application Development

Sample applications demonstrate how to use the subsystem and test drivers on actual hardware.

### Sample Directory Structure

```
samples/drivers/<subsystem>/<sample_name>/
├── CMakeLists.txt          # Build configuration
├── prj.conf                # Project configuration (Kconfig)
├── README.rst              # Documentation
├── sample.yaml             # Test metadata
├── src/
│   └── main.c              # Application code
└── boards/
    ├── <board1>.overlay    # Board-specific devicetree
    ├── <board2>.overlay    # Board-specific devicetree
    └── <board3>.conf       # Board-specific Kconfig (optional)
```

### CMakeLists.txt

Minimal build configuration:

```cmake
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(regulator_sample)

target_sources(app PRIVATE src/main.c)
```

### prj.conf

Common configuration options:

```conf
# Enable regulator subsystem
CONFIG_REGULATOR=y

# Enable logging
CONFIG_LOG=y
CONFIG_REGULATOR_LOG_LEVEL_DBG=y

# Enable console
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y

# Enable devicetree
CONFIG_GPIO=y
CONFIG_I2C=y  # or CONFIG_SPI=y depending on communication interface
```

### main.c - Sample Application

```c
/*
 * Copyright (c) 2024 Your Company
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/regulator.h>
#include <zephyr/sys/printk.h>

/* Get regulator device from devicetree */
#define REGULATOR_NODE DT_NODELABEL(buck1)

int main(void)
{
	const struct device *reg = DEVICE_DT_GET(REGULATOR_NODE);
	int ret;
	int32_t voltage_uv;

	if (!device_is_ready(reg)) {
		printk("Regulator device not ready\n");
		return 0;
	}

	printk("Regulator sample application\n");

	/* Enable regulator */
	ret = regulator_enable(reg);
	if (ret < 0) {
		printk("Failed to enable regulator: %d\n", ret);
		return 0;
	}
	printk("Regulator enabled\n");

	/* Get current voltage */
	ret = regulator_get_voltage(reg, &voltage_uv);
	if (ret == 0) {
		printk("Current voltage: %d uV (%d.%03d V)\n",
		       voltage_uv, voltage_uv / 1000000,
		       (voltage_uv % 1000000) / 1000);
	}

	/* Set voltage to 1.2V */
	ret = regulator_set_voltage(reg, 1200000, 1200000);
	if (ret < 0) {
		printk("Failed to set voltage: %d\n", ret);
	} else {
		printk("Voltage set to 1.2V\n");

		/* Verify new voltage */
		ret = regulator_get_voltage(reg, &voltage_uv);
		if (ret == 0) {
			printk("New voltage: %d uV\n", voltage_uv);
		}
	}

	/* Test voltage ramping */
	printk("\nVoltage ramping test:\n");
	int32_t voltages[] = {800000, 1000000, 1200000, 1500000, 1800000};

	for (size_t i = 0; i < ARRAY_SIZE(voltages); i++) {
		ret = regulator_set_voltage(reg, voltages[i], voltages[i]);
		if (ret == 0) {
			ret = regulator_get_voltage(reg, &voltage_uv);
			printk("Set %d uV -> actual %d uV\n",
			       voltages[i], voltage_uv);
			k_sleep(K_MSEC(500));
		}
	}

	/* Disable regulator */
	ret = regulator_disable(reg);
	if (ret < 0) {
		printk("Failed to disable regulator: %d\n", ret);
	} else {
		printk("\nRegulator disabled\n");
	}

	printk("Sample completed\n");
	return 0;
}
```

### README.rst - Sample Documentation

```rst
.. zephyr:code-sample:: regulator_basic
   :name: Regulator Basic Sample
   :relevant-api: regulator_interface

   Control voltage regulator output using the regulator API.

Overview
********

This sample demonstrates how to use the Regulator API to control
voltage regulators. It shows basic operations like enable/disable,
voltage get/set, and voltage ramping.

Requirements
************

* A board with a voltage regulator (PMIC or discrete regulator)
* The regulator must be defined in devicetree

Building and Running
********************

The regulator peripheral must be configured in devicetree. This sample
requires a regulator node, typically configured in a board overlay.

Example for a board with MAX20335 PMIC:

.. zephyr-app-commands::
   :zephyr-app: samples/drivers/regulator/basic
   :board: custom_board
   :goals: build flash
   :compact:

To build for a different board, change "custom_board" to your board name
and provide an appropriate devicetree overlay in the ``boards/`` directory.

Sample Output
=============

.. code-block::console

   *** Booting Zephyr OS build v3.7.0 ***
   Regulator sample application
   Regulator enabled
   Current voltage: 1200000 uV (1.200 V)
   Voltage set to 1.2V
   New voltage: 1200000 uV

   Voltage ramping test:
   Set 800000 uV -> actual 800000 uV
   Set 1000000 uV -> actual 1000000 uV
   Set 1200000 uV -> actual 1200000 uV
   Set 1500000 uV -> actual 1500000 uV
   Set 1800000 uV -> actual 1800000 uV

   Regulator disabled
   Sample completed
```

