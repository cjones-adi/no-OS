# Regulator and GPIO Integration

Detailed guide for integrating PMBus devices with Linux regulator framework and GPIO subsystem. Covers regulator operations, GPIO expanders in power sequencers, and NVMEM/blackbox support.

## Regulator Framework Integration

Many PMBus devices provide voltage regulation. The PMBus core supports registering as a regulator provider.

### Basic Regulator Integration

LTC2978 8-channel voltage supervisor as regulators:

```c
#include <linux/regulator/driver.h>
#include "pmbus.h"

#if IS_ENABLED(CONFIG_SENSORS_LTC2978_REGULATOR)

// Voltage range: 0 to 8V in 1mV steps
#define LTC2978_ADC_RES      0xFFFF  // 16-bit resolution
#define LTC2978_N_ADC        122     // ADC gain (mV per LSB)
#define LTC2978_MAX_UV       (LTC2978_ADC_RES * LTC2978_N_ADC)
#define LTC2978_UV_STEP      1000    // 1mV step
#define LTC2978_N_VOLTAGES   ((LTC2978_MAX_UV / LTC2978_UV_STEP) + 1)

// Define regulator descriptors for each page
static const struct regulator_desc ltc2978_reg_desc[] = {
	PMBUS_REGULATOR_STEP("vout", 0, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
	PMBUS_REGULATOR_STEP("vout", 1, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
	PMBUS_REGULATOR_STEP("vout", 2, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
	PMBUS_REGULATOR_STEP("vout", 3, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
	PMBUS_REGULATOR_STEP("vout", 4, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
	PMBUS_REGULATOR_STEP("vout", 5, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
	PMBUS_REGULATOR_STEP("vout", 6, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
	PMBUS_REGULATOR_STEP("vout", 7, LTC2978_N_VOLTAGES, LTC2978_UV_STEP, 0),
};

static int ltc2978_probe(struct i2c_client *client)
{
	struct ltc2978_data *data;
	struct pmbus_driver_info *info;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	info = &data->info;

	// ... (PMBus setup)

	// Register regulators
	info->num_regulators = info->pages;
	info->reg_desc = ltc2978_reg_desc;

	return pmbus_do_probe(client, info);
}

#endif /* CONFIG_SENSORS_LTC2978_REGULATOR */
```

### PMBUS_REGULATOR Macros

PMBus provides helper macros for regulator descriptors:

```c
// One regulator per page, linear voltage steps
#define PMBUS_REGULATOR_STEP(_name, _id, _n_voltages, _uv_step, _min_uv) \
	[_id] = { \
		.name = (_name), \
		.id = (_id), \
		.of_match = of_match_ptr(_name), \
		.regulators_node = of_match_ptr("regulators"), \
		.n_voltages = (_n_voltages), \
		.uV_step = (_uv_step), \
		.min_uV = (_min_uv), \
		.ops = &pmbus_regulator_ops, \
		.type = REGULATOR_VOLTAGE, \
		.owner = THIS_MODULE, \
	}

// One regulator per page, exact voltage list
#define PMBUS_REGULATOR_ONE(_name, _id) \
	[_id] = { \
		.name = (_name), \
		.id = (_id), \
		.of_match = of_match_ptr(_name), \
		.regulators_node = of_match_ptr("regulators"), \
		.n_voltages = 1, \
		.ops = &pmbus_regulator_ops, \
		.type = REGULATOR_VOLTAGE, \
		.owner = THIS_MODULE, \
	}
```

### Kconfig Integration

Add regulator support conditionally:

```kconfig
config SENSORS_LTC2978
	tristate "Linear Technologies LTC2978 and compatibles"
	help
	  If you say yes here you get hardware monitoring support for Linear
	  Technology LTC2974, LTC2975, LTC2977, LTC2978, LTC2980, LTC3880,
	  LTC3882, LTC3883, LTC3886, LTC3887, LTC3889, LTM2987, LTM4664,
	  LTM4675, LTM4676, LTM4677, LTM4678, LTM4680, LTM4686, and LTM4700.

config SENSORS_LTC2978_REGULATOR
	bool "Regulator support for LTC2978 and compatibles"
	depends on SENSORS_LTC2978 && REGULATOR
	help
	  If you say yes here you get regulator support for Linear Technology
	  LTC2974, LTC2975, LTC2977, LTC2978, LTC2980, LTC3880, LTC3882,
	  LTC3883, LTC3886, LTC3887, LTC3889, LTM2987, LTM4664, LTM4675,
	  LTM4676, LTM4677, LTM4678, LTM4680, LTM4686, and LTM4700.
```

