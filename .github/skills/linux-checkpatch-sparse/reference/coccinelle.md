# Coccinelle - Semantic Patching

Comprehensive guide to using Coccinelle for automated pattern-based code transformation and bug detection.

## Installation

```bash
# Debian/Ubuntu
sudo apt install coccinelle

# Fedora
sudo dnf install coccinelle

# From source
git clone https://github.com/coccinelle/coccinelle
cd coccinelle
./autogen
./configure
make
sudo make install
```

**Minimum version**: 1.0.0-rc11 or later

## Running coccicheck

```bash
# Run all semantic patches in report mode
make coccicheck MODE=report

# Run specific semantic patch
make coccicheck MODE=report COCCI=scripts/coccinelle/free/devm_free.cocci

# Propose fixes (patch mode)
make coccicheck MODE=patch

# Generate context (diff-like output)
make coccicheck MODE=context

# Run on specific directory
make coccicheck M=drivers/iio MODE=report

# Run on specific file
make C=1 CHECK=scripts/coccicheck drivers/iio/adc/ad7124.o

# Parallel execution
make coccicheck J=4 MODE=report

# Verbose output
make coccicheck V=1 MODE=report

# Debug semantic patch
make coccicheck DEBUG_FILE=cocci.log SPFLAGS="--profile --show-trying"
```

**Modes**:
- `report`: Show findings with file:line:column format (default)
- `patch`: Propose code fixes
- `context`: Show context around findings
- `org`: Emacs Org mode output
- `chain`: Try modes sequentially
- `rep+ctxt`: Combine report and context

## Built-in Semantic Patches

### Detect Unnecessary Casts (alloc_cast.cocci)

```bash
make coccicheck MODE=report COCCI=scripts/coccinelle/api/alloc/alloc_cast.cocci
```

**Detects**:
```c
// Bad - unnecessary cast
struct foo *p = (struct foo *)kmalloc(sizeof(*p), GFP_KERNEL);
u8 *buf = (u8 *)devm_kzalloc(&dev->dev, size, GFP_KERNEL);

// Good - no cast needed
struct foo *p = kmalloc(sizeof(*p), GFP_KERNEL);
u8 *buf = devm_kzalloc(&dev->dev, size, GFP_KERNEL);
```

### Detect Invalid devm_* Free (devm_free.cocci)

```bash
make coccicheck MODE=report COCCI=scripts/coccinelle/free/devm_free.cocci
```

**Detects double-free bugs**:
```c
// Bad - devm_ allocated memory freed manually (double free on detach)
void *ptr = devm_kzalloc(&dev->dev, size, GFP_KERNEL);
// ...
kfree(ptr);             // BUG: will be freed again on device detach

// Good - let devres handle it
void *ptr = devm_kzalloc(&dev->dev, size, GFP_KERNEL);
// No manual free needed
```

### Detect Missing IRQF_ONESHOT (irqf_oneshot.cocci)

```bash
make coccicheck MODE=report COCCI=scripts/coccinelle/misc/irqf_oneshot.cocci
```

**Detects**:
```c
// Bad - threaded IRQ without IRQF_ONESHOT
ret = devm_request_threaded_irq(&dev->dev, irq, NULL, thread_fn,
				0, "mydev", priv);

// Good - add IRQF_ONESHOT
ret = devm_request_threaded_irq(&dev->dev, irq, NULL, thread_fn,
				IRQF_ONESHOT, "mydev", priv);
```

### Detect Resource Leaks

```bash
# Check for missing clk_put
make coccicheck MODE=report COCCI=scripts/coccinelle/free/clk_put.cocci

# Check for missing iounmap
make coccicheck MODE=report COCCI=scripts/coccinelle/free/iounmap.cocci

# Check for missing put_device
make coccicheck MODE=report COCCI=scripts/coccinelle/free/put_device.cocci
```

## Writing Custom Semantic Patches

### Basic SmPL Syntax

```coccinelle
// Find all uses of kmalloc
@@
expression E, S;
@@

E = kmalloc(S, ...)
```

### Pattern Matching with Transformation

**Example**: Replace kmalloc with kzalloc when followed by memset

```coccinelle
@@
expression E, S;
@@

-E = kmalloc(S, ...);
-memset(E, 0, S);
+E = kzalloc(S, ...);
```

**Before**:
```c
ptr = kmalloc(size, GFP_KERNEL);
memset(ptr, 0, size);
```

**After**:
```c
ptr = kzalloc(size, GFP_KERNEL);
```

### Check for Missing NULL Checks

```coccinelle
@@
expression E;
statement S;
@@

E = kmalloc(...);
+if (!E)
+	return -ENOMEM;
S
```

## SmPL Advanced Patterns

### Iterate Over All Calls

```coccinelle
@@
expression dev, clk;
@@

clk = devm_clk_get(dev, ...);
...
-clk_prepare_enable(clk)
+clk_enable(clk)
```

### Conditional Patterns

```coccinelle
@@
expression E;
@@

E = kmalloc(...);
(
if (E == NULL) { ... }
|
if (!E) { ... }
|
// No NULL check - report error
)
```
