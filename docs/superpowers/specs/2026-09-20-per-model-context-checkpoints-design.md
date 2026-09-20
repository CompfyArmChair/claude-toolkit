# Per-model context checkpoints — design

**Date:** 2026-09-20
**Decided by:** Martin (this ruling supersedes the single fixed checkpoint set of 2026-05-31)
**Component:** `plugins/claude-toolkit/hooks/context-usage.py` and `plugins/claude-toolkit/hooks/context-checkpoints.txt` (+ its tests, hooks.json description, README, and Martin's `~/.claude/statusline.sh`)
**Release:** claude-toolkit 2.0.1 → 2.1.0; then 2.1.0 → 2.2.0 for §9

## 1. Problem

The context-usage hook announced checkpoints at one fixed set of absolute
token counts for every model. Those figures were set for Opus. Fable/Mythos-class models hold far more usable context and
Sonnet-class models less, so one set of figures either interrupts Fable far
too early or lets Sonnet run far too deep.

## 2. Checkpoint figures per model family (the ruling)

Four levels, in order. The wording per level is unchanged from today; only
the figures move with the family.

| Level | Name | Meaning |
|---|---|---|
| 0 | `ADVISORY` | informational only, no instruction, never forces a turn |
| 1 | `WRAP-UP` | main: wrap up + `/handover`; agent: finish the step, record state, end the turn per the pause protocol |
| 2 | `STOP` | as level 1, prefixed "Stop immediately" |
| 3 | `STOP-COMPROMISED` | as level 2, plus note that work quality may have been compromised |

**The figures themselves are not written here.** Under the ruling in §9 they
live in exactly one artefact,
`plugins/claude-toolkit/hooks/context-checkpoints.txt`, which is normative:
one row per family, four ascending figures per row. This section previously
carried a table of them; §9.5 removed it.

Opus keeps the pre-2.1.0 figures exactly, so any transcript without a readable
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
  fallback. Note for whoever revisits it: Haiku 4.5's window is 200k tokens,
  which the upper checkpoints of the Sonnet row sit at or above, so those
  checkpoints are unreachable on Haiku in practice.
- Absent model id → Opus figures, silently (absent fields are normal shape
  for old transcripts and the existing test fixtures).
- Unknown family word (a model family this hook does not know) → Opus figures
  **with a stderr breadcrumb naming the id**: a new family appearing is
  exactly the drift the hook's breadcrumbs exist to surface.
- Non-string model id → treated as absent, with the usual malformed-input
  breadcrumb.

## 4. Message composition

- The first sentence names the checkpoint, then its figure:
  `Context checkpoint WRAP-UP crossed at <figure>k`. The name is the
  checkpoint's identity; the figure is context beside it (§9.3).
- `(turn-end detection)` stays adjacent to the figure.
- The level-0 advisory text names the family's own figure ("The first
  <figure>k tokens - the highest-quality reasoning zone - are consumed.").
- The `[N tokens used]` prefix, the turn-end note, the scope-chosen
  instructions and the escalation wording are unchanged.

## 5. Unchanged mechanics

Channels (prompt / tool / stop / subagent_stop), the 50% reset, the turn-end
block-skip when an informational channel already announced, and scope
resolution all stay as specified in
`2026-06-06-teammate-scoped-context-checkpoints-design.md`.

**Once-per-checkpoint state is keyed by the checkpoint's LEVEL, not its
figure** (§9.4). This section previously said the state was keyed by the
announced absolute figure, and that "State stores absolute figures, so a family
switch mid-session degrades gracefully: an already-announced higher figure is
never re-announced." **That claim was false, and was falsified by reproduction
on 2026-09-20:** because a figure alone does not identify a checkpoint once the
figures differ per family, a family switch could leave a channel permanently
silent while the session sat in the severest band. See §9.1.

## 6. Status line (outside the plugin)

Martin's `~/.claude/statusline.sh` colours its context bar by the checkpoint
zone the session is in. It is personal configuration, not a plugin component,
but it is a reader of the figures, so under §9.5 it holds no copy of them: it
resolves the installed plugin's directory from
`~/.claude/plugins/installed_plugins.json` and reads
`hooks/context-checkpoints.txt` with shell builtins. If either read fails it
renders raw consumption with no zone colouring — never a bar drawn from
guessed figures.

Zone *names* on the bar are out of scope; Martin ruled that separately.

## 7. Tests (promise citations)

Tests cite this spec by section. §2 fixes the four level names and the
wording per level; §3 the detection rule and defaults; §4 the message
composition; §9 the two announcement promises and the state contract.

Per Martin's ruling in §9.5, **no test asserts a figure.** Figures are fixture
inputs, read from `context-checkpoints.txt` at test time; what a test asserts
is the named logic. Changing a figure must require no test edit.

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

## 9. Named checkpoints and one source of truth (2026-09-20, release 2.2.0)

**Decided by:** Martin. *"We should have really used named checkpoints rather
than by value because these will change over time."*

### 9.1 Why

A checkpoint was identified by its figure, both on the wire and in the state
file that prevents repeat announcements. Once §2's figures became per-family a
figure no longer identified a checkpoint, and §5's "degrades gracefully" claim
was false: a session that announced a checkpoint on one family and then
switched to a family where the same token count is a *severer* checkpoint went
silent on that channel for the rest of the session — while sitting in the band
whose instruction is "stop immediately".

A second defect: consumers could not name what they react to. The
`sdd-controller` agent had to enumerate the actionable checkpoints by figure,
which went stale the moment the figures became per-family.

### 9.2 The two promises

1. **A checkpoint severer than the last one announced on a channel is
   announced on that channel, whatever its figure.**
2. **A checkpoint no severer than the last one announced on a channel is never
   announced again on that channel, whatever its figure.**

"No severer than", not "milder than": the equal-level case is the one that is
easy to write wrongly. Both promises are stated in levels, so they hold across
any family switch.

**Accepted cost, named at ruling time.** Promise 2 removes warnings that fire
today. After a switch to a family with larger figures, a level already
announced is not announced again under its new, larger number. A level is never
*missed* — each still fires once per channel — but a re-warn can be deferred by
a long stretch of tokens. Re-warning on a family change would reintroduce
exactly the figure-driven noise this ruling removes, and is not part of it.

### 9.3 Wire format

Name first, uppercase: `ADVISORY`, `WRAP-UP`, `STOP`, `STOP-COMPROMISED` — the
§2 level names, uppercased. The plugin already uses uppercase keywords as
machine-keyable tokens (`WAITING` / `PAUSED` / `STOPPED` / `COMPLETE`). The
first sentence becomes `Context checkpoint <NAME> crossed at <figure>k`.

**The hyphen in `WRAP-UP` is load-bearing and must not be "tidied" to a
space.** Tests prove the level-1 *instruction* is present by matching "wrap up"
with a space. `WRAP-UP` lowercases to `wrap-up`, which does not contain that,
so those assertions keep testing the instruction. `WRAP UP` would make them
pass on the name alone, silently, even if the instruction were deleted.

### 9.4 State file, version 2

Shape: `{"version": 2, "prompt": <level>, "tool": <level>, "stop": <level>,
"subagent_stop": <level>, "peak_figure": <tokens>}`.

- Channel values are the announced **level**. `0` is a real level
  (`ADVISORY`), so "nothing announced yet" is `-1`.
- `peak_figure` is the largest figure announced in this identity's life. It
  exists only so the 50% reset of §5 keeps working, and it is exactly the
  previous `max_tracked`, so reset behaviour does not move. It is runtime
  state, not a configured threshold, so §9.5 does not reach it.
- **No migration.** A state file that does not say `"version": 2` is ignored —
  fresh state, nothing carried over. Martin: *"Why are we dealing with legacy
  values? Once all current sessions end, legacy values aren't a consideration.
  Legacy sessions will end within moments."* A state file is only ever reopened
  by the identity that wrote it, so only sessions alive at the instant of
  upgrade can be affected, and they end within hours. The older
  `last_announced` migration is deleted for the same reason.

### 9.5 One source of truth for the figures

Martin: *"I don't want to see the actual threshold values anywhere other than
in a single source of truth. No exceptions."*

`plugins/claude-toolkit/hooks/context-checkpoints.txt` is that source: one row
per family, four ascending figures per row. Its readers are the hook, the tests
and the status line (§6), each parsing it independently. Everything else — this
spec, the hook docstring, `README.md`, `hooks.json`, the agent instructions —
names checkpoints and never figures.

Plain text rather than JSON, so the status line reads it with shell builtins
and no extra process. Family aliasing stays in code, per §3: Haiku takes
Sonnet's row, Mythos takes Fable's, an unreadable id takes Opus's.

**What the rule governs.** Live artefacts: the ones a reader consults to learn
the current figures, and the ones that must change when a figure changes. Dated
plans, specs and validation notes record what was true when they were written
and are not edited. Martin ruled this on 2026-09-20 when he left the 2026-09-11
spec and plan's stale figures standing as a shipped record.

**What tests may do.** Martin, on this release: *"We can't hard code the values
for the tests because if the values change, so do the tests. We're interested
in testing the logic of the NAMED values, not the values themselves."* So no
test contains a threshold figure, and no test contains a token count chosen
because of one. Every token input is computed from the ladder at test time;
every expectation is a name. Changing a figure must cost zero test edits.

**The failure mode this introduces, and its guard.** The hook can now fail to
read its figures. It must never fail the way this hook exists to prevent —
silently never firing again (§8 is the same class of defect). An unreadable,
empty or unparseable ladder produces a stderr breadcrumb naming the file and
saying the install is broken, and a test asserts that the shipped file parses
and covers every family §3 maps to.
