LTC4284 Dual-Core Overcurrent Demo
===================================

Overview
--------

Dual-core hot swap + overcurrent protection using the LTC4284 on the
MAX32690 (ARM Cortex-M4F + RISC-V RV32).

The RISC-V core owns the I2C bus and the ALERT GPIO. It programs the OC
profile (V_ILIM, foldback, retry policy), enables the FET, and reacts to
ALERT edges with minimal latency. The ARM core is a pure observer: it boots
the coprocessor, polls telemetry over IPC, prints the OC banner and every
telemetry line, and narrates FAULT / FET state transitions.

Architecture
------------

ARM Cortex-M4F (CPU0) — Observer / Console
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Boots the RISC-V coprocessor from the embedded flash region
* Owns the shared IPC table + UART console
* Polls RISC-V for telemetry and the OC config snapshot
* Prints the OC banner (uses live ``CONFIG_1`` / ``CONTROL_2`` bytes read
  from the chip after RISC-V programs it)
* Decodes ``FAULT`` bits into a human-readable string
* Auto-sends ``CMD_CLEAR_FAULTS`` on new faults so the retry loop stays
  observable
* Narrates ``FET turned off`` / ``Retry succeeded. FET back on.``
  transitions

RISC-V RV32 (CPU1) — Real-Time Controller
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Brings up I2C0 (device-id 0, 100 kHz, VDDIOH pads)
* Initializes the LTC4284 driver
* Programs the OC profile from local macros in
  ``dual_core_example_riscv.c``:

  .. code-block:: c

     #define OC_ILIM_MV       15                /* V_ILIM in mV, 15..30 */
     #define OC_FOLDBACK      LTC4284_FB_50     /* Startup foldback */
     #define OC_RETRY_POLICY  LTC4284_RETRY_1   /* 1 retry then latch */

* Clears faults and enables the FET
* Configures a rising-edge GPIO interrupt on the LTC4284 ALERT pin (P0.19)
* Rings the ARM doorbell on every ALERT edge (RISC-V is the sole owner of
  the ALERT wire; the ARM is only notified via IPC)
* Serves IPC commands from ARM: ``READ_TELEMETRY``, ``READ_CONFIG_REGS``,
  ``CLEAR_FAULTS``, ``ENABLE_FET``, ``NOP``

Hardware Setup
--------------

**Components:**

* DC2470A (LTC4284 evaluation board)
* MAX32690EVKIT
* I²C level shifter — required because the DC2470A I²C bus is pulled to
  the LTC4284's INTVCC (5 V), while the MAX32690 GPIOs are 3.3 V
* Bench PSU capable of the trip current (see note below)
* Electronic load

**Connections:**

.. code-block:: text

   DC2470A (5 V bus)   MAX32690EVKIT (3.3 V)
   ------------------  ---------------------
   SDA (5 V)      -->  P2.7  (I2C0_SDA)   via level shifter
   SCL (5 V)      -->  P2.8  (I2C0_SCL)   via level shifter
   ALERT#         -->  P0.19 (GPIO, monitored by RISC-V)
   GND            -->  GND

**Wiring for the OC trip:**

With ``OC_ILIM_MV = 15`` and DC2470A ``RSENSE = 312 uohm`` the steady-state
trip is ~48 A and the fast (short-circuit) trip is ~96 A. Use **10 AWG
minimum ring-lug leads** — alligator clips will burn.

**Console:**

* UART2 (CN2 on MAX32690EVKIT), 115200 8N1, no flow control
* Appears as ``/dev/ttyUSB0`` on Linux via the on-board FTDI USB-to-UART
  bridge

Building
--------

.. code-block:: bash

   python tools/scripts/no_os_build.py build \
       --project ltc4284 \
       --variant dual_core \
       --board  max32690evkit

Build artifacts land in ``build-ltc4284-dual_core-max32690evkit/build/``:

* ``ltc4284.elf`` — ARM ELF with the RISC-V firmware embedded in
  ``.riscv_flash`` at ``0x10300000``
* ``ltc4284.hex`` — combined flash image

