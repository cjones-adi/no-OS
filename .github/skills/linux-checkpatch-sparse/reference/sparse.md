# sparse - Static Analysis Tool

Comprehensive guide to using sparse for semantic checking and bug detection in Linux kernel code.

## Installation and Setup

```bash
# Install sparse
sudo apt install sparse

# Or build from source
git clone https://git.kernel.org/pub/scm/devel/sparse/sparse.git
cd sparse
make
make install
```

## Running sparse

```bash
# Check specific file (re-compile with sparse)
make C=1 drivers/iio/adc/ad7124.o

# Check all files
make C=2

# Enable additional warnings
make C=1 W=1 drivers/iio/adc/ad7124.o

# Combine with specific config
make C=2 ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- allmodconfig

# Run sparse directly
sparse drivers/iio/adc/ad7124.c
```

**Warning levels** (W=):
- `W=1`: Enable extra build warnings
- `W=2`: Enable more warnings (usually false positives)
- `W=3`: Enable even more warnings (likely false positives)

## Sparse Annotations

### Address Space Annotations

#### __iomem: I/O memory (MMIO registers)

```c
#include <linux/io.h>

struct my_device {
	void __iomem *base;     // I/O memory pointer
};

static int probe(struct platform_device *pdev)
{
	struct my_device *dev;
	u32 val;

	dev->base = devm_ioremap_resource(&pdev->dev, res);
	if (IS_ERR(dev->base))
		return PTR_ERR(dev->base);

	// Correct - use accessor functions
	val = readl(dev->base + OFFSET_REG);
	writel(val | BIT(3), dev->base + OFFSET_REG);

	// Wrong - direct dereference generates sparse warning
	// val = *(dev->base + OFFSET_REG);
}
```

#### __user: Userspace pointer

```c
#include <linux/uaccess.h>

static ssize_t my_read(struct file *file, char __user *buf,
		       size_t count, loff_t *ppos)
{
	char kernel_buf[128];
	size_t len;

	len = min(count, sizeof(kernel_buf));

	// Correct - use copy_to_user
	if (copy_to_user(buf, kernel_buf, len))
		return -EFAULT;

	// Wrong - direct access generates sparse warning
	// memcpy(buf, kernel_buf, len);

	return len;
}
```

#### __percpu: Per-CPU variable

```c
DEFINE_PER_CPU(int, my_counter);

static void increment_counter(void)
{
	int __percpu *counter = &my_counter;

	this_cpu_inc(my_counter);
}
```

#### __rcu: RCU-protected pointer

```c
struct my_data {
	int value;
};

struct container {
	struct my_data __rcu *data;
};

static void reader(struct container *cont)
{
	struct my_data *data;

	rcu_read_lock();
	data = rcu_dereference(cont->data);
	if (data)
		printk("value: %d\n", data->value);
	rcu_read_unlock();
}
```

### Endianness Annotations

**__be16, __be32, __be64**: Big-endian

**__le16, __le32, __le64**: Little-endian

```c
#include <linux/types.h>
#include <asm/byteorder.h>

struct network_packet {
	__be32 src_addr;        // Network byte order (big-endian)
	__be32 dst_addr;
	__be16 port;
};

struct device_register {
	__le32 control;         // Device register (little-endian)
	__le16 status;
};

static void process_packet(struct network_packet *pkt)
{
	u32 addr;

	// Correct - convert endianness
	addr = be32_to_cpu(pkt->src_addr);

	// Wrong - direct assignment generates sparse warning
	// addr = pkt->src_addr;
}

static void write_register(void __iomem *base)
{
	__le32 reg_val;

	// Correct - convert and write
	reg_val = cpu_to_le32(0x12345678);
	writel(le32_to_cpu(reg_val), base + REG_CONTROL);
}
```

**Conversion functions**:
```c
// CPU to specific endianness
cpu_to_be16(), cpu_to_be32(), cpu_to_be64()
cpu_to_le16(), cpu_to_le32(), cpu_to_le64()

// Specific endianness to CPU
be16_to_cpu(), be32_to_cpu(), be64_to_cpu()
le16_to_cpu(), le32_to_cpu(), le64_to_cpu()

// Swap byte order
swab16(), swab32(), swab64()
```

### __bitwise and __force

**__bitwise**: Type-safe integers (prevents mixing different types)

```c
typedef u32 __bitwise pm_request_t;
typedef u32 __bitwise pm_state_t;

#define PM_SUSPEND ((__force pm_request_t) 1)
#define PM_RESUME ((__force pm_request_t) 2)

static int power_request(pm_request_t req)
{
	// Correct - same bitwise type
	if (req == PM_SUSPEND)
		do_suspend();

	// Wrong - mixing bitwise types generates warning
	// pm_state_t state = req;
}
```

### Locking Annotations

**__must_hold**: Function must be called with lock held

**__acquires**: Function acquires lock

**__releases**: Function releases lock

```c
#include <linux/spinlock.h>

static DEFINE_SPINLOCK(my_lock);

static void locked_function(void) __must_hold(&my_lock)
{
	// This function expects lock to be already held
	// sparse will warn if called without lock
	update_data();
}

static void acquire_and_process(void) __acquires(&my_lock)
{
	spin_lock(&my_lock);
	// sparse knows lock is now held
	process_data();
	spin_unlock(&my_lock);
}

static void process_and_release(void) __releases(&my_lock)
{
	// sparse expects lock to be held on entry
	process_data();
	spin_unlock(&my_lock);
}

// Balanced lock/unlock
static void balanced_function(void)
{
	spin_lock(&my_lock);
	locked_function();      // OK - lock is held
	spin_unlock(&my_lock);
}
```

## Common sparse Warnings

### warning: symbol 'foo' was not declared. Should it be static?

```c
// Bad - function only used in this file, not declared static
int helper_function(void)
{
	return 0;
}

// Good - make it static
static int helper_function(void)
{
	return 0;
}
```

### warning: incorrect type in assignment (different address spaces)

```c
// Bad - assigning __iomem pointer to regular pointer
void *ptr = ioremap(phys_addr, size);

// Good - preserve address space annotation
void __iomem *ptr = ioremap(phys_addr, size);
```

### warning: cast removes address space '<asn:2>' of expression

```c
// Bad - casting away __iomem
u32 *regs = (u32 *)ioremap(addr, size);

// Good - keep __iomem and use proper accessors
void __iomem *regs = ioremap(addr, size);
u32 val = readl(regs);
```

### warning: mixing different enum types

```c
enum state {
	STATE_OFF,
	STATE_ON,
};

enum mode {
	MODE_CONTINUOUS,
	MODE_SINGLE,
};

// Bad - comparing different enum types
if (state == MODE_CONTINUOUS)  // sparse warning

// Good - compare same type
if (mode == MODE_CONTINUOUS)
```

### warning: context imbalance - unexpected unlock

```c
// Bad - unbalanced locking
static void my_function(void)
{
	if (condition)
		spin_lock(&lock);
	process();
	spin_unlock(&lock);     // May unlock without locking
}

// Good - balanced locking
static void my_function(void)
{
	spin_lock(&lock);
	if (condition)
		process();
	spin_unlock(&lock);
}
```
