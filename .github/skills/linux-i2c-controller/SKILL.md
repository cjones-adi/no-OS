---
name: linux-i2c-controller
description: Complete guide to Linux I2C controller driver implementation for managing I2C buses. Use when implementing I2C master/host drivers, working with struct i2c_adapter and i2c_algorithm, handling bus recovery, managing adapter quirks, implementing atomic transfers, or debugging I2C controller hardware. This covers controller drivers, not device drivers.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: i2c
  tags:
    - i2c
    - i2c-adapter
    - i2c-algorithm
    - i2c-controller
    - i2c-master
    - smbus
    - bus-recovery
    - atomic-transfer
  dependencies:
    - linux-devicetree
    - linux-clk
    - linux-gpio
    - linux-debugging
  learning_objectives:
    - Implement I2C controller drivers with struct i2c_adapter
    - Handle I2C message transfers with struct i2c_algorithm
    - Implement bus recovery mechanisms (GPIO-based and controller-based)
    - Configure adapter quirks for hardware limitations
    - Support atomic transfers for suspend/resume
    - Debug I2C controller and transfer issues
---

# Linux I2C Controller Drivers

Quick-start guide for implementing I2C controller (adapter/master) drivers that manage I2C buses.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User mentions: "implement I2C controller", "I2C driver", "i2c_adapter", "i2c_algorithm", "struct i2c_msg"
- Questions about: xfer(), smbus_xfer(), xfer_atomic(), functionality(), i2c_add_adapter()
- User asks: "how to implement", "step by step", "create I2C controller", "master transfer"
- Topics: interrupt handling, FIFO management, repeated start, message processing, adapter registration
- Example drivers: i2c-cadence.c, i2c-imx.c, i2c-designware-*.c

**Triggers to read reference/transfer-handling.md**:
- User mentions: "atomic transfer", "xfer_atomic", "suspend/resume", "I2C vs SMBus"
- Questions about: error handling, timeout, arbitration loss, NACK, repeated start, combined transfers
- User asks: "10-bit addressing", "clock stretching", "error codes", "multi-master bus"
- Topics: I2C_M_RD flag, I2C_M_NOSTART, transfer patterns, write-read combination

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "DTS", "i2c-controller.yaml", "clock-frequency"
- Questions about: bus number assignment, aliases, standard I2C properties, client devices
- User asks: "devicetree example", "how to specify", "binding schema", "YAML"
- Topics: scl-gpios, sda-gpios, i2c-scl-falling-time-ns, #address-cells, #size-cells

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "timeout", "NACK", "bus stuck", "SDA low"
- Questions about: i2cdetect, i2cget, i2cset, i2cdump, dynamic debug, logic analyzer
- User asks: "troubleshoot", "diagnose", "I2C error", "transfer fails", "device not responding"
- Topics: pull-up resistors, clock configuration, interrupt routing, signal quality, bus recovery

---

## When to Use This Skill

- Implementing I2C controller drivers for SoC I2C blocks or I2C host adapters
- Working with I2C bus masters (not I2C device/client drivers)
- Adding bus recovery support to I2C controllers
- Implementing atomic transfers for PM applications
- Debugging I2C controller hardware issues

## What is an I2C Controller?

An I2C controller (also called adapter, master, or host) manages an I2C bus and initiates transfers to I2C devices. This skill covers **controller drivers**, not device drivers.

```
┌─────────────────────────────────────────────────────────┐
│                  I2C Device Drivers                      │
│         (Clients: EEPROMs, sensors, PMICs)              │
│                                                          │
│  i2c_smbus_read_byte_data(), i2c_transfer()            │
└──────────────────────┬──────────────────────────────────┘
                       │ I2C Core API
┌──────────────────────▼──────────────────────────────────┐
│                    I2C Core                              │
│            (drivers/i2c/i2c-core-*.c)                   │
│                                                          │
│  - Message routing and protocol handling                │
│  - Retry logic for arbitration loss                     │
│  - SMBus emulation on top of I2C                        │
│  - Bus recovery infrastructure                          │
└──────────────────────┬──────────────────────────────────┘
                       │ I2C Adapter API
┌──────────────────────▼──────────────────────────────────┐
│              I2C Controller Drivers                      │
│           (This skill - drivers/i2c/busses/)            │
│                                                          │
│  struct i2c_adapter, struct i2c_algorithm               │
│  xfer(), functionality(), bus_recovery_info             │
└──────────────────────────────────────────────────────────┘
```

## Quick Reference

### Key Structures

