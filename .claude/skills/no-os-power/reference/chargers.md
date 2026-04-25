# Battery Chargers

Complete guide to implementing battery charger drivers in no-OS, covering Li-Ion/Li-Po CC-CV charging, MPPT solar charging, and charge management.

## Battery Charging Fundamentals

### Li-Ion/Li-Po CC-CV Charging

**Constant Current - Constant Voltage** (CC-CV) is the standard charging profile for lithium-based batteries.

**Charging Phases**:
1. **Trickle/Precharge**: Low current (C/10) for deeply discharged batteries (V < 3.0V)
2. **Constant Current (CC)**: Full charge current (0.5C - 1C) until voltage reaches target
3. **Constant Voltage (CV)**: Hold voltage at 4.2V, current tapers off
4. **Termination**: Stop when current drops below threshold (C/20 typical)

```
Voltage (V)
   4.2V ┤           ┌───────────────  CV Phase
        │          ╱
   3.0V ┤─────────╱                   CC Phase
        │        ╱
   2.5V ┤───────╱                     Precharge Phase
        │      ╱
        └──────────────────────────> Time
               
Current (A)
   1.0A ┤─────────┐
        │         │
        │         └─────────╲         CC → CV transition
        │                   ╲
  0.05A ┤                    └─────  Termination
        └──────────────────────────> Time
```

### Charge Configuration

```c
// Li-Ion charging parameters
struct ltc4162l_config charge_config = {
    .charge_current_ma = 1000,         // 1A constant current phase (1C for 1Ah battery)
    .charge_voltage_mv = 4200,         // 4.2V constant voltage phase
    .input_current_limit_ma = 1500,    // Input current limit (adapter/USB)
    .precharge_current_ma = 100,       // Trickle charge current (C/10)
    .termination_current_ma = 50,      // C/20 termination threshold
    .charge_timeout_min = 240,         // 4-hour safety timeout
};

ret = ltc4162l_configure(dev, &charge_config);
if (ret) {
    pr_err("Charger configuration failed: %d\n", ret);
    return ret;
}

ret = ltc4162l_enable_charging(dev, true);
```

### Charge States

```c
enum ltc4162l_charge_status {
    LTC4162L_BAT_DETECT_FAILED,        // No battery detected
    LTC4162L_BAT_DETECT,               // Detecting battery presence
    LTC4162L_PRECHARGE,                // Trickle charge (V < Vprecharge)
    LTC4162L_CC_CV_CHARGE,             // Main charging (CC or CV phase)
    LTC4162L_NTC_PAUSE,                // Temperature suspend
    LTC4162L_TIMER_TERM,               // Timeout termination
    LTC4162L_C_OVER_X_TERM,            // Current termination (I < Iterm)
    LTC4162L_MAX_CHARGE_TIME_FAULT,    // Safety timeout exceeded
    LTC4162L_BAT_MISSING_FAULT,        // Battery removed during charge
    LTC4162L_BAT_SHORT_FAULT,          // Battery short circuit
};

enum ltc4162l_charge_status status;
ret = ltc4162l_get_charge_status(dev, &status);

switch (status) {
case LTC4162L_PRECHARGE:
    pr_info("Precharging (battery voltage low)\n");
    break;
case LTC4162L_CC_CV_CHARGE:
    pr_info("Fast charging (CC-CV mode)\n");
    break;
case LTC4162L_C_OVER_X_TERM:
    pr_info("Charge complete (current termination)\n");
    break;
case LTC4162L_BAT_MISSING_FAULT:
    pr_err("Battery not detected\n");
    break;
case LTC4162L_NTC_PAUSE:
    pr_warn("Charging paused due to temperature\n");
    break;
}
```

### Charge Monitoring

