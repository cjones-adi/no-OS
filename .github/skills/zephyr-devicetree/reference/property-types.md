## Property Types

Zephyr devicetree bindings support these property types:

### 1. `int` – Integer Value

Single numeric value.

```yaml
properties:
  resolution:
    type: int
    description: ADC resolution in bits
```

**Devicetree usage**:
```dts
resolution = <16>;
```

### 2. `boolean` – Boolean Flag

Presence indicates `true`, absence indicates `false`.

```yaml
properties:
  bipolar:
    type: boolean
    description: Enable bipolar mode
```

**Devicetree usage**:
```dts
bipolar;  /* Property present = true */
```

### 3. `string` – Text Value

Single string value.

```yaml
properties:
  voltage-reference:
    type: string
    default: "internal"
    enum:
      - "internal"
      - "external"
    description: Voltage reference selection
```

**Devicetree usage**:
```dts
voltage-reference = "external";
```

### 4. `array` – Numeric Array

Array of integers.

```yaml
properties:
  gpio-reserved-ranges:
    type: array
    description: |
      Tuples specifying unusable GPIO ranges [start, count].
```

**Devicetree usage**:
```dts
gpio-reserved-ranges = <3 2>, <10 1>;  /* GPIOs 3, 4, 10 reserved */
```

### 5. `uint8-array` – Byte Array

Array of 8-bit unsigned integers.

```yaml
properties:
  mac-address:
    type: uint8-array
    description: Ethernet MAC address
```

**Devicetree usage**:
```dts
mac-address = [00 11 22 33 44 55];
```

### 6. `string-array` – String Array

Array of strings.

```yaml
properties:
  gpio-line-names:
    type: string-array
    description: Names for each GPIO line
```

**Devicetree usage**:
```dts
gpio-line-names = "SDA", "SCL", "LED1", "LED2";
```

### 7. `phandle` – Device Reference

Reference to another devicetree node.

```yaml
properties:
  mfd-dev:
    type: phandle
    description: Reference to parent MFD device
```

**Devicetree usage**:
```dts
mfd-dev = <&pmic>;
```

### 8. `phandle-array` – Device Reference with Cells

Reference to another device with additional parameters (cells).

```yaml
properties:
  reset-gpios:
    type: phandle-array
    description: Reset GPIO pin
```

**Devicetree usage**:
```dts
reset-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>;
```

### 9. `path` – Path to Node

Path to another devicetree node.

```yaml
properties:
  zephyr,flash:
    type: path
    description: Flash controller for code
```

**Devicetree usage**:
```dts
zephyr,flash = &flash0;
```

### 10. `compound` – Complex Type

Structured value (rarely used, prefer `phandle-array`).

## Property Constraints

### `required`

Property must be present:

```yaml
properties:
  reg:
    type: array
    required: true
    description: Device address on bus
```

### `const`

Property must have a specific value:

```yaml
properties:
  "#io-channel-cells":
    type: int
    const: 1
```

### `default`

Default value if property is omitted:

```yaml
properties:
  gain:
    type: string
    default: "gain-1"
    enum:
      - "gain-1"
      - "gain-2"
```

### `enum`

Property value must be from this list:

```yaml
properties:
  power-down-mode:
    type: string
    enum:
      - "normal"
      - "power-down-1k"
      - "power-down-100k"
      - "power-down-3-state"
```

