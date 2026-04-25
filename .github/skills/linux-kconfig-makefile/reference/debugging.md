# Build System Debugging Reference

## Common Build Issues

### Issue 1: Driver Not Building

**Problem**: Added Kconfig/Makefile but driver doesn't build.

**Diagnosis Steps**:

**Check 1**: Verify config is enabled

```bash
grep CONFIG_AD9999 .config
# Should see: CONFIG_AD9999=y or CONFIG_AD9999=m
# If not found, config is not enabled
```

**Check 2**: Verify dependencies are met

```bash
make ARCH=arm menuconfig
# Navigate to: Device Drivers → Industrial I/O → Analog to digital converters
# Look for "AD9999" - if grayed out, dependency is missing
```

Common missing dependencies:
- `CONFIG_SPI=n` (for SPI drivers)
- `CONFIG_I2C=n` (for I2C drivers)
- `CONFIG_GPIOLIB=n` (for GPIO-using drivers)
- `CONFIG_COMMON_CLK=n` (for clock-using drivers)

**Check 3**: Verify Kconfig inclusion

```bash
# Check that subsystem Kconfig sources the driver's Kconfig
grep -r "source.*iio/adc/Kconfig" drivers/iio/

# Should find:
# drivers/iio/Kconfig: source "drivers/iio/adc/Kconfig"
```

**Check 4**: Verify Makefile syntax

```bash
# Check Makefile entry exists
grep AD9999 drivers/iio/adc/Makefile

# Should see:
# obj-$(CONFIG_AD9999) += ad9999.o
```

**Check 5**: Verify source file exists

```bash
ls -la drivers/iio/adc/ad9999.c
# Should exist
```

### Issue 2: Undefined Reference Errors

**Problem**: `undefined reference to 'ad_sd_read_reg'`

**Cause**: Missing `select` statement in Kconfig.

**Solution**: Add required library to Kconfig

```kconfig
config AD7124
	tristate "Analog Devices AD7124 ADC driver"
	depends on SPI
	select AD_SIGMA_DELTA  # <-- Add this
	select REGMAP_SPI
```

**Common Libraries to select**:
- `AD_SIGMA_DELTA` - Sigma-Delta ADC helper
- `REGMAP_SPI` - REGMAP for SPI devices
- `REGMAP_I2C` - REGMAP for I2C devices
- `IIO_BUFFER` - IIO buffering support
- `IIO_TRIGGERED_BUFFER` - Triggered buffer support

**How to Find Missing Symbol**:

```bash
# Search for the symbol in kernel source
grep -r "ad_sd_read_reg" drivers/iio/

# Example output:
# drivers/iio/adc/ad_sigma_delta.c:int ad_sd_read_reg(...)
# drivers/iio/adc/ad_sigma_delta.h:int ad_sd_read_reg(...)

# Symbol is in ad_sigma_delta, so select AD_SIGMA_DELTA
```

### Issue 3: Circular Dependency

**Problem**: `recursive dependency detected!`

**Example Error**:
```
drivers/iio/Kconfig:6:error: recursive dependency detected!
drivers/iio/Kconfig:6:	symbol IIO is selected by FOO
drivers/iio/adc/Kconfig:100:	symbol FOO depends on BAR
drivers/iio/Kconfig:50:	symbol BAR selects IIO
```

**Cause**: Circular dependency chain:
```kconfig
config FOO
	select BAR

config BAR
	depends on FOO  # Circular!
```

**Solution**: Break the cycle by changing one to `depends on` or removing the dependency.

**Prevention**: Use `depends on` for hard requirements, `select` only for helper libraries.

### Issue 4: Module Build Issues

**Problem**: Driver builds as built-in but not as module.

**Cause**: Selected library is `bool` instead of `tristate`.

**Check**:

```kconfig
config AD_SIGMA_DELTA
	bool  # <-- WRONG! Should be tristate
```

**Solution**:

