# Coverage-Driven Testing with gcov

Complete guide to using gcov for coverage analysis and achieving 80%+ line coverage for no-OS drivers.

## Why Coverage-Driven Testing?

Without coverage analysis, you don't know:
- Which functions are completely untested
- Which code paths (branches) are not exercised
- Whether you've reached your coverage target (80%)
- What specific lines need tests

**Result**: Guesswork, wasted effort, false confidence

## Coverage-Driven Loop

```
1. WRITE TESTS → 2. RUN TESTS → 3. GENERATE COVERAGE → 4. ANALYZE REPORT
                                                              ↓
6. ADD TARGETED TESTS ← 5. IDENTIFY GAPS (untested functions, red lines)
```

Repeat until 80%+ coverage reached.

## Step 1: Generate Coverage Report

### Run Tests with Coverage

```bash
# Run tests
ceedling test:driver_name

# Generate coverage report
ceedling gcov:driver_name
```

**What happens**:
1. Ceedling compiles driver with coverage instrumentation (`--coverage`)
2. Runs all tests and records which lines/branches are executed
3. Generates HTML report with color-coded coverage visualization

### Coverage Report Location

```
build/artifacts/gcov/gcovr/
├── coverage_report.driver_name.c.[hash].html  ← Driver coverage
├── coverage_report.html                        ← Summary
└── GcovCoverageResults.html                    ← Detailed view
```

### Example Terminal Output

```bash
$ ceedling gcov:max20370_regulator

------- gcov:max20370_regulator -------
Generating coverage report...

Coverage Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
File: drivers/power/max20370/max20370_regulator.c
  Lines:    773/945   (81.80%)  ← Your coverage
  Branches: 532/532   (100.00%)
  Functions: 92/92    (100.00%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HTML report: build/artifacts/gcov/gcovr/coverage_report.max20370_regulator.c.*.html
```

## Step 2: Analyze HTML Coverage Report

### Open the Report

```bash
# Linux/Mac
open build/artifacts/gcov/gcovr/coverage_report.driver_name.c.*.html

# Windows
start build/artifacts/gcov/gcovr/coverage_report.driver_name.c.*.html
```

### Understanding Color-Coded Display

**Line Colors**:
- 🟢 **Green**: Line executed by tests (covered)
- 🔴 **Red**: Line NEVER executed (NOT covered)
- 🟡 **Yellow**: Line partially executed (some branches not taken)

**Execution Counts** (left margin):
```
290x │ int driver_init(struct dev **device, struct init_param *param)
290x │ {
 12x │     if (!device)
 12x │         return -EINVAL;    // Executed 12 times
278x │     // ... more code
```

**Branch Coverage Indicators**:
```c
if (index >= MAX)   // Branch: taken 10/15 times
    return -EINVAL; // Yellow (partial coverage)
```

### Example Coverage Report

```
┌────────────────────────────────────────────────────────────┐
│ Coverage Report: max20370_regulator.c                      │
│ Lines: 773/945 (81.80%)  Branches: 532/532 (100%)         │
└────────────────────────────────────────────────────────────┘

Line │ Hits │ Source Code
─────┼──────┼────────────────────────────────────────────
 290 │ 290x │ int max20370_set_voltage(struct dev *dev, ...)
 291 │ 290x │ {
 292 │  15x │     if (!dev)              // ✅ Covered
 293 │  15x │         return -ENODEV;    // ✅ Covered
 294 │   0x │     if (index >= MAX)      // 🔴 RED: Never tested!
 295 │   0x │         return -EINVAL;    // 🔴 RED: Never tested!
 296 │ 275x │
 297 │ 275x │     return write_voltage(dev, index);
```

**Analysis**:
- Lines 292-293: ✅ Covered (NULL device test exists)
- Lines 294-295: 🔴 NOT covered (no test with invalid index)
- **Action**: Add test with `index >= MAX`

## Step 3: Identify Coverage Gaps

### Gap Type 1: Untested Functions (RED Functions)

**What to look for**: Functions with 0% coverage in summary

```
Function Coverage: 90/92 (97.8%)

NOT TESTED:
✗ max20370_en_buck_ssm (0%)
✗ max20370_debug_mode (0%)
```

**Priority**: HIGHEST - Complete functionality missing

**Action**: Add tests for these functions
```c
void test_max20370_en_buck_ssm_null_device(void) {
    int ret = max20370_en_buck_ssm(NULL, 0, true);
    TEST_ASSERT_EQUAL_INT(-ENODEV, ret);
}

void test_max20370_en_buck_ssm_valid(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = max20370_en_buck_ssm(test_dev, 0, true);
    TEST_ASSERT_EQUAL_INT(0, ret);
}
```

### Gap Type 2: Red Lines (Error Paths)

**What to look for**: Red lines in tested functions

```c
290x │ int set_voltage(struct dev *dev, uint8_t idx, uint32_t voltage)
290x │ {
 15x │     if (!dev)
 15x │         return -ENODEV;
  0x │     if (idx >= MAX)          // 🔴 RED: Never tested!
  0x │         return -EINVAL;      // 🔴 RED: Error path missing!
275x │     return update(dev, idx, voltage);
```

**Priority**: HIGH - Error handling not validated

**Action**: Add test with invalid parameter
```c
void test_set_voltage_invalid_index(void) {
    TEST_ASSERT_EQUAL_INT(0, create_mock_device());
    int ret = set_voltage(test_dev, 999, 3300);  // Invalid
    TEST_ASSERT_EQUAL_INT(-EINVAL, ret);
}
```

