#!/usr/bin/env python3
"""
Unified Header Generator

Combines register addresses from tables with bitfield extraction to generate
a complete C header file with:
- Correct register addresses and names
- Bitfield masks for each register

Usage:
    python unified_header_generator.py \\
        --complete max20370_complete.json \\
        --prefix MAX20370 \\
        --output max20370_unified.h
"""

import json
import argparse
import re


def camel_to_snake(name):
    """Convert CamelCase to SCREAMING_SNAKE_CASE"""
    if not name:
        return name
    # Insert underscore before uppercase letters that follow lowercase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert underscore before uppercase letters that follow lowercase or numbers
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.upper()


def normalize_register_name(name):
    """Normalize register name for matching (remove spaces, convert to lowercase)"""
    if not name:
        return None
    # Remove all whitespace and newlines
    name = re.sub(r'\s+', '', str(name))
    return name.lower()


def normalize_address(addr_str):
    """Normalize address to 0x00 format"""
    if not addr_str:
        return None

    addr = str(addr_str).strip()
    # Remove newlines
    addr = re.sub(r'\s+', '', addr)

    if not addr.startswith('0x'):
        return None

    # Normalize to lowercase and pad
    addr = addr.lower()
    if len(addr) == 3:  # 0xN
        addr = '0x0' + addr[2:]

    return addr


def clean_field_name(name):
    """Clean field name - remove newlines and whitespace"""
    if not name:
        return None

    name = str(name).strip()
    # Remove all newlines and extra whitespace
    name = re.sub(r'\s+', '', name)

    # Skip reserved fields
    if re.match(r'^(reserved|rfu|rsvd|n/a)$', name, re.IGNORECASE):
        return None

    if len(name) < 2:
        return None

    return name


