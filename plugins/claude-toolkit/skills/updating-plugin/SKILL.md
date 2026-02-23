---
name: updating-plugin
description: Use when adding, removing, or modifying components in an existing Claude Code plugin - covers version bumps, manifest updates, marketplace sync, and the checklist to avoid common mistakes
---

# Updating a Plugin

## Overview

When you modify an existing plugin — adding agents, commands, skills, or changing existing ones — you must update version numbers and manifests so users receive the changes.

## Update Checklist

Every plugin update requires these steps:

### 1. Make the Component Change

Add, modify, or remove the component file:

| Action | Location |
|--------|----------|
| Add agent | `agents/new-agent.md` |
| Add command | `commands/new-command.md` |
| Add skill | `skills/new-skill/SKILL.md` |
| Modify existing | Edit the existing file in place |
| Remove component | Delete the file |

### 2. Bump plugin.json Version

In `.claude-plugin/plugin.json`, bump `version` following semver:

| Change Type | Bump | Example |
|-------------|------|---------|
| Bug fix, content tweak | Patch | `1.0.0` → `1.0.1` |
| New agent, command, or skill | Minor | `1.0.0` → `1.1.0` |
| Removed components, breaking changes | Major | `1.0.0` → `2.0.0` |

Update `description` if it no longer accurately describes the plugin contents.

### 3. Bump marketplace.json Version (if applicable)

If the plugin is published through a marketplace, update **both** version fields in `.claude-plugin/marketplace.json`:

- `metadata.version` — the marketplace catalog version
- `plugins[].version` for the changed plugin — must match the plugin's own `plugin.json` version

### 4. Update README

Add or remove the component from the README's listing so users can discover it.

### 5. Commit and Push

Users receive updates via `claude plugin update`, which pulls from the marketplace git repo. Changes aren't visible until pushed.

## Version Alignment Rule

The plugin version must be consistent across all files:

```
.claude-plugin/plugin.json          → "version": "1.1.0"
marketplace.json plugins[].version  → "version": "1.1.0"   (must match)
marketplace.json metadata.version   → "version": "1.1.0"   (bump independently or match)
```

Mismatched versions between `plugin.json` and `marketplace.json plugins[].version` will cause update confusion.

## Quick Reference: Files to Touch

| What Changed | plugin.json | marketplace.json | README |
|-------------|:-----------:|:----------------:|:------:|
| Added component | version + description | both versions + description | add entry |
| Modified component | version | both versions | only if description changed |
| Removed component | version + description | both versions + description | remove entry |

## Common Mistakes

- **Updating plugin.json but not marketplace.json** — users install via marketplace, so both must be in sync
- **Forgetting to bump marketplace metadata.version** — the catalog itself needs a version bump for the marketplace to detect changes
- **Changing description in one place but not the other** — plugin.json and marketplace.json plugin entry should have matching descriptions
- **Not pushing** — version bumps only take effect once pushed to the remote
