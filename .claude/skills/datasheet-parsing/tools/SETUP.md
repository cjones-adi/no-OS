# Datasheet Parser Tool - Setup Instructions

## Overview

This tool helps GitHub Copilot agents parse PDF datasheets to extract:
- Register maps and bit fields
- Pin configurations
- Communication interfaces
- Electrical specifications
- Device features

## Setup (Do This Once)

### 1. Create a Virtual Environment (Recommended)

```bash
# Navigate to the tools directory
cd {WORKSPACE}/skills/datasheet-parsing/tools

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Make sure you're in the activated virtual environment
pip install -r requirements.txt
```

### 3. Install Java (Required for Table Extraction)

The tool uses `tabula-py` which requires Java Runtime Environment (JRE):

- **Windows**: Download from https://www.java.com/
- **Ubuntu/Debian**: `sudo apt-get install default-jre`
- **macOS**: `brew install openjdk`

Verify Java is installed:
```bash
java -version
```

## Usage

### Activate Virtual Environment

Before using the tool, activate the virtual environment:

```bash
# Windows
.github\agents\tools\venv\Scripts\activate

# Linux/macOS
source {WORKSPACE}/skills/datasheet-parsing/tools/venv/bin/activate
```

### Parse a Datasheet

```bash
# Parse entire datasheet
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max77779.pdf --output docs/max77779_parsed.json --pretty

# Parse specific section (faster)
python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max77779.pdf --section registers --output docs/max77779_registers.json --pretty
```

### Deactivate When Done

```bash
deactivate
```

## How Agents Use This Tool

When you invoke the planner agent (e.g., `@driver-planner`), it will:

1. **Detect** if a PDF datasheet exists in `docs/`
2. **Ask you** to run the parser tool
3. **Wait** for you to complete the parsing
4. **Read** the generated JSON file
5. **Extract** all hardware details for the SRS

### Example Agent Workflow:

```
You: @driver-planner create SRS for MAX77779

Agent: I found docs/max77779.pdf. To help me create accurate register maps,
       please run:

       python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max77779.pdf \
           --output docs/max77779_parsed.json --pretty

You: [Run the command]

Agent: [Reads docs/max77779_parsed.json and creates comprehensive SRS]
```

## File Structure

```
{WORKSPACE}/skills/datasheet-parsing/tools/
├── datasheet_parser.py    # Main parser tool
├── requirements.txt       # Python dependencies
├── README.md             # Full documentation
├── QUICK_START.md        # Quick reference guide
├── SETUP.md              # This file
├── install.sh            # Auto-install script (Linux/macOS)
├── install.bat           # Auto-install script (Windows)
└── venv/                 # Your virtual environment (after setup)
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`, make sure:
1. Virtual environment is activated
2. Dependencies are installed: `pip install -r requirements.txt`

### Java Not Found

If you get "Java not found" errors:
1. Install Java JRE
2. Verify with `java -version`
3. Restart your terminal

### Table Extraction Fails

If register tables don't extract:
- This is OK - the tool falls back to text parsing
- Some PDFs have non-extractable tables
- The tool will still extract text-based information

## Alternative: System-Wide Installation

If you prefer not to use a virtual environment:

```bash
# Install globally (not recommended)
pip install PyPDF2 pdfplumber tabula-py pandas openpyxl
```

## Next Steps

1. Set up the virtual environment (see above)
2. Try parsing your MAX77779 datasheet:
   ```bash
   python {WORKSPACE}/skills/datasheet-parsing/tools/datasheet_parser.py docs/max77779.pdf --output docs/max77779_parsed.json --pretty
   ```
3. Use the planner agent - it will now have access to structured datasheet data!

## Questions?

- See [README.md](README.md) for full documentation
- See [QUICK_START.md](QUICK_START.md) for quick reference
- Report issues on GitHub
