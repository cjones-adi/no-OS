# Clock Consumer API Reference

Complete reference for device drivers using clocks.

## Getting Clocks

### devm_clk_get()

```c
struct clk *devm_clk_get(struct device *dev, const char *id);
```

Get a clock by name. Resource-managed - automatically freed on driver detach.

**Parameters**:
- `dev`: Device structure
- `id`: Clock ID string (matches devicetree `clock-names`)

**Returns**: Clock pointer or ERR_PTR on error

**Example**:
```c
struct clk *clk;

clk = devm_clk_get(&pdev->dev, "core");
if (IS_ERR(clk))
	return PTR_ERR(clk);
```

**Devicetree**:
```dts
my_device {
	clocks = <&clkgen 0>;
	clock-names = "core";
};
```

### devm_clk_get_optional()

```c
struct clk *devm_clk_get_optional(struct device *dev, const char *id);
```

Get an optional clock. Returns NULL if clock is not present (not an error).

**Returns**: Clock pointer, NULL if not present, or ERR_PTR on error

**Use case**: For clocks that may not exist in all configurations.

**Example**:
```c
struct clk *ref_clk;

ref_clk = devm_clk_get_optional(&pdev->dev, "ref");
if (IS_ERR(ref_clk))
	return PTR_ERR(ref_clk);

if (ref_clk) {
	// Use external reference
} else {
	// Use internal oscillator
}
```

### devm_clk_get_enabled()

```c
struct clk *devm_clk_get_enabled(struct device *dev, const char *id);
```

Convenience function that combines get + prepare + enable in one call.

**Returns**: Clock pointer or ERR_PTR on error

**Automatically**: Disabled and unprepared on driver detach.

**Example**:
```c
struct clk *clk;

clk = devm_clk_get_enabled(&pdev->dev, "core");
if (IS_ERR(clk))
	return PTR_ERR(clk);

// Clock is ready to use immediately
```

### clk_bulk_get()

```c
int clk_bulk_get(struct device *dev, int num_clks, struct clk_bulk_data *clks);
int devm_clk_bulk_get(struct device *dev, int num_clks, struct clk_bulk_data *clks);
```

Get multiple clocks at once.

**Example**:
```c
struct clk_bulk_data clks[] = {
	{ .id = "core" },
	{ .id = "bus" },
	{ .id = "ref" },
};

ret = devm_clk_bulk_get(&pdev->dev, ARRAY_SIZE(clks), clks);
if (ret)
	return ret;

// Access individual clocks
clks[0].clk  // core clock
clks[1].clk  // bus clock
clks[2].clk  // ref clock
```

## Preparing and Enabling

### Two-Stage Activation

Clocks have separate prepare and enable stages:

1. **Prepare** (may sleep): Complex operations like enabling parent PLLs, waiting for lock
2. **Enable** (atomic): Fast gate/ungate operation

### clk_prepare()

```c
int clk_prepare(struct clk *clk);
```

Prepare clock for enabling. May sleep.

**Must be called**: Before `clk_enable()`
**Can be called**: From non-atomic context only
**Returns**: 0 on success, negative errno on error

### clk_enable()

```c
int clk_enable(struct clk *clk);
```

Enable the clock. Cannot sleep.

**Must be called**: After `clk_prepare()`
**Can be called**: From atomic context
**Returns**: 0 on success, negative errno on error

### clk_prepare_enable()

```c
int clk_prepare_enable(struct clk *clk);
```

Combined prepare + enable. Convenience function.

**Cannot be called**: From atomic context (may sleep)
**Returns**: 0 on success, negative errno on error

**Example**:
```c
ret = clk_prepare_enable(mydev->clk);
if (ret) {
	dev_err(dev, "Failed to enable clock: %d\n", ret);
	return ret;
}
```

### clk_disable_unprepare()

```c
void clk_disable_unprepare(struct clk *clk);
```

Combined disable + unprepare.

**Example**:
```c
clk_disable_unprepare(mydev->clk);
```

### Separate Calls

For atomic context enable/disable:

```c
// Setup (can sleep)
ret = clk_prepare(mydev->clk);
if (ret)
	return ret;

// Fast enable in atomic context
ret = clk_enable(mydev->clk);
if (ret) {
	clk_unprepare(mydev->clk);
	return ret;
}

// ... use clock ...

// Fast disable in atomic context
clk_disable(mydev->clk);

// Cleanup (can sleep)
clk_unprepare(mydev->clk);
```

