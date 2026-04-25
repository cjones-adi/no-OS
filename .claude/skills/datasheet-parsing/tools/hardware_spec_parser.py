#!/usr/bin/env python3
"""
Hardware Specification Parser Tool for GitHub Copilot Agents

Universal parser for hardware specifications in multiple formats:
- PDF datasheets
- XML register maps (IP-XACT, vendor-specific)
- CSV register tables
- YAML register definitions

Usage:
    python hardware_spec_parser.py <file_path> [--output <json_file>] [--format <format>]

Formats:
    - pdf: PDF datasheet
    - xml: XML register map
    - csv: CSV register table
    - yaml/yml: YAML register definition
    - auto: Auto-detect format (default)
"""

import sys
import json
import re
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import xml.etree.ElementTree as ET

try:
    import PyPDF2
    import pdfplumber
    import tabula
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class HardwareSpecParser:
    """Parse hardware specifications from multiple file formats."""

    def __init__(self, file_path: str, format_type: str = "auto"):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.format_type = format_type
        if format_type == "auto":
            self.format_type = self._detect_format()

        self.data = {
            "source": str(self.file_path),
            "format": self.format_type,
            "device_name": None,
            "manufacturer": None,
            "registers": [],
            "pins": [],
            "electrical_specs": {},
            "features": [],
            "interfaces": [],
            "metadata": {}
        }

    def _detect_format(self) -> str:
        """Auto-detect file format from extension."""
        ext = self.file_path.suffix.lower()
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.xml', '.yda']:
            # .yda (YAML Design Automation) files are XML-based register maps
            return 'xml'
        elif ext == '.csv':
            return 'csv'
        elif ext in ['.yaml', '.yml']:
            return 'yaml'
        else:
            raise ValueError(f"Unknown file format: {ext}")

    def parse(self) -> Dict[str, Any]:
        """Parse the file based on detected format."""
        if self.format_type == 'pdf':
            if not PDF_AVAILABLE:
                raise ImportError("PDF parsing requires: pip install PyPDF2 pdfplumber tabula-py")
            return self._parse_pdf()
        elif self.format_type == 'xml':
            return self._parse_xml()
        elif self.format_type == 'csv':
            return self._parse_csv()
        elif self.format_type == 'yaml':
            if not YAML_AVAILABLE:
                raise ImportError("YAML parsing requires: pip install pyyaml")
            return self._parse_yaml()
        else:
            raise ValueError(f"Unsupported format: {self.format_type}")

    def _parse_pdf(self) -> Dict[str, Any]:
        """Parse PDF datasheet (existing functionality)."""
        self._extract_pdf_metadata()
        self._extract_pdf_text()
        self._extract_pdf_features()
        self._extract_pdf_registers()
        self._extract_pdf_pins()
        self._extract_pdf_electrical_specs()
        self._extract_pdf_interfaces()
        return self.data

    def _parse_xml(self) -> Dict[str, Any]:
        """Parse XML register map."""
        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            # Extract metadata
            self._extract_xml_metadata(root)

            # Extract registers and bit fields
            self._extract_xml_registers(root)

            return self.data

        except Exception as e:
            print(f"Error parsing XML: {e}", file=sys.stderr)
            return self.data

    def _extract_xml_metadata(self, root: ET.Element):
        """Extract metadata from XML."""
        # Extract properties first (for YDA files)
        properties = root.find(".//Properties")
        if properties is not None:
            for prop in properties:
                if prop.text:
                    self.data["metadata"][prop.tag] = prop.text
                    # For YDA files, use Description as device_name
                    if prop.tag == 'Description' and prop.text.strip() and not self.data["device_name"]:
                        self.data["device_name"] = prop.text.strip()

        # Try to find device/hardware name if not already set
        if not self.data["device_name"]:
            for name_tag in ['HardwareName', 'DeviceName']:
                elem = root.find(f".//Properties/{name_tag}")
                if elem is not None and elem.text and elem.text.strip():
                    self.data["device_name"] = elem.text.strip()
                    break

    def _extract_xml_registers(self, root: ET.Element):
        """Extract register definitions from XML."""
        # First, try the YDA/IP-XACT format with BitFieldRefs
        if self._extract_xml_with_bitfield_refs(root):
            return

        # Fallback: Try common XML register map structures
        registers_found = False
        for reg_path in [
            ".//Register",
            ".//Registers/Register",
            ".//MemoryMap//Register",
            ".//BitField"
        ]:
            for reg_elem in root.findall(reg_path):
                reg_entry = self._parse_xml_register(reg_elem)
                if reg_entry:
                    self.data["registers"].append(reg_entry)
                    registers_found = True

        # Handle BitFields with parent Register structure
        if not registers_found:
            memory_map = root.find(".//MemoryMap")
            if memory_map is not None:
                self._extract_xml_bitfields(memory_map)

    def _parse_xml_register(self, elem: ET.Element) -> Optional[Dict]:
        """Parse a single register element."""
        reg = {}

        # Extract register name
        name_elem = elem.find(".//Name")
        if name_elem is not None and name_elem.text:
            reg["name"] = name_elem.text

        # Extract address
        for addr_tag in ["Address", "Offset", "offset", "address"]:
            addr_elem = elem.find(f".//{addr_tag}")
            if addr_elem is not None and addr_elem.text:
                # Handle Verilog-style addresses like 'h0000
                addr_text = addr_elem.text.strip("'").replace("h", "0x").replace("d", "")
                reg["address"] = addr_text
                break

        # Extract access mode
        access_elem = elem.find(".//Access")
        if access_elem is not None and access_elem.text:
            reg["access"] = access_elem.text

        # Extract default value
        default_elem = elem.find(".//DefaultValue")
        if default_elem is not None and default_elem.text:
            reg["reset_value"] = default_elem.text

        # Extract description
        desc_elem = elem.find(".//Description")
        if desc_elem is not None and desc_elem.text:
            reg["description"] = desc_elem.text

        # Extract bit width
        width_elem = elem.find(".//BitWidth")
        if width_elem is not None and width_elem.text:
            reg["width"] = width_elem.text

        # Extract bit position
        pos_elem = elem.find(".//BitPosition")
        if pos_elem is not None and pos_elem.text:
            reg["position"] = pos_elem.text

        return reg if reg else None

    def _extract_xml_with_bitfield_refs(self, root: ET.Element) -> bool:
        """
        Extract register map using BitFieldRefs structure (YDA/IP-XACT format).
        This handles the case where Registers reference BitFields via UIDs.
        Returns True if successful, False if format not detected.
        """
        # Build dictionary of BitFields by UID for quick lookup
        bitfield_dict = {}
        for bitfield in root.findall('.//BitFields/BitField'):
            uid_elem = bitfield.find('UID')
            if uid_elem is not None and uid_elem.text:
                uid = uid_elem.text.strip()
                bitfield_dict[uid] = {
                    'name': bitfield.findtext('Name', 'N/A'),
                    'width': bitfield.findtext('Width', 'N/A'),
                    'access': bitfield.findtext('Access', 'N/A'),
                    'default_value': bitfield.findtext('DefaultValue', 'N/A'),
                    'description': bitfield.findtext('Description', 'N/A'),
                    'documentation': bitfield.findtext('Documentation', 'N/A')
                }

        if not bitfield_dict:
            return False  # No BitFields found, try other methods

        # Find all Registers
        registers = root.findall('.//RegisterMap//Register')
        if not registers:
            registers = root.findall('.//Register')

        if not registers:
            return False  # No Registers found

        extracted_count = 0

        for register in registers:
            reg_name = register.findtext('Name', 'N/A')
            reg_address = register.findtext('Address', 'N/A')

            # Convert Verilog-style address to hex
            if reg_address.startswith("'h"):
                reg_address = '0x' + reg_address[2:]
            elif reg_address.startswith("'d"):
                try:
                    reg_address = hex(int(reg_address[2:]))
                except:
                    pass

            # Find all BitFieldRefs within this Register
            for bitfield_ref in register.findall('.//BitFieldRef'):
                bf_uid_elem = bitfield_ref.find('BF-UID')
                if bf_uid_elem is not None and bf_uid_elem.text:
                    bf_uid = bf_uid_elem.text.strip()

                    # Get bit position and width from the reference
                    reg_offset = bitfield_ref.findtext('RegOffset', '0')
                    slice_width = bitfield_ref.findtext('SliceWidth', '1')

                    # Look up the BitField details
                    if bf_uid in bitfield_dict:
                        bf_info = bitfield_dict[bf_uid]

                        # Create entry in same format as CSV parser
                        entry = {
                            'register': reg_name,
                            'address': reg_address,
                            'name': bf_info['name'],
                            'position': reg_offset,
                            'width': slice_width,
                            'access': bf_info['access'],
                            'reset_value': bf_info['default_value'],
                            'description': bf_info['description'],
                        }

                        # Add documentation if available
                        if bf_info['documentation'] and bf_info['documentation'] != 'N/A':
                            entry['documentation'] = bf_info['documentation']
                        elif bf_info['description'] and bf_info['description'] != 'N/A':
                            entry['documentation'] = bf_info['description']

                        self.data["registers"].append(entry)
                        extracted_count += 1

        return extracted_count > 0

    def _extract_xml_bitfields(self, memory_map: ET.Element):
        """Extract BitFields from IP-XACT style XML (fallback method)."""
        bitfields = memory_map.find(".//BitFields")
        if bitfields is None:
            return

        for bitfield in bitfields.findall(".//BitField"):
            bf_entry = {}

            # Name
            name = bitfield.find(".//Name")
            if name is not None and name.text:
                bf_entry["name"] = name.text

            # Access
            access = bitfield.find(".//Access")
            if access is not None and access.text:
                bf_entry["access"] = access.text

            # Default value
            default = bitfield.find(".//DefaultValue")
            if default is not None and default.text:
                bf_entry["reset_value"] = default.text

            # Description
            desc = bitfield.find(".//Description")
            if desc is not None and desc.text:
                bf_entry["description"] = desc.text

            # Documentation
            doc_set = bitfield.find(".//DocSets/Set1")
            if doc_set is not None:
                doc_name = doc_set.find(".//Name")
                doc_desc = doc_set.find(".//Description")
                if doc_desc is not None and doc_desc.text:
                    bf_entry["documentation"] = doc_desc.text

            if bf_entry:
                self.data["registers"].append(bf_entry)

    def _parse_csv(self) -> Dict[str, Any]:
        """Parse CSV register table."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Normalize column names (handle variations)
                fieldnames = reader.fieldnames
                if not fieldnames:
                    return self.data

                for row in reader:
                    reg_entry = self._parse_csv_row(row)
                    if reg_entry:
                        self.data["registers"].append(reg_entry)

            return self.data

        except Exception as e:
            print(f"Error parsing CSV: {e}", file=sys.stderr)
            return self.data

    def _parse_csv_row(self, row: Dict[str, str]) -> Optional[Dict]:
        """Parse a single CSV row into register entry."""
        reg = {}

        # Map common column names
        column_mapping = {
            'register name': 'register',
            'register_name': 'register',
            'reg name': 'register',
            'register address': 'address',
            'register_address': 'address',
            'reg addr': 'address',
            'address': 'address',
            'bit field name': 'name',
            'bit_field_name': 'name',
            'field name': 'name',
            'name': 'name',
            'bit position': 'position',
            'bit_position': 'position',
            'position': 'position',
            'bit width': 'width',
            'bit_width': 'width',
            'width': 'width',
            'access': 'access',
            'default value': 'reset_value',
            'default_value': 'reset_value',
            'reset': 'reset_value',
            'description': 'description',
            'documentation': 'documentation',
        }

        # Process each column
        for col_name, col_value in row.items():
            if not col_value or col_value.strip() == '':
                continue

            col_key = col_name.lower().strip()
            mapped_key = column_mapping.get(col_key, col_key)

            # Clean up Verilog-style values
            if mapped_key in ['address', 'position', 'width']:
                col_value = col_value.strip("'").replace("d", "").replace("b", "0b")
                if mapped_key == 'address' and not col_value.startswith('0x'):
                    try:
                        col_value = hex(int(col_value, 0))
                    except:
                        pass

            reg[mapped_key] = col_value.strip()

        return reg if reg else None

    def _parse_yaml(self) -> Dict[str, Any]:
        """Parse YAML register definition."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)

            if not yaml_data:
                return self.data

            # Extract device info
            if 'device' in yaml_data:
                if isinstance(yaml_data['device'], dict):
                    self.data["device_name"] = yaml_data['device'].get('name')
                    self.data["manufacturer"] = yaml_data['device'].get('manufacturer')
                else:
                    self.data["device_name"] = str(yaml_data['device'])

            # Extract registers
            if 'registers' in yaml_data:
                for reg_data in yaml_data['registers']:
                    if isinstance(reg_data, dict):
                        self.data["registers"].append(reg_data)

            # Extract other fields
            for key in ['features', 'interfaces', 'pins']:
                if key in yaml_data:
                    self.data[key] = yaml_data[key]

            if 'electrical_specs' in yaml_data:
                self.data["electrical_specs"] = yaml_data['electrical_specs']

            return self.data

        except Exception as e:
            print(f"Error parsing YAML: {e}", file=sys.stderr)
            return self.data

    # PDF parsing methods (from original datasheet_parser.py)
    def _extract_pdf_metadata(self):
        """Extract device name and manufacturer from PDF."""
        try:
            import pdfplumber
            with pdfplumber.open(self.file_path) as pdf:
                first_pages = ""
                for i in range(min(3, len(pdf.pages))):
                    first_pages += pdf.pages[i].extract_text() + "\n"

                # Device name patterns
                device_patterns = [
                    r'(MAX\d+[A-Z]?)',
                    r'(AD\d+[A-Z]?)',
                    r'(LT[CP]?\d+[A-Z]?)',
                ]

                for pattern in device_patterns:
                    match = re.search(pattern, first_pages)
                    if match:
                        self.data["device_name"] = match.group(1)
                        break

                # Manufacturer
                if "Analog Devices" in first_pages:
                    self.data["manufacturer"] = "Analog Devices"
                elif "Maxim" in first_pages:
                    self.data["manufacturer"] = "Maxim Integrated"

        except Exception as e:
            print(f"Warning: Could not extract PDF metadata: {e}", file=sys.stderr)

    def _extract_pdf_text(self):
        """Extract all text from PDF."""
        try:
            import pdfplumber
            with pdfplumber.open(self.file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n\n"
                self.data["metadata"]["raw_text"] = text
        except Exception as e:
            print(f"Warning: Could not extract PDF text: {e}", file=sys.stderr)

    def _extract_pdf_features(self):
        """Extract features from PDF."""
        text = self.data.get("metadata", {}).get("raw_text", "")
        features_section = re.search(
            r'(FEATURES?|BENEFITS?).*?(?=\n\n[A-Z]|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        if features_section:
            features = re.findall(r'[•●■▪]\s*(.+?)(?=\n[•●■▪]|\n\n|\Z)', features_section.group(0), re.DOTALL)
            self.data["features"] = [f.strip() for f in features if f.strip()]

    def _extract_pdf_registers(self):
        """Extract register tables from PDF."""
        # Use tabula for table extraction
        try:
            import tabula
            tables = tabula.read_pdf(str(self.file_path), pages='all', multiple_tables=True, guess=True)
            # Process tables...
        except:
            pass

    def _extract_pdf_pins(self):
        """Extract pin tables from PDF."""
        pass  # Similar to registers

    def _extract_pdf_electrical_specs(self):
        """Extract electrical specs from PDF."""
        pass

    def _extract_pdf_interfaces(self):
        """Extract interfaces from PDF."""
        text = self.data.get("metadata", {}).get("raw_text", "")
        interfaces = []
        if re.search(r'\bSPI\b', text, re.IGNORECASE):
            interfaces.append("SPI")
        if re.search(r'\bI2C\b', text, re.IGNORECASE):
            interfaces.append("I2C")
        if re.search(r'\bUART\b', text, re.IGNORECASE):
            interfaces.append("UART")
        self.data["interfaces"] = interfaces


def main():
    parser = argparse.ArgumentParser(description='Parse hardware specifications from various formats')
    parser.add_argument('file_path', help='Path to specification file (PDF, XML, CSV, YAML)')
    parser.add_argument('--output', '-o', help='Output JSON file', default=None)
    parser.add_argument('--format', '-f', choices=['auto', 'pdf', 'xml', 'csv', 'yaml'],
                       default='auto', help='File format (default: auto-detect)')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON')

    args = parser.parse_args()

    try:
        spec_parser = HardwareSpecParser(args.file_path, args.format)
        result = spec_parser.parse()

        indent = 2 if args.pretty else None
        output_json = json.dumps(result, indent=indent)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
            print(f"Results written to {args.output}", file=sys.stderr)
        else:
            print(output_json)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        import pandas as pd
    except ImportError:
        pass  # Only needed for PDF parsing

    main()
