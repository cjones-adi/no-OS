# Skills for Driver Development

This directory contains skills that extend agent capabilities with specialized knowledge for embedded driver development. Skills are self-contained folders with a `SKILL.md` file and optional bundled assets.

## Path Configuration

**AUTO-DETECTION**: When agents see `{WORKSPACE}` in documentation, they automatically detect which path to use:
- Checks if `.github/agents/` exists → uses `.github`
- Otherwise checks if `.claude/agents/` exists → uses `.claude`
- Falls back to `.github` if neither exists

All references to `{WORKSPACE}/skills/`, `{WORKSPACE}/skill-usage-logs/`, etc. are automatically resolved at runtime by the agents.

**For humans reading this**: Replace `{WORKSPACE}` mentally with whichever folder you're using (`.github` or `.claude`).

## What Are Skills?

Skills are modular packages that provide:
- **YAML frontmatter** with `name` and `description` for agent discovery
- **Detailed instructions** for specific workflows and tasks
- **Bundled assets** like reference docs, templates, and scripts
- **Slash-command invocation** via `/skill-name` in Copilot Chat

Skills follow the [Agent Skills specification](https://agentskills.io/specification).

## Skill Usage Tracking

To verify that skills are being actively used by agents, a usage tracking system is in place:

**Location**: [{WORKSPACE}/skill-usage-logs/archive/](../skill-usage-logs/)

When agents reference or consult skills during their workflows, they create usage logs documenting:
- Which skill provided guidance
- Why the skill was needed
- What information was extracted
- How it was applied to the task
- Outcome and results achieved

**Example**: When the unit tester agent uses `/no-os-unit-testing` to create tests, it logs the specific testing framework, mocking, or coverage information used and the tests created.

This provides:
- ✅ **Verification** that skill refactoring is valuable
- ✅ **Tracking** of which skills are most useful
- ✅ **Learning** from real-world application patterns
- ✅ **Improvement opportunities** based on actual usage

See [skill-usage-logs/README.md](../skill-usage-logs/README.md) for details and [EXAMPLE-skill-usage-log.md](../skill-usage-logs/EXAMPLE-skill-usage-log.md) for a sample log.

## Available Skills

| Skill | Description | Bundled Assets |
|-------|-------------|----------------|
| [no-os-iio](no-os-iio/SKILL.md) | Comprehensive guide to no-OS IIO (Industrial I/O) framework for analog and digital sensors | None |
| [no-os-make-and-linker](no-os-make-and-linker/SKILL.md) | Complete guide to Make build system and linker for ADI no-OS embedded projects | None |
| [no-os-spi](no-os-spi/SKILL.md) | Complete guide to no-OS SPI platform drivers for embedded systems and porting to new platforms | None |
| [no-os-i2c](no-os-i2c/SKILL.md) | Complete guide to no-OS I2C platform drivers for embedded systems and porting to new platforms | None |
| [no-os-gpio](no-os-gpio/SKILL.md) | Complete guide to no-OS GPIO platform drivers for digital I/O control and configuration | None |
| [no-os-irq](no-os-irq/SKILL.md) | Complete guide to no-OS IRQ platform drivers for interrupt handling and callbacks | None |
| [no-os-adc](no-os-adc/SKILL.md) | Complete guide to no-OS ADC drivers for data acquisition (SAR/Sigma-Delta ADCs, channel configuration, reference/gain settings, conversion modes, calibration, IIO integration) | None |
| [no-os-dac](no-os-dac/SKILL.md) | Complete guide to no-OS DAC drivers for signal generation (voltage/current output, LDAC synchronization, slew rate control, offset/gain calibration, daisy-chain, IIO integration) | None |
| [no-os-unit-testing](no-os-unit-testing/SKILL.md) | Comprehensive guide to unit testing with Ceedling, Unity, CMock, and gcov - covers test framework, mocking strategies, and coverage-driven development | None |
| [no-os-project-structure](no-os-project-structure/SKILL.md) | Complete guide to creating and organizing no-OS projects (project layout, build system, multi-platform support, examples organization) | None |
| [no-os-debugging](no-os-debugging/SKILL.md) | Complete guide to debugging no-OS embedded applications (logging, error codes, UART console, JTAG/SWD, troubleshooting initialization and communication issues) | None |
| [testing-strategies](testing-strategies/SKILL.md) | Cross-platform testing strategies for embedded driver development (unit/integration/HIL testing, coverage goals, test planning, no-OS/Linux/Zephyr testing workflows) | None |
| [no-os-imu](no-os-imu/SKILL.md) | Complete guide to no-OS IMU, accelerometer, and gyroscope drivers (3-axis motion sensing, FIFO data acquisition, motion detection features, calibration, burst read operations for synchronized sensor data) | None |
| [no-os-power](no-os-power/SKILL.md) | Complete guide to no-OS power management drivers including PMICs, regulators, battery chargers, and power monitors (buck/boost/LDO topologies, DVS, sequencing, PMBus protocol, battery charging CC-CV, power monitoring) | None |
| [no-os-temperature](no-os-temperature/SKILL.md) | Complete guide to no-OS temperature sensor drivers (digital sensors, RTD/thermocouple converters, multi-sensor hubs, temperature measurement modes, calibration, alert/threshold configuration) | None |
| [no-os-frequency](no-os-frequency/SKILL.md) | Complete guide to no-OS frequency synthesis and clock generation drivers (fractional-N PLLs, integer-N PLLs, VCOs, clock distributors, dividers, phase control, lock detection, SYSREF generation, multi-output synchronization) | None |
| [no-os-maxim-platform](no-os-maxim-platform/SKILL.md) | Complete guide to Maxim (MAX32xxx, MAX78xxx) platform drivers (platform initialization, SPI/I2C/UART/GPIO, DMA, clock management, pin multiplexing, VDDIO voltage selection, interrupt handling) | None |
| [no-os-stm32-platform](no-os-stm32-platform/SKILL.md) | Complete guide to STM32 platform drivers (HAL library integration, SPI/I2C/UART/GPIO/Timer, DMA, RCC clock management, GPIO alternate functions, NVIC interrupt handling, family-specific patterns) | None |
| [datasheet-parsing](datasheet-parsing/SKILL.md) | Comprehensive guide to extracting ALL datasheet information with pdfplumber (features, specs, timing, registers) plus tracking checklist for planners | None |
| [zephyr-build-system](zephyr-build-system/SKILL.md) | Complete guide to Zephyr build system including west commands, CMake integration, Kconfig, prj.conf, board overlays, virtual environment setup, and build troubleshooting | None |
| [zephyr-regulator](zephyr-regulator/SKILL.md) | Complete guide to Zephyr regulator drivers for PMICs and power management ICs (buck, LDO, boost, DVS, modes) | None |
| [zephyr-sensor](zephyr-sensor/SKILL.md) | Complete guide to Zephyr sensor drivers for measurement devices (temperature, accelerometer, gyroscope, pressure, humidity, light sensors) with ADI reference examples | None |
| [zephyr-adc](zephyr-adc/SKILL.md) | Complete guide to Zephyr ADC drivers for analog-to-digital converters (channel configuration, gain/reference settings, synchronous/asynchronous reads, value conversion, calibration) | None |
| [zephyr-dac](zephyr-dac/SKILL.md) | Complete guide to Zephyr DAC drivers for digital-to-analog converters (channel configuration, resolution, analog output generation, waveform synthesis, buffered/unbuffered modes) | None |
| [zephyr-mfd](zephyr-mfd/SKILL.md) | Complete guide to Zephyr MFD (Multi-Function Device) drivers for complex chips with multiple subsystems (parent-child architecture, bus abstraction, DAC+ADC+GPIO integration, PMIC drivers) | None |
| [zephyr-gpio](zephyr-gpio/SKILL.md) | Complete guide to Zephyr GPIO drivers for controllers and expanders (pin configuration, digital I/O, interrupts, pull resistors, I2C/SPI expanders, port operations) | None |
| [zephyr-i2c](zephyr-i2c/SKILL.md) | Complete guide to Zephyr I2C controller drivers for serial communication (speed configuration 100kHz-5MHz, 7-bit/10-bit addressing, multi-master support, bus recovery, target mode, transfer operations) | None |
| [zephyr-spi](zephyr-spi/SKILL.md) | Complete guide to Zephyr SPI controller drivers for synchronous serial communication (clock modes CPOL/CPHA, chip select GPIO/hardware, full/half duplex, scatter-gather buffers, multi-slave buses, master/slave modes) | None |
| [zephyr-uart](zephyr-uart/SKILL.md) | Complete guide to Zephyr UART drivers for serial communication (baud rate configuration, parity/stop/data bits, polling/interrupt/async modes, flow control RTS/CTS/DTR/DSR, RS-485 support, error handling) | None |
| [zephyr-unit-testing](zephyr-unit-testing/SKILL.md) | Comprehensive guide to unit testing Zephyr drivers using Ztest framework and Twister test runner (test structure, assertions, emulation/fake drivers, devicetree overlays, test fixtures, hardware-in-loop testing, testcase.yaml configuration) | None |
| [zephyr-devicetree](zephyr-devicetree/SKILL.md) | Complete guide to creating Zephyr devicetree bindings (YAML files that define hardware device interfaces, property types, bus-specific bindings I2C/SPI, controller bindings GPIO/ADC/DAC, parent-child hierarchies for MFDs, debugging devicetree issues) | None |
| [zephyr-pwm](zephyr-pwm/SKILL.md) | Complete guide to Zephyr PWM drivers for generating PWM signals (period/duty cycle configuration, motor control, LED dimming, PWM capture, event handling, polarity control) | None |
| [zephyr-led](zephyr-led/SKILL.md) | Complete guide to Zephyr LED controller drivers (on/off control, brightness 0-100%, blinking patterns, RGB/multicolor LEDs, I2C/SPI LED chips, PWM dimming) | None |
| [zephyr-charger](zephyr-charger/SKILL.md) | Complete guide to Zephyr battery charger drivers (CC-CV charging, current/voltage regulation, charging status monitoring, health detection, input power detection, PMIC chargers) | None |
| [zephyr-fuel-gauge](zephyr-fuel-gauge/SKILL.md) | Complete guide to Zephyr fuel gauge drivers (SOC measurement, voltage/current monitoring, capacity tracking, runtime estimation, SBS protocol, coulomb counting) | None |

## How to Use Skills

### Invoke by Slash Command

In GitHub Copilot Chat:
```
/no-os-iio
/no-os-make-and-linker
/no-os-spi
/no-os-i2c
/no-os-gpio
/no-os-irq
/no-os-adc
/no-os-dac
/no-os-unit-testing
/no-os-project-structure
/no-os-debugging
/testing-strategies
/no-os-imu
/no-os-power
/no-os-temperature
/no-os-frequency
/no-os-maxim-platform
/no-os-stm32-platform
/zephyr-build-system
/zephyr-regulator
/zephyr-sensor
/zephyr-adc
/zephyr-dac
/zephyr-mfd
/zephyr-gpio
/zephyr-i2c
/zephyr-spi
/zephyr-uart
/zephyr-unit-testing
/zephyr-devicetree
/zephyr-pwm
/zephyr-led
/zephyr-charger
/zephyr-fuel-gauge
```

### Invoke by Natural Language

Agents automatically discover skills based on context:
```
How do I add a new driver to src.mk?
How do I implement IIO channels for my ADC?
How do I port SPI drivers to a new platform?
How do I implement I2C read/write operations?
How do I configure GPIO pins as inputs or outputs?
How do I register interrupt callbacks?
How do I implement ADC drivers for no-OS?
How do I configure ADC channels and setups?
How do I set reference voltage and gain for ADCs?
How do I perform ADC calibration?
How do I integrate ADC drivers with IIO?
How do I implement DAC drivers for no-OS?
How do I configure DAC voltage and current output ranges?
How do I use LDAC for synchronized multi-channel DAC updates?
How do I configure DAC slew rate control?
How do I perform DAC offset and gain calibration?
How do I write unit tests with Ceedling?
How do I mock I2C functions for testing?
How do I create a new no-OS project?
How do I organize project files for multi-platform support?
How do I add examples to an existing project?
How do I debug initialization failures in no-OS?
How do I troubleshoot SPI communication errors?
How do I use UART console debugging?
How do I plan testing strategies for drivers?
How do I set up unit, integration, and HIL testing?
How do I achieve 80% test coverage?
How do I implement IMU drivers for no-OS?
How do I configure accelerometer and gyroscope sensors?
How do I implement motion detection (tap, free-fall, activity)?
How do I use FIFO data acquisition for IMU sensors?
How do I implement PMIC and regulator drivers?
How do I configure battery chargers (CC-CV charging)?
How do I implement PMBus protocol for power management?
How do I configure DVS (Dynamic Voltage Scaling)?
How do I implement temperature sensor drivers?
How do I work with RTD and thermocouple converters?
How do I configure temperature thresholds and alerts?
How do I implement fractional-N PLL drivers?
How do I configure clock distribution and multi-output systems?
How do I implement SYSREF generation for JESD204B?
How do I configure phase control and synchronization?
How do I configure Maxim platform drivers?
How do I use MXC_GPIO_Config for pin multiplexing?
How do I configure VDDIO voltage selection on Maxim?
How do I implement DMA on Maxim MAX32xxx?
How do I configure STM32 platform drivers?
How do I use STM32 HAL with no-OS?
How do I configure GPIO alternate functions on STM32?
How do I configure RCC clocks on STM32?
How do I implement DMA on STM32?
How do I build Zephyr applications with west?
How do I create board overlays for Zephyr?
How do I configure Kconfig for my driver?
How do I implement sensor drivers for Zephyr?
How do I work with sensor channels and triggers?
How do I configure sensor interrupts?
How do I implement ADC drivers for Zephyr?
How do I configure ADC channels with gain and reference?
How do I convert raw ADC values to millivolts?
How do I implement DAC drivers for Zephyr?
How do I generate analog waveforms with DAC?
How do I configure DAC resolution and buffering?
How do I implement MFD parent drivers for multi-function chips?
How do I create child drivers for MFD devices?
How do I integrate DAC, ADC, and GPIO in one MFD chip?
How do I abstract I2C and SPI in MFD parent drivers?
How do I implement GPIO controller drivers?
How do I configure GPIO pins as inputs or outputs?
How do I handle GPIO interrupts in Zephyr?
How do I work with I2C or SPI GPIO expanders?
How do I implement I2C controller drivers for Zephyr?
How do I configure I2C bus speed (100kHz to 5MHz)?
How do I support 10-bit I2C addressing?
How do I implement I2C bus recovery?
How do I handle I2C NACK and timeout errors?
How do I implement I2C target (slave) mode?
How do I implement SPI controller drivers for Zephyr?
How do I configure SPI clock modes (CPOL/CPHA)?
How do I control SPI chip select with GPIO or hardware?
How do I implement scatter-gather SPI transfers?
How do I handle multi-slave SPI buses?
How do I debug SPI signal timing issues?
How do I implement UART drivers for Zephyr?
How do I configure UART baud rate and serial settings?
How do I implement interrupt-driven UART with FIFO?
How do I implement async UART with DMA?
How do I configure UART flow control (RTS/CTS)?
How do I handle UART errors (overrun, parity, framing)?
How do I fix Zephyr build errors?
How do I measure and improve test coverage?
How do I create devicetree bindings for new devices?
How do I define property types in devicetree bindings?
How do I configure bus-specific bindings for I2C or SPI?
How do I create controller bindings for GPIO, ADC, or DAC?
How do I implement parent-child devicetree hierarchies for MFD devices?
How do I debug devicetree validation errors?
How do I work with cell specifiers in devicetree?
How do I implement PWM drivers for motor control or LED dimming?
How do I configure PWM period and duty cycle?
How do I implement PWM input capture?
How do I control LED brightness and blinking?
How do I set RGB LED colors?
How do I implement battery charger drivers?
How do I configure charging current and voltage?
How do I monitor charging status and health?
How do I implement fuel gauge drivers?
How do I read battery state of charge (SOC)?
How do I estimate battery runtime?
```

Copilot will detect the context and reference the appropriate skill.

### Reference Explicitly

In conversations with agents:
```
@driver-coder-no-os Please reference the /no-os-make-and-linker skill to help me
set up the build system for the MAX77779 driver.

@driver-coder-no-os Use the /no-os-iio skill to help implement IIO support for
the AD7606 ADC with buffered acquisition.

@driver-coder-no-os Reference the /no-os-spi skill to show me how to implement
SPI transfers for my device.
```

## Skill Overview

### no-os-iio
Industrial I/O framework for sensors and data acquisition devices. Covers:
- Channel and attribute definitions
- Buffered data acquisition
- Remote device control with libiio
- Trigger handlers and streaming
- Integration with IIO Oscilloscope

### no-os-make-and-linker
Build system and linking for no-OS projects. Covers:
- Makefile structure and variables
- Adding drivers to src.mk
- Conditional compilation
- Linker scripts and memory layout
- Cross-platform builds
- Troubleshooting build errors

### no-os-spi
SPI platform driver abstraction layer. Covers:
- Platform driver architecture
- SPI initialization and configuration
- Transfer functions (simple, message-based, DMA)
- Multi-slave bus management
- Porting to new platforms
- Platform-specific extras

### no-os-i2c
I2C platform driver abstraction layer. Covers:
- Platform driver architecture
- I2C initialization and bus management
- Read/write operations and repeated start
- Multi-device bus with mutex locking
- Burst transfers
- Porting to new platforms

### no-os-gpio
GPIO platform driver for digital I/O control. Covers:
- GPIO initialization and configuration
- Direction control (input/output)
- Read/write digital values
- Pull-up/pull-down resistors
- Optional GPIO handling
- Common patterns (LEDs, buttons, chip select)

### no-os-irq
IRQ platform driver for interrupt handling. Covers:
- IRQ controller initialization
- Callback registration
- Trigger levels (edge/level sensitive)
- Priority configuration
- Global and specific IRQ enable/disable
- Porting to new platforms

### no-os-adc
ADC (Analog-to-Digital Converter) drivers for data acquisition devices. Covers:
- ADC types: SAR (fast, multi-channel), Sigma-Delta (precision), high-speed
- Driver architecture and standard API patterns
- Channel configuration (single-ended vs differential)
- Reference voltage and PGA gain selection
- Conversion modes (continuous, single, burst, triggered)
- Filtering and output data rate (sigma-delta)
- Calibration approaches (factory, system, self, digital correction)
- Data conversion (raw to voltage)
- IIO integration and buffer support
- Power management and clock configuration
- Reference drivers: AD4692, AD7124, AD7768-1, AD717x

### no-os-dac
DAC (Digital-to-Analog Converter) drivers for signal generation and control. Covers:
- DAC types: Simple, Standard multi-channel, Advanced programmable
- Driver architecture and update modes
- Voltage output ranges (unipolar, bipolar, asymmetric spans)
- Current output modes (0-20mA, 4-20mA industrial loops)
- Reference voltage selection (internal/external)
- Update mechanisms: Immediate (asynchronous), LDAC synchronous, Slew rate control
- Offset and gain calibration (factory, user, digital correction)
- Code to voltage/current conversion
- Multi-device daisy-chain configuration
- Advanced features: Dither, readback, temperature monitoring, CRC protection
- IIO integration and channel attributes
- Reference drivers: AD5766, AD5758, AD5686, AD3552R, AD5460

### no-os-unit-testing
Comprehensive unit testing guide covering Ceedling, Unity, CMock, and gcov in one skill. Includes:
- **Test Framework**: Ceedling project structure, Unity assertions, test fixtures (setUp/tearDown)
- **Mocking Strategy**: CMock mock generation, platform API mocking (I2C/SPI/GPIO), mock patterns (Expect/Ignore/Stub)
- # datasheet-parsing
Comprehensive datasheet parsing guide for extracting hardware specifications. Covers:
- Using pdfplumber for text and table extraction
- Parsing electrical specifications and timing parameters
- Extracting register maps and bit fields
- Handling multi-page datasheets
- Validation and quality checks
- Tracking checklist for planner agents

### zephyr-build-system
Complete Zephyr build system guide. Covers:
- West workspace setup and virtual environment activation
- CMake integration and CMakeLists.txt patterns
- Kconfig configuration (prj.conf, Kconfig files)
- Board-specific overlays and configurations
- Build commands (west build, flash, debug)
- Troubleshooting common build errors
- Incremental build workflow

### zephyr-regulator
Zephyr regulator driver development for PMICs. Covers:
- Regulator subsystem API and data structures
- Driver implementation (enable/disable, voltage/current control)
- DVS (Dynamic Voltage Scaling) support
- Operating modes and active discharge
- Devicetree bindings and Kconfig
- Reference drivers (MAX20335, MAX20370, PCA9420)

### zephyr-sensor
Zephyr sensor driver development for measurement devices. Covers:
- Sensor subsystem API (sample_fetch, channel_get, attr_set, trigger_set)
- Channel types (ACCEL, GYRO, TEMP, PRESS, HUMIDITY, LIGHT)
- Trigger modes (DATA_READY, THRESHOLD, MOTION, FIFO)
- Power management and FIFO buffering
- Multi-bus support (I2C/SPI abstraction)
- ADI reference drivers (ADXL345, ADT7420, MAX30210)

### zephyr-adc
Zephyr ADC driver development for analog-to-digital converters. Covers:
- ADC subsystem API (channel_setup, read, read_async)
- Channel configuration (gain, reference, acquisition time, differential mode)
- Synchronous and asynchronous sampling
- Value conversion (raw to millivolts/microvolts)
- Resolution and oversampling
- ADI reference drivers (AD4114, AD7124, AD4130)

### zephyr-dac
Zephyr DAC driver development for digital-to-analog converters. Covers:
- DAC subsystem API (channel_setup, write_value)
- Channel configuration (resolution, buffered/unbuffered, internal path)
- Writing analog output values and waveform generation
- Multi-channel DAC support and broadcast mode
- Voltage to digital value conversion
- ADI reference drivers (AD5601, AD5611, AD5621, AD559x)

### zephyr-mfd
Zephyr MFD (Multi-Function Device) driver development for complex chips with multiple subsystems. Covers:
- Parent-child driver architecture pattern
- Bus abstraction via transfer functions (I2C/SPI)
- Parent driver implementation (register access, reset, initialization)
- Child driver integration (DAC, ADC, GPIO, regulators)
- Devicetree parent-child relationships
- Thread-safe register access with locking
- ADI reference drivers (AD559x, MAX22017, ADP5585)

### zephyr-gpio
Zephyr GPIO driver development for General Purpose Input/Output controllers and expanders. Covers:
- GPIO driver API structure (pin_configure, port operations, interrupts)
- Pin configuration (input/output, pull-up/pull-down, open-drain)
- Digital I/O operations (read, write, toggle, port operations)
- Interrupt handling (edge/level triggers, callbacks)
- I2C/SPI GPIO expanders (shadow registers, locking, ISR context)
- Devicetree integration (gpio_dt_spec, active-low handling)
- ADI reference drivers (ADP5585, MAX22017, MAX14906)

### zephyr-i2c
Zephyr I2C controller driver development for Inter-Integrated Circuit bus. Covers:
- I2C controller driver API (configure, transfer, target_register)
- Speed mode configuration (Standard 100kHz, Fast 400kHz, Fast+ 1MHz, High-Speed 3.4MHz, Ultra 5MHz)
- 7-bit and 10-bit addressing modes
- Master mode transfers (write, read, combined transfers)
- Message structure and flags (READ, WRITE, STOP, RESTART)
- I2C target (slave) mode implementation and callbacks
- Multi-master bus arbitration handling
- Bus recovery mechanisms
- Error handling (NACK, timeout, arbitration loss)
- Clock stretching support
- Consumer API usage (i2c_dt_spec, i2c_write_dt, i2c_read_dt, i2c_write_read_dt)
- Reference drivers (nRF TWI, STM32, DesignWare, ESP32)

### zephyr-spi
Zephyr SPI controller driver development for Serial Peripheral Interface. Covers:
- SPI controller driver API (transceive, transceive_async, release)
- Clock mode configuration (CPOL/CPHA - 4 modes)
- Frequency configuration and baud rate calculation
- Chip select control (GPIO or hardware native)
- CS timing (setup delay, hold delay, inter-frame delay)
- Master (controller) and slave (peripheral) modes
- Full-duplex and half-duplex transfers
- Scatter-gather buffer management (spi_buf, spi_buf_set)
- Word size configuration (8-bit, 16-bit, custom)
- Transfer control (HOLD_ON_CS, LOCK_ON, CS polarity)
- Advanced modes (Dual/Quad/Octal SPI, loopback)
- Consumer API usage (spi_dt_spec, spi_transceive_dt, spi_write_dt, spi_read_dt)
- Reference drivers (nRF SPIM, STM32, DesignWare, NXP DSPI)

### zephyr-uart
Zephyr UART driver development for Universal Asynchronous Receiver-Transmitter. Covers:
- UART driver API structure (polling, interrupt-driven, async modes)
- Configuration (baud rate, parity, stop bits, data bits, flow control)
- Polling API (poll_in, poll_out - blocking character I/O)
- Interrupt-driven API (fifo_fill, fifo_read, IRQ callbacks, FIFO management)
- Async API (uart_tx, uart_rx_enable, event-driven DMA transfers)
- Event handling (TX_DONE, RX_RDY, RX_BUF_REQUEST, RX_DISABLED)
- Hardware flow control (RTS/CTS, DTR/DSR)
- RS-485 half-duplex support
- Error handling (overrun, parity, framing, break detection)

### zephyr-unit-testing
Comprehensive guide to unit testing Zephyr drivers using Ztest framework and Twister test runner. Covers:
- Ztest framework (ZTEST, ZTEST_SUITE macros, test organization)
- Assertion macros (zassert_*, zassume_*, zexpect_* for hard/soft assertions)
- Test fixtures (setup/before/after/teardown functions for resource management)
- Devicetree overlays for test hardware configuration
- Emulation drivers (I2C emul, SPI emul, GPIO fake) for testing without hardware
- Twister configuration (testcase.yaml, platform filters, tags, dependencies)
- CMakeLists.txt test build configuration
- Common testing patterns (init tests, register R/W, error handling, interrupts, async ops)
- Hardware-in-loop testing vs emulation strategies
- Running tests with west twister (platform selection, coverage, filtering)
- Debugging tests (verbose output, single test execution)
- Complete example test suites with real-world patterns
- Line control (baud rate, DTR, RTS, DCD, DSR)
- Buffer management and double buffering
- Consumer API usage (uart_configure, uart_poll_*, uart_fifo_*, uart_tx/rx_enable)
- Reference drivers (nRF UARTE, STM32, NS16550, ARM PL011)

### zephyr-devicetree
Zephyr devicetree binding development for hardware device interfaces. Covers:
- Devicetree binding YAML structure and syntax
- Property types (int, boolean, string, array, phandle, phandle-array)
- Property constraints (required, const, default, enum)
- Base bindings and include mechanism (i2c-device, spi-device, base.yaml)
- Bus-specific bindings (I2C, SPI configuration)
- Controller bindings (GPIO, ADC, DAC with cell specifiers)
- Child-binding patterns for complex devices
- Parent-child devicetree hierarchies (MFD devices)
- Validation, testing, and debugging devicetree issues
- Vendor prefixes and naming conventions

### zephyr-pwm
Zephyr PWM (Pulse Width Modulation) driver development for signal generation. Covers:
- PWM controller driver implementation (set_cycles, get_cycles_per_sec)
- Period and pulse width configuration (nanoseconds and cycles)
- Duty cycle control and frequency calculation
- PWM polarity (normal and inverted)
- PWM input capture for frequency/pulse measurement
- PWM events and callbacks
- Motor control and servo positioning applications
- LED dimming via PWM
- Multi-channel PWM controllers

### zephyr-led
Zephyr LED controller driver development for lighting control. Covers:
- LED driver API (on/off, set_brightness, blink)
- Brightness control (0-100% range)
- Hardware blinking configuration (delay_on, delay_off)
- RGB and multicolor LED control (set_color)
- I2C/SPI LED controller chips (IS31FL, LP55xx)
- PWM-based LED dimming
- GPIO-based LED control
- LED matrix controllers
- Status indicators and LED patterns

### zephyr-charger
Zephyr battery charger driver development for Li-ion/Li-Po charging. Covers:
- Charger driver API (get_property, set_property, charge_enable)
- Charge algorithm (CC-CV: Constant Current, Constant Voltage)
- Charging current and voltage configuration (µA, µV)
- Charging status monitoring (charging, full, discharging, not_charging)
- Charger health and fault detection (overheat, overvoltage)
- External power detection (USB, AC adapter)
- Input current/voltage regulation
- Precharge and termination current
- PMIC charger integration
- SBS (Smart Battery System) protocol

### zephyr-fuel-gauge
Zephyr fuel gauge driver development for battery capacity monitoring. Covers:
- Fuel gauge driver API (get_property, set_property, get_buffer_property)
- State of Charge (SOC) measurement (absolute and relative, 0-100%)
- Battery voltage, current, and temperature monitoring
- Remaining capacity and full charge capacity (µAh)
- Runtime estimation (time to empty, time to full)
- Cycle count and battery health tracking
- SBS (Smart Battery System) registers and protocol
- Coulomb counting and voltage-based SOC
- Battery presence and connection detection
- Manufacturer info and chemistry strings

## Creating New Skills

To add a new no-OS skill:

1. **Create skill folder** with prefix `no-os-*`
2. **Create SKILL.md** with YAML frontmatter:

```yaml
---
name: no-os-my-skill
description: 'Brief description including keywords and triggers'
---
```

3. **Follow the template structure**:
   - Overview and "When to Use" section
   - Core concepts and architecture
   - Data structures and APIs
   - Usage examples
   - Best practices
   - Troubleshooting
   - Quick reference

4. **Update this README** with the new skill

### Naming Convention

All skills use prefixes for their target system:

**no-OS Platform Drivers:**
- `no-os-spi` – SPI drivers
- `no-os-i2c` – I2C drivers
- `no-os-gpio` – GPIO control
- `no-os-irq` – Interrupt handling
- `no-os-uart` – UART drivers
- `no-os-timer` – Timer drivers

**no-OS Device Drivers:**
- `no-os-adc` – ADC (Analog-to-Digital Converter) drivers
- `no-os-dac` – DAC (Digital-to-Analog Converter) drivers
- `no-os-imu` – IMU, accelerometer, and gyroscope drivers
- `no-os-power` – PMIC, regulator, battery charger drivers
- `no-os-temperature` – Temperature sensor drivers
- `no-os-frequency` – Frequency synthesis and clock generation drivers

**no-OS Platform Drivers (Platform-Specific):**
- `no-os-maxim-platform` – Maxim (MAX32xxx, MAX78xxx) platform implementation
- `no-os-stm32-platform` – STM32 platform implementation with HAL integration

**no-OS Frameworks:**
- `no-os-iio` – IIO framework
- `no-os-make-and-linker` – Build system

**no-OS Project & Development:**
- `no-os-project-structure` – Project creation and organization
- `no-os-debugging` – Debugging techniques and troubleshooting

**no-OS Testing:**
- `no-os-unit-testing` – Comprehensive unit testing (Ceedling, Unity, CMock, gcov)
- `testing-strategies` – Cross-platform testing strategies (unit/integration/HIL)

### no-os-imu
IMU, accelerometer, and gyroscope drivers for motion sensing. Covers:
- 3-axis accelerometer and gyroscope data acquisition
- FIFO modes for buffered data collection
- Motion detection features (tap, double-tap, free-fall, activity/inactivity)
- Calibration and offset adjustment
- Burst data read for synchronized sensor data
- Integration with ADIS IMU family
- Reference drivers: ADXL345, ADXL362, ADXL367, ADIS series

### no-os-power
Power management drivers for PMICs, regulators, battery chargers, and monitors. Covers:
- Switching regulators (buck, boost, buck-boost) and linear regulators (LDO)
- Battery charging algorithms (CC-CV for Li-Ion, multi-stage for lead-acid)
- MPPT for solar/renewable inputs
- PMBus protocol and data format conversion
- DVS (Dynamic Voltage Scaling) for power optimization
- Power sequencing and fault protection
- Multi-cell battery monitoring and balancing
- Reference drivers: LT8491, LTC4162L, LT7182S, ADP5055, MAX17851

### no-os-temperature
Temperature sensor drivers for digital sensors, RTD, and thermocouple converters. Covers:
- Digital temperature sensors (I2C interface, 16-bit resolution)
- RTD (Resistance Temperature Detector) converters with 2/3/4-wire configuration
- Thermocouple converters with cold-junction compensation
- Multi-sensor temperature hubs (LTC2983 with up to 20 sensors)
- Temperature threshold and alert configuration
- Calibration techniques (single-point, two-point, custom coefficients)
- 50Hz/60Hz noise filtering
- Reference drivers: ADT7420, MAX31865, MAX31855, LTC2983

### no-os-frequency
Frequency synthesis and clock generation drivers for PLLs and clock distributors. Covers:
- Fractional-N and integer-N PLL synthesis
- VCO configuration and calibration
- Multi-output clock distribution (up to 14 outputs)
- Phase control and synchronization
- SYSREF generation for JESD204B
- Lock detection and PLL optimization
- PMBus interface for clock chips
- Reference drivers: ADF4371, AD9523, ADF4368, HMC7044, LTC6953

### no-os-maxim-platform
Maxim (MAX32xxx, MAX78xxx) platform driver implementation. Covers:
- Platform initialization and clock management
- SPI/I2C/UART/GPIO/Timer/PWM drivers
- DMA configuration and request signal mapping
- Pin multiplexing with MXC_GPIO_Config
- VDDIO voltage level selection (1.8V, 3.3V)
- Interrupt handling and GPIO IRQ
- Family-specific patterns (MAX32650/655/660/665/670/672/690, MAX78000)
- RTC and delay functions

### no-os-stm32-platform
STM32 platform driver implementation with HAL library integration. Covers:
- HAL initialization and handle structures
- SPI/I2C/UART/GPIO/Timer/PWM drivers
- DMA configuration (streams/channels)
- RCC clock management and frequency queries
- GPIO alternate function assignment
- NVIC interrupt management
- Family-specific patterns (STM32F1/F2/F4/F7/H7/L1/L4/G4/U5/H5)
- I2C timing calculation for newer families

**Zephyr RTOS Subsystems:**
- `zephyr-build-system` – West, CMake, Kconfig, overlays
- `zephyr-regulator` – Regulator/PMIC drivers
- `zephyr-sensor` – Sensor drivers
- `zephyr-adc` – ADC drivers
- `zephyr-dac` – DAC drivers
- `zephyr-mfd` – Multi-Function Device drivers (parent-child architecture)
- `zephyr-gpio` – GPIO controllers and expanders
- `zephyr-devicetree` – Devicetree binding creation (YAML interface definitions)
- `zephyr-pwm` – PWM signal generation (motor control, LED dimming, capture)
- `zephyr-led` – LED controllers (brightness, blinking, RGB control)
- `zephyr-charger` – Battery chargers (CC-CV charging, health monitoring)
- `zephyr-fuel-gauge` – Battery fuel gauges (SOC, capacity, runtime estimation)

**General Tools:**
- `datasheet-parsing` – Extracting specifications from datasheets

**Future**: `no-os-pwm`, `zephyr-dac`, `zephyr-gpio`, etc.

### Description Guidelines

Include in the description:
- **Capabilities** – What the skill teaches
- **Triggers** – When to use it (keywords users might say)
- **Platforms** – Specific platforms covered
- **Common tasks** – Typical use cases

Example:
```yaml
description: 'Complete guide to no-OS SPI platform drivers. Use when implementing SPI device drivers, porting to new platforms (Maxim, STM32, Mbed), configuring SPI modes and speeds, implementing DMA transfers, or debugging SPI communication issues.'
```

## Validation Checklist

Before submitting a new skill:

- [ ] Name uses `no-os-*` prefix
- [ ] Name matches folder name exactly
- [ ] Description is 10-1024 characters
- [ ] Description includes trigger keywords
- [ ] YAML frontmatter is properly formatted
- [ ] Includes "When to Use This Skill" section
- [ ] Has code examples
- [ ] Includes troubleshooting section
- [ ] Added to this README's skills table
- [ ] Tested with `/skill-name` command

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [GitHub Awesome Copilot Skills](https://github.com/github/awesome-copilot/tree/main/skills)
- [Creating Effective Skills Guide](https://github.com/github/awesome-copilot/blob/main/website/src/content/docs/learning-hub/creating-effective-skills.md)

## Contributing

To contribute a new skill:

1. Create skill folder following naming convention
2. Write comprehensive SKILL.md with examples
3. Test with GitHub Copilot
4. Update this README
5. Submit a pull request

For questions or suggestions, open an issue in the repository.
