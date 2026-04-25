---
name: linux-spi-controller
description: Complete guide to Linux SPI controller driver implementation for managing SPI buses. Use when implementing SPI master/host drivers, working with struct spi_controller, handling DMA transfers, or debugging SPI bus issues. This covers controller drivers, not device drivers.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: spi
  tags:
    - spi
    - spi-controller
    - spi-master
    - spi-host
    - dma
    - axi-spi-engine
    - transfer
    - chip-select
  dependencies:
    - linux-devicetree
    - linux-dma
  learning_objectives:
    - Implement SPI controller drivers with struct spi_controller
    - Choose between transfer_one and transfer_one_message methods
    - Integrate DMA support for high-speed transfers
    - Manage chip select signals and timing
    - Configure SPI modes (CPOL, CPHA, LSB_FIRST)
    - Debug SPI controller hardware issues
    - Work with ADI AXI SPI Engine (FPGA-based controller)
---

# Linux SPI Controller Drivers

Quick-start guide for implementing SPI controller (master/host) drivers.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User mentions: "implement SPI controller", "SPI master driver", "spi_controller", "AXI SPI Engine"
- Questions about: setup(), set_cs(), cleanup(), allocation, registration, controller callbacks
- User asks: "how to implement", "step by step", "create SPI controller driver"
- Topics: mode_bits, max_transfer_size, bus_num, num_chipselect, prepare/unprepare methods

**Triggers to read reference/transfer-handling.md**:
- User mentions: "transfer_one", "transfer_one_message", "DMA", "spi_transfer", "spi_message"
- Questions about: return values, finalize functions, interrupt handling, blocking vs async transfers
- User asks: "how to handle transfers", "DMA integration", "which transfer method"
- Topics: spi_finalize_current_transfer(), spi_finalize_current_message(), DMA callbacks, error handling, CS management

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "DTS", "YAML schema", "#address-cells"
- Questions about: SPI controller properties, num-cs, cs-gpios, dma-names, spi-max-frequency
- User asks: "devicetree example", "how to define SPI controller in DT", "YAML validation"
- Topics: dt_binding_check, dtbs_check, compatible string, reg property

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "timeout", "data corruption", "wrong data"
- Questions about: dynamic debug, sysfs, ftrace, statistics, common issues
- User says: "troubleshoot", "diagnose", "SPI error", "transfer failed", "performance issue"
- Topics: /sys/class/spi_master/, /sys/bus/spi/devices/, dmesg, logic analyzer

---

## When to Use This Skill

- Implementing SPI controller drivers for SoC SPI blocks or FPGA IP cores
- Working with struct spi_controller and controller callbacks
- Adding DMA support to SPI controllers
- Debugging SPI controller hardware issues
- Working with ADI AXI SPI Engine (FPGA-based SPI controller)

**Note**: This skill covers **controller drivers** (bus masters). For SPI **device drivers** (peripherals), see device-specific skills.

## What is an SPI Controller?

The Linux SPI framework has two distinct driver types:

**Controller Drivers** (this skill):
- Manage SPI bus hardware (registers, clocks, DMA)
- Implement transfer operations
- Handle chip select signals
- Example: `drivers/spi/spi-axi-spi-engine.c`

**Device Drivers** (protocol drivers):
- Communicate with SPI peripherals (ADCs, DACs, sensors)
- Use SPI messages to send/receive data
- Example: `drivers/iio/adc/ad7124.c`

```
┌─────────────────┐
│  Device Driver  │  (e.g., AD7124 ADC driver)
└────────┬────────┘
         │ spi_sync(), spi_async()
         ▼
┌─────────────────┐
│ SPI Framework   │  (Message queuing, transfer logic)
└────────┬────────┘
         │ transfer_one(), setup()
         ▼
┌─────────────────┐
│ Controller      │  (e.g., AXI SPI Engine)
│   Driver        │  (Hardware manipulation)
└─────────────────┘
```

## Quick Reference

### Key Structure

