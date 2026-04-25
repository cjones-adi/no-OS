---
name: no-os-power
description: |
  Complete guide to no-OS power management drivers including PMICs, regulators, battery
  chargers, and power monitors. Covers buck/boost/LDO topologies, DVS, sequencing, PMBus
  protocol, battery charging (CC-CV), and power monitoring.
triggers:
  - "power"
  - "pmic"
  - "regulator"
  - "battery"
  - "charger"
  - "buck"
  - "boost"
  - "ldo"
  - "pmbus"
  - "dvs"
alwaysInclude: false
---

# no-OS Power Management Driver Development Guide

This skill provides comprehensive guidance for developing and working with power management drivers in the no-OS framework. Based on analysis of 23 drivers including LT8491, LTC4162L, LT7182S, ADP5055, MAX17851, and ADES1754.

## Quick Reference

**Common Driver Locations**:
- `drivers/power/` - All power management devices

**Key Header Files**:
- `drivers/power/lt8491/lt8491.h` - Buck-boost battery charger
- `drivers/power/ltc4162l/ltc4162l.h` - Advanced Li-Ion charger
- `drivers/power/lt7182s/lt7182s.h` - Dual-output PMBus regulator
- `drivers/power/adp5055/adp5055.h` - Buck regulator with charger
- `drivers/power/max17851/max17851.h` - Battery monitor (multicell)

**Typical API Functions**:
```c
int lt8491_init(struct lt8491_dev **device, struct lt8491_init_param *init_param);
int lt8491_set_output_voltage(struct lt8491_dev *dev, uint32_t voltage_mv);
int lt8491_set_charge_current(struct lt8491_dev *dev, uint32_t current_ma);
int ltc4162l_get_charge_status(struct ltc4162l_dev *dev, enum ltc4162l_charge_status *status);
int lt7182s_set_operation(struct lt7182s_dev *dev, uint8_t channel, bool enable);
int adp5055_enable_charger(struct adp5055_dev *dev, bool enable);
```

## Architecture Overview

### Power Device Types

1. **Switching Regulators**
   - **Buck** (step-down): Vin > Vout
   - **Boost** (step-up): Vout > Vin
   - **Buck-Boost**: Vout can be < or > Vin
   - High efficiency (85-95%+)
   - Requires inductor and output capacitor

2. **Linear Regulators (LDO)**
   - Simple, low noise
   - Lower efficiency (Eff = Vout/Vin)
   - No switching noise
   - Fast transient response

3. **Battery Chargers**
   - Li-Ion/Li-Po: CC-CV (Constant Current → Constant Voltage)
   - Lead-acid: Multi-stage charging
   - MPPT (Maximum Power Point Tracking) for solar
   - Charge termination and safety

4. **PMICs** (Power Management ICs)
   - Multiple regulators integrated
   - Power sequencing
   - DVS (Dynamic Voltage Scaling)
   - Fault monitoring and protection

5. **Battery Monitors**
   - Cell voltage monitoring (multicell stacks)
   - Coulomb counting (charge integration)
   - State of Charge (SoC) estimation
   - Cell balancing control

6. **Power Monitors**
   - Voltage, current, power measurement
   - Energy accumulation
   - Alerts and thresholds

### Common Design Patterns

**Device Descriptor**:
```c
struct lt8491_dev {
    struct no_os_i2c_desc *i2c_desc;       // I2C interface
    struct no_os_gpio_desc *alert_gpio;    // Alert pin
    uint32_t output_voltage_mv;            // Current Vout
    uint32_t charge_current_ma;            // Current Icharge
    enum lt8491_charge_state state;        // Charging state
};

struct lt7182s_dev {
    struct no_os_i2c_desc *i2c_desc;       // PMBus interface
    uint8_t i2c_addr;                      // Device address
    struct lt7182s_channel_state ch[2];    // Dual-channel state
};

struct ltc4162l_dev {
    struct no_os_i2c_desc *i2c_desc;
    struct ltc4162l_config config;         // Charging parameters
    struct no_os_gpio_desc *smbalert;      // SMBus alert
};
```