Flashing programs both cores in one shot.

Operation
---------

1. Power up the MAX32690EVKIT (USB) and the DC2470A (-48 V bench PSU).
2. The ARM prints the banner and boots the RISC-V core.
3. RISC-V initializes the LTC4284, programs the OC profile, and signals
   ready.
4. ARM fetches the config snapshot and prints the OC banner.
5. ARM polls telemetry every second and prints one line per poll.
6. Ramp the e-load past the configured trip current to observe the OC
   sequence.

Expected Console Output
^^^^^^^^^^^^^^^^^^^^^^^

Startup:

.. code-block:: text

   ====================================================
     LTC4284 Dual-Core Monitoring Example (MAX32690)
   ====================================================
   ARM Core:    User interface and telemetry display
   RISC-V Core: I2C control and OC monitoring
   ----------------------------------------------------

   [ARM] IPC table initialized at 0x20110000
   [ARM] Booting RISC-V coprocessor at 0x10300000...
   [ARM] RISC-V coprocessor booted
   [ARM] IPC initialized (doorbell + mailbox)
   [ARM] Waiting for RISC-V initialization...
   [ARM] RISC-V core ready

   ==== LTC4284 OC Config ====
     RSENSE          : 312 uohm
     CONFIG_1        : 0x04 (after programming)
     CONTROL_2       : 0x07 (after programming)
     V_ILIM          : 15 mV
     V_ILIM(FAST)    : 30 mV (auto 2x)
     Trip (steady)   : ~48076 mA
     Trip (fast)     : ~96152 mA
     OC retry policy : 1 retry then latch
   =========================

Steady-state telemetry:

.. code-block:: text

   [ARM] VIN=48.800V  IIN=0.000A  PIN=0.000W  VOUT=48.800V  VDS=0.000V  FET=1 PG=1  Alerts=0
   [ARM] VIN=48.800V  IIN=2.456A  PIN=119.865W  VOUT=48.795V  VDS=0.005V  FET=1 PG=1  Alerts=0

OC trip (steady-state exceed, single retry then latch):

.. code-block:: text

   [RV32->ARM] OVERCURRENT ALERT (RISC-V detected ALERT pin, notified ARM via IPC doorbell, count=1)
   [ARM] VIN=48.750V  IIN=48.100A  PIN=2344.611W  VOUT=0.150V  VDS=48.600V  FET=0 PG=0  Alerts=1
     ** FAULT 0x04: OC **
     [RV32] FET turned off. Waiting for auto-retry...
     --> FET is OFF.
   [ARM] VIN=48.800V  IIN=0.000A  ...  FET=1 PG=1  Alerts=1
     --> Retry succeeded. FET back on.

If the load stays above the trip current on the retry, the chip latches
off. A manual power cycle (or the loop's auto ``CMD_CLEAR_FAULTS`` combined
with the load dropping below trip) is required to recover.

KNOWN NON-ISSUE — Bench PSU sag
--------------------------------

If the supply cannot cleanly source the trip current, VIN sags below the
~43 V UV threshold when the load engages. The chip then trips on
``UV + POWER_FAILED`` (sometimes with a spurious OC bit set from the
transient), which looks like a false OC trip at low current — commonly
observed around 500 mA on a small bench supply with alligator clips.

**Signature:** ``FAULT = 0x22`` or ``0x26`` (UV + POWER_FAILED, sometimes
with OC), and VIN visibly sagging in the log before the trip.

This is **not** an overcurrent event and **not** a code problem. A proper
>60 A PSU with 10 AWG ring-lug leads will not exhibit it; VIN stays stable
and the real OC trip fires at ~48 A as programmed.

Inter-Core Communication
-------------------------

**IPC hardware:** MAX32690 SEMA peripheral (doorbell semaphores).
The ARM rings ``irq0`` (RISC-V-side); RISC-V rings ``irq1`` (ARM-side).

**Shared memory:** IPC table at ``0x20110000`` in the RISC-V-dedicated
SRAM region (accessible by both cores).

**Commands (ARM → RISC-V):**

