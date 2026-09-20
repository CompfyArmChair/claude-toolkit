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
from collections import namedtuple
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "plugins" / "claude-toolkit" / "hooks" / "context-usage.py"
STATE_DIR = Path.home() / ".claude" / "hooks" / "state"
HOOKS_JSON = REPO_ROOT / "plugins" / "claude-toolkit" / "hooks" / "hooks.json"
LADDER_FILE = (
    REPO_ROOT / "plugins" / "claude-toolkit" / "hooks" / "context-checkpoints.txt"
)


def read_ladder(path=LADDER_FILE):
    """The shipped figure ladder: one row per model family, four ascending
    figures per row. Parsed here independently of the hook's own parser, so a
    disagreement between the two surfaces as a behaviour mismatch instead of
    cancelling out. Figures are fixture INPUTS only - spec §9.5 forbids a
    test asserting one."""
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("#", 1)[0].split()
        if fields:
            rows[fields[0]] = tuple(int(figure) for figure in fields[1:])
    return rows


LADDER = read_ladder()

# Checkpoint levels by name (spec §2). Names and ordering are what this
# release is about, so they are written here; the figures never are.
ADVISORY, WRAP_UP, STOP, STOP_COMPROMISED = 0, 1, 2, 3
ACTIONABLE_LEVELS = (WRAP_UP, STOP, STOP_COMPROMISED)
LEVEL_NAMES = ("ADVISORY", "WRAP-UP", "STOP", "STOP-COMPROMISED")

# Spec §3: a transcript with no readable model id is measured against this row.
DEFAULT_FAMILY = "opus"


def label(level, family=DEFAULT_FAMILY):
    """How the hook writes a family's figure for a level (spec §4): whole
    thousands, then "k". Derived from the ladder, never typed."""
    return f"{LADDER[family][level] // 1000}k"


def announcement(level, family=DEFAULT_FAMILY):
    """The first sentence spec §4 promises for a crossing: the checkpoint's
    NAME, then the family's own figure for it."""
    return f"Context checkpoint {LEVEL_NAMES[level]} crossed at {label(level, family)}"


