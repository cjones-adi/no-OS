/***************************************************************************//**
 *   @file   dual_core_example.c
 *   @brief  ARM Cortex-M4F (CPU0) side of LTC4284 dual-core monitoring example.
 *   @author Analog Devices Inc.
 *
 * This example demonstrates dual-core LTC4284 hot swap monitoring on MAX32690:
 *
 * ARM (CPU0) responsibilities:
 * - Initialize LTC4284 driver via I2C
 * - Configure voltage and current thresholds
 * - Periodically read telemetry (VIN, IIN, PIN)
 * - Display status on UART console
 * - Boot and manage RISC-V coprocessor
 * - Receive overcurrent alerts from RISC-V via IPC
 *
 * RISC-V (CPU1) responsibilities:
 * - Monitor LTC4284 ALERT pin via GPIO interrupt (real-time)
 * - Send overcurrent notifications to ARM via IPC doorbell
 * - Minimal latency for hardware protection events
 *
 * Hardware setup (DC2470A + MAX32690EVKIT):
 * - DC2470A SDA  -> P2.7 (I2C1_SDA)
 * - DC2470A SCL  -> P2.8 (I2C1_SCL)
 * - DC2470A ALERT -> P0.19 (GPIO, monitored by RISC-V core)
 * - Console: UART2 (115200 8N1)
 *
 ******************************************************************************
 * Copyright 2026(c) Analog Devices, Inc.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of Analog Devices, Inc. nor the names of its
 *    contributors may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES, INC. "AS IS" AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
 * EVENT SHALL ANALOG DEVICES, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
 * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
 * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *******************************************************************************/

#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include "no_os_uart.h"
#include "no_os_delay.h"
#include "no_os_ipc.h"
#include "no_os_barrier.h"
#include "no_os_util.h"
#include "no_os_error.h"
#include "maxim_ipc.h"
#include "common_data.h"
#include "parameters.h"
#include "mxc_sys.h"
#include "dual_core_ltc4284_ipc.h"

/* External symbol from linker script */
extern uint8_t _riscv_boot;

/* Pointer to shared IPC memory */
static volatile ltc4284_ipc_table_t *const g_ipc_table =
	(volatile ltc4284_ipc_table_t *)LTC4284_IPC_TABLE_ADDR;

/* IPC descriptor */
static struct no_os_ipc_desc *ipc_desc;

/* Alert statistics */
static volatile uint32_t arm_alert_count = 0;

/**
 * @brief Boot RISC-V coprocessor using SDK function
 */
static void boot_riscv_coprocessor(void)
{
	printf("[ARM] Booting RISC-V coprocessor at 0x%08lx...\r\n",
	       (unsigned long)&_riscv_boot);

	/*
	 * Note: MXC_SYS_RISCVRun() expects _binary_riscv_bin_start symbol
	 * from the SDK's dual-core template. Our CMake build uses _riscv_boot.
	 * We can either:
	 *   1) Rename the symbol in our linker script
	 *   2) Use direct register manipulation here
	 *
	 * For now, use direct register access matching the SDK implementation.
	 */

	/* Disable RISC-V core */
	MXC_GCR->pclkdis1 |= MXC_F_GCR_PCLKDIS1_CPU1;

	/* Set boot address to embedded firmware */
	/* MXC_FCR is defined in max32690.h but fcr_regs.h needs to be included */
	*((volatile uint32_t *)(MXC_BASE_FCR + 0x00)) = (uint32_t)&_riscv_boot;

	/* Enable and release RISC-V from reset */
	MXC_GCR->pclkdis1 &= ~MXC_F_GCR_PCLKDIS1_CPU1;
	MXC_GCR->rst1 |= MXC_F_GCR_RST1_CPU1;

	printf("[ARM] RISC-V coprocessor booted\r\n");
}

/**
 * @brief Check for and handle RISC-V alerts via IPC
 */
static void check_riscv_alerts(void)
{
	/* Read alert count from shared memory */
	no_os_barrier_full();
	uint32_t new_count = g_ipc_table->alert_count;

	/* Check if alert count increased */
	if (new_count > arm_alert_count) {
		arm_alert_count = new_count;
		printf("\r\n[ARM] !!! OVERCURRENT ALERT from RISC-V (count=%lu) !!!\r\n",
		       (unsigned long)arm_alert_count);
	}
}

/**
 * @brief Initialize shared IPC table
 */
static void init_ipc_table(void)
{
	volatile ltc4284_ipc_table_t *tbl = g_ipc_table;

	/* Clear the table */
	tbl->magic = 0;
	no_os_barrier_full();

	tbl->alert_count = 0;
	tbl->last_alert_ms = 0;

	no_os_barrier_full();

	/* Validate the table */
	tbl->magic = LTC4284_IPC_MAGIC;
	no_os_barrier_full();

	printf("[ARM] IPC table initialized at 0x%08lx\r\n", (unsigned long)tbl);
}

/**
 * @brief Initialize IPC (doorbell + mailbox)
 */
