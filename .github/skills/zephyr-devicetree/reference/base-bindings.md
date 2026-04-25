## Base Bindings (Include Mechanism)

Base bindings provide common properties that many devices share.

### Common Base Bindings

#### `base.yaml` – All Devices

Every device binding should include `base.yaml` (directly or indirectly):

```yaml
include: base.yaml
```

**Provides**:
- `compatible` (required)
- `status` ("okay", "disabled", "reserved", "fail")
- `reg` (device address)
- `reg-names` (register block names)

#### `power.yaml` – Power Management

Devices with power management:

```yaml
include: [base.yaml, power.yaml]
```

**Provides**:
- `wakeup-source` (boolean)
- `zephyr,pm-device-runtime-auto` (boolean)

### Bus-Specific Bindings

#### `i2c-device.yaml` – I2C Devices

```yaml
include: [i2c-device.yaml]
```

**Provides**:
- `on-bus: i2c`
- `reg` (required) – I2C address

**Example**:
```yaml
# adi,adxl345.yaml
compatible: "adi,adxl345"
include: [i2c-device.yaml, sensor-device.yaml]
```

**Devicetree usage**:
```dts
&i2c0 {
    adxl345@1d {
        compatible = "adi,adxl345";
        reg = <0x1d>;  /* I2C address */
    };
};
```

#### `spi-device.yaml` – SPI Devices

```yaml
include: [spi-device.yaml]
```

**Provides**:
- `on-bus: spi`
- `reg` (required) – Chip select index
- `spi-max-frequency` (required) – Max SPI clock Hz
- `spi-cpol` (boolean) – Clock polarity
- `spi-cpha` (boolean) – Clock phase
- `spi-cs-high` (boolean) – Chip select active high
- `spi-lsb-first` (boolean) – LSB first mode

**Example**:
```yaml
# adi,ad4130-adc.yaml
compatible: "adi,ad4130-adc"
include: [adc-controller.yaml, spi-device.yaml]

properties:
  spi-cs-setup-delay-ns:
    default: 1000
  spi-cs-hold-delay-ns:
    default: 1000
```

**Devicetree usage**:
```dts
&spi0 {
    ad4130@0 {
        compatible = "adi,ad4130-adc";
        reg = <0>;  /* CS index */
        spi-max-frequency = <2700000>;
    };
};
```

### Subsystem Base Bindings

#### `sensor-device.yaml` – Sensors

```yaml
include: [sensor-device.yaml]
```

**Provides**:
- `friendly-name` (string) – Human-readable sensor name

#### `adc-controller.yaml` – ADC Controllers

```yaml
include: [adc-controller.yaml]
```

**Provides**:
- `#io-channel-cells` (required)
- `#address-cells: 1`
- `#size-cells: 0`
- Child binding for ADC channels

#### `dac-controller.yaml` – DAC Controllers

```yaml
include: [dac-controller.yaml]
```

**Provides**:
- `#io-channel-cells` (int)

#### `gpio-controller.yaml` – GPIO Controllers

**Provides**:
- `gpio-controller` (boolean, required)
- `#gpio-cells` (required) – Number of cells in GPIO specifier
- `ngpios` (int, default 32) – Number of GPIO pins
- `gpio-reserved-ranges` (array) – Unusable GPIO ranges
- `gpio-line-names` (string-array) – GPIO pin names

