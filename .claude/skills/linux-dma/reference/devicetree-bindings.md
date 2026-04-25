# DMA Devicetree Bindings

Guide to DMA controller and consumer devicetree bindings.

## DMA Controller Bindings

DMA controllers must specify the number of cells in consumer references.

### Basic DMA Controller

```dts
dma_controller: dma@40000000 {
	compatible = "vendor,dma-controller";
	reg = <0x40000000 0x1000>;
	interrupts = <GIC_SPI 10 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clkc 15>;

	#dma-cells = <1>;        // Number of cells in consumer reference
	dma-channels = <8>;      // Number of available channels
};
```

### Multi-Cell DMA Controllers

Some controllers need multiple cells to identify channels:

```dts
dmac: dma@50000000 {
	compatible = "vendor,advanced-dma";
	reg = <0x50000000 0x1000>;
	interrupts = <GIC_SPI 20 IRQ_TYPE_LEVEL_HIGH>;

	#dma-cells = <2>;        // <channel, request_id>
	dma-channels = <16>;
	dma-requests = <64>;     // Number of DMA request lines
};
```

### ADI AXI DMAC

Analog Devices AXI DMAC for FPGA designs:

```dts
axi_dmac: dma@44a30000 {
	compatible = "adi,axi-dmac-1.00.a";
	reg = <0x44a30000 0x1000>;
	interrupts = <0 57 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clkc 15>;

	#dma-cells = <1>;
	dma-channels = <1>;

	adi,channels {
		#size-cells = <0>;
		#address-cells = <1>;

		dma-channel@0 {
			reg = <0>;
			adi,source-bus-width = <64>;
			adi,destination-bus-width = <64>;
			adi,source-bus-type = <ADI_AXI_DMAC_TYPE_AXI_STREAM>;
			adi,destination-bus-type = <ADI_AXI_DMAC_TYPE_AXI_MM>;
		};
	};
};
```

Bus type constants (defined in dt-bindings/dma/adi-axi-dmac.h):
```c
#define ADI_AXI_DMAC_TYPE_AXI_MM       0    // AXI Memory Mapped
#define ADI_AXI_DMAC_TYPE_AXI_STREAM   1    // AXI Stream
#define ADI_AXI_DMAC_TYPE_AXI_FIFO     2    // AXI FIFO
```

## DMA Consumer Bindings

Device drivers request DMA channels using `dmas` and `dma-names` properties.

### Single Channel Consumer

```dts
spi0: spi@40100000 {
	compatible = "vendor,spi-controller";
	reg = <0x40100000 0x1000>;
	interrupts = <GIC_SPI 11 IRQ_TYPE_LEVEL_HIGH>;

	// Reference DMA controller and channel
	dmas = <&dma_controller 2>;
	dma-names = "tx";
};
```

### Dual Channel Consumer (TX/RX)

```dts
spi1: spi@40200000 {
	compatible = "vendor,spi-controller";
	reg = <0x40200000 0x1000>;
	interrupts = <GIC_SPI 12 IRQ_TYPE_LEVEL_HIGH>;

	// TX and RX channels
	dmas = <&dma_controller 3>, <&dma_controller 4>;
	dma-names = "tx", "rx";
};
```

### Multi-Cell Consumer

For controllers with #dma-cells > 1:

```dts
uart0: serial@40300000 {
	compatible = "vendor,uart";
	reg = <0x40300000 0x1000>;
	interrupts = <GIC_SPI 13 IRQ_TYPE_LEVEL_HIGH>;

	// <channel, request_id>
	dmas = <&dmac 0 10>, <&dmac 1 11>;
	dma-names = "tx", "rx";
};
```

### Multiple Controllers

Device can use channels from different controllers:

```dts
audio_codec: codec@40400000 {
	compatible = "vendor,audio-codec";
	reg = <0x40400000 0x1000>;

	// TX from dma_controller, RX from audio_dma
	dmas = <&dma_controller 5>, <&audio_dma 0>;
	dma-names = "tx", "rx";
};
```

## IIO with DMA Backend

IIO drivers use DMA via IIO buffer backend:

```dts
axi_adc: axi-adc@44a00000 {
	compatible = "adi,axi-adc-10.0.a";
	reg = <0x44a00000 0x10000>;
	dmas = <&axi_dmac 0>;
	dma-names = "rx";

	#io-channel-cells = <1>;
	clocks = <&clkc 15>;

	adi,axi-adc-channels {
		#address-cells = <1>;
		#size-cells = <0>;

		adc-channel@0 {
			reg = <0>;
			adi,name = "voltage0";
		};

		adc-channel@1 {
			reg = <1>;
			adi,name = "voltage1";
		};
	};
};

ad9361_adc: ad9361-lpc@79020000 {
	compatible = "adi,axi-ad9361-6.00.a";
	reg = <0x79020000 0x6000>;
	dmas = <&rx_dma 0>;
	dma-names = "rx";

	spibus = <&spi0>;
	clocks = <&clkc 15>, <&ad9361_clkin>;
	clock-names = "sampl_clk", "clkin";
};
```

## DMA Channel Specifier Format

The format of `dmas` property cells depends on `#dma-cells`:

### #dma-cells = 1
```dts
dmas = <&dma_controller channel_id>;

// Example:
dmas = <&dmac 0>;              // Channel 0
dmas = <&dmac 5>;              // Channel 5
```

### #dma-cells = 2
```dts
dmas = <&dma_controller channel_id request_id>;

// Example:
dmas = <&dmac 0 10>;           // Channel 0, request line 10
dmas = <&dmac 3 25>;           // Channel 3, request line 25
```

