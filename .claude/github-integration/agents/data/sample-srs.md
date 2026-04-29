# Software Requirements Specification: AD7606 8-Channel, 16-Bit SAR ADC

## Document Control

| Property | Value |
|----------|-------|
| **Document ID** | SRS-AD7606-001 |
| **Version** | 1.0 |
| **Date** | March 2, 2026 |
| **Author** | driver-planner agent |
| **Status** | Example |

## 1. Introduction

### 1.1 Purpose
This SRS defines the requirements for developing a no-OS driver for the AD7606 8-channel, 16-bit simultaneous-sampling SAR analog-to-digital converter. The driver enables applications to configure the ADC, initiate conversions, and read analog measurement data from 8 parallel channels.

### 1.2 Scope
**Included:**
- ADC initialization and configuration
- Single and continuous conversion modes
- Reading raw ADC data from all 8 channels
- Oversampling configuration
- Range selection (±10V, ±5V)
- Standby and power-down modes
- GPIO-based conversion triggering

**Excluded:**
- DMA-based data transfer (future enhancement)
- Advanced diagnostics (CRC, self-test at this phase)
- Multi-device chaining

### 1.3 Target Hardware
- **Device**: AD7606B-8 (8-channel variant)
- **Manufacturer**: Analog Devices
- **Communication Interface**: Parallel 8-bit or 16-bit bus (with optional SPI mode)
- **Key Features**: 
  - 8 simultaneous-sampling channels
  - 16-bit resolution
  - 800 kSps conversion rate per channel
  - Software and hardware configurable range
  - Chop mode for noise reduction
  
### 1.4 Datasheet Reference
- **Part Number**: AD7606B
- **Key Sections**: 
  - Timing Specifications (Table 6)
  - Register Definitions (Section 5)
  - Conversion Sequences (Figure 10)

## 2. System Overview

### 2.1 Hardware Description
The AD7606 is a fully integrated data acquisition system that simultaneously samples 8 analog input channels and converts them to 16-bit digital words. Key capabilities:

- **8-Channel Simultaneous Sampling**: Eliminates skew between channels
- **Configurable Input Range**: ±10V, ±5V (per channel independently)
- **Conversion Speed**: 800 kSps per channel
- **Low Power**: Under 10 mW typical
- **Oversampling**: 2x, 4x, 8x, 16x modes available

### 2.2 Physical Interface
- **Data Bus**: 8 or 16 parallel lines or SPI
- **Parallel Mode Signals**:
  - CONVST: Conversion start (active high pulse)
  - RD: Read strobe
  - CS: Chip select
  - WR: Write strobe (for range/mode configuration)
- **Control GPIO**: 
  - STBY: Standby control (optional)
  - RESET: Hardware reset (optional)
- **Interrupt**: BUSY signal (indicates conversion in progress)

### 2.3 Block Diagram
```
┌─────────────────────────────────────┐
│   8 Analog Input Channels (0-7)     │
│   With Independent Range Select     │
└─────────────┬───────────────────────┘
              │
      ┌───────▼────────┐
      │ Sample & Hold  │
      │ (8 channels)   │
      └────────┬────────┘
               │
      ┌────────▼────────┐
      │ 16-bit SAR ADC  │
      │ (Shared)        │
      └────────┬────────┘
               │
      ┌────────▼─────────────┐
      │ Output Register      │
      │ (16 bits × 8 ch)     │
      └────────┬─────────────┘
               │
         Parallel/SPI Bus
         to Microcontroller
```

## 3. Functional Requirements

### 3.1 Initialization & Configuration

**REQ-001**: Driver shall provide `ad7606_init()` function that:
- Accepts hardware configuration (bus interface, GPIO pins, input ranges)
- Initializes the ADC in a known state
- Configures all 8 input channels
- Returns a device descriptor for subsequent operations
- Returns error code if initialization fails

**REQ-002**: Driver shall support per-channel range configuration:
- Each of 8 channels independently configurable to ±10V or ±5V
- Range changes reflected immediately after `ad7606_set_range()` call
- Default range: ±10V for all channels

**REQ-003**: Driver shall provide `ad7606_remove()` function that:
- Powers down the ADC (places in standby)
- Releases all allocated resources
- Prevents further operations without re-initialization

### 3.2 Conversion Control

**REQ-004**: Driver shall provide `ad7606_start_conversion()` function that:
- Initiates a single conversion cycle across all 8 channels
- Blocking call that waits for conversion complete (via BUSY polling or interrupt)
- Returns immediately with sample timestamp internally recorded
- Returns error if ADC is not ready

