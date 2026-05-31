---
title: Iteration <N> handover — <plan-slug>
date: <YYYY-MM-DD>
team: <team-name>
supervisor: or-supervisor-<N>
plan: <path/to/plan.md>
branch: <branch-name>
end_status: STOPPED_FOR_HANDOVER | COMPLETED
---

# Iteration <N> Handover

For STOPPED_FOR_HANDOVER: successor `or-supervisor-<N+1>` reads this FIRST, then continues from "Next Task to Start" below.

For COMPLETED: this doubles as the post-implementation report.

---

## Status (at handover)

- HEAD SHA: `<sha>`
- Tests: `<pass | fail with summary>`
- Typecheck: `<clean | errors with summary>`
- Branch state: `<n>` commits ahead of `<base>`, working tree `<clean | dirty + file list>`

## Summary

- Tasks completed this iteration: `<N>`
- Tasks completed cumulatively (plan total): `<N>` / `<TOTAL>`
- Commits this iteration: `<N>` (full SHA list under "Tasks Completed" below)

## Tasks Completed (this iteration)

| Task | Workers | Commits | One-line description |
|------|---------|---------|----------------------|
| Task <N>: <name> | `or-implementer-task<N>` / `or-spec-reviewer-task<N>` ✅ / `or-code-quality-reviewer-task<N>` ✅ | `<sha>`, `<sha>` | `<desc>` |

## Current Task State (omit if nothing in-flight or end_status = COMPLETED)

- Task: `<name>`
- Workers active: `<name>` — status `<DONE | fix-loop | reviewing>`
- Last accomplished: `<summary>`
- Next needed: `<summary>`
- Outstanding findings: `<list with file:line refs>`

## Next Task to Start (omit if end_status = COMPLETED)

Task `<N>`: `<name>`. First SPAWN: `or-implementer-task<N>`.

## Plan Deviations

- Task `<N>`: `<deviation + reasoning + approval source>`

## Reviewer Issues — Resolved

- Task `<N>` (`or-spec-reviewer-task<N>`): `<issue>` → `<fix sha>`
- Task `<N>` (`or-code-quality-reviewer-task<N>`): `<issue>` → `<fix sha>`

## Reviewer Issues — Parking Lot (deferred or unresolved)

- Task `<N>` (`or-code-quality-reviewer-task<N>`): `<soft note>` — deferred because `<reasoning>`

## Unplanned Changes

- Files modified outside plan scope: `<list>` — reason: `<...>`
- Unauthorized scope changes (caught and reverted, or accepted): `<list>`
- Dependencies added/changed beyond plan: `<list>`

(Empty if none.)

## Known Issues & Risks

- `<issue + impact + suggested next action>`
- Missing test coverage: `<areas>`
- Fragile-but-working: `<list>`

## Recommendations & Notes for Next Iteration

- Patterns that worked: `<list>`
- New precedents established: `<list>`
- Anti-patterns to avoid: `<list>`
- Suggested follow-up tasks: `<list>`
- Technical debt introduced: `<list>`

## Plan Progress

- Completed: `<N>` / `<TOTAL>` tasks
- In flight: `<task or none>`
- Remaining: `<list of task names>`
