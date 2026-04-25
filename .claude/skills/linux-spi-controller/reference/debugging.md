# SPI Controller Debugging

Comprehensive debugging guide for SPI controller drivers, covering dynamic debug, sysfs inspection, and common issues.

## Enable SPI Core Debug

### Dynamic Debug

```bash
# Enable debug for SPI core
echo "file drivers/spi/spi.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable debug for specific controller
echo "file drivers/spi/spi-axi-spi-engine.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable all SPI debug
echo "file drivers/spi/* +p" > /sys/kernel/debug/dynamic_debug/control

# View messages
dmesg -w
```

### Kernel Config Options

```kconfig
CONFIG_DYNAMIC_DEBUG=y
CONFIG_DEBUG_FS=y
CONFIG_SPI_DEBUG=y
```

## SysFS Inspection

### List SPI Buses and Devices

```bash
# List SPI buses
ls /sys/bus/spi/devices/
# spi0.0  spi0.1  spi1.0

# View controller info
cat /sys/class/spi_master/spi0/uevent
# DEVTYPE=spi_master
# MODALIAS=platform:my-spi

# Check statistics
cat /sys/class/spi_master/spi0/statistics/*
```

### SPI Device Information

```bash
# View SPI device properties
cat /sys/bus/spi/devices/spi0.0/modalias
# spi:ad7124

cat /sys/bus/spi/devices/spi0.0/statistics/bytes
# 1024

cat /sys/bus/spi/devices/spi0.0/statistics/messages
# 32
```

## Common Issues

### Issue 1: Transfers Timeout

**Symptom**:
```
spi spi0.0: SPI transfer timed out
```

**Causes**:
1. Controller interrupt not firing
2. `spi_finalize_current_message()` or `spi_finalize_current_transfer()` not called
3. Hardware FIFO stalling
4. Clock not running

**Debug Steps**:

```bash
# Check if interrupt is registered
cat /proc/interrupts | grep spi

# Enable SPI debug
echo "file drivers/spi/spi.c +p" > /sys/kernel/debug/dynamic_debug/control

# Check controller registers
cat /sys/kernel/debug/regmap/spi@40000000/registers
```

**Fix**:

```c
/* Ensure finalize is called in ALL code paths */
static int my_spi_transfer_one_message(struct spi_controller *host,
				       struct spi_message *msg)
{
	int ret;

	ret = my_spi_do_transfer(host, msg);

	msg->status = ret;
	spi_finalize_current_message(host);  // MUST call this!

	return ret;
}

/* For interrupt-driven transfers */
static irqreturn_t my_spi_irq(int irq, void *dev_id)
{
	struct my_spi_controller *ctlr = dev_id;

	/* Clear interrupt */
	/* ... */

	/* Finalize transfer */
	spi_finalize_current_transfer(ctlr->host);

	return IRQ_HANDLED;
}
```

### Issue 2: Data Corruption

**Symptom**:
- Wrong data received
- Some bits always 0 or 1
- Data shifted by N bits

**Causes**:
1. Clock polarity/phase mismatch (CPOL/CPHA)
2. Incorrect bit order (MSB vs LSB first)
3. Chip select timing issues
4. DMA alignment problems

**Debug Steps**:

```bash
# Check SPI mode
cat /sys/bus/spi/devices/spi0.0/driver/module/parameters/spi_mode

# Enable verbose logging
echo 8 > /proc/sys/kernel/printk
```

**Fix**:

```c
/* Verify SPI mode configuration */
static int my_spi_setup(struct spi_device *spi)
{
	u32 config = 0;

	/* Ensure CPOL and CPHA match device requirements */
	if (spi->mode & SPI_CPOL)
		config |= MY_SPI_CPOL;  // Clock idle high
	if (spi->mode & SPI_CPHA)
		config |= MY_SPI_CPHA;  // Sample on trailing edge

	/* Check bit order */
	if (spi->mode & SPI_LSB_FIRST)
		config |= MY_SPI_LSB_FIRST;

	dev_dbg(&spi->dev, "SPI mode: CPOL=%d CPHA=%d LSB_FIRST=%d\n",
		!!(spi->mode & SPI_CPOL),
		!!(spi->mode & SPI_CPHA),
		!!(spi->mode & SPI_LSB_FIRST));

	writel(config, ctlr->base + MY_SPI_CONFIG);
	return 0;
}
```

### Issue 3: Performance Issues

**Symptom**:
- Slow transfer rates
- High CPU usage
- Frequent interrupts

**Causes**:
1. Not using DMA for large transfers
2. Small FIFO sizes
3. Inefficient clock divider
4. CPU frequency scaling interfering

**Debug Steps**:

```bash
# Check transfer statistics
cat /sys/class/spi_master/spi0/statistics/bytes_tx
cat /sys/class/spi_master/spi0/statistics/bytes_rx
cat /sys/class/spi_master/spi0/statistics/messages

# Monitor CPU usage
top -d 1

# Check interrupt rate
watch -n 1 'cat /proc/interrupts | grep spi'
```

**Fix**:

```c
/* Use DMA for large transfers */
#define DMA_MIN_BYTES	64

static int my_spi_transfer_one(struct spi_controller *host,
			       struct spi_device *spi,
			       struct spi_transfer *xfer)
{
	/* Use DMA for transfers >= 64 bytes */
	if (xfer->len >= DMA_MIN_BYTES && host->dma_tx && host->dma_rx)
		return my_spi_transfer_one_dma(host, spi, xfer);

	/* Use PIO for small transfers */
	return my_spi_transfer_one_pio(host, spi, xfer);
}
```

