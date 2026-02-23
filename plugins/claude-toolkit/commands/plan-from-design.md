# /plan-from-design - Create Implementation Plan from Design Doc

Wrapper around superpowers:writing-plans that uses the tracked design doc and tracks the created plan.

## Process

1. Read design doc pointer
2. Load design doc as context
3. Invoke superpowers:writing-plans
4. Save plan pointer, clear design pointer
5. Confirm

## Step 1: Get Design Doc

```bash
cat .claude/last-design-doc 2>/dev/null
```

If empty or missing, ask: "No design doc tracked. What's the path to your design doc?"

## Step 2: Load Context

Read the design doc and summarize key points before proceeding.

## Step 3: Create Plan

Invoke superpowers:writing-plans skill using the design doc as the spec/requirements. The skill will:
- Create detailed implementation plan
- Write to `docs/plans/YYYY-MM-DD-<feature-name>.md`
- Offer execution choice

**Important:** Do NOT proceed with execution choice. Stop after the plan is saved.

## Step 4: Update Pointers

After the plan doc is committed:

```bash
echo "docs/plans/YYYY-MM-DD-<feature-name>.md" > .claude/last-plan-doc && rm -f .claude/last-design-doc
```

Replace with actual path that was written.

## Step 5: Confirm

Announce: "Plan saved. Pointer set to: `<path>`. Design pointer cleared. Use `/implement-from-plan` after `/clear` to execute."
