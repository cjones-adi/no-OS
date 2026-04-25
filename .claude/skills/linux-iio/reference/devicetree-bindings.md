# IIO Devicetree Bindings

Guide to creating devicetree bindings for IIO devices and examples for different platforms.

## IIO Device Binding Template

```yaml
# SPDX-License-Identifier: (GPL-2.0-only OR BSD-2-Clause)
%YAML 1.2
---
$id: http://devicetree.org/schemas/iio/adc/adi,ad7944.yaml#
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: Analog Devices AD7944 18-bit PulSAR ADC

maintainers:
  - Your Name <your.email@example.com>

description: |
  The AD7944 is an 18-bit precision successive approximation register (SAR)
  analog-to-digital converter (ADC) with a throughput rate of 2.5 MSPS.

$ref: /schemas/spi/spi-peripheral-props.yaml#

properties:
  compatible:
    enum:
      - adi,ad7944
      - adi,ad7985
      - adi,ad7986

  reg:
    maxItems: 1

  spi-max-frequency:
    maximum: 111111111

  avdd-supply:
    description: 2.5V analog supply

  dvdd-supply:
    description: 2.5V digital supply

  vio-supply:
    description: 1.8V to 2.7V I/O supply

  vref-supply:
    description: External reference voltage (optional)

  cnv-gpios:
    maxItems: 1
    description: Convert input GPIO

  turbo-mode:
    type: boolean
    description: Enable turbo mode for higher throughput

required:
  - compatible
  - reg
  - avdd-supply
  - dvdd-supply
  - vio-supply

unevaluatedProperties: false

examples:
  - |
    #include <dt-bindings/gpio/gpio.h>

    spi {
        #address-cells = <1>;
        #size-cells = <0>;

        adc@0 {
            compatible = "adi,ad7944";
            reg = <0>;
            spi-max-frequency = <111111111>;

            avdd-supply = <&supply_2_5V>;
            dvdd-supply = <&supply_2_5V>;
            vio-supply = <&supply_1_8V>;

            cnv-gpios = <&gpio 0 GPIO_ACTIVE_HIGH>;
            turbo-mode;
        };
    };
```

## Common IIO Properties

### Reference Voltage

```yaml
properties:
  vref-supply:
    description: External reference voltage supply

  refin-supply:
    description: Alternative reference input

  adi,reference-select:
    $ref: /schemas/types.yaml#/definitions/uint32
    enum: [0, 1, 2]
    description: |
      Reference voltage source selection:
        0 - Internal reference
        1 - External reference (vref-supply)
        2 - AVDD/2
```

### Clock Properties

```yaml
properties:
  clocks:
    maxItems: 1

  clock-names:
    const: mclk

  adi,clock-frequency-hz:
    description: Master clock frequency in Hz
```

### Interrupt Properties

```yaml
properties:
  interrupts:
    maxItems: 1
    description: Data ready interrupt

  interrupt-names:
    const: DRDY
```

### Channel Configuration

For devices with configurable channels:

```yaml
properties:
  '#address-cells':
    const: 1

  '#size-cells':
    const: 0

patternProperties:
  "^channel@([0-7])$":
    type: object
    description: ADC channel configuration

    properties:
      reg:
        description: Channel number
        enum: [0, 1, 2, 3, 4, 5, 6, 7]

      adi,bipolar:
        type: boolean
        description: Enable bipolar mode for this channel

      adi,buffered:
        type: boolean
        description: Enable input buffer for this channel

      diff-channels:
        description: Differential channel pair as [positive, negative]
        $ref: /schemas/types.yaml#/definitions/uint32-array
        items:
          - description: Positive input
          - description: Negative input

    required:
      - reg

    additionalProperties: false
```

Example usage:
```dts
adc@0 {
    #address-cells = <1>;
    #size-cells = <0>;

    channel@0 {
        reg = <0>;
        adi,bipolar;
        diff-channels = <0 1>;
    };

    channel@1 {
        reg = <1>;
        adi,buffered;
    };
};
```

## Platform-Specific Examples

### Xilinx Zynq (ARM 32-bit)

Path: `arch/arm/boot/dts/xilinx/`

```dts
#include "zynq-zc706.dtsi"
#include "zynq-zc706-adv7511.dtsi"

/ {
    model = "Analog Devices AD9467 FMC Card on Zynq ZC706";

    vref: regulator-vref {
        compatible = "regulator-fixed";
        regulator-name = "vref-ad9467";
        regulator-min-microvolt = <2500000>;
        regulator-max-microvolt = <2500000>;
        regulator-always-on;
    };
};

&fpga_axi {
    rx_dma: dma@44a30000 {
        compatible = "adi,axi-dmac-1.00.a";
        reg = <0x44a30000 0x1000>;
        interrupts = <0 57 IRQ_TYPE_LEVEL_HIGH>;
        clocks = <&clkc 16>;
        #dma-cells = <1>;
        adi,channels {
            #size-cells = <0>;
            #address-cells = <1>;
            dma-channel@0 {
                reg = <0>;
                adi,source-bus-width = <64>;
                adi,destination-bus-width = <64>;
                adi,type = <0>;
            };
        };
    };

    axi_ad9467: axi-ad9467@44a00000 {
        compatible = "adi,axi-ad9467-1.0";
        reg = <0x44a00000 0x10000>;
        dmas = <&rx_dma 0>;
        dma-names = "rx";
        #io-backend-cells = <0>;
    };
};

&spi0 {
    status = "okay";

    adc@0 {
        compatible = "adi,ad9467";
        reg = <0>;
        spi-max-frequency = <10000000>;
        clocks = <&axi_ad9467_clkgen>;
        io-backends = <&axi_ad9467>;
        vref-supply = <&vref>;
    };
};
```

