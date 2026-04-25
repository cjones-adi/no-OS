# Devicetree Bindings Reference

Complete reference for clock devicetree integration.

## Clock Provider Binding

### YAML Schema Example

```yaml
# Documentation/devicetree/bindings/clock/vendor,my-pll.yaml
%YAML 1.2
---
$id: http://devicetree.org/schemas/clock/vendor,my-pll.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Vendor My-PLL Clock Generator

maintainers:
  - Your Name <your.email@example.com>

description: |
  The My-PLL is a configurable PLL clock generator that produces
  an output clock from a reference input. The PLL supports output
  frequencies from 100 MHz to 1.6 GHz.

properties:
  compatible:
    const: vendor,my-pll

  reg:
    maxItems: 1

  clocks:
    description: Reference clock input
    maxItems: 1

  clock-names:
    items:
      - const: ref

  '#clock-cells':
    description: Number of cells in clock specifier
    const: 0

  clock-output-names:
    description: Name of output clock
    maxItems: 1

  vendor,vco-min:
    description: Minimum VCO frequency in Hz
    $ref: /schemas/types.yaml#/definitions/uint32
    default: 800000000

  vendor,vco-max:
    description: Maximum VCO frequency in Hz
    $ref: /schemas/types.yaml#/definitions/uint32
    default: 1600000000

required:
  - compatible
  - reg
  - clocks
  - '#clock-cells'

additionalProperties: false

examples:
  - |
    pll@40000000 {
        compatible = "vendor,my-pll";
        reg = <0x40000000 0x1000>;
        clocks = <&ref_clk>;
        clock-names = "ref";
        #clock-cells = <0>;
        clock-output-names = "pll_out";
        vendor,vco-min = <800000000>;
        vendor,vco-max = <1600000000>;
    };
```

### Validation

```bash
# Validate schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/clock/vendor,my-pll.yaml

# Validate devicetree against schema
make dtbs_check DT_SCHEMA_FILES=vendor,my-pll
```

## Simple Provider (One Clock)

### Devicetree Node

```dts
ref_clk: oscillator {
	compatible = "fixed-clock";
	#clock-cells = <0>;
	clock-frequency = <24000000>;
	clock-output-names = "ref_clk";
};

pll: pll@40000000 {
	compatible = "vendor,my-pll";
	reg = <0x40000000 0x1000>;
	clocks = <&ref_clk>;
	clock-names = "ref";
	#clock-cells = <0>;
	clock-output-names = "pll_out";
};
```

**Key properties**:
- `#clock-cells = <0>`: No index required (single clock output)
- `clock-output-names`: Optional name for the clock

### Provider Implementation

```c
static int my_pll_probe(struct platform_device *pdev)
{
	struct my_pll *pll;
	// ... initialization ...

	// Register as simple provider
	return devm_of_clk_add_hw_provider(&pdev->dev,
					   of_clk_hw_simple_get,
					   &pll->hw);
}
```

### Consumer Usage

```dts
my_device {
	compatible = "vendor,my-device";
	clocks = <&pll>;  // Reference by phandle
	clock-names = "core";
};
```

## Indexed Provider (Multiple Clocks)

### Devicetree Node

```dts
clkgen: clock-generator@50000000 {
	compatible = "vendor,clkgen";
	reg = <0x50000000 0x1000>;
	clocks = <&ref_clk>;
	clock-names = "ref";
	#clock-cells = <1>;  // Index required
	clock-output-names = "clk0", "clk1", "clk2", "clk3";
};
```

**Key properties**:
- `#clock-cells = <1>`: One cell required (clock index)
- `clock-output-names`: Names for each indexed clock (optional)

### Provider Implementation

```c
static int clkgen_probe(struct platform_device *pdev)
{
	struct clkgen *gen;
	struct clk_hw_onecell_data *clk_data;
	int i;

	// ... initialization ...

	// Allocate indexed clock data
	clk_data = devm_kzalloc(&pdev->dev,
				struct_size(clk_data, hws, NUM_CLOCKS),
				GFP_KERNEL);
	if (!clk_data)
		return -ENOMEM;

	clk_data->num = NUM_CLOCKS;

	// Register each clock
	for (i = 0; i < NUM_CLOCKS; i++) {
		// ... register clock i ...
		clk_data->hws[i] = &gen->clks[i].hw;
	}

	// Register as indexed provider
	return devm_of_clk_add_hw_provider(&pdev->dev,
					   of_clk_hw_onecell_get,
					   clk_data);
}
```