**Initialization Parameters**:
```c
struct lt8491_init_param {
    struct no_os_i2c_init_param i2c_init;
    struct no_os_gpio_init_param alert_param;
    uint32_t output_voltage_mv;            // Target voltage
    uint32_t charge_current_ma;            // Charge current limit
    uint32_t mppt_ratio;                   // MPPT percentage (0-100)
    bool enable_mppt;                      // MPPT enable
};

struct adp5055_init_param {
    struct no_os_i2c_init_param i2c_init;
    uint32_t vbus_ilim_ma;                 // Input current limit
    uint32_t ichg_ma;                      // Charge current
    uint32_t vtrm_mv;                      // Termination voltage
    uint32_t vindpm_mv;                    // Input voltage threshold
    bool enable_charger;                   // Charger enable on init
};
```

## Core Functionality

### 1. Voltage and Current Control

**Setting Output Voltage**:
```c
// Set regulator output voltage
uint32_t voltage_mv = 3300;  // 3.3V
ret = lt7182s_set_vout(dev, LT7182S_CH0, voltage_mv);

// Read back actual voltage
uint32_t actual_mv;
ret = lt7182s_read_vout(dev, LT7182S_CH0, &actual_mv);
pr_info("Channel 0 output: %u mV\n", actual_mv);

// Voltage range checking
if (voltage_mv < LT7182S_VOUT_MIN || voltage_mv > LT7182S_VOUT_MAX) {
    pr_err("Voltage out of range: %u mV\n", voltage_mv);
    return -EINVAL;
}
```

**Setting Current Limits**:
```c
// Output current limit
uint32_t current_limit_ma = 1500;
ret = lt7182s_set_iout_max(dev, LT7182S_CH0, current_limit_ma);

// Charge current for battery chargers
uint32_t charge_current_ma = 1000;  // 1A charging
ret = ltc4162l_set_charge_current(dev, charge_current_ma);

// Input current limit (for VBUS/adapter)
ret = adp5055_set_input_current_limit(dev, 500);  // 500mA USB
```

### 2. Enable/Disable Control

**Regulator Enable**:
```c
// Enable channel
ret = lt7182s_set_operation(dev, LT7182S_CH0, true);

// Disable channel
ret = lt7182s_set_operation(dev, LT7182S_CH1, false);

// Read enable state
bool enabled;
ret = lt7182s_get_operation(dev, LT7182S_CH0, &enabled);
```

**Charger Enable**:
```c
// Enable battery charging
ret = adp5055_enable_charger(dev, true);

// Disable charging (trickle charge may continue)
ret = adp5055_enable_charger(dev, false);

// Check charger status
enum adp5055_charge_status status;
ret = adp5055_get_charge_status(dev, &status);
if (status == ADP5055_CHG_STATUS_CHARGING) {
    pr_info("Battery charging\n");
}
```

### 3. Battery Charging (CC-CV)

**Charge Configuration**:
```c
// Li-Ion charging parameters
struct ltc4162l_config charge_config = {
    .charge_current_ma = 1000,         // 1A constant current phase
    .charge_voltage_mv = 4200,         // 4.2V constant voltage phase
    .input_current_limit_ma = 1500,    // Input current limit
    .precharge_current_ma = 100,       // Trickle charge current
    .termination_current_ma = 50,      // C/20 termination
};

ret = ltc4162l_configure(dev, &charge_config);
ret = ltc4162l_enable_charging(dev, true);
```

**Charge States**:
```c
enum ltc4162l_charge_status {
    LTC4162L_BAT_DETECT_FAILED,        // No battery
    LTC4162L_BAT_DETECT,               // Detecting battery
    LTC4162L_PRECHARGE,                // Trickle charge (V < Vprecharge)
    LTC4162L_CC_CV_CHARGE,             // Main charging
    LTC4162L_NTC_PAUSE,                // Temperature suspend
    LTC4162L_TIMER_TERM,               // Timeout termination
    LTC4162L_C_OVER_X_TERM,            // Current termination (I < Iterm)
    LTC4162L_MAX_CHARGE_TIME_FAULT,    // Safety timeout
    LTC4162L_BAT_MISSING_FAULT,        // Battery removed
    LTC4162L_BAT_SHORT_FAULT,          // Battery short
};

enum ltc4162l_charge_status status;
ret = ltc4162l_get_charge_status(dev, &status);

switch (status) {
case LTC4162L_PRECHARGE:
    pr_info("Precharging (low voltage)\n");
    break;
case LTC4162L_CC_CV_CHARGE:
    pr_info("Fast charging\n");
    break;
case LTC4162L_C_OVER_X_TERM:
    pr_info("Charge complete\n");
    break;
case LTC4162L_BAT_MISSING_FAULT:
    pr_err("Battery not detected\n");
    break;
}
```

