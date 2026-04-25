# Fuel Gauge and Battery Monitoring

Complete guide to implementing battery monitors, fuel gauges, and multi-cell battery management in no-OS.

## Battery Monitor Types

### 1. Cell Voltage Monitoring

Monitor individual cell voltages in series battery packs (e.g., 3S, 4S, 12S lithium packs).

**Example**: MAX17851 - Monitor up to 14 series cells

```c
struct max17851_dev {
    struct no_os_spi_desc *spi_desc;       // SPI interface
    uint8_t num_cells;                     // Number of cells in pack
    uint16_t cell_voltages_mv[14];         // Cell voltage cache
    int32_t pack_current_ma;               // Pack current
    uint8_t balancing_mask;                // Active balancing cells
};

// Initialize for 12S battery pack
struct max17851_init_param init = {
    .spi_init = { /* SPI config */ },
    .num_cells = 12,
};

ret = max17851_init(&monitor, &init);
```

### 2. Coulomb Counting

Integrate current over time to track battery charge state.

```c
// Coulomb counter algorithm
struct coulomb_counter {
    int32_t accumulated_mah;    // Accumulated charge (mAh)
    uint32_t battery_capacity_mah;  // Full capacity
    uint32_t soc_percent;       // State of Charge (%)
};

// Update coulomb counter
void update_coulomb_counter(struct coulomb_counter *cc, 
                             int32_t current_ma, uint32_t delta_ms)
{
    // Integrate current over time
    // Q = I × t (in mAh)
    int32_t charge_delta = (current_ma * delta_ms) / 3600000;
    
    cc->accumulated_mah += charge_delta;
    
    // Clamp to battery capacity
    if (cc->accumulated_mah > cc->battery_capacity_mah)
        cc->accumulated_mah = cc->battery_capacity_mah;
    if (cc->accumulated_mah < 0)
        cc->accumulated_mah = 0;
    
    // Calculate SoC
    cc->soc_percent = (cc->accumulated_mah * 100) / cc->battery_capacity_mah;
}
```

### 3. Voltage-Based SoC Estimation

Estimate State of Charge from open-circuit voltage (OCV).

```c
// Li-Ion OCV-SoC lookup table
static const struct {
    uint32_t voltage_mv;
    uint8_t soc_percent;
} li_ion_ocv_table[] = {
    { 4200, 100 },
    { 4150, 95 },
    { 4100, 90 },
    { 4050, 80 },
    { 4000, 70 },
    { 3950, 60 },
    { 3900, 50 },
    { 3850, 40 },
    { 3800, 30 },
    { 3750, 20 },
    { 3700, 15 },
    { 3650, 10 },
    { 3600, 5 },
    { 3500, 0 },
};

static uint8_t estimate_soc_from_voltage(uint32_t vbat_mv)
{
    // Linear interpolation between table points
    for (int i = 0; i < ARRAY_SIZE(li_ion_ocv_table) - 1; i++) {
        if (vbat_mv >= li_ion_ocv_table[i + 1].voltage_mv) {
            uint32_t v_high = li_ion_ocv_table[i].voltage_mv;
            uint32_t v_low = li_ion_ocv_table[i + 1].voltage_mv;
            uint8_t soc_high = li_ion_ocv_table[i].soc_percent;
            uint8_t soc_low = li_ion_ocv_table[i + 1].soc_percent;
            
            // Linear interpolation
            uint8_t soc = soc_low + ((vbat_mv - v_low) * (soc_high - soc_low)) / 
                                     (v_high - v_low);
            return soc;
        }
    }
    return 0;  // Below minimum voltage
}
```

## Multi-Cell Battery Monitoring

### Reading Cell Voltages

```c
// MAX17851: Monitor up to 14 series cells
uint16_t cell_voltages_mv[14];
const int num_cells = 12;  // 12S pack

for (int i = 0; i < num_cells; i++) {
    ret = max17851_read_cell_voltage(dev, i, &cell_voltages_mv[i]);
    if (ret) {
        pr_err("Failed to read cell %d voltage: %d\n", i, ret);
        continue;
    }
    pr_info("Cell %d: %u mV\n", i, cell_voltages_mv[i]);
}

// Calculate pack voltage
uint32_t pack_voltage_mv = 0;
for (int i = 0; i < num_cells; i++) {
    pack_voltage_mv += cell_voltages_mv[i];
}
pr_info("Pack voltage: %u mV (%u.%u V)\n", 
        pack_voltage_mv, pack_voltage_mv / 1000, 
        (pack_voltage_mv % 1000) / 100);
```

