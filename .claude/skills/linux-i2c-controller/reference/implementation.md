# I2C Controller Driver Implementation

Complete guide to implementing I2C controller (adapter/host) drivers.

## Core Structures

### struct i2c_adapter

The `struct i2c_adapter` represents an I2C bus controller:

```c
struct i2c_adapter {
	struct module *owner;                           // Module owning this adapter
	const struct i2c_algorithm *algo;              // Transfer algorithm methods
	void *algo_data;                               // Private data for algorithm

	const struct i2c_lock_operations *lock_ops;    // Locking operations
	struct rt_mutex bus_lock;                      // Bus-level lock
	struct rt_mutex mux_lock;                      // Mux-level lock (for muxed buses)

	int timeout;                                   // Transfer timeout (jiffies)
	int retries;                                   // Number of retries for lost arbitration
	struct device dev;                             // Device structure

	unsigned long locked_flags;                    // Flags for bus locking
	int nr;                                        // Bus number
	char name[48];                                 // Adapter name

	struct completion dev_released;                // Synchronization for release

	struct mutex userspace_clients_lock;           // Lock for userspace clients
	struct list_head userspace_clients;            // List of userspace clients

	struct i2c_bus_recovery_info *bus_recovery_info;  // Bus recovery support
	const struct i2c_adapter_quirks *quirks;       // Hardware limitations

	struct irq_domain *host_notify_domain;         // For SMBus host notify
	struct regulator *bus_regulator;               // Bus power regulator
};
```

**Key fields**:
- `algo`: Points to algorithm implementation (xfer/smbus_xfer methods)
- `timeout`: Maximum time to wait for transfer (default ~1 second if not set)
- `retries`: How many times to retry after arbitration loss (default 1)
- `bus_recovery_info`: Enables automatic bus recovery when SDA stuck low
- `quirks`: Describes hardware limitations (max message length, no zero-length, etc.)
- `nr`: Bus number (can be auto-assigned with `i2c_add_adapter()`)

### struct i2c_algorithm

The `struct i2c_algorithm` defines how the controller performs transfers:

```c
struct i2c_algorithm {
	/*
	 * Master transfer function. Handles an array of i2c_msg structures.
	 * Returns number of messages processed, or negative errno on error.
	 */
	int (*xfer)(struct i2c_adapter *adap, struct i2c_msg *msgs, int num);

	/*
	 * SMBus-only transfer function for controllers that only support SMBus.
	 * Returns 0 on success, negative errno on error.
	 */
	int (*smbus_xfer)(struct i2c_adapter *adap, u16 addr,
			  unsigned short flags, char read_write,
			  u8 command, int size, union i2c_smbus_data *data);

	/*
	 * Atomic version of xfer for transfers that must work in atomic context
	 * (e.g., accessing PMICs during system suspend/resume).
	 */
	int (*xfer_atomic)(struct i2c_adapter *adap, struct i2c_msg *msgs, int num);

	/*
	 * Atomic version of smbus_xfer for SMBus-only controllers.
	 */
	int (*smbus_xfer_atomic)(struct i2c_adapter *adap, u16 addr,
				 unsigned short flags, char read_write,
				 u8 command, int size, union i2c_smbus_data *data);

	/*
	 * Returns supported functionality flags (I2C_FUNC_* constants).
	 * Called by i2c_check_functionality() to determine adapter capabilities.
	 */
	u32 (*functionality)(struct i2c_adapter *adap);
};
```

**Implementation priority**:
1. Implement `xfer()` for full I2C support (most common)
2. Optionally implement `xfer_atomic()` if your controller can work in atomic context
3. Only implement `smbus_xfer()` if hardware only supports SMBus transactions

### struct i2c_msg

The `struct i2c_msg` describes a single I2C transaction:

```c
struct i2c_msg {
	__u16 addr;     // 7-bit or 10-bit client address
	__u16 flags;    // I2C_M_RD, I2C_M_TEN, I2C_M_RECV_LEN, etc.
	__u16 len;      // Message length in bytes
	__u8 *buf;      // Data buffer
};
```

