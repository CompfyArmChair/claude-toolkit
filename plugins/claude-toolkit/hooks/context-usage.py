#!/usr/bin/env python3
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
  200,000  - ACTIONABLE: also delivered via the turn-end block. Instructs
             the scope's baseline (main: wrap up + /handover; agent:
             finish the step, record state, end the turn per the pause
             protocol).
  250,000  - ACTIONABLE: as 200k, prefixed "stop immediately".
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

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCOPE_MAIN = "main"
SCOPE_AGENT = "agent"

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


STATE_DIR = Path.home() / ".claude" / "hooks" / "state"
SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]")
RESET_RATIO = 0.5

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


def warn(message: str) -> None:
    """Debug breadcrumb for malformed input (exit code stays 0, so this is
    invisible in normal use and shows only under claude --debug)."""
    print(f"context-usage: {message}", file=sys.stderr)


def str_field(payload: dict, field: str) -> str | None:
    """A payload field that must be a string to be usable (transcript paths
    feed Path(), session_id feeds the state filename, hook_event_name keys
    EVENT_STATE_KEYS). A non-string value is malformed input: warned and
    treated as absent, like every other malformed-input path."""
    value = payload.get(field)
    if value is None or isinstance(value, str):
        return value or None
    warn(f"non-string payload field {field!r} treated as absent")
    return None


def total_tokens(usage: dict) -> int:
    total = 0
    non_numeric = []
    for field in (
        "input_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "output_tokens",
    ):
        value = usage.get(field)
        if isinstance(value, (int, float)):
            total += value
        elif value is not None:  # absent fields are normal; wrong types are not
            non_numeric.append(field)
    if non_numeric:
        warn(f"non-numeric usage field(s) counted as 0: {', '.join(non_numeric)}")
    return int(total)


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


def emit_for(event_name: str, message: str) -> str:
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name or EVENT_PROMPT,
            "additionalContext": message,
        }
    })


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


def highest_crossing(thresholds, current, announced) -> int | None:
    """The highest threshold at/below current that exceeds what this state
    key already announced, or None."""
    crossed = [t for t in thresholds if current >= t]
    if not crossed:
        return None
    threshold = crossed[-1]
    return None if threshold <= announced else threshold


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        warn("malformed stdin payload (not a JSON object) - ignoring event")
        return 0

    event_name = str_field(payload, "hook_event_name") or EVENT_PROMPT
    turn_end = event_name in TURN_END_EVENTS

    # Loop guard: a blocked turn-end forced one extra turn; that turn's own
    # Stop/SubagentStop arrives with stop_hook_active=true. Never block it
    # again.
    if turn_end and payload.get("stop_hook_active"):
        return 0

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

    # Reset on significant backwards jump (compact, rewind, fresh transcript).
    # Persist immediately: the turn-end path announces nothing below 200k, so
    # without persistence a post-compact session would stay silenced.
    max_tracked = max(state[k] for k in STATE_KEYS)
    if max_tracked > 0 and current < max_tracked * RESET_RATIO:
        for k in STATE_KEYS:
            state[k] = 0
        save_state(target.state_id, state)

    key = EVENT_STATE_KEYS.get(event_name, STATE_KEY_PROMPT)
    thresholds = ACTIONABLE_CHECKPOINTS if turn_end else CHECKPOINTS
    threshold = highest_crossing(thresholds, current, state[key])
    if threshold is None:
        return 0

    state[key] = threshold
    save_state(target.state_id, state)

    message = checkpoint_message(threshold, target.scope, turn_end)
    full_msg = f"[{current:,} tokens used] {message}"
    if turn_end:
        print(json.dumps({"decision": "block", "reason": full_msg}))
    else:
        print(emit_for(event_name, full_msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
