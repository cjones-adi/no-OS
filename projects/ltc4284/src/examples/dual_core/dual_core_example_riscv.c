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
#include "mxc_device.h"
#include "gpio.h"
#include "maxim_ipc.h"

/* Shared IPC memory (must match ARM definition) */
#define IPC_TABLE_ADDR 0x20110000UL
#define LTC4284_IPC_MAGIC 0xC0DEC0DEUL

typedef struct {
	uint32_t magic;
	volatile uint32_t alert_count;
	volatile uint32_t last_alert_ms;
	uint32_t reserved[13];
} ltc4284_ipc_table_t;

static volatile ltc4284_ipc_table_t *const g_ipc_table =
	(volatile ltc4284_ipc_table_t *)IPC_TABLE_ADDR;

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
		g_ipc_table->last_alert_ms = 0;  /* Could add real timer here */

		/* Notify ARM via IPC doorbell */
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
	/* Wait for ARM to initialize the IPC table */
	wait_for_ipc_table();

	/* Initialize GPIO interrupt for ALERT monitoring */
	init_alert_gpio();

	/* Enable global interrupts */
	__enable_irq();

	/* Notify ARM that RISC-V is ready */
	maxim_ipc_raw_ring_host();

	/* Main loop: sleep and wait for interrupts */
	while (1) {
		__WFI();  /* Wait For Interrupt */
	}

	return 0;
}
