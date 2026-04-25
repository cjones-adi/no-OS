## CMakeLists.txt Patterns

### Application CMakeLists.txt

**Minimal application** (`samples/<app>/CMakeLists.txt`):
```cmake
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(application_name)

target_sources(app PRIVATE src/main.c)
```

**With multiple source files**:
```cmake
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(sensor_app)

target_sources(app PRIVATE
    src/main.c
    src/sensor_handler.c
    src/display.c
)
```

**With conditional sources**:
```cmake
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app)

target_sources(app PRIVATE src/main.c)

if(CONFIG_USB)
    target_sources(app PRIVATE src/usb_handler.c)
endif()

if(CONFIG_BT)
    target_sources(app PRIVATE src/bluetooth.c)
endif()
```

**With include directories**:
```cmake
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(app)

target_include_directories(app PRIVATE include/)

target_sources(app PRIVATE
    src/main.c
    src/driver.c
)
```

### Driver Subsystem CMakeLists.txt

**Pattern for driver subsystem** (`drivers/<subsystem>/CMakeLists.txt`):
```cmake
# SPDX-License-Identifier: Apache-2.0

zephyr_library()

# Common subsystem code (always compiled)
zephyr_library_sources(subsystem_common.c)
zephyr_library_sources_ifdef(CONFIG_SUBSYSTEM_SHELL subsystem_shell.c)

# Individual driver sources (conditional on Kconfig)
zephyr_library_sources_ifdef(CONFIG_DRIVER_CHIP1 driver_chip1.c)
zephyr_library_sources_ifdef(CONFIG_DRIVER_CHIP2 driver_chip2.c)
zephyr_library_sources_ifdef(CONFIG_DRIVER_CHIP3 driver_chip3.c)
```

**Example: Regulator subsystem** (`drivers/regulator/CMakeLists.txt`):
```cmake
# Copyright 2020 Peter Bigot Consulting, LLC
# SPDX-License-Identifier: Apache-2.0

zephyr_library()

zephyr_library_sources(regulator_common.c)
zephyr_library_sources_ifdef(CONFIG_REGULATOR_SHELL regulator_shell.c)

zephyr_library_sources_ifdef(CONFIG_REGULATOR_PCA9420 regulator_pca9420.c)
zephyr_library_sources_ifdef(CONFIG_REGULATOR_MAX20335 regulator_max20335.c)
zephyr_library_sources_ifdef(CONFIG_REGULATOR_FIXED regulator_fixed.c)
zephyr_library_sources_ifdef(CONFIG_REGULATOR_GPIO regulator_gpio.c)
```

### Adding a New Driver to CMakeLists.txt

**Step 1**: Add driver source to `drivers/<subsystem>/CMakeLists.txt`:
```cmake
zephyr_library_sources_ifdef(CONFIG_DRIVER_MY_NEW_CHIP driver_my_new_chip.c)
```

**Step 2**: Keep alphabetically sorted (Zephyr convention):
```cmake
# zephyr-keep-sorted-start
zephyr_library_sources_ifdef(CONFIG_REGULATOR_CHIP_A regulator_chip_a.c)
zephyr_library_sources_ifdef(CONFIG_REGULATOR_MY_NEW_CHIP regulator_my_new_chip.c)
zephyr_library_sources_ifdef(CONFIG_REGULATOR_CHIP_Z regulator_chip_z.c)
# zephyr-keep-sorted-stop
```

