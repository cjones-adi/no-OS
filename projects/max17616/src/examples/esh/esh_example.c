/***************************************************************************//**
 *   @file   esh_example.c
 *   @brief  ESH example source file for max17616 project.
 *   @author Carlos Jones (carlosjr.jones@analog.com)
********************************************************************************
 * Copyright 2025(c) Analog Devices, Inc.
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
#include "common_data.h"
#include "no_os_delay.h"
#include "no_os_print_log.h"
#include "no_os_esh.h"
#include "max17616.h"
#include "esh_example.h"
#include "shell.h"
#include "printf.h"
#include <stdlib.h>

/* Global device handle */
static struct max17616_dev *max17616_dev;

/**
 * @brief Function pointer type for fault processing
 * @param fault_group - Fault group identifier
 * @param bit - Bit position
 * @return Pointer to fault description string or NULL if not found
 */
typedef const char *(*fault_processor_t)(uint16_t fault_group, uint8_t bit);

/**
 * @brief Process fault bits using a function pointer
 * @param fault_value - 8-bit fault register value
 * @param fault_group - Fault group identifier
 * @param fault_name - Name of the fault type for display
 * @param processor - Function pointer to process individual faults
 */
static void process_fault_bits(uint8_t fault_value, uint16_t fault_group,
			       const char *fault_name,
			       fault_processor_t processor)
{
	const char *fault_desc;

	if (!fault_value)
		return;

	pr_info("%s Faults: 0x%02X\r\n", fault_name, fault_value);
	for (int bit = 0; bit < 8; bit++) {
		if (fault_value & (1 << bit)) {
			fault_desc = processor(fault_group, bit);
			if (fault_desc)
				pr_info("  [%d] %s\r\n", bit, fault_desc);
		}
	}
}

/**
 * @brief Display telemetry data in a formatted way
 * @param telemetry - Telemetry structure to display
 */
static void display_telemetry(struct max17616_telemetry *telemetry)
{
	pr_info("=== MAX17616 Telemetry ===\r\n");

	if (telemetry->valid_mask & NO_OS_BIT(0))
		pr_info("VIN:         %d V\r\n", telemetry->vin);

	if (telemetry->valid_mask & NO_OS_BIT(1))
		pr_info("VOUT:        %d V\r\n", telemetry->vout);

	if (telemetry->valid_mask & NO_OS_BIT(3))
		pr_info("IOUT:        %d A\r\n", telemetry->iout);

	if (telemetry->valid_mask & NO_OS_BIT(4))
		pr_info("Temperature: %d °C\r\n", telemetry->temp1);

	if (telemetry->valid_mask & NO_OS_BIT(5))
		pr_info("Power:       %d W\r\n", telemetry->pout);

	pr_info("\r\n");
}

/**
 * @brief Shell command to read telemetry
 */
static int cmd_telemetry(int argc, char **argv)
{
	struct max17616_telemetry telemetry;
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	ret = max17616_read_telemetry_all(max17616_dev, &telemetry);
	if (ret) {
		pr_err("Failed to read telemetry: %d\r\n", ret);
		return ret;
	}

	display_telemetry(&telemetry);
	return 0;
}

/**
 * @brief Shell command to display fault status
 */
