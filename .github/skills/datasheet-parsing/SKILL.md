---
name: datasheet-parsing
description: 'Complete guide to datasheet parsing with pdfplumber for extracting ALL information (features, electrical specs, timing, registers, tables) from hardware datasheets. Use for comprehensive extraction beyond just register maps - includes tracking checklist for planner agents. Works for all platforms: no-OS, Zephyr, and Linux.'
---

> **📁 Path Configuration - Auto-Detection**
> This skill uses `{WORKSPACE}` as a placeholder. **Agents automatically detect** which path to use:
> - Check if `.github/agents/` exists → use `.github`
> - Otherwise check if `.claude/agents/` exists → use `.claude`
> - Fallback to `.github` if neither exists
>
> Replace all `{WORKSPACE}` references with the detected value when using file paths.

# Hardware Datasheet Parsing Tools

This skill provides comprehensive guidance on using Python parser tools and pdfplumber to extract **all information** from datasheets - not just register tables - for driver development planning and implementation.

## When to Use This Skill

Use this skill when you need to:
- Extract register maps from PDF datasheets
- Parse XML/CSV/YAML/YDA hardware specification files
- Extract PMBus command tables
- Generate C header files from register definitions
- Extract bit field definitions with descriptions
- Convert datasheet tables to structured JSON
- Prepare hardware specifications for SRS creation
- Parse datasheets **without invoking planner agents**

## ⚠️ CRITICAL: Complete Information Extraction Strategy

**ALWAYS extract ALL information from datasheets using pdfplumber, not just register tables.**

Specialized parsers (bitfield_parser, reg_parser, pmbus_parser) extract **structured register/command data** for implementation, but planner agents and users need **complete device context** for SRS creation, feature planning, and driver design decisions.

### Why Complete Extraction Matters

❌ **What specialized parsers MISS** (but planners need):
- **Features & Capabilities**: Operating modes, supported protocols, channel counts
- **Electrical Specifications**: Supply voltage, current consumption, power dissipation
- **Timing Requirements**: Clock frequencies, setup/hold times, conversion rates
- **Temperature Ranges**: Operating/storage temperatures, thermal considerations
- **Pin Descriptions**: Pin functions, configuration options, alternate functions
- **Initialization Sequences**: Power-up procedures, calibration requirements
- **Application Notes**: Recommended circuits, layout guidelines, design tips
- **Error Handling**: Fault conditions, diagnostic features, recovery procedures
- **Communication Interfaces**: I2C/SPI modes, speeds, addressing, timing diagrams
- **Feature Dependencies**: Mode interactions, register dependencies, initialization order

✅ **What datasheet_reader.py provides**:
- ALL text content from every page
- ALL tables (electrical specs, timing, pinout, feature tables)
- Complete context for understanding device behavior
- Information needed for comprehensive SRS requirements

### Comprehensive Information Tracking Checklist

When extracting datasheets for planner agents, **track and provide ALL of the following**:

#### 1. Device Overview
- [ ] Part number and variant identification
- [ ] Key features and capabilities summary
- [ ] Target applications and use cases
- [ ] Block diagram and architecture overview
- [ ] Functional modes and operating states

#### 2. Electrical Characteristics
- [ ] Supply voltage range (min/typ/max)
- [ ] Current consumption (active, sleep, shutdown modes)
- [ ] Power dissipation and thermal limits
- [ ] Input/output voltage levels and thresholds
- [ ] Drive strength and load capacitance
- [ ] ESD protection levels

#### 3. Communication Interface Details
- [ ] Protocol support (I2C, SPI, UART, etc.)
- [ ] Address configuration and slave addressing
- [ ] Clock frequency ranges (min/max)
- [ ] Timing requirements (setup, hold, access times)
- [ ] Data formats and byte ordering
- [ ] Read/write transaction examples

#### 4. Timing Specifications
- [ ] Clock requirements and frequencies
- [ ] Setup and hold times
- [ ] Conversion times and delays
- [ ] Startup/power-up timing
- [ ] Response times for commands
- [ ] Settling times for outputs

#### 5. Pin Configuration
- [ ] Pin names, numbers, and functions
- [ ] Alternate pin functions
- [ ] Input/output types (digital, analog, open-drain, etc.)
- [ ] Pull-up/pull-down requirements
- [ ] Pin strapping and configuration

