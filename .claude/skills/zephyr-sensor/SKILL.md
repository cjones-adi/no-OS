---
name: zephyr-sensor
description: 'Complete guide to Zephyr sensor drivers for measurement devices (temperature, accelerometer, gyroscope, magnetometer, pressure, humidity, light). Use when implementing sensor drivers, working with channels and attributes, setting up triggers and interrupts, configuring FIFO buffering, implementing polling or interrupt-driven operation, or debugging sensor issues.'
---

# Zephyr Sensor Driver Development

This skill provides comprehensive understanding of the Zephyr sensor driver subsystem for measurement and monitoring devices, with extensive examples from Analog Devices sensor drivers.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement sensor driver", "sample_fetch", "channel_get", "trigger_set"
- Questions about: driver API, attr_set, init function, register access
- User mentions: implementing sensor functions, ADC conversion, data ready
- Need: detailed implementation steps (Steps 1-9) with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "sensor binding", "YAML", "overlay"
- Questions about: sensor properties, compatible strings, DT integration
- User asks: "how to define sensor binding", "devicetree example"
- Need: complete binding structure and examples

**Triggers to read reference/kconfig-cmake.md**:
- User mentions: "Kconfig", "CMakeLists", "build system", "subsystem integration"
- Questions about: adding sensor to build, CONFIG options, vendor Kconfig
- User asks: "how to integrate with build", "add to Kconfig"
- Need: Kconfig and CMake integration patterns

**Triggers to read reference/sample-apps.md**:
- User asks: "example application", "how to use sensor", "polling mode", "interrupt mode"
- Questions about: sample code, prj.conf, overlay, main.c structure
- Need: complete application examples (polling and interrupt)

**Triggers to read reference/advanced-features.md**:
- User mentions: "FIFO", "power management", "watermark", "PM", "low power"
- Questions about: FIFO support, power modes, advanced features
- Need: FIFO and PM implementation patterns

**Triggers to read reference/sensor-values.md**:
- User asks: "unit conversion", "sensor_value", "accel_ms2_to_g", "raw to SI"
- Questions about: converting values, utility functions, double conversion
- User mentions: "scaling", "LSB to m/s²", "value helpers"
- Need: sensor value conversion utilities and examples

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "multi-channel", "IMU", "design patterns"
- Questions about: register helpers, error handling, unit conversions
- Need: common patterns for sensor drivers

**Triggers to read reference/debugging.md**:
- User says: "not working", "wrong values", "debugging", "sensor issue"
- Build/runtime errors
- Questions about: device ID verification, bus communication, interrupts
- Need: debugging steps and troubleshooting

---

## When to Use This Skill

Use this skill when you need to:
- Implement sensor drivers for temperature, accelerometer, gyroscope, pressure, humidity, or light sensors
- Work with sensor channels (ACCEL_XYZ, GYRO_XYZ, TEMP, PRESS, etc.)
- Implement sensor attributes (sampling frequency, thresholds, range, ODR)
- Set up sensor triggers (data ready, threshold, motion, tap, FIFO watermark)
- Configure interrupt-driven sensor operation
- Implement FIFO buffering and watermark interrupts
- Support both polling and interrupt modes
- Add RTIO (Real-Time I/O) support for async sensor reading
- Create multi-channel sensors (IMU with accel + gyro + temp)
- Debug sensor communication or data acquisition issues
- Implement sensor power modes (standby, low-power, measurement)

## What is a Sensor?

**A sensor** is a device that measures physical properties and converts them to electrical signals that can be read by a microcontroller:

- **Environmental sensors**: Temperature, pressure, humidity
- **Motion sensors**: Accelerometer, gyroscope, magnetometer (IMU)
- **Light sensors**: Ambient light, proximity, color (RGB)
- **Specialty sensors**: Gas, particulate matter, distance, voltage/current

### Zephyr Sensor Subsystem

The Zephyr sensor subsystem provides:
- **Unified API**: Common interface for all sensor types
- **Channel-based data**: Organize sensor data by measurement type
- **Polling mode**: Read data on demand
- **Interrupt mode**: Data-ready, threshold, and motion triggers
- **FIFO support**: Buffer multiple samples for efficient reading
- **RTIO support**: Asynchronous I/O for high-performance applications

### Benefits

- **Consistent interface** – Same API across different sensor types and vendors
- **Flexible triggering** – Poll or interrupt-driven operation
- **Power efficient** – Supports low-power modes and wake-on-motion
- **Multi-channel** – Single device exposes multiple measurement types
- **Standard units** – Consistent SI units across all sensors

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│         Application Code                                   │
│    sensor_sample_fetch() / sensor_channel_get()            │
│    sensor_trigger_set() for interrupts                     │
└────────────────┬───────────────────────────────────────────┘
                 │
    ┌────────────┴──────────────┐
    │  sensor.h API             │  Channels: ACCEL_XYZ, TEMP, GYRO_XYZ
    │  (Generic Interface)      │  Triggers: DATA_READY, MOTION, THRESHOLD
    │                           │  Attributes: SAMPLING_FREQ, FULL_SCALE
    └────────────┬──────────────┘
                 │
