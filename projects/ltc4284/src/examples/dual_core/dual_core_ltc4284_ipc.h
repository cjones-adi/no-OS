/***************************************************************************//**
 *   @file   dual_core_ltc4284_ipc.h
 *   @brief  Shared IPC definitions for LTC4284 dual-core example.
 *   @author Analog Devices Inc.
 *
 * This header defines the shared memory structure and constants used for
 * inter-processor communication between ARM (CPU0) and RISC-V (CPU1) cores
 * in the LTC4284 dual-core monitoring example.
 *
 * Both ARM and RISC-V source files include this header to ensure consistent
 * IPC table layout and magic values.
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

#ifndef _DUAL_CORE_LTC4284_IPC_H_
#define _DUAL_CORE_LTC4284_IPC_H_

#include <stdint.h>

/**
 * LTC4284 IPC shared memory address
 *
 * Located in RISC-V SRAM region (0x20100000-0x20120000) to ensure both cores
 * can access it. The ARM core can read/write anywhere, while the RISC-V core
 * has restricted access to only its dedicated SRAM.
 */
#define LTC4284_IPC_TABLE_ADDR  0x20110000UL

/**
 * Magic value to validate IPC table initialization
 */
#define LTC4284_IPC_MAGIC       0xC0DEC0DEUL

/**
 * Shared IPC table structure
 *
 * This structure resides in shared memory accessible by both ARM and RISC-V.
 * The ARM core initializes it, and both cores read/write fields with proper
 * memory barriers.
 */
typedef struct {
	/** Magic value (LTC4284_IPC_MAGIC when initialized) */
	uint32_t magic;

	/** Overcurrent alert counter (written by RISC-V, read by ARM) */
	volatile uint32_t alert_count;

	/** Timestamp of last alert in milliseconds (written by RISC-V) */
	volatile uint32_t last_alert_ms;

	/** Reserved for future use (align to cache line) */
	uint32_t reserved[13];
} ltc4284_ipc_table_t;

#endif /* _DUAL_CORE_LTC4284_IPC_H_ */