class HookFixture(unittest.TestCase):
    """Shared fixture: temp transcripts, per-test session identity, state
    cleanup, the subprocess hook contract, and the ladder-derived token counts
    every test is written in. No tests of its own."""

    # Spec §2 wording per actionable level: (must contain, must not contain),
    # matched case-insensitively, keyed by LEVEL and never by figure. The
    # level-3 "must" is the INSTRUCTION's own phrase rather than the bare word
    # "compromised": the name STOP-COMPROMISED now puts that word into every
    # level-3 message, so the bare word would pass even with the instruction
    # deleted.
    ESCALATION = {
        WRAP_UP: ((), ("stop immediately", "compromised")),
        STOP: (("stop immediately",), ("compromised",)),
        STOP_COMPROMISED: (
            ("stop immediately", "work quality may have been compromised"), ()
        ),
    }

    @staticmethod
    def crossing(level, family=DEFAULT_FAMILY):
        """The token count that crosses `level` in a family's row, and no
        severer checkpoint."""
        return LADDER[family][level]

    @staticmethod
    def inside(level, family=DEFAULT_FAMILY):
        """A count strictly inside `level`'s band - past its figure, below the
        next checkpoint - so a second reading of the same checkpoint cannot be
        mistaken for the same number twice."""
        figures = LADDER[family]
        ceiling = (
            figures[level + 1] if level + 1 < len(figures) else figures[level] * 2
        )
        return (figures[level] + ceiling) // 2

    @staticmethod
    def below(level, family=DEFAULT_FAMILY):
        """One token short of `level`."""
        return LADDER[family][level] - 1

    @staticmethod
    def after_compaction(level, family=DEFAULT_FAMILY):
        """A count low enough to trip the 50 percent reset against the figure
        `level` was announced at."""
        return LADDER[family][level] // 2 - 1

    def assertEscalates(self, messages):
        """Each actionable level's message carries its own escalation wording
        and none of the severer level's (spec §2). `messages` maps level to
        the text announced for it."""
        for level, text in messages.items():
            must, must_not = self.ESCALATION[level]
            with self.subTest(level=LEVEL_NAMES[level], check="escalation"):
                for phrase in must:
                    self.assertIn(phrase, text.lower())
                for phrase in must_not:
                    self.assertNotIn(phrase, text.lower())

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_dir = Path(self._tmp.name)
        self.session_id = self._base_session_id = f"test-{uuid.uuid4().hex}"
        self.addCleanup(self._remove_state)

    def _fresh_identity(self, *tags):
        """A distinct measurement identity under this test's base prefix, so a
        test that needs several cannot leak once-per-checkpoint state between
        them."""
        self.session_id = "-".join((self._base_session_id, *map(str, tags)))

    def _remove_state(self):
        # Glob: agent-scoped tests create context-usage-<session>--<agent>.json
        # siblings alongside the session file, and _fresh_identity adds more
        # under the same base prefix. That prefix is a per-test UUID, so the
        # glob can only match this test's files.
        for state_file in STATE_DIR.glob(
            f"context-usage-{self._base_session_id}*.json"
        ):
            state_file.unlink()

    @staticmethod
    def _usage(tokens):
        return {
            "input_tokens": tokens,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "output_tokens": 0,
        }

    def _main_entry(self, tokens, model=None):
        """One main-transcript assistant entry. No model -> the hook's
        default (Opus) figures (spec 2026-09-20 §3); a model id picks that
        family's figures."""
        message = {"usage": self._usage(tokens)}
        if model is not None:
            message["model"] = model
        return {"type": "assistant", "message": message}

    def _transcript(self, tokens, model=None):
        entry = self._main_entry(tokens, model)
        path = self.tmp_dir / "transcript.jsonl"
        path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return path

    def _agent_entry(self, tokens, agent_id, model=None):
        """One assistant entry as the harness writes it in an agent's own
        transcript: isSidechain on every line (verified on-disk shape)."""
        message = {"usage": self._usage(tokens)}
        if model is not None:
            message["model"] = model
        return {
            "type": "assistant",
            "isSidechain": True,
            "agentId": agent_id,
            "message": message,
        }

    def _agent_transcript(self, tokens, agent_id, model=None):
        """An agent transcript at an EXPLICIT path (what SubagentStop names in
        agent_transcript_path)."""
        path = self.tmp_dir / f"agent-{agent_id}.jsonl"
        path.write_text(
            json.dumps(self._agent_entry(tokens, agent_id, model)) + "\n",
            encoding="utf-8",
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

    def run_hook(self, event, tokens, model=None, **extra):
        payload = {
            "hook_event_name": event,
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(tokens, model)),
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



class ContextUsageHookTests(HookFixture):
    """Channel, scope, state and malformed-input behaviour. No fixture here
    carries a model id, so every checkpoint is the hook's default (opus) row
    - spec 2026-09-20 §3."""

    # --- turn-end (Stop / SubagentStop): actionable crossings block ---

    def test_stop_blocks_at_the_wrap_up_checkpoint(self):
        out = json.loads(self.run_hook("Stop", self.crossing(WRAP_UP)))
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])
        self.assertIn("reasoning", out["reason"].lower())

    def test_subagent_stop_measures_agent_transcript_not_parents(self):
        # The agent transcript (past wrap-up, every entry isSidechain) is
        # measured; the parent transcript (below every checkpoint) is not.
        # 1.5.1 had this inverted.
        tokens = self.crossing(WRAP_UP)
        agent_t = self._agent_transcript(tokens, agent_id="aaa111")
        out = json.loads(self.run_hook(
            "SubagentStop", self.below(ADVISORY),
            agent_id="aaa111", agent_transcript_path=str(agent_t),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])
        self.assertIn(f"[{tokens:,} tokens used]", out["reason"])

    def test_stop_below_actionable_threshold_stays_silent(self):
        # The advisory checkpoint is crossed, but turn-end events never force
        # a turn for non-actionable information.
        self.assertEqual(self.run_hook("Stop", self.crossing(ADVISORY)), "")

    def test_stop_blocks_once_per_threshold(self):
        self.run_hook("Stop", self.crossing(WRAP_UP))
        self.assertEqual(self.run_hook("Stop", self.inside(WRAP_UP)), "")

    def test_stop_escalates_to_next_threshold(self):
        self.run_hook("Stop", self.crossing(WRAP_UP))
        out = json.loads(self.run_hook("Stop", self.crossing(STOP)))
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(STOP), out["reason"])

    def test_stop_hook_active_guard_prevents_reblocking(self):
        self.assertEqual(
            self.run_hook("Stop", self.crossing(WRAP_UP), stop_hook_active=True), ""
        )

    # --- spec 5.1 turn-end addendum: the block is a delivery channel. Once an
    # --- informational channel (prompt or tool key) has announced checkpoint
    # --- C for an identity, the turn-end block for C is skipped; it still
    # --- fires when neither did, and for a severer checkpoint than announced.
    # --- Replaces test_turn_end_state_is_independent_of_prompt_state
    # --- (2026-06-06), whose promise the addendum reverses.

    def test_main_turn_end_skipped_after_prompt_announced_same_threshold(self):
        self.run_hook("UserPromptSubmit", self.crossing(WRAP_UP))
        self.assertEqual(self.run_hook("Stop", self.inside(WRAP_UP)), "")

    def test_main_turn_end_skipped_after_tool_announced_same_threshold(self):
        self.run_hook("PostToolUse", self.crossing(WRAP_UP))
        self.assertEqual(self.run_hook("Stop", self.inside(WRAP_UP)), "")

    def test_agent_turn_end_skipped_after_tool_announced_same_threshold(self):
        # The controller's normal pause: the mid-wake warning (derived
        # transcript) landed, so its SubagentStop (explicit transcript, same
        # agent id) must not force a wasted turn.
        self._derived_agent_transcript(self.crossing(WRAP_UP), "aaa111")
        self.assertIn(
            announcement(WRAP_UP),
            self.run_hook("PostToolUse", self.below(ADVISORY), agent_id="aaa111"),
        )
        explicit = self._agent_transcript(self.inside(WRAP_UP), agent_id="aaa111")
        self.assertEqual(
            self.run_hook(
                "SubagentStop", self.below(ADVISORY),
                agent_id="aaa111", agent_transcript_path=str(explicit),
            ),
            "",
        )

    def test_subagent_stop_explicit_transcript_wins_over_derived(self):
        # Spec 5.1 rule 1 / spec 8 test 3: "an explicit agent_transcript_path
        # wins over the derived path when both exist, so SubagentStop
        # behaves as today."
        # Fixture built to break the promise: the SAME agent_id has both a
        # derived transcript (below every checkpoint) and an explicit one
        # (past wrap-up) on disk. Only measuring the explicit path produces
        # the block below; measuring the derived path - or the untouched
        # parent, equally low - would not.
        # Red evidence: with the candidate order in measurement_target()
        # temporarily swapped (derived tried before explicit), this test
        # fails - the derived low transcript is picked, no actionable
        # checkpoint is crossed, and the assertion on "decision" errors.
        # Reverted, it passes.
        tokens = self.crossing(WRAP_UP)
        self._derived_agent_transcript(self.below(ADVISORY), "ccc333")
        explicit = self._agent_transcript(tokens, agent_id="ccc333")
        out = json.loads(self.run_hook(
            "SubagentStop", self.below(ADVISORY),
            agent_id="ccc333", agent_transcript_path=str(explicit),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])
        self.assertIn(f"[{tokens:,} tokens used]", out["reason"])

    def test_turn_end_still_blocks_when_no_informational_channel_announced(self):
        # The starved-loop case the block was built for (F20/F22): no prompt
        # or tool announcement for the identity -> block, both scopes.
        with self.subTest(scope="main"):
            out = json.loads(self.run_hook("Stop", self.crossing(WRAP_UP)))
            self.assertEqual(out["decision"], "block")
            self.assertIn(announcement(WRAP_UP), out["reason"])
        with self.subTest(scope="agent"):
            explicit = self._agent_transcript(
                self.crossing(WRAP_UP), agent_id="bbb222"
            )
            out = json.loads(self.run_hook(
                "SubagentStop", self.below(ADVISORY),
                agent_id="bbb222", agent_transcript_path=str(explicit),
            ))
            self.assertEqual(out["decision"], "block")
            self.assertIn(announcement(WRAP_UP), out["reason"])

    def test_turn_end_still_blocks_for_a_higher_threshold_than_announced(self):
        # Whole claim: only the announced checkpoint is skipped. A later,
        # severer crossing still forces its delivery turn.
        self.run_hook("UserPromptSubmit", self.crossing(WRAP_UP))
        out = json.loads(self.run_hook("Stop", self.crossing(STOP)))
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(STOP), out["reason"])

    def test_reset_rearms_both_channels_together(self):
        # 5.1 addendum, last sentence: the 50 percent reset clears all keys,
        # so after a compaction the turn-end channel is live again even
        # though the prompt channel had announced before it.
        self.run_hook("UserPromptSubmit", self.crossing(WRAP_UP))
        self.assertEqual(self.run_hook("Stop", self.inside(WRAP_UP)), "")   # skipped
        self.assertEqual(
            self.run_hook("Stop", self.after_compaction(WRAP_UP)), ""
        )                                                                   # reset
        out = json.loads(self.run_hook("Stop", self.crossing(WRAP_UP)))
        self.assertEqual(out["decision"], "block")

    def test_reset_rearms_turn_end_after_compact(self):
        self.run_hook("Stop", self.crossing(STOP_COMPROMISED))
        self.assertEqual(
            self.run_hook("Stop", self.after_compaction(STOP_COMPROMISED)), ""
        )                                                    # reset, persisted
        out = json.loads(self.run_hook("Stop", self.crossing(WRAP_UP)))
        self.assertEqual(out["decision"], "block")           # re-armed
        self.assertIn(announcement(WRAP_UP), out["reason"])

    def test_turn_end_reasons_carry_advisory_and_instruction_at_every_tier(self):
        # 2026-07-21 design change: every actionable message keeps the sensor
        # advisory (figure, checkpoint, reasoning-quality implication) AND
        # carries the baseline instruction - wrap up and use /handover. STOP
        # and STOP-COMPROMISED escalate to "stop immediately";
        # STOP-COMPROMISED additionally notes that work quality may have been
        # compromised. Vague deferral ("operating instructions") stays banned.
        # Escalation walks all three actionable levels in one session.
        # Spec 5.1 wording: main-scoped actionable messages always say
        # /handover and never name a pause protocol.
        reasons = {
            level: json.loads(
                self.run_hook("Stop", self.crossing(level))
            )["reason"]
            for level in ACTIONABLE_LEVELS
        }
        for level, reason in reasons.items():
            with self.subTest(level=LEVEL_NAMES[level]):
                self.assertIn(announcement(level), reason)
                self.assertIn("reasoning", reason.lower())    # advisory kept
                self.assertIn("wrap up", reason.lower())      # instruction
                self.assertIn("/handover", reason)
                self.assertNotIn("pause protocol", reason)   # main scope never names it
                self.assertNotIn("operating instructions", reason.lower())
        self.assertEscalates(reasons)

    # --- SubagentStop: teammate-scoped measurement (Spike 8 facet 3) ---
    # The agent's OWN transcript is measured (sidechain filter lifted - agent
    # transcripts are wholly isSidechain:true) under a per-agent state
    # identity <session_id>--<agent_id>. Never fall back to the parent's
    # transcript_path: mis-scoped measurement IS the 1.5.1 bug.

    def test_subagent_transcript_path_alias_accepted(self):
        # Docs name the field subagent_transcript_path; the installed binary
        # says agent_transcript_path. Either must work (naming drift is real).
        agent_t = self._agent_transcript(self.crossing(WRAP_UP), agent_id="aaa111")
        out = json.loads(self.run_hook(
            "SubagentStop", self.below(ADVISORY),
            agent_id="aaa111", subagent_transcript_path=str(agent_t),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])

    def test_agent_transcript_path_wins_over_alias(self):
        # Regression pin (green before AND after): when BOTH fields are
        # present, the installed binary's name (agent_transcript_path) beats
        # the docs' alias - measurement_target() reads it first. The primary
        # is past the wrap-up checkpoint and the alias below every
        # checkpoint, so a block proves the primary was measured.
        tokens = self.crossing(WRAP_UP)
        primary = self._agent_transcript(tokens, agent_id="aaa111")
        alias = self._agent_transcript(self.below(ADVISORY), agent_id="bbb222")
        out = json.loads(self.run_hook(
            "SubagentStop", self.below(ADVISORY),
            agent_id="aaa111",
            agent_transcript_path=str(primary),
            subagent_transcript_path=str(alias),
        ))
        self.assertEqual(out["decision"], "block")
        self.assertIn(f"[{tokens:,} tokens used]", out["reason"])

    def test_subagent_stop_without_agent_transcript_skips_with_breadcrumb(self):
        # No agent-transcript field (future payload rename): skip + stderr
        # breadcrumb, exit 0, no output, parent state untouched. The parent
        # transcript is past the wrap-up checkpoint, so a parent fallback
        # would block here.
        proc = self.run_hook_proc(self._payload(
            "SubagentStop", self._transcript(self.crossing(WRAP_UP))
        ))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("agent_transcript_path", proc.stderr)
        parent_state = STATE_DIR / f"context-usage-{self.session_id}.json"
        self.assertFalse(parent_state.exists())

    def test_agent_crossing_writes_only_agent_scoped_state(self):
        # Spike-8 collision regression: the teammate's crossing must land in
        # the agent's own state file, leaving the manager's pools untouched.
        agent_t = self._agent_transcript(self.crossing(WRAP_UP), agent_id="aaa111")
        self.run_hook(
            "SubagentStop", self.below(ADVISORY),
            agent_id="aaa111", agent_transcript_path=str(agent_t),
        )
        parent_state = STATE_DIR / f"context-usage-{self.session_id}.json"
        agent_state = (
            STATE_DIR / f"context-usage-{self.session_id}--aaa111.json"
        )
        self.assertFalse(parent_state.exists())
        self.assertTrue(agent_state.exists())
        # The manager's own subsequent crossing still announces.
        out = json.loads(self.run_hook("Stop", self.crossing(WRAP_UP)))
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])

    def test_two_agents_cross_independently(self):
        # 1.5.1 pooled all agents in the parent's subagent_stop key: the
        # second agent's own wrap-up crossing would have been suppressed.
        a = self._agent_transcript(self.crossing(WRAP_UP), agent_id="aaa111")
        out_a = json.loads(self.run_hook(
            "SubagentStop", self.below(ADVISORY),
            agent_id="aaa111", agent_transcript_path=str(a),
        ))
        self.assertEqual(out_a["decision"], "block")
        b = self._agent_transcript(self.inside(WRAP_UP), agent_id="bbb222")
        out_b = json.loads(self.run_hook(
            "SubagentStop", self.below(ADVISORY),
            agent_id="bbb222", agent_transcript_path=str(b),
        ))
        self.assertEqual(out_b["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out_b["reason"])

    def test_agent_id_falls_back_to_transcript_stem(self):
        # No agent_id in the payload: the transcript filename stem keys the
        # state, so per-agent pooling survives the field's absence.
        agent_t = self._agent_transcript(self.crossing(WRAP_UP), agent_id="ccc333")
        out = json.loads(self.run_hook(
            "SubagentStop", self.below(ADVISORY),
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
        agent_t = self._agent_transcript(self.crossing(WRAP_UP), agent_id="aaa111")
        self.assertEqual(
            self.run_hook(
                "SubagentStop", self.below(ADVISORY),
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
                "SubagentStop", self.below(ADVISORY),
                agent_id="aaa111", agent_transcript_path=str(agent_t),
            )

        out = json.loads(fire(self.crossing(STOP_COMPROMISED)))
        self.assertIn(announcement(STOP_COMPROMISED), out["reason"])
        self.assertEqual(fire(self.after_compaction(STOP_COMPROMISED)), "")
        out = json.loads(fire(self.crossing(WRAP_UP)))       # re-armed
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])

    def test_missing_agent_transcript_file_skips_silently(self):
        # Dead agent path + parent past the wrap-up checkpoint: still no
        # parent fallback.
        self.assertEqual(
            self.run_hook(
                "SubagentStop", self.crossing(WRAP_UP),
                agent_id="aaa111",
                agent_transcript_path=str(self.tmp_dir / "agent-gone.jsonl"),
            ),
            "",
        )

    def test_low_agent_usage_stays_silent_despite_high_parent_usage(self):
        # One-shot subagent completing on a session past the wrap-up
        # checkpoint: 1.5.1 measured the parent and emitted a spurious
        # end-of-run block. Agent-scoped measurement is silent.
        agent_t = self._agent_transcript(self.below(ADVISORY), agent_id="aaa111")
        self.assertEqual(
            self.run_hook(
                "SubagentStop", self.crossing(WRAP_UP),
                agent_id="aaa111", agent_transcript_path=str(agent_t),
            ),
            "",
        )

    # --- informational path (UserPromptSubmit / PostToolUse): unchanged ---

    def test_prompt_event_emits_additional_context_not_block(self):
        out = json.loads(self.run_hook("UserPromptSubmit", self.crossing(WRAP_UP)))
        self.assertNotIn("decision", out)
        ctx = out["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "UserPromptSubmit")
        self.assertIn(announcement(WRAP_UP), ctx["additionalContext"])

    def test_informational_warnings_carry_advisory_and_instruction(self):
        # Same advisory+instruction wording on the informational path: the
        # actionable additionalContext warnings report the reasoning-quality
        # implication AND instruct wrap-up + /handover, with the same
        # escalation as the turn-end path.
        # Spec 5.1 wording: main-scoped actionable messages always say
        # /handover and never name a pause protocol.
        contexts = {
            level: json.loads(
                self.run_hook("UserPromptSubmit", self.crossing(level))
            )["hookSpecificOutput"]["additionalContext"]
            for level in ACTIONABLE_LEVELS
        }
        for level, ctx in contexts.items():
            with self.subTest(level=LEVEL_NAMES[level]):
                self.assertIn(announcement(level), ctx)
                self.assertIn("reasoning", ctx.lower())       # advisory kept
                self.assertIn("wrap up", ctx.lower())         # instruction
                self.assertIn("/handover", ctx)
                self.assertNotIn("pause protocol", ctx)   # main scope never names it
                self.assertNotIn("operating instructions", ctx.lower())
        self.assertEscalates(contexts)

    def test_the_advisory_checkpoint_carries_no_instruction(self):
        # The sub-actionable advisory checkpoint is context, not a directive
        # to hand over.
        out = json.loads(self.run_hook("UserPromptSubmit", self.crossing(ADVISORY)))
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn(announcement(ADVISORY), ctx)
        self.assertNotIn("/handover", ctx)
        self.assertNotIn("wrap up", ctx.lower())

    def test_tool_event_announces_once(self):
        first = self.run_hook("PostToolUse", self.crossing(ADVISORY))
        self.assertIn(announcement(ADVISORY), first)
        self.assertEqual(self.run_hook("PostToolUse", self.inside(ADVISORY)), "")

    def test_main_transcript_still_excludes_sidechain_entries(self):
        # Regression pin (green before AND after): lifting the sidechain
        # filter applies ONLY to agent transcripts. A sidechain entry in a
        # MAIN transcript stays invisible (historical inline-sidechain
        # format). Order matters: the sidechain entry is LAST and far past
        # every checkpoint, so an unfiltered read would block.
        transcript = self._transcript_lines(
            self._usage_entry({
                "input_tokens": self.below(WRAP_UP),
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            }),
            json.dumps({
                "type": "assistant",
                "isSidechain": True,
                "message": {"usage": {"input_tokens": self.crossing(STOP_COMPROMISED)}},
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
        # parent far past the wrap-up checkpoint with the agent under every
        # checkpoint (a parent-scoped read announces), then the reverse (a
        # parent-scoped read stays silent). PostToolUse and
        # PostToolUseFailure alike.
        tokens = self.crossing(WRAP_UP)
        for event in ("PostToolUse", "PostToolUseFailure"):
            with self.subTest(event=event, case="high parent, low agent"):
                agent_id = f"low{event}"
                self._derived_agent_transcript(self.below(ADVISORY), agent_id)
                self.assertEqual(
                    self.run_hook(event, self.crossing(STOP), agent_id=agent_id), ""
                )
            with self.subTest(event=event, case="low parent, high agent"):
                agent_id = f"high{event}"
                self._derived_agent_transcript(tokens, agent_id)
                out = json.loads(
                    self.run_hook(event, self.below(ADVISORY), agent_id=agent_id)
                )
                ctx = out["hookSpecificOutput"]
                self.assertEqual(ctx["hookEventName"], event)
                self.assertIn(f"[{tokens:,} tokens used]", ctx["additionalContext"])
                self.assertIn(announcement(WRAP_UP), ctx["additionalContext"])

    def test_agent_crossing_leaves_parent_state_byte_identical(self):
        # Spec 8 test 2 (5.1 rule 1). The parent already owns a state file
        # (its own advisory announce), so "untouched" is byte identity, not
        # absence. The parent sits in the advisory band: a mis-scoped
        # PostToolUse would record the wrap-up level there and change the
        # bytes.
        self.run_hook("UserPromptSubmit", self.crossing(ADVISORY))
        parent_state = STATE_DIR / f"context-usage-{self.session_id}.json"
        before = parent_state.read_bytes()
        self._derived_agent_transcript(self.crossing(WRAP_UP), "aaa111")
        out = self.run_hook("PostToolUse", self.crossing(ADVISORY), agent_id="aaa111")
        self.assertIn(announcement(WRAP_UP), out)
        self.assertEqual(parent_state.read_bytes(), before)
        agent_state = STATE_DIR / f"context-usage-{self.session_id}--aaa111.json"
        self.assertEqual(
            json.loads(agent_state.read_text(encoding="utf-8"))["tool"], WRAP_UP
        )

    def test_agent_id_without_resolvable_transcript_skips_with_breadcrumb(self):
        # Spec 8 test 4 (5.1 rule 2). No explicit field, no derived file, and
        # the parent past every checkpoint beside it: any fallback would
        # announce. Expect nothing on stdout, no state file for either
        # identity, and a stderr breadcrumb naming the agent.
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "PostToolUse",
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(self.crossing(STOP_COMPROMISED))),
            "agent_id": "ghost1",
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("ghost1", proc.stderr)
        self.assertEqual(
            list(STATE_DIR.glob(f"context-usage-{self.session_id}*.json")), []
        )

    def test_post_tool_use_and_failure_share_the_tool_key(self):
        # Spec 8 test 6 (5.1 events). A checkpoint announced by one event is
        # not re-announced by the other - both orders, both scopes, each on
        # a fresh identity.
        for first, second in (
            ("PostToolUse", "PostToolUseFailure"),
            ("PostToolUseFailure", "PostToolUse"),
        ):
            with self.subTest(scope="agent", first=first):
                agent_id = f"share{first}"
                self._derived_agent_transcript(self.crossing(WRAP_UP), agent_id)
                self.assertIn(
                    announcement(WRAP_UP),
                    self.run_hook(first, self.below(ADVISORY), agent_id=agent_id),
                )
                self._derived_agent_transcript(self.inside(WRAP_UP), agent_id)
                self.assertEqual(
                    self.run_hook(second, self.below(ADVISORY), agent_id=agent_id), ""
                )
        with self.subTest(scope="main"):
            self.assertIn(
                announcement(WRAP_UP),
                self.run_hook("PostToolUseFailure", self.crossing(WRAP_UP)),
            )
            self.assertEqual(self.run_hook("PostToolUse", self.inside(WRAP_UP)), "")

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
        # turn-end block), all three actionable levels, walked in escalation
        # on one identity per channel.
        for channel in ("PostToolUse", "SubagentStop"):
            agent_id = f"word{channel}"
            messages = {}
            for level in ACTIONABLE_LEVELS:
                self._derived_agent_transcript(self.crossing(level), agent_id)
                out = json.loads(
                    self.run_hook(channel, self.below(ADVISORY), agent_id=agent_id)
                )
                messages[level] = (
                    out["reason"] if channel == "SubagentStop"
                    else out["hookSpecificOutput"]["additionalContext"]
                )
            for level, text in messages.items():
                with self.subTest(channel=channel, level=LEVEL_NAMES[level]):
                    self.assertIn(announcement(level), text)
                    self.assertIn("reasoning", text.lower())      # advisory kept
                    self.assertIn("per your pause protocol", text)  # instruction
                    self.assertIn("record your state", text)
                    self.assertNotIn("/handover", text)
                    self.assertNotIn("operating instructions", text.lower())
            with self.subTest(channel=channel, level="escalation"):
                self.assertEscalates(messages)
            if channel == "SubagentStop":
                for text in messages.values():
                    self.assertIn("forced", text)  # turn-end note kept

    def test_agent_scoped_advisory_checkpoint_carries_no_instruction(self):
        # Spec 5.1 wording: the sub-actionable checkpoint carries no
        # instruction in either scope. Regression pin (green before and
        # after this change): red evidence came from temporarily adding an
        # advisory entry to INSTRUCTIONS[SCOPE_AGENT], not from a code path
        # exercised by default.
        self._derived_agent_transcript(self.crossing(ADVISORY), "adv111")
        out = json.loads(
            self.run_hook("PostToolUse", self.below(ADVISORY), agent_id="adv111")
        )
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn(announcement(ADVISORY), ctx)
        self.assertNotIn("pause protocol", ctx)
        self.assertNotIn("/handover", ctx)

    # --- malformed-input hardening: graceful recovery, exit 0, one stderr
    # --- breadcrumb naming what was malformed (visible under claude --debug)

    def test_non_dict_state_file_recovers_fresh_and_warns(self):
        self._write_state_file(json.dumps([1, 2, 3]))
        proc = self.run_hook_proc(
            self._payload("Stop", self._transcript(self.crossing(WRAP_UP)))
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])
        self.assertIn("state file", proc.stderr)

    def test_non_numeric_usage_field_counts_zero_and_warns(self):
        transcript = self._transcript_lines(self._usage_entry({
            "input_tokens": "lots",  # malformed -> counts as 0
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": self.crossing(WRAP_UP),
            "output_tokens": 0,
        }))
        proc = self.run_hook_proc(self._payload("Stop", transcript))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        # The numeric fields alone still cross the wrap-up checkpoint.
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])
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
                "input_tokens": self.crossing(WRAP_UP),
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            }),
        )
        proc = self.run_hook_proc(self._payload("Stop", transcript))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])
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
        # Parent transcript past the wrap-up checkpoint: degrading must still
        # not fall back to measuring the parent (same rule as the
        # missing-field test above).
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "SubagentStop",
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(self.crossing(WRAP_UP))),
            "agent_id": "aaa111",
            "agent_transcript_path": {"path": "agent-aaa111.jsonl"},
        }))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("agent_transcript_path", proc.stderr)

    def test_non_string_session_id_falls_back_with_warning(self):
        # Below every checkpoint: the pin is exit 0 + breadcrumb (no crash),
        # not output. The state identity degrades to "default" (absent-field
        # rule), which only malformed payloads ever use.
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "Stop",
            "session_id": 42,
            "transcript_path": str(self._transcript(self.below(ADVISORY))),
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
            "transcript_path": str(self._transcript(self.crossing(WRAP_UP))),
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
        agent_t = self._agent_transcript(self.crossing(WRAP_UP), agent_id="ccc333")
        proc = self.run_hook_proc(json.dumps({
            "hook_event_name": "SubagentStop",
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(self.below(ADVISORY))),
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
                "input_tokens": self.crossing(WRAP_UP),
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "output_tokens": 0,
            }),
        )
        proc = self.run_hook_proc(self._payload("Stop", transcript))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout.strip())
        self.assertEqual(out["decision"], "block")
        self.assertIn(announcement(WRAP_UP), out["reason"])
        self.assertIn("transcript", proc.stderr)

    def test_placeholder_entries_are_not_measured(self):
        # Spec 2026-09-20 section 8: an entry whose model is "<synthetic>",
        # or whose four token fields are all zero, is a harness placeholder
        # and not an API response. The hook measures the latest REAL
        # response, so a trailing placeholder must not silence the warning.
        placeholder = {
            "type": "assistant",
            "message": {
                "model": "<synthetic>",
                "usage": {
                    "input_tokens": 0,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 0,
                },
            },
        }
        zero_usage = {
            "type": "assistant",
            "message": {"model": "claude-opus-5", "usage": self._usage(0)},
        }
        tokens = self.crossing(WRAP_UP)
        for case, trailing in (
            ("synthetic model", placeholder),
            ("all-zero usage", zero_usage),
        ):
            with self.subTest(case=case):
                self._fresh_identity(case.split()[0])
                transcript = self._transcript_lines(
                    json.dumps(self._main_entry(tokens, "claude-opus-5")),
                    json.dumps(trailing),
                )
                proc = self.run_hook_proc(self._payload("Stop", transcript))
                self.assertEqual(proc.returncode, 0, proc.stderr)
                out = json.loads(proc.stdout.strip())
                self.assertEqual(out["decision"], "block")
                self.assertIn(f"[{tokens:,} tokens used]", out["reason"])


