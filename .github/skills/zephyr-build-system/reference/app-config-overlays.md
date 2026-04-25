## Application Configuration (prj.conf)

### Overview

**prj.conf** enables Kconfig options for your application.

**Format**: `CONFIG_OPTION=y` (or `=n`, `=value`)

### Minimal prj.conf

**Example for ADC sample**:
```conf
CONFIG_ADC=y
```

**Example for sensor sample**:
```conf
CONFIG_SENSOR=y
CONFIG_I2C=y
```

### Common Configuration Patterns

**Enable driver subsystem**:
```conf
CONFIG_SPI=y
CONFIG_I2C=y
CONFIG_GPIO=y
CONFIG_SENSOR=y
CONFIG_ADC=y
CONFIG_DAC=y
CONFIG_REGULATOR=y
```

**Enable logging**:
```conf
CONFIG_LOG=y
CONFIG_SENSOR_LOG_LEVEL_DBG=y
CONFIG_I2C_LOG_LEVEL_DBG=y
```

**Console and shell**:
```conf
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y
CONFIG_SHELL=y
CONFIG_REGULATOR_SHELL=y
```

**Threading and synchronization**:
```conf
CONFIG_MULTITHREADING=y
CONFIG_MAIN_STACK_SIZE=2048
CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE=2048
```

**USB console**:
```conf
CONFIG_USB_DEVICE_STACK=y
CONFIG_USB_DEVICE_PRODUCT="Zephyr CDC ACM"
CONFIG_USB_CDC_ACM=y
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y
CONFIG_UART_LINE_CTRL=y
```

**Devicetree shell** (for debugging DT):
```conf
CONFIG_SHELL=y
CONFIG_DEVMEM_SHELL=y
CONFIG_DEVICE_SHELL=y
```

### Driver-Specific Configuration

**Example: Regulator with logging**:
```conf
CONFIG_REGULATOR=y
CONFIG_REGULATOR_THREAD_SAFE_REFCNT=y
CONFIG_I2C=y

CONFIG_LOG=y
CONFIG_REGULATOR_LOG_LEVEL_DBG=y
CONFIG_I2C_LOG_LEVEL_DBG=y
```

**Example: Sensor with shell**:
```conf
CONFIG_SENSOR=y
CONFIG_I2C=y
CONFIG_SENSOR_SHELL=y
CONFIG_SHELL=y
CONFIG_LOG=y
```

## Board Overlays

### Overview

**Board overlays** modify devicetree for specific boards without changing the board's base devicetree.

**Location**: `boards/<boardname>.overlay` in app directory

**Purpose**:
- Add devices not in board's default DT
- Configure I2C/SPI bus assignments
- Define GPIOs, interrupts, and pins
- Override default settings

### Basic Overlay Structure

**Simple I2C device** (`boards/nrf52840dk_nrf52840.overlay`):
```dts
&i2c0 {
    status = "okay";

    my_sensor: sensor@48 {
        compatible = "vendor,sensor";
        reg = <0x48>;
        int-gpios = <&gpio0 11 GPIO_ACTIVE_LOW>;
    };
};
```

**SPI device** (`boards/nrf52840dk_nrf52840.overlay`):
```dts
&spi1 {
    status = "okay";
    cs-gpios = <&gpio0 25 GPIO_ACTIVE_LOW>;

    dac: dac@0 {
        compatible = "vendor,dac";
        reg = <0>;
        spi-max-frequency = <8000000>;
        ldac-gpios = <&gpio0 26 GPIO_ACTIVE_LOW>;
        shdn-gpios = <&gpio0 27 GPIO_ACTIVE_HIGH>;
    };
};
```

**Using zephyr,user node** (for test/sample code):
```dts
/ {
    zephyr,user {
        io-channels = <&adc0 0>, <&adc0 1>;
    };
};

&adc0 {
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;

    channel@0 {
        reg = <0>;
        zephyr,gain = "ADC_GAIN_1";
        zephyr,reference = "ADC_REF_INTERNAL";
        zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
        zephyr,resolution = <12>;
    };
};
```

### Common Overlay Patterns

**Enable existing peripheral**:
```dts
&i2c1 {
    status = "okay";  // Enable disabled peripheral
};
```

**Add GPIO expander**:
```dts
&i2c0 {
    status = "okay";

    gpio_exp: gpio@20 {
        compatible = "nxp,pcal6408a";
        reg = <0x20>;
        gpio-controller;
        #gpio-cells = <2>;
        ngpios = <8>;
        int-gpios = <&gpio0 3 GPIO_ACTIVE_LOW>;
    };
};
```

**Aliases for sample code**:
```dts
/ {
    aliases {
        myregulator = &buck1;
        mysensor = &temp_sensor;
    };
};
```

**Multiple devices on same bus**:
```dts
&i2c0 {
    status = "okay";

    sensor1: sensor@48 {
        compatible = "vendor,sensor";
        reg = <0x48>;
    };

    sensor2: sensor@49 {
        compatible = "vendor,sensor";
        reg = <0x49>;
    };
};
```

### Board-Specific Considerations

Different boards use different I2C/SPI buses and GPIO ports:

**nRF52840 DK**:
```dts
&i2c1 {  // nRF uses i2c1 for external devices
    status = "okay";
    // device config
};
```

**STM32 Nucleo**:
```dts
&i2c2 {  // STM32 often uses i2c2
    status = "okay";
    // device config
};
```

**ESP32**:
```dts
&i2c0 {  // ESP32 uses i2c0
    status = "okay";
    // device config
};
```

