LTC4284 Project
===============

Overview
--------

This project demonstrates the LTC4284 High Power Negative Voltage Hot Swap
Controller driver running on the MAX32690EVKIT, interfacing with the DC2470A
evaluation kit.

The LTC4284 is designed for -48V distributed power systems commonly used in
telecom infrastructure and data centers. It provides hot swap control, power
monitoring, and fault protection with a built-in energy meter and EEPROM.

Supported Evaluation Boards
----------------------------

* `DC2470A <https://www.analog.com/DC2470A>`_ — LTC4284 Evaluation Kit

Hardware Setup
--------------

**Required Hardware:**

* DC2470A Evaluation Kit (LTC4284 demo board)
* MAX32690EVKIT
* PCA9603 I²C level shifter (or equivalent) — required because the DC2470A
  I²C bus is pulled to LTC4284's INTVCC (5V), while the MAX32690 GPIOs are 3.3V
* -48V power supply
* USB cable for UART console (CN2 connector - FTDI USB-to-UART bridge)

**Connections:**

=================  ======================  ===========================
DC2470A            MAX32690EVKIT           Description
=================  ======================  ===========================
SDA (5V)           P2.7 via PCA9603        I²C data
SCL (5V)           P2.8 via PCA9603        I²C clock
ALERT# (optional)  GPIO pin                Alert interrupt (optional)
GND                GND                     Common ground (float-safe)
=================  ======================  ===========================

**Power Configuration:**

* DC2470A: Connect -48V input power supply and an electronic load to the output
* MAX32690EVKIT: Connect USB for power and UART console
* PCA9603 VCCA (MCU side) = 3.3V, VCCB (DC2470A side) = 5V

**I²C Address Configuration (DC2470A default):**

The DC2470A straps ADR1=H (INTVCC) and ADR0=H (INTVCC), selecting address
``LTC4284_I2C_ADDR_6`` (0x16). This is set in ``common_data.c``:

.. code-block:: c

   .slave_address = LTC4284_I2C_ADDR_6,

**UART Console (CN2):**

The MAX32690EVKIT's CN2 connector provides serial console output via an on-board
FTDI USB-to-UART bridge chip. The MCU uses its UART2 peripheral, configured at
115200 baud, 8N1.

On Linux, the console appears as ``/dev/ttyUSB0`` (or similar):

.. code-block:: bash

   # Connect to console
   screen /dev/ttyUSB0 115200

On Windows, the console appears as a COM port. Use PuTTY or similar terminal
software with settings: 115200 baud, 8 data bits, no parity, 1 stop bit.

Software Setup
--------------

**Build Configuration:**

The project supports the following build targets:

.. code-block:: bash

   # Basic continuous monitoring example (Arm core)
   make PLATFORM=maxim TARGET=max32690 EXAMPLE=basic

   # Overcurrent protection example (Arm core)
   make PLATFORM=maxim TARGET=max32690 EXAMPLE=overcurrent

   # OC smoke test — software-injected fault (Arm core)
   make PLATFORM=maxim TARGET=max32690 EXAMPLE=oc_smoke_test

   # Any example on the RISC-V core
   make PLATFORM=maxim TARGET=max32690 EXAMPLE=overcurrent CPU=riscv

**Programming the MAX32690EVKIT (Arm core):**

.. code-block:: bash

   make PLATFORM=maxim TARGET=max32690 EXAMPLE=basic run

**Programming the MAX32690EVKIT (RISC-V core — two-step procedure):**

The MSDK's ``max32690_riscv.cfg`` has a known ``$_CHIPNAME`` typo in its
flash bank definition and cannot be used directly. Use the workaround below.

Step 1 — Flash the Arm loader (releases the RV32 core after 2 s):

.. code-block:: bash

   openocd -s <MAXIM_PATH>/Tools/OpenOCD/scripts \
       -f interface/cmsis-dap.cfg -f target/max32690.cfg \
       -c "program /tmp/rv_arm_loader/build/max32690.elf verify reset exit"

Step 2 — Flash the RV32 application ELF into the RISC-V flash region
(``0x10300000``). Create ``/tmp/flash_riscv.cfg``:

.. code-block:: text

   source [find interface/cmsis-dap.cfg]
   source [find target/max32690.cfg]
   flash bank riscv_flash max32xxx 0x10300000 0x40000 0 0 max32xxx.cpu 0x40029400 0x2000 60 0x01

Then flash:

.. code-block:: bash

   openocd -s <MAXIM_PATH>/Tools/OpenOCD/scripts \
       -f /tmp/flash_riscv.cfg \
       -c "program projects/ltc4284/build/ltc4284.elf verify reset exit"

Running the Examples
--------------------

Basic Example
~~~~~~~~~~~~~

Continuously monitors all LTC4284 telemetry channels and decodes fault bits.

1. Build and flash the firmware
2. Open UART console at 115200 baud, 8N1, no flow control (UART2 on MAX32690EVKIT)
3. Apply -48V to the DC2470A

**Expected output:**

.. code-block:: text

   LTC4284 Basic Example
   LTC4284 initialized successfully.

    VIN: 48800 mV | IIN:  487 mA | VOUT: 48510 mV | PWR: 23763 mW | ENERGY: ... mJ | FAULT: 0x00

Overcurrent Example
~~~~~~~~~~~~~~~~~~~

Live monitoring with fault decode, retry narration, and configurable overcurrent
protection parameters. Shows the OC retry loop and reports fault register values
with human-readable bit descriptions.

.. code-block:: bash

   make PLATFORM=maxim TARGET=max32690 EXAMPLE=overcurrent

**Expected output (normal operation):**

.. code-block:: text

   LTC4284 Overcurrent Protection Example
   ILIM set to 18 mV | RSENSE = 312 uohm | I_LIMIT ~ 57692 mA
    VIN: 48800 mV | IIN:  487 mA | PWR: 23499 mW | FAULT: 0x00

**UV false-trip note:** If the bench PSU sags below the LTC4284's -43V UV
lockout threshold under load (due to alligator clip or wiring resistance),
the chip trips with ``FAULT=0x22`` (UV + POWER_FAILED) rather than a real OC
event. Reduce series resistance or increase PSU setpoint to avoid this.

OC Smoke Test Example
~~~~~~~~~~~~~~~~~~~~~

Software-injected fault test — does not require a live load or -48V supply.
Exercises the fault decode and clear path by writing a fault condition directly
to the LTC4284's fault register, then verifying the driver reads and clears it
correctly.

.. code-block:: bash

   make PLATFORM=maxim TARGET=max32690 EXAMPLE=oc_smoke_test

Useful for CI or bench-less bring-up validation.

Configuration
-------------

Board-specific values in ``src/common/common_data.c``:

.. code-block:: c

   struct ltc4284_init_param ltc4284_ip = {
       .i2c_init      = &ltc4284_i2c_ip,
       .rsense_uohm   = 312,   /* uohm -- DC2470A: 5 mohm || (6 x 2 mohm) = 312 uohm */
       .vpwr_divider  = 40,    /* DC2470A: 390 kohm / 10 kohm = 40:1 */
       .drain_divider = 40,    /* DC2470A: 390 kohm / 10 kohm = 40:1 */
       .vsense_mv     = 18,    /* V_ILIM: 18 mV (DC2470A EEPROM altered default) */
       .alert_gpio    = NULL,
   };

Modify ``rsense_uohm`` and the dividers to match your hardware if using a
different carrier board.

Troubleshooting
---------------

**I²C Communication Failures (-9 / E_COMM_ERR):**

* Verify pull-up resistors on the DC2470A I²C bus (4.7 kohm to INTVCC)
* Confirm PCA9603 VCCB is powered from the DC2470A 5V rail, not from the MCU
* Check I²C address matches ADR strap configuration
* Ensure DC2470A has -48V applied before the MCU tries to communicate

**Device Not Responding:**

* Verify DC2470A has a -48V power supply connected
* Check ALERT# pin if a fault is latched
* Try power cycling both boards

**Incorrect Measurements:**

* Verify ``rsense_uohm`` in ``common_data.c`` matches your hardware
* Check that ``vpwr_divider`` / ``drain_divider`` match the resistor network

**RISC-V build: "invalid origin for memory region FLASH":**

Ensure you are not setting ``DUAL_CORE=1``. The ``maxim.mk`` RISC-V block
injects the required memory region symbols directly for standalone builds.

**RISC-V flash: "target 'max32xxx_riscv.cpu' not defined":**

The MSDK's ``max32690_riscv.cfg`` cannot be used for flashing. Use the
two-step OpenOCD procedure described in the Software Setup section above.

Support
-------

* `LTC4284 Product Page <https://www.analog.com/ltc4284>`_
* `DC2470A Evaluation Kit <https://www.analog.com/DC2470A>`_
* `LTC4284 Datasheet <https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4284.pdf>`_
* `no-OS Repository <https://github.com/analogdevicesinc/no-OS>`_
