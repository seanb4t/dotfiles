# Agent Instructions

`AGENTS.md` is the shared source of truth for repository instructions in this
repo. Use it for Codex, Claude Code, and other agents. `CLAUDE.md` is a
Claude-specific addendum only.

## Repository Purpose

This repository publishes four source plugins for the fzymgc-house skills
marketplace:

- `homelab` - infrastructure skills for Grafana, Terraform, and skill QA
- `pr-review` - PR review orchestrators plus review/fix/verification agents
- `jj` - Jujutsu workflow guidance
- `superpowers` - development workflow skills forked from obra/superpowers

It also publishes a repo-local Codex compatibility layer:

- `.agents/plugins/marketplace.json` - Codex marketplace manifest
- `plugins/<name>/` - thin Codex wrapper plugins

Keep the real skill content in the source plugin directories (`homelab/`,
`pr-review/`, `jj/`, `superpowers/`). The `plugins/` wrappers should point
back to those sources instead of copying them.

## Quick Start

```bash
# Install git hooks
lefthook install

# Verify hooks and local quality gates
lefthook run pre-commit --all-files
```

## Agent Docs

- Read this file first for repo-wide rules.
- Read `CLAUDE.md` only for Claude-specific behavior and compatibility notes.
- In agent prompts or skills, prefer `AGENTS.md` first and `CLAUDE.md` second.

## Repository Structure

```text
.claude-plugin/
  marketplace.json      # Claude marketplace manifest
.agents/plugins/
  marketplace.json      # Codex marketplace manifest
plugins/
  <plugin-name>/
    .codex-plugin/
      plugin.json       # Codex wrapper manifest
    ...                 # Symlinks back to source plugin content
homelab/
  plugin.json
  skills/
pr-review/
  plugin.json
  agents/
  references/
  skills/
jj/
  plugin.json
  commands/
  hooks/
  skills/
superpowers/
  plugin.json
  agents/
  commands/
  hooks/
  references/
  scripts/
  skills/
```

## Issue Tracking With bd

This project uses **bd (beads)** for all issue tracking. Do not use markdown
TODO lists or ad-hoc task tracking.

Start with:

```bash
bd onboard
bd ready
```

Quick reference:

```bash
bd ready                 # Find available work
bd show <id>             # View issue details
bd update <id> --claim   # Claim work atomically
bd close <id>            # Complete work
bd prime                 # Show current workflow guidance
bd dolt push             # Push bead history if a Dolt remote is configured
```

If bead synchronization matters, check whether a Dolt remote exists first:

```bash
bd dolt remote list
```

If no remote is configured, do not invent a sync step.

## Non-Interactive Shell Commands

Always use non-interactive flags with file operations to avoid hangs from
interactive aliases.

```bash
cp -f source dest
mv -f source dest
rm -f file
rm -rf directory
cp -rf source dest
scp -o BatchMode=yes ...
ssh -o BatchMode=yes ...
apt-get -y ...
HOMEBREW_NO_AUTO_UPDATE=1 brew ...
```

## Development Rules

### Commits

All commits must follow Conventional Commits:

```text
<type>(<scope>): <description>
```

Examples:

```text
feat(grafana): add incident management support
fix(review-pr): correct agent dispatch for security aspect
docs: update agent instructions
```

Validation is enforced by `cog verify` in the commit-msg hook.

### Testing and Linting

Primary local checks:

```bash
uv run --with pytest pytest .claude/hooks/tests/ jj/hooks/tests/ tests/ -v --import-mode=importlib
rumdl check README.md AGENTS.md CLAUDE.md docs/plans/*.md
jq empty .agents/plugins/marketplace.json plugins/*/.codex-plugin/plugin.json
```

Use narrower commands when touching only part of the repo, but verify the
relevant surface before claiming completion.

### Release Versioning

Versions are managed by release-please. Do not manually bump versions in:

- `.claude-plugin/marketplace.json`
- `plugin.json`
- `.codex-plugin/plugin.json`
- `SKILL.md` metadata version markers

When adding or removing a skill or plugin package, keep these in sync:

- `release-please-config.json`
- `.release-please-manifest.json`

### MCP Servers

Repo-level MCP servers are declared in `.mcp.json`:

- `grafana`
- `context7`
- `terraform`

Codex wrapper plugins may expose these via symlinks or manifest paths, but the
source configuration remains repo-rooted.

## Cross-Platform Guidance

### Claude and Codex

- Claude installs from `.claude-plugin/marketplace.json` and the source plugin
  directories.
- Codex uses `.agents/plugins/marketplace.json` and the thin wrappers in
  `plugins/`.
- Do not duplicate skill trees across the Claude and Codex layers.

### Agent Dispatch

Some workflows, especially in `pr-review` and `superpowers`, were authored for
Claude-style named subagents. In Codex, use the compatibility guidance in:

`superpowers/skills/using-superpowers/references/codex-tools.md`

That guidance explains how to map named agent dispatch to `spawn_agent`
workflows while reusing the existing prompt files.

## Gotchas

### Worktree Layout

Agent worktrees use a sibling directory layout:

```text
<repo>/
<repo>_worktrees/
  <worktree-name>/
```

Do not manually invent nested worktree repos under the main checkout.

### jj Rule

When `jj root` succeeds, treat the repo as a jj repo even if `.git/` also
exists. Use jj for mutating VCS operations.

- Allowed git usage: read-only commands such as `git log`, `git diff`,
  `git rev-parse`
- Disallowed when jj is present: `git commit`, `git checkout`,
  `git worktree add`, `git merge`, `git push`

### Session Completion

Work is not complete until the relevant changes are committed and pushed.

Required sequence:

1. File follow-up beads for leftover work
2. Run quality gates for the changed surface
3. Update or close the related bead
4. Push Git or jj changes
5. If a Dolt remote is configured, run `bd dolt push`
6. Verify final state with `git status` or `jj st`
7. Hand off concise context for the next session

Never stop at "ready to push." Push the branch yourself when the workflow
expects it.
