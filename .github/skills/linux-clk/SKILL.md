---
name: linux-clk
description: Complete guide to Linux Common Clock Framework (CCF) for clock providers and consumers. Use when implementing clock controller drivers or using clocks in device drivers.
metadata:
  version: "2.0"
  platform: linux
  category: subsystem
  subsystem: clk
  tags:
    - clk
    - clock
    - pll
    - divider
    - mux
    - gate
    - clock-controller
    - clock-consumer
    - ccf
  dependencies:
    - linux-devicetree
    - linux-kconfig-makefile
  learning_objectives:
    - Implement clock provider drivers (PLLs, dividers, muxes, gates)
    - Use descriptor-based clock consumer API (clk_* functions)
    - Calculate PLL parameters for frequency synthesis
    - Work with clock hierarchies and parent-child relationships
    - Configure clock flags and constraints
    - Register devicetree clock providers
    - Debug clock issues with debugfs
---

# Linux Common Clock Framework (CCF)

Quick-start guide for implementing clock controller drivers and using clocks in device drivers.

## For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/consumer-api.md**:
- User mentions: "use clock", "clk_get", "clk_enable", "clk_set_rate", "consumer driver"
- Questions about: clk_prepare_enable, clk_disable_unprepare, clk_round_rate, clk_get_rate
- User asks: "how to use clock in driver", "enable clock", "set clock rate", "get clock"
- Topics: devm_clk_get, devm_clk_get_optional, devm_clk_get_enabled, clk_bulk_get

**Triggers to read reference/provider-api.md**:
- User mentions: "implement clock controller", "clock driver", "clk_hw", "clk_ops", "PLL driver"
- Questions about: recalc_rate, round_rate, set_rate, prepare, enable, disable callbacks
- User asks: "how to implement", "create clock driver", "register clock provider"
- Topics: struct clk_hw, struct clk_init_data, struct clk_ops, devm_clk_hw_register

**Triggers to read reference/clock-types.md**:
- User mentions: "fixed-rate", "fixed-factor", "gate", "divider", "mux", "composite", "PLL"
- Questions about: clk_hw_register_fixed_rate, clk_hw_register_gate, clk_hw_register_divider
- User asks: "what clock type", "built-in clocks", "clock hierarchy", "clock tree"
- Topics: oscillator, fixed divider, programmable divider, clock mux, gate clock

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "DTS", "#clock-cells", "clock-output-names"
- Questions about: clock provider binding, clock consumer binding, assigned-clocks
- User asks: "devicetree example", "YAML schema", "how to specify clock in DT"
- Topics: of_clk_add_hw_provider, clock-names, clocks property, indexed provider

**Triggers to read reference/debugging.md**:
- User mentions: "debug", "not working", "clock stuck", "wrong rate", "clock disabled"
- Questions about: clk_summary, debugfs, clock tree, enable count, prepare count
- User says: "troubleshoot", "diagnose", "clock error", "rate change fails"
- Topics: /sys/kernel/debug/clk, dynamic debug, ftrace, common issues

---

## When to Use This Skill

- Implementing clock controller drivers for SoC clock blocks or clock generators
- Using clocks in device drivers (PLLs, dividers, reference clocks)
- Calculating PLL parameters for frequency synthesis
- Working with clock hierarchies and parent-child relationships
- Debugging clock controller or consumer issues

## What is the Linux Common Clock Framework?

The Linux CCF provides infrastructure for:
- **Clock Providers** (controllers): Drivers that control clock hardware
- **Clock Consumers** (devices): Device drivers that use clocks

### Two-Sided API

```
┌─────────────────────────────────────────────────────────────┐
│                    Clock Consumer Drivers                    │
│            (Device drivers using clocks)                     │
│                                                              │
│  clk_get(), clk_set_rate(), clk_prepare_enable()           │
└──────────────────────┬──────────────────────────────────────┘
                       │ Consumer API
┌──────────────────────▼──────────────────────────────────────┐
│                     Clock Core                               │
│         (CCF in drivers/clk/clk.c)                          │
│                                                              │
│  - Reference counting                                        │
│  - Rate calculation and propagation                          │
│  - Parent-child relationships                                │
│  - Notification chains                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ Provider API
┌──────────────────────▼──────────────────────────────────────┐
│                  Clock Provider Drivers                      │
│       (Clock controllers: PLLs, dividers, muxes)            │
│                                                              │
│  clk_hw_register(), clk_ops callbacks                       │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start: Clock Consumer

### Basic Usage

```c
#include <linux/clk.h>

struct my_device {
	struct device *dev;
	struct clk *clk;
};

