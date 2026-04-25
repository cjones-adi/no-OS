#!/usr/bin/env python3
"""
PDF Register Bitfield Extractor
Extracts register bit field information from PDF tables and generates JSON output
"""

import re
import sys
import json
import argparse
from pathlib import Path

def extract_register_context_from_text(text_above_table):
    """
    Extract register address and name from text above a table.
    Common patterns:
    - "Register 0x00: CHG_CFG0 - Charger Configuration"
    - "0x00 CHG_CFG0"
    - "CHG_CFG0 (0x00)" or "CHG_CFG0 (0x0)"
    - "INTSRC_STS (0x22)"
    - "Table: Register 0x00"
    """
    if not text_above_table:
        return None, None

    # Pattern 1: "NAME (0x00)" or "NAME (0x0)"
    # Matches: "INTSRC_STS (0x22)", "PMIC_REVISION (0x1)"
    # Must be at start of line or after newline to avoid matching
    match = re.search(r'(?:^|\n)\s*([A-Z][A-Z0-9_]{2,})\s*\(\s*(0x[0-9a-f]{1,2})\s*\)', text_above_table, re.IGNORECASE | re.MULTILINE)
    if match:
        name = match.group(1)
        addr = match.group(2).lower()
        # Normalize address (pad single digit hex)
        if len(addr) == 3:  # 0xN
            addr = '0x0' + addr[2:]
        return addr, name

    # Pattern 2: "Register 0x00: NAME" or "Reg 0x00: NAME"
    match = re.search(r'(?:register|reg)\s+(0x[0-9a-f]+)[:\s]+([A-Z_][A-Z0-9_]*)', text_above_table, re.IGNORECASE)
    if match:
        addr = match.group(1).lower()
        if len(addr) == 3:
            addr = '0x0' + addr[2:]
        return addr, match.group(2)

    # Pattern 3: "0x00: NAME" or "0x00 - NAME"
    match = re.search(r'(0x[0-9a-f]+)\s*[:\-]\s*([A-Z_][A-Z0-9_]*)', text_above_table, re.IGNORECASE)
    if match:
        addr = match.group(1).lower()
        if len(addr) == 3:
            addr = '0x0' + addr[2:]
        return addr, match.group(2)

    # Pattern 4: "NAME - 0x00" (less common)
    match = re.search(r'([A-Z_][A-Z0-9_]*)\s*\-\s*(0x[0-9a-f]+)', text_above_table, re.IGNORECASE)
    if match:
        addr = match.group(2).lower()
        if len(addr) == 3:
            addr = '0x0' + addr[2:]
        return addr, match.group(1)

    # Pattern 5: Just address "0x00"
    match = re.search(r'(0x[0-9a-f]+)', text_above_table, re.IGNORECASE)
    if match:
        addr = match.group(1).lower()
        if len(addr) == 3:
            addr = '0x0' + addr[2:]
        return addr, None

    return None, None

def extract_register_map_from_tables(tables):
    """
    Extract register map (address to name mapping) from register map tables.
    Looking for tables with columns: Address, Register, Name, Description, etc.
    Returns: dict mapping address -> {'name': str, 'page': int, 'description': str}
    """
    register_map = {}

    for table_data in tables:
        # Unpack table data
        if len(table_data) == 5:
            page_num, table, _, _, _ = table_data
        elif len(table_data) == 4:
            page_num, table, _, _ = table_data
        else:
            page_num, table = table_data

        if not table or len(table) < 2:
            continue

        header = table[0]
        if not header:
            continue

        header_str = ' '.join([str(col).lower() if col else '' for col in header])

        # Check if this is a register map table
        # Looking for: Address, Register/Name columns
        has_address = 'address' in header_str or 'addr' in header_str
        has_register = 'register' in header_str or 'reg name' in header_str or 'name' in header_str

        if not (has_address and has_register):
            continue

        # Find column indices
        addr_col = -1
        name_col = -1
        desc_col = -1

        for i, col in enumerate(header):
            if not col:
                continue
            col_str = str(col).lower().strip()

            if 'address' in col_str or col_str == 'addr':
                addr_col = i
            elif 'register' in col_str or 'reg name' in col_str or col_str == 'name':
                name_col = i
            elif 'description' in col_str or 'desc' in col_str:
                desc_col = i

        if addr_col < 0 or name_col < 0:
            continue

        print(f"Found register map table on page {page_num}")

        # Parse each row
        for row in table[1:]:
            if not row or len(row) <= max(addr_col, name_col):
                continue

            addr = row[addr_col]
            name = row[name_col]
            desc = row[desc_col] if desc_col >= 0 and desc_col < len(row) else None

            if not addr or not name:
                continue

            # Clean address
            addr_str = str(addr).strip().lower()
            # Match 0x00, 0X00, 00h, etc.
            addr_match = re.search(r'(0x[0-9a-f]+)', addr_str, re.IGNORECASE)
            if not addr_match:
                # Try hex without 0x prefix
                if re.match(r'^[0-9a-f]+h?$', addr_str, re.IGNORECASE):
                    addr_str = '0x' + addr_str.rstrip('hH')
                else:
                    continue
            else:
                addr_str = addr_match.group(1).lower()

            # Normalize address (pad to 2 digits)
            if len(addr_str) == 3:  # 0xN
                addr_str = '0x0' + addr_str[2:]

            # Clean name
            name_str = str(name).strip()
            # Remove whitespace/newlines from PDF wrapping
            name_str = re.sub(r'\s+', '_', name_str).upper()

            # Store in register map
            if addr_str not in register_map:
                register_map[addr_str] = {
                    'name': name_str,
                    'page': page_num,
                    'description': desc
                }

    return register_map


