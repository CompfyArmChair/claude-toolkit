# `or-superpowers-at-scale` — Suite Run Order (execution entry point)

This is the **entry point** for building `or-superpowers-at-scale`: four implementation plans that run **in order**. Implement each with `/sdd-at-scale <plan-path>`; after a plan's final self-review/integration task is GREEN, advance to the next. The suite is done when Plan 4's release push (Task 6) completes on your approval; then run cutover.

All plans target the **`claude-toolkit` plugin** repo `I:\Dev\claude-toolkit`, branch **`or-superpowers-at-scale`** (real git — **one commit per task** is the SDD rollback boundary). The branch currently holds the plans + the reviewed `or-*` agent drafts; **no plugin component is on disk yet** — execution is what creates them (the per-task `git mv`s and file authoring).

## Run order

Absolute base for all plan paths: `I:\Dev\claude-toolkit\docs\superpowers\plans\`

| # | Plan file | Scope | Depends on |
|---|-----------|-------|------------|
| 1 | `2026-05-30-or-superpowers-at-scale-1-research-skills.md` | 3 shared research/deposit skills (`research-deposit`, `dependency-research-methodology`, `community-research-methodology`) + 2 refactored researchers | — |
| 2 | `2026-05-30-or-superpowers-at-scale-2-phase-agents-skeleton.md` | `or-brainstormer` + `or-plan-writer` + `SKILL.md` skeleton + behavioral-spikes doc | 1 |
| 3 | `2026-05-30-or-superpowers-at-scale-3-workers-research-assets.md` | `or-supervisor` + 4 workers + 2 research teammates + 11 `assets/*` | 2 |
| 4 | `2026-05-31-or-superpowers-at-scale-4-manager-skill-release.md` | manager-discipline `SKILL.md` body + command wrapper + `1.1.1 → 1.2.0` release + push | 3 |

## Execution protocol

1. **Start at Plan 1:**
   `/sdd-at-scale I:\Dev\claude-toolkit\docs\superpowers\plans\2026-05-30-or-superpowers-at-scale-1-research-skills.md`
2. Implement every task; commit per task; run the plan's final self-review/integration task.
3. When that task is GREEN, **continue to the next plan.** Each plan's "Plan suite status" footer names its successor and its start-state assumptions (e.g. Plan 3 assumes Plan 2's agents + skeleton already exist on the branch). Run `/sdd-at-scale <next-plan-path>`.
4. Repeat through Plan 4. **Plan 4 Task 6 (release push) is gated on explicit user approval** — the push *is* the suite release; nothing is published before it.
5. **After the release**, run **cutover** (not a plan task): follow `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` → "Cutover checklist" — remove the deprecated loose `~/.claude` copies, `claude plugin install claude-toolkit`, then run Spikes 1–5 + Plan 1's wrapper check against the **installed** plugin. Do not declare the orchestrator behaviorally done until Spikes 1–3 are GREEN.

## Progress (the suite's current-position record — update as each plan lands)

- [ ] Plan 1 implemented (research skills + deposit)
- [ ] Plan 2 implemented (phase agents + skeleton + spikes doc)
- [ ] Plan 3 implemented (workers + research teammates + assets)
- [ ] Plan 4 implemented (manager `SKILL.md` body + command + release edits)
- [ ] Release pushed (Plan 4 Task 6, on approval)
- [ ] Cutover spikes run against installed plugin (Spikes 1–3 GREEN = done)

> The `.claude/last-plan-doc` pointer points here. To resume the suite, read this file, check the Progress box, and run `/sdd-at-scale` on the first unchecked plan.
