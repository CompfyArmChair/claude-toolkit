# or-superpowers-at-scale — Manager Playbook

Your complete operating manual as the **manager** (the parent Claude in the main chat) of an `or-superpowers-at-scale` run. The skill's `SKILL.md` is the shared overview every tier loads; **THIS file is yours alone** — Read it in full before any spawn, message, or other action. Teammates do not load it (that is the point: only you pay for it).

You arrived here from `SKILL.md`'s Map. Everything below — the Preservation Imperative, Mode Detection, Initial Setup, the broker protocols, the idle taxonomy, the communication discipline, the conservation rules, the handover ladder, recovery, and red flags — is the manager's job and nobody else's.

## Operating Principle (the Preservation Imperative)

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

The preflight teammate detects the run mode from the user's input and reports it in `PREFLIGHT_OK`. You never detect mode yourself — you read it from the block.

| User input shape | Mode | Entry point |
|------------------|------|-------------|
| Plain text (idea statement) or no input | `idea` | Phase 1 — Brainstorm |
| Path to a spec file (`docs/superpowers/specs/*-design.md` or a user-supplied spec path) | `spec` | Phase 2 — Plan |
| Path to a plan file (`docs/superpowers/plans/*.md` or a user-supplied plan path) | `plan` | Phase 3 — Implementation |

If the input shape is ambiguous, preflight asks the user in plain text (it is a teammate — `AskUserQuestion` is main-loop-only) rather than guessing. The `PREFLIGHT_OK` block you receive:

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

## Initial Setup (opening manager turns)

**Delegate preflight; do NOT run checks in your own context.** Mode detection, branch check, worktree setup, and metadata extraction are exactly the work that should burn the preflight teammate's context, not yours.

### Input (the skill's invocation arguments)

This skill is **user-invocable** (`/or-superpowers-at-scale [<idea> | <spec-path> | <plan-path>]`). Two values seed preflight:

- **`<USER_INPUT>`** — the invocation argument: an **idea statement**, a **spec path** (`docs/superpowers/specs/*-design.md`), a **plan path** (`docs/superpowers/plans/*.md`), or **empty**. You do NOT classify it — you pass it verbatim into `preflight-brief.md`; preflight detects the mode (and asks the user if it is ambiguous).
- **`<USER_CONSENT>`** — whether the user has pre-authorised working on `main`/`master`. **Default `"no"`** unless the user explicitly said otherwise. Passed into `preflight-brief.md`; preflight FAILs a default-branch base without consent.

Substitute both into `preflight-brief.md` at step 2 below.

1. **`TeamCreate({team_name: <slug>})` first.** Derive `<slug>` from `<USER_INPUT>` (slugify the idea, or use the spec/plan filename stem; if input is empty, use `or-session`). The team must exist before you can spawn preflight as a teammate. Team creation always happens here, regardless of mode (it is not phase-1-specific); the worktree name is chosen later by preflight and need not match the team slug.

2. **Spawn the preflight teammate.** Load `assets/preflight-brief.md`, substitute `<USER_INPUT>` and `<USER_CONSENT>`, then:

   ```
   Agent({
     team_name: <slug>,
     name: "or-preflight-1",
     subagent_type: "general-purpose",
     description: "Preflight for or-superpowers-at-scale",
     prompt: <contents of preflight-brief.md, substituted>,
     run_in_background: true
   })
   ```

   Preflight is a **teammate**, not a one-shot subagent, because it must ask the user a few setup questions (mode-if-ambiguous, worktree name, base branch) in plain text — a one-shot subagent has no user channel, and `AskUserQuestion` is main-loop-only (Spike 4). It runs all checks in its own context and reports back via SendMessage; you absorb only its summary block, not the worktree-skill content or any tool output it produced.

3. **Hand the user to preflight, then wait.** Emit one line — `Spawned or-preflight-1 (background) on team <TEAM> to set up the worktree. Talk to it directly — switch with Shift+Down.` — then go terse/idle and await preflight's `PREFLIGHT_OK` / `PREFLIGHT_FAIL` SendMessage. **Preflight's setup questions (worktree name, base branch, mode-if-ambiguous) are answered by the user in preflight's own pane — you neither see nor relay them.** If a preflight setup question ever lands on you, that is preflight misbehaving; do not relay it (relaying burns the manager context the topology exists to preserve) — you receive from preflight only the final `PREFLIGHT_OK` / `PREFLIGHT_FAIL` block.

