# DMA Provider Implementation

Complete guide for implementing DMA controller drivers. DMA providers expose DMA channels to consumer drivers via the DMAengine framework.

## Core Structures

### struct dma_device

The main registration structure for DMA controllers:

```c
#include <linux/dmaengine.h>
#include "dmaengine.h"  // Internal header for providers

struct my_dma_controller {
	void __iomem *base;
	int irq;
	struct clk *clk;
	struct dma_device dma_dev;
	struct my_dma_chan channels[MAX_CHANNELS];
};

static int my_dma_probe(struct platform_device *pdev)
{
	struct my_dma_controller *dmac;
	struct dma_device *dma_dev;
	int ret;

	dmac = devm_kzalloc(&pdev->dev, sizeof(*dmac), GFP_KERNEL);
	if (!dmac)
		return -ENOMEM;

	dma_dev = &dmac->dma_dev;

	// Initialize channel list
	INIT_LIST_HEAD(&dma_dev->channels);

	// Set device capabilities
	dma_cap_set(DMA_SLAVE, dma_dev->cap_mask);
	dma_cap_set(DMA_CYCLIC, dma_dev->cap_mask);
	dma_cap_set(DMA_MEMCPY, dma_dev->cap_mask);

	// Set supported bus widths (bitmask)
	dma_dev->src_addr_widths = BIT(DMA_SLAVE_BUSWIDTH_1_BYTE) |
	                           BIT(DMA_SLAVE_BUSWIDTH_2_BYTES) |
	                           BIT(DMA_SLAVE_BUSWIDTH_4_BYTES);
	dma_dev->dst_addr_widths = dma_dev->src_addr_widths;

	// Set supported directions
	dma_dev->directions = BIT(DMA_MEM_TO_DEV) |
	                      BIT(DMA_DEV_TO_MEM) |
	                      BIT(DMA_MEM_TO_MEM);

	// Residue granularity
	dma_dev->residue_granularity = DMA_RESIDUE_GRANULARITY_BURST;

	// Device operations (callbacks)
	dma_dev->dev = &pdev->dev;
	dma_dev->device_alloc_chan_resources = my_dma_alloc_chan_resources;
	dma_dev->device_free_chan_resources = my_dma_free_chan_resources;
	dma_dev->device_prep_slave_sg = my_dma_prep_slave_sg;
	dma_dev->device_prep_dma_cyclic = my_dma_prep_dma_cyclic;
	dma_dev->device_config = my_dma_config;
	dma_dev->device_issue_pending = my_dma_issue_pending;
	dma_dev->device_tx_status = my_dma_tx_status;
	dma_dev->device_terminate_all = my_dma_terminate_all;
	dma_dev->device_synchronize = my_dma_synchronize;

	// Add channels to device
	for (i = 0; i < MAX_CHANNELS; i++) {
		struct my_dma_chan *chan = &dmac->channels[i];
		chan->vchan.desc_free = my_desc_free;
		vchan_init(&chan->vchan, dma_dev);
	}

	// Register DMA device
	ret = dma_async_device_register(dma_dev);
	if (ret) {
		dev_err(&pdev->dev, "Failed to register DMA device: %d\n", ret);
		return ret;
	}

	// Register with devicetree for client lookup
	ret = of_dma_controller_register(pdev->dev.of_node, my_of_dma_xlate, dmac);
	if (ret) {
		dma_async_device_unregister(dma_dev);
		return ret;
	}

	platform_set_drvdata(pdev, dmac);
	return 0;
}
```

### Residue Granularity

Indicates how accurately the DMA controller can report remaining bytes:

```c
enum dma_residue_granularity {
	DMA_RESIDUE_GRANULARITY_DESCRIPTOR = 0,  // Only descriptor-level tracking
	DMA_RESIDUE_GRANULARITY_SEGMENT,         // Segment-level (SG entry)
	DMA_RESIDUE_GRANULARITY_BURST,           // Burst-level (most accurate)
};
```

## Virtual DMA Helper (virt-dma.h)

Most modern DMA drivers use the virtual DMA helper library to simplify descriptor management:

```c
#include "virt-dma.h"

struct my_dma_chan {
	struct virt_dma_chan vchan;  // Must be first member
	struct my_dma_desc *current_desc;
	struct list_head active_descs;
};

struct my_dma_desc {
	struct virt_dma_desc vdesc;  // Must be first member
	dma_addr_t src;
	dma_addr_t dst;
	size_t len;
};

static struct my_dma_chan *to_my_chan(struct dma_chan *c)
{
	return container_of(c, struct my_dma_chan, vchan.chan);
}

static struct my_dma_desc *to_my_desc(struct virt_dma_desc *vd)
{
	return container_of(vd, struct my_dma_desc, vdesc);
}
```

## Descriptor Preparation

### Slave SG Preparation

