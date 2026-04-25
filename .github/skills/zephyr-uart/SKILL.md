---
name: zephyr-uart
description: 'Complete guide to Zephyr UART drivers for serial communication. Use when implementing UART drivers, configuring baud rates and serial settings (parity, stop bits, data bits), sending and receiving data in polling/interrupt/async modes, handling flow control (RTS/CTS), implementing RS-485 support, or debugging UART communication issues.'
---

# Zephyr UART Driver Development

This skill provides comprehensive understanding of the Zephyr UART (Universal Asynchronous Receiver-Transmitter) driver subsystem.

## 📚 For AI Assistant: When to Read Reference Files

This skill is modular. The main file provides quick reference. Use the Read tool to load detailed docs when needed:

**Triggers to read reference/implementation.md**:
- User asks: "implement UART driver", "step by step", "poll_in", "poll_out", "fifo_fill"
- Questions about: driver API, register access, IRQ handlers, async events
- User mentions: implementing driver functions, hardware register mapping
- Need: detailed implementation steps (Steps 1-8) with complete code

**Triggers to read reference/devicetree-bindings.md**:
- User mentions: "devicetree", "binding", "uart-controller", "DTS", "overlay"
- Questions about: DT properties, current-speed, parity, stop-bits, flow control
- User asks: "how to define UART binding", "devicetree example"
- Need: binding patterns and examples

**Triggers to read reference/api-usage.md**:
- User asks: "how to use UART", "polling mode", "interrupt mode", "async mode"
- Questions about: uart_poll_in, uart_poll_out, uart_irq_callback_set, uart_tx, uart_rx_enable
- Need: application-side UART usage examples (4 patterns)

**Triggers to read reference/best-practices.md**:
- User asks: "best practices", "choose API", "buffer management", "error handling"
- Questions about: FIFO handling, flow control, device ready check
- Need: design patterns (6 detailed patterns)

**Triggers to read reference/debugging.md**:
- User says: "not working", "wrong data", "debugging", "UART issue", "overrun"
- Build/runtime errors with UART
- Questions about: baud rate mismatch, signal levels, loopback testing
- Need: debugging steps (6 detailed tips)

---

## When to Use This Skill

Use this skill when you need to:
- Implement UART controller drivers for Zephyr
- Configure UART parameters (baud rate, parity, stop bits, data bits)
- Implement polling mode UART (blocking character I/O)
- Implement interrupt-driven UART (FIFO-based with callbacks)
- Implement async UART (DMA-based event-driven API)
- Support hardware flow control (RTS/CTS, DTR/DSR)
- Implement RS-485 half-duplex support
- Handle UART errors (overrun, parity, framing, break)
- Debug UART communication issues

## What is UART?

**UART (Universal Asynchronous Receiver-Transmitter)** is an asynchronous serial communication protocol that transmits data without a shared clock signal.

### Key Concepts

- **Asynchronous**: No shared clock between transmitter and receiver
- **Serial**: Data transmitted one bit at a time
- **Two-Wire**: TX (transmit) and RX (receive) lines (minimum)
- **Optional Flow Control**: RTS/CTS or DTR/DSR for handshaking
- **Frame Format**: Start bit + Data bits + Parity bit (optional) + Stop bits

### UART Frame Format

```
      Start  Data Bits      Parity  Stop
Idle  Bit    (5-9 bits)     (opt)   Bits   Idle
─┐   ┌──────────────────┐   ┌─┐   ┌────  ─────
 └───┘ LSB          MSB └───┘ └───┘

Common configuration: 8N1 (8 data bits, No parity, 1 stop bit)
```

### UART Parameters

- **Baud Rate**: Transmission speed in bits per second (e.g., 9600, 115200)
- **Parity**: Error checking (None, Even, Odd, Mark, Space)
- **Stop Bits**: End-of-frame marker (0.5, 1, 1.5, 2 bits)
- **Data Bits**: Bits per character (5, 6, 7, 8, 9 bits)
- **Flow Control**: Handshaking (None, RTS/CTS, DTR/DSR, RS-485)

