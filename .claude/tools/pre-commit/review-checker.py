#!/usr/bin/env python3
"""
no-OS Automated Review Checker

Analyzes code for common review issues found in comprehensive PR pattern analysis.
Based on 6-month analysis of 144 merged PRs with 507 review comments (Aug 2025 - Feb 2026).

Top issues this prevents (updated priorities):
1. Error Handling (107 occurrences, 21.1% of issues)
2. Documentation (62 occurrences, 12.2% of issues)
3. Type Safety (31 occurrences, 6.1% of issues)
4. Header Guards/Includes (24 occurrences, 4.7% of issues)
5. Testing Issues (22 occurrences, 4.3% of issues)
6. Code Organization (21 occurrences, 4.1% of issues)
7. Constants/Magic Numbers (12 occurrences, 2.4% of issues)
8. Naming Conventions (9 occurrences, 1.8% of issues)

Enhanced features:
- Unused Headers Detection: Identifies potentially unused #include statements
- Unused Variables Detection: Finds declared but unused local variables
- Bit Operations: Suggests NO_OS_BIT/NO_OS_GENMASK usage for better code style

Automation Coverage: 62.5% of review issues prevented before PR submission.
"""

import re
import sys
import os
from typing import List, Dict, NamedTuple
from enum import Enum


class IssueLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Issue(NamedTuple):
    file_path: str
    line_number: int
    level: IssueLevel
    category: str
    message: str
    suggestion: str = ""


