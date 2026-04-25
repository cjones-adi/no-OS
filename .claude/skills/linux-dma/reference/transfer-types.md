# DMA Transfer Types

Guide to different DMA transfer types supported by the DMAengine framework.

## Overview

DMAengine supports several transfer types:
- **Slave single/SG**: One-shot transfers between memory and peripherals
- **Cyclic**: Continuous looping transfers for audio/streaming
- **Memcpy**: Memory-to-memory copies
- **Interleaved**: 2D/strided transfers

## Slave Single Transfer

Simplest form: single contiguous buffer transfer.

```c
struct dma_async_tx_descriptor *dmaengine_prep_slave_single(
	struct dma_chan *chan,
	dma_addr_t buf,           // DMA address (must be mapped)
	size_t len,               // Transfer length in bytes
	enum dma_transfer_direction dir,
	unsigned long flags);

// Direction options:
// DMA_MEM_TO_DEV  - Memory to peripheral (TX)
// DMA_DEV_TO_MEM  - Peripheral to memory (RX)
// DMA_MEM_TO_MEM  - Memory to memory (memcpy)
// DMA_DEV_TO_DEV  - Peripheral to peripheral
```

### Example: Simple RX Transfer

```c
static int my_rx_single(struct my_device *mydev, void *buffer, size_t len)
{
	struct dma_async_tx_descriptor *desc;
	dma_addr_t dma_addr;
	dma_cookie_t cookie;

	// Map buffer
	dma_addr = dma_map_single(mydev->dev, buffer, len, DMA_FROM_DEVICE);
	if (dma_mapping_error(mydev->dev, dma_addr))
		return -ENOMEM;

	// Prepare descriptor
	desc = dmaengine_prep_slave_single(mydev->rx_chan, dma_addr, len,
	                                   DMA_DEV_TO_MEM,
	                                   DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
	if (!desc) {
		dma_unmap_single(mydev->dev, dma_addr, len, DMA_FROM_DEVICE);
		return -ENOMEM;
	}

	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	cookie = dmaengine_submit(desc);
	dma_async_issue_pending(mydev->rx_chan);

	// Wait for completion...
	// Unmap buffer after completion
	dma_unmap_single(mydev->dev, dma_addr, len, DMA_FROM_DEVICE);

	return 0;
}
```

## Scatter-Gather Transfer

Transfer multiple non-contiguous buffers in a single DMA operation.

```c
struct dma_async_tx_descriptor *dmaengine_prep_slave_sg(
	struct dma_chan *chan,
	struct scatterlist *sgl,  // Scatter-gather list (must be mapped)
	unsigned int sg_len,      // Number of entries (use mapped count!)
	enum dma_transfer_direction dir,
	unsigned long flags);
```

### Example: Multi-Buffer RX

```c
static int my_rx_sg(struct my_device *mydev, struct scatterlist *sgl,
                    unsigned int nents)
{
	struct dma_async_tx_descriptor *desc;
	int mapped_nents;
	dma_cookie_t cookie;

	// Map scatter-gather list
	mapped_nents = dma_map_sg(mydev->dev, sgl, nents, DMA_FROM_DEVICE);
	if (mapped_nents == 0)
		return -ENOMEM;

	// Prepare SG descriptor (use mapped_nents, NOT nents!)
	desc = dmaengine_prep_slave_sg(mydev->rx_chan, sgl, mapped_nents,
	                               DMA_DEV_TO_MEM,
	                               DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
	if (!desc) {
		dma_unmap_sg(mydev->dev, sgl, nents, DMA_FROM_DEVICE);
		return -ENOMEM;
	}

	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	cookie = dmaengine_submit(desc);
	dma_async_issue_pending(mydev->rx_chan);

	// Wait for completion...
	// Unmap after completion (use original nents for unmap!)
	dma_unmap_sg(mydev->dev, sgl, nents, DMA_FROM_DEVICE);

	return 0;
}
```

### Building Scatter-Gather Lists

```c
#include <linux/scatterlist.h>

static int my_build_sg_list(struct my_device *mydev, void **buffers,
                             size_t *lengths, unsigned int count)
{
	struct scatterlist *sgl;
	unsigned int i;

	// Allocate SG table
	sgl = kmalloc_array(count, sizeof(*sgl), GFP_KERNEL);
	if (!sgl)
		return -ENOMEM;

	sg_init_table(sgl, count);

	// Fill SG entries
	for (i = 0; i < count; i++) {
		sg_set_buf(&sgl[i], buffers[i], lengths[i]);
	}

	// Now map and use the SG list
	// ...

	kfree(sgl);
	return 0;
}
```

