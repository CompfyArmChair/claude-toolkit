---
name: designing-mcp-tools
description: Use when designing MCP server tools for AI agent interaction - provides naming conventions, parameter design, error handling patterns, and granularity guidance to make tools discoverable and usable by AI agents
---

# Designing MCP Tools

## Overview

MCP tools are a **UI for AI agents**. Design them so agents can discover, understand, and use them reliably. Descriptions are tooltips, parameters are form fields, errors are validation messages.

## Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Domain-specific naming** | `promote_release` not `update_record` |
| **Rich descriptions** | Every tool and parameter gets a description |
| **Behavioral annotations** | Mark `ReadOnly`, `Idempotent`, `Destructive` |
| **Actionable errors** | Include context + what to do next |
| **Structured outputs** | Define output schemas for reliable chaining |

## Tool Naming

```csharp
// BAD: Generic CRUD
[McpServerTool(Name = "create_record")]
[McpServerTool(Name = "update_row")]

// GOOD: Domain actions
[McpServerTool(Name = "create_release")]
[McpServerTool(Name = "promote_release")]
[McpServerTool(Name = "add_service_to_release")]
```

**Rules:**
- Use `snake_case`
- Start with verb: `create_`, `get_`, `list_`, `update_`, `delete_`
- Include domain noun: `_release`, `_service`, `_template`
- Be specific: `promote_release` not `change_release_stage`

## Parameter Design

```csharp
[McpServerTool(Name = "promote_release")]
[Description("Promote a release to the next stage (Dev -> Staging -> Vnext)")]
public async Task<PromoteResult> PromoteRelease(
    [Description("Release code (e.g., 'rel-acme-2024-q4')")] string releaseCode,
    [Description("Skip validation checks (use with caution)")] bool force = false,
    CancellationToken ct = default)
```

**Rules:**
- Every parameter needs `[Description]`
- Include examples in descriptions: `"(e.g., 'rel-acme-2024-q4')"`
- Use semantic types over primitives when possible
- Mark required vs optional clearly
- Provide sensible defaults

## Tool Annotations

```csharp
// Safe query - can retry freely
[McpServerTool(Name = "list_releases", ReadOnly = true, Idempotent = true)]

// Mutation - changes state
[McpServerTool(Name = "create_release", ReadOnly = false, Idempotent = false)]

// Safe mutation - can retry
[McpServerTool(Name = "update_service_version", ReadOnly = false, Idempotent = true)]
```

| Annotation | Meaning |
|------------|---------|
| `ReadOnly = true` | Does not modify state |
| `Idempotent = true` | Safe to retry without side effects |
| `Destructive = true` | May cause data loss (use with Title for confirmation) |

## Error Handling Strategy

Use **hybrid error handling** - domain errors become actionable MCP responses, infrastructure errors propagate as protocol errors:

```csharp
[McpServerTool(Name = "promote_release", UseStructuredContent = true)]
public async Task<CallToolResult> PromoteRelease(
    [Description("Release code")] string releaseCode,
    CancellationToken ct)
{
    try
    {
        var result = await _releaseService.PromoteAsync(releaseCode, ct);
        return new CallToolResult
        {
            Content = [new TextContentBlock { Text = $"Release '{releaseCode}' promoted to {result.Stage}" }],
            IsError = false  // Explicit for clarity
        };
    }
    catch (InvalidOperationException ex)  // Domain error - recoverable
    {
        return new CallToolResult
        {
            Content = [new TextContentBlock { Text =
                $"Cannot promote '{releaseCode}': {ex.Message}. " +
                "Try 'validate_release' to see what's missing." }],
            IsError = true
        };
    }
    // Infrastructure errors (DB, network) propagate as protocol errors
}
```

| Error Type | Handling | Why |
|------------|----------|-----|
| Validation errors | `IsError = true` + actionable message | Agent can fix input and retry |
| Domain rule violations | `IsError = true` + next steps | Agent can call different tool |
| Not found | `IsError = true` + suggestions | Agent can search/list first |
| Infrastructure (DB, network) | Let propagate | Agent can't fix, human needed |

**Actionable error messages include:**
- What went wrong
- Current state/context
- What to do next (specific tool to call)

## Output Design

Define structured outputs for tool chaining:

```csharp
public record ListReleasesResult(
    IReadOnlyList<ReleaseSummary> Releases,
    int TotalCount,
    string? ContinuationToken);

public record ReleaseSummary(
    string ReleaseCode,      // Can pass to other tools
    string CustomerId,
    ReleaseStage Stage,
    int ServiceCount);
```

**Rules:**
- Return IDs/codes that can be passed to other tools
- Include counts for pagination awareness
- Use records for immutability

## Granularity

**One tool per domain operation** - focused tools beat multi-purpose tools:

```
// GOOD: Focused tools
create_release
promote_release
validate_release
add_service_to_release
list_releases

// BAD: Multi-purpose
manage_release(operation: "create" | "promote" | "validate", ...)
```

**For large tool collections (50+):** Implement progressive discovery:
```csharp
[McpServerTool(Name = "search_tools")]
public async Task<ToolInfo[]> SearchTools(
    [Description("Search query")] string query,
    [Description("Detail level")] DetailLevel detail = DetailLevel.NameAndDescription)
```

## Domain Separation

Organize tools by domain boundary:

