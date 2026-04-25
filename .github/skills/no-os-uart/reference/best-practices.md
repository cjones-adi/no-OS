# UART Best Practices

Best practices and guidelines for using no-OS UART drivers effectively.

## Initialization and Cleanup

### 1. Always Initialize Before Use

```c
struct no_os_uart_desc *uart_desc;
struct no_os_uart_init_param uart_init = {
    .device_id = 0,
    .baud_rate = 115200,
    .size = NO_OS_UART_CS_8,
    .parity = NO_OS_UART_PAR_NO,
    .stop = NO_OS_UART_STOP_1_BIT,
    .platform_ops = &max_uart_ops,
};

// ALWAYS check return value
int ret = no_os_uart_init(&uart_desc, &uart_init);
if (ret) {
    printf("UART init failed: %d\n", ret);
    return ret;
}
```

**Why:** Uninitialized UART descriptor will cause crashes or undefined behavior.

### 2. Always Free Resources

```c
// Cleanup when done
if (uart_desc) {
    no_os_uart_remove(uart_desc);
    uart_desc = NULL;
}
```

**Why:** Prevents memory leaks and ensures UART peripheral is properly disabled.

### 3. Validate Return Values

```c
int ret = no_os_uart_init(&uart_desc, &uart_init);
if (ret) {
    // Handle error appropriately
    return ret;
}

// Check write return value
ret = no_os_uart_write(uart_desc, data, len);
if (ret < 0) {
    printf("UART write error: %d\n", ret);
}
```

**Why:** Errors can occur (invalid parameters, hardware failures, bus errors).

## Baud Rate Selection

### 4. Use Appropriate Baud Rate

**Debug/logging:** 115200 baud
```c
.baud_rate = 115200,  // Fast enough for real-time debug
```

**Industrial protocols:** 9600-19200 baud
```c
.baud_rate = 9600,    // Modbus RTU standard
```

**High-speed logging:** 250000+ baud
```c
.baud_rate = 250000,  // For fast sensor logging
```

**Why:** Higher baud = faster but shorter cable distance. Balance speed vs reliability.

### 5. Verify Baud Rate Divisor

```c
// Check if baud rate is achievable
// divisor = peripheral_clock / (oversampling * baud_rate)
uint32_t divisor = 48000000 / (16 * 115200);
// divisor should be integer with < 2% error
```

**Why:** Rounding errors at unusual baud rates can cause communication failures.

## Serial Settings

### 6. Match Serial Settings on Both Sides

```c
// Transmitter configuration
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_NO,
.stop = NO_OS_UART_STOP_1_BIT,

// Receiver MUST have IDENTICAL settings
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_NO,
.stop = NO_OS_UART_STOP_1_BIT,
```

**Why:** Mismatched settings cause garbled data or no communication.

### 7. Use Standard 8N1 When Possible

```c
.size = NO_OS_UART_CS_8,        // 8 data bits
.parity = NO_OS_UART_PAR_NO,    // No parity
.stop = NO_OS_UART_STOP_1_BIT,  // 1 stop bit
```

**Why:** Most common configuration, universally supported, maximum throughput.

### 8. Use Parity for Error Detection

```c
// For industrial/critical applications
.parity = NO_OS_UART_PAR_EVEN,  // Error detection
```

**Why:** Detects single-bit errors on noisy lines. Required for Modbus RTU.

## I/O Mode Selection

### 9. Use Blocking I/O When Possible

```c
.asynchronous_rx = false,  // Simple, reliable

// Blocking read - waits for data
int bytes = no_os_uart_read(uart_desc, buffer, len);
```

**Why:** Simpler code, more reliable, easier to debug.

### 10. Use Async RX for CLI/Streaming

```c
.asynchronous_rx = true,   // For interactive applications
.irq_id = 2,               // Specify IRQ

// Non-blocking read - returns immediately
int bytes = no_os_uart_read_nonblocking(uart_desc, buffer, len);
```

**Why:** Allows application to process other tasks while waiting for data.

## Error Handling

### 11. Check for Errors Regularly

```c
uint32_t errors = no_os_uart_get_errors(uart_desc);
if (errors > 0) {
    printf("UART errors: %u\n", errors);
    // Handle errors: log, reset UART, notify user
}
```