def extract_tables_from_pdf(pdf_path):
    """Extract tables from PDF file using pdfplumber with context"""
    try:
        import pdfplumber
    except ImportError:
        print("Error: pdfplumber is not installed. Installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
        import pdfplumber

    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                # Extract text from the page
                page_text = page.extract_text() or ""

                # Extract tables with their bounding boxes
                page_tables = page.find_tables()
                if page_tables:
                    for table_obj in page_tables:
                        # Extract the table data
                        table = table_obj.extract()

                        # Get table bounding box
                        bbox = table_obj.bbox
                        table_top = bbox[1] if bbox else 0

                        # Find text above the table (within 200 pixels above)
                        context_text = ""
                        try:
                            # Extract text from region above table
                            if table_top > 50:
                                # Look at text in the region above the table (increased to 200 pixels)
                                above_bbox = (0, max(0, table_top - 200), page.width, table_top)
                                cropped = page.crop(above_bbox)
                                context_text = cropped.extract_text() or ""
                        except:
                            # Fallback: use general page text
                            context_text = page_text

                        # Extract register info from context
                        reg_addr, reg_name = extract_register_context_from_text(context_text)

                        # Store table with context AND page number
                        tables.append((page_num + 1, table, reg_addr, reg_name, page_num + 1))
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                # Fallback to simple table extraction if find_tables fails
                try:
                    page_tables = page.extract_tables()
                    if page_tables:
                        page_text = page.extract_text() or ""
                        for table in page_tables:
                            reg_addr, reg_name = extract_register_context_from_text(page_text)
                            tables.append((page_num + 1, table, reg_addr, reg_name, page_num + 1))
                except:
                    print(f"Warning: Could not extract tables from page {page_num + 1}: {e}")
                    continue

    return tables

def find_register_for_page(page_num, register_map, current_reg_addr=None):
    """
    Find the most likely register for a given page number.
    Strategy:
    1. If current_reg_addr is set, use it (from table header)
    2. Otherwise, find registers on the same page
    3. If multiple on same page, return first one
    4. If none on same page, find nearest page before this one
    """
    if current_reg_addr:
        return current_reg_addr, register_map.get(current_reg_addr, {}).get('name')

    # Find registers on this page
    registers_on_page = [
        (addr, info) for addr, info in register_map.items()
        if info['page'] == page_num
    ]

    if registers_on_page:
        # Sort by address and take first one
        registers_on_page.sort(key=lambda x: int(x[0], 16))
        return registers_on_page[0][0], registers_on_page[0][1]['name']

    # Find nearest register on previous pages (within 5 pages)
    nearest_reg = None
    nearest_page_dist = 999
    for addr, info in register_map.items():
        if info['page'] < page_num and (page_num - info['page']) <= 5:
            page_dist = page_num - info['page']
            if page_dist < nearest_page_dist:
                nearest_page_dist = page_dist
                nearest_reg = (addr, info['name'])

    if nearest_reg:
        return nearest_reg[0], nearest_reg[1]

    return None, None


def parse_bitfield_tables(tables, chip_prefix="MAX20370", register_map=None, verbose=False):
    """
    Parse register bitfield tables.
    Looking for tables with:
    1. BITFIELD/BITS/DESCRIPTION format: BITFIELD, BITS, DESCRIPTION, DECODE (BEST - prioritized)
    2. Explicit bit columns: Reg, Name, Bits, Bit 7, Bit 6, ..., Bit 0, Reset, Access
    3. MSB/LSB format: Reg, Name, MSB, ..., LSB, Reset, Access
    4. Numeric bit columns: BIT, 7, 6, 5, 4, 3, 2, 1, 0

    Args:
        tables: List of table data
        chip_prefix: Chip name prefix
        register_map: Dict mapping address -> {'name': str, 'page': int} from register map tables
    """
    bitfields = []
    bitfield_descriptions = {}  # Store descriptions for SRS generation

    if register_map is None:
        register_map = {}

    for table_data in tables:
        # Unpack table data (with backward compatibility)
        if len(table_data) == 5:
            page_num, table, context_reg_addr, context_reg_name, table_page = table_data
        elif len(table_data) == 4:
            page_num, table, context_reg_addr, context_reg_name = table_data
            table_page = page_num
        else:
            # Legacy format
            page_num, table = table_data
            context_reg_addr, context_reg_name = None, None
            table_page = page_num
        if not table or len(table) < 2:
            continue

        # Get header row
        header = table[0]
        if not header:
            continue

        # Check if this looks like a register summary table
        header_str = ' '.join([str(col).lower() if col else '' for col in header])

        # Format 0: BITFIELD/BITS/DESCRIPTION format (BEST - prioritize this!)
        # Header variations:
        # - BITFIELD, BITS, DESCRIPTION, [DECODE]
        # - BIT NAME, BITS, DESCRIPTION, [SETTINGS], [RESET], [ACCESS]
        # - FIELD, BITS, DESC
        has_bitfield_bits_desc = (('bitfield' in header_str or 'bit name' in header_str or
                                   ('field' in header_str and 'name' in header_str)) and
                                  'bits' in header_str and
                                  ('description' in header_str or 'desc' in header_str))

        # Format 1: Explicit "Bit 7", "Bit 6", etc.
        has_explicit_bits = 'bit 7' in header_str or 'bit 6' in header_str

        # Format 2: MSB/LSB format
        has_msb_lsb = ('msb' in header_str or 'lsb' in header_str) and \
                      ('name' in header_str or 'field' in header_str or 'bit' in header_str)

        # Format 3: "BIT" column with numeric columns (7, 6, 5, 4...) - MAX77779 style
        # Check if first column is "BIT" or "BITFIELD" and other columns are numbers
        has_bit_numeric_cols = False
        if not has_bitfield_bits_desc and header and len(header) > 1:
            first_col = str(header[0]).lower().strip() if header[0] else ''
            if first_col in ['bit', 'bitfield']:
                # Check if next columns are numbers (but not if we have BITS/DESCRIPTION)
                numeric_cols = sum(1 for h in header[1:] if h and str(h).strip().isdigit())
                has_bit_numeric_cols = numeric_cols >= 4

        if not has_bitfield_bits_desc and not has_explicit_bits and not has_msb_lsb and not has_bit_numeric_cols:
            continue

        # Find column indices
        reg_col = -1
        name_col = -1
        bitfield_col = -1  # For BITFIELD column (Format 0)
        description_col = -1  # For DESCRIPTION column (Format 0)
        decode_col = -1  # For DECODE column (Format 0)
        bit_cols = {}  # bit number -> column index
        msb_col = -1
        lsb_col = -1
        bits_col = -1  # "Bits" or "Bit" column showing range like "7:4"

        numeric_bit_cols = {}  # bit number -> column index (for Format 3)

        for i, col in enumerate(header):
            if not col:
                continue
            col_str = str(col).lower().strip()

            if col_str == 'reg' or col_str == 'register' or col_str == 'address':
                reg_col = i
            elif col_str == 'bitfield' or col_str == 'bit field':
                bitfield_col = i
            elif col_str == 'bit name' or col_str == 'bitname':
                bitfield_col = i  # Treat "bit name" as bitfield column
            elif col_str == 'description' or col_str == 'desc':
                description_col = i
            elif col_str == 'decode' or col_str == 'settings':
                decode_col = i  # Treat "settings" as decode column
            elif col_str == 'name' or col_str == 'field' or col_str == 'field name':
                name_col = i
            elif col_str == 'msb':
                msb_col = i
            elif col_str == 'lsb':
                lsb_col = i
            elif col_str == 'bits' or col_str == 'bit':
                bits_col = i
            elif 'bit' in col_str and col_str != 'bits':
                # Extract bit number from "Bit 7", "Bit 6", etc.
                bit_match = re.search(r'bit\s*(\d+)', col_str)
                if bit_match:
                    bit_num = int(bit_match.group(1))
                    bit_cols[bit_num] = i
            # Format 3: numeric columns (7, 6, 5, 4, 3, 2, 1, 0)
            elif col_str.isdigit():
                bit_num = int(col_str)
                numeric_bit_cols[bit_num] = i

        # Determine table format
        # Priority order:
        # 1. BITFIELD/BITS/DESC format (most accurate, has descriptions for SRS)
        # 2. MSB/LSB format (common in many datasheets)
        # 3. Explicit bit format (Bit 7, Bit 6, etc.)
        # Note: Numeric bit format disabled - it gives wrong bit positions for multi-row registers
        is_bitfield_bits_desc_format = (bitfield_col >= 0 or name_col >= 0) and bits_col >= 0 and description_col >= 0
        is_explicit_bit_format = len(bit_cols) >= 4  # Re-enabled: Need at least 4 bit columns
        is_msb_lsb_format = (msb_col >= 0 and lsb_col >= 0) or \
                           (bits_col >= 0 and name_col >= 0)  # Re-enabled: MSB/LSB columns OR Bits+Name
        is_numeric_bit_format = False  # Disabled - wrong positions for multi-row registers

        if not is_bitfield_bits_desc_format and not is_explicit_bit_format and not is_msb_lsb_format and not is_numeric_bit_format:
            continue

        # Determine which format to use (priority order)
        # Prefer BITFIELD/BITS/DESC when available, otherwise use MSB/LSB or explicit bits
        if is_bitfield_bits_desc_format:
            format_name = 'BITFIELD/BITS/DESC'
        elif is_msb_lsb_format:
            format_name = 'MSB/LSB'
            # Disable other formats if MSB/LSB is selected
            is_bitfield_bits_desc_format = False
            is_explicit_bit_format = False
        elif is_explicit_bit_format:
            format_name = 'explicit bits'
            is_bitfield_bits_desc_format = False
            is_msb_lsb_format = False
        else:
            format_name = 'numeric bits'

        print(f"Found register summary table on page {page_num} ({format_name})")

        # Debug: Print column info for MSB/LSB format
        if is_msb_lsb_format and verbose:
            print(f"  MSB col: {msb_col}, LSB col: {lsb_col}, Bits col: {bits_col}, Name col: {name_col}")
            print(f"  Header: {header[:10] if len(header) > 10 else header}")

        # Parse each row
        for row_idx, row in enumerate(table[1:]):  # Skip header
            if not row or len(row) == 0:
                continue

            # Format 0: BITFIELD/BITS/DESCRIPTION (BEST - most accurate)
            if is_bitfield_bits_desc_format:
                # Try to get register address/name from context (text above table)
                register_addr = context_reg_addr
                register_name = context_reg_name

                # If not in context, try to get from table column
                if not register_addr and not register_name:
                    if reg_col >= 0 and reg_col < len(row) and row[reg_col]:
                        reg_value = str(row[reg_col]).strip()
                        # Check if it looks like an address (0x00, 00h, etc.)
                        if re.match(r'^(0x[0-9a-f]+|[0-9a-f]+h)$', reg_value, re.IGNORECASE):
                            register_addr = reg_value
                        elif reg_value and not re.match(r'^(reg|register|address)$', reg_value, re.IGNORECASE):
                            register_name = reg_value

                # If still not found, use register map based on page proximity
                if not register_addr and not register_name and register_map:
                    register_addr, register_name = find_register_for_page(table_page, register_map, None)

                # Get field name from BITFIELD or name column
                field_col = bitfield_col if bitfield_col >= 0 else name_col
                if field_col < 0 or field_col >= len(row):
                    continue

                field_name = row[field_col]
                if not field_name:
                    continue

                field_name = str(field_name).strip()
                # Remove newlines and extra whitespace from field name (PDF line wrapping)
                field_name = re.sub(r'\s+', '', field_name)
                # Remove _MASK suffix if present (we'll add it back later)
                if field_name.endswith('_MASK'):
                    field_name = field_name[:-5]

                # Remove bit range suffixes like _7_0, _15_8, etc. from field names
                # These indicate the bit range but shouldn't be part of the field name
                field_name = re.sub(r'_\d+_\d+$', '', field_name)
                field_name = re.sub(r'_\[\d+:\d+\]$', '', field_name)

                # Skip reserved fields and single-letter artifacts
                if re.match(r'^(reserved|rfu|rsvd|-|n/a|[a-z])$', field_name, re.IGNORECASE):
                    continue

                # Skip if field name is too short (likely artifact)
                if len(field_name) < 2:
                    continue

                # Get bit range from BITS column
                if bits_col < 0 or bits_col >= len(row) or not row[bits_col]:
                    continue

                bits_str = str(row[bits_col]).strip()

                # Parse bit range: "7:4", "7", "15:8", etc.
                bit_range_match = re.search(r'(\d+)\s*[:‑\-\.]+\s*(\d+)', bits_str)
                if bit_range_match:
                    msb_val = int(bit_range_match.group(1))
                    lsb_val = int(bit_range_match.group(2))
                    if msb_val < lsb_val:
                        msb_val, lsb_val = lsb_val, msb_val
                    field_bits = list(range(lsb_val, msb_val + 1))
                else:
                    # Single bit
                    single_bit_match = re.search(r'^\s*(\d+)\s*$', bits_str)
                    if single_bit_match:
                        bit_val = int(single_bit_match.group(1))
                        field_bits = [bit_val]
                    else:
                        continue

                # Store bitfield with register info
                bitfield_entry = (field_name, field_bits, register_addr, register_name)
                bitfields.append(bitfield_entry)

                # Store description and decode for SRS generation
                if description_col >= 0 and description_col < len(row) and row[description_col]:
                    desc = str(row[description_col]).strip()
                    if decode_col >= 0 and decode_col < len(row) and row[decode_col]:
                        decode = str(row[decode_col]).strip()
                        bitfield_descriptions[field_name] = f"{desc} | {decode}"
                    else:
                        bitfield_descriptions[field_name] = desc

            # Format 1: Explicit bit format
            elif is_explicit_bit_format:
                # Original logic for explicit "Bit 7", "Bit 6" format
                bit_to_field = {}  # bit_num -> field_name

                for bit_num in sorted(bit_cols.keys(), reverse=True):
                    col_idx = bit_cols[bit_num]
                    if col_idx >= len(row):
                        continue

                    field_name = row[col_idx]
                    if field_name:
                        field_name = str(field_name).strip()
                        if not re.match(r'^reserved$', field_name, re.IGNORECASE):
                            bit_to_field[bit_num] = field_name

                # Group consecutive bits
                current_field = None
                field_bits = []

                for bit_num in sorted(bit_cols.keys(), reverse=True):  # Bit 7 down to 0
                    if bit_num in bit_to_field:
                        # Found a named field
                        if current_field and field_bits:
                            # Save previous field
                            bitfields.append((current_field, field_bits))
                        # Start new field
                        current_field = bit_to_field[bit_num]
                        field_bits = [bit_num]
                    else:
                        # Empty cell - belongs to current field if one is active
                        if current_field:
                            field_bits.append(bit_num)

                # Don't forget the last field in the row
                if current_field and field_bits:
                    bitfields.append((current_field, field_bits, None, None))

            elif is_msb_lsb_format:
                # MSB/LSB format - two cases:
                # Case 1: MSB and LSB are column headers, bit field names are in cells (MAX86178 style)
                # Case 2: MSB and LSB are values in cells, field name is in NAME column

                # Detect which case: if MSB/LSB columns exist and there are multiple columns between them
                if msb_col >= 0 and lsb_col >= 0 and (lsb_col - msb_col) >= 2:
                    # Case 1: MSB/LSB as headers, bit field names in between
                    # Columns between MSB and LSB represent bit positions
                    # Parse bit fields from cells in those columns
                    bit_to_field = {}  # bit_num -> field_name

                    # Calculate bit positions from column positions
                    # MSB column = highest bit, LSB column = lowest bit
                    num_bit_cols = lsb_col - msb_col + 1

                    for col_offset in range(num_bit_cols):
                        col_idx = msb_col + col_offset
                        bit_num = (num_bit_cols - 1) - col_offset  # MSB is highest bit

                        if col_idx >= len(row):
                            continue

                        field_value = row[col_idx]
                        if field_value:
                            field_value_original = str(field_value).strip()
                            # Remove newlines and normalize whitespace
                            field_value_original = re.sub(r'\s+', '', field_value_original)

                            # Check if field has a bit range suffix in brackets [N:M]
                            # This indicates the field spans those bits (within 0-7 range for 8-bit register)
                            bit_range_match = re.search(r'\[(\d+):(\d+)\]$', field_value_original)
                            single_bit_match = re.search(r'\[(\d+)\]$', field_value_original)

                            # IMPORTANT: Extract and store range hint BEFORE cleaning the field name
                            range_hint = None  # Will store (msb, lsb) if applicable

                            if bit_range_match:
                                # Field like FIELD[6:0] or FIELD[10:8] in single cell
                                msb = int(bit_range_match.group(1))
                                lsb = int(bit_range_match.group(2))
                                # Store the range hint regardless of whether it's in 0-7 range
                                range_hint = (msb, lsb)
                                # Clean field name
                                field_value = re.sub(r'\[\d+:\d+\]$', '', field_value_original)

                                # Only use the suffix range if it's within the valid 0-7 bit range
                                # This filters out things like [10:8] which we'll handle in gap-filling
                                if msb <= 7 and lsb >= 0:
                                    # Store this field for all bits in the range
                                    for b in range(lsb, msb + 1):
                                        bit_to_field[b] = field_value
                                    continue
                            elif single_bit_match:
                                # Field like FIELD[8] - extract the bit number
                                bit_num_suffix = int(single_bit_match.group(1))
                                field_value = re.sub(r'\[\d+\]$', '', field_value_original)
                                range_hint = (bit_num_suffix, bit_num_suffix)

                                # Only use suffix if it's within 0-7 range
                                if bit_num_suffix <= 7:
                                    bit_to_field[bit_num_suffix] = field_value
                                    continue

                            # No bit range suffix in valid range, or suffix out of range
                            # Clean the field value further
                            field_value = re.sub(r'\[\d+:\d+\]$', '', field_value_original) if not range_hint else field_value
                            field_value = re.sub(r'\[\d+\]$', '', field_value)
                            field_value = re.sub(r'_\d+_\d+$', '', field_value)
                            field_value = re.sub(r'_\d+$', '', field_value)

                            # Skip reserved/empty
                            if field_value and not re.match(r'^(reserved|rfu|rsvd|-|n/a|–|—|�|\s*)$', field_value, re.IGNORECASE):
                                # Store field with optional range hint
                                if range_hint and range_hint not in [(7,7), (6,6), (5,5), (4,4), (3,3), (2,2), (1,1), (0,0)]:
                                    # Out-of-register-range hint (like [10:8]) - store with hint for later processing
                                    bit_to_field[bit_num] = (field_value, range_hint)
                                else:
                                    # Normal case
                                    bit_to_field[bit_num] = field_value

                    # Fill in gaps between bits with same field name (handles merged PDF cells)
                    # Example: if bit 7 and bit 5 both have "ECG_NDIV" but bit 6 is empty,
                    # fill in bit 6 as well (PDF merged cells scenario)
                    bit_to_field_filled = dict(bit_to_field)

                    # First pass: if a field has an out-of-range bit hint like [10:8],
                    # map it to the actual register bits
                    for bit_num, field_entry in list(bit_to_field.items()):
                        # Check if this is a tuple with range hint
                        if isinstance(field_entry, tuple):
                            field_name, (hint_msb, hint_lsb) = field_entry
                            hint_width = hint_msb - hint_lsb + 1  # Number of bits indicated

                            # Map the hint range to register bits
                            # For example, [10:8] is 3 bits, so if appearing at column/bit 7,
                            # it should map to bits 7, 6, 5
                            if 2 <= hint_width <= 8 and bit_num >= hint_width - 1:
                                # Fill from bit_num down for hint_width bits
                                start_bit = bit_num
                                end_bit = max(0, bit_num - hint_width + 1)
                                for fill_bit in range(end_bit, start_bit + 1):
                                    bit_to_field_filled[fill_bit] = field_name
                                    if verbose and fill_bit != start_bit:
                                        print(f"      Filled from range hint: bit {fill_bit} = {field_name} (hint [{hint_msb}:{hint_lsb}])")
                        else:
                            # Normal field name, keep as is
                            bit_to_field_filled[bit_num] = field_entry

                    # Second pass: fill gaps between consecutive bits with same name
                    for bit_num in sorted(bit_to_field_filled.keys(), reverse=True):
                        field_name = bit_to_field_filled[bit_num]
                        # Skip if this is a tuple (shouldn't happen after first pass)
                        if isinstance(field_name, tuple):
                            field_name = field_name[0]
                            bit_to_field_filled[bit_num] = field_name

                        # Look for nearby bits with same field name and fill between
                        for check_bit in range(bit_num - 1, -1, -1):
                            check_field = bit_to_field_filled.get(check_bit)
                            if isinstance(check_field, tuple):
                                check_field = check_field[0]

                            if check_field:
                                if check_field == field_name:
                                    # Found same field name, fill any gaps between
                                    for fill_bit in range(check_bit + 1, bit_num):
                                        if fill_bit not in bit_to_field_filled:
                                            bit_to_field_filled[fill_bit] = field_name
                                            if verbose:
                                                print(f"      Filled gap: bit {fill_bit} = {field_name}")
                                    break
                                else:
                                    # Different field, stop looking
                                    break
                            elif check_bit < bit_num - 2:
                                # Gap is too large, probably different field
                                break

                    # Group consecutive bits with same field name
                    processed_bits = set()

                    for bit_num in sorted(bit_to_field_filled.keys(), reverse=True):
                        if bit_num in processed_bits:
                            continue

                        field_name = bit_to_field_filled[bit_num]
                        field_bits = [bit_num]
                        processed_bits.add(bit_num)

                        # Look for consecutive lower bits with same field name
                        for lower_bit in range(bit_num - 1, -1, -1):
                            if lower_bit in bit_to_field_filled and bit_to_field_filled[lower_bit] == field_name:
                                field_bits.append(lower_bit)
                                processed_bits.add(lower_bit)
                            else:
                                break

                        # Get register info: try to get from current row first (ADDRESS column)
                        register_addr = None
                        register_name = None

                        # Check if there's an ADDRESS column (column 0) in this row
                        if len(row) > 0 and row[0]:
                            addr_cell = str(row[0]).strip()
                            # Check if it looks like an address
                            if re.match(r'^0x[0-9A-Fa-f]+$', addr_cell):
                                register_addr = addr_cell.lower()
                                if len(register_addr) == 3:  # 0xN -> 0x0N
                                    register_addr = '0x0' + register_addr[2:]

                        # Check if there's a NAME column (column 1) in this row
                        if len(row) > 1 and row[1]:
                            name_cell = str(row[1]).strip()
                            # Remove bit range from register name
                            register_name = re.sub(r'\[\d+:\d+\]$', '', name_cell)

                        # Fallback to context if not in row
                        if not register_addr:
                            register_addr = context_reg_addr
                        if not register_name:
                            register_name = context_reg_name

                        # Final fallback to register map
                        if not register_addr and not register_name and register_map:
                            register_addr, register_name = find_register_for_page(table_page, register_map, None)

                        if verbose:
                            print(f"    Created field: {field_name} bits={field_bits} reg={register_addr}")

                        bitfields.append((field_name, field_bits, register_addr, register_name))

                else:
                    # Case 2: Traditional MSB/LSB format (values in cells, name in NAME column)
                    # Get field name
                    if name_col < 0 or name_col >= len(row):
                        continue

                    field_name = row[name_col]
                    if not field_name:
                        continue

                    field_name = str(field_name).strip()
                    if re.match(r'^(reserved|rfu|rsvd|-|n/a)$', field_name, re.IGNORECASE):
                        continue

                    # Parse bit range from MSB/LSB columns or Bits column
                    msb_val = None
                    lsb_val = None

                    # Try Bits column first (format: "7:4" or "15:8")
                    if bits_col >= 0 and bits_col < len(row) and row[bits_col]:
                        bits_str = str(row[bits_col]).strip()
                        # Handle formats: "7:4", "[7:4]", "7-4", "7..4"
                        bit_range_match = re.search(r'(\d+)\s*[:‑\-\.]+\s*(\d+)', bits_str)
                        if bit_range_match:
                            msb_val = int(bit_range_match.group(1))
                            lsb_val = int(bit_range_match.group(2))
                        else:
                            # Single bit
                            single_bit_match = re.search(r'^\s*(\d+)\s*$', bits_str)
                            if single_bit_match:
                                msb_val = lsb_val = int(single_bit_match.group(1))

                    # If not found, try MSB/LSB columns
                    if msb_val is None and msb_col >= 0 and msb_col < len(row) and row[msb_col]:
                        msb_str = str(row[msb_col]).strip()
                        if msb_str.isdigit():
                            msb_val = int(msb_str)

                    if lsb_val is None and lsb_col >= 0 and lsb_col < len(row) and row[lsb_col]:
                        lsb_str = str(row[lsb_col]).strip()
                        if lsb_str.isdigit():
                            lsb_val = int(lsb_str)

                    # Create bit list
                    if msb_val is not None and lsb_val is not None:
                        # Ensure MSB >= LSB
                        if msb_val < lsb_val:
                            msb_val, lsb_val = lsb_val, msb_val

                        field_bits = list(range(lsb_val, msb_val + 1))
                        bitfields.append((field_name, field_bits, None, None))
                    elif msb_val is not None:
                        # Single bit (MSB only)
                        bitfields.append((field_name, [msb_val], None, None))

            elif is_numeric_bit_format:
                # Format 3: Numeric bit columns (BIT | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0)
                # The field names appear in the cells under the bit number columns
                # Example: Row = ['Field', '�', '�', '�', 'TSHDN_DIS', '�', '�', '�', '�']
                #          where 'TSHDN_DIS' is at bit 4 position

                # Skip rows that are reset values (all cells contain binary/hex patterns)
                # Check if this looks like a reset value row
                if row and len(row) > 1:
                    non_empty_cells = [str(cell).strip() for cell in row[1:] if cell and str(cell).strip()]
                    if non_empty_cells:
                        # If all non-empty cells are reset values, skip this row
                        all_reset_values = all(
                            re.match(r'^(0b[01]+|0x[0-9a-f]+|�|\u2500|\u2502)$', cell, re.IGNORECASE)
                            for cell in non_empty_cells
                        )
                        if all_reset_values:
                            continue

                bit_to_field = {}  # bit_num -> field_name

                for bit_num in sorted(numeric_bit_cols.keys(), reverse=True):
                    col_idx = numeric_bit_cols[bit_num]
                    if col_idx >= len(row):
                        continue

                    field_value = row[col_idx]
                    if field_value:
                        field_value = str(field_value).strip()
                        # Skip reserved/empty indicators including Unicode box drawing chars
                        # Common empty indicators: reserved, RFU, -, N/A, �, single digits (bit numbers), etc.
                        if field_value and not re.match(r'^(reserved|rfu|rsvd|-|n/a|–|—|�|\s*|\u2014|\u2013|\u2500|\u2502|\u2550|\u2551|0b[01]+|0x[0-9a-f]+|field|reset|access|default|type|\d+)$', field_value, re.IGNORECASE):
                            # Also skip if it's just access modes
                            if not re.match(r'^(r|w|r/w|ro|wo|rw|rc|wc)$', field_value, re.IGNORECASE):
                                bit_to_field[bit_num] = field_value

                # Only process if we found at least one field
                if not bit_to_field:
                    continue

                # Group consecutive bits ONLY if they have the same field name
                # Don't automatically group empty cells with named fields
                processed_bits = set()

                for bit_num in sorted(numeric_bit_cols.keys(), reverse=True):  # Bit 7 down to 0
                    if bit_num in processed_bits or bit_num not in bit_to_field:
                        continue

                    field_name = bit_to_field[bit_num]
                    field_bits = [bit_num]
                    processed_bits.add(bit_num)

                    # Look for consecutive lower bits with the SAME field name
                    for lower_bit in range(bit_num - 1, -1, -1):
                        if lower_bit not in numeric_bit_cols:
                            continue
                        if lower_bit in bit_to_field and bit_to_field[lower_bit] == field_name:
                            field_bits.append(lower_bit)
                            processed_bits.add(lower_bit)
                        else:
                            # Different field or empty - stop grouping
                            break

                    bitfields.append((field_name, field_bits, None, None))

    return bitfields, bitfield_descriptions

def generate_json_output(bitfields, chip_prefix="MAX20370", output_file=None, descriptions=None, pretty=True):
    """Generate JSON output with bit field definitions"""

    if not bitfields:
        print("Warning: No bit fields found in the PDF")
        return

    if descriptions is None:
        descriptions = {}

    # Build JSON structure similar to hardware_spec_parser.py
    result = {
        "source": output_file or "PDF datasheet",
        "format": "pdf",
        "device_name": chip_prefix,
        "bitfields": []
    }

    # Remove duplicates and build bitfield entries
    seen = set()
    for bitfield_data in bitfields:
        # Unpack bitfield data (with backward compatibility)
        if len(bitfield_data) == 4:
            field_name, bits, register_addr, register_name = bitfield_data
        else:
            # Legacy format
            field_name, bits = bitfield_data
            register_addr, register_name = None, None

        # Skip if already seen
        field_key = (field_name, tuple(sorted(bits)))
        if field_key in seen:
            continue
        seen.add(field_key)

        # Sort bits to get position and width
        bits_sorted = sorted(bits)
        position = bits_sorted[0]  # Lowest bit (LSB)
        width = len(bits)

        # Build bitfield entry
        entry = {
            "name": field_name,
            "position": position,
            "width": width,
            "bits": f"{max(bits)}:{min(bits)}" if width > 1 else str(position)
        }

        # Add register information if available
        if register_addr:
            entry["register_address"] = register_addr
        if register_name:
            entry["register_name"] = register_name

        # Add description if available
        if field_name in descriptions:
            desc = descriptions[field_name]
            # Split description and decode if separated by |
            if " | " in desc:
                description, decode = desc.split(" | ", 1)
                entry["description"] = description.strip()
                entry["decode"] = decode.strip()
            else:
                entry["description"] = desc

        result["bitfields"].append(entry)

    # Write JSON output
    indent = 2 if pretty else None
    output_json = json.dumps(result, indent=indent)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"JSON file generated: {output_file}")
        print(f"Total bit fields: {len(result['bitfields'])}")
    else:
        print(output_json)

    return result

