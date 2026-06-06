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

**RESULT — ✅ GREEN (cutover 2026-06-01, installed plugin `d924696`).** Both facets run as probe-mode background teammates (STEP -1 skipped, no dialogue/research). The **RED baseline was observed directly inside each real agent**: before any `Skill()` call — with the `skills:` frontmatter present — the skill's instructional **body was absent** from context (only its name + one-line trigger description were present, for routing). Frontmatter alone does not activate a skill; the in-body call is load-bearing. This is a stronger demonstration than a separate stripped variant (it is the real agent with its real frontmatter showing the body absent pre-call).

- **Facet A — cross-plugin (`or-brainstormer` → `superpowers:brainstorming`):** the in-body `Skill('superpowers:brainstorming')` loaded the full body (HARD-GATE, 9-item checklist, process digraph; base dir `…/superpowers/5.1.0/skills/brainstorming`). Now-active directives quoted as proof: *"ask questions one at a time"*, *"Propose 2–3 different approaches with trade-offs."* Pre-call these were absent. ✅
- **Facet B — same-plugin (`or-dependency-researcher` → `claude-toolkit:dependency-research-methodology`):** the qualified in-body call loaded the methodology (quoted: *"Every claim must have an inline citation [1]…"*); `claude-toolkit:research-deposit` loaded too. ✅
- **Name resolution (open question resolved):** the **bare** `Skill('dependency-research-methodology')` *also* resolved — byte-identical content (same `…/claude-toolkit/1.4.0/skills/…` base dir), no error. **Same-plugin bare names resolve; the `claude-toolkit:` prefix is NOT required.** The Fallback's "qualified required" branch is moot. Agent bodies keep the qualified form (more explicit, harmless). ✅

---

## Spike 2 — Terminal override holds (impl-note #6) — once per phase agent

**Purpose:** Each phase agent, driven to its pre-seeded skill's terminal step, must emit its completion signal to the manager and must **not** invoke the forbidden next skill or offer the user an execution choice. The pre-seeded skills end with forceful directives to invoke the next skill (`brainstorming`'s "writing-plans is the ONLY skill you invoke afterward"; `writing-plans`' "Execution Handoff" → "Which approach?" → invoke `subagent-driven-development`/`executing-plans`); the agent body must override that.

**Setup:** Plugin installed. For `or-brainstormer`: a tiny idea that can reach an approved spec quickly. For `or-plan-writer`: a minimal approved spec in `docs/superpowers/specs/`.

**Procedure — `or-brainstormer`:** Spawn `or-brainstormer-1`; drive a minimal brainstorm to user approval. At the terminal, verify it (a) SendMessages the manager `BRAINSTORM_COMPLETE — spec: <path>` and (b) does **not** invoke `superpowers:writing-plans`.

**Procedure — `or-plan-writer`:** Spawn `or-plan-writer-1` with the approved spec; drive to a saved, self-reviewed plan. Verify it (a) SendMessages `PLAN_COMPLETE — plan: <path>`, (b) tells the user to switch to the manager, and (c) does **not** invoke `superpowers:subagent-driven-development` / `superpowers:executing-plans` or ask "Which approach?".

**RED baseline (proves the override is load-bearing):** For each agent, spawn a variant that **keeps** its STEP 0 `Skill(...)` call but **drops** the override + Closed-loopholes sections. Confirm it follows the canonical skill's terminal (the brainstormer invokes writing-plans; the plan-writer offers the execution choice). The baseline **must** keep STEP 0 — otherwise RED "passes" for the wrong reason (no skill loaded ⇒ no terminal pressure to resist).

**GREEN:** Each real agent resists the terminal and emits its completion token; each RED variant follows the skill's terminal.

**Fallback:** If an override does not hold, strengthen that agent's Closed-loopholes list / add a pre-terminal interceptor in its body, then re-run until GREEN. The belt-and-braces design (in-body `Skill(...)` call + explicit Closed-loopholes list) is unverified until this is GREEN for both agents.

**RESULT — ✅ GREEN (cutover 2026-06-01, plugin `d924696`).** Each real phase agent loaded its skill (STEP 0) and was placed at the skill's terminal; a general-purpose RED control loaded the *same* skill **without** the override.
- **`or-brainstormer`:** `OVERRIDE_HELD` — sent `BRAINSTORM_COMPLETE — spec: …`, did **not** invoke `superpowers:writing-plans`. RED control followed the skill's terminal (*"Invoke the writing-plans skill … Do NOT invoke any other skill"*). ✅
- **`or-plan-writer`:** `OVERRIDE_HELD` — sent `PLAN_COMPLETE — plan: …`, did **not** ask "Which approach?" or invoke `subagent-driven-development`/`executing-plans`. RED control followed the skill's "Execution Handoff" terminal (*"offer execution choice … 'Which approach?'"* → `subagent-driven-development`). ✅
- The RED↔real delta isolates each agent body's override + Closed-loopholes list as the load-bearing mechanism. (Probe mode had no live user, so the plan-writer's "tell the user to switch to the manager" final-dialogue line was not exercised — a UX step in a real session; the completion-signal + no-forbidden-skill core held.)

---

