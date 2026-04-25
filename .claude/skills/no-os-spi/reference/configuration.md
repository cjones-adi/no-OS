# SPI Configuration Details

Comprehensive details about SPI configuration parameters, modes, and data structures.

## Core Data Structures

### 1. no_os_spi_init_param - Initialization Parameters

```c
struct no_os_spi_init_param {
    uint32_t device_id;              // SPI bus number (0, 1, 2...)
    uint32_t max_speed_hz;           // Maximum SPI clock speed
    uint8_t chip_select;             // CS pin number
    enum no_os_spi_mode mode;        // SPI mode (0-3)
    enum no_os_spi_bit_order bit_order; // MSB/LSB first
    enum no_os_spi_lanes lanes;      // Single/Dual/Quad/Octo
    const struct no_os_spi_platform_ops *platform_ops;
    struct no_os_platform_spi_delays platform_delays;
    void *extra;                     // Platform-specific params
    struct no_os_spi_desc *parent;   // Parent device (optional)
};
```

**Field descriptions:**

- **device_id**: SPI peripheral number (SPI0=0, SPI1=1, etc.)
- **max_speed_hz**: Maximum clock frequency in Hz (e.g., 1000000 = 1 MHz)
- **chip_select**: CS/SS pin number for this device
- **mode**: SPI clock mode (0-3) - see SPI modes section
- **bit_order**: Data transmission order (MSB or LSB first)
- **lanes**: Data line configuration (standard SPI uses single lane)
- **platform_ops**: Pointer to platform-specific function table
- **platform_delays**: Hardware-specific timing delays
- **extra**: Pointer to platform-specific init parameters
- **parent**: Optional parent descriptor for shared resources

### 2. no_os_spi_desc - Runtime SPI Descriptor

```c
struct no_os_spi_desc {
    struct no_os_spibus_desc *bus;   // Shared bus descriptor
    uint32_t device_id;              // SPI bus number
    uint32_t max_speed_hz;           // Max clock speed
    uint8_t chip_select;             // CS pin
    enum no_os_spi_mode mode;        // SPI mode
    enum no_os_spi_bit_order bit_order;
    enum no_os_spi_lanes lanes;
    const struct no_os_spi_platform_ops *platform_ops;
    struct no_os_platform_spi_delays platform_delays;
    void *extra;                     // Platform-specific data
    struct no_os_spi_desc *parent;
};
```

This structure is allocated and populated by `no_os_spi_init()` based on `no_os_spi_init_param`.

### 3. no_os_spi_mode - SPI Clock Configuration

```c
enum no_os_spi_mode {
    NO_OS_SPI_MODE_0 = (0 | 0),            // CPOL=0, CPHA=0
    NO_OS_SPI_MODE_1 = (0 | NO_OS_SPI_CPHA),      // CPOL=0, CPHA=1
    NO_OS_SPI_MODE_2 = (NO_OS_SPI_CPOL | 0),      // CPOL=1, CPHA=0
    NO_OS_SPI_MODE_3 = (NO_OS_SPI_CPOL | NO_OS_SPI_CPHA) // CPOL=1, CPHA=1
};
```

**SPI Mode Details:**

- **CPOL (Clock Polarity)** - Idle state of clock line
  - 0 = Clock idle LOW
  - 1 = Clock idle HIGH

- **CPHA (Clock Phase)** - Data sampling edge
  - 0 = Sample on LEADING edge (first transition)
  - 1 = Sample on TRAILING edge (second transition)

**Mode Selection Table:**

| Mode | CPOL | CPHA | Clock Idle | Sample Edge | Shift Edge |
|------|------|------|------------|-------------|------------|
| 0 | 0 | 0 | Low | Rising (1st) | Falling (2nd) |
| 1 | 0 | 1 | Low | Falling (2nd) | Rising (1st) |
| 2 | 1 | 0 | High | Falling (1st) | Rising (2nd) |
| 3 | 1 | 1 | High | Rising (2nd) | Falling (1st) |

