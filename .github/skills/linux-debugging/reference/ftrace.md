# Ftrace - Function and Event Tracing

Ftrace is the kernel's internal tracing infrastructure for debugging and performance analysis.

## Function Tracer

Records every kernel function call (uses dynamic ftrace with minimal overhead):

```bash
cd /sys/kernel/tracing  # or /sys/kernel/debug/tracing

# Select function tracer
echo function > current_tracer

# Filter specific functions (wildcard supported)
echo 'ad7124_*' > set_ftrace_filter

# Or filter by module
echo ':mod:ad7124' > set_ftrace_filter

# View current filter
cat set_ftrace_filter

# Start tracing
echo 1 > tracing_on

# ... perform operations (load module, trigger hardware) ...

# Stop tracing
echo 0 > tracing_on

# View trace
cat trace | less

# Clear trace buffer
echo > trace

# Disable tracer
echo nop > current_tracer
```

**Trace output format**:
```
# tracer: function
#
# TASK-PID   CPU#  TIMESTAMP  FUNCTION
# |    |      |       |         |
  bash-1234  [001] 12345.678901: ad7124_probe <-platform_drv_probe
  bash-1234  [001] 12345.678923: ad7124_init_regs <-ad7124_probe
```

## Function Graph Tracer

Shows function call hierarchy with entry/exit and duration:

```bash
echo function_graph > current_tracer

# Filter which functions to graph
echo ad7124_read_raw > set_graph_function

echo 1 > tracing_on
# ... trigger read operation ...
echo 0 > tracing_on

cat trace
```

**Output shows call graph**:
```
 1)               |  ad7124_read_raw() {
 1)               |    ad7124_set_channel() {
 1)   1.234 us    |      ad7124_spi_write();
 1)   5.678 us    |    }
 1)               |    ad7124_wait_for_conv() {
 1) + 12.345 us   |      msleep();
 1) + 15.234 us   |    }
 1)   0.456 us    |    ad7124_spi_read();
 1) + 25.678 us   |  }
```

## Event Tracing

Trace specific kernel events (interrupts, scheduling, I/O):

```bash
# List available events
cat available_events | grep iio

# Enable IIO events
echo 1 > events/iio/enable

# Or enable specific event
echo 1 > events/iio/iio_trigger_poll/enable

# View trace_pipe for live output
cat trace_pipe
```

## Tracepoints in Driver Code

Add custom tracepoints to your driver:

```c
#include <trace/events/iio.h>  // If using existing IIO tracepoints

// Or define custom tracepoints
#define CREATE_TRACE_POINTS
#include "ad7124_trace.h"

// In driver function
trace_ad7124_conversion_complete(val, channel);
```

## Common Debugging Patterns

### Verify Device Probe

```c
static int my_probe(struct spi_device *spi)
{
	dev_info(&spi->dev, "Probe started\n");

	// Check hardware ID
	ret = my_read_id(spi, &id);
	dev_info(&spi->dev, "Device ID: 0x%04x (expected 0x%04x)\n", id, EXPECTED_ID);

	if (id != EXPECTED_ID) {
		dev_err(&spi->dev, "ID mismatch - check wiring\n");
		return -ENODEV;
	}

	dev_info(&spi->dev, "Probe successful\n");
	return 0;
}
```

### Trace Register Access

```c
static int my_write_reg(struct device *dev, u8 reg, u32 val)
{
	dev_dbg(dev, "Write reg=0x%02x val=0x%08x\n", reg, val);
	return spi_write(...);
}

static int my_read_reg(struct device *dev, u8 reg, u32 *val)
{
	int ret = spi_read(...);
	dev_dbg(dev, "Read reg=0x%02x val=0x%08x\n", reg, *val);
	return ret;
}
```

### Check DMA Mapping Errors

```c
dma_addr_t dma_handle;

dma_handle = dma_map_single(dev, buffer, size, DMA_TO_DEVICE);
if (dma_mapping_error(dev, dma_handle)) {
	dev_err(dev, "DMA mapping failed - check IOMMU/SWIOTLB\n");
	return -ENOMEM;
}

// ... use DMA ...

dma_unmap_single(dev, dma_handle, size, DMA_TO_DEVICE);
```

### Verify Interrupt Handling

```c
static irqreturn_t my_irq_handler(int irq, void *dev_id)
{
	struct my_device *dev = dev_id;

	dev_dbg(&dev->spi->dev, "IRQ triggered\n");

	u32 status = read_status_reg(dev);
	dev_dbg(&dev->spi->dev, "Status: 0x%08x\n", status);

	if (status & ERROR_MASK)
		dev_err(&dev->spi->dev, "Hardware error: 0x%08x\n", status);

	return IRQ_HANDLED;
}
```
