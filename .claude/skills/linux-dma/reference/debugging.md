# DMA Debugging Guide

Comprehensive guide to debugging DMA issues in Linux kernel drivers.

## Enable DMA Debug Messages

### Dynamic Debug

```bash
# Enable DMAengine core debug
echo 'file dmaengine.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable virtual DMA helper debug
echo 'file virt-dma.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable specific DMA controller debug
echo 'file dma-axi-dmac.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable all DMA subsystem debug
echo 'file drivers/dma/* +p' > /sys/kernel/debug/dynamic_debug/control

# Check messages
dmesg | grep -i dma
dmesg -w  # Watch live
```

### Kernel Config Options

```kconfig
CONFIG_DMADEVICES=y           # DMA engine support
CONFIG_DEBUG_DMA_API=y        # DMA-API debugging
CONFIG_DMA_API_DEBUG=y        # DMA-API debug hash
CONFIG_DMA_ENGINE_RAID=y      # DMA engine RAID support
CONFIG_ASYNC_TX_DMA=y         # Async TX DMA support
CONFIG_DYNAMIC_DEBUG=y        # Dynamic debug support
```

### Driver Debug Prints

Add debug prints in your DMA code:

```c
#define DEBUG 1  // At top of file

dev_dbg(dev, "DMA transfer started: addr=0x%llx len=%zu\n", addr, len);
dev_dbg(dev, "DMA callback fired\n");
dev_dbg(dev, "DMA residue: %u bytes\n", state.residue);

// Or use pr_debug for non-device code
pr_debug("DMA descriptor prepared\n");
```

## DMA Channel Information

### Sysfs Interface

```bash
# List all DMA devices and channels
ls /sys/class/dma/
# Output: dma0chan0 dma0chan1 dma0chan2 ...

# Check channel details
cat /sys/class/dma/dma0chan0/uevent
# DEVNAME=dma0chan0
# MODALIAS=dma:dma0chan0

# Check channel capabilities
cat /sys/class/dma/dma0chan0/cap_mask
```

### Debugfs Interface

```bash
# DMA-API debug info (if CONFIG_DMA_API_DEBUG=y)
cat /sys/kernel/debug/dma-api/dump
cat /sys/kernel/debug/dma-api/error_count
cat /sys/kernel/debug/dma-api/num_errors

# Check for DMA mapping leaks
cat /sys/kernel/debug/dma-api/dump | grep -i "leaked"
```

## Common DMA Issues

### 1. DMA Mapping Failures

**Symptoms**: Transfer doesn't start, timeout errors, or ENOMEM

**Causes**:
- Buffer not in DMA-capable memory
- IOMMU configuration issues
- DMA mask too restrictive

**Debug**:
```c
// Always check mapping errors
dma_addr_t addr = dma_map_single(dev, buffer, len, DMA_TO_DEVICE);
if (dma_mapping_error(dev, addr)) {
	dev_err(dev, "DMA mapping failed\n");
	dev_err(dev, "Buffer: %p, len: %zu\n", buffer, len);
	dev_err(dev, "DMA mask: 0x%llx\n", *dev->dma_mask);
	return -ENOMEM;
}
```

**Solutions**:
```c
// Set appropriate DMA mask
ret = dma_set_mask_and_coherent(dev, DMA_BIT_MASK(32));
if (ret) {
	dev_err(dev, "Failed to set DMA mask\n");
	return ret;
}

// Use coherent allocation for problematic buffers
buf = dma_alloc_coherent(dev, size, &dma_addr, GFP_KERNEL);
```

### 2. Transfer Timeout

**Symptoms**: wait_for_completion_timeout() returns 0

**Causes**:
- Interrupt not firing
- Callback not set
- DMA not started
- Hardware FIFO full/empty

**Debug**:
```bash
# Check if interrupt is registered
cat /proc/interrupts | grep -i dma

# Check interrupt count (should increment during transfer)
before=$(cat /proc/interrupts | grep dmac | awk '{print $2}')
# ... run transfer ...
after=$(cat /proc/interrupts | grep dmac | awk '{print $2}')
echo "Interrupts: $((after - before))"
```

