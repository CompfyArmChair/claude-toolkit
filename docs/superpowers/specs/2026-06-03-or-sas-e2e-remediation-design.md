# or-superpowers-at-scale — E2E-Run Remediation Design

**Date:** 2026-06-03
**Status:** Design complete (brainstormed + approved) — awaiting `plan-from-design`.
**Scope:** Remediation of the 28 findings (F1–F28) surfaced by the first true end-to-end run of the `claude-toolkit:or-superpowers-at-scale` orchestrator (plugin 1.4.2).
**Version target:** plugin `1.4.x` bump (exact number chosen at implementation time, as the prior cycle did).

---

## 1. Problem Statement

The first true end-to-end exercise of the orchestrator — manager-driven, building a throwaway breakout game idea→ship on team `breakout-game`, across multiple manager/supervisor sessions — surfaced **28 real-world defects (F1–F28)**, recorded in `docs/superpowers/validation/2026-06-03-or-sas-e2e-breakout-run-notes.md`. The prior remediation cycle had fixed the design-review findings and passed every behavioral spike; this was the first time the orchestrator was actually *used* end-to-end.

The **headline defect**: the core safeguard — the 200k cross-session handover that protects the single non-refreshable **manager** context — **silently never fired**. Both the manager (~400k) and the supervisor (~600k) blew past their 200k thresholds without detecting it, because the checkpoint hook that announces threshold crossings is **starved of the events it fires on** during inbox-driven team operation (F20/F22). The manager then operated ~200k into the degrading zone, directly causing the idle-discipline collapse (F18).

Alongside the headline, the run exposed agent-body and protocol defects: a supervisor that knew the two-stage review rule yet skipped stage 2 under load (F8/F17); non-deterministic worker-report misrouting to the manager instead of the supervisor (F7/F13/F19/F24/F26); a manager-purity violation baked into a conservation rule (F25); phase-agent dialogue routed through the manager instead of the agent's own pane (F2/F5/F6); and resume/handover gaps (F11/F21/F23/F28).

This document designs the fixes. It does not redesign the orchestrator — it repairs the tiers, assets, and the one hook so the topology behaves as designed under real load. The prior cycle's design (`docs/superpowers/specs/2026-05-31-or-sas-review-remediation-design.md`) is the structural template.

---

## 2. Guiding Principles

These six principles were settled during the brainstorm and shape every fix below. They are stated here once so each theme can refer back to them.

