# Pre-Commit Checks and CI/CD Integration

Guide to automating code quality checks using git hooks and CI/CD pipelines.

## Git Hook Setup

Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh

# Check patch with checkpatch.pl
echo "Running checkpatch..."
git diff --cached | ./scripts/checkpatch.pl --no-tree -
if [ $? -ne 0 ]; then
	echo "Checkpatch failed. Fix errors before committing."
	exit 1
fi

# Optional: Run sparse on modified C files
echo "Running sparse..."
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.c$'); do
	make C=1 "${file%.c}.o" 2>&1 | grep -i warning
done

exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## CI/CD Integration

### GitHub Actions

`.github/workflows/checkpatch.yml`:

```yaml
name: Kernel Code Quality

on: [pull_request, push]

jobs:
  checkpatch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Install dependencies
        run: |
          sudo apt update
          sudo apt install -y sparse coccinelle

      - name: Run checkpatch
        run: |
          git diff origin/main...HEAD | ./scripts/checkpatch.pl - || true

      - name: Build with sparse
        run: |
          make C=2 W=1 allmodconfig
          make C=2 W=1 || true

      - name: Run coccicheck
        run: |
          make coccicheck MODE=report || true
```
