# Clock Types Reference

Complete reference for built-in CCF clock types.

## Fixed-Rate Clock

For oscillators and fixed-frequency sources.

### clk_hw_register_fixed_rate()

```c
struct clk_hw *clk_hw_register_fixed_rate(struct device *dev,
					  const char *name,
					  const char *parent_name,
					  unsigned long flags,
					  unsigned long rate);
```

**Parameters**:
- `dev`: Device (can be NULL)
- `name`: Clock name
- `parent_name`: Parent clock name (can be NULL for root clocks)
- `flags`: Clock flags (usually 0)
- `rate`: Fixed rate in Hz

**Returns**: `struct clk_hw *` or ERR_PTR on error

### Example

```c
struct clk_hw *osc_hw;

// 24 MHz oscillator (root clock, no parent)
osc_hw = clk_hw_register_fixed_rate(NULL, "osc_24mhz", NULL, 0, 24000000);
if (IS_ERR(osc_hw))
	return PTR_ERR(osc_hw);

// Resource-managed version
osc_hw = devm_clk_hw_register_fixed_rate(&pdev->dev, "osc", NULL, 0, 24000000);
```

### Devicetree

```dts
clocks {
	ref_clk: oscillator {
		compatible = "fixed-clock";
		#clock-cells = <0>;
		clock-frequency = <24000000>;
		clock-output-names = "ref_clk";
	};
};
```

## Fixed-Factor Clock

For fixed dividers/multipliers.

### clk_hw_register_fixed_factor()

```c
struct clk_hw *clk_hw_register_fixed_factor(struct device *dev,
					    const char *name,
					    const char *parent_name,
					    unsigned long flags,
					    unsigned int mult,
					    unsigned int div);
```

**Parameters**:
- `mult`: Multiplier
- `div`: Divider

**Formula**: `output_rate = parent_rate * mult / div`

### Example

```c
// PLL divided by 2
struct clk_hw *pll_div2_hw;
pll_div2_hw = clk_hw_register_fixed_factor(NULL, "pll_div2", "pll",
					    0, 1, 2);  // × 1 / 2

// PLL multiplied by 3
struct clk_hw *pll_x3_hw;
pll_x3_hw = clk_hw_register_fixed_factor(NULL, "pll_x3", "pll",
					 0, 3, 1);  // × 3 / 1

// PLL multiplied by 2/3 (e.g., 800 MHz → 533.33 MHz)
struct clk_hw *pll_2_3_hw;
pll_2_3_hw = clk_hw_register_fixed_factor(NULL, "pll_2_3", "pll",
					  CLK_SET_RATE_PARENT, 2, 3);
```

## Gate Clock

For simple on/off control.

### clk_hw_register_gate()

```c
struct clk_hw *clk_hw_register_gate(struct device *dev,
				    const char *name,
				    const char *parent_name,
				    unsigned long flags,
				    void __iomem *reg,
				    u8 bit_idx,
				    u8 clk_gate_flags,
				    spinlock_t *lock);
```

**Parameters**:
- `reg`: Register address
- `bit_idx`: Bit index in register (0-31)
- `clk_gate_flags`: Gate-specific flags
- `lock`: Spinlock for register access (can be NULL)

**Gate flags**:
- `CLK_GATE_SET_TO_DISABLE`: Set bit to disable (inverted logic)
- `CLK_GATE_HIWORD_MASK`: Upper 16 bits are write mask

### Example

```c
struct clk_hw *gate_hw;

// Simple gate: bit 0 in register at base+0x10
gate_hw = clk_hw_register_gate(NULL, "clk_gate", "pll",
			       CLK_SET_RATE_PARENT,
			       base + 0x10,  // Register
			       0,            // Bit 0
			       0,            // Normal logic (set=enable)
			       NULL);        // No shared lock

// Inverted gate: set bit to disable
gate_hw = clk_hw_register_gate(NULL, "clk_gate_inv", "pll",
			       0,
			       base + 0x14,
			       5,  // Bit 5
			       CLK_GATE_SET_TO_DISABLE,
			       &my_lock);

// Hiword mask gate (Rockchip style)
gate_hw = clk_hw_register_gate(NULL, "clk_gate_hiword", "pll",
			       0,
			       base + 0x20,
			       3,
			       CLK_GATE_HIWORD_MASK,
			       NULL);
```

## Divider Clock