| Structure | Purpose | Location |
|-----------|---------|----------|
| `struct spi_controller` | SPI bus master (provider side) | `<linux/spi/spi.h>` |
| `struct spi_device` | SPI peripheral device | `<linux/spi/spi.h>` |
| `struct spi_transfer` | Individual transfer | `<linux/spi/spi.h>` |
| `struct spi_message` | List of transfers | `<linux/spi/spi.h>` |

### Required Controller Callbacks

| Callback | Purpose | Required? |
|----------|---------|-----------|
| `setup` | Configure SPI mode and device settings | Yes |
| `transfer_one` OR `transfer_one_message` | Perform SPI transfers | Yes (one of) |
| `set_cs` | Control chip select lines | Optional (uses GPIO if missing) |

### Optional Controller Callbacks

| Callback | Purpose |
|----------|---------|
| `cleanup` | Free per-device state allocated in setup() |
| `prepare_transfer_hardware` | Prepare controller before transfers (power on) |
| `unprepare_transfer_hardware` | Unprepare controller after transfers (power off) |
| `prepare_message` | Prepare for each message |
| `unprepare_message` | Cleanup after each message |

### SPI Mode Bits

| Mode Bit | Purpose |
|----------|---------|
| `SPI_CPOL` | Clock polarity (idle high) |
| `SPI_CPHA` | Clock phase (sample on trailing edge) |
| `SPI_CS_HIGH` | Chip select active high |
| `SPI_LSB_FIRST` | LSB transmitted first |
| `SPI_3WIRE` | Bidirectional mode (shared MOSI/MISO) |
| `SPI_LOOP` | Loopback mode |
| `SPI_NO_CS` | Single device, no CS needed |

## Quick Start: Basic SPI Controller

### Controller Driver Pattern

```c
#include <linux/spi/spi.h>
#include <linux/platform_device.h>
#include <linux/module.h>

struct my_spi_controller {
	void __iomem		*base;
	struct clk		*clk;
};

static void my_spi_set_cs(struct spi_device *spi, bool enable)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(spi->controller);
	u8 cs = spi_get_chipselect(spi, 0);

	if (enable) {
		/* Assert CS (usually active low) */
		if (spi->mode & SPI_CS_HIGH)
			writel(BIT(cs), ctlr->base + CS_SET);
		else
			writel(BIT(cs), ctlr->base + CS_CLR);
	} else {
		/* Deassert CS */
		if (spi->mode & SPI_CS_HIGH)
			writel(BIT(cs), ctlr->base + CS_CLR);
		else
			writel(BIT(cs), ctlr->base + CS_SET);
	}
}

static int my_spi_setup(struct spi_device *spi)
{
	/* Validate configuration */
	if (spi->bits_per_word != 8 && spi->bits_per_word != 16) {
		dev_err(&spi->dev, "Unsupported bits_per_word: %d\n",
			spi->bits_per_word);
		return -EINVAL;
	}

	if (spi->max_speed_hz > 50000000) {
		dev_err(&spi->dev, "Speed too high: %d Hz\n", spi->max_speed_hz);
		return -EINVAL;
	}

	return 0;
}

static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(host);
	const u8 *tx_buf = xfer->tx_buf;
	u8 *rx_buf = xfer->rx_buf;
	unsigned int len = xfer->len;
	unsigned int i;

	/* Set clock divisor */
	writel(clk_get_rate(ctlr->clk) / xfer->speed_hz,
	       ctlr->base + CLK_DIV);

	/* Transfer data */
	for (i = 0; i < len; i++) {
		/* Write data */
		writeb(tx_buf ? tx_buf[i] : 0, ctlr->base + TX_DATA);

		/* Wait for transfer complete */
		while (!(readl(ctlr->base + STATUS) & TX_DONE))
			cpu_relax();

		/* Read data */
		if (rx_buf)
			rx_buf[i] = readb(ctlr->base + RX_DATA);
	}

	return 0;  // Success
}

static int my_spi_probe(struct platform_device *pdev)
{
	struct spi_controller *host;
	struct my_spi_controller *ctlr;
	int ret;

	/* Allocate controller + private data */
	host = devm_spi_alloc_host(&pdev->dev, sizeof(*ctlr));
	if (!host)
		return -ENOMEM;

	ctlr = spi_controller_get_devdata(host);

	/* Map registers */
	ctlr->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(ctlr->base))
		return PTR_ERR(ctlr->base);

	/* Get clock */
	ctlr->clk = devm_clk_get(&pdev->dev, NULL);
	if (IS_ERR(ctlr->clk))
		return PTR_ERR(ctlr->clk);

	ret = clk_prepare_enable(ctlr->clk);
	if (ret)
		return ret;

	/* Configure controller */
	host->mode_bits = SPI_CPOL | SPI_CPHA | SPI_CS_HIGH;
	host->bits_per_word_mask = SPI_BPW_MASK(8) | SPI_BPW_MASK(16);
	host->setup = my_spi_setup;
	host->transfer_one = my_spi_transfer_one;
	host->set_cs = my_spi_set_cs;
	host->num_chipselect = 4;
	host->bus_num = pdev->id;

	/* Register controller */
	ret = devm_spi_register_controller(&pdev->dev, host);
	if (ret) {
		clk_disable_unprepare(ctlr->clk);
		return ret;
	}

	return 0;
}

static int my_spi_remove(struct platform_device *pdev)
{
	struct spi_controller *host = platform_get_drvdata(pdev);
	struct my_spi_controller *ctlr = spi_controller_get_devdata(host);

	clk_disable_unprepare(ctlr->clk);
	return 0;
}

static const struct of_device_id my_spi_of_match[] = {
	{ .compatible = "vendor,my-spi" },
	{ }
};
MODULE_DEVICE_TABLE(of, my_spi_of_match);

static struct platform_driver my_spi_driver = {
	.probe = my_spi_probe,
	.remove = my_spi_remove,
	.driver = {
		.name = "my-spi",
		.of_match_table = my_spi_of_match,
	},
};
module_platform_driver(my_spi_driver);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name <your.email@example.com>");
MODULE_DESCRIPTION("My SPI Controller Driver");
```