## Cyclic Transfers

Continuous looping transfers for streaming applications (audio, ADC/DAC).

```c
struct dma_async_tx_descriptor *dmaengine_prep_dma_cyclic(
	struct dma_chan *chan,
	dma_addr_t buf_addr,      // Ring buffer address
	size_t buf_len,           // Total buffer length
	size_t period_len,        // Period size (callback interval)
	enum dma_transfer_direction dir,
	unsigned long flags);
```

**Key characteristics**:
- Continuously loops the buffer until explicitly stopped
- Callback fires every period (NOT at buffer completion)
- Common for audio (ALSA), IIO streaming, video capture

### Example: Audio Playback

```c
static int my_audio_start(struct my_device *mydev, dma_addr_t buf_addr,
                          size_t buf_len, size_t period_len)
{
	struct dma_async_tx_descriptor *desc;
	dma_cookie_t cookie;

	// buf_len must be multiple of period_len
	if (buf_len % period_len) {
		dev_err(mydev->dev, "Buffer length must be multiple of period\n");
		return -EINVAL;
	}

	// Prepare cyclic descriptor
	desc = dmaengine_prep_dma_cyclic(mydev->tx_chan, buf_addr, buf_len,
	                                 period_len, DMA_MEM_TO_DEV,
	                                 DMA_PREP_INTERRUPT);
	if (!desc) {
		dev_err(mydev->dev, "Failed to prepare cyclic descriptor\n");
		return -ENOMEM;
	}

	// Callback will fire every period
	desc->callback = my_period_callback;
	desc->callback_param = mydev;

	cookie = dmaengine_submit(desc);
	if (dma_submit_error(cookie))
		return -EIO;

	dma_async_issue_pending(mydev->tx_chan);

	return 0;
}

static void my_period_callback(void *data)
{
	struct my_device *mydev = data;

	// Called every period_len bytes
	// Update buffer pointers, process data, etc.
	// Transfer continues automatically
}

static int my_audio_stop(struct my_device *mydev)
{
	// Stop cyclic transfer
	dmaengine_terminate_sync(mydev->tx_chan);
	return 0;
}
```

## Memory-to-Memory Transfer

DMA-accelerated memory copy (if supported by hardware).

```c
struct dma_async_tx_descriptor *dmaengine_prep_dma_memcpy(
	struct dma_chan *chan,
	dma_addr_t dst,           // Destination address
	dma_addr_t src,           // Source address
	size_t len,               // Transfer length
	unsigned long flags);
```

### Example: DMA Memcpy

```c
static int my_dma_memcpy(struct my_device *mydev, void *dst, void *src,
                         size_t len)
{
	struct dma_async_tx_descriptor *desc;
	dma_addr_t dst_dma, src_dma;
	dma_cookie_t cookie;
	int ret = 0;

	// Map source and destination
	src_dma = dma_map_single(mydev->dev, src, len, DMA_TO_DEVICE);
	if (dma_mapping_error(mydev->dev, src_dma))
		return -ENOMEM;

	dst_dma = dma_map_single(mydev->dev, dst, len, DMA_FROM_DEVICE);
	if (dma_mapping_error(mydev->dev, dst_dma)) {
		dma_unmap_single(mydev->dev, src_dma, len, DMA_TO_DEVICE);
		return -ENOMEM;
	}

	// Prepare memcpy descriptor
	desc = dmaengine_prep_dma_memcpy(mydev->memcpy_chan, dst_dma, src_dma,
	                                 len, DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
	if (!desc) {
		ret = -ENOMEM;
		goto unmap;
	}

	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	cookie = dmaengine_submit(desc);
	if (dma_submit_error(cookie)) {
		ret = -EIO;
		goto unmap;
	}

	dma_async_issue_pending(mydev->memcpy_chan);

	// Wait for completion...

unmap:
	dma_unmap_single(mydev->dev, dst_dma, len, DMA_FROM_DEVICE);
	dma_unmap_single(mydev->dev, src_dma, len, DMA_TO_DEVICE);
	return ret;
}
```

## Interleaved Transfers

2D or strided transfers (e.g., image processing, video frames).