For programmable dividers.

### clk_hw_register_divider()

```c
struct clk_hw *clk_hw_register_divider(struct device *dev,
				       const char *name,
				       const char *parent_name,
				       unsigned long flags,
				       void __iomem *reg,
				       u8 shift,
				       u8 width,
				       u8 clk_divider_flags,
				       spinlock_t *lock);
```

**Parameters**:
- `reg`: Register address
- `shift`: Bit position of divider field
- `width`: Width of divider field in bits
- `clk_divider_flags`: Divider-specific flags
- `lock`: Spinlock for register access

**Divider flags**:
- `CLK_DIVIDER_ONE_BASED`: Divider = register_value + 1
- `CLK_DIVIDER_POWER_OF_TWO`: Divider = 2^register_value
- `CLK_DIVIDER_ALLOW_ZERO`: Allow zero divider value
- `CLK_DIVIDER_HIWORD_MASK`: Upper 16 bits are write mask
- `CLK_DIVIDER_ROUND_CLOSEST`: Round to closest divider
- `CLK_DIVIDER_READ_ONLY`: Read-only (fixed divider)

### Example

```c
struct clk_hw *div_hw;

// 3-bit divider (8 values: 1-8)
// Bits 2:0 in register, value+1 encoding
div_hw = clk_hw_register_divider(NULL, "apb_div", "pll",
				 CLK_SET_RATE_PARENT,
				 base + 0x14,  // Register
				 0,            // Shift (bits 0-2)
				 3,            // Width (3 bits = 8 values)
				 CLK_DIVIDER_ONE_BASED,
				 NULL);
// Register value 0 → divide by 1
// Register value 7 → divide by 8

// Power-of-2 divider
div_hw = clk_hw_register_divider(NULL, "div_pow2", "pll",
				 CLK_SET_RATE_PARENT,
				 base + 0x18,
				 8,            // Shift (bits 8-10)
				 3,            // Width (3 bits = 8 values)
				 CLK_DIVIDER_POWER_OF_TWO,
				 NULL);
// Register value 0 → divide by 1
// Register value 1 → divide by 2
// Register value 2 → divide by 4
// Register value 3 → divide by 8

// Read-only divider (fixed by hardware)
div_hw = clk_hw_register_divider(NULL, "fixed_div4", "pll",
				 0,
				 base + 0x1C,
				 0,
				 2,
				 CLK_DIVIDER_READ_ONLY,
				 NULL);
```

## Mux Clock

For clock source selection.

### clk_hw_register_mux()

```c
struct clk_hw *clk_hw_register_mux(struct device *dev,
				   const char *name,
				   const char * const *parent_names,
				   u8 num_parents,
				   unsigned long flags,
				   void __iomem *reg,
				   u8 shift,
				   u8 width,
				   u8 clk_mux_flags,
				   spinlock_t *lock);
```

**Parameters**:
- `parent_names`: Array of parent clock names
- `num_parents`: Number of parents
- `reg`: Register address
- `shift`: Bit position of mux field
- `width`: Width of mux field in bits
- `clk_mux_flags`: Mux-specific flags

**Mux flags**:
- `CLK_MUX_INDEX_ONE`: Parent index 0 = register value 1
- `CLK_MUX_INDEX_BIT`: Parent index = bit position (one-hot encoding)
- `CLK_MUX_HIWORD_MASK`: Upper 16 bits are write mask
- `CLK_MUX_READ_ONLY`: Read-only (fixed mux)
- `CLK_MUX_ROUND_CLOSEST`: Round to closest parent rate

### Example

```c
const char * const mux_parents[] = { "pll0", "pll1", "osc", "ext_clk" };
struct clk_hw *mux_hw;

// 2-bit mux (4 options)
mux_hw = clk_hw_register_mux(NULL, "sys_clk_mux", mux_parents, 4,
			     CLK_SET_RATE_PARENT,
			     base + 0x20,  // Register
			     0,            // Shift (bits 0-1)
			     2,            // Width (2 bits = 4 values)
			     0,            // Normal encoding
			     NULL);
// Register value 0 → pll0
// Register value 1 → pll1
// Register value 2 → osc
// Register value 3 → ext_clk

// One-hot mux (bit position)
const char * const onehot_parents[] = { "clk_a", "clk_b", "clk_c", "clk_d" };
mux_hw = clk_hw_register_mux(NULL, "onehot_mux", onehot_parents, 4,
			     0,
			     base + 0x24,
			     0,
			     4,  // 4 bits for one-hot
			     CLK_MUX_INDEX_BIT,
			     NULL);
// Register value 0x1 (bit 0) → clk_a
// Register value 0x2 (bit 1) → clk_b
// Register value 0x4 (bit 2) → clk_c
// Register value 0x8 (bit 3) → clk_d
```

