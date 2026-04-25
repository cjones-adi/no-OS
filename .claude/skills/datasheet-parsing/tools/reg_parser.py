#!/usr/bin/env python3
"""
PDF Register Map to C Header Converter
Extracts register map information from a PDF and generates C header file with #define statements
"""

import re
import sys
import argparse
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file using pdfplumber"""
    try:
        import pdfplumber
    except ImportError:
        print("Error: pdfplumber is not installed. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
        import pdfplumber

    text = ""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract text
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

            # Extract tables (with error handling for problematic pages)
            try:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                # Skip problematic pages
                print(f"Warning: Could not extract tables from page {page_num + 1}: {e}")
                continue

    return text, tables

def parse_register_map(text, chip_prefix="LTC3220", tables=None):
    """
    Parse register map from extracted text and tables.
    Looks for:
    - Tables with Address and Name columns
    - Binary address patterns (7 6 5 4 3 2 1 0 followed by register name)
    - Hex addresses (0x00, 0x01, etc.)
    """
    registers = []

    # First, try to parse tables if available
    if tables:
        for table in tables:
            if not table or len(table) < 2:
                continue

            # Get header row
            header = table[0]
            if not header:
                continue

            # Find Address and Name columns
            addr_col = -1
            name_col = -1

            for i, col in enumerate(header):
                if col:
                    col_lower = str(col).lower().strip()
                    if 'address' in col_lower or 'addr' in col_lower:
                        addr_col = i
                    elif 'name' in col_lower or 'register' in col_lower or 'mnemonic' in col_lower:
                        name_col = i

            # If we found both columns, parse the table
            if addr_col >= 0 and name_col >= 0:
                for row in table[1:]:  # Skip header
                    if not row or len(row) <= max(addr_col, name_col):
                        continue

                    addr_val = row[addr_col]
                    name_val = row[name_col]

                    if not addr_val or not name_val:
                        continue

                    addr_val = str(addr_val).strip()
                    name_val = str(name_val).strip()

                    # Parse address - could be hex (0x00, 0h, 00h) or decimal
                    addr = None
                    if re.match(r'0[xX][0-9A-Fa-f]+', addr_val):
                        # Already in hex format like 0x00
                        addr = addr_val.upper()
                    elif re.match(r'[0-9A-Fa-f]+[hH]', addr_val):
                        # Format like 00h
                        hex_part = addr_val.rstrip('hH')
                        addr = f"0x{hex_part.upper()}"
                    elif re.match(r'^[0-9]+$', addr_val):
                        # Decimal number
                        addr = f"0x{int(addr_val):02X}"
                    elif re.match(r'^[0-9A-Fa-f]{1,2}$', addr_val):
                        # Hex without prefix
                        addr = f"0x{addr_val.upper().zfill(2)}"

                    if addr and name_val and len(name_val) > 0:
                        # Clean up the register name
                        # Remove common prefixes
                        reg_name = re.sub(r'^(REGISTER|REG|R_)\s*', '', name_val, flags=re.IGNORECASE)

                        # Remove any line breaks or extra spaces that might have been introduced
                        reg_name = re.sub(r'\s+', '', reg_name)

                        # Convert PascalCase/camelCase to snake_case
                        # Insert underscore before uppercase letters that follow lowercase letters or digits
                        reg_name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', reg_name)
                        # Insert underscore before uppercase letters followed by lowercase (handles acronyms like "ABCDef" -> "ABC_Def")
                        reg_name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', reg_name)

                        # Convert to uppercase
                        reg_name = reg_name.upper()

                        # Keep only alphanumeric and underscores, remove special chars
                        reg_name = re.sub(r'[^\w]', '_', reg_name)
                        # Replace multiple underscores with single underscore
                        reg_name = re.sub(r'_+', '_', reg_name)
                        # Remove leading/trailing underscores
                        reg_name = reg_name.strip('_')

                        if reg_name and len(reg_name) > 0:
                            registers.append((reg_name, addr))

    # Fallback: Parse from text if no tables found or tables didn't work
    if not registers:
        lines = text.split('\n')

        # Pattern 1: Binary format (common in datasheets)
        # Example: "0 0 0 0 0 0 0 0 REG0 COMMAND"
        binary_pattern = r'^([01])\s+([01])\s+([01])\s+([01])\s+([01])\s+([01])\s+([01])\s+([01])\s+(REG\d+)?\s*(.+?)$'

        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                continue

            # Try binary pattern first
            binary_match = re.match(binary_pattern, line.strip())
            if binary_match:
                # Extract binary bits
                bits = ''.join(binary_match.groups()[0:8])
                # Convert binary to hex
                addr = f"0x{int(bits, 2):02X}"

                # Extract register name (everything after the binary bits)
                remainder = binary_match.group(10).strip() if binary_match.group(10) else ""
                reg_num = binary_match.group(9) if binary_match.group(9) else ""

                # Combine register number and name
                if remainder:
                    # Remove common prefixes
                    reg_name = re.sub(r'^(Register|Reg|REG)\s+', '', remainder, flags=re.IGNORECASE)
                    # Clean up the register name
                    reg_name = re.sub(r'[^\w\s/-]', '', reg_name)
                    reg_name = re.sub(r'[\s-]+', '_', reg_name)
                    reg_name = reg_name.upper().strip('_')

                    if reg_name and len(reg_name) > 0:
                        registers.append((reg_name, addr))
                continue

            # Pattern 2: Hex addresses (0x00 - 0xFF)
            hex_pattern = r'(0[xX][0-9A-Fa-f]{2})'
            hex_matches = re.finditer(hex_pattern, line)

            for hex_match in hex_matches:
                addr = hex_match.group(1)

                # Try to extract register name from the same line
                before = line[:hex_match.start()].strip()
                after = line[hex_match.end():].strip()

                # Clean up common separators
                before = re.sub(r'[:\|\t]+$', '', before).strip()
                after = re.sub(r'^[:\|\t]+', '', after).strip()

                reg_name = None

                # Prefer text before the address if it looks like a register name
                if before and len(before) > 2 and not re.match(r'^\d+$', before):
                    reg_name = re.sub(r'^(Register|Reg|REG)\s+', '', before, flags=re.IGNORECASE)
                elif after and len(after) > 2 and not re.match(r'^\d+$', after):
                    reg_name = re.sub(r'^(Register|Reg|REG)\s+', '', after, flags=re.IGNORECASE)

                if reg_name:
                    # Clean up the register name
                    reg_name = re.sub(r'[^\w\s-]', '', reg_name)
                    reg_name = re.sub(r'[\s-]+', '_', reg_name)
                    reg_name = reg_name.upper().strip('_')

                    if reg_name and len(reg_name) > 1:
                        registers.append((reg_name, addr.upper()))

    # Remove duplicates while preserving order
    seen = set()
    unique_registers = []
    for name, addr in registers:
        key = (name, addr)
        if key not in seen:
            seen.add(key)
            unique_registers.append((name, addr))

    return unique_registers

def generate_c_header(registers, chip_prefix="LTC3220", output_file=None):
    """Generate C header file with #define statements"""

    if not registers:
        print("Warning: No registers found in the PDF")
        return

    header_guard = f"{chip_prefix}_H"

    header_content = f"""/*
 * {chip_prefix} Register Map
 * Auto-generated from PDF datasheet
 * Generated on: {Path(__file__).name}
 */

#ifndef {header_guard}
#define {header_guard}

/* Register Addresses */
"""

    # Add register defines
    for reg_name, addr in registers:
        # Ensure the register name has the chip prefix
        if not reg_name.startswith(chip_prefix):
            define_name = f"{chip_prefix}_REG_{reg_name}"
        else:
            define_name = f"{reg_name}"

        # Use single tab for spacing
        header_content += f"#define {define_name}\t{addr}\n"

    header_content += f"\n#endif /* {header_guard} */\n"

    # Write to file or print
    if output_file:
        with open(output_file, 'w') as f:
            f.write(header_content)
        print(f"C header file generated: {output_file}")
    else:
        print(header_content)

    return header_content