class PerModelCheckpointTests(HookFixture):
    """Every model family is measured against its own row of the ladder.

    Promise source: docs/superpowers/specs/2026-09-20-per-model-context-
    checkpoints-design.md (ruled by Martin, 2026-09-20). §2 fixes the four
    checkpoint names and the wording per level, §3 the family detection rule
    and its defaults, §4 the announcement format.

    Per §9.5 no case below contains a threshold figure or a token count
    chosen because of one: every count is read from the shipped ladder and
    every expectation is a NAME, so moving a figure costs no edit here. Each
    case runs under its own session identity, so once-per-checkpoint state
    never leaks between families or cases.
    """

    # Spec §3: the family is the word after "claude-" in the model id, and two
    # words are aliases of another family's row - haiku takes sonnet's, mythos
    # takes fable's. Real model ids, so the id shape the hook parses is
    # exercised alongside the row it selects. These are names, not figures:
    # they do not move when a figure moves.
    MODEL_IDS = {
        "sonnet": ("claude-sonnet-5", "claude-haiku-4-5-20251001"),
        "opus": ("claude-opus-5",),
        "fable": ("claude-fable-5-1", "claude-mythos-5-1"),
    }

    def _family_models(self):
        """Every ladder row paired with each model id that must resolve to it."""
        self.assertEqual(
            sorted(self.MODEL_IDS),
            sorted(LADDER),
            "every ladder row needs at least one model id that reaches it",
        )
        return [
            (family, model)
            for family, models in self.MODEL_IDS.items()
            for model in models
        ]

    def _primary_model(self, family):
        """One id for a row, where the case is about the row rather than about
        which ids reach it."""
        return self.MODEL_IDS[family][0]

    @staticmethod
    def _rows_by_wrap_up():
        """Every pair of rows whose wrap-up figures differ, milder first. The
        ladder decides which pairs exist, so none is chosen by hand; rows that
        share a wrap-up figure yield no pair, there being no per-family
        difference left to observe between them."""
        for milder in LADDER:
            for severer in LADDER:
                if LADDER[milder][WRAP_UP] < LADDER[severer][WRAP_UP]:
                    yield milder, severer

    def test_the_advisory_checkpoint_is_informational_only_per_family(self):
        # Spec §2 level 0 and §4: ADVISORY is announced mid-turn naming the
        # family's own figure, carries no instruction, and never forces a
        # turn; below it nothing is announced at all.
        for family, model in self._family_models():
            with self.subTest(model=model, case="below the advisory"):
                self._fresh_identity(model, "below")
                self.assertEqual(
                    self.run_hook(
                        "UserPromptSubmit", self.below(ADVISORY, family), model=model
                    ),
                    "",
                )
            with self.subTest(model=model, case="advisory mid-turn"):
                self._fresh_identity(model, "adv")
                out = json.loads(
                    self.run_hook(
                        "UserPromptSubmit", self.inside(ADVISORY, family), model=model
                    )
                )
                ctx = out["hookSpecificOutput"]["additionalContext"]
                self.assertIn(announcement(ADVISORY, family), ctx)
                self.assertIn(f"The first {label(ADVISORY, family)} tokens", ctx)
                self.assertNotIn("/handover", ctx)
                self.assertNotIn("pause protocol", ctx)
            with self.subTest(model=model, case="advisory never blocks"):
                self._fresh_identity(model, "advstop")
                self.assertEqual(
                    self.run_hook("Stop", self.inside(ADVISORY, family), model=model),
                    "",
                )

    def test_actionable_checkpoints_escalate_per_family(self):
        # Spec §2 levels 1-3: inside each band of the family's own row the
        # turn end blocks, announcing that level's NAME with that level's
        # wording and the main-scope /handover instruction; below the
        # family's wrap-up nothing blocks.
        for family, model in self._family_models():
            with self.subTest(model=model, case="below wrap-up"):
                self._fresh_identity(model, "belowwrap")
                self.assertEqual(
                    self.run_hook("Stop", self.below(WRAP_UP, family), model=model),
                    "",
                )
            for level in ACTIONABLE_LEVELS:
                with self.subTest(model=model, level=LEVEL_NAMES[level]):
                    self._fresh_identity(model, LEVEL_NAMES[level])
                    out = json.loads(
                        self.run_hook("Stop", self.inside(level, family), model=model)
                    )
                    self.assertEqual(out["decision"], "block")
                    self.assertIn(announcement(level, family), out["reason"])
                    self.assertIn("/handover", out["reason"])
                    self.assertEscalates({level: out["reason"]})

    def test_each_family_stays_silent_below_its_own_wrap_up(self):
        # Spec §2 and §3: a family is read against its own row, so a count
        # that is actionable on another row - as every count above one single
        # set was before release 2.1.0 - announces nothing here until this
        # family's own wrap-up. The counts are the other rows' actionable
        # figures that fall short of this row's wrap-up, plus the count one
        # token below it, so every family has at least one case.
        for family in LADDER:
            model = self._primary_model(family)
            elsewhere = {
                LADDER[other][level]
                for other in LADDER
                if other != family
                for level in ACTIONABLE_LEVELS
            }
            silent_counts = {self.below(WRAP_UP, family)} | {
                tokens
                for tokens in elsewhere
                if tokens < self.crossing(WRAP_UP, family)
            }
            for tokens in sorted(silent_counts):
                with self.subTest(model=model, tokens=tokens):
                    self._fresh_identity(model, tokens)
                    self.assertEqual(self.run_hook("Stop", tokens, model=model), "")

    def test_unknown_or_absent_model_uses_the_default_family(self):
        # Spec §3: absent id -> the default family's row silently; unknown
        # family -> the default row with a breadcrumb naming the id;
        # non-string id -> treated as absent with the malformed-input
        # breadcrumb. `announcement` reads that same default row.
        tokens = self.inside(WRAP_UP)
        with self.subTest(case="absent"):
            self._fresh_identity("absent")
            out = json.loads(self.run_hook("Stop", tokens))
            self.assertIn(announcement(WRAP_UP), out["reason"])
        with self.subTest(case="unknown family"):
            self._fresh_identity("unknown")
            transcript = self._transcript(tokens, model="claude-zephyr-9")
            proc = self.run_hook_proc(self._payload("Stop", transcript))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out = json.loads(proc.stdout.strip())
            self.assertIn(announcement(WRAP_UP), out["reason"])
            self.assertIn("claude-zephyr-9", proc.stderr)
        with self.subTest(case="non-string"):
            self._fresh_identity("nonstring")
            transcript = self._transcript(tokens, model=42)
            proc = self.run_hook_proc(self._payload("Stop", transcript))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            out = json.loads(proc.stdout.strip())
            self.assertIn(announcement(WRAP_UP), out["reason"])
            self.assertIn("model", proc.stderr)

    def test_family_is_read_from_the_entry_that_supplies_the_usage(self):
        # Spec §3: the model id comes from the same latest assistant entry as
        # the usage figure, so a mid-session model switch is followed. Each
        # pair runs at the milder family's wrap-up count, which is actionable
        # there and silent on the severer row, so reading the model from the
        # earlier entry fails whichever way round the pair is written. The
        # earlier entry sits below its own family's advisory, so it has
        # nothing of its own to announce.
        for milder, severer in self._rows_by_wrap_up():
            tokens = self.crossing(WRAP_UP, milder)
            with self.subTest(last=severer, case="severer family last"):
                self._fresh_identity(milder, severer, "last-severer")
                transcript = self._transcript_lines(
                    json.dumps(
                        self._main_entry(
                            self.below(ADVISORY, milder), self._primary_model(milder)
                        )
                    ),
                    json.dumps(
                        self._main_entry(tokens, self._primary_model(severer))
                    ),
                )
                proc = self.run_hook_proc(self._payload("Stop", transcript))
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), "")
            with self.subTest(last=milder, case="milder family last"):
                self._fresh_identity(milder, severer, "last-milder")
                transcript = self._transcript_lines(
                    json.dumps(
                        self._main_entry(
                            self.below(ADVISORY, severer), self._primary_model(severer)
                        )
                    ),
                    json.dumps(
                        self._main_entry(tokens, self._primary_model(milder))
                    ),
                )
                proc = self.run_hook_proc(self._payload("Stop", transcript))
                self.assertEqual(proc.returncode, 0, proc.stderr)
                out = json.loads(proc.stdout.strip())
                self.assertIn(announcement(WRAP_UP, milder), out["reason"])

    def test_agent_scope_reads_the_agent_transcript_model(self):
        # Spec §3 with the scope rules of the 2026-06-06 spec §5.1: an agent
        # is measured on its own transcript, so the agent's own model id
        # picks the row and the main session's never does. Each pair runs
        # both ways round, so neither a swapped scope nor a coincidence can
        # pass: the count that blocks for the milder agent is silent on the
        # severer main row, and the count that is silent for the severer
        # agent would block on the milder main row.
        for milder, severer in self._rows_by_wrap_up():
            with self.subTest(agent=milder, main=severer, case="agent blocks"):
                self._fresh_identity(milder, severer, "agent-blocks")
                agent_path = self._agent_transcript(
                    self.inside(WRAP_UP, milder), "w1",
                    model=self._primary_model(milder),
                )
                out = json.loads(
                    self.run_hook(
                        "SubagentStop", self.below(ADVISORY, severer),
                        model=self._primary_model(severer),
                        agent_id="w1", agent_transcript_path=str(agent_path),
                    )
                )
                self.assertEqual(out["decision"], "block")
                self.assertIn(announcement(WRAP_UP, milder), out["reason"])
                self.assertIn("pause protocol", out["reason"])
                self.assertNotIn("/handover", out["reason"])
            with self.subTest(agent=severer, main=milder, case="agent silent"):
                self._fresh_identity(milder, severer, "agent-silent")
                agent_path = self._agent_transcript(
                    self.crossing(WRAP_UP, milder), "w2",
                    model=self._primary_model(severer),
                )
                self.assertEqual(
                    self.run_hook(
                        "SubagentStop", self.below(ADVISORY, milder),
                        model=self._primary_model(milder),
                        agent_id="w2", agent_transcript_path=str(agent_path),
                    ),
                    "",
                )


