## Sensor Value Utility Functions

The Zephyr sensor API provides utility functions to convert between `sensor_value` and other formats, as well as unit conversions for common measurements.

### Converting to sensor_value

```c
#include <zephyr/drivers/sensor.h>

/* From double (floating point) */
struct sensor_value temp;
sensor_value_from_double(&temp, 25.6);  // temp.val1=25, temp.val2=600000

/* From float */
struct sensor_value pressure;
sensor_value_from_float(&pressure, 1013.25f);  // pressure.val1=1013, pressure.val2=250000

/* From milli units (e.g., millivolts) */
struct sensor_value voltage;
sensor_value_from_milli(&voltage, 3300);  // 3300mV → 3.3V

/* From micro units (e.g., micrograms) */
struct sensor_value particulate;
sensor_value_from_micro(&particulate, 25000000);  // 25000000µg → 25.0g
```

**Use cases**:
- Setting sensor attributes from floating-point values
- Converting external measurements to sensor_value format
- Test fixtures with precise floating-point values

### Converting from sensor_value

```c
/* To double */
double temp_c = (double)temp.val1 + (double)temp.val2 / 1000000.0;

/* To float */
float pressure_kpa = (float)pressure.val1 + (float)pressure.val2 / 1000000.0f;

/* To integer (truncate fractional part) */
int32_t temp_int = temp.val1;

/* To millis */
int64_t voltage_mv = (int64_t)voltage.val1 * 1000 + voltage.val2 / 1000;
```

### Accelerometer Unit Conversions

For accelerometer data, convert between m/s² and g (gravitational acceleration):

```c
struct sensor_value accel_xyz[3];

/* Fetch accelerometer data (in m/s²) */
sensor_sample_fetch_chan(dev, SENSOR_CHAN_ACCEL_XYZ);
sensor_channel_get(dev, SENSOR_CHAN_ACCEL_XYZ, accel_xyz);

/* Convert m/s² to milli-g (mg) */
int32_t accel_x_mg = sensor_ms2_to_mg(&accel_xyz[0]);
int32_t accel_y_mg = sensor_ms2_to_mg(&accel_xyz[1]);
int32_t accel_z_mg = sensor_ms2_to_mg(&accel_xyz[2]);

printf("Accel: %d mg, %d mg, %d mg\n", accel_x_mg, accel_y_mg, accel_z_mg);

/* Convert m/s² to micro-g (µg) for ultra-low acceleration */
int32_t accel_x_ug = sensor_ms2_to_ug(&accel_xyz[0]);

/* Convert m/s² to g (integers) */
int32_t accel_x_g = sensor_ms2_to_g(&accel_xyz[0]);

/* Convert g to m/s² (for setting thresholds) */
struct sensor_value threshold_2g;
sensor_g_to_ms2(2, &threshold_2g);  // 2g → 19.6 m/s²

/* Convert µg to m/s² (for ultra-low values) */
struct sensor_value low_threshold;
sensor_ug_to_ms2(500000, &low_threshold);  // 500000µg = 0.5g → 4.9 m/s²
```

**Common use cases**:
- Display accelerometer data in familiar g units
- Set motion detection thresholds in g
- Ultra-precision measurements in µg for seismic sensors
- Comparing measurements across different accelerometers

### Gyroscope Unit Conversions

For gyroscope data, convert between rad/s and degrees:

```c
struct sensor_value gyro_xyz[3];

/* Fetch gyroscope data (in rad/s) */
sensor_sample_fetch_chan(dev, SENSOR_CHAN_GYRO_XYZ);
sensor_channel_get(dev, SENSOR_CHAN_GYRO_XYZ, gyro_xyz);

/* Convert rad/s to degrees/s */
int32_t gyro_x_deg = sensor_rad_to_degrees(&gyro_xyz[0]);
int32_t gyro_y_deg = sensor_rad_to_degrees(&gyro_xyz[1]);
int32_t gyro_z_deg = sensor_rad_to_degrees(&gyro_xyz[2]);

printf("Gyro: %d °/s, %d °/s, %d °/s\n", gyro_x_deg, gyro_y_deg, gyro_z_deg);

/* Convert rad/s to 10 micro-degrees/s (ultra-precision) */
int32_t gyro_x_10udeg = sensor_rad_to_10udegrees(&gyro_xyz[0]);

/* Convert degrees to rad/s (for setting rate thresholds) */
struct sensor_value rate_threshold;
sensor_degrees_to_rad(90, &rate_threshold);  // 90°/s → 1.57 rad/s
```

