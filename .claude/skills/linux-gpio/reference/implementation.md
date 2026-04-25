# GPIO Controller Driver Implementation

Detailed guide for implementing GPIO controller drivers in Linux kernel. This covers basic GPIO controllers, IRQ chip integration, I2C/SPI GPIO expanders, and register access patterns.

## Basic GPIO Controller

Simple memory-mapped GPIO controller:

```c
#include <linux/gpio/driver.h>
#include <linux/platform_device.h>
#include <linux/module.h>

#define MYGPIO_DATA     0x00    // Data register (read input, write output)
#define MYGPIO_DIR      0x04    // Direction register (1=input, 0=output)
#define MYGPIO_NGPIO    32      // Number of GPIO lines

struct mygpio_priv {
	void __iomem *base;
	struct gpio_chip gc;
	raw_spinlock_t lock;        // Protect concurrent access
};

static int mygpio_get_direction(struct gpio_chip *gc, unsigned int offset)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	u32 dir;

	dir = readl(priv->base + MYGPIO_DIR);

	if (dir & BIT(offset))
		return GPIO_LINE_DIRECTION_IN;
	else
		return GPIO_LINE_DIRECTION_OUT;
}

static int mygpio_direction_input(struct gpio_chip *gc, unsigned int offset)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	unsigned long flags;
	u32 dir;

	raw_spin_lock_irqsave(&priv->lock, flags);
	dir = readl(priv->base + MYGPIO_DIR);
	dir |= BIT(offset);                 // Set bit = input
	writel(dir, priv->base + MYGPIO_DIR);
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

	// Set output value first
	data = readl(priv->base + MYGPIO_DATA);
	if (value)
		data |= BIT(offset);
	else
		data &= ~BIT(offset);
	writel(data, priv->base + MYGPIO_DATA);

	// Then set direction to output
	dir = readl(priv->base + MYGPIO_DIR);
	dir &= ~BIT(offset);                // Clear bit = output
	writel(dir, priv->base + MYGPIO_DIR);

	raw_spin_unlock_irqrestore(&priv->lock, flags);

	return 0;
}

static int mygpio_get(struct gpio_chip *gc, unsigned int offset)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);

	return !!(readl(priv->base + MYGPIO_DATA) & BIT(offset));
}

static void mygpio_set(struct gpio_chip *gc, unsigned int offset, int value)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	unsigned long flags;
	u32 data;

	raw_spin_lock_irqsave(&priv->lock, flags);
	data = readl(priv->base + MYGPIO_DATA);
	if (value)
		data |= BIT(offset);
	else
		data &= ~BIT(offset);
	writel(data, priv->base + MYGPIO_DATA);
	raw_spin_unlock_irqrestore(&priv->lock, flags);
}

// Optimize multiple GPIO operations in one transaction
static int mygpio_get_multiple(struct gpio_chip *gc, unsigned long *mask,
			       unsigned long *bits)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);

	*bits = readl(priv->base + MYGPIO_DATA);
	return 0;
}

static void mygpio_set_multiple(struct gpio_chip *gc, unsigned long *mask,
				unsigned long *bits)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	unsigned long flags;
	u32 data;

	raw_spin_lock_irqsave(&priv->lock, flags);
	data = readl(priv->base + MYGPIO_DATA);
	data = (data & ~(*mask)) | (*bits & *mask);
	writel(data, priv->base + MYGPIO_DATA);
	raw_spin_unlock_irqrestore(&priv->lock, flags);
}

static int mygpio_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct mygpio_priv *priv;
	struct gpio_chip *gc;
	int ret;

	priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	priv->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(priv->base))
		return PTR_ERR(priv->base);

	raw_spin_lock_init(&priv->lock);

	gc = &priv->gc;
	gc->label = "mygpio";
	gc->parent = dev;
	gc->owner = THIS_MODULE;
	gc->base = -1;                      // Dynamic GPIO number allocation
	gc->ngpio = MYGPIO_NGPIO;
	gc->get_direction = mygpio_get_direction;
	gc->direction_input = mygpio_direction_input;
	gc->direction_output = mygpio_direction_output;
	gc->get = mygpio_get;
	gc->set = mygpio_set;
	gc->get_multiple = mygpio_get_multiple;
	gc->set_multiple = mygpio_set_multiple;
	gc->can_sleep = false;              // MMIO operations don't sleep

	ret = devm_gpiochip_add_data(dev, gc, priv);
	if (ret)
		return dev_err_probe(dev, ret, "Failed to add GPIO chip\n");

	platform_set_drvdata(pdev, priv);

	dev_info(dev, "GPIO controller registered with %d GPIOs\n", gc->ngpio);
	return 0;
}

static const struct of_device_id mygpio_of_match[] = {
	{ .compatible = "vendor,mygpio" },
	{ }
};
MODULE_DEVICE_TABLE(of, mygpio_of_match);

static struct platform_driver mygpio_driver = {
	.probe = mygpio_probe,
	.driver = {
		.name = "mygpio",
		.of_match_table = mygpio_of_match,
	},
};
module_platform_driver(mygpio_driver);

MODULE_DESCRIPTION("My GPIO Controller Driver");
MODULE_LICENSE("GPL");
```

