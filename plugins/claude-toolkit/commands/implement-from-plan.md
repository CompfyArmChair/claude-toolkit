# /implement-from-plan - Execute Plan with Subagent-Driven Development

Wrapper around superpowers:subagent-driven-development that uses the tracked plan and clears the pointer on completion.

## Process

1. Read plan doc pointer
2. Invoke superpowers:subagent-driven-development
3. Generate post-implementation report
4. On completion, clear plan pointer
5. Confirm

## Step 1: Get Plan Doc

```bash
cat .claude/last-plan-doc 2>/dev/null
```

If empty or missing, ask: "No plan doc tracked. What's the path to your plan?"

## Step 2: Execute Plan

Invoke superpowers:subagent-driven-development with the plan file. The skill will:
- Read plan and extract all tasks
- Dispatch fresh subagent per task
- Two-stage review after each (spec compliance, then code quality)
- Final code review
- Use superpowers:finishing-a-development-branch when complete

## Step 3: Post-Implementation Report

After all tasks are complete and the final code review passes, but **before** offering finishing-a-development-branch options, generate a comprehensive report covering:

### 3.1 Summary
- Total tasks completed
- Total commits made (list SHAs with one-line descriptions)
- Test results (total tests, all passing?)

### 3.2 Plan Deviations
- Any tasks that diverged from the plan and why
- SDK/API differences discovered during implementation
- Assumptions in the plan that proved incorrect

### 3.3 Reviewer Issues
- Issues flagged by spec compliance reviewers (and how each was resolved)
- Issues flagged by code quality reviewers (and how each was resolved)
- Any issues that were **not** addressed, with justification

### 3.4 Unplanned Changes
- Files modified outside the plan's scope
- Any unauthorized scope changes made by subagents
- Dependencies added or changed beyond what the plan specified

### 3.5 Known Issues & Risks
- Anything that works but feels fragile
- Missing test coverage
- Potential integration issues
- Items that may need follow-up work

### 3.6 Recommendations
- Suggested follow-up tasks (if any)
- Areas that would benefit from additional testing
- Technical debt introduced

**Format:** Present the report directly to the user. Omit sections that have nothing to report (e.g., if there were no plan deviations, skip 3.2).

## Step 4: Clear Pointer

After successful completion (all tasks done, final review passed, branch finished):

```bash
rm -f .claude/last-plan-doc
```

## Step 5: Confirm

Announce: "Implementation complete. Plan pointer cleared."
