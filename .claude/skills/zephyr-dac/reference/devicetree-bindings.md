## Devicetree Binding Pattern

### Base Binding: dac-controller.yaml

All DAC bindings include `dac-controller.yaml`:

```yaml
# From dts/bindings/dac/dac-controller.yaml
include: base.yaml

properties:
  "#io-channel-cells":
    type: int
    required: true
```

**Minimal binding** – just requires `#io-channel-cells` property.

### Device-Specific Binding: AD56x1 (Single-Channel SPI)

From **dts/bindings/dac/adi,ad56x1-base.yaml**:

```yaml
include: [dac-controller.yaml, spi-device.yaml]

properties:
  "#io-channel-cells":
    const: 1

io-channel-cells:
  - output
```

**Usage in devicetree**:

```dts
&spi0 {
	status = "okay";
	cs-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;

	dac_ad5621: ad5621@0 {
		compatible = "adi,ad5621";
		reg = <0>;
		spi-max-frequency = <30000000>;
		#io-channel-cells = <1>;
	};
};
```

### Device-Specific Binding: AD559x (Multi-Channel MFD)

From **dts/bindings/dac/adi,ad559x-dac.yaml**:

```yaml
description: AD559x DAC Controller

compatible: "adi,ad559x-dac"

include: dac-controller.yaml

properties:
  "#io-channel-cells":
    const: 1

  double-output-range:
    type: boolean
    description: |
      Default DAC output range is 0V to Vref.
      This option increases the range from 0V to 2 x Vref.
      Note that this requires VDD >= 2 x Vref.

io-channel-cells:
  - output
```

**Usage in devicetree** (MFD parent-child):

```dts
&i2c1 {
	status = "okay";

	ad5592: ad5592@11 {
		compatible = "adi,ad5592";
		reg = <0x11>;
		#address-cells = <1>;
		#size-cells = <0>;

		dac: dac {
			compatible = "adi,ad559x-dac";
			#io-channel-cells = <1>;
			double-output-range;  /* 0V to 2×Vref */
		};
	};
};
```

