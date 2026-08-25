# claude-toolkit

Agents, commands, skills, and hooks for Claude Code — covering code review, research, and development workflows.

## What's Included

### Agents
- **architecture-reviewer** — Production code review against DI, configuration, layer separation, API design, naming, and SRP rules
- **test-reviewer** — Test code review against mocking practices, test setup patterns, and test isolation rules
- **community-researcher** — Research how the community solves problems, surface trade-offs and real-world experience; saves a cited report to docs/research/ and replies with a digest plus the path
- **dependency-researcher** — Research library/SDK documentation from multiple sources; saves a cited report to docs/research/ and replies with a digest plus the path
- **violation-verifier** — Verify whether flagged architectural violations are real or false positives
- **page-courier** — Tier-2 courier of the raw-fetch pipeline: fetches a page in the user's real Chrome and appends its text verbatim to the fetch-page deposit; spawned with URL / DEPOSIT / HELPER from fetch-page's JSON output

**or-superpowers-at-scale orchestrator agents** (internal — spawned by the orchestrator, not for standalone use):
- **or-brainstormer** / **or-plan-writer** — Phase-1/2 teammates the user talks to directly (idea → spec, spec → plan)
- **or-supervisor** — Phase-3 implementation supervisor (drives subagent-driven-development)
- **or-implementer**, **or-spec-reviewer**, **or-code-quality-reviewer**, **or-final-reviewer** — per-task worker tier
- **or-finisher** — Phase-4 ship teammate (drives finishing-a-development-branch in direct dialogue)
- **or-dependency-researcher**, **or-community-researcher** — deposit-aware research teammates

### Commands
- **/design** — Brainstorm and track a design doc (depends on superpowers plugin)
- **/plan-from-design** — Create an implementation plan from a tracked design doc (depends on superpowers plugin)
- **/implement-from-plan** — Execute a tracked plan with subagent-driven development (depends on superpowers plugin)
- **/learn** — Extract reusable patterns from the current session

### Skills
- **designing-mcp-tools** — Naming conventions, parameter design, error handling, and granularity guidance for MCP server tools
- **update-architecture-rules** — Add or modify rules in the architecture-reviewer agent
- **creating-marketplace** — Guide to setting up a Claude Code plugin marketplace
- **creating-plugin** — Guide to creating a Claude Code plugin
- **updating-plugin** — Checklist for modifying an existing plugin: version bumps, manifest sync, and common mistakes
- **or-superpowers-at-scale** — User-invocable 3-tier orchestrator: brainstorm → plan → implement → ship, with the manager's context preserved (`/or-superpowers-at-scale [<idea> | <spec> | <plan>]`; depends on superpowers plugin)
- **research-deposit** — Deposit protocol: research agents write findings to disk and reply with a minimal token
- **research-persistence** — Standalone delivery protocol: researchers save the full report to docs/research/ and reply with a digest plus the path
- **dependency-research-methodology** — Shared library/SDK research-and-citation workflow (used by the dependency researchers)
- **community-research-methodology** — Shared community/real-world research workflow (used by the community researchers)

### Hooks
- **context-usage** — Context-window checkpoint hook (`UserPromptSubmit`, `PostToolUse`, `Stop`, `SubagentStop`): announces once per measurement identity, per event, when token usage crosses 100k / 200k / 250k / 300k. Each warning reports the crossing and its implication for reasoning quality; the ≥200k warnings additionally instruct the baseline response — wrap up and use `/handover`, escalating to stop-immediately at 250k/300k, with 300k noting that work quality may have been compromised (tier-specific protocol still lives in the agent manuals). The informational events inject the warning as `additionalContext`; the turn-end events deliver actionable (≥200k) crossings as `decision:block`, forcing one extra turn so the warning lands — even in inbox-driven team loops where the informational events starve. `SubagentStop` measures the subagent's own transcript under per-agent state, so teammates are warned on their own context, not the parent session's. Per-identity state lives under `~/.claude/hooks/state/`.
- **deny-webfetch** — Unconditional PreToolUse deny for WebFetch; the deny reason teaches the raw-fetch substitute with resolved, runnable plugin paths
- **inject-web-doctrine** — SessionStart injection of the web-research doctrine, rendered from `hooks/web-doctrine.md` with resolved plugin paths

### fetch-page (raw-fetch pipeline CLI)

`fetch-page/` is the tier-1 fetcher of the WebFetch-ban pipeline: it GETs a
URL, extracts readable content, writes it verbatim to a project-local
deposit file (`<projectRoot>/.claude/web-deposits/`), and prints exactly one
JSON line — page content never appears inline. Invoke it via the launcher:

    node <plugin>/fetch-page/bin/fetch-page.js <url>

**First-run behaviour:** dependencies are not bundled. On first use the
launcher runs `npm ci` in the package directory (npm output to stderr; needs
network + npm on PATH); if npm fails it prints a one-line
`{"verdict":"FAIL",...,"reasons":["install:<code>"]}` and exits 1. Full
design: `docs/superpowers/specs/2026-08-08-webfetch-ban-raw-fetch-pipeline-design.md`
and the delta `docs/superpowers/specs/2026-08-23-pipeline-plugin-move-design.md`.

### Running the tests

- fetch-page suite: `cd plugins/claude-toolkit/fetch-page && npm test`
- hook tests: `node --test "tests/hooks/*.test.mjs"` (from the repo root; a bare directory argument fails on current Node)
- python hook tests: `pytest tests/`

## Install

```bash
# Add this marketplace
claude plugin marketplace add https://github.com/CompfyArmChair/claude-toolkit

# Install the plugin
claude plugin install claude-toolkit
```

## Dependencies

The `/design`, `/plan-from-design`, and `/implement-from-plan` commands — and the `or-superpowers-at-scale` skill — depend on the **superpowers** plugin. Install it separately if you want to use them.

## License

MIT
