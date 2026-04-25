# Clock Debugging Reference

Complete reference for debugging clock issues.

## Clock Debugfs

### View Clock Tree

```bash
# View complete clock tree with rates and enable counts
cat /sys/kernel/debug/clk/clk_summary

# Example output:
   clock                         enable_cnt  prepare_cnt  rate        accuracy   phase
----------------------------------------------------------------------------------------
 ref_clk                         1           1            24000000    0          0
    pll                          2           2            800000000   0          0
       pll_div2                  0           0            400000000   0          0
       cpu_clk                   1           1            800000000   0          0
       apb_div                   1           1            100000000   0          0
          uart_clk               1           1            100000000   0          0
          i2c_clk                0           0            100000000   0          0
          spi_clk                1           1            100000000   0          0
```

**Columns explained**:
- `enable_cnt`: Number of times clock is enabled
- `prepare_cnt`: Number of times clock is prepared
- `rate`: Current clock rate in Hz
- `accuracy`: Clock accuracy (if supported)
- `phase`: Clock phase (if supported)

### View Specific Clock

```bash
# Clock rate
cat /sys/kernel/debug/clk/pll/clk_rate
# Output: 800000000

# Enable count
cat /sys/kernel/debug/clk/pll/clk_enable_count
# Output: 2

# Prepare count
cat /sys/kernel/debug/clk/pll/clk_prepare_count
# Output: 2

# Parent clock
cat /sys/kernel/debug/clk/pll/clk_parent
# Output: ref_clk

# Accuracy
cat /sys/kernel/debug/clk/pll/clk_accuracy
# Output: 0

# Phase
cat /sys/kernel/debug/clk/pll/clk_phase
# Output: 0

# Flags
cat /sys/kernel/debug/clk/pll/clk_flags
# Output: CLK_SET_RATE_GATE

# List all available clocks
ls /sys/kernel/debug/clk/
```

### Find Clock Consumers

```bash
# Find which devices are using a clock
grep -r "pll" /sys/kernel/debug/clk/*/clk_parent
```

## Kernel Configuration

Enable clock debugging:

```kconfig
CONFIG_COMMON_CLK=y
CONFIG_DEBUG_FS=y
CONFIG_COMMON_CLK_DEBUG=y  # Enable clock debugfs
```

## Common Issues and Solutions

### Issue: Clock Not Found

**Symptom**:
```
[    1.234567] my-device: failed to get clock 'core': -2
```

**Debug**:
```bash
# Check if clock provider is registered
ls /sys/kernel/debug/clk/ | grep expected_clock

# Check devicetree
dtc -I fs /sys/firmware/devicetree/base | grep -A 5 my-device

# Check clock names in DT
cat /sys/firmware/devicetree/base/my-device/clock-names
```

**Common causes**:
1. Clock provider driver not loaded
2. Mismatch between DT `clock-names` and driver `devm_clk_get()` name
3. Missing `#clock-cells` in provider node
4. Wrong phandle reference in DT

**Solutions**:
```dts
// Wrong
clocks = <&clkgen>;  // Missing index for indexed provider
clock-names = "wrong_name";  // Doesn't match driver

// Correct
clocks = <&clkgen 0>;
clock-names = "core";  // Matches devm_clk_get(dev, "core")
```

### Issue: Rate Change Fails

**Symptom**:
```
[    1.234567] my-device: failed to set clock rate: -16
```

**Debug**:
```bash
# Check clock flags
cat /sys/kernel/debug/clk/my_clk/clk_flags

# Check if clock is enabled
cat /sys/kernel/debug/clk/my_clk/clk_enable_count

# Check parent rate
cat /sys/kernel/debug/clk/parent_clk/clk_rate
```

**Common causes**:
1. Clock has `CLK_SET_RATE_GATE` but is currently enabled
2. Requested rate is outside supported range
3. Parent clock cannot achieve required rate

**Solutions**:
```c
// If CLK_SET_RATE_GATE is set
clk_disable_unprepare(clk);
ret = clk_set_rate(clk, new_rate);
if (ret) {
	dev_err(dev, "Failed to set rate: %d\n", ret);
	return ret;
}
clk_prepare_enable(clk);

// Check achievable rate first
long rounded = clk_round_rate(clk, desired_rate);
dev_info(dev, "Desired %lu Hz, can achieve %ld Hz\n", desired_rate, rounded);
```

### Issue: Clock Stuck at Wrong Rate

**Symptom**: Clock shows expected rate in debugfs but device doesn't work.

**Debug**:
```bash
# Verify actual hardware rate
cat /sys/kernel/debug/clk/my_clk/clk_rate

# Check parent rate
cat /sys/kernel/debug/clk/parent_clk/clk_rate

# Check enable count
cat /sys/kernel/debug/clk/my_clk/clk_enable_count
```

