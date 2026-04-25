# Kernel Logging and printk

## Log Levels and printk

The kernel provides eight log levels for categorizing messages by severity:

```c
#include <linux/kern_levels.h>
#include <linux/printk.h>

// pr_*() macros (general purpose)
pr_emerg("System is unusable - emergency situation");                 // KERN_EMERG (0)
pr_alert("Action must be taken immediately");                        // KERN_ALERT (1)
pr_crit("Critical conditions - hardware failure");                   // KERN_CRIT (2)
pr_err("Error conditions - operation failed");                       // KERN_ERR (3)
pr_warn("Warning conditions - degraded operation");                  // KERN_WARNING (4)
pr_notice("Normal but significant condition");                       // KERN_NOTICE (5)
pr_info("Informational message");                                    // KERN_INFO (6)
pr_debug("Debug-level message (needs DEBUG or dynamic debug)");      // KERN_DEBUG (7)

// Rate-limited variants (prevent log flooding)
pr_err_ratelimited("Error occurred: %d\n", error_code);
pr_warn_once("This warning only appears once\n");
```

**Viewing kernel messages**:
```bash
# View kernel log buffer
dmesg

# Follow kernel log in real-time
dmesg -w

# Show only errors and warnings
dmesg --level=err,warn

# Human-readable timestamps
dmesg -T
```

## Device-Specific Logging

For device drivers, always use `dev_*()` macros which include device information in the log:

```c
#include <linux/device.h>

static int my_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	int ret;

	dev_info(dev, "Probing device\n");
	// Output: my_device 0000:00:01.0: Probing device

	ret = my_init(dev);
	if (ret) {
		dev_err(dev, "Initialization failed: %d\n", ret);
		return ret;
	}

	dev_dbg(dev, "Register 0x%02x = 0x%02x\n", reg, val);  // Only with DEBUG or dynamic debug
	return 0;
}

// Rate-limited device logging
dev_err_ratelimited(dev, "Frequent error: %d\n", err);
dev_warn_once(dev, "Hardware quirk detected\n");
```

**Log format includes**:
- Driver name
- Bus address (PCI, platform, etc.)
- Message

## Dynamic Debug

Dynamic debug allows enabling/disabling debug messages at runtime without recompiling:

```c
// In driver code - use dev_dbg() or pr_debug()
dev_dbg(&spi->dev, "SPI transfer: %zu bytes at %d Hz\n", len, speed);
```

**Runtime control** (`/sys/kernel/debug/dynamic_debug/control`):

```bash
# Enable all debug messages in a specific file
echo "file drivers/iio/adc/ad7124.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable for specific function
echo "func ad7124_read_raw +p" > /sys/kernel/debug/dynamic_debug/control

# Enable for entire module
echo "module ad7124 +p" > /sys/kernel/debug/dynamic_debug/control

# Enable with line number range
echo "file ad7124.c line 100-200 +p" > /sys/kernel/debug/dynamic_debug/control

# Disable all
echo "file ad7124.c -p" > /sys/kernel/debug/dynamic_debug/control

# Query current settings
grep ad7124 /sys/kernel/debug/dynamic_debug/control
```

**Boot-time dynamic debug**:
```bash
# In kernel command line
dyndbg="file drivers/iio/adc/* +p; module ad7124 +p"
```

**Flags**:
- `+p` - Enable printing
- `+f` - Include function name
- `+l` - Include line number
- `+m` - Include module name
- `+t` - Include thread ID

## print_hex_dump - Buffer Dumping

For dumping binary data (SPI/I2C transfers, DMA buffers):

```c
#include <linux/printk.h>

void my_dump_buffer(struct device *dev, const void *buf, size_t len)
{
	// Output format: offset, hex bytes, ASCII representation
	print_hex_dump(KERN_DEBUG, "SPI RX: ", DUMP_PREFIX_OFFSET,
		       16, 1, buf, len, true);
}

/*
Example output:
SPI RX: 00000000: 01 23 45 67 89 ab cd ef fe dc ba 98 76 54 32 10  .#Eg............
SPI RX: 00000010: aa bb cc dd                                      ....
*/

// Device-specific variant
dev_dbg(dev, "Buffer contents:\n");
print_hex_dump_debug("DMA: ", DUMP_PREFIX_ADDRESS, 16, 1, dma_buf, 64, false);
```

