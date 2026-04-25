# Virtual Environment Setup for Zephyr Testing

## Overview

West (Zephyr's build tool) must be available before running tests. It's typically installed in a Python virtual environment.

## Checking Your Setup

```bash
# Check if .venv exists
ls -la ~/zephyrproject/.venv/

# Check if west is in virtual environment
ls -la ~/zephyrproject/.venv/bin/west

# Check if west is in PATH
which west
```

## Activating Virtual Environment

### Linux/Mac
```bash
cd ~/zephyrproject
source .venv/bin/activate

# Verify activation (should show venv path)
which west
west --version
```

### Windows
```cmd
cd %USERPROFILE%\zephyrproject
.venv\Scripts\activate

# Verify activation
where west
west --version
```

## Common Issues

### Issue: Command 'west' not found
**Symptom**:
```
$ west twister -T tests/...
Command 'west' not found, did you mean:
  command 'jest' from deb jest
  command 'test' from deb coreutils
```

**Solution**: Activate virtual environment
```bash
source .venv/bin/activate
west --version  # Should work now
```

### Issue: Tests filter to 0 configurations
**Symptom**:
```
INFO - 0 of 0 executed test configurations passed
INFO - 3959 test scenarios selected, 97859 configurations filtered
```

**Solution**: Specify platform explicitly
```bash
west twister -T zephyr/tests/drivers/sensor/mysensor -p qemu_cortex_m3
```

### Issue: Virtual environment not created
**Symptom**: `.venv` directory doesn't exist

**Solution**: Create it following Zephyr Getting Started Guide
```bash
cd ~/zephyrproject
python3 -m venv .venv
source .venv/bin/activate
pip install west
west init -l zephyr/
west update
```

## Best Practices

### 1. Always Activate Before Testing
Add to your workflow:
```bash
#!/bin/bash
cd ~/zephyrproject
source .venv/bin/activate

# Now run tests
west twister -T zephyr/tests/drivers/sensor/mysensor -p qemu_cortex_m3
```

### 2. Add Activation Check to Scripts
```bash
#!/bin/bash
if ! command -v west &> /dev/null; then
    echo "Error: west not found. Activate virtual environment:"
    echo "  source ~/zephyrproject/.venv/bin/activate"
    exit 1
fi

# Continue with tests...
```

### 3. Document in README
Always include activation instructions in test README:
```markdown
## Running Tests

1. Activate virtual environment:
   ```bash
   source ~/zephyrproject/.venv/bin/activate
   ```

2. Run tests:
   ```bash
   west twister -T . -p qemu_cortex_m3
   ```
```

## IDE Integration

### VS Code
Add to `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "terminal.integrated.env.linux": {
        "VIRTUAL_ENV": "${workspaceFolder}/.venv",
        "PATH": "${workspaceFolder}/.venv/bin:${env:PATH}"
    }
}
```

### Terminal Aliases
Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias zephyr='cd ~/zephyrproject && source .venv/bin/activate'
alias ztest='cd ~/zephyrproject && source .venv/bin/activate && west twister'
```

Usage:
```bash
zephyr  # Activates and changes to zephyr directory
ztest -T zephyr/tests/drivers/sensor/mysensor -p qemu_cortex_m3
```

## Troubleshooting

### Check Activation Status
```bash
# Should show path inside .venv
echo $VIRTUAL_ENV
# Output: /home/user/zephyrproject/.venv

# Should show venv in prompt
(venv) user@host:~/zephyrproject$
```

### Verify West Installation
```bash
source .venv/bin/activate
pip list | grep west
# Should show: west x.x.x
```

### Reinstall West if Needed
```bash
source .venv/bin/activate
pip install --upgrade west
west --version
```

## Quick Reference Card

| Command | Purpose |
|---------|---------|
| `source .venv/bin/activate` | Activate venv (Linux/Mac) |
| `.venv\Scripts\activate` | Activate venv (Windows) |
| `which west` | Check if west is available |
| `west --version` | Verify west installation |
| `deactivate` | Exit virtual environment |
| `echo $VIRTUAL_ENV` | Check if venv is active |

## Integration with CI/CD

### GitHub Actions
```yaml
name: Zephyr Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Create virtual environment
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install west

      - name: Run tests
        run: |
          source .venv/bin/activate
          west twister -T zephyr/tests/drivers/sensor/mysensor -p qemu_cortex_m3
```

### GitLab CI
```yaml
zephyr_test:
  image: zephyrprojectrtos/ci:latest
  script:
    - source .venv/bin/activate || python3 -m venv .venv && source .venv/bin/activate
    - pip install west
    - west twister -T zephyr/tests/drivers/sensor/mysensor -p qemu_cortex_m3
```

## Summary

**Key Points**:
- ✅ Always activate `.venv` before running `west` commands
- ✅ Check activation with `which west` or `echo $VIRTUAL_ENV`
- ✅ Add activation to scripts and documentation
- ✅ Specify platform with `-p qemu_cortex_m3` to avoid filtering
- ✅ Virtual environment is project-specific (in `~/zephyrproject/.venv`)