### Issue 4: Device Not Detected

**Symptom**:
```
spi spi0: Failed to create SPI device for /soc/spi@40000000/adc@0
```

**Causes**:
1. Devicetree errors
2. Missing `#address-cells` or `#size-cells`
3. Incompatible driver
4. Probe failures

**Debug Steps**:

```bash
# Check devicetree
ls /sys/firmware/devicetree/base/soc/spi@*/

# Validate devicetree
make dtbs_check

# Check driver binding
cat /sys/bus/spi/drivers/*/uevent
```

**Fix**:

Ensure devicetree has proper structure:

```dts
spi0: spi@40000000 {
	compatible = "vendor,my-spi";
	reg = <0x40000000 0x1000>;
	#address-cells = <1>;  // REQUIRED
	#size-cells = <0>;     // REQUIRED

	adc@0 {
		compatible = "adi,ad7124";
		reg = <0>;  // Chip select number
		spi-max-frequency = <5000000>;
	};
};
```

### Issue 5: DMA Errors

**Symptom**:
```
dmaengine: descriptor preparation failed
spi spi0.0: Failed to prepare DMA
```

**Causes**:
1. Buffer not DMA-safe (on stack)
2. Alignment issues
3. DMA channel busy
4. Invalid DMA configuration

**Debug Steps**:

```bash
# Check DMA channels
cat /sys/kernel/debug/dmaengine/summary

# Enable DMA debug
echo "file drivers/dma/* +p" > /sys/kernel/debug/dynamic_debug/control
```

**Fix**:

```c
/* Validate DMA buffers */
static int my_spi_transfer_one_dma(struct spi_controller *host,
				   struct spi_device *spi,
				   struct spi_transfer *xfer)
{
	/* Check buffer alignment */
	if (host->dma_alignment) {
		if ((uintptr_t)xfer->tx_buf & (host->dma_alignment - 1)) {
			dev_warn(&spi->dev, "TX buffer not aligned\n");
			return -EINVAL;
		}
		if ((uintptr_t)xfer->rx_buf & (host->dma_alignment - 1)) {
			dev_warn(&spi->dev, "RX buffer not aligned\n");
			return -EINVAL;
		}
	}

	/* Fallback to PIO if DMA fails */
	/* ... */
}
```

## Debugging Tools

### ftrace

Trace SPI function calls:

```bash
# Enable function tracing for SPI
echo 'spi_*' > /sys/kernel/debug/tracing/set_ftrace_filter
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Perform SPI operation
# ...

# View trace
cat /sys/kernel/debug/tracing/trace

# Disable tracing
echo 0 > /sys/kernel/debug/tracing/tracing_on
```

### Logic Analyzer

Use logic analyzer to capture SPI signals:

- **SCLK**: SPI clock
- **MOSI**: Master Out, Slave In
- **MISO**: Master In, Slave Out
- **CS**: Chip Select

Verify:
- Clock polarity (CPOL)
- Clock phase (CPHA)
- Bit order (MSB/LSB first)
- Chip select timing
- Data integrity

### Register Dumps

Add debug prints for register dumps:

```c
static void my_spi_dump_regs(struct my_spi_controller *ctlr)
{
	dev_dbg(ctlr->dev, "CR:   0x%08x\n", readl(ctlr->base + MY_SPI_CR));
	dev_dbg(ctlr->dev, "SR:   0x%08x\n", readl(ctlr->base + MY_SPI_SR));
	dev_dbg(ctlr->dev, "CCR:  0x%08x\n", readl(ctlr->base + MY_SPI_CCR));
	dev_dbg(ctlr->dev, "IER:  0x%08x\n", readl(ctlr->base + MY_SPI_IER));
}
```

## Kernel Debugging Techniques

### printk/dev_dbg

```c
/* Use dev_dbg for verbose logging (disabled by default) */
dev_dbg(&spi->dev, "Transfer: len=%u, speed=%u, mode=0x%x\n",
	xfer->len, xfer->speed_hz, spi->mode);

/* Use dev_info for important events */
dev_info(&spi->dev, "SPI controller initialized\n");

/* Use dev_err for errors */
dev_err(&spi->dev, "Transfer failed: %d\n", ret);
```

### WARN_ON / BUG_ON

```c
/* Use WARN_ON for unexpected conditions */
if (WARN_ON(!xfer->tx_buf && !xfer->rx_buf))
	return -EINVAL;

/* Use BUG_ON for critical errors (use sparingly) */
BUG_ON(!host);
```

## Common Checklist

When debugging SPI controller issues:

- [ ] Controller probe successful? Check `dmesg | grep spi`
- [ ] Interrupts registered? Check `/proc/interrupts`
- [ ] Clock enabled? Check clock subsystem
- [ ] DMA channels allocated? Check `/sys/kernel/debug/dmaengine/summary`
- [ ] `spi_finalize_current_message()` called in all paths?
- [ ] SPI mode configured correctly (CPOL/CPHA)?
- [ ] Chip select working? Check GPIO state
- [ ] Transfer size within limits?
- [ ] Devicetree correct? Validate with `make dtbs_check`
- [ ] Bus number conflicts? Check `/sys/class/spi_master/`

## References

- `Documentation/spi/spi-summary.rst` - SPI subsystem overview
- `Documentation/driver-api/spi.rst` - SPI driver API
- `drivers/spi/spi.c` - SPI core implementation
- `/sys/kernel/debug/dynamic_debug/control` - Dynamic debug interface