**Timing Diagrams:**

```
Mode 0 (CPOL=0, CPHA=0):
CS:   ‾‾|______________|‾‾‾
CLK:  __|‾|_|‾|_|‾|_|‾|_|__
MOSI: ==|D0|D1|D2|D3|D4|==
        ^  ^  ^  ^  ^       Sample on rising edge

Mode 1 (CPOL=0, CPHA=1):
CS:   ‾‾|______________|‾‾‾
CLK:  __|‾|_|‾|_|‾|_|‾|_|__
MOSI: |D0|D1|D2|D3|D4|==
         ^  ^  ^  ^  ^      Sample on falling edge

Mode 2 (CPOL=1, CPHA=0):
CS:   ‾‾|______________|‾‾‾
CLK:  ‾‾|_|‾|_|‾|_|‾|_|‾‾
MOSI: ==|D0|D1|D2|D3|D4|==
           ^  ^  ^  ^  ^    Sample on falling edge

Mode 3 (CPOL=1, CPHA=1):
CS:   ‾‾|______________|‾‾‾
CLK:  ‾‾|_|‾|_|‾|_|‾|_|‾‾
MOSI: |D0|D1|D2|D3|D4|==
        ^  ^  ^  ^  ^       Sample on rising edge
```

**How to choose mode:**
1. Consult device datasheet - look for SPI timing diagrams
2. Most common: Mode 0 (default for many devices)
3. Mode 3 also common (second most used)
4. Modes 1 and 2 less common

### 4. no_os_spi_bit_order - Bit Transmission Order

```c
enum no_os_spi_bit_order {
    NO_OS_SPI_BIT_ORDER_MSB_FIRST = 0,
    NO_OS_SPI_BIT_ORDER_LSB_FIRST = 1
};
```

**MSB First (Most Significant Bit First):**
- Most common
- Byte 0xAB transmitted as: A (1010), B (1011)
- Bit 7 → Bit 6 → ... → Bit 0

**LSB First (Least Significant Bit First):**
- Less common
- Byte 0xAB transmitted as: B (1011), A (1010) reversed
- Bit 0 → Bit 1 → ... → Bit 7

### 5. no_os_spi_msg - Transfer Message

```c
struct no_os_spi_msg {
    uint8_t *tx_buff;           // Transmit buffer (NULL = send 0x00)
    uint8_t *rx_buff;           // Receive buffer (NULL = discard)
    uint32_t bytes_number;      // Transfer length
    uint8_t cs_change;          // Deassert CS after transfer
    uint32_t cs_change_delay;   // Delay (us) before next CS assert
    uint32_t cs_delay_first;    // Delay (us) after CS assert
    uint32_t cs_delay_last;     // Delay (us) before CS deassert
};
```

**Buffer handling:**

| tx_buff | rx_buff | Behavior |
|---------|---------|----------|
| Valid | Valid | Full-duplex: transmit tx_buff, receive into rx_buff |
| Valid | NULL | TX-only: transmit tx_buff, discard RX data |
| NULL | Valid | RX-only: send 0x00, receive into rx_buff |
| NULL | NULL | ERROR: Invalid configuration |

**CS control:**

- **cs_change = 0**: Keep CS asserted (for multi-message sequences)
- **cs_change = 1**: Deassert CS after this message

**Timing delays:**

- **cs_delay_first**: Delay in nanoseconds AFTER CS assert, BEFORE first SCLK
- **cs_delay_last**: Delay in nanoseconds AFTER last SCLK, BEFORE CS deassert
- **cs_change_delay**: Delay in microseconds AFTER CS deassert, BEFORE next message

### 6. no_os_spi_platform_ops - Platform Function Pointers