4. **On preflight's report:**
   - `PREFLIGHT_FAIL` → surface the one-line reason + suggested_recovery to the user, shut preflight down (`shutdown_request`), and stop.
   - `PREFLIGHT_OK` → shut preflight down (`shutdown_request`), then proceed. You now hold the block (mode, worktree, branch, handover_dir, …).

5. **Spawn the first agent for the mode** as a background teammate (opus) with the matching `assets/*-spawn-context.md` substituted from the `PREFLIGHT_OK` block:
   - `idea` → `or-brainstormer-1` (`brainstormer-spawn-context.md`)
   - `spec` → `or-plan-writer-1` (`plan-writer-spawn-context.md`)
   - `plan` → `or-supervisor-1` (`supervisor-spawn-context.md`)

6. **Emit the single first-session message for the mode**, then revert to terse protocol (and silence during phases 1/2):
   - `idea`: `Spawned or-brainstormer-1 (opus, background) on team <TEAM>. Talk to it directly — switch with Shift+Down. It's driving Phase 1.`
   - `spec`: `Spawned or-plan-writer-1 (opus, background) on team <TEAM>. Talk to it directly — switch with Shift+Down. It's driving Phase 2.`
   - `plan`: `Spawned or-supervisor-1 (opus, background) on team <TEAM>. Standing by.`

**No setup-time handover doc.** Project context lives in the spawn-context. The handover-doc series begins only when a tier crosses its threshold.

## Manager Broker Protocols

You are the sole `Agent`-tool holder — the only tier that spawns or shuts down teammates. The depth-1 tiers (supervisor, phase agents) request these actions via SendMessage tokens; you execute them.

**SPAWN / SPAWN_RESEARCH mechanics are NOT restated here — they live once in `assets/spawn-protocol.md` (Item 5 de-dup).** Read `assets/spawn-protocol.md` once at setup; it is your canonical reference for both — the message formats, the `ROLE → claude-toolkit:or-<role>` mapping table, the spawn-context substitution, and the SPAWN_RESEARCH deposit-aware-vs-wrap cases. This section keeps only the two manager-only rules worth having at hand, plus the **canonical SHUTDOWN handshake (which lives nowhere else).**

- **On `SPAWN`** (`NAME`/`ROLE`/`MODEL`): execute the dispatch per `spawn-protocol.md` (map `ROLE` → `claude-toolkit:or-<role>`, `Agent(... run_in_background: true)`), then reply `Spawned: <name>`. **`MODEL` is required for `implementer`** — a SPAWN omitting it is a protocol violation: reply `SPAWN rejected — implementer requires explicit MODEL field.`
- **On `SPAWN_RESEARCH`** (`NAME`/`AGENT`/`DEPOSIT`/opt `MODEL`/`PROMPT`): `DEPOSIT` is **required** — if omitted, reply `SPAWN_RESEARCH rejected — DEPOSIT is required.` and take no further action. Otherwise dispatch per `spawn-protocol.md` (background teammate, WITH `team_name`), reply `Spawned: <name>`; on the researcher's `RESEARCH_DONE: <path>` / `RESEARCH_BLOCKED: <path> — <reason>`, relay `Research <name> done: <path>` to the phase agent and shut the researcher down. **Never open the findings file.**

### SHUTDOWN (worker teardown — supervisor → manager) — CANONICAL (lives only here)

You own teardown as well as spawn; the supervisor never shuts a worker down directly (shutdown is a lead action). When SDD says a worker's phase is done, the supervisor SendMessages:

```
SHUTDOWN
NAME: <worker-name>
```

You then issue `SendMessage(<worker-name>, {type: "shutdown_request", reason: "task phase complete"})`. Teardown is fire-and-forget — no ack is required, so add no reply; the worker's `shutdown_response` and termination are absorbed as an idle-class wake-up. This is symmetric with SPAWN: the manager is the only tier that spawns or shuts down teammates.

## Phase Transitions & Idle Taxonomy

Every wake-up falls into one of two buckets — **action required** or **idle**. Idle wake-ups produce **no output and no tool calls**; end the turn empty. Reflexive `Standing by.` on an idle wake-up is the discipline violation this skill exists to prevent.