def convert_to_snake_case(name):
    """Convert PascalCase/camelCase to SNAKE_CASE"""
    # Remove any whitespace
    name = re.sub(r'\s+', '', name)

    # Insert underscore before uppercase letters that follow lowercase letters or digits
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    # Insert underscore before uppercase letters followed by lowercase (handles acronyms)
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)

    # Convert to uppercase
    name = name.upper()

    # Keep only alphanumeric and underscores
    name = re.sub(r'[^\w]', '_', name)
    # Replace multiple underscores with single
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')

    return name

def generate_c_header(bitfields, chip_prefix="MAX20370", output_file=None, descriptions=None):
    """Generate C header file with bit field mask defines"""

    if not bitfields:
        print("Warning: No bit fields found in the PDF")
        return

    if descriptions is None:
        descriptions = {}

    header_guard = f"{chip_prefix}_BITS_H"

    header_content = f"""/*
 * {chip_prefix} Register Bit Field Definitions
 * Auto-generated from PDF datasheet
 */

#ifndef {header_guard}
#define {header_guard}

#include <linux/bits.h>

/* Register Bit Field Masks */
"""

    # Add bitfield defines
    seen = set()
    for bitfield_data in bitfields:
        # Unpack bitfield data (with backward compatibility)
        if len(bitfield_data) == 4:
            field_name, bits, register_addr, register_name = bitfield_data
        else:
            # Legacy format
            field_name, bits = bitfield_data
            register_addr, register_name = None, None

        # Convert to snake case
        snake_name = convert_to_snake_case(field_name)

        if not snake_name:
            continue

        # Create the mask name
        mask_name = f"{chip_prefix}_{snake_name}_MASK"

        # Skip duplicates
        if mask_name in seen:
            continue
        seen.add(mask_name)

        # Sort bits to get highest and lowest
        bits_sorted = sorted(bits, reverse=True)
        highest_bit = bits_sorted[0]
        lowest_bit = bits_sorted[-1]

        # Add description as comment if available
        if field_name in descriptions:
            desc = descriptions[field_name]
            # Wrap long descriptions to 80 chars
            if len(desc) > 70:
                desc = desc[:67] + "..."
            header_content += f"/* {desc} */\n"

        # Generate the define
        if len(bits) == 1:
            # Single bit - use BIT()
            header_content += f"#define {mask_name}\tBIT({highest_bit})\n"
        else:
            # Multiple bits - use GENMASK(high, low)
            header_content += f"#define {mask_name}\tGENMASK({highest_bit}, {lowest_bit})\n"

    header_content += f"\n#endif /* {header_guard} */\n"

    # Write to file or print
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(header_content)
        print(f"C header file generated: {output_file}")
        print(f"Total bit fields: {len(seen)}")
    else:
        print(header_content)

    return header_content