**Common causes**:
1. Clock not actually enabled (enable_count = 0)
2. Parent clock at wrong rate
3. Hardware not configured (driver bug)

**Solutions**:
```c
// Verify clock is actually enabled
ret = clk_prepare_enable(clk);

// Verify actual rate
unsigned long actual_rate = clk_get_rate(clk);
dev_info(dev, "Expected %lu Hz, actual %lu Hz\n", expected, actual_rate);

// Add debugging to recalc_rate
dev_dbg(dev, "recalc_rate: parent=%lu, m=%u, n=%u, result=%lu\n",
	parent_rate, m, n, rate);
```

### Issue: Parent Rate Not Propagating

**Symptom**: Changing child clock rate doesn't affect parent.

**Debug**:
```bash
# Check clock flags
cat /sys/kernel/debug/clk/child_clk/clk_flags
# Should show: CLK_SET_RATE_PARENT
```

**Solution**:
```c
// Add CLK_SET_RATE_PARENT flag
init.flags = CLK_SET_RATE_PARENT;
```

### Issue: Clock Disabled by Framework

**Symptom**:
```
[    5.123456] clk: Disabling unused clocks
[    5.123457] clock 'unused_clk' disabled
```

**Debug**:
```bash
# Check enable count
cat /sys/kernel/debug/clk/unused_clk/clk_enable_count
# Output: 0 (no consumers)

# Check if clock is critical
cat /sys/kernel/debug/clk/unused_clk/clk_flags
```

**Solutions**:
```c
// Mark clock as critical (never disable)
init.flags = CLK_IS_CRITICAL;

// Or mark as ignore unused
init.flags = CLK_IGNORE_UNUSED;

// Or ensure consumer enables it
ret = clk_prepare_enable(clk);
```

### Issue: Circular Dependency

**Symptom**:
```
[    1.234567] clk: circular dependency detected between 'clk_a' and 'clk_b'
```

**Debug**: Check clock tree for loops.

```bash
# Check parent chain
cat /sys/kernel/debug/clk/clk_a/clk_parent
cat /sys/kernel/debug/clk/clk_b/clk_parent
```

**Solution**: Fix devicetree or driver to remove circular parent relationships.

## Dynamic Debug

Enable verbose clock framework logging:

```bash
# Enable all clock framework debug
echo "file drivers/clk/* +p" > /sys/kernel/debug/dynamic_debug/control

# Enable specific file
echo "file drivers/clk/clk.c +p" > /sys/kernel/debug/dynamic_debug/control

# Enable specific driver
echo "file drivers/clk/clk-my-pll.c +p" > /sys/kernel/debug/dynamic_debug/control

# View messages
dmesg | grep clk
```

## Ftrace Clock Events

Trace clock operations:

```bash
# Enable clock tracing
cd /sys/kernel/debug/tracing
echo 1 > events/clk/enable

# View trace
cat trace

# Example output:
# clk_set_rate: clk=pll rate=800000000
# clk_enable: clk=cpu_clk
# clk_prepare: clk=cpu_clk
```

## Adding Debug to Driver

### Provider Debug

```c
static unsigned long my_pll_recalc_rate(struct clk_hw *hw,
					unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	u32 val, m, n;
	u64 rate;

	val = readl(pll->base + PLL_CONFIG);
	m = (val >> 8) & 0xFF;
	n = val & 0xFF;

	dev_dbg(pll->dev, "recalc_rate: reg=0x%08x m=%u n=%u parent=%lu\n",
		val, m, n, parent_rate);

	rate = (u64)parent_rate * m;
	do_div(rate, n);

	dev_dbg(pll->dev, "recalc_rate: calculated rate=%llu\n", rate);

	return rate;
}

static int my_pll_set_rate(struct clk_hw *hw, unsigned long rate,
			   unsigned long parent_rate)
{
	struct my_pll *pll = to_my_pll(hw);
	unsigned int m, n;

	dev_info(pll->dev, "set_rate: requested=%lu parent=%lu\n",
		 rate, parent_rate);

	// Calculate parameters
	my_pll_calc_params(pll, parent_rate, rate, &m, &n);

	dev_info(pll->dev, "set_rate: using m=%u n=%u\n", m, n);

	// Program hardware
	writel((m << 8) | n, pll->base + PLL_CONFIG);

	return 0;
}
```

### Consumer Debug

