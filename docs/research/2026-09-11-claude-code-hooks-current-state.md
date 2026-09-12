# Claude Code hooks: current state (research, 2026-09-11)

**Purpose:** input to the SDD-at-scale lean redesign brainstorm. Answers: the full current hook-event list; Stop/SubagentStop payload and `decision: block` semantics; whether any event fires when an agent idles with background children running, or on background-task completion; agent-type matchers and agent-frontmatter hooks; compaction hooks and settings; recent changelog entries on hooks/agents/teams/Workflow/compaction; whether a subagent can read its own token usage.

**Provenance:** fetched via the raw-fetch pipeline by a background research agent on 2026-09-11; all four pages returned verdict OK. Claude Code build at the time: 2.1.269. Every claim below cites `deposit:line`.

**Deposit paths** (all under `C:\Users\marti\.claude\.claude\web-deposits\`), aliased for brevity:
- **H** = `2026-09-11-code-claude-com-docs-en-hooks.md`
- **G** = `2026-09-11-code-claude-com-docs-en-hooks-guide.md`
- **S** = `2026-09-11-code-claude-com-docs-en-sub-agents.md`
- **C** = `2026-09-11-raw-githubusercontent-com-anthropics-claude-code-main-change.md`

---

## A. Complete documented hook-event list

33 events, from the summary table at **H:272-305**. One line each, verbatim-condensed:

| Event | Fires | Line |
|---|---|---|
| SessionStart | session begins or resumes | H:273 |
| Setup | `--init-only`, or `--init`/`--maintenance` in `-p` | H:274 |
| UserPromptSubmit | you submit a prompt, before Claude processes it | H:275 |
| UserPromptExpansion | user-typed command expands into a prompt; can block | H:276 |
| PreToolUse | before a tool call; can block | H:277 |
| PermissionRequest | tool call needs a permission decision | H:278 |
| PermissionDenied | auto mode denies a tool call | H:279 |
| PostToolUse | after a tool call succeeds | H:280 |
| PostToolUseFailure | after a tool call fails | H:281 |
| PostToolBatch | after a parallel batch resolves, before next model call | H:282 |
| Notification | Claude Code sends a notification | H:283 |
| MessageDisplay | while assistant message text is displayed | H:284 |
| **SubagentStart** | when a subagent is spawned | H:285 |
| **SubagentStop** | when a subagent finishes | H:286 |
| TaskCreated | task being created via `TaskCreate` | H:287 |
| **TaskCompleted** | task being marked completed | H:288 |
| **Stop** | Claude finishes responding | H:289 |
| StopFailure | turn ends due to an API error | H:290 |
| **TeammateIdle** | an agent-team teammate is about to go idle | H:291 |
| InstructionsLoaded | CLAUDE.md / `.claude/rules/*.md` loaded | H:292 |
| ConfigChange | config file changes mid-session | H:293 |
| CwdChanged | working directory changes | H:294 |
| DirectoryAdded | dir added via `/add-dir` / `register_repo_root` | H:295 |
| FileChanged | a watched file changes on disk | H:296 |
| WorktreeCreate / WorktreeRemove | worktree created / removed | H:297-298 |
| PreCompact / PostCompact | before / after context compaction | H:299-300 |
| PreModelSwitch / PostModelSwitch | before / after a model switch | H:301-302 |
| Elicitation / ElicitationResult | MCP elicitation request / response | H:303-304 |
| SessionEnd | session terminates | H:305 |

There is **no** `WorkflowStart`/`WorkflowStop`, no `AgentIdle`, and no background-task-completion event in this list.

## B. Stop and SubagentStop

**Stop input** (H:2890): common fields plus `stop_hook_active`, `last_assistant_message`, `background_tasks`, `session_crons`. `stop_hook_active` is `true` "when Claude Code is already continuing as a result of a stop hook… Claude Code overrides the hook and ends the turn after **8 consecutive blocks**" (H:2890). `background_tasks` entry fields: `id`, `type`, `status`, `description`, `command`, `agent_type`, `server`, `tool`, `name` (H:2894-2904); `type` labels include `shell`, `subagent`, `monitor`, `workflow`, `teammate`, `cloud session`, `MCP task` (H:2896). Full JSON example H:2913-2935.

**SubagentStop input** (H:2711, verbatim): "SubagentStop hooks receive `stop_hook_active`, `agent_id`, `agent_type`, `agent_transcript_path`, and `last_assistant_message`… The `transcript_path` is the main session's transcript, while `agent_transcript_path` is the subagent's own transcript stored in a nested `subagents/` folder… SubagentStop hooks also receive the `background_tasks` and `session_crons` arrays described under Stop input. **Both arrays are scoped to the parent session, not the subagent.**" Note: the field is `agent_transcript_path`, **not** `subagent_transcript_path`. JSON example H:2714-2729. Common fields (`session_id`, `prompt_id`, `transcript_path`, `cwd`, `scratchpad_dir`, `permission_mode`, `effort`, `hook_event_name`) at H:987-996; `agent_id`/`agent_type` at H:1001-1002.

**Decision semantics** (H:2960-2982): `decision: "block"` — "prevents Claude from stopping. Omit to allow Claude to stop"; `reason` — "Required when `decision` is `"block"`. Tells Claude why it should continue"; `hookSpecificOutput.additionalContext` — "Non-error feedback for Claude. The conversation continues so Claude can act on it, but unlike `decision: "block"` it is shown in the transcript as hook feedback rather than a hook error." Universal `continue: false` + `stopReason` and `systemMessage` are at H:1191-1196.

**What "block" does**, exactly: Stop → "Prevents Claude from stopping, continues the conversation" (H:1122); SubagentStop → "Prevents the subagent from stopping" (H:1123). And H:2718 (verbatim): "Returning `decision: "block"` with a `reason` keeps the subagent running and delivers `reason` to the subagent as its next instruction. A hook that blocks by exiting 2 delivers its stderr message the same way. **To inject context into the parent session after a subagent returns, use a `PostToolUse` hook on the `Agent` tool instead.**" Prompt-type hooks use `{ok, reason, impossible}`; `impossible: true` on Stop/SubagentStop lets the turn end (H:4048, H:4054).

## C. SubagentStop vs. background children — **not documented**

- No page states when SubagentStop fires relative to background subagents the subagent itself spawned. The only statement is the definitional "Runs when a Claude Code subagent has finished responding" (H:2701).
- The `background_tasks` array a SubagentStop hook receives is **explicitly parent-session-scoped, not the subagent's** (H:2711) — so it cannot be used to see the subagent's own in-flight children.
- **No event fires for "agent idle with children still running."** The documented substitute is Stop's `background_tasks`: "let hooks distinguish 'session is done' from 'session is paused waiting for background work to wake it back up'" (H:2890).
- **No "background task/agent completed" hook event.** `TaskCompleted` is about the `TaskCreate`/`TaskUpdate` task list, not background agents (H:2809). The closest signal is the `Notification` matcher `agent_completed`: "A background session finishes or fails. **Fires only while agent view is open in a terminal**" (H:2575) — a background *session*, not a background subagent, and requires v2.1.198+ (H:2577).
- A `PostToolUse` hook on `Agent` does **not** signal completion for background subagents: `status` is `"async_launched"` and "For background subagents, the tool returns when the task moves to the background, so `tool_response` carries no usage fields" (H:2017, H:2027). Delivery is model-side only: "A background subagent's results reach Claude as a completion notification in a later turn" (S:1041).

## D. Targeting a specific agent type / frontmatter hooks

- **SubagentStart** matcher = agent type: "`general-purpose`, `Explore`, `Plan`, custom agent names, or plugin-scoped names like `^my-plugin:reviewer$`" (H:546). **SubagentStop** matcher = "agent type | same values as `SubagentStart`" (H:549). Matcher value is the frontmatter `name`; plugin agents use the scoped id and must be anchored because `:` forces the regex path (H:2651, S:935).
- `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted` have **no matcher support** — "always fires on every occurrence" (H:556).
- **Subagent frontmatter hooks**: scope "While that subagent is running" (H:510). "Claude Code runs them only while that subagent is running and removes them when it finishes. **Claude Code converts a `Stop` hook here to `SubagentStop`**" (H:923). Syntax (S:894-910):

```yaml
---
name: code-reviewer
description: Review code changes with automatic linting
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-command.sh $TOOL_INPUT"
---
```

  "All hook events are supported" in subagent frontmatter (S:889). Project-subagent frontmatter hooks require workspace trust; a `-p` session doesn't count (H:938, S:887).
- **Skill frontmatter hooks**: same format, but "registers them when you or Claude invoke the skill and keeps running them for the rest of the session"; `once: true` removes after first success (H:924, example H:928-937).

## E. Hooks and compaction

- `PreCompact` matchers `manual` / `auto`; "Exit with code 2 to block compaction… You can also block by returning JSON with `"decision": "block"`." Blocking proactive auto-compact skips it; blocking recovery compaction makes the request fail. `systemMessage` and `continue` are discarded (H:3470-3478).
- PreCompact input adds `trigger` and `custom_instructions` (H:3484).
- `PostCompact` input adds `trigger` and `compact_summary`; "PostCompact hooks have no decision control" (H:3516, H:3534).
- **Subagents do compact**: "Subagents support automatic compaction using the same logic as the main conversation. Compaction triggers under the same conditions, and **`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` applies to subagents as well**" (S:1262). Compact boundaries are logged in the subagent transcript as `{"type":"system","subtype":"compact_boundary","compactMetadata":{"trigger":"auto","preTokens":167189}}` (S:1264-1273).

## F. CHANGELOG

**The CHANGELOG carries no dates** — headings are bare version numbers (`## 2.1.269`, C:12), so a 2026-06-01 cutoff cannot be verified from the fetched page. Table below covers versions **2.1.200-2.1.269** (the most recent 60-odd releases). **Latest version: 2.1.269** (C:12).

| Ver | Entry (verbatim, trimmed) |
|---|---|
| 2.1.269 | Added `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` (1–256) to raise the Workflow tool's per-run concurrent agent limit (C:19) |
| 2.1.269 | Fixed remote and headless sessions reporting "waiting for your input" while background agents were still running (`CLAUDE_CODE_BG_TASKS_REPORT_RUNNING=0`) (C:24) |
| 2.1.269 | [VSCode] Added a Hooks dialog… managed, plugin, and session hooks stay read-only |
| 2.1.268 | Fixed PermissionRequest hooks not firing in `--print` mode |
| 2.1.268 | Fixed `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` not extending SessionEnd hooks |
| 2.1.265 | Fixed agent teammates and resumed subagents moving SubagentStart hook context… out of the prompt prefix |
| 2.1.261 | Fixed in-process agent-team teammates re-sending their first-turn tool and skill announcements |
| 2.1.260 | Fixed Workflow tool subagents being restarted as stalled while a long context compaction was still in progress |
| 2.1.260 | Improved auto-compact for 1M-context models: Opus and Fable sessions now compact shortly before the 1M-token limit |
| **2.1.259** | **Fixed blocking Stop hooks causing the turn after a block to lose the model's reasoning from that turn** |
| **2.1.259** | **Improved nested background subagent results to be saved in the parent subagent's transcript, so resumed subagents keep them** |
| 2.1.251 | Added `PreModelSwitch` and `PostModelSwitch` hook events; `SessionStart` resume hooks now receive session staleness and estimated re-cache cost |
| 2.1.248 | Improved the Workflow tool's prompt footprint: description now ~1k tokens instead of 5.7k (`workflow-authoring` skill) |
| 2.1.247 | Changed Sonnet 5's default auto-compact window to its full 1M context (~967K tokens) |
| 2.1.239 | `ListAgents` and `/list-agents` now list your live teammates |
| 2.1.234 | Removed the "Default teammate model" setting; agent-team teammates now use the leader's model |
| 2.1.232 | Subagent forking is now on by default… non-teammate agent spawns in interactive sessions now run in the background by default |
| **2.1.219** | **Subagents can now spawn nested subagents up to depth 3 by default (was 1); set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` to disable nesting** |
| 2.1.219 | Added `DirectoryAdded` hook event; added nested subagent forwarding in stream-json at depth-2+ |
| 2.1.218 | Fixed agent frontmatter hooks running from untrusted folders |
| **2.1.217** | **Changed subagents to no longer spawn nested subagents by default** |
| 2.1.214 | Fixed hooks with exit code 2 not blocking as documented when stdout JSON fails schema validation; SessionStart now reports source `"fork"` |
| 2.1.212 | Added a per-session cap on subagent spawns (default 200, `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION`) |
| 2.1.211 | Fixed auto mode overriding a PreToolUse hook's `ask` decision |

All rows above are greppable in **C** by their text. Historical anchors outside that window: `PostCompact` added 2.1.76; `TeammateIdle`/`TaskCompleted` added 2.1.33; `SubagentStart` added 2.0.43; Stop/SubagentStop `additionalContext` added 2.1.163; `background_tasks`/`session_crons` added to Stop/SubagentStop in 2.1.145; `last_assistant_message` added 2.1.47.

## G. A subagent learning its own context usage — **not documented**

Nothing on any of the four pages gives a subagent a runtime read of its own token count.

- The hooks page enumerates the env vars a hook process sees; the only per-run value exposed is `$CLAUDE_EFFORT` (H:993). It states plainly "There is no `$CLAUDE_MODEL` environment variable" (H:1003). No context/token env var exists.
- `context_tokens` appears only in **SessionStart** input for `resume`/`fork` sessions (H:1395) and in **PreModelSwitch/PostModelSwitch** input (H:3633) — main-session hook payloads, not readable by a subagent about itself.
- Parent-side token data only: PostToolUse on a foreground `Agent` call gives `totalTokens`/`usage`, and those cover "the subagent's final API request… not a total across the whole run" (H:2022, H:2025); a background launch "carries no usage fields" (H:2027).
- Retrospective only: `preTokens` in the subagent transcript's `compact_boundary` record (S:1273).
- **Per-agent context limits: not documented.** Subagent frontmatter has no context/token field (full table S:452-472); `maxTurns` caps *turns*, not tokens (S:461). Context sizing is model-derived: "a subagent's context window is sized by its own model, not the parent's" (S:1225).
- **Auto-handover: not documented.** The only automatic mechanism is auto-compaction, shared with the main conversation and tunable only by the global `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (S:1262). The nearest manual analogue is resuming a subagent stopped at `maxTurns`, whose output is marked partial (S:1233).
- `subagentStatusLine` is named in passing (H:511) but its contents are documented on the statusline page, which was not fetched.
