# `or-superpowers-at-scale` — Review & Remediation (1.4.0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The `SKILL.md`/playbook/agent-authoring tasks are also governed by **superpowers:writing-skills** — load it before authoring. The final integration task is governed by **superpowers:finishing-a-development-branch**.

**Goal:** Land the consolidated remediation of the 11 review findings (Items 0–10) for the `claude-toolkit:or-superpowers-at-scale` skill — a foundational restructure (lean `SKILL.md` + new manager-only playbook + `spawn-protocol.md` as the sole SPAWN source), a new Phase 4 "Ship" finisher tier, and the doc/code fixes — shipping as plugin `1.3.0 → 1.4.0`, with the three deferred-to-verify items (worktree binding, auto-compaction, empty-idle-turn) landing as design + tracked TODOs + behavioral spikes executed at live-install cutover.

**Architecture:** The oversized `SKILL.md` is split into a lean shared entry point (overview + Core Principle headline + When/When-not + Topology + Phase flow + an asset Map whose first line tells the *manager* to read the playbook) and a new manager-only `assets/manager-playbook.md` (the full operating discipline — moved verbatim from `SKILL.md`, then edited in place). `assets/spawn-protocol.md` becomes the single source of the SPAWN / SPAWN_RESEARCH mechanics (Item 5 de-dup); the playbook keeps only the canonical SHUTDOWN handshake + trigger pointers. A new user-facing `or-finisher` agent (pre-seeded `superpowers:finishing-a-development-branch`) runs Phase 4 in direct dialogue and signals `SHIP_COMPLETE`. The three deferred items land as harness-native `EnterWorktree` bind directives, a compaction-config requirement, and explicit "load-bearing & unverified" notes — each co-located with a TODO pointing at a new behavioral spike.

**Tech Stack:** Claude Code plugin components in the `claude-toolkit` plugin repo (`I:\Dev\claude-toolkit`, real git) — Markdown `SKILL.md` + `assets/*.md` + `agents/*.md`, JSON manifests, and a Markdown validation doc. No compiled code. In-session verification is **structural** (`claude plugin validate` + content greps + JSON-shape checks); all **behavioral** validation is deferred to suite cutover against the *installed* plugin. Per-task `git -C I:\Dev\claude-toolkit commit` is the rollback boundary.

---

## Scope of this plan

Source design (authoritative): `docs/superpowers/specs/2026-05-31-or-sas-review-remediation-design.md`. This plan implements its Sections 2–6.

**In scope (lands on the feature branch):**
- **Restructure / spine (Item 5):** create `assets/manager-playbook.md`; lean-rewrite `SKILL.md`; make `assets/spawn-protocol.md` the sole SPAWN/SPAWN_RESEARCH copy. (Tasks 1–3)
- **Playbook-side item fixes (Items 0, 4, 6, 8, 9):** Input subsection, allowlist restructure, PHASE_ABORT mechanical handling, PHASE_PAUSE collapse, orphaned-worker reaping, compaction/empty-idle notes, backtick fixes. (Tasks 4–8)
- **Item 2 — Phase 4 Ship:** new `or-finisher` agent + `finisher-spawn-context.md` asset + `SHIP_COMPLETE` token + topology/idle/status/handover wiring + `manager-handover-template.md` `ship` enum. (Tasks 9–11)
- **Supervisor fixes (Items 3, 7, 6):** Adaptations & override block; structured PHASE_PAUSE + narrowed Phase-3 triggers. (Task 12)
- **Item 1 — worktree binding (deferred-design):** `Worktree:` in spawn-contexts; `EnterWorktree` tool grant + bind directive on every repo-touching tier; preflight creates the worktree under `.claude/worktrees/`. Plus Item 4a phase-agent abort confirm, Item 9.2 researcher-naming note, Item 9.5 F7 note. (Tasks 13–16)
- **Item 8a — compaction (deferred-design):** preflight check/warn + playbook requirement note. (folded into Tasks 8, 16)
- **Item 10 — spikes:** add the worktree-binding + empty-idle-turn spikes; update the cutover checklist. (Task 17)
- **Item 0 cleanup + release:** delete the wrapper command; README; version bump `1.3.0 → 1.4.0`. (Tasks 18–20)
- **Self-review + structural validation + approval-gated finish.** (Tasks 21–22)

**Out of scope (suite cutover — post-release, against the installed plugin):**
- **Execution** of any behavioral spike (Spikes 1–7 in `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`). Items 1, 8, 10 are **not "done"** until their spikes pass at cutover; this plan only lands their design + TODOs + the spike definitions.
- Removing deprecated loose `~/.claude` copies (already done 2026-05-31 per the spikes doc cutover checklist) and `claude plugin install claude-toolkit`.

## Git workflow (READ FIRST)

