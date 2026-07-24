/***************************************************************************//**
 *   @file   dual_core_example_riscv.c
 *   @brief  RISC-V RV32 (CPU1) side of LTC4284 dual-core monitoring example.
 *   @author Analog Devices Inc.
 *
 * This is the freestanding RISC-V firmware that monitors the LTC4284 ALERT pin
 * in real-time and notifies the ARM core via IPC when overcurrent events occur.
 *
 * RISC-V responsibilities:
 * - Configure GPIO interrupt on LTC4284 ALERT pin (P0.19)
 * - Detect rising edge (overcurrent event)
 * - Increment shared memory alert counter
 * - Ring ARM doorbell via IPC
 * - Minimal latency for hardware protection
 *
 * This firmware runs from flash (no SRAM copy) and uses only the RISC-V-
 * dedicated SRAM region (0x20100000-0x20120000). It cannot link the full no-OS
 * runtime, so it uses:
 * - Direct SEMA register access for IPC (maxim_ipc_raw_* helpers)
 * - Minimal MXC GPIO driver
 * - No malloc, no printf (ARM handles console output)
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

#include <stdint.h>
#include <stdbool.h>
#include <errno.h>
#include "mxc_device.h"
#include "gpio.h"
#include "maxim_ipc.h"
#include "maxim_riscv_compat.h"
#include "no_os_i2c.h"
#include "no_os_delay.h"
#include "ltc4284.h"
#include "maxim_i2c.h"
#include "dual_core_ltc4284_ipc.h"

/* Pointer to shared IPC memory */
static volatile ltc4284_ipc_table_t *const g_ipc_table =
	(volatile ltc4284_ipc_table_t *)LTC4284_IPC_TABLE_ADDR;

/* LTC4284 device descriptor */
static struct ltc4284_dev *ltc4284_dev = NULL;

/* I2C initialization for RISC-V */
static struct max_i2c_init_param i2c_extra = {
	.vssel = MXC_GPIO_VSSEL_VDDIO
};

static struct no_os_i2c_init_param i2c_ip = {
	.device_id = 1,              /* I2C1 bus */
	.max_speed_hz = 400000,      /* 400 kHz */
	.slave_address = 0x16,       /* LTC4284_I2C_ADDR_6 */
	.platform_ops = &max_i2c_ops,
	.extra = &i2c_extra
};

static struct ltc4284_init_param ltc4284_ip = {
	.i2c_init      = &i2c_ip,
	.rsense_uohm   = 312,        /* 312 µΩ (DC2470A) */
	.vpwr_divider  = 40,         /* 40:1 divider */
	.drain_divider = 40,         /* 40:1 divider */
	.vsense_mv     = 18,         /* 18 mV limit */
	.alert_gpio    = NULL
};

/* LTC4284 ALERT pin: P0.19 (GPIO0, pin 19) */
#define ALERT_GPIO_PORT     MXC_GPIO0
#define ALERT_GPIO_PIN      MXC_GPIO_PIN_19

/* Local alert counter */
static volatile uint32_t local_alert_count = 0;

/**
 * @brief GPIO interrupt handler for LTC4284 ALERT pin
 */
void GPIO0_IRQHandler(void)
{
	/* Check if our pin triggered the interrupt */
	if (MXC_GPIO_GetFlags(ALERT_GPIO_PORT) & ALERT_GPIO_PIN) {
		/* Clear the interrupt flag */
		MXC_GPIO_ClearFlags(ALERT_GPIO_PORT, ALERT_GPIO_PIN);

		/* Increment local counter */
		local_alert_count++;

		/* Update shared memory */
		g_ipc_table->alert_count = local_alert_count;
		g_ipc_table->last_alert_ms = 0;

		/* Set alert status flag */
		g_ipc_table->status |= LTC4284_STATUS_ALERT;

		/* Notify ARM via IPC doorbell */
		maxim_ipc_raw_ring_host();
	}
}

/**
 * @brief Process IPC command from ARM
 */
