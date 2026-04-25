# PMBus Commands and Data Formats

Detailed guide to PMBus standard commands, virtual commands, data format conversions (linear, direct, IEEE 754), and coefficient calculations.

## PMBus Standard Commands

Common PMBus commands defined in the specification:

```c
// Page management
#define PMBUS_PAGE                  0x00  // Select page (multi-page devices)
#define PMBUS_OPERATION             0x01  // On/off control
#define PMBUS_ON_OFF_CONFIG         0x02  // On/off configuration
#define PMBUS_CLEAR_FAULTS          0x03  // Clear fault registers

// Capability
#define PMBUS_CAPABILITY            0x19  // Device capabilities

// Voltage commands
#define PMBUS_VOUT_MODE             0x20  // Output voltage mode
#define PMBUS_VOUT_COMMAND          0x21  // Output voltage setpoint
#define PMBUS_VOUT_MAX              0x24  // Maximum output voltage
#define PMBUS_VOUT_MARGIN_HIGH      0x25  // High margin voltage
#define PMBUS_VOUT_MARGIN_LOW       0x26  // Low margin voltage

// Fault limits
#define PMBUS_VOUT_OV_FAULT_LIMIT   0x40  // Overvoltage fault limit
#define PMBUS_VOUT_OV_WARN_LIMIT    0x42  // Overvoltage warning limit
#define PMBUS_VOUT_UV_WARN_LIMIT    0x43  // Undervoltage warning limit
#define PMBUS_VOUT_UV_FAULT_LIMIT   0x44  // Undervoltage fault limit
#define PMBUS_IOUT_OC_FAULT_LIMIT   0x46  // Overcurrent fault limit
#define PMBUS_IOUT_OC_WARN_LIMIT    0x4A  // Overcurrent warning limit
#define PMBUS_OT_FAULT_LIMIT        0x4F  // Overtemperature fault limit
#define PMBUS_OT_WARN_LIMIT         0x51  // Overtemperature warning limit

// Status commands
#define PMBUS_STATUS_BYTE           0x78  // Summary status
#define PMBUS_STATUS_WORD           0x79  // Extended status
#define PMBUS_STATUS_VOUT           0x7A  // Output voltage status
#define PMBUS_STATUS_IOUT           0x7B  // Output current status
#define PMBUS_STATUS_INPUT          0x7C  // Input status
#define PMBUS_STATUS_TEMPERATURE    0x7D  // Temperature status
#define PMBUS_STATUS_CML            0x7E  // Communication status
#define PMBUS_STATUS_OTHER          0x7F  // Other status

// Measurement commands
#define PMBUS_READ_VIN              0x88  // Input voltage
#define PMBUS_READ_IIN              0x89  // Input current
#define PMBUS_READ_VCAP             0x8A  // Bulk capacitor voltage
#define PMBUS_READ_VOUT             0x8B  // Output voltage
#define PMBUS_READ_IOUT             0x8C  // Output current
#define PMBUS_READ_TEMPERATURE_1    0x8D  // Temperature sensor 1
#define PMBUS_READ_TEMPERATURE_2    0x8E  // Temperature sensor 2
#define PMBUS_READ_TEMPERATURE_3    0x8F  // Temperature sensor 3
#define PMBUS_READ_FAN_SPEED_1      0x90  // Fan 1 tachometer
#define PMBUS_READ_FAN_SPEED_2      0x91  // Fan 2 tachometer
#define PMBUS_READ_POUT             0x96  // Output power
#define PMBUS_READ_PIN              0x97  // Input power

// Manufacturer-specific (0xA0-0xFF reserved)
#define PMBUS_MFR_ID                0x99  // Manufacturer ID string
#define PMBUS_MFR_MODEL             0x9A  // Model name string
#define PMBUS_MFR_REVISION          0x9B  // Revision string
```

## Virtual Commands

Virtual commands (0x100+) are Linux kernel extensions for non-standard functionality:

```c
// Peak/minimum tracking
#define PMBUS_VIRT_READ_VIN_MAX         0x100  // Peak input voltage
#define PMBUS_VIRT_READ_VIN_MIN         0x101  // Minimum input voltage
#define PMBUS_VIRT_READ_VOUT_MAX        0x102  // Peak output voltage
#define PMBUS_VIRT_READ_VOUT_MIN        0x103  // Minimum output voltage
#define PMBUS_VIRT_READ_IOUT_MAX        0x104  // Peak output current
#define PMBUS_VIRT_READ_IOUT_MIN        0x105  // Minimum output current
#define PMBUS_VIRT_READ_TEMP_MAX        0x106  // Peak temperature
#define PMBUS_VIRT_READ_TEMP_MIN        0x107  // Minimum temperature
#define PMBUS_VIRT_READ_PIN_MAX         0x108  // Peak input power
#define PMBUS_VIRT_READ_PIN_MIN         0x109  // Minimum input power
#define PMBUS_VIRT_READ_POUT_MAX        0x10A  // Peak output power
#define PMBUS_VIRT_READ_POUT_MIN        0x10B  // Minimum output power

// History reset (write triggers reset)
#define PMBUS_VIRT_RESET_VOUT_HISTORY   0x110  // Clear VOUT peak/min
#define PMBUS_VIRT_RESET_VIN_HISTORY    0x111  // Clear VIN peak/min
#define PMBUS_VIRT_RESET_IOUT_HISTORY   0x112  // Clear IOUT peak/min
#define PMBUS_VIRT_RESET_TEMP_HISTORY   0x113  // Clear temperature peak/min
#define PMBUS_VIRT_RESET_PIN_HISTORY    0x114  // Clear PIN peak/min
#define PMBUS_VIRT_RESET_POUT_HISTORY   0x115  // Clear POUT peak/min

// Sampling configuration
#define PMBUS_VIRT_POWER_SAMPLES        0x120  // Number of power samples
#define PMBUS_VIRT_IN_SAMPLES           0x121  // Number of input samples
#define PMBUS_VIRT_CURR_SAMPLES         0x122  // Number of current samples
#define PMBUS_VIRT_TEMP_SAMPLES         0x123  // Number of temperature samples

// Multi-phase support
#define PMBUS_VIRT_READ_PMON            0x130  // Per-phase monitoring
#define PMBUS_VIRT_READ_PHASE_IOUT      0x131  // Phase current
```

### Handling Virtual Commands

Virtual commands **must** be handled in device-specific callbacks:

```c
static int mypmbus_read_word_data(struct i2c_client *client, int page,
                                  int phase, int reg)
{
	int ret;

	switch (reg) {
	case PMBUS_VIRT_READ_IOUT_MAX:
		// Map to manufacturer-specific register
		ret = pmbus_read_word_data(client, page, 0xff, MFR_PEAK_IOUT);
		break;

	case PMBUS_VIRT_RESET_IOUT_HISTORY:
		// Signal supported (actual reset in write handler)
		ret = 0;
		break;

	default:
		// IMPORTANT: Return -ENODATA for unsupported virtual commands
		ret = -ENODATA;
		break;
	}

	return ret;
}

static int mypmbus_write_word_data(struct i2c_client *client, int page,
                                   int reg, u16 word)
{
	int ret;

	switch (reg) {
	case PMBUS_VIRT_RESET_IOUT_HISTORY:
		// Clear peak value
		ret = pmbus_write_word_data(client, page, MFR_PEAK_IOUT, 0);
		break;

	default:
		ret = -ENODATA;
		break;
	}

	return ret;
}
```

## Data Formats

PMBus supports four data formats:

### 1. Linear11 Format (Standard PMBus)

5-bit exponent + 11-bit mantissa (LINEAR11):

```
Format: EEEEE MMMMMMMMMMM
Value = mantissa * 2^exponent
```

