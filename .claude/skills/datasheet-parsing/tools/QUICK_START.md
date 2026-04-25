# Quick Start Guide: Datasheet Parser

This guide will help you quickly set up and use the datasheet parser tool.

## 1. Installation (One-Time Setup)

### Windows:
```bash
cd {WORKSPACE}/skills/datasheet-parsing/tools
install.bat
```

### Linux/macOS:
```bash
cd {WORKSPACE}/skills/datasheet-parsing/tools
chmod +x install.sh
./install.sh
```

### Manual Installation:
```bash
pip install PyPDF2 pdfplumber tabula-py pandas openpyxl
```

**Important**: You also need Java Runtime Environment (JRE) installed for table extraction.

## 2. Basic Usage

### Parse a complete datasheet:
```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max7779.pdf --output docs/max7779_parsed.json --pretty
```

### Parse only registers (faster):
```bash
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max7779.pdf --section registers --output docs/max7779_registers.json --pretty
```

## 3. What You Get

The tool creates a JSON file with:

```json
{
  "device_name": "MAX77779",
  "manufacturer": "Analog Devices",
  "features": [
    "Dual Input Switching Mode Charger",
    "26VAMR for Both Inputs",
    "..."
  ],
  "interfaces": ["SPMI", "I2C", "USB"],
  "registers": [
    {
      "address": "0x00",
      "name": "CONFIG",
      "description": "Configuration register"
    }
  ],
  "pins": [...],
  "electrical_specs": {...}
}
```

## 4. Using with GitHub Copilot Agents

When the planner agent asks you to run the parser:

1. Copy the command it provides
2. Run it in your terminal
3. Let the agent know it's complete
4. The agent will read the parsed JSON and use it to create the SRS

## 5. Troubleshooting

### "ModuleNotFoundError: No module named 'PyPDF2'"
Run: `pip install -r {WORKSPACE}/skills/datasheet-parsing/tools/requirements.txt`

### "tabula-py requires Java"
Install Java:
- Windows: https://www.java.com/
- Ubuntu: `sudo apt-get install default-jre`
- macOS: `brew install openjdk`

### "Could not extract register tables"
This is OK - the tool will fall back to text parsing. Some PDFs don't have extractable tables.

### "Command not found: python"
Try `python3` instead of `python`

## 6. Example Workflow

```bash
# 1. Parse the datasheet
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max77779.pdf --output docs/max77779_parsed.json --pretty

# 2. Check the output
cat docs/max77779_parsed.json | head -50

# 3. Now invoke the planner agent with the parsed data available
@driver-planner create SRS for MAX77779, use docs/max77779_parsed.json for hardware details
```

## 7. Advanced Options

### Extract specific sections:
```bash
# Metadata only (fast)
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/chip.pdf --section metadata

# Registers only
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/chip.pdf --section registers -o registers.json

# Pins only
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/chip.pdf --section pins -o pins.json

# Electrical specs only
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/chip.pdf --section specs -o specs.json
```

### Batch process multiple datasheets:
```bash
for pdf in docs/*.pdf; do
    basename=$(basename "$pdf" .pdf)
    python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py "$pdf" --output "docs/${basename}_parsed.json"
done
```

## 8. What Gets Extracted

✅ Device name (e.g., MAX77779, AD7124)
✅ Manufacturer name
✅ Feature list from datasheet
✅ Communication interfaces (SPI, I2C, UART, etc.)
✅ Register map tables (addresses, names, bit fields)
✅ Pin configuration tables
✅ Electrical specifications
✅ Full text content

❌ Block diagram images (text descriptions only)
❌ Timing diagram images
❌ Complex mathematical formulas
❌ Scanned/image-only PDFs (requires OCR)

## Need Help?

- See full documentation: [README.md](README.md)
- Check tool issues on GitHub
- Ask questions in the project chat
