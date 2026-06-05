#!/usr/bin/env python3
"""Context-window checkpoint hook (UserPromptSubmit, PostToolUse, Stop, SubagentStop).

Reads the active transcript, computes current main-thread context usage, and
announces a checkpoint crossing exactly once per session, per event type:

  UserPromptSubmit -> informational: injects additionalContext into the
                      assistant's view at the start of each turn
  PostToolUse      -> informational: injects additionalContext mid-turn,
                      immediately after the next tool call following a
                      crossing - so the assistant can adapt mid-task
  Stop             -> turn-end: for ACTIONABLE crossings (>= 200k, the
                      handover threshold) returns {"decision": "block",
                      "reason": <handover instruction>}, forcing exactly one
                      more turn - the handover turn. Sub-threshold crossings
                      never block (never force a turn for information).
  SubagentStop     -> turn-end: same as Stop, for subagent / background-
                      teammate sessions.

Why turn-end events (E2E findings F20/F22): in inbox-driven team loops both
UserPromptSubmit and PostToolUse are starved - teammate-inbox deliveries
trigger neither - so a tier can blow past its handover threshold with zero
announcements. Stop/SubagentStop fire reliably at turn end in those loops,
but they fire AFTER the assistant's response, so additionalContext has no
in-progress turn to land in; the block path is the only delivery that works
there, and it is reserved for actionable crossings.

Loop safety: a blocked turn-end forces one more turn whose own Stop fires
with stop_hook_active=true - the hook exits immediately on that flag. The
once-per-threshold state prevents re-announcing the same threshold.

Checkpoints (cumulative tokens):
  100,000  - informational only. Left the 0-100k prime-thinking zone.
  200,000  - ACTIONABLE: handover threshold crossed.
  250,000  - ACTIONABLE: 50k past the handover threshold.
  300,000  - ACTIONABLE: past useful context.

State file (one JSON per session_id):
  ~/.claude/hooks/state/context-usage-<session_id>.json
  Shape: {"prompt": <t>, "tool": <t>, "stop": <t>, "subagent_stop": <t>}
  Legacy field "last_announced" migrates to "prompt" on first read.

Reset: if current usage falls below 50% of any previously announced threshold
(e.g. after /compact or /rewind), all tracked thresholds reset - and the
reset is persisted immediately, so turn-end detection (which announces
nothing below 200k that could piggyback persistence) re-arms too.
"""

import json
import re
import sys
from pathlib import Path

# Informational wording (additionalContext on UserPromptSubmit/PostToolUse).
# The >=200k entries are action-toned: the handover is mandatory the moment
# the threshold is crossed (manager playbook, F10), so even the informational
# path must not suggest waiting for a better moment.
CHECKPOINTS = [
    (
        100_000,
        "Context checkpoint 100k crossed. You've consumed the first 100k - "
        "your prime thinking real-estate. The next 100k is still high-quality. "
        "No action needed yet, but be aware.",
    ),
    (
        200_000,
        "Context checkpoint 200k crossed. You are AT the handover threshold: "
        "execute your tier's handover protocol now (write your handover/"
        "iteration doc and emit your handover signal). The handover is "
        "mandatory - do not wait for a natural stopping point.",
    ),
    (
        250_000,
        "Context checkpoint 250k crossed. You are 50k PAST the handover "
        "threshold and quality is dropping. Stop taking new work and execute "
        "your handover protocol immediately.",
    ),
    (
        300_000,
        "Context checkpoint 300k crossed. You are far past useful context. "
        "Hand over NOW - write your handover/iteration doc and stop.",
    ),
]

