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
HOOKS_JSON = REPO_ROOT / "plugins" / "claude-toolkit" / "hooks" / "hooks.json"


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
        self.assertIn("reasoning", out["reason"].lower())

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

    def test_subagent_stop_explicit_transcript_wins_over_derived(self):
        # Spec 5.1 rule 1 / spec 8 test 3: "an explicit agent_transcript_path
        # wins over the derived path when both exist, so SubagentStop
        # behaves as today."
        # Fixture built to break the promise: the SAME agent_id has both a
        # derived transcript (50k, below every threshold) and an explicit
        # one (210k) on disk. Only measuring the explicit path produces the
        # block below; measuring the derived path (or the untouched parent,
        # at 50k) would not.
        # Red evidence: with the candidate order in measurement_target()
        # temporarily swapped (derived tried before explicit), this test
        # fails - the derived 50k transcript is picked, nothing crosses
        # 200k, and the assertion on "decision" errors. Reverted, it passes.
        self._derived_agent_transcript(50_000, "ccc333")
        explicit = self._agent_transcript(210_000, agent_id="ccc333")
        out = json.loads(self.run_hook(
            "SubagentStop", 50_000,
            agent_id="ccc333", agent_transcript_path=str(explicit),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("[210,000 tokens used]", out["reason"])

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

    def test_reset_rearms_turn_end_after_compact(self):
        self.run_hook("Stop", 310_000)                        # announce 300k
        self.assertEqual(self.run_hook("Stop", 120_000), "")  # <50% -> reset (persisted)
        out = json.loads(self.run_hook("Stop", 210_000))      # re-arms
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

    def test_turn_end_reasons_carry_advisory_and_instruction_at_every_tier(self):
        # 2026-07-21 design change: each >=200k message keeps the sensor
        # advisory (figure, threshold, reasoning-quality implication) AND
        # carries the baseline instruction - wrap up and use /handover.
        # 250k/300k escalate to "stop immediately"; 300k additionally notes
        # that work quality may have been compromised. Vague deferral
        # ("operating instructions") stays banned. Escalation walks all
        # three actionable tiers in one session.
        # Spec 5.1 wording: main-scoped 200k+ messages always say /handover
        # and never name a pause protocol.
        reasons = {}
        for tokens, tier in (
            (210_000, "200k"),
            (260_000, "250k"),
            (310_000, "300k"),
        ):
            reasons[tier] = json.loads(self.run_hook("Stop", tokens))["reason"]
        for tier, reason in reasons.items():
            with self.subTest(tier=tier):
                self.assertIn(tier, reason)
                self.assertIn("reasoning", reason.lower())    # advisory kept
                self.assertIn("wrap up", reason.lower())      # instruction
                self.assertIn("/handover", reason)
                self.assertNotIn("pause protocol", reason)   # main scope never names it
                self.assertNotIn("operating instructions", reason.lower())
        self.assertNotIn("stop immediately", reasons["200k"].lower())
        self.assertIn("stop immediately", reasons["250k"].lower())
        self.assertIn("stop immediately", reasons["300k"].lower())
        self.assertNotIn("compromised", reasons["200k"].lower())
        self.assertNotIn("compromised", reasons["250k"].lower())
        self.assertIn("compromised", reasons["300k"].lower())

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

    def test_informational_warnings_carry_advisory_and_instruction(self):
        # Same advisory+instruction wording on the informational path: the
        # >=200k additionalContext warnings report the reasoning-quality
        # implication AND instruct wrap-up + /handover, with the same
        # escalation as the turn-end path (250k/300k stop immediately,
        # 300k notes possible quality compromise).
        # Spec 5.1 wording: main-scoped 200k+ messages always say /handover
        # and never name a pause protocol.
        contexts = {}
        for tokens, tier in (
            (210_000, "200k"),
            (260_000, "250k"),
            (310_000, "300k"),
        ):
            out = json.loads(self.run_hook("UserPromptSubmit", tokens))
            contexts[tier] = out["hookSpecificOutput"]["additionalContext"]
        for tier, ctx in contexts.items():
            with self.subTest(tier=tier):
                self.assertIn(tier, ctx)
                self.assertIn("reasoning", ctx.lower())       # advisory kept
                self.assertIn("wrap up", ctx.lower())         # instruction
                self.assertIn("/handover", ctx)
                self.assertNotIn("pause protocol", ctx)   # main scope never names it
                self.assertNotIn("operating instructions", ctx.lower())
        self.assertNotIn("stop immediately", contexts["200k"].lower())
        self.assertIn("stop immediately", contexts["250k"].lower())
        self.assertIn("stop immediately", contexts["300k"].lower())
        self.assertNotIn("compromised", contexts["200k"].lower())
        self.assertNotIn("compromised", contexts["250k"].lower())
        self.assertIn("compromised", contexts["300k"].lower())

    def test_100k_checkpoint_stays_advisory_only(self):
        # The sub-actionable 100k checkpoint carries no instruction: it is
        # context, not a directive to hand over.
        out = json.loads(self.run_hook("UserPromptSubmit", 110_000))
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("100k", ctx)
        self.assertNotIn("/handover", ctx)
        self.assertNotIn("wrap up", ctx.lower())

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
        # instruction in either scope. Regression pin (green before and
        # after this change): red evidence came from temporarily adding a
        # 100k entry to INSTRUCTIONS[SCOPE_AGENT], not from a code path
        # exercised by default.
        self._derived_agent_transcript(110_000, "adv111")
        out = json.loads(self.run_hook("PostToolUse", 50_000, agent_id="adv111"))
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("100k", ctx)
        self.assertNotIn("pause protocol", ctx)
        self.assertNotIn("/handover", ctx)

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
