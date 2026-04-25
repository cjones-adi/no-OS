## Debugging Tips

### 1. Enable ADC Logging

**In prj.conf**:
```conf
CONFIG_ADC_LOG_LEVEL_DBG=y
CONFIG_LOG=y
```

**In driver code**:
```c
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(adc_mydevice, CONFIG_ADC_LOG_LEVEL);

LOG_DBG("Channel %d configured: gain=%d, ref=%d", ch, gain, ref);
LOG_ERR("SPI transfer failed: %d", ret);
```

### 2. Verify SPI/I2C Bus Communication

```c
/* Check bus ready */
if (!spi_is_ready_dt(&config->spi)) {
	LOG_ERR("SPI bus not ready");
	return -ENODEV;
}

/* Read device ID register to verify communication */
uint8_t id;
int ret = read_register(dev, REG_ID, &id);
if (ret < 0) {
	LOG_ERR("Failed to read ID register: %d", ret);
	return ret;
}

if (id != EXPECTED_ID) {
	LOG_ERR("Wrong device ID: got 0x%02X, expected 0x%02X", id, EXPECTED_ID);
	return -EIO;
}

LOG_INF("Found device ID 0x%02X", id);
```

### 3. Check Buffer Alignment and Size

```c
LOG_DBG("Sequence: channels=0x%08X, buffer_size=%zu, resolution=%d",
        sequence->channels, sequence->buffer_size, sequence->resolution);

uint8_t num_ch = POPCOUNT(sequence->channels);
size_t needed = num_ch * (sequence->resolution > 16 ? 4 : 2);

if (sequence->buffer_size < needed) {
	LOG_ERR("Buffer size %zu too small, need %zu",
	        sequence->buffer_size, needed);
	return -ENOMEM;
}
```

### 4. Log Raw ADC Values

```c
LOG_DBG("ADC read: raw=0x%04X (%u decimal)", raw, raw);

int32_t val_mv = (int32_t)raw;
int err = adc_raw_to_millivolts_dt(&spec, &val_mv);

if (err == 0) {
	LOG_INF("Converted: %u → %d mV", raw, val_mv);
} else {
	LOG_WRN("Conversion failed: %d", err);
}
```

### 5. Validate Gain and Reference Configuration

```c
static const char *gain_str(enum adc_gain gain) {
	switch (gain) {
	case ADC_GAIN_1_6: return "1/6";
	case ADC_GAIN_1:   return "1";
	case ADC_GAIN_2:   return "2";
	/* ... */
	default: return "unknown";
	}
}

static const char *ref_str(enum adc_reference ref) {
	switch (ref) {
	case ADC_REF_INTERNAL: return "INTERNAL";
	case ADC_REF_VDD_1:    return "VDD";
	case ADC_REF_EXTERNAL0: return "EXTERNAL0";
	/* ... */
	default: return "unknown";
	}
}

LOG_DBG("Channel %d: gain=%s, ref=%s, acq_time=%u",
        channel_id, gain_str(cfg->gain), ref_str(cfg->reference),
        cfg->acquisition_time);
```

### 6. Check for Clipping and Saturation

```c
uint16_t raw = buffer[0];
uint16_t max_val = (1U << resolution) - 1;

if (raw >= max_val) {
	LOG_WRN("ADC saturated at maximum (0x%04X)", raw);
} else if (raw == 0) {
	LOG_WRN("ADC reading zero (input below range?)");
}
```

### 7. Verify Reference Voltage Value

```c
int32_t vref_mv;

if (spec.channel_cfg.reference == ADC_REF_INTERNAL) {
	vref_mv = (int32_t)adc_ref_internal(spec.dev);
	LOG_DBG("Using internal reference: %d mV", vref_mv);
} else {
	vref_mv = spec.vref_mv;
	LOG_DBG("Using DT reference: %d mV", vref_mv);
}

if (vref_mv == 0) {
	LOG_ERR("Reference voltage not specified!");
}
```

### 8. Test with Known Voltage

```c
/* Connect ADC input to known voltage (e.g., VCC/2 resistor divider) */
/* Expected reading: */
int32_t expected_mv = 1650;  /* 3.3V / 2 = 1.65V */
int32_t tolerance = 50;      /* ±50mV */

int32_t actual_mv = (int32_t)raw;
adc_raw_to_millivolts_dt(&spec, &actual_mv);

if (abs(actual_mv - expected_mv) > tolerance) {
	LOG_WRN("ADC reading out of range: got %d mV, expected %d mV ±%d",
	        actual_mv, expected_mv, tolerance);
}
```