```c
// Monitor charging progress
while (charging) {
    enum ltc4162l_charge_status status;
    uint32_t vbat_mv, ibat_ma;
    int16_t bat_temp_c;
    
    ltc4162l_get_charge_status(dev, &status);
    ltc4162l_get_vbat(dev, &vbat_mv);
    ltc4162l_get_ibat(dev, &ibat_ma);
    ltc4162l_get_bat_temp(dev, &bat_temp_c);
    
    pr_info("Status: %d, Vbat: %u mV, Ibat: %u mA, Temp: %d C\n",
            status, vbat_mv, ibat_ma, bat_temp_c);
    
    // Check for completion
    if (status == LTC4162L_C_OVER_X_TERM) {
        pr_info("Charging complete\n");
        break;
    }
    
    // Check for faults
    if (status == LTC4162L_BAT_MISSING_FAULT ||
        status == LTC4162L_MAX_CHARGE_TIME_FAULT) {
        pr_err("Charging fault detected\n");
        ltc4162l_enable_charging(dev, false);
        break;
    }
    
    no_os_mdelay(1000);  // Update every second
}
```

## USB Battery Charger

### USB Current Limits

```c
#define USB_CURRENT_SDP     100   // USB 2.0 Standard Downstream Port (unconfigured)
#define USB_CURRENT_SDP_CFG 500   // USB 2.0 SDP (configured)
#define USB_CURRENT_CDP     1500  // USB Charging Downstream Port
#define USB_CURRENT_DCP     1500  // USB Dedicated Charging Port
#define USB_CURRENT_PD      3000  // USB Power Delivery (variable)

// Configure for USB charging
struct adp5055_init_param init = {
    .vbus_ilim_ma = USB_CURRENT_SDP_CFG,  // Start with USB 2.0 limit
    .ichg_ma = 500,                        // 0.5C charge rate
    .vtrm_mv = 4200,                       // 4.2V for Li-Ion
    .vindpm_mv = 4500,                     // VBUS threshold
    .enable_charger = true,
};

ret = adp5055_init(&dev, &init);
```

### Charger Type Detection

```c
// Detect charger type and adjust current limit
enum adp5055_charger_type type;
ret = adp5055_get_charger_type(dev, &type);

switch (type) {
case ADP5055_CHG_TYPE_SDP:
    pr_info("USB SDP detected (500mA max)\n");
    adp5055_set_input_current_limit(dev, USB_CURRENT_SDP_CFG);
    adp5055_set_charge_current(dev, 500);
    break;
    
case ADP5055_CHG_TYPE_CDP:
    pr_info("USB CDP detected (1.5A max)\n");
    adp5055_set_input_current_limit(dev, USB_CURRENT_CDP);
    adp5055_set_charge_current(dev, 1000);
    break;
    
case ADP5055_CHG_TYPE_DCP:
    pr_info("Dedicated charger detected (1.5A max)\n");
    adp5055_set_input_current_limit(dev, USB_CURRENT_DCP);
    adp5055_set_charge_current(dev, 1000);
    break;
    
case ADP5055_CHG_TYPE_NONE:
    pr_info("No charger detected\n");
    adp5055_enable_charger(dev, false);
    break;
}
```

### USB VBUS Monitoring

```c
// Monitor VBUS for plug/unplug events
bool vbus_present = false;

void charger_monitor_task(void)
{
    bool current_vbus;
    int ret;
    
    ret = adp5055_get_vbus_status(dev, &current_vbus);
    if (ret)
        return;
    
    // VBUS connected
    if (current_vbus && !vbus_present) {
        pr_info("VBUS connected\n");
        
        // Detect charger type
        enum adp5055_charger_type type;
        adp5055_get_charger_type(dev, &type);
        
        // Configure and enable charging
        configure_charger_for_type(dev, type);
        adp5055_enable_charger(dev, true);
        
        vbus_present = true;
    }
    // VBUS disconnected
    else if (!current_vbus && vbus_present) {
        pr_info("VBUS disconnected\n");
        adp5055_enable_charger(dev, false);
        vbus_present = false;
    }
}
```