```kconfig
config AD_SIGMA_DELTA
	tristate  # <-- Correct
```

**Rule**: If a driver can be a module (tristate), all `select`ed libraries must also be tristate.

### Issue 5: Driver Not in CI Build

**Problem**: CI doesn't build driver, `CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT` fails.

**Cause**: Driver not added to Kconfig.adi.

**Solution**: Add to appropriate Kconfig.adi

```kconfig
# drivers/iio/Kconfig.adi
config IIO_ALL_ADI_DRIVERS
	tristate "Build all Analog Devices IIO Drivers"
	imply AD9999  # <-- Add this
```

**Verification**:

```bash
# Load defconfig that enables all ADI drivers
make ARCH=arm zynq_xcomm_adv7511_defconfig

# Check that driver is enabled
grep AD9999 .config
# Should see: CONFIG_AD9999=y or CONFIG_AD9999=m

# Build
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# Verify object was built
ls drivers/iio/adc/ad9999.o
```

### Issue 6: Wrong Conditional in Kconfig.adi

**Problem**: Driver has dependencies but Kconfig.adi doesn't reflect them.

**Example**:

```kconfig
# Kconfig
config AD9999
	depends on SPI
	depends on GPIOLIB

# Kconfig.adi (WRONG)
imply AD9999  # Missing conditions!
```

**Solution**:

```kconfig
# Kconfig.adi (CORRECT)
imply AD9999 if (SPI && GPIOLIB)
```

**Check**: Verify all dependencies are reflected in imply condition.

### Issue 7: Symbol Not Found in .config

**Problem**: Set `CONFIG_AD9999=y` but it's not in `.config` after build.

**Cause**: Dependency not met, Kconfig silently disabled the symbol.

**Debug Steps**:

```bash
# 1. Try to enable manually
scripts/config --enable AD9999

# 2. Rebuild .config (resolves dependencies)
make ARCH=arm olddefconfig

# 3. Check if it's enabled now
grep AD9999 .config

# If still not found, check dependencies in menuconfig
make ARCH=arm menuconfig
# Navigate to driver, check why it's grayed out
```

### Issue 8: Multiple Definition Errors

**Problem**: `multiple definition of 'ad9999_probe'`

**Cause**: Source file compiled multiple times (duplicate Makefile entries).

**Check**:

```bash
grep ad9999 drivers/iio/adc/Makefile

# Bad (duplicate):
# obj-$(CONFIG_AD9999) += ad9999.o
# obj-$(CONFIG_AD9999) += ad9999.o  # <-- Duplicate!
```

**Solution**: Remove duplicate Makefile entry.

### Issue 9: Wrong Module Name

**Problem**: Module loads but with different name than expected.

**Cause**: Makefile composite object pattern.

**Example**:

```makefile
obj-$(CONFIG_AD9999) += ad9999_driver.o
ad9999_driver-y := ad9999_core.o ad9999_spi.o
```

**Result**: Module is named `ad9999_driver.ko`, not `ad9999.ko`.

**Solution**: Ensure object name matches expected module name:

```makefile
obj-$(CONFIG_AD9999) += ad9999.o
ad9999-y := ad9999_core.o ad9999_spi.o
```

## Dependency Troubleshooting

### Understanding Dependency Chains

**Example Dependency Chain**:

```kconfig
config AD7124
	depends on SPI
	select AD_SIGMA_DELTA

config AD_SIGMA_DELTA
	tristate
	select IIO_BUFFER
	select IIO_TRIGGERED_BUFFER

config IIO_TRIGGERED_BUFFER
	tristate
	select IIO_TRIGGER
	select IIO_KFIFO_BUF
```

**Chain**: `AD7124` → `AD_SIGMA_DELTA` → `IIO_BUFFER` + `IIO_TRIGGERED_BUFFER` → `IIO_TRIGGER` + `IIO_KFIFO_BUF`

**Check Full Dependency Tree**:

```bash
# Use menuconfig to see dependencies
make ARCH=arm menuconfig
# Press '?' on the symbol to see help and dependencies

# Or check with scripts/kconfig/streamline_config.pl
```

### Resolving Unmet Dependencies

**Problem**: Driver grayed out in menuconfig.

**Steps**:

1. **Find the dependency**: Press `?` on grayed-out option to see "Depends on:" line
2. **Enable dependency**: Navigate to dependency and enable it
3. **Repeat**: Some dependencies have their own dependencies

**Example**:

```
Symbol: AD7124 [=n]
Type  : tristate
Defined at drivers/iio/adc/Kconfig:123
Depends on: IIO [=y] && SPI [=n]  # <-- SPI is disabled!
```

Solution: Enable `CONFIG_SPI=y` or `CONFIG_SPI=m`.

### Platform-Specific Dependencies

**Problem**: Driver needs specific architecture.

**Example**:

```kconfig
config AXI_ADC
	depends on (ARCH_ZYNQ || ARCH_ZYNQMP || MICROBLAZE || COMPILE_TEST)
```

**Solution 1**: Build for correct architecture

```bash
make ARCH=arm zynq_xcomm_adv7511_defconfig
```

**Solution 2**: Use `COMPILE_TEST` for build testing

```bash
make defconfig
scripts/config --enable COMPILE_TEST
scripts/config --enable AXI_ADC
```

## Cross-Platform Build Testing

### Testing on Multiple Architectures

**ARM (32-bit)**:

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- zynq_xcomm_adv7511_defconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc) KCFLAGS="-Werror"
```

**ARM64 (64-bit)**:

```bash
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- adi_zynqmp_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc) KCFLAGS="-Werror"
```

**x86_64 (compile test)**:

```bash
make defconfig
scripts/config --enable COMPILE_TEST
scripts/config --enable IIO_ALL_ADI_DRIVERS
make -j$(nproc) KCFLAGS="-Werror"
```

### Architecture-Specific Issues

**Problem**: Compiles on ARM but not x86_64.

**Common Causes**:
- Architecture-specific includes (e.g., `<asm/...>`)
- Endianness assumptions
- Pointer size assumptions (32-bit vs 64-bit)
- Hardware-specific assembly

**Solution**: Use portable kernel APIs and add `|| COMPILE_TEST` to dependencies.

## Defconfig Management

### Updating Defconfig After Changes

**Workflow**:

```bash
# 1. Load existing defconfig
make ARCH=arm zynq_xcomm_adv7511_defconfig

# 2. Enable new driver
scripts/config --enable AD9999

# 3. Resolve dependencies
make ARCH=arm olddefconfig

# 4. Test build
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc)

# 5. Save minimal defconfig
make ARCH=arm savedefconfig

# 6. Update defconfig file
cp defconfig arch/arm/configs/zynq_xcomm_adv7511_defconfig

# 7. Verify changes
git diff arch/arm/configs/zynq_xcomm_adv7511_defconfig
```

### Defconfig Diff Too Large

**Problem**: `savedefconfig` creates huge diff.

**Cause**: Unnecessary config changes or Kconfig structure changes.

**Solution**:

```bash
# Start fresh
make mrproper
make ARCH=arm zynq_xcomm_adv7511_defconfig

# Make only necessary changes
scripts/config --enable AD9999

# Rebuild .config
make ARCH=arm olddefconfig

# Save
make ARCH=arm savedefconfig
cp defconfig arch/arm/configs/zynq_xcomm_adv7511_defconfig
```

### Conflicting Defconfig Changes

**Problem**: Merge conflict in defconfig file.

**Solution**: Regenerate defconfig

```bash
# 1. Take one side of the conflict
git checkout --ours arch/arm/configs/zynq_xcomm_adv7511_defconfig

# 2. Load it
make ARCH=arm zynq_xcomm_adv7511_defconfig

