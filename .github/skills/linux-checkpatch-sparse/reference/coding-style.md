# Linux Kernel Coding Style - Detailed Guide

This document provides comprehensive coverage of Linux kernel coding style conventions.

## 1. Indentation

**Rule**: Use 8-character tabs for indentation. Never use spaces.

```c
// Correct
if (condition) {
	do_something();          // 8-space tab
	if (nested_condition) {
		nested_action();      // 16 spaces (2 tabs)
	}
}

// Incorrect
if (condition) {
    do_something();          // 4 spaces - WRONG
        nested_action();     // Mixed spaces - WRONG
}
```

**Rationale**: Deep nesting (> 3 levels) indicates code should be refactored. 8-space tabs make excessive nesting visually obvious.

**Switch statements**: Align `switch` and `case` at same column:

```c
switch (action) {
case ACTION_READ:
	do_read();
	break;
case ACTION_WRITE:
	do_write();
	break;
default:
	return -EINVAL;
}
```

## 2. Line Length

**Rule**: 80 columns maximum (100 acceptable in some cases).

```c
// Bad - exceeds 80 columns
dev_err(&spi->dev, "Failed to initialize device with configuration error code %d\n", ret);

// Good - split into multiple lines
dev_err(&spi->dev, "Failed to initialize device: %d\n", ret);

// Good - split function call
ret = my_long_function_name(device, parameter1, parameter2,
			     parameter3, parameter4);

// Exception: Never break user-visible strings (enables grepping)
dev_err(&dev->dev, "This is a very long error message that exceeds 80 characters but is kept on one line for grepability\n");
```

## 3. Braces

**Functions**: Opening brace on new line

```c
// Correct
static int my_function(struct device *dev)
{
	/* body */
}

// Incorrect
static int my_function(struct device *dev) {
	/* body */
}
```

**Control statements**: Opening brace on same line

```c
// Correct
if (condition) {
	action();
} else {
	other_action();
}

while (condition) {
	action();
}

for (i = 0; i < count; i++) {
	action();
}

do {
	action();
} while (condition);

// Single statement - no braces needed
if (error)
	return error;

// But use braces if any branch needs them
if (condition) {
	action1();
	action2();
} else {
	single_action();
}
```

## 4. Spacing

**After keywords** (if, switch, case, for, do, while):

```c
if (condition)
for (i = 0; i < n; i++)
while (condition)
switch (value)
```

**Not after function-like keywords**:

```c
sizeof(struct foo)
typeof(x)
alignof(struct bar)
__attribute__((packed))
```

**Around operators**:

```c
// Binary and ternary operators
x = y + z;
result = (a > b) ? a : b;
value |= BIT(3);

// No space after unary operators
!enabled
~mask
++i
&addr
*ptr

// No space around structure member operators
dev->parent
chip.ngpio
```

**Pointer declarations**: Asterisk attaches to variable name

```c
char *linux_banner;
int *my_func(void)
unsigned long long memparse(char *ptr, char **retptr);

// Not this
char* linux_banner;     // Wrong
char * linux_banner;    // Wrong
```

## 5. Naming

**Global symbols**: Descriptive names

```c
// Good
int i2c_transfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num);

// Bad
int foo(struct i2c_adapter *adap, struct i2c_msg *msgs, int num);
```

**Local variables**: Short, meaningful names

```c
int i, j;               // Loop counters
int ret;                // Return value
int err;                // Error code
struct device *dev;     // Device pointer
int tmp;                // Temporary variable
```

**Avoid**:
- Hungarian notation: `iCount`, `szName`
- Verbose names: `ThisVariableIsATemporaryCounter`
- Unclear abbreviations: `cnt`, `flg`

**Inclusive terminology**: Avoid `master/slave`, `blacklist/whitelist`

```c
// Preferred alternatives
// For master/slave: primary/secondary, controller/device, leader/follower
spi->controller (not spi->master)
i2c->target (not i2c->slave)

// For blacklist/whitelist: denylist/allowlist, blocklist/passlist
```

## 6. Typedefs

**Avoid typedefs** for structures and pointers

```c
// Bad
typedef struct {
	int x;
	int y;
} point_t;

// Good
struct point {
	int x;
	int y;
};
```

**Acceptable typedefs**:
- Opaque types: `pte_t`, `pgd_t`
- Integer types for clarity: `u8`, `u16`, `u32`, `u64`, `s8`, `s16`, `s32`, `s64`
- Sparse type checking: `__be32`, `__le32`, `__bitwise`

## 7. Functions

