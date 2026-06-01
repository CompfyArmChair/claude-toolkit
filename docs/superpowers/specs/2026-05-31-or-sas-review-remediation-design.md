# or-superpowers-at-scale — Review & Remediation Design

**Date:** 2026-05-31 (design walk completed 2026-06-01)
**Status:** Design complete — awaiting user review gate, then `writing-plans`.
**Scope:** Consolidated remediation of 11 review findings (Items 0–10) plus one foundational restructure, for the `claude-toolkit:or-superpowers-at-scale` skill.
**Version target:** plugin `1.3.0 → 1.4.0` (batch-level bump; no CHANGELOG file — versioning is via release commits).

---

## 1. Background & Approach

A full review of the `or-superpowers-at-scale` skill (SKILL.md, all assets, all 9 `or-*` agents, the upstream `superpowers:subagent-driven-development` (SDD), the validation doc, and the manifests) surfaced 11 findings. We walked each finding to an agreed approach in a "design all, then build" loop; this document consolidates those approaches into one spec. After the user review gate it goes to `superpowers:writing-plans`, then build on a feature branch off `master`.

**Three findings (Items 1, 8, 10) are runtime-behavior concerns that land as design + a tracked TODO + a behavioral spike**, because they depend on Claude Code harness behavior that is undocumented and must be verified at live install. All other items are doc/code edits that land in the build.

**Skill identity recap.** `or-superpowers-at-scale` orchestrates the full superpowers workflow in one session (brainstorm → plan → implement) across a tiered team: a non-refreshable **manager** (parent Claude) that only brokers spawns/teardown and relays at transitions; refreshable **phase agents** (`or-brainstormer`, `or-plan-writer`) the user talks to directly; a refreshable **supervisor** (`or-supervisor`) that runs SDD; and disposable **workers** (`or-implementer`, `or-spec-reviewer`, `or-code-quality-reviewer`, `or-final-reviewer`) + one-shot **research agents**. The Core Principle is that **manager context is sacred** (the only non-refreshable tier).

---

## 2. Foundational Restructure (the spine — Item 5 folds in here)

**Decision: Option A.** Split the single oversized `SKILL.md` into a lean entry point + a manager-only playbook, and make `spawn-protocol.md` the single source of the SPAWN mechanics.

- **`SKILL.md` (lean, ~700 words):** overview + Core Principle + When/When-not + the Topology table + the Phase flow + a **Map** whose **first line is an imperative telling the manager to Read the playbook**.
- **`assets/manager-playbook.md` (new, manager-only):** Initial Setup (incl. the Item 0 Input subsection), Broker Protocols (incl. the **canonical SHUTDOWN** handshake, which lives nowhere else), Idle Taxonomy, Communication Style, Conservation Rules, Handover Ladder, Recovery, Red Flags.
- **`assets/spawn-protocol.md`:** becomes the **sole** copy of the SPAWN + SPAWN_RESEARCH mechanics (resolves **Item 5** — the de-dup). `SKILL.md`/playbook keep only the canonical SHUTDOWN.

**Honest framing (do not lose this):** the split does **not** shrink the *manager's* own context footprint — it loads lean-SKILL + playbook ≈ the same total. The real wins are: maintainability/cohesion; **teammates stop loading the manager playbook** just to fetch a shared asset (saving on *refreshable* contexts); and killing the SPAWN duplication. The real cost: it adds a load-bearing "manager must Read the playbook" step — mitigated by making the SKILL.md Map's first line an explicit imperative to read it.

**Loader model (why this is safe):** `Skill(...)` loads the full SKILL.md body into the *invoking* agent. Loaders are: manager once; supervisor ≥1 (needs the iteration template); brainstormer/plan-writer 0–1; +1 per handover successor. Implementers/reviewers/researchers never load it. So ~2–4 loads/run, and only the manager pays for the playbook.

---

## 3. Remediation Items

