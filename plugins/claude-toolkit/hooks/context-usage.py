#!/usr/bin/env python3
"""Context-window checkpoint hook (UserPromptSubmit + PostToolUse).

Reads the active transcript, computes current main-thread context usage, and
announces a checkpoint crossing exactly once per session, per event type:

  UserPromptSubmit -> injects additionalContext into the assistant's view
                      at the start of each turn
  PostToolUse      -> injects additionalContext into the assistant's view
                      mid-turn, immediately after the next tool call following
                      a crossing - so the assistant can adapt strategy mid-task

Each event tracks its own state so a single crossing announces once per
audience (mid-turn-self, next-turn-self), rather than the first event
silencing the other. Non-blocking: never blocks a prompt or tool.

Checkpoints (cumulative tokens):
  100,000  - Left the 0-100k prime-thinking zone.
  200,000  - Left the 100-200k high-quality zone; performance starts dropping.
  250,000  - Entering 250-300k, the last of useful context.
  300,000  - Past useful context. Recommend handover or /compact.

State file (one JSON per session_id):
  ~/.claude/hooks/state/context-usage-<session_id>.json
  Shape: {"prompt": <threshold>, "tool": <threshold>}
  Legacy field "last_announced" migrates to "prompt" on first read.

Reset: if current usage falls below 50% of any previously announced threshold
(e.g. after /compact or /rewind), all tracked thresholds reset so future
crossings re-announce.
"""

import json
import re
import sys
from pathlib import Path

CHECKPOINTS = [
    (
        100_000,
        "Context checkpoint 100k crossed. You've consumed the first 100k - "
        "your prime thinking real-estate. The next 100k is still high-quality. "
        "No action needed yet, but be aware.",
    ),
    (
        200_000,
        "Context checkpoint 200k crossed. You're now in the 200k-250k zone "
        "where performance starts dropping significantly. Trim tool output, "
        "prefer subagents for large reads, and start planning a natural "
        "handover point.",
    ),
    (
        250_000,
        "Context checkpoint 250k crossed. From here to 300k is the last of "
        "your useful context. Wrap up the current line of work or hand over "
        "now.",
    ),
    (
        300_000,
        "Context checkpoint 300k crossed. You're past the useful range - "
        "quality is degrading. Strongly recommend handover or /compact before "
        "any new work.",
    ),
]

STATE_DIR = Path.home() / ".claude" / "hooks" / "state"
SAFE_ID = re.compile(r"[^A-Za-z0-9_.-]")
RESET_RATIO = 0.5

EVENT_PROMPT = "UserPromptSubmit"
EVENT_TOOL = "PostToolUse"
STATE_KEY_PROMPT = "prompt"
STATE_KEY_TOOL = "tool"
STATE_KEYS = (STATE_KEY_PROMPT, STATE_KEY_TOOL)


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


def state_key_for(event_name: str) -> str:
    if event_name == EVENT_TOOL:
        return STATE_KEY_TOOL
    return STATE_KEY_PROMPT


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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    event_name = payload.get("hook_event_name") or EVENT_PROMPT
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

    crossed = [(t, m) for (t, m) in CHECKPOINTS if current >= t]
    if not crossed:
        return 0
    highest_threshold, highest_message = crossed[-1]

    state = load_state(session_id)

    # Reset on significant backwards jump (compact, rewind, fresh transcript).
    max_tracked = max(state[k] for k in STATE_KEYS)
    if max_tracked > 0 and current < max_tracked * RESET_RATIO:
        for k in STATE_KEYS:
            state[k] = 0

    key = state_key_for(event_name)
    if highest_threshold <= state[key]:
        return 0

    state[key] = highest_threshold
    save_state(session_id, state)

    full_msg = f"[{current:,} tokens used] {highest_message}"
    print(emit_for(event_name, full_msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
