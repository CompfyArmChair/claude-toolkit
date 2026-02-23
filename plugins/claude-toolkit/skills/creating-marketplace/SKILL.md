---
name: creating-marketplace
description: Use when setting up a Claude Code plugin marketplace repository to share plugins with a team or the community - covers marketplace.json schema, repo structure, plugin source types, and team distribution via settings
---

# Creating a Plugin Marketplace

## Overview

A **marketplace** is a GitHub repository with a `.claude-plugin/marketplace.json` catalog that lists available plugins. Users add marketplaces to discover and install plugins.

## Repo Structure

```
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json        # Catalog (required)
├── plugins/
│   ├── plugin-a/               # Each plugin is a directory
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json     # Plugin manifest
│   │   ├── agents/
│   │   ├── commands/
│   │   └── skills/
│   └── plugin-b/
│       └── ...
├── .gitignore
├── LICENSE
└── README.md
```

The `.claude-plugin/marketplace.json` at the repo root is what makes it a marketplace. Plugins can live in-repo or be referenced externally.

## marketplace.json Schema

```json
{
  "name": "my-marketplace",
  "owner": { "name": "your-name" },
  "metadata": {
    "description": "What this marketplace offers",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "What this plugin does",
      "version": "1.0.0"
    }
  ]
}
```

## Plugin Source Types

The `source` field in each plugin entry supports multiple formats:

| Source Type | Format | Example |
|-------------|--------|---------|
| Relative path | `./plugins/name` | Local plugin in same repo |
| GitHub | `github:owner/repo` | Public GitHub repository |
| Git URL | `git+https://...` | Any Git repository |
| npm | `npm:package-name` | npm registry package |
| pip | `pip:package-name` | PyPI package |

Relative paths are resolved from the marketplace repo root.

## User Commands

```bash
# Add a marketplace
claude plugin marketplace add https://github.com/owner/marketplace-repo

# List available plugins from all marketplaces
claude plugin marketplace list

# Install a plugin from a marketplace
claude plugin install plugin-name

# Remove a marketplace
claude plugin marketplace remove marketplace-name

# Update all installed plugins
claude plugin update
```

## Team Sharing

Distribute a marketplace to your team via `settings.json`:

```json
{
  "extraKnownMarketplaces": [
    "https://github.com/your-org/internal-marketplace"
  ]
}
```

Place in project-level `.claude/settings.json` so the marketplace is available to anyone cloning the repo. Users still choose which plugins to install.

## Quick Reference

| File | Purpose |
|------|---------|
| `.claude-plugin/marketplace.json` | Catalog of available plugins (makes repo a marketplace) |
| `plugins/*/` | Plugin directories (if hosting in-repo) |
| `metadata.pluginRoot` | Default directory for relative plugin paths |
| `metadata.version` | Marketplace version (bump on catalog changes) |

## Common Mistakes

- **Missing `.claude-plugin/` directory** at repo root — without it, the repo isn't recognized as a marketplace
- **Mismatched version numbers** — `plugins[].version` should match the plugin's own `plugin.json` version
- **Forgetting to bump marketplace version** — users won't see updates unless `metadata.version` changes
- **Using absolute paths in source** — always use relative paths for in-repo plugins
