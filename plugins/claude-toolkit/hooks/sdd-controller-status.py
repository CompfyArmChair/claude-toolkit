#!/usr/bin/env python3
"""SubagentStop status-line guard for the claude-toolkit:sdd-controller agent.

The driver (/implement-from-plan) branches on the controller's final
message, so the status line is enforced by the harness rather than
promised by the prompt (spec 5.3). Registered in hooks.json under
SubagentStop with the anchored matcher ^claude-toolkit:sdd-controller$ -
SubagentStop matchers take the agent type, plugin agents use the scoped
id, and ":" forces the regex path, hence the anchors (R:73).

Grammar (spec 6): the final message, after leading whitespace, starts with
one of WAITING, PAUSED, STOPPED, COMPLETE (case-sensitive) as a whole
keyword - followed by ":", whitespace, or the end of the message. Anything
else is blocked with a reason telling the controller to re-issue its
status. WAITING (2.0.1) is the line the controller ends a dispatch turn
with so the worker's completion notification can re-invoke it; the driver
never branches on it.

Loop safety: the forced turn's own SubagentStop arrives with
stop_hook_active=true and always passes - at most one forced retry, never
a loop. A second non-status reply reaches the driver, which asks the human.

Malformed payloads (non-JSON, non-object, missing or non-string
last_assistant_message) exit 0 silently, as the context-usage hook does.
The context-usage hook runs on the same event, unmatched; each decides
independently.
"""

import json
import re
import sys

STATUS_LINE = re.compile(r"^\s*(WAITING|PAUSED|STOPPED|COMPLETE)(?::|\s|$)")
BLOCK_REASON = (
    "Your final message must be a status line: WAITING: <what for> | "
    "PAUSED: <ledger last line> | STOPPED: <question> | COMPLETE <report>. "
    "Re-issue your status now."
)


def is_status_line(message: str) -> bool:
    return STATUS_LINE.match(message) is not None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    if payload.get("stop_hook_active"):
        return 0
    message = payload.get("last_assistant_message")
    if not isinstance(message, str):
        return 0
    if is_status_line(message):
        return 0
    print(json.dumps({"decision": "block", "reason": BLOCK_REASON}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