`I:\Dev\claude-toolkit` **is a real git repository**. All work happens on a new feature branch **`or-sas-review-remediation`** off `master`, **one commit per task** (matches the suite's established workflow; design §6).

- The session working directory is a different drive from the repo. **Every git command targets the repo explicitly via `git -C I:\Dev\claude-toolkit …`** — do not rely on ambient cwd, and do not `cd` (it can trigger a permission prompt).
- **Task 0 (do once, before Task 1):** `git -C I:\Dev\claude-toolkit checkout master; git -C I:\Dev\claude-toolkit pull --ff-only; git -C I:\Dev\claude-toolkit checkout -b or-sas-review-remediation`. (Also `git -C I:\Dev\claude-toolkit add docs/superpowers/plans/2026-06-01-or-sas-review-remediation.md && git -C I:\Dev\claude-toolkit commit -m "docs(plan): or-sas review remediation implementation plan"` so the plan itself is tracked.)
- Tasks 1–21 commit locally only. **Do NOT `git push` until Task 22**, and only after **explicit user approval** (Task 22 runs `finishing-a-development-branch`).
- A worktree is **not** required for this doc-edit plan (the suite's prior plans worked the branch directly). If the executor prefers isolation, create one via `superpowers:using-git-worktrees` first; nothing in the tasks below assumes a worktree.

## Verification approach (structural in-session; behavioral at cutover)

The `claude-toolkit` marketplace is **not installed in the authoring/execution session**, so `Skill('claude-toolkit:or-superpowers-at-scale')` will not resolve the files being edited and the `claude-toolkit:or-*` subagent types are not registered. **Hard gates are therefore structural** — `claude plugin validate` (or the `plugin-validator` agent) + content greps (`Select-String`) + JSON-shape checks. **Every behavioral check is deferred** to cutover (Spikes 1–7). If `claude` is unavailable in-session, record the skip explicitly and rely on greps — never claim a `validate` pass that did not run.

Verification idiom (PowerShell, matching the suite's prior plans): `Test-Path`, `Select-String -Pattern '<regex>'` (expect match / no-match), and `(Get-Content $f | Measure-Object -Word).Words` for word-count soft-checks. Checks are **content-based, not line-number-based**, so they survive the edits that shift line numbers.

## File structure (decomposition map)

| File | Disposition | Responsibility after this plan |
|------|-------------|--------------------------------|
| `skills/or-superpowers-at-scale/SKILL.md` | rewrite (lean) | Shared entry point every tier loads: overview, When/not, Topology (+`or-finisher`), Phase flow (0–4), Integration, condensed Core Principle, and the asset **Map** (first line = manager-read-the-playbook imperative). |
| `…/assets/manager-playbook.md` | **create** | The manager's complete operating manual (moved from `SKILL.md` + the Item 0/4/6/8/9 fixes + Phase-4 wiring). Loaded only by the manager. |
| `…/assets/spawn-protocol.md` | unchanged (verified sole copy) | The single source of SPAWN + SPAWN_RESEARCH mechanics (Item 5 de-dup target). |
| `…/assets/manager-handover-template.md` | edit | `active_phase` enum gains `ship`; `active_phase_agent` gains `or-finisher-<N>`. |
| `…/assets/finisher-spawn-context.md` | **create** | Per-spawn variables for `or-finisher` (identity / worktree / branch / base / handover dir / plan / latest iteration doc). |
| `…/assets/{supervisor,implementer,reviewer}-spawn-context.md` | edit | Add `Worktree: <WORKTREE_PATH>` (Item 1). |
| `…/assets/preflight-brief.md` | edit | Create the worktree under `.claude/worktrees/<name>` (Item 1); optional compaction check/warn (Item 8a). |
| `agents/or-finisher.md` | **create** | Phase-4 ship teammate (pre-seed `finishing-a-development-branch`; `EnterWorktree`-bound; `SHIP_COMPLETE` terminal). |
| `agents/or-supervisor.md` | edit | Adaptations & override (Items 3, 7); structured PHASE_PAUSE + narrowed triggers (Item 6); `EnterWorktree` bind (Item 1). |
| `agents/or-brainstormer.md`, `agents/or-plan-writer.md` | edit | Phase-agent-owned abort confirm (Item 4a); `EnterWorktree` bind (Item 1); researcher-naming note (Item 9.2). |
| `agents/or-implementer.md`, `agents/or-spec-reviewer.md`, `agents/or-code-quality-reviewer.md`, `agents/or-final-reviewer.md` | edit | `EnterWorktree` bind directive + tool grant (Item 1); F7 note (Item 9.5). |
| `docs/superpowers/validation/2026-05-30-…-behavioral-spikes.md` | edit | Add Spike 6 (worktree binding) + Spike 7 (empty idle turn); update cutover checklist (Items 1, 8b, 10). |
| `README.md` | edit | Remove the command bullet; update the skill bullet; fix Dependencies; add `or-finisher` to the agent listing (Item 0). |
| `plugins/claude-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | edit | Version `1.3.0 → 1.4.0` (×3). |
| `plugins/claude-toolkit/commands/or-superpowers-at-scale.md` | **delete** | Wrapper command removed — the skill is now `user_invocable` (Item 0). |

## Deviations from the design's §5 manifest (explicit, reviewable)

1. **`EnterWorktree` tool grant (frontmatter).** Item 1's "every repo-touching tier calls `EnterWorktree(<path>)`" directive is **inert unless the tool is granted**; §5 lists only body + spawn-context edits. This plan adds `EnterWorktree` to the `tools:` frontmatter of all repo-touching agents (supervisor, 4 workers, 2 phase agents, finisher) and folds "is `EnterWorktree` grantable to a teammate **and** does it bind a *shared* worktree" into Spike 6's scope. (Necessary consequence, made explicit.)
2. **`manager-handover-template.md` `ship` enum.** §5 omits this file, but Phase 4 (Item 2) means a manager can cross 200k mid-ship; its `active_phase` enum + the resume prose must include `ship`/`or-finisher` or a fresh manager cannot resume Phase 4. Edited in Task 11. (Latent-bug gap closed.)
3. **README also lists `or-finisher`.** §5's README edit covers Item 0; this plan additionally adds the new `or-finisher` agent to the README agent listing (plugin hygiene per `updating-plugin`). Task 19.
4. **Supervisor "drop the finishing claim" (Item 2) is a no-op.** §5 says `or-supervisor.md` drops the finishing claim, but the supervisor body contains none — the only `finishing-a-development-branch` claim in the skill is `SKILL.md:54` (verified by grep). Task 12 grep-confirms absence and makes no supervisor edit for Item 2.
5. **No `finisher-handover-template.md` (YAGNI).** The design left this "confirm during planning." Decision: not bundled — the ship step is far too short to reach 150k; if it ever does, a fresh `or-finisher` re-runs `finishing-a-development-branch` (which idempotently re-assesses branch state). The Handover Ladder row documents this.

---

## Task 1: Create `assets/manager-playbook.md` (move + Item 5 de-dup)

Create the manager's operating manual by **moving** the manager-only sections out of the current `SKILL.md` **verbatim**, applying exactly **one** transformation during the move — the Item 5 Broker-Protocols de-dup. No other item-fixes here (they land in Tasks 4–8/11). `SKILL.md` is trimmed to its lean form in Task 2, so between this commit and Task 2 the moved content is briefly duplicated — that is expected and resolved by Task 2's GREEN.

**Files:**
- Create: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`
- Read (source, do not edit here): `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md`

- [ ] **Step 1: Load authoring discipline + read the source**

Invoke `Skill('superpowers:writing-skills')` and skim it (assets are skill content for the loading model — here the manager; no placeholders/forward-stubs). Then Read the current `SKILL.md` end-to-end — it is the move source.

- [ ] **Step 2: Confirm the playbook does not yet exist (RED)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Test-Path $pb    # expect False
```

- [ ] **Step 3: Create `manager-playbook.md` — title + intro, then the moved sections in this order**

Write this title/intro at the top:

````markdown
# or-superpowers-at-scale — Manager Playbook

Your complete operating manual as the **manager** (the parent Claude in the main chat) of an `or-superpowers-at-scale` run. The skill's `SKILL.md` is the shared overview every tier loads; **THIS file is yours alone** — Read it in full before any spawn, message, or other action. Teammates do not load it (that is the point: only you pay for it).

You arrived here from `SKILL.md`'s Map. Everything below — the Preservation Imperative, Mode Detection, Initial Setup, the broker protocols, the idle taxonomy, the communication discipline, the conservation rules, the handover ladder, recovery, and red flags — is the manager's job and nobody else's.
````

Then append these sections, **copied verbatim from the current `SKILL.md`** (by heading), in this exact order, EXCEPT where a transform is noted:

1. `## Operating Principle (the Preservation Imperative)` — move the current `### The Preservation Imperative` subsection **plus** the four `**The phase agent exists…**`/`…supervisor…`/`…handover doc…`/`…worker…` lines (current `SKILL.md` "The Preservation Imperative" through "…context doesn't have to accumulate."). Re-level the heading from `###` to `##`. (Its parent `## Core Principle` headline stays in `SKILL.md`, condensed — Task 2.)
2. `## Mode Detection` — verbatim (the whole current section incl. the table and the `PREFLIGHT_OK` block).
3. `## Initial Setup (first manager turn)` — verbatim (Input subsection + backtick fix land in Task 4).
4. `## Manager Broker Protocols` — **TRANSFORMED (Item 5 de-dup):** replace the whole section body with the text in Step 4 below. This removes the duplicated SPAWN/SPAWN_RESEARCH message-format blocks + the `ROLE → subagent_type` table + the SPAWN_RESEARCH case table (now sole-sourced in `spawn-protocol.md`), keeping only the manager-only rules + the **canonical SHUTDOWN** handshake.
5. `## Phase Transitions & Idle Taxonomy` — verbatim (edits in Tasks 5, 6, 11).
6. `## Proactive Status Reporting (all tiers)` — verbatim (edit in Task 11).
7. `## Required Communication Style (HARD RULE)` — verbatim (allowlist replaced in Task 5).
8. `## Conservation Rules` — verbatim.
9. `## Handover Ladder` — verbatim (edits in Tasks 8, 11).
10. `## Recovery from Common Gotchas` — verbatim (edit in Task 7).
11. `## Red Flags` — verbatim.

- [ ] **Step 4: Use this EXACT text for the transformed `## Manager Broker Protocols` section**

````markdown
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
````

- [ ] **Step 5: Verify the move + de-dup (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Test-Path $pb    # expect True
# all 11 moved section headings present:
Select-String -Path $pb -Pattern '^## Operating Principle','^## Mode Detection$','^## Initial Setup','^## Manager Broker Protocols$','^## Phase Transitions','^## Proactive Status Reporting','^## Required Communication Style','^## Conservation Rules$','^## Handover Ladder$','^## Recovery from Common Gotchas$','^## Red Flags$' | Measure-Object   # expect Count = 11
# canonical SHUTDOWN lives here:
Select-String -Path $pb -Pattern 'type: "shutdown_request"'   # expect 1 match
# de-dup: the full SPAWN/SPAWN_RESEARCH tables are NOT duplicated into the playbook:
Select-String -Path $pb -Pattern '^\| ROLE \| subagent_type \|','SPAWN message format \(exact\)'   # expect NO match (those live only in spawn-protocol.md)
```

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "refactor(or-sas): extract manager-playbook.md; de-dup SPAWN into spawn-protocol.md (Item 5)"
```

---

## Task 2: Lean-rewrite `SKILL.md` to final state

Replace `SKILL.md` with the lean shared entry point. This is a full-file Write (no line-number fragility). It folds in every `SKILL.md`-resident item-fix: Item 0 `user_invocable`; Item 2 topology `or-finisher` row + Phase 0–4 flow + Integration correction; Item 9.4 `or-` prefix expansion; and the Item 5 Map imperative. The moved sections (now in the playbook) are absent.

**Files:**
- Modify (full replace): `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md`

- [ ] **Step 1: Confirm the moved sections still exist in `SKILL.md` (pre-state)**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
Select-String -Path $s -Pattern '^## Manager Broker Protocols$','^## Conservation Rules$'   # expect matches (about to be removed)
(Get-Content $s | Measure-Object -Word).Words   # record W0 (will drop sharply)
```

- [ ] **Step 2: Replace the entire file with this exact content**

````markdown
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
````

- [ ] **Step 3: Verify the lean rewrite (GREEN)**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
# Item 0 / Item 2 / Item 9.4 / Item 5 markers present:
Select-String -Path $s -Pattern 'user_invocable: true','or-finisher-N','brainstorm → plan → implement → ship','= \*orchestrator\*','Phase 4 — Ship','Read it in full now'   # expect all matched
# moved sections are GONE from SKILL.md:
Select-String -Path $s -Pattern '^## Manager Broker Protocols$','^## Conservation Rules$','^## Mode Detection$','^## Initial Setup','^## Required Communication Style'   # expect NO match
# the false finishing claim is corrected (no "supervisor invokes it"):
Select-String -Path $s -Pattern 'the supervisor invokes it after the final iteration'   # expect NO match
# leanness soft-check:
(Get-Content $s | Measure-Object -Word).Words   # expect well under W0 (target ~700–900)
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md
git -C I:\Dev\claude-toolkit commit -m "refactor(or-sas): lean SKILL.md entry point; fold in user_invocable + Phase-4 topology + or- prefix (Items 0,2,5,9.4)"
```

---

## Task 3: Spine verification (no content lost; cross-refs resolve; de-dup complete)

A pure verification + reconciliation task (no edits unless a check fails). Confirms the restructure preserved every section in exactly one home and that the de-dup is complete.

**Files:** none modified (verification only; if a check fails, fix in the relevant file and re-run before committing nothing — this task has no commit unless a fix was needed).

- [ ] **Step 1: Every old `SKILL.md` section now lives in exactly one of {SKILL.md, manager-playbook.md}**

```powershell
$dir = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale"
$s = "$dir\SKILL.md"; $pb = "$dir\assets\manager-playbook.md"
# kept in SKILL.md:
Select-String -Path $s -Pattern '^## When to Use$','^## Architecture$','^## Integration with Other Skills$','^## Core Principle','^## Map'   # expect matches
# moved to playbook:
Select-String -Path $pb -Pattern '^## Operating Principle','^## Mode Detection$','^## Initial Setup','^## Manager Broker Protocols$','^## Phase Transitions','^## Proactive Status Reporting','^## Required Communication Style','^## Conservation Rules$','^## Handover Ladder$','^## Recovery from Common Gotchas$','^## Red Flags$'   # expect matches
```

- [ ] **Step 2: SPAWN/SPAWN_RESEARCH full mechanics are sole-sourced in `spawn-protocol.md`**

```powershell
$dir = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
# the canonical role table + exact-format block exist ONLY in spawn-protocol.md:
Select-String -Path "$dir\spawn-protocol.md" -Pattern 'SPAWN message format \(exact\)','^\| ROLE \| subagent_type \|'   # expect matches
Select-String -Path "$dir\manager-playbook.md" -Pattern 'SPAWN message format \(exact\)','^\| ROLE \| subagent_type \|'   # expect NO match
# canonical SHUTDOWN exists ONLY in the playbook (not spawn-protocol.md):
Select-String -Path "$dir\manager-playbook.md" -Pattern 'type: "shutdown_request"'   # expect 1 match
Select-String -Path "$dir\spawn-protocol.md" -Pattern 'type: "shutdown_request"'      # expect NO match
```

- [ ] **Step 3: The manager-read-the-playbook imperative resolves**

```powershell
$s = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
Select-String -Path $s -Pattern 'assets/manager-playbook\.md'   # expect match (Map points at it)
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"   # expect True
```

- [ ] **Step 4: If any check failed, fix in-place and commit; otherwise no commit (spine already committed in Tasks 1–2)**

```powershell
# only if a reconciliation edit was needed:
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): reconcile restructure (spine verification)"
```

---

## Task 4: Item 0 — `Input` subsection + Item 9.3 backtick fix (playbook Initial Setup)

Add the explicit Input subsection to the playbook's `## Initial Setup` (now that the skill is `user_invocable`, the `/`-args must be defined where the manager consumes them), and fix the broken backtick spans in the three first-session messages.

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Confirm the broken backticks and the missing Input subsection (RED)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'on team `<name>`\. `'   # expect 3 matches (broken span: backtick before <name> closes the code span early)
Select-String -Path $pb -Pattern '^### Input'             # expect NO match
```

- [ ] **Step 2: Insert the Input subsection immediately under `## Initial Setup (first manager turn)`** (before its numbered step 1)

````markdown
### Input (the skill's invocation arguments)

This skill is **user-invocable** (`/or-superpowers-at-scale [<idea> | <spec-path> | <plan-path>]`). Two values seed preflight:

- **`<USER_INPUT>`** — the invocation argument: an **idea statement**, a **spec path** (`docs/superpowers/specs/*-design.md`), a **plan path** (`docs/superpowers/plans/*.md`), or **empty**. You do NOT classify it — you pass it verbatim into `preflight-brief.md`; preflight detects the mode (and asks the user if it is ambiguous).
- **`<USER_CONSENT>`** — whether the user has pre-authorised working on `main`/`master`. **Default `"no"`** unless the user explicitly said otherwise. Passed into `preflight-brief.md`; preflight FAILs a default-branch base without consent.

Substitute both into `preflight-brief.md` at step 1 below.
````

- [ ] **Step 3: Fix the three first-session messages** — rewrite each so `<name>` sits inside one clean code span (replace the placeholder with `<TEAM>` and close the span correctly). Replace the three message lines so each reads as a single backticked span, e.g.:

````markdown
   - `idea`: `Spawned or-brainstormer-1 (opus, background) on team <TEAM>. Talk to it directly — switch with Shift+Down. It's driving Phase 1.`
   - `spec`: `Spawned or-plan-writer-1 (opus, background) on team <TEAM>. Talk to it directly — switch with Shift+Down. It's driving Phase 2.`
   - `plan`: `Spawned or-supervisor-1 (opus, background) on team <TEAM>. Standing by.`
````

- [ ] **Step 4: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern '^### Input \(the skill''s invocation arguments\)','<USER_INPUT>','Default `"no"`'   # expect matches
Select-String -Path $pb -Pattern 'on team `<name>`\. `'   # expect NO match (broken span gone)
Select-String -Path $pb -Pattern 'on team <TEAM>\.'        # expect 3 matches (clean spans)
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): playbook Input subsection + first-session backtick fix (Items 0, 9.3)"
```

---

## Task 5: Item 4 — PHASE_ABORT mechanical handling + allowlist restructure (playbook)

Two halves of Item 4, both manager-side (the phase-agent half is Task 14). (a) PHASE_ABORT becomes purely mechanical for the manager (the confirm moved to the phase agent). (b) The flat "ONLY situations" output list becomes two explicit categories with cross-references.

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Confirm the pre-state (RED)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern "Confirm by typing 'exit'"              # expect match (old surfaced confirm)
Select-String -Path $pb -Pattern 'The ONLY situations that warrant manager text output'   # expect match (flat list)
```

- [ ] **Step 2 (Item 4a): Replace the PHASE_ABORT idle-taxonomy row** with the mechanical form:

````markdown
| Phase agent `PHASE_ABORT` | Action | **Mechanical** — shut the phase agent down and end the session cleanly. The user-facing confirm already happened in the phase agent's own dialogue (it emits `PHASE_ABORT` only post-confirmation); the manager surfaces nothing. |
````

If a standalone PHASE_ABORT paragraph exists below the table, delete its "surface a confirm prompt" wording (the row is now self-contained).

- [ ] **Step 3 (Item 4b): Replace the whole "The ONLY situations that warrant manager text output:" block** (down to, but not including, the "Forbidden in manager output:" line) with:

````markdown
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
````

- [ ] **Step 4: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern "Confirm by typing 'exit'"   # expect NO match
Select-String -Path $pb -Pattern 'PHASE_ABORT.*Mechanical'    # expect match
Select-String -Path $pb -Pattern 'Routine protocol replies','Sanctioned transition & lifecycle surfacings'   # expect both
Select-String -Path $pb -Pattern 'The ONLY situations that warrant'   # expect NO match
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): PHASE_ABORT mechanical + two-category output allowlist (Item 4)"
```

---

## Task 6: Item 6 — collapse `PHASE_PAUSE / PAUSE` to one `PHASE_PAUSE` (playbook)

The supervisor gains the structured `PHASE_PAUSE` token in Task 12; the manager handles it identically to the phase agents', so the idle-taxonomy row and PAUSE-relay prose collapse to the single token.

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Confirm the hedged wording (RED)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'PHASE_PAUSE` / PAUSE'   # expect match (hedged row)
```

- [ ] **Step 2: Edit the idle-taxonomy row** — change `Phase agent / supervisor `PHASE_PAUSE` / PAUSE` to `Phase agent / supervisor `PHASE_PAUSE`` (drop "/ PAUSE"); keep the action text ("Relay one short paragraph (action + impact); after approval reply `PROCEED` / `REJECTED — reason: <line>`").

- [ ] **Step 3: Edit the PAUSE-relay paragraph** — update its opening so the structured token is explicit and singular:

````markdown
**PAUSE relay.** Phase agents and the supervisor request a PAUSE with the **single structured `PHASE_PAUSE` token** (the same token across all depth-1 tiers — `action:` / `impact:` fields) for actions **beyond** the normal workflow: genuinely destructive or visible-to-others operations (a `git push` outside Phase 4, deleting files outside the worktree, an external API call). Relay one short paragraph (action + impact only — no commit lists, no narration). Local commits the underlying skills perform are NOT a pause case.
````

- [ ] **Step 4: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'PHASE_PAUSE` / PAUSE'        # expect NO match
Select-String -Path $pb -Pattern 'single structured `PHASE_PAUSE` token'   # expect match
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): collapse to single structured PHASE_PAUSE token (Item 6)"
```

---

## Task 7: Item 9.1 — orphaned-worker reaping on resume (playbook)

Extend the "Fresh manager resume" protocol so a fresh manager reaps **all** orphaned members (not just the active depth-1 tier) before spawning the successor.

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Confirm the pre-state (RED)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'enumerate \*all\* members|enumerate ALL members'   # expect NO match
```

- [ ] **Step 2: In the "Fresh manager resume" paragraph, insert the reaping step** before "spawn the `N+1` successor":

````markdown
**Reap orphans first.** Before spawning the successor, enumerate **ALL** members in `~/.claude/teams/<team>/config.json` — not just the active depth-1 tier — and issue `shutdown_request` to every orphaned teammate the interrupted session left alive (stale implementers, reviewers, researchers, a prior phase agent / supervisor / finisher). A fresh manager inherits no roster knowledge, so orphans left alive bloat it immediately.
````

Also extend the "Old phase agent / supervisor still alive on resume" Recovery bullet to read "**any** orphaned member (phase agent, supervisor, finisher, worker, researcher)".

- [ ] **Step 3: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'enumerate \*\*ALL\*\* members','Reap orphans first'   # expect matches
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): reap all orphaned members on fresh-manager resume (Item 9.1)"
```

---

## Task 8: Item 8 — compaction prerequisite + empty-idle-turn note (playbook, deferred-design)

Document the auto-compaction requirement (so every tier reaches its handover threshold before lossy compaction) and flag the empty-idle-turn behavior as load-bearing-and-unverified. Both carry a TODO pointing at their cutover spike (added in Task 17).

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Confirm the pre-state (RED)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'CLAUDE_AUTOCOMPACT_PCT_OVERRIDE','empty turn'   # expect NO match
```