**Debug in driver**:
```c
static int my_submit_dma(struct my_device *mydev, ...)
{
	// ... prepare descriptor ...

	dev_dbg(mydev->dev, "Submitting DMA: addr=0x%llx len=%zu\n", addr, len);

	// Ensure callback is set
	desc->callback = my_dma_callback;
	desc->callback_param = mydev;

	cookie = dmaengine_submit(desc);
	dev_dbg(mydev->dev, "DMA cookie: %d\n", cookie);

	// Start transfer
	dma_async_issue_pending(chan);
	dev_dbg(mydev->dev, "DMA issued\n");

	// Wait with debug
	ret = wait_for_completion_timeout(&mydev->dma_complete,
	                                   msecs_to_jiffies(5000));
	if (ret == 0) {
		dev_err(mydev->dev, "DMA timeout!\n");
		dev_err(mydev->dev, "Checking status...\n");

		status = dmaengine_tx_status(chan, cookie, &state);
		dev_err(mydev->dev, "Status: %d, residue: %u\n",
		        status, state.residue);

		// Check hardware status registers
		dev_err(mydev->dev, "HW status: 0x%08x\n",
		        readl(dmac->base + STATUS_REG));
	}
}

static void my_dma_callback(void *data)
{
	struct my_device *mydev = data;

	dev_dbg(mydev->dev, "DMA callback fired\n");
	complete(&mydev->dma_complete);
}
```

### 3. Incorrect Residue Calculation

**Symptoms**: Wrong remaining byte count, transfer appears incomplete

**Causes**:
- Controller doesn't support accurate residue
- Provider driver bug in tx_status callback

**Debug**:
```c
struct dma_tx_state state;
enum dma_status status;

status = dmaengine_tx_status(chan, cookie, &state);
dev_info(dev, "Status: %d\n", status);
dev_info(dev, "Residue: %u bytes\n", state.residue);
dev_info(dev, "Residue granularity: %d\n",
         chan->device->residue_granularity);

// Check controller's residue granularity
switch (chan->device->residue_granularity) {
case DMA_RESIDUE_GRANULARITY_DESCRIPTOR:
	dev_info(dev, "Descriptor-level residue only\n");
	break;
case DMA_RESIDUE_GRANULARITY_SEGMENT:
	dev_info(dev, "Segment-level residue\n");
	break;
case DMA_RESIDUE_GRANULARITY_BURST:
	dev_info(dev, "Burst-level residue (accurate)\n");
	break;
}
```

### 4. Memory Corruption

**Symptoms**: Data corruption, crashes, random behavior

**Causes**:
- Cache coherency issues
- Buffer freed before DMA completes
- Missing dma_unmap
- Wrong DMA direction

**Debug**:
```bash
# Enable DMA-API debugging
echo 1 > /sys/kernel/debug/dma-api/disabled
cat /sys/kernel/debug/dma-api/error_count

# Check for common errors in dmesg:
# - DMA-API: device driver tries to free DMA memory it has not allocated
# - DMA-API: device driver frees DMA memory with different size
# - DMA-API: device driver frees DMA memory with wrong function
```

**Solutions**:
```c
// CORRECT: Unmap after DMA completes
dma_addr = dma_map_single(dev, buf, len, DMA_FROM_DEVICE);
// ... submit and wait for DMA ...
dmaengine_terminate_sync(chan);  // Ensure DMA stopped
dma_unmap_single(dev, dma_addr, len, DMA_FROM_DEVICE);

// WRONG: Unmap before DMA completes
dma_unmap_single(dev, dma_addr, len, DMA_FROM_DEVICE);
// DMA still running - corruption!

// CORRECT: Match direction
dma_addr = dma_map_single(dev, buf, len, DMA_FROM_DEVICE);
// ...
dma_unmap_single(dev, dma_addr, len, DMA_FROM_DEVICE);  // Same direction

// WRONG: Mismatched direction
dma_addr = dma_map_single(dev, buf, len, DMA_FROM_DEVICE);
// ...
dma_unmap_single(dev, dma_addr, len, DMA_TO_DEVICE);  // Wrong direction!
```

### 5. Callbacks Not Firing

**Symptoms**: Completion never signaled, timeout

