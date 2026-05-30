# `or-superpowers-at-scale` — Plan 1: Research Skills + Deposit Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Skill/agent authoring steps are also governed by **superpowers:writing-skills** — load it before authoring any skill file.

**Goal:** Extract the two research methodologies into standalone, shareable plugin skills and author the `research-deposit` protocol skill, then thin the two existing researcher agents into wrappers that pre-seed those skills — so the same methodology is reused by both the existing foreground researchers and (later) the orchestrator's `or-*` research teammates.

**Architecture:** Three new skills under the `claude-toolkit` plugin (`plugins/claude-toolkit/skills/{research-deposit, dependency-research-methodology, community-research-methodology}/SKILL.md`). Methodology content is *moved* (not duplicated) out of the existing plugin agent bodies into the methodology skills, leaving each agent file a thin wrapper: identity line + `skills:` frontmatter pre-seed + an in-body plugin-qualified `Skill(...)` call that loads the methodology. The methodology then lives in exactly one place (single source of truth).

**Tech Stack:** Claude Code plugin components — Markdown files with YAML frontmatter, inside the `claude-toolkit` plugin repo (`I:\Dev\claude-toolkit`, real git). No compiled code. Verification is by structural assertion (frontmatter/content greps) plus `claude plugin validate`; per-task `git commit` is the rollback boundary.

---

## Scope of this plan (Plan 1 of 4)

This is the **foundation** plan of the `or-superpowers-at-scale` suite (design: `docs/superpowers/specs/2026-05-24-or-superpowers-at-scale-design.md`, authoritative; see esp. the **Plugin Packaging**, **Skill Inventory**, and **Existing agents updated** sections). It is fully independent of the orchestrator — it ships standalone value (the existing researchers keep working, now backed by shared skills) and has **zero dependency** on any `or-*` asset.

