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

**🔧 Available Framework Validation Tools:**
- **Primary Validation**: `.claude/tools/scripts/framework_validation.sh <device> <category> <platform>`
- **Build System Skills**: Use `/no-os-make-and-linker` skill for build system guidance
- **Testing Framework**: Use `/no-os-unit-testing` skill for Ceedling/Unity/CMock validation
- **Platform-Specific Skills**:
  - `/no-os-maxim-platform` - MAX32xxx platform validation
  - `/no-os-stm32-platform` - STM32 HAL integration validation
- **GitHub Integration Agents**: `.claude/github-integration/agents/`
  - `driver-orchestrator.agent.md` - Workflow coordination and validation

**🚨 CRITICAL: Never proceed to planning without framework verification**

### **Phase 1: Planning & Approval (REQUIRED)**
1. **Planning Mode**: Enter planning mode with `EnterPlanMode` to analyze requirements
2. **Datasheet Analysis**: Extract device specifications, interface type, and command sets
3. **Framework Integration Plan**: Detail specific build system integration with verified APIs
4. **Build Validation Strategy**: Define build verification approach for each commit
5. **Plan Presentation**: Present comprehensive implementation plan to user
6. **User Approval**: Wait for explicit user approval before proceeding with implementation
7. **Plan Finalization**: Use `ExitPlanMode` when plan is approved

**📋 Available Planning & Analysis Skills:**
- **Datasheet Analysis**: Use `/datasheet-parsing` skill to extract ALL device information (features, specs, timing, registers, tables)
- **Platform Integration**: Use `/no-os-project-structure` skill for project organization and multi-platform builds
- **Testing Strategy**: Use `/testing-strategies` skill for comprehensive test planning (unit/integration/HIL)
- **Driver Architecture**: Choose appropriate driver skills based on device category:
  - **ADC Devices**: `/no-os-adc` - SAR, Sigma-Delta, channel configuration, calibration
  - **DAC Devices**: `/no-os-dac` - Voltage/current output, LDAC, synchronization
  - **Power Devices**: `/no-os-power` - PMICs, regulators, chargers, PMBus protocol
  - **IMU/Sensors**: `/no-os-imu` - Motion sensing, FIFO, calibration patterns
  - **Temperature**: `/no-os-temperature` - RTD, thermocouple, digital sensors
  - **Frequency**: `/no-os-frequency` - PLLs, VCOs, clock distribution, JESD204B
- **GitHub Integration Agents**: `.claude/github-integration/agents/`
  - `driver-planner-no-os.agent.md` - Specialized no-OS planning agent
  - `driver-planner-linux.agent.md` - Linux kernel planning agent
  - `driver-planner-zephyr.agent.md` - Zephyr RTOS planning agent

### **Phase 2: Implementation (6-Commit Pattern)**
Claude MUST follow this exact commit sequence for ALL driver implementations:

1. **Core Driver**: `drivers: <category>: <device>: Add driver support for <device>`
2. **IIO Support**: `drivers: <category>: <device>: Add IIO support for <device>`
3. **Driver Docs**: `drivers: <category>: <device>: Add README documentation for <device>`
4. **Project Files**: `projects: <device>: Add project for <device>`
5. **Project Docs**: `projects: <device>: Add README documentation for project`
6. **Unit Tests**: `tests: drivers: <category>: <device>: Add unit tests for <device>`

**🛠️ Implementation Support Skills & Tools:**

**Core Driver Implementation (Commit 1):**
- **Communication Interface**: `/no-os-i2c`, `/no-os-spi`, `/no-os-uart` - Platform abstraction patterns
- **Platform APIs**: `/no-os-gpio`, `/no-os-irq`, `/no-os-timer` - Hardware control and timing
- **Device Category Skills**:
  - **ADC**: `/no-os-adc` - Channel setup, reference/gain, conversion modes, data processing
  - **DAC**: `/no-os-dac` - Output ranges, LDAC synchronization, calibration patterns
  - **Power**: `/no-os-power` - PMBus commands, LINEAR formats, sequencing, fault handling
  - **IMU**: `/no-os-imu` - Motion detection, FIFO management, burst reads, calibration
  - **Temperature**: `/no-os-temperature` - Multi-sensor support, threshold configuration
  - **Frequency**: `/no-os-frequency` - PLL configuration, lock detection, phase control

