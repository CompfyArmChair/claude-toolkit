# `or-superpowers-at-scale` — Design

_Revised 2026-05-25: folded in the seven finished agent-body drafts — now referenced from `docs/superpowers/drafts/` (authoritative for frontmatter) — and the prior handover's tool-grant and naming decisions; the Agent Inventory is reconciled accordingly._

_Revised 2026-05-25 (later): added the Phase-1/2 anti-drift resume discipline (flush-on-resume, interrupted-turn capture on `MANAGER STOPPING`, latest-revision cross-check) and applied it consistently across this design and the `or-brainstormer` / `or-plan-writer` drafts; trimmed the "Phase agent bodies" restatement to a pointer + three guarantees; added the plan-writer template's `Latest revision` field and impl-note #9. Independently audited for cross-file consistency._

_Revised 2026-05-30: re-homed into the **`claude-toolkit` plugin** (repo `I:\Dev\claude-toolkit`, marketplace `claude-toolkit`, GitHub `CompfyArmChair/claude-toolkit`) instead of loose `~/.claude/`. All assets are now `claude-toolkit:*` plugin components; the three research skills are genuinely shared with the plugin's existing `dependency-researcher` / `community-researcher` (refactored to thin wrappers, extracted from the **plugin's** canonical copies — the `~/.claude/agents/` copies are stale legacy, out of scope). Subagent types and in-body skill references are plugin-qualified (`claude-toolkit:or-*`). Spec + plans now live in the repo under `docs/superpowers/`. See the new **Plugin Packaging** section, which is authoritative wherever it touches homes, namespaces, release, or git._

_Revised 2026-05-30 (later): reconciled the Release-discipline wording — the orchestrator ships as a **single** minor release (`1.1.1 → 1.2.0`) finalized in the Plan 4 release step, not a bump per plan; Plans 1–3 commit components without manifest churn. Added the **Cutover & end-state validation** subsection: the loose `~/.claude` copies are deprecated; on completion, remove them, install the plugin, then run the deferred behavioral validation against the installed plugin._

## Goal

A single Claude Code skill that orchestrates the full superpowers workflow end-to-end in one session: **brainstorm → plan → implement**, with manager context preserved throughout by delegating each phase to a dedicated teammate agent the user talks to directly.

Supersedes `subagent-driven-development-at-scale` (no need to maintain the original).

## Scope

This spec defines:
- The new orchestrator skill itself (`or-superpowers-at-scale`)
- Nine new agent definitions (orchestrator-specific, prefixed `or-*`)
- Three new shared skills (research methodology + deposit pattern)
- Frontmatter updates to two existing agents
- Spec/handover document conventions for the new phases

**Naming convention:** All public-facing orchestrator assets (skill name, agent names) carry the `or-*` prefix. Shared methodology skills do not — they are reused outside the orchestrator.

**Asset reuse:** Where the existing SDD-at-scale content (descriptions, protocols, templates, disciplines) carries over, the implementer preserves the existing wording verbatim or with minimal adaptation. The phrase "PRESERVE FROM" in this spec means "copy from the original source as-is".

---

## Plugin Packaging

This skill ships as part of the **`claude-toolkit` plugin** (repo `I:\Dev\claude-toolkit`, marketplace `claude-toolkit`, GitHub `CompfyArmChair/claude-toolkit`). It is **not** installed loose into `~/.claude/`. This section is authoritative wherever it touches asset homes, namespacing, release, or git; older `~/.claude/...` paths elsewhere in this spec are superseded by it.

### Home & layout