**Common flags**:
- `I2C_M_RD`: Read from client (otherwise write)
- `I2C_M_TEN`: 10-bit address
- `I2C_M_RECV_LEN`: First byte is message length (SMBus block read)
- `I2C_M_NO_RD_ACK`: Don't ACK last byte on read
- `I2C_M_IGNORE_NAK`: Continue even if client NACKs
- `I2C_M_NOSTART`: Don't send START condition (repeated start)

## Complete Implementation Example

Based on drivers/i2c/busses/i2c-cadence.c (Xilinx Zynq/ZynqMP controller):

```c
#include <linux/i2c.h>
#include <linux/platform_device.h>
#include <linux/interrupt.h>
#include <linux/clk.h>
#include <linux/of.h>

/* Hardware register offsets */
#define CDNS_I2C_CR_OFFSET		0x00  // Control Register
#define CDNS_I2C_SR_OFFSET		0x04  // Status Register
#define CDNS_I2C_ADDR_OFFSET		0x08  // I2C Address Register
#define CDNS_I2C_DATA_OFFSET		0x0C  // I2C Data Register
#define CDNS_I2C_ISR_OFFSET		0x10  // Interrupt Status Register
#define CDNS_I2C_XFER_SIZE_OFFSET	0x14  // Transfer Size Register
#define CDNS_I2C_TIME_OUT_OFFSET	0x1C  // Time Out Register
#define CDNS_I2C_IER_OFFSET		0x24  // Interrupt Enable Register
#define CDNS_I2C_IDR_OFFSET		0x28  // Interrupt Disable Register

/* Control Register bits */
#define CDNS_I2C_CR_HOLD		BIT(4)  // Hold bus
#define CDNS_I2C_CR_ACK_EN		BIT(3)  // ACK enable
#define CDNS_I2C_CR_NEA			BIT(2)  // Normal addressing mode
#define CDNS_I2C_CR_MS			BIT(1)  // Master mode
#define CDNS_I2C_CR_RW			BIT(0)  // Read/Write (1=read)

/* Status Register bits */
#define CDNS_I2C_SR_BA			BIT(8)  // Bus active
#define CDNS_I2C_SR_RXDV		BIT(5)  // RX data valid

/* Interrupt Status/Enable bits */
#define CDNS_I2C_IXR_ARB_LOST		BIT(9)  // Arbitration lost
#define CDNS_I2C_IXR_NACK		BIT(7)  // NACK received
#define CDNS_I2C_IXR_COMP		BIT(0)  // Transfer complete

#define CDNS_I2C_FIFO_DEPTH		16
#define CDNS_I2C_TRANSFER_SIZE		255  // Max bytes per transfer

struct cdns_i2c {
	struct i2c_adapter	adap;
	void __iomem		*membase;
	struct clk		*clk;
	struct clk		*pclk;
	struct completion	xfer_done;
	struct i2c_msg		*curr_msg;
	int			irq;
	u8			*curr_buf;
	int			curr_len;
	int			err_status;
};

/**
 * cdns_i2c_clear_bus_hold - Clear bus hold bit
 *
 * Helper to release the bus hold after transfer completion.
 */
static void cdns_i2c_clear_bus_hold(struct cdns_i2c *id)
{
	u32 reg = readl(id->membase + CDNS_I2C_CR_OFFSET);
	reg &= ~CDNS_I2C_CR_HOLD;
	writel(reg, id->membase + CDNS_I2C_CR_OFFSET);
}

/**
 * cdns_i2c_isr - Interrupt handler
 *
 * Handles transfer completion, NACK, and arbitration lost interrupts.
 */
static irqreturn_t cdns_i2c_isr(int irq, void *ptr)
{
	struct cdns_i2c *id = ptr;
	u32 isr_status;

	isr_status = readl(id->membase + CDNS_I2C_ISR_OFFSET);
	writel(isr_status, id->membase + CDNS_I2C_ISR_OFFSET);  // Clear

	// Check for errors
	if (isr_status & CDNS_I2C_IXR_ARB_LOST) {
		id->err_status = -EAGAIN;  // Arbitration lost - can retry
		complete(&id->xfer_done);
		return IRQ_HANDLED;
	}

	if (isr_status & CDNS_I2C_IXR_NACK) {
		id->err_status = -ENXIO;  // NACK - device not responding
		complete(&id->xfer_done);
		return IRQ_HANDLED;
	}

	// Transfer complete
	if (isr_status & CDNS_I2C_IXR_COMP) {
		// Read remaining data from FIFO for read transfers
		if (id->curr_msg->flags & I2C_M_RD) {
			while (id->curr_len > 0 &&
			       (readl(id->membase + CDNS_I2C_SR_OFFSET) & CDNS_I2C_SR_RXDV)) {
				*id->curr_buf++ = readl(id->membase + CDNS_I2C_DATA_OFFSET);
				id->curr_len--;
			}
		}
		id->err_status = 0;
		complete(&id->xfer_done);
	}

	return IRQ_HANDLED;
}

/**
 * cdns_i2c_master_xfer - Main transfer function
 * @adap: I2C adapter
 * @msgs: Array of messages
 * @num: Number of messages
 *
 * Returns: Number of messages processed on success, negative errno on error
 *
 * This is the core xfer() implementation called by the I2C core for every
 * transfer. It processes each message sequentially, handling both reads
 * and writes. The controller supports a maximum of 255 bytes per transfer.
 */
static int cdns_i2c_master_xfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	struct cdns_i2c *id = i2c_get_adapdata(adap);
	int ret, count;
	u32 reg, bytes_to_send;
	unsigned long timeout;

	// Enable clocks
	ret = clk_enable(id->clk);
	if (ret)
		return ret;

	ret = clk_enable(id->pclk);
	if (ret) {
		clk_disable(id->clk);
		return ret;
	}

	// Process each message
	for (count = 0; count < num; count++) {
		id->curr_msg = &msgs[count];
		id->curr_buf = msgs[count].buf;
		id->curr_len = msgs[count].len;
		id->err_status = 0;
		reinit_completion(&id->xfer_done);

		// Set slave address
		writel(msgs[count].addr, id->membase + CDNS_I2C_ADDR_OFFSET);

		// Configure control register
		reg = readl(id->membase + CDNS_I2C_CR_OFFSET);
		reg &= ~CDNS_I2C_CR_RW;
		if (msgs[count].flags & I2C_M_RD)
			reg |= CDNS_I2C_CR_RW;

		// Hold bus if more messages follow (for repeated start)
		if (count < num - 1)
			reg |= CDNS_I2C_CR_HOLD;
		else
			reg &= ~CDNS_I2C_CR_HOLD;

		writel(reg, id->membase + CDNS_I2C_CR_OFFSET);

		// Set transfer size (controller has 255 byte limit)
		bytes_to_send = min_t(u32, id->curr_len, CDNS_I2C_TRANSFER_SIZE);
		writel(bytes_to_send, id->membase + CDNS_I2C_XFER_SIZE_OFFSET);

		// For write transfers, fill TX FIFO
		if (!(msgs[count].flags & I2C_M_RD)) {
			while (id->curr_len > 0 && bytes_to_send > 0) {
				writel(*id->curr_buf++, id->membase + CDNS_I2C_DATA_OFFSET);
				id->curr_len--;
				bytes_to_send--;
			}
		}

		// Enable interrupts
		writel(CDNS_I2C_IXR_COMP | CDNS_I2C_IXR_NACK | CDNS_I2C_IXR_ARB_LOST,
		       id->membase + CDNS_I2C_IER_OFFSET);

		// Wait for completion
		timeout = wait_for_completion_timeout(&id->xfer_done, adap->timeout);
		if (!timeout) {
			dev_err(&adap->dev, "Transfer timeout\n");
			ret = -ETIMEDOUT;
			goto err_clk_dis;
		}

		// Check for errors
		if (id->err_status) {
			cdns_i2c_clear_bus_hold(id);
			ret = id->err_status;
			goto err_clk_dis;
		}
	}

	ret = num;  // Return number of messages processed

err_clk_dis:
	clk_disable(id->pclk);
	clk_disable(id->clk);
	return ret;
}

/**
 * cdns_i2c_func - Return adapter functionality
 *
 * Advertises I2C_FUNC_I2C for full I2C protocol support and
 * I2C_FUNC_SMBUS_EMUL for SMBus emulation by the I2C core.
 */
static u32 cdns_i2c_func(struct i2c_adapter *adap)
{
	return I2C_FUNC_I2C | I2C_FUNC_SMBUS_EMUL;
}

static const struct i2c_algorithm cdns_i2c_algo = {
	.xfer = cdns_i2c_master_xfer,
	.functionality = cdns_i2c_func,
};

static int cdns_i2c_probe(struct platform_device *pdev)
{
	struct cdns_i2c *id;
	int ret;

	id = devm_kzalloc(&pdev->dev, sizeof(*id), GFP_KERNEL);
	if (!id)
		return -ENOMEM;

	platform_set_drvdata(pdev, id);
	init_completion(&id->xfer_done);

	id->membase = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(id->membase))
		return PTR_ERR(id->membase);

	id->irq = platform_get_irq(pdev, 0);
	if (id->irq < 0)
		return id->irq;

	// Get clocks
	id->clk = devm_clk_get(&pdev->dev, "i2c");
	if (IS_ERR(id->clk))
		return PTR_ERR(id->clk);

	id->pclk = devm_clk_get(&pdev->dev, "pclk");
	if (IS_ERR(id->pclk))
		return PTR_ERR(id->pclk);

	ret = clk_prepare_enable(id->clk);
	if (ret)
		return ret;

	ret = clk_prepare_enable(id->pclk);
	if (ret) {
		clk_disable_unprepare(id->clk);
		return ret;
	}

	// Initialize hardware
	writel(CDNS_I2C_CR_ACK_EN | CDNS_I2C_CR_NEA | CDNS_I2C_CR_MS,
	       id->membase + CDNS_I2C_CR_OFFSET);

	// Set timeout (default 1 second)
	writel(0xFF, id->membase + CDNS_I2C_TIME_OUT_OFFSET);

	clk_disable(id->pclk);
	clk_disable(id->clk);

	// Setup adapter
	i2c_set_adapdata(&id->adap, id);
	id->adap.owner = THIS_MODULE;
	id->adap.algo = &cdns_i2c_algo;
	id->adap.dev.parent = &pdev->dev;
	id->adap.dev.of_node = pdev->dev.of_node;
	id->adap.timeout = msecs_to_jiffies(1000);  // 1 second timeout
	id->adap.retries = 3;  // Retry 3 times on arbitration loss
	snprintf(id->adap.name, sizeof(id->adap.name), "Cadence I2C at %08lx",
		 (unsigned long)id->membase);

	// Request IRQ
	ret = devm_request_irq(&pdev->dev, id->irq, cdns_i2c_isr,
			       IRQF_SHARED, DRIVER_NAME, id);
	if (ret) {
		dev_err(&pdev->dev, "Cannot request IRQ\n");
		goto err_clk;
	}

	// Register adapter
	ret = i2c_add_adapter(&id->adap);
	if (ret < 0)
		goto err_clk;

	dev_info(&pdev->dev, "%s at 0x%08lx mapped to %p, irq=%d\n",
		 id->adap.name, (unsigned long)id->membase, id->membase, id->irq);

	return 0;

err_clk:
	clk_disable_unprepare(id->pclk);
	clk_disable_unprepare(id->clk);
	return ret;
}
```

