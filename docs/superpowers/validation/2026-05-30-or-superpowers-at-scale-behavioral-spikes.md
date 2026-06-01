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