### #dma-cells = 3
```dts
dmas = <&dma_controller channel_id request_id flags>;

// Example:
dmas = <&dmac 0 10 0x01>;      // Channel 0, request 10, flags
```

## DMA Router Bindings

Some SoCs have DMA routers/multiplexers:

```dts
dma_router: dma-router@40500000 {
	compatible = "vendor,dma-router";
	reg = <0x40500000 0x1000>;
	#dma-cells = <3>;

	dma-masters = <&dma_controller>;
	dma-requests = <128>;
};

// Consumer uses router instead of controller directly
spi2: spi@40600000 {
	compatible = "vendor,spi";
	reg = <0x40600000 0x1000>;

	dmas = <&dma_router 0 42 0>, <&dma_router 1 43 0>;
	dma-names = "tx", "rx";
};
```

## Common Properties

### Required Properties (Controller)

```yaml
compatible:
  description: DMA controller compatible string

reg:
  description: MMIO register region

interrupts:
  description: DMA transfer completion interrupt(s)

#dma-cells:
  description: Number of cells in DMA specifier
  const: 1  # or 2, 3, etc.

dma-channels:
  description: Total number of DMA channels
```

### Optional Properties (Controller)

```yaml
dma-requests:
  description: Total number of DMA request signals

clocks:
  description: DMA controller clock(s)

resets:
  description: Reset control for DMA controller

iommus:
  description: IOMMU mapping for DMA addresses
```

### Required Properties (Consumer)

```yaml
dmas:
  description: List of DMA channel specifiers

dma-names:
  description: List of DMA channel names (must match dmas order)
  items:
    - const: tx
    - const: rx
```

## Driver DMA Name Lookup

The driver uses `dma-names` to request channels:

```c
// Devicetree:
// dmas = <&dmac 2>, <&dmac 3>;
// dma-names = "tx", "rx";

// Driver code:
tx_chan = dma_request_chan(dev, "tx");  // Gets channel 2
rx_chan = dma_request_chan(dev, "rx");  // Gets channel 3
```

Order in `dmas` and `dma-names` must match:
```dts
// CORRECT:
dmas = <&dmac 2>, <&dmac 3>;
dma-names = "tx", "rx";

// WRONG (mismatched order):
dmas = <&dmac 2>, <&dmac 3>;
dma-names = "rx", "tx";  // rx gets channel 2, tx gets channel 3!
```

## Platform-Specific Examples

### ARM PL330 DMA Controller

```dts
pdma0: pdma@12680000 {
	compatible = "arm,pl330", "arm,primecell";
	reg = <0x12680000 0x1000>;
	interrupts = <GIC_SPI 138 IRQ_TYPE_LEVEL_HIGH>;
	clocks = <&clock CLK_PDMA0>;
	clock-names = "apb_pclk";
	#dma-cells = <1>;
	#dma-channels = <8>;
	#dma-requests = <32>;
};
```

### Xilinx AXI DMA

```dts
axidma: dma@40400000 {
	compatible = "xlnx,axi-dma-7.1", "xlnx,axi-dma-1.00.a";
	reg = <0x40400000 0x10000>;
	interrupts = <0 29 4>, <0 30 4>;
	#dma-cells = <1>;
	xlnx,include-sg;
	xlnx,sg-length-width = <14>;

	dma-channel@40400000 {
		compatible = "xlnx,axi-dma-mm2s-channel";
		interrupts = <0 29 4>;
		xlnx,datawidth = <0x20>;
	};

	dma-channel@40400030 {
		compatible = "xlnx,axi-dma-s2mm-channel";
		interrupts = <0 30 4>;
		xlnx,datawidth = <0x20>;
	};
};
```

### STM32 DMA Controller

```dts
dma1: dma-controller@40026000 {
	compatible = "st,stm32-dma";
	reg = <0x40026000 0x400>;
	interrupts = <11>, <12>, <13>, <14>, <15>, <16>, <17>, <47>;
	clocks = <&rcc DMA1>;
	#dma-cells = <4>;  // <channel, slot, priority, config>
	st,mem2mem;
};

// Consumer example
spi1: spi@40013000 {
	compatible = "st,stm32h7-spi";
	reg = <0x40013000 0x400>;
	interrupts = <35>;
	dmas = <&dma1 0 37 0x00400 0x05>,  // TX: channel 0, request 37
	       <&dma1 1 38 0x00400 0x05>;  // RX: channel 1, request 38
	dma-names = "tx", "rx";
};
```

## YAML Binding Schema Example

DMA controller binding schema (Documentation/devicetree/bindings/dma/):

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/dma/vendor,dma-controller.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Vendor DMA Controller

maintainers:
  - Vendor Name <vendor@example.com>

allOf:
  - $ref: dma-controller.yaml#

properties:
  compatible:
    const: vendor,dma-controller

  reg:
    maxItems: 1

  interrupts:
    maxItems: 1

  clocks:
    maxItems: 1

  "#dma-cells":
    const: 1
    description: The cell specifies the DMA channel index

  dma-channels:
    maximum: 16

required:
  - compatible
  - reg
  - interrupts
  - "#dma-cells"

additionalProperties: false

examples:
  - |
    dma: dma@40000000 {
        compatible = "vendor,dma-controller";
        reg = <0x40000000 0x1000>;
        interrupts = <10>;
        #dma-cells = <1>;
        dma-channels = <8>;
    };
```

## Kernel Documentation

- DMA Bindings: https://docs.kernel.org/devicetree/bindings/dma/dma.html
- DMAengine Client API: https://docs.kernel.org/driver-api/dmaengine/client.html
- DMAengine Provider API: https://docs.kernel.org/driver-api/dmaengine/provider.html
