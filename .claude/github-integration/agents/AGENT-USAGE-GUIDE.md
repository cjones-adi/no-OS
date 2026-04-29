# Agent Usage Guide

This guide explains how to use the no-OS, Linux, and Zephyr RTOS driver development agents both standalone and as part of the full workflow.

## Path Configuration

> **AUTO-DETECTION**: When you see `{WORKSPACE}` in this documentation, agents will automatically detect which path to use:
> - Checks if `.github/agents/` exists → uses `.github`
> - Otherwise checks if `.claude/agents/` exists → uses `.claude`
> - Falls back to `.github` if neither exists
>
> All paths like `{WORKSPACE}/agents/`, `{WORKSPACE}/skills/`, `{WORKSPACE}/docs/` are automatically resolved at runtime.
>
> **For humans reading this**: Replace `{WORKSPACE}` mentally with whichever folder you're using (`.github` or `.claude`).

## Supported Platforms

Agents are available for three platforms:

- **no-OS**: Lightweight embedded framework (agents: `*-no-os`)
- **Linux**: Linux kernel drivers (agents: `*-linux`)
- **Zephyr**: Zephyr RTOS drivers (agents: `*-zephyr`)

Choose the agent matching your target platform. The workflow and capabilities are similar across platforms, with platform-specific conventions.

## Available Resources

### Skills Library
The `skills/` directory contains subsystem-specific technical knowledge that agents reference when implementing drivers. Skills provide:

- Detailed implementation patterns for specific driver types
- Subsystem architecture and key APIs
- Device tree binding examples
- Common pitfalls and best practices
- Reference to well-implemented kernel drivers

**Current Skills**:
- **Linux**:
  - `skills/linux/hwmon/SKILLS.md` - PMBus power supply/regulator monitoring
  - `skills/linux/iio/SKILLS.md` - IIO ADC drivers
  - *(More coming soon - see skills/README.md)*

Agents automatically reference relevant skills when working on subsystem-specific drivers.

---

## Zephyr RTOS Agents

### Available Zephyr Agents

- **driver-planner-zephyr**: Research and create SRS for Zephyr drivers
- **driver-coder-zephyr**: Implement Zephyr drivers with devicetree and Kconfig
- **driver-code-reviewer-zephyr**: Review Zephyr driver code for compliance
- **driver-documenter-zephyr**: Create documentation for Zephyr drivers

### Zephyr-Specific Features

Zephyr agents understand:
- **Devicetree**: Binding creation, property definition, compile-time configuration
- **Kconfig**: Build configuration, dependencies, feature options
- **Zephyr APIs**: Subsystem APIs (GPIO, Sensor, DAC, etc.), logging, threading
- **Code Style**: Zephyr coding standards, checkpatch.pl compliance
- **Build System**: West, CMake, subsystem integration

### Quick Start with Zephyr Agents

**Create a new Zephyr driver**:
```
@driver-planner-zephyr create SRS for MAX4822 8-channel relay driver
[Review SRS]
@driver-coder-zephyr implement driver based on SRS
@driver-documenter-zephyr create sample and documentation
@driver-code-reviewer-zephyr review implementation
```

**Review existing Zephyr driver**:
```
@driver-code-reviewer-zephyr review drivers/gpio/gpio_max4822.c
```

**Add documentation**:
```
@driver-documenter-zephyr create sample README for drivers/gpio/gpio_max4822.c
```

---

## Two Ways to Use Agents

### 1. Full Workflow (via Orchestrator)
For complete driver development from scratch with planning, implementation, documentation, testing, and review.

### 2. Standalone (Direct Agent Invocation)
For specific tasks on existing code without formal planning or SRS.

---

## Standalone Agent Usage

### Zephyr Code Review (driver-code-reviewer-zephyr)

**When to use**:
- Review existing Zephyr driver code
- Check devicetree binding compliance
- Verify Kconfig integration
- Pre-submission review
- Zephyr coding standards check

**How to invoke**:
```
@driver-code-reviewer-zephyr review drivers/gpio/gpio_max4822.c
```

