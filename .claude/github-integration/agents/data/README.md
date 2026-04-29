# Agent Historical Data Directory

This directory stores historical data used by agents to improve code quality over time.

## Files

### `review-history.json`

Contains aggregated review findings from the past 6 months of no-OS Pull Requests. Used by `driver-code-reviewer` agent to:

- Identify common issues that appear frequently in PRs
- Prioritize review checks based on historical patterns
- Provide examples of correct patterns from past reviews
- Track whether new drivers avoid recurring problems

### Data Structure

```json
{
  "last_updated": "YYYY-MM-DD",
  "data_range": {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "months": 6
  },
  "common_issues": [
    {
      "category": "error_handling|memory_management|style|safety|documentation|testing",
      "issue": "Brief description",
      "description": "Detailed explanation of the issue",
      "severity": "critical|major|minor",
      "frequency": 23,
      "example": "Example code or comment showing correct pattern",
      "files_affected": ["List", "of", "file types"]
    }
  ],
  "pr_reviews_analyzed": 156,
  "total_issues_extracted": 342
}
```

## Refresh Schedule

- **Automatic**: Agent checks if data is older than 3 months and refreshes automatically
- **Manual**: Delete `review-history.json` to force fresh fetch on next review
- **Recommended**: Quarterly updates to capture evolving patterns

## Data Generation

The `driver-code-reviewer` agent automatically generates this data by:

1. Fetching closed/merged PRs from https://github.com/adi-innersource/no-OS/pulls
2. Filtering for PRs that modified driver code (drivers/ directory)
3. Parsing review comments to identify common issues
4. Categorizing and counting issue frequency
5. Extracting example code snippets and recommendations
6. Saving structured JSON for future reviews

## Benefits

- **Team-wide learning**: All developers benefit from institutional knowledge
- **Consistent quality**: New code avoids repeating past mistakes
- **Faster reviews**: Common issues check automatically
- **Trend tracking**: See if certain issues are increasing or decreasing

## Privacy & Security

- Only publicly available GitHub PR review comments are analyzed
- No sensitive data is stored (credentials, secrets, etc.)
- Data is committed to repository for transparency and sharing