**Why:** Detects overrun, framing, and parity errors that indicate communication issues.

### 12. Handle NULL Pointers

```c
if (!uart_desc) {
    return -ENODEV;
}

if (!data || bytes_number == 0) {
    return -EINVAL;
}
```

**Why:** Prevents crashes and provides clear error codes.

### 13. Add Timeouts to Blocking Reads

```c
// Platform implementation should include timeout
int32_t myplatform_uart_read(struct no_os_uart_desc *desc,
                              uint8_t *data, uint32_t bytes_number)
{
    uint32_t start_time = get_timestamp_ms();
    uint32_t idx = 0;
    
    while (idx < bytes_number) {
        // Check timeout
        if ((get_timestamp_ms() - start_time) > UART_TIMEOUT_MS) {
            return -ETIMEDOUT;
        }
        
        if (HAL_UART_HasData(desc->device_id)) {
            data[idx++] = HAL_UART_ReadByte(desc->device_id);
        }
    }
    
    return idx;
}
```

**Why:** Prevents infinite blocking on lost connections or hardware failures.

## Buffer Management

### 14. Monitor RX FIFO in Async Mode

```c
// Check available space in RX FIFO
if (desc->rx_fifo) {
    uint32_t available = lf256fifo_len(desc->rx_fifo);
    if (available > 200) {  // Near full
        printf("Warning: RX FIFO near full\n");
    }
}
```

**Why:** Prevents buffer overflow and data loss.

### 15. Process Data Promptly

```c
// In main loop, frequently drain RX buffer
while (1) {
    uint8_t buffer[64];
    int bytes = no_os_uart_read_nonblocking(uart_desc, buffer, 64);
    
    if (bytes > 0) {
        process_data(buffer, bytes);  // Process immediately
    }
}
```

**Why:** Prevents RX FIFO overflow and ensures timely response.

## Multi-Threading Safety

### 16. Protect Shared Access

```c
// For multi-threaded systems
no_os_mutex_lock(uart_desc->mutex);
no_os_uart_write(uart_desc, data, len);
no_os_mutex_unlock(uart_desc->mutex);
```

**Why:** Prevents race conditions when multiple threads access same UART.

### 17. Don't Share UART Descriptors Carelessly

```c
// Good: Each module uses separate UART
struct no_os_uart_desc *debug_uart;    // Module A
struct no_os_uart_desc *modbus_uart;   // Module B

// Bad: Multiple modules sharing same UART
// Requires careful synchronization
```

**Why:** Simplifies code and avoids synchronization issues.

## Line Endings

### 18. Use Consistent Line Endings

```c
// Unix style (preferred for embedded)
printf("Message\n");

// Windows style (if required by host)
printf("Message\r\n");
```

**Why:** Inconsistent line endings cause formatting issues in terminal applications.

### 19. Handle Both \r and \n in CLI

```c
// Accept both CR and LF as command terminator
if (char_received == '\n' || char_received == '\r') {
    cmd_buffer[cmd_index] = '\0';
    process_command(cmd_buffer);
    cmd_index = 0;
}
```

**Why:** Different terminals send different line endings (Unix vs Windows).

## Documentation

### 20. Document UART Assignments

```c
// Document which UART is used for what purpose
// UART0: Debug console (115200, 8N1)
// UART1: Modbus RTU (9600, 8E1)
// UART2: GPS receiver (9600, 8N1, async RX)

struct no_os_uart_desc *debug_uart;   // UART0
struct no_os_uart_desc *modbus_uart;  // UART1
struct no_os_uart_desc *gps_uart;     // UART2
```

**Why:** Makes code maintainable and prevents configuration errors.

### 21. Document Baud Rate Requirements

```c
// Document why specific baud rate chosen
.baud_rate = 250000,  // High speed for oscilloscope data logging
                      // (requires short cable < 5m)
```

**Why:** Helps future developers understand constraints and requirements.

## Platform-Specific Considerations

### 22. Configure Platform Extras Properly

