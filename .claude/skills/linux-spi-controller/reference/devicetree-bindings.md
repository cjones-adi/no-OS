# SPI Controller Devicetree Bindings

Guide for creating devicetree bindings for SPI controllers and understanding SPI controller DT properties.

## SPI Controller Node

Basic SPI controller devicetree node:

```dts
spi0: spi@40000000 {
	compatible = "vendor,my-spi";
	reg = <0x40000000 0x1000>;
	interrupts = <GIC_SPI 50 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clk_spi0>;
	clock-names = "spi_clk";

	/* Standard SPI controller properties */
	#address-cells = <1>;
	#size-cells = <0>;
	num-cs = <4>;

	/* Optional DMA */
	dmas = <&dma0 0>, <&dma0 1>;
	dma-names = "tx", "rx";

	status = "okay";
};
```

## Required Properties

| Property | Description |
|----------|-------------|
| `compatible` | Device-specific string (e.g., "adi,axi-spi-engine-1.00.a") |
| `reg` | Register base address and size |
| `#address-cells` | Must be `<1>` (chip select number) |
| `#size-cells` | Must be `<0>` (no size for SPI devices) |

## Optional Properties

| Property | Description | Example |
|----------|-------------|---------|
| `num-cs` | Number of chip select lines | `num-cs = <4>;` |
| `interrupts` | Interrupt specification | `interrupts = <GIC_SPI 50 IRQ_TYPE_LEVEL_HIGH>;` |
| `clocks` | Clock phandles | `clocks = <&clk_spi0>;` |
| `clock-names` | Clock names | `clock-names = "spi_clk";` |
| `dmas` | DMA channel phandles | `dmas = <&dma0 0>, <&dma0 1>;` |
| `dma-names` | DMA channel names | `dma-names = "tx", "rx";` |
| `cs-gpios` | GPIO-based chip selects | `cs-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;` |

## SPI Device Nodes (Children)

SPI devices are children of the SPI controller:

```dts
spi0: spi@40000000 {
	compatible = "vendor,my-spi";
	reg = <0x40000000 0x1000>;
	#address-cells = <1>;
	#size-cells = <0>;

	/* SPI device at CS0 */
	adc@0 {
		compatible = "adi,ad7124";
		reg = <0>;  /* Chip select number */
		spi-max-frequency = <5000000>;
		spi-cpol;
		spi-cpha;
	};

	/* SPI device at CS1 */
	dac@1 {
		compatible = "adi,ad5766";
		reg = <1>;  /* Chip select number */
		spi-max-frequency = <10000000>;
	};
};
```

## SPI Device Properties

| Property | Description | Example |
|----------|-------------|---------|
| `reg` | Chip select number (0, 1, 2, ...) | `reg = <0>;` |
| `spi-max-frequency` | Maximum SPI clock frequency (Hz) | `spi-max-frequency = <5000000>;` |
| `spi-cpol` | Clock polarity (idle high) | `spi-cpol;` |
| `spi-cpha` | Clock phase (sample on trailing edge) | `spi-cpha;` |
| `spi-cs-high` | Chip select active high | `spi-cs-high;` |
| `spi-lsb-first` | LSB transmitted first | `spi-lsb-first;` |
| `spi-3wire` | Bidirectional mode (shared MOSI/MISO) | `spi-3wire;` |

## GPIO-Based Chip Selects

Use GPIOs for chip selects instead of hardware CS:

```dts
spi0: spi@40000000 {
	compatible = "vendor,my-spi";
	reg = <0x40000000 0x1000>;
	#address-cells = <1>;
	#size-cells = <0>;

	/* GPIO-based chip selects */
	cs-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>,   /* CS0 */
		   <&gpio0 6 GPIO_ACTIVE_LOW>,   /* CS1 */
		   <&gpio0 7 GPIO_ACTIVE_LOW>;   /* CS2 */

	adc@0 {
		compatible = "adi,ad7124";
		reg = <0>;  /* Uses gpio0 pin 5 */
		spi-max-frequency = <5000000>;
	};
};
```

