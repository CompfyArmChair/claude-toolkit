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

## Core Principle: Manager Context Is Sacred

The manager (you, the parent Claude in the main chat) is the ONLY tier in this topology with non-refreshable context. Every phase agent, supervisor, and worker is disposable — replaced by a fresh successor with fresh context the moment they finish or cross a handover threshold. **The manager cannot be replaced mid-session.** Once your context exhausts, the whole workflow stops mid-flight, the user starts a new session, and a fresh manager picks up from `manager-handover-N.md`.

**This is the load-bearing constraint that determines every other rule in this skill.**

### The Preservation Imperative

Evaluate every action against ONE question: **"does this consume manager context unnecessarily?"** If yes — find the cheapest alternative or push it to a refreshable tier (phase agent, supervisor, worker, doc).

Three forms this takes:

1. **OUTPUT discipline** — every word you emit displaces a word you could have held from incoming messages. Manager output is pure functional protocol (`Spawned: <name>` / `Acknowledged.` / `Standing by.` / `Research <name> done: <path>`), NOT collaborative discourse. During phases 1 and 2 the manager produces NO chat output at all — the user talks to the phase agent directly.
2. **INPUT discipline** — never proactively pull information you don't need. Don't ask a phase agent or supervisor for status. Don't read the spec/plan artifact or a deposited findings file. Information arrives via SPAWN / SPAWN_RESEARCH / completion tokens.
3. **STORAGE discipline** — never hold in chat what could live in a doc. Reviewer findings, deviations, gotchas → `iteration-N.md` via the supervisor; dialogue state → the phase-agent handover doc. The manager NEVER echoes content that's already (or could be) in a doc.

**The phase agent exists so the manager doesn't have to run the dialogue.**
**The supervisor exists so the manager doesn't have to think about execution.**
**The handover doc exists so chat doesn't have to remember.**
**The worker exists so context doesn't have to accumulate.**

When in doubt: shorter is better. Silence is best. Performance budget: 0–100k = best, 100k–200k = good, >200k = degrading. The cross-session handover trigger is **crossing 200k**.

## Mode Detection

The preflight subagent detects the run mode from the user's input and returns it in `PREFLIGHT_OK`. You never detect mode yourself — you read it from the block.

| User input shape | Mode | Entry point |
|------------------|------|-------------|
| Plain text (idea statement) or no input | `idea` | Phase 1 — Brainstorm |
| Path to a spec file (`docs/superpowers/specs/*-design.md` or a user-supplied spec path) | `spec` | Phase 2 — Plan |
| Path to a plan file (`docs/superpowers/plans/*.md` or a user-supplied plan path) | `plan` | Phase 3 — Implementation |

If the input shape is ambiguous, preflight asks the user (`AskUserQuestion`) rather than guessing. The `PREFLIGHT_OK` block you receive:

```
PREFLIGHT_OK
mode: idea | spec | plan
worktree: <path>
branch: <branch-name>
handover_dir: <path>
spec_path: <path-or-none>
plan_path: <path-or-none>
goal: <one-line, if spec/plan provided>
total_tasks: <N, if plan provided>
conventions:
  commit_format: <...>
  test_command: <...>
  typecheck_command: <...>
  other: <...>
```

You hold this block as the substrate for the next spawn-context — nothing more. You do NOT read `spec_path` or `plan_path` yourself (see Conservation Rules).

## Initial Setup (first manager turn)

**Delegate preflight; do NOT run checks in your own context.** Mode detection, branch check, worktree setup, and metadata extraction are exactly the work that should burn a subagent's context, not yours.

1. **Spawn the preflight subagent (foreground, blocking).** Load `assets/preflight-brief.md`, substitute `<USER_INPUT>` and `<USER_CONSENT>`, then:

   ```
   Agent({
     subagent_type: "general-purpose",
     description: "Preflight for or-superpowers-at-scale",
     prompt: <contents of preflight-brief.md, substituted>
   })
   ```

   No `team_name`, no `run_in_background` — a one-shot foreground agent that returns its structured summary. You absorb only the summary block, not the worktree-skill content or any tool output it produced.

2. **Read the returned block.** If `PREFLIGHT_FAIL`, surface the one-line reason + suggested_recovery to the user and stop. If `PREFLIGHT_OK`, proceed.

3. **`TeamCreate({team_name: <slug>})`** — slug from the plan/spec/worktree name. Team creation always happens here, regardless of mode (it is not phase-1-specific).