**Causes**:
- DMA_PREP_INTERRUPT flag not set
- Interrupt handler not calling vchan_cookie_complete()
- Hardware interrupt not enabled

**Debug**:
```c
// Provider driver interrupt handler
static irqreturn_t my_dma_irq(int irq, void *devid)
{
	struct my_dma_controller *dmac = devid;
	unsigned int status;

	status = readl(dmac->base + STATUS_REG);

	dev_dbg(dmac->dev, "DMA IRQ: status=0x%08x\n", status);

	if (!(status & IRQ_PENDING)) {
		dev_dbg(dmac->dev, "Spurious interrupt\n");
		return IRQ_NONE;
	}

	// Clear interrupt
	writel(status, dmac->base + STATUS_REG);

	// Process completion
	spin_lock(&chan->vchan.lock);

	if (chan->current_desc) {
		dev_dbg(dmac->dev, "Completing descriptor\n");
		vchan_cookie_complete(&chan->current_desc->vdesc);
		chan->current_desc = NULL;
	} else {
		dev_warn(dmac->dev, "IRQ but no active descriptor!\n");
	}

	spin_unlock(&chan->vchan.lock);

	return IRQ_HANDLED;
}
```

### 6. Scatter-Gather Issues

**Symptoms**: Only first segment transfers, corruption

**Causes**:
- Using nents instead of mapped_nents
- Not checking sg_dma_len()
- Controller doesn't support SG

**Debug**:
```c
static int my_sg_transfer(struct my_device *mydev, struct scatterlist *sgl,
                          unsigned int nents)
{
	int mapped_nents;
	struct scatterlist *sg;
	int i;

	dev_dbg(mydev->dev, "SG transfer: %u entries\n", nents);

	// Map SG list
	mapped_nents = dma_map_sg(mydev->dev, sgl, nents, DMA_FROM_DEVICE);
	if (mapped_nents == 0) {
		dev_err(mydev->dev, "SG mapping failed\n");
		return -ENOMEM;
	}

	dev_dbg(mydev->dev, "SG mapped: %u -> %u entries\n",
	        nents, mapped_nents);

	// Debug mapped entries
	for_each_sg(sgl, sg, mapped_nents, i) {
		dev_dbg(mydev->dev, "  [%d] addr=0x%llx len=%u\n",
		        i, (u64)sg_dma_address(sg), sg_dma_len(sg));
	}

	// IMPORTANT: Use mapped_nents, not nents!
	desc = dmaengine_prep_slave_sg(mydev->rx_chan, sgl, mapped_nents,
	                               DMA_DEV_TO_MEM,
	                               DMA_PREP_INTERRUPT | DMA_CTRL_ACK);

	// ... rest of transfer ...

	// Unmap with original nents
	dma_unmap_sg(mydev->dev, sgl, nents, DMA_FROM_DEVICE);

	return 0;
}
```

## Performance Debugging

### Measure Transfer Throughput

```c
static void my_measure_throughput(struct my_device *mydev)
{
	ktime_t start, end;
	s64 elapsed_ns;
	size_t bytes_transferred = 1024 * 1024;  // 1MB
	unsigned long throughput_mbps;

	start = ktime_get();

	// Perform DMA transfer
	my_submit_dma(mydev, ...);

	end = ktime_get();
	elapsed_ns = ktime_to_ns(ktime_sub(end, start));

	// Calculate throughput in MB/s
	throughput_mbps = (bytes_transferred * 1000000000ULL) /
	                  (elapsed_ns * 1024 * 1024);

	dev_info(mydev->dev, "Transfer: %zu bytes in %lld ns (%lu MB/s)\n",
	         bytes_transferred, elapsed_ns, throughput_mbps);
}
```

### Check DMA Idle Time

```c
// In provider driver
static void my_start_transfer(struct my_dma_chan *chan)
{
	ktime_t now = ktime_get();

	if (chan->last_completion) {
		s64 idle_us = ktime_us_delta(now, chan->last_completion);
		dev_dbg(chan->dev, "Channel idle: %lld us\n", idle_us);
	}

	// ... program hardware ...

	chan->transfer_start = now;
}

static void my_complete_transfer(struct my_dma_chan *chan)
{
	ktime_t now = ktime_get();
	s64 duration_us = ktime_us_delta(now, chan->transfer_start);

	dev_dbg(chan->dev, "Transfer duration: %lld us\n", duration_us);

	chan->last_completion = now;
}
```

