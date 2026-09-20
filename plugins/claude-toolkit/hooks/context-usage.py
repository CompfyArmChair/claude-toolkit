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
  Stop               -> turn-end: for ACTIONABLE crossings (the model
                        family's wrap-up figure and above, see
                        Checkpoints below) returns
                        {"decision": "block", "reason": <context warning>},
                        forcing exactly one more turn so the warning reaches
                        the agent. The advisory crossing never blocks (never
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
implication for reasoning quality; the ACTIONABLE messages (levels 1-3)
additionally carry the baseline instruction, chosen by scope because the
hook knows whose context it measured and no agent should have to
translate "/handover":
  main scope  - wrap up and use /handover to continue in a fresh session
  agent scope - finish the step you are in, record your state, and end
                your turn per your pause protocol so a fresh agent can
                continue
escalating to "stop immediately" at levels 2-3, and at level 3 noting that
work quality may have been compromised. Agent-scoped messages never
contain "/handover"; main-scoped actionable messages always do. The
advisory checkpoint (level 0) stays advisory-only in both scopes. What
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

Turn-end addendum (2026-09-11): because the block is only a delivery
channel, it is skipped when an informational channel (the "prompt" or
"tool" state key) has already announced a checkpoint at least this severe
for the same identity - the warning was delivered, and forcing a turn would
deliver it twice, one wasted turn per controller pause. The block still
fires when neither informational channel announced it, which is exactly the
starved-loop case above, and for a SEVERER checkpoint than the one
announced. The 50 percent reset clears all keys together, so a compaction
re-arms both channels.

Loop safety: a blocked turn-end forces one more turn whose own Stop fires
with stop_hook_active=true - the hook exits immediately on that flag. The
once-per-threshold state prevents re-announcing the same threshold.

Checkpoints - per model family since 2026-09-20
(docs/superpowers/specs/2026-09-20-per-model-context-checkpoints-design.md,
ruled by Martin). Four levels, named on the wire since 2026-09-20 (spec
§9.3); the wording is per level, the figure per family:

  level 0 advisory   - informational only. Left the prime-thinking zone.
  level 1 wrap-up    - ACTIONABLE: also delivered via the turn-end block.
                       Instructs the scope's baseline (main: wrap up +
                       /handover; agent: finish the step, record state,
                       end the turn per the pause protocol).
  level 2 stop       - ACTIONABLE: as level 1, prefixed "stop immediately".
  level 3 stop,      - ACTIONABLE: as level 2, plus note that work quality
          compromised  may have been compromised.