### clk_bulk_prepare_enable()

```c
int clk_bulk_prepare_enable(int num_clks, struct clk_bulk_data *clks);
void clk_bulk_disable_unprepare(int num_clks, struct clk_bulk_data *clks);
```

Enable/disable multiple clocks at once.

**Example**:
```c
ret = clk_bulk_prepare_enable(ARRAY_SIZE(clks), clks);
if (ret)
	return ret;

// ... use clocks ...

clk_bulk_disable_unprepare(ARRAY_SIZE(clks), clks);
```

## Rate Operations

### clk_get_rate()

```c
unsigned long clk_get_rate(struct clk *clk);
```

Get current clock rate in Hz.

**Returns**: Clock rate in Hz

**Example**:
```c
unsigned long rate = clk_get_rate(mydev->clk);
dev_info(dev, "Clock rate: %lu Hz (%lu MHz)\n", rate, rate / 1000000);
```

### clk_set_rate()

```c
int clk_set_rate(struct clk *clk, unsigned long rate);
```

Set clock rate.

**Parameters**:
- `clk`: Clock to configure
- `rate`: Desired rate in Hz

**Returns**: 0 on success, negative errno on error

**Important**:
- Actual rate may differ from requested (check with `clk_get_rate()`)
- Some clocks require being disabled before rate change (CLK_SET_RATE_GATE)

**Example**:
```c
// Request 100 MHz
ret = clk_set_rate(mydev->clk, 100000000);
if (ret) {
	dev_err(dev, "Failed to set clock rate: %d\n", ret);
	return ret;
}

// Verify actual rate
unsigned long actual_rate = clk_get_rate(mydev->clk);
dev_info(dev, "Requested 100 MHz, got %lu Hz\n", actual_rate);
```

### clk_round_rate()

```c
long clk_round_rate(struct clk *clk, unsigned long rate);
```

Find closest achievable rate without actually changing the clock.

**Returns**: Closest achievable rate (may be different from requested)

**Use case**: Query what rate the clock can actually achieve before calling `clk_set_rate()`

**Example**:
```c
unsigned long requested = 100000000;  // 100 MHz
long rounded = clk_round_rate(mydev->clk, requested);

if (rounded < 0) {
	dev_err(dev, "Failed to round rate: %ld\n", rounded);
	return rounded;
}

dev_info(dev, "Requested %lu Hz, can achieve %lu Hz\n", requested, rounded);

// Now set the rate
ret = clk_set_rate(mydev->clk, requested);
```

### clk_set_rate_range()

```c
int clk_set_rate_range(struct clk *clk, unsigned long min, unsigned long max);
```

Constrain clock rate to a range.

**Parameters**:
- `min`: Minimum allowed rate in Hz
- `max`: Maximum allowed rate in Hz

**Use case**: Prevent clock rate from going outside specified range. Useful when multiple consumers need different rate ranges.

**Example**:
```c
// Constrain to 50-150 MHz
ret = clk_set_rate_range(mydev->clk, 50000000, 150000000);
if (ret) {
	dev_err(dev, "Failed to set rate range: %d\n", ret);
	return ret;
}
```

## Parent Operations

### clk_get_parent()

```c
struct clk *clk_get_parent(struct clk *clk);
```

Get current parent clock.

**Returns**: Parent clock pointer or NULL

### clk_set_parent()

```c
int clk_set_parent(struct clk *clk, struct clk *parent);
```

Change clock parent (for muxed clocks).

**Returns**: 0 on success, negative errno on error

## Complete Consumer Example

From IIO ADC driver:

```c
#include <linux/clk.h>

struct ad7124_state {
	struct spi_device *spi;
	struct clk *mclk;         // Master clock
	unsigned long mclk_rate;  // Cached rate
};

static int ad7124_probe(struct spi_device *spi)
{
	struct iio_dev *indio_dev;
	struct ad7124_state *st;
	int ret;

	indio_dev = devm_iio_device_alloc(&spi->dev, sizeof(*st));
	if (!indio_dev)
		return -ENOMEM;

	st = iio_priv(indio_dev);
	st->spi = spi;

	// Get optional master clock
	st->mclk = devm_clk_get_optional(&spi->dev, "mclk");
	if (IS_ERR(st->mclk))
		return PTR_ERR(st->mclk);

	if (st->mclk) {
		// Prepare and enable clock
		ret = clk_prepare_enable(st->mclk);
		if (ret) {
			dev_err(&spi->dev, "Failed to enable mclk: %d\n", ret);
			return ret;
		}

		// Get rate for ADC timing calculations
		st->mclk_rate = clk_get_rate(st->mclk);
		dev_dbg(&spi->dev, "Using master clock at %lu Hz\n", st->mclk_rate);
	} else {
		// Use internal oscillator
		st->mclk_rate = AD7124_INTERNAL_OSC_FREQ;
		dev_dbg(&spi->dev, "Using internal oscillator\n");
	}

	// ... rest of initialization ...

	return devm_iio_device_register(&spi->dev, indio_dev);
}

static void ad7124_remove(struct spi_device *spi)
{
	struct iio_dev *indio_dev = spi_get_drvdata(spi);
	struct ad7124_state *st = iio_priv(indio_dev);

	if (st->mclk)
		clk_disable_unprepare(st->mclk);
}
```

## Bulk Clock Example

Managing multiple clocks:

```c
struct my_device {
	struct device *dev;
	struct clk_bulk_data clks[3];
};

static int my_probe(struct platform_device *pdev)
{
	struct my_device *mydev;
	int ret;

	mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
	if (!mydev)
		return -ENOMEM;

	mydev->dev = &pdev->dev;

	// Initialize clock names
	mydev->clks[0].id = "core";
	mydev->clks[1].id = "bus";
	mydev->clks[2].id = "ref";

	// Get all clocks
	ret = devm_clk_bulk_get(&pdev->dev, ARRAY_SIZE(mydev->clks), mydev->clks);
	if (ret) {
		dev_err(&pdev->dev, "Failed to get clocks: %d\n", ret);
		return ret;
	}

	// Enable all clocks
	ret = clk_bulk_prepare_enable(ARRAY_SIZE(mydev->clks), mydev->clks);
	if (ret) {
		dev_err(&pdev->dev, "Failed to enable clocks: %d\n", ret);
		return ret;
	}

	// ... use device ...

	return 0;
}

static int my_remove(struct platform_device *pdev)
{
	struct my_device *mydev = platform_get_drvdata(pdev);

	clk_bulk_disable_unprepare(ARRAY_SIZE(mydev->clks), mydev->clks);

	return 0;
}
```

## Common Patterns

### Optional Clock with Fallback

```c
st->ext_clk = devm_clk_get_optional(&pdev->dev, "ext");
if (IS_ERR(st->ext_clk))
	return PTR_ERR(st->ext_clk);

if (st->ext_clk) {
	ret = clk_prepare_enable(st->ext_clk);
	if (ret)
		return ret;
	st->rate = clk_get_rate(st->ext_clk);
} else {
	// Use default internal rate
	st->rate = INTERNAL_CLOCK_RATE;
}
```

### Runtime Clock Gating (Power Management)

```c
static int my_runtime_suspend(struct device *dev)
{
	struct my_device *mydev = dev_get_drvdata(dev);

	clk_disable_unprepare(mydev->clk);
	return 0;
}

static int my_runtime_resume(struct device *dev)
{
	struct my_device *mydev = dev_get_drvdata(dev);

	return clk_prepare_enable(mydev->clk);
}

static const struct dev_pm_ops my_pm_ops = {
	SET_RUNTIME_PM_OPS(my_runtime_suspend, my_runtime_resume, NULL)
};
```

### Rate Change with Disable

Some clocks require CLK_SET_RATE_GATE and must be disabled before rate change:

```c
// Disable clock
clk_disable_unprepare(mydev->clk);

// Change rate
ret = clk_set_rate(mydev->clk, new_rate);
if (ret) {
	dev_err(dev, "Failed to set rate: %d\n", ret);
	return ret;
}

// Re-enable clock
ret = clk_prepare_enable(mydev->clk);
if (ret) {
	dev_err(dev, "Failed to enable clock: %d\n", ret);
	return ret;
}
```
