# checkpatch.pl - Coding Style Checker

Comprehensive guide to using checkpatch.pl for Linux kernel code style verification.

## Basic Usage

```bash
# Check patch file
./scripts/checkpatch.pl 0001-my-patch.patch

# Check uncommitted changes
git diff | ./scripts/checkpatch.pl -

# Check committed changes
git format-patch -1 HEAD --stdout | ./scripts/checkpatch.pl -

# Check specific commits
git format-patch -2 --stdout | ./scripts/checkpatch.pl -

# Check file directly
./scripts/checkpatch.pl -f drivers/iio/adc/ad7124.c

# Strict mode (includes style suggestions)
./scripts/checkpatch.pl --strict patch.patch

# Ignore specific warnings
./scripts/checkpatch.pl --ignore=LINE_SPACING,LONG_LINE patch.patch

# Set line length limit
./scripts/checkpatch.pl --max-line-length=100 patch.patch

# Show types for all issues
./scripts/checkpatch.pl --show-types patch.patch

# Fix simple issues automatically
./scripts/checkpatch.pl --fix-inplace -f file.c
```

## Common Errors and Fixes

### ERROR: spaces required around that '=' (ctx:VxV)

```c
// Bad
int ret=0;
x=y+z;

// Good
int ret = 0;
x = y + z;
```

### ERROR: open brace '{' following function definitions go on the next line

```c
// Bad
static int my_func(void) {
	return 0;
}

// Good
static int my_func(void)
{
	return 0;
}
```

### ERROR: trailing whitespace

```c
// Bad (space at end of line)
int x = 0; ␣

// Good
int x = 0;
```

### ERROR: do not use assignment in if condition

```c
// Bad
if ((ret = device_init(dev)) < 0)
	return ret;

// Good
ret = device_init(dev);
if (ret < 0)
	return ret;
```

### ERROR: that open brace { should be on the previous line

```c
// Bad
if (condition)
{
	action();
}

// Good
if (condition) {
	action();
}
```

## Common Warnings and Fixes

### WARNING: line over 80 characters

```c
// Bad
dev_err(&spi->dev, "Failed to initialize device with error code %d at line %d\n", ret, __LINE__);

// Good
dev_err(&spi->dev, "Device initialization failed: %d\n", ret);
```

### WARNING: missing space after return type

```c
// Bad
static int*my_function(void)

// Good
static int *my_function(void)
```

### WARNING: braces {} are not necessary for single statement blocks

```c
// Bad
if (ret) {
	return ret;
}

// Good
if (ret)
	return ret;

// But use braces when one branch needs them
if (condition) {
	statement1();
	statement2();
} else {
	single_statement();
}
```

### WARNING: Prefer using '"%s...", __func__' to using 'function_name'

```c
// Bad
dev_dbg(&dev->dev, "my_function: error\n");

// Good
dev_dbg(&dev->dev, "%s: error\n", __func__);
```

### WARNING: Missing or malformed SPDX-License-Identifier tag

```c
// Bad (missing)
/*
 * Driver for AD7124 ADC
 */

// Good
// SPDX-License-Identifier: GPL-2.0
/*
 * Driver for AD7124 ADC
 */

// For dual licensing
// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
```

### WARNING: EXPORT_SYMBOL(foo); should immediately follow its function/variable

```c
// Bad
int i2c_transfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	return ret;
}

static int helper(void) { }

EXPORT_SYMBOL(i2c_transfer);

// Good
int i2c_transfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	return ret;
}
EXPORT_SYMBOL(i2c_transfer);

static int helper(void) { }
```

### WARNING: Prefer 'unsigned int' to bare use of 'unsigned'

```c
// Bad
static int my_func(unsigned offset)

// Good
static int my_func(unsigned int offset)
```

### WARNING: quoted string split across lines

```c
// Bad
dev_err(&dev->dev, "This is a very long "
		   "error message\n");

// Good
dev_err(&dev->dev,
	"This is a very long error message\n");
```

## CHECK Warnings (--strict mode)

### CHECK: Alignment should match open parenthesis

```c
// Bad
ret = request_irq(irq, handler,
	IRQF_TRIGGER_HIGH, name, dev);

// Good
ret = request_irq(irq, handler,
		  IRQF_TRIGGER_HIGH, name, dev);
```

### CHECK: Prefer kernel type 'u32' over 'uint32_t'

```c
// Bad
uint32_t reg_value;
uint8_t buffer[16];

// Good
u32 reg_value;
u8 buffer[16];
```

### CHECK: Unnecessary parentheses

```c
// Bad
if ((ret < 0))
	return ret;

// Good
if (ret < 0)
	return ret;
```

### CHECK: Lines should not end with a '('

```c
// Bad
ret = my_very_long_function_name(
	arg1, arg2, arg3);

// Good
ret = my_very_long_function_name(arg1, arg2,
				 arg3);
```