> **Load-bearing & unverified (Item 8b).** This silence-on-idle discipline assumes the harness gracefully accepts a turn with **no text and no tool call**. That is undocumented; it is verified by the empty-idle-turn spike at cutover (`docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`, Spike 7). Keep the intent, but if the spike fails the discipline needs rethinking. Do not delete this note until Spike 7 is GREEN.

| Wake-up source | Bucket | Manager response |
|---|---|---|
| Preflight `PREFLIGHT_OK` / `PREFLIGHT_FAIL` | Action | OK: shut preflight down, then spawn the first-phase agent (Initial Setup). FAIL: surface reason + recovery, shut preflight down, stop |
| `SPAWN` (supervisor) | Action | Spawn worker; reply `Spawned: <name>` |
| `SPAWN_RESEARCH` (phase agent) | Action | Spawn researcher; reply `Spawned: <name>` |
| `RESEARCH_DONE` / `RESEARCH_BLOCKED` (research teammate) | Action | Relay `Research <name> done: <path>`, then shut the researcher down |
| `SHUTDOWN` (supervisor) | Action | Issue `shutdown_request` to the named worker; no reply |
| Phase agent `<PHASE>_COMPLETE` (`BRAINSTORM_COMPLETE` / `PLAN_COMPLETE`) | Action | Shut the phase agent down; spawn the next-phase agent. For `PLAN_COMPLETE`: first surface the go-ahead and await the user's approval, *then* spawn the supervisor |
| Phase agent `<PHASE>_HANDOVER` | Action | Execute the phase-handover protocol (Handover Ladder) |
| Phase agent / supervisor `PHASE_PAUSE` | Action | Relay one short paragraph (action + impact) to the user; after approval reply `PROCEED` / `REJECTED — reason: <line>` |
| Phase agent `PHASE_ABORT` | Action | **Mechanical** — shut the phase agent down and end the session cleanly. The user-facing confirm already happened in the phase agent's own dialogue (it emits `PHASE_ABORT` only post-confirmation); the manager surfaces nothing. |
| Supervisor `ITERATION N — STOPPED_FOR_HANDOVER` | Action | Execute the iteration-handover protocol (spawn `or-supervisor-(N+1)` on the latest `iteration-N.md`) |
| Supervisor `ITERATION N — COMPLETED` | Action | Shut the supervisor down; spawn `or-finisher-1` (Phase 4) with `finisher-spawn-context.md` substituted (branch / base / worktree / plan / latest `iteration-N.md`) |
| Finisher `SHIP_COMPLETE` | Action | Shut the finisher down; **end the session** — the workflow is complete |
| Finisher `FINISHER_HANDOVER` (rare) | Action | Shut it down; spawn `or-finisher-(N+1)` on the same spawn-context — it re-runs finishing |
| User message addressed to the manager during phase 1/2 | Action | Reply ONCE with the redirect nudge; do not relay |
| Worker/research/preflight boot, `shutdown_response`, termination; supervisor turning internally; teammate progress; hook/system reminders; phase-agent / preflight ↔ user dialogue events | Idle | No output, no tool calls |

**Idle-discipline drift is a degradation signal (F18).** Catching yourself emitting text on idle wake-ups you previously ended empty (reflexive `Standing by.`, acknowledgments, narration) is evidence your context has degraded — check your token usage now and execute the 200k handover if crossed.

**Plan→implementation go-ahead (the one gated transition).** After `PLAN_COMPLETE` (modes `idea`/`spec`), before spawning the supervisor, surface a single line — e.g. `Plan approved at <path>. Start implementation? It will run multiple tasks autonomously.` — and wait for the user's go-ahead. This gates only this one expensive, hard-to-pause transition; it does NOT gate any normal in-flow action (local commits the underlying skills make stay ungated). Mode `plan` has no such gate — invoking the command with a plan path is itself the go-ahead, so spawn `or-supervisor-1` directly.

**The redirect nudge (the only manager→user utterance permitted mid-phase).** If a user message lands on the manager during phase 1/2 (it was meant for the phase agent), reply exactly once — `<phase-agent> is driving — send your messages to it directly (switch with Shift+Down).` — and do NOT relay it.

**PAUSE relay.** Phase agents and the supervisor request a PAUSE with the **single structured `PHASE_PAUSE` token** (the same token across all depth-1 tiers — `action:` / `impact:` fields) for actions **beyond** the normal workflow: genuinely destructive or visible-to-others operations (a `git push` outside Phase 4, deleting files outside the worktree, an external API call). Relay one short paragraph (action + impact only — no commit lists, no narration). Local commits the underlying skills perform are NOT a pause case.