**Key Patterns**:
- Use `devm_gpiochip_add_data()` to register GPIO chip with automatic cleanup
- Always set output value BEFORE changing direction to output (prevents glitches)
- Use spinlock for MMIO GPIO controllers (fast, non-sleeping)
- Set `can_sleep = false` for MMIO, `can_sleep = true` for I2C/SPI
- Implement `get_multiple/set_multiple` for efficiency when possible

### GPIO Chip with Electrical Configuration

Support pull-up/down, debounce, open-drain:

```c
#include <linux/pinctrl/consumer.h>

#define MYGPIO_PULL     0x08    // Pull-up/down enable (1=enabled)
#define MYGPIO_PULL_SEL 0x0C    // Pull direction (1=pull-up, 0=pull-down)
#define MYGPIO_DEBOUNCE 0x10    // Debounce enable
#define MYGPIO_OPENDRAIN 0x14   // Open-drain enable

static int mygpio_set_config(struct gpio_chip *gc, unsigned int offset,
			     unsigned long config)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	enum pin_config_param param = pinconf_to_config_param(config);
	u32 arg = pinconf_to_config_argument(config);
	unsigned long flags;
	u32 reg;

	switch (param) {
	case PIN_CONFIG_BIAS_DISABLE:
		raw_spin_lock_irqsave(&priv->lock, flags);
		reg = readl(priv->base + MYGPIO_PULL);
		reg &= ~BIT(offset);            // Disable pull
		writel(reg, priv->base + MYGPIO_PULL);
		raw_spin_unlock_irqrestore(&priv->lock, flags);
		break;

	case PIN_CONFIG_BIAS_PULL_UP:
		raw_spin_lock_irqsave(&priv->lock, flags);
		// Set pull direction to up
		reg = readl(priv->base + MYGPIO_PULL_SEL);
		reg |= BIT(offset);
		writel(reg, priv->base + MYGPIO_PULL_SEL);
		// Enable pull
		reg = readl(priv->base + MYGPIO_PULL);
		reg |= BIT(offset);
		writel(reg, priv->base + MYGPIO_PULL);
		raw_spin_unlock_irqrestore(&priv->lock, flags);
		break;

	case PIN_CONFIG_BIAS_PULL_DOWN:
		raw_spin_lock_irqsave(&priv->lock, flags);
		// Set pull direction to down
		reg = readl(priv->base + MYGPIO_PULL_SEL);
		reg &= ~BIT(offset);
		writel(reg, priv->base + MYGPIO_PULL_SEL);
		// Enable pull
		reg = readl(priv->base + MYGPIO_PULL);
		reg |= BIT(offset);
		writel(reg, priv->base + MYGPIO_PULL);
		raw_spin_unlock_irqrestore(&priv->lock, flags);
		break;

	case PIN_CONFIG_INPUT_DEBOUNCE:
		// arg is debounce time in microseconds
		raw_spin_lock_irqsave(&priv->lock, flags);
		reg = readl(priv->base + MYGPIO_DEBOUNCE);
		if (arg > 0)
			reg |= BIT(offset);     // Enable debounce
		else
			reg &= ~BIT(offset);    // Disable debounce
		writel(reg, priv->base + MYGPIO_DEBOUNCE);
		raw_spin_unlock_irqrestore(&priv->lock, flags);
		break;

	case PIN_CONFIG_DRIVE_OPEN_DRAIN:
		raw_spin_lock_irqsave(&priv->lock, flags);
		reg = readl(priv->base + MYGPIO_OPENDRAIN);
		reg |= BIT(offset);
		writel(reg, priv->base + MYGPIO_OPENDRAIN);
		raw_spin_unlock_irqrestore(&priv->lock, flags);
		break;

	case PIN_CONFIG_DRIVE_PUSH_PULL:
		raw_spin_lock_irqsave(&priv->lock, flags);
		reg = readl(priv->base + MYGPIO_OPENDRAIN);
		reg &= ~BIT(offset);
		writel(reg, priv->base + MYGPIO_OPENDRAIN);
		raw_spin_unlock_irqrestore(&priv->lock, flags);
		break;

	default:
		return -ENOTSUPP;
	}

	return 0;
}

// In probe():
// gc->set_config = mygpio_set_config;
```

