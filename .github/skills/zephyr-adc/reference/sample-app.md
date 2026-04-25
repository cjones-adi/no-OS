## Sample Application Structure

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(adc_sample)

target_sources(app PRIVATE src/main.c)
```

### prj.conf

```conf
CONFIG_ADC=y
CONFIG_LOG=y
CONFIG_ADC_LOG_LEVEL_DBG=y

# If using specific ADC driver
CONFIG_ADC_AD4130=y  # Example
CONFIG_SPI=y         # If SPI-based ADC
CONFIG_I2C=y         # If I2C-based ADC

# Optional
CONFIG_ADC_ASYNC=y
```

### boards/<board>.overlay

```dts
/ {
	zephyr,user {
		io-channels = <&ad4130 1>, <&ad4130 2>;
		io-channel-names = "sensor0", "sensor1";
	};
};

&spi0 {
	status = "okay";
	cs-gpios = <&gpio0 15 GPIO_ACTIVE_LOW>;

	ad4130: ad4130@0 {
		compatible = "adi,ad4130-adc";
		reg = <0>;
		spi-max-frequency = <2700000>;
		status = "okay";

		#address-cells = <1>;
		#size-cells = <0>;
		#io-channel-cells = <1>;

		bipolar;
		internal-reference-value = <0>;  /* 2.5V */
		adc-mode = <0>;  /* Continuous */

		channel@1 {
			reg = <1>;
			zephyr,gain = "ADC_GAIN_1";
			zephyr,reference = "ADC_REF_INTERNAL";
			zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
			zephyr,resolution = <24>;
			zephyr,input-positive = <AD4130_ADC_AIN8>;
			zephyr,input-negative = <AD4130_ADC_AIN9>;
		};

		channel@2 {
			reg = <2>;
			zephyr,gain = "ADC_GAIN_2";
			zephyr,reference = "ADC_REF_INTERNAL";
			zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
			zephyr,resolution = <24>;
			zephyr,input-positive = <AD4130_ADC_AIN10>;
		};
	};
};
```

### src/main.c

```c
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#if !DT_NODE_EXISTS(DT_PATH(zephyr_user)) || \
	!DT_NODE_HAS_PROP(DT_PATH(zephyr_user), io_channels)
#error "No suitable devicetree overlay specified"
#endif

#define DT_SPEC_AND_COMMA(node_id, prop, idx) \
	ADC_DT_SPEC_GET_BY_IDX(node_id, idx),

static const struct adc_dt_spec adc_channels[] = {
	DT_FOREACH_PROP_ELEM(DT_PATH(zephyr_user), io_channels, DT_SPEC_AND_COMMA)
};

int main(void)
{
	int err;
	uint32_t buf;
	struct adc_sequence sequence = {
		.buffer = &buf,
		.buffer_size = sizeof(buf),
	};

	printk("ADC Sample Application\n");

	/* Configure all channels */
	for (size_t i = 0U; i < ARRAY_SIZE(adc_channels); i++) {
		if (!adc_is_ready_dt(&adc_channels[i])) {
			printk("ADC controller device %s not ready\n",
			       adc_channels[i].dev->name);
			return 0;
		}

		err = adc_channel_setup_dt(&adc_channels[i]);
		if (err < 0) {
			printk("Could not setup channel #%d (%d)\n", i, err);
			return 0;
		}
	}

	printk("All channels configured\n");

	/* Read loop */
	while (1) {
		printk("\n--- ADC Reading ---\n");

		for (size_t i = 0U; i < ARRAY_SIZE(adc_channels); i++) {
			int32_t val_mv;

			printk("Channel %d (%s): ",
			       adc_channels[i].channel_id,
			       i < DT_PROP_LEN(DT_PATH(zephyr_user), io_channel_names) ?
			           DT_PROP_BY_IDX(DT_PATH(zephyr_user), io_channel_names, i) :
			           "unnamed");

			(void)adc_sequence_init_dt(&adc_channels[i], &sequence);

			err = adc_read_dt(&adc_channels[i], &sequence);
			if (err < 0) {
				printk("Read failed (%d)\n", err);
				continue;
			}

			val_mv = (int32_t)buf;
			printk("raw=%u", buf);

			err = adc_raw_to_millivolts_dt(&adc_channels[i], &val_mv);
			if (err < 0) {
				printk(" (conversion not available)\n");
			} else {
				printk(" → %d mV\n", val_mv);
			}
		}

		k_sleep(K_MSEC(1000));
	}

	return 0;
}
```

### sample.yaml

```yaml
sample:
  name: ADC Sample
  description: ADC driver sample application
tests:
  sample.drivers.adc:
    harness: console
    tags: adc drivers
    filter: dt_compat_enabled("adi,ad4130-adc")
    platform_allow:
      - nrf52840dk/nrf52840
      - nucleo_f767zi
    integration_platforms:
      - nrf52840dk/nrf52840
```

### README.rst

```rst
ADC Sample
##########

Overview
********

This sample demonstrates how to use the ADC driver API to read analog
voltages from ADC channels configured in devicetree.

Requirements
************

- Board with ADC support
- ADC channels configured in devicetree overlay

Building and Running
********************

Build and flash as follows:

.. zephyr-app-commands::
   :zephyr-app: samples/drivers/adc
   :board: nrf52840dk/nrf52840
   :goals: build flash
   :compact:

Sample Output
*************

.. code-block:: console

   ADC Sample Application
   All channels configured

   --- ADC Reading ---
   Channel 1 (sensor0): raw=8388608 → 2500 mV
   Channel 2 (sensor1): raw=4194304 → 1250 mV

   --- ADC Reading ---
   Channel 1 (sensor0): raw=8389120 → 2501 mV
   Channel 2 (sensor1): raw=4194816 → 1251 mV
```

