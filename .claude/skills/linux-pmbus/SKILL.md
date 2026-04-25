---
name: linux-pmbus
description: Comprehensive guide to Linux PMBus subsystem for power management devices. Use when implementing PMBus drivers for DC-DC converters, PMICs, hot-swap controllers, power supplies, or sequencers. Covers multi-page devices, direct format coefficients, virtual commands, peak tracking, regulator/GPIO integration, and debugging.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: hwmon-pmbus
  tags:
    - pmbus
    - hwmon
    - power-management
    - dc-dc-converter
    - pmic
    - hot-swap
    - voltage-regulator
    - direct-format
    - linear-format
  dependencies:
    - linux-hwmon
    - linux-regulator
    - linux-gpio
    - linux-i2c-controller
    - linux-devicetree
  learning_objectives:
    - Implement PMBus device drivers with pmbus_driver_info
    - Configure direct format coefficients (m, b, R)
    - Handle multi-page devices and page switching
    - Implement virtual commands for peak tracking
    - Integrate with regulator framework
    - Add GPIO support for power sequencers
    - Debug PMBus communication and data format issues
---

# Linux PMBus Subsystem

Quick-start guide for implementing PMBus power management device drivers.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User mentions: "implement PMBus driver", "probe function", "pmbus_driver_info", "identify callback"
- Questions about: direct format setup, coefficient calculation, chip variants, busy-wait devices
- User asks: "how to implement", "create PMBus driver", "ADM1275", "LTC2978", "hot-swap controller"
- Topics: probe pattern, device-specific quirks, IEEE 754 format, shunt resistor scaling

**Triggers to read reference/commands.md**:
- User mentions: "PMBus commands", "virtual commands", "PMBUS_VIRT_*", "data format", "LINEAR11"
- Questions about: m/b/R coefficients, direct format formula, sensor classes, page parameter
- User asks: "what is PMBUS_READ_VOUT", "how to calculate coefficients", "linear vs direct format"
- Topics: standard commands, manufacturer-specific commands, format conversion, phase parameter

**Triggers to read reference/multi-page.md**:
- User mentions: "multi-page", "PAGE command", "power sequencer", "multiple rails", "LTC2974"
- Questions about: page switching, per-page functionality, page broadcast, multi-phase
- User asks: "17 pages", "8 channels", "how to handle multiple outputs", "page vs phase"
- Topics: shared VIN, independent regulators, page count, sysfs for multi-page

**Triggers to read reference/integration.md**:
- User mentions: "regulator framework", "GPIO", "NVMEM", "blackbox", "ADM1266"
- Questions about: regulator support, PDIO pins, GPIO expander, fault recording
- User asks: "integrate with regulator", "add GPIO support", "PMBUS_REGULATOR_STEP"
- Topics: regulator descriptors, gpio_chip, NVMEM provider, platform data flags

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "wrong value", "incorrect reading", "alarm not triggering"
- Questions about: sysfs interface, i2c-tools, tracing, dynamic debug
- User says: "troubleshoot", "diagnose", "PMBus error", "coefficient wrong", "peak tracking broken"
- Topics: debugfs, I2C tracing, common issues, performance debugging, kernel oops

---

## When to Use This Skill

- Implementing drivers for PMBus/SMBus power management ICs:
  - **DC-DC converters**: Buck, boost, buck-boost (LTC3880, LT7170)
  - **PMICs**: Multi-rail power management (LTC2978, ADM1266)
  - **Hot-swap controllers**: Current/power monitoring (ADM1275, ADM1293)
  - **Power sequencers**: Multi-output supervisors (ADM1266, LTC2974)
  - **Battery chargers**: PMBus-compliant charging controllers
  - **Power supplies**: Server/telecom power supplies

## What is the Linux PMBus Subsystem?

PMBus is an open standard power management protocol over SMBus/I2C. The Linux PMBus subsystem uses a three-layer architecture:

```
┌─────────────────────────────────────┐
│   Device-Specific Driver Layer      │  ← Chip-specific initialization
│   (adm1275.c, ltc2978.c, etc.)      │     Non-standard commands
├─────────────────────────────────────┤     Peak tracking, GPIO, etc.
│   Generic Driver Layer              │
│   (pmbus.c)                          │  ← Auto-detection for standard
├─────────────────────────────────────┤     PMBus devices
│   Core Driver Layer                 │
│   (pmbus_core.c)                    │  ← Generic functionality & API
└─────────────────────────────────────┘     Exports pmbus_do_probe(), etc.
         ↓
    HWMON subsystem
```