**REQ-005**: Driver shall provide `ad7606_read_data()` function that:
- Returns the most recent conversion results as array of 8 int16_t values
- Data represents raw ADC codes (0-65535 for ±10V range)
- Invalid if called before first conversion completed
- Channel order: [CH0, CH1, CH2, CH3, CH4, CH5, CH6, CH7]

**REQ-006**: Driver shall support continuous conversion mode via `ad7606_start_continuous()`:
- Initiates repeated conversions at maximum rate (800 kSps per channel)
- Non-blocking call
- Requires subsequent `ad7606_stop_continuous()` to cease conversions
- Each conversion cycle fills the output register, available for reading

### 3.3 Oversampling and Signal Conditioning

**REQ-007**: Driver shall provide `ad7606_set_oversampling()` function that:
- Accepts oversampling ratio: 1, 2, 4, 8, or 16
- Higher ratios reduce noise but increase conversion time proportionally
- Affects all 8 channels simultaneously
- Default: No oversampling (ratio = 1)

**REQ-008**: Driver shall provide `ad7606_set_chop_mode()` function that:
- Enables/disables chop mode (reduces 1/f noise and offset)
- Affects all channels simultaneously
- Default: Disabled

### 3.4 Power Management

**REQ-009**: Driver shall provide `ad7606_set_standby()` function that:
- Places ADC in low-power standby mode (≤ 1 µA)
- CONVST pulses ignored while in standby
- Wake-up via `ad7606_start_conversion()` or explicit wake call
- Device exits standby within 1 µs

**REQ-010**: Driver shall provide `ad7606_shutdown()` function that:
- Removes power from ADC (requires external STBY GPIO control)
- All configuration lost; must call `ad7606_init()` to restart
- Power consumption nearly zero (leakage only)

### 3.5 Data Management

**REQ-011**: Driver shall maintain internal state including:
- Current range configuration per channel
- Last conversion results (8 × 16-bit values)
- Oversampling ratio
- Conversion busy status
- Timestamp of last conversion

**REQ-012**: Driver shall return all data as int16_t values:
- Raw ADC codes without scaling (0-65535 for ±10V)
- Caller responsible for scaling to voltage if needed
- Data format: signed 16-bit two's complement

## 4. Non-Functional Requirements

### 4.1 Performance

**REQ-013**: Conversion latency shall not exceed:
- Single conversion start to data ready: 2 µs (typical)
- Continuous conversions: ≥ 800 kSps per channel

**REQ-014**: Memory footprint shall be:
- Maximum 1 KB for driver code + data structures
- No dynamic memory allocation

### 4.2 Robustness

**REQ-015**: Driver shall handle error conditions:
- Timeout if conversion doesn't complete within 10 ms
- Invalid channel index (REQ returns -EINVAL)
- Setting invalid range (returns -EINVAL)
- Bus communication errors (returns -EIO)

**REQ-016**: Driver shall be resilient to:
- Repeated `init()` calls without `remove()`
- Spurious device interrupts
- Partial configuration updates

### 4.3 Code Quality

**REQ-017**: All functions shall have clear documentation:
- Function purpose
- Parameter descriptions
- Return values and error codes
- Usage examples in docstrings

**REQ-018**: Driver shall follow no-OS conventions:
- Naming: `ad7606_*()` for public functions, `_ad7606_*()` for private
- Return type: `int32_t` with error codes from `no_os_error.h`
- Parameter order: device descriptor first, then configuration parameters

## 5. API Specification

### 5.1 Data Structures

```c
/* Initialization parameters */
struct ad7606_init_param {
    struct no_os_spi_desc *spi_desc;    /* SPI interface descriptor */
    struct no_os_gpio_desc *convst_gpio; /* CONVST control GPIO */
    struct no_os_gpio_desc *busy_gpio;   /* BUSY status GPIO */
    struct no_os_gpio_desc *reset_gpio;  /* Optional RESET GPIO */
    uint8_t range[8];                     /* Range per channel (0=±10V, 1=±5V) */
    uint8_t oversampling;                 /* OS ratio: 1, 2, 4, 8, 16 */
    bool chop_mode_enabled;               /* Chop mode flag */
};

/* Device descriptor (opaque to user) */
struct ad7606_dev {
    struct no_os_spi_desc *spi_desc;
    struct no_os_gpio_desc *convst_gpio;
    struct no_os_gpio_desc *busy_gpio;
    struct no_os_gpio_desc *reset_gpio;
    uint16_t data[8];                    /* Last conversion results */
    uint8_t range[8];
    uint8_t oversampling;
    bool continuous_mode;
    /* [internal state fields] */
};
```