## I2C Functionality Flags

The `functionality()` callback returns supported features using these flags:

```c
/* I2C functionality flags (from include/uapi/linux/i2c.h) */

// Basic I2C operations
#define I2C_FUNC_I2C                    0x00000001  // Plain I2C support
#define I2C_FUNC_10BIT_ADDR             0x00000002  // 10-bit addressing
#define I2C_FUNC_PROTOCOL_MANGLING      0x00000004  // I2C_M_* flags supported
#define I2C_FUNC_NOSTART                0x00000010  // I2C_M_NOSTART (repeated start)

// SMBus operations
#define I2C_FUNC_SMBUS_QUICK            0x00010000  // SMBus Quick command
#define I2C_FUNC_SMBUS_READ_BYTE        0x00020000  // SMBus Read Byte
#define I2C_FUNC_SMBUS_WRITE_BYTE       0x00040000  // SMBus Write Byte
#define I2C_FUNC_SMBUS_READ_BYTE_DATA   0x00080000  // SMBus Read Byte Data
#define I2C_FUNC_SMBUS_WRITE_BYTE_DATA  0x00100000  // SMBus Write Byte Data
#define I2C_FUNC_SMBUS_READ_WORD_DATA   0x00200000  // SMBus Read Word Data
#define I2C_FUNC_SMBUS_WRITE_WORD_DATA  0x00400000  // SMBus Write Word Data
#define I2C_FUNC_SMBUS_PROC_CALL        0x00800000  // SMBus Process Call
#define I2C_FUNC_SMBUS_READ_BLOCK_DATA  0x01000000  // SMBus Read Block Data
#define I2C_FUNC_SMBUS_WRITE_BLOCK_DATA 0x02000000  // SMBus Write Block Data

// SMBus emulation - I2C core will emulate SMBus on top of I2C
#define I2C_FUNC_SMBUS_EMUL \
	(I2C_FUNC_SMBUS_QUICK | I2C_FUNC_SMBUS_BYTE | \
	 I2C_FUNC_SMBUS_BYTE_DATA | I2C_FUNC_SMBUS_WORD_DATA | \
	 I2C_FUNC_SMBUS_PROC_CALL | I2C_FUNC_SMBUS_WRITE_BLOCK_DATA | \
	 I2C_FUNC_SMBUS_I2C_BLOCK | I2C_FUNC_SMBUS_PEC)

// Typical implementation
static u32 my_i2c_func(struct i2c_adapter *adap)
{
	// Most controllers support full I2C + SMBus emulation
	return I2C_FUNC_I2C | I2C_FUNC_SMBUS_EMUL;
}
```

