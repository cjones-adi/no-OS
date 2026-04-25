# Clock Provider API Reference

Complete reference for implementing clock controller drivers.

## Core Structures

### struct clk_hw

The hardware-specific clock structure. Bridge between generic framework and hardware implementation.

```c
#include <linux/clk-provider.h>

struct clk_hw {
	struct clk_core *core;          // Points to framework clock
	struct clk *clk;                // Consumer clock handle
	const struct clk_init_data *init;  // Initialization data
};
```

**Usage**: Drivers embed `clk_hw` in their own structures using `container_of()`.

**Example**:
```c
struct my_pll {
	void __iomem *base;
	struct clk_hw hw;
	/* Hardware-specific fields */
};

#define to_my_pll(_hw) container_of(_hw, struct my_pll, hw)
```

### struct clk_init_data

Clock initialization data passed during registration.

```c
struct clk_init_data {
	const char *name;               // Clock name
	const struct clk_ops *ops;      // Operations
	const char * const *parent_names;  // Parent clock names
	const struct clk_parent_data *parent_data;  // Or parent data
	const struct clk_hw **parent_hws;  // Or parent hw pointers
	u8 num_parents;                 // Number of parents
	unsigned long flags;            // CLK_* flags
};
```

**Parent specification** (choose one method):
1. `parent_names`: Array of parent clock name strings
2. `parent_data`: Array of `struct clk_parent_data` (preferred for DT)
3. `parent_hws`: Array of `struct clk_hw *` pointers (for internal clocks)

**Example**:
```c
static const char * const pll_parents[] = { "ref_clk", "osc" };

struct clk_init_data init = {
	.name = "my_pll",
	.ops = &my_pll_ops,
	.parent_names = pll_parents,
	.num_parents = ARRAY_SIZE(pll_parents),
	.flags = CLK_SET_RATE_GATE,
};
```

### struct clk_ops

Hardware-specific operations. Only implement what your hardware supports.

```c
struct clk_ops {
	// Preparation (may sleep, protected by prepare_lock mutex)
	int (*prepare)(struct clk_hw *hw);
	void (*unprepare)(struct clk_hw *hw);
	int (*is_prepared)(struct clk_hw *hw);

	// Enable/disable (atomic, cannot sleep, protected by enable_lock spinlock)
	int (*enable)(struct clk_hw *hw);
	void (*disable)(struct clk_hw *hw);
	int (*is_enabled)(struct clk_hw *hw);

	// Rate operations (protected by prepare_lock mutex)
	unsigned long (*recalc_rate)(struct clk_hw *hw, unsigned long parent_rate);
	long (*round_rate)(struct clk_hw *hw, unsigned long rate, unsigned long *parent_rate);
	int (*determine_rate)(struct clk_hw *hw, struct clk_rate_request *req);
	int (*set_rate)(struct clk_hw *hw, unsigned long rate, unsigned long parent_rate);

	// Parent operations (protected by prepare_lock mutex)
	int (*set_parent)(struct clk_hw *hw, u8 index);
	u8 (*get_parent)(struct clk_hw *hw);

	// Phase operations
	int (*set_phase)(struct clk_hw *hw, int degrees);
	int (*get_phase)(struct clk_hw *hw);

	// Debugging
	void (*debug_init)(struct clk_hw *hw, struct dentry *dentry);
};
```

## Clock Flags

### Rate and Parent Flags

```c
#define CLK_SET_RATE_GATE       BIT(0)  // Clock must be gated to change rate
#define CLK_SET_PARENT_GATE     BIT(1)  // Clock must be gated to change parent
#define CLK_SET_RATE_PARENT     BIT(2)  // Propagate rate changes to parent
#define CLK_IGNORE_UNUSED       BIT(3)  // Don't disable if unused
#define CLK_GET_RATE_NOCACHE    BIT(6)  // Always recalculate rate
#define CLK_SET_RATE_NO_REPARENT BIT(7) // Don't change parent when setting rate
#define CLK_GET_ACCURACY_NOCACHE BIT(8) // Always recalculate accuracy
#define CLK_RECALC_NEW_RATES    BIT(9)  // Recalc rates after notifications
#define CLK_SET_RATE_UNGATE     BIT(10) // Clock must be ungated to change rate
#define CLK_IS_CRITICAL         BIT(11) // Never disable, always keep enabled
#define CLK_OPS_PARENT_ENABLE   BIT(12) // Enable parent during ops
```

**Common combinations**:
- `CLK_SET_RATE_GATE`: Clock must be disabled before rate change (most PLLs)
- `CLK_SET_RATE_PARENT`: Pass rate changes to parent (for dividers)
- `CLK_IS_CRITICAL`: Critical infrastructure clocks (never disable)
- `CLK_IGNORE_UNUSED`: Keep enabled even if no consumers