```c
static struct dma_async_tx_descriptor *
my_dma_prep_slave_sg(struct dma_chan *c, struct scatterlist *sgl,
                     unsigned int sg_len, enum dma_transfer_direction direction,
                     unsigned long flags, void *context)
{
	struct my_dma_chan *chan = to_my_chan(c);
	struct my_dma_desc *desc;
	struct scatterlist *sg;
	unsigned int i;

	// Allocate descriptor (GFP_NOWAIT: cannot sleep!)
	desc = kzalloc(sizeof(*desc), GFP_NOWAIT);
	if (!desc)
		return NULL;

	// Process scatter-gather list
	for_each_sg(sgl, sg, sg_len, i) {
		dma_addr_t addr = sg_dma_address(sg);
		size_t len = sg_dma_len(sg);

		// Validate alignment and constraints
		if ((addr & (chan->addr_align - 1)) != 0) {
			dev_err(chan->vchan.chan.device->dev,
			        "Address 0x%llx not aligned\n", addr);
			kfree(desc);
			return NULL;
		}

		// Store SG entry in hardware-specific format
		// ... (hardware-specific code)
	}

	// Return virtual DMA descriptor
	return vchan_tx_prep(&chan->vchan, &desc->vdesc, flags);
}
```

### Cyclic Preparation

```c
static struct dma_async_tx_descriptor *
my_dma_prep_dma_cyclic(struct dma_chan *c, dma_addr_t buf_addr,
                       size_t buf_len, size_t period_len,
                       enum dma_transfer_direction direction,
                       unsigned long flags)
{
	struct my_dma_chan *chan = to_my_chan(c);
	struct my_dma_desc *desc;
	unsigned int num_periods;

	if (period_len == 0 || buf_len % period_len)
		return NULL;

	num_periods = buf_len / period_len;

	desc = kzalloc(sizeof(*desc), GFP_NOWAIT);
	if (!desc)
		return NULL;

	desc->cyclic = true;
	desc->buf_addr = buf_addr;
	desc->buf_len = buf_len;
	desc->period_len = period_len;
	desc->num_periods = num_periods;

	return vchan_tx_prep(&chan->vchan, &desc->vdesc, flags);
}
```

## Issuing Pending Transfers

```c
static void my_dma_issue_pending(struct dma_chan *c)
{
	struct my_dma_chan *chan = to_my_chan(c);
	unsigned long flags;

	spin_lock_irqsave(&chan->vchan.lock, flags);

	// Move pending descriptors to issued list
	if (vchan_issue_pending(&chan->vchan))
		my_start_transfer(chan);

	spin_unlock_irqrestore(&chan->vchan.lock, flags);
}

static void my_start_transfer(struct my_dma_chan *chan)
{
	struct virt_dma_desc *vd;
	struct my_dma_desc *desc;

	if (chan->current_desc)
		return;  // Transfer already in progress

	vd = vchan_next_desc(&chan->vchan);
	if (!vd)
		return;  // No pending descriptors

	list_del(&vd->node);
	chan->current_desc = to_my_desc(vd);
	desc = chan->current_desc;

	// Program hardware to start transfer
	writel(desc->src, chan->base + SRC_ADDR_REG);
	writel(desc->dst, chan->base + DST_ADDR_REG);
	writel(desc->len, chan->base + LEN_REG);
	writel(START_BIT, chan->base + CTRL_REG);
}
```

## Interrupt Handler and Completion

```c
static irqreturn_t my_dma_irq(int irq, void *devid)
{
	struct my_dma_controller *dmac = devid;
	struct my_dma_chan *chan = &dmac->channels[0];
	struct my_dma_desc *desc;
	unsigned int status;

	status = readl(chan->base + STATUS_REG);
	if (!(status & IRQ_PENDING))
		return IRQ_NONE;

	// Clear interrupt
	writel(status, chan->base + STATUS_REG);

	spin_lock(&chan->vchan.lock);

	desc = chan->current_desc;
	if (desc) {
		if (desc->cyclic) {
			// Cyclic transfer: notify period completion
			vchan_cyclic_callback(&desc->vdesc);
		} else {
			// Single/SG transfer: mark complete and start next
			vchan_cookie_complete(&desc->vdesc);
			chan->current_desc = NULL;
			my_start_transfer(chan);
		}
	}

	spin_unlock(&chan->vchan.lock);

	return IRQ_HANDLED;
}
```

## Termination

```c
static int my_dma_terminate_all(struct dma_chan *c)
{
	struct my_dma_chan *chan = to_my_chan(c);
	unsigned long flags;
	LIST_HEAD(head);

	spin_lock_irqsave(&chan->vchan.lock, flags);

	// Stop hardware
	writel(STOP_BIT, chan->base + CTRL_REG);

	// Clear current descriptor
	chan->current_desc = NULL;

	// Get all pending/active descriptors
	vchan_get_all_descriptors(&chan->vchan, &head);

	spin_unlock_irqrestore(&chan->vchan.lock, flags);

	// Free all descriptors (calls desc_free callback)
	vchan_dma_desc_free_list(&chan->vchan, &head);

	return 0;
}

static void my_dma_synchronize(struct dma_chan *c)
{
	struct my_dma_chan *chan = to_my_chan(c);

	// Ensure callbacks have finished
	vchan_synchronize(&chan->vchan);
}
```

