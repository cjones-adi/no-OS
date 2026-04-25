# UART Troubleshooting Guide

Common UART issues, symptoms, causes, and solutions.

## No Data Received

### Symptom
Transmitter sends data, but receiver gets nothing. Read operations timeout or return 0 bytes.

### Possible Causes and Solutions

**1. Baud rate mismatch**
```c
// Verify both sides use IDENTICAL baud rate
// Transmitter
.baud_rate = 115200,

// Receiver (MUST match)
.baud_rate = 115200,
```
**Solution:** Ensure exact baud rate match on both TX and RX.

**2. Cable connections wrong**
```
Correct wiring:
TX (transmitter) → RX (receiver)
RX (transmitter) → TX (receiver)
GND → GND (CRITICAL - must be connected)

Common mistake:
TX → TX, RX → RX (won't work)
```
**Solution:** Connect TX to RX and RX to TX. Always connect ground.

**3. Serial format mismatch**
```c
// Both sides MUST match
.size = NO_OS_UART_CS_8,
.parity = NO_OS_UART_PAR_NO,
.stop = NO_OS_UART_STOP_1_BIT,
```
**Solution:** Verify 8N1 (or configured format) on both TX and RX.

**4. Wrong I/O mode**
```c
// If using blocking read with async RX disabled
.asynchronous_rx = false,
int bytes = no_os_uart_read(uart_desc, buffer, 128);
// May block forever if no data

// If expecting async but not configured
.asynchronous_rx = false,  // ← Missing interrupt setup
int bytes = no_os_uart_read_nonblocking(uart_desc, buffer, 128);
// Will always return 0 (no FIFO)
```
**Solution:** Use async RX (with IRQ) for non-blocking reads, or blocking read for polling.

**5. IRQ not enabled**
```c
// Async RX requires IRQ configuration
.asynchronous_rx = true,
.irq_id = 2,  // ← Must specify valid IRQ
```
**Solution:** Verify IRQ ID is correct and interrupt handler is registered.

**6. UART not initialized**
```c
struct no_os_uart_desc *uart_desc;  // NULL

// Forgot to initialize
// no_os_uart_init(&uart_desc, &uart_init);

// Using uninitialized descriptor
no_os_uart_read(uart_desc, buffer, 128);  // CRASH or undefined
```
**Solution:** Always call `no_os_uart_init()` before using UART.

**7. Cable too long for baud rate**
```c
// 115200 baud over 50m cable - won't work reliably
.baud_rate = 115200,  // Max ~15m cable

// Use lower baud for long cables
.baud_rate = 9600,    // Max ~300m cable
```
**Solution:** Reduce baud rate or shorten cable.

## Garbled Data

### Symptom
Receiver gets data, but it's corrupted, random characters, or unreadable.

### Possible Causes and Solutions

**1. Baud rate mismatch (most common)**
```c
// Transmitter: 115200
// Receiver: 9600
// Result: Garbled data

// FIX: Match baud rates
.baud_rate = 115200,  // Both sides
```
**Solution:** Use oscilloscope to verify actual baud rate on TX line.

**2. Parity mismatch**
```c
// Transmitter: No parity
.parity = NO_OS_UART_PAR_NO,

// Receiver: Even parity
.parity = NO_OS_UART_PAR_EVEN,

// Result: Every byte corrupted
```
**Solution:** Match parity settings on both sides.

**3. Data bits mismatch**
```c
// Transmitter: 8 bits
.size = NO_OS_UART_CS_8,

// Receiver: 7 bits
.size = NO_OS_UART_CS_7,

// Result: High bit lost or corrupted
```
**Solution:** Match data bits (usually 8).

**4. Stop bits mismatch**
```c
// Transmitter: 1 stop bit
.stop = NO_OS_UART_STOP_1_BIT,

// Receiver: 2 stop bits
.stop = NO_OS_UART_STOP_2_BIT,

// Result: Occasional framing errors
```
**Solution:** Match stop bits (usually 1).

**5. Electrical noise on wire**
```
Symptoms:
- Random bit flips
- Intermittent corruption
- Errors increase with cable length
```
**Solution:** 
- Use shielded cable
- Shorten cable length
- Reduce baud rate
- Add ferrite beads
- Improve grounding

**6. Voltage level mismatch**
```
RS-232: ±12V levels
TTL: 0V/3.3V or 0V/5V levels

Connecting RS-232 to TTL directly: DAMAGE
```
**Solution:** Use level shifter (MAX3232, etc.) between RS-232 and TTL.

## Transmission Slow

### Symptom
Data transmits, but slower than expected. Low throughput.

### Possible Causes and Solutions

**1. Baud rate too low**
```c
.baud_rate = 9600,    // Only ~960 bytes/sec throughput

// Increase if cable allows
.baud_rate = 115200,  // ~11.5 kB/sec throughput
```
**Solution:** Increase baud rate if cable distance permits.

