LTC4284 - High Power Negative Voltage Hot Swap Controller
==========================================================

Supported Devices
-----------------

* `LTC4284 <https://www.analog.com/ltc4284>`_

Overview
--------

The LTC4284 is a high power negative voltage hot swap controller with integrated
I²C energy monitor and EEPROM. It provides comprehensive protection and monitoring
for -48V distributed power systems commonly used in telecom infrastructure, data
centers, and server applications.

The device drives external N-channel MOSFETs to allow a board to be safely
inserted and removed from a live backplane. The dual-gate, multi-mode drivers
optimize the MOSFET safe operating area (SOA) for a variety of power levels,
with an SOA timer limiting MOSFET temperature rise for reliable protection
against overstresses.

Features
--------

* Dual-gate N-channel MOSFET driver for high power applications
* Configurable operating modes: Parallel, Staged Start, or Single modes
* MOSFET SOA timer protection
* Programmable 15 mV to 30 mV current limit sense voltage with <3.3% accuracy
* Adjustable current limit foldback
* 8-bit to 16-bit gear-shift ADC with 0.7% accuracy
* Monitors voltages, currents, power, and energy
* Nonvolatile configuration and fault recording via EEPROM
* Floating topology for rugged high voltage operation
* Selectable inrush control: dV/dt or current limit modes
* I²C/SMBus or single-wire broadcast interfaces
* Min/max ADC measurement logging with programmable alerts
* Reboots on I²C command with programmable delay
* Adjustable input UV/OV thresholds and hysteresis
* 44-Pin 5mm × 8mm QFN Package

Applications
------------

* -48V Telecom and Datacom Infrastructure
* -48V Distributed Power Systems
* Hot-swappable Power Supplies
* Servers and Data Centers
* Network Equipment
* Blade Server Systems

LTC4284 Device Configuration
-----------------------------

Driver Initialization
^^^^^^^^^^^^^^^^^^^^^

The LTC4284 driver is initialized using the following structure. The I²C
address is set in ``no_os_i2c_init_param.slave_address``; there is no separate
``i2c_addr`` field in ``ltc4284_init_param``.

.. code-block:: c

	#include "ltc4284.h"

	struct no_os_i2c_init_param ltc4284_i2c_ip = {
		.device_id    = 0,
		.max_speed_hz = 100000,
		.slave_address = LTC4284_I2C_ADDR_6,  /* 0x16 — ADR1=H, ADR0=H */
		.platform_ops = &max_i2c_ops,
		.extra        = &i2c_extra
	};

	struct ltc4284_init_param ltc4284_ip = {
		.i2c_init      = &ltc4284_i2c_ip,
		.rsense_uohm   = 312,   /* µΩ — DC2470A: 5 mΩ ‖ (6 × 2 mΩ) ≈ 312 µΩ */
		.vpwr_divider  = 40,    /* DC2470A: 390 kΩ / 10 kΩ = 40:1 */
		.drain_divider = 40,    /* DC2470A: 390 kΩ / 10 kΩ = 40:1 */
		.vsense_mv     = 18,    /* V_ILIM: 18 mV (DC2470A EEPROM default) */
		.alert_gpio    = NULL
	};

	struct ltc4284_dev *dev;
	int ret = ltc4284_init(&dev, &ltc4284_ip);

I²C Address Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

The LTC4284 I²C 7-bit address is set by the ADR0 and ADR1 strap pins
(L = VEE, H = INTVCC, NC = float). Eight addresses are available:

======  ======  ==========================
ADR1    ADR0    7-bit Address (define)
======  ======  ==========================
L       L       0x10 (``LTC4284_I2C_ADDR_0``)
L       NC      0x11 (``LTC4284_I2C_ADDR_1``)
H       NC      0x12 (``LTC4284_I2C_ADDR_2``)
L       H       0x13 (``LTC4284_I2C_ADDR_3``)
NC      L       0x14 (``LTC4284_I2C_ADDR_4``)
NC      NC      0x15 (``LTC4284_I2C_ADDR_5``)
H       H       0x16 (``LTC4284_I2C_ADDR_6``) — DC2470A default
NC      H       0x17 (``LTC4284_I2C_ADDR_7``)
======  ======  ==========================

Two global broadcast addresses are also defined:

* ``LTC4284_I2C_ADDR_MASS_WRITE`` (0x1F) — write-only, targets all devices
* ``LTC4284_I2C_ADDR_ALERT_RESP`` (0x0C) — read-only, SMBus Alert Response

