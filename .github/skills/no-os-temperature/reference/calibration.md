# Temperature Sensor Calibration and Accuracy

This document covers calibration techniques, accuracy considerations, and best practices for achieving precise temperature measurements.

## Calibration Methods

### Offset Calibration (Digital Sensors)

Single-point calibration for correcting systematic offset errors.

```c
// Read temperature in known environment
float measured_temp;
ret = adt7420_get_temperature(dev, &measured_temp);

// Known reference temperature
float reference_temp = 25.0;  // Ice bath, temp chamber, etc.

// Calculate offset
float offset = reference_temp - measured_temp;
pr_info("Calibration offset: %.3f C\n", offset);

// Apply offset in software
float calibrated_temp;
ret = adt7420_get_temperature(dev, &calibrated_temp);
calibrated_temp += offset;
```

**When to use**:
- Factory calibration
- Known systematic offset
- Quick field calibration
- Simple correction needed

**Limitations**:
- Doesn't correct gain errors
- Only valid near calibration temperature
- Assumes linear response

### Two-Point Calibration (RTD)

Linear calibration using two reference temperatures for gain and offset correction.

```c
// Single-point calibration (at 0°C ice bath)
float ice_temp;
ret = max31865_read_temp(dev, &ice_temp);
float offset_0c = 0.0 - ice_temp;

// Two-point calibration (0°C and 100°C boiling water)
float ice_temp, boil_temp;
ret = max31865_read_temp(dev, &ice_temp);
// ... heat to boiling ...
ret = max31865_read_temp(dev, &boil_temp);

float gain = 100.0 / (boil_temp - ice_temp);
float offset = -ice_temp * gain;

// Apply calibration
float raw_temp;
ret = max31865_read_temp(dev, &raw_temp);
float calibrated = raw_temp * gain + offset;
```

**When to use**:
- Wide temperature range
- Gain error present
- Higher accuracy required
- RTD or thermocouple systems

**Reference points**:
- Ice bath: 0°C (easy, accurate)
- Boiling water: 100°C (pressure dependent)
- Body temperature: 37°C (convenient)
- Dry block calibrator (industrial)

### Multi-Point Calibration

For highly non-linear sensors or best accuracy across wide range.

```c
// Calibration table (temperature vs. measured)
struct calibration_point {
    float reference;  // True temperature
    float measured;   // Sensor reading
};

struct calibration_point cal_table[] = {
    { -40.0, -39.2 },
    {   0.0,   0.5 },
    {  25.0,  25.1 },
    {  50.0,  49.8 },
    { 100.0, 100.3 },
    { 150.0, 149.5 },
};

// Linear interpolation
float apply_calibration(float measured_temp)
{
    int i;
    
    // Find bracketing points
    for (i = 0; i < ARRAY_SIZE(cal_table) - 1; i++) {
        if (measured_temp <= cal_table[i+1].measured)
            break;
    }
    
    // Interpolate
    float x0 = cal_table[i].measured;
    float x1 = cal_table[i+1].measured;
    float y0 = cal_table[i].reference;
    float y1 = cal_table[i+1].reference;
    
    float corrected = y0 + (measured_temp - x0) * (y1 - y0) / (x1 - x0);
    
    return corrected;
}
```

**When to use**:
- Wide temperature range (>100°C)
- Non-linear response
- Maximum accuracy needed
- Precision calibration chamber available

### LTC2983 Custom Calibration

Custom coefficients for non-standard sensors.

```c
// Custom Steinhart-Hart coefficients for thermistor
struct ltc2983_steinhart_hart custom_thermistor = {
    .a = 1.12874e-3,
    .b = 2.34289e-4,
    .c = 8.76543e-8,
};

ret = ltc2983_set_custom_steinhart_hart(dev, 10, &custom_thermistor);

// Custom RTD coefficients (Callendar-Van Dusen)
struct ltc2983_rtd_custom custom_rtd = {
    .r0 = 100.0,      // Resistance at 0°C
    .a = 3.9083e-3,
    .b = -5.775e-7,
    .c = -4.183e-12,
};

ret = ltc2983_set_custom_rtd(dev, 5, &custom_rtd);
```

**When to use**:
- Custom RTD/thermistor
- Specific calibration certificate
- Non-standard sensor curves
- Best accuracy with LTC2983

## RTD Calibration Details

### Reference Resistor Accuracy

The reference resistor value directly affects measurement accuracy.

```c
// Measure actual Rref value with precision DMM
// Example: marked 4.00k, measured 4.02k

struct max31865_init_param init = {
    .r_ref = 4020,  // Use measured value, not nominal
    // ...
};

// Accuracy impact:
// 1% Rref error = 1% temperature error
// 0.1% Rref error = 0.1% temperature error
```

