---
name: linux-gpio
description: Complete guide to Linux GPIO subsystem for GPIO controllers and consumers. Use when implementing GPIO controller drivers or using GPIOs in device drivers.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: gpio
  tags:
    - gpio
    - gpio-controller
    - gpio-chip
    - gpiod
    - gpio-consumer
    - irq-chip
    - gpio-expander
    - i2c-gpio
    - spi-gpio
    - regmap-gpio
  dependencies:
    - linux-i2c-controller
    - linux-spi-controller
    - linux-regulator
    - linux-devicetree
  learning_objectives:
    - Implement GPIO controller drivers with struct gpio_chip
    - Use descriptor-based GPIO consumer API (gpiod_* functions)
    - Integrate IRQ chip support for GPIO interrupts
    - Work with I2C and SPI GPIO expanders
    - Configure electrical properties (pull-up/down, debounce, open-drain)
    - Handle hierarchical IRQ domains for GPIO controllers
    - Use regmap for GPIO register access in bus-connected expanders
    - Debug GPIO controller and consumer issues
---

# Linux GPIO Subsystem

Quick-start guide for implementing GPIO controller drivers and using GPIOs in device drivers.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User mentions: "implement GPIO controller", "GPIO driver", "gpio_chip", "I2C GPIO expander", "SPI GPIO expander"
- Questions about: direction_input, direction_output, get, set, get_multiple, set_multiple callbacks
- User asks: "how to implement", "step by step", "create GPIO driver", "PCA953x", "bank-based addressing"
- Topics: regmap GPIO, register caching, IRQ chip integration, nested IRQs, bus_lock pattern

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "DTS", "gpio-controller", "#gpio-cells"
- Questions about: GPIO consumer binding, gpio-line-names, GPIO flags (GPIO_ACTIVE_LOW, GPIO_OPEN_DRAIN)
- User asks: "how to specify GPIO in DT", "devicetree example", "gpio-hog"

**Triggers to read reference/api-usage.md**:
- User mentions: "use GPIO", "consumer driver", "gpiod_get", "gpiod_set_value"
- Questions about: descriptor-based API, devm_gpiod_get, gpiod_direction_input, gpiod_direction_output
- User asks: "how to use GPIO in driver", "read GPIO", "write GPIO", "GPIO interrupt", "gpiod_to_irq"
- Topics: GPIO flags (GPIOD_OUT_HIGH, GPIOD_IN), gpiod_set_value_cansleep, GPIO polarity handling

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "common patterns", "GPIO checklist", "what to avoid"
- Questions about: locking strategy, spinlock vs mutex, register caching, set output before direction
- Topics: can_sleep flag, IRQCHIP_IMMUTABLE, GPIOCHIP_IRQ_RESOURCE_HELPERS, line names

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "GPIO stuck", "interrupt not firing", "wrong value"
- Questions about: debugfs, sysfs, ftrace, dynamic debug, GPIO tracing
- User says: "troubleshoot", "diagnose", "GPIO error", "can't read GPIO", "can't set GPIO"
- Topics: /sys/kernel/debug/gpio, /sys/class/gpio (legacy), CONFIG_DEBUG_GPIO

---

## When to Use This Skill

- Implementing GPIO controller drivers for SoC GPIO blocks or GPIO expanders
- Using GPIOs in device drivers (reset lines, chip selects, power controls, LEDs, buttons)
- Adding IRQ chip support to GPIO controllers
- Working with I2C or SPI GPIO expanders (PCA953x, PCF857x, MCP23xxx)
- Debugging GPIO controller or consumer issues

## What is the Linux GPIO Subsystem?

The Linux GPIO subsystem provides infrastructure for:
- **GPIO Controllers** (providers): Drivers that control GPIO hardware
- **GPIO Consumers** (clients): Device drivers that use GPIOs

### Two-Sided API