# Turn-end wording (decision:block on Stop/SubagentStop). These force the
# handover turn, so they instruct - never merely inform. 100k is deliberately
# absent: never force a turn for non-actionable information.
ACTIONABLE_CHECKPOINTS = [
    (
        200_000,
        "Context checkpoint 200k crossed (turn-end detection). You are at "
        "your handover threshold. This extra turn exists so you can hand "
        "over: before taking ANY new work, execute your tier's handover "
        "protocol now - write your handover/iteration doc and emit your "
        "handover signal per your operating manual. If you have no handover "
        "protocol, wrap up and recommend a fresh session.",
    ),
    (
        250_000,
        "Context checkpoint 250k crossed (turn-end detection). You are 50k "
        "past your handover threshold and quality is dropping. STOP taking "
        "new work and execute your handover protocol immediately.",
    ),
    (
        300_000,
        "Context checkpoint 300k crossed (turn-end detection). You are far "
        "past useful context. Hand over NOW - write your handover/iteration "
        "doc and stop.",
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


def total_tokens(usage: dict) -> int:
    return (
        (usage.get("input_tokens") or 0)
        + (usage.get("cache_creation_input_tokens") or 0)
        + (usage.get("cache_read_input_tokens") or 0)
        + (usage.get("output_tokens") or 0)
    )


def state_path(session_id: str) -> Path:
    safe = SAFE_ID.sub("_", session_id)[:128] or "default"
    return STATE_DIR / f"context-usage-{safe}.json"


def load_state(session_id: str) -> dict:
    try:
        data = json.loads(state_path(session_id).read_text(encoding="utf-8"))
    except Exception:
        return {k: 0 for k in STATE_KEYS}
    # Migrate legacy single-event state.
    if "last_announced" in data and STATE_KEY_PROMPT not in data:
        data[STATE_KEY_PROMPT] = data["last_announced"]
    for k in STATE_KEYS:
        data.setdefault(k, 0)
        v = data.get(k)
        data[k] = int(v) if isinstance(v, (int, float)) else 0
    return data


def save_state(session_id: str, state: dict) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        out = {k: int(state.get(k, 0)) for k in STATE_KEYS}
        state_path(session_id).write_text(json.dumps(out), encoding="utf-8")
    except Exception:
        pass


def emit_for(event_name: str, message: str) -> str:
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": event_name or EVENT_PROMPT,
            "additionalContext": message,
        }
    })


def latest_main_thread_usage(transcript: Path) -> dict | None:
    latest = None
    try:
        with transcript.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if entry.get("type") != "assistant":
                    continue
                if entry.get("isSidechain"):
                    continue
                msg = entry.get("message") or {}
                usage = msg.get("usage")
                if isinstance(usage, dict):
                    latest = usage
    except Exception:
        return None
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

    event_name = payload.get("hook_event_name") or EVENT_PROMPT
    turn_end = event_name in TURN_END_EVENTS

    # Loop guard: a blocked turn-end forced one extra turn; that turn's own
    # Stop/SubagentStop arrives with stop_hook_active=true. Never block it
    # again.
    if turn_end and payload.get("stop_hook_active"):
        return 0

    session_id = payload.get("session_id") or "default"
    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        return 0
    p = Path(transcript_path)
    if not p.exists():
        return 0

    usage = latest_main_thread_usage(p)
    if not usage:
        return 0

    current = total_tokens(usage)
    state = load_state(session_id)

    # Reset on significant backwards jump (compact, rewind, fresh transcript).
    # Persist immediately: the turn-end path announces nothing below 200k, so
    # without persistence a post-compact session would stay silenced.
    max_tracked = max(state[k] for k in STATE_KEYS)
    if max_tracked > 0 and current < max_tracked * RESET_RATIO:
        for k in STATE_KEYS:
            state[k] = 0
        save_state(session_id, state)

    key = EVENT_STATE_KEYS.get(event_name, STATE_KEY_PROMPT)
    checkpoints = ACTIONABLE_CHECKPOINTS if turn_end else CHECKPOINTS
    crossing = highest_crossing(checkpoints, current, state[key])
    if crossing is None:
        return 0
    threshold, message = crossing

    state[key] = threshold
    save_state(session_id, state)

    full_msg = f"[{current:,} tokens used] {message}"
    if turn_end:
        print(json.dumps({"decision": "block", "reason": full_msg}))
    else:
        print(emit_for(event_name, full_msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