```c
struct no_os_spi_platform_ops {
    int32_t (*init)(struct no_os_spi_desc **,
                    const struct no_os_spi_init_param *);
    int32_t (*write_and_read)(struct no_os_spi_desc *,
                              uint8_t *, uint16_t);
    int32_t (*transfer)(struct no_os_spi_desc *,
                        struct no_os_spi_msg *, uint32_t);
    int32_t (*transfer_dma)(struct no_os_spi_desc *,
                            struct no_os_spi_msg *, uint32_t);
    int32_t (*transfer_dma_async)(struct no_os_spi_desc *,
                                  struct no_os_spi_msg *, uint32_t,
                                  void (*callback)(void *), void *ctx);
    int32_t (*remove)(struct no_os_spi_desc *);
    int32_t (*transfer_abort)(struct no_os_spi_desc *);
};
```

**Required functions:**
- `init`: Initialize SPI peripheral
- `write_and_read`: Basic transfer
- `remove`: Cleanup resources

**Optional functions:**
- `transfer`: Message-based transfer (recommended)
- `transfer_dma`: DMA transfer (blocking)
- `transfer_dma_async`: DMA transfer (non-blocking with callback)
- `transfer_abort`: Abort ongoing transfer

### 7. no_os_spibus_desc - Shared Bus Descriptor

```c
struct no_os_spibus_desc {
    void *mutex;                    // Bus mutex (thread safety)
    uint8_t slave_number;           // Number of slaves on bus
    uint32_t device_id;             // Bus number
    uint32_t max_speed_hz;          // Bus max speed
    enum no_os_spi_mode mode;       // Bus mode
    enum no_os_spi_bit_order bit_order;
    enum no_os_spi_lanes lanes;
    const struct no_os_spi_platform_ops *platform_ops;
    void *extra;                    // Platform-specific
};
```

**Automatic bus management:**
- Created on first `no_os_spi_init()` for a bus
- Shared by all devices on same `device_id`
- Freed when last device is removed
- Mutex ensures thread-safe bus access

## SPI Bus Management

### Multi-Slave Bus Architecture

```
SPI Bus 0 (device_id = 0)
│
├── Slave 0 (CS0) - ADC
│   ├── spi_desc->chip_select = 0
│   └── spi_desc->bus → spibus_desc
│
├── Slave 1 (CS1) - DAC
│   ├── spi_desc->chip_select = 1
│   └── spi_desc->bus → spibus_desc (same bus)
│
└── Slave 2 (CS2) - EEPROM
    ├── spi_desc->chip_select = 2
    └── spi_desc->bus → spibus_desc (same bus)
```

### Bus Creation and Sharing

**Automatic creation:**

```c
// First init on SPI0 creates the bus
struct no_os_spi_init_param init_adc = {
    .device_id = 0,
    .chip_select = 0,
    // ...
};
no_os_spi_init(&spi_adc, &init_adc);
// Behind the scenes:
// 1. no_os_spibus_init() creates shared bus
// 2. Bus stored in spi_table[0]
// 3. spi_adc->bus points to shared bus
// 4. bus->slave_number = 1
```

**Sharing:**

```c
// Second init on SPI0 reuses the bus
struct no_os_spi_init_param init_dac = {
    .device_id = 0,    // Same bus
    .chip_select = 1,  // Different CS
    // ...
};
no_os_spi_init(&spi_dac, &init_dac);
// Behind the scenes:
// 1. Finds existing bus in spi_table[0]
// 2. spi_dac->bus points to same bus as spi_adc
// 3. bus->slave_number = 2
```

### Bus Mutex Locking

**Automatic locking in transfers:**

```c
int32_t no_os_spi_write_and_read(struct no_os_spi_desc *desc, ...)
{
    int ret;
    
    // Lock bus (thread-safe)
    no_os_mutex_lock(desc->bus->mutex);
    
    // Perform transfer
    ret = desc->platform_ops->write_and_read(desc, data, bytes_number);
    
    // Unlock bus
    no_os_mutex_unlock(desc->bus->mutex);
    
    return ret;
}
```

