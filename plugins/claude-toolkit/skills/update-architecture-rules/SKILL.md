---
name: update-architecture-rules
description: /update-architecture-rules - Add or modify rules in the architecture-reviewer agent
user_invocable: true
---

# Update Architecture Rules

Add or modify rules in `~/.claude/agents/architecture-reviewer.md`.

## Rule Quality Checklist

Before finalizing any rule change, verify:

1. **States the WHY** - Explains the purpose DI/layering/etc. serves
2. **Has characteristics** - Bullet list of what qualifies/disqualifies
3. **Shows contrast** - Both OK and VIOLATION examples side-by-side
4. **Minimal code** - Smallest example that illustrates the point
5. **Fresh context test** - Would an agent with no prior conversation understand?

## Rule Structure Template

```markdown
N. **Rule Name**: One-sentence principle explaining WHY this matters.

   **Characteristics:**
   - Condition that makes this applicable
   - Another condition
   - What disqualifies from this rule

   ```csharp
   // NOT A VIOLATION - [reason]
   _example = new Example();    // [brief explanation]

   // VIOLATION - [reason]
   _bad = new BadExample();     // [brief explanation]
   ```
```

## Process

1. Read current `~/.claude/agents/architecture-reviewer.md`
2. Identify where the rule fits (which section, which exception list)
3. Draft rule following template above
4. Review for fresh-context clarity
5. Apply edit

## Fresh Context Test

Ask: "If I knew nothing about this conversation, would I understand:"
- What qualifies for this rule/exception?
- What doesn't qualify?
- Why the distinction matters?

If any answer is "no", add more context or contrast.