### Cell Imbalance Detection

```c
// Check for cell imbalance
uint16_t min_v = 0xFFFF, max_v = 0;
uint8_t min_cell = 0, max_cell = 0;

for (int i = 0; i < num_cells; i++) {
    if (cell_voltages_mv[i] < min_v) {
        min_v = cell_voltages_mv[i];
        min_cell = i;
    }
    if (cell_voltages_mv[i] > max_v) {
        max_v = cell_voltages_mv[i];
        max_cell = i;
    }
}

uint16_t delta_mv = max_v - min_v;
pr_info("Cell voltage range: %u - %u mV (delta: %u mV)\n",
        min_v, max_v, delta_mv);

// Imbalance thresholds
#define IMBALANCE_WARN_MV   50   // 50mV warning
#define IMBALANCE_FAULT_MV  100  // 100mV fault

if (delta_mv > IMBALANCE_FAULT_MV) {
    pr_err("Cell imbalance fault: %u mV\n", delta_mv);
    pr_err("Min: Cell %d (%u mV), Max: Cell %d (%u mV)\n",
           min_cell, min_v, max_cell, max_v);
    // Start balancing or stop charging
    max17851_enable_balancing(dev, true);
}
else if (delta_mv > IMBALANCE_WARN_MV) {
    pr_warn("Cell imbalance warning: %u mV\n", delta_mv);
}
```

### Cell Balancing

```c
// Active cell balancing
void balance_cells(struct max17851_dev *dev, uint16_t *cell_mv, int num_cells)
{
    uint16_t max_v = 0;
    uint8_t balance_mask = 0;
    
    // Find highest voltage
    for (int i = 0; i < num_cells; i++) {
        if (cell_mv[i] > max_v)
            max_v = cell_mv[i];
    }
    
    // Balance cells within 10mV of highest
    for (int i = 0; i < num_cells; i++) {
        if ((max_v - cell_mv[i]) > 10) {  // More than 10mV below max
            balance_mask |= (1 << i);  // Enable balancing for this cell
        }
    }
    
    if (balance_mask != 0) {
        pr_info("Enabling balancing for cells: 0x%02X\n", balance_mask);
        max17851_set_balancing_mask(dev, balance_mask);
        max17851_enable_balancing(dev, true);
    } else {
        max17851_enable_balancing(dev, false);
    }
}
```

## Pack Current Monitoring

### Current Measurement

```c
// Read pack current (charge/discharge)
int32_t pack_current_ma;
ret = max17851_read_pack_current(dev, &pack_current_ma);

if (pack_current_ma > 0) {
    pr_info("Battery charging: %d mA\n", pack_current_ma);
} else if (pack_current_ma < 0) {
    pr_info("Battery discharging: %d mA\n", -pack_current_ma);
} else {
    pr_info("Battery idle\n");
}

// Calculate power
uint32_t pack_voltage_mv;
max17851_get_pack_voltage(dev, &pack_voltage_mv);
int32_t pack_power_mw = ((int64_t)pack_voltage_mv * pack_current_ma) / 1000;
pr_info("Pack power: %d mW\n", pack_power_mw);
```

### Overcurrent Detection

```c
#define DISCHARGE_OC_LIMIT_MA  10000  // 10A max discharge
#define CHARGE_OC_LIMIT_MA     5000   // 5A max charge

void check_pack_current(int32_t current_ma)
{
    if (current_ma < -DISCHARGE_OC_LIMIT_MA) {
        pr_err("Discharge overcurrent: %d mA\n", current_ma);
        // Disconnect load or reduce discharge rate
    }
    
    if (current_ma > CHARGE_OC_LIMIT_MA) {
        pr_err("Charge overcurrent: %d mA\n", current_ma);
        // Reduce charge current
    }
}
```

## State of Charge (SoC) Estimation

### Hybrid SoC Algorithm

Combine voltage-based and coulomb counting for accurate SoC.

