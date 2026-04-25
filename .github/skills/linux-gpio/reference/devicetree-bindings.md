# Devicetree GPIO Bindings

Detailed guide for devicetree GPIO specification, bindings, and line naming.

## Devicetree GPIO Specification

```dts
// GPIO controller node
gpio0: gpio@40000000 {
	compatible = "vendor,mygpio";
	reg = <0x40000000 0x1000>;
	gpio-controller;
	#gpio-cells = <2>;              // <gpio_number flags>
	interrupt-controller;
	#interrupt-cells = <2>;
	interrupts = <GIC_SPI 10 IRQ_TYPE_LEVEL_HIGH>;
	ngpios = <32>;
};

// GPIO consumer
my_device: my-device@41000000 {
	compatible = "vendor,my-device";
	reg = <0x41000000 0x1000>;

	// GPIO properties: <con_id>-gpios = <&controller gpio_num flags>;
	reset-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;     // Active low
	enable-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;  // Active high
	irq-gpios = <&gpio0 15 GPIO_ACTIVE_HIGH>;

	// Multiple GPIOs with same con_id (use gpiod_get_array)
	cs-gpios = <&gpio0 20 GPIO_ACTIVE_LOW>,
		   <&gpio0 21 GPIO_ACTIVE_LOW>,
		   <&gpio0 22 GPIO_ACTIVE_LOW>;
};
```

**GPIO Flags** (from `dt-bindings/gpio/gpio.h`):
- `GPIO_ACTIVE_HIGH`: Active high (0=inactive, 1=active)
- `GPIO_ACTIVE_LOW`: Active low (1=inactive, 0=active)
- `GPIO_OPEN_DRAIN`: Open-drain output
- `GPIO_OPEN_SOURCE`: Open-source output
- `GPIO_PULL_UP`: Enable pull-up resistor
- `GPIO_PULL_DOWN`: Enable pull-down resistor

### GPIO Line Names

```c
// In GPIO controller driver:
static const char * const mygpio_names[] = {
	"SPI_CS0",
	"SPI_CS1",
	"I2C_SDA",
	"I2C_SCL",
	"UART_TX",
	"UART_RX",
	"LED_STATUS",
	"BUTTON_RESET",
	// ... up to ngpio names
};

// In probe:
gc->names = mygpio_names;
```

These names appear in `/sys/kernel/debug/gpio` and can be used for lookup.