**Common use cases**:
- Display rotation rate in degrees per second
- Detect rapid rotation (e.g., drop detection)
- Navigation and orientation tracking
- Setting rotation thresholds in intuitive degrees units

### Complete Example: Application with Unit Conversions

```c
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>

int main(void)
{
    const struct device *imu = DEVICE_DT_GET(DT_NODELABEL(adxl345));
    struct sensor_value accel[3], threshold;

    if (!device_is_ready(imu)) {
        return -ENODEV;
    }

    /* Set motion threshold: 1.5g in m/s² */
    sensor_value_from_double(&threshold, 14.715);  // 1.5g = 14.715 m/s²
    /* Or use helper: sensor_g_to_ms2(1.5, &threshold); -- needs float support */

    sensor_attr_set(imu, SENSOR_CHAN_ACCEL_XYZ,
                    SENSOR_ATTR_SLOPE_TH, &threshold);

    while (1) {
        /* Fetch and display acceleration */
        sensor_sample_fetch(imu);
        sensor_channel_get(imu, SENSOR_CHAN_ACCEL_XYZ, accel);

        /* Display in milli-g (easier to read than m/s²) */
        printk("Accel: %d mg, %d mg, %d mg\n",
               sensor_ms2_to_mg(&accel[0]),
               sensor_ms2_to_mg(&accel[1]),
               sensor_ms2_to_mg(&accel[2]));

        /* Check if acceleration exceeds threshold */
        int32_t magnitude_mg = 0;
        for (int i = 0; i < 3; i++) {
            int32_t val_mg = sensor_ms2_to_mg(&accel[i]);
            magnitude_mg += val_mg * val_mg;
        }
        /* sqrt approximation: if any axis > 1000mg, motion detected */
        for (int i = 0; i < 3; i++) {
            if (abs(sensor_ms2_to_mg(&accel[i])) > 1000) {
                printk("Motion detected!\n");
                break;
            }
        }

        k_sleep(K_MSEC(100));
    }
}
```

### Summary of Utility Functions

| Function | Purpose | Input → Output |
|----------|---------|----------------|
| `sensor_value_from_double()` | Double to sensor_value | `double` → `sensor_value` |
| `sensor_value_from_float()` | Float to sensor_value | `float` → `sensor_value` |
| `sensor_value_from_milli()` | Milli-units to sensor_value | `int64_t` millis → `sensor_value` |
| `sensor_value_from_micro()` | Micro-units to sensor_value | `int64_t` micros → `sensor_value` |
| `sensor_ms2_to_g()` | Acceleration to g | `sensor_value` m/s² → `int32_t` g |
| `sensor_g_to_ms2()` | g to acceleration | `int32_t` g → `sensor_value` m/s² |
| `sensor_ms2_to_mg()` | Acceleration to milli-g | `sensor_value` m/s² → `int32_t` mg |
| `sensor_ms2_to_ug()` | Acceleration to micro-g | `sensor_value` m/s² → `int32_t` µg |
| `sensor_ug_to_ms2()` | Micro-g to acceleration | `int32_t` µg → `sensor_value` m/s² |
| `sensor_rad_to_degrees()` | Radians to degrees | `sensor_value` rad/s → `int32_t` °/s |
| `sensor_degrees_to_rad()` | Degrees to radians | `int32_t` °/s → `sensor_value` rad/s |
| `sensor_rad_to_10udegrees()` | Radians to 10µ° | `sensor_value` rad/s → `int32_t` 10µ°/s |

**Header**: `#include <zephyr/drivers/sensor.h>` (all utility functions are static inline)