### 5.2 Function Prototypes

```c
/* Initialization & Cleanup */
int32_t ad7606_init(struct ad7606_dev **device,
                    struct ad7606_init_param *init_param);
int32_t ad7606_remove(struct ad7606_dev *device);

/* Conversion Control */
int32_t ad7606_start_conversion(struct ad7606_dev *device);
int32_t ad7606_read_data(struct ad7606_dev *device, uint16_t *data);
int32_t ad7606_start_continuous(struct ad7606_dev *device);
int32_t ad7606_stop_continuous(struct ad7606_dev *device);

/* Configuration */
int32_t ad7606_set_range(struct ad7606_dev *device, uint8_t channel, uint8_t range);
int32_t ad7606_get_range(struct ad7606_dev *device, uint8_t channel, uint8_t *range);
int32_t ad7606_set_oversampling(struct ad7606_dev *device, uint8_t ratio);
int32_t ad7606_get_oversampling(struct ad7606_dev *device, uint8_t *ratio);
int32_t ad7606_set_chop_mode(struct ad7606_dev *device, bool enabled);

/* Power Management */
int32_t ad7606_set_standby(struct ad7606_dev *device, bool standby);
int32_t ad7606_shutdown(struct ad7606_dev *device);
```

## 6. Error Handling

| Error Code | Meaning | Recovery |
|------------|---------|----------|
| 0 | Success | Continue operation |
| -EINVAL | Invalid parameter (range, channel, ratio) | Verify input and retry |
| -EIO | Bus communication error | Retry or reinitialize |
| -ETIMEDOUT | Conversion didn't complete in time | Check hardware, retry |
| -EBUSY | Device already performing operation | Wait and retry |

## 7. Usage Example (Pseudo-code)

```c
/* Initialize */
struct ad7606_init_param init = {
    .spi_desc = spi_device,
    .convst_gpio = convst_pin,
    .busy_gpio = busy_pin,
    .range = {0, 0, 0, 0, 0, 0, 0, 0},  /* All ±10V */
    .oversampling = 1
};
ad7606_init(&adc, &init);

/* Configure channel 0 for ±5V */
ad7606_set_range(adc, 0, 1);

/* Read single conversion */
ad7606_start_conversion(adc);
uint16_t data[8];
ad7606_read_data(adc, data);

/* Continuous acquisition */
ad7606_start_continuous(adc);
for (int i = 0; i < 1000; i++) {
    ad7606_read_data(adc, data);  /* Latest results */
}
ad7606_stop_continuous(adc);

/* Cleanup */
ad7606_remove(adc);
```

## 8. Design Considerations

### 8.1 Register Access
The driver shall use helper functions to abstract register read/write operations:
- `_ad7606_write_config()`: Write to configuration register
- `_ad7606_read_status()`: Read status/busy signal
- Implementation uses SPI or parallel bus depending on hardware configuration

### 8.2 Timing Considerations
- CONVST pulse must be ≥ 40 ns
- Minimum time between CONVST pulses: 1.28 µs + conversion time
- BUSY signal cleared within 150 ns after conversion complete
- Driver uses GPIO polling or interrupt-based detection

### 8.3 Synchronization
For multi-channel simultaneous sampling, the driver ensures:
- All 8 channels sample within ≤ 10 ns of each other (hardware guarantee)
- Sample-to-digital delay matched across all channels
- No artificial synchronization overhead in firmware

## 9. Testing Strategy

### 9.1 Unit Test Coverage
- **Initialization**: Valid/invalid parameters, repeated init
- **Range configuration**: All 16 combinations (8 channels × 2 ranges)
- **Conversion**: Single and continuous modes, timeout handling
- **Power management**: Standby/wake transitions
- **Error handling**: Invalid inputs, bus errors (mocked)

### 9.2 Coverage Target
Minimum 85% code coverage including:
- All public functions
- All error paths
- All valid configurations

### 9.3 Hardware Validation (Post-testing)
- Verify output data correctness with known input signals
- Measure conversion timing and latency
- Test all 8 channels with varying input ranges
- Stress test with rapid conversions

## 10. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-02 | driver-planner | Initial version with 8 basic requirements |
| | | | - Read single conversion |
| | | | - Support all 8 channels |
| | | | - Per-channel range configuration |
| | | | - Oversampling and chop mode |
| | | | - Power management (standby/shutdown) |

---

**Document Status**: Example/Reference
**Next Steps**: User review and feedback on proposed API and requirements