## Solar MPPT Charger

### MPPT (Maximum Power Point Tracking)

MPPT optimizes solar panel power extraction by tracking the voltage point where Power = Voc × 0.95 (typically).

**MPPT Algorithm**:
- Measure solar panel open-circuit voltage (Voc)
- Set operating point to Voc × MPPT_RATIO (e.g., 95%)
- Continuously adjust to track maximum power point

```c
// Solar panel to battery with MPPT
struct lt8491_init_param init = {
    .output_voltage_mv = 14400,  // 12V lead-acid (14.4V float voltage)
    .charge_current_ma = 5000,   // 5A max charge current
    .enable_mppt = true,
    .mppt_ratio = 95,            // 95% of Voc (typical)
};

ret = lt8491_init(&dev, &init);
if (ret) {
    pr_err("LT8491 init failed: %d\n", ret);
    return ret;
}
```

### MPPT Monitoring and Adjustment

```c
// Monitor solar charging with MPPT
while (charging) {
    uint32_t vin_mv, vout_mv, iout_ma, input_power_mw;
    enum lt8491_charge_state state;
    
    lt8491_get_input_voltage(dev, &vin_mv);
    lt8491_get_output_voltage(dev, &vout_mv);
    lt8491_get_charge_current(dev, &iout_ma);
    lt8491_get_input_power(dev, &input_power_mw);
    lt8491_get_charge_state(dev, &state);
    
    pr_info("Solar: %u mV, %u mW | Bat: %u mV, %u mA | State: %d\n",
            vin_mv, input_power_mw, vout_mv, iout_ma, state);
    
    // Adjust MPPT ratio based on conditions
    if (input_power_mw < 1000) {  // Low light
        lt8491_set_mppt_ratio(dev, 93);  // Lower ratio for low light
    } else {
        lt8491_set_mppt_ratio(dev, 95);  // Optimal ratio
    }
    
    no_os_mdelay(1000);
}
```

### Multi-Stage Solar Charging

```c
enum solar_charge_stage {
    SOLAR_BULK,      // CC phase: max current
    SOLAR_ABSORPTION, // CV phase: hold voltage
    SOLAR_FLOAT,     // Maintenance: lower voltage
};

static enum solar_charge_stage current_stage = SOLAR_BULK;

void solar_charge_state_machine(void)
{
    uint32_t vbat_mv, ibat_ma;
    
    lt8491_get_output_voltage(dev, &vbat_mv);
    lt8491_get_charge_current(dev, &ibat_ma);
    
    switch (current_stage) {
    case SOLAR_BULK:
        // Bulk charging: constant current until absorption voltage
        if (vbat_mv >= 14400) {  // 14.4V for 12V lead-acid
            pr_info("Entering absorption stage\n");
            current_stage = SOLAR_ABSORPTION;
        }
        break;
        
    case SOLAR_ABSORPTION:
        // Hold at absorption voltage until current drops
        if (ibat_ma < 200) {  // C/20 termination
            pr_info("Entering float stage\n");
            lt8491_set_output_voltage(dev, 13600);  // 13.6V float
            current_stage = SOLAR_FLOAT;
        }
        break;
        
    case SOLAR_FLOAT:
        // Maintain float voltage
        if (vbat_mv < 13000) {  // Battery discharged
            pr_info("Battery voltage low, returning to bulk\n");
            lt8491_set_output_voltage(dev, 14400);
            current_stage = SOLAR_BULK;
        }
        break;
    }
}
```

## Temperature Management

### NTC Thermistor Monitoring