**Best practices**:
- Use 0.1% or better precision resistor
- Measure actual value with calibrated DMM
- Account for temperature coefficient
- Update firmware with measured value

### Wire Resistance Compensation

Lead resistance affects RTD accuracy significantly.

```c
// 2-wire: No compensation
// Lead resistance adds directly to RTD
// Error: ~0.4°C per ohm of lead resistance
// Example: 1Ω lead × 2 wires = 2Ω error = 5°C at 100°C!

// 3-wire: Compensates one lead
// Assumes balanced lead resistance
// Error: <0.1°C if leads matched
enum max31865_wire_mode wire_mode = MAX31865_3WIRE;

// 4-wire: Complete compensation
// Eliminates all lead resistance
// Error: 0°C from lead resistance
enum max31865_wire_mode wire_mode = MAX31865_4WIRE;
```

**Choosing wire mode**:
- **4-wire**: Lab equipment, precision measurement
- **3-wire**: Industrial standard, balanced trade-off
- **2-wire**: Only for very short leads (<1m)

### Excitation Current Effects

RTD self-heating from excitation current.

```c
// Higher current = more heating
// PT100: ~1mW/mA² self-heating
// Heating depends on thermal coupling

// LTC2983 excitation current options
enum ltc2983_rtd_current {
    LTC2983_RTD_CURRENT_5UA   = 0,  // Minimal heating
    LTC2983_RTD_CURRENT_10UA  = 1,
    LTC2983_RTD_CURRENT_25UA  = 2,
    LTC2983_RTD_CURRENT_50UA  = 3,
    LTC2983_RTD_CURRENT_100UA = 4,
    LTC2983_RTD_CURRENT_250UA = 5,
    LTC2983_RTD_CURRENT_500UA = 6,  // Good SNR, moderate heating
    LTC2983_RTD_CURRENT_1MA   = 7,  // High heating risk
};

// For air measurement: use lower current (50-100µA)
// For liquid measurement: can use higher current (500µA-1mA)
```

## Thermocouple Calibration

### Cold Junction Compensation

Critical for thermocouple accuracy.

```c
// MAX31855 has integrated CJ compensation
// Accuracy depends on CJ sensor placement

// Best practices:
// 1. Good thermal contact between CJ sensor and terminal
// 2. No air gaps
// 3. Shield from drafts
// 4. Thermal mass for stability

// Verify CJ temperature is reasonable
float cj_temp;
max31855_read_internal_temp(dev, &cj_temp);

if (cj_temp < -40 || cj_temp > 85) {
    pr_warn("CJ temperature out of range: %.1f C\n", cj_temp);
    pr_warn("Check: thermal contact, airflow, ambient\n");
}
```

### Thermocouple Type Accuracy

Different thermocouple types have different accuracy specs.

| Type | Range | Accuracy (Standard) | Common Use |
|------|-------|---------------------|------------|
| K | -200 to 1350°C | ±2.2°C or 0.75% | General purpose |
| J | -210 to 1200°C | ±2.2°C or 0.75% | Reducing environments |
| T | -250 to 400°C | ±1.0°C or 0.75% | Low temperature |
| E | -200 to 1000°C | ±1.7°C or 0.5% | High output |
| N | -200 to 1300°C | ±2.2°C or 0.75% | High stability |
| R/S | -50 to 1750°C | ±1.5°C or 0.25% | High temp, expensive |

```c
// Select appropriate type for application
struct ltc2983_sensor tc_sensor = {
    .type = LTC2983_SENSOR_TYPE_THERMOCOUPLE_K,  // Type K
    // For high accuracy at low temp, use Type T
    // For high temp, use Type N or R/S
};
```

## Accuracy Considerations

### Digital Sensor Accuracy

Typical specifications and factors affecting accuracy.

```c
// ADT7420 specifications:
// - Accuracy: ±0.25°C (-40 to +105°C)
// - Resolution: 0.0078°C (16-bit)
// - Resolution ≠ Accuracy!

// Factors affecting accuracy:
// 1. Self-heating: ~0.1°C in still air
// 2. Thermal time constant: 30 seconds typical
// 3. Calibration drift: minimal (<0.01°C/year)
// 4. Supply voltage: minimal effect
```

**Improving accuracy**:
- Allow thermal settling time
- Avoid heat-generating components nearby
- Use thermal paste for good contact
- One-point calibration at operating temp

### RTD Accuracy Budget

Understanding total system accuracy.