**MPPT (Maximum Power Point Tracking)**:
```c
// For solar/renewable input sources
struct lt8491_init_param init = {
    .enable_mppt = true,
    .mppt_ratio = 95,  // Track at 95% of open-circuit voltage
};
ret = lt8491_init(&dev, &init);

// Adjust MPPT ratio dynamically
ret = lt8491_set_mppt_ratio(dev, 93);

// Read input power
uint32_t input_power_mw;
ret = lt8491_get_input_power(dev, &input_power_mw);
pr_info("Solar input: %u mW\n", input_power_mw);
```

### 4. Power Monitoring

**Voltage/Current Measurement**:
```c
// Read output voltage
uint32_t vout_mv;
ret = lt7182s_read_vout(dev, LT7182S_CH0, &vout_mv);

// Read output current
uint32_t iout_ma;
ret = lt7182s_read_iout(dev, LT7182S_CH0, &iout_ma);

// Read input voltage
uint32_t vin_mv;
ret = lt7182s_read_vin(dev, &vin_mv);

// Calculate power
uint32_t power_mw = (uint64_t)vout_mv * iout_ma / 1000;
pr_info("Output power: %u mW (%.2f W)\n", power_mw, power_mw / 1000.0);
```

**Battery Monitor (Multicell)**:
```c
// MAX17851: Monitor up to 14 series cells
uint16_t cell_voltages_mv[14];
for (int i = 0; i < 14; i++) {
    ret = max17851_read_cell_voltage(dev, i, &cell_voltages_mv[i]);
    pr_info("Cell %d: %u mV\n", i, cell_voltages_mv[i]);
}

// Check for imbalance
uint16_t min_v = 0xFFFF, max_v = 0;
for (int i = 0; i < num_cells; i++) {
    if (cell_voltages_mv[i] < min_v) min_v = cell_voltages_mv[i];
    if (cell_voltages_mv[i] > max_v) max_v = cell_voltages_mv[i];
}
uint16_t delta_mv = max_v - min_v;
if (delta_mv > 100) {  // 100mV imbalance threshold
    pr_warn("Cell imbalance: %u mV\n", delta_mv);
}
```

**Temperature Monitoring**:
```c
// Die temperature
int16_t die_temp_c;
ret = ltc4162l_get_die_temp(dev, &die_temp_c);

// Battery temperature (NTC thermistor)
int16_t bat_temp_c;
ret = ltc4162l_get_bat_temp(dev, &bat_temp_c);

// Temperature limits
if (bat_temp_c < 0 || bat_temp_c > 45) {
    pr_warn("Battery temp out of safe range: %d C\n", bat_temp_c);
    ltc4162l_enable_charging(dev, false);
}
```

### 5. PMBus Protocol

**PMBus Commands**:
```c
// PMBus is I2C-based with standardized command set

// Read voltage (PMBus LINEAR11 format)
uint16_t vout_raw;
ret = lt7182s_pmbus_read_word(dev, PMBUS_READ_VOUT, &vout_raw);
uint32_t vout_mv = pmbus_linear11_to_millivolts(vout_raw);

// Write voltage (PMBus LINEAR16 format)
uint16_t vout_cmd = pmbus_millivolts_to_linear16(3300);
ret = lt7182s_pmbus_write_word(dev, PMBUS_VOUT_COMMAND, vout_cmd);

// Standard PMBus commands
#define PMBUS_OPERATION         0x01
#define PMBUS_ON_OFF_CONFIG     0x02
#define PMBUS_VOUT_COMMAND      0x21
#define PMBUS_IOUT_OC_FAULT_LIMIT 0x46
#define PMBUS_READ_VIN          0x88
#define PMBUS_READ_VOUT         0x8B
#define PMBUS_READ_IOUT         0x8C
#define PMBUS_READ_TEMPERATURE_1 0x8D
```

