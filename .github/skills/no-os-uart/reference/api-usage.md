# UART API Usage Examples

Complete examples and usage patterns for no-OS UART driver API.

## Common UART Patterns

### Pattern 1: Simple Debug Output

```c
struct no_os_uart_desc *uart;

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&uart, &uart_init);

// Redirect printf to UART
no_os_uart_stdio(uart);

// Now printf works
printf("System initialized\n");
printf("Temperature: %d°C\n", temp_value);

no_os_uart_remove(uart);
```

### Pattern 2: Command-Line Interface (CLI)

```c
struct no_os_uart_desc *uart;
char cmd_buffer[256];
int cmd_index = 0;

// Initialize with async RX
struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .irq_id = 2,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,  // Async RX for CLI
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&uart, &uart_init);
no_os_uart_write(uart, (uint8_t *)"> ", 2);  // Print prompt

// Main loop
while (1) {
    uint8_t char_received;
    int bytes = no_os_uart_read_nonblocking(uart, &char_received, 1);

    if (bytes > 0) {
        if (char_received == '\n' || char_received == '\r') {
            cmd_buffer[cmd_index] = '\0';
            // Process command
            process_command(cmd_buffer);
            cmd_index = 0;
            no_os_uart_write(uart, (uint8_t *)"> ", 2);
        } else if (cmd_index < sizeof(cmd_buffer) - 1) {
            cmd_buffer[cmd_index++] = char_received;
            // Echo received character
            no_os_uart_write(uart, &char_received, 1);
        }
    }
}

no_os_uart_remove(uart);
```

### Pattern 3: Sensor Data Logging

```c
struct no_os_uart_desc *uart;
uint32_t sample_count = 0;

struct no_os_uart_init_param uart_init = {
    .device_id = 1,
    .baud_rate = 250000,  // High baud for fast logging
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&uart, &uart_init);
no_os_uart_stdio(uart);

// Sensor callback (called periodically)
void sensor_callback(int32_t temperature, int32_t humidity)
{
    printf("%u,%.1f,%.1f\n", sample_count++,
           temperature / 1000.0, humidity / 1000.0);
}
```

### Pattern 4: Modbus RTU (9-bit mode)

```c
struct no_os_uart_desc *uart;

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 19200,
    .size = NO_OS_UART_CS_9,      // 9-bit for Modbus
    .parity = NO_OS_UART_PAR_EVEN,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&uart, &uart_init);

// Transmit Modbus frame
uint8_t modbus_frame[] = {0x01, 0x03, 0x00, 0x40, 0x00, 0x02, 0x41, 0x80};
no_os_uart_write(uart, modbus_frame, sizeof(modbus_frame));

// Receive response
uint8_t response[256];
int bytes = no_os_uart_read(uart, response, sizeof(response));
```

### Pattern 5: Multi-UART Management

```c
struct no_os_uart_desc *debug_uart;
struct no_os_uart_desc *modbus_uart;
struct no_os_uart_desc *gps_uart;

// Debug UART (fast, async)
struct no_os_uart_init_param debug_init = {
    .device_id = 0,
    .irq_id = 2,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,
    .platform_ops = &max_uart_ops,
};

// Modbus UART (Modbus RTU)
struct no_os_uart_init_param modbus_init = {
    .device_id = 1,
    .baud_rate = 9600,
    .size = NO_OS_UART_CS_9,
    .parity = NO_OS_UART_PAR_EVEN,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = false,
    .platform_ops = &max_uart_ops,
};

// GPS UART (NMEA protocol)
struct no_os_uart_init_param gps_init = {
    .device_id = 2,
    .irq_id = 3,
    .baud_rate = 9600,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&debug_uart, &debug_init);
no_os_uart_init(&modbus_uart, &modbus_init);
no_os_uart_init(&gps_uart, &gps_init);

// Use each UART independently
no_os_uart_write(debug_uart, (uint8_t *)"Debug output\n", 13);
no_os_uart_write(modbus_uart, modbus_frame, len);
// GPS data automatically buffered in RX FIFO
```

### Pattern 6: Data Rate Conversion

```c
// Read from slow UART, write to fast UART
// Useful for data logging, protocol conversion

struct no_os_uart_desc *rx_uart;   // 9600 baud
struct no_os_uart_desc *tx_uart;   // 115200 baud
uint8_t buffer[256];

while (1) {
    // Read from slow
    int bytes = no_os_uart_read_nonblocking(rx_uart, buffer, 256);
    if (bytes > 0) {
        // Write to fast (non-blocking)
        no_os_uart_write_nonblocking(tx_uart, buffer, bytes);
    }
}
```

