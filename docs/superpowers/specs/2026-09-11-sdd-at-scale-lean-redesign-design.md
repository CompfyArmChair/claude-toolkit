# SDD-at-Scale Lean Redesign - Design

Date: 2026-09-11. Repo: `claude-toolkit`, plugin `plugins/claude-toolkit`
(1.7.2 at `15ff9ca`). Status: design approved section by section in the
brainstorm (Martin, 2026-09-11); next step is `superpowers:writing-plans`.

Supersedes the or-superpowers-at-scale design (2026-05-24) and its two
remediation specs (2026-05-31, 2026-06-03). Extends the teammate-scoped
context checkpoints design (2026-06-06) from one event to every event.

Citations: `R:<n>` is a line of
`docs/research/2026-09-11-claude-code-hooks-current-state.md`; `K:<n>` is a
line of `docs/research/2026-09-11-spike-posttooluse-subagent-context.md`;
`S:<n>` is a line of the sub-agents docs deposit
`~/.claude/.claude/web-deposits/2026-09-11-code-claude-com-docs-en-sub-agents.md`
(the anchor R uses for the same file); `SDD` is the installed skill
`superpowers/6.3.0/skills/subagent-driven-development/SKILL.md`, cited by
section name.

## 1. Problem

Long implementation runs outlive one context window. The manual loop -
`/handover`, `/clear`, "resume" - works but costs Martin a round trip at
every 200k crossing, and the or-superpowers-at-scale orchestrator that
was built to remove it is ~2,000 lines across one skill, 13 assets and ten
agents. That size came from two premises that no longer hold:

- Agent nesting was capped at depth 1, so a manager had to broker every
  spawn (the SPAWN/SHUTDOWN handshakes, the flat team roster, the
  handover-doc ladder).
- SDD had no durable ledger, so every context loss needed a hand-written
  handover document.

SDD 6.3.0 has a ledger that is resumable by design (SDD "Setup": tasks
with a `Task <N>: complete` line are skipped; a task whose last line is a
fix round resumes at the next round; "trust the ledger and git log over
your own recollection"). Agent nesting is three levels deep (verified by
live probe on 2.1.269, 2026-09-11: main -> L1 with Agent -> L2 with Agent
-> L3 without). Both props under the old design are gone, so the design
goes too.

The one thing that was never solved is the trigger. Task cost is
unpredictable, so a token budget per task is a guess. The pause authority
must stay the context-usage hook, measuring real usage. Until now that
hook could only reach a subagent at the end of its wake (SubagentStop),
never while it worked - so a controller that runs a whole plan in one wake
could never be paused by it.

## 2. Rulings (all Martin, 2026-09-11)

- Scope is the implementation loop only. Brainstorm and plan phases keep
  their existing interactive commands.
- The pause authority is the context hook, extended, not a budget.
- Approach 1 (main session messages the controller once per task)
  rejected: "marginal gains". Approach 2 (a nested driver level sending
  one message per task) superseded by the spike finding below.
- Approach 3 approved: main -> one controller per plan -> SDD workers,
  one message per plan, the hook warning the controller mid-wake on its
  own transcript. Sections (a)-(f) of the design approved as written here,
  including the turn-end addendum in 5.1 and the pivot amendment in 5.4.

## 3. Verified facts the design rests on

Every load-bearing fact below was verified on Claude Code 2.1.269 on
2026-09-11, and each cites where the evidence lives.

1. PostToolUse fires inside subagents at depth 1 and depth 2, and its
   payload carries `agent_id` and `agent_type` while `transcript_path`
   names the MAIN session transcript (K:68-71).
2. The agent's own transcript is derivable as
   `<transcript stem>/subagents/agent-<agent_id>.jsonl`; it exists from
   the agent's first model turn on, not yet at spawn-time SubagentStart
   (K:70-74).
3. `additionalContext` returned by a PostToolUse hook that measured the
   agent's own transcript reaches the agent mid-wake, before its reply, at
   depth 1 and depth 2 (K:21-26, K:37-41, K:58-67). Delivery attached to a
   background Agent launch is shown too (K:58-65).
4. PostToolUse fires only after a tool call succeeds; a failed call fires
   PostToolUseFailure (R:28-29). The depth-1 probe missed three failed
   Reads for exactly this reason (K:50-57). Both events accept
   `hookSpecificOutput.additionalContext` (hooks docs, PostToolUseFailure
   decision control).
