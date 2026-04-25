## Binding Validation and Testing

### Devicetree Compiler Validation

The Zephyr build system validates devicetree files against bindings:

```bash
west build -b boardname samples/sensor/adxl345
```

**Common errors**:

```
devicetree error: <Node /i2c@40000000/adxl345@1d>:
  missing required property 'reg'
```

**Fix**: Add `reg` property to devicetree:
```dts
adxl345@1d {
    compatible = "adi,adxl345";
    reg = <0x1d>;  /* Add I2C address */
};
```

```
devicetree error: <Node /i2c@40000000/adxl345@1d>:
  'range' value 5 is not in enum [0, 1, 2, 3]
```

**Fix**: Use valid enum value:
```dts
range = <2>;  /* ADXL345_DT_RANGE_8G */
```

### Testing Bindings

1. **Create test devicetree overlay**:

**File**: `boards/test_board.overlay`

```dts
&i2c0 {
    status = "okay";

    test_device: adxl345@1d {
        compatible = "adi,adxl345";
        reg = <0x1d>;
        range = <2>;
        odr = <10>;
        int1-gpios = <&gpio0 5 GPIO_ACTIVE_HIGH>;
    };
};
```

2. **Build with board**:

```bash
west build -b boardname -p -- -DDTC_OVERLAY_FILE=boards/test_board.overlay
```

3. **Check generated macros**:

```bash
cat build/zephyr/include/generated/zephyr/devicetree_generated.h | grep -i adxl345
```

Expected output:
```c
#define DT_N_S_soc_S_i2c_40000000_S_adxl345_1d_P_range 2
#define DT_N_S_soc_S_i2c_40000000_S_adxl345_1d_P_odr 10
```

