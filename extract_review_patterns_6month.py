#!/usr/bin/env python3
"""
Extract review patterns from 6 months of merged PRs to build a comprehensive
reference guide for common review comments and coding issues.
"""

import json
import subprocess
import sys
from collections import defaultdict
import re
from datetime import datetime, timezone

def run_gh_command(cmd):
    """Run a GitHub CLI command and return the JSON result."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running: {cmd}")
            print(f"Error: {result.stderr}")
            return None
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        print(f"Invalid JSON from: {cmd}")
        return None

def get_merged_prs_since_date(cutoff_date="2025-08-25"):
    """Get all merged PRs since the cutoff date."""
    # Get a large number initially and filter by date
    cmd = f'gh pr list --state merged --limit 200 --json number,title,mergedAt,author'
    all_prs = run_gh_command(cmd)

    if not all_prs:
        return []

    # Filter PRs by merge date
    cutoff = datetime.fromisoformat(cutoff_date).replace(tzinfo=timezone.utc)
    filtered_prs = []

    for pr in all_prs:
        if pr.get('mergedAt'):
            merge_date = datetime.fromisoformat(pr['mergedAt'].replace('Z', '+00:00'))
            if merge_date >= cutoff:
                filtered_prs.append(pr)

    print(f"Found {len(filtered_prs)} PRs merged since {cutoff_date}")
    return filtered_prs

def get_pr_review_comments(pr_number):
    """Get review comments (overall PR reviews) for a specific PR."""
    cmd = f'gh api "repos/analogdevicesinc/no-OS/pulls/{pr_number}/reviews"'
    reviews = run_gh_command(cmd)
    if not reviews:
        return []

    comments = []
    for review in reviews:
        if review.get('body', '').strip():
            comments.append({
                'type': 'review',
                'author': review['user']['login'],
                'body': review['body'],
                'state': review['state']
            })
    return comments

def get_pr_line_comments(pr_number):
    """Get line-by-line review comments for a specific PR."""
    cmd = f'gh api "repos/analogdevicesinc/no-OS/pulls/{pr_number}/comments"'
    comments = run_gh_command(cmd)
    if not comments:
        return []

    line_comments = []
    for comment in comments:
        if comment.get('body', '').strip():
            line_comments.append({
                'type': 'line_comment',
                'author': comment['user']['login'],
                'body': comment['body'],
                'path': comment.get('path', 'N/A'),
                'line': comment.get('line', 0)
            })
    return line_comments

def categorize_comment(comment_text):
    """Categorize a review comment based on its content."""
    comment_lower = comment_text.lower()

    # Define categories with key phrases
    categories = {
        'Error Handling': [
            'error', 'return', 'null', 'check', 'handle', 'validation', 'leak', 'memory',
            'free', 'malloc', 'deallocation', 'fail', 'ret !=', 'ret ==', 'if (!', 'errno'
        ],
        'Documentation': [
            'comment', 'documentation', 'doc', 'readme', 'doxygen', '@brief', '@param',
            '@return', 'document', 'explain', 'describe', 'unclear', 'missing comment'
        ],
        'Header Guards/Includes': [
            'header', 'include', 'guard', '#ifndef', '#define', '#include', 'include order',
            'missing include', 'circular include', 'header guard'
        ],
        'Constants/Magic Numbers': [
            'magic number', 'constant', 'define', '#define', 'hardcode', 'literal',
            'magic', 'hardcoded', 'define this', 'use define'
        ],
        'Naming Convention': [
            'naming', 'name', 'convention', 'prefix', 'suffix', 'rename', 'variable name',
            'function name', 'inconsistent', 'should be named', 'name should'
        ],
        'Code Style': [
            'style', 'format', 'indent', 'spacing', 'bracket', 'brace', 'astyle',
            'formatting', 'whitespace', 'line length', 'indentation'
        ],
        'Type Safety': [
            'cast', 'casting', 'type', 'overflow', 'underflow', 'uint', 'int', 'float',
            'double', 'size_t', 'pointer', 'alignment', 'type safety'
        ],
        'Performance': [
            'performance', 'optimize', 'speed', 'memory', 'leak', 'efficiency',
            'slow', 'fast', 'memory usage', 'cpu', 'optimization'
        ],
        'Security': [
            'security', 'buffer overflow', 'bounds check', 'validation', 'sanitize',
            'vulnerable', 'exploit', 'attack', 'secure', 'safety'
        ],
        'Testing': [
            'test', 'testing', 'unit test', 'integration', 'coverage', 'assert',
            'verify', 'validation', 'test case'
        ],
        'Platform Compatibility': [
            'platform', 'compatibility', 'portable', 'cross-platform', 'linux',
            'windows', 'embedded', 'architecture', 'endian'
        ],
        'Typos/Grammar': [
            'typo', 'typos', 'spelling', 'grammar', 'misspell', 'correct spelling',
            'should be', 'meant', 'fix typo'
        ],
        'Code Organization': [
            'organize', 'structure', 'refactor', 'move', 'separate', 'split',
            'organize code', 'code structure', 'architecture'
        ]
    }

    # Score each category
    category_scores = defaultdict(int)

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in comment_lower:
                category_scores[category] += 1

    # Return the category with highest score, or 'Uncategorized'
    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]
    else:
        return 'Uncategorized'

def analyze_patterns():
    """Extract and analyze review patterns from merged PRs."""
    print("🔍 Extracting review patterns from 6 months of merged PRs...")

    # Get PRs from last 6 months
    prs = get_merged_prs_since_date("2025-08-25")

    if not prs:
        print("❌ No PRs found")
        return

    print(f"📊 Analyzing {len(prs)} PRs...")

    all_comments = []
    category_counts = defaultdict(int)
    category_examples = defaultdict(list)

    # Process each PR
    for i, pr in enumerate(prs, 1):
        pr_number = pr['number']
        print(f"Processing PR #{pr_number} ({i}/{len(prs)})")

        # Get both types of comments
        review_comments = get_pr_review_comments(pr_number)
        line_comments = get_pr_line_comments(pr_number)

        # Process all comments for this PR
        pr_comments = review_comments + line_comments

        for comment in pr_comments:
            comment_text = comment['body']

            # Skip very short comments (likely not substantial)
            if len(comment_text.strip()) < 10:
                continue

            # Categorize the comment
            category = categorize_comment(comment_text)
            category_counts[category] += 1

            # Store example (limit examples per category)
            if len(category_examples[category]) < 10:
                category_examples[category].append({
                    'body': comment_text,
                    'path': comment.get('path', 'N/A'),
                    'pr': pr_number
                })

            all_comments.append({
                'pr': pr_number,
                'category': category,
                'comment': comment_text,
                'author': comment['author'],
                'path': comment.get('path', 'N/A')
            })

    # Create results
    results = {
        'analysis_scope': {
            'period': 'Last 6 months (since 2025-08-25)',
            'total_prs': len(prs),
            'total_comments': len(all_comments),
            'prs_analyzed': [pr['number'] for pr in prs]
        },
        'category_counts': dict(category_counts),
        'category_examples': {k: v for k, v in category_examples.items()}
    }

    # Save results
    output_file = 'review_patterns_6month.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Analysis complete!")
    print(f"📄 Results saved to: {output_file}")
    print(f"📊 Total PRs analyzed: {len(prs)}")
    print(f"💬 Total comments analyzed: {len(all_comments)}")
    print("\n📋 Category breakdown:")

    # Sort categories by frequency
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    total_comments = sum(category_counts.values())

    for category, count in sorted_categories:
        percentage = (count / total_comments) * 100
        print(f"  {category}: {count} ({percentage:.1f}%)")

    return results

if __name__ == "__main__":
    try:
        results = analyze_patterns()
        if results:
            print("\n🎉 6-month analysis completed successfully!")
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)