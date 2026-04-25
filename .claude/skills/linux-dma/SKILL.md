---
name: linux-dma
description: Complete guide to Linux DMAengine framework for high-speed data transfers. Use when implementing DMA controller drivers (providers), adding DMA support to device drivers (consumers), working with scatter-gather/cyclic/interleaved transfers, optimizing throughput, or debugging DMA issues.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: dma
  tags:
    - dma
    - dmaengine
    - dma-controller
    - dma-consumer
    - scatter-gather
    - cyclic-dma
    - virt-dma
    - dma-mapping
    - axi-dmac
  dependencies:
    - linux-devicetree
    - linux-iio
    - linux-spi-controller
    - linux-debugging
  learning_objectives:
    - Implement DMA controller drivers with struct dma_device
    - Use DMAengine consumer API for device driver DMA support
    - Work with scatter-gather, cyclic, and interleaved transfers
    - Integrate virtual DMA helper (virt-dma.h) for descriptor management
    - Handle DMA mapping and cache coherency correctly
    - Configure DMA channels with slave_config
    - Debug DMA timeouts, mapping failures, and residue issues
---

# Linux DMAengine Framework

Quick-start guide for implementing DMA controller drivers (providers) and using DMA in device drivers (consumers).

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/provider-implementation.md**:
- User mentions: "implement DMA controller", "DMA driver", "dma_device", "virt-dma", "DMA provider"
- Questions about: device_prep_slave_sg, device_prep_dma_cyclic, device_issue_pending, device_tx_status callbacks
- User asks: "how to implement DMA controller", "create DMA driver", "vchan_cookie_complete", "AXI DMAC"
- Topics: residue granularity, hardware descriptor management, interrupt handling, vchan helpers, of_dma_controller_register

**Triggers to read reference/consumer-usage.md**:
- User mentions: "use DMA", "consumer driver", "dma_request_chan", "dmaengine_prep_slave_sg", "add DMA support"
- Questions about: channel allocation, dmaengine_slave_config, DMA mapping, callbacks, termination
- User asks: "how to use DMA in driver", "DMA transfer", "DMA completion", "dma_async_issue_pending"
- Topics: dma_slave_config, bus width, burst size, DMA_PREP_INTERRUPT, dmaengine_terminate_sync

**Triggers to read reference/transfer-types.md**:
- User mentions: "scatter-gather", "cyclic DMA", "memcpy", "interleaved", "2D transfer", "streaming"
- Questions about: dmaengine_prep_slave_sg, dmaengine_prep_dma_cyclic, dmaengine_prep_interleaved_dma
- User asks: "continuous DMA", "audio DMA", "ring buffer", "SG list", "strided transfer"
- Topics: period callbacks, nents vs mapped_nents, descriptor flags, burst size tuning

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "DTS", "#dma-cells", "dmas property", "dma-names"
- Questions about: DMA controller binding, consumer binding, channel specifier, dma-channels
- User asks: "how to specify DMA in DT", "devicetree example", "DMA channel reference"
- Topics: of_dma_xlate, dma-router, multi-cell controllers, AXI DMAC binding

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "DMA timeout", "mapping failed", "corruption", "residue wrong"
- Questions about: dynamic debug, ftrace, DMA-API debugging, performance measurement
- User says: "troubleshoot", "diagnose", "DMA error", "transfer stuck", "callback not firing"
- Topics: /sys/kernel/debug/dma-api, CONFIG_DMA_API_DEBUG, register dumps, throughput measurement

---

## When to Use This Skill

- Implementing DMA controller drivers for SoC DMA engines or FPGA IP cores
- Adding DMA support to device drivers (SPI, I2C, UART, IIO, network)
- Working with high-throughput streaming data (ADC/DAC, audio, video)
- Optimizing data transfer performance
- Debugging DMA transfer issues

## What is the Linux DMAengine Framework?

DMAengine separates DMA functionality into two roles:
- **DMA Providers** (controllers): Drivers that manage DMA hardware
- **DMA Consumers** (clients): Device drivers that use DMA channels

### Two-Sided API

```
┌───────────────────────────────┐
│    DMA Consumer (Client)      │  Device drivers (SPI, IIO, UART, etc.)
│    Request channels           │  Use dmaengine_prep_* functions
│    Submit descriptors         │  Receive completion callbacks
└───────────────┬───────────────┘
                │ dmaengine API
                ↓
┌───────────────────────────────┐
│    DMA Provider (Controller)  │  DMA controller drivers
│    Manage hardware channels   │  Implement device_prep_* callbacks
│    Execute transfers          │  Generate interrupts
└───────────────────────────────┘
```

