# GPIO Debugging Techniques

Comprehensive debugging guide using debugfs, sysfs, ftrace, and common troubleshooting techniques for GPIO controller and consumer drivers.

## Debugging GPIO Drivers

### debugfs Interface

```bash
# List all GPIO controllers and their lines
cat /sys/kernel/debug/gpio

# Example output:
gpiochip0: GPIOs 0-31, parent: platform/40000000.gpio, mygpio:
 gpio-0   (SPI_CS0             |spi-cs               ) out hi
 gpio-5   (                    |reset                ) out lo ACTIVE LOW
 gpio-10  (                    |enable               ) out hi
 gpio-15  (                    |irq                  ) in  hi

# GPIO line information (requires CONFIG_GPIO_CDEV)
cat /sys/kernel/debug/gpio-mockup/gpiochip0
```

### sysfs Interface (Legacy, use gpiod API instead)

```bash
# Export GPIO for userspace access (legacy method)
echo 5 > /sys/class/gpio/export
cat /sys/class/gpio/gpio5/value
echo out > /sys/class/gpio/gpio5/direction
echo 1 > /sys/class/gpio/gpio5/value
echo 5 > /sys/class/gpio/unexport
```

### Kernel Configuration

```kconfig
# GPIO subsystem
CONFIG_GPIOLIB=y
CONFIG_GPIOLIB_FASTPATH_LIMIT=512    # Inline get/set for GPIOs < 512
CONFIG_GPIO_CDEV=y                   # Character device interface
CONFIG_GPIO_SYSFS=y                  # Legacy sysfs interface (deprecated)

# GPIO expanders
CONFIG_GPIO_PCA953X=m                # I2C GPIO expander
CONFIG_GPIO_PCA953X_IRQ=y            # IRQ support for PCA953x

# Debugging
CONFIG_DEBUG_GPIO=y                  # Debug messages
```

### Common Debug Techniques

```c
// Enable dynamic debug for GPIO subsystem
// Boot cmdline: dyndbg="file drivers/gpio/* +p"
// Or at runtime:
// echo 'file drivers/gpio/gpiolib.c +p' > /sys/kernel/debug/dynamic_debug/control

// Trace GPIO operations
#define DEBUG
#include <linux/gpio/driver.h>

static int mygpio_get(struct gpio_chip *gc, unsigned int offset)
{
	struct mygpio_priv *priv = gpiochip_get_data(gc);
	u32 val;

	val = readl(priv->base + MYGPIO_DATA);
	dev_dbg(gc->parent, "get gpio%d: reg=0x%08x bit=%d val=%d\n",
		offset, val, offset, !!(val & BIT(offset)));

	return !!(val & BIT(offset));
}

// Check GPIO chip registration
static int mygpio_probe(struct platform_device *pdev)
{
	// ...
	ret = devm_gpiochip_add_data(dev, gc, priv);
	if (ret)
		return ret;

	dev_info(dev, "Registered GPIO chip: base=%d ngpio=%d\n",
		 gc->base, gc->ngpio);

	return 0;
}

// Verify GPIO consumer acquisition
mydev->reset_gpio = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);
if (IS_ERR(mydev->reset_gpio)) {
	dev_err(dev, "Failed to get reset GPIO: %ld\n",
		PTR_ERR(mydev->reset_gpio));
	return PTR_ERR(mydev->reset_gpio);
}

dev_dbg(dev, "Got reset GPIO: chip=%s offset=%d active_low=%d\n",
	gpiod_get_label(mydev->reset_gpio),
	desc_to_gpio(mydev->reset_gpio),
	gpiod_is_active_low(mydev->reset_gpio));
```

### ftrace GPIO Events

```bash
# Trace GPIO operations
cd /sys/kernel/debug/tracing
echo 1 > events/gpio/enable
cat trace

# Example output:
# irq_handler-123   [000] ....    10.123456: gpio_value: 32 get 1
# worker-456        [001] ....    10.234567: gpio_direction: 15 out
# worker-456        [001] ....    10.234568: gpio_value: 15 set 1
```

