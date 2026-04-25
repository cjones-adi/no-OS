# src.mk Guide

Complete guide to project-specific build configuration using src.mk files.

## Purpose of src.mk

The `src.mk` file defines:
- Device drivers needed for the project
- Generic HAL interfaces required
- Utility functions
- Optional features (IIO, networking, etc.)

## Standard src.mk Template

**Location**: `projects/PROJECT_NAME/src.mk`

```makefile
# Device-specific core drivers
INCS += $(DRIVERS)/adc/ad4692/ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/ad4692.c

# Generic no-OS API layers (Hardware Abstraction Layer)
INCS += $(INCLUDE)/no_os_spi.h
INCS += $(INCLUDE)/no_os_gpio.h
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_spi.c
SRCS += $(DRIVERS)/api/no_os_gpio.c
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
SRCS += $(NO-OS)/util/no_os_util.c

# Optional: IIO support
IIOD = y
INCS += $(DRIVERS)/adc/ad4692/iio_ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/iio_ad4692.c
```

## Key Variables

### INCS - Header Files
Adds include directories and header files:
```makefile
INCS += $(DRIVERS)/adc/ad4692/ad4692.h
INCS += $(INCLUDE)/no_os_spi.h
```

### SRCS - Source Files
Adds source files to compile:
```makefile
SRCS += $(DRIVERS)/adc/ad4692/ad4692.c
SRCS += $(DRIVERS)/api/no_os_spi.c
```

### IIOD - IIO Daemon Flag
Enables IIO framework:
```makefile
IIOD = y
```

### ENABLE_IIO_NETWORK - Network Transport
Enables IIO network transport:
```makefile
ENABLE_IIO_NETWORK = y
```

## Common HAL Interfaces

### Communication Interfaces

**SPI**:
```makefile
INCS += $(INCLUDE)/no_os_spi.h
SRCS += $(DRIVERS)/api/no_os_spi.c
```

**I2C**:
```makefile
INCS += $(INCLUDE)/no_os_i2c.h
SRCS += $(DRIVERS)/api/no_os_i2c.c
```

**UART**:
```makefile
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_uart.c
```

### Control Interfaces

**GPIO**:
```makefile
INCS += $(INCLUDE)/no_os_gpio.h
SRCS += $(DRIVERS)/api/no_os_gpio.c
```

**PWM**:
```makefile
INCS += $(INCLUDE)/no_os_pwm.h
SRCS += $(DRIVERS)/api/no_os_pwm.c
```

**IRQ**:
```makefile
INCS += $(INCLUDE)/no_os_irq.h
SRCS += $(DRIVERS)/api/no_os_irq.c
```

**Timer**:
```makefile
INCS += $(INCLUDE)/no_os_timer.h
SRCS += $(DRIVERS)/api/no_os_timer.c
```

### Utilities

**Core Utilities**:
```makefile
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_error.h
INCS += $(INCLUDE)/no_os_print_log.h
SRCS += $(NO-OS)/util/no_os_util.c
```

**Advanced Utilities**:
```makefile
# List operations
INCS += $(INCLUDE)/no_os_list.h
SRCS += $(NO-OS)/util/no_os_list.c

# Memory allocation
INCS += $(INCLUDE)/no_os_alloc.h
SRCS += $(NO-OS)/util/no_os_alloc.c

# Mutex/synchronization
INCS += $(INCLUDE)/no_os_mutex.h
SRCS += $(NO-OS)/util/no_os_mutex.c

# CRC calculations
INCS += $(INCLUDE)/no_os_crc8.h
INCS += $(INCLUDE)/no_os_crc16.h
SRCS += $(NO-OS)/util/no_os_crc8.c
SRCS += $(NO-OS)/util/no_os_crc16.c
```

## IIO Framework Integration

### Basic IIO Support

```makefile
# Enable IIO daemon
IIOD = y

# Add IIO driver variant
INCS += $(DRIVERS)/adc/ad4692/iio_ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/iio_ad4692.c
```

### IIO with Network Transport

```makefile
# Enable IIO daemon with network support
IIOD = y
ENABLE_IIO_NETWORK = y

# Add IIO driver
INCS += $(DRIVERS)/adc/ad4692/iio_ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/iio_ad4692.c
```

**Note**: IIO support is usually configured in `example.mk` rather than `src.mk` since it's example-specific.

## Conditional Compilation

### Platform-Specific Sources

```makefile
# Add sources only for specific platform
ifeq ($(PLATFORM), maxim)
    SRCS += project_specific_maxim.c
endif

ifeq ($(PLATFORM), mbed)
    SRCS += project_specific_mbed.cpp
endif
```

### Feature Flags

```makefile
# Add sources based on feature flags
ifdef ENABLE_CUSTOM_FEATURE
    INCS += $(DRIVERS)/custom/custom_feature.h
    SRCS += $(DRIVERS)/custom/custom_feature.c
endif
```

## Example: Complete ADC Project src.mk

```makefile
# Device driver - AD4692 ADC
INCS += $(DRIVERS)/adc/ad4692/ad4692.h
SRCS += $(DRIVERS)/adc/ad4692/ad4692.c

# Communication interfaces
INCS += $(INCLUDE)/no_os_spi.h
SRCS += $(DRIVERS)/api/no_os_spi.c

# Control interfaces
INCS += $(INCLUDE)/no_os_gpio.h
SRCS += $(DRIVERS)/api/no_os_gpio.c

# UART for console
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
INCS += $(INCLUDE)/no_os_error.h
SRCS += $(NO-OS)/util/no_os_util.c
```