Common electrical configurations:
- `PIN_CONFIG_BIAS_DISABLE`: Disable pull-up/pull-down
- `PIN_CONFIG_BIAS_PULL_UP`: Enable pull-up resistor
- `PIN_CONFIG_BIAS_PULL_DOWN`: Enable pull-down resistor
- `PIN_CONFIG_INPUT_DEBOUNCE`: Debounce input (argument is microseconds)
- `PIN_CONFIG_DRIVE_OPEN_DRAIN`: Configure output as open-drain
- `PIN_CONFIG_DRIVE_PUSH_PULL`: Configure output as push-pull
- `PIN_CONFIG_DRIVE_STRENGTH`: Set output drive strength (argument is mA)

## IRQ Chip Integration for GPIO Controllers

GPIO controllers often generate interrupts on pin state changes.

### IRQ Chip Setup

```c
#include <linux/gpio/driver.h>
#include <linux/interrupt.h>
#include <linux/irq.h>

#define MYGPIO_IRQ_EN     0x20    // Interrupt enable register
#define MYGPIO_IRQ_RISING 0x24    // Rising edge interrupt enable
#define MYGPIO_IRQ_FALLING 0x28   // Falling edge interrupt enable
#define MYGPIO_IRQ_STATUS 0x2C    // Interrupt status (write 1 to clear)

struct mygpio_priv {
	void __iomem *base;
	struct gpio_chip gc;
	raw_spinlock_t lock;
	int irq;                      // Parent IRQ from hardware
	u32 irq_enabled;              // Bitmask of enabled interrupts
	u32 irq_rising;               // Bitmask of rising edge interrupts
	u32 irq_falling;              // Bitmask of falling edge interrupts
};

static void mygpio_irq_mask(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	irq_hw_number_t hwirq = irqd_to_hwirq(d);

	priv->irq_enabled &= ~BIT(hwirq);
	gpiochip_disable_irq(gc, hwirq);    // Required for IRQCHIP_IMMUTABLE
}

static void mygpio_irq_unmask(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	irq_hw_number_t hwirq = irqd_to_hwirq(d);

	gpiochip_enable_irq(gc, hwirq);     // Required for IRQCHIP_IMMUTABLE
	priv->irq_enabled |= BIT(hwirq);
}

static int mygpio_irq_set_type(struct irq_data *d, unsigned int type)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	irq_hw_number_t hwirq = irqd_to_hwirq(d);

	// GPIO interrupts only support edge triggering
	if (!(type & IRQ_TYPE_EDGE_BOTH))
		return -EINVAL;

	if (type & IRQ_TYPE_EDGE_RISING)
		priv->irq_rising |= BIT(hwirq);
	else
		priv->irq_rising &= ~BIT(hwirq);

	if (type & IRQ_TYPE_EDGE_FALLING)
		priv->irq_falling |= BIT(hwirq);
	else
		priv->irq_falling &= ~BIT(hwirq);

	return 0;
}

static void mygpio_irq_bus_sync_unlock(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	unsigned long flags;

	// Synchronize cached IRQ configuration to hardware
	raw_spin_lock_irqsave(&priv->lock, flags);
	writel(priv->irq_enabled, priv->base + MYGPIO_IRQ_EN);
	writel(priv->irq_rising, priv->base + MYGPIO_IRQ_RISING);
	writel(priv->irq_falling, priv->base + MYGPIO_IRQ_FALLING);
	raw_spin_unlock_irqrestore(&priv->lock, flags);
}

static const struct irq_chip mygpio_irq_chip = {
	.name = "mygpio-irq",
	.irq_mask = mygpio_irq_mask,
	.irq_unmask = mygpio_irq_unmask,
	.irq_set_type = mygpio_irq_set_type,
	.irq_bus_sync_unlock = mygpio_irq_bus_sync_unlock,
	.flags = IRQCHIP_IMMUTABLE,
	GPIOCHIP_IRQ_RESOURCE_HELPERS,      // Sets .irq_enable/.irq_disable
};

static irqreturn_t mygpio_irq_handler(int irq, void *data)
{
	struct mygpio_priv *priv = data;
	unsigned long status;
	int offset;

	// Read and clear interrupt status
	status = readl(priv->base + MYGPIO_IRQ_STATUS);
	writel(status, priv->base + MYGPIO_IRQ_STATUS);  // Write 1 to clear

	// Handle each pending interrupt
	for_each_set_bit(offset, &status, priv->gc.ngpio) {
		int virq = irq_find_mapping(priv->gc.irq.domain, offset);

		if (virq)
			generic_handle_irq(virq);
	}

	return status ? IRQ_HANDLED : IRQ_NONE;
}

static int mygpio_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct mygpio_priv *priv;
	struct gpio_chip *gc;
	struct gpio_irq_chip *girq;
	int ret;

	priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	priv->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(priv->base))
		return PTR_ERR(priv->base);

	priv->irq = platform_get_irq(pdev, 0);
	if (priv->irq < 0)
		return priv->irq;

	raw_spin_lock_init(&priv->lock);

	gc = &priv->gc;
	gc->label = "mygpio";
	gc->parent = dev;
	gc->owner = THIS_MODULE;
	gc->base = -1;
	gc->ngpio = MYGPIO_NGPIO;
	gc->get_direction = mygpio_get_direction;
	gc->direction_input = mygpio_direction_input;
	gc->direction_output = mygpio_direction_output;
	gc->get = mygpio_get;
	gc->set = mygpio_set;
	gc->can_sleep = false;

	// Setup IRQ chip integration
	girq = &gc->irq;
	gpio_irq_chip_set_chip(girq, &mygpio_irq_chip);
	girq->parent_handler = NULL;        // We use request_irq instead
	girq->num_parents = 0;
	girq->parents = NULL;
	girq->default_type = IRQ_TYPE_NONE;
	girq->handler = handle_simple_irq;  // Use handle_edge_irq for edge-only

	ret = devm_request_irq(dev, priv->irq, mygpio_irq_handler,
			       IRQF_SHARED, dev_name(dev), priv);
	if (ret)
		return dev_err_probe(dev, ret, "Failed to request IRQ\n");

	ret = devm_gpiochip_add_data(dev, gc, priv);
	if (ret)
		return dev_err_probe(dev, ret, "Failed to add GPIO chip\n");

	return 0;
}
```

