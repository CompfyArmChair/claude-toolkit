# Design — Teammate-Scoped Context Checkpoints (SubagentStop self-measurement)

**Date:** 2026-06-06
**Status:** Approved (brainstorming dialogue, this date)
**Branch:** `teammate-scoped-checkpoints` (off `master` = `26717c5`, plugin 1.5.1)
**Origin:** Spike 8 facet-3 finding (`docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`, RESULT block) — the one open follow-up from the or-sas E2E remediation cycle (F20/F22 → 1.5.0/1.5.1).

## Problem

The 1.5.x turn-end detection (`plugins/claude-toolkit/hooks/context-usage.py`) delivers to
teammates but measures the wrong context. On `SubagentStop`:

- `transcript_path` in the payload is the **parent session's main transcript** (binary-confirmed:
  the payload constructor builds it from the same shared base as `Stop`'s), so the hook computes
  the **manager's** usage, never the teammate's own.
- `session_id` is the **parent's**, so the manager and all teammates share one
  once-per-threshold pool per event type. Observed live (Spike 8): a teammate's PostToolUse 200k
  announce consumed the `tool` key and suppressed the manager's own mid-turn announce.
- Consequence one: a teammate gets the handover block when the *manager* crosses a threshold,
  never on its own context — supervisor/phase-agent SELF-detection is not delivered by 1.5.1.
- Consequence two: once the main session is ≥200k, the next one-shot subagent completion (any
  SDD worker, any researcher) eats a spurious handover block measuring the manager's context —
  pure noise, one wasted turn, on every long session, or-sas or not.

## Evidence (exploration, 2026-06-06 — no live probe needed)

1. **Installed binary payload schema** (recovered from `claude.exe`, zod schema + constructor):
   `SubagentStop` input = common fields + `hook_event_name`, `stop_hook_active: boolean`,
   `agent_id: string`, `agent_transcript_path: string` (built per agent id), `agent_type: string`,
   `last_assistant_message?`. Current docs name the transcript field `subagent_transcript_path` —
   **naming drift between docs and installed binary is already real**, so the fix accepts both.
2. **Agent transcript shape** (verified on 11 real files across two sessions, incl. the three
   Spike-8 `s8-bloater` incarnations): `<project>/<session-id>/subagents/agent-<id>.jsonl`; every
   entry has `isSidechain: true` and `agentId` == the filename's id; assistant entries carry
   normal `usage` dicts; zero foreign-agent entries. The bloaters' real own usage
   (246k/228k/245k) vs the parent-scoped figures the hook reported corroborates Spike 8 exactly.
3. **PostToolUse payload carries no agent identifier** (binary-verified constructor:
   `tool_name, tool_input, tool_response, tool_use_id, duration_ms` + common fields). A
   teammate-originated informational event is structurally indistinguishable at the hook.
   The runtime knows the `agentId` internally but does not pass it.

## Goal

A `SubagentStop` crossing measures the **agent's own transcript** and enforces the **agent's own
handover**, under a **per-agent state identity**. The manager's pools are untouched by teammate
events. One-shot subagents stop receiving spurious end-of-run blocks.

**Non-goals:** fixing the informational paths (see Residual limitations); any or-* agent/skill
body changes (hook-only); threshold or wording changes; state-file cleanup mechanisms.

## Design

### Core change: measurement-target resolution (approach B, chosen over inline branching)

One new pure function in `context-usage.py` is the single decision point for *whose context is
measured, under which state identity, with which entry filter*:

```
measurement_target(payload) -> (transcript_path, state_id, include_sidechain) | None
```

| Event | transcript | state identity | sidechain entries |
|---|---|---|---|
| UserPromptSubmit / PostToolUse / Stop | `transcript_path` (unchanged) | `session_id` (unchanged) | excluded (unchanged) |
| SubagentStop | `agent_transcript_path`, else `subagent_transcript_path` | `session_id + "--" + agent_id` (if `agent_id` is absent: the transcript filename stem, e.g. `agent-a197e3402dd2bcffb`) | **included** |

- The installed-binary field name is tried first, the docs name second (covers the rename in
  either direction). If neither is present: return `None` → the hook exits 0 with no output, bar
  one stderr breadcrumb (see Degradation) — **never** fall back to the parent's
  `transcript_path`, since mis-scoped measurement *is* the bug.
- `include_sidechain=True` for agent transcripts because they are 100% `isSidechain: true`; the
  filter stays in force for main transcripts, where it guards against the historical
  inline-sidechain format. Implementation: the transcript reader
  (`latest_main_thread_usage`) gains an `include_sidechain` parameter.
- `main()` consumes the tuple. Everything downstream — checkpoint tables, once-per-threshold,
  reset-on-compaction, the `stop_hook_active` loop guard (binary schema confirms the field on
  SubagentStop), save-only-on-crossing — is untouched and becomes per-agent purely via the state
  identity.

### Behavior that falls out automatically

- **Per-agent threshold pools.** Teammate turn-end events never touch the parent's state file;
  the Spike-8 `subagent_stop`/`tool`-style cross-suppression on the turn-end path is gone.
- **Reset works for teammate auto-compaction.** A ≥50% usage drop inside the agent's own state
  file triggers the existing reset logic.
- **Re-spawned teammate incarnation** = new `agent_id` = fresh pool — matching its genuinely
  fresh context.
