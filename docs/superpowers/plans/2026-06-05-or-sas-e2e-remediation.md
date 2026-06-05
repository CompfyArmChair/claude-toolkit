# `or-superpowers-at-scale` — E2E-Run Remediation (F1–F28) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The agent-body / playbook / SKILL.md authoring tasks are also governed by **superpowers:writing-skills** — load it before authoring. The hook tasks (1–2) are governed by **superpowers:test-driven-development**. The final integration task is governed by **superpowers:finishing-a-development-branch**.

**Goal:** Land the remediation of the 28 findings (F1–F28) from the first true end-to-end run of the `claude-toolkit:or-superpowers-at-scale` orchestrator — headline: turn-end (`Stop`/`SubagentStop`) threshold detection in the context-checkpoint hook so the 200k handover actually fires under inbox-driven operation — shipping as plugin `1.4.2 → 1.5.0`.

**Architecture:** Three layers change. (1) **Hook layer:** `hooks.json` registers `context-usage.py` on `Stop` + `SubagentStop`; the script returns `{"decision":"block","reason":…}` for actionable (≥200k) crossings at turn-end — forcing exactly one more turn, the handover turn — while the 100k checkpoint stays informational on the existing events. (2) **Agent bodies + spawn-contexts (belt-and-suspenders, Principle 4):** the supervisor loses its parallel-review override (canonical SDD sequential gate + an explicit SPAWN/SHUTDOWN gate-close sequencing rule); all four worker bodies and both worker spawn-contexts gain report-to-SUPERVISOR directives; reviewer bodies become orchestration-only (criteria live in SDD's brief); phase agents ask in their own pane and the plan-writer owns the single plan-approval gate. (3) **Manager assets:** the playbook makes the 200k handover mandatory-and-automatic, removes Conservation Rule #8 (manager never originates teardown), adds the first-class `resume` mode, the roster delta-check, and zombie tolerance. One new behavioral spike (turn-end detection — the lone load-bearing unknown: manager main-loop `Stop` under inbox-wake) is authored now, executed at cutover.

**Tech Stack:** Claude Code plugin components in the `claude-toolkit` repo (`I:\Dev\claude-toolkit`, real git) — Markdown agent bodies / `SKILL.md` / `assets/*.md`, JSON manifests, one Python hook (stdlib only). New: a stdlib-`unittest` test file for the hook (repo-root `tests/`, NOT shipped in the plugin). In-session verification is **structural + hook-behavioral** (`claude plugin validate`, content greps, `python tests\hooks\test_context_usage.py`); all **team-behavioral** validation is deferred to cutover (Spike 8). One commit per task is the rollback boundary.

---

## Scope of this plan

Source design (authoritative): `docs/superpowers/specs/2026-06-03-or-sas-e2e-remediation-design.md`. This plan implements its Sections 2–7 under its six guiding principles (manager-purely-broker · simplicity-survives-degradation · detection-without-spam · root-cause-in-bodies-AND-spawn-contexts · detail-on-disk · orchestration-only). Findings doc (background): `docs/superpowers/validation/2026-06-03-or-sas-e2e-breakout-run-notes.md`.

**In scope (lands on the feature branch):**
- **Theme A — turn-end threshold detection (F20/F22/F10/F18):** `hooks.json` + `context-usage.py` + hook tests; playbook mandatory-auto-handover + idle-drift line; Spike 8 authored. (Tasks 1–4)
- **Theme B + Principle-6(a) — review-gate simplification (F8/F17/F14):** remove the parallel-review override → canonical SDD; gate-close SPAWN/SHUTDOWN sequencing rule; board re-assert workaround. (Task 5)
- **Theme C — worker I/O & report-trust (F7/F13/F19/F24/F26) + Principle-6(b):** supervisor DMs workers; report-to-supervisor in all 4 worker bodies + both spawn-contexts; implementer role-boundary + commit discipline; reviewer verdict self-evidence; reviewer bodies stripped to orchestration-only. (Tasks 5–8)
- **Theme D — manager purity (F25/F27/F4):** Conservation Rule #8 rewritten (never originate teardown); supervisor reaps implementer on gate-close; terse pointers; F4 documented. (Tasks 5, 12)
- **Theme E — phase-agent dialogue & flow (F2/F5/F6/F1):** ask-in-own-pane for brainstormer/plan-writer/finisher; plan-writer walkthrough+approval gate; auto-start on `PLAN_COMPLETE`; preflight one-question-at-a-time. (Tasks 9–11, 13, 16)
- **Theme F — handover/resume (F11/F21/F23/F28):** first-class `resume` mode; roster capture + names-only delta-check; the one sanctioned teardown; zombie tolerance. (Tasks 14–16)
- **Theme G — reviewer/plan accuracy (F15/F12):** supervisor source-verification at HEAD; decide-and-log (no new question channel). (Tasks 5, 12)
- **Principle-6 audit (a–d)** as named per-task checks + a final audit gate. (Tasks 5, 6, 9, 10, 18)
- **Release:** version bump `1.4.2 → 1.5.0` (×3), `claude plugin validate`, approval-gated finish. (Tasks 17–19)

**Out of scope:**
- **Execution of Spike 8** (turn-end detection — design §5). Authored in Task 3; **run at cutover against the installed 1.5.0 plugin**. Theme A's manager-side detection is **not "done"** until facet (1) — manager main-loop `Stop` under inbox-wake — is GREEN. Per the design's contingency note, the fallback is deliberately NOT designed here; `SubagentStop` detection for teammate tiers stands regardless (documented event).
- **Upstream suggestions (F15-reviewer-side, F16):** review-the-committed-artifact belongs to SDD's `spec-reviewer-prompt.md`; plan-artifact self-review hardening belongs to `writing-plans`. Both are suggestions for the superpowers plugin (not this repo); record nothing in our bodies (Principle 6). No task implements them.
- **Non-actionable findings (F3, F9):** no-ops per the design coverage table.
- **Leftover housekeeping (design Appendix):** stray `breakout-*.png` files, `breakout-game` branch/worktree/team, F23 `task12` zombie — NOT part of this plan. ⚠️ Because 3 stray `breakout-*.png` sit untracked at repo root, **never use `git add -A` / `git add .`** — every commit below adds explicit paths.

## Git workflow (READ FIRST)

`I:\Dev\claude-toolkit` is a real git repository. All work happens on the **existing** branch **`or-sas-e2e-remediation`** (already holds the findings doc + the approved design spec + this plan), **one commit per task**.

- Every git command targets the repo explicitly via `git -C I:\Dev\claude-toolkit …` — do not rely on ambient cwd, and do not `cd`.
- **Task 0 verifies the branch.** Tasks 1–17 commit locally only. **Do NOT `git push` until Task 19**, and only after explicit user approval (Task 19 runs `finishing-a-development-branch`).
- A worktree is **not** required (doc + small-script edits; the suite's prior plans worked the branch directly). If the executor prefers isolation, create one via `superpowers:using-git-worktrees` first; nothing below assumes one.
- Commit messages follow the repo convention (`fix(or-sas): …` / `feat(or-sas): …` / `docs(or-sas): …` / `test(or-sas): …` / `release: …` — see `git log`).

## Verification approach

The `claude-toolkit` marketplace plugin installed in the executing session is **1.4.2** — it does NOT contain these edits, so `Skill('claude-toolkit:or-superpowers-at-scale')` resolves the *old* assets and the `or-*` teammate behaviors cannot be exercised live. **Hard gates are therefore:**

1. **Hook behavior (real, in-session):** `python tests\hooks\test_context_usage.py -v` — the hook is a plain stdin→stdout script, fully testable without the harness (Task 2).
2. **Structural:** `claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit` + `claude plugin validate I:\Dev\claude-toolkit` (marketplace) — expect pass (note: `--strict` has 4 pre-existing unrelated command-frontmatter failures; not ours, do not fix here).
3. **Content greps (PowerShell `Select-String`):** expect-match / expect-no-match patterns per task. Checks are content-based, not line-number-based, so they survive edits that shift lines.

**Team-behavioral checks are deferred to Spike 8 at cutover** (manager `Stop` under inbox-wake, `decision:block` forcing the handover turn, `SubagentStop` per-teammate delivery, loop-guard).

## File structure (decomposition map)

| File | Disposition | Responsibility after this plan |
|------|-------------|--------------------------------|
| `plugins/claude-toolkit/hooks/hooks.json` | edit | Registers the checkpoint hook on `UserPromptSubmit`, `PostToolUse`, **`Stop`, `SubagentStop`**. |
| `plugins/claude-toolkit/hooks/context-usage.py` | edit | Informational `additionalContext` on prompt/tool events; **`decision:block` handover-forcing on turn-end events for ≥200k**; `stop_hook_active` loop guard; once-per-threshold per event; durable <50% reset. |
| `tests/hooks/test_context_usage.py` | **create** | stdlib-unittest behavioral tests for the hook (subprocess, real stdin/stdout contract). Repo-root `tests/` — NOT inside the plugin. |
| `…/skills/or-superpowers-at-scale/assets/manager-playbook.md` | edit (Tasks 4, 12, 13, 14 — consecutive by theme) | F10 mandatory auto-handover + forbidden inference; F18 idle-drift line; F25 pure-broker teardown rules; F4/F14 documented; F6 auto-start; F11 resume mode; F21 sanctioned teardown; F23 zombie tolerance; F28 delta-check; F12 decide-and-log. |
| `…/assets/manager-handover-template.md` | edit | F11 copy-pasteable resume invocation header; F28 canonical enumerated-roster capture. |
| `…/assets/preflight-brief.md` | edit | F1 one-question-per-turn sequencing (worktree → base → mode-if-ambiguous third). |
| `…/assets/implementer-spawn-context.md` | edit | F13 report-to-supervisor directive; F26 no-commit-before-brief directive. |
| `…/assets/reviewer-spawn-context.md` | edit | F13 report-to-supervisor directive; F24 verdict-protocol directive. |
| `…/assets/supervisor-spawn-context.md` | edit | F7 supervisor-DMs-workers / manager-never-proxies directive. |
| `…/skills/or-superpowers-at-scale/SKILL.md` | edit | F6 Phase-2 flow line (no manager gate); F11 `resume` invocation mode. |
| `agents/or-supervisor.md` | edit (single pass — B/C/D/G + P6a) | Canonical SDD (override removed); gate-close sequencing rule; board re-assert; DM-workers; implementer reap; HEAD source-verify; terse pointers; decide-and-log. |
| `agents/or-implementer.md` | edit | F13 report target; F19 role-boundary honesty; F26 commit discipline. |
| `agents/or-spec-reviewer.md`, `or-code-quality-reviewer.md`, `or-final-reviewer.md` | edit | Orchestration-only (criteria stripped — P6b); F13 report target; F24 verdict self-evidence. |
| `agents/or-brainstormer.md`, `or-finisher.md` | edit | F2 ask-in-own-pane / never-relay; P6c audit. |
| `agents/or-plan-writer.md` | edit | F2; F5 walkthrough+approval phase-gate; F6 closing-turn wording; P6c audit. |
| `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md` | edit | Spike 8 (turn-end threshold detection) + cutover-checklist/suite-status lines. |
| `plugins/claude-toolkit/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | edit | Version `1.4.2 → 1.5.0` (×3). |

Files NOT touched (verified against the design §7 manifest): `assets/spawn-protocol.md` (SPAWN/SHUTDOWN mechanics unchanged — the sequencing rule is supervisor discipline, not protocol shape), the brainstormer/plan-writer/finisher spawn-contexts, both handover templates other than the manager's, `README.md`, the researcher agents.

## Plan-level decisions (explicit, reviewable)

1. **Version `1.5.0`.** The design leaves the number to implementation time. This cycle changes behavior (new hook events, gate relocation, override removal) → minor bump, consistent with the prior remediation's `1.3.0 → 1.4.0`.
2. **Hook tests are new infrastructure.** The design's manifest lists only the two hook files; TDD (this suite's standing discipline) requires a failing test first. stdlib `unittest` + `subprocess` (no pytest dependency), at repo-root `tests/hooks/` so nothing ships inside the plugin. Tests use unique per-test `session_id`s and clean up their state files — no production testability shims needed.
3. **Durable reset (micro-fix inside Task 2).** The current script persists state only on announce. The turn-end path has no sub-200k announce to piggyback the <50% reset's persistence on — after a `/compact` from ≥300k, a later 200k turn-end crossing would stay silenced forever. Task 2 persists the reset when it fires. This *preserves* the design's "keep the <50% reset" intent for the new path (and is covered by a test).
4. **F1 "third sequential question" read literally.** The mode-if-ambiguous question moves to *after* worktree-name and base-branch (design Theme E wording: "mode-if-ambiguous, when it fires, is the third sequential question"). Step 1 classifies silently and defers its question; Step 2 sequences all three one-per-turn. Mechanically sound: the slug default derives from the raw input text; the mode is needed only from Step 3 (artifact check) onward.
5. **Supervisor Discipline #1 retimed.** "Tear down the instant they report DONE" becomes phase-scoped: reviewers on verdict received, the **implementer at gate-close** (design D/F25: "the supervisor reaps the task implementer on gate-close, symmetric with how it already reaps the reviewers").
6. **Playbook edited in four consecutive tasks (4, 12, 13, 14), not one.** Design §8.1 itself splits Theme A's playbook edits from the rest ("The playbook F10/F18 edits accompany it"); §8.3's "one pass" guidance is honored as *consecutive same-file tasks, no interleaving with other concerns* — each theme group stays a separately reviewable commit.
7. **Spike numbering:** the new spike is **Spike 8** (the validation doc's next free number).
8. **Hook info-path wording for 200k/250k/300k is re-toned** ("reframed consistently", design Theme A): the old "start planning a natural handover point" contradicts F10's mandatory-immediate handover. The 100k message is untouched.

## F1–F28 → task coverage

| Finding | Task(s) | | Finding | Task(s) |
|---|---|---|---|---|
| F1 | 11 | | F15 | 5 (+upstream note: out of scope) |
| F2 | 9, 10 | | F16 | upstream-only (out of scope) |
| F3 | no-op | | F17 | 5 |
| F4 | 12 | | F18 | 4 |
| F5 | 10 | | F19 | 7 |
| F6 | 10, 13, 16 | | F20 | 1, 2, 4 |
| F7 | 5, 8 | | F21 | 14 |
| F8 | 5 | | F22 | 1, 2 |
| F9 | no-op | | F23 | 14 |
| F10 | 4 | | F24 | 6, 8 |
| F11 | 14, 15, 16 | | F25 | 5, 12 |
| F12 | 5, 12 | | F26 | 7, 8 |
| F13 | 6, 7, 8 | | F27 | 5 |
| F14 | 5, 12 | | F28 | 14, 15 |

Principle-6 audit: (a) Task 5 · (b) Task 6 · (c) Tasks 9–10 · (d) Task 18. Spike: Task 3. Release: Tasks 17–19.

---

## Task 0: Verify branch & starting state

**Files:** none (verification only).

- [ ] **Step 1: Confirm branch, design spec, and clean tracked tree**

```powershell
git -C I:\Dev\claude-toolkit branch --show-current        # expect: or-sas-e2e-remediation
git -C I:\Dev\claude-toolkit status --short               # expect: only untracked breakout-*.png (do NOT add/delete them)
Test-Path I:\Dev\claude-toolkit\docs\superpowers\specs\2026-06-03-or-sas-e2e-remediation-design.md   # expect: True
Test-Path I:\Dev\claude-toolkit\docs\superpowers\plans\2026-06-05-or-sas-e2e-remediation.md          # expect: True (this plan, already committed)
```

If the branch is wrong, STOP and resolve with the user before any edit.

---

## Task 1: Register the checkpoint hook on `Stop` + `SubagentStop` (F20/F22)

Pure registration — the script learns to *handle* these events in Task 2 (TDD). Dormant at runtime either way: the installed plugin (1.4.2) is what executes, not this repo copy. (At the Task-1-only commit the current script would emit `additionalContext` on a turn-end event — an unsupported combo the harness ignores; resolved one commit later.)

**Files:**
- Modify: `plugins/claude-toolkit/hooks/hooks.json`

- [ ] **Step 1: Confirm current registration (RED — the starvation defect)**

```powershell
Select-String -Path I:\Dev\claude-toolkit\plugins\claude-toolkit\hooks\hooks.json -Pattern '"Stop"|"SubagentStop"'
# expect: NO matches — the hook fires only on UserPromptSubmit/PostToolUse (both starved in inbox-driven loops)
```

- [ ] **Step 2: Write the new `hooks.json` (complete content)**

```json
{
  "description": "Context-window checkpoint hook — announces once per session, per event, when main-thread token usage crosses 100k / 200k / 250k / 300k. Turn-end events (Stop/SubagentStop) deliver actionable (≥200k) crossings as decision:block, forcing the handover turn (E2E F20/F22).",
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 3
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/context-usage.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Verify JSON shape + registration (GREEN)**

```powershell
python -c "import json; d=json.load(open(r'I:\Dev\claude-toolkit\plugins\claude-toolkit\hooks\hooks.json', encoding='utf-8')); print(sorted(d['hooks'].keys()))"
# expect: ['PostToolUse', 'Stop', 'SubagentStop', 'UserPromptSubmit']
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/hooks/hooks.json
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): register context-usage hook on Stop + SubagentStop (F20/F22)"
```

---

## Task 2: Turn-end `decision:block` handover delivery in `context-usage.py` (F20/F22) — TDD

The behavior change, test-first. The hook is a plain stdin→stdout script — the tests exercise the **real contract** via subprocess. Design requirements implemented here: turn-end events block on actionable (≥200k) crossings only; `stop_hook_active` loop guard; once-per-threshold per event (new `stop`/`subagent_stop` state keys); the <50% reset preserved **and persisted when it fires** (plan-level decision 3); informational path untouched except re-toned ≥200k wording (plan-level decision 8).

**Files:**
- Create: `tests/hooks/test_context_usage.py`
- Modify: `plugins/claude-toolkit/hooks/context-usage.py`

- [ ] **Step 1: Write the failing tests (complete file)**

Create `tests/hooks/test_context_usage.py`:

```python
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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "plugins" / "claude-toolkit" / "hooks" / "context-usage.py"
STATE_DIR = Path.home() / ".claude" / "hooks" / "state"


class ContextUsageHookTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_dir = Path(self._tmp.name)
        self.session_id = f"test-{uuid.uuid4().hex}"
        self.addCleanup(self._remove_state)

    def _remove_state(self):
        state_file = STATE_DIR / f"context-usage-{self.session_id}.json"
        if state_file.exists():
            state_file.unlink()

    def _transcript(self, tokens):
        entry = {
            "type": "assistant",
            "message": {
                "usage": {
                    "input_tokens": tokens,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 0,
                }
            },
        }
        path = self.tmp_dir / "transcript.jsonl"
        path.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return path

    def run_hook(self, event, tokens, **extra):
        payload = {
            "hook_event_name": event,
            "session_id": self.session_id,
            "transcript_path": str(self._transcript(tokens)),
            **extra,
        }
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    # --- turn-end (Stop / SubagentStop): actionable crossings block ---

    def test_stop_blocks_at_200k(self):
        out = json.loads(self.run_hook("Stop", 210_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])
        self.assertIn("handover", out["reason"].lower())

    def test_subagent_stop_blocks_at_200k(self):
        out = json.loads(self.run_hook("SubagentStop", 210_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

    def test_stop_below_actionable_threshold_stays_silent(self):
        # 150k crosses the informational 100k checkpoint, but turn-end events
        # never force a turn for non-actionable information.
        self.assertEqual(self.run_hook("Stop", 150_000), "")

    def test_stop_blocks_once_per_threshold(self):
        self.run_hook("Stop", 210_000)
        self.assertEqual(self.run_hook("Stop", 215_000), "")

    def test_stop_escalates_to_next_threshold(self):
        self.run_hook("Stop", 210_000)
        out = json.loads(self.run_hook("Stop", 260_000))
        self.assertEqual(out["decision"], "block")
        self.assertIn("250k", out["reason"])

    def test_stop_hook_active_guard_prevents_reblocking(self):
        self.assertEqual(self.run_hook("Stop", 210_000, stop_hook_active=True), "")

    def test_turn_end_state_is_independent_of_prompt_state(self):
        # A prompt-event announcement must not silence the turn-end block.
        self.run_hook("UserPromptSubmit", 210_000)
        out = json.loads(self.run_hook("Stop", 210_000))
        self.assertEqual(out["decision"], "block")

    def test_reset_rearms_turn_end_after_compact(self):
        self.run_hook("Stop", 310_000)                        # announce 300k
        self.assertEqual(self.run_hook("Stop", 120_000), "")  # <50% -> reset (persisted)
        out = json.loads(self.run_hook("Stop", 210_000))      # re-arms
        self.assertEqual(out["decision"], "block")
        self.assertIn("200k", out["reason"])

    # --- informational path (UserPromptSubmit / PostToolUse): unchanged ---

    def test_prompt_event_emits_additional_context_not_block(self):
        out = json.loads(self.run_hook("UserPromptSubmit", 210_000))
        self.assertNotIn("decision", out)
        ctx = out["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "UserPromptSubmit")
        self.assertIn("200k", ctx["additionalContext"])

    def test_tool_event_announces_once(self):
        first = self.run_hook("PostToolUse", 110_000)
        self.assertIn("100k", first)
        self.assertEqual(self.run_hook("PostToolUse", 120_000), "")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests — verify they FAIL for the right reason**

```powershell
python I:\Dev\claude-toolkit\tests\hooks\test_context_usage.py -v
```

Expected: the informational-path tests PASS (regression guards); every turn-end test FAILS — the current script treats `Stop`/`SubagentStop` as unknown events (falls back to the `prompt` state key) and emits `additionalContext` instead of `decision:block` (e.g. `test_stop_blocks_at_200k` → `KeyError: 'decision'`; `test_stop_below_actionable_threshold_stays_silent` → non-empty output; `test_stop_hook_active_guard_prevents_reblocking` → non-empty output).

- [ ] **Step 3: Rewrite `context-usage.py` (complete file)**

Replace the entire file with:

```python
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
```

Notes for the implementer:
- `state_key_for()` is **replaced** by the `EVENT_STATE_KEYS` dict (same fallback: unknown events map to the `prompt` key).
- `latest_main_thread_usage` is unchanged — including the `isSidechain` skip. Whether `SubagentStop` delivers the teammate's own transcript (so the computed usage is the teammate's, not the parent's) is a Spike 8 facet; do not speculate in code.
- Keep everything ASCII in the Python strings (the current file's convention — plain `-`, no smart punctuation).

- [ ] **Step 4: Run the tests — verify ALL PASS**

```powershell
python I:\Dev\claude-toolkit\tests\hooks\test_context_usage.py -v
# expect: 10 tests, OK
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/hooks/context-usage.py tests/hooks/test_context_usage.py
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): turn-end decision:block handover delivery in context-usage hook (F20/F22)"
```

---

## Task 3: Author Spike 8 — turn-end threshold detection (design §5)

Append the one new behavioral spike to the validation doc. **Authored now, executed at cutover** against the installed 1.5.0 plugin (this session's installed plugin is 1.4.2 — running it here would validate the wrong artifact).

**Files:**
- Modify: `docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md`

- [ ] **Step 1: Verify the spike does not exist yet (RED)**

```powershell
Select-String -Path I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md -Pattern 'Spike 8'
# expect: NO matches
```

- [ ] **Step 2: Insert Spike 8 between Spike 7's RESULT block and `## Cutover checklist`**

Insert this block immediately after Spike 7's RESULT paragraph (which ends `…The silence-on-idle conservation discipline is sound.`) and before the `---` preceding `## Cutover checklist`:

````markdown
## Spike 8 — Turn-end threshold detection (E2E remediation Theme A — F20/F22)

**Purpose:** Verify the 1.5.0 hook changes deliver threshold detection in inbox-driven team loops. Facets: (1) the **manager's main-loop `Stop` hook fires under an inbox-wake** (not only on a real user keystroke) — the lone load-bearing unknown of the E2E remediation (undocumented harness behavior); (2) the hook's `{"decision":"block","reason":…}` return on a ≥200k crossing **forces exactly one more turn** containing the handover instruction — the handover turn; (3) **`SubagentStop` delivers for background teammates** (supervisor / phase agents / finisher / workers), and the usage it computes is the *teammate's own* (transcript_path + the script's `isSidechain` filtering interact correctly); (4) the `stop_hook_active` payload guard + once-per-threshold state prevent re-blocking loops (the forced turn's own Stop exits the hook immediately).

**Setup:** Plugin **1.5.0** installed (restart so hooks load). A team with at least one background teammate. A main-loop/teammate transcript pushed past 200k — or, to make crossing cheap, a throwaway copy of the hook with lowered thresholds substituted via a scratch plugin (do NOT lower thresholds in the shipped plugin).

**RED baseline (already recorded — the E2E run itself):** F22 forensics — 126 tool calls across 165 turn-ends produced **zero** hook firings after the last real keystroke; both the manager (~400k) and supervisor (~600k) blew through 200k undetected. The starvation is proven; this spike verifies the cure.

**GREEN:** All four facets hold. Specifically: an inbox-wake turn that ends ≥200k gets one forced handover turn (manager via `Stop`; teammate via `SubagentStop`) whose reason text is the handover instruction; the next turn-end does NOT re-block (guard + once-per-threshold); the teammate-facet usage matches the teammate's transcript, not the parent's.

**Fallback (deliberately not designed — design §5 contingency):** hook-only detection **for the manager** is contingent on facet (1). If facet (1) fails, the manager-side fallback is revisited in a **follow-up design** — the user chose hook-only delivery precisely to avoid proactive-self-tracking context-spam, so no ad-hoc fallback is to be improvised. A facet-(1) failure does NOT invalidate the rest: `SubagentStop` is documented-good, so supervisor/phase-agent/finisher/worker detection stands regardless. If facet (3)'s usage turns out to be the parent's (sidechain interaction), add a SubagentStop-aware transcript path in a follow-up.

---
````

- [ ] **Step 3: Update the cutover checklist + suite status**

Append a new numbered item to `## Cutover checklist` (after item 4):

```markdown
5. **(1.5.0 E2E remediation)** After the 1.5.0 release: `claude plugin install claude-toolkit` (restart so the new hook registration loads), run **Spike 8**, and record its RESULT inline. Theme A's manager-side detection is not "done" until facet (1) is GREEN.
```

And append one line to the end of the `## SUITE STATUS` section:

```markdown
**Spike 8 (turn-end threshold detection) added 2026-06-05 by the E2E remediation (F20/F22) — execution pending at the 1.5.0 cutover.** The "no open follow-ups remain" line above predates it and is superseded for exactly this one spike.
```

- [ ] **Step 4: Verify (GREEN)**

```powershell
$spikes = "I:\Dev\claude-toolkit\docs\superpowers\validation\2026-05-30-or-superpowers-at-scale-behavioral-spikes.md"
Select-String -Path $spikes -Pattern '## Spike 8'                       # expect: 1 match
Select-String -Path $spikes -Pattern 'stop_hook_active'                 # expect: ≥1 match
Select-String -Path $spikes -Pattern '1\.5\.0 E2E remediation'          # expect: 1 match (checklist item 5)
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add docs/superpowers/validation/2026-05-30-or-superpowers-at-scale-behavioral-spikes.md
git -C I:\Dev\claude-toolkit commit -m "docs(or-sas): author Spike 8 - turn-end threshold detection (design 5)"
```

---

## Task 4: Playbook Theme A — mandatory auto-handover (F10) + idle-drift line (F18)

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: F10 — make the 200k handover mandatory and automatic**

In `## Handover Ladder`, replace this paragraph opener:

```markdown
**Cross-session manager handover (crossing 200k).** Stop accepting new SPAWN / SPAWN_RESEARCH requests.
```

with:

```markdown
**Cross-session manager handover (crossing 200k) — MANDATORY AND AUTOMATIC (F10).** Crossing 200k is not a decision point. Do NOT present the user a menu (wrap up / continue / fix-forward), do NOT ask whether to hand over, and do NOT wait for a go-ahead — execute the handover the moment you know you are past 200k. The turn-end checkpoint hook (`Stop` event) announces the crossing and forces one extra turn precisely so the handover can run in it. **Never infer "no reminder yet ⇒ still under threshold"** — reminder absence is evidence of nothing (hook starvation was the headline E2E failure, F20/F22); if ANY signal (hook reminder, token display, your own accounting) shows ≥200k, hand over. *(Load-bearing & unverified until Spike 8 facet 1 is GREEN: whether the manager's main-loop `Stop` fires under an inbox-wake is undocumented — verified at the 1.5.0 cutover. `SubagentStop` for teammates is documented-good.)* On crossing: stop accepting new SPAWN / SPAWN_RESEARCH requests, then:
```

- [ ] **Step 2: F10 — the handover notice is a notice, not a question**

Still in `## Handover Ladder`, replace:

```markdown
Then write `manager-handover-<N>.md` (template at `assets/manager-handover-template.md` — it adds `active_phase` + `active_phase_agent`), and tell the user: `Manager context >200k — recommend fresh session. New manager reads manager-handover-<N>.md first.`
```

with:

```markdown
Then write `manager-handover-<N>.md` (template at `assets/manager-handover-template.md` — it adds `active_phase` + `active_phase_agent`, and its header carries the copy-pasteable resume invocation), and tell the user: `Manager context >200k — recommend fresh session. Resume by pasting the invocation at the top of manager-handover-<N>.md.` That single line is the handover's only user-facing output — it is a **notice, not a question**; no user go-ahead gates any handover step.
```

- [ ] **Step 3: F18 — one named idle-drift line**

In `## Phase Transitions & Idle Taxonomy`, immediately after the wake-up table (after the row ending `| Idle | No output, no tool calls |`), insert:

```markdown
**Idle-discipline drift is a degradation signal (F18).** Catching yourself emitting text on idle wake-ups you previously ended empty (reflexive `Standing by.`, acknowledgments, narration) is evidence your context has degraded — check your token usage now and execute the 200k handover if crossed.
```

- [ ] **Step 4: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'MANDATORY AND AUTOMATIC \(F10\)'      # expect: 1 match
Select-String -Path $pb -Pattern 'no reminder yet'                      # expect: 1 match (the forbidden inference)
Select-String -Path $pb -Pattern 'notice, not a question'               # expect: 1 match
Select-String -Path $pb -Pattern 'Idle-discipline drift'                # expect: 1 match
Select-String -Path $pb -Pattern 'Spike 8 facet 1'                      # expect: 1 match
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): playbook - mandatory auto-handover at 200k (F10) + idle-drift signal (F18)"
```

---

## Task 5: `or-supervisor.md` single pass — Themes B/C/D/G + Principle-6(a) (F8, F17, F14, F7, F25, F27, F15, F12)

The design's §8.3 one-file pass. Load `Skill('superpowers:writing-skills')` before authoring (agent bodies are skill-like content).

**Files:**
- Modify: `plugins/claude-toolkit/agents/or-supervisor.md`

- [ ] **Step 1: Remove the parallel-review override → canonical SDD (F8/F17, P6a)**

Replace everything from the `### Adaptations & override` heading through the line `Everything else from SDD applies verbatim — its red flags, status handling, per-task structure.` (inclusive) with:

````markdown
### Adaptations (the ONLY deviations from SDD)

Two adaptations, both forced by the team topology — pure orchestration. Nothing else deviates: the review flow is SDD's **canonical sequential gate** (implementer → spec review → on pass, code-quality review → fix loops → complete). A "parallel reviewers" optimization used to live here; it was REMOVED after it fragmented under load (E2E F17) — simplicity survives degradation; clever dispatch order does not.

- **Adaptation 1 — dispatch via SPAWN.** Where SDD says "Dispatch implementer subagent" (or spec / code-quality / final reviewer), use the SPAWN protocol below instead. You have no `Agent` tool.
- **Adaptation 2 — `Task*` for task tracking.** SDD instructs `TodoWrite`; you have the team-harness-native `TaskCreate` / `TaskUpdate` / `TaskList` (granted to every teammate by the spec's F7). Use `Task*` wherever SDD says `TodoWrite` — same intent, harness-native mechanism. (The manager seeing `Task*` system reminders is expected and handled manager-side; do not change your behavior for it.)

Everything else from SDD applies verbatim — its red flags, status handling, review sequence, per-task structure.
````

- [ ] **Step 2: Add the parallel-review loophole closure**

In `### Closed loopholes`, after the `- ❌ "I'll skip loading the prompt templates SDD references" …` item (before the `If you catch yourself paraphrasing SDD content` line), add:

```markdown
- ❌ "Reviews can run in parallel to save wall-clock" — they cannot. SDD's sequential gate is canonical;
  the parallel override was removed after it fragmented under load (F17). Dispatch the code-quality
  review only after the spec review PASSES.
```

- [ ] **Step 3: Insert the gate-close sequencing rule (F17 structural guard, F25 implementer reap)**

Insert a new section immediately before `## Depth-1 Constraint`:

````markdown
## Gate-Close Sequencing (HARD RULE — the F17 guard)

SDD's sequential review gate, made explicit at the SPAWN/SHUTDOWN broker layer. A task's gate **fully closes before the next task begins**:

1. A task is **gate-closed** only when its spec review has PASSED and then its code-quality review has PASSED (SDD's order, fix loops settled).
2. On gate-close: mark the task `completed`, request SHUTDOWN for the task's implementer (its reviewers were already reaped on verdict — the implementer reap is the one extra SHUTDOWN per task that keeps the roster stray-free; F25), and only THEN — in a separate, later message — SPAWN the next task's implementer.
3. **Never batch a reviewer SHUTDOWN with the next task's implementer SPAWN in one message.** That batching rhythm is exactly how a missing stage-2 review hides (E2E F17: the SHUTDOWN-then-SPAWN cadence masked an absent code-quality spawn). One protocol action per message keeps the gate auditable: after every SHUTDOWN you can still answer "which review stage is this task in?"

---
````

- [ ] **Step 4: Insert the team-board workaround (F14)**

Insert a new section immediately after the `## Worker Naming Convention` section (i.e. after the line `**Never reuse worker names. Fresh agent = fresh context.**` and its trailing `---`), before `## Topology Disciplines …`:

````markdown
## Team-Board Discipline (harness workaround — F14)

The team task board **auto-flips a task `in_progress → completed` when a background worker exits** — even though the worker never touched the board. Confirmed harness side effect (E2E F14, controlled test), not worker behavior. You own board truth:

- After any of the task's workers exits **before gate-close** (e.g. the spec reviewer reaped on verdict), **re-assert the task to `in_progress`** via `TaskUpdate` — the auto-flip is noise, not progress.
- Mark a task `completed` only at gate-close (both reviews PASSED). Never trust an auto-flip.

---
````

- [ ] **Step 5: Replace the Topology Disciplines list (F7, F25, F15, F27, F12)**

Replace the entire `## Topology Disciplines (manager-context conservation — ordered by impact)` section body — from the heading through the end of current item 6 (which ends `… commit lists / follow-up flags live in ``iteration-N.md``.`), up to but not including the `---` before `## Iteration Handover` — with:

````markdown
## Topology Disciplines (manager-context conservation — ordered by impact)

1. **You DM workers directly — the manager NEVER proxies worker I/O (F7).** Workers are teammates: SendMessage them their task briefs and receive their STATUS reports directly. Never ask the manager to inject a brief, query a worker, or relay a report — the manager is a spawn/teardown broker, nothing more. If you catch yourself routing worker I/O through the manager, STOP and message the worker.
2. **Tear down workers the instant their phase is done** — reviewers when their verdict lands, the task implementer at gate-close (see Gate-Close Sequencing) — by SendMessaging the `manager` a `SHUTDOWN` request (`NAME: <worker>`); the `manager` executes teardown ONLY on your request and never originates one (F25), so any worker you fail to reap idles forever and bloats the manager. One SHUTDOWN per worker, every task, no strays.
3. **Chain actions same-turn** — after `Spawned: X`, brief the worker same turn. No idle gap.
4. **Proactive reporting (all directions).** Workers report STATUS to you the instant they finish — if a worker hasn't reported within reasonable time, ping them once; don't let silent completion block the fix loop. You report iteration handover (>200k or completion) to the `manager` proactively — don't wait to be asked.
5. **Verify reviewer verdicts against the committed artifact at HEAD before gating or relaying (F15).** Spot-check the cited paths/lines in the actual commit (`git show` / `git diff`), not the plan's wording — a reviewer can produce a confident, well-formatted verdict about the wrong artifact. This independent source-verification is the backstop that catches it; wrong fix loops are pure manager-context tax.
6. **In fix-loop relays, enumerate which soft notes to fix vs skip with reasoning.** You are the sole relay between reviewer and implementer; relay quality determines fix-loop efficiency.
7. **Detail lives on disk; pointers go to the manager (F27).** Candidate findings, deviations, gotchas → write them into `iteration-N.md` the moment you notice them; the manager receives at most a one-line pointer (`candidate finding logged in iteration-3.md §2`). Never send the manager multi-paragraph write-ups — its context is the one non-refreshable resource.
8. **`PHASE_PAUSE` before unusual mid-implementation visible actions; everything non-blocking is decide-and-log (F12).** Phase 3 is **local-commits-only**: frequent local commits to the worktree branch are normal workflow — do them freely, never pause for them. Routine end-of-branch integration (push / PR / merge) is **not** your job — it is Phase 4 (`or-finisher`), so it never triggers a pause here either. PAUSE only for the *unusual mid-implementation* visible-to-others or hard-to-reverse action: an external API call, a plan task that itself pushes / deploys / publishes, a delete outside the worktree. To pause, brief the worker to STATUS-and-PAUSE, then SendMessage the `manager` the **structured** token (identical to the phase agents'; one PAUSE token across all depth-1 tiers):

       PHASE_PAUSE
       action: <one line>
       impact: <one line>

   and wait for `PROCEED` or `REJECTED — reason: <line>` propagated back through the `manager`. Send action + impact only — commit lists / follow-up flags live in `iteration-N.md`. **Non-blocking judgment calls are NOT a pause case and never go to the user:** decide, log the decision + rationale in `iteration-N.md`, continue. Phase 3 is autonomous — there is no question channel to the user, by design (F12).
````

- [ ] **Step 6: Principle-6(a) audit + verify (GREEN)**

```powershell
$sup = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-supervisor.md"
Select-String -Path $sup -Pattern 'Override — parallel reviewers'        # expect: NO matches (override gone)
Select-String -Path $sup -Pattern 'spec-gated'                           # expect: NO matches
Select-String -Path $sup -Pattern 'which-result-counts'                  # expect: NO matches
Select-String -Path $sup -Pattern 'Gate-Close Sequencing'                # expect: ≥2 matches (heading + discipline ref)
Select-String -Path $sup -Pattern 'Team-Board Discipline'                # expect: 1 match
Select-String -Path $sup -Pattern 'NEVER proxies worker I/O'             # expect: 1 match
Select-String -Path $sup -Pattern 'committed artifact at HEAD'           # expect: 1 match
Select-String -Path $sup -Pattern 'decide-and-log|decide, log'           # expect: ≥1 match
Select-String -Path $sup -Pattern 'one-line pointer'                     # expect: 1 match
```

P6(a) check: read the final body once — it must contain **no review criteria and no review-ordering methodology beyond the broker-layer sequencing rule** (the sequence itself is stated as SPAWN/SHUTDOWN discipline referencing SDD as owner, which is the design's intent).

- [ ] **Step 7: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-supervisor.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas)!: supervisor - canonical SDD sequential gate + gate-close sequencing guard; board, worker-I/O, teardown, HEAD-verify, decide-and-log disciplines (F8/F17/F14/F7/F25/F27/F15/F12)"
```

---

## Task 6: Reviewer bodies → orchestration-only + report-to-supervisor + verdict self-evidence (F13, F24, P6b)

Same treatment ×3. The bodies keep: worktree bind (STEP -1), report-to-supervisor, verdict protocol, STATUS vocabulary, await-shutdown, read-only tooling constraints. The review **criteria** prose goes — SDD's reviewer-prompt templates own it and arrive via the supervisor's brief.

**Files:**
- Modify: `plugins/claude-toolkit/agents/or-spec-reviewer.md`
- Modify: `plugins/claude-toolkit/agents/or-code-quality-reviewer.md`
- Modify: `plugins/claude-toolkit/agents/or-final-reviewer.md`

- [ ] **Step 1: `or-spec-reviewer.md` — replace `## Protocol` body and add the verdict protocol**

Replace the `## Protocol` paragraph (begins `Idle until your supervisor SendMessages you with your review brief.` and ends `Await ``shutdown_request`` after reporting.`) with:

````markdown
Idle until your supervisor SendMessages you with your review brief. Execute the brief, then
**proactively SendMessage your SUPERVISOR — the agent named `Supervisor:` in your spawn context,
NEVER the manager/team-lead (F13) — your verdict the moment your review is complete or you hit a
blocker.** The manager never proxies worker I/O; a report sent to it is a misroute. Do not idle
silently after finishing — silent completion blocks the fix loop. Await `shutdown_request` after
reporting.

### Verdict protocol (F24 — one self-evident message)

Emit exactly ONE verdict message, no preamble:

1. The first lines echo your **task-id** and the **exact files-under-review** (taken from the diff
   you actually reviewed) — so a wrong-task review is self-evidently invalid to the supervisor.
2. Then the STATUS verdict: DONE / DONE_WITH_CONCERNS (+ enumerated findings citing exact
   `file:line`) / BLOCKED / NEEDS_CONTEXT.
````

- [ ] **Step 2: `or-spec-reviewer.md` — strip criteria from `## Disposition` (P6b)**

Replace the `## Disposition — Read-only spec review` paragraph (begins `You are a REVIEWER, not an implementer.` and ends `…DONE_WITH_CONCERNS with an enumerated findings list otherwise.`) with:

````markdown
You are a REVIEWER, not an implementer. You have no `Edit`/`Write` tools and you never modify code or
mutate state; use `Bash` only for read-only inspection (e.g. `git diff`). **Your review criteria
arrive in your supervisor's brief** (built from SDD's spec-reviewer prompt template) — judge by the
brief; this body is orchestration-only and deliberately restates none of the methodology.
````

- [ ] **Step 3: `or-code-quality-reviewer.md` — same two replacements**

`## Protocol`: identical replacement text to Step 1 (same paragraph + same `### Verdict protocol (F24 — one self-evident message)` block, verbatim).

`## Disposition — Read-only code-quality review`: replace its paragraph (begins `You are a REVIEWER, not an implementer.` and ends `…DONE_WITH_CONCERNS with an enumerated findings list otherwise.`) with:

````markdown
You are a REVIEWER, not an implementer. You have no `Edit`/`Write` tools and you never modify code or
mutate state; use `Bash` only for read-only inspection (e.g. `git diff`). **Your review criteria
arrive in your supervisor's brief** (built from SDD's code-quality-reviewer prompt template) — judge
by the brief; this body is orchestration-only and deliberately restates none of the methodology.
````

- [ ] **Step 4: `or-final-reviewer.md` — same two replacements, branch-scoped echo**

`## Protocol`: replacement as Step 1, except the verdict-protocol item 1 reads:

````markdown
1. The first lines echo the **branch** and the **diff range** (`<base>..HEAD`) you actually
   reviewed — so a wrong-target review is self-evidently invalid to the supervisor.
````

`## Disposition — Read-only final review (whole branch, once)`: replace its paragraph (begins `You are a REVIEWER, not an implementer.` and ends `…DONE_WITH_CONCERNS with an enumerated findings list otherwise.`) with:

````markdown
You are a REVIEWER, not an implementer. You have no `Edit`/`Write` tools and you never modify code or
mutate state; use `Bash` only for read-only inspection (e.g. `git diff`, `git log`). Unlike the
per-task reviewers, you run ONCE per branch after the plan's tasks have landed — that scope is your
identity. **The holistic review criteria arrive in your supervisor's brief** (built from SDD's
final-reviewer prompt template) — judge by the brief; this body is orchestration-only and
deliberately restates none of the methodology.
````

- [ ] **Step 5: Verify (GREEN)**

```powershell
$agents = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
# Criteria prose stripped:
Select-String -Path "$agents\or-spec-reviewer.md" -Pattern 'Judge the implementation strictly'        # expect: NO matches
Select-String -Path "$agents\or-code-quality-reviewer.md" -Pattern 'high cohesion / low coupling'     # expect: NO matches
Select-String -Path "$agents\or-final-reviewer.md" -Pattern 'integrate coherently'                    # expect: NO matches
# New directives present in all three:
Select-String -Path "$agents\or-spec-reviewer.md","$agents\or-code-quality-reviewer.md","$agents\or-final-reviewer.md" -Pattern 'NEVER the manager/team-lead \(F13\)'   # expect: 3 matches
Select-String -Path "$agents\or-spec-reviewer.md","$agents\or-code-quality-reviewer.md","$agents\or-final-reviewer.md" -Pattern 'Verdict protocol \(F24'                # expect: 3 matches
Select-String -Path "$agents\or-spec-reviewer.md","$agents\or-code-quality-reviewer.md","$agents\or-final-reviewer.md" -Pattern 'orchestration-only'                    # expect: 3 matches
```

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-spec-reviewer.md plugins/claude-toolkit/agents/or-code-quality-reviewer.md plugins/claude-toolkit/agents/or-final-reviewer.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): reviewer bodies orchestration-only; report-to-supervisor + self-evident verdicts (F13/F24, P6b)"
```

---

## Task 7: `or-implementer.md` — report target, role boundary, commit discipline (F13, F19, F26)

**Files:**
- Modify: `plugins/claude-toolkit/agents/or-implementer.md`

- [ ] **Step 1: Replace the `## Protocol` paragraph**

