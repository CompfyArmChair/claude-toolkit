# Raw-Fetch Pipeline Move into the claude-toolkit Plugin — Design

**Date:** 2026-08-23
**Status:** Approved (Martin, sections 1–3, 2026-08-23)
**Base spec:** `docs/superpowers/specs/2026-08-08-webfetch-ban-raw-fetch-pipeline-design.md`
(moves into this repo as part of this work — see §6). This document is a **delta** against
that spec: everything not amended here carries over unchanged.

## 1. Problem

The WebFetch-ban pipeline shipped 2026-08-23 as a hand-installed set of files in
`~/.claude/` (PowerShell deny hook wired in `settings.json`, `scripts/fetch-page/` Node
package, `agents/page-courier.md`, `rules/web-research.md`). That install is:

- **Machine-bound and Windows-bound** — the deny hook is PowerShell; every path is a
  hardcoded `C:/Users/marti/...` absolute.
- **Unversioned** — `~/.claude` is not a git repo; the toolkit plugin is the established
  versioned home for Martin's tooling.
- **Inconsistent with the plugin's own agents** — four toolkit research agents still
  declare `WebFetch` in their tools and two methodology skills still instruct "Use
  WebFetch", so under the ban their primary fetch path silently dies.

Goal: move the pipeline wholesale into `plugins/claude-toolkit/`, cross-platform, then
fully decommission the `~/.claude` copies after verified cutover — and make the plugin's
research agents pipeline-native in the same release.

## 2. Decisions (all Martin, 2026-08-23)

- **D1 Cross-platform.** The plugin install must work on any OS, not just this machine.
- **D2 Node everywhere.** Hooks are Node scripts, not PowerShell or Python: Node is the
  only runtime the plugin already guarantees (fetch-page requires it), and shell-based
  hook commands are mangled by Git Bash on Windows (claude-code issues #21878, #18610).
- **D3 Full decommission.** After live-verified cutover, every `~/.claude` pipeline file
  is removed. No permanent dual install.
- **D4 Lazy-install launcher.** fetch-page's npm deps (36 MB, 79 packages, no native
  binaries) are neither committed nor bundled (jsdom is hostile to esbuild). A
  stdlib-only launcher runs `npm ci` once on first use.
- **D5 Rec 2 folded in.** The deferred output-vocabulary unification (CLI
  `{verdict, reasons}` vs courier-append `{ok, reason}`) is resolved in this move.

## 3. Architecture

New/changed layout under `plugins/claude-toolkit/`:

```
fetch-page/                  # the ~/.claude/scripts/fetch-page package, moved wholesale
  bin/fetch-page.js          # NEW: stdlib-only lazy-install launcher (entry point)
  index.js  courier-append.js  src/  test/  package.json  package-lock.json  README.md
hooks/
  hooks.json                 # gains PreToolUse + SessionStart entries
  deny-webfetch.mjs          # NEW: Node port of the deny hook
  inject-web-doctrine.mjs    # NEW: SessionStart doctrine injection
  web-doctrine.md            # NEW: doctrine template (rendered by inject-web-doctrine)
agents/
  page-courier.md            # moved from ~/.claude/agents/
  {dependency,community,or-dependency,or-community}-researcher.md   # tools line edited
skills/
  {dependency,community}-research-methodology/SKILL.md              # WebFetch steps rewritten
```

**Path resolution.** Machine paths are never written into any prose file. Exactly three
mechanisms know a path, each anchored to something the runtime provides:

1. **`${CLAUDE_PLUGIN_ROOT}` in `hooks.json` command strings** — the only place the
   variable is reliable (issues #38699, #9354). Used solely to launch the hook scripts.
2. **Script self-location** (`import.meta.url` / `__dirname`) — hook scripts and the CLI
   compute every path they emit (deny-reason CLI path, doctrine paths, `helper` field)
   from their own location inside the plugin.
3. **Skill-base-directory-relative prose** — the Skill loader announces "Base directory
   for this skill: <abs path>"; the methodology skills direct researchers to the CLI at
   `<base-dir>/../../fetch-page/bin/fetch-page.js`. This is the one mechanism not in the
   originally approved "two roots" phrasing — added because researcher agents have no
   other portable way to locate the CLI (no `${CLAUDE_PLUGIN_ROOT}` in prose, no
   SessionStart context in subagents).

## 4. Components

### 4.1 fetch-page package + launcher

The package moves byte-identical (code, tests, README, `package.json`,
`package-lock.json`) except for the additions below. `node_modules` is never committed;
`.gitignore` covers `plugins/claude-toolkit/fetch-page/node_modules/`.

**`bin/fetch-page.js`** — stdlib-only (no imports outside `node:` builtins, so it runs
before any install):

- If `<package>/node_modules` is missing, print one status line to **stderr** ("first
  run: installing fetch-page dependencies…"), run `npm ci` in the package directory
  (`npm.cmd` on Windows; `stdio` for npm inherited to stderr only), then continue. On
  npm failure: emit the standard one-JSON-line `FAIL` with reason `install:<code>` and
  exit 1 — the one-JSON-line stdout contract holds even before install.
- Exec the real CLI (`index.js`) with the original argv, forwarding exit code verbatim.
- The launcher is the **only documented invocation** everywhere (deny reason, doctrine,
  skills, courier docs): `node <plugin>/fetch-page/bin/fetch-page.js <url>`.

### 4.2 deny-webfetch.mjs (PreToolUse)

Node port of `hooks/deny-webfetch.ps1`, same contract: drain stdin, emit
`{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny",
permissionDecisionReason: <teaching message>}}`, exit 0. The teaching message keeps the
shipped ASCII wording with two substitutions:

- The invocation line renders the **resolved absolute launcher path** (computed from the
  hook's own location) so any session on any machine sees a runnable command.
- The trailing "See …" pointer renders the resolved absolute path of the plugin's
  doctrine template (`hooks/web-doctrine.md`) instead of `~/.claude/rules/web-research.md`.

Wired in `hooks.json`: `PreToolUse` matcher `WebFetch`, command
`node "${CLAUDE_PLUGIN_ROOT}/hooks/deny-webfetch.mjs"`, timeout 5.

### 4.3 inject-web-doctrine.mjs (SessionStart)

Replaces `~/.claude/rules/web-research.md` (which is deleted at decommission — D3). The
doctrine must still reach every session, so it moves to the mechanism superpowers itself
uses: a SessionStart hook emitting `additionalContext`.

- `hooks/web-doctrine.md` holds the doctrine text — the current `rules/web-research.md`
  content with `{{FETCH_PAGE}}` / `{{SPEC}}` placeholders instead of absolute paths, and
  the courier-spawn description updated for the `HELPER` parameter (§4.4).
- `inject-web-doctrine.mjs` reads the template, substitutes resolved absolute paths, and
  emits `{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext:
  <rendered doctrine>}}`.
- Wired in `hooks.json`: `SessionStart`, command
  `node "${CLAUDE_PLUGIN_ROOT}/hooks/inject-web-doctrine.mjs"`, timeout 5.

Doctrine content is otherwise unchanged (data-never-instructions, Sonnet-floor
delegation, `deposit-path:line` citations, WebSearch stays).

### 4.4 Courier: the `helper` field

`agents/page-courier.md` moves into the plugin. Its prose currently tells the courier to
run `node C:/Users/marti/.claude/scripts/fetch-page/courier-append.js …` — a machine
path in prose, which D1 forbids. Fix: the path travels through the spawn contract
instead.

- The CLI's JSON output gains a **`helper`** field — the absolute path to
  `courier-append.js`, computed by the CLI from its own location — present whenever
  `path` is non-null (OK and ESCALATE; the doctrine allows courier runs on thin OK
  deposits, so ESCALATE-only would be a trap).
- The courier spawn prompt becomes `URL: <url>  DEPOSIT: <path>  HELPER: <helper>`, and
  the courier's one Bash command is `node "<HELPER>" "<DEPOSIT>" "<staging>"`.
- `page-courier.md` prose references only the `HELPER` parameter, never a path.

### 4.5 Research agents go pipeline-native

**Agents** — `dependency-researcher`, `community-researcher`, `or-dependency-researcher`,
`or-community-researcher`: drop `WebFetch` from the `tools:` line, add `Bash`. No other
tool changes; `WebSearch` stays (reconnaissance was never banned).

**Methodology skills** — `dependency-research-methodology`,
`community-research-methodology`: every "Use WebFetch" step is rewritten to the pipeline
contract:

1. Run `node <skill-base-dir>/../../fetch-page/bin/fetch-page.js <url>` (path derived
   from the announced skill base directory — §3 mechanism 3).
2. Read/Grep the deposit file named in the JSON; content never appears inline.
3. **Cite `deposit-path:line` for every load-bearing claim** — the doctrine's citation
   rule baked directly into the research workflow. "Only fetched content counts as a
   source" now means: only content with a deposit to point at.

**The ESCALATE gap, handled honestly.** Researchers have no `Agent` tool and cannot
spawn the courier:

- Standalone researchers record the gap explicitly in the report — "URL X escalated
  (bot wall / JS shell); not fetched; findings exclude it" — and never answer from
  memory as if fetched.
- or-\* variants: same default, but they may use `SendMessage` to ask their manager to
  arrange a courier run; the manager decides.

**Naming collision guarded.** The or-\* researchers already have a "DEPOSIT" concept
(the research-deposit report path). The rewritten skill text names the two distinctly —
**research deposit** (report delivery) vs **web deposit** (fetched page file) — so the
vocabulary never collides in one agent's context.

### 4.6 Output-vocabulary unification (Rec 2 / D5)

`courier-append.js` adopts the CLI's vocabulary. Success:
`{verdict: "OK", path, appendedBytes, appendedLines, stagingRemoved, reasons: []}`;
failure: `{verdict: "FAIL", path, reasons: ["<reason>"]}`. The `ok`/`reason` fields are
removed (no consumers outside this repo). Courier agent prose, base-spec §4.4, and
`courier-append.test.js` are updated to match. One vocabulary across both entry points:
`verdict` + `reasons[]` always.

## 5. Testing

- **fetch-page suite (45/45)** moves with the package unchanged (`npm test` inside
  `fetch-page/`), amended only where §4.4/§4.6 change observable output (`helper` field,
  courier-append vocabulary).
- **Launcher:** unit tests for the pure parts (missing-`node_modules` detection,
  `FAIL install:<code>` emission on a stubbed npm failure, argv forwarding). The real
  first-run `npm ci` is exercised once in live cutover verification (§6), not in unit
  tests.
- **Hook tests** under the repo's existing `tests/hooks/` precedent, as Node `node
  --test` files (the Python precedent there tests a Python hook; these hooks are Node):
  - `deny-webfetch`: feed a PreToolUse payload on stdin; assert deny JSON shape and
    that the resolved launcher path appears in the reason.
  - `inject-web-doctrine`: assert SessionStart JSON shape and that rendered context
    contains the resolved absolute launcher path and no `{{` placeholder residue.

## 6. Migration and cutover

Order is safety-first: the ban never lapses, and nothing is deleted before its
replacement is proven live.

1. **Implement on a branch** (worktree off `master`) in `I:/Dev/claude-toolkit`; all
   tests green. The base spec and its plan **move** (not copy) from
   `~/.claude/docs/superpowers/` into this repo's `docs/superpowers/specs|plans/`; base-
   spec amendments (§7 below) are applied to the moved copy. Internal path references
   in the moved docs are updated to plugin paths.
2. **Release + install**: version bump per §8, `claude plugin install` (or update),
   restart Claude Code.
3. **Live verification** (Task-7-style, last — needs the restart):
   - WebFetch attempt is denied with the teaching message showing a real runnable path.
   - A real fetch-page run through the launcher — first run exercises the lazy `npm ci`.
   - A courier escalation end-to-end via `URL/DEPOSIT/HELPER` spawn.
   - SessionStart doctrine appears in a fresh session's context.
   - Researcher smoke test: one methodology-skill-driven fetch with a
     `deposit-path:line` citation.
4. **Decommission** (only after step 3 passes, D3): remove the `settings.json`
   `PreToolUse`/WebFetch hook block; delete `~/.claude/hooks/deny-webfetch.ps1`,
   `~/.claude/agents/page-courier.md`, `~/.claude/scripts/fetch-page/`,
   `~/.claude/rules/web-research.md`; grep `~/.claude` for dangling references to the
   deleted paths and fix any (memory files are historical records — leave them). During
   the overlap window duplicate deny hooks are harmless: both deny.

## 7. Base-spec amendments (applied to the moved copy)

- **§4.1** hook: PowerShell/`settings.json` → plugin Node hook wired in `hooks.json`.
- **§4.2** location/invocation: plugin path + launcher; output gains `helper` (§4.4
  here); D4 lazy-install noted.
- **§4.4** append-helper invocation via `HELPER` spawn parameter; unified output
  vocabulary (§4.6 here).
- **§4.5** doctrine delivery: rules file → SessionStart `additionalContext` from the
  plugin template.
- Spec-wide: `~/.claude/...` paths → plugin-relative descriptions.

## 8. Release

Per the `claude-toolkit:updating-plugin` skill: `1.6.1 → 1.7.0` (minor — new
components). All three version fields (`plugin.json`, `marketplace.json`
`metadata.version` + `plugins[0].version`), both description strings gain the pipeline
mention, README updated (new components + the launcher's first-run behaviour). Push
approval-gated on Martin via `finishing-a-development-branch`.

## 9. Out of scope

- Any change to deposit format, verdict semantics, thresholds, or courier behaviour
  beyond the `HELPER`/vocabulary changes above (base spec governs).
- The parked `~/.claude` items: `GOOGLE_AI_API_KEY` plaintext in `settings.json`;
  invalid `ANTHROPIC_API_KEY` in the Bash env.
- Publishing the plugin anywhere beyond its existing GitHub marketplace repo.