## Ftrace for DMA Tracing

### Trace DMA Operations

```bash
# Enable DMA tracepoints
echo 1 > /sys/kernel/debug/tracing/events/dma/enable

# Start tracing
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Run your DMA operation
# ...

# Stop tracing
echo 0 > /sys/kernel/debug/tracing/tracing_on

# View trace
cat /sys/kernel/debug/tracing/trace

# Example output:
#   mydriver-123 [000] .... 12345.678901: dma_map_single: device=dma addr=0x12345000 size=4096
#   mydriver-123 [000] .... 12345.678902: dma_issue_pending: chan=dma0chan0
#   kworker/0:1-456 [000] d.h. 12345.679123: dma_complete: chan=dma0chan0 cookie=1
```

### Custom DMA Trace Events

Add to your driver:

```c
#include <trace/events/dma.h>

TRACE_EVENT(my_dma_submit,
	TP_PROTO(struct dma_chan *chan, dma_addr_t addr, size_t len),
	TP_ARGS(chan, addr, len),
	TP_STRUCT__entry(
		__field(dma_addr_t, addr)
		__field(size_t, len)
		__string(chan_name, dev_name(&chan->dev->device))
	),
	TP_fast_assign(
		__entry->addr = addr;
		__entry->len = len;
		__assign_str(chan_name);
	),
	TP_printk("chan=%s addr=0x%llx len=%zu",
	          __get_str(chan_name), __entry->addr, __entry->len)
);

// Use in code:
trace_my_dma_submit(chan, addr, len);
```

## Hardware Register Dumps

### Add Register Dump Function

```c
static void my_dma_dump_regs(struct my_dma_controller *dmac)
{
	dev_info(dmac->dev, "DMA Register Dump:\n");
	dev_info(dmac->dev, "  CTRL:   0x%08x\n", readl(dmac->base + CTRL_REG));
	dev_info(dmac->dev, "  STATUS: 0x%08x\n", readl(dmac->base + STATUS_REG));
	dev_info(dmac->dev, "  SRC:    0x%08x\n", readl(dmac->base + SRC_ADDR_REG));
	dev_info(dmac->dev, "  DST:    0x%08x\n", readl(dmac->base + DST_ADDR_REG));
	dev_info(dmac->dev, "  LEN:    0x%08x\n", readl(dmac->base + LEN_REG));
	dev_info(dmac->dev, "  IRQ_EN: 0x%08x\n", readl(dmac->base + IRQ_EN_REG));
}

// Call on timeout:
if (!wait_for_completion_timeout(...)) {
	dev_err(dev, "DMA timeout\n");
	my_dma_dump_regs(dmac);
	dmaengine_terminate_sync(chan);
}
```

## Checklist for DMA Debugging

Consumer driver issues:
- [ ] DMA channel requested successfully (check dmas property in DT)
- [ ] Channel configured with dmaengine_slave_config()
- [ ] Buffers mapped before dmaengine_prep_* (check dma_mapping_error)
- [ ] DMA_PREP_INTERRUPT flag set in prep call
- [ ] Callback and callback_param set on descriptor
- [ ] dma_async_issue_pending() called after submit
- [ ] Unmap only after transfer completes
- [ ] terminate_sync() called before freeing resources

Provider driver issues:
- [ ] Interrupt registered in probe
- [ ] Interrupt handler clears hardware status
- [ ] vchan_cookie_complete() called on completion
- [ ] vchan_cyclic_callback() called for cyclic mode
- [ ] Hardware started in device_issue_pending
- [ ] device_tx_status returns accurate residue
- [ ] device_terminate_all stops hardware
- [ ] device_synchronize waits for callbacks

## Kernel Documentation

- DMAengine API: https://docs.kernel.org/driver-api/dmaengine/
- DMA-API: https://docs.kernel.org/core-api/dma-api.html
- Dynamic Debug: https://docs.kernel.org/admin-guide/dynamic-debug-howto.html
- Ftrace: https://docs.kernel.org/trace/ftrace.html