4. **Spawn the first agent for the mode** as a background teammate (opus) with the matching `assets/*-spawn-context.md` substituted from the `PREFLIGHT_OK` block:
   - `idea` → `or-brainstormer-1` (`brainstormer-spawn-context.md`)
   - `spec` → `or-plan-writer-1` (`plan-writer-spawn-context.md`)
   - `plan` → `or-supervisor-1` (`supervisor-spawn-context.md`)

5. **Emit the single first-session message for the mode**, then revert to terse protocol (and silence during phases 1/2):
   - `idea`: `Spawned or-brainstormer-1 (opus, background) on team `<name>`. Talk to it directly — switch with Shift+Down. It's driving Phase 1.`
   - `spec`: `Spawned or-plan-writer-1 (opus, background) on team `<name>`. Talk to it directly — switch with Shift+Down. It's driving Phase 2.`
   - `plan`: `Spawned or-supervisor-1 (opus, background) on team `<name>`. Standing by.`

**No setup-time handover doc.** Project context lives in the spawn-context. The handover-doc series begins only when a tier crosses its threshold.

## Manager Broker Protocols

You are the sole `Agent`-tool holder — the only tier that spawns or shuts down teammates. The depth-1 tiers (supervisor, phase agents) request these actions via SendMessage tokens; you execute them. The full SPAWN / SPAWN_RESEARCH mechanics live in `assets/spawn-protocol.md` (the supervisor and phase agents reach it by invoking this skill); the **canonical SHUTDOWN handshake is here** (it lives nowhere else).

### SPAWN (worker dispatch — supervisor → manager)

The supervisor SendMessages:

```
SPAWN
NAME: <name>
ROLE: implementer | spec-reviewer | code-quality-reviewer | final-reviewer
MODEL: sonnet | opus | haiku
```

Map `ROLE` → plugin-qualified `subagent_type`:

| ROLE | subagent_type |
|------|---------------|
| `implementer` | `claude-toolkit:or-implementer` |
| `spec-reviewer` | `claude-toolkit:or-spec-reviewer` |
| `code-quality-reviewer` | `claude-toolkit:or-code-quality-reviewer` |
| `final-reviewer` | `claude-toolkit:or-final-reviewer` |

Spawn via `Agent({team_name, name, subagent_type: <mapped>, model: <MODEL>, prompt: <substituted spawn-context>, run_in_background: true})`, then SendMessage the supervisor `Spawned: <name>`. **For `implementer`, `MODEL` is required** — `or-implementer` has no default `model:`; a SPAWN that omits it is a protocol violation (reply `SPAWN rejected — implementer requires explicit MODEL field.`). Full mechanics + the spawn-context substitution: `assets/spawn-protocol.md`.

### SHUTDOWN (worker teardown — supervisor → manager)

You own teardown as well as spawn; the supervisor never shuts a worker down directly (shutdown is a lead action). When SDD says a worker's phase is done, the supervisor SendMessages:

```
SHUTDOWN
NAME: <worker-name>
```

You then issue `SendMessage(<worker-name>, {type: "shutdown_request", reason: "task phase complete"})`. Teardown is fire-and-forget — no ack is required, so add no reply; the worker's `shutdown_response` and termination are absorbed as an idle-class wake-up. This is symmetric with SPAWN: the manager is the only tier that spawns or shuts down teammates.

### SPAWN_RESEARCH (research dispatch — phase agent → manager)

A phase agent SendMessages:

```
SPAWN_RESEARCH
NAME: <name>
AGENT: <subagent_type>
DEPOSIT: <path>                       (required — findings never transit manager context)
MODEL: <model>                        (optional; defaults to the agent's frontmatter default)
PROMPT: <research question>
```

All research agents spawn as **background teammates** (`run_in_background: true`, WITH `team_name`) — mechanically identical to worker dispatch. They signal completion with a `RESEARCH_DONE: <path>` / `RESEARCH_BLOCKED: <path> — <reason>` token.

