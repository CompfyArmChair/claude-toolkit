# `or-superpowers-at-scale` — Plan 3: Execution-Phase Agents + Research Teammates + Skill Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Skill/agent authoring steps are also governed by **superpowers:writing-skills** — load it before authoring any agent or asset file.

**Goal:** Finalize the five remaining Phase-3 teammate agents (`or-supervisor`, `or-implementer`, `or-spec-reviewer`, `or-code-quality-reviewer`, `or-final-reviewer`) from their reviewed drafts into the plugin's `agents/` directory; author the two deposit-aware research teammates (`or-dependency-researcher`, `or-community-researcher`) from the design's "Research agent body" template; and author the orchestrator skill's eleven `assets/*` templates (spawn-context, handover, and protocol-reference files) — so the implementation tier and the skill's referenced assets exist on the branch, leaving only the manager-discipline `SKILL.md` body and the release for Plan 4.

**Architecture:** Five reviewed drafts moved verbatim (`git mv`) from `docs/superpowers/drafts/` to `plugins/claude-toolkit/agents/` (single source of truth — the draft is the final body, with no edit during the move). All five — `or-supervisor` included — reference the orchestrator's protocols and handover templates by invoking `Skill('claude-toolkit:or-superpowers-at-scale')` (the install-agnostic form their drafts already carry, per the pre-suite skill-invocation rework), so each is a pure relocation. Two new research agent bodies authored fresh from the design template. Eleven new asset files authored under `skills/or-superpowers-at-scale/assets/`: five tiny spawn-context templates and two phase handover templates (NEW, content pinned in the design); one iteration handover template (PRESERVED from the legacy skill with `or-*` naming normalization); one manager handover template (ADAPTED — adds two phase fields); and two protocol references — `spawn-protocol.md` (ADAPTED — preserves SPAWN, adds SPAWN_RESEARCH) and `preflight-brief.md` (ADAPTED — adds mode detection + worktree prompting).

**Tech Stack:** Claude Code plugin components — Markdown files with YAML frontmatter (agents) and plain Markdown templates (assets), inside the `claude-toolkit` plugin repo (`I:\Dev\claude-toolkit`, real git). No compiled code. Verification is by structural assertion (frontmatter/content greps, rename detection, line-count equality) plus `claude plugin validate`; all behavioral validation is deferred to suite cutover (the plugin is not installed in the authoring session). Per-task `git commit` is the rollback boundary.

---

## Scope of this plan (Plan 3 of 4)

