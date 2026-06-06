#!/usr/bin/env python3
"""Context-window checkpoint hook (UserPromptSubmit, PostToolUse, Stop, SubagentStop).

Reads the active transcript, computes current main-thread context usage, and
announces a checkpoint crossing exactly once per session, per event type:

  UserPromptSubmit -> informational: injects additionalContext into the
                      assistant's view at the start of each turn
  PostToolUse      -> informational: injects additionalContext mid-turn,
                      immediately after the next tool call following a
                      crossing - so the assistant can adapt mid-task
  Stop             -> turn-end: for ACTIONABLE crossings (>= 200k) returns
                      {"decision": "block", "reason": <context warning>},
                      forcing exactly one more turn so the warning reaches
                      the agent. Sub-actionable crossings never block (never
                      force a turn for information).
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

Sensor, not policy (de-engineered in 1.5.4): every message reports the
figure and the threshold, then defers to the agent's own operating
instructions. What a crossing REQUIRES (e.g. the or-* tiers'
handover-at-200k rule) is policy and lives in the agent manuals (F10 keeps
it there); duplicating it in the hook's wording proved to be scope creep.

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
  200,000  - ACTIONABLE: also delivered via the turn-end block.
  250,000  - ACTIONABLE: 50k past the 200k checkpoint.
  300,000  - ACTIONABLE: 100k past the 200k checkpoint.

State files (one JSON per measurement identity):
  main loop:  ~/.claude/hooks/state/context-usage-<session_id>.json
  per agent:  ~/.claude/hooks/state/
              context-usage-<session_id>--<agent_id>.json
  Shape: {"prompt": <t>, "tool": <t>, "stop": <t>, "subagent_stop": <t>}
  (an agent file only ever accrues "subagent_stop" in practice). Files
  appear only on a first actionable crossing, so accumulation is bounded
  to agents that actually cross.
  Legacy field "last_announced" migrates to "prompt" on first read.

Reset: if current usage falls below 50% of any previously announced threshold
(e.g. after /compact or /rewind), all tracked thresholds reset - and the
reset is persisted immediately, so turn-end detection (which announces
nothing below 200k that could piggyback persistence) re-arms too.

Accepted residual (teammate-scoped design, 2026-06-06): teammate-originated
PostToolUse - and user prompts typed in a teammate's pane (UserPromptSubmit)
- carry no agent identifier (binary-verified), so the informational paths
remain parent-scoped: a teammate may see mid-turn announces describing the
MANAGER's context, and such a crossing consumes the parent's prompt/tool
once-per-threshold keys (possibly suppressing one manager informational
announce). The authoritative per-agent signal is the turn-end SubagentStop
block above, which IS agent-scoped.

Accepted residual (per-wake re-warning, Spike 9 2026-06-06): the harness
assigns every teammate WAKE a fresh agent_id and a fresh wake transcript,
so per-agent once-per-threshold state never carries across wakes - a
teammate that wakes still over an actionable threshold is re-warned (one
forced turn) at every wake until its context shrinks. Under sensor
semantics that is "one warning per wake while over-threshold" - accepted
delivery behavior, not a defect. Cross-wake identity engineering (payload
introspection for a wake-stable key, transcript lineage) was considered
and rejected as over-engineering.

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
from pathlib import Path

# Informational wording (additionalContext on UserPromptSubmit/PostToolUse).
# Sensor language only: report the figure and the threshold, then defer to
# the agent's own operating instructions. What crossing a threshold REQUIRES
# (e.g. the or-* tiers' handover-at-200k rule, F10) is policy and lives in
# the agent manuals - never here.
CHECKPOINTS = [
    (
        100_000,
        "Context checkpoint 100k crossed. The first 100k tokens - the "
        "highest-quality reasoning zone - are consumed.",
    ),
    (
        200_000,
        "Context checkpoint 200k crossed. Consult your operating "
        "instructions for how to handle this context warning.",
    ),
    (
        250_000,
        "Context checkpoint 250k crossed - 50k past the 200k checkpoint. "
        "Consult your operating instructions for how to handle this context "
        "warning.",
    ),
    (
        300_000,
        "Context checkpoint 300k crossed - 100k past the 200k checkpoint. "
        "Consult your operating instructions for how to handle this context "
        "warning.",
    ),
]

# Turn-end wording (decision:block on Stop/SubagentStop). The block is a
# DELIVERY channel, not enforcement: in inbox-driven loops only turn-end
# events fire reliably (F20/F22), and additionalContext is discarded there,
# so forcing one extra turn is the only way the warning reaches the agent.
# The message explains the forced turn mechanically and defers, like every
# checkpoint, to the agent's operating instructions. 100k is deliberately
# absent: never force a turn for a sub-actionable checkpoint.
ACTIONABLE_CHECKPOINTS = [
    (
        200_000,
        "Context checkpoint 200k crossed (turn-end detection). This turn "
        "was forced so the warning could reach you. Consult your operating "
        "instructions for how to handle this context warning.",
    ),
    (
        250_000,
        "Context checkpoint 250k crossed (turn-end detection) - 50k past "
        "the 200k checkpoint. This turn was forced so the warning could "
        "reach you. Consult your operating instructions for how to handle "
        "this context warning.",
    ),
    (
        300_000,
        "Context checkpoint 300k crossed (turn-end detection) - 100k past "
        "the 200k checkpoint. This turn was forced so the warning could "
        "reach you. Consult your operating instructions for how to handle "
        "this context warning.",
    ),
]

STATE_DIR = Path.home() / ".claude" / "hooks" / "state"
SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]")
RESET_RATIO = 0.5

EVENT_PROMPT = "UserPromptSubmit"
EVENT_TOOL = "PostToolUse"
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

EVENT_STATE_KEYS = {
    EVENT_PROMPT: STATE_KEY_PROMPT,
    EVENT_TOOL: STATE_KEY_TOOL,
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


def measurement_target(payload: dict, event_name: str) -> tuple[str, str, bool] | None:
    """Resolve whose context this event measures: (transcript path, state
    identity, include_sidechain). Payload fields are read via str_field:
    a non-string value is malformed input, warned and treated as absent.

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
    session_id = str_field(payload, "session_id") or "default"
    if event_name != EVENT_SUBAGENT_STOP:
        transcript_path = str_field(payload, "transcript_path")
        if not transcript_path:
            return None
        return transcript_path, session_id, False
    transcript_path = str_field(payload, "agent_transcript_path") or str_field(
        payload, "subagent_transcript_path"
    )
    if not transcript_path:
        warn(
            "SubagentStop payload missing agent_transcript_path/"
            "subagent_transcript_path - skipping (cannot measure the "
            "agent's own context)"
        )
        return None
    agent_id = str_field(payload, "agent_id") or Path(transcript_path).stem
    return transcript_path, f"{session_id}--{agent_id}", True


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


def highest_crossing(checkpoints, current, announced):
    """The highest checkpoint at/below current that exceeds what this event
    already announced, or None."""
    crossed = [(t, m) for (t, m) in checkpoints if current >= t]
    if not crossed:
        return None
    threshold, message = crossed[-1]
    if threshold <= announced:
        return None
    return threshold, message


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


if __name__ == "__main__":
    sys.exit(main())
