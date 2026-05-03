# User Preferences

This file contains Sean's personal instructions for Claude Code across all projects. These preferences override default behavior and MUST be followed exactly as written.

**General Scope:** For ALL interactions (including non-development tasks):

| Requirement | Description |
|-------------|-------------|
| MUST be direct | Skip preamble, unnecessary caveats, and explanations of intent |
| MUST minimize context | Use concise reasoning and output |
| SHOULD minimize questions | Ask only when essential, not for edge cases |
| MUST act immediately | Don't announce what you're about to do - just do it |

**Development Scope:** The technical rules below apply specifically to software development tasks (code, infrastructure, configuration, documentation).

*For non-development tasks (creative writing, general Q&A, analysis), use default behavior except for the General Scope rules above.*

## Quick Reference

Before ANY development task:

1. Check if skill applies (see [Critical Skills](#critical-skills)) → invoke with `Skill` tool FIRST
2. Plan internally before editing (don't announce planning to user)
3. Batch related changes into single coherent edits
4. Verify work before claiming completion
5. If ALL tools in priority chain fail → ask user for guidance

**Common command patterns:**
```bash
# Search codebase
rg "pattern" --type py -C 3

# GitHub PR workflow
gh pr list --limit 10 --json number,title,state
gh pr view 123 --json reviews,reviewDecision

# Git worktree verification
git worktree list && git branch --show-current
```

## RFC2119 Keywords

| Keyword | Meaning |
|---------|---------|
| **MUST** / **MUST NOT** | Absolute requirement / prohibition - no exceptions without explicit user approval |
| **SHOULD** / **SHOULD NOT** | Strong recommendation - may ignore with justification |
| **MAY** | Optional, implementation choice |

**Precedence:** MUST/MUST NOT requirements always override efficiency or convenience preferences.

**Clarification:** "MUST act immediately" (line 12) means skip preamble in responses, NOT skip internal planning. Always plan first internally, then act without announcing.

## Communication Style

*See General Scope table above for core rules (be direct, act immediately, minimize questions).*

| Requirement | Description |
|-------------|-------------|
| SHOULD show diffs | Show only relevant changes unless full context requested |

## Context Management

| Requirement | Action | Example |
|-------------|--------|---------|
| MUST minimize context | Use concise reasoning and output | |
| MUST use filters | Use Read with offset/limit (e.g., `offset=100, limit=50`) OR `rg` with context (e.g., `-A 5 -B 5`) | Never read entire 1000-line file |
| MUST filter output | Show only what's needed from command results | Use `--limit 10`, `head -20`, etc. |
| SHOULD summarize | Don't echo large outputs verbatim | Summarize key points instead |
| SHOULD edit sections | Prefer targeted edits over rewriting whole files | Edit 10 lines, not rewrite 200 |

## Git Operations

When working with Git worktrees or sparse checkouts, MUST verify the current working directory and branch before reading or writing files. Use `git worktree list` and `pwd` to confirm context before any file operations.

## Tool Precedence & Fallbacks

**Priority order (highest to lowest):**

| Priority | Tool Type | When to Use |
|----------|-----------|-------------|
| 1 | Skills | When task matches skill trigger (see [Critical Skills](#critical-skills)) - invoke BEFORE other tools |
| 2 | MCP servers | When skill doesn't exist for task |
| 3 | Native tools | When MCP unavailable or CLI more efficient |

**Fallback rules:**

| Scenario | Action |
|----------|--------|
| Skill invocation fails | MAY proceed without skill or ask user for guidance |
| MCP server unavailable | MAY use native tools as fallback |
| All tools in chain fail | MUST ask user: "X, Y, Z unavailable. Proceed anyway or abort?" |
| Tool conflict (MUST vs efficiency) | MUST requirements always win |

**Model selection order (for commits/PRs):**

Opus 4.6 → Sonnet 4+ → Haiku  (use highest available)

## Tool Usage

### File Operations

| Priority | Tool | Use Case | Requirement |
|----------|------|----------|-------------|
| 1 | Read/Write/Edit | File read/write operations | MUST use with offset/limit to read only needed portions |
| 2 | Grep tool / `rg` | File content search | MUST use (never raw `grep`) |

**File creation/modification:**

| Requirement | Action |
|-------------|--------|
| SHOULD use working dir | Unless path specified |
| MUST NOT create boilerplate | No README, LICENSE unless requested |
| MUST preserve structure | Follow existing naming conventions |

### Web Operations

| Tool | Use Case | Requirement |
|------|----------|-------------|
| `mcp__exa__*` | Intelligent web search | MUST use for search |
| `firecrawl` skill | Web scraping, content extraction, crawling | MUST use for data extraction |

**Workflow:** Use Exa to find pages → Use `firecrawl` skill to extract content

### Browser Automation

Use `agent-browser` for web automation. Run `agent-browser --help` for all commands.

Core workflow:
1. `agent-browser open <url>` - Navigate to page
2. `agent-browser snapshot -i` - Get interactive elements with refs (@e1, @e2)
3. `agent-browser click @e1` / `fill @e2 "text"` - Interact using refs
4. Re-snapshot after page changes

## Critical Skills

**MUST invoke these skills when task matches trigger:**

| Skill | Trigger | Requirement |
|-------|---------|-------------|
| `systematic-debugging` | ANY error, bug, test failure, unexpected behavior | MUST use before proposing fixes |
| `verification-before-completion` | Before claiming work is complete/fixed/passing | MUST verify with actual commands |
| `fzymgc-house:grafana` | ANY Grafana operation | MUST use (skill overrides MCP) |
| `fzymgc-house:terraform` | ANY Terraform operation | MUST use (skill overrides MCP) |

## Development Workflows

### Git

| Requirement | Details |
|-------------|---------|
| MUST use format | Conventional commits: `type(scope): description` |
| MUST commit atomically | One logical change per commit |
| MUST NOT amend/rebase | Unless explicitly requested |
| MUST use highest model | For PR/commit messages: Opus 4.6 → Sonnet 4+ → Haiku (use highest available) |

### GitHub CLI

| Requirement | Pattern |
|-------------|---------|
| MUST use `gh` | No web API, no git aliases |
| MUST use `--json` | Always filter with `--jq` |
| MUST limit results | Default `--limit 10` for listings |
| MUST NOT use interactive | No `-i`, `--interactive` flags |
| SHOULD avoid diffs | Don't fetch full content unless needed |

**Examples:**

```bash
gh pr list --limit 10 --json number,title,state
gh pr view 123 --json title,reviewDecision,reviews
gh issue create --title "..." --body "..." --label "bug"
```

**Constraints:**

| Action | Requirement |
|--------|-------------|
| Add issue reviewers | MUST NOT do manually |
| Request review | MUST use `requesting-code-review` skill |
| Respond to PR comments | MUST use `fzymgc-house:respond-to-pr-comments` skill |
| Add comments/commits | MUST include AI authorship byline |

### Code Review

When reviewing PRs, MUST read files from the PR's feature branch or worktree diff — never from the main branch. Use `gh pr diff <number>` or check out the PR branch first.

**Before making any file changes for a PR, MUST complete these verification steps (showing output of each):**

1. `git worktree list` — identify which worktree has the PR branch
2. `cd` into that worktree
3. `git branch --show-current` — confirm correct branch
4. Only then proceed with file reads and edits

### Security & Infrastructure

| Area | Requirement | Details |
|------|-------------|---------|
| TLS/CA verification | MUST NOT skip | Without explicit approval |
| Certificate issues | MUST ask first | Before skipping verification |
| Web searches | MUST verify date | Run `date +%Y` before using year in searches |
| GitHub Actions | MUST verify version | Check marketplace before use |
| Git hooks | MUST install | When creating worktrees with hook configs |

**Git hooks installation:**

```bash
git worktree add ../feature-branch
cd ../feature-branch
# Install hooks based on what the repo uses
[[ -f lefthook.yaml ]] && lefthook install
[[ -f .pre-commit-config.yaml ]] && pre-commit install
[[ -f .beads/config.yaml ]] && bd hooks install --chain
```

**Date verification:**

```bash
# Wrong - assumes outdated year
# Search: cloudflared tunnel credentials 2024

# Right - verify first
date +%Y  # Returns: 2026
# Search: cloudflared tunnel credentials $(date +%Y)
```

## Code Editing

### Planning

| Requirement | Action | Context |
|-------------|--------|---------|
| MUST plan first | Understand full scope before editing | Plan internally, don't announce to user |
| MUST batch changes | Make coherent whole-file edits, not line-by-line incremental changes | Applies to edits within same file/feature |
| SHOULD consider ripple effects | Think across codebase before changing | |
| SHOULD make holistic changes | Edit files as coherent wholes when possible | Balance with targeted edits (see Context Management) |

**Clarification:** "Batch changes" means make all related changes to a file/feature at once, not one line at a time. "Edit sections" (Context Management) means prefer targeted edits over rewriting entire files. Both apply to different contexts and are NOT contradictory.

**Example - Good Planning:**

```
user: Fix the auth bug
assistant: *internally: auth could be middleware, routes, or tokens*
assistant: *searches for auth files*
assistant: *reads relevant files*
assistant: *identifies root cause across 3 files*
assistant: *makes coordinated batch changes to all 3 files*
```

**Example - Bad Planning:**

```
user: Fix the auth bug
assistant: *reads one file*
assistant: *makes one-line change*
assistant: Done!
```

### Lint and Errors

| When | Requirement |
|------|-------------|
| Warnings/errors occur | MUST attempt proper fix first (not ignore directives) |
| Fix not straightforward | MUST explain issue and ask how to proceed |
| ANY case | MUST NOT auto-add ignore directives without justification |
| ANY case | MUST surface problems clearly, never hide them |

### Code Style

| Requirement | Description |
|-------------|-------------|
| SHOULD prefer simple | Readable over clever solutions |
| MUST NOT add obvious comments | Don't restate what code does |
| MUST match conventions | Follow existing project patterns |
| SHOULD NOT add unnecessary tests | Write only when requested or for non-trivial changes requiring test coverage |

## Decision Making Under Uncertainty

| Scenario | Action |
|----------|--------|
| Missing information | SHOULD make reasonable assumptions and proceed |
| Significant assumptions | SHOULD state briefly if they affect approach |
| Something fails | SHOULD try alternative before asking |
| Tool unavailable | MAY use fallback per precedence rules above |
| All fallbacks exhausted | MUST ask user: "X, Y, Z unavailable. Proceed anyway or abort?" |

## Environment Notes

When running on macOS, be aware of sandbox restrictions on SQLite writes and symlinks. If writes to beads directories or DB files fail, SHOULD check sandbox permissions before attempting complex debugging.

## Bead / Task Management

For bead CLI operations:

| Requirement | Details |
|-------------|---------|
| MUST use `--parent` | Not `-p` for parent flags |
| MUST include `--description` | Always provide description argument |
| MUST trim whitespace | Be careful with trailing whitespace in batch ID lists |

## CLAUDE.md Maintenance

| Action | Command |
|--------|---------|
| Quick update during session | Press `#` key to auto-incorporate learnings |
| Comprehensive audit | `/claude-md-improver` skill |
| Manual edit | Edit this file directly at `~/.claude/CLAUDE.md` |

---

*Last updated: 2026-03-08*
*AI Assistant: Claude Opus 4.6*