1. **Manager is purely a broker.** The manager spawns/despawns teammates *on request* and does nothing else: it originates no teardown, holds no task state, makes no decisions, and relays nothing beyond the few sanctioned phase/lifecycle surfacings. (Established by F25; reinforced by F18, F27, F12.)
2. **Simplicity survives degradation.** Instructions a tier must keep following as its context fills have to be simple and canonical. Clever optimizations that fragment under load are removed, not patched. (Root cause of F17 — a "spec-gated parallel reviewers" override the supervisor stopped honoring under pressure.)
3. **Detection without spam.** Threshold detection rides on turn-end events (immune to inbox starvation) and is delivered once per threshold. No proactive self-tracking, no work-unit counters, no periodic nags. (Derived from the F20/F22 forensics.)
4. **Root-cause in bodies AND spawn-contexts.** In-run nudges work but do not persist — F3 proved a fix-forward nudge corrected behavior for the rest of the run yet left the agent body unchanged. Every fix lands in the agent body **and** its spawn-context (belt-and-suspenders), so a fresh successor inherits the corrected behavior.
5. **Findings/detail live on disk, never in the manager.** Tiers write detail to their handover/iteration docs and send the manager only terse pointers. (F27.)
6. **Orchestration-only.** The `or-*` bodies and assets contain **only** orchestration concerns — topology, SPAWN/SHUTDOWN, routing, handover, context economy, worktree binding, idle discipline. All *task methodology* is loaded verbatim from the superpowers skills at runtime. A fix must **never** restate or duplicate task instructions; where a behavior belongs to a superpowers skill, the fix makes the wrapper faithfully defer to it.

   **Verified during the brainstorm** (so the fixes can rely on it): `superpowers:writing-plans` contains only a self-review checklist plus an execution-handoff step — it has **no** user-facing plan-review-and-approval step (so F5's plan walkthrough is a genuine orchestration gate the wrapper must own, not a duplication). `superpowers:subagent-driven-development` (SDD) owns the **entire** two-stage review gate — `spec-reviewer-prompt.md` → `code-quality-reviewer-prompt.md`, run sequentially, with fix loops and a final reviewer — and the reviewer criteria themselves. So the review *methodology* and *criteria* are SDD's; our layer must defer to them, not restate them.

---

## 3. Remediation Themes

Findings are grouped into themes A–G plus a Principle-6 audit. Each theme states the root cause, the fix, and the files it touches. A complete F1–F28 coverage table is in Section 6.

### Theme A — Threshold detection & handover automation (F20, F22, F10; F18, F9) — HEADLINE

**Root cause (F22, forensically confirmed).** The "Context checkpoint Nk crossed" reminders are emitted by the claude-toolkit plugin hook `plugins/claude-toolkit/hooks/context-usage.py` (registered in `plugins/claude-toolkit/hooks/hooks.json`), which fires on exactly two events: `UserPromptSubmit` and `PostToolUse`. **Both are starved in inbox-driven team loops** — teammate-inbox deliveries do not trigger `UserPromptSubmit`, and `PostToolUse` does not fire for tool calls made inside an inbox-driven continuation loop. Forensic accounting of the failed run: 126 tool calls across 165 turn-ends produced **zero** hook firings after the last real keystroke. Token accounting is correct; the hook simply never runs. So the 200k handover never fires.

**Fix.** Register the hook **also** on `Stop` and `SubagentStop` (edit both `hooks.json` and `context-usage.py`). These turn-end events fire reliably in the inbox-driven loop. But they fire *after* the assistant's response, so they **cannot** inject via `additionalContext` (there is no in-progress turn to add context to). Therefore the delivery mechanism splits by whether the threshold is *actionable*:

- **Actionable thresholds (≥200k, the handover triggers):** on a `Stop`/`SubagentStop` crossing, the hook returns `{"decision": "block", "reason": "<handover instruction>"}`, which **forces exactly one more turn** — the handover turn the tier needs. The once-per-threshold state (already present) plus the `stop_hook_active` payload guard prevent re-blocking and infinite loops.
- **Informational threshold (the 100k checkpoint):** stays best-effort on the existing `UserPromptSubmit`/`PostToolUse` + `additionalContext` path. Never force a turn for non-actionable information.

Preserve the existing once-per-threshold anti-spam and the <50%-usage reset (for `/compact`/`/rewind`). The 250k/300k checkpoints are reframed consistently: any checkpoint at or above the handover threshold is actionable via the block path on turn-end; sub-threshold ones remain informational.

**Coverage and the one residual uncertainty.** `SubagentStop` reliably reaches every background teammate — supervisor, phase agents, finisher, workers — so their detection is solid. The **manager** is the parent Claude in the main loop; whether its main-loop `Stop` fires under an inbox-wake (rather than a user keystroke) is **undocumented**. This is the only load-bearing unknown in the whole remediation, so it is gated by a behavioral spike (Section 5). Hook-only detection **for the manager** is contingent on that spike passing.

**F10 — handover is mandatory and auto-executed.** Edit `manager-playbook.md` (Handover Ladder + Required Communication Style) so the 200k cross-session handover is **mandatory and automatic**: the manager does NOT present a wrap/continue/fix-forward menu. It executes the handover and emits exactly one sanctioned surfacing — "recommend fresh session." Explicitly forbid the inference "no reminder ⇒ still under threshold" (the manager made exactly this wrong inference during the run). No user go-ahead gates the handover (unlike the plan→implementation transition, which itself is being removed — see Theme E).

**F18 — idle-discipline drift.** The primary cure is the fixed detection above: once the manager reliably hands over at 200k it never reaches the deep-degradation zone where the four idle-discipline slips occurred. Per Principle 2, add **one** short named line to the playbook idle taxonomy naming "idle-discipline drift" as a recognized degradation signal — and **no** heavy machinery (no per-wake-up gate scaffolding, no escalation state). The structural cure is "hand over at 200k on time," not new idle bookkeeping.

**F9 — no fix (context-only).** The manager hit 200k at Task 2 only because it was doubling as the test scribe (logging F1–F8 and the correction dialogue). That is not a normal-run cost; there is no clean baseline to act on. Recorded as a non-actionable meta-finding.

**Files:** `plugins/claude-toolkit/hooks/context-usage.py`, `plugins/claude-toolkit/hooks/hooks.json`, `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`.

---

### Theme B — Review-gate simplification (F8, F17, F14)

**Root cause (F17, the scariest finding).** A supervisor that *knew* the two-stage rule and had run it correctly for 8 tasks still skipped the code-quality stage on Task 9 — it batched the spec-reviewer SHUTDOWN with the next task's implementer SPAWN, and the SHUTDOWN-then-SPAWN rhythm masked the missing stage-2 spawn. Prose briefing does **not** hold a load-bearing invariant under degradation (Principle 2). F8 was the same defect one session earlier (supervisor skipped reviewers entirely until nudged).

**Fix (Principles 2 + 6).** **Remove the "parallel reviewers, spec-gated" override** from `or-supervisor.md` (the current "Adaptations & override" block). The supervisor follows **canonical SDD verbatim**: implementer → spec-review → (on pass) code-quality-review → fix loops → complete — sequential, simple, and entirely SDD's. This deletes the clever optimization that fragmented under load. Keep **only** the two unavoidable topology adaptations, which are pure orchestration:

1. SDD "dispatch subagent" → the SPAWN broker handshake (the supervisor has no `Agent` tool).
2. SDD `TodoWrite` → `Task*` (the team-harness-native task mechanism).

**One explicit orchestration-protocol guard.** Add a single SPAWN/SHUTDOWN sequencing rule to `or-supervisor.md` that makes SDD's sequential flow explicit at the broker layer and names the F17 anti-pattern: *a task's gate fully closes (BOTH reviews PASS) before the next task's implementer is spawned; never batch a reviewer SHUTDOWN with the next-task SPAWN.* Frame it as a **SPAWN/SHUTDOWN sequencing rule** (orchestration — which is ours) rather than as review discipline (which is SDD's). This is the structural guard F17 demands without re-stating SDD's review methodology.

