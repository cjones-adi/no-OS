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
#include "no_os_uart.h"
#include "no_os_delay.h"
#include "no_os_ipc.h"
#include "no_os_barrier.h"
#include "ltc4284.h"
#include "maxim_ipc.h"
#include "common_data.h"
#include "parameters.h"

/* Shared IPC memory for ARM <-> RISC-V communication */
#define IPC_TABLE_ADDR 0x20110000UL  /* In RISC-V SRAM region */

typedef struct {
	uint32_t magic;                  /* 0xC0DEC0DE when valid */
	volatile uint32_t alert_count;   /* Overcurrent event counter from RISC-V */
	volatile uint32_t last_alert_ms; /* Timestamp of last alert */
	uint32_t reserved[13];           /* Padding to 64 bytes */
} ltc4284_ipc_table_t;

static volatile ltc4284_ipc_table_t *const g_ipc_table =
	(volatile ltc4284_ipc_table_t *)IPC_TABLE_ADDR;

#define LTC4284_IPC_MAGIC 0xC0DEC0DEUL

/* IPC descriptor */
static struct no_os_ipc_desc *ipc_desc;

/* LTC4284 device descriptor */
extern struct ltc4284_dev *ltc4284_dev;

/* Alert statistics */
static volatile uint32_t arm_alert_count = 0;

/**
 * @brief IPC doorbell callback - invoked when RISC-V signals an alert
 */
static void ltc4284_alert_callback(void *ctx)
{
	(void)ctx;

	/* Read alert count from shared memory */
	no_os_barrier_full();
	arm_alert_count = g_ipc_table->alert_count;

	printf("\r\n[ARM] !!! OVERCURRENT ALERT from RISC-V (count=%lu) !!!\r\n",
	       (unsigned long)arm_alert_count);
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

	/* Register callback for RISC-V doorbell */
	ret = no_os_ipc_register_callback(ipc_desc, NO_OS_IPC_CHAN_HOST,
	                                   ltc4284_alert_callback, NULL);
	if (ret) {
		printf("[ARM] ERROR: IPC callback registration failed (%d)\r\n", ret);
		return ret;
	}

	printf("[ARM] IPC initialized (doorbell + mailbox)\r\n");
	return 0;
}

/**
 * @brief Read and display LTC4284 telemetry
 */
static void display_telemetry(void)
{
	int ret;
	uint32_t vin_mv, iin_ma, pin_mw;
	uint8_t status;

	/* Read voltage */
	ret = ltc4284_read_vin(ltc4284_dev, &vin_mv);
	if (ret) {
		printf("[ARM] ERROR: Failed to read VIN\r\n");
		return;
	}

	/* Read current */
	ret = ltc4284_read_iin(ltc4284_dev, &iin_ma);
	if (ret) {
		printf("[ARM] ERROR: Failed to read IIN\r\n");
		return;
	}

	/* Calculate power */
	pin_mw = (vin_mv * iin_ma) / 1000;

	/* Read status */
	ret = ltc4284_read_status(ltc4284_dev, &status);
	if (ret) {
		printf("[ARM] ERROR: Failed to read status\r\n");
		return;
	}

	printf("[ARM] VIN=%u.%03uV  IIN=%u.%03uA  PIN=%u.%03uW  Status=0x%02X  Alerts=%lu\r\n",
	       vin_mv / 1000, vin_mv % 1000,
	       iin_ma / 1000, iin_ma % 1000,
	       pin_mw / 1000, pin_mw % 1000,
	       status,
	       (unsigned long)arm_alert_count);
}

/**
 * @brief Main dual-core example
 */
int example_main(void)
{
	int ret;

	printf("\r\n");
	printf("====================================================\r\n");
	printf("  LTC4284 Dual-Core Monitoring Example (MAX32690)  \r\n");
	printf("====================================================\r\n");
	printf("ARM Core:    I2C control and telemetry\r\n");
	printf("RISC-V Core: Real-time ALERT pin monitoring\r\n");
	printf("----------------------------------------------------\r\n");

	/* Initialize shared IPC table */
	init_ipc_table();

	/*
	 * Note: RISC-V core boots automatically from embedded firmware.
	 * The CMake build system embeds the RISC-V binary in the ARM ELF's
	 * .riscv_flash section, and the hardware boots it automatically.
	 */
	printf("[ARM] RISC-V firmware embedded at _riscv_boot address\r\n");

	/* Initialize IPC for inter-core communication */
	ret = init_ipc();
	if (ret)
		return ret;

	/* LTC4284 is already initialized in common_data.c */
	printf("[ARM] LTC4284 I2C address: 0x%02X\r\n", ltc4284_dev->i2c_addr);

	/* Main monitoring loop */
	printf("\r\n[ARM] Starting monitoring loop...\r\n\r\n");

	uint32_t loop_count = 0;
	while (1) {
		/* Display telemetry every second */
		display_telemetry();

		/* Brief status every 10 seconds */
		if (++loop_count % 10 == 0) {
			printf("[ARM] --- %lu seconds elapsed, %lu total alerts ---\r\n",
			       (unsigned long)(loop_count),
			       (unsigned long)arm_alert_count);
		}

		no_os_mdelay(1000);
	}

	return 0;
}