**2. Blocking on full buffer**
```c
// Writing faster than transmit can keep up
while (1) {
    no_os_uart_write(uart_desc, data, 1024);  // Blocks until sent
}
```
**Solution:** Use non-blocking writes or reduce data rate.

**3. DMA not enabled**
```c
// CPU busy-waits for each byte
struct max_uart_init_param extra = {
    .dma_enabled = false,  // ← CPU overhead
};

// Enable DMA for high-speed
.dma_enabled = true,  // Offload CPU
```
**Solution:** Enable DMA for transfers > 64 bytes.

**4. System interrupt latency**
```c
// Long-running ISRs block UART interrupt
void slow_isr(void) {
    // 10ms of processing
    // UART ISR can't run - data lost
}
```
**Solution:** Keep ISRs short, process data in main loop.

**5. Flow control slowing transmission**
```c
// Receiver asserting RTS (not ready)
// Transmitter must wait

// Check if receiver can keep up
```
**Solution:** Optimize receiver processing, increase baud rate, or disable flow control if not needed.

## RX Buffer Overflow

### Symptom
Data lost, error count increases, `no_os_uart_get_errors()` returns non-zero.

### Possible Causes and Solutions

**1. Processing data too slowly**
```c
// Main loop not draining FIFO fast enough
while (1) {
    // Long processing
    process_data();  // Takes 100ms
    
    // Only check UART once per 100ms - overflow!
    int bytes = no_os_uart_read_nonblocking(uart_desc, buffer, 64);
}
```
**Solution:** Check UART more frequently, reduce processing time.

**2. Async RX not enabled**
```c
// Without async RX, no background buffering
.asynchronous_rx = false,  // ← Data lost if not polling fast enough

// Enable async RX
.asynchronous_rx = true,
.irq_id = 2,
```
**Solution:** Enable async RX for automatic background buffering.

**3. RX FIFO too small**
```c
// Default 256-byte FIFO may not be enough for burst data

// Solution: Increase FIFO size or process more frequently
```
**Solution:** Process data more frequently or increase FIFO size if platform allows.

**4. High baud rate, slow processing**
```c
// 115200 baud = ~11.5 kB/sec
// Processing takes 50ms = 575 bytes arrive during processing
// Default 256-byte FIFO overflows
```
**Solution:** Reduce baud rate, increase processing speed, or use flow control.

**5. No error checking**
```c
// Errors occurring but not detected
uint32_t errors = no_os_uart_get_errors(uart_desc);
if (errors > 0) {
    printf("UART errors: %u\n", errors);
}
```
**Solution:** Regularly check for errors with `get_errors()`.

## UART Won't Initialize

### Symptom
`no_os_uart_init()` returns error code.

### Possible Causes and Solutions

**1. Invalid device ID**
```c
.device_id = 5,  // Platform only has UART 0-2

// Check platform documentation
.device_id = 0,  // Valid
```
**Solution:** Use valid device ID for platform (usually 0-2).

**2. Platform ops missing**
```c
.platform_ops = NULL,  // ← Missing

.platform_ops = &max_uart_ops,  // Correct
```
**Solution:** Always specify platform ops.

**3. Invalid baud rate**
```c
// Very high rates may not be supported
.baud_rate = 5000000,  // May fail on some platforms

// Use standard rate
.baud_rate = 115200,   // Widely supported
```
**Solution:** Use standard baud rates (9600, 115200, etc.).

**4. IRQ ID invalid**
```c
// Async RX with wrong IRQ
.asynchronous_rx = true,
.irq_id = 99,  // ← Invalid IRQ number

// Check platform IRQ table
.irq_id = 2,   // Valid for UART0 on this platform
```
**Solution:** Verify IRQ number from platform documentation.

**5. Memory allocation failed**
```c
// Heap exhausted
// no_os_uart_init() allocates descriptor

// Check heap size
printf("Free heap: %u\n", get_free_heap());
```
**Solution:** Increase heap size or free unused memory.

**6. UART already initialized**
```c
// Double initialization
no_os_uart_init(&uart_desc, &uart_init);  // First time OK
no_os_uart_init(&uart_desc, &uart_init);  // May fail or leak

// Always remove before re-initializing
no_os_uart_remove(uart_desc);
no_os_uart_init(&uart_desc, &uart_init);
```
**Solution:** Remove existing descriptor before re-initializing.

## Printf Not Working

### Symptom
`printf()` produces no output or crashes.

### Possible Causes and Solutions

**1. Forgot to call no_os_uart_stdio()**
```c
no_os_uart_init(&uart_desc, &uart_init);

// Printf won't work yet
printf("Test\n");  // No output

// MUST redirect stdio
no_os_uart_stdio(uart_desc);

// Now printf works
printf("Test\n");  // Output to UART
```
**Solution:** Call `no_os_uart_stdio()` after initialization.

