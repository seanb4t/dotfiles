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

## RFC2119 Keywords

| Keyword | Meaning |
|---------|---------|
| **MUST** / **MUST NOT** | Absolute requirement / prohibition - no exceptions without explicit user approval |
| **SHOULD** / **SHOULD NOT** | Strong recommendation - may ignore with justification |
| **MAY** | Optional, implementation choice |

**Precedence:** MUST/MUST NOT requirements always override efficiency or convenience preferences.

**Clarification:** "MUST act immediately" (line 33) means skip preamble in responses, NOT skip internal planning. Always plan first internally, then act without announcing.

## Communication Style

| Requirement | Description |
|-------------|-------------|
| MUST be direct | Skip preamble, unnecessary caveats, and explanations of intent |
| MUST act immediately | Don't announce what you're about to do - just do it (but plan internally first) |
| SHOULD minimize questions | Ask only when essential, not for edge cases |
| SHOULD show diffs | Show only relevant changes unless full context requested |

## Context Management

| Requirement | Action | Example |
|-------------|--------|---------|
| MUST minimize context | Use concise reasoning and output | |
| MUST use filters | Use Read with offset/limit (e.g., `offset=100, limit=50`) OR `rg` with context (e.g., `-A 5 -B 5`) | Never read entire 1000-line file |
| MUST filter output | Show only what's needed from command results | Use `--limit 10`, `head -20`, etc. |
| SHOULD summarize | Don't echo large outputs verbatim | Summarize key points instead |
| SHOULD edit sections | Prefer targeted edits over rewriting whole files | Edit 10 lines, not rewrite 200 |

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

Opus 4.5 → Sonnet 4.5 → Haiku 4 (use highest available)

## Tool Usage

### File Operations

| Priority | Tool | Use Case | Requirement |
|----------|------|----------|-------------|
| 1 | Read/Write/Edit | File read/write operations | MUST use with offset/limit to read only needed portions |
| 2 | `rg` CLI | File content search | MUST use (never `grep`) |

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
| `mcp__firecrawl-mcp__*` | Web scraping, content extraction, crawling | MUST use for data extraction |

**Workflow:** Use Exa to find pages → Use Firecrawl to extract content

## Critical Skills

**MUST invoke these skills when task matches trigger:**

| Skill | Trigger | Requirement |
|-------|---------|-------------|
| `systematic-debugging` | ANY error, bug, test failure, unexpected behavior | MUST use before proposing fixes |
| `verification-before-completion` | Before claiming work is complete/fixed/passing | MUST verify with actual commands |
| `fzymgc-house:grafana` | ANY Grafana operation | MUST use (skill overrides MCP) |
| `fzymgc-house:terraform` | ANY Terraform operation | MUST use (skill overrides MCP) |
| `fzymgc-house:respond-to-pr-comments` | Responding to PR comments | MUST use |
| `commit-commands:commit` | Creating git commits | MUST use |

**Skill relevance heuristics:**

A skill is relevant when:

- Task keyword matches skill name (e.g., "debug" → `systematic-debugging`)
- User explicitly requests workflow (e.g., "review this" → `requesting-code-review`)
- Task type matches skill category (e.g., new feature → `brainstorming`)
- Skill is in Critical Skills table above and trigger matches

### Full Skills Catalog

| Category | Skills |
|----------|--------|
| **Development** | `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, `verification-before-completion` |
| **Code Review** | `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch` |
| **Quality** | `pr-review-toolkit:review-pr`, `code-review:code-review`, `elements-of-style:writing-clearly-and-concisely` |
| **Commits** | `commit-commands:commit`, `commit-commands:commit-push-pr`, `commit-commands:clean_gone` |
| **Domain** | `fzymgc-house:grafana`, `fzymgc-house:terraform`, `fzymgc-house:respond-to-pr-comments` |
| **Plugin Dev** | `plugin-dev:create-plugin`, `skill-development`, `command-development`, `agent-development`, `hook-development`, `plugin-structure`, `plugin-settings`, `mcp-integration` |
| **Feature** | `feature-dev:feature-dev` |

*All `superpowers:*` prefix omitted from Development/Code Review for brevity*

### MCP Servers

| Server | Use Case | Requirement |
|--------|----------|-------------|
| `mcp__exa__*` | Intelligent web search | MUST use for search |
| `mcp__firecrawl-mcp__*` | Web scraping/extraction | MUST use for extraction |
| `mcp__context7__*` | Library documentation | SHOULD use |
| `mcp__kubernetes-mcp-server__*` | K8s cluster ops | MAY use |
| `mcp__terraform__*` | Terraform state/workspace | MAY use |

**Overrides (Skills take precedence over MCP):**

| Task | Use Skill (NOT MCP) |
|------|---------------------|
| Grafana operations | `fzymgc-house:grafana` |
| Terraform operations | `fzymgc-house:terraform` |

## Development Workflows

### Git

| Requirement | Details |
|-------------|---------|
| MUST use skill | `commit-commands:commit` for all commits |
| MUST use format | Conventional commits: `type(scope): description` |
| MUST commit atomically | One logical change per commit |
| MUST NOT amend/rebase | Unless explicitly requested |
| MUST use highest model | For PR/commit messages: Opus 4.5 → Sonnet 4.5 → Haiku 4 |

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

### Security & Infrastructure

| Area | Requirement | Details |
|------|-------------|---------|
| TLS/CA verification | MUST NOT skip | Without explicit approval |
| Certificate issues | MUST ask first | Before skipping verification |
| Web searches | MUST verify date | Check current year (2026 as of 2026-01-05) |
| GitHub Actions | MUST verify version | Check marketplace before use |
| Pre-commit hooks | MUST install | When creating worktrees with `.pre-commit-config.yaml` |

**Pre-commit installation:**

```bash
git worktree add ../feature-branch
cd ../feature-branch
[[ -f .pre-commit-config.yaml ]] && pre-commit install
```

**Date verification:**

```bash
# Wrong - assumes outdated year
# Search: cloudflared tunnel credentials 2024

# Right - verify first
date +%Y  # Returns: 2026
# Search: cloudflared tunnel credentials 2026
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

---

*Last updated: 2026-01-16*
*AI Assistant: Claude Opus 4.5*
