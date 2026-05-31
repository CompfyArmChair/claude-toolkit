# `or-superpowers-at-scale` — Plan 4: Manager-Discipline `SKILL.md` Body + Command Wrapper + Suite Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The `SKILL.md`-body and command-authoring steps are also governed by **superpowers:writing-skills** — load it before authoring. The final release step is governed by **superpowers:finishing-a-development-branch** — load it before integrating/pushing.

**Goal:** Append the manager-discipline operating body to the Plan-2 `SKILL.md` skeleton (the orchestrator's complete manager playbook — Core Principle, Mode Detection, Initial Setup, the manager-side SPAWN / **SHUTDOWN** / SPAWN_RESEARCH broker protocols, Phase Transitions & Idle Taxonomy, Proactive Status Reporting, Required Communication Style, Conservation Rules, the Handover Ladder, Recovery, Red Flags, and a Protocol & Template Reference that surfaces the bundled `assets/*`), author the optional `commands/or-superpowers-at-scale.md` thin wrapper, and ship the whole suite as a single minor release (`1.1.1 → 1.2.0` across both manifests + README + an approval-gated push) — so the orchestrator becomes behaviorally complete on the branch and, on the user's go-ahead, live for users.

**Architecture:** The `SKILL.md` body is appended **additively** to the Plan-2 skeleton (whole, complete sections after `## Integration with Other Skills`; no stub-and-fill, no "TBD"/"Plan 4" markers) — split across two tasks so each commit leaves the file structurally valid. The manager-discipline content **PRESERVES** the legacy `subagent-driven-development-at-scale/SKILL.md` sections (Core Principle, Proactive Status Reporting, Required Communication Style, Conservation Rules, Recovery, Red Flags) with `or-*` naming updates and the orchestrator's additions (phase-agent silence, deposit-opacity, the redirect nudge), and inlines the design's NEW manager-facing sections (Mode Detection, the broker protocols including the **canonical SHUTDOWN handshake deferred here from Plan 3**, the Idle Taxonomy, the Handover Ladder, the asset-surfacing reference). The command wrapper mirrors the plugin's existing skill-wrapping commands (no frontmatter; `# /cmd` + `## Process`; invokes the skill). The release is the suite's single user-visible increment, gated on explicit user approval.

**Tech Stack:** Claude Code plugin components — a Markdown `SKILL.md` (appended), a Markdown command file, and JSON manifests, inside the `claude-toolkit` plugin repo (`I:\Dev\claude-toolkit`, real git). No compiled code. In-session verification is structural (`claude plugin validate` + content greps); all behavioral validation is deferred to suite cutover against the *installed* plugin (Plan 2's behavioral-spikes doc). Per-task `git commit` is the rollback boundary; the final task performs the release push on approval.

---

## Scope of this plan (Plan 4 of 4 — the final plan)

This is the **manager-discipline + release** plan of the `or-superpowers-at-scale` suite (design: `docs/superpowers/specs/2026-05-24-or-superpowers-at-scale-design.md`, authoritative; see esp. **Plugin Packaging** → "Release discipline" + "Cutover & end-state validation", **Mode Detection**, **Protocols** (SPAWN / **SHUTDOWN** / SPAWN_RESEARCH), **Handover Ladder**, **Manager Context Discipline**, **Red Flags**, **Manager definition tightening**, **Clarifications**, and impl-note **#8**). It completes the orchestrator skill the Plan-2 skeleton started and the Plan-3 assets reference, then ships the suite.

In scope:
- **Append the manager-discipline body** to `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md` (Tasks 1–2; the skeleton already exists from Plan 2).
- **Author the command wrapper** → `plugins/claude-toolkit/commands/or-superpowers-at-scale.md` (Task 3, NEW).
- **Suite release edits** (Task 4): `plugin.json` version `1.1.1 → 1.2.0` + description; `marketplace.json` `metadata.version` + `plugins[].version` → `1.2.0` + `plugins[].description` sync; `README.md` component listing.
- **Suite-wide self-review** (Task 5) and **approval-gated release/push** (Task 6 — the suite release).

Out of scope (suite cutover — post-release, against the installed plugin):
- **Execution of the behavioral spikes** (Plan 2's `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`) — the in-body `Skill()` load (incl. whether a teammate's `Skill('claude-toolkit:or-superpowers-at-scale')` invocation reaches the bundled `assets/*`), terminal-override, anti-drift-resume, `AskUserQuestion` surfacing, and teammate task-tool spikes.
- **Removing the deprecated loose `~/.claude` copies** and `claude plugin install claude-toolkit` (design §"Cutover & end-state validation"; the spikes doc's "Cutover checklist").

**Suite-order assumption:** the suite executes Plan 1 → 2 → 3 → 4 in order via `/implement-from-plan`. At Plan 4 start, Plan 2 has created `skills/or-superpowers-at-scale/SKILL.md` (skeleton, ending after `## Integration with Other Skills`) and Plan 3 has authored every `assets/*` file the body below references. Plan 4 modifies the skeleton (append-only), adds one command, edits the two manifests + README, and pushes. It does not touch any agent or asset file.

## Git workflow (READ FIRST)

`I:\Dev\claude-toolkit` **is a real git repository** (verified). All work happens on the existing feature branch **`or-superpowers-at-scale`** with **one commit per task** (design §"Git workflow"). The real-git review/rollback loop is the SDD rollback boundary.

- The working directory is `C:\Users\marti\.claude` (a different drive from the repo). **Every git command targets the repo explicitly via `git -C I:\Dev\claude-toolkit …`** — do not rely on the ambient cwd, and do not `cd` (it can trigger a permission prompt).
- Tasks 1–5 commit locally only. **Do NOT `git push` until Task 6**, and in Task 6 only after **explicit user approval** — the push *is* the suite release (design handover; spec §"Release discipline").

## Release execution (this plan flips Plans 1–3's deferral)

Plans 1–3 deliberately made **no** version / manifest / README change — nothing was user-visible until this release. Plan 4 is where that single `1.1.1 → 1.2.0` minor increment lands (design §"Plugin Packaging" → "Release discipline"): the version bump + both `marketplace.json` versions + the README listing happen **once**, in Task 4; the integration/push happens **once**, in Task 6, on the user's explicit go-ahead. There is no per-plan bump anywhere in the suite.

## Verification approach (structural in-session; behavioral at cutover)

The `claude-toolkit` marketplace is **not installed in the authoring session** (design handover; confirmed in Plans 1–3), so `Skill('claude-toolkit:or-superpowers-at-scale')` would not resolve the file being written and the `claude-toolkit:or-*` subagent types are not registered. **Plan 4's hard gates are therefore structural** — `claude plugin validate` + content greps run against the repo files, plus JSON-shape checks on the manifests. **Every behavioral check is deferred** to suite cutover against the *installed* plugin — the five spikes in Plan 2 (incl. impl-note #3's reframed question: *when a teammate invokes `Skill('claude-toolkit:or-superpowers-at-scale')`, can it reach the skill's bundled `assets/*` content?*) plus Plan 1's wrapper check. If `claude` is unavailable in-session, record the skip explicitly and rely on the greps — never claim a `validate` pass that did not run.

## Progressive assembly of `SKILL.md` (this plan completes it)

Per impl-note #8's split, the orchestrator `SKILL.md` is assembled across the suite: **Plan 2** wrote the skeleton (frontmatter + Goal + When-to-Use + Architecture + Integration); **Plan 3** wrote the `assets/*` it references; **Plan 4 (this plan)** appends the operating-discipline body. This is **additive** assembly, not stub-and-fill — the skeleton ended cleanly after `## Integration with Other Skills`, and Tasks 1–2 append **whole, complete sections** after it. At every commit the file parses, the frontmatter is unchanged (`name` + `description` only), and every section present is complete (no `TBD`, no "added later", no `Plan 4` markers). After Task 1 the file holds the manager's operating mechanics (sections 1–5); after Task 2 it holds the full playbook (sections 1–12). The skill becomes **behaviorally complete** here and **live** only at install (cutover).

## Source-of-truth references

| Artifact being built | Source content | Notes |
|---|---|---|
| `SKILL.md` §§ Core Principle, Proactive Status Reporting, Required Communication Style, Conservation Rules, Recovery, Red Flags | Legacy `subagent-driven-development-at-scale/SKILL.md` (PRESERVE) + design §"Manager Context Discipline" + §"Red Flags" | Inlined in full in Tasks 1–2 with `or-*` naming + the orchestrator additions. |
| `SKILL.md` §§ Mode Detection, Initial Setup, Manager Broker Protocols, Phase Transitions & Idle Taxonomy, Handover Ladder, Protocol & Template Reference | Design §"Mode Detection", §"Phase flow" Phase 0, §"Protocols" (SPAWN / **SHUTDOWN** / SPAWN_RESEARCH), §"Manager definition tightening", §"Clarifications", §"Handover Ladder", §"Asset Inventory" | Inlined in full in Tasks 1–2. **SHUTDOWN's canonical handshake lands here** (Plan 3 deferred it — see Plan 3 §"spawn-protocol.md scope"). |
| `commands/or-superpowers-at-scale.md` | Design §"Plugin Packaging" → "Home & layout" (thin wrapper, mirrors `plan-from-design`) + §"Phase flow" entry line | NEW — inlined in full in Task 3. |
| `plugin.json`, `marketplace.json`, `README.md` | Design §"Plugin Packaging" → "Release discipline" | Edits inlined in full in Task 4. |

All plugin paths are relative to the plugin root `I:\Dev\claude-toolkit\plugins\claude-toolkit\`, except `marketplace.json` and `README.md`, which live at the **repo root** (`I:\Dev\claude-toolkit\.claude-plugin\marketplace.json`, `I:\Dev\claude-toolkit\README.md`). The legacy skill is the PRESERVE source for the discipline sections; it is **not** modified by this plan (it is deprecated at cutover, separately).

---

## Task 1: Append the manager broker + operating sections to `SKILL.md`

Append the first five operating-discipline sections to the Plan-2 skeleton — the manager's "what it does" mechanics: Core Principle, Mode Detection, Initial Setup, the Manager Broker Protocols (SPAWN / **SHUTDOWN** / SPAWN_RESEARCH), and Phase Transitions & Idle Taxonomy. These append after the skeleton's final section (`## Integration with Other Skills`). One cohesive commit; the file stays valid (sections 6–12 follow in Task 2).

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md` (append-only)

- [ ] **Step 1: Load the authoring discipline**

Invoke `Skill('superpowers:writing-skills')` and skim it. Load-bearing here: the body is the skill's content for the model that loads it (the manager); frontmatter stays `name` + `description` only (unchanged from Plan 2); no placeholders/forward-stubs.

- [ ] **Step 2: Confirm the skeleton exists, ends after Integration, and lacks all operating sections (RED)**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
Test-Path $s                                                                          # expect True (Plan 2 created it)
# the skeleton's final section is Integration — nothing operating-discipline yet
Select-String -Path $s -Pattern '^## Integration with Other Skills$' | Select-Object Line
Select-String -Path $s -Pattern '^## Core Principle','^## Mode Detection$','^## Initial Setup','^## Manager Broker Protocols$','^## Phase Transitions'   # expect NO match
# record the current line count (the append must only grow the file)
(Get-Content $s | Measure-Object -Line).Lines                                         # record N0
```
Expected: `True`; the `## Integration with Other Skills` heading present; **no** match for any of the five Task-1 section headers; record `N0`.

- [ ] **Step 3: Append these five sections verbatim to the end of `SKILL.md`**

Append the following after the skeleton's last line (the `- **Followed by:** … finishing-a-development-branch …` bullet under `## Integration with Other Skills`). Do not edit any existing line.

````markdown

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
````

- [ ] **Step 4: Verify the five sections landed, with the load-bearing details, and nothing regressed (GREEN)**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
# all five section headers present
Select-String -Path $s -Pattern '^## Core Principle: Manager Context Is Sacred$','^## Mode Detection$','^## Initial Setup \(first manager turn\)$','^## Manager Broker Protocols$','^## Phase Transitions & Idle Taxonomy$' | Select-Object Line
# the canonical SHUTDOWN handshake landed HERE (Plan 3 deferred it)
Select-String -Path $s -Pattern '^### SHUTDOWN \(worker teardown','SHUTDOWN\b','shutdown_request' | Select-Object Line
# broker invariants: ROLE mapping, DEPOSIT-required, implementer-MODEL rule, idle-taxonomy silence
Select-String -Path $s -Pattern 'claude-toolkit:or-implementer','SPAWN_RESEARCH rejected — DEPOSIT is required','implementer requires explicit MODEL field','No output, no tool calls' | Select-Object Line
# the skeleton is intact: frontmatter + Integration still present; file only grew
Get-Content $s -TotalCount 2 | Select-Object -Last 1                                  # name: or-superpowers-at-scale
Select-String -Path $s -Pattern '^## Integration with Other Skills$' | Select-Object Line
# no placeholders / authoring-plan references
Select-String -Path $s -Pattern 'TBD','TODO','added later','filled in','Plan 4','Plan 3','coming soon'   # expect NO match
(Get-Content $s | Measure-Object -Line).Lines                                         # expect > N0 (grew only)
```
Expected: all five section headers match; the `### SHUTDOWN` heading + `shutdown_request` present; the ROLE mapping, DEPOSIT-required rejection, implementer-MODEL rule, and idle-silence line all present; the frontmatter `name:` and `## Integration with Other Skills` still present; **no** placeholder/plan-reference matches; line count grew beyond `N0`.

- [ ] **Step 5: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes (the skill's frontmatter is unchanged; the body is valid Markdown). If `claude` is unavailable, record the skip and rely on Step 4.

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md
git -C I:\Dev\claude-toolkit commit -m "feat(skills): add or-superpowers-at-scale manager broker + operating sections"
```
Expected: one commit on `or-superpowers-at-scale` modifying only `SKILL.md` (append-only — `git show --stat HEAD` shows additions, zero deletions).

---

## Task 2: Append the manager context-discipline + reference sections to `SKILL.md`

Append the remaining seven sections — the manager's "how it conserves" discipline (mostly PRESERVED from the legacy skill, `or-*`-adapted) plus the asset-surfacing reference: Proactive Status Reporting, Required Communication Style, Conservation Rules, the Handover Ladder, Recovery from Common Gotchas, Red Flags, and Protocol & Template Reference. These append after Task 1's sections, completing the body. One commit.

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md` (append-only)

- [ ] **Step 1: Confirm Task 1's sections are present and these seven are not yet (RED)**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
# precondition: Task 1 landed
Select-String -Path $s -Pattern '^## Phase Transitions & Idle Taxonomy$' | Select-Object Line          # expect match
# these seven are not yet present
Select-String -Path $s -Pattern '^## Proactive Status Reporting','^## Required Communication Style','^## Conservation Rules$','^## Handover Ladder$','^## Recovery from Common Gotchas$','^## Red Flags$','^## Protocol & Template Reference'   # expect NO match
(Get-Content $s | Measure-Object -Line).Lines                                         # record N1
```
Expected: `## Phase Transitions & Idle Taxonomy` present (Task 1 precondition); **no** match for any of the seven Task-2 headers; record `N1`.

- [ ] **Step 2: Append these seven sections verbatim to the end of `SKILL.md`**

Append after Task 1's final line (the `**PAUSE relay.**` paragraph). Do not edit any existing line.

````markdown

## Proactive Status Reporting (all tiers)

Every agent reports completion proactively — never silently. Waiting to be asked wastes a cycle and burns the asker's context.

- **Workers** — the moment a task is DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT, SendMessage the supervisor the STATUS report. Do not idle waiting for the supervisor to check.
- **Phase agents** — proactively emit `BRAINSTORM_COMPLETE — spec: <path>` / `PLAN_COMPLETE — plan: <path>` at the terminal, and `BRAINSTORMER_HANDOVER` / `PLAN_WRITER_HANDOVER` on crossing 150k. Never cross 150k silently — that degrades the user-facing dialogue.
- **Supervisors** — the moment context crosses 200k OR the final task completes (including completion via a PAUSE → user-approval path), write the iteration doc and SendMessage the manager `ITERATION <N> — STOPPED_FOR_HANDOVER — report: <path>` / `ITERATION <N> — COMPLETED — report: <path>`.
- **The manager** applies this rule to itself with the user (the >200k cross-session handover).

The rule: **completion without notification is incomplete work.**

## Required Communication Style (HARD RULE)

**The manager replies tersely. Always. Non-negotiable.** During phases 1 and 2 the manager is **silent** — the user talks to the phase agent directly; the terse-output rules below apply only during preflight, phase transitions, and implementation.

The ONLY situations that warrant manager text output:

- A SPAWN / SPAWN_RESEARCH arrived: reply `Spawned: <name>` after dispatching.
- A research teammate returned a completion token: reply `Research <name> done: <path>` (the only multi-word manager→teammate utterance beyond the three below).
- The supervisor explicitly asked for confirmation/status: reply `Acknowledged.` or `On track.` (the shorter).
- A check-in ("Are you still there?"): reply `Standing by.`
- A PAUSE request: relay one short paragraph for the user — **action + impact only**, no commit lists, no follow-up flags.
- A user message landed on the manager mid-phase: the redirect nudge, exactly once.
- The single first-session message for the mode (≤ ~25 words; see Initial Setup). Mode `plan` keeps the terse `Spawned … Standing by.` form.

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

| Tier | Threshold | Handover doc | Trigger token |
|------|-----------|--------------|---------------|
| Manager | 200k | `manager-handover-N.md` | (manager surfaces to user — fresh session recommended) |
| Supervisor | 200k | `iteration-N.md` | `ITERATION <N> — STOPPED_FOR_HANDOVER` / `COMPLETED` |
| Phase agent | **150k** | `brainstormer-handover-N.md` / `plan-writer-handover-N.md` | `BRAINSTORMER_HANDOVER` / `PLAN_WRITER_HANDOVER` |
| Research teammate | N/A (one-shot) | — | — |

Templates are bundled at `assets/{iteration,manager,brainstormer,plan-writer}-handover-template.md`; the supervisor and phase agents reach them by invoking this skill. Phase agents handover at 150k (below the supervisor's 200k) so interactive dialogue stays above any compression risk; their handover doc is intentionally <5KB.

**Cross-session manager handover (crossing 200k).** Stop accepting new SPAWN / SPAWN_RESEARCH requests.
- *Phase 1/2 (a phase agent is alive):* SendMessage it `MANAGER STOPPING — write your handover doc before any further messages, then await shutdown.` The phase agent tells the user to wait, records the interrupted turn's unresolved intent into its handover doc's not-yet-applied section, writes the doc, SendMessages `<PHASE>_HANDOVER — doc: <path>`, and awaits shutdown. (User-facing signaling is the phase agent's job, not the manager's.)
- *Phase 3 (the supervisor is alive):* SendMessage `MANAGER STOPPING — write iteration-<N>.md before any further dispatches.` and wait for `iteration-<N>.md`.

Then write `manager-handover-<N>.md` (template at `assets/manager-handover-template.md` — it adds `active_phase` + `active_phase_agent`), and tell the user: `Manager context >200k — recommend fresh session. New manager reads manager-handover-<N>.md first.`

**Fresh manager resume.** Read `manager-handover-<N>.md`; identify `active_phase` / `active_phase_agent`. Confirm identities via `~/.claude/teams/<team>/config.json`. If a predecessor agent is still alive, `shutdown_request` it, then spawn the `N+1` successor (`or-<phase>-N+1` pointing at the phase-agent handover doc + artifact, or `or-supervisor-N+1` pointing at the latest `iteration-N.md`), and resume the broker role. (The new phase agent runs its flush-on-resume + latest-revision cross-check before reopening dialogue.)

## Recovery from Common Gotchas

- **Old phase agent / supervisor still alive on resume:** check `~/.claude/teams/<team>/config.json` members; `shutdown_request` it before spawning the `N+1` successor.
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

## Protocol & Template Reference (bundled assets)

A teammate that loads this skill (`Skill('claude-toolkit:or-superpowers-at-scale')`) reaches the orchestrator's protocol and template files here — they are NOT referenced by path from any agent body (that is what the skill-invocation design buys: install-agnostic access). The skill surfaces:

| Asset | Reached by | Contains |
|-------|-----------|----------|
| `assets/spawn-protocol.md` | supervisor, phase agents (via this skill) | Full SPAWN + SPAWN_RESEARCH mechanics (SHUTDOWN's canonical text is above, under Manager Broker Protocols) |
| `assets/preflight-brief.md` | manager (Initial Setup) | Preflight: mode detection, worktree/branch prompts, the `PREFLIGHT_OK` / `PREFLIGHT_FAIL` blocks |
| `assets/{brainstormer,plan-writer,supervisor,implementer,reviewer}-spawn-context.md` | manager (broker) | Per-spawn variable templates substituted at spawn time |
| `assets/iteration-handover-template.md` | supervisor (via this skill) | Iteration handover doc |
| `assets/{brainstormer,plan-writer}-handover-template.md` | phase agents (via this skill) | Phase handover docs (the anti-drift ledger) |
| `assets/manager-handover-template.md` | manager (200k handover) | Cross-session manager handover (with the `active_phase` / `active_phase_agent` fields) |
````

- [ ] **Step 3: Verify the full playbook is present, complete, and valid (GREEN)**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
# all seven Task-2 headers present
Select-String -Path $s -Pattern '^## Proactive Status Reporting \(all tiers\)$','^## Required Communication Style \(HARD RULE\)$','^## Conservation Rules$','^## Handover Ladder$','^## Recovery from Common Gotchas$','^## Red Flags$','^## Protocol & Template Reference \(bundled assets\)$' | Select-Object Line
# the new conservation rules + deposit-opacity that distinguish this from the legacy skill
Select-String -Path $s -Pattern 'Do NOT read the spec or plan artifact','Findings never transit the manager','redirect nudge' | Select-Object Line
# the asset-surfacing table names spawn-protocol + the handover templates (skill-invocation rework requirement)
Select-String -Path $s -Pattern 'assets/spawn-protocol.md','assets/iteration-handover-template.md','assets/\{brainstormer,plan-writer\}-handover-template.md' | Select-Object Line
# holistic: all twelve operating sections present alongside the four skeleton sections
$twelve = '^## Core Principle','^## Mode Detection$','^## Initial Setup','^## Manager Broker Protocols$','^## Phase Transitions','^## Proactive Status Reporting','^## Required Communication Style','^## Conservation Rules$','^## Handover Ladder$','^## Recovery from Common Gotchas$','^## Red Flags$','^## Protocol & Template Reference'
"operating sections present: {0} / 12" -f ($twelve | Where-Object { Select-String -Path $s -Pattern $_ -Quiet }).Count
Select-String -Path $s -Pattern '^## When to Use$','^## Architecture$','^## Integration with Other Skills$' | Select-Object Line   # skeleton intact
# no placeholders / authoring-plan references anywhere in the finished file
Select-String -Path $s -Pattern 'TBD','TODO','added later','filled in','Plan 4','Plan 3','coming soon'   # expect NO match
(Get-Content $s | Measure-Object -Line).Lines                                         # expect > N1
```
Expected: all seven headers match; the new-conservation-rule + deposit-opacity + redirect-nudge anchors present; the asset table names `spawn-protocol.md` and the handover templates; `operating sections present: 12 / 12`; the three skeleton sections still present; **no** placeholder/plan-reference matches; line count grew beyond `N1`.

- [ ] **Step 4: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes. If `claude` is unavailable, record the skip and rely on Step 3.

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md
git -C I:\Dev\claude-toolkit commit -m "feat(skills): add or-superpowers-at-scale manager context-discipline + reference sections"
```
Expected: one commit modifying only `SKILL.md` (append-only). The orchestrator skill is now behaviorally complete on the branch (live only at install).

---

## Task 3: Author the `commands/or-superpowers-at-scale.md` thin wrapper

Author the optional user-facing entry command. It mirrors the plugin's existing skill-wrapping commands (`design.md` / `plan-from-design.md`): **no YAML frontmatter** (the command name derives from the filename), a `# /command` title, and a `## Process` that invokes the skill. It is **thin** — the skill is the manager's playbook and owns everything; the command only provides the `/or-superpowers-at-scale [<idea> | <spec-path> | <plan-path>]` entry point and passes the argument through.

**Files:**
- Create: `plugins/claude-toolkit/commands/or-superpowers-at-scale.md`

- [ ] **Step 1: Verify the command does not yet exist (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\commands\or-superpowers-at-scale.md"
```
Expected: `False`.

- [ ] **Step 2: Create the command with this exact content**

````markdown
# /or-superpowers-at-scale - Orchestrate brainstorm → plan → implement end-to-end

Thin wrapper that invokes the `or-superpowers-at-scale` orchestrator skill. The skill is the manager's playbook — it owns preflight, mode detection, worktree creation, team creation, and all phase orchestration. This command exists only to give the workflow a `/or-superpowers-at-scale [<idea> | <spec-path> | <plan-path>]` entry point.

## Process

Invoke `Skill('claude-toolkit:or-superpowers-at-scale')` and follow it. Pass `$ARGUMENTS` through as the orchestrator's starting input:

- an **idea statement** (or empty) → the skill starts at Phase 1 (brainstorm)
- a **spec path** (`docs/superpowers/specs/*-design.md`) → starts at Phase 2 (plan)
- a **plan path** (`docs/superpowers/plans/*.md`) → starts at Phase 3 (implementation)

Do NOT pre-classify the input — the skill's preflight subagent detects the mode and asks the user if it is ambiguous. Everything after invocation (worktree setup, spawning the first phase agent, and the manager's spawn-brokering) is the skill's responsibility; this command adds no logic of its own.
````

- [ ] **Step 3: Verify the wrapper is present, thin, and invokes the skill (GREEN)**

```powershell
$c = "I:\Dev\claude-toolkit\plugins\claude-toolkit\commands\or-superpowers-at-scale.md"
Test-Path $c                                                                          # expect True
# title + skill invocation + argument pass-through present
Select-String -Path $c -Pattern '^# /or-superpowers-at-scale','Skill\(.claude-toolkit:or-superpowers-at-scale.\)','\$ARGUMENTS' | Select-Object Line
# matches the plugin convention: no YAML frontmatter (first line is the title, not '---')
Get-Content $c -TotalCount 1                                                          # expect the '# /or-superpowers-at-scale …' line, NOT '---'
```
Expected: `True`; the title, the `Skill('claude-toolkit:or-superpowers-at-scale')` invocation, and the `$ARGUMENTS` pass-through all present; the first line is the `#` title (no frontmatter fence) — matching `design.md` / `plan-from-design.md`.

- [ ] **Step 4: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes (the new command is discovered). If `claude` is unavailable, record the skip and rely on Step 3.

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/commands/or-superpowers-at-scale.md
git -C I:\Dev\claude-toolkit commit -m "feat(commands): add /or-superpowers-at-scale entry command"
```
Expected: one new file committed on `or-superpowers-at-scale`.

---

## Task 4: Suite release edits (version bump + manifest sync + README)

Make the single user-visible increment for the whole orchestrator: bump the version `1.1.1 → 1.2.0` in all three version fields, update the plugin descriptions to mention the orchestrator, and add every new component to the README at once (design §"Plugin Packaging" → "Release discipline"). This is the only task in the entire suite that touches a manifest, version, or the README. **No push here** — that is Task 6, on user approval.

**Files:**
- Modify: `plugins/claude-toolkit/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json` (repo root)
- Modify: `README.md` (repo root)

- [ ] **Step 1: Confirm the pre-release baseline (RED)**

```powershell
# all three version fields read 1.1.1; README has no orchestrator entry yet
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json" -Pattern '"version": "1.1.1"' | Select-Object Line
Select-String -Path "I:\Dev\claude-toolkit\.claude-plugin\marketplace.json" -Pattern '"version": "1.1.1"' | Select-Object Line       # two matches (metadata + plugins[])
Select-String -Path "I:\Dev\claude-toolkit\README.md" -Pattern 'or-superpowers-at-scale'                                            # expect NO match
```
Expected: `plugin.json` shows one `"version": "1.1.1"`; `marketplace.json` shows two; the README has **no** `or-superpowers-at-scale` reference yet.

- [ ] **Step 2: Edit `plugin.json` — bump version + update description**

In `I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json`:
- Change `"version": "1.1.1"` → `"version": "1.2.0"`.
- Change the `description` value from
  `"Architecture review agents, test review agents, research agents, development workflow commands, and MCP/skill design guides"`
  to
  `"Architecture and test review agents, research agents, a 3-tier brainstorm-to-ship orchestrator (or-superpowers-at-scale), development workflow commands, and MCP/skill design guides"`.

Resulting file:
```json
{
  "name": "claude-toolkit",
  "version": "1.2.0",
  "description": "Architecture and test review agents, research agents, a 3-tier brainstorm-to-ship orchestrator (or-superpowers-at-scale), development workflow commands, and MCP/skill design guides",
  "author": { "name": "marti" }
}
```

- [ ] **Step 3: Edit `marketplace.json` — bump both versions + sync `plugins[].description`**

In `I:\Dev\claude-toolkit\.claude-plugin\marketplace.json`: bump `metadata.version` and `plugins[].version` to `1.2.0`, and update `plugins[].description` to match `plugin.json` (they are currently identical — keep them in sync). Leave `metadata.description` (the generic marketplace blurb) unchanged.

Resulting file:
```json
{
  "name": "claude-toolkit",
  "owner": { "name": "marti" },
  "metadata": {
    "description": "Agents, commands, and skills for code review, research, and development workflows",
    "version": "1.2.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "claude-toolkit",
      "source": "./plugins/claude-toolkit",
      "description": "Architecture and test review agents, research agents, a 3-tier brainstorm-to-ship orchestrator (or-superpowers-at-scale), development workflow commands, and MCP/skill design guides",
      "version": "1.2.0"
    }
  ]
}
```

- [ ] **Step 4: Edit `README.md` — add every new component**

In `I:\Dev\claude-toolkit\README.md`:

**(a)** Under `### Agents`, after the `violation-verifier` bullet, add the orchestrator agents group:
```markdown

**or-superpowers-at-scale orchestrator agents** (internal — spawned by the orchestrator, not for standalone use):
- **or-brainstormer** / **or-plan-writer** — Phase-1/2 teammates the user talks to directly (idea → spec, spec → plan)
- **or-supervisor** — Phase-3 implementation supervisor (drives subagent-driven-development)
- **or-implementer**, **or-spec-reviewer**, **or-code-quality-reviewer**, **or-final-reviewer** — per-task worker tier
- **or-dependency-researcher**, **or-community-researcher** — deposit-aware research teammates
```

**(b)** Under `### Commands`, after the `/learn` bullet, add:
```markdown
- **/or-superpowers-at-scale** — Orchestrate brainstorm → plan → implement end-to-end in one session (depends on superpowers plugin)
```

**(c)** Under `### Skills`, after the `updating-plugin` bullet, add:
```markdown
- **or-superpowers-at-scale** — 3-tier orchestrator: brainstorm → plan → implement with manager context preserved (depends on superpowers plugin)
- **research-deposit** — Deposit protocol: research agents write findings to disk and reply with a minimal token
- **dependency-research-methodology** — Shared library/SDK research-and-citation workflow (used by the dependency researchers)
- **community-research-methodology** — Shared community/real-world research workflow (used by the community researchers)
```

**(d)** In the `## Dependencies` section, change the sentence
`The `/design`, `/plan-from-design`, and `/implement-from-plan` commands depend on the **superpowers** plugin. Install it separately if you want to use those commands.`
to
`The `/design`, `/plan-from-design`, `/implement-from-plan`, and `/or-superpowers-at-scale` commands — and the `or-superpowers-at-scale` skill — depend on the **superpowers** plugin. Install it separately if you want to use them.`

- [ ] **Step 5: Verify the bump, description, and README are consistent (GREEN)**

```powershell
# all three version fields now read 1.2.0; none reads 1.1.1
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json" -Pattern '"version": "1.2.0"' | Select-Object Line
Select-String -Path "I:\Dev\claude-toolkit\.claude-plugin\marketplace.json" -Pattern '"version": "1.2.0"' | Select-Object Line       # expect two
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json","I:\Dev\claude-toolkit\.claude-plugin\marketplace.json" -Pattern '1\.1\.1'   # expect NO match
# description mentions the orchestrator in both manifests
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json","I:\Dev\claude-toolkit\.claude-plugin\marketplace.json" -Pattern 'brainstorm-to-ship orchestrator' | Select-Object Path
# README lists the new command + skills + the orchestrator agents group + dependency note
Select-String -Path "I:\Dev\claude-toolkit\README.md" -Pattern '/or-superpowers-at-scale','or-superpowers-at-scale orchestrator agents','research-deposit','dependency-research-methodology','community-research-methodology' | Select-Object Line
# both manifests still parse as JSON
Get-Content "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json" -Raw | ConvertFrom-Json | Out-Null; "plugin.json OK"
Get-Content "I:\Dev\claude-toolkit\.claude-plugin\marketplace.json" -Raw | ConvertFrom-Json | Out-Null; "marketplace.json OK"
```
Expected: `plugin.json` shows one `"version": "1.2.0"`, `marketplace.json` two; **no** `1.1.1` remains; both descriptions contain "brainstorm-to-ship orchestrator"; the README shows the new command, the three skills, and the orchestrator-agents group; both manifests parse as JSON (`plugin.json OK`, `marketplace.json OK`).

- [ ] **Step 6: Plugin validates with the bumped manifests**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes with version `1.2.0`. If `claude` is unavailable, record the skip and rely on Step 5's JSON-parse + greps.

- [ ] **Step 7: Commit (the release-prep commit — still local)**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git -C I:\Dev\claude-toolkit commit -m "release: claude-toolkit 1.2.0 — or-superpowers-at-scale orchestrator"
```
Expected: one commit touching exactly the two manifests + README. **Not pushed** (Task 6).

---

## Task 5: Plan-4 + suite integration self-review

A consolidation gate confirming the orchestrator skill is behaviorally complete and internally consistent, the command exists, the release edits are correct, every component the four plans produce is present and coherent, and the plugin validates — **before** the irreversible release push. Verification only — no new component files; a commit is made only if a fix is required.

**Files:** none created.

- [ ] **Step 1: The `SKILL.md` is the full playbook (skeleton + 12 operating sections), no placeholders**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
$all = '^## When to Use$','^## Architecture$','^## Integration with Other Skills$','^## Core Principle','^## Mode Detection$','^## Initial Setup','^## Manager Broker Protocols$','^## Phase Transitions','^## Proactive Status Reporting','^## Required Communication Style','^## Conservation Rules$','^## Handover Ladder$','^## Recovery from Common Gotchas$','^## Red Flags$','^## Protocol & Template Reference'
"sections present: {0} / 15" -f ($all | Where-Object { Select-String -Path $s -Pattern $_ -Quiet }).Count
Select-String -Path $s -Pattern 'TBD','TODO','added later','Plan 4','Plan 3','coming soon'   # expect NO match
# SHUTDOWN canonical text is in the SKILL.md (not in the spawn-protocol asset)
Select-String -Path $s -Pattern '^### SHUTDOWN \(worker teardown' | Select-Object Line
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\spawn-protocol.md" -Pattern '^## SHUTDOWN'   # expect NO match (deferred-here invariant holds)
```
Expected: `sections present: 15 / 15`; no placeholder/plan markers; the `### SHUTDOWN` heading present in `SKILL.md`; **no** `## SHUTDOWN` in `spawn-protocol.md` (Plan 3's deferral is honored exactly once, here).

- [ ] **Step 2: The command exists and the four-plan component set is complete**

```powershell
$P = "I:\Dev\claude-toolkit\plugins\claude-toolkit"
Test-Path "$P\commands\or-superpowers-at-scale.md"                                     # expect True
# nine or-* agents (Plans 2–3)
$nine = 'or-brainstormer','or-plan-writer','or-supervisor','or-implementer','or-spec-reviewer','or-code-quality-reviewer','or-final-reviewer','or-dependency-researcher','or-community-researcher'
"agents: {0} / 9" -f ($nine | Where-Object { Test-Path "$P\agents\$_.md" }).Count
# four skills (Plan 1 + this skill)
$skills = 'or-superpowers-at-scale','research-deposit','dependency-research-methodology','community-research-methodology'
"skills: {0} / 4" -f ($skills | Where-Object { Test-Path "$P\skills\$_\SKILL.md" }).Count
# eleven assets (Plan 3)
(Get-ChildItem "$P\skills\or-superpowers-at-scale\assets\*.md" | Measure-Object).Count | ForEach-Object { "assets: $_ / 11" }
# no draft left behind
Get-ChildItem "I:\Dev\claude-toolkit\docs\superpowers\drafts\" -Filter *.md -ErrorAction SilentlyContinue | Measure-Object | ForEach-Object { "drafts remaining: {0}" -f $_.Count }
```
Expected: command `True`; `agents: 9 / 9`; `skills: 4 / 4`; `assets: 11 / 11`; `drafts remaining: 0`.

- [ ] **Step 3: Depth-1 holds; agents still reach protocols via skill invocation (no stale paths leaked)**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
Select-String -Path "$a\or-*.md" -Pattern '^tools:.*\bAgent\b'                          # expect NO match (depth-1)
Select-String -Path "$a\or-*.md" -Pattern 'assets/.*\.md','~/\.claude/'                 # expect NO match (skill-invocation, not paths)
```
Expected: **no** `Agent` tool in any `or-*` agent; **no** stale `assets/*.md` or `~/.claude/` path in any agent body. (This was Plan 3's invariant; re-checked here because the SKILL.md Plan 4 added is what those invocations resolve to.)

- [ ] **Step 4: Release state is correct and self-consistent**

```powershell
# versions all 1.2.0; descriptions mention the orchestrator; README updated
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json","I:\Dev\claude-toolkit\.claude-plugin\marketplace.json" -Pattern '1\.1\.1'   # expect NO match
Select-String -Path "I:\Dev\claude-toolkit\README.md" -Pattern '^- \*\*/or-superpowers-at-scale\*\*','^- \*\*or-superpowers-at-scale\*\*' | Select-Object Line
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: no `1.1.1` anywhere; the README command + skill bullets present; `claude plugin validate` passes at `1.2.0` (or skip recorded).

- [ ] **Step 5: Commit graph — the four Plan-4 commits are present, none pushed**

```powershell
# match by commit subject, not a fixed SHA range — the execution-time graph shape varies (real component commits replace the planning commits)
git -C I:\Dev\claude-toolkit log --oneline -12 | Select-String 'manager broker \+ operating sections','manager context-discipline \+ reference sections','/or-superpowers-at-scale entry command','release: claude-toolkit 1.2.0'
git -C I:\Dev\claude-toolkit status -sb            # confirm no upstream / ahead — NOT pushed yet
```
Expected: all four Plan-4 commit subjects appear in recent history, in order, atop the executed Plan-1/2/3 commits; `status -sb` shows the branch is local only (no upstream, or ahead with nothing pushed). The push happens only in Task 6.

- [ ] **Step 6: Spec-coverage check for Plan 4**

Confirm every Plan-4 design requirement has a corresponding artifact:
- Manager-discipline `SKILL.md` body appended — Core Principle, Mode Detection, Initial Setup, SPAWN / **SHUTDOWN** / SPAWN_RESEARCH, Phase Transitions & Idle Taxonomy, Proactive Status Reporting, Required Communication Style, Conservation Rules, Handover Ladder, Recovery, Red Flags ✓ (design §"Manager Context Discipline", §"Red Flags", §"Mode Detection", §"Handover Ladder", §"Protocols", §"Manager definition tightening", §"Clarifications")
- **SHUTDOWN canonical handshake** lands in the `SKILL.md` (Plan 3 deferral discharged), absent from `spawn-protocol.md` ✓ (design §"SHUTDOWN protocol [NEW]"; Plan 3 §"spawn-protocol.md scope")
- The `SKILL.md` **surfaces** the SPAWN + SPAWN_RESEARCH protocol and the three handover templates (Protocol & Template Reference) — the skill-invocation-rework requirement ✓
- Manager-side additions to the PRESERVED sections — phase-1/2 silence, deposit-opacity, the redirect nudge, manager-forbidden-to-read-artifact, the idle taxonomy, the plan→impl go-ahead gate ✓ (design §"New conservation rules", §"Idle wake-up taxonomy", §"Manager forbidden to read spec/plan artifact", §"Plan→implementation go-ahead")
- Optional `commands/or-superpowers-at-scale.md` thin wrapper ✓ (design §"Plugin Packaging" → "Home & layout")
- Suite release — `1.1.1 → 1.2.0` across `plugin.json` + both `marketplace.json` fields + README, single increment ✓ (design §"Plugin Packaging" → "Release discipline")
- Behavioral validation (the five spikes + wrapper check) + loose-copy removal + install: intentionally **deferred to cutover** ✓ (design §"Cutover & end-state validation"; Plan 2 spikes doc)

- [ ] **Step 7: Checkpoint — Plan 4 complete (pre-push)**

All checks green (or `claude plugin validate` explicitly noted as skipped). If any step required an edit, commit it:
```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "fix(plan-4): integration self-review corrections"
```
Otherwise no commit is needed. The orchestrator is built and release-prepped on the branch; the only remaining action is the release push (Task 6), gated on the user.

---

## Task 6: Release push (the suite release) — gated on explicit user approval

The single outward-facing action of the entire suite. Until now everything is local; this task integrates the branch and publishes `claude-toolkit 1.2.0` so users get the orchestrator via `claude plugin update`. **Do nothing here without the user's explicit go-ahead** — the push *is* the release (design handover: "push only when the user asks").

**Files:** none created.

- [ ] **Step 1: Surface the release decision to the user (HARD GATE)**

State plainly: the suite is complete and self-reviewed on `or-superpowers-at-scale`, version-bumped to `1.2.0`, **not pushed**. Ask for explicit approval to release, and how to integrate (the marketplace serves the repo's default branch, so `1.2.0` must land there for `claude plugin update` to see it). **Do not proceed past this step without an explicit "yes".** If the user defers, stop here — the branch stays local and the release waits.

- [ ] **Step 2: Integrate the branch via `superpowers:finishing-a-development-branch`**

On approval, invoke `Skill('superpowers:finishing-a-development-branch')` and follow it to integrate `or-superpowers-at-scale` into the marketplace's default branch (merge or PR per the user's choice — do NOT hardcode one). The goal: the `1.2.0` commit reaches the branch `claude plugin update` reads.

- [ ] **Step 3: Push (the release)**

Push per the integration choice from Step 2 (e.g. push the merged default branch, or push the feature branch + open the PR). Example for a direct push of the default branch after merge:
```powershell
git -C I:\Dev\claude-toolkit push origin <default-branch>
```
Expected: the remote `CompfyArmChair/claude-toolkit` now carries `claude-toolkit 1.2.0` on its default branch.

- [ ] **Step 4: Confirm the release is live**

```powershell
git -C I:\Dev\claude-toolkit log --oneline -1 <default-branch>
git -C I:\Dev\claude-toolkit show <default-branch>:.claude-plugin/marketplace.json | Select-String '"version"'
```
Expected: the release commit is on the default branch; `marketplace.json` there reads `1.2.0`. Tell the user the orchestrator is published; users pick it up with `claude plugin update`.

- [ ] **Step 5: Point to cutover (post-release, not part of this suite execution)**

The suite is shipped, but **behaviorally unvalidated**. Surface the next, separate step: run the **cutover** per `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` → "Cutover checklist" (design §"Cutover & end-state validation"): remove the deprecated loose `~/.claude` copies, `claude plugin install claude-toolkit`, then run Spikes 1–5 + Plan 1's wrapper check against the *installed* plugin, applying each spike's fallback on failure. Do NOT declare the orchestrator behaviorally done until Spikes 1–3 are GREEN. This runs after release because the checks must exercise the installed plugin, not the authoring session's stale loose copies.

---

## Self-Review (run after writing, before declaring Plan 4 done)

**1. Spec coverage:** Task 5 Step 6 enumerates the Plan-4 requirements against the design — the full manager-discipline `SKILL.md` body (every named section), the SHUTDOWN-here deferral, the asset-surfacing reference (skill-invocation rework), the command wrapper, and the single `1.1.1 → 1.2.0` release — plus the deliberate cutover deferral (behavioral spikes, loose-copy removal, install). The PRESERVE-FROM sections (Core Principle, Proactive Status Reporting, Required Communication Style, Conservation Rules, Recovery, Red Flags) are inlined in full from the legacy skill with `or-*` naming and the orchestrator's additions, per design §"Manager Context Discipline" / §"Red Flags". No gaps.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to above". The `SKILL.md` body, the command, and every manifest/README edit are inlined in full (no "PRESERVE from X" by reference — the engineer needs no second file open). Tasks 1 and 2 actively grep the finished file for `TBD`/`Plan 4`/forward-stub markers and expect none; the body is additive (whole sections appended), not stub-and-fill. The one cross-file dependency is the legacy `subagent-driven-development-at-scale/SKILL.md` as the PRESERVE source, which is the design-sanctioned source, fully transcribed-and-adapted in-task.

**3. Type/name consistency:** Section headings match the verification greps exactly (`## Core Principle: Manager Context Is Sacred`, `## Phase Transitions & Idle Taxonomy`, `## Protocol & Template Reference (bundled assets)`, etc. — Tasks 1–2 RED/GREEN reference the identical strings). The completion/handover tokens (`BRAINSTORM_COMPLETE — spec: <path>`, `PLAN_COMPLETE — plan: <path>`, `BRAINSTORMER_HANDOVER`/`PLAN_WRITER_HANDOVER`, `ITERATION <N> — STOPPED_FOR_HANDOVER`/`COMPLETED`, `RESEARCH_DONE: <path>`/`RESEARCH_BLOCKED: <path> — <reason>`, `SHUTDOWN`/`SPAWN`/`SPAWN_RESEARCH`) match the design §"Handover trigger token shape", §"Protocols", and the Plan-3 `spawn-protocol.md` / agent bodies. The `ROLE → subagent_type` map (`implementer → claude-toolkit:or-implementer`, …) matches the spec and `spawn-protocol.md`. The asset filenames in the Protocol & Template Reference (`spawn-protocol.md`, `preflight-brief.md`, the five `*-spawn-context.md`, the four `*-handover-template.md`) match the eleven files Plan 3 authored. The skill name `or-superpowers-at-scale`, the command filename, and the `Skill('claude-toolkit:or-superpowers-at-scale')` invocation are identical across the command, the SKILL.md asset reference, and the agent bodies. The version `1.2.0` is identical across all three manifest fields; the descriptions in `plugin.json` and `marketplace.json` `plugins[]` are kept byte-identical.

## Plan suite status

This is **Plan 4 of 4 — the final plan**. With it written, the suite is complete: Plan 1 (research skills + `research-deposit`), Plan 2 (the two phase agents + the orchestrator skill skeleton + the behavioral-spikes doc), Plan 3 (the five remaining agents + the two research teammates + the eleven `assets/*`), and Plan 4 (the manager-discipline `SKILL.md` body + the command wrapper + the `1.2.0` release). **Do not** proceed to execution from this file alone — the whole suite executes in order (Plan 1 → 2 → 3 → 4) via `/implement-from-plan` after the user has reviewed all four plans. The real per-task `git mv`/commits restore the SDD rollback boundary the plans assume. After the suite executes and Task 6 pushes the release, run the **cutover** (the behavioral-spikes doc's "Cutover checklist") against the installed plugin — the suite's only remaining validation, deferred there by design because it must exercise the installed plugin, not the authoring session.
