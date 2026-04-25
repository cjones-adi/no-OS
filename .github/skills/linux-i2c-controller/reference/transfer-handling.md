# I2C Transfer Handling and Bus Recovery

Guide to handling I2C transfers, atomic transfers, and bus recovery mechanisms.

## I2C vs SMBus

The Linux I2C subsystem supports both I2C and SMBus protocols:

- **I2C**: Full I2C protocol implementation supporting arbitrary message sequences
- **SMBus**: Subset of I2C with specific transaction types (Quick, Byte, Word, Block, etc.)

Most modern controllers implement the `xfer()` method for I2C transactions. The I2C core can emulate SMBus transactions on top of I2C if needed. Some controllers that only support SMBus transactions implement `smbus_xfer()` instead.

## Atomic Transfers

Some controllers need to work during system suspend/resume to access PMICs. For this, implement `xfer_atomic()`:

```c
/**
 * my_i2c_xfer_atomic - Atomic transfer (no sleeping)
 *
 * This version cannot use interrupts or completions. It must poll
 * for transfer completion and cannot sleep. Used during suspend/resume.
 */
static int my_i2c_xfer_atomic(struct i2c_adapter *adap,
			      struct i2c_msg *msgs, int num)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);
	int i, ret;
	unsigned long timeout;

	for (i = 0; i < num; i++) {
		// Setup transfer (same as xfer)
		my_i2c_setup_msg(i2c, &msgs[i]);

		// Poll for completion instead of using interrupts
		timeout = jiffies + msecs_to_jiffies(1000);
		while (!(my_i2c_is_done(i2c))) {
			if (time_after(jiffies, timeout))
				return -ETIMEDOUT;
			cpu_relax();  // Busy-wait, no sleeping
		}

		ret = my_i2c_get_status(i2c);
		if (ret < 0)
			return ret;
	}

	return num;
}

static const struct i2c_algorithm my_i2c_algo = {
	.xfer = my_i2c_xfer,
	.xfer_atomic = my_i2c_xfer_atomic,  // Add atomic support
	.functionality = my_i2c_func,
};
```

## Bus Recovery

When an I2C slave device crashes or holds SDA low, the bus becomes stuck. The I2C core provides infrastructure for automatic bus recovery.

### Generic SCL Recovery (Controller-based)

If your controller can manually toggle SCL:

```c
#include <linux/i2c.h>

static void my_i2c_prepare_recovery(struct i2c_adapter *adap)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);

	// Switch pins to recovery mode (GPIO mode)
	my_i2c_enable_recovery_mode(i2c);
}

static void my_i2c_unprepare_recovery(struct i2c_adapter *adap)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);

	// Restore pins to I2C mode
	my_i2c_disable_recovery_mode(i2c);
}

static int my_i2c_get_scl(struct i2c_adapter *adap)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);
	return !!(readl(i2c->base + GPIO_INPUT_REG) & SCL_PIN);
}

static void my_i2c_set_scl(struct i2c_adapter *adap, int val)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);
	u32 reg = readl(i2c->base + GPIO_OUTPUT_REG);

	if (val)
		reg |= SCL_PIN;
	else
		reg &= ~SCL_PIN;

	writel(reg, i2c->base + GPIO_OUTPUT_REG);
}

static int my_i2c_get_sda(struct i2c_adapter *adap)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);
	return !!(readl(i2c->base + GPIO_INPUT_REG) & SDA_PIN);
}

static struct i2c_bus_recovery_info my_i2c_recovery_info = {
	.recover_bus = i2c_generic_scl_recovery,  // Use generic recovery
	.prepare_recovery = my_i2c_prepare_recovery,
	.unprepare_recovery = my_i2c_unprepare_recovery,
	.get_scl = my_i2c_get_scl,
	.set_scl = my_i2c_set_scl,
	.get_sda = my_i2c_get_sda,
};

// In probe():
id->adap.bus_recovery_info = &my_i2c_recovery_info;
```

### GPIO-based Recovery

If SCL/SDA are connected to GPIO pins:

```c
#include <linux/i2c.h>
#include <linux/gpio/consumer.h>

struct my_i2c {
	struct i2c_adapter adap;
	struct gpio_desc *scl_gpio;
	struct gpio_desc *sda_gpio;
};

static int my_i2c_probe(struct platform_device *pdev)
{
	struct my_i2c *i2c;
	int ret;

	i2c = devm_kzalloc(&pdev->dev, sizeof(*i2c), GFP_KERNEL);
	if (!i2c)
		return -ENOMEM;

	// Get GPIO descriptors for recovery
	i2c->scl_gpio = devm_gpiod_get_optional(&pdev->dev, "scl", GPIOD_OUT_HIGH);
	if (IS_ERR(i2c->scl_gpio))
		return PTR_ERR(i2c->scl_gpio);

	i2c->sda_gpio = devm_gpiod_get_optional(&pdev->dev, "sda", GPIOD_IN);
	if (IS_ERR(i2c->sda_gpio))
		return PTR_ERR(i2c->sda_gpio);

	// Setup recovery if GPIOs available
	if (i2c->scl_gpio && i2c->sda_gpio) {
		i2c->adap.bus_recovery_info = &(struct i2c_bus_recovery_info){
			.recover_bus = i2c_generic_scl_recovery,
			.get_scl = i2c_get_scl_gpio_value,
			.set_scl = i2c_set_scl_gpio_value,
			.get_sda = i2c_get_sda_gpio_value,
			.scl_gpiod = i2c->scl_gpio,
			.sda_gpiod = i2c->sda_gpio,
		};
	}

	// ... rest of probe
}
```