**Benefits:**
- Multiple threads can access different slaves safely
- Bus access is serialized automatically
- No manual mutex management required

### Bus Removal

**Automatic cleanup:**

```c
no_os_spi_remove(spi_adc);     // bus->slave_number = 2
no_os_spi_remove(spi_dac);     // bus->slave_number = 1
no_os_spi_remove(spi_eeprom);  // bus->slave_number = 0
                               // → Bus automatically freed
```

## Clock Speed Configuration

### Selecting max_speed_hz

**Considerations:**

1. **Device maximum** - Check datasheet
   - Example: MAX20370 supports up to 10 MHz
   
2. **Platform limitations** - Check platform capabilities
   - Some platforms have limited prescaler options
   - Actual speed may be rounded down to nearest supported
   
3. **Signal integrity** - PCB layout matters
   - Long traces → lower speed
   - Good ground planes → higher speed
   - Typical: 1-10 MHz for most applications
   
4. **Debugging** - Start slow
   - Initial development: 100 kHz - 1 MHz
   - Production: Increase to maximum reliable speed

**Example speeds:**

```c
// Conservative (debugging)
.max_speed_hz = 100000,        // 100 kHz

// Typical (production)
.max_speed_hz = 1000000,       // 1 MHz

// Fast (short traces, good PCB)
.max_speed_hz = 10000000,      // 10 MHz

// Very fast (careful design required)
.max_speed_hz = 50000000,      // 50 MHz
```

### Platform Speed Limitations

**Maxim platform example:**

```c
// SPI clock derived from peripheral clock with prescaler
// Actual speed = PCLK / (2 * (DIV + 1))
// If PCLK = 50 MHz, max_speed_hz = 10 MHz:
//   10 MHz = 50 MHz / (2 * (DIV + 1))
//   DIV = 1.5 → rounds to 2
//   Actual = 50 MHz / (2 * 3) = 8.33 MHz
```

**Best practice:** Request desired speed, platform will select closest achievable.

## Chip Select Configuration

### Hardware vs Software CS

**Hardware CS:**
- CS controlled by SPI peripheral
- Automatic assertion/deassertion
- Limited flexibility (may toggle between bytes on some platforms)

**Software CS:**
- CS controlled via GPIO
- Full control over timing
- Required for some devices with strict CS requirements

**Platform example (Mbed):**

```c
struct mbed_spi_init_param extra = {
    .spi_miso_pin = SPI_MISO,
    .spi_mosi_pin = SPI_MOSI,
    .spi_clk_pin = SPI_SCK,
    .use_sw_csb = true,    // Use software CS control
};
```

### CS Polarity

**Active-low (standard):**
- CS=1 (HIGH) when idle
- CS=0 (LOW) to select device
- Most common

**Active-high (uncommon):**
- CS=0 (LOW) when idle
- CS=1 (HIGH) to select device
- Some specialized devices

**Platform example (Maxim):**

```c
struct max_spi_init_param extra = {
    .polarity = 0,    // Active-low (standard)
    // .polarity = 1,    // Active-high (uncommon)
};
```

## Lane Configuration

### Standard SPI (Single Lane)

```c
enum no_os_spi_lanes {
    NO_OS_SPI_LANES_SINGLE = 1,
    NO_OS_SPI_LANES_DUAL = 2,
    NO_OS_SPI_LANES_QUAD = 4,
    NO_OS_SPI_LANES_OCTO = 8
};
```

**Single lane (standard):**
- MOSI (Master Out, Slave In)
- MISO (Master In, Slave Out)
- Separate TX and RX lines
- Most common configuration

**Dual/Quad/Octo (advanced):**
- Multiple data lines for higher throughput
- Typically used for flash memory
- Requires special hardware support
- Not commonly used in general SPI devices

**Example:**

```c
struct no_os_spi_init_param spi_init = {
    .lanes = NO_OS_SPI_LANES_SINGLE,  // Standard SPI
    // ...
};
```
