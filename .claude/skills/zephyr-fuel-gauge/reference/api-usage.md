## Consumer API Usage

### Read State of Charge (SOC)

```c
#include <zephyr/drivers/fuel_gauge.h>

const struct device *fg = DEVICE_DT_GET(DT_NODELABEL(fuel_gauge));

union fuel_gauge_prop_val val;

/* Read relative SOC (0-100%) */
fuel_gauge_get_prop(fg, FUEL_GAUGE_RELATIVE_STATE_OF_CHARGE, &val);
printk("Battery: %u%%\n", val.relative_state_of_charge);
```

### Read Battery Voltage and Current

```c
union fuel_gauge_prop_val voltage, current;

/* Read voltage (µV) */
fuel_gauge_get_prop(fg, FUEL_GAUGE_VOLTAGE, &voltage);
printk("Voltage: %d.%03d V\n",
       voltage.voltage / 1000000,
       (voltage.voltage % 1000000) / 1000);

/* Read current (µA, negative = discharging) */
fuel_gauge_get_prop(fg, FUEL_GAUGE_CURRENT, &current);
if (current.current < 0) {
    printk("Discharging: %d mA\n", -current.current / 1000);
} else {
    printk("Charging: %d mA\n", current.current / 1000);
}
```

### Read Remaining Capacity

```c
union fuel_gauge_prop_val remaining, full;

/* Read remaining capacity */
fuel_gauge_get_prop(fg, FUEL_GAUGE_REMAINING_CAPACITY, &remaining);

/* Read full charge capacity */
fuel_gauge_get_prop(fg, FUEL_GAUGE_FULL_CHARGE_CAPACITY, &full);

printk("Capacity: %u / %u mAh\n",
       remaining.remaining_capacity / 1000,
       full.full_charge_capacity / 1000);
```

### Estimate Runtime

```c
union fuel_gauge_prop_val runtime;

/* Time to empty (minutes) */
fuel_gauge_get_prop(fg, FUEL_GAUGE_RUNTIME_TO_EMPTY, &runtime);
if (runtime.runtime_to_empty != UINT16_MAX) {
    printk("Time to empty: %u:%02u\n",
           runtime.runtime_to_empty / 60,
           runtime.runtime_to_empty % 60);
}
```

### Read Battery Information

```c
char manufacturer[32];
char device_name[32];
char chemistry[8];

/* Read manufacturer name */
fuel_gauge_get_buffer_prop(fg, FUEL_GAUGE_MANUFACTURER_NAME,
                            manufacturer, sizeof(manufacturer));

/* Read device name */
fuel_gauge_get_buffer_prop(fg, FUEL_GAUGE_DEVICE_NAME,
                            device_name, sizeof(device_name));

/* Read chemistry */
fuel_gauge_get_buffer_prop(fg, FUEL_GAUGE_DEVICE_CHEMISTRY,
                            chemistry, sizeof(chemistry));

printk("Battery: %s %s (%s)\n", manufacturer, device_name, chemistry);
```

## Common Patterns and Best Practices

### 1. Battery Monitor Thread

```c
void battery_monitor_thread(void)
{
    const struct device *fg = DEVICE_DT_GET(DT_NODELABEL(fuel_gauge));
    union fuel_gauge_prop_val soc, voltage, current;

    while (1) {
        fuel_gauge_get_prop(fg, FUEL_GAUGE_RELATIVE_STATE_OF_CHARGE, &soc);
        fuel_gauge_get_prop(fg, FUEL_GAUGE_VOLTAGE, &voltage);
        fuel_gauge_get_prop(fg, FUEL_GAUGE_CURRENT, &current);

        printk("[Battery] SOC: %u%%, %d.%03dV, %dmA\n",
               soc.relative_state_of_charge,
               voltage.voltage / 1000000,
               (voltage.voltage % 1000000) / 1000,
               current.current / 1000);

        /* Check low battery */
        if (soc.relative_state_of_charge < 10) {
            printk("WARNING: Low battery!\n");
        }

        k_msleep(60000);  /* Update every minute */
    }
}
```