```c
// Battery temperature monitoring with NTC
int16_t bat_temp_c;
ret = ltc4162l_get_bat_temp(dev, &bat_temp_c);

// Temperature limits for Li-Ion charging
#define CHARGE_TEMP_MIN  0    // 0°C minimum
#define CHARGE_TEMP_MAX  45   // 45°C maximum
#define CHARGE_TEMP_WARN 40   // 40°C warning

if (bat_temp_c < CHARGE_TEMP_MIN || bat_temp_c > CHARGE_TEMP_MAX) {
    pr_err("Battery temp out of safe range: %d C\n", bat_temp_c);
    ltc4162l_enable_charging(dev, false);
}
else if (bat_temp_c > CHARGE_TEMP_WARN) {
    // Reduce charge current at high temperature
    uint32_t reduced_current = CHARGE_CURRENT_NOMINAL * 70 / 100;  // 70%
    ltc4162l_set_charge_current(dev, reduced_current);
    pr_warn("High battery temp (%d C): reducing current to %u mA\n",
            bat_temp_c, reduced_current);
}
```

### Temperature-Based Charge Adjustment

```c
static uint32_t get_charge_current_for_temp(int16_t temp_c)
{
    // Temperature-based derating table
    if (temp_c < 0)
        return 0;                           // No charging below 0°C
    else if (temp_c < 10)
        return CHARGE_CURRENT_NOMINAL / 2;  // 50% below 10°C
    else if (temp_c < 45)
        return CHARGE_CURRENT_NOMINAL;      // 100% normal range
    else if (temp_c < 50)
        return CHARGE_CURRENT_NOMINAL / 2;  // 50% above 45°C
    else
        return 0;                           // No charging above 50°C
}

void update_charge_current_for_temperature(void)
{
    int16_t bat_temp_c;
    uint32_t new_current;
    
    ltc4162l_get_bat_temp(dev, &bat_temp_c);
    new_current = get_charge_current_for_temp(bat_temp_c);
    
    if (new_current > 0) {
        ltc4162l_set_charge_current(dev, new_current);
        ltc4162l_enable_charging(dev, true);
    } else {
        ltc4162l_enable_charging(dev, false);
        pr_warn("Temperature %d C: charging disabled\n", bat_temp_c);
    }
}
```

## Input Current Management

### Input Current Limit (VINDPM)

```c
// Input voltage-based dynamic power management
// Prevents input voltage from sagging below threshold

#define VINDPM_THRESHOLD_MV  4500  // 4.5V minimum input

ret = adp5055_set_vindpm_threshold(dev, VINDPM_THRESHOLD_MV);

// When VIN drops below threshold:
// - Charger automatically reduces input current
// - Prevents brownout of upstream supply
// - Allows system to continue operating
```

### Input Current Limiting

```c
// Set input current limit based on source
void configure_input_current_limit(enum power_source source)
{
    uint32_t ilim_ma;
    
    switch (source) {
    case POWER_SOURCE_USB_SDP:
        ilim_ma = 500;   // USB 2.0 Standard Downstream Port
        break;
    case POWER_SOURCE_USB_CDP:
        ilim_ma = 1500;  // USB Charging Downstream Port
        break;
    case POWER_SOURCE_WALL_ADAPTER:
        ilim_ma = 2000;  // Wall adapter (2A)
        break;
    case POWER_SOURCE_SOLAR:
        ilim_ma = 3000;  // Solar panel (no strict limit)
        break;
    default:
        ilim_ma = 100;   // Safe default
        break;
    }
    
    adp5055_set_input_current_limit(dev, ilim_ma);
    pr_info("Input current limit set to %u mA\n", ilim_ma);
}
```

## Charge Termination

### Multiple Termination Methods

