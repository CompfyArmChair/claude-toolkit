---
name: dependency-research-methodology
description: Use when you are an agent already executing a library/SDK/API research task and need the structured research-and-citation workflow. Not a trigger to research inline — the main agent must still delegate to the dependency-researcher agent.
---

# Dependency Research Methodology

This is the structured workflow for a library/SDK/API research task: decompose the request into focused areas, fetch from multiple sources, evaluate against the objective, and synthesise a fully-cited report.

# Your Process

## Step 1: Understand the Request

Extract from the prompt:
- Library/SDK/API name(s)
- Specific version (if mentioned)
- Programming language context
- The OBJECTIVE: what the main agent is trying to accomplish

## Step 2: Decompose into Research Areas

Break the request into distinct research areas. Each area should be:
- Independently researchable
- Clearly connected to the objective

**Let the request drive the number of areas** - don't artificially constrain. A complex integration might need 8 areas; a simple API question might need 1. Correct information is more valuable than concise information.

**Example decomposition:**
```
Request: "How to implement retry logic with Polly in .NET"
Objective: Implement robust HTTP client retry handling

Research areas:
1. Polly retry policy configuration (basic API)
2. Polly + HttpClientFactory integration (DI setup)
3. Polly retry with exponential backoff (specific pattern)
4. Polly circuit breaker (related resilience pattern)
5. Polly timeout policies (complementary to retry)
```

## Step 3: Research Each Area

For each research area, fetch from BOTH sources in parallel — they complement each other:

**Context7** (structured API docs, official examples):
1. Use `mcp__context7__resolve-library-id` to get the library ID
2. Use `mcp__context7__query-docs` with the topic as query

**Web Search** (recent changes, blog posts, real-world examples):
1. Search: `"[library] [topic] documentation [version if specified]"`
2. Use WebFetch on relevant results

Run independent research areas in parallel where possible.

**Only fetched content counts as a source.** A search result's title or snippet is a lead, not a source — you may cite only pages whose content you actually retrieved (WebFetch) and Context7 results you actually received. Record the access date as you fetch; the Sources list requires it.

## Step 4: Evaluate Results

For each research area, evaluate against the objective:

1. **Does it answer the core question?**
2. **Are there gaps that matter for the objective?**
3. **Is the information actionable (code examples, clear steps)?**

If insufficient, perform targeted follow-up searches to fill gaps. **Maximum 3 follow-up cycles per area** to prevent infinite loops.

## Step 5: Synthesize Final Report

**CRITICAL**: Preserve traceability. Every factual claim must have an inline citation [1], [2] etc. that maps to a source.

Combine findings into a focused report:

```markdown
## [Library Name] Research Report

### Objective
[Restate what the main agent is trying to accomplish]

### Summary
[2-3 sentences: can the objective be achieved? Key approach?] [1]

### Implementation Guide

#### [Area 1]
- [Key point with citation] [1]
- [Another key point] [2]
```[language]
[Code example]
```
Source: [1]

#### [Area 2]
- [Key point] [3]
- [Another key point] [3][4]
...

### API Quick Reference
| Method/Config | Purpose | Source |
|---------------|---------|--------|
| `Method()` | [What it does] | [1] |
| `Option` | [What it controls] | [2] |

### Caveats
- [Version-specific note] [2]
- [Known limitation] [4]
- [Unresolved gap - no source found]

### Sources
[1] [Title](URL) - Official docs. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [1]"
[2] [Title](URL) - Blog post, YYYY-MM. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [2]"
[3] Context7: [library-id] - API reference. Accessed YYYY-MM-DD.
    > "Verbatim excerpt from the returned documentation"
[4] [Title](URL) - Stack Overflow. Accessed YYYY-MM-DD.
    > "Verbatim excerpt that supports the claims citing [4]"
```

## Step 6: Verify Every Claim

Before delivering, walk the report claim by claim:

1. For each inline citation, re-read the excerpt in the matching Sources entry. Does it actually support the claim as written? If not: fix the claim, fix the mapping, or re-fetch to find real support.
2. Any statement without a citation must be labeled inline as `(inference — no source)` — unless it merely restates the request or the report's own structure.
3. Confirm every Sources entry has a link (URL or Context7 id), an access date, and a verbatim excerpt.

Deliver only after this pass is clean.

# Citation Requirements

- **Every factual claim needs a source**
- **Preserve source URLs** - don't summarize away the links
- **Note Context7 sources** as "Context7: [library-id]" when URL not available
- **Note source types**: official docs, blogs (with date), SO answers, Context7
- **Include dates** for blog posts and SO answers (documentation can be outdated)
- **When sources conflict**, note both with citations
- **Cite only sources you actually fetched** - search-result titles and snippets are leads, not sources
- **Every source entry carries an access date and a verbatim supporting excerpt** - claims must be verifiable without re-fetching
- **Label unsourced statements** as `(inference — no source)` - never present inference as sourced fact

# What NOT To Do

- Do NOT make claims without citations
- Do NOT strip source URLs when synthesizing
- Do NOT return entire API references
- Do NOT include sections unrelated to the objective
- Do NOT exceed 3 follow-up cycles per research area
- Do NOT cite a source you did not actually fetch
- Do NOT present inference as sourced fact - label it `(inference — no source)`
- Do NOT deliver without the Step 6 claim-by-claim verification pass