# Nothing announced yet on a channel. Level 0 is a real level, so zero cannot
# stand for "none" once the state file holds levels rather than figures.
LEVEL_NONE = -1

# The implication sentence the hook prints per level. This release does not
# touch them, so they are the LEVEL ORACLE here: a case fails for the
# announcement behaviour alone, never for the new wire format. The wire names
# are asserted by the message-composition tests instead.
LEVEL_IMPLICATIONS = (
    "highest-quality reasoning zone",
    "well past the peak-quality",
    "significantly degraded",
    "severely degraded",
)

# One generated family switch: the session announces in family_a at `tokens`,
# switches to family_b at the same usage, and the two levels are what each
# family's ladder row says that count crosses.
SwitchCase = namedtuple("SwitchCase", "family_a family_b level_a level_b tokens")


def top_level_crossed(figures, tokens):
    """The severest level a token count crosses in one ladder row, or
    LEVEL_NONE below the row's first figure."""
    crossed = [level for level, figure in enumerate(figures) if tokens >= figure]
    return crossed[-1] if crossed else LEVEL_NONE


def model_id(family):
    """A model id the hook resolves to this ladder row. Spec §3: the family is
    the word after "claude-", so the row name is the whole id that is needed."""
    return f"claude-{family}"


class NamedCheckpointTests(HookFixture):
    """Announcement and suppression keyed by the checkpoint's level.

    Promise source: docs/superpowers/specs/2026-09-20-per-model-context-
    checkpoints-design.md §9.2 (ruled by Martin, 2026-09-20):

      1. A checkpoint severer than the last one announced on a channel is
         announced on that channel, whatever its figure.
      2. A checkpoint no severer than the last one announced on a channel is
         never announced again on that channel, whatever its figure.

    and §9.4: a state file that does not say "version": 2 is ignored.

    Per §9.5 no case below contains a threshold figure or a token count chosen
    because of one. Every case is generated from the shipped ladder and every
    expectation is a level, so changing a figure costs no edit to this file.
    """

    # Step 2 arrives on both delivery channels. Mid-turn, the channel's own
    # once-per-checkpoint comparison decides; at turn end, the
    # already-delivered-mid-turn comparison decides. Both are keyed on the
    # checkpoint, so generating over the pair covers both without either
    # having to be singled out by hand.
    SECOND_STEP_EVENTS = ("UserPromptSubmit", "Stop")

    @staticmethod
    def _switch_cases():
        """Every family switch the ladder implies: each ordered pair of rows,
        crossed with each level of the second row, at the token count that
        crosses that level there. Usage is identical across the two steps, so
        the backwards-jump reset never fires."""
        for family_a, figures_a in LADDER.items():
            for family_b, figures_b in LADDER.items():
                if family_a == family_b:
                    continue
                for level_b, tokens in enumerate(figures_b):
                    yield SwitchCase(
                        family_a,
                        family_b,
                        top_level_crossed(figures_a, tokens),
                        level_b,
                        tokens,
                    )

    def _runnable_cases(self):
        """Each switch case crossed with the channel step 2 arrives on. A turn
        end never announces the advisory level (spec §2 level 0 never forces a
        turn), so those pairings are not cases."""
        for case in self._switch_cases():
            for event in self.SECOND_STEP_EVENTS:
                if event == "Stop" and case.level_b == ADVISORY:
                    continue
                yield case, event

    def _announced_level(self, output):
        """The level an announcement carries, read from its implication
        sentence. None when nothing was announced."""
        if not output:
            return None
        payload = json.loads(output)
        if "decision" in payload:
            self.assertEqual(payload["decision"], "block")
            text = payload["reason"]
        else:
            text = payload["hookSpecificOutput"]["additionalContext"]
        levels = [
            level
            for level, phrase in enumerate(LEVEL_IMPLICATIONS)
            if phrase in text
        ]
        self.assertEqual(len(levels), 1, f"no single level named in {text!r}")
        return levels[0]

    def _switch(self, case, second_event):
        """Announce in family A, then re-run at the same usage in family B.
        Returns the level family B's event announced, or None. The first step
        is asserted against family A's own row, so a case can never pass on a
        setup that quietly announced nothing."""
        self._fresh_identity(
            case.family_a, case.family_b, case.level_b, second_event
        )
        first = self._announced_level(
            self.run_hook(
                "UserPromptSubmit", case.tokens, model=model_id(case.family_a)
            )
        )
        self.assertEqual(
            first,
            None if case.level_a == LEVEL_NONE else case.level_a,
            "setup: the first family did not announce its own level",
        )
        return self._announced_level(
            self.run_hook(second_event, case.tokens, model=model_id(case.family_b))
        )

    def test_a_severer_checkpoint_is_announced_after_a_milder_one(self):
        # Spec §9.2 promise 1, over every generated case whose second crossing
        # is severer than its first.
        for case, event in self._runnable_cases():
            if case.level_b <= case.level_a:
                continue
            with self.subTest(case=case, channel=event):
                self.assertEqual(self._switch(case, event), case.level_b)

    def test_a_checkpoint_no_severer_than_the_last_is_never_re_announced(self):
        # Spec §9.2 promise 2, over every generated case whose second crossing
        # is no severer than its first. "No severer", not "milder": the
        # equal-level case is the one that is easy to write wrongly, and the
        # generator produces it without anyone having to choose it.
        for case, event in self._runnable_cases():
            if case.level_b > case.level_a:
                continue
            with self.subTest(case=case, channel=event):
                self.assertIsNone(self._switch(case, event))

    def test_a_state_file_without_version_2_is_ignored(self):
        # Spec §9.4: a state file that does not say "version": 2 is ignored -
        # fresh state, nothing carried over. Both pre-2.2.0 shapes are tried at
        # the severest level of every row, the one place a carried-over value
        # would silence the hook for the rest of the session.
        channel_keys = ("prompt", "tool", "stop", "subagent_stop")
        for family, figures in LADDER.items():
            severest, peak = len(figures) - 1, figures[-1]
            for shape, state in (
                ("channels", {key: peak for key in channel_keys}),
                ("last_announced", {"last_announced": peak}),
            ):
                with self.subTest(family=family, state=shape):
                    self._fresh_identity(family, shape)
                    self._write_state_file(json.dumps(state))
                    self.assertEqual(
                        self._announced_level(
                            self.run_hook(
                                "UserPromptSubmit", peak, model=model_id(family)
                            )
                        ),
                        severest,
                    )


class ShippedLadderTests(unittest.TestCase):
    """The shipped figure ladder is readable and complete.

    Promise source: the same spec, §9.5 - the ladder is the one source of the
    figures, and an unreadable or incomplete one is the failure mode this
    release introduces. Green by construction rather than red first: it guards
    a new artefact instead of changing behaviour.
    """

    # Spec §3 maps every model family onto one of these three rows (haiku takes
    # sonnet's, mythos takes fable's, an unreadable id takes opus's). These are
    # names, not figures: they do not move when a figure moves.
    LADDER_ROWS = ("sonnet", "opus", "fable")

    def test_the_shipped_ladder_file_parses_and_covers_every_family(self):
        ladder = read_ladder()
        self.assertEqual(sorted(ladder), sorted(self.LADDER_ROWS))
        for family, figures in ladder.items():
            with self.subTest(family=family):
                self.assertEqual(
                    len(figures), len(LEVEL_IMPLICATIONS), "one figure per level"
                )
                self.assertTrue(all(figure > 0 for figure in figures))
                self.assertEqual(list(figures), sorted(set(figures)), "figures ascend")


if __name__ == "__main__":
    unittest.main()