| Structure | Purpose | Location |
|-----------|---------|----------|
| `struct i2c_adapter` | I2C bus controller | `<linux/i2c.h>` |
| `struct i2c_algorithm` | Transfer methods (xfer, functionality) | `<linux/i2c.h>` |
| `struct i2c_msg` | I2C message descriptor | `<linux/i2c.h>` |
| `struct i2c_bus_recovery_info` | Bus recovery configuration | `<linux/i2c.h>` |
| `struct i2c_adapter_quirks` | Hardware limitations | `<linux/i2c.h>` |

### I2C Algorithm Callbacks

| Callback | Purpose | Required? |
|----------|---------|-----------|
| `xfer` | I2C message transfer | Yes (or smbus_xfer) |
| `functionality` | Return supported features | Yes |
| `xfer_atomic` | Atomic transfer (no sleep) | Optional |
| `smbus_xfer` | SMBus-only transfer | Optional |

### I2C Message Flags

| Flag | Purpose |
|------|---------|
| `I2C_M_RD` | Read from client (otherwise write) |
| `I2C_M_TEN` | 10-bit client address |
| `I2C_M_RECV_LEN` | First byte is message length |
| `I2C_M_NO_RD_ACK` | Don't ACK last byte on read |
| `I2C_M_IGNORE_NAK` | Continue even if client NACKs |
| `I2C_M_NOSTART` | Don't send START (repeated start) |

### I2C Functionality Flags

| Flag | Purpose |
|------|---------|
| `I2C_FUNC_I2C` | Full I2C protocol support |
| `I2C_FUNC_10BIT_ADDR` | 10-bit addressing |
| `I2C_FUNC_SMBUS_EMUL` | SMBus emulation by core |
| `I2C_FUNC_NOSTART` | Repeated start support |

### Common Error Codes

| Error | Meaning |
|-------|---------|
| `num` | Success - number of messages processed |
| `-ENXIO` | Device not responding (NACK on address) |
| `-EAGAIN` | Arbitration lost (core will retry) |
| `-ETIMEDOUT` | Transfer timeout |
| `-EINVAL` | Invalid parameters |
| `-EIO` | Hardware error |

## Quick Start

### Minimal I2C Controller Driver