**Example**: Read VIN = 0x7C50
```
Binary:   0111 1100 0101 0000
Exponent: 01111 = 15 (as unsigned)
          15 - 16 = -1 (convert to signed)
Mantissa: 10001010000 = 1104 (as unsigned)
          1104 - 2048 = -944 (convert to signed 11-bit)

Wait, positive value should have exponent interpreted differently.
Let me recalculate:

Exponent: 01111 = 15
          If bit 4 is 0, it's positive: 0-15 range maps to -16 to -1
          Actually, 5-bit signed: 01111 = +15 (in two's complement)

Let's use proper LINEAR11 decoding:
- Exponent is bits [15:11], sign-extended from 5 bits
- Mantissa is bits [10:0], sign-extended from 11 bits

0x7C50 = 0111110001010000
Exponent: 01111 (5 bits) = +15
Mantissa: 10001010000 (11 bits)
          As unsigned: 1104
          As signed: negative (bit 10 set)
          Two's complement: -(2048 - 1104) = -944

Hmm, this doesn't make sense for VIN. Let me check the standard approach:

Actually in LINEAR11:
- Exponent [15:11]: signed, range -16 to +15
- Mantissa [10:0]: signed, range -1024 to +1023

0x7C50:
Exp: 01111b = 15 decimal
Man: 00001010000b = 80 decimal

Value = 80 * 2^15 = 80 * 32768 = 2,621,440 (too large!)

The issue is exponent interpretation. Let's use standard LINEAR11:
Exponent should be interpreted as: if bit4=0 and value > 15, then it's negative.
Actually, proper 5-bit two's complement: 01111 = +15 is wrong.

Let me use the kernel's approach:
```c
s16 exponent = ((s16)data) >> 11;        // Sign-extend from bit 15
s32 mantissa = (((s16)(data << 5)) >> 5); // Sign-extend from bit 10

Value = mantissa * (1 << exponent);  // or mantissa * 2^exp
```

Actually for positive voltages, this makes more sense:
0xC050: C = 1100, so exponent = 1100 0000 0101 0000 >> 11 = 0xFFF8 = -8
        Mantissa: 0000 0101 0000 = 80
        Value = 80 * 2^-8 = 80 / 256 = 0.3125 V = 312.5 mV

This is more realistic!
```

**Kernel conversion helpers** (in pmbus_core.c):
```c
// Convert from LINEAR11 to milliunit
static long pmbus_reg2data_linear(struct pmbus_data *data,
                                   struct pmbus_sensor *sensor)
{
	s16 exponent;
	s32 mantissa;
	long val;

	exponent = ((s16)sensor->data) >> 11;
	mantissa = (((s16)(sensor->data << 5)) >> 5);

	val = mantissa;

	// Apply exponent
	if (exponent >= 0)
		val <<= exponent;
	else
		val >>= -exponent;

	return val;
}
```

### 2. Direct Format

Explicit m, b, R coefficients:

```
real_value = (register_value * m - b) * 10^R

Where:
  m = multiplier (slope)
  b = offset
  R = exponent (power of 10)
```

**Example**: ADM1275 with m=19199, b=0, R=-2
```
Register = 0x1234 = 4660 decimal

voltage = (4660 * 19199 - 0) * 10^-2
        = 89447340 * 0.01
        = 894473.4 mV
        = 894.47 V (this is wrong, likely for current)

Actually for voltage:
Register = 0x00C8 = 200 decimal
voltage = (200 * 19199 - 0) * 10^-2
        = 3839800 * 0.01
        = 38398 mV
        = 38.4 V (correct for 60V range)
```

**Shunt resistor scaling** for current:
```c
// Datasheet assumes 1 mOhm shunt
// Actual shunt is 2 mOhm
// Current = Vsense / Rshunt
// Measured current is half with 2x shunt

m_actual = m_datasheet * shunt_uohm / 1000

Example:
  m_datasheet = 807
  shunt = 2000 uOhm (2 mOhm)
  m_actual = 807 * 2000 / 1000 = 1614
```

### 3. VID Format

Voltage Identifier codes (Intel/AMD VID tables). Rarely used in PMBus.

### 4. IEEE 754 Format

Single-precision floating point (LT7170, LT7171):

```c
info->format[PSC_VOLTAGE_OUT] = ieee754;
```

PMBus core handles conversion automatically. No coefficients needed.

## Sensor Classes

Data formats are specified per sensor class:

