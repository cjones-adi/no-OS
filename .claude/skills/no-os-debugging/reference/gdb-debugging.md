# GDB and JTAG/SWD Debugging

Complete guide to using JTAG/SWD debugging with platform-specific tools and GDB for no-OS embedded applications.

---

## JTAG/SWD Debugging Overview

JTAG/SWD debugging provides:
- Breakpoint debugging (step through code)
- Variable inspection at runtime
- Register viewing (peripheral and core)
- Memory inspection
- Stack trace analysis on crashes
- Flash programming and reset

---

## Platform-Specific Debugging

### Debug Configuration Files

**Location**: `tools/scripts/platform/{PLATFORM}/debug_config/`

Debug configurations are typically stored as JSON files for VSCode or Eclipse integration.

---

### Example: Raspberry Pi Pico (RP2040)

**Debug Configuration** (`.vscode/launch.json` or debug_config):
```json
{
    "name": "Cortex Debug",
    "cwd": "${workspaceRoot}",
    "executable": "./build/app",
    "request": "launch",
    "type": "cortex-debug",
    "servertype": "openocd",
    "device": "RP2040",
    "configFiles": ["interface/cmsis-dap.cfg", "target/rp2040.cfg"],
    "svdFile": "${env:PICO_SDK_PATH}/src/rp2040/hardware_regs/rp2040.svd",
    "runToMain": true,
    "targetId": "RP2040_M0_0"
}
```

**Key Settings**:
- `executable`: Path to compiled .elf file (with debug symbols)
- `servertype`: Debug server (openocd, jlink, stlink, pyocd)
- `svdFile`: System View Description for register inspection
- `runToMain`: Break at main() entry automatically
- `device`: Target device name
- `configFiles`: OpenOCD configuration files

---

### Example: STM32 Platform

**OpenOCD Configuration**:
```json
{
    "name": "STM32 Debug",
    "type": "cortex-debug",
    "servertype": "openocd",
    "device": "STM32F407VG",
    "configFiles": [
        "interface/stlink.cfg",
        "target/stm32f4x.cfg"
    ],
    "svdFile": "STM32F407.svd",
    "executable": "./build/app.elf",
    "runToMain": true
}
```

---

### Example: Maxim Platform (MAX32xxx)

**OpenOCD Configuration**:
```json
{
    "name": "MAX32 Debug",
    "type": "cortex-debug",
    "servertype": "openocd",
    "device": "MAX32690",
    "configFiles": [
        "interface/cmsis-dap.cfg",
        "target/max32690.cfg"
    ],
    "svdFile": "MAX32690.svd",
    "executable": "./build/app.elf",
    "runToMain": true
}
```

---

## GDB Debugging Workflow

### Starting a Debug Session

**1. Build with Debug Symbols**:
```makefile
# Ensure debug symbols enabled
CFLAGS += -g3 -O0
```

**2. Start Debug Server** (OpenOCD, JLink, etc.):
```bash
# OpenOCD
openocd -f interface/cmsis-dap.cfg -f target/stm32f4x.cfg

# JLink
JLinkGDBServer -device STM32F407VG -if SWD -speed 4000
```

**3. Launch GDB**:
```bash
arm-none-eabi-gdb build/app.elf

# Connect to debug server
(gdb) target remote localhost:3333

# Load program to device
(gdb) load

# Reset and halt
(gdb) monitor reset halt

# Run to main
(gdb) break main
(gdb) continue
```

---

## Common GDB Commands

### Breakpoints

```gdb
# Set breakpoint at function
break ad4692_init

# Set breakpoint at file:line
break ad4692.c:123

# Set breakpoint at address
break *0x08001234

# List breakpoints
info breakpoints

# Delete breakpoint
delete 1

# Disable/enable breakpoint
disable 2
enable 2

# Set conditional breakpoint
break ad4692_init if ret != 0
```

---

### Execution Control

```gdb
# Continue execution
continue (or c)

# Step into function
step (or s)

# Step over function
next (or n)

# Step out of function
finish

# Run until location
until ad4692.c:150

# Reset and run
monitor reset halt
continue
```

---

### Variable Inspection

```gdb
# Print variable
print ret
print desc->spi_desc

# Print in hex
print/x reg_val

# Print pointer
print/x desc

# Print structure
print *desc

# Print array
print buffer[0]@16

# Display variable (auto-print on each step)
display ret
display desc->spi_desc
```

---

### Register Inspection

```gdb
# Print all registers
info registers

# Print specific register
print $sp
print $pc
print $lr

# Print peripheral register (SVD required)
print/x SPI1->CR1
print/x GPIOA->ODR
```

---

### Memory Inspection

```gdb
# Examine memory (hex)
x/16xw 0x20000000

# Examine memory (instructions)
x/10i $pc

# Examine string
x/s 0x08001000

# Dump memory to file
dump binary memory dump.bin 0x20000000 0x20001000
```

---

### Stack Trace

```gdb
# Show call stack
backtrace (or bt)

# Show detailed call stack
backtrace full

# Switch to frame
frame 2

# Show local variables
info locals

# Show arguments
info args
```

---

### Watchpoints (Data Breakpoints)