## Required Callbacks

DMA providers must implement these callbacks:

```c
struct dma_device {
	// Channel resource management
	int (*device_alloc_chan_resources)(struct dma_chan *chan);
	void (*device_free_chan_resources)(struct dma_chan *chan);

	// Descriptor preparation (implement what hardware supports)
	struct dma_async_tx_descriptor *(*device_prep_slave_sg)(
		struct dma_chan *chan, struct scatterlist *sgl,
		unsigned int sg_len, enum dma_transfer_direction direction,
		unsigned long flags, void *context);

	struct dma_async_tx_descriptor *(*device_prep_dma_cyclic)(
		struct dma_chan *chan, dma_addr_t buf_addr, size_t buf_len,
		size_t period_len, enum dma_transfer_direction direction,
		unsigned long flags);

	struct dma_async_tx_descriptor *(*device_prep_dma_memcpy)(
		struct dma_chan *chan, dma_addr_t dst, dma_addr_t src,
		size_t len, unsigned long flags);

	// Configuration and control
	int (*device_config)(struct dma_chan *chan,
	                     struct dma_slave_config *config);
	int (*device_pause)(struct dma_chan *chan);
	int (*device_resume)(struct dma_chan *chan);
	int (*device_terminate_all)(struct dma_chan *chan);
	void (*device_synchronize)(struct dma_chan *chan);

	// Transfer management
	void (*device_issue_pending)(struct dma_chan *chan);
	enum dma_status (*device_tx_status)(struct dma_chan *chan,
	                                     dma_cookie_t cookie,
	                                     struct dma_tx_state *txstate);
};
```

## ADI AXI DMAC Example

Complete example of a production DMA controller driver. See drivers/dma/dma-axi-dmac.c for full implementation.

### Key Features
- Hardware scatter-gather support
- 2D transfer support
- Cyclic mode
- Partial transfer reporting
- Uni-directional channels (MEM2DEV or DEV2MEM)

### Capability Detection

```c
static int axi_dmac_detect_caps(struct axi_dmac *dmac, unsigned int version)
{
	struct axi_dmac_chan *chan = &dmac->chan;

	// Test cyclic support by writing flag register
	axi_dmac_write(dmac, AXI_DMAC_REG_FLAGS, AXI_DMAC_FLAG_CYCLIC);
	if (axi_dmac_read(dmac, AXI_DMAC_REG_FLAGS) == AXI_DMAC_FLAG_CYCLIC)
		chan->hw_cyclic = true;

	// Test partial transfer reporting
	axi_dmac_write(dmac, AXI_DMAC_REG_FLAGS, AXI_DMAC_FLAG_PARTIAL_REPORT);
	if (axi_dmac_read(dmac, AXI_DMAC_REG_FLAGS) == AXI_DMAC_FLAG_PARTIAL_REPORT)
		chan->hw_partial_xfer = true;

	// Check 2D support
	axi_dmac_write(dmac, AXI_DMAC_REG_Y_LENGTH, 1);
	if (axi_dmac_read(dmac, AXI_DMAC_REG_Y_LENGTH) == 1)
		chan->hw_2d = true;

	// Check scatter-gather support
	axi_dmac_write(dmac, AXI_DMAC_REG_SG_ADDRESS, 0xFFFFFFFF);
	if (axi_dmac_read(dmac, AXI_DMAC_REG_SG_ADDRESS) != 0)
		chan->hw_sg = true;

	return 0;
}
```

### Descriptor Structures

```c
struct axi_dmac_hw_desc {
	u32 flags;
	u32 id;
	u64 dest_addr;
	u64 src_addr;
	u64 next_sg_addr;
	u32 y_len;
	u32 x_len;
	u32 src_stride;
	u32 dst_stride;
	u64 __pad[2];
} __packed;

struct axi_dmac_sg {
	unsigned int partial_len;
	bool schedule_when_free;

	struct axi_dmac_hw_desc *hw;
	dma_addr_t hw_phys;
};

struct axi_dmac_desc {
	struct virt_dma_desc vdesc;
	struct axi_dmac_chan *chan;

	bool cyclic;
	bool have_partial_xfer;

	unsigned int num_submitted;
	unsigned int num_completed;
	unsigned int num_sgs;
	struct axi_dmac_sg sg[] __counted_by(num_sgs);
};
```

## Kernel Documentation

- Provider API: https://docs.kernel.org/driver-api/dmaengine/provider.html
- DMA API Guide: https://docs.kernel.org/core-api/dma-api.html