**Size**: Short and focused (1-2 screenfuls on 80x24 terminal)

```c
// Good - does one thing
static int validate_config(struct config *cfg)
{
	if (!cfg)
		return -EINVAL;
	if (cfg->value > MAX_VALUE)
		return -ERANGE;
	return 0;
}

// Bad - does too many things, too long
static int do_everything(struct device *dev, struct config *cfg, int mode)
{
	/* 200 lines of mixed validation, initialization,
	 * configuration, error handling, and business logic */
}
```

**Local variables**: Limit to 5-10 per function

**Function prototypes**: Include parameter names

```c
// Good
int request_irq(unsigned int irq, irq_handler_t handler,
		unsigned long flags, const char *name, void *dev);

// Bad
int request_irq(unsigned int, irq_handler_t, unsigned long,
		const char *, void *);
```

**Exported functions**: EXPORT macro immediately after closing brace

```c
int i2c_transfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	/* ... */
	return ret;
}
EXPORT_SYMBOL(i2c_transfer);
```

## 8. Comments

**C-style comments** (not C++ style):

```c
// Bad
// This is a comment

// Good
/* This is a comment */

/*
 * This is a multi-line comment
 * with proper formatting
 */
```

**What to comment**: Explain *what* and *why*, not *how*

```c
// Bad
/* Set bit 3 */
reg |= BIT(3);

// Good
/* Enable continuous conversion mode */
reg |= AD7124_CONFIG_CONT;
```

**Function comments**: Use kernel-doc format

```c
/**
 * i2c_transfer - Perform I2C transfer
 * @adap: I2C adapter
 * @msgs: Array of messages
 * @num: Number of messages
 *
 * Execute one or more I2C transactions atomically.
 *
 * Return: Number of messages transferred, or negative error code
 */
int i2c_transfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)
{
	/* ... */
}
```

## 9. Error Handling

**Return values**:
- Commands/actions: 0 for success, -Exxx for error
- Predicates: boolean (0=false, non-zero=true)
- Computed values: actual result, ERR_PTR for errors

```c
// Command function
static int device_init(struct device *dev)
{
	int ret;

	ret = device_power_on(dev);
	if (ret)
		return ret;           // Propagate error

	ret = device_configure(dev);
	if (ret)
		goto err_power_off;   // Cleanup on error

	return 0;

err_power_off:
	device_power_off(dev);
	return ret;
}

// Predicate function
static bool device_is_ready(struct device *dev)
{
	return (readl(dev->base + STATUS_REG) & STATUS_READY) != 0;
}

// Computed result
static struct device *find_device(int id)
{
	struct device *dev;

	dev = lookup_device(id);
	if (!dev)
		return ERR_PTR(-ENODEV);

	return dev;
}
```

## 10. Goto for Cleanup

**Use goto** for error cleanup paths:

```c
static int probe(struct platform_device *pdev)
{
	struct my_device *mydev;
	int ret;

	mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
	if (!mydev)
		return -ENOMEM;

	mydev->clk = devm_clk_get(&pdev->dev, "adc");
	if (IS_ERR(mydev->clk)) {
		ret = PTR_ERR(mydev->clk);
		goto err_free;
	}

	ret = clk_prepare_enable(mydev->clk);
	if (ret)
		goto err_free;

	ret = device_init(mydev);
	if (ret)
		goto err_disable_clk;

	return 0;

err_disable_clk:
	clk_disable_unprepare(mydev->clk);
err_free:
	kfree(mydev);
	return ret;
}
```

**Label naming**: Describe what cleanup happens, not error number

```c
// Good
err_disable_clk:
err_free_irq:
err_unmap:
out_unlock:

// Bad
err1:
err2:
error:
```

## 11. Macros

**Capitalization**: Macros use UPPERCASE

```c
#define MAX_BUFFER_SIZE 1024
#define AD7124_MODE_CONTINUOUS BIT(0)
```

**Multi-statement macros**: Wrap in do-while

```c
#define UPDATE_REGISTER(dev, reg, val) \
	do { \
		writel(val, dev->base + reg); \
		dev->cached_##reg = val; \
	} while (0)
```

**Expression macros**: Parenthesize arguments and expression

```c
// Good
#define SQUARE(x) ((x) * (x))

// Bad
#define SQUARE(x) x * x          // SQUARE(1+1) = 1+1*1+1 = 3

// Good
#define MIN(a, b) ({ \
	typeof(a) _a = (a); \
	typeof(b) _b = (b); \
	_a < _b ? _a : _b; \
})
```