### Devicetree Regulator Configuration

```dts
&i2c0 {
	ltc2978@5c {
		compatible = "lltc,ltc2978";
		reg = <0x5c>;

		regulators {
			vout0: vout0 {
				regulator-name = "vout0";
				regulator-min-microvolt = <500000>;  // 0.5V
				regulator-max-microvolt = <1500000>; // 1.5V
				regulator-boot-on;
				regulator-always-on;
			};

			vout1: vout1 {
				regulator-name = "vout1";
				regulator-min-microvolt = <1800000>;
				regulator-max-microvolt = <3300000>;
			};

			// ... more regulators ...
		};
	};
};

// Consumer device
sdhci@50000000 {
	compatible = "vendor,sdhci";
	reg = <0x50000000 0x1000>;

	vmmc-supply = <&vout0>;  // SD card power from LTC2978 page 0
	vqmmc-supply = <&vout1>; // SD card I/O from LTC2978 page 1
};
```

## GPIO Integration

Power sequencers often include GPIO or PDIO (Power Digital I/O) pins for general-purpose control.

### ADM1266: GPIO and PDIO

ADM1266 has 9 GPIOs + 16 PDIOs integrated with PMBus functionality:

```c
#include <linux/gpio/driver.h>
#include "pmbus.h"

#define ADM1266_GPIO_NR      9   // 9 GPIO pins
#define ADM1266_PDIO_NR      16  // 16 PDIO pins
#define ADM1266_TOTAL_GPIO   (ADM1266_GPIO_NR + ADM1266_PDIO_NR)

// Manufacturer-specific commands
#define ADM1266_GPIO_STATUS  0xD0
#define ADM1266_PDIO_STATUS  0xD1

struct adm1266_data {
	struct pmbus_driver_info info;
	struct gpio_chip gc;
	const char *gpio_names[ADM1266_TOTAL_GPIO];
	struct i2c_client *client;
	struct mutex gpio_lock;
};

static int adm1266_gpio_get(struct gpio_chip *chip, unsigned int offset)
{
	struct adm1266_data *data = gpiochip_get_data(chip);
	u8 read_buf[I2C_SMBUS_BLOCK_MAX + 1];
	unsigned long pins_status;
	unsigned int pmbus_cmd;
	int ret;

	// GPIOs and PDIOs have separate status registers
	if (offset < ADM1266_GPIO_NR)
		pmbus_cmd = ADM1266_GPIO_STATUS;
	else
		pmbus_cmd = ADM1266_PDIO_STATUS;

	mutex_lock(&data->gpio_lock);
	ret = i2c_smbus_read_block_data(data->client, pmbus_cmd, read_buf);
	mutex_unlock(&data->gpio_lock);

	if (ret < 0)
		return ret;

	pins_status = read_buf[0] + (read_buf[1] << 8);

	if (offset < ADM1266_GPIO_NR) {
		// GPIO mapping (hardware-specific)
		return !!(pins_status & BIT(offset));
	} else {
		// PDIO direct mapping
		return !!(pins_status & BIT(offset - ADM1266_GPIO_NR));
	}
}

static void adm1266_gpio_set(struct gpio_chip *chip, unsigned int offset,
                             int value)
{
	struct adm1266_data *data = gpiochip_get_data(chip);
	u8 write_buf[3];
	unsigned int pmbus_cmd;

	if (offset < ADM1266_GPIO_NR)
		pmbus_cmd = ADM1266_GPIO_CONTROL;
	else
		pmbus_cmd = ADM1266_PDIO_CONTROL;

	write_buf[0] = offset;
	write_buf[1] = value ? 1 : 0;

	mutex_lock(&data->gpio_lock);
	i2c_smbus_write_block_data(data->client, pmbus_cmd, 2, write_buf);
	mutex_unlock(&data->gpio_lock);
}

static int adm1266_gpio_get_direction(struct gpio_chip *chip,
                                      unsigned int offset)
{
	// ADM1266 GPIOs are bidirectional, query hardware
	// Implementation depends on device-specific registers
	return GPIO_LINE_DIRECTION_IN;  // Simplified
}

static int adm1266_gpio_direction_input(struct gpio_chip *chip,
                                        unsigned int offset)
{
	// Configure GPIO as input via device-specific command
	return 0;
}

static int adm1266_gpio_direction_output(struct gpio_chip *chip,
                                         unsigned int offset, int value)
{
	// Set value first
	adm1266_gpio_set(chip, offset, value);

	// Configure GPIO as output via device-specific command
	return 0;
}

static int adm1266_config_gpio(struct adm1266_data *data)
{
	const char *name = dev_name(&data->client->dev);
	int i;

	// Generate unique GPIO names
	for (i = 0; i < ADM1266_GPIO_NR; i++) {
		data->gpio_names[i] = devm_kasprintf(&data->client->dev,
		                                     GFP_KERNEL,
		                                     "adm1266-%x-gpio%d",
		                                     data->client->addr, i);
		if (!data->gpio_names[i])
			return -ENOMEM;
	}

	for (i = 0; i < ADM1266_PDIO_NR; i++) {
		data->gpio_names[ADM1266_GPIO_NR + i] =
			devm_kasprintf(&data->client->dev, GFP_KERNEL,
			               "adm1266-%x-pdio%d",
			               data->client->addr, i);
		if (!data->gpio_names[ADM1266_GPIO_NR + i])
			return -ENOMEM;
	}

	data->gc.label = name;
	data->gc.parent = &data->client->dev;
	data->gc.owner = THIS_MODULE;
	data->gc.can_sleep = true;  // I2C access may sleep
	data->gc.base = -1;  // Dynamic allocation
	data->gc.names = data->gpio_names;
	data->gc.ngpio = ADM1266_TOTAL_GPIO;
	data->gc.get = adm1266_gpio_get;
	data->gc.set = adm1266_gpio_set;
	data->gc.get_direction = adm1266_gpio_get_direction;
	data->gc.direction_input = adm1266_gpio_direction_input;
	data->gc.direction_output = adm1266_gpio_direction_output;

	return devm_gpiochip_add_data(&data->client->dev, &data->gc, data);
}

static int adm1266_probe(struct i2c_client *client)
{
	struct adm1266_data *data;
	int ret;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	data->client = client;
	mutex_init(&data->gpio_lock);

	// Configure GPIO before PMBus probe
	ret = adm1266_config_gpio(data);
	if (ret < 0)
		return ret;

	// Continue with PMBus initialization
	data->info.pages = 17;
	data->info.format[PSC_VOLTAGE_OUT] = linear;

	for (i = 0; i < data->info.pages; i++)
		data->info.func[i] = PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT;

	return pmbus_do_probe(client, &data->info);
}
```