**Key principle**: Consumers and providers are completely decoupled. Consumers use generic `dmaengine_*` functions, while providers implement controller-specific `device_*` callbacks.

## Quick Start: DMA Consumer

### 1. Request DMA Channel

```c
#include <linux/dmaengine.h>

struct my_device {
	struct device *dev;
	struct dma_chan *rx_chan;
	struct completion dma_complete;
};

static int my_probe(struct platform_device *pdev)
{
	struct my_device *mydev;

	mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
	if (!mydev)
		return -ENOMEM;

	mydev->dev = &pdev->dev;
	init_completion(&mydev->dma_complete);

	// Request DMA channel (from devicetree: dmas = <&dmac 0>;)
	mydev->rx_chan = dma_request_chan(mydev->dev, "rx");
	if (IS_ERR(mydev->rx_chan))
		return PTR_ERR(mydev->rx_chan);

	return 0;
}

static void my_remove(struct platform_device *pdev)
{
	struct my_device *mydev = platform_get_drvdata(pdev);
	dma_release_channel(mydev->rx_chan);
}
```

### 2. Configure DMA Channel

```c
static int my_setup_dma(struct my_device *mydev, resource_size_t phys_base)
{
	struct dma_slave_config config = {
		.direction      = DMA_DEV_TO_MEM,
		.src_addr       = phys_base + MY_RX_FIFO_REG,
		.src_addr_width = DMA_SLAVE_BUSWIDTH_4_BYTES,
		.src_maxburst   = 4,  // 4 beats per burst
	};

	return dmaengine_slave_config(mydev->rx_chan, &config);
}
```

### 3. Map, Prepare, and Submit Transfer

```c
static void my_dma_callback(void *data)
{
	struct my_device *mydev = data;
	complete(&mydev->dma_complete);
}

static int my_dma_transfer(struct my_device *mydev, void *buffer, size_t len)
{
	struct dma_async_tx_descriptor *desc;
	dma_addr_t dma_addr;
	dma_cookie_t cookie;

	// 1. Map buffer for DMA
	dma_addr = dma_map_single(mydev->dev, buffer, len, DMA_FROM_DEVICE);
	if (dma_mapping_error(mydev->dev, dma_addr))
		return -ENOMEM;

	// 2. Prepare DMA descriptor
	desc = dmaengine_prep_slave_single(mydev->rx_chan, dma_addr, len,
	                                   DMA_DEV_TO_MEM,
	                                   DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
	if (!desc) {
		dma_unmap_single(mydev->dev, dma_addr, len, DMA_FROM_DEVICE);
		return -ENOMEM;
	}

	// 3. Set callback
	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	// 4. Submit descriptor
	cookie = dmaengine_submit(desc);
	if (dma_submit_error(cookie)) {
		dma_unmap_single(mydev->dev, dma_addr, len, DMA_FROM_DEVICE);
		return -EIO;
	}

	// 5. Start DMA transfer
	dma_async_issue_pending(mydev->rx_chan);

	// 6. Wait for completion
	if (!wait_for_completion_timeout(&mydev->dma_complete,
	                                 msecs_to_jiffies(5000))) {
		dmaengine_terminate_sync(mydev->rx_chan);
		dma_unmap_single(mydev->dev, dma_addr, len, DMA_FROM_DEVICE);
		return -ETIMEDOUT;
	}

	// 7. Unmap after completion
	dma_unmap_single(mydev->dev, dma_addr, len, DMA_FROM_DEVICE);

	return 0;
}
```

## Quick Start: DMA Provider

### 1. Define Controller and Channel Structures

```c
#include <linux/dmaengine.h>
#include "dmaengine.h"
#include "virt-dma.h"

struct my_dma_controller {
	void __iomem *base;
	int irq;
	struct dma_device dma_dev;
	struct my_dma_chan channels[MAX_CHANNELS];
};

struct my_dma_chan {
	struct virt_dma_chan vchan;
	struct my_dma_desc *current_desc;
};

struct my_dma_desc {
	struct virt_dma_desc vdesc;
	dma_addr_t src;
	dma_addr_t dst;
	size_t len;
	bool cyclic;
};
```

### 2. Register DMA Device