5. PostToolUse fires once per tool even inside a parallel batch;
   PostToolBatch fires once per batch (R:30, hooks docs PostToolBatch).
6. No hook event fires while an agent idles waiting on a background child;
   there is no background-completion event (R:68). SubagentStop is
   turn-end only: a block's reason reaches the agent as one forced turn
   whose own SubagentStop carries `stop_hook_active: true`.
7. SubagentStop carries `agent_id`, `agent_type`, `agent_transcript_path`,
   `last_assistant_message`, `stop_hook_active` (R:57, K:76-78).
8. SubagentStart and SubagentStop matchers take the agent type, including
   plugin-scoped names such as `^my-plugin:reviewer$` (R:73). Plugin
   subagents ignore the `hooks` frontmatter field (S:404, S:463), so a
   controller-specific hook must live in the plugin's hooks.json.
9. An unnamed subagent spawned by the Agent tool returns a task
   notification whose result is its last reply; the spawner can resume it
   by SendMessage to its agent id, and it keeps its transcript memory
   across that resume (live probes, 2026-09-11, recorded in the
   brainstorm notes). Named agents form a flat roster and cannot spawn
   named children; not used here.
10. A general-purpose subagent in this environment starts at ~61k tokens
    because its system prompt carries the full MCP tool roster (K:81-83).
    The Read tool refuses a single call over 25,000 tokens (K:50-53).
