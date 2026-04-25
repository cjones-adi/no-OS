# Hardware Debugging Tools

Complete guide to using logic analyzers, oscilloscopes, and other hardware tools for debugging no-OS embedded systems.

---

## Logic Analyzers

Logic analyzers capture and display digital signals, essential for debugging communication protocols.

### When to Use a Logic Analyzer

- Verify SPI/I2C/UART signal integrity
- Check clock frequencies
- Verify chip select timing
- Analyze protocol transactions
- Debug timing issues
- Confirm pin assignments are correct

---

### What to Check with Logic Analyzer

**SPI Signals**:
- Clock (SCLK) - Is it present? Correct frequency?
- MOSI - Data from master to device
- MISO - Data from device to master
- CS (Chip Select) - Active during transaction? Correct polarity?

**I2C Signals**:
- SCL (Clock) - Is it present? Correct frequency?
- SDA (Data) - Toggling during transaction?
- Start/Stop conditions - Properly formed?
- ACK/NACK - Device responding?

**UART Signals**:
- TX - Data transmitting?
- RX - Data receiving?
- Baud rate - Matches configuration?
- Start/stop bits - Correct format?

---

### Common Issues Found with Logic Analyzer

**No Clock Signal**:
```
Problem: SCLK or SCL line stays low/high
Causes:
- SPI/I2C peripheral not initialized
- Wrong GPIO pin configuration
- Pin not configured as alternate function
- Clock not enabled
```

**Chip Select Not Asserted**:
```
Problem: CS stays high during SPI transaction
Causes:
- CS pin not configured
- Wrong CS pin number
- CS polarity inverted (should be active-low)
```

**Wrong Clock Frequency**:
```
Problem: Clock frequency doesn't match configured value
Causes:
- Platform prescaler incorrect
- System clock misconfigured
- max_speed_hz parameter wrong
```

**No ACK on I2C**:
```
Problem: No ACK bit after address byte
Causes:
- Wrong I2C address (7-bit vs 8-bit)
- Device not powered
- Pull-up resistors missing/incorrect value
- Device in reset or sleep mode
```

**MOSI/MISO Lines Stuck**:
```
Problem: Data lines don't toggle
Causes:
- MOSI/MISO pins swapped
- Wrong GPIO pins configured
- Pin not in SPI mode (still GPIO)
- Short circuit or connection issue
```

---

### Decoding Protocols

Modern logic analyzers can decode protocols automatically:

**SPI Decoder Settings**:
- CPOL: 0 or 1 (clock polarity)
- CPHA: 0 or 1 (clock phase)
- Bit order: MSB-first or LSB-first
- Bits per transfer: 8, 16, etc.

**I2C Decoder Settings**:
- Address format: 7-bit or 10-bit
- Speed: Standard (100kHz), Fast (400kHz), etc.

**UART Decoder Settings**:
- Baud rate: 9600, 115200, etc.
- Data bits: 7, 8, 9
- Parity: None, Even, Odd
- Stop bits: 1, 1.5, 2

---

## Oscilloscopes

Oscilloscopes measure analog signal characteristics and timing.

### When to Use an Oscilloscope

- Verify power supply voltage levels
- Check signal rise/fall times
- Measure clock jitter
- Verify analog sensor outputs
- Debug power supply noise
- Check signal integrity at high speeds

---

### What to Check with Oscilloscope

**Power Supply**:
- Voltage level correct (3.3V, 5V, etc.)
- Clean DC level (no ripple/noise)
- Stable under load
- No voltage drops during operation

**Clock Signals**:
- Frequency correct
- Rise/fall times adequate
- Amplitude correct (0V to VDD)
- No overshoot/undershoot
- Low jitter

**Digital Signals**:
- Logic levels correct (0V = low, VDD = high)
- Clean transitions (no ringing)
- Setup/hold times met
- No cross-talk between signals

**Analog Signals**:
- Voltage range correct
- Clean signal (low noise)
- Correct DC offset
- Expected frequency/shape

---

### Common Issues Found with Oscilloscope

**Power Supply Issues**:
```
Problem: Voltage sags during operation
Causes:
- Insufficient current capability
- Long/thin power wires (voltage drop)
- Missing decoupling capacitors
- Brownout during high current draw
```