┌────────────────┴────────────────────────┐
│                                         │
┌───▼─────────────────────┐     ┌────────▼──────────────┐
│ ADXL345 (Accelerometer) │     │  ADT7420 (Temperature)│
│ 3-axis accel + FIFO     │     │  I2C with threshold   │
│ I2C/SPI + interrupts    │     │                       │
└───┬─────────────────────┘     └────────┬──────────────┘
    │                                     │
┌───▼─────────────────────┐     ┌────────▼──────────────┐
│ I2C or SPI Driver       │     │  I2C Driver           │
└─────────────────────────┘     └───────────────────────┘
```

### Sensor Data Flow

```
1. Initialization:
   sensor_init() → Configure range, ODR, mode → Enable sensor

2. Polling Mode:
   sensor_sample_fetch() → Trigger ADC conversion → Read all channels
   sensor_channel_get() → Return cached channel values

3. Interrupt Mode:
   sensor_trigger_set() → Configure interrupt (DATA_READY, MOTION, etc.)
   [Hardware triggers interrupt]
   trigger_handler() → sensor_sample_fetch() → Process data
```

## File Structure (Quick Reference)

- **Driver**: `drivers/sensor/<vendor>/<chip>/<chip>.c`
- **Binding**: `dts/bindings/sensor/<vendor>,<chip>.yaml`
- **Kconfig**: `drivers/sensor/<vendor>/<chip>/Kconfig`
- **CMakeLists**: `drivers/sensor/<vendor>/CMakeLists.txt`
- **Headers** (optional): `drivers/sensor/<vendor>/<chip>/<chip>.h`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **sensor_value** | Standard value representation | `val1` (integer), `val2` (fractional × 10^6) |
| **sensor_driver_api** | Driver API table | `sample_fetch()`, `channel_get()`, `attr_set()`, `trigger_set()` |
| **sensor_trigger** | Trigger specification | `type` (DATA_READY, MOTION, etc.), `chan` (channel) |
| **Config structure** | Compile-time config | I2C/SPI spec, GPIO specs, devicetree properties |
| **Data structure** | Runtime state | Sample cache, trigger handler, work queue |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## Sensor Channels (Quick Reference)

Common sensor channels (from `enum sensor_channel`):

| Channel | Unit | Description |
|---------|------|-------------|
| `SENSOR_CHAN_ACCEL_XYZ` | m/s² | All 3 axes acceleration |
| `SENSOR_CHAN_GYRO_XYZ` | rad/s | All 3 axes angular velocity |
| `SENSOR_CHAN_MAGN_XYZ` | Gauss | All 3 axes magnetic field |
| `SENSOR_CHAN_DIE_TEMP` | °C | Internal die temperature |
| `SENSOR_CHAN_AMBIENT_TEMP` | °C | Ambient temperature |
| `SENSOR_CHAN_PRESS` | kPa | Pressure |
| `SENSOR_CHAN_HUMIDITY` | % | Relative humidity |
| `SENSOR_CHAN_AMBIENT_LIGHT` | lux | Visible light |
| `SENSOR_CHAN_PROX` | - | Proximity (0 or 1) |

## Sensor Attributes (Quick Reference)

Common sensor attributes (from `enum sensor_attribute`):

| Attribute | Description |
|-----------|-------------|
| `SENSOR_ATTR_SAMPLING_FREQUENCY` | Sample rate in Hz |
| `SENSOR_ATTR_FULL_SCALE` | Measurement range (e.g., ±2g, ±16g) |
| `SENSOR_ATTR_OVERSAMPLING` | Oversampling factor for noise reduction |
| `SENSOR_ATTR_UPPER_THRESH` | Upper threshold for trigger |
| `SENSOR_ATTR_LOWER_THRESH` | Lower threshold for trigger |
| `SENSOR_ATTR_SLOPE_TH` | Slope threshold for motion detection |

## Sensor Triggers (Quick Reference)

Common sensor triggers (from `enum sensor_trigger_type`):

| Trigger | When Fires |
|---------|-----------|
| `SENSOR_TRIG_DATA_READY` | New sample data available |
| `SENSOR_TRIG_THRESHOLD` | Value crosses upper/lower threshold |
| `SENSOR_TRIG_DELTA` | Value change exceeds slope threshold |
| `SENSOR_TRIG_MOTION` | Motion detected |
| `SENSOR_TRIG_TAP` | Single tap detected |
| `SENSOR_TRIG_DOUBLE_TAP` | Double tap detected |
| `SENSOR_TRIG_FIFO_WATERMARK` | FIFO reached watermark level |

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Implement Bus Abstraction** (I2C/SPI read/write helpers)
3. **Implement sample_fetch()** – Trigger conversion, read all channels
4. **Implement channel_get()** – Return cached channel values
5. **Implement attr_set()** (Optional) – Set sampling frequency, range, thresholds
6. **Implement trigger_set()** (Optional) – Configure interrupt triggers
7. **Define API Structure** with all function pointers
8. **Implement Init Function** – Initialize hardware, configure defaults
9. **Device Instantiation Macro** – `DEVICE_DT_INST_DEFINE()` with API
10. **Create Devicetree Binding** – Define sensor properties
11. **Integrate Kconfig and CMakeLists** – Add to build system

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### sensor_value Structure

```c
struct sensor_value {
    int32_t val1;  // Integer part
    int32_t val2;  // Fractional part (× 10^-6)
};