#### 6. Operating Modes
- [ ] All supported modes (normal, low-power, calibration, etc.)
- [ ] Mode transitions and requirements
- [ ] Mode-specific behaviors
- [ ] Configuration register settings per mode
- [ ] Mode dependencies and restrictions

#### 7. Register Map (from specialized parsers)
- [ ] Register addresses and names
- [ ] Bit field definitions and positions
- [ ] Access types (R, W, R/W)
- [ ] Reset/default values
- [ ] Bit field descriptions and decode values

#### 8. Initialization & Configuration
- [ ] Power-up sequence
- [ ] Required initialization steps
- [ ] Calibration procedures
- [ ] Configuration register programming order
- [ ] Default settings verification

#### 9. Error Handling & Diagnostics
- [ ] Error conditions and flags
- [ ] Interrupt sources and configuration
- [ ] Fault detection mechanisms
- [ ] Recovery procedures
- [ ] Diagnostic features

#### 10. Application Information
- [ ] Recommended external components
- [ ] PCB layout guidelines
- [ ] Decoupling capacitor requirements
- [ ] Signal routing recommendations
- [ ] EMI/EMC considerations

### Standard Extraction Workflow for Planners

**Step 1: Extract complete datasheet** (MANDATORY):
```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py {WORKSPACE}/docs/datasheet.pdf \
    -o {WORKSPACE}/docs/[chip]_complete.json --pretty
```

**What this provides**:
- Complete text from all 100+ pages
- ALL tables (electrical, timing, features, pinout)
- Full context for SRS requirements
- Application notes and design guidelines

**Step 2: Extract bitfield definitions**:
```bash
# Extract bit fields with position/width information
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py {WORKSPACE}/docs/datasheet.pdf \
    -p CHIP -o {WORKSPACE}/docs/[chip]_bitfields.json --pretty
```

**What this provides**:
- Bit field names, positions (MSB/LSB), and widths
- Descriptions and decode values for each bitfield
- Register name and address associations

**Step 3: Extract register addresses**:
```bash
# Extract register address map
python {WORKSPACE}/skills/datasheet-parsing/tools/reg_parser.py {WORKSPACE}/docs/datasheet.pdf \
    -p CHIP -o {WORKSPACE}/docs/[chip]_regs.h
```

**What this provides**:
- C header with all register addresses as #defines
- ~90% accuracy on register address extraction
- Clear register name to address mapping

**Step 4: Auto-generate final C header** (AUTO-DETECTS 8-BIT vs 16-BIT):
```bash
# Automatically detects register width by analyzing actual bitfield positions:
#   - Simple 8-bit (max bit position ≤ 7)  → bitfield_parser.py with c-header format
#   - Column-per-bit (Bit 7, Bit 6, ...)   → unified_header_generator.py
#   - True 16-bit ([15:8], [7:0] in names) → merge_to_final_header.py

python {WORKSPACE}/skills/datasheet-parsing/tools/auto_generate_final_header.py \
    --complete {WORKSPACE}/docs/[chip]_complete.json \
    --regs {WORKSPACE}/docs/[chip]_regs.h \
    --bitfields {WORKSPACE}/docs/[chip]_bitfields.json \
    -p CHIP \
    -o {WORKSPACE}/docs/[chip]_FINAL.h
```

**What this provides**:
- **Smart Auto-detection**: Analyzes actual bitfield positions to determine register width
  - Checks max bit position in bitfields (≤7 = 8-bit, >7 = 16-bit)
  - Prevents false 16-bit detection when MSB/LSB are just column headers
- **Simple 8-bit format** (e.g., MAX86178): Uses bitfield_parser.py directly
  - All bitfields fit in 0-7 bit range
  - Generates clean 8-bit register header with BIT(n) and GENMASK(7,0) macros
- **Column-per-bit format** (e.g., MAX20370): Uses unified_header_generator.py
  - Parses tables with Bit 7, Bit 6, ... Bit 0 columns
  - Handles 8-bit registers with multi-bit field consolidation
- **True 16-bit format** (e.g., MAX7779): Uses merge_to_final_header.py
  - Handles genuine 16-bit registers with [15:8]/[7:0] byte splits in register names
  - Consolidates register pairs (_15_8 + _7_0)
  - Corrects bit positions for high/low bytes
  - Applies MAX/MIN heuristics (VMAX→15:8, VMIN→7:0)
- **Production-ready C header**: Register addresses + bitfield masks with correct positions

**Step 5: Create SRS summary document**:

Create a **datasheet summary document** tracking all key information for driver development:
```markdown
# [Chip] Datasheet Analysis Summary

## Device Overview
- Part number: MAX86178
- Key features: PPG, ECG, BioZ AFE for vital signs
- Applications: Wearable monitors, pulse oximeters

## Critical Specifications
- Supply voltage: AVDD, DVDD, IOVDD ranges
- Current consumption: Shutdown current, active modes
- I2C/SPI speed: Standard/Fast mode support
- Temperature range: -40°C to +85°C

## Communication Interface
- Protocol: SPI or I2C (selectable)
- 7-bit address: Configurable via SDO/ADDR pin
- Clock speeds and timing requirements

## Key Features
1. Multi-channel acquisition (PPG, ECG, BioZ)
2. High-resolution ADCs (18-bit, 20-bit)
3. Built-in signal processing and filtering
4. 256-word FIFO with timestamps

## Initialization Sequence
1. Power-up sequence
2. Configure communication interface
3. Initialize each AFE channel
4. Enable interrupts and FIFO
5. Start acquisition

## Register Count
- Total registers: 126 addresses
- Register width: 8-bit
- Total bit fields: 323

## Special Considerations
- Clinical-grade ECG compliance
- Multi-AFE synchronization support
- Calibration requirements for BioZ
- Lead-off detection capabilities

## Files Generated
- [chip]_complete.json (full datasheet, 222 pages, 724 tables)
- [chip]_bitfields.json (323 bitfields)
- [chip]_regs.h (126 register addresses)
- [chip]_FINAL.h (merged register map + bitmasks)
```

**Step 6: Validate extraction quality**:
- Review FINAL.h header against original datasheet
- Check register address accuracy
- Verify bitfield positions match datasheet tables
- Confirm register width detection (8-bit vs 16-bit) is correct
- Test header compiles without errors

### Using Extracted Information for SRS Creation

**For planner agents**, provide:

1. **Complete JSON** (`_complete.json`):
   - Read features section for capabilities
   - Extract electrical specs for requirements
   - Find timing requirements for interface design
   - Review application notes for best practices

2. **Structured registers** (`_registers.json`):
   - Define register access functions
   - Create bit field manipulation macros
   - Generate error checking code
   - Design register configuration sequences

3. **Summary document**:
   - Quick reference for key specifications
   - Initialization sequence requirements
   - Critical design constraints
   - Known issues and workarounds

## Advanced pdfplumber Usage for Custom Extraction

When automated parsers miss critical information:

**Extract specific sections by keyword**:
```python
import pdfplumber

with pdfplumber.open('{WORKSPACE}/docs/datasheet.pdf') as pdf:
    # Find all pages mentioning specific topics
    electrical_specs = []
    timing_specs = []

    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        if not text:
            continue

        # Track electrical characteristics
        if 'electrical characteristics' in text.lower():
            electrical_specs.append({
                'page': page_num + 1,
                'content': text,
                'tables': page.extract_tables()
            })

        # Track timing specifications
        if 'timing' in text.lower() or 'clock' in text.lower():
            timing_specs.append({
                'page': page_num + 1,
                'content': text,
                'tables': page.extract_tables()
            })

# Save extracted sections
import json
with open('electrical_specs.json', 'w') as f:
    json.dump(electrical_specs, f, indent=2)
```

**Extract tables with custom settings**:
```python
import pdfplumber

with pdfplumber.open('{WORKSPACE}/docs/datasheet.pdf') as pdf:
    page = pdf.pages[25]  # Page with complex table

    # Custom table extraction settings
    table = page.extract_table(table_settings={
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "min_words_vertical": 3,
        "min_words_horizontal": 3,
    })

    if table:
        # Process table data
        headers = table[0]
        rows = table[1:]

        # Convert to structured format
        specs = []
        for row in rows:
            if len(row) >= len(headers):
                spec = dict(zip(headers, row))
                specs.append(spec)
```

**Search for specific parameters**:
```python
import pdfplumber
import re

with pdfplumber.open('{WORKSPACE}/docs/datasheet.pdf') as pdf:
    # Find all voltage specifications
    voltage_specs = []

    for page in pdf.pages:
        text = page.extract_text()
        if text:
            # Match voltage patterns (e.g., "3.3V", "1.8V - 3.6V")
            matches = re.findall(r'\d+\.?\d*\s*V\s*[-–]\s*\d+\.?\d*\s*V|\d+\.?\d*\s*V', text)
            if matches:
                voltage_specs.extend(matches)

    print("Found voltage specifications:", set(voltage_specs))
```

