# Zephyr Unit Testing Skill

Modular skill for writing unit tests for Zephyr drivers using Ztest and Twister.

## Structure

```
zephyr-unit-testing/
├── SKILL.md                          # Main skill (325 lines) - quick-start workflow
├── SKILL.md.old                      # Original comprehensive documentation (2381 lines)
├── reference/                        # Detailed documentation by topic
│   ├── test-macros.md               # Complete ZTEST macro reference
│   └── troubleshooting.md           # 12 common issues with solutions
└── examples/                         # Working code examples
    └── sensor-with-emulation.c      # Complete sensor test suite example
```

## How the Modular Structure Works

### Automatic Loading
- **SKILL.md** is loaded when skill is invoked (always available)

### On-Demand Loading (via Read tool)
Reference files are **not** automatically loaded. The AI assistant reads them when triggered by:

**User keywords**:
- "ZTEST_P", "parameterized" → Read `reference/test-macros.md`
- "error", "build fails" → Read `reference/troubleshooting.md`
- "show example" → Read `examples/sensor-with-emulation.c`

**Error messages in user output**:
- Fixture struct errors → `troubleshooting.md` Issue #1
- k_malloc undefined → `troubleshooting.md` Issue #2
- Device not found → `troubleshooting.md` Issue #12

### For Users

#### Quick Start
Read **SKILL.md** for:
- 6-step workflow to create test project
- Test macro quick reference
- Common patterns and best practices
- Quick troubleshooting fixes

#### When You Need More
Just ask naturally:
- "How do I use parameterized tests?" → AI reads `test-macros.md`
- "Build fails with fixture struct error" → AI reads `troubleshooting.md`
- "Show me a complete example" → AI reads `sensor-with-emulation.c`

No need to reference files explicitly - the AI knows when to read them!

#### Manual Reference
You can also directly reference:
- **reference/test-macros.md** - All ZTEST variants
- **reference/troubleshooting.md** - 12 common errors + fixes
- **examples/sensor-with-emulation.c** - Complete working example
- **SKILL.md.old** - Original comprehensive docs

## Size Comparison

| File | Lines | Purpose |
|------|-------|---------|
| SKILL.md (new) | 325 | Quick reference and workflow |
| SKILL.md.old | 2381 | Comprehensive documentation |
| test-macros.md | ~200 | Detailed macro reference |
| troubleshooting.md | ~300 | Issue resolution guide |

**Total reduction**: Main skill is now **86% smaller** while maintaining access to all information through references.

## Benefits of Modular Structure

1. **Reduced context window usage**: Only load what you need
2. **Faster lookup**: Organized by topic
3. **Easier maintenance**: Update specific sections independently
4. **Better organization**: Reference vs examples vs quick-start clearly separated
5. **Preserved detail**: All original content available in reference files

## Migration Notes

- Old SKILL.md preserved as SKILL.md.old
- All content from old skill is still accessible
- New structure optimized for quick reference with optional deep-dive
