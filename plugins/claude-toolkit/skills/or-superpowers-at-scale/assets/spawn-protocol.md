# SPAWN / SPAWN_RESEARCH Protocol — full mechanics

The handshakes that let depth-1 tiers (the supervisor and the phase agents — none of which hold the `Agent` tool) cause a fresh teammate to be spawned via the `manager` (the sole `Agent`-tool holder). Both the manager and the requesting tier load this file as canonical reference.

---

## SPAWN (worker dispatch — supervisor → manager)

```
[Supervisor]   SendMessage manager:
                   SPAWN
                   NAME: or-implementer-task5
                   ROLE: implementer
                   MODEL: sonnet

[Manager]      SAME TURN:
               1. Agent({
                    team_name: <team>,
                    name: "or-implementer-task5",
                    subagent_type: "claude-toolkit:or-implementer",   // ROLE mapped — see table
                    model: "sonnet",
                    prompt: <substituted implementer-spawn-context.md>,
                    run_in_background: true
                  })
               2. SendMessage supervisor:
                    Spawned: or-implementer-task5

[Supervisor]   SAME TURN after `Spawned: or-implementer-task5`:
               SendMessage or-implementer-task5:
                   <task-specific brief built from SDD's implementer-prompt.md
                    template, with Task 5's full text + scene-setting context>
```

No idle gap. The manager's two actions are same-turn; the supervisor's task brief is same-turn after `Spawned:` confirmation.

### SPAWN message format (exact)

The message body MUST be EXACTLY this shape, as its own SendMessage (no preamble, no trailing text):

    SPAWN
    NAME: <name>
    ROLE: <role>
    MODEL: <model>

Where:
- `<name>` follows the worker naming convention (`or-implementer-task5`, `or-code-quality-reviewer-task5-rev2`, etc. — the authoritative table is in `or-supervisor.md`).
- `<role>` ∈ {`implementer`, `spec-reviewer`, `code-quality-reviewer`, `final-reviewer`}.
- `<model>` ∈ {`sonnet`, `opus`, `haiku`}. Pick per SDD's model-selection guidance. **For `implementer`, `MODEL` is REQUIRED** — the `or-implementer` agent has no default `model:`; a SPAWN that omits it for an implementer is a protocol violation (manager replies `SPAWN rejected — implementer requires explicit MODEL field.`).

If you need to include rationale or context, send it in a separate SendMessage AFTER the `Spawned:` response — never inside the SPAWN message.

### ROLE → subagent_type mapping (manager broker)

The manager maps the short `ROLE` to the plugin-qualified `subagent_type`:

| ROLE | subagent_type |
|------|---------------|
| `implementer` | `claude-toolkit:or-implementer` |
| `spec-reviewer` | `claude-toolkit:or-spec-reviewer` |
| `code-quality-reviewer` | `claude-toolkit:or-code-quality-reviewer` |
| `final-reviewer` | `claude-toolkit:or-final-reviewer` |

The manager substitutes the matching role spawn-context template for the worker's per-spawn variables — `implementer-spawn-context.md` for the implementer; `reviewer-spawn-context.md` (parameterised by `<ROLE>`) for any reviewer — then calls `Agent(...)` with `run_in_background: true`. Manager replies stay terse — `Spawned: <name>` is the entire message body. Acknowledgments and progress narration belong in the supervisor's `iteration-N.md`, not in chat.

---

## SPAWN_RESEARCH (research dispatch — phase agent → manager)

A phase agent SendMessages the manager:

```
SPAWN_RESEARCH
NAME: <name>
AGENT: <subagent_type>
DEPOSIT: <path>                       (required — findings never transit manager context)
MODEL: <model>                        (optional; defaults to the agent's frontmatter default)
PROMPT: <research question>
```

All research agents are spawned as **background teammates** (`run_in_background: true`, WITH `team_name`) — mechanically identical to worker dispatch. They signal completion by SendMessaging the manager a `RESEARCH_DONE: <path>` / `RESEARCH_BLOCKED: <path> — <reason>` token. After relaying to the phase agent, the manager shuts the research teammate down to keep the roster clean.

| Case | Manager action |
|------|----------------|
| `AGENT` is `or-dependency-researcher` or `or-community-researcher` (always deposit-aware) | Spawn as a background teammate with `DEPOSIT` appended to the prompt. The agent writes findings to `<DEPOSIT>` and SendMessages `RESEARCH_DONE: <path>`. Manager forwards `Research <name> done: <path>` to the phase agent, then shuts the researcher down. Manager NEVER opens the findings file. |
| `AGENT` is any other subagent_type (`dependency-researcher`/`community-researcher`/`Plan`/`Explore`/`general-purpose`, …) | Wrap: spawn `general-purpose` as a background teammate with a prompt that imitates the requested agent's style + writes to `<DEPOSIT>` + SendMessages `RESEARCH_DONE: <path>`. (Or, if the requested agent already has both `Write` and `SendMessage`, spawn it directly with the deposit instruction appended.) Manager shuts it down after relay. |

If a `SPAWN_RESEARCH` omits `DEPOSIT`, the manager rejects it (findings must never transit manager context): SendMessage the phase agent `SPAWN_RESEARCH rejected — DEPOSIT is required.` and take no further action on that request.

Then the manager SendMessages the phase agent: `Spawned: <name>`.