## Example: Complete DAC Project src.mk

```makefile
# Device driver - AD5791 DAC
INCS += $(DRIVERS)/dac/ad5791/ad5791.h
SRCS += $(DRIVERS)/dac/ad5791/ad5791.c

# Communication interfaces
INCS += $(INCLUDE)/no_os_spi.h
SRCS += $(DRIVERS)/api/no_os_spi.c

# Control interfaces
INCS += $(INCLUDE)/no_os_gpio.h
SRCS += $(DRIVERS)/api/no_os_gpio.c

# UART for console
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
INCS += $(INCLUDE)/no_os_error.h
SRCS += $(NO-OS)/util/no_os_util.c
```

## Example: PMIC/Power Project src.mk

```makefile
# Device driver - MAX20370 PMIC
INCS += $(DRIVERS)/power/max20370/max20370.h
SRCS += $(DRIVERS)/power/max20370/max20370.c

# Regulator support
INCS += $(DRIVERS)/power/max20370/max20370-regulator.h
SRCS += $(DRIVERS)/power/max20370/max20370-regulator.c

# Communication interfaces
INCS += $(INCLUDE)/no_os_i2c.h
SRCS += $(DRIVERS)/api/no_os_i2c.c

# Control interfaces
INCS += $(INCLUDE)/no_os_gpio.h
SRCS += $(DRIVERS)/api/no_os_gpio.c

# IRQ handling
INCS += $(INCLUDE)/no_os_irq.h
SRCS += $(DRIVERS)/api/no_os_irq.c

# UART for console
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
INCS += $(INCLUDE)/no_os_error.h
INCS += $(INCLUDE)/no_os_alloc.h
SRCS += $(NO-OS)/util/no_os_util.c
SRCS += $(NO-OS)/util/no_os_alloc.c
```

## Path Variables Reference

### $(NO-OS)
Root directory of no-OS framework:
```makefile
$(NO-OS)/util/no_os_util.c
```

### $(INCLUDE)
Include directory for generic headers:
```makefile
$(INCLUDE)/no_os_spi.h
$(INCLUDE)/no_os_gpio.h
```

### $(DRIVERS)
Drivers directory:
```makefile
$(DRIVERS)/adc/ad4692/ad4692.h
$(DRIVERS)/api/no_os_spi.c
```

### $(PLATFORM_DRIVERS)
Platform-specific drivers (auto-set based on PLATFORM):
```makefile
$(PLATFORM_DRIVERS)/maxim_spi.h
```

## Best Practices

**DO**:
- Include only what you need
- Add headers to INCS
- Add implementations to SRCS
- Use path variables ($(DRIVERS), $(INCLUDE), $(NO-OS))
- Group by function (device, HAL, utilities)
- Comment sections

**DON'T**:
- Include platform-specific drivers (use platform_src.mk)
- Hardcode absolute paths
- Duplicate includes
- Add .mk files to SRCS
- Mix example-specific code (use example.mk)

## Common Patterns

### Minimal src.mk (Simple Device)
```makefile
# Device driver
INCS += $(DRIVERS)/sensor/adxl345/adxl345.h
SRCS += $(DRIVERS)/sensor/adxl345/adxl345.c

# Communication
INCS += $(INCLUDE)/no_os_i2c.h
SRCS += $(DRIVERS)/api/no_os_i2c.c

# Console
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_uart.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
SRCS += $(NO-OS)/util/no_os_util.c
```

### Complex src.mk (Multi-Device System)
```makefile
# Primary ADC
INCS += $(DRIVERS)/adc/ad7124/ad7124.h
SRCS += $(DRIVERS)/adc/ad7124/ad7124.c

# Secondary DAC
INCS += $(DRIVERS)/dac/ad5791/ad5791.h
SRCS += $(DRIVERS)/dac/ad5791/ad5791.c

# Communication interfaces
INCS += $(INCLUDE)/no_os_spi.h
INCS += $(INCLUDE)/no_os_i2c.h
INCS += $(INCLUDE)/no_os_uart.h
SRCS += $(DRIVERS)/api/no_os_spi.c
SRCS += $(DRIVERS)/api/no_os_i2c.c
SRCS += $(DRIVERS)/api/no_os_uart.c

# Control
INCS += $(INCLUDE)/no_os_gpio.h
INCS += $(INCLUDE)/no_os_irq.h
SRCS += $(DRIVERS)/api/no_os_gpio.c
SRCS += $(DRIVERS)/api/no_os_irq.c

# Utilities
INCS += $(INCLUDE)/no_os_util.h
INCS += $(INCLUDE)/no_os_delay.h
INCS += $(INCLUDE)/no_os_print_log.h
INCS += $(INCLUDE)/no_os_list.h
INCS += $(INCLUDE)/no_os_alloc.h
SRCS += $(NO-OS)/util/no_os_util.c
SRCS += $(NO-OS)/util/no_os_list.c
SRCS += $(NO-OS)/util/no_os_alloc.c
```

## Troubleshooting

**"No rule to make target $(DRIVERS)/..."**:
- Verify driver path is correct
- Check driver file exists
- Ensure variables are spelled correctly

**"Undefined reference to 'no_os_spi_init'"**:
- Add $(DRIVERS)/api/no_os_spi.c to SRCS
- Don't just include the header

**Platform drivers in src.mk**:
- Move to platform_src.mk
- src.mk is for device drivers only

**Duplicate symbols**:
- Check for duplicate entries in SRCS
- Verify same source not in platform_src.mk
