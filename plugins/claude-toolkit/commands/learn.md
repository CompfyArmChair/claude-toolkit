# /learn - Extract Reusable Patterns

Analyze the current session and extract patterns worth saving as skills.

## What to Extract

- Error resolution patterns
- Debugging techniques
- Workarounds (library quirks, API limitations, version-specific fixes)
- Project-specific patterns (conventions, architecture decisions)

## Output Format

Save to `~/.claude/skills/learned/[pattern-name].md`:

```markdown
# [Descriptive Pattern Name]

**Extracted:** [Date]
**Context:** [When this applies]

## Problem
[What problem this solves]

## Solution
[The pattern/technique/workaround]

## Example
[Code example if applicable]

## When to Use
[Trigger conditions]
```

## Process

1. Review session for extractable patterns
2. Draft the skill file
3. Ask user to confirm before saving

## Don't Extract

- Trivial fixes (typos, simple syntax errors)
- One-time issues (API outages, transient problems)
