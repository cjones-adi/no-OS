## Debugging Tips

### 1. Check Device Tree Structure

Verify parent-child relationship in devicetree:

```bash
# Generate and inspect devicetree
west build -t devicetree

# Check build/zephyr/zephyr.dts for structure:
#   parent {
#       child1 { };
#       child2 { };
#   };
```

**Common issue:** Child not nested under parent – `DT_INST_PARENT()` will fail.

### 2. Verify Init Order

Add logging to parent and child init functions:

```c
static int mfd_xxx_init(const struct device *dev)
{
	LOG_INF("MFD parent init: %s", dev->name);
	// ...
}

static int dac_xxx_init(const struct device *dev)
{
	LOG_INF("DAC child init: %s", dev->name);
	// ...
}
```

**Expected order:** Parent init before any child init.

**Fix if wrong:** Check init priorities, ensure children use `CONFIG_MFD_INIT_PRIORITY` or later.

### 3. Enable MFD and Child Logging

```conf
# prj.conf
CONFIG_LOG=y
CONFIG_MFD_LOG_LEVEL_DBG=y
CONFIG_DAC_LOG_LEVEL_DBG=y
CONFIG_ADC_LOG_LEVEL_DBG=y
CONFIG_GPIO_LOG_LEVEL_DBG=y
```

### 4. Check Parent Device Ready

Children should log if parent not ready:

```c
if (!device_is_ready(config->mfd_dev)) {
	LOG_ERR("Parent device %s not ready", config->mfd_dev->name);
	return -ENODEV;
}
```

**Common causes:**
- Parent init failed
- Parent devicetree status not "okay"
- Parent compatible missing from build

### 5. Verify Bus Communication

Add logging in bus-specific implementations:

```c
static int mfd_xxx_i2c_write_reg(const struct device *dev, uint8_t reg, uint16_t val)
{
	LOG_DBG("I2C write: reg=0x%02x, val=0x%04x", reg, val);

	int ret = i2c_write_dt(...);
	if (ret < 0) {
		LOG_ERR("I2C write failed: %d", ret);
	}
	return ret;
}
```

**Check:**
- Correct I2C/SPI bus enabled
- Correct bus address/CS pin
- Bus speed within device limits

### 6. Check Transfer Function Initialization

Ensure transfer function pointer is set:

```c
int mfd_xxx_write_reg(const struct device *dev, uint8_t reg, uint16_t val)
{
	struct mfd_xxx_data *data = dev->data;

	if (data->transfer_function == NULL) {
		LOG_ERR("Transfer function not initialized!");
		return -ENODEV;
	}

	return data->transfer_function->write_reg(dev, reg, val);
}
```

**Common cause:** Bus init function not called or failed.

### 7. Use Logic Analyzer or Oscilloscope

Capture bus traffic to verify:
- Correct register addresses
- Correct data values
- Correct byte order (endianness)
- Bus timing (clock speed, setup/hold times)

### 8. Test Parent Alone First

Temporarily disable children in devicetree, test parent init and basic register access:

```dts
ad559x: ad559x@13 {
	compatible = "adi,ad559x";
	status = "okay";

	// Comment out children initially
	// dac-controller { ... };
	// adc-controller { ... };
};
```

Add test code in parent init:

```c
static int mfd_xxx_init(const struct device *dev)
{
	int ret;

	// Normal init...

	// Test register access
	uint16_t device_id;
	ret = mfd_xxx_read_reg(dev, DEVICE_ID_REG, 0, &device_id);
	if (ret == 0) {
		LOG_INF("Device ID: 0x%04x", device_id);
	} else {
		LOG_ERR("Failed to read device ID: %d", ret);
	}

	return ret;
}
```

### 9. Check Devicetree Macro Expansion

Verify `DT_INST_PARENT()` expands correctly:

```c
// In child driver, temporarily add:
#pragma message "Parent node: " DT_NODE_PATH(DT_INST_PARENT(0))
```

Build output will show expanded devicetree path.

### 10. Review Reference Drivers

Compare your implementation against working ADI drivers:
- **AD559x**: Well-documented, multi-bus, multiple children
- **MAX22017**: SPI-only, CRC support, locking
- **ADP5585**: I2C, interrupt handling