## Implementing Clock Operations

### recalc_rate()

Calculate current clock rate from hardware registers.

```c
/**
 * recalc_rate - Recalculate output rate
 * @hw: Clock hardware structure
 * @parent_rate: Parent clock rate in Hz
 *
 * Returns: Current output rate in Hz
 *
 * Called by framework to determine current clock rate.
 * Read hardware registers and calculate output frequency.
 */
static unsigned long my_pll_recalc_rate(struct clk_hw *hw,
					unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	u32 val, m, n, div;
	u64 rate;

	// Read hardware registers
	val = readl(pll->base + PLL_CONFIG);
	m = (val >> M_SHIFT) & M_MASK;
	n = (val >> N_SHIFT) & N_MASK;
	div = (val >> DIV_SHIFT) & DIV_MASK;

	// Calculate rate: (parent_rate * m) / (n * div)
	rate = (u64)parent_rate * m;
	do_div(rate, n * div);

	return (unsigned long)rate;
}
```

### round_rate()

Find closest achievable rate.

```c
/**
 * round_rate - Find closest achievable rate
 * @hw: Clock hardware structure
 * @rate: Requested rate in Hz
 * @parent_rate: Parent rate (may be modified if CLK_SET_RATE_PARENT)
 *
 * Returns: Closest achievable rate in Hz (or negative errno)
 *
 * Calculate what rate the clock can actually achieve.
 * Does not modify hardware - just calculates.
 */
static long my_pll_round_rate(struct clk_hw *hw, unsigned long rate,
			      unsigned long *parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	unsigned int m, n, div;
	u64 rounded;

	// Calculate best parameters for requested rate
	my_pll_calc_params(pll, *parent_rate, rate, &m, &n, &div);

	// Calculate actual achievable rate
	rounded = (u64)*parent_rate * m;
	do_div(rounded, n * div);

	return (long)rounded;
}
```

### set_rate()

Set clock to specific rate.

```c
/**
 * set_rate - Set clock rate
 * @hw: Clock hardware structure
 * @rate: Desired rate in Hz
 * @parent_rate: Parent clock rate in Hz
 *
 * Returns: 0 on success, negative errno on error
 *
 * Program hardware registers to achieve desired frequency.
 * If CLK_SET_RATE_GATE is set, clock is guaranteed to be disabled.
 */
static int my_pll_set_rate(struct clk_hw *hw, unsigned long rate,
			   unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	unsigned int m, n, div;
	u32 val;

	// Calculate parameters
	my_pll_calc_params(pll, parent_rate, rate, &m, &n, &div);

	if (m == 0 || n == 0 || div == 0)
		return -EINVAL;

	// Program hardware
	val = (m << M_SHIFT) | (n << N_SHIFT) | (div << DIV_SHIFT);
	writel(val, pll->base + PLL_CONFIG);

	// Trigger PLL recalculation/lock
	my_pll_recalculate(pll);

	return 0;
}
```

### enable() and disable()

Gate/ungate clock (atomic operations).

```c
/**
 * enable - Enable clock output (atomic, cannot sleep)
 * @hw: Clock hardware structure
 *
 * Returns: 0 on success, negative errno on error
 *
 * Fast operation to enable clock output.
 * Called with enable_lock spinlock held.
 */
static int my_clk_enable(struct clk_hw *hw)
{
	struct my_clk *clk = to_my_clk(hw);

	// Set enable bit (atomic register write)
	writel(readl(clk->base + CLK_CTRL) | CLK_EN_BIT,
	       clk->base + CLK_CTRL);

	return 0;
}

/**
 * disable - Disable clock output (atomic, cannot sleep)
 * @hw: Clock hardware structure
 *
 * Called with enable_lock spinlock held.
 */
static void my_clk_disable(struct clk_hw *hw)
{
	struct my_clk *clk = to_my_clk(hw);

	// Clear enable bit
	writel(readl(clk->base + CLK_CTRL) & ~CLK_EN_BIT,
	       clk->base + CLK_CTRL);
}

/**
 * is_enabled - Check if clock is enabled
 * @hw: Clock hardware structure
 *
 * Returns: 1 if enabled, 0 if disabled
 */
static int my_clk_is_enabled(struct clk_hw *hw)
{
	struct my_clk *clk = to_my_clk(hw);

	return !!(readl(clk->base + CLK_CTRL) & CLK_EN_BIT);
}
```

### prepare() and unprepare()

Complex operations that may sleep.