Replace the `## Protocol` paragraph (begins `Idle until your supervisor SendMessages you with your task brief.` and ends `Await ``shutdown_request`` after reporting.`) with:

````markdown
Idle until your supervisor SendMessages you with your task brief. **Until that brief arrives, take no
work action: do not start implementing and do NOT commit anything — the team-board task description
is CONTEXT, not your assignment (F26: a fresh implementer once committed scope the user had
explicitly declined, treating the ambient board description as its brief).** Execute the brief, then
**proactively SendMessage your SUPERVISOR — the agent named `Supervisor:` in your spawn context,
NEVER the manager/team-lead (F13) — your STATUS report (DONE / DONE_WITH_CONCERNS / BLOCKED /
NEEDS_CONTEXT) the moment work is complete or you hit a blocker.** The manager never proxies worker
I/O; a report sent to it is a misroute. Do not idle silently after finishing — silent completion
blocks the fix loop. Await `shutdown_request` after reporting.

## Role Boundary (F19)

You implement and test exactly what your brief dispatches — nothing more:

- Do NOT claim or perform verification outside your dispatched role — no browser/manual smoke
  checks, no ad-hoc end-to-end validation. Gate verification is the supervisor's job, exercised
  through the review workers. (E2E F19: an implementer claimed a browser smoke check its brief
  explicitly forbade.)
