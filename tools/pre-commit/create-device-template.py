#!/usr/bin/env python3
"""
Device Template Generator for no-OS

Creates device driver templates for specific categories like ADC, GPIO, PMBus devices.
Optimized for power management applications and MAX32655/Pi4 platforms.
"""

import os
import sys
import argparse
from datetime import datetime


class DeviceTemplateGenerator:
    def __init__(self):
        self.year = datetime.now().year

    def create_adc_template(self, device_name: str, output_dir: str):
        """Create ADC driver template optimized for power management."""

        device_upper = device_name.upper()
        device_lower = device_name.lower()

        header_content = f'''
/***************************************************************************//**
 *   @file   {device_lower}.h
 *   @brief  Header file of {device_upper} ADC Driver.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright {self.year}(c) Analog Devices, Inc.
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
#ifndef __{device_upper}_H__
#define __{device_upper}_H__

#include <stdint.h>
#include "no_os_spi.h"
#include "no_os_gpio.h"
#include "no_os_util.h"

/******************************************************************************/
/********************** Macros and Constants Definitions ********************/
/******************************************************************************/

/* {device_upper} Register Map */
#define {device_upper}_REG_STATUS           0x00    /**< Status register */
#define {device_upper}_REG_CONFIG           0x01    /**< Configuration register */
#define {device_upper}_REG_DATA             0x02    /**< Data register */
#define {device_upper}_REG_ID               0x03    /**< Device ID register */

/* {device_upper} Status Register Bits */
#define {device_upper}_STATUS_READY_MSK     NO_OS_BIT(7)    /**< Ready bit */
#define {device_upper}_STATUS_ERROR_MSK     NO_OS_BIT(6)    /**< Error bit */

/* {device_upper} Configuration Register Bits */
#define {device_upper}_CONFIG_MODE_MSK      NO_OS_GENMASK(1, 0)    /**< Operating mode */
#define {device_upper}_CONFIG_MODE(x)       no_os_field_prep({device_upper}_CONFIG_MODE_MSK, x)

/* {device_upper} Device ID */
#define {device_upper}_DEVICE_ID            0xAB    /**< Expected device ID */

/* {device_upper} Constants */
#define {device_upper}_RESET_DELAY_MS       10      /**< Reset delay in milliseconds */
#define {device_upper}_CONVERSION_TIME_US   100     /**< Conversion time in microseconds */

/******************************************************************************/
/*************************** Types Declarations *******************************/
/******************************************************************************/

/**
 * @enum {device_lower}_operating_mode
 * @brief {device_upper} operating modes
 */
enum {device_lower}_operating_mode {{
    {device_upper}_MODE_NORMAL = 0,    /**< Normal operation mode */
    {device_upper}_MODE_LOW_POWER,     /**< Low power mode */
    {device_upper}_MODE_HIGH_SPEED,    /**< High speed mode */
    {device_upper}_MODE_SHUTDOWN       /**< Shutdown mode */
}};

/**
 * @struct {device_lower}_dev
 * @brief {device_upper} device driver handler
 */
struct {device_lower}_dev {{
    /** SPI communication interface */
    struct no_os_spi_desc      *spi_desc;
    /** GPIO pins */
    struct no_os_gpio_desc     *gpio_reset;
    struct no_os_gpio_desc     *gpio_convst;
    /** Device configuration */
    enum {device_lower}_operating_mode  mode;
    /** Reference voltage in millivolts */
    uint32_t                    vref_mv;
    /** Resolution in bits */
    uint8_t                     resolution;
}};

/**
 * @struct {device_lower}_init_param
 * @brief {device_upper} initialization parameters
 */
struct {device_lower}_init_param {{
    /** SPI initialization parameters */
    struct no_os_spi_init_param    spi_init;
    /** GPIO initialization parameters */
    struct no_os_gpio_init_param   gpio_reset;
    struct no_os_gpio_init_param   gpio_convst;
    /** Device configuration */
    enum {device_lower}_operating_mode      mode;
    /** Reference voltage in millivolts */
    uint32_t                        vref_mv;
}};

/******************************************************************************/
/************************ Functions Declarations ****************************/
/******************************************************************************/

/**
 * @brief Initialize the {device_upper} device.
 * @param device     - The device structure.
 * @param init_param - The structure that contains the device initial parameters.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_init(struct {device_lower}_dev **device,
                            struct {device_lower}_init_param init_param);

/**
 * @brief Remove the {device_upper} device.
 * @param dev - The device structure.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_remove(struct {device_lower}_dev *dev);

/**
 * @brief Read device register.
 * @param dev      - The device structure.
 * @param reg_addr - Register address.
 * @param reg_data - Pointer to store register data.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_read_register(struct {device_lower}_dev *dev,
                                     uint8_t reg_addr,
                                     uint8_t *reg_data);

/**
 * @brief Write device register.
 * @param dev      - The device structure.
 * @param reg_addr - Register address.
 * @param reg_data - Register data.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_write_register(struct {device_lower}_dev *dev,
                                      uint8_t reg_addr,
                                      uint8_t reg_data);

/**
 * @brief Set operating mode.
 * @param dev  - The device structure.
 * @param mode - Operating mode.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_set_mode(struct {device_lower}_dev *dev,
                                enum {device_lower}_operating_mode mode);

/**
 * @brief Start ADC conversion.
 * @param dev - The device structure.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_start_conversion(struct {device_lower}_dev *dev);

/**
 * @brief Read ADC conversion result.
 * @param dev  - The device structure.
 * @param data - Pointer to store conversion result.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_read_data(struct {device_lower}_dev *dev,
                                 uint16_t *data);

/**
 * @brief Convert raw ADC value to voltage.
 * @param dev      - The device structure.
 * @param raw_data - Raw ADC value.
 * @param voltage  - Pointer to store voltage in millivolts.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_raw_to_voltage(struct {device_lower}_dev *dev,
                                      uint16_t raw_data,
                                      uint32_t *voltage);

/**
 * @brief Get device status.
 * @param dev    - The device structure.
 * @param status - Pointer to store device status.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t {device_lower}_get_status(struct {device_lower}_dev *dev,
                                  uint8_t *status);

#endif /* __{device_upper}_H__ */
'''

        source_content = f'''
/***************************************************************************//**
 *   @file   {device_lower}.c
 *   @brief  Implementation of {device_upper} ADC Driver.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright {self.year}(c) Analog Devices, Inc.
 * [Same license as header file...]
*******************************************************************************/

#include <stdlib.h>
#include <string.h>
#include "{device_lower}.h"
#include "no_os_alloc.h"
#include "no_os_error.h"
#include "no_os_delay.h"

/******************************************************************************/
/************************ Functions Definitions *******************************/
/******************************************************************************/

/**
 * @brief Read device register.
 */
int32_t {device_lower}_read_register(struct {device_lower}_dev *dev,
                                     uint8_t reg_addr,
                                     uint8_t *reg_data)
{{
    int32_t ret;
    uint8_t tx_buf[2] = {{reg_addr | 0x80, 0x00}};  // Read command
    uint8_t rx_buf[2] = {{0}};

    if (!dev || !dev->spi_desc || !reg_data)
        return -EINVAL;

    ret = no_os_spi_write_and_read(dev->spi_desc, tx_buf, sizeof(tx_buf));
    if (ret < 0)
        return ret;

    ret = no_os_spi_write_and_read(dev->spi_desc, rx_buf, sizeof(rx_buf));
    if (ret < 0)
        return ret;

    *reg_data = rx_buf[1];

    return 0;
}}

/**
 * @brief Write device register.
 */
int32_t {device_lower}_write_register(struct {device_lower}_dev *dev,
                                      uint8_t reg_addr,
                                      uint8_t reg_data)
{{
    int32_t ret;
    uint8_t tx_buf[2] = {{reg_addr & 0x7F, reg_data}};  // Write command

    if (!dev || !dev->spi_desc)
        return -EINVAL;

    ret = no_os_spi_write_and_read(dev->spi_desc, tx_buf, sizeof(tx_buf));
    if (ret < 0)
        return ret;

    return 0;
}}

/**
 * @brief Initialize the {device_upper} device.
 */
int32_t {device_lower}_init(struct {device_lower}_dev **device,
                            struct {device_lower}_init_param init_param)
{{
    struct {device_lower}_dev *dev;
    uint8_t device_id;
    int32_t ret;

    if (!device)
        return -EINVAL;

    dev = no_os_calloc(1, sizeof(*dev));
    if (!dev)
        return -ENOMEM;

    /* Initialize SPI communication */
    ret = no_os_spi_init(&dev->spi_desc, &init_param.spi_init);
    if (ret < 0)
        goto error_spi;

    /* Initialize GPIO pins */
    if (init_param.gpio_reset.number != NO_OS_GPIO_UNASSIGNED) {{
        ret = no_os_gpio_init(&dev->gpio_reset, &init_param.gpio_reset);
        if (ret < 0)
            goto error_gpio_reset;

        /* Perform hardware reset */
        ret = no_os_gpio_set_value(dev->gpio_reset, NO_OS_GPIO_LOW);
        if (ret < 0)
            goto error_gpio_convst;

        no_os_mdelay({device_upper}_RESET_DELAY_MS);

        ret = no_os_gpio_set_value(dev->gpio_reset, NO_OS_GPIO_HIGH);
        if (ret < 0)
            goto error_gpio_convst;

        no_os_mdelay({device_upper}_RESET_DELAY_MS);
    }}

    if (init_param.gpio_convst.number != NO_OS_GPIO_UNASSIGNED) {{
        ret = no_os_gpio_init(&dev->gpio_convst, &init_param.gpio_convst);
        if (ret < 0)
            goto error_gpio_convst;
    }}

    /* Store configuration */
    dev->mode = init_param.mode;
    dev->vref_mv = init_param.vref_mv;
    dev->resolution = 16;  // Default resolution, adjust as needed

    /* Verify device ID */
    ret = {device_lower}_read_register(dev, {device_upper}_REG_ID, &device_id);
    if (ret < 0)
        goto error_gpio_convst;

    if (device_id != {device_upper}_DEVICE_ID) {{
        ret = -ENODEV;
        goto error_gpio_convst;
    }}

    /* Configure device */
    ret = {device_lower}_set_mode(dev, dev->mode);
    if (ret < 0)
        goto error_gpio_convst;

    *device = dev;

    return 0;

error_gpio_convst:
    if (dev->gpio_convst)
        no_os_gpio_remove(dev->gpio_convst);
    if (dev->gpio_reset)
        no_os_gpio_remove(dev->gpio_reset);
error_gpio_reset:
    no_os_spi_remove(dev->spi_desc);
error_spi:
    no_os_free(dev);

    return ret;
}}

/**
 * @brief Remove the {device_upper} device.
 */
int32_t {device_lower}_remove(struct {device_lower}_dev *dev)
{{
    if (!dev)
        return -EINVAL;

    if (dev->gpio_convst)
        no_os_gpio_remove(dev->gpio_convst);

    if (dev->gpio_reset)
        no_os_gpio_remove(dev->gpio_reset);

    no_os_spi_remove(dev->spi_desc);
    no_os_free(dev);

    return 0;
}}

/**
 * @brief Set operating mode.
 */
int32_t {device_lower}_set_mode(struct {device_lower}_dev *dev,
                                enum {device_lower}_operating_mode mode)
{{
    int32_t ret;
    uint8_t config_reg;

    if (!dev)
        return -EINVAL;

    ret = {device_lower}_read_register(dev, {device_upper}_REG_CONFIG, &config_reg);
    if (ret < 0)
        return ret;

    config_reg &= ~{device_upper}_CONFIG_MODE_MSK;
    config_reg |= {device_upper}_CONFIG_MODE(mode);

    ret = {device_lower}_write_register(dev, {device_upper}_REG_CONFIG, config_reg);
    if (ret < 0)
        return ret;

    dev->mode = mode;

    return 0;
}}

/**
 * @brief Start ADC conversion.
 */
int32_t {device_lower}_start_conversion(struct {device_lower}_dev *dev)
{{
    int32_t ret;

    if (!dev)
        return -EINVAL;

    /* Use GPIO to trigger conversion if available */
    if (dev->gpio_convst) {{
        ret = no_os_gpio_set_value(dev->gpio_convst, NO_OS_GPIO_HIGH);
        if (ret < 0)
            return ret;

        no_os_udelay(1);  // Brief pulse

        ret = no_os_gpio_set_value(dev->gpio_convst, NO_OS_GPIO_LOW);
        if (ret < 0)
            return ret;
    }} else {{
        /* Software trigger via register write */
        ret = {device_lower}_write_register(dev, {device_upper}_REG_CONFIG, 0x01);
        if (ret < 0)
            return ret;
    }}

    /* Wait for conversion to complete */
    no_os_udelay({device_upper}_CONVERSION_TIME_US);

    return 0;
}}

/**
 * @brief Read ADC conversion result.
 */
int32_t {device_lower}_read_data(struct {device_lower}_dev *dev, uint16_t *data)
{{
    int32_t ret;
    uint8_t data_high, data_low;

    if (!dev || !data)
        return -EINVAL;

    /* Check if conversion is ready */
    uint8_t status;
    ret = {device_lower}_get_status(dev, &status);
    if (ret < 0)
        return ret;

    if (!(status & {device_upper}_STATUS_READY_MSK))
        return -EAGAIN;

    /* Read data registers */
    ret = {device_lower}_read_register(dev, {device_upper}_REG_DATA, &data_high);
    if (ret < 0)
        return ret;

    ret = {device_lower}_read_register(dev, {device_upper}_REG_DATA + 1, &data_low);
    if (ret < 0)
        return ret;

    *data = (uint16_t)((data_high << 8) | data_low);

    return 0;
}}

/**
 * @brief Convert raw ADC value to voltage.
 */
int32_t {device_lower}_raw_to_voltage(struct {device_lower}_dev *dev,
                                      uint16_t raw_data,
                                      uint32_t *voltage)
{{
    if (!dev || !voltage)
        return -EINVAL;

    /* Convert raw data to millivolts */
    *voltage = (uint32_t)(((uint64_t)raw_data * dev->vref_mv) >> dev->resolution);

    return 0;
}}

/**
 * @brief Get device status.
 */
int32_t {device_lower}_get_status(struct {device_lower}_dev *dev, uint8_t *status)
{{
    if (!dev || !status)
        return -EINVAL;

    return {device_lower}_read_register(dev, {device_upper}_REG_STATUS, status);
}}
'''

        # Create directory structure
        driver_dir = os.path.join(output_dir, f"drivers/adc/{device_lower}")
        os.makedirs(driver_dir, exist_ok=True)

        # Write files
        with open(os.path.join(driver_dir, f"{device_lower}.h"), 'w') as f:
            f.write(header_content.strip())

        with open(os.path.join(driver_dir, f"{device_lower}.c"), 'w') as f:
            f.write(source_content.strip())

        return driver_dir

    def create_pmbus_template(self, device_name: str, output_dir: str):
        """Create PMBus device template for power management."""

        device_upper = device_name.upper()
        device_lower = device_name.lower()

        header_content = f'''
/***************************************************************************//**
 *   @file   {device_lower}.h
 *   @brief  Header file of {device_upper} PMBus Driver.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright {self.year}(c) Analog Devices, Inc.
 * [Same license as previous templates...]
*******************************************************************************/
#ifndef __{device_upper}_H__
#define __{device_upper}_H__

#include <stdint.h>
#include "no_os_i2c.h"
#include "no_os_gpio.h"
#include "no_os_util.h"

/******************************************************************************/
/********************** Macros and Constants Definitions ********************/
/******************************************************************************/

/* {device_upper} PMBus Commands */
#define {device_upper}_CMD_PAGE                 0x00    /**< Page select */
#define {device_upper}_CMD_OPERATION           0x01    /**< Operation command */
#define {device_upper}_CMD_ON_OFF_CONFIG       0x02    /**< On/Off configuration */
#define {device_upper}_CMD_CLEAR_FAULTS        0x03    /**< Clear faults */
#define {device_upper}_CMD_WRITE_PROTECT       0x10    /**< Write protect */

/* Voltage Commands */
#define {device_upper}_CMD_VOUT_MODE           0x20    /**< Output voltage mode */
#define {device_upper}_CMD_VOUT_COMMAND        0x21    /**< Output voltage command */
#define {device_upper}_CMD_VOUT_MAX            0x24    /**< Maximum output voltage */
#define {device_upper}_CMD_VOUT_MARGIN_HIGH    0x25    /**< Output voltage margin high */
#define {device_upper}_CMD_VOUT_MARGIN_LOW     0x26    /**< Output voltage margin low */

/* Current Commands */
#define {device_upper}_CMD_IOUT_CAL_GAIN       0x38    /**< Output current calibration gain */
#define {device_upper}_CMD_IOUT_MAX            0x39    /**< Maximum output current */
#define {device_upper}_CMD_IOUT_OC_FAULT_LIMIT 0x46    /**< Output over-current fault limit */

/* Status Commands */
#define {device_upper}_CMD_STATUS_BYTE         0x78    /**< Status byte */
#define {device_upper}_CMD_STATUS_WORD         0x79    /**< Status word */
#define {device_upper}_CMD_STATUS_VOUT         0x7A    /**< Output voltage status */
#define {device_upper}_CMD_STATUS_IOUT         0x7B    /**< Output current status */
#define {device_upper}_CMD_STATUS_INPUT        0x7C    /**< Input status */

/* Telemetry Commands */
#define {device_upper}_CMD_READ_VIN            0x88    /**< Read input voltage */
#define {device_upper}_CMD_READ_VOUT           0x8B    /**< Read output voltage */
#define {device_upper}_CMD_READ_IOUT           0x8C    /**< Read output current */
#define {device_upper}_CMD_READ_TEMPERATURE_1  0x8D    /**< Read temperature 1 */
#define {device_upper}_CMD_READ_DUTY_CYCLE     0x94    /**< Read duty cycle */

/* Device Information */
#define {device_upper}_CMD_PMBUS_REVISION      0x98    /**< PMBus revision */
#define {device_upper}_CMD_MFR_ID              0x99    /**< Manufacturer ID */
#define {device_upper}_CMD_MFR_MODEL           0x9A    /**< Manufacturer model */
#define {device_upper}_CMD_MFR_REVISION        0x9B    /**< Manufacturer revision */

/* {device_upper} Specific Constants */
#define {device_upper}_I2C_ADDRESS            0x10    /**< Default I2C address */
#define {device_upper}_PAGE_COUNT              4       /**< Number of power supply pages */

/* Status Byte Bits */
#define {device_upper}_STATUS_NONE_ABOVE       NO_OS_BIT(0)
#define {device_upper}_STATUS_CML              NO_OS_BIT(1)
#define {device_upper}_STATUS_TEMPERATURE      NO_OS_BIT(2)
#define {device_upper}_STATUS_VIN_UV           NO_OS_BIT(3)
#define {device_upper}_STATUS_IOUT_OC          NO_OS_BIT(4)
#define {device_upper}_STATUS_VOUT_OV          NO_OS_BIT(5)
#define {device_upper}_STATUS_OFF              NO_OS_BIT(6)
#define {device_upper}_STATUS_BUSY             NO_OS_BIT(7)

/******************************************************************************/
/*************************** Types Declarations *******************************/
/******************************************************************************/

/**
 * @enum {device_lower}_page
 * @brief {device_upper} power supply pages
 */
enum {device_lower}_page {{
    {device_upper}_PAGE_0 = 0,
    {device_upper}_PAGE_1,
    {device_upper}_PAGE_2,
    {device_upper}_PAGE_3
}};

/**
 * @struct {device_lower}_telemetry
 * @brief {device_upper} telemetry data
 */
struct {device_lower}_telemetry {{
    uint16_t vin_mv;        /**< Input voltage in millivolts */
    uint16_t vout_mv;       /**< Output voltage in millivolts */
    uint16_t iout_ma;       /**< Output current in milliamps */
    int16_t  temp_mc;       /**< Temperature in millicelsius */
    uint16_t duty_cycle;    /**< PWM duty cycle (0-100%) */
}};

/**
 * @struct {device_lower}_dev
 * @brief {device_upper} device driver handler
 */
struct {device_lower}_dev {{
    /** I2C communication interface */
    struct no_os_i2c_desc      *i2c_desc;
    /** GPIO pins */
    struct no_os_gpio_desc     *gpio_enable;
    struct no_os_gpio_desc     *gpio_alert;
    /** Device configuration */
    uint8_t                     i2c_address;
    enum {device_lower}_page    current_page;
}};

/**
 * @struct {device_lower}_init_param
 * @brief {device_upper} initialization parameters
 */
struct {device_lower}_init_param {{
    /** I2C initialization parameters */
    struct no_os_i2c_init_param    i2c_init;
    /** GPIO initialization parameters */
    struct no_os_gpio_init_param   gpio_enable;
    struct no_os_gpio_init_param   gpio_alert;
    /** Device I2C address */
    uint8_t                         i2c_address;
}};

/******************************************************************************/
/************************ Functions Declarations ****************************/
/******************************************************************************/

/* Core Functions */
int32_t {device_lower}_init(struct {device_lower}_dev **device,
                            struct {device_lower}_init_param init_param);
int32_t {device_lower}_remove(struct {device_lower}_dev *dev);

/* PMBus Communication */
int32_t {device_lower}_read_byte(struct {device_lower}_dev *dev,
                                 uint8_t command,
                                 uint8_t *data);
int32_t {device_lower}_write_byte(struct {device_lower}_dev *dev,
                                  uint8_t command,
                                  uint8_t data);
int32_t {device_lower}_read_word(struct {device_lower}_dev *dev,
                                 uint8_t command,
                                 uint16_t *data);
int32_t {device_lower}_write_word(struct {device_lower}_dev *dev,
                                  uint8_t command,
                                  uint16_t data);

/* Page Management */
int32_t {device_lower}_set_page(struct {device_lower}_dev *dev,
                                enum {device_lower}_page page);
int32_t {device_lower}_get_page(struct {device_lower}_dev *dev,
                                enum {device_lower}_page *page);

/* Power Management */
int32_t {device_lower}_enable_output(struct {device_lower}_dev *dev,
                                     enum {device_lower}_page page,
                                     bool enable);
int32_t {device_lower}_set_vout(struct {device_lower}_dev *dev,
                                enum {device_lower}_page page,
                                uint16_t voltage_mv);
int32_t {device_lower}_get_vout(struct {device_lower}_dev *dev,
                                enum {device_lower}_page page,
                                uint16_t *voltage_mv);

/* Status and Monitoring */
int32_t {device_lower}_get_status(struct {device_lower}_dev *dev,
                                  uint8_t *status);
int32_t {device_lower}_clear_faults(struct {device_lower}_dev *dev);
int32_t {device_lower}_get_telemetry(struct {device_lower}_dev *dev,
                                     enum {device_lower}_page page,
                                     struct {device_lower}_telemetry *telemetry);

/* Utility Functions */
int32_t {device_lower}_linear_to_voltage(uint16_t linear_data,
                                         int8_t vout_mode,
                                         uint16_t *voltage_mv);
int32_t {device_lower}_voltage_to_linear(uint16_t voltage_mv,
                                         int8_t vout_mode,
                                         uint16_t *linear_data);

#endif /* __{device_upper}_H__ */
'''

        # Create directory and write header file
        driver_dir = os.path.join(output_dir, f"drivers/power/{device_lower}")
        os.makedirs(driver_dir, exist_ok=True)

        with open(os.path.join(driver_dir, f"{device_lower}.h"), 'w') as f:
            f.write(header_content.strip())

        print(f"✅ PMBus template created at: {driver_dir}")
        return driver_dir

    def create_project_template(self, device_name: str, device_type: str, output_dir: str):
        """Create project template for MAX32655/Pi4 platforms."""

        device_lower = device_name.lower()
        device_upper = device_name.upper()

        # Create basic project structure
        project_dir = os.path.join(output_dir, f"projects/{device_lower}-eval")
        src_dir = os.path.join(project_dir, "src")

        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(os.path.join(src_dir, "platform/maxim"), exist_ok=True)
        os.makedirs(os.path.join(src_dir, "platform/linux"), exist_ok=True)

        # Create src.mk
        src_mk_content = f'''################################################################################
#									       #
#     Shared variables:							       #
#	- PROJECT							       #
#	- DRIVERS							       #
#	- INCLUDE							       #
#	- PLATFORM_DRIVERS						       #
#	- NO-OS								       #
#									       #
################################################################################

SRCS += $(PROJECT)/src/{device_lower}_eval.c
SRCS += $(DRIVERS)/api/no_os_spi.c \\
	$(DRIVERS)/api/no_os_i2c.c \\
	$(DRIVERS)/api/no_os_gpio.c \\
	$(DRIVERS)/api/no_os_uart.c \\
	$(DRIVERS)/{device_type}/{device_lower}/{device_lower}.c \\
	$(NO-OS)/util/no_os_util.c \\
	$(NO-OS)/util/no_os_alloc.c \\
	$(NO-OS)/util/no_os_mutex.c

# Platform-specific sources (automatically selected)
SRCS +=	$(PLATFORM_DRIVERS)/$(PLATFORM)_spi.c \\
	$(PLATFORM_DRIVERS)/$(PLATFORM)_i2c.c \\
	$(PLATFORM_DRIVERS)/$(PLATFORM)_gpio.c \\
	$(PLATFORM_DRIVERS)/$(PLATFORM)_delay.c \\
	$(PLATFORM_DRIVERS)/$(PLATFORM)_uart.c

INCS += $(PROJECT)/src/parameters.h
INCS += $(DRIVERS)/{device_type}/{device_lower}/{device_lower}.h

# Platform headers
INCS +=	$(PLATFORM_DRIVERS)/$(PLATFORM)_spi.h \\
	$(PLATFORM_DRIVERS)/$(PLATFORM)_i2c.h \\
	$(PLATFORM_DRIVERS)/$(PLATFORM)_gpio.h \\
	$(PLATFORM_DRIVERS)/$(PLATFORM)_uart.h

# no-OS headers
INCS +=	$(INCLUDE)/no_os_spi.h \\
	$(INCLUDE)/no_os_i2c.h \\
	$(INCLUDE)/no_os_gpio.h \\
	$(INCLUDE)/no_os_uart.h \\
	$(INCLUDE)/no_os_error.h \\
	$(INCLUDE)/no_os_delay.h \\
	$(INCLUDE)/no_os_util.h \\
	$(INCLUDE)/no_os_alloc.h \\
	$(INCLUDE)/no_os_mutex.h

# IIO support for Linux platform
ifeq ($(PLATFORM),linux)
SRCS += $(DRIVERS)/api/no_os_irq.c \\
	$(NO-OS)/iio/iio.c \\
	$(NO-OS)/iio/iio_app.c \\
	$(PROJECT)/src/iio_{device_lower}.c

INCS += $(INCLUDE)/no_os_irq.h \\
	$(INCLUDE)/iio/iio.h \\
	$(INCLUDE)/iio/iio_app.h \\
	$(PROJECT)/src/iio_{device_lower}.h
endif
'''

        # Create main application file
        main_content = f'''
/***************************************************************************//**
 *   @file   {device_lower}_eval.c
 *   @brief  {device_upper} evaluation application.
 *   @author Your Name (your.email@analog.com)
********************************************************************************
 * Copyright {self.year}(c) Analog Devices, Inc.
 * [Same license...]
*******************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include "parameters.h"
#include "{device_lower}.h"
#include "no_os_error.h"
#include "no_os_delay.h"
#include "no_os_uart.h"

#ifdef IIO_SUPPORT
#include "iio_{device_lower}.h"
#include "iio/iio_app.h"
#endif

/******************************************************************************/
/************************ Variables Declarations *****************************/
/******************************************************************************/

struct {device_lower}_dev *{device_lower}_device;

/******************************************************************************/
/************************ Functions Definitions *******************************/
/******************************************************************************/

/**
 * @brief Basic example for {device_upper} device.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t basic_example(void)
{{
    int32_t ret;
    struct {device_lower}_init_param init_param = {device_lower}_default_init_param;

    printf("\\n{device_upper} Basic Example\\n");

    /* Initialize device */
    ret = {device_lower}_init(&{device_lower}_device, init_param);
    if (ret < 0) {{
        printf("ERROR: {device_lower}_init failed (%d)\\n", ret);
        return ret;
    }}

    printf("{device_upper} device initialized successfully\\n");

    /* Device-specific example operations */
    // TODO: Add device-specific example code here

    printf("{device_upper} basic example completed\\n");

    return 0;
}}

#ifdef IIO_SUPPORT
/**
 * @brief IIO example for {device_upper} device.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t iio_example(void)
{{
    int32_t ret;
    struct iio_app_desc *app;
    struct iio_app_init_param app_init_param = {{ 0 }};

    printf("\\n{device_upper} IIO Example\\n");

    /* Initialize IIO application */
    ret = iio_app_init(&app, app_init_param);
    if (ret < 0) {{
        printf("ERROR: iio_app_init failed (%d)\\n", ret);
        return ret;
    }}

    /* Add {device_upper} IIO device */
    ret = iio_{device_lower}_init(&iio_{device_lower}_desc, &iio_{device_lower}_init_param);
    if (ret < 0) {{
        printf("ERROR: iio_{device_lower}_init failed (%d)\\n", ret);
        iio_app_remove(app);
        return ret;
    }}

    printf("{device_upper} IIO device initialized\\n");

    /* Run IIO application */
    ret = iio_app_run(app);

    /* Cleanup */
    iio_{device_lower}_remove(iio_{device_lower}_desc);
    iio_app_remove(app);

    return ret;
}}
#endif

/**
 * @brief Main application function.
 * @return 0 in case of success, negative error code otherwise.
 */
int32_t main(void)
{{
    int32_t ret;

#ifdef IIO_SUPPORT
    ret = iio_example();
#else
    ret = basic_example();
#endif

    if ({device_lower}_device)
        {device_lower}_remove({device_lower}_device);

    if (ret < 0)
        printf("ERROR: Application failed (%d)\\n", ret);
    else
        printf("Application completed successfully\\n");

    return ret;
}}
'''

        # Write files
        with open(os.path.join(project_dir, "src.mk"), 'w') as f:
            f.write(src_mk_content.strip())

        with open(os.path.join(src_dir, f"{device_lower}_eval.c"), 'w') as f:
            f.write(main_content.strip())

        print(f"✅ Project template created at: {project_dir}")
        return project_dir