### Devicetree Example

```dts
spi0: spi@40000000 {
	compatible = "vendor,my-spi";
	reg = <0x40000000 0x1000>;
	clocks = <&clk_spi0>;
	clock-names = "spi_clk";

	/* Required for SPI controllers */
	#address-cells = <1>;
	#size-cells = <0>;

	num-cs = <4>;

	/* SPI device at CS0 */
	adc@0 {
		compatible = "adi,ad7124";
		reg = <0>;  /* Chip select number */
		spi-max-frequency = <5000000>;
		spi-cpol;
		spi-cpha;
	};
};
```

## Essential Patterns

### transfer_one() vs transfer_one_message()

**Use transfer_one() if**:
- Simpler implementation
- Framework handles message iteration
- Good for interrupt-driven controllers

```c
static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	/* Perform one transfer */
	return 0;  // 0 = success, 1 = in progress, negative = error
}
```

**Use transfer_one_message() if**:
- Need to optimize across multiple transfers
- Custom message handling logic
- Complex CS management

```c
static int my_spi_transfer_one_message(struct spi_controller *host,
				       struct spi_message *msg)
{
	struct spi_transfer *xfer;
	int ret = 0;

	/* Iterate through transfers */
	list_for_each_entry(xfer, &msg->transfers, transfer_list) {
		ret = my_spi_do_transfer(xfer);
		if (ret)
			break;
		msg->actual_length += xfer->len;
	}

	msg->status = ret;
	spi_finalize_current_message(host);  // CRITICAL: Must call this!
	return ret;
}
```

### DMA Integration Pattern

```c
static int my_spi_probe(struct platform_device *pdev)
{
	struct spi_controller *host;

	host = devm_spi_alloc_host(&pdev->dev, sizeof(*ctlr));
	/* ... */

	/* Request DMA channels */
	host->dma_tx = dma_request_chan(&pdev->dev, "tx");
	if (IS_ERR(host->dma_tx))
		host->dma_tx = NULL;  // DMA optional

	host->dma_rx = dma_request_chan(&pdev->dev, "rx");
	if (IS_ERR(host->dma_rx))
		host->dma_rx = NULL;  // DMA optional

	/* Set DMA alignment */
	host->dma_alignment = 4;

	/* ... */
}

static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	/* Use DMA for large transfers */
	if (host->dma_tx && host->dma_rx && xfer->len > 64)
		return my_spi_transfer_one_dma(host, spi, xfer);

	/* Use PIO for small transfers */
	return my_spi_transfer_one_pio(host, spi, xfer);
}
```