- **One-shot subagents** are measured on their own (usually sub-200k) usage → the spurious
  end-of-run block disappears. A one-shot that genuinely crosses 200k gets one wrap-up turn —
  uniform with teammates. The payload cannot distinguish kinds, and uniform is also the right
  semantics: the ACTIONABLE wording already covers agents without a handover protocol ("wrap up
  and recommend a fresh session").

### Degradation (graceful + loud, per the 1.5.1 hardening precedent `131806c`)

- `SubagentStop` payload with no agent-transcript field (future rename): **skip + one stderr
  breadcrumb** naming the missing field. Rationale: the natural symptom — teammate detection
  silently dead — is exactly the F20/F22 starvation class this hook exists to fix; the breadcrumb
  makes it diagnosable under `claude --debug` while exit code stays 0.
- Agent transcript path nonexistent / unreadable / empty of usage: existing silent-skip paths
  (`p.exists()`, `if not usage`) cover it unchanged.

### Residual limitations (accepted + documented — user decision this date)

Teammate-originated **PostToolUse** (and user prompts typed in a teammate's pane →
**UserPromptSubmit**) remain parent-scoped: those payloads carry no agent identifier
(binary-verified), so nothing actionable exists hook-side. Consequences, accepted:

1. A teammate may see mid-turn informational announces describing the **manager's** context.
2. A teammate-originated informational crossing still consumes the parent's `prompt`/`tool`
   once-per-threshold keys, possibly suppressing one manager informational announce.

The authoritative per-agent signal is the turn-end block, which this design fixes. The residual
is recorded in the hook docstring.

### State lifecycle

- Agent state files: `context-usage-<session_id>--<agent_id>.json` — the composite id passes
  through the existing `SAFE_ID` sanitizer + 128-char cap (~55 chars in practice).
- Same 4-key shape as session files — uniform load/save, no special-casing; in practice only
  `subagent_stop` is ever written in an agent file.
- Files are created only on a first actionable crossing (existing save-only-on-announce
  behavior), so accumulation is bounded to agents that actually cross — rare, consistent with
  the existing per-session no-cleanup precedent.

## Files touched

| File | Change |
|---|---|
| `plugins/claude-toolkit/hooks/context-usage.py` | `measurement_target()`; `include_sidechain` parameter on the transcript reader; docstring scoping section incl. the accepted residual |
| `plugins/claude-toolkit/hooks/hooks.json` | description string only (SubagentStop measures the subagent's own transcript); no registration changes |
| `tests/hooks/test_context_usage.py` | new TDD cases below |
| `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` | author **Spike 9** (below) |
| `plugins/claude-toolkit/plugin.json` + marketplace manifests | version **1.5.2** (patch: bugfix of the 1.5.0 detection feature, semver + 1.4.x precedent) |
| or-* agent/skill bodies | **expected zero changes**; a plan task greps the plugin for 200k/handover-threshold/context-usage references and confirms no wording promises per-agent scoping semantics that need a touch |

## Testing (TDD, stdlib unittest, extends the existing 15)

1. SubagentStop + `agent_transcript_path` → block computed from the **agent** transcript
   (all-sidechain entries counted), not the parent's.
2. `subagent_transcript_path` alias accepted.
3. Neither field present → exit 0, no output, parent state untouched, stderr breadcrumb.
4. Spike-8 collision regression: a teammate crossing writes only the agent-scoped state file;
   the manager's subsequent own crossing still announces.
5. Two agents cross independently (separate pools).
6. Main-transcript sidechain filter still excludes sidechain entries (regression).
7. `stop_hook_active` on SubagentStop → silent exit.
8. Reset on a compaction-scale drop within an agent's own state file.
9. Agent transcript path nonexistent → silent skip.

## Verification — Spike 9 (authored now, executed at cutover)

**Spike 9 — teammate-scoped turn-end detection.** Run against the installed 1.5.2 after release
(prior pattern: install + restart + record RESULT inline in the spikes doc). GREEN =

- a teammate that bloats its own context past 200k while the manager stays low is blocked with
  its **own** figure;
- the manager's pools are untouched by the teammate's crossing;
- a manager crossing does **not** block teammates;
- a one-shot subagent completing on a ≥200k session shows **no** spurious block;
- `stop_hook_active` guard + once-per-threshold hold **per agent**.

## Release mechanics

Branch `teammate-scoped-checkpoints` off `master`; first commit = the previously-uncommitted
Spike-8 RESULT edits (`fbeb7af`, user's recorded decision to commit them with this follow-up).
Then: this spec → plan (`/plan-from-design`) → TDD implementation → 1.5.2 release commit →
`claude plugin validate` plugin + marketplace (+ `--strict`, expected GREEN since `ad895f7`) →
approval-gated finishing (no push without explicit user choice) → cutover: install + restart +
run Spike 9 and record its RESULT inline.

## Decision log

| Decision | Choice | Why |
|---|---|---|
| Informational-path residual | Accept + document | No agent identifier in those payloads (binary-verified); heuristics risk silencing the manager's real announces |
| Implementation shape | B — `measurement_target()` resolution | The scoping decision lives in one named, unit-testable seam — the property whose absence let the bug hide |
| Missing-field degradation | Silent skip + stderr breadcrumb | Parent fallback *is* the bug; breadcrumb per 1.5.1 graceful+loud precedent |
| Pre-implementation live payload probe | Skipped | The installed binary's zod schema + constructor answer the payload question authoritatively; Spike 9 verifies end-to-end at cutover |
| Version | 1.5.2 (patch) | Bugfix of the 1.5.0 detection feature; semver + repo precedent (1.4.1/1.4.2) |
