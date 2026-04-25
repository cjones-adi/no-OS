## Sample Application Pattern

### Directory Structure

```
samples/sensor/<sensor_name>/
├── CMakeLists.txt
├── prj.conf
├── README.rst
├── sample.yaml
├── src/
│   └── main.c
└── boards/
    ├── nrf52840dk_nrf52840.overlay
    └── nucleo_f767zi.overlay
```

### Sample main.c (Polling Mode)

**Example from ADT7420 sample** (simplified):

```c
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <stdio.h>

#define SENSOR_NODE DT_NODELABEL(adt7420)

int main(void)
{
    const struct device *dev = DEVICE_DT_GET(SENSOR_NODE);
    struct sensor_value temp;
    int ret;

    if (!device_is_ready(dev)) {
        printf("Sensor device not ready\n");
        return -ENODEV;
    }

    while (1) {
        // Fetch sensor data
        ret = sensor_sample_fetch(dev);
        if (ret) {
            printf("sensor_sample_fetch failed: %d\n", ret);
            k_sleep(K_SECONDS(1));
            continue;
        }

        // Get temperature channel
        ret = sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &temp);
        if (ret) {
            printf("sensor_channel_get failed: %d\n", ret);
            k_sleep(K_SECONDS(1));
            continue;
        }

        // Print temperature
        printf("Temperature: %d.%06d °C\n", temp.val1, temp.val2);

        k_sleep(K_SECONDS(2));
    }

    return 0;
}
```

### Sample main.c (Interrupt Mode)

**Example from ADT7420 with threshold trigger**:

```c
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <stdio.h>

#define SENSOR_NODE DT_NODELABEL(adt7420)

static K_SEM_DEFINE(sem, 0, 1);

static void trigger_handler(const struct device *dev,
                            const struct sensor_trigger *trigger)
{
    k_sem_give(&sem);
}

int main(void)
{
    const struct device *dev = DEVICE_DT_GET(SENSOR_NODE);
    struct sensor_value temp, threshold;
    struct sensor_trigger trig;
    int ret;

    if (!device_is_ready(dev)) {
        printf("Sensor device not ready\n");
        return -ENODEV;
    }

    // Set threshold to 25°C
    threshold.val1 = 25;
    threshold.val2 = 0;
    ret = sensor_attr_set(dev, SENSOR_CHAN_AMBIENT_TEMP,
                         SENSOR_ATTR_UPPER_THRESH, &threshold);
    if (ret) {
        printf("Failed to set upper threshold: %d\n", ret);
    }

    // Set lower threshold to 20°C
    threshold.val1 = 20;
    threshold.val2 = 0;
    ret = sensor_attr_set(dev, SENSOR_CHAN_AMBIENT_TEMP,
                         SENSOR_ATTR_LOWER_THRESH, &threshold);
    if (ret) {
        printf("Failed to set lower threshold: %d\n", ret);
    }

    // Configure trigger
    trig.type = SENSOR_TRIG_THRESHOLD;
    trig.chan = SENSOR_CHAN_AMBIENT_TEMP;

    ret = sensor_trigger_set(dev, &trig, trigger_handler);
    if (ret) {
        printf("Failed to set trigger: %d\n", ret);
        return ret;
    }

    printf("Waiting for temperature to cross thresholds (20-25°C)...\n");

    while (1) {
        k_sem_take(&sem, K_FOREVER);

        ret = sensor_sample_fetch(dev);
        if (ret == 0) {
            sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &temp);
            printf("Alert! Temperature: %d.%06d °C\n", temp.val1, temp.val2);
        }
    }

    return 0;
}
```

### prj.conf

```conf
CONFIG_SENSOR=y
CONFIG_I2C=y

# Enable logging
CONFIG_LOG=y
CONFIG_SENSOR_LOG_LEVEL_DBG=y
CONFIG_I2C_LOG_LEVEL_DBG=y

# Enable console
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y
```

### Board Overlay

**nrf52840dk_nrf52840.overlay**:
```dts
&i2c0 {
    status = "okay";

    adt7420: adt7420@48 {
        compatible = "adi,adt7420";
        reg = <0x48>;
        int-gpios = <&gpio0 11 GPIO_ACTIVE_LOW>;
    };
};
```

**adxl345 overlay** (with interrupts):
```dts
&i2c1 {
    status = "okay";

    adxl345: adxl345@1d {
        compatible = "adi,adxl345-i2c";
        reg = <0x1d>;
        int1-gpios = <&gpio0 11 (GPIO_PULL_UP | GPIO_ACTIVE_HIGH)>;
        range = <ADXL345_DT_RANGE_8G>;
        odr = <ADXL345_DT_ODR_100>;
    };
};
```