def main():
    parser = argparse.ArgumentParser(
        description='Convert PDF register map to C header file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 32201fd.pdf
  %(prog)s 32201fd.pdf -o ltc3220.h
  %(prog)s 32201fd.pdf -p LTC3220 -o ltc3220_regs.h
        """
    )

    parser.add_argument('pdf_file', help='Input PDF file containing register map')
    parser.add_argument('-o', '--output', help='Output C header file (default: print to stdout)')
    parser.add_argument('-p', '--prefix', default='LTC3220',
                       help='Chip/register prefix for defines (default: LTC3220)')

    args = parser.parse_args()

    # Check if PDF file exists
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: PDF file '{args.pdf_file}' not found")
        return 1

    print(f"Reading PDF file: {args.pdf_file}")

    # Extract text from PDF
    try:
        text, tables = extract_text_from_pdf(args.pdf_file)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 1

    print(f"Parsing register map...")

    # Parse register map
    registers = parse_register_map(text, args.prefix, tables)

    if not registers:
        print("No registers found. The PDF might have a different format.")
        print("First 500 characters of extracted text:")
        print(text[:500])
        return 1

    print(f"Found {len(registers)} register(s)")

    # Generate C header
    generate_c_header(registers, args.prefix, args.output)

    return 0

if __name__ == "__main__":
    sys.exit(main())
