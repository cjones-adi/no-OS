# Regulators and PMICs

Complete guide to implementing switching regulators, linear regulators (LDOs), and multi-channel PMICs in no-OS.

## Regulator Types

### 1. Switching Regulators

#### Buck Converter (Step-Down)
- **Topology**: Vin > Vout
- **Efficiency**: 85-95%+
- **Components**: Inductor, output capacitor, control IC
- **Use cases**: High current, moderate voltage step-down

**Example**: LT7182S channel configured as buck
```c
struct lt7182s_init_param init = {
    .channels[0] = {
        .vout_mv = 1800,         // 1.8V output
        .iout_max_ma = 3000,     // 3A max
        .enabled = true,
    },
};

// Typical efficiency: 90-93% for 5V→1.8V conversion
```

#### Boost Converter (Step-Up)
- **Topology**: Vout > Vin
- **Efficiency**: 85-92%
- **Components**: Inductor, output capacitor, control IC
- **Use cases**: Battery to higher voltage rail

**Example**: Boost from 3.3V battery to 5V output
```c
// Configure for boost operation
// 3.3V battery → 5V output @ 500mA
ret = boost_regulator_set_vout(dev, 5000);  // 5V
ret = boost_regulator_set_iout_max(dev, 500);  // 500mA
```

#### Buck-Boost Converter
- **Topology**: Vout can be < or > Vin
- **Efficiency**: 85-95%
- **Components**: Inductor, output capacitor, control IC
- **Use cases**: Wide input range, regulated output

**Example**: LT8491 buck-boost battery charger
```c
struct lt8491_init_param init = {
    .output_voltage_mv = 14400,   // 12V lead-acid (14.4V float)
    .charge_current_ma = 5000,    // 5A max
};

// Operates in buck mode when Vin > 14.4V (solar high voltage)
// Operates in boost mode when Vin < 14.4V (solar low voltage)
```

### 2. Linear Regulators (LDO)

#### Characteristics
- **Simple topology**: No inductor required
- **Efficiency**: Eff = Vout / Vin (dissipates difference as heat)
- **Low noise**: No switching noise
- **Fast transient response**: Microsecond settling
- **Dropout voltage**: Minimum Vin - Vout difference (50-300mV)

**Example**: 3.3V LDO from 5V supply
```c
// Efficiency = 3.3V / 5V = 66%
// Power dissipation = (5V - 3.3V) × Iload = 1.7V × Iload
// At 100mA: 170mW dissipated as heat
```

#### When to Use LDO vs Switcher
- **Use LDO when**:
  - Low noise critical (analog circuits, ADC references)
  - Small voltage drop (Vin close to Vout)
  - Low current (<100mA typically)
  - Simple design, small PCB area
  
- **Use Switcher when**:
  - High current (>100mA)
  - Large voltage conversion
  - Efficiency critical (battery-powered)
  - Heat dissipation is concern

### 3. PMICs (Power Management ICs)

Multi-channel regulators with integrated sequencing, monitoring, and control.

**Example**: LT7182S dual-channel PMIC
```c
struct lt7182s_dev {
    struct no_os_i2c_desc *i2c_desc;       // PMBus interface
    uint8_t i2c_addr;
    struct lt7182s_channel_state ch[2];    // Independent channels
};

// Channel 0: Core voltage (1.8V)
// Channel 1: I/O voltage (3.3V)
```

## Voltage and Current Control

### Setting Output Voltage

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

### Setting Current Limits

```c
// Output current limit
uint32_t current_limit_ma = 1500;
ret = lt7182s_set_iout_max(dev, LT7182S_CH0, current_limit_ma);

// Read actual current
uint32_t iout_ma;
ret = lt7182s_read_iout(dev, LT7182S_CH0, &iout_ma);

// Current limit with margin (typical: 20-30% above nominal)
uint32_t nominal_current_ma = 1000;
uint32_t limit_with_margin = nominal_current_ma * 130 / 100;  // +30%
ret = lt7182s_set_iout_max(dev, LT7182S_CH0, limit_with_margin);
```

## Enable/Disable Control

### Basic Enable/Disable

```c
// Enable channel
ret = lt7182s_set_operation(dev, LT7182S_CH0, true);

// Disable channel
ret = lt7182s_set_operation(dev, LT7182S_CH1, false);

// Read enable state
bool enabled;
ret = lt7182s_get_operation(dev, LT7182S_CH0, &enabled);
pr_info("Channel 0 is %s\n", enabled ? "enabled" : "disabled");
```

### Enable with Power Good Wait

```c
ret = lt7182s_set_operation(dev, LT7182S_CH0, true);
if (ret)
    return ret;

// Wait for power good
bool pg;
uint32_t timeout = 100;  // 100ms timeout
while (timeout--) {
    ret = lt7182s_get_power_good(dev, LT7182S_CH0, &pg);
    if (ret)
        return ret;
    if (pg)
        break;
    no_os_mdelay(1);
}

if (!pg) {
    pr_err("Channel 0 power good timeout\n");
    lt7182s_set_operation(dev, LT7182S_CH0, false);
    return -ETIMEDOUT;
}

pr_info("Channel 0 powered up successfully\n");
```

