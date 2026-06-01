---
name: or-superpowers-at-scale
description: Use when the user wants to take an idea, spec, or plan all the way to shipped code in one orchestrated session — phrased as "brainstorm to ship", "full superpowers workflow orchestrated", or "end-to-end orchestration" — especially when the plan does not yet exist but the work is expected to benefit from 3-tier orchestration once implementation begins. Not for direct execution of an existing plan (use superpowers:subagent-driven-development) or for ad-hoc exploratory work.
user_invocable: true
---

# or-superpowers-at-scale

Orchestrates the full superpowers workflow end-to-end in one session — **brainstorm → plan → implement → ship** — with the manager's context preserved throughout by delegating each phase to a dedicated teammate agent the user talks to directly. Supersedes `subagent-driven-development-at-scale`.

The manager (the parent Claude in the main chat) is the single precious, non-refreshable context: it brokers spawns and teardown, relays only at phase transitions, and is silent while a phase agent owns the user dialogue. Each phase is run by a refreshable teammate, so a long brainstorm, plan, implementation, or ship step never burns down the one context that cannot be replaced in-session.

## When to Use

- User wants to take an idea, spec, or plan all the way to shipped code in one session.
- Plan size is unknown at session start (the plan may not yet exist) but the work is expected to benefit from 3-tier orchestration once implementation begins.
- User explicitly asks for "full superpowers workflow orchestrated", "brainstorm to ship", or "orchestrated end-to-end".

**When NOT to use:**

- User already has a plan and wants direct execution without phase-agent overhead → use `superpowers:subagent-driven-development` directly.
- Ad-hoc exploratory work → no orchestration overhead at all.
- Single-question lookups, simple edits → direct chat.

## Architecture

The orchestrator runs across a tiered team (the `or-` prefix throughout = *orchestrator*).

### Topology

| Tier | Identity | Active during | Talks to user? | Spawns? | Refreshable? |
|------|----------|---------------|----------------|---------|--------------|
| **Manager** | Parent Claude (main chat) | Whole session | Only at phase transitions + PAUSE relays | Yes — sole `Agent`-tool holder | **Not in-session** — refreshed only via cross-session handover (single precious context) |
| **Phase agent** | `or-brainstormer-N` / `or-plan-writer-N` | One phase | **Yes, directly** (Claude Code teammate routing) | No — uses `SPAWN_RESEARCH` broker | Yes — handover at 150k |
| **Finisher** | `or-finisher-N` | Phase 4 (ship) | **Yes, directly** (teammate routing) | No | Yes — handover at 150k (rare; see Handover Ladder) |
| **Supervisor** | `or-supervisor-N` | One implementation iteration | No (PAUSE relays only) | No — uses `SPAWN` broker | Yes — handover at 200k |
| **Worker** | `or-implementer-task<N>` / `or-spec-reviewer-task<N>` / `or-code-quality-reviewer-task<N>` / `or-final-reviewer` | One task phase | No | No | Fresh per phase, shutdown after DONE |
| **Research agent** | `or-<topic>-researcher-N` (background teammate) | One research request | No | No | One-shot — manager shuts down after `RESEARCH_DONE` |

### Phase flow

The orchestrator runs up to five phases; mode detection at preflight chooses the entry point (a plain idea starts at brainstorm, a spec path skips to plan, a plan path skips to implementation). Ship (Phase 4) always runs after the final implementation iteration.

- **Phase 0 — Preflight** (foreground one-shot subagent): detect mode (`idea` / `spec` / `plan`) from the input, prompt for a worktree name + base branch, create the worktree, and return `PREFLIGHT_OK` with the resolved mode, paths, and conventions.
- **Phase 1 — Brainstorm** (mode `idea`): the manager spawns `or-brainstormer-1` (teammate, opus). The user talks to it directly. It follows `superpowers:brainstorming` to an approved spec, then signals the manager `BRAINSTORM_COMPLETE — spec: <path>`.
- **Phase 2 — Plan** (mode `idea` or `spec`): the manager spawns `or-plan-writer-1` (teammate, opus). The user talks to it directly. It follows `superpowers:writing-plans` to a reviewed plan, then signals `PLAN_COMPLETE — plan: <path>`. The plan→implementation transition is the one phase boundary the manager gates on the user's explicit go-ahead.
- **Phase 3 — Implementation** (always): the manager spawns `or-supervisor-1` (teammate, opus), which invokes `superpowers:subagent-driven-development` and dispatches `or-implementer` / `or-spec-reviewer` / `or-code-quality-reviewer` workers per task through the manager's `SPAWN` broker, with `or-final-reviewer` at the end.
- **Phase 4 — Ship** (always): on `ITERATION <N> — COMPLETED`, the manager shuts the supervisor down and spawns `or-finisher-1` (teammate, opus). The user talks to it directly. It follows `superpowers:finishing-a-development-branch` (merge / PR / cleanup, performed directly — it is user-facing), then signals `SHIP_COMPLETE`; the manager shuts it down and ends the session.

