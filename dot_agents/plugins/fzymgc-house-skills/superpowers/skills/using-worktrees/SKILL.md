---
name: using-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated workspaces (git worktrees or jj workspaces) with smart directory selection and safety verification
metadata:
  author: fzymgc-house
  version: 0.1.0 # x-release-please-version
  upstream: obra/superpowers v5.0.7 (skills/using-git-worktrees)
---

# Using Worktrees

> **Before running any VCS commands, read `references/vcs-preamble.md` and use
> the appropriate commands for the detected VCS (git or jj).**

## Overview

Workspaces create isolated working copies sharing the same repository, allowing
work on multiple features simultaneously without switching branches.

- **git**: Uses git worktrees
- **jj**: Uses jj workspaces (MUST use `jj workspace add`, never `git worktree add`)

**Core principle:** Sibling directory layout + VCS detection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-worktrees skill to set up an isolated workspace."

## VCS Detection

```bash
if jj root >/dev/null 2>&1; then
  VCS=jj
  # jj: always fetch at start
  jj git fetch
else
  VCS=git
fi
```

## Workspace Directory Convention

All workspaces use the **sibling directory** pattern to avoid confusing LSP
servers with nested repos:

```text
<repo>/                    # main repo
<repo>_worktrees/          # workspace parent (sibling)
  feature-auth/            # one workspace per task
  fix-bug-123/
```

The parent directory is `../<repo-basename>_worktrees/`. This is determined
automatically — no user prompt needed.

## Creation Steps

### 1. Detect Project Info

```bash
# Get repo root and name
if [ "$VCS" = "jj" ]; then
  repo_root=$(jj root)
else
  repo_root=$(git rev-parse --show-toplevel)
fi
project=$(basename "$repo_root")
worktree_parent="$(dirname "$repo_root")/${project}_worktrees"
```

### 2. Create Parent Directory

```bash
mkdir -p "$worktree_parent"
```

### 3. Create Workspace

**git:**

```bash
git worktree add "$worktree_parent/$BRANCH_NAME" -b "$BRANCH_NAME"
cd "$worktree_parent/$BRANCH_NAME"
```

**jj:**

```bash
jj workspace add "$worktree_parent/$WORKSPACE_NAME" --name "$WORKSPACE_NAME"
cd "$worktree_parent/$WORKSPACE_NAME"
# Create a bookmark for the workspace (needed for pushing/PRs)
jj bookmark create "$WORKSPACE_NAME" -r @
```

### 4. Run Project Setup

Auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 5. Install Hooks

If the repo uses git hooks, install them in the new workspace:

```bash
[[ -f lefthook.yaml ]] && lefthook install
[[ -f .pre-commit-config.yaml ]] && pre-commit install
[[ -f .beads/config.yaml ]] && bd hooks install --chain
```

### 6. Verify Clean Baseline

Run tests to ensure workspace starts clean:

```bash
# Examples — use project-appropriate command
npm test
cargo test
pytest
go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 7. Report Location

```text
Workspace ready at <full-path>
VCS: <git|jj>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Cleanup

When done with a workspace:

**git:**

```bash
git worktree remove <path>
```

**jj:**

```bash
jj workspace forget <name>
rm -rf <path>
```

Note: `jj workspace forget` de-registers the workspace but does NOT delete
files — you must `rm -rf` the directory after.

## Quick Reference

| Situation | Action |
|-----------|--------|
| VCS is git | `git worktree add ../<repo>_worktrees/<name> -b <name>` |
| VCS is jj | `jj workspace add ../<repo>_worktrees/<name> --name <name>` |
| Project has package.json | Run `npm install` after creation |
| Project has lefthook.yaml | Run `lefthook install` after creation |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |
| Cleanup (git) | `git worktree remove <path>` |
| Cleanup (jj) | `jj workspace forget <name>` + `rm -rf <path>` |

## Common Mistakes

### Nesting worktrees inside the repo

- **Problem:** LSP servers see nested repos, causing indexing confusion
- **Fix:** Always use sibling directory pattern (`<repo>_worktrees/`)

### Using git worktree in jj repos

- **Problem:** Creates a git worktree that jj doesn't track, causing sync issues
- **Fix:** Always detect VCS first; use `jj workspace add` in jj repos

### Forgetting to create a bookmark (jj)

- **Problem:** Can't push or create PRs without a bookmark
- **Fix:** Always `jj bookmark create <name> -r @` after workspace creation

### Forgetting to fetch (jj)

- **Problem:** Workspace starts with stale state
- **Fix:** Always `jj git fetch` before creating workspace

### Proceeding with failing tests

- **Problem:** Can't distinguish new bugs from pre-existing issues
- **Fix:** Report failures, get explicit permission to proceed

## Example Workflow

**git:**

```text
You: I'm using the using-worktrees skill to set up an isolated workspace.

[VCS detected: git]
[Create workspace: git worktree add ../myproject_worktrees/auth -b feature/auth]
[Run npm install]
[Run lefthook install]
[Run npm test — 47 passing]

Workspace ready at /Users/dev/myproject_worktrees/auth
VCS: git
Tests passing (47 tests, 0 failures)
Ready to implement auth feature
```

**jj:**

```text
You: I'm using the using-worktrees skill to set up an isolated workspace.

[VCS detected: jj]
[jj git fetch]
[Create workspace: jj workspace add ../myproject_worktrees/auth --name auth]
[jj bookmark create auth -r @]
[Run npm install]
[Run lefthook install]
[Run npm test — 47 passing]

Workspace ready at /Users/dev/myproject_worktrees/auth
VCS: jj
Tests passing (47 tests, 0 failures)
Ready to implement auth feature
```

## Integration

**Called by:**

- **brainstorming** — REQUIRED when design is approved and implementation follows
- **subagent-driven-development** — REQUIRED before executing any tasks
- **executing-plans** — REQUIRED before executing any tasks
- Any skill needing isolated workspace

**Pairs with:**

- **finishing-a-development-branch** — REQUIRED for cleanup after work complete