**Noisy Signals**:
```
Problem: Clock or data lines show noise
Causes:
- Ground loop
- Missing decoupling capacitors
- Cross-talk from adjacent signals
- EMI from switching power supplies
```

**Wrong Logic Levels**:
```
Problem: Signal doesn't reach full VDD
Causes:
- Wrong pull-up resistor value
- Output drive strength too weak
- Loading too high (too many devices on bus)
- Voltage level mismatch (3.3V vs 5V)
```

---

## Multimeter

Essential for basic electrical measurements.

### What to Measure

**Continuity**:
- Verify connections between pins
- Check for shorts to ground/VDD
- Confirm cable/wire integrity

**Voltage**:
- Power supply rails (3.3V, 5V, etc.)
- GPIO pin states (high/low)
- Analog sensor outputs

**Resistance**:
- Pull-up/pull-down resistor values
- Check for shorts (0Ω) or opens (∞Ω)
- Verify I2C pull-ups (typically 2.2kΩ - 10kΩ)

---

### Common Checks

**Power Supply**:
```
Check VDD pin: Should read 3.3V or 5V (nominal)
Check GND pin: Should read 0V
Check between VDD and GND: Should be stable
```

**I2C Pull-ups**:
```
Measure SDA to VDD: ~2.2kΩ - 10kΩ (pull-up present)
Measure SCL to VDD: ~2.2kΩ - 10kΩ (pull-up present)
If missing: Add pull-up resistors
```

**SPI Chip Select**:
```
Measure CS when idle: Should be VDD (active-low CS)
Measure CS during transaction: Should be 0V
```

**GPIO Configuration**:
```
Set GPIO high: Should measure VDD
Set GPIO low: Should measure 0V
If wrong: GPIO not configured or pin muxing incorrect
```

---

## LED Debugging

Simple but effective when UART and JTAG are unavailable.

### LED Blink Patterns

**Initialization Checkpoint**:
```c
// Blink LED to indicate progress
void led_checkpoint(int checkpoint)
{
    for (int i = 0; i < checkpoint; i++) {
        led_on();
        no_os_mdelay(200);
        led_off();
        no_os_mdelay(200);
    }
    no_os_mdelay(1000);
}

int example_main(void)
{
    led_checkpoint(1);  // 1 blink - starting
    ret = uart_init();
    
    led_checkpoint(2);  // 2 blinks - UART done
    ret = spi_init();
    
    led_checkpoint(3);  // 3 blinks - SPI done
    ret = device_init();
    
    led_checkpoint(4);  // 4 blinks - all done
}
```

**Error Indication**:
```c
// Rapid blinking = error
void indicate_error(int error_code)
{
    while (1) {
        for (int i = 0; i < error_code; i++) {
            led_on();
            no_os_mdelay(100);
            led_off();
            no_os_mdelay(100);
        }
        no_os_mdelay(2000);
    }
}

int example_main(void)
{
    ret = critical_init();
    if (ret) {
        indicate_error(abs(ret));  // Blink error code
    }
}
```

**Status Indication**:
```c
led_on();   // Operation in progress
ret = long_operation();
led_off();  // Operation complete

if (ret) {
    // Rapid blink = error
    while(1) {
        led_toggle();
        no_os_mdelay(100);
    }
}
```

---

## Signal Generators

Use signal generators to provide test inputs to devices.

### Use Cases

**Function Generator**:
- Generate clock signals for testing
- Provide PWM signals
- Create test waveforms for ADCs
- Simulate sensor outputs

**Arbitrary Waveform Generator**:
- Generate complex test patterns
- Simulate communication protocols
- Create specific test scenarios

---

## I2C/SPI Bus Analyzers

Dedicated protocol analyzers for I2C/SPI.

### Features

- Real-time protocol decoding
- Trigger on specific transactions
- Capture long sequences
- Error detection (NACK, parity, etc.)
- Timing analysis
- Protocol violations

### Popular Tools

- Saleae Logic Analyzers
- Digilent Analog Discovery
- Total Phase Beagle I2C/SPI analyzers
- DSLogic series