```c
static int my_dma_probe(struct platform_device *pdev)
{
	struct my_dma_controller *dmac;
	struct dma_device *dma_dev;
	int ret, i;

	dmac = devm_kzalloc(&pdev->dev, sizeof(*dmac), GFP_KERNEL);
	if (!dmac)
		return -ENOMEM;

	dma_dev = &dmac->dma_dev;

	INIT_LIST_HEAD(&dma_dev->channels);

	// Set capabilities
	dma_cap_set(DMA_SLAVE, dma_dev->cap_mask);
	dma_cap_set(DMA_CYCLIC, dma_dev->cap_mask);

	dma_dev->src_addr_widths = BIT(DMA_SLAVE_BUSWIDTH_4_BYTES);
	dma_dev->dst_addr_widths = BIT(DMA_SLAVE_BUSWIDTH_4_BYTES);
	dma_dev->directions = BIT(DMA_MEM_TO_DEV) | BIT(DMA_DEV_TO_MEM);
	dma_dev->residue_granularity = DMA_RESIDUE_GRANULARITY_BURST;

	// Set callbacks
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

	// Initialize channels
	for (i = 0; i < MAX_CHANNELS; i++) {
		struct my_dma_chan *chan = &dmac->channels[i];
		chan->vchan.desc_free = my_desc_free;
		vchan_init(&chan->vchan, dma_dev);
	}

	// Register DMA device
	ret = dma_async_device_register(dma_dev);
	if (ret)
		return ret;

	// Register for devicetree lookup
	ret = of_dma_controller_register(pdev->dev.of_node,
	                                  my_of_dma_xlate, dmac);
	if (ret) {
		dma_async_device_unregister(dma_dev);
		return ret;
	}

	return 0;
}
```

### 3. Implement Descriptor Preparation

```c
static struct dma_async_tx_descriptor *
my_dma_prep_slave_sg(struct dma_chan *c, struct scatterlist *sgl,
                     unsigned int sg_len, enum dma_transfer_direction direction,
                     unsigned long flags, void *context)
{
	struct my_dma_chan *chan = container_of(c, struct my_dma_chan, vchan.chan);
	struct my_dma_desc *desc;

	desc = kzalloc(sizeof(*desc), GFP_NOWAIT);
	if (!desc)
		return NULL;

	// Fill descriptor with hardware-specific data
	// ...

	return vchan_tx_prep(&chan->vchan, &desc->vdesc, flags);
}
```

### 4. Implement Issue Pending and IRQ Handler

```c
static void my_dma_issue_pending(struct dma_chan *c)
{
	struct my_dma_chan *chan = container_of(c, struct my_dma_chan, vchan.chan);
	unsigned long flags;

	spin_lock_irqsave(&chan->vchan.lock, flags);
	if (vchan_issue_pending(&chan->vchan))
		my_start_transfer(chan);
	spin_unlock_irqrestore(&chan->vchan.lock, flags);
}

static irqreturn_t my_dma_irq(int irq, void *devid)
{
	struct my_dma_controller *dmac = devid;
	struct my_dma_chan *chan = &dmac->channels[0];
	struct my_dma_desc *desc;

	// Read and clear interrupt status
	// ...

	spin_lock(&chan->vchan.lock);

	desc = chan->current_desc;
	if (desc) {
		if (desc->cyclic) {
			vchan_cyclic_callback(&desc->vdesc);
		} else {
			vchan_cookie_complete(&desc->vdesc);
			chan->current_desc = NULL;
			my_start_transfer(chan);
		}
	}

	spin_unlock(&chan->vchan.lock);

	return IRQ_HANDLED;
}
```

## Transfer Types

### Single Transfer
```c
desc = dmaengine_prep_slave_single(chan, dma_addr, len, direction, flags);
```

### Scatter-Gather Transfer
```c
// Map SG list first
mapped_nents = dma_map_sg(dev, sgl, nents, dir);

// Prepare with mapped_nents (NOT original nents!)
desc = dmaengine_prep_slave_sg(chan, sgl, mapped_nents, direction, flags);
```

### Cyclic Transfer (Audio/Streaming)
```c
// Continuous looping for streaming applications
desc = dmaengine_prep_dma_cyclic(chan, buf_addr, buf_len,
                                 period_len, direction, flags);
// Callback fires every period_len bytes
```

### Memory-to-Memory
```c
desc = dmaengine_prep_dma_memcpy(chan, dst_addr, src_addr, len, flags);
```

## DMA Mapping Critical Rules

**Rule 1**: Map buffers BEFORE preparing descriptors
```c
// CORRECT:
dma_addr = dma_map_single(dev, buf, len, DMA_FROM_DEVICE);
desc = dmaengine_prep_slave_single(chan, dma_addr, len, ...);

// WRONG:
desc = dmaengine_prep_slave_single(chan, virt_to_phys(buf), len, ...);  // NO!
```

