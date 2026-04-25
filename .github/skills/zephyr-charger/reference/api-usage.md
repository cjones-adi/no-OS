## Consumer API Usage

### Get Charging Status

```c
#include <zephyr/drivers/charger.h>

const struct device *charger = DEVICE_DT_GET(DT_NODELABEL(charger));

union charger_propval val;

/* Get charging status */
charger_get_property(charger, CHARGER_PROP_STATUS, &val);

switch (val.status) {
case CHARGER_STATUS_CHARGING:
    printk("Battery charging\n");
    break;
case CHARGER_STATUS_FULL:
    printk("Battery full\n");
    break;
case CHARGER_STATUS_DISCHARGING:
    printk("Battery discharging\n");
    break;
case CHARGER_STATUS_NOT_CHARGING:
    printk("Not charging\n");
    break;
}
```

### Check External Power

```c
union charger_propval val;

charger_get_property(charger, CHARGER_PROP_ONLINE, &val);

if (val.online == CHARGER_ONLINE_FIXED) {
    printk("USB/AC power connected\n");
} else {
    printk("Running on battery\n");
}
```

### Configure Charge Current

```c
union charger_propval val;

/* Set charge current to 500mA */
val.const_charge_current_ua = 500000;
charger_set_property(charger, CHARGER_PROP_CONSTANT_CHARGE_CURRENT_UA, &val);
```

### Configure Charge Voltage

```c
union charger_propval val;

/* Set charge voltage to 4.2V (Li-ion standard) */
val.const_charge_voltage_uv = 4200000;
charger_set_property(charger, CHARGER_PROP_CONSTANT_CHARGE_VOLTAGE_UV, &val);
```

### Enable/Disable Charging

```c
/* Enable charging */
charger_charge_enable(charger, true);

/* Disable charging */
charger_charge_enable(charger, false);
```

## Common Patterns and Best Practices

### 1. USB Current Detection

```c
void configure_for_usb(enum usb_type type)
{
    const struct device *charger = DEVICE_DT_GET(DT_NODELABEL(charger));
    union charger_propval val;

    switch (type) {
    case USB_SDP:  /* Standard Downstream Port */
        val.input_current_regulation_current_ua = 500000;  /* 500mA */
        break;
    case USB_DCP:  /* Dedicated Charging Port */
        val.input_current_regulation_current_ua = 1500000; /* 1.5A */
        break;
    case USB_CDP:  /* Charging Downstream Port */
        val.input_current_regulation_current_ua = 1500000; /* 1.5A */
        break;
    }

    charger_set_property(charger,
                         CHARGER_PROP_INPUT_REGULATION_CURRENT_UA,
                         &val);
}
```

### 2. Charging Monitor Thread

```c
void charging_monitor_thread(void)
{
    const struct device *charger = DEVICE_DT_GET(DT_NODELABEL(charger));
    union charger_propval status, health;

    while (1) {
        /* Check charging status */
        charger_get_property(charger, CHARGER_PROP_STATUS, &status);
        charger_get_property(charger, CHARGER_PROP_HEALTH, &health);

        if (health.health != CHARGER_HEALTH_GOOD) {
            printk("Charger fault: %d\n", health.health);
            /* Handle fault */
        }

        if (status.status == CHARGER_STATUS_FULL) {
            /* Battery full - reduce current or disable */
        }

        k_msleep(1000);
    }
}
```

### 3. Temperature-Based Charge Control

```c
void adjust_charge_current_for_temp(int16_t temp_celsius)
{
    const struct device *charger = DEVICE_DT_GET(DT_NODELABEL(charger));
    union charger_propval val;

    if (temp_celsius < 0 || temp_celsius > 45) {
        /* Outside safe range - disable charging */
        charger_charge_enable(charger, false);
    } else if (temp_celsius > 40) {
        /* High temp - reduce current */
        val.const_charge_current_ua = 500000;  /* 500mA */
        charger_set_property(charger,
                             CHARGER_PROP_CONSTANT_CHARGE_CURRENT_UA,
                             &val);
    } else {
        /* Normal temp - full current */
        val.const_charge_current_ua = 1000000; /* 1A */
        charger_set_property(charger,
                             CHARGER_PROP_CONSTANT_CHARGE_CURRENT_UA,
                             &val);
        charger_charge_enable(charger, true);
    }
}
```