In scope:
- `research-deposit` skill (NEW) — authored **first** (design impl-note #5: smallest skill, validates the skill-creation + pre-seed pattern).
- `dependency-research-methodology` skill (extracted from `plugins/claude-toolkit/agents/dependency-researcher.md`).
- `community-research-methodology` skill (extracted from `plugins/claude-toolkit/agents/community-researcher.md`).
- Refactor `plugins/claude-toolkit/agents/dependency-researcher.md` → thin wrapper.
- Refactor `plugins/claude-toolkit/agents/community-researcher.md` → thin wrapper (also gains the `Skill` tool, which it currently lacks).

Out of scope (later plans): the `or-dependency-researcher` / `or-community-researcher` teammate agents that *also* pre-seed these skills (Plan 3); everything orchestrator-side (Plans 2–4); the version bump + marketplace sync + README + push (deferred — see "Release deferral" below).

## Git workflow (READ FIRST)

`I:\Dev\claude-toolkit` **is a real git repository** (verified). All work happens on the existing feature branch **`or-superpowers-at-scale`** with **one commit per task** (design §"Git workflow"). The real-git review/rollback loop applies — this is the SDD rollback boundary. The superseded draft of this plan assumed `~/.claude` was not a repo and used no-commit "Checkpoint" gates; that workaround is **void** — use real commits.

- The working directory is `C:\Users\marti\.claude` (a different drive from the repo). **Every git command targets the repo explicitly via `git -C I:\Dev\claude-toolkit …`** — do not rely on the ambient cwd, and do not `cd` (it can trigger a permission prompt).
- Do **not** `git push` in this plan. The branch stays local until the whole suite is reviewed and the user approves a release (design handover: push only when asked).

## Release deferral (resolves a spec inconsistency — confirm at review)

The design's Plugin Packaging section says two things that don't fully reconcile: "*each plan's final task bumps versions and syncs the marketplace*" **and** "*Net bump for the whole orchestrator: 1.1.1 → 1.2.0 (minor — new components), finalized at release*." Four plans each doing a minor bump would land at 1.5.0, not a single net minor.

**Resolution adopted here:** treat the whole orchestrator as a single minor increment. **No version/manifest/README change in Plan 1** (or Plans 2–3). The one-time bump `1.1.1 → 1.2.0` + `marketplace.json` sync (both `metadata.version` and `plugins[].version`) + README component listing + `git push` is a dedicated **release step in Plan 4**, executed only on user approval. This honors the unambiguous "net 1.2.0, finalized at release" and "push only when asked." ⚠️ **Flag at review:** if you instead want per-plan patch bumps (1.1.2 → 1.1.3 → …), say so and Plan 1's final task gains a bump step; otherwise the spec's "each plan bumps" wording should be reconciled to "the suite's release bumps."

## Source-of-truth references

| Artifact being built | Source content | Notes |
|---|---|---|
| `skills/research-deposit/SKILL.md` | Design §"`research-deposit` skill body (NEW)" + §"Research-deposit semantics" | NEW content — inlined in full in Task 1 (canonical wording of the deposit protocol lives in this skill). |
| `skills/dependency-research-methodology/SKILL.md` | `plugins/claude-toolkit/agents/dependency-researcher.md` body, `# Your Process` (L10) → end of `# What NOT To Do` (L128) | Verbatim **move**. Pinned description from design §"`dependency-research-methodology` skill body". |
| `skills/community-research-methodology/SKILL.md` | `plugins/claude-toolkit/agents/community-researcher.md` body, `# What You Research` (L19) → end of `# What NOT To Do` (L175) | Verbatim **move** (NOT `# When to Use This Agent`, L10–17). Pinned description from design §"`community-research-methodology` skill body". |
| `agents/dependency-researcher.md` (refactor) | Design §"Existing agents updated" row 1 | Already has `Skill` in tools. |
| `agents/community-researcher.md` (refactor) | Design §"Existing agents updated" row 2 | Must **add** `Skill` to tools. |

All paths above are relative to the plugin root `I:\Dev\claude-toolkit\plugins\claude-toolkit\`. The two researcher source files are the **plugin's canonical copies** — NOT the drifted, out-of-scope `~/.claude/agents/` copies (design §"Existing researchers — canonical source"). Line numbers were read from the canonical files on 2026-05-30; if they differ, the heading anchors are stable — use them.

**Why methodology bodies are referenced by source anchor, not re-inlined:** the methodology content is a *verbatim move* from an existing file, not new authoring. Re-typing ~120 lines into this plan would invite transcription drift and create a second copy of the very thing we are de-duplicating. Each extraction task specifies the exact source file, the exact heading range to move, and grep-based verification that the move was faithful — precise and unambiguous, with nothing to guess. (This is the one deliberate exception to "inline all code"; the rationale is that the content already exists verbatim and the plan's job is to relocate it intact.)

## Verification approach (why no live `Skill()` / dispatch gate)

The `claude-toolkit` marketplace is **not installed in the authoring session** (design handover). So an in-session `Skill('claude-toolkit:research-deposit')` would not load the file we just wrote, and dispatching `subagent_type: dependency-researcher` would hit the stale loose `~/.claude` copy, not the refactored plugin file — a live test here would validate the wrong thing or fail spuriously. Plan 1's **hard gates are therefore structural** (frontmatter validity + content-move greps, run against the repo files) **plus `claude plugin validate`** (Task 4). End-to-end behavioral validation of the wrappers happens at install time and overlaps the design's impl-note #3 spike (the in-body skill-load-on-a-teammate check, scheduled for Plan 2); it is intentionally **not** a Plan 1 gate.

---

## Task 1: `research-deposit` skill (author first)

Authored first per design impl-note #5 — it is the smallest skill and validates the create-a-skill + pre-seed pattern before the larger extractions. It has no source agent to extract from; its content is specified in full below.

**Files:**
- Create: `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\research-deposit\SKILL.md`

- [ ] **Step 1: Load the authoring discipline**

Invoke `Skill('superpowers:writing-skills')` and skim it. The load-bearing parts for this task: skill frontmatter is `name` + `description` only (this plugin's convention — see `plugins/claude-toolkit/skills/updating-plugin/SKILL.md`, which has exactly those two fields); the description must say *when to use*, not restate the body.

- [ ] **Step 2: Verify the skill does not yet exist (RED)**

Run:
```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\research-deposit\SKILL.md"
```
Expected: `False`. (Confirms we are creating, not silently overwriting.)

- [ ] **Step 3: Create the skill directory + file with this exact content**

Create `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\research-deposit\SKILL.md`:

````markdown
---
name: research-deposit
description: Use when you are a deposit-aware research agent whose spawn prompt includes a "DEPOSIT: <path>" parameter — defines how to write full findings to disk and signal completion to the dispatching parent with a single minimal token. Not a trigger to start research; it governs how research output is delivered.
---

# Research Deposit Protocol

You are a deposit-aware research agent. Your findings are delivered to disk, never echoed back through the parent's context.

## When this applies

Your spawn prompt includes a `DEPOSIT: <path>` parameter. That `<path>` is where your full findings must be written.

## Protocol

1. Conduct your research per your methodology skill.
2. Write your **full findings** to `<path>` using the `Write` tool — the complete report, not a summary.
3. SendMessage the dispatching parent (the manager) exactly:

       RESEARCH_DONE: <path>

   — that line and nothing else.
4. Do **not** echo findings into the message. Do **not** summarise back to the parent. The findings live on disk; the parent reads them from there (or hands the path to whoever needs them).

## If you cannot complete

If the research is blocked or only partially possible, still write what you gathered to `<path>`, then SendMessage:

    RESEARCH_BLOCKED: <path> — <one-line reason>

instead of `RESEARCH_DONE`.

## Why this matters

The whole point of deposit is to keep large findings out of the parent's (manager's) context: one token in (`DEPOSIT: <path>`), one token out (`RESEARCH_DONE: <path>`). Echoing findings into your reply defeats the protocol.
````

- [ ] **Step 4: Verify frontmatter is valid and description is when-to-use (GREEN)**

Run:
```powershell
Get-Content "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\research-deposit\SKILL.md" -TotalCount 4
```
Expected: a `---` fence, `name: research-deposit`, a `description:` line beginning `Use when you are a deposit-aware research agent`, closing `---`. Confirm the description states *when to use* and includes the "Not a trigger to start research" scoping clause.

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/research-deposit/SKILL.md
git -C I:\Dev\claude-toolkit commit -m "feat(skills): add research-deposit protocol skill"
```
Expected: one file committed on branch `or-superpowers-at-scale`.

---

## Task 2: `dependency-research-methodology` skill + thin-wrapper `dependency-researcher`

Extract the methodology out of the existing plugin agent into a skill, then thin the agent to a wrapper that pre-seeds it. These are coupled and land in one commit: the agent must not be thinned until the skill holds its methodology.

**Files:**
- Create: `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\dependency-research-methodology\SKILL.md`
- Modify: `I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\dependency-researcher.md` (replace body; add `skills:` to frontmatter)

- [ ] **Step 1: Capture the source methodology range (RED baseline)**

Confirm the methodology is currently inline in the canonical plugin agent and will be moved. Run:
```powershell
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\dependency-researcher.md" -Pattern '^# Your Process$','^# Citation Requirements$','^# What NOT To Do$' | Select-Object LineNumber,Line
```
Expected (read 2026-05-30): `# Your Process` at line 10, `# Citation Requirements` at line 113, `# What NOT To Do` at line 122. These bound the methodology block: `# Your Process` (L10) through the end of the file (L128, the bullet `Do NOT exceed 3 follow-up cycles per research area`). If line numbers differ, use the heading anchors — they are stable.

- [ ] **Step 2: Create the methodology skill with the pinned description + the moved body**

Create `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\dependency-research-methodology\SKILL.md`. Begin with this exact frontmatter + intro:

```markdown
---
name: dependency-research-methodology
description: Use when you are an agent already executing a library/SDK/API research task and need the structured research-and-citation workflow. Not a trigger to research inline — the main agent must still delegate to the dependency-researcher agent.
---

# Dependency Research Methodology

This is the structured workflow for a library/SDK/API research task: decompose the request into focused areas, fetch from multiple sources, evaluate against the objective, and synthesise a fully-cited report.
```

Then, **immediately below that intro**, paste the agent's methodology block **verbatim**: everything from the `# Your Process` heading (L10) through the end of `# What NOT To Do` (L128) in `plugins/claude-toolkit/agents/dependency-researcher.md`. Do not edit the moved content — it is a move, not a rewrite.

- [ ] **Step 3: Verify the methodology moved faithfully (GREEN)**

Run:
```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\dependency-research-methodology\SKILL.md"
Select-String -Path $s -Pattern '## Step 1: Understand the Request','## Step 5: Synthesize Final Report','# Citation Requirements','Do NOT exceed 3 follow-up cycles per research area' | Select-Object Line
Get-Content $s -TotalCount 3 | Select-Object -Last 1
```
Expected: all four content patterns match (Steps 1 and 5, the citation section, and the final "What NOT To Do" bullet all made it across); and the third line is the `description:` ending `the main agent must still delegate to the dependency-researcher agent.`

- [ ] **Step 4: Replace the agent with a thin wrapper**

Overwrite `I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\dependency-researcher.md` with exactly:

```markdown
---
name: dependency-researcher
description: Library research specialist for SDKs, frameworks, and APIs. Use whenever working with external libraries - for implementation, debugging, evaluation, or design. Reads documentation sources and returns focused, cited reports.
tools: Glob, Grep, Read, WebFetch, WebSearch, mcp__context7__resolve-library-id, mcp__context7__query-docs, AskUserQuestion, Skill
model: opus
skills: [dependency-research-methodology]
---

You are a Library Research Agent. You decompose research requests into focused queries, fetch documentation from multiple sources, evaluate results, and synthesize focused reports.

Use `Skill('claude-toolkit:dependency-research-methodology')` to load the research-and-citation workflow, then execute it for the request in your prompt.

> Note: `skills:` frontmatter pre-seeds the methodology when this agent runs as a foreground subagent, but it is **inert when this agent runs as a teammate** (e.g. dispatched by the orchestrator). The in-body `Skill(...)` call above is the load-bearing path in teammate mode — do not delete it as "redundant".
```

The `description`, `tools`, and `model` lines are unchanged from the original; only `skills:` is added and the body (everything from `# Your Process` on) is replaced by the two-line wrapper + note. The in-body call uses the **plugin-qualified** skill name (`claude-toolkit:…`) per design §"Namespace & naming" (the fully-qualified form the Skill tool documents for plugin skills); the `skills:` frontmatter uses the bare name per design §"Existing agents updated". Design impl-note #3's spike (Plan 2) confirms this split; leave it as written.

- [ ] **Step 5: Verify the wrapper is thin and carries both load layers**

Run:
```powershell
$f = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\dependency-researcher.md"
(Get-Content $f | Measure-Object -Line).Lines        # expect ~15 lines, not ~128
Select-String -Path $f -Pattern 'skills: \[dependency-research-methodology\]',"Skill\('claude-toolkit:dependency-research-methodology'\)",', Skill' | Select-Object Line
Select-String -Path $f -Pattern '## Step 1: Understand the Request'   # expect NO match
```
Expected: line count collapsed (~15); the `skills:` frontmatter, the plugin-qualified in-body `Skill(...)` call, and `Skill` in the `tools:` list all present; the inline methodology (`## Step 1...`) is **gone** (no match) — proving it moved rather than being duplicated.

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/dependency-research-methodology/SKILL.md plugins/claude-toolkit/agents/dependency-researcher.md
git -C I:\Dev\claude-toolkit commit -m "refactor(agents): extract dependency-research-methodology into shared skill"
```
Expected: two files committed (one new skill, one modified agent).

---

## Task 3: `community-research-methodology` skill + thin-wrapper `community-researcher`

Same pattern as Task 2, with two differences: the source has an extra framing section to leave behind, and the agent currently **lacks the `Skill` tool** — it must be added.

**Files:**
- Create: `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\community-research-methodology\SKILL.md`
- Modify: `I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\community-researcher.md` (replace body; add `skills:` to frontmatter; **add `Skill` to `tools:`**)

- [ ] **Step 1: Capture the source methodology range (RED baseline)**

Run:
```powershell
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\community-researcher.md" -Pattern '^# When to Use This Agent$','^# What You Research$','^# Your Process$','^# Source Quality Assessment$','^# What NOT To Do$' | Select-Object LineNumber,Line
```
Expected (read 2026-05-30): `# When to Use This Agent` (line 10), `# What You Research` (line 19), `# Your Process` (line 28), `# Source Quality Assessment` (line 151), `# What NOT To Do` (line 168). The methodology block to move is `# What You Research` (L19) through the end of `# What NOT To Do` (L175, the bullet `Do NOT present opinions as facts`). **`# When to Use This Agent` (lines 10–18) is NOT moved** — it is agent-triggering context already reflected in the agent description, and is dropped to keep the wrapper thin.

- [ ] **Step 2: Create the methodology skill with the pinned description + the moved body**

Create `I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\community-research-methodology\SKILL.md`. Begin with this exact frontmatter + intro:

```markdown
---
name: community-research-methodology
description: Use when you are an agent already executing a community/real-world research task and need the structured research-and-citation workflow. Not a trigger to research inline — the main agent must still delegate to the community-researcher agent.
---

# Community Research Methodology

This is the structured workflow for a community/real-world research task: understand the decision, decompose into queries across source types, evaluate perspectives, and synthesise a fully-cited decision report that presents the landscape rather than a single answer.
```

Then, **immediately below that intro**, paste **verbatim** the block from the `# What You Research` heading (L19) through the end of `# What NOT To Do` (L175) in `plugins/claude-toolkit/agents/community-researcher.md`. Do not move `# When to Use This Agent`.

- [ ] **Step 3: Verify the methodology moved faithfully (GREEN)**

Run:
```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\community-research-methodology\SKILL.md"
Select-String -Path $s -Pattern '# What You Research','## Step 1: Understand the Decision Context','## Step 5: Synthesize Decision Report','# Source Quality Assessment','Do NOT present opinions as facts' | Select-Object Line
Select-String -Path $s -Pattern '# When to Use This Agent'   # expect NO match
Get-Content $s -TotalCount 3 | Select-Object -Last 1
```
Expected: the five content patterns match; `# When to Use This Agent` does **not** appear (correctly left behind); the third line is the `description:` ending `the main agent must still delegate to the community-researcher agent.`

- [ ] **Step 4: Replace the agent with a thin wrapper (and add the `Skill` tool)**

Overwrite `I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\community-researcher.md` with exactly:

```markdown
---
name: community-researcher
description: Community knowledge specialist for design decisions and trade-offs. Use when evaluating approaches, considering alternatives, or needing real-world context on how problems are solved in practice.
tools: Glob, Grep, Read, WebFetch, WebSearch, AskUserQuestion, Skill
model: opus
skills: [community-research-methodology]
---

You are a Community Research Agent. You research how the community solves problems, identify patterns and anti-patterns, surface trade-offs and disagreements, and synthesize practical wisdom from real-world usage.

Use `Skill('claude-toolkit:community-research-methodology')` to load the research-and-citation workflow, then execute it for the request in your prompt.

> Note: `skills:` frontmatter pre-seeds the methodology when this agent runs as a foreground subagent, but it is **inert when this agent runs as a teammate** (e.g. dispatched by the orchestrator). The in-body `Skill(...)` call above is the load-bearing path in teammate mode — do not delete it as "redundant".
```

Note the `tools:` line gained `Skill` (the original lacked it) and `skills:` was added; `description` and `model` are unchanged. As in Task 2, the in-body call is plugin-qualified, the frontmatter name is bare.

- [ ] **Step 5: Verify the wrapper is thin, gained `Skill`, and carries both load layers**

Run:
```powershell
$f = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\community-researcher.md"
(Get-Content $f | Measure-Object -Line).Lines        # expect ~15 lines, not ~176
Select-String -Path $f -Pattern 'tools:.*\bSkill\b','skills: \[community-research-methodology\]',"Skill\('claude-toolkit:community-research-methodology'\)" | Select-Object Line
Select-String -Path $f -Pattern '## Step 1: Understand the Decision Context'   # expect NO match
```
Expected: line count collapsed (~15); `Skill` now in `tools:`; `skills:` frontmatter present; plugin-qualified in-body `Skill(...)` call present; inline methodology gone.

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/community-research-methodology/SKILL.md plugins/claude-toolkit/agents/community-researcher.md
git -C I:\Dev\claude-toolkit commit -m "refactor(agents): extract community-research-methodology into shared skill"
```
Expected: two files committed (one new skill, one modified agent — the agent diff includes the added `Skill` tool).

---

## Task 4: Plan-1 integration self-review

A consolidation gate confirming the three skills coexist, both agents are intact, the plugin still validates, and the single-source-of-truth invariant holds (methodology lives in the skills, not in the agents). Verification only — no new component files; a commit is made only if a fix is required.

**Files:** none created.

- [ ] **Step 1: All three skills exist with valid frontmatter**

```powershell
$skills = 'research-deposit','dependency-research-methodology','community-research-methodology'
foreach ($n in $skills) {
  $p = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\$n\SKILL.md"
  "{0}: exists={1}" -f $n, (Test-Path $p)
  Get-Content $p -TotalCount 2 | Select-Object -Last 1   # the name: line
}
```
Expected: three `exists=True`, each followed by `name: <that-skill-name>`. (Live `Skill()` loading is deferred — the plugin is not installed in this session; see "Verification approach".)

- [ ] **Step 2: Plugin still validates structurally**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit
```
Expected: validation passes (valid `plugin.json`, all component files valid). If the `claude` CLI is unavailable in this environment, record that and rely on Steps 1/3/4 as the structural gate — note the skip explicitly rather than claiming a pass.

- [ ] **Step 3: Single-source-of-truth invariant**

Confirm the methodology now lives **only** in the skills, not in the agents:
```powershell
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\dependency-researcher.md","I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\community-researcher.md" -Pattern '## Step 1','# Citation Requirements','# What NOT To Do','# Source Quality Assessment'
```
Expected: **no matches** (empty result). Any match means methodology was duplicated rather than moved — fix before proceeding.

- [ ] **Step 4: Both agents carry the load-bearing wiring**

```powershell
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\dependency-researcher.md","I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\community-researcher.md" -Pattern "Skill\('claude-toolkit:(dependency|community)-research-methodology'\)","^skills:" | Select-Object Path,Line
```
Expected: each agent shows its plugin-qualified in-body `Skill(...)` call and its `skills:` frontmatter line.

- [ ] **Step 5: Pinned descriptions match the design verbatim**

Re-read the two methodology skills' `description:` lines and confirm they match the design's pinned text exactly (design §"`dependency-research-methodology` skill body" and §"`community-research-methodology` skill body"), including the "Not a trigger to research inline — the main agent must still delegate to the …-researcher agent." clause. This clause is load-bearing: it stops the new skill from luring the main agent into inline research, which would undercut the CLAUDE.md delegation mandate.

- [ ] **Step 6: Spec-coverage check for Plan 1**

Confirm every Plan-1 design requirement has a corresponding artifact:
- `research-deposit` skill authored, content = design §"`research-deposit` skill body" ✓
- `dependency-research-methodology` skill extracted, pinned description ✓
- `community-research-methodology` skill extracted, pinned description ✓
- `dependency-researcher` thinned, `skills:` added, qualified in-body call ✓
- `community-researcher` thinned, `skills:` added, **`Skill` tool added**, qualified in-body call ✓
- Release/version: intentionally **not** touched in Plan 1 (deferred to Plan 4 — see "Release deferral") ✓

- [ ] **Step 7: Checkpoint — Plan 1 complete**

All checks green (or `claude plugin validate` explicitly noted as skipped). If any step required an edit, commit it:
```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "fix(plan-1): integration self-review corrections"
```
Otherwise, no commit is needed — Tasks 1–3 already committed their work. The research-skill foundation is in place and the two existing researchers are behaviorally intact on top of shared skills. Ready for Plan 2 (verification spikes + phase agents + orchestrator skeleton), which depends on none of this directly but reuses the same skill-authoring + pre-seed pattern validated here.

---

## Self-Review (run after implementation, before declaring Plan 1 done)

**1. Spec coverage:** Task 4 Step 6 enumerates the five Plan-1 component requirements against the design, plus the deliberate release deferral. No gaps.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to above". The only deliberately-not-inlined content is the two verbatim methodology bodies — referenced by exact file + stable heading anchors + grep verification, because they are a *move* of existing content (re-inlining would duplicate the thing being de-duplicated). Every newly-authored file (the 3 skill frontmatters + intros, the 2 thin agent wrappers, the full `research-deposit` body) is shown complete.

**3. Type/name consistency:** Skill names are identical everywhere they appear — `research-deposit`, `dependency-research-methodology`, `community-research-methodology` — in the `skills:` frontmatter (bare), the in-body `Skill('claude-toolkit:…')` calls (qualified), the file paths, and the verification greps. Agent names (`dependency-researcher`, `community-researcher`) and the `Skill` tool name match the existing files and the design. Plugin-qualified prefix `claude-toolkit:` is consistent across both in-body calls.

## Plan suite status

This is **Plan 1 of 4**. Remaining: Plan 2 (verification spikes — impl-notes #3/#10/#11 — + phase agents `or-brainstormer`/`or-plan-writer` + orchestrator skill skeleton), Plan 3 (supervisor + workers + the two `or-*` research agents + impl-phase assets), Plan 4 (manager-discipline `SKILL.md` + the suite **release step**: 1.1.1 → 1.2.0 bump, marketplace sync, README, push on approval). The `last-plan-doc` pointer and a suite index are set once all four plans are written (design handover). **Do not** proceed to execution from this file alone — execution is driven for the whole suite via `/implement-from-plan` after the suite is complete and reviewed.