class ReviewChecker:
    def __init__(self):
        self.issues: List[Issue] = []

        # Common no-OS patterns
        self.device_prefixes = [
            'ad', 'adm', 'adf', 'adt', 'ltc', 'max', 'lt', 'cn'
        ]

        # Magic numbers that are usually OK
        self.allowed_magic_numbers = {
            '0', '1', '2', '8', '16', '32', '64', '100', '1000',
            '0x00', '0x01', '0xFF', '0x80'
        }

    def analyze_file(self, file_path: str) -> List[Issue]:
        """Analyze a single file for review issues."""
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return [Issue(file_path, 0, IssueLevel.ERROR, "File Access", f"Could not read file: {e}")]

        file_issues = []

        if file_path.endswith('.h'):
            file_issues.extend(self._check_header_file(file_path, lines, content))
        elif file_path.endswith('.c'):
            file_issues.extend(self._check_source_file(file_path, lines, content))

        # Common checks for both .c and .h files
        file_issues.extend(self._check_error_handling(file_path, lines))
        file_issues.extend(self._check_documentation(file_path, lines))
        file_issues.extend(self._check_magic_numbers(file_path, lines))
        file_issues.extend(self._check_type_safety(file_path, lines))
        file_issues.extend(self._check_naming_conventions(file_path, lines))
        file_issues.extend(self._check_bit_operations(file_path, lines))
        file_issues.extend(self._check_unused_headers(file_path, lines, content))
        file_issues.extend(self._check_unused_variables(file_path, lines))

        return file_issues

    def _check_header_file(self, file_path: str, lines: List[str], content: str) -> List[Issue]:
        """Check header file specific issues."""
        issues = []

        # Check header guard format
        filename = os.path.basename(file_path)
        expected_guard = f"__{filename.upper().replace('.', '_').replace('-', '_')}__"

        has_ifndef = any(f"#ifndef {expected_guard}" in line for line in lines[:10])
        has_define = any(f"#define {expected_guard}" in line for line in lines[:10])

        if not has_ifndef or not has_define:
            suggested_guard = expected_guard
            issues.append(Issue(
                file_path, 1, IssueLevel.WARNING, "Header Guards",
                f"Header guard format may be incorrect",
                f"Expected: #ifndef {suggested_guard} / #define {suggested_guard}"
            ))

        # Check for missing includes
        if 'struct no_os_spi_desc' in content and '#include "no_os_spi.h"' not in content:
            issues.append(Issue(
                file_path, 1, IssueLevel.WARNING, "Missing Includes",
                "Uses SPI structures but doesn't include no_os_spi.h",
                "Add: #include \"no_os_spi.h\""
            ))

        if 'struct no_os_gpio_desc' in content and '#include "no_os_gpio.h"' not in content:
            issues.append(Issue(
                file_path, 1, IssueLevel.WARNING, "Missing Includes",
                "Uses GPIO structures but doesn't include no_os_gpio.h",
                "Add: #include \"no_os_gpio.h\""
            ))

        return issues

    def _check_source_file(self, file_path: str, lines: List[str], content: str) -> List[Issue]:
        """Check source file specific issues."""
        issues = []

        # Check for missing includes
        if 'no_os_calloc' in content and '#include "no_os_alloc.h"' not in content:
            issues.append(Issue(
                file_path, 1, IssueLevel.WARNING, "Missing Includes",
                "Uses no_os_calloc but doesn't include no_os_alloc.h",
                "Add: #include \"no_os_alloc.h\""
            ))

        if 'no_os_mdelay' in content and '#include "no_os_delay.h"' not in content:
            issues.append(Issue(
                file_path, 1, IssueLevel.WARNING, "Missing Includes",
                "Uses no_os_mdelay but doesn't include no_os_delay.h",
                "Add: #include \"no_os_delay.h\""
            ))

        return issues

    def _check_error_handling(self, file_path: str, lines: List[str]) -> List[Issue]:
        """Check for error handling issues (most common: 30 occurrences)."""
        issues = []

        for i, line in enumerate(lines, 1):
            # Check for function calls without return value checking
            if re.search(r'no_os_\w+\([^)]*\);', line) and not re.search(r'(ret|result|status)\s*=', line):
                # Skip obvious cases that don't need checking
                if not any(skip in line for skip in ['no_os_mdelay', 'no_os_udelay', 'no_os_free']):
                    issues.append(Issue(
                        file_path, i, IssueLevel.WARNING, "Error Handling",
                        "no-OS function call without return value check",
                        "Consider: ret = no_os_function(); if (ret < 0) return ret;"
                    ))

            # Check for missing null pointer checks
            if re.search(r'->\w+', line) and not any(check in line for check in ['if', '&&', '||', '?']):
                # Look for obvious pointer dereferences without null checks
                if re.search(r'\b\w+->(?:spi_desc|gpio_\w+|i2c_desc)', line):
                    # Check if there's a null check in the previous few lines
                    prev_lines = lines[max(0, i-5):i]
                    has_null_check = any(re.search(r'if\s*\(.*!\w+', prev_line) for prev_line in prev_lines)
                    if not has_null_check:
                        issues.append(Issue(
                            file_path, i, IssueLevel.WARNING, "Error Handling",
                            "Potential null pointer dereference",
                            "Add null check: if (!dev || !dev->spi_desc) return -EINVAL;"
                        ))

        return issues

    def _check_documentation(self, file_path: str, lines: List[str]) -> List[Issue]:
        """Check documentation issues (2nd most common: 18 occurrences)."""
        issues = []

        in_function = False
        has_doxygen = False

        for i, line in enumerate(lines, 1):
            # Check for function definitions
            if re.match(r'^int\d*_t\s+\w+.*\(', line) or re.match(r'^void\s+\w+.*\(', line):
                if file_path.endswith('.h'):  # Only check public functions in headers
                    if not has_doxygen:
                        issues.append(Issue(
                            file_path, i, IssueLevel.WARNING, "Documentation",
                            "Public function missing Doxygen documentation",
                            "Add: /** @brief ... */ comment block before function"
                        ))
                has_doxygen = False

            # Check for Doxygen comment blocks
            if '@brief' in line or '@param' in line or '@return' in line:
                has_doxygen = True

            # Check for incomplete Doxygen
            if '@brief' in line and line.strip().endswith('@brief'):
                issues.append(Issue(
                    file_path, i, IssueLevel.INFO, "Documentation",
                    "Incomplete @brief description",
                    "Add meaningful description after @brief"
                ))

        return issues

    def _check_magic_numbers(self, file_path: str, lines: List[str]) -> List[Issue]:
        """Check for magic numbers (9 occurrences in analysis)."""
        issues = []

        for i, line in enumerate(lines, 1):
            # Skip comments and strings
            if '//' in line or '/*' in line or '"' in line:
                continue

            # Find numeric literals
            numbers = re.findall(r'\b(\d+|0x[0-9A-Fa-f]+)\b', line)

            for number in numbers:
                if number not in self.allowed_magic_numbers:
                    # Skip if it's already in a #define
                    if '#define' in line:
                        continue

                    # Skip if it's in array bounds or bit shifts
                    if re.search(rf'\[.*{re.escape(number)}.*\]|<<\s*{re.escape(number)}|>>\s*{re.escape(number)}', line):
                        continue

                    # Check for delay values
                    if 'delay' in line.lower() and int(number, 0 if not number.startswith('0x') else 16) > 10:
                        issues.append(Issue(
                            file_path, i, IssueLevel.INFO, "Magic Numbers",
                            f"Consider defining delay constant: {number}",
                            f"#define DEVICE_RESET_DELAY_MS {number}"
                        ))

                    # Check for large numbers that might be register addresses/values
                    try:
                        num_val = int(number, 0 if not number.startswith('0x') else 16)
                        if num_val > 255 and 'define' not in line.lower():
                            issues.append(Issue(
                                file_path, i, IssueLevel.INFO, "Magic Numbers",
                                f"Large number might need a constant: {number}",
                                f"Consider: #define DEVICE_REG_VALUE {number}"
                            ))
                    except ValueError:
                        pass

        return issues

    def _check_type_safety(self, file_path: str, lines: List[str]) -> List[Issue]:
        """Check type safety issues (5 occurrences in analysis)."""
        issues = []

        for i, line in enumerate(lines, 1):
            # Check for potentially unsafe casts
            unsafe_casts = re.findall(r'\(\s*(uint\d+_t|int\d+_t)\s*\*\s*\)', line)
            if unsafe_casts:
                issues.append(Issue(
                    file_path, i, IssueLevel.WARNING, "Type Safety",
                    "Potentially unsafe pointer cast",
                    "Consider using no_os_get_unaligned_*() functions for safe access"
                ))

            # Check for mixing signed/unsigned in comparisons
            if re.search(r'if\s*\([^)]*[<>]=?\s*sizeof', line) and 'int' in line:
                issues.append(Issue(
                    file_path, i, IssueLevel.WARNING, "Type Safety",
                    "Comparing signed value with sizeof (unsigned)",
                    "Use unsigned types for size comparisons"
                ))

        return issues

    def _check_naming_conventions(self, file_path: str, lines: List[str]) -> List[Issue]:
        """Check naming convention issues (6 occurrences in analysis)."""
        issues = []

        device_name = self._extract_device_name(file_path)

        for i, line in enumerate(lines, 1):
            # Check #define naming
            define_match = re.match(r'#define\s+(\w+)', line)
            if define_match:
                define_name = define_match.group(1)

                # Should start with device name prefix
                if device_name and not define_name.startswith(device_name.upper()):
                    # Skip common exceptions
                    if not define_name.startswith(('__', 'NO_OS_', 'BIT', 'GENMASK')):
                        issues.append(Issue(
                            file_path, i, IssueLevel.INFO, "Naming Convention",
                            f"Macro doesn't follow device prefix convention",
                            f"Consider: {device_name.upper()}_{define_name}"
                        ))

                # Check for non-descriptive names
                if re.match(r'.*_(REG|REGISTER)\d+$', define_name):
                    issues.append(Issue(
                        file_path, i, IssueLevel.INFO, "Naming Convention",
                        "Non-descriptive register name",
                        "Use descriptive names: DEVICE_REG_STATUS instead of DEVICE_REG1"
                    ))

            # Check function naming
            func_match = re.match(r'^\w+\s+(\w+)\s*\(', line)
            if func_match and file_path.endswith('.h'):
                func_name = func_match.group(1)

                # Should start with device name prefix
                if device_name and not func_name.startswith(device_name.lower()):
                    # Skip constructors and common exceptions
                    if not func_name.startswith(('no_os_', 'main', 'init')):
                        issues.append(Issue(
                            file_path, i, IssueLevel.INFO, "Naming Convention",
                            f"Function doesn't follow device prefix convention",
                            f"Consider: {device_name.lower()}_{func_name}"
                        ))

        return issues

    def _check_bit_operations(self, file_path: str, lines: List[str]) -> List[Issue]:
        """Check for bit operations that should use no-OS macros."""
        issues = []

        for i, line in enumerate(lines, 1):
            # Skip comments and strings
            if '//' in line or '/*' in line or '"' in line:
                continue

            # Check for (1 << n) that should be NO_OS_BIT(n)
            bit_shift_match = re.search(r'\(1\s*<<\s*(\d+)\)', line)
            if bit_shift_match:
                bit_num = bit_shift_match.group(1)
                issues.append(Issue(
                    file_path, i, IssueLevel.INFO, "Bit Operations",
                    f"Use NO_OS_BIT({bit_num}) instead of (1 << {bit_num})",
                    f"Replace with: NO_OS_BIT({bit_num})"
                ))

            # Check for manual bit field creation that should use NO_OS_GENMASK
            # Pattern: ((1 << n) - 1) << m  or similar constructs
            genmask_patterns = [
                r'\(\(1\s*<<\s*\d+\)\s*-\s*1\)\s*<<\s*\d+',  # ((1 << n) - 1) << m
                r'0x[fF]+\s*<<\s*\d+',  # 0xFF << n type patterns
            ]

            for pattern in genmask_patterns:
                if re.search(pattern, line):
                    issues.append(Issue(
                        file_path, i, IssueLevel.INFO, "Bit Operations",
                        "Consider using NO_OS_GENMASK for bit field masks",
                        "Use: NO_OS_GENMASK(high_bit, low_bit) for multi-bit fields"
                    ))

            # Check for manual field operations that should use no_os_field_prep/no_os_field_get
            # Pattern: (value << shift) & mask or (reg & mask) >> shift
            field_prep_pattern = r'\(\s*\w+\s*<<\s*\d+\s*\)\s*&\s*\w+'
            field_get_pattern = r'\(\s*\w+\s*&\s*\w+\s*\)\s*>>\s*\d+'

            if re.search(field_prep_pattern, line):
                issues.append(Issue(
                    file_path, i, IssueLevel.INFO, "Bit Operations",
                    "Consider using no_os_field_prep() for field preparation",
                    "Use: no_os_field_prep(MASK, value)"
                ))

            if re.search(field_get_pattern, line):
                issues.append(Issue(
                    file_path, i, IssueLevel.INFO, "Bit Operations",
                    "Consider using no_os_field_get() for field extraction",
                    "Use: no_os_field_get(MASK, reg_value)"
                ))

            # Check for hardcoded masks that should be defined with NO_OS_GENMASK
            if '#define' in line:
                # Look for masks like 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF patterns
                mask_match = re.search(r'#define\s+(\w+)\s+(0x[0-9A-Fa-f]+)', line)
                if mask_match:
                    mask_name = mask_match.group(1)
                    mask_value = mask_match.group(2)

                    # Convert hex to int to check if it's a continuous bit field
                    try:
                        mask_int = int(mask_value, 16)
                        # Check if it's a continuous bit field (e.g., 0x07 = bits 0-2, 0x3F = bits 0-5)
                        if mask_int > 0 and (mask_int & (mask_int + 1)) == 0:
                            # It's a continuous bit field from bit 0
                            high_bit = mask_int.bit_length() - 1
                            if high_bit > 0 and '_MSK' in mask_name:
                                issues.append(Issue(
                                    file_path, i, IssueLevel.INFO, "Bit Operations",
                                    f"Consider using NO_OS_GENMASK({high_bit}, 0) for mask definition",
                                    f"#define {mask_name} NO_OS_GENMASK({high_bit}, 0)"
                                ))
                    except ValueError:
                        pass

            # Check for missing NO_OS_BIT usage in bit definitions
            if '#define' in line and re.search(r'#define\s+\w+\s+0x[0-9A-Fa-f]+', line):
                define_match = re.search(r'#define\s+(\w+)\s+(0x[0-9A-Fa-f]+)', line)
                if define_match:
                    define_name = define_match.group(1)
                    define_value = define_match.group(2)

                    try:
                        value_int = int(define_value, 16)
                        # Check if it's a single bit (power of 2)
                        if value_int > 0 and (value_int & (value_int - 1)) == 0:
                            bit_pos = value_int.bit_length() - 1
                            if 'BIT' in define_name or 'MSK' in define_name:
                                issues.append(Issue(
                                    file_path, i, IssueLevel.INFO, "Bit Operations",
                                    f"Consider using NO_OS_BIT({bit_pos}) for single bit definition",
                                    f"#define {define_name} NO_OS_BIT({bit_pos})"
                                ))
                    except ValueError:
                        pass

        return issues

    def _check_unused_headers(self, file_path: str, lines: List[str], content: str) -> List[Issue]:
        """Check for potentially unused header includes."""
        issues = []

        # Extract all #include statements
        include_lines = []
        for i, line in enumerate(lines, 1):
            include_match = re.match(r'#include\s+[<"]([^>"]+)[>"]', line.strip())
            if include_match:
                header_name = include_match.group(1)
                include_lines.append((i, header_name, line.strip()))

        # Known headers that are often needed but may not have obvious usage
        system_headers = {
            'stdint.h', 'stdbool.h', 'stddef.h', 'stdlib.h', 'string.h',
            'stdio.h', 'errno.h', 'assert.h'
        }

        # Headers that provide only macros or typedefs (harder to detect usage)
        macro_headers = {
            'no_os_error.h', 'no_os_util.h', 'no_os_units.h'
        }

        for line_num, header_name, include_line in include_lines:
            # Skip system headers and macro-only headers for now
            if any(sys_header in header_name for sys_header in system_headers):
                continue
            if any(macro_header in header_name for macro_header in macro_headers):
                continue

            # Skip the device's own header in source files
            if file_path.endswith('.c'):
                base_name = os.path.basename(file_path).replace('.c', '.h')
                if header_name.endswith(base_name):
                    continue

            # Check if header appears to be used in the file
            header_base = os.path.basename(header_name).replace('.h', '')

            # Look for common usage patterns
            usage_patterns = [
                # Function calls with header prefix
                rf'\b{re.escape(header_base)}_\w+\(',
                # Structure types with header prefix
                rf'\b{re.escape(header_base)}_\w+\s+\w+',
                rf'\bstruct\s+{re.escape(header_base)}_\w+',
                # Constants/macros with header prefix (uppercase)
                rf'\b{re.escape(header_base.upper())}_\w+',
                # no-OS specific patterns
                rf'no_os_{re.escape(header_base.replace("no_os_", ""))}_\w+',
            ]

            # Special patterns for common no-OS headers
            special_patterns = {
                'no_os_spi.h': [r'\bno_os_spi_\w+', r'\bstruct\s+no_os_spi_\w+', r'\bNO_OS_SPI_\w+'],
                'no_os_i2c.h': [r'\bno_os_i2c_\w+', r'\bstruct\s+no_os_i2c_\w+', r'\bNO_OS_I2C_\w+'],
                'no_os_gpio.h': [r'\bno_os_gpio_\w+', r'\bstruct\s+no_os_gpio_\w+', r'\bNO_OS_GPIO_\w+'],
                'no_os_uart.h': [r'\bno_os_uart_\w+', r'\bstruct\s+no_os_uart_\w+', r'\bNO_OS_UART_\w+'],
                'no_os_delay.h': [r'\bno_os_[mu]?delay', r'\bNO_OS_.*DELAY'],
                'no_os_alloc.h': [r'\bno_os_calloc', r'\bno_os_malloc', r'\bno_os_free'],
                'no_os_print_log.h': [r'\bpr_(info|err|warn|debug)', r'\bno_os_printf'],
                'iio.h': [r'\biio_\w+', r'\bstruct\s+iio_\w+'],
                'iio_app.h': [r'\biio_app_\w+', r'\bstruct\s+iio_app_\w+'],
            }

            # Use special patterns if available, otherwise use general patterns
            if header_name in special_patterns:
                patterns = special_patterns[header_name]
            else:
                patterns = usage_patterns

            # Check if any pattern is found in the content
            is_used = any(re.search(pattern, content, re.MULTILINE) for pattern in patterns)

            if not is_used:
                # Additional check: look for any identifier that might come from this header
                # This is a more lenient check for headers we might have missed
                header_words = header_base.replace('_', '').lower()
                if len(header_words) > 3:  # Only for reasonably long header names
                    if header_words in content.lower():
                        is_used = True

                if not is_used:
                    issues.append(Issue(
                        file_path, line_num, IssueLevel.INFO, "Unused Headers",
                        f"Header '{header_name}' may be unused",
                        "Remove unused includes to reduce compilation time and dependencies"
                    ))

        return issues

    def _check_unused_variables(self, file_path: str, lines: List[str]) -> List[Issue]:
        """Check for potentially unused variables."""
        issues = []

        # Only check source files for unused variables
        if not file_path.endswith('.c'):
            return issues

        # Track variable declarations and usage
        declared_vars = {}  # line_num: (var_name, var_type)
        used_vars = set()

        for i, line in enumerate(lines, 1):
            # Skip comments, strings, and preprocessor directives
            if re.match(r'^\s*(//|/\*|\*|#)', line):
                continue

            # Look for variable declarations
            # Pattern for local variable declarations
            var_decl_patterns = [
                r'^\s*(uint\d+_t|int\d+_t|bool|float|double|char)\s+(\w+)\s*[=;]',
                r'^\s*(struct\s+\w+)\s+(\w+)\s*[=;]',
                r'^\s*(enum\s+\w+)\s+(\w+)\s*[=;]',
            ]

            for pattern in var_decl_patterns:
                match = re.search(pattern, line)
                if match:
                    var_type = match.group(1)
                    var_name = match.group(2)

                    # Skip common variable names that are often intentionally unused
                    if var_name in ['ret', 'status', 'result', 'i', 'j', 'k', 'argc', 'argv']:
                        continue

                    # Skip function parameters (simple heuristic)
                    if ')' in line and '(' in line:
                        continue

                    # Skip variables in function signatures
                    if any(keyword in line for keyword in ['static', 'extern', 'typedef']):
                        continue

                    declared_vars[i] = (var_name, var_type)

            # Track variable usage
            for line_num, (var_name, var_type) in declared_vars.items():
                if line_num != i:  # Don't count declaration line
                    # Look for variable usage patterns
                    usage_patterns = [
                        rf'\b{re.escape(var_name)}\b(?!\s*[=])',  # Used but not assigned
                        rf'\b{re.escape(var_name)}\s*[.>]',       # Member access
                        rf'[(&]\s*{re.escape(var_name)}\b',       # Address taken or function call
                        rf'\b{re.escape(var_name)}\s*\[',         # Array access
                    ]

                    if any(re.search(pattern, line) for pattern in usage_patterns):
                        used_vars.add(var_name)

        # Report unused variables
        for line_num, (var_name, var_type) in declared_vars.items():
            if var_name not in used_vars:
                # Additional check: make sure it's not used in a later assignment or initialization
                var_line = lines[line_num - 1]

                # Skip if variable is initialized (might be intentionally unused)
                if '=' in var_line and var_name in var_line:
                    continue

                # Skip if it's a macro or used in sizeof
                remaining_content = '\n'.join(lines[line_num:])
                if re.search(rf'\bsizeof\s*\(\s*{re.escape(var_name)}\s*\)', remaining_content):
                    continue

                issues.append(Issue(
                    file_path, line_num, IssueLevel.INFO, "Unused Variables",
                    f"Variable '{var_name}' may be unused",
                    "Remove unused variables or add '(void)var_name;' if intentionally unused"
                ))

        return issues

    def _extract_device_name(self, file_path: str) -> str:
        """Extract device name from file path."""
        filename = os.path.basename(file_path)
        name = filename.split('.')[0]

        # Check if it matches known device patterns
        for prefix in self.device_prefixes:
            if name.startswith(prefix):
                return name

        return ""

    def print_issues(self):
        """Print all found issues in a readable format."""
        if not self.issues:
            print("✅ No issues found!")
            return

        # Group issues by category
        by_category = {}
        for issue in self.issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)

        print(f"🔍 Found {len(self.issues)} potential issues:")
        print()

        for category, issues in by_category.items():
            print(f"📋 {category} ({len(issues)} issues):")
            for issue in issues:
                icon = "❌" if issue.level == IssueLevel.ERROR else "⚠️" if issue.level == IssueLevel.WARNING else "💡"
                print(f"  {icon} {os.path.basename(issue.file_path)}:{issue.line_number} - {issue.message}")
                if issue.suggestion:
                    print(f"      💡 {issue.suggestion}")
            print()

    def get_error_count(self) -> int:
        """Get number of error-level issues."""
        return sum(1 for issue in self.issues if issue.level == IssueLevel.ERROR)


def main():
    if len(sys.argv) < 2:
        print("Usage: review-checker.py <file1> [file2] ...")
        sys.exit(1)

    checker = ReviewChecker()

    for file_path in sys.argv[1:]:
        if not file_path.endswith(('.c', '.h')):
            continue

        file_issues = checker.analyze_file(file_path)
        checker.issues.extend(file_issues)

    checker.print_issues()

    # Exit with error code if there are any error-level issues
    error_count = checker.get_error_count()
    if error_count > 0:
        print(f"❌ {error_count} error(s) found - please fix before proceeding")
        sys.exit(1)
    else:
        print("✅ No critical errors found")
        sys.exit(0)


if __name__ == "__main__":
    main()