**IRQ Chip Key Points**:
- Use `IRQCHIP_IMMUTABLE` flag (required for new drivers)
- Include `GPIOCHIP_IRQ_RESOURCE_HELPERS` macro for .irq_enable/.irq_disable
- Call `gpiochip_disable_irq/gpiochip_enable_irq` in mask/unmask for immutable chips
- Use `generic_handle_irq()` in hardirq handler
- Set `girq->handler` to `handle_simple_irq` or `handle_edge_irq`
- For I2C/SPI GPIO expanders, use nested threaded IRQ handler (see PCA953x example below)

### Nested Threaded IRQ Handler (I2C/SPI GPIO Expanders)

For slow-bus GPIO expanders that can't read status in hardirq context:

```c
static irqreturn_t pca953x_irq_handler(int irq, void *devid)
{
	struct pca953x_chip *chip = devid;
	struct gpio_chip *gc = &chip->gpio_chip;
	DECLARE_BITMAP(pending, MAX_LINE);
	int level;
	bool ret;

	// Read pending interrupts (this may sleep for I2C)
	scoped_guard(mutex, &chip->i2c_lock)
		ret = pca953x_irq_pending(chip, pending);

	if (ret) {
		for_each_set_bit(level, pending, gc->ngpio) {
			int nested_irq = irq_find_mapping(gc->irq.domain, level);

			if (unlikely(nested_irq <= 0)) {
				dev_warn_ratelimited(gc->parent,
						     "unmapped interrupt %d\n", level);
				continue;
			}

			// Use handle_nested_irq for threaded context
			handle_nested_irq(nested_irq);
		}
		return IRQ_HANDLED;
	}

	return IRQ_NONE;
}

// In probe:
girq->threaded = true;              // Mark as threaded
ret = devm_request_threaded_irq(dev, client->irq, NULL, pca953x_irq_handler,
				IRQF_ONESHOT | IRQF_SHARED, dev_name(dev), chip);
```