---

## In-Circuit Debuggers (ICD)

Hardware debuggers for JTAG/SWD debugging.

### Common Debuggers

**ST-Link** (STM32):
- SWD interface
- Flash programming
- Breakpoint debugging
- Low cost (~$20)

**J-Link** (Segger):
- JTAG/SWD interface
- High performance
- Wide device support
- Professional features

**CMSIS-DAP**:
- Open standard
- USB debugging
- SWD interface
- Many implementations

**PICkit/ICD** (Microchip):
- For PIC/AVR devices
- Programming and debugging
- Low cost

---

## Protocol Sniffers

Passive monitoring of communication buses.

### I2C Sniffer

Monitor I2C bus without interfering:
```
Connections:
- SCL → Sniffer clock input
- SDA → Sniffer data input
- GND → Common ground

View all transactions on bus
Decode addresses, data, ACK/NACK
Trigger on specific address
```

### SPI Sniffer

Monitor SPI bus:
```
Connections:
- SCLK → Sniffer clock
- MOSI → Sniffer data in
- MISO → Sniffer data out
- CS → Sniffer chip select (if needed)

Decode based on CPOL/CPHA
View all transactions
```

---

## Power Supply Debug Tools

### Current Measurement

**Inline ammeter**:
- Measure device current consumption
- Identify power issues
- Check for unexpected current draw
- Verify sleep mode current

**Power supply with current limit**:
- Set current limit to safe value
- Detect shorts (current limit trips)
- Monitor current during operation

### Power Analysis

**Expected currents**:
```
Active mode: 10-100 mA typical
Sleep mode: μA to mA range
Startup surge: Can be higher briefly
```

**High current issues**:
```
Causes:
- Short circuit (VDD to GND)
- Device continuously transmitting
- Multiple peripherals active
- Missing sleep mode entry
```

**Low/zero current**:
```
Causes:
- Device not powered
- Voltage regulator disabled
- Device in shutdown mode
- Connection issue
```

---

## Thermal Debugging

Use temperature to identify issues.

### Thermal Camera

- Identify hot spots on PCB
- Find shorted components
- Verify heat dissipation
- Check thermal management

### Temperature Measurement

**Thermocouple or IR thermometer**:
- Measure chip temperature
- Verify within safe limits
- Check for thermal shutdown
- Identify failing components

**Common Issues**:
```
Chip too hot (>85°C typical max):
- Short circuit
- Wrong voltage (overvoltage)
- Excessive current
- Poor heat dissipation

Chip cold (room temp):
- Not powered
- Not operating
- In shutdown mode
```

---

## Documentation and Datasheets

Essential "tools" for debugging.

### What to Check in Datasheet

**Electrical Characteristics**:
- Supply voltage range
- Logic levels (VIH, VIL)
- Current consumption
- Maximum ratings

**Timing Requirements**:
- Setup time, hold time
- Clock frequency limits
- Power-up sequence timing
- Communication timing diagrams

**Pin Descriptions**:
- Pin functions and alternate functions
- Internal pull-ups/pull-downs
- Pin muxing options
- Default states

**Register Maps**:
- Register addresses
- Bit definitions
- Reset values
- Read/write permissions

**Application Notes**:
- Reference designs
- Layout guidelines
- Known issues and errata
- Design recommendations

---

## Systematic Hardware Debug Approach

### Step 1: Power Supply

1. Verify voltage at device VDD pin (correct level)
2. Check current consumption (reasonable)
3. Measure voltage stability under load
4. Check all decoupling capacitors present

### Step 2: Clock Signals

1. Verify system clock present
2. Check peripheral clocks enabled
3. Measure frequency accuracy
4. Check for jitter or noise

### Step 3: Communication Bus

1. Verify clock signal present
2. Check data signals toggle
3. Confirm chip select/enable signals
4. Decode protocol with analyzer

### Step 4: Signal Integrity

1. Check logic levels (0V and VDD)
2. Verify clean transitions
3. Check for cross-talk
4. Measure rise/fall times

### Step 5: Device Response

1. Verify device ID read correctly
2. Check register write/readback
3. Confirm expected behavior
4. Verify interrupt signals (if used)