**Data Format Conversion**:
```c
// LINEAR11 format: 5-bit exponent, 11-bit mantissa
static uint32_t pmbus_linear11_to_millivolts(uint16_t value)
{
    int16_t exponent = (int8_t)(value >> 11);  // Sign-extend
    int16_t mantissa = (int16_t)(value & 0x7FF);
    if (mantissa > 0x3FF) mantissa |= 0xF800;  // Sign-extend

    int32_t result = mantissa;
    if (exponent >= 0)
        result <<= exponent;
    else
        result >>= -exponent;

    return result;  // Already in mV for voltage
}

// LINEAR16 format: Fixed exponent (device-specific)
static uint16_t pmbus_millivolts_to_linear16(uint32_t mv, int8_t exponent)
{
    int32_t mantissa = mv;
    if (exponent >= 0)
        mantissa >>= exponent;
    else
        mantissa <<= -exponent;

    return (uint16_t)(mantissa & 0xFFFF);
}
```

### 6. Fault Handling and Protection

**Fault Status**:
```c
// Read fault status
uint8_t fault_status;
ret = lt7182s_read_status_byte(dev, &fault_status);

if (fault_status & LT7182S_STATUS_VOUT_OV) {
    pr_err("Output overvoltage fault\n");
}
if (fault_status & LT7182S_STATUS_IOUT_OC) {
    pr_err("Output overcurrent fault\n");
}
if (fault_status & LT7182S_STATUS_TEMPERATURE) {
    pr_err("Overtemperature fault\n");
}

// Clear latched faults
ret = lt7182s_clear_faults(dev);
```

**Protection Thresholds**:
```c
// Set overcurrent threshold
uint32_t oc_limit_ma = 2000;  // 2A limit
ret = lt7182s_set_iout_oc_fault_limit(dev, LT7182S_CH0, oc_limit_ma);

// Set overvoltage threshold
uint32_t ov_limit_mv = 3600;  // 10% above nominal 3.3V
ret = lt7182s_set_vout_ov_fault_limit(dev, LT7182S_CH0, ov_limit_mv);

// Set undervoltage threshold
uint32_t uv_limit_mv = 3000;  // 10% below nominal
ret = lt7182s_set_vout_uv_fault_limit(dev, LT7182S_CH0, uv_limit_mv);

// Overtemperature threshold
ret = lt7182s_set_ot_fault_limit(dev, 125);  // 125°C
```

**Alert/Interrupt Handling**:
```c
// Configure alert pin
struct no_os_gpio_init_param alert_init = {
    .number = ALERT_GPIO_PIN,
    .platform_ops = &gpio_ops,
};
ret = no_os_gpio_get(&dev->alert_gpio, &alert_init);
ret = no_os_gpio_direction_input(dev->alert_gpio);

// Alert interrupt handler
void alert_isr(void *context)
{
    struct lt7182s_dev *dev = context;
    uint8_t status;

    // Read status to determine cause
    lt7182s_read_status_byte(dev, &status);

    if (status & LT7182S_STATUS_IOUT_OC) {
        // Handle overcurrent
        pr_err("Overcurrent detected\n");
        lt7182s_set_operation(dev, LT7182S_CH0, false);
    }

    // Clear alert
    lt7182s_clear_faults(dev);
}
```

### 7. Power Sequencing

**Startup Sequencing**:
```c
// Power up rails in specific order with delays
struct power_rail {
    struct lt7182s_dev *dev;
    uint8_t channel;
    uint32_t voltage_mv;
    uint32_t delay_ms;
};

struct power_rail rails[] = {
    { dev, LT7182S_CH0, 1800, 10 },  // 1.8V core, 10ms delay
    { dev, LT7182S_CH1, 3300, 5 },   // 3.3V I/O, 5ms delay
};

for (int i = 0; i < ARRAY_SIZE(rails); i++) {
    ret = lt7182s_set_vout(rails[i].dev, rails[i].channel,
                           rails[i].voltage_mv);
    ret = lt7182s_set_operation(rails[i].dev, rails[i].channel, true);

    // Wait for power good
    bool pg;
    uint32_t timeout = 100;  // 100ms timeout
    while (timeout--) {
        lt7182s_get_power_good(rails[i].dev, rails[i].channel, &pg);
        if (pg) break;
        no_os_mdelay(1);
    }
    if (!pg) {
        pr_err("Rail %d power good timeout\n", i);
        return -ETIMEDOUT;
    }

    no_os_mdelay(rails[i].delay_ms);
}
```

**Shutdown Sequencing**:
```c
// Power down in reverse order
for (int i = ARRAY_SIZE(rails) - 1; i >= 0; i--) {
    ret = lt7182s_set_operation(rails[i].dev, rails[i].channel, false);
    no_os_mdelay(5);  // Discharge delay
}
```