static int cmd_faults(int argc, char **argv)
{
	struct max17616_status status;
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	ret = max17616_read_status(max17616_dev, &status);
	if (ret) {
		pr_err("Failed to read fault status: %d\r\n", ret);
		return ret;
	}

	if (status.word == 0) {
		pr_info("No faults detected.\r\n");
		return 0;
	}

	pr_info("=== FAULT STATUS ===\r\n");
	pr_info("STATUS_WORD: 0x%04X\r\n", status.word);

	/* Check individual fault registers */
	process_fault_bits(status.cml, MAX17616_FAULT_GRP_CML,
			   "CML", max17616_get_fault_description);
	process_fault_bits(status.temperature, MAX17616_FAULT_GRP_TEMPERATURE,
			   "Temperature", max17616_get_fault_description);
	process_fault_bits(status.input, MAX17616_FAULT_GRP_INPUT,
			   "Input", max17616_get_fault_description);
	process_fault_bits(status.iout, MAX17616_FAULT_GRP_IOUT_POUT,
			   "Output Current", max17616_get_fault_description);
	process_fault_bits(status.vout, MAX17616_FAULT_GRP_VOUT,
			   "Output Voltage", max17616_get_fault_description);
	process_fault_bits(status.mfr_specific, MAX17616_FAULT_GRP_MFR_SPECIFIC,
			   "Manufacturer", max17616_get_fault_description);

	return 0;
}

/**
 * @brief Shell command to get/set current limit mode
 */
static int cmd_clmode(int argc, char **argv)
{
	enum max17616_current_limit_mode clmode;
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	if (argc == 1) {
		/* Get current mode */
		ret = max17616_get_current_limit_mode(max17616_dev, &clmode);
		if (ret) {
			pr_err("Failed to get current limit mode: %d\r\n", ret);
			return ret;
		}

		const char *mode_str;
		switch (clmode) {
		case MAX17616_CLMODE_LATCH_OFF:
			mode_str = "Latch-off";
			break;
		case MAX17616_CLMODE_CONTINUOUS:
			mode_str = "Continuous";
			break;
		case MAX17616_CLMODE_AUTO_RETRY:
			mode_str = "Auto-retry";
			break;
		default:
			mode_str = "Unknown";
		}
		pr_info("Current Limit Mode: %s (0x%02X)\r\n", mode_str, (uint8_t)clmode);
	} else if (argc == 2) {
		/* Set mode */
		int mode_val = atoi(argv[1]);
		if (mode_val < 0 || mode_val > 2) {
			pr_err("Invalid mode. Use: 0=Latch-off, 1=Continuous, 2=Auto-retry\r\n");
			return -1;
		}

		clmode = (enum max17616_current_limit_mode)mode_val;
		ret = max17616_set_current_limit_mode(max17616_dev, clmode);
		if (ret) {
			pr_err("Failed to set current limit mode: %d\r\n", ret);
			return ret;
		}

		pr_info("Current limit mode set successfully\r\n");
	} else {
		pr_info("Usage: clmode [mode]\r\n");
		pr_info("  mode: 0=Latch-off, 1=Continuous, 2=Auto-retry\r\n");
		pr_info("  Without arguments, displays current mode\r\n");
	}

	return 0;
}

/**
 * @brief Shell command to get/set current start ratio
 */
static int cmd_istart(int argc, char **argv)
{
	enum max17616_istart_ratio istart_ratio;
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	if (argc == 1) {
		/* Get current ratio */
		ret = max17616_get_istart_ratio(max17616_dev, &istart_ratio);
		if (ret) {
			pr_err("Failed to get current start ratio: %d\r\n", ret);
			return ret;
		}

		const char *ratio_str;
		switch (istart_ratio) {
		case MAX17616_ISTART_FULL:
			ratio_str = "Full (I_limit)";
			break;
		case MAX17616_ISTART_HALF:
			ratio_str = "Half (I_limit/2)";
			break;
		case MAX17616_ISTART_QUARTER:
			ratio_str = "Quarter (I_limit/4)";
			break;
		case MAX17616_ISTART_EIGHTH:
			ratio_str = "Eighth (I_limit/8)";
			break;
		case MAX17616_ISTART_SIXTEENTH:
			ratio_str = "Sixteenth (I_limit/16)";
			break;
		default:
			ratio_str = "Unknown";
		}
		pr_info("Current Start Ratio: %s (0x%02X)\r\n", ratio_str, (uint8_t)istart_ratio);
	} else if (argc == 2) {
		/* Set ratio */
		int ratio_val = atoi(argv[1]);
		if (ratio_val < 0 || ratio_val > 4) {
			pr_err("Invalid ratio. Use: 0=Full, 1=Half, 2=Quarter, 3=Eighth, 4=Sixteenth\r\n");
			return -1;
		}

		istart_ratio = (enum max17616_istart_ratio)ratio_val;
		ret = max17616_set_istart_ratio(max17616_dev, istart_ratio);
		if (ret) {
			pr_err("Failed to set current start ratio: %d\r\n", ret);
			return ret;
		}

		pr_info("Current start ratio set successfully\r\n");
	} else {
		pr_info("Usage: istart [ratio]\r\n");
		pr_info("  ratio: 0=Full, 1=Half, 2=Quarter, 3=Eighth, 4=Sixteenth\r\n");
		pr_info("  Without arguments, displays current ratio\r\n");
	}

	return 0;
}