11. SDD 6.3.0 stops for exactly four reasons - an irreversible or
    destructive operation, a security-sensitive action, a side effect
    outside the worktree that norms say you ask about first, and a plan
    so broken that every path forward is a guess - and rules on everything
    else, recording each ruling in the ledger (SDD, opening "Rulings, not
    stalls"). Its workspace script derives the repo root from the current
    directory (`git rev-parse --show-toplevel`, `scripts/sdd-workspace`
    line 35).

## 4. Architecture

Principle: **one agent runs the whole plan, the hook decides when it
stops, and the ledger is the only state that has to survive.** Everything
else follows. There is no manager, no broker, no handover document, no
per-task messaging, and no token budget.

Topology (three levels, one inside the verified limit):

```
main session (driver: /implement-from-plan)
  |  one unnamed spawn per controller life: PLAN + ROOT
  v
claude-toolkit:sdd-controller (runs superpowers:subagent-driven-development)
  |  SDD's own dispatches: implementer, spec reviewer, quality reviewer,
  |  fix subagents, final reviewer
  v
workers (unnamed, one-shot)
```

Data flow:

- Driver -> controller: the spawn prompt (`PLAN`, `ROOT`), and on a
  STOPPED question, one resume message (`RULING`).
- Controller -> driver: its final message, a status line (section 6),
  delivered as the task notification's result. No SendMessage upward.
- Hook -> controller: `additionalContext` on PostToolUse and
  PostToolUseFailure measured on the controller's own transcript; the
  SubagentStop block as the turn-end backstop.
- Durable state: SDD's ledger at `<ROOT>/.superpowers/sdd/<plan>/progress.md`
  (written by whichever controller life is running), git history, and the
  driver's run record `.claude/sdd-run.json`.

A run's life:

1. Driver resolves the plan, establishes ROOT (worktree or in place),
   writes the run record, spawns controller life 1.
2. The controller runs SDD from the ledger's current position.
3. At the 200k crossing the hook warns it mid-wake. It reaches the next
   ledger write, dispatches nothing new, replies `PAUSED`. The driver
   spawns life 2 with the identical prompt; SDD's Setup resumes it at the
   first incomplete task or round. Repeat as needed.
4. A stop case ends the wake with `STOPPED`. The driver asks Martin,
   resumes the same life by agent id with `RULING`; the controller
   ledgers the ruling and continues.
5. The last life runs SDD's final review, compiles the report, deletes
   the workspace, replies `COMPLETE`. The driver presents the report,
   runs finishing-a-development-branch, deletes the run record and the
   plan pointer.

## 5. Components

### 5.1 Context-usage hook: agent-scoped measurement on every event

Principle: **the hook measures the context of whoever it is talking to.**
A payload that identifies an agent measures that agent; otherwise it
measures the main session. Today only SubagentStop is agent-scoped; the
informational events measure the main transcript even inside a subagent,
which is the scoping gap that left controllers blind (fact 1). The
docstring's "PostToolUse carries no agent identifier" residual
(2026-06-06) is retired: false on 2.1.269.

Resolution rule, replacing the SubagentStop-only branch:

1. If the payload carries a string `agent_id`, the event is agent-scoped.
   The transcript is `agent_transcript_path` (alias
   `subagent_transcript_path`) when present, else the derived path
   `Path(transcript_path).with_suffix("") / "subagents" /
   f"agent-{agent_id}.jsonl"`. The state identity is
   `<session_id>--<agent_id>`. Sidechain entries count.
2. If agent-scoped and no candidate path exists on disk, skip with a
   stderr breadcrumb and never fall back to the parent transcript.
   Mis-scoped measurement is the bug this rule exists to prevent.
3. Otherwise measure `transcript_path` under `session_id`, excluding
   sidechain entries, exactly as today.
4. SubagentStop without any agent transcript field keeps today's skip.

Events. `PostToolUseFailure` is registered in hooks.json with the same
command and timeout as PostToolUse and maps to the same `tool` state key:
one mid-turn announcement per threshold, whichever event lands first
(fact 4). PostToolBatch is not registered (fact 5; its `agent_id` presence
is unverified and it adds nothing).

Wording. The advisory text per checkpoint is unchanged. The instruction
suffix is chosen by scope, because the hook knows whose context it
measured and no agent should have to translate `/handover`:

- main scope, 200k: "Wrap up your current work and use /handover to
  continue in a fresh session." (unchanged; 250k/300k escalate as today)
- agent scope, 200k: "Finish the step you are in, record your state, and
  end your turn per your pause protocol so a fresh agent can continue."
  250k/300k prefix "Stop immediately:" and 300k adds the quality note, as
  today.

Agent-scoped messages never contain `/handover`; main-scoped 200k+
messages always do. The docstring's "or-* tiers / agent manuals" phrasing
becomes "the agent definition's own protocol".

Turn-end addendum (approved). The Stop/SubagentStop block is a delivery
channel, not enforcement (hook docstring). When an informational channel
(`prompt` or `tool` state key) has already announced threshold T for the
same identity, the turn-end block for T is skipped; it still fires when
neither has, which is the starved-loop case it was built for (F20/F22).
This removes one wasted forced turn per controller pause and applies
identically to the main session. The 50 percent reset rule clears all keys
together, so a compaction re-arms both channels.

Unchanged: thresholds (100k/200k/250k/300k), once-per-threshold state,
reset rule, malformed-input handling, the accepted duplicate-announce race
under parallel tool calls (PostToolUse runs concurrently per tool, fact 5).

Consequence for the controller: with a ~61k baseline (fact 10) the 200k
warning lands after roughly 140k of work per controller life. The
mid-wake message is the primary channel; the SubagentStop block matters
only if a wake ends with no successful or failed tool call after the
crossing.

### 5.2 The controller: `agents/sdd-controller.md`

Principle: **the controller is SDD plus a pause protocol, nothing more.**
Every capability that SDD already has - ledger, resume, dispatch, model
selection, fix loops, rulings, final review, workspace deletion - is used
by invoking the skill, not re-described.

Frontmatter: `name: sdd-controller`; description marks it "spawned by
/implement-from-plan; not for standalone use"; `tools: Read, Write, Edit,
Glob, Grep, Bash, Skill, Agent`; `model: inherit`. No SendMessage, no
ListAgents: the controller talks to nobody; its reply is its output. No
`hooks` field (ignored for plugin agents, fact 8).

Spawn prompt (two lines, absolute paths):

```
PLAN: <absolute path of the plan file under ROOT>
ROOT: <absolute path of the repository root the run executes in>
```

Resume message (one line): `RULING: <Martin's answer>`.

Body, in this order:

1. **Preflight.** `git rev-parse --show-toplevel` must equal ROOT (the SDD
   workspace script derives its root from the current directory, fact 11);
   if not, reply `STOPPED: <what differs>` without touching anything.
2. **Mandate.** Invoke `superpowers:subagent-driven-development` on PLAN
   and run it end to end, from the ledger's current position. A ledger
   written by an earlier controller life or by a plain SDD run in a main
   session is resumed the same way; the controller has no resume logic of
   its own.
3. **Pause protocol.** When a context warning names your pause protocol:
   finish the step in flight up to its next ledger write (a dispatched
   worker returns and is ledgered; a fix round completes and is ledgered;
   a final-review stage is ledgered), dispatch nothing new, then end the
   turn with `PAUSED: <the ledger's last line>`. Never pause between a
   dispatch and its return - the ledger would be behind git.
4. **Stop cases.** SDD's four stop reasons end the turn with
   `STOPPED: <question, with the options as SDD framed them>`. On
   `RULING`, append `Ruling (human): <question> -> <answer>` to the
   ledger before acting, so a later life keeps it, then continue.
5. **Final-review ledgering.** Append `Final review: dispatched (package
   <path>, <base7>..<head7>)`. The controller dispatches the final
   reviewer with the instruction to write its full report to
   `<workspace>/final-review-report.md` and to reply with only that path
   and its finding counts; once that file exists, append `Final review:
   <K> findings (report <path>)` (K may be 0, in which case the next line
   is `Final review: clean`). Append `Final review: fix wave (<base7>..
   <head7>, re-review package <path>)` when the single fix dispatch and
   its scoped re-review have returned and residuals are adjudicated, then
   `Final review: clean`. A resumed life takes the findings from the
   report file, never from recollection. On resume with every task
   complete, continue the final review at the stage after the last
   `Final review:` line, or start it if there is none.
6. **Completion.** Compile the post-implementation report (section 5.5)
   from the ledger, `git log` and the workspace's review packages - never
   from recollection, since earlier lives are gone - then follow SDD
   "Finish" (rulings list, workspace deletion), then reply `COMPLETE`
   followed by the report. Do not invoke finishing-a-development-branch;
   the driver runs it.
7. **Reply discipline.** The final message of every wake is plain text
   beginning with one status keyword (section 6). On a hook-forced extra
   turn, re-issue the same line. Never emit tag-shaped text: the harness
   rewrites it.
8. **Read discipline.** Never Read a file whole when it may exceed the
   25,000-token cap (fact 10); use offset/limit or Grep.

### 5.3 The status-line guard: `hooks/sdd-controller-status.py`

Principle: **the driver branches on the status line, so the status line
is enforced by the harness, not promised by the prompt.**

Registered in hooks.json under SubagentStop with matcher
`^claude-toolkit:sdd-controller$` (fact 8), timeout 5, alongside the
context-usage hook (both run; each decides independently).

Behaviour: read `last_assistant_message`; strip leading whitespace; if it
starts with `PAUSED`, `STOPPED` or `COMPLETE` (case-sensitive, optionally
followed by `:`), exit 0 with no output. Otherwise print
`{"decision": "block", "reason": "Your final message must be a status
line: PAUSED: <ledger last line> | STOPPED: <question> | COMPLETE
<report>. Re-issue your status now."}`. If `stop_hook_active` is true,
exit 0 whatever the message: at most one forced retry, never a loop.
Malformed payloads exit 0 silently, as the context hook does.

The context-usage hook stays role-agnostic; the guard is the only
controller-specific hook.

### 5.4 The driver: `commands/implement-from-plan.md` (rewritten)

Principle: **the main session holds the run's identity and Martin's
attention; it never holds the run's progress.** Its context grows by one
notification per controller life and one question per stop case.

Files:

- `.claude/last-plan-doc` - the plan pointer, a bare path written by
  `/plan-from-design`. Unchanged; may be absent.
- `.claude/sdd-run.json` - the run record, `{"plan": "<abs>", "root":
  "<abs>"}`, created at spawn, deleted after the ship step. It lives in
  `.claude/` of the repository root current when the command is invoked;
  a resumed run is invoked from the same place. No agent id: a resume by
  id only works inside the spawning session, where the driver still has
  the id in context.

Plan resolution, in order: an explicit argument
(`/implement-from-plan <plan-path>`), the run record, the plan pointer, a
question. An argument that names a different plan than a live run record
is surfaced to Martin, never silently overriding it. This order is what
lets a plain SDD run in a main session pivot to this flow after
`/clear`: the ledger it wrote is resumed by the controller unchanged.

Start (no run record): run `superpowers:using-git-worktrees` here, in the
main session, because consent, directory choice and a failing baseline are
questions for Martin. Its Step 0 detects an existing worktree, and a
declined worktree means working in place on a feature branch; ROOT is
whatever repository root results. The session's working directory is ROOT
when the controller is spawned. Write the run record. Spawn.

Start (run record present): spawn from the record. Any controller from a
dead session is abandoned; the ledger is the resume point.

Spawn: one unnamed `Agent` call, `subagent_type:
"claude-toolkit:sdd-controller"` (the namespaced id; the bare name does
not resolve - the 1.7.2 lesson), prompt = PLAN + ROOT. No `model` unless
Martin asked for one. The driver then ends its turn; the harness
re-invokes it on the task notification. It never polls.

Loop, on each notification:

- `PAUSED`: print one line to Martin ("controller paused at <ledger last
  line>, respawning"). No-progress guard: read the ledger's last line; if
  it equals the last line recorded at the previous PAUSED, stop and ask
  Martin instead of respawning (a liveness check, not a budget).
  Otherwise record it and spawn a fresh controller with the identical
  prompt.
- `STOPPED`: put the question to Martin verbatim; on the answer, resume
  the same controller: `SendMessage(to: <agent id>, message: "RULING:
  <answer>")`.
- `COMPLETE`: present the report verbatim; proceed to 5.5.
- Anything else (the guard already forced one retry): show the reply and
  ask Martin how to proceed. Never guess a status.

End: after the ship step, `rm -f .claude/sdd-run.json .claude/last-plan-doc`
and announce completion.

### 5.5 Final review and ship

Final review: SDD "Final Review" runs unchanged inside the controller as
the tail of its run (review package, one dispatch on the most capable
model, at most one fix wave, one scoped re-review, adjudication), with the
stage ledgering of 5.2 item 5 so a pause during it resumes at the stage in
flight rather than re-running the review.

Report: today's six sections (summary with commits and test results; plan
deviations; reviewer issues and resolutions; unplanned changes; known
issues and risks; recommendations), each omitted when empty, plus SDD's
exhaustive "Rulings I made" list, the branch name and the commit range
`<merge-base7>..<head7>`. Compiled by the last controller life from the
ledger, `git log`, and the workspace's review packages, before the
workspace is deleted.

Ship: the driver runs `superpowers:finishing-a-development-branch` in the
main session after presenting the report; merge, PR and push are the side
effects SDD reserves for Martin (fact 11). Rework before shipping is a new
instruction or a follow-up plan; the driver loop does not run backwards.

### 5.6 Deletion and release

Removed: `skills/or-superpowers-at-scale/` (SKILL.md and 13 assets,
including `manager-playbook.md` and the handover ladder) and the ten
`agents/or-*.md` files (`or-brainstormer`, `or-code-quality-reviewer`,
`or-community-researcher`, `or-dependency-researcher`, `or-final-reviewer`,
`or-finisher`, `or-implementer`, `or-plan-writer`, `or-spec-reviewer`,
`or-supervisor`). No command wrapper exists for the skill.

Updated: `.claude-plugin/plugin.json` (description names the controller
and driver instead of the orchestrator; version 2.0.0 - removing a skill
and ten agents is breaking), the marketplace entry and README per
`claude-toolkit:updating-plugin`, hooks.json description, the
context-usage docstring (5.1).

Kept: `docs/superpowers/validation/*` and `docs/superpowers/handovers/*`
as records of past runs; the stale worktrees under `.claude/worktrees/`
are outside this work.

After release: update the installed plugin and restart the session before
the driver can spawn `claude-toolkit:sdd-controller`.

## 6. Status protocol

The controller's final message in every wake is plain text whose first
line begins with exactly one of:

| Keyword | Meaning | Driver action |
|---|---|---|
| `PAUSED: <ledger last line>` | Context threshold reached; ledger at a boundary | Respawn a fresh controller (after the no-progress guard) |
| `STOPPED: <question and options>` | One of SDD's four stop reasons, or a failed preflight | Ask Martin; resume the same controller with `RULING:` |
| `COMPLETE` + report | Final review clean, workspace deleted | Present report; ship; clear pointers |

No FAILED status: an environment the controller cannot work in is a
question for Martin and is `STOPPED`. Keywords are case-sensitive; the
guard (5.3) enforces the grammar with one forced retry.

## 7. Failure handling

- Hook cannot resolve the agent transcript: silent skip with breadcrumb;
  the agent runs unwarned until the SubagentStop backstop (5.1 rule 2).
- Controller ignores the mid-wake warning and ends its wake later: the
  SubagentStop block forces one turn with the same instruction, unless
  the addendum has already recorded a mid-turn delivery, in which case
  the driver simply receives a later PAUSED. Either way the ledger is at
  a boundary because the pause protocol only pauses at ledger writes.
- Controller replies without a status line: the guard forces one retry;
  a second failure reaches the driver, which asks Martin (5.4).
- A life pauses without advancing the ledger twice in a row: the
  no-progress guard stops the driver (5.4).
- Controller life dies mid-step (crash, session end): the ledger and git
  hold the last boundary; the next life resumes from there, at worst
  re-running one in-flight step, which SDD's review loop tolerates.
- Session dies: `/implement-from-plan` again from the same repository
  root reads the run record and spawns a fresh life. When ROOT is a
  worktree, the driver re-enters it before that spawn.
- Worker dispatched by the controller crosses its own 200k: the hook now
  warns it too (5.1 applies to every agent); SDD's per-task escalation
  rules govern what the controller does with a worker that stops early.
- Auto-compaction of the controller near 1M (R, subagents auto-compact)
  remains a safety net, never the authority; the 50 percent reset re-arms
  the hook afterwards.

## 8. Testing

Rule: every test names the promise it holds (this spec's section), asserts
the whole claim, is built on the state most likely to break it, and is
shown red against the pre-change code before it is accepted (the red
evidence is pasted in the plan's task report).

Hook promises (`tests/hooks/test_context_usage.py`, extended):

1. 5.1 rule 1: an event carrying `agent_id` measures the agent's own
   transcript, never the parent's, on PostToolUse and PostToolUseFailure.
   Fixture: parent transcript at 250k, derived agent transcript at 50k ->
   no output; the reverse -> the agent's figure in the message.
2. 5.1 rule 1: a crossing writes only `<session>--<agent_id>` state; the
   parent's state file is byte-identical before and after.
3. 5.1 rule 1: an explicit `agent_transcript_path` wins over the derived
   path when both exist, so SubagentStop behaves as today.
4. 5.1 rule 2: `agent_id` with no resolvable transcript emits nothing,
   writes no state, leaves a breadcrumb; the parent transcript at 300k
   beside it stays unmeasured.
5. 5.1 wording: agent-scoped 200k/250k/300k messages contain the
   pause-protocol instruction and never `/handover`; main-scoped ones
   still contain `/handover`.
6. 5.1 events: PostToolUse and PostToolUseFailure share the `tool` key -
   a threshold announced by one is not re-announced by the other.
7. 5.1 addendum: a turn-end block for T is skipped when `prompt` or
   `tool` already recorded T for the identity, and still fires when
   neither did (both scopes).

Guard promises (`tests/hooks/test_sdd_controller_status.py`, new):

8. 5.3: a last message beginning with `PAUSED`, `STOPPED` or `COMPLETE`
   passes with no output; any other message blocks with the reason.
9. 5.3: `stop_hook_active: true` never blocks, whatever the message.
10. 5.3 and 5.1: hooks.json carries the guard under SubagentStop with the
    anchored matcher and carries PostToolUseFailure with the context-usage
    command (registration test).

Live spikes (the plan's acceptance checklist; a small throwaway plan):

- 4 step 3: a controller receives the 200k warning mid-wake on its own
  transcript and replies PAUSED with the ledger at a boundary.
- 5.2 item 2: a respawned life resumes at the correct task or round with
  no re-dispatch of completed tasks.
- 5.2 item 4: STOPPED, a RULING by agent id, continuation with the ruling
  ledgered.
- 5.3: the guard blocks a non-status final message exactly once.
- 5.4: a ledger written by plain SDD in a main session is resumed by the
  controller with no pointer present.
- 5.6: the namespaced controller id resolves after the plugin update and
  restart.

## 9. Out of scope

- The brainstorm and plan phases (`/design`, `/plan-from-design`) and
  their interactive workflow. The or-brainstormer and or-plan-writer
  roles vanish with no replacement.
- Named agents, teammates, mailboxes. Not used.
- Resuming a controller by id across sessions. The ledger is the
  cross-session resume.
- PostToolBatch registration.
- Per-agent token limits or budgets of any kind.
- The stale E2E worktrees under `.claude/worktrees/` and the stray
  `.superpowers/sdd/task-4-brief.md`.