## I2C GPIO Expander Example: PCA953x Family

Complete I2C GPIO expander with regmap, IRQ chip, and pin configuration.

**From drivers/gpio/gpio-pca953x.c** (NXP/TI PCA9534/PCA9535/PCA9536/PCAL6xxx):

### Driver Structure

```c
#include <linux/gpio/driver.h>
#include <linux/i2c.h>
#include <linux/regmap.h>
#include <linux/pinctrl/consumer.h>

#define PCA953x_INPUT           0x00
#define PCA953x_OUTPUT          0x01
#define PCA953x_INVERT          0x02
#define PCA953x_DIRECTION       0x03

// PCAL extended registers (PCAL6xxx family)
#define PCAL953X_PULL_EN        0x40
#define PCAL953X_PULL_SEL       0x41
#define PCAL953X_INT_MASK       0x42
#define PCAL953X_INT_STAT       0x43
#define PCAL953X_IN_LATCH       0x44

#define BANK_SZ 8               // 8 GPIOs per register bank
#define MAX_BANK 5              // Support up to 40 GPIOs (5 banks)
#define NBANK(chip) DIV_ROUND_UP(chip->gpio_chip.ngpio, BANK_SZ)

struct pca953x_chip {
	struct i2c_client *client;
	struct gpio_chip gpio_chip;
	struct regmap *regmap;
	struct mutex i2c_lock;      // Protect I2C transactions

	unsigned long driver_data;  // Chip type and capabilities

	// IRQ support
	struct mutex irq_lock;      // Protect IRQ configuration
	DECLARE_BITMAP(irq_mask, MAX_LINE);
	DECLARE_BITMAP(irq_trig_raise, MAX_LINE);
	DECLARE_BITMAP(irq_trig_fall, MAX_LINE);
	DECLARE_BITMAP(irq_stat, MAX_LINE);

	u8 (*recalc_addr)(struct pca953x_chip *chip, int reg, int off);
};
```

### Bank-Based Register Addressing

Multi-bank GPIO expanders (16/24/40 GPIO) spread registers across multiple banks:

```c
// Calculate register address for multi-bank devices
static u8 pca953x_recalc_addr(struct pca953x_chip *chip, int reg, int off)
{
	int bank_shift = pca953x_bank_shift(chip);  // 0 for 8-GPIO, 3 for 16+
	int addr = (reg & PCAL_GPIO_MASK) << bank_shift;
	int pinctrl = (reg & PCAL_PINCTRL_MASK) << 1;
	u8 regaddr = pinctrl | addr | (off / BANK_SZ);

	return regaddr;
}

// Read registers across all banks using bitmap
static int pca953x_read_regs(struct pca953x_chip *chip, int reg,
			     unsigned long *val)
{
	u8 regaddr = chip->recalc_addr(chip, reg, 0);
	u8 value[MAX_BANK];
	int i, ret;

	// Bulk read all banks
	ret = regmap_bulk_read(chip->regmap, regaddr, value, NBANK(chip));
	if (ret < 0) {
		dev_err(&chip->client->dev, "failed reading register: %d\n", ret);
		return ret;
	}

	// Convert byte array to bitmap
	for (i = 0; i < NBANK(chip); i++)
		bitmap_set_value8(val, value[i], i * BANK_SZ);

	return 0;
}

// Write registers across all banks
static int pca953x_write_regs(struct pca953x_chip *chip, int reg,
			      unsigned long *val)
{
	u8 regaddr = chip->recalc_addr(chip, reg, 0);
	u8 value[MAX_BANK];
	int i, ret;

	// Convert bitmap to byte array
	for (i = 0; i < NBANK(chip); i++)
		value[i] = bitmap_get_value8(val, i * BANK_SZ);

	// Bulk write all banks
	ret = regmap_bulk_write(chip->regmap, regaddr, value, NBANK(chip));
	if (ret < 0) {
		dev_err(&chip->client->dev, "failed writing register: %d\n", ret);
		return ret;
	}

	return 0;
}
```

### GPIO Chip Callbacks