## Architecture Overview

```
Application
    ↓
UART API (uart.h)
    ├─ Polling (poll_in, poll_out)
    ├─ Interrupt-driven (fifo_fill, fifo_read, IRQ callbacks)
    └─ Async (uart_tx, uart_rx_enable, event callbacks)
    ↓
UART Driver (uart_*.c)
    ↓
Hardware UART Controller
    ↓
TX/RX Lines (± RTS/CTS)
```

## File Structure (Quick Reference)

- **Driver**: `drivers/serial/uart_<chip>.c`
- **Binding**: `dts/bindings/serial/<vendor>,<chip>-uart.yaml`
- **Kconfig**: Update `drivers/serial/Kconfig`

## Core Data Structures (Quick Reference)

| Structure | Purpose | Key Members |
|-----------|---------|-------------|
| **uart_config** | UART configuration | `baudrate`, `parity`, `stop_bits`, `data_bits`, `flow_ctrl` |
| **uart_event** | Async event | `type` (TX_DONE, RX_RDY, RX_BUF_REQUEST, ERROR), `data` (buffer, length, errors) |
| **uart_driver_api** | Driver API table | `poll_in()`, `poll_out()`, `configure()`, `config_get()`, `fifo_fill()`, `fifo_read()`, `irq_*()`, `tx()`, `rx_enable()` |

**See**: [reference/implementation.md](reference/implementation.md) for detailed structures and implementation.

## UART API Modes (Quick Reference)

| Mode | Use Case | Key Functions | DMA |
|------|----------|---------------|-----|
| **Polling** | Simple, low-throughput | `uart_poll_in()`, `uart_poll_out()` | No |
| **Interrupt-Driven** | Moderate throughput, FIFO-based | `uart_fifo_fill()`, `uart_fifo_read()`, `uart_irq_callback_set()` | No |
| **Async** | High throughput, event-driven | `uart_tx()`, `uart_rx_enable()`, `uart_callback_set()` | Yes |

## Quick Start Workflow

1. **Define Register Map** and bit definitions
2. **Define Config and Data Structures** with hardware base address, pinctrl, buffers
3. **Implement Polling API** – `poll_in()`, `poll_out()`
4. **Implement Configuration API** – `configure()`, `config_get()`
5. **Implement Interrupt-Driven API** (Optional) – `fifo_fill()`, `fifo_read()`, IRQ handlers
6. **Define API Structure** with function pointers
7. **Implement Init Function** – Initialize hardware, set defaults
8. **Device Instantiation Macro** – Register driver

**For detailed step-by-step implementation**: Read [reference/implementation.md](reference/implementation.md)

## Key Patterns

### UART Configuration

```c
struct uart_config cfg = {
    .baudrate = 115200,
    .parity = UART_CFG_PARITY_NONE,
    .stop_bits = UART_CFG_STOP_BITS_1,
    .data_bits = UART_CFG_DATA_BITS_8,
    .flow_ctrl = UART_CFG_FLOW_CTRL_NONE
};
uart_configure(uart_dev, &cfg);
```

### Polling Mode

```c
// Blocking write
char c = 'A';
uart_poll_out(uart_dev, c);

// Non-blocking read
char c;
if (uart_poll_in(uart_dev, &c) == 0) {
    // Character received
}
```

### Interrupt-Driven Mode

```c
static void uart_callback(const struct device *dev, void *user_data)
{
    if (uart_irq_rx_ready(dev)) {
        uint8_t buf[32];
        int len = uart_fifo_read(dev, buf, sizeof(buf));
        // Process received data
    }
    if (uart_irq_tx_ready(dev)) {
        // Fill TX FIFO
        uart_fifo_fill(dev, tx_data, tx_len);
    }
}

uart_irq_callback_set(uart_dev, uart_callback);
uart_irq_rx_enable(uart_dev);
```

### Async Mode