**F14 — board auto-completes on worker exit (harness behavior).** A controlled test during the run confirmed the team task board auto-flips a task from `in_progress` to `completed` when the background worker exits — even when the worker is explicitly told not to touch the board. This is a harness side effect, not the implementer. Document it in `or-supervisor.md` (and note it in `manager-playbook.md`): the supervisor **re-asserts `in_progress`** after an implementer exits and marks `completed` only after **both** reviews PASS. This is a required harness-workaround step and pure orchestration — SDD's solo model has no team board to defend against.

**Manager involvement: zero.** The manager is not a review backstop (during the run the manager's noticing of the missing stage-2 spawn caught F17, but per Principle 1 the manager originates nothing). The structural guard lives at the supervisor/board layer where it belongs.

**Files:** `plugins/claude-toolkit/agents/or-supervisor.md`; `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md` (F14 note only).

---

### Theme C — Worker I/O & report-trust (F7, F13, F19, F24, F26)

**Root cause.** Worker→supervisor reporting is **non-deterministic without an explicit directive**. Misroutes (report sent to the manager instead of the supervisor) hit the implementer role *and* both reviewer roles across three confirmed occurrences. The spawn-context names `Supervisor: <name>` as a *fact* but carries no directive to report there; the worker bodies default to addressing the team-lead. Per Principle 4, every fix lands in the agent body **and** the spawn-context.

- **F7 — supervisor↔worker channel.** Edit `or-supervisor.md`: make explicit that the supervisor **can and must** DM workers directly (briefs and STATUS both), because workers are teammates; the manager **never** proxies worker I/O — it does not inject the brief and does not relay the report. This kills the "I can't talk to workers, so the manager must proxy" misconception that drove the severe F7 violation (the supervisor tried to make the manager a heavyweight relay for all 15 tasks). Reinforce in `supervisor-spawn-context.md`.
- **F13 — worker reporting target.** Add a directive to **every worker spawn-context** (`implementer-spawn-context.md`, `reviewer-spawn-context.md`): *"Report ALL status/findings to your SUPERVISOR (`<SUPERVISOR_NAME>`) via SendMessage — NEVER to the manager/team-lead."* Bake the same into all four worker bodies (`or-implementer`, `or-spec-reviewer`, `or-code-quality-reviewer`, `or-final-reviewer`). (The run proved this is not reviewer-specific — an implementer misrouted too.)
- **F19 — implementer role-boundary / reporting honesty.** Edit `or-implementer.md` (orchestration framing): *do NOT claim or perform verification outside your dispatched role — no browser/manual smoke checks; that is the supervisor's gate — and report only the work you actually performed.* (During the run an implementer claimed a browser smoke check its brief explicitly forbade.)
- **F24 — reviewer verdict self-evidence.** Edit the reviewer bodies and `reviewer-spawn-context.md`: *echo the task-id + the exact files-under-review (from the diff) at the top of your verdict; emit exactly ONE verdict message, no preamble.* This makes a wrong-task report (a reviewer once produced a confident, well-formatted review of the wrong task) self-evidently invalid. This is **reporting protocol** (orchestration), not review *criteria* (SDD's), so it belongs in our layer.
- **F26 — implementer commit discipline.** Edit `or-implementer.md` and `implementer-spawn-context.md`: *do NOT commit anything until your supervisor sends your task brief; the board task description is CONTEXT, not your assignment.* (During the run a fresh implementer committed — including an explicitly declined scope item — before its brief arrived, treating the ambient board task description as its assignment.)

**Files:** `plugins/claude-toolkit/agents/or-supervisor.md`, `or-implementer.md`, `or-spec-reviewer.md`, `or-code-quality-reviewer.md`, `or-final-reviewer.md`; `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/implementer-spawn-context.md`, `reviewer-spawn-context.md`, `supervisor-spawn-context.md`.

---

### Theme D — Manager purity & supervisor→manager economy (F25, F27, F4)

- **F25 — Conservation Rule #8 is a defect (test-director ruling).** Edit `manager-playbook.md` to **remove/rewrite Conservation Rule #8** ("cull idle workers aggressively"). The corrected invariant (Principle 1): the manager **never originates a teardown**; strays are tolerated as idle until the supervisor reaps them or the session ends. The teardown asymmetry is fixed at the source: edit `or-supervisor.md` so the **supervisor reaps the task implementer on gate-close**, symmetric with how it already reaps the reviewers (one extra SHUTDOWN per task). Update the playbook idle-taxonomy and Red-Flags rows so they describe a pure broker (the current "Cull idle workers" red-flag framing and any "idle ⇒ cull-signal" language must go; "worker idle ⇒ no action" is the correct rule).
- **F27 — supervisor→manager economy.** Edit `or-supervisor.md`: candidate findings and their detail go to `iteration-N.md`; the manager receives only a **one-line pointer** (e.g. "candidate finding logged in iteration-3.md §X"). Nothing verbose transits the manager (Principle 5). During the run the supervisor sent multi-paragraph finding write-ups straight into the non-refreshable manager context.
- **F4 — generic TaskCreate nudge (document-only).** Conservation Rule #1 already tells the manager to ignore the generic `TaskCreate` system reminder. Note it explicitly as a known harness limitation with **no plugin-side suppression** available. Minor; no behavioral change.

**Files:** `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`; `plugins/claude-toolkit/agents/or-supervisor.md`.

---

### Theme E — Phase-agent dialogue & flow (F2, F5, F6, F1)

- **F2 — generalize the preflight anti-relay fix to all user-facing teammates.** The prior cycle gave preflight an explicit "ask in your own pane, never relay" guarantee, but the phase-agent bodies say only "ask in plain text" without forbidding the relay channel — so the brainstormer relayed its first question through the manager. Edit `or-brainstormer.md`, `or-plan-writer.md`, and `or-finisher.md` to add: *ask the user directly in plain text in your own pane; NEVER SendMessage the manager your user-facing questions or ask it to relay.*
- **F5 — plan-writer owns the plan review + approval.** Edit `or-plan-writer.md` to make a **full plan walkthrough + explicit user approval** a required orchestration phase-gate **before** `PLAN_COMPLETE`. `superpowers:writing-plans` has no such step to defer to (verified — Principle 6), so this is the user-facing tier legitimately owning a phase-transition approval, **not** duplicating task methodology. Mirror the brainstormer's section-by-section + written-approval pattern. During the run the plan-writer self-reviewed and resolved open questions but never walked the user through the plan for approval.
- **F6 — drop the manager's redundant plan→implementation go-ahead gate.** On `PLAN_COMPLETE` (which, post-F5, *implies* user approval), the manager shuts the plan-writer down and spawns the supervisor **directly** — identical to mode `plan`. Edit `manager-playbook.md` (the `PLAN_COMPLETE` idle-taxonomy row, the "Plan→implementation go-ahead (the one gated transition)" subsection, and the Required-Communication-Style sanctioned-surfacings list) and `SKILL.md` (the Phase-2 flow line that currently calls the plan→impl transition "the one phase boundary the manager gates on the user's explicit go-ahead"). The plan-writer's closing turn becomes: *"Plan approved — implementation starts automatically; the supervisor runs autonomously."*

  **F5↔F6 coupling (state explicitly).** Auto-start is safe **only** because F5 guarantees `PLAN_COMPLETE` always carries user approval. The manager's separate gate only ever made sense under the broken assumption that the plan-writer did NOT review the plan with the user. **Net effect:** the single user-approval gate **relocates** from the manager to the user-facing plan-writer's own pane — it is not removed, just moved to the correct tier.
- **F1 — preflight one-question-at-a-time.** Edit `preflight-brief.md` Step 2 to sequence the setup questions one at a time (worktree name → wait → base branch → wait; mode-if-ambiguous, when it fires, is the third sequential question) and state the one-at-a-time rule explicitly. The current Step 2 instructs asking for *both* in one message.

**Files:** `plugins/claude-toolkit/agents/or-brainstormer.md`, `or-plan-writer.md`, `or-finisher.md`; `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`, `preflight-brief.md`; `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md`.

---

### Theme F — Handover / resume (F11, F21, F23, F28)

- **F11 — first-class `resume` invocation mode.** Add a `resume` mode: the manager recognizes a `manager-handover-*.md` path argument and branches **straight to Fresh-Manager-Resume, skipping preflight/Initial Setup** (the worktree and team already exist on a resume — there is nothing to set up, so no preflight teammate is spawned; this is the simplest correct path). The `manager-handover-template.md` header carries the copy-pasteable invocation `/claude-toolkit:or-superpowers-at-scale <abs-path-to-this-doc>` so the user just pastes it after `/clear`. Edit `manager-playbook.md` (the Mode Detection table + an Initial-Setup pre-check for a handover-path argument), `SKILL.md` (invocation modes), and `manager-handover-template.md` (header).
- **F28 (+F21) — capture the roster; cheap delta-check on resume.** The `manager-handover-template.md` captures the **enumerated live roster** at write time — one disposition line per member (keep / reap / zombie / live-worker) — as canonical and required (currently it has a "Workers (alive at handover)" table but the full-roster capture was ad-hoc). The Fresh-Manager-Resume protocol then does a **names-only delta-check**: Grep the member `name` fields from `~/.claude/teams/<team>/config.json` (a handful of lines) and diff against the captured roster — it does **not** full-read the verbose config. It reads full member detail **only for a delta** (a live member the handover didn't list, or a listed member now gone); that delta is exactly the orphan/zombie to reap. Edit `manager-playbook.md` ("Fresh manager resume" / "Reap orphans first") and `manager-handover-template.md`.

  **Why not just trust the captured roster:** F21/F23 proved config *lags reality* (handover assertions go stale). The capture cannot *replace* the live check — it only makes it **cheap**. The live names-only check stays mandatory.
- **F21 — reap-by-enumeration stays load-bearing.** Keep reap-by-enumeration exactly as-is — during the run it caught two real orphans the handover doc did not expect. Document the resume reap as **the one sanctioned manager-originated teardown** — an explicit, documented exception to Principle 1 (a dead session has no live supervisor to request the teardown). Edit `manager-playbook.md` to name this exception.
- **F23 — tolerate un-reapable zombies.** A handover-inherited in-process orphan can ignore `shutdown_request` (emit idle "available" instead of terminating; no force-terminate path exists in the harness). The successor manager **tolerates** it: at most **2 shutdown attempts, then stop**; treat the zombie's idle pings as idle (no spam); and **flag it in the next handover** so the next successor does not re-attempt. Harness-adjacent; document in `manager-playbook.md` Recovery.

**Files:** `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-handover-template.md`, `manager-playbook.md`; `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md`.

---

### Theme G — Reviewer/plan accuracy + the non-blocking question (F15, F16, F12)

This theme **shrinks under Principle 6** — most of it belongs to upstream superpowers skills, not our layer.

- **F15 — spec-reviewer false positive (reviewed plan wording, not the committed artifact).** The durable fix that is **ours** is orchestration: keep the supervisor's **independent per-commit source-verification** (review the committed artifact at HEAD before gating) as a required, documented step in `or-supervisor.md` — it is the backstop that caught the reviewer's confident false positive. The reviewer-side fix ("review the committed artifact at HEAD, not the plan's wording") is review **methodology** → it belongs to SDD's `spec-reviewer-prompt.md` (upstream), **not** our body. Note it as an optional upstream suggestion only.
- **F16 — plan-artifact defects (mislabeled comments / dead imports) propagating via faithful TDD.** This belongs to `writing-plans`' self-review (upstream); our layer already catches such defects at review (it did, twice). Optional upstream suggestion; **nothing** baked into our bodies.
- **F12 — non-blocking judgment calls (resolved: no new channel).** Add **one line** to `or-supervisor.md` and `manager-playbook.md`: non-blocking judgment calls are **decided-and-logged** to `iteration-N.md`, never relayed to the user. `PHASE_PAUSE` remains reserved for genuinely destructive / visible-to-others actions only. Phase 3 is autonomous — the supervisor does not need a `PHASE_QUESTION` channel; introducing one would invite exactly the manager-relay improvisation the rest of the skill eliminates.

**Files:** `plugins/claude-toolkit/agents/or-supervisor.md`; `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md` (+ optional upstream-suggestion notes, not code in this repo).

---

## 4. Principle-6 Audit (explicit deliverable)

A pass that strips any task-methodology from the `or-*` bodies and ensures each defers to its skill. This is a named deliverable so the plan schedules it, not an afterthought.

- **(a) Remove the parallel-reviewer override** from `or-supervisor.md` (Theme B) — it is a task-methodology override that fragmented under load.
- **(b) Reduce the reviewer bodies to orchestration-only.** `or-spec-reviewer`, `or-code-quality-reviewer`, and `or-final-reviewer` should contain only: worktree bind, report-to-supervisor (F13), echo task-id + files-under-review + one verdict message (F24), the STATUS vocabulary, and await-shutdown. The review **criteria** arrive in the supervisor's SDD-derived brief, so **strip any criteria prose** that duplicates SDD's reviewer-prompt templates (e.g. the spec-reviewer body's current "judge the implementation strictly against the task's spec requirements … report DONE if compliant" wording is criteria that SDD owns).
- **(c) Confirm the remaining bodies are invoke-skill-and-adapt only.** Audit `or-brainstormer`, `or-plan-writer`, `or-implementer`, and `or-finisher` for any task-methodology stragglers and strip them; their bodies should be STEP -1 bind → STEP 0 invoke-the-skill → the minimal orchestration adaptations.
- **(d) Confirm the new gates are framed as orchestration.** F5 (plan walkthrough/approval), F15 (supervisor source-verification), and F16 (plan-artifact accuracy) are framed as orchestration phase-gates / supervisor discipline / upstream suggestions respectively — **not** as task-method duplication. The reviewer self-evidence rule (F24) is reporting protocol, not criteria.

---

## 5. Behavioral Spike (the one load-bearing unknown)

Add **one** new behavioral spike, appended to `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` and run against the **installed** plugin (prior cutover-spike style):

> **Spike — turn-end threshold detection.** Verify that (1) the **manager's main-loop `Stop` hook fires under an inbox-wake** (not only on a real user keystroke); (2) the hook's `{"decision":"block","reason":...}` return on a ≥200k crossing **forces the handover turn**; and (3) `SubagentStop` delivers for background teammates (supervisor/phase agents/finisher/workers). Confirm the `stop_hook_active` guard + once-per-threshold state prevent re-blocking loops.

**Contingency note (state in the spec, do not design now):** hook-only detection **for the manager** is contingent on facet (1) passing. The user chose hook-only delivery precisely to avoid the context-spam of proactive self-tracking, so **the fallback is deliberately not designed here.** If the spike fails, the fallback would need revisiting in a follow-up — but `SubagentStop`-based detection for all *teammate* tiers stands regardless (it is well-documented), so even a manager-`Stop` failure leaves the supervisor/phase-agent/finisher detection intact.

---

## 6. F1–F28 Coverage Table

Every finding appears exactly once. **Layer** marks harness-level items (the fix is documentation + a supervisor/manager workaround, because the root cause is the Claude Code harness, not this repo) and non-actionable items.

| # | Finding (short) | Theme | Disposition | Primary file(s) | Layer |
|---|-----------------|-------|-------------|-----------------|-------|
| F1 | Preflight should ask one question at a time | E | fix | `preflight-brief.md` | ours |
| F2 | Phase agent relays user-question through manager | E | fix | `or-brainstormer.md`, `or-plan-writer.md`, `or-finisher.md` | ours |
| F3 | (positive) fix-forward nudge worked | A (Principle 4) | no-op | — | non-actionable |
| F4 | Generic `TaskCreate` reminder nudges manager | D | document | `manager-playbook.md` | harness |
| F5 | Plan-writer didn't review plan with user | E | fix | `or-plan-writer.md` | ours |
| F6 | Plan→impl should auto-start on approved `PLAN_COMPLETE` | E | fix | `manager-playbook.md`, `SKILL.md` | ours |
| F7 | Supervisor tries to make manager a worker-I/O proxy | C | fix | `or-supervisor.md`, `supervisor-spawn-context.md` | ours |
| F8 | Supervisor skips two-stage review unless nudged | B | fix | `or-supervisor.md` | ours |
| F9 | Manager hit 200k at Task 2 (test-scribe inflated) | A | no-op | — | non-actionable |
| F10 | Manager offered a handover menu instead of auto-executing | A | fix | `manager-playbook.md` | ours |
| F11 | No first-class resume trigger after manager handover | F | fix | `manager-playbook.md`, `SKILL.md`, `manager-handover-template.md` | ours |
| F12 | No first-class supervisor→user non-blocking question | G | fix (decide-and-log; no new channel) | `or-supervisor.md`, `manager-playbook.md` | ours |
| F13 | Worker routes report to manager not supervisor | C | fix | `implementer-spawn-context.md`, `reviewer-spawn-context.md`, all four worker bodies | ours |
| F14 | Board auto-completes a task on worker exit | B | document | `or-supervisor.md`, `manager-playbook.md` | harness |
| F15 | Spec-reviewer false-positive from plan wording | G | fix (supervisor source-verify) + upstream suggestion | `or-supervisor.md` | ours (+upstream) |
| F16 | Plan-artifact defects propagate via faithful TDD | G | upstream suggestion only | — | upstream |
| F17 | Briefed supervisor still skipped stage-2 review | B | fix (structural SPAWN/SHUTDOWN guard) | `or-supervisor.md` | ours |
| F18 | Manager idle-discipline drifts over long session | A | fix (fixed detection + one named line) | `manager-playbook.md` | ours |
| F19 | Implementer claimed forbidden out-of-scope verification | C | fix | `or-implementer.md` | ours |
| F20 | Threshold self-monitoring FAILED for manager + supervisor | A | fix | `context-usage.py`, `hooks.json`, `manager-playbook.md` | ours |
| F21 | Resume found orphans the handover didn't expect | F | fix (keep enumeration; name the one sanctioned teardown) | `manager-playbook.md` | ours |
| F22 | WHY F20: hook starved of UserPromptSubmit/PostToolUse | A | fix | `context-usage.py`, `hooks.json` | ours |
| F23 | Inherited in-process zombie ignores `shutdown_request` | F | document (successor tolerance) | `manager-playbook.md` | harness |
| F24 | Reviewer emitted confident wrong-task report | C | fix | reviewer bodies, `reviewer-spawn-context.md` | ours |
| F25 | Manager = pure broker; Conservation Rule #8 is a defect | D | fix | `manager-playbook.md`, `or-supervisor.md` | ours |
| F26 | Implementer committed before/beyond its brief | C | fix | `or-implementer.md`, `implementer-spawn-context.md` | ours |
| F27 | Supervisor sends verbose summaries to manager | D | fix | `or-supervisor.md` | ours |
| F28 | Handover should capture roster for a cheap delta-check | F | fix | `manager-handover-template.md`, `manager-playbook.md` | ours |

**Tallies:** 22 fix · 3 document (F4, F14, F23 — all harness-layer) · 3 no-op/upstream-only (F3, F9 non-actionable; F16 upstream-only). Harness-layer: F4, F14, F23. Non-actionable: F3, F9. Upstream-only: F16 (F15 is partly upstream but has an ours fix).

---

## 7. File-Change Manifest (target end-state)

No files are created or deleted; this remediation edits existing files only.

**Hook layer (Theme A):**
- `plugins/claude-toolkit/hooks/hooks.json` — register the hook on `Stop` + `SubagentStop` (in addition to the existing two events).
- `plugins/claude-toolkit/hooks/context-usage.py` — handle the two turn-end events; return `decision:block` for actionable (≥threshold) crossings on turn-end; keep `additionalContext` for the informational checkpoint on the existing events; preserve once-per-threshold + reset; add the `stop_hook_active` loop guard.

**Skill assets:**
- `…/assets/manager-playbook.md` — F10 (mandatory auto-handover + no-menu + forbid the "no reminder ⇒ under threshold" inference), F18 (one idle-drift line), F25 (remove/rewrite Conservation Rule #8; idle-taxonomy + Red-Flags rows → pure broker), F4 (document the nudge limitation), F14 (board-auto-complete note), F6 (`PLAN_COMPLETE` row + drop the go-ahead subsection + communication-style list), F11 (Mode Detection table + resume pre-check), F21 (name the one sanctioned teardown), F23 (zombie-tolerance in Recovery), F28 (cheap delta-check in Fresh-Manager-Resume), F12 (decide-and-log line).
- `…/assets/manager-handover-template.md` — F11 (header with copy-pasteable resume invocation), F28 (canonical enumerated-roster capture with a disposition per member).
- `…/assets/preflight-brief.md` — F1 (Step 2 one-question-at-a-time).
- `…/assets/implementer-spawn-context.md` — F13 (report-to-supervisor directive), F26 (do-not-commit-until-briefed directive).
- `…/assets/reviewer-spawn-context.md` — F13 (report-to-supervisor directive), F24 (echo task-id + files-under-review + one verdict).
- `…/assets/supervisor-spawn-context.md` — F7 (supervisor DMs workers directly; manager never proxies).

**Agent bodies:**
- `agents/or-supervisor.md` — F8/F17 (remove the parallel-review override → canonical SDD; add the SPAWN/SHUTDOWN sequencing guard), F14 (re-assert `in_progress`), F25 (reap the implementer on gate-close), F27 (terse pointer; detail → `iteration-N.md`), F15 (keep source-verification), F12 (decide-and-log), F7 (DM workers directly), Principle-6 (remove override).
- `agents/or-implementer.md` — F13 (report to supervisor), F19 (no out-of-scope verification claims), F26 (don't commit before the brief).
- `agents/or-spec-reviewer.md`, `agents/or-code-quality-reviewer.md`, `agents/or-final-reviewer.md` — F13 (report to supervisor), F24 (echo task-id + files + one verdict), Principle-6 (orchestration-only; strip criteria prose).
- `agents/or-brainstormer.md`, `agents/or-plan-writer.md`, `agents/or-finisher.md` — F2 (ask in own pane, never relay); `or-plan-writer.md` additionally F5 (plan walkthrough + approval gate) and F6 (closing turn → auto-start wording); Principle-6 audit pass.

**Skill entry point:**
- `…/SKILL.md` — F6 (Phase-2 flow line no longer calls the plan→impl transition a gated boundary), F11 (document the resume invocation mode).

**Validation:**
- `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` — append the turn-end-detection spike (Section 5).

**Manifests:**
- `plugins/claude-toolkit/.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — version bump (number chosen at implementation time).

---

## 8. Build Sequencing (guidance for plan-from-design)

1. **Theme A first (the headline + the only spike).** Land the hook changes and run the turn-end-detection spike against the installed plugin; the manager-`Stop` facet gates whether hook-only manager detection is final. The playbook F10/F18 edits accompany it.
2. **Principle-6 audit + Theme B together.** Removing the parallel-review override (audit item a) and adding the SPAWN/SHUTDOWN guard are the same edit region in `or-supervisor.md`; the reviewer-body strip (audit item b) pairs with Theme C's reviewer directives.
3. **Themes C, D, E, F** are largely independent doc/body edits; sequence by file to minimize churn (e.g. all `or-supervisor.md` edits — B/C/D/G — in one pass; all `manager-playbook.md` edits — A/D/E/F/G — in one pass).
4. **Theme G** is small (one supervisor line + one playbook line + optional upstream notes).
5. **Version bump** last, in both manifests.
6. Validate with `claude plugin validate` (plugin + marketplace) as the prior cycle did.

---

## Appendix — Leftover housekeeping (NOT part of this spec)

These are test-run artifacts to be cleared separately; they are flagged here so they are not forgotten and are **out of scope** for this remediation:

- 3 stray `breakout-*.png` files at the repo root (clutter from the E2E run).
- The `breakout-game` branch + its worktree (`.claude/worktrees/breakout-game`) — a throwaway test vehicle, deliberately left unmerged.
- The F23 `task12` zombie + the `breakout-game` team in `~/.claude/teams/` — throwaway test artifacts.