**Rule 2**: Unmap AFTER transfer completes
```c
// CORRECT:
dma_async_issue_pending(chan);
wait_for_completion(&complete);
dma_unmap_single(dev, dma_addr, len, DMA_FROM_DEVICE);

// WRONG:
dma_async_issue_pending(chan);
dma_unmap_single(dev, dma_addr, len, DMA_FROM_DEVICE);  // Still running!
```

**Rule 3**: Match map/unmap directions
```c
dma_addr = dma_map_single(dev, buf, len, DMA_FROM_DEVICE);
// ...
dma_unmap_single(dev, dma_addr, len, DMA_FROM_DEVICE);  // Must match
```

**Rule 4**: For SG, use mapped_nents for prep, original nents for unmap
```c
mapped = dma_map_sg(dev, sgl, nents, dir);
desc = dmaengine_prep_slave_sg(chan, sgl, mapped, ...);  // Use mapped
// ...
dma_unmap_sg(dev, sgl, nents, dir);  // Use original
```

## Devicetree Bindings

### DMA Controller
```dts
dmac: dma@40000000 {
	compatible = "vendor,dma-controller";
	reg = <0x40000000 0x1000>;
	interrupts = <GIC_SPI 10 IRQ_TYPE_LEVEL_HIGH>;
	#dma-cells = <1>;
	dma-channels = <8>;
};
```

### DMA Consumer
```dts
spi0: spi@40100000 {
	compatible = "vendor,spi-controller";
	reg = <0x40100000 0x1000>;

	dmas = <&dmac 2>, <&dmac 3>;
	dma-names = "tx", "rx";
};
```

Driver requests channels by name:
```c
tx_chan = dma_request_chan(dev, "tx");  // Gets channel 2
rx_chan = dma_request_chan(dev, "rx");  // Gets channel 3
```

## Common Pitfalls and Solutions

### Timeout Issues
```c
// Problem: DMA_PREP_INTERRUPT flag missing
desc = dmaengine_prep_slave_single(chan, addr, len, dir, 0);  // NO callback!

// Solution: Always set DMA_PREP_INTERRUPT
desc = dmaengine_prep_slave_single(chan, addr, len, dir,
                                   DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
```

### Memory Corruption
```c
// Problem: Unmap before DMA completes
dma_async_issue_pending(chan);
dma_unmap_single(dev, addr, len, dir);  // DMA still running!

// Solution: Wait for completion
dma_async_issue_pending(chan);
wait_for_completion(&complete);
dmaengine_synchronize(chan);  // Ensure callbacks done
dma_unmap_single(dev, addr, len, dir);
```

### Provider Callback Not Firing
```c
// Problem: Forgot to call vchan_cookie_complete()
static irqreturn_t my_dma_irq(int irq, void *devid)
{
	// Clear interrupt
	// ... but never notify completion!
	return IRQ_HANDLED;  // Consumer waits forever
}

// Solution: Always complete descriptors
static irqreturn_t my_dma_irq(int irq, void *devid)
{
	spin_lock(&chan->vchan.lock);
	if (chan->current_desc)
		vchan_cookie_complete(&chan->current_desc->vdesc);
	spin_unlock(&chan->vchan.lock);
	return IRQ_HANDLED;
}
```

## Quick Debug Commands

```bash
# Enable DMA debug
echo 'file dmaengine.c +p' > /sys/kernel/debug/dynamic_debug/control
echo 'file dma-axi-dmac.c +p' > /sys/kernel/debug/dynamic_debug/control

# List DMA channels
ls /sys/class/dma/

# Check DMA-API errors (needs CONFIG_DMA_API_DEBUG=y)
cat /sys/kernel/debug/dma-api/error_count
cat /sys/kernel/debug/dma-api/dump

# Check interrupts
cat /proc/interrupts | grep dma

# Watch kernel messages
dmesg -w | grep -i dma
```

## Key API Functions Summary

### Consumer API
```c
// Channel management
struct dma_chan *dma_request_chan(struct device *dev, const char *name);
void dma_release_channel(struct dma_chan *chan);
int dmaengine_slave_config(struct dma_chan *chan, struct dma_slave_config *config);

// Descriptor preparation
struct dma_async_tx_descriptor *dmaengine_prep_slave_single(...);
struct dma_async_tx_descriptor *dmaengine_prep_slave_sg(...);
struct dma_async_tx_descriptor *dmaengine_prep_dma_cyclic(...);

// Submission
dma_cookie_t dmaengine_submit(struct dma_async_tx_descriptor *desc);
void dma_async_issue_pending(struct dma_chan *chan);

// Control
int dmaengine_terminate_sync(struct dma_chan *chan);
void dmaengine_synchronize(struct dma_chan *chan);
```