**IIO Integration (Commit 2):**
- **IIO Framework**: `/no-os-iio` - Channel definitions, buffered acquisition, trigger handling
- **Linux IIO**: `/linux-iio` - Kernel subsystem integration, advanced features, debugging

**Platform Projects (Commit 4):**
- **Build System**: `/no-os-make-and-linker` - src.mk configuration, platform builds, dependencies
- **Project Structure**: `/no-os-project-structure` - Multi-platform organization, examples integration
- **Platform Configuration**:
  - `/no-os-maxim-platform` - MAX32xxx setup, VDDIO configuration, DMA patterns
  - `/no-os-stm32-platform` - HAL integration, RCC clocks, GPIO alternate functions

**Unit Testing (Commit 6):**
- **Testing Framework**: `/no-os-unit-testing` - Ceedling/Unity/CMock, mocking strategies, coverage
- **Quality Tools**: `.claude/tools/pre-commit/` - AStyle, Cppcheck, pattern detection
- **Coverage Analysis**: Built-in gcov support and automated coverage reporting
- **GitHub Integration Agents**: `.claude/github-integration/agents/`
  - `driver-coder-no-os.agent.md` - Specialized no-OS implementation agent
  - `driver-coder-linux.agent.md` - Linux kernel implementation agent
  - `driver-coder-zephyr.agent.md` - Zephyr RTOS implementation agent
  - `driver-documenter-no-os.agent.md` - no-OS documentation agent
  - `driver-documenter-linux.agent.md` - Linux documentation agent
  - `driver-documenter-zephyr.agent.md` - Zephyr documentation agent
  - `driver-unit-tester-no-os.agent.md` - no-OS unit testing agent

### **Phase 3: Quality Assurance (Automated)**
7. **Automated Quality** - Pattern detection and style cleanup
8. **Local Testing** - Unit tests with 80%+ coverage via Ceedling
9. **Build Validation** - Multi-platform build testing

**🔍 Available Quality Assurance Tools:**

**Code Quality & Style:**
- **Pre-commit Hooks**: `.claude/tools/pre-commit/install-hooks.sh` - AStyle, Cppcheck, branch validation
- **Pattern Detection**: `.claude/tools/pre-commit/review-checker.py` - 6-month analysis, 62.5% automation
- **SonarCloud Integration**: `.claude/tools/pre-commit/setup-local-sonar.sh` - Local static analysis
- **Linux Code Quality**: `/linux-checkpatch-sparse` - Kernel coding standards, sparse analysis

**Testing & Coverage:**
- **Unit Testing**: `/no-os-unit-testing` - Comprehensive Ceedling/Unity/CMock framework
- **Coverage Targets**: 80%+ code coverage with gcov integration and automated reporting
- **Testing Strategies**: `/testing-strategies` - Unit/integration/HIL across platforms
- **Quality Validation**: `.claude/tools/pre-commit/validate-setup.sh` - Environment verification

**Build System Validation:**
- **Multi-platform Builds**: Python build scripts for xilinx, stm32, maxim, mbed, pico, aducm3029, lattice
- **Build System Skills**: `/no-os-make-and-linker` - src.mk validation, dependency checking
- **Platform Verification**: Platform-specific skills for build environment validation
- **GitHub Actions Workflows**: `.claude/github-integration/workflows/`
  - `ci-enhanced.yml` - Enhanced CI with metrics and multi-platform builds
  - `sonarcloud.yml` - Automated SonarCloud static analysis

**Automated Pattern Analysis:**
- **Review Pattern Automation**: 144 PRs analyzed, 507 comments categorized, 62.5% prevention rate
- **Real-time Quality**: `.claude/tools/pre-commit/auto-update-patterns.py` - Continuous improvement
- **Quality Metrics**: Complete 6-month statistical analysis for systematic improvement
- **GitHub Integration Agents**: `.claude/github-integration/agents/`
  - `driver-code-reviewer-no-os.agent.md` - no-OS code review agent
  - `driver-code-reviewer-linux.agent.md` - Linux kernel code review agent
  - `driver-code-reviewer-zephyr.agent.md` - Zephyr RTOS code review agent
