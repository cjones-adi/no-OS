# DMA Consumer Usage

Complete guide for using DMA in device drivers. DMA consumers request DMA channels and submit transfers to offload data movement from the CPU.

## Channel Allocation

Device drivers request DMA channels via devicetree, ACPI, or platform data:

```c
#include <linux/dmaengine.h>
#include <linux/completion.h>

struct my_device {
	struct device *dev;
	struct dma_chan *tx_chan;
	struct dma_chan *rx_chan;
	struct completion dma_complete;
};

static int my_probe(struct platform_device *pdev)
{
	struct my_device *mydev;
	int ret;

	mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
	if (!mydev)
		return -ENOMEM;

	mydev->dev = &pdev->dev;
	init_completion(&mydev->dma_complete);

	// Request TX DMA channel (devicetree: dmas = <&dmac 0>;)
	mydev->tx_chan = dma_request_chan(mydev->dev, "tx");
	if (IS_ERR(mydev->tx_chan)) {
		ret = PTR_ERR(mydev->tx_chan);
		if (ret != -EPROBE_DEFER)
			dev_err(mydev->dev, "Failed to get TX DMA channel: %d\n", ret);
		return ret;
	}

	// Request RX DMA channel (devicetree: dma-names = "tx", "rx";)
	mydev->rx_chan = dma_request_chan(mydev->dev, "rx");
	if (IS_ERR(mydev->rx_chan)) {
		ret = PTR_ERR(mydev->rx_chan);
		dma_release_channel(mydev->tx_chan);
		return ret;
	}

	platform_set_drvdata(pdev, mydev);
	return 0;
}

static void my_remove(struct platform_device *pdev)
{
	struct my_device *mydev = platform_get_drvdata(pdev);

	dma_release_channel(mydev->rx_chan);
	dma_release_channel(mydev->tx_chan);
}
```

## Channel Configuration

Before transfers begin, configure the DMA channel with device-specific parameters:

```c
static int my_setup_dma(struct my_device *mydev, resource_size_t phys_base)
{
	struct dma_slave_config rx_conf = {
		.direction      = DMA_DEV_TO_MEM,
		.src_addr       = phys_base + MY_RX_FIFO_REG,  // Hardware FIFO address
		.src_addr_width = DMA_SLAVE_BUSWIDTH_4_BYTES,  // 32-bit transfers
		.src_maxburst   = 4,                           // 4 beats per burst
	};

	struct dma_slave_config tx_conf = {
		.direction      = DMA_MEM_TO_DEV,
		.dst_addr       = phys_base + MY_TX_FIFO_REG,
		.dst_addr_width = DMA_SLAVE_BUSWIDTH_4_BYTES,
		.dst_maxburst   = 4,
	};

	int ret;

	ret = dmaengine_slave_config(mydev->rx_chan, &rx_conf);
	if (ret) {
		dev_err(mydev->dev, "RX DMA config failed: %d\n", ret);
		return ret;
	}

	ret = dmaengine_slave_config(mydev->tx_chan, &tx_conf);
	if (ret) {
		dev_err(mydev->dev, "TX DMA config failed: %d\n", ret);
		return ret;
	}

	return 0;
}
```

### Bus Width Options

```c
enum dma_slave_buswidth {
	DMA_SLAVE_BUSWIDTH_UNDEFINED = 0,
	DMA_SLAVE_BUSWIDTH_1_BYTE    = 1,
	DMA_SLAVE_BUSWIDTH_2_BYTES   = 2,
	DMA_SLAVE_BUSWIDTH_3_BYTES   = 3,
	DMA_SLAVE_BUSWIDTH_4_BYTES   = 4,
	DMA_SLAVE_BUSWIDTH_8_BYTES   = 8,
	DMA_SLAVE_BUSWIDTH_16_BYTES  = 16,
	DMA_SLAVE_BUSWIDTH_32_BYTES  = 32,
	DMA_SLAVE_BUSWIDTH_64_BYTES  = 64,
	DMA_SLAVE_BUSWIDTH_128_BYTES = 128,
};
```