# 3. Apply changes from other side manually
scripts/config --enable DRIVER_FROM_OTHER_BRANCH

# 4. Regenerate
make ARCH=arm savedefconfig
cp defconfig arch/arm/configs/zynq_xcomm_adv7511_defconfig
```

## Verification Commands

### Check Symbol Definition

```bash
# Check if symbol is defined in .config
grep CONFIG_AD9999 .config

# Should see one of:
# CONFIG_AD9999=y  (built-in)
# CONFIG_AD9999=m  (module)
# # CONFIG_AD9999 is not set  (disabled)
```

### Check Object Compilation

```bash
# For built-in (=y)
ls drivers/iio/adc/ad9999.o

# For module (=m)
ls drivers/iio/adc/ad9999.ko

# Check if object is linked into vmlinux (built-in only)
nm vmlinux | grep ad9999
```

### Check Symbol Dependencies

```bash
# Use menuconfig
make ARCH=arm menuconfig
# Navigate to symbol, press '?'

# Shows:
# Symbol: AD9999 [=n]
# Type  : tristate
# Defined at drivers/iio/adc/Kconfig:123
# Depends on: IIO [=y] && SPI [=y]
# Selects: AD_SIGMA_DELTA [=n] && REGMAP_SPI [=n]
```

### Check Makefile Integration

```bash
# Verify Makefile entry
grep AD9999 drivers/iio/adc/Makefile

# Verify source file exists
ls drivers/iio/adc/ad9999.c

# Check build log for compilation
make ARCH=arm V=1 2>&1 | grep ad9999
```

## Using CI Scripts

### Local CI Build Test

```bash
# Set environment
export DEFCONFIG=zynq_xcomm_adv7511_defconfig
export ARCH=arm
export CROSS_COMPILE=arm-linux-gnueabi-
export CHECK_ALL_ADI_DRIVERS_HAVE_BEEN_BUILT=1

# Run build
./ci/travis/run-build.sh
```

### Debugging CI Failures

**Check CI Logs**:

```
ERROR: The following ADI drivers were not built:
  CONFIG_AD9999
```

**Solution**: Add to Kconfig.adi

**Check Compile Exceptions**:

```bash
# View exception list for specific defconfig
cat ci/travis/zynq_xcomm_adv7511_defconfig_compile_exceptions

# Add exception if driver legitimately can't be built on this platform
echo "CONFIG_PLATFORM_SPECIFIC_DRIVER" >> ci/travis/zynq_xcomm_adv7511_defconfig_compile_exceptions
```

## Best Practices

### 1. Test Before Submitting

```bash
# Clean build
make mrproper

# Test with ADI defconfig
make ARCH=arm zynq_xcomm_adv7511_defconfig
scripts/config --enable IIO_ALL_ADI_DRIVERS
make ARCH=arm olddefconfig
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabi- -j$(nproc) KCFLAGS="-Werror"

# Verify driver built
ls drivers/iio/adc/ad9999.o
```

### 2. Check All Architectures

Test on ARM, ARM64, and x86_64 (with COMPILE_TEST).

### 3. Run Checkpatch

```bash
./scripts/checkpatch.pl --no-tree -f drivers/iio/adc/Kconfig
./scripts/checkpatch.pl --no-tree -f drivers/iio/adc/Makefile
```

### 4. Verify Kconfig.adi Integration

Ensure driver is in Kconfig.adi with correct conditionals.

### 5. Check for Unintended Config Changes

```bash
# After savedefconfig, check diff is minimal
git diff arch/arm/configs/zynq_xcomm_adv7511_defconfig

# Should only show your driver change, not hundreds of lines
```

## References

- `scripts/config` - Config manipulation tool
- `scripts/checkpatch.pl` - Code style checker
- `ci/travis/run-build.sh` - CI build script
- [Kconfig Language Documentation](https://docs.kernel.org/kbuild/kconfig-language.html)
- [Kbuild Documentation](https://docs.kernel.org/kbuild/)
