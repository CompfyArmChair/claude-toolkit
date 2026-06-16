# claude-toolkit

Agents, commands, skills, and hooks for Claude Code — covering code review, research, and development workflows.

## What's Included

### Agents
- **architecture-reviewer** — Production code review against DI, configuration, layer separation, API design, naming, and SRP rules
- **test-reviewer** — Test code review against mocking practices, test setup patterns, and test isolation rules
- **community-researcher** — Research how the community solves problems, surface trade-offs and real-world experience
- **dependency-researcher** — Research library/SDK documentation from multiple sources, return focused cited reports
- **violation-verifier** — Verify whether flagged architectural violations are real or false positives

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
- **dependency-research-methodology** — Shared library/SDK research-and-citation workflow (used by the dependency researchers)
- **community-research-methodology** — Shared community/real-world research workflow (used by the community researchers)

### Hooks
- **context-usage** — Context-window checkpoint hook (`UserPromptSubmit`, `PostToolUse`, `Stop`, `SubagentStop`): announces once per measurement identity, per event, when token usage crosses 100k / 200k / 250k / 300k. Sensor only — each warning reports the crossing and its implication for reasoning quality (threshold policy lives in the agent manuals). The informational events inject the warning as `additionalContext`; the turn-end events deliver actionable (≥200k) crossings as `decision:block`, forcing one extra turn so the warning lands — even in inbox-driven team loops where the informational events starve. `SubagentStop` measures the subagent's own transcript under per-agent state, so teammates are warned on their own context, not the parent session's. Per-identity state lives under `~/.claude/hooks/state/`.

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
