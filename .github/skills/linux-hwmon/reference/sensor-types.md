# HWMON Sensor Types and Units

Complete reference for all HWMON sensor types, standard units, and attribute bitmasks.

## Sensor Type Overview

```c
enum hwmon_sensor_types {
	hwmon_chip,       // Chip-level attributes (update_interval, alarms)
	hwmon_temp,       // Temperature sensors
	hwmon_in,         // Voltage inputs
	hwmon_curr,       // Current sensors
	hwmon_power,      // Power sensors
	hwmon_energy,     // Energy counters
	hwmon_humidity,   // Humidity sensors
	hwmon_fan,        // Fan tachometers
	hwmon_pwm,        // PWM outputs
	hwmon_intrusion,  // Chassis intrusion
	hwmon_max         // Sentinel value
};
```

## Temperature (hwmon_temp)

**Units**: **millidegrees Celsius** (m°C)

### Attribute Bitmasks

```c
HWMON_T_INPUT           // Current temperature (read-only)
HWMON_T_MIN             // Minimum threshold
HWMON_T_MAX             // Maximum threshold
HWMON_T_CRIT            // Critical threshold
HWMON_T_CRIT_HYST       // Critical hysteresis
HWMON_T_LCRIT           // Low critical threshold
HWMON_T_ALARM           // Alarm flag (0/1)
HWMON_T_MIN_ALARM       // Min alarm flag
HWMON_T_MAX_ALARM       // Max alarm flag
HWMON_T_CRIT_ALARM      // Critical alarm flag
HWMON_T_FAULT           // Sensor fault flag
HWMON_T_LABEL           // Channel label (string)
```

### Sysfs Filenames

```
temp[1-*]_input         // Temperature in m°C
temp[1-*]_min           // Minimum threshold
temp[1-*]_max           // Maximum threshold
temp[1-*]_crit          // Critical threshold
temp[1-*]_alarm         // Alarm status
temp[1-*]_label         // Channel name
```

### Example Conversion

```c
// Hardware returns 16-bit value: temperature = -45°C + (raw * 175 / 65535)
*val = -45000 + ((int32_t)raw_value * 175000) / 65535;

// Example: 25°C = 25000 m°C
```

## Voltage (hwmon_in)

**Units**: **millivolts** (mV)

### Attribute Bitmasks

```c
HWMON_I_INPUT           // Current voltage (read-only)
HWMON_I_MIN             // Minimum threshold
HWMON_I_MAX             // Maximum threshold
HWMON_I_LCRIT           // Low critical threshold
HWMON_I_CRIT            // Critical threshold
HWMON_I_AVERAGE         // Average voltage
HWMON_I_ALARM           // Alarm flag
HWMON_I_LABEL           // Channel label
```

### Sysfs Filenames

```
in[0-*]_input           // Voltage in mV
in[0-*]_min             // Minimum threshold
in[0-*]_max             // Maximum threshold
in[0-*]_alarm           // Alarm status
in[0-*]_label           // Channel name
```

**Note**: Voltage channels start at index 0 (unlike temperature starting at 1).

### Example Values

```c
// 3.3V rail: 3300 mV
// 1.8V rail: 1800 mV
// 12V rail: 12000 mV
```

## Current (hwmon_curr)

**Units**: **milliamperes** (mA)

### Attribute Bitmasks

```c
HWMON_C_INPUT           // Current in mA
HWMON_C_MIN             // Minimum threshold
HWMON_C_MAX             // Maximum threshold
HWMON_C_CRIT            // Critical threshold
HWMON_C_AVERAGE         // Average current
HWMON_C_ALARM           // Alarm flag
HWMON_C_LABEL           // Channel label
```

### Sysfs Filenames

```
curr[1-*]_input         // Current in mA
curr[1-*]_max           // Maximum threshold
curr[1-*]_alarm         // Alarm status
```

### Example Values

```c
// 500 mA = 500
// 1.5 A = 1500 mA
```

## Power (hwmon_power)

**Units**: **microwatts** (µW)