```c
enum pmbus_sensor_classes {
	PSC_VOLTAGE_IN,      // Input voltage
	PSC_VOLTAGE_OUT,     // Output voltage
	PSC_CURRENT_IN,      // Input current
	PSC_CURRENT_OUT,     // Output current
	PSC_POWER,           // Power
	PSC_TEMPERATURE,     // Temperature
	PSC_FAN,             // Fan speed
	PSC_PWM,             // PWM duty cycle
	PSC_NUM_CLASSES,
};

// Configuration
info->format[PSC_VOLTAGE_IN] = linear;
info->format[PSC_VOLTAGE_OUT] = direct;
info->format[PSC_CURRENT_OUT] = direct;
info->format[PSC_POWER] = direct;
info->format[PSC_TEMPERATURE] = linear;

// Direct format coefficients
info->m[PSC_VOLTAGE_OUT] = 19199;
info->b[PSC_VOLTAGE_OUT] = 0;
info->R[PSC_VOLTAGE_OUT] = -2;

info->m[PSC_CURRENT_OUT] = 807;
info->b[PSC_CURRENT_OUT] = 20475;
info->R[PSC_CURRENT_OUT] = -1;
```

## Coefficient Sources

Where to find m, b, R coefficients:

1. **Datasheet "Direct Format Coefficients" table**
2. **Calculate from transfer function**:
   ```
   If V_out = V_code * 0.1953125 mV (from datasheet):

   m = 1 / 0.1953125 = 5.12 ≈ 5
   R = adjustment to get millivolts

   Better approach:
   V_out(V) = V_code * 0.1953125 / 1000
   V_out(mV) = V_code * 0.1953125

   m = 1 / 0.0001953125 = 5120  (for mV)
   b = 0
   R = -3  (since 0.1953125 ≈ 195.3125 * 10^-3)
   ```

3. **Reverse-engineer from example code**

4. **Extract from datasheet formulas**:
   ```
   If datasheet says: I_sense = (Code * 15.625 uV) / R_sense

   For 1 mOhm sense resistor:
   I(A) = Code * 15.625e-6 / 0.001
        = Code * 0.015625
   I(mA) = Code * 15.625

   m = 15625 (for mA)
   b = 0
   R = -3
   ```

## Helper Functions

PMBus core provides register access helpers:

```c
// Read byte
int pmbus_read_byte_data(struct i2c_client *client, int page, u8 reg);

// Read word (with page and phase)
int pmbus_read_word_data(struct i2c_client *client, int page,
                         int phase, int reg);

// Write byte
int pmbus_write_byte(struct i2c_client *client, int page, u8 value);

// Write word
int pmbus_write_word_data(struct i2c_client *client, int page,
                          int reg, u16 word);

// Update byte (read-modify-write)
int pmbus_update_byte_data(struct i2c_client *client, int page,
                            u8 reg, u8 mask, u8 value);

// Get driver info from client
struct pmbus_driver_info *pmbus_get_driver_info(struct i2c_client *client);
```

Use these in your read/write callbacks:

```c
static int mypmbus_read_word_data(struct i2c_client *client, int page,
                                  int phase, int reg)
{
	switch (reg) {
	case PMBUS_VIRT_READ_IOUT_MAX:
		// Use helper to access manufacturer register
		return pmbus_read_word_data(client, page, 0xff, MFR_PEAK_IOUT);
	default:
		return -ENODATA;
	}
}
```

## Page Parameter

The `page` parameter selects voltage rails in multi-page devices:

- `0xff` = broadcast to all pages (if supported)
- `0` to `pages-1` = specific page
- Some devices auto-increment page on sequential reads

```c
// Read VOUT from page 2
ret = pmbus_read_word_data(client, 2, 0xff, PMBUS_READ_VOUT);
```

## Phase Parameter

The `phase` parameter selects phases in multi-phase regulators:

- `0xff` = aggregate/sum of all phases
- `0` to `phases-1` = specific phase current

```c
// Read phase 0 current
ret = pmbus_read_word_data(client, 0, 0, PMBUS_READ_IOUT);

// Read total current (sum of all phases)
ret = pmbus_read_word_data(client, 0, 0xff, PMBUS_READ_IOUT);
```