## Power Monitoring

### Voltage/Current Measurement

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

// Calculate efficiency
uint32_t iin_ma;
ret = lt7182s_read_iin(dev, &iin_ma);
uint32_t pin_mw = (uint64_t)vin_mv * iin_ma / 1000;
uint32_t efficiency_pct = (power_mw * 100) / pin_mw;
pr_info("Efficiency: %u%%\n", efficiency_pct);
```

### Temperature Monitoring

```c
// Die temperature
int16_t die_temp_c;
ret = lt7182s_get_die_temp(dev, &die_temp_c);
pr_info("Die temperature: %d C\n", die_temp_c);

// Temperature limits
if (die_temp_c > 125) {
    pr_err("Die overtemperature: %d C\n", die_temp_c);
    // Reduce load or shut down
    lt7182s_set_operation(dev, LT7182S_CH0, false);
}

// Thermal derating
if (die_temp_c > 100) {
    // Reduce current limit by 20%
    uint32_t current_limit;
    lt7182s_get_iout_max(dev, LT7182S_CH0, &current_limit);
    lt7182s_set_iout_max(dev, LT7182S_CH0, current_limit * 80 / 100);
    pr_warn("Thermal derating: reduced current to 80%%\n");
}
```

## Power Sequencing

### Startup Sequencing

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
    // Set voltage
    ret = lt7182s_set_vout(rails[i].dev, rails[i].channel,
                           rails[i].voltage_mv);
    if (ret)
        goto error_shutdown;
    
    // Enable channel
    ret = lt7182s_set_operation(rails[i].dev, rails[i].channel, true);
    if (ret)
        goto error_shutdown;

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
        ret = -ETIMEDOUT;
        goto error_shutdown;
    }

    // Inter-rail delay
    no_os_mdelay(rails[i].delay_ms);
    pr_info("Rail %d (%u mV) powered up\n", i, rails[i].voltage_mv);
}

return 0;

error_shutdown:
    // Shutdown in reverse order
    for (int j = i - 1; j >= 0; j--) {
        lt7182s_set_operation(rails[j].dev, rails[j].channel, false);
        no_os_mdelay(5);
    }
    return ret;
```

### Shutdown Sequencing

```c
// Power down in reverse order
for (int i = ARRAY_SIZE(rails) - 1; i >= 0; i--) {
    ret = lt7182s_set_operation(rails[i].dev, rails[i].channel, false);
    if (ret)
        pr_err("Failed to disable rail %d\n", i);
    
    no_os_mdelay(5);  // Discharge delay
    pr_info("Rail %d powered down\n", i);
}
```

## Dynamic Voltage Scaling (DVS)

### DVS for Power Optimization

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
    uint32_t current_voltage_mv;
    int ret;
    
    // Get current voltage
    ret = lt7182s_read_vout(dev, LT7182S_CH0, &current_voltage_mv);
    if (ret)
        return ret;

    // When increasing performance: voltage up first, then frequency
    if (dvs_table[mode].voltage_mv > current_voltage_mv) {
        ret = lt7182s_set_vout(dev, LT7182S_CH0,
                               dvs_table[mode].voltage_mv);
        if (ret)
            return ret;
        
        no_os_udelay(100);  // Settling time (100us typical)
        
        ret = set_cpu_frequency(dvs_table[mode].cpu_freq_mhz);
        if (ret)
            return ret;
    }
    // When decreasing performance: frequency down first, then voltage
    else {
        ret = set_cpu_frequency(dvs_table[mode].cpu_freq_mhz);
        if (ret)
            return ret;
        
        ret = lt7182s_set_vout(dev, LT7182S_CH0,
                               dvs_table[mode].voltage_mv);
        if (ret)
            return ret;
    }

    pr_info("Performance mode: %d (Vcore=%u mV, Freq=%u MHz)\n",
            mode, dvs_table[mode].voltage_mv, dvs_table[mode].cpu_freq_mhz);
    
    return 0;
}
```

### DVS State Machine

```c
static enum performance_mode current_mode = PERF_NORMAL;

int dvs_increase_performance(void)
{
    enum performance_mode new_mode;
    
    switch (current_mode) {
    case PERF_LOW_POWER:
        new_mode = PERF_NORMAL;
        break;
    case PERF_NORMAL:
        new_mode = PERF_TURBO;
        break;
    case PERF_TURBO:
        return 0;  // Already at max
    default:
        return -EINVAL;
    }
    
    int ret = set_performance_mode(new_mode);
    if (ret == 0)
        current_mode = new_mode;
    
    return ret;
}