- [ ] **Step 2 (Item 8a): Add a prerequisite note at the top of `## Handover Ladder`:**

````markdown
> **Prerequisite — auto-compaction (Item 8a; verification pending Spike 6/7 suite at cutover).** Auto-compaction fires at ~95% of the context window by default (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`). This is window-size-coupled: on a 1M-window model 95% ≈ 950k (well above these thresholds — safe); on a **200k-window** model 95% ≈ 190k, which would pre-empt the manager's 200k handover with lossy compaction. **Do not assume a 1M window.** Run the orchestration with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` set high (or disabled) so every tier reaches its handover threshold *first* (handover-not-compact, for all tiers). Preflight can check/warn (see `preflight-brief.md`).
````

- [ ] **Step 3 (Item 8b): Add an "unverified" note** near the Idle Taxonomy's "Idle wake-ups produce no output and no tool calls" statement:

````markdown
> **Load-bearing & unverified (Item 8b).** This silence-on-idle discipline assumes the harness gracefully accepts a turn with **no text and no tool call**. That is undocumented; it is verified by the empty-idle-turn spike at cutover (`docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`, Spike 7). Keep the intent, but if the spike fails the discipline needs rethinking. Do not delete this note until Spike 7 is GREEN.
````

- [ ] **Step 4: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'CLAUDE_AUTOCOMPACT_PCT_OVERRIDE','Do not assume a 1M window','Load-bearing & unverified \(Item 8b\)','Spike 7'   # expect matches
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): compaction prerequisite + empty-idle-turn unverified note (Item 8)"
```

---

## Task 9: Item 2 — create the `or-finisher` agent

New user-facing Phase-4 agent (symmetric with `or-plan-writer`): pre-seeds `superpowers:finishing-a-development-branch`, binds the worktree (Item 1), runs in direct dialogue, and signals `SHIP_COMPLETE`. Model it on `agents/or-plan-writer.md` structure.

**Files:**
- Create: `plugins/claude-toolkit/agents/or-finisher.md`

- [ ] **Step 1: Confirm it doesn't exist (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-finisher.md"   # expect False
```

