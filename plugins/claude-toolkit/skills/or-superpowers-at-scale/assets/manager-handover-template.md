---
title: Manager Handover <N> — <plan-slug>
date: <YYYY-MM-DD>
team: <team-name>
plan: <path/to/plan-or-none>
branch: <branch-name>
active_phase: brainstorm | plan | implement | ship
active_phase_agent: <name of currently-alive phase agent or finisher, or none>
---

# Manager Handover <N>

## Resume invocation (user: paste this after `/clear`)

```
/claude-toolkit:or-superpowers-at-scale <ABS_PATH_TO_THIS_DOC>
```

(Writing manager: substitute the literal absolute path of this file. The fresh manager detects the `manager-handover-*.md` argument and branches straight to Fresh-Manager-Resume — no preflight, no TeamCreate.)

## Topology & Protocol Reference

This workflow runs under the `or-superpowers-at-scale` skill (part of the `claude-toolkit` plugin). The skill's `SKILL.md` is the manager's playbook; its `assets/` directory contains the spawn / SPAWN_RESEARCH protocol, the preflight brief, the spawn-context templates, and the handover templates.

Invoke `Skill('claude-toolkit:or-superpowers-at-scale')` to load.

## Active phase (read FIRST on resume)

- `active_phase`: `<brainstorm | plan | implement | ship>`
- `active_phase_agent`: `<or-brainstormer-<N> | or-plan-writer-<N> | or-finisher-<N> | none>`
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

### Live roster at handover (canonical — REQUIRED, every member; F28)

Enumerate **every** member from a live read of `~/.claude/teams/<team>/config.json` at write time — never from memory. One disposition line per member. The successor runs a names-only delta-check against this table and reads member detail only for deltas.

| Name | Role | Disposition | Note |
|------|------|-------------|------|
| `<name>` | `<role>` | `keep` / `reap` / `zombie` / `live-worker` | `<one line>` |

Dispositions: `keep` = the resume needs it alive (e.g. the active phase agent); `reap` = orphan — successor issues `shutdown_request`; `zombie` = ignores `shutdown_request` — a prior session already exhausted the max-2-attempts cap (F23); successor skips shutdown for it and tolerates its idle pings; `live-worker` = genuinely mid-work.

### Recent SPAWN / shutdown history (last 5–10 events)

- `<timestamp>` SPAWN `<name>` (`<role>`, `<model>`)
- `<timestamp>` shutdown `<name>` (reported `<STATUS>`)

### Open issues / known gotchas this session

- `<issue>` — `<recovery>`