```c
struct dma_interleaved_template {
	dma_addr_t src_start;
	dma_addr_t dst_start;
	enum dma_transfer_direction dir;
	bool src_inc;         // Increment source address
	bool dst_inc;         // Increment destination address
	bool src_sgl;         // Source is scatter-gather
	bool dst_sgl;         // Destination is scatter-gather
	size_t numf;          // Number of frames
	size_t frame_size;    // Size of each frame
	struct data_chunk chunks[0];
};

struct data_chunk {
	size_t size;          // Chunk size in bytes
	size_t icg;           // Inter-chunk gap (bytes to skip)
	size_t dst_icg;       // Destination inter-chunk gap
};

struct dma_async_tx_descriptor *dmaengine_prep_interleaved_dma(
	struct dma_chan *chan,
	struct dma_interleaved_template *xt,
	unsigned long flags);
```

### Example: 2D Image Transfer

```c
static int my_2d_transfer(struct my_device *mydev, dma_addr_t src,
                          dma_addr_t dst, size_t width, size_t height,
                          size_t src_stride, size_t dst_stride)
{
	struct dma_interleaved_template *xt;
	struct dma_async_tx_descriptor *desc;
	dma_cookie_t cookie;

	// Allocate template with 1 chunk per frame
	xt = kzalloc(sizeof(*xt) + sizeof(struct data_chunk), GFP_KERNEL);
	if (!xt)
		return -ENOMEM;

	xt->src_start = src;
	xt->dst_start = dst;
	xt->dir = DMA_MEM_TO_MEM;
	xt->src_inc = true;
	xt->dst_inc = true;
	xt->src_sgl = false;
	xt->dst_sgl = false;
	xt->numf = height;           // Number of rows
	xt->frame_size = 1;          // 1 chunk per row

	xt->chunks[0].size = width;           // Row width in bytes
	xt->chunks[0].icg = src_stride - width;      // Source padding
	xt->chunks[0].dst_icg = dst_stride - width;  // Destination padding

	// Prepare interleaved descriptor
	desc = dmaengine_prep_interleaved_dma(mydev->memcpy_chan, xt,
	                                      DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
	kfree(xt);

	if (!desc)
		return -ENOMEM;

	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	cookie = dmaengine_submit(desc);
	dma_async_issue_pending(mydev->memcpy_chan);

	return 0;
}
```

## Descriptor Flags

Flags passed to prep functions:

```c
// Request interrupt on completion
#define DMA_PREP_INTERRUPT    (1 << 0)

// Acknowledge descriptor (allows controller to free it)
#define DMA_CTRL_ACK          (1 << 1)

// Reuse descriptor (for repeated transfers)
#define DMA_CTRL_REUSE        (1 << 2)

// Peripheral-paced transfer
#define DMA_PREP_FENCE        (1 << 3)

// Continue on error
#define DMA_PREP_CONTINUE_ON_ERROR  (1 << 4)
```

Common combinations:
```c
// Standard one-shot transfer with callback
unsigned long flags = DMA_PREP_INTERRUPT | DMA_CTRL_ACK;

// Cyclic transfer (auto-repeating)
unsigned long flags = DMA_PREP_INTERRUPT;  // Don't ACK (reused)

// Fire-and-forget (no callback)
unsigned long flags = DMA_CTRL_ACK;
```

## Performance Considerations

### Single vs SG vs Cyclic

**Single**: Simplest, good for small transfers
- One descriptor per transfer
- Best for occasional, small data movements

**Scatter-Gather**: Efficient for fragmented data
- One descriptor for multiple buffers
- Reduces CPU intervention
- Better for network packets, file I/O

**Cyclic**: Best for continuous streaming
- One descriptor that loops forever
- Minimal overhead
- Ideal for audio, video, ADC/DAC streaming

### Buffer Size and Alignment

```c
// Good: Large, aligned buffers
#define BUFFER_SIZE    (64 * 1024)    // 64KB
void *buf = kmalloc(BUFFER_SIZE, GFP_KERNEL);

// Bad: Small, unaligned buffers
char small_buf[17];  // Odd size, may not align
```

Best practices:
- Use power-of-2 buffer sizes (4K, 8K, 64K)
- Ensure buffers are cache-line aligned
- For cyclic mode, make buffer size multiple of period
- Match period size to hardware FIFO depth

### Burst Size Tuning

```c
struct dma_slave_config config = {
	.src_maxburst = 4,    // 4 beats per burst
	.dst_maxburst = 4,
};

// Larger bursts = better efficiency (but more latency)
// Smaller bursts = lower latency (but more overhead)
// Match to peripheral FIFO depth for best results
```

## Kernel Documentation

- Client API: https://docs.kernel.org/driver-api/dmaengine/client.html
- Provider API: https://docs.kernel.org/driver-api/dmaengine/provider.html
