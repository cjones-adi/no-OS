## Debugging Devicetree Issues

### 1. Enable Devicetree Debugging

Build with verbose devicetree output:

```bash
west build -b boardname -- -DEXTRA_DTC_FLAGS="-v"
```

### 2. View Generated Devicetree

```bash
cat build/zephyr/zephyr.dts
```

This shows the final devicetree after overlays and preprocessing.

### 3. View Generated Macros

```bash
cat build/zephyr/include/generated/zephyr/devicetree_generated.h | grep -i device_name
```

### 4. Common Errors and Solutions

#### Error: "unknown compatible"

```
devicetree warning: compatible 'vendor,chip' is unknown, ignoring
```

**Cause**: No binding file matches the compatible string.

**Solution**:
- Create binding file: `dts/bindings/subsystem/vendor,chip.yaml`
- Or add compatible to existing binding

#### Error: "missing required property"

```
devicetree error: <Node /path/to/device>:
  missing required property 'reg'
```

**Cause**: Devicetree node missing a required property from binding.

**Solution**: Add property to devicetree:
```dts
device@addr {
    reg = <0xaddr>;  /* Add required property */
};
```

#### Error: "value not in enum"

```
devicetree error: 'range' value 5 is not in enum [0, 1, 2, 3]
```

**Cause**: Property value doesn't match binding's enum.

**Solution**: Use valid enum value:
```dts
range = <2>;  /* Use value from enum list */
```

#### Error: "duplicate node name"

```
devicetree error: duplicate node name
```

**Cause**: Multiple nodes with same name/address.

**Solution**: Use unique node names:
```dts
device1: sensor@1d { ... };
device2: sensor@1e { ... };  /* Different address */
```

#### Error: "#cells mismatch"

```
devicetree error: phandle array 'gpios' has wrong cell count
```

**Cause**: GPIO/ADC/DAC specifier has wrong number of cells.

**Solution**: Match `#gpio-cells` count:
```dts
/* If #gpio-cells = <2>, provide 2 cells */
reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;
```

## Devicetree Header Files

For enum values, create header files visible to devicetree.

**File**: `include/zephyr/dt-bindings/sensor/adxl345.h`

```c
/* Copyright (c) 2024 Analog Devices Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ZEPHYR_INCLUDE_DT_BINDINGS_SENSOR_ADXL345_H_
#define ZEPHYR_INCLUDE_DT_BINDINGS_SENSOR_ADXL345_H_

/* Range values */
#define ADXL345_DT_RANGE_2G   0
#define ADXL345_DT_RANGE_4G   1
#define ADXL345_DT_RANGE_8G   2
#define ADXL345_DT_RANGE_16G  3

/* ODR values */
#define ADXL345_DT_ODR_12_5   7
#define ADXL345_DT_ODR_25     8
#define ADXL345_DT_ODR_50     9
#define ADXL345_DT_ODR_100    10
#define ADXL345_DT_ODR_200    11

#endif /* ZEPHYR_INCLUDE_DT_BINDINGS_SENSOR_ADXL345_H_ */
```

**Devicetree usage**:

```dts
#include <zephyr/dt-bindings/sensor/adxl345.h>

&i2c0 {
    adxl345@1d {
        compatible = "adi,adxl345";
        reg = <0x1d>;
        range = <ADXL345_DT_RANGE_8G>;  /* Use macro instead of raw value */
        odr = <ADXL345_DT_ODR_100>;
    };
};
```

## Best Practices

### 1. Use Descriptive Property Names

❌ **Bad**:
```yaml
properties:
  val:
    type: int
```

✅ **Good**:
```yaml
properties:
  voltage-reference:
    type: string
    description: Voltage reference selection
```

### 2. Provide Clear Descriptions

❌ **Bad**:
```yaml
properties:
  mode:
    type: int
    enum: [0, 1, 2]
```

✅ **Good**:
```yaml
properties:
  operating-mode:
    type: int
    default: 0
    enum:
      - 0  # MODE_NORMAL
      - 1  # MODE_LOW_POWER
      - 2  # MODE_HIGH_SPEED
    description: |
      Device operating mode:
      - 0: Normal mode (default, 100 mA)
      - 1: Low power mode (10 mA)
      - 2: High speed mode (200 mA)
```

### 3. Use Sensible Defaults

