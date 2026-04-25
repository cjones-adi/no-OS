# SPI Controller Driver Implementation

Detailed guide for implementing SPI controller (master/host) drivers in Linux kernel. This covers struct spi_controller, transfer methods, chip select management, and the ADI AXI SPI Engine.

## struct spi_controller

The `spi_controller` structure represents an SPI bus master:

```c
struct spi_controller {
	struct device	dev;

	s16			bus_num;  // Bus number (0, 1, 2, ...)
	u16			num_chipselect;  // Number of CS lines

	/* Bitmask of supported mode bits */
	u32			mode_bits;
	u32			buswidth_override_bits;

	/* Limits on transfer size */
	size_t			max_transfer_size;
	size_t			max_message_size;

	/* Lock and queue for transfers */
	struct mutex		io_mutex;
	spinlock_t		queue_lock;
	struct list_head	queue;
	struct spi_message	*cur_msg;
	bool			idling;
	bool			busy;
	bool			running;
	bool			rt;
	bool			auto_runtime_pm;
	bool			cur_msg_prepared;
	bool			cur_msg_mapped;
	bool			last_cs_mode_high;
	bool			last_cs_index_mask;
	u8			last_cs;

	/* DMA channels */
	struct dma_chan		*dma_tx;
	struct dma_chan		*dma_rx;

	/* Controller methods - implement these! */
	int			(*setup)(struct spi_device *spi);
	int			(*set_cs_timing)(struct spi_device *spi);
	int			(*transfer_one_message)(struct spi_controller *ctlr,
							struct spi_message *mesg);
	int			(*transfer_one)(struct spi_controller *ctlr,
						struct spi_device *spi,
						struct spi_transfer *transfer);
	void			(*set_cs)(struct spi_device *spi, bool enable);
	int			(*prepare_transfer_hardware)(struct spi_controller *ctlr);
	int			(*unprepare_transfer_hardware)(struct spi_controller *ctlr);
	int			(*prepare_message)(struct spi_controller *ctlr,
						   struct spi_message *message);
	int			(*unprepare_message)(struct spi_controller *ctlr,
						     struct spi_message *message);
	void			(*cleanup)(struct spi_device *spi);

	/* Controller-specific data */
	void			*controller_data;
};
```

## Allocation and Registration

```c
#include <linux/spi/spi.h>

struct my_spi_controller {
	struct spi_controller	*host;
	void __iomem		*base;
	struct clk		*clk;
	/* Driver-specific fields */
};

static int my_spi_probe(struct platform_device *pdev)
{
	struct spi_controller *host;
	struct my_spi_controller *spi;
	int ret;

	/* Allocate controller + private data */
	host = devm_spi_alloc_host(&pdev->dev, sizeof(*spi));
	if (!host)
		return -ENOMEM;

	/* Get private data */
	spi = spi_controller_get_devdata(host);
	spi->host = host;

	/* Configure controller */
	host->mode_bits = SPI_CPOL | SPI_CPHA | SPI_CS_HIGH;
	host->bits_per_word_mask = SPI_BPW_MASK(8) | SPI_BPW_MASK(16);
	host->setup = my_spi_setup;
	host->transfer_one = my_spi_transfer_one;
	host->set_cs = my_spi_set_cs;
	host->num_chipselect = 4;
	host->bus_num = pdev->id;

	/* Register with SPI framework */
	ret = devm_spi_register_controller(&pdev->dev, host);
	if (ret)
		return ret;

	return 0;
}
```

**Key Functions**:
- `devm_spi_alloc_host()`: Allocate controller with managed cleanup
- `spi_controller_get_devdata()`: Get private data pointer
- `devm_spi_register_controller()`: Register controller (managed)

## Required Controller Methods

### 1. setup() Method

Called when a device is added or reconfigured. Sets up SPI mode, clock rate, and chip select.

**Signature**:

```c
int (*setup)(struct spi_device *spi);
```

**Example**:

```c
static int my_spi_setup(struct spi_device *spi)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(spi->controller);
	u32 config = 0;

	/* Configure SPI mode (CPOL, CPHA) */
	if (spi->mode & SPI_CPOL)
		config |= MY_SPI_CONFIG_CPOL;
	if (spi->mode & SPI_CPHA)
		config |= MY_SPI_CONFIG_CPHA;
	if (spi->mode & SPI_LSB_FIRST)
		config |= MY_SPI_CONFIG_LSB_FIRST;

	/* Set bits per word */
	if (spi->bits_per_word != 8 && spi->bits_per_word != 16) {
		dev_err(&spi->dev, "Unsupported bits_per_word: %d\n",
			spi->bits_per_word);
		return -EINVAL;
	}

	/* Store per-device state if needed */
	spi_set_ctldata(spi, my_per_device_state);

	return 0;
}
```

**Important**:
- Can sleep
- Should validate `spi->mode`, `spi->bits_per_word`, `spi->max_speed_hz`
- Store per-device state with `spi_set_ctldata()` if needed
- Don't modify shared hardware state (transfer is active) - defer to transfer methods

### 2. set_cs() Method

Controls chip select lines. Called by framework before/after transfers.

**Signature**:

```c
void (*set_cs)(struct spi_device *spi, bool enable);
```

**Example**:

```c
static void my_spi_set_cs(struct spi_device *spi, bool enable)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(spi->controller);
	u8 cs = spi_get_chipselect(spi, 0);

	if (enable) {
		/* Assert CS (usually active low) */
		if (spi->mode & SPI_CS_HIGH)
			my_spi_cs_set_high(ctlr, cs);
		else
			my_spi_cs_set_low(ctlr, cs);
	} else {
		/* Deassert CS */
		if (spi->mode & SPI_CS_HIGH)
			my_spi_cs_set_low(ctlr, cs);
		else
			my_spi_cs_set_high(ctlr, cs);
	}
}
```

**Important**:
- `enable = true`: Assert chip select (activate device)
- `enable = false`: Deassert chip select (deactivate device)
- Respect `SPI_CS_HIGH` mode flag
- If not provided, framework uses GPIO CS if available

### 3. cleanup() Method

Frees per-device state allocated in `setup()`.

**Signature**:

```c
void (*cleanup)(struct spi_device *spi);
```

**Example**:

```c
static void my_spi_cleanup(struct spi_device *spi)
{
	struct my_per_device_state *state = spi_get_ctldata(spi);

	kfree(state);
	spi_set_ctldata(spi, NULL);
}
```

## Optional Controller Methods

### prepare_transfer_hardware() / unprepare_transfer_hardware()

Called once before processing queued messages / after queue is empty. Use for power management.

```c
static int my_spi_prepare_hw(struct spi_controller *host)
{
	struct my_spi_controller *spi = spi_controller_get_devdata(host);

	/* Enable clocks */
	clk_prepare_enable(spi->clk);

	/* Power on hardware */
	pm_runtime_get_sync(spi->dev);

	return 0;
}

static int my_spi_unprepare_hw(struct spi_controller *host)
{
	struct my_spi_controller *spi = spi_controller_get_devdata(host);

	/* Disable clocks */
	clk_disable_unprepare(spi->clk);

	/* Power off hardware */
	pm_runtime_put(spi->dev);

	return 0;
}
```

### prepare_message() / unprepare_message()

Called before/after each message. Use for per-message setup.

```c
static int my_spi_prepare_message(struct spi_controller *host,
				  struct spi_message *msg)
{
	/* Lock resources, configure for this message */
	return 0;
}

static int my_spi_unprepare_message(struct spi_controller *host,
				    struct spi_message *msg)
{
	/* Release resources */
	return 0;
}
```

## Controller Configuration

### Mode Bits

Declare supported SPI modes:

```c
host->mode_bits = SPI_CPOL | SPI_CPHA | SPI_CS_HIGH |
		  SPI_LSB_FIRST | SPI_3WIRE;
```

**Common Mode Bits**:
- `SPI_CPOL`: Clock polarity (idle high)
- `SPI_CPHA`: Clock phase (sample on trailing edge)
- `SPI_CS_HIGH`: Chip select active high
- `SPI_LSB_FIRST`: LSB transmitted first
- `SPI_3WIRE`: Bidirectional mode (shared MOSI/MISO)
- `SPI_LOOP`: Loopback mode
- `SPI_NO_CS`: Single device, no CS needed

### Transfer Size Limits

```c
/* Maximum bytes per transfer */
host->max_transfer_size = my_spi_max_transfer_size;

/* Maximum bytes per message */
host->max_message_size = my_spi_max_message_size;

/* Bits per word supported */
host->bits_per_word_mask = SPI_BPW_MASK(8) | SPI_BPW_MASK(16);
```