Current Limiting Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The current limit is set by the RSENSE resistor value and the V_ILIM sense
voltage programmed in CONFIG_1. Use ``ltc4284_set_ilim_mv`` to change V_ILIM
at runtime (valid range: 15–30 mV in the hardware's 1 mV steps):

.. code-block:: c

	/* Set current limit sense voltage to 25 mV */
	ret = ltc4284_set_ilim_mv(dev, 25);

	/* Configure foldback: 50% of V_ILIM at V_OUT = 0 (DC2470A default) */
	ret = ltc4284_set_foldback(dev, LTC4284_FB_50);

	/* Set OC retry: 7 retries before latch-off */
	ret = ltc4284_set_oc_retry(dev, LTC4284_RETRY_7);

The resulting current limit is: ``I_LIMIT = V_ILIM / R_SENSE``.
For V_ILIM = 18 mV and R_SENSE = 312 µΩ this gives approximately 57.7 A.

Monitoring Functions
^^^^^^^^^^^^^^^^^^^^

The driver provides monitoring functions for voltage, current, power, and energy:

.. code-block:: c

	uint32_t vin_mv, iin_ma, vout_mv, vds_mv, power_mw;
	uint64_t energy_mj;

	/* Read input (bus) voltage */
	ret = ltc4284_read_vin(dev, &vin_mv);

	/* Read input current */
	ret = ltc4284_read_iin(dev, &iin_ma);

	/* Read output bus voltage (computed as VIN - V_DS) */
	ret = ltc4284_read_vout(dev, &vout_mv);

	/* Read drain-to-source voltage across the external MOSFET.
	 * Under normal conduction V_DS is a few mV (I * Rds_on). When the
	 * FET is off V_DS rises toward VIN and inductive transients can peg
	 * the ADC at full-scale (drain_divider * 2.048 V).
	 */
	ret = ltc4284_read_vds(dev, &vds_mv);

	/* Read power consumption */
	ret = ltc4284_read_power(dev, &power_mw);

	/* Read cumulative energy */
	ret = ltc4284_read_energy(dev, &energy_mj);

FET Control
^^^^^^^^^^^

Control MOSFET gate drivers:

.. code-block:: c

	/* Enable FET drivers for hot swap turn-on */
	ret = ltc4284_enable_fet(dev, true);

	/* Disable FET drivers for turn-off */
	ret = ltc4284_enable_fet(dev, false);

Fault Management
^^^^^^^^^^^^^^^^

Read fault status and clear faults:

.. code-block:: c

	uint8_t status, faults;

	/* Read system status */
	ret = ltc4284_read_status(dev, &status);

	/* Get latched fault conditions */
	ret = ltc4284_get_fault(dev, &faults);

	/* Check individual fault bits */
	if (faults & LTC4284_FAULT_UV)
		printf("Undervoltage fault\n");

	if (faults & LTC4284_FAULT_OC)
		printf("Overcurrent fault\n");

	/* Clear all faults */
	ret = ltc4284_clear_faults(dev);

EEPROM Configuration
^^^^^^^^^^^^^^^^^^^^

Store and restore configuration to/from EEPROM:

.. code-block:: c

	/* Snapshot operating registers to EEPROM */
	ret = ltc4284_store_config(dev);

	/* Restore configuration from EEPROM */
	ret = ltc4284_restore_config(dev);

LTC4284 Driver Architecture
----------------------------

Register Interface
^^^^^^^^^^^^^^^^^^

The driver provides a complete register map based on the LTC4284 datasheet:

* **System Status Registers** (0x00–0x04): Status, faults, ADC status
* **Control Registers** (0x0A–0x0F): System control, configuration
* **GPIO Configuration** (0x10–0x12): GPIO and ADC I/O configuration
* **ADC Threshold Registers** (0x1B–0x40): Min/max thresholds for alarm generation
* **ADC Data Registers** (0x41–0x79): Voltage, current, power, and aux readings
* **Energy Meter** (0x7A–0x7F): 48-bit energy accumulator (MSB first)
* **Tick Counter** (0x80–0x83): 32-bit time base counter
* **Meter Control** (0x84–0x85): Meter reset, halt, and snapshot control
* **EEPROM Registers** (0xA2–0xF0): Nonvolatile configuration storage

Multi-Mode Operation
^^^^^^^^^^^^^^^^^^^^^

The LTC4284 supports four operating modes for dual-gate MOSFET control:

1. **Single Driver Mode (Mode 1)**: Single MOSFET for lower power
2. **Parallel Mode (Mode 2)**: Dual parallel MOSFETs for high power
3. **High Stress Staged Start (Mode 3)**: Sequential turn-on for stress management
4. **Low Stress Staged Start (Mode 4)**: Optimized sequential turn-on (DC2470A default)

Mode selection is hardware-pin-configured at power-on, not software-selectable.

Fault Protection
^^^^^^^^^^^^^^^^

The driver supports comprehensive fault detection and auto-retry:

* **Overcurrent (OC)**: Programmable current limit with foldback
* **Overvoltage (OV)**: Adjustable OV threshold with hysteresis
* **Undervoltage (UV)**: Adjustable UV threshold with hysteresis (-43V hardware lockout)
* **FET Bad**: MOSFET failure detection
* **FET Short**: MOSFET short circuit detection
* **External Fault**: Integration with external fault monitors
* **Power Failed**: Power good monitoring with timeout

All faults support configurable auto-retry with programmable cooling delays.

LTC4284 Support
---------------

Hardware Platforms
^^^^^^^^^^^^^^^^^^

The driver has been tested on:

* **MAX32690EVKIT** (Arm Cortex-M4 and RISC-V RV32 cores)
* **DC2470A** evaluation kit (LTC4284 demo board)

Additional platform support can be added by implementing the no-OS I²C platform
drivers for the target MCU.

Documentation
^^^^^^^^^^^^^

* **Datasheet**: https://www.analog.com/ltc4284
* **Evaluation Kit**: https://www.analog.com/DC2470A

Support and Contact
^^^^^^^^^^^^^^^^^^^

For questions or support:

* **no-OS Repository**: https://github.com/analogdevicesinc/no-OS
* **Technical Support**: https://www.analog.com/support
