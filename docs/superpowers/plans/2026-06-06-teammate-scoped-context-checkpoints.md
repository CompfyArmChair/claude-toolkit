# Teammate-Scoped Context Checkpoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `SubagentStop` checkpoint crossings measure the agent's **own** transcript under a **per-agent** state identity — delivering supervisor/phase-agent self-detection and killing the spurious end-of-run blocks on one-shot subagents — shipped as claude-toolkit **1.5.2**.

**Architecture:** One new pure function in `plugins/claude-toolkit/hooks/context-usage.py` — `measurement_target(payload) -> (transcript_path, state_id, include_sidechain) | None` — becomes the single decision point for whose context is measured, under which state identity, with which entry filter. `main()` consumes the tuple; everything downstream (checkpoint tables, once-per-threshold, reset-on-compaction, `stop_hook_active` guard, save-only-on-crossing) is untouched and becomes per-agent purely via the state identity. The transcript reader gains an `include_sidechain` parameter because agent transcripts are 100% `isSidechain: true`.

**Tech Stack:** Python 3 stdlib only (`json`, `re`, `sys`, `pathlib`); stdlib `unittest` exercising the real stdin→stdout hook contract via `subprocess`; `claude plugin validate` for release checks.

**Spec:** `docs/superpowers/specs/2026-06-06-teammate-scoped-context-checkpoints-design.md` (approved 2026-06-06). Read it before starting any task.