## Available Parser Tools

## Available Parser Tools

### Core Workflow Tools (Required)

These tools form the standard 4-step extraction workflow:

| Tool | Purpose | Step | Output Format |
|------|---------|------|---------------|
| `datasheet_reader.py` | Complete PDF text extraction | 1 | JSON (all pages, all tables) |
| `bitfield_parser.py` | PDF bit field definitions | 2 | JSON / C header |
| `reg_parser.py` | PDF register addresses | 3 | C header |
| `auto_generate_final_header.py` | Auto-detect & merge | 4 | C header (FINAL.h) |

### Specialized Tools (Optional)

For specific file formats or device types:

| Tool | Best For | Accuracy | Output Format |
|------|----------|----------|---------------|
| `hardware_spec_parser.py` | XML/CSV/YAML/YDA files | 100% | JSON |
| `pmbus_parser.py` | PMBus command tables | 100% for PMBus tables | JSON |

### Internal Tools (Used by auto_generate_final_header.py)

These are called automatically - you don't invoke them directly:

| Tool | Purpose |
|------|---------|
| `merge_to_final_header.py` | Merge regs + bitfields for true 16-bit registers |
| `unified_header_generator.py` | Generate header from column-per-bit tables |

## Tool 1: hardware_spec_parser.py (Structured Files)

**Best for**: XML, CSV, YAML, YDA files - **100% accurate**

### Supported Formats

- **XML** - Register map files
- **YDA** - YAML Design Automation (XML-based register maps from design tools)
- **CSV** - Comma-separated register definitions
- **YAML** - YAML register specifications

### Usage

```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/hardware_spec_parser.py INPUT_FILE \
    --output OUTPUT.json \
    --pretty
```

### Examples

**Parse XML register map**:
```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/hardware_spec_parser.py \
    {WORKSPACE}/docs/FG_RAM.xml \
    --output {WORKSPACE}/docs/fuel_gauge.json \
    --pretty
```

**Parse YDA file** (YAML Design Automation):
```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/hardware_spec_parser.py \
    {WORKSPACE}/docs/MAX77798_Register_Map.yda \
    --output {WORKSPACE}/docs/max77798.json \
    --pretty
```

### Output Structure

```json
{
  "registers": [
    {
      "name": "STATUS",
      "address": "0x00",
      "width": 8,
      "access": "R",
      "reset_value": "0x00",
      "description": "Status register",
      "fields": [
        {
          "name": "READY",
          "bit_range": "0",
          "access": "R",
          "description": "Device ready flag"
        }
      ]
    }
  ]
}
```

### When to Use

✅ **Use hardware_spec_parser.py when**:
- You have structured files (XML, YDA, CSV, YAML)
- Design team provided register map exports
- 100% accuracy is critical
- Complete register definitions with all metadata

## Tool 2: datasheet_reader.py (Complete PDF Extraction)

**Best for**: Extracting ALL text and tables from PDF datasheets using pdfplumber

**⚠️ CRITICAL**: Always run this FIRST to extract comprehensive device information.

### Why This Tool is Essential for Planners and Users

This tool extracts **ALL information** tracked in the "Comprehensive Information Tracking Checklist" above:

