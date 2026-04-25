# SPI Transfer Handling and DMA

Detailed guide for implementing SPI transfer methods, choosing between transfer_one and transfer_one_message, and integrating DMA support.

## Transfer Methods Overview

The SPI framework provides two approaches for implementing transfers:

### transfer_one() Method

Processes **one transfer at a time**. Framework handles message iteration.

**Signature**:

```c
int (*transfer_one)(struct spi_controller *ctlr,
		    struct spi_device *spi,
		    struct spi_transfer *xfer);
```

**Return Values**:
- **0**: Transfer complete (synchronous)
- **1**: Transfer still in progress (will call `spi_finalize_current_transfer()` later)
- **Negative errno**: Error occurred

**Example (Blocking)**:

```c
static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(host);
	int ret;

	/* Set clock rate */
	my_spi_set_clock(ctlr, xfer->speed_hz);

	/* Configure transfer */
	my_spi_configure(ctlr, spi->mode, xfer->bits_per_word);

	/* Perform transfer (blocking) */
	ret = my_spi_do_blocking_transfer(ctlr, xfer->tx_buf, xfer->rx_buf, xfer->len);

	return ret;  // 0 = success, negative = error
}
```

**Example (Interrupt-Driven)**:

```c
static int my_spi_transfer_one_irq(struct spi_controller *host,
				   struct spi_device *spi,
				   struct spi_transfer *xfer)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(host);

	/* Save transfer state */
	ctlr->current_transfer = xfer;
	ctlr->tx_buf = xfer->tx_buf;
	ctlr->rx_buf = xfer->rx_buf;
	ctlr->len = xfer->len;

	/* Start transfer (non-blocking) */
	my_spi_start_transfer(ctlr);

	return 1;  // Still in progress, IRQ will complete
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

### transfer_one_message() Method

Processes a **complete SPI message** (list of transfers). Framework queues messages and calls this method.

**Signature**:

```c
int (*transfer_one_message)(struct spi_controller *ctlr,
			    struct spi_message *msg);
```

**Example**:

```c
static int my_spi_transfer_one_message(struct spi_controller *host,
				       struct spi_message *msg)
{
	struct my_spi_controller *spi = spi_controller_get_devdata(host);
	struct spi_device *spi_dev = msg->spi;
	struct spi_transfer *xfer;
	int ret = 0;

