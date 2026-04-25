## Sample Application Structure

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(dac_sample)

target_sources(app PRIVATE src/main.c)
```

### prj.conf

```conf
CONFIG_DAC=y
CONFIG_LOG=y
CONFIG_DAC_LOG_LEVEL_DBG=y

# If using SPI-based DAC
CONFIG_SPI=y

# If using I2C-based DAC
CONFIG_I2C=y

# Floating point for sine wave generation
CONFIG_FPU=y
CONFIG_NEWLIB_LIBC=y
CONFIG_NEWLIB_LIBC_FLOAT_PRINTF=y
```

### boards/<board>.overlay

```dts
/ {
	zephyr,user {
		dac = <&dac_ad5621>;
		dac-channel-id = <0>;
		dac-resolution = <12>;
	};
};

&spi0 {
	status = "okay";
	cs-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;

	dac_ad5621: ad5621@0 {
		compatible = "adi,ad5621";
		reg = <0>;
		spi-max-frequency = <30000000>;
		#io-channel-cells = <1>;
	};
};
```

### src/main.c (Complete Example)

```c
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/dac.h>
#include <zephyr/sys/printk.h>
#include <math.h>

#define ZEPHYR_USER_NODE DT_PATH(zephyr_user)

#if (DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, dac) && \
     DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, dac_channel_id) && \
     DT_NODE_HAS_PROP(ZEPHYR_USER_NODE, dac_resolution))
#define DAC_NODE        DT_PHANDLE(ZEPHYR_USER_NODE, dac)
#define DAC_CHANNEL_ID  DT_PROP(ZEPHYR_USER_NODE, dac_channel_id)
#define DAC_RESOLUTION  DT_PROP(ZEPHYR_USER_NODE, dac_resolution)
#else
#error "Unsupported board: check /zephyr,user node properties"
#endif

static const struct device *const dac_dev = DEVICE_DT_GET(DAC_NODE);

static const struct dac_channel_cfg dac_ch_cfg = {
	.channel_id  = DAC_CHANNEL_ID,
	.resolution  = DAC_RESOLUTION,
	.buffered    = true,
};

int main(void)
{
	int ret;
	uint32_t max_value = (1U << DAC_RESOLUTION) - 1;

	printk("DAC Sample Application\n");
	printk("DAC: %s, Channel: %d, Resolution: %d bits\n",
	       dac_dev->name, DAC_CHANNEL_ID, DAC_RESOLUTION);

	/* Check if DAC is ready */
	if (!device_is_ready(dac_dev)) {
		printk("ERROR: DAC device not ready\n");
		return 0;
	}

	/* Configure DAC channel */
	ret = dac_channel_setup(dac_dev, &dac_ch_cfg);
	if (ret != 0) {
		printk("ERROR: DAC channel setup failed: %d\n", ret);
		return 0;
	}

	printk("DAC configured successfully\n");
	printk("Max value: %u (%.2f%% = full scale)\n",
	       max_value, 100.0);

	/* Test 1: Set DC levels */
	printk("\nTest 1: DC Levels\n");
	uint32_t test_levels[] = {0, max_value/4, max_value/2, 3*max_value/4, max_value};
	const char *level_names[] = {"0%", "25%", "50%", "75%", "100%"};

	for (int i = 0; i < ARRAY_SIZE(test_levels); i++) {
		ret = dac_write_value(dac_dev, DAC_CHANNEL_ID, test_levels[i]);
		if (ret == 0) {
			printk("  %s: value=%u\n", level_names[i], test_levels[i]);
			k_sleep(K_SECONDS(2));
		} else {
			printk("  ERROR writing %s: %d\n", level_names[i], ret);
		}
	}

	/* Test 2: Generate sawtooth wave */
	printk("\nTest 2: Generating sawtooth wave (5 cycles)\n");
	const int steps = 100;
	const int cycles = 5;

	for (int cycle = 0; cycle < cycles; cycle++) {
		for (int step = 0; step < steps; step++) {
			uint32_t value = (uint32_t)((uint64_t)step * max_value / steps);
			dac_write_value(dac_dev, DAC_CHANNEL_ID, value);
			k_usleep(1000);  /* 1ms per step */
		}
	}

	printk("Sawtooth wave complete\n");

	/* Set to mid-scale and hold */
	uint32_t mid_scale = max_value / 2;
	dac_write_value(dac_dev, DAC_CHANNEL_ID, mid_scale);
	printk("\nHolding at mid-scale: value=%u\n", mid_scale);

	return 0;
}
```

### README.rst

```rst
DAC Sample Application
######################

Overview
********

This sample demonstrates the DAC driver API by generating analog output
waveforms.

Features:
- Configure DAC channel with resolution and buffering
- Set DC voltage levels
- Generate sawtooth waveforms
- Measure output with multimeter or oscilloscope

Requirements
************

- Board with DAC support (SPI or I2C DAC, or MCU with integrated DAC)
- Board overlay with DAC devicetree configuration

Building and Running
********************

Build for your board with DAC overlay:

.. code-block:: console

   west build -p always -b your_board samples/drivers/dac
   west flash

Expected Output
***************

.. code-block:: console

   DAC Sample Application
   DAC: ad5621@0, Channel: 0, Resolution: 12 bits
   DAC configured successfully
   Max value: 4095 (100.00% = full scale)

   Test 1: DC Levels
     0%: value=0
     25%: value=1023
     50%: value=2047
     75%: value=3071
     100%: value=4095

   Test 2: Generating sawtooth wave (5 cycles)
   Sawtooth wave complete

   Holding at mid-scale: value=2047
```