**What you need**:
- Path to driver .c file
- (Optional) Path to devicetree binding .yaml file
- (Optional) Path to sample application
- (Optional) Path to SRS document

**What you get**:
- Zephyr checkpatch.pl compliance report
- Devicetree binding review
- Kconfig integration review
- Build verification
- Code quality analysis
- Subsystem API compliance check
- Structured review report with priorities

**Example**:
```
@driver-code-reviewer-zephyr

Please review the MAX4822 GPIO driver:
- drivers/gpio/gpio_max4822.c
- dts/bindings/gpio/adi,max4822.yaml
- samples/drivers/gpio_max4822/

Focus on devicetree integration and thread safety.
```

---

### Zephyr Implementation (driver-coder-zephyr)

**When to use**:
- Implement new Zephyr driver
- Add features to existing driver
- Create devicetree bindings
- Integrate Kconfig options
- Create sample applications

**How to invoke**:
```
@driver-coder-zephyr implement MAX4822 GPIO driver according to SRS
```

**What you need**:
- SRS document (from driver-planner-zephyr) or feature description
- Hardware specifications
- Target subsystem (GPIO, Sensor, DAC, etc.)

**What you get**:
- Driver source (.c file)
- Devicetree binding (.yaml file)
- Kconfig configuration
- CMakeLists.txt integration
- Sample application
- Board overlay examples
- Build-verified code

**Example**:
```
@driver-coder-zephyr

Implement GPIO controller driver for MAX4822:
- 8-channel relay driver
- SPI interface
- Hardware reset/set pins
- Use SRS at docs/max4822-srs.md
```

---

### Zephyr Documentation (driver-documenter-zephyr)

**When to use**:
- Create sample README
- Document devicetree binding
- Add usage examples
- Create troubleshooting guides
- Document configuration options

**How to invoke**:
```
@driver-documenter-zephyr create documentation for drivers/gpio/gpio_max4822.c
```

**What you need**:
- Path to driver source
- (Optional) Path to sample application
- (Optional) Datasheet link

**What you get**:
- Sample README.rst (reStructuredText)
- Devicetree configuration examples
- Kconfig documentation
- Usage examples with code
- Troubleshooting section
- References to datasheet and Zephyr docs

**Example**:
```
@driver-documenter-zephyr

Create sample documentation for:
- drivers/gpio/gpio_max4822.c
- samples/drivers/gpio_max4822/

Include devicetree examples for nRF52 and STM32 boards.
```

---

### Zephyr Planning (driver-planner-zephyr)

**When to use**:
- Research before implementing new driver
- Create SRS for Zephyr driver
- Understand Zephyr subsystem patterns
- Plan devicetree binding
- Design Kconfig integration

**How to invoke**:
```
@driver-planner-zephyr create SRS for MAX4822 relay driver
```

**What you need**:
- Driver name and hardware specifications
- (Optional) Datasheet link or file
- Target Zephyr subsystem
- (Optional) Similar existing drivers

**What you get**:
- Complete SRS document
- Proposed subsystem integration
- Devicetree binding specification
- Kconfig design
- API structure (subsystem or custom)
- Data structures (config and data)
- Implementation phases

**Example**:
```
@driver-planner-zephyr

Research and create SRS for MAX31865 RTD-to-Digital converter:
- SPI interface
- Zephyr Sensor subsystem
- Datasheet: [link]
- Reference: drivers/sensor/max6675/
```

---

### no-OS/Linux Code Review (driver-code-reviewer)

**When to use**:
- Review existing driver code
- Check code before committing
- Quick bug scan
- CI compliance check
- Learn from historical review patterns

**How to invoke**:
```
@driver-code-reviewer review drivers/adc/ad7124/ad7124.c and ad7124.h
```

**What you need**:
- Path to driver .c and .h files
- (Optional) Path to test files
- (Optional) Path to SRS document

**What you get**:
- CI compliance report (astyle, cppcheck, docs)
- Historical issue analysis
- Bug and safety findings
- Style and standards check
- Test coverage assessment
- Structured review report with priorities

**Example**:
```
@driver-code-reviewer

Please review the following files:
- drivers/temperature/max31865/max31865.c
- drivers/temperature/max31865/max31865.h

Focus on memory safety and error handling.
```