	/* Iterate through transfers in message */
	list_for_each_entry(xfer, &msg->transfers, transfer_list) {
		/* Set clock divisor */
		ret = my_spi_set_speed(spi, xfer->speed_hz);
		if (ret)
			goto out;

		/* Perform transfer */
		ret = my_spi_do_transfer(spi, xfer);
		if (ret)
			goto out;

		msg->actual_length += xfer->len;

		/* Delay between transfers */
		if (xfer->delay.value)
			spi_delay_exec(&xfer->delay, xfer);

		/* Change CS if needed */
		if (xfer->cs_change) {
			/* ... handle CS toggle ... */
		}
	}

out:
	msg->status = ret;
	spi_finalize_current_message(host);  // CRITICAL: Must call this!
	return ret;
}
```

**Critical**:
- **MUST** call `spi_finalize_current_message()` when done
- Update `msg->actual_length` with bytes transferred
- Set `msg->status` to 0 (success) or negative errno
- Handle `xfer->delay` between transfers
- Handle `xfer->cs_change` for CS toggling

### Choosing the Right Method

**Use transfer_one if**:
- Simpler implementation
- Framework handles message iteration automatically
- Good for interrupt-driven controllers
- Standard transfer handling is sufficient

**Use transfer_one_message if**:
- Need to optimize across multiple transfers
- Custom message handling logic required
- Complex CS management between transfers
- Performance-critical applications

## DMA Support

### Setting Up DMA Channels

```c
static int my_spi_probe(struct platform_device *pdev)
{
	struct spi_controller *host;
	struct my_spi_controller *spi;

	host = devm_spi_alloc_host(&pdev->dev, sizeof(*spi));
	/* ... */

	/* Request DMA channels */
	host->dma_tx = dma_request_chan(&pdev->dev, "tx");
	if (IS_ERR(host->dma_tx)) {
		dev_warn(&pdev->dev, "Failed to get TX DMA channel\n");
		host->dma_tx = NULL;
	}

	host->dma_rx = dma_request_chan(&pdev->dev, "rx");
	if (IS_ERR(host->dma_rx)) {
		dev_warn(&pdev->dev, "Failed to get RX DMA channel\n");
		host->dma_rx = NULL;
	}

	/* Set DMA alignment requirements */
	host->dma_alignment = 4;  // 4-byte alignment

	/* ... */
}
```

### DMA Transfer Implementation

```c
static int my_spi_transfer_one_dma(struct spi_controller *host,
				   struct spi_device *spi,
				   struct spi_transfer *xfer)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(host);
	struct dma_async_tx_descriptor *tx_desc = NULL, *rx_desc = NULL;
	int ret;

	/* Prepare RX DMA */
	if (xfer->rx_buf) {
		struct dma_slave_config rx_conf = {
			.direction = DMA_DEV_TO_MEM,
			.src_addr = ctlr->phys_base + MY_SPI_RX_FIFO,
			.src_addr_width = DMA_SLAVE_BUSWIDTH_1_BYTE,
			.src_maxburst = 1,
		};

		dmaengine_slave_config(host->dma_rx, &rx_conf);

		rx_desc = dmaengine_prep_slave_sg(host->dma_rx,
						   xfer->rx_sg.sgl,
						   xfer->rx_sg.nents,
						   DMA_DEV_TO_MEM,
						   DMA_PREP_INTERRUPT);
		if (!rx_desc)
			return -ENOMEM;

		rx_desc->callback = my_spi_dma_rx_callback;
		rx_desc->callback_param = ctlr;
	}

	/* Prepare TX DMA */
	if (xfer->tx_buf) {
		struct dma_slave_config tx_conf = {
			.direction = DMA_MEM_TO_DEV,
			.dst_addr = ctlr->phys_base + MY_SPI_TX_FIFO,
			.dst_addr_width = DMA_SLAVE_BUSWIDTH_1_BYTE,
			.dst_maxburst = 1,
		};

		dmaengine_slave_config(host->dma_tx, &tx_conf);

		tx_desc = dmaengine_prep_slave_sg(host->dma_tx,
						   xfer->tx_sg.sgl,
						   xfer->tx_sg.nents,
						   DMA_MEM_TO_DEV,
						   DMA_PREP_INTERRUPT);
		if (!tx_desc) {
			dmaengine_terminate_sync(host->dma_rx);
			return -ENOMEM;
		}

		tx_desc->callback = my_spi_dma_tx_callback;
		tx_desc->callback_param = ctlr;
	}

	/* Submit DMA transfers */
	reinit_completion(&ctlr->dma_completion);

	if (rx_desc)
		dmaengine_submit(rx_desc);
	if (tx_desc)
		dmaengine_submit(tx_desc);

	dma_async_issue_pending(host->dma_rx);
	dma_async_issue_pending(host->dma_tx);

	/* Start SPI transfer */
	my_spi_start_transfer(ctlr);

	return 1;  // Transfer in progress
}