* ``LTC4284_CMD_NOP`` — heartbeat
* ``LTC4284_CMD_READ_TELEMETRY`` — populates the ``telemetry`` block
* ``LTC4284_CMD_CLEAR_FAULTS`` — writes the FAULT clear pattern
* ``LTC4284_CMD_ENABLE_FET`` — ``param1`` = 0/1
* ``LTC4284_CMD_READ_CONFIG_REGS`` — populates the ``config`` snapshot with
  ``CONFIG_1``, ``CONTROL_2``, and the programmed OC settings

**Handshake:** ARM writes ``cmd_opcode`` + ``cmd_param*``, increments
``cmd_sequence``, then rings the RISC-V doorbell. RISC-V processes the
command, writes ``rsp_error_code`` and sets ``rsp_sequence`` equal to
``cmd_sequence``, then rings the ARM doorbell. ARM polls
``rsp_sequence == cmd_sequence`` to detect completion.

**RISC-V → ARM notifications:** OC ALERT edges from the LTC4284's ALERT
pin. RISC-V increments ``alert_count`` and rings the ARM doorbell. ARM
polls ``alert_count`` each loop and prints ``[RV32->ARM] OVERCURRENT
ALERT ...`` when it advances.

Memory Layout
-------------

ARM (CPU0)
^^^^^^^^^^

* Flash: ``0x10000000 - 0x10300000`` (3 MB ARM region)
* SRAM:  ``0x20000000 - 0x20100000`` (1 MB)

RISC-V (CPU1)
^^^^^^^^^^^^^

* Flash: ``0x10300000 - 0x10340000`` (256 KB, embedded in ARM ELF)
* SRAM:  ``0x20100000 - 0x20120000`` (128 KB, dedicated)

IPC Shared Memory
^^^^^^^^^^^^^^^^^

* Address: ``0x20110000``
* Size: 256 bytes (defined by ``ltc4284_ipc_table_t``)
* Located in RISC-V SRAM for dual-core access

Debugging (dual-core)
---------------------

The RISC-V firmware is embedded in the ARM ELF via ``.incbin``. To debug
both cores at once you need two GDB sessions — one per core — each backed
by its own OpenOCD server on a different port. The RISC-V symbols are in
the separately-built ``riscv.elf`` inside the build tree
(``build-ltc4284-dual_core-max32690evkit/projects/ltc4284/coprocessor/``).

Troubleshooting
---------------

**No UART output**

* Check USB cable to CN2 on the MAX32690EVKIT
* Verify UART2 is enumerated (``/dev/ttyUSB0`` on Linux) at 115200 8N1
* Confirm on-board FTDI adapter has power

**Banner prints but no telemetry**

* RISC-V may have failed the OC programming step. Watch for a stuck
  ``STATUS_ERROR`` bit in the IPC status before the ``[ARM] RISC-V core
  ready`` line

**Telemetry runs but no OC alert fires under load**

* Verify the ALERT wire from DC2470A to MAX32690EVKIT P0.19
* Confirm the load actually exceeds the programmed trip current (see banner)
* Check the RISC-V is running: ``[ARM] RISC-V coprocessor booted`` must
  appear at startup

**RISC-V not booting** (banner never advances past "Waiting for RISC-V…")

* Verify ``_riscv_boot`` symbol exists in the ARM linker map
* Confirm ``FCR->urvbootaddr`` is being programmed (should match the
  ``[ARM] Booting RISC-V coprocessor at 0x…`` address)
* Confirm the ``interrupt("machine")`` attribute is on the RISC-V IRQ
  handlers — without it, ``mret`` is not emitted and interrupts stop
  after the first firing

References
----------

* `LTC4284 Datasheet <https://www.analog.com/ltc4284>`_
* `MAX32690 User Guide <https://www.analog.com/max32690>`_
* IPC protocol: ``dual_core_ltc4284_ipc.h``
* no-OS IPC API: ``include/no_os_ipc.h``
* Maxim IPC driver: ``drivers/platform/maxim/max32690/maxim_ipc.h``
