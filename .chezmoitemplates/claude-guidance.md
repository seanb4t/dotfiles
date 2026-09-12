## Claude Code

Invoke relevant skills with the available Skill tool. Use Claude model identifiers
for delegated work. Additional tool guidance is in `~/.claude/rules/`.

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.
- **Reference docs** (MCP only): call `resources/list` then `resources/read` for the per-tool reference beyond this summary.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->