### Provider API (virt-dma helpers)
```c
// Channel initialization
void vchan_init(struct virt_dma_chan *vc, struct dma_device *dmadev);

// Descriptor management
struct dma_async_tx_descriptor *vchan_tx_prep(...);
void vchan_cookie_complete(struct virt_dma_desc *vd);
void vchan_cyclic_callback(struct virt_dma_desc *vd);

// Pending queue
bool vchan_issue_pending(struct virt_dma_chan *vc);
struct virt_dma_desc *vchan_next_desc(struct virt_dma_chan *vc);

// Termination
void vchan_get_all_descriptors(struct virt_dma_chan *vc, struct list_head *head);
void vchan_dma_desc_free_list(struct virt_dma_chan *vc, struct list_head *head);
void vchan_synchronize(struct virt_dma_chan *vc);
```

## Production Example: ADI AXI DMAC

Complete DMA controller driver for FPGA designs:
- Location: `drivers/dma/dma-axi-dmac.c`
- Features: Hardware SG, cyclic mode, 2D transfers, partial residue reporting
- Binding: `Documentation/devicetree/bindings/dma/adi,axi-dmac.yaml`

Key patterns demonstrated:
- Virtual DMA helper usage
- Hardware capability detection
- Coherent memory allocation for HW descriptors
- Uni-directional channel configuration
- IIO buffer backend integration

## Architecture Overview

```
Consumer Driver              DMAengine Core              Provider Driver
───────────────              ──────────────              ───────────────

dma_request_chan() ──────────> Find channel
                                    │
                                    └──────────────────> of_dma_xlate()
                                                         Allocate channel

dmaengine_slave_config() ────────> Validate ────────> device_config()
                                                       Store config

dma_map_single() ────────────> DMA-API
                                Map buffer

dmaengine_prep_slave_sg() ───────> Validate ────────> device_prep_slave_sg()
                                                       Build HW descriptors
                                                       vchan_tx_prep()

dmaengine_submit() ──────────────> Queue desc

dma_async_issue_pending() ───────> Process queue ───> device_issue_pending()
                                                       Start transfer

    [Wait]                              [Transfer]           [HW running]

    [IRQ] <───────────────────────────────────────────── Hardware interrupt
                                                         device_irq()
                                                         vchan_cookie_complete()

callback() <──────────────────── Tasklet runs
                                 Fire callbacks

dmaengine_synchronize() ─────────> Wait tasklet

dma_unmap_single() ──────────────> DMA-API
                                   Unmap buffer

dma_release_channel() ───────────> Free channel
```

## Virtual DMA Helper Benefits

The virt-dma helper (`drivers/dma/virt-dma.h`) simplifies provider implementation:

1. **Descriptor management**: Automatic queuing, lifecycle tracking
2. **Cookie handling**: Automatic cookie generation and tracking
3. **Tasklet integration**: Safe callback execution context
4. **Locking helpers**: Simplified spinlock patterns
5. **Cyclic mode support**: Built-in period callback handling

Use virt-dma unless you have specific reasons not to (e.g., hardware manages descriptors).

## Performance Tips

1. **Use cyclic mode for streaming**: More efficient than re-submitting descriptors
2. **Batch transfers with SG**: Reduces descriptor overhead
3. **Match burst size to FIFO depth**: Optimize src_maxburst/dst_maxburst
4. **Start next transfer in IRQ**: Minimize idle time between transfers
5. **Use coherent buffers for small, frequent transfers**: Avoid map/unmap overhead

## Related Skills

- **linux-iio**: IIO buffered acquisition with DMA backends
- **linux-spi-controller**: SPI DMA integration
- **linux-devicetree**: DMA devicetree binding creation
- **linux-debugging**: ftrace and dynamic debug for DMA tracing

## Kernel Documentation

- Provider API: https://docs.kernel.org/driver-api/dmaengine/provider.html
- Client API: https://docs.kernel.org/driver-api/dmaengine/client.html
- DMA API Guide: https://docs.kernel.org/core-api/dma-api.html
- DMA Coherent Memory: https://docs.kernel.org/core-api/dma-api-howto.html
