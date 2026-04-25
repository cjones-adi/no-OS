#!/usr/bin/env python3
"""
Merge Register Header and Bitfield JSON to Final Header

Combines:
1. Register addresses from reg_parser.py output (C header)
2. Bitfield definitions from bitfield_parser.py output (JSON)

To create a unified FINAL.h header with register addresses and bitfield masks.

Usage:
    python merge_to_final_header.py \\
        --regs max7779_regs.h \\
        --bitfields max7779_bitfields.json \\
        --prefix MAX7779 \\
        --output max7779_FINAL.h
"""

import json
import argparse
import re
from collections import defaultdict


def camel_to_snake(name):
    """Convert CamelCase to SCREAMING_SNAKE_CASE"""
    if not name:
        return name
    # Insert underscore before uppercase letters that follow lowercase
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert underscore before uppercase letters that follow lowercase or numbers
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.upper()


def parse_register_header(header_file):
    """
    Parse register addresses from C header file.
    Handles:
    1. Registers with _15_8 suffix (16-bit registers)
    2. Registers with _7_0 suffix (8-bit or 16-bit - determined by bitfields)
    3. Registers with _H/_L pairs (split 16-bit registers)
    Returns: dict mapping normalized_reg_name -> (display_name, address, is_16bit)
    """
    registers = {}
    register_pairs = {}  # Track _H/_L pairs only

    with open(header_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Match: #define CHIP_REG_NAME   0xNN
            match = re.search(r'#define\s+(\w+)_REG_(\w+)\s+(0[xX][0-9A-Fa-f]+)', line)
            if match:
                reg_name = match.group(2)  # Just the register name part
                addr = match.group(3).lower()

                # Check if this is a _15_8 suffix (16-bit register indicator)
                if reg_name.endswith('_15_8'):
                    base_name = reg_name[:-5]
                    norm_name = base_name.lower().replace('_', '')
                    registers[norm_name] = (base_name, addr, True)

                # Check if this is a _7_0 suffix (might be 8-bit or 16-bit)
                elif reg_name.endswith('_7_0'):
                    base_name = reg_name[:-4]
                    norm_name = base_name.lower().replace('_', '')
                    # Mark as 8-bit for now, will adjust based on bitfields later
                    registers[norm_name] = (base_name, addr, False)

                # Check for _H / _L format (true split 16-bit pairs)
                elif reg_name.endswith('_H'):
                    base_name = reg_name[:-2]
                    if base_name not in register_pairs:
                        register_pairs[base_name] = {}
                    register_pairs[base_name]['high'] = addr

                elif reg_name.endswith('_L'):
                    base_name = reg_name[:-2]
                    if base_name not in register_pairs:
                        register_pairs[base_name] = {}
                    register_pairs[base_name]['low'] = addr

                # Regular register (no suffix)
                else:
                    norm_name = reg_name.lower().replace('_', '')
                    registers[norm_name] = (reg_name, addr, False)

    # Add _H/_L pairs as consolidated 16-bit registers
    for base_name, pair in register_pairs.items():
        if 'high' in pair and 'low' in pair:
            # Use low byte address for 16-bit register
            addr = pair['low']
            norm_name = base_name.lower().replace('_', '')
            registers[norm_name] = (base_name, addr, True)
        elif 'high' in pair:
            # Only _H exists
            addr = pair['high']
            norm_name = base_name.lower().replace('_', '')
            registers[norm_name] = (base_name, addr, False)
        elif 'low' in pair:
            # Only _L exists
            addr = pair['low']
            norm_name = base_name.lower().replace('_', '')
            registers[norm_name] = (base_name, addr, False)

    print(f"Parsed {len(registers)} registers from header file")
    return registers


def load_bitfield_json(bitfield_file):
    """
    Load bitfield JSON from bitfield_parser.py output.
    Returns: dict mapping normalized_reg_name -> list of bitfields

    For 16-bit registers split into high/low bytes, adjusts bit positions:
    - When consecutive bitfields have same bit position (0-7), first is high byte (+8 offset)
    - Uses address + register name to avoid collisions between different registers
    """
    with open(bitfield_file, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    # First pass: build a map of register_name -> addresses
    regname_to_addr = defaultdict(set)
    for bf in data.get('bitfields', []):
        reg_addr = bf.get('register_address', '')
        reg_name = bf.get('register_name', '')
        if reg_addr and reg_name:
            regname_to_addr[reg_name].add(reg_addr.lower())

    # Second pass: group by register name ONLY to apply MAX/MIN heuristics
    bitfields_by_regname = defaultdict(list)
    for bf in data.get('bitfields', []):
        reg_name = bf.get('register_name', '')
        if reg_name:
            bitfields_by_regname[reg_name].append(bf)

    # Apply MAX/MIN heuristics to fix bitfield_parser extraction errors
    for reg_name, bf_list in bitfields_by_regname.items():
        # Look for exactly 2 fields with MAX/MIN pattern
        if len(bf_list) == 2:
            bf0 = bf_list[0]
            bf1 = bf_list[1]

            # Check if both claim to be at bits 7:0
            bits0 = bf0.get('bits', '')
            bits1 = bf1.get('bits', '')

            if bits0 == '7:0' and bits1 == '7:0':
                name0 = bf0.get('name', '').upper()
                name1 = bf1.get('name', '').upper()

                # Apply MAX/MIN correction
                if 'MAX' in name0 and 'MIN' in name1:
                    # MAX should be 15:8, MIN should be 7:0
                    bf0['bits'] = '15:8'
                    bf0['position'] = 8
                elif 'MIN' in name0 and 'MAX' in name1:
                    # MAX should be 15:8, MIN should be 7:0
                    bf1['bits'] = '15:8'
                    bf1['position'] = 8

    # Group by address + register name to avoid mixing different registers
    bitfields_by_addr_reg = defaultdict(list)

    for bf in data.get('bitfields', []):
        reg_addr = bf.get('register_address', '').lower()
        reg_name = bf.get('register_name', '')

        # If missing address, try to infer from register name
        if not reg_addr and reg_name and reg_name in regname_to_addr:
            # Use the first address associated with this register name
            addr_set = regname_to_addr[reg_name]
            if len(addr_set) == 1:
                reg_addr = list(addr_set)[0]

        # Normalize register name for matching
        if reg_name:
            norm_name = reg_name.lower().replace('_', '').replace(' ', '')

            # Parse bit position and width
            bits_str = bf.get('bits', '')
            if ':' in bits_str:
                # Format: "7:0" or "15:8"
                parts = bits_str.split(':')
                msb = int(parts[0])
                lsb = int(parts[1])
            else:
                # Single bit
                msb = lsb = int(bits_str) if bits_str.isdigit() else bf.get('position', 0)

            field_name = bf.get('name', '')
            width = msb - lsb + 1

            bitfield = {
                'name': field_name,
                'msb': msb,
                'lsb': lsb,
                'width': width,
                'description': bf.get('description', ''),
                'register_address': reg_addr
            }

            # Key by address + normalized name to separate different registers
            key = f"{reg_addr}:{norm_name}"
            bitfields_by_addr_reg[key].append(bitfield)

    # Post-process: For each address+register group, detect high/low byte splits
    bitfields_by_reg = defaultdict(list)

    for key, bitfield_list in bitfields_by_addr_reg.items():
        addr, norm_name = key.split(':', 1)

        # Find bit positions that appear multiple times (indicating high/low byte split)
        bit_positions = defaultdict(list)
        for i, bf in enumerate(bitfield_list):
            if bf['msb'] <= 7:  # Only consider fields in 0-7 range
                bit_positions[bf['lsb']].append(i)

        # For positions with duplicates, first occurrence is high byte
        indices_to_offset = set()
        for lsb, indices in bit_positions.items():
            if len(indices) >= 2:
                # Mark first occurrence for +8 offset
                indices_to_offset.add(indices[0])

        # Apply +8 offset to high byte fields
        for idx in indices_to_offset:
            bitfield_list[idx]['msb'] += 8
            bitfield_list[idx]['lsb'] += 8

        # Additional heuristic: For MAX/MIN, HIGH/LOW, UPPER/LOWER pairs
        # If both are at bits 7:0, assign MAX/HIGH/UPPER to high byte
        if len(bitfield_list) == 2:
            field0 = bitfield_list[0]
            field1 = bitfield_list[1]

            # Check if both are 8-bit fields at same position
            if (field0['msb'] == field1['msb'] == 7 and
                field0['lsb'] == field1['lsb'] == 0):

                name0 = field0['name'].upper()
                name1 = field1['name'].upper()

                # Detect MAX/MIN pattern
                if ('MAX' in name0 and 'MIN' in name1):
                    # MAX goes to high byte
                    field0['msb'] = 15
                    field0['lsb'] = 8
                elif ('MIN' in name0 and 'MAX' in name1):
                    # MAX goes to high byte
                    field1['msb'] = 15
                    field1['lsb'] = 8
                # Detect HIGH/LOW pattern
                elif ('HIGH' in name0 and 'LOW' in name1):
                    field0['msb'] = 15
                    field0['lsb'] = 8
                elif ('LOW' in name0 and 'HIGH' in name1):
                    field1['msb'] = 15
                    field1['lsb'] = 8
                # Detect UPPER/LOWER pattern
                elif ('UPPER' in name0 and 'LOWER' in name1):
                    field0['msb'] = 15
                    field0['lsb'] = 8
                elif ('LOWER' in name0 and 'UPPER' in name1):
                    field1['msb'] = 15
                    field1['lsb'] = 8

        # Add to output dict
        bitfields_by_reg[norm_name].extend(bitfield_list)

    print(f"Loaded bitfields for {len(bitfields_by_reg)} registers from JSON (with 16-bit offset correction)")
    return bitfields_by_reg


def normalize_address(addr):
    """Normalize address to 0x00 format"""
    if not addr:
        return None
    addr = str(addr).lower().strip()
    if not addr.startswith('0x'):
        return None
    # Pad to at least 0x00 format
    if len(addr) == 3:  # 0xN
        addr = '0x0' + addr[2:]
    return addr


def match_bitfields_to_registers(registers, bitfields_by_reg):
    """
    Match bitfields to registers using multiple strategies.
    Returns: dict mapping register_name -> (address, is_16bit, list of bitfields)
    """
    matched = {}

    # Strategy 1: Match by normalized register name
    for norm_name, (reg_name, addr, is_16bit) in registers.items():
        if norm_name in bitfields_by_reg:
            matched[reg_name] = (addr, is_16bit, bitfields_by_reg[norm_name])
            continue

        # Strategy 2: Match by address
        addr_norm = normalize_address(addr)
        for bf_norm_name, bf_list in bitfields_by_reg.items():
            if bf_list and bf_list[0]['register_address'] == addr_norm:
                matched[reg_name] = (addr, is_16bit, bf_list)
                break

    print(f"Matched bitfields to {len(matched)} registers")
    print(f"Registers without bitfields: {len(registers) - len(matched)}")

    return matched


def generate_final_header(registers, matched_bitfields, chip_prefix, output_file):
    """
    Generate unified FINAL.h header with register addresses and bitfield masks.
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
    sorted_regs = sorted(registers.items(), key=lambda x: (x[1][1], x[1][0]))

    total_regs = 0
    total_bitfields = 0
    regs_with_bitfields = 0
    regs_16bit = 0

    for norm_name, (reg_name, addr, is_16bit) in sorted_regs:
        # Convert register name to SCREAMING_SNAKE_CASE
        reg_name_snake = camel_to_snake(reg_name)

        # Register definition (no indentation)
        # For 16-bit registers, add comment
        if is_16bit:
            lines.append(f"#define {chip_prefix}_REG_{reg_name_snake}    {addr.upper()}  /* 16-bit */")
            regs_16bit += 1
        else:
            lines.append(f"#define {chip_prefix}_REG_{reg_name_snake}    {addr.upper()}")
        total_regs += 1

        # Check if we have bitfields for this register
        if reg_name in matched_bitfields:
            addr_matched, is_16bit_matched, bitfields = matched_bitfields[reg_name]

            # Sort bitfields by MSB (descending)
            bitfields_sorted = sorted(bitfields, key=lambda x: x['msb'], reverse=True)

            for bf in bitfields_sorted:
                field_name = bf['name']
                msb = bf['msb']
                lsb = bf['lsb']
                width = bf['width']

                # Skip if field name is invalid
                if not field_name or len(field_name) < 2:
                    continue

                # For 16-bit registers, if the field width is 8 bits and starts at bit 0,
                # check if this is actually a full 16-bit field (common in fuel gauge ICs)
                if is_16bit and width == 8 and lsb == 0:
                    # Only expand if this is the ONLY field in the register
                    # If there are multiple fields, they're likely byte splits (high/low)
                    if len(bitfields_sorted) == 1:
                        # Single 8-bit field in 16-bit register - likely should be 16-bit
                        msb = 15
                        width = 16

                if width == 1:
                    # Single bit
                    mask_str = f"BIT({lsb})"
                    comment = ""
                else:
                    # Multi-bit field
                    mask_value = ((1 << width) - 1) << lsb
                    mask_str = f"GENMASK({msb}, {lsb})"
                    # For 16-bit values, use 4 hex digits
                    if mask_value > 0xFF:
                        comment = f"  /* 0x{mask_value:04X} */"
                    else:
                        comment = f"  /* 0x{mask_value:02X} */"

                # Convert field name to SCREAMING_SNAKE_CASE
                field_name_snake = camel_to_snake(field_name)

                # Bitmask definition (4-space indentation)
                # Format: MAX7779_REG_NAME_FIELD_NAME_MASK
                lines.append(f"    #define {chip_prefix}_{reg_name_snake}_{field_name_snake}_MASK    {mask_str}{comment}")
                total_bitfields += 1

            regs_with_bitfields += 1

        lines.append("")  # Blank line after each register

    lines.append(f"/* Total Registers: {total_regs} */")
    lines.append(f"/* 16-bit Registers: {regs_16bit} */")
    lines.append(f"/* Registers with Bitfields: {regs_with_bitfields} */")
    lines.append(f"/* Total Bit Fields: {total_bitfields} */")

    content = '\n'.join(lines)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nFinal C header written to: {output_file}")
    print(f"  Total Registers: {total_regs}")
    print(f"  16-bit Registers: {regs_16bit}")
    print(f"  Registers with Bitfields: {regs_with_bitfields}")
    print(f"  Total Bit Fields: {total_bitfields}")


def main():
    parser = argparse.ArgumentParser(
        description='Merge register header and bitfield JSON to create FINAL.h'
    )
    parser.add_argument('--regs', required=True,
                       help='Input register header file (from reg_parser.py)')
    parser.add_argument('--bitfields', required=True,
                       help='Input bitfield JSON file (from bitfield_parser.py)')
    parser.add_argument('-p', '--prefix', default='CHIP',
                       help='Chip prefix for C header')
    parser.add_argument('-o', '--output', required=True,
                       help='Output FINAL.h header file')

    args = parser.parse_args()

    print("=" * 80)
    print("MERGE TO FINAL HEADER GENERATOR")
    print("=" * 80)

    print(f"\n[1/4] Parsing register header file...")
    registers = parse_register_header(args.regs)

    print(f"[2/4] Loading bitfield JSON...")
    bitfields_by_reg = load_bitfield_json(args.bitfields)

    print(f"[3/4] Matching bitfields to registers...")
    matched_bitfields = match_bitfields_to_registers(registers, bitfields_by_reg)

    print(f"[4/4] Generating FINAL.h header...")
    generate_final_header(registers, matched_bitfields, args.prefix, args.output)

    print("\n" + "=" * 80)
    print("[SUCCESS] FINAL HEADER GENERATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
