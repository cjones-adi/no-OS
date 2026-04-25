# Skill Usage Tracking Logs

This directory contains logs documenting when agents use skills during their workflows. This provides traceability and verification that the skill system is being actively utilized.

## Purpose

When agents reference skills (like `/no-os-unit-testing` or `/no-os-spi`), they create usage logs here to document:
- **What skill was used** - Which skill provided guidance
- **Why it was needed** - What problem or task triggered the skill reference
- **What was learned** - Specific information extracted from the skill
- **How it was applied** - How the skill knowledge was used in the current work
- **Outcome** - What was accomplished (tests created, coverage achieved, issues resolved)

## Log File Naming Convention

Logs use the format: `[timestamp]-[skill-name].md`

**Examples**:
- `2026-03-24T14-30-45-no-os-unit-testing.md`
- `2026-03-24T15-12-08-no-os-spi.md`
- `2026-03-24T16-45-22-datasheet-parsing.md`

**Timestamp format**: ISO 8601 with hyphens (YYYY-MM-DDTHH-MM-SS)

## Log File Structure

Each log follows this template:

```markdown
# Skill Usage Log

**Skill**: [skill-name]
**Agent**: [agent-name]
**Timestamp**: [ISO 8601 timestamp]
**Session Context**: [Brief description of work being done]

## Why This Skill Was Used

[Explanation of what triggered the need for this skill]

## Information Needed From Skill

- [Specific information item 1]
- [Specific information item 2]
- [etc.]

## How Skill Information Was Applied

[Description of how the skill knowledge was applied to complete the task]

## Outcome

- [What was accomplished]
- [Metrics if applicable: tests created, coverage %, issues resolved]
- [Any follow-up actions]
```

## Available Skills

**Testing Skills**:
- `no-os-unit-testing` - Comprehensive unit testing (Ceedling, Unity, CMock, gcov)

**Platform Driver Skills**:
- `no-os-spi` - SPI platform drivers
- `no-os-i2c` - I2C platform drivers
- `no-os-gpio` - GPIO platform drivers
- `no-os-irq` - IRQ interrupt handling

**Framework Skills**:
- `no-os-iio` - Industrial I/O framework
- `no-os-make-and-linker` - Build system

**Tools & Parsers**:
- `datasheet-parsing` - Hardware specification extraction

## Usage Statistics

To analyze skill usage:

```bash
# Count total skill usage logs
ls -1 *.md | grep -v README | wc -l

# Usage by skill
ls -1 *-no-os-unit-testing.md | wc -l
ls -1 *-no-os-spi.md | wc -l
ls -1 *-datasheet-parsing.md | wc -l

# Usage by date
ls -1 2026-03-24*.md | wc -l
```

## Benefits

1. **Verification**: Confirms that skill refactoring is being utilized
2. **Tracking**: Shows which skills are most valuable
3. **Learning**: Documents real-world skill application patterns
4. **Improvement**: Identifies gaps in skill content or areas needing expansion
5. **Accountability**: Provides audit trail of agent decision-making

## Agent Responsibility

Agents **MUST** create skill usage logs when:
- They consult a skill for guidance
- They reference a skill in their workflow
- They apply knowledge from a skill to solve a problem
- The outcome was directly influenced by skill content

Agents should create logs **AFTER** using the skill, not just when mentioning it. The log should reflect actual usage and tangible outcomes.

## Reviewing Logs

Periodically review logs to:
- **Identify popular skills** - Which skills are used most often?
- **Find usage patterns** - When and why are skills needed?
- **Spot coverage gaps** - What information is missing from skills?
- **Validate value** - Are skills helping agents complete tasks more effectively?
- **Improve content** - Based on what agents extract, what should be emphasized?

## Example Log

See [EXAMPLE-skill-usage-log.md](EXAMPLE-skill-usage-log.md) for a complete example of a well-documented skill usage log.

---

**Note**: This directory should accumulate logs over time. Periodically archive older logs (e.g., move to `archive/YYYY-MM/`) to keep the directory manageable while preserving history.
