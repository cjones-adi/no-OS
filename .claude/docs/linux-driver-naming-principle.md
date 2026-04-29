# Linux Driver Naming Principle for no-OS Development

## 🚨 Core Principle

> **Linux drivers must not rely on generic or wildcard‑style names to represent multiple devices. The kernel driver model requires explicit device matching via ID tables or device tree compatibles, and device naming stability is intentionally delegated to user space.**

This principle applies to all no-OS driver development, ensuring compatibility with Linux kernel standards and proper device identification.

## ❌ Prohibited Patterns

### Branch Names
```bash
# WRONG - Generic/wildcard patterns
git checkout -b dev/ad717x          # Generic family name
git checkout -b dev/ltm470x         # Wildcard-style name
git checkout -b dev/power-device    # Category-based name
git checkout -b dev/adc-driver      # Function-based name
git checkout -b dev/sensor-generic  # Generic designation
```

### Driver Names
```c
// WRONG - Generic structure names
struct sensor_dev;
struct power_controller_dev;
struct adc_driverX_dev;
```

### File Names
```bash
# WRONG - Generic file naming
drivers/power/power_controller.h
drivers/adc/generic_adc.c
drivers/sensor/sensor_familyX.h
```

## ✅ Correct Linux-Compliant Patterns

### Branch Names
```bash
# CORRECT - Explicit device names
git checkout -b dev/ltm4700         # Primary device in LTM470x family
git checkout -b dev/adm1275         # Specific PMBus device
git checkout -b dev/ad7175          # Specific ADC (even if supporting AD7176/7177)
git checkout -b dev/max31865        # Explicit temperature sensor
```

### Driver Implementation
```c
// CORRECT - Specific device structures
struct ltm4700_dev {
    uint8_t chip_id;    // Explicit device identification
    // ... device-specific members
};

struct adm1275_dev {
    uint8_t device_variant;  // Explicit variant tracking
    // ... device-specific members
};
```

### File Structure
```bash
# CORRECT - Specific device naming
drivers/power/ltm4700/
├── ltm4700.h           # Primary device name
├── ltm4700.c           # Supports LTM4700, LTM4777 via chip_id
└── iio_ltm4700.h       # IIO interface

drivers/adc/ad7175/
├── ad7175.h            # Primary device name
├── ad7175.c            # Supports AD7175/AD7176/AD7177 via chip_id
└── README.rst
```

## 🔧 Implementation Strategies

### 1. Family Driver with Explicit Identification
```c
// Use primary device name, detect variants via chip_id
struct ltm4700_dev {
    uint8_t chip_id;           // 0x01 = LTM4700, 0x02 = LTM4777
    enum ltm4700_variant {
        LTM4700_VARIANT,
        LTM4777_VARIANT
    } variant;
};

int32_t ltm4700_init(struct ltm4700_dev **device, struct ltm4700_init_param init_param)
{
    // Detect specific device via chip ID register
    ret = ltm4700_read_chip_id(dev, &chip_id);
    switch (chip_id) {
    case 0x01:
        dev->variant = LTM4700_VARIANT;
        break;
    case 0x02:
        dev->variant = LTM4777_VARIANT;
        break;
    default:
        return -ENODEV;
    }
}
```

### 2. Device Tree Compatibility (for Linux projects)
```c
// Explicit device matching - no wildcards
static const struct of_device_id ltm4700_of_match[] = {
    { .compatible = "adi,ltm4700", .data = (void*)LTM4700_VARIANT },
    { .compatible = "adi,ltm4777", .data = (void*)LTM4777_VARIANT },
    { /* sentinel */ }
};
```

### 3. Project Naming
```bash
# CORRECT - Use primary device name
projects/ltm4700-eval/          # Primary device name
projects/adm1275-eval/          # Specific device name
projects/ad7175-eval/           # Primary family device

# Documentation reflects supported variants
projects/ltm4700-eval/README.rst:
"Supports LTM4700 and LTM4777 devices via automatic chip ID detection"
```

## 📋 Documentation Requirements

### Driver Headers
```c
/**
 * @file   ltm4700.h
 * @brief  LTM4700/LTM4777 Family Power Module Driver
 *
 * Supports both LTM4700 and LTM4777 devices through explicit
 * chip ID detection. Device variant is determined at initialization
 * and stored in device structure for runtime decisions.
 */
```

### README Documentation
```rst
LTM4700 Family Driver
=====================

**Supported Devices:**
- LTM4700 (Primary device, chip_id=0x01)
- LTM4777 (Variant device, chip_id=0x02)

**Device Detection:**
Device variant is automatically detected via MFR_MODEL PMBus command
during initialization. No user configuration required.
```

## 🎯 Benefits of This Approach

1. **Linux Kernel Compatibility**: Aligns with kernel driver model requirements
2. **Clear Device Identification**: Explicit chip ID detection prevents ambiguity
3. **Stable Naming**: Device names remain consistent across kernel versions
4. **User Space Delegation**: Device enumeration handled by appropriate subsystems
5. **Maintainable Code**: Clear device-specific logic paths
6. **Documentation Clarity**: Explicit supported device lists

## ⚠️ Migration Guidelines

### For Existing Generic Names
1. **Identify primary device** in family (usually first or most common)
2. **Rename branch** to primary device name (`dev/ltm470x` → `dev/ltm4700`)
3. **Update file names** to use primary device (`ltm470x.h` → `ltm4700.h`)
4. **Add chip_id detection** for device variant identification
5. **Update documentation** to list all supported devices explicitly

### For New Drivers
1. **Start with specific device name** from datasheet
2. **Design chip_id detection** if family support planned
3. **Use primary device name** for all files and branches
4. **Document supported variants** explicitly in README

---

**Enforcement:** This principle is enforced by pre-commit hooks and review checkers. Generic device names will trigger CI failures and review comments.