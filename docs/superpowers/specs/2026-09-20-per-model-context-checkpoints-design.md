# Per-model context checkpoints — design

**Date:** 2026-09-20
**Decided by:** Martin (this ruling supersedes the single fixed checkpoint set of 2026-05-31)
**Component:** `plugins/claude-toolkit/hooks/context-usage.py` (+ its tests, hooks.json description, README)
**Release:** claude-toolkit 2.0.1 → 2.1.0

## 1. Problem

The context-usage hook announces checkpoints at fixed absolute token counts
(100k advisory; 200k / 250k / 300k actionable) for every model. Those figures
were set for Opus. Fable/Mythos-class models hold far more usable context and
Sonnet-class models less, so one set of figures either interrupts Fable far
too early or lets Sonnet run far too deep.

## 2. Checkpoint figures per model family (the ruling)

Four levels, in order. The wording per level is unchanged from today; only
the figures move with the family.

| Level | Meaning | Sonnet | Opus | Fable / Mythos |
|---|---|---|---|---|
| 0 advisory | informational only, no instruction, never forces a turn | 75k | 100k | 200k |
| 1 wrap-up | main: wrap up + `/handover`; agent: finish the step, record state, end the turn per the pause protocol | 150k | 200k | 300k |
| 2 stop | as level 1, prefixed "Stop immediately" | 200k | 250k | 400k |
| 3 stop, compromised | as level 2, plus note that work quality may have been compromised | 250k | 300k | 450k |

Opus keeps today's figures exactly, so any transcript without a readable
model id behaves as before.

## 3. Family detection

- The family is read from `message.model` of the **same** latest assistant
  entry that supplies the usage figure (so a mid-session `/model` switch is
  followed as soon as the next assistant entry lands, and an agent's own
  transcript names the agent's own model).
- The family is the word after `claude-` in the model id (`claude-fable-5-1`
  → `fable`, `claude-mythos-5-1` → `mythos`, `claude-opus-5` → `opus`,
  `claude-sonnet-5` → `sonnet`, `claude-haiku-4-5-20251001` → `haiku`).
  Matching by that word, not by exact id, keeps provider prefixes, dated
  suffixes and the `[1m]` suffix from breaking detection.
- Mapping: `fable`, `mythos` → Fable figures; `opus` → Opus figures;
  `sonnet` → Sonnet figures.
- `haiku` → Sonnet figures. **Martin ruled Haiku out of scope on 2026-09-20
  ("Haiku is out of scope. I don't use Haiku"), so this mapping is a
  placeholder, not a considered figure set.** It exists so a Haiku
  transcript is classified rather than falling through to the Opus
  fallback. Note for whoever revisits it: Haiku 4.5's window is 200k, so
  under these figures the 200k and 250k checkpoints cannot fire.
- Absent model id → Opus figures, silently (absent fields are normal shape
  for old transcripts and the existing test fixtures).
- Unknown family word (a model family this hook does not know) → Opus figures
  **with a stderr breadcrumb naming the id**: a new family appearing is
  exactly the drift the hook's breadcrumbs exist to surface.
- Non-string model id → treated as absent, with the usual malformed-input
  breadcrumb.

## 4. Message composition

- Labels are derived from the figure (`75k`, `150k`, `200k`, ... `450k`).
- The level-0 advisory text names the family's own figure: "The first 200k
  tokens - the highest-quality reasoning zone - are consumed." on Fable.
- The `[N tokens used]` prefix, the turn-end note, the scope-chosen
  instructions and the escalation wording are unchanged.

## 5. Unchanged mechanics

Channels (prompt / tool / stop / subagent_stop), once-per-threshold state
keyed by the announced absolute figure, the 50% reset, the turn-end
block-skip when an informational channel already announced, and scope
resolution all stay as specified in
`2026-06-06-teammate-scoped-context-checkpoints-design.md`. State stores
absolute figures, so a family switch mid-session degrades gracefully: an
already-announced higher figure is never re-announced.

## 6. Status line (outside the plugin)

Martin's `~/.claude/statusline.sh` may show spacers at the family's figures
on the ctx bar. That script is personal configuration, not a plugin
component; it carries its own copy of the table in §2 with a comment naming
this spec as the source of truth.

## 7. Tests (promise citations)

Tests cite this spec by section. §2 fixes the figures per family and the
wording per level; §3 the detection rule and defaults; §4 the labels and
the advisory text.

## 8. Measurement hygiene: placeholder entries are not measured

Research on 2026-09-20 (3,038 transcripts, 66,882 assistant usage entries on
this machine; deposits under
`C:\Users\marti\.claude\projects\C--Users-marti--claude\memory\.claude\web-deposits\`)
found 153 assistant entries whose model is `<synthetic>`, every one of them
with all four token fields zero. They are harness placeholders, such as
"No response requested." or a session-limit notice, not API responses. In 14
of 617 main transcripts the **last** assistant entry is one of these, so a
hook measuring the last entry reads zero and silently stops warning for the
rest of the session.

The hook therefore measures the latest assistant entry that is a real API
response: an entry whose model is `<synthetic>`, or whose four token fields
are all zero or absent, is skipped and the search continues backwards. A
transcript of nothing but placeholders measures nothing, as before.

Two related findings from the same research, already satisfied and recorded
so they are not re-litigated:

- Consecutive transcript lines repeat one logical response with an identical
  usage object. The hook takes the latest entry and never sums across
  entries, so it is unaffected. Summing across entries yields the billing
  total (one session: 4,925,692 tokens against a true context of 230,090).
- When a usage object carries an `iterations` array, the top-level flat
  token fields equal the **last** iteration, not the sum, and the nested
  `cache_creation` object can disagree with the flat field on a model-refusal
  fallback turn. The hook reads only the flat fields, which is correct.
