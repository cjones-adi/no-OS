LTC4284 Dual-Core Monitoring Example
=====================================

Overview
--------

This example demonstrates dual-core hot swap monitoring using the LTC4284 on the MAX32690 microcontroller's ARM Cortex-M4F and RISC-V RV32 cores.

Architecture
------------

ARM Cortex-M4 (CPU0) - Main Controller
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Initializes LTC4284 via I2C
* Configures voltage and current thresholds
* Periodically reads telemetry (VIN, IIN, PIN)
* Displays status on UART console
* Boots and manages RISC-V coprocessor
* Receives overcurrent alerts from RISC-V via IPC

RISC-V RV32 (CPU1) - Real-Time Monitor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Monitors LTC4284 ALERT pin via GPIO interrupt
* Provides minimal latency for overcurrent detection
* Sends notifications to ARM via IPC doorbell
* Runs from flash (no SRAM copy required)
* Uses dedicated SRAM region (0x20100000-0x20120000)

Hardware Setup
--------------

**Components:**

* DC2470A (LTC4284 evaluation board)
* MAX32690EVKIT

**Connections:**

.. code-block:: text

   DC2470A          MAX32690EVKIT
   --------         --------------
   SDA       -----> P2.7  (I2C1_SDA)
   SCL       -----> P2.8  (I2C1_SCL)
   ALERT     -----> P0.19 (GPIO, monitored by RISC-V)
   GND       -----> GND

**Power:**

* Connect USB to MAX32690EVKIT for power and debug
* Connect appropriate power source to DC2470A (typically 12V-48V via terminal blocks)

**Console:**

* UART2: 115200 baud, 8N1, no flow control
* Accessible via MAX32690EVKIT on-board USB serial adapter

Building
--------

.. code-block:: bash

   # Navigate to repository root
   cd /path/to/no-OS

   # Configure for MAX32690EVKIT with dual-core example
   cmake --preset max32690evkit -DPROJECT_DEFCONFIG=ltc4284/dual_core.conf

   # Build the project
   cmake --build build-ltc4284-dual_core-max32690evkit

   # The output files are in: build-ltc4284-dual_core-max32690evkit/
   #   - ltc4284.elf  (ARM + embedded RISC-V firmware)
   #   - ltc4284.hex  (Flash programming file)

Programming
-----------

ARM Core (includes embedded RISC-V firmware)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Using OpenOCD (via MAX32690EVKIT on-board CMSIS-DAP)
   openocd -f interface/cmsis-dap.cfg -f target/max32690.cfg \
           -c "program ltc4284.elf verify reset exit"

The ARM ELF file includes the RISC-V firmware embedded in its ``.riscv_flash`` section, so flashing the ARM image programs both cores.

Operation
---------

1. Power up the MAX32690EVKIT
2. The ARM core boots and initializes:

   * UART console
   * I2C interface
   * LTC4284 driver
   * IPC system

3. ARM boots the RISC-V core from embedded firmware
4. RISC-V configures GPIO interrupt on ALERT pin
5. ARM enters main monitoring loop:

   * Reads LTC4284 telemetry every second
   * Displays VIN, IIN, PIN, status
   * Reports alert count from RISC-V

Expected Console Output
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   ====================================================
     LTC4284 Dual-Core Monitoring Example (MAX32690)
   ====================================================
   ARM Core:    I2C control and telemetry
   RISC-V Core: Real-time ALERT pin monitoring
   ----------------------------------------------------
   [ARM] IPC table initialized at 0x20110000
   [ARM] RISC-V coprocessor initialized
   [ARM] RISC-V core booted at 0x10300000
   [ARM] IPC initialized (doorbell + mailbox)
   [ARM] LTC4284 I2C address: 0x5A

   [ARM] Starting monitoring loop...

   [ARM] VIN=12.345V  IIN=0.123A  PIN=1.520W  Status=0x00  Alerts=0
   [ARM] VIN=12.348V  IIN=0.125A  PIN=1.544W  Status=0x00  Alerts=0

   [ARM] !!! OVERCURRENT ALERT from RISC-V (count=1) !!!
   [ARM] VIN=12.342V  IIN=2.456A  PIN=30.312W  Status=0x08  Alerts=1

Inter-Core Communication
------------------------

IPC Mechanism
^^^^^^^^^^^^^

* **Hardware**: MAX32690 SEMA peripheral (semaphore + mailbox)
* **Doorbell**: RISC-V → ARM interrupt on overcurrent event
* **Shared Memory**: IPC table at 0x20110000 (in RISC-V SRAM)

IPC Table Structure
^^^^^^^^^^^^^^^^^^^

.. code-block:: c

   typedef struct {
       uint32_t magic;                  // 0xC0DEC0DE when valid
       volatile uint32_t alert_count;   // Overcurrent event counter
       volatile uint32_t last_alert_ms; // Timestamp of last alert
       uint32_t reserved[13];           // Future expansion
   } ltc4284_ipc_table_t;

Memory Layout
-------------

ARM (CPU0)
^^^^^^^^^^

* Flash: 0x10000000 - 0x10340000 (3.25 MB)
* SRAM:  0x20000000 - 0x20100000 (1 MB)

RISC-V (CPU1)
^^^^^^^^^^^^^

* Flash: 0x10300000 - 0x10340000 (256 KB, embedded in ARM region)
* SRAM:  0x20100000 - 0x20120000 (128 KB, dedicated)

IPC Shared Memory
^^^^^^^^^^^^^^^^^

* Address: 0x20110000 (64 bytes)
* Located in RISC-V SRAM for dual-core access

Troubleshooting
---------------

**No UART output:**

* Check USB connection to MAX32690EVKIT
* Verify UART2 is connected (115200 8N1)
* Ensure proper board power

**No overcurrent alerts:**

* Check ALERT pin connection (DC2470A → P0.19)
* Verify LTC4284 threshold configuration
* Ensure load current exceeds configured threshold
* Check RISC-V core is running (ARM prints boot message)

**RISC-V not booting:**

* Verify ``_riscv_boot`` symbol in linker map
* Check coprocessor initialization in ARM console output
* Ensure max32690_dualcore_arm.ld linker script is used

References
----------

* `LTC4284 Datasheet <https://www.analog.com/ltc4284>`_
* `MAX32690 User Guide <https://www.analog.com/max32690>`_
* no-OS IPC API: ``include/no_os_ipc.h``
* Maxim IPC Driver: ``drivers/platform/maxim/max32690/maxim_ipc.h``