(Item 5 is covered by the restructure in Section 2; Items 1, 8, and 10 are deferred-to-verify in Section 4 — hence the numbering below skips them.)

### 3.1 Item 0 — Command → user-invocable skill
- Delete `commands/or-superpowers-at-scale.md` (a pure wrapper).
- Add `user_invocable: true` to `SKILL.md` frontmatter (mechanism confirmed via `skills/update-architecture-rules/SKILL.md`).
- **Keep the rich "Use when…" description** — `user_invocable` is independent of description format; do **not** downgrade to a `/cmd - short` form.
- Add an explicit **Input** subsection (in the playbook's Initial Setup) defining `<USER_INPUT>` (the `/`-arg: an idea, a spec path, a plan path, or empty) and `<USER_CONSENT>` (**default "no"**).
- Update `README.md` lines 25/33/53 to reflect the skill (not command) entry point.

### 3.2 Item 2 — Ship step via a dedicated Phase 4 finisher
Shipping is currently homeless: `SKILL.md` claims the supervisor invokes `superpowers:finishing-a-development-branch` after the final iteration, but `or-supervisor.md` never wires it in, and the phase flow lists only Phases 0–3. `finishing-a-development-branch` is interactive (merge/PR/cleanup) while the supervisor is non-user-facing.

**Decision: add a real Phase 4 — Ship, run by a dedicated user-facing `or-finisher` agent** (symmetric with the brainstormer/plan-writer).
- New agent **`or-finisher`** (opus, background teammate, pre-seeded `superpowers:finishing-a-development-branch`).
- Flow: on `ITERATION <N> — COMPLETED`, the manager shuts the supervisor down and spawns `or-finisher-1` (with `finisher-spawn-context.md` substituted: branch / base / worktree / plan / iteration-doc paths). The finisher runs `finishing-a-development-branch` in **direct dialogue** (merge/PR/cleanup; push/PR done directly — no PAUSE needed, it *is* user-facing), then signals **`SHIP_COMPLETE`**; the manager shuts it down and ends the session.
- New asset **`assets/finisher-spawn-context.md`**; new token **`SHIP_COMPLETE`**.
- Topology table + Idle Taxonomy + Handover Ladder gain an `or-finisher` row (phase-agent-class: user-facing, 150k handover — the handover doc is unlikely to ever trigger but kept for symmetry; confirm whether a `finisher-handover-template.md` is worth bundling during planning).
- Phase flow becomes **Phases 0–4** ("up to five phases").
- Correct the false `SKILL.md` claim (ship is Phase 4 via `or-finisher`, **not** supervisor-invoked). The supervisor is otherwise unchanged except it drops the claim to invoke finishing.

### 3.3 Item 3 — Document the TodoWrite → Task* adaptation
SDD instructs `TodoWrite`; the supervisor has `Task*` (`TaskCreate`/`TaskUpdate`/`TaskList`) — the team-harness-native task mechanism (granted to every teammate via the spec's **F7**; standard Claude Code SDD uses `TodoWrite`). The supervisor says "follow SDD verbatim" but cannot for task tracking.

**Decision:** in `or-supervisor.md`'s "One adaptation, one override" block, make all SDD deviations explicit (heading → "Adaptations & override"):
1. *(adaptation, existing)* SDD "dispatch subagent" → the SPAWN protocol (no `Agent` tool).
2. *(adaptation, new)* SDD `TodoWrite` → `Task*` (team-harness-native; F7 auto-grant).
3. *(override)* SDD sequential reviewers → parallel, spec-gated (Item 7).

The manager-side cost (Task* is team-shared, so the manager sees task system-reminders) is **already handled** by Conservation Rule 1 + the Recovery note ("ignore; the supervisor owns the TaskList") — no new work.

### 3.4 Item 4 — PHASE_ABORT to the phase agent + allowlist restructure
**Unifying principle: mid-phase user interactions belong to the phase agent; phase-*transition* surfacings belong to the manager.**
- **(a) PHASE_ABORT (mid-phase) → phase-agent-owned.** The phase agent confirms the abort directly in its own dialogue ("this ends the whole session; your spec/plan so far is saved at `<path>` — confirm?"), then emits `PHASE_ABORT`. The manager's handling (`SKILL.md:214`) becomes purely mechanical — shut the phase agent down, end the session — **no surfaced confirm, no pane-switch**. Update `or-brainstormer.md:127–135` and `or-plan-writer.md` "Abort path".
- **(b) Communication-Style allowlist** (`SKILL.md:240–250`): replace the flat "the ONLY situations" list — which is contradicted by required utterances it omits — with **two explicit categories**:
  - *Routine protocol replies:* `Spawned` / `Research … done` / `Acknowledged`|`On track` / `Standing by` / PAUSE relay / redirect nudge.
  - *Sanctioned transition & lifecycle surfacings:* the single first-session message + the plan→impl go-ahead (line 219) + the 200k handover notice (line 292) — each **cross-referencing its governing section** so wording isn't duplicated.
  - "Silent mid-phase" still holds (every sanctioned surfacing is at a transition). The plan→impl go-ahead **stays with the manager** (a genuine transition); only abort moves.

### 3.5 Item 6 — Structured `PHASE_PAUSE` token for the supervisor
The phase agents emit a structured `PHASE_PAUSE` (`action:` / `impact:` fields, awaiting `PROCEED` / `REJECTED — reason: <line>`); the supervisor's PAUSE is prose only, so the manager's idle-taxonomy row hedges "`PHASE_PAUSE` / PAUSE".

**Decision:** give the supervisor the **same** structured `PHASE_PAUSE` token (one PAUSE token across all depth-1 tiers; no supervisor-specific token — the manager handles them identically). Idle-taxonomy row collapses to just "`PHASE_PAUSE`". Update `or-supervisor.md` Topology Discipline 6 (line 131) from prose to the explicit token.
- **Interaction with Item 2:** routine end-of-branch push/PR/merge is now Phase 4 (finisher), so the supervisor's PAUSE triggers **narrow** to unusual *mid-implementation* visible actions (an external API call; a plan task that explicitly pushes/deploys/publishes; deletes outside the worktree). Clean split: Phase 3 supervisor = local-commits-only (PAUSE only for the unusual); Phase 4 finisher = integration in user-facing dialogue.

### 3.6 Item 7 — Parallel review with a preserved spec-gate
SDD's flowchart makes spec review a hard gate (code-quality reviewer dispatched only after spec passes). The supervisor's parallel override had a non-sequitur justification and risked the code-quality reviewer reviewing stale (about-to-change) code.

**Decision: keep parallel, but fix it.**
- Honest rationale: **wall-clock latency** (parallel reviewers are cheap in this team topology; both finish in the time of the slower one).
- **Preserve SDD's gate by moving it from dispatch-order to which-result-counts:**
  - *Spec passes* (common, esp. post-TDD) → the concurrent code-quality result was looking at spec-compliant code → **valid**, act on it (one round-trip saved).
  - *Spec fails* → this round's code-quality result is potentially **stale** → **discard it**; relay spec-fixes, re-run spec review, and once it passes dispatch a **fresh** code-quality review (`-rev<K>`, which the worker-naming convention already supports) on the now-compliant code.
- Guarantee: code-quality findings never apply to code about to change (same correctness as SDD's sequential gate); the only cost is wasted compute on a spec-failure round (uncommon).
- Stays the supervisor's **one override**; `or-supervisor.md:46–53` becomes "two adaptations [SPAWN, Task*], one override [parallel review, spec-gated]" with the rationale + gate rule spelled out.

### 3.7 Item 9 — Polish batch
1. **Orphaned-worker reaping on resume:** extend the "Fresh manager resume" Recovery protocol to enumerate *all* members in `~/.claude/teams/<team>/config.json` and `shutdown_request` any orphaned workers (not just the active depth-1 tier) before spawning the successor.
2. **`or-<topic>-researcher-N` naming:** keep as a **documented phase-agent-side convention** (used when composing the `SPAWN_RESEARCH NAME`); **no manager-side enforcement** (the manager spawns with whatever `NAME` it is given).
3. **Backticks `SKILL.md:136–138`:** all three first-session messages contain `` on team `<name>`. `` — the backtick before `<name>` closes the code span early. Rewrite each as one clean span with a non-backtick placeholder (e.g. `<TEAM>`).
4. **`or-` prefix:** expand once at first use — "(the `or-` prefix = *orchestrator*)" — in the Architecture/Topology section.
5. **Frontmatter consistency:** **keep** the supervisor's explicit `Task*` listing as belt-and-suspenders and document that phase agents rely on the F7 auto-grant; **defer any removal until the F7 spike runs** (Item 10) — removing now would lean on unverified F7 behavior.

---

## 4. Deferred-to-verify items & the spike suite

These three land as **design + a tracked TODO in the build + a behavioral spike**; the design is settled, the empirical confirmation happens at live-install cutover.

### 4.1 Item 1 — Worktree binding (top risk) — via harness-native `EnterWorktree`
Today only the brainstormer/plan-writer spawn-contexts carry the worktree path; the supervisor + workers don't, and no tier has a directive to enter the worktree — yet all assert they're "checked out in the worktree." A spawned teammate most likely inherits the manager's CWD (the main checkout). The Claude Code docs confirm **"subagent sessions never carry over working directory changes"** — so a `cd`-based binding is unreliable.

**Design (harness-native):**
- Every repo-touching tier calls **`EnterWorktree(<WORKTREE_PATH>)`** as its first action, then verifies `git rev-parse --show-toplevel` matches, **before** invoking its skill (the pre-seeded skills assume CWD = repo). This replaces the rejected `cd` directive.
- Create the shared worktree under **`.claude/worktrees/<name>`** to satisfy the `EnterWorktree` path constraint.
- Add `Worktree: <WORKTREE_PATH>` to every repo-touching spawn-context (supervisor + workers + finisher; phase agents already have it). The manager substitutes it (it holds the path from `PREFLIGHT_OK` and across the manager-handover template). The **manager itself never binds** — it never touches the repo.

**Open → resolved by the spike (4.4):** the default isolation behavior of team teammates (`worktree.bgIsolation: "none"` exists as an opt-out → background sessions *may* be auto-isolated by default); whether `EnterWorktree(path)` works from a fresh teammate into a *shared* worktree; the exact `.claude/worktrees/` constraint; and whether the preflight keeps `superpowers:using-git-worktrees` (creating under `.claude/worktrees/`) or switches to harness-native creation. The shared-worktree-for-a-team scenario is **undocumented**.

### 4.2 Item 8 — Auto-compaction knob + empty-idle-turn verification
- **(a) Auto-compaction:** documented to fire at **~95% of the context window** by default, configurable via **`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`**. The risk is window-size-coupled: on a 1M-window model 95% ≈ 950k (far above the 150k/200k handover thresholds — safe); on a 200k-window model 95% ≈ 190k → it would **pre-empt the manager's 200k handover** with lossy compaction. **Design:** document/require running the orchestration with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` set high/disabled so every tier reaches its handover threshold first (consistent with the handover-not-compact philosophy for *all* tiers); the preflight can check/warn. Do **not** assume a 1M window.
- **(b) Empty idle turns:** whether the harness gracefully accepts a truly-empty turn (no text, no tool call) is **undocumented** — and the skill's central conservation discipline (silence on idle: `SKILL.md:203/217/250/313`) depends on it. Keep the intent but flag it as **load-bearing and unverified**; the spike must confirm it. If unsupported, the core discipline needs rethinking.

### 4.3 Item 10 — Execute the behavioral spikes at cutover
The Spike 1–5 suite (`docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`) is well-designed with RED baselines but **authored, not executed** (no GREEN recorded; cutover steps 2–4 unticked). Execute it at live-install cutover and record results.

### 4.4 New spikes to add
- **Worktree-binding spike (Item 1):** verify the actual starting CWD of a fresh background teammate; whether team teammates are auto-isolated by default (and whether `worktree.bgIsolation:"none"` is needed); whether `EnterWorktree(<shared path>)` binds a teammate into the shared worktree; and the `.claude/worktrees/` constraint. **No current spike covers this.**
- **Empty-idle-turn spike (Item 8b):** verify the harness accepts a turn with no output and no tool call.
- **(The F7 spike already exists** and gates the Item 9.5 frontmatter cleanup.)

---

## 5. File-change manifest (target end-state)

**Create:**
- `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md` (restructure)
- `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/finisher-spawn-context.md` (Item 2)
- `plugins/claude-toolkit/agents/or-finisher.md` (Item 2)

**Edit:**
- `…/skills/or-superpowers-at-scale/SKILL.md` — lean rewrite (restructure); Phase 0–4 flow + topology/idle/handover rows for `or-finisher` (Item 2); allowlist restructure + PHASE_ABORT mechanical handling (Item 4); `PHASE_PAUSE` collapse (Item 6); backticks + `or-` prefix + reaping (Item 9); Item 0 `user_invocable` + Input; correct the finishing-a-development-branch claim.
- `…/assets/spawn-protocol.md` — becomes the sole SPAWN/SPAWN_RESEARCH copy (Item 5/restructure).
- `…/assets/{supervisor,implementer,reviewer}-spawn-context.md` — add `Worktree: <WORKTREE_PATH>` (Item 1).
- `…/assets/preflight-brief.md` — create the worktree under `.claude/worktrees/`; optional compaction check/warn (Items 1, 8).
- `agents/or-supervisor.md` — Adaptations & override block (Items 3, 7); structured `PHASE_PAUSE` + narrowed triggers (Item 6); `EnterWorktree` bind directive (Item 1); drop the finishing claim (Item 2).
- `agents/or-brainstormer.md`, `agents/or-plan-writer.md` — phase-agent-owned abort confirm (Item 4); `EnterWorktree` bind directive (Item 1).
- `agents/or-implementer.md`, `agents/or-spec-reviewer.md`, `agents/or-code-quality-reviewer.md`, `agents/or-final-reviewer.md` — `EnterWorktree` bind directive (Item 1).
- `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` — add the worktree-binding + empty-idle-turn spikes (Items 1, 8b, 10).
- `README.md` — lines 25/33/53 (Item 0).
- `plugins/claude-toolkit/.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` — version `1.3.0 → 1.4.0`.

**Delete:**
- `plugins/claude-toolkit/commands/or-superpowers-at-scale.md` (Item 0).

---

## 6. Build sequencing

1. **Restructure first** (Item 5 / spine): create `manager-playbook.md`, lean `SKILL.md`, `spawn-protocol.md` as sole SPAWN copy. The doc-level item fixes then land in the post-restructure files.
2. **Doc/code item fixes** (Items 0, 2, 3, 4, 6, 7, 9) into the new structure, plus the `or-finisher` agent + asset.
3. **Deferred-design items** (1, 8): land the `EnterWorktree` binding directives + spawn-context paths + the compaction-config documentation, each with a tracked TODO noting verification is pending the spike.
4. **Spikes** (Item 10): add the new spikes; execute the full suite at live-install cutover and record GREEN.
5. **Version bump** to 1.4.0 in both manifests.

Doc-level items merge on the feature branch; Items 1/8/10 are not "done" until the spikes pass at cutover.