### Consumer Usage

```dts
my_device {
	compatible = "vendor,my-device";
	clocks = <&clkgen 0>, <&clkgen 2>;  // Index 0 and 2
	clock-names = "core", "ref";
};
```

## Clock Consumer Binding

### Simple Consumer

```dts
my_device {
	compatible = "vendor,my-device";
	clocks = <&pll>;
	clock-names = "core";
};
```

**Driver code**:
```c
clk = devm_clk_get(&pdev->dev, "core");
```

### Multiple Clocks

```dts
my_device {
	compatible = "vendor,my-device";
	clocks = <&clkgen 0>, <&ref_clk>, <&clkgen 2>;
	clock-names = "core", "bus", "ref";
};
```

**Driver code**:
```c
core_clk = devm_clk_get(&pdev->dev, "core");
bus_clk = devm_clk_get(&pdev->dev, "bus");
ref_clk = devm_clk_get(&pdev->dev, "ref");

// Or use bulk API
struct clk_bulk_data clks[] = {
	{ .id = "core" },
	{ .id = "bus" },
	{ .id = "ref" },
};
ret = devm_clk_bulk_get(&pdev->dev, ARRAY_SIZE(clks), clks);
```

### Optional Clocks

```dts
my_device {
	compatible = "vendor,my-device";
	clocks = <&clkgen 0>;  // Only core clock
	clock-names = "core";
	// "ref" clock is optional, not specified
};
```

**Driver code**:
```c
core_clk = devm_clk_get(&pdev->dev, "core");  // Required
if (IS_ERR(core_clk))
	return PTR_ERR(core_clk);

ref_clk = devm_clk_get_optional(&pdev->dev, "ref");  // Optional
if (IS_ERR(ref_clk))
	return PTR_ERR(ref_clk);

if (ref_clk) {
	// Use external reference
} else {
	// Use internal reference
}
```

## Fixed Clock Binding

```dts
clocks {
	ref_clk: oscillator {
		compatible = "fixed-clock";
		#clock-cells = <0>;
		clock-frequency = <24000000>;
		clock-output-names = "ref_clk";
	};

	osc_32k: oscillator-32k {
		compatible = "fixed-clock";
		#clock-cells = <0>;
		clock-frequency = <32768>;
		clock-output-names = "osc_32k";
	};
};
```

**No driver needed** - handled by `of_fixed_clk_setup()`.

## Clock Hierarchy Example

```dts
clocks {
	// Root: 24 MHz oscillator
	ref_clk: oscillator {
		compatible = "fixed-clock";
		#clock-cells = <0>;
		clock-frequency = <24000000>;
	};
};

// PLL: ref_clk → 800 MHz
pll: pll@40000000 {
	compatible = "vendor,pll";
	reg = <0x40000000 0x1000>;
	clocks = <&ref_clk>;
	clock-names = "ref";
	#clock-cells = <0>;
};

// Clock generator: PLL → multiple outputs
clkgen: clock-generator@50000000 {
	compatible = "vendor,clkgen";
	reg = <0x50000000 0x1000>;
	clocks = <&pll>;
	clock-names = "pll";
	#clock-cells = <1>;
	clock-output-names = "cpu_clk", "bus_clk", "periph_clk", "apb_clk";
};

// Device consumers
cpu {
	compatible = "arm,cortex-a9";
	clocks = <&clkgen 0>;  // cpu_clk
	clock-names = "cpu";
};

uart@60000000 {
	compatible = "vendor,uart";
	reg = <0x60000000 0x1000>;
	clocks = <&clkgen 3>;  // apb_clk
	clock-names = "apb_pclk";
};

i2c@61000000 {
	compatible = "vendor,i2c";
	reg = <0x61000000 0x1000>;
	clocks = <&clkgen 3>;  // apb_clk
	clock-names = "pclk";
};
```

## Clock Flags (Consumer)

Clocks can have flags specified in devicetree (not commonly used):

```dts
my_device {
	clocks = <&clkgen 0>;
	clock-names = "core";
	assigned-clocks = <&clkgen 0>;
	assigned-clock-rates = <100000000>;  // Set to 100 MHz at boot
};
```

## Assigned Clocks

Set clock rates and parents at boot time:

```dts
&clkgen {
	assigned-clocks = <&clkgen 0>, <&clkgen 1>;
	assigned-clock-rates = <800000000>, <400000000>;
};

// Or in consumer
my_device {
	clocks = <&clkgen 0>;
	assigned-clocks = <&clkgen 0>;
	assigned-clock-rates = <100000000>;
	assigned-clock-parents = <&pll>;
};
```

