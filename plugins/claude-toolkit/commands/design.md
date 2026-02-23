# /design - Brainstorm and Track Design Doc

Wrapper around superpowers:brainstorming that tracks the created design doc.

## Process

1. Invoke superpowers:brainstorming skill and follow it completely
2. After the design doc is written to `docs/plans/*-design.md`, save the pointer
3. Confirm the pointer was saved

## Step 1: Brainstorm

Invoke superpowers:brainstorming and follow it exactly. The skill will:
- Explore the idea through questions
- Present design in sections
- Write validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Commit the design document

## Step 2: Save Pointer

After the design doc is committed, save its path:

```bash
mkdir -p .claude && echo "docs/plans/YYYY-MM-DD-<topic>-design.md" > .claude/last-design-doc
```

Replace with the actual path that was written.

## Step 3: Confirm

Announce: "Design doc saved. Pointer set to: `<path>`. Use `/plan-from-design` after `/clear` to create implementation plan."