## Adapter Registration

Two methods to register I2C adapters:

```c
/**
 * i2c_add_adapter - Register adapter with dynamic bus number
 *
 * The I2C core will assign the next available bus number.
 */
ret = i2c_add_adapter(&id->adap);

/**
 * i2c_add_numbered_adapter - Register adapter with specific bus number
 *
 * Use when bus number matters (devicetree aliases, backwards compatibility).
 * Set id->adap.nr before calling.
 */
id->adap.nr = 0;  // Request i2c-0
ret = i2c_add_numbered_adapter(&id->adap);
```

For devicetree, use aliases to specify bus numbers:
```dts
aliases {
	i2c0 = &i2c_main;
	i2c1 = &i2c_aux;
};
```

Then call `i2c_add_adapter()` and the core will use the alias number.

## Adapter Quirks

The `struct i2c_adapter_quirks` describes hardware limitations:

```c
/**
 * struct i2c_adapter_quirks - describe flaws of an i2c adapter
 * @flags: see I2C_AQ_* for possible flags
 * @max_num_msgs: maximum number of messages per transfer
 * @max_write_len: maximum length of a write message
 * @max_read_len: maximum length of a read message
 * @max_comb_1st_msg_len: maximum length of the first msg in a combined message
 * @max_comb_2nd_msg_len: maximum length of the second msg in a combined message
 */
struct i2c_adapter_quirks {
	u64 flags;
	int max_num_msgs;
	u16 max_write_len;
	u16 max_read_len;
	u16 max_comb_1st_msg_len;
	u16 max_comb_2nd_msg_len;
};

/* Quirk flags */
#define I2C_AQ_COMB			BIT(0)  // Can combine I2C_M_RD with write
#define I2C_AQ_COMB_WRITE_FIRST		BIT(1)  // Write must be first in combined
#define I2C_AQ_COMB_READ_SECOND		BIT(2)  // Read must be second in combined
#define I2C_AQ_COMB_SAME_ADDR		BIT(3)  // Combined msgs must have same addr
#define I2C_AQ_NO_ZERO_LEN		BIT(4)  // Zero-length messages not supported
#define I2C_AQ_NO_ZERO_LEN_READ		BIT(5)  // Zero-length reads not supported
#define I2C_AQ_NO_ZERO_LEN_WRITE	BIT(6)  // Zero-length writes not supported
#define I2C_AQ_NO_REP_START		BIT(7)  // Repeated start not supported
#define I2C_AQ_NO_CLK_STRETCH		BIT(8)  // Clock stretching not supported
```

**Example: Controller with 255-byte transfer limit**:
```c
static const struct i2c_adapter_quirks my_i2c_quirks = {
	.max_write_len = 255,
	.max_read_len = 255,
	.max_comb_1st_msg_len = 255,
	.max_comb_2nd_msg_len = 255,
};

// In probe():
id->adap.quirks = &my_i2c_quirks;
```

The I2C core will automatically split large transfers and return `-EOPNOTSUPP` for unsupported transactions.