static int my_probe(struct platform_device *pdev)
{
	struct my_device *mydev;
	int ret;

	mydev = devm_kzalloc(&pdev->dev, sizeof(*mydev), GFP_KERNEL);
	if (!mydev)
		return -ENOMEM;

	// Get clock
	mydev->clk = devm_clk_get(&pdev->dev, "core");
	if (IS_ERR(mydev->clk))
		return PTR_ERR(mydev->clk);

	// Enable clock
	ret = clk_prepare_enable(mydev->clk);
	if (ret)
		return ret;

	// Get rate
	unsigned long rate = clk_get_rate(mydev->clk);
	dev_info(&pdev->dev, "Clock rate: %lu Hz\n", rate);

	return 0;
}

static void my_remove(struct platform_device *pdev)
{
	struct my_device *mydev = platform_get_drvdata(pdev);

	clk_disable_unprepare(mydev->clk);
}
```

**Devicetree**:
```dts
my_device {
	compatible = "vendor,my-device";
	clocks = <&clkgen 0>;
	clock-names = "core";
};
```

### Consumer API Summary

| Function | Purpose | Context |
|----------|---------|---------|
| `devm_clk_get()` | Get clock by name | Non-atomic |
| `devm_clk_get_optional()` | Get optional clock (NULL if missing) | Non-atomic |
| `devm_clk_get_enabled()` | Get and enable in one call | Non-atomic |
| `clk_prepare_enable()` | Prepare and enable clock | Non-atomic |
| `clk_disable_unprepare()` | Disable and unprepare clock | Non-atomic |
| `clk_get_rate()` | Get current rate in Hz | Any |
| `clk_set_rate()` | Set rate in Hz | Non-atomic |
| `clk_round_rate()` | Find closest achievable rate | Any |

## Quick Start: Clock Provider

### Basic PLL Provider

```c
#include <linux/clk-provider.h>

struct my_pll {
	void __iomem *base;
	struct clk_hw hw;
};

#define to_my_pll(_hw) container_of(_hw, struct my_pll, hw)

static unsigned long my_pll_recalc_rate(struct clk_hw *hw,
					unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	u32 val, m, n;

	val = readl(pll->base + PLL_CONFIG);
	m = (val >> 8) & 0xFF;
	n = val & 0xFF;

	if (n == 0)
		return 0;

	return (parent_rate * m) / n;
}

static long my_pll_round_rate(struct clk_hw *hw, unsigned long rate,
			      unsigned long *parent_rate)
{
	// Calculate closest achievable rate
	// (simplified - see reference/provider-api.md for full implementation)
	return rate;
}