```c
#include <linux/i2c.h>
#include <linux/platform_device.h>
#include <linux/interrupt.h>
#include <linux/clk.h>

struct my_i2c {
	struct i2c_adapter	adap;
	void __iomem		*base;
	struct clk		*clk;
	struct completion	xfer_done;
	int			irq;
	int			err_status;
};

static irqreturn_t my_i2c_isr(int irq, void *ptr)
{
	struct my_i2c *i2c = ptr;
	u32 status = readl(i2c->base + STATUS_REG);

	writel(status, i2c->base + STATUS_REG);  // Clear

	if (status & ARB_LOST_BIT) {
		i2c->err_status = -EAGAIN;  // Arbitration lost
		complete(&i2c->xfer_done);
		return IRQ_HANDLED;
	}

	if (status & NACK_BIT) {
		i2c->err_status = -ENXIO;  // Device not responding
		complete(&i2c->xfer_done);
		return IRQ_HANDLED;
	}

	if (status & COMPLETE_BIT) {
		i2c->err_status = 0;  // Success
		complete(&i2c->xfer_done);
	}

	return IRQ_HANDLED;
}

static int my_i2c_xfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);
	int ret, count;

	ret = clk_enable(i2c->clk);
	if (ret)
		return ret;

	// Process each message
	for (count = 0; count < num; count++) {
		i2c->err_status = 0;
		reinit_completion(&i2c->xfer_done);

		// Configure transfer
		writel(msgs[count].addr, i2c->base + ADDR_REG);

		if (msgs[count].flags & I2C_M_RD) {
			// Setup read transfer
			writel(msgs[count].len, i2c->base + LEN_REG);
			writel(READ_MODE, i2c->base + CTRL_REG);
		} else {
			// Setup write transfer, fill TX FIFO
			for (int i = 0; i < msgs[count].len; i++)
				writel(msgs[count].buf[i], i2c->base + DATA_REG);
			writel(WRITE_MODE, i2c->base + CTRL_REG);
		}

		// Enable interrupts and start transfer
		writel(IRQ_ENABLE_ALL, i2c->base + IER_REG);
		writel(START_TRANSFER, i2c->base + START_REG);

		// Wait for completion
		if (!wait_for_completion_timeout(&i2c->xfer_done, adap->timeout)) {
			dev_err(&adap->dev, "Transfer timeout\n");
			ret = -ETIMEDOUT;
			goto err_clk;
		}

		// Check for errors
		if (i2c->err_status) {
			ret = i2c->err_status;
			goto err_clk;
		}

		// For reads, get data from RX FIFO
		if (msgs[count].flags & I2C_M_RD) {
			for (int i = 0; i < msgs[count].len; i++)
				msgs[count].buf[i] = readl(i2c->base + DATA_REG);
		}
	}

	ret = num;  // Success - return number of messages

err_clk:
	clk_disable(i2c->clk);
	return ret;
}

static u32 my_i2c_func(struct i2c_adapter *adap)
{
	return I2C_FUNC_I2C | I2C_FUNC_SMBUS_EMUL;
}

static const struct i2c_algorithm my_i2c_algo = {
	.xfer = my_i2c_xfer,
	.functionality = my_i2c_func,
};

static int my_i2c_probe(struct platform_device *pdev)
{
	struct my_i2c *i2c;
	int ret;

	i2c = devm_kzalloc(&pdev->dev, sizeof(*i2c), GFP_KERNEL);
	if (!i2c)
		return -ENOMEM;

	platform_set_drvdata(pdev, i2c);
	init_completion(&i2c->xfer_done);

	// Get resources
	i2c->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(i2c->base))
		return PTR_ERR(i2c->base);

	i2c->irq = platform_get_irq(pdev, 0);
	if (i2c->irq < 0)
		return i2c->irq;

	i2c->clk = devm_clk_get(&pdev->dev, NULL);
	if (IS_ERR(i2c->clk))
		return PTR_ERR(i2c->clk);

	ret = clk_prepare_enable(i2c->clk);
	if (ret)
		return ret;

	// Initialize hardware
	writel(CONTROLLER_RESET, i2c->base + CTRL_REG);
	writel(TIMEOUT_VALUE, i2c->base + TIMEOUT_REG);

	clk_disable(i2c->clk);

	// Setup adapter
	i2c_set_adapdata(&i2c->adap, i2c);
	i2c->adap.owner = THIS_MODULE;
	i2c->adap.algo = &my_i2c_algo;
	i2c->adap.dev.parent = &pdev->dev;
	i2c->adap.dev.of_node = pdev->dev.of_node;
	i2c->adap.timeout = msecs_to_jiffies(1000);  // 1 second
	i2c->adap.retries = 3;  // Retry 3 times on arbitration loss
	snprintf(i2c->adap.name, sizeof(i2c->adap.name),
		 "My I2C at %p", i2c->base);

	// Request IRQ
	ret = devm_request_irq(&pdev->dev, i2c->irq, my_i2c_isr,
			       0, dev_name(&pdev->dev), i2c);
	if (ret)
		return ret;

	// Register adapter
	ret = i2c_add_adapter(&i2c->adap);
	if (ret < 0)
		goto err_clk;

	dev_info(&pdev->dev, "I2C controller registered\n");
	return 0;

err_clk:
	clk_disable_unprepare(i2c->clk);
	return ret;
}

static void my_i2c_remove(struct platform_device *pdev)
{
	struct my_i2c *i2c = platform_get_drvdata(pdev);

	i2c_del_adapter(&i2c->adap);
	clk_disable_unprepare(i2c->clk);
}

static const struct of_device_id my_i2c_of_match[] = {
	{ .compatible = "vendor,my-i2c" },
	{ }
};
MODULE_DEVICE_TABLE(of, my_i2c_of_match);

static struct platform_driver my_i2c_driver = {
	.driver = {
		.name = "my-i2c",
		.of_match_table = my_i2c_of_match,
	},
	.probe = my_i2c_probe,
	.remove = my_i2c_remove,
};
module_platform_driver(my_i2c_driver);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("My I2C Controller Driver");
```

### Devicetree Binding

```dts
i2c0: i2c@40000000 {
	compatible = "vendor,my-i2c";
	reg = <0x40000000 0x1000>;
	interrupts = <GIC_SPI 25 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clkc 38>;
	clock-frequency = <400000>;  // 400 kHz
	#address-cells = <1>;
	#size-cells = <0>;

	// I2C devices on this bus
	eeprom@50 {
		compatible = "atmel,24c64";
		reg = <0x50>;
	};
};
```

## Essential Patterns

### Repeated Start Support

Hold bus between messages for repeated start:

```c
static int my_i2c_xfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	for (count = 0; count < num; count++) {
		// ... setup transfer ...

		// Hold bus if more messages follow
		if (count < num - 1)
			reg |= HOLD_BUS_BIT;  // Keep START active
		else
			reg &= ~HOLD_BUS_BIT;  // Release bus after last message

		// ... perform transfer ...
	}
}
```

### Bus Recovery (GPIO-based)

