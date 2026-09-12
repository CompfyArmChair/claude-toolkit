---
description: Drive the tracked plan to completion across context windows - spawns a claude-toolkit:sdd-controller per controller life, respawns from the SDD ledger on PAUSED, relays your ruling on STOPPED, and ships in this session on COMPLETE
---

# /implement-from-plan - Drive a plan to completion

You are the driver. You hold the run's identity (which plan, which
repository root) and your human partner's attention; you never hold the
run's progress. Progress lives in SDD's ledger under ROOT
(`<ROOT>/.superpowers/sdd/<plan-basename>/progress.md`) and in git. Your
context grows by one notification per controller life and one question
per stop case, nothing more. There is no handover document, no per-task
messaging, and no token budget: the controller pauses when the context
hook tells it to, and the ledger is the resume point.

## Files

- `.claude/last-plan-doc` - the plan pointer, a bare path written by
  `/plan-from-design`. May be absent.
- `.claude/sdd-run.json` - the run record, exactly
  `{"plan": "<absolute plan path>", "root": "<absolute repository root>"}`.
  Created at the first spawn, deleted after the ship step. It lives in
  `.claude/` of the repository root current when this command is invoked
  (INVOKE_ROOT below); a resumed run is invoked from the same place. It
  carries no agent id: resuming a controller by id only works inside the
  session that spawned it, where you still have the id in context.

## Step 0: Capture where you were invoked

```bash
INVOKE_ROOT=$(git rev-parse --show-toplevel) && echo "$INVOKE_ROOT"
```

Every read or write of the two files above is relative to INVOKE_ROOT,
even after Step 2 moves the run into a worktree.

## Step 1: Resolve the plan

Read both files:

```bash
cat "$INVOKE_ROOT/.claude/sdd-run.json" 2>/dev/null; echo; cat "$INVOKE_ROOT/.claude/last-plan-doc" 2>/dev/null
```

Resolution order:

1. **An explicit argument** (`/implement-from-plan <plan-path>`). If a run
   record exists and names a different plan, do not override it silently:
   tell your human partner both paths and ask whether to resume the
   recorded run or abandon it (delete the record) and start the argument's
   plan.
2. **The run record**, when present: PLAN and ROOT come from it; skip to
   Step 3 with no new worktree work. Any controller from a dead session is
   abandoned; the ledger is the resume point. Before Step 3, check
   `git rev-parse --show-toplevel` against ROOT. If they differ, the run
   lives in a worktree and this session started elsewhere: re-enter that
   worktree with your native worktree tool (`EnterWorktree` with
   `path: <ROOT>`), then re-check. Without such a tool, tell your human
   partner to restart the session in ROOT and stop.
3. **The plan pointer**, when present.
4. Otherwise ask: "No plan tracked. What's the path to your plan?"

This order lets a plain SDD run in a main session pivot to this flow
after `/clear`: the ledger it wrote is resumed by the controller unchanged.

## Step 2: Establish ROOT (only when there is no run record)

Invoke `superpowers:using-git-worktrees` here, in this session, because
consent, directory choice and a failing baseline are questions for your
human partner. Its Step 0 detects an existing worktree; a declined
worktree means working in place on a feature branch. ROOT is whatever
repository root results:

```bash
ROOT=$(git rev-parse --show-toplevel) && echo "$ROOT"
```

Your working directory must be ROOT when the controller is spawned. Make
PLAN absolute under ROOT (a pointer holds a repo-relative path:
`PLAN="$ROOT/<relative path>"`), confirm the file exists, then write the
run record:

```bash
python -c "import json,os,sys; os.makedirs(os.path.dirname(sys.argv[3]), exist_ok=True); json.dump({'plan': sys.argv[1], 'root': sys.argv[2]}, open(sys.argv[3], 'w'))" "$PLAN" "$ROOT" "$INVOKE_ROOT/.claude/sdd-run.json"
```

## Step 3: Spawn a controller life

One unnamed `Agent` call:

- `subagent_type`: `claude-toolkit:sdd-controller` - the namespaced id; the
  bare name does not resolve.
- `prompt`: exactly two lines,

  ```
  PLAN: <PLAN>
  ROOT: <ROOT>
  ```

- No `name`. No `model` unless your human partner asked for one.

Record the agent id the tool returns - a STOPPED question is answered by
resuming that id. Print one line ("Controller life N spawned for
`<plan basename>`; waiting for its status.") and **end your turn**. The
harness re-invokes you when the controller's notification arrives. Never
poll, never sleep, never send it a message while it runs.

## Step 4: Act on the notification

The notification's result is the controller's final message; its first
line begins with one of three keywords (a SubagentStop guard has already
forced one retry if it did not).

**`PAUSED: <ledger last line>`** - the context hook paused it with the
ledger at a boundary.

1. Liveness check (not a budget): read the ledger's last line,

   ```bash
   tail -n 1 "$ROOT/.superpowers/sdd/$(basename "$PLAN" .md)/progress.md"
   ```

   If it equals the last line you recorded at the previous PAUSED, the
   run made no progress across a whole life: stop and tell your human
   partner, showing both PAUSED lines; do not respawn.
2. Otherwise record this last line, print one line ("Controller paused at
   `<ledger last line>`; respawning.") and go to Step 3 with the identical
   PLAN and ROOT. SDD's Setup resumes the new life at the first incomplete
   task or round.

**`STOPPED: <question and options>`** - one of SDD's four stop cases, or a
failed preflight. Put the question to your human partner verbatim. On the
answer, resume the **same** controller:

```
SendMessage(to: <the agent id from Step 3>, message: "RULING: <the answer>")
```

then end your turn and wait for its next notification. If the session
that spawned the controller is gone (no id in context), the answer cannot
be relayed: tell your human partner, then go to Step 3 with the same PLAN
and ROOT. The fresh life resumes from the ledger and re-raises the
question when it reaches the stop case, and you then hold its id.

**`COMPLETE`** followed by the report - final review clean, workspace
deleted. Present the report verbatim, then go to Step 5.

**Anything else** - show the reply verbatim and ask your human partner how
to proceed. Never guess a status.

## Step 5: Ship and clear

Run `superpowers:finishing-a-development-branch` in this session (merge,
PR and push are the side effects SDD reserves for your human partner).
Rework requested at this point is a new instruction or a follow-up plan;
this loop never runs backwards.

After the ship step:

```bash
rm -f "$INVOKE_ROOT/.claude/sdd-run.json" "$INVOKE_ROOT/.claude/last-plan-doc"
```

Announce: "Implementation complete. Run record and plan pointer cleared."

## Failure handling

- The session dies mid-run: run `/implement-from-plan` again from
  INVOKE_ROOT. Step 1 finds the run record and Step 3 spawns a fresh life
  (a worktree ROOT is re-entered first - Step 1 item 2); the ledger and
  git hold the last boundary, at worst one in-flight step is re-run, which
  SDD's review loop tolerates.
- Two PAUSED lives with the same ledger last line: Step 4's liveness check
  stops you; ask, do not respawn.
- A controller reply with no status keyword after the guard's one forced
  retry: show it and ask.