## DMA Mapping: Preparing Buffers for DMA

**Critical**: Map buffers before preparing DMA descriptors. DMAengine expects scatter-gather lists to be already mapped.

### Single Buffer Mapping

```c
static int my_single_transfer(struct my_device *mydev, void *buffer,
                              size_t len, enum dma_data_direction dir)
{
	dma_addr_t dma_addr;
	int ret;

	// Map buffer for DMA
	dma_addr = dma_map_single(mydev->dev, buffer, len, dir);
	if (dma_mapping_error(mydev->dev, dma_addr)) {
		dev_err(mydev->dev, "DMA mapping failed\n");
		return -ENOMEM;
	}

	// Perform DMA transfer (see next section)
	ret = my_submit_dma(mydev, dma_addr, len, dir);

	// Unmap after transfer completes
	dma_unmap_single(mydev->dev, dma_addr, len, dir);

	return ret;
}
```

### Scatter-Gather Mapping

```c
static int my_sg_transfer(struct my_device *mydev, struct scatterlist *sg,
                          unsigned int nents, enum dma_data_direction dir)
{
	int ret, mapped_nents;

	// Map scatter-gather list
	mapped_nents = dma_map_sg(mydev->dev, sg, nents, dir);
	if (mapped_nents == 0) {
		dev_err(mydev->dev, "DMA SG mapping failed\n");
		return -ENOMEM;
	}

	// Perform DMA transfer using mapped_nents (NOT original nents!)
	ret = my_submit_sg_dma(mydev, sg, mapped_nents, dir);

	// Unmap after transfer completes
	dma_unmap_sg(mydev->dev, sg, nents, dir);

	return ret;
}
```

## Prepare and Submit Transfers

### Slave Single Transfer

```c
static void my_dma_callback(void *data)
{
	struct my_device *mydev = data;

	// Called from DMA engine tasklet context
	complete(&mydev->dma_complete);
}

static int my_submit_dma(struct my_device *mydev, dma_addr_t addr,
                         size_t len, enum dma_data_direction dir)
{
	struct dma_async_tx_descriptor *desc;
	struct dma_chan *chan;
	enum dma_transfer_direction dma_dir;
	dma_cookie_t cookie;
	unsigned long flags = DMA_PREP_INTERRUPT | DMA_CTRL_ACK;

	// Select channel and direction
	if (dir == DMA_FROM_DEVICE) {
		chan = mydev->rx_chan;
		dma_dir = DMA_DEV_TO_MEM;
	} else {
		chan = mydev->tx_chan;
		dma_dir = DMA_MEM_TO_DEV;
	}

	// Prepare DMA descriptor
	desc = dmaengine_prep_slave_single(chan, addr, len, dma_dir, flags);
	if (!desc) {
		dev_err(mydev->dev, "Failed to prepare DMA descriptor\n");
		return -ENOMEM;
	}

	// Set completion callback
	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	// Submit descriptor to pending queue
	cookie = dmaengine_submit(desc);
	if (dma_submit_error(cookie)) {
		dev_err(mydev->dev, "Failed to submit DMA\n");
		return -EIO;
	}

	// Start DMA transfer
	dma_async_issue_pending(chan);

	// Wait for completion
	if (!wait_for_completion_timeout(&mydev->dma_complete,
	                                 msecs_to_jiffies(5000))) {
		dev_err(mydev->dev, "DMA transfer timeout\n");
		dmaengine_terminate_sync(chan);
		return -ETIMEDOUT;
	}

	return 0;
}
```

### Scatter-Gather Transfer

