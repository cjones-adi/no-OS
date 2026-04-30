# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) for working with code in this repository, with special focus on driver development workflow.

## About no-OS

This is Analog Devices' no-OS repository containing hardware drivers and reference projects for embedded systems without an operating system. It supports microcontrollers, FPGAs, and other embedded platforms that interface with ADI hardware peripherals.

## Enhanced Driver Development Workflow

**🎯 MANDATORY: For ALL driver development requests, Claude MUST follow this exact workflow:**

### **Phase 0: Framework Verification (MANDATORY FIRST STEP)**
1. **Current Version Check**: Verify current no-OS, Ceedling, Unity framework versions
2. **Build System Validation**: Check current build system patterns and requirements
3. **Platform API Verification**: Validate platform-specific constants, headers, and APIs exist
4. **Test Framework Setup**: Verify current Ceedling configuration format and capabilities
5. **Reference Driver Analysis**: Examine existing similar drivers for current patterns

**🚨 CRITICAL: Never proceed to planning without framework verification**

### **Phase 1: Planning & Approval (REQUIRED)**
1. **Planning Mode**: Enter planning mode with `EnterPlanMode` to analyze requirements
2. **Datasheet Analysis**: Extract device specifications, interface type, and command sets
3. **Framework Integration Plan**: Detail specific build system integration with verified APIs
4. **Build Validation Strategy**: Define build verification approach for each commit
5. **Plan Presentation**: Present comprehensive implementation plan to user
6. **User Approval**: Wait for explicit user approval before proceeding with implementation
7. **Plan Finalization**: Use `ExitPlanMode` when plan is approved

### **Phase 2: Implementation (6-Commit Pattern)**
Claude MUST follow this exact commit sequence for ALL driver implementations:

1. **Core Driver**: `drivers: <category>: <device>: Add driver support for <device>`
2. **IIO Support**: `drivers: <category>: <device>: Add IIO support for <device>`
3. **Driver Docs**: `drivers: <category>: <device>: Add README documentation for <device>`
4. **Project Files**: `projects: <device>: Add project for <device>`
5. **Project Docs**: `projects: <device>: Add README documentation for project`
6. **Unit Tests**: `tests: drivers: <category>: <device>: Add unit tests for <device>`

### **Phase 3: Quality Assurance (Automated)**
7. **Automated Quality** - Pattern detection and style cleanup
8. **Local Testing** - Unit tests with 80%+ coverage via Ceedling
9. **Build Validation** - Multi-platform build testing

### **Phase 4: Submission**
10. **PR Creation** - Submit with proper commit messages and complete build system
11. **Review & Iteration** - Address feedback with 62.5% issue prevention
12. **Hardware Testing** - Validate on target hardware
13. **Merge** - Maintainer approval and integration

**🔒 MANDATORY PRE-ACTION COMPLIANCE CHECK:**
**BEFORE ANY driver development work (including file creation, commits, or planning), Claude MUST:**

1. **Read and acknowledge ALL 🚨 CRITICAL REQUIREMENTS below**
2. **Create explicit compliance checklist for current task**
3. **Verify each critical requirement will be followed**
4. **Only proceed after confirming 100% compliance**

**Example Pre-Action Check:**
```
✅ Framework validation completed
✅ Planning mode will be used
✅ 6-commit pattern planned
✅ NO AI attribution in any files (author field = "Analog Devices")
✅ Complete implementation scope confirmed
✅ Proper project naming (no "-eval" suffix)
```

**🚨 CRITICAL REQUIREMENTS:**
- **Framework Verification First**: ALWAYS run framework validation before ANY implementation
- **Planning First**: ALWAYS use EnterPlanMode for driver development
- **Autonomous Execution**: DO NOT ask about basic commands (`cd`, `ls`, etc.) - execute directly
- **Complete Implementation**: Include ALL components (driver, IIO, project, tests, docs)
- **Exact Commit Pattern**: Follow 6-commit sequence precisely
- **No "-eval" Suffix**: Projects are named `projects/<device>` NOT `projects/<device>-eval`
- **No AI Attribution**: NEVER include AI attribution in code files, commits, or headers (no Co-Authored-By Claude, no "Generated with" mentions, etc.)

---

## Driver Implementation Patterns

### File Structure and Naming

Every driver should follow this structure:

