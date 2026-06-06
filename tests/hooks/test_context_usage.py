"""Behavioral tests for plugins/claude-toolkit/hooks/context-usage.py.

Run: python tests\\hooks\\test_context_usage.py -v

Exercises the real stdin->stdout hook contract via subprocess. Each test uses
a unique session_id and removes its state file afterward, so the real
~/.claude/hooks/state directory is never polluted.
"""

import json
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "plugins" / "claude-toolkit" / "hooks" / "context-usage.py"
STATE_DIR = Path.home() / ".claude" / "hooks" / "state"


class ContextUsageHookTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_dir = Path(self._tmp.name)
        self.session_id = f"test-{uuid.uuid4().hex}"
        self.addCleanup(self._remove_state)

    def _remove_state(self):
        # Glob: agent-scoped tests create context-usage-<session>--<agent>.json
        # siblings alongside the session file. session_id is a per-test UUID,
        # so the glob can only match this test's files.
        for state_file in STATE_DIR.glob(f"context-usage-{self.session_id}*.json"):
            state_file.unlink()

    def _transcript(self, tokens):
        entry = {
            "type": "assistant",
            "message": {
                "usage": {
                    "input_tokens": tokens,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 0,
                }
            },
        }
        path = self.tmp_dir / "transcript.jsonl"
        path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return path

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

    def run_hook(self, event, tokens, **extra):
        payload = {
            "hook_event_name": event,
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(tokens)),
            **extra,
        }
        proc = self.run_hook_proc(json.dumps(payload))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    # --- helpers for malformed-input tests ---

    def run_hook_proc(self, stdin_text):
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def _payload(self, event, transcript_path):
        return json.dumps({
            "hook_event_name": event,
            "session_id": self.session_id,
            "transcript_path": str(transcript_path),
        })

    def _transcript_lines(self, *lines):
        path = self.tmp_dir / "transcript.jsonl"
        path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        return path

    def _write_state_file(self, content):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_file = STATE_DIR / f"context-usage-{self.session_id}.json"
        state_file.write_text(content, encoding="utf-8")

    def _usage_entry(self, usage):
        return json.dumps({"type": "assistant", "message": {"usage": usage}})

    # --- turn-end (Stop / SubagentStop): actionable crossings block ---

    def test_stop_blocks_at_200k(self):
        out = json.loads(self.run_hook("Stop", 210_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("handover", out["reason"].lower())

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

    def test_stop_below_actionable_threshold_stays_silent(self):
        # 150k crosses the informational 100k checkpoint, but turn-end events
        # never force a turn for non-actionable information.
        self.assertEqual(self.run_hook("Stop", 150_000), "")

    def test_stop_blocks_once_per_threshold(self):
        self.run_hook("Stop", 210_000)
        self.assertEqual(self.run_hook("Stop", 215_000), "")

    def test_stop_escalates_to_next_threshold(self):
        self.run_hook("Stop", 210_000)
        out = json.loads(self.run_hook("Stop", 260_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("250k", out["reason"])

    def test_stop_hook_active_guard_prevents_reblocking(self):
        self.assertEqual(self.run_hook("Stop", 210_000, stop_hook_active=True), "")

    def test_turn_end_state_is_independent_of_prompt_state(self):
        # A prompt-event announcement must not silence the turn-end block.
        self.run_hook("UserPromptSubmit", 210_000)
        out = json.loads(self.run_hook("Stop", 210_000))
        self.assertEqual(out["decision"], "block")

    def test_reset_rearms_turn_end_after_compact(self):
        self.run_hook("Stop", 310_000)                        # announce 300k
        self.assertEqual(self.run_hook("Stop", 120_000), "")  # <50% -> reset (persisted)
        out = json.loads(self.run_hook("Stop", 210_000))      # re-arms
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

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

    def test_agent_transcript_path_wins_over_alias(self):
        # Regression pin (green before AND after): when BOTH fields are
        # present, the installed binary's name (agent_transcript_path) beats
        # the docs' alias - measurement_target() reads it first. The primary
        # is past 200k and the alias below every threshold, so a block
        # proves the primary was measured.
        primary = self._agent_transcript(210_000, agent_id="aaa111")
        alias = self._agent_transcript(50_000, agent_id="bbb222")
        out = json.loads(self.run_hook(
            "SubagentStop", 50_000,
            agent_id="aaa111",
            agent_transcript_path=str(primary),
            subagent_transcript_path=str(alias),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn("[210,000 tokens used]", out["reason"])

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

    # --- informational path (UserPromptSubmit / PostToolUse): unchanged ---

    def test_prompt_event_emits_additional_context_not_block(self):
        out = json.loads(self.run_hook("UserPromptSubmit", 210_000))
        self.assertNotIn("decision", out)
        ctx = out["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "UserPromptSubmit")
        self.assertIn("200k", ctx["additionalContext"])

    def test_tool_event_announces_once(self):
        first = self.run_hook("PostToolUse", 110_000)
        self.assertIn("100k", first)
        self.assertEqual(self.run_hook("PostToolUse", 120_000), "")

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

    # --- malformed-input hardening: graceful recovery, exit 0, one stderr
    # --- breadcrumb naming what was malformed (visible under claude --debug)

    def test_non_dict_state_file_recovers_fresh_and_warns(self):
        self._write_state_file(json.dumps([1, 2, 3]))
        proc = self.run_hook_proc(self._payload("Stop", self._transcript(210_000)))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("state file", proc.stderr)

    def test_non_numeric_usage_field_counts_zero_and_warns(self):
        transcript = self._transcript_lines(self._usage_entry({
            "input_tokens": "lots",  # malformed -> counts as 0
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 210_000,
            "output_tokens": 0,
        }))
        proc = self.run_hook_proc(self._payload("Stop", transcript))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")  # numeric fields alone reach 210k
        self.assertIn("200k", out["reason"])
        self.assertIn("usage", proc.stderr)

    def test_non_dict_stdin_payload_ignored_with_warning(self):
        proc = self.run_hook_proc(json.dumps([1, 2, 3]))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("stdin", proc.stderr)

    def test_non_dict_transcript_line_skipped_not_poisoning_scan(self):
        transcript = self._transcript_lines(
            json.dumps(["not", "a", "dict"]),
            self._usage_entry({
                "input_tokens": 210_000,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            }),
        )
        proc = self.run_hook_proc(self._payload("Stop", transcript))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("transcript", proc.stderr)

    # Non-string payload string-fields (transcript paths, session_id,
    # hook_event_name, agent_id) must degrade per the same contract - the
    # naive read raises TypeError (Path(123), re.sub on an int session_id,
    # dict lookup on an unhashable event name) and breaks the exit-0 promise.

    def test_non_string_transcript_path_ignored_with_warning(self):
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "Stop",
            "session_id": self.session_id,
            "transcript_path": 12345,
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("transcript_path", proc.stderr)

    def test_non_string_agent_transcript_field_skips_with_breadcrumb(self):
        # Parent transcript past 200k: degrading must still not fall back to
        # measuring the parent (same rule as the missing-field test above).
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "SubagentStop",
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(210_000)),
            "agent_id": "aaa111",
            "agent_transcript_path": {"path": "agent-aaa111.jsonl"},
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("agent_transcript_path", proc.stderr)

    def test_non_string_session_id_falls_back_with_warning(self):
        # Below threshold: the pin is exit 0 + breadcrumb (no crash), not
        # output. The state identity degrades to "default" (absent-field
        # rule), which only malformed payloads ever use.
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "Stop",
            "session_id": 42,
            "transcript_path": str(self._transcript(50_000)),
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("session_id", proc.stderr)

    def test_non_string_event_name_treated_as_prompt_event(self):
        # An unhashable event name ({"x": 1}) must not crash the state-key
        # lookup; the event degrades to the default (UserPromptSubmit).
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": {"x": 1},
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(210_000)),
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(
            out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit"
        )
        self.assertIn("hook_event_name", proc.stderr)

    def test_non_string_agent_id_falls_back_to_transcript_stem(self):
        # A non-string agent_id is malformed input - treated as absent, so
        # the transcript stem keys the state (not a stringified garbage id).
        agent_t = self._agent_transcript(210_000, agent_id="ccc333")
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "SubagentStop",
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(50_000)),
            "agent_id": 7,
            "agent_transcript_path": str(agent_t),
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")
        self.assertIn("agent_id", proc.stderr)
        stem_state = STATE_DIR / (
            f"context-usage-{self.session_id}--agent-ccc333.json"
        )
        self.assertTrue(stem_state.exists())

    def test_non_dict_message_field_skipped_not_poisoning_scan(self):
        transcript = self._transcript_lines(
            json.dumps({"type": "assistant", "message": "oops"}),
            self._usage_entry({
                "input_tokens": 210_000,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            }),
        )
        proc = self.run_hook_proc(self._payload("Stop", transcript))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("transcript", proc.stderr)


if __name__ == "__main__":
    unittest.main()