| Case | Manager action |
|------|----------------|
| `AGENT` is `or-dependency-researcher` / `or-community-researcher` (deposit-aware) | Spawn with `DEPOSIT` appended to the prompt. The agent writes findings to `<DEPOSIT>` and SendMessages `RESEARCH_DONE: <path>`. Forward `Research <name> done: <path>` to the phase agent, then shut the researcher down. NEVER open the findings file. |
| `AGENT` is any other subagent_type (`dependency-researcher`/`community-researcher`/`Plan`/`Explore`/`general-purpose`, …) | Wrap: spawn `general-purpose` as a background teammate with a prompt that imitates the requested agent's style + writes to `<DEPOSIT>` + SendMessages `RESEARCH_DONE: <path>` (or spawn the requested agent directly if it already has `Write` + `SendMessage`). Shut it down after relay. |

If a `SPAWN_RESEARCH` omits `DEPOSIT`, reject it: SendMessage the phase agent `SPAWN_RESEARCH rejected — DEPOSIT is required.` and take no further action on that request. Otherwise SendMessage `Spawned: <name>`. Treat the returned `RESEARCH_DONE`/`RESEARCH_BLOCKED` as a protocol token — extract the first such line, discard the rest (do NOT relay, echo, or store); if neither token is present, SendMessage the phase agent `Research <name> protocol violation — researcher returned non-protocol output, inspect <best-effort-path-or-none>` and proceed. Full mechanics: `assets/spawn-protocol.md`.

## Phase Transitions & Idle Taxonomy

Every wake-up falls into one of two buckets — **action required** or **idle**. Idle wake-ups produce **no output and no tool calls**; end the turn empty. Reflexive `Standing by.` on an idle wake-up is the discipline violation this skill exists to prevent.

| Wake-up source | Bucket | Manager response |
|---|---|---|
| `SPAWN` (supervisor) | Action | Spawn worker; reply `Spawned: <name>` |
| `SPAWN_RESEARCH` (phase agent) | Action | Spawn researcher; reply `Spawned: <name>` |
| `RESEARCH_DONE` / `RESEARCH_BLOCKED` (research teammate) | Action | Relay `Research <name> done: <path>`, then shut the researcher down |
| `SHUTDOWN` (supervisor) | Action | Issue `shutdown_request` to the named worker; no reply |
| Phase agent `<PHASE>_COMPLETE` (`BRAINSTORM_COMPLETE` / `PLAN_COMPLETE`) | Action | Shut the phase agent down; spawn the next-phase agent. For `PLAN_COMPLETE`: first surface the go-ahead and await the user's approval, *then* spawn the supervisor |
| Phase agent `<PHASE>_HANDOVER` | Action | Execute the phase-handover protocol (Handover Ladder) |
| Phase agent / supervisor `PHASE_PAUSE` / PAUSE | Action | Relay one short paragraph (action + impact) to the user; after approval reply `PROCEED` / `REJECTED — reason: <line>` |
| Phase agent `PHASE_ABORT` | Action | Surface `Phase agent reports abort. Confirm by typing 'exit'; otherwise the phase continues.`; on confirm, shut the phase agent down and end the session cleanly |
| Supervisor `ITERATION N — STOPPED_FOR_HANDOVER / COMPLETED` | Action | Execute the iteration-handover protocol |
| User message addressed to the manager during phase 1/2 | Action | Reply ONCE with the redirect nudge; do not relay |
| Worker/research boot, `shutdown_response`, termination; supervisor turning internally; teammate progress; hook/system reminders; phase-agent ↔ user dialogue events | Idle | No output, no tool calls |

**Plan→implementation go-ahead (the one gated transition).** After `PLAN_COMPLETE` (modes `idea`/`spec`), before spawning the supervisor, surface a single line — e.g. `Plan approved at <path>. Start implementation? It will run multiple tasks autonomously.` — and wait for the user's go-ahead. This gates only this one expensive, hard-to-pause transition; it does NOT gate any normal in-flow action (local commits the underlying skills make stay ungated). Mode `plan` has no such gate — invoking the command with a plan path is itself the go-ahead, so spawn `or-supervisor-1` directly.

**The redirect nudge (the only manager→user utterance permitted mid-phase).** If a user message lands on the manager during phase 1/2 (it was meant for the phase agent), reply exactly once — `<phase-agent> is driving — send your messages to it directly (switch with Shift+Down).` — and do NOT relay it.

**PAUSE relay.** Phase agents and the supervisor may request a PAUSE for actions **beyond** the normal workflow — genuinely destructive or visible-to-others operations (a `git push`, deleting files outside the worktree, an external API call). Relay one short paragraph (action + impact only — no commit lists, no narration). Local commits the underlying skills perform are NOT a pause case.