### 8. Dynamic Voltage Scaling (DVS)

**DVS for Power Optimization**:
```c
enum performance_mode {
    PERF_LOW_POWER,    // Low voltage, low frequency
    PERF_NORMAL,       // Normal operation
    PERF_TURBO,        // High voltage, high frequency
};

static const struct {
    uint32_t voltage_mv;
    uint32_t cpu_freq_mhz;
} dvs_table[] = {
    [PERF_LOW_POWER] = { 1000, 100 },
    [PERF_NORMAL]    = { 1200, 400 },
    [PERF_TURBO]     = { 1350, 600 },
};

int set_performance_mode(enum performance_mode mode)
{
    // Change voltage first when increasing
    if (dvs_table[mode].voltage_mv > current_voltage_mv) {
        ret = lt7182s_set_vout(dev, LT7182S_CH0,
                               dvs_table[mode].voltage_mv);
        no_os_udelay(100);  // Settling time
    }

    // Change CPU frequency
    ret = set_cpu_frequency(dvs_table[mode].cpu_freq_mhz);

    // Change voltage last when decreasing
    if (dvs_table[mode].voltage_mv < current_voltage_mv) {
        ret = lt7182s_set_vout(dev, LT7182S_CH0,
                               dvs_table[mode].voltage_mv);
    }

    current_voltage_mv = dvs_table[mode].voltage_mv;
    return 0;
}
```

## IIO Integration

**IIO Channels** (Example: LTC4162L):
```c
static struct iio_channel ltc4162l_channels[] = {
    {
        .name = "vbat",
        .ch_type = IIO_VOLTAGE,
        .indexed = true,
        .channel = 0,
        .attributes = ltc4162l_vbat_attrs,
    },
    {
        .name = "ibat",
        .ch_type = IIO_CURRENT,
        .indexed = true,
        .channel = 0,
        .attributes = ltc4162l_ibat_attrs,
    },
    {
        .name = "charge_status",
        .ch_type = IIO_ENUM,
        .indexed = false,
        .attributes = ltc4162l_status_attrs,
    },
};

static int ltc4162l_iio_read_raw(void *dev, char *buf, uint32_t len,
                                  const struct iio_ch_info *channel,
                                  intptr_t priv)
{
    struct ltc4162l_dev *ltc4162l = dev;
    uint32_t value;
    int ret;

    switch (channel->ch_num) {
    case 0:  // Battery voltage
        ret = ltc4162l_get_vbat(ltc4162l, &value);
        return iio_format_value(buf, len, IIO_VAL_INT, 1, (int32_t*)&value);
    case 1:  // Battery current
        ret = ltc4162l_get_ibat(ltc4162l, &value);
        return iio_format_value(buf, len, IIO_VAL_INT, 1, (int32_t*)&value);
    default:
        return -EINVAL;
    }
}
```

## Common Use Cases

### 1. USB Battery Charger
```c
// Configure for USB charging with input current limit
struct adp5055_init_param init = {
    .vbus_ilim_ma = 500,        // USB 2.0 limit
    .ichg_ma = 500,             // 0.5C charge rate
    .vtrm_mv = 4200,            // 4.2V for Li-Ion
    .vindpm_mv = 4500,          // VBUS threshold
    .enable_charger = true,
};

ret = adp5055_init(&dev, &init);

// Detect charger type and adjust
enum adp5055_charger_type type;
ret = adp5055_get_charger_type(dev, &type);
if (type == ADP5055_CHG_TYPE_DCP) {  // Dedicated charger
    adp5055_set_input_current_limit(dev, 1500);  // 1.5A
    adp5055_set_charge_current(dev, 1000);        // 1A
}
```

### 2. Solar MPPT Charger
```c
// Solar panel to battery with MPPT
struct lt8491_init_param init = {
    .output_voltage_mv = 14400,  // 12V lead-acid (14.4V float)
    .charge_current_ma = 5000,   // 5A max
    .enable_mppt = true,
    .mppt_ratio = 95,            // 95% of Voc
};

ret = lt8491_init(&dev, &init);

// Monitor charging
while (charging) {
    uint32_t vin_mv, vout_mv, iout_ma;
    enum lt8491_charge_state state;

    lt8491_get_input_voltage(dev, &vin_mv);
    lt8491_get_output_voltage(dev, &vout_mv);
    lt8491_get_charge_current(dev, &iout_ma);
    lt8491_get_charge_state(dev, &state);

    pr_info("Solar: %u mV, Bat: %u mV, I: %u mA, State: %d\n",
            vin_mv, vout_mv, iout_ma, state);

    no_os_mdelay(1000);
}
```