```gdb
# Break when variable changes
watch desc->spi_desc

# Break when variable is read
rwatch desc->spi_desc

# Break when variable is read or written
awatch desc->spi_desc

# Watch memory location
watch *(uint32_t*)0x20000100
```

---

## Debugging Common Issues with GDB

### Debugging Initialization Hangs

**Problem**: Application stops responding during init, no console output.

**GDB Approach**:
```gdb
# Start debugging
target remote localhost:3333
load
monitor reset halt

# Set breakpoint at suspected area
break ad4692_init

# Run
continue

# Step through to find where it hangs
next
next
next
# ... keeps stepping until it hangs

# Check current location
backtrace

# Inspect variables
print ret
print desc
print *desc
```

---

### Debugging NULL Pointer Dereferences

**Problem**: Crash or hard fault.

**GDB Approach**:
```gdb
# Device will be halted at fault

# Check fault location
backtrace

# Inspect program counter
print/x $pc

# Check variables
print desc
print desc->spi_desc  # If desc is NULL, this causes fault

# Inspect memory at fault address
info registers
x/10i $pc
```

---

### Debugging Memory Corruption

**Problem**: Variables changing unexpectedly.

**GDB Approach**:
```gdb
# Set watchpoint on variable
watch my_variable

# Run until it changes
continue

# GDB stops when variable changes
# Check what code modified it
backtrace
```

---

## SVD Files (System View Description)

SVD files enable viewing peripheral registers by name in debugger.

**Location**: Usually provided by vendor SDK or OpenOCD

**Usage**:
- View register values: `print/x SPI1->CR1`
- Inspect peripheral state during debugging
- See bitfield breakdowns in IDE

**Finding SVD Files**:
- Vendor SDK (STM32CubeMX, Maxim SDK, Nordic SDK)
- CMSIS-SVD repository: https://github.com/posborne/cmsis-svd
- OpenOCD: `share/openocd/contrib/`

---

## Platform-Specific Notes

### Maxim Platform

**Debug GPIO Initialization**:
```c
#include "mxc_device.h"
#include "mxc_sys.h"

// Add logging
pr_debug("Initializing GPIO port %u, pin %u\n", port, pin);

// Set breakpoint and inspect
// (gdb) break gpio_init
// (gdb) print port
// (gdb) print pin
```

**Debug SPI Initialization**:
```c
pr_debug("SPI%d configuration: speed=%u, mode=%u\n",
         spi_desc->device_id,
         spi_desc->max_speed_hz,
         spi_desc->mode);
```

---

### Mbed Platform

**Runtime Configuration**:
```c
// Set before init - check in debugger
device_ip.spi_ip = spi_ip;  

pr_debug("Mbed platform: assigning SPI instance\n");

// Verify in GDB
// (gdb) break device_init
// (gdb) print device_ip.spi_ip
```

---

## Debugging Before UART is Available

When UART hasn't been initialized yet, use JTAG/SWD:

```c
int example_main(void)
{
    // UART not initialized yet - can't use pr_err()
    ret = no_os_uart_init(&uart, &uart_ip);
    if (ret) {
        // Use JTAG debugger or LED blink pattern
        // (gdb) break here
        // (gdb) print ret
        return ret;
    }

    // Now UART available
    no_os_uart_stdio(uart);
    pr_info("Debug console ready\n");
}
```

**GDB Approach**:
```gdb
break no_os_uart_init
continue
# Step through UART init
next
next
print ret
```

---

## VSCode Cortex-Debug Extension

Popular extension for ARM Cortex debugging in VSCode.

**Installation**:
1. Install "Cortex-Debug" extension
2. Configure `launch.json` (see examples above)
3. Install OpenOCD/JLink/pyOCD

**Features**:
- Graphical breakpoint setting
- Variable inspection in sidebar
- Register viewer (with SVD)
- Memory viewer
- Disassembly view
- Integrated GDB console

---

## Common Debug Server Commands

### OpenOCD Monitor Commands

```gdb
# Reset device
monitor reset halt

# Flash program
monitor program build/app.elf verify reset

# Erase flash
monitor flash erase_sector 0 0 last

# Show targets
monitor targets

# Halt target
monitor halt

# Resume target
monitor resume
```

---

### JLink Monitor Commands

```gdb
# Reset
monitor reset

# Show speed
monitor speed

# Set speed
monitor speed 4000

# Halt
monitor halt

# Go
monitor go
```

---

## Debugging Checklist

### Before Debugging
- [ ] Debug symbols enabled (`-g3 -O0`)
- [ ] .elf file built successfully
- [ ] Debug probe connected (SWD/JTAG)
- [ ] Debug server running (OpenOCD/JLink)
- [ ] SVD file loaded (for register viewing)

### During Debug Session
- [ ] Set breakpoint at suspected location
- [ ] Step through code to find issue
- [ ] Inspect variable values
- [ ] Check return codes
- [ ] View call stack on crash
- [ ] Use watchpoints for unexpected changes

### For Crashes
- [ ] Check program counter (`$pc`)
- [ ] View backtrace (`bt`)
- [ ] Inspect registers (`info registers`)
- [ ] Check for NULL pointers
- [ ] Look at disassembly (`x/10i $pc`)
