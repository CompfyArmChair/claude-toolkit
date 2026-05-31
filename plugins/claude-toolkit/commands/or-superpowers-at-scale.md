# /or-superpowers-at-scale - Orchestrate brainstorm → plan → implement end-to-end

Thin wrapper that invokes the `or-superpowers-at-scale` orchestrator skill. The skill is the manager's playbook — it owns preflight, mode detection, worktree creation, team creation, and all phase orchestration. This command exists only to give the workflow a `/or-superpowers-at-scale [<idea> | <spec-path> | <plan-path>]` entry point.

## Process

Invoke `Skill('claude-toolkit:or-superpowers-at-scale')` and follow it. Pass `$ARGUMENTS` through as the orchestrator's starting input:

- an **idea statement** (or empty) → the skill starts at Phase 1 (brainstorm)
- a **spec path** (`docs/superpowers/specs/*-design.md`) → starts at Phase 2 (plan)
- a **plan path** (`docs/superpowers/plans/*.md`) → starts at Phase 3 (implementation)

Do NOT pre-classify the input — the skill's preflight subagent detects the mode and asks the user if it is ambiguous. Everything after invocation (worktree setup, spawning the first phase agent, and the manager's spawn-brokering) is the skill's responsibility; this command adds no logic of its own.