### 3. Multi-Rail PMIC
```c
// Configure multiple rails with sequencing
struct lt7182s_dev *pmic;
ret = lt7182s_init(&pmic, &init_param);

// Configure rails
lt7182s_set_vout(pmic, LT7182S_CH0, 1800);  // Core
lt7182s_set_vout(pmic, LT7182S_CH1, 3300);  // I/O

// Set current limits
lt7182s_set_iout_max(pmic, LT7182S_CH0, 3000);  // 3A
lt7182s_set_iout_max(pmic, LT7182S_CH1, 1000);  // 1A

// Power up sequence
lt7182s_set_operation(pmic, LT7182S_CH0, true);
no_os_mdelay(10);
lt7182s_set_operation(pmic, LT7182S_CH1, true);

// Monitor
uint32_t vout0, vout1, iout0, iout1;
lt7182s_read_vout(pmic, LT7182S_CH0, &vout0);
lt7182s_read_vout(pmic, LT7182S_CH1, &vout1);
lt7182s_read_iout(pmic, LT7182S_CH0, &iout0);
lt7182s_read_iout(pmic, LT7182S_CH1, &iout1);
```

### 4. Battery Pack Monitor
```c
// Monitor 12S Li-Ion battery pack
struct max17851_dev *monitor;
ret = max17851_init(&monitor, &init_param);

const int num_cells = 12;
uint16_t cell_mv[12];
int16_t pack_current_ma;
uint32_t soc_percent;

// Read all cells
for (int i = 0; i < num_cells; i++) {
    max17851_read_cell_voltage(monitor, i, &cell_mv[i]);
}

// Pack current
max17851_read_pack_current(monitor, &pack_current_ma);

// State of Charge (from coulomb counting)
max17851_get_soc(monitor, &soc_percent);

// Check for issues
uint16_t min_cell = 0xFFFF, max_cell = 0;
for (int i = 0; i < num_cells; i++) {
    if (cell_mv[i] < min_cell) min_cell = cell_mv[i];
    if (cell_mv[i] > max_cell) max_cell = cell_mv[i];
}

if (max_cell - min_cell > 100) {
    pr_warn("Cell imbalance detected, starting balancing\n");
    max17851_enable_balancing(monitor, true);
}

if (min_cell < 3000) {
    pr_err("Cell undervoltage: %u mV\n", min_cell);
}
if (max_cell > 4250) {
    pr_err("Cell overvoltage: %u mV\n", max_cell);
}
```

## Debugging Guide

### Common Issues

**No Communication**:
```c
// Check device presence
uint16_t device_id;
ret = ltc4162l_read_reg(dev, LTC4162L_REG_DEVICE_ID, &device_id);
if (ret < 0) {
    pr_err("I2C communication failed: %d\n", ret);
    // Check: I2C address, pull-ups, bus speed
}
if (device_id != LTC4162L_DEVICE_ID) {
    pr_err("Wrong device ID: 0x%04X (expected 0x%04X)\n",
           device_id, LTC4162L_DEVICE_ID);
}
```

**Regulator Not Starting**:
```c
// Check enable status
bool enabled;
ret = lt7182s_get_operation(dev, LT7182S_CH0, &enabled);
pr_info("Regulator enabled: %s\n", enabled ? "yes" : "no");

// Check fault status
uint8_t status;
ret = lt7182s_read_status_byte(dev, &status);
if (status != 0) {
    pr_err("Fault status: 0x%02X\n", status);
    lt7182s_clear_faults(dev);
}

// Check input voltage
uint32_t vin_mv;
ret = lt7182s_read_vin(dev, &vin_mv);
if (vin_mv < MIN_INPUT_VOLTAGE) {
    pr_err("Input voltage too low: %u mV\n", vin_mv);
}
```