## DMA Configuration

Specify DMA channels for TX and RX:

```dts
spi0: spi@40000000 {
	compatible = "vendor,my-spi";
	reg = <0x40000000 0x1000>;

	/* DMA channels */
	dmas = <&dma0 0>,   /* TX: DMA channel 0 */
	       <&dma0 1>;   /* RX: DMA channel 1 */
	dma-names = "tx", "rx";
};
```

## ADI AXI SPI Engine Example

Complete AXI SPI Engine devicetree binding:

```dts
axi_spi_engine_0: spi@44a00000 {
	compatible = "adi,axi-spi-engine-1.00.a";
	reg = <0x44a00000 0x1000>;
	interrupt-parent = <&intc>;
	interrupts = <0 56 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clkc 15>;
	clock-names = "s_axi_aclk";
	num-cs = <1>;

	#address-cells = <1>;
	#size-cells = <0>;

	ad9361_phy: ad9361-phy@0 {
		compatible = "adi,ad9361";
		reg = <0>;
		spi-max-frequency = <10000000>;
		spi-cpol;
		spi-cpha;

		/* Device-specific properties */
		/* ... */
	};
};
```

## YAML Schema Example

Example YAML schema for SPI controller binding:

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/spi/vendor,my-spi.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Vendor My SPI Controller

maintainers:
  - Your Name <your.email@example.com>

allOf:
  - $ref: spi-controller.yaml#

properties:
  compatible:
    const: vendor,my-spi

  reg:
    maxItems: 1

  interrupts:
    maxItems: 1

  clocks:
    maxItems: 1

  clock-names:
    items:
      - const: spi_clk

  num-cs:
    description: Number of chip select lines
    $ref: /schemas/types.yaml#/definitions/uint32
    minimum: 1
    maximum: 4

required:
  - compatible
  - reg
  - interrupts
  - clocks
  - clock-names

unevaluatedProperties: false

examples:
  - |
    #include <dt-bindings/interrupt-controller/irq.h>

    spi@40000000 {
        compatible = "vendor,my-spi";
        reg = <0x40000000 0x1000>;
        interrupts = <50 IRQ_TYPE_LEVEL_HIGH>;
        clocks = <&clk_spi0>;
        clock-names = "spi_clk";
        num-cs = <4>;

        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7124";
            reg = <0>;
            spi-max-frequency = <5000000>;
        };
    };
```

## Validation

Validate devicetree bindings:

```bash
# Check YAML schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/spi/vendor,my-spi.yaml

# Check devicetree against schemas
make dtbs_check
```

## Common Pitfalls

1. **Missing #address-cells and #size-cells**:
   ```dts
   /* Wrong - missing address/size cells */
   spi0: spi@40000000 {
       compatible = "vendor,my-spi";
       reg = <0x40000000 0x1000>;
   };

   /* Correct */
   spi0: spi@40000000 {
       compatible = "vendor,my-spi";
       reg = <0x40000000 0x1000>;
       #address-cells = <1>;
       #size-cells = <0>;
   };
   ```

2. **Incorrect reg property in SPI device**:
   ```dts
   /* Wrong - reg should be chip select number, not address */
   adc@0 {
       compatible = "adi,ad7124";
       reg = <0x40000000>;  /* WRONG */
   };

   /* Correct */
   adc@0 {
       compatible = "adi,ad7124";
       reg = <0>;  /* Chip select 0 */
   };
   ```

3. **Missing spi-max-frequency**:
   ```dts
   /* Device driver will fail without max frequency */
   adc@0 {
       compatible = "adi,ad7124";
       reg = <0>;
       /* Missing: spi-max-frequency = <5000000>; */
   };
   ```

## References

- `Documentation/devicetree/bindings/spi/spi-controller.yaml` - Base SPI controller schema
- `Documentation/devicetree/bindings/spi/adi,axi-spi-engine.yaml` - AXI SPI Engine binding
- `Documentation/devicetree/bindings/spi/spi-cadence.yaml` - Cadence SPI controller (Zynq)
