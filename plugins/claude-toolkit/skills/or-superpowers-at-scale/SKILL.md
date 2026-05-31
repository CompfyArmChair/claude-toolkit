---
name: or-superpowers-at-scale
description: Use when the user wants to take an idea, spec, or plan all the way to shipped code in one orchestrated session — phrased as "brainstorm to ship", "full superpowers workflow orchestrated", or "end-to-end orchestration" — especially when the plan does not yet exist but the work is expected to benefit from 3-tier orchestration once implementation begins. Not for direct execution of an existing plan (use superpowers:subagent-driven-development) or for ad-hoc exploratory work.
---

# or-superpowers-at-scale

Orchestrates the full superpowers workflow end-to-end in one session — **brainstorm → plan → implement** — with the manager's context preserved throughout by delegating each phase to a dedicated teammate agent the user talks to directly. Supersedes `subagent-driven-development-at-scale`.

The manager (the parent Claude in the main chat) is the single precious, non-refreshable context: it brokers spawns and teardown, relays only at phase transitions, and is silent while a phase agent owns the user dialogue. Each phase is run by a refreshable teammate, so a long brainstorm, plan, or implementation never burns down the one context that cannot be replaced in-session.

## When to Use

- User wants to take an idea, spec, or plan all the way to shipped code in one session.
- Plan size is unknown at session start (the plan may not yet exist) but the work is expected to benefit from 3-tier orchestration once implementation begins.
- User explicitly asks for "full superpowers workflow orchestrated", "brainstorm to ship", or "orchestrated end-to-end".

**When NOT to use:**

- User already has a plan and wants direct execution without phase-agent overhead → use `superpowers:subagent-driven-development` directly.
- Ad-hoc exploratory work → no orchestration overhead at all.
- Single-question lookups, simple edits → direct chat.

## Architecture

### Topology

| Tier | Identity | Active during | Talks to user? | Spawns? | Refreshable? |
|------|----------|---------------|----------------|---------|--------------|
| **Manager** | Parent Claude (main chat) | Whole session | Only at phase transitions + PAUSE relays | Yes — sole `Agent`-tool holder | **Not in-session** — refreshed only via cross-session handover (single precious context) |
| **Phase agent** | `or-brainstormer-N` / `or-plan-writer-N` | One phase | **Yes, directly** (Claude Code teammate routing) | No — uses `SPAWN_RESEARCH` broker | Yes — handover at 150k |
| **Supervisor** | `or-supervisor-N` | One implementation iteration | No (PAUSE relays only) | No — uses `SPAWN` broker | Yes — handover at 200k |
| **Worker** | `or-implementer-task<N>` / `or-spec-reviewer-task<N>` / `or-code-quality-reviewer-task<N>` / `or-final-reviewer` | One task phase | No | No | Fresh per phase, shutdown after DONE |
| **Research agent** | `or-<topic>-researcher-N` (background teammate) | One research request | No | No | One-shot — manager shuts down after `RESEARCH_DONE` |

### Phase flow

The orchestrator runs up to four phases; mode detection at preflight chooses the entry point (a plain idea starts at brainstorm, a spec path skips to plan, a plan path skips to implementation).

- **Phase 0 — Preflight** (foreground one-shot subagent): detect mode (`idea` / `spec` / `plan`) from the input, prompt for a worktree name + base branch, create the worktree, and return `PREFLIGHT_OK` with the resolved mode, paths, and conventions.
- **Phase 1 — Brainstorm** (mode `idea`): the manager spawns `or-brainstormer-1` (teammate, opus). The user talks to it directly. It follows `superpowers:brainstorming` to an approved spec, then signals the manager `BRAINSTORM_COMPLETE — spec: <path>`.
- **Phase 2 — Plan** (mode `idea` or `spec`): the manager spawns `or-plan-writer-1` (teammate, opus). The user talks to it directly. It follows `superpowers:writing-plans` to a reviewed plan, then signals `PLAN_COMPLETE — plan: <path>`. The plan→implementation transition is the one phase boundary the manager gates on the user's explicit go-ahead.
- **Phase 3 — Implementation** (always): the manager spawns `or-supervisor-1` (teammate, opus), which invokes `superpowers:subagent-driven-development` and dispatches `or-implementer` / `or-spec-reviewer` / `or-code-quality-reviewer` workers per task through the manager's `SPAWN` broker, with `or-final-reviewer` at the end.

Throughout, research is delegated — phase agents request it via the manager's `SPAWN_RESEARCH` broker, and findings are deposited to disk so they never transit the manager's context.

## Integration with Other Skills

- **Hard dependency:** `superpowers:brainstorming` (pre-seeded into `or-brainstormer`)
- **Hard dependency:** `superpowers:writing-plans` (pre-seeded into `or-plan-writer`)
- **Hard dependency:** `superpowers:subagent-driven-development` (pre-seeded into `or-supervisor`)
- **Hard dependency:** `superpowers:test-driven-development` (pre-seeded into `or-implementer`)
- **Hard dependency:** `superpowers:using-git-worktrees` (invoked by preflight)
- **Followed by:** `superpowers:finishing-a-development-branch` (the supervisor invokes it after the final iteration)
