#!/usr/bin/env python3
"""
Auto Final Header Generator

Automatically detects datasheet format and uses the appropriate tool:
- unified_header_generator.py for column-per-bit format (e.g., MAX20370)
- merge_to_final_header.py for byte-split 16-bit format (e.g., MAX7779)

Usage:
    python auto_generate_final_header.py \\
        --complete max20370_complete.json \\
        --regs max20370_regs.h \\
        --bitfields max20370_bitfields.json \\
        --prefix MAX20370 \\
        --output max20370_FINAL.h
"""

import json
import argparse
import subprocess
import sys
import os
import re


def detect_table_format(complete_json_file, regs_header_file=None):
    """
    Detect datasheet table format by analyzing tables and register header.

    Returns:
        'column_per_bit': Tables have Bit 7, Bit 6, ... Bit 0 columns (e.g., MAX20370)
        'byte_split': Tables have [15:8] and [7:0] byte indicators (e.g., MAX7779)
        'unknown': Cannot determine format
    """
    with open(complete_json_file, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)

    tables = data.get('tables', [])

    # Count format indicators
    column_per_bit_count = 0
    byte_split_count = 0

    for table in tables:  # Check all tables
        table_data = table.get('data', [])
        if not table_data or len(table_data) < 2:
            continue

        header = table_data[0]
        if not header:
            continue

        # Check for column-per-bit format (Bit 7, Bit 6, ...)
        header_str = ' '.join([str(col).lower() for col in header if col])
        header_no_space = ''.join([str(col).lower().replace(' ', '').replace('\n', '') for col in header if col])

        if ('bit7' in header_no_space and 'bit6' in header_no_space) or \
           ('bit 7' in header_str and 'bit 6' in header_str):
            column_per_bit_count += 1
            continue  # Don't double-count

        # Check for byte-split format ([15:8], [7:0])
        for row in table_data[:10]:  # Check first 10 rows for efficiency
            for cell in row:
                if cell and isinstance(cell, str):
                    # Look for [15:8] or [7:0] patterns in register names
                    cell_str = str(cell).replace('\n', '').replace(' ', '')
                    if re.search(r'\[15:8\]|\[7:0\]', cell_str):
                        byte_split_count += 1
                        break
            if byte_split_count > 0:
                break

    # If regs header file provided, check for _15_8/_7_0 suffixes
    has_split_suffixes = False
    if regs_header_file and os.path.exists(regs_header_file):
        with open(regs_header_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Count registers with _15_8 or _7_0 suffixes
            has_15_8 = len(re.findall(r'_15_8\s', content)) > 0
            has_7_0 = len(re.findall(r'_7_0\s', content)) > 0
            if has_15_8 or has_7_0:
                has_split_suffixes = True
                byte_split_count += 10  # Boost score for register suffix pattern

    print(f"Format detection:")
    print(f"  Column-per-bit indicators: {column_per_bit_count}")
    print(f"  Byte-split indicators: {byte_split_count}")
    if has_split_suffixes:
        print(f"  Register suffix pattern detected (_15_8/_7_0)")

    # Determine format based on counts
    if column_per_bit_count > byte_split_count and column_per_bit_count >= 3:
        return 'column_per_bit'
    elif byte_split_count > column_per_bit_count and byte_split_count >= 5:
        return 'byte_split'
    else:
        return 'unknown'


def run_unified_header_generator(complete_file, prefix, output_file):
    """Run unified_header_generator.py for column-per-bit format"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(script_dir, 'unified_header_generator.py')

    cmd = [
        sys.executable,
        script,
        '--complete', complete_file,
        '--prefix', prefix,
        '--output', output_file
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_merge_to_final_header(regs_file, bitfields_file, prefix, output_file):
    """Run merge_to_final_header.py for byte-split 16-bit format"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(script_dir, 'merge_to_final_header.py')

    cmd = [
        sys.executable,
        script,
        '--regs', regs_file,
        '--bitfields', bitfields_file,
        '--prefix', prefix,
        '--output', output_file
    ]

    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description='Auto-detect datasheet format and generate final header'
    )
    parser.add_argument('--complete', required=True,
                       help='Complete JSON file from datasheet_reader.py')
    parser.add_argument('--regs',
                       help='Register header file from reg_parser.py (for byte-split format)')
    parser.add_argument('--bitfields',
                       help='Bitfields JSON file from bitfield_parser.py (for byte-split format)')
    parser.add_argument('-p', '--prefix', required=True,
                       help='Chip prefix for C header (e.g., MAX20370)')
    parser.add_argument('-o', '--output', required=True,
                       help='Output C header file')

    args = parser.parse_args()

    print("=" * 80)
    print("AUTO FINAL HEADER GENERATOR")
    print("=" * 80)

    # Detect format
    print(f"\n[1/2] Detecting datasheet table format...")
    format_type = detect_table_format(args.complete, args.regs)

    if format_type == 'column_per_bit':
        print(f"\n[OK] Detected: Column-per-bit format (e.g., MAX20370)")
        print(f"  Using: unified_header_generator.py\n")

        # Run unified_header_generator
        print("[2/2] Generating final header...")
        returncode = run_unified_header_generator(
            args.complete,
            args.prefix,
            args.output
        )

    elif format_type == 'byte_split':
        print(f"\n[OK] Detected: Byte-split 16-bit format (e.g., MAX7779)")
        print(f"  Using: merge_to_final_header.py\n")

        # Validate required files
        if not args.regs or not args.bitfields:
            print("\n[ERROR] Byte-split format requires --regs and --bitfields arguments")
            print("   Run reg_parser.py and bitfield_parser.py first, then provide:")
            print("   --regs <chip>_regs.h --bitfields <chip>_bitfields.json")
            sys.exit(1)

        if not os.path.exists(args.regs):
            print(f"\n[ERROR] Register file not found: {args.regs}")
            sys.exit(1)

        if not os.path.exists(args.bitfields):
            print(f"\n[ERROR] Bitfields file not found: {args.bitfields}")
            sys.exit(1)

        # Run merge_to_final_header
        print("[2/2] Generating final header...")
        returncode = run_merge_to_final_header(
            args.regs,
            args.bitfields,
            args.prefix,
            args.output
        )

    else:
        print(f"\n[ERROR] Unable to determine datasheet format")
        print("   Could not detect column-per-bit or byte-split patterns")
        print("\n   Manual options:")
        print("   1. For column-per-bit format (Bit 7, Bit 6, ...):")
        print(f"      python unified_header_generator.py --complete {args.complete} -p {args.prefix} -o {args.output}")
        print("\n   2. For byte-split format ([15:8], [7:0]):")
        print(f"      python merge_to_final_header.py --regs <chip>_regs.h --bitfields <chip>_bitfields.json -p {args.prefix} -o {args.output}")
        sys.exit(1)

    print("\n" + "=" * 80)
    if returncode == 0:
        print("[SUCCESS] FINAL HEADER GENERATION COMPLETE")
    else:
        print("[FAILED] Header generation failed")
    print("=" * 80)

    sys.exit(returncode)


if __name__ == '__main__':
    main()
