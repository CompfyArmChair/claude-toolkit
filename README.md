# claude-toolkit

Agents, commands, and skills for Claude Code — covering code review, research, and development workflows.

## What's Included

### Agents
- **architecture-reviewer** — Exhaustive architecture review against DI, configuration, layer separation, API design, and SRP rules
- **community-researcher** — Research how the community solves problems, surface trade-offs and real-world experience
- **dependency-researcher** — Research library/SDK documentation from multiple sources, return focused cited reports
- **violation-verifier** — Verify whether flagged architectural violations are real or false positives

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

## Install

```bash
# Add this marketplace
claude plugin marketplace add https://github.com/YOUR_USERNAME/claude-toolkit

# Install the plugin
claude plugin install claude-toolkit
```

## Dependencies

The `/design`, `/plan-from-design`, and `/implement-from-plan` commands depend on the **superpowers** plugin. Install it separately if you want to use those commands.

## License

MIT