**Preconditions (already done — verify, don't redo):**
- You are on branch `teammate-scoped-checkpoints` (off `master` = `26717c5`, plugin 1.5.1). Verify: `git branch --show-current`.
- The Spike-8 RESULT edits (`fbeb7af`) and the design spec (`fee7212`) are already committed on this branch.

**Repo-wide rules for every task:**
- NEVER `git add -A` or `git add .` — the repo root contains stray untracked `breakout-*.png` files that must not be committed. Stage explicit paths only.
- Test suite invocation (from repo root, Windows): `python tests\hooks\test_context_usage.py -v`
- All work happens in the main checkout on the existing branch — no new worktree is required by this plan (follow your executor's standard isolation flow if it mandates one).

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `plugins/claude-toolkit/hooks/context-usage.py` | The checkpoint hook | New `measurement_target()` seam; `include_sidechain` parameter on the transcript reader; `state_path`/`load_state`/`save_state` parameter renamed `session_id` → `state_id`; `main()` rewired; docstring scoping section + accepted residual (Task 2) |
| `tests/hooks/test_context_usage.py` | Behavioral tests (currently 15) | 1 test rewritten (it encodes the old parent-fallback bug) + 10 new tests → 25 total |
| `plugins/claude-toolkit/hooks/hooks.json` | Hook registration | Description string only — **no registration changes** |
| `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` | Behavioral spike suite | Author **Spike 9** (executed later at cutover, NOT in this plan); cutover checklist item 6; SUITE STATUS amendment |
| `plugins/claude-toolkit/.claude-plugin/plugin.json` | Plugin manifest | Version 1.5.1 → **1.5.2** |
| `.claude-plugin/marketplace.json` | Marketplace manifest | Version 1.5.1 → **1.5.2** (two fields) |
| or-* agent/skill bodies | Orchestration suite | **Expected zero changes** — Task 3 greps and confirms |

---

### Task 1: Teammate-scoped measurement — tests + implementation (the core)

The entire behavioral change, TDD'd in one red→green cycle. Eleven test bodies are written first (one of them replaces an existing test that asserts the buggy behavior); 9 go red, 2 are deliberate regression pins that stay green before AND after (they exist to catch an implementation that breaks the main-transcript sidechain filter or the loop guard).

**Files:**
- Modify: `tests/hooks/test_context_usage.py`
- Modify: `plugins/claude-toolkit/hooks/context-usage.py`

- [ ] **Step 1: Update the state-file cleanup helper to catch agent-scoped files**

Agent-scoped tests create sibling state files named `context-usage-<session_id>--<agent_id>.json`. In `tests/hooks/test_context_usage.py`, replace the `_remove_state` method (currently lines 31–34):

```python
    def _remove_state(self):
        state_file = STATE_DIR / f"context-usage-{self.session_id}.json"
        if state_file.exists():
            state_file.unlink()
```

with:

```python
    def _remove_state(self):
        # Glob: agent-scoped tests create context-usage-<session>--<agent>.json
        # siblings alongside the session file. session_id is a per-test UUID,
        # so the glob can only match this test's files.
        for state_file in STATE_DIR.glob(f"context-usage-{self.session_id}*.json"):
            state_file.unlink()
```

- [ ] **Step 2: Add the agent-transcript helper**

Immediately after the `_transcript` method (after current line 50), add:

```python
    def _agent_transcript(self, tokens, agent_id):
        """A teammate/one-shot agent transcript: every entry isSidechain
        (the verified on-disk shape of <session>/subagents/agent-<id>.jsonl)."""
        entry = {
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
        path = self.tmp_dir / f"agent-{agent_id}.jsonl"
        path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return path
```

Note: `_transcript` writes `transcript.jsonl` and `_agent_transcript` writes `agent-<id>.jsonl` — distinct files in the same tmp dir, so a payload can carry both a parent and an agent transcript without clobbering.

- [ ] **Step 3: Rewrite the one existing test that encodes the bug**

`test_subagent_stop_blocks_at_200k` (currently lines 102–105) sends a SubagentStop payload carrying only the parent's `transcript_path` and expects a block — that is exactly the 1.5.1 parent-fallback defect. Replace:

```python
    def test_subagent_stop_blocks_at_200k(self):
        out = json.loads(self.run_hook("SubagentStop", 210_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
```

with (design test 1 — the agent transcript is measured, not the parent's):

```python
    def test_subagent_stop_measures_agent_transcript_not_parents(self):
        # The agent transcript (210k, every entry isSidechain) is measured;
        # the parent transcript (50k) is not. 1.5.1 had this inverted.
        agent_t = self._agent_transcript(210_000, agent_id="aaa111")
        out = json.loads(self.run_hook(
            "SubagentStop", 50_000,
            agent_id="aaa111", agent_transcript_path=str(agent_t),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("[210,000 tokens used]", out["reason"])
```

(`run_hook`'s `**extra` kwargs land in the payload, and its `tokens` argument builds the parent `transcript_path` — so this payload carries BOTH transcripts, like the real runtime's.)

- [ ] **Step 4: Add the new SubagentStop test section**

Insert a new section after `test_reset_rearms_turn_end_after_compact` (after current line 136), before the `# --- informational path ...` comment:

```python
    # --- SubagentStop: teammate-scoped measurement (Spike 8 facet 3) ---
    # The agent's OWN transcript is measured (sidechain filter lifted - agent
    # transcripts are wholly isSidechain:true) under a per-agent state
    # identity <session_id>--<agent_id>. Never fall back to the parent's
    # transcript_path: mis-scoped measurement IS the 1.5.1 bug.

    def test_subagent_transcript_path_alias_accepted(self):
        # Docs name the field subagent_transcript_path; the installed binary
        # says agent_transcript_path. Either must work (naming drift is real).
        agent_t = self._agent_transcript(210_000, agent_id="aaa111")
        out = json.loads(self.run_hook(
            "SubagentStop", 50_000,
            agent_id="aaa111", subagent_transcript_path=str(agent_t),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

    def test_subagent_stop_without_agent_transcript_skips_with_breadcrumb(self):
        # No agent-transcript field (future payload rename): skip + stderr
        # breadcrumb, exit 0, no output, parent state untouched. The parent
        # transcript is past 200k, so a parent fallback would block here.
        proc = self.run_hook_proc(
            self._payload("SubagentStop", self._transcript(210_000))
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("agent_transcript_path", proc.stderr)
        parent_state = STATE_DIR / f"context-usage-{self.session_id}.json"
        self.assertFalse(parent_state.exists())

    def test_agent_crossing_writes_only_agent_scoped_state(self):
        # Spike-8 collision regression: the teammate's crossing must land in
        # the agent's own state file, leaving the manager's pools untouched.
        agent_t = self._agent_transcript(210_000, agent_id="aaa111")
        self.run_hook(
            "SubagentStop", 50_000,
            agent_id="aaa111", agent_transcript_path=str(agent_t),
        )
        parent_state = STATE_DIR / f"context-usage-{self.session_id}.json"
        agent_state = (
            STATE_DIR / f"context-usage-{self.session_id}--aaa111.json"
        )
        self.assertFalse(parent_state.exists())
        self.assertTrue(agent_state.exists())
        # The manager's own subsequent crossing still announces.
        out = json.loads(self.run_hook("Stop", 210_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

    def test_two_agents_cross_independently(self):
        # 1.5.1 pooled all agents in the parent's subagent_stop key: the
        # second agent's own 200k crossing would have been suppressed.
        a = self._agent_transcript(210_000, agent_id="aaa111")
        out_a = json.loads(self.run_hook(
            "SubagentStop", 50_000,
            agent_id="aaa111", agent_transcript_path=str(a),
        ))
        self.assertEqual(out_a["decision"], "block")
        b = self._agent_transcript(205_000, agent_id="bbb222")
        out_b = json.loads(self.run_hook(
            "SubagentStop", 50_000,
            agent_id="bbb222", agent_transcript_path=str(b),
        ))
        self.assertEqual(out_b["decision"], "block")
        self.assertIn("200k", out_b["reason"])

    def test_agent_id_falls_back_to_transcript_stem(self):
        # No agent_id in the payload: the transcript filename stem keys the
        # state, so per-agent pooling survives the field's absence.
        agent_t = self._agent_transcript(210_000, agent_id="ccc333")
        out = json.loads(self.run_hook(
            "SubagentStop", 50_000,
            agent_transcript_path=str(agent_t),
        ))
        self.assertEqual(out["decision"], "block")
        stem_state = STATE_DIR / (
            f"context-usage-{self.session_id}--agent-ccc333.json"
        )
        self.assertTrue(stem_state.exists())

    def test_stop_hook_active_guard_on_subagent_stop(self):
        # Regression pin (green before AND after): the forced handover turn's
        # own SubagentStop must not re-block.
        agent_t = self._agent_transcript(210_000, agent_id="aaa111")
        self.assertEqual(
            self.run_hook(
                "SubagentStop", 50_000,
                agent_id="aaa111", agent_transcript_path=str(agent_t),
                stop_hook_active=True,
            ),
            "",
        )

    def test_reset_rearms_agent_pool_after_agent_compaction(self):
        # A compaction-scale drop inside the agent's OWN state file resets
        # and re-arms that agent's pool.
        def fire(tokens):
            agent_t = self._agent_transcript(tokens, agent_id="aaa111")
            return self.run_hook(
                "SubagentStop", 50_000,
                agent_id="aaa111", agent_transcript_path=str(agent_t),
            )

        out = json.loads(fire(310_000))             # announce 300k
        self.assertIn("300k", out["reason"])
        self.assertEqual(fire(120_000), "")         # <50% -> reset, silent
        out = json.loads(fire(210_000))             # re-armed
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

    def test_missing_agent_transcript_file_skips_silently(self):
        # Dead agent path + parent past 200k: still no parent fallback.
        self.assertEqual(
            self.run_hook(
                "SubagentStop", 210_000,
                agent_id="aaa111",
                agent_transcript_path=str(self.tmp_dir / "agent-gone.jsonl"),
            ),
            "",
        )

    def test_low_agent_usage_stays_silent_despite_high_parent_usage(self):
        # One-shot subagent completing on a >=200k session: 1.5.1 measured
        # the parent and emitted a spurious end-of-run block. Agent-scoped
        # measurement is silent.
        agent_t = self._agent_transcript(50_000, agent_id="aaa111")
        self.assertEqual(
            self.run_hook(
                "SubagentStop", 210_000,
                agent_id="aaa111", agent_transcript_path=str(agent_t),
            ),
            "",
        )
```

- [ ] **Step 5: Add the main-transcript sidechain regression pin**

In the malformed-input section style (custom transcript lines), add after `test_tool_event_announces_once` (after current line 150), at the end of the `# --- informational path ---` section:

```python
    def test_main_transcript_still_excludes_sidechain_entries(self):
        # Regression pin (green before AND after): lifting the sidechain
        # filter applies ONLY to agent transcripts. A sidechain entry in a
        # MAIN transcript stays invisible (historical inline-sidechain
        # format). Order matters: the sidechain entry is LAST, so an
        # unfiltered read would see 500k and block.
        transcript = self._transcript_lines(
            self._usage_entry({
                "input_tokens": 150_000,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            }),
            json.dumps({
                "type": "assistant",
                "isSidechain": True,
                "message": {"usage": {"input_tokens": 500_000}},
            }),
        )
        proc = self.run_hook_proc(self._payload("Stop", transcript))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
```

- [ ] **Step 6: Run the suite — verify exactly the expected reds**

Run: `python tests\hooks\test_context_usage.py -v`

Expected: **25 tests total — 9 failures/errors, 16 passes.**

Failing (against the current 1.5.1 hook, which measures the parent transcript and pools state per session):
- `test_subagent_stop_measures_agent_transcript_not_parents` — ERROR (`json.loads("")`: parent is 50k → hook silent)
- `test_subagent_transcript_path_alias_accepted` — ERROR (same)
- `test_subagent_stop_without_agent_transcript_skips_with_breadcrumb` — FAIL (old code blocks on the parent's 210k; expects empty + breadcrumb)
- `test_agent_crossing_writes_only_agent_scoped_state` — FAIL (no agent-scoped state file exists)
- `test_two_agents_cross_independently` — ERROR (`json.loads("")`)
- `test_agent_id_falls_back_to_transcript_stem` — ERROR (`json.loads("")`)
- `test_reset_rearms_agent_pool_after_agent_compaction` — ERROR (`json.loads("")`)
- `test_missing_agent_transcript_file_skips_silently` — FAIL (old code blocks on the parent's 210k)
- `test_low_agent_usage_stays_silent_despite_high_parent_usage` — FAIL (old code blocks on the parent's 210k)

Passing: the 14 untouched existing tests + the 2 regression pins (`test_stop_hook_active_guard_on_subagent_stop`, `test_main_transcript_still_excludes_sidechain_entries`).

If the red set differs from this list, STOP and investigate before implementing.

- [ ] **Step 7: Implement `measurement_target()` + wiring in `context-usage.py`**

Four edits to `plugins/claude-toolkit/hooks/context-usage.py`:

**(a)** Rename the state functions' parameter (`session_id` → `state_id`) — the identity is no longer always a session id. Replace the three functions (currently lines 174–203):

```python
def state_path(state_id: str) -> Path:
    safe = SAFE_ID.sub("_", state_id)[:128] or "default"
    return STATE_DIR / f"context-usage-{safe}.json"


def load_state(state_id: str) -> dict:
    try:
        data = json.loads(state_path(state_id).read_text(encoding="utf-8"))
    except Exception:
        return {k: 0 for k in STATE_KEYS}
    if not isinstance(data, dict):
        warn("malformed state file (not a JSON object) - using fresh state")
        return {k: 0 for k in STATE_KEYS}
    # Migrate legacy single-event state.
    if "last_announced" in data and STATE_KEY_PROMPT not in data:
        data[STATE_KEY_PROMPT] = data["last_announced"]
    for k in STATE_KEYS:
        data.setdefault(k, 0)
        v = data.get(k)
        data[k] = int(v) if isinstance(v, (int, float)) else 0
    return data


def save_state(state_id: str, state: dict) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        out = {k: int(state.get(k, 0)) for k in STATE_KEYS}
        state_path(state_id).write_text(json.dumps(out), encoding="utf-8")
    except Exception:
        pass
```

(Only the parameter name changes; bodies are otherwise identical to current.)

**(b)** Insert the new resolution seam between `emit_for()` and `latest_main_thread_usage()` (after current line 212):

```python
def measurement_target(payload: dict) -> tuple[str, str, bool] | None:
    """Resolve whose context this event measures: (transcript path, state
    identity, include_sidechain).

    Main-loop events (UserPromptSubmit/PostToolUse/Stop) measure the
    session's main transcript under the session_id, excluding sidechain
    entries (guards against the historical inline-sidechain format).

    SubagentStop measures the AGENT's own transcript under a per-agent
    identity (Spike 8 facet 3: the payload's transcript_path is the
    PARENT's, and the parent session_id would pool every agent's
    once-per-threshold state together). Agent transcripts are entirely
    isSidechain:true, so sidechain entries count there. The installed
    binary names the field agent_transcript_path; the docs say
    subagent_transcript_path - accept both, binary's name first.

    Returns None when no measurable transcript is named. A SubagentStop
    payload without an agent-transcript field is skipped with a stderr
    breadcrumb - NEVER measured against the parent's transcript_path,
    because mis-scoped measurement is the very bug this resolution fixes.
    """
    session_id = payload.get("session_id") or "default"
    event_name = payload.get("hook_event_name") or EVENT_PROMPT
    if event_name != EVENT_SUBAGENT_STOP:
        transcript_path = payload.get("transcript_path")
        if not transcript_path:
            return None
        return transcript_path, session_id, False
    transcript_path = payload.get("agent_transcript_path") or payload.get(
        "subagent_transcript_path"
    )
    if not transcript_path:
        warn(
            "SubagentStop payload missing agent_transcript_path/"
            "subagent_transcript_path - skipping (cannot measure the "
            "agent's own context)"
        )
        return None
    agent_id = payload.get("agent_id") or Path(transcript_path).stem
    return transcript_path, f"{session_id}--{agent_id}", True
```

**(c)** Give the transcript reader the `include_sidechain` parameter. Replace `latest_main_thread_usage` (currently lines 215–244):

```python
def latest_main_thread_usage(
    transcript: Path, include_sidechain: bool = False
) -> dict | None:
    """Latest assistant usage dict in the transcript. Sidechain entries are
    skipped unless include_sidechain (agent transcripts are wholly
    sidechain-flagged, so the filter would blind the read there)."""
    latest = None
    malformed = 0
    try:
        with transcript.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if not isinstance(entry, dict):
                    malformed += 1
                    continue
                if entry.get("type") != "assistant":
                    continue
                if not include_sidechain and entry.get("isSidechain"):
                    continue
                msg = entry.get("message")
                if not isinstance(msg, dict):
                    if msg is not None:  # absent message is normal shape
                        malformed += 1
                    continue
                usage = msg.get("usage")
                if isinstance(usage, dict):
                    latest = usage
    except Exception:
        return None
    if malformed:
        warn(f"skipped {malformed} malformed transcript line(s)")
    return latest
```

(Only the signature, the new docstring, and the `if not include_sidechain and entry.get("isSidechain"):` line change.)

**(d)** Rewire `main()` to consume the tuple. Replace the whole function (currently lines 259–316):

```python
def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        warn("malformed stdin payload (not a JSON object) - ignoring event")
        return 0

    event_name = payload.get("hook_event_name") or EVENT_PROMPT
    turn_end = event_name in TURN_END_EVENTS

    # Loop guard: a blocked turn-end forced one extra turn; that turn's own
    # Stop/SubagentStop arrives with stop_hook_active=true. Never block it
    # again.
    if turn_end and payload.get("stop_hook_active"):
        return 0

    target = measurement_target(payload)
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

    # Reset on significant backwards jump (compact, rewind, fresh transcript).
    # Persist immediately: the turn-end path announces nothing below 200k, so
    # without persistence a post-compact session would stay silenced.
    max_tracked = max(state[k] for k in STATE_KEYS)
    if max_tracked > 0 and current < max_tracked * RESET_RATIO:
        for k in STATE_KEYS:
            state[k] = 0
        save_state(state_id, state)

    key = EVENT_STATE_KEYS.get(event_name, STATE_KEY_PROMPT)
    checkpoints = ACTIONABLE_CHECKPOINTS if turn_end else CHECKPOINTS
    crossing = highest_crossing(checkpoints, current, state[key])
    if crossing is None:
        return 0
    threshold, message = crossing

    state[key] = threshold
    save_state(state_id, state)

    full_msg = f"[{current:,} tokens used] {message}"
    if turn_end:
        print(json.dumps({"decision": "block", "reason": full_msg}))
    else:
        print(emit_for(event_name, full_msg))
    return 0
```

(Diff vs current: the `session_id`/`transcript_path` block is replaced by the `measurement_target` call + unpack; `latest_main_thread_usage` gets `include_sidechain=`; `load_state`/`save_state` take `state_id`. The guard, reset, crossing, and output logic are byte-identical.)

- [ ] **Step 8: Run the suite — verify all green**

Run: `python tests\hooks\test_context_usage.py -v`
Expected: **OK — 25 tests, 0 failures, 0 errors.**

- [ ] **Step 9: Commit**

```bash
git add plugins/claude-toolkit/hooks/context-usage.py tests/hooks/test_context_usage.py
git commit -m "fix(hooks): teammate-scoped SubagentStop measurement - agent transcript + per-agent state

SubagentStop now resolves the AGENT's own transcript (agent_transcript_path,
alias subagent_transcript_path) under a per-agent state identity
<session_id>--<agent_id>, with the sidechain filter lifted for agent
transcripts (they are wholly isSidechain:true). Never falls back to the
parent's transcript_path - mis-scoped measurement was the Spike 8 facet-3
bug. One new seam: measurement_target(). Kills the shared once-per-threshold
pool collisions and the spurious end-of-run blocks on one-shot subagents."
```

---

### Task 2: Docstrings + hooks.json description

Documentation of the new scoping semantics and the accepted residual limitation. No behavior changes — the test suite must stay green untouched.

**Files:**
- Modify: `plugins/claude-toolkit/hooks/context-usage.py` (module docstring only)
- Modify: `plugins/claude-toolkit/hooks/hooks.json` (description string only — **no registration changes**)

- [ ] **Step 1: Update the SubagentStop line in the module docstring**

In `context-usage.py`, replace (currently lines 17–18):

```
  SubagentStop     -> turn-end: same as Stop, for subagent / background-
                      teammate sessions.
```

with:

```
  SubagentStop     -> turn-end: same as Stop, but measured on the AGENT's
                      own transcript (payload agent_transcript_path, alias
                      subagent_transcript_path) under a per-agent state
                      identity <session_id>--<agent_id>, so a teammate is
                      blocked on ITS OWN crossing, never the manager's
                      (Spike 8 facet 3). Agent transcripts are entirely
                      isSidechain:true, so the sidechain filter is lifted
                      there. A payload naming no agent transcript is
                      skipped (stderr breadcrumb) - never measured against
                      the parent's transcript: mis-scoped measurement is
                      the bug this scoping fixes.
```

- [ ] **Step 2: Update the state-file section of the module docstring**

Replace (currently lines 38–41):

```
State file (one JSON per session_id):
  ~/.claude/hooks/state/context-usage-<session_id>.json
  Shape: {"prompt": <t>, "tool": <t>, "stop": <t>, "subagent_stop": <t>}
  Legacy field "last_announced" migrates to "prompt" on first read.
```

with:

```
State files (one JSON per measurement identity):
  main loop:  ~/.claude/hooks/state/context-usage-<session_id>.json
  per agent:  ~/.claude/hooks/state/
              context-usage-<session_id>--<agent_id>.json
  Shape: {"prompt": <t>, "tool": <t>, "stop": <t>, "subagent_stop": <t>}
  (an agent file only ever accrues "subagent_stop" in practice). Files
  appear only on a first actionable crossing, so accumulation is bounded
  to agents that actually cross.
  Legacy field "last_announced" migrates to "prompt" on first read.
```

- [ ] **Step 3: Add the accepted-residual paragraph**

Insert a new paragraph between the "Reset:" paragraph and the "Malformed input" paragraph (i.e., after current line 46's paragraph ends):

```
Accepted residual (teammate-scoped design, 2026-06-06): teammate-originated
PostToolUse - and user prompts typed in a teammate's pane (UserPromptSubmit)
- carry no agent identifier (binary-verified), so the informational paths
remain parent-scoped: a teammate may see mid-turn announces describing the
MANAGER's context, and such a crossing consumes the parent's prompt/tool
once-per-threshold keys (possibly suppressing one manager informational
announce). The authoritative per-agent signal is the turn-end SubagentStop
block above, which IS agent-scoped.
```

- [ ] **Step 4: Update the hooks.json description string**

In `plugins/claude-toolkit/hooks/hooks.json`, replace the `"description"` value (line 2):

```
Context-window checkpoint hook — announces once per session, per event, when main-thread token usage crosses 100k / 200k / 250k / 300k. Turn-end events (Stop/SubagentStop) deliver actionable (≥200k) crossings as decision:block, forcing the handover turn (E2E F20/F22).
```

with:

```
Context-window checkpoint hook — announces once per measurement identity, per event, when token usage crosses 100k / 200k / 250k / 300k. Turn-end events (Stop/SubagentStop) deliver actionable (≥200k) crossings as decision:block, forcing the handover turn (E2E F20/F22). SubagentStop measures the subagent's OWN transcript under per-agent state, so teammates hand over on their own context, not the manager's (Spike 8 facet 3).
```

Touch nothing else in the file — the four event registrations are correct as-is.

- [ ] **Step 5: Verify**

- Run: `python tests\hooks\test_context_usage.py -v` → Expected: OK, 25 tests.
- Run: `python -c "import json; json.load(open('plugins/claude-toolkit/hooks/hooks.json'))"` → Expected: no output (valid JSON).

- [ ] **Step 6: Commit**

```bash
git add plugins/claude-toolkit/hooks/context-usage.py plugins/claude-toolkit/hooks/hooks.json
git commit -m "docs(hooks): document teammate scoping + accepted informational-path residual"
```

---

### Task 3: or-* wording audit (expected zero changes)

The design predicts no or-* agent/skill body needs touching, because their wording describes the handover-at-200k *discipline* (which is correct under the new semantics — more correct than before, since teammates now hear about their OWN context), not *whose transcript the hook measures*. This task verifies that prediction.

**Files:**
- Read-only grep over `plugins/claude-toolkit/` (agents, skills, commands). Modify only if a genuine contradiction is found (none expected).

- [ ] **Step 1: Grep for checkpoint/handover-threshold references**

Run these from the repo root (ripgrep via the Grep tool or `git grep -in`):

- Pattern `200k|200,000` in `plugins/claude-toolkit/` (exclude `hooks/`)
- Pattern `handover threshold` in `plugins/claude-toolkit/`
- Pattern `context-usage|context usage` in `plugins/claude-toolkit/` (exclude `hooks/`)
- Pattern `checkpoint` in `plugins/claude-toolkit/agents/` and `plugins/claude-toolkit/skills/`

- [ ] **Step 2: Adjudicate each hit**

For every hit, answer: *does this wording promise anything about WHOSE transcript the hook measures, or assert manager/teammates share one threshold pool?*

- Wording like "when your context crosses 200k, execute your handover protocol" / "a checkpoint hook announces crossings" — **fine, leave it** (under 1.5.2 this is now literally true for teammates).
- Wording asserting the hook measures the parent/session transcript for teammates, or that pools are shared — **fix it** (none is expected to exist).

- [ ] **Step 3: Record the outcome**

- If zero edits needed (expected): no commit. State in your task report: "or-* grep audit clean — N hits reviewed, none promises measurement-scoping semantics; zero edits."
- If a contradiction was found: make the minimal wording fix and commit:

```bash
git add <specific files>
git commit -m "docs(or-sas): align wording with per-agent checkpoint scoping"
```

---

### Task 4: Author Spike 9 in the behavioral-spikes doc

Spike 9 is **authored now, executed later** — at cutover, against the *installed* 1.5.2 (you cannot run it in this plan; the running session still has 1.5.1 hooks loaded). This mirrors how Spike 8 was authored during the 1.5.0 plan and executed at the 1.5.1 cutover.

**Files:**
- Modify: `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`

- [ ] **Step 1: Insert Spike 9 after Spike 8's RESULT block**

Insert before the `## Cutover checklist` heading (after the `---` that closes Spike 8's section):

```markdown
## Spike 9 — Teammate-scoped turn-end detection (Spike 8 facet-3 follow-up)

**Purpose:** Verify the 1.5.2 teammate-scoped measurement (design:
`docs/superpowers/specs/2026-06-06-teammate-scoped-context-checkpoints-design.md`):
a `SubagentStop` crossing measures the **agent's own** transcript and enforces the
agent's own handover under a **per-agent** state identity
(`context-usage-<session_id>--<agent_id>.json`); the manager's pools are untouched
by teammate events; one-shot subagents stop receiving spurious end-of-run blocks.

**Setup:** Plugin **1.5.2** installed (restart so the updated hook loads). A team
with at least one background teammate; real shipped thresholds (Spike 8 method:
bloat context by Reading old-transcript noise; cross-check figures with a helper
mirroring the hook's own `latest_main_thread_usage()` computation — for teammates,
read `<project>/<session-id>/subagents/agent-<id>.jsonl` WITHOUT the sidechain
filter).

**RED baseline (already recorded — Spike 8 facet 3):** a teammate was blocked at
the MANAGER's figure (parent transcript, parent session_id); shared
once-per-threshold pools observed live (a teammate's PostToolUse announce consumed
the parent's `tool` key and suppressed the manager's own mid-turn announce).

**GREEN (all five):**

1. A teammate that bloats its own context past 200k while the manager stays low is
   blocked with its **own** figure (the reason's `[N tokens used]` matches the
   teammate's `subagents/agent-<id>.jsonl` usage, not the parent transcript's).
2. The manager's pools are untouched by the teammate's crossing: the parent state
   file shows no `subagent_stop` write, and the manager's own subsequent crossing
   still announces; the teammate's write lands in
   `context-usage-<session_id>--<agent_id>.json`.
3. A manager crossing does **not** block teammates (a teammate turn-end after the
   manager passes 200k stays silent while the teammate is below threshold).
4. A one-shot subagent completing on a ≥200k session shows **no** spurious
   end-of-run block.
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
```

- [ ] **Step 2: Add cutover checklist item 6**

In the `## Cutover checklist` section, after item 5, add:

```markdown
6. **(1.5.2 teammate scoping)** After the 1.5.2 release: `claude plugin install claude-toolkit` (restart so the updated hook loads), run **Spike 9**, and record its RESULT inline. Spike 8 facet (3)'s scoping defect is not closed until Spike 9 is GREEN.
```

- [ ] **Step 3: Amend the SUITE STATUS trailing paragraph**

The doc's final paragraph currently ends:

```
Fix shape: measure the agent transcript named by the payload without the sidechain filter and key state per agent — a hook-only change, needs its own design pass + spike.
```

Replace that final sentence fragment (`a hook-only change, needs its own design pass + spike.`) with:

```
a hook-only change — **designed 2026-06-06** (`docs/superpowers/specs/2026-06-06-teammate-scoped-context-checkpoints-design.md`), implemented as **1.5.2** on branch `teammate-scoped-checkpoints`; verification = **Spike 9** above, to run at the 1.5.2 cutover (checklist item 6).
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md
git commit -m "docs(validation): author Spike 9 - teammate-scoped turn-end detection (run at 1.5.2 cutover)"
```

---

### Task 5: Version bump to 1.5.2 + plugin validation

Patch bump: bugfix of the 1.5.0 turn-end detection feature (semver + the 1.4.1/1.4.2 repo precedent).

**Files:**
- Modify: `plugins/claude-toolkit/.claude-plugin/plugin.json` (1 field)
- Modify: `.claude-plugin/marketplace.json` (2 fields)

- [ ] **Step 1: Bump the plugin manifest**

In `plugins/claude-toolkit/.claude-plugin/plugin.json` line 3:

```json
  "version": "1.5.1",
```
→
```json
  "version": "1.5.2",
```

- [ ] **Step 2: Bump the marketplace manifest (both fields)**

In `.claude-plugin/marketplace.json`: `metadata.version` (line 6) and `plugins[0].version` (line 14), both `"1.5.1"` → `"1.5.2"`.

- [ ] **Step 3: Validate**

- Run: `claude plugin validate plugins/claude-toolkit` → Expected: validation passes (plugin).
- Run: `claude plugin validate .` → Expected: validation passes (marketplace).
- Run: `claude plugin validate . --strict` → Expected: GREEN with zero warnings (strict has been clean since `ad895f7`; a new warning means this branch introduced it — fix before committing).
- Run: `python tests\hooks\test_context_usage.py -v` → Expected: OK, 25 tests.

(If the `claude plugin validate` argument forms differ in the installed CLI version, run `claude plugin validate --help` and use the equivalent invocation for plugin + marketplace; the requirement is: both validate clean, and `--strict` is warning-free.)

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "release: claude-toolkit 1.5.2 - teammate-scoped context checkpoints (Spike 8 facet-3 fix)"
```

---

### Task 6: Final verification + approval-gated finishing

**Files:** none modified — verification and branch finishing only.

- [ ] **Step 1: Full verification sweep**

- Run: `python tests\hooks\test_context_usage.py -v` → OK, 25 tests.
- Run: `claude plugin validate .` and `claude plugin validate . --strict` → both clean.
- Run: `git status` → working tree clean except the three pre-existing stray `breakout-*.png` (untracked — leave them).
- Run: `git log --oneline master..HEAD` → expect, oldest-first: the Spike-8 RESULT commit (`fbeb7af`), the design spec (`fee7212`), then this plan's commits (plan doc, Task 1 fix, Task 2 docs, Task 4 Spike 9, Task 5 release — plus Task 3's only if the audit found something).

- [ ] **Step 2: Spec-coverage spot-check**

Confirm against the design doc's "Files touched" table: every row is discharged (context-usage.py ✓ T1/T2, hooks.json ✓ T2, tests ✓ T1, spikes doc ✓ T4, manifests ✓ T5, or-* grep ✓ T3).

- [ ] **Step 3: Approval-gated finishing**

Invoke `superpowers:finishing-a-development-branch`. **Approval-gated: present the merge/PR/keep options and STOP for the user's explicit choice — do NOT merge or push anything without it** (repo rule from the prior release cycles).

- [ ] **Step 4: Hand the user the cutover reminder**

After the user's chosen finishing action, remind them (do not perform it in this session — the running session still has the 1.5.1 hook loaded):

> Cutover: `claude plugin install claude-toolkit`, restart the session, run **Spike 9** (behavioral-spikes doc, checklist item 6), and record its RESULT inline. Spike 8 facet (3) is not closed until Spike 9 is GREEN.

---

## Spec coverage map (self-review)

| Design section | Plan coverage |
|---|---|
| Core change: `measurement_target()` table (3 event rows, alias order, stem fallback, never-parent-fallback) | Task 1 Steps 4, 7b |
| `include_sidechain` on the transcript reader | Task 1 Step 7c; pins: Step 5 |
| `main()` consumes tuple; downstream untouched | Task 1 Step 7d |
| Per-agent pools / reset / re-spawn / one-shot semantics | Task 1 tests (state-scoping, reset, low-agent-high-parent); re-spawn = new agent_id = fresh pool is emergent from the state identity (no code path of its own) |
| Degradation: missing field → skip + breadcrumb; dead path → silent | Task 1 tests (breadcrumb, missing-file) |
| Residual limitations documented | Task 2 Step 3 (docstring) |
| State lifecycle (`<session>--<agent>` files, SAFE_ID, 4-key shape) | Task 1 Step 7a/7b + state-file assertions in tests |
| hooks.json description only | Task 2 Step 4 |
| Testing list 1–9 | Task 1 (all nine, plus stem-fallback and one-shot-silent extras) |
| Spike 9 authored now, executed at cutover | Task 4 |
| Version 1.5.2 + manifests | Task 5 |
| or-* zero-change grep task | Task 3 |
| Release mechanics (validate, --strict, approval-gated finish, cutover) | Tasks 5–6 |