```
┌─────────────────────────────────────────────────────────────┐
│                    GPIO Consumer Drivers                     │
│            (Device drivers using GPIOs)                      │
│                                                              │
│  gpiod_get(), gpiod_set_value(), gpiod_direction_output()  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Descriptor-based Consumer API
┌──────────────────────▼──────────────────────────────────────┐
│                     GPIO Core                                │
│         (gpiolib in drivers/gpio/gpiolib.c)                 │
│                                                              │
│  - GPIO descriptor management and lookup                     │
│  - Devicetree/ACPI GPIO parsing                             │
│  - IRQ domain management for GPIO interrupts                │
│  - sysfs/debugfs interfaces                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ GPIO Chip Provider API
┌──────────────────────▼──────────────────────────────────────┐
│                GPIO Controller Drivers                       │
│           (GPIO hardware drivers)                            │
│                                                              │
│  struct gpio_chip: direction_input/output, get, set, ...    │
└──────────────────────────────────────────────────────────────┘
```

## Quick Reference

### Key Structures

| Structure | Purpose | Location |
|-----------|---------|----------|
| `struct gpio_chip` | GPIO controller (provider side) | `<linux/gpio/driver.h>` |
| `struct gpio_desc` | GPIO descriptor (consumer side) | `<linux/gpio/consumer.h>` |
| `struct gpio_irq_chip` | IRQ chip integration for GPIOs | `<linux/gpio/driver.h>` |

### GPIO Controller Callbacks

| Callback | Purpose | Required? |
|----------|---------|-----------|
| `direction_input` | Set GPIO as input | Yes |
| `direction_output` | Set GPIO as output with value | Yes |
| `get` | Read GPIO value | Yes |
| `set` | Write GPIO value | Yes |
| `get_direction` | Query current direction | Recommended |
| `get_multiple` | Read multiple GPIOs efficiently | Optional |
| `set_multiple` | Write multiple GPIOs efficiently | Optional |
| `set_config` | Configure pull-up/down, debounce, etc. | Optional |
| `request` | Allocate GPIO resources | Optional |
| `free` | Release GPIO resources | Optional |

### GPIO Consumer API (gpiod_*)

| Function | Purpose |
|----------|---------|
| `devm_gpiod_get(dev, con_id, flags)` | Get GPIO descriptor (managed) |
| `devm_gpiod_get_optional(dev, con_id, flags)` | Get optional GPIO (returns NULL if missing) |
| `gpiod_direction_input(desc)` | Set GPIO as input |
| `gpiod_direction_output(desc, value)` | Set GPIO as output with initial value |
| `gpiod_get_value(desc)` | Read GPIO value (fast path, MMIO only) |
| `gpiod_set_value(desc, value)` | Write GPIO value (fast path, MMIO only) |
| `gpiod_get_value_cansleep(desc)` | Read GPIO value (may sleep, I2C/SPI safe) |
| `gpiod_set_value_cansleep(desc, value)` | Write GPIO value (may sleep, I2C/SPI safe) |
| `gpiod_to_irq(desc)` | Get IRQ number from GPIO |

### GPIO Flags (Consumer API)

| Flag | Purpose |
|------|---------|
| `GPIOD_IN` | Request as input |
| `GPIOD_OUT_LOW` | Request as output, initial value = 0 |
| `GPIOD_OUT_HIGH` | Request as output, initial value = 1 |
| `GPIOD_OUT_LOW_OPEN_DRAIN` | Output low, open-drain |
| `GPIOD_OUT_HIGH_OPEN_DRAIN` | Output high, open-drain |

### Devicetree GPIO Flags

| Flag | Value | Purpose |
|------|-------|---------|
| `GPIO_ACTIVE_HIGH` | 0 | Active high (default) |
| `GPIO_ACTIVE_LOW` | 1 | Active low (invert logic) |
| `GPIO_OPEN_DRAIN` | 2 | Open-drain output |
| `GPIO_OPEN_SOURCE` | 4 | Open-source output |
| `GPIO_PULL_UP` | 8 | Enable pull-up resistor |
| `GPIO_PULL_DOWN` | 16 | Enable pull-down resistor |

## Quick Start

### GPIO Controller Driver Pattern