/**
 * @brief Shell command to get/set overcurrent timeout
 */
static int cmd_timeout(int argc, char **argv)
{
	enum max17616_overcurrent_timeout tstoc;
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	if (argc == 1) {
		/* Get current timeout */
		ret = max17616_get_overcurrent_timeout(max17616_dev, &tstoc);
		if (ret) {
			pr_err("Failed to get overcurrent timeout: %d\r\n", ret);
			return ret;
		}

		const char *timeout_str;
		switch (tstoc) {
		case MAX17616_TIMEOUT_400US:
			timeout_str = "400 microseconds";
			break;
		case MAX17616_TIMEOUT_1MS:
			timeout_str = "1 millisecond";
			break;
		case MAX17616_TIMEOUT_4MS:
			timeout_str = "4 milliseconds";
			break;
		case MAX17616_TIMEOUT_24MS:
			timeout_str = "24 milliseconds";
			break;
		default:
			timeout_str = "Unknown";
		}
		pr_info("Overcurrent Timeout: %s (0x%02X)\r\n", timeout_str, (uint8_t)tstoc);
	} else if (argc == 2) {
		/* Set timeout */
		int timeout_val = atoi(argv[1]);
		if (timeout_val < 0 || timeout_val > 3) {
			pr_err("Invalid timeout. Use: 0=400us, 1=1ms, 2=4ms, 3=24ms\r\n");
			return -1;
		}

		tstoc = (enum max17616_overcurrent_timeout)timeout_val;
		ret = max17616_set_overcurrent_timeout(max17616_dev, tstoc);
		if (ret) {
			pr_err("Failed to set overcurrent timeout: %d\r\n", ret);
			return ret;
		}

		pr_info("Overcurrent timeout set successfully\r\n");
	} else {
		pr_info("Usage: timeout [value]\r\n");
		pr_info("  value: 0=400us, 1=1ms, 2=4ms, 3=24ms\r\n");
		pr_info("  Without arguments, displays current timeout\r\n");
	}

	return 0;
}

/**
 * @brief Shell command to get/set operation state
 */
static int cmd_operation(int argc, char **argv)
{
	bool operation_enabled;
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	if (argc == 1) {
		/* Get current state */
		ret = max17616_get_operation_state(max17616_dev, &operation_enabled);
		if (ret) {
			pr_err("Failed to get operation state: %d\r\n", ret);
			return ret;
		}

		pr_info("Operation State: %s\r\n", operation_enabled ? "ENABLED" : "DISABLED");
	} else if (argc == 2) {
		/* Set state */
		int enable_val = atoi(argv[1]);
		if (enable_val != 0 && enable_val != 1) {
			pr_err("Invalid value. Use: 0=Disable, 1=Enable\r\n");
			return -1;
		}

		operation_enabled = (bool)enable_val;
		ret = max17616_set_operation_state(max17616_dev, operation_enabled);
		if (ret) {
			pr_err("Failed to set operation state: %d\r\n", ret);
			return ret;
		}

		pr_info("Operation state set to %s\r\n", operation_enabled ? "ENABLED" : "DISABLED");
	} else {
		pr_info("Usage: operation [state]\r\n");
		pr_info("  state: 0=Disable, 1=Enable\r\n");
		pr_info("  Without arguments, displays current state\r\n");
	}

	return 0;
}