```c
// Maxim platform
struct max_uart_init_param maxim_extra = {
    .flow_control = true,   // Required for high-speed transfers
    .dma_enabled = false,   // DMA not needed for debug output
};

struct no_os_uart_init_param uart_init = {
    // ... standard parameters ...
    .extra = &maxim_extra,
};
```

**Why:** Platform-specific features can improve performance and reliability.

### 23. Verify Platform Support

```c
// Check if platform supports requested features
if (baud_rate > platform_max_baud) {
    printf("Baud rate %u not supported\n", baud_rate);
    return -ENOTSUP;
}
```

**Why:** Not all platforms support all baud rates or features.

## Testing and Debugging

### 24. Test with Loopback First

```c
// Connect TX to RX for loopback testing
uint8_t test_data[] = "Hello";
no_os_uart_write(uart_desc, test_data, 5);

uint8_t rx_buffer[5];
int bytes = no_os_uart_read(uart_desc, rx_buffer, 5);

if (memcmp(test_data, rx_buffer, 5) == 0) {
    printf("Loopback test passed\n");
}
```

**Why:** Verifies UART hardware and driver before testing external connections.

### 25. Use Oscilloscope for Debugging

```c
// Verify baud rate accuracy with oscilloscope
// Measure bit width on TX line
// For 115200 baud: 1 bit = 8.68 μs
```

**Why:** Hardware issues (wrong baud rate, bad connections) can't be debugged in software.

### 26. Enable Verbose Debug Output

```c
#ifdef UART_DEBUG
    printf("UART init: device_id=%u, baud=%u\n",
           uart_init.device_id, uart_init.baud_rate);
#endif
```

**Why:** Helps identify configuration issues during development.

## Performance Optimization

### 27. Use DMA for High-Speed Transfers

```c
// Enable DMA for transfers > 64 bytes
struct max_uart_init_param maxim_extra = {
    .dma_enabled = true,    // Offload CPU
};
```

**Why:** Reduces CPU load and enables higher sustained data rates.

### 28. Batch Writes When Possible

```c
// Good: Single write
char message[64];
int len = snprintf(message, sizeof(message), "Temp: %d\n", temp);
no_os_uart_write(uart_desc, (uint8_t *)message, len);

// Bad: Multiple small writes
no_os_uart_write(uart_desc, (uint8_t *)"Temp: ", 6);
no_os_uart_write(uart_desc, temp_str, strlen(temp_str));
no_os_uart_write(uart_desc, (uint8_t *)"\n", 1);
```

**Why:** Reduces overhead from multiple function calls and interrupt handling.

## Common Anti-Patterns to Avoid

### 29. Don't Use UART in ISR

```c
// BAD: UART operations in interrupt handler
void timer_isr(void)
{
    // DON'T DO THIS
    printf("Timer fired\n");  // UART write in ISR
}

// GOOD: Set flag, process in main loop
volatile bool timer_fired = false;

void timer_isr(void)
{
    timer_fired = true;
}

void main_loop(void)
{
    if (timer_fired) {
        printf("Timer fired\n");  // Safe in main context
        timer_fired = false;
    }
}
```

**Why:** UART operations can block, causing ISR to run too long.

### 30. Don't Ignore Platform Differences

```c
// BAD: Assuming all platforms behave identically
// GOOD: Check platform capabilities
if (platform_supports_feature(UART_FEATURE_9BIT)) {
    uart_init.size = NO_OS_UART_CS_9;
} else {
    uart_init.size = NO_OS_UART_CS_8;
}
```

**Why:** Platform implementations have different capabilities and limitations.

## Summary

**Key best practices:**
1. Always initialize and cleanup properly
2. Verify return values for errors
3. Match baud rate and serial settings on both sides
4. Use blocking I/O when possible (simpler)
5. Use async RX for CLI/interactive applications
6. Check for errors regularly with get_errors()
7. Add timeouts to prevent infinite blocking
8. Monitor RX FIFO to prevent overflow
9. Document UART assignments and requirements
10. Test with loopback before external connections

**Remember:**
- Higher baud rate = shorter cable distance
- Standard 8N1 is most common and compatible
- Async RX requires interrupt and FIFO setup
- Platform extras provide advanced features
- Error handling prevents silent failures
- Proper cleanup prevents resource leaks