```
ReleaseTools        -> create_release, promote_release, validate_release
ServiceTools        -> create_service, list_services, refresh_module_versions
TemplateTools       -> generate_templates, preview_templates
ModuleTools         -> check_module_exists, list_module_versions
```

Each domain can be a separate `[McpServerToolType]` class with its own dependencies.

## Quick Reference

| Aspect | Pattern |
|--------|---------|
| Name | `snake_case`, verb + domain noun |
| Description | What it does + when to use |
| Parameters | All have descriptions with examples |
| Annotations | `ReadOnly`, `Idempotent` for safety hints |
| Errors | Context + what went wrong + next action |
| Output | Structured records with chainable IDs |
| Granularity | One operation per tool |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Generic CRUD names | `create_record` is ambiguous | Use domain language |
| Missing descriptions | Agent guesses meaning | Describe everything |
| Vague errors | "Failed" gives no recovery path | Include context + next steps |
| Multi-purpose tools | Complex parameter logic | Split into focused tools |
| Primitive-only params | Lose semantic meaning | Use typed parameters |
| No output schema | Agent can't parse reliably | Define structured outputs |
| Catch-all in infrastructure | Errors hidden, tool returns empty success | Only catch expected cases |

## Infrastructure Error Handling

**Critical rule:** Infrastructure code (repositories, clients, adapters) must NOT swallow errors. Only catch specific expected exceptions.

```csharp
// BAD: Catch-all hides auth failures, network errors, parsing errors
public async Task<ServiceDefinition?> ReadManifestAsync(string serviceId, CancellationToken ct)
{
    try
    {
        // ... read from ACR
        return _yaml.Deserialize<ServiceDefinition>(content);
    }
    catch (RequestFailedException ex) when (ex.Status == 404)
    {
        return null;  // OK - expected case
    }
    catch (Exception ex)
    {
        _logger.LogWarning(ex, "Failed to read manifest");
        return null;  // BAD - tool returns empty success, agent thinks nothing exists
    }
}

// GOOD: Only catch expected cases, let others bubble up
public async Task<ServiceDefinition?> ReadManifestAsync(string serviceId, CancellationToken ct)
{
    try
    {
        // ... read from ACR
        return _yaml.Deserialize<ServiceDefinition>(content);
    }
    catch (RequestFailedException ex) when (ex.Status == 404)
    {
        return null;  // Expected: resource doesn't exist
    }
    // Auth errors, network errors, parse errors -> propagate to tool layer
}
```

**Why this matters:**
- Swallowed errors cause tools to return `{"services": [], "count": 0}` instead of error messages
- Agent thinks operation succeeded with no results, when actually it failed
- Debugging becomes impossible - logs show warnings but no actionable feedback
- Only the tool layer should decide how to present errors to the agent

## .NET SDK Specifics (v0.5.0+)

Package: `ModelContextProtocol.AspNetCore` version `0.5.0-preview.1`

### Key API Details

**Content blocks use `TextContentBlock`** (not `TextContent`):
```csharp
using ModelContextProtocol.Protocol;

// CORRECT - v0.5.0+
Content = [new TextContentBlock { Text = "message" }]

// WRONG - older API
Content = [new TextContent { Type = "text", Text = "message" }]
```

**`Type` property is read-only** - The `TextContentBlock.Type` property is auto-set to `"text"`. Do not try to assign it.

**`UseStructuredContent = true` - Required for custom return types, NOT for MCP library types:**

```csharp
// CORRECT: Custom return type requires UseStructuredContent = true
[McpServerTool(Name = "list_services", ReadOnly = true, Idempotent = true, UseStructuredContent = true)]
public async Task<ServiceListResult> ListServices(CancellationToken ct = default)
{
    var services = await _client.ListAsync(ct);
    return new ServiceListResult(services, services.Count);
}

// CORRECT: CallToolResult does NOT use UseStructuredContent
[McpServerTool(Name = "validate_release", ReadOnly = true, Idempotent = true)]
public async Task<CallToolResult> ValidateRelease(...)

// WRONG: UseStructuredContent with CallToolResult produces invalid response
[McpServerTool(Name = "validate_release", UseStructuredContent = true)]  // DON'T
public async Task<CallToolResult> ValidateRelease(...)
```

| Return Type | UseStructuredContent |
|-------------|---------------------|
| Custom objects (`ServiceListResult`, etc.) | `true` (required) |
| `CallToolResult` | `false` or omit (default) |
| Other MCP library types | `false` or omit (default) |

**Set `IsError` explicitly** - For success responses, explicitly set `IsError = false`:
```csharp
return new CallToolResult
{
    Content = [new TextContentBlock { Text = "Success message" }],
    IsError = false  // Be explicit for testability
};
```

### Response Helper Pattern

Create a helper class for consistent responses:

```csharp
public static class McpToolResponse
{
    public static CallToolResult Success(string message) => new()
    {
        Content = [new TextContentBlock { Text = message }],
        IsError = false
    };

    public static CallToolResult Error(string message) => new()
    {
        Content = [new TextContentBlock { Text = message }],
        IsError = true
    };
}
```

### Testing Responses

When testing `CallToolResult`, cast content blocks to access `Text`:

```csharp
using ModelContextProtocol.Protocol;

// Access text content in tests
var text = ((TextContentBlock)result.Content[0]).Text;
text.Should().Contain("promoted");
```
