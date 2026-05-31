# claude-toolkit

Agents, commands, and skills for Claude Code — covering code review, research, and development workflows.

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
- **or-dependency-researcher**, **or-community-researcher** — deposit-aware research teammates

### Commands
- **/design** — Brainstorm and track a design doc (depends on superpowers plugin)
- **/plan-from-design** — Create an implementation plan from a tracked design doc (depends on superpowers plugin)
- **/implement-from-plan** — Execute a tracked plan with subagent-driven development (depends on superpowers plugin)
- **/learn** — Extract reusable patterns from the current session
- **/or-superpowers-at-scale** — Orchestrate brainstorm → plan → implement end-to-end in one session (depends on superpowers plugin)

### Skills
- **designing-mcp-tools** — Naming conventions, parameter design, error handling, and granularity guidance for MCP server tools
- **update-architecture-rules** — Add or modify rules in the architecture-reviewer agent
- **creating-marketplace** — Guide to setting up a Claude Code plugin marketplace
- **creating-plugin** — Guide to creating a Claude Code plugin
- **updating-plugin** — Checklist for modifying an existing plugin: version bumps, manifest sync, and common mistakes
- **or-superpowers-at-scale** — 3-tier orchestrator: brainstorm → plan → implement with manager context preserved (depends on superpowers plugin)
- **research-deposit** — Deposit protocol: research agents write findings to disk and reply with a minimal token
- **dependency-research-methodology** — Shared library/SDK research-and-citation workflow (used by the dependency researchers)
- **community-research-methodology** — Shared community/real-world research workflow (used by the community researchers)

## Install

```bash
# Add this marketplace
claude plugin marketplace add https://github.com/CompfyArmChair/claude-toolkit

# Install the plugin
claude plugin install claude-toolkit
```

## Dependencies

The `/design`, `/plan-from-design`, `/implement-from-plan`, and `/or-superpowers-at-scale` commands — and the `or-superpowers-at-scale` skill — depend on the **superpowers** plugin. Install it separately if you want to use them.

## License

MIT