### Manual Recovery Triggering

You can manually trigger bus recovery when needed:

```c
// Check if recovery is configured
if (!adap->bus_recovery_info) {
	dev_err(&adap->dev, "No bus recovery configured\n");
}

// Manually trigger recovery
i2c_recover_bus(&adap);
```

### How Bus Recovery Works

The generic SCL recovery algorithm works by:

1. Check if SDA is stuck low (if high, bus is fine)
2. Generate up to 9 SCL clock pulses
3. After each pulse, check if SDA goes high
4. If SDA goes high, generate STOP condition
5. If after 9 pulses SDA still low, recovery failed

This works because most I2C slaves will release SDA after completing their current byte transfer (which takes at most 9 clock cycles).

## Error Handling

### Common Error Codes

Return appropriate error codes from `xfer()`:

```c
// Transfer successful
return num;  // Number of messages processed

// Device not responding (NACK on address)
return -ENXIO;

// Arbitration lost (multi-master bus)
return -EAGAIN;  // Core will retry

// Transfer timeout
return -ETIMEDOUT;

// Invalid parameters
return -EINVAL;

// Hardware error
return -EIO;
```

### Timeout Handling

The adapter timeout field controls maximum wait time:

```c
// In probe, set timeout (in jiffies)
id->adap.timeout = msecs_to_jiffies(1000);  // 1 second

// In xfer, use adapter timeout
timeout = wait_for_completion_timeout(&id->xfer_done, adap->timeout);
if (!timeout) {
	dev_err(&adap->dev, "Transfer timeout\n");
	return -ETIMEDOUT;
}
```

### Arbitration Loss

For multi-master buses, handle arbitration loss:

```c
// In interrupt handler
if (isr_status & ARB_LOST_BIT) {
	id->err_status = -EAGAIN;  // Tell core to retry
	complete(&id->xfer_done);
	return IRQ_HANDLED;
}

// In probe, set retry count
id->adap.retries = 3;  // Retry 3 times on arbitration loss
```

## Transfer Patterns

### Repeated Start Condition

Support for repeated start (no STOP between messages):

```c
// Process each message
for (count = 0; count < num; count++) {
	// ... setup message ...

	// Hold bus if more messages follow (for repeated start)
	if (count < num - 1)
		reg |= HOLD_BUS_BIT;
	else
		reg &= ~HOLD_BUS_BIT;  // Release bus after last message

	// ... perform transfer ...
}
```

**Example**: Reading EEPROM with repeated start
```
START - ADDR(W) - REG_ADDR - REPEATED_START - ADDR(R) - DATA - STOP
[  msg[0]: write ]           [      msg[1]: read             ]
```

### Combined Write-Read Transfer

Common pattern for register reads:

```c
struct i2c_msg msgs[2] = {
	{
		.addr = client->addr,
		.flags = 0,           // Write
		.len = 1,
		.buf = &reg_addr,
	},
	{
		.addr = client->addr,
		.flags = I2C_M_RD,    // Read
		.len = data_len,
		.buf = data_buf,
	},
};

ret = i2c_transfer(client->adapter, msgs, 2);
```

Your controller should handle this as a single transaction with repeated start.

### 10-bit Addressing

Support for 10-bit client addresses:

```c
static int my_i2c_xfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	// Check for 10-bit address
	if (msgs[0].flags & I2C_M_TEN) {
		// Program controller for 10-bit addressing
		// First byte: 11110xx (xx = bits 9-8 of address)
		// Second byte: bits 7-0 of address
	}
	// ...
}

static u32 my_i2c_func(struct i2c_adapter *adap)
{
	// Advertise 10-bit address support
	return I2C_FUNC_I2C | I2C_FUNC_10BIT_ADDR | I2C_FUNC_SMBUS_EMUL;
}
```

## Clock Stretching

Some I2C slaves hold SCL low to slow down the master (clock stretching). Most hardware controllers handle this automatically, but ensure your controller supports it.

If your controller doesn't support clock stretching, declare it in quirks:

```c
static const struct i2c_adapter_quirks my_i2c_quirks = {
	.flags = I2C_AQ_NO_CLK_STRETCH,
};

id->adap.quirks = &my_i2c_quirks;
```