The figures themselves live in exactly one artefact, context-checkpoints.txt
beside this file (spec §9.5, ruled by Martin: "I don't want to see the actual
threshold values anywhere other than in a single source of truth"). They are
deliberately absent from this docstring. An unreadable ladder breadcrumbs and
announces nothing: there is no fallback set, because the figures ARE the
ruling and guessing them would be worse than saying so loudly.

The family is the word after "claude-" in message.model of the same latest
assistant entry that supplies the usage, so a mid-session model switch and
an agent's own model are both followed. Haiku takes the Sonnet figures
(spec assumption). Absent model: Opus figures, silently. Unknown family:
Opus figures with a breadcrumb naming the id - a new family is transcript
drift worth surfacing. Non-string model: treated as absent, breadcrumbed.

Once per checkpoint, per channel, keyed by the checkpoint's LEVEL rather than
its figure (spec §9.2, 2026-09-20). A figure stopped identifying a checkpoint
when the figures became per-family, and the earlier figure-keyed state was
silently skipping announcements across a model switch. The two promises:
a checkpoint SEVERER than the last announced on a channel is announced,
whatever its figure; one NO SEVERER is never announced again on that channel,
whatever its figure.

State files (one JSON per measurement identity):
  main loop:  ~/.claude/hooks/state/context-usage-<session_id>.json
  per agent:  ~/.claude/hooks/state/
              context-usage-<session_id>--<agent_id>.json
  Shape: {"version": 2, "prompt": <level>, "tool": <level>, "stop": <level>,
          "subagent_stop": <level>, "peak_figure": <tokens>}
  Channel values are the LEVEL last announced there, or -1 for none (0 is a
  real level). peak_figure is the largest figure ever announced by this
  identity, kept only so the reset below still compares tokens.
  Files appear only on a first crossing, so accumulation is bounded to
  identities that actually cross.
  A file that does not declare version 2 is ignored outright - fresh state,
  nothing carried over (spec §9.4: only sessions alive at the instant of
  upgrade can hold one, and they end within hours).

Reset: if current usage falls below 50% of the largest figure this identity
ever announced (e.g. after /compact or /rewind), every channel resets - and
the reset is persisted immediately, so turn-end detection (which announces
nothing below the wrap-up figure that could piggyback persistence)
re-arms too.

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


def warn(message: str) -> None:
    """Debug breadcrumb for malformed input (exit code stays 0, so this is
    invisible in normal use and shows only under claude --debug)."""
    print(f"context-usage: {message}", file=sys.stderr)


SCOPE_MAIN = "main"
SCOPE_AGENT = "agent"

# Checkpoint levels (spec 2026-09-20 section 2). The wording is per level;
# the figure per model family. Every checkpoint message is: advisory (figure
# is prepended by main(); then "Context checkpoint <label> crossed" and the
# implication for reasoning quality), the turn-end note when the message
# is delivered by a forced turn, then the instruction chosen by SCOPE - the
# hook knows whose context it measured, and no agent should have to
# translate "/handover" into its own pause protocol. Level 0 carries no
# instruction in either scope: it is context, not a directive.
LEVEL_ADVISORY = 0
LEVEL_WRAP_UP = 1
LEVEL_STOP = 2
LEVEL_STOP_COMPROMISED = 3
LEVELS = (LEVEL_ADVISORY, LEVEL_WRAP_UP, LEVEL_STOP, LEVEL_STOP_COMPROMISED)
# Levels 1-3 carry the instruction, and turn-end events may block. Level 0
# is deliberately absent: never force a turn for an advisory checkpoint.
ACTIONABLE_LEVELS = (LEVEL_WRAP_UP, LEVEL_STOP, LEVEL_STOP_COMPROMISED)

# A checkpoint's NAME is its identity on the wire and in state (spec §9.3);
# its figure is context beside it. Uppercase, like the plugin's other
# machine-keyable keywords (WAITING / PAUSED / STOPPED / COMPLETE).
CHECKPOINT_NAMES = {
    LEVEL_ADVISORY: "ADVISORY",
    LEVEL_WRAP_UP: "WRAP-UP",
    LEVEL_STOP: "STOP",
    LEVEL_STOP_COMPROMISED: "STOP-COMPROMISED",
}

# The figure families (spec section 2). Opus is the default, keeping the
# pre-2026-09-20 behaviour for a transcript with no readable model id.
FAMILY_SONNET = "sonnet"
FAMILY_OPUS = "opus"
FAMILY_FABLE = "fable"
DEFAULT_FAMILY = FAMILY_OPUS

# The word after "claude-" in the model id names the family (spec section
# 3): matching that word, not the exact id, survives provider prefixes,
# dated suffixes and the "[1m]" suffix. Mythos shares Fable's figures; Haiku
# takes Sonnet's (spec section 3 assumption, flagged there).
MODEL_WORD = re.compile(r"claude-([a-z]+)")
FAMILY_BY_MODEL_WORD = {
    "sonnet": FAMILY_SONNET,
    "haiku": FAMILY_SONNET,
    "opus": FAMILY_OPUS,
    "fable": FAMILY_FABLE,
    "mythos": FAMILY_FABLE,
}

# The one source of the figures (spec §9.5), shipped beside this hook the way
# web-doctrine.md sits beside inject-web-doctrine.mjs.
LADDER_FILE = Path(__file__).resolve().parent / "context-checkpoints.txt"


def parse_ladder(path: Path) -> dict[str, tuple[int, ...]]:
    """One row per family, four ascending figures per row; "#" starts a
    comment. Deliberately trivial: the status line parses the same file with
    shell builtins, so the format has to stay readable to both."""
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("#", 1)[0].split()
        if fields:
            rows[fields[0]] = tuple(int(figure) for figure in fields[1:])
    return rows


def load_figures() -> dict[str, tuple[int, ...]]:
    """The ladder, or an empty mapping with a breadcrumb naming the file.
    There is no fallback set of figures: the figures ARE the ruling, so a
    guess would be worse than announcing nothing loudly. This is the one
    failure mode the ladder introduces, and the breadcrumb is what keeps it
    from becoming the silent starvation this hook exists to prevent."""
    try:
        rows = parse_ladder(LADDER_FILE)
        missing = set(FAMILY_BY_MODEL_WORD.values()) - set(rows)
        wrong_width = [f for f, figures in rows.items() if len(figures) != len(LEVELS)]
        if missing or wrong_width:
            raise ValueError(
                f"missing families {sorted(missing)}, "
                f"wrong width {sorted(wrong_width)}"
            )
    except Exception as exc:
        warn(
            f"cannot read the checkpoint figures from {LADDER_FILE} ({exc}) - "
            "this claude-toolkit install is broken and NO checkpoint can be "
            "announced until the file is restored"
        )
        return {}
    return rows


FIGURES_BY_FAMILY = load_figures()

IMPLICATIONS = {
    LEVEL_ADVISORY: (
        "The first {label} tokens - the highest-quality reasoning zone - are "
        "consumed."
    ),
    LEVEL_WRAP_UP: (
        "You are well past the peak-quality reasoning zone - recall of "
        "earlier context is less reliable and multi-step reasoning is more "
        "error-prone than at the start."
    ),
    LEVEL_STOP: (
        "Reasoning quality is significantly degraded - earlier context is "
        "increasingly likely to be missed, misremembered, or contradicted."
    ),
    LEVEL_STOP_COMPROMISED: (
        "Reasoning quality is severely degraded - expect dropped context, "
        "overlooked instructions, and inconsistent output."
    ),
}

INSTRUCTIONS = {
    SCOPE_MAIN: {
        LEVEL_WRAP_UP: (
            "Wrap up your current work and use /handover to continue in a "
            "fresh session."
        ),
        LEVEL_STOP: (
            "Stop immediately: wrap up and use /handover to continue in a "
            "fresh session."
        ),
        LEVEL_STOP_COMPROMISED: (
            "Stop immediately: wrap up and use /handover to continue in a "
            "fresh session, noting in the handover that work quality may "
            "have been compromised."
        ),
    },
    SCOPE_AGENT: {
        LEVEL_WRAP_UP: (
            "Finish the step you are in, record your state, and end your "
            "turn per your pause protocol so a fresh agent can continue."
        ),
        LEVEL_STOP: (
            "Stop immediately: finish the step you are in, record your "
            "state, and end your turn per your pause protocol so a fresh "
            "agent can continue."
        ),
        LEVEL_STOP_COMPROMISED: (
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


@dataclass(frozen=True)
class Checkpoint:
    """One crossing candidate: a level, the name that identifies it, and the
    family's figure for it."""

    level: int
    figure: int

    @property
    def name(self) -> str:
        return CHECKPOINT_NAMES[self.level]

    @property
    def label(self) -> str:
        return f"{self.figure // 1000}k"


def figure_family(model: object) -> str:
    """The figure family for a transcript's model id (spec section 3).
    Absent -> default silently (absent fields are normal shape). Non-string
    -> treated as absent with the malformed-input breadcrumb. Unknown family
    word -> default with a breadcrumb naming the id: a new family is the
    transcript drift this hook's breadcrumbs exist to surface."""
    if model is None:
        return DEFAULT_FAMILY
    if not isinstance(model, str):
        warn("non-string transcript field 'model' treated as absent")
        return DEFAULT_FAMILY
    match = MODEL_WORD.search(model)
    family = FAMILY_BY_MODEL_WORD.get(match.group(1)) if match else None
    if family is None:
        warn(f"unknown model family in {model!r} - using the {DEFAULT_FAMILY} figures")
        return DEFAULT_FAMILY
    return family


def checkpoints_for(family: str, turn_end: bool) -> tuple[Checkpoint, ...]:
    """The family's checkpoints this event may announce, ascending."""
    figures = FIGURES_BY_FAMILY[family]
    levels = ACTIONABLE_LEVELS if turn_end else LEVELS
    return tuple(Checkpoint(level, figures[level]) for level in levels)


def checkpoint_message(checkpoint: Checkpoint, scope: str, turn_end: bool) -> str:
    detection = " (turn-end detection)" if turn_end else ""
    implication = IMPLICATIONS[checkpoint.level].format(label=checkpoint.label)
    parts = [
        f"Context checkpoint {checkpoint.name} crossed at {checkpoint.label}"
        f"{detection}. {implication}"
    ]
    if turn_end:
        parts.append(TURN_END_NOTE)
    instruction = INSTRUCTIONS[scope].get(checkpoint.level)
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
STATE_KEY_VERSION = "version"
STATE_KEY_PEAK_FIGURE = "peak_figure"
STATE_VERSION = 2
# Nothing announced yet on a channel. Level 0 is a real level (ADVISORY), so
# zero cannot stand for "none" now that channels hold levels (spec §9.4).
LEVEL_NONE = -1
STORABLE_LEVELS = (LEVEL_NONE, *LEVELS)


@dataclass
class State:
    """What one measurement identity has announced (spec §9.4). A dataclass
    rather than a bare dict so a level and the one figure cannot be confused,
    and so serialisation is written out field by field - the comprehension it
    replaces silently dropped every key outside STATE_KEYS."""

    levels: dict[str, int]
    peak_figure: int

    @classmethod
    def fresh(cls) -> "State":
        return cls({key: LEVEL_NONE for key in STATE_KEYS}, 0)

    def record(self, key: str, checkpoint: Checkpoint) -> None:
        """Remember that this channel announced this checkpoint."""
        self.levels[key] = checkpoint.level
        self.peak_figure = max(self.peak_figure, checkpoint.figure)

    def as_dict(self) -> dict:
        """The flat on-disk shape, which stays the documented file contract."""
        return {
            STATE_KEY_VERSION: STATE_VERSION,
            **self.levels,
            STATE_KEY_PEAK_FIGURE: self.peak_figure,
        }

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


# The four flat usage fields that make up a context measurement. When a
# usage object carries an "iterations" array these flat fields hold the LAST
# iteration's figures, which is what we want; the nested "cache_creation"
# object can disagree with them on a model-refusal fallback turn, so it is
# never read (spec 2026-09-20 section 8).
USAGE_FIELDS = (
    "input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
)

# The harness writes placeholder assistant entries - "No response requested.",
# a session-limit notice - under this model name, always with all four token
# fields zero. They are not API responses and carry no measurement.
SYNTHETIC_MODEL = "<synthetic>"


def is_placeholder(message: dict) -> bool:
    """True for a harness placeholder rather than a real API response (spec
    2026-09-20 section 8): the synthetic model, or a usage object whose four
    token fields are all zero or absent. Measuring one reads zero and
    silently stops the warnings for the rest of the session - observed as the
    last entry in 14 of 617 main transcripts."""
    if message.get("model") == SYNTHETIC_MODEL:
        return True
    usage = message["usage"]
    return not any(
        isinstance(usage.get(field), (int, float)) and usage.get(field)
        for field in USAGE_FIELDS
    )


def total_tokens(usage: dict) -> int:
    total = 0
    non_numeric = []
    for field in USAGE_FIELDS:
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


def stored_level(value: object, key: str) -> int:
    """A channel value read back from disk. Anything that is not a storable
    level becomes LEVEL_NONE with a breadcrumb, following this module's
    malformed-input doctrine: harmless (a repeated warning), never a missed
    one."""
    if isinstance(value, (int, float)) and value in STORABLE_LEVELS:
        return int(value)
    warn(f"state key {key!r} holds {value!r}, not a checkpoint level - "
         "treated as nothing announced")
    return LEVEL_NONE


def load_state(state_id: str) -> State:
    """The identity's record, or fresh state. A file that does not declare
    version 2 is ignored outright - no migration (spec §9.4)."""
    try:
        data = json.loads(state_path(state_id).read_text(encoding="utf-8"))
    except Exception:
        return State.fresh()
    if not isinstance(data, dict):
        warn("malformed state file (not a JSON object) - using fresh state")
        return State.fresh()
    if data.get(STATE_KEY_VERSION) != STATE_VERSION:
        return State.fresh()
    peak = data.get(STATE_KEY_PEAK_FIGURE)
    return State(
        {key: stored_level(data.get(key), key) for key in STATE_KEYS},
        int(peak) if isinstance(peak, (int, float)) and peak > 0 else 0,
    )


def save_state(state_id: str, state: State) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_path(state_id).write_text(
            json.dumps(state.as_dict()), encoding="utf-8"
        )
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


def latest_assistant_message(
    transcript: Path, include_sidechain: bool = False
) -> dict | None:
    """Latest assistant message dict that is a real API response. The usage
    figure and the model id are both read from this one entry (spec
    2026-09-20 section 3); harness placeholders are skipped so a trailing one
    cannot silence the hook (section 8). Sidechain entries are skipped unless
    include_sidechain (agent transcripts are wholly sidechain-flagged, so
    the filter would blind the read there)."""
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
                if isinstance(msg.get("usage"), dict) and not is_placeholder(msg):
                    latest = msg
    except Exception:
        return None
    if malformed:
        warn(f"skipped {malformed} malformed transcript line(s)")
    return latest


def highest_crossing(
    checkpoints: tuple[Checkpoint, ...], current: int, announced_level: int
) -> Checkpoint | None:
    """The highest checkpoint this usage has crossed, if it is severer than
    what this state key already announced (spec §9.2), else None. Whether a
    checkpoint is CROSSED is a token comparison and stays one; only whether
    it has already been ANNOUNCED moves to levels."""
    crossed = [c for c in checkpoints if current >= c.figure]
    if not crossed:
        return None
    top = crossed[-1]
    return None if top.level <= announced_level else top


def informational_already_announced(state: State, level: int) -> bool:
    """Turn-end addendum (spec 5.1, 2026-09-11): the block is only a delivery
    channel. If the prompt or tool channel already delivered a checkpoint at
    least this severe to this identity mid-turn, forcing a turn would deliver
    it twice and cost the agent a wasted turn per pause."""
    return max(state.levels[STATE_KEY_PROMPT], state.levels[STATE_KEY_TOOL]) >= level


def main() -> int:
    if not FIGURES_BY_FAMILY:
        return 0  # load_figures() has already breadcrumbed why
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

    message = latest_assistant_message(
        target.transcript, include_sidechain=target.include_sidechain
    )
    if not message:
        return 0

    current = total_tokens(message["usage"])
    family = figure_family(message.get("model"))
    state = load_state(target.state_id)

    # Reset on significant backwards jump (compact, rewind, fresh transcript).
    # Persist immediately: the turn-end path announces nothing below the
    # family's wrap-up figure, so without persistence a post-compact session
    # would stay silenced. The comparison is against the largest FIGURE this
    # identity ever announced - a token measurement, not a level.
    if state.peak_figure > 0 and current < state.peak_figure * RESET_RATIO:
        state = State.fresh()
        save_state(target.state_id, state)

    key = EVENT_STATE_KEYS.get(event_name, STATE_KEY_PROMPT)
    crossing = highest_crossing(
        checkpoints_for(family, turn_end), current, state.levels[key]
    )
    if crossing is None:
        return 0

    if turn_end and informational_already_announced(state, crossing.level):
        return 0

    state.record(key, crossing)
    save_state(target.state_id, state)

    warning = checkpoint_message(crossing, target.scope, turn_end)
    full_msg = f"[{current:,} tokens used] {warning}"
    if turn_end:
        print(json.dumps({"decision": "block", "reason": full_msg}))
    else:
        print(emit_for(event_name, full_msg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
