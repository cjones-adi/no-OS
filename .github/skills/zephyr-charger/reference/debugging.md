## Debugging Tips

### 1. Monitor Charger State

```c
void debug_charger_state(const struct device *charger)
{
    union charger_propval val;

    charger_get_property(charger, CHARGER_PROP_STATUS, &val);
    printk("Status: %d\n", val.status);

    charger_get_property(charger, CHARGER_PROP_ONLINE, &val);
    printk("Online: %d\n", val.online);

    charger_get_property(charger, CHARGER_PROP_HEALTH, &val);
    printk("Health: %d\n", val.health);

    charger_get_property(charger, CHARGER_PROP_CONSTANT_CHARGE_CURRENT_UA, &val);
    printk("Charge Current: %u µA\n", val.const_charge_current_ua);

    charger_get_property(charger, CHARGER_PROP_CONSTANT_CHARGE_VOLTAGE_UV, &val);
    printk("Charge Voltage: %u µV\n", val.const_charge_voltage_uv);
}
```

### 2. Common Issues

**Not charging**:
- Check `CHARGER_PROP_ONLINE` - external power connected?
- Check `CHARGER_PROP_HEALTH` - any faults?
- Verify charge_enable() was called
- Check battery present detection

**Wrong charge current**:
- Verify register value calculation
- Check input current limit
- Verify hardware current sense resistor value

**Charging stops prematurely**:
- Check termination current setting
- Verify CV voltage threshold
- Monitor temperature (thermal shutdown?)

