## Best Practices

### 1. Always Use Virtual Environment
```bash
# EVERY terminal session, before any west command:
source .venv/bin/activate
```

### 2. Clean Builds for Major Changes
```bash
west build -p always -b <board> <app>
```

### 3. Incremental Development
- Build after each small change
- Don't wait until "complete" to test build

### 4. Use Logging for Debugging
```conf
CONFIG_LOG=y
CONFIG_<SUBSYSTEM>_LOG_LEVEL_DBG=y
```

### 5. Check Dependencies
- I2C/SPI driver needs `CONFIG_I2C=y` or `CONFIG_SPI=y`
- GPIO needs `CONFIG_GPIO=y`
- Thread-safety needs `CONFIG_MULTITHREADING=y`

### 6. Init Priorities Matter
- Driver must initialize AFTER its bus (I2C, SPI)
- Driver must initialize BEFORE consumers
- Typical: I2C=60, Driver=75, Application=90

### 7. Keep Sorted
```cmake
# zephyr-keep-sorted-start
zephyr_library_sources_ifdef(CONFIG_A driver_a.c)
zephyr_library_sources_ifdef(CONFIG_B driver_b.c)
zephyr_library_sources_ifdef(CONFIG_C driver_c.c)
# zephyr-keep-sorted-stop
```