- [ ] **Step 2: Create the file with this exact content**

````markdown
---
name: or-finisher
description: Phase-4 ship agent for the or-superpowers-at-scale orchestrator. The manager spawns this agent as a background teammate after the final iteration to run finishing-a-development-branch in a direct conversation with the user (merge / PR / cleanup) and signal completion. Not for standalone use — it signals SHIP_COMPLETE to the manager instead of ending on its own.
tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, Skill, SendMessage, EnterWorktree
model: opus
skills: [superpowers:finishing-a-development-branch]
---

# or-finisher — Phase-4 Operating Manual (`or-superpowers-at-scale`)

Operating manual for any finisher (`or-finisher-1`, `or-finisher-2`, ...) in the orchestrator
topology. Your per-spawn identity, worktree, branch, base branch, handover dir, plan path, and the
latest iteration doc arrive in your spawn context. Read this manual end-to-end before binding,
invoking any skill, or composing any message.

---

## STEP -1 — Bind to the worktree (REQUIRED, FIRST ACTION, before STEP 0)

Your spawn context names a `Worktree:` path. A spawned teammate inherits the manager's CWD (the main
checkout), NOT the worktree — so before reading any repo file, invoking any skill, or running git,
bind your session to the worktree:

    EnterWorktree(<WORKTREE_PATH>)

Then verify you landed in it:

    git rev-parse --show-toplevel   # must equal <WORKTREE_PATH>

If `EnterWorktree` is unavailable or the path does not match, STOP and SendMessage the manager
`BLOCKED — worktree bind failed: <detail>` rather than shipping from the wrong checkout.

> **Verification pending (Item 1 / Spike 6).** Whether `EnterWorktree(<path>)` binds a fresh
> background teammate into a *shared* team worktree is undocumented and is verified by the
> worktree-binding spike at cutover
> (`docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`). If the
> spike fails, this directive's mechanism changes (see the spike's fallback). Do not delete this note
> until Spike 6 is GREEN.

---

## STEP 0 — Invoke the canonical finishing skill (REQUIRED, after STEP -1)

Invoke:

    Skill("superpowers:finishing-a-development-branch")

_The `skills:` frontmatter is inert for teammates (which you are): teammates don't auto-load
frontmatter skills, so this in-body call is what actually loads the skill. Never skip it as "already
pre-seeded."_

**Then follow that skill verbatim** — present the structured completion options (merge / PR / cleanup)
and carry them out per the user's choice.

### Override — signal completion instead of simply closing

`finishing-a-development-branch` ends by completing the integration and treating the work as done. You
are user-facing (the user talks to you directly via teammate routing), so perform the merge / PR /
cleanup the user chooses **directly** — pushing and opening PRs is exactly your job in Phase 4, so no
PAUSE is needed for it. The single override: when the integration is complete, SendMessage the manager

    SHIP_COMPLETE — <one line: what was done, e.g. "merged to master" / "PR #123 opened">

then await `shutdown_request`. Do NOT end the session yourself; the manager ends it after
`SHIP_COMPLETE`.

---

## You are the user-facing tier

The user talks to you directly. The manager is silent during Phase 4 and does not relay your
conversation. Own the dialogue: surface the finishing options, get the user's choice, carry it out.

## Depth-1 Constraint

You have no `Agent` tool. The manager is the sole spawn-broker; attempting to use `Agent` will silently
fail. You do not need research — if you somehow do, that is a sign the plan was under-specified; raise
it to the user rather than spawning.

## Abort path

If the user makes clear they want to end the whole session without finishing, confirm directly first
("Ending now leaves the branch unmerged at `<branch>`. Confirm abort? (yes / no)"); only on "yes"
SendMessage the manager `PHASE_ABORT — reason: <one line>` and await `shutdown_request`.

## Finisher Handover (rare)

The ship step is short; crossing ~150k is near-impossible. No dedicated handover template is bundled.
If you ever approach it, finish the in-flight operation, SendMessage the manager
`FINISHER_HANDOVER — <one-line branch state>`, and await shutdown — a fresh `or-finisher-(N+1)`
re-runs `finishing-a-development-branch`, which idempotently re-assesses branch state.
````

- [ ] **Step 3: Verify (GREEN)**

```powershell
$f = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-finisher.md"
Test-Path $f   # expect True
Select-String -Path $f -Pattern 'name: or-finisher','EnterWorktree','skills: \[superpowers:finishing-a-development-branch\]','SHIP_COMPLETE','STEP -1 — Bind to the worktree'   # expect matches
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-finisher.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): add or-finisher Phase-4 ship agent (Item 2)"
```

---

## Task 10: Item 2 — create `finisher-spawn-context.md`

Per-spawn variable template the manager substitutes when spawning `or-finisher` (branch / base / worktree / plan / iteration-doc paths — design §3.2).

**Files:**
- Create: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/finisher-spawn-context.md`

- [ ] **Step 1: Confirm it doesn't exist (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\finisher-spawn-context.md"   # expect False
```

- [ ] **Step 2: Create the file with this exact content**

````markdown
Identity: <NAME> in team <TEAM>
Worktree: <WORKTREE_PATH>
Branch: <BRANCH>
Base branch: <BASE_BRANCH>
Handover dir: <HANDOVER_DIR>
Plan: <PLAN_PATH>
Latest iteration doc: <HANDOVER_DIR>/iteration-<N>.md
````

- [ ] **Step 3: Verify (GREEN)**

```powershell
$f = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\finisher-spawn-context.md"
Test-Path $f   # expect True
Select-String -Path $f -Pattern '^Worktree: <WORKTREE_PATH>$','^Base branch: <BASE_BRANCH>$','^Latest iteration doc:'   # expect matches
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/finisher-spawn-context.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): add finisher-spawn-context.md (Item 2)"
```

---

## Task 11: Item 2 — wire Phase 4 into the playbook + manager-handover template