```c
static int my_probe(struct platform_device *pdev)
{
	struct clk *clk;
	unsigned long rate;
	int ret;

	clk = devm_clk_get(&pdev->dev, "core");
	if (IS_ERR(clk)) {
		dev_err(&pdev->dev, "Failed to get clock 'core': %ld\n",
			PTR_ERR(clk));
		return PTR_ERR(clk);
	}

	dev_info(&pdev->dev, "Got clock 'core'\n");

	ret = clk_prepare_enable(clk);
	if (ret) {
		dev_err(&pdev->dev, "Failed to enable clock: %d\n", ret);
		return ret;
	}

	rate = clk_get_rate(clk);
	dev_info(&pdev->dev, "Clock enabled at %lu Hz (%lu MHz)\n",
		 rate, rate / 1000000);

	return 0;
}
```

## Checking Hardware Registers

Add debugfs for raw register access:

```c
static int my_pll_debug_show(struct seq_file *s, void *data)
{
	struct my_pll *pll = s->private;
	u32 config, status;

	config = readl(pll->base + PLL_CONFIG);
	status = readl(pll->base + PLL_STATUS);

	seq_printf(s, "PLL Configuration:\n");
	seq_printf(s, "  CONFIG: 0x%08x\n", config);
	seq_printf(s, "  STATUS: 0x%08x\n", status);
	seq_printf(s, "  M: %u\n", (config >> 8) & 0xFF);
	seq_printf(s, "  N: %u\n", config & 0xFF);
	seq_printf(s, "  Locked: %s\n", (status & PLL_LOCKED) ? "yes" : "no");

	return 0;
}

static int my_pll_debug_open(struct inode *inode, struct file *file)
{
	return single_open(file, my_pll_debug_show, inode->i_private);
}

static const struct file_operations my_pll_debug_fops = {
	.open = my_pll_debug_open,
	.read = seq_read,
	.llseek = seq_lseek,
	.release = single_release,
};

static void my_pll_debug_init(struct clk_hw *hw, struct dentry *dentry)
{
	struct my_pll *pll = to_my_pll(hw);

	debugfs_create_file("registers", 0444, dentry, pll,
			    &my_pll_debug_fops);
}

static const struct clk_ops my_pll_ops = {
	// ... other ops ...
	.debug_init = my_pll_debug_init,
};
```

Then view:
```bash
cat /sys/kernel/debug/clk/my_pll/registers
```

## Common Debugging Patterns

### Verify Clock Hierarchy

```bash
# View parent chain
clk="my_clk"
while [ -n "$clk" ]; do
	echo "Clock: $clk"
	cat /sys/kernel/debug/clk/$clk/clk_rate 2>/dev/null || echo "  (no rate)"
	clk=$(cat /sys/kernel/debug/clk/$clk/clk_parent 2>/dev/null)
done
```

### Monitor Rate Changes

```bash
# Watch clock rate changes
watch -n 0.1 'cat /sys/kernel/debug/clk/my_clk/clk_rate'
```

### Check All Clock Consumers

```bash
# Find all devices using clocks
for dev in /sys/devices/platform/*/clocks; do
	echo "Device: $(dirname $dev)"
	cat $dev 2>/dev/null || echo "  (no clocks)"
done
```

## Error Code Reference

| Error | Code | Meaning | Common Cause |
|-------|------|---------|--------------|
| -ENOENT | -2 | No such entry | Clock not found, provider not registered |
| -EINVAL | -22 | Invalid argument | Invalid rate, bad parameters |
| -EBUSY | -16 | Device busy | Clock enabled but needs to be disabled |
| -ENODEV | -19 | No such device | Clock provider not available |
| -EPROBE_DEFER | -517 | Probe deferred | Clock provider not yet probed |

## Kernel Boot Messages

Look for clock-related messages:

```bash
# Clock registration
dmesg | grep "clk:"

# Clock consumers
dmesg | grep "clock"

# Specific driver
dmesg | grep "my-pll"
```

## Checklist for Clock Issues

1. Is clock provider driver loaded?
   ```bash
   lsmod | grep clk
   ls /sys/kernel/debug/clk/
   ```

2. Is clock visible in debugfs?
   ```bash
   ls /sys/kernel/debug/clk/ | grep my_clk
   ```

3. Is clock at expected rate?
   ```bash
   cat /sys/kernel/debug/clk/my_clk/clk_rate
   ```

4. Is clock enabled?
   ```bash
   cat /sys/kernel/debug/clk/my_clk/clk_enable_count
   ```

5. Is parent clock correct?
   ```bash
   cat /sys/kernel/debug/clk/my_clk/clk_parent
   ```

6. Are devicetree bindings correct?
   ```bash
   dtc -I fs /sys/firmware/devicetree/base | grep -A 10 my_clk
   ```

7. Are clock flags correct?
   ```bash
   cat /sys/kernel/debug/clk/my_clk/clk_flags
   ```
