#!/usr/bin/env python3
"""
Datasheet Reader Tool
=====================

Extracts comprehensive text and table content from PDF datasheets using pdfplumber.
This provides complete context that complements the specialized parser tools.

Usage:
    python datasheet_reader.py <datasheet.pdf> [options]

Examples:
    # Extract all text to JSON
    python datasheet_reader.py datasheet.pdf -o output.json
    
    # Extract all text to Markdown
    python datasheet_reader.py datasheet.pdf -o output.md --format markdown
    
    # Extract specific page range
    python datasheet_reader.py datasheet.pdf -o output.json --pages 1-10
    
    # Extract tables only
    python datasheet_reader.py datasheet.pdf -o tables.json --tables-only

Dependencies:
    pip install pdfplumber
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is not installed.")
    print("Install it with: pip install pdfplumber")
    sys.exit(1)


def parse_page_range(page_range: str, total_pages: int) -> List[int]:
    """
    Parse page range string into list of page numbers.
    
    Args:
        page_range: String like "1-10", "5,7,9", "1-5,10-15"
        total_pages: Total number of pages in document
        
    Returns:
        List of page numbers (0-indexed)
    """
    pages = set()
    
    for part in page_range.split(','):
        part = part.strip()
        if '-' in part:
            start_str, end_str = part.split('-')
            start = int(start_str.strip()) - 1  # Convert to 0-indexed
            end = int(end_str.strip())  # Keep 1-indexed for range
            pages.update(range(max(0, start), min(total_pages, end)))
        else:
            page_num = int(part.strip()) - 1  # Convert to 0-indexed
            if 0 <= page_num < total_pages:
                pages.add(page_num)
    
    return sorted(list(pages))


def extract_text_from_pdf(pdf_path: str, page_numbers: Optional[List[int]] = None) -> Dict:
    """
    Extract all text content from PDF.
    
    Args:
        pdf_path: Path to PDF file
        page_numbers: Optional list of page numbers to extract (0-indexed)
        
    Returns:
        Dictionary with extracted content
    """
    result = {
        "metadata": {},
        "pages": [],
        "full_text": ""
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        # Extract metadata
        result["metadata"] = {
            "total_pages": len(pdf.pages),
            "file_path": str(pdf_path)
        }
        
        if pdf.metadata:
            result["metadata"]["pdf_metadata"] = {
                k: str(v) if v else None 
                for k, v in pdf.metadata.items()
            }
        
        # Determine which pages to process
        pages_to_process = page_numbers if page_numbers else range(len(pdf.pages))
        
        # Extract text from each page
        all_text = []
        for page_num in pages_to_process:
            if page_num >= len(pdf.pages):
                continue
                
            page = pdf.pages[page_num]
            text = page.extract_text() or ""
            
            page_data = {
                "page_number": page_num + 1,  # 1-indexed for output
                "text": text,
                "char_count": len(text)
            }
            
            result["pages"].append(page_data)
            all_text.append(f"=== Page {page_num + 1} ===\n{text}\n")
        
        result["full_text"] = "\n".join(all_text)
    
    return result


def extract_tables_from_pdf(pdf_path: str, page_numbers: Optional[List[int]] = None) -> Dict:
    """
    Extract all tables from PDF.
    
    Args:
        pdf_path: Path to PDF file
        page_numbers: Optional list of page numbers to extract (0-indexed)
        
    Returns:
        Dictionary with extracted tables
    """
    result = {
        "metadata": {},
        "tables": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        result["metadata"] = {
            "total_pages": len(pdf.pages),
            "file_path": str(pdf_path)
        }
        
        # Determine which pages to process
        pages_to_process = page_numbers if page_numbers else range(len(pdf.pages))
        
        # Extract tables from each page
        for page_num in pages_to_process:
            if page_num >= len(pdf.pages):
                continue
                
            page = pdf.pages[page_num]
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if not table:
                    continue
                
                table_data = {
                    "page_number": page_num + 1,
                    "table_number": table_idx + 1,
                    "rows": len(table),
                    "columns": len(table[0]) if table else 0,
                    "data": table
                }
                
                result["tables"].append(table_data)
        
        result["metadata"]["total_tables"] = len(result["tables"])
    
    return result


def format_as_markdown(data: Dict, include_tables: bool = True) -> str:
    """
    Format extracted data as Markdown.
    
    Args:
        data: Extracted data dictionary
        include_tables: Whether to include table data
        
    Returns:
        Markdown formatted string
    """
    lines = []
    
    # Add metadata as front matter
    lines.append("# Datasheet Content")
    lines.append("")
    lines.append(f"**File**: {data['metadata'].get('file_path', 'Unknown')}")
    lines.append(f"**Total Pages**: {data['metadata'].get('total_pages', 'Unknown')}")
    
    if 'pdf_metadata' in data['metadata']:
        lines.append("")
        lines.append("## PDF Metadata")
        for key, value in data['metadata']['pdf_metadata'].items():
            if value:
                lines.append(f"- **{key}**: {value}")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Add page content
    if 'pages' in data:
        for page_data in data['pages']:
            lines.append(f"## Page {page_data['page_number']}")
            lines.append("")
            lines.append(page_data['text'])
            lines.append("")
            lines.append("---")
            lines.append("")
    
    # Add tables if present and requested
    if include_tables and 'tables' in data:
        lines.append("## Extracted Tables")
        lines.append("")
        
        for table_data in data['tables']:
            lines.append(f"### Table {table_data['table_number']} (Page {table_data['page_number']})")
            lines.append("")
            
            # Convert table to markdown
            table = table_data['data']
            if table:
                # Header row
                header = table[0]
                lines.append("| " + " | ".join(str(cell or "") for cell in header) + " |")
                lines.append("| " + " | ".join("---" for _ in header) + " |")
                
                # Data rows
                for row in table[1:]:
                    lines.append("| " + " | ".join(str(cell or "") for cell in row) + " |")
            
            lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract comprehensive content from PDF datasheets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all content to JSON
  python datasheet_reader.py datasheet.pdf -o output.json
  
  # Extract to Markdown
  python datasheet_reader.py datasheet.pdf -o output.md --format markdown
  
  # Extract specific pages
  python datasheet_reader.py datasheet.pdf -o output.json --pages 1-10,15,20-25
  
  # Extract tables only
  python datasheet_reader.py datasheet.pdf -o tables.json --tables-only
        """
    )
    
    parser.add_argument(
        "pdf_file",
        help="Path to PDF datasheet file"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output file path (.json or .md)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "md"],
        help="Output format (auto-detected from extension if not specified)"
    )
    
    parser.add_argument(
        "--pages",
        help="Page range to extract (e.g., '1-10', '5,7,9', '1-5,10-15')"
    )
    
    parser.add_argument(
        "--tables-only",
        action="store_true",
        help="Extract only tables, not full text"
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.suffix.lower() == '.pdf':
        print(f"Warning: File does not have .pdf extension: {pdf_path}")
    
    # Determine output format
    output_path = Path(args.output)
    if args.format:
        output_format = "markdown" if args.format == "md" else args.format
    else:
        # Auto-detect from extension
        if output_path.suffix.lower() in ['.md', '.markdown']:
            output_format = "markdown"
        else:
            output_format = "json"
    
    # Parse page range if specified
    page_numbers = None
    if args.pages:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
            page_numbers = parse_page_range(args.pages, total_pages)
            print(f"Extracting pages: {[p+1 for p in page_numbers]}")
        except Exception as e:
            print(f"Error parsing page range: {e}")
            sys.exit(1)
    
    # Extract content
    print(f"Reading PDF: {pdf_path}")
    
    try:
        if args.tables_only:
            data = extract_tables_from_pdf(str(pdf_path), page_numbers)
            print(f"Extracted {len(data['tables'])} tables from {len(page_numbers or [])} pages")
        else:
            data = extract_text_from_pdf(str(pdf_path), page_numbers)
            
            # Also extract tables and merge
            tables_data = extract_tables_from_pdf(str(pdf_path), page_numbers)
            data['tables'] = tables_data['tables']
            data['metadata']['total_tables'] = len(tables_data['tables'])
            
            print(f"Extracted content from {len(data['pages'])} pages")
            if data['tables']:
                print(f"Found {len(data['tables'])} tables")
    
    except Exception as e:
        print(f"Error extracting content: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Write output
    print(f"Writing output to: {output_path}")
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_format == "markdown":
            content = format_as_markdown(data, include_tables=not args.tables_only)
            output_path.write_text(content, encoding='utf-8')
        else:
            # JSON format
            indent = 2 if args.pretty else None
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            output_path.write_text(content, encoding='utf-8')
        
        print(f"Success! Output written to {output_path}")
        print(f"File size: {output_path.stat().st_size:,} bytes")
    
    except Exception as e:
        print(f"Error writing output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