### GPIO Devicetree Integration

```dts
&i2c0 {
	adm1266@42 {
		compatible = "adi,adm1266";
		reg = <0x42>;

		gpio-controller;
		#gpio-cells = <2>;
	};
};

// GPIO consumer
reset_device {
	compatible = "gpio-reset";
	reset-gpios = <&adm1266 5 GPIO_ACTIVE_LOW>;  // PDIO5
};
```

## NVMEM/Blackbox Support

ADM1266 includes fault recording ("blackbox") accessible via NVMEM subsystem:

```c
#include <linux/nvmem-consumer.h>
#include <linux/nvmem-provider.h>

#define ADM1266_BLACKBOX_SIZE       64   // Bytes per record
#define ADM1266_BLACKBOX_RECORDS    32   // Number of records
#define ADM1266_BLACKBOX_TOTAL      (ADM1266_BLACKBOX_SIZE * ADM1266_BLACKBOX_RECORDS)

#define ADM1266_BLACKBOX_INFO       0xE0
#define ADM1266_READ_BLACKBOX       0xE1

struct adm1266_data {
	// ... (other fields)
	struct nvmem_device *nvmem;
	struct nvmem_config nvmem_config;
	u8 *dev_mem;  // Cached blackbox data
};

static const struct nvmem_cell_info adm1266_nvmem_cells[] = {
	{
		.name   = "blackbox",
		.offset = 0,
		.bytes  = ADM1266_BLACKBOX_TOTAL,
	},
};

static int adm1266_nvmem_read_blackbox(struct adm1266_data *data, u8 *read_buff)
{
	int record_count;
	char index;
	u8 info_buf[5];
	int ret;

	// Query number of blackbox records
	ret = i2c_smbus_read_block_data(data->client, ADM1266_BLACKBOX_INFO,
	                                info_buf);
	if (ret < 0)
		return ret;

	record_count = info_buf[3];

	// Read each record
	for (index = 0; index < record_count; index++) {
		u8 cmd_buf[2] = { ADM1266_READ_BLACKBOX, index };

		ret = i2c_smbus_write_block_data(data->client,
		                                 ADM1266_READ_BLACKBOX,
		                                 2, cmd_buf);
		if (ret < 0)
			return ret;

		ret = i2c_smbus_read_block_data(data->client,
		                                ADM1266_READ_BLACKBOX,
		                                read_buff);
		if (ret < 0)
			return ret;

		if (ret != ADM1266_BLACKBOX_SIZE)
			return -EIO;

		read_buff += ADM1266_BLACKBOX_SIZE;
	}

	return 0;
}

static int adm1266_nvmem_read(void *priv, unsigned int offset,
                              void *val, size_t bytes)
{
	struct adm1266_data *data = priv;
	int ret;

	if (offset + bytes > data->nvmem_config.size)
		return -EINVAL;

	// Refresh blackbox data on first read
	if (offset == 0) {
		memset(data->dev_mem, 0, data->nvmem_config.size);

		ret = adm1266_nvmem_read_blackbox(data, data->dev_mem);
		if (ret) {
			dev_err(&data->client->dev, "Could not read blackbox\n");
			return ret;
		}
	}

	memcpy(val, data->dev_mem + offset, bytes);
	return 0;
}

static int adm1266_config_nvmem(struct adm1266_data *data)
{
	data->nvmem_config.name = dev_name(&data->client->dev);
	data->nvmem_config.dev = &data->client->dev;
	data->nvmem_config.root_only = true;
	data->nvmem_config.read_only = true;
	data->nvmem_config.owner = THIS_MODULE;
	data->nvmem_config.reg_read = adm1266_nvmem_read;
	data->nvmem_config.cells = adm1266_nvmem_cells;
	data->nvmem_config.ncells = ARRAY_SIZE(adm1266_nvmem_cells);
	data->nvmem_config.priv = data;
	data->nvmem_config.stride = 1;
	data->nvmem_config.word_size = 1;
	data->nvmem_config.size = ADM1266_BLACKBOX_TOTAL;

	data->dev_mem = devm_kzalloc(&data->client->dev,
	                             data->nvmem_config.size, GFP_KERNEL);
	if (!data->dev_mem)
		return -ENOMEM;

	data->nvmem = devm_nvmem_register(&data->client->dev,
	                                  &data->nvmem_config);
	if (IS_ERR(data->nvmem)) {
		dev_err(&data->client->dev, "Could not register nvmem\n");
		return PTR_ERR(data->nvmem);
	}

	return 0;
}

static int adm1266_probe(struct i2c_client *client)
{
	struct adm1266_data *data;
	int ret;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	data->client = client;

	// Configure NVMEM (blackbox)
	ret = adm1266_config_nvmem(data);
	if (ret < 0)
		return ret;

	// Configure GPIO
	ret = adm1266_config_gpio(data);
	if (ret < 0)
		return ret;

	// PMBus initialization
	// ...

	return pmbus_do_probe(client, &data->info);
}
```

### Accessing Blackbox from Userspace

```bash
# Find NVMEM device
ls /sys/bus/nvmem/devices/

# Read blackbox
hexdump -C /sys/bus/nvmem/devices/1-0042*/nvmem

# Or via sysfs
cat /sys/bus/nvmem/devices/1-0042*/nvmem > blackbox.bin
```

## Platform Data

Some PMBus devices need platform-specific configuration flags:

```c
struct pmbus_platform_data {
	u32 flags;
};

// Flags
#define PMBUS_SKIP_STATUS_CHECK          BIT(0)
#define PMBUS_WRITE_PROTECTED            BIT(1)
#define PMBUS_NO_CAPABILITY              BIT(2)
#define PMBUS_READ_STATUS_AFTER_FAILED_CHECK  BIT(3)

// Usage in probe
static int mypmbus_probe(struct i2c_client *client)
{
	struct pmbus_platform_data *pdata;

	pdata = dev_get_platdata(&client->dev);
	if (pdata) {
		if (pdata->flags & PMBUS_WRITE_PROTECTED)
			dev_info(&client->dev, "Write protection enabled\n");
	}

	// ...
}
```