```c
#include <linux/gpio/driver.h>
#include <linux/platform_device.h>
#include <linux/module.h>

struct mygpio_priv {
	void __iomem *base;
	struct gpio_chip gc;
	raw_spinlock_t lock;
};

static int mygpio_direction_input(struct gpio_chip *gc, unsigned int offset)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	unsigned long flags;
	u32 dir;

	raw_spin_lock_irqsave(&priv->lock, flags);
	dir = readl(priv->base + DIR_REG);
	dir |= BIT(offset);  // 1 = input
	writel(dir, priv->base + DIR_REG);
	raw_spin_unlock_irqrestore(&priv->lock, flags);

	return 0;
}

static int mygpio_direction_output(struct gpio_chip *gc, unsigned int offset,
				   int value)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	unsigned long flags;
	u32 dir, data;

	raw_spin_lock_irqsave(&priv->lock, flags);

	// IMPORTANT: Set output value BEFORE changing direction
	data = readl(priv->base + DATA_REG);
	if (value)
		data |= BIT(offset);
	else
		data &= ~BIT(offset);
	writel(data, priv->base + DATA_REG);

	// Then set direction to output
	dir = readl(priv->base + DIR_REG);
	dir &= ~BIT(offset);  // 0 = output
	writel(dir, priv->base + DIR_REG);

	raw_spin_unlock_irqrestore(&priv->lock, flags);

	return 0;
}

static int mygpio_get(struct gpio_chip *gc, unsigned int offset)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);

	return !!(readl(priv->base + DATA_REG) & BIT(offset));
}

static void mygpio_set(struct gpio_chip *gc, unsigned int offset, int value)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	unsigned long flags;
	u32 data;

	raw_spin_lock_irqsave(&priv->lock, flags);
	data = readl(priv->base + DATA_REG);
	if (value)
		data |= BIT(offset);
	else
		data &= ~BIT(offset);
	writel(data, priv->base + DATA_REG);
	raw_spin_unlock_irqrestore(&priv->lock, flags);
}

static int mygpio_probe(struct platform_device *pdev)
{
	struct mygpio_priv *priv;
	int ret;

	priv = devm_kzalloc(&pdev->dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	priv->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(priv->base))
		return PTR_ERR(priv->base);

	raw_spin_lock_init(&priv->lock);

	// Initialize GPIO chip
	priv->gc.label = "mygpio";
	priv->gc.parent = &pdev->dev;
	priv->gc.owner = THIS_MODULE;
	priv->gc.direction_input = mygpio_direction_input;
	priv->gc.direction_output = mygpio_direction_output;
	priv->gc.get = mygpio_get;
	priv->gc.set = mygpio_set;
	priv->gc.base = -1;  // Dynamic allocation
	priv->gc.ngpio = 32;
	priv->gc.can_sleep = false;  // MMIO access, no sleep

	// Register GPIO chip
	ret = devm_gpiochip_add_data(&pdev->dev, &priv->gc, priv);
	if (ret)
		return ret;

	dev_info(&pdev->dev, "GPIO controller registered with %d GPIOs\n",
		 priv->gc.ngpio);

	return 0;
}

static const struct of_device_id mygpio_of_match[] = {
	{ .compatible = "vendor,mygpio" },
	{ }
};
MODULE_DEVICE_TABLE(of, mygpio_of_match);

static struct platform_driver mygpio_driver = {
	.driver = {
		.name = "mygpio",
		.of_match_table = mygpio_of_match,
	},
	.probe = mygpio_probe,
};
module_platform_driver(mygpio_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("My GPIO Controller Driver");
```

### GPIO Consumer Driver Pattern