### Gap Type 3: Yellow Lines (Partial Branches)

**What to look for**: Yellow lines with branch notation

```c
120x │     if (enable && voltage > 0)   // Branch: T=100, F=20
100x │         ret = enable_reg();       // 🟡 YELLOW: Partial
```

**Priority**: MEDIUM - Both paths tested, but imbalanced

**Action**: Add more tests for under-tested branch

### Gap Type 4: Red Blocks (Untested Features)

**What to look for**: Multiple consecutive red lines

```c
     │     switch (mode) {
 50x │     case MODE_SIMPLE:
 50x │         return configure_simple(dev);
  0x │     case MODE_ADVANCED:        // 🔴 RED block
  0x │         ret = configure_adv(); // 🔴 RED
  0x │         if (ret)               // 🔴 RED
  0x │             return ret;        // 🔴 RED
```

**Priority**: MEDIUM-HIGH - Entire feature untested

**Action**: Add test using that enum value

## Step 4: Iterative Test Development

### Workflow Example

**Iteration 1: Baseline**
```
Coverage: 45% (250 tests)
Gaps: 10 untested functions, 25 red error paths
```

**Iteration 2: Add function tests**
```
Coverage: 62% (+17%, 280 tests)
Gaps: All functions tested, 18 red error paths remain
```

**Iteration 3: Add error path tests**
```
Coverage: 75% (+13%, 315 tests)
Gaps: 8 red error paths remain
```

**Iteration 4: Target remaining gaps**
```
Coverage: 83% (+8%, 340 tests) ← 80% GOAL REACHED ✅
```

### Prioritizing Tests

**High Priority** (address first):
1. Untested functions (0% coverage)
2. Error handling paths (red lines)
3. Input validation (NULL checks, range checks)

**Medium Priority**:
4. Yellow branches (partial coverage)
5. Edge cases (min/max values)
6. Multi-step sequences

**Low Priority**:
7. Debug/diagnostic functions
8. Already well-covered paths

## Step 5: Coverage Goals

### Target: 80%+ Line Coverage

**Industry standard for embedded drivers**: 80-85% line coverage

**Why not 100%?**
- Some code is unreachable or defensive
- Debug/diagnostic code may not need coverage
- Diminishing returns above 85%
- Focus on quality over quantity

### Coverage Metrics

```
Lines:     81.80%  ← Primary metric (target 80%+)
Branches:  100.00% ← Ideal (all if/else paths tested)
Functions:  97.80% ← Good (most functions tested)
```

**Good coverage balanced across all three metrics**

## Common Coverage Patterns

### Pattern 1: Error Path Coverage

```c
// Red lines indicate missing error tests
int driver_init(struct dev **device, struct init_param *param) {
    if (!device) return -EINVAL;     // ✅ Tested
    if (!param) return -EINVAL;      // 🔴 NOT tested - add test!
    // ...
}
```

**Fix**: Add NULL parameter test

### Pattern 2: Range Validation Coverage

```c
int set_output(struct dev *dev, uint8_t index, uint32_t value) {
    if (index >= MAX_OUTPUTS) return -EINVAL;  // 🔴 NOT tested
    if (value > MAX_VALUE) return -EINVAL;     // 🔴 NOT tested
    // ...
}
```

**Fix**: Add tests with invalid index and invalid value

### Pattern 3: Switch Case Coverage

```c
switch (mode) {
    case MODE_A: return handle_a();  // ✅ Tested
    case MODE_B: return handle_b();  // 🔴 NOT tested
    case MODE_C: return handle_c();  // 🔴 NOT tested
    default: return -EINVAL;         // 🔴 NOT tested
}
```

**Fix**: Add tests for MODE_B, MODE_C, and invalid mode

## Best Practices

1. **Generate coverage after every test session** - Know where you stand
2. **Focus on red lines first** - Highest coverage gain
3. **Don't chase 100%** - 80-85% is the sweet spot
4. **Verify error paths** - Red lines often indicate missing error tests
5. **Use coverage to guide, not dictate** - Quality > coverage percentage
6. **Track progress iteratively** - Measure improvement each iteration
7. **Balance all metrics** - Lines, branches, functions all matter

## Common Issues

**Issue**: Coverage lower than expected after adding tests
**Cause**: Tests not actually calling driver code (mocking issues)
**Fix**: Verify test actually exercises driver functions

**Issue**: Can't reach 80% no matter what
**Cause**: Unreachable defensive code, debug functions
**Solution**: Acceptable - focus on meaningful coverage

**Issue**: Tests pass but coverage is 0%
**Cause**: Coverage build not enabled, wrong configuration
**Fix**: Check `project.yml` has `:gcov:` section configured

## Summary

**Coverage-Driven Workflow**:
1. **Generate**: `ceedling gcov:driver_name`
2. **Analyze**: Open HTML report, identify red/yellow lines
3. **Prioritize**: Untested functions → error paths → branches
4. **Test**: Add targeted tests for gaps
5. **Repeat**: Until 80%+ reached

**Focus Areas**:
- 🔴 Red lines (untested code) - HIGHEST priority
- Untested functions (0% coverage) - HIGHEST priority
- 🟡 Yellow lines (partial branches) - MEDIUM priority
- Missing error paths - HIGH priority

**Goal**: 80-85% line coverage with balanced branch and function coverage.