## Getting Clock Names in Driver

### From devicetree

```c
// Get clock name from DT property
const char *clk_name;
ret = of_property_read_string(np, "clock-output-names", &clk_name);
if (ret)
	clk_name = np->name;  // Fallback to node name
```

### Parent Clock Names

```c
// Get parent clock name
const char *parent_name;
parent_name = of_clk_get_parent_name(np, 0);  // First parent

// For multiple parents
const char *parent_names[MAX_PARENTS];
int num_parents;

num_parents = of_clk_get_parent_count(np);
for (i = 0; i < num_parents; i++)
	parent_names[i] = of_clk_get_parent_name(np, i);
```

## Real-World Examples

### ADI AXI CLKGEN

```dts
axi_clkgen: axi-clkgen@43c00000 {
	compatible = "adi,axi-clkgen-2.00.a";
	reg = <0x43c00000 0x1000>;
	clocks = <&clk0_ad9361>;
	#clock-cells = <0>;
	clock-output-names = "axi_clkgen";
};

axi_ad9361: axi-ad9361@79020000 {
	compatible = "adi,axi-ad9361-1.00.a";
	reg = <0x79020000 0x6000>;
	clocks = <&axi_clkgen>;  // Use generated clock
};
```

### Clock Gating Controller

```dts
clock-controller@1000 {
	compatible = "vendor,clk-gate";
	reg = <0x1000 0x100>;
	#clock-cells = <1>;
	clock-output-names = "gate0", "gate1", "gate2", "gate3";
	clocks = <&pll>, <&pll>, <&pll>, <&pll>;
	clock-names = "gate0", "gate1", "gate2", "gate3";
};
```

## Common Properties

| Property | Type | Description |
|----------|------|-------------|
| `clocks` | phandle + cells | Parent clock reference(s) |
| `clock-names` | string array | Names for parent clocks |
| `#clock-cells` | u32 | Number of cells in consumer specifier |
| `clock-output-names` | string array | Names for output clocks |
| `clock-frequency` | u32 | Fixed clock frequency (Hz) |
| `assigned-clocks` | phandle + cells | Clocks to configure at boot |
| `assigned-clock-rates` | u32 array | Rates for assigned clocks |
| `assigned-clock-parents` | phandle + cells | Parents for assigned clocks |

## Debugging Devicetree Clocks

### Check parsed clocks

```bash
# View clock tree from devicetree
cat /sys/kernel/debug/clk/clk_summary

# Check device clocks
ls -l /sys/devices/.../clk:*
```

### Common Issues

**Clock not found**:
```dts
// Wrong
clocks = <&clkgen>;  // Missing index for indexed provider
clock-names = "wrong_name";  // Doesn't match driver

// Correct
clocks = <&clkgen 0>;
clock-names = "core";  // Matches devm_clk_get(dev, "core")
```

**Circular dependency**:
```dts
// Wrong - circular
clk_a {
	clocks = <&clk_b>;
};
clk_b {
	clocks = <&clk_a>;  // Circular!
};
```

**Missing #clock-cells**:
```dts
// Wrong - provider missing #clock-cells
my_pll {
	compatible = "vendor,pll";
	// Missing: #clock-cells = <0>;
};

// Correct
my_pll {
	compatible = "vendor,pll";
	#clock-cells = <0>;
};
```

## Parent Specification Methods

### Method 1: parent_names (legacy)

```c
static const char * const pll_parents[] = { "ref_clk", "osc" };

init.parent_names = pll_parents;
init.num_parents = ARRAY_SIZE(pll_parents);
```

### Method 2: parent_data (preferred)

```c
static const struct clk_parent_data pll_parents[] = {
	{ .fw_name = "ref" },
	{ .fw_name = "osc" },
};

init.parent_data = pll_parents;
init.num_parents = ARRAY_SIZE(pll_parents);
```

### Method 3: parent_hws (internal clocks)

```c
static const struct clk_hw *pll_parents[] = {
	&ref_clk_hw,
	&osc_hw,
};

init.parent_hws = pll_parents;
init.num_parents = ARRAY_SIZE(pll_parents);
```

**Devicetree** (for methods 1 and 2):
```dts
pll {
	clocks = <&ref_clk>, <&osc>;
	clock-names = "ref", "osc";
};
```
