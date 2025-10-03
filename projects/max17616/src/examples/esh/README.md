# MAX17616 ESH (Embedded Shell) Example

This example integrates the embedded shell library (esh) with the MAX17616 power management IC driver, providing an interactive command-line interface for device configuration and monitoring.

## Available Commands

### Device Information
- `telemetry` - Read and display all device telemetry (VIN, VOUT, IOUT, Temperature, Power)
- `faults` - Display detailed fault status information
- `settings` - Display all current device settings
- `clear` - Clear all device faults

### Configuration Commands
- `clmode [mode]` - Get/set current limit mode
  - 0: Latch-off
  - 1: Continuous
  - 2: Auto-retry

- `istart [ratio]` - Get/set current start ratio
  - 0: Full (I_limit)
  - 1: Half (I_limit/2)
  - 2: Quarter (I_limit/4)
  - 3: Eighth (I_limit/8)
  - 4: Sixteenth (I_limit/16)

- `timeout [value]` - Get/set overcurrent timeout
  - 0: 400 microseconds
  - 1: 1 millisecond
  - 2: 4 milliseconds
  - 3: 24 milliseconds

- `operation [state]` - Get/set operation state
  - 0: Disable
  - 1: Enable

### Usage Examples

```
max17616> telemetry
=== MAX17616 Telemetry ===
VIN:         12 V
VOUT:        5 V
IOUT:        2 A
Temperature: 45 °C
Power:       10 W

max17616> clmode 1
Current limit mode set successfully

max17616> settings
=== Device Settings ===
Current Limit Mode: Continuous (0x01)
Current Start Ratio: Half (I_limit/2) (0x01)
...
```

## Building

Set `ESH_EXAMPLE = y` in the project Makefile to build this example.

## Features

- Interactive command-line interface
- Real-time telemetry monitoring
- Configuration parameter adjustment
- Fault status monitoring and clearing
- Command help system (type `help`)

## Hardware Requirements

- MAX17616 evaluation board
- UART connection for terminal interface