This is the **implementation-tier + assets** plan of the `or-superpowers-at-scale` suite (design: `docs/superpowers/specs/2026-05-24-or-superpowers-at-scale-design.md`, authoritative; see esp. the **Plugin Packaging**, **Agent Inventory** + §"Skill loading mechanism" + §"Research agent body", **Asset Inventory** + §"Spawn-context templates" + §"Phase handover templates", **Protocols**, and impl-notes **#1/#7/#8**). It builds the Phase-3 execution tier (supervisor + workers), the two `or-*` research teammates, and every `assets/*` file the Plan-2 skill skeleton references. It is the heaviest plan in the suite (18 deliverable files). It reuses the exact `git mv` finalization + structural-verification pattern Plan 2 validated, and the from-template authoring + pinned-content pattern Plan 1 validated.

In scope:
- **Finalize four worker agents** (verbatim `git mv` from reviewed drafts): `or-implementer`, `or-spec-reviewer`, `or-code-quality-reviewer`, `or-final-reviewer`.
- **Finalize `or-supervisor`** (verbatim `git mv` — its draft already invokes the orchestrator skill for protocol/template refs; see Task 2).
- **Author two research teammates** (NEW, from the design's "Research agent body" template): `or-dependency-researcher`, `or-community-researcher`.
- **Author eleven `assets/*` files** under `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/`:
  - Spawn-context (5, NEW): `brainstormer-spawn-context.md`, `plan-writer-spawn-context.md`, `supervisor-spawn-context.md`, `implementer-spawn-context.md`, `reviewer-spawn-context.md`.
  - Handover templates (4): `brainstormer-handover-template.md` (NEW), `plan-writer-handover-template.md` (NEW), `iteration-handover-template.md` (PRESERVED), `manager-handover-template.md` (ADAPTED).
  - Protocol references (2, ADAPTED): `spawn-protocol.md`, `preflight-brief.md`.

Out of scope (Plan 4 / cutover):
- The orchestrator skill's **operating-discipline body** appended to the Plan-2 skeleton — Mode Detection, the manager-side SPAWN / **SHUTDOWN** / SPAWN_RESEARCH broker protocols, the Handover Ladder, Manager Context Discipline, Red Flags (Plan 4). **SHUTDOWN's full manager-side handshake lives there, not in this plan's `spawn-protocol.md`** (see "spawn-protocol.md scope" below).
- The optional `commands/or-superpowers-at-scale.md` thin wrapper (Plan 4).
- The version bump + marketplace sync + README + push (Plan 4 release step — see "Release deferral").
- **Execution** of any agent/asset behaviorally (suite cutover, post-Plan-4, against the installed plugin — see Plan 2's behavioral-spikes doc).

**Suite-order assumption:** the suite executes Plan 1 → 2 → 3 → 4 in order via `/implement-from-plan`. At Plan 3 start, Plan 2 has already finalized `or-brainstormer` + `or-plan-writer` into `agents/` and created `skills/or-superpowers-at-scale/SKILL.md`. Plan 3's `agents/` RED checks assert only the *five* new destinations are absent; its asset RED checks assert the `assets/` files are absent (the parent skill dir already exists from Plan 2). Plan 3 does not modify any Plan-1 or Plan-2 artifact.

## Git workflow (READ FIRST)

`I:\Dev\claude-toolkit` **is a real git repository** (verified). All work happens on the existing feature branch **`or-superpowers-at-scale`** with **one commit per task** (design §"Git workflow"). The real-git review/rollback loop is the SDD rollback boundary.

- The working directory is `C:\Users\marti\.claude` (a different drive from the repo). **Every git command targets the repo explicitly via `git -C I:\Dev\claude-toolkit …`** — do not rely on the ambient cwd, and do not `cd` (it can trigger a permission prompt).
- Use **`git mv`** for the five agent finalizations — it moves the file in one tracked operation, preserving history. All five are byte-identical moves (no body edit). Do **not** hand-copy any body.
- Do **not** `git push` in this plan. The branch stays local until the whole suite is reviewed and the user approves the release (design handover: push only when asked; the push *is* the suite release).

## Release deferral (carried from Plans 1–2 — user-confirmed 2026-05-30)

The whole orchestrator ships as a **single** minor increment `1.1.1 → 1.2.0`, finalized in a dedicated **Plan 4** release step on user approval. **Plan 3 makes no version / manifest / README change** — nothing here is user-visible until the release push. New components are committed to the feature branch only.

## Verification approach (why every behavioral check is deferred)

The `claude-toolkit` marketplace is **not installed in the authoring session** (design handover; confirmed in Plans 1–2). So the finalized agents are not live `claude-toolkit:or-*` subagent types here, and the skill's assets are not loadable by a teammate. **Plan 3's hard gates are therefore structural** — `claude plugin validate` + frontmatter/content greps + rename detection + line-count equality, run against the repo files. **Every behavioral check is deferred** to suite cutover (after the Plan 4 release), run against the *installed* plugin (`claude plugin install claude-toolkit`) — that deferred set is the five spikes authored in Plan 2 plus Plan 1's deferred wrapper check (see the behavioral-spikes doc's "Cutover checklist" and design §"Cutover & end-state validation"). In particular, the in-body `Skill('claude-toolkit:…')` load mechanism (impl-note #3) — including whether a teammate that invokes `Skill('claude-toolkit:or-superpowers-at-scale')` can reach the orchestrator's bundled `assets/*` content — is confirmed there, uniformly, for **all** agents, including the two research bodies and the supervisor authored here.

## Source-of-truth references

| Artifact being built | Source content | Notes |
|---|---|---|
| `agents/or-implementer.md` | `docs/superpowers/drafts/or-implementer.md` | Verbatim **move** (`git mv`). No body edit. |
| `agents/or-spec-reviewer.md` | `docs/superpowers/drafts/or-spec-reviewer.md` | Verbatim **move**. |
| `agents/or-code-quality-reviewer.md` | `docs/superpowers/drafts/or-code-quality-reviewer.md` | Verbatim **move**. |
| `agents/or-final-reviewer.md` | `docs/superpowers/drafts/or-final-reviewer.md` | Verbatim **move**. |
| `agents/or-supervisor.md` | `docs/superpowers/drafts/or-supervisor.md` | Verbatim **move** (`git mv`). No body edit — the draft already invokes the skill for its protocol/template refs. |
| `agents/or-dependency-researcher.md` | Design §"Research agent body" template + Agent Inventory tool grants | NEW — inlined in full in Task 3. |
| `agents/or-community-researcher.md` | Design §"Research agent body" template + Agent Inventory tool grants | NEW — inlined in full in Task 3. |
| `assets/{brainstormer,plan-writer,supervisor,implementer,reviewer}-spawn-context.md` | Design §"Spawn-context templates" | NEW — pinned content inlined in Task 4. |
| `assets/{brainstormer,plan-writer}-handover-template.md` | Design §"Phase handover templates" | NEW — pinned content inlined in Task 5. |
| `assets/iteration-handover-template.md` | Legacy `subagent-driven-development-at-scale/assets/iteration-handover-template.md` | PRESERVED + `or-*` naming normalization — inlined in Task 5. |
| `assets/manager-handover-template.md` | Legacy `…/assets/manager-handover-template.md` | ADAPTED (adds two phase fields + skill-ref normalization) — inlined in Task 5. |
| `assets/spawn-protocol.md` | Legacy `…/assets/spawn-protocol.md` + design §"SPAWN_RESEARCH protocol" | ADAPTED — inlined in Task 6. |
| `assets/preflight-brief.md` | Legacy `…/assets/preflight-brief.md` + design §"Mode Detection" + §"Phase flow" Phase 0 | ADAPTED — inlined in Task 6. |

All plugin paths are relative to the plugin root `I:\Dev\claude-toolkit\plugins\claude-toolkit\`. The five draft source files are the **reviewed, authoritative** agent bodies — they already encode every spec decision (no `Agent` tool anywhere; `Skill` only where a skill is loaded in-body — including the in-body `Skill('claude-toolkit:or-superpowers-at-scale')` invocation each phase/supervisor agent uses for orchestrator protocol/template refs; read-only reviewers keep `SendMessage`; `or-implementer` carries no `model:`). **None of the five bodies are edited during the moves** (Tasks 1–2).

### Why the five reviewed bodies are moved, not re-inlined

The body is reviewed content that already exists verbatim in a committed repo file. Re-typing it into this plan would invite transcription drift and create a second copy of the very thing being finalized. `git mv` relocates the exact bytes and preserves history; verification is by frontmatter/anchor greps + rename detection + line-count equality. (Same deliberate exception Plans 1–2 made for verbatim moves.) This applies to all five finalized here — the four workers **and** `or-supervisor`.

### Agents invoke the skill for protocol/template refs (no body edits here)

All five drafts — like the two phase agents Plan 2 finalized — reach the orchestrator's SPAWN protocol and handover templates by invoking `Skill('claude-toolkit:or-superpowers-at-scale')` (the in-body form of the `/` command), never by an `assets/...` path or an absolute `~/.claude/...` path. This is install-agnostic and is the load path the whole design rests on for teammates (design §"Skill loading mechanism"). The supervisor draft once carried stale absolute `~/.claude/skills/or-superpowers-at-scale/assets/...` paths (written 2026-05-25, before the 2026-05-30 re-homing); the **pre-suite skill-invocation rework** corrected those — and the equivalent refs in `or-brainstormer`/`or-plan-writer` — to the skill invocation, at the drafts, before this suite runs. Consequently **every** finalization in this plan — `or-supervisor` included — is a pure byte-faithful `git mv` with no body edit. Verification asserts each phase/supervisor agent carries the `Skill('claude-toolkit:or-superpowers-at-scale')` invocation and **zero** `~/.claude` or `assets/*.md` path references. (The four worker drafts — `or-implementer` + three reviewers — reference no orchestrator assets at all.)

### `spawn-protocol.md` scope (SPAWN + SPAWN_RESEARCH; SHUTDOWN deferred to Plan 4)

The design's Asset Inventory pins `spawn-protocol.md` as the "Canonical **SPAWN + SPAWN_RESEARCH** protocol reference" (PRESERVE SPAWN; ADD SPAWN_RESEARCH). The **SHUTDOWN** protocol (design §"SHUTDOWN protocol [NEW]") is a manager-owned teardown handshake; its canonical full text belongs in the Plan-4 manager-discipline `SKILL.md` alongside the other manager broker protocols (handover plan: Plan 4 SKILL.md = "SPAWN/SHUTDOWN/SPAWN_RESEARCH protocols"). The `or-supervisor` body already carries the supervisor-side SHUTDOWN summary (the `SHUTDOWN / NAME: <worker>` request shape). So this plan **deliberately omits SHUTDOWN from `spawn-protocol.md`** to honor the Inventory's scope and avoid Plan-3/Plan-4 duplication. This is intentional, not an omission to fix.

---

## Task 1: Finalize the four worker agents (`or-implementer` + the three reviewers)

Move the four reviewed worker drafts into the plugin's `agents/` directory via `git mv` (single source of truth — the draft *is* the final body). They are finalized together: identical mechanism, a cohesive "Phase-3 worker tier" unit, one commit. None reference assets, so none is edited.

**Files:**
- Move: `docs/superpowers/drafts/or-implementer.md` → `plugins/claude-toolkit/agents/or-implementer.md`
- Move: `docs/superpowers/drafts/or-spec-reviewer.md` → `plugins/claude-toolkit/agents/or-spec-reviewer.md`
- Move: `docs/superpowers/drafts/or-code-quality-reviewer.md` → `plugins/claude-toolkit/agents/or-code-quality-reviewer.md`
- Move: `docs/superpowers/drafts/or-final-reviewer.md` → `plugins/claude-toolkit/agents/or-final-reviewer.md`

- [ ] **Step 1: Verify the four source drafts exist and the four destinations do not (RED)**

```powershell
$d = "I:\Dev\claude-toolkit\docs\superpowers\drafts"
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
foreach ($n in 'or-implementer','or-spec-reviewer','or-code-quality-reviewer','or-final-reviewer') {
  "{0}: draft={1} dest={2}" -f $n, (Test-Path "$d\$n.md"), (Test-Path "$a\$n.md")
}
```
Expected: each line shows `draft=True dest=False` (confirms we are finalizing, not overwriting an existing agent).

- [ ] **Step 2: Capture the source line counts (integrity baseline)**

```powershell
$d = "I:\Dev\claude-toolkit\docs\superpowers\drafts"
foreach ($n in 'or-implementer','or-spec-reviewer','or-code-quality-reviewer','or-final-reviewer') {
  "{0}: {1}" -f $n, (Get-Content "$d\$n.md" | Measure-Object -Line).Lines
}
```
Record all four (expected ≈ `or-implementer` 23, `or-spec-reviewer` 21, `or-code-quality-reviewer` 23, `or-final-reviewer` 23). After the move (Step 4) the destination line counts must match exactly — proving the moves were byte-faithful.

- [ ] **Step 3: Move all four drafts with `git mv`**

```powershell
git -C I:\Dev\claude-toolkit mv docs/superpowers/drafts/or-implementer.md           plugins/claude-toolkit/agents/or-implementer.md
git -C I:\Dev\claude-toolkit mv docs/superpowers/drafts/or-spec-reviewer.md          plugins/claude-toolkit/agents/or-spec-reviewer.md
git -C I:\Dev\claude-toolkit mv docs/superpowers/drafts/or-code-quality-reviewer.md  plugins/claude-toolkit/agents/or-code-quality-reviewer.md
git -C I:\Dev\claude-toolkit mv docs/superpowers/drafts/or-final-reviewer.md         plugins/claude-toolkit/agents/or-final-reviewer.md
```
Expected: no output (success). The four files are now staged as renames.

- [ ] **Step 4: Verify byte-faithful relocation (GREEN — integrity)**

```powershell
$d = "I:\Dev\claude-toolkit\docs\superpowers\drafts"
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
foreach ($n in 'or-implementer','or-spec-reviewer','or-code-quality-reviewer','or-final-reviewer') {
  "{0}: dest={1} src={2} lines={3}" -f $n, (Test-Path "$a\$n.md"), (Test-Path "$d\$n.md"), (Get-Content "$a\$n.md" | Measure-Object -Line).Lines
}
# git sees four pure renames (R100 = 100% similarity, no content change)
git -C I:\Dev\claude-toolkit diff --cached --find-renames --name-status
```
Expected: each line shows `dest=True src=False` with `lines` equal to Step 2; `git diff --cached` shows four `R100` rename entries (`docs/superpowers/drafts/… -> plugins/claude-toolkit/agents/…`) and **no** content modification.

- [ ] **Step 5: Verify load-bearing frontmatter and body anchors survived (GREEN — content)**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
# or-implementer: name, skills, in-body TDD call, STATUS protocol; NO model field; NO Agent tool
Select-String -Path "$a\or-implementer.md" -Pattern '^name: or-implementer$','^skills: \[superpowers:test-driven-development\]$','Skill\("superpowers:test-driven-development"\)','DONE / DONE_WITH_CONCERNS / BLOCKED / NEEDS_CONTEXT' | Select-Object Line
Select-String -Path "$a\or-implementer.md" -Pattern '^model:'                 # expect NO match (supervisor picks per SPAWN)
# three reviewers: name, model, read-only disposition, SendMessage present; NO Skill tool; NO Agent tool
Select-String -Path "$a\or-spec-reviewer.md"         -Pattern '^name: or-spec-reviewer$','^model: sonnet$',"You have no ``Edit``/``Write`` tools" | Select-Object Line
Select-String -Path "$a\or-code-quality-reviewer.md" -Pattern '^name: or-code-quality-reviewer$','^model: opus$','design quality, correctness, and' | Select-Object Line
Select-String -Path "$a\or-final-reviewer.md"        -Pattern '^name: or-final-reviewer$','^model: opus$','ONCE per branch' | Select-Object Line
# depth-1 across all four: NO Agent in any tools line
Select-String -Path "$a\or-implementer.md","$a\or-spec-reviewer.md","$a\or-code-quality-reviewer.md","$a\or-final-reviewer.md" -Pattern '^tools:.*\bAgent\b'   # expect NO match
# reviewers carry SendMessage but NOT Skill
Select-String -Path "$a\or-spec-reviewer.md","$a\or-code-quality-reviewer.md","$a\or-final-reviewer.md" -Pattern '^tools: Read, Grep, Glob, Bash, SendMessage$' | Select-Object Path
```
Expected: every `name`/`model`/`skills` assertion matches; `or-implementer` has **no** `model:` line and its in-body `Skill("superpowers:test-driven-development")` call is present; each reviewer shows its model, read-only disposition text, and the exact `tools: Read, Grep, Glob, Bash, SendMessage` line; **no** `Agent` in any `tools:` line.

- [ ] **Step 6: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes (valid `plugin.json`; the four new agent files have valid frontmatter). If the `claude` CLI is unavailable in this environment, record that explicitly and rely on Steps 4–5 as the structural gate — note the skip rather than claiming a pass.

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "feat(agents): finalize or-implementer and the three reviewer workers"
```
Expected: one commit on `or-superpowers-at-scale` containing four renames (drafts → `agents/`). `git -C I:\Dev\claude-toolkit show --stat HEAD` should list all four as renames with zero net line change.

---

## Task 2: Finalize `or-supervisor` (verbatim move)

Move the reviewed `or-supervisor` draft into `agents/` via `git mv` — a pure byte-faithful relocation. Its draft already invokes `Skill('claude-toolkit:or-superpowers-at-scale')` for the SPAWN protocol and the iteration-handover template (the pre-suite skill-invocation rework applied this across every draft before the suite runs), so no body edit is needed. This is the suite's orchestration-tier agent, so it gets its own task and commit — separate from the four workers in Task 1; like them, it is an R100 rename.

**Files:**
- Move: `docs/superpowers/drafts/or-supervisor.md` → `plugins/claude-toolkit/agents/or-supervisor.md`

- [ ] **Step 1: Verify the source exists, the destination does not, capture the line-count baseline, and confirm the draft is in its post-rework state (RED)**

```powershell
$src = "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-supervisor.md"
$dst = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-supervisor.md"
Test-Path $src                                                                        # expect True
Test-Path $dst                                                                        # expect False
(Get-Content $src | Measure-Object -Line).Lines                                       # record N (the move must preserve it exactly)
# confirm the draft already invokes the orchestrator skill (skill-invocation rework) — expect exactly two
Select-String -Path $src -Pattern "Skill\('claude-toolkit:or-superpowers-at-scale'\)" | Select-Object LineNumber
# and carries NO stale asset path of either form — expect NO match
Select-String -Path $src -Pattern '~/\.claude/skills/','assets/.*\.md'
```
Expected: `True`, then `False`; record the line count (before==after is the integrity gate — robust regardless of the absolute number, which `Measure-Object` under-reports on these drafts). **Exactly two** `Skill('claude-toolkit:or-superpowers-at-scale')` invocations (the SPAWN-protocol reference + the iteration-handover-template reference); **zero** `~/.claude/skills/` and **zero** `assets/*.md` path matches. This confirms the source is the already-corrected draft, so the move is a pure relocation.

- [ ] **Step 2: Move `or-supervisor.md` with `git mv`**

```powershell
git -C I:\Dev\claude-toolkit mv docs/superpowers/drafts/or-supervisor.md plugins/claude-toolkit/agents/or-supervisor.md
```
Expected: no output (success). The file is staged as a rename.

- [ ] **Step 3: Verify the byte-faithful move (GREEN)**

```powershell
$src = "I:\Dev\claude-toolkit\docs\superpowers\drafts\or-supervisor.md"
$dst = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-supervisor.md"
Test-Path $dst                                                                        # expect True
Test-Path $src                                                                        # expect False
(Get-Content $dst | Measure-Object -Line).Lines                                       # expect == Step 1's recorded N
# git sees a pure rename (R100 = 100% similarity, no content change) — like the four workers in Task 1
git -C I:\Dev\claude-toolkit diff --cached --find-renames --name-status
# the skill-invocation refs survived the move (expect two); NO stale paths of either form (expect none)
Select-String -Path $dst -Pattern "Skill\('claude-toolkit:or-superpowers-at-scale'\)" | Select-Object Line
Select-String -Path $dst -Pattern '~/\.claude/skills/','assets/.*\.md'
```
Expected: destination `True`, source `False`; line count equals Step 1's recorded value; `git diff --cached` shows a single `R100` rename (`docs/superpowers/drafts/or-supervisor.md -> plugins/claude-toolkit/agents/or-supervisor.md`) with **no** content modification; **two** `Skill('claude-toolkit:or-superpowers-at-scale')` invocations in the destination; **zero** `~/.claude/skills/` and **zero** `assets/*.md` path matches. (Because the move is byte-faithful these necessarily hold — asserting them is the explicit supervisor-ref gate.)

- [ ] **Step 4: Verify load-bearing frontmatter and body anchors survived (GREEN — content)**

```powershell
$dst = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-supervisor.md"
# frontmatter: name, model, skills; tools includes Skill + SendMessage + Task*; NO Agent
Select-String -Path $dst -Pattern '^name: or-supervisor$','^model: opus$','^skills: \[superpowers:subagent-driven-development\]$','^tools:.*\bSkill\b.*\bSendMessage\b.*\bTaskCreate\b' | Select-Object Line
Select-String -Path $dst -Pattern '^tools:.*\bAgent\b'                                # expect NO match (depth-1)
# body anchors: STEP 0 in-body call, the one-adaptation-one-override, Closed loopholes, depth-1, worker naming, ITERATION token
Select-String -Path $dst -Pattern 'Skill\("superpowers:subagent-driven-development"\)','### One adaptation, one override','### Closed loopholes','^## Depth-1 Constraint$','^## Worker Naming Convention$','ITERATION <N> — STOPPED_FOR_HANDOVER' | Select-Object Line
```
Expected: every frontmatter assertion matches; **no** `Agent` in `tools:`; each body anchor present (the in-body `Skill(...)` call, the adaptation/override and Closed-loopholes sections, the depth-1 and worker-naming headings, and the iteration handover token).

- [ ] **Step 5: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes. If `claude` is unavailable, record the skip and rely on Steps 3–4.

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "feat(agents): finalize or-supervisor"
```
Expected: one commit containing the supervisor as a pure rename (R100). `git -C I:\Dev\claude-toolkit show --stat HEAD` lists it as a rename with zero net line change; no body line differs.

---

## Task 3: Author the two research teammates (`or-dependency-researcher`, `or-community-researcher`)

These two have **no draft** — author them fresh from the design's "Research agent body" template (design §"Research agent body"; tool grants from §"Agent Inventory" rows 8–9). They are a cohesive "deposit-aware research teammate" unit (one differs from the other only in methodology skill and the absence of the Context7 tools), so they land in one commit. Both pre-seed their methodology skill + the `research-deposit` skill via in-body, **plugin-qualified** `Skill('claude-toolkit:…')` calls (the load-bearing path for teammates; the `skills:` frontmatter is inert for teammates — design §"Skill loading mechanism"). Neither has `Agent` (leaf teammate) or `AskUserQuestion`.

**Files:**
- Create: `I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-dependency-researcher.md`
- Create: `I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-community-researcher.md`

- [ ] **Step 1: Load the authoring discipline**

Invoke `Skill('superpowers:writing-skills')` and skim it (the agent-authoring guidance applies: frontmatter is load-bearing; the body is the agent's instruction set). Load-bearing for this task: `Skill` must be in `tools` for the in-body calls to work; `Write` + `SendMessage` are required for deposit; **no** `Agent`; the in-body skill names are plugin-qualified (`claude-toolkit:`) per design §"Namespace & naming" and Plan 1's confirmed split (qualified in-body, bare in `skills:` frontmatter).

- [ ] **Step 2: Verify neither agent exists yet (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-dependency-researcher.md"   # expect False
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-community-researcher.md"     # expect False
```
Expected: both `False`.

- [ ] **Step 3: Create `or-dependency-researcher.md` with this exact content**

````markdown
---
name: or-dependency-researcher
description: Phase-3 dependency/library research teammate for the or-superpowers-at-scale orchestrator. The manager spawns this deposit-aware agent as a background teammate via the SPAWN_RESEARCH broker; it researches a library/SDK/API question, writes its full findings to the DEPOSIT path, and signals the manager with a single RESEARCH_DONE token. Not for standalone use.
tools: Read, Grep, Glob, WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs, Write, Skill, SendMessage
model: opus
skills: [dependency-research-methodology, research-deposit]
---

# or-dependency-researcher — Deposit-Aware Library Research Teammate (`or-superpowers-at-scale`)

You are an `or-dependency-researcher` deposit-aware research agent in the orchestrator topology. Your name, team, branch, and a `DEPOSIT: <path>` parameter arrive in your spawn context / prompt. You have no `Agent` tool — you are a leaf teammate; you never spawn.

## Methodology

Use `Skill('claude-toolkit:dependency-research-methodology')` to load the research-and-citation approach, then execute it for the research question in your prompt.

## Deposit

Use `Skill('claude-toolkit:research-deposit')` to deliver your findings and signal completion. You will receive a `DEPOSIT: <path>` parameter — write your **full findings** there with the `Write` tool (the complete report, not a summary), then SendMessage the manager exactly `RESEARCH_DONE: <path>` and nothing else. Never echo findings into your message. If you cannot complete, write what you gathered to the path and SendMessage `RESEARCH_BLOCKED: <path> — <one-line reason>` instead.

## Tools

You have `Write` (deposit requires it) and `SendMessage` (to signal the manager). You have no `Agent` tool — you are a leaf teammate.

> Note: `skills:` frontmatter is **inert for teammates** (which you are) — a teammate loads skills like a normal session, not from agent frontmatter. The two in-body `Skill(...)` calls above are the load-bearing path that loads the methodology and deposit skills; never skip them as "already pre-seeded."
````

- [ ] **Step 4: Create `or-community-researcher.md` with this exact content**

(Identical structure; community methodology skill, and **no** Context7 tools — design §"Agent Inventory" row 9.)

````markdown
---
name: or-community-researcher
description: Phase-3 community/real-world research teammate for the or-superpowers-at-scale orchestrator. The manager spawns this deposit-aware agent as a background teammate via the SPAWN_RESEARCH broker; it researches how the community solves a problem, writes its full findings to the DEPOSIT path, and signals the manager with a single RESEARCH_DONE token. Not for standalone use.
tools: Read, Grep, Glob, WebFetch, WebSearch, Write, Skill, SendMessage
model: opus
skills: [community-research-methodology, research-deposit]
---

# or-community-researcher — Deposit-Aware Community Research Teammate (`or-superpowers-at-scale`)

You are an `or-community-researcher` deposit-aware research agent in the orchestrator topology. Your name, team, branch, and a `DEPOSIT: <path>` parameter arrive in your spawn context / prompt. You have no `Agent` tool — you are a leaf teammate; you never spawn.

## Methodology

Use `Skill('claude-toolkit:community-research-methodology')` to load the research-and-citation approach, then execute it for the research question in your prompt.

## Deposit

Use `Skill('claude-toolkit:research-deposit')` to deliver your findings and signal completion. You will receive a `DEPOSIT: <path>` parameter — write your **full findings** there with the `Write` tool (the complete report, not a summary), then SendMessage the manager exactly `RESEARCH_DONE: <path>` and nothing else. Never echo findings into your message. If you cannot complete, write what you gathered to the path and SendMessage `RESEARCH_BLOCKED: <path> — <one-line reason>` instead.

## Tools

You have `Write` (deposit requires it) and `SendMessage` (to signal the manager). You have no `Agent` tool — you are a leaf teammate.

> Note: `skills:` frontmatter is **inert for teammates** (which you are) — a teammate loads skills like a normal session, not from agent frontmatter. The two in-body `Skill(...)` calls above are the load-bearing path that loads the methodology and deposit skills; never skip them as "already pre-seeded."
````

- [ ] **Step 5: Verify both bodies carry the five template elements + correct tool grants (GREEN)**

```powershell
$dep = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-dependency-researcher.md"
$com = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-community-researcher.md"
# frontmatter: name, model opus, skills pair; Write + Skill + SendMessage in tools; NO Agent, NO AskUserQuestion
Select-String -Path $dep -Pattern '^name: or-dependency-researcher$','^model: opus$','^skills: \[dependency-research-methodology, research-deposit\]$','^tools:.*\bWrite\b.*\bSkill\b.*\bSendMessage\b' | Select-Object Line
Select-String -Path $com -Pattern '^name: or-community-researcher$','^model: opus$','^skills: \[community-research-methodology, research-deposit\]$','^tools:.*\bWrite\b.*\bSkill\b.*\bSendMessage\b' | Select-Object Line
Select-String -Path $dep,$com -Pattern '^tools:.*\b(Agent|AskUserQuestion)\b'           # expect NO match
# Context7 only on the dependency researcher
Select-String -Path $dep -Pattern '^tools:.*mcp__context7__'                            # expect match
Select-String -Path $com -Pattern '^tools:.*mcp__context7__'                            # expect NO match
# body: plugin-qualified methodology + deposit calls, RESEARCH_DONE/BLOCKED, leaf-teammate + inert-frontmatter notes
Select-String -Path $dep -Pattern "Skill\('claude-toolkit:dependency-research-methodology'\)","Skill\('claude-toolkit:research-deposit'\)",'RESEARCH_DONE: <path>','RESEARCH_BLOCKED: <path>','leaf teammate','inert for teammates' | Select-Object Line
Select-String -Path $com -Pattern "Skill\('claude-toolkit:community-research-methodology'\)","Skill\('claude-toolkit:research-deposit'\)",'RESEARCH_DONE: <path>','RESEARCH_BLOCKED: <path>','leaf teammate','inert for teammates' | Select-Object Line
```
Expected: all frontmatter assertions match for both; **no** `Agent`/`AskUserQuestion` in either `tools:`; Context7 tools on the dependency researcher only; each body shows its plugin-qualified methodology call, the plugin-qualified `research-deposit` call, both completion tokens, and the leaf-teammate + inert-frontmatter notes (the five template elements: identity, methodology directive, deposit directive, tool note, skill-load note).

- [ ] **Step 6: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes. If `claude` is unavailable, record the skip and rely on Step 5.

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-dependency-researcher.md plugins/claude-toolkit/agents/or-community-researcher.md
git -C I:\Dev\claude-toolkit commit -m "feat(agents): add or-dependency-researcher and or-community-researcher research teammates"
```
Expected: two new files committed on `or-superpowers-at-scale`.

---

## Task 4: Author the five spawn-context templates (NEW)

Author the five per-spawn variable templates the SPAWN / SPAWN_RESEARCH brokers substitute when spawning each role. They are tiny and their content is **pinned verbatim** in the design (§"Spawn-context templates"). One cohesive "spawn-context" unit, one commit. These create the `assets/` directory under the Plan-2 skill dir.

**Files (all under `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\`):**
- Create: `brainstormer-spawn-context.md`
- Create: `plan-writer-spawn-context.md`
- Create: `supervisor-spawn-context.md`
- Create: `implementer-spawn-context.md`
- Create: `reviewer-spawn-context.md`

- [ ] **Step 1: Verify the five files do not yet exist (RED)**

```powershell
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
foreach ($n in 'brainstormer-spawn-context','plan-writer-spawn-context','supervisor-spawn-context','implementer-spawn-context','reviewer-spawn-context') {
  "{0}: {1}" -f $n, (Test-Path "$x\$n.md")
}
```
Expected: all five `False`.

- [ ] **Step 2: Create `brainstormer-spawn-context.md` with this exact content**

````markdown
Identity: <NAME> in team <TEAM>
Worktree: <WORKTREE_PATH>
Branch: <BRANCH>
Handover dir: <HANDOVER_DIR>
Initial user input: <USER_IDEA>
<if resuming after handover: Prior handover: <HANDOVER_DIR>/brainstormer-handover-<N-1>.md>
````

- [ ] **Step 3: Create `plan-writer-spawn-context.md` with this exact content**

````markdown
Identity: <NAME> in team <TEAM>
Worktree: <WORKTREE_PATH>
Branch: <BRANCH>
Handover dir: <HANDOVER_DIR>
Spec path: <SPEC_PATH>
<if resuming after handover: Prior handover: <HANDOVER_DIR>/plan-writer-handover-<N-1>.md>
````

- [ ] **Step 4: Create `supervisor-spawn-context.md` with this exact content**

````markdown
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
````

- [ ] **Step 5: Create `implementer-spawn-context.md` with this exact content**

````markdown
Identity: <NAME> in team <TEAM>
Branch: <BRANCH>
Supervisor: <SUPERVISOR_NAME>
````

- [ ] **Step 6: Create `reviewer-spawn-context.md` with this exact content**

(Parameterized by role at spawn time — one template for any reviewer role.)

````markdown
Identity: <NAME> (<ROLE>) in team <TEAM>
Branch: <BRANCH>
Supervisor: <SUPERVISOR_NAME>
````

- [ ] **Step 7: Verify all five exist and match the pinned content (GREEN)**

```powershell
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
foreach ($n in 'brainstormer-spawn-context','plan-writer-spawn-context','supervisor-spawn-context','implementer-spawn-context','reviewer-spawn-context') {
  "{0}: exists={1}" -f $n, (Test-Path "$x\$n.md")
}
# distinctive lines per template
Select-String -Path "$x\brainstormer-spawn-context.md" -Pattern 'Initial user input: <USER_IDEA>' | Select-Object Line
Select-String -Path "$x\plan-writer-spawn-context.md"  -Pattern 'Spec path: <SPEC_PATH>' | Select-Object Line
Select-String -Path "$x\supervisor-spawn-context.md"   -Pattern 'First SPAWN target hint: <FIRST_TASK_HINT>' | Select-Object Line
Select-String -Path "$x\implementer-spawn-context.md"  -Pattern 'Supervisor: <SUPERVISOR_NAME>' | Select-Object Line
Select-String -Path "$x\reviewer-spawn-context.md"     -Pattern 'Identity: <NAME> \(<ROLE>\) in team <TEAM>' | Select-Object Line
```
Expected: all five `exists=True`; each distinctive line present.

- [ ] **Step 8: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/
git -C I:\Dev\claude-toolkit commit -m "feat(skills): add or-superpowers-at-scale spawn-context templates"
```
Expected: five new files committed on `or-superpowers-at-scale`.

---

## Task 5: Author the four handover templates

Author the four handover-doc templates the Handover Ladder uses: the two phase-agent templates (NEW, pinned in the design), the iteration template (PRESERVED from the legacy skill with `or-*` naming normalization), and the manager template (ADAPTED — adds two phase fields + skill-ref normalization). One cohesive "handover templates" unit, one commit.

**Files (all under `…\skills\or-superpowers-at-scale\assets\`):**
- Create: `brainstormer-handover-template.md` (NEW)
- Create: `plan-writer-handover-template.md` (NEW)
- Create: `iteration-handover-template.md` (PRESERVED + naming normalization)
- Create: `manager-handover-template.md` (ADAPTED)

- [ ] **Step 1: Verify the four files do not yet exist (RED)**

```powershell
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
foreach ($n in 'brainstormer-handover-template','plan-writer-handover-template','iteration-handover-template','manager-handover-template') {
  "{0}: {1}" -f $n, (Test-Path "$x\$n.md")
}
```
Expected: all four `False`.

- [ ] **Step 2: Create `brainstormer-handover-template.md` with this exact content (NEW — design §"Phase handover templates")**

````markdown
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
````

- [ ] **Step 3: Create `plan-writer-handover-template.md` with this exact content (NEW — design §"Phase handover templates")**

````markdown
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
````

- [ ] **Step 4: Create `iteration-handover-template.md` (PRESERVED + `or-*` naming normalization)**

This is the legacy `subagent-driven-development-at-scale/assets/iteration-handover-template.md`, **preserved structure verbatim**, with the example agent names normalized to the orchestrator's `or-*` worker-naming convention (design impl-note #1 explicitly permits naming-update edits in PRESERVE content; the supervisor's authoritative naming table is `supervisor-<N>` → `or-supervisor-<N>`, `impl-task<N>` → `or-implementer-task<N>`, `spec-task<N>` → `or-spec-reviewer-task<N>`, `code-task<N>` → `or-code-quality-reviewer-task<N>`). Create with this exact content:

````markdown
---
title: Iteration <N> handover — <plan-slug>
date: <YYYY-MM-DD>
team: <team-name>
supervisor: or-supervisor-<N>
plan: <path/to/plan.md>
branch: <branch-name>
end_status: STOPPED_FOR_HANDOVER | COMPLETED
---

# Iteration <N> Handover

For STOPPED_FOR_HANDOVER: successor `or-supervisor-<N+1>` reads this FIRST, then continues from "Next Task to Start" below.

For COMPLETED: this doubles as the post-implementation report.

---

## Status (at handover)

- HEAD SHA: `<sha>`
- Tests: `<pass | fail with summary>`
- Typecheck: `<clean | errors with summary>`
- Branch state: `<n>` commits ahead of `<base>`, working tree `<clean | dirty + file list>`

## Summary

- Tasks completed this iteration: `<N>`
- Tasks completed cumulatively (plan total): `<N>` / `<TOTAL>`
- Commits this iteration: `<N>` (full SHA list under "Tasks Completed" below)

## Tasks Completed (this iteration)

| Task | Workers | Commits | One-line description |
|------|---------|---------|----------------------|
| Task <N>: <name> | `or-implementer-task<N>` / `or-spec-reviewer-task<N>` ✅ / `or-code-quality-reviewer-task<N>` ✅ | `<sha>`, `<sha>` | `<desc>` |

## Current Task State (omit if nothing in-flight or end_status = COMPLETED)

- Task: `<name>`
- Workers active: `<name>` — status `<DONE | fix-loop | reviewing>`
- Last accomplished: `<summary>`
- Next needed: `<summary>`
- Outstanding findings: `<list with file:line refs>`

## Next Task to Start (omit if end_status = COMPLETED)

Task `<N>`: `<name>`. First SPAWN: `or-implementer-task<N>`.

## Plan Deviations

- Task `<N>`: `<deviation + reasoning + approval source>`

## Reviewer Issues — Resolved

- Task `<N>` (`or-spec-reviewer-task<N>`): `<issue>` → `<fix sha>`
- Task `<N>` (`or-code-quality-reviewer-task<N>`): `<issue>` → `<fix sha>`

## Reviewer Issues — Parking Lot (deferred or unresolved)

- Task `<N>` (`or-code-quality-reviewer-task<N>`): `<soft note>` — deferred because `<reasoning>`

## Unplanned Changes

- Files modified outside plan scope: `<list>` — reason: `<...>`
- Unauthorized scope changes (caught and reverted, or accepted): `<list>`
- Dependencies added/changed beyond plan: `<list>`

(Empty if none.)

## Known Issues & Risks

- `<issue + impact + suggested next action>`
- Missing test coverage: `<areas>`
- Fragile-but-working: `<list>`

## Recommendations & Notes for Next Iteration

- Patterns that worked: `<list>`
- New precedents established: `<list>`
- Anti-patterns to avoid: `<list>`
- Suggested follow-up tasks: `<list>`
- Technical debt introduced: `<list>`

## Plan Progress

- Completed: `<N>` / `<TOTAL>` tasks
- In flight: `<task or none>`
- Remaining: `<list of task names>`
````

- [ ] **Step 5: Create `manager-handover-template.md` (ADAPTED — design §"Handover Ladder" + §"Manager handover during phase 1 or 2")**

This is the legacy manager-handover template, with three adaptations: (a) the Topology & Protocol Reference points at **this** plugin skill (`or-superpowers-at-scale`, invoked plugin-qualified) instead of the legacy loose skill; (b) the supervisor reference is normalized to `or-supervisor-<N>`; (c) a new **`active_phase` / `active_phase_agent`** block is added so a fresh manager on resume knows whether a brainstormer/plan-writer is alive or implementation was already underway (design §"Manager handover during phase 1 or 2"). The `~/.claude/teams/<team>/config.json` path is retained — teams genuinely live there at runtime (design §"Fresh manager session resume"). Create with this exact content:

````markdown
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
````

- [ ] **Step 6: Verify all four exist with the right structure (GREEN)**

```powershell
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
foreach ($n in 'brainstormer-handover-template','plan-writer-handover-template','iteration-handover-template','manager-handover-template') {
  "{0}: exists={1}" -f $n, (Test-Path "$x\$n.md")
}
# NEW phase templates: the load-bearing anti-drift fields
Select-String -Path "$x\brainstormer-handover-template.md" -Pattern '^predecessor: or-brainstormer-<N>$','## User preferences captured so far \(not yet in spec\)','- Latest revision: <one-line>' | Select-Object Line
Select-String -Path "$x\plan-writer-handover-template.md"  -Pattern '^predecessor: or-plan-writer-<N>$','## Outstanding user feedback not yet applied','- Latest revision: <one-line>' | Select-Object Line
# iteration: PRESERVED structure + normalized names; NO legacy bare names
Select-String -Path "$x\iteration-handover-template.md" -Pattern '^supervisor: or-supervisor-<N>$','or-implementer-task<N>','or-code-quality-reviewer-task<N>' | Select-Object Line
Select-String -Path "$x\iteration-handover-template.md" -Pattern '^supervisor: supervisor-<N>$','`impl-task<N>`','`code-task<N>`'   # expect NO match (legacy names normalized)
# manager: ADAPTED — the two new phase fields + plugin-qualified skill ref
Select-String -Path "$x\manager-handover-template.md" -Pattern '^active_phase: brainstorm \| plan \| implement$','^active_phase_agent:','Skill\(.claude-toolkit:or-superpowers-at-scale.\)','or-supervisor-<N>' | Select-Object Line
Select-String -Path "$x\manager-handover-template.md" -Pattern 'subagent-driven-development-at-scale'   # expect NO match (legacy skill ref replaced)
```
Expected: all four `exists=True`; the phase templates carry their predecessor + not-yet-applied + Latest-revision fields; the iteration template shows normalized `or-*` names and **no** legacy bare names; the manager template shows the two new phase fields, the plugin-qualified skill reference, and **no** legacy `subagent-driven-development-at-scale` reference.

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/
git -C I:\Dev\claude-toolkit commit -m "feat(skills): add or-superpowers-at-scale handover templates"
```
Expected: four new files committed on `or-superpowers-at-scale`.

---

## Task 6: Author the two protocol references (`spawn-protocol.md`, `preflight-brief.md`) — ADAPTED

Author the two ADAPTED reference assets. `spawn-protocol.md` preserves the legacy SPAWN handshake (normalized to `manager`, plugin-qualified `claude-toolkit:or-<role>` subagent types, and role spawn-context substitution) and **adds** the SPAWN_RESEARCH section (design §"SPAWN_RESEARCH protocol"). `preflight-brief.md` preserves the legacy preflight's check/output discipline and **adds** mode detection, worktree-name + base-branch prompting, and the extended `PREFLIGHT_OK` block (design §"Mode Detection", §"Phase flow" Phase 0). One "protocol references" unit, one commit. (SHUTDOWN is intentionally not here — see "spawn-protocol.md scope" above.)

**Files (all under `…\skills\or-superpowers-at-scale\assets\`):**
- Create: `spawn-protocol.md`
- Create: `preflight-brief.md`

- [ ] **Step 1: Verify neither file exists yet (RED)**

```powershell
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
Test-Path "$x\spawn-protocol.md"     # expect False
Test-Path "$x\preflight-brief.md"    # expect False
```
Expected: both `False`.

- [ ] **Step 2: Create `spawn-protocol.md` with this exact content (ADAPTED)**

````markdown
# SPAWN / SPAWN_RESEARCH Protocol — full mechanics

The handshakes that let depth-1 tiers (the supervisor and the phase agents — none of which hold the `Agent` tool) cause a fresh teammate to be spawned via the `manager` (the sole `Agent`-tool holder). Both the manager and the requesting tier load this file as canonical reference.

---

## SPAWN (worker dispatch — supervisor → manager)

```
[Supervisor]   SendMessage manager:
                   SPAWN
                   NAME: or-implementer-task5
                   ROLE: implementer
                   MODEL: sonnet

[Manager]      SAME TURN:
               1. Agent({
                    team_name: <team>,
                    name: "or-implementer-task5",
                    subagent_type: "claude-toolkit:or-implementer",   // ROLE mapped — see table
                    model: "sonnet",
                    prompt: <substituted implementer-spawn-context.md>,
                    run_in_background: true
                  })
               2. SendMessage supervisor:
                    Spawned: or-implementer-task5

[Supervisor]   SAME TURN after `Spawned: or-implementer-task5`:
               SendMessage or-implementer-task5:
                   <task-specific brief built from SDD's implementer-prompt.md
                    template, with Task 5's full text + scene-setting context>
```

No idle gap. The manager's two actions are same-turn; the supervisor's task brief is same-turn after `Spawned:` confirmation.

### SPAWN message format (exact)

The message body MUST be EXACTLY this shape, as its own SendMessage (no preamble, no trailing text):

    SPAWN
    NAME: <name>
    ROLE: <role>
    MODEL: <model>

Where:
- `<name>` follows the worker naming convention (`or-implementer-task5`, `or-code-quality-reviewer-task5-rev2`, etc. — the authoritative table is in `or-supervisor.md`).
- `<role>` ∈ {`implementer`, `spec-reviewer`, `code-quality-reviewer`, `final-reviewer`}.
- `<model>` ∈ {`sonnet`, `opus`, `haiku`}. Pick per SDD's model-selection guidance. **For `implementer`, `MODEL` is REQUIRED** — the `or-implementer` agent has no default `model:`; a SPAWN that omits it for an implementer is a protocol violation (manager replies `SPAWN rejected — implementer requires explicit MODEL field.`).

If you need to include rationale or context, send it in a separate SendMessage AFTER the `Spawned:` response — never inside the SPAWN message.

### ROLE → subagent_type mapping (manager broker)

The manager maps the short `ROLE` to the plugin-qualified `subagent_type`:

| ROLE | subagent_type |
|------|---------------|
| `implementer` | `claude-toolkit:or-implementer` |
| `spec-reviewer` | `claude-toolkit:or-spec-reviewer` |
| `code-quality-reviewer` | `claude-toolkit:or-code-quality-reviewer` |
| `final-reviewer` | `claude-toolkit:or-final-reviewer` |

The manager substitutes the matching role spawn-context template for the worker's per-spawn variables — `implementer-spawn-context.md` for the implementer; `reviewer-spawn-context.md` (parameterised by `<ROLE>`) for any reviewer — then calls `Agent(...)` with `run_in_background: true`. Manager replies stay terse — `Spawned: <name>` is the entire message body. Acknowledgments and progress narration belong in the supervisor's `iteration-N.md`, not in chat.

---

## SPAWN_RESEARCH (research dispatch — phase agent → manager)

A phase agent SendMessages the manager:

```
SPAWN_RESEARCH
NAME: <name>
AGENT: <subagent_type>
DEPOSIT: <path>                       (required — findings never transit manager context)
MODEL: <model>                        (optional; defaults to the agent's frontmatter default)
PROMPT: <research question>
```

All research agents are spawned as **background teammates** (`run_in_background: true`, WITH `team_name`) — mechanically identical to worker dispatch. They signal completion by SendMessaging the manager a `RESEARCH_DONE: <path>` / `RESEARCH_BLOCKED: <path> — <reason>` token. After relaying to the phase agent, the manager shuts the research teammate down to keep the roster clean.

| Case | Manager action |
|------|----------------|
| `AGENT` is `or-dependency-researcher` or `or-community-researcher` (always deposit-aware) | Spawn as a background teammate with `DEPOSIT` appended to the prompt. The agent writes findings to `<DEPOSIT>` and SendMessages `RESEARCH_DONE: <path>`. Manager forwards `Research <name> done: <path>` to the phase agent, then shuts the researcher down. Manager NEVER opens the findings file. |
| `AGENT` is any other subagent_type (`dependency-researcher`/`community-researcher`/`Plan`/`Explore`/`general-purpose`, …) | Wrap: spawn `general-purpose` as a background teammate with a prompt that imitates the requested agent's style + writes to `<DEPOSIT>` + SendMessages `RESEARCH_DONE: <path>`. (Or, if the requested agent already has both `Write` and `SendMessage`, spawn it directly with the deposit instruction appended.) Manager shuts it down after relay. |

If a `SPAWN_RESEARCH` omits `DEPOSIT`, the manager rejects it (findings must never transit manager context): SendMessage the phase agent `SPAWN_RESEARCH rejected — DEPOSIT is required.` and take no further action on that request.

Then the manager SendMessages the phase agent: `Spawned: <name>`.
````

- [ ] **Step 3: Create `preflight-brief.md` with this exact content (ADAPTED)**

````markdown
You are the preflight agent for `or-superpowers-at-scale`. Your job is to detect the run mode, prepare the worktree, verify the environment, and return a one-block summary to the manager. **Only emit the structured summary block at the end — do not narrate, do not explain, do not echo your work.**

Every word you emit ends up in the manager's context, which is the scarcest resource in this topology. Run all the checks in your own context; surface only the result.

## Inputs

- User input: `<USER_INPUT>` (an idea statement, a spec path, a plan path, or empty)
- User pre-authorised work on main/master: `<USER_CONSENT or "no">`

## Step 1 — Detect mode

Classify `<USER_INPUT>`:

| Input shape | Mode |
|-------------|------|
| Plain text (idea statement) or empty | `idea` |
| Path matching `docs/superpowers/specs/*-design.md` (or a user-supplied spec path that exists) | `spec` |
| Path matching `docs/superpowers/plans/*.md` (or a user-supplied plan path that exists) | `plan` |

If the shape is ambiguous (e.g. a path that matches neither convention), ask the user with `AskUserQuestion`: "I see you provided `<input>`. Is this an idea, a spec, or a plan?" Never guess.

## Step 2 — Prompt for worktree name + base branch

Use `AskUserQuestion` to ask the user for:
- the **worktree name** (offer a slug derived from the idea/spec/plan as the suggested default), and
- the **base branch** to branch from (default: current HEAD; if that is `main`/`master` and `<USER_CONSENT>` is not "yes", require an explicit non-default choice).

## Step 3 — Checks (in order; stop on first failure)

1. **Mode artifact exists (modes `spec`/`plan` only).** `test -f <path>`. Missing → FAIL.
2. **Branch is appropriate.** If the chosen base is `main`/`master` and `<USER_CONSENT>` is not "yes" → FAIL.
3. **Worktree ready.** Invoke `Skill("superpowers:using-git-worktrees")` and apply its check; create the worktree with the chosen name off the chosen base, and create a `handovers/` directory under the worktree for this session's handover docs. **You absorb the worktree-skill content; the manager does NOT need it in its context.** If something fundamentally blocks worktree setup → FAIL.
4. **Metadata extraction.**
   - For `spec`: read the spec's leading section; extract a one-line goal.
   - For `plan`: read the plan's leading section (first ~80 lines — the preamble, before the task list); extract total task count (count `### Task N:` or equivalent headings via grep/wc rather than reading the whole plan if it's large), the one-line goal (usually `**Goal:**` or the top-line summary), and project conventions surfaced in the preamble (commit format, test command, typecheck command, anything notable).
   - For `idea`: no artifact yet — `goal`, `spec_path`, `plan_path`, and `total_tasks` are `none`.

## Step 4 — Output (exact format)

If all checks pass, emit ONLY this block as your final message:

```
PREFLIGHT_OK
mode: idea | spec | plan
worktree: <path>
branch: <branch-name>
handover_dir: <path>
spec_path: <path-or-none>
plan_path: <path-or-none>
goal: <one-line, if spec/plan provided; else none>
total_tasks: <N, if plan provided; else none>
conventions:
  commit_format: <convention or "(none specified)">
  test_command: <cmd or "(none specified)">
  typecheck_command: <cmd or "(none specified)">
  other: <bullets or "(none)">
```

If a check fails, emit ONLY:

```
PREFLIGHT_FAIL
reason: <one-sentence reason>
suggested_recovery: <one-sentence action the user can take>
```

Brevity is load-bearing. The manager uses this block as the substrate for the next phase agent's (or the supervisor's) spawn-context — every extra word displaces a word the manager could have held from a later SPAWN message.
````

- [ ] **Step 4: Verify both references are complete and correctly adapted (GREEN)**

```powershell
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
Test-Path "$x\spawn-protocol.md"; Test-Path "$x\preflight-brief.md"                   # expect True, True
# spawn-protocol: normalized to manager (no legacy team-lead), plugin-qualified mapping, SPAWN_RESEARCH added, deposit required; SHUTDOWN absent
Select-String -Path "$x\spawn-protocol.md" -Pattern '## SPAWN \(worker dispatch','## SPAWN_RESEARCH \(research dispatch','claude-toolkit:or-implementer','DEPOSIT: <path>','implementer requires explicit MODEL field' | Select-Object Line
Select-String -Path "$x\spawn-protocol.md" -Pattern '\bteam-lead\b'                                                          # expect NO match (normalized to "manager")
Select-String -Path "$x\spawn-protocol.md" -Pattern '^## SHUTDOWN'                                                           # expect NO match (deferred to Plan 4 SKILL.md)
# preflight: mode detection + worktree/branch prompt + extended PREFLIGHT_OK
Select-String -Path "$x\preflight-brief.md" -Pattern '## Step 1 — Detect mode','AskUserQuestion','^mode: idea \| spec \| plan$','^handover_dir: <path>$','PREFLIGHT_OK','PREFLIGHT_FAIL' | Select-Object Line
```
Expected: both `True`; `spawn-protocol.md` has both protocol sections, the plugin-qualified mapping, the deposit-required rule, and the implementer-MODEL rule, with **no** `team-lead` reference and **no** `## SHUTDOWN` heading; `preflight-brief.md` has the mode-detection step, the `AskUserQuestion` prompts, and the extended `PREFLIGHT_OK`/`PREFLIGHT_FAIL` blocks (including `mode:` and `handover_dir:`).

- [ ] **Step 5: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes (the assets are plain Markdown; the skill and plugin frontmatter are unchanged). If `claude` is unavailable, record the skip and rely on Step 4.

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/spawn-protocol.md plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/preflight-brief.md
git -C I:\Dev\claude-toolkit commit -m "feat(skills): add or-superpowers-at-scale spawn-protocol and preflight-brief references"
```
Expected: two new files committed on `or-superpowers-at-scale`.

---

## Task 7: Plan-3 integration self-review

A consolidation gate confirming all seven agents are in `agents/` (the five finalized here + the two from Plan 2, plus the two research bodies = nine `or-*` agents total), the eleven assets exist, every phase/supervisor agent invokes the orchestrator skill for protocol/template refs (no stale `~/.claude`/`assets/*` paths), depth-1 holds everywhere, the plugin validates, no draft remains, and no manifest/user-facing churn leaked in. Verification only — no new component files; a commit is made only if a fix is required.

**Files:** none created.

- [ ] **Step 1: All nine `or-*` agents live in `agents/`, all seven drafts gone**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
$nine = 'or-brainstormer','or-plan-writer','or-supervisor','or-implementer','or-spec-reviewer','or-code-quality-reviewer','or-final-reviewer','or-dependency-researcher','or-community-researcher'
foreach ($n in $nine) { "{0}: {1}" -f $n, (Test-Path "$a\$n.md") }
Get-ChildItem "I:\Dev\claude-toolkit\docs\superpowers\drafts\" -Filter *.md -ErrorAction SilentlyContinue | Measure-Object | ForEach-Object { "drafts remaining: {0}" -f $_.Count }
```
Expected: all nine `True`; `drafts remaining: 0` (Plan 2 moved two; Plan 3 moved the other five — the drafts directory is now empty of `or-*.md`).

- [ ] **Step 2: Depth-1 holds across every `or-*` agent; reviewers/researchers carry the right tools**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
# NO Agent tool in any or-* agent
Select-String -Path "$a\or-*.md" -Pattern '^tools:.*\bAgent\b'                          # expect NO match
# every or-* agent carries SendMessage (load-bearing for STATUS / completion / research signalling)
$nine = 'or-brainstormer','or-plan-writer','or-supervisor','or-implementer','or-spec-reviewer','or-code-quality-reviewer','or-final-reviewer','or-dependency-researcher','or-community-researcher'
foreach ($n in $nine) { "{0}: SendMessage={1}" -f $n, [bool](Select-String -Path "$a\$n.md" -Pattern '^tools:.*\bSendMessage\b') }
# research bodies carry Write + Skill; reviewers carry neither Skill nor Write
Select-String -Path "$a\or-dependency-researcher.md","$a\or-community-researcher.md" -Pattern '^tools:.*\bWrite\b.*\bSkill\b' | Select-Object Path
Select-String -Path "$a\or-spec-reviewer.md","$a\or-code-quality-reviewer.md","$a\or-final-reviewer.md" -Pattern '^tools:.*\b(Skill|Write|Edit)\b'   # expect NO match
```
Expected: **no** `Agent` anywhere; every agent shows `SendMessage=True`; the two research bodies carry `Write` + `Skill`; the three reviewers carry none of `Skill`/`Write`/`Edit` (read-only + SendMessage only).

- [ ] **Step 3: Supervisor + phase agents invoke the orchestrator skill (no stale paths)**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
Select-String -Path "$a\or-supervisor.md","$a\or-brainstormer.md","$a\or-plan-writer.md" -Pattern '~/\.claude/skills/','assets/.*\.md'                 # expect NO match
foreach ($n in 'or-supervisor','or-brainstormer','or-plan-writer') { "{0}: skill-invocations={1}" -f $n, (Select-String -Path "$a\$n.md" -Pattern "Skill\('claude-toolkit:or-superpowers-at-scale'\)").Count }
```
Expected: **no** `~/.claude/skills/` or `assets/*.md` path reference in any of the three; each of `or-supervisor`/`or-brainstormer`/`or-plan-writer` shows `skill-invocations=2` — confirming all three reach orchestrator protocols/templates via skill invocation, not a path.

- [ ] **Step 4: All eleven assets exist under the skill**

```powershell
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
$eleven = 'brainstormer-spawn-context','plan-writer-spawn-context','supervisor-spawn-context','implementer-spawn-context','reviewer-spawn-context','brainstormer-handover-template','plan-writer-handover-template','iteration-handover-template','manager-handover-template','spawn-protocol','preflight-brief'
$present = ($eleven | Where-Object { Test-Path "$x\$_.md" }).Count
"assets present: $present / 11"
(Get-ChildItem "$x\*.md" | Measure-Object).Count | ForEach-Object { "assets in dir: $_" }
```
Expected: `assets present: 11 / 11` and `assets in dir: 11` (exactly the eleven — no stray files).

- [ ] **Step 5: No agent references a bundled asset by path; the assets the skill surfaces all exist**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
$x = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
# invariant: NO or-* agent reaches an asset by path — protocol/template access is via skill invocation only
Select-String -Path "$a\or-*.md" -Pattern 'assets/.*\.md','~/\.claude/'
# the assets the skill surfaces to a teammate that invokes it (spawn-protocol + the three handover templates) exist
foreach ($f in 'spawn-protocol.md','iteration-handover-template.md','brainstormer-handover-template.md','plan-writer-handover-template.md') {
  "{0}: {1}" -f $f, (Test-Path "$x\$f")
}
```
Expected: **no** `assets/*.md` or `~/.claude/` path reference in any `or-*` agent body (agents invoke `Skill('claude-toolkit:or-superpowers-at-scale')` instead — Step 3); and each asset the skill surfaces on invocation (`spawn-protocol.md`, the iteration / brainstormer / plan-writer handover templates) is `True`. (Whether a teammate's skill invocation resolves that bundled content at runtime is impl-note #3 — deferred to the cutover spike.)

- [ ] **Step 6: Plugin validates; no manifest/version/README churn**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
git -C I:\Dev\claude-toolkit diff efe9637..HEAD --name-only -- plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
```
Expected: validation passes (or `claude` skip recorded). The `git diff` since the Plan-2 tip `efe9637` for the manifests + README returns **empty** — Plan 3 (like Plans 1–2) touched no version/manifest/README file (release deferred to Plan 4). If `claude` is unavailable, record the skip and rely on the structural greps in Steps 1–5.

- [ ] **Step 7: Commit graph is six clean component commits since Plan 2**

```powershell
git -C I:\Dev\claude-toolkit log --oneline efe9637..HEAD
```
Expected: six commits since the Plan-2 tip `efe9637` — `feat(agents): finalize or-implementer and the three reviewer workers`, `feat(agents): finalize or-supervisor`, `feat(agents): add or-dependency-researcher and or-community-researcher research teammates`, `feat(skills): add or-superpowers-at-scale spawn-context templates`, `feat(skills): add or-superpowers-at-scale handover templates`, `feat(skills): add or-superpowers-at-scale spawn-protocol and preflight-brief references` — plus (after this plan is saved) the Plan-3 doc commit.

- [ ] **Step 8: Spec-coverage check for Plan 3**

Confirm every Plan-3 design requirement has a corresponding artifact:
- Five remaining drafts finalized into `agents/`, frontmatter + bodies intact, depth-1 ✓ (design §"Agent Inventory" rows 3–7, §"`or-supervisor.md` body composition", §"`or-implementer.md` frontmatter" — no `model:`)
- All five reviewed drafts (incl. `or-supervisor`) finalized verbatim; agents reach orchestrator protocols + handover templates by invoking `Skill('claude-toolkit:or-superpowers-at-scale')` — no stale `~/.claude`/`assets/*` paths ✓ (skill-invocation rework; design §"Skill loading mechanism", re-homing revision 2026-05-30)
- Two research teammates authored from the template — five body elements, plugin-qualified `Skill(...)` calls, `Write`+`SendMessage`, no `Agent`/`AskUserQuestion`, Context7 on dependency only ✓ (design §"Research agent body", §"Agent Inventory" rows 8–9)
- Five spawn-context templates — content matches design §"Spawn-context templates" verbatim ✓
- Two phase handover templates — content matches design §"Phase handover templates" verbatim ✓
- Iteration handover template PRESERVED with `or-*` naming normalization ✓ (Asset Inventory; impl-note #1)
- Manager handover template ADAPTED — `active_phase` + `active_phase_agent` added, skill ref re-homed ✓ (design §"Handover Ladder", §"Manager handover during phase 1 or 2")
- `spawn-protocol.md` ADAPTED — SPAWN preserved+normalized, SPAWN_RESEARCH added; SHUTDOWN deliberately deferred to Plan 4 ✓ (Asset Inventory; design §"SPAWN_RESEARCH protocol")
- `preflight-brief.md` ADAPTED — mode detection + worktree/branch prompt + extended PREFLIGHT_OK ✓ (design §"Mode Detection", §"Phase flow" Phase 0)
- Release/version/README/command: intentionally **not** touched in Plan 3 (deferred to Plan 4) ✓
- Operating-discipline `SKILL.md` body + SHUTDOWN canonical text: intentionally **not** here (Plan 4) ✓

- [ ] **Step 9: Checkpoint — Plan 3 complete**

All checks green (or `claude plugin validate` explicitly noted as skipped). If any step required an edit, commit it:
```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "fix(plan-3): integration self-review corrections"
```
Otherwise, no commit is needed — Tasks 1–6 already committed their work. The full implementation tier (supervisor + workers), the two research teammates, and every `assets/*` template the orchestrator skill references now exist on the branch. Ready for Plan 4 (the manager-discipline `SKILL.md` body appended to the skeleton — including the canonical SHUTDOWN handshake and the manager-side SPAWN/SPAWN_RESEARCH broker behavior — the optional `commands/` wrapper, and the suite **release step**: 1.1.1 → 1.2.0 bump, marketplace sync, README, push on approval).

---

## Self-Review (run after implementation, before declaring Plan 3 done)

**1. Spec coverage:** Task 7 Step 8 enumerates the Plan-3 component requirements against the design (five draft finalizations, two research bodies, eleven assets), plus the deliberate Plan-4 deferrals (operating-discipline body, SHUTDOWN canonical text, command wrapper, release). No gaps.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to above". The deliberately-not-inlined content is the five reviewed agent bodies (`or-supervisor`, `or-implementer`, and the three reviewers) — relocated by `git mv` (a byte-faithful move of reviewed, committed content) and verified by frontmatter/anchor greps + R100 rename detection + line-count equality, because re-inlining them would duplicate the thing being finalized. All five are pure moves with no body edit: their drafts already invoke `Skill('claude-toolkit:or-superpowers-at-scale')` for protocol/template refs (the pre-suite skill-invocation rework). Every newly-authored file (the two research bodies, all eleven assets) is shown complete and verbatim in its task. The PRESERVED iteration template and ADAPTED manager template / spawn-protocol / preflight-brief are each inlined in full (not "PRESERVE from X" by reference), so the engineer needs no second file open.

**3. Type/name consistency:** Agent names (`or-supervisor`, `or-implementer`, `or-spec-reviewer`, `or-code-quality-reviewer`, `or-final-reviewer`, `or-dependency-researcher`, `or-community-researcher`) match the drafts, the spec Agent Inventory, and the Plan-2 skeleton's phase-flow. The worker-naming convention (`or-implementer-task<N>`, `or-spec-reviewer-task<N>`, `or-code-quality-reviewer-task<N>`, `or-final-reviewer`) is identical in the supervisor body, the iteration template's normalized names, and the spawn-protocol examples. The `ROLE → subagent_type` map (`implementer → claude-toolkit:or-implementer`, etc.) matches the spec §"SPAWN protocol". The research bodies' in-body skill names (`claude-toolkit:dependency-research-methodology`, `claude-toolkit:community-research-methodology`, `claude-toolkit:research-deposit`) match the Skill Inventory and Plan 1's authored skill names; their `skills:` frontmatter uses the bare forms, matching Plan 1's qualified-in-body / bare-in-frontmatter split. Completion tokens (`RESEARCH_DONE: <path>`, `RESEARCH_BLOCKED: <path> — <reason>`, `ITERATION <N> — STOPPED_FOR_HANDOVER`) match the design §"Handover trigger token shape" and §"Research-deposit semantics". The spawn-context filenames the broker substitutes (`implementer-spawn-context.md`, `reviewer-spawn-context.md`) match the files authored in Task 4. Agents reach the orchestrator's protocols + handover templates by invoking `Skill('claude-toolkit:or-superpowers-at-scale')` (Task 7 Steps 3, 5), not by asset paths; the assets that skill surfaces are authored in Tasks 4–6.

## Plan suite status

This is **Plan 3 of 4**. Remaining: Plan 4 (manager-discipline `SKILL.md` body appended to the Plan-2 skeleton — Mode Detection, the manager-side SPAWN / **SHUTDOWN** / SPAWN_RESEARCH broker protocols, the Handover Ladder, Manager Context Discipline, Red Flags — plus the optional `commands/or-superpowers-at-scale.md` wrapper and the suite **release step**: 1.1.1 → 1.2.0 bump, marketplace sync, README, push on approval). The `last-plan-doc` pointer and a suite index are set once all four plans are written (design handover) — **deferred**. **Do not** proceed to execution from this file alone — execution is driven for the whole suite via `/implement-from-plan` after the suite is complete and reviewed.