### Bus Numbering

```c
/* Static bus number */
host->bus_num = pdev->id;

/* Or dynamic assignment */
host->bus_num = -1;  // Framework assigns next available

/* Number of chip selects */
host->num_chipselect = 4;  // Hardware supports 4 CS lines
```

## ADI AXI SPI Engine

The **AXI SPI Engine** is ADI's FPGA-based SPI controller for high-speed applications.

### Architecture

```
┌─────────────────────────────────────┐
│         AXI SPI Engine              │
│  ┌──────────┐  ┌──────────┐        │
│  │ CMD FIFO │  │ SDO FIFO │        │
│  └────┬─────┘  └────┬─────┘        │
│       │             │               │
│  ┌────▼─────────────▼─────┐        │
│  │   Execution Unit       │        │
│  │  (Programmable SPI)    │        │
│  └────┬───────────────────┘        │
│       │                             │
│  ┌────▼─────┐                      │
│  │ SDI FIFO │                      │
│  └──────────┘                      │
└──────┬──────────────────────────────┘
       │
       ▼
   [ SPI Bus ]
```

### Key Features

- **Programmable**: Uses command sequences (not register-based)
- **High Speed**: Optimized for fast ADCs/DACs
- **Offload Mode**: Hardware-triggered autonomous transfers
- **Multi-lane**: Supports dual/quad SPI modes

### Command-Based Operation

The SPI Engine uses commands written to CMD FIFO:

```c
/* Commands */
#define SPI_ENGINE_CMD_TRANSFER(flags, n) \
	((0x0 << 12) | ((flags) << 8) | (n))

#define SPI_ENGINE_CMD_ASSERT(delay, cs) \
	((0x1 << 12) | ((delay) << 8) | (cs))

#define SPI_ENGINE_CMD_WRITE(reg, val) \
	((0x2 << 12) | ((reg) << 8) | (val))

#define SPI_ENGINE_CMD_SLEEP(delay) \
	((0x3 << 12) | (0x1 << 8) | (delay))

/* Example: Read 16 bits */
uint16_t cmd[] = {
	SPI_ENGINE_CMD_WRITE(SPI_ENGINE_CMD_REG_CLK_DIV, clk_div),
	SPI_ENGINE_CMD_WRITE(SPI_ENGINE_CMD_REG_CONFIG, config),
	SPI_ENGINE_CMD_ASSERT(1, 0x1),  // Assert CS
	SPI_ENGINE_CMD_TRANSFER(SPI_ENGINE_TRANSFER_READ, 2),  // Read 2 bytes
	SPI_ENGINE_CMD_ASSERT(1, 0x0),  // Deassert CS
};

/* Write commands to FIFO */
for (i = 0; i < ARRAY_SIZE(cmd); i++)
	writel(cmd[i], spi->base + SPI_ENGINE_REG_CMD_FIFO);
```

### Reference Driver

See `drivers/spi/spi-axi-spi-engine.c` for full implementation.

## Complete Example: Simple SPI Controller

