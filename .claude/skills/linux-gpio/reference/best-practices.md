# GPIO Best Practices and Common Patterns

Essential patterns, register caching, locking strategies, and checklists for GPIO controller and consumer drivers.

## Common Patterns Summary

### GPIO Controller Driver Checklist

- [ ] Define `struct gpio_chip` with callbacks
- [ ] Implement `direction_input/output, get, set`
- [ ] Implement `get_multiple/set_multiple` for efficiency
- [ ] Add `set_config` for electrical configuration support
- [ ] Use appropriate locking (spinlock for MMIO, mutex for I2C/SPI)
- [ ] Set `can_sleep` correctly (false for MMIO, true for I2C/SPI)
- [ ] Set output value BEFORE changing direction to output
- [ ] Use `devm_gpiochip_add_data()` for automatic cleanup
- [ ] Add IRQ chip support if hardware supports GPIO interrupts
- [ ] Use `IRQCHIP_IMMUTABLE` and `GPIOCHIP_IRQ_RESOURCE_HELPERS`
- [ ] Implement bus_lock/bus_sync_unlock for I2C/SPI IRQ chips
- [ ] Use regmap for I2C/SPI GPIO expanders
- [ ] Mark volatile registers (input, interrupt status)
- [ ] Provide GPIO line names for debuggability

### GPIO Consumer Driver Checklist

- [ ] Use descriptor-based API (`gpiod_*`, not legacy GPIO numbers)
- [ ] Use `devm_gpiod_get()` or `devm_gpiod_get_optional()`
- [ ] Specify initial direction/value in flags parameter
- [ ] Use `gpiod_set_value()` for MMIO GPIOs (fast path)
- [ ] Use `gpiod_set_value_cansleep()` for I2C/SPI GPIOs
- [ ] Use `gpiod_to_irq()` to get IRQ number from GPIO
- [ ] Handle GPIO polarity via devicetree (GPIO_ACTIVE_LOW/HIGH)
- [ ] Use `dev_err_probe()` for deferred probe handling
- [ ] Add devicetree bindings with `<con_id>-gpios` properties