- **Report only work you actually performed.** A STATUS report that claims checks you did not run
  poisons the review gate that relies on it.
````

- [ ] **Step 2: Verify (GREEN)**

```powershell
$imp = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-implementer.md"
Select-String -Path $imp -Pattern 'CONTEXT, not your assignment \(F26'   # expect: 1 match
Select-String -Path $imp -Pattern 'NEVER the manager/team-lead \(F13\)'  # expect: 1 match
Select-String -Path $imp -Pattern 'Role Boundary \(F19\)'                # expect: 1 match
Select-String -Path $imp -Pattern 'work you actually performed'          # expect: 1 match
Select-String -Path $imp -Pattern 'test-driven-development'              # expect: ≥2 matches (frontmatter + STEP 0 untouched)
```

- [ ] **Step 3: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-implementer.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): implementer - report-to-supervisor, role boundary, no-commit-before-brief (F13/F19/F26)"
```

---

## Task 8: Spawn-context directives — the belt-and-suspenders halves (F13, F26, F24, F7)

Principle 4: every Theme-C fix lands in the agent body (Tasks 5–7) **and** its spawn-context (this task), so a fresh successor inherits the corrected behavior even if a body edit regresses. These files are templates the manager substitutes at spawn time — keep them terse; every line transits the spawn prompt.

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/implementer-spawn-context.md`
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/reviewer-spawn-context.md`
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/supervisor-spawn-context.md`