✅ **Provides complete device knowledge**:
- Feature descriptions and operating modes (Checklist #1, #6)
- Electrical characteristics - voltage, current, power (Checklist #2)
- Timing requirements - clocks, delays, conversion times (Checklist #4)
- Communication interfaces - I2C/SPI details, timing (Checklist #3)
- Pin descriptions and configuration (Checklist #5)
- Initialization sequences and procedures (Checklist #8)
- Application notes and design guidelines (Checklist #10)
- Error handling and diagnostics (Checklist #9)
- Temperature ranges and environmental specs (Checklist #2)

❌ **What specialized parsers CANNOT provide**:
- Context for why registers exist
- Relationships between features and registers
- Design constraints and best practices
- Mode-specific behaviors and dependencies
- System-level integration requirements

**This tool uses pdfplumber internally** to extract all text, tables, and metadata from every page. It provides the foundation for comprehensive SRS creation and informed driver design decisions.

### Usage

```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py INPUT.pdf \
    --output OUTPUT.json \
    --pretty
```

### Example

```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py \
    {WORKSPACE}/docs/MAX20370_datasheet.pdf \
    --output {WORKSPACE}/docs/max20370_full.json \
    --pretty
```

### Output Structure

```json
{
  "metadata": {
    "filename": "MAX20370_datasheet.pdf",
    "pages": 145,
    "extraction_date": "2026-03-23"
  },
  "pages": [
    {
      "page_number": 1,
      "text": "Full text from page...",
      "tables": [
        {
          "headers": ["Parameter", "Min", "Typ", "Max", "Unit"],
          "rows": [...]
        }
      ]
    }
  ]
}
```

### When to Use

✅ **Use datasheet_reader.py when**:
- Starting any new driver project (MANDATORY FIRST STEP)
- Need complete datasheet context
- Creating SRS requirements
- Understanding device features and capabilities
- Researching electrical specifications
- Looking for initialization sequences
- Need application notes

## Tool 3: bitfield_parser.py (PDF Bit Fields)

**Best for**: Extracting bit field definitions from PDF with automatic register association

### Key Features

- **Auto register association**: Matches bit fields to register addresses (60% success rate)
- **High description accuracy**: 97% of descriptions extracted correctly
- **C header generation**: Direct output in C format
- **JSON output**: Structured data for processing

### Usage

```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py INPUT.pdf \
    --prefix CHIP_PREFIX \
    --output OUTPUT.json \
    --pretty
```

**Generate C header directly**:
```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py INPUT.pdf \
    --prefix MAX20370 \
    --output max20370_regs.h \
    --format c-header
```

### Example

```bash
# Extract to JSON
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py \
    {WORKSPACE}/docs/MAX20370_datasheet.pdf \
    --prefix MAX20370 \
    --output {WORKSPACE}/docs/max20370_bitfields.json \
    --pretty

# Generate C header
cd {WORKSPACE}/docs && python ../skills/datasheet-parsing/tools/bitfield_parser.py \
    MAX20370_datasheet.pdf \
    --prefix MAX20370 \
    --output max20370_regs.h \
    --format c-header
```

### Output Structure (JSON)

```json
{
  "bitfields": [
    {
      "name": "PMICTOP_INT",
      "position": 7,
      "width": 1,
      "bits": "7",
      "register_address": "0x22",
      "register_name": "INTSRC_STS",
      "description": "PMICTOP Interrupt",
      "decode": "0b0: No interrupt\n0b1: Interrupt detected"
    }
  ]
}
```

### Output Structure (C Header)

```c
/* Register 0x22: INTSRC_STS */
#define MAX20370_REG_INTSRC_STS_ADDR         0x22

/* INTSRC_STS bit fields */
/** PMICTOP Interrupt */
#define MAX20370_INTSRC_STS_PMICTOP_INT_MSK  NO_OS_BIT(7)
```

### When to Use

✅ **Use bitfield_parser.py when**:
- PDF datasheet has register bit field tables
- Need C header file generation
- Want automatic register address association
- Extracting 100+ bit fields
- Creating driver implementation headers

## Tool 4: reg_parser.py (PDF Register Addresses)

**Best for**: Extracting explicit register address map from PDF (~90% accuracy)

**IMPORTANT**: Always run this alongside bitfield_parser.py to get a clear register map. Many bitfields may not include register_address in the JSON, but reg_parser.py creates an explicit register address header.

### Usage

```bash
cd {WORKSPACE}/docs && python ../skills/datasheet-parsing/tools/reg_parser.py DATASHEET.pdf \
    --prefix CHIP_PREFIX \
    --output chip_regs.h
```

### Example

```bash
cd {WORKSPACE}/docs && python ../skills/datasheet-parsing/tools/reg_parser.py \
    MAX20370_datasheet.pdf \
    -p MAX20370 \
    -o max20370_regs.h
```

### Output (C Header)

```c
#define MAX20370_REG_CHIP_ID        0x00
#define MAX20370_REG_STATUS         0x01
#define MAX20370_REG_CONTROL        0x02
```

### When to Use

✅ **Use reg_parser.py when**:
- Need an explicit, complete register address map
- Want a clear C header with all register addresses
- bitfield_parser.py output lacks register_address fields for many registers
- Want ~90% accuracy on register addresses (vs 60% from bitfield_parser)
- Creating implementation headers

**RECOMMENDED**: Always run BOTH bitfield_parser.py (for bit fields) AND reg_parser.py (for register map) to get complete coverage.

## Tool 5: pmbus_parser.py (PMBus Commands)

**Best for**: Extracting PMBus command tables from DC-DC converters, PMICs

### Usage

```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/pmbus_parser.py INPUT.pdf \
    --prefix CHIP_PREFIX \
    --output OUTPUT.json \
    --pretty
```

### Example

```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/pmbus_parser.py \
    {WORKSPACE}/docs/LTC3880_datasheet.pdf \
    --prefix LTC3880 \
    --output {WORKSPACE}/docs/ltc3880_pmbus.json \
    --pretty
```

### Output Structure

```json
{
  "pmbus_commands": [
    {
      "command": "READ_VOUT",
      "code": "0x8B",
      "type": "Read Word",
      "description": "Read output voltage",
      "units": "Volts"
    }
  ]
}
```

### When to Use

✅ **Use pmbus_parser.py when**:
- Device uses PMBus protocol
- DC-DC converters, power management ICs
- Datasheet has PMBus command table
- 100% accuracy needed for critical power management

## Recommended Workflows

### Workflow 1: Standard Register-Based Device (UPDATED)

**Best for**: ADCs, DACs, sensors, AFEs with register maps

```bash
# Step 1: ALWAYS extract full datasheet first (MANDATORY)
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --output {WORKSPACE}/docs/[chip]_complete.json \
    --pretty

# Step 2: Extract bit fields with position/width information
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --prefix CHIP \
    --output {WORKSPACE}/docs/[chip]_bitfields.json \
    --pretty

# Step 3: Extract explicit register address map (RECOMMENDED)
python {WORKSPACE}/skills/datasheet-parsing/tools/reg_parser.py \
    {WORKSPACE}/docs/datasheet.pdf \
    -p CHIP \
    -o {WORKSPACE}/docs/[chip]_regs.h

# Step 4: Auto-generate final merged header (AUTO-DETECTS 8-bit vs 16-bit)
python {WORKSPACE}/skills/datasheet-parsing/tools/auto_generate_final_header.py \
    --complete {WORKSPACE}/docs/[chip]_complete.json \
    --regs {WORKSPACE}/docs/[chip]_regs.h \
    --bitfields {WORKSPACE}/docs/[chip]_bitfields.json \
    -p CHIP \
    -o {WORKSPACE}/docs/[chip]_FINAL.h

# Step 5: Create SRS summary document with all key information

# Result:
# - [chip]_complete.json: Complete context for SRS (all pages, all tables)
# - [chip]_bitfields.json: Structured bit fields for implementation
# - [chip]_regs.h: Clear register address map (~90% accuracy)
# - [chip]_FINAL.h: Production-ready merged header with correct register width
```

### Workflow 2: Structured Register Map Files

**Best for**: Devices with XML/YDA/CSV register definitions

```bash
# Step 1: Parse structured file (100% accurate)
python {WORKSPACE}/skills/datasheet-parsing/tools/hardware_spec_parser.py \
    {WORKSPACE}/docs/register_map.xml \
    --output {WORKSPACE}/docs/chip_regs.json \
    --pretty

# Optional Step 2: Also extract PDF datasheet for context
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --output {WORKSPACE}/docs/datasheet_full.json \
    --pretty
```

### Workflow 3: PMBus Devices

**Best for**: DC-DC converters, PMICs with PMBus

```bash
# Step 1: ALWAYS extract full datasheet first
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --output {WORKSPACE}/docs/datasheet_full.json \
    --pretty

# Step 2: Extract PMBus commands
python {WORKSPACE}/skills/datasheet-parsing/tools/pmbus_parser.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --prefix CHIP \
    --output {WORKSPACE}/docs/chip_pmbus.json \
    --pretty

# Step 3: Extract regular registers if device has both
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --prefix CHIP \
    --output {WORKSPACE}/docs/chip_bitfields.json \
    --pretty
```

### Workflow 4: Complex Multi-Source Device

**Best for**: Devices with multiple specification sources

```bash
# Step 1: Extract PDF datasheet
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --output {WORKSPACE}/docs/datasheet_full.json \
    --pretty

# Step 2: Parse XML register map (if available)
python {WORKSPACE}/skills/datasheet-parsing/tools/hardware_spec_parser.py \
    {WORKSPACE}/docs/register_map.xml \
    --output {WORKSPACE}/docs/chip_regs_xml.json \
    --pretty

# Step 3: Extract bit fields from PDF
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py \
    {WORKSPACE}/docs/datasheet.pdf \
    --prefix CHIP \
    --output {WORKSPACE}/docs/chip_bitfields.json \
    --pretty

# Combine outputs for complete specification
```

## Python Environment Setup

### Prerequisites

Ensure Python environment is set up:

```bash
# Check if virtual environment exists
ls .venv/

# If .venv exists, use it
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies (if needed)
pip install pdfplumber pandas openpyxl
```

### Using .venv in Scripts

**Portable approach** (works across systems):

```bash
# Determine Python command
if [ -d .venv ]; then
    PYTHON_CMD=".venv/bin/python3"
    [ ! -f "$PYTHON_CMD" ] && PYTHON_CMD=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Use discovered Python command
$PYTHON_CMD {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py datasheet.pdf ...
```

## Output Files Organization

**Recommended structure**:

```
{WORKSPACE}/docs/
├── [chip]_datasheet.pdf              # Original datasheet
├── [chip]_full.json                  # Complete text extraction
├── [chip]_bitfields.json             # Bit field definitions
├── [chip]_regs.h                     # Generated C header
├── [chip]_pmbus.json                 # PMBus commands (if applicable)
└── register_map.xml                  # Structured register map (if available)
```

## Common Issues and Solutions

### Issue 1: Module Not Found

**Error**: `ModuleNotFoundError: No module named 'pdfplumber'`

**Solution**:
```bash
# Use .venv Python
.venv/bin/python3 {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py ...

# Or install in active environment
pip install pdfplumber pandas openpyxl
```

### Issue 2: Low Register Address Match Rate

**Problem**: bitfield_parser.py only finds 30% of register addresses

**Solution**:
1. Run `reg_parser.py` separately to extract addresses
2. Manually combine outputs
3. Check if datasheet has non-standard format
4. Consider manual pdfplumber code for custom extraction

### Issue 3: Tables Not Extracted

**Problem**: Datasheet tables not showing in JSON output

**Solution**:
```python
# Use custom pdfplumber code for non-standard tables
import pdfplumber

with pdfplumber.open('{WORKSPACE}/docs/datasheet.pdf') as pdf:
    page = pdf.pages[10]  # Page with table
    tables = page.extract_tables()
    for table in tables:
        print(table)
```

### Issue 4: Missing Bit Field Descriptions

**Problem**: Bit field descriptions empty in output

**Solution**:
- Check if PDF has text descriptions (not just images)
- Try increasing page range in parser
- Use OCR if datasheet is scanned image
- Manual entry for critical fields

## Converting JSON to C Headers

### Manual Conversion Pattern

From `chip_bitfields.json`:

```json
{
  "name": "ENABLE_BIT",
  "position": 7,
  "width": 1,
  "register_address": "0x10",
  "register_name": "CONTROL"
}
```

To C header:

```c
/* Register 0x10: CONTROL */
#define CHIP_REG_CONTROL_ADDR           0x10

/* CONTROL register bit fields */
#define CHIP_CONTROL_ENABLE_MSK         NO_OS_BIT(7)
```

### Automated Conversion

Use `--format c-header` option:

```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py datasheet.pdf \
    --prefix CHIP \
    --output chip_regs.h \
    --format c-header
```

## Best Practices

### Comprehensive Information Extraction
1. **ALWAYS start with datasheet_reader.py** - Extract ALL information using pdfplumber, not just register tables
2. **Use the tracking checklist** - Verify all 10 categories of information are captured
3. **Create summary documents** - Track key specs, features, and constraints for quick reference
4. **Extract complete context** - Don't rely solely on register parsers; get electrical specs, timing, features, etc.

### Tool Selection & Workflow
5. **Use hardware_spec_parser.py for XML/YDA** - 100% accuracy for structured files
6. **Run all 4 extraction steps in order** - datasheet_reader.py → bitfield_parser.py → reg_parser.py → auto_generate_final_header.py
7. **Let auto_generate_final_header.py detect register width** - Analyzes bitfield positions to correctly identify 8-bit vs 16-bit
8. **Run specialized parsers after datasheet_reader.py** - Complete context first, then structured data

### Quality & Organization
9. **Check output quality** - Verify parser results against PDF, especially for complex tables
10. **Verify register width detection** - Confirm 8-bit vs 16-bit is correct in FINAL.h header
11. **Organize outputs by purpose** - Keep `_complete.json` for planning, `_FINAL.h` for implementation
12. **Version control parser outputs** - Track extracted data in git for reproducibility
13. **Document extraction sources** - Note which tool/version generated each file and when

### For Planner Agents & Users
14. **Provide complete extraction** - Complete JSON, bitfields JSON, and FINAL.h header
15. **Highlight critical constraints** - Voltage, timing, initialization requirements
16. **Note special requirements** - Calibration needs, external components, layout considerations
17. **Track feature dependencies** - Document mode interactions and configuration order

## Quick Reference

| Task | Command |
|------|---------|
| Extract full PDF | `python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_reader.py input.pdf -o output.json --pretty` |
| Parse XML/YDA | `python {WORKSPACE}/skills/datasheet-parsing/tools/hardware_spec_parser.py input.xml -o output.json --pretty` |
| Extract bit fields | `python {WORKSPACE}/skills/datasheet-parsing/tools/bitfield_parser.py input.pdf -p CHIP -o output.json --pretty` |
| Extract register addresses | `python {WORKSPACE}/skills/datasheet-parsing/tools/reg_parser.py input.pdf -p CHIP -o regs.h` |
| Auto-generate final header | `python {WORKSPACE}/skills/datasheet-parsing/tools/auto_generate_final_header.py --complete complete.json --regs regs.h --bitfields bitfields.json -p CHIP -o FINAL.h` |
| Extract PMBus | `python {WORKSPACE}/skills/datasheet-parsing/tools/pmbus_parser.py input.pdf -p CHIP -o output.json --pretty` |

## Further Documentation

- **Detailed setup**: `{WORKSPACE}/skills/datasheet-parsing/tools/SETUP.md`
- **Complete guide**: `{WORKSPACE}/docs/PARSER_TOOLS_GUIDE.md`
- **Tool source code**: `{WORKSPACE}/skills/datasheet-parsing/tools/*.py`

## Summary

The hardware datasheet parsing tools with pdfplumber provide:
- **Comprehensive information extraction** - ALL device information, not just register tables
- **Complete context for planners** - Features, electrical specs, timing, initialization, constraints
- **Tracking checklist** - 10 categories covering everything planner agents and users need
- **Automated extraction** from multiple source formats (PDF, XML, YDA, CSV)
- **High accuracy** (95-100% for structured formats, complete coverage from pdfplumber)
- **Multiple output formats** (JSON for analysis, C headers for implementation)
- **Standalone usage** without agent invocation
- **Flexible workflows** for different device types

**Critical Workflow for Complete Extraction**:
1. **Extract complete datasheet** with `datasheet_reader.py` using pdfplumber (MANDATORY)
   - Gets ALL information: features, specs, timing, pins, modes, application notes
   - Provides complete context for SRS creation and design decisions
   - Covers all 10 categories in tracking checklist

2. **Extract bitfield definitions** with `bitfield_parser.py`
   - Gets bit field names, positions (MSB/LSB), and widths
   - Extracts descriptions and decode values
   - Associates bitfields with register names and addresses

3. **Extract register addresses** with `reg_parser.py`
   - Gets ~90% accurate register address map
   - Creates C header with all register #defines
   - Provides clear register name to address mapping

4. **Auto-generate final header** with `auto_generate_final_header.py`
   - Intelligently detects 8-bit vs 16-bit registers by analyzing bitfield positions
   - Prevents false 16-bit detection from MSB/LSB column headers
   - Routes to correct generator:
     - Simple 8-bit (max bit ≤ 7): Uses bitfield_parser.py directly
     - Column-per-bit: Uses unified_header_generator.py
     - True 16-bit: Uses merge_to_final_header.py
   - Generates production-ready FINAL.h header

5. **Create SRS summary document**
   - Track all key information using the 10-category checklist
   - Document critical specs, features, and constraints
   - Provide complete context for driver development

6. **Verify and validate**
   - Review FINAL.h against original datasheet
   - Confirm register width detection is correct
   - Test header compiles without errors
   - Use complete context for SRS requirements
   - Use FINAL.h header for driver implementation

**Remember**: The 4-step extraction process (datasheet_reader → bitfield_parser → reg_parser → auto_generate_final_header) provides complete information: pdfplumber extracts everything planners need, specialized parsers create implementation-ready headers, and auto-detection ensures correct register width.

These tools significantly reduce manual datasheet analysis effort and ensure no critical information is missed during driver planning and development.