Throughout, research is delegated — phase agents request it via the manager's `SPAWN_RESEARCH` broker, and findings are deposited to disk so they never transit the manager's context.

## Integration with Other Skills

- **Hard dependency:** `superpowers:brainstorming` (pre-seeded into `or-brainstormer`)
- **Hard dependency:** `superpowers:writing-plans` (pre-seeded into `or-plan-writer`)
- **Hard dependency:** `superpowers:subagent-driven-development` (pre-seeded into `or-supervisor`)
- **Hard dependency:** `superpowers:test-driven-development` (pre-seeded into `or-implementer`)
- **Hard dependency:** `superpowers:finishing-a-development-branch` (pre-seeded into `or-finisher`; run in Phase 4 — **not** supervisor-invoked)
- **Hard dependency:** `superpowers:using-git-worktrees` (invoked by preflight)

## Core Principle: Manager Context Is Sacred

The manager (you, the parent Claude in the main chat) is the ONLY tier in this topology with non-refreshable context. Every phase agent, finisher, supervisor, and worker is disposable — replaced by a fresh successor with fresh context the moment they finish or cross a handover threshold. **The manager cannot be replaced mid-session.** Once your context exhausts, the whole workflow stops mid-flight, the user starts a new session, and a fresh manager picks up from `manager-handover-N.md`.

**This is the load-bearing constraint that determines every other rule in this skill.** The operating discipline it implies — the Preservation Imperative (OUTPUT / INPUT / STORAGE) and every conservation rule — is in the playbook.

When in doubt: shorter is better. Silence is best. Performance budget: 0–100k = best, 100k–200k = good, >200k = degrading. The cross-session handover trigger is **crossing 200k**.

## Map — bundled assets

**Manager: your operating manual is `assets/manager-playbook.md`. Read it in full now** (resolve it against this skill's base directory, shown above as "Base directory for this skill") **before any spawn or message** — this `SKILL.md` is only the shared overview; your Initial Setup, broker protocols, idle taxonomy, communication style, conservation rules, handover ladder, recovery, and red flags all live in the playbook. Teammates ignore this line and use the table below to reach their own templates.

A teammate that loads this skill (`Skill('claude-toolkit:or-superpowers-at-scale')`) reaches these files — they are NOT referenced by path from any agent body (that is what skill-invocation buys: install-agnostic access):

| Asset | Reached by | Contains |
|-------|-----------|----------|
| `assets/manager-playbook.md` | manager (FIRST ACTION) | The manager's complete operating manual |
| `assets/spawn-protocol.md` | manager, supervisor, phase agents | Full SPAWN + SPAWN_RESEARCH mechanics (the canonical SHUTDOWN handshake is in the playbook) |
| `assets/preflight-brief.md` | manager (via the playbook's Initial Setup) | Preflight: mode detection, worktree/branch prompts, `PREFLIGHT_OK` / `PREFLIGHT_FAIL` |
| `assets/{brainstormer,plan-writer,supervisor,implementer,reviewer,finisher}-spawn-context.md` | manager (broker) | Per-spawn variable templates substituted at spawn time |
| `assets/iteration-handover-template.md` | supervisor (via this skill) | Iteration handover doc |
| `assets/{brainstormer,plan-writer}-handover-template.md` | phase agents (via this skill) | Phase handover docs (the anti-drift ledger) |
| `assets/manager-handover-template.md` | manager (200k handover) | Cross-session manager handover (with the `active_phase` / `active_phase_agent` fields) |
