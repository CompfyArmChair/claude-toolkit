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
        state_file = STATE_DIR / f"context-usage-{self.session_id}.json"
        if state_file.exists():
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

    def run_hook(self, event, tokens, **extra):
        payload = {
            "hook_event_name": event,
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(tokens)),
            **extra,
        }
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    # --- turn-end (Stop / SubagentStop): actionable crossings block ---

    def test_stop_blocks_at_200k(self):
        out = json.loads(self.run_hook("Stop", 210_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("handover", out["reason"].lower())

    def test_subagent_stop_blocks_at_200k(self):
        out = json.loads(self.run_hook("SubagentStop", 210_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

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


if __name__ == "__main__":
    unittest.main()