Wire the `or-finisher` lifecycle into the playbook (idle taxonomy, status reporting, handover ladder, fresh-manager resume) and teach the manager-handover template the `ship` phase (deviation #2 — closing the §5 gap).

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-handover-template.md`

- [ ] **Step 1: Confirm the pre-state (RED)**

```powershell
$dir = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
Select-String -Path "$dir\manager-playbook.md" -Pattern 'SHIP_COMPLETE','or-finisher-1'   # expect NO match
Select-String -Path "$dir\manager-handover-template.md" -Pattern 'ship'   # expect NO match
```

- [ ] **Step 2: In the playbook idle-taxonomy table, split the supervisor COMPLETED row and add the SHIP_COMPLETE row.** Replace the single `Supervisor ITERATION N — STOPPED_FOR_HANDOVER / COMPLETED` row with:

````markdown
| Supervisor `ITERATION N — STOPPED_FOR_HANDOVER` | Action | Execute the iteration-handover protocol (spawn `or-supervisor-(N+1)` on the latest `iteration-N.md`) |
| Supervisor `ITERATION N — COMPLETED` | Action | Shut the supervisor down; spawn `or-finisher-1` (Phase 4) with `finisher-spawn-context.md` substituted (branch / base / worktree / plan / latest `iteration-N.md`) |
| Finisher `SHIP_COMPLETE` | Action | Shut the finisher down; **end the session** — the workflow is complete |
| Finisher `FINISHER_HANDOVER` (rare) | Action | Shut it down; spawn `or-finisher-(N+1)` on the same spawn-context — it re-runs finishing |
````

- [ ] **Step 3: In `## Proactive Status Reporting`, add a finisher bullet** (after the supervisor bullet):

````markdown
- **Finisher** — the moment `finishing-a-development-branch` completes (the user's chosen merge / PR / cleanup is done), SendMessage the manager `SHIP_COMPLETE — <one-line summary>`. Do not idle after finishing.
````

- [ ] **Step 4: In `## Handover Ladder`, add the finisher row** (after the Phase-agent row):

````markdown
| Finisher | 150k (rare) | (none — successor re-runs `finishing-a-development-branch`) | `FINISHER_HANDOVER` |
````

And in the **Fresh manager resume** paragraph, add the ship case: "If `active_phase` is `ship`, spawn `or-finisher-(N+1)` pointing at the plan + the latest `iteration-N.md` (it re-runs finishing on the existing branch)."

- [ ] **Step 5: Edit `manager-handover-template.md`** — extend the `active_phase` enum and `active_phase_agent` in both the frontmatter and the "Active phase" body:
  - frontmatter line `active_phase: brainstorm | plan | implement` → `active_phase: brainstorm | plan | implement | ship`
  - frontmatter `active_phase_agent:` comment and the body lines that enumerate agents → add `| or-finisher-<N>`
  - body line `active_phase`: `<brainstorm | plan | implement>` → `<brainstorm | plan | implement | ship>`
  - body `active_phase_agent`: `<or-brainstormer-<N> | or-plan-writer-<N> | none>` → `<or-brainstormer-<N> | or-plan-writer-<N> | or-finisher-<N> | none>`

- [ ] **Step 6: Verify (GREEN)**

```powershell
$dir = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
Select-String -Path "$dir\manager-playbook.md" -Pattern 'ITERATION N — COMPLETED.*or-finisher-1','SHIP_COMPLETE','end the session','active_phase` is `ship`'   # expect matches
Select-String -Path "$dir\manager-handover-template.md" -Pattern 'implement \| ship','or-finisher-<N>'   # expect matches
```

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-handover-template.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): wire Phase-4 ship lifecycle + manager-handover ship enum (Item 2)"
```

---

## Task 12: Items 3, 7, 6 — supervisor Adaptations & override + structured PHASE_PAUSE

Rewrite `or-supervisor.md`'s "One adaptation, one override" block into "Adaptations & override" (two adaptations [SPAWN, Task*] + one spec-gated parallel override), and convert Topology Discipline 6 from prose PAUSE to the structured `PHASE_PAUSE` token with narrowed Phase-3-local-only triggers. (Item 1's `EnterWorktree` bind for the supervisor is added in Task 15. Item 2 for the supervisor is a no-op — verified in Step 1.)

**Files:**
- Modify: `plugins/claude-toolkit/agents/or-supervisor.md`

- [ ] **Step 1: Confirm pre-state + Item-2 no-op (RED)**

```powershell
$sup = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-supervisor.md"
Select-String -Path $sup -Pattern '### One adaptation, one override'   # expect match (about to be rewritten)
Select-String -Path $sup -Pattern 'finishing-a-development-branch'      # expect NO match (so Item 2 = no-op here)
```

- [ ] **Step 2 (Items 3, 7): Replace the `### One adaptation, one override` block** (from that heading through "Everything else from SDD applies verbatim — its red flags, status handling, per-task structure.") with:

````markdown
### Adaptations & override

Two adaptations (forced by the team topology) and one override (a deliberate improvement):

- **Adaptation 1 — dispatch via SPAWN.** Where SDD says "Dispatch implementer subagent" (or spec / code-quality / final reviewer), use the SPAWN protocol below instead. You have no `Agent` tool.
- **Adaptation 2 — `Task*` for task tracking.** SDD instructs `TodoWrite`; you have the team-harness-native `TaskCreate` / `TaskUpdate` / `TaskList` (granted to every teammate by the spec's F7). Use `Task*` wherever SDD says `TodoWrite` — same intent, harness-native mechanism. (The manager seeing `Task*` system reminders is expected and handled manager-side; do not change your behavior for it.)
- **Override — parallel reviewers, spec-gated.** SDD dispatches spec review, then (only on pass) code-quality review — a sequential gate. You run spec + code-quality reviewers **in parallel** after the implementer reports DONE. Rationale: **wall-clock latency** — in this team topology both reviewers are cheap and finish in the time of the slower one. **You preserve SDD's gate by moving it from dispatch-order to which-result-counts:**
  - *Spec passes* (the common case, especially post-TDD) → the concurrent code-quality result was looking at spec-compliant code → it is **valid**; act on it (one round-trip saved).
  - *Spec fails* → this round's code-quality result was looking at code that is about to change → **discard it**; relay the spec fixes to the implementer, re-run spec review, and once it passes dispatch a **fresh** code-quality review (`or-code-quality-reviewer-task<N>-rev<K>`) on the now-compliant code.
  - Guarantee: code-quality findings never apply to code about to change (same correctness as SDD's sequential gate); the only cost is wasted compute on a spec-failure round (uncommon).

Everything else from SDD applies verbatim — its red flags, status handling, per-task structure.
````

- [ ] **Step 3 (Item 6): Replace Topology Discipline 6** with the structured token + narrowed triggers:

````markdown
6. **`PHASE_PAUSE` before unusual mid-implementation visible actions.** Phase 3 is **local-commits-only**: frequent local commits to the worktree branch are normal workflow — do them freely, never pause for them. Routine end-of-branch integration (push / PR / merge) is **not** your job — it is Phase 4 (`or-finisher`), so it never triggers a pause here either. PAUSE only for the *unusual mid-implementation* visible-to-others or hard-to-reverse action: an external API call, a plan task that itself pushes / deploys / publishes, a delete outside the worktree. To pause, brief the worker to STATUS-and-PAUSE, then SendMessage the `manager` the **structured** token (identical to the phase agents'; one PAUSE token across all depth-1 tiers):

       PHASE_PAUSE
       action: <one line>
       impact: <one line>

   and wait for `PROCEED` or `REJECTED — reason: <line>` propagated back through the `manager`. Send action + impact only — commit lists / follow-up flags live in `iteration-N.md`.
````

- [ ] **Step 4: Verify (GREEN)**

```powershell
$sup = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-supervisor.md"
Select-String -Path $sup -Pattern '### Adaptations & override','Adaptation 2 — `Task\*`','spec-gated','which-result-counts'   # expect matches
Select-String -Path $sup -Pattern '### One adaptation, one override'   # expect NO match
Select-String -Path $sup -Pattern 'local-commits-only','PHASE_PAUSE'    # expect matches
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-supervisor.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): supervisor Adaptations & override + structured PHASE_PAUSE (Items 3,6,7)"
```

---

## Task 13: Item 1 — add `Worktree:` to the supervisor/implementer/reviewer spawn-contexts

The manager substitutes `<WORKTREE_PATH>` (it holds it from `PREFLIGHT_OK`); these tiers need it to bind in Task 15. Insert `Worktree: <WORKTREE_PATH>` as line 2 (after `Identity:`), matching the brainstormer/plan-writer pattern.

**Files:**
- Modify: `…/assets/supervisor-spawn-context.md`, `…/assets/implementer-spawn-context.md`, `…/assets/reviewer-spawn-context.md`

- [ ] **Step 1: Confirm pre-state (RED)**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
Select-String -Path "$a\supervisor-spawn-context.md","$a\implementer-spawn-context.md","$a\reviewer-spawn-context.md" -Pattern '^Worktree:'   # expect NO match
```

- [ ] **Step 2: In each of the three files, insert a new line `Worktree: <WORKTREE_PATH>` immediately after the `Identity:` line.** Final shapes:
  - `supervisor-spawn-context.md`: `Identity:` / `Worktree: <WORKTREE_PATH>` / `Plan:` / `Branch:` / …
  - `implementer-spawn-context.md`: `Identity:` / `Worktree: <WORKTREE_PATH>` / `Branch:` / `Supervisor:`
  - `reviewer-spawn-context.md`: `Identity:` / `Worktree: <WORKTREE_PATH>` / `Branch:` / `Supervisor:`

- [ ] **Step 3: Verify (GREEN)**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
(Select-String -Path "$a\supervisor-spawn-context.md","$a\implementer-spawn-context.md","$a\reviewer-spawn-context.md" -Pattern '^Worktree: <WORKTREE_PATH>$').Count   # expect 3
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/supervisor-spawn-context.md plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/implementer-spawn-context.md plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/reviewer-spawn-context.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): add Worktree: to supervisor/implementer/reviewer spawn-contexts (Item 1)"
```

---

## Task 14: Items 4a, 1, 9.2 — phase-agent abort confirm + EnterWorktree bind + researcher-naming note

Edit both phase agents: (4a) own the abort confirm in their own dialogue; (1) add the `EnterWorktree` tool + STEP -1 bind directive; (9.2) document the `or-<topic>-researcher-N` naming convention in the SPAWN_RESEARCH summary.

**Files:**
- Modify: `plugins/claude-toolkit/agents/or-brainstormer.md`, `plugins/claude-toolkit/agents/or-plan-writer.md`

- [ ] **Step 1: Confirm pre-state (RED)**

```powershell
$b = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-brainstormer.md"
$p = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-plan-writer.md"
Select-String -Path $b,$p -Pattern 'EnterWorktree','STEP -1'   # expect NO match
Select-String -Path $b,$p -Pattern 'The manager surfaces a confirm prompt to the user'   # expect match (old abort path)
```

- [ ] **Step 2 (Item 1): Add `EnterWorktree` to the `tools:` frontmatter** of both agents:
  - both currently: `tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, Skill, SendMessage` → append `, EnterWorktree`.

- [ ] **Step 3 (Item 1): Add a STEP -1 bind directive** at the top of each agent body (immediately before its `## STEP 0` heading). Use this text (it references the agent's already-present `Worktree:` spawn-context line):

````markdown
## STEP -1 — Bind to the worktree (REQUIRED, FIRST ACTION, before STEP 0)

Your spawn context names a `Worktree:` path. A spawned teammate inherits the manager's CWD (the main checkout), NOT the worktree — so before reading the spec/plan, invoking any skill, or running git, bind your session:

    EnterWorktree(<WORKTREE_PATH>)
    git rev-parse --show-toplevel   # must equal <WORKTREE_PATH>

If `EnterWorktree` is unavailable or the path does not match, STOP and SendMessage the manager `BLOCKED — worktree bind failed: <detail>` rather than working in the wrong checkout.

> **Verification pending (Item 1 / Spike 6).** Whether `EnterWorktree(<path>)` binds a fresh background teammate into a *shared* team worktree is undocumented and is verified by the worktree-binding spike at cutover (`docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`). Do not delete this note until Spike 6 is GREEN.

---
````

- [ ] **Step 4 (Item 4a): Replace the `## Abort path` section** in each agent with the phase-agent-owned confirm. For `or-brainstormer` use "spec"; for `or-plan-writer` use "plan":

````markdown
## Abort path

If, during the dialogue, the user makes clear they want to end the whole orchestrator session (not merely finish this phase), confirm it with them **directly** first — this is your dialogue to own:

"Ending now stops the whole orchestrated session. Your <spec|plan> so far is saved at `<path>`. Confirm you want to abort? (yes / no)"

Only on an explicit "yes" do you SendMessage the manager:

    PHASE_ABORT — reason: <one line capturing the user's confirmed request>

The manager's handling is then purely mechanical (shut you down, end the session) — it surfaces no further confirm. Do NOT shut yourself down or abandon the workflow on your own — await the manager's `shutdown_request`. If the user says "no," resume the phase.
````

- [ ] **Step 5 (Item 9.2): In each agent's SPAWN_RESEARCH summary, add a one-line naming-convention note** after the `NAME: <short-name>` field description:

````markdown
> Naming convention: compose `NAME` as `or-<topic>-researcher-N` (the documented phase-agent-side convention). The manager spawns with whatever `NAME` you give — there is no manager-side enforcement.
````

- [ ] **Step 6: Verify (GREEN)**

```powershell
$b = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-brainstormer.md"
$p = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-plan-writer.md"
Select-String -Path $b,$p -Pattern 'Skill, SendMessage, EnterWorktree','## STEP -1 — Bind to the worktree','Confirm you want to abort\? \(yes / no\)','or-<topic>-researcher-N'   # expect matches in both
Select-String -Path $b,$p -Pattern 'The manager surfaces a confirm prompt to the user'   # expect NO match
```

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-brainstormer.md plugins/claude-toolkit/agents/or-plan-writer.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): phase-agent abort confirm + EnterWorktree bind + researcher-naming note (Items 4a,1,9.2)"
```

---

## Task 15: Item 1 (+ 9.5) — EnterWorktree bind on the supervisor + four workers

Add the `EnterWorktree` tool grant + a bind directive to `or-supervisor` and the four worker agents. For the workers, reconcile the unreliable "already checked out in this worktree" assertion to depend on the bind. Add the Item 9.5 F7 note where the tools are listed.

**Files:**
- Modify: `agents/or-supervisor.md`, `agents/or-implementer.md`, `agents/or-spec-reviewer.md`, `agents/or-code-quality-reviewer.md`, `agents/or-final-reviewer.md`

- [ ] **Step 1: Confirm pre-state (RED)**

```powershell
$g = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
Select-String -Path "$g\or-supervisor.md","$g\or-implementer.md","$g\or-spec-reviewer.md","$g\or-code-quality-reviewer.md","$g\or-final-reviewer.md" -Pattern 'EnterWorktree'   # expect NO match
```

- [ ] **Step 2: Add `EnterWorktree` to each `tools:` frontmatter line:**
  - `or-supervisor.md`: `… Skill, SendMessage, TaskCreate, TaskUpdate, TaskList` → append `, EnterWorktree`.
  - `or-implementer.md`: `Read, Write, Edit, Glob, Grep, Bash, Skill, SendMessage` → append `, EnterWorktree`.
  - `or-spec-reviewer.md`, `or-code-quality-reviewer.md`, `or-final-reviewer.md`: `Read, Grep, Glob, Bash, SendMessage` → append `, EnterWorktree`.

- [ ] **Step 3: Insert the bind directive.** For `or-supervisor.md`, add it as `## STEP -1` immediately before "## STEP 0 — Invoke the canonical execution skill". For the four workers, add it as a `## STEP -1` section immediately before their `## Protocol` heading. Directive text (same as Task 14 Step 3, but the failure recipient is the **supervisor** for workers / the **manager** for the supervisor):

````markdown
## STEP -1 — Bind to the worktree (REQUIRED, FIRST ACTION)

Your spawn context names a `Worktree:` path. A spawned teammate inherits the manager's CWD (the main checkout), NOT the worktree — so before reading any repo file, invoking any skill, or running git, bind your session:

    EnterWorktree(<WORKTREE_PATH>)
    git rev-parse --show-toplevel   # must equal <WORKTREE_PATH>

If `EnterWorktree` is unavailable or the path does not match, STOP and SendMessage your <supervisor|the manager> `BLOCKED — worktree bind failed: <detail>` rather than operating in the wrong checkout. This bind is what actually places this session on the branch.

> **Verification pending (Item 1 / Spike 6).** Whether `EnterWorktree(<path>)` binds a fresh background teammate into a *shared* team worktree is undocumented; verified by the worktree-binding spike at cutover. Do not delete this note until Spike 6 is GREEN.

---
````

- [ ] **Step 4: Reconcile the workers' stale assertion.** In each of the four workers, change the preamble sentence "The branch named in your spawn context is already checked out in this worktree." → "Bind to the `Worktree:` path in your spawn context as your first action (STEP -1) — that bind is what places this session on the branch."

- [ ] **Step 5 (Item 9.5): Add the F7 note to `or-supervisor.md`** near its frontmatter/STEP-0 (a body line):

````markdown
> Tool-grant note (Item 9.5): the supervisor lists `Task*` explicitly as belt-and-suspenders; phase agents and workers rely on the spec's **F7** auto-grant (Claude Code grants `SendMessage` + the task tools to every teammate regardless of frontmatter). Removing the explicit listing is **deferred until the F7 spike (Spike 5) is GREEN** at cutover.
````

- [ ] **Step 6: Verify (GREEN)**

```powershell
$g = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
$files = "$g\or-supervisor.md","$g\or-implementer.md","$g\or-spec-reviewer.md","$g\or-code-quality-reviewer.md","$g\or-final-reviewer.md"
(Select-String -Path $files -Pattern ', EnterWorktree').Count   # expect 5 (one tools line each)
(Select-String -Path $files -Pattern '## STEP -1 — Bind to the worktree').Count   # expect 5
Select-String -Path "$g\or-implementer.md","$g\or-spec-reviewer.md","$g\or-code-quality-reviewer.md","$g\or-final-reviewer.md" -Pattern 'already checked out in this worktree'   # expect NO match
Select-String -Path "$g\or-supervisor.md" -Pattern 'Tool-grant note \(Item 9.5\)'   # expect match
```

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-supervisor.md plugins/claude-toolkit/agents/or-implementer.md plugins/claude-toolkit/agents/or-spec-reviewer.md plugins/claude-toolkit/agents/or-code-quality-reviewer.md plugins/claude-toolkit/agents/or-final-reviewer.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): EnterWorktree bind on supervisor+workers; F7 note (Items 1,9.5)"
```

---

## Task 16: Items 1, 8a — preflight creates `.claude/worktrees/<name>` + compaction check/warn

`preflight-brief.md` must create the shared worktree under `.claude/worktrees/<name>` (the `EnterWorktree` path constraint) and optionally check/warn the compaction config.

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/preflight-brief.md`

- [ ] **Step 1: Confirm pre-state (RED)**

```powershell
$pf = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\preflight-brief.md"
Select-String -Path $pf -Pattern '\.claude/worktrees/','CLAUDE_AUTOCOMPACT_PCT_OVERRIDE'   # expect NO match
```

- [ ] **Step 2 (Item 1): In Step 3 check 3 ("Worktree ready"), specify the location.** Change "create the worktree with the chosen name off the chosen base" to: "create the worktree **under `.claude/worktrees/<name>`** (the `EnterWorktree` path constraint that the repo-touching tiers bind to) off the chosen base". Add a one-line note: "The resolved absolute `.claude/worktrees/<name>` path is what you return as `worktree:` — every repo-touching tier `EnterWorktree`s into it."

- [ ] **Step 3 (Item 8a): Add a new check 5 to Step 3** (non-fatal — warn only):

````markdown
5. **Auto-compaction headroom (warn, non-fatal).** If `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` is unset and the model's context window is ≤ 200k, the ~95% auto-compaction trigger (~190k) would pre-empt the manager's 200k handover. Surface a one-line `warning:` in the output block recommending the user set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` high/disabled (Item 8a; verified at cutover by the spike suite). Do not FAIL on this.
````

Add an optional `warning: <text or "(none)">` line to the `PREFLIGHT_OK` output block in Step 4.

- [ ] **Step 4: Verify (GREEN)**

```powershell
$pf = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\preflight-brief.md"
Select-String -Path $pf -Pattern '\.claude/worktrees/<name>','CLAUDE_AUTOCOMPACT_PCT_OVERRIDE','warning:'   # expect matches
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/preflight-brief.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): preflight creates .claude/worktrees/<name> + compaction warn (Items 1,8a)"
```

---

## Task 17: Item 10 — add Spike 6 (worktree binding) + Spike 7 (empty idle turn) + update cutover

Add the two new spikes for the deferred-design items and extend the cutover checklist. These are **authored, not executed** here (execution is at cutover).

**Files:**
- Modify: `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`

- [ ] **Step 1: Confirm pre-state (RED)**

```powershell
$sp = "I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md"
Select-String -Path $sp -Pattern '^## Spike 6','^## Spike 7'   # expect NO match
Select-String -Path $sp -Pattern 'Run \*\*Spike 1 → Spike 5\*\*'   # expect match (about to widen)
```

- [ ] **Step 2: Insert Spike 6 and Spike 7 immediately before the `## Cutover checklist` heading**

````markdown
## Spike 6 — Worktree binding from a fresh teammate (remediation Item 1 — TOP RISK)

**Purpose:** Resolve the top-risk unknown: a spawned teammate's actual starting CWD, and whether `EnterWorktree(<path>)` binds it into the team's **shared** worktree. Sub-questions: (a) is `EnterWorktree` grantable to a teammate via `tools:` frontmatter and callable by it; (b) what is a fresh background teammate's starting `git rev-parse --show-toplevel` (hypothesis: the manager's main checkout, NOT the worktree); (c) are team teammates auto-isolated by default (and is `worktree.bgIsolation: "none"` needed); (d) does `EnterWorktree(<shared .claude/worktrees/ path>)` land the teammate on the shared branch state; (e) the exact `.claude/worktrees/` path constraint.

**Setup:** Plugin installed. A shared team worktree created under `.claude/worktrees/<name>` (preflight's path).

**RED baseline (proves the bind is load-bearing):** Spawn a repo-touching teammate variant whose body **omits** the STEP -1 bind directive. Confirm its `git rev-parse --show-toplevel` is the **main checkout**, not the worktree — i.e. teammates do NOT inherit the worktree CWD. This is what makes the bind load-bearing.

**GREEN:** A teammate WITH the STEP -1 bind directive (and the `EnterWorktree` tool grant) lands in the shared worktree (`rev-parse` equals `<WORKTREE_PATH>`) and can commit to the branch; spec/code-quality reviewers and the implementer all operate on the **same** branch state.

**Fallback:** If `EnterWorktree` does not bind a *shared* worktree, or teammates are auto-isolated into their own worktrees by default, the shared-worktree design must be reconciled (the supervisor + workers MUST see the same branch) — try `worktree.bgIsolation: "none"`, or switch the per-tier model. If `EnterWorktree` is not grantable to a teammate at all, escalate — the binding mechanism needs redesign before the suite ships. **This is the top-risk item; do not declare the suite done until Spike 6 is GREEN** (no acceptable degraded end-state).

---

## Spike 7 — Empty idle turn (remediation Item 8b)

**Purpose:** Confirm the harness gracefully accepts a manager turn with **no text and no tool call** (end the turn empty). The skill's central conservation discipline — silence on idle wake-ups (worker boot, `shutdown_response`, teammate progress, hook reminders) — depends on it.

**Setup:** Plugin installed; a running orchestration (or a minimal manager teammate) driven to an idle-class wake-up.

**RED baseline:** None meaningful — capability probe. The implicit failure mode is the harness erroring or forcing output on an empty turn.

**GREEN:** The manager ends an idle wake-up with no output and no tool call, and the harness accepts it (no error, no forced text).

**Fallback:** If a truly-empty turn is rejected, the silence-on-idle discipline must be reworked — define the minimal accepted no-op and update the playbook's Idle Taxonomy + Communication Style. Until GREEN, treat silence-on-idle as load-bearing-and-unverified. **Do not declare the suite done until Spike 7 is GREEN.**
````

- [ ] **Step 3: Update the cutover checklist.**
  - Step 3 line: `Run **Spike 1 → Spike 5** above` → `Run **Spike 1 → Spike 7** above`.
  - Step 4 last sentence: extend the must-pass set: `**Do not declare the suite done until Spikes 1–3, Spike 6 (worktree binding — top risk), and Spike 7 (empty idle turn) are GREEN** (Spikes 4–5 retain acceptable plain-text/frontmatter fallbacks).`
  - Add a note to step 3: "Spikes 6–7 discharge remediation Items 1 and 8b respectively."

- [ ] **Step 4: Verify (GREEN)**

```powershell
$sp = "I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md"
Select-String -Path $sp -Pattern '^## Spike 6 —','^## Spike 7 —','Run \*\*Spike 1 → Spike 7\*\*','Spikes 1–3, Spike 6'   # expect matches
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md
git -C I:\Dev\claude-toolkit commit -m "test(or-sas): add worktree-binding + empty-idle-turn spikes; widen cutover (Item 10)"
```

---

## Task 18: Item 0 — delete the wrapper command

The skill is now `user_invocable` (Task 2), so the thin wrapper command is redundant.

**Files:**
- Delete: `plugins/claude-toolkit/commands/or-superpowers-at-scale.md`

- [ ] **Step 1: Confirm it exists (RED)**

```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\commands\or-superpowers-at-scale.md"   # expect True
```

- [ ] **Step 2: Delete the file**

```powershell
git -C I:\Dev\claude-toolkit rm plugins/claude-toolkit/commands/or-superpowers-at-scale.md
```

- [ ] **Step 3: Verify no dangling references remain (GREEN)** — only the README (fixed in Task 19) and historical docs/plans may mention it; there must be no *active* command reference:

```powershell
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\commands\or-superpowers-at-scale.md"   # expect False
# scan plugin sources (not docs/plans history) for stray refs to the command file path:
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\*" -Pattern 'commands/or-superpowers-at-scale' -Recurse   # expect NO match
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas)!: remove wrapper command; skill is user_invocable (Item 0)"
```

---

## Task 19: Item 0 — README updates (+ deviation #3: list `or-finisher`)

Remove the command bullet, update the skill bullet to reflect the user-invocable entry point + Phase-4 ship, fix the Dependencies sentence, and add `or-finisher` to the agent listing.

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Confirm pre-state (RED)**

```powershell
$r = "I:\Dev\claude-toolkit\README.md"
Select-String -Path $r -Pattern '- \*\*/or-superpowers-at-scale\*\* — Orchestrate'   # expect match (command bullet)
Select-String -Path $r -Pattern 'or-finisher'   # expect NO match
```

- [ ] **Step 2: Remove the command bullet** (the `### Commands` line `- **/or-superpowers-at-scale** — Orchestrate brainstorm → plan → implement end-to-end in one session (depends on superpowers plugin)`).

- [ ] **Step 3: Update the skill bullet** (under `### Skills`) to:

````markdown
- **or-superpowers-at-scale** — User-invocable 3-tier orchestrator: brainstorm → plan → implement → ship, with the manager's context preserved (`/or-superpowers-at-scale [<idea> | <spec> | <plan>]`; depends on superpowers plugin)
````

- [ ] **Step 4: Add `or-finisher` to the orchestrator agent listing** — after the `or-implementer … or-final-reviewer` line add:

````markdown
- **or-finisher** — Phase-4 ship teammate (drives finishing-a-development-branch in direct dialogue)
````

- [ ] **Step 5: Fix the Dependencies sentence** — change `The /design, /plan-from-design, /implement-from-plan, and /or-superpowers-at-scale commands — and the or-superpowers-at-scale skill — depend on …` to:

````markdown
The `/design`, `/plan-from-design`, and `/implement-from-plan` commands — and the `or-superpowers-at-scale` skill — depend on the **superpowers** plugin. Install it separately if you want to use them.
````

- [ ] **Step 6: Verify (GREEN)**

```powershell
$r = "I:\Dev\claude-toolkit\README.md"
Select-String -Path $r -Pattern '- \*\*/or-superpowers-at-scale\*\* — Orchestrate'   # expect NO match
Select-String -Path $r -Pattern 'User-invocable 3-tier orchestrator','implement → ship','or-finisher'   # expect matches
Select-String -Path $r -Pattern '/implement-from-plan, and /or-superpowers-at-scale commands'   # expect NO match
```

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add README.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): README — skill entry point + or-finisher; drop command refs (Item 0)"
```

---

## Task 20: Version bump `1.3.0 → 1.4.0`

Bump the version in all three places. Follow the `claude-toolkit:updating-plugin` checklist (manifest sync; no CHANGELOG file — versioning is via release commits, per design).

**Files:**
- Modify: `plugins/claude-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`

- [ ] **Step 1: Confirm current versions (RED)**

```powershell
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json","I:\Dev\claude-toolkit\.claude-plugin\marketplace.json" -Pattern '"version": "1.3.0"'   # expect 3 matches (plugin.json ×1, marketplace.json ×2)
```

- [ ] **Step 2: Edit the three `"version": "1.3.0"` → `"version": "1.4.0"`** — `plugin.json` (`version`), `marketplace.json` (`metadata.version` **and** `plugins[0].version`). Leave descriptions unchanged (still accurate). Confirm both files remain valid JSON.

- [ ] **Step 3: Verify (GREEN)**

```powershell
$pj = "I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json"
$mj = "I:\Dev\claude-toolkit\.claude-plugin\marketplace.json"
(Select-String -Path $pj,$mj -Pattern '"version": "1.4.0"').Count   # expect 3
(Select-String -Path $pj,$mj -Pattern '"version": "1.3.0"').Count   # expect 0
Get-Content $pj -Raw | ConvertFrom-Json | Out-Null    # parses → valid JSON
Get-Content $mj -Raw | ConvertFrom-Json | Out-Null    # parses → valid JSON
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git -C I:\Dev\claude-toolkit commit -m "release: claude-toolkit 1.4.0 — or-superpowers-at-scale review remediation"
```

---

## Task 21: Consolidated self-review + structural validation

The plan's self-review run as a task: validate the plugin structurally and confirm spec coverage with fresh eyes. No new content unless a gap is found.

**Files:** none (verification); fix-and-commit only if a gap surfaces.

- [ ] **Step 1: Structural plugin validation**

Run `claude plugin validate` against the repo (or dispatch the `plugin-dev:plugin-validator` agent on `plugins/claude-toolkit`). Expect: valid manifest, all agents parse (frontmatter valid), no broken component references. If `claude` is unavailable, record the skip and rely on the greps below.

- [ ] **Step 2: Frontmatter sanity on every touched agent + the skill**

```powershell
$g = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
# EnterWorktree granted on all 8 repo-touching agents (7 edited + or-finisher created):
(Select-String -Path "$g\or-supervisor.md","$g\or-brainstormer.md","$g\or-plan-writer.md","$g\or-implementer.md","$g\or-spec-reviewer.md","$g\or-code-quality-reviewer.md","$g\or-final-reviewer.md","$g\or-finisher.md" -Pattern 'EnterWorktree').Count   # expect ≥ 8
Select-String -Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md" -Pattern 'user_invocable: true'   # expect match
```

- [ ] **Step 3: Cross-reference + de-dup integrity (repeat the Task 3 checks) + no orphaned command refs.**

```powershell
$a = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
Test-Path "$a\manager-playbook.md","$a\finisher-spawn-context.md"   # expect True, True
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-finisher.md"   # expect True
Test-Path "I:\Dev\claude-toolkit\plugins\claude-toolkit\commands\or-superpowers-at-scale.md"   # expect False
Select-String -Path "$a\manager-playbook.md" -Pattern '^\| ROLE \| subagent_type \|'   # expect NO match (de-dup holds)
```

- [ ] **Step 4: Spec-coverage pass.** Walk the design Items 0–10 against the coverage table at the bottom of this plan; confirm each maps to a landed task. List any gap; if found, add a task and implement before proceeding.

- [ ] **Step 5: Commit (only if a gap fix was needed)**

```powershell
git -C I:\Dev\claude-toolkit add -A
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): close self-review gap"
```

---

## Task 22: Approval-gated finish (`superpowers:finishing-a-development-branch`)

Integrate the branch. **This task requires explicit user approval before any push/PR.**

**Files:** none (git integration).

- [ ] **Step 1: Invoke `Skill('superpowers:finishing-a-development-branch')`** and follow it — present merge / PR / cleanup options for branch `or-sas-review-remediation` off `master`.

- [ ] **Step 2: On the user's explicit go-ahead**, perform the chosen integration (`git -C I:\Dev\claude-toolkit …`). Do not push without approval.

- [ ] **Step 3: Confirm + record next step.** Note that Items 1, 8, and 10 remain **open until cutover** — the spikes (esp. Spike 6, top risk) must be executed against the installed plugin and recorded GREEN in the spikes doc before the remediation is truly complete.

---

## Self-review — spec coverage (design Items 0–10 → tasks)

| Design item | Lands in | Notes |
|---|---|---|
| **Item 5** (foundational restructure / spine) | Tasks 1, 2, 3 | Playbook created; lean SKILL.md; spawn-protocol.md sole SPAWN source. |
| **Item 0** (command → user-invocable skill; Input) | Tasks 2 (`user_invocable`), 4 (Input subsection), 18 (delete command), 19 (README) | Rich description kept verbatim. |
| **Item 2** (Phase 4 ship via `or-finisher`) | Tasks 9 (agent), 10 (spawn-context), 11 (wiring + manager-handover ship enum), 2 (SKILL topology/phase/integration) | Supervisor Item-2 = no-op (verified Task 12). `SHIP_COMPLETE` token added. |
| **Item 3** (TodoWrite → Task* adaptation) | Task 12 | Adaptation 2 in the supervisor's "Adaptations & override". |
| **Item 4** (PHASE_ABORT to phase agent; allowlist) | Tasks 5 (manager-side mechanical + two-category allowlist), 14 (phase-agent-owned confirm) | |
| **Item 6** (structured PHASE_PAUSE for supervisor) | Tasks 6 (playbook collapse), 12 (supervisor token + narrowed triggers) | One PAUSE token across depth-1 tiers. |
| **Item 7** (parallel review, spec-gated) | Task 12 | Which-result-counts gate; wall-clock rationale. |
| **Item 9** (polish batch) | 9.1 reaping → Task 7; 9.2 researcher naming → Task 14; 9.3 backticks → Task 4; 9.4 `or-` prefix → Task 2; 9.5 frontmatter/F7 → Task 15 (note; removal deferred to Spike 5) | |
| **Item 1** (worktree binding — top risk, deferred) | Tasks 13 (spawn-contexts), 14 (phase agents), 15 (supervisor+workers), 16 (preflight `.claude/worktrees/`), 9 (finisher); Spike 6 (Task 17) | `EnterWorktree` tool grant added (deviation #1). Open until Spike 6 GREEN. |
| **Item 8** (compaction + empty-idle, deferred) | Task 8 (playbook notes), 16 (preflight warn); Spike 7 (Task 17) | Open until Spike 7 GREEN. |
| **Item 10** (execute spikes at cutover) | Task 17 (author Spikes 6–7 + widen cutover); execution itself is out of scope (cutover) | |

**Deviations from §5 manifest:** see the "Deviations" section above (EnterWorktree tool grant; manager-handover ship enum; README `or-finisher`; supervisor Item-2 no-op; no finisher-handover template).

**Placeholder scan:** every code/content step contains the literal target text or a precise verbatim-move instruction anchored to a stable heading; verification steps are runnable PowerShell with expected match/no-match. No "TBD"/"similar to"/"add appropriate" steps.

**Type/name consistency:** token names used consistently — `SHIP_COMPLETE`, `FINISHER_HANDOVER`, `PHASE_PAUSE` (single), `PHASE_ABORT`, `or-finisher-N`, `claude-toolkit:or-finisher`; `active_phase` enum `brainstorm | plan | implement | ship`; worktree path `.claude/worktrees/<name>`; spawn-context var `<WORKTREE_PATH>`.
