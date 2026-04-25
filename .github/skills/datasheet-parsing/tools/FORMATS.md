# Supported Hardware Specification Formats

The hardware specification parser supports multiple file formats commonly used for documenting hardware registers and specifications.

## Supported Formats

### 1. PDF Datasheets (.pdf)

Traditional hardware datasheets in PDF format.

**Example**:
```bash
python hardware_spec_parser.py docs/chip.pdf --output chip.json --pretty
```

**Extracts**:
- Device name and manufacturer
- Feature lists
- Register tables
- Pin configuration tables
- Electrical specifications
- Communication interfaces

**Limitations**:
- Requires Java for table extraction
- Scanned PDFs without OCR won't work
- Complex diagrams are not extracted

---

### 2. XML Register Maps (.xml)

XML-based register definitions, including IP-XACT format and vendor-specific formats.

**Example XML** (IP-XACT style):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Module>
  <Properties>
    <HardwareName>FG_RAM</HardwareName>
    <Address>'h0000</Address>
  </Properties>
  <MemoryMap>
    <BitFields>
      <BitField>
        <Name>ADCStat</Name>
        <Access>R/W</Access>
        <DefaultValue>0</DefaultValue>
        <Description>FG AdcStat</Description>
      </BitField>
    </BitFields>
  </MemoryMap>
</Module>
```

**Usage**:
```bash
python hardware_spec_parser.py docs/FG_RAM.xml --output FG_RAM.json --pretty
```

**Extracts**:
- Register names
- Bit field definitions
- Access modes (R/W, R, W)
- Reset/default values
- Addresses (handles Verilog-style like 'h0000)
- Descriptions and documentation

**Supported XML Structures**:
- IP-XACT standard format
- Custom vendor formats with Register/BitField elements
- Nested MemoryMap structures

---

### 3. CSV Register Tables (.csv)

Comma-separated value files with register definitions.

**Example CSV**:
```csv
Register Name,Register Address,Bit Field Name,Bit Position,Bit Width,Access,Default Value,Documentation
Status,0x0,PONR,'d1,'d1,R/W,'b1,Power-On Reset bit
Status,0x0,Imn,'d2,'d1,R/W,'b0,Minimum Current Alert
VAlrtTh,0x3,VMIN,'d0,'d8,R/W,'b00000000,Minimum Voltage Threshold
```

**Usage**:
```bash
python hardware_spec_parser.py docs/FG_RAM.csv --output FG_RAM.json --pretty
```

**Extracts**:
- Register names and addresses
- Bit field names, positions, and widths
- Access modes
- Default/reset values (handles Verilog-style like 'b0, 'd1)
- Full documentation strings

**Flexible Column Names**:
The parser handles various column name variations:
- `Register Name`, `register_name`, `reg name` → register
- `Bit Field Name`, `field name`, `name` → name
- `Register Address`, `address`, `reg addr` → address
- `Bit Position`, `position` → position
- `Bit Width`, `width` → width
- `Default Value`, `reset`, `default_value` → reset_value

---

### 4. YAML Register Definitions (.yaml, .yml)

YAML format for structured register definitions.

**Example YAML**:
```yaml
device:
  name: MAX77779
  manufacturer: Analog Devices

registers:
  - name: STATUS
    address: 0x00
    access: R/W
    reset_value: 0x00
    description: Status register
    fields:
      - name: PONR
        position: 1
        width: 1
        description: Power-On Reset

  - name: CONFIG
    address: 0x01
    access: R/W
    reset_value: 0x80

features:
  - Dual Input Switching Mode Charger
  - Fuel Gauge
  - USB Type-C Support

interfaces:
  - SPMI
  - I2C
```

**Usage**:
```bash
python hardware_spec_parser.py docs/registers.yaml --output registers.json --pretty
```

**Extracts**:
- Device metadata
- Complete register hierarchy
- Bit field definitions
- Features and interfaces
- Electrical specifications (if present)

---

## Output Format

All formats produce the same standardized JSON output:

```json
{
  "source": "docs/FG_RAM.csv",
  "format": "csv",
  "device_name": "FG_RAM",
  "manufacturer": null,
  "registers": [
    {
      "register": "Status",
      "address": "0x0",
      "name": "PONR",
      "position": "1",
      "width": "1",
      "access": "R/W",
      "reset_value": "0b1",
      "documentation": "Power-On Reset. This bit is set to a 1..."
    }
  ],
  "pins": [],
  "electrical_specs": {},
  "features": [],
  "interfaces": [],
  "metadata": {}
}
```

---

## Auto-Detection

The parser automatically detects format from file extension:

```bash
# Auto-detects as XML
python hardware_spec_parser.py docs/FG_RAM.xml --output output.json

# Auto-detects as CSV
python hardware_spec_parser.py docs/FG_RAM.csv --output output.json

# Auto-detects as PDF
python hardware_spec_parser.py docs/max77779.pdf --output output.json

# Auto-detects as YAML
python hardware_spec_parser.py docs/registers.yaml --output output.json
```

Or explicitly specify format:

```bash
python hardware_spec_parser.py input.txt --format csv --output output.json
```

---

## Format Comparison

| Feature | PDF | XML | CSV | YAML |
|---------|-----|-----|-----|------|
| **Register Maps** | ✅ (tables) | ✅ | ✅ | ✅ |
| **Bit Fields** | ✅ (tables) | ✅ | ✅ | ✅ |
| **Descriptions** | ✅ | ✅ | ✅ | ✅ |
| **Features** | ✅ (text) | ❌ | ❌ | ✅ |
| **Pins** | ✅ (tables) | ⚠️ | ⚠️ | ✅ |
| **Interfaces** | ✅ (text) | ❌ | ❌ | ✅ |
| **Electrical Specs** | ✅ (text) | ❌ | ❌ | ✅ |
| **Ease of Parsing** | ⚠️ Complex | ✅ Easy | ✅ Easy | ✅ Easy |
| **Human Readable** | ✅ | ⚠️ | ✅ | ✅ |
| **Completeness** | ✅ Full | ⚠️ Registers only | ⚠️ Registers only | ✅ Full |

---

## Verilog-Style Values

The parser handles Verilog-style numeric literals commonly found in hardware files:

- `'h0000` → `0x0000` (hex)
- `'d10` → `10` (decimal)
- `'b1010` → `0b1010` (binary)

---

## Best Practices

### For XML Files:
- Use standard tags: `<Name>`, `<Address>`, `<Access>`, `<DefaultValue>`, `<Description>`
- Group related fields under `<Register>` or `<BitField>` elements
- Include metadata in `<Properties>` section

### For CSV Files:
- Include column headers in first row
- Use standard column names (see above)
- Document all bit fields, not just registers
- Use Verilog-style or hex notation for consistency

### For YAML Files:
- Use hierarchical structure with fields nested under registers
- Include device metadata at top level
- Document all features and interfaces
- Use consistent indentation (2 spaces)

### For PDF Files:
- Ensure PDF has searchable text (not scanned images)
- Tables should be properly formatted
- Install Java for table extraction

---

## Examples by Use Case

### Vendor Register Specification (XML)
Best for: Chip vendor provides XML register definitions

### Quick Register Table (CSV)
Best for: Exporting from spreadsheet, sharing register maps via email

### Configuration Management (YAML)
Best for: Version-controlled register configs, human-editable specs

### Official Documentation (PDF)
Best for: Complete datasheets with all specifications

---

## Next Steps

1. Choose the format that best matches your source data
2. Run the parser to extract structured data
3. Use the JSON output with planner agents for SRS creation
4. Version control the JSON output for future reference