def extract_register_addresses(complete_json_file):
    """
    Extract register addresses and names from tables.
    Returns: dict mapping normalized_name -> (display_name, address)
    """
    with open(complete_json_file, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    tables = data.get('tables', [])
    print(f"Found {len(tables)} tables in complete JSON")

    registers = {}  # normalized_name -> (display_name, address)

    for table_idx, table_info in enumerate(tables):
        table_data = table_info.get('data', [])

        if not table_data or len(table_data) < 2:
            continue

        header = table_data[0]
        if not header:
            continue

        # Check if this table has Address and Name columns
        addr_col = -1
        name_col = -1

        for i, col in enumerate(header):
            if not col:
                continue
            col_str = str(col).lower().strip()
            col_clean = re.sub(r'\s+', '', col_str)

            if 'address' in col_clean or 'addr' in col_clean:
                addr_col = i
            elif col_clean == 'name' or 'register' in col_clean or 'mnemonic' in col_clean:
                name_col = i

        if addr_col < 0 or name_col < 0:
            continue

        print(f"Found register address table (addr_col={addr_col}, name_col={name_col})")

        # Parse each row
        for row in table_data[1:]:
            if not row or len(row) <= max(addr_col, name_col):
                continue

            addr_val = row[addr_col] if addr_col < len(row) else None
            name_val = row[name_col] if name_col < len(row) else None

            if not addr_val or not name_val:
                continue

            addr = normalize_address(addr_val)
            if not addr:
                continue

            # Get display name (cleaned but preserving case)
            display_name = str(name_val).strip()
            display_name = re.sub(r'\s+', '', display_name)

            # Get normalized name for matching
            norm_name = normalize_register_name(display_name)

            if norm_name and display_name:
                registers[norm_name] = (display_name, addr)

    print(f"Extracted {len(registers)} unique register addresses\n")
    return registers


def extract_bitfields_from_tables(complete_json_file):
    """
    Extract bitfields from explicit bits format tables.
    Returns: dict mapping normalized_reg_name -> list of bitfields
    """
    with open(complete_json_file, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    tables = data.get('tables', [])
    bitfields_by_register = {}  # normalized_reg_name -> list of bitfields

    for table_idx, table_info in enumerate(tables):
        table_data = table_info.get('data', [])

        if not table_data or len(table_data) < 2:
            continue

        header = table_data[0]
        if not header:
            continue

        # Check if this is an explicit bits format table
        header_no_space = [re.sub(r'\s+', '', str(col).lower()) if col else '' for col in header]
        header_with_space = [re.sub(r'\s+', ' ', str(col).lower()) if col else '' for col in header]

        header_str_no_space = ' '.join(header_no_space)
        header_str_with_space = ' '.join(header_with_space)

        has_reg_col = 'reg' in header_str_no_space
        has_bit_cols = 'bit7' in header_str_no_space or 'bit6' in header_str_no_space or 'bit 7' in header_str_with_space or 'bit 6' in header_str_with_space

        if not (has_reg_col and has_bit_cols):
            continue

        # Find column indices
        reg_col = -1
        name_col = -1
        bit_cols = {}  # bit number -> column index

        for i, col in enumerate(header):
            if not col:
                continue
            col_str = str(col).lower()
            col_clean = re.sub(r'\s+', '', col_str)

            if 'reg' in col_clean:
                reg_col = i
            elif col_clean == 'name':
                name_col = i
            elif 'bit' in col_clean:
                col_normalized = re.sub(r'\s+', ' ', col_str)
                match = re.search(r'bit\s*(\d+)', col_normalized)
                if match:
                    bit_num = int(match.group(1))
                    bit_cols[bit_num] = i

        if reg_col < 0 or name_col < 0 or len(bit_cols) < 4:
            continue

        print(f"Found explicit bits table (reg_col={reg_col}, name_col={name_col}, bits={len(bit_cols)})")

        # Parse each row
        for row in table_data[1:]:
            if not row or len(row) < max(reg_col, name_col):
                continue

            # Get register name
            reg_name = row[name_col] if name_col < len(row) else None
            if not reg_name:
                continue

            reg_name = str(reg_name).strip()
            reg_name = re.sub(r'\s+', '', reg_name)

            # Normalize register name for lookup
            norm_reg_name = normalize_register_name(reg_name)

            # Initialize list if not exists
            if norm_reg_name not in bitfields_by_register:
                bitfields_by_register[norm_reg_name] = []

            # Extract bit fields from this row
            processed_bits = set()

            for bit_num in sorted(bit_cols.keys(), reverse=True):  # Start from Bit 7
                if bit_num in processed_bits:
                    continue

                col_idx = bit_cols[bit_num]
                if col_idx >= len(row):
                    continue

                field_name = row[col_idx]
                field_name = clean_field_name(field_name)

                if not field_name:
                    continue

                # This bit has a field name, so it's the MSB of the field
                msb = bit_num
                lsb = bit_num

                # Look FORWARD (to lower bits) to find nulls that belong to this field
                for lower_bit in range(bit_num - 1, -1, -1):
                    if lower_bit not in bit_cols:
                        break

                    lower_col = bit_cols[lower_bit]
                    if lower_col >= len(row):
                        break

                    lower_name = clean_field_name(row[lower_col])

                    if lower_name is None:
                        # Null bit - belongs to current field
                        lsb = lower_bit
                        processed_bits.add(lower_bit)
                    else:
                        # Found another field name - stop here
                        break

                # Mark MSB as processed
                processed_bits.add(bit_num)

                # Add bitfield
                bitfield = {
                    'name': field_name,
                    'msb': msb,
                    'lsb': lsb,
                    'width': msb - lsb + 1
                }

                bitfields_by_register[norm_reg_name].append(bitfield)

    print(f"Extracted bitfields for {len(bitfields_by_register)} registers\n")
    return bitfields_by_register


def generate_unified_header(registers, bitfields_by_register, chip_prefix, output_file):
    """
    Generate unified C header with register addresses and bitfields.
    """
    lines = []

    lines.append(f"/* {chip_prefix} Register Map */")
    lines.append(f"/* Auto-generated from datasheet tables */")
    lines.append("")
    lines.append("#ifndef BIT")
    lines.append("#define BIT(n) (1U << (n))")
    lines.append("#endif")
    lines.append("#ifndef GENMASK")
    lines.append("#define GENMASK(h, l) (((~0UL) - (1UL << (l)) + 1) & (~0UL >> (31 - (h))))")
    lines.append("#endif")
    lines.append("")

    # Sort registers by address, then by name
    sorted_items = sorted(registers.items(), key=lambda x: (x[1][1], x[1][0]))

    total_regs = 0
    total_bitfields = 0
    regs_with_bitfields = 0

    for norm_name, (display_name, addr) in sorted_items:
        # Convert register name to SCREAMING_SNAKE_CASE
        reg_name_snake = camel_to_snake(display_name)

        # Register definition: MAX20370_REG_CHG_CTRL0
        lines.append(f"#define {chip_prefix}_REG_{reg_name_snake}    {addr.upper()}")
        total_regs += 1

        # Check if we have bitfields for this register
        if norm_name in bitfields_by_register:
            bitfields = bitfields_by_register[norm_name]

            # Sort bitfields by MSB
            bitfields_sorted = sorted(bitfields, key=lambda x: x['msb'], reverse=True)

            for bf in bitfields_sorted:
                field_name = bf['name']
                field_name_snake = camel_to_snake(field_name)
                msb = bf['msb']
                lsb = bf['lsb']
                width = bf['width']

                if width == 1:
                    # Single bit
                    mask_str = f"BIT({lsb})"
                    comment = ""
                else:
                    # Multi-bit field
                    mask_value = ((1 << width) - 1) << lsb
                    mask_str = f"GENMASK({msb}, {lsb})"
                    comment = f"  /* 0x{mask_value:02X} */"

                # Bitmask definition: MAX20370_CHG_CTRL0_CHG_I_CHG_DONE_MASK
                lines.append(f"    #define {chip_prefix}_{reg_name_snake}_{field_name_snake}_MASK    {mask_str}{comment}")
                total_bitfields += 1

            regs_with_bitfields += 1

        lines.append("")  # Blank line

    lines.append(f"/* Total Registers: {total_regs} */")
    lines.append(f"/* Registers with Bitfields: {regs_with_bitfields} */")
    lines.append(f"/* Total Bit Fields: {total_bitfields} */")

    content = '\n'.join(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nUnified C header written to: {output_file}")
    print(f"  Total Registers: {total_regs}")
    print(f"  Registers with Bitfields: {regs_with_bitfields}")
    print(f"  Total Bit Fields: {total_bitfields}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate unified header with register addresses and bitfields'
    )
    parser.add_argument('--complete', required=True,
                       help='Input complete JSON file (from datasheet_reader.py)')
    parser.add_argument('-p', '--prefix', default='CHIP',
                       help='Chip prefix for C header')
    parser.add_argument('-o', '--output', required=True,
                       help='Output C header file')

    args = parser.parse_args()

    print("=" * 80)
    print("UNIFIED HEADER GENERATOR")
    print("=" * 80)

    print(f"\n[1/3] Extracting register addresses...")
    registers = extract_register_addresses(args.complete)

    print(f"[2/3] Extracting bitfields from tables...")
    bitfields_by_register = extract_bitfields_from_tables(args.complete)

    print(f"[3/3] Generating unified C header...")
    generate_unified_header(registers, bitfields_by_register, args.prefix, args.output)

    print("\n" + "=" * 80)
    print("[SUCCESS] UNIFIED HEADER GENERATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