// Example: 25.123456°C
struct sensor_value temp = {
    .val1 = 25,
    .val2 = 123456
};
```

### Polling Mode

```c
int ret = sensor_sample_fetch(dev);  // Trigger conversion, read all channels
if (ret == 0) {
    struct sensor_value accel_x;
    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_X, &accel_x);
}
```

### Interrupt Mode

```c
static void trigger_handler(const struct device *dev,
                           const struct sensor_trigger *trig)
{
    sensor_sample_fetch(dev);
    // Process data
}

struct sensor_trigger trig = {
    .type = SENSOR_TRIG_DATA_READY,
    .chan = SENSOR_CHAN_ACCEL_XYZ
};
sensor_trigger_set(dev, &trig, trigger_handler);
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Use `sensor_value` structure for all measurements
- Cache sample data in `sample_fetch()`, return in `channel_get()`
- Implement all channels in single `sample_fetch()` call
- Use `SENSOR_G` macro for converting g to m/s² (9.80665 m/s²)
- Provide unit conversion helpers (`sensor_value_to_double()`, etc.)
- Use work queue for interrupt handlers if needed
- Support both polling and interrupt modes
- Document units in comments and bindings

❌ **DON'T**:
- Don't read hardware in `channel_get()` (use cached data)
- Don't block in `sample_fetch()` for extended periods
- Don't use floating point in driver code (use `sensor_value`)
- Don't forget to handle all relevant channels
- Don't ignore error codes from bus operations

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **Sensor API**: `zephyr/include/zephyr/drivers/sensor.h`
- **Sensor Drivers**: `zephyr/drivers/sensor/`
- **Bindings**: `zephyr/dts/bindings/sensor/`

**Example Drivers**:
- **ADXL345** (I2C/SPI accelerometer): `drivers/sensor/adi/adxl345/`
- **ADXL362** (SPI accelerometer with FIFO): `drivers/sensor/adi/adxl362/`
- **ADT7420** (I2C temperature): `drivers/sensor/adi/adt7420/`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-9)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Sensor binding patterns
- [reference/kconfig-cmake.md](reference/kconfig-cmake.md) – Build system integration
- [reference/sample-apps.md](reference/sample-apps.md) – Example applications (polling and interrupt)
- [reference/advanced-features.md](reference/advanced-features.md) – FIFO and power management
- [reference/sensor-values.md](reference/sensor-values.md) – Unit conversion utilities
- [reference/best-practices.md](reference/best-practices.md) – Design patterns
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide

## Summary Checklist

### Driver Implementation
- [ ] Register map defined with bit masks
- [ ] Bus abstraction (I2C/SPI read/write helpers)
- [ ] Config structure with bus specs and devicetree properties
- [ ] Data structure with sample cache and trigger handler
- [ ] `sample_fetch()` implemented (trigger conversion, read all channels)
- [ ] `channel_get()` implemented (return cached values)
- [ ] `attr_set()` implemented (optional: sampling frequency, range)
- [ ] `trigger_set()` implemented (optional: interrupts)
- [ ] API structure defined with function pointers
- [ ] Init function initializes hardware
- [ ] Device instantiation macro with API

### Devicetree and Build
- [ ] Binding created with sensor properties
- [ ] Kconfig entry with dependencies
- [ ] CMakeLists.txt integration
- [ ] Board overlay for testing

### Testing
- [ ] Polling mode works (sample_fetch + channel_get)
- [ ] Interrupt mode works (trigger_set + callback)
- [ ] Attributes can be set (sampling frequency, range)
- [ ] Unit conversions are correct
- [ ] Multi-channel sensors expose all channels
- [ ] FIFO works (if implemented)