static void my_spi_dma_rx_callback(void *data)
{
	struct my_spi_controller *ctlr = data;

	complete(&ctlr->dma_completion);
	spi_finalize_current_transfer(ctlr->host);
}
```

### DMA Fallback Pattern

Implement both DMA and PIO (Programmed I/O) paths:

```c
static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	struct my_spi_controller *ctlr = spi_controller_get_devdata(host);

	/* Use DMA for large transfers if available */
	if (host->dma_tx && host->dma_rx && xfer->len > 64)
		return my_spi_transfer_one_dma(host, spi, xfer);

	/* Fall back to PIO for small transfers or if DMA unavailable */
	return my_spi_transfer_one_pio(host, spi, xfer);
}
```

## Transfer Delays

Handle delays between transfers using `spi_delay_exec()`:

```c
/* In transfer_one_message() */
list_for_each_entry(xfer, &msg->transfers, transfer_list) {
	/* Perform transfer */
	ret = my_spi_do_transfer(spi, xfer);
	if (ret)
		goto out;

	/* Delay after transfer */
	if (xfer->delay.value)
		spi_delay_exec(&xfer->delay, xfer);
}
```

## Chip Select Management

### Basic CS Control

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

### CS Change Between Transfers

Handle `xfer->cs_change` flag in `transfer_one_message()`:

```c
list_for_each_entry(xfer, &msg->transfers, transfer_list) {
	/* Perform transfer */
	ret = my_spi_do_transfer(spi, xfer);
	if (ret)
		goto out;

	/* Handle CS change */
	if (xfer->cs_change) {
		/* If not the last transfer, toggle CS */
		if (list_is_last(&xfer->transfer_list, &msg->transfers)) {
			/* Last transfer: keep CS asserted if cs_change=1 */
		} else {
			/* Mid-message: toggle CS */
			my_spi_set_cs(msg->spi, false);  // Deassert
			spi_delay_exec(&xfer->cs_change_delay, xfer);
			my_spi_set_cs(msg->spi, true);   // Reassert
		}
	}
}
```

## Error Handling

### Proper Error Cleanup

```c
static int my_spi_transfer_one_message(struct spi_controller *host,
				       struct spi_message *msg)
{
	int ret;

	ret = my_spi_do_transfer(host, msg);

	/* Set message status */
	msg->status = ret;

	/* Always finalize, even on error */
	spi_finalize_current_message(host);

	return ret;
}
```

### DMA Error Handling

```c
static int my_spi_transfer_one_dma(struct spi_controller *host,
				   struct spi_device *spi,
				   struct spi_transfer *xfer)
{
	struct dma_async_tx_descriptor *tx_desc = NULL, *rx_desc = NULL;

	/* Prepare RX DMA */
	if (xfer->rx_buf) {
		rx_desc = dmaengine_prep_slave_sg(host->dma_rx, ...);
		if (!rx_desc) {
			dev_err(&spi->dev, "Failed to prepare RX DMA\n");
			return -ENOMEM;
		}
	}

	/* Prepare TX DMA */
	if (xfer->tx_buf) {
		tx_desc = dmaengine_prep_slave_sg(host->dma_tx, ...);
		if (!tx_desc) {
			dev_err(&spi->dev, "Failed to prepare TX DMA\n");
			/* Clean up RX DMA if already prepared */
			if (rx_desc)
				dmaengine_terminate_sync(host->dma_rx);
			return -ENOMEM;
		}
	}

	/* Submit and start DMA */
	/* ... */
}
```

## Performance Optimization

### Use DMA for Large Transfers

```c
#define DMA_MIN_BYTES	64

static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	/* Use DMA for transfers >= 64 bytes */
	if (xfer->len >= DMA_MIN_BYTES)
		return my_spi_transfer_one_dma(host, spi, xfer);

	/* Use PIO for small transfers */
	return my_spi_transfer_one_pio(host, spi, xfer);
}
```

### Batch Register Writes

Minimize MMIO accesses by batching register writes:

```c
/* Bad: Multiple register writes */
writel(config, base + CONFIG_REG);
writel(speed, base + SPEED_REG);
writel(mode, base + MODE_REG);

/* Better: Batch configuration */
struct spi_config cfg = {
	.config = config,
	.speed = speed,
	.mode = mode,
};
my_spi_apply_config(ctlr, &cfg);
```

## Important DMA Notes

- Device drivers must provide DMA-safe buffers (not on stack!)
- Use `xfer->tx_sg` and `xfer->rx_sg` for scatter-gather
- Set `host->dma_alignment` if hardware requires aligned buffers
- Implement DMA callbacks to finalize transfers
- Always provide PIO fallback for small transfers
- Test DMA path with large transfers (> 1KB)