```c
struct battery_state {
    uint8_t soc_percent;          // State of Charge
    uint32_t capacity_mah;        // Full capacity
    int32_t accumulated_mah;      // Coulomb counter
    uint32_t last_update_ms;      // Last update timestamp
};

void update_soc(struct battery_state *bat, uint32_t vbat_mv, int32_t ibat_ma)
{
    uint32_t now_ms = get_system_time_ms();
    uint32_t delta_ms = now_ms - bat->last_update_ms;
    
    // Coulomb counting update
    int32_t charge_delta_mah = (ibat_ma * delta_ms) / 3600000;
    bat->accumulated_mah += charge_delta_mah;
    
    // Clamp to capacity
    if (bat->accumulated_mah > bat->capacity_mah)
        bat->accumulated_mah = bat->capacity_mah;
    if (bat->accumulated_mah < 0)
        bat->accumulated_mah = 0;
    
    // Calculate SoC from coulomb counter
    uint8_t soc_cc = (bat->accumulated_mah * 100) / bat->capacity_mah;
    
    // If battery is at rest (low current), use voltage-based SoC
    if (abs(ibat_ma) < 50) {  // <50mA = at rest
        uint8_t soc_ocv = estimate_soc_from_voltage(vbat_mv);
        
        // Blend coulomb counting and OCV estimate
        bat->soc_percent = (soc_cc + soc_ocv) / 2;
        
        // Recalibrate coulomb counter from OCV
        bat->accumulated_mah = (soc_ocv * bat->capacity_mah) / 100;
    } else {
        // Use coulomb counting during active charge/discharge
        bat->soc_percent = soc_cc;
    }
    
    bat->last_update_ms = now_ms;
}
```

### SoC Reporting

```c
void report_battery_status(struct battery_state *bat, 
                            uint32_t vbat_mv, int32_t ibat_ma)
{
    pr_info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
    pr_info("Battery Status:\n");
    pr_info("  SoC:     %u%%\n", bat->soc_percent);
    pr_info("  Voltage: %u mV (%u.%u V)\n", 
            vbat_mv, vbat_mv / 1000, (vbat_mv % 1000) / 100);
    pr_info("  Current: %d mA (%s)\n", 
            abs(ibat_ma), ibat_ma > 0 ? "charging" : "discharging");
    pr_info("  Capacity: %u / %u mAh\n", 
            bat->accumulated_mah, bat->capacity_mah);
    
    // Time remaining estimate
    if (ibat_ma < -50) {  // Discharging
        uint32_t time_to_empty_min = (bat->accumulated_mah * 60) / (-ibat_ma);
        pr_info("  Time to empty: %u min (%u hrs %u min)\n",
                time_to_empty_min, time_to_empty_min / 60, 
                time_to_empty_min % 60);
    } else if (ibat_ma > 50) {  // Charging
        uint32_t remaining_mah = bat->capacity_mah - bat->accumulated_mah;
        uint32_t time_to_full_min = (remaining_mah * 60) / ibat_ma;
        pr_info("  Time to full: %u min (%u hrs %u min)\n",
                time_to_full_min, time_to_full_min / 60, 
                time_to_full_min % 60);
    }
    pr_info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}
```

## Battery Pack Protection

### Overvoltage/Undervoltage per Cell

```c
#define CELL_OV_MV  4250  // 4.25V overvoltage
#define CELL_UV_MV  3000  // 3.0V undervoltage

void check_cell_voltages(uint16_t *cell_mv, int num_cells)
{
    bool fault = false;
    
    for (int i = 0; i < num_cells; i++) {
        if (cell_mv[i] > CELL_OV_MV) {
            pr_err("Cell %d overvoltage: %u mV\n", i, cell_mv[i]);
            fault = true;
        }
        if (cell_mv[i] < CELL_UV_MV) {
            pr_err("Cell %d undervoltage: %u mV\n", i, cell_mv[i]);
            fault = true;
        }
    }
    
    if (fault) {
        // Disconnect battery pack
        disconnect_battery_pack();
    }
}
```

### Pack Temperature Monitoring