def main():
    parser = argparse.ArgumentParser(description='Generate no-OS device driver templates')
    parser.add_argument('device_name', help='Device name (e.g., ad7980, adm1266)')
    parser.add_argument('device_type', choices=['adc', 'pmbus', 'gpio', 'power'],
                       help='Device type')
    parser.add_argument('--output', '-o', default='.',
                       help='Output directory (default: current directory)')
    parser.add_argument('--with-project', action='store_true',
                       help='Also create project template')

    args = parser.parse_args()

    generator = DeviceTemplateGenerator()

    try:
        print(f"🚀 Creating {args.device_type.upper()} driver template for {args.device_name}...")

        if args.device_type == 'adc':
            driver_dir = generator.create_adc_template(args.device_name, args.output)
        elif args.device_type == 'pmbus':
            driver_dir = generator.create_pmbus_template(args.device_name, args.output)
        else:
            print(f"❌ Template for {args.device_type} not yet implemented")
            sys.exit(1)

        print(f"✅ Driver template created: {driver_dir}")

        if args.with_project:
            project_dir = generator.create_project_template(args.device_name, args.device_type, args.output)
            print(f"✅ Project template created: {project_dir}")

        print(f"\\n📋 Next steps:")
        print(f"1. Customize the templates for your specific device")
        print(f"2. Update register definitions and device constants")
        print(f"3. Implement device-specific functionality")
        print(f"4. Test with hardware")
        print(f"5. Run pre-commit checks: ./tools/pre-commit/install-hooks.sh")

    except Exception as e:
        print(f"❌ Error creating template: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()