```c
static int pca953x_gpio_direction_input(struct gpio_chip *gc, unsigned off)
{
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	u8 dirreg = chip->recalc_addr(chip, PCA953x_DIRECTION, off);
	u8 bit = BIT(off % BANK_SZ);

	guard(mutex)(&chip->i2c_lock);

	// Set direction bit = input (1)
	return regmap_write_bits(chip->regmap, dirreg, bit, bit);
}

static int pca953x_gpio_direction_output(struct gpio_chip *gc,
					 unsigned off, int val)
{
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	u8 dirreg = chip->recalc_addr(chip, PCA953x_DIRECTION, off);
	u8 outreg = chip->recalc_addr(chip, PCA953x_OUTPUT, off);
	u8 bit = BIT(off % BANK_SZ);
	int ret;

	guard(mutex)(&chip->i2c_lock);

	// Set output value FIRST
	ret = regmap_write_bits(chip->regmap, outreg, bit, val ? bit : 0);
	if (ret)
		return ret;

	// Then set direction to output (0)
	return regmap_write_bits(chip->regmap, dirreg, bit, 0);
}

static int pca953x_gpio_get_value(struct gpio_chip *gc, unsigned off)
{
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	u8 inreg = chip->recalc_addr(chip, PCA953x_INPUT, off);
	u8 bit = BIT(off % BANK_SZ);
	u32 reg_val;
	int ret;

	scoped_guard(mutex, &chip->i2c_lock)
		ret = regmap_read(chip->regmap, inreg, &reg_val);
	if (ret < 0)
		return ret;

	return !!(reg_val & bit);
}

static void pca953x_gpio_set_value(struct gpio_chip *gc, unsigned off, int val)
{
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	u8 outreg = chip->recalc_addr(chip, PCA953x_OUTPUT, off);
	u8 bit = BIT(off % BANK_SZ);

	guard(mutex)(&chip->i2c_lock);

	regmap_write_bits(chip->regmap, outreg, bit, val ? bit : 0);
}

// Optimized multi-bit operations
static int pca953x_gpio_get_multiple(struct gpio_chip *gc,
				     unsigned long *mask, unsigned long *bits)
{
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	DECLARE_BITMAP(reg_val, MAX_LINE);
	int ret;

	scoped_guard(mutex, &chip->i2c_lock)
		ret = pca953x_read_regs(chip, PCA953x_INPUT, reg_val);
	if (ret)
		return ret;

	bitmap_replace(bits, bits, reg_val, mask, gc->ngpio);
	return 0;
}

static void pca953x_gpio_set_multiple(struct gpio_chip *gc,
				      unsigned long *mask, unsigned long *bits)
{
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	DECLARE_BITMAP(reg_val, MAX_LINE);
	int ret;

	guard(mutex)(&chip->i2c_lock);

	// Read-modify-write
	ret = pca953x_read_regs(chip, PCA953x_OUTPUT, reg_val);
	if (ret)
		return;

	bitmap_replace(reg_val, reg_val, bits, mask, gc->ngpio);
	pca953x_write_regs(chip, PCA953x_OUTPUT, reg_val);
}
```

### Pin Configuration (PCAL Extended Features)

```c
static int pca953x_gpio_set_pull_up_down(struct pca953x_chip *chip,
					 unsigned int offset,
					 unsigned long config)
{
	enum pin_config_param param = pinconf_to_config_param(config);
	u8 pull_en_reg = chip->recalc_addr(chip, PCAL953X_PULL_EN, offset);
	u8 pull_sel_reg = chip->recalc_addr(chip, PCAL953X_PULL_SEL, offset);
	u8 bit = BIT(offset % BANK_SZ);
	int ret;

	// Check if device supports pull-up/down
	if (!(chip->driver_data & PCA_PCAL))
		return -ENOTSUPP;

	guard(mutex)(&chip->i2c_lock);

	// Configure pull direction
	if (param == PIN_CONFIG_BIAS_PULL_UP)
		ret = regmap_write_bits(chip->regmap, pull_sel_reg, bit, bit);
	else if (param == PIN_CONFIG_BIAS_PULL_DOWN)
		ret = regmap_write_bits(chip->regmap, pull_sel_reg, bit, 0);
	else
		ret = 0;
	if (ret)
		return ret;

	// Enable/disable pull
	if (param == PIN_CONFIG_BIAS_DISABLE)
		return regmap_write_bits(chip->regmap, pull_en_reg, bit, 0);
	else
		return regmap_write_bits(chip->regmap, pull_en_reg, bit, bit);
}

static int pca953x_gpio_set_config(struct gpio_chip *gc, unsigned int offset,
				   unsigned long config)
{
	struct pca953x_chip *chip = gpiochip_get_data(gc);

	switch (pinconf_to_config_param(config)) {
	case PIN_CONFIG_BIAS_PULL_UP:
	case PIN_CONFIG_BIAS_PULL_DOWN:
	case PIN_CONFIG_BIAS_DISABLE:
		return pca953x_gpio_set_pull_up_down(chip, offset, config);
	default:
		return -ENOTSUPP;
	}
}
```