**Battery Not Charging**:
```c
// Check charge status
enum ltc4162l_charge_status status;
ret = ltc4162l_get_charge_status(dev, &status);
pr_info("Charge status: %d\n", status);

// Common issues:
if (status == LTC4162L_BAT_MISSING_FAULT) {
    pr_err("Battery not detected\n");
    // Check: Battery connection, voltage divider
}
if (status == LTC4162L_NTC_PAUSE) {
    int16_t temp;
    ltc4162l_get_bat_temp(dev, &temp);
    pr_err("Charging paused due to temperature: %d C\n", temp);
}

// Check input
uint32_t vin_mv;
ltc4162l_get_input_voltage(dev, &vin_mv);
if (vin_mv < 4500) {
    pr_err("Input voltage too low: %u mV\n", vin_mv);
}
```

**PMBus Communication**:
```c
// Enable PEC (Packet Error Checking) for reliability
ret = lt7182s_enable_pec(dev, true);

// Verify read/write
ret = lt7182s_pmbus_write_word(dev, PMBUS_VOUT_COMMAND, 0x1234);
uint16_t readback;
ret = lt7182s_pmbus_read_word(dev, PMBUS_VOUT_COMMAND, &readback);
if (readback != 0x1234) {
    pr_err("PMBus read/write mismatch\n");
}
```

## Best Practices

1. **Always Check Input Voltage**
   - Verify VIN is within operating range before enabling
   - Use UVLO (Under-Voltage Lock-Out) thresholds
   - Monitor for brownout conditions

2. **Set Appropriate Current Limits**
   - Prevents overcurrent damage
   - Accounts for inrush current
   - Leaves margin for transients (20-30%)

3. **Implement Fault Recovery**
   - Read fault status after errors
   - Clear faults before retry
   - Limit retry attempts to prevent damage
   - Log fault events for diagnostics

4. **Temperature Monitoring**
   - Check die temperature under load
   - Battery temperature critical for Li-Ion
   - Derate current at high temperatures

5. **Use Power Good Signals**
   - Wait for PG before enabling dependent rails
   - Timeout on PG wait (detect startup failures)
   - Monitor PG during operation for fault detection

6. **Charge Termination**
   - Implement multiple termination methods (current, voltage, time)
   - Don't over-charge Li-Ion (safety hazard)
   - Monitor charge time for faults

7. **Sequencing and Timing**
   - Follow IC startup sequence requirements
   - Allow settling time after voltage changes
   - Ramp rates for sensitive loads

8. **PMBus Best Practices**
   - Enable PEC for noisy environments
   - Use block reads for efficiency
   - Verify critical writes with readback

## Testing Strategies

**Unit Tests**:
```c
void test_voltage_setting(void) {
    ret = lt7182s_set_vout(dev, LT7182S_CH0, 3300);
    TEST_ASSERT_EQUAL(0, ret);

    uint32_t vout_mv;
    ret = lt7182s_read_vout(dev, LT7182S_CH0, &vout_mv);
    TEST_ASSERT_INT32_WITHIN(50, 3300, vout_mv);  // ±50mV tolerance
}

void test_current_limit(void) {
    lt7182s_set_iout_max(dev, LT7182S_CH0, 1000);

    // Apply overload (requires programmable load)
    // Verify current clamps at limit
    uint32_t iout_ma;
    lt7182s_read_iout(dev, LT7182S_CH0, &iout_ma);
    TEST_ASSERT_INT32_WITHIN(100, 1000, iout_ma);
}
```

**Integration Tests**:
```c
void test_charge_cycle(void) {
    // Start charging
    ltc4162l_enable_charging(dev, true);

    // Wait for charging state
    enum ltc4162l_charge_status status;
    for (int i = 0; i < 100; i++) {
        ltc4162l_get_charge_status(dev, &status);
        if (status == LTC4162L_CC_CV_CHARGE) break;
        no_os_mdelay(100);
    }
    TEST_ASSERT_EQUAL(LTC4162L_CC_CV_CHARGE, status);

    // Verify charge current
    uint32_t ibat_ma;
    ltc4162l_get_charge_current(dev, &ibat_ma);
    TEST_ASSERT_INT32_WITHIN(100, 1000, ibat_ma);
}
```

## Reference Examples

- **LT8491 Example**: `projects/lt8491/src/examples/`
- **LTC4162L Example**: `projects/ltc4162l/src/examples/`
- **LT7182S Example**: `projects/lt7182s/src/examples/`
- **PMBus Integration**: Check drivers for PMBus command implementations

## Related Resources

- `/no-os-debugging` - Debugging techniques for driver issues
- `/testing-strategies` - Cross-platform testing approaches
- `/no-os-project-structure` - Project organization patterns
- Datasheet-specific charging algorithms and electrical limits
