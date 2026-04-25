# Kernel Sanitizers and Lock Debugging

## KASAN - Kernel Address Sanitizer

KASAN is a **dynamic memory error detector** that finds out-of-bounds accesses and use-after-free bugs at runtime.

### KASAN Modes

**Three implementation modes**:

1. **Generic KASAN** (`CONFIG_KASAN_GENERIC`):
   - For debugging (not production)
   - Supported: x86_64, arm64, arm, powerpc, riscv, s390, xtensa, loongarch
   - Overhead: **Significant** performance (~2x slower) and memory (1/8 RAM for shadow)
   - Most thorough detection

2. **Software Tag-Based KASAN** (`CONFIG_KASAN_SW_TAGS`):
   - For debugging on constrained devices
   - Supported: **arm64 only**
   - Overhead: **Moderate** (1/16 RAM for shadow)

3. **Hardware Tag-Based KASAN** (`CONFIG_KASAN_HW_TAGS`):
   - For **production** use
   - Requires: arm64 with MTE (Memory Tagging Extension)
   - Overhead: **Low** memory and performance

### Enabling KASAN

**Kernel configuration**:
```kconfig
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y     # or SW_TAGS or HW_TAGS
CONFIG_KASAN_INLINE=y      # Faster (2x) but larger binary
# or CONFIG_KASAN_OUTLINE=y  # Smaller binary
```

**Compiler requirements**:
- Generic: GCC 8.3.0+ or Clang 7+
- Software tags: GCC 11+ or Clang 11+
- Hardware tags: GCC 10+ or Clang 12+

### Boot Parameters

```bash
# Report every error (not just first)
kasan_multi_shot

# Control behavior on detection
kasan.fault=report        # Just report (default)
kasan.fault=panic         # Panic on any error
kasan.fault=panic_on_write  # Panic only on writes

# Stack trace collection
kasan.stacktrace=off      # Disable stack traces
kasan.stacktrace=on       # Enable (default)
```

### KASAN Report Interpretation

**Example report**:
```
==================================================================
BUG: KASAN: use-after-free in ad7124_read+0x123/0x456 [ad7124]
Read of size 4 at addr ffff888012345678 by task cat/1234

CPU: 0 PID: 1234 Comm: cat Not tainted 6.5.0 #1
Hardware name: QEMU Standard PC (i440FX + PIIX, 1996)
Call Trace:
 dump_stack+0x45/0x67
 print_address_description+0x78/0x123
 kasan_report+0x234/0x345
 ad7124_read+0x123/0x456 [ad7124]
 vfs_read+0x234/0x567
 ...

Allocated by task 1200:
 kasan_save_stack+0x12/0x34
 kasan_set_track+0x23/0x45
 __kasan_kmalloc+0x56/0x78
 ad7124_probe+0x89/0x123 [ad7124]
 ...

Freed by task 1200:
 kasan_save_stack+0x12/0x34
 kasan_set_track+0x23/0x45
 kasan_save_free_info+0x34/0x56
 __kasan_slab_free+0x78/0x9a
 ad7124_remove+0xab/0xcd [ad7124]
 ...

Memory state around the buggy address:
 ffff888012345600: fc fc fc fc fc fc fc fc fc fc fc fc fc fc fc fc
 ffff888012345680: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
>ffff888012345700: fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd fd
                                                 ^
 ffff888012345780: fc fc fc fc fc fc fc fc fc fc fc fc fc fc fc fc
==================================================================
```

**Understanding the report**:
- `use-after-free`: Memory was freed, then accessed
- `Read of size 4`: 4-byte read operation
- Call Trace: Where the invalid access occurred
- Allocated/Freed: When/where the memory was allocated and freed
- Memory state: Visualization of shadow memory
  - `fd` = freed memory
  - `fa` = left redzone (allocated but out of bounds)
  - `fc` = freed or padding
  - `00` = valid accessible memory
  - `01-07` = partially accessible bytes

### Common KASAN Detections

**Out-of-bounds access**:
```c
struct my_data *data = kmalloc(sizeof(*data), GFP_KERNEL);
data->buf[100] = 0;  // KASAN: out-of-bounds if buf is smaller
```

**Use-after-free**:
```c
kfree(data);
pr_info("Value: %d\n", data->value);  // KASAN: use-after-free
```

**Stack out-of-bounds**:
```c
int buf[10];
buf[10] = 42;  // KASAN: stack-out-of-bounds
```

### Disabling KASAN for Specific Code

```c
// Per-function
__no_sanitize_address
static void my_special_function(void)
{
	// KASAN disabled here
}

// Or use noinstr
noinstr void my_lowlevel_function(void)
{
	// No instrumentation
}

// Runtime disable/enable
kasan_disable_current();
// ... code that shouldn't be checked ...
kasan_enable_current();
```

**Per-file in Makefile**:
```makefile
KASAN_SANITIZE_myfile.o := n
```

## UBSAN - Undefined Behavior Sanitizer