**Parameters**:
- Level: `KERN_DEBUG`, `KERN_INFO`, etc.
- Prefix: String prepended to each line
- Prefix type: `DUMP_PREFIX_OFFSET`, `DUMP_PREFIX_ADDRESS`, `DUMP_PREFIX_NONE`
- `rowsize`: Bytes per row (typically 16 or 32)
- `groupsize`: Bytes per group (1, 2, 4, 8)
- `ascii`: Show ASCII representation

## Debugfs - Custom Debug Interfaces

Debugfs provides a simple filesystem interface for driver debugging.

### Creating Debugfs Entries

**Modern pattern using DEFINE_SHOW_ATTRIBUTE**:

```c
#include <linux/debugfs.h>
#include <linux/seq_file.h>

struct ad7124_state {
	struct spi_device *spi;
	struct dentry *debugfs_root;
	u32 regs[64];
};

/**
 * ad7124_status_show - Show device status
 *
 * Displays register dump and device state for debugging.
 */
static int ad7124_status_show(struct seq_file *s, void *unused)
{
	struct ad7124_state *st = s->private;
	int i;

	seq_puts(s, "AD7124 Status\n");
	seq_puts(s, "=============\n");

	// Read and display registers
	for (i = 0; i < 16; i++) {
		u32 val;
		ad7124_spi_read(st, i, &val);
		seq_printf(s, "Reg[0x%02x] = 0x%08x\n", i, val);
	}

	// Show configuration state
	seq_printf(s, "\nActive channels: 0x%02x\n", st->active_channels);
	seq_printf(s, "Sample rate: %d SPS\n", st->sample_rate);

	return 0;
}
DEFINE_SHOW_ATTRIBUTE(ad7124_status);  // Creates ad7124_status_fops

/**
 * ad7124_debugfs_reg_access - Register access via debugfs
 *
 * Allows reading/writing registers through IIO debugfs interface.
 */
static int ad7124_debugfs_reg_access(struct iio_dev *indio_dev,
				     unsigned int reg, unsigned int writeval,
				     unsigned int *readval)
{
	struct ad7124_state *st = iio_priv(indio_dev);

	if (readval)
		return ad7124_spi_read(st, reg, readval);
	else
		return ad7124_spi_write(st, reg, writeval);
}

static const struct iio_info ad7124_info = {
	.read_raw = ad7124_read_raw,
	.write_raw = ad7124_write_raw,
	.debugfs_reg_access = ad7124_debugfs_reg_access,  // Enables direct_reg_access
};

static int ad7124_probe(struct spi_device *spi)
{
	struct ad7124_state *st;
	struct iio_dev *indio_dev;

	indio_dev = devm_iio_device_alloc(&spi->dev, sizeof(*st));
	if (!indio_dev)
		return -ENOMEM;

	st = iio_priv(indio_dev);
	st->spi = spi;

	// ... setup iio_dev ...

	ret = devm_iio_device_register(&spi->dev, indio_dev);
	if (ret)
		return ret;

	// Create custom debugfs entries under IIO debugfs directory
	if (iio_get_debugfs_dentry(indio_dev)) {
		debugfs_create_devm_seqfile(&spi->dev, "status",
					    iio_get_debugfs_dentry(indio_dev),
					    ad7124_status_show);
	}

	return 0;
}
```

**Accessing debugfs**:
```bash
# IIO device debugfs is under /sys/kernel/debug/iio/iio:deviceX/

# View custom status file
cat /sys/kernel/debug/iio/iio:device0/status

# Direct register access (if debugfs_reg_access implemented)
echo "0x10 0x1234" > /sys/kernel/debug/iio/iio:device0/direct_reg_access  # Write
cat /sys/kernel/debug/iio/iio:device0/direct_reg_access  # Read last register
```

### Simple Debugfs Types

```c
// Create directory
st->debugfs_root = debugfs_create_dir("ad7124", NULL);

// Simple value files (automatically formatted)
debugfs_create_u32("sample_rate", 0644, st->debugfs_root, &st->sample_rate);
debugfs_create_u8("gain", 0644, st->debugfs_root, &st->gain);
debugfs_create_bool("enabled", 0644, st->debugfs_root, &st->enabled);

// Read-only hex
debugfs_create_x32("status_reg", 0444, st->debugfs_root, &st->status);

// Blob (binary data)
debugfs_create_blob("coefficients", 0444, st->debugfs_root, &st->coef_blob);
```
