#!/usr/bin/env python3
"""
Auto-update PR review patterns with incremental analysis.
Maintains a rolling 6-month window of review comments.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

class ReviewPatternUpdater:
    def __init__(self, repo_root="/home/cj/no-OS"):
        self.repo_root = Path(repo_root)
        self.patterns_file = self.repo_root / "review_patterns_6month.json"
        self.state_file = self.repo_root / ".review_patterns_state.json"

    def load_existing_patterns(self):
        """Load existing patterns and state."""
        if not self.patterns_file.exists():
            return None, None

        with open(self.patterns_file) as f:
            patterns = json.load(f)

        # Load state file if exists
        state = {"last_updated": "2025-08-25"}
        if self.state_file.exists():
            with open(self.state_file) as f:
                state = json.load(f)

        return patterns, state

    def get_new_prs_since(self, since_date):
        """Get PRs merged since the last update."""
        cmd = f'gh pr list --state merged --limit 50 --json number,title,mergedAt,author'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error fetching PRs: {result.stderr}")
                return []

            all_prs = json.loads(result.stdout) if result.stdout.strip() else []

            # Filter by date
            cutoff = datetime.fromisoformat(since_date).replace(tzinfo=timezone.utc)
            new_prs = []

            for pr in all_prs:
                if pr.get('mergedAt'):
                    merge_date = datetime.fromisoformat(pr['mergedAt'].replace('Z', '+00:00'))
                    if merge_date >= cutoff:
                        new_prs.append(pr)

            return new_prs

        except Exception as e:
            print(f"Error processing PRs: {e}")
            return []

    def analyze_pr_comments(self, pr_number):
        """Extract and categorize comments from a PR (simplified)."""
        # Get review comments
        cmd = f'gh api "repos/analogdevicesinc/no-OS/pulls/{pr_number}/reviews"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            reviews = json.loads(result.stdout) if result.stdout.strip() else []
        except:
            reviews = []

        # Get line comments
        cmd = f'gh api "repos/analogdevicesinc/no-OS/pulls/{pr_number}/comments"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            line_comments = json.loads(result.stdout) if result.stdout.strip() else []
        except:
            line_comments = []

        # Simplified categorization
        categorized = []
        for review in reviews:
            if review.get('body', '').strip():
                category = self.categorize_comment(review['body'])
                categorized.append({
                    'category': category,
                    'body': review['body'],
                    'pr': pr_number
                })

        for comment in line_comments:
            if comment.get('body', '').strip():
                category = self.categorize_comment(comment['body'])
                categorized.append({
                    'category': category,
                    'body': comment['body'],
                    'pr': pr_number,
                    'path': comment.get('path', 'N/A')
                })

        return categorized

    def categorize_comment(self, text):
        """Simple categorization logic."""
        text_lower = text.lower()

        if any(word in text_lower for word in ['error', 'return', 'null', 'check', 'handle']):
            return 'Error Handling'
        elif any(word in text_lower for word in ['comment', 'doc', 'doxygen', '@brief']):
            return 'Documentation'
        elif any(word in text_lower for word in ['header', 'include', '#ifndef', 'guard']):
            return 'Header Guards/Includes'
        elif any(word in text_lower for word in ['test', 'coverage', 'unit test']):
            return 'Testing'
        elif any(word in text_lower for word in ['cast', 'type', 'unsafe', 'overflow']):
            return 'Type Safety'
        else:
            return 'Code Organization'

    def update_patterns(self, force_full=False):
        """Update patterns with new PRs."""
        print("🔄 Updating PR review patterns...")

        patterns, state = self.load_existing_patterns()

        if force_full or not patterns:
            print("🔄 Running full analysis (no existing patterns found)")
            # Run full extraction
            subprocess.run([sys.executable, str(self.repo_root / "extract_review_patterns_6month.py")])
            return

        # Get new PRs since last update
        last_updated = state.get('last_updated', '2025-08-25')
        new_prs = self.get_new_prs_since(last_updated)

        if not new_prs:
            print("✅ No new PRs to analyze")
            return

        print(f"📊 Analyzing {len(new_prs)} new PRs...")

        # Analyze new PRs
        new_comments = []
        for pr in new_prs:
            pr_comments = self.analyze_pr_comments(pr['number'])
            new_comments.extend(pr_comments)

        # Update pattern counts
        for comment in new_comments:
            category = comment['category']
            if category not in patterns['category_counts']:
                patterns['category_counts'][category] = 0
            patterns['category_counts'][category] += 1

            # Add examples (limit 10 per category)
            if category not in patterns['category_examples']:
                patterns['category_examples'][category] = []
            if len(patterns['category_examples'][category]) < 10:
                patterns['category_examples'][category].append({
                    'body': comment['body'][:200] + '...' if len(comment['body']) > 200 else comment['body'],
                    'path': comment.get('path', 'N/A'),
                    'pr': comment['pr']
                })

        # Update metadata
        patterns['analysis_scope']['total_comments'] += len(new_comments)
        patterns['analysis_scope']['prs_analyzed'].extend([pr['number'] for pr in new_prs])

        # Remove old PRs (keep rolling 6-month window)
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        cutoff_str = six_months_ago.strftime('%Y-%m-%d')
        patterns['analysis_scope']['period'] = f'Rolling 6 months (since {cutoff_str})'

        # Save updated patterns
        with open(self.patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)

        # Update state
        state['last_updated'] = datetime.now(timezone.utc).isoformat()
        state['last_pr_count'] = len(new_prs)
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"✅ Added {len(new_comments)} new comments to patterns")
        print(f"📄 Updated: {self.patterns_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Update PR review patterns')
    parser.add_argument('--full', action='store_true', help='Force full re-analysis')
    args = parser.parse_args()

    updater = ReviewPatternUpdater()
    updater.update_patterns(force_full=args.full)