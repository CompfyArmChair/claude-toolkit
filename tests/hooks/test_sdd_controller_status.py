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