## Fractional Divider

For fractional division (M/N).

### clk_hw_register_fractional_divider()

```c
struct clk_hw *clk_hw_register_fractional_divider(struct device *dev,
						  const char *name,
						  const char *parent_name,
						  unsigned long flags,
						  void __iomem *reg,
						  u8 mshift, u8 mwidth,
						  u8 nshift, u8 nwidth,
						  u8 clk_divider_flags,
						  spinlock_t *lock);
```

**Parameters**:
- `mshift`, `mwidth`: Position and width of numerator (M)
- `nshift`, `nwidth`: Position and width of denominator (N)

**Formula**: `output_rate = parent_rate * M / N`

### Example

```c
struct clk_hw *frac_div_hw;

// Fractional divider: M in bits 0-7, N in bits 8-15
frac_div_hw = clk_hw_register_fractional_divider(NULL,
						 "frac_div", "pll",
						 CLK_SET_RATE_PARENT,
						 base + 0x30,
						 0, 8,   // M: bits 0-7
						 8, 8,   // N: bits 8-15
						 0,
						 NULL);
```

## Composite Clock

Combining multiple clock types.

### clk_hw_register_composite()

```c
struct clk_hw *clk_hw_register_composite(struct device *dev,
					 const char *name,
					 const char * const *parent_names,
					 int num_parents,
					 struct clk_hw *mux_hw,
					 const struct clk_ops *mux_ops,
					 struct clk_hw *rate_hw,
					 const struct clk_ops *rate_ops,
					 struct clk_hw *gate_hw,
					 const struct clk_ops *gate_ops,
					 unsigned long flags);
```

Combines mux, divider/rate, and gate into single clock.

### Example

```c
struct clk_hw *composite_hw;
struct clk_hw *mux_hw, *div_hw, *gate_hw;
const char * const parents[] = { "pll0", "pll1", "osc" };

// Create individual components (without registering)
mux_hw = clk_hw_register_mux(NULL, NULL, parents, 3, 0,
			     base + 0x00, 0, 2, 0, NULL);

div_hw = clk_hw_register_divider(NULL, NULL, NULL, 0,
				 base + 0x00, 8, 4,
				 CLK_DIVIDER_ONE_BASED, NULL);

gate_hw = clk_hw_register_gate(NULL, NULL, NULL, 0,
			       base + 0x00, 15, 0, NULL);

// Combine into composite
composite_hw = clk_hw_register_composite(&pdev->dev,
					 "output_clk",
					 parents, 3,
					 mux_hw, &clk_mux_ops,
					 div_hw, &clk_divider_ops,
					 gate_hw, &clk_gate_ops,
					 CLK_SET_RATE_PARENT);
```

## Manual Composite Example

Creating composite functionality manually:

```c
static int my_clk_probe(struct platform_device *pdev)
{
	struct clk_hw *mux_hw, *div_hw, *gate_hw;
	const char * const parents[] = { "pll0", "pll1", "osc" };
	void __iomem *base;

	base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(base))
		return PTR_ERR(base);

	// All control in single register at offset 0x00:
	// Bits 0-1: Mux (parent select)
	// Bits 8-11: Divider (4 bits, one-based)
	// Bit 15: Gate (enable)

	// 1. Mux to select source (bits 0-1)
	mux_hw = devm_clk_hw_register_mux(&pdev->dev, "clk_mux",
					  parents, 3,
					  CLK_SET_RATE_PARENT,
					  base + 0x00, 0, 2, 0, NULL);
	if (IS_ERR(mux_hw))
		return PTR_ERR(mux_hw);

	// 2. Divider (bits 8-11)
	div_hw = devm_clk_hw_register_divider(&pdev->dev, "clk_div",
					      "clk_mux",
					      CLK_SET_RATE_PARENT,
					      base + 0x00, 8, 4,
					      CLK_DIVIDER_ONE_BASED, NULL);
	if (IS_ERR(div_hw))
		return PTR_ERR(div_hw);

	// 3. Gate (bit 15)
	gate_hw = devm_clk_hw_register_gate(&pdev->dev, "output_clk",
					    "clk_div",
					    CLK_SET_RATE_PARENT | CLK_IS_CRITICAL,
					    base + 0x00, 15, 0, NULL);
	if (IS_ERR(gate_hw))
		return PTR_ERR(gate_hw);

	// Register final output as provider
	return devm_of_clk_add_hw_provider(&pdev->dev,
					   of_clk_hw_simple_get, gate_hw);
}
```