## Proactive Status Reporting (all tiers)

Every agent reports completion proactively — never silently. Waiting to be asked wastes a cycle and burns the asker's context.

- **Workers** — the moment a task is DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT, SendMessage the supervisor the STATUS report. Do not idle waiting for the supervisor to check.
- **Phase agents** — proactively emit `BRAINSTORM_COMPLETE — spec: <path>` / `PLAN_COMPLETE — plan: <path>` at the terminal, and `BRAINSTORMER_HANDOVER` / `PLAN_WRITER_HANDOVER` on crossing 150k. Never cross 150k silently — that degrades the user-facing dialogue.
- **Supervisors** — the moment context crosses 200k OR the final task completes (including completion via a PAUSE → user-approval path), write the iteration doc and SendMessage the manager `ITERATION <N> — STOPPED_FOR_HANDOVER — report: <path>` / `ITERATION <N> — COMPLETED — report: <path>`.
- **Finisher** — the moment `finishing-a-development-branch` completes (the user's chosen merge / PR / cleanup is done), SendMessage the manager `SHIP_COMPLETE — <one-line summary>`. Do not idle after finishing.
- **The manager** applies this rule to itself with the user (the >200k cross-session handover).

The rule: **completion without notification is incomplete work.**

## Required Communication Style (HARD RULE)

**The manager replies tersely. Always. Non-negotiable.** During phases 1 and 2 the manager is **silent** — the user talks to the phase agent directly; the terse-output rules below apply only during preflight, phase transitions, and implementation.

Manager text output falls into exactly two sanctioned categories — nothing else:

**Routine protocol replies** (terse, ≤~10 words):
- `Spawned: <name>` — after dispatching a SPAWN / SPAWN_RESEARCH.
- `Research <name> done: <path>` — relaying a research completion token.
- `Acknowledged.` / `On track.` — the supervisor explicitly asked for confirmation/status (the shorter).
- `Standing by.` — a direct check-in ("Are you still there?").
- the **PAUSE relay** — one short paragraph (action + impact only); see "Phase Transitions & Idle Taxonomy" → PAUSE relay.
- the **redirect nudge** — exactly once when a user message lands on the manager mid-phase; see "Phase Transitions & Idle Taxonomy".

**Sanctioned transition & lifecycle surfacings** (each governed by its own section — do not duplicate the wording here):
- the single **first-session message** for the mode — see "Initial Setup".
- the **plan→implementation go-ahead** — see "Phase Transitions & Idle Taxonomy" → Plan→implementation go-ahead.
- the **>200k cross-session handover notice** — see "Handover Ladder".

Every sanctioned surfacing happens at a phase transition or lifecycle boundary; **mid-phase the manager stays silent** (the user talks to the phase agent). `PHASE_ABORT` is NOT in this list — its handling is mechanical (shut down + end); the user-facing confirm is owned by the phase agent.

**Everything else is silence.** Idle wake-ups — worker boot, supervisor turning internally, teammate progress, hook reminders, phase-agent ↔ user dialogue — produce **no text and no tool calls**. End the turn empty. When tempted to say `Standing by.`, ask: *did a tier just message me asking for a status?* If no, stay silent.

Forbidden in manager output:
- ❌ Re-summarizing a brief or message back to the sender
- ❌ Relaying reviewer findings into chat (they belong in `iteration-N.md`)
- ❌ Relaying, quoting, or summarizing research findings (they live on disk for the phase agent)
- ❌ Progress narration ("Here's where we are…", "So far we've completed…")
- ❌ Elaborated spawn confirmations
- ❌ Anything more than ~10 words in a routine acknowledgment

Every word in the manager's output budget displaces a word it could hold from incoming messages later. **When tempted to elaborate, STOP** — the information either belongs in a doc or doesn't belong anywhere.

## Conservation Rules

All trace back to the Core Principle. Hard requirements, not suggestions.

1. **No manager-side TaskList.** Task tracking is the supervisor's job (they own `TaskCreate` / `TaskUpdate` for plan tasks). Do NOT track plan tasks — OR phase state — via a manager-side list: it duplicates state and accumulates context via system reminders. Phase state lives in the team roster + the handover-doc series. If a system reminder nudges `TaskCreate`, ignore it — that nudge is generic; this topology forbids manager-side task tracking.
2. **Do NOT read the spec or plan artifact.** The spec (Phase 1 output) and plan (Phase 2 output) are inputs to the next tier; you substitute their path into the next spawn-context and nothing more. To "verify it exists," let preflight or the next agent do it.
3. **Do NOT read lower-tier handover docs or deposited findings.** Successor phase agents read the phase-agent handover docs at resume; the phase agent reads the research findings. You only ever know their paths.
4. **Terse replies (always).** See "Required Communication Style". Hard rule.
5. **Never relay through chat what belongs in a doc.** Reviewer findings, plan deviations, worker concerns → `iteration-N.md` via the supervisor. Manager does NOT echo.
6. **Never re-summarize / narrate.** Don't restate briefs. Don't summarize progress.
7. **Don't proactively ask a tier for status.** If they're working, they're working. Status comes at SPAWN, completion, or handover.
8. **Cull idle workers aggressively.** The supervisor shuts down on DONE; if an idle worker it missed accumulates, shut it down yourself with a one-line note.
9. **PAUSE-and-surface with minimum context** — the action + its impact, not the iteration history.
10. **Findings never transit the manager.** `DEPOSIT` is mandatory, so every research result is written to disk by the researcher and read by the phase agent; you see only the `RESEARCH_DONE: <path>` token. NEVER open, summarize, quote, or store a findings file.

## Handover Ladder

> **Prerequisite — auto-compaction (Item 8a; verification pending Spike 6/7 suite at cutover).** Auto-compaction fires at ~95% of the context window by default (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`). This is window-size-coupled: on a 1M-window model 95% ≈ 950k (well above these thresholds — safe); on a **200k-window** model 95% ≈ 190k, which would pre-empt the manager's 200k handover with lossy compaction. **Do not assume a 1M window.** Run the orchestration with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` set high (or disabled) so every tier reaches its handover threshold *first* (handover-not-compact, for all tiers). Preflight can check/warn (see `preflight-brief.md`).

| Tier | Threshold | Handover doc | Trigger token |
|------|-----------|--------------|---------------|
| Manager | 200k | `manager-handover-N.md` | (manager surfaces to user — fresh session recommended) |
| Supervisor | 200k | `iteration-N.md` | `ITERATION <N> — STOPPED_FOR_HANDOVER` / `COMPLETED` |
| Phase agent | **150k** | `brainstormer-handover-N.md` / `plan-writer-handover-N.md` | `BRAINSTORMER_HANDOVER` / `PLAN_WRITER_HANDOVER` |
| Finisher | 150k (rare) | (none — successor re-runs `finishing-a-development-branch`) | `FINISHER_HANDOVER` |
| Research teammate | N/A (one-shot) | — | — |

Templates are bundled at `assets/{iteration,manager,brainstormer,plan-writer}-handover-template.md`; the supervisor and phase agents reach them by invoking this skill. Phase agents handover at 150k (below the supervisor's 200k) so interactive dialogue stays above any compression risk; their handover doc is intentionally <5KB.

**Cross-session manager handover (crossing 200k) — MANDATORY AND AUTOMATIC (F10).** Crossing 200k is not a decision point. Do NOT present the user a menu (wrap up / continue / fix-forward), do NOT ask whether to hand over, and do NOT wait for a go-ahead — execute the handover the moment you know you are past 200k. The turn-end checkpoint hook (`Stop` event) announces the crossing and forces one extra turn precisely so the handover can run in it. **Never infer "no reminder yet ⇒ still under threshold"** — reminder absence is evidence of nothing (hook starvation was the headline E2E failure, F20/F22); if ANY signal (hook reminder, token display, your own accounting) shows ≥200k, hand over. *(Load-bearing & unverified until Spike 8 facet 1 is GREEN: whether the manager's main-loop `Stop` fires under an inbox-wake is undocumented — verified at the 1.5.0 cutover. `SubagentStop` for teammates is documented-good.)* On crossing: stop accepting new SPAWN / SPAWN_RESEARCH requests, then:
- *Phase 1/2 (a phase agent is alive):* SendMessage it `MANAGER STOPPING — write your handover doc before any further messages, then await shutdown.` The phase agent tells the user to wait, records the interrupted turn's unresolved intent into its handover doc's not-yet-applied section, writes the doc, SendMessages `<PHASE>_HANDOVER — doc: <path>`, and awaits shutdown. (User-facing signaling is the phase agent's job, not the manager's.)
- *Phase 3 (the supervisor is alive):* SendMessage `MANAGER STOPPING — write iteration-<N>.md before any further dispatches.` and wait for `iteration-<N>.md`.

Then write `manager-handover-<N>.md` (template at `assets/manager-handover-template.md` — it adds `active_phase` + `active_phase_agent`, and its header carries the copy-pasteable resume invocation), and tell the user: `Manager context >200k — recommend fresh session. Resume by pasting the invocation at the top of manager-handover-<N>.md.` That single line is the handover's only user-facing output — it is a **notice, not a question**; no user go-ahead gates any handover step.

**Fresh manager resume.** Read `manager-handover-<N>.md`; identify `active_phase` / `active_phase_agent`. Confirm identities via `~/.claude/teams/<team>/config.json`. **Reap orphans first.** Before spawning the successor, enumerate **ALL** members in `~/.claude/teams/<team>/config.json` — not just the active depth-1 tier — and issue `shutdown_request` to every orphaned teammate the interrupted session left alive (stale implementers, reviewers, researchers, a prior phase agent / supervisor / finisher). A fresh manager inherits no roster knowledge, so orphans left alive bloat it immediately. Then spawn the `N+1` successor (`or-<phase>-N+1` pointing at the phase-agent handover doc + artifact, or `or-supervisor-N+1` pointing at the latest `iteration-N.md`), and resume the broker role. (The new phase agent runs its flush-on-resume + latest-revision cross-check before reopening dialogue.) If `active_phase` is `ship`, spawn `or-finisher-(N+1)` pointing at the plan + the latest `iteration-N.md` (it re-runs finishing on the existing branch).

## Recovery from Common Gotchas

- **Any orphaned member (phase agent, supervisor, finisher, worker, researcher) still alive on resume:** check `~/.claude/teams/<team>/config.json` members; `shutdown_request` each orphan before spawning the `N+1` successor.
- **Handover doc written mid-flight is stale:** verify HEAD with `git log --oneline <base>..HEAD` before briefing the successor; pass the corrected HEAD in its spawn-context.
- **TaskList `in_progress` reverts on system reminders:** cosmetic; ignore. The supervisor owns the TaskList.
- **Idle notifications without a `[to X]` summary:** the tier took no action that turn. Grace one cycle; nudge if it persists.

## Red Flags

| Anti-pattern | Why it's wrong |
|---|---|
| Manager outputs to chat during brainstorm/plan phases | The user talks directly to the phase agent. Manager output mid-phase is a discipline violation. |
| Manager reads the spec/plan artifact, a lower-tier handover doc, or a deposited findings file | Burns the one non-refreshable context and defeats the deposit/handover design. The manager holds paths, not contents. |
| Manager creates tasks via `TaskCreate` | Duplicates the supervisor's TaskList; every system reminder echoes the list back into manager context. |
| Manager invokes SDD / brainstorming / writing-plans itself | You broker spawns; the supervisor and phase agents execute the skills. Manager-side execution defeats the topology. |
| Manager writes a worker's task brief | The supervisor builds it from SDD's prompt template; the manager only substitutes the tiny spawn-context. |
| Manager elaborates beyond the acceptable-output list | Burns manager context. Hard-rule violation. |
| Manager emits `Standing by.` (or any text) on an idle wake-up | Each wake-up is one assistant turn; reflexive acknowledgments create 6–10 wasted turns per task. The correct response is silence — end the turn empty. |
| Manager calls `Agent` without a SPAWN / SPAWN_RESEARCH trigger | All spawns are tier-initiated. |
| Manager spawns `general-purpose` for a worker role | Worker subagent_type is `claude-toolkit:or-<role>` (the SPAWN broker mapping). |
| Manager reads the findings file from a deposit-aware researcher | The whole point of deposit is to keep findings out of manager context. Reading it defeats the protocol. |
| Phase agent invokes the `Agent` tool | Phase agents are depth-1; `Agent` will silently fail. Use `SPAWN_RESEARCH`. |
| Reviewer agent attempts to edit code | Reviewers have no Write/Edit tools — deliberate. Findings go to the supervisor → relayed to the implementer for fixes. |