- **GitHub Actions Workflows**: `.claude/github-integration/workflows/`
  - `update-review-patterns.yml` - Automated weekly pattern analysis updates
  - `security-analysis.yml` - Automated security vulnerability scanning
  - `dashboard.yml` - Development metrics and dashboard automation

### **Phase 4: Submission**
10. **PR Creation** - Submit with proper commit messages and complete build system
11. **Review & Iteration** - Address feedback with 62.5% issue prevention
12. **Hardware Testing** - Validate on target hardware
13. **Merge** - Maintainer approval and integration

**🔄 Automated Submission Support:**
- **GitHub Actions Workflows**: `.claude/github-integration/workflows/`
  - `labeler.yml` - Automated PR labeling based on file paths and content

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
✅ NO AI attribution in any files (author field = configured git user)
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
- **No AI Attribution**: NEVER include AI attribution in code files, commits, or headers (no Co-Authored-By Claude, no "Generated with" mentions, etc.) - Use configured git user information
- **Git Configuration**: Use configured git user.name and user.email from `git config --global` for all commits and author attribution
- **Resolve Commit Issues**: NEVER use --no-verify flags - Instead resolve pre-commit hook findings and quality issues properly

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
system patterns to prevent integration failures.

Let me use the framework validation tools and platform-specific skills to ensure proper integration."

[Claude performs framework verification using .claude/tools/scripts/framework_validation.sh and /no-os-maxim-platform skill, optionally delegating to driver-orchestrator.agent.md for workflow coordination]

Claude: "Framework verification complete:
✅ Build system patterns validated (individual file includes, no wildcards)
✅ Platform APIs confirmed (maxim_uart.h, MAX_UART_FLOW_DIS constants)
✅ Test framework version verified (Ceedling 1.0.1, current Unity/CMock patterns)
✅ API signatures validated (CRC, IIO, no-OS core APIs)

Now entering planning mode for comprehensive implementation strategy."

[Claude uses EnterPlanMode tool]

Claude: "
IMPLEMENTATION PLAN: LTM4700 PMBus Dual-Channel Regulator Driver

ANALYSIS (using /datasheet-parsing and /no-os-power skills):
- Device: LTM4700 dual 50A or single 100A μModule regulator
- Interface: PMBus 1.3 compliant I2C (default address 0x5A)
- Variant Support: LTM4777 through device ID detection
- Channels: Dual-channel power monitoring and control

IMPLEMENTATION STRATEGY (guided by specialized skills):
1. Core Driver (drivers/power/ltm4700/) - Using /no-os-power skill
   - Complete PMBus command set implementation
   - Dual-channel support with PAGE commands
   - LINEAR11/LINEAR16 data format conversion
   - Device identification (LTM4700 vs LTM4777)

2. IIO Integration (REQUIRED for monitoring devices) - Using /no-os-iio skill
   - 12 IIO channels: VIN, IIN, PIN, VOUT0/1, IOUT0/1, POUT0/1, TEMP1/2/3
   - Write support for VOUT control
   - Linux Industrial I/O subsystem compliance

3. Project Structure (projects/ltm4700/) - Using /no-os-project-structure skill
   - Multi-platform build system (MAX32655, STM32, Linux, etc.)
   - Basic telemetry monitoring example
   - IIO integration example

4. Unit Testing (tests/drivers/power/ltm4700/) - Using /no-os-unit-testing skill
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