### IRQ Chip with Bus Lock Pattern

I2C/SPI GPIO expanders need deferred IRQ configuration:

```c
static void pca953x_irq_mask(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	irq_hw_number_t hwirq = irqd_to_hwirq(d);

	clear_bit(hwirq, chip->irq_mask);
	gpiochip_disable_irq(gc, hwirq);
}

static void pca953x_irq_unmask(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	irq_hw_number_t hwirq = irqd_to_hwirq(d);

	gpiochip_enable_irq(gc, hwirq);
	set_bit(hwirq, chip->irq_mask);
}

static void pca953x_irq_bus_lock(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct pca953x_chip *chip = gpiochip_get_data(gc);

	mutex_lock(&chip->irq_lock);
}

static void pca953x_irq_bus_sync_unlock(struct irq_data *d)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	DECLARE_BITMAP(irq_mask, MAX_LINE);

	// Synchronize cached IRQ configuration to hardware
	if (chip->driver_data & PCA_PCAL) {
		guard(mutex)(&chip->i2c_lock);

		// Enable input latch for interrupt-enabled pins
		pca953x_write_regs(chip, PCAL953X_IN_LATCH, chip->irq_mask);

		// Write interrupt mask (inverted logic: 0=enabled)
		bitmap_complement(irq_mask, chip->irq_mask, gc->ngpio);
		pca953x_write_regs(chip, PCAL953X_INT_MASK, irq_mask);
	}

	mutex_unlock(&chip->irq_lock);
}

static int pca953x_irq_set_type(struct irq_data *d, unsigned int type)
{
	struct gpio_chip *gc = irq_data_get_irq_chip_data(d);
	struct pca953x_chip *chip = gpiochip_get_data(gc);
	irq_hw_number_t hwirq = irqd_to_hwirq(d);

	if (!(type & IRQ_TYPE_EDGE_BOTH)) {
		dev_err(&chip->client->dev, "irq %d: unsupported type %d\n",
			d->irq, type);
		return -EINVAL;
	}

	assign_bit(hwirq, chip->irq_trig_fall, type & IRQ_TYPE_EDGE_FALLING);
	assign_bit(hwirq, chip->irq_trig_raise, type & IRQ_TYPE_EDGE_RISING);

	return 0;
}

static const struct irq_chip pca953x_irq_chip = {
	.name = "pca953x",
	.irq_mask = pca953x_irq_mask,
	.irq_unmask = pca953x_irq_unmask,
	.irq_bus_lock = pca953x_irq_bus_lock,
	.irq_bus_sync_unlock = pca953x_irq_bus_sync_unlock,
	.irq_set_type = pca953x_irq_set_type,
	.flags = IRQCHIP_IMMUTABLE,
	GPIOCHIP_IRQ_RESOURCE_HELPERS,
};
```

**Bus Lock Pattern**:
- `irq_bus_lock`: Acquire mutex, start of transaction
- `irq_mask/unmask/set_type`: Cache configuration changes
- `irq_bus_sync_unlock`: Synchronize cached changes to hardware, release mutex
- This batches multiple IRQ config changes into single I2C transaction

### Regmap Configuration