static int init_ipc(void)
{
	int ret;
	struct no_os_ipc_init_param ipc_param = {
		.platform_ops = &max_ipc_ops,
		.extra = NULL
	};

	ret = no_os_ipc_init(&ipc_desc, &ipc_param);
	if (ret) {
		printf("[ARM] ERROR: IPC init failed (%d)\r\n", ret);
		return ret;
	}

	printf("[ARM] IPC initialized (doorbell + mailbox)\r\n");
	return 0;
}

/**
 * @brief Send command to RISC-V and wait for response
 */
static int send_command(uint32_t opcode, uint32_t param1, uint32_t param2)
{
	volatile ltc4284_ipc_table_t *tbl = g_ipc_table;
	uint32_t start_ms;
	uint32_t expected_seq;

	/* Wait for RISC-V ready */
	start_ms = 0; /* Simplified timeout for no_os_mdelay */
	while (tbl->status & LTC4284_STATUS_BUSY) {
		if (start_ms++ > 100) {
			printf("[ARM] ERROR: RISC-V busy timeout\r\n");
			return -ETIMEDOUT;
		}
		no_os_udelay(1000);
	}

	/* Send command */
	expected_seq = tbl->cmd_sequence + 1;
	tbl->cmd_opcode = opcode;
	tbl->cmd_param1 = param1;
	tbl->cmd_param2 = param2;
	tbl->cmd_sequence = expected_seq;
	no_os_barrier_full();

	/* Notify RISC-V */
	no_os_ipc_notify(ipc_desc, NO_OS_IPC_CHAN_COPROC);

	/* Wait for response */
	start_ms = 0;
	while (tbl->rsp_sequence != expected_seq) {
		if (start_ms++ > 100) {
			printf("[ARM] ERROR: Response timeout\r\n");
			return -ETIMEDOUT;
		}
		no_os_udelay(1000);
	}

	no_os_barrier_full();
	return (tbl->rsp_error_code == 0) ? 0 : -EIO;
}

/**
 * @brief Request and display telemetry from RISC-V
 */
static void display_telemetry(void)
{
	volatile ltc4284_ipc_table_t *tbl = g_ipc_table;
	int ret;

	/* Request fresh telemetry */
	ret = send_command(LTC4284_CMD_READ_TELEMETRY, 0, 0);
	if (ret) {
		printf("[ARM] ERROR: Telemetry request failed\r\n");
		return;
	}

	/* Read from shared memory */
	no_os_barrier_full();
	printf("[ARM] VIN=%lu.%03luV  IIN=%lu.%03luA  PIN=%lu.%03luW  VOUT=%lu.%03luV  "
	       "Status=0x%02X  Energy=%lluJ  Alerts=%lu\r\n",
	       (unsigned long)(tbl->telemetry.vin_mv / 1000),
	       (unsigned long)(tbl->telemetry.vin_mv % 1000),
	       (unsigned long)(tbl->telemetry.iin_ma / 1000),
	       (unsigned long)(tbl->telemetry.iin_ma % 1000),
	       (unsigned long)(tbl->telemetry.pin_mw / 1000),
	       (unsigned long)(tbl->telemetry.pin_mw % 1000),
	       (unsigned long)(tbl->telemetry.vout_mv / 1000),
	       (unsigned long)(tbl->telemetry.vout_mv % 1000),
	       tbl->telemetry.status_reg,
	       (unsigned long long)(tbl->telemetry.energy_mj / 1000),
	       (unsigned long)tbl->alert_count);
}

/**
 * @brief Main dual-core example
 */
int example_main(void)
{
	int ret;
	uint32_t loop_count = 0;
	uint32_t start_ms;

	printf("\r\n====================================================\r\n");
	printf("  LTC4284 Dual-Core Monitoring Example (MAX32690)  \r\n");
	printf("====================================================\r\n");
	printf("ARM Core:    User interface and telemetry display\r\n");
	printf("RISC-V Core: I2C control and ALERT monitoring\r\n");
	printf("----------------------------------------------------\r\n\r\n");

	/* Initialize shared IPC table */
	init_ipc_table();

	/* Boot RISC-V coprocessor */
	boot_riscv_coprocessor();

	/* Give RISC-V time to initialize */
	no_os_mdelay(100);

	/* Initialize IPC */
	ret = init_ipc();
	if (ret)
		return ret;

	/* Wait for RISC-V ready signal */
	printf("[ARM] Waiting for RISC-V initialization...\r\n");
	start_ms = 0;
	while (!(g_ipc_table->status & LTC4284_STATUS_READY)) {
		if (start_ms++ > 5000) {
			printf("[ARM] ERROR: RISC-V timeout\r\n");
			return -ETIMEDOUT;
		}
		no_os_mdelay(1);
	}
	printf("[ARM] RISC-V core ready\r\n\r\n");

	/* Main monitoring loop */
	printf("[ARM] Starting telemetry monitoring...\r\n\r\n");
	while (1) {
		/* Check for alerts from RISC-V */
		check_riscv_alerts();

		/* Display telemetry */
		display_telemetry();

		if (++loop_count % 10 == 0) {
			printf("[ARM] --- %lu seconds, I2C errors: %lu, failed: %lu ---\r\n",
			       (unsigned long)loop_count,
			       (unsigned long)g_ipc_table->i2c_errors,
			       (unsigned long)g_ipc_table->failed_commands);
		}

		no_os_mdelay(1000);
	}

	return 0;
}