int dvs_decrease_performance(void)
{
    enum performance_mode new_mode;
    
    switch (current_mode) {
    case PERF_TURBO:
        new_mode = PERF_NORMAL;
        break;
    case PERF_NORMAL:
        new_mode = PERF_LOW_POWER;
        break;
    case PERF_LOW_POWER:
        return 0;  // Already at min
    default:
        return -EINVAL;
    }
    
    int ret = set_performance_mode(new_mode);
    if (ret == 0)
        current_mode = new_mode;
    
    return ret;
}
```

## Protection Features

### Overcurrent Protection

```c
// Set overcurrent threshold
uint32_t oc_limit_ma = 2000;  // 2A limit
ret = lt7182s_set_iout_oc_fault_limit(dev, LT7182S_CH0, oc_limit_ma);

// Configure OC response (warning vs fault)
ret = lt7182s_set_iout_oc_warn_limit(dev, LT7182S_CH0, 1800);  // 1.8A warning

// Read OC status
uint8_t status;
ret = lt7182s_read_status_iout(dev, LT7182S_CH0, &status);
if (status & LT7182S_IOUT_OC_FAULT) {
    pr_err("Overcurrent fault detected\n");
    lt7182s_clear_faults(dev);
}
```

### Overvoltage/Undervoltage Protection

```c
// Set overvoltage threshold (typically +10% of nominal)
uint32_t ov_limit_mv = 3600;  // 10% above nominal 3.3V
ret = lt7182s_set_vout_ov_fault_limit(dev, LT7182S_CH0, ov_limit_mv);

// Set undervoltage threshold (typically -10% of nominal)
uint32_t uv_limit_mv = 3000;  // 10% below nominal
ret = lt7182s_set_vout_uv_fault_limit(dev, LT7182S_CH0, uv_limit_mv);

// Read voltage fault status
uint8_t status;
ret = lt7182s_read_status_vout(dev, LT7182S_CH0, &status);
if (status & LT7182S_VOUT_OV_FAULT) {
    pr_err("Overvoltage fault: output too high\n");
}
if (status & LT7182S_VOUT_UV_FAULT) {
    pr_err("Undervoltage fault: output too low\n");
}
```

### Overtemperature Protection

```c
// Set overtemperature threshold
ret = lt7182s_set_ot_fault_limit(dev, 125);  // 125°C fault
ret = lt7182s_set_ot_warn_limit(dev, 110);   // 110°C warning

// Read temperature status
uint8_t status;
ret = lt7182s_read_status_temperature(dev, &status);
if (status & LT7182S_OT_FAULT) {
    pr_err("Overtemperature fault: shutting down\n");
    lt7182s_set_operation(dev, LT7182S_CH0, false);
}
if (status & LT7182S_OT_WARN) {
    pr_warn("Overtemperature warning: reducing current\n");
    // Implement thermal derating
}
```

### Fault Handling

```c
// Read comprehensive fault status
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
if (fault_status & LT7182S_STATUS_INPUT) {
    pr_err("Input fault (UVLO or OV)\n");
}

// Clear latched faults
ret = lt7182s_clear_faults(dev);

// Attempt recovery
no_os_mdelay(100);  // Allow fault condition to clear
ret = lt7182s_set_operation(dev, LT7182S_CH0, true);
if (ret) {
    pr_err("Fault recovery failed\n");
}
```

## Multi-Rail PMIC Example

### Complete PMIC Configuration

```c
// Configure multiple rails with sequencing
struct lt7182s_dev *pmic;
struct lt7182s_init_param init_param = {
    .i2c_init = {
        .device_id = 0,
        .max_speed_hz = 400000,  // 400kHz I2C
        .slave_address = 0x4F,
    },
    .enable_pec = true,  // PMBus PEC for reliability
    .channels[0] = {
        .vout_mv = 1800,           // 1.8V core rail
        .iout_max_ma = 3000,       // 3A limit
        .vout_ov_limit_mv = 2000,  // +11% OV threshold
        .vout_uv_limit_mv = 1600,  // -11% UV threshold
        .enabled = false,          // Don't enable yet
    },
    .channels[1] = {
        .vout_mv = 3300,           // 3.3V I/O rail
        .iout_max_ma = 1000,       // 1A limit
        .vout_ov_limit_mv = 3600,
        .vout_uv_limit_mv = 3000,
        .enabled = false,
    },
};

ret = lt7182s_init(&pmic, &init_param);
if (ret) {
    pr_err("PMIC init failed: %d\n", ret);
    return ret;
}

// Power up sequence: CH0 first, then CH1
ret = lt7182s_set_operation(pmic, LT7182S_CH0, true);
no_os_mdelay(10);
ret = lt7182s_set_operation(pmic, LT7182S_CH1, true);

// Monitor all rails
uint32_t vout0, vout1, iout0, iout1;
lt7182s_read_vout(pmic, LT7182S_CH0, &vout0);
lt7182s_read_vout(pmic, LT7182S_CH1, &vout1);
lt7182s_read_iout(pmic, LT7182S_CH0, &iout0);
lt7182s_read_iout(pmic, LT7182S_CH1, &iout1);

pr_info("Core: %u mV, %u mA\n", vout0, iout0);
pr_info("I/O:  %u mV, %u mA\n", vout1, iout1);
```