---

### Unit Testing (driver-unit-tester)

**When to use**:
- Add tests to existing driver
- Improve test coverage
- Test-driven development
- Create tests without SRS

**How to invoke**:
```
@driver-unit-tester create tests for drivers/dac/ad5766/ad5766.c targeting 80% coverage
```

**What you need**:
- Path to driver .c and .h files
- (Optional) Existing test files to extend
- (Optional) Path to SRS document
- (Optional) Coverage target (default: 80%)

**What you get**:
- Complete test suite in `tests/drivers/test/test_[driver]/`
- Mock/stub implementations
- Ceedling configuration
- Test execution commands
- Coverage report

**Example**:
```
@driver-unit-tester

Create comprehensive unit tests for:
- drivers/adc/ad7124/ad7124.c
- drivers/adc/ad7124/ad7124.h

Cover all public APIs and error conditions. Target 85% coverage.
```

---

### Implementation (driver-coder)

**When to use**:
- Implement specific feature addition
- Fix bugs with proper style
- Refactor existing code
- Generate sample applications

**How to invoke**:
```
@driver-coder implement the ad7124_read_temperature() function in drivers/adc/ad7124/ad7124.c
```

**What you need**:
- Description of what to implement
- Path to files to modify
- (Optional) Path to SRS for context
- (Optional) Reference driver for patterns

**What you get**:
- Implemented code following no-OS standards
- Minimal but necessary comments
- Named constants (no magic numbers)
- Build-verified code

**Example**:
```
@driver-coder

Add support for continuous read mode in drivers/dac/ad5766/ad5766.c
Reference similar implementation in drivers/dac/ad5758/ad5758.c
```

---

### Documentation (driver-documenter)

**When to use**:
- Create README for existing driver (no SRS needed)
- Document example application
- Improve existing documentation
- Add API reference from code
- Document legacy drivers

**How to invoke**:
```
@driver-documenter create README for drivers/adc/ad7124/
```

**What you need**:
- Path to driver source files
- (Optional) Path to example application
- (Optional) Path to SRS
- (Optional) Datasheet link

**What you get**:
- Driver README.md with API reference
- Example README.md with usage guide (if example exists)
- Hardware setup instructions
- Configuration options explained
- Troubleshooting section

**Without SRS or Example**:
- Documents from code analysis and Doxygen comments
- Creates usage examples within driver README
- References similar drivers for patterns

**Example**:
```
@driver-documenter

Generate documentation for drivers/temperature/max31865/
No SRS or example available - infer from code.
```

**Example with everything**:
```
@driver-documenter

Generate comprehensive documentation for:
- drivers/temperature/max31865/
- projects/max31865-example/

Include hardware connection diagrams and common issues.
```

---

### Planning (driver-planner)

**When to use**:
- Research before implementing new driver
- Create SRS document
- Understand existing codebase patterns
- Get API recommendations

**How to invoke**:
```
@driver-planner create SRS for AD7768-1 24-bit ADC driver
```

**What you need**:
- Driver name and hardware specs
- (Optional) Datasheet link or file
- (Optional) Similar existing drivers for reference

**What you get**:
- Complete SRS document in `docs/srs/[driver]-srs.md`
- Proposed API structure
- Hardware requirements
- Implementation checklist

**Example**:
```
@driver-planner

Research and create SRS for MAX20360 PMIC driver
Datasheet: https://datasheets.maximintegrated.com/en/ds/MAX20360.pdf
Reference similar drivers: drivers/power/lt8491/
```

---

## Full Workflow (via Orchestrator)

**When to use**:
- Complete driver development from scratch
- Formal development process with reviews
- Team collaboration with approval gates
- Full traceability (SRS → Code → Tests → Review)

**How to invoke**:
```
@driver-orchestrator develop driver for AD7124 24-bit ADC
```

**What happens**:
1. **Planning Phase**: Creates SRS, waits for your approval
2. **Implementation Phase**: Implements driver, waits for your approval
3. **Documentation Phase**: Creates README files, waits for your approval
4. **Unit Testing Phase**: Creates tests, reports results, waits for your approval
5. **Review Phase**: Reviews everything, waits for your final approval
6. **Iteration**: Repeats if needed