- [ ] **Step 1: `implementer-spawn-context.md` — full new content (4 lines → 6 lines)**

```markdown
Identity: <NAME> in team <TEAM>
Worktree: <WORKTREE_PATH>
Branch: <BRANCH>
Supervisor: <SUPERVISOR_NAME>
Report ALL status/findings to your SUPERVISOR (<SUPERVISOR_NAME>) via SendMessage — NEVER to the manager/team-lead.
Do NOT commit anything until <SUPERVISOR_NAME> sends your task brief — the board task description is context, not your assignment.
```

- [ ] **Step 2: `reviewer-spawn-context.md` — full new content (4 lines → 6 lines)**

```markdown
Identity: <NAME> (<ROLE>) in team <TEAM>
Worktree: <WORKTREE_PATH>
Branch: <BRANCH>
Supervisor: <SUPERVISOR_NAME>
Report ALL status/findings to your SUPERVISOR (<SUPERVISOR_NAME>) via SendMessage — NEVER to the manager/team-lead.
Verdict protocol: echo the task-id + the exact files-under-review at the top of your verdict; emit exactly ONE verdict message, no preamble.
```

- [ ] **Step 3: `supervisor-spawn-context.md` — append one line (F7)**

After the line `First SPAWN target hint: <FIRST_TASK_HINT>`, append:

```markdown
Worker I/O is yours alone: SendMessage workers their briefs and receive their STATUS reports directly — the manager NEVER proxies worker I/O (no brief injection, no report relay).
```

- [ ] **Step 4: Verify (GREEN)**

```powershell
$assets = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets"
Select-String -Path "$assets\implementer-spawn-context.md" -Pattern 'NEVER to the manager/team-lead'   # expect: 1 match
Select-String -Path "$assets\implementer-spawn-context.md" -Pattern 'not your assignment'              # expect: 1 match
Select-String -Path "$assets\reviewer-spawn-context.md" -Pattern 'NEVER to the manager/team-lead'      # expect: 1 match
Select-String -Path "$assets\reviewer-spawn-context.md" -Pattern 'exactly ONE verdict message'         # expect: 1 match
Select-String -Path "$assets\supervisor-spawn-context.md" -Pattern 'NEVER proxies worker I/O'          # expect: 1 match
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/implementer-spawn-context.md plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/reviewer-spawn-context.md plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/supervisor-spawn-context.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): spawn-contexts carry report-routing, commit-discipline, verdict, worker-I/O directives (F13/F26/F24/F7)"
```

---

## Task 9: `or-brainstormer.md` + `or-finisher.md` — ask in your own pane, never relay (F2) + P6c audit

The prior cycle fixed this for preflight only; the phase-agent bodies still say merely "ask in plain text" — which is how the brainstormer relayed its first question through the manager during the E2E run.

**Files:**
- Modify: `plugins/claude-toolkit/agents/or-brainstormer.md`
- Modify: `plugins/claude-toolkit/agents/or-finisher.md`

- [ ] **Step 1: `or-brainstormer.md` — extend the user-facing section**

In `## You are the user-facing tier`, replace:

```markdown
You have no `AskUserQuestion` — it is main-loop-only and inert for a teammate (Spike 4). Ask the user
in plain text (the canonical skill's questions already are); never reach for a structured prompt.
```

with:

```markdown
You have no `AskUserQuestion` — it is main-loop-only and inert for a teammate (Spike 4). Ask the user
in plain text (the canonical skill's questions already are); never reach for a structured prompt.

**Ask in your OWN pane (F2).** Emit your questions as plain text in your own turn — the user answers
in your pane (they switch with Shift+Down). **NEVER SendMessage the manager your user-facing
questions, and never ask it to relay them**: the manager treats your dialogue as idle and stays
silent, so a relayed question deadlocks the phase — and relaying burns the one context the topology
exists to preserve.
```

- [ ] **Step 2: `or-finisher.md` — same guarantee in its user-facing section**

In `## You are the user-facing tier`, replace:

```markdown
The user talks to you directly. The manager is silent during Phase 4 and does not relay your
conversation. Own the dialogue: surface the finishing options, get the user's choice, carry it out.
```

with:

```markdown
The user talks to you directly. The manager is silent during Phase 4 and does not relay your
conversation. Own the dialogue: surface the finishing options, get the user's choice, carry it out.

**Ask in your OWN pane (F2).** Emit the completion options and any follow-up questions as plain text
in your own turn — the user answers in your pane (Shift+Down). **NEVER SendMessage the manager your
user-facing questions, and never ask it to relay them**: the manager treats your dialogue as idle and
stays silent, so a relayed question deadlocks the phase.
```

- [ ] **Step 3: P6c audit — confirm both bodies are invoke-skill-and-adapt only**

Read both final bodies once. Expected outcome (matches the current content — record in the commit message if clean): every section is orchestration (bind, skill invocation, terminal override, SPAWN_RESEARCH, disciplines, abort, handover); **no task-methodology restatement** (no brainstorming-question technique, no merge-mechanics instructions beyond the worktree/exit topology notes). If a straggler is found, strip it and note it in the commit message.

- [ ] **Step 4: Verify (GREEN)**

```powershell
$agents = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents"
Select-String -Path "$agents\or-brainstormer.md" -Pattern 'Ask in your OWN pane \(F2\)'   # expect: 1 match
Select-String -Path "$agents\or-finisher.md" -Pattern 'Ask in your OWN pane \(F2\)'       # expect: 1 match
Select-String -Path "$agents\or-brainstormer.md","$agents\or-finisher.md" -Pattern 'NEVER SendMessage the manager your'   # expect: 2 matches
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-brainstormer.md plugins/claude-toolkit/agents/or-finisher.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): brainstormer + finisher ask in their own pane, never relay via manager (F2)"
```