static int my_pll_set_rate(struct clk_hw *hw, unsigned long rate,
			   unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	unsigned int m, n;

	// Calculate m and n for desired rate
	m = rate / 1000000;
	n = parent_rate / 1000000;

	writel((m << 8) | n, pll->base + PLL_CONFIG);

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

**Devicetree**:
```dts
ref_clk: oscillator {
	compatible = "fixed-clock";
	#clock-cells = <0>;
	clock-frequency = <24000000>;
};

pll: pll@40000000 {
	compatible = "vendor,my-pll";
	reg = <0x40000000 0x1000>;
	clocks = <&ref_clk>;
	#clock-cells = <0>;
	clock-output-names = "pll_out";
};
```

### Provider API Summary

| Component | Purpose |
|-----------|---------|
| `struct clk_hw` | Hardware clock structure (embed in driver struct) |
| `struct clk_init_data` | Initialization data (name, ops, parents, flags) |
| `struct clk_ops` | Hardware operations (recalc_rate, set_rate, enable, etc.) |
| `devm_clk_hw_register()` | Register clock with framework |
| `devm_of_clk_add_hw_provider()` | Register as devicetree provider |

## CCF Architecture

### Two-Half Design

1. **Common Layer** (`struct clk_core`):
   - Framework-level accounting and infrastructure
   - Clock topology management (parent-child relationships)
   - Reference counting and notification

2. **Hardware Layer** (`struct clk_ops`):
   - Device-specific operations (enable, set_rate, etc.)
   - Hardware register manipulation

3. **Bridge** (`struct clk_hw`):
   - Connects common and hardware layers
   - Used in `container_of()` patterns

### Locking Strategy

**Enable Lock** (spinlock):
- Protects: `.enable()` / `.disable()` / `.is_enabled()`
- Characteristics: Non-sleeping, atomic-context safe

**Prepare Lock** (mutex):
- Protects: All other operations (`.prepare()`, `.set_rate()`, etc.)
- Characteristics: Allows sleeping, requires non-atomic context

## Built-in Clock Types

The CCF provides pre-built clock types for common hardware patterns.

### Fixed-Rate Clock

For oscillators and fixed-frequency sources:

```c
struct clk_hw *osc_hw;

osc_hw = devm_clk_hw_register_fixed_rate(&pdev->dev, "osc_24mhz",
					 NULL, 0, 24000000);
```

### Fixed-Factor Clock

For fixed dividers/multipliers:

```c
// PLL divided by 2
struct clk_hw *pll_div2_hw;
pll_div2_hw = clk_hw_register_fixed_factor(NULL, "pll_div2", "pll",
					    0, 1, 2);  // × 1 / 2
```

### Gate Clock

For simple on/off control:

```c
struct clk_hw *gate_hw;
gate_hw = clk_hw_register_gate(NULL, "clk_gate", "pll",
			       CLK_SET_RATE_PARENT,
			       base + 0x10,  // Register
			       0,            // Bit 0
			       0, NULL);
```

### Divider Clock

For programmable dividers:

```c
struct clk_hw *div_hw;
div_hw = clk_hw_register_divider(NULL, "apb_div", "pll",
				 CLK_SET_RATE_PARENT,
				 base + 0x14,  // Register
				 0,            // Shift (bits 0-2)
				 3,            // Width (8 values: 1-8)
				 CLK_DIVIDER_ONE_BASED, NULL);
```

### Mux Clock

For clock source selection:

```c
const char * const parents[] = { "pll0", "pll1", "osc" };
struct clk_hw *mux_hw;

mux_hw = clk_hw_register_mux(NULL, "sys_clk_mux", parents, 3,
			     CLK_SET_RATE_PARENT,
			     base + 0x20,  // Register
			     0,            // Shift
			     2,            // Width (4 options)
			     0, NULL);
```

## Clock Flags

Common flags for clock configuration:

```c
#define CLK_SET_RATE_GATE       BIT(0)  // Clock must be gated to change rate
#define CLK_SET_PARENT_GATE     BIT(1)  // Clock must be gated to change parent
#define CLK_SET_RATE_PARENT     BIT(2)  // Propagate rate changes to parent
#define CLK_IGNORE_UNUSED       BIT(3)  // Don't disable if unused
#define CLK_GET_RATE_NOCACHE    BIT(6)  // Always recalculate rate
#define CLK_IS_CRITICAL         BIT(11) // Never disable, always keep enabled
```

## Devicetree Integration

### Simple Provider (One Clock)

```dts
pll: pll@40000000 {
	compatible = "vendor,my-pll";
	reg = <0x40000000 0x1000>;
	clocks = <&ref_clk>;
	#clock-cells = <0>;  // No index required
	clock-output-names = "pll_out";
};
```

**Driver registration**:
```c
return devm_of_clk_add_hw_provider(&pdev->dev,
				   of_clk_hw_simple_get,
				   &pll->hw);
```

### Indexed Provider (Multiple Clocks)

```dts
clkgen: clock-generator@50000000 {
	compatible = "vendor,clkgen";
	reg = <0x50000000 0x1000>;
	clocks = <&ref_clk>;
	#clock-cells = <1>;  // Index required
	clock-output-names = "clk0", "clk1", "clk2", "clk3";
};
```

**Driver registration**:
```c
struct clk_hw_onecell_data *clk_data;

clk_data = devm_kzalloc(dev, struct_size(clk_data, hws, 4), GFP_KERNEL);
clk_data->num = 4;
clk_data->hws[0] = &clk0_hw;
clk_data->hws[1] = &clk1_hw;
clk_data->hws[2] = &clk2_hw;
clk_data->hws[3] = &clk3_hw;

return devm_of_clk_add_hw_provider(&pdev->dev,
				   of_clk_hw_onecell_get,
				   clk_data);
```

### Consumer Usage

```dts
my_device {
	compatible = "vendor,my-device";
	clocks = <&clkgen 0>, <&ref_clk>;
	clock-names = "core", "ref";
};
```

**Driver code**:
```c
core_clk = devm_clk_get(&pdev->dev, "core");
ref_clk = devm_clk_get(&pdev->dev, "ref");
```

## PLL Parameter Calculation

Typical PLL formula: `output = (input / D) * M / DOUT`

Where:
- **D**: Input divider (pre-divider)
- **M**: Feedback multiplier
- **DOUT**: Output divider

### Constraints

- `fpfd_min <= input/D <= fpfd_max` (PFD input range)
- `fvco_min <= VCO <= fvco_max` (VCO output range)
- `1 <= D <= D_max`
- `1 <= M <= M_max`
- `1 <= DOUT <= DOUT_max`

### Calculation Algorithm

```c
static void calc_pll_params(unsigned long fin, unsigned long fout,
			    unsigned int *d, unsigned int *m,
			    unsigned int *dout)
{
	unsigned long d_min, d_max, m_min, m_max;
	unsigned long best_f = ULONG_MAX;

	// Calculate D range based on PFD limits
	d_min = max_t(unsigned long, DIV_ROUND_UP(fin, fpfd_max), 1);
	d_max = min_t(unsigned long, fin / fpfd_min, D_MAX);

	// Calculate M range based on VCO limits
	m_min = max_t(unsigned long,
		      DIV_ROUND_UP(fvco_min, fin) * d_min, 1);
	m_max = min_t(unsigned long,
		      fvco_max * d_max / fin, M_MAX);

	// Try all valid D and M combinations
	for (m = m_min; m <= m_max; m++) {
		for (d = d_min; d <= d_max; d++) {
			fvco = fin * m / d;

			if (fvco < fvco_min || fvco > fvco_max)
				continue;

			dout_calc = DIV_ROUND_CLOSEST(fvco, fout);
			dout_calc = clamp_t(unsigned long,
					    dout_calc, 1, DOUT_MAX);

			f = fvco / dout_calc;

			if (abs(f - fout) < abs(best_f - fout)) {
				best_f = f;
				*d = d;
				*m = m;
				*dout = dout_calc;
			}
		}
	}
}
```

## Debugging

### Clock Tree

```bash
# View complete clock tree
cat /sys/kernel/debug/clk/clk_summary

# Example output:
   clock                         enable_cnt  prepare_cnt  rate
----------------------------------------------------------------
 ref_clk                         1           1            24000000
    pll                          2           2            800000000
       cpu_clk                   1           1            800000000
       apb_div                   1           1            100000000
```

### Specific Clock

```bash
# Clock rate
cat /sys/kernel/debug/clk/pll/clk_rate

# Enable count
cat /sys/kernel/debug/clk/pll/clk_enable_count

# Parent
cat /sys/kernel/debug/clk/pll/clk_parent

# Flags
cat /sys/kernel/debug/clk/pll/clk_flags
```

### Enable Debugging

```kconfig
CONFIG_COMMON_CLK=y
CONFIG_DEBUG_FS=y
CONFIG_COMMON_CLK_DEBUG=y
```

### Dynamic Debug

```bash
# Enable clock framework debug
echo "file drivers/clk/* +p" > /sys/kernel/debug/dynamic_debug/control

# View messages
dmesg | grep clk
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
	st->rate = INTERNAL_CLOCK_RATE;
}
```

### Multiple Clocks (Bulk API)

```c
struct clk_bulk_data clks[] = {
	{ .id = "core" },
	{ .id = "bus" },
	{ .id = "ref" },
};

ret = devm_clk_bulk_get(&pdev->dev, ARRAY_SIZE(clks), clks);
if (ret)
	return ret;

ret = clk_bulk_prepare_enable(ARRAY_SIZE(clks), clks);
if (ret)
	return ret;
```

### Rate Change with Disable

```c
// Some clocks require CLK_SET_RATE_GATE
clk_disable_unprepare(clk);
ret = clk_set_rate(clk, new_rate);
clk_prepare_enable(clk);
```

## Real-World Example: ADI AXI CLKGEN

From `drivers/clk/clk-axi-clkgen.c`:

```c
struct axi_clkgen {
	void __iomem *base;
	struct clk_hw clk_hw;
	unsigned int fpfd_min;
	unsigned int fpfd_max;
	unsigned int fvco_min;
	unsigned int fvco_max;
};

#define to_axi_clkgen(_hw) container_of(_hw, struct axi_clkgen, clk_hw)

// Calculates PLL parameters (D, M, DOUT) for desired frequency
static void axi_clkgen_calc_params(struct axi_clkgen *clkgen,
				   unsigned long fin, unsigned long fout,
				   unsigned int *best_d,
				   unsigned int *best_m,
				   unsigned int *best_dout);

static unsigned long axi_clkgen_recalc_rate(struct clk_hw *hw,
					    unsigned long parent_rate);

static long axi_clkgen_round_rate(struct clk_hw *hw, unsigned long rate,
				  unsigned long *parent_rate);

static int axi_clkgen_set_rate(struct clk_hw *hw, unsigned long rate,
			       unsigned long parent_rate);

static const struct clk_ops axi_clkgen_ops = {
	.recalc_rate = axi_clkgen_recalc_rate,
	.round_rate = axi_clkgen_round_rate,
	.set_rate = axi_clkgen_set_rate,
};
```

**Devicetree**:
```dts
axi_clkgen: axi-clkgen@43c00000 {
	compatible = "adi,axi-clkgen-2.00.a";
	reg = <0x43c00000 0x1000>;
	clocks = <&clk0_ad9361>;
	#clock-cells = <0>;
	clock-output-names = "axi_clkgen";
};
```

## Related Skills

- **linux-devicetree**: Clock devicetree bindings
- **linux-regulator**: Often used together with clocks for power management
- **linux-kconfig-makefile**: Adding clock drivers to build system