```c
#include <linux/gpio/consumer.h>

struct my_i2c {
	struct i2c_adapter adap;
	struct gpio_desc *scl_gpio;
	struct gpio_desc *sda_gpio;
};

static int my_i2c_probe(struct platform_device *pdev)
{
	struct my_i2c *i2c;

	// ... allocate and setup ...

	// Get GPIOs for recovery
	i2c->scl_gpio = devm_gpiod_get_optional(&pdev->dev, "scl", GPIOD_OUT_HIGH);
	i2c->sda_gpio = devm_gpiod_get_optional(&pdev->dev, "sda", GPIOD_IN);

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

	// ... rest of probe ...
}
```

### Adapter Quirks

Declare hardware limitations:

```c
static const struct i2c_adapter_quirks my_i2c_quirks = {
	.max_write_len = 255,      // Max 255 bytes per write
	.max_read_len = 255,       // Max 255 bytes per read
	.flags = I2C_AQ_NO_ZERO_LEN,  // Zero-length not supported
};

// In probe:
i2c->adap.quirks = &my_i2c_quirks;
```

The I2C core will automatically split large transfers.

### Atomic Transfers

For suspend/resume PMIC access:

```c
static int my_i2c_xfer_atomic(struct i2c_adapter *adap,
			      struct i2c_msg *msgs, int num)
{
	struct my_i2c *i2c = i2c_get_adapdata(adap);
	int count;
	unsigned long timeout;

	for (count = 0; count < num; count++) {
		// Setup transfer (no interrupts)
		// ...

		// Poll for completion (no sleeping!)
		timeout = jiffies + msecs_to_jiffies(1000);
		while (!(readl(i2c->base + STATUS_REG) & COMPLETE_BIT)) {
			if (time_after(jiffies, timeout))
				return -ETIMEDOUT;
			cpu_relax();  // Busy-wait
		}
	}

	return num;
}

static const struct i2c_algorithm my_i2c_algo = {
	.xfer = my_i2c_xfer,
	.xfer_atomic = my_i2c_xfer_atomic,  // Add atomic support
	.functionality = my_i2c_func,
};
```

## Testing

### Check Adapter Registration

```bash
# List I2C adapters
i2cdetect -l

# Should show:
# i2c-0   i2c         My I2C at 0x40000000           I2C adapter
```

### Scan for Devices

```bash
# Scan bus 0 for devices
i2cdetect -y 0

# Read from device
i2cget -y 0 0x50 0x00

# Write to device
i2cset -y 0 0x50 0x00 0x42
```

### Enable Debug

```bash
# Enable I2C core debug
echo 'file i2c-core-* +p' > /sys/kernel/debug/dynamic_debug/control

# Enable driver debug
echo 'file my-i2c.c +p' > /sys/kernel/debug/dynamic_debug/control

# View logs
dmesg -w
```

## Implementation Checklist

- [ ] Implement `xfer()` to handle I2C message transfers
- [ ] Implement `functionality()` to return supported features
- [ ] Set `adap.timeout` (typically 1 second)
- [ ] Set `adap.retries` (typically 3 for arbitration loss)
- [ ] Handle interrupts for transfer completion, NACK, arbitration loss
- [ ] Return correct error codes (-ENXIO for NACK, -EAGAIN for arb loss, -ETIMEDOUT)
- [ ] Support repeated start (hold bus between messages)
- [ ] Configure `quirks` if hardware has limitations
- [ ] Add bus recovery support (GPIO or controller-based)
- [ ] Optionally implement `xfer_atomic()` for PM
- [ ] Create devicetree binding in YAML format
- [ ] Test with `i2cdetect`, `i2cget`, `i2cset`

## Common Issues

### Transfer Timeout
- Check clock is enabled
- Verify interrupt is registered and firing
- Increase `adap.timeout` value
- Check hardware initialization

### NACK on All Transfers
- Wrong device address (use 7-bit, not 8-bit)
- Clock speed too high (try 100 kHz)
- Missing pull-up resistors on SDA/SCL
- Device not powered or in reset

### Bus Stuck (SDA Low)
- Configure bus recovery
- Check pull-up resistors (4.7kΩ for 100kHz, 2.2kΩ for 400kHz)
- Manually trigger recovery: `echo 1 > /sys/kernel/debug/i2c/i2c-0/bus_recovery`

## References

- **Kernel Documentation**: `Documentation/i2c/`
- **I2C Core**: `drivers/i2c/i2c-core-base.c`
- **Example Drivers**:
  - `drivers/i2c/busses/i2c-cadence.c` - Xilinx Zynq/ZynqMP
  - `drivers/i2c/busses/i2c-imx.c` - i.MX series
  - `drivers/i2c/busses/i2c-designware-*.c` - DesignWare I2C
- **Headers**:
  - `include/linux/i2c.h` - I2C adapter/algorithm API
  - `include/uapi/linux/i2c.h` - I2C message flags