```c
static void uart_event_handler(const struct device *dev,
                               struct uart_event *evt, void *user_data)
{
    switch (evt->type) {
    case UART_TX_DONE:
        // TX complete
        break;
    case UART_RX_RDY:
        // Data in evt->data.rx.buf, length evt->data.rx.len
        break;
    case UART_RX_BUF_REQUEST:
        // Provide new buffer
        uart_rx_buf_rsp(dev, next_buf, next_buf_len);
        break;
    }
}

uart_callback_set(uart_dev, uart_event_handler, NULL);
uart_rx_enable(uart_dev, rx_buf, rx_buf_len, TIMEOUT);
uart_tx(uart_dev, tx_buf, tx_len, TIMEOUT);
```

## Common Patterns and Best Practices (Summary)

✅ **DO**:
- Always check device ready state before use
- Choose the right API for your use case (polling vs interrupt vs async)
- Handle FIFO properly in interrupt mode (drain on RX, fill on TX)
- Provide double-buffering in async mode
- Handle all error types (overrun, parity, framing, break)
- Use flow control for reliable high-speed communication
- Configure correct baud rate, parity, stop bits
- Test with loopback mode

❌ **DON'T**:
- Don't block in IRQ callbacks
- Don't use polling mode for high-throughput applications
- Don't ignore overrun errors
- Don't forget to enable RX interrupts after callback setup
- Don't assume baud rate accuracy (check tolerance)
- Don't modify RX buffers while async RX is active

**See**: [reference/best-practices.md](reference/best-practices.md) for detailed patterns with examples.

## References

**Zephyr Documentation**:
- **UART API**: `zephyr/include/zephyr/drivers/uart.h`
- **UART Drivers**: `zephyr/drivers/serial/`
- **Bindings**: `zephyr/dts/bindings/serial/`

**Example Drivers**:
- **MAX32 UART**: `drivers/serial/uart_max32.c`
- **nRF UARTE**: `drivers/serial/uart_nrfx_uarte.c`
- **STM32 UART**: `drivers/serial/uart_stm32.c`

**Reference Guides**:
- [reference/implementation.md](reference/implementation.md) – Detailed driver implementation (Steps 1-8)
- [reference/devicetree-bindings.md](reference/devicetree-bindings.md) – Binding patterns and examples
- [reference/api-usage.md](reference/api-usage.md) – Application usage (4 modes)
- [reference/best-practices.md](reference/best-practices.md) – Design patterns (6 detailed)
- [reference/debugging.md](reference/debugging.md) – Troubleshooting guide (6 tips)

## Summary Checklist

### Driver Implementation
- [ ] Register map defined with bit masks
- [ ] Config structure with base address and pinctrl
- [ ] Data structure with runtime state
- [ ] `poll_in()` implemented (polling RX)
- [ ] `poll_out()` implemented (polling TX)
- [ ] `configure()` implemented (set baud, parity, stop bits)
- [ ] `config_get()` implemented (read current config)
- [ ] `fifo_fill()` / `fifo_read()` implemented (if interrupt mode)
- [ ] IRQ handlers implemented (if interrupt mode)
- [ ] `tx()` / `rx_enable()` implemented (if async mode)
- [ ] API structure defined with function pointers
- [ ] Init function initializes hardware
- [ ] Device instantiation macro

### Devicetree and Build
- [ ] Binding created (include uart-controller.yaml)
- [ ] Properties defined (current-speed, parity, stop-bits)
- [ ] Pinctrl integration
- [ ] Flow control pins (if supported)
- [ ] Kconfig entry with dependencies
- [ ] Board DTS defines UART

### Testing
- [ ] Configuration works (baud rate, parity, stop bits, data bits)
- [ ] Polling mode works (poll_in, poll_out)
- [ ] Interrupt-driven mode works (FIFO callbacks)
- [ ] Async mode works (DMA events)
- [ ] Error handling works (overrun, parity, framing)
- [ ] Flow control works (if supported)
- [ ] Loopback test passes