### Interrupt-Driven Transfer Pattern

```c
static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(host);

	/* Save transfer state */
	ctlr->current_transfer = xfer;

	/* Start transfer (non-blocking) */
	my_spi_start_transfer(ctlr);

	/* Enable interrupt */
	writel(INT_ENABLE, ctlr->base + INT_CTRL);

	return 1;  // Transfer in progress
}

static irqreturn_t my_spi_irq(int irq, void *dev_id)
{
	struct my_spi_controller *ctlr = dev_id;

	/* Handle interrupt, transfer data */
	/* ... */

	/* If transfer complete */
	if (transfer_complete) {
		spi_finalize_current_transfer(ctlr->host);
	}

	return IRQ_HANDLED;
}
```

## ADI-Specific: AXI SPI Engine

The **AXI SPI Engine** is ADI's FPGA-based SPI controller for high-speed applications.

### Key Features

- **Programmable**: Uses command sequences (not register-based)
- **High Speed**: Optimized for fast ADCs/DACs
- **Offload Mode**: Hardware-triggered autonomous transfers
- **Multi-lane**: Supports dual/quad SPI modes

### Reference

See `drivers/spi/spi-axi-spi-engine.c` for full implementation and `Documentation/devicetree/bindings/spi/adi,axi-spi-engine.yaml` for devicetree binding.

## Key Takeaways

### SPI Controller Checklist

- [ ] Implement required callbacks: `setup()`, `transfer_one()` OR `transfer_one_message()`
- [ ] Optionally implement `set_cs()` (uses GPIO CS if missing)
- [ ] Set `mode_bits` to declare supported SPI modes
- [ ] Set `bits_per_word_mask` for supported word sizes
- [ ] Set `num_chipselect` to number of CS lines
- [ ] Use `devm_spi_alloc_host()` for automatic cleanup
- [ ] Call `spi_finalize_current_message()` or `spi_finalize_current_transfer()` when done
- [ ] Validate configuration in `setup()` callback
- [ ] Add DMA support for large transfers (optional but recommended)
- [ ] Create YAML devicetree binding in `Documentation/devicetree/bindings/spi/`

### Common Pitfalls

1. **Forgetting to call finalize function**: Always call `spi_finalize_current_message()` or `spi_finalize_current_transfer()`
2. **Wrong return value in transfer_one()**: 0 = success, 1 = in progress, negative = error
3. **Not setting mode_bits**: Device drivers won't know which modes are supported
4. **Missing #address-cells/#size-cells in DT**: SPI devices won't be created
5. **Not handling DMA fallback**: Always provide PIO path for small transfers

## Debugging Quick Reference

```bash
# Enable SPI debug
echo "file drivers/spi/spi.c +p" > /sys/kernel/debug/dynamic_debug/control
echo "file drivers/spi/spi-axi-spi-engine.c +p" > /sys/kernel/debug/dynamic_debug/control

# List SPI buses
ls /sys/class/spi_master/

# List SPI devices
ls /sys/bus/spi/devices/

# View statistics
cat /sys/class/spi_master/spi0/statistics/*

# Check kernel log
dmesg | grep -i spi
```

## References

- **Kernel Documentation**:
  - `Documentation/spi/spi-summary.rst` - SPI subsystem overview
  - `Documentation/driver-api/spi.rst` - SPI driver API
- **Header Files**:
  - `include/linux/spi/spi.h` - Core SPI structures and functions
- **Example Drivers**:
  - `drivers/spi/spi-axi-spi-engine.c` - ADI AXI SPI Engine (FPGA)
  - `drivers/spi/spi-cadence.c` - Cadence SPI (Zynq)
  - `drivers/spi/spi-pl022.c` - ARM PrimeCell SPI