UBSAN detects undefined behavior at runtime using compile-time instrumentation.

### Enabling UBSAN

```kconfig
CONFIG_UBSAN=y
CONFIG_UBSAN_ALIGNMENT=y  # Detect misaligned accesses (optional)
```

### What UBSAN Detects

- Signed integer overflow
- Division by zero
- Shift operations exceeding type width
- Out-of-bounds array indexing
- Misaligned pointer access (with CONFIG_UBSAN_ALIGNMENT)
- Type mismatches
- NULL pointer passed to nonnull

**Example report**:
```
UBSAN: shift-out-of-bounds in drivers/iio/adc/ad7124.c:123:4
shift exponent 32 is too large for 32-bit type 'unsigned int'
CPU: 0 PID: 1234 Comm: modprobe Not tainted 6.5.0 #1
Call Trace:
 dump_stack+0x45/0x67
 ubsan_epilogue+0x12/0x34
 __ubsan_handle_shift_out_of_bounds+0x56/0x78
 ad7124_calculate_freq+0x89/0xab [ad7124]
```

### Disabling UBSAN for Specific Files

```makefile
# In Makefile
UBSAN_SANITIZE_myfile.o := n

# Re-enable if directory has UBSAN_SANITIZE := n
UBSAN_SANITIZE_myfile.o := y
```

## KCSAN - Kernel Concurrency Sanitizer

KCSAN detects data races by watching memory accesses at runtime.

### Enabling KCSAN

```kconfig
CONFIG_KCSAN=y
CONFIG_KCSAN_REPORT_ONCE_IN_MS=3000  # Rate limit reports
```

### What KCSAN Detects

- Concurrent reads and writes to same memory location
- Concurrent writes to same memory location
- Missing barriers/locks

**Example report**:
```
==================================================================
BUG: KCSAN: data-race in ad7124_read_raw / ad7124_write_raw

write to 0xffff888012345678 of 4 bytes by task 1234 on cpu 0:
 ad7124_write_raw+0x56/0x123 [ad7124]
 iio_channel_write+0x78/0x9a
 ...

read to 0xffff888012345678 of 4 bytes by task 1235 on cpu 1:
 ad7124_read_raw+0xab/0xcd [ad7124]
 iio_channel_read+0xef/0x123
 ...

==================================================================
```

## Lockdep - Lock Dependency Validator

Lockdep detects potential deadlocks by analyzing lock ordering at runtime.

### Enabling Lockdep

```kconfig
CONFIG_PROVE_LOCKING=y
CONFIG_DEBUG_LOCK_ALLOC=y
CONFIG_LOCK_STAT=y  # Lock statistics
```

### What Lockdep Detects

- Circular lock dependencies (potential deadlock)
- Inconsistent lock state (IRQ-safe vs IRQ-unsafe)
- Recursive locking
- Lock inversion

**Example warning**:
```
======================================================
WARNING: possible circular locking dependency detected
6.5.0 #1 Not tainted
------------------------------------------------------
modprobe/1234 is trying to acquire lock:
 ffff888012345678 (&st->lock){+.+.}, at: ad7124_trigger_handler+0x12/0x345

but task is already holding lock:
 ffff888087654321 (&indio_dev->mlock){+.+.}, at: iio_trigger_poll+0x23/0x456

which lock already depends on the new lock.

the existing dependency chain (in reverse order) is:

-> #1 (&indio_dev->mlock){+.+.}:
       lock_acquire+0x12/0x34
       mutex_lock+0x45/0x67
       iio_update_buffers+0x78/0x9a
       ...

-> #0 (&st->lock){+.+.}:
       __lock_acquire+0xab/0xcd
       lock_acquire+0x12/0x34
       mutex_lock+0x45/0x67
       ad7124_trigger_handler+0x12/0x345
       ...
```

**Fix**: Change lock ordering to be consistent across all code paths.

## kmemleak - Memory Leak Detector

Kmemleak scans memory for unreferenced allocated objects.

### Enabling kmemleak

```kconfig
CONFIG_DEBUG_KMEMLEAK=y
CONFIG_DEBUG_KMEMLEAK_DEFAULT_OFF=y  # Manual start
```

**Runtime control**:
```bash
# Start scanning
echo scan > /sys/kernel/debug/kmemleak

# Trigger immediate scan
echo scan=on > /sys/kernel/debug/kmemleak

# View detected leaks
cat /sys/kernel/debug/kmemleak

# Clear results
echo clear > /sys/kernel/debug/kmemleak
```

**Example leak report**:
```
unreferenced object 0xffff888012345678 (size 128):
  comm "modprobe", pid 1234, jiffies 4294967890 (age 120.456s)
  hex dump (first 32 bytes):
    00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
    00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
  backtrace:
    [<ffffffff81234567>] kmem_cache_alloc_trace+0x12/0x34
    [<ffffffffa0123456>] ad7124_probe+0x56/0x789 [ad7124]
    [<ffffffff81345678>] platform_drv_probe+0x78/0x9a
```
