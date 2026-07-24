/***************************************************************************//**
 *   @file   maxim_sys_riscv_stubs.c
 *   @brief  Minimal MXC_SYS stubs for RISC-V dual-core builds.
 *   @author Analog Devices Inc.
 *
 * RISC-V firmware runs in a minimal environment where:
 * - Clock configuration is handled by ARM core during boot
 * - RISC-V runs at a fixed clock rate (determined at boot)
 * - Peripheral clocks are already enabled by ARM before RISC-V starts
 *
 * These stubs provide no-op or minimal implementations for SDK functions that
 * would normally be in sys_me15.c, which is incompatible with RISC-V due to
 * missing register definitions in the SDK.
 ******************************************************************************/

#include <stdint.h>
#include "mxc_errors.h"
#include "gcr_regs.h"
#include "mxc_sys.h"

/**
 * @brief Return the RISC-V core clock rate (fixed at boot time)
 *
 * The RISC-V clock is configured by the ARM core before booting the
 * coprocessor. For MAX32690, the RISC-V typically runs at the same
 * frequency as the system clock (100 MHz default).
 *
 * @return RISC-V clock frequency in Hz
 */
uint32_t MXC_SYS_RiscVClockRate(void)
{
	/* MAX32690 RISC-V runs at system clock frequency */
	/* Default: 100 MHz (IPO) */
	/* This could be read from GCR registers if needed */
	return 100000000; /* 100 MHz */
}

/**
 * @brief Enable a peripheral clock (stub)
 *
 * On RISC-V builds, assume all required peripheral clocks are already
 * enabled by the ARM core before the RISC-V boots. This stub does nothing.
 *
 * @param clock Peripheral clock to enable (mxc_sys_periph_clock_t)
 */
void MXC_SYS_ClockEnable(mxc_sys_periph_clock_t clock)
{
	/* No-op: ARM core has already enabled necessary clocks */
	(void)clock;
}

/**
 * @brief Disable a peripheral clock (stub)
 *
 * On RISC-V builds, clock management is handled by the ARM core.
 * Disabling clocks from RISC-V could interfere with ARM operation.
 *
 * @param clock Peripheral clock to disable (mxc_sys_periph_clock_t)
 */
void MXC_SYS_ClockDisable(mxc_sys_periph_clock_t clock)
{
	/* No-op: Don't disable clocks that ARM might be using */
	(void)clock;
}

/**
 * @brief Reset a peripheral (wrapped version with RMW protection)
 *
 * The SDK's MXC_SYS_Reset_Periph implementation uses plain writes to GCR->rst1,
 * which clobbers unrelated bits (SMPHR, SIMO) and can corrupt the hardware
 * semaphore or glitch the JTAG TAP.
 *
 * This wrapped version uses read-modify-write to preserve other bits.
 *
 * @param reset Peripheral reset bit (mxc_sys_reset_t)
 * @return E_NO_ERROR on success, E_BAD_PARAM if invalid
 */
int __wrap_MXC_SYS_Reset_Periph(mxc_sys_reset_t reset)
{
	/* Validate reset index */
	if (reset >= 32) {
		return E_BAD_PARAM;
	}

	/* Read-modify-write to GCR->rst1 to preserve other bits */
	uint32_t mask = (1U << reset);
	MXC_GCR->rst1 |= mask;

	/* Wait for reset to complete */
	while (MXC_GCR->rst1 & mask) {
		/* Spin */
	}

	return E_NO_ERROR;
}
