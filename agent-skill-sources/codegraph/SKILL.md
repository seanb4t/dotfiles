---
name: codegraph
description: Use when asked where X is defined, how Y works, what calls X, or what changing X breaks in a .codegraph/ repo.
---

## Which tool for which question

| Question shape | Reach for this |
|---|---|
| Where is X defined? How does Y work? | `codegraph_explore` (MCP tool), or the `codegraph explore "<query>"` CLI as the shell fallback |
| What calls X? What does X call? | `codegraph_callers` / `codegraph_callees` |
| What breaks if I change X's signature? | `codegraph_impact` |
| I don't know the exact symbol name — fuzzy lookup | `codegraph_search` |
| Show one symbol's full detail | `codegraph_node` |
| Which files are involved? | `codegraph_files` |
| Is the index current? | `codegraph_status` |

## When not to reach for codegraph

With no `.codegraph/` directory at the repository root, skip codegraph entirely — use grep, find, and ordinary file reads instead. Indexing is the user's decision, not something to prompt for.

If the registered tool list looks shorter than the table above, `CODEGRAPH_MCP_TOOLS` is narrowing the companion set to a subset of `codegraph_node`, `codegraph_search`, `codegraph_callers`, `codegraph_callees`, `codegraph_impact`, `codegraph_files`, and `codegraph_status` — `codegraph_explore` is never removable by this filter. Unsetting the variable restores the full set.

## Worked examples

### The 2026-08-08 misdirection incident

A user reported: "the mcp server is only showing one tool." The session's first move was wrong — it searched the `instructions` string and the README for an explanation, because the instructions text of the day attributed tool visibility solely to index state ("an empty tool list means this repository has no index yet"). That explanation misled the session structurally, not just factually: a missing index produces zero tools, never one, so the single cause it offered could not have produced the symptom actually observed.

The right move was a `codegraph_explore` call against the server's own source — `internal/mcp/server.go` and `internal/cli/serve.go` — which would have surfaced the allowlist-resolution path (`ResolveCompanions`, gated by `CODEGRAPH_MCP_TOOLS`) directly, instead of trusting a wire-contract string that was, at the time, itself wrong.

Full root cause, timeline, and evidence: `.planning/debug/resolved/mcp-server-one-tool-only.md`. The `instructions` string has since been corrected to name all three visibility mechanisms — this example is a lesson about the failure mode, not a description of current behavior.

### Impact analysis before a refactor

"What breaks if I change this function's signature?" Reach for `codegraph_impact` (MCP), or `codegraph impact <symbol>` as the CLI fallback — a depth-bounded reverse blast radius over the call graph, not a manual grep for every call site. Grepping for a symbol's name finds textual matches; it does not compute what actually depends on it, and it misses call sites reached through an interface or alias. For the parameter's full semantics, read `codegraph://tools/impact`.

### Cross-file symbol lookup across dynamic dispatch

"Where is X defined?" or "how does Y work?" sometimes has an answer that sits behind an interface implementation or a dynamic-dispatch hop — the call site names an interface method, and the implementation that actually runs lives in a different file entirely. A text search matches the call site's spelling, not the implementation it resolves to, so the hop is exactly what grep structurally cannot follow. `codegraph_explore` (MCP), or `codegraph explore "<query>"` as the CLI fallback, resolves the call graph across that hop and returns the verbatim source plus the path that reaches it.

## Full reference

Every parameter, default, and return shape deliberately absent above lives in a resource this server serves — read it on demand through your MCP resource-read tool rather than trusting this file to restate it:

- `codegraph_explore` → `codegraph://tools/explore`
- `codegraph_node` → `codegraph://tools/node`
- `codegraph_search` → `codegraph://tools/search`
- `codegraph_callers` → `codegraph://tools/callers`
- `codegraph_callees` → `codegraph://tools/callees`
- `codegraph_impact` → `codegraph://tools/impact`
- `codegraph_files` → `codegraph://tools/files`
- `codegraph_status` → `codegraph://tools/status`
- How `CODEGRAPH_MCP_TOOLS` narrows the companion set → `codegraph://tools-filter`
- Preconditions for tool registration based on index presence → `codegraph://index-state`

All 8 tools are documented this way — nothing above restates a parameter, a default, a maximum, or a return shape that one of these resources already owns.