```c
static const struct regmap_config pca953x_i2c_regmap = {
	.reg_bits = 8,
	.val_bits = 8,

	.use_single_read = true,        // I2C: single byte read
	.use_single_write = true,       // I2C: single byte write

	.readable_reg = pca953x_readable_register,
	.writeable_reg = pca953x_writeable_register,
	.volatile_reg = pca953x_volatile_register,

	.disable_locking = true,        // We use our own mutex
	.cache_type = REGCACHE_MAPLE,
	.max_register = 0x7f,
};

static bool pca953x_volatile_register(struct device *dev, unsigned int reg)
{
	struct pca953x_chip *chip = dev_get_drvdata(dev);
	u32 bank;

	// Input register and interrupt status are volatile
	if (PCA_CHIP_TYPE(chip->driver_data) == PCA957X_TYPE)
		bank = PCA957x_BANK_INPUT;
	else
		bank = PCA953x_BANK_INPUT;

	if (chip->driver_data & PCA_PCAL)
		bank |= PCAL9xxx_BANK_IRQ_STAT;

	return chip->check_reg(chip, reg, bank);
}

static int pca953x_probe(struct i2c_client *client)
{
	struct pca953x_chip *chip;
	struct gpio_chip *gc;
	struct gpio_irq_chip *girq;
	int ret;

	chip = devm_kzalloc(&client->dev, sizeof(*chip), GFP_KERNEL);
	if (!chip)
		return -ENOMEM;

	chip->client = client;
	chip->driver_data = (unsigned long)i2c_get_match_data(client);

	mutex_init(&chip->i2c_lock);

	// Create regmap for I2C access
	chip->regmap = devm_regmap_init_i2c(client, &pca953x_i2c_regmap);
	if (IS_ERR(chip->regmap))
		return PTR_ERR(chip->regmap);

	gc = &chip->gpio_chip;
	gc->direction_input = pca953x_gpio_direction_input;
	gc->direction_output = pca953x_gpio_direction_output;
	gc->get = pca953x_gpio_get_value;
	gc->set = pca953x_gpio_set_value;
	gc->get_direction = pca953x_gpio_get_direction;
	gc->get_multiple = pca953x_gpio_get_multiple;
	gc->set_multiple = pca953x_gpio_set_multiple;
	gc->set_config = pca953x_gpio_set_config;
	gc->can_sleep = true;           // I2C operations may sleep
	gc->base = -1;
	gc->ngpio = pca953x_get_ngpio(chip);
	gc->label = dev_name(&client->dev);
	gc->parent = &client->dev;
	gc->owner = THIS_MODULE;

	// Setup IRQ chip if hardware supports interrupts
	if (client->irq && (chip->driver_data & PCA_INT)) {
		girq = &gc->irq;
		gpio_irq_chip_set_chip(girq, &pca953x_irq_chip);
		girq->parent_handler = NULL;
		girq->num_parents = 0;
		girq->parents = NULL;
		girq->default_type = IRQ_TYPE_NONE;
		girq->handler = handle_simple_irq;
		girq->threaded = true;      // Threaded IRQ for I2C

		mutex_init(&chip->irq_lock);

		ret = devm_request_threaded_irq(&client->dev, client->irq,
						NULL, pca953x_irq_handler,
						IRQF_ONESHOT | IRQF_SHARED,
						dev_name(&client->dev), chip);
		if (ret)
			return ret;
	}

	ret = devm_gpiochip_add_data(&client->dev, gc, chip);
	if (ret)
		return ret;

	i2c_set_clientdata(client, chip);

	return 0;
}

static const struct i2c_device_id pca953x_id[] = {
	{ "pca9534", 8 | PCA953X_TYPE | PCA_INT },
	{ "pca9535", 16 | PCA953X_TYPE | PCA_INT },
	{ "pca9536", 4 | PCA953X_TYPE },
	{ "pca9537", 4 | PCA953X_TYPE | PCA_INT },
	{ "pca9538", 8 | PCA953X_TYPE | PCA_INT },
	{ "pca9539", 16 | PCA953X_TYPE | PCA_INT },
	{ "pca9554", 8 | PCA953X_TYPE | PCA_INT },
	{ "pca9555", 16 | PCA953X_TYPE | PCA_INT },
	{ "pca9557", 8 | PCA953X_TYPE },
	{ "pcal6534", 34 | PCA953X_TYPE | PCA_PCAL | PCA_INT },
	{ }
};
MODULE_DEVICE_TABLE(i2c, pca953x_id);

static struct i2c_driver pca953x_driver = {
	.driver = {
		.name = "pca953x",
		.of_match_table = pca953x_of_match,
		.acpi_match_table = pca953x_acpi_ids,
	},
	.probe = pca953x_probe,
	.id_table = pca953x_id,
};
module_i2c_driver(pca953x_driver);
```