```c
// Total error sources:
// 1. RTD sensor: ±0.15°C (Class A PT100)
// 2. Reference resistor: ±0.04°C (0.1%, 4kΩ)
// 3. Lead resistance: ±0.05°C (3-wire compensation)
// 4. MAX31865 ADC: ±0.5°C typical
// 5. Linearization: ±0.05°C
// 
// RSS total: √(0.15² + 0.04² + 0.05² + 0.5² + 0.05²) = ±0.53°C

// To improve:
// - Use Class AA RTD: ±0.10°C → total ±0.52°C
// - Use 4-wire: lead error → 0°C → total ±0.51°C
// - Calibrate Rref: ±0.02°C → total ±0.51°C
// - Two-point cal: -0.3°C offset → total ±0.40°C
```

### Thermocouple Accuracy Budget

```c
// Total error sources:
// 1. Thermocouple wire: ±2.2°C (Type K standard)
// 2. Cold junction sensor: ±1.0°C (MAX31855 internal)
// 3. CJ thermal gradient: ±0.5°C (poor coupling)
// 4. ADC: ±0.25°C
// 5. Linearization: ±0.15°C
//
// Total: ~±4°C worst case!

// To improve:
// - Use special limits wire: ±1.1°C
// - External precision CJ sensor: ±0.25°C
// - Isothermal block for CJ: ±0.1°C
// - Better ADC (24-bit): ±0.1°C
// → Improved total: ±1.6°C
```

## Calibration Procedures

### Ice Bath Calibration (0°C Reference)

Most accessible accurate reference.

```
Equipment:
- Insulated container
- Crushed ice
- Distilled water
- Stirrer

Procedure:
1. Fill container with crushed ice
2. Add distilled water to just cover ice
3. Stir thoroughly
4. Insert sensor, ensure full immersion
5. Wait 2-5 minutes for equilibrium
6. Record reading
7. Expected: 0.0°C ±0.1°C

Notes:
- Use crushed ice, not cubes (better contact)
- Must have ice+water, not just ice
- Stir continuously
- Distilled water prevents contamination
```

```c
// Ice bath calibration
float ice_reading;
ret = sensor_read_temp(dev, &ice_reading);

float offset = 0.0 - ice_reading;
pr_info("Ice bath offset: %.3f C\n", offset);

// Store in non-volatile memory
eeprom_write_float(CAL_OFFSET_ADDR, offset);
```

### Boiling Water Calibration (100°C Reference)

Pressure-dependent reference point.

```
Equipment:
- Clean water
- Heat source
- Barometer (for pressure compensation)

Procedure:
1. Boil water vigorously
2. Measure atmospheric pressure
3. Calculate boiling point from pressure
4. Insert sensor in steam or water
5. Wait for stable reading
6. Record temperature

Pressure compensation:
- Sea level (1013 mbar): 100.0°C
- 2000m altitude (795 mbar): 93.0°C
- Formula: Tboil = 100 + (P - 1013) × 0.0367
```

```c
// Boiling point from pressure
float calculate_boiling_point(float pressure_mbar)
{
    // Approximate formula
    return 100.0 + (pressure_mbar - 1013.25) * 0.0367;
}

float pressure = read_barometer();  // e.g., 1013.25 mbar
float expected_boiling = calculate_boiling_point(pressure);

float boil_reading;
ret = sensor_read_temp(dev, &boil_reading);

float gain = expected_boiling / boil_reading;
```

### Dry Block Calibrator (Industrial)

Professional calibration equipment.

```
Advantages:
- Precise temperature control
- Multiple reference points
- Wide temperature range
- Fast stabilization
- Excellent uniformity

Procedure:
1. Set block to desired temperature
2. Wait for stabilization (5-10 min)
3. Insert reference probe + DUT
4. Wait for equilibrium (2-5 min)
5. Record both readings
6. Repeat at multiple temperatures
7. Generate calibration table
```

```c
// Multi-point calibration from dry block
float calibration_points[][2] = {
    // [reference, measured]
    { -40.0, -39.8 },
    {   0.0,   0.3 },
    {  25.0,  25.2 },
    {  50.0,  49.9 },
    { 100.0, 100.4 },
    { 150.0, 149.7 },
};

// Store in EEPROM for runtime correction
store_calibration_table(calibration_points, 6);
```

## Best Practices

1. **Calibration Environment**
   - Same conditions as operating environment
   - Allow thermal equilibrium (5-10 minutes)
   - Minimize drafts and heat sources
   - Good thermal contact with reference

2. **Reference Equipment**
   - Traceable calibration certificate
   - Higher accuracy than DUT (10:1 rule)
   - Regular recalibration schedule
   - Proper handling and storage

3. **Documentation**
   - Record all calibration data
   - Environmental conditions
   - Equipment serial numbers
   - Date and operator
   - Store calibration constants securely

4. **Validation**
   - Verify after calibration
   - Check at multiple points
   - Compare to independent reference
   - Regular recalibration (annually)

5. **Software Implementation**
   - Store calibration in non-volatile memory
   - Apply corrections in firmware
   - Validate calibration data on boot
   - Provide calibration mode/UI
   - Log calibration events