```yaml
properties:
  gain:
    type: string
    default: "gain-1"  # Default to unity gain
    enum:
      - "gain-1"
      - "gain-2"
```

### 4. Document Register Values

```yaml
properties:
  power-down-mode:
    type: string
    default: "normal"
    enum:
      - "normal"            # reg: 0
      - "power-down-1k"     # reg: 1
      - "power-down-100k"   # reg: 2
    description: |
      Power-down mode select.
      - Normal mode (reg: 0)
      - 1 kOhm output impedance (reg: 1)
      - 100 kOhm output impedance (reg: 2)
```

### 5. Include Required Base Bindings

Always include appropriate base bindings:

```yaml
# I2C device
include: [i2c-device.yaml, sensor-device.yaml]

# SPI device
include: [spi-device.yaml, adc-controller.yaml]

# GPIO controller
include: [gpio-controller.yaml]
```

### 6. Use Property Allowlists for Child Nodes

When including base bindings but not exposing all properties:

```yaml
include: [base.yaml, power.yaml]

property-allowlist:
  - compatible
  - reg
  - status
```

### 7. Document Cell Specifiers

```yaml
properties:
  "#gpio-cells":
    const: 2

gpio-cells:
  - pin
  - flags
```

### 8. Validate Enums with Header Files

Create `.h` files for enum constants:

```yaml
# In binding
properties:
  range:
    type: int
    enum:
      - 0  # ADXL345_DT_RANGE_2G (from dt-bindings/sensor/adxl345.h)
      - 1  # ADXL345_DT_RANGE_4G
      - 2  # ADXL345_DT_RANGE_8G
```

## References

- **Base Binding**: `dts/bindings/base/base.yaml`
- **I2C Device Binding**: `dts/bindings/i2c/i2c-device.yaml`
- **SPI Device Binding**: `dts/bindings/spi/spi-device.yaml`
- **GPIO Controller Binding**: `dts/bindings/gpio/gpio-controller.yaml`
- **ADC Controller Binding**: `dts/bindings/adc/adc-controller.yaml`
- **DAC Controller Binding**: `dts/bindings/dac/dac-controller.yaml`
- **Sensor Device Binding**: `dts/bindings/sensor/sensor-device.yaml`
- **Binding Types**: `dts/bindings/binding-types.txt`
- **Vendor Prefixes**: `dts/bindings/vendor-prefixes.txt`
- **Official Documentation**: https://docs.zephyrproject.org/latest/build/dts/api/bindings.html
- **Devicetree Specification**: https://devicetree-specification.readthedocs.io/

**Reference Bindings**:
- **I2C Sensor**: `dts/bindings/sensor/adi,adxl345.yaml` – Simple I2C accelerometer
- **SPI ADC with Channels**: `dts/bindings/adc/adi,ad4130-adc.yaml` – SPI ADC with child channel configuration
- **I2C DAC Family**: `dts/bindings/dac/adi,ad569x-base.yaml` – Base binding with variants
- **MFD Device**: `dts/bindings/mfd/adi,ad559x-i2c.yaml` – Multi-function device parent
- **GPIO Controller**: `dts/bindings/gpio/adi,adp5585-gpio.yaml` – GPIO controller with cell specifier

## Summary Checklist

When creating a new devicetree binding:

- [ ] Choose appropriate file name: `vendor,chip[-subsystem].yaml`
- [ ] Add copyright and SPDX license header
- [ ] Write clear multi-line description
- [ ] Define `compatible` string
- [ ] Include appropriate base bindings (`i2c-device`, `spi-device`, etc.)
- [ ] Define all device-specific properties with:
  - [ ] Correct `type` (int, boolean, string, array, phandle-array, etc.)
  - [ ] Clear `description` with usage guidance
  - [ ] `required: true` if property is mandatory
  - [ ] `default` value if applicable
  - [ ] `enum` list if value is constrained
  - [ ] `const` if value must be specific
- [ ] For controllers, define cell specifiers:
  - [ ] `#gpio-cells`, `#io-channel-cells`, etc.
  - [ ] Document what each cell represents
- [ ] For devices with sub-nodes, define `child-binding`
- [ ] Create corresponding `.h` file in `include/zephyr/dt-bindings/` for enum constants
- [ ] Test binding with sample devicetree overlay
- [ ] Verify devicetree compiler validates correctly
- [ ] Check generated macros in `devicetree_generated.h`
- [ ] Document any hardware-specific constraints or requirements