[Claude executes the 6-commit implementation autonomously, optionally using driver-coder-no-os.agent.md, driver-documenter-no-os.agent.md, and driver-unit-tester-no-os.agent.md for specialized workflow phases]
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
- **🚨 USE SPECIALIZED SKILLS** - Leverage `.claude/skills/` for domain-specific guidance:
  - `/datasheet-parsing` for comprehensive device analysis
  - Device-specific skills (`/no-os-power`, `/no-os-adc`, `/no-os-dac`, etc.) for implementation
  - `/no-os-unit-testing` for comprehensive test coverage
  - Platform skills (`/no-os-maxim-platform`, `/no-os-stm32-platform`) for integration
  - GitHub integration agents (`.claude/github-integration/agents/`) for autonomous workflow execution
- **🚨 NO intermediate questions** - Don't ask about `cd`, `ls`, file paths, etc.
- **🚨 Complete implementation** - All 6 components (driver, IIO, project, tests, docs)
- **🚨 No "-eval" suffix** - Projects are `projects/<device>` NOT `projects/<device>-eval`
- **🚨 Autonomous execution** - After plan approval, execute without further questions
- **🚨 NO AI attribution** - Never add AI attribution to code files, commits, or headers - Use configured git user information
- **🚨 Git configuration compliance** - Use configured git user.name and user.email from `git config --global`
- **🚨 Quality enforcement** - NEVER use --no-verify flags, instead resolve pre-commit hook findings and quality issues properly

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

## Git Configuration and Commit Standards

### **Git User Configuration**
All commits MUST use the configured git user information:
- **Name**: Use value from `git config --global user.name`
- **Email**: Use value from `git config --global user.email`

### **Commit Message Standards**
Follow the established format for all commits:
```
<scope>: <component>: <description>

Signed-off-by: <Name> <email@domain.com>
```

Example:
```
drivers: power: ltm4700: Add driver support for ltm4700

Add comprehensive PMBus driver for LTM4700 dual-channel regulator.
Includes support for device identification, dual-channel monitoring,
and complete LINEAR format conversion.

Signed-off-by: <Name> <email@domain.com>
```

### **Quality Enforcement Policy**
**🚨 CRITICAL: NEVER use bypass flags like --no-verify**

Instead of bypassing quality checks:
1. **Resolve AStyle issues**: Fix formatting and style violations
2. **Address Cppcheck warnings**: Fix static analysis findings
3. **Satisfy pre-commit hooks**: Resolve pattern detection issues
4. **Fix build errors**: Ensure clean compilation across platforms
5. **Complete unit tests**: Achieve 80%+ code coverage

**Philosophy**: Quality issues indicate real problems that need fixing, not obstacles to bypass.

---

## Pre-Submission Checklist

Before creating a PR, verify:

### **🚨 Framework Verification (MANDATORY FIRST)**
- [ ] Framework validation passes (`./.claude/tools/scripts/framework_validation.sh`)
- [ ] Build system patterns verified (no wildcards, individual includes)
- [ ] Platform APIs confirmed (headers exist, constants validated)
- [ ] Test framework version verified (Ceedling 1.0.1, modern format)
- [ ] API signatures validated (no-OS, IIO, platform-specific)

### **🚨 CRITICAL: Documentation Files (ALL 4 REQUIRED)**
- [ ] Driver README: `drivers/<category>/<device>/README.rst`
- [ ] Project README: `projects/<device>/README.rst`
- [ ] Driver Sphinx: `doc/sphinx/source/drivers/<category>/<device>.rst`
- [ ] **Project Sphinx**: `doc/sphinx/source/projects/<category>/<device>.rst` ⚠️ **COMMONLY MISSED**

**Sphinx File Content Pattern:**
```rst
.. include:: ../../../../../projects/<device>/README.rst
```

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
- [ ] All commits signed off (`-s`) using configured git user information from `git config --global`

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

## 🎯 Claude Skills & Automation (.claude/)

### Comprehensive Skill Library (.claude/skills/)

**🔧 Framework & Build System:**
- **`/no-os-make-and-linker`** - Build system, Makefile configuration, src.mk patterns, linker scripts
- **`/no-os-project-structure`** - Project organization, multi-platform builds, examples integration
- **`/no-os-debugging`** - UART console, JTAG/SWD, error codes, initialization troubleshooting