static void process_command(void)
{
	volatile ltc4284_ipc_table_t *tbl = g_ipc_table;
	int ret = 0;
	/* Temporary non-volatile variables for API calls */
	uint32_t vin_mv, iin_ma, pin_mw, vout_mv;
	uint8_t status_reg, fault_reg;
	uint64_t energy_mj;

	tbl->status |= LTC4284_STATUS_BUSY;

	uint32_t opcode = tbl->cmd_opcode;
	uint32_t param1 = tbl->cmd_param1;

	switch (opcode) {
	case LTC4284_CMD_READ_TELEMETRY:
		/* Read into temporary variables, then copy to volatile shared memory */
		ret = ltc4284_read_vin(ltc4284_dev, &vin_mv);
		if (!ret) ret = ltc4284_read_iin(ltc4284_dev, &iin_ma);
		if (!ret) ret = ltc4284_read_power(ltc4284_dev, &pin_mw);
		if (!ret) ret = ltc4284_read_vout(ltc4284_dev, &vout_mv);
		if (!ret) ret = ltc4284_read_status(ltc4284_dev, &status_reg);
		if (!ret) ret = ltc4284_get_fault(ltc4284_dev, &fault_reg);
		if (!ret) ret = ltc4284_read_energy(ltc4284_dev, &energy_mj);
		/* Copy to shared memory */
		if (!ret) {
			tbl->telemetry.vin_mv = vin_mv;
			tbl->telemetry.iin_ma = iin_ma;
			tbl->telemetry.pin_mw = pin_mw;
			tbl->telemetry.vout_mv = vout_mv;
			tbl->telemetry.status_reg = status_reg;
			tbl->telemetry.fault_reg = fault_reg;
			tbl->telemetry.energy_mj = energy_mj;
		}
		break;

	case LTC4284_CMD_CLEAR_FAULTS:
		ret = ltc4284_clear_faults(ltc4284_dev);
		break;

	case LTC4284_CMD_ENABLE_FET:
		ret = ltc4284_enable_fet(ltc4284_dev, (bool)param1);
		break;

	case LTC4284_CMD_NOP:
		break;

	default:
		ret = -1;
		break;
	}

	/* Update statistics */
	tbl->total_commands++;
	if (ret) {
		tbl->failed_commands++;
		if (ret == -EIO)
			tbl->i2c_errors++;
	}

	/* Write response */
	tbl->rsp_error_code = (ret == 0) ? 0 : (uint32_t)(-ret);
	tbl->rsp_sequence = tbl->cmd_sequence;

	tbl->status &= ~LTC4284_STATUS_BUSY;
	if (ret)
		tbl->status |= LTC4284_STATUS_ERROR;
	else
		tbl->status &= ~LTC4284_STATUS_ERROR;
}

/**
 * @brief SEMA interrupt - ARM doorbell
 */
void SEMA_IRQHandler(void)
{
	if (maxim_ipc_raw_pending_coproc()) {
		maxim_ipc_raw_ack_coproc();
		process_command();
		maxim_ipc_raw_ring_host();
	}
}

/**
 * @brief Configure GPIO interrupt for ALERT pin
 */
static void init_alert_gpio(void)
{
	mxc_gpio_cfg_t gpio_cfg = {
		.port = ALERT_GPIO_PORT,
		.mask = ALERT_GPIO_PIN,
		.func = MXC_GPIO_FUNC_IN,
		.pad  = MXC_GPIO_PAD_PULL_UP,
		.vssel = MXC_GPIO_VSSEL_VDDIO
	};

	/* Configure pin as input with pull-up */
	MXC_GPIO_Config(&gpio_cfg);

	/* Configure interrupt: rising edge (overcurrent assertion) */
	MXC_GPIO_RegisterCallback(&gpio_cfg, NULL, NULL);
	MXC_GPIO_IntConfig(&gpio_cfg, MXC_GPIO_INT_RISING);
	MXC_GPIO_EnableInt(ALERT_GPIO_PORT, ALERT_GPIO_PIN);

	/* Enable GPIO0 interrupt in RISC-V PLIC */
	NVIC_EnableIRQ(GPIO0_IRQn);
}

/**
 * @brief Wait for shared IPC table to be initialized by ARM
 */
static void wait_for_ipc_table(void)
{
	/* Poll until ARM sets the magic value */
	while (g_ipc_table->magic != LTC4284_IPC_MAGIC) {
		/* Spin-wait */
		for (volatile int i = 0; i < 1000; i++);
	}
}

/**
 * @brief RISC-V main entry point
 */
int main(void)
{
	int ret;

	/* Wait for ARM to initialize the IPC table */
	wait_for_ipc_table();

	/* Initialize LTC4284 on I2C1 */
	ret = ltc4284_init(&ltc4284_dev, &ltc4284_ip);
	if (ret) {
		g_ipc_table->status = LTC4284_STATUS_ERROR;
		g_ipc_table->rsp_error_code = (uint32_t)(-ret);
		maxim_ipc_raw_ring_host();
		while (1) __WFI();
	}

	/* Clear faults and enable FET */
	ltc4284_clear_faults(ltc4284_dev);
	ltc4284_enable_fet(ltc4284_dev, true);

	/* Initialize ALERT GPIO interrupt */
	init_alert_gpio();

	/* Enable SEMA interrupt for IPC */
	NVIC_EnableIRQ(SEMA_IRQn);
	__enable_irq();

	/* Signal ready to ARM */
	g_ipc_table->status = LTC4284_STATUS_READY;
	maxim_ipc_raw_ring_host();

	/* Main loop: sleep and wait for interrupts */
	while (1) {
		__WFI();
	}

	return 0;
}