/**
 * @brief Shell command to display device settings
 */
static int cmd_settings(int argc, char **argv)
{
	enum max17616_current_limit_mode clmode;
	enum max17616_istart_ratio istart_ratio;
	enum max17616_overcurrent_timeout tstoc;
	enum max17616_overcurrent_limit istlim;
	enum max17616_nominal_voltage voltage;
	enum max17616_pgood_threshold threshold;
	bool operation_enabled;
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	pr_info("=== Device Settings ===\r\n");

	ret = max17616_get_current_limit_mode(max17616_dev, &clmode);
	if (ret == 0) {
		const char *mode_str;
		switch (clmode) {
		case MAX17616_CLMODE_LATCH_OFF:
			mode_str = "Latch-off";
			break;
		case MAX17616_CLMODE_CONTINUOUS:
			mode_str = "Continuous";
			break;
		case MAX17616_CLMODE_AUTO_RETRY:
			mode_str = "Auto-retry";
			break;
		default:
			mode_str = "Unknown";
		}
		pr_info("Current Limit Mode: %s (0x%02X)\r\n", mode_str, (uint8_t)clmode);
	}

	ret = max17616_get_istart_ratio(max17616_dev, &istart_ratio);
	if (ret == 0) {
		const char *ratio_str;
		switch (istart_ratio) {
		case MAX17616_ISTART_FULL:
			ratio_str = "Full (I_limit)";
			break;
		case MAX17616_ISTART_HALF:
			ratio_str = "Half (I_limit/2)";
			break;
		case MAX17616_ISTART_QUARTER:
			ratio_str = "Quarter (I_limit/4)";
			break;
		case MAX17616_ISTART_EIGHTH:
			ratio_str = "Eighth (I_limit/8)";
			break;
		case MAX17616_ISTART_SIXTEENTH:
			ratio_str = "Sixteenth (I_limit/16)";
			break;
		default:
			ratio_str = "Unknown";
		}
		pr_info("Current Start Ratio: %s (0x%02X)\r\n", ratio_str, (uint8_t)istart_ratio);
	}

	ret = max17616_get_overcurrent_timeout(max17616_dev, &tstoc);
	if (ret == 0) {
		const char *timeout_str;
		switch (tstoc) {
		case MAX17616_TIMEOUT_400US:
			timeout_str = "400 microseconds";
			break;
		case MAX17616_TIMEOUT_1MS:
			timeout_str = "1 millisecond";
			break;
		case MAX17616_TIMEOUT_4MS:
			timeout_str = "4 milliseconds";
			break;
		case MAX17616_TIMEOUT_24MS:
			timeout_str = "24 milliseconds";
			break;
		default:
			timeout_str = "Unknown";
		}
		pr_info("Overcurrent Timeout: %s (0x%02X)\r\n", timeout_str, (uint8_t)tstoc);
	}

	ret = max17616_get_overcurrent_limit(max17616_dev, &istlim);
	if (ret == 0) {
		const char *limit_str;
		switch (istlim) {
		case MAX17616_OC_LIMIT_1_25:
			limit_str = "1.25:1 ratio";
			break;
		case MAX17616_OC_LIMIT_1_50:
			limit_str = "1.50:1 ratio";
			break;
		case MAX17616_OC_LIMIT_1_75:
			limit_str = "1.75:1 ratio";
			break;
		case MAX17616_OC_LIMIT_2_00:
			limit_str = "2.00:1 ratio";
			break;
		default:
			limit_str = "Unknown";
		}
		pr_info("Overcurrent Limit: %s (0x%02X)\r\n", limit_str, (uint8_t)istlim);
	}

	ret = max17616_get_vout_uv_fault_limit_config(max17616_dev, &voltage, &threshold);
	if (ret == 0) {
		const char *voltage_str, *threshold_str;

		switch (voltage) {
		case MAX17616_NOMINAL_5V:
			voltage_str = "5V";
			break;
		case MAX17616_NOMINAL_9V:
			voltage_str = "9V";
			break;
		case MAX17616_NOMINAL_12V:
			voltage_str = "12V";
			break;
		case MAX17616_NOMINAL_24V:
			voltage_str = "24V";
			break;
		case MAX17616_NOMINAL_36V:
			voltage_str = "36V";
			break;
		case MAX17616_NOMINAL_48V:
			voltage_str = "48V";
			break;
		case MAX17616_NOMINAL_60V:
			voltage_str = "60V";
			break;
		case MAX17616_NOMINAL_72V:
			voltage_str = "72V";
			break;
		default:
			voltage_str = "Unknown";
		}

		switch (threshold) {
		case MAX17616_PGOOD_MINUS_10_PERCENT:
			threshold_str = "-10%";
			break;
		case MAX17616_PGOOD_MINUS_20_PERCENT:
			threshold_str = "-20%";
			break;
		case MAX17616_PGOOD_MINUS_30_PERCENT:
			threshold_str = "-30%";
			break;
		default:
			threshold_str = "Unknown";
		}

		pr_info("VOUT UV Fault Limit: %s nominal, %s PGOOD threshold (0x%02X)\r\n",
			voltage_str, threshold_str, ((uint8_t)voltage << 2) | (uint8_t)threshold);
	}

	ret = max17616_get_operation_state(max17616_dev, &operation_enabled);
	if (ret == 0)
		pr_info("Operation State: %s\r\n", operation_enabled ? "ENABLED" : "DISABLED");

	return 0;
}

