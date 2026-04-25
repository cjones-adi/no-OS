## Kconfig Integration

### Overview

**Kconfig** is a configuration language that manages build-time options and dependencies.

**Key Concepts**:
- **menuconfig**: Top-level subsystem option
- **config**: Individual options (bool, int, string, hex)
- **depends on**: Dependencies
- **select**: Automatically enable other options
- **default**: Default value
- **help**: Description text

### Subsystem Kconfig

**Pattern for subsystem** (`drivers/<subsystem>/Kconfig`):
```kconfig
menuconfig SUBSYSTEM
    bool "Subsystem drivers"
    help
      Include drivers for subsystem in system config

if SUBSYSTEM

config SUBSYSTEM_THREAD_SAFE
    bool "Thread-safe operations"
    depends on MULTITHREADING
    default y
    help
      Enable thread-safe reference counting for subsystem

config SUBSYSTEM_SHELL
    bool "Subsystem shell"
    depends on SHELL
    help
      Enable subsystem shell for interactive control

module = SUBSYSTEM
module-str = subsystem
source "subsys/logging/Kconfig.template.log_config"

# Include individual driver Kconfig files
source "drivers/subsystem/Kconfig.chip1"
source "drivers/subsystem/Kconfig.chip2"

endif # SUBSYSTEM
```

**Example: Regulator subsystem** (`drivers/regulator/Kconfig`):
```kconfig
menuconfig REGULATOR
    bool "Regulator drivers"
    help
      Include drivers for current/voltage regulators in system config

if REGULATOR

config REGULATOR_THREAD_SAFE_REFCNT
    bool "Thread-safe reference counting"
    depends on MULTITHREADING
    default y
    help
      When enabled, regulator reference counting is thread-safe.

config REGULATOR_SHELL
    bool "Regulator shell"
    depends on SHELL
    help
      Enable regulator shell framework

module = REGULATOR
module-str = regulator
source "subsys/logging/Kconfig.template.log_config"

source "drivers/regulator/Kconfig.pca9420"
source "drivers/regulator/Kconfig.max20335"

endif # REGULATOR
```

### Driver-Specific Kconfig

**Pattern for individual driver** (`drivers/<subsystem>/Kconfig.<chip>`):
```kconfig
config SUBSYSTEM_CHIP_NAME
    bool "Vendor CHIP driver"
    default y
    depends on DT_HAS_VENDOR_CHIP_ENABLED
    select I2C  # or SPI, GPIO, etc.
    help
      Enable the Vendor CHIP driver

if SUBSYSTEM_CHIP_NAME

config SUBSYSTEM_CHIP_NAME_INIT_PRIORITY
    int "Vendor CHIP driver init priority"
    default 75
    help
      Init priority for the driver. Must be greater than bus init priority.

endif # SUBSYSTEM_CHIP_NAME
```

**Example: PCA9420 regulator** (`drivers/regulator/Kconfig.pca9420`):
```kconfig
config REGULATOR_PCA9420
    bool "NXP PCA9420 PMIC regulator driver"
    default y
    depends on DT_HAS_NXP_PCA9420_ENABLED
    select I2C
    help
      Enable the NXP PCA9420 PMIC regulator driver

if REGULATOR_PCA9420

config REGULATOR_PCA9420_COMMON_INIT_PRIORITY
    int "NXP PCA9420 regulator driver init priority (common part)"
    default 75
    help
      Init priority for the common part. Must be greater than I2C init priority.

config REGULATOR_PCA9420_INIT_PRIORITY
    int "NXP PCA9420 regulator driver init priority"
    default 76
    help
      Init priority for the driver. Must be greater than COMMON_INIT_PRIORITY.

endif
```

### Kconfig Dependency Patterns

**Automatic enablement with devicetree**:
```kconfig
config DRIVER_CHIP
    bool "Chip driver"
    default y
    depends on DT_HAS_VENDOR_CHIP_ENABLED  # Auto-enabled if DT node present
    select I2C
```

**Optional feature**:
```kconfig
config DRIVER_CHIP_DVS
    bool "Enable DVS (Dynamic Voltage Scaling)"
    depends on DRIVER_CHIP
    help
      Enable runtime voltage scaling
```

**Multi-level dependencies**:
```kconfig
config DRIVER_ADVANCED
    bool "Advanced features"
    depends on DRIVER_CHIP && DRIVER_CHIP_DVS && MULTITHREADING
    select DYNAMIC_INTERRUPTS
```

### Adding a New Driver Kconfig

**Step 1**: Create `drivers/<subsystem>/Kconfig.<chip>`:
```kconfig
config SUBSYSTEM_MY_CHIP
    bool "Vendor MY_CHIP driver"
    default y
    depends on DT_HAS_VENDOR_MY_CHIP_ENABLED
    select I2C
    help
      Enable the Vendor MY_CHIP driver

if SUBSYSTEM_MY_CHIP

config SUBSYSTEM_MY_CHIP_INIT_PRIORITY
    int "Init priority"
    default 75
    help
      Driver initialization priority

endif
```

**Step 2**: Add source line to `drivers/<subsystem>/Kconfig`:
```kconfig
if SUBSYSTEM

# ... existing content ...

source "drivers/subsystem/Kconfig.my_chip"

endif # SUBSYSTEM
```