def main():
    parser = argparse.ArgumentParser(
        description='Extract register bit field information from PDF datasheets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s datasheet.pdf -o bitfields.json
  %(prog)s datasheet.pdf -p MAX20370 -o max20370_bits.json
  %(prog)s datasheet.pdf -o bitfields.json --pretty
  %(prog)s datasheet.pdf -o bitfields.h --format c-header  # Legacy C header output
        """
    )

    parser.add_argument('pdf_file', help='Input PDF file containing register bit field tables')
    parser.add_argument('-o', '--output', help='Output file (JSON or C header, default: print JSON to stdout)')
    parser.add_argument('-p', '--prefix', default='MAX20370',
                       help='Chip prefix for defines (default: MAX20370)')
    parser.add_argument('--format', choices=['json', 'c-header'], default='json',
                       help='Output format: json (default) or c-header (legacy)')
    parser.add_argument('--pretty', action='store_true',
                       help='Pretty-print JSON output (default: enabled)', default=True)
    parser.add_argument('--no-pretty', action='store_false', dest='pretty',
                       help='Compact JSON output')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose debug output')

    args = parser.parse_args()

    # Check if PDF file exists
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: PDF file '{args.pdf_file}' not found")
        return 1

    print(f"Reading PDF file: {args.pdf_file}")

    # Extract tables from PDF
    try:
        tables = extract_tables_from_pdf(args.pdf_file)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 1

    print(f"Extracted {len(tables)} table(s) from PDF")

    # First pass: Extract register map from tables
    print(f"Extracting register map...")
    register_map = extract_register_map_from_tables(tables)
    print(f"Found {len(register_map)} unique register(s) in register map")

    # Second pass: Parse bit field tables with register map context
    print(f"Parsing bit field tables...")
    bitfields, descriptions = parse_bitfield_tables(tables, args.prefix, register_map, args.verbose)

    if not bitfields:
        print("No bit field tables found. Make sure the PDF contains register summary tables.")
        return 1

    print(f"Found {len(bitfields)} bit field(s)")

    # Generate output based on format
    if args.format == 'json':
        generate_json_output(bitfields, args.prefix, args.output, descriptions, args.pretty)
    else:  # c-header
        generate_c_header(bitfields, args.prefix, args.output, descriptions)

    return 0

if __name__ == "__main__":
    sys.exit(main())