### Attribute Bitmasks

```c
HWMON_P_INPUT           // Instantaneous power in µW
HWMON_P_AVERAGE         // Average power
HWMON_P_CAP             // Power cap limit
HWMON_P_CAP_MAX         // Maximum power cap
HWMON_P_MAX             // Maximum power threshold
HWMON_P_CRIT            // Critical power threshold
HWMON_P_ALARM           // Alarm flag
HWMON_P_LABEL           // Channel label
```

### Sysfs Filenames

```
power[1-*]_input        // Power in µW
power[1-*]_average      // Average power
power[1-*]_cap          // Power cap
```

### Example Values

```c
// 5 watts = 5,000,000 µW
// 100 milliwatts = 100,000 µW
```

## Energy (hwmon_energy)

**Units**: **microjoules** (µJ)

### Attribute Bitmasks

```c
HWMON_E_INPUT           // Accumulated energy in µJ
```

### Sysfs Filenames

```
energy[1-*]_input       // Energy counter
```

### Usage

Energy counters are typically monotonic (always increasing) and used to track accumulated energy consumption over time. Userspace tools calculate power consumption by taking the derivative (ΔE/Δt).

## Humidity (hwmon_humidity)

**Units**: **milli-percent** (0.001%)

### Attribute Bitmasks

```c
HWMON_H_INPUT           // Relative humidity
HWMON_H_MIN             // Minimum threshold
HWMON_H_MAX             // Maximum threshold
HWMON_H_ALARM           // Alarm flag
HWMON_H_LABEL           // Channel label
```

### Sysfs Filenames

```
humidity[1-*]_input     // Humidity in milli-percent
```

### Example Values

```c
// 45.2% RH = 45200 milli-percent (100000 = 100%)
// 80% RH = 80000 milli-percent
```

## Fan (hwmon_fan)

**Units**: **RPM** (revolutions per minute)

### Attribute Bitmasks

```c
HWMON_F_INPUT           // Fan speed in RPM
HWMON_F_MIN             // Minimum RPM
HWMON_F_MAX             // Maximum RPM
HWMON_F_ALARM           // Alarm (fan stopped/stalled)
HWMON_F_FAULT           // Fault detection
HWMON_F_LABEL           // Channel label
```

### Sysfs Filenames

```
fan[1-*]_input          // Fan speed in RPM
fan[1-*]_min            // Minimum speed
```

### Example Values

```c
// 2000 RPM
// 0 RPM (fan stopped)
```

## PWM (hwmon_pwm)

**Units**: **0-255** (duty cycle)

### Attribute Bitmasks

```c
HWMON_PWM_INPUT         // Current PWM value (0-255)
HWMON_PWM_MODE          // PWM vs DC mode
HWMON_PWM_ENABLE        // Enable/disable PWM
HWMON_PWM_FREQ          // PWM frequency in Hz
```

### Sysfs Filenames

```
pwm[1-*]                // PWM duty cycle (0=off, 255=full)
pwm[1-*]_mode           // Mode selection
pwm[1-*]_enable         // Enable/manual/automatic
```

### Example Values

```c
// 0 = 0% duty cycle (off)
// 128 = 50% duty cycle
// 255 = 100% duty cycle (full on)
```

## Chip-level Attributes

### Attribute Bitmasks

```c
HWMON_C_UPDATE_INTERVAL // Polling interval in milliseconds
HWMON_C_ALARMS          // Consolidated alarm bitmap
HWMON_C_BEEP_ENABLE     // Global beep enable
HWMON_C_REGISTER        // Register access for debugging
```

### Sysfs Filenames

```
update_interval         // Poll interval (ms)
alarms                  // Alarm bitmap
```

### Usage

```c
// Set 2 second polling interval
echo 2000 > /sys/class/hwmon/hwmon0/update_interval

// Read alarm bitmap
cat /sys/class/hwmon/hwmon0/alarms
```

## Multi-Channel Configuration Example

Example for a power monitor with multiple sensor types:

```c
static const struct hwmon_channel_info * const ltc2991_info[] = {
	// Chip-level attributes
	HWMON_CHANNEL_INFO(chip, HWMON_C_UPDATE_INTERVAL),

	// Temperature channels 0-3
	HWMON_CHANNEL_INFO(temp,
			   HWMON_T_INPUT | HWMON_T_LABEL,
			   HWMON_T_INPUT | HWMON_T_LABEL,
			   HWMON_T_INPUT | HWMON_T_LABEL,
			   HWMON_T_INPUT | HWMON_T_LABEL),

	// Voltage channels 0-7 (note: starts at 0, not 1)
	HWMON_CHANNEL_INFO(in,
			   HWMON_I_INPUT | HWMON_I_LABEL,
			   HWMON_I_INPUT | HWMON_I_LABEL,
			   HWMON_I_INPUT | HWMON_I_LABEL,
			   HWMON_I_INPUT | HWMON_I_LABEL,
			   HWMON_I_INPUT | HWMON_I_LABEL,
			   HWMON_I_INPUT | HWMON_I_LABEL,
			   HWMON_I_INPUT | HWMON_I_LABEL,
			   HWMON_I_INPUT | HWMON_I_LABEL),

	// Current channels 1-4
	HWMON_CHANNEL_INFO(curr,
			   HWMON_C_INPUT | HWMON_C_LABEL,
			   HWMON_C_INPUT | HWMON_C_LABEL,
			   HWMON_C_INPUT | HWMON_C_LABEL,
			   HWMON_C_INPUT | HWMON_C_LABEL),

	// Power channels 1-4
	HWMON_CHANNEL_INFO(power,
			   HWMON_P_INPUT | HWMON_P_LABEL,
			   HWMON_P_INPUT | HWMON_P_LABEL,
			   HWMON_P_INPUT | HWMON_P_LABEL,
			   HWMON_P_INPUT | HWMON_P_LABEL),
	NULL
};
```

## Channel Indexing Rules

| Sensor Type | Index Start | Example |
|-------------|-------------|---------|
| Temperature | 1 | temp1_input, temp2_input |
| Voltage (in) | 0 | in0_input, in1_input |
| Current | 1 | curr1_input, curr2_input |
| Power | 1 | power1_input, power2_input |
| Energy | 1 | energy1_input, energy2_input |
| Humidity | 1 | humidity1_input, humidity2_input |
| Fan | 1 | fan1_input, fan2_input |
| PWM | 1 | pwm1, pwm2 |

## Standard Unit Conversion Examples

### Temperature Sensor (SHT4x)

```c
// Hardware: 16-bit value representing -45°C to +125°C
u16 t_ticks = (raw_data[0] << 8) | raw_data[1];

// Convert to millidegrees Celsius
data->temperature = ((21875 * (int32_t)t_ticks) >> 13) - 45000;
```

### Voltage Monitor (12-bit ADC, 0-5V range)

```c
// Hardware: 12-bit ADC, 5V full scale
u16 raw_adc = read_adc();

// Convert to millivolts
*val = (raw_adc * 5000) / 4095;  // 0-5000 mV
```

### Current Monitor (INA219, shunt resistor)

```c
// Hardware: 12-bit ADC measuring voltage across 0.1Ω shunt
// Full scale ±40mV = ±400mA
s16 raw_current = read_current_reg();

// Convert to milliamperes (LSB = 100µA)
*val = raw_current / 10;  // mA
```

### Power Monitor (calculated from V and I)

```c
// Calculate power from voltage (mV) and current (mA)
long voltage_mv = read_voltage();
long current_ma = read_current();

// Power = V * I, convert to µW
// (mV * mA) = µW
*val = voltage_mv * current_ma;
```

### Humidity Sensor (SHT4x)

```c
// Hardware: 16-bit value representing 0-100% RH
u16 rh_ticks = (raw_data[3] << 8) | raw_data[4];

// Convert to milli-percent
data->humidity = ((15625 * (int32_t)rh_ticks) >> 13) - 6000;
```