---

## Task 10: `or-plan-writer.md` — walkthrough+approval gate, auto-start wording, own-pane (F5, F6, F2) + P6c audit

The single user-approval gate **relocates** from the manager to this user-facing tier (F5↔F6 coupling: auto-start is safe only because `PLAN_COMPLETE` now always carries approval).

**Files:**
- Modify: `plugins/claude-toolkit/agents/or-plan-writer.md`

- [ ] **Step 1: Insert the walkthrough+approval phase-gate (F5)**

Insert a new section immediately after the `### One adaptation, one override` block (i.e. directly before `### Closed loopholes`):

````markdown
### Required phase-gate — plan walkthrough + user approval (F5, BEFORE `PLAN_COMPLETE`)

`superpowers:writing-plans` has **no** user-facing plan-review step (verified during the remediation
design: its self-review is solo and its terminal is the execution handoff this manual overrides). The
walkthrough below is therefore an ORCHESTRATION gate this tier owns — the **single user-approval
gate** for the plan→implementation transition. It is not optional and it is not a duplication of the
canonical skill.

After the plan is written, self-reviewed, and saved — and BEFORE sending `PLAN_COMPLETE`:

1. **Walk the user through the plan in your own pane, section by section** (mirror the brainstormer's
   design-presentation pattern): the Goal/Architecture header first, then the task list as one-line
   summaries, then each task's substance in digestible chunks — checking after each section that it
   matches their intent.
2. **Incorporate feedback by revising the plan file in place**, then re-present the revised section.
3. **Ask for explicit written approval** of the complete plan (e.g. "approve" / "good to go").

Only that explicit approval arms `PLAN_COMPLETE`. Implementation auto-starts on your signal — if the
user has not approved, sending it is a protocol violation.
````

- [ ] **Step 2: Rewire the Override bullet to the approved-means-auto-start contract (F5+F6)**

In `### One adaptation, one override`, replace the Override bullet's closing prose. Replace:

```markdown
  written, self-reviewed against the spec, saved — SendMessage the manager:

      PLAN_COMPLETE — plan: <absolute path to the saved plan>

  The manager then asks the user to confirm before starting implementation, and spawns the supervisor
  (Phase 3) on approval. As your final dialogue turn, tell the user: "Plan complete and saved at
  <path>. Switch to the manager to start implementation." Everything else from the skill applies verbatim —
```

with:

```markdown
  written, self-reviewed against the spec, saved, **and approved by the user through the walkthrough
  gate below (F5)** — SendMessage the manager:

      PLAN_COMPLETE — plan: <absolute path to the saved plan>

  `PLAN_COMPLETE` *means* "the user has approved this plan": the manager spawns the supervisor
  directly on it — there is no second, manager-side go-ahead (F6). As your final dialogue turn, tell
  the user: "Plan approved — implementation starts automatically; the supervisor runs autonomously."
  Everything else from the skill applies verbatim —
```

- [ ] **Step 3: Update the completeness loophole**

In `### Closed loopholes`, replace:

```markdown
- ❌ "I haven't offered the choice, so the plan isn't really complete." — Completeness = plan
  written, self-reviewed against the spec, and saved. The execution choice is exactly the step this
  manual overrides. `PLAN_COMPLETE` fires at that point.
```

with:

```markdown
- ❌ "I haven't offered the choice, so the plan isn't really complete." — Completeness = plan
  written, self-reviewed against the spec, saved, AND user-approved through the walkthrough gate.
  The execution choice is exactly the step this manual overrides. `PLAN_COMPLETE` fires at that
  point.
```

- [ ] **Step 4: Own-pane guarantee (F2)**

In `## You are the user-facing tier`, replace:

```markdown
You have no `AskUserQuestion` — it is main-loop-only and inert for a teammate (Spike 4). Ask the user
in plain text (the canonical skill's questions already are); never reach for a structured prompt.
```

with:

```markdown
You have no `AskUserQuestion` — it is main-loop-only and inert for a teammate (Spike 4). Ask the user
in plain text (the canonical skill's questions already are); never reach for a structured prompt.

**Ask in your OWN pane (F2).** Emit your questions — including every walkthrough-gate section check —
as plain text in your own turn; the user answers in your pane (Shift+Down). **NEVER SendMessage the
manager your user-facing questions, and never ask it to relay them**: the manager treats your
dialogue as idle and stays silent, so a relayed question deadlocks the phase.
```

- [ ] **Step 5: P6c audit + verify (GREEN)**

Read the final body once — every section must be orchestration (bind, skill invocation, gate, override, resume-flush, SPAWN_RESEARCH, disciplines, abort, handover); no restatement of writing-plans methodology (the gate section describes *presentation and approval*, not how to write plans). Then:

```powershell
$pw = "I:\Dev\claude-toolkit\plugins\claude-toolkit\agents\or-plan-writer.md"
Select-String -Path $pw -Pattern 'Required phase-gate — plan walkthrough'        # expect: 1 match
Select-String -Path $pw -Pattern 'single user-approval'                          # expect: 1 match
Select-String -Path $pw -Pattern 'implementation starts automatically'           # expect: 1 match
Select-String -Path $pw -Pattern 'Switch to the manager to start implementation' # expect: NO matches (old final turn gone)
Select-String -Path $pw -Pattern 'manager then asks the user to confirm'         # expect: NO matches (old gate gone)
Select-String -Path $pw -Pattern 'Ask in your OWN pane \(F2\)'                   # expect: 1 match
```

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/agents/or-plan-writer.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas)!: plan-writer owns the plan walkthrough+approval gate; PLAN_COMPLETE = approved (F5/F6); own-pane dialogue (F2)"
```

---

## Task 11: `preflight-brief.md` — one question per turn (F1)

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/preflight-brief.md`

- [ ] **Step 1: Defer the mode-disambiguation question (Step 1 of the brief)**

In `## Step 1 — Detect mode`, replace:

```markdown
If the shape is ambiguous (e.g. a path that matches neither convention), **ask the user in plain text in your own turn** (not via the manager): "I see you provided `<input>`. Is this an idea, a spec, or a plan?" End your turn and wait for their reply in your pane. Never guess.
```

with:

```markdown
If the shape is ambiguous (e.g. a path that matches neither convention), do NOT ask yet: classify provisionally as `idea` (enough for Step 2's slug suggestion) and **defer the disambiguation to the THIRD sequential question** in Step 2: "I see you provided `<input>`. Is this an idea, a spec, or a plan?" Never guess the final mode — Step 3's checks must not run until the user has answered.
```

- [ ] **Step 2: Rewrite the brief's Step 2 as a one-per-turn sequence**

Replace the whole `## Step 2 — Ask the user for worktree name + base branch` section (heading through `…(Plain text, not ``AskUserQuestion``; never relayed through the manager.)`) with:

````markdown
## Step 2 — Ask the setup questions ONE AT A TIME (worktree name → base branch → mode-if-ambiguous)

**One question per turn (F1).** Emit a single plain-text question in your own turn, end the turn, and wait for the user's answer in your pane before asking the next. Never bundle two setup questions in one message. (Plain text, not `AskUserQuestion`; never relayed through the manager.)

1. **Worktree name** — suggest a slug derived from the idea/spec/plan as the default the user can accept. End your turn; wait for the reply.
2. **Base branch** — default the current HEAD; if that is `main`/`master` and `<USER_CONSENT>` is not "yes", require an explicit non-default choice. End your turn; wait for the reply.
3. **Mode — only if Step 1 found the input ambiguous** — ask the deferred disambiguation question. End your turn; wait for the reply.

Only then proceed to Step 3.
````

- [ ] **Step 3: Verify (GREEN)**

```powershell
$pf = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\preflight-brief.md"
Select-String -Path $pf -Pattern 'ONE AT A TIME'                 # expect: 1 match
Select-String -Path $pf -Pattern 'One question per turn \(F1\)'  # expect: 1 match
Select-String -Path $pf -Pattern 'THIRD sequential question'     # expect: 1 match
Select-String -Path $pf -Pattern 'ask the user for both'         # expect: NO matches (bundled ask gone)
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/preflight-brief.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): preflight asks setup questions one per turn; mode disambiguation third (F1)"
```

---

## Task 12: Playbook Themes D+G — pure broker, harness notes, decide-and-log (F25, F4, F14, F12)

First of three consecutive playbook tasks (12–14, per design §8.3 sequencing-by-file).

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Rewrite Conservation Rule #8 (F25)**

Replace:

```markdown
8. **Cull idle workers aggressively.** The supervisor shuts down on DONE; if an idle worker it missed accumulates, shut it down yourself with a one-line note.
```

with:

```markdown
8. **Never originate a teardown (F25).** You execute SHUTDOWN *requests* — broker work — and decide no teardown yourself. A stray worker the supervisor missed idles harmlessly: tolerate it (no output, no action) until the supervisor requests its SHUTDOWN or the session ends. The supervisor reaps each task's implementer at gate-close, so strays are rare by design. (The ONE sanctioned manager-originated teardown is resume reap-by-enumeration — a dead session has no live supervisor to request it; see Handover Ladder.)
```

- [ ] **Step 2: Document the un-suppressible TaskCreate nudge (F4)**

In Conservation Rule #1, replace the closing sentence:

```markdown
If a system reminder nudges `TaskCreate`, ignore it — that nudge is generic; this topology forbids manager-side task tracking.
```

with:

```markdown
If a system reminder nudges `TaskCreate`, ignore it — that nudge is generic; this topology forbids manager-side task tracking. (Known harness limitation, F4: the generic nudge cannot be suppressed plugin-side — it WILL recur; ignoring it every time is correct.)
```

- [ ] **Step 3: Align the SHUTDOWN handshake intro with the pure-broker rule (F25)**

In `### SHUTDOWN (worker teardown — supervisor → manager) — CANONICAL (lives only here)`, replace the opening sentence:

```markdown
You own teardown as well as spawn; the supervisor never shuts a worker down directly (shutdown is a lead action). When SDD says a worker's phase is done, the supervisor SendMessages:
```

with:

```markdown
You own teardown *execution* as well as spawn; the supervisor never shuts a worker down directly (shutdown is a lead action) — and you never *originate* a teardown (F25; Conservation Rule 8): it happens only on a supervisor SHUTDOWN request (resume reap-by-enumeration is the one exception). When SDD says a worker's phase is done, the supervisor SendMessages:
```

- [ ] **Step 4: Add the stray-idle-worker case to the idle taxonomy + the Red-Flags row (F25)**

In the wake-up table's final Idle row, replace:

```markdown
| Worker/research/preflight boot, `shutdown_response`, termination; supervisor turning internally; teammate progress; hook/system reminders; phase-agent / preflight ↔ user dialogue events | Idle | No output, no tool calls |
```

with:

```markdown
| Worker/research/preflight boot, `shutdown_response`, termination; a stray worker idling with no SHUTDOWN requested; supervisor turning internally; teammate progress; hook/system reminders; phase-agent / preflight ↔ user dialogue events | Idle | No output, no tool calls |
```

In `## Red Flags`, insert a new row immediately after the `| Manager calls ``Agent`` without a SPAWN / SPAWN_RESEARCH trigger | All spawns are tier-initiated. |` row:

```markdown
| Manager originates a teardown (culls an idle worker without a supervisor SHUTDOWN request) | Pure broker: spawn and teardown happen only on request (F25). A stray idles harmlessly until the supervisor reaps it; the one exception is resume reap-by-enumeration. |
```

- [ ] **Step 5: Document the board auto-complete (F14) in Recovery**

In `## Recovery from Common Gotchas`, insert after the `- **TaskList ``in_progress`` reverts on system reminders:** …` bullet:

```markdown
- **Team board auto-flips a task `completed` when a worker exits (F14, harness side effect):** noise, not progress. The supervisor re-asserts `in_progress` and owns board truth; the manager takes no action.
```

- [ ] **Step 6: Decide-and-log line (F12)**

In the `**PAUSE relay.**` paragraph, replace the closing sentence:

```markdown
Local commits the underlying skills perform are NOT a pause case.
```

with:

```markdown
Local commits the underlying skills perform are NOT a pause case. Non-blocking judgment calls never reach you either — the supervisor decides and logs them in `iteration-N.md` (decide-and-log, F12); if one lands on you anyway, that is supervisor misbehavior — do not relay it to the user.
```

- [ ] **Step 7: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'Cull idle workers'                    # expect: NO matches (F25 framing gone)
Select-String -Path $pb -Pattern 'Never originate a teardown \(F25\)'   # expect: 1 match
Select-String -Path $pb -Pattern 'Known harness limitation, F4'         # expect: 1 match
Select-String -Path $pb -Pattern 'a stray worker idling'                # expect: 1 match (idle row)
Select-String -Path $pb -Pattern 'Manager originates a teardown'        # expect: 1 match (red flag)
Select-String -Path $pb -Pattern 'auto-flips a task'                    # expect: 1 match (F14)
Select-String -Path $pb -Pattern 'decide-and-log, F12'                  # expect: 1 match
```

- [ ] **Step 8: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas)!: playbook - manager never originates teardown (F25); F4/F14 harness notes; decide-and-log (F12)"
```

---

## Task 13: Playbook Theme E — plan→implementation auto-start (F6)

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Rewire the `PLAN_COMPLETE` idle-taxonomy row**

Replace:

```markdown
| Phase agent `<PHASE>_COMPLETE` (`BRAINSTORM_COMPLETE` / `PLAN_COMPLETE`) | Action | Shut the phase agent down; spawn the next-phase agent. For `PLAN_COMPLETE`: first surface the go-ahead and await the user's approval, *then* spawn the supervisor |
```

with:

```markdown
| Phase agent `<PHASE>_COMPLETE` (`BRAINSTORM_COMPLETE` / `PLAN_COMPLETE`) | Action | Shut the phase agent down; spawn the next-phase agent. `PLAN_COMPLETE` already carries the plan-writer's user-approval gate (F5) — spawn the supervisor directly, no further go-ahead (F6; identical to mode `plan`) |
```

- [ ] **Step 2: Replace the go-ahead paragraph with the auto-start contract**

Replace the whole paragraph:

```markdown
**Plan→implementation go-ahead (the one gated transition).** After `PLAN_COMPLETE` (modes `idea`/`spec`), before spawning the supervisor, surface a single line — e.g. `Plan approved at <path>. Start implementation? It will run multiple tasks autonomously.` — and wait for the user's go-ahead. This gates only this one expensive, hard-to-pause transition; it does NOT gate any normal in-flow action (local commits the underlying skills make stay ungated). Mode `plan` has no such gate — invoking the command with a plan path is itself the go-ahead, so spawn `or-supervisor-1` directly.
```

with:

```markdown
**Plan→implementation auto-start (F6).** `PLAN_COMPLETE` *means* the plan-writer walked the user through the plan and obtained explicit approval (its required F5 phase-gate) — so spawn the supervisor directly on it, all modes identical to mode `plan` (where invoking with a plan path is itself the approval). There is NO manager-side go-ahead: the single user-approval gate lives in the plan-writer's own pane. Surfacing a second confirmation here is a discipline violation — it burns manager context re-asking an answered question.
```

- [ ] **Step 3: Drop the sanctioned go-ahead surfacing from the communication-style list**

In `## Required Communication Style (HARD RULE)`, delete this bullet from the sanctioned transition & lifecycle surfacings list:

```markdown
- the **plan→implementation go-ahead** — see "Phase Transitions & Idle Taxonomy" → Plan→implementation go-ahead.
```

(The list keeps the first-session message and the >200k handover notice.)

- [ ] **Step 4: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'go-ahead and await'                   # expect: NO matches
Select-String -Path $pb -Pattern 'Start implementation\?'               # expect: NO matches (old surfacing gone)
Select-String -Path $pb -Pattern 'auto-start \(F6\)'                    # expect: ≥1 match
Select-String -Path $pb -Pattern 'plan→implementation go-ahead'         # expect: NO matches (bullet deleted)
```

- [ ] **Step 5: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas)!: playbook - implementation auto-starts on PLAN_COMPLETE; manager go-ahead gate removed (F6)"
```

---

## Task 14: Playbook Theme F — `resume` mode, delta-check, sanctioned teardown, zombie tolerance (F11, F28, F21, F23)

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md`

- [ ] **Step 1: Add the `resume` input shape to Mode Detection (F11)**

In `## Mode Detection`, append to the intro paragraph (which ends `…You never detect mode yourself — you read it from the block.`):

```markdown
 **Exception — `resume` (F11):** a `manager-handover-*.md` path is detected by YOU, before any preflight exists (see the Initial Setup pre-check); preflight never sees it.
```

And add a fourth row to the input-shape table after the `plan` row:

```markdown
| Path to a manager handover doc (`*manager-handover-*.md`) | `resume` | Fresh-Manager-Resume — no preflight, no TeamCreate (Initial Setup pre-check) |
```

- [ ] **Step 2: Add the Initial Setup resume pre-check (F11)**

In `## Initial Setup (opening manager turns)`, insert immediately before step `1.` (`**``TeamCreate({team_name: <slug>})`` first.** …`):

```markdown
0. **Resume pre-check (F11, before anything else).** If `<USER_INPUT>` is a path matching `manager-handover-*.md`, this is a **resume**: the team, worktree, and handover dir already exist — there is nothing to set up. Do NOT TeamCreate, do NOT spawn preflight; jump straight to "Handover Ladder → Fresh manager resume" with that doc. (The handover template's header carries this invocation pre-filled, so the user pastes it after `/clear`.)
```

- [ ] **Step 3: Rewrite Fresh-manager-resume with the cheap delta-check + the sanctioned teardown (F28, F21)**

In `## Handover Ladder`, replace the whole `**Fresh manager resume.**` paragraph (begins `**Fresh manager resume.** Read ``manager-handover-<N>.md``;` and ends `…(it re-runs finishing on the existing branch).`) with:

````markdown
**Fresh manager resume** (entered via the `resume` pre-check, or any time the user points you at a `manager-handover-*.md`). Read `manager-handover-<N>.md`; identify `active_phase` / `active_phase_agent` and the **enumerated live-roster table** (one disposition line per member — canonical and required in the template, F28). **Reap orphans first — by live enumeration, made cheap by the captured roster (F21/F28).** Reap-by-enumeration is the **one sanctioned manager-originated teardown** — the explicit, documented exception to the pure-broker rule (F25): a dead session has no live supervisor to request it. Procedure:

1. **Names-only delta-check:** Grep the member `name` fields out of `~/.claude/teams/<team>/config.json` (a handful of lines — do NOT full-read the verbose config) and diff them against the handover's roster table.
2. **Read full member detail only for a delta** — a live member the handover didn't list, or a listed member now gone. The delta is exactly the orphan/zombie set to act on.
3. Issue `shutdown_request` to every orphaned teammate the interrupted session left alive (stale implementers, reviewers, researchers, a prior phase agent / supervisor / finisher). The captured roster makes the live check **cheap**; it never **replaces** it — config lags reality (F21: during the E2E run, live enumeration caught two real orphans the handover doc did not expect).

Then spawn the `N+1` successor (`or-<phase>-N+1` pointing at the phase-agent handover doc + artifact, or `or-supervisor-N+1` pointing at the latest `iteration-N.md`), and resume the broker role. (The new phase agent runs its flush-on-resume + latest-revision cross-check before reopening dialogue.) If `active_phase` is `ship`, spawn `or-finisher-(N+1)` pointing at the plan + the latest `iteration-N.md` (it re-runs finishing on the existing branch).
````

- [ ] **Step 4: Zombie tolerance in Recovery (F23)**

In `## Recovery from Common Gotchas`, insert after the first bullet (`- **Any orphaned member … ``shutdown_request`` each orphan before spawning the ``N+1`` successor.`):

```markdown
- **A handover-inherited zombie ignores `shutdown_request` (F23, harness limitation):** an in-process orphan can emit an idle "available" instead of terminating, and no force-terminate path exists. Tolerate it: at most **2** shutdown attempts, then stop; treat its idle pings as idle (no output, no spam); **flag it in your next manager-handover doc's roster as `zombie`** so the successor does not re-attempt.
```

- [ ] **Step 5: Verify (GREEN)**

```powershell
$pb = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-playbook.md"
Select-String -Path $pb -Pattern 'Resume pre-check \(F11'                 # expect: 1 match
Select-String -Path $pb -Pattern '\| `resume` \|'                         # expect: 1 match (table row)
Select-String -Path $pb -Pattern 'Names-only delta-check'                 # expect: 1 match
Select-String -Path $pb -Pattern 'one sanctioned manager-originated teardown'   # expect: 1 match
Select-String -Path $pb -Pattern 'zombie ignores'                         # expect: 1 match
Select-String -Path $pb -Pattern 'at most \*\*2\*\* shutdown attempts'    # expect: 1 match
```

- [ ] **Step 6: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-playbook.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): playbook - first-class resume mode, roster delta-check, sanctioned teardown, zombie tolerance (F11/F28/F21/F23)"
```

---

## Task 15: `manager-handover-template.md` — resume invocation header + canonical roster capture (F11, F28)

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-handover-template.md`

- [ ] **Step 1: Resume-invocation header (F11)**

Insert immediately after the `# Manager Handover <N>` heading (before `## Topology & Protocol Reference`):

````markdown
## Resume invocation (user: paste this after `/clear`)

```
/claude-toolkit:or-superpowers-at-scale <ABS_PATH_TO_THIS_DOC>
```

(Writing manager: substitute the literal absolute path of this file. The fresh manager detects the `manager-handover-*.md` argument and branches straight to Fresh-Manager-Resume — no preflight, no TeamCreate.)
````

- [ ] **Step 2: Canonical enumerated-roster capture (F28)**