All artifacts are components of the existing plugin at `I:\Dev\claude-toolkit\plugins\claude-toolkit\`:

| Component | Path (under the plugin) |
|-----------|--------------------------|
| Orchestrator skill | `skills/or-superpowers-at-scale/SKILL.md` |
| Orchestrator assets | `skills/or-superpowers-at-scale/assets/*` |
| Shared research skills | `skills/{research-deposit, dependency-research-methodology, community-research-methodology}/SKILL.md` |
| `or-*` agents (9) | `agents/or-*.md` |
| Refactored researchers | `agents/dependency-researcher.md`, `agents/community-researcher.md` (existing plugin files) |
| Optional command wrapper | `commands/or-superpowers-at-scale.md` (thin; invokes the skill — mirrors the `plan-from-design` command) |

### Namespace & naming

Installed, every component is namespaced `claude-toolkit:*`:

- **Subagent types are plugin-qualified.** The SPAWN broker maps `ROLE → claude-toolkit:or-<role>` (e.g. `implementer → claude-toolkit:or-implementer`). Every `subagent_type` reference in this spec is read with the `claude-toolkit:` prefix.
- **In-body skill references are plugin-qualified** — `Skill('claude-toolkit:research-deposit')`, etc. Whether bare same-plugin names also resolve is **unverified**; the impl-note #3 spike must confirm the working form before the agent bodies are finalized (fall back to fully-qualified names if bare fails).
- **The `or-` prefix is retained** as intra-plugin grouping — it distinguishes orchestrator agents from the plugin's existing `architecture-reviewer` / `test-reviewer` / researchers, and matches the seven drafts. (The namespace makes it technically redundant; keeping it avoids re-editing every draft.)

### Existing researchers — canonical source

The plugin's `agents/dependency-researcher.md` and `agents/community-researcher.md` are the **canonical** copies and the extraction source for the methodology skills. The `~/.claude/agents/` copies have **drifted** (verified — different content) and are stale legacy; they are out of scope (optionally deleted later). Do not extract from them.

### Release discipline (per the `updating-plugin` skill)

This is a plugin **update**, not a new plugin, and the whole orchestrator ships as a **single minor release**. The version bump + marketplace sync + README update + push happen **once**, in the suite's final plan (Plan 4) as a dedicated release step gated on user approval — **not** once per plan. Plans 1–3 commit their components to the feature branch with **no** manifest/version/README churn (nothing is user-visible until the release push). That release step:

- `plugins/claude-toolkit/.claude-plugin/plugin.json` → bump `version` `1.1.1 → 1.2.0` + update `description`.
- `.claude-plugin/marketplace.json` → bump **both** `metadata.version` and `plugins[].version` (kept equal to `plugin.json`).
- Update the repo `README.md` component listing (all new components added at once).
- Commit and push (users update via `claude plugin update`).

Net bump for the whole orchestrator: `1.1.1 → 1.2.0` (minor — new components), finalized at the Plan 4 release.

### Git workflow

Work happens on a feature branch **`or-superpowers-at-scale`** in `I:\Dev\claude-toolkit`, with a commit per task. The repo is real git, so the SDD review/rollback loop applies — this **supersedes** any "no-repo checkpoint" note in the plans. Docs (this spec + the plan suite) live in the repo under `docs/superpowers/{specs,plans}/`.

### Cutover & end-state validation

The loose `~/.claude` copies the plugin supersedes — the drifted `agents/{dependency,community}-researcher.md`, and the loose `design` / `plan-from-design` / `subagent-driven-development-at-scale` assets — are **deprecated** in favour of the plugin. On suite completion (after the Plan 4 release): remove the deprecated loose copies, install the plugin (`claude plugin install claude-toolkit`), and only then run the **behavioral validation** that Plans 1–3 defer — live `Skill()` load, an agent dispatch that returns a cited report, and the impl-note #3/#10/#11 teammate spikes — against the *installed* plugin. Until install, verification is **structural** (`claude plugin validate` + content greps): the components are not live in the authoring session, so a live test there would exercise the stale loose copies, not the plugin files.

---

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

```
[User] /or-superpowers-at-scale [<idea> | <spec-path> | <plan-path>]
        │
        ▼
[Phase 0 — Preflight]   foreground Agent (one-shot)
  • Detect mode from input (idea / spec / plan)
  • AskUserQuestion: worktree name + base branch
  • Verify branch state (respect user-consent for main/master)
  • Create worktree via superpowers:using-git-worktrees
  • If spec/plan provided: validate exists + extract metadata
  • Return PREFLIGHT_OK { mode, worktree, branch, handover_dir, ... }
        │
        ▼
[Phase 1 — Brainstorm]   if mode == idea
  • Manager TeamCreate, spawns or-brainstormer-1 (teammate, opus)
  • User talks directly to or-brainstormer-1
  • or-brainstormer-1 follows superpowers:brainstorming verbatim,
    with override: terminal "invoke writing-plans" replaced with
    SendMessage manager: BRAINSTORM_COMPLETE — spec: <path>
  • Research dispatched via SPAWN_RESEARCH broker
  • Handover at 150k via BRAINSTORMER_HANDOVER
  • Manager shuts down or-brainstormer-N on completion
        │
        ▼
[Phase 2 — Plan]   if mode == idea OR spec
  • Manager spawns or-plan-writer-1 (teammate, opus)
  • User talks directly to or-plan-writer-1
  • or-plan-writer-1 follows superpowers:writing-plans verbatim,
    with override: Execution Handoff replaced with
    SendMessage manager: PLAN_COMPLETE — plan: <path>
  • Research dispatched via SPAWN_RESEARCH broker
  • Handover at 150k via PLAN_WRITER_HANDOVER
  • Manager shuts down or-plan-writer-N on completion
        │
        ▼
[Phase 3 — Implementation]   always
  • If arriving from Phase 2 (PLAN_COMPLETE): manager surfaces the
    implementation go-ahead to the user, waits for approval (F6)
  • Manager spawns or-supervisor-1 (teammate, opus)
  • Supervisor invokes superpowers:subagent-driven-development as
    STEP 0 and follows it verbatim, with one override:
    spec + code-quality reviewers spawn in PARALLEL
    (SDD describes them sequentially)
  • Supervisor SPAWN messages route through manager broker
  • or-implementer / or-spec-reviewer / or-code-quality-reviewer
    workers dispatched per task; or-final-reviewer at end
  • Iteration handover at 200k
  • Manager handover at 200k (cross-session) if needed
```

---

## Agent Inventory

All agents are orchestrator-specific (`or-*` prefix). Their home is the `claude-toolkit` plugin's `agents/` directory (installed as `claude-toolkit:or-*` subagent types — see **Plugin Packaging**). The seven non-research bodies are **already drafted** in `docs/superpowers/drafts/` and are the **authoritative source for each agent's exact frontmatter** (tools, model, declared skills — see *Skill loading mechanism* below); they are finalised into the plugin's `agents/` directory at implementation. The two research bodies are not yet drafted — they are authored from the template below at implementation. The "Tool grants" column is a human-readable gist; where it and a draft's frontmatter disagree, the draft wins.

| Agent file | Default model | Tool grants (gist — draft frontmatter is authoritative) | Declared skills (loaded in-body) | Body source |
|------------|---------------|---------------------------------------------------------|-------------------|-------------|
| `or-brainstormer.md` | opus | Read/Write/Edit/Glob/Grep/Bash, AskUserQuestion, Skill, SendMessage; **no Agent** (task tools are platform-granted to teammates — see below) | `superpowers:brainstorming` | → `docs/superpowers/drafts/or-brainstormer.md` |
| `or-plan-writer.md` | opus | Read/Write/Edit/Glob/Grep/Bash, AskUserQuestion, Skill, SendMessage; **no Agent** | `superpowers:writing-plans` | → `docs/superpowers/drafts/or-plan-writer.md` |
| `or-supervisor.md` | opus | Read/Write/Edit/Glob/Grep/Bash, Skill, SendMessage, Task\* (Create/Update/List); **no AskUserQuestion** (surfaces via manager), **no web/research** (delegated), **no Agent** | `superpowers:subagent-driven-development` | → `docs/superpowers/drafts/or-supervisor.md` (absorbs the original SDD-at-scale `supervisor-protocol.md` + `supervisor-brief.md`) |
| `or-implementer.md` | **Not locked** — supervisor picks at SPAWN | Read/Write/Edit/Glob/Grep/Bash, Skill, SendMessage; **no Agent** | `superpowers:test-driven-development` | → `docs/superpowers/drafts/or-implementer.md` (from `worker-generic-brief.md`, implementer-flavored) |
| `or-spec-reviewer.md` | sonnet | Read/Grep/Glob/Bash, SendMessage (read-only — **no Edit/Write**) | none | → `docs/superpowers/drafts/or-spec-reviewer.md` |
| `or-code-quality-reviewer.md` | **opus** | Read/Grep/Glob/Bash, SendMessage (read-only — **no Edit/Write**) | none | → `docs/superpowers/drafts/or-code-quality-reviewer.md` |
| `or-final-reviewer.md` | opus | Read/Grep/Glob/Bash, SendMessage (read-only — **no Edit/Write**) | none | → `docs/superpowers/drafts/or-final-reviewer.md` |
| `or-dependency-researcher.md` | **opus** | Read/Grep/Glob, WebFetch, WebSearch, `mcp__context7__*`, **Write**, Skill, **SendMessage**; no AskUserQuestion; **no Agent** | `dependency-research-methodology`, `research-deposit` | NEW — **not yet drafted**; author from "Research agent body" below |
| `or-community-researcher.md` | **opus** | Read/Grep/Glob, WebFetch, WebSearch, **Write**, Skill, **SendMessage** (no `mcp__context7__*`); no AskUserQuestion; **no Agent** | `community-research-methodology`, `research-deposit` | NEW — **not yet drafted**; author from "Research agent body" below |

### Skill loading mechanism (frontmatter `skills:` is inert for teammates)

Every `or-*` agent is spawned as a **teammate** (`run_in_background: true` + `team_name`). Per Claude Code's agent-teams behavior, the `skills:` (and `mcpServers:`) frontmatter fields are **not applied to a teammate** — a teammate loads skills from user/project settings exactly like a normal session. So frontmatter `skills:` pre-seeds nothing here.

The load-bearing mechanism is the **in-body `Skill(...)` call** each skill-bearing agent makes as its first action (the brainstormer / plan-writer / supervisor STEP 0, the implementer's Disposition, and the research agents' methodology + deposit directives). Every such agent carries `Skill` in its `tools`, so the call works.

`skills:` frontmatter is retained on these agents as **documentation only**, and each skill-bearing body carries a one-line note that it is inert for teammates so the STEP 0 call is never deleted as "redundant." (The two existing researchers — `dependency-researcher` / `community-researcher` — also run as foreground subagents, where the frontmatter may still load; they keep both layers.)

### Agent tool-grant decisions (reconciled with drafts)

These were settled while drafting the bodies; they live here now (previously only in the handover):

- **Phase-agent task tools (no frontmatter split).** Teammates always get `SendMessage` and the task-management tools (`TaskCreate/TaskUpdate/TaskList`) regardless of frontmatter, so neither phase agent's task-tool access is controlled by its `tools:` list — the earlier "brainstormer carries `Task*`, plan-writer deliberately omits" split was a no-op and is dropped. Neither lists them now. (The brainstorming skill mandates a working checklist: in standard Claude Code that is `TodoWrite`; this team harness exposes the `Task*` family. Confirm the checklist step works with whatever the teammate has — see impl-note #11.) The supervisor is also a teammate and receives the task tools the same way; it keeps `Task*` in its `tools:` list as documentation of its heavy task-list use (it drives the SDD task list), not because frontmatter is what grants them.
- **Supervisor grant** is the concrete orchestration set, not a literal "all except Agent": it excludes `AskUserQuestion` (the supervisor surfaces to the user *through* the manager, never directly) and all web/research tools (delegated). The only load-bearing exclusion is `Agent` (depth-1).
- **Every worker — including the read-only reviewers — has `SendMessage`.** It is load-bearing for the STATUS-report protocol even though reviewers are otherwise read-only; the spec's read-only framing must not be read as removing it.
- **`or-implementer` has no `model:`** in frontmatter — the supervisor picks per task via the SPAWN `MODEL` field (see "`or-implementer.md` frontmatter" under Clarifications).
- **Worker instance naming** is `or-<role>-task<N>` (+ `-fix<M>` / `-rev<K>`; `or-final-reviewer` has no suffix). The authoritative naming table lives in `docs/superpowers/drafts/or-supervisor.md`.

### Phase agent bodies (`or-brainstormer.md` / `or-plan-writer.md`)

The finished bodies are authoritative in `docs/superpowers/drafts/` — do not restate their structure here (that duplication is the next drift surface). The design depends on three load-bearing guarantees from those bodies:

- **Terminal override** — at the canonical skill's terminal step the agent SendMessages the manager (`BRAINSTORM_COMPLETE — spec: <path>` / `PLAN_COMPLETE — plan: <path>`) instead of invoking the next skill or offering the execution choice; a Closed-loopholes list pins this against the skill's terminal pressure. Verified at implementation per impl-note #6.
- **Depth-1** — research is delegated via `SPAWN_RESEARCH`, never the `Agent` tool. Structurally enforced — the bodies carry no `Agent` grant in frontmatter — so no test note is needed.
- **Anti-drift resume** — the spec/plan artifact is the running ledger, not the handover doc; see "Phase-agent anti-drift resume discipline" below. Verified at implementation per impl-note #9.

The 150k handover threshold (vs the supervisor's 200k) keeps interactive dialogue above any compression risk; the handover doc is kept <5KB so the successor boots on a small doc plus the spec/plan artifact.

### Research agent body (template for `or-dependency-researcher.md` / `or-community-researcher.md`)

**Status: not yet drafted.** Unlike the seven bodies above, these two have no draft file — author them from this template at implementation. Each research agent's body includes:

1. **Identity line** — "You are an `or-<topic>-researcher` deposit-aware research agent."
2. **Methodology directive** — "Use `Skill('<topic>-research-methodology')` to load the research approach."
3. **Deposit directive** — "Use `Skill('research-deposit')` to write your findings and signal completion. You will receive a `DEPOSIT` path in your prompt — write your full findings there, then SendMessage the manager exactly `RESEARCH_DONE: <path>` and nothing else. Never echo findings into your message."
4. **Tool note** — "You have `Write` (deposit requires it) and `SendMessage` (to signal the manager). You have no `Agent` tool — you are a leaf teammate."
5. **Skill-load note** — a one-line reminder that frontmatter `skills:` is inert for teammates (see *Skill loading mechanism*); the `Skill(...)` calls in items 2–3 are what load the methodology and deposit skills.

### Existing agents updated (frontmatter only)

| Agent file | Change |
|------------|--------|
| `agents/dependency-researcher.md` (plugin — canonical) | Add `skills: [dependency-research-methodology]` to frontmatter. Body **replaced with a thin wrapper**: keep the identity line ("You are a Library Research Agent…"), pre-seed the methodology skill, and direct the agent to execute it for the request. The 5-step methodology + citation rules + what-not-to-do move into the skill. |
| `agents/community-researcher.md` (plugin — canonical) | Add `skills: [community-research-methodology]` to frontmatter. **Also add `Skill` to its `tools:` list** — it currently lacks it (only `Glob, Grep, Read, WebFetch, WebSearch, AskUserQuestion`), and the thin-wrapper body needs `Skill` for the belt-and-braces `Skill('community-research-methodology')` call. (The dependency-researcher already has `Skill`, so this asymmetry is community-only.) Body **replaced with a thin wrapper** (same pattern: identity line + pre-seed + execute). |

The methodology content is *extracted* from the existing agent body and moved into the standalone skill file (single source of truth). The agent file keeps only its identity framing and a pointer to the skill, so the methodology lives in exactly one place. (Both agents also run as teammates inside the orchestrator — via SPAWN_RESEARCH or the wrap case — where, as with the `or-*` agents, frontmatter `skills:` is inert; the thin wrapper's in-body `Skill(...)` call is the load-bearing path in that mode. The frontmatter still helps when they run as foreground subagents.)

---

## Skill Inventory

| Skill | Location | Scope | Used by |
|-------|----------|-------|---------|
| `or-superpowers-at-scale` | `skills/or-superpowers-at-scale/` (plugin) | The orchestrator (this skill — user-invoked) | User |
| `dependency-research-methodology` | `skills/dependency-research-methodology/` (plugin) | Shared methodology (library research workflow) | `dependency-researcher`, `or-dependency-researcher` |
| `community-research-methodology` | `skills/community-research-methodology/` (plugin) | Shared methodology (community/real-world research workflow) | `community-researcher`, `or-community-researcher` |
| `research-deposit` | `skills/research-deposit/` (plugin) | Deposit protocol (write findings to disk, reply minimal) | `or-dependency-researcher`, `or-community-researcher` |

### `or-superpowers-at-scale` skill frontmatter

`name: or-superpowers-at-scale`. Per `superpowers:writing-skills` CSO guidance the description states *when to use*, not the workflow:

> `Use when the user wants to take an idea, spec, or plan all the way to shipped code in one orchestrated session — phrased as "brainstorm to ship", "full superpowers workflow orchestrated", or "end-to-end orchestration" — especially when the plan does not yet exist but the work is expected to benefit from 3-tier orchestration once implementation begins. Not for direct execution of an existing plan (use superpowers:subagent-driven-development) or for ad-hoc exploratory work.`

This is a user-invoked skill (slash command), so the description also guides surfacing; the when-NOT-to-use clause mirrors the "When to Use" section below. Keep the description's triggers in sync with that section.

### `dependency-research-methodology` skill body

PRESERVE FROM the body of the plugin's `agents/dependency-researcher.md` (the canonical copy) — extract the methodology content (how to resolve library IDs, query Context7, structure findings, cite sources). The skill body is the methodology; the agent file becomes a thin wrapper that pre-seeds it.

**Description (pinned)** — scoped so the skill never lures the main agent into inline research (which would undercut the CLAUDE.md mandate to delegate to the `dependency-researcher` agent):
> `Use when you are an agent already executing a library/SDK/API research task and need the structured research-and-citation workflow. Not a trigger to research inline — the main agent must still delegate to the dependency-researcher agent.`

### `community-research-methodology` skill body

PRESERVE FROM the body of the plugin's `agents/community-researcher.md` (the canonical copy) — extract the methodology (how to search community knowledge, identify real-world patterns, evaluate trade-offs, cite sources).

**Description (pinned)** — same scoping rationale as `dependency-research-methodology`:
> `Use when you are an agent already executing a community/real-world research task and need the structured research-and-citation workflow. Not a trigger to research inline — the main agent must still delegate to the community-researcher agent.`

### `research-deposit` skill body (NEW)

A concise skill (~30 lines) defining the deposit protocol:

- The deposit-aware research agent receives a `DEPOSIT: <path>` parameter in its prompt.
- After completing research, write the full findings to that path (use `Write` tool).
- SendMessage the dispatching parent (the manager) exactly: `RESEARCH_DONE: <path>` — nothing else.
- Do NOT echo findings into the message. Do NOT summarize back to parent. The findings live on disk; the parent reads them from there.
- If the research is blocked or cannot complete, write a partial findings doc with what was gathered and SendMessage `RESEARCH_BLOCKED: <path> — <one-line reason>` instead of `RESEARCH_DONE`.

This skill is the **canonical source** of the deposit protocol wording. The SPAWN_RESEARCH general-purpose wrap case (case 2) reproduces this wording in the manager's inline prompt rather than re-inventing it.

---

## Asset Inventory (`skills/or-superpowers-at-scale/assets/` in the plugin)

| Asset file | Status | Description |
|------------|--------|-------------|
| `preflight-brief.md` | ADAPTED | Foreground preflight brief, extended for mode detection + worktree-name prompting. PRESERVE structure from original `preflight-brief.md`; ADD mode-detection logic and AskUserQuestion for worktree name + base branch. |
| `spawn-protocol.md` | ADAPTED | Canonical SPAWN + SPAWN_RESEARCH protocol reference. PRESERVE SPAWN mechanics from original; ADD SPAWN_RESEARCH section. |
| `supervisor-spawn-context.md` | NEW | Per-spawn variables for `or-supervisor`. Tiny (~12 lines). See "Spawn-context templates" below. |
| `implementer-spawn-context.md` | NEW | Per-spawn variables for `or-implementer`. Tiny (~5 lines). |
| `reviewer-spawn-context.md` | NEW | Per-spawn variables for any reviewer role (one template, role passed as variable). |
| `brainstormer-spawn-context.md` | NEW | Per-spawn variables for `or-brainstormer` (idea statement, worktree path, handover dir). |
| `plan-writer-spawn-context.md` | NEW | Per-spawn variables for `or-plan-writer` (spec path, worktree path, handover dir). |
| `iteration-handover-template.md` | PRESERVED | Supervisor's iteration handover doc template. Reuse as-is from original. |
| `manager-handover-template.md` | ADAPTED | Cross-session manager handover. PRESERVE structure; ADD `active_phase` field (brainstorm / plan / implement) and `active_phase_agent` field (if any). |
| `brainstormer-handover-template.md` | NEW | Phase agent handover doc (in-flight dialogue state). See "Phase handover templates" below. |
| `plan-writer-handover-template.md` | NEW | Phase agent handover doc (mirrors brainstormer-handover). |

### Spawn-context templates

**`brainstormer-spawn-context.md`:**
```
Identity: <NAME> in team <TEAM>
Worktree: <WORKTREE_PATH>
Branch: <BRANCH>
Handover dir: <HANDOVER_DIR>
Initial user input: <USER_IDEA>
<if resuming after handover: Prior handover: <HANDOVER_DIR>/brainstormer-handover-<N-1>.md>
```

**`plan-writer-spawn-context.md`:**
```
Identity: <NAME> in team <TEAM>
Worktree: <WORKTREE_PATH>
Branch: <BRANCH>
Handover dir: <HANDOVER_DIR>
Spec path: <SPEC_PATH>
<if resuming after handover: Prior handover: <HANDOVER_DIR>/plan-writer-handover-<N-1>.md>
```

**`supervisor-spawn-context.md`:**
```
Identity: <SUPERVISOR_NAME> in team <TEAM_NAME>
Plan: <PLAN_PATH>
Branch: <BRANCH>
Handover dir: <HANDOVER_DIR>
<if N>1: Prior iteration handover: <HANDOVER_DIR>/iteration-<N-1>.md>
<if cross-session: Manager handover: <HANDOVER_DIR>/manager-handover-<M>.md>
<CORRECTIONS_FROM_PARENT or "No corrections from parent.">
Project conventions:
<PROJECT_CONVENTIONS or "(None for this run.)">
First SPAWN target hint: <FIRST_TASK_HINT>
```

**`implementer-spawn-context.md`:**
```
Identity: <NAME> in team <TEAM>
Branch: <BRANCH>
Supervisor: <SUPERVISOR_NAME>
```

**`reviewer-spawn-context.md`** (parameterized by role at spawn time):
```
Identity: <NAME> (<ROLE>) in team <TEAM>
Branch: <BRANCH>
Supervisor: <SUPERVISOR_NAME>
```

### Phase handover templates

**`brainstormer-handover-template.md`** (sketch, intentionally <5KB):
```
---
title: Brainstormer Handover <N>
date: <YYYY-MM-DD>
team: <team-name>
predecessor: or-brainstormer-<N>
spec_draft: <path-or-none>
---

# Brainstormer Handover <N>

## Where we are in the workflow
- Brainstorming checklist progress: <which steps done>
- Currently: <asking clarifying questions | presenting design sections | awaiting user spec review>

## User preferences captured so far (not yet in spec)
- <bullets>

## Open questions to ask next
- <one-line>

## Current spec draft
- Path: <path-or-none>
- Latest revision: <one-line>

## What to do next when resumed
<one-paragraph: the exact next question or action>
```

**`plan-writer-handover-template.md`** (mirrors structure):
```
---
title: Plan-writer Handover <N>
date: <YYYY-MM-DD>
team: <team-name>
predecessor: or-plan-writer-<N>
plan_draft: <path-or-none>
---

# Plan-writer Handover <N>

## Where we are in the workflow
- Plan checklist progress: <which steps done>
- Currently: <writing file structure | drafting tasks | running self-review | awaiting user review>

## Tasks drafted so far
- Count: <N> / <total estimated>
- Path: <plan-draft-path>
- Latest revision: <one-line>

## Outstanding user feedback not yet applied
- <bullets>

## What to do next when resumed
<one-paragraph: the exact next action>
```

---

## Protocols

### SPAWN protocol (worker dispatch — supervisor → manager)

PRESERVE FROM the original `assets/spawn-protocol.md` with role names updated to `or-*` subagent types:

```
SPAWN
NAME: <name>
ROLE: implementer | spec-reviewer | code-quality-reviewer | final-reviewer
MODEL: sonnet | opus | haiku
```

Manager broker maps `ROLE` → `subagent_type` (plugin-qualified — see **Plugin Packaging**):
- `implementer` → `claude-toolkit:or-implementer`
- `spec-reviewer` → `claude-toolkit:or-spec-reviewer`
- `code-quality-reviewer` → `claude-toolkit:or-code-quality-reviewer`
- `final-reviewer` → `claude-toolkit:or-final-reviewer`

Manager spawns via:
```
Agent({
  team_name: <team>,
  name: <name>,
  subagent_type: <mapped subagent_type>,
  model: <MODEL>,                    // from SPAWN, supervisor picks per task
  prompt: <substituted spawn-context>,
  run_in_background: true
})
```

Then SendMessages supervisor: `Spawned: <name>`.

### SHUTDOWN protocol (worker teardown — supervisor → manager) [NEW]

The manager is the sole manager of agent resources — it owns teardown as well as spawn. The supervisor never shuts a worker down directly (shutdown is a lead action; the supervisor is not the lead). When SDD says a worker's phase is done, the supervisor SendMessages the manager:

```
SHUTDOWN
NAME: <worker-name>
```

The manager then issues `SendMessage(<worker-name>, {type: "shutdown_request", reason: "task phase complete"})`. Teardown is fire-and-forget for the supervisor — no ack is required, so the manager adds no reply; the worker's `shutdown_response` and termination are absorbed as an idle-class wake-up (see the idle taxonomy). This is symmetric with the SPAWN broker: the manager is the only tier that spawns or shuts down teammates.

### SPAWN_RESEARCH protocol (research dispatch — phase agent → manager) [NEW]

Phase agent SendMessages manager:

```
SPAWN_RESEARCH
NAME: <name>
AGENT: <subagent_type>
DEPOSIT: <path>                       (required — findings never transit manager context)
MODEL: <model>                        (optional; defaults to agent's frontmatter default)
PROMPT: <research question>
```

Manager broker behavior:

**All research agents are spawned as background teammates** (`run_in_background: true`, WITH `team_name`) — mechanically identical to worker dispatch. They signal completion by SendMessaging the manager the `RESEARCH_DONE` / `RESEARCH_BLOCKED` token. After relaying to the phase agent, the manager shuts the research teammate down (`shutdown_request`) to keep the roster clean.

| Case | Manager action |
|------|----------------|
| `AGENT` is `or-dependency-researcher` or `or-community-researcher` (always deposit-aware) | Spawn as background teammate with `DEPOSIT` appended to prompt. The agent writes findings to `<DEPOSIT>` and SendMessages manager `RESEARCH_DONE: <path>`. Manager forwards `Research <name> done: <path>` to phase agent, then shuts the researcher down. Manager NEVER opens the findings file. |
| `AGENT` is any other subagent_type (`dependency-researcher`/`community-researcher`/`Plan`/`Explore`/`general-purpose`, …) | Wrap: spawn `general-purpose` as a background teammate with a prompt that imitates the requested agent's style + writes to `<DEPOSIT>` + SendMessages `RESEARCH_DONE: <path>`. (Or if the requested agent already has both `Write` and `SendMessage`, spawn it directly with deposit instruction appended.) Manager shuts it down after relay. |

If a SPAWN_RESEARCH omits `DEPOSIT`, the manager rejects it (findings must never transit manager context): SendMessage the phase agent `SPAWN_RESEARCH rejected — DEPOSIT is required.` and take no further action on that request.

Then SendMessages phase agent: `Spawned: <name>`.

### Research-deposit semantics (used by deposit-aware agents)

When a deposit-aware research agent receives a `DEPOSIT: <path>` parameter:

1. Conduct research per the methodology skill.
2. Write the full findings to `<path>` using the Write tool.
3. SendMessage manager (parent): `RESEARCH_DONE: <path>` — exact text, nothing else.
4. If unable to complete: write partial findings to `<path>` and SendMessage `RESEARCH_BLOCKED: <path> — <one-line reason>`.

---

## Handover Ladder

| Tier | Threshold | Handover doc | Trigger token |
|------|-----------|--------------|---------------|
| Manager | 200k | `manager-handover-N.md` | (manager surfaces to user — fresh session recommended) |
| Supervisor | 200k | `iteration-N.md` | `ITERATION <N> — STOPPED_FOR_HANDOVER` or `COMPLETED` |
| Phase agent | **150k** | `brainstormer-handover-N.md` / `plan-writer-handover-N.md` | `BRAINSTORMER_HANDOVER` / `PLAN_WRITER_HANDOVER` |
| Research subagent | N/A (one-shot) | — | — |

**Why phase agents handover at 150k** (vs supervisor's 200k): interactive dialogue quality must stay above any compression risk. The handover doc is intentionally <5KB so the successor's initial context = small doc + spec/plan artifact, well under any compression trigger. The original agent's context at handover time is still pre-compression, so the handover doc is written from a clean understanding.

**Manager handover during phase 1 or 2:** The manager-handover template gains two fields:
- `active_phase`: `brainstorm | plan | implement`
- `active_phase_agent`: name of currently-alive phase agent (if any)

So a fresh manager on session-resume knows whether to expect a brainstormer/plan-writer to be alive in the team config or whether implementation was already underway.

---

## Mode Detection (preflight extension)

Preflight subagent receives the user's input and detects mode:

| User input shape | Detected mode | Skip-ahead |
|------------------|---------------|------------|
| Plain text (idea statement) or no input | `idea` | Start at brainstorm |
| Path to a spec file (matches `docs/superpowers/specs/*-design.md` or user-supplied path) | `spec` | Start at plan |
| Path to a plan file (matches `docs/superpowers/plans/*.md` or user-supplied path) | `plan` | Start at implementation |

If mode detection is ambiguous (e.g., user passes a path that doesn't match either convention), preflight asks the user explicitly via `AskUserQuestion`: "I see you provided `<input>`. Is this an idea, a spec, or a plan?"

Preflight `PREFLIGHT_OK` block extended:
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

---

## Manager Context Discipline

PRESERVE FROM the original `subagent-driven-development-at-scale` SKILL.md sections (verbatim or with `or-*` naming updates):

- **Core Principle: Manager Context Is Sacred** (entire section)
- **Proactive Status Reporting (all tiers)** (entire section, with phase-agent reporting added: phase agents report `BRAINSTORM_COMPLETE` / `PLAN_COMPLETE` / `<PHASE>_HANDOVER` proactively)
- **Required Communication Style (HARD RULE)** (entire section) — with a key addition: during phases 1 and 2, the manager produces NO chat output at all. The user talks to the phase agent directly; the manager is invisible. The terse-style rules apply only during preflight, phase transitions, and implementation.
- **Conservation Rules** (entire section) — with one addition: "Never read the findings file written by a deposit-aware research subagent. The findings live on disk for the phase agent."
- **Recovery from Common Gotchas** (entire section, with `or-*` naming updates such as `supervisor-N+1` → `or-supervisor-N+1`) — the operational recovery guidance (stale handover docs, old supervisor still alive on resume, TaskList revert, idle-notification grace) still applies. The orchestrator's phase-agent recovery cases are detailed under "Manager handover during phases 1 and 2" above; cross-reference those rather than duplicate.

### New conservation rules (phase-agent-specific)

- **Manager is silent during phase-agent dialogue.** No relay, no chat output, no narration. Manager wakes only for SPAWN_RESEARCH brokering and phase transitions.
- **The one exception to manager silence: the redirect nudge.** If the user's message lands on the manager during phase 1/2 (it was meant for the phase agent, but the user didn't switch to the teammate), the manager replies exactly once — `<phase-agent> is driving — send your messages to it directly (switch with Shift+Down).` — and does NOT relay the message. This is the only manager→user utterance permitted mid-phase; it joins the acceptable-output list.
- **Findings never transit the manager.** `DEPOSIT` is mandatory, so every research result is written to disk by the researcher and read by the phase agent; the manager only ever sees the `RESEARCH_DONE: <path>` token. Manager NEVER opens, summarizes, quotes, or stores findings.
- **Deposit-aware research is opaque to manager.** Manager sees only `SPAWN_RESEARCH` → `Spawned: <name>` → `RESEARCH_DONE: <path>` → relay `Research <name> done: <path>`. The findings file is never opened by manager.

---

## Red Flags (anti-patterns)

PRESERVE FROM the original SKILL.md "Red Flags" table. ADD:

| Anti-pattern | Why it's wrong |
|--------------|----------------|
| Manager outputs to chat during brainstorm/plan phases | User talks directly to phase agent. Manager output during these phases is a discipline violation. |
| Manager reads the findings file from a deposit-aware research subagent | The whole point of deposit is to keep findings out of manager context. Reading it defeats the protocol. |
| Phase agent invokes `Agent` tool | Phase agents are depth-1; `Agent` will silently fail. Use `SPAWN_RESEARCH`. |
| Phase agent invokes `superpowers:writing-plans` directly | Override rule violated. Brainstormer signals `BRAINSTORM_COMPLETE`; manager spawns the plan-writer. |
| Phase agent invokes execution-handoff or `superpowers:subagent-driven-development` | Override rule violated. Plan-writer signals `PLAN_COMPLETE`; manager spawns the supervisor. |
| Phase agent crosses 150k silently | Manager and user expect proactive `<PHASE>_HANDOVER`. Silent cross degrades user-facing dialogue. |
| Research teammate echoes findings in its message (deposit mode) | Findings live on disk; the SendMessage to manager is `RESEARCH_DONE: <path>` and nothing else. |
| Reviewer agent attempts to edit code | Reviewers have no Write/Edit tools. Tool grant is deliberate. Reviewer findings go back to supervisor → relayed to implementer for fixes. |
| Manager spawns `general-purpose` for a worker role | Worker subagent_type is `or-<role>`. Mapping is in the SPAWN broker. |

---

## Integration with Other Skills

- **Hard dependency:** `superpowers:brainstorming` (pre-seeded into `or-brainstormer.md`)
- **Hard dependency:** `superpowers:writing-plans` (pre-seeded into `or-plan-writer.md`)
- **Hard dependency:** `superpowers:subagent-driven-development` (pre-seeded into `or-supervisor.md`)
- **Hard dependency:** `superpowers:test-driven-development` (pre-seeded into `or-implementer.md`)
- **Hard dependency:** `superpowers:using-git-worktrees` (invoked by preflight)
- **Followed by:** `superpowers:finishing-a-development-branch` (supervisor invokes after final iteration, per existing SDD-at-scale)

---

## When to Use

- User wants to take an idea, spec, or plan all the way to shipped code in one session
- Plan size is unknown at session start (because plan may not yet exist) but expected to benefit from 3-tier orchestration once implementation begins
- User explicitly asks for "full superpowers workflow orchestrated", "brainstorm to ship", or "orchestrated end-to-end"

**When NOT to use:**
- User already has a plan and wants direct execution without phase-agent overhead → use `superpowers:subagent-driven-development` directly
- Ad-hoc exploratory work → no orchestration overhead at all
- Single-question lookups, simple edits → direct chat

---

## Migration from `subagent-driven-development-at-scale`

This skill supersedes `subagent-driven-development-at-scale`. The original can be:
- Left in place (parallel skill; user picks based on starting point)
- Or deleted

No backwards-compatibility constraint for the original. Its content has been adapted where reusable; the original files are reference material going forward.

---

## Implementation Notes

When implementing this design:

1. **PRESERVE wherever possible.** Sections marked PRESERVE FROM should be copied verbatim from the source with minimal edits (naming updates from `general-purpose` → `or-*`, addition of new sections, etc.). Do not re-author content that already works.

2. **NEW content must respect the discipline.** Manager-context conservation is the load-bearing constraint. Every new rule traces back to it.

3. **Validate the in-body skill-load on one teammate first.** Frontmatter `skills:` is inert for teammates (see *Skill loading mechanism* above), so the thing to validate is the **in-body `Skill(...)` call**: spawn one `or-*` agent as a teammate and confirm its STEP 0 `Skill(...)` call actually loads the canonical skill's content into its context, before authoring all nine agent files. (This supersedes the earlier assumption that the `skills:` frontmatter auto-loads — per Claude Code's docs it does not, for teammates.)

4. **Mode detection should be explicit.** If the user's input shape is ambiguous, preflight asks. Never guess.

5. **`research-deposit` skill is the smallest skill.** Author it first as a validation of the skill-creation + pre-seed pattern, then use it to validate `or-dependency-researcher` end-to-end.

6. **Test that each phase agent's terminal override HOLDS — not just that the skill loads.** Note #3 validates that the in-body `Skill(...)` call loads the canonical skill into the teammate's context; that is necessary but insufficient. The load-bearing risk is the *terminal seam*: each pre-seeded skill ends with a forceful directive to invoke the next skill (brainstorming's `<HARD-GATE>` + "writing-plans is the ONLY skill you invoke afterward"; writing-plans' "Execution Handoff" → offer choice → "REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development / executing-plans"), and the agent body must override it. Per the `superpowers:writing-skills` Iron Law, for **each** phase agent add a pressure test that drives the agent to its skill's terminal and verifies it (a) emits the completion signal to the manager (`BRAINSTORM_COMPLETE` / `PLAN_COMPLETE`) and (b) does NOT invoke the forbidden next skill or offer the user an execution choice. Run RED first: confirm a baseline agent *without* the override section actually follows the skill's terminal (proving the override is load-bearing) before relying on it. The baseline agent must keep its STEP 0 `Skill(...)` call and drop *only* the override section — otherwise RED "passes" for the wrong reason (no skill loaded ⇒ no terminal pressure to resist). Belt-and-braces (in-body `Skill(...)` call + explicit Closed-loopholes list) is unverified until this test is GREEN.

7. **The seven non-research agent bodies are already drafted** in `docs/superpowers/drafts/` — they are the current source of truth for frontmatter and body. At implementation, finalise them into the plugin's `agents/` directory via the agent-authoring tooling rather than re-authoring. Author the two research bodies (`or-dependency-researcher`, `or-community-researcher`) fresh from the "Research agent body" template at that time.

8. **Decompose the implementation plan into ~4 self-contained, independently-testable sub-phase plans.** Suggested split: shared methodology + `research-deposit` skills → phase agents + orchestrator skill skeleton → supervisor + workers + skill assets → manager-discipline `SKILL.md`. Sequence within that per the notes above: `research-deposit` first (#5), validate the `skills:` pre-seed on one agent (#3), add the override-holding test per phase agent (#6).

9. **Test the anti-drift resume discipline, not just the terminal override.** The flush-on-resume, interrupted-turn-capture, and latest-revision cross-check rules (see "Phase-agent anti-drift resume discipline") are load-bearing against lost intent. For each phase agent, add a resume test: seed a handover doc with a not-yet-applied preference plus a "Latest revision" the artifact does not yet contain, spawn the successor, and verify it writes BOTH into the spec/plan before engaging the user. RED first: confirm a successor *without* the discipline leaves the artifact stale, proving the rules are load-bearing.

10. **Verify `AskUserQuestion` surfaces from a subagent and from a teammate before relying on it.** Preflight (a foreground one-shot subagent) prompts the user for worktree name + base branch + mode disambiguation via `AskUserQuestion`, and the phase agents (teammates) lean on it throughout the brainstorming / plan dialogue. Only direct *text* dialogue with a teammate is confirmed; structured `AskUserQuestion` from a non-main agent is not. Spike both paths — (a) a foreground subagent surfacing `AskUserQuestion`, and (b) a teammate surfacing it — alongside the note-#3 spike. If a tier cannot surface it, fall back to plain-text questions there: the phase agents' confirmed direct dialogue already supports that, and preflight's prompts would move up to the manager (which can always use `AskUserQuestion`). Until this is GREEN, preflight's reliance on `AskUserQuestion` is unverified.

11. **Confirm teammates receive the task-management tools, and the brainstorming checklist works with them.** The phase agents no longer list task tools in frontmatter, on the basis that Claude Code grants `SendMessage` + the task-management tools to every teammate regardless of frontmatter (F7). Verify in the same spike: spawn a teammate with no `Task*` (or `TodoWrite`) in frontmatter and confirm it can create/update tasks, and that the brainstorming skill's checklist step runs with whatever todo/task tool the teammate has (`TodoWrite` in standard Claude Code, `Task*` here). If teammates do NOT get them automatically, re-add `TaskCreate/TaskUpdate/TaskList` to `or-brainstormer`'s frontmatter.

---

## Open Questions (resolved during brainstorming)

| Question | Resolution |
|----------|------------|
| Mode detection vs always-brainstorm-first | Mode detect at preflight |
| Skill identity (new vs replace) | New skill, distinct name (`or-superpowers-at-scale`); supersedes original |
| Worktree timing | Early (preflight creates before brainstorming, asks user for name + base branch) |
| Phase agent compression risk | Lower handover threshold to 150k; constrain handover doc to <5KB |
| Phase agent subagent dispatch | `SPAWN_RESEARCH` broker pattern; manager mediates |
| Subagent allowlist | Open-ended — phase agent can request any subagent_type |
| Communication with user during phases 1/2 | Direct (Claude Code teammate routing); manager silent |
| Specific agent files vs general-purpose + briefs | Specific `or-*` agents; briefs absorbed into agent file bodies |
| Existing SDD-at-scale skill | Superseded — no need to maintain |
| Methodology skill sharing | Both original and `or-*` researchers pre-seed the shared methodology skills |
| Asset naming convention | `or-*` prefix on orchestrator-specific public-facing assets (agents, skills); shared methodology skills unprefixed |
| Code-quality-reviewer model | opus |
| Research agents model | opus |
| Implementer model | Configurable — supervisor picks per task via SPAWN MODEL field |
| Asset content reuse | PRESERVE existing SDD-at-scale content wherever it carries over |

---

## Clarifications (post-review)

### Manager handover during phases 1 and 2

When manager context crosses 200k while a phase agent is alive:

1. Manager stops accepting new SPAWN_RESEARCH requests. SendMessage active phase agent: `MANAGER STOPPING — write your handover doc before any further messages, then await shutdown.`
2. Phase agent first records the interrupted turn's unresolved intent into the handover doc's not-yet-applied section (see "Phase-agent anti-drift resume discipline"), then writes its handover doc (per the phase-specific template) and SendMessages manager: `<PHASE>_HANDOVER — doc: <path>`.
3. Manager writes `manager-handover-<N>.md` with `active_phase` and `active_phase_agent` populated, including the phase-agent handover doc path.
4. Manager tells user: "Manager context >200k — recommend fresh session. New manager reads `manager-handover-<N>.md` first."

**Fresh manager session resume (phase 1 or 2):**

1. Read `manager-handover-<N>.md`, identify `active_phase` and `active_phase_agent`.
2. Confirm phase agent's identity via `~/.claude/teams/<team>/config.json`.
3. If old phase agent is still alive, `SendMessage(<phase-agent>, {type: "shutdown_request", reason: "manager handover; or-<phase>-N+1 will resume"})`.
4. Spawn `or-<phase>-N+1` with spawn-context pointing at the phase-agent handover doc + the spec/plan artifact path.
5. Resume spawn-broker role; user resumes conversation with the new phase agent.

Before reopening dialogue, the new phase agent runs the flush-on-resume and latest-revision cross-check (see "Phase-agent anti-drift resume discipline" below), so no intent the predecessor captured is lost across the manager handover.

This parallels the existing fresh-manager-session protocol for implementation-phase handover.

### Phase-agent anti-drift resume discipline

The recurring failure mode across handovers is **unrecorded intent**: a preference or revision the user stated in dialogue, captured in a handover doc but never written into the spec/plan artifact. Because each handover is a lossy summary, intent that lives only in handover docs degrades with every hop. The fix makes the **artifact the running ledger** and the handover doc a thin pointer. Three rules, carried in the phase-agent bodies (`or-brainstormer.md` / `or-plan-writer.md`, authoritative) and verified at implementation (impl-note #9):

1. **Flush on resume.** Before any new dialogue, a resuming phase agent applies every "captured but not yet in the artifact" bullet from the inherited handover doc into the spec/plan now (asking the user first only where a bullet needs confirmation). Only genuinely-open items carry forward; an applied preference never appears in a second handover doc.
2. **Capture the interrupted turn on `MANAGER STOPPING`.** The self-triggered (150k) handover finishes the turn in flight, so nothing is mid-air; the manager-triggered handover does not (it stops "before any further messages"). So before writing its handover token, the phase agent records the interrupted turn's unresolved intent into the handover's not-yet-applied section — otherwise that turn's intent is the one thing flush-on-resume cannot recover.
3. **Latest-revision cross-check.** On first read, the successor reconciles the artifact against the handover's stated latest revision (and, for the plan-writer, its task count). A mismatch means the predecessor described a revision verbally but handed over before writing it to the file — the successor applies it (or confirms with the user) before continuing.

Together these close the two drift channels: the lossy-summary chain (rules 1–2) and the verbal-revision-before-file-write race (rule 3). The artifact always reflects the full known intent before the conversation moves on.

### SPAWN_RESEARCH discipline (manager-side enforcement)

For deposit-aware research (case 1 in the SPAWN_RESEARCH table), the manager MUST treat the research teammate's `RESEARCH_DONE`/`RESEARCH_BLOCKED` SendMessage as a protocol token, not free-form text:

- Extract the first `RESEARCH_DONE: <path>` or `RESEARCH_BLOCKED: <path> — <reason>` line.
- Discard everything else in the message body (do NOT relay, do NOT echo, do NOT store).
- If neither token is present, manager treats it as a protocol violation: SendMessage phase agent `Research <name> protocol violation — researcher returned non-protocol output, inspect <best-effort-path-or-none>` and proceed.

This is what makes the deposit case truly opaque to manager context. The `research-deposit` skill's instructions to the agent are NOT load-bearing on their own — the manager's broker enforces the discipline.

### `or-implementer.md` frontmatter

The agent file's frontmatter does NOT include a `model:` field. Every SPAWN message for an implementer worker MUST include `MODEL:` — the supervisor picks based on SDD's model-selection guidance per task. If a SPAWN omits `MODEL` for an implementer, the manager treats it as a protocol violation and SendMessages supervisor: `SPAWN rejected — implementer requires explicit MODEL field.`

All other agent files DO include `model:` in frontmatter (their listed default). The SPAWN `MODEL` field overrides per spawn if present.

### Mode = `plan` team creation

For mode = `plan`, the preflight subagent:

1. Verifies the plan file exists and extracts metadata (per original preflight behavior).
2. AskUserQuestion for worktree name + base branch.
3. Creates the worktree.
4. Returns `PREFLIGHT_OK` with `mode: plan`.

Manager then `TeamCreate({team_name: <slug-from-plan-or-worktree>})` BEFORE spawning the supervisor. Team creation always happens at this manager step regardless of mode — it is not phase-1-specific. For modes `idea` or `spec`, the same `TeamCreate` happens before the first phase agent is spawned.

### Plan→implementation go-ahead (F6)

The plan→implementation transition is the one phase boundary the manager gates with the user. After `PLAN_COMPLETE` (modes `idea` / `spec`), and before spawning the supervisor, the manager surfaces a single line — e.g. `Plan approved at <path>. Start implementation? It will run multiple tasks autonomously.` — and waits for the user's go-ahead. On approval it proceeds (`TeamCreate` is already done; spawn `or-supervisor-1`). This is a phase-transition confirm before the expensive, hard-to-pause implementation phase — it does NOT gate any normal in-flow action (local commits and the like stay ungated). The plan-writer's final dialogue turn tells the user to switch to the manager, so the go-ahead is seen (per F3 routing). Mode `plan` has no such gate: invoking `/or-superpowers-at-scale <plan-path>` is itself the go-ahead, so the manager spawns the supervisor directly (per the mode-`plan` first message).

### User mid-phase intervention (declared out of scope for v1)

Full mid-phase mode-switching (e.g., "I have a spec now, skip ahead to plan-writing") is **out of scope** for v1. If the user wants to change tracks, they exit and restart with `/or-superpowers-at-scale <new-input>`.

A lightweight abort path is supported: if the phase agent decides during dialogue that the user wants to end the session, it SendMessages manager: `PHASE_ABORT — reason: <user request>`. Manager surfaces a single line to user: `Phase agent reports abort. Confirm by typing 'exit'; otherwise the phase continues.` On confirm, manager shuts down the phase agent and ends the orchestrator session cleanly (the worktree, spec/plan drafts, and any handover docs remain on disk).

### Naming consistency: `manager`

The original `subagent-driven-development-at-scale` skill addresses the manager as `team-lead` in SPAWN protocol prose. The new skill uses `manager` consistently. When PRESERVING content from the original assets, normalize all `team-lead` references to `manager`. The role is unchanged; only the name is normalized.

### Worker brief inventory

`worker-generic-brief.md` is NOT carried into the new skill's `assets/` directory — its content is absorbed into the agent file bodies (`or-implementer.md`, `or-spec-reviewer.md`, `or-code-quality-reviewer.md`, `or-final-reviewer.md`). Similarly, `supervisor-protocol.md` is absorbed into `or-supervisor.md`'s body. The Asset Inventory table is complete as listed; these two original assets are reference material, not preserved assets.

### `or-supervisor.md` body composition

The agent file body for `or-supervisor.md` contains:

- Identity preamble — adapted from the original `supervisor-brief.md` Identity section
- Required Reading list (read plan, then prior `iteration-N-1.md` if applicable, then `manager-handover-M.md` if applicable) — adapted from `supervisor-brief.md`
- STEP 0 directive — invoke `superpowers:subagent-driven-development` and follow it verbatim, with **one adaptation** (dispatch via SPAWN, not the `Agent` tool) and **one override** (spawn the spec + code-quality reviewers in parallel, where SDD describes them sequentially) — adapted from `supervisor-protocol.md`
- Operating disciplines (depth-1 constraint, SPAWN protocol summary, worker naming convention, topology disciplines, iteration handover trigger) — adapted from `supervisor-protocol.md`

The agent file body is the agent's persistent instruction set; `supervisor-spawn-context.md` provides per-spawn variables (supervisor name, plan path, branch, handover dir, prior-iteration handover path if N>1).

### Handover trigger token shape

Tokens use the suffix `_HANDOVER` for handover events and `_COMPLETE` for terminal completion:

- `BRAINSTORM_COMPLETE — spec: <path>`
- `PLAN_COMPLETE — plan: <path>`
- `BRAINSTORMER_HANDOVER — doc: <path>`
- `PLAN_WRITER_HANDOVER — doc: <path>`
- `ITERATION <N> — STOPPED_FOR_HANDOVER` / `ITERATION <N> — COMPLETED` (supervisor — PRESERVED from original)

The two forms are intentional: `_COMPLETE` is terminal (phase done); `_HANDOVER` is mid-phase (context exhaustion). Manager handles them differently.

### `or-final-reviewer` naming exception

All other workers follow `or-<role>-task<N>`. `or-final-reviewer` runs once per branch (not per task), so it has no task suffix. This mirrors the original SDD-at-scale convention and is intentional, not an inconsistency.

---

## Manager definition tightening (post-second-review)

A focused comparison of the manager's definition between this skill and the legacy `subagent-driven-development-at-scale` surfaced additional points. Since the manager is the only non-refreshable tier, drift here compounds — these clarifications are load-bearing.

### Phase-agent PAUSE relay

Phase agents MAY request a PAUSE for actions **beyond the superpowers workflow** — genuinely destructive or visible-to-others operations (e.g., a `git push`, deleting files outside the worktree, or an external API call). Local commits that the underlying skill performs as part of its normal flow are NOT a pause case: they are local, reversible, and inside the worktree. The orchestrator faithfully enables the workflow; it does not gate the skill's own normal actions. The PAUSE token from a phase agent:

```
PHASE_PAUSE
action: <one-line>
impact: <one-line>
```

Manager relays one short paragraph to user (action + impact only — same discipline as legacy supervisor PAUSE). After user approval, manager SendMessages phase agent: `PROCEED` or `REJECTED — reason: <line>`. Same shape as the supervisor PAUSE protocol; just different originating tier.

### Idle wake-up taxonomy (manager)

Every wake-up the manager experiences falls into one of two buckets:

| Wake-up source | Bucket | Manager response |
|---|---|---|
| `SPAWN` (worker dispatch from supervisor) | **Action required** | Spawn worker; reply `Spawned: <name>` |
| `SPAWN_RESEARCH` (from phase agent) | **Action required** | Spawn research subagent; reply `Spawned: <name>` |
| Research teammate `RESEARCH_DONE`/`RESEARCH_BLOCKED` (SendMessage) | **Action required** | Relay path to phase agent, then shut the researcher down |
| Phase agent `<PHASE>_COMPLETE` | **Action required** | Shutdown phase agent; spawn next-phase agent. For `PLAN_COMPLETE`: first surface the implementation go-ahead and await the user's approval, *then* spawn the supervisor (F6) |
| Phase agent `<PHASE>_HANDOVER` | **Action required** | Execute phase-handover protocol |
| Phase agent `PHASE_PAUSE` | **Action required** | Relay to user |
| Supervisor `ITERATION N — STOPPED_FOR_HANDOVER / COMPLETED` | **Action required** | Execute iteration-handover protocol |
| Supervisor PAUSE request | **Action required** | Relay to user |
| Supervisor `SHUTDOWN` request (worker teardown) | **Action required** | Issue `shutdown_request` to the named worker; no reply needed |
| Worker / research-teammate boot, `shutdown_response`, or termination notifications | **Idle** | No output, no tool calls |
| Supervisor turning internally | **Idle** | No output, no tool calls |
| Teammate progress events | **Idle** | No output, no tool calls |
| Hook reminders / system reminders | **Idle** | No output, no tool calls |
| Phase-agent ↔ user dialogue events (the routing happens out-of-band) | **Idle** | No output, no tool calls — phase agent owns the dialogue |
| User message addressed to the manager during phase 1/2 | **Action required** | Reply once with the redirect nudge; do not relay |

Idle wake-ups produce **no output and no tool calls**. End the turn empty. Reflexive `Standing by.` on any idle wake-up is the discipline violation this skill exists to prevent.

### Manager-side TaskList still forbidden

Conservation Rule #1 from the legacy skill is doubly important during phase 1/2 silent stretches: the temptation to "track which phase we're in" via TaskList must be resisted. Phase state lives in the team config (member roster) and the handover doc series. The manager owns no TaskList for plan tasks OR for phase tracking.

### Manager handover during phase 1/2 — user signaling

The user is mid-conversation with the phase agent when manager initiates a >200k handover. The user-facing signaling is the phase agent's responsibility, NOT the manager's:

- Manager SendMessages phase agent: `MANAGER STOPPING — write your handover doc before any further messages, then await shutdown.`
- Phase agent tells user: `Manager is initiating a handover. Wait for the fresh-session prompt before continuing the conversation.`
- Phase agent captures the interrupted turn's intent into the handover doc's not-yet-applied section (see "Phase-agent anti-drift resume discipline"), writes its handover doc, SendMessages manager the `<PHASE>_HANDOVER` token, and awaits shutdown.

Manager does NOT directly output to user during phases 1/2 — the phase agent is the user-facing tier; only it signals.

### Manager forbidden to read spec/plan artifact (NEW conservation rule)

The manager does NOT read the spec file (Phase 1 output) or plan file (Phase 2 output) at any point in the session. These are inputs to the next phase agent / supervisor; the manager substitutes the path into the next spawn-context and nothing more. If the manager wants to "verify it exists," the preflight subagent or the next-phase agent does that on its behalf.

Similarly, manager does NOT read phase-agent handover docs — successor phase agents do, at resume. Manager only knows their paths.

This is a NEW conservation rule (legacy rule #2 forbade reading the plan; this extends to all artifacts written by lower tiers).

### SPAWN_RESEARCH relay token shape

For the completion relay, manager SendMessages phase agent:

- **All research is deposit-aware (or wrapped to deposit):** `Research <name> done: <path>` — exact phrasing, 5 words + path. There is no non-deposit relay — `DEPOSIT` is mandatory (F4), so findings never transit manager context.

These reply patterns are codified in the manager-output acceptable list alongside `Spawned: <name>`, `Acknowledged.`, and `Standing by.`. `Research <name> done: <path>` is the only multi-word allowed manager-to-teammate utterance beyond the legacy three.

### First-session-message exception (adapted)

Legacy first-message exception adapts by mode. The phase-agent modes also tell the user how to reach the teammate (per F3 — the user must address the teammate directly, or messages land on the manager), so they run a little past the legacy 15-word budget; `plan` mode keeps the terse form:

- Mode `idea`: `Spawned or-brainstormer-1 (opus, background) on team \`<name>\`. Talk to it directly — switch with Shift+Down. It's driving Phase 1.`
- Mode `spec`: `Spawned or-plan-writer-1 (opus, background) on team \`<name>\`. Talk to it directly — switch with Shift+Down. It's driving Phase 2.`
- Mode `plan`: `Spawned or-supervisor-1 (opus, background) on team \`<name>\`. Standing by.`

After this single message, manager reverts to terse-protocol (and silent during phases 1/2).