```
drivers/<category>/<device_name>/
├── <device_name>.h        # Public API declarations
├── <device_name>.c        # Implementation
├── iio_<device_name>.h    # IIO subsystem interface (REQUIRED for monitoring devices)
├── iio_<device_name>.c    # IIO implementation
├── <device_name>_regs.h   # Register definitions (if complex)
└── README.rst            # Comprehensive documentation

projects/<device_name>/
├── Makefile              # Platform build selection
├── builds.json           # CI build matrix
├── src.mk               # Source dependencies and platform support
├── README.rst            # Complete project documentation
└── src/
    ├── common/
    ├── examples/
    └── platform/<target>/
```

**🚨 Linux Driver Naming Principle:**
> **Critical**: Linux drivers must not rely on generic or wildcard‑style names to represent multiple devices. The kernel driver model requires explicit device matching via ID tables or device tree compatibles.

**Implementation Guidelines:**
- ❌ **Avoid**: Generic names like `device_nameX`, `sensor_driver`, `power_controller`
- ✅ **Use**: Specific device names like `ltm4700`, `adm1275`, `ad7980`
- ✅ **Family Support**: Use explicit device identification in code (e.g., chip_id detection)
- ✅ **Branch Names**: `dev/ltm4700`, `dev/adm1275` (not `dev/ltm470x` or `dev/power_device`)

---

## 🤖 Enhanced Development with Claude Code

**🚨 MANDATORY WORKFLOW: Claude MUST follow this exact process for ALL driver development:**

### **Phase 0: Framework Verification (MANDATORY FIRST STEP)**
Claude must ALWAYS verify framework compatibility before any planning:

**Example Session (REQUIRED FLOW):**
```
Developer: "Create a no-OS driver for LTM4700"

Claude: "I'll help you create a comprehensive no-OS driver for the LTM4700. Before starting
implementation planning, I need to verify the current framework compatibility and build
system patterns to prevent integration failures."

[Claude performs framework verification - checking build patterns, platform APIs, test framework versions]

Claude: "Framework verification complete:
✅ Build system patterns validated (individual file includes, no wildcards)
✅ Platform APIs confirmed (maxim_uart.h, MAX_UART_FLOW_DIS constants)
✅ Test framework version verified (Ceedling 1.0.1, current Unity/CMock patterns)
✅ API signatures validated (CRC, IIO, no-OS core APIs)

Now entering planning mode for comprehensive implementation strategy."

[Claude uses EnterPlanMode tool]

Claude: "
IMPLEMENTATION PLAN: LTM4700 PMBus Dual-Channel Regulator Driver

ANALYSIS:
- Device: LTM4700 dual 50A or single 100A μModule regulator
- Interface: PMBus 1.3 compliant I2C (default address 0x5A)
- Variant Support: LTM4777 through device ID detection
- Channels: Dual-channel power monitoring and control

IMPLEMENTATION STRATEGY:
1. Core Driver (drivers/power/ltm4700/)
   - Complete PMBus command set implementation
   - Dual-channel support with PAGE commands
   - LINEAR11/LINEAR16 data format conversion
   - Device identification (LTM4700 vs LTM4777)

2. IIO Integration (REQUIRED for monitoring devices)
   - 12 IIO channels: VIN, IIN, PIN, VOUT0/1, IOUT0/1, POUT0/1, TEMP1/2/3
   - Write support for VOUT control
   - Linux Industrial I/O subsystem compliance

3. Project Structure (projects/ltm4700/)
   - Multi-platform build system (MAX32655, STM32, Linux, etc.)
   - Basic telemetry monitoring example
   - IIO integration example

4. Unit Testing (tests/drivers/power/ltm4700/)
   - Comprehensive Ceedling test suite
   - 80%+ code coverage target
   - PMBus format testing and mock validation

COMMIT SEQUENCE (6 commits):
1. drivers: power: ltm4700: Add driver support for ltm4700
2. drivers: power: ltm4700: Add IIO support for ltm4700
3. drivers: power: ltm4700: Add README documentation for ltm4700
4. projects: ltm4700: Add project for ltm4700
5. projects: ltm4700: Add README documentation for project
6. tests: drivers: power: ltm4700: Add unit tests for ltm4700

Does this implementation plan look correct? Should I proceed with this approach?"

[User reviews and approves plan]

Developer: "Yes, this looks perfect. Please proceed with the implementation."

Claude: "Excellent! I'll now implement the complete LTM4700 driver following the approved plan.
Starting with branch creation and core driver implementation..."

[Claude executes the 6-commit implementation autonomously]
```