Replace the `### Workers (alive at handover)` section (heading, table, and the trailing `(Workers reported DONE should already be shutdown — list only those genuinely mid-work.)` line) with:

````markdown
### Live roster at handover (canonical — REQUIRED, every member; F28)

Enumerate **every** member from a live read of `~/.claude/teams/<team>/config.json` at write time — never from memory. One disposition line per member. The successor runs a names-only delta-check against this table and reads member detail only for deltas.

| Name | Role | Disposition | Note |
|------|------|-------------|------|
| `<name>` | `<role>` | `keep` / `reap` / `zombie` / `live-worker` | `<one line>` |

Dispositions: `keep` = the resume needs it alive (e.g. the active phase agent); `reap` = orphan — successor issues `shutdown_request`; `zombie` = ignores `shutdown_request` — successor tolerates, max 2 attempts (F23); `live-worker` = genuinely mid-work.
````

- [ ] **Step 3: Verify (GREEN)**

```powershell
$tpl = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\assets\manager-handover-template.md"
Select-String -Path $tpl -Pattern 'Resume invocation'                    # expect: 1 match
Select-String -Path $tpl -Pattern 'or-superpowers-at-scale <ABS_PATH_TO_THIS_DOC>'   # expect: 1 match
Select-String -Path $tpl -Pattern 'Live roster at handover'              # expect: 1 match
Select-String -Path $tpl -Pattern 'Workers \(alive at handover\)'        # expect: NO matches (replaced)
Select-String -Path $tpl -Pattern 'zombie'                               # expect: ≥2 matches
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/manager-handover-template.md
git -C I:\Dev\claude-toolkit commit -m "feat(or-sas): manager-handover template - resume invocation header + canonical roster capture (F11/F28)"
```

---

## Task 16: `SKILL.md` — auto-start flow line + `resume` invocation mode (F6, F11)

**Files:**
- Modify: `plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md`

- [ ] **Step 1: Rewire the Phase-2 flow line (F6)**

In `### Phase flow`, replace:

```markdown
- **Phase 2 — Plan** (mode `idea` or `spec`): the manager spawns `or-plan-writer-1` (teammate, opus). The user talks to it directly. It follows `superpowers:writing-plans` to a reviewed plan, then signals `PLAN_COMPLETE — plan: <path>`. The plan→implementation transition is the one phase boundary the manager gates on the user's explicit go-ahead.
```

with:

```markdown
- **Phase 2 — Plan** (mode `idea` or `spec`): the manager spawns `or-plan-writer-1` (teammate, opus). The user talks to it directly. It follows `superpowers:writing-plans` to a reviewed plan, **walks the user through it for explicit approval** (its required phase-gate, F5), then signals `PLAN_COMPLETE — plan: <path>` — on which the manager spawns the supervisor **directly** (implementation auto-starts; the single user-approval gate lives in the plan-writer's pane, F6).
```

- [ ] **Step 2: Document the `resume` invocation mode (F11)**

In `### Phase flow`, replace the intro paragraph:

```markdown
The orchestrator runs up to five phases; mode detection at preflight chooses the entry point (a plain idea starts at brainstorm, a spec path skips to plan, a plan path skips to implementation). Ship (Phase 4) always runs after the final implementation iteration.
```

with:

```markdown
The orchestrator runs up to five phases; mode detection at preflight chooses the entry point (a plain idea starts at brainstorm, a spec path skips to plan, a plan path skips to implementation). A `manager-handover-*.md` path is the fourth invocation mode — **`resume`** (F11): the manager detects it itself, skips preflight entirely (team + worktree already exist), and executes Fresh-Manager-Resume from that doc; every manager handover doc carries the invocation pre-filled in its header. Ship (Phase 4) always runs after the final implementation iteration.
```

- [ ] **Step 3: Verify (GREEN)**

```powershell
$sk = "I:\Dev\claude-toolkit\plugins\claude-toolkit\skills\or-superpowers-at-scale\SKILL.md"
Select-String -Path $sk -Pattern 'one phase boundary the manager gates'   # expect: NO matches
Select-String -Path $sk -Pattern 'implementation auto-starts'             # expect: 1 match
Select-String -Path $sk -Pattern 'fourth invocation mode'                 # expect: 1 match
Select-String -Path $sk -Pattern 'Fresh-Manager-Resume'                   # expect: 1 match
```

- [ ] **Step 4: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/skills/or-superpowers-at-scale/SKILL.md
git -C I:\Dev\claude-toolkit commit -m "fix(or-sas): SKILL.md - auto-start Phase-2 flow + resume invocation mode (F6/F11)"
```

---

## Task 17: Version bump `1.4.2 → 1.5.0` (×3)

**Files:**
- Modify: `plugins/claude-toolkit/.claude-plugin/plugin.json` (1 occurrence)
- Modify: `.claude-plugin/marketplace.json` (2 occurrences: `metadata.version` + `plugins[0].version`)

- [ ] **Step 1: Bump all three version fields**

In `plugins/claude-toolkit/.claude-plugin/plugin.json`: `"version": "1.4.2"` → `"version": "1.5.0"`.
In `.claude-plugin/marketplace.json`: both `"version": "1.4.2"` occurrences → `"version": "1.5.0"`.

- [ ] **Step 2: Verify (GREEN)**

```powershell
Select-String -Path I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json, I:\Dev\claude-toolkit\.claude-plugin\marketplace.json -Pattern '1\.4\.2'   # expect: NO matches
Select-String -Path I:\Dev\claude-toolkit\plugins\claude-toolkit\.claude-plugin\plugin.json, I:\Dev\claude-toolkit\.claude-plugin\marketplace.json -Pattern '1\.5\.0'   # expect: 3 matches
```

- [ ] **Step 3: Commit**

```powershell
git -C I:\Dev\claude-toolkit add plugins/claude-toolkit/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git -C I:\Dev\claude-toolkit commit -m "release: claude-toolkit 1.5.0 - or-superpowers-at-scale E2E-run remediation (F1-F28)"
```

---

## Task 18: Structural validation + Principle-6(d) audit + plan-coverage self-review

No file edits expected — this is the gate before finishing. If any check fails, fix it as a `fix(or-sas):` follow-up commit and re-run the failed check.

**Files:** none (verification only; possible fix-up commits).

- [ ] **Step 1: Plugin + marketplace validation**

```powershell
claude plugin validate I:\Dev\claude-toolkit\plugins\claude-toolkit    # expect: pass
claude plugin validate I:\Dev\claude-toolkit                           # expect: pass (marketplace)
```

(If `claude` is unavailable in-session, record the skip explicitly in the commit/iteration notes — never claim a pass that did not run. Known pre-existing: `--strict` fails on 4 unrelated command files; out of scope.)

- [ ] **Step 2: Hook tests still green**

```powershell
python I:\Dev\claude-toolkit\tests\hooks\test_context_usage.py -v      # expect: 10 tests, OK
```

- [ ] **Step 3: Cross-file consistency greps**

```powershell
$root = "I:\Dev\claude-toolkit\plugins\claude-toolkit"
# The removed manager gate must be gone EVERYWHERE (skill + playbook + plan-writer):
Select-String -Path "$root\skills\or-superpowers-at-scale\SKILL.md","$root\skills\or-superpowers-at-scale\assets\manager-playbook.md","$root\agents\or-plan-writer.md" -Pattern 'go-ahead'   # expect: only NEGATED occurrences ("no further go-ahead", "NO manager-side go-ahead") — read each match
# The parallel-review override must be gone everywhere:
Select-String -Path "$root\agents\or-supervisor.md" -Pattern 'in parallel' # expect: only the two NEGATED occurrences (removal note + closed loophole)
# Worker report-routing is consistent (bodies + spawn-contexts):
Select-String -Path "$root\agents\or-implementer.md","$root\agents\or-spec-reviewer.md","$root\agents\or-code-quality-reviewer.md","$root\agents\or-final-reviewer.md" -Pattern 'NEVER the manager/team-lead'   # expect: 4 matches
# spawn-protocol.md untouched:
git -C I:\Dev\claude-toolkit diff master -- plugins/claude-toolkit/skills/or-superpowers-at-scale/assets/spawn-protocol.md   # expect: empty
```

- [ ] **Step 4: Principle-6(d) audit (named deliverable — design §4)**

Confirm, reading the final text of each:
1. **(a)** `or-supervisor.md` — no review-methodology override remains; the sequencing rule is framed as SPAWN/SHUTDOWN broker discipline. (Done in Task 5; re-confirm.)
2. **(b)** Reviewer bodies — orchestration-only; criteria deferred to the supervisor's SDD-derived brief. (Task 6; re-confirm.)
3. **(c)** `or-brainstormer.md`, `or-plan-writer.md`, `or-implementer.md`, `or-finisher.md` — STEP -1 bind → STEP 0 invoke-the-skill → minimal orchestration adaptations; no task-methodology stragglers. (Tasks 7, 9, 10; re-confirm.)
4. **(d)** New gates framed as orchestration: the F5 walkthrough section calls itself an ORCHESTRATION gate; F15 is supervisor verification discipline; F24 is reporting protocol — none restate superpowers-skill methodology.

Record the audit outcome (one line per item) in the final iteration/handover notes.

- [ ] **Step 5: Coverage self-review**

Walk the design's §6 coverage table (F1–F28) against `git -C I:\Dev\claude-toolkit log --oneline master..HEAD` — every `fix`/`feat` disposition must map to a landed commit; F3/F9 (non-actionable) and F16 (upstream-only) map to none by design. Confirm the plan's own F→task table matches what landed.

---

## Task 19: Finish the branch (approval-gated)

**REQUIRED SUB-SKILL:** `superpowers:finishing-a-development-branch`.

- [ ] **Step 1: Invoke `Skill('superpowers:finishing-a-development-branch')`**

Present the structured completion options for branch `or-sas-e2e-remediation` (merge to `master` / push + PR / keep as-is). **Do NOT push or merge without the user's explicit choice.**

- [ ] **Step 2: After integration (if merge chosen)**

Remind the user of the cutover step (not part of this plan): `claude plugin install claude-toolkit` + session restart, then **run Spike 8** against the installed 1.5.0 plugin and record its RESULT inline in the spikes doc. Theme A's manager-side detection is contingent on facet (1) GREEN (design §5).

---

## Execution notes for the supervisor/executor

- One commit per task; never `git add -A` (stray untracked `breakout-*.png` at repo root).
- Tasks 4, 12, 13, 14 all edit `manager-playbook.md` — execute them in order, no interleaving edits to that file from other tasks (they were sequenced to be non-overlapping; each step's old-string anchors are unique at its point in the sequence).
- The skill/agent files use LF or CRLF as currently checked in — preserve each file's existing line endings; do not normalize.
- Markdown edits: the old-string anchors quoted in each task are exact at plan-writing time (2026-06-05, HEAD `cf47497`). If an anchor fails to match, STOP and re-read the file — do not fuzzy-match.