**📡 Communication Protocols:**
- **`/no-os-i2c`** - I2C platform drivers, bus management, multi-device configurations
- **`/no-os-spi`** - SPI platform drivers, modes, multi-slave, DMA integration
- **`/no-os-uart`** - UART platform drivers, configuration, flow control

**⚡ Hardware Control:**
- **`/no-os-gpio`** - GPIO control, direction, pull-resistors, interrupt handling
- **`/no-os-irq`** - Interrupt handling, callbacks, priority configuration
- **`/no-os-timer`** - Hardware timers, delays, time measurement

**📊 Device Categories:**
- **`/no-os-adc`** - SAR/Sigma-Delta ADCs, channels, reference/gain, calibration, IIO integration
- **`/no-os-dac`** - Voltage/current output, LDAC synchronization, slew rate, calibration
- **`/no-os-power`** - PMICs, regulators, chargers, PMBus protocol, DVS, battery management
- **`/no-os-imu`** - Motion sensing, FIFO, motion detection, calibration, burst reads
- **`/no-os-temperature`** - RTD, thermocouple, digital sensors, thresholds, multi-sensor hubs
- **`/no-os-frequency`** - PLLs, VCOs, clock distribution, JESD204B, phase control

**💻 Platform-Specific:**
- **`/no-os-maxim-platform`** - MAX32xxx initialization, VDDIO, DMA, pin multiplexing
- **`/no-os-stm32-platform`** - HAL integration, RCC clocks, GPIO alternate functions

**🧪 Testing & Quality:**
- **`/no-os-unit-testing`** - Ceedling/Unity/CMock, mocking strategies, 80%+ coverage
- **`/testing-strategies`** - Unit/integration/HIL testing across platforms
- **`/no-os-iio`** - Industrial I/O framework, channels, buffered acquisition

**📖 Analysis & Documentation:**
- **`/datasheet-parsing`** - Complete datasheet extraction (features, specs, registers, timing)

**🐧 Linux Kernel Development:**
- **`/linux-iio`** - IIO subsystem, channels, buffered acquisition, advanced features
- **`/linux-pmbus`** - PMBus drivers, multi-page devices, direct format coefficients
- **`/linux-hwmon`** - Hardware monitoring, sensors, voltage/current/temperature
- **`/linux-devicetree`** - Devicetree bindings, YAML schema, validation
- **`/linux-gpio`**, **`/linux-i2c-controller`**, **`/linux-spi-controller`** - Kernel subsystems
- **`/linux-debugging`** - ftrace, printk, KASAN, lockdep, Raspberry Pi testing
- **`/linux-checkpatch-sparse`** - Code quality, kernel coding standards

**⚙️ Zephyr RTOS Development:**
- **Device Drivers**: `/zephyr-adc`, `/zephyr-dac`, `/zephyr-gpio`, `/zephyr-sensor`, `/zephyr-regulator`
- **Communication**: `/zephyr-i2c`, `/zephyr-spi`, `/zephyr-uart`
- **Power Management**: `/zephyr-charger`, `/zephyr-fuel-gauge`
- **System**: `/zephyr-build-system`, `/zephyr-devicetree`, `/zephyr-unit-testing`
- **Control**: `/zephyr-pwm`, `/zephyr-led`
- **Advanced**: `/zephyr-mfd` - Multi-Function Device drivers

### Automation Tools (.claude/tools/)

**🔍 Quality Assurance:**
```bash
.claude/tools/pre-commit/install-hooks.sh              # Complete pre-commit setup
.claude/tools/pre-commit/validate-setup.sh             # Environment verification
.claude/tools/pre-commit/review-checker.py             # 6-month pattern analysis
.claude/tools/pre-commit/setup-local-sonar.sh          # SonarCloud integration
```

**🏗️ Build & Development:**
```bash
.claude/tools/scripts/framework_validation.sh          # MANDATORY framework verification
.claude/tools/scripts/build_projects.py                # Multi-platform builds
.claude/tools/pre-commit/create-device-template.py     # Device template generation
.claude/tools/pre-commit/new-dev-branch.sh            # Branch creation automation
```

