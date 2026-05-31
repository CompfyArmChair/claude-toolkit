---
title: Manager Handover <N> — <plan-slug>
date: <YYYY-MM-DD>
team: <team-name>
plan: <path/to/plan-or-none>
branch: <branch-name>
active_phase: brainstorm | plan | implement
active_phase_agent: <name of currently-alive phase agent, or none>
---

# Manager Handover <N>

## Topology & Protocol Reference

This workflow runs under the `or-superpowers-at-scale` skill (part of the `claude-toolkit` plugin). The skill's `SKILL.md` is the manager's playbook; its `assets/` directory contains the spawn / SPAWN_RESEARCH protocol, the preflight brief, the spawn-context templates, and the handover templates.

Invoke `Skill('claude-toolkit:or-superpowers-at-scale')` to load.

## Active phase (read FIRST on resume)

- `active_phase`: `<brainstorm | plan | implement>`
- `active_phase_agent`: `<or-brainstormer-<N> | or-plan-writer-<N> | none>`
- Phase-agent handover doc (if mid-phase 1/2): `<HANDOVER_DIR>/<phase>-handover-<N>.md`

A fresh manager uses this to decide whether to expect a phase agent alive in the team config (resume per design §"Fresh manager session resume") or whether implementation was already underway (resume per the supervisor/iteration handover).

## Plan & Project Context

- Plan: `<path-or-none>`
- Branch: `<branch-name>`
- Team: `<team-name>` (config: `~/.claude/teams/<team-name>/config.json`)
- Worktree: `<path>`
- Handover directory: `<path>`

## Project-specific conventions

- Commit format: `<convention>`
- Test command: `<cmd>`
- Typecheck command: `<cmd>`
- Other: `<bullets>`

---

## Current State (omit for N=1 if ever used at session start; required for N>1)

### Supervisor (implement phase only)

- Active supervisor: `or-supervisor-<N>`
- Latest iteration doc: `<path/to/iteration-<N>.md>`
- Last reported status: `<summary>`

### Workers (alive at handover)

| Name | Role | Status |
|------|------|--------|
| `<name>` | `<role>` | `<DONE | working | idle>` |

(Workers reported DONE should already be shutdown — list only those genuinely mid-work.)

### Recent SPAWN / shutdown history (last 5–10 events)

- `<timestamp>` SPAWN `<name>` (`<role>`, `<model>`)
- `<timestamp>` shutdown `<name>` (reported `<STATUS>`)

### Open issues / known gotchas this session

- `<issue>` — `<recovery>`
