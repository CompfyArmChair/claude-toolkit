# Spike: PostToolUse hook measuring the subagent's own transcript delivers context mid-wake? (2026-09-11)

## Depth 1 (this agent)

Start-of-conversation hook text (verbatim or none):
none

Read 1 (offset 1, limit 700): no hook text. The Read itself errored:
```
File content (35029 tokens) exceeds maximum allowed tokens (25000). Use offset and limit parameters to read specific portions of the file, or search for specific content instead of reading the whole file.
```

Read 2 (offset 2000, limit 700): no hook text. The Read itself errored:
```
File content (28111 tokens) exceeds maximum allowed tokens (25000). Use offset and limit parameters to read specific portions of the file, or search for specific content instead of reading the whole file.
```

Read 3 (offset 4000, limit 700): no hook text. The Read itself errored:
```
File content (26385 tokens) exceeds maximum allowed tokens (25000). Use offset and limit parameters to read specific portions of the file, or search for specific content instead of reading the whole file.
```

## Depth 2 (child)

Child's reply, verbatim:
```
Start: none
Read 1: PostToolUse:Read hook additional context: CTX-PROBE: agent a3d668d146e5992bd (general-purpose) is at 68,920 tokens (measured from derived). If you can read this, quote it verbatim in your report.
Read 2: none
Read 3: none
```

Envelope kind it arrived in: a background `<task-notification>` system-reminder (not a live user turn), wrapped in a preamble reading "[SYSTEM NOTIFICATION - NOT USER INPUT] ... This is an automated background-task event, NOT a message from the user." The notification carried `<task-id>a3d668d146e5992bd</task-id>`, `<status>completed</status>`, a `<summary>` line, and a `<result>` tag containing the child's four-line reply verbatim as quoted above. Usage metadata accompanying it: `<subagent_tokens>84359</subagent_tokens><tool_uses>6</tool_uses><duration_ms>42268</duration_ms>`.

## Anything unexpected

Immediately after the Step 2 Agent tool call (launching the depth-2 child), before any Read in Step 1's own sequence and outside the three "Read N" slots this spike was measuring, this agent's own transcript received:
```
PostToolUse:Agent hook additional context: CTX-PROBE: agent afb88fc5c7615538e (general-purpose) is at 71,039 tokens (measured from derived). If you can read this, quote it verbatim in your report.
```
This is a `PostToolUse:Agent` hook (not `PostToolUse:Read`), and it fired on the Agent tool call itself, not on any of this agent's three Step-1 Read calls. Also of note: the agent ID named inside that hook text (`afb88fc5c7615538e`) does not match the `agentId` this agent was given for the launched child in the Agent tool's own result (`a3d668d146e5992bd`) — the latter is the ID that subsequently appeared, self-consistently, inside the child's own Read-1 hook text and inside the task-notification's `<task-id>`.

## Session-2 analysis (2026-09-11, main session, after the agent's report)

Verdict: PASS at both depths. The depth-1 "never" is explained by the
agent's own transcript (`~/.claude/projects/C--Users-marti--claude/
c846d396-e9e8-407b-b4dd-cceb131d9c74/subagents/agent-afb88fc5c7615538e.jsonl`)
and the probe log (`ctx_probe.log`, 26 lines):

- The three depth-1 Reads were SEQUENTIAL (three separate assistant
  messages, transcript lines 13, 21, 25 at 20:15:31Z / :37Z / :39Z) and
  every one returned `is_error: true` (the 25,000-token Read cap quoted
  above). PostToolUse fires only after a tool call SUCCEEDS; a failed call
  fires PostToolUseFailure instead (hooks docs event table). The probe was
  registered on PostToolUse only, so nothing ran and nothing was measured.
  The parallel-batch / PostToolBatch hypothesis raised in session 1 is
  wrong: no batch was issued.
- Depth-1 delivery DID work. The probe emitted its once-per-agent marker on
  the first SUCCESSFUL tool call, the background Agent spawn (log line 8,
  21:15:52 local, 71,039 tokens measured from the derived path), and the
  agent acknowledged it mid-wake six seconds later (transcript line 36,
  20:15:58Z: "Noted - a `PostToolUse:Agent hook additional context:
  CTX-PROBE: agent afb88fc5c7615538e ...`") - the same text quoted under
  "Anything unexpected" above. It reported "never" only because its
  answer slots were "after Read N".
- Depth-2 delivery worked at Read 1 (log line 10, 68,920 tokens), quoted
  verbatim above, mid-wake, before its reply.
- Payload facts (log lines 4-15): PostToolUse inside a subagent carries
  `agent_id` and `agent_type`, and `transcript_path` is the MAIN session
  transcript; the derived path `<transcript stem>/subagents/agent-<id>.jsonl`
  exists from the agent's first model turn on (`derived_exists: true` on
  every in-agent PostToolUse) but NOT yet at the spawn-time SubagentStart
  (line 4, `derived_exists: false`); it does exist at the SubagentStart
  that fires on RESUME (line 15, after the child returned). SubagentStart
  keys: agent_id, agent_type, cwd, hook_event_name, prompt_id,
  scratchpad_dir, session_id, transcript_path. SubagentStop adds
  agent_transcript_path, background_tasks, last_assistant_message,
  session_crons, stop_hook_active, effort, permission_mode. One SubagentStop
  arrived for an agent with `agent_type: ""` and no transcript on disk
  (line 12) - a harness helper; a hook must tolerate a missing transcript.
- Baseline: a general-purpose subagent in this environment starts at
  ~61k tokens (cache_creation_input_tokens 60,912 on its first call),
  because the system prompt carries the full MCP tool roster.

Design consequences carried into the 2026-09-11 lean-redesign spec:
measure the agent's own transcript on PostToolUse AND PostToolUseFailure
(both accept `hookSpecificOutput.additionalContext`); PostToolBatch is
not needed (PostToolUse fires per tool even inside a parallel batch);
never rely on whole-file Reads inside a controller (25k cap per Read).