```c
#include <linux/gpio/consumer.h>
#include <linux/platform_device.h>
#include <linux/module.h>

struct mydev_priv {
	struct gpio_desc *reset_gpio;
	struct gpio_desc *enable_gpio;
};

static int mydev_probe(struct platform_device *pdev)
{
	struct mydev_priv *priv;
	int ret;

	priv = devm_kzalloc(&pdev->dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	// Get required GPIO (returns error if missing)
	priv->reset_gpio = devm_gpiod_get(&pdev->dev, "reset", GPIOD_OUT_HIGH);
	if (IS_ERR(priv->reset_gpio))
		return dev_err_probe(&pdev->dev, PTR_ERR(priv->reset_gpio),
				     "Failed to get reset GPIO\n");

	// Get optional GPIO (returns NULL if missing, not an error)
	priv->enable_gpio = devm_gpiod_get_optional(&pdev->dev, "enable",
						    GPIOD_OUT_LOW);
	if (IS_ERR(priv->enable_gpio))
		return dev_err_probe(&pdev->dev, PTR_ERR(priv->enable_gpio),
				     "Failed to get enable GPIO\n");

	// Reset device
	gpiod_set_value_cansleep(priv->reset_gpio, 0);  // Assert reset
	msleep(10);
	gpiod_set_value_cansleep(priv->reset_gpio, 1);  // De-assert reset
	msleep(10);

	// Enable device if GPIO is present
	if (priv->enable_gpio)
		gpiod_set_value_cansleep(priv->enable_gpio, 1);

	platform_set_drvdata(pdev, priv);

	dev_info(&pdev->dev, "Device initialized\n");

	return 0;
}

static const struct of_device_id mydev_of_match[] = {
	{ .compatible = "vendor,mydev" },
	{ }
};
MODULE_DEVICE_TABLE(of, mydev_of_match);

static struct platform_driver mydev_driver = {
	.driver = {
		.name = "mydev",
		.of_match_table = mydev_of_match,
	},
	.probe = mydev_probe,
};
module_platform_driver(mydev_driver);

MODULE_LICENSE("GPL");
```

### Devicetree Example

```dts
// GPIO controller node
gpio0: gpio@40000000 {
	compatible = "vendor,mygpio";
	reg = <0x40000000 0x1000>;
	gpio-controller;
	#gpio-cells = <2>;  // <gpio_number flags>
	ngpios = <32>;
	gpio-line-names = "GPIO0", "GPIO1", "GPIO2", "GPIO3",
			  "SPI_CS", "I2C_SCL", "I2C_SDA", "UART_TX";
};

// GPIO consumer node
mydev@50000000 {
	compatible = "vendor,mydev";
	reg = <0x50000000 0x1000>;

	// reset-gpios: GPIO 5, active low
	reset-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;

	// enable-gpios: GPIO 10, active high
	enable-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
};
```

## Essential Patterns

### Locking Strategy

| GPIO Type | Locking | Reason |
|-----------|---------|--------|
| MMIO GPIO | `raw_spinlock_t` | Fast path, atomic context safe |
| I2C/SPI GPIO | `struct mutex` | Bus operations may sleep |

**MMIO GPIO**:
```c
struct mygpio_priv {
	raw_spinlock_t lock;
	// ...
};

// In callbacks
raw_spin_lock_irqsave(&priv->lock, flags);
// Modify registers
raw_spin_unlock_irqrestore(&priv->lock, flags);
```

**I2C/SPI GPIO**:
```c
struct mygpio_priv {
	struct mutex lock;
	struct i2c_client *client;
	// ...
};

// In callbacks
mutex_lock(&priv->lock);
// I2C/SPI operations
mutex_unlock(&priv->lock);
```

### Set can_sleep Flag Correctly

```c
// MMIO GPIO (no sleep)
priv->gc.can_sleep = false;  // gpiod_set_value() is safe

// I2C/SPI GPIO (may sleep)
priv->gc.can_sleep = true;   // Must use gpiod_set_value_cansleep()
```

### Set Output Value Before Direction

**IMPORTANT**: Always set the output value BEFORE changing direction to output.

```c
static int mygpio_direction_output(struct gpio_chip *gc, unsigned offset, int value)
{
	// CORRECT: Set value first
	data = readl(base + DATA);
	if (value)
		data |= BIT(offset);
	else
		data &= ~BIT(offset);
	writel(data, base + DATA);

	// Then set direction
	dir = readl(base + DIR);
	dir &= ~BIT(offset);  // 0 = output
	writel(dir, base + DIR);

	return 0;
}
```