```c
struct battery_temperatures {
    int16_t cell_temp_c[4];   // Multiple temperature sensors
    int16_t pack_temp_c;      // Average pack temperature
};

void monitor_pack_temperature(struct battery_temperatures *temps)
{
    // Read multiple temperature sensors
    max17851_read_temp_sensor(dev, 0, &temps->cell_temp_c[0]);
    max17851_read_temp_sensor(dev, 1, &temps->cell_temp_c[1]);
    max17851_read_temp_sensor(dev, 2, &temps->cell_temp_c[2]);
    max17851_read_temp_sensor(dev, 3, &temps->cell_temp_c[3]);
    
    // Calculate average
    int32_t temp_sum = 0;
    for (int i = 0; i < 4; i++) {
        temp_sum += temps->cell_temp_c[i];
    }
    temps->pack_temp_c = temp_sum / 4;
    
    // Check for hotspots
    int16_t max_temp = temps->cell_temp_c[0];
    int16_t min_temp = temps->cell_temp_c[0];
    for (int i = 1; i < 4; i++) {
        if (temps->cell_temp_c[i] > max_temp)
            max_temp = temps->cell_temp_c[i];
        if (temps->cell_temp_c[i] < min_temp)
            min_temp = temps->cell_temp_c[i];
    }
    
    // Temperature limits
    #define DISCHARGE_TEMP_MAX  60   // 60°C max discharge
    #define CHARGE_TEMP_MAX     45   // 45°C max charge
    #define CHARGE_TEMP_MIN     0    // 0°C min charge
    
    if (max_temp > DISCHARGE_TEMP_MAX) {
        pr_err("Pack overtemperature: %d C\n", max_temp);
        disconnect_battery_pack();
    }
    
    if (max_temp - min_temp > 10) {
        pr_warn("Pack temperature gradient: %d C\n", max_temp - min_temp);
        // Reduce current to prevent hotspot
    }
}
```

## Battery Pack Monitor Example

### Complete 12S Battery Monitor

```c
// Monitor 12S Li-Ion battery pack
struct max17851_dev *monitor;
struct battery_state bat_state = {
    .capacity_mah = 10000,  // 10Ah battery
    .soc_percent = 0,
    .accumulated_mah = 0,
};

ret = max17851_init(&monitor, &init_param);
if (ret) {
    pr_err("Battery monitor init failed: %d\n", ret);
    return ret;
}

const int num_cells = 12;
uint16_t cell_mv[12];
int32_t pack_current_ma;
uint32_t pack_voltage_mv;

// Monitoring loop
while (1) {
    // Read all cells
    for (int i = 0; i < num_cells; i++) {
        max17851_read_cell_voltage(monitor, i, &cell_mv[i]);
    }
    
    // Pack current and voltage
    max17851_read_pack_current(monitor, &pack_current_ma);
    max17851_get_pack_voltage(monitor, &pack_voltage_mv);
    
    // Check cell voltages
    check_cell_voltages(cell_mv, num_cells);
    
    // Check for imbalance
    uint16_t min_v = 0xFFFF, max_v = 0;
    for (int i = 0; i < num_cells; i++) {
        if (cell_mv[i] < min_v) min_v = cell_mv[i];
        if (cell_mv[i] > max_v) max_v = cell_mv[i];
    }
    
    if (max_v - min_v > 100) {
        pr_warn("Cell imbalance detected: %u mV, starting balancing\n",
                max_v - min_v);
        balance_cells(monitor, cell_mv, num_cells);
    }
    
    // Update SoC
    update_soc(&bat_state, pack_voltage_mv, pack_current_ma);
    
    // Report status every 10 seconds
    static uint32_t last_report = 0;
    uint32_t now = get_system_time_ms();
    if (now - last_report > 10000) {
        report_battery_status(&bat_state, pack_voltage_mv, pack_current_ma);
        last_report = now;
    }
    
    // Check overcurrent
    check_pack_current(pack_current_ma);
    
    no_os_mdelay(100);  // 100ms update rate
}
```

## Capacity Learning

### Full Charge Cycle Calibration

```c
void calibrate_battery_capacity(struct battery_state *bat)
{
    uint32_t vbat_mv;
    int32_t ibat_ma;
    
    // Detect full charge
    ltc4162l_get_vbat(dev, &vbat_mv);
    ltc4162l_get_ibat(dev, &ibat_ma);
    
    if (vbat_mv >= 4190 && ibat_ma < 50) {  // Full charge detected
        pr_info("Full charge detected, calibrating capacity\n");
        
        // Record coulomb counter at 100% SoC
        bat->accumulated_mah = bat->capacity_mah;
        bat->soc_percent = 100;
    }
    
    // Detect empty
    if (vbat_mv <= 3200) {  // Empty (cutoff voltage)
        pr_info("Battery empty, calibrating capacity\n");
        
        // Calculate actual capacity from last full charge
        // Capacity = charge delivered from 100% to 0%
        bat->capacity_mah = bat->capacity_mah - bat->accumulated_mah;
        bat->accumulated_mah = 0;
        bat->soc_percent = 0;
        
        pr_info("Learned capacity: %u mAh\n", bat->capacity_mah);
    }
}
```
