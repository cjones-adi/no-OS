## Kconfig Integration

### Subsystem Kconfig

`drivers/sensor/Kconfig`:
```kconfig
menuconfig SENSOR
    bool "Sensor drivers"
    help
      Include sensor drivers in system config

if SENSOR

module = SENSOR
module-str = sensor
source "subsys/logging/Kconfig.template.log_config"

config SENSOR_INIT_PRIORITY
    int "Sensor init priority"
    default 90
    help
      Sensor initialization priority. Must be greater than I2C/SPI init priority.

config SENSOR_ASYNC_API
    bool "Sensor asynchronous API"
    select RTIO
    help
      Enable asynchronous sensor API using RTIO.

rsource "adi/Kconfig"
rsource "bosch/Kconfig"
# ... other vendors

endif # SENSOR
```

### Driver-Specific Kconfig

`drivers/sensor/adi/adxl345/Kconfig`:
```kconfig
# ADXL345 3-Axis Digital Accelerometer
# Copyright (c) 2020 Antmicro
# SPDX-License-Identifier: Apache-2.0

config ADXL345
    bool "ADXL345 Three Axis accelerometer"
    default y
    depends on DT_HAS_ADI_ADXL345_ENABLED
    select I2C if $(dt_compat_on_bus,$(DT_COMPAT_ADI_ADXL345),i2c)
    select SPI if $(dt_compat_on_bus,$(DT_COMPAT_ADI_ADXL345),spi)
    select RTIO_WORKQ if SENSOR_ASYNC_API
    help
      Enable driver for ADXL345 3-axis accelerometer.

if ADXL345

config ADXL345_ACCEL_RANGE_RUNTIME
    bool "Select range at runtime"
    help
      Enable runtime selection of accelerometer range via attr_set.

choice ADXL345_TRIGGER_MODE
    prompt "Trigger mode"
    default ADXL345_TRIGGER_NONE
    help
      Specify interrupt triggering mode.

config ADXL345_TRIGGER_NONE
    bool "No trigger"

config ADXL345_TRIGGER_GLOBAL_THREAD
    bool "Use global thread"
    depends on GPIO
    select ADXL345_TRIGGER

config ADXL345_TRIGGER_OWN_THREAD
    bool "Use own thread"
    depends on GPIO
    select ADXL345_TRIGGER

endchoice

config ADXL345_TRIGGER
    bool

config ADXL345_THREAD_PRIORITY
    int "Thread priority"
    depends on ADXL345_TRIGGER_OWN_THREAD
    default 10
    help
      Priority of thread used by interrupt handler.

config ADXL345_THREAD_STACK_SIZE
    int "Thread stack size"
    depends on ADXL345_TRIGGER_OWN_THREAD
    default 1024
    help
      Stack size of thread used by interrupt handler.

config ADXL345_STREAM
    bool "Enable RTIO stream support"
    depends on SENSOR_ASYNC_API
    help
      Enable RTIO-based streaming with FIFO support.

endif # ADXL345
```

## CMakeLists.txt Integration

### Sensor Subsystem Level

`drivers/sensor/CMakeLists.txt`:
```cmake
# SPDX-License-Identifier: Apache-2.0

# zephyr-keep-sorted-start
add_subdirectory(adi)
add_subdirectory(bosch)
add_subdirectory(st)
# ... other vendors
# zephyr-keep-sorted-stop
```

### Vendor Level

`drivers/sensor/adi/CMakeLists.txt`:
```cmake
# SPDX-License-Identifier: Apache-2.0

# zephyr-keep-sorted-start
add_subdirectory_ifdef(CONFIG_AD2S1210 ad2s1210)
add_subdirectory_ifdef(CONFIG_ADLTC2990 adltc2990)
add_subdirectory_ifdef(CONFIG_ADT7310 adt7310)
add_subdirectory_ifdef(CONFIG_ADT7420 adt7420)
add_subdirectory_ifdef(CONFIG_ADXL345 adxl345)
add_subdirectory_ifdef(CONFIG_ADXL362 adxl362)
add_subdirectory_ifdef(CONFIG_ADXL367 adxl367)
add_subdirectory_ifdef(CONFIG_ADXL372 adxl372)
# zephyr-keep-sorted-stop
```

### Driver Level

`drivers/sensor/adi/adxl345/CMakeLists.txt`:
```cmake
# SPDX-License-Identifier: Apache-2.0

zephyr_library()

zephyr_library_sources(adxl345.c)
zephyr_library_sources_ifdef(CONFIG_ADXL345_TRIGGER adxl345_trigger.c)
zephyr_library_sources_ifdef(CONFIG_ADXL345_STREAM adxl345_stream.c)
zephyr_library_sources_ifdef(CONFIG_ADXL345_STREAM adxl345_rtio.c)
zephyr_library_sources_ifdef(CONFIG_ADXL345_STREAM adxl345_decoder.c)
```