## UART Initialization Patterns

### Basic UART - Blocking I/O

```c
struct no_os_uart_desc *uart_desc;

struct no_os_uart_init_param uart_init = {
    .device_id = 0,              // UART 0
    .baud_rate = 115200,         // 115.2k baud
    .size = NO_OS_UART_CS_8,     // 8 data bits
    .parity = NO_OS_UART_PAR_NO, // No parity
    .stop = NO_OS_UART_STOP_1_BIT, // 1 stop bit
    .asynchronous_rx = false,    // Blocking mode
    .platform_ops = &max_uart_ops,
};

// Initialize UART
int ret = no_os_uart_init(&uart_desc, &uart_init);
if (ret) {
    printf("UART init failed\n");
    return ret;
}

// Now ready to use
// ...

// Cleanup
no_os_uart_remove(uart_desc);
```

### Interrupt-Driven UART - Asynchronous RX

```c
struct no_os_uart_desc *uart_desc;

struct no_os_uart_init_param uart_init = {
    .device_id = 1,              // UART 1
    .irq_id = 2,                 // Use IRQ 2 for RX
    .baud_rate = 9600,           // 9.6k baud
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_EVEN,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,     // Enable interrupt-driven RX
    .platform_ops = &max_uart_ops,
};

// Initialize with async RX
int ret = no_os_uart_init(&uart_desc, &uart_init);
if (ret)
    return ret;

// Received characters automatically buffered in RX FIFO
// Use no_os_uart_read() to retrieve from buffer
```

### Platform-Specific Extras Example

```c
// Maxim platform extras
struct max_uart_init_param extra_params = {
    .flow_control = false,  // No hardware flow control
    .dma_enabled = false,   // No DMA
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .extra = &extra_params,  // Platform-specific settings
    .platform_ops = &max_uart_ops,
};
```

## UART Operations

### 1. Blocking I/O (Wait for Completion)

#### Blocking Write

```c
int32_t no_os_uart_write(struct no_os_uart_desc *desc,
                         const uint8_t *data,
                         uint32_t bytes_number);
```

**Behavior:** Function blocks until all data is transmitted.

```c
const char *message = "Hello, World!\n";
int ret = no_os_uart_write(uart_desc, (uint8_t *)message,
                           strlen(message));
if (ret)
  printf("Write failed: %d\n", ret);
// Function returns after all bytes sent
```

#### Blocking Read

```c
int32_t no_os_uart_read(struct no_os_uart_desc *desc,
                        uint8_t *data,
                        uint32_t bytes_number);
```

**Behavior:** Function blocks until all bytes received (or timeout in some implementations).

```c
uint8_t buffer[128];
int bytes_read = no_os_uart_read(uart_desc, buffer, 128);
if (bytes_read > 0)
  printf("Received %d bytes\n", bytes_read);
  // Process data
```

### 2. Non-Blocking I/O (Don't Wait)

#### Non-Blocking Write

```c
int32_t no_os_uart_write_nonblocking(struct no_os_uart_desc *desc,
                                     const uint8_t *data,
                                     uint32_t bytes_number);
```

**Behavior:** Returns immediately. Returns number of bytes queued (may be less than requested).

```c
const char *message = "Quick message!\n";
int queued = no_os_uart_write_nonblocking(uart_desc,
                                          (uint8_t *)message,
                                          strlen(message));
if (queued < strlen(message))
    printf("Only queued %d of %d bytes\n", queued,
           (int)strlen(message));
// Function returns immediately, transmit continues in background
```

#### Non-Blocking Read

```c
int32_t no_os_uart_read_nonblocking(struct no_os_uart_desc *desc,
                                     uint8_t *data,
                                     uint32_t bytes_number);
```

**Behavior:** Returns immediately. Returns number of bytes available in RX buffer (may be 0).

```c
uint8_t buffer[64];
int available = no_os_uart_read_nonblocking(uart_desc, buffer, 64);
if (available > 0)
    printf("Received %d bytes\n", available); // Process data
else
    printf("No data available\n");
```

### 3. Error Handling

```c
uint32_t no_os_uart_get_errors(struct no_os_uart_desc *desc);
```

