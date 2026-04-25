## Debugging Tips

### 1. Verify I2C Communication

```c
const struct device *fg = DEVICE_DT_GET(DT_NODELABEL(fuel_gauge));

if (!device_is_ready(fg)) {
    printk("ERROR: Fuel gauge not ready\n");
    return -ENODEV;
}

/* Try reading a simple register */
union fuel_gauge_prop_val val;
int ret = fuel_gauge_get_prop(fg, FUEL_GAUGE_VOLTAGE, &val);
if (ret < 0) {
    printk("I2C read failed: %d\n", ret);
}
```

### 2. Check SBS Address

SBS standard addresses:
- Write: 0x16 (7-bit: 0x0B)
- Read: 0x17

### 3. Monitor SOC Accuracy

```c
void monitor_soc_accuracy(void)
{
    const struct device *fg = DEVICE_DT_GET(DT_NODELABEL(fuel_gauge));
    union fuel_gauge_prop_val voltage, soc;

    fuel_gauge_get_prop(fg, FUEL_GAUGE_VOLTAGE, &voltage);
    fuel_gauge_get_prop(fg, FUEL_GAUGE_RELATIVE_STATE_OF_CHARGE, &soc);

    printk("Voltage: %u mV, SOC: %u%%\n",
           voltage.voltage / 1000,
           soc.relative_state_of_charge);

    /* For Li-ion, approximate SOC from voltage:
     * 4.2V = 100%, 3.7V = 50%, 3.0V = 0% (rough estimate) */
}
```

### 4. Common Issues

**SOC not updating**:
- Check that battery is actually charging/discharging
- Verify coulomb counter is not stuck
- Some chips need calibration cycle

**Incorrect SOC**:
- Verify sense resistor value in devicetree
- Check for calibration requirements
- Ensure battery capacity matches devicetree

**Communication errors**:
- Verify I2C address (0x0B or 0x55)
- Check pull-up resistors on I2C bus
- Verify power supply to fuel gauge