```c
// SPDX-License-Identifier: GPL-2.0-only
#include <linux/clk.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/platform_device.h>
#include <linux/spi/spi.h>

#define MY_SPI_CR		0x00  // Control register
#define MY_SPI_SR		0x04  // Status register
#define MY_SPI_DR		0x08  // Data register
#define MY_SPI_CCR		0x0C  // Clock config register

struct my_spi {
	void __iomem		*base;
	struct clk		*clk;
	struct completion	done;
};

static void my_spi_set_cs(struct spi_device *spi, bool enable)
{
	struct my_spi *mspi = spi_controller_get_devdata(spi->controller);
	u32 val = readl(mspi->base + MY_SPI_CR);

	if (enable)
		val |= BIT(spi_get_chipselect(spi, 0));
	else
		val &= ~BIT(spi_get_chipselect(spi, 0));

	writel(val, mspi->base + MY_SPI_CR);
}

static int my_spi_setup(struct spi_device *spi)
{
	/* Validate configuration */
	if (spi->bits_per_word != 8 && spi->bits_per_word != 16)
		return -EINVAL;

	if (spi->max_speed_hz > 50000000)
		return -EINVAL;

	return 0;
}

static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	struct my_spi *mspi = spi_controller_get_devdata(host);
	const u8 *tx_buf = xfer->tx_buf;
	u8 *rx_buf = xfer->rx_buf;
	unsigned int len = xfer->len;
	unsigned int i;

	/* Set clock divisor */
	writel(clk_get_rate(mspi->clk) / xfer->speed_hz,
	       mspi->base + MY_SPI_CCR);

	/* Transfer data */
	for (i = 0; i < len; i++) {
		/* Write data */
		writeb(tx_buf ? tx_buf[i] : 0, mspi->base + MY_SPI_DR);

		/* Wait for transfer complete */
		while (!(readl(mspi->base + MY_SPI_SR) & BIT(0)))
			cpu_relax();

		/* Read data */
		if (rx_buf)
			rx_buf[i] = readb(mspi->base + MY_SPI_DR);
	}

	return 0;
}

static int my_spi_probe(struct platform_device *pdev)
{
	struct spi_controller *host;
	struct my_spi *mspi;
	int ret;

	host = devm_spi_alloc_host(&pdev->dev, sizeof(*mspi));
	if (!host)
		return -ENOMEM;

	mspi = spi_controller_get_devdata(host);
	platform_set_drvdata(pdev, host);

	mspi->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(mspi->base))
		return PTR_ERR(mspi->base);

	mspi->clk = devm_clk_get(&pdev->dev, NULL);
	if (IS_ERR(mspi->clk))
		return PTR_ERR(mspi->clk);

	ret = clk_prepare_enable(mspi->clk);
	if (ret)
		return ret;

	host->mode_bits = SPI_CPOL | SPI_CPHA | SPI_CS_HIGH;
	host->bits_per_word_mask = SPI_BPW_MASK(8) | SPI_BPW_MASK(16);
	host->setup = my_spi_setup;
	host->transfer_one = my_spi_transfer_one;
	host->set_cs = my_spi_set_cs;
	host->num_chipselect = 4;
	host->bus_num = pdev->id;

	ret = devm_spi_register_controller(&pdev->dev, host);
	if (ret) {
		clk_disable_unprepare(mspi->clk);
		return ret;
	}

	return 0;
}

static int my_spi_remove(struct platform_device *pdev)
{
	struct spi_controller *host = platform_get_drvdata(pdev);
	struct my_spi *mspi = spi_controller_get_devdata(host);

	clk_disable_unprepare(mspi->clk);
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

MODULE_AUTHOR("Author Name <email@example.com>");
MODULE_DESCRIPTION("My SPI Controller Driver");
MODULE_LICENSE("GPL");
```

## Best Practices

### 1. Use Managed Resources

```c
/* Preferred (automatic cleanup) */
host = devm_spi_alloc_host(&pdev->dev, sizeof(*spi));
devm_spi_register_controller(&pdev->dev, host);
devm_clk_get(&pdev->dev, NULL);

/* Avoid manual cleanup */
spi_alloc_host();  // Requires spi_controller_put()
spi_register_controller();  // Requires spi_unregister_controller()
```

### 2. Validate in setup()

```c
static int my_spi_setup(struct spi_device *spi)
{
	/* Check supported modes */
	if (spi->mode & ~(host->mode_bits))
		return -EINVAL;

	/* Check bits_per_word */
	if (!spi_is_bpw_supported(host, spi->bits_per_word))
		return -EINVAL;

	/* Check speed */
	if (spi->max_speed_hz > MAX_SPEED_HZ)
		return -EINVAL;

	return 0;
}
```

### 3. Implement Runtime PM

```c
host->auto_runtime_pm = true;

static int my_spi_runtime_suspend(struct device *dev)
{
	struct spi_controller *host = dev_get_drvdata(dev);
	struct my_spi *spi = spi_controller_get_devdata(host);

	clk_disable_unprepare(spi->clk);
	return 0;
}

static int my_spi_runtime_resume(struct device *dev)
{
	struct spi_controller *host = dev_get_drvdata(dev);
	struct my_spi *spi = spi_controller_get_devdata(host);

	return clk_prepare_enable(spi->clk);
}

static const struct dev_pm_ops my_spi_pm_ops = {
	SET_RUNTIME_PM_OPS(my_spi_runtime_suspend,
			   my_spi_runtime_resume, NULL)
};
```