### IRQ Chip Integration (Modern Pattern)

```c
#include <linux/gpio/driver.h>
#include <linux/interrupt.h>

static void mygpio_irq_mask(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	// Mask interrupt for GPIO d->hwirq
}

static void mygpio_irq_unmask(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	// Unmask interrupt for GPIO d->hwirq
}

static struct irq_chip mygpio_irq_chip = {
	.name = "mygpio",
	.irq_mask = mygpio_irq_mask,
	.irq_unmask = mygpio_irq_unmask,
	.flags = IRQCHIP_IMMUTABLE,
	GPIOCHIP_IRQ_RESOURCE_HELPERS,
};

static int mygpio_probe(struct platform_device *pdev)
{
	struct gpio_irq_chip *girq;
	int parent_irq;

	// ... setup GPIO chip ...

	parent_irq = platform_get_irq(pdev, 0);
	if (parent_irq < 0)
		return parent_irq;

	girq = &priv->gc.irq;
	gpio_irq_chip_set_chip(girq, &mygpio_irq_chip);
	girq->parent_handler = mygpio_irq_handler;
	girq->num_parents = 1;
	girq->parents = devm_kcalloc(&pdev->dev, 1, sizeof(*girq->parents),
				     GFP_KERNEL);
	if (!girq->parents)
		return -ENOMEM;
	girq->parents[0] = parent_irq;
	girq->default_type = IRQ_TYPE_NONE;
	girq->handler = handle_bad_irq;

	return devm_gpiochip_add_data(&pdev->dev, &priv->gc, priv);
}
```

## Key Takeaways

### GPIO Controller Checklist

- [ ] Implement required callbacks: `direction_input`, `direction_output`, `get`, `set`
- [ ] Set `can_sleep = false` for MMIO, `true` for I2C/SPI
- [ ] Use `raw_spinlock_t` for MMIO, `mutex` for I2C/SPI
- [ ] Set output value BEFORE changing direction to output
- [ ] Use `devm_gpiochip_add_data()` for automatic cleanup
- [ ] Set `gc.base = -1` for dynamic GPIO number allocation
- [ ] Provide `gpio-line-names` in devicetree for debuggability
- [ ] Add IRQ chip support if hardware supports GPIO interrupts
- [ ] Use `IRQCHIP_IMMUTABLE` and `GPIOCHIP_IRQ_RESOURCE_HELPERS`

### GPIO Consumer Checklist

- [ ] Use descriptor-based API (`gpiod_*`, not legacy GPIO numbers)
- [ ] Use `devm_gpiod_get()` or `devm_gpiod_get_optional()`
- [ ] Specify initial direction/value in flags parameter
- [ ] Use `gpiod_set_value()` for MMIO GPIOs
- [ ] Use `gpiod_set_value_cansleep()` for I2C/SPI GPIOs
- [ ] Handle GPIO polarity via devicetree flags (GPIO_ACTIVE_LOW)
- [ ] Use `dev_err_probe()` for deferred probe handling
- [ ] Add devicetree bindings with `<con_id>-gpios` properties

## References

- **Kernel Documentation**: `Documentation/driver-api/gpio/`
- **GPIO Driver API**: `Documentation/driver-api/gpio/driver.rst`
- **GPIO Consumer API**: `Documentation/driver-api/gpio/consumer.rst`
- **Header Files**:
  - `include/linux/gpio/driver.h` - GPIO controller API
  - `include/linux/gpio/consumer.h` - GPIO consumer API
  - `include/dt-bindings/gpio/gpio.h` - Devicetree GPIO flags
- **Example Drivers**:
  - `drivers/gpio/gpio-pca953x.c` - I2C GPIO expander
  - `drivers/gpio/gpio-74x164.c` - SPI GPIO expander
  - `drivers/gpio/gpio-mmio.c` - MMIO GPIO controller
