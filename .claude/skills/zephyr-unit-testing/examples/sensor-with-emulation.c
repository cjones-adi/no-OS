/**
 * Complete example: Sensor driver tests with I2C emulation
 *
 * This example demonstrates:
 * - Test fixture usage with static allocation
 * - ZTEST_F() for tests needing fixture access
 * - I2C emulation setup
 * - Test organization across multiple suites
 * - Before/after hooks for test isolation
 *
 * Directory structure:
 * tests/drivers/sensor/mysensor/
 * ├── src/
 * │   ├── main.c                  # This file
 * │   ├── test_init.c            # Initialization tests
 * │   ├── test_sample.c          # Sample/channel tests
 * │   └── test_mysensor.h        # Shared header
 * ├── boards/
 * │   └── emulated.overlay       # Devicetree overlay
 * ├── CMakeLists.txt
 * ├── testcase.yaml
 * └── prj.conf
 */

#include <zephyr/ztest.h>
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>

/* Shared header with fixture definitions */
#include "test_mysensor.h"

/*******************************************************************************
 * Test Fixtures
 ******************************************************************************/

/* Static fixture instance - avoids k_malloc() dependency */
static struct mysensor_fixture fixture_inst;

/**
 * Setup - Called once before test suite runs
 *
 * Use for:
 * - Device initialization
 * - Resource allocation
 * - Checking device ready state
 */
static void *mysensor_setup(void)
{
    fixture_inst.dev = DEVICE_DT_GET(DT_NODELABEL(mysensor));

    /* Use zassume for setup - skips entire suite if fails */
    zassume_not_null(fixture_inst.dev, "Device binding not found");
    zassume_true(device_is_ready(fixture_inst.dev), "Device not ready");

    return &fixture_inst;
}

/**
 * Before - Called before EACH test
 *
 * Use for:
 * - Resetting device to known state
 * - Clearing registers
 * - Reinitializing per-test resources
 */
static void mysensor_before(void *f)
{
    struct mysensor_fixture *fixture = f;

    /* Reset sensor to default configuration */
    struct sensor_value default_odr = { .val1 = 100, .val2 = 0 };
    sensor_attr_set(fixture->dev, SENSOR_CHAN_ALL,
                    SENSOR_ATTR_SAMPLING_FREQUENCY, &default_odr);
}

/**
 * After - Called after EACH test (optional)
 *
 * Use for:
 * - Per-test cleanup
 * - Disabling interrupts
 */
static void mysensor_after(void *f)
{
    /* Optional cleanup */
}

/**
 * Teardown - Called once after all tests (optional)
 *
 * Use for:
 * - Freeing global resources
 * - Power down devices
 */
static void mysensor_teardown(void *f)
{
    /* Optional global cleanup */
}

/*******************************************************************************
 * Test Suite Definitions
 ******************************************************************************/

/* Initialization tests - verify device ready and state */
ZTEST_SUITE(mysensor_init,      /* Suite name */
            NULL,                /* Predicate (NULL = always run) */
            mysensor_setup,      /* Setup (once before) */
            mysensor_before,     /* Before (each test) */
            mysensor_after,      /* After (each test) */
            mysensor_teardown);  /* Teardown (once after) */

/* Sample and channel tests - verify data acquisition */
ZTEST_SUITE(mysensor_sample, NULL, mysensor_setup, mysensor_before,
            mysensor_after, mysensor_teardown);

/* Attribute tests - verify configuration */
ZTEST_SUITE(mysensor_attr, NULL, mysensor_setup, mysensor_before,
            mysensor_after, mysensor_teardown);

/* Error handling tests - verify robustness */
ZTEST_SUITE(mysensor_error, NULL, mysensor_setup, mysensor_before,
            mysensor_after, mysensor_teardown);

/*******************************************************************************
 * Example Test Cases (in separate files in real project)
 ******************************************************************************/

/* Example from test_init.c */
ZTEST_F(mysensor_init, test_device_ready)
{
    /* Fixture available via 'fixture' pointer */
    zassert_not_null(fixture->dev, "Device structure is NULL");
    zassert_true(device_is_ready(fixture->dev), "Device not ready");
}

/* Example from test_sample.c */
ZTEST_F(mysensor_sample, test_sample_fetch)
{
    int ret = sensor_sample_fetch(fixture->dev);
    zassert_ok(ret, "Sample fetch failed: %d", ret);
}

ZTEST_F(mysensor_sample, test_channel_get_accel_x)
{
    struct sensor_value accel;
    int ret;

    /* Fetch sample first */
    ret = sensor_sample_fetch(fixture->dev);
    zassert_ok(ret, "Sample fetch failed");

    /* Read X channel */
    ret = sensor_channel_get(fixture->dev, SENSOR_CHAN_ACCEL_X, &accel);
    zassert_ok(ret, "Failed to get X channel");

    TC_PRINT("Accel X: %d.%06d m/s²\n", accel.val1, accel.val2);
}

/* Example from test_attr.c */
ZTEST_F(mysensor_attr, test_set_odr_200hz)
{
    struct sensor_value odr;
    int ret;

    /* Set ODR to 200 Hz */
    odr.val1 = 200;
    odr.val2 = 0;
    ret = sensor_attr_set(fixture->dev, SENSOR_CHAN_ACCEL_XYZ,
                          SENSOR_ATTR_SAMPLING_FREQUENCY, &odr);
    zassert_ok(ret, "Failed to set ODR to 200Hz");
}

/* Example from test_error.c */
ZTEST_F(mysensor_error, test_null_device_handling)
{
    struct sensor_value val;
    int ret;

    /* Test NULL device pointer */
    ret = sensor_sample_fetch(NULL);
    zassert_equal(ret, -EINVAL, "Should reject NULL device");

    ret = sensor_channel_get(NULL, SENSOR_CHAN_ACCEL_X, &val);
    zassert_equal(ret, -EINVAL, "Should reject NULL device");
}

ZTEST_F(mysensor_error, test_unsupported_channel)
{
    struct sensor_value val;
    int ret;

    /* Accelerometer doesn't support temperature */
    ret = sensor_sample_fetch(fixture->dev);
    zassert_ok(ret, "Sample fetch failed");

    ret = sensor_channel_get(fixture->dev, SENSOR_CHAN_AMBIENT_TEMP, &val);
    zassert_not_equal(ret, 0, "Should fail for unsupported channel");
}
