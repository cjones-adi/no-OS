#!/usr/bin/env python3
"""
SonarCloud Report Analyzer for no-OS

Processes SonarCloud JSON reports and integrates with local review patterns.
Helps prioritize issues and provides fix suggestions.
"""

import json
import sys
import argparse
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime


class SonarReportAnalyzer:
    def __init__(self):
        self.severity_priority = {
            'BLOCKER': 1,
            'CRITICAL': 2,
            'MAJOR': 3,
            'MINOR': 4,
            'INFO': 5
        }

        self.rule_categories = {
            # Security issues
            'security': ['squid:S2068', 'squid:S1313', 'squid:S1449', 'squid:S2245'],
            # Memory management
            'memory': ['squid:S1066', 'squid:S1119', 'squid:S1143'],
            # Error handling
            'error_handling': ['squid:S1181', 'squid:S1193', 'squid:S899'],
            # Code quality
            'code_quality': ['squid:S100', 'squid:S101', 'squid:S138', 'squid:S1151'],
            # Performance
            'performance': ['squid:S1943', 'squid:S1313'],
            # Maintainability
            'maintainability': ['squid:S1067', 'squid:S134', 'squid:S1479']
        }

    def load_report(self, report_path: str) -> Dict[str, Any]:
        """Load SonarCloud JSON report."""
        try:
            with open(report_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading report: {e}")
            return {}

    def analyze_issues(self, report: Dict[str, Any]) -> Dict[str, List]:
        """Analyze issues from SonarCloud report."""
        issues = report.get('issues', [])

        analysis = {
            'by_severity': defaultdict(list),
            'by_file': defaultdict(list),
            'by_category': defaultdict(list),
            'by_rule': defaultdict(list)
        }

        for issue in issues:
            severity = issue.get('severity', 'UNKNOWN')
            file_path = issue.get('component', '').replace('project:', '')
            rule_key = issue.get('rule', '')

            # Categorize by severity
            analysis['by_severity'][severity].append(issue)

            # Categorize by file
            analysis['by_file'][file_path].append(issue)

            # Categorize by rule
            analysis['by_rule'][rule_key].append(issue)

            # Categorize by type
            category = self.categorize_rule(rule_key)
            analysis['by_category'][category].append(issue)

        return analysis

    def categorize_rule(self, rule_key: str) -> str:
        """Categorize SonarCloud rule into no-OS review categories."""
        for category, rules in self.rule_categories.items():
            if any(rule in rule_key for rule in rules):
                return category
        return 'other'

    def get_fix_suggestions(self, issue: Dict[str, Any]) -> str:
        """Provide fix suggestions based on rule type."""
        rule_key = issue.get('rule', '')
        message = issue.get('message', '')

        # Common no-OS specific fixes
        suggestions = {
            'squid:S100': 'Use descriptive function names with device prefix (e.g., adm1275_read_voltage)',
            'squid:S101': 'Follow no-OS naming: lowercase with underscores, device prefix',
            'squid:S1066': 'Add proper null checks before pointer dereference',
            'squid:S1119': 'Use no_os_malloc/no_os_free instead of stdlib functions',
            'squid:S138': 'Split large functions into smaller, focused functions',
            'squid:S1181': 'Handle specific error codes, return appropriate no-OS error codes',
            'squid:S2068': 'Remove hardcoded credentials, use configuration parameters',
            'squid:S899': 'Use NO_OS_BIT() macro instead of (1 << n) patterns',
        }

        # Extract rule number for lookup
        for pattern, suggestion in suggestions.items():
            if pattern in rule_key:
                return suggestion

        # Generic suggestions based on message content
        if 'function' in message.lower() and 'complex' in message.lower():
            return 'Break into smaller functions following no-OS single-responsibility pattern'
        elif 'variable' in message.lower() and 'name' in message.lower():
            return 'Use descriptive variable names with device/component context'
        elif 'memory' in message.lower():
            return 'Review memory management - use no_os_alloc/no_os_free consistently'
        elif 'error' in message.lower():
            return 'Improve error handling - return specific error codes, check all return values'

        return 'Review SonarCloud documentation for this rule'

    def prioritize_issues(self, analysis: Dict[str, List]) -> List[Dict]:
        """Prioritize issues for developer action."""
        all_issues = []

        for severity, issues in analysis['by_severity'].items():
            for issue in issues:
                priority_score = self.severity_priority.get(severity, 10)

                # Boost priority for no-OS specific concerns
                rule_key = issue.get('rule', '')
                if any(cat in ['security', 'memory', 'error_handling']
                       for cat, rules in self.rule_categories.items()
                       if any(rule in rule_key for rule in rules)):
                    priority_score -= 0.5

                # Boost priority for driver files
                file_path = issue.get('component', '')
                if 'drivers/' in file_path:
                    priority_score -= 0.3

                issue['priority_score'] = priority_score
                issue['fix_suggestion'] = self.get_fix_suggestions(issue)
                all_issues.append(issue)

        # Sort by priority score
        return sorted(all_issues, key=lambda x: x['priority_score'])

    def generate_report(self, analysis: Dict[str, List], prioritized_issues: List[Dict]):
        """Generate human-readable report."""
        print("🔍 SonarCloud Analysis Report for no-OS")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Summary by severity
        print("📊 Issue Summary by Severity:")
        total_issues = 0
        for severity in ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']:
            count = len(analysis['by_severity'][severity])
            if count > 0:
                icon = '🔴' if severity in ['BLOCKER', 'CRITICAL'] else '🟡' if severity == 'MAJOR' else '🟢'
                print(f"   {icon} {severity:8} {count:3d} issues")
                total_issues += count

        print(f"\nTotal issues: {total_issues}")
        print()

        # Top problematic files
        print("📁 Files with Most Issues:")
        sorted_files = sorted(analysis['by_file'].items(),
                            key=lambda x: len(x[1]), reverse=True)
        for file_path, file_issues in sorted_files[:10]:
            if file_issues:  # Only show files with issues
                print(f"   {len(file_issues):2d} issues: {file_path}")
        print()

        # Category breakdown
        print("🏷️  Issues by Category:")
        for category, issues in analysis['by_category'].items():
            if issues:
                print(f"   {len(issues):2d} {category}")
        print()

        # Top priority issues
        print("🎯 Top Priority Issues to Fix:")
        print("-" * 60)

        high_priority = [issue for issue in prioritized_issues
                        if issue['priority_score'] <= 3][:10]

        for i, issue in enumerate(high_priority, 1):
            severity = issue.get('severity', 'UNKNOWN')
            file_path = issue.get('component', '').replace('project:', '')
            line = issue.get('line', 0)
            message = issue.get('message', '')
            rule_key = issue.get('rule', '')

            icon = '🔴' if severity in ['BLOCKER', 'CRITICAL'] else '🟡' if severity == 'MAJOR' else '🟢'

            print(f"{i:2d}. {icon} {severity} - {file_path}:{line}")
            print(f"    Rule: {rule_key}")
            print(f"    Issue: {message}")
            print(f"    Fix: {issue['fix_suggestion']}")
            print()

        # Recommendations
        print("💡 Recommendations:")
        print("-" * 60)

        if analysis['by_severity']['BLOCKER'] or analysis['by_severity']['CRITICAL']:
            print("🔴 URGENT: Address BLOCKER/CRITICAL issues before proceeding")

        if len(analysis['by_category']['security']) > 0:
            print("🔒 Security: Review all security-related findings carefully")

        if len(analysis['by_category']['memory']) > 0:
            print("🧠 Memory: Check memory management patterns, use no-OS allocators")

        if len(analysis['by_category']['error_handling']) > 0:
            print("⚠️  Errors: Improve error handling, validate all return values")

        driver_files = [f for f in analysis['by_file'].keys() if 'drivers/' in f]
        if driver_files:
            print(f"🔧 Drivers: Focus on driver code quality ({len(driver_files)} files affected)")

        print()
        print("🚀 Next Steps:")
        print("   1. Fix BLOCKER/CRITICAL issues first")
        print("   2. Address security and memory issues")
        print("   3. Improve error handling patterns")
        print("   4. Run local pre-commit checks")
        print("   5. Re-run SonarCloud analysis")

    def export_for_claude_review(self, prioritized_issues: List[Dict], output_file: str):
        """Export prioritized issues in Claude-friendly format."""
        claude_report = {
            'summary': {
                'total_issues': len(prioritized_issues),
                'high_priority': len([i for i in prioritized_issues if i['priority_score'] <= 2]),
                'medium_priority': len([i for i in prioritized_issues if 2 < i['priority_score'] <= 3]),
                'generated': datetime.now().isoformat()
            },
            'high_priority_issues': []
        }

        for issue in prioritized_issues[:20]:  # Top 20 for Claude review
            claude_issue = {
                'severity': issue.get('severity'),
                'file': issue.get('component', '').replace('project:', ''),
                'line': issue.get('line'),
                'rule': issue.get('rule'),
                'message': issue.get('message'),
                'fix_suggestion': issue['fix_suggestion'],
                'priority_score': issue['priority_score']
            }
            claude_report['high_priority_issues'].append(claude_issue)

        with open(output_file, 'w') as f:
            json.dump(claude_report, f, indent=2)

        print(f"📄 Claude review report exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze SonarCloud reports for no-OS')
    parser.add_argument('report_file', help='SonarCloud JSON report file')
    parser.add_argument('--export-claude', help='Export file for Claude review')
    parser.add_argument('--format', choices=['console', 'json'], default='console',
                       help='Output format')

    args = parser.parse_args()

    analyzer = SonarReportAnalyzer()

    # Load and analyze report
    report = analyzer.load_report(args.report_file)
    if not report:
        sys.exit(1)

    analysis = analyzer.analyze_issues(report)
    prioritized = analyzer.prioritize_issues(analysis)

    if args.format == 'console':
        analyzer.generate_report(analysis, prioritized)
    else:
        print(json.dumps({
            'analysis': dict(analysis),
            'prioritized_issues': prioritized
        }, indent=2))

    # Export for Claude if requested
    if args.export_claude:
        analyzer.export_for_claude_review(prioritized, args.export_claude)


if __name__ == '__main__':
    main()