```c
static int my_submit_sg_dma(struct my_device *mydev, struct scatterlist *sg,
                            unsigned int nents, enum dma_data_direction dir)
{
	struct dma_async_tx_descriptor *desc;
	struct dma_chan *chan;
	enum dma_transfer_direction dma_dir;
	dma_cookie_t cookie;

	if (dir == DMA_FROM_DEVICE) {
		chan = mydev->rx_chan;
		dma_dir = DMA_DEV_TO_MEM;
	} else {
		chan = mydev->tx_chan;
		dma_dir = DMA_MEM_TO_DEV;
	}

	// Prepare scatter-gather descriptor
	desc = dmaengine_prep_slave_sg(chan, sg, nents, dma_dir,
	                               DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
	if (!desc) {
		dev_err(mydev->dev, "Failed to prepare SG descriptor\n");
		return -ENOMEM;
	}

	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	cookie = dmaengine_submit(desc);
	if (dma_submit_error(cookie))
		return -EIO;

	dma_async_issue_pending(chan);

	if (!wait_for_completion_timeout(&mydev->dma_complete,
	                                 msecs_to_jiffies(5000))) {
		dmaengine_terminate_sync(chan);
		return -ETIMEDOUT;
	}

	return 0;
}
```

## Termination and Synchronization

```c
// Async termination (non-blocking)
dmaengine_terminate_async(mydev->rx_chan);

// Ensure termination complete before freeing resources
dmaengine_synchronize(mydev->rx_chan);

// Or use blocking version (combines both)
dmaengine_terminate_sync(mydev->rx_chan);
```

**Important**: Always call `dmaengine_synchronize()` or `dmaengine_terminate_sync()` before freeing DMA buffers to ensure callbacks have finished.

## Transfer Status

Query the status of a DMA transfer:

```c
enum dma_status status;
struct dma_tx_state state;

status = dmaengine_tx_status(chan, cookie, &state);

switch (status) {
case DMA_COMPLETE:
	// Transfer completed successfully
	break;
case DMA_IN_PROGRESS:
	// Transfer still in progress
	// state.residue contains remaining bytes
	break;
case DMA_PAUSED:
	// Transfer paused
	break;
case DMA_ERROR:
	// Transfer error occurred
	break;
}
```

## Pause and Resume

Some DMA controllers support pausing and resuming transfers:

```c
// Pause transfer
ret = dmaengine_pause(chan);
if (ret)
	dev_err(dev, "DMA pause failed: %d\n", ret);

// Resume transfer
ret = dmaengine_resume(chan);
if (ret)
	dev_err(dev, "DMA resume failed: %d\n", ret);
```

## Consumer API Reference

```c
// Channel allocation
struct dma_chan *dma_request_chan(struct device *dev, const char *name);
struct dma_chan *dma_request_slave_channel(struct device *dev, const char *name);
void dma_release_channel(struct dma_chan *chan);

// Configuration
int dmaengine_slave_config(struct dma_chan *chan, struct dma_slave_config *config);

// Descriptor preparation
struct dma_async_tx_descriptor *dmaengine_prep_slave_single(
	struct dma_chan *chan, dma_addr_t buf, size_t len,
	enum dma_transfer_direction dir, unsigned long flags);

struct dma_async_tx_descriptor *dmaengine_prep_slave_sg(
	struct dma_chan *chan, struct scatterlist *sgl, unsigned int sg_len,
	enum dma_transfer_direction dir, unsigned long flags);

struct dma_async_tx_descriptor *dmaengine_prep_dma_cyclic(
	struct dma_chan *chan, dma_addr_t buf_addr, size_t buf_len,
	size_t period_len, enum dma_transfer_direction dir, unsigned long flags);

// Submission
dma_cookie_t dmaengine_submit(struct dma_async_tx_descriptor *desc);
void dma_async_issue_pending(struct dma_chan *chan);

// Status
enum dma_status dmaengine_tx_status(struct dma_chan *chan, dma_cookie_t cookie,
                                    struct dma_tx_state *txstate);

// Control
int dmaengine_pause(struct dma_chan *chan);
int dmaengine_resume(struct dma_chan *chan);
int dmaengine_terminate_async(struct dma_chan *chan);
int dmaengine_terminate_sync(struct dma_chan *chan);
void dmaengine_synchronize(struct dma_chan *chan);
```

## Kernel Documentation

- Client API: https://docs.kernel.org/driver-api/dmaengine/client.html
- DMA API Guide: https://docs.kernel.org/core-api/dma-api.html