### Xilinx ZynqMP (ARM64)

Path: `arch/arm64/boot/dts/xilinx/`

```dts
#include "zynqmp-zcu102-rev1.0.dts"

&spi0 {
    status = "okay";
    num-cs = <2>;

    adc@0 {
        compatible = "adi,ad9081";
        reg = <0>;
        spi-max-frequency = <5000000>;

        reset-gpios = <&gpio 133 GPIO_ACTIVE_LOW>;

        vdd1-supply = <&reg_1v8>;
        vdd2-supply = <&reg_1v8>;
        avdd1-supply = <&reg_1v3>;
        avdd2-supply = <&reg_1v3>;

        clocks = <&axi_ad9081_rx_jesd 0>;
        clock-names = "jesd_rx_clk";

        io-backends = <&axi_ad9081_rx>;

        adi,jesd204-topology = <1 2 8 4>;
    };
};
```

### Raspberry Pi (Overlay)

Path: Custom overlay file

```dts
/dts-v1/;
/plugin/;

/ {
    compatible = "brcm,bcm2711";  // RPi 4

    fragment@0 {
        target = <&spi0>;
        __overlay__ {
            status = "okay";
            #address-cells = <1>;
            #size-cells = <0>;

            ad7606: adc@0 {
                compatible = "adi,ad7606-8";
                reg = <0>;
                spi-max-frequency = <10000000>;

                avcc-supply = <&reg_5v0>;

                reset-gpios = <&gpio 22 GPIO_ACTIVE_LOW>;
                convst-gpios = <&gpio 17 GPIO_ACTIVE_HIGH>;
                busy-gpios = <&gpio 27 GPIO_ACTIVE_HIGH>;

                interrupt-parent = <&gpio>;
                interrupts = <27 IRQ_TYPE_EDGE_FALLING>;
            };
        };
    };
};
```

Compile:
```bash
dtc -@ -I dts -O dtb -o ad7606-overlay.dtbo ad7606-overlay.dts
sudo cp ad7606-overlay.dtbo /boot/overlays/
```

Add to `/boot/config.txt`:
```
dtoverlay=ad7606-overlay
```

### SoCFPGA (Intel/Altera)

Path: `arch/arm/boot/dts/intel/socfpga/`

```dts
#include "socfpga_cyclone5.dtsi"

&spi1 {
    status = "okay";

    adc@0 {
        compatible = "adi,ad7124-4";
        reg = <0>;
        spi-max-frequency = <5000000>;

        vref-supply = <&vref_2v5>;
        avdd-supply = <&avdd_3v3>;

        clocks = <&osc1>;

        #address-cells = <1>;
        #size-cells = <0>;

        channel@0 {
            reg = <0>;
            adi,bipolar;
            diff-channels = <0 1>;
        };
    };
};
```

## IIO Backend Integration

For devices using IIO backend framework:

```yaml
properties:
  io-backends:
    description: Phandle to IIO backend device
    maxItems: 1
```

Device tree:
```dts
axi_ad3552r: axi-ad3552r@44a70000 {
    compatible = "adi,axi-ad3552r";
    reg = <0x44a70000 0x1000>;
    dmas = <&tx_dma 0>;
    dma-names = "tx";
    #io-backend-cells = <0>;
};

&spi0 {
    dac@0 {
        compatible = "adi,ad3552r";
        reg = <0>;
        spi-max-frequency = <66000000>;
        io-backends = <&axi_ad3552r>;

        vref-supply = <&vref_2v5>;
    };
};
```

## Validation

```bash
# Validate binding schema
make dt_binding_check DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad7944.yaml

# Validate compiled devicetree
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- dtbs_check

# Validate specific DTS against binding
make ARCH=arm64 DT_SCHEMA_FILES=Documentation/devicetree/bindings/iio/adc/adi,ad9081.yaml dtbs_check
```

## Common Patterns

### Conditional Properties

Use `allOf` with `if/then` for variant-specific constraints:

```yaml
allOf:
  # Mutually exclusive reference sources
  - if:
      required:
        - vref-supply
    then:
      properties:
        refin-supply: false

  # Device-specific constraints
  - if:
      properties:
        compatible:
          contains:
            const: adi,ad7124-4
    then:
      properties:
        channel@4: false
        channel@5: false
        channel@6: false
        channel@7: false
```

### Multiple Compatible Strings

```yaml
properties:
  compatible:
    oneOf:
      - const: adi,ad9467
      - items:
          - enum:
              - adi,ad9643
              - adi,ad9434
          - const: adi,ad9467  # Fallback
```

## Testing Device Tree

```bash
# Check device registered
cat /sys/bus/iio/devices/iio:device0/name

# Check DT properties loaded
cat /proc/device-tree/amba/spi@e0007000/adc@0/compatible

# Verify supply connections
grep -r "vref-supply" /sys/firmware/devicetree/base/

# Test IIO device
iio_info | grep -A 20 ad7944
```
