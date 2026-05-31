# `or-superpowers-at-scale` — Plan 2: Phase Agents + Orchestrator Skill Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Skill/agent authoring steps are also governed by **superpowers:writing-skills** — load it before authoring any skill file.

**Goal:** Finalize the two Phase-1/2 teammate agents (`or-brainstormer`, `or-plan-writer`) from their reviewed drafts into the plugin's `agents/` directory, lay down the orchestrator skill's structural skeleton (`skills/or-superpowers-at-scale/SKILL.md` — identity, when-to-use, architecture, integration), and author the suite's behavioral-validation spikes as a deferred-execution doc — so the orchestrator's user-facing tier and its self-describing entry skill exist on the branch, with every load-bearing behavioral risk captured for execution at cutover.

**Architecture:** Two agent files moved verbatim from `docs/superpowers/drafts/` to `plugins/claude-toolkit/agents/` (single source of truth — the draft is already the final body; nothing is re-authored). One new skill file carrying only its self-contained overview sections (the operating-discipline body is appended later, in Plan 4 — progressive additive assembly, never stub-and-fill). One new validation doc capturing the five behavioral spikes (impl-notes #3/#6/#9/#10/#11) as runnable RED/GREEN procedures whose execution is deferred to suite cutover against the *installed* plugin.

**Tech Stack:** Claude Code plugin components — Markdown files with YAML frontmatter, inside the `claude-toolkit` plugin repo (`I:\Dev\claude-toolkit`, real git). No compiled code. Verification is by structural assertion (frontmatter/content greps + `claude plugin validate`) in-session; all behavioral validation is deferred to cutover (the plugin is not installed in the authoring session). Per-task `git commit` is the rollback boundary.

---

## Scope of this plan (Plan 2 of 4)

This is the **orchestrator structural foundation** plan of the `or-superpowers-at-scale` suite (design: `docs/superpowers/specs/2026-05-24-or-superpowers-at-scale-design.md`, authoritative; see esp. the **Plugin Packaging**, **Agent Inventory** + §"Skill loading mechanism", **Skill Inventory**, **Architecture**, and impl-notes **#3/#6/#8/#9/#10/#11**). It builds the user-facing Phase-1/2 tier and the entry skill's shell. It depends on **none** of Plan 1's research skills directly, but reuses the same skill-authoring + structural-verification pattern Plan 1 validated.

In scope:
- **Finalize `or-brainstormer`** → `plugins/claude-toolkit/agents/or-brainstormer.md` (verbatim `git mv` from the reviewed draft).
- **Finalize `or-plan-writer`** → `plugins/claude-toolkit/agents/or-plan-writer.md` (verbatim `git mv` from the reviewed draft).
- **Orchestrator skill skeleton** → `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md` (NEW — identity + when-to-use + architecture + integration only; operating discipline deferred to Plan 4).
- **Behavioral-validation spikes doc** → `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` (NEW — impl-notes #3/#6/#9/#10/#11 as deferred-execution procedures).

Out of scope (later plans / cutover):
- The five other `or-*` agents — `or-supervisor`, `or-implementer`, `or-spec-reviewer`, `or-code-quality-reviewer`, `or-final-reviewer` — and the two research agents `or-dependency-researcher` / `or-community-researcher` (Plan 3).
- The skill's `assets/*` templates — spawn-context, handover, and protocol-reference files (Plan 3).
- The skill's **operating-discipline body** — Mode Detection, SPAWN / SHUTDOWN / SPAWN_RESEARCH protocols, the Handover Ladder, Manager Context Discipline, and Red Flags (Plan 4, appended to the skeleton).
- The optional `commands/or-superpowers-at-scale.md` thin wrapper (user-facing entry — Plan 4, with the release).
- The version bump + marketplace sync + README + push (Plan 4 release step — see "Release deferral" below).
- **Execution** of the spikes authored here (suite cutover, post-Plan-4, against the installed plugin).

## Git workflow (READ FIRST)

`I:\Dev\claude-toolkit` **is a real git repository** (verified). All work happens on the existing feature branch **`or-superpowers-at-scale`** with **one commit per task** (design §"Git workflow"). The real-git review/rollback loop is the SDD rollback boundary.

- The working directory is `C:\Users\marti\.claude` (a different drive from the repo). **Every git command targets the repo explicitly via `git -C I:\Dev\claude-toolkit …`** — do not rely on the ambient cwd, and do not `cd` (it can trigger a permission prompt).
- Use **`git mv`** for the two phase-agent finalizations (Task 1) — it moves the file in one tracked operation, preserving history and guaranteeing the content is byte-identical to the reviewed draft (no transcription). Do **not** hand-copy the bodies.
- Do **not** `git push` in this plan. The branch stays local until the whole suite is reviewed and the user approves the release (design handover: push only when asked; the push *is* the suite release).

## Release deferral (carried from Plan 1 — user-confirmed 2026-05-30)

Per Plan 1's resolution and the spec's reconciled Release-discipline wording: the whole orchestrator ships as a **single** minor increment `1.1.1 → 1.2.0`, finalized in a dedicated **Plan 4** release step on user approval. **Plan 2 makes no version / manifest / README change** — nothing here is user-visible until the release push. New components are committed to the feature branch only.

## Verification approach (why every behavioral check is deferred)

The `claude-toolkit` marketplace is **not installed in the authoring session** (design handover; confirmed in Plan 1). Two consequences bound what Plan 2 can verify in-session:

1. **The finalized agents are not live subagent types.** `subagent_type: claude-toolkit:or-brainstormer` is not registered in this session — the files are in the repo, not installed — so they cannot be spawned to observe behavior here.
2. **The skeleton skill is not loadable.** `Skill('claude-toolkit:or-superpowers-at-scale')` would not resolve the file just written.

So **Plan 2's hard gates are structural** — `claude plugin validate` + frontmatter/content greps run against the repo files, plus a content-integrity check that the moved agent bodies are intact. **Every behavioral check is deferred** to suite cutover (after the Plan 4 release), run against the *installed* plugin (`claude plugin install claude-toolkit`). That deferred set is exactly the five spikes authored in Task 3 (impl-notes #3/#6/#9/#10/#11) plus Plan 1's deferred wrapper check — see the spikes doc's "Cutover checklist" and design §"Cutover & end-state validation".

**Why author the spikes now, if they run later?** The spikes encode the suite's load-bearing behavioral risks — the in-body skill-load mechanism (#3), each phase agent's terminal-override (#6) and anti-drift-resume (#9) disciplines, `AskUserQuestion` surfacing (#10), and teammate task-tool grants (#11). These are tied to the phase agents finalized here and the topology decisions in the spec; capturing them as precise procedures while that context is fresh (and co-located with the agents they exercise) is higher-fidelity than reconstructing them at cutover. The drafts already *bet* on these mechanisms (e.g. the in-body `Skill(...)` call, the `skills:`-is-inert note, no `Task*` in frontmatter); the spikes are the documented confirmation of those bets, with a fallback for each.

## Progressive assembly of `SKILL.md` (skeleton now, discipline in Plan 4)

The orchestrator `SKILL.md` is assembled across the suite, per impl-note #8's split ("phase agents + orchestrator skill skeleton" → "supervisor + workers + skill assets" → "manager-discipline `SKILL.md`"):

- **Plan 2 (this plan)** writes the skeleton: frontmatter (the pinned description), Goal, When to Use / When NOT, Architecture (topology + phase-flow overview), and Integration with Other Skills. These are the self-contained "what this skill is and when to use it" sections.
- **Plan 3** adds the `assets/*` template files the skill references.
- **Plan 4** **appends** the operating-discipline sections (Mode Detection, the SPAWN / SHUTDOWN / SPAWN_RESEARCH protocols, the Handover Ladder, Manager Context Discipline, Red Flags) and ships the release.

This is **additive** assembly, not stub-and-fill: the skeleton contains **no** "TBD"/"added later" markers (those are forbidden placeholders). It ends cleanly after Integration; later plans add whole, complete sections. At every commit the file is structurally valid (parses, valid frontmatter) and every section present is complete. The skill is not *behaviorally* complete until Plan 4 and not *live* until install — but since nothing is released until cutover, an in-progress-but-valid skill on the feature branch is the intended state.

## Source-of-truth references

| Artifact being built | Source content | Notes |
|---|---|---|
| `agents/or-brainstormer.md` | `docs/superpowers/drafts/or-brainstormer.md` (committed `06a7f1d`) | Verbatim **move** (`git mv`). Draft is the authoritative final body (design §"Agent Inventory" → "Body source"). |
| `agents/or-plan-writer.md` | `docs/superpowers/drafts/or-plan-writer.md` (committed `06a7f1d`) | Verbatim **move** (`git mv`). |
| `skills/or-superpowers-at-scale/SKILL.md` | Design §"`or-superpowers-at-scale` skill frontmatter" (pinned description), §"Goal", §"Architecture" (Topology + Phase flow), §"Integration with Other Skills", §"When to Use" | NEW — inlined in full in Task 2. Skeleton layer only. |
| `docs/superpowers/validation/…-behavioral-spikes.md` | Design impl-notes #3, #6, #9, #10, #11 + §"Cutover & end-state validation" | NEW — inlined in full in Task 3. Deferred-execution procedures. |

All plugin paths are relative to the plugin root `I:\Dev\claude-toolkit\plugins\claude-toolkit\`. The two draft source files are the **reviewed, authoritative** phase-agent bodies — they already encode every spec decision (no `Agent` tool; `Skill` + `SendMessage` in `tools`; `skills:` retained as documentation with an inert-for-teammates note; the terminal override + Closed-loopholes list; the anti-drift resume discipline). **Nothing in the bodies is edited during the move** — both reach the orchestrator's SPAWN protocol and handover templates by invoking `Skill('claude-toolkit:or-superpowers-at-scale')` (install-agnostic; the pre-suite skill-invocation rework applied this at the drafts), not by any path that the file's directory could affect.

**Why the agent bodies are moved, not re-inlined:** the body is reviewed content that already exists verbatim in a committed repo file. Re-typing ~165 lines per agent into this plan would invite transcription drift and create a second copy of the very thing being finalized. `git mv` relocates the exact bytes and preserves history; verification is by frontmatter/anchor greps + `claude plugin validate`. (This is the same deliberate exception Plan 1 made for the verbatim methodology move.)

---

## Task 1: Finalize the two phase agents (`or-brainstormer`, `or-plan-writer`)

Move both reviewed drafts into the plugin's `agents/` directory via `git mv` (single source of truth — the draft *is* the final body). They are finalized together: identical mechanism, a cohesive "Phase-1/2 user-facing tier" unit, one commit. The bodies are not edited.

**Files:**
- Move: `docs/superpowers/drafts/or-brainstormer.md` → `plugins/claude-toolkit/agents/or-brainstormer.md`
- Move: `docs/superpowers/drafts/or-plan-writer.md` → `plugins/claude-toolkit/agents/or-plan-writer.md`

- [ ] **Step 1: Verify the source drafts exist and the destinations do not (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-brainstormer.md"          # expect True
Test-Path "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-plan-writer.md"           # expect True
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-brainstormer.md"    # expect False
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-plan-writer.md"     # expect False
```
Expected: the two drafts are `True`, the two destinations are `False` (confirms we are finalizing, not overwriting an existing agent).

- [ ] **Step 2: Capture the source line counts (integrity baseline)**

```powershell
(Get-Content "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-brainstormer.md" | Measure-Object -Line).Lines   # record (≈166)
(Get-Content "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-plan-writer.md"  | Measure-Object -Line).Lines   # record (≈181)
```
Record both numbers. After the move (Step 5) the destination line counts must match exactly — proving the move was byte-faithful.

- [ ] **Step 3: Move `or-brainstormer.md` with `git mv`**

```powershell
git -C I:\Dev\claude-toolkit mv docs/superpowers/drafts/or-brainstormer.md plugins/claude-toolkit/agents/or-brainstormer.md
```
Expected: no output (success). The file is now staged as a rename in git.

- [ ] **Step 4: Move `or-plan-writer.md` with `git mv`**

```powershell
git -C I:\Dev\claude-toolkit mv docs/superpowers/drafts/or-plan-writer.md plugins/claude-toolkit/agents/or-plan-writer.md
```
Expected: no output (success).

- [ ] **Step 5: Verify byte-faithful relocation (GREEN — integrity)**

```powershell
# destinations exist, sources gone
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-brainstormer.md"    # expect True
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-plan-writer.md"     # expect True
Test-Path "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-brainstormer.md"          # expect False
Test-Path "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-plan-writer.md"           # expect False
# line counts unchanged (compare to Step 2)
(Get-Content "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-brainstormer.md" | Measure-Object -Line).Lines
(Get-Content "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-plan-writer.md"  | Measure-Object -Line).Lines
# git sees pure renames (R100 = 100% similarity, no content change)
git -C I:\Dev\claude-toolkit diff --cached --find-renames --name-status
```
Expected: destinations `True`, sources `False`; line counts equal to Step 2; `git diff --cached` shows two `R100` rename entries (`docs/superpowers/drafts/… -> plugins/claude-toolkit/agents/…`) and **no** content modification.

- [ ] **Step 6: Verify the load-bearing frontmatter and body anchors survived (GREEN — content)**

```powershell
$b = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-brainstormer.md"
$p = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-plan-writer.md"
# frontmatter: name, model, skills present; tools includes Skill + SendMessage; NO Agent tool
Select-String -Path $b -Pattern '^name: or-brainstormer$','^model: opus$','^skills: \[superpowers:brainstorming\]$','^tools:.*\bSkill\b.*\bSendMessage\b' | Select-Object Line
Select-String -Path $p -Pattern '^name: or-plan-writer$','^model: opus$','^skills: \[superpowers:writing-plans\]$','^tools:.*\bSkill\b.*\bSendMessage\b' | Select-Object Line
Select-String -Path $b,$p -Pattern '^tools:.*\bAgent\b'    # expect NO match (depth-1 constraint)
# body anchors: STEP 0 in-body Skill() call, terminal override token, Closed loopholes, anti-drift resume
Select-String -Path $b -Pattern "Skill\(""superpowers:brainstorming""\)",'BRAINSTORM_COMPLETE','### Closed loopholes','## On resume after a handover' | Select-Object Line
Select-String -Path $p -Pattern "Skill\(""superpowers:writing-plans""\)",'PLAN_COMPLETE','### Closed loopholes','## On resume after a handover' | Select-Object Line
```
Expected: every `name`/`model`/`skills`/`tools` line matches for each agent; **no** `Agent` in either `tools:` line; each body shows its in-body `Skill(...)` call, its completion token (`BRAINSTORM_COMPLETE` / `PLAN_COMPLETE`), its Closed-loopholes list, and its anti-drift resume section. (These are the four mechanisms the spikes in Task 3 exercise; their presence is the structural precondition.)

- [ ] **Step 7: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes (valid `plugin.json`; the two new agent files have valid frontmatter). If the `claude` CLI is unavailable in this environment, record that explicitly and rely on Steps 5–6 as the structural gate — note the skip rather than claiming a pass.

- [ ] **Step 8: Commit**

```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "feat(agents): finalize or-brainstormer and or-plan-writer phase agents"
```
Expected: one commit on `or-superpowers-at-scale` containing two renames (drafts → `agents/`). `git -C I:\Dev\claude-toolkit show --stat HEAD` should list both files as renames with zero net line change.

---

## Task 2: Orchestrator skill skeleton (`skills/or-superpowers-at-scale/SKILL.md`)

Author the entry skill's structural shell — identity, when-to-use, architecture, integration. This is NEW content, inlined in full below. It deliberately stops after Integration; the operating-discipline body is appended in Plan 4 (see "Progressive assembly of `SKILL.md`"). No placeholders, no forward-stub.

**Files:**
- Create: `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md`

- [ ] **Step 1: Load the authoring discipline**

Invoke `Skill('superpowers:writing-skills')` and skim it. Load-bearing for this task: skill frontmatter is `name` + `description` only (this plugin's convention — see any existing `plugins/claude-toolkit/skills/*/SKILL.md`); the `description` must say *when to use*, not restate the body; the body is the skill's content for the model that loads it.

- [ ] **Step 2: Verify the skill does not yet exist (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
```
Expected: `False`. (Confirms we are creating, not overwriting.)

- [ ] **Step 3: Create the skill directory + file with this exact content**

Create `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md`:

````markdown
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
````

- [ ] **Step 4: Verify frontmatter is valid and the description is when-to-use (GREEN)**

```powershell
Get-Content "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md" -TotalCount 4
```
Expected: a `---` fence, `name: or-superpowers-at-scale`, a `description:` line beginning `Use when the user wants to take an idea, spec, or plan all the way to shipped code`, closing `---`. Confirm the description states *when to use* and includes the "Not for direct execution … or for ad-hoc exploratory work." scoping clause (it mirrors the body's When-NOT-to-use).

- [ ] **Step 5: Verify the skeleton covers exactly its layer — and carries no placeholder/forward-stub (GREEN)**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
# present: the four skeleton sections
Select-String -Path $s -Pattern '^## When to Use$','^## Architecture$','^### Topology$','^### Phase flow$','^## Integration with Other Skills$' | Select-Object Line
# absent: operating-discipline sections (those are Plan 4) — expect NO matches
Select-String -Path $s -Pattern '^## Manager Context Discipline$','^## Red Flags$','^### SPAWN protocol','^## Mode Detection$','^## Handover Ladder$'
# absent: forbidden placeholder markers — expect NO matches
Select-String -Path $s -Pattern 'TBD','TODO','added later','filled in','Plan 4','Plan 3','coming soon'
```
Expected: the five skeleton-section patterns all match; the operating-discipline patterns return **nothing** (correctly deferred to Plan 4); the placeholder/plan-reference patterns return **nothing** (the file is additive, not stub-and-fill, and references no authoring-plan numbers).

- [ ] **Step 6: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes (the new skill has valid frontmatter and a `SKILL.md`). If `claude` is unavailable, record the skip and rely on Steps 4–5.

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md
git -C I:\Dev\claude-toolkit commit -m "feat(skills): add or-superpowers-at-scale orchestrator skill skeleton"
```
Expected: one new file committed on `or-superpowers-at-scale`.

---

## Task 3: Behavioral-validation spikes doc (deferred to cutover)

Author the suite's five behavioral spikes (impl-notes #3/#6/#9/#10/#11) as one runnable, deferred-execution doc. NEW content, inlined in full below. This is the concrete form of Plan 2's "verification spikes" deliverable: the procedures are written now (co-located with the phase agents they exercise, while context is fresh); their RED/GREEN **execution runs at cutover** against the installed plugin (design §"Cutover & end-state validation"). Authoring it is a documentation task — its in-session gate is that the doc exists, is structurally valid, and covers all five impl-notes with a fallback each.

**Files:**
- Create: `I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`

- [ ] **Step 1: Verify the doc does not yet exist (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md"
```
Expected: `False`.

- [ ] **Step 2: Create the validation directory + doc with this exact content**

Create `I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`:

````markdown
# `or-superpowers-at-scale` — Behavioral Validation Spikes

**Status: authored, NOT yet executed.** Execution is **deferred to suite cutover** — after the Plan 4 release, run against the **installed** plugin (`claude plugin install claude-toolkit`). These cannot run in the authoring session: the plugin is not installed there, so the `claude-toolkit:or-*` subagent types are not registered and `Skill('claude-toolkit:…')` would not resolve the repo files — a run there would exercise stale loose `~/.claude` copies or fail spuriously, validating the wrong thing (design §"Cutover & end-state validation"; Plan 1 §"Verification approach").

Each spike states its **purpose**, the **impl-note** it discharges, **setup**, a **RED** baseline (where a baseline is meaningful — it proves the mechanism under test is load-bearing), the **GREEN** pass condition, and the **fallback** if it fails. Where a spike is a pure capability probe (no regression baseline), that is stated.

Run order is top-to-bottom: Spike 1 (does the in-body skill-load work at all) gates the value of Spikes 2–3 (which assume the pre-seeded skill is loaded).

---

## Spike 1 — In-body `Skill(...)` load on a teammate (impl-note #3)

**Purpose:** Confirm that a teammate's first-action in-body `Skill(...)` call loads the canonical skill's content into its context — because the `skills:` frontmatter field is **inert for teammates** (they load skills like a normal session, not from agent frontmatter). Also resolve whether a **same-plugin** skill resolves by bare name or must be plugin-qualified (`claude-toolkit:`).

**Setup:** Plugin installed. A throwaway worktree. A trivial research/idea prompt.

**Facet A — cross-plugin load, phase agent.** Spawn `claude-toolkit:or-brainstormer` as a background teammate with a one-line idea. Observe that its STEP 0 `Skill("superpowers:brainstorming")` call takes effect — i.e. it then behaves per the brainstorming skill (asks one question at a time, proposes 2–3 approaches), rather than free-forming.

**Facet B — same-plugin load + name resolution, research agent.** Spawn `claude-toolkit:or-dependency-researcher` (authored in Plan 3) with a `DEPOSIT:` path. Observe its `Skill("claude-toolkit:dependency-research-methodology")` call loads the methodology. Then, separately, have a teammate attempt the **bare** form `Skill("dependency-research-methodology")` and record whether same-plugin bare names resolve.

**RED baseline (proves the in-body call is load-bearing):** Spawn a teammate variant whose body **omits** the `Skill(...)` call but **keeps** the `skills:` frontmatter. Confirm the skill's content is **not** active (frontmatter alone did not load it). This is what makes the in-body call — not the frontmatter — the load-bearing path for teammates.

**GREEN:** Facet A and Facet B both show the in-body `Skill(...)` call loading the skill content; the RED variant does not.

**Fallback:**
- If **bare** same-plugin names do not resolve: no change — the agent bodies already use the qualified `claude-toolkit:` form. Record "qualified required" as the confirmed convention.
- If the **in-body call does not load for teammates at all** (unexpected — superpowers teammates rely on it): escalate; the whole pre-seed mechanism needs rework before the suite ships. Do not declare the suite done.

---

## Spike 2 — Terminal override holds (impl-note #6) — once per phase agent

**Purpose:** Each phase agent, driven to its pre-seeded skill's terminal step, must emit its completion signal to the manager and must **not** invoke the forbidden next skill or offer the user an execution choice. The pre-seeded skills end with forceful directives to invoke the next skill (`brainstorming`'s "writing-plans is the ONLY skill you invoke afterward"; `writing-plans`' "Execution Handoff" → "Which approach?" → invoke `subagent-driven-development`/`executing-plans`); the agent body must override that.

**Setup:** Plugin installed. For `or-brainstormer`: a tiny idea that can reach an approved spec quickly. For `or-plan-writer`: a minimal approved spec in `docs/superpowers/specs/`.

**Procedure — `or-brainstormer`:** Spawn `or-brainstormer-1`; drive a minimal brainstorm to user approval. At the terminal, verify it (a) SendMessages the manager `BRAINSTORM_COMPLETE — spec: <path>` and (b) does **not** invoke `superpowers:writing-plans`.

**Procedure — `or-plan-writer`:** Spawn `or-plan-writer-1` with the approved spec; drive to a saved, self-reviewed plan. Verify it (a) SendMessages `PLAN_COMPLETE — plan: <path>`, (b) tells the user to switch to the manager, and (c) does **not** invoke `superpowers:subagent-driven-development` / `superpowers:executing-plans` or ask "Which approach?".

**RED baseline (proves the override is load-bearing):** For each agent, spawn a variant that **keeps** its STEP 0 `Skill(...)` call but **drops** the override + Closed-loopholes sections. Confirm it follows the canonical skill's terminal (the brainstormer invokes writing-plans; the plan-writer offers the execution choice). The baseline **must** keep STEP 0 — otherwise RED "passes" for the wrong reason (no skill loaded ⇒ no terminal pressure to resist).

**GREEN:** Each real agent resists the terminal and emits its completion token; each RED variant follows the skill's terminal.

**Fallback:** If an override does not hold, strengthen that agent's Closed-loopholes list / add a pre-terminal interceptor in its body, then re-run until GREEN. The belt-and-braces design (in-body `Skill(...)` call + explicit Closed-loopholes list) is unverified until this is GREEN for both agents.

---

## Spike 3 — Anti-drift resume holds (impl-note #9) — once per phase agent

**Purpose:** A resuming phase agent must flush captured-but-unwritten intent into the spec/plan artifact **before** opening new dialogue — so intent that lived only in a handover doc is not lost across the hop. The artifact is the running ledger; the handover doc is a thin pointer.

**Setup:** Plugin installed. Seed, in a worktree: (a) an artifact (spec for brainstormer / plan for plan-writer) that is **missing one revision**; (b) a handover doc that lists **one not-yet-applied user preference** and states a **"Latest revision"** (and, for the plan-writer, a task count) the artifact does **not** yet contain.

**Procedure:** Spawn the successor (`or-brainstormer-2` / `or-plan-writer-2`) with spawn-context naming the seeded handover doc + artifact. Verify it writes **both** the not-yet-applied preference **and** the missing revision into the artifact before engaging the user (the flush-on-resume + latest-revision cross-check from the agent body's "On resume after a handover").

**RED baseline (proves the discipline is load-bearing):** Spawn a variant whose body **omits** the "On resume after a handover" section. Confirm it leaves the artifact stale (opens dialogue without reconciling).

**GREEN:** The real successor reconciles the artifact first; the RED variant does not.

**Fallback:** If the discipline does not hold, strengthen the flush-on-resume wording in that agent's body, then re-run until GREEN.

---

## Spike 4 — `AskUserQuestion` surfaces from a subagent and a teammate (impl-note #10)

**Purpose:** Confirm a structured `AskUserQuestion` reaches the user from (a) a **foreground one-shot subagent** (preflight prompts for worktree name + base branch + mode disambiguation) and (b) a **teammate** (phase agents lean on it through the dialogue). Only direct *text* dialogue with a teammate is confirmed today; structured `AskUserQuestion` from a non-main agent is not.

**Setup:** Plugin installed.

**Facet A — foreground subagent:** Dispatch the preflight subagent path that issues an `AskUserQuestion` (worktree name + base branch). Confirm the user sees the structured prompt and the chosen answer returns to the subagent.

**Facet B — teammate:** Spawn a phase-agent teammate that issues an `AskUserQuestion` mid-dialogue. Confirm it surfaces to the user and the answer returns.

**RED baseline:** None — this is a capability probe, not a regression. The implicit failure mode is that a tier's `AskUserQuestion` never reaches the user (silently dropped).

**GREEN:** Both facets surface the prompt and return the answer.

**Fallback:** If a tier cannot surface `AskUserQuestion`, fall back to **plain-text questions** there: the phase agents' confirmed direct text dialogue already supports that, and preflight's prompts move up to the manager (which can always use `AskUserQuestion`). Update `assets/preflight-brief.md` and the phase-agent bodies accordingly, then re-validate. Until GREEN, preflight's reliance on `AskUserQuestion` is unverified.

---

## Spike 5 — Teammates receive task tools; brainstorming checklist works (impl-note #11)

**Purpose:** Confirm a teammate with **no** `Task*`/`TodoWrite` in frontmatter still receives the task-management tools (the spec's F7: Claude Code grants `SendMessage` + the task tools to every teammate regardless of frontmatter), **and** that the brainstorming skill's checklist step runs with whatever todo/task tool the teammate has.

**Setup:** Plugin installed.

**Procedure:** Spawn `or-brainstormer-1` (its frontmatter lists no `Task*`/`TodoWrite`). Confirm it can `TaskCreate` / `TaskUpdate` / `TaskList`. Then drive the brainstorming skill to its checklist step and confirm the step runs with the teammate's available todo/task tool (`Task*` in this team harness; `TodoWrite` in standard Claude Code).

**RED baseline:** None — capability probe. The implicit failure mode is that the teammate has no task tool and the brainstorming checklist step cannot run.

**GREEN:** The teammate creates/updates tasks and the brainstorming checklist step runs.

**Fallback:** If teammates do **not** auto-receive the task tools, re-add `TaskCreate, TaskUpdate, TaskList` to `or-brainstormer` (and `or-plan-writer`) frontmatter and re-validate. This would also revisit the spec's F7 assumption (design §"Agent tool-grant decisions" → "Phase-agent task tools").

---

## Cutover checklist

Run once, at suite cutover (after the Plan 4 release), in order (design §"Cutover & end-state validation"):

1. Remove the deprecated loose `~/.claude` copies the plugin supersedes — the drifted `agents/{dependency,community}-researcher.md`, and the loose `design` / `plan-from-design` / `subagent-driven-development-at-scale` assets.
2. `claude plugin install claude-toolkit`.
3. Run **Spike 1 → Spike 5** above, plus Plan 1's deferred wrapper check (a live `Skill('claude-toolkit:dependency-research-methodology')` load and an `or-dependency-researcher` / `dependency-researcher` dispatch that returns a cited report from disk).
4. Record each result inline in this doc. For any spike that fails, apply its **Fallback**, commit the fix, and re-run that spike. **Do not declare the suite done until Spikes 1–3 are GREEN** (Spikes 4–5 have plain-text/frontmatter fallbacks that are acceptable end states if their probe fails).
````

- [ ] **Step 3: Verify the doc exists and covers all five impl-notes + cutover (GREEN)**

```powershell
$v = "I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md"
Test-Path $v                                                                          # expect True
# each impl-note has a spike section
Select-String -Path $v -Pattern 'impl-note #3','impl-note #6','impl-note #9','impl-note #10','impl-note #11' | Select-Object Line
# each spike carries a Fallback; the deferral + cutover are stated
Select-String -Path $v -Pattern '^\*\*Fallback:\*\*','deferred to suite cutover','^## Cutover checklist$' | Select-Object Line,Pattern
```
Expected: `True`; all five impl-note references present (one per spike); a `**Fallback:**` line under each spike that has one (Spikes 1–3 mandatory; 4–5 state their fallback inline); the cutover-deferral statement and the `## Cutover checklist` heading present.

- [ ] **Step 4: Confirm no in-session execution was attempted**

This is a documentation deliverable — there is nothing to run in-session. Confirm the doc's own header states the deferral ("authored, NOT yet executed") so a future reader does not mistake it for a passing test record:
```powershell
Get-Content "I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md" -TotalCount 1
```
Expected: the first heading line, followed (in the file) by the bold `Status: authored, NOT yet executed.` line.

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md
git -C I:\Dev\claude-toolkit commit -m "docs(validation): author or-superpowers-at-scale behavioral spikes (deferred to cutover)"
```
Expected: one new file committed on `or-superpowers-at-scale`.

---

## Task 4: Plan-2 integration self-review

A consolidation gate confirming the phase agents are finalized and intact, the skill skeleton is valid and scoped to its layer, the spikes doc is complete, the plugin still validates, and no manifest/user-facing churn leaked in. Verification only — no new component files; a commit is made only if a fix is required.

**Files:** none created.

- [ ] **Step 1: Both phase agents live in `agents/`, drafts gone, depth-1 intact**

```powershell
$ag = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
Test-Path "$ag\or-brainstormer.md"; Test-Path "$ag\or-plan-writer.md"                 # expect True, True
Test-Path "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-brainstormer.md"          # expect False
Test-Path "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-plan-writer.md"           # expect False
Select-String -Path "$ag\or-brainstormer.md","$ag\or-plan-writer.md" -Pattern '^tools:.*\bAgent\b'   # expect NO match
```
Expected: both agents present in `agents/`; both drafts gone; neither agent grants `Agent` (depth-1).

- [ ] **Step 2: The remaining five drafts are untouched (Plan 3's inputs)**

```powershell
Get-ChildItem "I:\Dev\claude-toolkit\docs\superpowers\drafts\" -Name
```
Expected: exactly the five Plan-3 drafts remain — `or-supervisor.md`, `or-implementer.md`, `or-spec-reviewer.md`, `or-code-quality-reviewer.md`, `or-final-reviewer.md`. (The two phase-agent drafts were moved in Task 1; no other draft was touched.)

- [ ] **Step 3: Skill skeleton is valid and scoped to its layer**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
Get-Content $s -TotalCount 2 | Select-Object -Last 1                                  # name: or-superpowers-at-scale
Select-String -Path $s -Pattern '^## When to Use$','^## Architecture$','^## Integration with Other Skills$' | Select-Object Line
Select-String -Path $s -Pattern '^## Manager Context Discipline$','^### SPAWN protocol','TBD','Plan 4'   # expect NO match
```
Expected: `name:` line correct; the three skeleton sections present; **no** operating-discipline section, **no** placeholder, **no** authoring-plan reference (the deferral is documented in *this plan*, not the shipped skill).

- [ ] **Step 4: Spikes doc is complete and self-labels as deferred**

```powershell
$v = "I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md"
Select-String -Path $v -Pattern 'impl-note #3','impl-note #6','impl-note #9','impl-note #10','impl-note #11','^## Cutover checklist$','authored, NOT yet executed' | Select-Object Line
```
Expected: all five impl-notes, the cutover checklist, and the deferral self-label all present.

- [ ] **Step 5: Plugin validates; no manifest/version/README churn**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
git -C I:\Dev\claude-toolkit diff fba913b..HEAD --name-only -- plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
```
Expected: validation passes (or `claude` skip recorded). The `git diff` for the manifests + README returns **empty** — Plan 2 (like Plan 1) touched no version/manifest/README file (release deferred to Plan 4). If `claude` is unavailable, record the skip and rely on the structural greps in Steps 1–4.

- [ ] **Step 6: Commit graph is three clean component commits**

```powershell
git -C I:\Dev\claude-toolkit log --oneline cd76792..HEAD
```
Expected: three commits since the Plan-1 baseline `cd76792` — `feat(agents): finalize or-brainstormer and or-plan-writer phase agents`, `feat(skills): add or-superpowers-at-scale orchestrator skill skeleton`, `docs(validation): author or-superpowers-at-scale behavioral spikes (deferred to cutover)` — plus (after this plan is saved) the Plan-2 doc commit.

- [ ] **Step 7: Spec-coverage check for Plan 2**

Confirm every Plan-2 design requirement has a corresponding artifact:
- `or-brainstormer` finalized into `agents/`, frontmatter + body intact, no `Agent` tool ✓ (design §"Agent Inventory", §"Phase agent bodies")
- `or-plan-writer` finalized into `agents/`, frontmatter + body intact, no `Agent` tool ✓
- Orchestrator skill skeleton authored — pinned description, when-to-use, topology, phase flow, integration ✓ (design §"`or-superpowers-at-scale` skill frontmatter", §"Architecture", §"Integration", §"When to Use")
- Operating-discipline body **correctly deferred** to Plan 4 (impl-note #8 split) ✓
- Behavioral spikes #3/#6/#9/#10/#11 authored as deferred-execution procedures with fallbacks ✓ (design impl-notes #3/#6/#9/#10/#11, §"Cutover & end-state validation")
- Release/version/README/command: intentionally **not** touched in Plan 2 (deferred to Plan 4 — see "Release deferral") ✓

- [ ] **Step 8: Checkpoint — Plan 2 complete**

All checks green (or `claude plugin validate` explicitly noted as skipped). If any step required an edit, commit it:
```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "fix(plan-2): integration self-review corrections"
```
Otherwise, no commit is needed — Tasks 1–3 already committed their work. The orchestrator's user-facing Phase-1/2 tier and its self-describing entry skill exist on the branch, and every load-bearing behavioral risk is captured for cutover. Ready for Plan 3 (supervisor + workers + the two `or-*` research agents + the skill's `assets/*` templates), which finalizes the remaining five drafts using the exact `git mv` pattern validated here and authors the two research bodies + spawn/handover templates the skeleton references.

---

## Self-Review (run after implementation, before declaring Plan 2 done)

**1. Spec coverage:** Task 4 Step 7 enumerates the Plan-2 component requirements against the design (two phase agents, skill skeleton, five spikes), plus the deliberate Plan-4 deferrals (operating-discipline body, command wrapper, release). No gaps.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to above". The one deliberately-not-inlined content is the two phase-agent bodies — relocated by `git mv` (a byte-faithful move of reviewed, committed content) and verified by frontmatter/anchor greps + rename detection + line-count equality, because re-inlining ~165 lines per agent would duplicate the thing being finalized. Every newly-authored file (the skill skeleton, the spikes doc) is shown complete. The skeleton's missing operating-discipline sections are an **additive deferral documented in this plan**, not in-file stubs — and Task 2 Step 5 + Task 4 Step 3 actively assert the file contains no `TBD`/`Plan 4`/forward-stub markers.

**3. Type/name consistency:** Agent names (`or-brainstormer`, `or-plan-writer`) and their completion tokens (`BRAINSTORM_COMPLETE`, `PLAN_COMPLETE`) match the drafts, the spec, and the skeleton's phase-flow. The skill name `or-superpowers-at-scale` is identical in the file path, the frontmatter, and every reference. The pinned description matches design §"`or-superpowers-at-scale` skill frontmatter" verbatim. The pre-seeded skill names in the skeleton's Integration list (`superpowers:brainstorming` / `writing-plans` / `subagent-driven-development` / `test-driven-development` / `using-git-worktrees` / `finishing-a-development-branch`) match the spec's Integration section and the agents' `skills:` frontmatter. The five spikes' impl-note numbers (#3/#6/#9/#10/#11) match the design's Implementation Notes.

## Plan suite status

This is **Plan 2 of 4**. Remaining: Plan 3 (supervisor + workers + the two `or-*` research agents + the skill's `assets/*` templates — finalizing the five remaining drafts via the `git mv` pattern validated here, authoring the two research bodies from the design's "Research agent body" template, and authoring the spawn-context / handover / protocol-reference assets), Plan 4 (manager-discipline `SKILL.md` body appended to the skeleton + the optional `commands/` wrapper + the suite **release step**: 1.1.1 → 1.2.0 bump, marketplace sync, README, push on approval). The `last-plan-doc` pointer and a suite index are set once all four plans are written (design handover) — **deferred**. **Do not** proceed to execution from this file alone — execution is driven for the whole suite via `/implement-from-plan` after the suite is complete and reviewed.
