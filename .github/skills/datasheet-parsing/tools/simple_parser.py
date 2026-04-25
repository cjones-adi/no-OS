#!/usr/bin/env python3
"""
Simple PDF Register Parser using pdfplumber
Extracts register maps without complex dependencies.
"""

import re
import sys
import argparse
from pathlib import Path

def extract_registers(pdf_path, chip_prefix="CHIP", page_range=None, verbose=False):
    """Extract registers from PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        print("Error: pdfplumber not installed. Run: pip install pdfplumber")
        return []

    registers = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        # Determine page range
        if page_range:
            start, end = page_range
            pages = pdf.pages[start-1:end]
        else:
            pages = pdf.pages

        print(f"Scanning {len(pages)} pages...")

        for page_num, page in enumerate(pages, start=1):
            if verbose:
                print(f"Page {page_num}...")

            # Extract tables
            tables = page.extract_tables()

            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue

                # Get header
                header = table[0]

                # Find address and name columns
                addr_col = -1
                name_col = -1

                for i, col in enumerate(header):
                    if not col:
                        continue
                    col_lower = str(col).lower()

                    if 'addr' in col_lower or 'offset' in col_lower:
                        addr_col = i
                    elif 'name' in col_lower or 'register' in col_lower or 'mnemonic' in col_lower:
                        name_col = i

                # If no header found, try to infer from data
                if addr_col < 0 and len(table) > 1:
                    # Look for hex addresses in first few rows
                    for row in table[:3]:
                        for i, cell in enumerate(row):
                            if cell and re.search(r'0[xX][0-9A-Fa-f]+', str(cell)):
                                addr_col = i
                                break
                        if addr_col >= 0:
                            break

                if addr_col < 0:
                    continue

                # If still no name column, use the column after address
                if name_col < 0 and addr_col < len(header) - 1:
                    name_col = addr_col + 1

                if verbose:
                    print(f"  Table {table_idx+1}: addr_col={addr_col}, name_col={name_col}")

                # Parse rows
                # Count how many valid register rows this table has
                valid_count = 0
                temp_regs = []

                for row in table[1:]:  # Skip header
                    if not row or len(row) <= max(addr_col, name_col):
                        continue

                    addr_cell = row[addr_col] if addr_col < len(row) else None
                    name_cell = row[name_col] if name_col < len(row) else None

                    if not addr_cell or not name_cell:
                        continue

                    # Clean address
                    addr_str = str(addr_cell).strip()
                    addr_str = re.sub(r'\s+', '', addr_str)
                    addr_str = re.sub(r'[hH]$', '', addr_str)

                    # Parse address
                    addr = None
                    if re.match(r'^0[xX][0-9A-Fa-f]+$', addr_str):
                        addr = '0x' + addr_str[2:].upper()
                    elif re.match(r'^[0-9A-Fa-f]{1,4}$', addr_str):
                        # Check if it looks like a hex register address (reasonable range)
                        val = int(addr_str, 16)
                        if val < 0x1000:  # Typical register map range
                            addr = f"0x{addr_str.upper()}"
                    elif re.match(r'^[0-9]+$', addr_str):
                        val = int(addr_str)
                        if val < 256:  # Small decimal values might be register addresses
                            addr = f"0x{val:02X}"

                    if not addr:
                        continue

                    # Clean name
                    name_str = str(name_cell).strip()
                    name_str = re.sub(r'\s+', ' ', name_str)

                    # Skip reserved/empty
                    if not name_str or name_str.lower() in ['reserved', 'rfu', '-', '—', 'n/a']:
                        continue

                    # Convert to C identifier
                    reg_name = name_str.upper()
                    reg_name = re.sub(r'^(REGISTER|REG|R_)\s*', '', reg_name)

                    # Replace common Unicode characters
                    reg_name = reg_name.replace('Ω', 'OHM')
                    reg_name = reg_name.replace('μ', 'U')
                    reg_name = reg_name.replace('°', 'DEG')

                    # Convert to ASCII (replace non-ASCII with underscore)
                    reg_name = reg_name.encode('ascii', 'replace').decode('ascii').replace('?', '_')

                    reg_name = re.sub(r'[\s\-/]+', '_', reg_name)
                    reg_name = re.sub(r'[^\w]', '_', reg_name)
                    reg_name = re.sub(r'_+', '_', reg_name)
                    reg_name = reg_name.strip('_')

                    # Filter out obviously wrong register names
                    # Heuristic: real register names are typically 3-50 chars
                    if reg_name and 3 <= len(reg_name) <= 50:
                        temp_regs.append((reg_name, addr))
                        valid_count += 1

                # Only add registers if this table looks like a real register map
                # (has at least 3 valid register entries)
                if valid_count >= 3:
                    for reg_name, addr in temp_regs:
                        registers.append((reg_name, addr))
                        if verbose:
                            # Handle Unicode characters in output
                            try:
                                print(f"    {addr} -> {reg_name}")
                            except UnicodeEncodeError:
                                print(f"    {addr} -> {reg_name.encode('ascii', 'replace').decode('ascii')}")

    # Remove duplicates
    seen = set()
    unique = []
    for name, addr in registers:
        if (name, addr) not in seen:
            seen.add((name, addr))
            unique.append((name, addr))

    return unique

def generate_header(registers, chip_prefix, output_file=None):
    """Generate C header file."""
    if not registers:
        print("No registers found!")
        return

    guard = f"{chip_prefix.upper()}_REGS_H"

    content = f"""/*
 * {chip_prefix.upper()} Register Definitions
 * Auto-generated from PDF datasheet
 */

#ifndef {guard}
#define {guard}

/* Register Addresses */
"""

    for name, addr in registers:
        if not name.startswith(chip_prefix.upper()):
            define = f"{chip_prefix.upper()}_REG_{name}"
        else:
            define = name

        content += f"#define {define:<50} {addr}\n"

    content += f"\n#endif /* {guard} */\n"

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated: {output_file} ({len(registers)} registers)")
    else:
        # Handle console output encoding
        try:
            print(content)
        except UnicodeEncodeError:
            print(content.encode('ascii', 'replace').decode('ascii'))

def main():
    parser = argparse.ArgumentParser(description='Simple PDF register parser')
    parser.add_argument('pdf', help='PDF file path')
    parser.add_argument('-p', '--prefix', default='CHIP', help='Register prefix')
    parser.add_argument('-o', '--output', help='Output header file')
    parser.add_argument('--pages', help='Page range (e.g. 10-20)')
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    # Parse page range
    page_range = None
    if args.pages:
        m = re.match(r'(\d+)-(\d+)', args.pages)
        if m:
            page_range = (int(m.group(1)), int(m.group(2)))

    # Extract registers
    print(f"Parsing: {args.pdf}")
    registers = extract_registers(args.pdf, args.prefix, page_range, args.verbose)

    if not registers:
        print("No registers found.")
        return 1

    print(f"Found {len(registers)} registers")

    # Generate header
    generate_header(registers, args.prefix, args.output)

    return 0

if __name__ == '__main__':
    sys.exit(main())