### **Phase 2: Autonomous Implementation**
After plan approval, Claude executes WITHOUT asking intermediate questions:
- ✅ **Create development branch** (`dev/ltm4700`)
- ✅ **Execute all 6 commits** following exact pattern
- ✅ **Run quality checks** automatically
- ✅ **Execute unit tests** for validation
- ✅ **Report completion** with summary

### **Critical Requirements for Claude:**
- **🚨 ALWAYS use framework validation first** - Run `./.claude/tools/scripts/framework_validation.sh` before planning
- **🚨 ALWAYS use EnterPlanMode** - No implementation without planning
- **🚨 NO intermediate questions** - Don't ask about `cd`, `ls`, file paths, etc.
- **🚨 Complete implementation** - All 6 components (driver, IIO, project, tests, docs)
- **🚨 No "-eval" suffix** - Projects are `projects/<device>` NOT `projects/<device>-eval`
- **🚨 Autonomous execution** - After plan approval, execute without further questions
- **🚨 NO AI attribution** - Never add AI attribution to code files, commits, or headers

---

## Build Commands

### Primary Build Commands

```bash
# Build all projects
python3 tools/scripts/build_projects.py . -export_dir exports -log_dir logs

# Build specific project
python3 tools/scripts/build_projects.py . -project=<project_name>

# Build for specific platform
python3 tools/scripts/build_projects.py . -platform=<platform> -project=<project_name>

# Supported platforms: xilinx, stm32, maxim, mbed, pico, aducm3029, lattice
```

### Framework Validation

```bash
# MANDATORY before ANY driver implementation
./.claude/tools/scripts/framework_validation.sh <device> <category> <platform>

# Example usage
./.claude/tools/scripts/framework_validation.sh ltm4700 power maxim
```

---

## Pre-Submission Checklist

Before creating a PR, verify:

### **🚨 Framework Verification (MANDATORY FIRST)**
- [ ] Framework validation passes (`./.claude/tools/scripts/framework_validation.sh`)
- [ ] Build system patterns verified (no wildcards, individual includes)
- [ ] Platform APIs confirmed (headers exist, constants validated)
- [ ] Test framework version verified (Ceedling 1.0.1, modern format)
- [ ] API signatures validated (no-OS, IIO, platform-specific)

### Code Quality
- [ ] AStyle formatting passes
- [ ] Cppcheck analysis passes
- [ ] All functions have Doxygen documentation
- [ ] Error handling for all failure paths
- [ ] Consistent naming conventions

### Build System
- [ ] Driver builds successfully
- [ ] Project integrates without errors
- [ ] `src.mk` includes all required dependencies (individual files only)
- [ ] Examples integration included (`include $(PROJECT)/src/examples.mk`)
- [ ] No directory wildcard includes (`**` patterns avoided)

### Testing
- [ ] Hardware validation completed
- [ ] All driver functions tested
- [ ] Error conditions verified
- [ ] Unit tests with 80%+ coverage

### Documentation
- [ ] Header file fully documented
- [ ] Project README written
- [ ] Commit messages follow format
- [ ] All commits signed off (`-s`)

---

## Supporting Documentation

For detailed implementation guidance, see these comprehensive guides:

### Core Development Guides
- **[Framework Integration Guide](docs/framework-integration-guide.md)**: Complete framework verification process
- **[Framework Validation Lessons](docs/framework-validation-lessons.md)**: Critical failure patterns and solutions (IMPORTANT)
- **[Framework Troubleshooting](docs/framework-validation-troubleshooting.md)**: Quick fixes for common validation failures
- **[Driver Templates](docs/driver-templates.md)**: Standard templates and patterns
- **[Quality Assurance Guide](docs/quality-assurance-guide.md)**: QA patterns and error prevention
- **[Git Workflow Guide](docs/git-workflow-guide.md)**: Complete git workflow and commit patterns

### Specialized Guides
- **[Testing Guide](docs/testing-guide.md)**: Unit testing with Ceedling and hardware validation
- **[Architecture Guide](docs/architecture-guide.md)**: Repository structure and platform abstraction

### Quality Analysis
- **[6-Month Review Analysis](docs/no-os-review-pattern-analysis.md)**: Statistical quality analysis and improvement patterns

---

This enhanced guide provides the foundation for efficient driver development that aligns with no-OS standards, incorporates systematic quality improvements, and eliminates framework integration failures through comprehensive pre-implementation validation.