```c
/**
 * prepare - Prepare clock for enabling (may sleep)
 * @hw: Clock hardware structure
 *
 * Returns: 0 on success, negative errno on error
 *
 * Perform operations that may sleep (e.g., enabling parent PLLs,
 * waiting for PLL lock). Called with prepare_lock mutex held.
 */
static int my_pll_prepare(struct clk_hw *hw)
{
	struct my_pll *pll = to_my_pll(hw);
	int ret;

	// Power up PLL
	writel(PLL_POWER_ON, pll->base + PLL_POWER);

	// Wait for PLL to lock (may sleep)
	ret = readl_poll_timeout(pll->base + PLL_STATUS,
				 val, val & PLL_LOCKED,
				 10, 1000);
	if (ret) {
		dev_err(pll->dev, "PLL failed to lock\n");
		writel(PLL_POWER_OFF, pll->base + PLL_POWER);
		return ret;
	}

	return 0;
}

/**
 * unprepare - Unprepare clock (may sleep)
 * @hw: Clock hardware structure
 *
 * Called with prepare_lock mutex held.
 */
static void my_pll_unprepare(struct clk_hw *hw)
{
	struct my_pll *pll = to_my_pll(hw);

	// Power down PLL
	writel(PLL_POWER_OFF, pll->base + PLL_POWER);
}
```

### get_parent() and set_parent()

For clock muxes.

```c
/**
 * get_parent - Get current parent index
 * @hw: Clock hardware structure
 *
 * Returns: Current parent index (0 to num_parents-1)
 */
static u8 my_mux_get_parent(struct clk_hw *hw)
{
	struct my_mux *mux = to_my_mux(hw);
	u32 val;

	val = readl(mux->base + MUX_CTRL);
	return (val >> MUX_SHIFT) & MUX_MASK;
}

/**
 * set_parent - Set parent clock
 * @hw: Clock hardware structure
 * @index: Parent index to select
 *
 * Returns: 0 on success, negative errno on error
 */
static int my_mux_set_parent(struct clk_hw *hw, u8 index)
{
	struct my_mux *mux = to_my_mux(hw);
	u32 val;

	val = readl(mux->base + MUX_CTRL);
	val &= ~(MUX_MASK << MUX_SHIFT);
	val |= (index & MUX_MASK) << MUX_SHIFT;
	writel(val, mux->base + MUX_CTRL);

	return 0;
}
```

## Registering Clocks

### Basic Registration

```c
/**
 * devm_clk_hw_register - Register clock with framework
 * @dev: Device structure
 * @hw: Clock hardware structure
 *
 * Returns: 0 on success, negative errno on error
 *
 * Resource-managed - automatically unregistered on driver detach.
 */
static int my_pll_probe(struct platform_device *pdev)
{
	struct my_pll *pll;
	struct clk_init_data init;
	int ret;

	pll = devm_kzalloc(&pdev->dev, sizeof(*pll), GFP_KERNEL);
	if (!pll)
		return -ENOMEM;

	pll->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(pll->base))
		return PTR_ERR(pll->base);

	// Initialize clock description
	init.name = "my_pll";
	init.ops = &my_pll_ops;
	init.parent_names = (const char *[]){ "ref_clk" };
	init.num_parents = 1;
	init.flags = CLK_SET_RATE_GATE;

	pll->hw.init = &init;

	// Register with CCF
	ret = devm_clk_hw_register(&pdev->dev, &pll->hw);
	if (ret)
		return ret;

	return 0;
}
```

### Multiple Clock Registration

```c
static int my_clkgen_probe(struct platform_device *pdev)
{
	struct my_clkgen *clkgen;
	struct clk_hw_onecell_data *clk_data;
	int i, ret;

	clkgen = devm_kzalloc(&pdev->dev, sizeof(*clkgen), GFP_KERNEL);
	if (!clkgen)
		return -ENOMEM;

	clkgen->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(clkgen->base))
		return PTR_ERR(clkgen->base);

	// Allocate clock data for multiple outputs
	clk_data = devm_kzalloc(&pdev->dev,
				struct_size(clk_data, hws, NUM_CLOCKS),
				GFP_KERNEL);
	if (!clk_data)
		return -ENOMEM;

	clk_data->num = NUM_CLOCKS;

	// Register each clock
	for (i = 0; i < NUM_CLOCKS; i++) {
		ret = devm_clk_hw_register(&pdev->dev, &clkgen->clks[i].hw);
		if (ret)
			return ret;

		clk_data->hws[i] = &clkgen->clks[i].hw;
	}

	// Register as provider
	return devm_of_clk_add_hw_provider(&pdev->dev,
					   of_clk_hw_onecell_get,
					   clk_data);
}
```