## PLL Clock

PLLs typically use custom `clk_ops` due to complex locking and configuration.

### Typical PLL Structure

```c
struct my_pll {
	void __iomem *base;
	struct clk_hw hw;
	unsigned int min_rate;
	unsigned int max_rate;
	unsigned int min_vco;
	unsigned int max_vco;
	spinlock_t lock;
};

static const struct clk_ops my_pll_ops = {
	.prepare = my_pll_prepare,      // Power up, wait for lock
	.unprepare = my_pll_unprepare,  // Power down
	.recalc_rate = my_pll_recalc_rate,
	.round_rate = my_pll_round_rate,
	.set_rate = my_pll_set_rate,
};
```

See `reference/provider-api.md` for complete PLL implementation examples.

## Clock Hierarchy Example

Building a complete clock tree:

```c
static int clkgen_probe(struct platform_device *pdev)
{
	struct clk_hw *osc_hw, *pll_hw, *pll_div2_hw;
	struct clk_hw *cpu_mux_hw, *cpu_div_hw, *cpu_gate_hw;
	void __iomem *base;

	base = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(base))
		return PTR_ERR(base);

	// Root: 24 MHz oscillator
	osc_hw = devm_clk_hw_register_fixed_rate(&pdev->dev, "osc",
						 NULL, 0, 24000000);

	// PLL: 800 MHz (custom implementation)
	pll_hw = devm_clk_hw_register_my_pll(&pdev->dev, "pll",
					     "osc", base + 0x00);

	// PLL/2: 400 MHz
	pll_div2_hw = devm_clk_hw_register_fixed_factor(&pdev->dev,
							"pll_div2", "pll",
							0, 1, 2);

	// CPU mux: select between PLL and PLL/2
	const char * const cpu_parents[] = { "pll", "pll_div2" };
	cpu_mux_hw = devm_clk_hw_register_mux(&pdev->dev, "cpu_mux",
					      cpu_parents, 2,
					      CLK_SET_RATE_PARENT,
					      base + 0x10, 0, 1, 0, NULL);

	// CPU divider: 1-8
	cpu_div_hw = devm_clk_hw_register_divider(&pdev->dev, "cpu_div",
						  "cpu_mux",
						  CLK_SET_RATE_PARENT,
						  base + 0x10, 8, 3,
						  CLK_DIVIDER_ONE_BASED, NULL);

	// CPU gate
	cpu_gate_hw = devm_clk_hw_register_gate(&pdev->dev, "cpu_clk",
						"cpu_div",
						CLK_SET_RATE_PARENT | CLK_IS_CRITICAL,
						base + 0x10, 15, 0, NULL);

	// Register CPU clock as provider
	return devm_of_clk_add_hw_provider(&pdev->dev,
					   of_clk_hw_simple_get,
					   cpu_gate_hw);
}
```

**Resulting clock tree**:
```
osc (24 MHz)
 └─ pll (800 MHz)
     ├─ pll_div2 (400 MHz)
     └─ cpu_mux (select pll or pll_div2)
         └─ cpu_div (divide by 1-8)
             └─ cpu_clk (final output with gate)
```

## Choosing Clock Type

| Hardware Feature | Clock Type | Notes |
|-----------------|------------|-------|
| Oscillator, fixed frequency | Fixed-rate | Root clocks |
| Fixed divider (/2, /4) | Fixed-factor | div=2, div=4 |
| Fixed multiplier (×2, ×3) | Fixed-factor | mult=2, mult=3 |
| Enable/disable gate | Gate | Simple on/off |
| Programmable divider | Divider | Variable division |
| Clock mux/selector | Mux | Parent selection |
| Fractional divider | Fractional divider | M/N division |
| PLL with configuration | Custom ops | Complex logic |
| Multiple features in one register | Composite | Combines mux+div+gate |