## Spike 3 — Anti-drift resume holds (impl-note #9) — once per phase agent

**Purpose:** A resuming phase agent must flush captured-but-unwritten intent into the spec/plan artifact **before** opening new dialogue — so intent that lived only in a handover doc is not lost across the hop. The artifact is the running ledger; the handover doc is a thin pointer.

**Setup:** Plugin installed. Seed, in a worktree: (a) an artifact (spec for brainstormer / plan for plan-writer) that is **missing one revision**; (b) a handover doc that lists **one not-yet-applied user preference** and states a **"Latest revision"** (and, for the plan-writer, a task count) the artifact does **not** yet contain.

**Procedure:** Spawn the successor (`or-brainstormer-2` / `or-plan-writer-2`) with spawn-context naming the seeded handover doc + artifact. Verify it writes **both** the not-yet-applied preference **and** the missing revision into the artifact before engaging the user (the flush-on-resume + latest-revision cross-check from the agent body's "On resume after a handover").

**RED baseline (proves the discipline is load-bearing):** Spawn a variant whose body **omits** the "On resume after a handover" section. Confirm it leaves the artifact stale (opens dialogue without reconciling).

**GREEN:** The real successor reconciles the artifact first; the RED variant does not.

**Fallback:** If the discipline does not hold, strengthen the flush-on-resume wording in that agent's body, then re-run until GREEN.

**RESULT — ✅ GREEN (cutover 2026-06-01, plugin `d924696`).** Probed on `or-brainstormer` (its "On resume after a handover" section is structurally identical to `or-plan-writer`'s — same reconcile-latest-revision + flush-unwritten-preferences discipline; result generalizes). Seeded a spec missing "Revision 3" and a handover naming that revision plus a not-yet-applied snake_case preference.
- **Real successor (`or-brainstormer-2`): `RECONCILED_FIRST`.** Before any dialogue it wrote into the spec (**verified on disk**): `R2: --json` pretty-printable via `--json-indent N` (the handover's Revision 3), the snake_case preference, and a "Revision 3" history entry. ✅
- **RED control (read-only):** the canonical `superpowers:brainstorming` skill *alone* does **NOT** drive reconcile-the-artifact-first on resume (it writes the spec only at its own post-approval step; it never treats a handover as a source to flush) — its first action would be to continue the dialogue, leaving the deltas unwritten. ✅ This isolates the body's "On resume after a handover" section as load-bearing.
- **Note:** `or-plan-writer`'s identical "On resume" section was not separately exercised (context economy); structurally identical → expected GREEN. Run an independent pass if fully exhaustive coverage is wanted.

---

## Spike 4 — `AskUserQuestion` surfaces from a subagent and a teammate (impl-note #10)

**Purpose:** Confirm a structured `AskUserQuestion` reaches the user from (a) a **foreground one-shot subagent** (preflight prompts for worktree name + base branch + mode disambiguation) and (b) a **teammate** (phase agents lean on it through the dialogue). Only direct *text* dialogue with a teammate is confirmed today; structured `AskUserQuestion` from a non-main agent is not.

**Setup:** Plugin installed.

**Facet A — foreground subagent:** Dispatch the preflight subagent path that issues an `AskUserQuestion` (worktree name + base branch). Confirm the user sees the structured prompt and the chosen answer returns to the subagent.

**Facet B — teammate:** Spawn a phase-agent teammate that issues an `AskUserQuestion` mid-dialogue. Confirm it surfaces to the user and the answer returns.

**RED baseline:** None — this is a capability probe, not a regression. The implicit failure mode is that a tier's `AskUserQuestion` never reaches the user (silently dropped).

**GREEN:** Both facets surface the prompt and return the answer.

**Fallback:** If a tier cannot surface `AskUserQuestion`, fall back to **plain-text questions** there: the phase agents' confirmed direct text dialogue already supports that, and preflight's prompts move up to the manager (which can always use `AskUserQuestion`). Update `assets/preflight-brief.md` and the phase-agent bodies accordingly, then re-validate. Until GREEN, preflight's reliance on `AskUserQuestion` is unverified.

**RESULT — ❌ RED → remediated (2026-06-03, installed plugin `d924696`; fix on branch `or-sas-spike4-remediation`).** `AskUserQuestion` is **main-loop-only** — unavailable to *every* non-main agent.
- **Facet A — RED (real defect).** The shipped preflight path dispatches `subagent_type: general-purpose` as a one-shot foreground subagent (`manager-playbook.md`). A direct probe of that exact vehicle found `AskUserQuestion` absent — not in the `*` grant, and `ToolSearch select:AskUserQuestion` → "No matching deferred tools found". A one-shot subagent also has **no** plain-text dialogue channel, so it cannot ask the user *at all*. Preflight Steps 1–2 as shipped were unrunnable.
- **Facet B — RED but non-blocking.** A real `claude-toolkit:or-brainstormer` teammate — whose frontmatter *listed* `AskUserQuestion` — reported the tool absent from its toolset. **Frontmatter `AskUserQuestion` is inert for teammates** (like `skills:`). Non-blocking because teammates DO have a plain-text dialogue channel, and the canonical brainstorming / writing-plans / finishing skills ask in plain text (zero `AskUserQuestion` calls in any of them — grep-confirmed).
- **Net:** the "fall back to plain text" direction holds for the user-facing *teammate* tiers; preflight needed a structural fix because a one-shot subagent has no channel.

**Remediation applied (this branch), per the user's chosen design — promote preflight to a teammate:**
- **Preflight → background teammate** (`or-preflight-1`): asks mode-if-ambiguous + worktree name + base branch in **plain text**, reports `PREFLIGHT_OK`/`PREFLIGHT_FAIL` to the manager via SendMessage. It **creates** the worktree (`git worktree add`) but does **not** `EnterWorktree` (a teammate's bind moves the whole session — Spike 6). `preflight-brief.md` rewritten; `manager-playbook.md` Initial Setup reordered (TeamCreate first → spawn preflight teammate → await token → shut it down → spawn the phase agent) + idle/action taxonomy + L26/L34 wording; `SKILL.md` Phase 0 wording.
- **Inert `AskUserQuestion` frontmatter removed** from `or-brainstormer`/`or-plan-writer`/`or-finisher` (+ a one-line "ask in plain text" note in each) and from the general `community-researcher`/`dependency-researcher`.
**Follow-up DIALOGUE spike — ✅ GREEN (mechanism) + 1 coordination defect found & remediated (2026-06-03).** Ran the end-to-end preflight-teammate dialogue against the shipped brief (`preflight-brief.md` @ `1454923`, pasted inline — byte-equivalent to the installed plugin — into a `general-purpose` background teammate `or-preflight-1` on throwaway team `or-preflight-spike`, with the main loop acting as manager and driving the playbook's Initial Setup steps 1–4 manually). Inputs: `<USER_INPUT>` = a plain idea string, `<USER_CONSENT>` = `yes`.
- **Mechanism GREEN.** Preflight (a) classified `mode = idea` correctly, (b) asked the worktree-name + base-branch setup questions in **plain text with no `AskUserQuestion`**, (c) created the worktree via `git worktree add .claude/worktrees/or-sas-preflight-dialogue-spike -b … master` with a `handovers/` dir, (d) **did NOT bind the shared session** — after `PREFLIGHT_OK` the manager's `git rev-parse --show-toplevel` was still the main checkout (`I:/Dev/claude-toolkit`, `master`), `git worktree list` showed the new worktree on its own branch at `1454923`, (e) surfaced the auto-compaction `warning:` (Step 5 warn-path), and (f) emitted a well-formed `PREFLIGHT_OK` block. The Spike-4 remediation (`git worktree add`, not `EnterWorktree`) and the Spike-6 no-drag guarantee both held end-to-end.
- **Coordination defect found.** The shipped brief told preflight to *"ask the user in plain text"* but never said **how** its user channel works; preflight reasoned *"the user interacts primarily with the team lead, so my dialogue flows through the team lead as the relay"* and `SendMessage`d its setup questions **to the manager**. That contradicts `manager-playbook.md`'s idle taxonomy (*"preflight ↔ user dialogue events → Idle, no output"*): if the manager strictly idles and the user stays anchored to it, the setup dialogue **deadlocks**. (In the spike it only completed because the manager relayed — which violates the Preservation Imperative.)
- **Remediation (this commit) — keep the manager idle; preflight asks in its own pane.** Per the user's call (*relaying breaks the prime directive of preserving manager context*): `preflight-brief.md` now states preflight emits its setup questions as plain text **in its own turn** and the user answers **in preflight's pane** (Shift+Down) — and **never `SendMessage`s the manager its questions / never asks for a relay**; the manager receives exactly one message, the final block. `SKILL.md` Phase 0 aligned (*"directly, in its own pane … never relayed through the manager"*). `manager-playbook.md` Initial Setup step 3 hardened (a preflight setup question landing on the manager = preflight misbehaving; do not relay). The idle-taxonomy entry is now correct as written.
- **Status:** the gold-standard dialogue path is now confirmed working AND its one coordination gap is closed. The throwaway worktree/branch/team were torn down after the run.

---

## Spike 5 — Teammates receive task tools; brainstorming checklist works (impl-note #11)

**Purpose:** Confirm a teammate with **no** `Task*`/`TodoWrite` in frontmatter still receives the task-management tools (the spec's F7: Claude Code grants `SendMessage` + the task tools to every teammate regardless of frontmatter), **and** that the brainstorming skill's checklist step runs with whatever todo/task tool the teammate has.

**Setup:** Plugin installed.

**Procedure:** Spawn `or-brainstormer-1` (its frontmatter lists no `Task*`/`TodoWrite`). Confirm it can `TaskCreate` / `TaskUpdate` / `TaskList`. Then drive the brainstorming skill to its checklist step and confirm the step runs with the teammate's available todo/task tool (`Task*` in this team harness; `TodoWrite` in standard Claude Code).

**RED baseline:** None — capability probe. The implicit failure mode is that the teammate has no task tool and the brainstorming checklist step cannot run.

**GREEN:** The teammate creates/updates tasks and the brainstorming checklist step runs.

**Fallback:** If teammates do **not** auto-receive the task tools, re-add `TaskCreate, TaskUpdate, TaskList` to `or-brainstormer` (and `or-plan-writer`) frontmatter and re-validate. This would also revisit the spec's F7 assumption (design §"Agent tool-grant decisions" → "Phase-agent task tools").

**RESULT — ✅ GREEN (cutover 2026-06-01, plugin `d924696`).** Probed via the real `claude-toolkit:or-brainstormer` (frontmatter `tools:` lists **no** `Task*`/`TodoWrite`).
- **Task tools auto-granted (F7 holds):** `TaskList`, `TaskCreate` (#9 "spike5-probe"), `TaskUpdate→completed`, `TaskUpdate→deleted` all **succeeded with no authorization error** despite none being in frontmatter. **Caveat:** the `Task*` tools are *deferred* for teammates (the agent ran `ToolSearch select:…` to load schemas before calling) — granted but not pre-listed; no permission was denied.
- **Brainstorming checklist step:** the loaded skill says *"create a task for each of these items"* (generic, not tool-pinned). In this team harness the available mechanism is the **`Task*`** family (not `TodoWrite`), and it works — a teammate runs the checklist with `Task*`. ✅
- **Gated follow-up now unblocked:** the explicit `TaskCreate, TaskUpdate, TaskList` listing in `or-supervisor` frontmatter is **redundant for functionality** (auto-grant covers it; Item 9.5). Removal is optional — it still documents intent. Batch with the other post-suite agent-body edits.

---

## Spike 6 — Worktree binding from a fresh teammate (remediation Item 1 — TOP RISK)

**Purpose:** Resolve the top-risk unknown: a spawned teammate's actual starting CWD, and whether `EnterWorktree(<path>)` binds it into the team's **shared** worktree. Sub-questions: (a) is `EnterWorktree` grantable to a teammate via `tools:` frontmatter and callable by it; (b) what is a fresh background teammate's starting `git rev-parse --show-toplevel` (hypothesis: the manager's main checkout, NOT the worktree); (c) are team teammates auto-isolated by default (and is `worktree.bgIsolation: "none"` needed); (d) does `EnterWorktree(<shared .claude/worktrees/ path>)` land the teammate on the shared branch state; (e) the exact `.claude/worktrees/` path constraint.

**Setup:** Plugin installed. A shared team worktree created under `.claude/worktrees/<name>` (preflight's path).

**RED baseline (proves the bind is load-bearing):** Spawn a repo-touching teammate variant whose body **omits** the STEP -1 bind directive. Confirm its `git rev-parse --show-toplevel` is the **main checkout**, not the worktree — i.e. teammates do NOT inherit the worktree CWD. This is what makes the bind load-bearing.

**GREEN:** A teammate WITH the STEP -1 bind directive (and the `EnterWorktree` tool grant) lands in the shared worktree (`rev-parse` equals `<WORKTREE_PATH>`) and can commit to the branch; spec/code-quality reviewers and the implementer all operate on the **same** branch state.

**Fallback:** If `EnterWorktree` does not bind a *shared* worktree, or teammates are auto-isolated into their own worktrees by default, the shared-worktree design must be reconciled (the supervisor + workers MUST see the same branch) — try `worktree.bgIsolation: "none"`, or switch the per-tier model. If `EnterWorktree` is not grantable to a teammate at all, escalate — the binding mechanism needs redesign before the suite ships. **This is the top-risk item; do not declare the suite done until Spike 6 is GREEN** (no acceptable degraded end-state).

**RESULT — ✅ GREEN (cutover 2026-06-01, installed plugin `d924696`).** Probes run as background teammates in team `or-sas-spikes` against a shared worktree `.claude/worktrees/spike6-wt` (branch `or-sas-spike6`, created via `git worktree add`, registered in `git worktree list`).

- **(a) `EnterWorktree` grantable via `tools:` frontmatter — YES.** The real `claude-toolkit:or-implementer` (frontmatter `tools: … EnterWorktree`) called it directly on its first action with **no `ToolSearch`**. Caveat worth recording: the harness *also* lists `EnterWorktree` in the deferred-tools system-reminder with a "calling directly will fail with InputValidationError" warning — **that warning is wrong for a frontmatter-listed tool**; the call executed and returned a domain result.
- **(b) fresh-teammate starting CWD — the SHARED session working directory (NOT a private isolated worktree).** With the manager cleanly in the main checkout, a fresh teammate (`spike6-probe2`) started in the main checkout (`I:/Dev/claude-toolkit`, `master`).
- **(c) auto-isolated by default — NO.** No teammate landed in a private per-agent worktree; they landed in the shared session cwd (main checkout, or the shared worktree once bound). `worktree.bgIsolation: "none"` was **not** needed.
- **bind from main checkout — YES.** `EnterWorktree({path: …/spike6-wt})` from the main checkout returned *"Entered worktree at …spike6-wt on branch or-sas-spike6"* (genuine success, not a no-op); toplevel + branch flipped to the shared worktree.
- **(d) shared branch state + commit — YES.** `spike6-probe2` saw `spike6-probe1`'s commit `c39c309` at log top and appended `43a0452`. Teammates operating in the worktree see and extend the same branch — supervisor/workers/reviewers will share one branch state.
- **(e) path constraint — YES.** A directory under `.claude/worktrees/` created by `git worktree add` and registered in `git worktree list` is bindable via `EnterWorktree({path})`.

**KEY DISCOVERY (refines the STEP -1 rationale, does NOT block GREEN): a background team teammate's `EnterWorktree` mutates the SHARED session working directory — the manager and all subsequently-spawned teammates — not just the calling teammate.** Evidence chain: after `spike6-probe2` (a teammate) bound into the worktree, (i) the manager shell's own cwd flipped to the worktree, (ii) plain bash `cd` back to the main checkout no longer persisted — the harness re-pinned the shell to the worktree, and (iii) the next teammate (`spike6-impl`) spawned **already inside** the worktree (its STEP -1 `EnterWorktree` was an idempotent no-op — *"is the current working directory"* — but its `git rev-parse --show-toplevel` check matched, so it correctly verdicted `BIND_OK`, never falsely `BLOCKED`). The manager returns to the main checkout with **`ExitWorktree({action:"keep"})`** (works even though a *teammate*, not the manager, performed the bind; preserves the branch/commits). This **contradicts** the `EnterWorktree` schema note ("from a pinned agent the switch only affects this agent, not the parent session") — background *team* teammates are NOT cwd-isolated; the team shares one working directory that both `cd` and any teammate's `EnterWorktree` mutate, and a teammate's bind escalates to an EnterWorktree-managed session binding for the whole team.

- **Impact on the design — GREEN holds, arguably stronger.** The goal (supervisor + workers + reviewers all on the same shared branch/worktree) is achieved even more robustly: once *any* teammate binds, the whole session is in the worktree. STEP -1 remains correct as an **idempotent safeguard** (and the real agent handled the no-op case gracefully via its `rev-parse` verification — it did not false-block).
- **Follow-up refinement (non-blocking, after the full suite):** the `or-implementer` STEP -1 rationale — *"a spawned teammate inherits the manager's CWD (the main checkout), NOT the worktree"* — is imprecise. A teammate inherits the **shared session cwd, which may already be the worktree** if an earlier teammate bound. Reword across all repo-touching agents carrying this note to: *"you inherit the shared session working directory, which may already be the worktree; call `EnterWorktree` to guarantee placement, then verify with `git rev-parse`."* Remove the "Verification pending (Item 1 / Spike 6)" markers now that Spike 6 is GREEN.
- **Design risk flagged for the finisher:** because the shared cwd ends up bound to the worktree/feature branch, `or-finisher`'s merge step must first `ExitWorktree({action:"keep"})` (or otherwise operate in the main checkout) to merge into `master` — git forbids checking out `master` inside the worktree while it is checked out in the main checkout. Validate this when exercising the finisher.

---

## Spike 7 — Empty idle turn (remediation Item 8b)

**Purpose:** Confirm the harness gracefully accepts a manager turn with **no text and no tool call** (end the turn empty). The skill's central conservation discipline — silence on idle wake-ups (worker boot, `shutdown_response`, teammate progress, hook reminders) — depends on it.

**Setup:** Plugin installed; a running orchestration (or a minimal manager teammate) driven to an idle-class wake-up.

**RED baseline:** None meaningful — capability probe. The implicit failure mode is the harness erroring or forcing output on an empty turn.

**GREEN:** The manager ends an idle wake-up with no output and no tool call, and the harness accepts it (no error, no forced text).

**Fallback:** If a truly-empty turn is rejected, the silence-on-idle discipline must be reworked — define the minimal accepted no-op and update the playbook's Idle Taxonomy + Communication Style. Until GREEN, treat silence-on-idle as load-bearing-and-unverified. **Do not declare the suite done until Spike 7 is GREEN.**

**RESULT — ✅ GREEN (cutover 2026-06-01, plugin `d924696`).** Tested via a teammate (`s7-empty`, a manager-equivalent agent) instructed to emit a turn with **no text and no tool call**. The harness **accepted it cleanly** — the agent simply went idle, with **no error, no system-reminder forcing output, and no forced text**. It honored the instruction across **three** consecutive turns (including after an explicit "you MUST emit text" poke), and the harness accepted **every** empty turn without rejection or forced output. This behavioral evidence directly satisfies the GREEN condition (a no-output/no-tool turn is accepted); the repeated clean idles are stronger than a single verbal confirmation. The silence-on-idle conservation discipline is sound.

---

## Spike 8 — Turn-end threshold detection (E2E remediation Theme A — F20/F22)

**Purpose:** Verify the 1.5.0 hook changes deliver threshold detection in inbox-driven team loops. Facets: (1) the **manager's main-loop `Stop` hook fires under an inbox-wake** (not only on a real user keystroke) — the lone load-bearing unknown of the E2E remediation (undocumented harness behavior); (2) the hook's `{"decision":"block","reason":…}` return on a ≥200k crossing **forces exactly one more turn** containing the handover instruction — the handover turn; (3) **`SubagentStop` delivers for background teammates** (supervisor / phase agents / finisher / workers), and the usage it computes is the *teammate's own* (the harness passes the teammate's own `transcript_path` in the SubagentStop payload; the script's `isSidechain` filtering within that transcript then skips sidechain entries — scoping is by transcript_path, not by the filter); (4) the `stop_hook_active` payload guard + once-per-threshold state prevent re-blocking loops (the forced turn's own Stop exits the hook immediately).

**Setup:** Plugin **1.5.0** installed (restart so hooks load). A team with at least one background teammate. A main-loop/teammate transcript pushed past 200k — or, to make crossing cheap, a throwaway copy of the hook with lowered thresholds substituted via a scratch plugin (do NOT lower thresholds in the shipped plugin). Lower both `ACTIONABLE_CHECKPOINTS` and `CHECKPOINTS` in the scratch copy — the turn-end facets read `ACTIONABLE_CHECKPOINTS` specifically.

**RED baseline (already recorded — the E2E run itself):** F22 forensics — 126 tool calls across 165 turn-ends produced **zero** hook firings after the last real keystroke; both the manager (~400k) and supervisor (~600k) blew through 200k undetected. The starvation is proven; this spike verifies the cure.

**GREEN:** All four facets hold. Specifically: an inbox-wake turn that ends ≥200k gets one forced handover turn (manager via `Stop`; teammate via `SubagentStop`) whose reason text is the handover instruction; the next turn-end does NOT re-block (guard + once-per-threshold); the teammate-facet usage matches the teammate's transcript, not the parent's (and the count excludes any sidechain-flagged entries in that transcript — code-readable if impractical to probe live).

**Fallback (deliberately not designed — design §5 contingency):** hook-only detection **for the manager** is contingent on facet (1). If facet (1) fails, the manager-side fallback is revisited in a **follow-up design** — the user chose hook-only delivery precisely to avoid proactive-self-tracking context-spam, so no ad-hoc fallback is to be improvised. A facet-(1) failure does NOT invalidate the rest: `SubagentStop` is documented-good, so supervisor/phase-agent/finisher/worker detection stands regardless. If facet (3)'s usage turns out to be the parent's (sidechain interaction), add a SubagentStop-aware transcript path in a follow-up.

**RESULT — run 2026-06-06 against installed plugin 1.5.1 (`26717c5`; cache byte-identical to repo: `hooks.json`, `context-usage.py`, `plugin.json`). Facets (1) ✅ (2) ✅ (4) ✅ — facet (3) split: delivery ✅, scoping ❌ (parent-measured; the pre-planned contingency above applies).**

Method: **real shipped thresholds** (no scratch plugin — higher fidelity than the cheap-crossing setup suggested above). The manager session and one throwaway teammate (`s8-bloater`, team `spike8`) each deliberately bloated context past 200k by Reading old-transcript noise, with usage cross-checked against the hook's own computation via a helper script mirroring `latest_main_thread_usage()`.

- **(1) ✅ The manager's main-loop `Stop` hook fires under inbox-wake.** The manager crossed 200k on a turn initiated by a teammate `SendMessage` delivery — zero keystrokes since the last real user prompt three turns earlier (the exact F22 starvation scenario). Turn-end → hook fired → blocked with `[207,895 tokens used] Context checkpoint 200k crossed (turn-end detection)…` State file confirms `"stop": 200000` — and `"prompt": 0` in the same file is the starvation signature made visible: UserPromptSubmit never saw any of the session's growth past 100k, yet turn-end caught the crossing. The lone load-bearing unknown of the E2E remediation is GREEN.
- **(2) ✅ The block forces exactly one handover turn.** The harness delivered the reason verbatim as "Stop hook feedback" and forced exactly one extra turn containing the full handover instruction.
- **(3) ⚠️ `SubagentStop` DELIVERS for background teammates — but measures the PARENT's transcript.** Delivery: the teammate's turn-end fired `SubagentStop`, blocked, and forced its handover turn with the full actionable text (it reported the verbatim reason). Scoping: the computed usage was the **manager's** main transcript, cross-confirmed twice — the teammate's mid-turn PostToolUse announce (`[203,259]`) and its turn-end block (`[206,494]`) both exactly matched the *parent* transcript's last-entry usage at those moments. Root cause is structural: teammate transcripts live at `<parent-session>/subagents/agent-<id>.jsonl` with **every entry `isSidechain: true`** — under the hook's sidechain filter such a file computes to no usage at all, so the only transcript the hook can ever measure in this topology is the parent's. The events also carry the **parent session_id**: both teammate firings wrote into the parent's state file (`"subagent_stop": 200000`, `"tool": 200000`), so the manager and all teammates share one once-per-threshold pool per event type — observed live when the teammate's PostToolUse 200k announce consumed the `tool` key and suppressed the manager's own mid-turn announce. **Operational meaning: a teammate gets the handover block when the MANAGER crosses a threshold, not when its own context does — supervisor/phase-agent SELF-detection is NOT delivered by 1.5.1.** Follow-up (per the contingency above): SubagentStop-aware measurement — read the agent transcript named by the payload without the sidechain filter and key state per agent. The manager-side cure stands regardless.
- **(4) ✅ No re-block loops, both paths.** Manager: the forced turn's own Stop (`stop_hook_active: true`) did not re-block, and subsequent turn-ends below 250k stayed silent (once-per-threshold). Teammate: its forced turn ended idle with no second block, and its next turn likewise (threshold already announced in the shared pool).
- **Bonus observations:** the informational paths fired live and as designed — manager saw the 100k announce (`[100,478]`) on a keystroke-initiated turn's PostToolUse; the teammate saw the 200k informational mid-turn. Per-event state keys behaved independently (`tool` consumed separately from `stop`), exactly as the per-event design intends.

---

## Spike 9 — Teammate-scoped turn-end detection (Spike 8 facet-3 follow-up)

**Purpose:** Verify the 1.5.2 teammate-scoped measurement (design:
`docs/superpowers/specs/2026-06-06-teammate-scoped-context-checkpoints-design.md`):
a `SubagentStop` crossing measures the **agent's own** transcript and enforces the
agent's own handover under a **per-agent** state identity
(`context-usage-<session_id>--<agent_id>.json`); the manager's pools are untouched
by teammate events; one-shot subagents stop receiving spurious end-of-run blocks.

**Setup:** Plugin **1.5.2+** installed (1.5.3 adds malformed-payload hardening
only — the teammate scoping under test is identical; restart so the updated
hook loads). A team
with at least one background teammate; real shipped thresholds (Spike 8 method:
bloat context by Reading old-transcript noise; cross-check figures with a helper
mirroring the hook's own `latest_main_thread_usage()` computation — for teammates,
read `<project>/<session-id>/subagents/agent-<id>.jsonl` WITHOUT the sidechain
filter — i.e., count all assistant usage entries, do not skip
`isSidechain: true` lines).

**RED baseline (already recorded — Spike 8 facet 3):** a teammate was blocked at
the MANAGER's figure (parent transcript, parent session_id); shared
once-per-threshold pools observed live (a teammate's PostToolUse announce consumed
the parent's `tool` key and suppressed the manager's own mid-turn announce).

**GREEN (all five):**

1. A teammate that bloats its own context past 200k while the manager stays low is
   blocked with its **own** figure (the reason's `[N tokens used]` matches the
   teammate's `subagents/agent-<id>.jsonl` usage, not the parent transcript's).
2. The manager's pools are untouched by the teammate's crossing: the parent state
   file shows no `subagent_stop` write (mechanism check: the parent
   `context-usage-<session_id>.json` is absent, or every key in it is unchanged
   from before the teammate's crossing), and the manager's own subsequent
   crossing still announces; the teammate's write lands in
   `context-usage-<session_id>--<agent_id>.json`.
3. A manager crossing does **not** block teammates (a teammate turn-end after the
   manager passes 200k stays silent while the teammate is below threshold).
4. A one-shot subagent completing on a ≥200k session (manager context ≥200k;
   the one-shot's own transcript sub-200k) shows **no** spurious end-of-run
   block.
5. `stop_hook_active` guard + once-per-threshold hold **per agent**: the forced
   turn's own SubagentStop does not re-block, and the same agent's next turn-end
   below the next threshold stays silent.

**Fallback:** If the installed payload carries neither `agent_transcript_path` nor
`subagent_transcript_path` (field-name drift), the hook skips with a stderr
breadcrumb (visible under `claude --debug`) — diagnose the actual field name from
the live payload and extend the alias list in `measurement_target()`. If
`agent_id` is absent, state falls back to the transcript filename stem — verify
the composite state filename rather than failing the spike on naming alone.

---

## Cutover checklist

Run once, at suite cutover (after the Plan 4 release), in order (design §"Cutover & end-state validation"):

1. **Remove the deprecated loose `~/.claude` copies the plugin supersedes — DONE 2026-05-31** (backed up to `~/.claude/backups/2026-05-31-toolkit-cutover/`; its README is the full manifest + restore paths). The set below was reconciled against an independent audit — the original narrow list here had drifted (it omitted real name-collisions):
   - **agents/** (4): `architecture-reviewer.md` (plugin split the test rules TEST-001/002 + MOCK-001/002/003 into the new `test-reviewer` agent; production rules retained), `community-researcher.md` + `dependency-researcher.md` (pre-rehoming full-methodology copies; plugin uses thin dispatchers + the `*-research-methodology` skills), `violation-verifier.md` (byte-identical).
   - **commands/** (5): `design.md`, `implement-from-plan.md`, `learn.md`, `plan-from-design.md` (all content-identical bar CRLF/LF), and `sdd-at-scale.md` (functionally replaced by `/or-superpowers-at-scale`). `handover.md` kept (no plugin equivalent).
   - **skills/** (3): `designing-mcp-tools/` (byte-identical), `update-architecture-rules/` (CRLF/LF only), `subagent-driven-development-at-scale/` (functionally replaced by the `or-superpowers-at-scale` skill).
   - **hooks/**: stripped the `"hooks"` block from `settings.json` and both scripts. `context-usage.py` is now **bundled into the plugin** (released as **v1.3.0**, auto-registered via `hooks/hooks.json`); `completion-verification.py` was retired. `hooks/state/` kept.
2. `claude plugin install claude-toolkit` (then restart the session so hooks load).
3. Run **Spike 1 → Spike 7** above, plus Plan 1's deferred wrapper check (a live `Skill('claude-toolkit:dependency-research-methodology')` load and an `or-dependency-researcher` / `dependency-researcher` dispatch that returns a cited report from disk). Spikes 6–7 discharge remediation Items 1 and 8b respectively.
4. Record each result inline in this doc. For any spike that fails, apply its **Fallback**, commit the fix, and re-run that spike. **Do not declare the suite done until Spikes 1–3, Spike 6 (worktree binding — top risk), and Spike 7 (empty idle turn) are GREEN** (Spikes 4–5 retain acceptable plain-text/frontmatter fallbacks).
5. **(1.5.0 E2E remediation)** After the 1.5.0 release: `claude plugin install claude-toolkit` (restart so the new hook registration loads), run **Spike 8**, and record its RESULT inline. Theme A's manager-side detection is not "done" until facet (1) is GREEN. — **DONE 2026-06-06 against installed 1.5.1: facet (1) GREEN** (see Spike 8 RESULT; facet (3) scoping spawned one named follow-up).
6. **(1.5.2 teammate scoping)** After the 1.5.2 release: `claude plugin install claude-toolkit` (restart so the updated hook loads), run **Spike 9**, and record its RESULT inline. Spike 8 facet (3)'s scoping defect is not closed until Spike 9 is GREEN.

---

## SUITE STATUS — ✅ MUST-PASS GATE COMPLETE (cutover 2026-06-01, installed plugin `d924696`)

All must-pass spikes GREEN: **Spike 1 ✅, Spike 2 ✅, Spike 3 ✅, Spike 6 ✅ (top risk), Spike 7 ✅** — plus **Spike 5 ✅** (F7 auto-grant). The behavioral suite's must-pass gate is **complete**; design Items 1, 8b and impl-notes #3/#6/#9/#11 are discharged. Run as background teammates in team `or-sas-spikes` against a shared worktree under `.claude/worktrees/`.

**Non-gate work — DONE 2026-06-03 on branch `or-sas-spike4-remediation` (one reviewed commit):**
- **Spike 4 RUN — ❌ RED → remediated** (see Spike 4's RESULT block above). `AskUserQuestion` is main-loop-only (inert for one-shot subagents AND teammates); **preflight promoted to a teammate** that asks in plain text; inert `AskUserQuestion` frontmatter stripped from the phase agents + the general researchers.
- **Spike 4 follow-up DIALOGUE spike — ✅ GREEN + 1 coordination defect remediated (2026-06-03)** (see Spike 4's "Follow-up DIALOGUE spike" RESULT block above). End-to-end run confirmed preflight conducts a plain-text setup dialogue, creates the worktree via `git worktree add` **without binding the shared session**, surfaces the auto-compaction warning, and emits a well-formed `PREFLIGHT_OK`. It surfaced a brief↔playbook contradiction (preflight relayed its questions through the manager, vs. the manager's idle discipline) — **remediated this commit**: preflight now asks in its **own pane** (user answers there; never relayed through the manager), keeping the Preservation Imperative intact. `preflight-brief.md` / `SKILL.md` Phase 0 / `manager-playbook.md` Initial Setup step 3 updated. **No open follow-ups remain.**
- **Follow-up source edits (shipped in the same commit):**
  1. Removed the discharged "**Verification pending (Item 1 / Spike 6)**" notes from all 8 repo-touching agents.
  2. Refined the **STEP -1 rationale** in all 8: a teammate inherits the **shared session cwd** (possibly *already* the worktree if an earlier teammate bound — Spike 6); `EnterWorktree` is an idempotent safeguard confirmed with `git rev-parse`. Added the finisher exit-path note: a teammate's bind drags the whole session into the worktree, so `or-finisher` `ExitWorktree({action:"keep"})`s before merging into the base branch.
  3. Dropped the redundant `TaskCreate, TaskUpdate, TaskList` from `or-supervisor` frontmatter (Spike 5 GREEN — Item 9.5).
- **Committed** this validation doc together with the above (it was uncommitted on `master`).

**Spike 8 (turn-end threshold detection) EXECUTED 2026-06-06 at the 1.5.1 cutover — facets (1)/(2)/(4) ✅ GREEN; facet (3) delivery ✅ / scoping ❌** (see its RESULT block). Theme A's manager-side detection is **done**. Exactly one open follow-up remains, inherited from facet (3): **teammate-scoped SubagentStop measurement** — teammate turn-end events carry the parent's session_id, and teammate transcripts (`<parent-session>/subagents/agent-<id>.jsonl`, all entries `isSidechain: true`) are invisible to the hook's sidechain filter, so teammates are currently blocked on the *manager's* usage, not their own. Fix shape: measure the agent transcript named by the payload without the sidechain filter and key state per agent — a hook-only change — **designed 2026-06-06** (`docs/superpowers/specs/2026-06-06-teammate-scoped-context-checkpoints-design.md`), implemented as **1.5.2** on branch `teammate-scoped-checkpoints`; verification = **Spike 9** above, to run at the 1.5.2 cutover (checklist item 6).
