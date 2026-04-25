#!/usr/bin/env python3
"""
PMBus Command Table Parser

Extracts PMBus command definitions from PDF datasheets.
Looks for tables with columns: Command Code, Command Name, Description, Type, Data Format, Factory Value

Usage:
    python pmbus_parser.py <datasheet>.pdf -p <CHIP_PREFIX> -o <output>.json [--pretty]

Example:
    python pmbus_parser.py max20830.pdf -p MAX20830 -o max20830_pmbus.json --pretty
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is not installed")
    print("Install with: pip install pdfplumber")
    sys.exit(1)


def normalize_command_code(code_str: str) -> Optional[str]:
    """
    Normalize command code to standard hex format.
    Handles: 0x01, 01h, 0x1, etc.
    """
    if not code_str:
        return None

    code_str = str(code_str).strip()

    # Match hex patterns
    match = re.search(r'(0x[0-9a-fA-F]+|[0-9a-fA-F]+h?)', code_str)
    if match:
        hex_val = match.group(1)
        if hex_val.startswith('0x'):
            # Normalize to lowercase and pad to 2 digits
            hex_part = hex_val[2:]
            if len(hex_part) == 1:
                return f"0x0{hex_part.lower()}"
            return hex_val.lower()
        elif hex_val.endswith('h'):
            # Convert "01h" to "0x01"
            hex_part = hex_val[:-1]
            if len(hex_part) == 1:
                return f"0x0{hex_part.lower()}"
            return f"0x{hex_part.lower()}"
        else:
            # Assume it's hex without prefix
            if len(hex_val) == 1:
                return f"0x0{hex_val.lower()}"
            return f"0x{hex_val.lower()}"

    return None


def clean_cell_text(text: str) -> str:
    """Clean cell text by removing newlines and extra whitespace."""
    if not text:
        return ""
    # Replace newlines with spaces
    text = str(text).replace('\n', ' ')
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_from_text_pattern(text: str, chip_prefix: str) -> List[Dict]:
    """
    Fallback: Extract PMBus commands from text using regex patterns.
    Handles cases where table extraction fails (e.g., ADM1266).

    Pattern: 0xNN COMMAND_NAME Type Bytes
    """
    commands = []

    # Pattern: 0xNN followed by command name, type, and optional bytes
    # Example: "0x00 PAGE R/W 1"
    # Example: "0xD7 SYSTEM_CONFIGURATION Block WR/W 3 to 250"
    pattern = r'(0x[0-9a-fA-F]{1,2})\s+([A-Z][A-Z0-9_]+)\s+((?:Block\s+)?[A-Z/]+(?:,\s*Block\s+[A-Z/]+)?)\s+([0-9]+(?:\s+to\s+[0-9]+)?)'

    for match in re.finditer(pattern, text):
        code = normalize_command_code(match.group(1))
        name = match.group(2).strip()
        cmd_type = match.group(3).strip()
        bytes_info = match.group(4).strip()

        if code and name and name not in ['Reserved', 'RESERVED']:
            cmd = {
                'command_code': code,
                'command_name': name,
                'type': cmd_type,
                'chip_prefix': chip_prefix
            }

            # Add bytes as description if available
            if bytes_info:
                cmd['description'] = f"{bytes_info} bytes"

            commands.append(cmd)

    return commands


def extract_pmbus_commands_from_pdf(pdf_path: str, chip_prefix: str = "CHIP") -> List[Dict]:
    """
    Extract PMBus command tables from PDF datasheet.

    Returns:
        List of command dictionaries with keys:
        - command_code
        - command_name
        - description
        - type
        - data_format
        - factory_value
        - chip_prefix
    """
    commands = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()

                if not tables:
                    continue

                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue

                    # Get header row
                    header = table[0]
                    if not header:
                        continue

                    # Normalize header (remove newlines, lowercase)
                    header_normalized = [clean_cell_text(col).lower() if col else '' for col in header]

                    # Check if this is a PMBus command table
                    # Must have: command code, command name
                    has_command_code = any('command' in h and 'code' in h for h in header_normalized)
                    has_command_name = any('command' in h and 'name' in h for h in header_normalized)

                    if not (has_command_code and has_command_name):
                        continue

                    print(f"Found PMBus command table on page {page_num + 1}")

                    # Find column indices
                    code_col = -1
                    name_col = -1
                    desc_col = -1
                    type_col = -1
                    format_col = -1
                    factory_col = -1

                    for i, h in enumerate(header_normalized):
                        if 'command' in h and 'code' in h:
                            code_col = i
                        elif 'command' in h and 'name' in h:
                            name_col = i
                        elif 'description' in h or 'desc' in h:
                            desc_col = i
                        elif 'type' in h and 'data' not in h:
                            type_col = i
                        elif 'data' in h and 'format' in h:
                            format_col = i
                        elif 'format' in h and 'data' not in h:
                            format_col = i
                        elif 'factory' in h or 'default' in h or ('initial' in h and 'value' in h):
                            factory_col = i

                    if code_col < 0 or name_col < 0:
                        print(f"  Warning: Could not find required columns")
                        continue

                    # Parse each row
                    for row_idx, row in enumerate(table[1:]):
                        if not row or len(row) == 0:
                            continue

                        # Get command code
                        code = None
                        if code_col < len(row):
                            code = normalize_command_code(row[code_col])

                        if not code:
                            continue  # Skip rows without valid command code

                        # Get command name
                        name = clean_cell_text(row[name_col]) if name_col < len(row) and row[name_col] else ""

                        if not name or name.lower() in ['reserved', 'n/a', '-']:
                            continue  # Skip reserved commands

                        # Build command entry
                        cmd = {
                            'command_code': code,
                            'command_name': name,
                            'chip_prefix': chip_prefix
                        }

                        # Optional fields
                        if desc_col >= 0 and desc_col < len(row) and row[desc_col]:
                            cmd['description'] = clean_cell_text(row[desc_col])

                        if type_col >= 0 and type_col < len(row) and row[type_col]:
                            cmd['type'] = clean_cell_text(row[type_col])

                        if format_col >= 0 and format_col < len(row) and row[format_col]:
                            data_format = clean_cell_text(row[format_col])
                            # Remove unicode artifacts
                            data_format = re.sub(r'[^\x00-\x7F]+', '', data_format).strip()
                            if data_format and data_format not in ['-', 'n/a']:
                                cmd['data_format'] = data_format

                        if factory_col >= 0 and factory_col < len(row) and row[factory_col]:
                            factory_val = clean_cell_text(row[factory_col])
                            if factory_val and factory_val not in ['�', '-', 'n/a', 'N/A']:
                                cmd['factory_value'] = factory_val

                        commands.append(cmd)

            except Exception as e:
                print(f"Warning: Error processing page {page_num + 1}: {e}")
                continue

    # Fallback: If no commands found from tables, try text extraction
    if not commands:
        print("Table extraction failed, trying text-based extraction...")
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and ('pmbus command' in text.lower() or ('code' in text.lower() and 'name' in text.lower())):
                    page_commands = extract_from_text_pattern(text, chip_prefix)
                    if page_commands:
                        print(f"Found {len(page_commands)} commands on page {page_num + 1} (text extraction)")
                        commands.extend(page_commands)

    return commands


def generate_json_output(commands: List[Dict], chip_prefix: str, output_file: Optional[str], pretty: bool = True):
    """Generate JSON output with PMBus commands."""

    output = {
        'device_name': chip_prefix,
        'format': 'pmbus',
        'total_commands': len(commands),
        'commands': commands
    }

    # Add statistics
    with_description = len([c for c in commands if c.get('description')])
    with_type = len([c for c in commands if c.get('type')])
    with_format = len([c for c in commands if c.get('data_format')])
    with_factory = len([c for c in commands if c.get('factory_value')])

    output['statistics'] = {
        'with_description': f"{with_description}/{len(commands)} ({with_description*100//len(commands) if commands else 0}%)",
        'with_type': f"{with_type}/{len(commands)} ({with_type*100//len(commands) if commands else 0}%)",
        'with_data_format': f"{with_format}/{len(commands)} ({with_format*100//len(commands) if commands else 0}%)",
        'with_factory_value': f"{with_factory}/{len(commands)} ({with_factory*100//len(commands) if commands else 0}%)"
    }

    # Write JSON
    json_str = json.dumps(output, indent=2 if pretty else None, ensure_ascii=False)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"JSON file generated: {output_file}")
    else:
        print(json_str)

    # Print summary
    print(f"\nTotal PMBus commands: {len(commands)}")
    if commands:
        print(f"  With description: {with_description} ({with_description*100//len(commands)}%)")
        print(f"  With type: {with_type} ({with_type*100//len(commands)}%)")
        print(f"  With data format: {with_format} ({with_format*100//len(commands)}%)")
        print(f"  With factory value: {with_factory} ({with_factory*100//len(commands)}%)")


def generate_c_header(commands: List[Dict], chip_prefix: str, output_file: Optional[str]):
    """Generate C header file with PMBus command defines."""

    lines = []
    lines.append(f"/* {chip_prefix} PMBus Command Codes */")
    lines.append(f"/* Auto-generated from datasheet */")
    lines.append(f"")
    lines.append(f"#ifndef {chip_prefix}_PMBUS_H")
    lines.append(f"#define {chip_prefix}_PMBUS_H")
    lines.append(f"")
    lines.append(f"/* PMBus Command Codes */")

    for cmd in sorted(commands, key=lambda x: int(x['command_code'], 16)):
        # Create define name from command name
        define_name = cmd['command_name'].upper().replace(' ', '_').replace('-', '_')
        define_name = re.sub(r'[^A-Z0-9_]', '', define_name)

        # Add comment with description if available
        if cmd.get('description'):
            desc = cmd['description']
            if len(desc) > 70:
                desc = desc[:67] + "..."
            lines.append(f"/** {desc} */")

        lines.append(f"#define {chip_prefix}_PMBUS_{define_name:40s} {cmd['command_code']}")

        # Add type and format as comment
        if cmd.get('type') or cmd.get('data_format'):
            type_info = cmd.get('type', '')
            format_info = cmd.get('data_format', '')
            comment = f"/* {type_info}"
            if format_info:
                comment += f", {format_info}"
            if cmd.get('factory_value'):
                comment += f", Default: {cmd['factory_value']}"
            comment += " */"
            lines.append(f"/* Type: {type_info}{', Format: ' + format_info if format_info else ''}{', Default: ' + cmd['factory_value'] if cmd.get('factory_value') else ''} */")

        lines.append("")

    lines.append(f"#endif /* {chip_prefix}_PMBUS_H */")

    output_str = '\n'.join(lines)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"C header file generated: {output_file}")
    else:
        print(output_str)


def main():
    parser = argparse.ArgumentParser(
        description='Extract PMBus command tables from PDF datasheets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s max20830.pdf -p MAX20830 -o max20830_pmbus.json --pretty
  %(prog)s datasheet.pdf -p CHIP -o commands.h --format c-header
        """
    )

    parser.add_argument('pdf_file', help='Input PDF datasheet file')
    parser.add_argument('-p', '--prefix', default='CHIP',
                       help='Chip prefix for defines (default: CHIP)')
    parser.add_argument('-o', '--output', help='Output file (JSON or C header)')
    parser.add_argument('--format', choices=['json', 'c-header'], default='json',
                       help='Output format: json (default) or c-header')
    parser.add_argument('--pretty', action='store_true', default=True,
                       help='Pretty-print JSON output (default: True)')
    parser.add_argument('--no-pretty', action='store_false', dest='pretty',
                       help='Compact JSON output')

    args = parser.parse_args()

    # Check if PDF file exists
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: PDF file '{args.pdf_file}' not found")
        return 1

    print(f"Reading PDF file: {args.pdf_file}")
    print(f"Looking for PMBus command tables...")
    print()

    # Extract PMBus commands
    try:
        commands = extract_pmbus_commands_from_pdf(args.pdf_file, args.prefix)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 1

    if not commands:
        print("No PMBus command tables found in the PDF.")
        print("Expected table with columns: Command Code, Command Name, Description, Type, Data Format, Factory Value")
        return 1

    print(f"Found {len(commands)} PMBus command(s)")
    print()

    # Generate output
    if args.format == 'json':
        generate_json_output(commands, args.prefix, args.output, args.pretty)
    else:  # c-header
        generate_c_header(commands, args.prefix, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