**Key design principle**: Device-specific drivers handle chip quirks without modifying core code (similar to PCI quirks).

**PMBus characteristics**:
- No mandatory commands (specification defines but doesn't require)
- Vendor extensions beyond standard commands
- Multi-page support for multiple voltage rails
- Multi-phase support for high-current outputs

## Quick Reference

### Core Structure

```c
#include <linux/pmbus.h>
#include "pmbus.h"  // Internal header in drivers/hwmon/pmbus/

struct pmbus_driver_info {
	int pages;                      // Number of pages (voltage rails)
	int phases[PMBUS_PAGES];        // Phases per page

	// Data format for each sensor class
	enum pmbus_format format[PSC_NUM_CLASSES];

	// Direct format coefficients (if format[x] = direct)
	s32 m[PSC_NUM_CLASSES];         // Multiplier
	s32 b[PSC_NUM_CLASSES];         // Offset
	s32 R[PSC_NUM_CLASSES];         // Exponent (power of 10)

	// Functionality per page
	u32 func[PMBUS_PAGES];

	// Optional callbacks
	int (*read_word_data)(struct i2c_client *client, int page,
	                      int phase, int reg);
	int (*read_byte_data)(struct i2c_client *client, int page, int reg);
	int (*write_word_data)(struct i2c_client *client, int page,
	                       int reg, u16 word);
	int (*write_byte)(struct i2c_client *client, int page, u8 byte);
	int (*identify)(struct i2c_client *client,
	                struct pmbus_driver_info *info);

	// Regulator integration
	int num_regulators;
	const struct regulator_desc *reg_desc;
};
```

### Data Formats

```c
enum pmbus_format {
	linear,      // Linear11: 5-bit exponent, 11-bit mantissa (standard)
	direct,      // Direct: real = (register * m - b) * 10^R
	vid,         // VID format: voltage identifier codes
	ieee754,     // IEEE 754 floating point (LT7170, LT7171)
};
```

### Sensor Classes

```c
enum pmbus_sensor_classes {
	PSC_VOLTAGE_IN,      // Input voltage
	PSC_VOLTAGE_OUT,     // Output voltage
	PSC_CURRENT_IN,      // Input current
	PSC_CURRENT_OUT,     // Output current
	PSC_POWER,           // Power
	PSC_TEMPERATURE,     // Temperature
	PSC_FAN,             // Fan speed
	PSC_PWM,             // PWM duty cycle
	PSC_NUM_CLASSES,
};
```

### Functionality Flags

```c
#define PMBUS_HAVE_VIN          BIT(0)   // Input voltage monitoring
#define PMBUS_HAVE_VOUT         BIT(1)   // Output voltage monitoring
#define PMBUS_HAVE_IIN          BIT(2)   // Input current monitoring
#define PMBUS_HAVE_IOUT         BIT(3)   // Output current monitoring
#define PMBUS_HAVE_PIN          BIT(4)   // Input power monitoring
#define PMBUS_HAVE_POUT         BIT(5)   // Output power monitoring
#define PMBUS_HAVE_TEMP         BIT(8)   // Temperature sensor
#define PMBUS_HAVE_STATUS_VOUT  BIT(11)  // Output voltage status/alarms
#define PMBUS_HAVE_STATUS_IOUT  BIT(12)  // Output current status/alarms
#define PMBUS_HAVE_STATUS_INPUT BIT(13)  // Input status/alarms
#define PMBUS_HAVE_STATUS_TEMP  BIT(14)  // Temperature status/alarms
```

### Virtual Commands

Virtual commands (0x100+) provide consistent interfaces for non-standard features:

```c
// Peak/history tracking
#define PMBUS_VIRT_READ_VIN_MAX         0x100  // Peak input voltage
#define PMBUS_VIRT_READ_VOUT_MAX        0x102  // Peak output voltage
#define PMBUS_VIRT_READ_IOUT_MAX        0x104  // Peak output current
#define PMBUS_VIRT_READ_TEMP_MAX        0x106  // Peak temperature
#define PMBUS_VIRT_READ_PIN_MAX         0x108  // Peak input power

// Reset commands
#define PMBUS_VIRT_RESET_VOUT_HISTORY   0x110  // Clear VOUT peak/min
#define PMBUS_VIRT_RESET_IOUT_HISTORY   0x112  // Clear IOUT peak/min

// Sampling
#define PMBUS_VIRT_POWER_SAMPLES        0x120  // Number of power samples
#define PMBUS_VIRT_IN_SAMPLES           0x121  // Number of input samples
```

**Important**: Virtual commands must be handled in read/write callbacks. Return `-ENODATA` for unsupported commands.

## Quick Start

### Basic PMBus Driver (Linear Format)

```c
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/of.h>
#include "pmbus.h"

static struct pmbus_driver_info example_info = {
	.pages = 1,
	.format[PSC_VOLTAGE_IN] = linear,
	.format[PSC_VOLTAGE_OUT] = linear,
	.format[PSC_CURRENT_OUT] = linear,
	.format[PSC_TEMPERATURE] = linear,
	.func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_STATUS_INPUT |
	           PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT |
	           PMBUS_HAVE_IOUT | PMBUS_HAVE_STATUS_IOUT |
	           PMBUS_HAVE_TEMP | PMBUS_HAVE_STATUS_TEMP,
};

static int example_probe(struct i2c_client *client)
{
	return pmbus_do_probe(client, &example_info);
}

static const struct i2c_device_id example_id[] = {
	{ "example_pmbus", 0 },
	{}
};
MODULE_DEVICE_TABLE(i2c, example_id);

static const struct of_device_id example_of_match[] = {
	{ .compatible = "example,pmbus" },
	{}
};
MODULE_DEVICE_TABLE(of, example_of_match);

static struct i2c_driver example_driver = {
	.driver = {
		.name = "example_pmbus",
		.of_match_table = example_of_match,
	},
	.probe = example_probe,
	.id_table = example_id,
};
module_i2c_driver(example_driver);

MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("PMBus driver for Example Device");
MODULE_LICENSE("GPL");
MODULE_IMPORT_NS(PMBUS);
```

### Direct Format with Coefficients

```c
struct adm1275_data {
	struct pmbus_driver_info info;
};

static int adm1275_probe(struct i2c_client *client)
{
	struct adm1275_data *data;
	struct pmbus_driver_info *info;
	u32 shunt;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	if (!data)
		return -ENOMEM;

	info = &data->info;
	info->pages = 1;
	info->format[PSC_VOLTAGE_IN] = direct;
	info->format[PSC_VOLTAGE_OUT] = direct;
	info->format[PSC_CURRENT_OUT] = direct;

	info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_VOUT | PMBUS_HAVE_IOUT;

	// Read shunt resistor from devicetree
	if (of_property_read_u32(client->dev.of_node,
	                         "shunt-resistor-micro-ohms", &shunt))
		shunt = 1000; // Default: 1 mOhm

	// Voltage coefficients (60V range)
	info->m[PSC_VOLTAGE_IN] = 19199;
	info->b[PSC_VOLTAGE_IN] = 0;
	info->R[PSC_VOLTAGE_IN] = -2;

	info->m[PSC_VOLTAGE_OUT] = 19199;
	info->b[PSC_VOLTAGE_OUT] = 0;
	info->R[PSC_VOLTAGE_OUT] = -2;

	// Current coefficients: scale by shunt resistor
	// Formula: I = Vsense / Rshunt
	info->m[PSC_CURRENT_OUT] = 807 * shunt / 1000;
	info->b[PSC_CURRENT_OUT] = 20475;
	info->R[PSC_CURRENT_OUT] = -1;

	return pmbus_do_probe(client, info);
}
```

**Direct format formula**:
```
real_value = (register_value * m - b) * 10^R
```

### Multi-Page Device

```c
static int ltc2978_probe(struct i2c_client *client)
{
	struct pmbus_driver_info *info;
	int i;

	info = devm_kzalloc(&client->dev, sizeof(*info), GFP_KERNEL);
	if (!info)
		return -ENOMEM;

	info->pages = 8;  // 8 voltage outputs
	info->format[PSC_VOLTAGE_IN] = linear;
	info->format[PSC_VOLTAGE_OUT] = linear;

	// Page 0: VIN, VOUT, TEMP
	info->func[0] = PMBUS_HAVE_VIN | PMBUS_HAVE_STATUS_INPUT |
	                PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT |
	                PMBUS_HAVE_TEMP | PMBUS_HAVE_STATUS_TEMP;

	// Pages 1-7: VOUT only
	for (i = 1; i < info->pages; i++)
		info->func[i] = PMBUS_HAVE_VOUT | PMBUS_HAVE_STATUS_VOUT;

	return pmbus_do_probe(client, info);
}
```

### Virtual Command Handling

```c
static int adm1275_read_word_data(struct i2c_client *client, int page,
                                  int phase, int reg)
{
	int ret;

	switch (reg) {
	case PMBUS_VIRT_READ_IOUT_MAX:
		// Map virtual command to manufacturer register
		ret = pmbus_read_word_data(client, 0, 0xff, ADM1275_PEAK_IOUT);
		break;

	case PMBUS_VIRT_READ_VIN_MAX:
		ret = pmbus_read_word_data(client, 0, 0xff, ADM1275_PEAK_VIN);
		break;

	case PMBUS_VIRT_RESET_IOUT_HISTORY:
	case PMBUS_VIRT_RESET_VIN_HISTORY:
		ret = 0;  // Signal supported
		break;

	default:
		ret = -ENODATA;  // MUST return -ENODATA for unsupported
		break;
	}

	return ret;
}

static int adm1275_write_word_data(struct i2c_client *client, int page,
                                   int reg, u16 word)
{
	int ret;

	switch (reg) {
	case PMBUS_VIRT_RESET_IOUT_HISTORY:
		ret = pmbus_write_word_data(client, 0, ADM1275_PEAK_IOUT, 0);
		break;

	case PMBUS_VIRT_RESET_VIN_HISTORY:
		ret = pmbus_write_word_data(client, 0, ADM1275_PEAK_VIN, 0);
		break;

	default:
		ret = -ENODATA;
		break;
	}

	return ret;
}

static int adm1275_probe(struct i2c_client *client)
{
	// ... (setup info)

	info->read_word_data = adm1275_read_word_data;
	info->write_word_data = adm1275_write_word_data;

	return pmbus_do_probe(client, info);
}
```

### Devicetree Integration

```dts
&i2c0 {
	/* ADM1275 hot-swap controller */
	adm1275@40 {
		compatible = "adi,adm1275";
		reg = <0x40>;
		shunt-resistor-micro-ohms = <1000>;  /* 1 mOhm sense resistor */
		adi,volt-curr-sample-average = <128>;  /* 128 samples averaging */
	};

	/* LTC2978 8-output supervisor */
	ltc2978@5c {
		compatible = "lltc,ltc2978";
		reg = <0x5c>;
	};

	/* ADM1266 sequencer with GPIO and blackbox */
	adm1266@42 {
		compatible = "adi,adm1266";
		reg = <0x42>;

		gpio-controller;
		#gpio-cells = <2>;
	};
};
```

## Essential Patterns

### Coefficient Calculation

For direct format, extract coefficients from datasheet:

**Example**: Datasheet says "VOUT = Code × 0.195 mV"
```
Convert to millivolts:
  VOUT(mV) = Code × 0.195

Express as direct format (mV):
  VOUT = (Code × m - b) × 10^R

Match equation:
  m = 1 / 0.195 ≈ 5.128
  To get integer: m = 5128, R = -3
  b = 0

Coefficients:
  m = 5128
  b = 0
  R = -3
```

**Shunt resistor scaling** for current:
```c
// Datasheet assumes 1 mOhm shunt
// Actual shunt from devicetree: shunt_uohm
m_actual = m_datasheet * shunt_uohm / 1000;
```

### Handling Chip Variants

```c
enum chips { adm1275, adm1276, adm1278 };

static const struct i2c_device_id adm1275_id[] = {
	{ "adm1275", adm1275 },
	{ "adm1276", adm1276 },
	{ "adm1278", adm1278 },
	{}
};

struct adm1275_data {
	enum chips id;
	bool have_pin_max;
	struct pmbus_driver_info info;
};

static int adm1275_probe(struct i2c_client *client)
{
	const struct i2c_device_id *mid = i2c_match_id(adm1275_id, client);
	struct adm1275_data *data;

	data = devm_kzalloc(&client->dev, sizeof(*data), GFP_KERNEL);
	data->id = mid->driver_data;

	// Variant-specific features
	switch (data->id) {
	case adm1275:
		data->have_pin_max = false;
		break;
	case adm1276:
	case adm1278:
		data->have_pin_max = true;
		break;
	}

	// Configure info based on variant
	// ...
}
```

### Page Switching (Multi-Page)

The PMBus core automatically handles PAGE command:

```c
// Core switches to page 2 before reading
ret = pmbus_read_word_data(client, 2, 0xff, PMBUS_READ_VOUT);

// Core optimizes: no redundant page writes
ret = pmbus_read_word_data(client, 2, 0xff, PMBUS_READ_IOUT);  // Still on page 2
```

### PMBus Helper Functions

```c
// Read byte
int pmbus_read_byte_data(struct i2c_client *client, int page, u8 reg);

// Read word (with page and phase)
int pmbus_read_word_data(struct i2c_client *client, int page,
                         int phase, int reg);

// Write byte
int pmbus_write_byte(struct i2c_client *client, int page, u8 value);

// Write word
int pmbus_write_word_data(struct i2c_client *client, int page,
                          int reg, u16 word);

// Get driver info
struct pmbus_driver_info *pmbus_get_driver_info(struct i2c_client *client);
```

## Sysfs Interface

PMBus drivers expose HWMON sysfs attributes:

```bash
cd /sys/class/hwmon/hwmon*/device/

# Voltage monitoring
cat in0_input       # VIN (millivolts)
cat in1_input       # VOUT page 0 (millivolts)
cat in2_input       # VOUT page 1 (multi-page devices)
cat in1_max         # VOUT max limit
cat in1_alarm       # VOUT alarm status

# Current monitoring
cat curr1_input     # IIN (milliamps)
cat curr2_input     # IOUT (milliamps)
cat curr2_max       # IOUT max limit

# Power monitoring
cat power1_input    # PIN (microwatts)
cat power2_input    # POUT (microwatts)

# Temperature
cat temp1_input     # Temperature (millidegrees Celsius)

# Peak tracking (if supported)
cat in1_highest     # Peak VOUT
cat curr2_highest   # Peak IOUT
echo 1 > in1_reset_history  # Reset VOUT peak
```

## Key Takeaways

### PMBus Driver Checklist

- [ ] Choose data format: `linear` (standard) or `direct` (needs m/b/R)
- [ ] Set `pages` count for multi-rail devices
- [ ] Configure functionality flags per page (`PMBUS_HAVE_*`)
- [ ] For direct format: calculate m, b, R coefficients from datasheet
- [ ] Handle shunt resistor scaling for current measurements
- [ ] Implement `read_word_data` callback for virtual commands
- [ ] Return `-ENODATA` for unsupported virtual commands
- [ ] Add `MODULE_IMPORT_NS(PMBUS)` for module builds
- [ ] Test with sysfs interface and verify readings
- [ ] Enable debug to trace page switching and coefficient application

### Common Patterns

| Pattern | When to Use |
|---------|-------------|
| Linear format | Standard PMBus devices, simple setup |
| Direct format | Precise coefficients needed, non-standard scaling |
| Multi-page | Power sequencers, multi-rail PMICs |
| Virtual commands | Peak tracking, sampling config, non-standard features |
| Regulator integration | Voltage control needed by other drivers |
| GPIO integration | Power sequencers with PDIO/GPIO pins |

## Debugging Quick Tips

**Wrong readings**: Check m/b/R coefficients, shunt resistor value, voltage range config
**Virtual command errors**: Ensure callback returns `-ENODATA`, not `-EINVAL`
**Multi-page issues**: Verify `info->pages` and `info->func[i]` for each page
**Device not detected**: Check I2C address, pull-ups, SMBALERT# pin

**Enable debug**:
```bash
echo 'file pmbus_core.c +p' > /sys/kernel/debug/dynamic_debug/control
dmesg | tail -f
```

## References

- **PMBus Core API**: https://docs.kernel.org/hwmon/pmbus-core.html
- **Generic PMBus**: https://docs.kernel.org/hwmon/pmbus.html
- **HWMON Subsystem**: https://docs.kernel.org/hwmon/hwmon-kernel-api.html
- **PMBus Specification**: https://pmbus.org/ (external)
- **Header Files**:
  - `include/linux/pmbus.h` - Public PMBus API
  - `drivers/hwmon/pmbus/pmbus.h` - Internal PMBus definitions
- **Example Drivers**:
  - `drivers/hwmon/pmbus/adm1275.c` - Hot-swap controller with direct format
  - `drivers/hwmon/pmbus/ltc2978.c` - Multi-page supervisor with peak tracking
  - `drivers/hwmon/pmbus/adm1266.c` - Sequencer with GPIO and NVMEM