### 2. SOC-Based LED Indicator

```c
void update_battery_led(void)
{
    const struct device *fg = DEVICE_DT_GET(DT_NODELABEL(fuel_gauge));
    const struct device *led = DEVICE_DT_GET(DT_NODELABEL(battery_led));
    union fuel_gauge_prop_val soc;

    fuel_gauge_get_prop(fg, FUEL_GAUGE_RELATIVE_STATE_OF_CHARGE, &soc);

    if (soc.relative_state_of_charge > 80) {
        led_set_color(led, 0, 3, (uint8_t[]){0, 100, 0});  /* Green */
    } else if (soc.relative_state_of_charge > 20) {
        led_set_color(led, 0, 3, (uint8_t[]){100, 100, 0}); /* Yellow */
    } else {
        led_set_color(led, 0, 3, (uint8_t[]){100, 0, 0});   /* Red */
    }
}
```

### 3. Battery Health Check

```c
void check_battery_health(void)
{
    const struct device *fg = DEVICE_DT_GET(DT_NODELABEL(fuel_gauge));
    union fuel_gauge_prop_val full_cap, design_cap, cycles;

    fuel_gauge_get_prop(fg, FUEL_GAUGE_FULL_CHARGE_CAPACITY, &full_cap);
    fuel_gauge_get_prop(fg, FUEL_GAUGE_DESIGN_CAPACITY, &design_cap);
    fuel_gauge_get_prop(fg, FUEL_GAUGE_CYCLE_COUNT, &cycles);

    /* Calculate health percentage */
    uint8_t health = (full_cap.full_charge_capacity * 100) /
                     (design_cap.design_capacity * 1000);

    printk("Battery Health: %u%% (%u cycles)\n", health, cycles.cycle_count);

    if (health < 80) {
        printk("WARNING: Battery degraded, consider replacement\n");
    }
}
```

### 4. Display Battery Status

```c
void display_battery_status(void)
{
    const struct device *fg = DEVICE_DT_GET(DT_NODELABEL(fuel_gauge));
    union fuel_gauge_prop_val val;
    char buf[64];

    /* SOC */
    fuel_gauge_get_prop(fg, FUEL_GAUGE_RELATIVE_STATE_OF_CHARGE, &val);
    printk("=== Battery Status ===\n");
    printk("SOC: %u%%\n", val.relative_state_of_charge);

    /* Voltage */
    fuel_gauge_get_prop(fg, FUEL_GAUGE_VOLTAGE, &val);
    printk("Voltage: %d mV\n", val.voltage / 1000);

    /* Current */
    fuel_gauge_get_prop(fg, FUEL_GAUGE_CURRENT, &val);
    if (val.current < 0) {
        printk("Discharging: %d mA\n", -val.current / 1000);
    } else if (val.current > 0) {
        printk("Charging: %d mA\n", val.current / 1000);
    } else {
        printk("Idle\n");
    }

    /* Temperature */
    fuel_gauge_get_prop(fg, FUEL_GAUGE_TEMPERATURE, &val);
    int16_t temp_c = (val.temperature / 10) - 273;
    printk("Temperature: %d°C\n", temp_c);

    /* Capacity */
    fuel_gauge_get_prop(fg, FUEL_GAUGE_REMAINING_CAPACITY, &val);
    uint32_t remaining = val.remaining_capacity;
    fuel_gauge_get_prop(fg, FUEL_GAUGE_FULL_CHARGE_CAPACITY, &val);
    printk("Capacity: %u / %u mAh\n",
           remaining / 1000,
           val.full_charge_capacity / 1000);

    /* Runtime */
    fuel_gauge_get_prop(fg, FUEL_GAUGE_RUNTIME_TO_EMPTY, &val);
    if (val.runtime_to_empty != UINT16_MAX) {
        printk("Time to empty: %u minutes\n", val.runtime_to_empty);
    }
}
```

