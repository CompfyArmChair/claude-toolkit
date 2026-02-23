---
name: creating-plugin
description: Use when creating a Claude Code plugin to package and share agents, commands, skills, hooks, or MCP servers - covers plugin.json schema, directory layout, component types, local testing, and validation
---

# Creating a Plugin

## Overview

A **plugin** is a directory with a `.claude-plugin/plugin.json` manifest and component directories (agents, commands, skills, etc.) at the same level. Plugins package Claude Code extensions for distribution via marketplaces.

## Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json             # Manifest (required)
├── agents/                     # Agent definitions
│   └── my-agent.md
├── commands/                   # Slash commands
│   └── my-command.md
├── skills/                     # Skills
│   └── my-skill/
│       └── SKILL.md
├── hooks/                      # Lifecycle hooks
│   └── pre-commit.sh
├── mcp-servers/                # MCP server configurations
│   └── my-server.json
└── lsp-servers/                # LSP server configurations
    └── my-lsp.json
```

Components sit **next to** `.claude-plugin/`, not inside it.

## plugin.json Schema

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin provides",
  "author": { "name": "your-name" }
}
```

Optional fields for custom component paths:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin provides",
  "author": { "name": "your-name" },
  "agents": "./custom-agents-dir",
  "commands": "./custom-commands-dir",
  "skills": "./custom-skills-dir"
}
```

If custom paths are omitted, the default directory names (`agents/`, `commands/`, `skills/`, etc.) are used.

## Component Types

| Component | Directory | Format | Purpose |
|-----------|-----------|--------|---------|
| Agents | `agents/` | `.md` files with YAML frontmatter | Specialized subagent definitions |
| Commands | `commands/` | `.md` files | Slash commands (`/command-name`) |
| Skills | `skills/` | `skill-name/SKILL.md` | Reference guides and techniques |
| Hooks | `hooks/` | Shell scripts or config | Lifecycle event handlers |
| MCP Servers | `mcp-servers/` | `.json` config files | Model Context Protocol servers |
| LSP Servers | `lsp-servers/` | `.json` config files | Language Server Protocol servers |

## Local Testing

Test your plugin before publishing:

```bash
# Run Claude Code with your plugin loaded
claude --plugin-dir /path/to/my-plugin

# Verify agents appear
# Verify commands appear (type / to list)
# Verify skills are discoverable
```

## Validation

```bash
# Validate plugin structure
claude plugin validate /path/to/my-plugin
```

Checks for:
- Valid `plugin.json` with required fields
- Component directories exist and contain valid files
- No structural errors

## Version Bumps

Users receive updates only when `version` in `plugin.json` changes. Always bump the version when modifying plugin contents:

```
1.0.0 → 1.0.1  (patch: bug fixes, minor content changes)
1.0.0 → 1.1.0  (minor: new agents, commands, or skills added)
1.0.0 → 2.0.0  (major: breaking changes, removed components)
```

## Quick Reference

| File | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin manifest (makes directory a plugin) |
| `agents/*.md` | Agent definitions with YAML frontmatter |
| `commands/*.md` | Slash command definitions |
| `skills/*/SKILL.md` | Skill reference documents |
| `version` in plugin.json | Must bump for users to receive updates |

## Common Mistakes

- **Putting components inside `.claude-plugin/`** — components go next to it, not inside it
- **Forgetting version bumps** — users won't get updates without a version change
- **Missing YAML frontmatter in agents** — agents need `name`, `description`, `tools`, and optionally `model` in frontmatter
- **Flat skill files** — skills must be in subdirectories: `skills/skill-name/SKILL.md`, not `skills/SKILL.md`
- **Using spaces in names** — use hyphens: `my-plugin` not `my plugin`