**Example**:
```
@driver-orchestrator

Develop complete driver for MAX31865 RTD-to-Digital converter
- SPI interface
- Supports 2-wire, 3-wire, 4-wire RTD configurations
- Temperature reading with fault detection
- Reference existing temperature drivers

Create full implementation with tests and documentation.
```

---

## Agent Combinations

You can chain agents for specific workflows:

### Review → Fix → Review Again
```
1. @driver-code-reviewer review drivers/adc/ad7124/ad7124.c
2. [Review report shows issues]
3. @driver-coder fix the memory leak in ad7124_init() error path
4. @driver-code-reviewer re-review drivers/adc/ad7124/ad7124.c
```

### Code → Test → Review
```
1. @driver-coder implement drivers/new_driver/new_driver.c
2. @driver-unit-tester create tests for drivers/new_driver/
3. @driver-code-reviewer review everything in drivers/new_driver/
```

### Plan → Implement → Document
```
1. @driver-planner create SRS for AD7768-1
2. @driver-coder implement based on docs/srs/ad7768-1-srs.md
3. @driver-documenter create README for drivers/adc/ad7768-1/
```

---

## Tips for Effective Agent Usage

### Be Specific
❌ "Review my code"
✅ "Review drivers/adc/ad7124/ad7124.c focusing on error handling and memory safety"

### Provide Context
❌ "Add tests"
✅ "Add tests for drivers/dac/ad5766/ad5766.c, reference tests/drivers/test/test_ad5758/ for patterns, target 85% coverage"

### Use References
- Point to similar drivers for patterns
- Reference existing tests for style
- Provide datasheet links for planning

### Iterate
- Agents can be called multiple times
- Review results and request refinements
- Use feedback loop to improve quality

### Combine Agents
- Use code-reviewer after driver-coder
- Use unit-tester after driver-coder
- Use documenter after everything is working

---

## Common Workflows

### Quick Review of Existing Code
```
@driver-code-reviewer review drivers/[path]
```

### Add Tests to Legacy Driver
```
@driver-unit-tester create tests for drivers/[path] targeting 80% coverage
```

### Fix Bug with Proper Style
```
@driver-coder fix [bug description] in drivers/[path]/[file].c following no-OS standards
```

### Create Documentation
```
@driver-documenter create README for drivers/[path] and projects/[example]
```

### Full Driver Development
```
@driver-orchestrator develop complete driver for [chip name] with [brief specs]
```

---

## Agent Files Location

All agents are in `{WORKSPACE}/agents/`:

**no-OS Agents**:
- `driver-orchestrator.agent.md` - Full workflow coordinator
- `driver-planner-no-os.agent.md` - Research and SRS creation
- `driver-coder-no-os.agent.md` - Code implementation
- `driver-documenter-no-os.agent.md` - Documentation generation
- `driver-unit-tester-no-os.agent.md` - Unit test creation
- `driver-code-reviewer-no-os.agent.md` - Code review and quality

**Linux Agents**:
- `driver-planner-linux.agent.md` - Research and SRS creation for Linux
- `driver-coder-linux.agent.md` - Linux kernel driver implementation
- `driver-documenter-linux.agent.md` - Linux driver documentation
- `driver-code-reviewer-linux.agent.md` - Linux driver review

**Zephyr RTOS Agents**:
- `driver-planner-zephyr.agent.md` - Research and SRS creation for Zephyr
- `driver-coder-zephyr.agent.md` - Zephyr driver implementation
- `driver-documenter-zephyr.agent.md` - Zephyr driver documentation
- `driver-code-reviewer-zephyr.agent.md` - Zephyr driver review

Historical data: `{WORKSPACE}/agents/data/review-history.json`

---

## Need Help?

- Read the individual agent .md files for detailed capabilities
- Check `{WORKSPACE}/agents/data/README.md` for historical review data info
- Look at existing drivers in `drivers/` for patterns
- Look at existing tests in `tests/drivers/test/` for test patterns