**2. UART not initialized**
```c
no_os_uart_stdio(uart_desc);  // uart_desc is NULL - CRASH

// Initialize first
no_os_uart_init(&uart_desc, &uart_init);
no_os_uart_stdio(uart_desc);
```
**Solution:** Initialize UART before calling stdio redirection.

**3. Buffering issues**
```c
// Output may be buffered
printf("Test");  // No newline - may not flush

// Add newline or flush
printf("Test\n");        // Newline flushes
fflush(stdout);          // Manual flush
```
**Solution:** Add `\n` to printf or call `fflush(stdout)`.

## Interrupt Not Firing

### Symptom
Async RX configured, but interrupt handler never called. No data buffered.

### Possible Causes and Solutions

**1. IRQ not enabled**
```c
.asynchronous_rx = true,
.irq_id = 2,

// Platform implementation must enable IRQ
// Check platform init code
```
**Solution:** Verify platform implementation enables RX interrupt.

**2. Wrong IRQ handler name**
```c
// IRQ handler name must match platform vector table
void UART_RX_IRQHandler(void)  // ← Must match exactly
{
    // Handler code
}
```
**Solution:** Check platform vector table for correct handler name.

**3. Global interrupts disabled**
```c
// Interrupts disabled globally
__disable_irq();

// Enable global interrupts
__enable_irq();
```
**Solution:** Ensure global interrupts are enabled.

**4. IRQ priority too low**
```c
// Other interrupts blocking UART IRQ
// Increase UART IRQ priority

NVIC_SetPriority(UART_IRQn, 1);  // Higher priority
```
**Solution:** Adjust IRQ priority if other ISRs are blocking.

## Debugging Techniques

### 1. Oscilloscope Verification

```c
// Verify baud rate on TX line
// For 115200 baud: 1 bit = 8.68 μs
// Measure bit width with oscilloscope
```

### 2. Loopback Testing

```c
// Connect TX to RX physically
uint8_t test_data[] = "Test";
no_os_uart_write(uart_desc, test_data, 4);

uint8_t rx_buffer[4];
int bytes = no_os_uart_read(uart_desc, rx_buffer, 4);

if (memcmp(test_data, rx_buffer, 4) == 0)
    printf("Loopback OK\n");
else
    printf("Loopback FAILED\n");
```

### 3. Enable Debug Output

```c
#define UART_DEBUG

#ifdef UART_DEBUG
    printf("UART init: device=%u, baud=%u\n",
           uart_init.device_id, uart_init.baud_rate);
#endif
```

### 4. Check Error Counters

```c
// Periodically check for errors
uint32_t errors = no_os_uart_get_errors(uart_desc);
if (errors > 0) {
    printf("Errors detected: %u\n", errors);
    // Framing, parity, or overrun errors
}
```

### 5. Test with Known-Good Device

```c
// Test with USB-to-serial adapter
// Use terminal program (PuTTY, TeraTerm)
// Verify settings match (baud, 8N1)
```

## Common Error Codes

| Error Code | Meaning | Common Cause |
|------------|---------|--------------|
| `-EINVAL` | Invalid parameter | NULL pointer, zero length |
| `-ENODEV` | No device | UART not initialized |
| `-EIO` | I/O error | Hardware failure, bus error |
| `-ENOMEM` | Out of memory | Heap exhausted |
| `-ETIMEDOUT` | Timeout | No data received, blocking read timeout |
| `-EBUSY` | Device busy | UART already in use |
| `-ENOTSUP` | Not supported | Feature not available on platform |

## Quick Diagnostic Checklist

- [ ] Baud rate matches on TX and RX
- [ ] Serial format (8N1) matches on both sides
- [ ] TX connected to RX, RX connected to TX
- [ ] Ground (GND) connected between devices
- [ ] UART initialized successfully (`no_os_uart_init()` returned 0)
- [ ] Async RX enabled if using non-blocking reads
- [ ] IRQ ID correct for async RX
- [ ] Platform ops specified
- [ ] Cable length appropriate for baud rate
- [ ] Voltage levels compatible (TTL vs RS-232)
- [ ] No electrical noise or interference
- [ ] Error counters checked (`no_os_uart_get_errors()`)

## Summary

**Most common issues:**
1. Baud rate mismatch
2. Wrong cable connections (TX-TX instead of TX-RX)
3. Serial format mismatch (8N1 vs other)
4. Forgot to initialize UART
5. Async RX not configured for non-blocking reads

**First steps to debug:**
1. Verify baud rate with oscilloscope
2. Check cable connections (TX-RX, RX-TX, GND)
3. Test with loopback (TX connected to RX)
4. Enable debug output
5. Check error counters
6. Test with known-good device (USB-serial adapter)