/**
 * @brief Shell command to clear faults
 */
static int cmd_clear_faults(int argc, char **argv)
{
	int ret;

	if (!max17616_dev) {
		pr_err("Device not initialized\r\n");
		return -1;
	}

	ret = max17616_clear_faults(max17616_dev);
	if (ret) {
		pr_err("Failed to clear faults: %d\r\n", ret);
		return ret;
	}

	pr_info("Faults cleared successfully\r\n");
	return 0;
}

/* Define shell commands */
ADD_CMD(telemetry, "Read and display device telemetry", cmd_telemetry);
ADD_CMD(faults, "Display fault status", cmd_faults);
ADD_CMD(clmode, "Get/set current limit mode", cmd_clmode);
ADD_CMD(istart, "Get/set current start ratio", cmd_istart);
ADD_CMD(timeout, "Get/set overcurrent timeout", cmd_timeout);
ADD_CMD(operation, "Get/set operation state", cmd_operation);
ADD_CMD(settings, "Display all device settings", cmd_settings);
ADD_CMD(clear, "Clear all faults", cmd_clear_faults);

int example_main(void)
{
	struct no_os_uart_desc *uart_desc;
	int ret;

	ret = no_os_uart_init(&uart_desc, &uart_ip);
	if (ret)
		return ret;

	no_os_uart_stdio(uart_desc);
	pr_info("\e[2J\e[H");
	pr_info("MAX17616 ESH example.\r\n");

	ret = max17616_init(&max17616_dev, &max17616_ip);
	if (ret) {
		pr_err("Failed to initialize MAX17616: %d\r\n", ret);
		return ret;
	}

	pr_info("MAX17616 device initialized successfully.\r\n");
	pr_info("Starting shell interface...\r\n");
	
	/* Setup esh read/write functions */
	initial_setup();
	
	/* Use the built-in esh prompt function */
	prompt();

	/* Should never reach here */
	if (max17616_dev)
		max17616_remove(max17616_dev);

	return 0;
}
