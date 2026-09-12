# SDD-at-Scale Lean Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the or-superpowers-at-scale orchestrator with one controller agent that runs a whole plan via subagent-driven development, is paused mid-wake by the context-usage hook measuring its own transcript, and is respawned from the SDD ledger by a thin driver command.

**Architecture:** The context-usage hook becomes agent-scoped on every event (it measures whoever it is talking to, via the agent's own transcript derived from `agent_id`), gains a scope-aware instruction suffix, registers `PostToolUseFailure`, and skips a turn-end block already delivered mid-turn. A new `sdd-controller` agent is SDD plus a pause protocol; a new `SubagentStop` guard enforces its status-line grammar; `/implement-from-plan` is rewritten as the driver that spawns controller lives, relays rulings, and ships. The or-* skill and agents are deleted and the plugin is released as 2.0.0.

**Tech Stack:** Python 3.13 hooks (stdlib only, `unittest` via `pytest 8.3.4`), Claude Code plugin conventions (agent frontmatter, `hooks.json`, `.claude-plugin/plugin.json`, marketplace), superpowers 6.3.0 skills (`subagent-driven-development`, `using-git-worktrees`, `finishing-a-development-branch`).

**Spec:** `docs/superpowers/specs/2026-09-11-sdd-at-scale-lean-redesign-design.md` (section numbers below are that spec's). Its research deposits: `docs/research/2026-09-11-claude-code-hooks-current-state.md` (R:) and `docs/research/2026-09-11-spike-posttooluse-subagent-context.md` (K:).

## Global Constraints

- **Repository and branch:** `I:\Dev\claude-toolkit`, branch `sdd-at-scale-lean-redesign` (from master `15ff9ca`, plugin 1.7.2). All commands below run from the repository root in Bash-tool syntax unless stated. Commit after every task; never commit to master.
- **Commit trailers:** append the attribution trailer your session's system reminder specifies to every commit message.
- **Thresholds and state are unchanged** (spec 5.1 "Unchanged"): checkpoints 100k / 200k / 250k / 300k; once-per-threshold per state key; reset when usage falls below 50 percent of any announced threshold (`RESET_RATIO = 0.5`); state files `~/.claude/hooks/state/context-usage-<session_id>.json` (main) and `context-usage-<session_id>--<agent_id>.json` (agent); malformed-input handling (exit 0, stderr breadcrumb) exactly as today.
- **Scope rule** (spec 5.1 rules 1-4): a payload carrying a string `agent_id` (or an explicit `agent_transcript_path` / `subagent_transcript_path`) is agent-scoped; transcript = explicit field when present, else `Path(transcript_path).with_suffix("") / "subagents" / f"agent-{agent_id}.jsonl"`; state identity `<session_id>--<agent_id>`; sidechain entries count. Agent-scoped with no candidate on disk: skip with breadcrumb, **never** measure the parent transcript. Otherwise main-scoped as today. `SubagentStop` naming no agent identity keeps its skip.
- **Events** (spec 5.1 "Events"): `PostToolUseFailure` registered with the same command and timeout (3) as `PostToolUse`; both map to the `tool` state key. `PostToolBatch` is **not** registered.
- **Wording** (spec 5.1 "Wording"): advisory text per checkpoint unchanged. Main-scope 200k suffix: "Wrap up your current work and use /handover to continue in a fresh session." Agent-scope 200k suffix: "Finish the step you are in, record your state, and end your turn per your pause protocol so a fresh agent can continue." 250k/300k prefix "Stop immediately:"; 300k adds the quality note. Agent-scoped messages never contain `/handover`; main-scoped 200k+ messages always do.
- **Turn-end addendum** (spec 5.1): a `Stop`/`SubagentStop` block for threshold T is skipped when the `prompt` or `tool` state key of the same identity already recorded T; it still fires when neither did.
- **Guard** (spec 5.3 and 6): `hooks/sdd-controller-status.py` on `SubagentStop`, matcher `^claude-toolkit:sdd-controller$`, timeout 5. Passes when `last_assistant_message`, after leading whitespace, starts with `PAUSED`, `STOPPED` or `COMPLETE` (case-sensitive, as a whole keyword: followed by `:`, whitespace, or end of message). Otherwise blocks with reason exactly: `Your final message must be a status line: PAUSED: <ledger last line> | STOPPED: <question> | COMPLETE <report>. Re-issue your status now.` `stop_hook_active: true` always passes. Malformed payloads exit 0 silently.
- **Controller** (spec 5.2): `agents/sdd-controller.md`, frontmatter `name: sdd-controller`, `tools: Read, Write, Edit, Glob, Grep, Bash, Skill, Agent`, `model: inherit`, no `hooks` field, no SendMessage, no ListAgents. Spawn prompt is two lines `PLAN: <abs>` / `ROOT: <abs>`; resume message `RULING: <answer>`. Final message of every wake begins with `PAUSED:`, `STOPPED:` or `COMPLETE`. Never Read a file whole that may exceed 25,000 tokens.
- **Driver** (spec 5.4): `commands/implement-from-plan.md`; run record `.claude/sdd-run.json` = `{"plan": "<abs>", "root": "<abs>"}` in `.claude/` of the repository root current at invocation; plan resolution order: argument, run record, pointer `.claude/last-plan-doc`, ask; spawn `subagent_type: "claude-toolkit:sdd-controller"` (namespaced; the bare name does not resolve), unnamed, no `model` unless asked; never poll.
- **Deletion** (spec 5.6): `plugins/claude-toolkit/skills/or-superpowers-at-scale/` (SKILL.md + 13 assets) and the ten `plugins/claude-toolkit/agents/or-*.md` files. `docs/superpowers/validation/*`, `docs/superpowers/handovers/*` and `.claude/worktrees/*` are untouched.
- **Release** (spec 5.6): version `1.7.2` -> `2.0.0` in `plugins/claude-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` `metadata.version` and `plugins[0].version`; descriptions name the controller and driver; README per `claude-toolkit:updating-plugin`.
- **Testing rule** (spec 8, `~/.claude/rules/black-box-testing.md`): every test names the promise it holds (the spec section, in its comment), asserts the whole claim, is built on the state most likely to break it, and is shown red before it is accepted. **Red evidence is mandatory:** each "run to verify it fails" step's actual failing assertion is pasted into the task report. A test that is a regression pin (green before and after) says so in its comment and its red evidence is produced by the temporary code change the step names, then reverted.
- **Test commands:** `python -m pytest tests/hooks/test_context_usage.py -q`, `python -m pytest tests/hooks/test_sdd_controller_status.py -q`, full suite `python -m pytest tests/ -q` plus `node --test "tests/hooks/*.test.mjs"`. Tests write real state files under `~/.claude/hooks/state/` keyed by a per-test UUID session id and remove them in cleanup.
- **`.claude/` is git-ignored** in this repository, so `.claude/sdd-run.json` and `.claude/last-plan-doc` are local files, never committed. `.superpowers/` (the SDD workspace) is self-ignoring.
- **The live spikes are post-release** (spec 5.6 "After release", spec 8 "Live spikes"): they need the installed plugin at 2.0.0 and a restarted session, so they are the acceptance checklist at the end of this document, not an SDD task. SDD executes Tasks 1-7 only.

## File Structure

| File | Task | Responsibility |
|---|---|---|
| `plugins/claude-toolkit/hooks/context-usage.py` | 1, 2, 3 | The pause authority. Task 1: scope resolution on every event (`Target`, `measurement_target`, derived path) + `PostToolUseFailure`. Task 2: scope-aware message composition (`checkpoint_message`). Task 3: turn-end addendum (`informational_already_announced`). |
| `tests/hooks/test_context_usage.py` | 1, 2, 3 | Spec 8 promises 1-7 and the `PostToolUseFailure` half of promise 10 (extends the existing suite). |
| `plugins/claude-toolkit/hooks/hooks.json` | 1, 4 | Task 1: register `PostToolUseFailure`. Task 4: register the guard under `SubagentStop` with the anchored matcher. |
| `plugins/claude-toolkit/hooks/sdd-controller-status.py` | 4 | The status-line guard (spec 5.3). |
| `tests/hooks/test_sdd_controller_status.py` | 4 | Spec 8 promises 8, 9 and the guard half of promise 10. |
| `plugins/claude-toolkit/agents/sdd-controller.md` | 5 | The controller: SDD plus a pause protocol (spec 5.2, 5.5, 6). |
| `plugins/claude-toolkit/commands/implement-from-plan.md` | 6 | The driver (spec 5.4, 5.5, 6). |
| `plugins/claude-toolkit/skills/or-superpowers-at-scale/**`, `plugins/claude-toolkit/agents/or-*.md` | 7 | Deleted (spec 5.6). |
| `plugins/claude-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`, `plugins/claude-toolkit/skills/{community,dependency}-research-methodology/SKILL.md` | 7 | 2.0.0 release: versions, descriptions, README listing, dangling or-* mentions (spec 5.6). |

Task order is load-bearing: Tasks 1 -> 2 -> 3 each build on the previous hook change; Task 4 is independent; Task 5 relies on the hook wording ("per your pause protocol", Task 2) and the guard grammar (Task 4); Task 6 relies on the controller's contract (Task 5); Task 7 is last.

---

### Task 1: Hook - agent-scoped measurement on every event, PostToolUseFailure registered

**Files:**
- Modify: `plugins/claude-toolkit/hooks/context-usage.py` (docstring lines 2-107; constants lines 180-204; `measurement_target` lines 289-330; `main` lines 378-433)
- Modify: `plugins/claude-toolkit/hooks/hooks.json`
- Test: `tests/hooks/test_context_usage.py`

**Interfaces:**
- Consumes: the existing helpers `str_field`, `warn`, `latest_main_thread_usage(transcript, include_sidechain)`, `load_state`, `save_state`, `emit_for`, `highest_crossing`.
- Produces (used by Tasks 2 and 3): `SCOPE_MAIN = "main"`, `SCOPE_AGENT = "agent"`, `EVENT_TOOL_FAILURE = "PostToolUseFailure"`, `class Target(transcript: Path, state_id: str, scope: str)` with property `include_sidechain`, `derived_agent_transcript(transcript_path: str, agent_id: str) -> Path`, `measurement_target(payload: dict, event_name: str) -> Target | None`. `main()` reads `target.transcript`, `target.state_id`, `target.include_sidechain`, and (from Task 2 on) `target.scope`.

- [ ] **Step 1: Add the derived-path fixture and the spec-8 tests 1, 2, 4, 6 and the registration test**

Add to `tests/hooks/test_context_usage.py`. First a module-level constant after `STATE_DIR`:

```python
HOOKS_JSON = REPO_ROOT / "plugins" / "claude-toolkit" / "hooks" / "hooks.json"
```

Then replace the existing `_agent_transcript` helper with an entry builder plus two path helpers (the explicit-path fixture keeps its name and location so every existing test still works):

```python
    def _agent_entry(self, tokens, agent_id):
        """One assistant entry as the harness writes it in an agent's own
        transcript: isSidechain on every line (verified on-disk shape)."""
        return {
            "type": "assistant",
            "isSidechain": True,
            "agentId": agent_id,
            "message": {
                "usage": {
                    "input_tokens": tokens,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 0,
                }
            },
        }

    def _agent_transcript(self, tokens, agent_id):
        """An agent transcript at an EXPLICIT path (what SubagentStop names in
        agent_transcript_path)."""
        path = self.tmp_dir / f"agent-{agent_id}.jsonl"
        path.write_text(
            json.dumps(self._agent_entry(tokens, agent_id)) + "\n", encoding="utf-8"
        )
        return path

    def _derived_agent_transcript(self, tokens, agent_id):
        """The agent's own transcript where the harness puts it, relative to
        the MAIN transcript this fixture writes at <tmp>/transcript.jsonl:
        <tmp>/transcript/subagents/agent-<id>.jsonl (spec 5.1 rule 1, K:70-74)."""
        path = self.tmp_dir / "transcript" / "subagents" / f"agent-{agent_id}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._agent_entry(tokens, agent_id)) + "\n", encoding="utf-8"
        )
        return path
```

Then add a new test section after the existing `# --- informational path (UserPromptSubmit / PostToolUse): unchanged ---` tests:

```python
    # --- spec 5.1 rules 1-2: the hook measures whoever it is talking to.
    # --- Every event carrying agent_id is agent-scoped: the agent's OWN
    # --- transcript (derived beside the main one) under <session>--<agent>
    # --- state. Never the parent's, never a fallback.

    def test_tool_events_with_agent_id_measure_the_agents_own_transcript(self):
        # Spec 8 test 1 (5.1 rule 1). Built to break the promise both ways:
        # parent far past 200k with the agent under every threshold (a
        # parent-scoped read announces), then the reverse (a parent-scoped
        # read stays silent). PostToolUse and PostToolUseFailure alike.
        for event in ("PostToolUse", "PostToolUseFailure"):
            with self.subTest(event=event, case="parent 250k, agent 50k"):
                agent_id = f"low{event}"
                self._derived_agent_transcript(50_000, agent_id)
                self.assertEqual(self.run_hook(event, 250_000, agent_id=agent_id), "")
            with self.subTest(event=event, case="parent 50k, agent 210k"):
                agent_id = f"high{event}"
                self._derived_agent_transcript(210_000, agent_id)
                out = json.loads(self.run_hook(event, 50_000, agent_id=agent_id))
                ctx = out["hookSpecificOutput"]
                self.assertEqual(ctx["hookEventName"], event)
                self.assertIn("[210,000 tokens used]", ctx["additionalContext"])
                self.assertIn("200k", ctx["additionalContext"])

    def test_agent_crossing_leaves_parent_state_byte_identical(self):
        # Spec 8 test 2 (5.1 rule 1). The parent already owns a state file
        # (its own 100k announce), so "untouched" is byte identity, not
        # absence. The parent sits at 110k: a mis-scoped PostToolUse would
        # record tool=100000 there and change the bytes.
        self.run_hook("UserPromptSubmit", 110_000)
        parent_state = STATE_DIR / f"context-usage-{self.session_id}.json"
        before = parent_state.read_bytes()
        self._derived_agent_transcript(210_000, "aaa111")
        out = self.run_hook("PostToolUse", 110_000, agent_id="aaa111")
        self.assertIn("200k", out)
        self.assertEqual(parent_state.read_bytes(), before)
        agent_state = STATE_DIR / f"context-usage-{self.session_id}--aaa111.json"
        self.assertEqual(
            json.loads(agent_state.read_text(encoding="utf-8"))["tool"], 200_000
        )

    def test_agent_id_without_resolvable_transcript_skips_with_breadcrumb(self):
        # Spec 8 test 4 (5.1 rule 2). No explicit field, no derived file, and
        # the parent at 300k beside it: any fallback would announce. Expect
        # nothing on stdout, no state file for either identity, and a stderr
        # breadcrumb naming the agent.
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "PostToolUse",
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(300_000)),
            "agent_id": "ghost1",
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("ghost1", proc.stderr)
        self.assertEqual(
            list(STATE_DIR.glob(f"context-usage-{self.session_id}*.json")), []
        )

    def test_post_tool_use_and_failure_share_the_tool_key(self):
        # Spec 8 test 6 (5.1 events). A threshold announced by one event is
        # not re-announced by the other - both orders, both scopes, each on
        # a fresh identity.
        for first, second in (
            ("PostToolUse", "PostToolUseFailure"),
            ("PostToolUseFailure", "PostToolUse"),
        ):
            with self.subTest(scope="agent", first=first):
                agent_id = f"share{first}"
                self._derived_agent_transcript(210_000, agent_id)
                self.assertIn("200k", self.run_hook(first, 50_000, agent_id=agent_id))
                self._derived_agent_transcript(215_000, agent_id)
                self.assertEqual(self.run_hook(second, 50_000, agent_id=agent_id), "")
        with self.subTest(scope="main"):
            self.assertIn("200k", self.run_hook("PostToolUseFailure", 210_000))
            self.assertEqual(self.run_hook("PostToolUse", 215_000), "")

    def test_hooks_json_registers_post_tool_use_failure_with_context_usage(self):
        # Spec 8 test 10, context-usage half (5.1 events): PostToolUseFailure
        # runs the same command with the same timeout as PostToolUse.
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]

        def context_usage_entries(event):
            return [
                h for entry in hooks.get(event, []) for h in entry["hooks"]
                if "context-usage.py" in h["command"]
            ]

        success = context_usage_entries("PostToolUse")
        failure = context_usage_entries("PostToolUseFailure")
        self.assertEqual(len(success), 1)
        self.assertEqual(len(failure), 1)
        self.assertEqual(failure[0]["command"], success[0]["command"])
        self.assertEqual(failure[0]["timeout"], success[0]["timeout"])
        self.assertNotIn("PostToolBatch", hooks)
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `python -m pytest tests/hooks/test_context_usage.py -q -k "agents_own_transcript or byte_identical or resolvable_transcript or share_the_tool_key or registers_post_tool_use_failure"`

Expected: 5 failed. Paste each failing assertion into the task report. Expected shapes: `test_tool_events_with_agent_id_measure_the_agents_own_transcript` fails on `assertEqual(..., "")` with a 250k announcement (parent measured); `test_agent_crossing_leaves_parent_state_byte_identical` fails on the byte comparison; `test_agent_id_without_resolvable_transcript_skips_with_breadcrumb` fails on `assertEqual(proc.stdout.strip(), "")` with a 300k announcement; `test_post_tool_use_and_failure_share_the_tool_key` fails on `assertIn("200k", ...)` for the Failure-first order; the registration test fails on `assertEqual(len(failure), 1)` with `0 != 1`.

Also run the whole file: `python -m pytest tests/hooks/test_context_usage.py -q` and confirm only those 5 fail (the pre-existing tests stay green).

- [ ] **Step 3: Replace the constants block and `measurement_target`**

In `plugins/claude-toolkit/hooks/context-usage.py`, add `from dataclasses import dataclass` to the imports. Replace the block from `STATE_DIR = ...` through the end of `EVENT_STATE_KEYS = {...}` (lines 180-204) with:

```python
STATE_DIR = Path.home() / ".claude" / "hooks" / "state"
SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]")
RESET_RATIO = 0.5

SCOPE_MAIN = "main"
SCOPE_AGENT = "agent"

EVENT_PROMPT = "UserPromptSubmit"
EVENT_TOOL = "PostToolUse"
EVENT_TOOL_FAILURE = "PostToolUseFailure"
EVENT_STOP = "Stop"
EVENT_SUBAGENT_STOP = "SubagentStop"
TURN_END_EVENTS = (EVENT_STOP, EVENT_SUBAGENT_STOP)

STATE_KEY_PROMPT = "prompt"
STATE_KEY_TOOL = "tool"
STATE_KEY_STOP = "stop"
STATE_KEY_SUBAGENT_STOP = "subagent_stop"
STATE_KEYS = (
    STATE_KEY_PROMPT,
    STATE_KEY_TOOL,
    STATE_KEY_STOP,
    STATE_KEY_SUBAGENT_STOP,
)

# PostToolUse and PostToolUseFailure share one key: one mid-turn announcement
# per threshold, whichever event lands first (a failed tool call fires only
# PostToolUseFailure - the depth-1 probe missed three failed Reads for exactly
# this reason, K:50-57).
EVENT_STATE_KEYS = {
    EVENT_PROMPT: STATE_KEY_PROMPT,
    EVENT_TOOL: STATE_KEY_TOOL,
    EVENT_TOOL_FAILURE: STATE_KEY_TOOL,
    EVENT_STOP: STATE_KEY_STOP,
    EVENT_SUBAGENT_STOP: STATE_KEY_SUBAGENT_STOP,
}
```

Replace the whole `measurement_target` function (its docstring included) with:

```python
@dataclass(frozen=True)
class Target:
    """Whose context this event measures."""

    transcript: Path
    state_id: str
    scope: str  # SCOPE_MAIN or SCOPE_AGENT

    @property
    def include_sidechain(self) -> bool:
        # Agent transcripts are wholly isSidechain:true, so the filter would
        # blind the read there; main transcripts keep excluding sidechain
        # entries (historical inline-sidechain format).
        return self.scope == SCOPE_AGENT


def derived_agent_transcript(transcript_path: str, agent_id: str) -> Path:
    """The agent's own transcript as the harness lays it out on disk
    (verified on 2.1.269, K:70-74): <main transcript stem>/subagents/agent-<id>.jsonl."""
    return (
        Path(transcript_path).with_suffix("") / "subagents" / f"agent-{agent_id}.jsonl"
    )


def measurement_target(payload: dict, event_name: str) -> Target | None:
    """Resolve whose context this event measures (spec 5.1 rules 1-4).

    Agent-scoped when the payload carries a string agent_id or an explicit
    agent-transcript field (agent_transcript_path; docs alias
    subagent_transcript_path). The transcript is the explicit field when
    present, else the derived path; the first candidate that exists wins.
    The state identity is <session_id>--<agent_id>, agent_id falling back
    to the explicit transcript's stem. No candidate on disk: skip with a
    breadcrumb and NEVER measure the parent's transcript_path - mis-scoped
    measurement is the bug this resolution exists to prevent.

    Main-scoped otherwise: transcript_path under session_id. SubagentStop
    naming no agent identity at all keeps its skip.

    Payload fields are read via str_field: a non-string value is malformed
    input, warned and treated as absent.
    """
    session_id = str_field(payload, "session_id") or "default"
    agent_id = str_field(payload, "agent_id")
    explicit = str_field(payload, "agent_transcript_path") or str_field(
        payload, "subagent_transcript_path"
    )
    transcript_path = str_field(payload, "transcript_path")

    if agent_id is None and explicit is None:
        if event_name == EVENT_SUBAGENT_STOP:
            warn(
                "SubagentStop payload missing agent_id and agent_transcript_path/"
                "subagent_transcript_path - skipping (cannot measure the "
                "agent's own context)"
            )
            return None
        if not transcript_path:
            return None
        return Target(Path(transcript_path), session_id, SCOPE_MAIN)

    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if agent_id and transcript_path:
        candidates.append(derived_agent_transcript(transcript_path, agent_id))
    identity = agent_id or Path(explicit).stem
    for candidate in candidates:
        if candidate.exists():
            return Target(candidate, f"{session_id}--{identity}", SCOPE_AGENT)
    looked_at = " or ".join(str(c) for c in candidates) or "<no candidate path>"
    warn(
        f"agent-scoped {event_name} for agent {identity!r}: no transcript at "
        f"{looked_at} - skipping (never measuring the parent transcript)"
    )
    return None
```

- [ ] **Step 4: Use the `Target` in `main()`**

In `main()`, replace the block

```python
    target = measurement_target(payload, event_name)
    if target is None:
        return 0
    transcript_path, state_id, include_sidechain = target
    p = Path(transcript_path)
    if not p.exists():
        return 0

    usage = latest_main_thread_usage(p, include_sidechain=include_sidechain)
    if not usage:
        return 0

    current = total_tokens(usage)
    state = load_state(state_id)
```

with

```python
    target = measurement_target(payload, event_name)
    if target is None:
        return 0
    if not target.transcript.exists():
        return 0

    usage = latest_main_thread_usage(
        target.transcript, include_sidechain=target.include_sidechain
    )
    if not usage:
        return 0

    current = total_tokens(usage)
    state = load_state(target.state_id)
```

and replace the two later `save_state(state_id, state)` calls with `save_state(target.state_id, state)`.

- [ ] **Step 5: Register `PostToolUseFailure` in hooks.json**

Replace `plugins/claude-toolkit/hooks/hooks.json` with:

```json
{
  "description": "Context-window checkpoint hook — measures the context of whoever the event is talking to (the agent's own transcript whenever the payload carries an agent_id, else the main session's) and announces once per measurement identity, per channel, when token usage crosses 100k / 200k / 250k / 300k. Each warning reports the crossing and its implication for reasoning quality; the ≥200k warnings additionally instruct the baseline response — wrap up and use /handover, escalating to stop-immediately at 250k/300k, with 300k noting that work quality may have been compromised (the agent definition's own protocol carries the detail). Informational events (UserPromptSubmit, PostToolUse, PostToolUseFailure — the two tool events share one announcement) inject additionalContext mid-turn; turn-end events (Stop/SubagentStop) deliver actionable (≥200k) crossings as decision:block, forcing one delivery turn (E2E F20/F22). Also ships the raw-fetch pipeline hooks: PreToolUse/WebFetch — unconditional deny that teaches the pipeline (deny-webfetch.mjs); SessionStart — injects the web-research doctrine rendered from web-doctrine.md with resolved plugin paths (inject-web-doctrine.mjs).",
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 3
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 3
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/deny-webfetch.mjs\"",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/inject-web-doctrine.mjs\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: Rewrite the module docstring**

Replace the entire module docstring of `context-usage.py` (the triple-quoted block at the top of the file, lines 2-107) with the following. Paragraphs marked "unchanged" are copied verbatim from today's docstring; the rest describe the new scope rule and retire the two paragraphs that are now false (the "PostToolUse carries no agent identifier" residual and the "or-* tiers" phrasing).

```python
"""Context-window checkpoint hook (UserPromptSubmit, PostToolUse,
PostToolUseFailure, Stop, SubagentStop).

Reads the transcript of whoever the event is talking to, computes that
context's current usage, and announces a checkpoint crossing exactly once
per measurement identity, per channel:

  UserPromptSubmit   -> informational: injects additionalContext into the
                        assistant's view at the start of each turn
  PostToolUse        -> informational: injects additionalContext mid-turn,
  PostToolUseFailure    immediately after the next tool call - succeeded
                        or failed - following a crossing, so the assistant
                        can adapt mid-task. The two events share one state
                        key ("tool"): one announcement per threshold,
                        whichever lands first. PostToolUse fires only after
                        a tool call succeeds; a failed call fires
                        PostToolUseFailure (K:50-57).
  Stop               -> turn-end: for ACTIONABLE crossings (>= 200k) returns
                        {"decision": "block", "reason": <context warning>},
                        forcing exactly one more turn so the warning reaches
                        the agent. Sub-actionable crossings never block (never
                        force a turn for information).
  SubagentStop       -> turn-end: same as Stop, measured on the agent's own
                        transcript like every other agent-scoped event.

Scope resolution (2026-09-11; extends the SubagentStop-only agent scoping
of 2026-06-06 to every event): the hook measures the context of whoever it
is talking to. On Claude Code 2.1.269 every event fired inside a subagent
carries agent_id and agent_type while transcript_path names the MAIN
session's transcript (docs/research/2026-09-11-spike-posttooluse-subagent-
context.md, K:68-71). Rules, in order:

  1. A payload carrying a string agent_id - or an explicit agent-transcript
     field - is AGENT-SCOPED. The transcript is agent_transcript_path
     (docs alias subagent_transcript_path) when present, else the derived
     path
       Path(transcript_path).with_suffix("") / "subagents"
                                            / f"agent-{agent_id}.jsonl"
     which is where the harness writes the agent's own transcript. The
     state identity is <session_id>--<agent_id> (agent_id falls back to
     the explicit transcript's stem). Agent transcripts are entirely
     isSidechain:true, so sidechain entries count there.
  2. Agent-scoped but no candidate transcript exists on disk: skip with a
     stderr breadcrumb. NEVER fall back to the parent's transcript -
     mis-scoped measurement is the bug this rule exists to prevent.
  3. Otherwise the event is MAIN-SCOPED: measure transcript_path under
     session_id, excluding sidechain entries (guards against the
     historical inline-sidechain format).
  4. SubagentStop naming no agent identity at all keeps its skip (with a
     breadcrumb), never the parent's transcript.

Advisory plus instruction (design change 2026-07-21, reversing the earlier
sensor-only stance): every message reports the figure, the threshold, and
the resulting implication for reasoning quality; the ACTIONABLE (>= 200k)
messages additionally carry the baseline instruction - wrap up and use
/handover - escalating to "stop immediately" at 250k/300k, and at 300k
noting that work quality may have been compromised. The sub-actionable
100k checkpoint stays advisory-only. Tier-specific protocol detail lives
in the agent definition's own protocol; the hook's instruction is the
baseline, not the full protocol.

Why turn-end events (E2E findings F20/F22): in inbox-driven team loops both
UserPromptSubmit and PostToolUse are starved - teammate-inbox deliveries
trigger neither - so an agent can blow past every checkpoint with zero
announcements. Stop/SubagentStop fire reliably at turn end in those loops,
but they fire AFTER the assistant's response, so additionalContext has no
in-progress turn to land in; the block path is the only delivery that works
there, and it is reserved for actionable crossings. The block is a delivery
channel, not enforcement.

Loop safety: a blocked turn-end forces one more turn whose own Stop fires
with stop_hook_active=true - the hook exits immediately on that flag. The
once-per-threshold state prevents re-announcing the same threshold.

Checkpoints (cumulative tokens):
  100,000  - informational only. Left the 0-100k prime-thinking zone.
  200,000  - ACTIONABLE: also delivered via the turn-end block. Instructs:
             wrap up and use /handover.
  250,000  - ACTIONABLE: instructs: stop immediately, wrap up, /handover.
  300,000  - ACTIONABLE: as 250k, plus note that work quality may have
             been compromised.

State files (one JSON per measurement identity):
  main loop:  ~/.claude/hooks/state/context-usage-<session_id>.json
  per agent:  ~/.claude/hooks/state/
              context-usage-<session_id>--<agent_id>.json
  Shape: {"prompt": <t>, "tool": <t>, "stop": <t>, "subagent_stop": <t>}
  Files appear only on a first crossing, so accumulation is bounded to
  identities that actually cross.
  Legacy field "last_announced" migrates to "prompt" on first read.

Reset: if current usage falls below 50% of any previously announced threshold
(e.g. after /compact or /rewind), all tracked thresholds reset - and the
reset is persisted immediately, so turn-end detection (which announces
nothing below 200k that could piggyback persistence) re-arms too.

Accepted residual (per-wake re-warning, Spike 9 2026-06-06): the harness
assigns every teammate WAKE a fresh agent_id and a fresh wake transcript,
so per-agent once-per-threshold state never carries across wakes - a
teammate that wakes still over an actionable threshold is re-warned (one
forced turn) at every wake until its context shrinks. Under sensor
semantics that is "one warning per wake while over-threshold" - accepted
delivery behavior, not a defect. Cross-wake identity engineering (payload
introspection for a wake-stable key, transcript lineage) was considered
and rejected as over-engineering.

Accepted residual (duplicate announce under parallel tool calls): PostToolUse
runs concurrently per tool inside a parallel batch (R:30), so two tool
events of one identity can both read the pre-announce state and both
announce the same threshold once. Harmless: a repeated warning, never a
missed one.

Malformed input (non-dict state file / stdin payload / transcript entry,
non-numeric usage field, non-string payload string-field) degrades
gracefully - fresh state, skipped entry, field counted as 0, or field
treated as absent - with a one-line stderr breadcrumb naming what was
malformed (visible under claude --debug; exit code stays 0). The breadcrumb
exists because the likeliest trigger is transcript-format drift in a future
Claude Code release, whose natural symptom - checkpoints silently never
firing again - is exactly the starvation this hook exists to fix (F20/F22).
"""
```

- [ ] **Step 7: Run the whole hook suite to verify it passes**

Run: `python -m pytest tests/hooks/test_context_usage.py -q`

Expected: all pass (every pre-existing test plus the 5 new ones). Then `node --test "tests/hooks/*.test.mjs"` - expected: pass (hooks.json is still valid JSON with the two node hooks intact).

- [ ] **Step 8: Commit**

```bash
git add plugins/claude-toolkit/hooks/context-usage.py plugins/claude-toolkit/hooks/hooks.json tests/hooks/test_context_usage.py
git commit -m "hook: agent-scoped measurement on every event; register PostToolUseFailure" -m "Every event carrying agent_id now measures the agent's own transcript (explicit field, else <stem>/subagents/agent-<id>.jsonl) under <session>--<agent> state, never the parent's. PostToolUse and PostToolUseFailure share the tool key. Spec 5.1 rules 1-4 and events; spec 8 tests 1, 2, 4, 6, 10 (context-usage half)."
```

---

### Task 2: Hook - scope-aware instruction suffix

**Files:**
- Modify: `plugins/claude-toolkit/hooks/context-usage.py` (the `CHECKPOINTS` / `ACTIONABLE_CHECKPOINTS` blocks and their comments, lines 109-178 of the pre-Task-1 file; `highest_crossing`; `main`; one docstring paragraph)
- Test: `tests/hooks/test_context_usage.py`

**Interfaces:**
- Consumes: `SCOPE_MAIN`, `SCOPE_AGENT`, `Target.scope` (Task 1).
- Produces (used by Task 3): `CHECKPOINTS: tuple[int, ...]`, `ACTIONABLE_CHECKPOINTS: tuple[int, ...]`, `checkpoint_message(threshold: int, scope: str, turn_end: bool) -> str`, `highest_crossing(thresholds, current, announced) -> int | None` (now returns the threshold only). The agent-scope instruction contains the phrase `per your pause protocol`, which Task 5's controller keys on.

- [ ] **Step 1: Add the wording tests (spec 8 test 5) and tighten the two main-scope wording pins**

Add to `tests/hooks/test_context_usage.py`, after the scope tests from Task 1:

```python
    # --- spec 5.1 wording: the instruction suffix is chosen by scope. Agent
    # --- scope names the pause protocol and never /handover; main scope
    # --- keeps /handover and never mentions a pause protocol.

    def test_agent_scoped_warnings_instruct_the_pause_protocol_never_handover(self):
        # Spec 8 test 5. Both channels (mid-turn additionalContext and the
        # turn-end block), all three actionable tiers, walked in escalation
        # on one identity per channel.
        for channel in ("PostToolUse", "SubagentStop"):
            agent_id = f"word{channel}"
            messages = {}
            for tokens, tier in ((210_000, "200k"), (260_000, "250k"), (310_000, "300k")):
                self._derived_agent_transcript(tokens, agent_id)
                out = json.loads(self.run_hook(channel, 50_000, agent_id=agent_id))
                messages[tier] = (
                    out["reason"] if channel == "SubagentStop"
                    else out["hookSpecificOutput"]["additionalContext"]
                )
            for tier, text in messages.items():
                with self.subTest(channel=channel, tier=tier):
                    self.assertIn(tier, text)
                    self.assertIn("reasoning", text.lower())      # advisory kept
                    self.assertIn("per your pause protocol", text)  # instruction
                    self.assertIn("record your state", text)
                    self.assertNotIn("/handover", text)
                    self.assertNotIn("operating instructions", text.lower())
            with self.subTest(channel=channel, tier="escalation"):
                self.assertNotIn("stop immediately", messages["200k"].lower())
                self.assertIn("stop immediately", messages["250k"].lower())
                self.assertIn("stop immediately", messages["300k"].lower())
                self.assertNotIn("compromised", messages["200k"].lower())
                self.assertNotIn("compromised", messages["250k"].lower())
                self.assertIn("compromised", messages["300k"].lower())
            if channel == "SubagentStop":
                for text in messages.values():
                    self.assertIn("forced", text)  # turn-end note kept

    def test_agent_scoped_100k_stays_advisory_only(self):
        # Spec 5.1 wording: the sub-actionable checkpoint carries no
        # instruction in either scope.
        self._derived_agent_transcript(110_000, "adv111")
        out = json.loads(self.run_hook("PostToolUse", 50_000, agent_id="adv111"))
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("100k", ctx)
        self.assertNotIn("pause protocol", ctx)
        self.assertNotIn("/handover", ctx)
```

Then in the two existing main-scope wording tests, `test_turn_end_reasons_carry_advisory_and_instruction_at_every_tier` and `test_informational_warnings_carry_advisory_and_instruction`, add one assertion inside their per-tier `subTest` loop, directly after the `/handover` assertion:

```python
                self.assertNotIn("pause protocol", reason)   # main scope never names it
```

(in the second test the variable is `ctx`, not `reason`). Update each test's comment with the line: `Spec 5.1 wording: main-scoped 200k+ messages always say /handover and never name a pause protocol.`

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `python -m pytest tests/hooks/test_context_usage.py -q -k "pause_protocol_never_handover or 100k_stays_advisory"`

Expected: `test_agent_scoped_warnings_instruct_the_pause_protocol_never_handover` FAILS on `assertIn("per your pause protocol", text)` (today's agent-scoped message says `/handover`). `test_agent_scoped_100k_stays_advisory_only` passes already (regression pin: the 100k message carries no instruction in any version; its red evidence is Step 4 below). Paste the failing assertion into the report.

- [ ] **Step 3: Replace the message tables and composition**

In `context-usage.py`, replace everything from the comment `# Informational wording (additionalContext on UserPromptSubmit/PostToolUse).` through the closing `]` of `ACTIONABLE_CHECKPOINTS` with:

```python
# Message composition. Every checkpoint message is: advisory (figure is
# prepended by main(); then "Context checkpoint <label> crossed" and the
# implication for reasoning quality), the turn-end note when the message
# is delivered by a forced turn, then the instruction chosen by SCOPE - the
# hook knows whose context it measured, and no agent should have to
# translate "/handover" into its own pause protocol. 100k carries no
# instruction in either scope: it is context, not a directive.
CHECKPOINTS = (100_000, 200_000, 250_000, 300_000)
# >=200k: the instruction is carried, and turn-end events may block. 100k is
# deliberately absent: never force a turn for a sub-actionable checkpoint.
ACTIONABLE_CHECKPOINTS = (200_000, 250_000, 300_000)

LABELS = {100_000: "100k", 200_000: "200k", 250_000: "250k", 300_000: "300k"}

IMPLICATIONS = {
    100_000: (
        "The first 100k tokens - the highest-quality reasoning zone - are "
        "consumed."
    ),
    200_000: (
        "You are well past the peak-quality reasoning zone - recall of "
        "earlier context is less reliable and multi-step reasoning is more "
        "error-prone than at the start."
    ),
    250_000: (
        "Reasoning quality is significantly degraded - earlier context is "
        "increasingly likely to be missed, misremembered, or contradicted."
    ),
    300_000: (
        "Reasoning quality is severely degraded - expect dropped context, "
        "overlooked instructions, and inconsistent output."
    ),
}

INSTRUCTIONS = {
    SCOPE_MAIN: {
        200_000: (
            "Wrap up your current work and use /handover to continue in a "
            "fresh session."
        ),
        250_000: (
            "Stop immediately: wrap up and use /handover to continue in a "
            "fresh session."
        ),
        300_000: (
            "Stop immediately: wrap up and use /handover to continue in a "
            "fresh session, noting in the handover that work quality may "
            "have been compromised."
        ),
    },
    SCOPE_AGENT: {
        200_000: (
            "Finish the step you are in, record your state, and end your "
            "turn per your pause protocol so a fresh agent can continue."
        ),
        250_000: (
            "Stop immediately: finish the step you are in, record your "
            "state, and end your turn per your pause protocol so a fresh "
            "agent can continue."
        ),
        300_000: (
            "Stop immediately: finish the step you are in, record your "
            "state, and end your turn per your pause protocol so a fresh "
            "agent can continue, noting in your recorded state that work "
            "quality may have been compromised."
        ),
    },
}

# Turn-end delivery (decision:block on Stop/SubagentStop) explains the
# forced turn mechanically. The block is a DELIVERY channel, not
# enforcement: in inbox-driven loops only turn-end events fire reliably
# (F20/F22), and additionalContext is discarded there.
TURN_END_NOTE = "This turn was forced so the warning could reach you."


def checkpoint_message(threshold: int, scope: str, turn_end: bool) -> str:
    detection = " (turn-end detection)" if turn_end else ""
    parts = [
        f"Context checkpoint {LABELS[threshold]} crossed{detection}. "
        f"{IMPLICATIONS[threshold]}"
    ]
    if turn_end:
        parts.append(TURN_END_NOTE)
    instruction = INSTRUCTIONS[scope].get(threshold)
    if instruction:
        parts.append(instruction)
    return " ".join(parts)
```

Replace `highest_crossing` with:

```python
def highest_crossing(thresholds, current, announced) -> int | None:
    """The highest threshold at/below current that exceeds what this state
    key already announced, or None."""
    crossed = [t for t in thresholds if current >= t]
    if not crossed:
        return None
    threshold = crossed[-1]
    return None if threshold <= announced else threshold
```

In `main()`, replace

```python
    key = EVENT_STATE_KEYS.get(event_name, STATE_KEY_PROMPT)
    checkpoints = ACTIONABLE_CHECKPOINTS if turn_end else CHECKPOINTS
    crossing = highest_crossing(checkpoints, current, state[key])
    if crossing is None:
        return 0
    threshold, message = crossing

    state[key] = threshold
    save_state(target.state_id, state)

    full_msg = f"[{current:,} tokens used] {message}"
```

with

```python
    key = EVENT_STATE_KEYS.get(event_name, STATE_KEY_PROMPT)
    thresholds = ACTIONABLE_CHECKPOINTS if turn_end else CHECKPOINTS
    threshold = highest_crossing(thresholds, current, state[key])
    if threshold is None:
        return 0

    state[key] = threshold
    save_state(target.state_id, state)

    message = checkpoint_message(threshold, target.scope, turn_end)
    full_msg = f"[{current:,} tokens used] {message}"
```

Then replace the docstring paragraph beginning `Advisory plus instruction (design change 2026-07-21` (ending `...the baseline, not the full protocol.`) with:

```
Advisory plus instruction (2026-07-21; scope-aware since 2026-09-11):
every message reports the figure, the threshold, and the resulting
implication for reasoning quality; the ACTIONABLE (>= 200k) messages
additionally carry the baseline instruction, chosen by scope because the
hook knows whose context it measured and no agent should have to
translate "/handover":
  main scope  - wrap up and use /handover to continue in a fresh session
  agent scope - finish the step you are in, record your state, and end
                your turn per your pause protocol so a fresh agent can
                continue
escalating to "stop immediately" at 250k/300k, and at 300k noting that
work quality may have been compromised. Agent-scoped messages never
contain "/handover"; main-scoped actionable messages always do. The
sub-actionable 100k checkpoint stays advisory-only in both scopes. What
"pause protocol" means lives in the agent definition's own protocol; the
hook's instruction is the baseline, not the full protocol.
```

and in the "Checkpoints (cumulative tokens)" list change the three `Instructs:` phrases to `Instructs the scope's baseline (main: wrap up + /handover; agent: finish the step, record state, end the turn per the pause protocol).` for 200k, `as 200k, prefixed "stop immediately".` for 250k, and `as 250k, plus note that work quality may have been compromised.` for 300k.

- [ ] **Step 4: Run the tests to verify they pass, and produce the pin's red evidence**

Run: `python -m pytest tests/hooks/test_context_usage.py -q`

Expected: all pass. The main-scope wording is byte-for-byte what it was (the existing wording tests are the proof; they are unchanged apart from the added assertion).

Red evidence for the pin `test_agent_scoped_100k_stays_advisory_only`: temporarily add `100_000: "Finish the step you are in per your pause protocol."` to `INSTRUCTIONS[SCOPE_AGENT]`, run `python -m pytest tests/hooks/test_context_usage.py -q -k 100k_stays_advisory`, paste the failing `assertNotIn("pause protocol", ctx)` into the report, then remove the line and re-run to green.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-toolkit/hooks/context-usage.py tests/hooks/test_context_usage.py
git commit -m "hook: scope-aware instruction suffix - agents are told their pause protocol, never /handover" -m "Messages are composed from advisory + turn-end note + an instruction chosen by measurement scope. Main-scope wording is unchanged. Spec 5.1 wording; spec 8 test 5."
```

---

### Task 3: Hook - turn-end addendum

**Files:**
- Modify: `plugins/claude-toolkit/hooks/context-usage.py` (`main`, one new helper, two docstring paragraphs)
- Test: `tests/hooks/test_context_usage.py`

**Interfaces:**
- Consumes: `STATE_KEY_PROMPT`, `STATE_KEY_TOOL`, `highest_crossing` (Task 2 signature).
- Produces: `informational_already_announced(state: dict, threshold: int) -> bool`.

- [ ] **Step 1: Replace the superseded independence test with the addendum tests (spec 8 test 7)**

Delete `test_turn_end_state_is_independent_of_prompt_state` from `tests/hooks/test_context_usage.py`. Its promise (2026-06-06: a prompt announcement must not silence the turn-end block) is reversed by spec 5.1's approved addendum; per the black-box rule, the test follows the written promise, and the promise changed. Add in its place:

```python
    # --- spec 5.1 turn-end addendum: the block is a delivery channel. Once an
    # --- informational channel (prompt or tool key) has announced threshold
    # --- T for an identity, the turn-end block for T is skipped; it still
    # --- fires when neither did, and for a higher threshold than announced.
    # --- Replaces test_turn_end_state_is_independent_of_prompt_state
    # --- (2026-06-06), whose promise the addendum reverses.

    def test_main_turn_end_skipped_after_prompt_announced_same_threshold(self):
        self.run_hook("UserPromptSubmit", 210_000)
        self.assertEqual(self.run_hook("Stop", 212_000), "")

    def test_main_turn_end_skipped_after_tool_announced_same_threshold(self):
        self.run_hook("PostToolUse", 210_000)
        self.assertEqual(self.run_hook("Stop", 212_000), "")

    def test_agent_turn_end_skipped_after_tool_announced_same_threshold(self):
        # The controller's normal pause: the mid-wake warning (derived
        # transcript) landed, so its SubagentStop (explicit transcript, same
        # agent id) must not force a wasted turn.
        self._derived_agent_transcript(210_000, "aaa111")
        self.assertIn("200k", self.run_hook("PostToolUse", 50_000, agent_id="aaa111"))
        explicit = self._agent_transcript(212_000, agent_id="aaa111")
        self.assertEqual(
            self.run_hook(
                "SubagentStop", 50_000,
                agent_id="aaa111", agent_transcript_path=str(explicit),
            ),
            "",
        )

    def test_turn_end_still_blocks_when_no_informational_channel_announced(self):
        # The starved-loop case the block was built for (F20/F22): no prompt
        # or tool announcement for the identity -> block, both scopes.
        with self.subTest(scope="main"):
            out = json.loads(self.run_hook("Stop", 210_000))
            self.assertEqual(out["decision"], "block")
            self.assertIn("200k", out["reason"])
        with self.subTest(scope="agent"):
            explicit = self._agent_transcript(210_000, agent_id="bbb222")
            out = json.loads(self.run_hook(
                "SubagentStop", 50_000,
                agent_id="bbb222", agent_transcript_path=str(explicit),
            ))
            self.assertEqual(out["decision"], "block")
            self.assertIn("200k", out["reason"])

    def test_turn_end_still_blocks_for_a_higher_threshold_than_announced(self):
        # Whole claim: only the announced threshold T is skipped. A later,
        # higher crossing still forces its delivery turn.
        self.run_hook("UserPromptSubmit", 210_000)
        out = json.loads(self.run_hook("Stop", 260_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("250k", out["reason"])

    def test_reset_rearms_both_channels_together(self):
        # 5.1 addendum, last sentence: the 50 percent reset clears all keys,
        # so after a compaction the turn-end channel is live again even
        # though the prompt channel had announced before it.
        self.run_hook("UserPromptSubmit", 210_000)
        self.assertEqual(self.run_hook("Stop", 212_000), "")   # skipped
        self.assertEqual(self.run_hook("Stop", 90_000), "")    # <50% -> reset
        out = json.loads(self.run_hook("Stop", 210_000))
        self.assertEqual(out["decision"], "block")
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `python -m pytest tests/hooks/test_context_usage.py -q -k "turn_end_skipped or still_blocks or rearms_both"`

Expected: the three `*_skipped_*` tests FAIL on `assertEqual(..., "")` with a `{"decision": "block", ...}` line (today's turn-end state is independent); `test_reset_rearms_both_channels_together` FAILS on its first `assertEqual(..., "")`; the two `still_blocks` tests pass (pins of unchanged behaviour). Paste the failing assertions into the report.

- [ ] **Step 3: Implement the addendum**

In `context-usage.py`, add after `highest_crossing`:

```python
def informational_already_announced(state: dict, threshold: int) -> bool:
    """Turn-end addendum (spec 5.1, 2026-09-11): the block is only a delivery
    channel. If the prompt or tool channel already delivered this threshold
    to this identity mid-turn, forcing a turn would deliver it twice and
    cost the agent a wasted turn per pause."""
    return max(state[STATE_KEY_PROMPT], state[STATE_KEY_TOOL]) >= threshold
```

In `main()`, between `if threshold is None: return 0` and `state[key] = threshold`, insert:

```python
    if turn_end and informational_already_announced(state, threshold):
        return 0
```

Replace the docstring paragraph beginning `Why turn-end events (E2E findings F20/F22):` and the following `Loop safety:` paragraph with:

```
Why turn-end events (E2E findings F20/F22): in inbox-driven team loops both
UserPromptSubmit and PostToolUse are starved - teammate-inbox deliveries
trigger neither - so an agent can blow past every checkpoint with zero
announcements. Stop/SubagentStop fire reliably at turn end in those loops,
but they fire AFTER the assistant's response, so additionalContext has no
in-progress turn to land in; the block path is the only delivery that works
there, and it is reserved for actionable crossings. The block is a delivery
channel, not enforcement.

Turn-end addendum (2026-09-11): because the block is only a delivery
channel, it is skipped when an informational channel (the "prompt" or
"tool" state key) has already announced that threshold for the same
identity - the warning was delivered, and forcing a turn would deliver it
twice, one wasted turn per controller pause. The block still fires when
neither informational channel announced the threshold, which is exactly
the starved-loop case above, and for a higher threshold than the one
announced. The 50 percent reset clears all keys together, so a compaction
re-arms both channels.

Loop safety: a blocked turn-end forces one more turn whose own Stop fires
with stop_hook_active=true - the hook exits immediately on that flag. The
once-per-threshold state prevents re-announcing the same threshold.
```

- [ ] **Step 4: Run the whole suite to verify it passes**

Run: `python -m pytest tests/ -q`

Expected: all pass. Then `node --test "tests/hooks/*.test.mjs"` - expected: pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-toolkit/hooks/context-usage.py tests/hooks/test_context_usage.py
git commit -m "hook: skip the turn-end block when an informational channel already announced the threshold" -m "One wasted forced turn per controller pause removed; the block still fires in the starved-loop case and for higher thresholds. Replaces the 2026-06-06 independence test, whose promise the approved addendum reverses. Spec 5.1 addendum; spec 8 test 7."
```

---

### Task 4: The status-line guard `hooks/sdd-controller-status.py`

**Files:**
- Create: `plugins/claude-toolkit/hooks/sdd-controller-status.py`
- Modify: `plugins/claude-toolkit/hooks/hooks.json`
- Test: `tests/hooks/test_sdd_controller_status.py`

**Interfaces:**
- Consumes: the `SubagentStop` payload fields `last_assistant_message` (string) and `stop_hook_active` (bool) (R:57).
- Produces: the status grammar every controller reply must satisfy (regex `^\s*(PAUSED|STOPPED|COMPLETE)(?::|\s|$)`), and the exact block reason `BLOCK_REASON`. Task 5's controller and Task 6's driver depend on this grammar.

- [ ] **Step 1: Write the failing tests**

Create `tests/hooks/test_sdd_controller_status.py`:

```python
"""Behavioral tests for plugins/claude-toolkit/hooks/sdd-controller-status.py
and its registration in hooks.json (spec 5.3, 6; spec 8 tests 8-10).

Run: python -m pytest tests/hooks/test_sdd_controller_status.py -q

Exercises the real stdin->stdout hook contract via subprocess. The guard
keeps no state, so nothing needs cleaning up.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "plugins" / "claude-toolkit" / "hooks"
GUARD = HOOKS_DIR / "sdd-controller-status.py"
HOOKS_JSON = HOOKS_DIR / "hooks.json"
CONTROLLER_TYPE = "claude-toolkit:sdd-controller"
BLOCK_REASON = (
    "Your final message must be a status line: PAUSED: <ledger last line> | "
    "STOPPED: <question> | COMPLETE <report>. Re-issue your status now."
)


class SddControllerStatusGuardTests(unittest.TestCase):
    def run_guard(self, stdin_text):
        return subprocess.run(
            [sys.executable, str(GUARD)],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def payload(self, message, **extra):
        return json.dumps({
            "hook_event_name": "SubagentStop",
            "session_id": "session-1",
            "agent_id": "agent-1",
            "agent_type": CONTROLLER_TYPE,
            "last_assistant_message": message,
            **extra,
        })

    # Spec 5.3 / 6: a final message that begins, after leading whitespace,
    # with PAUSED, STOPPED or COMPLETE (case-sensitive, optionally followed
    # by ":") passes with no output.

    def test_status_lines_pass_silently(self):
        # Spec 8 test 8, passing half. Every keyword, with and without the
        # colon, with a multi-line report, with leading whitespace.
        for message in (
            "PAUSED: Task 3: complete (commits a1b2c3d..d4e5f6a, review clean)",
            "STOPPED: Task 5 pushes the branch to origin. Push now / skip Task 5 / abort?",
            "COMPLETE\n\n## Summary\n3 tasks, 4 commits, 12/12 tests passing",
            "COMPLETE",
            "  \n PAUSED: Final review: dispatched (package x, abc1234..def5678)",
            "STOPPED preflight - missing ROOT",
        ):
            with self.subTest(message=message[:32]):
                proc = self.run_guard(self.payload(message))
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), "")

    def test_non_status_messages_block_with_the_reason(self):
        # Spec 8 test 8, blocking half. Fixtures chosen to break a lax
        # matcher: lowercase keyword, keyword not first, keyword as a prefix
        # of a longer word, empty reply, tag-shaped text.
        for message in (
            "Done. All tasks complete and the workspace is deleted.",
            "paused: waiting for the reviewer",
            "The status is PAUSED: Task 2",
            "COMPLETED the plan",
            "PAUSEDish",
            "",
            "<status>PAUSED</status>",
        ):
            with self.subTest(message=message[:32]):
                proc = self.run_guard(self.payload(message))
                self.assertEqual(proc.returncode, 0, proc.stderr)
                out = json.loads(proc.stdout.strip())
                self.assertEqual(out, {"decision": "block", "reason": BLOCK_REASON})

    def test_stop_hook_active_never_blocks(self):
        # Spec 8 test 9 (5.3): the forced retry's own SubagentStop passes
        # whatever the message - at most one forced retry, never a loop.
        proc = self.run_guard(
            self.payload("Still not a status line", stop_hook_active=True)
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")

    def test_malformed_payloads_exit_zero_silently(self):
        # Spec 5.3: malformed payloads exit 0 silently, as the context hook
        # does. Non-JSON, non-object, missing message, non-string message.
        for stdin_text in (
            "not json",
            json.dumps([1, 2, 3]),
            json.dumps({"hook_event_name": "SubagentStop"}),
            json.dumps({"hook_event_name": "SubagentStop", "last_assistant_message": 42}),
        ):
            with self.subTest(stdin=stdin_text[:32]):
                proc = self.run_guard(stdin_text)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), "")
                self.assertEqual(proc.stderr.strip(), "")

    def test_hooks_json_registers_guard_under_subagent_stop_with_anchored_matcher(self):
        # Spec 8 test 10, guard half (5.3): SubagentStop carries the guard
        # under the anchored scoped matcher with timeout 5, alongside the
        # unmatched context-usage hook (both run; each decides independently).
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        guarded = [
            entry for entry in hooks["SubagentStop"]
            if entry.get("matcher") == f"^{CONTROLLER_TYPE}$"
        ]
        self.assertEqual(len(guarded), 1)
        self.assertEqual(
            [h["command"] for h in guarded[0]["hooks"]],
            ['python "${CLAUDE_PLUGIN_ROOT}/hooks/sdd-controller-status.py"'],
        )
        self.assertEqual(guarded[0]["hooks"][0]["timeout"], 5)
        unmatched_commands = [
            h["command"] for entry in hooks["SubagentStop"]
            if "matcher" not in entry for h in entry["hooks"]
        ]
        self.assertTrue(any("context-usage.py" in c for c in unmatched_commands))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/hooks/test_sdd_controller_status.py -q`

Expected: 5 failed. The four subprocess tests fail because `GUARD` does not exist (`python: can't open file ... sdd-controller-status.py` -> returncode 2, `assertEqual(proc.returncode, 0)`); the registration test fails on `assertEqual(len(guarded), 1)` with `0 != 1`. Paste the failing assertions into the report.

- [ ] **Step 3: Write the guard**

Create `plugins/claude-toolkit/hooks/sdd-controller-status.py`:

```python
#!/usr/bin/env python3
"""SubagentStop status-line guard for the claude-toolkit:sdd-controller agent.

The driver (/implement-from-plan) branches on the controller's final
message, so the status line is enforced by the harness rather than
promised by the prompt (spec 5.3). Registered in hooks.json under
SubagentStop with the anchored matcher ^claude-toolkit:sdd-controller$ -
SubagentStop matchers take the agent type, plugin agents use the scoped
id, and ":" forces the regex path, hence the anchors (R:73).

Grammar (spec 6): the final message, after leading whitespace, starts with
one of PAUSED, STOPPED, COMPLETE (case-sensitive) as a whole keyword -
followed by ":", whitespace, or the end of the message. Anything else is
blocked with a reason telling the controller to re-issue its status.

Loop safety: the forced turn's own SubagentStop arrives with
stop_hook_active=true and always passes - at most one forced retry, never
a loop. A second non-status reply reaches the driver, which asks the human.

Malformed payloads (non-JSON, non-object, missing or non-string
last_assistant_message) exit 0 silently, as the context-usage hook does.
The context-usage hook runs on the same event, unmatched; each decides
independently.
"""

import json
import re
import sys

STATUS_LINE = re.compile(r"^\s*(PAUSED|STOPPED|COMPLETE)(?::|\s|$)")
BLOCK_REASON = (
    "Your final message must be a status line: PAUSED: <ledger last line> | "
    "STOPPED: <question> | COMPLETE <report>. Re-issue your status now."
)


def is_status_line(message: str) -> bool:
    return STATUS_LINE.match(message) is not None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get("stop_hook_active"):
        return 0
    message = payload.get("last_assistant_message")
    if not isinstance(message, str):
        return 0
    if is_status_line(message):
        return 0
    print(json.dumps({"decision": "block", "reason": BLOCK_REASON}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Register the guard in hooks.json**

In `plugins/claude-toolkit/hooks/hooks.json`, replace the `"SubagentStop"` array with:

```json
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "^claude-toolkit:sdd-controller$",
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/sdd-controller-status.py\"",
            "timeout": 5
          }
        ]
      }
    ],
```

and append this sentence to the `description` string, before `Also ships the raw-fetch pipeline hooks:`:

```
SubagentStop additionally runs the sdd-controller status-line guard, matched on ^claude-toolkit:sdd-controller$ (sdd-controller-status.py): a controller reply that is not PAUSED / STOPPED / COMPLETE is blocked once so /implement-from-plan always branches on a status line.
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/ -q` and `node --test "tests/hooks/*.test.mjs"`

Expected: all pass (hooks.json still parses; the node hook tests are untouched).

- [ ] **Step 6: Commit**

```bash
git add plugins/claude-toolkit/hooks/sdd-controller-status.py plugins/claude-toolkit/hooks/hooks.json tests/hooks/test_sdd_controller_status.py
git commit -m "hook: sdd-controller status-line guard on SubagentStop" -m "Blocks once (never on stop_hook_active) a controller final message that does not begin with PAUSED / STOPPED / COMPLETE, so the driver always branches on a status line. Spec 5.3 and 6; spec 8 tests 8, 9, 10 (guard half)."
```

---

### Task 5: The controller `agents/sdd-controller.md`

**Files:**
- Create: `plugins/claude-toolkit/agents/sdd-controller.md`

**Interfaces:**
- Consumes: the hook's agent-scope instruction ("...end your turn per your pause protocol...", Task 2); the guard grammar (Task 4); SDD 6.3.0's ledger lines (`Task <N>: complete (...)`, `Task <N>: fix round <R>/5 (...)`, `Ruling: ...`) and its Setup / Final Review / Finish sections.
- Produces (used by Task 6): the spawn prompt (`PLAN: <abs>` newline `ROOT: <abs>`), the resume message (`RULING: <answer>`), the status lines `PAUSED: <ledger last line>` / `STOPPED: <question and options>` / `COMPLETE` + report, and the ledger lines `Ruling (human): <question> -> <answer>` and `Final review: dispatched (package <path>, <base7>..<head7>)` / `Final review: <K> findings` / `Final review: fix wave (<base7>..<head7>)` / `Final review: clean`.

- [ ] **Step 1: Write the agent definition**

Create `plugins/claude-toolkit/agents/sdd-controller.md`:

````markdown
---
name: sdd-controller
description: Runs one implementation plan end to end with superpowers:subagent-driven-development, pausing when the context hook warns it and replying a status line (PAUSED / STOPPED / COMPLETE) that /implement-from-plan branches on. Spawned by /implement-from-plan with PLAN and ROOT; not for standalone use.
tools: Read, Write, Edit, Glob, Grep, Bash, Skill, Agent
model: inherit
---

# sdd-controller

You run one implementation plan from its current position to completion
with the `superpowers:subagent-driven-development` skill (SDD), and you
stop for exactly three reasons: the context hook told you to pause, one of
SDD's own stop cases applies, or the plan is complete. Everything SDD
already does - the ledger and resuming from it, dispatching implementers
and reviewers, model selection, fix loops, rulings, the final review,
workspace deletion - you do by invoking the skill, not by re-deriving it.
You add exactly one thing: a pause protocol, so that a fresh copy of you
can continue from the ledger when your context runs out.

You talk to nobody. Your final message is your output: the driver that
spawned you reads it and nothing else. You have no SendMessage and no
ListAgents on purpose.

## Inputs

Your spawn prompt is two lines, both absolute paths:

```
PLAN: <absolute path of the plan file under ROOT>
ROOT: <absolute path of the repository root the run executes in>
```

A resume message is one line: `RULING: <your human partner's answer>`.

## 1. Preflight

Before touching anything:

1. If `PLAN` or `ROOT` is missing from the prompt, reply
   `STOPPED: preflight - missing <PLAN|ROOT>` and do nothing else.
2. Run `git rev-parse --show-toplevel` from your working directory and
   compare it with ROOT as resolved absolute paths. If they differ, reply
   `STOPPED: preflight - repository root is <printed path> but ROOT is
   <ROOT>` and do nothing else. SDD's workspace script derives its root
   from the current directory, so a mismatch would put the ledger in the
   wrong repository.
3. Run `git rev-parse --abbrev-ref HEAD`. If it prints `main` or `master`,
   reply `STOPPED: preflight - ROOT is on <branch>; SDD never implements on
   main/master without explicit consent. Create a branch or worktree and
   respawn?` and do nothing else. The driver establishes the isolated
   workspace before spawning you; a feature branch at ROOT is what you
   expect to find. Never create a worktree yourself and never ask about
   one - that question belongs to the driver.
4. Confirm PLAN exists and lies under ROOT; otherwise
   `STOPPED: preflight - PLAN <path> not found under ROOT`.

## 2. Mandate

Invoke `superpowers:subagent-driven-development` on PLAN and run it end to
end from the ledger's current position. SDD's Setup owns the resume: a
ledger whose first line names PLAN is your progress, tasks with a
`Task <N>: complete` line are done, a task whose last line is a fix round
resumes at the next round. That ledger may have been written by an earlier
life of this controller or by a plain SDD run in a main session; both are
resumed the same way. You have no resume logic of your own, and you never
re-dispatch a task the ledger marks complete.

Where SDD's Setup says to ensure an isolated workspace: the preflight has
already confirmed ROOT is on a feature branch, which satisfies it.

## 3. Pause protocol

The context hook measures your own transcript and warns you mid-wake. A
checkpoint message that tells you to end your turn **per your pause
protocol** (the 200k, 250k or 300k checkpoint; the 100k one is advisory)
is the pause signal. On receiving it:

1. Finish the step in flight up to its next ledger write, and no further:
   - a dispatched worker returns and its result is ledgered (a task
     completion, a fix-round line, or a parked finding);
   - a fix round completes and is ledgered;
   - a final-review stage completes and is ledgered (section 5).
2. Dispatch nothing new. No next task, no next fix round, no next review.
3. End the turn with `PAUSED: <the ledger's last line>`, copied verbatim
   from the ledger.

Never pause between a dispatch and its return - the ledger would be behind
git, and the next life would re-run or lose the step. The 250k and 300k
messages change nothing but urgency: still no new dispatch, still finish
the in-flight step to its ledger write, then pause.

A fresh life resumes exactly at the ledger's next unfinished unit; the
driver spawns it with the same PLAN and ROOT.

## 4. Stop cases

SDD stops for four reasons only: an irreversible or destructive operation,
a security-sensitive action, a side effect outside the worktree that norms
say you ask about first (a merge, a push to a shared branch, a publish),
and a plan so broken that every path forward is a guess. Everything else
you rule on and ledger, as SDD instructs. When one of the four applies, end
the turn with `STOPPED: <the question, with the options as SDD framed
them>`.

On a `RULING: <answer>` message, before acting on it, append to the ledger

```
Ruling (human): <the question you asked> -> <the answer>
```

so a later life keeps the decision, then continue the run from where you
stopped. A failed preflight is also `STOPPED`; there is no FAILED status -
an environment you cannot work in is a question for your human partner.

## 5. Final-review ledgering

SDD's Final Review runs inside you as the tail of the run. Append a ledger
line as each stage completes, so a pause during the review resumes at the
stage in flight instead of re-running the whole review:

```
Final review: dispatched (package <review-package path>, <merge-base7>..<head7>)
Final review: <K> findings
Final review: fix wave (<fix-base7>..<head7>)
Final review: clean
```

`Final review: <K> findings` is written when the reviewer returns (K may
be 0, in which case the next line is `Final review: clean`). `Final
review: fix wave` is written when the single fix dispatch and its scoped
re-review have returned and residuals are adjudicated. On resume with
every task complete, continue the final review at the stage after the last
`Final review:` line, or start it if there is none.

## 6. Completion

When the final review is clean:

1. Compile the post-implementation report from the ledger, `git log`, and
   the workspace's review packages - never from recollection, because
   earlier lives are gone. Sections, each omitted when empty:
   - **Summary** - tasks completed; every commit in the range with its
     one-line description; test results (total, all passing?).
   - **Plan deviations** - tasks that diverged from the plan and why;
     assumptions in the plan that proved incorrect.
   - **Reviewer issues** - findings from task reviews and the final review,
     each with its resolution; anything left unaddressed, with the ruling.
   - **Unplanned changes** - files modified outside the plan's scope;
     dependencies added or changed beyond the plan.
   - **Known issues and risks** - anything fragile, missing coverage,
     likely follow-up.
   - **Recommendations** - follow-up tasks, areas needing more testing,
     technical debt introduced.
   - **Rulings I made** - SDD's exhaustive list: every ledger line
     containing `Ruling:` or `Ruling (human):`, in order, each with what it
     costs if wrong.
   - **Branch and range** - the branch name and `<merge-base7>..<head7>`.
2. Follow SDD's Finish: with the report compiled, delete this plan's
   workspace (`rm -rf <workspace>`); sibling directories belong to other
   plans.
3. Reply `COMPLETE` on the first line, followed by the report.

Do not invoke `superpowers:finishing-a-development-branch`: merge, PR and
push are side effects the driver runs with your human partner in the main
session.

## 7. Reply discipline

The final message of every wake is plain text whose first line begins with
exactly one of `PAUSED:`, `STOPPED:` or `COMPLETE`. A SubagentStop guard
blocks any other final message once and asks you to re-issue your status;
on that or any other hook-forced extra turn, re-issue the same status
line. Never wrap the status in tags or code fences - tag-shaped text is
rewritten by the harness before the driver sees it.

## 8. Read discipline

The Read tool refuses a single call over 25,000 tokens. Never Read a file
whole when it may exceed that (plans, research deposits, transcripts,
review packages): use `offset`/`limit`, or Grep for the lines you need.
SDD already hands workers their briefs and packages as files; keep it that
way and never paste them into a dispatch.
````

- [ ] **Step 2: Verify the frontmatter and the contract phrases**

Run:

```bash
python - <<'EOF'
from pathlib import Path
text = Path("plugins/claude-toolkit/agents/sdd-controller.md").read_text(encoding="utf-8")
head, body = text.split("---\n", 2)[1:]
fm = dict(line.split(": ", 1) for line in head.strip().splitlines())
assert fm["name"] == "sdd-controller", fm
assert fm["tools"] == "Read, Write, Edit, Glob, Grep, Bash, Skill, Agent", fm["tools"]
assert fm["model"] == "inherit", fm
assert "hooks" not in fm and "skills" not in fm, fm
assert "spawned by /implement-from-plan" in fm["description"].lower() or "Spawned by /implement-from-plan" in fm["description"]
for phrase in ("PLAN: <absolute path", "ROOT: <absolute path", "RULING: <", "per your pause\nprotocol", "PAUSED: <the ledger's last line>", "STOPPED: <the question", "Ruling (human):", "Final review: dispatched", "Final review: clean", "COMPLETE", "25,000 tokens", "finishing-a-development-branch"):
    assert phrase in body, phrase
assert "SendMessage" in body and "ListAgents" in body  # named as absent
print("sdd-controller.md: frontmatter and contract phrases OK")
EOF
```

Expected: `sdd-controller.md: frontmatter and contract phrases OK`. This is a definition check, not a behavioural test; the behaviour is verified by the post-release live spikes (acceptance section).

- [ ] **Step 3: Commit**

```bash
git add plugins/claude-toolkit/agents/sdd-controller.md
git commit -m "agent: sdd-controller - SDD plus a pause protocol" -m "Runs one plan via subagent-driven-development from the ledger's position; pauses at the next ledger write on the hook's warning (PAUSED), surfaces SDD's four stop cases (STOPPED) and ledgers the human ruling, ledgers final-review stages, and replies COMPLETE with a report compiled from the ledger and git. Spec 5.2, 5.5, 6."
```

---

### Task 6: The driver `commands/implement-from-plan.md`

**Files:**
- Modify: `plugins/claude-toolkit/commands/implement-from-plan.md` (full rewrite)

**Interfaces:**
- Consumes: the controller's spawn prompt, resume message, status grammar and ledger lines (Task 5); `superpowers:using-git-worktrees` (Step 0 detects existing isolation; a declined worktree means a feature branch in place); `superpowers:finishing-a-development-branch`; the SDD ledger path `<ROOT>/.superpowers/sdd/<plan-basename>/progress.md`.
- Produces: the run record `.claude/sdd-run.json` = `{"plan": "<abs>", "root": "<abs>"}`.

- [ ] **Step 1: Rewrite the command**

Replace the whole of `plugins/claude-toolkit/commands/implement-from-plan.md` with:

````markdown
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
   abandoned; the ledger is the resume point.
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
python -c "import json,sys; json.dump({'plan': sys.argv[1], 'root': sys.argv[2]}, open(sys.argv[3], 'w'))" "$PLAN" "$ROOT" "$INVOKE_ROOT/.claude/sdd-run.json"
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
be relayed: tell your human partner, then treat the run as paused - go to
Step 3 and pass the ruling as a third prompt line `RULING: <answer>` only
if they confirm; otherwise leave the record in place for a later resume.

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
  INVOKE_ROOT. Step 1 finds the run record and Step 3 spawns a fresh life;
  the ledger and git hold the last boundary, at worst one in-flight step is
  re-run, which SDD's review loop tolerates.
- Two PAUSED lives with the same ledger last line: Step 4's liveness check
  stops you; ask, do not respawn.
- A controller reply with no status keyword after the guard's one forced
  retry: show it and ask.
````

- [ ] **Step 2: Verify the driver's contract phrases**

Run:

```bash
python - <<'EOF'
from pathlib import Path
text = Path("plugins/claude-toolkit/commands/implement-from-plan.md").read_text(encoding="utf-8")
for phrase in (
    'subagent_type`: `claude-toolkit:sdd-controller`',
    '.claude/sdd-run.json',
    '{"plan": "<absolute plan path>", "root": "<absolute repository root>"}',
    "PLAN: <PLAN>", "ROOT: <ROOT>",
    "**An explicit argument**", "**The run record**", "**The plan pointer**",
    "superpowers:using-git-worktrees", "superpowers:finishing-a-development-branch",
    "**`PAUSED: <ledger last line>`**", "**`STOPPED: <question and options>`**", "**`COMPLETE`**",
    'RULING: <the answer>', "Never guess a status", "Never\npoll",
    'rm -f "$INVOKE_ROOT/.claude/sdd-run.json" "$INVOKE_ROOT/.claude/last-plan-doc"',
):
    assert phrase in text, phrase
assert "Step 3: Post-Implementation Report" not in text  # old wrapper gone
print("implement-from-plan.md: contract phrases OK")
EOF
```

Expected: `implement-from-plan.md: contract phrases OK`.

- [ ] **Step 3: Commit**

```bash
git add plugins/claude-toolkit/commands/implement-from-plan.md
git commit -m "command: rewrite /implement-from-plan as the controller driver" -m "Resolves the plan (argument > run record > pointer > ask), establishes ROOT via using-git-worktrees in the main session, writes .claude/sdd-run.json, spawns one unnamed claude-toolkit:sdd-controller per life, respawns on PAUSED behind a no-progress guard, relays RULING by agent id on STOPPED, and ships via finishing-a-development-branch on COMPLETE. Spec 5.4, 5.5, 6, 7."
```

---

### Task 7: Delete the or-* topology and release 2.0.0

**Files:**
- Delete: `plugins/claude-toolkit/skills/or-superpowers-at-scale/` (SKILL.md + 13 assets), `plugins/claude-toolkit/agents/or-brainstormer.md`, `or-code-quality-reviewer.md`, `or-community-researcher.md`, `or-dependency-researcher.md`, `or-final-reviewer.md`, `or-finisher.md`, `or-implementer.md`, `or-plan-writer.md`, `or-spec-reviewer.md`, `or-supervisor.md`
- Modify: `plugins/claude-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`, `plugins/claude-toolkit/skills/community-research-methodology/SKILL.md:85-86`, `plugins/claude-toolkit/skills/dependency-research-methodology/SKILL.md:60-61`

**Interfaces:**
- Consumes: `claude-toolkit:updating-plugin` (the release checklist: plugin.json version + description, both marketplace.json versions + description, README, commit, push).
- Produces: plugin 2.0.0.

- [ ] **Step 1: Delete the or-* skill and agents**

```bash
test "$(ls plugins/claude-toolkit/agents/or-*.md | wc -l)" -eq 10 && test "$(find plugins/claude-toolkit/skills/or-superpowers-at-scale -type f | wc -l)" -eq 14 && echo counts-ok
git rm -r -q plugins/claude-toolkit/skills/or-superpowers-at-scale
git rm -q plugins/claude-toolkit/agents/or-*.md
git diff --cached --name-only | wc -l
```

Expected: `counts-ok`, then `24` staged deletions (untracked `__pycache__`/`.clone` dirs are not counted). If the counts differ, stop and reconcile against the Deletion constraint before removing anything.

- [ ] **Step 2: Remove the dangling or-* mentions in the two research-methodology skills**

In `plugins/claude-toolkit/skills/community-research-methodology/SKILL.md` (lines 85-86) and `plugins/claude-toolkit/skills/dependency-research-methodology/SKILL.md` (lines 60-61), make the same two edits:

Replace

```
(A web deposit is a fetched-page file; it is distinct from the or-* *research deposit*, the path where deposit-aware teammates deliver their report.)
```

with

```
(A web deposit is a fetched-page file; it is distinct from the *research deposit*, the path where a deposit-aware research agent delivers its report.)
```

and replace

```
If you are an or-* teammate with `SendMessage`, you MAY ask your manager to arrange a courier run (send the URL plus the `path` and `helper` values from the JSON line); the manager decides.
```

with

```
If you have `SendMessage`, you MAY ask the agent that spawned you to arrange a courier run (send the URL plus the `path` and `helper` values from the JSON line); it decides.
```

- [ ] **Step 3: Commit the deletion**

```bash
git add -A plugins/claude-toolkit/skills
git commit -m "remove: or-superpowers-at-scale skill and the ten or-* agents" -m "The orchestrator existed for two premises that no longer hold (depth-1 agent nesting; no durable SDD ledger). Replaced by sdd-controller + the /implement-from-plan driver. Spec 5.6."
```

(The remaining or-* mentions are in `README.md` and `plugin.json`, edited in Steps 4-5 and verified by the grep in Step 6; `docs/` keeps its historical records.)

- [ ] **Step 4: Bump versions and descriptions**

`plugins/claude-toolkit/.claude-plugin/plugin.json`:

```json
{
  "name": "claude-toolkit",
  "version": "2.0.0",
  "description": "Architecture and test review agents, research agents, a plan-to-ship driver (/implement-from-plan spawning the sdd-controller agent: subagent-driven development across context windows, paused by the context hook and resumed from the SDD ledger), development workflow commands, MCP/skill design guides, context-window checkpoint hooks, and the raw-fetch web pipeline (WebFetch deny hook, fetch-page CLI, page-courier agent)",
  "author": { "name": "marti" }
}
```

`.claude-plugin/marketplace.json`:

```json
{
  "name": "claude-toolkit",
  "owner": { "name": "marti" },
  "metadata": {
    "description": "Agents, commands, skills, and hooks for code review, research, and development workflows, plus the raw-fetch web pipeline",
    "version": "2.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "claude-toolkit",
      "source": "./plugins/claude-toolkit",
      "description": "Architecture and test review agents, research agents, a plan-to-ship driver (/implement-from-plan spawning the sdd-controller agent: subagent-driven development across context windows, paused by the context hook and resumed from the SDD ledger), development workflow commands, MCP/skill design guides, context-window checkpoint hooks, and the raw-fetch web pipeline (WebFetch deny hook, fetch-page CLI, page-courier agent)",
      "version": "2.0.0"
    }
  ]
}
```

- [ ] **Step 5: Update the README**

In `README.md`:

1. Under `### Agents`, delete the whole block from `**or-superpowers-at-scale orchestrator agents** (internal ...` through the `or-dependency-researcher`, `or-community-researcher` line (README lines 15-20), and append after the `page-courier` bullet:

```
- **sdd-controller** — Internal: spawned by `/implement-from-plan` with `PLAN` and `ROOT`; runs one plan end to end via subagent-driven-development, pauses on the context hook's warning with the SDD ledger at a boundary, and replies a status line (`PAUSED` / `STOPPED` / `COMPLETE`). Not for standalone use.
```

2. Under `### Commands`, replace the `/implement-from-plan` bullet with:

```
- **/implement-from-plan** — Drive a tracked plan to completion across context windows: spawns an `sdd-controller` per controller life, respawns from the SDD ledger on `PAUSED`, relays your ruling on `STOPPED`, and ships in the main session on `COMPLETE` (depends on superpowers plugin)
```

3. Under `### Skills`, delete the `**or-superpowers-at-scale**` bullet.

4. Under `### Hooks`, replace the `**context-usage**` bullet with:

```
- **context-usage** — Context-window checkpoint hook (`UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `SubagentStop`): measures the context of whoever the event is talking to — the agent's own transcript whenever the payload carries an `agent_id`, else the main session's — and announces once per measurement identity, per channel, when usage crosses 100k / 200k / 250k / 300k. Each warning reports the crossing and its implication for reasoning quality; the ≥200k warnings add the baseline instruction — main scope: wrap up and use `/handover`; agent scope: finish the step, record your state, and end your turn per your pause protocol — escalating to stop-immediately at 250k/300k, with 300k noting that work quality may have been compromised. The informational events inject the warning as `additionalContext` mid-turn (the two tool events share one announcement); the turn-end events deliver actionable crossings as `decision:block` only when no informational channel already announced that threshold for the same identity. Per-identity state lives under `~/.claude/hooks/state/`.
- **sdd-controller-status** — `SubagentStop` guard matched on `^claude-toolkit:sdd-controller$`: blocks (once) a controller reply that is not a status line, so `/implement-from-plan` always branches on `PAUSED` / `STOPPED` / `COMPLETE`
```

5. Under `## Dependencies`, replace the paragraph with:

```
The `/design`, `/plan-from-design`, and `/implement-from-plan` commands — and the `sdd-controller` agent the last one drives — depend on the **superpowers** plugin. Install it separately if you want to use them.
```

6. Under `### Running the tests`, replace `- python hook tests: \`pytest tests/\`` with:

```
- python hook tests: `python -m pytest tests/ -q` (context-usage and the sdd-controller status guard)
```

- [ ] **Step 6: Verify the release**

```bash
grep -n '"version"' plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
grep -rn -E "or-superpowers-at-scale|or-(brainstormer|supervisor|implementer|finisher)" README.md plugins .claude-plugin || echo no-or-refs
python -c "import json; json.load(open('plugins/claude-toolkit/.claude-plugin/plugin.json')); json.load(open('.claude-plugin/marketplace.json')); json.load(open('plugins/claude-toolkit/hooks/hooks.json')); print('json-ok')"
ls plugins/claude-toolkit/agents plugins/claude-toolkit/skills
python -m pytest tests/ -q && node --test "tests/hooks/*.test.mjs" && (cd plugins/claude-toolkit/fetch-page && npm test)
```

Expected: three `"version": "2.0.0"` lines and nothing else from the first grep; `no-or-refs`; `json-ok`; the agents listing shows `sdd-controller.md` and no `or-*`; the skills listing has no `or-superpowers-at-scale`; every suite green.

- [ ] **Step 7: Commit the release**

```bash
git add plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json README.md
git commit -m "release: 2.0.0 - sdd-controller + driver replace the or-superpowers-at-scale orchestrator" -m "Breaking: removes one skill and ten agents. Adds the sdd-controller agent, the sdd-controller-status SubagentStop guard, agent-scoped context measurement on every hook event with a scope-aware instruction, and the rewritten /implement-from-plan driver. Spec 5.6."
```

Do not push: the push happens in the ship step (finishing-a-development-branch), which is also where the acceptance checklist below begins.

---

## Self-review (writing-plans checklist, run 2026-09-11)

**Spec coverage.** 5.1 rules 1-4 -> Task 1; 5.1 events -> Task 1 (PostToolBatch deliberately absent, asserted); 5.1 wording -> Task 2; 5.1 addendum -> Task 3; 5.1 "Unchanged" -> the existing suite stays green in every task; 5.2 items 1-8 -> Task 5 sections 1-8; 5.3 -> Task 4; 5.4 -> Task 6 (resolution order, run record, worktree in main, spawn, loop, end); 5.5 report + final-review ledgering -> Task 5 sections 5-6, ship -> Task 6 Step 5; 5.6 deletion + versions + descriptions + README + hooks.json description + docstring -> Tasks 1, 4, 7; 6 status grammar -> Tasks 4, 5, 6; 7 failure handling -> Tasks 3 (backstop), 4 (guard retry), 6 (liveness check, dead session); 8 tests 1-10 -> Tasks 1-4 (test 10 split across the two files by promise); 8 live spikes -> acceptance section below. 9 out of scope: nothing here touches named agents, PostToolBatch, budgets, or the stale worktrees.

**Placeholder scan.** No TBD/TODO; every code step carries its code; every test names its promise; every "verify it fails" step names the expected failing assertion.

**Type consistency.** `Target(transcript: Path, state_id: str, scope: str)` with `include_sidechain` property is introduced in Task 1 and read by name in Tasks 2-3 (`target.scope`, `target.state_id`, `target.transcript`, `target.include_sidechain`). `highest_crossing` returns `int | None` from Task 2 on and Task 3's insertion uses `threshold`. `checkpoint_message(threshold, scope, turn_end)` signature is identical in its definition and its call. `BLOCK_REASON` is the same string in the guard, its test, and the spec. The controller's status lines, `RULING:` message and ledger lines are quoted identically in Tasks 5 and 6.

---

## Acceptance: live spikes (post-release, run by Martin; not an SDD task)

The spikes need the installed plugin at 2.0.0 and a restarted session (spec 5.6 "After release"), so they run after the ship step. Findings become a 2.0.x patch via `claude-toolkit:updating-plugin`. Each spike names the spec claim it verifies; record PASS/FAIL with the evidence path beside it.

### A. Install and restart

1. Ship: `superpowers:finishing-a-development-branch` merges `sdd-at-scale-lean-redesign` into `master` and pushes.
2. `claude plugin marketplace update claude-toolkit && claude plugin update claude-toolkit`, then restart Claude Code.
3. Verify: `ls ~/.claude/plugins/cache/claude-toolkit/claude-toolkit/` lists `2.0.0`, and `cat ~/.claude/plugins/cache/claude-toolkit/claude-toolkit/2.0.0/hooks/hooks.json | grep -c sdd-controller-status` prints `1`.

### B. Throwaway repository and plan

```bash
SPIKE=/c/Users/marti/AppData/Local/Temp/sdd-spike
rm -rf "$SPIKE" && mkdir -p "$SPIKE" && cd "$SPIKE"
git init -q --bare origin.git
git init -q -b main repo && cd repo && git remote add origin ../origin.git
mkdir -p lib test docs/plans
cat > package.json <<'EOF'
{ "name": "sdd-spike", "private": true, "type": "module", "scripts": { "test": "node --test \"test/*.test.js\"" } }
EOF
cat > docs/plans/spike-plan.md <<'EOF'
# Spike Plan (throwaway)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** A tiny ESM library with three distinct modules, a README, and a publish step - enough plan to exercise pause, resume, stop and completion.

**Tech Stack:** Node 24, `node:test`, no dependencies.

## Global Constraints
- ESM only (`"type": "module"`). Tests run with `npm test`.
- Commit after every task.

### Task 1: add
**Files:** Create `lib/add.js`, `test/add.test.js`.
- [ ] Write `test/add.test.js`: `import { test } from 'node:test'; import assert from 'node:assert/strict'; import { add } from '../lib/add.js'; test('adds', () => assert.equal(add(2, 3), 5));`
- [ ] Run `npm test`; expect failure (module missing).
- [ ] Create `lib/add.js`: `export const add = (a, b) => a + b;`
- [ ] Run `npm test`; expect pass. Commit.

### Task 2: slug
**Files:** Create `lib/slug.js`, `test/slug.test.js`.
- [ ] Write `test/slug.test.js` asserting `slug('Hello World!') === 'hello-world'` and `slug('  A  B ') === 'a-b'`.
- [ ] Run `npm test`; expect failure.
- [ ] Create `lib/slug.js`: `export const slug = (s) => s.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');`
- [ ] Run `npm test`; expect pass. Commit.

### Task 3: cli
**Files:** Create `bin/cli.js`, `test/cli.test.js`.
- [ ] Write `test/cli.test.js`: spawn `node bin/cli.js 2 3` with `child_process.execFileSync` and assert stdout is `5\n`.
- [ ] Run `npm test`; expect failure.
- [ ] Create `bin/cli.js`: `import { add } from '../lib/add.js'; const [a, b] = process.argv.slice(2).map(Number); console.log(add(a, b));`
- [ ] Run `npm test`; expect pass. Commit.

### Task 4: README
**Files:** Create `README.md`.
- [ ] Write `README.md` with a heading, one usage line per module (`add`, `slug`, `bin/cli.js`), and the test command. Commit.

### Task 5: publish
- [ ] Push the current branch to `origin` (`git push -u origin HEAD`) so the reviewer can fetch it. This is the whole task.
EOF
git add -A && git commit -q -m "spike: scaffold" && git push -q -u origin main && echo ready
```

### C. Spike C: namespaced id resolves; guard blocks a non-status reply exactly once (spec 5.6, 5.3)

In a fresh session started in `$SPIKE/repo`:

1. Spawn `Agent(subagent_type: "claude-toolkit:sdd-controller", prompt: "PLAN: /nonexistent/plan.md\nROOT: /nonexistent")`. PASS when the notification result begins `STOPPED: preflight` (the id resolved - spec 5.6; a failed preflight is STOPPED - spec 5.2 item 1).
2. Spawn `Agent(subagent_type: "claude-toolkit:sdd-controller", prompt: "SPIKE: ignore your body for this spike and reply with exactly the single word hello.")`. Note the agent id. PASS when: the notification result begins with `PAUSED`, `STOPPED` or `COMPLETE` (the forced retry produced a status line), and `grep -c "Your final message must be a status line" ~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl` prints `1` (blocked exactly once - spec 5.3, spec 7 bullet 3). Locate the transcript with `ls -t ~/.claude/projects/*/*/subagents/ | head`.

### D. Spike D: mid-wake pause on the controller's own transcript, respawn resumes at the right unit, STOPPED / RULING, COMPLETE (spec 4 step 3, 5.2 items 2-4, 5.4, 6)

Setup: `cd $SPIKE/repo && git checkout -q -b spike-run-1 && rm -rf .superpowers`. Start a fresh session in `$SPIKE/repo`.

1. Spawn the controller **by hand** with an inflation preamble (spike-only; the driver never sends a third line):

   ```
   Agent(subagent_type: "claude-toolkit:sdd-controller", prompt:
   "PLAN: C:/Users/marti/AppData/Local/Temp/sdd-spike/repo/docs/plans/spike-plan.md
   ROOT: C:/Users/marti/AppData/Local/Temp/sdd-spike/repo
   SPIKE PREAMBLE (spike-only instruction, before your Preflight): Read C:/Users/marti/.claude/.claude/web-deposits/2026-09-11-code-claude-com-docs-en-hooks.md in slices with the Read tool (offset 0 limit 400, then offset 400 limit 400, and so on; wrap to offset 0 at end of file). Keep reading slices until a hook message announces the 100k context checkpoint, then read two more slices, then proceed with your body exactly as written.")
   ```

   The preamble lifts the controller to roughly 150k before SDD starts, so the 200k crossing lands mid-plan (spec fact 10: ~140k of working room per life).

2. PASS conditions on the first notification (spec 4 step 3, 5.2 item 3):
   - the result begins `PAUSED: ` and its remainder equals `tail -n 1 .superpowers/sdd/spike-plan/progress.md`;
   - that line is a boundary: `Task <N>: complete (...)`, a `Task <N>: fix round ...` line, or a `Final review: ...` line - never a dispatch in flight;
   - the controller's transcript (`agent-<id>.jsonl`) contains the mid-wake text `per your pause protocol` **before** its final message, attributed to a `PostToolUse` or `PostToolUseFailure` hook (not only a SubagentStop block).
3. Run `/implement-from-plan C:/Users/marti/AppData/Local/Temp/sdd-spike/repo/docs/plans/spike-plan.md`. There is no run record and no pointer, so the driver invokes `using-git-worktrees`; decline the worktree (work in place on `spike-run-1`). PASS when `.claude/sdd-run.json` appears with the two absolute paths and a controller life 2 is spawned (spec 5.4 start).
4. PASS on resume (spec 5.2 item 2): after life 2 reports, `grep -c "^Task 1: complete" .superpowers/sdd/spike-plan/progress.md` prints `1` for every task completed in life 1 (no re-dispatch), and `git log --oneline` shows each task's commits once.
5. PASS on the stop case (spec 5.2 item 4, 5.4 STOPPED): a notification begins `STOPPED: ` and quotes Task 5's push; the driver puts it to you verbatim; answer "push it"; the driver sends `RULING: push it` to the same agent id; the next notification comes from that id; the ledger contains a line beginning `Ruling (human): ` naming the push; `git -C ../origin.git branch` lists `spike-run-1`.
6. PASS on completion (spec 5.5, 5.4 COMPLETE, 6): the last notification begins `COMPLETE` and the report has Summary, Rulings I made, and Branch and range; `.superpowers/sdd/spike-plan/` no longer exists; the driver runs `finishing-a-development-branch` (choose "keep the branch, do nothing"); afterwards `.claude/sdd-run.json` is gone.

### E. Spike E: a plain-SDD ledger is resumed by the controller with no pointer present (spec 5.4 resolution order)

Setup: `cd $SPIKE/repo && git checkout -q main && git branch -q -D spike-run-1; git checkout -q -b spike-run-2 && rm -rf .superpowers .claude/sdd-run.json`. Start a fresh session in `$SPIKE/repo`.

1. Say: "Use superpowers:subagent-driven-development on docs/plans/spike-plan.md. Execute Task 1 only, then stop and report." PASS when `.superpowers/sdd/spike-plan/progress.md` exists, its first line names the plan, and it contains `Task 1: complete`.
2. `/clear`, then `/implement-from-plan C:/Users/marti/AppData/Local/Temp/sdd-spike/repo/docs/plans/spike-plan.md` (no pointer, no record; decline the worktree again).
3. PASS when life 1 of the controller dispatches Task 2 first (`ls .superpowers/sdd/spike-plan/` shows a Task-2 brief and no new Task-1 brief), `grep -c "^Task 1: complete"` stays `1`, and the run proceeds to the STOPPED / RULING / COMPLETE sequence as in Spike D.

### G. Spike G: a worktree run resumes after session death (spec 7, 5.4 Step 1 item 2)

Setup: as Spike D, but accept the worktree when the driver offers it in Step 2. After life 1 pauses or stops, end the session and start a fresh one in `$SPIKE/repo` (the launch directory, not the worktree). Run `/implement-from-plan` with no argument.

PASS when the driver finds the run record, re-enters the worktree (`git rev-parse --show-toplevel` in the session equals ROOT), and life 2 resumes from the ledger - never `STOPPED: preflight - repository root is ...`.

### F. Wrap-up

- Record PASS/FAIL per spike with the evidence paths in the handover memory.
- Failures: brainstorm the fix, patch, release 2.0.x via `claude-toolkit:updating-plugin`, update, restart, re-run the failed spike.
- `rm -rf /c/Users/marti/AppData/Local/Temp/sdd-spike`.
