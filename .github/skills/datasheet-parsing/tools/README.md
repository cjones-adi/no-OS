# Agent Tools

This directory contains tools that GitHub Copilot agents can use for specialized tasks.

## Datasheet Parser Tool

The `datasheet_parser.py` tool extracts structured information from hardware datasheets (PDF format).

### Installation

Install required Python packages:

```bash
pip install -r requirements.txt
```

**Note:** `tabula-py` also requires Java Runtime Environment (JRE) to be installed on your system.

### Usage

#### Basic usage (extract everything):

```bash
python datasheet_parser.py path/to/datasheet.pdf --output output.json --pretty
```

#### Extract specific sections:

```bash
# Extract only register information
python datasheet_parser.py datasheet.pdf --section registers --output registers.json

# Extract only pin configuration
python datasheet_parser.py datasheet.pdf --section pins --output pins.json

# Extract electrical specifications
python datasheet_parser.py datasheet.pdf --section specs --output specs.json

# Extract metadata only (device name, manufacturer)
python datasheet_parser.py datasheet.pdf --section metadata
```

### Output Format

The tool outputs JSON with the following structure:

```json
{
  "source": "path/to/datasheet.pdf",
  "device_name": "MAX77779",
  "manufacturer": "Analog Devices",
  "features": [
    "Dual Input Switching Mode Charger",
    "26VAMR for Both Inputs",
    "..."
  ],
  "interfaces": ["SPI", "I2C", "USB"],
  "registers": [
    {
      "address": "0x00",
      "name": "DEVICE_ID",
      "reset_value": "0x45",
      "description": "Device identification register"
    }
  ],
  "pins": [
    {
      "pin": "1",
      "name": "CHGIN",
      "type": "Power Input",
      "description": "Charger input voltage"
    }
  ],
  "electrical_specs": {
    "supply_voltage": "Supply Voltage: 2.7V to 5.5V",
    "operating_temp": "Operating Temperature: -40°C to +85°C"
  },
  "raw_text": "Full text content of the PDF..."
}
```

### What It Extracts

1. **Metadata**
   - Device name (e.g., MAX77779, AD7124)
   - Manufacturer

2. **Features and Benefits**
   - Bullet-point list of device features
   - Key capabilities

3. **Communication Interfaces**
   - Detects SPI, I2C, UART, SPMI, USB, Parallel interfaces

4. **Register Map**
   - Register addresses
   - Register names
   - Bit fields
   - Reset/default values
   - Descriptions

5. **Pin Configuration**
   - Pin numbers
   - Pin names
   - Pin types
   - Pin descriptions

6. **Electrical Specifications**
   - Supply voltage ranges
   - Operating temperature
   - Current consumption
   - Other key specs

### Using with GitHub Copilot Agents

The planner agents can invoke this tool to parse datasheets:

```markdown
# In the agent prompt:

1. First, use the bash tool to run the datasheet parser:
   ```
   python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max77779.pdf --output /tmp/max77779_parsed.json --pretty
   ```

2. Then read the parsed JSON output:
   ```
   Read the file /tmp/max77779_parsed.json to get structured datasheet information
   ```

3. Use the extracted data to create SRS requirements
```

### Limitations

- **Table extraction**: Works best with well-formatted PDFs. Hand-drawn or scanned tables may not extract correctly.
- **Complex diagrams**: Block diagrams are not extracted as images, only text descriptions are captured.
- **Formulas**: Mathematical equations may not parse correctly.
- **Scanned PDFs**: PDFs that are just images (not searchable text) will not work without OCR.

### Troubleshooting

#### "tabula-py requires Java"

Install Java Runtime Environment:
- Windows: Download from [java.com](https://www.java.com/)
- Linux: `sudo apt-get install default-jre`
- macOS: `brew install openjdk`

#### "Could not extract register tables"

If table extraction fails, the tool will fall back to text-based parsing. You may need to:
1. Check if the PDF is searchable (not a scanned image)
2. Manually verify the register map section exists
3. Consider using a different PDF version if available

#### Large PDF files

For very large datasheets (>50MB), extraction may be slow. Use `--section` to extract only what you need.

### Advanced Usage

#### Batch processing multiple datasheets:

```bash
for pdf in docs/*.pdf; do
    python datasheet_parser.py "$pdf" --output "parsed/$(basename $pdf .pdf).json"
done
```

#### Integration with agents:

The tool can be called from agent workflows:

```python
import subprocess
import json

result = subprocess.run(
    ['python', '{WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py',
     'docs/max77779.pdf', '--section', 'registers'],
    capture_output=True,
    text=True
)

registers = json.loads(result.stdout)
```

## Future Tools

Additional tools that could be added:
- `register_generator.py` - Generate C header files from register maps
- `srs_validator.py` - Validate SRS documents against templates
- `api_analyzer.py` - Analyze driver API patterns across the codebase