**📈 Pattern Automation:**
```bash
.claude/tools/pre-commit/auto-update-patterns.py       # Continuous improvement
.claude/tools/pre-commit/configure-pattern-automation.sh # Setup automation
.claude/tools/transfer-to-repository.sh                # Repository migration
```

### GitHub Actions Workflows (.claude/github-integration/workflows/)

**🏗️ CI/CD Automation:**
```bash
ci-enhanced.yml                                        # Enhanced CI with metrics and multi-platform builds
sonarcloud.yml                                         # Automated SonarCloud static analysis and security scanning
```

**📊 Quality & Analytics:**
```bash
update-review-patterns.yml                             # Weekly automated review pattern analysis updates
security-analysis.yml                                  # Comprehensive security vulnerability scanning
dashboard.yml                                          # Development metrics and dashboard automation
```

**🔄 Repository Management:**
```bash
labeler.yml                                           # Automated PR labeling based on file paths and content changes
```

### GitHub Integration Agents (.claude/github-integration/agents/)

**🎯 Workflow Coordination:**
```bash
driver-orchestrator.agent.md                           # Complete workflow orchestration
```

**📋 Planning Agents:**
```bash
driver-planner-no-os.agent.md                         # no-OS driver planning
driver-planner-linux.agent.md                         # Linux kernel driver planning
driver-planner-zephyr.agent.md                        # Zephyr RTOS driver planning
```

**⚙️ Implementation Agents:**
```bash
driver-coder-no-os.agent.md                           # no-OS driver implementation
driver-coder-linux.agent.md                           # Linux kernel driver implementation
driver-coder-zephyr.agent.md                          # Zephyr RTOS driver implementation
```

**📖 Documentation Agents:**
```bash
driver-documenter-no-os.agent.md                      # no-OS driver documentation
driver-documenter-linux.agent.md                      # Linux kernel driver documentation
driver-documenter-zephyr.agent.md                     # Zephyr RTOS driver documentation
```

**🧪 Testing & Review Agents:**
```bash
driver-unit-tester-no-os.agent.md                     # no-OS unit testing
driver-code-reviewer-no-os.agent.md                   # no-OS code review
driver-code-reviewer-linux.agent.md                   # Linux kernel code review
driver-code-reviewer-zephyr.agent.md                  # Zephyr RTOS code review
```

**🛠️ Skill Development:**
```bash
skill-creator-no-os.agent.md                          # no-OS skill creation
skill-creator-zephyr.agent.md                         # Zephyr skill creation
```

### Usage Guidelines

**🎯 Direct Skill Invocation:**
- Use `/skill-name` format to invoke skills directly
- Skills provide comprehensive domain-specific guidance
- All skills include troubleshooting and best practices

**🔧 Tool Integration:**
- Framework validation is **MANDATORY** before any implementation
- Quality tools provide 62.5% automated issue prevention
- Build tools support all major embedded platforms

**🤖 GitHub Integration Agents:**
- Use specialized agents for complex multi-phase driver development
- Agents provide autonomous execution for specific workflow phases
- Platform-specific agents (no-OS, Linux, Zephyr) ensure proper implementation patterns
- Orchestrator agent coordinates complete end-to-end workflows

**🔄 GitHub Actions Workflows:**
- Automated CI/CD pipelines for continuous integration and deployment
- Enhanced multi-platform build validation with metrics collection
- Automated code quality analysis (SonarCloud, security scanning)
- Weekly review pattern updates for continuous process improvement
- Automated PR management and labeling for efficient workflow

**📚 Comprehensive Coverage:**
- 40+ specialized skills covering all aspects of embedded development
- 16 GitHub integration agents for autonomous workflow execution
- 6 GitHub Actions workflows for automated CI/CD and quality assurance
- Cross-platform support (no-OS, Linux, Zephyr)
- Complete development lifecycle (analysis → implementation → testing → quality → deployment)

This skill library provides comprehensive guidance for all aspects of driver development, from initial datasheet analysis through final quality assurance and testing.

---

This enhanced guide provides the foundation for efficient driver development that aligns with no-OS standards, incorporates systematic quality improvements, and eliminates framework integration failures through comprehensive pre-implementation validation.