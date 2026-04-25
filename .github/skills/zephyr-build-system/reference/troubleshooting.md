## Build Troubleshooting

### Common Build Errors

#### 1. "west: command not found"

**Cause**: Virtual environment not activated or west not installed

**Solution**:
```bash
source .venv/bin/activate  # or .venv/Scripts/activate on Windows
pip install west
```

#### 2. "CMake Error: Could not find CMAKE_MAKE_PROGRAM"

**Cause**: Ninja or make not installed

**Solution** (Ubuntu/Debian):
```bash
sudo apt install ninja-build
```

**Solution** (Windows):
- Install Ninja via chocolatey: `choco install ninja`

#### 3. "No board named 'boardname' found"

**Cause**: Invalid board name or board not supported

**Solution**:
```bash
west boards  # List all boards
west build -b correct_board_name samples/hello_world
```

#### 4. "Devicetree error: /node: compatible not found"

**Cause**: Missing or incorrect compatible string in overlay

**Solution**: Verify compatible matches driver's DT_DRV_COMPAT:
```dts
// Driver has: #define DT_DRV_COMPAT vendor_chip
// Overlay must have:
my_device: device@addr {
    compatible = "vendor,chip";  // Note: underscore -> comma
};
```

#### 5. "undefined reference to symbol"

**Cause**: Driver source not added to CMakeLists.txt

**Solution**: Add to `drivers/<subsystem>/CMakeLists.txt`:
```cmake
zephyr_library_sources_ifdef(CONFIG_DRIVER_CHIP driver_chip.c)
```

#### 6. "CONFIG option not recognized"

**Cause**: Kconfig file not sourced or typo

**Solution**: Verify Kconfig option exists and subsystem Kconfig sources your driver's Kconfig:
```kconfig
# In drivers/<subsystem>/Kconfig
source "drivers/<subsystem>/Kconfig.my_chip"
```

#### 7. "I2C/SPI bus not ready"

**Cause**: Bus not enabled in devicetree overlay

**Solution**: Enable bus in overlay:
```dts
&i2c0 {
    status = "okay";
};
```

#### 8. "Init priority error: X initialized before Y"

**Cause**: Init priority conflicts (driver initializing before its dependencies)

**Solution**: Adjust init priority in Kconfig:
```kconfig
config DRIVER_CHIP_INIT_PRIORITY
    int "Init priority"
    default 85  # Must be > I2C (usually 60-70) and < APPLICATION (90)
```

**Init priority ranges**:
- PRE_KERNEL_1: 0-19
- PRE_KERNEL_2: 20-39
- POST_KERNEL: 40-69
- APPLICATION: 70-89
- LATE: 90-99

### Build Verification Checklist

After implementing a driver, verify:

1. **Virtual environment activated**:
   ```bash
   which west  # Should show .venv path
   ```

2. **CMakeLists.txt updated**:
   - Driver source added with `zephyr_library_sources_ifdef()`

3. **Kconfig created and sourced**:
   - `Kconfig.<chip>` exists
   - Sourced in subsystem `Kconfig`

4. **prj.conf enables subsystem**:
   ```conf
   CONFIG_SUBSYSTEM=y
   CONFIG_I2C=y  # or CONFIG_SPI=y
   ```

5. **Board overlay exists**:
   - `boards/<boardname>.overlay` with device node

6. **Build without errors**:
   ```bash
   west build -p always -b <board> samples/drivers/<subsystem>/<chip>
   ```

7. **Check build output for warnings**:
   - Review compile warnings
   - Check devicetree warnings

### Incremental Build Workflow

**Pattern for implementation**:

1. Create minimal devicetree binding
2. Create Kconfig file
3. Create minimal driver with init only
4. Add to CMakeLists.txt
5. **Build immediately** ← Catch errors early
6. Add one API function
7. **Build again** ← Verify
8. Repeat for each feature

**Build after EVERY change**, not at the end!