**Returns:** Error count (overflow, framing error, parity error, etc.)

```c
uint32_t errors = no_os_uart_get_errors(uart_desc);
if (errors > 0)
    printf("UART errors detected: %u\n", errors);
    // Handle errors (reset UART, notify user, etc.)
```

### 4. Standard I/O Redirection

```c
void no_os_uart_stdio(struct no_os_uart_desc *desc);
```

**Effect:** Redirects stdin/stdout/stderr to UART, enables printf/scanf.

```c
no_os_uart_stdio(uart_desc);  // After this, printf works
printf("This goes to UART!\n");
```

## Advanced Examples

### Protocol Parser Example

```c
struct no_os_uart_desc *uart;
uint8_t rx_buffer[256];
int rx_index = 0;

// Initialize async UART
struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .irq_id = 2,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&uart, &uart_init);

// Main loop - parse incoming data
while (1) {
    uint8_t byte;
    int bytes = no_os_uart_read_nonblocking(uart, &byte, 1);
    
    if (bytes > 0) {
        if (byte == 0xAA) {  // Start of frame
            rx_index = 0;
            rx_buffer[rx_index++] = byte;
        } else if (rx_index > 0) {
            rx_buffer[rx_index++] = byte;
            
            // Check for complete frame
            if (rx_index >= 3 && rx_buffer[rx_index-1] == 0x55) {
                // Process frame
                process_frame(rx_buffer, rx_index);
                rx_index = 0;
            }
            
            // Prevent overflow
            if (rx_index >= sizeof(rx_buffer)) {
                rx_index = 0;
            }
        }
    }
}
```

### Binary Protocol Example

```c
struct no_os_uart_desc *uart;

// Send binary structure
struct sensor_data {
    uint32_t timestamp;
    int16_t temperature;
    int16_t humidity;
    uint16_t crc;
} __attribute__((packed));

struct sensor_data data = {
    .timestamp = get_timestamp(),
    .temperature = 2350,  // 23.5°C
    .humidity = 6540,     // 65.4%
};

// Calculate CRC
data.crc = calculate_crc((uint8_t *)&data, 
                         sizeof(data) - sizeof(data.crc));

// Send binary data
no_os_uart_write(uart, (uint8_t *)&data, sizeof(data));
```

### NMEA GPS Parser Example

```c
struct no_os_uart_desc *gps_uart;
char nmea_buffer[128];
int nmea_index = 0;

// Initialize GPS UART
struct no_os_uart_init_param gps_init = {
    .device_id = 2,
    .irq_id = 3,
    .baud_rate = 9600,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .asynchronous_rx = true,
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&gps_uart, &gps_init);

// Parse NMEA sentences
while (1) {
    uint8_t byte;
    int bytes = no_os_uart_read_nonblocking(gps_uart, &byte, 1);
    
    if (bytes > 0) {
        if (byte == '$') {
            // Start of NMEA sentence
            nmea_index = 0;
            nmea_buffer[nmea_index++] = byte;
        } else if (nmea_index > 0) {
            nmea_buffer[nmea_index++] = byte;
            
            if (byte == '\n') {
                // Complete sentence
                nmea_buffer[nmea_index] = '\0';
                parse_nmea_sentence(nmea_buffer);
                nmea_index = 0;
            }
            
            if (nmea_index >= sizeof(nmea_buffer)) {
                nmea_index = 0;  // Overflow protection
            }
        }
    }
}
```

### Flow Control Example

```c
struct no_os_uart_desc *uart;

// Maxim platform with hardware flow control
struct max_uart_init_param maxim_extra = {
    .flow_control = true,  // Enable RTS/CTS
    .dma_enabled = false,
};

struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .extra = &maxim_extra,
    .platform_ops = &max_uart_ops,
};

no_os_uart_init(&uart, &uart_init);

// Hardware flow control automatically handles TX/RX buffering
// No need to check buffer status manually
```

## Summary

Key usage patterns:
- **Debug output** - Simple printf redirection
- **CLI** - Async RX with character-by-character parsing
- **Logging** - High baud rate, blocking writes
- **Modbus** - 9-bit mode, even parity, specific timing
- **Multi-UART** - Independent instances for different functions
- **Protocol parsing** - Async RX with state machine

Always match:
- Baud rate on both TX and RX sides
- Data bits, parity, stop bits configuration
- Use async RX for interactive applications
- Use blocking I/O for simple logging/debug