## Provider Registration

### Simple Provider (One Clock)

```c
/**
 * of_clk_add_hw_provider - Register as devicetree clock provider
 *
 * For single clock output.
 */
ret = of_clk_add_hw_provider(pdev->dev.of_node,
			      of_clk_hw_simple_get,
			      &pll->hw);

// Resource-managed version
ret = devm_of_clk_add_hw_provider(&pdev->dev,
				  of_clk_hw_simple_get,
				  &pll->hw);
```

### Indexed Provider (Multiple Clocks)

```c
/**
 * of_clk_add_hw_provider - Register indexed provider
 *
 * For multiple clock outputs (indexed by #clock-cells).
 */
struct clk_hw_onecell_data *clk_data;

clk_data = devm_kzalloc(dev, struct_size(clk_data, hws, 4), GFP_KERNEL);
clk_data->num = 4;
clk_data->hws[0] = &clk0_hw;
clk_data->hws[1] = &clk1_hw;
clk_data->hws[2] = &clk2_hw;
clk_data->hws[3] = &clk3_hw;

ret = devm_of_clk_add_hw_provider(&pdev->dev,
				  of_clk_hw_onecell_get,
				  clk_data);
```

## Helper Functions

### clk_hw_get_parent()

```c
struct clk_hw *parent_hw = clk_hw_get_parent(hw);
```

Get parent clock hardware structure.

### clk_hw_get_rate()

```c
unsigned long rate = clk_hw_get_rate(hw);
```

Get clock rate from hardware structure.

### clk_hw_round_rate()

```c
long rounded = clk_hw_round_rate(hw, rate);
```

Round rate using hardware structure.

## Complete Provider Example

Simplified PLL implementation:

```c
#include <linux/clk-provider.h>
#include <linux/io.h>
#include <linux/platform_device.h>

struct my_pll {
	void __iomem *base;
	struct clk_hw hw;
	spinlock_t lock;
};

#define to_my_pll(_hw) container_of(_hw, struct my_pll, hw)

static unsigned long my_pll_recalc_rate(struct clk_hw *hw,
					unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	u32 val, m, n;
	u64 rate;

	val = readl(pll->base + PLL_CONFIG);
	m = (val >> 8) & 0xFF;
	n = val & 0xFF;

	if (n == 0)
		return 0;

	rate = (u64)parent_rate * m;
	do_div(rate, n);

	return rate;
}

static long my_pll_round_rate(struct clk_hw *hw, unsigned long rate,
			      unsigned long *parent_rate)
{
	// Simplified: just return requested rate
	return rate;
}

static int my_pll_set_rate(struct clk_hw *hw, unsigned long rate,
			   unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	u32 val, m, n;
	unsigned long flags;

	// Simplified calculation: find m/n for rate
	m = rate / 1000000;
	n = parent_rate / 1000000;

	spin_lock_irqsave(&pll->lock, flags);
	val = (m << 8) | n;
	writel(val, pll->base + PLL_CONFIG);
	spin_unlock_irqrestore(&pll->lock, flags);

	return 0;
}

static const struct clk_ops my_pll_ops = {
	.recalc_rate = my_pll_recalc_rate,
	.round_rate = my_pll_round_rate,
	.set_rate = my_pll_set_rate,
};

static int my_pll_probe(struct platform_device *pdev)
{
	struct my_pll *pll;
	struct clk_init_data init;
	const char *parent_name;
	int ret;

	pll = devm_kzalloc(&pdev->dev, sizeof(*pll), GFP_KERNEL);
	if (!pll)
		return -ENOMEM;

	pll->base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(pll->base))
		return PTR_ERR(pll->base);

	spin_lock_init(&pll->lock);

	parent_name = of_clk_get_parent_name(pdev->dev.of_node, 0);

	init.name = "my_pll";
	init.ops = &my_pll_ops;
	init.parent_names = &parent_name;
	init.num_parents = 1;
	init.flags = CLK_SET_RATE_GATE;

	pll->hw.init = &init;

	ret = devm_clk_hw_register(&pdev->dev, &pll->hw);
	if (ret)
		return ret;

	return devm_of_clk_add_hw_provider(&pdev->dev,
					   of_clk_hw_simple_get,
					   &pll->hw);
}

static const struct of_device_id my_pll_ids[] = {
	{ .compatible = "vendor,my-pll" },
	{ }
};
MODULE_DEVICE_TABLE(of, my_pll_ids);

static struct platform_driver my_pll_driver = {
	.driver = {
		.name = "my-pll",
		.of_match_table = my_pll_ids,
	},
	.probe = my_pll_probe,
};
module_platform_driver(my_pll_driver);
```
