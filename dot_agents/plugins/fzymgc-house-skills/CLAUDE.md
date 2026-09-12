# CLAUDE.md

Read `AGENTS.md` first.

This file is a Claude-specific addendum. `AGENTS.md` is the canonical
cross-platform repo guide for Codex, Claude Code, and other agents.

## Claude-Specific Notes

### Claude Marketplace

Claude installs the source plugins from the repository marketplace rooted at:

```text
.claude-plugin/marketplace.json
```

The source plugin manifests live in:

- `homelab/plugin.json`
- `pr-review/plugin.json`
- `jj/plugin.json`
- `superpowers/plugin.json`

### Claude Hook Behavior

Claude-specific hooks and settings live under `.claude/` when present.
Historically this repo has used Claude hooks for formatting and worktree
automation. If you are investigating Claude-only behavior, inspect:

- `.claude/settings.json`
- `.claude/hooks/`

These are Claude-specific implementation details, not the shared source of
truth for repo workflow rules.

### Claude-Specific Compatibility

Some older agent prompts and docs in this repo refer to `CLAUDE.md` for project
conventions. Keep this file present as a compatibility shim, but put general
repository rules in `AGENTS.md`.