```c
// Implement multiple termination conditions for safety
bool is_charging_complete(void)
{
    enum ltc4162l_charge_status status;
    uint32_t vbat_mv, ibat_ma;
    uint32_t charge_time_min;
    
    ltc4162l_get_charge_status(dev, &status);
    ltc4162l_get_vbat(dev, &vbat_mv);
    ltc4162l_get_ibat(dev, &ibat_ma);
    ltc4162l_get_charge_time(dev, &charge_time_min);
    
    // Method 1: Current termination (primary)
    if (status == LTC4162L_C_OVER_X_TERM) {
        pr_info("Charge complete: current termination\n");
        return true;
    }
    
    // Method 2: Voltage + low current (backup)
    if (vbat_mv >= 4190 && ibat_ma < 50) {  // 4.19V and <C/20
        pr_info("Charge complete: voltage + low current\n");
        return true;
    }
    
    // Method 3: Safety timeout (fault condition)
    if (charge_time_min > 240) {  // 4 hours
        pr_warn("Charge complete: safety timeout\n");
        return true;
    }
    
    // Method 4: Charge status indicates termination
    if (status == LTC4162L_TIMER_TERM) {
        pr_info("Charge complete: timer termination\n");
        return true;
    }
    
    return false;
}
```

### Top-Off Charging

```c
// After main charge complete, implement top-off charge
void top_off_charge(void)
{
    // Wait after charge completion
    no_os_mdelay(60000);  // 1 minute
    
    // Check if voltage dropped
    uint32_t vbat_mv;
    ltc4162l_get_vbat(dev, &vbat_mv);
    
    if (vbat_mv < 4150) {  // Voltage dropped during rest
        pr_info("Starting top-off charge\n");
        
        // Re-enable charging with reduced current
        ltc4162l_set_charge_current(dev, 200);  // C/5
        ltc4162l_enable_charging(dev, true);
        
        // Monitor for completion
        while (!is_charging_complete()) {
            no_os_mdelay(10000);
        }
        
        ltc4162l_enable_charging(dev, false);
        pr_info("Top-off charge complete\n");
    }
}
```

## Charge Safety Features

### Overvoltage Protection

```c
// Battery overvoltage protection
#define VBAT_OV_THRESHOLD_MV  4250  // 4.25V fault threshold

void check_battery_overvoltage(void)
{
    uint32_t vbat_mv;
    ltc4162l_get_vbat(dev, &vbat_mv);
    
    if (vbat_mv > VBAT_OV_THRESHOLD_MV) {
        pr_err("Battery overvoltage detected: %u mV\n", vbat_mv);
        
        // Immediate shutdown
        ltc4162l_enable_charging(dev, false);
        
        // Disable battery connection if possible
        // (requires external FET control)
    }
}
```

### Charge Timer Watchdog

```c
#define MAX_CHARGE_TIME_MIN  480  // 8 hours max

static uint32_t charge_start_time = 0;

void start_charging_with_timer(void)
{
    charge_start_time = get_system_time_ms();
    ltc4162l_enable_charging(dev, true);
}

void check_charge_timeout(void)
{
    uint32_t elapsed_min = (get_system_time_ms() - charge_start_time) / 60000;
    
    if (elapsed_min > MAX_CHARGE_TIME_MIN) {
        pr_err("Charge timeout: %u minutes elapsed\n", elapsed_min);
        ltc4162l_enable_charging(dev, false);
        
        // Check for battery fault
        uint32_t vbat_mv, ibat_ma;
        ltc4162l_get_vbat(dev, &vbat_mv);
        ltc4162l_get_ibat(dev, &ibat_ma);
        
        pr_err("Final state: Vbat=%u mV, Ibat=%u mA\n", vbat_mv, ibat_ma);
    }
}
```

### Battery Disconnect Detection

```c
void check_battery_connection(void)
{
    enum ltc4162l_charge_status status;
    ltc4162l_get_charge_status(dev, &status);
    
    if (status == LTC4162L_BAT_MISSING_FAULT) {
        pr_err("Battery disconnected during charging\n");
        
        // Disable charging
        ltc4162l_enable_charging(dev, false);
        
        // Wait for battery reconnection
        no_os_mdelay(1000);
        
        // Retry detection
        ltc4162l_get_charge_status(dev, &status);
        if (status != LTC4162L_BAT_MISSING_FAULT) {
            pr_info("Battery reconnected, resuming charge\n");
            ltc4162l_enable_charging(dev, true);
        }
    }
}
```
